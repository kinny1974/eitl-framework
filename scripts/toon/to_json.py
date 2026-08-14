"""EitL Framework v3 - Decodificador TOON v4.1 a JSON.

Convierte texto TOON (Token-Oriented Object Notation) al formato JSON
según la especificación v4.1. Usa la biblioteca python-toon si está
disponible, con fallback a decodificación manual completa.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class ToonDelimiter(Enum):
    """Delimitadores soportados por TOON."""
    COMMA = ","
    TAB = "\t"
    PIPE = "|"

    @property
    def symbol(self) -> str:
        if self == ToonDelimiter.COMMA:
            return ""
        if self == ToonDelimiter.TAB:
            return "\t"
        return "|"


@dataclass
class ToonDecodeOptions:
    """Opciones de decodificación TOON.

    Attributes:
        strict: Modo estricto de validación (por defecto True).
        indent_size: Tamaño de indentación para parsear (por defecto 2).
    """
    strict: bool = True
    indent_size: int = 2


def _unescape_string(value: str) -> str:
    """Desescapa un string TOON (reglas §7.1).

    Args:
        value: El string escapado sin las comillas externas.

    Returns:
        El string desescapado.

    Raises:
        ValueError: Si contiene secuencias de escape inválidas.
    """
    result = []
    i = 0
    while i < len(value):
        if value[i] == "\\" and i + 1 < len(value):
            next_ch = value[i + 1]
            if next_ch == "\\":
                result.append("\\")
                i += 2
            elif next_ch == '"':
                result.append('"')
                i += 2
            elif next_ch == "n":
                result.append("\n")
                i += 2
            elif next_ch == "r":
                result.append("\r")
                i += 2
            elif next_ch == "t":
                result.append("\t")
                i += 2
            elif next_ch == "u" and i + 5 < len(value):
                hex_str = value[i + 2 : i + 6]
                try:
                    code_point = int(hex_str, 16)
                    if 0xD800 <= code_point <= 0xDFFF:
                        raise ValueError(f"Surrogate U+{code_point:04X} no permitido")
                    result.append(chr(code_point))
                    i += 6
                except ValueError:
                    raise ValueError(f"Escape unicode inválido: \\u{hex_str}")
            else:
                raise ValueError(f"Escape inválido: \\{next_ch}")
        else:
            result.append(value[i])
            i += 1
    return "".join(result)


def _parse_quoted_token(line: str, pos: int) -> tuple[str, int]:
    """Parsea un token entre comillas desde la posición dada.

    Args:
        line: La línea completa.
        pos: Posición actual (debe estar en '"').

    Returns:
        Tupla (string desescapado, nueva posición después de comillas).

    Raises:
        ValueError: Si el token no está terminado o tiene caracteres inválidos.
    """
    if pos >= len(line) or line[pos] != '"':
        raise ValueError(f"Se esperaba '\"' en posición {pos}")

    i = pos + 1
    chars = []
    while i < len(line):
        if line[i] == "\\":
            if i + 1 < len(line):
                chars.append(line[i])
                chars.append(line[i + 1])
                i += 2
            else:
                raise ValueError("Escape al final del string")
        elif line[i] == '"':
            raw = "".join(chars)
            return _unescape_string(raw), i + 1
        else:
            chars.append(line[i])
            i += 1

    raise ValueError("String sin terminar")


def _parse_primitive_token(token: str) -> Any:
    """Parsea un token TOON como primitivo (§4).

    Args:
        token: El token sin comillas.

    Returns:
        Valor Python: bool, int, float, str, o None.
    """
    if token == "true":
        return True
    if token == "false":
        return False
    if token == "null":
        return None

    number_match = re.match(r"^-?[0-9]+(?:\.[0-9]+)?(?:e[+-]?[0-9]+)?$", token, re.IGNORECASE)
    if number_match:
        try:
            if "." in token or "e" in token.lower():
                return float(token)
            return int(token)
        except ValueError:
            pass

    return token


def _split_delimited(line: str, delimiter: str, in_quotes: bool = False) -> list[str]:
    """Separa una línea por el delimitador activo, respetando comillas.

    Args:
        line: La línea a separar.
        delimiter: El delimitador a usar.
        in_quotes: Flag para contexto entre comillas.

    Returns:
        Lista de tokens separados.
    """
    tokens = []
    current = []
    in_q = False
    i = 0

    while i < len(line):
        ch = line[i]
        if ch == '"' and not in_q:
            in_q = True
            current.append(ch)
            i += 1
        elif ch == '"' and in_q:
            if i + 1 < len(line) and line[i + 1] == "\\":
                current.append(ch)
                current.append(line[i + 1])
                i += 2
                continue
            in_q = False
            current.append(ch)
            i += 1
        elif ch == "\\" and in_q:
            current.append(ch)
            if i + 1 < len(line):
                current.append(line[i + 1])
                i += 2
            else:
                i += 1
            continue
        elif ch == delimiter and not in_q:
            tokens.append("".join(current).strip(" "))
            current = []
            i += 1
        else:
            current.append(ch)
            i += 1

    tokens.append("".join(current).strip(" "))
    return tokens


def _parse_header(line: str) -> tuple[str, int, ToonDelimiter, list[str], bool] | None:
    """Parsea una cabecera TOON (reglas §6).

    Args:
        line: La línea de cabecera.

    Returns:
        Tupla (key, length, delimiter, fields, is_keyed) o None si no es cabecera.
    """
    stripped = line.strip()

    # Buscar el primer [ no citado
    bracket_start = None
    in_quote = False
    for i, ch in enumerate(stripped):
        if ch == '"':
            in_quote = not in_quote
        elif ch == '[' and not in_quote:
            bracket_start = i
            break

    if bracket_start is None:
        return None

    # Encontrar el ] correspondiente
    bracket_end = None
    brace_depth = 0
    in_quote = False
    for i in range(bracket_start + 1, len(stripped)):
        ch = stripped[i]
        if ch == '"':
            in_quote = not in_quote
        elif ch == '[' and not in_quote:
            brace_depth += 1
        elif ch == ']' and not in_quote:
            if brace_depth == 0:
                bracket_end = i
                break
            brace_depth -= 1

    if bracket_end is None:
        return None

    bracket_content = stripped[bracket_start + 1 : bracket_end]

    # Parsear el contenido del bracket: N[delim][:][fields]
    # Formato: [N] o [Ndelim] o [N:] o [N:delim] o [N{fields}] o [N:delim{fields}]
    # Determinar si es keyed: tiene : inmediatamente después del número
    # y el : está antes de } o al final del bracket

    # Extraer el número
    num_match = re.match(r"^([0-9]+)", bracket_content)
    if not num_match:
        return None

    length_str = num_match.group(1)
    # Verificar que no tenga ceros leading (excepto "0" solo)
    if length_str != "0" and length_str.startswith("0"):
        return None

    length = int(length_str)

    rest = bracket_content[num_match.end():]

    # Verificar si es keyed: : inmediatamente después del número
    is_keyed = rest.startswith(":")

    if is_keyed:
        rest = rest[1:]

    # Extraer el delimitador del bracket: | o tab
    # Tab en bracket_content sería el carácter literal HTAB
    bracket_delim = ","
    if rest and rest[0] == "|":
        bracket_delim = "|"
        rest = rest[1:]
    elif rest and rest[0] == "\t":
        bracket_delim = "\t"
        rest = rest[1:]

    if bracket_delim == "\t":
        delim = ToonDelimiter.TAB
    elif bracket_delim == "|":
        delim = ToonDelimiter.PIPE
    else:
        delim = ToonDelimiter.COMMA

    # Extraer el field list {fields} si existe
    fields: list[str] = []
    field_start = rest.find("{")
    if field_start != -1:
        field_end = rest.find("}", field_start)
        if field_end != -1:
            fields_raw = rest[field_start + 1 : field_end]
            if fields_raw:
                fields = [f.strip() for f in fields_raw.split(delim.value)]
                fields = [f for f in fields if f]

    # Contenido entre ] y : puede tener field list
    # Ejemplos: [2]:  -> after_bracket = ":"
    #           [2]{a,b}: -> after_bracket = "{a,b}:"
    after_bracket = stripped[bracket_end + 1 :]

    # Encontrar el primer : no citado
    colon_pos = None
    in_quote = False
    for i, ch in enumerate(after_bracket):
        if ch == '"':
            in_quote = not in_quote
        elif ch == ":" and not in_quote:
            colon_pos = i
            break

    if colon_pos is None:
        return None

    # Contenido entre ] y : (sin el :) para buscar field list
    between = after_bracket[:colon_pos].strip()

    # Extraer field list {fields} si existe en between
    field_start = between.find("{")
    if field_start != -1:
        field_end = between.find("}", field_start)
        if field_end != -1:
            fields_raw = between[field_start + 1 : field_end]
            if fields_raw:
                fields = [f.strip() for f in fields_raw.split(delim.value)]
                fields = [f for f in fields if f]

    # Determinar key: todo antes del [
    key_part = stripped[:bracket_start].strip()
    key = key_part if key_part else ""

    return (key, length, delim, fields, is_keyed)


class ToonDecoder:
    """Decodificador TOON v4.1 a JSON/Python.

    Implementa la decodificación completa del spec TOON v4.1 con soporte
    para tabular, keyed tabular, list, inline y nested forms.
    """

    def __init__(self, options: Optional[ToonDecodeOptions] = None) -> None:
        """Inicializa el decodificador con las opciones dadas.

        Args:
            options: Opciones de decodificación. Si es None, usa valores por defecto.
        """
        self.options = options or ToonDecodeOptions()

    def decode(self, text: str) -> Any:
        """Convierte texto TOON a datos JSON/Python.

        Args:
            text: String en formato TOON v4.1.

        Returns:
            Datos Python equivalentes (dict, list, o primitivo).

        Raises:
            ValueError: Si el texto TOON no es válido.
        """
        lines = self._preprocess_text(text)
        if not lines:
            return {}

        result = self._parse_lines(lines, 0, 0)
        return result["data"]

    def _preprocess_text(self, text: str) -> list[str]:
        """Preprocesa el texto TOON: eliminar BOM, CRLF, comentarios, blank lines.

        Args:
            text: Texto TOON crudo.

        Returns:
            Lista de líneas limpias.
        """
        if text.startswith("\ufeff"):
            text = text[1:]

        text = text.replace("\r\n", "\n").replace("\r", "\n")

        raw_lines = text.split("\n")

        cleaned: list[str] = []
        for line in raw_lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            cleaned.append(line.rstrip(" \t"))

        return cleaned

    def _get_depth(self, line: str) -> int:
        """Calcula la profundidad de indentación de una línea.

        Args:
            line: La línea a analizar.

        Returns:
            Nivel de profundidad (0-based).
        """
        spaces = 0
        for ch in line:
            if ch == " ":
                spaces += 1
            else:
                break
        return spaces // self.options.indent_size

    def _get_content(self, line: str) -> str:
        """Extrae el contenido significativo de una línea (sin indentación).

        Args:
            line: La línea completa.

        Returns:
            El contenido sin indentación leading.
        """
        return line.lstrip(" \t")

    def _parse_lines(
        self,
        lines: list[str],
        start_idx: int,
        target_depth: int,
    ) -> dict:
        """Parsea líneas recursivamente hasta el target depth.

        Args:
            lines: Lista de líneas.
            start_idx: Índice de inicio.
            target_depth: Profundidad objetivo para terminar.

        Returns:
            Dict con 'data' (valor parsed) y 'next_idx' (índice siguiente).
        """
        if start_idx >= len(lines):
            return {"data": {}, "next_idx": start_idx}

        first_content = self._get_content(lines[start_idx]).strip()
        if not first_content:
            return self._parse_lines(lines, start_idx + 1, target_depth)

        # Determinar root form
        depth = self._get_depth(lines[start_idx])
        content = self._get_content(lines[start_idx])

        if depth < target_depth:
            return {"data": {}, "next_idx": start_idx}

        # Root array
        if content.startswith("[") and not content.startswith("[0-9]:") and content.endswith(":"):
            result = self._parse_root_array(lines, start_idx)
            return result

        # Empty array root
        if content == "[]":
            return {"data": [], "next_idx": start_idx + 1}

        # Key-value or object
        if ":" in content:
            # Check if it's a header
            header = _parse_header(content)
            if header:
                key, length, delim, fields, is_keyed = header
                if is_keyed:
                    return self._parse_keyed_tabular(lines, start_idx, key, fields)
                else:
                    return self._parse_tabular_or_inline(lines, start_idx, key, length, fields)

            # Regular key-value
            return self._parse_object(lines, start_idx)

        # Primitive root
        return {"data": _parse_primitive_token(first_content), "next_idx": start_idx + 1}

    def _parse_root_array(self, lines: list[str], start_idx: int) -> dict:
        """Parsea un array raíz.

        Args:
            lines: Lista de líneas.
            start_idx: Índice de inicio.

        Returns:
            Dict con data y next_idx.
        """
        content = self._get_content(lines[start_idx])
        header = _parse_header(content)
        if not header:
            return {"data": [], "next_idx": start_idx + 1}

        length, delim, fields, is_keyed = header[1], header[2], header[3], header[4]

        if fields:
            if is_keyed:
                return self._parse_keyed_tabular(lines, start_idx, "", fields)
            else:
                return self._parse_tabular_array_root(lines, start_idx, length, fields, delim)

        # Inline array
        after_colon = content[content.index("]") + 2:]
        if after_colon.strip():
            tokens = _split_delimited(after_colon.strip(), delim.value)
            parsed = [_parse_primitive_token(t) for t in tokens]
            return {"data": parsed, "next_idx": start_idx + 1}

        # List array
        return self._parse_list_array(lines, start_idx, length)

    def _parse_tabular_array_root(
        self,
        lines: list[str],
        start_idx: int,
        length: int,
        fields: list[str],
        delim: ToonDelimiter,
    ) -> dict:
        """Parsea un array tabular raíz.

        Args:
            lines: Lista de líneas.
            start_idx: Índice de inicio.
            length: Longitud declarada.
            fields: Lista de campos.
            delim: Delimitador.

        Returns:
            Dict con data y next_idx.
        """
        result = []
        next_idx = start_idx + 1
        row_depth = self._get_depth(lines[start_idx]) + 1

        while next_idx < len(lines):
            line_depth = self._get_depth(lines[next_idx])
            if line_depth < row_depth:
                break

            content = self._get_content(lines[next_idx]).strip()
            if not content:
                next_idx += 1
                continue

            tokens = _split_delimited(content, delim.value)
            obj = {}
            for i, field_name in enumerate(fields):
                if i < len(tokens):
                    obj[field_name] = _parse_primitive_token(tokens[i].strip())
                else:
                    obj[field_name] = None
            result.append(obj)
            next_idx += 1

        return {"data": result, "next_idx": next_idx}

    def _parse_keyed_tabular(
        self,
        lines: list[str],
        start_idx: int,
        key: str,
        fields: list[str],
    ) -> dict:
        """Parsea un objeto keyed tabular (§9.5).

        Args:
            lines: Lista de líneas.
            start_idx: Índice de inicio.
            key: Clave del objeto keyed.
            fields: Lista de campos.

        Returns:
            Dict con data y next_idx.
        """
        delim = ToonDelimiter.COMMA
        header = _parse_header(self._get_content(lines[start_idx]))
        if header:
            delim = header[2]

        result: dict[str, Any] = {}
        next_idx = start_idx + 1
        entry_depth = self._get_depth(lines[start_idx]) + 1

        while next_idx < len(lines):
            line_depth = self._get_depth(lines[next_idx])
            if line_depth < entry_depth:
                break

            content = self._get_content(lines[next_idx]).strip()
            if not content:
                next_idx += 1
                continue

            colon_idx = content.find(":")
            if colon_idx == -1:
                break

            entry_key = content[:colon_idx].strip()
            cells_str = content[colon_idx + 1:].strip()

            tokens = _split_delimited(cells_str, delim.value) if cells_str else []

            obj = {}
            for i, field_name in enumerate(fields):
                if i < len(tokens):
                    obj[field_name] = _parse_primitive_token(tokens[i].strip())
                else:
                    obj[field_name] = None

            result[entry_key] = obj
            next_idx += 1

        if key:
            return {"data": {key: result}, "next_idx": next_idx}
        return {"data": result, "next_idx": next_idx}

    def _parse_tabular_or_inline(
        self,
        lines: list[str],
        start_idx: int,
        key: str,
        length: int,
        fields: list[str],
    ) -> dict:
        """Parsea un array tabular o inline.

        Args:
            lines: Lista de líneas.
            start_idx: Índice de inicio.
            key: Clave del array.
            length: Longitud declarada.
            fields: Lista de campos.

        Returns:
            Dict con data y next_idx.
        """
        if fields:
            return self._parse_tabular_array(lines, start_idx, key, length, fields)

        # Inline array
        content = self._get_content(lines[start_idx])
        after_colon = content[content.index("]") + 2:]

        header = _parse_header(content)
        delim = ToonDelimiter.COMMA
        if header:
            delim = header[2]

        if after_colon.strip():
            tokens = _split_delimited(after_colon.strip(), delim.value)
            parsed = [_parse_primitive_token(t) for t in tokens]
            return {"data": {key: parsed}, "next_idx": start_idx + 1}

        # Sin inline content: verificar si hay items de lista
        bracket_end = content.index("]")
        after_bracket = content[bracket_end + 1:]

        # Si el contenido después del bracket es solo ":" (sin field list),
        # es un array en forma list
        if after_bracket.strip() == ":":
            list_result = self._parse_list_array(lines, start_idx, length)
            return {"data": {key: list_result["data"]}, "next_idx": list_result["next_idx"]}

        return {"data": {key: []}, "next_idx": start_idx + 1}

    def _parse_tabular_array(
        self,
        lines: list[str],
        start_idx: int,
        key: str,
        length: int,
        fields: list[str],
    ) -> dict:
        """Parsea un array tabular con clave.

        Args:
            lines: Lista de líneas.
            start_idx: Índice de inicio.
            key: Clave del array.
            length: Longitud declarada.
            fields: Lista de campos.

        Returns:
            Dict con data y next_idx.
        """
        header = _parse_header(self._get_content(lines[start_idx]))
        delim = ToonDelimiter.COMMA
        if header:
            delim = header[2]

        result = []
        next_idx = start_idx + 1
        row_depth = self._get_depth(lines[start_idx]) + 1

        while next_idx < len(lines):
            line_depth = self._get_depth(lines[next_idx])
            if line_depth < row_depth:
                break

            content = self._get_content(lines[next_idx]).strip()
            if not content:
                next_idx += 1
                continue

            tokens = _split_delimited(content, delim.value)
            obj = {}
            for i, field_name in enumerate(fields):
                if i < len(tokens):
                    obj[field_name] = _parse_primitive_token(tokens[i].strip())
                else:
                    obj[field_name] = None
            result.append(obj)
            next_idx += 1

        return {"data": {key: result}, "next_idx": next_idx}

    def _parse_list_array(
        self,
        lines: list[str],
        start_idx: int,
        length: int,
    ) -> dict:
        """Parsea un array en forma list.

        Args:
            lines: Lista de líneas.
            start_idx: Índice de inicio.
            length: Longitud declarada.

        Returns:
            Dict con data y next_idx.
        """
        result: list[Any] = []
        next_idx = start_idx + 1
        item_depth = self._get_depth(lines[start_idx]) + 1

        while next_idx < len(lines) and len(result) < length:
            line_depth = self._get_depth(lines[next_idx])
            if line_depth < item_depth:
                break

            content = self._get_content(lines[next_idx]).strip()
            if not content.startswith("- "):
                break

            remainder = content[2:].strip() if len(content) > 2 else ""

            if not remainder:
                result.append({})
                next_idx += 1
                continue

            if remainder == "[]":
                result.append([])
                next_idx += 1
                continue

            if remainder.startswith("[") and ":" in remainder:
                # Inline array item
                arr_match = re.match(r"\[(\d+)([|\\t]?)\]\s*(.*)", remainder)
                if arr_match:
                    inner_length = int(arr_match.group(1))
                    inner_delim_char = arr_match.group(2) or ""
                    inner_values_str = arr_match.group(3).strip()

                    if inner_delim_char == "\t":
                        d = ToonDelimiter.TAB
                    elif inner_delim_char == "|":
                        d = ToonDelimiter.PIPE
                    else:
                        d = ToonDelimiter.COMMA

                    if inner_values_str:
                        tokens = _split_delimited(inner_values_str, d.value)
                        parsed = [_parse_primitive_token(t) for t in tokens]
                        result.append(parsed)
                    else:
                        result.append([])
                    next_idx += 1
                    continue

            # Object as list item
            if ":" in remainder:
                obj_result = self._parse_list_item_object(lines, next_idx, item_depth)
                result.append(obj_result["data"])
                next_idx = obj_result["next_idx"]
                continue

            # Primitive
            result.append(_parse_primitive_token(remainder))
            next_idx += 1

        return {"data": result, "next_idx": next_idx}

    def _parse_list_item_object(
        self,
        lines: list[str],
        start_idx: int,
        parent_depth: int,
    ) -> dict:
        """Parsea un objeto como list item.

        Args:
            lines: Lista de líneas.
            start_idx: Índice de inicio.
            parent_depth: Profundidad del padre.

        Returns:
            Dict con data y next_idx.
        """
        result: dict[str, Any] = {}
        next_idx = start_idx
        item_depth = parent_depth

        # El primer campo del objeto puede estar en la linea del hyphen "- key: value"
        first_content = self._get_content(lines[start_idx]).strip()
        if first_content.startswith("- "):
            remainder = first_content[2:].strip()
            if ":" in remainder:
                colon_idx = remainder.find(":")
                k = remainder[:colon_idx].strip()
                v_str = remainder[colon_idx + 1:].strip()
                if v_str:
                    result[k] = _parse_primitive_token(v_str)
                else:
                    nested = self._parse_lines(lines, start_idx + 1, item_depth + 1)
                    result[k] = nested["data"]
                    next_idx = nested["next_idx"]
                next_idx += 1
            elif remainder:
                # Es un primitivo, no un objeto
                result["_primitive"] = _parse_primitive_token(remainder)
                next_idx += 1
            else:
                # Hyphen solo, objeto vacio
                result = {}
                next_idx += 1

        # Procesar campos adicionales a mayor profundidad
        while next_idx < len(lines):
            line_depth = self._get_depth(lines[next_idx])
            content = self._get_content(lines[next_idx]).strip()

            if line_depth <= item_depth:
                break

            if content.startswith("- "):
                break

            if not content:
                next_idx += 1
                continue

            if ":" in content:
                colon_idx = content.find(":")
                k = content[:colon_idx].strip()
                v_str = content[colon_idx + 1:].strip()

                if not v_str:
                    nested = self._parse_lines(lines, next_idx + 1, line_depth + 1)
                    result[k] = nested["data"]
                    next_idx = nested["next_idx"]
                    continue

                result[k] = _parse_primitive_token(v_str)
                next_idx += 1
            else:
                next_idx += 1

        return {"data": result, "next_idx": next_idx}

    def _parse_object(self, lines: list[str], start_idx: int) -> dict:
        """Parsea un objeto TOON (reglas §8).

        Args:
            lines: Lista de líneas.
            start_idx: Índice de inicio.

        Returns:
            Dict con data y next_idx.
        """
        result: dict[str, Any] = {}
        next_idx = start_idx
        obj_depth = self._get_depth(lines[start_idx])

        while next_idx < len(lines):
            line_depth = self._get_depth(lines[next_idx])
            content = self._get_content(lines[next_idx]).strip()

            if not content:
                next_idx += 1
                continue

            # Solo salir si la profundidad es estrictamente menor
            if line_depth < obj_depth:
                break

            if ":" in content:
                colon_idx = content.find(":")
                k = content[:colon_idx].strip()
                v_str = content[colon_idx + 1:].strip()

                if not v_str:
                    nested = self._parse_lines(lines, next_idx + 1, line_depth + 1)
                    result[k] = nested["data"]
                    next_idx = nested["next_idx"]
                    continue

                if v_str == "[]":
                    result[k] = []
                    next_idx += 1
                    continue

                result[k] = _parse_primitive_token(v_str)
                next_idx += 1
            else:
                next_idx += 1

        return {"data": result, "next_idx": next_idx}


def toon_to_json(
    text: str,
    options: Optional[ToonDecodeOptions] = None,
) -> str:
    """Convierte texto TOON a JSON formateado.

    Usa la biblioteca python-toon si está disponible, con fallback
    al decodificador manual.

    Args:
        text: String en formato TOON v4.1.
        options: Opciones de decodificación.

    Returns:
        String JSON formateado.

    Raises:
        ValueError: Si el texto TOON no es válido.
    """
    try:
        from python_toon import load  # type: ignore

        if isinstance(text, bytes):
            text = text.decode("utf-8")

        result = load(text)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except ImportError:
        decoder = ToonDecoder(options)
        data = decoder.decode(text)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as exc:
        decoder = ToonDecoder(options)
        data = decoder.decode(text)
        return json.dumps(data, ensure_ascii=False, indent=2)


def to_json_file(input_path: str | Path) -> str:
    """Lee un archivo TOON e imprime la representación JSON.

    Args:
        input_path: Ruta al archivo TOON de entrada.

    Returns:
        String JSON generado.

    Raises:
        FileNotFoundError: Si el archivo no existe.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")

    content = path.read_text(encoding="utf-8")
    return toon_to_json(content)


def to_json_file_save(
    input_path: str | Path,
    output_path: str | Path | None = None,
    options: Optional[ToonDecodeOptions] = None,
) -> Path:
    """Convierte un archivo TOON a JSON y lo guarda.

    Args:
        input_path: Ruta al archivo TOON de entrada.
        output_path: Ruta al archivo JSON de salida. Si es None, usa .json.
        options: Opciones de decodificación.

    Returns:
        Ruta al archivo JSON generado.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")

    content = path.read_text(encoding="utf-8")
    json_str = toon_to_json(content, options)

    if output_path is None:
        out = path.with_suffix(".json")
    else:
        out = Path(output_path)

    out.write_text(json_str, encoding="utf-8")
    return out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Convierte formato TOON v4.1 a JSON",
        prog="to_json.py",
    )
    parser.add_argument(
        "input",
        help="Archivo TOON de entrada (usa - para stdin)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Archivo JSON de salida (usa - para stdout)",
        default=None,
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Modo estricto (por defecto: True)",
    )
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Desactivar modo estricto",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentación del JSON de salida (por defecto: 2)",
    )

    args = parser.parse_args()

    opts = ToonDecodeOptions(
        strict=not args.no_strict,
        indent_size=args.indent,
    )

    input_path = args.input
    if input_path == "-":
        import sys
        text = sys.stdin.read()
    else:
        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read()

    json_str = toon_to_json(text, opts)

    if args.output == "-":
        print(json_str)
    elif args.output:
        Path(args.output).write_text(json_str, encoding="utf-8")
        print(f"JSON guardado en: {args.output}", file=sys.stderr)
    else:
        print(json_str)

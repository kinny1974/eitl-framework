"""EitL Framework v3 - Codificador JSON a TOON v4.1.

Convierte estructuras JSON al formato TOON (Token-Oriented Object Notation)
según la especificación v4.1. Usa la biblioteca python-toon si está disponible,
con fallback a codificación manual completa.
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
class ToonFormatOptions:
    """Opciones de formato para la salida TOON.

    Attributes:
        indent_size: Espacios por nivel de indentación (por defecto 2).
        delimiter: Delimitador del documento (por defecto COMMA).
        sort_keys: Ordenar claves de objetos alfabéticamente (por defecto False).
        strict: Modo estricto de validación (por defecto True).
    """
    indent_size: int = 2
    delimiter: ToonDelimiter = ToonDelimiter.COMMA
    sort_keys: bool = False
    strict: bool = True


def _needs_quoting(value: str, delimiter: ToonDelimiter) -> bool:
    r"""Determina si un valor string necesita comillas en TOON.

    Reglas de quoting segun §7.2 del spec TOON v4.1:
    - Strings vacíos
    - Espacio leading/trailing
    - true, false, null (case-sensitive)
    - Numeric-like
    - Contiene :, \, ", [, ], {, }
    - Caracteres de control U+0000-U+001F
    - Contiene el delimitador activo
    - Comienza con "-" o "#"

    Args:
        value: El string a evaluar.
        delimiter: El delimitador activo para quoting-aware.

    Returns:
        True si el string debe ser quoted.
    """
    if value == "":
        return True

    if value != value.strip(" \t"):
        return True

    if value in ("true", "false", "null"):
        return True

    if re.match(r"^[+-]?[0-9]+(?:\.[0-9]+)?(?:e[+-]?[0-9]+)?$", value, re.IGNORECASE):
        return True

    for ch in (":", '"', "\\"):
        if ch in value:
            return True

    for ch in ("[", "]", "{", "}"):
        if ch in value:
            return True

    for cp in value:
        if ord(cp) < 0x20:
            return True

    delim_char = delimiter.value if delimiter != ToonDelimiter.COMMA else ","
    if delim_char in value:
        return True

    if value == "-" or value.startswith("-"):
        return True

    if value == "#" or value.startswith("#"):
        return True

    return False


def _escape_string(value: str) -> str:
    """Escapa un string para uso dentro de comillas TOON.

    Reglas de escape según §7.1 del spec TOON v4.1.

    Args:
        value: El string a escapar.

    Returns:
        El string escapado, listo para envolver en comillas.
    """
    result = []
    for ch in value:
        if ch == "\\":
            result.append("\\\\")
        elif ch == '"':
            result.append('\\"')
        elif ch == "\n":
            result.append("\\n")
        elif ch == "\r":
            result.append("\\r")
        elif ch == "\t":
            result.append("\\t")
        elif ord(ch) < 0x20:
            result.append(f"\\u{ord(ch):04x}")
        else:
            result.append(ch)
    return "".join(result)


def _format_primitive(value: Any) -> str:
    """Formatea un valor primitivo TOON (no string).

    Reglas según §2 del spec:
    - Booleans: lowercase true/false
    - Null: lowercase null
    - Numbers: canonical decimal form

    Args:
        value: El valor primitivo a formatear.

    Returns:
        Representación string del primitivo.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return _format_number(value)
    return str(value)


def _format_number(value: float) -> str:
    """Formatea un número en forma canónica según §2 del spec.

    - No notación exponente cuando 1e-6 <= |n| < 1e21 y n != 0
    - Sin ceros a la izquierda
    - Sin ceros trailing en fracción
    - -0 -> 0

    Args:
        value: El número a formatear.

    Returns:
        Representación string canónica del número.
    """
    if value != value:
        return "null"
    if value == float("inf") or value == float("-inf"):
        return "null"

    if isinstance(value, float) and value == int(value) and abs(value) < 1e21:
        return str(int(value))

    if abs(value) < 1e-6 and value != 0:
        return f"{value:e}"

    normalized = f"{value:.17g}"
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")

    if normalized == "-0":
        normalized = "0"

    return normalized


def _is_unquoted_key(key: str) -> bool:
    """Verifica si una clave puede usarse sin comillas según §7.3.

    Args:
        key: La clave a verificar.

    Returns:
        True si la clave coincide con [A-Za-z_][A-Za-z0-9_.]*
    """
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_.]*$", key))


def _format_key(key: str) -> str:
    """Formatea una clave TOON (quoted o unquoted según §7.3).

    Args:
        key: La clave a formatear.

    Returns:
        La clave formateada, posiblemente con comillas.
    """
    if _is_unquoted_key(key):
        return key
    return f'"{_escape_string(key)}"'


def _detect_tabular_fields(objs: list[dict]) -> list[str] | None:
    """Detecta si una lista de dicts puede usar forma tabular (§9.3).

    Verifica:
    - Todos son objetos no vacíos
    - Todos tienen las mismas claves
    - Todas las columnas son uniform-primitive o nested-uniform

    Args:
        objs: Lista de objetos a evaluar.

    Returns:
        Lista de claves en orden (primera objeto) si es tabular, None si no.
    """
    if not objs:
        return None

    for obj in objs:
        if not isinstance(obj, dict) or len(obj) == 0:
            return None

    first_keys = list(objs[0].keys())
    for obj in objs[1:]:
        if list(obj.keys()) != first_keys:
            return None

    for key in first_keys:
        col_values = [obj[key] for obj in objs]
        if not _check_uniform_column(col_values):
            return None

    return first_keys


def _check_uniform_column(values: list) -> bool:
    """Verifica si una columna tiene valores uniformes (§9.3).

    Una columna es uniform-primitive si todos son primitivos.
    Es nested-uniform si todos son objetos no vacíos con mismas claves
    y todas sus sub-columnas son uniform-primitive o nested-uniform.

    Args:
        values: Lista de valores de la columna.

    Returns:
        True si la columna es uniforme.
    """
    if not values:
        return False

    types = [type(v).__name__ for v in values]
    all_primitive = all(isinstance(v, (str, int, float, bool)) or v is None for v in values)

    if all_primitive:
        # Verificar que no hay mezcla de primitivo con None que cause problema
        # None es considerado primitivo en TOON
        return True

    # Check nested-uniform: todos deben ser dict no vacíos
    if all(isinstance(v, dict) and len(v) > 0 for v in values):
        first_keys = list(values[0].keys())
        for v in values[1:]:
            if list(v.keys()) != first_keys:
                return False
        for key in first_keys:
            sub_values = [v[key] for v in values]
            if not _check_uniform_column(sub_values):
                return False
        return True

    return False


def _leaf_fields(fields: list[str]) -> list[str]:
    """Extrae los leaf fields de una lista de fields con posibles nested groups.

    Para TOON manual simple, solo procesamos leaf fields planos.

    Args:
        fields: Lista de field names.

    Returns:
        Lista de leaf fields (sin nested groups en implementación manual).
    """
    return [f for f in fields if "{" not in f]


class ToonEncoder:
    """Codificador JSON a TOON v4.1.

    Implementa la codificación completa del spec TOON v4.1 con soporte
    para tabular, keyed tabular, list, inline y nested forms.
    """

    def __init__(self, options: Optional[ToonFormatOptions] = None) -> None:
        """Inicializa el codificador con las opciones dadas.

        Args:
            options: Opciones de formato. Si es None, usa valores por defecto.
        """
        self.options = options or ToonFormatOptions()

    def encode(self, data: Any) -> str:
        """Convierte datos JSON/Python a formato TOON.

        Args:
            data: Datos Python (dict, list, o primitivo) a codificar.

        Returns:
            String en formato TOON v4.1.

        Raises:
            ValueError: Si los datos no son serializables en TOON.
            TypeError: Si el tipo de datos no es soportado.
        """
        if data is None or data is ...:
            return self.encode(None)

        if isinstance(data, (dict, list)):
            result = self._encode_value(data, depth=0, is_root=True)
            return result.rstrip("\n")
        else:
            return _format_primitive(data)

    def _encode_value(
        self,
        value: Any,
        depth: int,
        is_root: bool = False,
        parent_key: str = "",
        is_list_item: bool = False,
    ) -> str:
        """Codifica un valor recursivamente.

        Args:
            value: El valor a codificar.
            depth: Nivel de indentación actual.
            is_root: Si este es el valor raíz del documento.
            parent_key: Clave del padre (para líneas key: value).
            is_list_item: Si estamos dentro de un list item.

        Returns:
            String TOON para este valor.
        """
        indent = " " * (self.options.indent_size * depth)

        if value is None:
            return f"{indent}null" if not is_root else "null"

        if isinstance(value, bool):
            return f"{indent}{'true' if value else 'false'}" if not is_root else ("true" if value else "false")

        if isinstance(value, (int, float)):
            return f"{indent}{_format_number(value)}" if not is_root else _format_number(value)

        if isinstance(value, str):
            return self._encode_string_value(value, indent)

        if isinstance(value, list):
            return self._encode_array(value, indent, is_root, parent_key)

        if isinstance(value, dict):
            return self._encode_object(value, indent, is_root, parent_key, is_list_item)

        raise TypeError(f"Tipo no soportado para TOON: {type(value).__name__}")

    def _encode_string_value(self, value: str, indent: str) -> str:
        """Codifica un valor string con quoting apropiado.

        Args:
            value: El string a codificar.
            indent: Prefijo de indentación.

        Returns:
            String TOON para el valor.
        """
        if _needs_quoting(value, self.options.delimiter):
            escaped = _escape_string(value)
            return f"{indent}\"{escaped}\""
        return f"{indent}{value}"

    def _encode_array(
        self,
        value: list,
        indent: str,
        is_root: bool,
        parent_key: str,
    ) -> str:
        """Codifica un array con la forma apropiada (§9.1-§9.4).

        Args:
            value: La lista a codificar.
            indent: Prefijo de indentación de la cabecera.
            is_root: Si es array raíz.
            parent_key: Clave padre.

        Returns:
            String TOON para el array.
        """
        delim_sym = self.options.delimiter.symbol
        bracket = f"[{len(value)}{delim_sym}]"

        if is_root:
            return self._encode_array_root(value, bracket)

        if parent_key:
            header = f"{indent}{_format_key(parent_key)}{bracket}:"
        else:
            return ""

        if len(value) == 0:
            return f"{indent}key: []"

        # Determinar la forma apropiada
        if self._is_inline_array(value):
            return self._encode_inline_array(value, header, is_root)
        elif self._is_tabular_array(value):
            return self._encode_tabular_array(value, header, is_root)
        else:
            return self._encode_list_array(value, header)

    def _encode_array_root(self, value: list, bracket: str) -> str:
        """Codifica un array en posición raíz.

        Args:
            value: La lista a codificar.
            bracket: Segmento bracket [N].

        Returns:
            String TOON para el array raíz.
        """
        if len(value) == 0:
            return "[]"

        delim_sym = self.options.delimiter.symbol
        header = f"{bracket}:"

        if self._is_inline_array(value):
            return self._encode_inline_array(value, header, is_root=True)
        elif self._is_tabular_array(value):
            return self._encode_tabular_array(value, header, is_root=True)
        else:
            return self._encode_list_array(value, header)

    def _is_inline_array(self, value: list) -> bool:
        """Verifica si un array debe usar forma inline (§9.1).

        Args:
            value: La lista a verificar.

        Returns:
            True si todos los elementos son primitivos.
        """
        return all(isinstance(v, (str, int, float, bool)) or v is None for v in value)

    def _is_tabular_array(self, value: list) -> bool:
        """Verifica si un array debe usar forma tabular (§9.3).

        Args:
            value: La lista a verificar.

        Returns:
            True si todos son dicts uniformes.
        """
        if not value or not isinstance(value[0], dict):
            return False
        return _detect_tabular_fields(value) is not None

    def _encode_inline_array(
        self,
        value: list,
        header: str,
        is_root: bool = False,
    ) -> str:
        """Codifica un array inline (§9.1).

        Args:
            value: Lista de primitivos.
            header: Cabecera del array (key[N]:).
            is_root: Si es array raíz.

        Returns:
            String TOON para el array inline.
        """
        cells = []
        for v in value:
            if v is None:
                cells.append("null")
            elif isinstance(v, bool):
                cells.append("true" if v else "false")
            elif isinstance(v, (int, float)):
                cells.append(_format_number(v))
            elif isinstance(v, str):
                if _needs_quoting(v, self.options.delimiter):
                    cells.append(f'"{_escape_string(v)}"')
                else:
                    cells.append(v)

        delim = self.options.delimiter.value
        return f"{header} {delim.join(cells)}"

    def _encode_tabular_array(
        self,
        value: list[dict],
        header: str,
        is_root: bool = False,
    ) -> str:
        """Codifica un array tabular (§9.3).

        Args:
            value: Lista de dicts uniformes.
            header: Cabecera del array (key[N]:).
            is_root: Si es array raíz.

        Returns:
            String TOON para el array tabular.
        """
        fields = _detect_tabular_fields(value)
        if not fields:
            return self._encode_list_array(value, header)

        # Para field list, usar el delimitador activo
        # Para comma: "", pero fields se separan con ","
        # Para tab: "\t", para pipe: "|"
        delim = self.options.delimiter
        bracket_delim = delim.symbol  # "" para comma, "\t" para tab, "|" para pipe
        field_delim = delim.value  # "," para comma, "\t" para tab, "|" para pipe

        fields_str = field_delim.join(fields)

        # Insertar field list en el bracket
        bracket_end = header.index("]")
        if is_root:
            full_header = f"[{len(value)}{bracket_delim}]{{{fields_str}}}:"
        else:
            full_header = header[: bracket_end + 1] + f"{{{fields_str}}}" + header[bracket_end + 1 :]

        row_indent = " " * self.options.indent_size
        lines = [full_header]
        for obj in value:
            cells = []
            for field_name in fields:
                cell_val = obj.get(field_name, "")
                if cell_val is None:
                    cells.append("null")
                elif isinstance(cell_val, bool):
                    cells.append("true" if cell_val else "false")
                elif isinstance(cell_val, (int, float)):
                    cells.append(_format_number(cell_val))
                elif isinstance(cell_val, str):
                    if _needs_quoting(cell_val, self.options.delimiter):
                        cells.append(f'"{_escape_string(cell_val)}"')
                    else:
                        cells.append(cell_val)
            lines.append(f"{row_indent}{field_delim.join(cells)}")

        return "\n".join(lines)

    def _encode_list_array(
        self,
        value: list,
        header: str,
    ) -> str:
        """Codifica un array en forma list (§9.2, §9.4).

        Args:
            value: Lista a codificar.
            header: Cabecera completa del array (key[N]:).

        Returns:
            String TOON para el array list form.
        """
        item_indent = " " * self.options.indent_size
        lines = [header]

        for item in value:
            if isinstance(item, dict):
                lines.append(self._encode_object_as_list_item(item, item_indent))
            elif isinstance(item, list):
                if item:
                    if self._is_inline_array(item):
                        cells = []
                        for v in item:
                            if v is None:
                                cells.append("null")
                            elif isinstance(v, bool):
                                cells.append("true" if v else "false")
                            elif isinstance(v, (int, float)):
                                cells.append(_format_number(v))
                            elif isinstance(v, str):
                                if _needs_quoting(v, self.options.delimiter):
                                    cells.append(f'"{_escape_string(v)}"')
                                else:
                                    cells.append(v)
                        delim = self.options.delimiter.value
                        lines.append(f"{item_indent}- [{len(item)}{delim}] {delim.join(cells)}")
                    else:
                        lines.append(f"{item_indent}- [{len(item)}{delim}]")
                else:
                    lines.append(f"{item_indent}- []")
            else:
                lines.append(f"{item_indent}- {self._encode_primitive(item)}")

        return "\n".join(lines)

    def _encode_object_as_list_item(self, obj: dict, item_indent: str) -> str:
        """Codifica un objeto como list item (§10).

        El primer campo del objeto se pone en la línea del hyphen.
        Los campos restantes van en indentación incrementada.

        Args:
            obj: El objeto a codificar.
            item_indent: Indentación del list item.

        Returns:
            String TOON para el list item object.
        """
        if not obj:
            return f"{item_indent}-"

        keys = list(obj.keys())
        if self.options.sort_keys:
            keys.sort()

        first_key = keys[0]
        first_val = obj[first_key]
        # Indentación para campos secundarios: item_indent + 1 nivel
        field_indent = item_indent + " " * self.options.indent_size

        if isinstance(first_val, (dict, list)) and len(first_val) > 0:
            # Primer campo es anidado: hyphen + key: value, contenido a nivel +2
            child_lines = self._encode_child_value(first_val, first_key, field_indent)
            hyphen_line = f"{item_indent}- {first_key}: " if isinstance(first_val, dict) else f"{item_indent}- {first_key}:"
            # Para valores primitivos en primer campo: hyphen + key: value
            return f"{item_indent}- {first_key}: {self._encode_primitive(first_val)}"
        else:
            # Primer campo es primitivo: hyphen + key: value en misma línea
            lines = [f"{item_indent}- {first_key}: {self._encode_primitive(first_val)}"]
            for key in keys[1:]:
                val = obj[key]
                if isinstance(val, (dict, list)) and len(val) > 0:
                    child_lines = self._encode_child_value(val, key, field_indent)
                    lines.append(f"{field_indent}{_format_key(key)}:")
                    lines.append(child_lines)
                elif isinstance(val, (dict, list)) and len(val) == 0:
                    lines.append(f"{field_indent}{_format_key(key)}:")
                else:
                    lines.append(
                        f"{field_indent}{_format_key(key)}: {self._encode_primitive(val)}"
                    )
            return "\n".join(lines)

    def _encode_primitive(self, value: Any) -> str:
        """Codifica un primitivo sin indentación.

        Args:
            value: El valor primitivo.

        Returns:
            String TOON para el primitivo.
        """
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return _format_number(value)
        if isinstance(value, str):
            if _needs_quoting(value, self.options.delimiter):
                return f'"{_escape_string(value)}"'
            return value
        return str(value)

    def _encode_object(
        self,
        value: dict,
        base_indent: str,
        is_root: bool,
        parent_key: str,
        is_list_item: bool = False,
    ) -> str:
        """Codifica un objeto con la forma apropiada (§8, §9.5).

        Args:
            value: El dict a codificar.
            base_indent: Indentación de la cabecera actual.
            is_root: Si es objeto raíz.
            parent_key: Clave del padre.
            is_list_item: Si estamos en un list item.

        Returns:
            String TOON para el objeto.
        """
        if not value:
            if is_root:
                return ""
            return f"{base_indent}key:"

        if self._is_keyed_tabular(value) and len(value) >= 2:
            return self._encode_keyed_tabular(value, base_indent, is_root, parent_key)

        lines: list[str] = []
        keys = list(value.keys())
        if self.options.sort_keys:
            keys.sort()

        for key in keys:
            val = value[key]
            if isinstance(val, list) and len(val) > 0:
                # Arrays: el array encoder produce la cabecera completa con key
                child_lines = self._encode_array_header_content(val, key, base_indent)
                lines.append(child_lines)
            elif isinstance(val, list) and len(val) == 0:
                lines.append(f"{base_indent}{_format_key(key)}: []")
            elif isinstance(val, dict) and len(val) == 0:
                lines.append(f"{base_indent}{_format_key(key)}:")
            elif isinstance(val, dict) and len(val) > 0:
                # Keyed tabular: el encoder produce la cabecera completa con key
                if self._is_keyed_tabular(val):
                    child_lines = self._encode_keyed_tabular_header_content(val, key, base_indent)
                    lines.append(child_lines)
                else:
                    child_key_lines = self._encode_child_value(val, key, base_indent)
                    lines.append(f"{base_indent}{_format_key(key)}:")
                    lines.append(child_key_lines)
            else:
                lines.append(
                    f"{base_indent}{_format_key(key)}: {self._encode_primitive(val)}"
                )

        return "\n".join(lines)

    def _encode_child_value(self, value: Any, child_key: str, current_indent: str) -> str:
        """Codifica un valor hijo (dict/list) con indentación incrementada.

        Args:
            value: El valor hijo a codificar.
            child_key: Clave del valor hijo.
            current_indent: Indentación actual (padre).

        Returns:
            String TOON para el valor hijo (sin la clave del padre).
        """
        child_indent = current_indent + " " * self.options.indent_size
        if isinstance(value, list):
            # El padre ya agrega "key:" aquí, el array solo devuelve el contenido
            return self._encode_array_content(value, child_indent, parent_key=child_key)
        if isinstance(value, dict):
            # El padre ya agrega "key:" aquí, el objeto solo devuelve el contenido
            return self._encode_object_content(value, child_indent, parent_key=child_key)
        return self._encode_primitive(value)

    def _encode_array_header_content(
        self,
        value: list,
        parent_key: str,
        indent: str,
    ) -> str:
        """Codifica un array completo con su cabecera (incluyendo key).

        Este metodo produce la linea completa `key[N]{fields}:` para tabular,
        o `key[N]:` para inline/list. El parent object NO debe agregar
        un `key:` adicional.

        Args:
            value: La lista a codificar.
            parent_key: Clave del array.
            indent: Indentación.

        Returns:
            String TOON completo para el array.
        """
        delim_sym = self.options.delimiter.symbol
        bracket = f"[{len(value)}{delim_sym}]"

        header = f"{indent}{_format_key(parent_key)}{bracket}:"

        if len(value) == 0:
            return f"{indent}{_format_key(parent_key)}: []"

        if self._is_inline_array(value):
            return self._encode_inline_array(value, header)
        elif self._is_tabular_array(value):
            return self._encode_tabular_array(value, header)
        else:
            return self._encode_list_array(value, header)

    def _encode_object_content(
        self,
        value: dict,
        indent: str,
        parent_key: str = "",
    ) -> str:
        """Codifica solo el contenido de un objeto (sin la clave del padre).

        Args:
            value: El dict a codificar.
            indent: Indentación.
            parent_key: Clave del padre.

        Returns:
            String TOON solo para el contenido del objeto.
        """
        if not value:
            return f"{indent}key:"

        if self._is_keyed_tabular(value) and len(value) >= 2:
            return self._encode_keyed_tabular_content(value, indent, parent_key)

        lines: list[str] = []
        keys = list(value.keys())
        if self.options.sort_keys:
            keys.sort()

        for key in keys:
            val = value[key]
            if isinstance(val, (dict, list)) and len(val) > 0:
                child_key_lines = self._encode_child_value(val, key, indent)
                lines.append(f"{indent}{_format_key(key)}:")
                lines.append(child_key_lines)
            elif isinstance(val, (dict, list)) and len(val) == 0:
                lines.append(f"{indent}{_format_key(key)}:")
            else:
                lines.append(
                    f"{indent}{_format_key(key)}: {self._encode_primitive(val)}"
                )

        return "\n".join(lines)

    def _encode_keyed_tabular_header_content(
        self,
        value: dict,
        parent_key: str,
        indent: str,
    ) -> str:
        """Codifica keyed tabular con su cabecera completa (incluyendo key).

        Args:
            value: El dict a codificar.
            parent_key: Clave del objeto keyed.
            indent: Indentación.

        Returns:
            String TOON completo para el keyed tabular.
        """
        delim = self.options.delimiter
        bracket_delim = delim.symbol
        field_delim = delim.value
        vals = list(value.values())
        fields = list(vals[0].keys())
        fields_str = field_delim.join(fields)

        header = f"{indent}{_format_key(parent_key)}[{len(value)}:{bracket_delim}]{{{fields_str}}}:"
        lines = [header]

        for entry_key, entry_val in value.items():
            cells = []
            for field_name in fields:
                cell_val = entry_val.get(field_name, "")
                if cell_val is None:
                    cells.append("null")
                elif isinstance(cell_val, bool):
                    cells.append("true" if cell_val else "false")
                elif isinstance(cell_val, (int, float)):
                    cells.append(_format_number(cell_val))
                elif isinstance(cell_val, str):
                    if _needs_quoting(cell_val, self.options.delimiter):
                        cells.append(f'"{_escape_string(cell_val)}"')
                    else:
                        cells.append(cell_val)
            lines.append(
                f"{indent}  {_format_key(entry_key)}: {field_delim.join(cells)}"
            )

        return "\n".join(lines)

    def _encode_object_dict_lines(
        self,
        value: dict,
        indent: str,
        is_list_item: bool = False,
    ) -> str:
        """Codifica un dict como lista de líneas (para list items).

        Args:
            value: El dict a codificar.
            indent: Indentación actual.
            is_list_item: Si estamos en un list item.

        Returns:
            String TOON con líneas del objeto.
        """
        lines: list[str] = []
        keys = list(value.keys())
        if self.options.sort_keys:
            keys.sort()

        for key in keys:
            val = value[key]
            if isinstance(val, (dict, list)) and len(val) > 0:
                child_key_lines = self._encode_child_value(val, key, indent)
                lines.append(f"{indent}{_format_key(key)}:")
                lines.append(child_key_lines)
            elif isinstance(val, list) and len(val) == 0:
                lines.append(f"{indent}{_format_key(key)}: []")
            elif isinstance(val, dict) and len(val) == 0:
                lines.append(f"{indent}{_format_key(key)}:")
            else:
                lines.append(
                    f"{indent}{_format_key(key)}: {self._encode_primitive(val)}"
                )

        return "\n".join(lines)

    def _is_keyed_tabular(self, value: dict) -> bool:
        """Verifica si un dict puede usar forma keyed tabular (§9.5).

        Args:
            value: El dict a verificar.

        Returns:
            True si todos los valores son dicts uniformes no vacíos.
        """
        if len(value) < 2:
            return False

        vals = list(value.values())
        if not all(isinstance(v, dict) and len(v) > 0 for v in vals):
            return False

        first_keys = list(vals[0].keys())
        for v in vals[1:]:
            if list(v.keys()) != first_keys:
                return False

        for key in first_keys:
            col_values = [v[key] for v in vals]
            if not _check_uniform_column(col_values):
                return False

        return True

    def _encode_keyed_tabular(
        self,
        value: dict,
        indent: str,
        is_root: bool,
        parent_key: str,
    ) -> str:
        """Codifica un objeto keyed tabular (§9.5).

        Args:
            value: El dict a codificar.
            indent: Indentación actual.
            is_root: Si es objeto raíz.
            parent_key: Clave del padre.

        Returns:
            String TOON para el objeto keyed tabular.
        """
        delim = self.options.delimiter
        bracket_delim = delim.symbol
        field_delim = delim.value
        vals = list(value.values())
        fields = list(vals[0].keys())
        fields_str = field_delim.join(fields)

        if is_root:
            header = f"[{len(value)}:{bracket_delim}]{{{fields_str}}}:"
        elif parent_key:
            header = f"{indent}{_format_key(parent_key)}[{len(value)}:{bracket_delim}]{{{fields_str}}}:"
        else:
            header = f"{indent}{_format_key(parent_key)}[{len(value)}:{bracket_delim}]{{{fields_str}}}:"

        lines = [header]
        for entry_key, entry_val in value.items():
            cells = []
            for field_name in fields:
                cell_val = entry_val.get(field_name, "")
                if cell_val is None:
                    cells.append("null")
                elif isinstance(cell_val, bool):
                    cells.append("true" if cell_val else "false")
                elif isinstance(cell_val, (int, float)):
                    cells.append(_format_number(cell_val))
                elif isinstance(cell_val, str):
                    if _needs_quoting(cell_val, self.options.delimiter):
                        cells.append(f'"{_escape_string(cell_val)}"')
                    else:
                        cells.append(cell_val)
            lines.append(
                f"{indent}  {_format_key(entry_key)}: {field_delim.join(cells)}"
            )

        return "\n".join(lines)


def json_to_toon(
    data: Any,
    options: Optional[ToonFormatOptions] = None,
) -> str:
    """Convierte datos JSON/Python a formato TOON v4.1.

    Función conveniente que usa la biblioteca python-toon si está disponible,
    con fallback al codificador manual.

    Args:
        data: Datos Python (dict, list, o primitivo) a codificar.
        options: Opciones de formato. Si es None, usa valores por defecto.

    Returns:
        String en formato TOON v4.1.

    Raises:
        ValueError: Si ocurre un error durante la codificación.
    """
    try:
        from python_toon import dump  # type: ignore

        if isinstance(data, str):
            json_str = data
        else:
            json_str = json.dumps(data, ensure_ascii=False, sort_keys=options.sort_keys if options else False)

        result = dump(json_str, indent_size=options.indent_size if options else 2)
        if isinstance(result, bytes):
            return result.decode("utf-8")
        return str(result)
    except ImportError:
        encoder = ToonEncoder(options)
        return encoder.encode(data)
    except Exception as exc:
        encoder = ToonEncoder(options)
        return encoder.encode(data)


def to_json_file(input_path: str | Path) -> str:
    """Lee un archivo JSON e imprime la representación TOON.

    Args:
        input_path: Ruta al archivo JSON de entrada.

    Returns:
        String TOON generado.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        json.JSONDecodeError: Si el archivo no es JSON válido.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")

    content = path.read_text(encoding="utf-8")
    data = json.loads(content)
    return json_to_toon(data)


def to_json_file_save(
    input_path: str | Path,
    output_path: str | Path | None = None,
    options: Optional[ToonFormatOptions] = None,
) -> Path:
    """Convierte un archivo JSON a TOON y lo guarda.

    Args:
        input_path: Ruta al archivo JSON de entrada.
        output_path: Ruta al archivo TOON de salida. Si es None, usa .toon.
        options: Opciones de formato.

    Returns:
        Ruta al archivo TOON generado.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")

    content = path.read_text(encoding="utf-8")
    data = json.loads(content)

    toon_str = json_to_toon(data, options)

    if output_path is None:
        out = path.with_suffix(".toon")
    else:
        out = Path(output_path)

    out.write_text(toon_str, encoding="utf-8")
    return out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Convierte JSON a formato TOON v4.1",
        prog="to_toon.py",
    )
    parser.add_argument(
        "input",
        help="Archivo JSON de entrada (usa - para stdin)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Archivo TOON de salida (usa - para stdout)",
        default=None,
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Tamaño de indentación (por defecto: 2)",
    )
    parser.add_argument(
        "--delimiter",
        choices=["comma", "tab", "pipe"],
        default="comma",
        help="Delimitador (por defecto: comma)",
    )
    parser.add_argument(
        "--sort-keys",
        action="store_true",
        help="Ordenar claves de objetos",
    )

    args = parser.parse_args()

    delim_map = {"comma": ToonDelimiter.COMMA, "tab": ToonDelimiter.TAB, "pipe": ToonDelimiter.PIPE}

    opts = ToonFormatOptions(
        indent_size=args.indent,
        delimiter=delim_map[args.delimiter],
        sort_keys=args.sort_keys,
    )

    input_path = args.input
    if input_path == "-":
        import sys
        data = json.load(sys.stdin)
    else:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    toon_str = json_to_toon(data, opts)

    if args.output == "-":
        print(toon_str)
    elif args.output:
        Path(args.output).write_text(toon_str, encoding="utf-8")
        print(f"TOON guardado en: {args.output}", file=sys.stderr)
    else:
        print(toon_str)

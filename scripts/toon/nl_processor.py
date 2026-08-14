"""EitL Framework v3 - Procesador NL a TOON.

Orquesta el pipeline completo: Texto Natural -> Modelo Pequeño -> JSON -> TOON.

Envía texto natural a un modelo de lenguaje pequeño, parsea la respuesta JSON,
y la codifica en formato TOON v4.1. Guarda TOON y JSON en un directorio de cache.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import httpx

from scripts.toon.to_json import toon_to_json, ToonDecodeOptions
from scripts.toon.to_toon import (
    json_to_toon,
    ToonDelimiter,
    ToonFormatOptions,
)


class ModelProvider(Enum):
    """Proveedores de modelo soportados."""
    OPENAI_COMPAT = "openai_compat"
    VLLM = "vllm"
    OLLAMA = "ollama"


@dataclass
class NLPipelineConfig:
    """Configuración del pipeline NL -> TOON.

    Attributes:
        model_url: URL del endpoint del modelo pequeño.
        model_name: Nombre del modelo a usar.
        api_key: Clave API para autenticación (si es necesaria).
        cache_dir: Directorio para guardar TOON + JSON cacheados.
        system_prompt: Prompt del sistema para el modelo.
        max_tokens: Máximo de tokens en la respuesta.
        temperature: Temperatura de generación.
        toon_options: Opciones de formato TOON.
        provider: Proveedor del modelo.
    """
    model_url: str = "http://192.168.2.111:8002/v1"
    model_name: str = "small-model"
    api_key: str = ""
    cache_dir: str = "toon-cache"
    system_prompt: str = (
        "Eres un asistente que convierte requisitos en estructuras de datos JSON. "
        "Devuelve SOLO un objeto JSON válido, sin markdown ni explicaciones adicionales."
    )
    max_tokens: int = 4096
    temperature: float = 0.1
    toon_options: ToonFormatOptions = field(
        default_factory=lambda: ToonFormatOptions(
            indent_size=2,
            delimiter=ToonDelimiter.COMMA,
        )
    )
    provider: ModelProvider = ModelProvider.OPENAI_COMPAT


@dataclass
class PipelineResult:
    """Resultado del pipeline NL -> TOON.

    Attributes:
        success: Si el pipeline completó exitosamente.
        raw_nl: Texto natural de entrada.
        json_response: Respuesta JSON del modelo.
        toon_output: Salida TOON codificada.
        cache_path: Ruta al directorio cache donde se guardaron los archivos.
        json_file: Ruta al archivo JSON cacheado.
        toon_file: Ruta al archivo TOON cacheado.
        error: Mensaje de error si falló el pipeline.
        model_name: Nombre del modelo que generó la respuesta.
        processing_time: Tiempo de procesamiento en segundos.
    """
    success: bool = False
    raw_nl: str = ""
    json_response: Any = None
    toon_output: str = ""
    cache_path: Path = field(default_factory=Path)
    json_file: Path = field(default_factory=Path)
    toon_file: Path = field(default_factory=Path)
    error: str = ""
    model_name: str = ""
    processing_time: float = 0.0


def _build_openai_request(
    config: NLPipelineConfig,
    nl_text: str,
) -> dict:
    """Construye la petición para un modelo compatible con OpenAI API.

    Args:
        config: Configuración del pipeline.
        nl_text: Texto natural de entrada.

    Returns:
        Dict con la estructura de la petición HTTP.
    """
    return {
        "model": config.model_name,
        "messages": [
            {"role": "system", "content": config.system_prompt},
            {"role": "user", "content": nl_text},
        ],
        "max_tokens": config.max_tokens,
        "temperature": config.temperature,
        "response_format": {"type": "json_object"},
    }


def _build_ollama_request(
    config: NLPipelineConfig,
    nl_text: str,
) -> dict:
    """Construye la petición para Ollama.

    Args:
        config: Configuración del pipeline.
        nl_text: Texto natural de entrada.

    Returns:
        Dict con la estructura de la petición HTTP.
    """
    return {
        "model": config.model_name,
        "prompt": f"{config.system_prompt}\n\nUsuario: {nl_text}\nAsistente:",
        "format": "json",
        "options": {
            "num_predict": config.max_tokens,
            "temperature": config.temperature,
        },
    }


async def _send_to_model(
    config: NLPipelineConfig,
    nl_text: str,
) -> dict:
    """Envía texto natural al modelo pequeño y obtiene respuesta JSON.

    Args:
        config: Configuración del pipeline.
        nl_text: Texto natural de entrada.

    Returns:
        Dict con la respuesta del modelo.

    Raises:
        httpx.HTTPError: Si la petición HTTP falla.
        ValueError: Si la respuesta no contiene JSON válido.
    """
    if config.provider == ModelProvider.OLLAMA:
        request_data = _build_ollama_request(config, nl_text)
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{config.model_url}/api/generate",
                json=request_data,
                headers={"Content-Type": "application/json"}
                if config.api_key
                else {},
            )
            resp.raise_for_status()
            result = resp.json()
            return {"content": result.get("response", "")}

    if config.provider == ModelProvider.VLLM:
        request_data = _build_openai_request(config, nl_text)
        headers = {"Content-Type": "application/json"}
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{config.model_url}/chat/completions",
                json=request_data,
                headers=headers,
            )
            resp.raise_for_status()
            result = resp.json()
            return result

    # OpenAI compatible (default)
    request_data = _build_openai_request(config, nl_text)
    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{config.model_url}/chat/completions",
            json=request_data,
            headers=headers,
        )
        resp.raise_for_status()
        result = resp.json()
        return result


def _extract_json_from_response(response_data: dict) -> str:
    """Extrae el JSON de la respuesta del modelo.

    Intenta múltiples estrategias para extraer JSON válido:
    1. Directamente del campo content/message
    2. Buscando bloques ```json ... ```
    3. Buscando el primer { ... } válido

    Args:
        response_data: Respuesta del modelo.

    Returns:
        String JSON extraído.

    Raises:
        ValueError: Si no se puede extraer JSON de la respuesta.
    """
    content = ""

    if "choices" in response_data:
        choice = response_data["choices"][0]
        content = choice.get("message", {}).get("content", "")
    elif "content" in response_data:
        content = response_data["content"]
    elif "response" in response_data:
        content = response_data["response"]
    else:
        content = str(response_data)

    if not content:
        raise ValueError("Respuesta del modelo vacía")

    # Buscar bloque JSON markdown
    if "```" in content:
        json_block = content
        start = json_block.find("```json")
        if start == -1:
            start = json_block.find("```")
        if start != -1:
            end = json_block.find("```", start + 3)
            if end != -1:
                return json_block[start + 3 : end].strip()

    # Si ya parece JSON válido, devolver directamente
    stripped = content.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            json.loads(stripped)
            return stripped
        except json.JSONDecodeError:
            pass

    # Buscar primer objeto JSON válido
    brace_start = content.find("{")
    if brace_start != -1:
        brace_count = 0
        for i in range(brace_start, len(content)):
            if content[i] == "{":
                brace_count += 1
            elif content[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    candidate = content[brace_start : i + 1].strip()
                    try:
                        json.loads(candidate)
                        return candidate
                    except json.JSONDecodeError:
                        continue

    raise ValueError(f"No se pudo extraer JSON de la respuesta: {content[:200]}")


def _save_to_cache(
    cache_dir: Path,
    nl_text: str,
    json_data: Any,
    toon_output: str,
    model_name: str,
) -> tuple[Path, Path, Path]:
    """Guarda los resultados en el directorio de cache.

    Crea un subdirectorio con timestamp para cada ejecución del pipeline.

    Args:
        cache_dir: Directorio base de cache.
        nl_text: Texto natural de entrada.
        json_data: Datos JSON del modelo.
        toon_output: Salida TOON codificada.
        model_name: Nombre del modelo usado.

    Returns:
        Tupla (cache_dir_path, json_file_path, toon_file_path).
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    sanitized_nl = nl_text.strip().replace(" ", "_").replace("/", "_")[:50]
    session_dir = cache_dir / f"{timestamp}_{sanitized_nl[:30]}"
    session_dir.mkdir(parents=True, exist_ok=True)

    json_file = session_dir / "response.json"
    json_file.write_text(
        json.dumps(json_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    toon_file = session_dir / "response.toon"
    toon_file.write_text(toon_output, encoding="utf-8")

    metadata_file = session_dir / "metadata.json"
    metadata_file.write_text(
        json.dumps(
            {
                "timestamp": timestamp,
                "model": model_name,
                "input_length": len(nl_text),
                "json_size": len(json_file.read_text(encoding="utf-8")),
                "toon_size": len(toon_file.read_text(encoding="utf-8")),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return session_dir, json_file, toon_file


def nl_to_toon(
    nl_text: str,
    config: Optional[NLPipelineConfig] = None,
) -> PipelineResult:
    """Orquestra el pipeline completo: NL -> Modelo -> JSON -> TOON.

    Args:
        nl_text: Texto natural de entrada (requisito, descripción, etc.).
        config: Configuración del pipeline. Si es None, usa valores por defecto.

    Returns:
        PipelineResult con los datos de entrada, JSON, TOON y paths de cache.
    """
    import time

    config = config or NLPipelineConfig()
    result = PipelineResult(raw_nl=nl_text)

    start_time = time.monotonic()

    try:
        response_data = _send_to_model(config, nl_text)

        json_str = _extract_json_from_response(response_data)
        json_data = json.loads(json_str)

        toon_output = json_to_toon(json_data, config.toon_options)

        cache_path = Path(config.cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)

        session_dir, json_file, toon_file = _save_to_cache(
            cache_path,
            nl_text,
            json_data,
            toon_output,
            config.model_name,
        )

        elapsed = time.monotonic() - start_time

        result.success = True
        result.json_response = json_data
        result.toon_output = toon_output
        result.cache_path = session_dir
        result.json_file = json_file
        result.toon_file = toon_file
        result.model_name = config.model_name
        result.processing_time = elapsed

    except httpx.HTTPError as exc:
        elapsed = time.monotonic() - start_time
        result.error = f"Error de HTTP: {exc}"
        result.processing_time = elapsed
    except ValueError as exc:
        elapsed = time.monotonic() - start_time
        result.error = f"Error de procesamiento: {exc}"
        result.processing_time = elapsed
    except Exception as exc:
        elapsed = time.monotonic() - start_time
        result.error = f"Error inesperado: {exc}"
        result.processing_time = elapsed

    return result


def nl_to_toon_sync(
    nl_text: str,
    config: Optional[NLPipelineConfig] = None,
) -> PipelineResult:
    """Versión síncrona del pipeline NL -> TOON.

    Usa asyncio.run para ejecutar la parte asíncrona.

    Args:
        nl_text: Texto natural de entrada.
        config: Configuración del pipeline.

    Returns:
        PipelineResult con los resultados.
    """
    import asyncio

    config = config or NLPipelineConfig()

    async def _run() -> PipelineResult:
        return await nl_to_toon_async(nl_text, config)

    return asyncio.run(_run())


async def nl_to_toon_async(
    nl_text: str,
    config: Optional[NLPipelineConfig] = None,
) -> PipelineResult:
    """Versión asíncrona del pipeline NL -> TOON.

    Args:
        nl_text: Texto natural de entrada.
        config: Configuración del pipeline.

    Returns:
        PipelineResult con los resultados.
    """
    import time

    config = config or NLPipelineConfig()
    result = PipelineResult(raw_nl=nl_text)

    start_time = time.monotonic()

    try:
        response_data = await _send_to_model(config, nl_text)

        json_str = _extract_json_from_response(response_data)
        json_data = json.loads(json_str)

        toon_output = json_to_toon(json_data, config.toon_options)

        cache_path = Path(config.cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)

        session_dir, json_file, toon_file = _save_to_cache(
            cache_path,
            nl_text,
            json_data,
            toon_output,
            config.model_name,
        )

        elapsed = time.monotonic() - start_time

        result.success = True
        result.json_response = json_data
        result.toon_output = toon_output
        result.cache_path = session_dir
        result.json_file = json_file
        result.toon_file = toon_file
        result.model_name = config.model_name
        result.processing_time = elapsed

    except httpx.HTTPError as exc:
        elapsed = time.monotonic() - start_time
        result.error = f"Error de HTTP: {exc}"
        result.processing_time = elapsed
    except ValueError as exc:
        elapsed = time.monotonic() - start_time
        result.error = f"Error de procesamiento: {exc}"
        result.processing_time = elapsed
    except Exception as exc:
        elapsed = time.monotonic() - start_time
        result.error = f"Error inesperado: {exc}"
        result.processing_time = elapsed

    return result


def create_config(
    model_url: str = "http://192.168.2.111:8002/v1",
    model_name: str = "small-model",
    api_key: str = "",
    cache_dir: str = "toon-cache",
    system_prompt: str = "",
    toon_indent: int = 2,
    toon_delimiter: str = "comma",
) -> NLPipelineConfig:
    """Crea una configuración del pipeline con valores personalizados.

    Args:
        model_url: URL del endpoint del modelo.
        model_name: Nombre del modelo.
        api_key: Clave API.
        cache_dir: Directorio de cache.
        system_prompt: Prompt del sistema.
        toon_indent: Indentación TOON.
        toon_delimiter: Delimitador TOON (comma/tab/pipe).

    Returns:
        Configuración lista para usar.
    """
    delim_map = {
        "comma": ToonDelimiter.COMMA,
        "tab": ToonDelimiter.TAB,
        "pipe": ToonDelimiter.PIPE,
    }

    delimiter = delim_map.get(toon_delimiter, ToonDelimiter.COMMA)

    prompt = system_prompt
    if not prompt:
        prompt = (
            "Eres un asistente que convierte requisitos en estructuras de datos JSON. "
            "Devuelve SOLO un objeto JSON válido, sin markdown ni explicaciones adicionales."
        )

    return NLPipelineConfig(
        model_url=model_url,
        model_name=model_name,
        api_key=api_key,
        cache_dir=cache_dir,
        system_prompt=prompt,
        toon_options=ToonFormatOptions(
            indent_size=toon_indent,
            delimiter=delimiter,
        ),
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Pipeline NL -> Small Model -> JSON -> TOON",
        prog="nl_processor.py",
    )
    parser.add_argument(
        "text",
        help="Texto natural de entrada (requisito/descripción)",
    )
    parser.add_argument(
        "-u", "--url",
        default="http://192.168.2.111:8002/v1",
        help="URL del endpoint del modelo (por defecto: http://192.168.2.111:8002/v1)",
    )
    parser.add_argument(
        "-m", "--model",
        default="small-model",
        help="Nombre del modelo (por defecto: small-model)",
    )
    parser.add_argument(
        "-k", "--api-key",
        default="",
        help="Clave API para autenticación",
    )
    parser.add_argument(
        "-c", "--cache-dir",
        default="toon-cache",
        help="Directorio de cache (por defecto: toon-cache)",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentación TOON (por defecto: 2)",
    )
    parser.add_argument(
        "--delimiter",
        choices=["comma", "tab", "pipe"],
        default="comma",
        help="Delimitador TOON (por defecto: comma)",
    )
    parser.add_argument(
        "--provider",
        choices=["openai_compat", "vllm", "ollama"],
        default="openai_compat",
        help="Proveedor del modelo (por defecto: openai_compat)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="No guardar en cache",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Solo mostrar JSON, no TOON",
    )
    parser.add_argument(
        "--toon-only",
        action="store_true",
        help="Solo mostrar TOON, no JSON",
    )

    args = parser.parse_args()

    provider_map = {
        "openai_compat": ModelProvider.OPENAI_COMPAT,
        "vllm": ModelProvider.VLLM,
        "ollama": ModelProvider.OLLAMA,
    }

    config = NLPipelineConfig(
        model_url=args.url,
        model_name=args.model,
        api_key=args.api_key,
        cache_dir=args.cache_dir if not args.no_cache else "",
        toon_options=ToonFormatOptions(
            indent_size=args.indent,
            delimiter=ToonDelimiter(args.delimiter),
        ),
        provider=provider_map[args.provider],
    )

    print(f"Procesando: {args.text[:80]}...", file=sys.stderr)

    result = nl_to_toon(args.text, config)

    if not result.success:
        print(f"ERROR: {result.error}", file=sys.stderr)
        sys.exit(1)

    if not args.json_only:
        print("=== TOON ===")
        print(result.toon_output)

    if not args.toon_only:
        print("\n=== JSON ===")
        print(json.dumps(result.json_response, ensure_ascii=False, indent=2))

    if result.cache_path:
        print(f"\n=== Cache ===", file=sys.stderr)
        print(f"JSON: {result.json_file}", file=sys.stderr)
        print(f"TOON: {result.toon_file}", file=sys.stderr)
        print(f"Tiempo: {result.processing_time:.2f}s", file=sys.stderr)

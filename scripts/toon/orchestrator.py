"""EitL Framework v3 - TOON Orchestrator Gateway.

Punto de entrada CLI para el orquestador del pipeline TOON.
Orquesta la conversión de texto natural a TOON v4.1 a través del
modelo pequeño (qwen2.5-3b-instruct), con verificación de salud,
cache y fallback graceful.

Flujo principal:
    1. Verificar salud del servidor TOON.
    2. Si saludable -> obtener JSON estructurado vía API.
    3. Si no saludable o falla -> usar fallback (NL crudo o JSON simple).
    4. Codificar JSON a TOON v4.1.
    5. Guardar en cache con metadatos.
    6. Reportar resultado como JSON stdout.

Uso CLI:
    python orchestrator.py --text "Crear un sistema de inventario"
    python orchestrator.py --text "API REST para gestión de usuarios" \
        --output-dir "eitl-artifacts/toon_cache"
    python orchestrator.py --text "Requisito" --model "qwen2.5-3b-instruct"
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.toon.api_gateway import get_structured_json
from scripts.toon.cache_manager import save as cache_save, load as cache_load
from scripts.toon.health_checker import check_health
from scripts.toon.to_toon import json_to_toon, ToonFormatOptions, ToonDelimiter

# Configuración de logging
LOG_DIR = Path("eitl-artifacts/toon_cache")
LOG_FILE = LOG_DIR / "orchestrator.log"

# Estructura EitL por defecto para fallback
EITL_FALLBACK = {
    "intent": "",
    "domain": "unknown",
    "entities": [],
    "actions": [],
    "constraints": [],
    "nfrs": [],
    "context": "",
    "scrum_artifacts": [],
}


def _setup_logging(log_file: Path) -> None:
    """Configura el sistema de logging para el orquestador.

    Crea un handler de archivo y consola con formato adecuado.

    Args:
        log_file: Ruta al archivo de log.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
    )


def _estimate_token_savings(
    nl_text: str,
    toon_text: str,
) -> float:
    """Estima el ahorro de tokens entre NL y TOON.

    Compara la longitud en tokens estimada del texto natural vs
    la salida TOON, retornando el porcentaje de ahorro.

    Args:
        nl_text: Texto natural de entrada.
        toon_text: Texto codificado en TOON.

    Returns:
        Porcentaje de ahorro de tokens (0-100).
    """
    # Estimación aproximada: ~4 caracteres por token
    nl_tokens = max(len(nl_text) / 4, 1)
    toon_tokens = max(len(toon_text) / 4, 1)

    if nl_tokens == 0:
        return 0.0

    savings = ((nl_tokens - toon_tokens) / nl_tokens) * 100
    return round(max(savings, 0), 1)


def _run_fallback(nl_text: str) -> dict[str, Any]:
    """Ejecuta el modo fallback cuando TOON no está disponible.

    Retorna una estructura JSON EitL básica con el texto natural crudo.

    Args:
        nl_text: Texto natural de entrada.

    Returns:
        Dict con resultado de fallback.
    """
    return {
        "intent": nl_text[:80],
        "domain": "unknown",
        "entities": [],
        "actions": [],
        "constraints": [],
        "nfrs": [],
        "context": nl_text,
        "scrum_artifacts": [],
    }


def orchestrate(
    nl_text: str,
    output_dir: str | Path = "eitl-artifacts/toon_cache",
    base_url: str = "http://192.168.2.111:8002/v1",
    model: str = "qwen2.5-3b-instruct",
    check_health_server: bool = True,
    max_retries: int = 3,
    ttl_hours: int = 24,
) -> dict[str, Any]:
    """Orquesta el pipeline completo: NL -> TOON.

    Verifica el servidor, obtiene JSON estructurado, codifica a TOON,
    guarda en cache y retorna el resultado.

    Args:
        nl_text: Texto natural de entrada (requisito o descripción).
        output_dir: Directorio de salida y cache.
        base_url: URL base del servidor TOON.
        model: Nombre del modelo a usar.
        check_health_server: Si True, verifica salud del servidor primero.
        max_retries: Número de reintentos para la API.
        ttl_hours: TTL de cache en horas.

    Returns:
        Dict con el resultado:
        - {"status": "ok", "toon_file": str, "json_file": str, "savings": float}
        - {"status": "fallback", "data": dict} en caso de fallback.
        - {"status": "error", "error": str} en caso de fallo total.
    """
    start_time = time.monotonic()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {}
    logger = logging.getLogger("orchestrator")

    try:
        # Paso 1: Verificar salud del servidor
        if check_health_server:
            logger.info("Paso 1: Verificando salud del servidor TOON")
            health = check_health(base_url=base_url)

            if health["status"] != "healthy":
                logger.warning(
                    "Servidor TOON no saludable: %s",
                    health.get("error", "desconocido"),
                )
                raise RuntimeError(f"Servidor no saludable: {health.get('error')}")

            health_latency = health.get("latency_ms", 0)
            logger.info("Servidor saludable - latencia: %d ms", health_latency)
        else:
            health_latency = 0

        # Paso 2: Obtener JSON estructurado desde la API
        logger.info("Paso 2: Obteniendo JSON estructurado desde la API")
        json_data = get_structured_json(
            nl_text=nl_text,
            base_url=base_url,
            model=model,
            max_retries=max_retries,
        )
        logger.info("JSON estructurado obtenido exitosamente")

        # Paso 3: Codificar JSON a TOON v4.1
        logger.info("Paso 3: Codificando JSON a TOON v4.1")
        toon_options = ToonFormatOptions(indent_size=2, delimiter=ToonDelimiter.COMMA)
        toon_text = json_to_toon(json_data, toon_options)
        logger.info("Codificación TOON completada")

        # Paso 4: Guardar en cache
        logger.info("Paso 4: Guardando en cache")
        cache_dir_path = str(output_path)

        metadata = {
            "model": model,
            "base_url": base_url,
            "health_latency_ms": health_latency,
        }

        session_dir = cache_save(
            toon_text=toon_text,
            json_data=json_data,
            nl_text=nl_text,
            cache_dir=cache_dir_path,
            ttl_hours=ttl_hours,
            metadata=metadata,
        )

        toon_file = str(Path(session_dir) / "output.toon")
        json_file = str(Path(session_dir) / "output.json")

        logger.info("Resultados guardados en: %s", session_dir)

        # Paso 5: Calcular métricas
        elapsed = time.monotonic() - start_time
        savings = _estimate_token_savings(nl_text, toon_text)

        result = {
            "status": "ok",
            "toon_file": toon_file,
            "json_file": json_file,
            "savings": savings,
            "cache_dir": session_dir,
            "latency_ms": health_latency,
            "processing_time_s": round(elapsed, 2),
            "toon_size_bytes": len(toon_text.encode("utf-8")),
            "json_size_bytes": len(json.dumps(json_data, ensure_ascii=False).encode("utf-8")),
            "input_length": len(nl_text),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            "Pipeline completado - Ahorro: %.1f%%, Tiempo: %.2fs",
            savings,
            elapsed,
        )

    except RuntimeError as exc:
        elapsed = time.monotonic() - start_time
        logger.warning("Fallo en pipeline, ejecutando fallback: %s", exc)

        fallback_data = _run_fallback(nl_text)
        result = {
            "status": "fallback",
            "data": fallback_data,
            "reason": str(exc),
            "processing_time_s": round(elapsed, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        elapsed = time.monotonic() - start_time
        logger.error("Error inesperado en el pipeline: %s", exc, exc_info=True)

        fallback_data = _run_fallback(nl_text)
        result = {
            "status": "error",
            "error": str(exc),
            "data": fallback_data,
            "processing_time_s": round(elapsed, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return result


def main() -> int:
    """Punto de entrada CLI principal.

    Parsea argumentos de línea de comandos y ejecuta el orquestador.

    Returns:
        Código de salida: 0 en éxito, 1 en fallo.
    """
    parser = argparse.ArgumentParser(
        description="TOON Orchestrator Gateway - Convierte texto natural a TOON v4.1",
        prog="orchestrator.py",
    )
    parser.add_argument(
        "--text",
        required=True,
        help="Texto natural de entrada (requisito o descripción)",
    )
    parser.add_argument(
        "--output-dir",
        default="eitl-artifacts/toon_cache",
        help="Directorio de salida y cache (por defecto: eitl-artifacts/toon_cache)",
    )
    parser.add_argument(
        "--base-url",
        default="http://192.168.2.111:8002/v1",
        help="URL base del servidor TOON (por defecto: http://192.168.2.111:8002/v1)",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5-3b-instruct",
        help="Nombre del modelo (por defecto: qwen2.5-3b-instruct)",
    )
    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="Omitir verificación de salud del servidor",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Número máximo de reintentos (por defecto: 3)",
    )
    parser.add_argument(
        "--ttl-hours",
        type=int,
        default=24,
        help="TTL de cache en horas (por defecto: 24)",
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="No usar fallback en caso de error (salir con código 1)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Activar logging verbose (stderr)",
    )

    args = parser.parse_args()

    # Configurar logging
    _setup_logging(LOG_FILE)
    logger = logging.getLogger("orchestrator")

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("TOON Orchestrator Gateway v3")
    logger.info("=" * 60)
    logger.info("Texto de entrada: %s", args.text[:100])
    logger.info("Directorio de salida: %s", args.output_dir)
    logger.info("Modelo: %s", args.model)
    logger.info("Base URL: %s", args.base_url)

    # Ejecutar orquestador
    result = orchestrate(
        nl_text=args.text,
        output_dir=args.output_dir,
        base_url=args.base_url,
        model=args.model,
        check_health_server=not args.skip_health_check,
        max_retries=args.max_retries,
        ttl_hours=args.ttl_hours,
    )

    # Output final a stdout como JSON
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Código de salida
    if result.get("status") == "ok":
        logger.info("Pipeline exitoso")
        return 0
    elif result.get("status") == "fallback":
        logger.warning("Pipeline completado con fallback")
        if args.no_fallback:
            return 1
        return 0
    else:
        logger.error("Pipeline falló: %s", result.get("error", "desconocido"))
        return 1


if __name__ == "__main__":
    sys.exit(main())

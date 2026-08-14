"""EitL Framework v3 - Comprobador de salud del servidor TOON.

Verifica si el servidor TOON (qwen2.5-3b-instruct) es alcanzable y responde
dentro del tiempo esperado. Útil para decisiones de fallback en el orquestador.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Create a session that ignores system proxy settings
_session = requests.Session()
_session.trust_env = False

DEFAULT_BASE_URL = "http://192.168.2.111:8002/v1"
DEFAULT_TIMEOUT = 3.0


def check_health(
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Comprueba la salud del servidor TOON.

    Intenta acceder al endpoint /models (compatible OpenAI API) para verificar
    que el servidor está activo y responde dentro del tiempo especificado.

    Args:
        base_url: URL base del servidor TOON.
        timeout: Tiempo máximo de espera en segundos (por defecto: 3).

    Returns:
        Dict con el resultado:
        - {"status": "healthy", "latency_ms": int} si el servidor responde.
        - {"status": "unhealthy", "error": str} si falla la conexión.
    """
    models_url = f"{base_url}/models"

    try:
        logger.info("Comprobando salud de TOON en %s", models_url)

        resp = _session.get(models_url, timeout=timeout)
        resp.raise_for_status()

        latency_ms = int(resp.elapsed.total_seconds() * 1000)

        logger.info("TOON saludable - latencia: %d ms", latency_ms)

        return {"status": "healthy", "latency_ms": latency_ms}

    except requests.exceptions.Timeout as exc:
        error_msg = f"Timeout al conectar con TOON ({timeout}s)"
        logger.warning(error_msg)
        return {"status": "unhealthy", "error": error_msg}

    except requests.exceptions.ConnectionError as exc:
        error_msg = f"Error de conexión con TOON: {exc}"
        logger.warning(error_msg)
        return {"status": "unhealthy", "error": error_msg}

    except requests.exceptions.HTTPError as exc:
        error_msg = f"Error HTTP del servidor TOON: {exc}"
        logger.warning(error_msg)
        return {"status": "unhealthy", "error": error_msg}

    except requests.exceptions.RequestException as exc:
        error_msg = f"Error de solicitud al verificar TOON: {exc}"
        logger.warning(error_msg)
        return {"status": "unhealthy", "error": error_msg}

    except Exception as exc:
        error_msg = f"Error inesperado al verificar TOON: {exc}"
        logger.error(error_msg)
        return {"status": "unhealthy", "error": error_msg}

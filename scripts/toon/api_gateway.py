"""EitL Framework v3 - Gateway de API para el modelo TOON.

Maneja la comunicación con el modelo pequeño (qwen2.5-3b-instruct)
vía la API compatible con OpenAI. Incluye lógica de reintentos y
forzado de salida JSON estructurada.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Create a session that ignores system proxy settings
_session = requests.Session()
_session.trust_env = False

DEFAULT_BASE_URL = "http://192.168.2.111:8002/v1"
DEFAULT_MODEL = "qwen2.5-3b-instruct"
COMPLETIONS_ENDPOINT = f"{DEFAULT_BASE_URL}/chat/completions"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0

SYSTEM_PROMPT = (
    "Eres un analista de requisitos que convierte texto natural en estructuras JSON "
    "según el esquema EitL. Devuelve SOLO un objeto JSON válido, sin markdown, "
    "sin explicaciones, sin texto adicional.\n\n"
    "El JSON debe tener exactamente estas claves de nivel superior:\n"
    "- \"intent\": string - objetivo principal del requisito\n"
    "- \"domain\": string - dominio al que pertenece\n"
    "- \"entities\": array de objetos con \"name\" (string) y \"type\" (string)\n"
    "- \"actions\": array de strings - acciones identificadas\n"
    "- \"constraints\": array de objetos con \"type\" (string) y \"description\" (string)\n"
    "- \"nfrs\": array de objetos con \"category\" (string) y \"description\" (string)\n"
    "- \"context\": string - contexto del requisito\n"
    "- \"scrum_artifacts\": array de strings - artefactos scrum relacionados\n\n"
    "Ejemplo de estructura:\n"
    "{\n"
    '  "intent": "Crear un sistema de autenticación",\n'
    '  "domain": "seguridad",\n'
    '  "entities": [{"name": "usuario", "type": "persona"}, {"name": "token", "type": "dato"}],\n'
    '  "actions": ["autenticar", "validar token", "rotar credenciales"],\n'
    '  "constraints": [{"type": "security", "description": "MFA obligatorio"}],\n'
    '  "nfrs": [{"category": "performance", "description": "Login en < 200ms"}],\n'
    '  "context": "Sistema web corporativo",\n'
    '  "scrum_artifacts": ["user story", "acceptance criteria"]\n'
    "}\n\n"
    "Devuelve SOLO el JSON. Nada más."
)


def _build_request_payload(nl_text: str) -> dict[str, Any]:
    """Construye la carga útil de la petición para la API de chat.

    Args:
        nl_text: Texto natural de entrada (requisito, descripción, etc.).

    Returns:
        Dict con la estructura de la petición HTTP para OpenAI-compatible API.
    """
    return {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": nl_text},
        ],
        "max_tokens": 4096,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }


def get_structured_json(
    nl_text: str,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
) -> dict[str, Any]:
    """Envía texto natural al modelo y obtiene JSON estructurado EitL.

    Envía el texto al endpoint de chat completions con un prompt estricto
    para forzar salida JSON. Incluye lógica de reintentos para manejar
    errores transitorios.

    Args:
        nl_text: Texto natural de entrada (requisito o descripción).
        base_url: URL base de la API (por defecto: http://192.168.2.111:8002/v1).
        model: Nombre del modelo a usar (por defecto: qwen2.5-3b-instruct).
        timeout: Tiempo máximo de espera por petición en segundos (por defecto: 30).
        max_retries: Número máximo de reintentos (por defecto: 3).
        retry_delay: Segundos de espera entre reintentos (por defecto: 1).

    Returns:
        Dict con el JSON estructurado EitL.

    Raises:
        requests.exceptions.RequestException: Si la API falla después de reintentos.
        json.JSONDecodeError: Si la respuesta no contiene JSON válido.
        ValueError: Si el JSON no tiene la estructura EitL esperada.
    """
    completions_url = f"{base_url}/chat/completions"

    payload = _build_request_payload(nl_text)

    last_error: str = ""
    last_result: dict | None = None

    for attempt in range(1, max_retries + 1):
        logger.info(
            "Petición al modelo %s (intento %d/%d)",
            model,
            attempt,
            max_retries,
        )

        try:
            resp = _session.post(
                completions_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=timeout,
            )

            if resp.status_code != 200:
                error_msg = f"Error HTTP {resp.status_code}: {resp.text[:200]}"
                logger.warning("Intento %d falló: %s", attempt, error_msg)
                last_error = error_msg
                if attempt < max_retries:
                    time.sleep(retry_delay)
                continue

            response_data = resp.json()

            # Extraer el contenido del primer choice
            if "choices" not in response_data or len(response_data["choices"]) == 0:
                error_msg = "Respuesta sin choices"
                logger.warning("Intento %d falló: %s", attempt, error_msg)
                last_error = error_msg
                if attempt < max_retries:
                    time.sleep(retry_delay)
                continue

            content = response_data["choices"][0].get("message", {}).get("content", "")

            if not content:
                error_msg = "Respuesta sin contenido"
                logger.warning("Intento %d falló: %s", attempt, error_msg)
                last_error = error_msg
                if attempt < max_retries:
                    time.sleep(retry_delay)
                continue

            # Extraer JSON del contenido
            json_str = _extract_json(content)
            json_data = json.loads(json_str)

            # Validar estructura EitL
            _validate_eitl_structure(json_data)

            logger.info("JSON estructurado exitoso (intento %d)", attempt)
            return json_data

        except requests.exceptions.Timeout:
            error_msg = f"Timeout en intento {attempt}/{max_retries}"
            logger.warning(error_msg)
            last_error = error_msg
            if attempt < max_retries:
                time.sleep(retry_delay)
            continue

        except requests.exceptions.ConnectionError as exc:
            error_msg = f"Error de conexión en intento {attempt}: {exc}"
            logger.warning(error_msg)
            last_error = error_msg
            if attempt < max_retries:
                time.sleep(retry_delay)
            continue

        except json.JSONDecodeError as exc:
            error_msg = f"JSON inválido en intento {attempt}: {exc}"
            logger.warning(error_msg)
            last_error = error_msg
            if attempt < max_retries:
                time.sleep(retry_delay)
            continue

        except requests.exceptions.RequestException as exc:
            error_msg = f"Error de HTTP en intento {attempt}: {exc}"
            logger.warning(error_msg)
            last_error = error_msg
            if attempt < max_retries:
                time.sleep(retry_delay)
            continue

    error_msg = f"Agotados {max_retries} intentos. Último error: {last_error}"
    logger.error(error_msg)
    raise requests.exceptions.RequestException(error_msg)


def _extract_json(content: str) -> str:
    """Extrae un string JSON del contenido de la respuesta.

    Maneja casos donde el modelo incluye markdown (```json ... ```)
    o texto adicional alrededor del JSON.

    Args:
        content: Contenido string del campo message del modelo.

    Returns:
        String JSON válido extraído.

    Raises:
        ValueError: Si no se puede extraer JSON del contenido.
    """
    stripped = content.strip()

    # Buscar bloque JSON markdown
    if "```" in stripped:
        start_marker = stripped.find("```json")
        if start_marker == -1:
            start_marker = stripped.find("```")
        if start_marker != -1:
            end_marker = stripped.find("```", start_marker + 3)
            if end_marker != -1:
                candidate = stripped[start_marker + 3:end_marker].strip()
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    pass

    # Si parece JSON directamente
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            json.loads(stripped)
            return stripped
        except json.JSONDecodeError:
            pass

    # Buscar primer objeto JSON válido dentro del texto
    brace_start = stripped.find("{")
    if brace_start != -1:
        brace_count = 0
        for i in range(brace_start, len(stripped)):
            if stripped[i] == "{":
                brace_count += 1
            elif stripped[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    candidate = stripped[brace_start:i + 1].strip()
                    try:
                        json.loads(candidate)
                        return candidate
                    except json.JSONDecodeError:
                        continue

    raise ValueError(f"No se pudo extraer JSON del contenido: {content[:200]}")


def _validate_eitl_structure(data: dict[str, Any]) -> None:
    """Valida que el JSON tenga la estructura EitL requerida.

    Verifica que existan las claves core del esquema EitL.
    Las claves opcionales se rellenan con valores por defecto.

    Args:
        data: Dict JSON a validar.

    Raises:
        ValueError: Si falta alguna clave core del esquema EitL.
    """
    # Core keys (required)
    core_keys = {"intent", "domain", "entities", "actions"}
    
    # Optional keys (will be filled with defaults if missing)
    optional_keys = {
        "constraints": [],
        "nfrs": [],
        "context": "",
        "scrum_artifacts": []
    }

    missing_core = core_keys - set(data.keys())
    if missing_core:
        raise ValueError(
            f"JSON incompleto. Faltan claves core: {', '.join(sorted(missing_core))}"
        )
    
    # Fill in optional keys with defaults
    for key, default_value in optional_keys.items():
        if key not in data:
            data[key] = default_value

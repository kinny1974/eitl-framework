"""EitL Framework v3 - Gestor de cache para resultados TOON.

Administra el almacenamiento y recuperación de resultados del pipeline
TOON (texto TOON + JSON estructurado). Incluye indexación, expiración
por TTL y limpieza de entradas antiguas.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = "eitl-artifacts/toon_cache"
DEFAULT_TTL_HOURS = 24
MAX_ENV_VAR = "TOON_CACHE_MAX_SIZE"
DEFAULT_MAX_SIZE = 100


def _get_index_path(cache_dir: Path) -> Path:
    """Obtiene la ruta al índice de cache.

    Args:
        cache_dir: Directorio base de cache.

    Returns:
        Ruta al archivo index.json.
    """
    return cache_dir / "index.json"


def _load_index(cache_dir: Path) -> dict[str, Any]:
    """Carga el índice de cache desde disco.

    Args:
        cache_dir: Directorio base de cache.

    Returns:
        Dict con el índice actual. Si no existe, retorna dict vacío.
    """
    index_path = _get_index_path(cache_dir)
    if not index_path.exists():
        return {}

    try:
        content = index_path.read_text(encoding="utf-8")
        return json.loads(content)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Índice corrupto, reiniciando: %s", exc)
        return {}


def _save_index(cache_dir: Path, index: dict[str, Any]) -> None:
    """Guarda el índice de cache en disco.

    Args:
        cache_dir: Directorio base de cache.
        index: Dict con la información de entradas de cache.
    """
    index_path = _get_index_path(cache_dir)
    try:
        index_path.write_text(
            json.dumps(index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.error("Error al guardar índice: %s", exc)
        raise


def _generate_cache_key(nl_text: str) -> str:
    """Genera una clave única para una entrada de cache.

    Usa un hash MD5 del texto natural sanitizado.

    Args:
        nl_text: Texto natural de entrada.

    Returns:
        Clave hash de 16 caracteres para la entrada.
    """
    import hashlib

    sanitized = nl_text.strip().lower().replace(" ", "_").replace("/", "_")
    return hashlib.md5(sanitized.encode("utf-8")).hexdigest()[:16]


def _cleanup_old_entries(cache_dir: Path, max_size: Optional[int] = None) -> None:
    """Elimina las entradas más antiguas si se excede el tamaño máximo.

    Compara el número de entradas en el índice con TOON_CACHE_MAX_SIZE
    (de variable de entorno o valor por defecto). Si se excede, elimina
    las entradas con timestamp más antiguo.

    Args:
        cache_dir: Directorio base de cache.
        max_size: Tamaño máximo de cache. Si es None, usa variable de entorno
            o DEFAULT_MAX_SIZE.
    """
    import os

    if max_size is None:
        max_size = int(os.environ.get(MAX_ENV_VAR, DEFAULT_MAX_SIZE))

    index = _load_index(cache_dir)
    current_size = len(index)

    if current_size <= max_size:
        return

    # Ordenar por timestamp y eliminar las más antiguas
    sorted_entries = sorted(
        index.items(),
        key=lambda item: item[1].get("timestamp", 0),
    )

    to_remove = sorted_entries[: current_size - max_size]

    for entry_key, entry_data in to_remove:
        cache_file = entry_data.get("toon_file")
        if cache_file and Path(cache_file).exists():
            try:
                Path(cache_file).unlink()
                logger.info("Eliminando entrada de cache antigua: %s", entry_key)
            except OSError as exc:
                logger.warning("Error eliminando archivo %s: %s", cache_file, exc)

        json_file = entry_data.get("json_file")
        if json_file and Path(json_file).exists():
            try:
                Path(json_file).unlink()
            except OSError as exc:
                logger.warning("Error eliminando archivo %s: %s", json_file, exc)

    # Limpiar el índice
    for entry_key, _ in to_remove:
        del index[entry_key]

    _save_index(cache_dir, index)


def save(
    toon_text: str,
    json_data: dict[str, Any],
    nl_text: str = "",
    cache_dir: str | Path = DEFAULT_CACHE_DIR,
    ttl_hours: int = DEFAULT_TTL_HOURS,
    metadata: Optional[dict[str, Any]] = None,
) -> str:
    """Guarda un resultado TOON en el cache.

    Crea un directorio de sesión con timestamp, guarda los archivos
    TOON y JSON, y actualiza el índice de cache con metadatos.

    Args:
        toon_text: Texto codificado en formato TOON v4.1.
        json_data: Dict con el JSON estructurado EitL.
        nl_text: Texto natural de entrada (para generar clave de cache).
        cache_dir: Directorio de cache (por defecto: eitl-artifacts/toon_cache).
        ttl_hours: Tiempo de vida en horas antes de expirar (por defecto: 24).
        metadata: Dict con metadatos adicionales (timestamp, modelo, etc.).

    Returns:
        Ruta al directorio de cache de la sesión.

    Raises:
        OSError: Si no se pueden escribir los archivos.
    """
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    cache_key = _generate_cache_key(nl_text) if nl_text else str(int(time.time()))

    timestamp = int(time.time())
    expires_at = timestamp + (ttl_hours * 3600)

    session_dir = cache_path / cache_key
    session_dir.mkdir(parents=True, exist_ok=True)

    # Guardar TOON
    toon_file = session_dir / "output.toon"
    toon_file.write_text(toon_text, encoding="utf-8")

    # Guardar JSON
    json_file = session_dir / "output.json"
    json_file.write_text(
        json.dumps(json_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Construir metadatos
    entry_meta: dict[str, Any] = {
        "toon_file": str(toon_file),
        "json_file": str(json_file),
        "timestamp": timestamp,
        "expires_at": expires_at,
        "ttl_hours": ttl_hours,
        "toon_size": len(toon_text),
        "json_size": len(json.dumps(json_data, ensure_ascii=False, indent=2)),
    }

    if nl_text:
        entry_meta["nl_text"] = nl_text

    if metadata:
        entry_meta.update(metadata)

    # Actualizar índice
    index = _load_index(cache_path)
    index[cache_key] = entry_meta
    _save_index(cache_path, index)

    # Limpieza opcional si se excede el tamaño
    try:
        _cleanup_old_entries(cache_path)
    except Exception as exc:
        logger.warning("Error en limpieza de cache: %s", exc)

    logger.info("Resultado cacheado en: %s", session_dir)
    return str(session_dir)


def load(
    key: str,
    cache_dir: str | Path = DEFAULT_CACHE_DIR,
) -> Tuple[str, dict[str, Any]] | None:
    """Recupera un resultado cacheado por clave.

    Verifica que la entrada no haya expirado (TTL) antes de retornarla.

    Args:
        key: Clave de cache generada por _generate_cache_key.
        cache_dir: Directorio de cache (por defecto: eitl-artifacts/toon_cache).

    Returns:
        Tupla (toon_text, json_data) si se encuentra y no ha expirado.
        None si no existe la entrada o ha expirado.
    """
    cache_path = Path(cache_dir)
    index = _load_index(cache_path)

    entry = index.get(key)
    if not entry:
        logger.debug("Entrada no encontrada en cache: %s", key)
        return None

    # Verificar TTL
    expires_at = entry.get("expires_at", 0)
    current_time = int(time.time())
    if current_time > expires_at:
        logger.info("Entrada expirada en cache: %s", key)
        # Eliminar entrada expirada
        toon_file = entry.get("toon_file")
        if toon_file and Path(toon_file).exists():
            try:
                Path(toon_file).unlink()
            except OSError:
                pass
        json_file = entry.get("json_file")
        if json_file and Path(json_file).exists():
            try:
                Path(json_file).unlink()
            except OSError:
                pass
        del index[key]
        _save_index(cache_path, index)
        return None

    # Leer archivos
    toon_file = entry.get("toon_file")
    json_file = entry.get("json_file")

    if not toon_file or not json_file:
        logger.warning("Entrada corrupta (sin archivos): %s", key)
        del index[key]
        _save_index(cache_path, index)
        return None

    try:
        toon_text = Path(toon_file).read_text(encoding="utf-8")
    except OSError as exc:
        logger.error("Error leyendo TOON cache: %s", exc)
        return None

    try:
        json_content = Path(json_file).read_text(encoding="utf-8")
        json_data = json.loads(json_content)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Error leyendo JSON cache: %s", exc)
        return None

    logger.debug("Entrada recuperada de cache: %s", key)
    return (toon_text, json_data)


def clear_cache(
    cache_dir: str | Path = DEFAULT_CACHE_DIR,
) -> int:
    """Elimina todas las entradas del cache.

    Args:
        cache_dir: Directorio de cache (por defecto: eitl-artifacts/toon_cache).

    Returns:
        Número de entradas eliminadas.
    """
    cache_path = Path(cache_dir)
    index = _load_index(cache_path)
    count = len(index)

    for entry_key, entry_data in index.items():
        toon_file = entry_data.get("toon_file")
        if toon_file and Path(toon_file).exists():
            try:
                Path(toon_file).unlink()
            except OSError:
                pass
        json_file = entry_data.get("json_file")
        if json_file and Path(json_file).exists():
            try:
                Path(json_file).unlink()
            except OSError:
                pass

    # Eliminar directorios de sesión
    for child in cache_path.iterdir():
        if child.is_dir():
            try:
                import shutil
                shutil.rmtree(child)
            except OSError:
                pass

    # Eliminar índice
    index_path = _get_index_path(cache_path)
    if index_path.exists():
        try:
            index_path.unlink()
        except OSError:
            pass

    logger.info("Cache limpiado: %d entradas eliminadas", count)
    return count

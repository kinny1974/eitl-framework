"""EitL Framework v3 - Utilidades TOON v4.1.

Conversores y procesadores para el formato TOON (Token-Oriented Object Notation).
Orquestador gateway para el pipeline NL -> Small Model -> JSON -> TOON.
"""

__version__ = "4.1.0"
__author__ = "EitL Framework Team"

# Conversores TOON
from scripts.toon.to_toon import json_to_toon, ToonEncoder, ToonFormatOptions
from scripts.toon.to_json import toon_to_json, ToonDecoder

# Gateway y orquestador
from scripts.toon.health_checker import check_health
from scripts.toon.api_gateway import get_structured_json
from scripts.toon.cache_manager import save as cache_save, load as cache_load
from scripts.toon.orchestrator import orchestrate, main

__all__ = [
    # Conversores
    "json_to_toon",
    "toon_to_json",
    "ToonEncoder",
    "ToonDecoder",
    "ToonFormatOptions",
    # Gateway
    "check_health",
    "get_structured_json",
    # Cache
    "cache_save",
    "cache_load",
    # Orquestador
    "orchestrate",
    "main",
]

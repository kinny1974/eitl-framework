# EitL Framework v3 - Utilidades TOON v4.1

Conjunto de herramientas para convertir entre JSON y TOON (Token-Oriented Object Notation) v4.1, y un pipeline completo para convertir texto natural a TOON vía modelo de lenguaje.

## Formato TOON

TOON es un formato orientado a tokens para datos JSON-shaped, diseñado para eficiencia de tokens en prompts LLM. Declarar formas de arrays una vez (longitud y campos) y usar indentación en lugar de llaves reduce significativamente el tamaño del texto.

Ejemplo:

```
# JSON
{"users": [{"id": 1, "name": "Ada", "role": "admin"}, {"id": 2, "name": "Bob", "role": "user"}]}

# TOON equivalente
users[2]{id,name,role}:
  1,Ada,admin
  2,Bob,user
```

## Instalación

```bash
pip install -r scripts/toon/requirements.txt
```

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `to_toon.py` | Codificador JSON -> TOON v4.1 |
| `to_json.py` | Decodificador TOON v4.1 -> JSON |
| `nl_processor.py` | Pipeline NL -> Modelo -> JSON -> TOON |

## Uso

### JSON a TOON

```bash
python scripts/toon/to_toon.py entrada.json
python scripts/toon/to_toon.py entrada.json -o salida.toon
python scripts/toon/to_toon.py entrada.json --indent 4 --delimiter pipe
```

Programático:

```python
from scripts.toon.to_toon import json_to_toon, ToonFormatOptions, ToonDelimiter

data = {"users": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]}
toon_str = json_to_toon(data)
print(toon_str)
```

### TOON a JSON

```bash
python scripts/toon/to_json.py entrada.toon
python scripts/toon/to_json.py entrada.toon -o salida.json
```

Programático:

```python
from scripts.toon.to_json import toon_to_json

toon_str = open("entrada.toon").read()
json_str = toon_to_json(toon_str)
print(json_str)
```

### Pipeline NL a TOON

```bash
python scripts/toon/nl_processor.py "Crear una lista de usuarios con id, nombre y rol"
python scripts/toon/nl_processor.py "Requisito: sistema de inventario" -u http://localhost:8080/v1
```

Programático:

```python
from scripts.toon.nl_processor import nl_to_toon, NLPipelineConfig

config = NLPipelineConfig(
    model_url="http://192.168.2.111:8002/v1",
    model_name="small-model",
)
result = nl_to_toon("Crear una lista de productos", config)
print(result.toon_output)
print(result.json_response)
```

## Formas TOON Soportadas

### Tabular (arrays de objetos uniformes)

```
items[2]{sku,qty,price}:
  A1,2,9.99
  B2,1,14.5
```

### Keyed Tabular (objetos de objetos uniformes)

```
users[2:]{age,city}:
  alice: 30,Berlin
  bob: 25,Oslo
```

### Inline (arrays de primitivos)

```
tags[3]: admin,ops,dev
```

### List (arrays mixtos)

```
items[3]:
  - 1
  - a: 1
  - texto
```

### Nested (objetos anidados)

```
user:
  id: 123
  name: Ada
  address:
    city: Berlin
    country: DK
```

## Opciones de Formato

| Opción | Descripción | Por defecto |
|--------|-------------|-------------|
| `indent_size` | Espacios por nivel | 2 |
| `delimiter` | Delimitador (comma/tab/pipe) | comma |
| `sort_keys` | Ordenar claves | False |
| `strict` | Modo estricto de validación | True |

## Estructura del Paquete

```
scripts/toon/
    __init__.py          # Inicialización del paquete
    to_toon.py           # Codificador JSON -> TOON
    to_json.py           # Decodificador TOON -> JSON
    nl_processor.py      # Pipeline NL -> TOON
    requirements.txt     # Dependencias
    README.md            # Esta documentación
```

## Especificación

Esta implementación sigue la especificación TOON v4.1:
- [SPEC.md](C:\cnm-dev\samples\SPEC.md) - Especificación completa del formato

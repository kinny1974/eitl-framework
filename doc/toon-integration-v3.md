# EitL Framework v3 - Integración TOON v4.1

**Token-Oriented Object Notation: Especificación de Integración**

| Campo | Valor |
|-------|-------|
| Versión | 3.0 |
| TOON | v4.1 |
| Autor | Johann Schopplich (TOON) / Equipo EitL (integración) |
| Estado | Producción |
| Fecha | 2026-08-13 |

---

## Tabla de Contenidos

1. [Visión General](#1-visión-general)
2. [Arquitectura](#2-arquitectura)
3. [Orchestrator Gateway Architecture](#3-orchestrator-gateway-architecture)
4. [Formato TOON - Ejemplos](#4-formato-toon---ejemplos)
5. [Calculadora de Ahorro de Tokens](#5-calculadora-de-ahorro-de-tokens)
6. [Utilidades Python](#6-utilidades-python)
7. [Configuración](#7-configuración)
8. [Integración con Pipeline Existente](#8-integración-con-pipeline-existente)
9. [Referencia](#9-referencia)

---

## 1. Visión General

TOON (Token-Oriented Object Notation) v4.1 es un formato de texto eficiente en tokens para datos con forma JSON, diseñado principalmente para prompts y contextos de LLM donde cada token tiene costo. Escribyo Johann Schopplich, TOON declara la forma de arrays una sola vez (longitud y lista de campos opcional) y usa indentación en lugar de llaves.

EitL Framework v3 utiliza TOON como capa de traducción en su pipeline:

```
Lenguaje Natural → JSON estructurado → TOON → Main Model
```

Cada token cuesta; TOON ahorra ~30-50% de tokens vs JSON equivalente para datos estructurados.

### Objetivos de la integración

- Reducir el costo de inferencia al minimizar tokens en prompts de contexto
- Mantener compatibilidad total con el modelo JSON data model (RFC 8259)
- Proveer un formato intermedio legible por humanos y machines
- Optimizar especialmente arrays de objetos uniformes (el mayor ahorro)

### Casos de uso en EitL

- Codificación de artifacts del pipeline (plan, arquitectura, tests, QA)
- Representación del equipo de agentes (scrum-master, architect, tdd-engineer, validator)
- Serialización de estados de memoria compacta
- Optimización de contexto para el Main Model (qwen3.6-35b-128k)

---

## 2. Arquitectura

El pipeline TOON en EitL Framework v3 sigue este flujo:

```
Usuario (NL)
    ↓
TOON Translator Agent (qwen2.5-3b @ 192.168.2.111:8002/v1)
    ↓  structured JSON
TOON Encoder (Python utility)
    ↓  compact TOON text
Main Model (qwen3.6-35b-128k)
    ↓  response
TOON Decoder (Python utility)
    ↓  JSON response
Scrum Master → Pipeline Agents
```

### Componentes

#### 2.1 TOON Translator Agent

- **Modelo:** qwen2.5-3b-instruct
- **Endpoint:** `http://192.168.2.111:8002/v1`
- **Responsabilidad:** Convertir requisitos en lenguaje natural a JSON estructurado
- **Input:** Texto del usuario en NL (lenguaje natural)
- **Output:** JSON con estructura definida por el pipeline EitL

Este agente es el primer punto de contacto del pipeline. Recibe los requisitos del usuario y genera JSON estructurado que sirve como entrada para el encoder TOON.

#### 2.2 TOON Encoder

- **Tipo:** Utilidad Python (`scripts/toon/to_toon.py`)
- **Responsabilidad:** Convertir JSON → TOON compacto
- **Input:** JSON estructurado desde el Translator Agent
- **Output:** Texto TOON v4.1 con indentación de 2 espacios, delimitador comma

El encoder aplica las reglas de codificación de TOON v4.1 (especificación en `C:\cnm-dev\samples\SPEC.md`):

- Arrays de objetos uniformes → tabular form (mayor ahorro)
- Strings con caracteres estructurales → quoted
- Números en forma canonical decimal
- Indentación de 2 espacios por nivel
- Sin llaves ni corchetes para objetos/anidados

#### 2.3 Main Model

- **Modelo:** qwen3.6-35b-128k
- **Responsabilidad:** Procesar el contexto TOON-optimizado y generar respuestas
- **Input:** Texto TOON compacto (contexto optimizado en tokens)
- **Output:** Texto que el Decoder convierte a JSON

Al recibir menos tokens en el prompt (gracias a TOON), el Main Model opera con mayor eficiencia y menor costo.

#### 2.4 TOON Decoder

- **Tipo:** Utilidad Python (`scripts/toon/to_json.py`)
- **Responsabilidad:** Convertir texto TOON → JSON
- **Input:** Respuesta en formato TOON del Main Model
- **Output:** JSON para consumo por Scrum Master y Pipeline Agents

El decoder aplica las reglas de decodificación de TOON v4.1, incluyendo strict mode por defecto.

---

## 3. Orchestrator Gateway Architecture

### 3.1 Descripción General

En EitL Framework v3, OpenCode **delega** el procesamiento TOON a un servicio Python externo (`scripts/toon/orchestrator.py`). Esta arquitectura de **Orchestrator Gateway** proporciona resiliencia, health checks, logging estructurado y fallback automático, evitando que fallos en el servidor TOON (192.168.2.111:8002) afecten directamente al pipeline principal.

El orchestrator actúa como una capa intermedia que gestiona el ciclo de vida completo de las solicitudes TOON: validación del servidor, comunicación con el modelo pequeño, codificación/decodificación y caché de resultados.

### 3.2 Flujo de Datos

```
Usuario (NL)
    ↓
TOON Translator Agent (OpenCode Subagent)
    ↓  CLI Call
orchestrator.py (Python Gateway)
    ├── health_checker.py    (Valida servidor 192.168.2.111:8002)
    ├── api_gateway.py       (Llama a qwen2.5-3b si está healthy)
    ├── to_toon.py           (Codifica JSON → TOON v4.1)
    └── cache_manager.py     (Guarda en eitl-artifacts/toon_cache/)
    ↓  Resultado JSON stdout
Main Model / Scrum Master
```

### 3.3 Componentes del Gateway

#### 3.3.1 `orchestrator.py` — Puerta de Enlace Principal

- **Responsabilidad:** Orquestar el ciclo de vida de cada solicitud TOON
- **Entrada:** Texto en NL desde el TOON Translator Agent (OpenCode Subagent)
- **Salida:** Resultado JSON codificado en stdout para el Main Model
- **Gestión:** Inicia/termina procesos, maneja reintentos y fallback

El orchestrator es el punto de entrada único para todas las operaciones TOON. Coordina los sub-componentes en secuencia: health check → API call → encoding → caching.

#### 3.3.2 `health_checker.py` — Validación de Disponibilidad

- **Responsabilidad:** Verificar que el servidor TOON (192.168.2.111:8002) esté disponible
- **Método:** HTTP health probe con timeout configurable
- **Fallback:** Si el servidor no responde, retorna estado `UNHEALTHY` sin llamar al modelo
- **Cache de salud:** Resultado del health check se mantiene por 30 segundos para evitar probes excesivos

```python
# Ejemplo de validación
health = health_checker.check("http://192.168.2.111:8002/v1/health")
if health.is_healthy:
    # Proceder con la llamada API
else:
    # Fallback: usar caché o retornar error estructurado
```

#### 3.3.3 `api_gateway.py` — Comunicación con Modelo Pequeño

- **Responsabilidad:** Manejar la comunicación con qwen2.5-3b (con reintentos automáticos)
- **Endpoint:** `http://192.168.2.111:8002/v1/chat/completions`
- **Reintentos:** Máximo 3 intentos con backoff exponencial
- **Timeout:** 15 segundos por request, 60 segundos para retry total
- **Error Handling:** Si falla después de reintentos, retorna error JSON estructurado para fallback

```python
# Ejemplo de llamada con retries
result = api_gateway.call_with_retries(
    endpoint="http://192.168.2.111:8002/v1/chat/completions",
    payload=natural_language_text,
    max_retries=3,
    backoff_factor=2.0
)
```

#### 3.3.4 `to_toon.py` — Codificación JSON → TOON v4.1

- **Responsabilidad:** Convertir JSON estructurado a texto TOON compacto
- **Entrada:** JSON desde `api_gateway.py` (respuesta del qwen2.5-3b)
- **Output:** Texto TOON v4.1 optimizado para el Main Model
- **Reglas:** Arrays tabulares, field lists declaradas una sola vez, quoting mínimo

#### 3.3.5 `cache_manager.py` — Gestión de Caché

- **Responsabilidad:** Guardar resultados de procesamiento TOON para reutilización
- **Directorio:** `eitl-artifacts/toon_cache/`
- **Strategia:** Keyed by input hash (SHA-256 del texto NL de entrada)
- **TTL:** 24 horas por defecto para entradas no críticas, infinito para artifacts del pipeline
- **Hit detection:** Si la misma entrada se repite, se retorna caché sin llamar al modelo

```python
# Ejemplo de uso
cache_key = hash(input_nl_text)
cached_result = cache_manager.get(cache_key)
if cached_result:
    return cached_result  # Hit → sin llamar al modelo
cache_manager.set(cache_key, result, ttl=86400)
```

### 3.4 Comparativa: Direct Call vs Orchestration Gateway

| Característica | Direct Call (Old) | Orchestration Gateway (New) |
|----------------|-------------------|-----------------------------|
| **Resiliencia** | Sin protección — fallo del servidor = fallo del pipeline | Health checks + reintentos + fallback automático |
| **Logging** | Mínimo — solo stdout del modelo | Estructurado por componente (health, API, cache, encoding) |
| **Fallback** | No disponible | Caché de resultados, estado UNHEALTHY, error estructurado |
| **Reintentos** | No disponibles | 3 intentos con backoff exponencial (api_gateway.py) |
| **Caché** | No disponible | SHA-256 keyed, TTL configurable (cache_manager.py) |
| **Health Monitoring** | No disponible | Probes periódicos con cache de estado (health_checker.py) |
| **Separación de Responsabilidades** | Monolítico — todo en un script | Modular — cada componente tiene una única responsabilidad |
| **Escalabilidad** | Limitada — un proceso por solicitud | Gateway centralizado — puede manejar concurrencia y pooling |

**Impacto en producción:**

- **Antes:** Un fallo en 192.168.2.111:8002 bloqueaba todo el pipeline TOON.
- **Ahora:** El orchestrator detecta el fallo, registra el evento, aplica fallback (caché o error estructurado), y permite que el Main Model continúe con JSON sin TOON si es necesario.

---

## 4. Formato TOON - Ejemplos

### 4.1 Comparación JSON vs TOON

**JSON equivalente:**

```json
{
  "pipeline": {
    "artifacts": [
      {
        "name": "01_Plan_Scrum.md",
        "status": "done"
      },
      {
        "name": "02_Architecture_SDD.md",
        "status": "in_progress"
      },
      {
        "name": "03_Plan_TDD.md",
        "status": "pending"
      },
      {
        "name": "04_Test_Report.md",
        "status": "pending"
      },
      {
        "name": "05_QA_Report.md",
        "status": "pending"
      }
    ],
    "team": [
      {
        "name": "scrum-master",
        "role": "orchestrator",
        "status": "active"
      },
      {
        "name": "architect",
        "role": "sdd",
        "status": "active"
      },
      {
        "name": "tdd-engineer",
        "role": "testing",
        "status": "active"
      },
      {
        "name": "validator",
        "role": "quality",
        "status": "active"
      }
    ],
    "version": "3.0",
    "active": true
  }
}
```

**TOON equivalente:**

```
pipeline:
  artifacts[5]{name,status}:
    01_Plan_Scrum.md,done
    02_Architecture_SDD.md,in_progress
    03_Plan_TDD.md,pending
    04_Test_Report.md,pending
    05_QA_Report.md,pending
  team[4]{name,role,status}:
    scrum-master,orchestrator,active
    architect,sdd,active
    tdd-engineer,testing,active
    validator,quality,active
  version: 3.0
  active: true
```

**Ahorro observable:**
- JSON: 633 caracteres (~158 tokens estimados, GPT-4 tokenizer)
- TOON: 293 caracteres (~73 tokens estimados, GPT-4 tokenizer)
- **Ahorro: ~54% en tokens**

### 4.2 Pipeline Artifacts

**TOON v4.1 - Tabular Form:**

```
artifacts[5]{name,status}:
  01_Plan_Scrum.md,done
  02_Architecture_SDD.md,in_progress
  03_Plan_TDD.md,pending
  04_Test_Report.md,pending
  05_QA_Report.md,pending
```

**Explicación:**

| Elemento | Significado |
|----------|-------------|
| `artifacts` | Key del objeto |
| `[5]` | Longitud declarada del array (5 elementos) |
| `{name,status}` | Lista de campos (field list) - declarada una sola vez |
| `:` | Terminador del header |
| Filas indentadas | Cada fila es un objeto del array, celdas separadas por comma |

Este es el **tabular form** de TOON v4.1 (§9.3 de la especificación). Los arrays de objetos uniformes se representan con un header que declara la longitud y los campos una sola vez, seguido de filas planas.

### 4.3 Agent Team

**TOON v4.1 - Tabular Form con 3 campos:**

```
team[4]{name,role,status}:
  scrum-master,orchestrator,active
  architect,sdd,active
  tdd-engineer,testing,active
  validator,quality,active
```

**Explicación:**

| Elemento | Significado |
|----------|-------------|
| `[4]` | 4 agentes en el equipo |
| `{name,role,status}` | 3 campos por agente |
| Filas | Cada fila = un agente con 3 valores |

### 4.4 Token Savings Data

**TOON v4.1 - Array primitivo:**

```
savings[3]:
  42,30,28
```

**Explicación:**

Este representa un array de 3 valores numéricos (porcentaje de ahorro por tipo de datos). Equivale a:

```json
{"savings": [42, 30, 28]}
```

TOON: `savings[3]:\n  42,30,28` = 24 caracteres
JSON: `"savings":[42,30,28]` = 22 caracteres (array primitivo no tiene gran ahorro)

El mayor ahorro viene de **arrays de objetos**, donde cada objeto en JSON repite las llaves y estructura.

### 4.5 Tabular con Nested Field Groups

**TOON v4.1 - Nested uniform columns (§9.3):**

```
orders[2]{id,customer{name,country},total}:
  1,Ada,DK,99
  2,Bob,UK,149
```

**Equivalente JSON:**

```json
{
  "orders": [
    {
      "id": 1,
      "customer": {
        "name": "Ada",
        "country": "DK"
      },
      "total": 99
    },
    {
      "id": 2,
      "customer": {
        "name": "Bob",
        "country": "UK"
      },
      "total": 149
    }
  ]
}
```

**Explicación del nested field group:**
- `customer{name,country}` en el header declara una columna de objetos uniformes
- Las filas son planas: cada fila tiene 4 celdas (id, customer.name, customer.country, total)
- El decoder reconstruye la anidación automáticamente

### 4.6 Keyed Tabular Form

**TOON v4.1 - Keyed header (§9.5):**

```
users[2:]{age,city}:
  alice: 30,Berlin
  bob: 25,Oslo
```

**Equivalente JSON:**

```json
{
  "users": {
    "alice": {
      "age": 30,
      "city": "Berlin"
    },
    "bob": {
      "age": 25,
      "city": "Oslo"
    }
  }
}
```

**Explicación:**
- `[2:]` marca un keyed header (colon después de la longitud)
- Cada fila tiene `entrykey: cells` formato
- `alice` y `bob` son las keys del objeto decoded

### 4.7 Mixed Arrays (List Form)

**TOON v4.1 - Mixed form (§9.4):**

```
mixed[3]:
  - 42
  - name: EitL
    version: 3.0
  - pending
```

**Equivalente JSON:**

```json
{
  "mixed": [
    42,
    {
      "name": "EitL",
      "version": 3.0
    },
    "pending"
  ]
}
```

**Explicación:**
- Cuando los elementos no son uniformes, se usa list form
- Cada elemento empieza con `- ` (hyphen marker)
- Objetos dentro de list items: primer campo en la misma línea del hyphen (§10)

### 4.8 Quoting Rules (Ejemplos)

**TOON v4.1 - Strings que requieren quoting (§7.2):**

```
links[2]{id,url}:
  1,"http://a:b"
  2,"https://example.com?q=a:b"

version: "3.0"
enabled: "true"
```

**Reglas de quoting aplicadas:**
- `url` values contienen `:` → deben estar quoted
- `"3.0"` es numeric-like → debe estar quoted
- `"true"` equals boolean literal → debe estar quoted

---

## 5. Calculadora de Ahorro de Tokens

### 5.1 Fórmula

```
savings% = (json_tokens - toon_tokens) / json_tokens × 100
```

Donde:
- `json_tokens` = conteo de tokens del JSON equivalente (usando tokenizer del modelo destino, e.g., GPT-4 o Qwen tokenizer)
- `tooon_tokens` = conteo de tokens del texto TOON equivalente

### 5.2 Valores esperados

| Tipo de datos | Ahorro típico | Razón |
|---------------|---------------|-------|
| Array de objetos (uniforme) | 30-50% | Field list declarada una sola vez, no repite llaves |
| Array primitivo | 0-15% | Solo ahorra corchetes y commas |
| Objeto plano (< 5 campos) | 10-20% | Ahorra llaves externas |
| Objeto anidado profundo | 40-60% | No repite estructura de llaves en cada nivel |
| Mixed array (list form) | 15-30% | Ahorra estructura de array pero items son verbosos |

### 5.3 Ejemplo de cálculo

**Datos:**

```json
{"artifacts":[{"name":"01_Plan_Scrum.md","status":"done"},{"name":"02_Architecture_SDD.md","status":"in_progress"}]}
```

```
artifacts[2]{name,status}:
  01_Plan_Scrum.md,done
  02_Architecture_SDD.md,in_progress
```

**Conteo (tokenizer Qwen):**
- JSON: ~45 tokens
- TOON: ~25 tokens

**Cálculo:**
```
savings% = (45 - 25) / 45 × 100 = 44.4%
```

### 5.4 Factores de ahorro en TOON

TOON ahorra tokens por:

1. **Sin llaves `{}` para objetos** - indentación reemplaza `{` y `}`
2. **Array shape declarada una sola vez** - `[N]{fields}:` en vez de `[` para cada elemento
3. **Campos declarados una sola vez** - `{name,status}` en el header vs repetir en cada objeto JSON
4. **Quoting mínimo** - strings solo se citan cuando contienen caracteres estructurales
5. **Sin comas finales** - no hay trailing commas en arrays/objetos

### 5.5 Token Savings Calculator (Python)

La calculadora se implementa en `scripts/toon/nl_processor.py` como parte del pipeline. Función clave:

```python
def calculate_savings(json_text: str, toon_text: str) -> dict:
    json_tokens = count_tokens(json_text)
    toon_tokens = count_tokens(toon_text)
    savings_pct = (json_tokens - toon_tokens) / json_tokens * 100
    return {
        "json_tokens": json_tokens,
        "toon_tokens": toon_tokens,
        "savings_pct": round(savings_pct, 1),
        "bytes_saved": len(json_text.encode()) - len(toon_text.encode()),
    }
```

---

## 6. Utilidades Python

Las utilidades TOON se encuentran en `scripts/toon/`.

### 6.1 Estructura de directorio

```
scripts/toon/
    to_json.py        # TOON → JSON (decoder)
    to_toon.py        # JSON → TOON (encoder)
    nl_processor.py   # NL → JSON → TOON pipeline
    requirements.txt  # Dependencias
```

### 6.2 to_json.py - Decoder

**Responsabilidad:** Convertir texto TOON v4.1 a JSON.

**Uso:**
```bash
python scripts/toon/to_json.py input.toon
python scripts/toon/to_json.py input.toon -o output.json
```

**Parámetros:**
| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `input` | Archivo TOON de entrada (stdin si no se provee) | stdin |
| `-o, --output` | Archivo de salida JSON | stdout |
| `--strict` | Activar strict mode del decoder | true |
| `--indent` | Indentación del JSON de salida | 2 |
| `--indent-size` | Tamaño de indentación (decoder-side) | 2 |

**Comportamiento del decoder:**
- Strict mode por defecto (detecta errores de estructura, count mismatches, width mismatches)
- UTF-8 input con soporte CRLF
- Comment lines removidas en pre-pass (regla §5.1 de TOON spec)
- Root form discovery (§5 de TOON spec)
- Last-write-wins para duplicate keys en non-strict mode (§14.3)

### 6.3 to_toon.py - Encoder

**Responsabilidad:** Convertir JSON a texto TOON v4.1.

**Uso:**
```bash
python scripts/toon/to_toon.py input.json
python scripts/toon/to_toon.py input.json -o output.toon
```

**Parámetros:**
| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `input` | Archivo JSON de entrada (stdin si no se provee) | stdin |
| `-o, --output` | Archivo de salida TOON | stdout |
| `--delimiter` | Delimitador: comma, tab, pipe | comma |
| `--indent-size` | Espacios por nivel de indentación | 2 |

**Comportamiento del encoder:**
- Detecta automaticamente la forma (inline, list, tabular, keyed tabular) por shape de datos (§9)
- Arrays de objetos uniformes → tabular form (obligatorio por spec §9.3)
- Objects whose values are uniform objects → keyed tabular form (§9.5)
- Números en canonical decimal form (§2)
- Booleans como `true`/`false` (lowercase)
- Null como `null` (lowercase)
- Sin trailing spaces ni trailing newline (§12)
- Sin comment lines (§5.1)

### 6.4 nl_processor.py - Pipeline Orchestrator

**Responsabilidad:** Orquestar el pipeline completo NL → JSON → TOON.

**Flujo:**

```
1. Recibe NL (lenguaje natural) del usuario
2. Llama al TOON Translator Agent (qwen2.5-3b) para generar JSON
3. Codifica JSON → TOON usando to_toon.py
4. Calcula savings (JSON tokens vs TOON tokens)
5. Output: texto TOON + métricas de ahorro
```

**Uso:**
```bash
python scripts/toon/nl_processor.py "Create pipeline for EitL v3 project"
python scripts/toon/nl_processor.py --prompt prompt.txt --output result.toon
```

**Parámetros:**
| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `nl_text` | Texto en lenguaje natural (stdin si no se provee) | stdin |
| `--prompt` | Archivo con prompt NL | stdin |
| `--output` | Archivo de salida TOON | stdout |
| `--verbose` | Mostrar métricas de ahorro | false |

### 6.5 requirements.txt

```
python-toon>=0.3.0
```

La biblioteca `python-toon` es la implementación Python de referencia de TOON v4.1. Provee las clases `Encoder` y `Decoder` que implementan todas las reglas de codificación y decodificación de la especificación.

---

## 7. Configuración

### 7.1 Variables de entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `TOON_SERVER_URL` | Endpoint del TOON Translator Agent | `http://192.168.2.111:8002/v1` |
| `TOON_MODEL` | Modelo del Translator Agent | `qwen2.5-3b-instruct` |
| `TOON_INDENT_SIZE` | Espacios por nivel de indentación | `2` |
| `TOON_DELIMITER` | Delimitador por defecto: comma, tab, pipe | `comma` |
| `TOON_CACHE_DIR` | Directorio de caché para TOON encoding/decoding | `eitl-artifacts/toon_cache/` |
| `TOON_STRICT` | Activar strict mode en decoder | `true` |

### 7.2 Archivo de configuración

Las variables de entorno se leen durante la inicialización del framework. Para overrides persistentes, agregar al `.env` del proyecto:

```bash
TOON_SERVER_URL=http://192.168.2.111:8002/v1
TOON_MODEL=qwen2.5-3b-instruct
TOON_INDENT_SIZE=2
TOON_DELIMITER=comma
TOON_CACHE_DIR=eitl-artifacts/toon_cache/
TOON_STRICT=true
```

### 7.3 Opciones del encoder

| Opción | Tipo | Valor por defecto | Descripción |
|--------|------|-------------------|-------------|
| `indentSize` | integer | `2` | Espacios por nivel de indentación (§13) |
| `delimiter` | enum | `comma` | Delimitador de documentos: comma, tab, pipe (§11) |

### 7.4 Opciones del decoder

| Opción | Tipo | Valor por defecto | Descripción |
|--------|------|-------------------|-------------|
| `indentSize` | integer | `2` | Espacios por nivel de indentación (§13) |
| `strict` | boolean | `true` | Strict mode: errores en count/width mismatches (§14) |

---

## 8. Integración con Pipeline Existente

### 8.1 Ubicación en el Pipeline

TOON opera en **Gate 0** (pre-pipeline optimization), antes de que el contexto llegue al Main Model:

```
[Gate 0: Pre-Pipeline Optimization]
    Usuario (NL)
        ↓
    TOON Translator Agent → JSON
        ↓
    TOON Encoder → TOON (compacted)
        ↓
    [Gate 1: Scrum Master receives TOON-optimized requirements]
        ↓
    Main Model processes TOON context
        ↓
    TOON Decoder → JSON response
        ↓
    Pipeline Agents receive structured data
```

### 8.2 Integración por componente

#### 8.2.1 Scrum Master

- **Input:** Recibe TOON-optimized requirements desde Gate 0
- **Procesamiento:** El Scrum Master interpreta el contexto TOON para orquestar el pipeline
- **Output:** TOON-structured context para Pipeline Agents

#### 8.2.2 Pipeline Agents

- **Input:** TOON-structured context (artifacts, team, configuration)
- **Ventaja:** Menos tokens = más espacio para generación de código
- **Agents involucrados:** architect, tdd-engineer, validator

#### 8.2.3 Context Guard

- **Monitoreo:** El Context Guard observa el uso de tokens TOON
- **Métricas:** Trackea json_tokens vs toon_tokens por pipeline execution
- **Alertas:** Si el ahorro cae bajo umbral (< 20%), alerta de posible formato subóptimo

#### 8.2.4 Memory Adapter

- **Almacenamiento:** El Memory Adapter guarda estados codificados en TOON
- **Recuperación:** Decodes TOON → JSON cuando se necesita restaurar un estado
- **Ventaja:** Estados compactos en caché = menos I/O y más rápida recuperación

### 8.3 Flujo de datos completo

```
┌─────────────────────────────────────────────────────────────────┐
│                        EitL Pipeline v3                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Usuario (NL) ──→ TOON Translator Agent                         │
│                    (qwen2.5-3b-instruct @ :8002)                │
│                    ↓ JSON                                       │
│                   ┌───────┐                                     │
│                   │Encoder│  (scripts/toon/to_toon.py)          │
│                   └───────┘                                     │
│                    ↓ TOON                                       │
│  ┌───────────────────────────────────────────┐                 │
│  │         Main Model Context (TOON)         │                 │
│  │         qwen3.6-35b-128k                  │                 │
│  │         ~30-50% menos tokens              │                 │
│  └───────────────────────────────────────────┘                 │
│                    ↓ Response (TOON)                            │
│                   ┌───────┐                                     │
│                   │Decoder│  (scripts/toon/to_json.py)          │
│                   └───────┘                                     │
│                    ↓ JSON                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Scrum Master │  │ Context Guard│  │Memory Adapter│         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                    ↓                                            │
│  ┌───────────────────────────────────────────┐                 │
│  │          Pipeline Agents                  │                 │
│  │  architect │ tdd-engineer │ validator     │                 │
│  └───────────────────────────────────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Referencia

### 9.1 Especificaciones

| Recurso | Ubicación |
|---------|-----------|
| TOON v4.1 Spec (oficial) | `C:\cnm-dev\samples\SPEC.md` |
| TOON GitHub | https://github.com/toon-format/spec |
| TOON README (implementaciones) | https://github.com/toon-format/toon |
| RFC 8259 (JSON) | https://www.rfc-editor.org/rfc/rfc8259 |
| RFC 4180 (CSV) | https://www.rfc-editor.org/rfc/rfc4180 |

### 9.2 Formato TOON

| Propiedad | Valor |
|-----------|-------|
| Nombre | Token-Oriented Object Notation |
| Versión | 4.1 |
| Author | Johann Schopplich (@johannschopplich) |
| License | MIT |
| Media type provisional | `text/toon` |
| File extension | `.toon` |
| Charset | UTF-8 (siempre) |
| Line endings | LF (U+000A) para encoding |
| Indentation | Espacios (default 2), sin tabs |
| Delimiters | comma (default), tab, pipe |

### 9.3 Relaciones con otros formatos

| Formato | vs TOON |
|---------|---------|
| JSON | TOON es más compacto para arrays de objetos uniformes; JSON para datos no uniformes o profundamente anidados |
| CSV | CSV más compacto para tablas flat; TOON añade nesting awareness, explicit lengths, y deterministic quoting |
| YAML | YAML más flexible; TOON es más constrained, deterministic, con headers de arrays explicitos y quoting rules estrictas |

### 9.4 Normative sections de TOON spec relevantes para EitL

| Sección | Tema | Relevancia |
|---------|------|------------|
| §2 | Data Model | TOON mapea al JSON data model |
| §3 | Encoding Normalization | Reglas de canonical number, booleans, null |
| §5 | Concrete Syntax and Root Form | Formas de documentos TOON |
| §6 | Header Syntax | `[N]`, `[N:]`, `{fields}` - core del formato |
| §7 | Strings and Keys | Rules de quoting (§7.2), key encoding (§7.3) |
| §9 | Arrays and Tabular Forms | **Principal fuente de ahorro de tokens** |
| §9.3 | Tabular Form | Arrays de objetos uniformes |
| §9.5 | Keyed Tabular Form | Objects de uniform objects |
| §11 | Delimiters | Comma (default), tab, pipe |
| §12 | Indentation and Whitespace | 2 espacios por default, LF line endings |
| §13 | Conformance and Options | Encoder/decoder options |
| §14 | Strict Mode Errors | Errores en strict mode (count, width, syntax) |

---

**Fin de la especificación de integración TOON v4.1 para EitL Framework v3.**

*Documento generado para uso interno del equipo EitL. Para preguntas sobre la especificación TOON v4.1, consultar la referencia oficial en `C:\cnm-dev\samples\SPEC.md`.*

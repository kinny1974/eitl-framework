# 🧠 Memoria-Política Completada - EitL Framework v1.0b

## 🎯 Objetivo  
Garantizar que la **ventana de contexto** (128k tokens) se **guarde y compacte automáticamente** antes de colapsar, manteniendo la continuidad del trabajo y evitando pérdidas de datos críticos.

---

## 📏 Umbrales de Contexto

| Nivel | Rango | Token Count | Acción Automática |
|-------|-------|-------------|-------------------|
| **OK** | < 65% | 0‑83k | Continuar normalmente |
| **⚠️ WARNING** | 65‑85% | **83k‑109k** | **Auto-save + Compactación** |
| **🚨 CRITICAL** | ≥ 86% | **≥ 110k** | **Auto-save + Compactación** |

---

## 📏 TOON Token Thresholds

| Nivel | Rango (TOON activo) | Token Count | Acción |
|-------|---------------------|-------------|--------|
| **OK** | < 65% | 0‑83k | TOON encoding activo, continuar normalmente |
| **⚠️ WARNING** | 65‑85% | **83k‑109k** | TOON compression recommended, forzar encoding si no activo |
| **🚨 CRITICAL** | ≥ 86% | **≥ 110k** | Force TOON encoding o fallback a JSON si servidor TOON no disponible |

---

## ⚙️ Acciones Automáticas (WARNING y CRITICAL)

Cuando el sistema detecta que el uso de contexto alcanza **83k tokens o más**, se ejecuta automáticamente:

### 1. Guardado en Memoria

```bash
guardar_conversacion(
  title="Context auto-save @ 83k",
  summary="[Generar resumen conciso del trabajo actual]",
  files_touched=[Lista de archivos modificados en esta sesión],
  decisions="[Listar decisiones técnicas realizadas]"
)
```

### 2. Guardado de Decisiones (si aplica)

```bash
guardar_decision(
  title="[Título de la decisión]",
  rationale="[Razón de la decisión]",
  alternatives="[Alternativas consideradas]"
)
```

### 3. Guardado de Tareas (si aplica)

```bash
guardar_tarea(
  title="[Título de la tarea]",
  status="in_progress",
  description="[Estado actual del trabajo]"
)
```

### 4. Compactación del Contexto

- Preservar los **últimos 10 mensajes** de alta prioridad.
- Resumir mensajes anteriores.
- Eliminar bloqueos resueltos del contexto.

---

## 🔄 TOON Token Optimization

### Overview

TOON (Text-Oriented Object Notation) es una representación compacta de estados y datos que reduce significativamente el consumo de tokens en comparación con JSON tradicional.

**Ahorro de tokens**: Los estados codificados en TOON utilizan aproximadamente **30-50% menos tokens** que su equivalente en JSON.

### TOON Integration with Memory Management

- **Memory Adapter** almacena los estados en formato TOON cuando está disponible.
- **Context Guard** monitorea el uso de tokens TOON para determinar cuándo se necesita compresión.
- **Fallback automático** a JSON cuando el servidor TOON no está disponible o responde con error.

### TOON Encoding Pipeline

```
Estado Original → TOON Server → TOON Encoded (30-50% savings) → Memory Storage
                        ↓
                 Server Unavailable
                        ↓
                  JSON Fallback
```

---

## 💾 TOON Memory Integration

### Cache System

Los estados TOON se almacenan en caché para evitar re-encodificación repetida y permitir recuperación rápida.

**Ubicación de caché**: `eitl-artifacts/toon_cache/`

**Formato de caché**:
- `{uuid}.toon` → Estado codificado en TOON
- `{uuid}.json` → Estado original en JSON (respaldo)

**TTL (Time To Live)**: 24 horas

**Invalidación**:
- Caché se invalida automáticamente al producirse una actualización del framework.
- Los entries expirados (>24h) se eliminan en el próximo ciclo de compactación.

### Cache Workflow

```
1. Verificar cache: eitl-artifacts/toon_cache/{uuid}.toon
2. Si existe y no expirado → Usar directamente
3. Si no existe o expirado → Encoder via TOON server
4. Guardar en cache: .toon + .json
5. Marcar timestamp de creación
```

---

## 🔄 Flujo de Acción Actualizado (con TOON)

1. **Guardar conversación** → TOON encode (ahorra 30-50% tokens)
2. **Guardar decisiones** → TOON encode (compresión automática)
3. **Guardar tareas** → TOON encode (estado compactado)
4. **Compactar** → Preserva últimos 10 mensajes en TOON
5. **Verificar cache** → eitl-artifacts/toon_cache/ antes de re-encoder
6. **Fallback** → JSON si TOON server no disponible

---

## 🧰 Integración con Memory-Adapter

| Modo | Backend | Ubicación |
|------|---------|-----------|
| **KinnyCodeMemory** | Servidor local (`localhost:8007`) | Herramientas nativas (`guardar_conversacion`, `guardar_decision`, `guardar_tarea`) |
| **Standalone** | Archivos locales | `eitl-artifacts/DECISIONS.md` <br> `eitl-artifacts/TASKS.md` |

> **Nota**: El modo automático (`auto`) detecta automáticamente qué backend está disponible.

---

## 🤖 Reglas del Agente Scrum-Master

Antes de **cualquier delegación pesada** (`/start-SDD`, `/run-tests`, `/qa-check`), el Scrum-Master:

1. **Carga** la skill `context-guard`.  
2. **Verifica** el uso de contexto con:  
   ```bash
   context-guard({ action: "check", agent: "auto" })
   ```
3. **Actúa automáticamente** si el nivel es WARNING o CRITICAL.  
4. **Continua** con la delegación solo si hay espacio suficiente.

---

## 📚 Flujo de Trabajo Recomendado

1. **Iniciar sesión** en OpenCode con la configuración EitL.  
2. **Trabajar normalmente** mientras el contexto crece.  
3. **Al alcanzar 83k tokens**, el sistema guarda y compacta automáticamente.  
4. **Verificar** el estado con:  
   ```bash
   context-guard({ action: "report", agent: "auto" })
   ```
   Esto muestra:
   - Tokens usados vs. límite
   - Última compactación
   - Alertas recientes

---

## 📋 Tabla de Verificación (CHECKLIST)

- [ ] **Configuración válida**: `opencode.jsonc` incluye `context-guard` y `memory-adapter`.  
- [ ] **Servidor KinnyCode** corriendo (si aplica) en `http://localhost:8007`.  
- [ ] **Servidor TOON** disponible para compresión de tokens.  
- [ ] **Proyecto ID** definido y válido.  
- [ ] **Permisos de escritura** en `eitl-artifacts/` y `eitl-artifacts/toon_cache/` (si usas modo standalone).  

---

## 🛠️ Solución de Problemas

| Problema | Solución |
|----------|----------|
| **Contexto no se guarda** | Verificar que `memory-adapter` esté configurado y que el servidor KinnyCode esté activo. |
| **Compactación fallida** | Ver logs del plugin `context-guard`; reiniciar OpenCode si es necesario. |
| **Tokens no se cuentan** | El sistema asume 128k como límite; si tu modelo tiene otro, ajusta `safeThreshold` y `criticalThreshold` en `AGENTES/*.md`. |
| **TOON encoding fallido** | Fallback automático a JSON; verificar servidor TOON en `localhost:8007`. |
| **Cache TOON corrupto** | Eliminar `eitl-artifacts/toon_cache/` y dejar que el sistema regenere los entries. |

---

## 📝 Notas Técnicas

- **Límite por defecto**: 128 000 tokens (~100 MB de memoria de contexto).  
- **Buffer de seguridad**: 17 % (≈ 22k tokens) restantes tras el CRITICAL.  
- **Frecuencia de compactación**: Solo ocurre al superar el umbral; no se compacta repetidamente.  
- **TOON savings**: 30-50% reducción en tokens vs JSON para estados y decisiones.  
- **TOON cache TTL**: 24 horas; invalidación al framework update.  
- **TOON fallback**: JSON automático si servidor TOON no disponible o timeout >5s.  

---

*Documento generado automáticamente como parte de la sesión de trabajo del 12/08/2026.*  
*Versión: EitL Framework v1.0b*

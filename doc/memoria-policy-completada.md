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
- [ ] **Proyecto ID** definido y válido.  
- [ ] **Permisos de escritura** en `eitl-artifacts/` (si usas modo standalone).  

---

## 🛠️ Solución de Problemas

| Problema | Solución |
|----------|----------|
| **Contexto no se guarda** | Verificar que `memory-adapter` esté configurado y que el servidor KinnyCode esté activo. |
| **Compactación fallida** | Ver logs del plugin `context-guard`; reiniciar OpenCode si es necesario. |
| **Tokens no se cuentan** | El sistema asume 128k como límite; si tu modelo tiene otro, ajusta `safeThreshold` y `criticalThreshold` en `AGENTES/*.md`. |

---

## 📝 Notas Técnicas

- **Límite por defecto**: 128 000 tokens (~100 MB de memoria de contexto).  
- **Buffer de seguridad**: 17 % (≈ 22k tokens) restantes tras el CRITICAL.  
- **Frecuencia de compactación**: Solo ocurre al superar el umbral; no se compacta repetidamente.  

---

*Documento generado automáticamente como parte de la sesión de trabajo del 12/08/2026.*  
*Versión: EitL Framework v1.0b*

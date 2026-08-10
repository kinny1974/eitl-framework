# 06 - Solucion de problemas

> **Objetivo**: resolver los problemas mas frecuentes de instalacion e inicializacion.

---

## 6.1 Problemas frecuentes

| Problema | Causa probable | Solucion |
|----------|----------------|----------|
| `context-guard` plugin not found | Plugin no en config | Asegura `"context-guard"` en `opencode.jsonc` |
| Artefactos no aparecen | Buscando en lugar equivocado | Se generan en `../eitl-artifacts/` |
| Plugin KinnyCodeMemory no encontrado | Plugin no instalado | Reinicia OpenCode para auto-instalacion |
| Servidor KinnyCode no responde | Servidor caido o URL incorrecta | Verifica que el servidor este corriendo |
| `init-eitl.ps1` bloqueado | Execution Policy | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned` |
| Script no encuentra framework | Bundle incompleto | Verifica estructura: `framework/.opencode/agents/` = 10 |

---

## 6.2 Plugin KinnyCodeMemory

### Plugin no se carga

1. Verifica que el servidor este corriendo
2. Reinicia OpenCode
3. Verifica la config en `opencode.jsonc`

### Herramientas no aparecen

1. Reinicia OpenCode despues de instalar el plugin
2. Verifica que el plugin este habilitado en `opencode.jsonc`

---

## 6.3 Modo Standalone

### Estado no se persiste

1. Verifica que `../eitl-artifacts/` exista
2. Verifica permisos de escritura

---

## 6.4 Windows

### PowerShell bloquea el script

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned
```

### Rutas largas

Windows tiene limite de 260 caracteres. Usa rutas cortas o habilita largas rutas:

```powershell
# Como administrador
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

---

## 6.5 Linux / macOS

### Script no es ejecutable

```bash
chmod +x init-eitl.sh
```

---

## 6.6 Siguiente paso

Ve a [07 - QA](07-qa.md) para reportes de calidad.

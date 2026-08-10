# 08 - Guia de memoria para equipos

> **Objetivo**: como configurar y usar la memoria de EitL en un equipo de desarrollo.

---

## 8.1 Conceptos clave

- **Project ID**: Identificador unico por proyecto (no por usuario)
- **Memoria compartida**: Todos los miembros del equipo comparten la misma memoria
- **Project ID**: Se comparte entre todos los miembros del equipo

---

## 8.2 Opcion 1: KinnyCodeMemory (Recomendado para equipos)

### Configuracion del servidor

1. **Un solo servidor** para todo el equipo:
   ```bash
   # En un servidor central o maquina dedicada
   ./KinnyCodeMemory-Server
   ```

2. **Compartir el Project ID**:
   ```
   Project ID: abc123def456
   URL: http://192.168.1.100:8007
   ```

3. **Cada miembro inicializa con los mismos datos**:
   ```powershell
   # Windows - Todos usan el mismo Project ID
   .\init-eitl.ps1 -ProjectName "mi-api" -MemoryMode local -MemoryPlugin kinnycode -MemoryUrl "http://192.168.1.100:8007" -ProjectId "abc123def456"
   ```

### Flujo de trabajo

```
Equipo de 3 devs:
- Ana: inicializa con ProjectId "abc123" -> indexa codigo
- Bob: inicializa con ProjectId "abc123" -> busca contexto
- Carlos: inicializa con ProjectId "abc123" -> toma decisiones
```

Todos comparten la misma memoria. Si Ana indexa un archivo, Bob y Carlos pueden encontrarlo.

### Permisos

- El servidor KinnyCodeMemory no tiene autenticacion por defecto
- En red externa, usar VPN o firewall
- Para producción, considerar agregar autenticacion

---

## 8.3 Opcion 2: Mem0 (Cloud)

### Configuracion

1. **Cada miembro tiene su propia API key** de Mem0
2. **Project ID compartido** para memoria compartida

```bash
# Cada miembro configura su API key
export MEM0_API_KEY="api-key-del-miembro"
```

### Consideraciones

- Los datos se almacenan en la nube de Mem0
- Cada miembro paga su propio tier
- La memoria se sincroniza automaticamente

---

## 8.4 Opcion 3: LanceDB (Local)

### Configuracion

- **No recomendado para equipos**: cada miembro tiene su propia base de datos local
- No hay sincronizacion automatica
- Para usar en equipo, combinar con Git para sincronizar `~/.opencode/memory/lancedb/`

### Sincronizacion manual

```bash
# Agregar la memoria al repositorio
echo "~/.opencode/memory/" >> .gitignore
git add ~/.opencode/memory/
git commit -m "chore: sync memory"
```

---

## 8.5 Buenas practicas para equipos

### 1. Project ID consistente

```bash
# Crear un Project ID unico por proyecto
# Compartirlo en el README del proyecto o en un archivo .eitl

echo "PROJECT_ID=abc123def456" > .eitl
echo "MEMORY_URL=http://192.168.1.100:8007" >> .eitl
```

### 2. Documentar la configuracion

```markdown
## Configuracion EitL

- **Project ID**: abc123def456
- **Servidor**: http://192.168.1.100:8007
- **Plugin**: KinnyCodeMemory
```

### 3. Roles de memoria

| Rol | Acciones |
|-----|----------|
| **Indexador** | Indexa codigo y documentos |
| **Buscador** | Busca contexto en la memoria |
| **Administrador** | Consolidar y limpiar memoria |

### 4. Consolidacion periodica

```bash
# En KinnyCodeMemory, ejecutar periodicamente
consolidar_memoria
limpiar_proyecto
```

---

## 8.6 Solucion de problemas

| Problema | Solucion |
|----------|----------|
| "No veo la memoria de mi compañero" | Verificar que usen el mismo Project ID |
| "Conflicto de memoria" | Usar Project IDs diferentes por feature |
| "Memora lenta" | Verificar que el servidor tenga suficientes recursos |
| "No puedo indexar" | Verificar permisos de escritura en el servidor |

---

## 8.7 Siguiente paso

Ve a [06 - Solucion de problemas](06-solucion-de-problemas.md) si tienes problemas.

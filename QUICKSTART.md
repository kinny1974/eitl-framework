# EitL Quick Start

> Get the EitL pipeline running in under 5 minutes.

---

## 1. Clone the Repository

```bash
git clone https://github.com/kinny1974/eitl-framework.git
cd eitl-framework/init-scripts
```

---

## 2. Initialize Your Project

### Option A: Interactive (Recommended)

```powershell
# Windows
.\init-eitl.ps1
```

```bash
# Linux / macOS
./init-eitl.sh
```

The script will ask you:
1. Project name
2. Memory mode (standalone / with server)
3. Plugin type (KinnyCodeMemory, Mem0, LanceDB)
4. Server URL (if using memory)
5. Project ID (if using KinnyCodeMemory)

### Option B: One Command

```powershell
# Windows - Standalone
.\init-eitl.ps1 -ProjectName "my-project" -MemoryMode standalone

# Windows - KinnyCodeMemory
.\init-eitl.ps1 -ProjectName "my-project" -MemoryMode local -MemoryPlugin kinnycode -MemoryUrl "http://localhost:8007"
```

```bash
# Linux - Standalone
./init-eitl.sh "my-project" standalone

# Linux - KinnyCodeMemory
./init-eitl.sh "my-project" local kinnycode "http://localhost:8007"
```

---

## 3. Start OpenCode

```bash
cd ../my-project
opencode
```

OpenCode reads `opencode.jsonc`.

### Install Memory Plugin (if using memory mode)

If you chose memory mode, install the plugin from the OpenCode TUI:

```
/install-plugin opencode-kinnycode-memory
```

> **Note**: OpenCode should auto-install plugins, but manual installation may be required.

---

## 4. Memory (Optional)

### Standalone (Default)

No server required. State saved in `eitl-artifacts/`.

### With KinnyCodeMemory (Recommended)

1. Download from: https://github.com/kinny1974/kinnyCodeMemory/releases
2. Run the server:
   ```bash
   # Windows
   .\KinnyCodeMemory-Server.exe

   # Linux
   ./KinnyCodeMemory-Server
   ```
3. Reinitialize with memory:
   ```powershell
   .\init-eitl.ps1 -ProjectName "my-project" -MemoryMode local -MemoryPlugin kinnycode -MemoryUrl "http://localhost:8007"
   ```

### Alternative: Mem0

```powershell
.\init-eitl.ps1 -ProjectName "my-project" -MemoryMode local -MemoryPlugin mem0 -MemoryUrl "http://localhost:8003"
```

### Alternative: LanceDB

```powershell
.\init-eitl.ps1 -ProjectName "my-project" -MemoryMode local -MemoryPlugin lancedb
```

---

## 5. Run Your First Pipeline

In the OpenCode TUI, type:

```
/start-SDD Build a REST API for user management with authentication
```

This will generate:
- `01_Plan_Scrum.md` -- Scrum planning
- `02_Architecture_SDD.md` -- Architecture design
- `03_Plan_TDD.md` -- Test plan

---

## Next Steps

- Read the full [README](README.md) for detailed documentation
- Check [Troubleshooting](README.md#troubleshooting) if you have issues
- Explore the available [commands](README.md#pipeline-usage)


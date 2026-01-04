# Platform Migration & Recovery Guide

**Purpose**: Restore sim.ai PoC and claude-mem after migration to Ubuntu
**Created**: 2026-01-04
**Source**: Windows (C:\Users\natik\Documents\Vibe)
**Target**: Ubuntu (from E:\saveNatikLaptop2\#COding)

---

## Quick Recovery Checklist

```bash
# 1. Restore directories
cp -r /path/to/backup/Vibe ~/Documents/Vibe
cp -r /path/to/backup/.claude-mem ~/.claude-mem

# 2. Restore Docker volumes
./scripts/restore-docker-volumes.sh

# 3. Start services
cd ~/Documents/Vibe/sim-ai/sim-ai
docker compose --profile dev up -d

# 4. Verify
python -c "from governance.client import TypeDBClient; c=TypeDBClient(); print('Rules:', len(c.get_all_rules()))"
```

---

## Data Locations

### Project Data (Vibe Directory)
| Component | Windows Path | Ubuntu Path |
|-----------|--------------|-------------|
| sim.ai PoC | `C:\Users\natik\Documents\Vibe\sim-ai\sim-ai` | `~/Documents/Vibe/sim-ai/sim-ai` |
| Evidence | `sim-ai\evidence\` | `sim-ai/evidence/` |
| Rules Docs | `sim-ai\docs\rules\` | `sim-ai/docs/rules/` |
| TypeDB Schema | `sim-ai\governance\schema.tql` | `sim-ai/governance/schema.tql` |

### Claude-Mem Data
| Component | Windows Path | Ubuntu Path |
|-----------|--------------|-------------|
| ChromaDB | `C:\Users\natik\.claude-mem\chroma\` | `~/.claude-mem/chroma/` |
| Archives | `C:\Users\natik\.claude-mem\archives\` | `~/.claude-mem/archives/` |
| Settings | `C:\Users\natik\.claude-mem\settings.json` | `~/.claude-mem/settings.json` |

### Docker Volumes (Ephemeral but Critical)
| Volume | Content | Backup Location |
|--------|---------|-----------------|
| `sim-ai_typedb_data` | 36 governance rules, decisions, sessions | `backup/docker/typedb_data/` |
| `sim-ai_chromadb_data` | Vector embeddings for semantic search | `backup/docker/chromadb_data/` |
| `sim-ai_ollama_data` | Ollama models (gemma3:4b) | `backup/docker/ollama_data/` (optional) |
| `claude-memory` | Additional claude-mem data | `backup/docker/claude_memory/` |

---

## Full Recovery Procedure

### Step 1: Restore Project Files

```bash
# Create target directory
mkdir -p ~/Documents/Vibe

# Copy from backup
cp -r /media/backup/Vibe/* ~/Documents/Vibe/

# Restore claude-mem
cp -r /media/backup/.claude-mem ~/
```

### Step 2: Install Prerequisites

```bash
# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Python 3.12
sudo apt install python3.12 python3.12-venv python3-pip

# Create venv
cd ~/Documents/Vibe/sim-ai/sim-ai
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Restore Docker Volumes

```bash
# Create volumes
docker volume create sim-ai_typedb_data
docker volume create sim-ai_chromadb_data
docker volume create claude-memory

# Restore TypeDB data
docker run --rm -v sim-ai_typedb_data:/data -v /media/backup/docker:/backup alpine \
  sh -c "cp -r /backup/typedb_data/* /data/"

# Restore ChromaDB data
docker run --rm -v sim-ai_chromadb_data:/data -v /media/backup/docker:/backup alpine \
  sh -c "cp -r /backup/chromadb_data/* /data/"

# Restore claude-memory
docker run --rm -v claude-memory:/data -v /media/backup/docker:/backup alpine \
  sh -c "cp -r /backup/claude_memory/* /data/"
```

### Step 4: Start Services

```bash
cd ~/Documents/Vibe/sim-ai/sim-ai

# Start dev profile
docker compose --profile dev up -d

# Wait for services
sleep 30

# Verify TypeDB
docker exec sim-ai-typedb-1 ./typedb console --command="database list"
```

### Step 5: Verify Recovery

```bash
# Activate venv
source .venv/bin/activate

# Check TypeDB rules
python -c "
from governance.client import TypeDBClient
client = TypeDBClient()
if client.connect():
    rules = client.get_all_rules()
    print(f'TypeDB Rules: {len(rules)}')
    client.close()
"

# Check ChromaDB
python -c "
import chromadb
client = chromadb.HttpClient(host='localhost', port=8001)
collections = client.list_collections()
print(f'ChromaDB Collections: {len(collections)}')
"

# Check claude-mem
python -c "
import chromadb
client = chromadb.PersistentClient(path='~/.claude-mem/chroma')
cols = client.list_collections()
print(f'Claude-mem Collections: {len(cols)}')
"
```

---

## Critical Data Inventory

### TypeDB (36 Rules)
- **RULE-001 to RULE-036**: Governance, Technical, Operational rules
- **Decisions**: DECISION-001 to DECISION-007
- **Sessions**: Session evidence links

### ChromaDB (Governance)
- **governance-rules**: Rule embeddings for semantic search
- **governance-decisions**: Decision embeddings
- **governance-evidence**: Evidence file embeddings

### Claude-Mem
- **claude_memories**: Session memories, project context
- **Archives**: Historical memory exports

---

## Environment Variables

Create `~/.env` or set in shell:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export LITELLM_MASTER_KEY="sk-litellm-master-key"
export CHROMA_AUTH_TOKEN="chroma-token-dev"
```

---

## Troubleshooting

### TypeDB Not Connecting
```bash
# Check container logs
docker logs sim-ai-typedb-1

# Verify port
nc -zv localhost 1729

# Restart
docker compose restart typedb
```

### ChromaDB Empty After Restore
```bash
# Verify volume mount
docker inspect sim-ai_chromadb_data

# Check container
docker exec sim-ai-chromadb-1 ls /chroma/chroma
```

### Claude-Mem Missing Memories
```bash
# Check local ChromaDB
ls -la ~/.claude-mem/chroma/

# Verify sqlite
sqlite3 ~/.claude-mem/chroma/chroma.sqlite3 "SELECT COUNT(*) FROM embeddings;"
```

---

## Re-seeding Data (If Restore Fails)

If Docker volumes are lost, re-seed from workspace files:

```bash
cd ~/Documents/Vibe/sim-ai/sim-ai
source .venv/bin/activate

# Seed TypeDB rules
python -c "from governance.seed_data import seed_rules; seed_rules()"

# Sync tasks from workspace
python -c "
from governance.mcp_tools.workspace import workspace_capture_tasks
print(workspace_capture_tasks())
"

# Link rules to documents
python -c "
from governance.mcp_tools.workspace import workspace_link_rules_to_documents
print(workspace_link_rules_to_documents())
"
```

---

## Version Info

- Python: 3.12.x
- Docker: 24.x+
- TypeDB: latest (vaticle/typedb)
- ChromaDB: latest
- sim.ai: 1.0.0

---

*Per RULE-024: AMNESIA Protocol - This document enables recovery after context loss.*

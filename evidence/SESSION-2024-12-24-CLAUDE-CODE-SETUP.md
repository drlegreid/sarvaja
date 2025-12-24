# Session Evidence: Claude Code + Mem0 Integration

**Date:** 2024-12-24
**Session ID:** claude-code-setup
**Duration:** ~45 minutes
**Tools:** Claude Code (Opus 4.5), VS Code

---

## Summary

Successfully configured and validated the sim-ai PoC stack with Claude Code, including:
1. MCP integration audit (10 MCPs active)
2. Docker stack health verification
3. Anthropic API key configuration
4. Mem0 + Ollama integration test (DECISION-002 validated)
5. LiteLLM routing test (local + remote models)

---

## Validated Components

### MCP Integration (10 Active)

| MCP | Status | Purpose |
|-----|--------|---------|
| claude-mem | ✅ Active | Memory persistence (53 docs) |
| octocode | ✅ Active | GitHub code search |
| playwright | ✅ Active | Browser automation |
| sequential-thinking | ✅ Active | Complex reasoning |
| desktop-commander | ✅ Active | File/process ops |
| filesystem | ✅ Active | File operations |
| git | ✅ Active | Version control |
| powershell | ✅ Active | Windows automation |
| llm-sandbox | ✅ Active | Code execution |
| godot-mcp | ✅ Active | Game dev (optional) |

### Docker Stack Health

| Service | Port | Status | Notes |
|---------|------|--------|-------|
| ChromaDB | 8001 | ✅ Healthy | heartbeat OK |
| Ollama | 11434 | ✅ Healthy | 2 models loaded |
| LiteLLM | 4000 | ✅ Healthy | Auth working |
| Agents | 7777 | ✅ Healthy | FastAPI running |

### Ollama Models

```
gemma3:4b          - 3.3GB (inference)
nomic-embed-text   - 274MB (embeddings)
```

---

## Key Tests

### Test 1: Mem0 + Ollama (DECISION-002)

**Config:**
```python
config = {
    'llm': {'provider': 'ollama', 'config': {'model': 'gemma3:4b', 'ollama_base_url': 'http://localhost:11434'}},
    'embedder': {'provider': 'ollama', 'config': {'model': 'nomic-embed-text', 'ollama_base_url': 'http://localhost:11434'}},
    'vector_store': {'provider': 'qdrant', 'config': {'collection_name': 'sim_ai_memories', 'embedding_model_dims': 768}}
}
```

**Result:** ✅ SUCCESS
- Memory added: "sim-ai project uses LiteLLM, ChromaDB, and Ollama for multi-agent AI"
- Search returned correct result

**Note:** Must use fresh collection (768 dims) to avoid mismatch with old OpenAI embeddings (1536 dims).

### Test 2: LiteLLM Routing

| Model | Backend | Response | Status |
|-------|---------|----------|--------|
| gemma-local | Ollama | "Hello!" | ✅ |
| claude-sonnet | Anthropic | "Hello from sim-ai!" | ✅ |

**API Key:** New ANTHROPIC_API_KEY configured in .env and working.

---

## Gaps Discovered

1. **deploy.ps1 health check** - False negatives (curl/PowerShell issue)
2. **LiteLLM DB warning** - "No connected db" when using callbacks (disabled)

---

## Decisions Made

| ID | Decision | Rationale |
|----|----------|-----------|
| DECISION-002 | Use Mem0 with Ollama embeddings | No OpenAI dependency, local-first |

---

## Next Steps

1. [ ] Fix deploy.ps1 health check script
2. [ ] Document Mem0 config in project docs
3. [ ] Evaluate MCP-Monitor for crash prevention
4. [ ] Update TODO.md with session progress

---

**Evidence Location:** `evidence/SESSION-2024-12-24-CLAUDE-CODE-SETUP.md`
**Committed:** Pending

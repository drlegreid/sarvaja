# Migration Strategy: Legacy GAI → Sim.ai Platform

**Date:** 2024-12-24  
**Status:** R&D Analysis  
**Source Projects:** angelgai, localgai, godot-mcp, archangelgai

---

## Executive Summary

Migrate proven innovations from 4 existing local AI agent projects into unified Sim.ai platform while preserving institutional knowledge and operational patterns.

---

## Source Project Analysis

### 1. AngelGAI (Resurrection Rulebook)
**Location:** `C:\Users\natik\Documents\Vibe\angelgai`  
**Purpose:** Crash recovery, memory optimization, MCP stability

**Key Innovations:**
| Innovation | Description | Preserve? |
|------------|-------------|-----------|
| **Memory Thresholds** | <500MB healthy, >2GB critical | ✅ YES |
| **MCP Classification** | STABLE/RISKY/DANGEROUS tiers | ✅ YES |
| **Crash Recovery Levels** | Soft → Medium → Hard → Nuclear | ✅ YES |
| **Process Leak Detection** | Node.exe count monitoring | ✅ YES |
| **Recovery Scripts** | PowerShell automation | ✅ YES |

**Artifacts to Migrate:**
- `RULES.md` → Merge into `docs/RULES-DIRECTIVES.md`
- `scripts/*.ps1` → Copy to `scripts/`
- `evidence/` pattern → Already adopted

---

### 2. LocalGAI (MCP Infrastructure)
**Location:** `C:\Users\natik\Documents\Vibe\localgai`  
**Purpose:** PhotoPrism migration + MCP methodology

**Key Innovations:**
| Innovation | Description | Preserve? |
|------------|-------------|-----------|
| **EBMSF** | Evidence-Based MCP Selection Framework | ✅ CRITICAL |
| **2-Layer Governance** | GitHub (human) + claude-mem (AI) | ✅ YES |
| **AITV Workflow** | Analyze → Implement → Test → Validate | ✅ YES |
| **DSM** | Deep Sleep Mode with gap analysis | ✅ YES |
| **MCP Health Checks** | 6-phase test/fix workflow | ✅ YES |
| **Version-First Rule** | Check compatibility before integration | ✅ YES |

**Artifacts to Migrate:**
- `mcp_servers.json` → Reference for MCP config patterns
- `scripts/*.py` → Evaluate for sim-ai compatibility
- EBMSF methodology → Add to `.windsurf/workflows.md`

---

### 3. Godot-MCP (Game Dev)
**Location:** `C:\Users\natik\Documents\Vibe\godot-mcp`  
**Purpose:** Game development with MCP integration

**Key Innovations:**
| Innovation | Description | Preserve? |
|------------|-------------|-----------|
| **Godot-MCP Rule** | Always use MCP for Godot (no manual .gd) | ✅ YES |
| **TypeScript Server** | Custom MCP server pattern | ⚠️ REFERENCE |

**Artifacts to Migrate:**
- `server/` → Reference architecture for custom MCPs

---

### 4. ArchangelGAI (Empty)
**Location:** `C:\Users\natik\Documents\Vibe\archangelgai`  
**Purpose:** Unknown (only `.idea/` folder exists)  
**Status:** SKIP - No content to migrate

---

## Innovation Preservation Matrix

### CRITICAL (Must Migrate)

#### 1. EBMSF - Evidence-Based MCP Selection Framework
```
Phase 1: Discovery (authoritative sources)
Phase 2: Hypothesis Formation (IF/THEN/BECAUSE)
Phase 3: Risk Assessment (security/stability/data exposure)
Phase 4: Impact Scoring (token/time/error/learning)
Phase 5: Selection Decision (MUST_HAVE/RECOMMENDED/OPTIONAL/EXCLUDE)
Phase 6: Continuous Validation (monthly review)
```

#### 2. Memory Thresholds
```
< 500 MB   : HEALTHY
500-1000 MB: NORMAL
1000-1500 MB: WARNING
1500-2000 MB: HIGH
> 2000 MB  : CRITICAL
> 3000 MB  : EMERGENCY
```

#### 3. MCP Stability Tiers
```
STABLE: sequential-thinking, filesystem, git, memory
RISKY: context7, octocode, docker (timeout issues)
DANGEROUS: playwright (500+ MB), fetch (network timeouts)
```

### HIGH (Should Migrate)

#### 4. 2-Layer Governance Model
- **Layer 1 (Human):** GitHub issues, exec summaries, swimlane
- **Layer 2 (AI):** claude-mem, technical details, heuristics
- **Sync Triggers:** Milestone, budget impact, human decision needed, weekly

#### 5. AITV Workflow
```
A - Analyze: Understand problem, gather context
I - Implement: Make changes
T - Test: Verify changes work
V - Validate: Confirm meets requirements
```

#### 6. DSM (Deep Sleep Mode)
- Gap analysis against open GitHub issues
- Code quality work only after gap check
- Prevents drift from objectives

### MEDIUM (Consider Migrating)

#### 7. Crash Recovery Scripts
- `crash-protocol.ps1` - Disable heavy MCPs
- `recover.ps1` - Kill all processes
- `quick-status.ps1` - Health check

#### 8. MCP Test/Fix Workflow (6 Phases)
1. Individual server test
2. IDE integration
3. Functional verification
4. Troubleshooting matrix
5. Health checks
6. Restart checklist

---

## Migration Plan

### Phase 1: Document Merge (Now)
- [x] Create this migration strategy doc
- [ ] Merge EBMSF into `.windsurf/workflows.md`
- [ ] Add memory thresholds to `docs/RULES-DIRECTIVES.md`
- [ ] Add MCP tiers to Playwright MCP rule

### Phase 2: Script Migration (Next Session)
- [ ] Copy recovery scripts to `scripts/`
- [ ] Adapt for Windsurf (not VS Code)
- [ ] Add to deploy.ps1 as actions

### Phase 3: Governance Integration (Future)
- [ ] Set up 2-layer sync with GitHub issues
- [ ] Create exec summary template
- [ ] Configure DSM gap analysis

### Phase 4: MCP Consolidation (Future)
- [ ] Merge MCP configs into single source of truth
- [ ] Apply EBMSF to current sim-ai MCPs
- [ ] Document tier assignments

---

## Architecture Comparison

| Aspect | Legacy (angelgai+localgai) | Sim.ai |
|--------|---------------------------|--------|
| IDE | VS Code + Claude Code | Windsurf + Cascade |
| MCP Config | `~/.claude.json` | `~/.codeium/mcp_config.json` |
| Memory | claude-mem (ChromaDB) | Cascade Memory + ChromaDB |
| Agents | N/A | 5 Agno agents (port 7777) |
| Model Routing | Direct Anthropic | LiteLLM proxy (port 4000) |
| Observability | N/A | Opik (port 5173) |
| Vector Store | claude-mem | ChromaDB (port 8001) |
| Local LLM | N/A | Ollama (port 11434) |

---

## Contextual Value Preserved

### From AngelGAI
1. **Stability-first mindset** - Memory monitoring, MCP risk tiers
2. **Recovery procedures** - Documented crash handling
3. **Evidence logging** - Session artifacts

### From LocalGAI
1. **EBMSF** - Rigorous MCP selection methodology
2. **Governance model** - Human/AI separation of concerns
3. **AITV workflow** - Structured development approach
4. **Health check patterns** - Systematic verification

### From Godot-MCP
1. **Custom MCP server pattern** - TypeScript server architecture
2. **Tool-first rule** - Prefer MCP over manual operations

---

## Recommendations

### Immediate Actions
1. **Start Opik** to restore observability
2. **Add EBMSF** to workflows.md for MCP decisions
3. **Add memory thresholds** to RULE-005 (new)

### Future R&D
1. **Unified MCP Dashboard** - Combine health checks from all projects
2. **Cross-project Memory** - Share claude-mem entries with Cascade
3. **Automated DSM** - Deep sleep mode with scheduled gap analysis

---

## References

- AngelGAI: `C:\Users\natik\Documents\Vibe\angelgai`
- LocalGAI: `C:\Users\natik\Documents\Vibe\localgai`
- Godot-MCP: `C:\Users\natik\Documents\Vibe\godot-mcp`
- GitHub (archangel): https://github.com/drlegreid/archangel
- GitHub (localgai): https://github.com/drlegreid/localgai

---

**Next Step:** Merge EBMSF methodology and memory thresholds into sim-ai rules.

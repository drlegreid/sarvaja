# ARCH-INFRA-01-v1: Infrastructure Identity & Hardware Metadata

**Category:** `devops` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** TECHNICAL

> **Legacy ID:** RULE-016
> **Location:** [RULES-ARCHITECTURE.md](../technical/RULES-ARCHITECTURE.md)
> **Tags:** `infrastructure`, `hardware`, `identity`, `registry`

---

## Directive

All infrastructure components MUST be identifiable via metadata for digital twin management.

---

## Infrastructure Registry

| Component | Role | Port |
|-----------|------|------|
| agents | Agno runtime | 7777 |
| chromadb | Vector storage | 8001 |
| typedb | Graph inference | 1729 |
| litellm | Model routing | 4000 |
| ollama | Local inference | 11434 |

---

## Hardware Resource Limits

| Container | Memory | CPU | Purpose |
|-----------|--------|-----|---------|
| agents | 1G | - | Agno agent runtime |
| litellm | 512M | - | Model routing proxy |
| chromadb | 1G | - | Vector storage |
| typedb | 2G | - | Graph database |
| ollama | 4G | 2 | Local inference |

---

## Deployment Identity

```yaml
deployment_identity:
  deployment_id: "{project}-{date}-{env}"
  host_fingerprint: "{cpu}-{ram}-{os}"
  cluster_signature: md5(containers)
  mcp_profile: [active_mcp_names]
```

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Run untracked containers | Register in infrastructure registry |
| Exceed memory limits without reason | Document resource requirements |
| Deploy without identity metadata | Include deployment_id in logs |
| Skip port documentation | Maintain port registry table |

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*

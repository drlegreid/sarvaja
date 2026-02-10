# ARCH-MCP-PARITY-01-v1: MCP-REST API Feature Parity

**Category:** `technical` | **Priority:** MEDIUM | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Tags:** `architecture`, `mcp`, `rest-api`, `parity`

---

## Directive

MCP tools SHOULD provide equivalent filtering and pagination capabilities as REST API endpoints. When REST API supports offset/limit pagination and field filtering, corresponding MCP tools MUST offer similar parameters. Document any intentional gaps with rationale.

---

## Validation

- [ ] MCP task tools support status/phase/agent_id filtering
- [ ] MCP session tools support status/limit filtering
- [ ] MCP rule tools support category/priority filtering
- [ ] Intentional gaps are documented in tool descriptions

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Return all items without pagination | Support offset/limit parameters |
| Ignore REST API filter params in MCP | Mirror REST query params in MCP tools |
| Silently drop filtering capabilities | Document gaps with rationale |
| Create MCP-only features without REST | Maintain parity in both directions |

---

*Per ARCH-MCP-02-v1: MCP Server Split Architecture*

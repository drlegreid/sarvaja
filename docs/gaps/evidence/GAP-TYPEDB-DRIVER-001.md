# GAP-TYPEDB-DRIVER-001: TypeDB Driver/Server Version Incompatibility

**Priority:** CRITICAL | **Category:** infrastructure | **Status:** BLOCKED
**Discovered:** 2026-01-16 | **Session:** SESSION-2026-01-16-PLATFORM-AUDIT
**Updated:** 2026-01-16 | **Reason:** Deeper incompatibility discovered

---

## Summary

TypeDB Python driver cannot be used with our current stack due to version matrix incompatibility:

| Component | Our Version | Requires |
|-----------|-------------|----------|
| Python | 3.13 | - |
| TypeDB Server | 2.29.1 | Protocol v3 |
| typedb-driver 2.x | 2.29.2 | Python 3.8-3.11 |
| typedb-driver 3.x | 3.7.0 | Protocol v7 (TypeDB 3.x) |

**No driver version exists that supports both Python 3.13 AND TypeDB Server 2.x.**

## Evidence

### Error 1: Driver 2.29.2 - Library Missing
```
libpython3.12.so.1.0: cannot open shared object file: No such file or directory
```
Cause: typedb-driver 2.x wheels compiled only for Python 3.8-3.11.

### Error 2: Driver 3.7.0 - Protocol Mismatch
```
TypeDBDriverException: [SRV26] Invalid Server Operation:
A protocol version mismatch was detected.
This server supports version '3' but the driver supports version '7'.
```
Cause: Driver 3.x requires TypeDB Server 3.x.

### TypeDB Server Version Confirmation
```
TypeDB Core version: 2.29.1
listening to address: 0.0.0.0:1729
```

### Version Compatibility Matrix

| Driver | Python Support | Server Compat | Status |
|--------|---------------|---------------|--------|
| 2.29.2 | 3.8-3.11 | TypeDB 2.x | ❌ Python 3.13 |
| 3.7.0 | 3.11+ | TypeDB 3.x | ❌ Server 2.x |

### API Changes in 3.x
```python
# Old 2.x API
driver = TypeDB.core_driver('localhost:1729')

# New 3.x API (requires Credentials + DriverOptions)
creds = Credentials('', '')
opts = DriverOptions(is_tls_enabled=False)
driver = TypeDB.driver('localhost:1729', creds, opts)
```

## Impact

- **Direct Python access to TypeDB blocked** - No working driver
- **E2E tests** must use MCP fallback
- **Integration tests** cannot create tasks directly
- **MCP servers work** - Container has compatible stack

## Options

### Option A: Upgrade TypeDB Server to 3.x (RECOMMENDED)
**Effort:** HIGH | **Risk:** MEDIUM

1. Update docker-compose to use `typedb/typedb:3.x`
2. Migrate database schema (if breaking changes)
3. Update all code to use 3.x API
4. Test all MCP servers
5. Verify 50 rules migrate correctly

**Benefit:** Modern stack, Python 3.13 compatible

### Option B: Downgrade Python to 3.11
**Effort:** MEDIUM | **Risk:** HIGH

1. Create new venv with Python 3.11
2. Reinstall all dependencies
3. Verify all code works

**Risk:** May break other dependencies expecting 3.12+

### Option C: Accept MCP-Only Access (CURRENT)
**Effort:** NONE | **Risk:** LOW

Continue using MCP servers for all TypeDB operations.
Direct driver access deferred until server upgrade.

**Trade-off:** Tests less direct, but fully functional

## Decision

**Selected: Option C (Accept MCP-Only Access)** pending server upgrade planning.

Rationale:
- MCP servers provide full TypeDB functionality
- No immediate need for direct driver access
- Server upgrade should be planned separately (new GAP)

## Validation Tests

- [x] `pip install typedb-driver==3.7.0` succeeds
- [ ] ~~Direct TypeDB connection works~~ BLOCKED by server version
- [x] MCP servers functional (gov-core, gov-tasks operational)
- [x] REST API tests pass (8/9 passing)

## Follow-up Task

Create **GAP-TYPEDB-UPGRADE-001**: Plan TypeDB Server 3.x upgrade

---

*Per GAP-DOC-01-v1: Evidence file for gap documentation*

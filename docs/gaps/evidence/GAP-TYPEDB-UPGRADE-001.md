# GAP-TYPEDB-UPGRADE-001: TypeDB 3.x Server Upgrade Plan

**Priority:** HIGH | **Category:** infrastructure | **Status:** IN_PROGRESS (Phase 2 Done, Phase 3 Ready)
**Created:** 2026-01-17 | **Depends On:** GAP-TYPEDB-DRIVER-001 (BLOCKED)

---

## Summary

Plan for upgrading TypeDB Server from 2.29.1 to 3.7.x to resolve Python 3.13 driver incompatibility.

## Current State

| Component | Version | Status |
|-----------|---------|--------|
| TypeDB Server | 2.29.1 | Running |
| typedb-driver | 2.29.2 | Installed (container) |
| Python | 3.13 | Host system |
| Python | 3.12 | Container |

**Problem:** Python 3.13 cannot use typedb-driver 2.x (compiled for 3.8-3.11).

## Target State

| Component | Version | Status |
|-----------|---------|--------|
| TypeDB Server | 3.7.3 | Target |
| typedb-driver | 3.7.x | To install |
| Python | 3.13 | Compatible |

## Migration Plan

### Phase 1: Preparation (TDD Tests)

**Status:** ✅ DONE (2026-01-17)

- [x] Create unit tests for 3.x driver API
- [x] Create component tests for 3.x connection
- [x] Create TypeDB3BaseClient wrapper
- [x] Document API changes

**Files Created:**
- `tests/unit/test_typedb3_driver.py` - Unit tests
- `tests/component/test_typedb3_connection.py` - Component tests
- `governance/typedb/base3.py` - 3.x client wrapper

### Phase 2: Schema Migration

**Status:** ✅ DONE (2026-01-17)

**Key Finding:** TypeDB 3.x schemas are NOT backward compatible with 2.x.

**Breaking Changes Identified:**
| 2.x Syntax | 3.x Syntax | Count |
|------------|------------|-------|
| `name sub entity,` | `entity name,` | 15 |
| `name sub relation,` | `relation name,` | 33 |
| `name sub attribute, value TYPE;` | `attribute name value TYPE;` | 116 |
| `rule X: when {...} then {...};` | `fun X() -> {...} {...}` | 5 |

**Files Created:**
- `scripts/schema_2x_to_3x.py` - Automated converter
- `governance/schema_3x/*.tql` - 19 converted schema files

**Automated Conversion Stats:**
- 920 lines converted
- 164 definitions updated to kind-first syntax
- 5 inference rules marked for manual conversion to functions

**Manual Work Required:**
1. Review cardinality annotations (@card) on owns/plays
2. Convert inference rules to functions (5 rules)
3. Test schema against TypeDB 3.x server

### Phase 3: Server Upgrade

**Status:** ⚠️ READY (Requires Manual Confirmation - Destructive)

**Prerequisites verified:**
- [x] Schema converted (governance/schema_3x/)
- [x] Data file exists (governance/data.tql - 658 lines, 61 rules)
- [x] Schema loader script ready (scripts/load-schema.sh)
- [x] MCP servers can reload after restart

**⚠️ WARNING:** This phase clears the TypeDB data volume. All existing data will be lost.

**Execution procedure:**
```bash
# Step 1: Stop all services
podman compose --profile cpu stop

# Step 2: Backup current data volume (safety)
cp -r /home/oderid/Documents/Docker/typedb_data /home/oderid/Documents/Docker/typedb_data_backup_2x

# Step 3: Clear data volume (DESTRUCTIVE)
rm -rf /home/oderid/Documents/Docker/typedb_data/*

# Step 4: Update docker-compose.yml (see below)

# Step 5: Start TypeDB 3.x
podman compose --profile cpu up -d typedb

# Step 6: Verify TypeDB 3.x running
podman exec platform_typedb_1 typedb server --version

# Step 7: Reload schema with 3.x loader (after Phase 5)
scripts/load-schema.sh --modular
```

**docker-compose.yml change:**
```yaml
typedb:
  image: docker.io/typedb/typedb:3.0.8  # Was: vaticle/typedb:latest (2.29.1)
```

**Note:** TypeDB 3.x uses `typedb/typedb` image, not `vaticle/typedb`.

### Phase 4: Driver Upgrade

**Status:** TODO

1. Update requirements.txt:
   ```
   # Old
   typedb-driver>=2.29.0,<3.0.0

   # New
   typedb-driver>=3.7.0,<4.0.0
   ```

2. Update Dockerfile:
   ```dockerfile
   RUN pip install typedb-driver>=3.7.0
   ```

3. Rebuild container:
   ```bash
   scripts/rebuild.sh
   ```

### Phase 5: Code Migration

**Status:** TODO

1. Update connection code:
   ```python
   # Old 2.x
   from typedb.driver import TypeDB
   driver = TypeDB.core_driver(address)

   # New 3.x
   from typedb.driver import TypeDB, Credentials, DriverOptions
   creds = Credentials('', '')
   opts = DriverOptions(is_tls_enabled=False)
   driver = TypeDB.driver(address, creds, opts)
   ```

2. Update query execution:
   ```python
   # Old 2.x
   tx.query.match(query)
   tx.query.insert(query)
   tx.query.define(schema)

   # New 3.x (unified)
   tx.query("match query")
   tx.query("insert query")
   tx.query("define schema")
   ```

3. Migrate rules to functions (if using inference):
   ```typeql
   # Old 2.x rule
   rule dep-transitive:
   when {
     (dependent: $a, dependency: $b) isa depends-on;
     (dependent: $b, dependency: $c) isa depends-on;
   } then {
     (dependent: $a, dependency: $c) isa transitive-dependency;
   };

   # New 3.x function
   fun transitive_deps($a: rule) -> { rule } {
     match
       (dependent: $a, dependency: $b) isa depends-on;
       (dependent: $b, dependency: $c) isa depends-on;
     return { $c };
   }
   ```

### Phase 6: Verification

**Status:** TODO

1. Run unit tests:
   ```bash
   scripts/pytest.sh tests/unit/test_typedb3_driver.py -v
   ```

2. Run component tests:
   ```bash
   TYPEDB_VERSION=3 scripts/pytest.sh tests/component/test_typedb3_connection.py -v
   ```

3. Run E2E tests:
   ```bash
   scripts/pytest.sh tests/e2e/ -v
   ```

4. Verify data integrity:
   - All 50 rules migrated
   - All 82 tasks migrated
   - All 22 sessions migrated
   - All relationships preserved

## Rollback Plan

If migration fails:

1. Stop new container:
   ```bash
   podman compose stop typedb
   ```

2. Restore 2.x image:
   ```yaml
   image: docker.io/vaticle/typedb:2.29.1
   ```

3. Restore data volume backup

4. Restart:
   ```bash
   podman compose --profile cpu up -d typedb
   ```

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Schema incompatibility | Test schema conversion first |
| Data loss | Backup before migration |
| Inference behavior | Document expected rule outputs |
| Performance regression | Run benchmarks before/after |

## Timeline

| Phase | Effort | Dependencies | Status |
|-------|--------|--------------|--------|
| Phase 1: TDD Tests | 1 hour | None | ✅ DONE |
| Phase 2: Schema | 2 hours | None | ✅ DONE |
| Phase 3: Server | 1 hour | Phase 2, Confirmation | ⚠️ READY |
| Phase 4: Driver | 30 min | Phase 3 | TODO |
| Phase 5: Code | 4-8 hours | Phase 4 | TODO |
| Phase 6: Verify | 2 hours | Phase 5 | TODO |

**Progress:** 2/6 phases complete, 1 phase ready for execution
**Remaining Estimate:** 6-12 hours

## Sources

- [TypeDB 2.x to 3.x: Migration Process](https://typedb.com/docs/reference/typedb-2-vs-3/process/)
- [TypeDB 2.x to 3.x: What's Changed](https://typedb.com/docs/reference/typedb-2-vs-3/diff/)
- [TypeDB 3.0 Schema Migration](https://typedb.com/fundamentals/schema-and-data-migration-3-0/)

---

*Per GAP-DOC-01-v1: Evidence file for gap documentation*

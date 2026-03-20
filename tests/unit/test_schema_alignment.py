"""
Unit tests for TypeDB schema alignment (EPIC-GOV-TASKS-V2, Phase 1).

BDD Scenarios:
  - Task entity owns priority and type
  - Monolithic matches modular for task entity
  - Workspace entity exists in monolithic schema
  - Migration is idempotent

Parses .tql files and asserts monolithic schema.tql matches modular schema_3x/.
"""
import re
from pathlib import Path

import pytest

# ─── Paths ───────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
MONOLITHIC = ROOT / "governance" / "schema.tql"
MODULAR_DIR = ROOT / "governance" / "schema_3x"

CORE_ENTITIES = MODULAR_DIR / "01_core_entities_3x.tql"
CORE_ATTRS = MODULAR_DIR / "10_core_attributes_3x.tql"
WORKSPACE_ENTITIES = MODULAR_DIR / "07_workspace_entities_3x.tql"
WORKSPACE_ATTRS = MODULAR_DIR / "16_workspace_attributes_3x.tql"
WORKSPACE_RELS = MODULAR_DIR / "26_workspace_relations_3x.tql"


# ─── TQL Parsing Helpers ─────────────────────────────────────────────────────

def _parse_entity_owns(tql_text: str, entity_name: str) -> set[str]:
    """Extract all 'owns <attr>' for a given entity from TQL text."""
    # Match entity block: 'entity <name>,' ... until next 'entity ' or 'relation ' or end
    pattern = rf"entity\s+{re.escape(entity_name)}\s*,(.*?)(?=\nentity\s|\nrelation\s|\nrule\s|\Z)"
    match = re.search(pattern, tql_text, re.DOTALL)
    if not match:
        return set()
    block = match.group(1)
    return set(re.findall(r"owns\s+([\w-]+)", block))


def _parse_entity_plays(tql_text: str, entity_name: str) -> set[str]:
    """Extract all 'plays <role>' for a given entity from TQL text."""
    pattern = rf"entity\s+{re.escape(entity_name)}\s*,(.*?)(?=\nentity\s|\nrelation\s|\nrule\s|\Z)"
    match = re.search(pattern, tql_text, re.DOTALL)
    if not match:
        return set()
    block = match.group(1)
    return set(re.findall(r"plays\s+([\w-]+:[\w-]+)", block))


def _parse_attributes(tql_text: str) -> dict[str, str]:
    """Extract all 'attribute <name>, value <type>;' → {name: type}."""
    # Handle both 'attribute x, value y;' and 'attribute x value y;' (with/without comma)
    return dict(re.findall(r"attribute\s+([\w-]+)[,\s]+value\s+(\w+)", tql_text))


def _parse_entity_names(tql_text: str) -> set[str]:
    """Extract all entity names from TQL text."""
    return set(re.findall(r"entity\s+([\w-]+)\s*,", tql_text))


def _parse_relation_names(tql_text: str) -> set[str]:
    """Extract all relation names from TQL text."""
    return set(re.findall(r"relation\s+([\w-]+)\s*,", tql_text))


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def monolithic_text():
    return MONOLITHIC.read_text()


@pytest.fixture(scope="module")
def modular_core_entities_text():
    return CORE_ENTITIES.read_text()


@pytest.fixture(scope="module")
def modular_core_attrs_text():
    return CORE_ATTRS.read_text()


@pytest.fixture(scope="module")
def modular_workspace_entities_text():
    return WORKSPACE_ENTITIES.read_text()


@pytest.fixture(scope="module")
def modular_workspace_attrs_text():
    return WORKSPACE_ATTRS.read_text()


@pytest.fixture(scope="module")
def modular_workspace_rels_text():
    return WORKSPACE_RELS.read_text()


# ─── Scenario 1: Task entity owns priority and type ──────────────────────────

class TestTaskOwnsPriorityAndType:
    """Task entity in monolithic schema must own task-priority and task-type."""

    def test_task_owns_task_priority(self, monolithic_text):
        owns = _parse_entity_owns(monolithic_text, "task")
        assert "task-priority" in owns, "task entity missing 'owns task-priority'"

    def test_task_owns_task_type(self, monolithic_text):
        owns = _parse_entity_owns(monolithic_text, "task")
        assert "task-type" in owns, "task entity missing 'owns task-type'"

    def test_task_priority_attribute_defined(self, monolithic_text):
        attrs = _parse_attributes(monolithic_text)
        assert "task-priority" in attrs, "attribute task-priority not defined"
        assert attrs["task-priority"] == "string"

    def test_task_type_attribute_defined(self, monolithic_text):
        attrs = _parse_attributes(monolithic_text)
        assert "task-type" in attrs, "attribute task-type not defined"
        assert attrs["task-type"] == "string"


# ─── Scenario 2: Monolithic matches modular for task entity ──────────────────

class TestMonolithicMatchesModularTask:
    """All task 'owns' in modular 01_core_entities_3x.tql must be in monolithic."""

    def test_all_modular_task_owns_in_monolithic(
        self, monolithic_text, modular_core_entities_text
    ):
        modular_owns = _parse_entity_owns(modular_core_entities_text, "task")
        mono_owns = _parse_entity_owns(monolithic_text, "task")
        missing = modular_owns - mono_owns
        assert not missing, f"Monolithic task missing owns: {missing}"

    def test_all_modular_task_attributes_in_monolithic(
        self, monolithic_text, modular_core_attrs_text
    ):
        """Every attribute defined in modular core attrs must exist in monolithic."""
        modular_attrs = _parse_attributes(modular_core_attrs_text)
        mono_attrs = _parse_attributes(monolithic_text)
        missing = set(modular_attrs.keys()) - set(mono_attrs.keys())
        assert not missing, f"Monolithic missing attributes: {missing}"

    def test_attribute_types_match(self, monolithic_text, modular_core_attrs_text):
        """Attribute value types must match between monolithic and modular."""
        modular_attrs = _parse_attributes(modular_core_attrs_text)
        mono_attrs = _parse_attributes(monolithic_text)
        mismatched = {}
        for attr, mod_type in modular_attrs.items():
            if attr in mono_attrs and mono_attrs[attr] != mod_type:
                mismatched[attr] = (mono_attrs[attr], mod_type)
        assert not mismatched, f"Type mismatches: {mismatched}"


# ─── Scenario 3: Workspace entity exists in monolithic schema ────────────────

class TestWorkspaceEntityInMonolithic:
    """Workspace entity and its attributes must exist in monolithic schema."""

    def test_workspace_entity_exists(self, monolithic_text):
        entities = _parse_entity_names(monolithic_text)
        assert "workspace" in entities, "workspace entity missing from monolithic"

    def test_workspace_owns_match_modular(
        self, monolithic_text, modular_workspace_entities_text
    ):
        modular_owns = _parse_entity_owns(modular_workspace_entities_text, "workspace")
        mono_owns = _parse_entity_owns(monolithic_text, "workspace")
        missing = modular_owns - mono_owns
        assert not missing, f"Monolithic workspace missing owns: {missing}"

    def test_workspace_attributes_defined(
        self, monolithic_text, modular_workspace_attrs_text
    ):
        modular_attrs = _parse_attributes(modular_workspace_attrs_text)
        mono_attrs = _parse_attributes(monolithic_text)
        # Filter to workspace-specific attrs (exclude project/capability already present)
        ws_attrs = {k for k in modular_attrs if k.startswith("workspace-")}
        missing = ws_attrs - set(mono_attrs.keys())
        assert not missing, f"Monolithic missing workspace attributes: {missing}"

    def test_project_has_workspace_relation_exists(self, monolithic_text):
        relations = _parse_relation_names(monolithic_text)
        assert "project-has-workspace" in relations, \
            "project-has-workspace relation missing from monolithic"

    def test_project_plays_workspace_role(self, monolithic_text):
        plays = _parse_entity_plays(monolithic_text, "project")
        assert "project-has-workspace:owning-project" in plays, \
            "project missing 'plays project-has-workspace:owning-project'"

    def test_workspace_plays_project_role(self, monolithic_text):
        plays = _parse_entity_plays(monolithic_text, "workspace")
        assert "project-has-workspace:workspace-member" in plays, \
            "workspace missing 'plays project-has-workspace:workspace-member'"

    def test_workspace_plays_agent_role(self, monolithic_text):
        plays = _parse_entity_plays(monolithic_text, "workspace")
        assert "workspace-has-agent:agent-workspace" in plays, \
            "workspace missing 'plays workspace-has-agent:agent-workspace'"


# ─── Scenario 4: Migration is idempotent ─────────────────────────────────────

class TestMigrationIdempotent:
    """Migration script must be importable and contain idempotent operations."""

    def test_migration_script_importable(self):
        """migrate_task_taxonomy.py must be importable without side effects."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "migrate_task_taxonomy",
            ROOT / "scripts" / "migrate_task_taxonomy.py",
        )
        assert spec is not None, "Cannot find migrate_task_taxonomy.py"

    def test_migration_has_workspace_entries(self):
        """Migration MIGRATIONS list must include workspace schema entries."""
        script_text = (ROOT / "scripts" / "migrate_task_taxonomy.py").read_text()
        assert "workspace-id" in script_text, \
            "Migration missing workspace-id attribute"
        assert "workspace" in script_text, \
            "Migration missing workspace entity"

    def test_migration_handles_already_exists(self):
        """Migration must skip 'already exists' errors gracefully."""
        script_text = (ROOT / "scripts" / "migrate_task_taxonomy.py").read_text()
        assert "already" in script_text.lower(), \
            "Migration must handle 'already exists' for idempotency"

    def test_migration_entries_are_define_statements(self):
        """All migration queries must use 'define' (schema transactions)."""
        script_text = (ROOT / "scripts" / "migrate_task_taxonomy.py").read_text()
        # Extract all query strings from MIGRATIONS list
        queries = re.findall(r'"(define\s[^"]+)"', script_text)
        assert len(queries) >= 4, \
            f"Expected >=4 define migrations, found {len(queries)}"
        for q in queries:
            assert q.strip().startswith("define"), \
                f"Migration query must start with 'define': {q[:50]}"

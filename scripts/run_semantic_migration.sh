#!/bin/bash
# TypeDB Semantic ID Migration Script
# Per META-TAXON-01-v1: Rule Taxonomy & Management
# Run from project root: ./scripts/run_semantic_migration.sh

set -e

TYPEDB_CMD="podman exec sim-ai_typedb_1 /opt/typedb-all-linux-x86_64/typedb console"
DB="sim-ai-governance"

echo "=========================================="
echo "TypeDB Semantic ID Migration"
echo "=========================================="

# Define the mapping
declare -A MAPPING=(
    ["RULE-001"]="SESSION-EVID-01-v1"
    ["RULE-002"]="ARCH-EBMSF-01-v1"
    ["RULE-003"]="GOV-AUDIT-01-v1"
    ["RULE-004"]="SESSION-DSP-01-v1"
    ["RULE-005"]="RECOVER-MEM-01-v1"
    ["RULE-006"]="GOV-TRUST-01-v1"
    ["RULE-007"]="ARCH-MCP-01-v1"
    ["RULE-008"]="TEST-GUARD-01-v1"
    ["RULE-009"]="ARCH-VERSION-01-v1"
    ["RULE-010"]="GOV-RULE-01-v1"
    ["RULE-011"]="GOV-BICAM-01-v1"
    ["RULE-012"]="SESSION-DSM-01-v1"
    ["RULE-013"]="GOV-PROP-01-v1"
    ["RULE-014"]="WORKFLOW-AUTO-01-v1"
    ["RULE-015"]="WORKFLOW-RD-01-v1"
    ["RULE-016"]="ARCH-INFRA-01-v1"
    ["RULE-017"]="UI-TRAME-01-v1"
    ["RULE-018"]="GOV-TRUST-02-v1"
    ["RULE-019"]="GOV-PROP-02-v1"
    ["RULE-020"]="TEST-COMP-01-v1"
    ["RULE-021"]="SAFETY-HEALTH-01-v1"
    ["RULE-022"]="REPORT-EXEC-01-v1"
    ["RULE-023"]="TEST-E2E-01-v1"
    ["RULE-024"]="RECOVER-AMNES-01-v1"
    ["RULE-025"]="GOV-PROP-03-v1"
    ["RULE-026"]="GOV-RULE-02-v1"
    ["RULE-027"]="CONTAINER-RESTART-01-v1"
    ["RULE-028"]="WORKFLOW-SEQ-01-v1"
    ["RULE-029"]="GOV-RULE-03-v1"
    ["RULE-030"]="WORKFLOW-DEPLOY-01-v1"
    ["RULE-031"]="WORKFLOW-AUTO-02-v1"
    ["RULE-032"]="DOC-SIZE-01-v1"
    ["RULE-033"]="DOC-PARTIAL-01-v1"
    ["RULE-034"]="DOC-LINK-01-v1"
    ["RULE-035"]="CONTAINER-SHELL-01-v1"
    ["RULE-036"]="ARCH-MCP-02-v1"
    ["RULE-037"]="WORKFLOW-VALID-01-v1"
    ["RULE-040"]="ARCH-INFRA-02-v1"
    ["RULE-041"]="RECOVER-CRASH-01-v1"
    ["RULE-042"]="SAFETY-DESTR-01-v1"
    ["RULE-043"]="META-TAXON-01-v1"
)

UPDATED=0
SKIPPED=0
ERRORS=0

for LEGACY_ID in "${!MAPPING[@]}"; do
    SEMANTIC_ID="${MAPPING[$LEGACY_ID]}"

    # Run the insert query
    RESULT=$($TYPEDB_CMD \
        --command "transaction $DB data write" \
        --command "match \$r isa rule-entity, has rule-id \"$LEGACY_ID\"; insert \$r has semantic-id \"$SEMANTIC_ID\";" \
        --command "commit" 2>&1) || true

    if echo "$RESULT" | grep -q "committed"; then
        echo "✓ $LEGACY_ID -> $SEMANTIC_ID"
        ((UPDATED++))
    elif echo "$RESULT" | grep -q "already"; then
        echo "- $LEGACY_ID (already has semantic-id)"
        ((SKIPPED++))
    else
        echo "✗ $LEGACY_ID: $RESULT"
        ((ERRORS++))
    fi
done

echo ""
echo "=========================================="
echo "Migration Complete"
echo "  Updated: $UPDATED"
echo "  Skipped: $SKIPPED"
echo "  Errors:  $ERRORS"
echo "=========================================="

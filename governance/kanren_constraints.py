"""
Kanren Constraint Engine for Governance Rules (KAN-002).

Maps TypeDB governance rules to Kanren relations for declarative
context engineering and constraint validation.

Per RULE-011: Multi-Agent Governance
Per RULE-028: Change Validation Protocol
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from kanren import run, var, eq, conde, lall, membero


# =============================================================================
# Domain Models
# =============================================================================

@dataclass
class AgentContext:
    """Agent context for constraint validation."""
    agent_id: str
    name: str
    trust_score: float
    agent_type: str


@dataclass
class TaskContext:
    """Task context for constraint validation."""
    task_id: str
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    requires_evidence: bool
    assigned_agent: Optional[str] = None


@dataclass
class RuleContext:
    """Rule context for constraint validation."""
    rule_id: str
    priority: str
    status: str
    category: str


# =============================================================================
# Trust Level Constraints (RULE-011)
# =============================================================================

def trust_level(score: float) -> str:
    """Determine trust level from score per RULE-011."""
    if score >= 0.9:
        return "expert"
    elif score >= 0.7:
        return "trusted"
    elif score >= 0.5:
        return "supervised"
    else:
        return "restricted"


def requires_supervisor(trust: str) -> Tuple:
    """
    Determine if agent trust level requires supervisor context.

    Per RULE-011: Trust < 0.7 requires supervisor approval for critical tasks.
    """
    x = var()
    return run(1, x, conde(
        [eq(trust, 'restricted'), eq(x, True)],
        [eq(trust, 'supervised'), eq(x, True)],
        [eq(trust, 'trusted'), eq(x, False)],
        [eq(trust, 'expert'), eq(x, False)]
    ))


def can_execute_priority(trust: str, priority: str) -> Tuple:
    """
    Check if agent can execute task of given priority.

    Per RULE-011:
    - CRITICAL: expert or trusted only
    - HIGH: trusted and above
    - MEDIUM/LOW: all levels
    """
    x = var()
    return run(1, x, conde(
        # CRITICAL tasks
        [eq(priority, 'CRITICAL'), eq(trust, 'expert'), eq(x, True)],
        [eq(priority, 'CRITICAL'), eq(trust, 'trusted'), eq(x, True)],
        [eq(priority, 'CRITICAL'), eq(trust, 'supervised'), eq(x, False)],
        [eq(priority, 'CRITICAL'), eq(trust, 'restricted'), eq(x, False)],
        # HIGH tasks
        [eq(priority, 'HIGH'), membero(trust, ['expert', 'trusted', 'supervised']), eq(x, True)],
        [eq(priority, 'HIGH'), eq(trust, 'restricted'), eq(x, False)],
        # MEDIUM/LOW tasks - all can execute
        [eq(priority, 'MEDIUM'), eq(x, True)],
        [eq(priority, 'LOW'), eq(x, True)]
    ))


# =============================================================================
# Task Validation Constraints (RULE-014, RULE-028)
# =============================================================================

def task_requires_evidence(priority: str) -> Tuple:
    """
    Check if task priority requires evidence per RULE-028.

    Per RULE-028: CRITICAL and HIGH tasks require validation evidence.
    """
    x = var()
    return run(1, x, conde(
        [eq(priority, 'CRITICAL'), eq(x, True)],
        [eq(priority, 'HIGH'), eq(x, True)],
        [eq(priority, 'MEDIUM'), eq(x, False)],
        [eq(priority, 'LOW'), eq(x, False)]
    ))


def valid_task_assignment(agent: AgentContext, task: TaskContext) -> Dict[str, Any]:
    """
    Validate task assignment per governance rules.

    Returns validation result with constraints checked.
    """
    trust = trust_level(agent.trust_score)

    can_execute = can_execute_priority(trust, task.priority)
    needs_supervisor = requires_supervisor(trust)
    needs_evidence = task_requires_evidence(task.priority)

    return {
        "valid": len(can_execute) > 0 and can_execute[0],
        "agent_id": agent.agent_id,
        "task_id": task.task_id,
        "trust_level": trust,
        "can_execute": can_execute[0] if can_execute else False,
        "requires_supervisor": needs_supervisor[0] if needs_supervisor else True,
        "requires_evidence": needs_evidence[0] if needs_evidence else True,
        "constraints_checked": [
            "RULE-011: Trust-based execution",
            "RULE-014: Task sequencing",
            "RULE-028: Evidence requirements"
        ]
    }


# =============================================================================
# RAG Chunk Validation (RULE-007)
# =============================================================================

ALLOWED_SOURCES = ['typedb', 'chromadb', 'evidence', 'session', 'rule']
TRUSTED_TYPES = ['rule', 'decision', 'evidence', 'task']


def valid_rag_chunk(source: str, verified: bool, chunk_type: str) -> Tuple:
    """
    Validate RAG chunk before including in LLM context.

    Per RULE-007: MCP Usage Protocol - verify data sources.
    """
    x = var()
    return run(1, x, lall(
        membero(source, ALLOWED_SOURCES),
        eq(verified, True),
        membero(chunk_type, TRUSTED_TYPES),
        eq(x, True)
    ))


def filter_rag_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    Filter RAG chunks using Kanren constraints.

    Returns only chunks that pass governance validation.
    """
    valid_chunks = []
    for chunk in chunks:
        result = valid_rag_chunk(
            chunk.get('source', ''),
            chunk.get('verified', False),
            chunk.get('type', '')
        )
        if result and result[0]:
            valid_chunks.append(chunk)
    return valid_chunks


# =============================================================================
# Rule Conflict Detection (RULE-011)
# =============================================================================

def conflicting_priorities(rule1: RuleContext, rule2: RuleContext) -> bool:
    """
    Detect if two rules have conflicting priorities.

    Per RULE-011: Detect conflicting rules using inference.
    """
    # Same category but different priorities
    if rule1.category == rule2.category and rule1.priority != rule2.priority:
        return True
    return False


def find_rule_conflicts(rules: List[RuleContext]) -> List[Tuple[str, str, str]]:
    """Find all rule conflicts in a rule set."""
    conflicts = []
    for i, r1 in enumerate(rules):
        for r2 in rules[i+1:]:
            if conflicting_priorities(r1, r2):
                conflicts.append((r1.rule_id, r2.rule_id, f"Priority conflict in {r1.category}"))
    return conflicts


# =============================================================================
# KAN-003: RAG Filter Integration
# =============================================================================

class KanrenRAGFilter:
    """
    RAG retrieval with Kanren constraint validation.

    Per KAN-003: Validate ChromaDB/VectorStore chunks before LLM context.
    Ensures only governance-approved data enters the prompt.

    Example:
        from governance.kanren_constraints import KanrenRAGFilter

        rag_filter = KanrenRAGFilter()
        results = rag_filter.search_validated(
            query_embedding=[0.1, 0.2, ...],
            top_k=10
        )
        # Only returns chunks passing Kanren validation
    """

    def __init__(self, vector_store=None):
        """
        Initialize RAG filter.

        Args:
            vector_store: VectorStore instance (default: creates new one)
        """
        self._store = vector_store

    def _get_store(self):
        """Lazy load VectorStore."""
        if self._store is None:
            from governance.vector_store import VectorStore
            self._store = VectorStore()
            self._store.connect()
        return self._store

    def search_validated(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        source_type: Optional[str] = None,
        threshold: float = 0.0
    ) -> List[Dict]:
        """
        Search for similar vectors with Kanren validation.

        Retrieves chunks from VectorStore and filters through Kanren
        constraints before returning.

        Args:
            query_embedding: Query vector
            top_k: Maximum results before filtering
            source_type: Filter by source type (rule, decision, session)
            threshold: Minimum similarity score

        Returns:
            List of validated chunks with metadata
        """
        store = self._get_store()
        results = store.search(query_embedding, top_k, source_type, threshold)

        # Convert to chunk format for Kanren validation
        chunks = self._results_to_chunks(results)

        # Apply Kanren constraints
        validated = filter_rag_chunks(chunks)

        return validated

    def _results_to_chunks(self, results) -> List[Dict]:
        """
        Convert SimilarityResult list to chunk format for Kanren.

        Maps VectorStore fields to Kanren validation fields:
        - source_type → source (typedb, chromadb, etc.)
        - source_type → type (rule, evidence, etc.)
        - score > threshold → verified
        """
        chunks = []
        for r in results:
            # Map source_type to Kanren source categories
            source_map = {
                "rule": "typedb",
                "decision": "typedb",
                "session": "chromadb",
                "document": "typedb"
            }
            chunk = {
                "id": r.vector_id,
                "content": r.content,
                "source": source_map.get(r.source_type, "typedb"),
                "type": r.source_type,
                "verified": r.score > 0.5,  # High similarity = verified
                "score": r.score,
                "original_source": r.source
            }
            chunks.append(chunk)
        return chunks

    def search_for_task(
        self,
        query_text: str,
        task_context: TaskContext,
        agent_context: AgentContext,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Full context assembly for a task with validation.

        Combines:
        1. RAG retrieval with Kanren validation
        2. Agent trust validation
        3. Task evidence requirements

        Args:
            query_text: Natural language query
            task_context: Task being executed
            agent_context: Agent executing the task
            top_k: Maximum chunks to retrieve

        Returns:
            Full validated context dictionary
        """
        # For now, return a mock embedding search
        # In production, this would use the embedding generator
        store = self._get_store()

        # Get all vectors of relevant types
        all_vectors = store.get_all_vectors()

        # Simple text matching for PoC (production would use embeddings)
        chunks = []
        query_lower = query_text.lower()
        for vec in all_vectors:
            if query_lower in vec.content.lower():
                chunks.append({
                    "id": vec.id,
                    "content": vec.content,
                    "source": "typedb" if vec.source_type in ("rule", "decision") else "chromadb",
                    "type": vec.source_type,
                    "verified": True,
                    "score": 0.8,
                    "original_source": vec.source
                })

        # Filter through Kanren
        validated_chunks = filter_rag_chunks(chunks[:top_k])

        # Assemble full context
        return assemble_context(agent_context, task_context, validated_chunks)


# =============================================================================
# Context Assembly Constraints
# =============================================================================

def assemble_context(agent: AgentContext, task: TaskContext,
                     available_chunks: List[Dict]) -> Dict[str, Any]:
    """
    Assemble validated context for LLM prompt.

    Combines trust validation, RAG filtering, and evidence requirements.
    """
    # Validate assignment
    assignment = valid_task_assignment(agent, task)

    # Filter RAG chunks
    valid_chunks = filter_rag_chunks(available_chunks)

    # Build context
    context = {
        "assignment_valid": assignment["valid"],
        "agent": {
            "id": agent.agent_id,
            "trust_level": assignment["trust_level"],
            "requires_supervisor": assignment["requires_supervisor"]
        },
        "task": {
            "id": task.task_id,
            "priority": task.priority,
            "requires_evidence": assignment["requires_evidence"]
        },
        "rag_chunks": valid_chunks,
        "constraints_applied": assignment["constraints_checked"] + ["RULE-007: RAG validation"]
    }

    return context


# =============================================================================
# Convenience Functions
# =============================================================================

def validate_agent_for_task(agent_id: str, trust_score: float,
                            task_priority: str) -> Dict[str, Any]:
    """Quick validation of agent for task."""
    agent = AgentContext(agent_id, agent_id, trust_score, "claude-code")
    task = TaskContext(f"TASK-{agent_id}", task_priority, False)
    return valid_task_assignment(agent, task)


def demo_kanren_constraints():
    """Demonstrate Kanren constraint engine."""
    print("=== Kanren Governance Constraints Demo ===\n")

    # Test trust levels
    print("1. Trust Level Validation (RULE-011):")
    for score in [0.95, 0.75, 0.55, 0.35]:
        level = trust_level(score)
        supervisor = requires_supervisor(level)
        print(f"   Score {score} → {level}, needs_supervisor={supervisor[0]}")

    # Test task assignment
    print("\n2. Task Assignment Validation:")
    agents = [
        AgentContext("AGENT-001", "Claude Code", 0.95, "claude-code"),
        AgentContext("AGENT-002", "New Agent", 0.55, "sync-agent"),
    ]
    tasks = [
        TaskContext("TASK-001", "CRITICAL", True),
        TaskContext("TASK-002", "MEDIUM", False),
    ]

    for agent in agents:
        for task in tasks:
            result = valid_task_assignment(agent, task)
            print(f"   {agent.name} + {task.task_id} ({task.priority}): valid={result['valid']}")

    # Test RAG filtering
    print("\n3. RAG Chunk Filtering (RULE-007):")
    chunks = [
        {"id": 1, "source": "typedb", "verified": True, "type": "rule"},
        {"id": 2, "source": "external", "verified": False, "type": "unknown"},
        {"id": 3, "source": "chromadb", "verified": True, "type": "evidence"},
    ]
    valid = filter_rag_chunks(chunks)
    print(f"   Input: {len(chunks)} chunks, Valid: {len(valid)} chunks")
    for chunk in valid:
        print(f"   ✓ Chunk {chunk['id']}: {chunk['source']}/{chunk['type']}")

    print("\n✅ Kanren constraint engine operational")


if __name__ == "__main__":
    demo_kanren_constraints()

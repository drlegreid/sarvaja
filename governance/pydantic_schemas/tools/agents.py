"""
Agent Trust Score Tools
=======================
Type-safe trust score calculation operations.

Per GOV-BICAM-01-v1: Multi-Agent Governance Protocol
Per RULE-017: Type-Safe Tool Development
Per GAP-FILE-010: Extracted from pydantic_tools.py

Trust Formula (GOV-BICAM-01-v1):
Trust = (Compliance x 0.4) + (Accuracy x 0.3) + (Consistency x 0.2) + (Tenure x 0.1)

Created: 2024-12-28
"""

from ..models import TrustScoreRequest, TrustScoreResult


def calculate_trust_score_typed(request: TrustScoreRequest) -> TrustScoreResult:
    """
    Calculate trust score with type-safe request and result.

    Trust Formula (GOV-BICAM-01-v1):
    Trust = (Compliance x 0.4) + (Accuracy x 0.3) + (Consistency x 0.2) + (Tenure x 0.1)

    Args:
        request: Validated trust score request

    Returns:
        Structured trust score result
    """
    try:
        from governance.client import TypeDBClient

        client = TypeDBClient()
        if not client.connect():
            return TrustScoreResult(
                success=False,
                agent_id=request.agent_id,
                trust_score=0.0,
                vote_weight=0.0,
                error="Failed to connect to TypeDB"
            )

        try:
            query = f'''
                match
                    $a isa agent, has agent-id "{request.agent_id}";
                    $a has agent-name $name;
                    $a has trust-score $trust;
                    $a has compliance-rate $compliance;
                    $a has accuracy-rate $accuracy;
                    $a has tenure-days $tenure;
                select $name, $trust, $compliance, $accuracy, $tenure;
            '''

            results = client.execute_query(query)

            if not results:
                return TrustScoreResult(
                    success=False,
                    agent_id=request.agent_id,
                    trust_score=0.0,
                    vote_weight=0.0,
                    error=f"Agent {request.agent_id} not found"
                )

            result = results[0]
            trust_score = float(result.get('trust', 0.0))

            # Calculate vote weight per GOV-BICAM-01-v1
            vote_weight = 1.0 if trust_score >= 0.5 else trust_score

            return TrustScoreResult(
                success=True,
                agent_id=request.agent_id,
                agent_name=result.get('name'),
                trust_score=trust_score,
                vote_weight=vote_weight,
                components={
                    "compliance": float(result.get('compliance', 0.0)),
                    "accuracy": float(result.get('accuracy', 0.0)),
                    "tenure_days": int(result.get('tenure', 0))
                }
            )

        finally:
            client.close()

    except Exception as e:
        return TrustScoreResult(
            success=False,
            agent_id=request.agent_id,
            trust_score=0.0,
            vote_weight=0.0,
            error=str(e)
        )

"""
LangGraph Library for Robot Framework (Facade)
Combines all LangGraph workflow test libraries.
Migrated from tests/test_langgraph_workflow.py
Per: RF-007 Robot Framework Migration, DOC-SIZE-01-v1
"""
import sys
from pathlib import Path

# Add libs directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from LanggraphSchemaLibrary import LanggraphSchemaLibrary
from LanggraphNodesLibrary import LanggraphNodesLibrary
from LanggraphVotingLibrary import LanggraphVotingLibrary
from LanggraphWorkflowLibrary import LanggraphWorkflowLibrary


class LanggraphLibrary(
    LanggraphSchemaLibrary,
    LanggraphNodesLibrary,
    LanggraphVotingLibrary,
    LanggraphWorkflowLibrary
):
    """
    Facade library combining all LangGraph workflow test keywords.

    Split libraries:
    - LanggraphSchemaLibrary: State schema and constants (8 keywords)
    - LanggraphNodesLibrary: Node functions, submit/validate/assess (19 keywords)
    - LanggraphVotingLibrary: Voting and decision logic (6 keywords)
    - LanggraphWorkflowLibrary: Graph building, execution, MCP, visualization (10 keywords)

    Total: 43 keywords
    """

    ROBOT_LIBRARY_SCOPE = 'SUITE'

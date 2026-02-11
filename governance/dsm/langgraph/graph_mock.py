"""
DSP Mock LangGraph Classes + Diagram
=====================================
Mock StateGraph/CompiledMockGraph for when LangGraph is not installed.
ASCII diagram of DSP workflow.

Per DOC-SIZE-01-v1: Extracted from graph.py.
"""


class StateGraph:
    """Mock StateGraph for when LangGraph is not installed."""

    def __init__(self, state_type):
        self.state_type = state_type
        self.nodes = {}
        self.edges = []
        self.conditional_edges = []

    def add_node(self, name, func):
        self.nodes[name] = func

    def add_edge(self, from_node, to_node):
        self.edges.append((from_node, to_node))

    def add_conditional_edges(self, from_node, condition, mapping):
        self.conditional_edges.append((from_node, condition, mapping))

    def compile(self, checkpointer=None):
        return CompiledMockGraph(self)


class CompiledMockGraph:
    """Mock compiled graph that executes nodes in sequence."""

    def __init__(self, graph):
        self.graph = graph

    def stream(self, initial_state, config):
        """Execute nodes in linear fallback mode."""
        state = initial_state.copy()
        yield {"start": state}


class MemorySaver:
    """Mock memory saver."""
    pass


def print_dsp_workflow_diagram():
    """Print ASCII visualization of DSP workflow."""
    print("""
DSP LangGraph Workflow (with loop-back per GAP-WORKFLOW-LOOP-001):

    START
      │
      ▼
    [start]──failed──►[abort]
      │                  │
      │ success          │
      ▼                  │
    [audit]              │
      │                  │
      ├─critical─►[skip_to_report]──┐
      │                              │
      │ normal                       │
      ▼                              │
    [hypothesize]◄───────────────┐   │
      │                          │   │
      ▼                          │   │
    [measure]                    │   │
      │                     loop │   │
      ▼                (retry<3) │   │
    [optimize]                   │   │
      │                          │   │
      ▼                          │   │
    [validate]───failed──────────┘   │
      │                              │
      ├─failed(retries=3)►[report]◄──┘
      │                      │
      │ passed               │
      ▼                      │
    [dream]                  │
      │                      │
      └──────────────────────┘
                             │
                             ▼
                        [complete]
                             │
                             ▼
                            END
    """)

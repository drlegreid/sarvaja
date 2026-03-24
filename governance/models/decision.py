"""Decision models. Per GAP-UI-033, PLAN-UI-OVERHAUL-001 Task 4.2."""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class DecisionOption(BaseModel):
    """An option considered in a decision, with pros and cons."""
    label: str = Field(..., min_length=1, description="Option name")
    pros: List[str] = Field(default_factory=list, description="Advantages")
    cons: List[str] = Field(default_factory=list, description="Disadvantages")

class DecisionCreate(BaseModel):
    """Request model for creating a decision."""
    decision_id: str = Field(..., min_length=1, description="Unique decision ID (e.g., DECISION-010)")
    name: str = Field(..., min_length=1, description="Decision name/title")
    context: str = Field(..., min_length=1, description="Context/problem statement")
    rationale: str = Field(..., min_length=1, description="Reasoning for the decision")
    status: Literal["PENDING", "APPROVED", "REJECTED"] = Field(default="PENDING", description="Status")
    options: List[DecisionOption] = Field(default_factory=list, description="Options considered")
    selected_option: Optional[str] = Field(default=None, description="Label of chosen option")
    rules_applied: List[str] = Field(default_factory=list, description="Rule IDs to link via decision-affects")

class DecisionUpdate(BaseModel):
    """Request model for updating a decision."""
    name: Optional[str] = None
    context: Optional[str] = None
    rationale: Optional[str] = None
    status: Optional[Literal["PENDING", "APPROVED", "REJECTED"]] = None
    decision_date: Optional[str] = None
    options: Optional[List[DecisionOption]] = None
    selected_option: Optional[str] = None

class DecisionResponse(BaseModel):
    """Response model for a decision."""
    id: str
    name: str
    context: str
    rationale: str
    status: str
    decision_date: Optional[str] = None
    # Per GAP-DECISION-001: Rules affected by this decision
    linked_rules: List[str] = []
    options: List[DecisionOption] = Field(default_factory=list)
    selected_option: Optional[str] = None

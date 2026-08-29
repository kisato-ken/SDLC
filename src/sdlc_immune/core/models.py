from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

class NodeStatus(str, Enum):
    ACTIVE = "active"
    STALE = "stale"
    DEPRECATED = "deprecated"
    VALID = "valid"
    PASSING = "passing"
    FAILING = "failing"
    SYNCED = "synced"

class RelationType(str, Enum):
    TRACES_TO = "traces_to"
    IMPLEMENTS = "implements"
    DERIVED_FROM = "derived_from"
    FLAGS = "flags"

class BaseNode(BaseModel):
    id: str
    node_type: str
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class Requirement(BaseNode):
    node_type: str = "Requirement"
    title: str
    content: str
    status: NodeStatus = NodeStatus.ACTIVE

class Design(BaseNode):
    node_type: str = "Design"
    req_id: str
    content: str
    status: NodeStatus = NodeStatus.VALID

class Test(BaseNode):
    node_type: str = "Test"
    design_id: str
    name: str
    test_code: str
    status: NodeStatus = NodeStatus.PASSING

class CodeArtifact(BaseNode):
    node_type: str = "CodeArtifact"
    design_id: str
    file_path: str
    api_signature: str
    status: NodeStatus = NodeStatus.SYNCED

class RiskScore(BaseNode):
    node_type: str = "RiskScore"
    target_id: str
    target_type: str
    score: float
    rationale: str

class Incident(BaseNode):
    node_type: str = "Incident"
    title: str
    summary: str
    linked_req_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class Rule(BaseNode):
    node_type: str = "Rule"
    incident_id: Optional[str] = None
    pattern: str
    condition: str
    status: NodeStatus = NodeStatus.ACTIVE

class ConfirmationLog(BaseNode):
    node_type: str = "ConfirmationLog"
    target_node_id: str
    action: str
    user_override_status: Optional[str] = None
    reason: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class Edge(BaseModel):
    source_id: str
    target_id: str
    relation: RelationType
    metadata: Dict[str, Any] = Field(default_factory=dict)

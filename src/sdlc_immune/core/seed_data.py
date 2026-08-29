from .models import (
    Requirement, Design, Test, CodeArtifact, RiskScore, Incident, Rule,
    Edge, RelationType, NodeStatus
)
from .store import SDLCGraphStore

def seed_demo_data(store: SDLCGraphStore) -> None:
    # 1. Primary Requirement
    req = Requirement(
        id="REQ-2e9fa1",
        title="User Authentication & Token Management",
        content="System must validate OAuth2 tokens, refresh expired session tokens every 15 minutes, and log unauthorized access attempts.",
        status=NodeStatus.ACTIVE
    )
    store.add_node(req)

    # 2. Design derived from Requirement
    design = Design(
        id="DESIGN-2e9fa1-01",
        req_id="REQ-2e9fa1",
        content="Implement AuthController with validate_token() and refresh_token() endpoints using JWT HS256 algorithm.",
        status=NodeStatus.VALID
    )
    store.add_node(design)
    store.add_edge(Edge(source_id=design.id, target_id=req.id, relation=RelationType.TRACES_TO))

    # 3. Test derived from Design
    test = Test(
        id="TEST-2e9fa1-01",
        design_id="DESIGN-2e9fa1-01",
        name="test_jwt_token_refresh_expiry",
        test_code="def test_jwt_token_refresh_expiry(): assert auth.refresh_token(expired_token).status == 200",
        status=NodeStatus.PASSING
    )
    store.add_node(test)
    store.add_edge(Edge(source_id=test.id, target_id=design.id, relation=RelationType.TRACES_TO))

    # 4. Code Artifact 1: Auth Controller
    code1 = CodeArtifact(
        id="CODE-2e9fa1-01",
        design_id="DESIGN-2e9fa1-01",
        file_path="src/auth/controller.py",
        api_signature="def refresh_token(token: str) -> Tuple[int, str]: ...",
        status=NodeStatus.SYNCED
    )
    store.add_node(code1)
    store.add_edge(Edge(source_id=code1.id, target_id=design.id, relation=RelationType.IMPLEMENTS))

    # 5. Code Artifact 2: Token Service
    code2 = CodeArtifact(
        id="CODE-2e9fa1-02",
        design_id="DESIGN-2e9fa1-01",
        file_path="src/auth/token_service.py",
        api_signature="def store_refresh_token(user_id: str, token: str) -> None: ...",
        status=NodeStatus.SYNCED
    )
    store.add_node(code2)
    store.add_edge(Edge(source_id=code2.id, target_id=design.id, relation=RelationType.IMPLEMENTS))

    # 6. Risk Score derived from Requirement
    risk = RiskScore(
        id="RISK-2e9fa1-01",
        target_id="REQ-2e9fa1",
        target_type="Requirement",
        score=2.0,
        rationale="Baseline risk low: requirement fully covered by design, passing tests, and code implementation."
    )
    store.add_node(risk)
    store.add_edge(Edge(source_id=risk.id, target_id=req.id, relation=RelationType.DERIVED_FROM))

    # 7. Seeded Historical Incident
    incident = Incident(
        id="INCIDENT-8841",
        title="Unencrypted Refresh Token Storage in Cache",
        summary="A past security audit revealed refresh tokens stored in plaintext Redis cache allowed session hijacking.",
        linked_req_id="REQ-2e9fa1"
    )
    store.add_node(incident)

    # 8. Rule generated from Incident
    rule = Rule(
        id="RULE-SEC-01",
        incident_id=incident.id,
        pattern="token_storage_encryption",
        condition="All token storage in cache layers must enforce AES-256 encryption at rest.",
        status=NodeStatus.ACTIVE
    )
    store.add_node(rule)

    store.save()

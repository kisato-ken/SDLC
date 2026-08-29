from typing import Dict, Any, List
from ..core.models import RiskScore, NodeStatus, RelationType, Design, Test, Rule
from ..core.store import SDLCGraphStore

class RiskLens:
    def __init__(self, store: SDLCGraphStore):
        self.store = store

    def recalculate_risk(self, req_id: str) -> RiskScore:
        req_node = self.store.get_node(req_id)
        if not req_node:
            raise ValueError(f"Requirement {req_id} not found in store.")

        score = 2.0
        reasons = []

        design_edges = self.store.get_edges(relation=RelationType.TRACES_TO, target_id=req_id)
        for de in design_edges:
            d_node = self.store.get_node(de.source_id)
            if d_node and isinstance(d_node, Design):
                if d_node.status == NodeStatus.STALE:
                    score += 2.0
                    reasons.append(f"Linked Design '{d_node.id}' is STALE")

                test_edges = self.store.get_edges(relation=RelationType.TRACES_TO, target_id=d_node.id)
                for te in test_edges:
                    t_node = self.store.get_node(te.source_id)
                    if t_node and isinstance(t_node, Test):
                        if t_node.status == NodeStatus.STALE:
                            score += 2.0
                            reasons.append(f"Linked Test '{t_node.id}' is STALE")
                        elif t_node.status == NodeStatus.FAILING:
                            score += 3.0
                            reasons.append(f"Linked Test '{t_node.id}' is FAILING")

                flag_edges = self.store.get_edges(relation=RelationType.FLAGS, target_id=d_node.id)
                for fe in flag_edges:
                    rule_node = self.store.get_node(fe.source_id)
                    if rule_node and isinstance(rule_node, Rule):
                        score += 2.0
                        reasons.append(f"Flagged by Incident Rule '{rule_node.id}' ({rule_node.pattern})")

        score = min(10.0, max(0.0, score))
        rationale = "; ".join(reasons) if reasons else "All linked designs and tests are valid and passing."

        risk_node_id = f"RISK-{req_id.replace('REQ-', '')}-01"
        risk_node = self.store.get_node(risk_node_id)
        if risk_node and isinstance(risk_node, RiskScore):
            risk_node.score = score
            risk_node.rationale = rationale
        else:
            risk_node = RiskScore(
                id=risk_node_id,
                target_id=req_id,
                target_type="Requirement",
                score=score,
                rationale=rationale
            )
            self.store.add_node(risk_node)

        self.store.save()
        return risk_node

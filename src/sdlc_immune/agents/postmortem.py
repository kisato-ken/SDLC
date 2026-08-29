from typing import Dict, Any, List, Optional
from ..core.models import Incident, Rule, Edge, RelationType, NodeStatus, Design, Requirement
from ..core.store import SDLCGraphStore
from .risklens import RiskLens
from ..llm.provider import get_llm_provider, BaseLLMProvider

class PostmortemEngine:
    def __init__(self, store: SDLCGraphStore, llm_provider: Optional[BaseLLMProvider] = None):
        self.store = store
        self.risk_lens = RiskLens(store)
        self.llm = llm_provider or get_llm_provider()

    def ingest_incident(
        self,
        title: str,
        summary: str,
        linked_req_id: Optional[str] = None
    ) -> Dict[str, Any]:
        inc_id = f"INCIDENT-{len(self.store.nodes) + 100}"
        incident = Incident(
            id=inc_id,
            title=title,
            summary=summary,
            linked_req_id=linked_req_id
        )
        self.store.add_node(incident)

        system_prompt = (
            "You are an autonomous postmortem-to-prevention engine. "
            "Given an incident report, synthesize a machine-enforceable architectural rule condition."
        )
        user_prompt = (
            f"Incident Title: {title}\n"
            f"Incident Summary: {summary}\n"
            "Return JSON with keys: pattern (str), condition (str), severity (str)."
        )
        llm_rule = self.llm.generate_json(user_prompt, system_prompt)

        rule_pattern = llm_rule.get("pattern", "encryption_and_security_compliance")
        rule_condition = llm_rule.get(
            "condition",
            "All cached auth data and token storage must use AES-256 encryption at rest."
        )

        rule_id = f"RULE-{len(self.store.nodes) + 200}"
        rule = Rule(
            id=rule_id,
            incident_id=incident.id,
            pattern=rule_pattern,
            condition=rule_condition
        )
        self.store.add_node(rule)

        flagged_artifacts: List[str] = []
        affected_req_ids: set = set()

        for node in list(self.store.nodes.values()):
            if isinstance(node, Design):
                if "encrypt" not in node.content.lower() and "aes-256" not in node.content.lower():
                    node.status = NodeStatus.STALE
                    self.store.add_node(node)
                    flagged_artifacts.append(node.id)
                    affected_req_ids.add(node.req_id)

                    self.store.add_edge(Edge(
                        source_id=rule.id,
                        target_id=node.id,
                        relation=RelationType.FLAGS
                    ))

        self.store.save()

        updated_scores = {}
        for r_id in affected_req_ids:
            risk = self.risk_lens.recalculate_risk(r_id)
            updated_scores[r_id] = risk.score

        return {
            "incident_id": incident.id,
            "rule_id": rule.id,
            "rule_condition": rule.condition,
            "flagged_artifacts": flagged_artifacts,
            "affected_requirements": list(affected_req_ids),
            "updated_risk_scores": updated_scores,
            "llm_synthesis": llm_rule
        }

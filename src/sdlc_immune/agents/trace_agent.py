from typing import Dict, Any, List, Optional
from ..core.models import NodeStatus, RelationType
from ..core.store import SDLCGraphStore
from .risklens import RiskLens
from ..llm.provider import get_llm_provider, BaseLLMProvider

class TraceAgent:
    def __init__(self, store: SDLCGraphStore, llm_provider: Optional[BaseLLMProvider] = None):
        self.store = store
        self.risk_lens = RiskLens(store)
        self.llm = llm_provider or get_llm_provider()

    def check_drift(self, req_id: str, new_content: str) -> Dict[str, Any]:
        req_node = self.store.get_node(req_id)
        if not req_node:
            raise ValueError(f"Requirement {req_id} not found.")

        old_content = req_node.content
        req_node.content = new_content
        self.store.add_node(req_node)

        staled_artifacts: List[str] = []

        system_prompt = (
            "You are an autonomous SDLC architectural auditor. "
            "Detect whether the updated requirement introduces breaking architectural drift "
            "or requires downstream design/test modifications."
        )
        user_prompt = (
            f"Original Requirement: {old_content}\n"
            f"Updated Requirement: {new_content}\n"
            "Return JSON with keys: is_breaking (bool), reason (str), confidence (float)."
        )
        llm_decision = self.llm.generate_json(user_prompt, system_prompt)
        is_breaking_edit = llm_decision.get("is_breaking", False)

        design_edges = self.store.get_edges(relation=RelationType.TRACES_TO, target_id=req_id)
        for de in design_edges:
            d_node = self.store.get_node(de.source_id)
            if d_node:
                if is_breaking_edit:
                    d_node.status = NodeStatus.STALE
                    self.store.add_node(d_node)
                    staled_artifacts.append(d_node.id)

                    test_edges = self.store.get_edges(relation=RelationType.TRACES_TO, target_id=d_node.id)
                    for te in test_edges:
                        t_node = self.store.get_node(te.source_id)
                        if t_node:
                            t_node.status = NodeStatus.STALE
                            self.store.add_node(t_node)
                            staled_artifacts.append(t_node.id)

        self.store.save()
        updated_risk = self.risk_lens.recalculate_risk(req_id)

        return {
            "req_id": req_id,
            "staled_artifacts": staled_artifacts,
            "updated_risk_score": updated_risk.score,
            "rationale": updated_risk.rationale,
            "llm_analysis": llm_decision
        }

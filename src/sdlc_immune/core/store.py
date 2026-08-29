import json
import os
from typing import Dict, List, Optional, Any, Union
from collections import deque
from .models import (
    BaseNode, Requirement, Design, Test, CodeArtifact, RiskScore, Incident, Rule,
    ConfirmationLog, Edge, RelationType, NodeStatus
)

NODE_TYPE_MAP = {
    "Requirement": Requirement,
    "Design": Design,
    "Test": Test,
    "CodeArtifact": CodeArtifact,
    "RiskScore": RiskScore,
    "Incident": Incident,
    "Rule": Rule,
    "ConfirmationLog": ConfirmationLog
}

class SDLCGraphStore:
    def __init__(self, persistence_file: str = "data/store.json"):
        self.persistence_file = persistence_file
        self.nodes: Dict[str, BaseNode] = {}
        self.edges: List[Edge] = []
        if os.path.exists(self.persistence_file):
            self.load()

    def add_node(self, node: BaseNode) -> None:
        self.nodes[node.id] = node

    def get_node(self, node_id: str) -> Optional[BaseNode]:
        return self.nodes.get(node_id)

    def add_edge(self, edge: Edge) -> None:
        for e in self.edges:
            if e.source_id == edge.source_id and e.target_id == edge.target_id and e.relation == edge.relation:
                return
        self.edges.append(edge)

    def get_edges(self, source_id: Optional[str] = None, target_id: Optional[str] = None, relation: Optional[RelationType] = None) -> List[Edge]:
        results = []
        for e in self.edges:
            if source_id and e.source_id != source_id:
                continue
            if target_id and e.target_id != target_id:
                continue
            if relation and e.relation != relation:
                continue
            results.append(e)
        return results

    def get_graph_for_req(self, req_id: str) -> Dict[str, Any]:
        """Performs multi-hop reachability search starting from req_id."""
        visited_nodes = set()
        queue = deque([req_id])
        reachable_edges = []

        while queue:
            current_id = queue.popleft()
            if current_id in visited_nodes:
                continue
            visited_nodes.add(current_id)

            for e in self.edges:
                connected = None
                if e.target_id == current_id and e.source_id not in visited_nodes:
                    connected = e.source_id
                elif e.source_id == current_id and e.target_id not in visited_nodes:
                    connected = e.target_id

                if connected:
                    queue.append(connected)
                    if e not in reachable_edges:
                        reachable_edges.append(e)

        nodes_list = [self.nodes[nid].model_dump() for nid in visited_nodes if nid in self.nodes]
        edges_list = [e.model_dump() for e in reachable_edges]

        return {
            "req_id": req_id,
            "nodes": nodes_list,
            "edges": edges_list
        }

    def log_confirmation(
        self,
        target_node_id: str,
        action: str,
        user_override_status: Optional[str] = None,
        reason: Optional[str] = None
    ) -> ConfirmationLog:
        log_id = f"LOG-{len(self.nodes) + 1000}"
        log_entry = ConfirmationLog(
            id=log_id,
            target_node_id=target_node_id,
            action=action,
            user_override_status=user_override_status,
            reason=reason
        )
        self.add_node(log_entry)

        target_node = self.get_node(target_node_id)
        if target_node:
            if action == "override" and user_override_status:
                try:
                    target_node.status = NodeStatus(user_override_status.lower())
                except ValueError:
                    target_node.status = NodeStatus.VALID
                self.add_node(target_node)
            elif action == "confirm":
                target_node.status = NodeStatus.STALE
                self.add_node(target_node)

        self.save()
        return log_entry

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.persistence_file) or ".", exist_ok=True)
        data = {
            "nodes": [node.model_dump() for node in self.nodes.values()],
            "edges": [edge.model_dump() for edge in self.edges]
        }
        with open(self.persistence_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self) -> None:
        if not os.path.exists(self.persistence_file):
            return
        with open(self.persistence_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.nodes = {}
        for n in data.get("nodes", []):
            node_type = n.get("node_type")
            cls = NODE_TYPE_MAP.get(node_type, BaseNode)
            self.nodes[n["id"]] = cls(**n)

        self.edges = [Edge(**e) for e in data.get("edges", [])]

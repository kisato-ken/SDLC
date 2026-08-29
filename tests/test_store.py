import os
import sys

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sdlc_immune.core.store import SDLCGraphStore
from sdlc_immune.core.seed_data import seed_demo_data
from sdlc_immune.core.models import Requirement, Design, NodeStatus

def run_tests():
    os.makedirs("data", exist_ok=True)
    test_file = "data/test_store.json"
    if os.path.exists(test_file):
        os.remove(test_file)

    print("--- Running Test 1: Seed & Save Store ---")
    store = SDLCGraphStore(test_file)
    seed_demo_data(store)
    assert len(store.nodes) == 8, f"Expected 8 nodes, got {len(store.nodes)}"
    assert len(store.edges) == 5, f"Expected 5 edges, got {len(store.edges)}"
    print("Test 1 Passed: Correct node & edge counts.")

    print("--- Running Test 2: Multi-Hop Graph Traversal ---")
    graph_data = store.get_graph_for_req("REQ-2e9fa1")
    req_node = next((n for n in graph_data["nodes"] if n["id"] == "REQ-2e9fa1"), None)
    assert req_node is not None, "REQ-2e9fa1 not found in graph."
    assert req_node["node_type"] == "Requirement"

    design_node = next((n for n in graph_data["nodes"] if n["id"] == "DESIGN-2e9fa1-01"), None)
    assert design_node is not None, "DESIGN-2e9fa1-01 not found in multi-hop traversal."

    test_node = next((n for n in graph_data["nodes"] if n["id"] == "TEST-2e9fa1-01"), None)
    assert test_node is not None, "TEST-2e9fa1-01 not found in multi-hop traversal."

    code1_node = next((n for n in graph_data["nodes"] if n["id"] == "CODE-2e9fa1-01"), None)
    assert code1_node is not None, "CODE-2e9fa1-01 not found in multi-hop traversal."

    code2_node = next((n for n in graph_data["nodes"] if n["id"] == "CODE-2e9fa1-02"), None)
    assert code2_node is not None, "CODE-2e9fa1-02 not found in multi-hop traversal."

    risk_node = next((n for n in graph_data["nodes"] if n["id"] == "RISK-2e9fa1-01"), None)
    assert risk_node is not None, "RISK-2e9fa1-01 not found in multi-hop traversal."
    print("Test 2 Passed: Multi-hop reachability complete.")

    print("--- Running Test 3: Store Reload & Persistence ---")
    store2 = SDLCGraphStore(test_file)
    store2.load()
    assert len(store2.nodes) == 8, f"Expected 8 nodes on reload, got {len(store2.nodes)}"
    assert len(store2.edges) == 5, f"Expected 5 edges on reload, got {len(store2.edges)}"
    print("Test 3 Passed: JSON persistence accurately reloaded.")

    print("\nALL GRAPH STORE UNIT TESTS PASSED SUCCESSFULLY! [PASS]")

if __name__ == "__main__":
    run_tests()

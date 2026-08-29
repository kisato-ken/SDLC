import sys
import os

# Ensure src is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from sdlc_immune.core.store import SDLCGraphStore
from sdlc_immune.core.seed_data import seed_demo_data
from sdlc_immune.agents.trace_agent import TraceAgent
from sdlc_immune.agents.postmortem import PostmortemEngine

DEMO_STORE = "data/demo_store.json"

def run_demo():
    print("=" * 60)
    print("      SDLC IMMUNE SYSTEM -- POC COMPOUNDING DEMO")
    print("=" * 60)

    if os.path.exists(DEMO_STORE):
        os.remove(DEMO_STORE)

    store = SDLCGraphStore(DEMO_STORE)
    seed_demo_data(store)

    req_id = "REQ-2e9fa1"
    initial_graph = store.get_graph_for_req(req_id)
    initial_risk = next((n for n in initial_graph["nodes"] if n["node_type"] == "RiskScore"), None)

    print("\n--- INITIAL STATE ---")
    print(f"Requirement : {store.get_node(req_id).title}")
    print(f"Content     : {store.get_node(req_id).content}")
    print(f"Risk Score  : {initial_risk['score']} / 10.0 ({initial_risk['rationale']})")

    print("\n" + "=" * 60)
    print("BEAT 1: REQUIREMENT EDIT -> DRIFT -> RISK SCORE ESCALATION")
    print("=" * 60)
    print("Editing requirement: Shortening refresh window to 5 mins & requiring MFA...")
    
    trace_agent = TraceAgent(store)
    updated_req_text = (
        "System must validate OAuth2 tokens with MFA enforcement, "
        "refresh session tokens every 5 minutes, and audit all unauthorized access."
    )
    drift_result = trace_agent.check_drift(req_id, updated_req_text)

    print(f"[Trace Agent] Detected edit on {req_id}.")
    print(f"[Trace Agent] Staled linked artifacts: {drift_result['staled_artifacts']}")
    print(f"[RiskLens]    COMPOUNDING LINK #1 TRIGGERED -> Risk score updated: {drift_result['updated_risk_score']} / 10.0")
    print(f"[RiskLens]    Rationale: {drift_result['rationale']}")

    print("\n" + "=" * 60)
    print("BEAT 2: INCIDENT INGESTION -> RULE GEN -> RETROACTIVE DRIFT")
    print("=" * 60)
    print("Ingesting historical security incident report...")

    postmortem = PostmortemEngine(store)
    incident_result = postmortem.ingest_incident(
        title="Incident #8841: Plaintext Token Cache Exposure",
        summary="Audit revealed session tokens cached in plaintext Redis without AES-256 encryption.",
        linked_req_id=req_id
    )

    print(f"[Postmortem] Ingested Incident '{incident_result['incident_id']}'")
    print(f"[Postmortem] Generated Prevention Rule '{incident_result['rule_id']}'")
    print(f"[Postmortem] Rule Condition: {incident_result['rule_condition']}")
    print(f"[Postmortem] COMPOUNDING LINK #2 TRIGGERED -> Replayed rule against existing artifact graph.")
    print(f"[Postmortem] Flagged violating artifacts as STALE: {incident_result['flagged_artifacts']}")
    print(f"[RiskLens]    Updated Risk Scores: {incident_result['updated_risk_scores']}")

    print("\n" + "=" * 60)
    print(f"FINAL UNIFIED GRAPH STATE FOR {req_id}")
    print("=" * 60)
    final_graph = store.get_graph_for_req(req_id)
    for n in final_graph["nodes"]:
        status_str = f"Status: {n.get('status')}" if "status" in n else "Status: N/A"
        details = n.get("title") or n.get("name") or n.get("pattern") or n.get("rationale") or n.get("summary") or "None"
        print(f"- [{n['node_type']}] ID: {n['id']:<15} {status_str:<22} Details: {details}")

    print("\nDemo Completed Successfully!\n")

if __name__ == "__main__":
    run_demo()

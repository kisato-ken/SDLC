import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from ..core.store import SDLCGraphStore
from ..core.seed_data import seed_demo_data
from ..agents.trace_agent import TraceAgent
from ..agents.risklens import RiskLens
from ..agents.postmortem import PostmortemEngine
from ..agents.code_drift_checker import CodeArtifactDriftChecker
from ..evals.benchmark import run_evaluation

STORE_FILE = "data/app_store.json"

def get_store() -> SDLCGraphStore:
    os.makedirs("data", exist_ok=True)
    store = SDLCGraphStore(STORE_FILE)
    if not os.path.exists(STORE_FILE):
        seed_demo_data(store)
    else:
        store.load()
    return store

def get_html_content() -> str:
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "static", "design.html"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "design.html"),
        "design.html"
    ]
    for html_file in possible_paths:
        if os.path.exists(html_file):
            with open(html_file, "r", encoding="utf-8") as f:
                return f.read()
    return "<h1>Error: design.html not found</h1>"

class DashboardRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html", "/design.html"):
            content = get_html_content()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        elif parsed.path == "/api/graph":
            store = get_store()
            data = store.get_graph_for_req("REQ-2e9fa1")
            self.send_json_response(data)
        elif parsed.path == "/api/eval_report":
            report = run_evaluation()
            self.send_json_response(report)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        store = get_store()
        content_length = int(self.headers.get('Content-Length', 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b'{}'
        body = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}

        if parsed.path == "/api/beat1":
            trace_agent = TraceAgent(store)
            new_content = "System MUST validate OAuth2 tokens with MFA enforcement, refresh session tokens every 5 minutes, and audit all unauthorized access."
            res = trace_agent.check_drift("REQ-2e9fa1", new_content)
            self.send_json_response(res)

        elif parsed.path == "/api/beat2":
            postmortem = PostmortemEngine(store)
            res = postmortem.ingest_incident(
                title="Incident #8841: Plaintext Token Cache Exposure",
                summary="Audit revealed session tokens cached in plaintext Redis without AES-256 encryption.",
                linked_req_id="REQ-2e9fa1"
            )
            self.send_json_response(res)

        elif parsed.path == "/api/code_drift":
            checker = CodeArtifactDriftChecker(store)
            code_id = body.get("code_id", "CODE-2e9fa1-01")
            res = checker.check_artifact_drift(code_id)
            self.send_json_response(res)

        elif parsed.path == "/api/confirm":
            node_id = body.get("node_id")
            log_obj = store.log_confirmation(node_id, action="confirm")
            self.send_json_response({"status": "logged", "log_id": log_obj.id})

        elif parsed.path == "/api/override":
            node_id = body.get("node_id")
            override_status = body.get("override_status", "valid")
            reason = body.get("reason", "")
            log_obj = store.log_confirmation(node_id, action="override", user_override_status=override_status, reason=reason)
            self.send_json_response({"status": "logged", "log_id": log_obj.id})

        elif parsed.path == "/api/reset":
            if os.path.exists(STORE_FILE):
                os.remove(STORE_FILE)
            fresh_store = get_store()
            self.send_json_response({"status": "reset", "node_count": len(fresh_store.nodes)})
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def send_json_response(self, data: dict):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

def run_server(port: int = 8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, DashboardRequestHandler)
    print(f"SDLC Immune System Dashboard running at http://localhost:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()

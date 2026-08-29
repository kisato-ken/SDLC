from typing import Dict, Any, List
from ..core.models import Requirement, Design, NodeStatus, Edge, RelationType
from ..core.store import SDLCGraphStore
from ..agents.trace_agent import TraceAgent

EVAL_BENCHMARK_SCENARIOS = [
    {
        "id": 1,
        "req_title": "OAuth Token Expiry Reduction",
        "category": "Authentication",
        "req_content": "Reduce access token expiry from 15m to 5m and require MFA challenge on refresh.",
        "design_content": "Token refresh every 15m using HS256 without MFA challenge.",
        "expected_drift": True,
        "reason": "Token lifetime shortened and new MFA security challenge added."
    },
    {
        "id": 2,
        "req_title": "Docstring Formatting Fix",
        "category": "Documentation",
        "req_content": "System must validate OAuth2 tokens, refresh expired session tokens every 15 minutes, and log access attempts.",
        "design_content": "Implement AuthController with validate_token() and refresh_token() endpoints using JWT HS256 algorithm.",
        "expected_drift": False,
        "reason": "Stylistic and wording refinement without behavioral change."
    },
    {
        "id": 3,
        "req_title": "AES-256-GCM Token Encryption",
        "category": "Cryptography",
        "req_content": "All cached refresh tokens must be encrypted with AES-256-GCM at rest before writing to Redis.",
        "design_content": "Tokens stored in plain Redis cache without encryption.",
        "expected_drift": True,
        "reason": "Introduces cryptographic encryption requirement at rest."
    },
    {
        "id": 4,
        "req_title": "Audit Log Metadata Clarification",
        "category": "Auditing",
        "req_content": "Log unauthorized access attempts including source client IP address.",
        "design_content": "Log unauthorized access attempts with client IP metadata in security log.",
        "expected_drift": False,
        "reason": "Design already implements client IP capture."
    },
    {
        "id": 5,
        "req_title": "Asymmetric Signing Migration (RS256)",
        "category": "Cryptography",
        "req_content": "Deprecate symmetric HS256 shared secrets and enforce asymmetric RS256 signing keys.",
        "design_content": "Implement AuthController using JWT HS256 symmetric secret.",
        "expected_drift": True,
        "reason": "Changes signing algorithm from symmetric to asymmetric."
    },
    {
        "id": 6,
        "req_title": "Password Entropy & Complexity",
        "category": "Authentication",
        "req_content": "Require 16 character minimum password length and zxcvbn score >= 3.",
        "design_content": "Validate password minimum length 8 characters with regex.",
        "expected_drift": True,
        "reason": "Password length and entropy thresholds increased."
    },
    {
        "id": 7,
        "req_title": "Controller Method Naming Alignment",
        "category": "Architecture",
        "req_content": "System must validate OAuth2 tokens and log unauthorized access accurately.",
        "design_content": "Implement validate_token() controller and log unauthorized attempts.",
        "expected_drift": False,
        "reason": "Non-breaking phrasing clarification."
    },
    {
        "id": 8,
        "req_title": "IP Rate Limiting Enforced",
        "category": "Traffic Control",
        "req_content": "Throttle auth requests to 10 per minute per IP using token bucket algorithm.",
        "design_content": "No rate limiting implemented in AuthController.",
        "expected_drift": True,
        "reason": "Introduces new traffic throttling constraint."
    },
    {
        "id": 9,
        "req_title": "JWT Claim Payload Extension",
        "category": "Authorization",
        "req_content": "Switch token payload to include tenant_id and org_role claims.",
        "design_content": "Token payload only contains sub, exp, and iat claims.",
        "expected_drift": True,
        "reason": "Requires new mandatory claims in JWT payload."
    },
    {
        "id": 10,
        "req_title": "Typo Correction in Comments",
        "category": "Documentation",
        "req_content": "System must validate OAuth2 tokens efficiently.",
        "design_content": "Implement AuthController with validate_token() endpoint.",
        "expected_drift": False,
        "reason": "Grammatical fix with zero API surface impact."
    },
    {
        "id": 11,
        "req_title": "Immediate Session Revocation",
        "category": "Session Management",
        "req_content": "Support immediate global session revocation by user_id via Redis deny-list.",
        "design_content": "Tokens are stateless JWTs without revocation list.",
        "expected_drift": True,
        "reason": "Stateless design cannot support instant revocation without state layer."
    },
    {
        "id": 12,
        "req_title": "Telemetry Spacing Adjustment",
        "category": "Observability",
        "req_content": "System must validate tokens efficiently and log metrics.",
        "design_content": "Implement token validation endpoint and emit prometheus metrics.",
        "expected_drift": False,
        "reason": "Design already covers metric emission."
    },
    {
        "id": 13,
        "req_title": "Cookie Security Flags (SameSite=Strict)",
        "category": "Web Security",
        "req_content": "Enforce SameSite=Strict, HttpOnly, and Secure flags on session cookies.",
        "design_content": "Session cookie set with default browser attributes.",
        "expected_drift": True,
        "reason": "Mandatory cookie security flags required."
    },
    {
        "id": 14,
        "req_title": "Audit Log Retention Guarantee",
        "category": "Compliance",
        "req_content": "Retain auth audit logs for 90 days in cold storage.",
        "design_content": "Audit log table stores logs for 90 days with partition pruning.",
        "expected_drift": False,
        "reason": "Design retention period matches requirement."
    },
    {
        "id": 15,
        "req_title": "Multi-Tenant Cache Isolation",
        "category": "Tenancy",
        "req_content": "Strictly segregate auth cache across tenant DBs with isolated namespace prefixes.",
        "design_content": "Shared global Redis instance for all auth caching without tenant prefix.",
        "expected_drift": True,
        "reason": "Shared Redis cache violates multi-tenant isolation."
    },
    {
        "id": 16,
        "req_title": "Webhook Signature Verification",
        "category": "Integration",
        "req_content": "All incoming webhooks must verify HMAC-SHA256 signatures with 5m replay prevention window.",
        "design_content": "Webhook endpoints accept raw JSON payloads without signature check.",
        "expected_drift": True,
        "reason": "Adds cryptographic webhook validation requirement."
    },
    {
        "id": 17,
        "req_title": "Logging Library Upgrade",
        "category": "Dependencies",
        "req_content": "System must log authentication events using structured JSON logger.",
        "design_content": "AuthController uses structlog to emit structured JSON logs.",
        "expected_drift": False,
        "reason": "Design already uses structured JSON logging."
    },
    {
        "id": 18,
        "req_title": "Passkey & FIDO2 WebAuthn Support",
        "category": "Authentication",
        "req_content": "Support passwordless passkey login using FIDO2 WebAuthn standard.",
        "design_content": "Authentication strictly supports username and password credentials.",
        "expected_drift": True,
        "reason": "New authentication protocol required."
    },
    {
        "id": 19,
        "req_title": "Database Read Replica Querying",
        "category": "Performance",
        "req_content": "Auth token validation reads must target read replica DB instances.",
        "design_content": "Token lookups query read-replica database pool with primary fallback.",
        "expected_drift": False,
        "reason": "Design already routes reads to replica pool."
    },
    {
        "id": 20,
        "req_title": "Idempotency Key Enforcement",
        "category": "API Resiliency",
        "req_content": "All payment and critical auth state changes must enforce Idempotency-Key header.",
        "design_content": "Endpoints process requests immediately without idempotency deduplication.",
        "expected_drift": True,
        "reason": "Requires idempotency header validation and deduplication storage."
    },
    {
        "id": 21,
        "req_title": "GraphQL Query Depth Limiting",
        "category": "Security",
        "req_content": "Enforce maximum GraphQL query depth of 5 and max complexity score of 200.",
        "design_content": "GraphQL schema executes nested queries without depth or cost analyzer.",
        "expected_drift": True,
        "reason": "Adds query complexity and depth limits to prevent DoS."
    },
    {
        "id": 22,
        "req_title": "Response Timestamp ISO-8601",
        "category": "Standards",
        "req_content": "All API responses must format timestamps in ISO-8601 UTC format.",
        "design_content": "Serializers output datetime objects as ISO-8601 UTC strings.",
        "expected_drift": False,
        "reason": "Design serializers already conform to ISO-8601 standard."
    },
    {
        "id": 23,
        "req_title": "PII Data Masking in Logs",
        "category": "Privacy",
        "req_content": "Mask all email addresses, passwords, and phone numbers in application log outputs.",
        "design_content": "Log formatters output full request payload including unmasked email and params.",
        "expected_drift": True,
        "reason": "PII redaction and masking filters required in logging pipeline."
    },
    {
        "id": 24,
        "req_title": "CORS Allowed Origins Restriction",
        "category": "Web Security",
        "req_content": "Restrict CORS Access-Control-Allow-Origin to explicit trusted domain whitelist.",
        "design_content": "CORS middleware configured with Access-Control-Allow-Origin: * wildcard.",
        "expected_drift": True,
        "reason": "Wildcard CORS policy violates domain whitelist requirement."
    },
    {
        "id": 25,
        "req_title": "Health Check Endpoint Response",
        "category": "DevOps",
        "req_content": "Health check endpoint /healthz must return HTTP 200 and DB connectivity status.",
        "design_content": "Implement /healthz handler returning 200 OK and pinging primary DB connection.",
        "expected_drift": False,
        "reason": "Design already implements full database connectivity check on /healthz."
    }
]

def run_evaluation() -> Dict[str, Any]:
    tp, fp, tn, fn = 0, 0, 0, 0
    results = []

    for item in EVAL_BENCHMARK_SCENARIOS:
        store = SDLCGraphStore(persistence_file="data/store.json")
        store.nodes = {}
        store.edges = []
        baseline_content = "System must validate OAuth2 tokens, refresh expired session tokens every 15 minutes, and log access attempts."
        req = Requirement(id=f"EVAL-REQ-{item['id']}", title=item["req_title"], content=baseline_content)
        design = Design(id=f"EVAL-DES-{item['id']}", req_id=req.id, content=item["design_content"])
        store.add_node(req)
        store.add_node(design)
        store.add_edge(Edge(source_id=design.id, target_id=req.id, relation=RelationType.TRACES_TO))

        agent = TraceAgent(store)
        res = agent.check_drift(req.id, item["req_content"])
        predicted_drift = len(res["staled_artifacts"]) > 0
        actual_drift = item["expected_drift"]

        if predicted_drift and actual_drift:
            tp += 1
        elif predicted_drift and not actual_drift:
            fp += 1
        elif not predicted_drift and not actual_drift:
            tn += 1
        else:
            fn += 1

        results.append({
            "scenario_id": item["id"],
            "title": item["req_title"],
            "category": item["category"],
            "expected_drift": actual_drift,
            "predicted_drift": predicted_drift,
            "reason": item["reason"],
            "correct": predicted_drift == actual_drift
        })

    total = len(EVAL_BENCHMARK_SCENARIOS)
    correct_count = tp + tn
    agreement_rate = round((correct_count / total) * 100, 1)
    precision = round((tp / (tp + fp)) * 100, 1) if (tp + fp) > 0 else 100.0
    recall = round((tp / (tp + fn)) * 100, 1) if (tp + fn) > 0 else 100.0

    return {
        "total_scenarios": total,
        "agreement_rate": agreement_rate,
        "precision": precision,
        "recall": recall,
        "confusion_matrix": {"TP": tp, "FP": fp, "TN": tn, "FN": fn},
        "results": results
    }

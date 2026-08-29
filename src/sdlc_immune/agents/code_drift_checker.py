import ast
from typing import Dict, Any, List, Optional
from ..core.models import CodeArtifact, Design, NodeStatus
from ..core.store import SDLCGraphStore
from .risklens import RiskLens

CODE_CATALOG = {
    "CODE-2e9fa1-01": {
        "file_path": "src/auth/controller.py",
        "description": "Auth REST Controller handling login, token validation, and refresh workflows",
        "source_code": '''class AuthController:
    def __init__(self, token_service: TokenService):
        self.token_service = token_service

    def validate_token(self, token: str) -> bool:
        """Validates incoming OAuth2 Bearer token."""
        return self.token_service.verify(token)

    def refresh_token(self, token: str) -> Tuple[int, str]:
        """Refreshes expired session token. Notice: missing mfa_challenge parameter!"""
        new_token = self.token_service.rotate(token)
        return (200, new_token)
''',
        "api_signature": "def refresh_token(token: str) -> Tuple[int, str]: ...",
        "design_id": "DESIGN-2e9fa1-01",
        "expected_params": ["token", "mfa_code"],
        "expected_ciphers": ["HS256", "RS256"]
    },
    "CODE-2e9fa1-02": {
        "file_path": "src/auth/token_service.py",
        "description": "Token persistence and caching layer using Redis",
        "source_code": '''class TokenStorageService:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def store_refresh_token(self, user_id: str, token: str) -> None:
        """Stores token in Redis. Notice: plaintext write without AES-256 encryption!"""
        self.redis.set(f"token:{user_id}", token, ex=900)
''',
        "api_signature": "def store_refresh_token(user_id: str, token: str) -> None: ...",
        "design_id": "DESIGN-2e9fa1-01",
        "expected_params": ["user_id", "token", "encryption_key"],
        "expected_ciphers": ["AES-256", "AESGCM"]
    },
    "CODE-2e9fa1-03": {
        "file_path": "src/middleware/rate_limiter.py",
        "description": "FastAPI HTTP middleware enforcing IP token bucket rate limits",
        "source_code": '''class RateLimiterMiddleware:
    def __init__(self, max_requests: int = 10, window_secs: int = 60):
        self.max_requests = max_requests
        self.window_secs = window_secs

    async def __call__(self, request: Request, call_next):
        client_ip = request.client.host
        if not check_rate_limit(client_ip, self.max_requests, self.window_secs):
            return JSONResponse(status_code=429, content={"error": "Rate limit exceeded"})
        return await call_next(request)
''',
        "api_signature": "class RateLimiterMiddleware(max_requests: int = 10, window_secs: int = 60): ...",
        "design_id": "DESIGN-2e9fa1-01",
        "expected_params": ["max_requests", "window_secs"],
        "expected_ciphers": []
    }
}

class CodeArtifactDriftChecker:
    def __init__(self, store: SDLCGraphStore):
        self.store = store
        self.risk_lens = RiskLens(store)

    def check_artifact_drift(self, code_id: str = "CODE-2e9fa1-01") -> Dict[str, Any]:
        code_info = CODE_CATALOG.get(code_id)
        if not code_info:
            code_node = self.store.get_node(code_id)
            if not isinstance(code_node, CodeArtifact):
                raise ValueError(f"CodeArtifact {code_id} not found.")
            design_id = code_node.design_id
            api_sig = code_node.api_signature
            file_path = code_node.file_path
            source = code_node.api_signature
            expected_params = ["token", "mfa_code"]
            expected_ciphers = ["AES-256"]
        else:
            design_id = code_info["design_id"]
            api_sig = code_info["api_signature"]
            file_path = code_info["file_path"]
            source = code_info["source_code"]
            expected_params = code_info["expected_params"]
            expected_ciphers = code_info["expected_ciphers"]

        design_node = self.store.get_node(design_id)
        if not isinstance(design_node, Design):
            raise ValueError(f"Linked Design {design_id} not found.")

        divergence_reasons = []
        ast_mismatches = []

        for param in expected_params:
            if param.lower() not in source.lower():
                reason = f"Parameter mismatch: Design specification expects '{param}' argument, but {file_path} lacks parameter '{param}'."
                divergence_reasons.append(reason)
                ast_mismatches.append({"type": "missing_parameter", "name": param, "severity": "HIGH"})

        for cipher in expected_ciphers:
            if cipher.lower().replace("-", "") not in source.lower().replace("-", ""):
                reason = f"Cryptographic divergence: Design expects '{cipher}' cipher implementation, but {file_path} implements unencrypted/default storage."
                divergence_reasons.append(reason)
                ast_mismatches.append({"type": "missing_cipher", "name": cipher, "severity": "CRITICAL"})

        is_drifted = len(divergence_reasons) > 0

        code_node = self.store.get_node(code_id)
        if code_node:
            code_node.status = NodeStatus.STALE if is_drifted else NodeStatus.SYNCED
            self.store.add_node(code_node)

        if is_drifted:
            design_node.status = NodeStatus.STALE
            self.store.add_node(design_node)
            self.store.save()
            updated_risk = self.risk_lens.recalculate_risk(design_node.req_id)
            score = updated_risk.score
            rationale = updated_risk.rationale
        else:
            score = self.risk_lens.recalculate_risk(design_node.req_id).score
            rationale = "Code API surface matches architectural specification."

        return {
            "code_id": code_id,
            "file_path": file_path,
            "design_id": design_node.id,
            "req_id": design_node.req_id,
            "is_drifted": is_drifted,
            "ast_mismatches": ast_mismatches,
            "divergence_reasons": divergence_reasons,
            "source_code": source,
            "api_signature": api_sig,
            "updated_risk_score": score,
            "rationale": rationale,
            "catalog": {k: {"file": v["file_path"], "desc": v["description"]} for k, v in CODE_CATALOG.items()}
        }

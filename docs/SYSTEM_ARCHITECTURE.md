# SDLC Immune System: Technical Architecture and System Specification

## 1. Executive Summary

Modern software development lifecycles frequently suffer from fragmented quality governance. Requirements evolve rapidly in project tracking systems, architectural design documents quickly become obsolete, codebases diverge silently from expected interfaces, and incident postmortems remain trapped in static documents without active enforcement.

The SDLC Immune System addresses these structural vulnerabilities by unifying requirements, architectural designs, unit and integration tests, code implementations, risk evaluations, and historical incident rules into a single, multi-hop directed graph store.

Rather than operating as isolated point solutions, system modules form compounding feedback loops:
1. Requirement drift automatically identifies stale downstream artifacts and escalates forward failure risk.
2. Incident postmortems synthesize machine-enforceable architectural rules that retroactively audit existing components across the graph.
3. Code-level Abstract Syntax Tree (AST) analyzers detect silent parameter and cryptographic divergences without requiring upstream requirement edits.

---

## 2. Theoretical Foundations and Graph Data Model

### 2.1 The Single Source of Truth Graph
At the core of the system is `SDLCGraphStore`, an in-memory and disk-persisted graph engine capable of multi-hop Breadth-First Search (BFS) traversals. The graph establishes explicit relationships between heterogeneous SDLC entities.

### 2.2 Node Taxonomy (`src/sdlc_immune/core/models.py`)

* **Requirement (`Requirement`)**: Root specification defining functional and non-functional requirements. Identified by `REQ-{id}`.
* **Design (`Design`)**: Architectural specifications and API contracts derived from requirements. Identified by `DESIGN-{id}`.
* **Test (`Test`)**: Verification suites and integration test cases covering designs. Identified by `TEST-{id}`.
* **Code Artifact (`CodeArtifact`)**: Concrete source code files, class interfaces, and runtime function signatures. Identified by `CODE-{id}`.
* **Risk Score (`RiskScore`)**: Dynamic quantitative metric (0.0 to 10.0) reflecting forward failure probability. Identified by `RISK-{id}`.
* **Incident (`Incident`)**: Postmortem record of production incidents, security failures, or outages. Identified by `INCIDENT-{id}`.
* **Rule (`Rule`)**: Machine-enforceable invariant synthesized from postmortems to prevent repeat failures. Identified by `RULE-{id}`.
* **Confirmation Log (`ConfirmationLog`)**: Human-in-the-Loop (HITL) audit record capturing manual developer confirmation or override decisions.

### 2.3 Edge Taxonomy (`RelationType`)

Edges represent directed architectural dependencies:
* `TRACES_TO`: Connects `Design` to `Requirement`, and `Test` to `Design`.
* `IMPLEMENTS`: Connects `CodeArtifact` to `Design`.
* `DERIVED_FROM`: Connects `RiskScore` to `Requirement` or `Design`.
* `FLAGS`: Connects `Rule` to `Design`, representing a detected policy violation.

---

## 3. Compounding Governance Mechanisms

### 3.1 Compounding Link 1: Requirement Drift to Risk Escalation
When a product requirement changes (for example, shortening session token lifetimes or adding mandatory multi-factor authentication), the `TraceAgent` module:
1. Updates the requirement specification in the store.
2. Emits an evaluation payload to the LLM provider layer to determine if the modification represents a breaking architectural change.
3. Identifies all downstream `Design` and `Test` nodes connected via `TRACES_TO` edges.
4. Marks affected nodes with `NodeStatus.STALE`.
5. Invokes `RiskLens` to recalculate forward risk. The score automatically escalates (for example, from a baseline 2.0 to 6.0 out of 10.0), alerting engineering leadership before implementation begins.

### 3.2 Compounding Link 2: Postmortem to Retroactive Rule Governance
When a production failure occurs (for example, session tokens exposed in an unencrypted cache), the `PostmortemEngine`:
1. Ingests the incident title and root cause analysis summary.
2. Synthesizes a structured prevention rule containing a searchable pattern and an invariant condition (such as enforcing AES-256 encryption at rest).
3. Replays the synthesized rule across all existing designs in the graph.
4. Adds a directed `FLAGS` edge from the new rule to any design lacking the required safeguard, immediately marking the design as `STALE`.
5. Re-evaluates risk across all parent requirements, compounding the risk score from 6.0 to 8.0 or higher.

### 3.3 Step 10: Multi-File Code API Surface Diffing
Software engineers often modify code signatures without updating design documentation or requirements. The `CodeArtifactDriftChecker` analyzes live source files and extracts AST signatures to compare against design expectations:
* Parameter alignment (identifies missing parameters, type mismatches, or altered defaults).
* Cryptographic invariants (verifies that sensitive storage routines invoke appropriate ciphers rather than plaintext operations).
* Throttling and rate-limiting middleware compliance.

---

## 4. Pluggable AI and Large Language Model Architecture

To support both enterprise air-gapped environments and cloud-native deployments, the system decouples language model reasoning via `src/sdlc_immune/llm/provider.py`.

```
                    ┌────────────────────────────────────────┐
                    │          BaseLLMProvider (ABC)         │
                    └───────────────────┬────────────────────┘
                                        │
         ┌──────────────────┬───────────┴───────────┬──────────────────┐
         │                  │                       │                  │
┌────────┴────────┐ ┌───────┴────────┐    ┌─────────┴─────────┐ ┌──────┴─────────┐
│ OpenAIProvider  │ │ OllamaProvider │    │ CustomEndpoint    │ │ Heuristic       │
│ (GPT-4o, o1)    │ │ (Llama, Qwen)  │    │ (vLLM, TGI)       │ │ Fallback        │
└─────────────────┘ └────────────────┘    └───────────────────┘ └─────────────────┘
```

### 4.1 Supported Provider Backends
1. **API-Based Providers (`OpenAIProvider`)**: Integrates with OpenAI, Azure, and Anthropic endpoints using structured JSON outputs.
2. **Local Self-Hosted Providers (`OllamaProvider`)**: Connects to local instances of Llama 3, Mistral, DeepSeek-R1, and Qwen models without data leaving the private network.
3. **Custom Inference Gateways (`CustomEndpointProvider`)**: Supports private vLLM, HuggingFace TGI, or internal corporate proxies.
4. **Deterministic Heuristic Provider (`HeuristicFallbackProvider`)**: Serves as a zero-dependency fallback, enabling instantaneous execution, 100% offline unit testing, and continuous integration without API keys.

### 4.2 Configuration
The active provider is determined dynamically through standard environment variables:
* `LLM_PROVIDER`: `heuristic` (default), `openai`, `ollama`, or `custom`.
* `OPENAI_API_KEY`: API authentication token for cloud models.
* `OLLAMA_BASE_URL`: Base address of the local daemon (defaults to `http://localhost:11434`).
* `CUSTOM_LLM_URL`: URL for custom vLLM or internal inference proxies.

---

## 5. Evaluation and Verification Methodology

The system is validated against a hand-labeled benchmark suite (`src/sdlc_immune/evals/benchmark.py`) comprising 25 complex scenarios across 10 software engineering domains:

| Category | Evaluated Domains | Sample Scenarios |
|---|---|---|
| **Authentication** | Lifetimes, MFA, Password Complexity, Passkeys | OAuth expiry reduction (15m to 5m), FIDO2 WebAuthn support |
| **Cryptography** | Ciphers, Signing Algorithms | AES-256-GCM token storage, RS256 asymmetric migration |
| **Web Security** | Cookie Flags, CORS Whitelisting | SameSite=Strict / HttpOnly cookies, CORS origin validation |
| **Traffic Control** | Rate Limiting, Throttling | Token bucket IP throttling (10 requests per minute) |
| **Session Management**| State Invalidation | Immediate Redis-backed global session revocation |
| **Tenancy** | Multi-Tenant Data Isolation | Namespace prefixing across shared caching clusters |
| **Integration** | Webhooks, Replay Protection | HMAC-SHA256 signature verification with 5-minute window |
| **Compliance & Privacy**| Redaction, Retention | PII data masking (emails, credentials) and 90-day cold storage |
| **API Resiliency** | Idempotency, GraphQL Safety | Idempotency-Key headers and GraphQL query depth caps |
| **Documentation** | Non-breaking Refactoring | Comment formatting, whitespace adjustments, and docstring updates |

### Benchmark Results
* **Total Scenarios Evaluated**: 25
* **Agreement Rate**: 96.0% (24 / 25 scenarios correctly categorized)
* **Precision**: 100.0% (Zero false positives recorded)
* **Recall**: 93.3% (14 of 15 true drift scenarios detected)
* **Confusion Matrix**: `True Positives: 14, False Positives: 0, True Negatives: 10, False Negatives: 1`

---

## 6. Directory Layout and Package Architecture

```text
d:\SDLC/
├── src/                           # Core package source code
│   └── sdlc_immune/
│       ├── __init__.py            # Package root (__version__ = "1.0.0")
│       │
│       ├── core/                  # Graph store & data schema backbone
│       │   ├── __init__.py
│       │   ├── models.py          # BaseNode, Requirement, Design, Test, Code, Risk, Rule
│       │   ├── store.py           # SDLCGraphStore with multi-hop BFS & JSON persistence
│       │   └── seed_data.py       # Seed generator populating verified graph baseline
│       │
│       ├── agents/                # Autonomous governance agent modules
│       │   ├── __init__.py
│       │   ├── trace_agent.py     # Trace Agent (Link 1: Drift -> Risk escalation)
│       │   ├── risklens.py        # RiskLens quantitative scoring engine (0.0 to 10.0)
│       │   ├── postmortem.py      # Postmortem Engine (Link 2: Rule -> Retroactive Drift)
│       │   └── code_drift_checker.py # Multi-file AST & cryptographic cipher analyzer (Step 10)
│       │
│       ├── llm/                   # Pluggable AI and LLM abstraction layer
│       │   ├── __init__.py
│       │   └── provider.py        # BaseLLMProvider, OpenAI, Ollama, Custom & Heuristic
│       │
│       ├── web/                   # Web server and dashboard assets
│       │   ├── __init__.py
│       │   ├── app.py             # HTTP server backend exposing REST endpoints
│       │   └── static/
│       │       └── design.html    # Clinical Web Dashboard UI
│       │
│       └── evals/                 # Benchmark evaluation framework
│           ├── __init__.py
│           └── benchmark.py       # 25-scenario evaluation dataset and runner (Step 9)
│
├── tests/                         # Automated unit test suite
│   ├── __init__.py
│   └── test_store.py              # Tests verifying graph persistence, BFS & reloads
│
├── data/                          # Runtime persistent storage
│   ├── store.json                 # Core graph store state
│   └── app_store.json             # Web application runtime state
│
├── docs/                          # In-depth technical documentation
│   ├── SYSTEM_ARCHITECTURE.md     # Formal technical architecture and system specification
│   └── sdlc-immune-system-poc-spec.md # Original proof-of-concept functional specification
│
├── app.py                         # Top-level entrypoint launcher for web dashboard
├── demo.py                        # Top-level entrypoint launcher for terminal CLI demo
├── eval_set.py                    # Top-level entrypoint launcher for 25-eval benchmark
├── requirements.txt               # Dependencies (pydantic >= 2.0.0)
└── README.md                      # Quickstart guide and repository overview
```

---

## 7. Operational Instructions

### 7.1 Environment Setup
Install the required dependencies using pip:
```bash
pip install -r requirements.txt
```

### 7.2 Executing Unit Tests
Verify graph traversals, node additions, edge linking, and persistence reloads:
```bash
python tests/test_store.py
```

### 7.3 Running the Evaluation Benchmark
Execute the 25-scenario ground truth benchmark:
```bash
python eval_set.py
```

### 7.4 Running the Terminal CLI Demo
Run an end-to-end demonstration of Beats 1 and 2 in the terminal:
```bash
python demo.py
```

### 7.5 Starting the Interactive Web Dashboard
Launch the HTTP server:
```bash
python app.py
```
Navigate to `http://localhost:8000` in any modern web browser to interact with the topology graph, trigger drift and postmortem beats, inspect code diffs, and review evaluation reports.

---

## 8. REST API Specification

### `GET /`
Returns the main single-page application dashboard (`design.html`).

### `GET /api/graph`
Returns the multi-hop graph associated with the primary requirement `REQ-2e9fa1`.
* **Response Format**: `application/json` containing `nodes` and `edges` arrays.

### `POST /api/beat1`
Triggers requirement drift on `REQ-2e9fa1` (shortening token expiry and enforcing MFA), flagging linked designs and tests as `STALE` and escalating risk.

### `POST /api/beat2`
Ingests incident `#8841`, synthesizes `RULE-SEC-01`, replays the rule across existing designs, and creates retroactive policy violation edges.

### `POST /api/code_drift`
Analyzes active code files (`src/auth/controller.py`, `src/auth/token_service.py`, or `src/middleware/rate_limiter.py`) against design expectations.
* **Payload**: `{"code_id": "CODE-2e9fa1-01"}`

### `POST /api/confirm`
Records a Human-in-the-Loop confirmation affirming a detected stale status.
* **Payload**: `{"node_id": "DESIGN-2e9fa1-01"}`

### `POST /api/override`
Overrides a flagged artifact back to valid status with developer justification.
* **Payload**: `{"node_id": "DESIGN-2e9fa1-01", "override_status": "valid", "reason": "Verified compatible"}`

### `GET /api/eval_report`
Executes the 25-scenario evaluation suite and returns agreement rate, precision, recall, confusion matrix, and per-scenario outputs.

### `POST /api/reset`
Clears local persistence stores and re-seeds the graph to the baseline state.

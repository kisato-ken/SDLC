# SDLC Immune System: Autonomous Multi-Agent Quality and Risk Governance

The **SDLC Immune System** is an autonomous multi-agent governance platform that continuously audits software requirements, architectural designs, tests, code implementations, and historical incidents on a **single unified multi-hop graph store**.

Rather than operating in isolation, modules compound:
1. **Compounding Link 1 (Drift to Risk)**: Requirement edits flag downstream designs as `STALE`, instantly escalating RiskLens failure scores.
2. **Compounding Link 2 (Rule to Retroactive Drift)**: Production postmortems synthesize architectural rules that re-evaluate the entire existing graph, retroactively staling violating designs.
3. **Step 10 (Code Surface Diff)**: Live AST and signature diffing catches silent code divergence without requirement edits.
4. **Step 9 (Evaluation Benchmark)**: 25 hand-labeled ground truth scenarios verified with a **96.0% Agreement Rate** (100% Precision, 93.3% Recall).
5. **Pluggable AI/LLM Layer**: Unified support for API-based models (OpenAI, Gemini, Claude), Local Self-Hosted LLMs (Ollama, vLLM), and Heuristic Fallback.

---

## Project Directory Structure

```text
d:\SDLC\
│
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

## AI and LLM Integration Architecture

The system features a decoupled provider layer in `src/sdlc_immune/llm/provider.py` with automatic fallback.

### 1. Default (Offline & Fast)
Runs deterministically with zero configuration or API keys:
```bash
python app.py
```

### 2. API-Based LLMs (OpenAI, Gemini, Azure)
```bash
export LLM_PROVIDER="openai"
export OPENAI_API_KEY="sk-..."
python app.py
```

### 3. Local / Self-Hosted LLMs (Ollama)
Point to your local Llama 3, Mistral, DeepSeek-R1, or Qwen2.5-Coder:
```bash
export LLM_PROVIDER="ollama"
export OLLAMA_BASE_URL="http://localhost:11434"
python app.py
```

### 4. Custom vLLM / HuggingFace TGI Endpoint
```bash
export LLM_PROVIDER="custom"
export CUSTOM_LLM_URL="http://localhost:8000/v1/chat/completions"
export CUSTOM_LLM_TOKEN="secret-bearer-token"
python app.py
```

---

## Quickstart & Commands

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Interactive Web Dashboard
```bash
python app.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

### 3. Run the CLI Demo (Beats 1 & 2)
```bash
python demo.py
```

### 4. Run the 25-Scenario Evaluation Benchmark
```bash
python eval_set.py
```

### 5. Run Unit Tests
```bash
python tests/test_store.py
```

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `GET /` | `GET` | Serves the interactive Web Dashboard |
| `GET /api/graph` | `GET` | Fetches the full multi-hop graph for `REQ-2e9fa1` |
| `POST /api/beat1` | `POST` | Triggers Beat 1: edits requirement text and escalates RiskScore |
| `POST /api/beat2` | `POST` | Triggers Beat 2: ingests incident #8841 and creates `RULE-SEC-01` |
| `POST /api/code_drift` | `POST` | Diffs active Python AST/signatures against design specifications |
| `POST /api/confirm` | `POST` | Logs human-in-the-loop confirmation of flagged drift |
| `POST /api/override` | `POST` | Overrides flagged artifact to `VALID` status |
| `GET /api/eval_report`| `GET` | Runs the 25-scenario benchmark matrix and returns metrics |
| `POST /api/reset` | `POST` | Cleans and re-seeds the store to baseline state |

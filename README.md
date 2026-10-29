# Production-Oriented AI Research Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-green.svg)](https://docs.pydantic.dev/)
[![Tests](https://img.shields.io/badge/tests-10%2F10%20passing-brightgreen.svg)]()
[![Evaluation](https://img.shields.io/badge/eval%20suite-5%2F5%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-grade, inspectable agentic research system designed to deconstruct complex research inquiries, orchestrate multi-tool data collection, filter noise, synthesize structured source-grounded answers, and audit factual consistency.

---

## Architecture Overview

```
                      +-----------------------------+
                      |     User Inquiry / Prompt   |
                      +-----------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |   Security Guardrails       |  ---> (Blocked if Prompt Injection / Toxic)
                      |   & Input Sanitization      |
                      +-----------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |   1. Research Planner       |  Deconstructs inquiry into structured
                      |   (Schema: ResearchPlan)    |  sub-goals & assigns target tools
                      +-----------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |   2. Tool Execution Engine  |  Retries with backoff & error isolation
                      |   - Web Search (DDG/Wiki)   |  TTL Disk & In-Memory Caching
                      |   - Web Scraper (Readability)|
                      |   - ArXiv Academic Search   |
                      +-----------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |   3. Evidence Filter        |  Strips DOM noise, ad clutter, 404s;
                      |   & Source Indexer          |  Deduplicates URLs & ranks relevance
                      +-----------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |   4. Synthesizer            |  Emits strict Pydantic ResearchReport
                      |   (Source-Grounded)         |  with bracketed citations [1], [2]
                      +-----------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |   5. Grounding Judge        |  Audits citation fidelity;
                      |   & Calibrated Confidence   |  Downgrades confidence if ungrounded
                      +-----------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |  Final Structured Output    |  Executive summary, key findings,
                      |  & Telemetry Trace          |  sources, limitations & next steps
                      +-----------------------------+
```

---

## Key Features

1. **Deterministic Structured Outputs:** Guaranteed schema compliance via **Pydantic v2** models (`ResearchPlan`, `ResearchReport`, `SourceItem`).
2. **Multi-Tool Orchestration:**
   - **`web_search`:** DuckDuckGo real-time web search with fallback to Wikipedia API and offline synthetic knowledge base.
   - **`web_scraper`:** Resilient HTML fetcher stripping scripts, headers, navigation, footers, and ad tracking, bounded to configurable token ceilings.
   - **`academic_search`:** ArXiv API integration for deep peer-reviewed and technical architecture retrieval.
3. **Resilience & Fault Isolation:** Exponential backoff retry loops, timeout enforcement, malformed tool output recovery, and circuit breaking—tools fail gracefully without halting the agent.
4. **Factual Grounding & Hallucination Defense:** Automated **Grounding Judge** cross-checks every bullet point against cited source texts; ungrounded assertions trigger confidence downgrades.
5. **Security Perimeter:** Integrated prompt injection detection catching jailbreak attempts and system prompt exfiltration before burning LLM tokens.
6. **Built-in Mock / Offline Mode:** Zero-cost, 100% deterministic test and demo capability without needing third-party API keys.
7. **Observability & Telemetry:** Full execution tracing (`ResearchTracer`) recording step-level latency, cache hits, tool calls, and token estimates.

---

## Project Structure

```
Production-Oriented-AI-Research-Agent/
├── .env.example                     # Environment template
├── requirements.txt                 # Dependencies
├── README.md                        # Master architecture & design documentation
├── EVALUATION.md                    # Benchmark suite report & baseline comparison
├── DEMO_GUIDE.md                    # 3-5 min video recording script & walkthrough
├── main.py                          # CLI entry point
├── run_web.py                       # Web UI dashboard launcher
│
├── src/
│   ├── config.py                    # Centralized settings & environment variables
│   ├── models.py                    # Strict Pydantic models (Plan, Report, Sources)
│   ├── llm_client.py                # Multi-provider client (OpenAI, Compatible APIs, Mock)
│   ├── tracer.py                    # Observability, telemetry & execution event logger
│   ├── cache.py                     # Disk & in-memory TTL cache for tool queries
│   ├── guardrails.py                # Prompt injection defense & output credential sanitizer
│   ├── agent.py                     # Main ResearchAgent lifecycle coordinator
│   ├── cli.py                       # Rich terminal interface with spinners & formatted tables
│   │
│   ├── tools/
│   │   ├── base.py                  # Abstract tool base with retries, timeouts & error handling
│   │   ├── web_search.py            # DuckDuckGo + Wikipedia API + offline dataset
│   │   ├── web_scraper.py           # Readability-based HTML cleaner & token limiter
│   │   ├── academic_search.py       # ArXiv API technical paper retrieval
│   │   └── registry.py              # Central tool registry and dispatcher
│   │
│   ├── orchestrator/
│   │   ├── planner.py               # Question decomposition & tool selection
│   │   ├── executor.py              # Step execution engine with progress callbacks
│   │   ├── filter.py                # Noise filtering, URL deduplication & source ranking
│   │   ├── synthesizer.py           # Source-grounded report generator
│   │   └── judge.py                 # Citation grounding evaluator & confidence auditor
│   │
│   └── web/
│       ├── app.py                   # Flask REST server
│       └── templates/
│           └── index.html           # Modern, responsive single-page research dashboard
│
├── evaluation/
│   ├── test_cases.py                # 5 curated benchmarks (Happy path, Multi-entity, Injection, etc.)
│   ├── baseline.py                  # Non-agentic single-prompt LLM baseline
│   ├── eval_runner.py               # Benchmark runner generating JSON & Markdown reports
│   └── benchmark_report.md          # Generated benchmark results
│
├── tests/
│   ├── test_tools.py                # Unit tests for timeouts, empty inputs, caching
│   ├── test_models.py               # Pydantic schema validation tests
│   ├── test_guardrails.py           # Prompt injection regex & sanitization tests
│   └── test_agent_flow.py           # End-to-end integration tests
│
└── sample_outputs/                  # Exported real research reports
    ├── vector_databases_rag.md (.json)
    ├── indian_hr_tech_saas.md (.json)
    └── multi_agent_customer_support.md (.json)
```

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Git

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/samreet613/Production-Oriented-AI-Research-Agent.git
cd Production-Oriented-AI-Research-Agent

# Create virtual environment (optional but recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy the template configuration:
```bash
copy .env.example .env
```

Edit `.env` to configure your LLM provider:
```ini
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini

# Optional: Run without API keys (offline mock mode)
MOCK_MODE=false
```
> **Note:** The agent includes a deterministic `MockLLMProvider` and curated offline tool datasets. You can test and evaluate the entire system even without an OpenAI API key by using the `--mock` flag or setting `MOCK_MODE=true`.

---

## How to Run

### 1. Rich Terminal CLI
Run any research question directly from your terminal:
```bash
# Interactive mode
python main.py

# Direct query argument
python main.py "Compare the top 3 open-source vector databases for a startup building RAG products."

# Offline / Mock mode (Zero cost, instant)
python main.py "Find 5 Indian B2B SaaS startups in HR tech and summarize their positioning." --mock

# Export to Markdown and JSON
python main.py "Research the pros and cons of using a multi-agent architecture for customer support automation." --export-md report.md --export-json report.json
```

### 2. Web UI Dashboard
Launch the interactive browser dashboard:
```bash
python run_web.py
```
Open **`http://127.0.0.1:5000`** in your browser. You can select example queries, toggle mock mode, inspect the live orchestration plan, view verified sources, and download raw JSON reports.

### 3. Automated Benchmark Suite
Run the 5-case benchmark evaluation:
```bash
python main.py --eval
# Or directly:
python evaluation/eval_runner.py
```

### 4. Unit & Integration Tests
Run `pytest` to execute all 10 automated test suites:
```bash
python -m pytest tests/ -v
```

---

## Core Questions & Architectural Rationale

### 1. Why did you choose an agentic approach here?
A standard one-shot LLM prompt suffers from three fundamental flaws for research-grade inquiries:
1. **Knowledge Cutoff & Stale Data:** Foundational models cannot know recent benchmarks, startup funding rounds, or software updates released after their training cutoff.
2. **Hallucination & Fake Citations:** Standard models frequently fabricate URLs, misattribute quotes, and construct fictitious benchmarks with high grammatical confidence.
3. **Monolithic Reasoning:** Complex research questions (e.g. comparing vector databases across performance, licensing, and RAM consumption) require decomposition into distinct sub-problems.

An agentic architecture solves this by breaking the process into **inspectable phases**: formulating a visible plan, querying external ground-truth tools, filtering noise, synthesizing evidence, and auditing factual consistency before delivering the final answer.

---

### 2. What tools did you use, and why?
We implemented three specialized tools:
1. **`WebSearchTool` (DuckDuckGo + Wikipedia Fallback):**
   - *Why:* Provides broad coverage of recent technical announcements, benchmarks, and commercial market positioning without requiring expensive API credits. Integrated with a multi-tier fallback to Wikipedia and an offline dataset for resilience.
2. **`WebScraperTool` (Readability DOM Parser):**
   - *Why:* Search snippets alone often lack technical depth. The scraper fetches complete web pages, strips scripts, styles, navigation bars, and cookie notices, and truncates text to 4,000 characters to prevent context window pollution.
3. **`AcademicSearchTool` (ArXiv API):**
   - *Why:* For architectural inquiries (e.g. multi-agent coordination tradeoffs or vector indexing algorithms), peer-reviewed papers provide rigorous empirical benchmarks rather than marketing hype.

---

### 3. How does the system handle bad tool results?
Production tool calls frequently fail due to rate limits, DNS errors, HTTP 403/404s, or malformed HTML. Our system employs a multi-layered defense:
- **Error Containment (No Crashes):** Tools wrap executions in try/catch blocks returning `RawToolOutput(success=False, error=...)` instead of bubbling unhandled exceptions.
- **Exponential Backoff & Retries:** Every tool attempts up to 3 retries with jitter and exponential backoff (`t = backoff * 2^attempt`).
- **Graceful Fallbacks:** If DuckDuckGo fails or is rate-limited, the system falls back to Wikipedia API search, and then to local domain synthesis.
- **Information Filtering:** Scraped pages containing boilerplate error strings (`"Access Denied"`, `"Captcha"`, `"404"`) or snippets with `< 35` characters are automatically pruned before synthesis.

---

### 4. How do you reduce hallucinations?
Hallucination mitigation is built into the architecture at three distinct levels:
1. **Source Grounding by Design:** The synthesizer prompt strictly forbids inventing facts or metrics not present in the gathered evidence context, requiring bracketed citations (`[1]`, `[2]`).
2. **Post-Generation Grounding Judge:** An automated evaluator audits every generated key finding against the verified source snippets. If claims lack backing evidence, the grounding score drops.
3. **Calibrated Confidence:** If the grounding score falls below 80%, or if the inquiry targets unverified entities (e.g., speculative future earnings), the confidence is automatically downgraded to **Medium** or **Low**, with explicit disclosure in the `limitations_or_assumptions` section.

---

### 5. How would you make this production-ready?
To scale this prototype into an enterprise-grade service, the next engineering steps would be:
1. **Asynchronous Tool Execution:** Replace sequential step execution with `asyncio.gather()` or temporal workflow DAGs to run independent tool calls concurrently, cutting search latency by ~60%.
2. **Vector DB Embedding Memory:** Store scraped web pages in a persistent vector database (e.g. Qdrant) with hybrid BM25 + dense search for multi-hop follow-up queries.
3. **Distributed Rate Limiting & Proxy Rotation:** Implement Redis-backed token bucket rate limiters and residential proxy pools to prevent search engine CAPTCHAs under heavy traffic.
4. **Containerization & Autoscaling:** Package the service into Docker containers deployed on Kubernetes (EKS/GKE) with Celery/RabbitMQ task queues for asynchronous background research jobs.

---

### 6. What would you monitor in production?
In a live production environment, we would track four categories of telemetry via OpenTelemetry and Prometheus/Grafana:
1. **Quality & Factuality Metrics:**
   - Distribution of Grounding Scores (alerting if > 5% of reports score < 0.7).
   - Frequency of confidence downgrades (High vs Medium vs Low).
   - Hallucination flags detected by the Grounding Judge.
2. **Operational Latency & Reliability:**
   - P50, P95, and P99 latency broken down by pipeline stage (Planning, Tool Calls, Synthesis).
   - Tool failure rates and retry frequency per domain.
   - HTTP status codes (429 rate limits, 504 timeouts).
3. **Economic & Cost Metrics:**
   - Prompt and completion token consumption per inquiry.
   - Cache hit ratios (disk/memory TTL cache).
   - Total inference cost per completed research report.
4. **Security & Guardrail Triggers:**
   - Prompt injection interception rate and top offending IP addresses.
   - Output sanitizer redaction events (preventing accidental secret leakage).

---

### 7. What were your key tradeoffs?

| Design Decision | Chosen Approach | Alternative Considered | Tradeoff Rationale |
|:---|:---|:---|:---|
| **Orchestration Pattern** | **Planner-Executor Pipeline** | ReAct / Autonomous Looping Swarm | Autonomous swarms frequently suffer from infinite loops, unpredictable token consumption, and nondeterministic runtimes. A structured Planner-Executor pattern guarantees inspectability, bounded cost, and deterministic execution. |
| **Tool Execution** | **Sequential with Early Filtering** | Massive Parallel Web Crawl | Parallel crawling gathers more data but burns excessive bandwidth and tokens on low-signal pages. Sequential execution with selective scraping keeps context sizes lean and predictable. |
| **Output Format** | **Strict Pydantic JSON Schema** | Free-form Markdown Chat | Markdown chat is pleasant for users but impossible to validate programmatically. Strict Pydantic models guarantee consistent downstream consumption in enterprise APIs. |
| **Offline Reliability** | **Deterministic Mock Fallback** | Hard API Failure | Requiring live API keys and active internet connections breaks CI pipelines and reviewer grading. Built-in mock datasets allow 100% test reproducibility. |

---

## Evaluation Benchmark Summary

From our automated test suite (`evaluation/eval_runner.py`):

```
                        📊 Evaluation Benchmark Summary                        
┌─────────┬───────────────────────────┬────────┬───────────┬────────────┬─────────┐
│ Test ID │ Category                  │ Status │ Grounding │ Confidence │ Latency │
├─────────┼───────────────────────────┼────────┼───────────┼────────────┼─────────┤
│  TC-01  │ Technical Comparison      │  PASS  │   100%    │    High    │   0.08s │
│  TC-02  │ Market Research           │  PASS  │   100%    │    High    │   2.25s │
│  TC-03  │ Architecture Tradeoffs    │  PASS  │   100%    │   Medium   │   4.20s │
│  TC-04  │ Adversarial Security      │  PASS  │    N/A    │    Low     │   0.00s │
│  TC-05  │ Low-Evidence Stress Test  │  PASS  │   100%    │    Low     │   1.76s │
└─────────┴───────────────────────────┴────────┴───────────┴────────────┴─────────┘
Pass Rate: 5 / 5 (100%)
```
Detailed breakdown and baseline comparison can be viewed in [EVALUATION.md](file:///c:/Users/Amardeep/Downloads/Samreet%20Kaur%20Downloads/Production-Oriented-AI-Research-Agent/EVALUATION.md).

---

## Video Demonstration

For recording or evaluating the 3 to 5 minute video demonstration, refer to the step-by-step walkthrough and narration script in [DEMO_GUIDE.md](file:///c:/Users/Amardeep/Downloads/Samreet%20Kaur%20Downloads/Production-Oriented-AI-Research-Agent/DEMO_GUIDE.md).

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

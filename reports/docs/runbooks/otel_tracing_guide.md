# ACRAS OpenTelemetry Tracing — Practitioner's Guide

**Project:** Hybrid Agentic ML for Risk Assessment (ACRAS)
**Version:** 1.1 — Post-OTel Stabilization
**Audience:** MLOps Engineer, Agentic System Architect
**Companion doc:** `reports/docs/architecture/observability_tracing.md`

---

## 1. What You Are Actually Seeing in the Terminal

When `DEBUG_TELEMETRY=1` is set (or Jaeger is unavailable), OTel falls back to the **ConsoleSpanExporter**, printing each closed span as a JSON object to stdout. This is the log you have been observing in the ACRAS-API window.

---

> **NOTE:** We set **`DEBUG_TELEMETRY=1`** during our troubleshooting phase for three specific, practical reasons:

#### **1. "Visibility is Control" (Real-time Debugging)**
Without this flag, OpenTelemetry sends traces silently to the background collector (Jaeger). When we were facing the `ConnectionRefusedError`, the traces were simply disappearing into the void. By enabling `DEBUG_TELEMETRY=1`, every span was printed directly to your terminal as a JSON block. This allowed us to:
*   See the **exact structure** of the spans.
*   Confirm that the **GenAI semantic conventions** (agent names, tiers) were being attached correctly.
*   Verify that the "Brawn" (tools) were being traced alongside the "Brain" (agents).

#### **2. Isolation of Failure**
It helped us prove that the issue was a **transport problem**, not a logic problem. Because we could see the spans in the terminal, we knew the "instrumentation" (the code creating the spans) was working perfectly. This allowed us to narrow down the culprit to the `OTLP_ENDPOINT` port mismatch (`4319` vs `4318`) rather than looking for bugs in the agent code.

#### **3. Development without Infrastructure**
It serves as a **"Local-First" mode**. You don't always want to have a Docker container (Jaeger) running just to see if a new tool is being traced. Setting this variable allows any developer on the team to verify tracing logic immediately in their stdout without setting up a full observability backend.

> **Summary:** In a production environment, you would turn this OFF to keep logs clean. But in local development, it is your "X-ray vision" into the internal reasoning and performance of the agentic system.

---

### 1.1 Anatomy of a Single Console Span

Here is the real span from your session, annotated field-by-field:

```json
{
    "name": "POST /v1/predict",           // ① Span name — operation being traced
    "context": {
        "trace_id": "0xfb96b2b756f78713282f13718b6e3c3b",  // ② Unique ID for the FULL request
        "span_id": "0x9af3c4f1d342f97a",                    // ③ ID for THIS specific operation
        "trace_state": "[]"                                  // ④ W3C trace propagation state
    },
    "kind": "SpanKind.SERVER",            // ⑤ Role: SERVER = entry point, INTERNAL = child
    "parent_id": null,                    // ⑥ null = ROOT span (no parent)
    "start_time": "2026-05-08T19:52:50.679456Z",
    "end_time":   "2026-05-08T19:52:50.862231Z",  // ⑦ Duration = end - start = ~183ms for ML API call
    "status": { "status_code": "UNSET" }, // ⑧ UNSET=success, ERROR=failure
    "attributes": {                       // ⑨ Semantic data — the diagnostic gold
        "http.method": "POST",
        "http.url": "http://localhost:8000/v1/predict",
        "http.route": "/v1/predict",
        "http.status_code": 200,
        "net.peer.ip": "127.0.0.1",
        "net.peer.port": 61401
    },
    "resource": {                         // ⑩ Service identity — same on every span
        "attributes": {
            "service.name": "acras",
            "deployment.environment": "production"
        }
    }
}
```

#### The 10 Fields You Must Know

| # | Field | What It Tells You |
|:--|:------|:-----------------|
| ① | `name` | The operation. `POST /v1/predict` = FastAPI root. `llm_call` = agent reasoning. `tool_execution` = deterministic tool. |
| ② | `trace_id` | The **session fingerprint**. Every span from one `/v1/predict` request shares the same `trace_id`. Use this to reconstruct the full waterfall. |
| ③ | `span_id` | The **operation fingerprint**. Unique to this one span. Referenced by children as their `parent_id`. |
| ④ | `trace_state` | W3C context propagation bag. Empty `[]` means no upstream caller. |
| ⑤ | `kind` | `SERVER` = HTTP entry point. `INTERNAL` = nested child (ASGI lifecycle, tool, LLM call). |
| ⑥ | `parent_id` | `null` = root span. Any other value = this is a child of that span. Use this to build the tree. |
| ⑦ | `start_time` / `end_time` | **Latency computation**. Subtract to get exact duration of any step. |
| ⑧ | `status_code` | `UNSET` = success (OTel default). `ERROR` = exception was recorded on the span. |
| ⑨ | `attributes` | The **semantic payload**. Business context: which agent, which provider, which tool. |
| ⑩ | `resource` | Static service identity stamped on every span. Used to filter by service in Jaeger/Grafana. |

---

## 2. The Full ACRAS Span Hierarchy

The console prints spans **as they close** — innermost children appear first (LIFO). Reading bottom-up gives you the logical order. Here is the complete tree for one Company 1090 assessment:

```
trace_id: 0x0a78323c3348e2f5a3a45fbefa818ef0
│
└── POST /v1/predict                           [SpanKind.SERVER]   ~183ms
    │   span_id: 0xd9c1fbd0334699f7
    │   parent_id: null  (ROOT)
    │   http.status_code: 200
    │
    ├── POST /v1/predict http receive           [SpanKind.INTERNAL] ~0ms
    │   parent_id: 0xd9c1fbd0334699f7
    │   asgi.event.type: "http.request"
    │
    ├── llm_call  [financial_analyst, tier_1]  [SpanKind.INTERNAL] ~5–12s
    │   gen_ai.agent.name: "financial_analyst"
    │   gen_ai.system:     "huggingface"
    │   gen_ai.request.tier: "tier_1"
    │   gen_ai.request.model: "Qwen/Qwen2.5-7B-Instruct"
    │   │
    │   ├── tool_execution (fetch_company_data)
    │   ├── tool_execution (calculate_debt_to_equity)
    │   ├── tool_execution (calculate_ebitda_margin)
    │   ├── tool_execution (calculate_current_ratio)
    │   └── tool_execution (calculate_revenue_growth)
    │
    ├── llm_call  [data_scientist, tier_1]     [SpanKind.INTERNAL] ~3–8s
    │   gen_ai.agent.name: "data_scientist"
    │   gen_ai.system:     "huggingface"
    │   gen_ai.request.tier: "tier_1"
    │   │
    │   └── tool_execution (get_credit_risk_score)
    │
    ├── llm_call  [orchestrator, tier_1]       [SpanKind.INTERNAL] ~5–15s
    │   gen_ai.agent.name: "orchestrator"
    │   gen_ai.system:     "huggingface"
    │   gen_ai.request.tier: "tier_1"
    │
    ├── POST /v1/predict http send (response.start)
    ├── POST /v1/predict http send (response.body)
    └── POST /v1/predict http send (response.body)
```

> **Why the hierarchy matters:** The `trace_id` ties all these spans together. When you see the 5 spans for the `/v1/predict` ASGI lifecycle in isolation, they look like noise. But grouped by `trace_id` in Jaeger, they form the complete end-to-end waterfall showing exactly where time was spent.

---

## 3. Jaeger UI — Practical Query Recipes

Once Jaeger is running (`http://localhost:16686`), use these specific queries to answer real operational questions.

### 3.1 Setup: Start Jaeger

```bash
docker run --rm -d \
  -p 16686:16686 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

Ensure your `.env` has:
```dotenv
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces
```

### 3.2 Recipe Catalog

#### Recipe A: Find All Traces for the `acras` Service
- **Service:** `acras`
- **Operation:** `POST /v1/predict`
- **Lookback:** `Last 1 hour`

This shows every risk assessment run. Click any trace to see the full waterfall.

---

#### Recipe B: Identify Slow Assessments (SLA Breach Detection)
- **Service:** `acras`
- **Operation:** `POST /v1/predict`
- **Min Duration:** `20s` (adjust to your SLA)

Any trace appearing here is a candidate for optimization. Expand its spans to see which agent (`financial_analyst`, `data_scientist`, `orchestrator`) or tool consumed the most time.

---

#### Recipe C: Detect Provider Fallbacks (Cost Spike Alert)
- **Service:** `acras`
- **Tags:** `gen_ai.request.tier=tier_2` OR `gen_ai.request.tier=tier_3`

> A `tier_2` span means the primary Qwen/HuggingFace model timed out and Gemini Flash was invoked. A `tier_3` span means Gemini Flash also failed and Gemini Flash-Lite was used. Regularly appearing `tier_2+` results signal provider instability and increased API costs.

---

#### Recipe D: Isolate a Specific Agent's Performance
- **Service:** `acras`
- **Tags:** `gen_ai.agent.name=orchestrator`

The orchestrator writes the final synthesis. If users report low-quality reports, check if its `llm_call` span duration has increased (more complex prompts) or if its `gen_ai.request.tier` has drifted to `tier_2` (degraded model).

---

#### Recipe E: Trace a Single Request from End-to-End
Copy a `trace_id` from the console logs (e.g., `0x0a78323c3348e2f5a3a45fbefa818ef0`). In Jaeger:
- Click **"Search"** tab → **"Trace ID"** input → paste the ID.

This reconstructs the exact waterfall for that specific request, isolating exactly where failures occurred.

---

## 4. Reading the Console Log Efficiently (Without Jaeger)

When Jaeger is not running, trace the execution manually using the `trace_id` field.

### Step 1: Group by `trace_id`

All spans with the same `trace_id` belong to one assessment run. In your terminal session:
```
trace_id: 0x0a78323c3348e2f5a3a45fbefa818ef0  →  Company 1090 run at 16:18:15 UTC
```

### Step 2: Build the Tree Using `parent_id`

```
span_id: 0xd9c1fbd0334699f7   parent_id: null          → ROOT (POST /v1/predict)
span_id: 0x0a3fa5876e27a1c3   parent_id: 0xd9c1...f97a → child of ROOT
span_id: 0x60823427ba4deb3f   parent_id: 0xd9c1...f97a → child of ROOT
```

### Step 3: Calculate Latency

```
Root span: start=20:18:15.126393Z, end=20:18:15.308436Z
Duration = 0.308 - 0.126 = 182ms  (FastAPI overhead only — no agent spans yet)
```

When full agent spans are present, use this formula per span:
```python
duration_ms = (end_time_ns - start_time_ns) / 1_000_000
```

### Step 4: Check `status_code`

| `status_code` | Meaning | Action |
|:---|:---|:---|
| `UNSET` | Success (OTel default for successful operations) | No action |
| `OK` | Explicitly marked successful by code | No action |
| `ERROR` | An exception was recorded on this span | Check `events` array for the exception message and stack trace |

---

## 5. Diagnosing Common Issues via Spans

### Issue: Assessment is slow (>30s)

1. Find the trace in Jaeger using Recipe B.
2. Expand the waterfall — look for the **longest horizontal bar**.
3. Check its `gen_ai.agent.name`: which agent is the bottleneck?
4. Check its `gen_ai.request.tier`: is it using a fallback (slower) model?

**Most likely causes:**
- `orchestrator` taking >15s → synthesis prompt too long; HuggingFace inference endpoint under load.
- `tool_execution (get_credit_risk_score)` taking >5s → FastAPI ML endpoint is cold-starting or the Random Forest model is being re-loaded from disk.

---

### Issue: Report quality is degraded

1. Filter traces by `gen_ai.request.tier=tier_2` (Recipe C).
2. If you see many `tier_2` results in a time window → HuggingFace API was unstable and Gemini Flash handled the load.
3. Check the agent: if `orchestrator` is on `tier_2`, the synthesis quality may differ from the primary model's output style.

---

### Issue: No traces appear in Jaeger

**Checklist:**
1. Verify Jaeger container is running: `docker ps | grep jaeger`
2. Verify port binding: `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces` in `.env`
3. Restart `launch_acras.bat` — the `.env` is read once at startup, not dynamically.
4. Confirm the ACRAS-API window does **not** show `"Exception while exporting Span"` or `port 4319` errors — that means the old process with a stale config is still running.

---

## 6. Attribute Reference: What ACRAS Currently Emits

### HTTP Layer (Auto — FastAPIInstrumentor)

| Attribute | Source | Example |
|:---|:---|:---|
| `http.method` | Request | `"POST"` |
| `http.url` | Request | `"http://localhost:8000/v1/predict"` |
| `http.route` | FastAPI router | `"/v1/predict"` |
| `http.status_code` | Response | `200` |
| `http.user_agent` | Request header | `"python-requests/2.32.5"` |
| `net.peer.ip` | Connection | `"127.0.0.1"` |
| `asgi.event.type` | ASGI lifecycle | `"http.request"` / `"http.response.start"` |

### Agent Layer (Manual — `graph.py`)

| Attribute | Source | Example |
|:---|:---|:---|
| `gen_ai.system` | `model_info` variable | `"huggingface"` / `"gemini"` |
| `gen_ai.agent.name` | Node name | `"financial_analyst"`, `"data_scientist"`, `"orchestrator"` |
| `gen_ai.request.tier` | Fallback logic | `"tier_1"`, `"tier_2"`, `"tier_3"` |
| `gen_ai.request.model` | Model factory | `"Qwen/Qwen2.5-7B-Instruct"`, `"gemini-2.5-flash"` |

### Tool Layer (Manual — `finance_tool.py`, `lookup_tool.py`, `ml_api_tool.py`)

| Attribute | Tool | Example |
|:---|:---|:---|
| `gen_ai.tool.name` | All tools | `"fetch_company_data"`, `"get_credit_risk_score"`, `"calculate_debt_to_equity"` |

---

## 7. Roadmap: Attributes Worth Adding Next

The current instrumentation covers latency, provider routing, and tool identification. The following additions would unlock business-level observability without changing the agent architecture.

### 7.1 Risk Decision Attribute (High Priority)

Add to `orchestrator_node` span after the risk score is computed:

```python
span.set_attribute("acras.risk_score", risk_score)          # e.g., 85.0
span.set_attribute("acras.risk_decision", "REJECT")          # "APPROVE" / "REVIEW" / "REJECT"
span.set_attribute("acras.company_id", str(company_id))      # e.g., "1090"
```

**Business value:** Enables queries like "show me all traces where the decision was REJECT in the last 7 days" — turning your trace backend into a lightweight audit log.

### 7.2 Deterministic Guardrail Events (High Priority)

When the orchestrator injects a `[SYSTEM] Deterministic Risk Advisory`, record it as a span event:

```python
span.add_event(
    "deterministic_guardrail_triggered",
    attributes={
        "guardrail.type": "mora_ratio_breach",   # or "current_ratio_breach"
        "guardrail.value": mora_ratio,
    }
)
```

**Business value:** Lets you audit exactly how often the LLM's narrative was overridden by deterministic rules — a critical metric for regulatory compliance.

### 7.3 Token Count Attributes (Medium Priority)

For HuggingFace/OpenAI providers, capture usage after each LLM call:

```python
if hasattr(response, "usage_metadata"):
    span.set_attribute("gen_ai.usage.input_tokens", response.usage_metadata.input_tokens)
    span.set_attribute("gen_ai.usage.output_tokens", response.usage_metadata.output_tokens)
```

**Business value:** Directly correlates token costs with specific agent roles. If the `orchestrator` accounts for 70% of tokens, its prompt can be optimized first.

### 7.4 Span Status on Tool Errors (Medium Priority)

Currently, if a tool raises an exception, the span status remains `UNSET`. Explicitly mark failures:

```python
# In tool modules, wrap execution:
try:
    result = ...
except Exception as e:
    span.set_status(StatusCode.ERROR, str(e))
    span.record_exception(e)
    raise
```

**Business value:** Makes ERROR spans visible in Jaeger's error filter, enabling instant detection of ML API failures without log-scraping.

---

## 8. Environment Variable Quick Reference

| Variable | Effect | When to Set |
|:---|:---|:---|
| `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces` | Sends spans to Jaeger | Development + Production with collector |
| `DEBUG_TELEMETRY=1` | Prints spans to stdout as JSON | Local debugging when Jaeger is unavailable |
| `TESTING=1` | Suppresses all export — no network calls | CI/CD pipelines, unit tests |
| `OTEL_SDK_DISABLED=true` | Disables the OTel SDK entirely | Emergency escape hatch |

> **Rule:** Never set both `TESTING=1` and `DEBUG_TELEMETRY=1` simultaneously — `TESTING` takes precedence and suppresses all export, making `DEBUG_TELEMETRY` a no-op.

---

## 9. Summary: The Observability Decision Matrix

| Question | Signal | Where to Look |
|:---|:---|:---|
| How long did the assessment take? | Root span duration | `POST /v1/predict` → `end_time - start_time` |
| Which agent was slowest? | Child span durations | `llm_call` spans by `gen_ai.agent.name` |
| Did a provider fallback occur? | `gen_ai.request.tier` | Filter for `tier_2` or `tier_3` |
| Which tools were invoked? | `tool_execution` spans | `gen_ai.tool.name` attribute |
| Did any step fail? | `status_code = ERROR` | Jaeger error filter or `events` array |
| Did a specific request fail? | Full trace reconstruction | Search by `trace_id` in Jaeger |
| What was the ML prediction latency? | `get_credit_risk_score` span | `tool_execution` → `gen_ai.tool.name=get_credit_risk_score` |

# ACRAS Jaeger Tracing — Practitioner's Guide

**Project:** Hybrid Agentic ML for Risk Assessment (ACRAS)
**Version:** 1.0 — Live Session Reference
**Audience:** MLOps Engineer, Agentic System Architect
**Companion docs:**
- `reports/docs/runbooks/otel_tracing_guide.md`
- `reports/docs/architecture/observability_tracing.md`

---

## 1. What Is Jaeger and Why ACRAS Uses It

The ACRAS system instruments every agent reasoning step, ML API call, and tool execution with OpenTelemetry spans. These spans are exported to Jaeger, which acts as the **visual backend** — turning raw JSON events into an interactive trace waterfall.

> **Relationship to the OTel Guide:** `otel_tracing_guide.md` explains what the spans *contain* and how to read them in the terminal. This guide explains how to *operate Jaeger itself* — deploy it, interpret its startup logs, understand its limitations, and plan its future.

---

## 2. Understanding the Startup Log (Annotated)

The log below is the **real startup output** from your ACRAS session on 2026-05-13. Each section is explained.

### 2.1 The v1 End-of-Life Warning

```
*******************************************************************************

🛑  WARNING: End-of-life Notice for Jaeger v1

You are currently running a v1 version of Jaeger, which is deprecated and will
reach end-of-life on December 31st, 2025. This means there will be no further
development, bug fixes, or security patches for v1 after this date.

We strongly recommend migrating to Jaeger v2 for continued support and access
to new features.
*******************************************************************************

application version: git-commit=63b27e1810a710ac54dc4522da0538e540bdc545,
                     git-version=v1.76.0, build-date=2025-12-03T16:07:08Z
```

**What this means:**

| Field | Value | Implication |
| :--- | :--- | :--- |
| `git-version` | `v1.76.0` | You are on the **last v1 release** (December 2025). |
| EOL Date | **December 31, 2025** | No further security patches for this image. |
| `jaegertracing/all-in-one:latest` | Resolves to v1 | The `latest` tag still points to v1 on Docker Hub. |

> [!WARNING]
> For production deployments, plan a migration to Jaeger v2. For local development, v1.76.0 is safe to use today. See [Section 6](#6-migrating-to-jaeger-v2-action-plan) for the migration action plan.

---

### 2.2 Port Allocation at Startup

The log confirms the exact ports that Jaeger bound to. This is the authoritative reference for firewall rules and `.env` configuration.

```
{"msg":"Starting GRPC server",       "endpoint":"[::]:4317"}   // OTLP gRPC receiver
{"msg":"Starting HTTP server",       "endpoint":"[::]:4318"}   // OTLP HTTP receiver ← ACRAS uses this
{"msg":"Starting jaeger-collector HTTP server", "host-port":":14268"}
{"msg":"Starting jaeger-collector gRPC server", "grpc.host-port":"[::]:14250"}
{"msg":"Query server started",  "http_addr":"[::]:16686",      // Jaeger UI
                                "grpc_addr":"[::]:16685"}
{"msg":"Admin server started",  "http.host-port":"[::]:14269"} // Health + metrics
```

**Complete Port Map:**

| Port | Protocol | Purpose | Who uses it |
| :--- | :--- | :--- | :--- |
| `4317` | gRPC | OTLP trace receiver | OTel SDKs (gRPC mode) |
| `4318` | HTTP | OTLP trace receiver | **ACRAS** (`OTEL_EXPORTER_OTLP_ENDPOINT`) |
| `14268` | HTTP | Jaeger native receiver (legacy) | Old Jaeger agents |
| `14250` | gRPC | Jaeger native receiver (legacy) | Old Jaeger agents |
| `16686` | HTTP | **Jaeger UI** | Browser / Developers |
| `16685` | gRPC | Query API | Grafana datasource plugin |
| `14269` | HTTP | Admin: `/health`, `/metrics` | Docker health checks |

> [!IMPORTANT]
> The ACRAS `.env` file must set `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces`. Port `4317` is for gRPC; using it with the HTTP exporter causes silent trace loss.

---

### 2.3 Memory Storage Initialization

```
{"msg":"Memory storage initialized","configuration":{"MaxTraces":0}}
```

`MaxTraces: 0` means **unlimited** traces are held in-memory. This is the default for the `all-in-one` image. Traces are lost when the container stops. For development, this is ideal. For CI pipelines, consider using a persistence-backed backend (see Section 6).

---

### 2.4 The First Live Trace — Channel READY Confirmation

At `16:20:19` (11 minutes after startup), Jaeger received its first span from ACRAS:

```json
{"msg":"[Channel #1] Channel Connectivity change to READY"}
{"msg":"[Channel #1 SubChannel #8] Subchannel picks a new address \"127.0.0.1:4317\""}
```

This confirms the internal gRPC channel between Jaeger's collector and its internal query service became active the moment ACRAS sent its first span. **This is the handshake that enables the Jaeger UI to show traces.**

---

## 3. Deploying Jaeger Locally

### 3.1 Persistent Setup (Recommended for Development)

Use this when you want traces to persist across multiple workflow runs in a single session.

#### **Bash (Linux/macOS/Git Bash)**
```bash
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

#### **PowerShell (Windows)**
```powershell
docker run -d --name jaeger `
  -e COLLECTOR_OTLP_ENABLED=true `
  -p 16686:16686 `
  -p 4318:4318 `
  jaegertracing/all-in-one:latest
```

> [!NOTE]
> PowerShell uses the backtick (`` ` ``) for line continuation, **not** the backslash (`\`). Using `\` in PowerShell causes the `docker: invalid reference format` error shown in the session terminal.

**Lifecycle commands:**
```powershell
docker stop jaeger    # Pause (traces preserved in memory until container starts again)
docker start jaeger   # Resume
docker rm -f jaeger   # Full teardown — all in-memory traces are lost
```

### 3.2 Ephemeral Setup (Quick Validation)

Use this when you only need to verify tracing works for a single run.

#### **PowerShell (Windows)**
```powershell
docker run --rm -d `
  -p 16686:16686 `
  -p 4318:4318 `
  jaegertracing/all-in-one:latest
```

The container is automatically deleted when stopped. No cleanup required.

### 3.3 Command Flag Reference

| Flag | Purpose | When to use |
| :--- | :--- | :--- |
| `--name jaeger` | Assigns a fixed ID, enables `docker stop/start jaeger`. | Persistent dev environments. |
| `--rm` | Deletes the container on exit. | One-off trace validation. |
| `-e COLLECTOR_OTLP_ENABLED=true` | Explicitly enables OTLP receivers on ports 4317/4318. | Ensures port 4318 is active. |
| `-d` | Detached mode (run in background). | Always — avoids blocking the terminal. |

---

## 4. Navigating the Jaeger UI

Open `http://localhost:16686` in your browser after starting the container.

### 4.1 Finding ACRAS Traces

1.  **Service dropdown** → select `acras`
2.  **Operation dropdown** → select `POST /v1/predict` (or `All`)
3.  **Lookback** → `Last 1 hour`
4.  Click **Find Traces**

### 4.2 Reading the Trace Waterfall

Each trace from an ACRAS analysis request will contain a **hierarchy of spans**:

```
POST /v1/predict  [SpanKind.SERVER — Root Span, parent_id: null]
  └── agent.reasoning  [SpanKind.INTERNAL]
        ├── tool.fetch_company_data
        ├── tool.calculate_financial_ratios
        ├── tool.ml_risk_prediction
        └── tool.generate_report
```

**Key fields to inspect in each span:**

| Field | What it tells you |
| :--- | :--- |
| `trace_id` | Links ALL spans in one request (e.g., `0xd780cab1081ca581...`) |
| `span_id` | Unique ID for this specific operation |
| `parent_id: null` | This is the **root span** — the entry point |
| `status_code: UNSET` | Operation succeeded |
| `status_code: ERROR` | Operation failed — check `events` for the exception |
| `http.status_code: 200` | FastAPI returned OK |
| Duration bar | Proportional width shows where time is spent |

### 4.3 Reading the Live Span from Your Session

The following root span was captured live during your 2026-05-13 session:

```json
{
    "name": "POST /v1/predict",
    "context": {
        "trace_id": "0xd780cab1081ca581ede6ba17f67485c0",
        "span_id": "0xe89ee157485d969b"
    },
    "kind": "SpanKind.SERVER",
    "parent_id": null,
    "start_time": "2026-05-13T20:10:29.603859Z",
    "end_time":   "2026-05-13T20:10:29.775043Z",
    "attributes": {
        "http.url": "http://localhost:8000/v1/predict",
        "http.method": "POST",
        "http.status_code": 200
    }
}
```

**Duration:** `775ms - 604ms = ~171ms` — This is the round-trip time for the ML risk prediction call. It serves as your **baseline latency benchmark** for the FastAPI service.

---

## 5. Common Operational Issues

### 5.1 `docker: invalid reference format` (PowerShell)

**Cause:** Using Bash-style `\` line continuation in PowerShell.
**Fix:** Replace every `\` with a backtick `` ` `` in your command.

### 5.2 Traces Not Appearing in UI

Run this checklist in order:

1.  **Is the container running?** → `docker ps` — look for `jaeger`.
2.  **Is port 4318 exposed?** → Confirm `-p 4318:4318` is in your run command.
3.  **Is `.env` correct?** → Must be `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces`. Not port `4317`.
4.  **Did you run a workflow?** → Traces only appear after at least one `POST /v1/predict` call.
5.  **Check `DEBUG_TELEMETRY`** → Set `DEBUG_TELEMETRY=1` in `.env` to confirm spans are being generated (they will print to the ACRAS-API terminal). If you see spans in the terminal but not in Jaeger, the issue is the export endpoint.

### 5.3 "Channel Exiting Idle Mode" in Jaeger Logs

```
{"msg":"[Channel #1] Channel exiting idle mode"}
```

This is **informational, not an error**. Jaeger's internal gRPC channel idles when no spans arrive and wakes automatically when the first span comes in. You saw this in your session at `16:20:19` (11 minutes after startup) — exactly when the first Streamlit-triggered analysis ran.

### 5.4 `Memory storage initialized — MaxTraces: 0`

This is the expected default. It means unlimited traces in memory. If you need to cap memory usage, restart with `-e SPAN_STORAGE_TYPE=memory -e MEMORY_MAX_TRACES=5000`.

---

## 6. Migrating to Jaeger v2 — Action Plan

The `jaegertracing/all-in-one:latest` image used in this session is **v1.76.0**, which reached end-of-life on **December 31, 2025**.

### 6.1 What Changes in v2

| Area | v1 | v2 |
| :--- | :--- | :--- |
| Config format | CLI flags | YAML config file |
| Image name | `jaegertracing/all-in-one` | `jaegertracing/jaeger` |
| OTLP support | Opt-in (`-e COLLECTOR_OTLP_ENABLED=true`) | **On by default** |
| Storage | In-memory, Cassandra, ES | Same + Badger (embedded) |
| Security patches | ❌ None after Dec 2025 | ✅ Active |

### 6.2 v2 Drop-In Replacement Command

#### **PowerShell (Windows)**
```powershell
docker run -d --name jaeger `
  -p 16686:16686 `
  -p 4318:4318 `
  jaegertracing/jaeger:latest
```

Note: `-e COLLECTOR_OTLP_ENABLED=true` is **no longer needed** — OTLP is enabled by default in v2.

### 6.3 Migration Resources

- **Official guide:** https://www.jaegertracing.io/docs/latest/migration/
- **Tracking issue:** https://github.com/jaegertracing/jaeger/issues/6321
- **v2 Docker Hub:** `jaegertracing/jaeger`

> [!TIP]
> When migrating, update the `observability_tracing.md` and this guide to reflect the new image name and remove the `COLLECTOR_OTLP_ENABLED` flag from the documented commands.

---

## 7. Environment Variable Quick Reference

| Variable | Required Value | Set in |
| :--- | :--- | :--- |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4318/v1/traces` | `.env` |
| `DEBUG_TELEMETRY` | `1` (local debug) / unset (production) | `.env` |
| `TESTING` | `1` (CI only) | CI environment |
| `COLLECTOR_OTLP_ENABLED` | `true` (Jaeger v1 only) | Docker run flag |

---

## 8. Session Reference Log Summary

| Timestamp | Event | Significance |
| :--- | :--- | :--- |
| `16:09:04` | Jaeger container started | v1.76.0 — EOL warning displayed |
| `16:09:04` | HTTP server started on `:16686` | UI available at `http://localhost:16686` |
| `16:09:04` | OTLP HTTP receiver on `:4318` | Ready to accept ACRAS spans |
| `16:09:04` | Memory storage initialized | `MaxTraces: 0` = unlimited |
| `16:09:05` | Jaeger container ID returned | `cd2e302c08a9...` — container is healthy |
| `16:10:29` | First ACRAS span received | `trace_id: 0xd780cab1...` |
| `16:20:19` | Internal gRPC channel → READY | Triggered by first span from ACRAS agent |

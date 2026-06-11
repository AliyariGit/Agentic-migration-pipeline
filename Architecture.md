# Agentic Migration Pipeline — Architecture

A governed, five-stage pipeline that autonomously migrates legacy VBScript and Classic ASP code to modern .NET Core C#, with automatic validation and surgical recovery.

---

## Table of Contents

1. [High-Level Overview](#1-high-level-overview)
2. [Directory Structure](#2-directory-structure)
3. [End-to-End Data Flow](#3-end-to-end-data-flow)
4. [Stage 1 — Extractor Agent](#4-stage-1--extractor-agent)
5. [Stage 2 — Context Assembler](#5-stage-2--context-assembler)
6. [Stage 3 — Generator](#6-stage-3--generator)
7. [Stage 4 — Validation Gate](#7-stage-4--validation-gate)
8. [Stage 5 — Recovery Agent](#8-stage-5--recovery-agent)
9. [Governance Files](#9-governance-files)
10. [Web UI Dashboard](#10-web-ui-dashboard)
11. [Key Data Schemas](#11-key-data-schemas)
12. [Running the Pipeline](#12-running-the-pipeline)
13. [Automation Deep-Dive — Classes, Functions & Technology](#13-automation-deep-dive--classes-functions--technology)

---

## 1. High-Level Overview

The pipeline takes two legacy source files as input and produces production-ready C# without human intervention:

```
Legacy VBScript + Classic ASP
           │
           ▼
  ┌─────────────────┐
  │  Stage 1        │  Decompose monolithic files into atomic units
  │  Extractor      │
  └────────┬────────┘
           │  5 JSON units
           ▼
  ┌─────────────────┐
  │  Stage 2        │  Inject rules, schema, and instructions per unit
  │  Assembler      │
  └────────┬────────┘
           │  5 context packages
           ▼
  ┌─────────────────┐
  │  Stage 3        │  Produce typed C# files from each context package
  │  Generator      │
  └────────┬────────┘
           │  5 C# / Razor files
           ▼
  ┌─────────────────┐
  │  Stage 4        │  Scan for forbidden patterns (9 rules, 3 severities)
  │  Validator      │
  └────────┬────────┘
           │
      ┌────┴─────┐
   PASSED     BLOCKED
      │           │
      ✓           ▼
         ┌─────────────────┐
         │  Stage 5        │  Apply surgical fixes, re-validate
         │  Recovery       │
         └────────┬────────┘
                  │
             ┌────┴──────┐
          PASSED     STILL BLOCKED
             ✓        (engineer review)
```

**Entry points:**
- `run_pipeline.py` — CLI orchestrator, runs all five stages sequentially
- `pipeline_ui.py` — Web dashboard with real-time log streaming (`http://localhost:8080`)

---

## 2. Directory Structure

```
agentic-pipeline/
│
├── run_pipeline.py                         # Main orchestrator
├── pipeline_ui.py                          # Web dashboard server
├── pipeline_ui.html                        # Dashboard HTML/CSS/JS
│
├── agents/
│   ├── extractor_agent.py                  # Stage 1
│   ├── context_assembler.py                # Stage 2
│   ├── generator.py                        # Stage 3
│   ├── enterprise_ai_validation_script.py  # Stage 4
│   └── recovery_agent.py                   # Stage 5
│
├── legacy/                                 # INPUT — never modified
│   ├── vbscript/
│   │   └── ProcessOrder.vbs               # 3 Subs: ProcessOrder, GetOrderTotal, CancelOrder
│   └── classic-asp/
│       └── order_detail.asp               # SQL DAL layer + UI layer
│
├── CLAUDE.md                               # Governance rulebook (agent must obey)
├── migration-patterns.md                   # Legacy → modern translation dictionary
│
├── sample-run/                             # Stages 1–2 output
│   ├── stage1-extracted-units/            # 5 atomic JSON units
│   ├── stage2-context-packages/           # 5 context packages (rules + schema + instructions)
│   └── stage5-recovery-logs/             # Recovery activity logs
│
├── output/                                 # Stage 3 output — generated C# code
│   ├── Services/
│   │   ├── OrderService.cs
│   │   └── OrderDataService.cs
│   ├── Controllers/
│   │   └── OrderController.cs
│   ├── ViewModels/
│   │   └── OrderDetailViewModel.cs
│   └── Views/Order/
│       └── Detail.cshtml
│
└── validation-reports/                     # Stage 4 output — JSON reports per file
    ├── OrderService_report.json
    ├── OrderController_report.json
    ├── OrderDetailViewModel_report.json
    ├── OrderDataService_report.json
    └── Detail_report.json
```

---

## 3. End-to-End Data Flow

| Stage | Agent | Reads | Writes |
|-------|-------|-------|--------|
| 1 | `extractor_agent.py` | `legacy/**` | `sample-run/stage1-extracted-units/*.json` |
| 2 | `context_assembler.py` | Stage 1 units + `CLAUDE.md` + `migration-patterns.md` + MCP schema | `sample-run/stage2-context-packages/*.json` |
| 3 | `generator.py` | Stage 2 context packages | `output/**/*.cs`, `output/**/*.cshtml` |
| 4 | `enterprise_ai_validation_script.py` | `output/**` | `validation-reports/*_report.json` |
| 5 | `recovery_agent.py` | BLOCKED reports + `output/**` | Modified files in `output/`, `stage5-recovery-logs/*.json` |

---

## 4. Stage 1 — Extractor Agent

**File:** `agents/extractor_agent.py`

**Goal:** Break monolithic legacy files into the smallest independently-migratable units — one Sub, one Function, or one architectural layer.

### VBScript Processing

1. Read `ProcessOrder.vbs` as a string.
2. Regex-extract every `Sub` and `Function` block:
   ```
   (?:Sub|Function)\s+\w+.*?End\s+(?:Sub|Function)
   ```
3. For each block, extract metadata:
   - **COM objects** — `CreateObject("...")` references → will be replaced with injected services
   - **SQL injection risk** — string concatenation (`&`) inside SQL literals
   - **Error handling presence** — `On Error` keyword

4. Produce one JSON unit per Sub/Function.

### Classic ASP Processing

1. Read `order_detail.asp` as a string.
2. Detect SQL blocks, `Request.Form` inputs, and `Session` access via regex.
3. **Split into two units** based on responsibility:
   - `DATA_ACCESS_LAYER` — SQL queries, form inputs, session variables → target: EF Core service
   - `UI_RESPONSE_LAYER` — `Response.Write` calls, HTML → target: Controller + ViewModel + Razor view

### Output per unit

```json
{
  "unit_id": "vbs_processorder_1",
  "source_file": "legacy/vbscript/ProcessOrder.vbs",
  "unit_type": "Sub",
  "name": "ProcessOrder",
  "legacy_code": "Sub ProcessOrder(...)\n  ...\nEnd Sub",
  "metadata": {
    "com_objects_detected": ["ADODB.Connection"],
    "sql_patterns_detected": 2,
    "has_error_handling": true,
    "has_sql_injection_risk": true
  },
  "migration_target": "public async Task ProcessOrderAsync(...) in OrderService.cs",
  "extracted_at": "2026-06-11T00:22:15.123456"
}
```

**Result:** 5 atomic JSON units (3 from VBScript, 2 from ASP).

---

## 5. Stage 2 — Context Assembler

**File:** `agents/context_assembler.py`

**Goal:** Build a self-contained context package for each unit — everything the generator needs and nothing it doesn't.

### What gets assembled

For each Stage 1 unit, the assembler fetches and packages:

| Component | Source | Purpose |
|-----------|--------|---------|
| `rulebook` | `CLAUDE.md` | Architecture rules the generator must follow |
| `migration_patterns` | `migration-patterns.md` | Legacy → modern translation table |
| `live_schema` | MCP server (simulated) | Typed entity definitions — prevents hallucinated table/column names |
| `agent_instructions` | Generated per unit | Exact slash command + task description + per-unit constraints |

### Slash command routing

| Unit type | Slash command assigned |
|-----------|----------------------|
| VBScript Sub / Function | `/map-vbscript-to-logic` |
| ASP Data Access Layer | `/modernize-asp-dal` |
| ASP UI Layer | `/modernize-asp-view` |

### MCP schema (simulated)

In production this is a live call. Here it returns the four EF Core entities the generated code will use:

```python
MCP_SCHEMA = {
  "entities": {
    "Order":     { "table": "Orders",     "properties": { "Id": "int (PK)", "CustomerId": "int (FK)", "Status": "string", "Total": "decimal", ... } },
    "Customer":  { "table": "Customers",  "properties": { ... } },
    "OrderItem": { "table": "OrderItems", "properties": { ... } },
    "AuditLog":  { "table": "AuditLogs",  "properties": { ... } }
  }
}
```

### Example agent instructions (excerpt)

```
SLASH COMMAND: /map-vbscript-to-logic
TASK: Migrate the VBScript Sub 'ProcessOrder' to a C# async method.

RULES (from CLAUDE.md — non-negotiable):
1. Output class MUST be sealed
2. Method MUST be async Task or async Task<T>
3. NO SQL strings — use EF Core entities from the live schema
4. NO bare catch blocks — log all exceptions
5. ALL dependencies via constructor injection
6. XML doc comment on the method

COM OBJECTS DETECTED: ['ADODB.Connection']
→ Replace with: constructor-injected AppDbContext

SQL INJECTION RISKS DETECTED: True
→ Replace ALL SQL strings with EF Core typed queries
```

### Output per unit

```json
{
  "unit_id": "vbs_processorder_1",
  "assembled_at": "2026-06-11T00:22:30.456789",
  "slash_command": "/map-vbscript-to-logic",
  "rulebook": "# CLAUDE.md ...",
  "migration_patterns": "# migration-patterns.md ...",
  "live_schema": { "entities": { "Order": { ... }, ... } },
  "target_unit": { ... },
  "agent_instructions": "SLASH COMMAND: /map-vbscript-to-logic\nTASK: ..."
}
```

**Result:** 5 context packages, each fully self-contained.

---

## 6. Stage 3 — Generator

**File:** `agents/generator.py`

**Goal:** Consume each context package and write valid, architecture-compliant C# to disk.

In production this submits the context package to the Claude API. Here it produces realistic sample output for each slash command to demonstrate the full pipeline.

### Routing logic

| Slash command | Files produced |
|--------------|----------------|
| `/map-vbscript-to-logic` | `output/Services/OrderService.cs` (3 async methods, one per VBScript Sub) |
| `/modernize-asp-view` | `output/Controllers/OrderController.cs`, `output/ViewModels/OrderDetailViewModel.cs`, `output/Views/Order/Detail.cshtml` |
| `/modernize-asp-dal` | `output/Services/OrderDataService.cs` |

### Generated code shape

All output obeys CLAUDE.md by construction:

```csharp
/// <summary>Processes a customer order and updates its status.</summary>
public async Task ProcessOrderAsync(int orderId, int customerId, decimal amount)
{
    try
    {
        var order = await _context.Orders.FindAsync(orderId)
            ?? throw new InvalidOperationException($"Order {orderId} not found.");

        order.Status = "Processing";
        await _context.SaveChangesAsync();
        _logger.LogInformation("Order {OrderId} processed", orderId);
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "Failed to process Order {OrderId}", orderId);
        throw;
    }
}
```

**Result:** 5 files written to `output/` — 4 `.cs` files + 1 `.cshtml` Razor view.

---

## 7. Stage 4 — Validation Gate

**File:** `agents/enterprise_ai_validation_script.py`

**Goal:** Scan every generated file for forbidden patterns before code reaches a human reviewer. A BLOCKED result does not stop the pipeline — it triggers Stage 5.

### Validation rules

| Rule ID | Severity | What it catches |
|---------|----------|-----------------|
| `sql_string_concatenation` | CRITICAL | SQL built by string `+` — injection risk |
| `bare_catch_block` | CRITICAL | `catch { }` or empty `catch (Exception)` — swallows errors silently |
| `dynamic_keyword` | CRITICAL | `dynamic` type — loses compile-time safety |
| `session_direct_access` | HIGH | `Session[` — bypasses auth middleware |
| `response_write` | HIGH | `Response.Write(` — UI output in wrong layer |
| `non_sealed_service` | HIGH | Service class missing `sealed` — architecture violation |
| `synchronous_db_call` | HIGH | `.Find(` / `.First(` etc. without `Async` — thread-pool starvation |
| `untyped_variable` | MEDIUM | `object varName =` — weakens type safety |
| `missing_null_check` | MEDIUM | `FindAsync(...)` result not guarded with `??` |

### Status determination

- **PASSED** — zero CRITICAL or HIGH issues
- **BLOCKED** — one or more CRITICAL or HIGH issues found

### Output per file

```json
{
  "file": "output/Services/OrderService.cs",
  "status": "PASSED",
  "issues": [],
  "checked_at": "2026-06-11T00:22:45.789012",
  "issue_count": { "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0 }
}
```

In demo mode (`--inject-failure`), the validator intentionally inserts violations to prove the recovery stage works.

**Result:** One JSON report per file in `validation-reports/`.

---

## 8. Stage 5 — Recovery Agent

**File:** `agents/recovery_agent.py`

**Goal:** For each BLOCKED file, apply targeted surgical fixes — no full regeneration.

### Fix handlers

| Pattern ID | Transformation applied |
|-----------|------------------------|
| `bare_catch_block` | Adds `_logger.LogError(ex, ...)` and re-throws |
| `dynamic_keyword` | Replaces `dynamic` with `object` + `// TODO: use explicit type` |
| `session_direct_access` | Rewrites `Session["key"]` → `_sessionService.Get("key")` |
| `synchronous_db_call` | Appends `Async` suffix to DB calls and wraps with `await` |
| `non_sealed_service` | Inserts `sealed` into the class declaration |
| `response_write` | Comments out the line and flags for engineer review |

### Recovery loop

```
Read BLOCKED report
       │
       ▼
Load generated file content
       │
       ▼
Apply fix handler for each unique pattern_id
       │
       ▼
Write fixed content back to disk
       │
       ▼
Re-run Stage 4 validator on the fixed file
       │
  ┌────┴──────┐
PASSED     STILL BLOCKED
  │             │
  ✓         Save log with
         "requires_engineer_review: true"
```

### Recovery log output

```json
{
  "file": "output/Services/OrderService.cs",
  "original_status": "BLOCKED",
  "fixes_applied": ["bare_catch_block", "synchronous_db_call"],
  "new_status": "PASSED",
  "recovered_at": "2026-06-11T00:22:55.234567"
}
```

**Result:** Modified files in `output/`, recovery logs in `sample-run/stage5-recovery-logs/`.

---

## 9. Governance Files

### `CLAUDE.md`

The single source of truth for what the generator is and is not allowed to produce. Every rule in this file has a corresponding validator check in Stage 4.

| Section | Contents |
|---------|----------|
| Architecture Rules | `sealed` classes, `async Task` methods, constructor injection only, repository pattern, 3-tier layering |
| C# Code Standards | PascalCase/camelCase conventions, method naming (`VerbNounAsync`), XML doc comments on all public methods |
| Forbidden Patterns | `dynamic`, untyped `object`, bare catches, SQL concatenation, `Session[]`, `Response.Write`, synchronous DB calls |
| Migration Targets | VBScript Sub → sealed Service; ASP SQL block → EF Core DbContext; ASP UI → Controller + ViewModel + Razor |

### `migration-patterns.md`

A translation dictionary used by the Context Assembler to tell the generator exactly which modern construct maps to each legacy one:

| Legacy | Modern |
|--------|--------|
| `ADODB.Connection` | `AppDbContext` (constructor-injected) |
| `conn.Execute("SELECT ...")` | `await _context.Orders.FindAsync(id)` |
| `Request.Form["x"]` | Strongly-typed ViewModel property |
| `Session["UserId"]` | `_sessionService.Get("UserId")` |
| `Response.Write(html)` | Razor `@Model.Property` |
| `On Error Resume Next` | `try/catch` with `_logger.LogError` |

---

## 10. Web UI Dashboard

**File:** `pipeline_ui.py`  
**Start:** `python pipeline_ui.py`  
**Open:** `http://localhost:8080`

### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serves the dashboard HTML |
| `POST` | `/api/run` | Starts the pipeline (`?demo=true` for demo mode) |
| `GET` | `/api/log` | Returns accumulated log lines + running status |
| `GET` | `/api/files` | Lists generated files in `output/` |
| `GET` | `/api/file?path=...` | Returns file content for the code viewer |
| `GET` | `/api/reports` | Lists validation reports with status and issue counts |

### Dashboard features

- **Progress bar** — 5-step visual indicator; each step goes idle → active → done/fail
- **Live log panel** — streams stdout from all agent scripts in real time
- **File browser** — sidebar listing generated `.cs` and `.cshtml` files
- **Code viewer** — syntax-highlighted view of any generated file
- **Validation panel** — per-file report with severity-badged issue list
- **Status bar** — total files generated, passed count, blocked count

---

## 11. Key Data Schemas

### Extracted Unit (Stage 1 → Stage 2)

```json
{
  "unit_id":         "string  — e.g. vbs_processorder_1",
  "source_file":     "string  — path to original legacy file",
  "unit_type":       "string  — Sub | Function | DATA_ACCESS_LAYER | UI_RESPONSE_LAYER",
  "name":            "string  — method or layer name",
  "legacy_code":     "string  — full source text of this unit",
  "metadata": {
    "com_objects_detected":    ["ADODB.Connection"],
    "sql_patterns_detected":   2,
    "has_error_handling":      true,
    "has_sql_injection_risk":  true
  },
  "migration_target": "string  — target class.method and file",
  "extracted_at":     "ISO 8601 timestamp"
}
```

### Context Package (Stage 2 → Stage 3)

```json
{
  "unit_id":            "string",
  "assembled_at":       "ISO 8601 timestamp",
  "slash_command":      "/map-vbscript-to-logic | /modernize-asp-view | /modernize-asp-dal",
  "rulebook":           "string  — full CLAUDE.md contents",
  "migration_patterns": "string  — full migration-patterns.md contents",
  "live_schema": {
    "entities": {
      "Order":     { "table": "Orders",     "properties": { ... } },
      "Customer":  { "table": "Customers",  "properties": { ... } },
      "OrderItem": { "table": "OrderItems", "properties": { ... } },
      "AuditLog":  { "table": "AuditLogs",  "properties": { ... } }
    }
  },
  "target_unit":        { ... extracted unit ... },
  "agent_instructions": "string  — full prompt for the generator"
}
```

### Validation Report (Stage 4 → Stage 5)

```json
{
  "file":       "string  — path to the file that was checked",
  "status":     "PASSED | BLOCKED",
  "issues": [
    {
      "severity":     "CRITICAL | HIGH | MEDIUM",
      "pattern_id":   "string  — e.g. bare_catch_block",
      "description":  "string",
      "line_number":  42,
      "line_content": "string  — the offending line",
      "fix_hint":     "string  — what the recovery agent should do"
    }
  ],
  "checked_at":   "ISO 8601 timestamp",
  "issue_count":  { "CRITICAL": 0, "HIGH": 1, "MEDIUM": 0 }
}
```

### Recovery Log (Stage 5 output)

```json
{
  "file":            "string  — path to the fixed file",
  "original_status": "BLOCKED",
  "fixes_applied":   ["bare_catch_block", "synchronous_db_call"],
  "new_status":      "PASSED | BLOCKED",
  "recovered_at":    "ISO 8601 timestamp"
}
```

---

## 12. Running the Pipeline

```bash
# Full clean migration
python run_pipeline.py

# Demo mode — injects validation failures to show Stage 5 recovery
python run_pipeline.py --demo

# Web dashboard
python pipeline_ui.py
# then open http://localhost:8080
```

### Stage-by-stage (manual)

```bash
python agents/extractor_agent.py
python agents/context_assembler.py
python agents/generator.py
python agents/enterprise_ai_validation_script.py
python agents/enterprise_ai_validation_script.py --inject-failure  # demo only
python agents/recovery_agent.py
```

### Requirements

- Python 3.11+
- Standard library only — no `pip install` needed

---

## 13. Automation Deep-Dive — Classes, Functions & Technology

### Technology Stack

**No LangChain. No LangGraph. No AutoGen. No CrewAI.**

This pipeline uses **pure Python standard library only** — `re`, `json`, `os`, `glob`, `subprocess`, `dataclasses`, `pathlib`, `datetime`. Zero external dependencies, zero `pip install`. The architecture deliberately avoids agent frameworks to show the underlying mechanics clearly.

The Claude API **is referenced** as the production path (in `generator.py` there is a comment block showing `anthropic.Anthropic()` usage), but in this demo it is **not called** — the generator uses static templates to simulate what a Claude API call would return.

To wire in the real API at Stage 3:

```python
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4000,
    system=context_package["rulebook"],           # CLAUDE.md as system prompt
    messages=[{
        "role": "user",
        "content": context_package["agent_instructions"]  # slash command + unit
    }]
)
generated_code = response.content[0].text
```

---

### Orchestrator — `run_pipeline.py`

**`banner(stage_num, title, description)`**
Prints a formatted stage header to stdout. Visual only.

**`cleanup()`**
Wipes `sample-run/`, `output/`, and `validation-reports/` using `shutil.rmtree` at the start of every run for a clean slate.

**`run_stage(script, extra_args=[]) → bool`**
The core sequencing mechanism. Spawns each agent as a child process:
```python
cmd = [sys.executable, script] + extra_args
result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
return result.returncode == 0
```
Stages 1–3 hard-stop the pipeline on failure (`sys.exit(1)`). Stages 4–5 are fire-and-continue — validation is expected to find issues, and recovery handles them. The `--demo` flag is forwarded to Stage 4 as `--inject-failure`.

**`main()`**
Reads `sys.argv` for `--demo`, records `datetime.now()` for elapsed time, calls `cleanup()` then sequences all 5 stages. Prints a final summary of all files produced.

---

### Stage 1 — `extractor_agent.py`

Automation mechanism: **regex-based structural parsing**. No AI involved.

**`extract_vbscript_units(filepath) → list[dict]`**

Single regex captures every Sub/Function block across multiple lines:
```python
pattern = r"((?:Sub|Function)\s+\w+.*?End\s+(?:Sub|Function))"
matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
```
`re.DOTALL` makes `.` match newlines so multi-line blocks are captured whole. For each match, three more regexes classify the block:
- `CreateObject\("([^"]+)"\)` — detects COM objects (need DI replacement)
- `(?:Execute|Open)\s*"([^"]*(?:SELECT|UPDATE|INSERT|DELETE)[^"]*)"` — detects SQL literals; checks for `&` concatenation to flag injection risk
- Plain string search `"On Error" in block` — detects error handling presence

**`extract_asp_units(filepath) → list[dict]`**

Splits one `.asp` file into exactly two units by architectural layer:
- **DAL unit**: SQL blocks (`conn.Execute`/`.Open` with SELECT/UPDATE/INSERT/DELETE), `Request.Form("x")` inputs, `Session("x")` accesses
- **UI unit**: count of `Response.Write(...)` calls, HTML blocks, `business_logic_in_view` boolean (true if Session access detected in view)

**`save_units(units, output_dir)`**
Writes each unit dict to `sample-run/stage1-extracted-units/{unit_id}.json` with `json.dump(..., indent=2)`.

**`run_extractor()`**
Entry point. Uses `Path("legacy/vbscript").glob("*.vbs")` and `Path("legacy/classic-asp").glob("*.asp")` to discover inputs dynamically — adding new legacy files to those folders is all that's needed to extend the pipeline.

---

### Stage 2 — `context_assembler.py`

Automation mechanism: **context construction** — packaging everything a code generator needs into one self-contained JSON per unit.

**`MCP_SCHEMA` (module-level dict)**
Simulates a live MCP (Model Context Protocol) server. Defines four EF Core entities (`Order`, `Customer`, `OrderItem`, `AuditLog`) with table names, typed property definitions, and `DbSet` declarations. Prevents the generator from hallucinating column or table names. In production: replace `fetch_mcp_schema()` with an HTTP call.

**`load_file(path) → str`**
Reads `CLAUDE.md` and `migration-patterns.md` as raw strings to embed verbatim in the context package.

**`fetch_mcp_schema(unit) → dict`**
Simulated MCP call — returns `MCP_SCHEMA`. Production signature: `GET https://your-mcp-server/schema?context={unit_id}`.

**`determine_slash_command(unit) → str`**
Routes by unit type:
- `unit_type in ["Sub", "Function"]` → `/map-vbscript-to-logic`
- `layer == "DATA_ACCESS_LAYER"` → `/modernize-asp-dal`
- `layer == "UI_RESPONSE_LAYER"` → `/modernize-asp-view`

**`build_instructions(unit, slash_command) → str`**
Generates the structured prompt that would be sent to Claude. Three branches by unit type, each producing a multiline string containing: slash command name, task description, numbered non-negotiable rules from CLAUDE.md, output file path, and per-unit metadata (detected COM objects, SQL injection risks, session-in-view warnings).

**`assemble_context(unit) → dict`**
Composes the final package: `slash_command` + `rulebook` + `migration_patterns` + `live_schema` + `target_unit` + `agent_instructions`. This is the single object passed to the generator (or Claude API in production).

**`run_assembler()`**
Entry point. Uses `glob.glob("sample-run/stage1-extracted-units/*.json")` to discover all units, calls `assemble_context()` on each, saves to `sample-run/stage2-context-packages/{unit_id}_context.json`.

---

### Stage 3 — `generator.py`

Automation mechanism: **template routing** — in production, replaced by a Claude API call per context package.

**Module-level string constants (the four output templates)**

Each is a Python f-string with `{{}}` double-braces (to escape the C# braces from Python's `.format()`):

| Constant | Produces |
|----------|----------|
| `VBSCRIPT_SERVICE_OUTPUT` | `sealed class OrderService` with `ProcessOrderAsync`, `GetOrderTotalAsync`, `CancelOrderAsync` |
| `CONTROLLER_OUTPUT` | `sealed class OrderController` with `[HttpGet] Detail` and `[HttpPost] Cancel` |
| `VIEWMODEL_OUTPUT` | Three `sealed` classes: `OrderDetailViewModel`, `OrderItemViewModel`, `CancelOrderViewModel` |
| `RAZOR_VIEW_OUTPUT` | `@model OrderDetailViewModel` Razor view with `@if`, `@foreach`, tag helpers |

**`run_generator()`**
Entry point. Reads context packages via `glob.glob`, extracts `slash_command`, routes to the correct template. The `/modernize-asp-view` route is special — it writes **three files** from one context package and uses `continue` to skip the single-file write path. All others write a single `.cs` file.

---

### Stage 4 — `enterprise_ai_validation_script.py`

Automation mechanism: **line-by-line regex scanning** with dataclass-based severity classification. Entirely rule-based, no AI.

**`@dataclass ValidationIssue`**
Fields: `severity`, `pattern_id`, `description`, `line_number`, `line_content`, `fix_hint`. The `@dataclass` decorator auto-generates `__init__`, `__repr__`, `__eq__`. `dataclasses.asdict()` converts it to a plain dict for JSON serialization without a custom encoder.

**`@dataclass ValidationReport`**
Fields: `file`, `status` (`PASSED | BLOCKED`), `issues` (list of dicts), `checked_at`, `issue_count` dict.

**`VALIDATION_RULES` (module-level list)**
9 tuples of `(pattern_id, regex, severity, description, fix_hint)`. The `fix_hint` field is the machine-readable instruction passed directly to the recovery agent — it closes the feedback loop between Stages 4 and 5.

| Severity | Rules | Blocking? |
|----------|-------|-----------|
| CRITICAL | `sql_string_concatenation`, `bare_catch_block`, `dynamic_keyword` | Yes |
| HIGH | `session_direct_access`, `response_write`, `non_sealed_service`, `synchronous_db_call` | Yes |
| MEDIUM | `untyped_variable`, `missing_null_check` | No (flagged only) |

**`validate_file(filepath) → ValidationReport`**
Reads file with `f.readlines()`, loops `enumerate(lines, start=1)`, tests every line against every rule with `re.search(regex, line, re.IGNORECASE)`. Builds a `ValidationIssue` on each match. Status is `BLOCKED` if any CRITICAL or HIGH count > 0.

**`inject_failure_for_demo(filepath)`**
Appends three deliberately broken methods to the first `.cs` file when `--inject-failure` is passed. Injects: empty `catch {}`, synchronous `.Find(id)`, `dynamic result`, `Session["UserId"]`, and SQL string concatenation. This is how demo mode proves the validator catches real violations.

**`print_report(report)`**
Formats report to stdout with emoji severity icons (🔴 CRITICAL / 🟠 HIGH / 🟡 MEDIUM).

**`save_report(report, output_dir)`**
Serializes the `ValidationReport` dataclass to JSON via `asdict()` and writes to `validation-reports/{filename}_report.json`. This file is read directly by Stage 5.

---

### Stage 5 — `recovery_agent.py`

Automation mechanism: **surgical regex replacement** keyed by `pattern_id`. No full regeneration — only the flagged pattern in the flagged file is touched.

**`FIX_HANDLERS` (module-level dict)**
Maps `pattern_id → function`. Six handlers:

**`fix_bare_catch_block(content, issue) → str`**
Two `re.sub` calls — one for `catch { }`, one for `catch (Exception ...) { }`. Both replace with a proper block containing `_logger.LogError(ex, ...)` and `throw`.

**`fix_dynamic_keyword(content, issue) → str`**
`re.sub(r'\bdynamic\b', 'object /* TODO: Replace with explicit type per CLAUDE.md */', content)` — word-boundary match ensures only the keyword is replaced, not substrings. Safe intermediate step; flags for engineer follow-up.

**`fix_session_direct_access(content, issue) → str`**
`re.sub(r'Session\["(\w+)"\]', r'_sessionService.Get("\1") /* Injected: ISessionService */', content)` — capture group `(\w+)` preserves the key name in the replacement.

**`fix_synchronous_db_call(content, issue) → str`**
Five `re.sub` calls to append `Async` suffix (`.Find(` → `.FindAsync(`, `.First(` → `.FirstOrDefaultAsync(`, etc.), then one lookahead-based sub to prepend `await ` to any `_context.X.XAsync(...)` not already preceded by `await`.

**`fix_non_sealed_service(content, issue) → str`**
`re.sub(r'public\s+class\s+(\w+Service)\b', r'public sealed class \1', content)` — capture group preserves the class name.

**`fix_response_write(content, issue) → str`**
Wraps the call in a TODO comment rather than deleting it. Cannot auto-fix because the Razor equivalent depends on the view structure — the one handler that flags for manual review instead of resolving automatically.

**`apply_fixes(filepath, issues) → (str, list)`**
Reads file content, deduplicates `pattern_id` values with `set()` (avoids running the same fix twice), calls each handler, detects actual content change by comparing before/after strings, returns fixed content and list of applied fix IDs.

**`rerun_validation(filepath) → ValidationReport`**
Imports `validate_file` and `save_report` directly from `enterprise_ai_validation_script` using `sys.path.insert(0, os.path.dirname(__file__))` and a Python import — runs validation in-process on the fixed file and overwrites the original report. This is the closed-loop re-check.

**`run_recovery()`**
Entry point. Reads all `validation-reports/*_report.json`, filters for `status == "BLOCKED"`, calls `apply_fixes()` on each, saves fixed content, calls `rerun_validation()`, saves a recovery log to `sample-run/stage5-recovery-logs/{filename}_recovery.json`.

---

### What's Automated vs. What's Simulated

| Concern | Status | Mechanism |
|---------|--------|-----------|
| Stage sequencing | **Automated** | `subprocess.run` in `run_stage()` |
| Legacy code parsing | **Automated** | `re.findall` / `re.search` with `re.DOTALL` |
| Context assembly | **Automated** | File reads + dict composition |
| Schema injection | **Simulated** | `MCP_SCHEMA` dict (production: HTTP call to MCP server) |
| C# code generation | **Simulated** | String templates (production: Claude API call) |
| Validation scanning | **Automated** | Line-by-line regex against 9 rules + `@dataclass` reports |
| Failure injection (demo) | **Automated** | `inject_failure_for_demo()` appends bad code blocks |
| Surgical fix application | **Automated** | Per-`pattern_id` `re.sub` handlers in `FIX_HANDLERS` |
| Re-validation after fix | **Automated** | Direct Python import + in-process `validate_file()` call |
| File discovery | **Automated** | `glob.glob` with recursive patterns |

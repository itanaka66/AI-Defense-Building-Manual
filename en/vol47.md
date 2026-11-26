---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 47: Examining the Existing AI Defense Manager Implementation"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 47 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 46 we decided on seven Wazuh alert fields to pass to the LLM. Here, to decide where to integrate that allowlist, we examine the existing implementation of the AI Defense Manager on VM 230, read-only.

1. Check VM 230's network and listening services
2. Examine the list of APIs and the input shapes (schemas)
3. Trace the module structure, the dependencies, and the data flow from Wazuh alerts to the LLM
4. Check the current conversion (fields, event IDs, severity, classification) and decide the target specification
5. Confirm that there are no tests and no Git, and decide the preparations before changing anything

Source bodies, SQL and secrets are not displayed. No files are changed, no services restarted and nothing is sent to the LLM.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: VM 230's Network and Services

## 1.1 Address and Listening Ports

> **Run on: VM 230**

```bash
echo "===== VM230 IDENTITY ====="
hostname
ip -br -4 addr

echo
echo "===== VM230 ROUTING ====="
ip route

echo
echo "===== VM230 LISTENING PORTS ====="
ss -lnt
```

| Item | Result |
|---|---|
| IPv4 | `192.168.0.33/24` (`enp6s18`). At this point an address received by DHCP (fixed to `192.168.0.221` in a later part) |
| Gateway | `192.168.0.1` |
| SSH | `0.0.0.0:22` |
| Application | `127.0.0.1:8000` only |

Port 8000 listens only on the loopback address and is not set up for direct connection from VM 220. **Port 8000 is not exposed externally.**

## 1.2 The Service on Port 8000

> **Run on: VM 230**

```bash
echo "===== PORT 8000 PROCESS ====="
PID="$(ss -lntp 2>/dev/null | sed -n 's/.*127\.0\.0\.1:8000.*pid=\([0-9]*\).*/\1/p' | head -1)"

if [ -n "$PID" ]; then
    ps -p "$PID" -o pid,ppid,user,comm,args
    echo
    echo "===== PROCESS EXECUTABLE AND WORKDIR ====="
    readlink -f "/proc/$PID/exe"
    readlink -f "/proc/$PID/cwd"
    echo
    echo "===== SYSTEMD UNIT ====="
    systemctl status "$PID" --no-pager -l 2>&1 | head -35
else
    echo "PORT_8000_PID_NOT_IDENTIFIED"
fi

echo
echo "===== RELEVANT SYSTEMD SERVICES ====="
systemctl list-units --type=service --state=running --no-legend |
    grep -Ei 'ai|defense|uvicorn|fastapi|python|gunicorn' |
    head -40

echo
echo "===== LOCAL HTTP RESPONSE ====="
for path in / /health /openapi.json; do
    echo "--- PATH=$path ---"
    curl -sS --connect-timeout 2 --max-time 5 \
        -o /dev/null \
        -w 'HTTP_STATUS=%{http_code} CONTENT_TYPE=%{content_type}\n' \
        "http://127.0.0.1:8000$path" || true
done

echo
echo "RESPONSE_BODY_DISPLAYED=NO"
echo "ENVIRONMENT_VARIABLES_DISPLAYED=NO"
```

The FastAPI/Uvicorn `AI Defense Manager API` is started automatically by systemd and running, the project is in `/opt/ai-defense-manager`, and `/health` and `/openapi.json` returned `HTTP 200`. There is no need to add a new API server.

# Chapter 2: APIs and Input Shapes

## 2.1 List of APIs

> **Run on: VM 230**

```bash
echo "===== AI DEFENSE MANAGER OPENAPI ROUTE INVENTORY ====="

python3 - <<'PY'
import json
import urllib.request

url = "http://127.0.0.1:8000/openapi.json"

try:
    with urllib.request.urlopen(url, timeout=5) as response:
        spec = json.load(response)
except Exception as exc:
    print("OPENAPI_READ_FAILED=" + type(exc).__name__)
    raise SystemExit(0)

print("API_TITLE=" + str(spec.get("info", {}).get("title", "unknown")))
print("API_VERSION=" + str(spec.get("info", {}).get("version", "unknown")))

paths = spec.get("paths", {})
print(f"PATH_COUNT={len(paths)}")

for path, methods in sorted(paths.items()):
    for method, operation in sorted(methods.items()):
        if method.lower() not in {
            "get", "post", "put", "patch", "delete", "options", "head"
        }:
            continue

        tags = operation.get("tags", [])
        operation_id = operation.get("operationId", "")
        request_body = operation.get("requestBody", {})
        body_required = request_body.get("required", False)

        print(
            f"{method.upper():7} {path} "
            f"TAGS={','.join(tags)} "
            f"OPERATION_ID={operation_id} "
            f"REQUEST_BODY={bool(request_body)} "
            f"BODY_REQUIRED={body_required}"
        )

print("SCHEMA_PROPERTY_VALUES_DISPLAYED=NO")
print("REQUEST_EXAMPLES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
PY
```

| API | Method | Purpose |
|---|---|---|
| `/api/v1/analysis` | POST | AI analysis |
| `/api/v1/wazuh/analyze` | POST | analysis of Wazuh events |
| `/api/v1/wazuh/events` | GET | retrieval of Wazuh events |
| `/health` | GET | status check |

APIs that integrate with Wazuh already exist. Rather than building a new entry point, we examine whether these fit the seven-field allowlist.

## 2.2 Input Shape

> **Run on: VM 230**

```bash
echo "===== EXISTING API INPUT SCHEMA INVENTORY ====="

python3 - <<'PY'
import json
import urllib.request

url = "http://127.0.0.1:8000/openapi.json"

with urllib.request.urlopen(url, timeout=5) as response:
    spec = json.load(response)

schemas = spec.get("components", {}).get("schemas", {})

print("===== REQUEST BODY REFERENCES =====")
for path, methods in sorted(spec.get("paths", {}).items()):
    for method, operation in sorted(methods.items()):
        body = operation.get("requestBody")
        if not body:
            continue

        content = body.get("content", {})
        for content_type, details in content.items():
            schema = details.get("schema", {})
            print(
                f"{method.upper()} {path} "
                f"CONTENT_TYPE={content_type} "
                f"SCHEMA_REF={schema.get('$ref', 'inline')}"
            )

print("\n===== COMPONENT SCHEMAS =====")
for name, schema in sorted(schemas.items()):
    print(f"\nSCHEMA={name}")
    print(f"TYPE={schema.get('type', 'unspecified')}")
    print(f"REQUIRED_FIELDS={','.join(schema.get('required', []))}")

    for prop, definition in sorted(schema.get("properties", {}).items()):
        prop_type = definition.get("type", "unspecified")
        if "$ref" in definition:
            prop_type = definition["$ref"]
        elif "items" in definition:
            item_type = definition["items"].get(
                "type",
                definition["items"].get("$ref", "unspecified")
            )
            prop_type += f"[{item_type}]"

        print(f"  FIELD={prop} TYPE={prop_type}")

print("\nVALUES_AND_EXAMPLES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
print("DATABASE_CONTENT_DISPLAYED=NO")
PY
```

The existing `SecurityEvent` has the following shape, which differs in both names and structure from the seven fields of Part 46.

- Required: `source`, `severity`, `event_category`, `event_summary`
- Optional: `event_id`, `observed_at`, `agent_id`, `agent_name`, `source_ip`, `destination_ip`, `rule_id`, `rule_description`

# Chapter 3: Modules and Data Flow

## 3.1 Source Layout

> **Run on: VM 230**

```bash
echo "===== AI DEFENSE MANAGER SOURCE STRUCTURE ====="

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

targets = {
    "SecurityEvent",
    "WazuhAnalysisRequest",
    "AIAnalysisRequest",
    "AIAnalysisProposal",
    "analyze_wazuh_events_api_v1_wazuh_analyze_post",
    "get_wazuh_events_api_v1_wazuh_events_get",
    "create_analysis_api_v1_analysis_post",
}

if not root.is_dir():
    print("APP_DIRECTORY_NOT_FOUND")
else:
    for path in sorted(root.rglob("*.py")):
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception as exc:
            print(f"PARSE_ERROR_FILE={path.relative_to(root)} TYPE={type(exc).__name__}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in targets:
                    kind = type(node).__name__
                    print(
                        f"DEFINITION={node.name} "
                        f"KIND={kind} "
                        f"FILE={path.relative_to(root)} "
                        f"LINE={node.lineno}"
                    )

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = []
                if isinstance(node, ast.Import):
                    names = [x.name for x in node.names]
                else:
                    names = [node.module or ""] + [x.name for x in node.names]

                joined = " ".join(names).lower()
                if any(x in joined for x in (
                    "sqlalchemy", "sqlite", "psycopg",
                    "asyncpg", "qdrant", "wazuh"
                )):
                    print(
                        f"RELEVANT_IMPORT_FILE={path.relative_to(root)} "
                        f"LINE={node.lineno} "
                        f"MODULE_CATEGORY="
                        f"{','.join(x for x in ('sqlalchemy','sqlite','postgresql','qdrant','wazuh') if x in joined)}"
                    )

print("SOURCE_CODE_CONTENT_DISPLAYED=NO")
print("ENVIRONMENT_VARIABLES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
PY
```

The APIs are split into `api/analysis.py` and `api/wazuh.py`, the input shapes are in `schemas/`, and the analysis history is in `services/analysis_history.py`.

## 3.2 Internal Structure

Using Python's AST, we extract only the names of functions, classes, modules used and functions that access the DB.

> **Run on: VM 230**

```bash
echo "===== AI DEFENSE MANAGER INTERNAL STRUCTURE ====="

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

files = [
    "api/analysis.py",
    "api/wazuh.py",
    "services/analysis_history.py",
    "schemas/security_event.py",
    "schemas/wazuh.py",
    "schemas/analysis.py",
]

interesting_calls = {
    "connect", "execute", "executemany", "commit", "rollback",
    "fetchone", "fetchall", "get_alerts", "get_agents",
    "analyze", "create_analysis", "save", "load",
}

for relative in files:
    path = root / relative
    print(f"\nFILE={relative}")

    if not path.is_file():
        print("STATUS=NOT_FOUND")
        continue

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"PARSE_ERROR={type(exc).__name__}")
        continue

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            print(f"DEFINITION={type(node).__name__}:{node.name}:LINE={node.lineno}")

    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])

    selected = sorted(
        m for m in modules
        if m in {
            "sqlite3", "sqlalchemy", "psycopg", "asyncpg",
            "requests", "httpx", "wazuh", "json", "pydantic"
        }
    )
    print("RELEVANT_MODULES=" + ",".join(selected))

    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            else:
                continue

            if name in interesting_calls:
                calls.add(name)

    print("RELEVANT_CALL_NAMES=" + ",".join(sorted(calls)))

print("\nSOURCE_CODE_DISPLAYED=NO")
print("SQL_TEXT_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
PY
```

SQLite was used to store the analysis history.

## 3.3 Dependencies

> **Run on: VM 230**

```bash
echo "===== AI DEFENSE MANAGER MODULE DEPENDENCY MAP ====="

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

if not root.is_dir():
    print("APP_DIRECTORY_NOT_FOUND")
else:
    for path in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"PARSE_ERROR={path.relative_to(root)}:{type(exc).__name__}")
            continue

        rel = path.relative_to(root)
        definitions = []
        imports = set()
        calls = set()
        routes = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name not in definitions:
                    definitions.append(node.name)

            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith(("api", "schemas", "services", "core")):
                    imports.add(node.module)

            if isinstance(node, ast.Call):
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else (
                    func.id if isinstance(func, ast.Name) else ""
                )
                if any(x in name.lower() for x in (
                    "wazuh", "analysis", "history", "ollama",
                    "sqlite", "database", "client", "request"
                )):
                    calls.add(name)

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        func = decorator.func
                        name = func.attr if isinstance(func, ast.Attribute) else (
                            func.id if isinstance(func, ast.Name) else ""
                        )
                        if name in ("get", "post", "put", "delete", "patch"):
                            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                routes.append(f"{name.upper()} {decorator.args[0].value}")

        if definitions or imports or calls or routes:
            print(f"\nMODULE={rel}")
            if definitions:
                print("DEFINITIONS=" + ",".join(definitions))
            if imports:
                print("LOCAL_IMPORTS=" + ",".join(sorted(imports)))
            if calls:
                print("RELEVANT_CALLS=" + ",".join(sorted(calls)))
            if routes:
                print("ROUTES=" + ",".join(routes))

print("\nSOURCE_CODE_DISPLAYED=NO")
print("SQL_TEXT_DISPLAYED=NO")
print("ENVIRONMENT_VARIABLES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
PY
```

| Module | Role |
|---|---|
| `services/wazuh_relay.py` | retrieving and converting Wazuh alerts |
| `services/event_sanitizer.py` | masking event summaries, masking IP addresses |
| `services/ai_analysis.py` | AI analysis |
| `services/analysis_history.py` | SQLite analysis history |
| `schemas/action.py` | defensive action proposals, approval state, validation |
| `schemas/analysis_proposal.py` | AI analysis results and action constraints |

## 3.4 Masking, Retrieval and Analysis

> **Run on: VM 230**

```bash
echo "===== SANITIZER / RELAY / ANALYSIS INTERFACE AUDIT ====="

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

targets = [
    "services/event_sanitizer.py",
    "services/wazuh_relay.py",
    "services/ai_analysis.py",
    "schemas/security_event.py",
    "schemas/action.py",
    "schemas/analysis_proposal.py",
    "core/config.py",
]

def annotation(node):
    if node is None:
        return "unspecified"
    try:
        result = ast.unparse(node)
        return result[:100]
    except Exception:
        return "unavailable"

for relative in targets:
    path = root / relative
    print(f"\nFILE={relative}")

    if not path.is_file():
        print("STATUS=NOT_FOUND")
        continue

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"PARSE_ERROR={type(exc).__name__}")
        continue

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [
                arg.arg for arg in (
                    node.args.posonlyargs
                    + node.args.args
                    + node.args.kwonlyargs
                )
            ]
            print(
                f"FUNCTION={node.name} "
                f"ARGS={','.join(args)} "
                f"RETURN={annotation(node.returns)} "
                f"LINE={node.lineno}"
            )

        elif isinstance(node, ast.ClassDef):
            print(f"CLASS={node.name} LINE={node.lineno}")

            for child in node.body:
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    print(
                        f"  FIELD={child.target.id} "
                        f"TYPE={annotation(child.annotation)}"
                    )

                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if child.name.startswith("validate") or child.name.startswith("model_"):
                        print(f"  METHOD={child.name}")

    calls = set()
    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = (
                func.attr if isinstance(func, ast.Attribute)
                else func.id if isinstance(func, ast.Name)
                else ""
            )
            if name:
                calls.add(name)

        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith(("services", "schemas", "core")):
                imports.add(node.module)

    print("LOCAL_IMPORTS=" + ",".join(sorted(imports)))
    print("CALL_NAMES=" + ",".join(sorted(calls)))

print("\nSOURCE_CODE_DISPLAYED=NO")
print("FUNCTION_BODIES_DISPLAYED=NO")
print("CONFIGURATION_VALUES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
PY
```

| Function | Current implementation | Assessment |
|---|---|---|
| Wazuh retrieval | `fetch_wazuh_events()` | use as is |
| Wazuh conversion | `_convert_alert()` | where the allowlist goes |
| IP address masking | `sanitize_event_summary()` | use as is |
| AI analysis | `analyze_events()` | use as is |
| AI output validation | Pydantic `model_validate()` | use as is |
| Action constraints | `validate_action` | an important foundation for safety |
| Approval management | `ApprovalStatus` | used for human approval |

The target flow is as follows.

```text
Wazuh alerts.json
       │
       ▼
wazuh_relay.py
       │
       ▼
Dedicated Wazuh normalization and validation
       │
       ▼
LLM input DTO limited to 7 fields
       │
       ▼
ai_analysis.py
       │
       ▼
AIAnalysisProposal
       │
       ▼
Deterministic policy validation
       │
       ▼
Action Gateway
```

## 3.5 Tracing the Data Flow

> **Run on: VM 230**

```bash
echo "===== EXISTING EVENT DATAFLOW AUDIT ====="

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

targets = [
    "api/wazuh.py",
    "api/analysis.py",
    "services/wazuh_relay.py",
    "services/ai_analysis.py",
    "services/event_sanitizer.py",
]

for relative in targets:
    path = root / relative
    print(f"\nMODULE={relative}")

    if not path.is_file():
        print("STATUS=NOT_FOUND")
        continue

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"PARSE_ERROR={type(exc).__name__}")
        continue

    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            names = ",".join(alias.name for alias in node.names)
            print(
                f"IMPORT_FROM={node.module or '.'} "
                f"SYMBOLS={names}"
            )

        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            print(f"\nFUNCTION={node.name}")

            for child in ast.walk(node):
                if isinstance(child, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                    targets_list = []

                    raw_targets = (
                        child.targets if isinstance(child, ast.Assign)
                        else [child.target]
                    )

                    for target in raw_targets:
                        if isinstance(target, ast.Name):
                            targets_list.append(target.id)
                        elif isinstance(target, ast.Attribute):
                            targets_list.append(target.attr)

                    if targets_list:
                        print("  ASSIGN_TARGETS=" + ",".join(targets_list))

                elif isinstance(child, ast.Call):
                    func = child.func
                    name = (
                        func.attr if isinstance(func, ast.Attribute)
                        else func.id if isinstance(func, ast.Name)
                        else "dynamic"
                    )
                    keywords = ",".join(
                        keyword.arg or "**kwargs"
                        for keyword in child.keywords
                    )
                    if name in (
                        "SecurityEvent", "AIAnalysisRequest",
                        "analyze_events", "fetch_wazuh_events",
                        "_convert_alert", "sanitize_event_summary",
                        "model_validate", "model_dump", "post",
                        "json", "dumps", "loads"
                    ):
                        print(
                            f"  CALL={name} "
                            f"KEYWORDS={keywords or 'none'}"
                        )

                elif isinstance(child, ast.Attribute):
                    if child.attr in (
                        "event_summary", "source", "severity",
                        "event_category", "rule_id",
                        "rule_description", "agent_id",
                        "agent_name", "source_ip", "destination_ip",
                        "full_log", "data", "timestamp"
                    ):
                        print(f"  FIELD_ACCESS={child.attr}")

print("\nSOURCE_CODE_DISPLAYED=NO")
print("FUNCTION_BODIES_DISPLAYED=NO")
print("SQL_AND_CONFIGURATION_VALUES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
PY
```

Raw Wazuh alerts are converted to `SecurityEvent` in `wazuh_relay.py`, then `ai_analysis.py` masks `event_summary` and sends it to the AI. Masking just before sending to the AI cannot guarantee that no extra fields slip in, so we use the following two stages.

1. Right after Wazuh retrieval: extract and check only the allowed fields
2. Right before sending to the AI: keep the current masking and check the input once more

# Chapter 4: The Current Conversion

## 4.1 Input and Output Fields

> **Run on: VM 230**

```bash
echo "===== WAZUH INPUT / AI OUTPUT FIELD AUDIT ====="

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

targets = {
    "services/wazuh_relay.py": ["_convert_alert"],
    "services/ai_analysis.py": ["analyze_events"],
}

for relative, wanted in targets.items():
    path = root / relative
    print(f"\nMODULE={relative}")

    if not path.is_file():
        print("STATUS=NOT_FOUND")
        continue

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"PARSE_ERROR={type(exc).__name__}")
        continue

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name not in wanted:
            continue

        print(f"\nFUNCTION={node.name}")

        for child in ast.walk(node):
            if isinstance(child, ast.Subscript):
                value = child.value
                base = (
                    ast.unparse(value)
                    if isinstance(value, (ast.Name, ast.Attribute))
                    else "complex"
                )
                key = child.slice
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    print(f"  INPUT_KEY={base}[{key.value!r}]")

            elif isinstance(child, ast.Call):
                func = child.func
                name = (
                    func.attr if isinstance(func, ast.Attribute)
                    else func.id if isinstance(func, ast.Name)
                    else "dynamic"
                )

                if name in (
                    "SecurityEvent", "sanitize_event_summary",
                    "model_dump", "dumps", "post", "json"
                ):
                    print(f"  CALL={name}")
                    for keyword in child.keywords:
                        if keyword.arg:
                            try:
                                expression = ast.unparse(keyword.value)
                            except Exception:
                                expression = "unavailable"
                            print(
                                f"    ARG={keyword.arg} "
                                f"EXPRESSION={expression[:180]}"
                            )

            elif isinstance(child, ast.Dict):
                keys = []
                for key in child.keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        keys.append(key.value)
                if keys:
                    print("  DICT_KEYS=" + ",".join(keys))

print("\nALERT_VALUES_DISPLAYED=NO")
print("TOKENS_OR_CREDENTIALS_DISPLAYED=NO")
print("SOURCE_FILES_MODIFIED=NO")
print("DATABASE_ACCESSED=NO")
PY
```

Besides the seven fields, `_convert_alert()` also passed `agent_name` to `SecurityEvent`. What is sent to the AI is six fields: `event_id`, `observed_at`, `severity`, `rule_id`, `event_category` and `event_summary`. The raw Wazuh data is not sent wholesale, but this is not an input boundary limited to the seven fields.

| Wazuh field | Field inside VM 230 |
|---|---|
| `timestamp` | `observed_at` |
| `rule.id` | `rule_id` |
| `rule.level` | `severity` |
| `rule.groups` | `event_category` |
| `rule.description` | `rule_description` |
| `decoder.name` | not stored |
| `agent.id` | `agent_id` |

`agent_name`, IP addresses, `full_log`, `data`, `location` and `predecoder` are removed at the input boundary.

## 4.2 Event IDs

> **Run on: VM 230**

```bash
echo "===== EVENT ID / WAZUH KEY / SANITIZER AUDIT ====="

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

targets = {
    "services/wazuh_relay.py": ["_severity", "_convert_alert"],
    "services/event_sanitizer.py": ["sanitize_event_summary"],
    "schemas/security_event.py": [],
    "schemas/analysis_proposal.py": [],
}

for relative, wanted in targets.items():
    path = root / relative
    print(f"\nMODULE={relative}")

    if not path.is_file():
        print("STATUS=NOT_FOUND")
        continue

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"PARSE_ERROR={type(exc).__name__}")
        continue

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if wanted and node.name not in wanted:
                continue

            print(f"\nFUNCTION={node.name}")

            for child in ast.walk(node):
                if isinstance(child, ast.Subscript):
                    try:
                        expression = ast.unparse(child)
                    except Exception:
                        expression = "unavailable"
                    print(f"  SUBSCRIPT={expression[:160]}")

                elif isinstance(child, ast.Call):
                    func = child.func
                    name = (
                        func.attr if isinstance(func, ast.Attribute)
                        else func.id if isinstance(func, ast.Name)
                        else ""
                    )
                    if name in (
                        "UUID", "uuid4", "Field", "ip_address",
                        "sanitize_event_summary", "strip", "sub",
                        "SecurityEvent"
                    ):
                        print(f"  CALL={name}")

        elif isinstance(node, ast.ClassDef):
            print(f"\nCLASS={node.name}")
            for child in node.body:
                if isinstance(child, ast.AnnAssign):
                    if isinstance(child.target, ast.Name):
                        try:
                            default = (
                                ast.unparse(child.value)
                                if child.value is not None else "REQUIRED"
                            )
                        except Exception:
                            default = "UNAVAILABLE"
                        print(
                            f"  FIELD={child.target.id} "
                            f"DEFAULT={default[:100]}"
                        )

                elif isinstance(child, ast.FunctionDef):
                    print(f"  METHOD={child.name}")

print("\nEVENT_CONTENT_DISPLAYED=NO")
print("SOURCE_CODE_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
print("FILES_MODIFIED=NO")
PY
```

- `SecurityEvent.event_id` is generated automatically with `uuid4`
- Wazuh's `rule.id` is kept as a separate field
- `evidence_event_ids` in AI proposals require UUIDs

**Do not use Wazuh rule IDs as event UUIDs.** Also, `ttl_seconds` in AI proposals has a maximum of 900 seconds, and `requires_human_approval` defaults to `True`. These constraints are kept.

## 4.3 How the Wazuh Fields Are Used

> **Run on: VM 230**

```bash
echo "===== WAZUH RELAY FIELD ACCESS AUDIT ====="

python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/opt/ai-defense-manager/app/services/wazuh_relay.py")
tree = ast.parse(path.read_text(encoding="utf-8"))

wanted = {"_convert_alert", "fetch_wazuh_events"}

for node in tree.body:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    if node.name not in wanted:
        continue

    print(f"\nFUNCTION={node.name}")

    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            name = (
                func.attr if isinstance(func, ast.Attribute)
                else func.id if isinstance(func, ast.Name)
                else ""
            )

            if name == "get":
                base = (
                    ast.unparse(func.value)
                    if isinstance(func, ast.Attribute)
                    else "unknown"
                )
                key = (
                    ast.literal_eval(child.args[0])
                    if child.args and isinstance(child.args[0], ast.Constant)
                    else "dynamic"
                )
                print(f"  GET_BASE={base} KEY={key!r}")

            elif name == "SecurityEvent":
                for keyword in child.keywords:
                    print(f"  SECURITY_EVENT_FIELD={keyword.arg}")

            elif name in ("json", "loads", "read_text"):
                print(f"  CALL={name}")

        elif isinstance(child, ast.Subscript):
            try:
                base = ast.unparse(child.value)
                key = ast.literal_eval(child.slice)
            except Exception:
                continue
            if isinstance(key, str):
                print(f"  SUBSCRIPT_BASE={base} KEY={key!r}")

print("\nALERT_VALUES_DISPLAYED=NO")
print("TOKEN_CONTENT_DISPLAYED=NO")
print("SOURCE_CODE_DISPLAYED=NO")
print("FILES_MODIFIED=NO")
PY
```

`_convert_alert()` referred to `timestamp`, `rule.level`, `rule.id`, `rule.description`, `agent.id`, `agent.name`, `location` and `decoder.name`. It did not read `rule.groups` directly but went through a dictionary for classification.

## 4.4 Severity and Classification Mapping

> **Run on: VM 230**

```bash
echo "===== EXISTING CATEGORY / SEVERITY MAPPING AUDIT ====="

python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/opt/ai-defense-manager/app/services/wazuh_relay.py")
tree = ast.parse(path.read_text(encoding="utf-8"))

for node in tree.body:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue

    if node.name not in ("_severity", "_convert_alert"):
        continue

    print(f"\nFUNCTION={node.name}")

    for child in ast.walk(node):
        if isinstance(child, ast.Assign):
            for target in child.targets:
                if not isinstance(target, ast.Name):
                    continue

                if target.id not in ("category_map",):
                    continue

                print(f"  CONSTANT_MAP={target.id}")

                if isinstance(child.value, ast.Dict):
                    for key, value in zip(child.value.keys, child.value.values):
                        try:
                            k = ast.literal_eval(key)
                            v = ast.literal_eval(value)
                            print(f"    {k!r} -> {v!r}")
                        except Exception:
                            print("    NON_LITERAL_ENTRY=YES")

        elif isinstance(child, ast.Match):
            print("  MATCH_STATEMENT=YES")

        elif isinstance(child, ast.Compare):
            try:
                expression = ast.unparse(child)
            except Exception:
                continue

            if any(term in expression.lower() for term in ("level", "severity")):
                print(f"  COMPARISON={expression[:180]}")

print("\nALERT_VALUES_DISPLAYED=NO")
print("SOURCE_CODE_DISPLAYED=NO")
print("CONFIGURATION_VALUES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
print("FILES_MODIFIED=NO")
PY
```

Kept as the current specification:

| Wazuh Level | Internal severity |
|---|---|
| 0–3 | info |
| 4–7 | low |
| 8–11 | medium |
| 12–14 | high |
| 15–16 | critical |

| Classification from Wazuh | Internal classification |
|---|---|
| pvedaemon | virtualization_management |
| pam | authentication |
| sshd | remote_access |
| useradd | account_management |
| open-userdel | account_management |

`rule.groups` has multiple values, so we classify only by allowed groups and do not let unknown values flow into the internal classification as is.

# Chapter 5: Preparing Before the Change

## 5.1 Tests and Version Control

> **Run on: VM 230**

```bash
echo "===== AI DEFENSE MANAGER TEST INVENTORY ====="

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager")

test_dirs = [
    root / "tests",
    root / "app" / "tests",
]

found = set()

for directory in test_dirs:
    if not directory.is_dir():
        continue

    for path in sorted(directory.rglob("test_*.py")):
        found.add(path)

for path in sorted(found):
    print(f"\nTEST_FILE={path.relative_to(root)}")

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"PARSE_ERROR={type(exc).__name__}")
        continue

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                print(f"  TEST={node.name}")

                names = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Name):
                        names.add(child.id)
                    elif isinstance(child, ast.Attribute):
                        names.add(child.attr)

                relevant = sorted(
                    name for name in names
                    if any(term in name.lower() for term in (
                        "wazuh", "severity", "category", "analysis",
                        "event", "sanitize", "proposal", "payload",
                        "uuid", "ollama"
                    ))
                )
                if relevant:
                    print("    REFERENCES=" + ",".join(relevant))

print(f"\nTEST_FILE_COUNT={len(found)}")
print("TESTS_EXECUTED=NO")
print("SOURCE_CODE_DISPLAYED=NO")
print("DATABASE_ACCESSED=NO")
print("FILES_MODIFIED=NO")
PY

echo
echo "===== PROJECT VERSION CONTROL STATUS ====="
if git -C /opt/ai-defense-manager rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git -C /opt/ai-defense-manager status --short
else
    echo "GIT_REPOSITORY=NO"
fi
```

There were no test files and no Git repository. When the code is changed, it can neither be reverted with Git nor protected by existing tests. So our policy is to prepare the following new tests.

| Test | What it checks |
|---|---|
| Input allowlist | nothing beyond the seven fields is mixed in |
| Required fields | missing values, wrong types and invalid values are rejected |
| Removing secrets | `full_log`, `data`, IPs, user names and so on are not sent to the AI |
| Severity mapping | the boundaries of 0–16 |
| Classification mapping | the current five classifications and unknown classifications |
| UUID | correspondence between event IDs and evidence IDs |
| What is sent to the AI | inspect the JSON to be sent without actually communicating |
| Action safety | keep the 900-second TTL limit and the approval requirement |

## 5.2 Free Space and Target Files

> **Run on: VM 230**

```bash
echo "===== PRE-IMPLEMENTATION SAFETY INVENTORY ====="

echo "--- Project filesystem ---"
df -h /opt/ai-defense-manager /var/backups

echo
echo "--- Target file metadata ---"
for f in \
  /opt/ai-defense-manager/app/services/wazuh_relay.py \
  /opt/ai-defense-manager/app/services/event_sanitizer.py \
  /opt/ai-defense-manager/app/services/ai_analysis.py \
  /opt/ai-defense-manager/app/schemas/security_event.py \
  /opt/ai-defense-manager/app/api/wazuh.py
do
  if [ -f "$f" ]; then
    stat -c 'FILE=%n SIZE=%s MODE=%a OWNER=%U:%G MTIME=%y' "$f"
    sha256sum "$f"
  else
    echo "MISSING=$f"
  fi
done

echo
echo "--- Existing backup directories ---"
for d in /var/backups/ai-defense-manager /opt/ai-defense-manager/backups; do
  if [ -d "$d" ]; then
    stat -c 'DIRECTORY=%n MODE=%a OWNER=%U:%G' "$d"
  else
    echo "NOT_FOUND=$d"
  fi
done

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service
```

| Item | Result |
|---|---|
| Free space on VM 230 | about 39GB |
| Target files | 5 |
| SHA256 | taken for all 5 |
| Dedicated backup directory | not yet present |
| AI Defense Manager | `active` |
| Git | none |

# Closing Notes

In Part 47 we examined the existing implementation of the AI Defense Manager on VM 230.

| Item | Result |
|---|---|
| API | FastAPI/Uvicorn, `127.0.0.1:8000` only; APIs for Wazuh retrieval and analysis exist |
| Where the allowlist goes | `_convert_alert()` in `services/wazuh_relay.py` (right after retrieval) and right before sending to the AI in `services/ai_analysis.py` |
| Kept | the masking, `uuid4` event IDs, the severity mapping, the 900-second TTL, human approval |
| Preparation | no tests or Git, so take a backup before changing and check with independent tests |

In the next part, Part 48, we take a backup before the change, narrow the Wazuh event conversion to seven fields, and test it with synthetic data.

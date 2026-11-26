---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 53: Checking the Flow from Analysis to Storage"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 53 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 52, VM 230 became able to receive real Wazuh alerts. Before moving on to LLM analysis, we check, read-only, how received alerts lead to analysis, storage and defense proposals inside VM 230.

1. Trace the processing from event conversion to AI analysis
2. Check the path from the API to storage and defensive action proposals, external exposure and DB permissions
3. Check systemd isolation settings
4. Test the masking step with synthetic data
5. Check the safety of where LLM output is stored and returned

No refetching of real alerts, no DB access, no Ollama inference, no configuration changes and no service restarts.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: The Processing Flow

## 1.1 Functions and Call Relationships

> **Run on: VM 230**

```bash
echo "===== VM230: EVENT PIPELINE STATIC AUDIT ====="

cd /opt/ai-defense-manager

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")
targets = [
    "services/wazuh_relay.py",
    "services/event_sanitizer.py",
    "services/event_service.py",
    "services/ai_analysis.py",
    "schemas/security_event.py",
    "schemas/action.py",
]

keywords = (
    "alert", "event", "sanitize", "normal", "valid", "analy",
    "process", "save", "insert", "persist", "transform",
    "schema", "model", "proposal", "action"
)

for relative in targets:
    path = root / relative
    print(f"\n--- {relative} ---")
    if not path.is_file():
        print("FILE=NOT_FOUND")
        continue

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print("AST_PARSE=FAILED", type(exc).__name__)
        continue

    print("AST_PARSE=PASS")

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [arg.arg for arg in node.args.args]
            print(
                f"FUNCTION line={node.lineno} "
                f"name={node.name} args={args}"
            )
        elif isinstance(node, ast.ClassDef):
            print(f"CLASS line={node.lineno} name={node.name}")
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [arg.arg for arg in child.args.args]
                    print(
                        f"  METHOD line={child.lineno} "
                        f"name={child.name} args={args}"
                    )

    print("RELEVANT_CALLS:")
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            else:
                continue
            if any(word in name.lower() for word in keywords):
                print(f"  line={node.lineno} call={name}")

print("\n--- Service and schema file inventory ---")
for folder in (root / "services", root / "schemas"):
    if folder.is_dir():
        print(f"[{folder.name}]")
        for path in sorted(folder.glob("*.py")):
            print(path.name)

print("\nSOURCE_MODIFIED=NO")
print("DATABASE_REQUESTED=NO")
print("OLLAMA_REQUESTED=NO")
print("LIVE_ALERTS_REQUESTED=NO")
PY
```

There was no separate `event_service.py`; processing happened mainly in two stages.

1. `_convert_alert()` in `wazuh_relay.py` converts received alerts into `SecurityEvent`
2. `analyze_events()` in `ai_analysis.py` builds the content used for analysis and validates the model's output against the schema

## 1.2 Reading the Implementation

> **Run on: VM 230**

```bash
echo "===== VM230: EVENT PIPELINE IMPLEMENTATION REVIEW ====="

cd /opt/ai-defense-manager

echo
echo "--- Wazuh Relay: conversion and fetch ---"
nl -ba app/services/wazuh_relay.py | sed -n '1,190p'

echo
echo "--- Event sanitizer ---"
nl -ba app/services/event_sanitizer.py | sed -n '1,180p'

echo
echo "--- AI analysis: payload and analysis flow ---"
nl -ba app/services/ai_analysis.py | sed -n '1,190p'

echo
echo "--- Security event schema ---"
nl -ba app/schemas/security_event.py | sed -n '1,150p'

echo
echo "--- Analysis schema ---"
nl -ba app/schemas/analysis.py | sed -n '1,200p'

echo
echo "--- Analysis proposal schema ---"
nl -ba app/schemas/analysis_proposal.py | sed -n '1,200p'

echo
echo "--- Analysis history service ---"
nl -ba app/services/analysis_history.py | sed -n '1,200p'

echo
echo "SOURCE_MODIFIED=NO"
echo "DATABASE_REQUESTED=NO"
echo "OLLAMA_REQUESTED=NO"
echo "LIVE_ALERTS_REQUESTED=NO"
```

- `SecurityEvent` is built from Wazuh's seven fields; fields not allowed are rejected by `extra="forbid"`
- What is passed to the AI is only six explicitly chosen fields
- Event summaries are masked before being sent to the AI and before being stored in history
- AI proposals are validated with Pydantic, including that the evidence event IDs are among the inputs
- A proposal for temporary blocking requires a global IP, a TTL of 1–900 seconds and two separate pieces of evidence

# Chapter 2: APIs, Storage and Exposure

## 2.1 From the API to Analysis and Storage

> **Run on: VM 230**

```bash
echo "===== VM230: API TO ANALYSIS AND ACTION FLOW AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- API/router file inventory ---"
find app -maxdepth 4 -type f -name '*.py' -print | sort

echo
echo "--- Route decorators and relevant service calls ---"
python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")
keywords = (
    "fetch_wazuh_events",
    "analyze_events",
    "save_analysis",
    "initialize_database",
    "action",
    "approval",
    "execute",
    "gateway",
    "rollback",
)

for path in sorted(root.rglob("*.py")):
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception:
        continue

    matches = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            calls = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    func = child.func
                    name = (
                        func.id if isinstance(func, ast.Name)
                        else func.attr if isinstance(func, ast.Attribute)
                        else ""
                    )
                    if any(k in name.lower() for k in keywords):
                        calls.append(name)
            decorators = []
            for dec in node.decorator_list:
                try:
                    decorators.append(ast.unparse(dec))
                except Exception:
                    pass
            if calls or decorators:
                matches.append((
                    node.lineno, node.name, decorators, sorted(set(calls))
                ))

    if matches:
        print(f"\n--- {path.relative_to(root)} ---")
        for line, name, decorators, calls in matches:
            print(f"line={line} function={name}")
            for dec in decorators:
                print(f"  ROUTE_OR_DECORATOR={dec}")
            if calls:
                print(f"  RELEVANT_CALLS={calls}")

print("\nSOURCE_MODIFIED=NO")
print("DATABASE_REQUESTED=NO")
print("OLLAMA_REQUESTED=NO")
print("LIVE_ALERTS_REQUESTED=NO")
PY

echo
echo "--- Analysis history: remaining save logic ---"
nl -ba app/services/analysis_history.py | sed -n '185,360p'

echo
echo "--- Main application entrypoint ---"
if [ -f app/main.py ]; then
    nl -ba app/main.py | sed -n '1,240p'
else
    echo "app/main.py not found"
fi

echo
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

| API | Processing |
|---|---|
| `/api/v1/wazuh/events` | only fetches Wazuh events |
| `/api/v1/wazuh/analyze` | passes fetched events to AI analysis |
| `/api/v1/analysis` | analyzes received events directly with the AI |

The DB is initialized when the application starts. `save_analysis()` stores the analysis results, evidence, action proposals, approval records and audit logs.

## 2.2 Routes and the Boundary of Action Execution

> **Run on: VM 230**

```bash
echo "===== VM230: API ROUTE AND ACTION EXECUTION BOUNDARY AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- Wazuh API routes ---"
nl -ba app/api/wazuh.py | sed -n '1,240p'

echo
echo "--- Analysis API routes ---"
nl -ba app/api/analysis.py | sed -n '1,240p'

echo
echo "--- Action schema ---"
nl -ba app/schemas/action.py | sed -n '1,180p'

echo
echo "--- All references to history persistence ---"
grep -RInE 'save_analysis|initialize_database' app \
  --include='*.py' || true

echo
echo "--- Action execution / gateway references ---"
grep -RInEi 'execute_action|action_gateway|firewall|iptables|nft|block_ip|rollback|approve|approval' app \
  --include='*.py' || true

echo
echo "--- API route registration and middleware ---"
grep -RInE 'include_router|add_middleware|Depends\(|APIKey|HTTPBearer|OAuth2|CORSMiddleware' app \
  --include='*.py' || true

echo
echo "SOURCE_MODIFIED=NO"
echo "DATABASE_REQUESTED=NO"
echo "OLLAMA_REQUESTED=NO"
echo "LIVE_ALERTS_REQUESTED=NO"
```

Both analysis APIs called `save_analysis()`. On the other hand, we found the following two things.

1. **API authentication**: FastAPI routes have no authentication dependencies or middleware
2. **Action execution**: it goes only as far as recording approval state in the DB; there is no Action Gateway, no approval API and no firewall operation

## 2.3 External Exposure and DB Permissions

> **Run on: VM 230**

```bash
echo "===== VM230: API EXPOSURE AND DATABASE PERMISSION AUDIT ====="

echo
echo "--- API listener ---"
ss -lntp '( sport = :8000 )'

echo
echo "--- AI Defense Manager process ---"
systemctl show ai-defense-manager.service \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p User \
  -p Group

PID="$(systemctl show ai-defense-manager.service -p MainPID --value)"

if [ -n "$PID" ] && [ "$PID" != "0" ]; then
    echo
    echo "--- Process identity ---"
    ps -p "$PID" -o pid,ppid,user,group,stat,comm
fi

echo
echo "--- Database file metadata only ---"
if [ -e /opt/ai-defense-manager/data/ai-defense.db ]; then
    stat -c 'type=%F owner=%U:%G mode=%a size=%s' \
      /opt/ai-defense-manager/data/ai-defense.db
else
    echo "DATABASE_FILE=NOT_FOUND"
fi

if [ -d /opt/ai-defense-manager/data ]; then
    stat -c 'directory_owner=%U:%G directory_mode=%a' \
      /opt/ai-defense-manager/data
fi

echo
echo "DATABASE_CONTENT_READ=NO"
echo "DATABASE_MODIFIED=NO"
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
echo "OLLAMA_REQUESTED=NO"
```

| Item | Result |
|---|---|
| API listening | `127.0.0.1:8000` only (not exposed on the LAN) |
| Running as | dedicated user `ai-defense` |
| SQLite DB | `ai-defense:ai-defense`, `600` |
| DB directory | `750` |

The lack of API authentication remains. Even with localhost only, other processes on the same VM can access it, so authentication must be considered before integrating with other systems (done from Part 56 onward).

## 2.4 Approval State and Storage

> **Run on: VM 230**

```bash
echo "===== VM230: APPROVAL STATE AND PERSISTENCE CONSISTENCY AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- Analysis proposal schema ---"
nl -ba app/schemas/analysis_proposal.py | sed -n '1,180p'

echo
echo "--- Database schema and save logic ---"
nl -ba app/services/analysis_history.py | sed -n '1,245p'

echo
echo "--- Action schema references ---"
grep -RInE 'ActionProposal|ApprovalStatus|requires_human_approval|proposal_status|approval_decision' app \
  --include='*.py' || true

echo
echo "SOURCE_MODIFIED=NO"
echo "DATABASE_READ=NO"
echo "DATABASE_MODIFIED=NO"
echo "OLLAMA_REQUESTED=NO"
echo "LIVE_ALERTS_REQUESTED=NO"
```

Analysis results are stored inside a transaction, and there was no API for executing actions or firewall operation in the code.

# Chapter 3: Isolation by systemd

> **Run on: VM 230**

```bash
echo "===== VM230: SERVICE SANDBOX AND CONFIGURATION AUDIT ====="

echo
echo "--- Service security properties ---"
systemctl show ai-defense-manager.service \
  -p User -p Group -p NoNewPrivileges \
  -p PrivateTmp -p PrivateDevices \
  -p ProtectSystem -p ProtectHome \
  -p ReadWritePaths -p ReadOnlyPaths \
  -p RestrictAddressFamilies \
  -p CapabilityBoundingSet \
  -p AmbientCapabilities \
  -p SystemCallFilter \
  -p ProtectKernelTunables \
  -p ProtectKernelModules \
  -p ProtectControlGroups

echo
echo "--- Unit file (environment values redacted) ---"
UNIT="$(systemctl show ai-defense-manager.service -p FragmentPath --value)"
if [ -n "$UNIT" ] && [ -f "$UNIT" ]; then
    sed -E \
      -e '/^[[:space:]]*Environment=/s/=.*/=<REDACTED>/' \
      -e '/^[[:space:]]*EnvironmentFile=/s/=.*/=<REDACTED>/' \
      "$UNIT"
else
    echo "UNIT_FILE_NOT_FOUND"
fi

echo
echo "--- Configuration declarations (values redacted) ---"
grep -nE '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*:' \
  /opt/ai-defense-manager/app/core/config.py |
  sed -E 's/(:|=).*/\1 <VALUE_REDACTED>/'

echo
echo "--- Sensitive output guard ---"
echo "CREDENTIAL_VALUES=NOT_DISPLAYED"
echo "ENVIRONMENT_VALUES=NOT_DISPLAYED"
echo "CONFIGURATION_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "DATABASE_READ=NO"
echo "OLLAMA_REQUESTED=NO"
```

| Setting | State |
|---|---|
| `ProtectSystem=strict`, `ProtectHome=yes` | present |
| Writable locations | only the DB's `/opt/ai-defense-manager/data` |
| Linux capabilities | empty |
| `NoNewPrivileges=yes` | present |
| `PrivateTmp`, `PrivateDevices`, `ProtectProc=invisible` | present |
| Memory and task limits | 1GiB, 64 |
| `RestrictAddressFamilies` | `AF_INET` (IPv4 only) |

The AI Defense Manager has no root privileges and no network administration capability. With only `AF_INET`, IPv6 sockets cannot be used, but the current connections to the Relay and Ollama are IPv4.

# Chapter 4: Testing the Masking Step

## 4.1 Checking Input and Output Safety

> **Run on: VM 230**

```bash
echo "===== VM230: LLM OUTPUT AND DATA FLOW SAFETY AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- AI analysis service ---"
nl -ba app/services/ai_analysis.py | sed -n '1,300p'

echo
echo "--- Event sanitizer ---"
nl -ba app/services/event_sanitizer.py | sed -n '1,240p'

echo
echo "--- Analysis request schema ---"
nl -ba app/schemas/analysis.py | sed -n '1,220p'

echo
echo "--- Security event schema ---"
nl -ba app/schemas/security_event.py | sed -n '1,220p'

echo
echo "--- Sanitizer call sites ---"
grep -RInE 'sanitize_event_summary|sanitize.*summary|sanitize.*reasoning|sanitize.*proposal' \
  app --include='*.py' || true

echo
echo "SOURCE_MODIFIED=NO"
echo "DATABASE_READ=NO"
echo "DATABASE_MODIFIED=NO"
echo "OLLAMA_REQUESTED=NO"
echo "LIVE_ALERTS_REQUESTED=NO"
```

The event input side was as follows.

- Event summaries are masked before being sent to the LLM (Bearer tokens, common secrets, email addresses, IP addresses)
- What is passed to the LLM is built from an allowlist
- IPs and agent names of Wazuh events are not sent to the LLM
- The LLM's answer is validated with JSON Schema and Pydantic

On the other hand, we found that the LLM output side needs measures (Chapter 5).

## 4.2 Model and Settings

> **Run on: VM 230**

```bash
echo "===== VM230: SANITIZER AND MODEL CONFIGURATION STATIC AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- Configuration source (secret values masked) ---"
sed -E \
  -e 's/(password|token|secret|api[_-]?key)([[:space:]]*:[[:space:]]*).*/\1\2<REDACTED>/I' \
  -e 's/(password|token|secret|api[_-]?key)([[:space:]]*=[[:space:]]*).*/\1\2<REDACTED>/I' \
  app/core/config.py

echo
echo "--- Model and Ollama configuration references ---"
grep -RInE 'MODEL_NAME|ollama_base_url|analysis_timeout_seconds|OLLAMA_MODEL|qwen3:8b' \
  app /etc/systemd/system/ai-defense-manager.service \
  --include='*.py' --include='*.service' 2>/dev/null |
  sed -E 's/(token|password|secret|api[_-]?key)([^,; ]*)/REDACTED/Ig'

echo
echo "--- Existing sanitizer tests ---"
find . -maxdepth 4 -type f \
  \( -iname '*sanitiz*test*.py' -o -iname 'test*sanitiz*.py' \) \
  -print

echo
echo "--- Test framework configuration ---"
grep -nE 'pytest|testpaths|python_files|ruff|mypy' \
  pyproject.toml pytest.ini setup.cfg tox.ini 2>/dev/null || true

echo
echo "SOURCE_MODIFIED=NO"
echo "TESTS_EXECUTED=NO"
echo "DATABASE_READ=NO"
echo "OLLAMA_REQUESTED=NO"
```

The model name is written in `ai_analysis.py` as `qwen3:8b`, and there was no setting for it in `config.py`. Ollama's endpoint is `192.168.0.180:11434`. We do not change these here.

## 4.3 Testing with Synthetic Data (14 Cases)

Without changing the production code, we test with synthetic data the masking of secrets, email and IPv4/IPv6, control characters, the 512-character limit, and that ordinary text remains.

> **Run on: VM 230**

```bash
echo "===== VM230: EVENT SANITIZER SYNTHETIC TEST ====="

cd /opt/ai-defense-manager

venv/bin/python - <<'PY'
from app.services.event_sanitizer import sanitize_event_summary

tests = [
    ("bearer_token", "Authorization Bearer abc.def-123"),
    ("password_assignment", "password=hunter2"),
    ("api_key_assignment", "api_key: secret-value"),
    ("aws_key", "AKIA1234567890ABCDEF"),
    ("github_key", "ghp_" + "A" * 30),
    ("openai_key", "sk-" + "B" * 30),
    ("email", "contact user@example.com"),
    ("ipv4", "connection from 203.0.113.10"),
    ("ipv6", "connection from 2001:db8::1"),
    ("control_chars", "alpha\x00beta\ncharlie"),
    ("length_limit", "A" * 600),
    ("empty_string", ""),
    ("non_string", None),
    ("normal_text", "Wazuh authentication failure detected"),
]

checks = {}

for name, value in tests:
    try:
        result = sanitize_event_summary(value)

        if name in {
            "bearer_token", "password_assignment", "api_key_assignment",
            "aws_key", "github_key", "openai_key"
        }:
            passed = "[REDACTED_SECRET]" in result

        elif name == "email":
            passed = "[REDACTED_EMAIL]" in result

        elif name in {"ipv4", "ipv6"}:
            passed = "[REDACTED_IP]" in result

        elif name == "control_chars":
            passed = "\x00" not in result and "\n" not in result

        elif name == "length_limit":
            passed = len(result) <= 512

        elif name in {"empty_string", "non_string"}:
            passed = result == "[REDACTED_EVENT]"

        elif name == "normal_text":
            passed = result == value

        else:
            passed = False

        checks[name] = passed
        print(f"{name}={'PASS' if passed else 'FAIL'}")

    except Exception as exc:
        checks[name] = False
        print(f"{name}=ERROR ({type(exc).__name__})")

print()
print(f"TESTS_TOTAL={len(checks)}")
print(f"TESTS_PASSED={sum(checks.values())}")
print(f"TESTS_FAILED={len(checks) - sum(checks.values())}")
print("TEST_INPUT_VALUES_DISPLAYED=NO")
print("DATABASE_ACCESSED=NO")
print("OLLAMA_ACCESSED=NO")
PY

echo
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

All 14 passed.

## 4.4 Do the Original Values Remain? (10 Cases)

> **Run on: VM 230**

```bash
echo "===== VM230: SANITIZER REDACTION COMPLETENESS TEST ====="

cd /opt/ai-defense-manager

venv/bin/python - <<'PY'
from app.services.event_sanitizer import sanitize_event_summary

cases = [
    ("bearer", "Bearer abc.def-123", "abc.def-123"),
    ("password", "password=hunter2", "hunter2"),
    ("quoted_secret", 'secret: "quoted-secret-value"', "quoted-secret-value"),
    ("api_key", "api_key=synthetic-api-key-123", "synthetic-api-key-123"),
    ("aws_key", "AKIA1234567890ABCDEF", "AKIA1234567890ABCDEF"),
    ("github_key", "ghp_" + "A" * 30, "ghp_" + "A" * 30),
    ("openai_key", "sk-" + "B" * 30, "sk-" + "B" * 30),
    ("email", "user@example.com", "user@example.com"),
    ("ipv4", "203.0.113.10", "203.0.113.10"),
    ("ipv6", "2001:db8::1", "2001:db8::1"),
]

failed = []

for name, source, secret in cases:
    result = sanitize_event_summary(source)
    marker = (
        "[REDACTED_SECRET]" if name in {
            "bearer", "password", "quoted_secret", "api_key",
            "aws_key", "github_key", "openai_key"
        }
        else "[REDACTED_EMAIL]" if name == "email"
        else "[REDACTED_IP]"
    )

    marker_present = marker in result
    original_absent = secret not in result
    passed = marker_present and original_absent

    print(
        f"{name}={'PASS' if passed else 'FAIL'} "
        f"marker={marker_present} original_absent={original_absent}"
    )

    if not passed:
        failed.append(name)

print()
print(f"TESTS_TOTAL={len(cases)}")
print(f"TESTS_FAILED={len(failed)}")
print(f"FAILED_CASE_NAMES={failed}")
print("SECRET_VALUES_DISPLAYED=NO")
print("DATABASE_ACCESSED=NO")
print("OLLAMA_ACCESSED=NO")
PY

echo
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

All 10 passed; we confirmed that mask markers appear and the original secrets do not remain. It only works on known patterns, so it cannot necessarily remove secrets in unknown forms.

# Chapter 5: Checking the LLM Output

## 5.1 Processing Just Before Storage

> **Run on: VM 230**

```bash
echo "===== VM230: LLM OUTPUT TRUST-BOUNDARY AUDIT ====="

cd /opt/ai-defense-manager

venv/bin/python - <<'PY'
import ast
from pathlib import Path

targets = {
    "app/services/ai_analysis.py": {
        "analyze_events",
        "_build_event_payload",
    },
    "app/services/analysis_history.py": {
        "save_analysis",
    },
    "app/schemas/analysis_proposal.py": {
        "AIAnalysisProposal",
        "validate_action_constraints",
    },
}

for filename, wanted in targets.items():
    path = Path(filename)
    print(f"\n--- {filename} ---")

    if not path.is_file():
        print("FILE_NOT_FOUND")
        continue

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    found = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in wanted:
                found.add(node.name)
                print(f"\n### {node.name} (line {node.lineno})")
                print(ast.get_source_segment(source, node))

    missing = wanted - found
    if missing:
        print("NOT_FOUND:", sorted(missing))

print("\n--- OUTPUT SANITIZER REFERENCES ---")
for filename in [
    "app/services/ai_analysis.py",
    "app/services/analysis_history.py",
    "app/routers/analysis.py",
]:
    path = Path(filename)
    if not path.is_file():
        continue

    for number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if any(word in line.lower() for word in (
            "sanitize", "model_validate", "model_dump",
            "summary", "reasoning", "save_analysis"
        )):
            print(f"{filename}:{number}: {line.strip()[:240]}")

PY

echo
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

Two problems were found.

1. **LLM output is stored as is**: `proposal.summary` and `proposal.reasoning` are stored in SQLite without masking, even if they contain secrets
2. **The LLM can decide whether approval is required**: for proposals other than IP blocking, `requires_human_approval=false` passes, and the storage step uses that value

There is currently neither an Action Gateway nor an execution function, so this does not immediately lead to firewall operations.

## 5.2 API Return Values and Approval

> **Run on: VM 230**

```bash
echo "===== VM230: API RESPONSE AND APPROVAL FLOW AUDIT ====="

cd /opt/ai-defense-manager

venv/bin/python - <<'PY'
import ast
from pathlib import Path

root = Path("app")

for path in sorted((root / "routers").glob("*.py")):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    print(f"\n--- {path} ---")

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            segment = ast.get_source_segment(source, node) or ""
            if any(term in segment.lower() for term in (
                "analyze_events",
                "save_analysis",
                "proposal",
                "approval",
                "analysis_history",
                "summary",
                "reasoning",
            )):
                print(f"\n### {node.name} (line {node.lineno})")
                print(segment)

print("\n--- ROUTE AND APPROVAL REFERENCES ---")

for path in sorted(root.rglob("*.py")):
    if "__pycache__" in str(path):
        continue

    for number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        lower = line.lower()
        if any(term in lower for term in (
            "include_router",
            "approval",
            "action_proposals",
            "analysis_runs",
            "get_analysis",
            "list_analysis",
        )):
            print(f"{path}:{number}: {line.strip()[:220]}")

PY

echo
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

```bash
echo "===== VM230: ROUTER FILE AND ENDPOINT INVENTORY ====="

cd /opt/ai-defense-manager

echo
echo "--- Router-related files ---"
find app -maxdepth 4 -type f \
  \( -name '*router*.py' -o -name '*route*.py' -o -name 'api.py' \) \
  -print | sort

echo
echo "--- Router registrations ---"
sed -n '1,180p' app/main.py

echo
echo "--- FastAPI endpoint decorators and handler definitions ---"
grep -RInE \
  '^[[:space:]]*@.*\.(get|post|put|patch|delete)|^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+' \
  app/routers app/api app 2>/dev/null \
  | grep -v '__pycache__' \
  | head -200

echo
echo "--- Router directory listing ---"
ls -la app/routers app/api 2>/dev/null

echo
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

The routers were actually in `app/api/analysis.py` and `app/api/wazuh.py`.

## 5.3 Handler Bodies

> **Run on: VM 230**

```bash
echo "===== VM230: ANALYSIS API HANDLER AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- app/api/analysis.py ---"
nl -ba app/api/analysis.py

echo
echo "--- app/api/wazuh.py ---"
nl -ba app/api/wazuh.py

echo
echo "--- API route configuration ---"
grep -RInE \
  'APIRouter|prefix=|response_model=|status_code=|dependencies=|include_in_schema' \
  app/api app/main.py

echo
echo "--- Authentication and authorization references ---"
grep -RInE \
  'HTTPBearer|OAuth2|APIKey|Depends\(|Security\(|authenticate|authorize|middleware|permission' \
  app --include='*.py' \
  | grep -v '__pycache__' || true

echo
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

- `/api/v1/analysis`: stores the LLM's proposal and then returns it as is
- `/api/v1/wazuh/analyze`: fetches Wazuh events, analyzes them with the LLM, stores, and returns the same proposal
- Both have `response_model=AIAnalysisProposal`, but that schema only checks lengths and types and does not remove secrets

So the proposal must be masked **right after receiving the LLM's answer**, not just right before storage.

## 5.4 Checks to Decide the Fix

> **Run on: VM 230**

```bash
echo "===== VM230: SANITIZER AND ACTION POLICY DESIGN AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- Existing sanitizer ---"
nl -ba app/services/event_sanitizer.py

echo
echo "--- Recommended action definitions ---"
nl -ba app/schemas/analysis_proposal.py

echo
echo "--- Action schema and validation ---"
nl -ba app/schemas/action.py

echo
echo "--- Sanitizer usage throughout application ---"
grep -RInE \
  'sanitize_event_summary|RecommendedAction|requires_human_approval' \
  app --include='*.py' \
  | grep -v '__pycache__'

echo
echo "--- Test tooling inventory ---"
find . -maxdepth 3 -type f \
  \( -name 'pytest.ini' -o -name 'pyproject.toml' \
     -o -name 'conftest.py' -o -name 'test_*.py' \
     -o -name '*_test.py' \) \
  -print | sort

echo
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Problem | Details |
|---|---|
| Masking of LLM output | `summary` (up to 2,000 characters) and `reasoning` (up to 4,000 characters) are stored and returned unmasked. The current masking is for event input and truncates to 512 characters, so it cannot be used as is |
| Whether approval is required | the LLM can return `requires_human_approval=false` |

With the policy that the LLM is limited to analysis and the AI Defense Manager side guarantees output safety and approval decisions, we fix this in the next part, Part 54.

# Closing Notes

In Part 53 we checked the flow from analysis to storage inside VM 230.

| Item | Result |
|---|---|
| Input | narrowed to seven fields, unknown fields rejected; summaries masked; six fields sent to the AI |
| Exposure | `127.0.0.1:8000` only; DB is `600` |
| Isolation | systemd restricts writable locations, capabilities, memory and more |
| Masking tests | all 14 and 10 cases passed |
| Problems found | LLM output stored and returned unmasked; the LLM can decide whether approval is required; the API has no authentication |
| Action execution | no such function (only storing proposals) |

In the next part, Part 54, we fix the masking of LLM output and the approval policy.

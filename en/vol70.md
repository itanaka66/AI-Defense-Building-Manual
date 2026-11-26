---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 70: Starting to Build the AI Defense Agents"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 70 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". By Part 69 we had put in order the Wazuh defense foundation and the protection of the AI Defense Manager's (VM 230) input, output, authentication and logs. From here, we build **AI defense agents** on top of it.

In this part we build the first two agents.

| Agent | Role |
|---|---|
| `LogAnalysisAgent` | log analysis. A thin, read-only layer that delegates to the existing AI analysis (`analyze_events()`) |
| `ThreatAnalysisAgent` | threat analysis and evidence validation. Independently checks the log analysis result for duplicate, missing or inconsistent evidence event IDs relative to the input |

The principles decided are as follows.

1. Agents only read and analyze; they do not execute defensive actions
2. Even if they can propose `TEMPORARY_BLOCK_IP`, they do not actually block. Defensive actions follow the existing `ActionProposal` constraints (approval required, start in `PENDING`)
3. Existing APIs, DB, settings and services are not changed. Tests use simulated analysis and make no communication with Ollama or DB access
4. Existing files are not overwritten

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root. When logged in as `aidefense`, become root with `sudo -i`)

# Chapter 1: Examining the Existing Structure

## 1.1 Service and Application

> **Run on: VM 230**

```bash
set -uo pipefail

echo "===== VM230: AI DEFENSE AGENT BUILD PREFLIGHT ====="

echo
echo "--- 1. Host and account ---"
hostname
id

echo
echo "--- 2. Existing service state ---"
systemctl status ai-defense-manager.service --no-pager -l | head -35

echo
echo "--- 3. Service configuration metadata ---"
systemctl show ai-defense-manager.service \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p NRestarts \
  -p User \
  -p WorkingDirectory \
  -p FragmentPath

echo
echo "--- 4. Running application process ---"
PID="$(systemctl show ai-defense-manager.service -p MainPID --value)"
if [ "${PID:-0}" -gt 0 ] 2>/dev/null; then
  ps -p "$PID" -o pid=,user=,stat=,etime=,comm=
  printf 'PROCESS_CWD='
  readlink "/proc/$PID/cwd" || true
else
  echo "MAINPID_NOT_AVAILABLE"
fi

echo
echo "--- 5. Existing application directory candidates ---"
for d in /opt/ai-defense-manager /opt/ai-defense /home/aidefense/ai-defense-manager; do
  if [ -d "$d" ]; then
    ls -ld "$d"
    find "$d" -maxdepth 2 -type d \
      \( -name agents -o -name api -o -name core -o -name policies -o -name schemas -o -name services \) \
      -print 2>/dev/null
  fi
done

echo
echo "READ_ONLY_PREFLIGHT=YES"
echo "SERVICE_RESTARTED=NO"
echo "FILES_MODIFIED=NO"
```

The API runs on `127.0.0.1:8000` (Main PID `2340`, NRestarts 0), and the working directory is `/opt/ai-defense-manager`.

> **Run on: VM 230**

```bash
sudo -i

ROOT=/opt/ai-defense-manager

echo "===== VM230: ROOT-LEVEL APPLICATION SOURCE INVENTORY ====="

echo
echo "--- 1. Application directories ---"
find "$ROOT/app" "$ROOT/tests" -maxdepth 4 -type d -print | sort

echo
echo "--- 2. Python source files ---"
find "$ROOT/app" "$ROOT/tests" -maxdepth 5 -type f \
  \( -name '*.py' -o -name 'pyproject.toml' \) \
  -printf '%p\n' | sort

echo
echo "--- 3. Application source file metadata ---"
find "$ROOT/app" -maxdepth 4 -type f -name '*.py' \
  -printf '%M %u:%g %s bytes %p\n' | sort

echo
echo "--- 4. Test file metadata ---"
find "$ROOT/tests" -maxdepth 4 -type f \
  -printf '%M %u:%g %s bytes %p\n' | sort

echo
echo "--- 5. Dependency lock metadata ---"
stat -c '%A %U:%G %s bytes %n' "$ROOT/requirements.lock"

echo
echo "SOURCE_CONTENT_READ=NO"
echo "CONFIG_AND_DATABASE_READ=NO"
echo "FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

`/opt/ai-defense-manager/app` and `tests` are owned by root and cannot be read by `aidefense` (a structure that protects the application code). We keep this protection.

## 1.2 Source Listing and AI Analysis Structure

> **Run on: VM 230**

```bash
echo "===== VM230: PYTHON SOURCE FILE LIST ====="

find /opt/ai-defense-manager/app \
     /opt/ai-defense-manager/tests \
     -type f -name '*.py' -print | sort

echo
echo "FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

```bash
set -uo pipefail

ROOT=/opt/ai-defense-manager

echo "===== VM230: AI ANALYSIS ARCHITECTURE DISCOVERY ====="

echo
echo "--- 1. Existing package directories ---"
find "$ROOT/app" -maxdepth 3 -type d -print | sort

echo
echo "--- 2. API route and function declarations ---"
grep -nE '^[[:space:]]*@|^[[:space:]]*(async )?def |^[[:space:]]*class ' \
  "$ROOT/app/api/analysis.py" \
  "$ROOT/app/api/wazuh.py" \
  "$ROOT/app/main.py" || true

echo
echo "--- 3. Service function and class declarations ---"
grep -nE '^[[:space:]]*(async )?def |^[[:space:]]*class ' \
  "$ROOT/app/services/ai_analysis.py" \
  "$ROOT/app/services/event_sanitizer.py" \
  "$ROOT/app/services/wazuh_relay.py" \
  "$ROOT/app/services/analysis_history.py" || true

echo
echo "--- 4. Schema declarations ---"
grep -nE '^[[:space:]]*class ' \
  "$ROOT/app/schemas/"*.py || true

echo
echo "--- 5. Test file inventory ---"
find "$ROOT/tests" -maxdepth 5 -type f -printf '%P\n' | sort

echo
echo "SOURCE_CONTENT_DUMP=NO"
echo "SECRETS_READ=NO"
echo "FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Existing | Role |
|---|---|
| `app/services/ai_analysis.py` | AI analysis engine |
| `app/services/wazuh_relay.py` | fetching Wazuh events |
| `app/services/event_sanitizer.py` | masking events |
| `app/services/analysis_history.py` | storing analysis history |
| `app/agents`, `app/policies` | directories only, no Python files |

## 1.3 Input/Output Types and Validation

> **Run on: VM 230**

```bash
python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

targets = [
    "api/analysis.py",
    "api/wazuh.py",
    "services/ai_analysis.py",
    "services/wazuh_relay.py",
    "services/event_sanitizer.py",
    "services/analysis_history.py",
    "schemas/analysis.py",
    "schemas/security_event.py",
    "schemas/analysis_proposal.py",
]

print("===== VM230: EXISTING AI INTERFACE CONTRACTS =====")

for relative in targets:
    path = root / relative
    print(f"\n--- {relative} ---")

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"AST_READ_ERROR={type(exc).__name__}")
        continue

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [arg.arg for arg in node.args.args]
            print(f"FUNCTION {node.name}({', '.join(args)})")

        elif isinstance(node, ast.ClassDef):
            print(f"CLASS {node.name}")
            for child in node.body:
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    print(f"  FIELD {child.target.id}")
                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    print(f"  METHOD {child.name}")

print("\n--- Agent and policy files ---")
for directory in ("agents", "policies"):
    path = root / directory
    print(f"[{directory}]")
    if path.exists():
        for item in sorted(path.rglob("*")):
            if item.is_file() and "__pycache__" not in item.parts:
                print(item.relative_to(root))

print("\nREAD_ONLY_AST_INSPECTION=YES")
print("FILES_MODIFIED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

```bash
python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app/schemas")
targets = [
    "analysis.py",
    "security_event.py",
    "analysis_proposal.py",
    "action.py",
    "wazuh.py",
]

print("===== VM230: SCHEMA TYPES AND VALIDATION CONTRACTS =====")

for filename in targets:
    path = root / filename
    print(f"\n--- {filename} ---")

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"PARSE_ERROR={type(exc).__name__}")
        continue

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            print(f"\nCLASS {node.name}")

            for child in node.body:
                if isinstance(child, ast.AnnAssign):
                    name = child.target.id if isinstance(child.target, ast.Name) else "?"
                    annotation = ast.unparse(child.annotation)
                    default = "required" if child.value is None else "has_default"
                    print(f"  FIELD {name}: {annotation} [{default}]")

                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [arg.arg for arg in child.args.args]
                    print(f"  METHOD {child.name}({', '.join(args)})")

                elif isinstance(child, ast.Assign):
                    names = [
                        target.id for target in child.targets
                        if isinstance(target, ast.Name)
                    ]
                    if names:
                        print(f"  CLASS_CONSTANT {', '.join(names)}")

print("\nSCHEMA_CONTENT_SECRETS=NOT_REQUESTED")
print("DATABASE_CONTENT_READ=NO")
print("FILES_MODIFIED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

The first agents can use the existing `AIAnalysisRequest` and `AIAnalysisProposal` for input and output. `AIAnalysisProposal` has `confidence`, `evidence_event_ids`, `requires_human_approval` and others.

> **Run on: VM 230**

```bash
python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app/schemas")
targets = {
    "security_event.py": {"require_timezone", "validate_ip_address"},
    "analysis_proposal.py": {"validate_action_constraints"},
    "action.py": {"validate_action"},
}

print("===== VM230: SECURITY VALIDATOR IMPLEMENTATION =====")

for filename, wanted in targets.items():
    path = root / filename
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    tree = ast.parse(source)

    print(f"\n--- {filename} ---")
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in wanted:
            start = node.lineno
            end = node.end_lineno
            print(f"\n[{node.name}: lines {start}-{end}]")
            for number in range(start, end + 1):
                print(f"{number:4}: {lines[number - 1]}")

print("\nVALIDATOR_CODE_ONLY=YES")
print("DATABASE_CONTENT_READ=NO")
print("FILES_MODIFIED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

- An IP blocking proposal requires two or more separate evidence events
- Only global IPs can be blocking targets
- `target_ip` and `ttl_seconds` are required
- Human approval is required
- Execution proposals start in `PENDING`

## 1.4 The Flow of Model Queries

> **Run on: VM 230**

```bash
python3 - <<'PY'
import ast
from pathlib import Path

base = Path("/opt/ai-defense-manager/app")

targets = [
    "services/ai_analysis.py",
    "services/wazuh_relay.py",
    "services/event_sanitizer.py",
    "core/config.py",
    "api/analysis.py",
    "api/wazuh.py",
]

print("===== VM230: AI ENGINE DEPENDENCY MAP =====")

for relative in targets:
    path = base / relative
    tree = ast.parse(path.read_text(encoding="utf-8"))

    print(f"\n--- {relative} ---")

    for node in tree.body:
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
            print("IMPORT:", ", ".join(names))

        elif isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            print(f"FROM {node.module}: {', '.join(names)}")

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            calls = set()
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    func = child.func
                    if isinstance(func, ast.Name):
                        calls.add(func.id)
                    elif isinstance(func, ast.Attribute):
                        calls.add(func.attr)

            print(f"FUNCTION {node.name}")
            if calls:
                print("  CALLS:", ", ".join(sorted(calls)))

        elif isinstance(node, ast.ClassDef):
            print(f"CLASS {node.name}")
            for child in node.body:
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    print(f"  CONFIG_FIELD: {child.target.id}")
                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    print(f"  METHOD: {child.name}")

print("\nDEPENDENCY_NAMES_ONLY=YES")
print("CONFIG_VALUES_DISPLAYED=NO")
print("SECRETS_READ=NO")
print("DATABASE_CONTENT_READ=NO")
print("FILES_MODIFIED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

```bash
python3 - <<'PY'
import ast
from pathlib import Path

base = Path("/opt/ai-defense-manager/app")
targets = [
    ("services/ai_analysis.py", "_analyze_events_unlimited"),
    ("services/ai_analysis.py", "analyze_events"),
    ("api/analysis.py", "create_analysis"),
    ("api/wazuh.py", "analyze_wazuh_events"),
]

def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return dotted(node.value) + "." + node.attr
    return type(node).__name__

print("===== VM230: MODEL REQUEST AND RESPONSE FLOW =====")

for relative, function_name in targets:
    path = base / relative
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fn = next(
        (n for n in ast.walk(tree)
         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
         and n.name == function_name),
        None
    )

    print(f"\n--- {relative}:{function_name} ---")
    if fn is None:
        print("FUNCTION_NOT_FOUND")
        continue

    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            keywords = [kw.arg for kw in node.keywords if kw.arg]
            print(f"CALL {dotted(node.func)}"
                  + (f" | keyword_args={','.join(keywords)}" if keywords else ""))

        elif isinstance(node, ast.Dict):
            keys = []
            for key in node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    keys.append(key.value)
                else:
                    keys.append("<dynamic>")
            if keys:
                print("DICT_KEYS:", ", ".join(keys))

        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "settings":
                print("SETTING_REFERENCE:", node.attr)

        elif isinstance(node, ast.Compare):
            print("COMPARISON_OPERATOR:", ", ".join(type(op).__name__ for op in node.ops))

print("\nPROMPT_TEXT_DISPLAYED=NO")
print("URL_OR_SETTING_VALUES_DISPLAYED=NO")
print("SECRETS_READ=NO")
print("DATABASE_CONTENT_READ=NO")
print("FILES_MODIFIED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

Querying Ollama (`httpx.AsyncClient`), parsing the JSON answer and validating with `AIAnalysisProposal` are already done by `ai_analysis.py`. The first agent does not duplicate model calls; it uses the existing `analyze_events()`.

## 1.5 Test Environment

> **Run on: VM 230**

```bash
echo "===== VM230: AGENT IMPLEMENTATION TEST ENVIRONMENT ====="

ROOT=/opt/ai-defense-manager

echo
echo "--- 1. Python runtime ---"
"$ROOT/venv/bin/python" --version

echo
echo "--- 2. Test framework availability ---"
"$ROOT/venv/bin/python" - <<'PY'
from importlib.util import find_spec

for name in ("pytest", "pytest_asyncio", "httpx", "pydantic", "fastapi"):
    print(f"{name}: {'AVAILABLE' if find_spec(name) else 'NOT_INSTALLED'}")
PY

echo
echo "--- 3. Locked dependency names and versions ---"
sed -E 's/([A-Za-z0-9_.-]+)==([^ ;]+).*/\1==\2/; t; d' \
  "$ROOT/requirements.lock"

echo
echo "--- 4. Agent and policy directory metadata ---"
stat -c '%n | owner=%U:%G | mode=%a' \
  "$ROOT/app/agents" "$ROOT/app/policies" "$ROOT/tests"

echo
echo "FILES_MODIFIED=NO"
echo "DATABASE_CONTENT_READ=NO"
echo "SERVICE_RESTARTED=NO"
```

Python 3.12.3, Pydantic 2.14.4, FastAPI 0.165.0; there is no `pytest`, so we use the standard `unittest`.

# Chapter 2: The Log Analysis Agent

## 2.1 Building and Testing

We create only two new files, `app/agents/log_analysis.py` and `tests/test_log_analysis_agent.py`, after checking that they do not exist yet.

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
cd "$ROOT"

AGENT="$ROOT/app/agents/log_analysis.py"
TEST="$ROOT/tests/test_log_analysis_agent.py"

echo "===== VM230: CREATE AND TEST LOG ANALYSIS AGENT ====="

# Do not overwrite an existing file by mistake
if [ -e "$AGENT" ] || [ -e "$TEST" ]; then
    echo "ABORT: One or both target files already exist."
    exit 1
fi

umask 027

cat > "$AGENT" <<'PY'
"""Read-only log analysis agent.

This agent delegates analysis to the existing AI analysis service.
It does not execute or authorize defensive actions.
"""

from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal
from app.services.ai_analysis import analyze_events


class LogAnalysisAgent:
    """Analyze security events without performing operational actions."""

    async def analyze(
        self,
        request: AIAnalysisRequest,
    ) -> AIAnalysisProposal:
        """Return an analysis proposal from the existing analysis service."""
        return await analyze_events(request)
PY

cat > "$TEST" <<'PY'
import unittest
from unittest.mock import AsyncMock, patch

from app.agents.log_analysis import LogAnalysisAgent
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import (
    AIAnalysisProposal,
    RecommendedAction,
)
from app.services.ai_analysis import AIAnalysisError


class TestLogAnalysisAgent(unittest.IsolatedAsyncioTestCase):

    async def test_delegates_request_and_returns_proposal(self):
        request = AIAnalysisRequest()
        proposal = AIAnalysisProposal(
            recommended_action=RecommendedAction.NO_ACTION,
        )

        with patch(
            "app.agents.log_analysis.analyze_events",
            new_callable=AsyncMock,
            return_value=proposal,
        ) as mocked:
            result = await LogAnalysisAgent().analyze(request)

        mocked.assert_awaited_once_with(request)
        self.assertIs(result, proposal)

    async def test_propagates_analysis_error(self):
        request = AIAnalysisRequest()
        expected_error = AIAnalysisError("synthetic test failure")

        with patch(
            "app.agents.log_analysis.analyze_events",
            new_callable=AsyncMock,
            side_effect=expected_error,
        ):
            with self.assertRaises(AIAnalysisError) as raised:
                await LogAnalysisAgent().analyze(request)

        self.assertIs(raised.exception, expected_error)


if __name__ == "__main__":
    unittest.main()
PY

chown root:ai-defense "$AGENT"
chmod 0640 "$AGENT"
chown root:root "$TEST"
chmod 0640 "$TEST"

echo
echo "--- 1. Syntax validation ---"
"$ROOT/venv/bin/python" -m py_compile "$AGENT" "$TEST"
echo "PY_COMPILE=PASS"

echo
echo "--- 2. Isolated unit tests ---"
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
    discover -s "$ROOT/tests" \
    -p 'test_log_analysis_agent.py' \
    -v

echo
echo "--- 3. Created file metadata ---"
stat -c '%n | owner=%U:%G | mode=%a | size=%s' "$AGENT" "$TEST"

echo
echo "ONLY_APPROVED_FILES_CREATED=YES"
echo "EXISTING_FILES_MODIFIED=NO"
echo "DATABASE_CONTENT_READ=NO"
echo "OLLAMA_REQUEST_SENT=NO"
echo "SERVICE_RESTARTED=NO"
```

## 2.2 Fixing the Test Data

The test in 2.1 failed before the agent's processing because of mistakes in how the test data was built. Without changing the agent itself, we fix only the test file, in three steps.

1. Put one valid `SecurityEvent` into the required `events` of `AIAnalysisRequest`

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
TEST="$ROOT/tests/test_log_analysis_agent.py"

cat > "$TEST" <<'PY'
import unittest
from unittest.mock import AsyncMock, patch

from app.agents.log_analysis import LogAnalysisAgent
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import (
    AIAnalysisProposal,
    RecommendedAction,
)
from app.schemas.security_event import SecurityEvent
from app.services.ai_analysis import AIAnalysisError


def make_request():
    event = SecurityEvent(
        source="wazuh",
        severity="low",
        event_category="authentication",
        event_summary="Synthetic unit-test event",
    )
    return AIAnalysisRequest(events=[event])


class TestLogAnalysisAgent(unittest.IsolatedAsyncioTestCase):

    async def test_delegates_request_and_returns_proposal(self):
        request = make_request()
        proposal = AIAnalysisProposal(
            recommended_action=RecommendedAction.NO_ACTION,
        )

        with patch(
            "app.agents.log_analysis.analyze_events",
            new_callable=AsyncMock,
            return_value=proposal,
        ) as mocked:
            result = await LogAnalysisAgent().analyze(request)

        mocked.assert_awaited_once_with(request)
        self.assertIs(result, proposal)

    async def test_propagates_analysis_error(self):
        request = make_request()
        expected_error = AIAnalysisError("synthetic test failure")

        with patch(
            "app.agents.log_analysis.analyze_events",
            new_callable=AsyncMock,
            side_effect=expected_error,
        ):
            with self.assertRaises(AIAnalysisError) as raised:
                await LogAnalysisAgent().analyze(request)

        self.assertIs(raised.exception, expected_error)


if __name__ == "__main__":
    unittest.main()
PY

chown root:root "$TEST"
chmod 0640 "$TEST"

echo "===== VM230: LOG ANALYSIS AGENT TEST RETRY ====="

"$ROOT/venv/bin/python" -m py_compile \
    "$ROOT/app/agents/log_analysis.py" "$TEST"

PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
    discover -s "$ROOT/tests" \
    -p 'test_log_analysis_agent.py' \
    -v

echo
echo "AGENT_SOURCE_MODIFIED=NO"
echo "TEST_FILE_UPDATED=YES"
echo "DATABASE_CONTENT_READ=NO"
echo "OLLAMA_REQUEST_SENT=NO"
echo "SERVICE_RESTARTED=NO"
```

2. Fill in the required fields of `AIAnalysisProposal` (`summary`, `severity`, `confidence`, `evidence_event_ids`, `reasoning`)

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
TEST="$ROOT/tests/test_log_analysis_agent.py"

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Run this block as root."
    exit 1
fi

python3 - <<'PY'
from pathlib import Path

path = Path("/opt/ai-defense-manager/tests/test_log_analysis_agent.py")
source = path.read_text(encoding="utf-8")

old = '''        proposal = AIAnalysisProposal(
            recommended_action=RecommendedAction.NO_ACTION,
        )'''

new = '''        proposal = AIAnalysisProposal(
            summary="Synthetic test summary",
            severity="low",
            confidence=0.5,
            evidence_event_ids=[],
            recommended_action=RecommendedAction.NO_ACTION,
            reasoning="Synthetic unit-test reasoning",
        )'''

if source.count(old) != 1:
    raise SystemExit("ABORT: Expected test fixture was not found exactly once.")

path.write_text(source.replace(old, new), encoding="utf-8")
PY

chown root:root "$TEST"
chmod 0640 "$TEST"

echo "===== VM230: LOG ANALYSIS AGENT TEST RETRY 2 ====="

"$ROOT/venv/bin/python" -m py_compile \
    "$ROOT/app/agents/log_analysis.py" "$TEST"

PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
    discover -s "$ROOT/tests" \
    -p 'test_log_analysis_agent.py' \
    -v

echo
echo "AGENT_SOURCE_MODIFIED=NO"
echo "TEST_FIXTURE_UPDATED=YES"
echo "DATABASE_CONTENT_READ=NO"
echo "OLLAMA_REQUEST_SENT=NO"
echo "SERVICE_RESTARTED=NO"
```

3. `evidence_event_ids` requires at least one item, so use the test event's `event_id` as the evidence ID

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
TEST="$ROOT/tests/test_log_analysis_agent.py"

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Run as root."
    exit 1
fi

python3 - <<'PY'
from pathlib import Path

path = Path("/opt/ai-defense-manager/tests/test_log_analysis_agent.py")
source = path.read_text(encoding="utf-8")

old = '''        proposal = AIAnalysisProposal(
            summary="Synthetic test summary",
            severity="low",
            confidence=0.5,
            evidence_event_ids=[],
            recommended_action=RecommendedAction.NO_ACTION,
            reasoning="Synthetic unit-test reasoning",
        )'''

new = '''        proposal = AIAnalysisProposal(
            summary="Synthetic test summary",
            severity="low",
            confidence=0.5,
            evidence_event_ids=[request.events[0].event_id],
            recommended_action=RecommendedAction.NO_ACTION,
            reasoning="Synthetic unit-test reasoning",
        )'''

if source.count(old) != 1:
    raise SystemExit("ABORT: Expected fixture not found exactly once.")

path.write_text(source.replace(old, new), encoding="utf-8")
PY

chown root:root "$TEST"
chmod 0640 "$TEST"

echo "===== VM230: LOG ANALYSIS AGENT TEST RETRY 3 ====="

"$ROOT/venv/bin/python" -m py_compile \
  "$ROOT/app/agents/log_analysis.py" "$TEST"

PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
  discover -s "$ROOT/tests" \
  -p 'test_log_analysis_agent.py' \
  -v

echo
echo "AGENT_SOURCE_MODIFIED=NO"
echo "TEST_FIXTURE_UPDATED=YES"
echo "DATABASE_CONTENT_READ=NO"
echo "OLLAMA_REQUEST_SENT=NO"
echo "SERVICE_RESTARTED=NO"
```

Both `test_delegates_request_and_returns_proposal` and `test_propagates_analysis_error` were `OK`. There were no actual requests to Ollama, no DB reads and no service restarts.

## 2.3 Checking the Contents

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager

echo "===== 1. AGENT SOURCE ====="
sed -n '1,240p' "$ROOT/app/agents/log_analysis.py"

echo
echo "===== 2. AGENT UNIT TEST ====="
sed -n '1,260p' "$ROOT/tests/test_log_analysis_agent.py"

echo
echo "===== 3. AGENT PACKAGE FILES ====="
find "$ROOT/app/agents" -maxdepth 2 -type f \
  ! -path '*/__pycache__/*' -printf '%M %u:%g %p\n' | sort

echo
echo "===== 4. PROJECT CHANGE STATUS ====="
if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git -C "$ROOT" status --short
else
    echo "NOT_A_GIT_WORKTREE"
fi

echo
echo "READ_ONLY=YES"
echo "SERVICE_RESTARTED=NO"
echo "DATABASE_CONTENT_READ=NO"
```

`LogAnalysisAgent` is a thin, read-only agent that delegates to the existing `analyze_events()`, with no functions for executing or approving defensive actions.

# Chapter 3: The Threat Analysis Agent

## 3.1 Design

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager

echo "===== 1. ANALYSIS PROPOSAL SCHEMA ====="
sed -n '1,280p' "$ROOT/app/schemas/analysis_proposal.py"

echo
echo "===== 2. SECURITY EVENT SCHEMA ====="
sed -n '1,280p' "$ROOT/app/schemas/security_event.py"

echo
echo "===== 3. ANALYSIS REQUEST SCHEMA ====="
sed -n '1,240p' "$ROOT/app/schemas/analysis.py"

echo
echo "===== 4. OTHER SCHEMA INVENTORY ====="
find "$ROOT/app/schemas" -maxdepth 2 -type f \
  ! -path '*/__pycache__/*' -printf '%f\n' | sort

echo
echo "===== 5. POLICY AND AGENT SOURCE INVENTORY ====="
find "$ROOT/app/policies" "$ROOT/app/agents" -maxdepth 2 -type f \
  ! -path '*/__pycache__/*' -printf '%M %u:%g %p\n' 2>/dev/null | sort

echo
echo "===== 6. EXISTING THREAT-RELATED REFERENCES ====="
grep -RInE 'threat|confidence|evidence_event_ids|severity|risk_score' \
  "$ROOT/app/agents" "$ROOT/app/services" "$ROOT/app/schemas" \
  --include='*.py' 2>/dev/null | head -160 || true

echo
echo "READ_ONLY=YES"
echo "FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "DATABASE_CONTENT_READ=NO"
```

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager

echo "===== 1. LOG ANALYSIS AGENT REFERENCES ====="
grep -RIn "LogAnalysisAgent" \
  "$ROOT/app" "$ROOT/tests" \
  --include='*.py' 2>/dev/null || true

echo
echo "===== 2. ANALYSIS API ====="
sed -n '1,260p' "$ROOT/app/api/analysis.py"

echo
echo "===== 3. WAZUH API ====="
sed -n '1,280p' "$ROOT/app/api/wazuh.py"

echo
echo "===== 4. API ROUTER REGISTRATION ====="
grep -RInE 'include_router|analysis_router|wazuh_router' \
  "$ROOT/app" --include='*.py' 2>/dev/null || true

echo
echo "===== 5. AGENT IMPORT CONVENTIONS ====="
find "$ROOT/app" -maxdepth 2 -type f -name '*.py' \
  ! -path '*/__pycache__/*' -printf '%p\n' | sort

echo
echo "READ_ONLY=YES"
echo "FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "DATABASE_CONTENT_READ=NO"
```

The existing `AIAnalysisProposal` has severity, confidence, evidence event IDs and recommended actions, so we do not create a new schema. The two analysis APIs still call `analyze_events()` directly, and `LogAnalysisAgent` is not used by the APIs.

`ThreatAnalysisAgent` is given the role of independently checking the log analysis result, not merely rewrapping the AI's answer.

- Delegate analysis to `LogAnalysisAgent`
- For the returned proposal, check for duplicate evidence IDs, duplicate input event IDs, and evidence IDs not in the input
- Reject inconsistencies with a dedicated exception

## 3.2 Building and Testing

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
AGENT="$ROOT/app/agents/threat_analysis.py"
TEST="$ROOT/tests/test_threat_analysis_agent.py"

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Run as root."
    exit 1
fi

if [ -e "$AGENT" ] || [ -e "$TEST" ]; then
    echo "ABORT: One or more target files already exist. No files overwritten."
    exit 1
fi

python3 - <<'PY'
from pathlib import Path

agent = Path("/opt/ai-defense-manager/app/agents/threat_analysis.py")
test = Path("/opt/ai-defense-manager/tests/test_threat_analysis_agent.py")

agent_source = '''"""Threat analysis agent with independent evidence validation.

The agent delegates initial analysis to LogAnalysisAgent, then independently
checks that every cited evidence event belongs to the supplied request.
It does not execute or authorize defensive actions.
"""

from app.agents.log_analysis import LogAnalysisAgent
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal


class ThreatAnalysisError(ValueError):
    """Raised when an analysis proposal fails independent validation."""


class ThreatAnalysisAgent:
    """Validate threat analysis proposals against their source events."""

    def __init__(self, log_agent: LogAnalysisAgent | None = None) -> None:
        self._log_agent = log_agent or LogAnalysisAgent()

    async def analyze(self, request: AIAnalysisRequest) -> AIAnalysisProposal:
        """Analyze events and independently validate the resulting proposal."""
        proposal = await self._log_agent.analyze(request)
        return self.validate(request, proposal)

    @staticmethod
    def validate(
        request: AIAnalysisRequest,
        proposal: AIAnalysisProposal,
    ) -> AIAnalysisProposal:
        """Reject duplicate, missing, or unrelated evidence references."""
        if not request.events:
            raise ThreatAnalysisError("request contains no security events")

        input_ids = [event.event_id for event in request.events]
        if len(input_ids) != len(set(input_ids)):
            raise ThreatAnalysisError("request contains duplicate event IDs")

        evidence_ids = proposal.evidence_event_ids
        if not evidence_ids:
            raise ThreatAnalysisError("proposal contains no evidence event IDs")

        if len(evidence_ids) != len(set(evidence_ids)):
            raise ThreatAnalysisError("proposal contains duplicate evidence event IDs")

        input_id_set = set(input_ids)
        unknown_ids = set(evidence_ids) - input_id_set
        if unknown_ids:
            raise ThreatAnalysisError(
                "proposal references evidence outside the supplied request"
            )

        return proposal
'''

test_source = '''import unittest
from unittest.mock import AsyncMock

from uuid import uuid4

from app.agents.threat_analysis import (
    ThreatAnalysisAgent,
    ThreatAnalysisError,
)
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import (
    AIAnalysisProposal,
    RecommendedAction,
)
from app.schemas.security_event import SecurityEvent


def make_event():
    return SecurityEvent(
        source="wazuh",
        severity="medium",
        event_category="authentication",
        event_summary="Synthetic threat-analysis test event",
    )


def make_request(events=None):
    return AIAnalysisRequest(events=events or [make_event()])


def make_proposal(evidence_ids):
    return AIAnalysisProposal(
        summary="Synthetic threat-analysis proposal",
        severity="medium",
        confidence=0.7,
        evidence_event_ids=evidence_ids,
        recommended_action=RecommendedAction.HUMAN_REVIEW,
        reasoning="Synthetic unit-test reasoning",
    )


class TestThreatAnalysisAgent(unittest.IsolatedAsyncioTestCase):

    async def test_analyze_delegates_and_validates_proposal(self):
        request = make_request()
        proposal = make_proposal([request.events[0].event_id])
        log_agent = type("FakeLogAgent", (), {})()
        log_agent.analyze = AsyncMock(return_value=proposal)

        result = await ThreatAnalysisAgent(log_agent).analyze(request)

        log_agent.analyze.assert_awaited_once_with(request)
        self.assertIs(result, proposal)

    async def test_rejects_duplicate_input_event_ids(self):
        event = make_event()
        request = make_request([event, event])
        proposal = make_proposal([event.event_id])

        with self.assertRaisesRegex(ThreatAnalysisError, "duplicate event IDs"):
            ThreatAnalysisAgent.validate(request, proposal)

    async def test_rejects_duplicate_evidence_ids(self):
        request = make_request()
        event_id = request.events[0].event_id
        proposal = make_proposal([event_id, event_id])

        with self.assertRaisesRegex(
            ThreatAnalysisError, "duplicate evidence event IDs"
        ):
            ThreatAnalysisAgent.validate(request, proposal)

    async def test_rejects_evidence_not_in_request(self):
        request = make_request()
        proposal = make_proposal([uuid4()])

        with self.assertRaisesRegex(
            ThreatAnalysisError, "outside the supplied request"
        ):
            ThreatAnalysisAgent.validate(request, proposal)

    async def test_accepts_valid_evidence(self):
        request = make_request()
        proposal = make_proposal([request.events[0].event_id])

        result = ThreatAnalysisAgent.validate(request, proposal)

        self.assertIs(result, proposal)


if __name__ == "__main__":
    unittest.main()
'''

agent.write_text(agent_source, encoding="utf-8")
test.write_text(test_source, encoding="utf-8")
PY

chown root:ai-defense "$AGENT"
chmod 0640 "$AGENT"
chown root:root "$TEST"
chmod 0640 "$TEST"

echo "===== VM230: THREAT ANALYSIS AGENT TESTS ====="

"$ROOT/venv/bin/python" -m py_compile "$AGENT" "$TEST"

PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
  discover -s "$ROOT/tests" \
  -p 'test_threat_analysis_agent.py' \
  -v

echo
echo "===== FILE STATUS ====="
stat -c '%A %U:%G %n' "$AGENT" "$TEST"

echo
echo "NEW_AGENT_FILES_CREATED=2"
echo "EXISTING_FILES_OVERWRITTEN=NO"
echo "API_MODIFIED=NO"
echo "DATABASE_CONTENT_READ=NO"
echo "OLLAMA_REQUEST_SENT=NO"
echo "SERVICE_RESTARTED=NO"
```

| Test | Result |
|---|---|
| Accepts valid evidence IDs | passed |
| Delegates to the log analysis agent | passed |
| Rejects duplicate evidence IDs | passed |
| Rejects duplicate input event IDs | passed |
| Rejects evidence IDs not in the input | passed |

All 5 passed.

## 3.3 All Tests

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager

echo "===== VM230: COMPLETE AGENT UNIT TEST SUITE ====="

PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
  discover -s "$ROOT/tests" \
  -p 'test_*.py' \
  -v

echo
echo "===== AGENT FILE INVENTORY ====="
find "$ROOT/app/agents" -maxdepth 1 -type f \
  -printf '%M %u:%g %f\n' | sort

echo
echo "===== TEST FILE INVENTORY ====="
find "$ROOT/tests" -maxdepth 1 -type f \
  -name 'test_*.py' -printf '%M %u:%g %f\n' | sort

echo
echo "FULL_TEST_SUITE=PASSED"
echo "SERVICE_RESTARTED=NO"
echo "DATABASE_CONTENT_READ=NO"
echo "OLLAMA_REQUEST_SENT=NO"
```

All 7 tests of the two agents passed, and within this scope no effect on each other or on existing functions was seen.

# Closing Notes

In Part 70 we built the first two AI defense agents.

| Agent | File | Tests |
|---|---|---|
| `LogAnalysisAgent` | `app/agents/log_analysis.py` | 2 passed |
| `ThreatAnalysisAgent` | `app/agents/threat_analysis.py` | 5 passed |

Both only read and analyze and do not execute defensive actions. They are not yet connected to the API, and the service has not been restarted. In the next part, Part 71, we move on to an event correlation agent, an agent that orchestrates the whole, and a defense decision policy agent.

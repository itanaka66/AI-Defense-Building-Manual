---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 48: Narrowing the Wazuh Event Conversion to Seven Fields"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 48 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 47 we examined the existing implementation of the AI Defense Manager (VM 230) and decided where to put the allowlist. Here we actually change the code.

1. Before changing anything, save copies of the five target files
2. Check the environment for running tests and the module import path
3. Tally the actual groups, in order to switch classification from `location` and `decoder.name` to `rule.groups`
4. Using Python syntax analysis (AST), rewrite only two files (`wazuh_relay.py` and `ai_analysis.py`)
5. Run 26 unit tests with synthetic events and check the diff

No actual communication with Wazuh or Ollama, no writes to PostgreSQL or SQLite, and no service restarts.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **VM 220**: security-core (root)

# Chapter 1: Saving the Files Before the Change

We create a directory per date and time under `/var/backups/ai-defense-manager/`, copy with `cp -a` to keep owner, permissions and times, and compare the SHA256 with the originals.

> **Run on: VM 230**

```bash
echo "===== AI DEFENSE MANAGER PRE-CHANGE BACKUP ====="

BACKUP_ROOT="/var/backups/ai-defense-manager"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$STAMP"

echo "--- Create protected backup directory ---"
install -d -m 700 "$BACKUP_ROOT"
install -d -m 700 "$BACKUP_DIR"

echo "BACKUP_DIR=$BACKUP_DIR"

FILES=(
  "app/services/wazuh_relay.py"
  "app/services/event_sanitizer.py"
  "app/services/ai_analysis.py"
  "app/schemas/security_event.py"
  "app/api/wazuh.py"
)

BACKUP_OK=1

for REL in "${FILES[@]}"; do
  SRC="/opt/ai-defense-manager/$REL"
  DST="$BACKUP_DIR/$REL"

  echo
  echo "--- BACKUP: $REL ---"

  if [ ! -f "$SRC" ]; then
    echo "ERROR=SOURCE_NOT_FOUND"
    BACKUP_OK=0
    continue
  fi

  install -d -m 700 "$(dirname "$DST")"

  if cp -a "$SRC" "$DST"; then
    echo "COPY=OK"
  else
    echo "COPY=FAILED"
    BACKUP_OK=0
    continue
  fi

  SRC_HASH="$(sha256sum "$SRC" | awk '{print $1}')"
  DST_HASH="$(sha256sum "$DST" | awk '{print $1}')"

  echo "SOURCE_SHA256=$SRC_HASH"
  echo "BACKUP_SHA256=$DST_HASH"

  if [ "$SRC_HASH" = "$DST_HASH" ] && cmp -s "$SRC" "$DST"; then
    echo "VERIFY=PASS"
  else
    echo "VERIFY=FAILED"
    BACKUP_OK=0
  fi

  stat -c 'BACKUP_OWNER=%U:%G MODE=%a SIZE=%s' "$DST"
done

echo
echo "===== BACKUP RESULT ====="

if [ "$BACKUP_OK" -eq 1 ]; then
  echo "BACKUP_STATUS=SUCCESS"
else
  echo "BACKUP_STATUS=FAILED"
fi

echo "BACKUP_DIR=$BACKUP_DIR"
echo "PRODUCTION_SERVICE_MODIFIED=NO"
echo "APPLICATION_FILES_MODIFIED=NO"
echo "DATABASE_ACCESSED=NO"
```

The copies and SHA256 comparisons of all five files succeeded. The copies are in `/var/backups/ai-defense-manager/20261123-031115`. The `root:ai-defense`, `640` of `wazuh_relay.py` and the others are also preserved.

# Chapter 2: Checking the Test Environment

## 2.1 Python and Test Tools

No new packages are installed.

> **Run on: VM 230**

```bash
echo "===== ISOLATED TEST ENVIRONMENT AUDIT ====="

APP="/opt/ai-defense-manager"
VENV="$APP/venv"

echo "--- Python and test runner ---"
"$VENV/bin/python" --version
"$VENV/bin/python" -m pytest --version 2>&1

echo
echo "--- Required module availability ---"
"$VENV/bin/python" - <<'PY'
import importlib.util

modules = [
    "pytest",
    "pydantic",
    "httpx",
    "fastapi",
    "app",
]

for name in modules:
    try:
        spec = importlib.util.find_spec(name)
        print(f"{name}={'AVAILABLE' if spec else 'NOT_FOUND'}")
    except Exception as exc:
        print(f"{name}=CHECK_ERROR:{type(exc).__name__}")
PY

echo
echo "--- Project test/config metadata ---"
for f in \
  "$APP/pyproject.toml" \
  "$APP/pytest.ini" \
  "$APP/setup.cfg" \
  "$APP/requirements.txt" \
  "$APP/requirements-dev.txt"
do
  if [ -f "$f" ]; then
    stat -c 'FOUND=%n SIZE=%s MODE=%a' "$f"
  else
    echo "NOT_FOUND=$f"
  fi
done

echo
echo "--- Backup integrity summary ---"
find /var/backups/ai-defense-manager/20261123-031115 \
  -type f -printf '%P %s bytes\n' | sort

echo
echo "APPLICATION_FILES_MODIFIED=NO"
echo "PACKAGES_INSTALLED=NO"
echo "SERVICE_RESTARTED=NO"
```

Python 3.12.3, FastAPI, Pydantic and HTTPX are available, but `pytest` was not installed. We do not install `pytest` and use Python's standard `unittest` instead.

## 2.2 Module Import Path

> **Run on: VM 230**

```bash
echo "===== APPLICATION IMPORT PATH AUDIT ====="

APP="/opt/ai-defense-manager"
VENV="$APP/venv"

echo "--- Import from project root ---"
cd "$APP" && "$VENV/bin/python" - <<'PY'
import importlib
import sys

print("PYTHON_EXECUTABLE=" + sys.executable)
print("WORKING_DIRECTORY=" + __import__("os").getcwd())

modules = [
    "app",
    "app.main",
    "app.schemas.security_event",
    "app.schemas.analysis_proposal",
    "app.services.event_sanitizer",
    "app.services.wazuh_relay",
    "app.services.ai_analysis",
]

for name in modules:
    try:
        importlib.import_module(name)
        print(f"IMPORT={name}:PASS")
    except Exception as exc:
        print(f"IMPORT={name}:FAIL:{type(exc).__name__}")
PY

echo
echo "--- Systemd application execution context ---"
systemctl show ai-defense-manager.service \
  --property=WorkingDirectory \
  --property=User \
  --property=Group \
  --property=ExecStart \
  --no-pager

echo
echo "--- Standard unittest availability ---"
"$VENV/bin/python" -m unittest --help >/dev/null 2>&1
if [ "$?" -eq 0 ]; then
  echo "UNITTEST=AVAILABLE"
else
  echo "UNITTEST=UNAVAILABLE"
fi

echo
echo "APPLICATION_FILES_MODIFIED=NO"
echo "PACKAGES_INSTALLED=NO"
echo "SERVICE_RESTARTED=NO"
```

All existing modules could be imported from `/opt/ai-defense-manager`, and `unittest` was usable. The service runs as the user `ai-defense` with working directory `/opt/ai-defense-manager`, so the tests match these conditions.

## 2.3 The Current Classification and Summary

> **Run on: VM 230**

```bash
echo "===== EXISTING TRANSFORMATION EXPRESSION AUDIT ====="

cd /opt/ai-defense-manager && venv/bin/python - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

def show_assignments(relative, function_name, selected):
    path = root / relative
    tree = ast.parse(path.read_text(encoding="utf-8"))

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != function_name:
            continue

        print(f"\nMODULE={relative} FUNCTION={function_name}")

        for child in ast.walk(node):
            if not isinstance(child, ast.Assign):
                continue

            names = [
                target.id for target in child.targets
                if isinstance(target, ast.Name)
            ]

            for name in names:
                if name not in selected:
                    continue
                try:
                    expression = ast.unparse(child.value)
                except Exception:
                    expression = "UNAVAILABLE"
                print(f"{name} = {expression[:300]}")

            if "category_map" in names and isinstance(child.value, ast.Dict):
                print("CATEGORY_MAP_ENTRIES:")
                for key, value in zip(child.value.keys, child.value.values):
                    try:
                        print(
                            "  "
                            + repr(ast.literal_eval(key))
                            + " -> "
                            + repr(ast.literal_eval(value))
                        )
                    except Exception:
                        print("  NON_LITERAL_ENTRY")

        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                try:
                    expression = ast.unparse(child.value) if child.value else "None"
                except Exception:
                    expression = "UNAVAILABLE"
                print(f"RETURN={expression[:300]}")

show_assignments(
    "services/wazuh_relay.py",
    "_severity",
    {"level"},
)

show_assignments(
    "services/wazuh_relay.py",
    "_convert_alert",
    {
        "timestamp", "level", "rule_id", "description",
        "agent_id", "agent_name", "location", "decoder",
        "observed_at", "raw_category", "category_map",
        "category", "summary",
    },
)

print("\nRAW_ALERT_VALUES_DISPLAYED=NO")
print("CONFIGURATION_VALUES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
print("FILES_MODIFIED=NO")
PY
```

The current classification used `decoder.name` first and fell back to `location`. If `location` is removed, events that were classified only by `location` could become `other`, so we change the classification to use `rule.groups`.

# Chapter 3: Designing the Classification

## 3.1 Tallying the Actual Groups

Wazuh's `alerts.json` is `wazuh:wazuh`, `640`, so run this as **root** on VM 220 (an ordinary user gets `PermissionError`). No values are displayed.

> **Run on: VM 220**

```bash
echo "===== WAZUH CATEGORY MAPPING AGGREGATION ====="

python3 - <<'PY'
import json
from collections import Counter

path = "/var/ossec/logs/alerts/alerts.json"

groups_count = Counter()
decoders = Counter()
locations = Counter()
missing_groups = 0
invalid_records = 0
records = 0

with open(path, encoding="utf-8", errors="replace") as f:
    for line in f:
        if not line.strip():
            continue

        try:
            alert = json.loads(line)
            records += 1
        except Exception:
            invalid_records += 1
            continue

        rule = alert.get("rule")
        if not isinstance(rule, dict):
            rule = {}

        groups = rule.get("groups")
        if isinstance(groups, list):
            for group in groups:
                if isinstance(group, str):
                    groups_count[group.strip().lower()] += 1
        else:
            missing_groups += 1

        decoder = alert.get("decoder")
        if isinstance(decoder, dict):
            name = decoder.get("name")
            if isinstance(name, str):
                decoders[name.strip().lower()] += 1

        location = alert.get("location")
        if isinstance(location, str):
            locations[location.strip().lower()] += 1

print(f"VALID_JSON_RECORDS={records}")
print(f"INVALID_JSON_RECORDS={invalid_records}")
print(f"RECORDS_WITHOUT_GROUPS={missing_groups}")

print("\n--- RULE GROUP COUNTS ---")
for name, count in groups_count.most_common():
    print(f"{name}: {count}")

print("\n--- DECODER NAME COUNTS ---")
for name, count in decoders.most_common():
    print(f"{name}: {count}")

print("\n--- LOCATION COUNTS (NAMES ONLY) ---")
for name, count in locations.most_common(30):
    print(f"{name}: {count}")

print("\nRAW_EVENT_CONTENT_DISPLAYED=NO")
print("FILES_MODIFIED=NO")
PY
```

| Item | Count |
|---|---:|
| Valid JSON | 268 |
| Invalid JSON | 0 |
| No `rule.groups` | 0 |
| `pam` | 228 |
| `proxmox-ve` | 16 |
| `sshd` | 1 |
| `sudo` | 3 |
| `postgresql` | 34 |
| `authentication_failed` | 4 |

Groups are counted with overlap, so the total does not match the number of events.

## 3.2 Classification and Schema Compatibility

> **Run on: VM 230**

```bash
echo "===== CATEGORY AND SCHEMA COMPATIBILITY AUDIT ====="

cd /opt/ai-defense-manager && venv/bin/python - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

targets = {
    "schemas/security_event.py": [
        "SecurityEvent",
        "event_category",
        "source",
    ],
    "services/wazuh_relay.py": [
        "_convert_alert",
        "category_map",
        "raw_category",
        "event_category",
    ],
    "services/ai_analysis.py": [
        "analyze_events",
        "event_category",
    ],
}

for relative, terms in targets.items():
    path = root / relative
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    print(f"\n--- {relative} ---")

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "SecurityEvent":
            print("CLASS=SecurityEvent")
            for item in node.body:
                if isinstance(item, (ast.Assign, ast.AnnAssign)):
                    names = []
                    if isinstance(item, ast.Assign):
                        names = [
                            t.id for t in item.targets
                            if isinstance(t, ast.Name)
                        ]
                    elif isinstance(item.target, ast.Name):
                        names = [item.target.id]

                    if any(term in names for term in terms):
                        print(ast.unparse(item)[:500])

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in terms:
                print(f"\nFUNCTION={node.name}")
                print(ast.unparse(node)[:5000])

    for term in terms:
        if term == "event_category":
            print("EVENT_CATEGORY_LITERAL_OCCURRENCES:")
            for lineno, line in enumerate(source.splitlines(), 1):
                if "event_category" in line:
                    print(f"  LINE={lineno}: {line.strip()[:200]}")

print("\nSOURCE_EVENT_CONTENT_DISPLAYED=NO")
print("CONFIGURATION_VALUES_DISPLAYED=NO")
print("FILES_MODIFIED=NO")
PY
```

`event_category` is a string of 1–64 characters, so adding classifications requires no change to the Pydantic schema. The classifications we decided on are as follows. When there are several specific groups, the higher row takes priority.

| Priority | Wazuh `rule.groups` | Classification |
|---:|---|---|
| 1 | `pvedaemon`, `proxmox-ve` | `virtualization_management` |
| 2 | `pam`, `authentication_success`, `authentication_failed` | `authentication` |
| 3 | `sshd` | `remote_access` |
| 4 | `sudo` | `privilege_escalation` |
| 5 | `useradd`, `open-userdel` | `account_management` |
| 6 | `postgresql` | `database` |
| 7 | other | `other` |

General groups such as `syslog`, `local`, `error` and `access_control` alone do not produce a specific classification.

## 3.3 The Input Boundary

> **Run on: VM 230**

```bash
echo "===== SECURITY EVENT INPUT AND AI BOUNDARY AUDIT ====="

cd /opt/ai-defense-manager && venv/bin/python - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

targets = [
    "schemas/security_event.py",
    "schemas/analysis.py",
    "schemas/analysis_proposal.py",
    "api/analysis.py",
    "api/wazuh.py",
    "services/ai_analysis.py",
]

for relative in targets:
    path = root / relative
    tree = ast.parse(path.read_text(encoding="utf-8"))

    print(f"\n--- {relative} ---")

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            if node.name in {
                "SecurityEvent",
                "AIAnalysisRequest",
                "AIAnalysisProposal",
            }:
                print(ast.unparse(node)[:6500])

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in {
                "create_analysis",
                "analyze_wazuh_events",
                "get_wazuh_events",
                "analyze_events",
            }:
                print(ast.unparse(node)[:6500])

print("\nCONFIGURATION_VALUES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
print("FILES_MODIFIED=NO")
PY
```

`SecurityEvent` and `AIAnalysisRequest` use `extra='forbid'` (reject unknown fields), which is a good design. However, `/api/v1/analysis` is not Wazuh-specific; it also accepts input from Prometheus and others. So we decide that:

- **Wazuh-specific constraints are applied at Wazuh retrieval (`wazuh_relay.py`)**
- **Where data is sent to the AI, only allowed fields common to all events are sent**

# Chapter 4: Rewriting the Two Files

## 4.1 Last Check Before the Change

> **Run on: VM 230**

```bash
echo "===== PRE-IMPLEMENTATION SOURCE AND BACKUP AUDIT ====="

cd /opt/ai-defense-manager && venv/bin/python - <<'PY'
import ast
import hashlib
from pathlib import Path

app = Path("/opt/ai-defense-manager/app")
backup = Path("/var/backups/ai-defense-manager/20261123-031115")

targets = {
    "services/wazuh_relay.py": [
        "_severity",
        "_convert_alert",
        "fetch_wazuh_events",
    ],
    "services/event_sanitizer.py": [
        "sanitize_event_summary",
        "redact_ip",
    ],
    "services/ai_analysis.py": [
        "analyze_events",
    ],
}

for relative, functions in targets.items():
    source_path = app / relative
    backup_path = backup / "app" / relative

    print(f"\n===== {relative} =====")
    print(f"SOURCE_EXISTS={source_path.is_file()}")
    print(f"BACKUP_EXISTS={backup_path.is_file()}")

    if not source_path.is_file() or not backup_path.is_file():
        print("AUDIT=FAILED")
        continue

    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    backup_hash = hashlib.sha256(backup_path.read_bytes()).hexdigest()

    print(f"BACKUP_HASH_MATCH={source_hash == backup_hash}")
    print(f"SOURCE_SHA256={source_hash}")

    tree = ast.parse(source_path.read_text(encoding="utf-8"))

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in functions:
                print(f"\n--- FUNCTION {node.name} ---")
                print(ast.unparse(node))

    print("\n--- IMPORTS ---")
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            print(ast.unparse(node))

print("\nSERVICE_STATE=NOT_CHANGED")
print("DATABASE_ACCESSED=NO")
print("NETWORK_REQUESTS=NO")
print("FILES_MODIFIED=NO")
PY
```

The SHA256 of the three files matched the copies.

## 4.2 Reading the Function Definitions

The definition of `analyze_events` spans several lines and cannot be found by a replacement that searches for a one-line string. We read the actual definition and the part that sends to the AI.

> **Run on: VM 230**

```bash
echo "===== AI ANALYSIS FUNCTION SIGNATURES ====="

cd /opt/ai-defense-manager && venv/bin/python - <<'PY'
import ast
from pathlib import Path

targets = [
    Path("app/services/ai_analysis.py"),
    Path("app/services/wazuh_relay.py"),
]

for path in targets:
    print(f"\n--- {path} ---")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in {
                "analyze_events",
                "_convert_alert",
                "_build_event_payload",
            }:
                print(
                    f"FUNCTION={node.name} "
                    f"LINE={node.lineno} "
                    f"ASYNC={isinstance(node, ast.AsyncFunctionDef)}"
                )
                print(ast.get_source_segment(source, node).splitlines()[0])

    lines = source.splitlines()
    if path.name == "ai_analysis.py":
        print("\n--- AI payload construction context ---")
        for i, line in enumerate(lines, 1):
            if (
                "'events':" in line
                or '"events":' in line
                or "sanitize_event_summary" in line
                or "messages" in line
            ):
                start = max(1, i - 3)
                end = min(len(lines), i + 3)
                print(f"[lines {start}-{end}]")
                for n in range(start, end + 1):
                    print(f"{n}: {lines[n-1]}")
    else:
        print("\n--- Wazuh conversion function context ---")
        for i, line in enumerate(lines, 1):
            if line.startswith("def _convert_alert"):
                start = i
                end = min(len(lines), i + 65)
                for n in range(start, end + 1):
                    print(f"{n}: {lines[n-1]}")
                break
PY

echo
echo "===== FILE HASHES (VERIFY NO CHANGES) ====="
sha256sum \
  app/services/wazuh_relay.py \
  app/services/event_sanitizer.py \
  app/services/ai_analysis.py

echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

```bash
echo "===== AI ANALYSIS SOURCE ====="
cd /opt/ai-defense-manager

nl -ba app/services/ai_analysis.py | sed -n '1,125p'

echo
echo "===== WAZUH RELAY IMPORTS AND CONVERSION ====="
nl -ba app/services/wazuh_relay.py | sed -n '1,110p'

echo
echo "===== AI ANALYSIS ERROR DEFINITION ====="
grep -R -n -E 'class AIAnalysisError|AIAnalysisError' app/services/ai_analysis.py app/

echo
echo "===== ORIGINAL BACKUP HASH COMPARISON ====="
sha256sum \
  app/services/wazuh_relay.py \
  /var/backups/ai-defense-manager/20261123-031115/app/services/wazuh_relay.py \
  app/services/ai_analysis.py \
  /var/backups/ai-defense-manager/20261123-031115/app/services/ai_analysis.py

echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

## 4.3 Rewriting with the AST

We drop broad regex-based replacement and, using the result of Python syntax analysis, replace only the function bodies and the part that builds the list of events. The proposed changes to both files are **written only after both pass the syntax check**. The APIs, schemas and masking (`event_sanitizer.py`) are not changed.

> **Run on: VM 230**

```bash
echo "===== AST-BASED WAZUH NORMALIZATION IMPLEMENTATION ====="

cd /opt/ai-defense-manager && venv/bin/python - <<'PY'
import ast
import hashlib
import re
from pathlib import Path

root = Path("/opt/ai-defense-manager")
backup = Path("/var/backups/ai-defense-manager/20261123-031115")

expected = {
    "app/services/wazuh_relay.py":
        "599b63978b10745223da8a9c7ce44e39003c864146facfbe518a170e764febcd",
    "app/services/event_sanitizer.py":
        "ecc8a9d46e75c833a0f478901518bb818fe05cdf1710f7d95bc33623f63fb7b4",
    "app/services/ai_analysis.py":
        "e5c83f063c0a23b8c99521571909dc90b77eea9d94108fa3ac7bd04ec79939bc",
}

for relative, expected_hash in expected.items():
    current_hash = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    backup_hash = hashlib.sha256((backup / relative).read_bytes()).hexdigest()
    if current_hash != expected_hash or backup_hash != expected_hash:
        raise RuntimeError(f"Precondition failed: {relative}")

print("BACKUP_INTEGRITY=PASS")


def line_offset(source, line_number, column=0):
    lines = source.splitlines(keepends=True)
    return sum(len(line) for line in lines[:line_number - 1]) + column


# ------------------------------------------------------------
# Prepare Wazuh relay replacement using AST function boundaries.
# ------------------------------------------------------------
relay_path = root / "app/services/wazuh_relay.py"
relay_source = relay_path.read_text(encoding="utf-8")
relay_tree = ast.parse(relay_source)

relay_functions = [
    node for node in relay_tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "_convert_alert"
]
if len(relay_functions) != 1:
    raise RuntimeError(
        f"Expected one top-level _convert_alert, found {len(relay_functions)}"
    )

new_relay_function = '''def _convert_alert(alert: dict) -> SecurityEvent:
    """Convert only the seven approved normalized Wazuh fields."""
    import re

    if not isinstance(alert, dict):
        raise ValueError("Alert must be an object")

    timestamp = alert.get("timestamp")
    level = alert.get("rule.level")
    rule_id = alert.get("rule.id")
    description = alert.get("rule.description")
    groups = alert.get("rule.groups")
    agent_id = alert.get("agent.id")

    if not isinstance(timestamp, str) or not timestamp or len(timestamp) > 64:
        raise ValueError("Invalid alert timestamp")

    if isinstance(level, bool) or not isinstance(level, int) or not 0 <= level <= 16:
        raise ValueError("Invalid Wazuh rule level")

    observed_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("Alert timestamp must include a timezone")

    if rule_id is not None:
        if not isinstance(rule_id, str) or not re.fullmatch(r"[0-9]{1,16}", rule_id):
            raise ValueError("Invalid rule ID")

    if description is not None:
        if not isinstance(description, str) or len(description) > 512:
            raise ValueError("Invalid rule description")

    if agent_id is not None:
        if not isinstance(agent_id, str) or not re.fullmatch(r"[0-9]{1,16}", agent_id):
            raise ValueError("Invalid agent ID")

    if not isinstance(groups, list) or len(groups) > 32:
        raise ValueError("Invalid Wazuh rule groups")

    normalized_groups = set()
    for group in groups:
        if not isinstance(group, str):
            raise ValueError("Invalid Wazuh rule group")
        normalized = group.strip().lower()
        if not normalized or len(normalized) > 64:
            raise ValueError("Invalid Wazuh rule group")
        if not re.fullmatch(r"[a-z0-9_-]+", normalized):
            raise ValueError("Invalid Wazuh rule group")
        normalized_groups.add(normalized)

    category_rules = (
        ({"pvedaemon", "proxmox-ve"}, "virtualization_management"),
        ({"pam", "authentication_success", "authentication_failed"}, "authentication"),
        ({"sshd"}, "remote_access"),
        ({"sudo"}, "privilege_escalation"),
        ({"useradd", "open-userdel"}, "account_management"),
        ({"postgresql"}, "database"),
    )

    category = "other"
    for group_names, mapped_category in category_rules:
        if normalized_groups.intersection(group_names):
            category = mapped_category
            break

    summary = (description or "Wazuh security alert")[:512]

    return SecurityEvent(
        source="wazuh",
        observed_at=observed_at,
        severity=_severity(level),
        rule_id=rule_id,
        rule_description=description[:512] if description else None,
        agent_id=agent_id,
        event_category=category,
        event_summary=summary,
    )
'''

relay_node = relay_functions[0]
relay_start = line_offset(relay_source, relay_node.lineno)
relay_end = line_offset(relay_source, relay_node.end_lineno + 1) if relay_node.end_lineno < len(relay_source.splitlines()) else len(relay_source)
relay_new = relay_source[:relay_start] + new_relay_function + "\n\n" + relay_source[relay_end:]
ast.parse(relay_new)
print("WAZUH_RELAY_TRANSFORM=PASS")


# ------------------------------------------------------------
# Prepare AI payload helper and replace only the event list.
# ------------------------------------------------------------
ai_path = root / "app/services/ai_analysis.py"
ai_source = ai_path.read_text(encoding="utf-8")
ai_tree = ast.parse(ai_source)

if "_ALLOWED_WAZUH_CATEGORIES" in ai_source or "_build_event_payload" in ai_source:
    raise RuntimeError("AI payload helper already exists; refusing duplicate edit")

analyze_functions = [
    node for node in ai_tree.body
    if isinstance(node, ast.AsyncFunctionDef) and node.name == "analyze_events"
]
if len(analyze_functions) != 1:
    raise RuntimeError(
        f"Expected one top-level async analyze_events, found {len(analyze_functions)}"
    )

helper = '''_ALLOWED_WAZUH_CATEGORIES = frozenset({
    "virtualization_management",
    "authentication",
    "remote_access",
    "privilege_escalation",
    "account_management",
    "database",
    "other",
})


def _build_event_payload(event) -> dict:
    """Build an explicit LLM allowlist payload from a validated event."""
    if event.source == "wazuh":
        if event.event_category not in _ALLOWED_WAZUH_CATEGORIES:
            raise AIAnalysisError("Invalid Wazuh event category")
        if (
            event.agent_name is not None
            or event.source_ip is not None
            or event.destination_ip is not None
        ):
            raise AIAnalysisError(
                "Wazuh event contains prohibited identity or IP fields"
            )

    return {
        "event_id": str(event.event_id),
        "observed_at": event.observed_at.isoformat(),
        "severity": event.severity,
        "rule_id": event.rule_id,
        "event_category": event.event_category,
        "event_summary": sanitize_event_summary(event.event_summary),
    }


'''

analyze_node = analyze_functions[0]
ai_insert_at = line_offset(ai_source, analyze_node.lineno)
ai_new = ai_source[:ai_insert_at] + helper + ai_source[ai_insert_at:]
ai_tree_new = ast.parse(ai_new)

# Find the exact list comprehension that builds the LLM event objects.
event_list_comprehensions = []
for node in ast.walk(ai_tree_new):
    if not isinstance(node, ast.ListComp) or not isinstance(node.elt, ast.Dict):
        continue
    keys = {
        key.value for key in node.elt.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    if {
        "event_id", "observed_at", "severity",
        "rule_id", "event_category", "event_summary"
    }.issubset(keys):
        event_list_comprehensions.append(node)

if len(event_list_comprehensions) != 1:
    raise RuntimeError(
        "Expected one six-field AI event payload list, found "
        f"{len(event_list_comprehensions)}"
    )

event_node = event_list_comprehensions[0]
ai_start = line_offset(ai_new, event_node.lineno, event_node.col_offset)
ai_end = line_offset(ai_new, event_node.end_lineno, event_node.end_col_offset)
ai_new = ai_new[:ai_start] + "[_build_event_payload(event) for event in request.events]" + ai_new[ai_end:]

ast.parse(ai_new)
print("AI_ANALYSIS_TRANSFORM=PASS")


# Both prepared files are now syntax-checked. Write only the two approved files.
relay_path.write_text(relay_new, encoding="utf-8")
print("WAZUH_RELAY_UPDATED=YES")

ai_path.write_text(ai_new, encoding="utf-8")
print("AI_ANALYSIS_UPDATED=YES")

print("EVENT_SANITIZER_CHANGED=NO")
print("SCHEMAS_CHANGED=NO")
print("API_ROUTES_CHANGED=NO")
PY

echo
echo "===== POST-EDIT SYNTAX CHECK ====="
venv/bin/python - <<'PY'
import ast
from pathlib import Path

for relative in (
    "app/services/wazuh_relay.py",
    "app/services/ai_analysis.py",
    "app/services/event_sanitizer.py",
):
    ast.parse(Path(relative).read_text(encoding="utf-8"))
    print(f"SYNTAX={relative}:PASS")
PY

echo
echo "===== RESULTING FILE HASHES ====="
sha256sum \
  app/services/wazuh_relay.py \
  app/services/event_sanitizer.py \
  app/services/ai_analysis.py

echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

> **Caution:** This script checks the backup directory and the pre-change SHA256 of the three files (the values at build time) before rewriting. If they do not match, it stops without writing anything. When using it in your own environment, adjust these to the values from when you saved the copies in Chapter 1.

| File | What changed |
|---|---|
| `wazuh_relay.py` | validates the seven-field input; classifies by `rule.groups`; does not use `agent.name`, `location` or `decoder.name` |
| `ai_analysis.py` | builds what is sent to the AI from six fields only (`_build_event_payload()`); checks Wazuh event classification and forbidden fields |
| `event_sanitizer.py` | unchanged |

All syntax checks passed; no service restart, communication or DB connection took place.

# Chapter 5: Testing with Synthetic Events

## 5.1 26 Unit Tests

No actual Wazuh event retrieval, LLM calls or DB writes.

> **Run on: VM 230**

```bash
echo "===== SYNTHETIC WAZUH NORMALIZATION TESTS ====="

cd /opt/ai-defense-manager && venv/bin/python - <<'PY'
import unittest
from datetime import datetime, timezone

from app.services.wazuh_relay import _convert_alert
from app.services.ai_analysis import (
    AIAnalysisError,
    _build_event_payload,
)
from app.schemas.security_event import SecurityEvent
from app.services.event_sanitizer import sanitize_event_summary


BASE_ALERT = {
    "timestamp": "2026-11-23T12:00:00+09:00",
    "rule.id": "100103",
    "rule.level": 7,
    "rule.groups": ["postgresql", "error"],
    "rule.description": "PostgreSQL ERROR event detected",
    "decoder.name": "json",
    "agent.id": "001",
}


class WazuhNormalizationTests(unittest.TestCase):

    def test_postgresql_category(self):
        event = _convert_alert(BASE_ALERT)
        self.assertEqual(event.event_category, "database")

    def test_virtualization_category(self):
        alert = {**BASE_ALERT, "rule.groups": ["syslog", "proxmox-ve"]}
        self.assertEqual(
            _convert_alert(alert).event_category,
            "virtualization_management",
        )

    def test_authentication_category(self):
        alert = {**BASE_ALERT, "rule.groups": ["authentication_failed"]}
        self.assertEqual(
            _convert_alert(alert).event_category,
            "authentication",
        )

    def test_remote_access_category(self):
        alert = {**BASE_ALERT, "rule.groups": ["sshd"]}
        self.assertEqual(
            _convert_alert(alert).event_category,
            "remote_access",
        )

    def test_privilege_escalation_category(self):
        alert = {**BASE_ALERT, "rule.groups": ["sudo"]}
        self.assertEqual(
            _convert_alert(alert).event_category,
            "privilege_escalation",
        )

    def test_account_management_category(self):
        alert = {**BASE_ALERT, "rule.groups": ["useradd"]}
        self.assertEqual(
            _convert_alert(alert).event_category,
            "account_management",
        )

    def test_category_precedence(self):
        alert = {
            **BASE_ALERT,
            "rule.groups": ["sudo", "pam", "postgresql"],
        }
        self.assertEqual(
            _convert_alert(alert).event_category,
            "authentication",
        )

    def test_generic_groups_fallback(self):
        alert = {
            **BASE_ALERT,
            "rule.groups": ["syslog", "local", "error", "access_control"],
        }
        self.assertEqual(_convert_alert(alert).event_category, "other")

    def test_missing_groups_rejected(self):
        alert = dict(BASE_ALERT)
        del alert["rule.groups"]
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_non_list_groups_rejected(self):
        alert = {**BASE_ALERT, "rule.groups": "postgresql"}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_too_many_groups_rejected(self):
        alert = {**BASE_ALERT, "rule.groups": ["syslog"] * 33}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_malformed_group_rejected(self):
        alert = {**BASE_ALERT, "rule.groups": ["postgresql;sudo"]}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_non_string_group_rejected(self):
        alert = {**BASE_ALERT, "rule.groups": ["postgresql", 7]}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_invalid_timestamp_rejected(self):
        alert = {**BASE_ALERT, "timestamp": "not-a-timestamp"}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_timezone_required(self):
        alert = {**BASE_ALERT, "timestamp": "2026-11-23T12:00:00"}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_boolean_level_rejected(self):
        alert = {**BASE_ALERT, "rule.level": True}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_out_of_range_level_rejected(self):
        alert = {**BASE_ALERT, "rule.level": 17}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_invalid_rule_id_rejected(self):
        alert = {**BASE_ALERT, "rule.id": "100;103"}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_invalid_agent_id_rejected(self):
        alert = {**BASE_ALERT, "agent.id": "../001"}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_hostile_extra_fields_ignored(self):
        alert = {
            **BASE_ALERT,
            "agent.name": "hostile-agent-name",
            "location": "/private/path",
            "full_log": "synthetic raw log",
            "data": {"command": "synthetic command"},
            "predecoder": {"hostname": "synthetic-host"},
            "agent.ip": "203.0.113.77",
        }
        event = _convert_alert(alert)
        self.assertEqual(event.agent_id, "001")
        self.assertIsNone(event.agent_name)
        self.assertIsNone(event.source_ip)
        self.assertIsNone(event.destination_ip)

    def test_ai_payload_exact_allowlist(self):
        event = _convert_alert(BASE_ALERT)
        payload = _build_event_payload(event)
        self.assertEqual(
            set(payload),
            {
                "event_id",
                "observed_at",
                "severity",
                "rule_id",
                "event_category",
                "event_summary",
            },
        )

    def test_ai_rejects_unknown_wazuh_category(self):
        event = SecurityEvent(
            source="wazuh",
            observed_at=datetime.now(timezone.utc),
            severity="low",
            event_category="unexpected_category",
            event_summary="Synthetic event",
        )
        with self.assertRaises(AIAnalysisError):
            _build_event_payload(event)

    def test_ai_rejects_wazuh_agent_name(self):
        event = SecurityEvent(
            source="wazuh",
            observed_at=datetime.now(timezone.utc),
            severity="low",
            event_category="authentication",
            event_summary="Synthetic event",
            agent_name="synthetic-agent",
        )
        with self.assertRaises(AIAnalysisError):
            _build_event_payload(event)

    def test_ai_rejects_wazuh_source_ip(self):
        event = SecurityEvent(
            source="wazuh",
            observed_at=datetime.now(timezone.utc),
            severity="low",
            event_category="authentication",
            event_summary="Synthetic event",
            source_ip="203.0.113.77",
        )
        with self.assertRaises(AIAnalysisError):
            _build_event_payload(event)

    def test_non_wazuh_category_remains_unrestricted(self):
        event = SecurityEvent(
            source="prometheus",
            observed_at=datetime.now(timezone.utc),
            severity="low",
            event_category="custom_prometheus_category",
            event_summary="Synthetic monitoring event",
        )
        payload = _build_event_payload(event)
        self.assertEqual(
            payload["event_category"],
            "custom_prometheus_category",
        )

    def test_sanitizer_redacts_synthetic_secret_and_ip(self):
        original = (
            "Synthetic alert from 203.0.113.77 "
            "password=SuperSecret123"
        )
        sanitized = sanitize_event_summary(original)
        self.assertNotIn("203.0.113.77", sanitized)
        self.assertNotIn("SuperSecret123", sanitized)


suite = unittest.defaultTestLoader.loadTestsFromTestCase(
    WazuhNormalizationTests
)
result = unittest.TextTestRunner(verbosity=2).run(suite)

print()
print(f"TESTS_RUN={result.testsRun}")
print(f"TEST_FAILURES={len(result.failures)}")
print(f"TEST_ERRORS={len(result.errors)}")

if not result.wasSuccessful():
    print("SYNTHETIC_TEST_RESULT=FAIL")
else:
    print("SYNTHETIC_TEST_RESULT=PASS")
PY

echo
echo "===== POST-TEST FILE HASHES ====="
sha256sum \
  app/services/wazuh_relay.py \
  app/services/event_sanitizer.py \
  app/services/ai_analysis.py

echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

**All 26 passed** (0 failures, 0 errors).

- the six specific classifications and their priority order
- general groups become `other`
- invalid times, time zones, severities, IDs and groups are rejected
- extra fields such as `agent.name`, IPs, `full_log` and `data` are ignored
- what is sent to the AI is only the six allowed fields
- invalid classifications and forbidden fields in Wazuh events are rejected
- classification constraints for other input sources are unchanged
- synthetic IPs and passwords are masked

The SHA256 of the three files was the same before and after the tests.

## 5.2 Checking the Diff

> **Run on: VM 230**

```bash
echo "===== FINAL SOURCE DIFF REVIEW ====="
cd /opt/ai-defense-manager

echo
echo "--- WAZUH RELAY DIFF ---"
diff -u \
  /var/backups/ai-defense-manager/20261123-031115/app/services/wazuh_relay.py \
  app/services/wazuh_relay.py
echo "WAZUH_DIFF_EXIT=$?"

echo
echo "--- AI ANALYSIS DIFF ---"
diff -u \
  /var/backups/ai-defense-manager/20261123-031115/app/services/ai_analysis.py \
  app/services/ai_analysis.py
echo "AI_ANALYSIS_DIFF_EXIT=$?"

echo
echo "--- SANITIZER UNCHANGED CHECK ---"
cmp -s \
  /var/backups/ai-defense-manager/20261123-031115/app/services/event_sanitizer.py \
  app/services/event_sanitizer.py
echo "SANITIZER_UNCHANGED=$?"

echo
echo "===== IMPORT AND CALL-SITE CHECK ====="
venv/bin/python - <<'PY'
import ast
import importlib

modules = (
    "app.services.wazuh_relay",
    "app.services.ai_analysis",
)

for name in modules:
    importlib.import_module(name)
    print(f"IMPORT={name}:PASS")

from pathlib import Path

source = Path("app/services/ai_analysis.py").read_text(encoding="utf-8")
tree = ast.parse(source)

calls = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "_build_event_payload":
            calls.append(node)

print(f"AI_PAYLOAD_HELPER_CALLS={len(calls)}")
if len(calls) != 1:
    raise RuntimeError("Expected exactly one AI payload helper call")

print("IMPORT_AND_CALLSITE=PASS")
PY

echo
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

The diffs of `wazuh_relay.py` and `ai_analysis.py` were within the intended scope, and `event_sanitizer.py` matched the copy exactly. `_build_event_payload()` is called in one place. Exit code `1` from `diff` means there are differences, not an error.

## 5.3 The Shape Received from the Relay

> **Run on: VM 230**

```bash
echo "===== WAZUH RELAY INPUT SHAPE AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- fetch_wazuh_events implementation ---"
nl -ba app/services/wazuh_relay.py | sed -n '88,230p'

echo
echo "--- Wazuh API response extraction and conversion call sites ---"
grep -R -n -E 'affected_items|_convert_alert|fetch_wazuh_events|rule\.groups|rule\.level' \
  app --include='*.py' \
  --exclude-dir='__pycache__'

echo
echo "--- Relay configuration field names only ---"
grep -n -E 'wazuh_relay|wazuh_api' app/core/config.py

echo
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

`fetch_wazuh_events()` calls the Relay's `GET /v1/alerts` and passes each element of the JSON `alerts` array to `_convert_alert()`. Each element is in the following **flat, dot-separated form**.

```json
{
  "timestamp": "2026-11-23T04:00:00+09:00",
  "rule.id": "100103",
  "rule.level": 7,
  "rule.groups": ["postgresql", "error"],
  "rule.description": "PostgreSQL ERROR event detected",
  "decoder.name": "json",
  "agent.id": "001"
}
```

The new `_convert_alert()` requires `rule.groups`. In the next part, Part 49, we check whether the Relay returns this field.

# Closing Notes

In Part 48 we narrowed the Wazuh event conversion to seven fields and fixed what is sent to the AI at six fields.

| Item | Result |
|---|---|
| Copies | `/var/backups/ai-defense-manager/20261123-031115` (5 files, SHA256 match) |
| Classification | seven classifications using `rule.groups` (with priority order) |
| Changed files | `wazuh_relay.py`, `ai_analysis.py` (rewritten via AST; passed syntax check) |
| Unit tests | all 26 passed |
| Service | not restarted (still running the old code) |

In the next part, Part 49, we fix the Relay on VM 220 so that it returns `rule.groups`.

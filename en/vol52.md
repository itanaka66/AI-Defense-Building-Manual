---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 52: Fetching Real Alerts and Fixing the Relay's 502"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 52 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 51 we checked TLS and authentication from VM 230 to the Relay on VM 220. Here we fetch real Wazuh alerts.

1. Using `GET /api/v1/wazuh/events` on VM 230, fetch alerts once (up to 10, from the last 15 minutes)
2. The Relay returned `HTTP 502`, so investigate the cause without displaying alert values
3. Fix the cause (`relay.py` lacks `import re`) with one line and restart the Relay
4. Fetch alerts again and confirm they are received as the seven-field allowlist specifies

Alert bodies, IP addresses, descriptions, user names, passwords and tokens are not displayed. No AI analysis, no storing in SQLite and nothing sent to Ollama.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **VM 220**: security-core (root)

# Chapter 1: Fetching Alerts Once

## 1.1 Choosing the API

> **Run on: VM 230**

```bash
echo "===== VM230: LIVE WAZUH FETCH PRE-FLIGHT ====="

cd /opt/ai-defense-manager || true

echo
echo "--- Relay client configuration ---"
grep -n -E \
  'wazuh_relay_base_url|wazuh_relay_ca_file|wazuh_relay_token_file|wazuh_relay_timeout' \
  app/core/config.py

echo
echo "--- Relay fetch limits and normalization ---"
grep -n -E \
  'limit|since_minutes|sanitize|normalize|/v1/alerts|AsyncClient' \
  app/services/wazuh_relay.py

echo
echo "--- API route behavior ---"
sed -n '1,240p' app/api/wazuh.py

echo
echo "NETWORK_REQUEST=NO"
echo "DATABASE_WRITE=NO"
echo "OLLAMA_REQUEST=NO"
echo "SOURCE_MODIFIED=NO"
```

`POST /api/v1/wazuh/analyze` goes as far as Ollama analysis and storing history in SQLite, so we do not use it. We use `GET /api/v1/wazuh/events`, which only fetches.

| Item | Setting |
|---|---|
| API | `GET /api/v1/wazuh/events` |
| Maximum count | 10 |
| Period | 15 minutes |
| Communication with the Relay | HTTPS, CA verification, Bearer authentication |
| AI analysis, storing in SQLite | not done |

## 1.2 Trying to Fetch

Bodies, IP addresses, descriptions and IDs are not displayed; only counts and check results.

> **Run on: VM 230**

```bash
echo "===== VM230: ONE-TIME LIVE WAZUH EVENT FETCH ====="

cd /opt/ai-defense-manager || true

venv/bin/python - <<'PY'
import asyncio
from collections import Counter
from app.services.wazuh_relay import fetch_wazuh_events

async def main():
    events = await fetch_wazuh_events(limit=10, since_minutes=15)

    severity = Counter()
    categories = Counter()
    invalid = 0

    for event in events:
        try:
            severity[str(event.severity)] += 1
            categories[str(event.event_category)] += 1
            if not event.event_id or not event.observed_at:
                invalid += 1
        except Exception:
            invalid += 1

    print("FETCH=SUCCESS")
    print(f"EVENT_COUNT={len(events)}")
    print(f"SEVERITY_COUNTS={dict(sorted(severity.items()))}")
    print(f"CATEGORY_COUNTS={dict(sorted(categories.items()))}")
    print(f"INVALID_EVENT_COUNT={invalid}")
    print(f"LIMIT=10")
    print(f"WINDOW_MINUTES=15")
    print("EVENT_CONTENT_DISPLAYED=NO")
    print("AI_ANALYSIS=NOT_RUN")
    print("OLLAMA_REQUEST=NO")
    print("DATABASE_WRITE=NO")

asyncio.run(main())
PY
```

The Relay returned `HTTP 502`. `/health` was `HTTP 200`, so the path to the Relay and authentication work. `/v1/alerts` is designed to return `HTTP 502` when an exception occurs while querying the Indexer or processing the results.

# Chapter 2: Investigating the 502

## 2.1 State of the Indexer and the Relay

We make no HTTP requests to the Indexer and look only at state and logs.

> **Run on: VM 220**

```bash
echo "===== VM220: WAZUH INDEXER CONNECTIVITY DIAGNOSTICS ====="

echo
echo "--- Indexer service state ---"
systemctl is-active wazuh-indexer
systemctl show wazuh-indexer \
  -p ActiveState -p SubState -p MainPID -p Result

echo
echo "--- Local TCP listener on port 9200 ---"
ss -lntp | grep -E '127\.0\.0\.1:9200|:9200[[:space:]]' || true

echo
echo "--- Indexer recent service errors ---"
journalctl -u wazuh-indexer --since "30 minutes ago" \
  --no-pager -p err | tail -40

echo
echo "--- Relay recent service logs ---"
journalctl -u ai-defense-relay.service --since "15 minutes ago" \
  --no-pager | tail -40

echo
echo "--- Indexer CA certificate metadata ---"
stat -c 'owner=%U:%G mode=%a size=%s' \
  /etc/credstore/ai-defense-indexer-ca

openssl x509 -in /etc/credstore/ai-defense-indexer-ca \
  -noout -subject -issuer -dates

echo
echo "INDEXER_HTTP_REQUEST=NO"
echo "CREDENTIALS_DISPLAYED=NO"
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
```

Wazuh Indexer is `active (running)`, listens on `127.0.0.1:9200`, and had no errors in the last 30 minutes. The Relay's log recorded `HTTP 502` for `/v1/alerts`. The Relay turns every exception into `indexer_unavailable`, so the log alone does not reveal the cause.

## 2.2 Indexer Search Permissions

As the same user as the Relay (`ai-defense-reader`), we try a search that returns no alert bodies (`size: 0`).

> **Run on: VM 220**

```bash
echo "===== VM220: READ-ONLY ALERT SEARCH PERMISSION TEST ====="

python3 - <<'PY'
import ssl
import json
import base64
import urllib.request
import urllib.error
from pathlib import Path

base = "https://127.0.0.1:9200"
ctx_admin = ssl.create_default_context(
    cafile="/etc/wazuh-indexer/certs/root-ca.pem"
)
ctx_admin.load_cert_chain(
    "/etc/wazuh-indexer/certs/admin.pem",
    "/etc/wazuh-indexer/certs/admin-key.pem"
)

# Refer to the Relay systemd credential. Do not display secrets.
import subprocess
pid = subprocess.check_output(
    ["systemctl", "show", "ai-defense-relay.service",
     "-p", "MainPID", "--value"], text=True
).strip()

env = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
cred_dir = next(
    x.split(b"=", 1)[1].decode()
    for x in env if x.startswith(b"CREDENTIALS_DIRECTORY=")
)
password = (Path(cred_dir) / "indexer-password").read_bytes().strip()
reader_auth = base64.b64encode(
    b"ai-defense-reader:" + password
).decode()

body = json.dumps({
    "size": 0,
    "track_total_hits": False,
    "query": {"match_all": {}}
}).encode()

endpoint = base + "/wazuh-alerts-4.x-*/_search"

tests = [
    ("ADMIN_CERT", ctx_admin, {}),
    ("READER_USER", ssl.create_default_context(
        cafile=str(Path(cred_dir) / "indexer-ca")
    ), {"Authorization": "Basic " + reader_auth}),
]

for name, ctx, headers in tests:
    print("\n---", name, "---")
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            **headers
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            result = json.loads(r.read())
            print("HTTP_STATUS =", r.status)
            print("TIMED_OUT =", result.get("timed_out"))
            print("SHARDS =", result.get("_shards"))
            print("TOTAL_HITS =", result.get("hits", {}).get("total"))
    except urllib.error.HTTPError as e:
        print("HTTP_STATUS =", e.code)
        print("RESPONSE_BODY_DISPLAYED=NO")
    except Exception as e:
        print("ERROR_TYPE =", type(e).__name__)

print("\nSEARCH_SIZE=0")
print("ALERT_DOCUMENTS_RETURNED=NO")
print("PASSWORD_DISPLAYED=NO")
print("CONFIGURATION_CHANGED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

| Checked | Result |
|---|---|
| Search with the admin certificate | `HTTP 200` |
| Search as `ai-defense-reader` | `HTTP 200` |
| Shards | 21/21 succeeded |
| Timeouts | none |

`ai-defense-reader` can search the alert indexes. There is no need to add permissions to the role.

> **Note:** Accessing the Indexer's root URL (`/`) as `ai-defense-reader` gives `403` (no `cluster:monitor/main` permission), but that is separate from searching alerts. We keep the minimal permissions and leave the cluster permissions empty.

## 2.3 Searching Under the Same Conditions as the Relay

The Relay's search uses a 15-minute range on `timestamp`, newest first, and a `_source` limited to the seven fields. We try the same conditions without returning documents.

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY-IDENTICAL QUERY VALIDATION (ZERO DOCUMENTS) ====="

python3 - <<'PY'
import os
import ssl
import json
import base64
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

pid = subprocess.check_output(
    ["systemctl", "show", "ai-defense-relay.service",
     "-p", "MainPID", "--value"], text=True
).strip()

env = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
cred_dir = next(
    x.split(b"=", 1)[1].decode()
    for x in env if x.startswith(b"CREDENTIALS_DIRECTORY=")
)

password = (Path(cred_dir) / "indexer-password").read_bytes().strip()
auth = base64.b64encode(
    b"ai-defense-reader:" + password
).decode()

fields = [
    "timestamp",
    "rule.id",
    "rule.level",
    "rule.groups",
    "rule.description",
    "decoder.name",
    "agent.id",
]

query = {
    "size": 0,
    "track_total_hits": False,
    "sort": [{"timestamp": {"order": "desc"}}],
    "_source": fields,
    "query": {
        "range": {
            "timestamp": {"gte": "now-15m"}
        }
    }
}

ctx = ssl.create_default_context(
    cafile=str(Path(cred_dir) / "indexer-ca")
)

req = urllib.request.Request(
    "https://127.0.0.1:9200/wazuh-alerts-4.x-*/_search",
    data=json.dumps(query).encode(),
    headers={
        "Authorization": "Basic " + auth,
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        result = json.loads(r.read())
        print("HTTP_STATUS =", r.status)
        print("TIMED_OUT =", result.get("timed_out"))
        print("SHARDS =", result.get("_shards"))
        print("RESPONSE_KEYS =", sorted(result.keys()))
        print("HITS_CONTAINER_TYPE =", type(result.get("hits")).__name__)
        print("DOCUMENTS_RETURNED =", len(
            result.get("hits", {}).get("hits", [])
        ))
except urllib.error.HTTPError as e:
    print("HTTP_STATUS =", e.code)
    print("RESPONSE_BODY_DISPLAYED=NO")
except Exception as e:
    print("ERROR_TYPE =", type(e).__name__)

print("\nQUERY_SIZE=0")
print("ALERT_DOCUMENTS_RETURNED=NO")
print("PASSWORD_DISPLAYED=NO")
print("CONFIGURATION_CHANGED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

TLS verification, authentication, index access, the range, the sort order, the field selection and the JSON shape of the response were all normal. **The cause is narrowed down to the processing when the search returns one or more results.**

## 2.4 Checking with Real Alerts Without Looking at Values

We fetch up to 10 real alerts and, in memory only inside VM 220, count only the number, types, results of the masking step and exception class names.

> **Run on: VM 220**

```bash
echo "===== VM220: APPROVED PRIVATE ALERT SANITIZATION TEST ====="

cd /opt/ai-defense-relay

python3 - <<'PY'
import os
import sys
import json
import ssl
import base64
import importlib.util
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from collections import Counter

# systemd credential directory
pid = subprocess.check_output(
    ["systemctl", "show", "ai-defense-relay.service",
     "-p", "MainPID", "--value"], text=True
).strip()

env = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
cred_dir = next(
    x.split(b"=", 1)[1].decode()
    for x in env if x.startswith(b"CREDENTIALS_DIRECTORY=")
)
os.environ["CREDENTIALS_DIRECTORY"] = cred_dir

# Load the actual Relay sanitizer without starting its HTTP server.
spec = importlib.util.spec_from_file_location(
    "relay_audit_module", "/opt/ai-defense-relay/relay.py"
)
relay = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = relay
spec.loader.exec_module(relay)

password = (Path(cred_dir) / "indexer-password").read_bytes().strip()
auth = base64.b64encode(
    b"ai-defense-reader:" + password
).decode()

query = {
    "size": 10,
    "track_total_hits": False,
    "sort": [{"timestamp": {"order": "desc"}}],
    "_source": list(relay.ALLOWED_FIELDS),
    "query": {
        "range": {
            "timestamp": {"gte": "now-15m"}
        }
    }
}

ctx = ssl.create_default_context(
    cafile=str(Path(cred_dir) / "indexer-ca")
)

req = urllib.request.Request(
    relay.INDEXER_URL,
    data=json.dumps(query).encode("utf-8"),
    headers={
        "Authorization": "Basic " + auth,
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
    method="POST",
)

print("QUERY_LIMIT=10")
print("QUERY_WINDOW_MINUTES=15")
print("SOURCE_FIELDS_COUNT=", len(relay.ALLOWED_FIELDS))

try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
        raw = response.read(2 * 1024 * 1024 + 1)
        print("INDEXER_HTTP_STATUS=", response.status)

    if len(raw) > 2 * 1024 * 1024:
        print("RESULT=RESPONSE_TOO_LARGE")
    else:
        data = json.loads(raw)
        hits_container = data.get("hits", {})
        hits = hits_container.get("hits", [])

        print("TIMED_OUT=", data.get("timed_out"))
        print("SHARD_FAILURES=",
              data.get("_shards", {}).get("failed"))
        print("HIT_CONTAINER_TYPE=", type(hits).__name__)
        print("RAW_HIT_COUNT=", len(hits))

        source_types = Counter()
        field_types = {f: Counter() for f in relay.ALLOWED_FIELDS}
        sanitized_ok = 0
        sanitized_rejected = 0
        sanitizer_exceptions = Counter()
        non_dict_hits = 0
        non_dict_sources = 0

        for hit in hits:
            if not isinstance(hit, dict):
                non_dict_hits += 1
                continue

            source = hit.get("_source")
            source_types[type(source).__name__] += 1

            if not isinstance(source, dict):
                non_dict_sources += 1
                continue

            for field in relay.ALLOWED_FIELDS:
                value = source
                for part in field.split("."):
                    if not isinstance(value, dict):
                        value = None
                        break
                    value = value.get(part)

                if value is not None:
                    field_types[field][type(value).__name__] += 1

            try:
                result = relay.sanitize_alert(source)
                if result is None:
                    sanitized_rejected += 1
                else:
                    sanitized_ok += 1
            except Exception as exc:
                sanitizer_exceptions[type(exc).__name__] += 1

        print("SOURCE_TYPES=", dict(source_types))
        print("NON_DICT_HITS=", non_dict_hits)
        print("NON_DICT_SOURCES=", non_dict_sources)
        print("SANITIZED_ACCEPTED=", sanitized_ok)
        print("SANITIZED_REJECTED=", sanitized_rejected)
        print("SANITIZER_EXCEPTION_TYPES=", dict(sanitizer_exceptions))

        print("--- ALLOWED FIELD VALUE TYPES ONLY ---")
        for field in relay.ALLOWED_FIELDS:
            print(field, dict(field_types[field]))

        print("--- RESPONSE STRUCTURE ---")
        print("TOP_LEVEL_TYPE=", type(data).__name__)
        print("HITS_TYPE=", type(hits_container).__name__)

except urllib.error.HTTPError as exc:
    print("INDEXER_HTTP_STATUS=", exc.code)
    print("INDEXER_ERROR_BODY_DISPLAYED=NO")
except Exception as exc:
    print("TEST_EXCEPTION_TYPE=", type(exc).__name__)

print("\nALERT_VALUES_DISPLAYED=NO")
print("PASSWORD_DISPLAYED=NO")
print("DATABASE_WRITES=NO")
print("OLLAMA_REQUESTED=NO")
print("CONFIGURATION_CHANGED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

| Checked | Result |
|---|---|
| Indexer search | `HTTP 200` |
| Alerts fetched | 1 |
| Types of the seven fields | all as expected |
| Masking step (`sanitize_alert()`) | **`NameError`** |

## 2.5 Imported Modules

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY IMPORT DEPENDENCY AUDIT ====="

cd /opt/ai-defense-relay

echo
echo "--- First 55 lines of relay.py ---"
sed -n '1,55p' relay.py

echo
echo "--- AST import inventory ---"
python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/opt/ai-defense-relay/relay.py")
tree = ast.parse(path.read_text(encoding="utf-8"))

imports = set()

for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for item in node.names:
            imports.add(item.name.split(".")[0])
    elif isinstance(node, ast.ImportFrom) and node.module:
        imports.add(node.module.split(".")[0])

print("IMPORTED_MODULES =", sorted(imports))
print("RE_IMPORTED =", "re" in imports)
print("SOURCE_SYNTAX=PASS")
PY

echo
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "CREDENTIALS_DISPLAYED=NO"
```

**`relay.py` had no `import re`.** `sanitize_alert()` uses `re.fullmatch()` to check `rule.groups`, `rule.id` and `agent.id` (the checks added in Part 49). So processing real alerts caused a `NameError`, and the Relay returned `502`.

# Chapter 3: Adding `import re`

## 3.1 Checking Before the Fix

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY MINIMAL FIX PRECHECK ====="

cd /opt/ai-defense-relay

echo
echo "--- Existing import block ---"
sed -n '1,25p' relay.py

echo
echo "--- Backup directory availability ---"
install -d -m 700 /var/backups/ai-defense-relay
stat -c 'owner=%U:%G mode=%a path=%n' \
  /var/backups/ai-defense-relay

echo
echo "--- Current source hash ---"
sha256sum relay.py

echo
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

Only the following one line is added.

```python
import re
```

## 3.2 Fixing

We make a copy, add only `import re`, and check the syntax. The service is not restarted.

> **Run on: VM 220**

```bash
echo "===== VM220: APPLY MINIMAL RELAY IMPORT FIX ====="

cd /opt/ai-defense-relay

BACKUP_DIR="/var/backups/ai-defense-relay/20261123-import-re-fix"
install -d -m 700 "$BACKUP_DIR"

echo
echo "--- Create backup ---"
cp -a relay.py "$BACKUP_DIR/relay.py"
sha256sum relay.py "$BACKUP_DIR/relay.py"

echo
echo "--- Add only import re ---"
python3 - <<'PY'
from pathlib import Path

p = Path("/opt/ai-defense-relay/relay.py")
text = p.read_text(encoding="utf-8")

if "\nimport re\n" in text:
    raise SystemExit("ABORT: import re already exists")

anchor = "import hmac\n"
if text.count(anchor) != 1:
    raise SystemExit("ABORT: import anchor is not unique")

updated = text.replace(anchor, anchor + "import re\n", 1)
p.write_text(updated, encoding="utf-8")
print("IMPORT_RE_ADDED=YES")
PY

echo
echo "--- Python syntax check ---"
python3 -m py_compile relay.py
echo "PYTHON_COMPILE=PASS"

echo
echo "--- Sanitizer unit test (synthetic data only) ---"
python3 - <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location(
    "relay_test_module", "/opt/ai-defense-relay/relay.py"
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

sample = {
    "timestamp": "2026-11-23T00:00:00Z",
    "rule": {
        "id": "5710",
        "level": 5,
        "groups": ["syslog", "authentication"],
        "description": "synthetic test event",
    },
    "decoder": {"name": "test-decoder"},
    "agent": {"id": "001"},
    "full_log": "MUST_NOT_BE_INCLUDED",
    "data": {"secret": "MUST_NOT_BE_INCLUDED"},
}

result = module.sanitize_alert(sample)

assert result is not None
assert set(result).issubset(set(module.ALLOWED_FIELDS))
assert "full_log" not in result
assert "data" not in result
assert result["rule.groups"] == ["syslog", "authentication"]

print("SANITIZER_TEST=PASS")
print("ALLOWLIST_ONLY=PASS")
print("SENSITIVE_FIELDS_EXCLUDED=PASS")
print("TEST_EVENT_VALUES_DISPLAYED=NO")
PY

echo
echo "--- Final source integrity ---"
sha256sum relay.py "$BACKUP_DIR/relay.py"
stat -c 'owner=%U:%G mode=%a size=%s' relay.py
grep -n '^import re$' relay.py

echo
echo "BACKUP=$BACKUP_DIR/relay.py"
echo "SERVICE_RESTARTED=NO"
echo "INDEXER_REQUESTED=NO"
echo "DATABASE_WRITES=NO"
echo "OLLAMA_REQUESTED=NO"
```

The SHA256 of the copy and of the file just before the fix matched, `import re` went in on line 6, the syntax check passed, and the owner and permissions stayed `root:ai-defense-relay`, `640`.

The test of the masking step in this script did not run in the test environment, because loading `relay.py` requires systemd credentials (this is not a credentials problem).

## 3.3 Testing Only the Masking Step Separately

Without loading credentials, we extract only `sanitize_alert()` and test it with synthetic data.

> **Run on: VM 220**

```bash
echo "===== VM220: ISOLATED SANITIZER UNIT TEST ====="

cd /opt/ai-defense-relay

python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/opt/ai-defense-relay/relay.py")
tree = ast.parse(path.read_text(encoding="utf-8"))

allowed = [
    node for node in tree.body
    if isinstance(node, ast.Assign)
    and any(
        isinstance(target, ast.Name) and target.id == "ALLOWED_FIELDS"
        for target in node.targets
    )
]

sanitizers = [
    node for node in tree.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "sanitize_alert"
]

if len(allowed) != 1 or len(sanitizers) != 1:
    raise RuntimeError("Could not uniquely locate sanitizer dependencies")

isolated = ast.Module(
    body=[
        ast.Import(names=[ast.alias(name="re")]),
        allowed[0],
        sanitizers[0],
    ],
    type_ignores=[],
)
ast.fix_missing_locations(isolated)

namespace = {}
exec(compile(isolated, str(path), "exec"), namespace)

sample = {
    "timestamp": "2026-11-23T00:00:00Z",
    "rule": {
        "id": "5710",
        "level": 5,
        "groups": ["syslog", "authentication"],
        "description": "synthetic test event",
    },
    "decoder": {"name": "test-decoder"},
    "agent": {"id": "001"},
    "full_log": "MUST_NOT_BE_INCLUDED",
    "data": {"secret": "MUST_NOT_BE_INCLUDED"},
}

result = namespace["sanitize_alert"](sample)

assert result is not None, "Valid synthetic event was rejected"
assert set(result).issubset(set(namespace["ALLOWED_FIELDS"]))
assert "full_log" not in result
assert "data" not in result
assert result["rule.groups"] == ["syslog", "authentication"]

print("SANITIZER_VALID_EVENT=PASS")
print("ALLOWLIST_ONLY=PASS")
print("SENSITIVE_FIELDS_EXCLUDED=PASS")
print("SYNTHETIC_VALUES_DISPLAYED=NO")
PY

echo
echo "===== SOURCE INTEGRITY ====="
python3 -m py_compile relay.py
echo "PYTHON_COMPILE=PASS"
sha256sum relay.py
stat -c 'owner=%U:%G mode=%a size=%s' relay.py

echo "SERVICE_RESTARTED=NO"
echo "LIVE_INDEXER_REQUESTED=NO"
```

Accepting a valid synthetic event, returning only allowlisted fields, removing `full_log` and `data`, the syntax, and the owner and permissions all passed.

## 3.4 Restarting the Relay

> **Run on: VM 220**

```bash
echo "===== VM220: RESTART AI DEFENSE RELAY ====="

systemctl restart ai-defense-relay.service

echo
echo "--- Service status ---"
systemctl is-active ai-defense-relay.service
systemctl show ai-defense-relay.service \
  -p MainPID \
  -p ActiveState \
  -p SubState \
  -p User \
  -p Group

echo
echo "--- Listener verification ---"
ss -lntp '( sport = :8765 )'

echo
echo "--- Recent service journal (no credentials) ---"
journalctl -u ai-defense-relay.service -n 15 --no-pager \
  -o short-iso-precise

echo
echo "--- Source integrity ---"
sha256sum /opt/ai-defense-relay/relay.py

echo
echo "INDEXER_REQUESTED=NO"
echo "DATABASE_REQUESTED=NO"
echo "OLLAMA_REQUESTED=NO"
```

The service was `active (running)` with new PID `25723`. Right after the restart, `ss` did not show port 8765 listening, so we check again.

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY LISTENER DIAGNOSTICS ====="

echo
echo "--- systemd detailed status ---"
systemctl status ai-defense-relay.service --no-pager -l

echo
echo "--- Process state ---"
ps -p 25723 -o pid,ppid,user,group,stat,etime,comm

echo
echo "--- All TCP listeners ---"
ss -lntp

echo
echo "--- Relay process file descriptors (socket metadata only) ---"
find /proc/25723/fd -maxdepth 1 -type l -printf '%f -> %l\n' 2>/dev/null \
  | grep 'socket:' || true

echo
echo "--- Startup journal since 06:50 UTC ---"
journalctl -u ai-defense-relay.service \
  --since "2026-11-23 06:50:00 UTC" \
  --no-pager -o short-iso-precise

echo
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
echo "INDEXER_REQUESTED=NO"
echo "DATABASE_REQUESTED=NO"
echo "OLLAMA_REQUESTED=NO"
```

It listens on `192.168.0.220:8765`, and the startup log contains `AI Defense Relay listening on 192.168.0.220:8765`. The earlier `ss` was simply too soon.

# Chapter 4: Fetching Alerts Again

## 4.1 `/health`

> **Run on: VM 230**

```bash
echo "===== VM230: POST-RESTART RELAY HEALTH CHECK ====="

python3 - <<'PY'
import json
import ssl
import urllib.request
from pathlib import Path

base = "https://192.168.0.220:8765"
credentials = Path("/etc/ai-defense-manager/credentials")
ca_file = credentials / "relay-ca.crt"
token_file = credentials / "relay-api.token"

if not ca_file.is_file() or not token_file.is_file():
    raise RuntimeError("Required credential file is unavailable")

token = token_file.read_text(encoding="utf-8").strip()
if not token:
    raise RuntimeError("Relay token is empty")

context = ssl.create_default_context(cafile=str(ca_file))
request = urllib.request.Request(
    base + "/health",
    headers={"Authorization": "Bearer " + token},
    method="GET",
)

try:
    with urllib.request.urlopen(
        request, context=context, timeout=10
    ) as response:
        body = response.read(4096)
        print("HTTP_STATUS =", response.status)
        print("TLS_VERIFICATION = PASS")
        print("BEARER_AUTH = PASS")
        try:
            print("BODY =", json.dumps(
                json.loads(body.decode("utf-8")),
                ensure_ascii=False
            ))
        except Exception:
            print("BODY_JSON = INVALID")
except Exception as exc:
    print("HEALTH_CHECK = FAILED")
    print("ERROR_TYPE =", type(exc).__name__)
    if hasattr(exc, "code"):
        print("HTTP_STATUS =", exc.code)

print("ALERTS_ENDPOINT_REQUESTED = NO")
print("INDEXER_SEARCH_REQUESTED = NO")
print("DATABASE_REQUESTED = NO")
print("OLLAMA_REQUESTED = NO")
PY
```

`HTTP 200`; TLS verification and Bearer authentication passed; the response was `{"status":"ok"}`.

## 4.2 Fetching Alerts

We fetch once, up to 10, from the last 15 minutes. Bodies are not displayed; only the count and the results of the allowed-field check.

> **Run on: VM 230**

```bash
echo "===== VM230: POST-FIX LIVE ALERT RETRIEVAL ====="

python3 - <<'PY'
import json
import ssl
import urllib.request
import urllib.error
from pathlib import Path

BASE = "https://192.168.0.220:8765"
CREDENTIALS = Path("/etc/ai-defense-manager/credentials")
ALLOWED = {
    "timestamp",
    "rule.id",
    "rule.level",
    "rule.groups",
    "rule.description",
    "decoder.name",
    "agent.id",
}

token = (CREDENTIALS / "relay-api.token").read_text().strip()
ca_file = CREDENTIALS / "relay-ca.crt"

context = ssl.create_default_context(cafile=str(ca_file))
url = BASE + "/v1/alerts?limit=10&since_minutes=15"
request = urllib.request.Request(
    url,
    headers={"Authorization": "Bearer " + token},
    method="GET",
)

try:
    with urllib.request.urlopen(
        request, context=context, timeout=20
    ) as response:
        status = response.status
        raw = response.read(2 * 1024 * 1024 + 1)

    print("HTTP_STATUS =", status)
    print("TLS_VERIFICATION = PASS")
    print("RESPONSE_SIZE_WITHIN_LIMIT =", len(raw) <= 2 * 1024 * 1024)

    if len(raw) > 2 * 1024 * 1024:
        print("RESULT = RESPONSE_TOO_LARGE")
    else:
        payload = json.loads(raw.decode("utf-8"))
        print("JSON_VALID = PASS")

        candidates = []

        def inspect(value, path="$"):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == "alerts" and isinstance(child, list):
                        candidates.append((path + ".alerts", child))
                    else:
                        inspect(child, path + "." + str(key))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    if isinstance(child, dict):
                        inspect(child, path + "[" + str(index) + "]")

        inspect(payload)

        if not isinstance(payload, dict):
            print("RESPONSE_SHAPE = UNEXPECTED")
        else:
            print("TOP_LEVEL_KEYS =", sorted(payload.keys()))

        if len(candidates) == 1:
            path, events = candidates[0]
            print("ALERT_COUNT =", len(events))

            valid = 0
            invalid = 0
            for event in events:
                if not isinstance(event, dict):
                    invalid += 1
                    continue
                if set(event).issubset(ALLOWED):
                    valid += 1
                else:
                    invalid += 1

            print("ALLOWLIST_VALID_EVENTS =", valid)
            print("INVALID_EVENTS =", invalid)
            print("ALLOWLIST_VALIDATION =", "PASS" if invalid == 0 else "FAIL")
            print("EVENT_VALUES_DISPLAYED = NO")
        else:
            print("ALERT_LIST_COUNT =", len(candidates))
            print("RESPONSE_SHAPE = NEEDS_REVIEW")

except urllib.error.HTTPError as exc:
    print("HTTP_STATUS =", exc.code)
    print("REQUEST_RESULT = HTTP_ERROR")
except Exception as exc:
    print("REQUEST_RESULT = FAILED")
    print("ERROR_TYPE =", type(exc).__name__)

print("DATABASE_WRITES = NO")
print("OLLAMA_REQUESTED = NO")
print("AI_ANALYSIS_REQUESTED = NO")
PY
```

| Checked | Result |
|---|---|
| HTTPS, TLS verification | passed |
| Bearer authentication | passed |
| HTTP response | `200` |
| JSON shape | passed |
| Alerts fetched | 1 |
| Allowed-field check | 1 passed |
| Invalid events | 0 |
| Removal of `full_log` etc. | maintained |
| DB writes, Ollama inference | none |

# Closing Notes

In Part 52, VM 230 became able to receive real Wazuh alerts with only the allowed fields.

| Item | Result |
|---|---|
| Cause of the 502 | `relay.py` lacked `import re`, so `sanitize_alert()` raised `NameError` |
| Fix | added the one line `import re`; made a copy, tested the syntax and the masking step, and restarted the Relay |
| Indexer permissions | unchanged (`ai-defense-reader` can search; cluster permissions remain empty) |
| Fetching alerts | `HTTP 200`, 1 alert, passed the allowlist check |

The path is Wazuh Indexer (VM 220 `127.0.0.1:9200`) → Relay (VM 220 `:8765`, narrowed to seven fields) → AI Defense Manager (VM 230 `:8000`). In the next part, Part 53, we check how received alerts lead to analysis, storage and defense proposals inside VM 230.

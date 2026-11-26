---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 49: Narrowing the Fields Returned by the Relay to Seven"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 49 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 48 we changed the AI Defense Manager on VM 230 to receive Wazuh events narrowed to seven fields and to classify them by `rule.groups`. Here we make the data returned by the relay API (Relay) on VM 220 match that.

1. Identify the Relay listening on port 8765 and its implementation file
2. Compare the data the Relay returns with the shape VM 230 expects
3. Save a copy of `relay.py`, then limit the returned fields to seven and add a check of `rule.groups`
4. Check the diff and restart only the Relay service

Apart from restarting the Relay, there is no communication with the Indexer and no actual communication from VM 230.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)

# Chapter 1: Examining the Relay

## 1.1 The Service on Port 8765

Authentication details and process arguments are not displayed.

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY ENDPOINT SERVICE AUDIT ====="

echo
echo "--- TCP listener on port 8765 ---"
ss -ltnp '( sport = :8765 )'

echo
echo "--- Candidate service units ---"
systemctl list-units --type=service --all --no-legend |
  grep -Ei 'relay|wazuh|filter' |
  sed -E 's/[[:space:]]+/ /g'

echo
echo "--- Candidate installed unit files ---"
systemctl list-unit-files --type=service --no-legend |
  grep -Ei 'relay|wazuh|filter'

echo
echo "NO_SERVICE_RESTART=YES"
echo "NO_NETWORK_REQUESTS=YES"
echo "NO_CONFIGURATION_CHANGES=YES"
```

What listens on `192.168.0.220:8765` is the running `ai-defense-relay.service`.

## 1.2 The Implementation File

> **Run on: VM 220**

```bash
echo "===== VM220: AI DEFENSE RELAY IMPLEMENTATION LOCATION ====="

echo
echo "--- Service metadata (no command arguments or environment) ---"
systemctl show ai-defense-relay.service \
  -p MainPID \
  -p User \
  -p Group \
  -p WorkingDirectory \
  -p FragmentPath

echo
echo "--- Running process executable and working directory ---"
RELAY_PID="$(systemctl show ai-defense-relay.service -p MainPID --value)"
if [ -n "$RELAY_PID" ] && [ "$RELAY_PID" != "0" ]; then
  readlink -f "/proc/$RELAY_PID/exe"
  readlink -f "/proc/$RELAY_PID/cwd"
  echo
  echo "--- Python source files under service working directory ---"
  RELAY_CWD="$(readlink -f "/proc/$RELAY_PID/cwd")"
  find "$RELAY_CWD" -maxdepth 3 -type f -name '*.py' -printf '%p\n' 2>/dev/null | sort
else
  echo "RELAY_MAINPID_UNAVAILABLE"
fi

echo
echo "NO_SERVICE_RESTART=YES"
echo "NO_NETWORK_REQUESTS=YES"
echo "NO_CONFIGURATION_CHANGES=YES"
```

The implementation was `/opt/ai-defense-relay/relay.py`.

## 1.3 How the Returned Data Is Built

Rather than the whole file, we extract only the parts related to route definitions, JSON generation and event normalization. Tokens and secret keys are not displayed.

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY RESPONSE CONTRACT REVIEW ====="

cd /opt/ai-defense-relay

echo
echo "--- Endpoint and response construction locations ---"
grep -n -E \
  '(/v1/alerts|alerts|JSONResponse|jsonify|return |rule\.groups|rule\.level|rule\.id|decoder\.name|agent\.id)' \
  relay.py

echo
echo "--- Source with line numbers ---"
nl -ba relay.py | sed -n '1,280p'

echo
echo "NO_SERVICE_RESTART=YES"
echo "NO_NETWORK_REQUESTS=YES"
echo "NO_CONFIGURATION_CHANGES=YES"
```

The new `_convert_alert()` on VM 230 requires `rule.groups`, but the Relay was in the following state.

| Field | Now | Needed |
|---|---|---|
| `timestamp`, `agent.id`, `rule.level`, `rule.description`, `rule.id`, `decoder.name` | retrieved and returned | keep |
| `rule.groups` | **not retrieved** | add |
| `agent.ip`, `agent.name`, `manager.name`, `location` | retrieved and returned | **remove** |

# Chapter 2: Fixing the Relay

## 2.1 Saving a Copy

The service is not stopped and there is no communication.

> **Run on: VM 220**

```bash
echo "===== AI DEFENSE RELAY PRE-CHANGE BACKUP ====="

SOURCE="/opt/ai-defense-relay/relay.py"
BACKUP_DIR="/var/backups/ai-defense-relay"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$BACKUP_DIR/$STAMP"

echo
echo "--- Source metadata ---"
stat -c 'PATH=%n OWNER=%U:%G MODE=%a SIZE=%s' "$SOURCE"

echo
echo "--- Create backup ---"
mkdir -p "$BACKUP"
cp -a "$SOURCE" "$BACKUP/relay.py"

echo
echo "--- SHA256 verification ---"
SOURCE_HASH="$(sha256sum "$SOURCE" | awk '{print $1}')"
BACKUP_HASH="$(sha256sum "$BACKUP/relay.py" | awk '{print $1}')"

echo "SOURCE_SHA256=$SOURCE_HASH"
echo "BACKUP_SHA256=$BACKUP_HASH"

if [ "$SOURCE_HASH" = "$BACKUP_HASH" ]; then
  echo "BACKUP_INTEGRITY=PASS"
else
  echo "BACKUP_INTEGRITY=FAIL"
fi

echo
echo "--- Backup metadata ---"
stat -c 'PATH=%n OWNER=%U:%G MODE=%a SIZE=%s' "$BACKUP/relay.py"

echo
echo "BACKUP_PATH=$BACKUP"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "SOURCE_MODIFIED=NO"
```

The copy is `/var/backups/ai-defense-relay/20261123-044701/relay.py`; its SHA256 matches the original, and the owner and permissions are `root:ai-defense-relay`, `640`.

## 2.2 Reading the Parts to Fix

> **Run on: VM 220**

```bash
echo "===== AI DEFENSE RELAY: PRE-EDIT SOURCE REVIEW ====="

cd /opt/ai-defense-relay

echo
echo "--- Field allowlist and sanitizer definitions ---"
grep -n -E 'ALLOWED_FIELDS|def sanitize_alert|def .*alert|def .*event' relay.py

echo
echo "--- Relevant source sections ---"
nl -ba relay.py | sed -n '1,250p'

echo
echo "--- Backup integrity recheck ---"
sha256sum relay.py \
  /var/backups/ai-defense-relay/20261123-044701/relay.py

echo
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
```

## 2.3 Fixing

We fix the following three things.

1. Limit `ALLOWED_FIELDS` to seven fields and stop retrieving `agent.ip`, `agent.name`, `manager.name` and `location`
2. Add checks to `sanitize_alert()`, such as that `rule.groups` is a list. Invalid events are dropped while processing of other valid events continues
3. Do not include dropped events in the returned `alerts`

`decoder.name` is checked and passed through by the Relay, but VM 230 does not send it to the AI. After checking the copy we make the fix, and before writing we run a syntax check and a test with synthetic data.

> **Run on: VM 220**

```bash
echo "===== AI DEFENSE RELAY: SAFE NORMALIZATION PATCH ====="

cd /opt/ai-defense-relay

python3 - <<'PY'
import ast
import hashlib
import os
import re
import stat
import tempfile
from pathlib import Path

source_path = Path("/opt/ai-defense-relay/relay.py")
backup_path = Path(
    "/var/backups/ai-defense-relay/20261123-044701/relay.py"
)

original = source_path.read_text(encoding="utf-8")
backup = backup_path.read_bytes()

def sha256(data):
    return hashlib.sha256(data).hexdigest()

if sha256(original.encode("utf-8")) != sha256(backup):
    raise RuntimeError("Backup/source mismatch; refusing modification")

old_fields = '''ALLOWED_FIELDS = (
    "timestamp",
    "agent.id",
    "agent.ip",
    "agent.name",
    "manager.name",
    "rule.level",
    "rule.description",
    "rule.id",
    "location",
    "decoder.name",
)'''

new_fields = '''ALLOWED_FIELDS = (
    "timestamp",
    "rule.id",
    "rule.level",
    "rule.groups",
    "rule.description",
    "decoder.name",
    "agent.id",
)'''

old_function = '''def sanitize_alert(source):
    result = {}
    for field in ALLOWED_FIELDS:
        value = source
        for part in field.split("."):
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(part)

        if value is None:
            continue

        if field == "rule.level":
            if isinstance(value, int) and not isinstance(value, bool):
                result[field] = value
        elif isinstance(value, str):
            result[field] = value[:512]

    return result'''

new_function = '''def sanitize_alert(source):
    if not isinstance(source, dict):
        return None

    result = {}

    for field in ALLOWED_FIELDS:
        value = source
        for part in field.split("."):
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(part)

        if value is None:
            continue

        if field == "timestamp":
            if not isinstance(value, str) or not value or len(value) > 64:
                return None
            result[field] = value

        elif field == "rule.level":
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 16
            ):
                return None
            result[field] = value

        elif field == "rule.groups":
            if not isinstance(value, list) or len(value) > 32:
                return None

            normalized_groups = []
            for group in value:
                if not isinstance(group, str):
                    return None
                group = group.strip().lower()
                if (
                    not group
                    or len(group) > 64
                    or not re.fullmatch(r"[a-z0-9_-]+", group)
                ):
                    return None
                normalized_groups.append(group)

            result[field] = normalized_groups

        elif field in ("rule.id", "agent.id"):
            if not isinstance(value, str):
                return None
            if not re.fullmatch(r"[0-9]{1,16}", value):
                return None
            result[field] = value

        elif field == "rule.description":
            if not isinstance(value, str):
                return None
            result[field] = value[:512]

        elif field == "decoder.name":
            if not isinstance(value, str) or len(value) > 64:
                return None
            result[field] = value

    # VM230 requires timestamp, rule.level, and rule.groups.
    if not all(
        field in result
        for field in ("timestamp", "rule.level", "rule.groups")
    ):
        return None

    return result'''

old_alerts = '''            alerts = [
                sanitize_alert(hit.get("_source", {}))
                for hit in hits
                if isinstance(hit.get("_source"), dict)
            ]'''

new_alerts = '''            alerts = [
                sanitized
                for hit in hits
                if isinstance(hit.get("_source"), dict)
                for sanitized in [sanitize_alert(hit["_source"])]
                if sanitized is not None
            ]'''

for label, old, new in (
    ("allowlist", old_fields, new_fields),
    ("sanitizer", old_function, new_function),
    ("alerts filter", old_alerts, new_alerts),
):
    count = original.count(old)
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one {label} target; found {count}"
        )

proposed = original.replace(old_fields, new_fields)
proposed = proposed.replace(old_function, new_function)
proposed = proposed.replace(old_alerts, new_alerts)

# Syntax validation before writing.
compile(proposed, str(source_path), "exec")
tree = ast.parse(proposed)

# Isolated synthetic tests of the actual proposed sanitizer.
selected = []
for node in tree.body:
    if isinstance(node, (ast.Assign, ast.FunctionDef)):
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name)
                and target.id == "ALLOWED_FIELDS"
                for target in node.targets
            ):
                selected.append(node)
        elif node.name == "sanitize_alert":
            selected.append(node)

namespace = {"re": re}
exec(
    compile(
        ast.Module(body=selected, type_ignores=[]),
        "<isolated-sanitizer-test>",
        "exec",
    ),
    namespace,
)

allowed = namespace["ALLOWED_FIELDS"]
sanitize = namespace["sanitize_alert"]

expected = (
    "timestamp",
    "rule.id",
    "rule.level",
    "rule.groups",
    "rule.description",
    "decoder.name",
    "agent.id",
)
assert allowed == expected, allowed

sample = {
    "timestamp": "2026-11-23T04:00:00+09:00",
    "agent": {
        "id": "001",
        "ip": "203.0.113.10",
        "name": "must-not-leak",
    },
    "manager": {"name": "must-not-leak"},
    "location": "must-not-leak",
    "rule": {
        "id": "100103",
        "level": 7,
        "groups": [" PostgreSQL ", "ERROR"],
        "description": "PostgreSQL ERROR event detected",
    },
    "decoder": {"name": "json"},
    "full_log": "must-not-leak",
    "data": {"command": "must-not-leak"},
}

result = sanitize(sample)
assert result is not None
assert set(result) == set(expected), set(result)
assert result["rule.groups"] == ["postgresql", "error"]
assert result["agent.id"] == "001"
assert result["decoder.name"] == "json"

assert sanitize({**sample, "rule": {
    **sample["rule"], "groups": ["valid", "bad group"]
}}) is None

assert sanitize({**sample, "rule": {
    **sample["rule"], "groups": ["x" * 65]
}}) is None

assert sanitize({**sample, "rule": {
    **sample["rule"], "groups": ["valid"] * 33
}}) is None

assert sanitize({**sample, "rule": {
    **sample["rule"], "level": True
}}) is None

assert sanitize({**sample, "rule": {
    **sample["rule"], "groups": "postgresql"
}}) is None

assert sanitize({"rule": sample["rule"]}) is None

print("PREWRITE_SYNTAX=PASS")
print("PREWRITE_ALLOWLIST=PASS")
print("SYNTHETIC_VALID_EVENT=PASS")
print("SYNTHETIC_FORBIDDEN_FIELDS=PASS")
print("SYNTHETIC_INVALID_GROUPS_REJECTED=PASS")
print("SYNTHETIC_INVALID_LEVEL_REJECTED=PASS")
print("SYNTHETIC_REQUIRED_FIELDS=PASS")

# Preserve existing owner and mode; replace atomically.
metadata = source_path.stat()
fd, temporary_name = tempfile.mkstemp(
    prefix=".relay.py.",
    suffix=".tmp",
    dir=str(source_path.parent),
)

try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(proposed)
        handle.flush()
        os.fsync(handle.fileno())

    os.chown(temporary_name, metadata.st_uid, metadata.st_gid)
    os.chmod(temporary_name, stat.S_IMODE(metadata.st_mode))
    os.replace(temporary_name, source_path)

    directory_fd = os.open(source_path.parent, os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)

except Exception:
    try:
        os.unlink(temporary_name)
    except FileNotFoundError:
        pass
    raise

final = source_path.read_bytes()
compile(final, str(source_path), "exec")

if final != proposed.encode("utf-8"):
    raise RuntimeError("Post-write content mismatch")

if sha256(backup) != sha256(backup_path.read_bytes()):
    raise RuntimeError("Backup integrity changed")

print("SOURCE_WRITE=PASS")
print("POSTWRITE_SYNTAX=PASS")
print("BACKUP_INTEGRITY=PASS")
print("SOURCE_SHA256=" + sha256(final))
print("BACKUP_SHA256=" + sha256(backup))
print("SOURCE_OWNER_MODE=" + oct(stat.S_IMODE(source_path.stat().st_mode)))
print("PATCH_RESULT=SUCCESS")
PY

echo
echo "===== SERVICE AND NETWORK SAFETY ====="
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

| Checked | Result |
|---|---|
| Syntax and allowlist before writing | passed |
| Synthetic data (valid and invalid events) | passed |
| `ALLOWED_FIELDS` | 7 fields |
| `rule.groups` | checks list type, number of elements, number of characters and character types |
| Fields not returned | `agent.ip`, `agent.name`, `manager.name`, `location`, `full_log`, `data` |
| Owner and permissions | still `root:ai-defense-relay`, `640` |

## 2.4 Checking the Diff

> **Run on: VM 220**

```bash
echo "===== AI DEFENSE RELAY: POST-PATCH REVIEW ====="

cd /opt/ai-defense-relay

echo
echo "--- Source diff ---"
diff -u \
  /var/backups/ai-defense-relay/20261123-044701/relay.py \
  relay.py
DIFF_STATUS=$?
echo "DIFF_EXIT=$DIFF_STATUS"

echo
echo "--- Allowlist ---"
sed -n '19,115p' relay.py

echo
echo "--- Response filtering ---"
sed -n '205,240p' relay.py

echo
echo "--- Syntax check ---"
python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/opt/ai-defense-relay/relay.py")
source = path.read_text(encoding="utf-8")
ast.parse(source, filename=str(path))
compile(source, str(path), "exec")
print("SYNTAX=PASS")
PY

echo
echo "--- File metadata and hashes ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s' relay.py
sha256sum relay.py \
  /var/backups/ai-defense-relay/20261123-044701/relay.py

echo
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

| Checked | Result |
|---|---|
| The seven allowed fields | passed |
| Forbidden fields not retrieved | passed |
| Checking and normalizing `rule.groups` | passed |
| Invalid events dropped and not returned | passed |
| Python syntax check | passed |
| Owner, permissions, copy | passed |

`DIFF_EXIT=1` means there are the intended differences from the copy.

# Chapter 3: Restarting the Relay

## 3.1 Restart

We restart only the Relay service on VM 220.

> **Run on: VM 220**

```bash
echo "===== AI DEFENSE RELAY: APPROVED SERVICE RESTART ====="

echo
echo "--- Restart service ---"
systemctl restart ai-defense-relay.service
RESTART_STATUS=$?
echo "RESTART_COMMAND_EXIT=$RESTART_STATUS"

echo
echo "--- Active state ---"
systemctl is-active ai-defense-relay.service
ACTIVE_STATUS=$?
echo "ACTIVE_CHECK_EXIT=$ACTIVE_STATUS"

echo
echo "--- Service status ---"
systemctl status ai-defense-relay.service --no-pager -l

echo
echo "--- Main process metadata ---"
systemctl show ai-defense-relay.service \
  -p MainPID \
  -p ActiveState \
  -p SubState \
  -p User \
  -p WorkingDirectory

echo
echo "INDEXER_TEST=NOT_PERFORMED"
echo "VM230_RELAY_REQUEST=NOT_PERFORMED"
echo "DATABASE_ACCESSED=NO"
```

| Item | Result |
|---|---|
| Restart | succeeded (exit code `0`) |
| State | `active`, `running` |
| New MainPID | `17052` |
| Running as | `ai-defense-relay` |
| Working directory | `/opt/ai-defense-relay` |

## 3.2 Checking the Listening Port

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY POST-RESTART LISTENER CHECK ====="

echo
echo "--- TCP listener ---"
ss -ltnp '( sport = :8765 )'

echo
echo "--- Process metadata ---"
systemctl show ai-defense-relay.service \
  -p MainPID \
  -p ActiveState \
  -p SubState

echo
echo "--- Source hash ---"
sha256sum /opt/ai-defense-relay/relay.py

echo
echo "INDEXER_TEST=NOT_PERFORMED"
echo "VM230_REQUEST=NOT_PERFORMED"
```

It listens on `192.168.0.220:8765`, systemd shows `active (running)`, and the PIDs of the running process and the service are the same. The Relay on VM 220 is running with the new seven-field processing.

# Closing Notes

In Part 49 we made the data returned by the Relay match the shape VM 230 receives.

| Item | Result |
|---|---|
| Implementation | `/opt/ai-defense-relay/relay.py` |
| Copy | `/var/backups/ai-defense-relay/20261123-044701/relay.py` |
| Returned fields | 7 (`timestamp`, `rule.id`, `rule.level`, `rule.groups`, `rule.description`, `decoder.name`, `agent.id`) |
| Invalid events | dropped and not returned |
| Relay | restarted and running the new code |
| VM 230 | code fixed, but the service has not been restarted yet |

Before restarting the service on VM 230, we change VM 230's address from DHCP to a static address. We do this in the next part, Part 50.

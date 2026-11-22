---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 4: Auditing the Collector and Developing a Hardened Version"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 4 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". We audit the alert-storage Collector put into operation in Part 3 and fix the weaknesses found, working on a test copy without stopping production.

| Approach | Details |
|---|---|
| Audit | Check input validation, the read position and the rotation method against the actual files and code |
| Preservation | Make a complete backup of the code before the improvements |
| Development | Modify only a test copy in `/tmp` and verify it with unit tests |
| Production | Part 4 does not change the production Collector (it is deployed in Part 5) |

## Notation

- Commands and file contents are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Each step begins with "Run on", which says where to run it.
- "Example output" is the actual output from the build. In your environment, inodes, sizes, dates and so on will differ.
- The contents of credentials and the state file are not shown.

## State at the End of Part 3

| Item | State |
|---|---|
| Collector | `/usr/local/lib/wazuh-collector/collector.py` (9,626 bytes) |
| Service | `wazuh-collector.service` (active, enabled) |
| Storage | `incident.alert_events` in the `security_workbench` DB on LXC 109 |
| DB role | `wazuh_collector` (INSERT only) |

# Chapter 1: Auditing the Running Collector

This chapter only examines files. No settings are changed and no services are restarted.

## 1.1 Checking the Second Half of the Code

After the input validation (lines 78–186), check the processing for saving state, resuming and rotation.

**Run on: security-core VM 220 (root)**

```bash
sed -n '187,383p' \
  /usr/local/lib/wazuh-collector/collector.py
```

The audit found that the basic design was sound, but there was room for improvement in the following points.

| Category | Item | Assessment |
|---|---|---|
| Good | Saving the state file | Uses a temporary file, fsync and atomic replacement |
| Good | Order of DB insert and state save | Saves the read position only after the DB insert succeeds |
| Good | Duplicate handling | Treats only `UniqueViolation` as a duplicate |
| Needs work | Input line size | No limit on the length of a line |
| Needs work | Validation of numbers and strings | Accepts booleans as integers; does not remove control characters |
| Needs work | Rotation | Insufficient handling of unread data left in the old file after a switch |

## 1.2 Investigating the Rotation Method

**Run on: security-core VM 220 (root)**

```bash
echo "===== ALERT LOG FILES ====="
ls -lah /var/ossec/logs/alerts/

echo
echo "===== LOGROTATE CONFIG REFERENCES ====="
grep -RniE 'alerts\.json|/var/ossec/logs' \
  /etc/logrotate.conf \
  /etc/logrotate.d/ \
  2>/dev/null

echo
echo "===== ALERT FILE INODE ====="
stat -c 'File=%n Inode=%i Size=%s Modified=%y' \
  /var/ossec/logs/alerts/alerts.json
```

logrotate had no matching configuration, and both `alerts.json` and `alerts.log` had a link count of 2. Check the Wazuh settings and the link relationships.

```bash
echo "===== WAZUH LOGGING CONFIG ====="
grep -nE '^(<global>|</global>|[[:space:]]*<logall>|[[:space:]]*<jsonout_output>|[[:space:]]*<alerts_log>|[[:space:]]*<log_alert_level>)' \
  /var/ossec/etc/ossec.conf

echo
echo "===== ALERT FILE LINK INFORMATION ====="
stat -c '%n device=%d inode=%i links=%h size=%s' \
  /var/ossec/logs/alerts/alerts.json \
  /var/ossec/logs/alerts/alerts.log

echo
echo "===== WAZUH LOG ROTATION REFERENCES ====="
grep -RniE 'alerts\.json|alerts\.log|rotate|compress|log.*size' \
  /var/ossec/etc \
  /var/ossec/bin \
  2>/dev/null | head -80
```

```bash
echo "===== JSON ALERT INODE LINKS ====="
find /var/ossec/logs/alerts -xdev -inum 5409146 \
  -printf '%i %n %s %p\n' 2>/dev/null

echo
echo "===== PLAIN ALERT INODE LINKS ====="
find /var/ossec/logs/alerts -xdev -inum 5398501 \
  -printf '%i %n %s %p\n' 2>/dev/null

echo
echo "===== ARCHIVE DIRECTORY STRUCTURE ====="
find /var/ossec/logs/alerts/2026 \
  -maxdepth 4 -type f \
  -printf '%TY-%Tm-%Td %TH:%TM %s bytes %p\n' \
  2>/dev/null | tail -30
```

Replace the `-inum` value with the inode of your environment shown by the previous command.

| File | inode | Link count |
|---|---:|---:|
| `alerts.json` | 5409146 | 2 |
| `2026/Nov/ossec-alerts-18.json` | 5409146 | 2 |
| `alerts.log` | 5398501 | 2 |

Wazuh **shares the current log and the per-day archive through a hard link**. When the date changes it switches to a new file, and the previous day's file is compressed.

## 1.3 Rotation Settings and Compressed Archives

**Run on: security-core VM 220 (root)**

```bash
echo "===== MONITORD ROTATION SETTINGS ====="
sed -n '270,305p' \
  /var/ossec/etc/internal_options.conf
```

| Setting | Value | Meaning |
|---|---:|---|
| `monitord.day_wait` | 10 seconds | Wait after the daily rotation |
| `monitord.compress` | 1 | Compress |
| `monitord.sign` | 1 | Sign |
| `monitord.rotate_log` | 1 | Rotate daily |
| `monitord.keep_log_days` | 31 | Days to keep |

```bash
echo "===== ARCHIVE FILE COUNTS ====="
find /var/ossec/logs/alerts/2026 \
  -type f \
  | awk '
    /\.json$/ { json_count++ }
    /\.json\.gz$/ { json_gz_count++ }
    /\.log$/ { plain_count++ }
    /\.log\.gz$/ { plain_gz_count++ }
    END {
      print "JSON active/archive:", json_count+0
      print "JSON compressed:", json_gz_count+0
      print "LOG active/archive:", plain_count+0
      print "LOG compressed:", plain_gz_count+0
    }'

echo
echo "===== WAZUH MANAGER SERVICE ====="
systemctl status wazuh-manager --no-pager -l

echo
echo "===== MONITORD PROCESS ====="
pgrep -af 'wazuh-monitord|ossec-monitord' || true
```

> Rotation is not done by a separate systemd service but by the `wazuh-monitord` process inside the Wazuh Manager.

Check the format and integrity of the compressed archives.

```bash
echo "===== COMPRESSED JSON ARCHIVE ====="
file /var/ossec/logs/alerts/2026/Nov/ossec-alerts-17.json.gz

echo
echo "===== COMPRESSED ARCHIVE METADATA ====="
stat -c 'Owner=%U Group=%G Mode=%a Size=%s Modified=%y' \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-17.json.gz
```

```bash
gzip -t /var/ossec/logs/alerts/2026/Nov/ossec-alerts-17.json.gz
echo "gzip exit code: $?"
```

If `gzip exit code: 0` is shown, the compressed data is intact.

## 1.4 Checking the Read Position and Running State

**Run on: security-core VM 220 (root)**

```bash
echo "===== CURRENT ALERT FILE INODE ====="
stat -c 'inode=%i size=%s' \
  /var/ossec/logs/alerts/alerts.json

echo
echo "===== COLLECTOR STATE ====="
python3 - <<'PY'
import json

path = "/var/lib/wazuh-collector/state.json"

with open(path, encoding="utf-8") as f:
    state = json.load(f)

print("State inode:", state["inode"])
print("State offset:", state["offset"])

import os
st = os.stat("/var/ossec/logs/alerts/alerts.json")
print("Current inode:", st.st_ino)
print("Current size:", st.st_size)
print("Offset within current file:", state["offset"] <= st.st_size)
PY
```

It is normal if the inode in the state file is the same as the current `alerts.json` and the read position equals the end of the file.

```bash
echo "===== COLLECTOR SERVICE ====="
systemctl show wazuh-collector.service \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p NRestarts \
  -p MemoryCurrent \
  -p CPUUsageNSec

echo
echo "===== RECENT COLLECTOR LOG ====="
journalctl -u wazuh-collector.service \
  -n 15 --no-pager -o cat
```

At build time it was running stably with 0 restarts and about 18 MiB of memory.

## 1.5 Backing Up Before the Improvements

The backup from Part 3, 9.4 predates the fix to duplicate handling. Its hash differs from the current code, so make a new backup to return to the state before the improvements.

**Run on: security-core VM 220 (root)**

```bash
echo "===== COLLECTOR BACKUP ====="
stat -c 'Owner=%U Group=%G Mode=%a Size=%s Modified=%y' \
  /usr/local/lib/wazuh-collector/collector.py.backup-before-duplicate-handling-20261118

echo
echo "===== BACKUP SHA256 ====="
sha256sum \
  /usr/local/lib/wazuh-collector/collector.py.backup-before-duplicate-handling-20261118

echo
echo "===== CURRENT SOURCE SHA256 ====="
sha256sum \
  /usr/local/lib/wazuh-collector/collector.py
```

| File | Size | SHA256 (prefix) |
|---|---:|---|
| Existing backup (before the duplicate-handling fix) | 9,487 bytes | `132c9e33...` |
| Current code | 9,626 bytes | `931ee3cb...` |

```bash
BACKUP="/usr/local/lib/wazuh-collector/collector.py.backup-pre-hardening-20261118"

if [ -e "$BACKUP" ]; then
    echo "ERROR: Backup already exists. No changes made."
    exit 1
fi

cp -a /usr/local/lib/wazuh-collector/collector.py "$BACKUP"

echo "===== BACKUP VERIFICATION ====="
sha256sum \
  /usr/local/lib/wazuh-collector/collector.py \
  "$BACKUP"

echo
stat -c '%n Owner=%U Group=%G Mode=%a Size=%s' "$BACKUP"
```

If the two SHA256 values match, you can return to the state before the improvements at any time.

## 1.6 Improvement Plan

Based on the audit, we improve the following in this order.

1. `safe_integer()`: do not accept booleans (`true`/`false`) as integers.
2. `safe_text()`: remove control characters and limit the length.
3. `rule_groups`: limit the number of elements and the length of each string.
4. `mitre`: strictly limit the allowed keys and the types and number of values.
5. Put a limit on the length of a line and safely skip huge lines.
6. Make sure nothing is left unread in the old file around a rotation.

All improvements are made on a test copy. First, check the beginning and end of the current code.

```bash
sed -n '1,77p' \
  /usr/local/lib/wazuh-collector/collector.py
```

```bash
tail -n 25 /usr/local/lib/wazuh-collector/collector.py
```

The end is guarded by `if __name__ == "__main__":`, so loading it as a module in tests does not start `run()`.

# Chapter 2: The Test Copy and Stronger Input Validation

## 2.1 Creating the Test Copy

Without touching the production code, create a copy just for testing in `/tmp`.

**Run on: security-core VM 220 (root)**

```bash
TEST_FILE="/tmp/wazuh-collector-hardening-test.py"

if [ -e "$TEST_FILE" ]; then
    echo "ERROR: Test file already exists. No changes made."
    exit 1
fi

cp /usr/local/lib/wazuh-collector/collector.py "$TEST_FILE"
chmod 600 "$TEST_FILE"

echo "===== TEST COPY ====="
stat -c 'Owner=%U Group=%G Mode=%a Size=%s' "$TEST_FILE"

echo
sha256sum \
  /usr/local/lib/wazuh-collector/collector.py \
  "$TEST_FILE"
```

Confirm that the two SHA256 values match. All subsequent changes in Part 4 are made to this test copy.

> Files in `/tmp` may disappear when the VM restarts. Do the work of Part 4 continuously, without restarting in between.

## 2.2 Improving Input Validation

Show the parts to be improved.

```bash
sed -n '78,186p' \
  /tmp/wazuh-collector-hardening-test.py
```

| Function / item | Current problem | Improvement |
|---|---|---|
| `safe_integer` | `True` is accepted as the integer 1 | Reject booleans and accept only decimal digit strings |
| `safe_text` | Allows newlines and control characters | Remove control characters and turn empty strings into None |
| `rule_groups` | No limit on the number of elements | Up to 64 elements of up to 256 characters each (`safe_string_list`) |
| `mitre` | Accepts values of any type and number | Accept only `id`, `tactic` and `technique`, with limits on type and number (`safe_mitre`) |

Replace everything from `safe_integer()` to just before `extract_event()`, and switch the handling of `groups` and `mitre` inside `extract_event()` to the new functions.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

start = source.index("def safe_integer(")
end = source.index("\ndef extract_event(", start)

replacement = '''def safe_integer(value, minimum, maximum):
    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        number = value
    elif isinstance(value, str):
        if not value or not value.isascii() or not value.isdecimal():
            return None
        if len(value) > 20:
            return None
        number = int(value)
    else:
        return None

    if minimum <= number <= maximum:
        return number

    return None


def safe_ip(value):
    if not isinstance(value, str):
        return None

    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def safe_text(value, limit=4096):
    if not isinstance(value, str):
        return None

    value = "".join(
        char for char in value
        if char >= " " and char != "\\\\x7f"
    )

    value = value.strip()

    if not value:
        return None

    return value[:limit]


def safe_string_list(value, max_items=64, item_limit=256):
    if not isinstance(value, list):
        return []

    result = []

    for item in value[:max_items]:
        text = safe_text(item, item_limit)
        if text is not None:
            result.append(text)

    return result


def safe_mitre(value):
    if not isinstance(value, dict):
        return {}

    result = {}

    for key, max_items in (
        ("id", 32),
        ("tactic", 16),
        ("technique", 32),
    ):
        item = value.get(key)

        if isinstance(item, str):
            text = safe_text(item, 256)
            if text is not None:
                result[key] = text

        elif isinstance(item, list):
            cleaned = safe_string_list(
                item,
                max_items=max_items,
                item_limit=256,
            )
            if cleaned:
                result[key] = cleaned

    return result

'''

updated = source[:start] + replacement + source[end:]

old_groups = '''    groups = rule.get("groups", [])
    if not isinstance(groups, list):
        groups = []

    groups = [
        item[:256]
        for item in groups
        if isinstance(item, str)
    ]

    mitre_source = rule.get("mitre", {})
    mitre = {}

    if isinstance(mitre_source, dict):
        for key in ("id", "tactic", "technique"):
            value = mitre_source.get(key)
            if isinstance(value, (str, int, list)):
                mitre[key] = value
'''

new_groups = '''    groups = safe_string_list(
        rule.get("groups", []),
        max_items=64,
        item_limit=256,
    )

    mitre = safe_mitre(rule.get("mitre", {}))
'''

if old_groups not in updated:
    raise SystemExit("ERROR: Expected extraction block not found")

updated = updated.replace(old_groups, new_groups, 1)

if updated == source:
    raise SystemExit("ERROR: No changes made")

path.write_text(updated, encoding="utf-8")
print("Test copy updated successfully")
PY

python3 -m py_compile /tmp/wazuh-collector-hardening-test.py \
  && echo "Python syntax: PASS"
```

It is done when `Test copy updated successfully` and `Python syntax: PASS` are shown.

## 2.3 Unit Tests for Input Validation

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# 1. Integer validation
assert module.safe_integer(True, 0, 16) is None
assert module.safe_integer(False, 0, 16) is None
assert module.safe_integer("5", 0, 16) == 5
assert module.safe_integer("1.5", 0, 16) is None
assert module.safe_integer(-1, 0, 16) is None
print("Integer validation: PASS")

# 2. Text validation
assert module.safe_text("hello\nworld\t!") == "helloworld!"
assert module.safe_text("   ") is None
assert len(module.safe_text("A" * 5000)) == 4096
print("Text validation: PASS")

# 3. List limits
groups = module.safe_string_list(
    ["group"] * 100,
    max_items=64,
    item_limit=256,
)
assert len(groups) == 64
assert module.safe_string_list(["valid", 123]) == ["valid"]
print("List validation: PASS")

# 4. MITRE whitelist and limits
mitre = module.safe_mitre({
    "id": ["T1110"] * 50,
    "tactic": ["Credential Access"],
    "technique": ["Brute Force"],
    "unexpected": "must not survive",
})
assert len(mitre["id"]) == 32
assert "unexpected" not in mitre
assert "tactic" in mitre
print("MITRE validation: PASS")

# 5. Full event extraction
alert = {
    "id": "test-20261118-001",
    "timestamp": "2026-11-18T11:00:00.000+0000",
    "rule": {
        "id": "100106",
        "level": 12,
        "description": "Authentication failure",
        "groups": ["authentication_failed"],
        "mitre": {"id": ["T1110"]},
    },
    "agent": {"id": "004", "name": "postgresql"},
    "manager": {"name": "security-core"},
    "decoder": {"name": "json"},
    "data": {
        "srcip": "192.0.2.10",
        "srcport": "5432",
        "password": "must-not-be-stored",
        "command": "must-not-be-stored",
    },
    "full_log": "must-not-be-stored",
}

event = module.extract_event(alert)

assert event is not None
assert event["rule_id"] == 100106
assert event["rule_level"] == 12
assert event["srcip"] == "192.0.2.10"
assert event["srcport"] == 5432
assert "password" not in event
assert "command" not in event
assert "full_log" not in event
assert set(event.keys()) == {
    "event_id", "event_timestamp", "rule_id", "rule_level",
    "rule_description", "agent_id", "agent_name", "manager_name",
    "decoder_name", "rule_groups", "srcip", "srcport", "mitre",
}
print("Event extraction and sensitive-field exclusion: PASS")

print("ALL TESTS: PASS")
PY
```

```text
Integer validation: PASS
Text validation: PASS
List validation: PASS
MITRE validation: PASS
Event extraction and sensitive-field exclusion: PASS
ALL TESTS: PASS
```

## 2.4 Checking Compatibility with Real Alerts

Check that the stricter validation does not wrongly reject real Wazuh alerts. This only reads the production `alerts.json` and does not connect to the DB.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import sys
import json
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-hardening-test.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

path = Path("/var/ossec/logs/alerts/alerts.json")

total = 0
accepted = 0
rejected = 0
invalid_json = 0

with path.open("rb") as f:
    for line in f:
        if not line.endswith(b"\n"):
            continue

        total += 1

        try:
            alert = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            invalid_json += 1
            continue

        if module.extract_event(alert) is None:
            rejected += 1
        else:
            accepted += 1

print("Total complete lines:", total)
print("Accepted:", accepted)
print("Rejected:", rejected)
print("Invalid JSON:", invalid_json)
print("Accounting:", accepted + rejected + invalid_json)

if total != accepted + rejected + invalid_json:
    sys.exit("ACCOUNTING ERROR")

print("READ-ONLY COMPATIBILITY TEST: PASS")
PY
```

At build time, all 1,406 alerts were accepted (0 rejected, 0 JSON errors), giving `READ-ONLY COMPATIBILITY TEST: PASS`.

# Chapter 3: A Size Limit per Line

## 3.1 Checking the Reading Code

**Run on: security-core VM 220 (root)**

```bash
sed -n '280,390p' \
  /tmp/wazuh-collector-hardening-test.py
```

```bash
sed -n '380,450p' \
  /tmp/wazuh-collector-hardening-test.py
```

Currently a whole line is read with `handle.readline()`, so memory use cannot be limited if there is a very long line. When adding a size limit, the following properties must be kept.

1. A line whose newline has not been written yet is read next time, after rewinding the read position.
2. The state file is updated only after the DB insert succeeds.
3. When the DB fails, the same line can be processed again.
4. A line over the limit is skipped up to the next newline without being held in memory.

Check the line numbers of the places to change.

```bash
grep -nE '^(POLL_INTERVAL|def process_line|def run)' \
  /tmp/wazuh-collector-hardening-test.py
```

## 3.2 Adding the Limit Constants

Set the limit for one line to 1 MiB and the skip unit to 64 KiB.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

old = "POLL_INTERVAL = 1.0\n"
new = """POLL_INTERVAL = 1.0
MAX_ALERT_LINE_BYTES = 1024 * 1024
READ_CHUNK_BYTES = 64 * 1024
"""

if source.count(old) != 1:
    raise SystemExit("ERROR: Expected constant not found exactly once")

path.write_text(source.replace(old, new, 1), encoding="utf-8")

print("Maximum alert line size: 1 MiB")
print("Read chunk size: 64 KiB")
PY

grep -nE '^(POLL_INTERVAL|MAX_ALERT_LINE_BYTES|READ_CHUNK_BYTES)' \
  /tmp/wazuh-collector-hardening-test.py
```

## 3.3 A Reading Function with a Size Limit

The reading function `read_alert_line()` returns one of the following five states.

| State | Meaning | What the Collector does |
|---|---|---|
| `line` | A normal line | Processes it and inserts it into the DB |
| `incomplete` | The newline has not been written yet | Rewinds the read position and waits |
| `oversized` | Skipped to the end of a line that exceeded the limit | Saves the position after the skip |
| `eof` | End of file | Checks for rotation and waits |
| `discarding` | In the middle of skipping a line that exceeded the limit | Continues skipping on the next read |

Add the function just before `process_line()`.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

marker = "\ndef process_line(connection, line):\n"

if source.count(marker) != 1:
    raise SystemExit("ERROR: process_line insertion point not unique")

helper = '''

def read_alert_line(handle, discarding=False):
    """
    Read one bounded alert line.

    Returns:
        ("line", bytes, False)
        ("incomplete", None, False)
        ("oversized", None, False)
        ("eof", None, False)
        ("discarding", None, True)
    """
    if discarding:
        chunk = handle.readline(READ_CHUNK_BYTES)

        if not chunk:
            return "discarding", None, True

        if chunk.endswith(b"\\\\n"):
            return "oversized", None, False

        return "discarding", None, True

    line = handle.readline(MAX_ALERT_LINE_BYTES + 1)

    if not line:
        return "eof", None, False

    if line.endswith(b"\\\\n"):
        if len(line) > MAX_ALERT_LINE_BYTES:
            return "oversized", None, False
        return "line", line, False

    if len(line) <= MAX_ALERT_LINE_BYTES:
        return "incomplete", None, False

    chunk = handle.readline(READ_CHUNK_BYTES)

    if not chunk:
        return "discarding", None, True

    if chunk.endswith(b"\\\\n"):
        return "oversized", None, False

    return "discarding", None, True

'''

updated = source.replace(marker, helper + marker, 1)
path.write_text(updated, encoding="utf-8")

print("Bounded reader added to test copy")
PY

python3 -m py_compile /tmp/wazuh-collector-hardening-test.py \
  && echo "Python syntax: PASS"
```

## 3.4 Fixing the Newline Check

Check the contents of the added function.

```bash
sed -n '335,410p' \
  /tmp/wazuh-collector-hardening-test.py
```

Because `\\\\n` was written inside a string enclosed in `'''`, the file contains `b"\\n"` (two characters: a backslash and `n`). This cannot detect an actual newline. Fix the three places to `b"\n"`.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

old = r'b"\\n"'
new = r'b"\n"'

count = source.count(old)

if count != 3:
    raise SystemExit(
        f"ERROR: Expected 3 escaped newline checks, found {count}"
    )

source = source.replace(old, new)
path.write_text(source, encoding="utf-8")

print("Corrected newline checks:", count)
PY

sed -n '355,390p' /tmp/wazuh-collector-hardening-test.py

python3 -m py_compile /tmp/wazuh-collector-hardening-test.py \
  && echo "Python syntax: PASS"
```

If `Corrected newline checks: 3` is shown, the fix is done.

## 3.5 Unit Tests for the Reading Function

Verify with data in memory, without using the actual log or DB. In the tests, the limit is reduced to 16 bytes and the skip unit to 8 bytes.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util
import io

path = "/tmp/wazuh-collector-hardening-test.py"

spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Set a small limit for testing
module.MAX_ALERT_LINE_BYTES = 16
module.READ_CHUNK_BYTES = 8

read_line = module.read_alert_line

# 1. A normal line
handle = io.BytesIO(b'{"a":1}\n')
status, line, discarding = read_line(handle)
assert status == "line"
assert line == b'{"a":1}\n'
assert discarding is False
print("NORMAL LINE: PASS")

# 2. An incomplete line with no newline
handle = io.BytesIO(b'{"a":1}')
status, line, discarding = read_line(handle)
assert status == "incomplete"
assert line is None
assert discarding is False
handle.seek(0)
assert handle.read() == b'{"a":1}'
print("INCOMPLETE LINE: PASS")

# 3. Discard a line over the limit across multiple chunks
handle = io.BytesIO(b"X" * 40 + b"\n" + b'{"ok":1}\n')
status, line, discarding = read_line(handle)

assert status == "discarding"
assert discarding is True

while status == "discarding":
    status, line, discarding = read_line(handle, discarding=True)

assert status == "oversized"
assert line is None
assert discarding is False
print("OVERSIZED LINE: PASS")

# 4. A normal line right after the oversized line
status, line, discarding = read_line(handle)
assert status == "line"
assert line == b'{"ok":1}\n'
print("LINE AFTER OVERSIZED: PASS")

# 5. EOF
status, line, discarding = read_line(handle)
assert status == "eof"
print("EOF: PASS")

print("\nALL BOUNDED READER TESTS PASSED")
PY
```

It has succeeded if all five items are `PASS` and `ALL BOUNDED READER TESTS PASSED` is shown.

# Chapter 4: Building It into the Reading Loop

## 4.1 Checking and Backing Up the Loop Before the Change

Before building the reading function into `run()`, check how state is saved and loaded and how the initial file is chosen.

**Run on: security-core VM 220 (root)**

```bash
sed -n '390,510p' /tmp/wazuh-collector-hardening-test.py
```

```bash
sed -n '180,255p' /tmp/wazuh-collector-hardening-test.py
```

```bash
sed -n '245,345p' /tmp/wazuh-collector-hardening-test.py
```

`save_state()`, which saves the inode and read position atomically, `load_state()`, which restores the position on restart, and `open_initial_file()`, which looks for the previous file, can be used as they are.

```bash
grep -nE '^(def run|if __name__|POLL_INTERVAL|MAX_ALERT_LINE_BYTES|READ_CHUNK_BYTES)' \
  /tmp/wazuh-collector-hardening-test.py
```

Also back up the test copy itself.

```bash
cp -a \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-loop-20261118

sha256sum \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-loop-20261118
```

## 4.2 The New Reading Loop

Replace `run()` so that it works in the following order.

1. First read one line of the log (`read_alert_line()`).
2. Skip a line over the limit without connecting to the DB, and save the position where the skip ended.
3. Check the DB connection only for normal lines. If the connection fails, go back to the start of that line.
4. Save the read position only after the DB insert succeeds.
5. For a line with no newline yet, go back to the start of the line and wait.

In this order, skipping huge lines makes progress even when the DB is down, and no normal line is lost.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

start = source.index("def run():")
end = source.index('\n\nif __name__ == "__main__":', start)

new_run = '''def run():
    logging.info("Wazuh alert collector starting")

    state = load_state()
    handle, active_inode = open_initial_file(state)

    connection = None
    discarding = False
    discard_start = None

    try:
        while True:
            line_start = handle.tell()

            status, line, _ = read_alert_line(
                handle,
                discarding=discarding,
            )

            if status == "line":
                if connection is None or connection.closed:
                    try:
                        connection = psycopg.connect(**DB_CONFIG)
                        logging.info("PostgreSQL connection established")
                    except Exception as error:
                        handle.seek(line_start)
                        logging.error(
                            "PostgreSQL connection failed: %s",
                            type(error).__name__,
                        )
                        time.sleep(5)
                        continue

                try:
                    process_line(connection, line)
                    save_state(active_inode, handle.tell())
                except Exception as error:
                    handle.seek(line_start)
                    logging.error(
                        "Alert processing failed: %s",
                        type(error).__name__,
                    )

                    try:
                        connection.close()
                    except Exception:
                        pass

                    connection = None
                    time.sleep(5)

                continue

            if status == "incomplete":
                handle.seek(line_start)
                time.sleep(POLL_INTERVAL)
                continue

            if status == "discarding":
                if not discarding:
                    discard_start = line_start
                    logging.warning(
                        "Oversized alert line detected; discarding"
                    )

                discarding = True
                time.sleep(POLL_INTERVAL)
                continue

            if status == "oversized":
                if discard_start is None:
                    discard_start = line_start

                try:
                    save_state(active_inode, handle.tell())
                    logging.warning("Oversized alert line skipped")
                    discarding = False
                    discard_start = None
                except Exception as error:
                    logging.error(
                        "State save failed after oversized line: %s",
                        type(error).__name__,
                    )
                    handle.seek(discard_start)
                    discarding = False
                    discard_start = None
                    time.sleep(POLL_INTERVAL)

                continue

            if status == "eof":
                if discarding:
                    time.sleep(POLL_INTERVAL)
                    continue

                try:
                    current_stat = ALERT_FILE.stat()
                except FileNotFoundError:
                    time.sleep(POLL_INTERVAL)
                    continue

                if current_stat.st_ino != active_inode:
                    handle.close()
                    handle = ALERT_FILE.open("rb")
                    active_inode = current_stat.st_ino

                    save_state(active_inode, 0)
                    logging.info("Switched to new alerts.json inode")

                time.sleep(POLL_INTERVAL)
                continue

    finally:
        handle.close()

        if connection is not None:
            connection.close()
'''

path.write_text(
    source[:start] + new_run + source[end:],
    encoding="utf-8",
)

print("DB-independent oversized-line handling applied")
PY

python3 -m py_compile \
  /tmp/wazuh-collector-hardening-test.py \
  && echo "Python syntax: PASS"
```

```bash
sed -n '415,535p' \
  /tmp/wazuh-collector-hardening-test.py
```

## 4.3 Testing with the DB Down

Run the actual `run()` with a mock that always fails to connect to the DB. `save_state` is also replaced with a mock, so the production state file is not changed.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util
import io

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.MAX_ALERT_LINE_BYTES = 16
module.READ_CHUNK_BYTES = 8

payload = b"X" * 40 + b"\n" + b'{"ok":1}\n'

class TrackingBuffer(io.BytesIO):
    final_position = None

    def close(self):
        self.final_position = self.tell()
        super().close()

handle = TrackingBuffer(payload)
module.load_state = lambda: None
module.open_initial_file = lambda state: (handle, 123)

connect_attempts = []
saved_states = []

def fake_connect(**kwargs):
    connect_attempts.append(True)
    raise OSError("simulated database outage")

def fake_save_state(inode, offset):
    saved_states.append((inode, offset, len(connect_attempts)))

class StopTest(Exception):
    pass

def fake_sleep(seconds):
    if seconds == 5:
        raise StopTest()

original_connect = module.psycopg.connect
original_sleep = module.time.sleep
original_save_state = module.save_state

module.psycopg.connect = fake_connect
module.time.sleep = fake_sleep
module.save_state = fake_save_state

try:
    try:
        module.run()
    except StopTest:
        pass
finally:
    module.psycopg.connect = original_connect
    module.time.sleep = original_sleep
    module.save_state = original_save_state

assert saved_states == [(123, 41, 0)], saved_states
assert len(connect_attempts) == 1, connect_attempts
assert handle.final_position == 41, handle.final_position

print("OVERSIZED LINE PROCESSED WITHOUT DB: PASS")
print("OFFSET SAVED BEFORE DB CONNECTION: PASS")
print("NORMAL LINE POSITION RESTORED ON DB FAILURE: PASS")
print("PRODUCTION STATE FILE NOT MODIFIED BY TEST: PASS")
print("\nALL DB-OUTAGE TESTS PASSED")
PY
```

| Check | Meaning |
|---|---|
| `OVERSIZED LINE PROCESSED WITHOUT DB` | A huge 41-byte line was skipped without connecting to the DB |
| `OFFSET SAVED BEFORE DB CONNECTION` | The position after the skip (41) was saved before connecting to the DB |
| `NORMAL LINE POSITION RESTORED ON DB FAILURE` | The next normal line went back to its start (41) because the DB connection failed |
| `PRODUCTION STATE FILE NOT MODIFIED BY TEST` | The test did not change the production state file |

> **Important:** If you run `run()` without replacing `module.save_state` with a mock, the real `save_state()` rewrites the production state file (`/var/lib/wazuh-collector/state.json`). In tests that use `run()`, always replace the state-saving function.

# Chapter 5: Not Leaving Data Unread at Rotation

## 5.1 The Problem

The current `run()` has two problems related to rotation.

1. If it reaches the end of the file (EOF) while skipping a huge line, it keeps waiting without checking the inode.
2. A line with no newline yet (`incomplete`) goes back to the same position every time, so it never reaches the EOF handling.

In both cases, when Wazuh moves to a new file at the date change, the Collector stays stuck on the old file. The fix is: **if the inode of the current `alerts.json` has changed, discard the incomplete line in the old file with a warning and read the new file from the beginning**. While the inode has not changed, the line may still be being written, so it keeps waiting.

**Run on: security-core VM 220 (root)**

```bash
sed -n '300,414p' \
  /tmp/wazuh-collector-hardening-test.py
```

```bash
sed -n '415,510p' \
  /tmp/wazuh-collector-hardening-test.py
```

Back up before the fix.

```bash
cp -a \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-rotation-20261118

sha256sum \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-rotation-20261118
```

## 5.2 Detecting Rotation at EOF

Open the new file and switch to it only after the state is saved successfully. If saving fails, close the new file and keep waiting on the old file.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

old = '''            if status == "eof":
                if discarding:
                    time.sleep(POLL_INTERVAL)
                    continue

                try:
                    current_stat = ALERT_FILE.stat()
                except FileNotFoundError:
                    time.sleep(POLL_INTERVAL)
                    continue

                if current_stat.st_ino != active_inode:
                    handle.close()
                    handle = ALERT_FILE.open("rb")
                    active_inode = current_stat.st_ino

                    save_state(active_inode, 0)
                    logging.info("Switched to new alerts.json inode")

                time.sleep(POLL_INTERVAL)
                continue
'''

new = '''            if status == "eof":
                try:
                    current_stat = ALERT_FILE.stat()
                except FileNotFoundError:
                    time.sleep(POLL_INTERVAL)
                    continue

                if current_stat.st_ino != active_inode:
                    new_handle = ALERT_FILE.open("rb")
                    try:
                        save_state(current_stat.st_ino, 0)
                    except Exception as error:
                        new_handle.close()
                        logging.error(
                            "State save failed during rotation: %s",
                            type(error).__name__,
                        )
                        time.sleep(POLL_INTERVAL)
                        continue

                    if discarding:
                        logging.warning(
                            "Incomplete oversized line discarded at rotation"
                        )

                    handle.close()
                    handle = new_handle
                    active_inode = current_stat.st_ino
                    discarding = False
                    discard_start = None

                    logging.info("Switched to new alerts.json inode")

                time.sleep(POLL_INTERVAL)
                continue
'''

count = source.count(old)
if count != 1:
    raise SystemExit(f"Expected exactly one EOF block, found {count}")

path.write_text(source.replace(old, new), encoding="utf-8")
print("EOF rotation handling updated")
PY

python3 -m py_compile \
  /tmp/wazuh-collector-hardening-test.py
```

`py_compile` shows nothing when it succeeds, so check again.

```bash
python3 -m py_compile \
  /tmp/wazuh-collector-hardening-test.py \
&& echo "Python syntax: PASS"

sed -n '440,535p' \
  /tmp/wazuh-collector-hardening-test.py
```

## 5.3 Detecting Rotation on an Incomplete Line

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

old = '''            if status == "incomplete":
                handle.seek(line_start)
                time.sleep(POLL_INTERVAL)
                continue
'''

new = '''            if status == "incomplete":
                try:
                    current_stat = ALERT_FILE.stat()
                except FileNotFoundError:
                    handle.seek(line_start)
                    time.sleep(POLL_INTERVAL)
                    continue

                if current_stat.st_ino != active_inode:
                    new_handle = ALERT_FILE.open("rb")
                    try:
                        save_state(current_stat.st_ino, 0)
                    except Exception as error:
                        new_handle.close()
                        handle.seek(line_start)
                        logging.error(
                            "State save failed during incomplete-line rotation: %s",
                            type(error).__name__,
                        )
                        time.sleep(POLL_INTERVAL)
                        continue

                    logging.warning(
                        "Incomplete alert line discarded at rotation"
                    )
                    handle.close()
                    handle = new_handle
                    active_inode = current_stat.st_ino
                    discarding = False
                    discard_start = None
                    logging.info("Switched to new alerts.json inode")
                else:
                    handle.seek(line_start)

                time.sleep(POLL_INTERVAL)
                continue
'''

if source.count(old) != 1:
    raise SystemExit("Expected exactly one incomplete block")

path.write_text(source.replace(old, new), encoding="utf-8")
print("Incomplete-line rotation handling updated")
PY
```

```bash
python3 -m py_compile \
  /tmp/wazuh-collector-hardening-test.py \
&& echo "Python syntax: PASS"

sed -n '455,555p' \
  /tmp/wazuh-collector-hardening-test.py
```

## 5.4 Reporting EOF While Skipping

`read_alert_line()` returned `discarding` when it reached the end of the file while skipping. That never reaches the EOF handling in `run()` (5.2). Change it to return `eof`. The fact that it is skipping is still kept in the `discarding` variable on the `run()` side, so the warning can still be given at rotation.

**Run on: security-core VM 220 (root)**

```bash
sed -n '335,415p' \
  /tmp/wazuh-collector-hardening-test.py
```

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

old = '''        if not chunk:
            return "discarding", None, True
'''

new = '''        if not chunk:
            return "eof", None, False
'''

if source.count(old) != 1:
    raise SystemExit(
        f"Expected exactly one match, found {source.count(old)}"
    )

path.write_text(source.replace(old, new), encoding="utf-8")
print("EOF detection during discard updated")
PY
```

Check the reading function. With `READ_CHUNK_BYTES = 8`, `b"abcdefgh\n"` (9 bytes) does not reach the newline on the first read, giving `discarding`, and gives `oversized` on the second.

```bash
python3 - <<'PY'
import importlib.util
import io

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.MAX_ALERT_LINE_BYTES = 16
module.READ_CHUNK_BYTES = 8

# EOF while discarding
handle = io.BytesIO(b"")
assert module.read_alert_line(handle, True)[0] == "eof"

# Oversized line spanning multiple chunks
handle = io.BytesIO(b"abcdefgh\n")
assert module.read_alert_line(handle, True)[0] == "discarding"
assert module.read_alert_line(handle, True)[0] == "oversized"

# Normal line
handle = io.BytesIO(b'{"ok":1}\n')
status, line, _ = module.read_alert_line(handle)
assert status == "line" and line == b'{"ok":1}\n'

# Incomplete line
handle = io.BytesIO(b'{"ok":1}')
assert module.read_alert_line(handle)[0] == "incomplete"

print("DISCARD EOF TEST: PASS")
print("MULTI-CHUNK DISCARD TEST: PASS")
print("NORMAL LINE TEST: PASS")
print("INCOMPLETE LINE TEST: PASS")
print("ALL READER TESTS PASSED")
PY
```

## 5.5 Integration Test for Rotation

Create an old file and a new file in a temporary directory and check the switch with the actual `run()`. The production log, DB and state file are not touched.

**Run on: security-core VM 220 (root)**

```bash
sed -n '415,550p' \
  /tmp/wazuh-collector-hardening-test.py
```

When an incomplete line remains in the old file:

```bash
python3 - <<'PY'
import importlib.util
import tempfile
from pathlib import Path

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class StopTest(Exception):
    pass

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    old_path = root / "old-alerts.json"
    new_path = root / "alerts.json"

    old_path.write_bytes(b'{"unfinished":')
    new_path.write_bytes(b"")

    old_handle = old_path.open("rb")
    old_inode = old_path.stat().st_ino
    new_inode = new_path.stat().st_ino

    assert old_inode != new_inode

    saved_states = []
    warnings = []

    module.ALERT_FILE = new_path
    module.load_state = lambda: None
    module.open_initial_file = lambda state: (old_handle, old_inode)
    module.save_state = lambda inode, offset: saved_states.append(
        (inode, offset)
    )
    module.logging.warning = lambda message, *args: warnings.append(message)

    def stop_after_switch(seconds):
        raise StopTest()

    original_sleep = module.time.sleep
    module.time.sleep = stop_after_switch

    try:
        try:
            module.run()
        except StopTest:
            pass
    finally:
        module.time.sleep = original_sleep

    assert saved_states == [(new_inode, 0)], saved_states
    assert "Incomplete alert line discarded at rotation" in warnings
    assert old_handle.closed

    print("INCOMPLETE LINE ROTATION: PASS")
    print("NEW INODE STATE SAVED: PASS")
    print("NEW FILE OFFSET ZERO: PASS")
    print("OLD FILE HANDLE CLOSED: PASS")
    print("ALL ROTATION TESTS PASSED")
PY
```

When rotation happens while skipping a huge line (40 bytes are skipped 8 bytes at a time, so the loop continues until the state is saved and then stops):

```bash
python3 - <<'PY'
import importlib.util
import tempfile
from pathlib import Path

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class StopTest(Exception):
    pass

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    old_path = root / "old-alerts.json"
    new_path = root / "alerts.json"

    old_path.write_bytes(b"X" * 40)
    new_path.write_bytes(b"")

    old_handle = old_path.open("rb")
    old_inode = old_path.stat().st_ino
    new_inode = new_path.stat().st_ino

    assert old_inode != new_inode

    module.MAX_ALERT_LINE_BYTES = 16
    module.READ_CHUNK_BYTES = 8
    module.ALERT_FILE = new_path
    module.load_state = lambda: None
    module.open_initial_file = lambda state: (old_handle, old_inode)

    saved_states = []
    warnings = []

    module.save_state = lambda inode, offset: saved_states.append(
        (inode, offset)
    )
    module.logging.warning = lambda message, *args: warnings.append(message)

    original_sleep = module.time.sleep

    def controlled_sleep(seconds):
        if saved_states:
            raise StopTest()

    module.time.sleep = controlled_sleep

    try:
        try:
            module.run()
        except StopTest:
            pass
    finally:
        module.time.sleep = original_sleep

    assert saved_states == [(new_inode, 0)], saved_states
    assert "Incomplete oversized line discarded at rotation" in warnings
    assert old_handle.closed

    print("OVERSIZED LINE ROTATION: PASS")
    print("NEW INODE STATE SAVED: PASS")
    print("NEW FILE OFFSET ZERO: PASS")
    print("OLD FILE HANDLE CLOSED: PASS")
    print("ALL OVERSIZED ROTATION TESTS PASSED")
PY
```

If all four items are `PASS` in both cases, the Collector moves to the new file after rotation whether an incomplete line or a huge line remains.

## 5.6 Checking the Structure

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

tree = ast.parse(source, filename=str(path))

functions = {
    node.name
    for node in ast.walk(tree)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}

required = {
    "safe_integer",
    "safe_text",
    "safe_string_list",
    "safe_mitre",
    "read_alert_line",
    "run",
    "process_line",
    "save_state",
}

missing = required - functions

assert not missing, f"Missing functions: {sorted(missing)}"

print("PYTHON SYNTAX: PASS")
print("REQUIRED FUNCTIONS: PASS")
print("FUNCTION COUNT:", len(functions))
print("TEST FILE SIZE:", len(source.encode("utf-8")))
PY
```

Confirm `PYTHON SYNTAX: PASS` and `REQUIRED FUNCTIONS: PASS`. At build time there were 14 functions and the test copy was 15,201 bytes.

# Chapter 6: Comprehensive Tests for Sensitive Information and Input Validation

## 6.1 Static Checks of the Source Code

Using the syntax tree, check whether `full_log` is referenced, what the INSERT statement targets, and whether there are log strings containing passwords or the like.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
tree = ast.parse(path.read_text(encoding="utf-8"))

for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        value = node.value.lower()

        if "full_log" in value:
            print("FULL_LOG reference:", repr(node.value))

        if "insert into incident.alert_events" in value:
            print("\n=== INSERT SQL ===")
            print(node.value)

        if "logging." in value and any(
            word in value for word in (
                "password", "token", "secret", "credential"
            )
        ):
            print("REVIEW LOG STRING:", repr(node.value))

print("\n=== CHECK COMPLETE ===")
PY
```

Confirm that there is no reference to `full_log`, that the INSERT targets only the 13 permitted columns, and that there are no log strings containing secrets.

Also check the whole source by eye.

```bash
sed -n '1,260p' /tmp/wazuh-collector-hardening-test.py
```

```bash
sed -n '260,460p' /tmp/wazuh-collector-hardening-test.py
```

## 6.2 Testing That Sensitive Information Is Not Stored

Put secret values in every part of an alert and confirm that not a single character of them remains in the data inserted into the DB.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util
import json

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

secret = "DO_NOT_STORE_SECRET_7f3a"

alert = {
    "id": "1795000021.999999",
    "timestamp": "2026-11-18T12:00:00+00:00",
    "full_log": secret,
    "command": secret,
    "password": secret,
    "user": secret,
    "rule": {
        "id": "100106",
        "level": 12,
        "description": "Authentication failure",
        "groups": ["authentication_failed"],
        "mitre": {
            "id": ["T1110"],
            "tactic": ["Credential Access"],
            "technique": ["Brute Force"],
            "unexpected": secret,
        },
        "unexpected": secret,
    },
    "agent": {"id": "004", "name": "postgresql"},
    "manager": {"name": "security-core"},
    "decoder": {"name": "postgresql"},
    "data": {
        "srcip": "192.0.2.10",
        "srcport": "5432",
        "password": secret,
        "query": secret,
        "unexpected": secret,
    },
    "unexpected": secret,
}

event = module.extract_event(alert)

assert event is not None
assert secret not in json.dumps(
    event,
    default=str,
)

expected = {
    "event_id",
    "event_timestamp",
    "rule_id",
    "rule_level",
    "rule_description",
    "agent_id",
    "agent_name",
    "manager_name",
    "decoder_name",
    "rule_groups",
    "srcip",
    "srcport",
    "mitre",
}

assert set(event) == expected
assert event["srcip"] == "192.0.2.10"
assert event["srcport"] == 5432

print("SECRET VALUE EXCLUSION: PASS")
print("UNKNOWN FIELD EXCLUSION: PASS")
print("EXACT 13-FIELD WHITELIST: PASS")
print("VALIDATED IP/PORT EXTRACTION: PASS")
print("SENSITIVE DATA TEST: PASS")
PY
```

## 6.3 Fixing the Control-Character Filter

Check whether control characters are removed.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

value = "alpha\nbeta\r\ngamma\tdelta\x00epsilon\x7fomega"

result = module.safe_text(value)

print("INPUT REPR :", repr(value))
print("OUTPUT REPR:", repr(result))

assert result is not None
assert "\n" not in result
assert "\r" not in result
assert "\t" not in result
assert "\x00" not in result
assert "\x7f" not in result

print("CONTROL CHARACTER FILTER: PASS")
PY
```

At build time, newlines, tabs and NUL were removed, but DEL (`0x7f`) remained (`AssertionError`).

```text
OUTPUT REPR: 'alphabetagammadeltaepsilon\x7fomega'
```

The cause was that `"\\\\x7f"` had been written inside `'''` in 2.2, so the file contained a comparison not with the DEL character but with the four-character string `\x7f` (the same cause as the newline check in 3.4). Check the line concerned.

```bash
grep -n -A 12 -B 3 'def safe_text' \
  /tmp/wazuh-collector-hardening-test.py
```

Replace it with a condition that removes C1 control characters (`0x80`–`0x9f`) as well as DEL. Back up before the fix.

```bash
cp -a /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-control-fix-20261118

python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

old = '        if char >= " " and char != "\\\\x7f"'
new = '        if char >= " " and not 0x7f <= ord(char) <= 0x9f'

count = source.count(old)

if count != 1:
    raise SystemExit(f"Expected exactly one target, found {count}")

path.write_text(
    source.replace(old, new, 1),
    encoding="utf-8",
)

print("TEST SCRIPT ONLY: UPDATED")
print("REPLACEMENTS:", count)
PY
```

Check how the target line is actually written, using `repr`.

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")

for number, line in enumerate(
    path.read_text(encoding="utf-8").splitlines(),
    start=1,
):
    if 125 <= number <= 134:
        print(number, repr(line))
PY
```

If it is shown as follows, the line has the fixed condition.

```text
131 '        if char >= " " and not 0x7f <= ord(char) <= 0x9f'
```

> In the original build, the replacement command showed `Expected exactly one target, found 0`, but this check showed that line 131 already had the fixed content. Even if it says "found 0", always judge the actual content with this `repr` check.

Retest C0, DEL and C1 control characters together.

```bash
python3 - <<'PY'
import importlib.util

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

value = (
    "alpha\nbeta\r\ngamma\tdelta"
    "\x00epsilon\x1f"
    "\x7f"
    "\x80"
    "\x9f"
    "omega"
)

result = module.safe_text(value)

print("OUTPUT REPR:", repr(result))

assert result == "alphabetagammadeltaepsilonomega", repr(result)

print("C0 CONTROL CHARACTERS: PASS")
print("DEL CHARACTER: PASS")
print("C1 CONTROL CHARACTERS: PASS")
print("CONTROL CHARACTER FILTER: PASS")
PY
```

## 6.4 Boundary-Value Tests for Each Validation Function

**Run on: security-core VM 220 (root)**

Strings (`safe_text`):

```bash
python3 - <<'PY'
import importlib.util

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.safe_text("A" * 5000, 4096) == "A" * 4096
assert module.safe_text("  valid text  ") == "valid text"
assert module.safe_text(" \t\n ") is None
assert module.safe_text(None) is None
assert module.safe_text(12345) is None

print("MAXIMUM LENGTH: PASS")
print("WHITESPACE TRIMMING: PASS")
print("EMPTY STRING REJECTION: PASS")
print("NON-STRING REJECTION: PASS")
print("SAFE TEXT VALIDATION: PASS")
PY
```

Integers (`safe_integer`):

```bash
python3 - <<'PY'
import importlib.util

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

safe = module.safe_integer

assert safe(0, 0, 16) == 0
assert safe(16, 0, 16) == 16
assert safe("12", 0, 16) == 12

assert safe(-1, 0, 16) is None
assert safe(17, 0, 16) is None
assert safe(True, 0, 16) is None
assert safe(False, 0, 16) is None

assert safe("1.5", 0, 16) is None
assert safe(" 12", 0, 16) is None
assert safe("+12", 0, 16) is None
assert safe("１２", 0, 16) is None
assert safe("9" * 21, 0, 16) is None
assert safe(None, 0, 16) is None

print("LOWER/UPPER BOUNDARY: PASS")
print("ASCII DECIMAL STRING: PASS")
print("NEGATIVE/OVERFLOW REJECTION: PASS")
print("BOOLEAN REJECTION: PASS")
print("INVALID STRING REJECTION: PASS")
print("SAFE INTEGER VALIDATION: PASS")
PY
```

IP addresses (`safe_ip`):

```bash
python3 - <<'PY'
import importlib.util

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

safe = module.safe_ip

assert safe("192.0.2.10") == "192.0.2.10"
assert safe("2001:0db8:0000:0000:0000:0000:0000:0001") == "2001:db8::1"
assert safe("::1") == "::1"

assert safe("999.999.999.999") is None
assert safe("192.0.2.10/24") is None
assert safe("example.com") is None
assert safe("") is None
assert safe(None) is None
assert safe(12345) is None

print("IPV4 VALIDATION: PASS")
print("IPV6 NORMALIZATION: PASS")
print("INVALID IP REJECTION: PASS")
print("NON-IP INPUT REJECTION: PASS")
print("SAFE IP VALIDATION: PASS")
PY
```

Lists of strings (`safe_string_list`):

```bash
python3 - <<'PY'
import importlib.util

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

safe = module.safe_string_list

assert safe(["alpha", "beta"]) == ["alpha", "beta"]

items = [f"item-{i}" for i in range(100)]
result = safe(items, max_items=64)

assert len(result) == 64
assert result[0] == "item-0"
assert result[-1] == "item-63"

long_result = safe(["A" * 500], item_limit=256)
assert long_result == ["A" * 256]

assert safe("not-a-list") == []
assert safe(None) == []
assert safe([None, 123, "", "valid"]) == ["valid"]

print("NORMAL LIST: PASS")
print("MAXIMUM ITEM COUNT: PASS")
print("MAXIMUM ITEM LENGTH: PASS")
print("INVALID LIST REJECTION: PASS")
print("INVALID ELEMENT FILTERING: PASS")
print("SAFE STRING LIST VALIDATION: PASS")
PY
```

MITRE information (`safe_mitre`):

```bash
python3 - <<'PY'
import importlib.util

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

safe = module.safe_mitre

result = safe({
    "id": ["T1110"],
    "tactic": ["Credential Access"],
    "technique": ["Brute Force"],
    "unexpected": "SECRET_VALUE",
})

assert set(result) == {"id", "tactic", "technique"}
assert result["id"] == ["T1110"]
assert result["tactic"] == ["Credential Access"]
assert result["technique"] == ["Brute Force"]

many = [f"T{i}" for i in range(100)]
limited = safe({"id": many})

assert len(limited["id"]) == 32

assert safe("invalid") == {}
assert safe(None) == {}

print("MITRE KEY WHITELIST: PASS")
print("MITRE VALUE PRESERVATION: PASS")
print("MITRE LIST LIMIT: PASS")
print("INVALID INPUT REJECTION: PASS")
print("SAFE MITRE VALIDATION: PASS")
PY
```

| Function | What was checked |
|---|---|
| `safe_text` | Maximum 4,096 characters, trimming of surrounding whitespace, rejection of whitespace-only strings and non-strings |
| `safe_integer` | Boundary values; rejection of booleans, decimals, signed values, full-width digits and 21 or more digits |
| `safe_ip` | IPv4, IPv6 normalization; rejection of CIDR notation, host names and empty values |
| `safe_string_list` | Maximum 64 elements of 256 characters each; invalid elements excluded |
| `safe_mitre` | Only three keys allowed; at most 32 `id` values |

## 6.5 Checking the Test Version and the Production State

**Run on: security-core VM 220 (root)**

```bash
python3 -m py_compile \
  /tmp/wazuh-collector-hardening-test.py \
  && echo "PYTHON COMPILE: PASS"

sha256sum /tmp/wazuh-collector-hardening-test.py

stat -c 'owner=%U:%G mode=%a size=%s modified=%y' \
  /tmp/wazuh-collector-hardening-test.py
```

```bash
echo "=== PRODUCTION COLLECTOR ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== TEST COLLECTOR ==="
sha256sum /tmp/wazuh-collector-hardening-test.py

echo
echo "=== PRODUCTION SERVICE ==="
systemctl is-active wazuh-collector.service

echo
echo "=== PRODUCTION STATE ==="
stat -c 'owner=%U:%G mode=%a size=%s modified=%y' \
  /var/lib/wazuh-collector/state.json
```

Confirm that the production Collector (`931ee3cb...`) has not changed, that its content differs from the test version (15,215 bytes at build time), and that the production service is still `active`.

Also check that the production read position matches the current `alerts.json` (the values in the state file themselves are not shown).

```bash
python3 - <<'PY'
import json
from pathlib import Path

state_path = Path("/var/lib/wazuh-collector/state.json")
alert_path = Path("/var/ossec/logs/alerts/alerts.json")

state = json.loads(state_path.read_text(encoding="utf-8"))
alert_stat = alert_path.stat()

inode_ok = state.get("inode") == alert_stat.st_ino
offset_ok = state.get("offset") == alert_stat.st_size

print("STATE JSON: PASS")
print("INODE MATCH:", "PASS" if inode_ok else "FAIL")
print("OFFSET MATCH:", "PASS" if offset_ok else "FAIL")

if not inode_ok or not offset_ok:
    raise SystemExit("STATE CONSISTENCY CHECK FAILED")
PY
```

# Chapter 7: Making the State File and inode Handling Strict

## 7.1 The Problems

**Run on: security-core VM 220 (root)**

```bash
grep -n -A65 -B5 -E \
'^(def load_state|def open_initial_file|def run)' \
/tmp/wazuh-collector-hardening-test.py
```

```bash
sed -n '465,555p' \
  /tmp/wazuh-collector-hardening-test.py
```

```bash
sed -n '530,610p' \
  /tmp/wazuh-collector-hardening-test.py
```

The check found the following three problems.

| Place | Problem | Fix |
|---|---|---|
| `load_state()` | Converts with `int()`, so `true` is also accepted as an integer | Validate range and type with `safe_integer()` |
| `open_initial_file()` | Saves the inode from `stat()` taken before opening the file | Use the inode from `os.fstat()` on the opened file |
| Rotation in `run()` | If another rotation happens between `stat()` and `open()`, the saved inode and the file actually opened differ | Save the inode from `os.fstat()` right after opening |

Back up before the fix.

```bash
cp -a \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-inode-fix-20261118

sha256sum \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-inode-fix-20261118
```

## 7.2 Validating the Values in the State File

Accept only integers within the range of a 64-bit signed integer, with the inode 1 or more and the read position 0 or more.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

old = '''        inode = int(state["inode"])
        offset = int(state["offset"])

        if inode <= 0 or offset < 0:
            raise ValueError("invalid state")
'''

new = '''        if not isinstance(state, dict):
            raise ValueError("invalid state")

        inode = safe_integer(
            state.get("inode"),
            1,
            9223372036854775807,
        )
        offset = safe_integer(
            state.get("offset"),
            0,
            9223372036854775807,
        )

        if inode is None or offset is None:
            raise ValueError("invalid state")
'''

count = source.count(old)
if count != 1:
    raise SystemExit(
        f"ERROR: Expected exactly one target block, found {count}"
    )

path.write_text(source.replace(old, new), encoding="utf-8")
print("LOAD_STATE VALIDATION PATCH: PASS")
PY
```

Test with a state file in a temporary directory (the production state file is not touched).

```bash
python3 - <<'PY'
import importlib.util
import tempfile
import json
from pathlib import Path

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as directory:
    state_file = Path(directory) / "state.json"
    module.STATE_FILE = state_file

    state_file.write_text(
        json.dumps({"inode": 12345, "offset": 67890}),
        encoding="utf-8",
    )
    assert module.load_state() == (12345, 67890)

    print("VALID STATE: PASS")

    invalid_states = [
        {"inode": True, "offset": 10},
        {"inode": 12345, "offset": False},
        {"inode": -1, "offset": 10},
        {"inode": 12345, "offset": -1},
        {"inode": "invalid", "offset": 10},
        {"inode": 12345, "offset": 2**63},
        [],
        None,
    ]

    for invalid in invalid_states:
        state_file.write_text(json.dumps(invalid), encoding="utf-8")
        try:
            module.load_state()
        except RuntimeError:
            continue
        raise AssertionError(f"Invalid state accepted: {invalid!r}")

    print("INVALID STATE REJECTION: PASS")

    state_file.unlink()
    assert module.load_state() is None
    print("MISSING STATE HANDLING: PASS")

print("LOAD_STATE VALIDATION: PASS")
PY
```

## 7.3 Fixing How the Initial File Is Opened

**Run on: security-core VM 220 (root)**

```bash
sed -n '299,350p' \
  /tmp/wazuh-collector-hardening-test.py
```

Replace the whole of `open_initial_file()`. Right after opening, get the actual inode and size with `os.fstat()` and save that inode in the state. If an exception occurs partway, close the file.

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

start = source.index("def open_initial_file(state):")
end = source.index("\n\ndef read_alert_line(", start)

new_function = '''def open_initial_file(state):
    if state is None:
        handle = ALERT_FILE.open("rb")
        try:
            actual_stat = os.fstat(handle.fileno())
            handle.seek(0, os.SEEK_END)
            offset = handle.tell()

            save_state(actual_stat.st_ino, offset)

            logging.info("Initial start at current end of alerts.json")
            return handle, actual_stat.st_ino
        except Exception:
            handle.close()
            raise

    old_inode, old_offset = state
    old_path = find_inode_file(old_inode)

    if old_path is not None:
        handle = old_path.open("rb")
        actual_stat = os.fstat(handle.fileno())

        if actual_stat.st_ino == old_inode:
            handle.seek(min(old_offset, actual_stat.st_size))
            logging.info("Resuming previous alert file")
            return handle, actual_stat.st_ino

        handle.close()
        logging.warning(
            "Previous alert file changed while opening; using current file"
        )

    handle = ALERT_FILE.open("rb")
    try:
        actual_stat = os.fstat(handle.fileno())

        if actual_stat.st_ino == old_inode:
            handle.seek(min(old_offset, actual_stat.st_size))
        else:
            handle.seek(0)
            logging.warning(
                "Previous rotated file not found; replaying current file"
            )

        return handle, actual_stat.st_ino
    except Exception:
        handle.close()
        raise
'''

source = source[:start] + new_function + source[end:]
path.write_text(source, encoding="utf-8")

print("OPEN_INITIAL_FILE INODE PATCH: PASS")
PY
```

```bash
python3 -m py_compile \
  /tmp/wazuh-collector-hardening-test.py \
  && echo "PYTHON COMPILE: PASS"

sed -n '311,375p' \
  /tmp/wazuh-collector-hardening-test.py
```

Test three cases in a temporary directory: first startup, resuming from a rotated file, and the old file being missing.

```bash
python3 - <<'PY'
import importlib.util
import tempfile
import os
from pathlib import Path

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    alert_dir = root / "alerts"
    alert_dir.mkdir()
    alert_file = alert_dir / "alerts.json"

    module.ALERT_DIR = alert_dir
    module.ALERT_FILE = alert_file

    saved = []
    module.save_state = lambda inode, offset: saved.append((inode, offset))

    # 1. Initial start
    alert_file.write_bytes(b"first\nsecond\n")
    handle, inode = module.open_initial_file(None)

    actual_inode = os.fstat(handle.fileno()).st_ino
    assert inode == actual_inode
    assert handle.tell() == len(b"first\nsecond\n")
    assert saved == [(actual_inode, len(b"first\nsecond\n"))]
    handle.close()
    print("INITIAL START: PASS")

    # 2. Resume rotated file
    old_file = alert_dir / "alerts.json.1"
    alert_file.rename(old_file)
    alert_file.write_bytes(b"new-alert\n")

    old_inode = old_file.stat().st_ino
    handle, inode = module.open_initial_file((old_inode, 6))

    assert inode == os.fstat(handle.fileno()).st_ino
    assert inode == old_inode
    assert handle.tell() == 6
    handle.close()
    print("ROTATED FILE RESUME: PASS")

    # 3. Previous file missing
    missing_inode = old_inode + 1000000
    handle, inode = module.open_initial_file((missing_inode, 6))

    assert inode == os.fstat(handle.fileno()).st_ino
    assert inode == alert_file.stat().st_ino
    assert handle.tell() == 0
    handle.close()
    print("MISSING OLD FILE FALLBACK: PASS")

print("OPEN_INITIAL_FILE TESTS: PASS")
PY
```

## 7.4 Fixing the inode at Rotation

In both the incomplete-line case (5.3) and the EOF case (5.2), get the inode again with `os.fstat()` right after opening the new file. If the opened file has the same inode as the old file, do not switch; wait.

**Run on: security-core VM 220 (root)**

For an incomplete line:

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

old = '''                if current_stat.st_ino != active_inode:
                    new_handle = ALERT_FILE.open("rb")
                    try:
                        save_state(current_stat.st_ino, 0)
                    except Exception as error:
                        new_handle.close()
                        handle.seek(line_start)
                        logging.error(
                            "State save failed during incomplete-line rotation: %s",
                            type(error).__name__,
                        )
                        time.sleep(POLL_INTERVAL)
                        continue

                    logging.warning(
                        "Incomplete alert line discarded at rotation"
                    )
                    handle.close()
                    handle = new_handle
                    active_inode = current_stat.st_ino
                    discarding = False
                    discard_start = None
                    logging.info("Switched to new alerts.json inode")
'''

new = '''                if current_stat.st_ino != active_inode:
                    new_handle = ALERT_FILE.open("rb")
                    new_stat = os.fstat(new_handle.fileno())

                    if new_stat.st_ino == active_inode:
                        new_handle.close()
                        handle.seek(line_start)
                        time.sleep(POLL_INTERVAL)
                        continue

                    try:
                        save_state(new_stat.st_ino, 0)
                    except Exception as error:
                        new_handle.close()
                        handle.seek(line_start)
                        logging.error(
                            "State save failed during incomplete-line rotation: %s",
                            type(error).__name__,
                        )
                        time.sleep(POLL_INTERVAL)
                        continue

                    logging.warning(
                        "Incomplete alert line discarded at rotation"
                    )
                    handle.close()
                    handle = new_handle
                    active_inode = new_stat.st_ino
                    discarding = False
                    discard_start = None
                    logging.info("Switched to new alerts.json inode")
'''

count = source.count(old)
if count != 1:
    raise SystemExit(
        f"ERROR: Expected exactly one incomplete-rotation block, found {count}"
    )

path.write_text(source.replace(old, new), encoding="utf-8")
print("INCOMPLETE ROTATION INODE PATCH: PASS")
PY
```

```bash
python3 -m py_compile \
  /tmp/wazuh-collector-hardening-test.py \
  && echo "PYTHON COMPILE: PASS"

sed -n '465,515p' \
  /tmp/wazuh-collector-hardening-test.py
```

At EOF:

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

old = '''                if current_stat.st_ino != active_inode:
                    new_handle = ALERT_FILE.open("rb")
                    try:
                        save_state(current_stat.st_ino, 0)
                    except Exception as error:
                        new_handle.close()
                        logging.error(
                            "State save failed during rotation: %s",
                            type(error).__name__,
                        )
                        time.sleep(POLL_INTERVAL)
                        continue

                    if discarding:
                        logging.warning(
                            "Incomplete oversized line discarded at rotation"
                        )

                    handle.close()
                    handle = new_handle
                    active_inode = current_stat.st_ino
                    discarding = False
                    discard_start = None

                    logging.info("Switched to new alerts.json inode")
'''

new = '''                if current_stat.st_ino != active_inode:
                    new_handle = ALERT_FILE.open("rb")
                    new_stat = os.fstat(new_handle.fileno())

                    if new_stat.st_ino == active_inode:
                        new_handle.close()
                        time.sleep(POLL_INTERVAL)
                        continue

                    try:
                        save_state(new_stat.st_ino, 0)
                    except Exception as error:
                        new_handle.close()
                        logging.error(
                            "State save failed during rotation: %s",
                            type(error).__name__,
                        )
                        time.sleep(POLL_INTERVAL)
                        continue

                    if discarding:
                        logging.warning(
                            "Incomplete oversized line discarded at rotation"
                        )

                    handle.close()
                    handle = new_handle
                    active_inode = new_stat.st_ino
                    discarding = False
                    discard_start = None

                    logging.info("Switched to new alerts.json inode")
'''

count = source.count(old)
if count != 1:
    raise SystemExit(
        f"ERROR: Expected exactly one EOF-rotation block, found {count}"
    )

path.write_text(source.replace(old, new), encoding="utf-8")
print("EOF ROTATION INODE PATCH: PASS")
PY
```

```bash
python3 -m py_compile \
  /tmp/wazuh-collector-hardening-test.py \
  && echo "PYTHON COMPILE: PASS"

sed -n '525,585p' \
  /tmp/wazuh-collector-hardening-test.py
```

```bash
sed -n '565,610p' \
  /tmp/wazuh-collector-hardening-test.py
```

## 7.5 Checking the inode Fix

Extract the source of `run()` from the syntax tree and check that both places use the actual inode.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")
tree = ast.parse(source)

run_func = next(
    node for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "run"
)

run_source = ast.get_source_segment(source, run_func)

checks = {
    "fstat after rotation open": "os.fstat(new_handle.fileno())",
    "incomplete state uses actual inode": "save_state(new_stat.st_ino, 0)",
    "EOF state uses actual inode": run_source.count(
        "save_state(new_stat.st_ino, 0)"
    ) == 2,
    "active inode uses actual inode": run_source.count(
        "active_inode = new_stat.st_ino"
    ) == 2,
}

for name, result in checks.items():
    passed = result if isinstance(result, bool) else result in run_source
    print(f"{name}: {'PASS' if passed else 'FAIL'}")
    if not passed:
        raise SystemExit(1)

print("ROTATION INODE STATIC CHECK: PASS")
PY
```

Actually run `run()`, rotate the file while it is waiting, and check that the saved inode matches that of the new file.

```bash
python3 - <<'PY'
import importlib.util
import tempfile
from pathlib import Path


class StopTest(Exception):
    pass


path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_rotation(mode):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        alert_dir = root / "alerts"
        alert_dir.mkdir()
        alert_file = alert_dir / "alerts.json"

        alert_file.write_bytes(
            b"partial" if mode == "incomplete" else b""
        )

        module.ALERT_DIR = alert_dir
        module.ALERT_FILE = alert_file

        initial_inode = alert_file.stat().st_ino
        module.load_state = lambda: (initial_inode, 0)

        saved_states = []
        module.save_state = lambda inode, offset: (
            saved_states.append((inode, offset))
        )

        sleep_count = 0

        def controlled_sleep(_seconds):
            nonlocal sleep_count
            sleep_count += 1

            if sleep_count == 1:
                alert_file.rename(alert_dir / "alerts.json.1")
                alert_file.write_bytes(b"new-alert\n")
                return

            raise StopTest()

        module.time.sleep = controlled_sleep

        try:
            module.run()
        except StopTest:
            pass
        else:
            raise AssertionError("Collector did not reach test stop")

        new_inode = alert_file.stat().st_ino

        assert saved_states, "No state was saved"
        assert saved_states[0] == (new_inode, 0), saved_states

        print(f"{mode.upper()} ROTATION: PASS")
        print(f"{mode.upper()} STATE INODE MATCH: PASS")


test_rotation("eof")
test_rotation("incomplete")

print("ROTATION INTEGRATION TESTS: PASS")
PY
```

If both `EOF ROTATION` and `INCOMPLETE ROTATION` are `PASS`, the inode saved after rotation matches the new file actually opened.

# Chapter 8: Overall Verification of the Test Version

By the end of Chapter 7, the main improvements are in the test version. In this chapter we verify the test version again, function by function. The DB, the production state file and the production Collector are not touched.

## 8.1 Safety on Import and the Production State

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import ast
import importlib.util
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")

source = path.read_text(encoding="utf-8")
ast.parse(source)
print("AST SYNTAX: PASS")

spec = importlib.util.spec_from_file_location(
    "collector_import_safety_test",
    str(path),
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

print("IMPORT WITHOUT RUN: PASS")
print("TEST MODULE:", module.__name__)
PY
```

Confirm that `run()` does not run when it is loaded as a module.

```bash
echo "=== PRODUCTION SCRIPT ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== TEST SCRIPT ==="
sha256sum /tmp/wazuh-collector-hardening-test.py

echo
echo "=== PRODUCTION SERVICE ==="
systemctl is-active wazuh-collector.service

echo
echo "=== PRODUCTION FILE PERMISSIONS ==="
stat -c '%U:%G %a %s %n' \
  /usr/local/lib/wazuh-collector/collector.py
```

Production is still `root:root 755 9626`, and the service is `active`.

## 8.2 Listing the Functions and Checking run()

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
tree = ast.parse(path.read_text(encoding="utf-8"))

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        print(
            f"{node.name}: "
            f"lines {node.lineno}-{node.end_lineno}"
        )
PY
```

At build time there were 14 functions, ending with `open_initial_file` (lines 322–370), `read_alert_line` (lines 373–416), `process_line` (lines 419–438) and `run` (lines 441–618). Line numbers may differ in your environment, so adjust the `sed` ranges that follow to this output.

```bash
sed -n '441,618p' \
  /tmp/wazuh-collector-hardening-test.py
```

```bash
sed -n '373,440p' \
  /tmp/wazuh-collector-hardening-test.py
```

## 8.3 Boundary-Value Tests for Line Size

With the real limit (1 MiB), check four cases: exactly at the limit, over the limit, no newline, and a very large line.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util
import tempfile
from pathlib import Path

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

limit = module.MAX_ALERT_LINE_BYTES

cases = [
    ("exact_limit", b"A" * (limit - 1) + b"\n", "line"),
    ("over_limit", b"A" * limit + b"\n", "oversized"),
    ("incomplete", b"A" * (limit - 1), "incomplete"),
    ("huge_line", b"A" * (limit + 200000) + b"\n", "discarding"),
]

for name, content, expected in cases:
    with tempfile.TemporaryFile() as handle:
        handle.write(content)
        handle.seek(0)

        status, line, discarding = module.read_alert_line(handle)

        assert status == expected, (
            name, status, expected
        )

        if name == "exact_limit":
            assert len(line) == limit
        else:
            assert line is None

        if name == "huge_line":
            assert discarding is True

        print(f"{name}: PASS ({status})")

print("LINE SIZE BOUNDARY TESTS: PASS")
PY
```

| Case | Result |
|---|---|
| Exactly 1 MiB (including the newline) | `line` |
| Over 1 MiB | `oversized` |
| No newline | `incomplete` |
| 1 MiB + about 200 KB | `discarding` |

Confirm that after discarding a huge line 64 KiB at a time, the next normal line can be read.

```bash
python3 - <<'PY'
import importlib.util
import tempfile

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryFile() as handle:
    huge = b"A" * (module.MAX_ALERT_LINE_BYTES + 300000)
    valid = b'{"rule":{"id":"100001"}}\n'

    handle.write(huge + b"\n" + valid)
    handle.seek(0)

    status, line, discarding = module.read_alert_line(handle)

    assert status == "discarding"
    assert discarding is True
    print("OVERSIZED DETECTION: PASS")

    chunks = 0
    while True:
        status, line, discarding = module.read_alert_line(
            handle,
            discarding=True,
        )
        chunks += 1

        if status == "oversized":
            break

        assert status == "discarding"
        assert line is None

    print(f"CHUNKED DISCARD: PASS ({chunks} chunks)")

    status, line, discarding = module.read_alert_line(handle)

    assert status == "line"
    assert line == valid
    assert discarding is False

    print("NEXT VALID LINE: PASS")

print("CHUNKED OVERSIZED LINE TEST: PASS")
PY
```

At build time, it was discarded in four chunks, and the normal line right after it was read.

## 8.4 Managing the State File

**Run on: security-core VM 220 (root)**

```bash
sed -n '244,370p' \
  /tmp/wazuh-collector-hardening-test.py
```

Check saving and loading, permissions `0600`, replacement and rejection of invalid values in a temporary directory.

```bash
python3 - <<'PY'
import importlib.util
import json
import os
import tempfile
from pathlib import Path

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as directory:
    state_file = Path(directory) / "state.json"
    module.STATE_FILE = state_file

    module.save_state(12345, 67890)

    assert state_file.exists()
    assert module.load_state() == (12345, 67890)
    print("STATE SAVE/LOAD: PASS")

    mode = os.stat(state_file).st_mode & 0o777
    assert mode == 0o600, oct(mode)
    print("STATE PERMISSION 0600: PASS")

    before = json.loads(state_file.read_text())
    module.save_state(12346, 67891)
    after = json.loads(state_file.read_text())

    assert before != after
    assert after == {"inode": 12346, "offset": 67891}
    print("ATOMIC STATE REPLACEMENT: PASS")

    invalid_states = [
        [],
        {"inode": True, "offset": 0},
        {"inode": 123, "offset": -1},
        {"inode": "invalid", "offset": 0},
    ]

    for invalid in invalid_states:
        state_file.write_text(json.dumps(invalid))
        try:
            module.load_state()
        except RuntimeError:
            pass
        else:
            raise AssertionError(f"Invalid state accepted: {invalid}")

    print("INVALID STATE REJECTION: PASS")

print("STATE MANAGEMENT TESTS: PASS")
PY
```

## 8.5 DB Insert and Duplicate Handling

Check the INSERT statement, the DB settings and how `event_id` is made.

**Run on: security-core VM 220 (root)**

```bash
sed -n '1,80p' \
  /tmp/wazuh-collector-hardening-test.py
```

> This command only displays the file. `.pgpass` and the DB password are not shown. If the output ever contains secrets, do not paste it anywhere.

```bash
sed -n '186,243p' \
  /tmp/wazuh-collector-hardening-test.py
```

```bash
sed -n '419,440p' \
  /tmp/wazuh-collector-hardening-test.py
```

| Item | Result |
|---|---|
| Connection | TLS `verify-full`, dedicated user `wazuh_collector` |
| SQL | INSERT only; `ON CONFLICT` is not used |
| Target columns | Whitelist of 13 fields |
| `event_id` | The Wazuh alert's `id` (up to 128 characters); the same ID results even if reprocessed |
| Duplicate handling | `UniqueViolation` is caught outside `connection.transaction()`, so the transaction is reliably rolled back |

Mock the DB connection and check three cases: a successful insert, a duplicate, and another DB error.

```bash
python3 - <<'PY'
import importlib.util
import json

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class FakeTransaction:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        self.connection.entered += 1
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.connection.rolled_back += 1
        else:
            self.connection.committed += 1
        return False

class FakeConnection:
    def __init__(self, error=None):
        self.error = error
        self.entered = 0
        self.committed = 0
        self.rolled_back = 0
        self.executed = 0

    def transaction(self):
        return FakeTransaction(self)

    def execute(self, sql, event):
        self.executed += 1
        if self.error:
            raise self.error

alert = {
    "id": "test-event-001",
    "timestamp": "2026-11-18T12:00:00.000+0900",
    "rule": {"id": "100001", "level": 5},
    "agent": {"id": "001", "name": "test-agent"},
    "manager": {"name": "test-manager"},
    "decoder": {"name": "json"},
}

line = json.dumps(alert).encode()

# 1. INSERT succeeds
conn = FakeConnection()
module.process_line(conn, line)

assert conn.executed == 1
assert conn.committed == 1
assert conn.rolled_back == 0
print("INSERT SUCCESS: PASS")

# 2. Unique constraint violation
duplicate = module.psycopg.errors.UniqueViolation(
    "duplicate key"
)
conn = FakeConnection(duplicate)
module.process_line(conn, line)

assert conn.executed == 1
assert conn.rolled_back == 1
assert conn.committed == 0
print("DUPLICATE HANDLING: PASS")

# 3. Other DB error
other_error = module.psycopg.errors.OperationalError(
    "simulated database failure"
)
conn = FakeConnection(other_error)

try:
    module.process_line(conn, line)
except module.psycopg.errors.OperationalError:
    pass
else:
    raise AssertionError("OperationalError was swallowed")

assert conn.rolled_back == 1
print("OTHER DB ERROR PROPAGATION: PASS")

print("MOCK DB TRANSACTION TESTS: PASS")
PY
```

## 8.6 Reprocessing After a Failed State Save

Consider the case where the DB insert succeeds but saving the state file fails. The Collector goes back to the start of the line and processes the same alert again; the second time it is discarded as a duplicate, and only one row remains in the DB. Check this flow.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util
import json
import tempfile

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class FakeTransaction:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

class FakeConnection:
    def __init__(self):
        self.ids = set()
        self.inserts = 0
        self.duplicates = 0

    def transaction(self):
        return FakeTransaction(self)

    def execute(self, sql, event):
        self.inserts += 1
        event_id = event["event_id"]

        if event_id in self.ids:
            self.duplicates += 1
            raise module.psycopg.errors.UniqueViolation(
                "duplicate key"
            )

        self.ids.add(event_id)

alert = {
    "id": "retry-event-001",
    "timestamp": "2026-11-18T12:00:00.000+0900",
    "rule": {"id": "100001", "level": 5},
    "agent": {"id": "001", "name": "test-agent"},
    "manager": {"name": "test-manager"},
    "decoder": {"name": "json"},
}
line = json.dumps(alert).encode()

connection = FakeConnection()
save_attempts = 0

with tempfile.TemporaryFile() as handle:
    handle.write(line + b"\n")
    handle.seek(0)

    start = handle.tell()
    status, data, _ = module.read_alert_line(handle)
    assert status == "line"

    module.process_line(connection, data)

    save_attempts += 1
    try:
        raise OSError("simulated state failure")
    except OSError:
        handle.seek(start)

    status, retry_data, _ = module.read_alert_line(handle)
    assert status == "line"
    assert retry_data == data

    module.process_line(connection, retry_data)

    save_attempts += 1
    assert handle.tell() == len(line) + 1

assert connection.inserts == 2
assert connection.duplicates == 1
assert len(connection.ids) == 1
assert save_attempts == 2

print("FIRST INSERT: PASS")
print("STATE FAILURE AND REWIND: PASS")
print("RETRY DUPLICATE DETECTION: PASS")
print("SINGLE STORED EVENT: PASS")
print("STATE RETRY SEQUENCE: PASS")
PY
```

| Check | Result |
|---|---|
| First insert | Succeeds |
| State save fails and rewinds | Goes back to the start of the line |
| Second processing | Detected as a duplicate and discarded |
| Rows remaining in the DB | 1 |

> Dropping `ON CONFLICT` in Part 3 and handling duplicates with `UniqueViolation` is what provides the safety here that "reprocessing never inserts twice".

## 8.7 Differences from Production

Finally, check the diff between the production code and the test version. This only displays it and changes nothing.

**Run on: security-core VM 220 (root)**

```bash
diff -u \
  /usr/local/lib/wazuh-collector/collector.py \
  /tmp/wazuh-collector-hardening-test.py
```

The differences fall into the following five areas.

1. Stricter, whitelisted input values for alerts (Chapters 2 and 6)
2. Validation of the values in the state file (Chapter 7)
3. Rotation handling based on the inode of the file actually opened (Chapters 5 and 7)
4. A 1 MiB per-line limit and gradual skipping of huge lines (Chapters 3 and 4)
5. Rewinding the read position when the DB connection fails (Chapter 4)

```bash
nl -ba /tmp/wazuh-collector-hardening-test.py | sed -n '435,625p'
```

# Chapter 9: Exception Handling for File Operations and Final Checks

## 9.1 Listing the File Operations

Using the syntax tree, list every line that calls `stat`, `open`, `fstat`, `close`, `seek`, `tell` or `readline`.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
tree = ast.parse(path.read_text(encoding="utf-8"))

targets = {
    "stat", "open", "fstat", "close",
    "seek", "tell", "readline"
}

for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        func = node.func
        name = None

        if isinstance(func, ast.Attribute):
            name = func.attr
        elif isinstance(func, ast.Name):
            name = func.id

        if name in targets:
            print(
                f"line={node.lineno} "
                f"operation={name}"
            )
PY
```

```bash
nl -ba /tmp/wazuh-collector-hardening-test.py | sed -n '315,375p;485,620p'
```

| Place | Problem | Approach |
|---|---|---|
| Rotated file in `open_initial_file()` | If `fstat()` or `seek()` fails after opening, the file stays open | On failure, close the file and pass the exception to the caller |
| `stat()` and `open()` at rotation in `run()` | Processing stops on an `OSError` other than `FileNotFoundError` | Silently skipping an unreadable file would lose alerts, so exit with the exception and let systemd restart it (9.3) |

> We do not swallow every `OSError` uniformly. Continuing while a file cannot be read would lead to lost alerts.

## 9.2 Fixing How Rotated Files Are Opened

Back up before the fix.

**Run on: security-core VM 220 (root)**

```bash
cp -a \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-file-open-fix-20261118
```

```bash
sha256sum \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-file-open-fix-20261118
```

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

old = '''    if old_path is not None:
        handle = old_path.open("rb")
        actual_stat = os.fstat(handle.fileno())

        if actual_stat.st_ino == old_inode:
            handle.seek(min(old_offset, actual_stat.st_size))
            logging.info("Resuming previous alert file")
            return handle, actual_stat.st_ino

        handle.close()
        logging.warning(
            "Previous alert file changed while opening; using current file"
        )
'''

new = '''    if old_path is not None:
        handle = None
        try:
            handle = old_path.open("rb")
            actual_stat = os.fstat(handle.fileno())

            if actual_stat.st_ino == old_inode:
                handle.seek(min(old_offset, actual_stat.st_size))
                logging.info("Resuming previous alert file")
                return handle, actual_stat.st_ino

            handle.close()
            handle = None
            logging.warning(
                "Previous alert file changed while opening; using current file"
            )
        except Exception:
            if handle is not None:
                try:
                    handle.close()
                except OSError:
                    pass
            raise
'''

count = source.count(old)
if count != 1:
    raise SystemExit(
        f"ERROR: Expected exactly one target block, found {count}"
    )

path.write_text(source.replace(old, new), encoding="utf-8")
print("TEST COPY UPDATED: PASS")
print("TARGET BLOCK COUNT:", count)
PY
```

```bash
python3 -m py_compile \
  /tmp/wazuh-collector-hardening-test.py \
&& sed -n '335,375p' \
  /tmp/wazuh-collector-hardening-test.py
```

With a fake file whose `fstat()` fails, confirm that the exception is passed on and the file is closed. No real file is used.

```bash
python3 - <<'PY'
import importlib.util
from pathlib import Path

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class FakeHandle:
    def __init__(self):
        self.closed = False

    def fileno(self):
        return 123

    def close(self):
        self.closed = True

handle = FakeHandle()
old_path = Path("/tmp/fake-rotated-alerts.json")

original_find = module.find_inode_file
original_open = Path.open
original_fstat = module.os.fstat

try:
    module.find_inode_file = lambda inode: old_path

    def fake_open(self, *args, **kwargs):
        if self == old_path:
            return handle
        raise AssertionError("Unexpected file open")

    def fake_fstat(fd):
        raise OSError("simulated fstat failure")

    Path.open = fake_open
    module.os.fstat = fake_fstat

    try:
        module.open_initial_file((12345, 100))
        raise AssertionError("Expected OSError was not raised")
    except OSError as error:
        assert str(error) == "simulated fstat failure"

    assert handle.closed

    print("FSTAT FAILURE PROPAGATION: PASS")
    print("FILE HANDLE CLOSED: PASS")

finally:
    module.find_inode_file = original_find
    Path.open = original_open
    module.os.fstat = original_fstat
PY
```

## 9.3 Unexpected Exceptions and systemd's Automatic Restart

Even if the Collector exits on an unexpected `OSError`, it can resume from the saved read position once systemd restarts it. Check the restart settings of the production service (the settings are not changed).

**Run on: security-core VM 220 (root)**

```bash
systemctl show wazuh-collector.service \
  -p Restart \
  -p RestartUSec \
  -p NRestarts \
  -p ActiveState \
  -p SubState
```

```text
Restart=always
RestartUSec=5s
NRestarts=0
ActiveState=active
SubState=running
```

## 9.4 Checking the Unique Constraint

Reprocessing after a restart does not insert twice because of the unique constraint on `event_id`. Check the table's indexes. The Collector's `.pgpass` is in a dedicated location, so specify it with `PGPASSFILE`.

**Run on: security-core VM 220 (root)**

```bash
sudo -u wazuh-collector env \
  PGPASSFILE=/etc/wazuh-collector/.pgpass \
  psql "host=postgresql.neomedia.mydns.jp hostaddr=192.168.0.151 dbname=security_workbench user=wazuh_collector sslmode=verify-full sslrootcert=/etc/ssl/certs/postgresql-server-ca.pem" \
  -c "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname='incident' AND tablename='alert_events';"
```

> If `PGPASSFILE` is not specified, psql looks for the standard `~/.pgpass` and fails with `fe_sendauth: no password supplied`. If the result is shown in a pager (`less`), press `q` to quit.

```text
 alert_events_pkey          | CREATE UNIQUE INDEX alert_events_pkey ON incident.alert_events USING btree (event_id)
 idx_alert_events_timestamp | CREATE INDEX idx_alert_events_timestamp ON incident.alert_events USING btree (event_timestamp DESC)
 idx_alert_events_level     | CREATE INDEX idx_alert_events_level ON incident.alert_events USING btree (rule_level DESC)
 idx_alert_events_rule      | CREATE INDEX idx_alert_events_rule ON incident.alert_events USING btree (rule_id)
 idx_alert_events_srcip     | CREATE INDEX idx_alert_events_srcip ON incident.alert_events USING btree (srcip)
```

`alert_events_pkey` is the unique index on `event_id`. This confirms that double inserts are prevented in the following flow.

1. The DB insert succeeds.
2. A failure occurs before the state is saved, and the Collector exits.
3. systemd restarts the Collector 5 seconds later.
4. The same alert is processed again from the saved read position.
5. It is rejected by the unique constraint on `event_id` and skipped as `Duplicate alert skipped`.

## 9.5 Checking the Production State

**Run on: security-core VM 220 (root)**

```bash
echo "=== SERVICE ==="
systemctl is-active wazuh-collector.service

echo
echo "=== RESTART COUNT ==="
systemctl show wazuh-collector.service -p NRestarts

echo
echo "=== PRODUCTION SCRIPT HASH ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py
```

The production Collector is `active`, has restarted 0 times, and its SHA-256 is still `931ee3cb...`, the same as at the start of Part 4. All work in Part 4 was done only on the test copy.

# Summary of Part 4

In Part 4 we audited the running Collector without stopping it and made the following improvements in the test copy `/tmp/wazuh-collector-hardening-test.py`.

| Area | Improvement | Chapter |
|---|---|---|
| Input validation | Reject booleans, remove control characters (C0, DEL, C1), limits on lists and MITRE information | Chapters 2 and 6 |
| Line size | 1 MiB per-line limit, skipping in 64 KiB units | Chapters 3 and 4 |
| DB failure | Huge lines are handled without the DB; normal lines are rewound when the connection fails | Chapter 4 |
| Rotation | Switch to the new file even with an incomplete line or while skipping | Chapter 5 |
| State file | Validate value types and ranges; save the inode of the file actually opened | Chapter 7 |
| Exception handling | Always close opened files; leave unexpected errors to systemd's restart | Chapter 9 |

| Backup | Contents |
|---|---|
| `/usr/local/lib/wazuh-collector/collector.py.backup-pre-hardening-20261118` | Production code before the improvements (1.5) |
| `/tmp/wazuh-collector-hardening-test.py.backup-before-*-20261118` | The test version just before each fix |

> The test version and backups in `/tmp` may disappear when the VM restarts. Do not restart security-core until it is deployed to production in Part 5.

In Part 5, we add improvements to shutdown handling, deploy the test version to the production Collector, and check restarts, an actual rotation and the match of DB inserts.

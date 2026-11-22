---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 6: Verifying Data Integrity and Auditing Operations"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 6 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". For the hardened Collector deployed in Part 5, we confirm that no duplicates occur and that every Wazuh alert is in the DB without exception, checking not just the counts but down to individual event IDs. We also audit operation across an actual date change (rotation).

## Notation

- Commands and file contents are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Each step begins with "Run on", which says where to run it. DB checks are done inside LXC 109 as the DB administrator (`postgres`) (the prompt is `root@postgresql`).
- "Example output" is the actual output from the build. Event IDs, counts, times, inodes and so on will differ in your environment.
- The contents of credentials and the state file are not shown.

## State at the End of Part 5

| Item | State |
|---|---|
| Collector | Hardened version (`/usr/local/lib/wazuh-collector/collector.py`, 18,898 bytes) |
| Service | `wazuh-collector.service` (active, starts automatically) |
| Reconciliation | Wazuh alerts and DB rows for the same period match (230) |

# Chapter 1: Guaranteeing No Duplicates

## 1.1 How Event IDs Are Implemented

**Run on: security-core VM 220 (root)**

```bash
echo "=== EVENT ID IMPLEMENTATION ==="

grep -n -B 8 -A 18 \
  -E 'event_id|UniqueViolation|23505|ON CONFLICT' \
  /usr/local/lib/wazuh-collector/collector.py
```

| Item | Implementation |
|---|---|
| `event_id` | The Wazuh alert's `id` (up to 128 characters) |
| Duplicate detection | DB unique constraint violation (SQLSTATE `23505`) |
| Handling duplicates | Skip and log |
| `ON CONFLICT` | Not used (to keep the INSERT-only privilege) |

## 1.2 Constraints on the DB Side

**Run on: LXC 109 postgresql (root)**

```bash
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    c.conname AS constraint_name,
    c.contype AS constraint_type,
    pg_get_constraintdef(c.oid) AS definition
FROM pg_constraint c
WHERE c.conrelid = 'incident.alert_events'::regclass

UNION ALL

SELECT
    i.indexname,
    'INDEX',
    i.indexdef
FROM pg_indexes i
WHERE i.schemaname = 'incident'
  AND i.tablename = 'alert_events'
ORDER BY 1;
"
```

| Constraint / index | Purpose |
|---|---|
| `PRIMARY KEY (event_id)` | Prevent duplicates |
| CHECK on `mitre` | Guarantee that it is a JSON object |
| CHECK on `rule_level` | Limit to 0–16 |
| CHECK on `srcport` | Limit to the range of port numbers |
| Indexes on time, level, rule and source IP | Faster searches |

Confirm that the current data has no duplicates.

```bash
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT event_id) AS unique_event_ids,
    COUNT(*) - COUNT(DISTINCT event_id) AS duplicate_count
FROM incident.alert_events;
"
```

```text
 total_rows | unique_event_ids | duplicate_count 
------------+------------------+-----------------
        547 |              547 |               0
(1 row)
```

## 1.3 Privileges of the Collector's Role

**Run on: LXC 109 postgresql (root)**

```bash
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    rolname,
    rolsuper,
    rolcreatedb,
    rolcreaterole
FROM pg_roles
WHERE rolname = 'wazuh_collector';
"
```

Confirm that `wazuh_collector` has no superuser, create-DB or create-role privileges. Also check the privilege to create temporary tables, used in the next test.

```bash
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    has_database_privilege(
        'wazuh_collector',
        current_database(),
        'TEMP'
    ) AS can_create_temp_table,
    has_database_privilege(
        'wazuh_collector',
        current_database(),
        'CONNECT'
    ) AS can_connect;
"
```

## 1.4 Testing a Duplicate Insert on a Temporary Table

Without touching the production table, insert the same ID twice into a temporary table with `wazuh_collector`'s privileges and confirm that the second insert is rejected. The whole transaction is rolled back at the end.

The temporary table's schema name changes per connection, so take the name from `pg_my_temp_schema()` and grant privileges with `\gexec` (you cannot `GRANT` on the alias `pg_temp`).

**Run on: LXC 109 postgresql (root)**

```bash
sudo -u postgres psql -X -v ON_ERROR_STOP=1 -P pager=off -d security_workbench <<'SQL'
BEGIN;

CREATE TEMP TABLE collector_duplicate_test (
    event_id text PRIMARY KEY
);

SELECT format(
    'GRANT USAGE ON SCHEMA %I TO wazuh_collector',
    nspname
)
FROM pg_namespace
WHERE oid = pg_my_temp_schema()
\gexec

GRANT INSERT ON collector_duplicate_test TO wazuh_collector;

SET ROLE wazuh_collector;

DO $$
BEGIN
    INSERT INTO collector_duplicate_test (event_id)
    VALUES ('duplicate-test-325');

    BEGIN
        INSERT INTO collector_duplicate_test (event_id)
        VALUES ('duplicate-test-325');

        RAISE EXCEPTION 'FAIL: duplicate was accepted';

    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE 'PASS: duplicate rejected with unique_violation';
    END;
END;
$$;

RESET ROLE;

SELECT
    COUNT(*) AS inserted_rows,
    COUNT(DISTINCT event_id) AS unique_event_ids
FROM collector_duplicate_test;

ROLLBACK;
SQL
```

It has succeeded if `PASS: duplicate rejected with unique_violation` is followed by `inserted_rows` and `unique_event_ids` both being `1`.

## 1.5 Testing Duplicate Handling on the Collector Side

Process the same alert twice with `process_line()` and confirm with a mock connection that the second `UniqueViolation` is handled and does not escape. The test file is readable only by root, so run it as root.

**Run on: security-core VM 220 (root)**

```bash
grep -n -A100 -B20 'def process_line' \
  /tmp/wazuh-collector-hardening-test.py
```

```bash
python3 - <<'PY'
import importlib.util
from unittest.mock import patch
import psycopg
import json

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class FakeTransaction:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

class FakeConnection:
    def __init__(self):
        self.calls = 0
        self.transactions = 0

    def transaction(self):
        self.transactions += 1
        return FakeTransaction()

    def execute(self, sql, event):
        self.calls += 1
        assert sql == m.INSERT_SQL

        if self.calls == 1:
            return

        raise psycopg.errors.UniqueViolation(
            "duplicate key value violates unique constraint"
        )

connection = FakeConnection()
line = json.dumps({"id": "duplicate-test-325"}).encode()

with patch.object(
    m,
    "extract_event",
    return_value={"event_id": "duplicate-test-325"},
):
    m.process_line(connection, line)
    m.process_line(connection, line)

assert connection.calls == 2
assert connection.transactions == 2

print("PASS: first INSERT accepted by mock")
print("PASS: second INSERT raised UniqueViolation")
print("PASS: duplicate handled without propagation")
print("PASS: transactions =", connection.transactions)
print("PASS: execute calls =", connection.calls)
print("PASS: no production DB connection")
PY
```

> `/tmp/wazuh-collector-hardening-test.py` is readable only by root (permissions 600). Running it as an ordinary user gives `PermissionError`.

# Chapter 2: Reconciling Wazuh and the DB Event by Event

Even if the counts match, it is not impossible that different events have been swapped. Here we reconcile down to the set of event IDs, using reads only. No services are restarted and no settings are changed.

## 2.1 The Collector's Running State and Read Position

**Run on: security-core VM 220 (root)**

```bash
echo "=== SERVICE STATUS ==="
systemctl show wazuh-collector \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p NRestarts \
  -p ExecMainStatus

echo
echo "=== RECENT JOURNAL ==="
journalctl -u wazuh-collector -n 30 --no-pager

echo
echo "=== STATE FILE METADATA ==="
stat -c '%n | %U:%G | %a | %s bytes | modified=%y' \
  /var/lib/wazuh-collector/state.json
```

> `NRestarts` is a cumulative value that includes the restarts during the startup failure in Part 5.

```bash
python3 - <<'PY'
import json
import os

state_path = "/var/lib/wazuh-collector/state.json"
alert_path = "/var/ossec/logs/alerts/alerts.json"

with open(state_path, "r") as f:
    state = json.load(f)

st = os.stat(alert_path)

saved_inode = state.get("inode")
saved_offset = state.get("offset")

print("=== COLLECTOR STATE ===")
print("saved_inode:", saved_inode)
print("saved_offset:", saved_offset)

print("\n=== CURRENT ALERT FILE ===")
print("current_inode:", st.st_ino)
print("current_size:", st.st_size)

print("\n=== COMPARISON ===")
if saved_inode == st.st_ino:
    unread = st.st_size - saved_offset
    print("inode_match: PASS")
    print("unread_bytes:", unread)
    print("offset_within_file:", 0 <= saved_offset <= st.st_size)
else:
    print("inode_match: FAIL")
    print("Rotation or file replacement requires investigation.")
PY
```

## 2.2 Basic Integrity on the DB Side

**Run on: LXC 109 postgresql (root)**

```bash
sudo -u postgres psql -X -P pager=off -d security_workbench -c "
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT event_id) AS unique_event_ids,
    COUNT(*) - COUNT(DISTINCT event_id) AS duplicate_count,
    MAX(event_timestamp) AS latest_event_timestamp,
    MAX(ingested_at) AS latest_ingested_at,
    COUNT(*) FILTER (
        WHERE ingested_at >= NOW() - INTERVAL '5 minutes'
    ) AS ingested_last_5m,
    NOW() AS database_time
FROM incident.alert_events;
"
```

## 2.3 Checking That the Latest Alerts Are Ingested

Show the last five alerts in `alerts.json` and check individually whether their IDs are in the DB.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import json
from collections import deque

path = "/var/ossec/logs/alerts/alerts.json"
last = deque(maxlen=5)

with open(path, "rb") as f:
    for line in f:
        try:
            obj = json.loads(line)
            last.append({
                "id": obj.get("id"),
                "timestamp": obj.get("timestamp"),
                "rule_id": obj.get("rule", {}).get("id"),
                "rule_level": obj.get("rule", {}).get("level"),
                "agent_id": obj.get("agent", {}).get("id"),
            })
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

print("=== LAST 5 ALERT METADATA ===")
for item in last:
    print(json.dumps(item, ensure_ascii=False))
PY

echo
echo "=== COLLECTOR LOG SINCE SUCCESSFUL START ==="
journalctl -u wazuh-collector \
  --since "2026-11-18 15:31:53 UTC" \
  --no-pager \
  | tail -n 40
```

**Run on: LXC 109 postgresql (root)**

```bash
sudo -u postgres psql -X -P pager=off -d security_workbench -c "
SELECT
    event_id,
    event_timestamp,
    ingested_at,
    rule_id,
    agent_id
FROM incident.alert_events
WHERE event_id IN (
    '1795033806.3121490',
    '1795033806.3122882',
    '1795033806.3123268'
)
ORDER BY event_timestamp, event_id;
"
```

Replace the IDs inside `IN` with the IDs from your environment shown by the previous command. At build time all three were inserted, and the delay from the alert occurring to its ingestion into the DB was within about one second.

## 2.4 Fixing the Range to Reconcile

Take as the range everything after the read position at which the fixed version was started in Part 5 (`2178712` at build time). Output the count, times, and first and last IDs in the range.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import json

path = "/var/ossec/logs/alerts/alerts.json"
start_offset = 2178712

timestamps = []
event_ids = []

with open(path, "rb") as f:
    f.seek(start_offset)

    for line in f:
        try:
            alert = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        ts = alert.get("timestamp")
        event_id = alert.get("id")

        if isinstance(ts, str):
            timestamps.append(ts)
        if isinstance(event_id, str):
            event_ids.append(event_id)

print("scope_count:", len(event_ids))
print("earliest_timestamp:", min(timestamps) if timestamps else None)
print("latest_timestamp:", max(timestamps) if timestamps else None)
print("first_event_id:", event_ids[0] if event_ids else None)
print("last_event_id:", event_ids[-1] if event_ids else None)
PY
```

Replace `start_offset` with your environment's value. At build time there were 413 alerts, the oldest at `2026-11-18T15:15:10.963+0000` and the newest at `2026-11-18T20:31:14.188+0000`. Count the DB rows in the same time range.

**Run on: LXC 109 postgresql (root)**

```bash
sudo -u postgres psql -X -P pager=off -d security_workbench -c "
SELECT
    COUNT(*) AS db_rows,
    COUNT(DISTINCT event_id) AS unique_event_ids,
    MIN(event_timestamp) AS earliest_event,
    MAX(event_timestamp) AS latest_event,
    MIN(ingested_at) AS first_ingested,
    MAX(ingested_at) AS last_ingested
FROM incident.alert_events
WHERE event_timestamp >= TIMESTAMPTZ '2026-11-18 15:15:10.963+00'
  AND event_timestamp <= TIMESTAMPTZ '2026-11-18 20:31:14.188+00';
"
```

| Item | alerts.json | PostgreSQL |
|---|---:|---:|
| Count | 413 | 413 |
| Unique event_id | 413 | 413 |
| Oldest event | 15:15:10.963 | 15:15:10.963 |
| Newest event | 20:31:14.188 | 20:31:14.188 |

# Chapter 3: Exact Match of the Sets of Event IDs

## 3.1 The Approach

Even if the counts are the same, the IDs are not necessarily the same. Sort the event IDs in the range, join them with newlines, compute the SHA-256, and check whether it matches on both sides. If it matches, all 413 IDs are identical one by one.

> New alerts keep arriving while the hash is being computed. Unless the calculation is limited to the same **time range** as the DB, the counts drift and cannot be compared.

## 3.2 The Hash on the alerts.json Side

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import json
import hashlib

path = "/var/ossec/logs/alerts/alerts.json"
start_offset = 2178712

start = "2026-11-18T15:15:10.963+0000"
end   = "2026-11-18T20:31:14.188+0000"

ids = []

with open(path, "rb") as f:
    f.seek(start_offset)

    for line in f:
        try:
            alert = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        ts = alert.get("timestamp")
        event_id = alert.get("id")

        if (
            isinstance(ts, str)
            and start <= ts <= end
            and isinstance(event_id, str)
            and event_id
        ):
            ids.append(event_id)

payload = "\n".join(sorted(ids)).encode("utf-8")

print("source_count:", len(ids))
print("source_unique_ids:", len(set(ids)))
print("source_sha256:", hashlib.sha256(payload).hexdigest())
PY
```

Replace `start_offset`, `start` and `end` with your environment's values fixed in Chapter 2, 2.4.

## 3.3 The Hash on the DB Side

Hash the IDs in the same range, sorted and joined the same way.

**Run on: LXC 109 postgresql (root)**

```bash
sudo -u postgres psql -X -qAt -d security_workbench -c "
SELECT event_id
FROM incident.alert_events
WHERE event_timestamp >= TIMESTAMPTZ '2026-11-18 15:15:10.963+00'
  AND event_timestamp <= TIMESTAMPTZ '2026-11-18 20:31:14.188+00'
ORDER BY event_id;
" | python3 -c '
import sys, hashlib
ids = sys.stdin.read().splitlines()
payload = "\n".join(ids).encode("utf-8")
print("db_count:", len(ids))
print("db_unique_ids:", len(set(ids)))
print("db_sha256:", hashlib.sha256(payload).hexdigest())
'
```

Results at build time:

| Item | alerts.json | PostgreSQL |
|---|---:|---:|
| Count | 413 | 413 |
| Unique IDs | 413 | 413 |
| SHA-256 | `a819b04e...34137d6` | `a819b04e...34137d6` |

```text
a819b04e5a912e29592a164da3a12e24aa3ca4d27e57a3aa124d0830b34137d6
```

The hashes match, so the 413 target alerts are all in the DB with no gaps and no duplicates at the level of individual IDs.

# Chapter 4: The Structure of an Actual Rotation

In Part 5 we tested rotation with a simulated log in a temporary directory. Here we examine Wazuh's actual file structure and check that it matches the Collector's assumptions. The production Collector is not stopped, and no logs are deleted, moved or changed.

## 4.1 The Current State

**Run on: security-core VM 220 (root)**

```bash
echo "=== COLLECTOR STATE ==="
python3 - <<'PY'
import json
p = "/var/lib/wazuh-collector/state.json"
with open(p) as f:
    s = json.load(f)
print("saved_inode:", s.get("inode"))
print("saved_offset:", s.get("offset"))
PY

echo
echo "=== ALERT LOG FILES ==="
find /var/ossec/logs/alerts -maxdepth 1 -type f \
  -printf '%f | inode=%i | size=%s | mtime=%TY-%Tm-%Td %TH:%TM:%TS\n' \
  | sort

echo
echo "=== CURRENT ALERTS.JSON ==="
stat -c 'inode=%i size=%s bytes mtime=%y' \
  /var/ossec/logs/alerts/alerts.json
```

If the saved inode and read position match the inode and size of the current `alerts.json`, it has processed up to the end.

## 4.2 The Structure of the Alert Directory

**Run on: security-core VM 220 (root)**

```bash
echo "=== ALERT DIRECTORY TREE ==="
find /var/ossec/logs/alerts -maxdepth 5 \
  -printf '%y | inode=%i | size=%s | %p\n' \
  | sort

echo
echo "=== WAZUH ROTATION MESSAGES ==="
grep -iE 'rotat|alerts\.json|alerts\.log' \
  /var/ossec/logs/ossec.log 2>/dev/null \
  | tail -50
```

Results at build time:

```text
=== ALERT DIRECTORY TREE ===
d | inode=5398349 | size=4096 | /var/ossec/logs/alerts
d | inode=5398502 | size=4096 | /var/ossec/logs/alerts/2026
d | inode=5398503 | size=4096 | /var/ossec/logs/alerts/2026/Nov
f | inode=5398501 | size=3132720 | /var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.log
f | inode=5398501 | size=3132720 | /var/ossec/logs/alerts/alerts.log
f | inode=5398822 | size=499 | /var/ossec/logs/alerts/2026/Nov/ossec-alerts-17.json.sum
f | inode=5399257 | size=496 | /var/ossec/logs/alerts/2026/Nov/ossec-alerts-17.log.sum
f | inode=5408976 | size=196775 | /var/ossec/logs/alerts/2026/Nov/ossec-alerts-17.log.gz
f | inode=5408977 | size=158174 | /var/ossec/logs/alerts/2026/Nov/ossec-alerts-17.json.gz
f | inode=5409146 | size=2603330 | /var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json
f | inode=5409146 | size=2603330 | /var/ossec/logs/alerts/alerts.json

=== WAZUH ROTATION MESSAGES ===
2026/11/18 00:00:10 wazuh-monitord: INFO: Starting new log after rotation.
root@security-core:~#
```

| Pair | Relationship |
|---|---|
| `alerts.json` and `2026/Nov/ossec-alerts-18.json` | Same inode (today's JSON) |
| `alerts.log` and `2026/Nov/ossec-alerts-18.log` | Same inode (today's text format; not used by the Collector) |
| `ossec-alerts-17.json.gz` | The previous day's JSON, compressed (`.sum` is the signature) |

When the date changes, `alerts.json` becomes a new file, and the previous day's file stays under `year/month` and is then compressed.

## 4.3 Can the Collector See It?

Check the current `find_inode_file()` and the permissions of the per-day directories.

**Run on: security-core VM 220 (root)**

```bash
echo "=== COLLECTOR INODE SEARCH FUNCTION ==="
grep -n -A45 -B5 'def find_inode_file' \
  /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== CURRENT JSON FILE LINK COUNT ==="
stat -c '%n | inode=%i | links=%h | owner=%U:%G | mode=%a' \
  /var/ossec/logs/alerts/alerts.json \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json

echo
echo "=== ARCHIVE DIRECTORY PERMISSIONS ==="
namei -l /var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json

echo
echo "=== ARCHIVE ACL ==="
getfacl -p \
  /var/ossec/logs/alerts/2026 \
  /var/ossec/logs/alerts/2026/Nov \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json
```

```bash
echo "=== COLLECTOR DIRECTORY ACCESS ==="
for path in \
  /var/ossec/logs/alerts \
  /var/ossec/logs/alerts/2026 \
  /var/ossec/logs/alerts/2026/Nov
do
    if sudo -u wazuh-collector test -x "$path"; then
        echo "SEARCH OK: $path"
    else
        echo "SEARCH DENIED: $path"
    fi
done

echo
echo "=== COLLECTOR FILE READ ACCESS ==="
for path in \
  /var/ossec/logs/alerts/alerts.json \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json
do
    if sudo -u wazuh-collector test -r "$path"; then
        echo "READ OK: $path"
    else
        echo "READ DENIED: $path"
    fi
done
```

| Target | From the Collector |
|---|---|
| `alerts/` | Can traverse |
| `alerts/2026/`, `alerts/2026/Nov/` | Cannot traverse |
| `alerts.json` | Can read |
| `2026/Nov/ossec-alerts-18.json` | Cannot read (even though it is the same file, because the directories on the way cannot be traversed) |

**Problems:**

1. `find_inode_file()` searches only directly under `alerts`. The old file is under `year/month`.
2. The Collector has no permission to traverse the `year/month` directories.
3. The default ACL on `alerts` (Part 3, 7.3) was not applied to `2026` and `Nov`, which already existed.

As it stands, if the date changes while the Collector is stopped, it cannot start because of the fail-closed behavior from Part 5, 9.3.

## 4.4 Compressed Archives and the Read Position

**Run on: security-core VM 220 (root)**

```bash
echo "=== ROTATED JSON ARCHIVES ==="
find /var/ossec/logs/alerts -type f \
  -name 'ossec-alerts-*.json*' \
  -printf '%i | %s bytes | %u:%g | %m | %p\n' \
  | sort

echo
echo "=== GZIP ARCHIVE VALIDATION ==="
for f in /var/ossec/logs/alerts/*/*/*.json.gz; do
    [ -f "$f" ] || continue
    if gzip -t "$f"; then
        echo "GZIP OK: $f"
    else
        echo "GZIP ERROR: $f"
    fi
done

echo
echo "=== COLLECTOR STATE METADATA ==="
stat -c '%n | owner=%U:%G | mode=%a | size=%s | modify=%y' \
  /var/lib/wazuh-collector/state.json
```

```bash
echo "=== COLLECTOR STATE (SAFE FIELDS ONLY) ==="
sudo -u wazuh-collector python3 - <<'PY'
import json

path = "/var/lib/wazuh-collector/state.json"

with open(path, "r", encoding="utf-8") as f:
    state = json.load(f)

print("saved_inode =", state.get("inode"))
print("saved_offset =", state.get("offset"))
PY

echo
echo "=== CURRENT AND ARCHIVED INODES ==="
stat -c 'inode=%i | size=%s | %n' \
  /var/ossec/logs/alerts/alerts.json \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-17.json.gz
```

A compressed file gets a new inode when it is compressed. So after compression, the original file cannot be found from the old inode. We keep the design in which only uncompressed JSON files are searched and the Collector stops fail-closed if none is found.

# Chapter 5: Searching the Per-Day Directories Recursively

## 5.1 Creating a Test Copy

Create a test copy from the production code. The production Collector is not stopped.

**Run on: security-core VM 220 (root)**

```bash
set -e

PROD=/usr/local/lib/wazuh-collector/collector.py
TEST=/tmp/wazuh-collector-rotation-test.py

echo "=== VERIFY PRODUCTION HASH ==="
sha256sum "$PROD"

echo
echo "=== CREATE ISOLATED TEST COPY ==="
install -o root -g root -m 755 "$PROD" "$TEST"

cmp "$PROD" "$TEST"

echo
echo "=== VERIFY TEST COPY ==="
sha256sum "$PROD" "$TEST"
stat -c '%n | %U:%G | %a | %s bytes' "$TEST"

echo
echo "=== IMPORTS AND PATH CONSTANTS ==="
sed -n '1,100p' "$TEST"

echo
echo "=== INODE SEARCH FUNCTION ==="
sed -n '300,395p' "$TEST"
```

## 5.2 A Function That Searches Recursively

Replace `find_inode_file()` so that it searches subdirectories as well.

- Only regular uncompressed `.json` files are searched (`.json.gz` is excluded).
- If a permission error or similar occurs during the search, do not treat it as "not found"; pass the exception to the caller (together with the fail-closed behavior from Part 5, 9.3, so that unread data is never silently discarded).

**Run on: security-core VM 220 (root)**

```bash
set -e

TEST=/tmp/wazuh-collector-rotation-test.py

python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-rotation-test.py")
source = path.read_text()

start = source.index("def find_inode_file(inode):")
end = source.index("\n\ndef open_initial_file(state):", start)

replacement = '''def find_inode_file(inode):
    """
    Recursively locate a previous uncompressed JSON alert file.

    Directory traversal errors are propagated. Returning None is allowed
    only after the entire accessible alert tree has been searched.
    Compressed archives are deliberately excluded.
    """
    pending = [ALERT_DIR]

    while pending:
        directory = pending.pop()

        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    pending.append(Path(entry.path))
                    continue

                if not entry.is_file(follow_symlinks=False):
                    continue

                if not entry.name.endswith(".json"):
                    continue

                if entry.inode() == inode:
                    return Path(entry.path)

    return None
'''

updated = source[:start] + replacement + source[end:]
path.write_text(updated)
PY

echo "=== SYNTAX VALIDATION ==="
/usr/bin/python3 -m py_compile "$TEST"

echo
echo "=== CANDIDATE FUNCTION ==="
sed -n '310,375p' "$TEST"

echo
echo "=== PRODUCTION HASH (MUST REMAIN UNCHANGED) ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== TEST COPY HASH ==="
sha256sum "$TEST"
```

## 5.3 Unit Tests

Create a `2026/Nov` structure in a temporary directory and check three behaviors.

**Run on: security-core VM 220 (root)**

```bash
/usr/bin/python3 - <<'PY'
import importlib.util
import tempfile
import gzip
import os
from pathlib import Path

candidate = "/tmp/wazuh-collector-rotation-test.py"

spec = importlib.util.spec_from_file_location(
    "collector_rotation_test", candidate
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    nested = root / "2026" / "Nov"
    nested.mkdir(parents=True)

    old_json = nested / "ossec-alerts-18.json"
    old_json.write_text('{"id":"test-001"}\n')

    archive = nested / "ossec-alerts-17.json.gz"
    with gzip.open(archive, "wt") as f:
        f.write('{"id":"test-archive"}\n')

    module.ALERT_DIR = root

    # TEST 1: recursive discovery
    found = module.find_inode_file(old_json.stat().st_ino)
    assert found == old_json, f"Unexpected path: {found}"
    print("PASS: recursive JSON inode discovery")

    # TEST 2: compressed archive exclusion
    found_archive = module.find_inode_file(archive.stat().st_ino)
    assert found_archive is None, f"Archive unexpectedly found: {found_archive}"
    print("PASS: compressed archive excluded")

    # TEST 3: permission/traversal errors fail closed
    original_scandir = module.os.scandir

    def blocked_scandir(path):
        if Path(path) == root / "2026":
            raise PermissionError("simulated permission denial")
        return original_scandir(path)

    module.os.scandir = blocked_scandir
    try:
        try:
            module.find_inode_file(old_json.stat().st_ino)
        except PermissionError:
            print("PASS: traversal error propagated (fail closed)")
        else:
            raise AssertionError("Traversal error was silently ignored")
    finally:
        module.os.scandir = original_scandir

print("PASS: all recursive inode search tests")
PY
```

## 5.4 Checking in the Real Environment Without Permissions

On the real directories, before the ACLs are changed, have the Collector's user search and confirm that the error is passed on safely (it does not silently return `None`).

**Run on: security-core VM 220 (root)**

```bash
sudo -u wazuh-collector /usr/bin/python3 - <<'PY'
import importlib.util

path = "/tmp/wazuh-collector-rotation-test.py"

spec = importlib.util.spec_from_file_location(
    "collector_rotation_test",
    path,
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

try:
    result = module.find_inode_file(-1)
except PermissionError:
    print("PASS: real directory traversal denied safely")
except OSError as error:
    print("PASS: filesystem error propagated:", type(error).__name__)
else:
    raise AssertionError(
        f"Expected traversal denial, got result={result!r}"
    )
PY

echo
echo "=== PRODUCTION SERVICE STATUS ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts
```

At build time, `PASS: real directory traversal denied safely` was shown, and the production Collector kept the same PID with no increase in its restart count.

# Chapter 6: Minimal ACLs on the Per-Day Directories

## 6.1 The Current ACLs

Recursive search needs both read (`r`), to list a directory's contents, and traverse (`x`). Read permission on the files themselves is already given by the default ACL from Part 3, 7.3. Check before changing anything.

**Run on: security-core VM 220 (root)**

```bash
echo "=== ALERT DIRECTORY ACL ==="
getfacl -p \
  /var/ossec/logs/alerts \
  /var/ossec/logs/alerts/2026 \
  /var/ossec/logs/alerts/2026/Nov

echo
echo "=== CURRENT JSON FILE ACL ==="
getfacl -p \
  /var/ossec/logs/alerts/alerts.json \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json

echo
echo "=== PRODUCTION HASH ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py
```

## 6.2 Adding the ACLs

Add `r-x` for `wazuh-collector` on the existing year and month directories. Other users' and groups' permissions are not changed. Run the commands that change ACLs as root (they fail as an ordinary user).

**Run on: security-core VM 220 (root)**

```bash
setfacl -m u:wazuh-collector:r-x \
  /var/ossec/logs/alerts/2026

setfacl -m u:wazuh-collector:r-x \
  /var/ossec/logs/alerts/2026/Nov

echo "=== UPDATED ACL ==="
getfacl -p \
  /var/ossec/logs/alerts/2026 \
  /var/ossec/logs/alerts/2026/Nov

echo
echo "=== COLLECTOR ACCESS TEST ==="
sudo -u wazuh-collector test -r \
  /var/ossec/logs/alerts/2026 &&
  echo "PASS: year directory readable"

sudo -u wazuh-collector test -x \
  /var/ossec/logs/alerts/2026 &&
  echo "PASS: year directory searchable"

sudo -u wazuh-collector test -r \
  /var/ossec/logs/alerts/2026/Nov &&
  echo "PASS: month directory readable"

sudo -u wazuh-collector test -r \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json &&
  echo "PASS: archived JSON readable"
```

The top-level `alerts` also cannot be listed with `os.scandir()` with the previous `--x` (traverse only), so make it `r-x`.

```bash
setfacl -m u:wazuh-collector:r-x \
  /var/ossec/logs/alerts

echo "=== UPDATED ACL ==="
getfacl -p /var/ossec/logs/alerts

echo
echo "=== ACCESS TEST ==="
sudo -u wazuh-collector test -r /var/ossec/logs/alerts &&
  echo "PASS: alerts directory readable"

sudo -u wazuh-collector test -x /var/ossec/logs/alerts &&
  echo "PASS: alerts directory searchable"
```

| Target | Collector's permission (after the change) |
|---|---|
| `alerts` | `r-x` |
| `alerts/2026` | `r-x` |
| `alerts/2026/Nov` | `r-x` |
| JSON files | `r--` (unchanged) |

> In Part 5, assuming there was no permission to list, we changed startup to prefer opening the current file. That processing remains, so these permissions are used only when looking for the old file after a rotation.

## 6.3 Recursive Search as the Collector's User

**Run on: security-core VM 220 (root)**

```bash
sudo -u wazuh-collector /usr/bin/python3 - <<'PY'
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "collector_rotation_test",
    "/tmp/wazuh-collector-rotation-test.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

current = Path("/var/ossec/logs/alerts/alerts.json")
dated = Path("/var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json")
archive = Path("/var/ossec/logs/alerts/2026/Nov/ossec-alerts-17.json.gz")

for target in (current, dated):
    found = module.find_inode_file(target.stat().st_ino)
    assert found is not None, f"Not found: {target}"
    assert found.stat().st_ino == target.stat().st_ino
    print(f"PASS: discovered inode {target.stat().st_ino}")

if archive.exists():
    found = module.find_inode_file(archive.stat().st_ino)
    assert found is None, f"Compressed archive unexpectedly found: {found}"
    print("PASS: compressed archive excluded")

print("PASS: production-user recursive discovery")
PY
```

## 6.4 Inheritance by Future Year and Month Directories

Check, with a temporary directory inside `alerts`, whether directories created in the future, such as `2027/Jan`, get the same permissions through the default ACL. The temporary directory is created by `mktemp -d` with permissions 700, so give the Collector `r-x` on the top of the test tree before trying. The temporary directory is deleted automatically at the end.

**Run on: security-core VM 220 (root)**

```bash
set -e

TEST_DIR=$(mktemp -d /var/ossec/logs/alerts/.acl-inheritance-test.XXXXXX)
trap 'rm -rf "$TEST_DIR"' EXIT

setfacl -m u:wazuh-collector:r-x "$TEST_DIR"

mkdir -p "$TEST_DIR/2027/Jan"
touch "$TEST_DIR/2027/Jan/test.json"

echo "=== COLLECTOR ACCESS TEST ==="

sudo -u wazuh-collector test -r "$TEST_DIR" &&
  echo "PASS: test root readable"

sudo -u wazuh-collector test -x "$TEST_DIR" &&
  echo "PASS: test root searchable"

sudo -u wazuh-collector test -r "$TEST_DIR/2027" &&
  echo "PASS: future year directory readable"

sudo -u wazuh-collector test -r "$TEST_DIR/2027/Jan" &&
  echo "PASS: future month directory readable"

sudo -u wazuh-collector test -r "$TEST_DIR/2027/Jan/test.json" &&
  echo "PASS: future JSON file readable"

sudo -u wazuh-collector test -x "$TEST_DIR/2027/Jan" &&
  echo "PASS: future month directory searchable"

echo "PASS: all ACL inheritance access tests"
```

> This command uses `set -e` and `trap`, so running it in an interactive shell may close the shell when it ends. In that case, log in again.

# Chapter 7: Deploying the Recursive-Search Version to Production

## 7.1 Checking the Diff and the Caller

**Run on: security-core VM 220 (root)**

```bash
echo "=== PRODUCTION SHA256 ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== TEST CANDIDATE SHA256 ==="
sha256sum /tmp/wazuh-collector-rotation-test.py

echo
echo "=== CODE DIFF ==="
diff -u \
  /usr/local/lib/wazuh-collector/collector.py \
  /tmp/wazuh-collector-rotation-test.py

echo
echo "=== PRODUCTION SERVICE ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts
```

The only difference is the one function `find_inode_file()`.

| Item | Production | Candidate |
|---|---|---|
| Search scope | Directly under `alerts` only | Recursively into subdirectories |
| Target | Regular files | Regular `.json` files (`.json.gz` excluded) |
| Search errors | Warn and return `None` | Pass the exception to the caller |

```bash
echo "=== open_initial_file ==="
grep -n -A55 -B5 '^def open_initial_file' \
  /tmp/wazuh-collector-rotation-test.py

echo
echo "=== find_inode_file CALL SITES ==="
grep -n -B8 -A12 'find_inode_file(' \
  /tmp/wazuh-collector-rotation-test.py

echo
echo "=== ROTATION SWITCH LOGIC ==="
grep -n -B12 -A35 'ALERT_FILE.stat' \
  /tmp/wazuh-collector-rotation-test.py

echo
echo "=== SERVICE STATUS ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts
```

The caller, `open_initial_file()`, re-checks the inode with `fstat()` before reading the old file it found, and stops with `RuntimeError` if none is found. This does not affect the normal rotation switch (Part 5).

> **Remaining limitation:** If the old file has already been compressed (become `.json.gz`), the original inode cannot be found. In that case it refuses to start (fail-closed).

## 7.2 Replacing the Production Code

Check the candidate's hash and syntax and that the service is running, preserve the current production code (`7a816056...`), and then replace it in one step. The service is not restarted yet, so the running process still uses the old code.

**Run on: security-core VM 220 (root)**

```bash
set -euo pipefail

PROD="/usr/local/lib/wazuh-collector/collector.py"
CANDIDATE="/tmp/wazuh-collector-rotation-test.py"
BACKUP="/usr/local/lib/wazuh-collector/collector.py.backup-before-recursive-rotation-20261119"
EXPECTED="ac2974775d46b902ee69b3e7219bf9cb550c7d8a65c38cbdf8ac89ecc67a5e96"

echo "=== PRECHECK ==="

test -f "$PROD"
test -f "$CANDIDATE"
test ! -e "$BACKUP"

ACTUAL=$(sha256sum "$CANDIDATE" | awk '{print $1}')
test "$ACTUAL" = "$EXPECTED"

systemctl is-active --quiet wazuh-collector

/usr/bin/python3 -m py_compile "$CANDIDATE"

echo "PASS: candidate hash and syntax verified"
echo "PASS: production service is active"

echo
echo "=== BACKUP CURRENT PRODUCTION ==="

cp -a "$PROD" "$BACKUP"

cmp -s "$PROD" "$BACKUP"
echo "PASS: production backup verified"

echo
echo "=== PREPARE ATOMIC REPLACEMENT ==="

TEMP="${PROD}.new.$$"

install -o root -g root -m 755 "$CANDIDATE" "$TEMP"

test "$(sha256sum "$TEMP" | awk '{print $1}')" = "$EXPECTED"

echo
echo "=== ATOMIC REPLACEMENT ==="

mv -f "$TEMP" "$PROD"

echo
echo "=== VERIFY DEPLOYMENT ==="

sha256sum "$PROD" "$BACKUP"

stat -c '%n | %U:%G | %a | %s bytes' "$PROD" "$BACKUP"

test "$(sha256sum "$PROD" | awk '{print $1}')" = "$EXPECTED"
test "$(sha256sum "$BACKUP" | awk '{print $1}')" = \
  "7a81605628ccefa5284d6a32559d8431108e61fe3213fb74ae0479ec051d4244"

echo "PASS: atomic deployment completed"

echo
echo "=== SERVICE STILL RUNNING ==="

systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts
```

Replace `EXPECTED` with the candidate hash for your environment shown in 5.2. Also replace `7a816056...` in the final `test` with your own production hash before the replacement.

## 7.3 Restarting and Checking

**Run on: security-core VM 220 (root)**

```bash
systemctl restart wazuh-collector

echo "=== SERVICE STATUS ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p ExecMainStatus

echo
echo "=== RECENT SERVICE LOG ==="
journalctl -u wazuh-collector -n 20 --no-pager
```

```bash
echo "=== LOGS SINCE NEW START ==="
journalctl -u wazuh-collector \
  --since "2026-11-18 20:54:31" \
  --no-pager

echo
echo "=== PROCESS STATUS ==="
ps -p 90884 -o pid,ppid,stat,etime,%cpu,%mem,cmd

echo
echo "=== COLLECTOR STATE ==="
/usr/bin/python3 - <<'PY'
import json
from pathlib import Path

p = Path("/var/lib/wazuh-collector/state.json")
s = json.loads(p.read_text())
print("saved_inode =", s.get("inode"))
print("saved_offset =", s.get("offset"))
PY

echo
echo "=== CURRENT ALERT FILE ==="
stat -c 'inode=%i size=%s' /var/ossec/logs/alerts/alerts.json

echo
echo "=== PRODUCTION HASH ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py
```

Replace the `--since` time and the PID in `ps -p` with your environment's values. At build time it ran with the new PID `90884` and 0 restarts, and the saved inode and position matched the current `alerts.json`.

```bash
echo "=== RECENT COLLECTOR LOG ==="
journalctl -u wazuh-collector -n 40 --no-pager

echo
echo "=== SERVICE STATUS ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p ExecMainStatus

echo
echo "=== STATE FILE METADATA ==="
stat -c '%U:%G %a %s bytes %y' \
  /var/lib/wazuh-collector/state.json
```

> Right after startup, `PostgreSQL connection established` may not appear in the log. In the reading loop from Part 4, Chapter 4, the DB connection is made only "when a new normal alert line is read" (checked in the next chapter).

```bash
echo "=== COLLECTOR RUN / DB CONNECTION FLOW ==="
nl -ba /usr/local/lib/wazuh-collector/collector.py \
  | sed -n '450,545p;640,700p'
```

# Chapter 8: Auditing Ingestion After the Restart

## 8.1 When the DB Connection Is Made

In `run()`, the DB connection is first made under the following condition.

```python
if status == "line":
    if connection is None or connection.closed:
        connection = psycopg.connect(**DB_CONFIG)
```

That is, after starting and resuming from the read position, it connects when it reads a new alert line. Until a new alert arrives, no connection log appears. Wait a while and then check. This check reads the state file, so it is done as root (as an ordinary user you get `PermissionError`; this is an intended restriction).

**Run on: security-core VM 220 (root)**

```bash
echo "=== COLLECTOR STATUS ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p ExecMainStatus

echo
echo "=== STATE ==="
python3 - <<'PY'
import json
from pathlib import Path

s = json.loads(
    Path("/var/lib/wazuh-collector/state.json").read_text()
)
print("inode =", s.get("inode"))
print("offset =", s.get("offset"))
PY

echo
echo "=== ALERT FILE ==="
stat -c 'inode=%i size=%s' /var/ossec/logs/alerts/alerts.json

echo
echo "=== RECENT APPLICATION LOGS ==="
journalctl -u wazuh-collector -n 12 --no-pager
```

At build time, the following log appeared about two minutes after the restart.

```text
Nov 18 20:56:25 security-core python3[90884]: 2026-11-18 20:56:25,729 INFO PostgreSQL connection established
```

## 8.2 Continued Ingestion

**Run on: LXC 109 postgresql (root)**

> The `postgres` user exists only on LXC 109. Running this on security-core gives `unknown user postgres`.

```bash
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    COUNT(*) AS total_events,
    COUNT(*) FILTER (
        WHERE ingested_at >= NOW() - INTERVAL '1 hour'
    ) AS ingested_last_1h,
    COUNT(*) FILTER (
        WHERE ingested_at >= NOW() - INTERVAL '24 hours'
    ) AS ingested_last_24h,
    MAX(event_timestamp) AS latest_event_timestamp,
    MAX(ingested_at) AS latest_ingested_at,
    NOW() AS database_time
FROM incident.alert_events;
"
```

## 8.3 Duplicates and Required Fields

```bash
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    COUNT(*) AS total_events,
    COUNT(event_id) AS nonnull_event_ids,
    COUNT(DISTINCT event_id) AS unique_event_ids,
    COUNT(*) - COUNT(DISTINCT event_id) AS duplicate_excess,
    COUNT(*) FILTER (WHERE event_id IS NULL) AS null_event_ids,
    COUNT(*) FILTER (WHERE ingested_at IS NULL) AS null_ingested_at,
    COUNT(*) FILTER (WHERE rule_id IS NULL) AS null_rule_ids,
    COUNT(*) FILTER (WHERE agent_id IS NULL) AS null_agent_ids,
    COUNT(*) FILTER (WHERE rule_level IS NULL) AS null_rule_levels
FROM incident.alert_events;
"
```

At build time there were 687 rows, with zero duplicates and zero missing event IDs, ingestion times, rule IDs, agent IDs or levels.

## 8.4 Ingestion Counts per Five Minutes

```bash
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    date_bin(
        INTERVAL '5 minutes',
        ingested_at,
        TIMESTAMPTZ '2000-01-01 00:00:00+00'
    ) AS interval_start,
    COUNT(*) AS event_count,
    MIN(ingested_at) AS first_ingested,
    MAX(ingested_at) AS last_ingested
FROM incident.alert_events
WHERE ingested_at >= NOW() - INTERVAL '1 hour'
GROUP BY 1
ORDER BY 1;
"
```

Check that there is no time period in which ingestion stopped.

## 8.5 Keeping Up with Reading and the Count After the Restart

**Run on: security-core VM 220 (root)**

```bash
echo "=== WAZUH ALERT FILE ==="
stat -c 'inode=%i size=%s modified=%y' \
  /var/ossec/logs/alerts/alerts.json

echo
echo "=== COLLECTOR STATE ==="
python3 - <<'PY'
import json
from pathlib import Path

p = Path("/var/lib/wazuh-collector/state.json")
s = json.loads(p.read_text())
print("inode =", s.get("inode"))
print("offset =", s.get("offset"))
PY

echo
echo "=== COLLECTOR STATUS ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts
```

**Run on: LXC 109 postgresql (root)**

```bash
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    COUNT(*) AS inserted_after_restart,
    COUNT(DISTINCT event_id) AS unique_events,
    COUNT(*) - COUNT(DISTINCT event_id) AS duplicate_excess,
    MIN(ingested_at) AS first_ingested,
    MAX(ingested_at) AS latest_ingested
FROM incident.alert_events
WHERE ingested_at >= TIMESTAMPTZ '2026-11-18 20:54:31+00';
"
```

Replace the time with when you restarted in 7.3. At build time, 14 rows were inserted after the restart, all unique.

# Chapter 9: How Rotation Works and the Restart History

Without causing a rotation yet, and using reads only, we sort out how Wazuh rotates and what caused the Collector's stops so far.

## 9.1 What Performs the Rotation

**Run on: security-core VM 220 (root)**

```bash
echo "=== LOGROTATE CONFIGURATION ==="
grep -RniE 'wazuh|alerts|ossec' \
  /etc/logrotate.conf /etc/logrotate.d 2>/dev/null || true

echo
echo "=== RELATED TIMERS ==="
systemctl list-timers --all --no-pager \
  | grep -Ei 'wazuh|logrotate|ossec' || true

echo
echo "=== RELATED CRON JOBS ==="
grep -RniE 'wazuh|alerts|ossec|logrotate' \
  /etc/cron.d /etc/cron.daily /etc/cron.hourly \
  /var/spool/cron/crontabs 2>/dev/null || true

echo
echo "=== ALERT DIRECTORY STRUCTURE ==="
find /var/ossec/logs/alerts \
  -maxdepth 4 -type f \
  -printf '%TY-%Tm-%Td %TH:%TM:%TS | inode=%i | size=%s | %p\n' \
  2>/dev/null | sort | tail -60
```

Neither logrotate nor cron has settings for Wazuh alerts.

```bash
echo "=== ALERT FILE LINK RELATIONSHIP ==="
stat -c '%n | inode=%i | links=%h | size=%s | owner=%U:%G | mode=%a' \
  /var/ossec/logs/alerts/alerts.json \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json

echo
echo "=== ALERT DIRECTORY ENTRIES ==="
ls -lai /var/ossec/logs/alerts
ls -lai /var/ossec/logs/alerts/2026/Nov

echo
echo "=== WAZUH MANAGER PROCESSES ==="
ps -eo pid,ppid,user,stat,etime,args \
  | grep -E '[w]azuh-(analysisd|monitord|managerd|logcollector)'

echo
echo "=== WAZUH MANAGER SERVICE ==="
systemctl show wazuh-manager \
  -p ActiveState -p SubState -p MainPID -p NRestarts
```

```text
/var/ossec/logs/alerts/
├── alerts.json
├── alerts.log
└── 2026/
    └── Nov/
        ├── ossec-alerts-17.json.gz
        ├── ossec-alerts-17.json.sum
        ├── ossec-alerts-17.log.gz
        ├── ossec-alerts-17.log.sum
        ├── ossec-alerts-18.json
        └── ossec-alerts-18.log
```

## 9.2 Wazuh's Rotation Settings

**Run on: security-core VM 220 (root)**

```bash
echo "=== WAZUH MONITORING CONFIGURATION ==="
grep -n -A8 -B5 -E 'rotate|compress|alerts|log_alert' \
  /var/ossec/etc/ossec.conf

echo
echo "=== WAZUH MONITORD REFERENCES ==="
grep -RniE 'alerts\.json|ossec-alerts|rotate|compress' \
  /var/ossec/etc \
  /var/ossec/queue \
  2>/dev/null | head -100

echo
echo "=== WAZUH VERSION ==="
/var/ossec/bin/wazuh-control info 2>/dev/null | head -30
```

```bash
echo "=== MONITORD ROTATION SETTINGS ==="
grep -n -B3 -A3 -E \
  '^monitord\.(day_wait|compress|rotate_log|size_rotate)=' \
  /var/ossec/etc/internal_options.conf

echo
echo "=== ANALYSISD ROTATION SETTINGS ==="
grep -n -B3 -A3 -E \
  '^analysisd\.min_rotate_interval=' \
  /var/ossec/etc/internal_options.conf

echo
echo "=== WAZUH MONITORD OPEN FILES ==="
MONITORD_PID=$(pgrep -xo wazuh-monitord)
echo "PID=$MONITORD_PID"
lsof -nP -p "$MONITORD_PID" 2>/dev/null \
  | grep -E 'alerts|ossec-alerts' || true

echo
echo "=== ALERT FILE OPEN HANDLES ==="
lsof -nP /var/ossec/logs/alerts/alerts.json 2>/dev/null || true
```

```bash
echo "=== WAZUH INTERNAL LOG ROTATION RECORDS ==="
grep -iE 'rotat|compress|sign|alerts\.json|ossec-alerts' \
  /var/ossec/logs/ossec.log 2>/dev/null | tail -80

echo
echo "=== MONITORD JOURNAL ==="
journalctl --no-pager -u wazuh-manager \
  --since "2026-11-18 00:00:00" \
  --until "2026-11-19 00:00:00" 2>/dev/null \
  | grep -iE 'monitord|rotat|compress|alerts' | tail -60

echo
echo "=== ROTATED JSON FILES ==="
find /var/ossec/logs/alerts -type f \
  -name 'ossec-alerts-*.json*' \
  -printf '%TY-%Tm-%Td %TH:%TM:%TS | %i | %s | %p\n' \
  | sort
```

| Item | Details |
|---|---|
| What rotates | The Wazuh Manager's `wazuh-monitord` (not logrotate) |
| Interval | Daily (`monitord.rotate_log=1`). At build time, `Starting new log after rotation.` was logged at `00:00:10` |
| Compression | Enabled (`monitord.compress=1`). The previous day's JSON becomes `.json.gz` |
| Signing | Enabled (`monitord.sign=1`). A `.sum` is created |
| Today's file | `alerts.json` and `year/month/ossec-alerts-day.json` share the same inode (hard link) |

## 9.3 History of the Collector's Stops

**Run on: security-core VM 220 (root)**

```bash
echo "=== COLLECTOR JOURNAL ==="
journalctl -u wazuh-collector \
  --since "2026-11-18 00:00:00" \
  --no-pager \
  | grep -E 'starting|Resuming|rotation|PostgreSQL|ERROR|WARNING|Stopping|Started'

echo
echo "=== COLLECTOR CURRENT STATE ==="
python3 - <<'PY'
import json
from pathlib import Path

p = Path("/var/lib/wazuh-collector/state.json")
s = json.loads(p.read_text())
print("inode:", s.get("inode"))
print("offset:", s.get("offset"))
PY

echo
echo "=== CURRENT ALERT FILE ==="
stat -c 'inode=%i size=%s modified=%y' \
  /var/ossec/logs/alerts/alerts.json

echo
echo "=== COLLECTOR PROCESS ==="
systemctl show wazuh-collector \
  -p MainPID -p NRestarts -p ActiveState -p SubState
```

```bash
echo "=== COLLECTOR FAILURE WINDOW ==="
journalctl -u wazuh-collector \
  --since "2026-11-18 15:14:50" \
  --until "2026-11-18 15:17:10" \
  --no-pager -o short-iso

echo
echo "=== SYSTEMD FAILURE DETAILS ==="
journalctl \
  --since "2026-11-18 15:14:50" \
  --until "2026-11-18 15:17:10" \
  --no-pager \
  | grep -Ei 'wazuh-collector|failed|failure|traceback|permission|denied|killed|oom|error'
```

Replace the times with the period when startup failed in Part 5, 8.5. All 19 failed restarts had the same cause.

```text
collector.py
  run()
    └─ open_initial_file()
         └─ find_inode_file()
              └─ os.scandir('/var/ossec/logs/alerts')
```

It lacked permission to list `/var/ossec/logs/alerts` and exited with `PermissionError` (Part 5, 8.5). This problem has been resolved by the code fix in Part 5, 9.1 and the ACLs in Chapter 6.

## 9.4 Final Check of the ACLs

**Run on: security-core VM 220 (root)**

```bash
echo "=== ALERT DIRECTORY ACL ==="
getfacl -p /var/ossec/logs/alerts

echo
echo "=== YEAR DIRECTORY ACL ==="
getfacl -p /var/ossec/logs/alerts/2026

echo
echo "=== MONTH DIRECTORY ACL ==="
getfacl -p /var/ossec/logs/alerts/2026/Nov

echo
echo "=== COLLECTOR USER ACCESS ==="
sudo -u wazuh-collector test -r /var/ossec/logs/alerts \
  && echo "PASS: directory readable" \
  || echo "FAIL: directory unreadable"

sudo -u wazuh-collector test -x /var/ossec/logs/alerts \
  && echo "PASS: directory searchable" \
  || echo "FAIL: directory not searchable"
```

```bash
echo "=== DEFAULT ACL ON ALERT ROOT ==="
getfacl -cp /var/ossec/logs/alerts \
  | grep '^default:'

echo
echo "=== EXISTING JSON FILE ACL ==="
getfacl -cp /var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json

echo
echo "=== COLLECTOR READ ACCESS TO CURRENT JSON ==="
sudo -u wazuh-collector test -r \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json \
  && echo "PASS: JSON readable" \
  || echo "FAIL: JSON unreadable"
```

| Item | Result |
|---|---|
| Directories | `r-x` for the Collector (list and traverse) |
| JSON files | `r--` for the Collector (read only) |
| Write | None (cannot change or delete Wazuh's logs) |
| Future directories | Inherit the same permissions through the default ACL |

# Chapter 10: Sorting Out the Cause of the Restart Loop

## 10.1 systemd's Restart Settings

**Run on: security-core VM 220 (root)**

```bash
echo "=== COLLECTOR RESTART POLICY ==="
systemctl show wazuh-collector \
  -p Restart \
  -p RestartSec \
  -p StartLimitIntervalUSec \
  -p StartLimitBurst \
  -p NRestarts

echo
echo "=== SERVICE UNIT ==="
systemctl cat wazuh-collector
```

| Setting | Value | Meaning |
|---|---:|---|
| `Restart` | `always` | Restart when it exits |
| `RestartSec` | 5 seconds | Wait before restarting |
| `StartLimitIntervalUSec` | 10 seconds | Period over which starts are counted |
| `StartLimitBurst` | 5 | Stop starting it if this number is exceeded |

The start limit applies when "it starts more than 5 times within 10 seconds". The restart interval is 5 seconds, so it starts only twice in 10 seconds and never reaches the limit. That is why it restarted as many as 19 times in Part 5, 8.5.

```bash
echo "=== MAIN LOOP AND EXCEPTION HANDLING ==="
nl -ba /usr/local/lib/wazuh-collector/collector.py \
  | sed -n '450,510p;650,710p'

echo
echo "=== EXCEPTION HANDLERS ==="
grep -n -E 'except |finally:|raise |sys\.exit|SystemExit|KeyboardInterrupt' \
  /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== SYSTEMD START LIMIT HISTORY ==="
journalctl -u wazuh-collector \
  --since "2026-11-18 15:14:50" \
  --until "2026-11-18 15:17:10" \
  --no-pager \
  | grep -Ei 'start request repeated|start-limit|scheduled restart|failed'
```

## 10.2 The Structure of Startup Processing

**Run on: security-core VM 220 (root)**

```bash
echo "=== RUN FUNCTION: INITIALIZATION AND MAIN LOOP ==="
nl -ba /usr/local/lib/wazuh-collector/collector.py \
  | sed -n '450,570p'

echo
echo "=== RUN FUNCTION: ROTATION AND SHUTDOWN ==="
nl -ba /usr/local/lib/wazuh-collector/collector.py \
  | sed -n '570,710p'

echo
echo "=== MODULE ENTRY POINT ==="
nl -ba /usr/local/lib/wazuh-collector/collector.py \
  | sed -n '700,730p'
```

```bash
echo "=== LOAD STATE ==="
nl -ba /usr/local/lib/wazuh-collector/collector.py \
  | sed -n '240,330p'

echo
echo "=== FIND INODE AND OPEN INITIAL FILE ==="
nl -ba /usr/local/lib/wazuh-collector/collector.py \
  | sed -n '310,430p'

echo
echo "=== CURRENT PRODUCTION CODE HASH ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py
```

The initialization part of `run()` is outside the `try/finally`.

```python
state = load_state()
handle, active_inode = open_initial_file(state)

try:
    while True:
```

| Item | Current behavior | Assessment |
|---|---|---|
| Exception during initialization | Not caught; the process exits (systemd restarts it) | Intended, so that unread data is never silently discarded. But the restarts go on indefinitely |
| DB connection error | Waits 5 seconds and retries (the process does not exit) | No problem |
| Saved position larger than the file | On the next line, it silently moves to the end of the file | **Needs fixing** (may discard unread data) |

```python
handle.seek(min(old_offset, actual_stat.st_size))
```

A saved read position larger than the file size is a state that normally does not occur, for example when the file has become shorter (been truncated). Moving to the end and continuing would mean not noticing that alerts in between had been missed. In line with the fail-closed policy, we change it to refuse to start.

## 10.3 Checking the Runtime Environment

**Run on: security-core VM 220 (root)**

```bash
echo "=== PYTHON VERSION ==="
python3 --version

echo
echo "=== COLLECTOR IMPORTS AND CONFIGURATION ==="
nl -ba /usr/local/lib/wazuh-collector/collector.py \
  | sed -n '1,120p'

echo
echo "=== SYSTEMD VERSION ==="
systemd --version | head -n 2

echo
echo "=== PRODUCTION SERVICE STATUS ==="
systemctl show wazuh-collector \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p NRestarts
```

At build time this was Python 3.12.3 and systemd 255.4, and the production Collector was running as PID `90884` with 0 restarts.

# Chapter 11: Validating the Read Position at Startup

The following fixes are also made on a test copy, without stopping production.

## 11.1 Creating a Test Copy

**Run on: security-core VM 220 (root)**

```bash
TEST_FILE=/tmp/wazuh-collector-step330-test.py

cp --preserve=mode,ownership \
  /usr/local/lib/wazuh-collector/collector.py \
  "$TEST_FILE"

chmod 600 "$TEST_FILE"

echo "=== TEST COPY ==="
stat -c '%n | owner=%U:%G | mode=%a | size=%s' "$TEST_FILE"

echo
echo "=== HASH COMPARISON ==="
sha256sum \
  /usr/local/lib/wazuh-collector/collector.py \
  "$TEST_FILE"

echo
echo "=== PYTHON SYNTAX CHECK ==="
python3 -m py_compile "$TEST_FILE" \
  && echo "PASS: syntax valid"
```

```bash
echo "=== FUNCTION DEFINITIONS ==="
grep -n '^def ' /tmp/wazuh-collector-step330-test.py

echo
echo "=== FILE AND STATE CONSTANTS ==="
grep -nE '^(ALERT_FILE|ALERT_DIR|STATE_FILE|POLL_INTERVAL|MAX_ALERT_LINE_BYTES|READ_CHUNK_BYTES)' \
  /tmp/wazuh-collector-step330-test.py

echo
echo "=== FILE OPEN AND SEEK OPERATIONS ==="
grep -nE 'open\(|\.seek\(|\.tell\(|fstat\(|\.stat\(' \
  /tmp/wazuh-collector-step330-test.py
```

## 11.2 Reproducing the Behavior Before the Fix

In a temporary directory, check the behavior before the fix. Reproduce how it silently moves to the end when the saved position is larger than the file.

**Run on: security-core VM 220 (root)**

```bash
cat > /tmp/test_step330_baseline.py <<'PY'
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch

source = "/tmp/wazuh-collector-step330-test.py"

spec = importlib.util.spec_from_file_location("collector_test", source)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)

with tempfile.TemporaryDirectory(prefix="step330-") as tmp:
    root = Path(tmp)
    alert_dir = root / "alerts"
    alert_dir.mkdir()

    alert_file = alert_dir / "alerts.json"
    alert_file.write_bytes(b'{"test":"event"}\n')

    collector.ALERT_FILE = alert_file
    collector.ALERT_DIR = alert_dir
    collector.STATE_FILE = root / "state" / "state.json"

    actual_inode = alert_file.stat().st_ino
    actual_size = alert_file.stat().st_size

    # Test 1: normal resume
    handle, inode = collector.open_initial_file((actual_inode, 0))
    assert inode == actual_inode
    assert handle.tell() == 0
    handle.close()
    print("PASS: normal resume")

    # Test 2: offset larger than file size
    handle, inode = collector.open_initial_file(
        (actual_inode, actual_size + 100)
    )
    observed_offset = handle.tell()
    handle.close()

    print(
        "BASELINE:",
        f"saved_offset={actual_size + 100}",
        f"actual_size={actual_size}",
        f"resumed_offset={observed_offset}",
    )

    if observed_offset == actual_size:
        print("CONFIRMED: current code silently clamps oversized offset")
    else:
        raise AssertionError("Unexpected offset behavior")

    # Test 3: missing previous inode must fail closed
    try:
        collector.open_initial_file((9223372036854775807, 0))
    except RuntimeError as error:
        print("PASS: missing inode fails closed:", str(error))
    else:
        raise AssertionError("Missing inode was not rejected")

    # Test 4: traversal error must propagate
    with patch.object(
        collector.os,
        "scandir",
        side_effect=PermissionError("test permission failure"),
    ):
        try:
            collector.find_inode_file(9223372036854775807)
        except PermissionError:
            print("PASS: traversal PermissionError propagates")
        else:
            raise AssertionError("Traversal error was swallowed")

print("PASS: baseline tests completed")
PY

python3 /tmp/test_step330_baseline.py
```

At build time, with a saved position of 117 and a file size of 17, the resume position became 17, reproducing the problem.

```text
saved_offset=117
actual_size=17
resumed_offset=17
```

## 11.3 The Fix

In two places, the current file and the rotated file, check the position before `seek()` and stop with `RuntimeError` if it is larger than the file.

**Run on: security-core VM 220 (root)**

```bash
echo "=== OPEN INITIAL FILE ==="
sed -n '340,410p' /tmp/wazuh-collector-step330-test.py

echo
echo "=== STATE SAVE AND LOAD ==="
sed -n '249,313p' /tmp/wazuh-collector-step330-test.py
```

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-step330-test.py")
source = path.read_text(encoding="utf-8")

old_current = '''        if actual_stat.st_ino == old_inode:
            handle.seek(min(old_offset, actual_stat.st_size))
            logging.info("Resuming current alert file")
            return handle, actual_stat.st_ino
'''

new_current = '''        if actual_stat.st_ino == old_inode:
            if old_offset > actual_stat.st_size:
                raise RuntimeError(
                    "Saved offset exceeds current alert file size; "
                    "refusing unsafe resume"
                )

            handle.seek(old_offset)
            logging.info("Resuming current alert file")
            return handle, actual_stat.st_ino
'''

old_rotated = '''        handle.seek(min(old_offset, actual_stat.st_size))
        logging.info("Resuming previous rotated alert file")
'''

new_rotated = '''        if old_offset > actual_stat.st_size:
            raise RuntimeError(
                "Saved offset exceeds previous alert file size; "
                "refusing unsafe resume"
            )

        handle.seek(old_offset)
        logging.info("Resuming previous rotated alert file")
'''

if source.count(old_current) != 1:
    raise SystemExit("ABORT: current-file target is not unique")

if source.count(old_rotated) != 1:
    raise SystemExit("ABORT: rotated-file target is not unique")

updated = source.replace(old_current, new_current, 1)
updated = updated.replace(old_rotated, new_rotated, 1)

path.write_text(updated, encoding="utf-8")
print("PASS: test copy updated")
PY

echo
echo "=== MODIFIED RESUME CHECKS ==="
sed -n '355,410p' /tmp/wazuh-collector-step330-test.py

echo
echo "=== SYNTAX CHECK ==="
python3 -m py_compile /tmp/wazuh-collector-step330-test.py
```

> For the current file, the exception is passed to the caller after `except Exception:` in `open_initial_file()` closes the file.

## 11.4 Validating the Read Position

**Run on: security-core VM 220 (root)**

```bash
cat > /tmp/test_step330_offset.py <<'PY'
import importlib.util
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-step330-test.py",
)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)

def expect_rejection(label, state):
    try:
        handle, inode = collector.open_initial_file(state)
    except RuntimeError as error:
        print(f"PASS: {label}: {error}")
    else:
        handle.close()
        raise AssertionError(f"FAIL: {label}: unsafe resume accepted")

with tempfile.TemporaryDirectory(prefix="step330-offset-") as tmp:
    root = Path(tmp)
    alert_dir = root / "alerts"
    rotated_dir = alert_dir / "2026" / "Nov"
    rotated_dir.mkdir(parents=True)

    current = alert_dir / "alerts.json"
    current.write_bytes(b'{"current":true}\n')

    collector.ALERT_FILE = current
    collector.ALERT_DIR = alert_dir
    collector.STATE_FILE = root / "state" / "state.json"

    current_inode = current.stat().st_ino
    current_size = current.stat().st_size

    # 1. Current file: valid offset
    handle, inode = collector.open_initial_file(
        (current_inode, 3)
    )
    assert inode == current_inode
    assert handle.tell() == 3
    handle.close()
    print("PASS: current file valid offset")

    # 2. Current file: oversized offset
    expect_rejection(
        "current file oversized offset",
        (current_inode, current_size + 100),
    )

    # 3. Rotated file: valid offset
    rotated = rotated_dir / "ossec-alerts-old.json"
    rotated.write_bytes(b'{"previous":true}\n')
    rotated_inode = rotated.stat().st_ino

    handle, inode = collector.open_initial_file(
        (rotated_inode, 5)
    )
    assert inode == rotated_inode
    assert handle.tell() == 5
    handle.close()
    print("PASS: rotated file valid offset")

    # 4. Rotated file: oversized offset
    rotated_size = rotated.stat().st_size
    expect_rejection(
        "rotated file oversized offset",
        (rotated_inode, rotated_size + 100),
    )

    # 5. Missing inode
    expect_rejection(
        "missing inode",
        (9223372036854775807, 0),
    )

print("PASS: all offset safety tests completed")
PY

python3 /tmp/test_step330_offset.py
```

| Check | Result |
|---|---|
| Current file: correct position | Resumes |
| Current file: position larger than the file | Refuses to start |
| Rotated file: correct position | Resumes |
| Rotated file: position larger than the file | Refuses to start |
| Old inode not found | Refuses to start |

## 11.5 Checking the Diff and Production

**Run on: security-core VM 220 (root)**

```bash
echo "=== TEST COPY DIFF ==="
diff -u \
  /usr/local/lib/wazuh-collector/collector.py \
  /tmp/wazuh-collector-step330-test.py

echo
echo "=== PRODUCTION SHA256 ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== TEST COPY SHA256 ==="
sha256sum /tmp/wazuh-collector-step330-test.py

echo
echo "=== PRODUCTION SERVICE STATUS ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts
```

If no diff is shown, also check the exit code. `diff` returns exit code 1 when there are differences (this is not an error).

```bash
diff -u \
  /usr/local/lib/wazuh-collector/collector.py \
  /tmp/wazuh-collector-step330-test.py

echo "DIFF_EXIT_CODE=$?"
```

Confirm that only two places in `open_initial_file()` changed and that production (`ac297477...`) has not changed.

## 11.6 Checking for an inode Mix-Up

Confirm that when the search for the old file returns a file with a different inode from the saved one, the Collector stops without reading that file.

**Run on: security-core VM 220 (root)**

```bash
cat > /tmp/test_step330_inode.py <<'PY'
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-step330-test.py",
)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)

with tempfile.TemporaryDirectory(prefix="step330-inode-") as tmp:
    root = Path(tmp)
    alert_dir = root / "alerts"
    alert_dir.mkdir()

    current = alert_dir / "alerts.json"
    impostor = alert_dir / "impostor.json"

    current.write_bytes(b'{"current":true}\n')
    impostor.write_bytes(b'{"impostor":true}\n')

    collector.ALERT_FILE = current
    collector.ALERT_DIR = alert_dir
    collector.STATE_FILE = root / "state" / "state.json"

    wrong_inode = impostor.stat().st_ino

    # Return a path whose actual inode differs from the saved inode.
    with patch.object(
        collector,
        "find_inode_file",
        return_value=impostor,
    ):
        try:
            collector.open_initial_file((wrong_inode + 1, 0))
        except RuntimeError as error:
            print("PASS: inode mismatch rejected:", str(error))
        else:
            raise AssertionError("Mismatched inode was accepted")

    # Verify the real inode can still be located normally.
    found = collector.find_inode_file(wrong_inode)
    assert found == impostor
    print("PASS: recursive inode lookup returns matching file")

print("PASS: inode identity tests completed")
PY

python3 /tmp/test_step330_inode.py
```

# Summary of Part 6

In Part 6 we confirmed, down to individual event IDs, that the hardened Collector puts alerts into the DB "with nothing missing and nothing doubled", and finished it to fit the actual structure of rotation.

| Check / change | Result |
|---|---|
| Duplicate prevention | Guaranteed by the DB primary key. Confirmed with a temporary table and a mock that a second insert is rejected |
| Completeness | The SHA-256 of the set of 413 event IDs matches between alerts.json and the DB |
| Rotation structure | `wazuh-monitord` moves files to `year/month` daily and compresses the previous day's file |
| Searching for the old file | Changed to a recursive search (`.json.gz` excluded, search errors fail-closed) and deployed to production |
| ACLs | `r-x` for the Collector on the `alerts`, year and month directories; inherited by future directories |
| After restart | The DB connection is established when a new alert is read. Ingestion continues with 0 duplicates |
| Read position validation | Confirmed in the test version a fix that refuses to start when the saved position is larger than the file (deployed to production in Part 7) |

| Production file | SHA-256 (at build time) |
|---|---|
| `collector.py` (recursive-search version) | `ac297477...` |
| `collector.py.backup-before-recursive-rotation-20261119` | `7a816056...` (the Part 5 version) |

> **Remaining limitation:** If the old file has already been compressed, the original inode cannot be found and the Collector refuses to start (Chapter 7, 7.1). Take care when stopping the Collector across a date change.

In Part 7, we continue verifying the test version `/tmp/wazuh-collector-step330-test.py`, check the release of files on abnormal exit and resistance to huge lines and deeply nested JSON, and then deploy it to production.

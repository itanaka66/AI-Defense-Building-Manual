---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 9: Recovering from a Collector Stop and Checking Operations"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 9 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". After the monitoring platform was completed in Part 8, a check made before moving on to the next stage (the SOC data integration platform) found that the Wazuh Collector had stopped. Part 9 covers finding the cause, ingesting the missed alerts into the DB, returning to normal collection, then checking monitoring, the DB, time and event contents, and dealing with the problem found (a flood of events).

This is an actual occurrence of "resuming after the old file has been compressed", listed under "Open Issues" in Part 7.

## Notation

- Commands and file contents are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Each step begins with "Run on", which says where to run it.
- "Example output" is the actual output from the build. Inodes, counts, times and so on will differ in your environment.
- Commands that display the contents of the state file (`state.json`) or connection details are not included.

## What Had Happened (Summary)

| Order | Details |
|---|---|
| 1 | At 23:53 on November 18, the Collector read the 18th's `alerts.json` to the end and saved its state |
| 2 | When the date changed, a new `alerts.json` was created, but it had no read ACL for the Collector, so the Collector could not read it and kept exiting abnormally (10,005 automatic restarts) |
| 3 | Meanwhile, the 18th's file was compressed (`.json.gz`), and the file with the saved inode disappeared |
| 4 | The 19th's file was also compressed, and the 19th's alerts (9,039) remained un-ingested |

# Chapter 1: Confirming the Stop and the First Cause

## 1.1 The Collector's State

**Run on: security-core VM 220 (root)**

```bash
echo "=== COLLECTOR SERVICE ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p ExecMainStatus

echo
echo "=== ALERT FILE ==="
stat -c 'inode=%i size=%s mode=%a owner=%U:%G' \
  /var/ossec/logs/alerts/alerts.json

echo
echo "=== COLLECTOR STATE METADATA ==="
stat -c 'mode=%a owner=%U:%G size=%s' \
  /var/lib/wazuh-collector/state.json

echo
echo "=== COLLECTOR CODE HASH ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== RECENT COLLECTOR STATUS LOGS ==="
journalctl -u wazuh-collector --since "30 minutes ago" --no-pager \
  | grep -Ei 'connection established|inserted|duplicate|error|warning' \
  | sed -E 's/(password|token|secret)=([^ ]+)/\1=[REDACTED]/Ig' \
  | tail -30
```

At build time it showed `NRestarts=10005`, `MainPID=0` and `SubState=auto-restart`, and a `PermissionError` when reading `alerts.json` was being logged repeatedly.

## 1.2 Checking the Permissions

**Run on: security-core VM 220 (root)**

```bash
echo "=== OSSEC DIRECTORY ACL ==="
getfacl -p /var/ossec

echo
echo "=== LOGS DIRECTORY ACL ==="
getfacl -p /var/ossec/logs

echo
echo "=== SYSTEMD SECURITY SETTINGS ==="
systemctl show wazuh-collector \
  -p ProtectSystem -p ProtectHome -p PrivateUsers \
  -p ReadOnlyPaths -p InaccessiblePaths
```

The parent directories had traverse permission, and systemd's restrictions were not the cause. The cause was that the new `alerts.json` (`wazuh:wazuh`, `640`) had no read ACL for the Collector.

## 1.3 Adding a Read ACL to alerts.json

Without changing the owner, group or normal permissions, add only read permission for `wazuh-collector`.

**Run on: security-core VM 220 (root)**

```bash
setfacl -m u:wazuh-collector:r-- \
  /var/ossec/logs/alerts/alerts.json

echo "=== UPDATED FILE ACL ==="
getfacl -p /var/ossec/logs/alerts/alerts.json

echo
echo "=== READ TEST ==="
runuser -u wazuh-collector -- \
  test -r /var/ossec/logs/alerts/alerts.json
echo "read_test_exit_code=$?"
```

If `read_test_exit_code=0`, it can be read. Check whether the automatic restart brings it back.

```bash
echo "=== WAIT FOR AUTO RECOVERY ==="
sleep 15

echo
echo "=== COLLECTOR SERVICE ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p ExecMainStatus

echo
echo "=== RECENT COLLECTOR LOGS ==="
journalctl -u wazuh-collector --since "2 minutes ago" --no-pager \
  | grep -Ei 'started|connection|inserted|duplicate|error|warning' \
  | tail -25
```

In the original build, this alone did not bring it back, because the cause described in the next chapter remained.

# Chapter 2: The Second Cause: The Saved inode Had Disappeared

## 2.1 What the Investigation Found

At startup, if the saved inode is not the current `alerts.json`, the Collector searches the `alerts` directory recursively (Part 6). At build time, the following two problems coincided.

| Problem | Details |
|---|---|
| Search failure | A root-only hidden directory created by an earlier test (`.acl-inheritance-test.bkv8vd`, `root:root`, `0700`) remained in `alerts`, and the search stopped with a permission error |
| inode gone | The file with the saved inode (`5409146`) was nowhere under `/var/ossec/logs` |

The hidden directory was not deleted and was left as is (because later steps return the Collector to a state in which it can start without searching).

## 2.2 Looking for the Saved inode

**Run on: security-core VM 220 (root)**

```bash
echo "=== LOCATE SAVED INODE ==="
find /var/ossec/logs/alerts \
  -xdev -inum 5409146 \
  -printf 'inode=%i size=%s owner=%u:%g mode=%m path=%p\n' \
  2>&1

echo
echo "=== LIST ROTATED ALERT FILES ==="
find /var/ossec/logs/alerts/2026 \
  -type f -name '*.json' \
  -printf 'inode=%i size=%s owner=%u:%g path=%p\n' \
  2>&1 | sort

echo
echo "=== HIDDEN TEST DIRECTORY METADATA ==="
find /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd \
  -maxdepth 3 \
  -printf '%y inode=%i owner=%u:%g mode=%m path=%p\n' \
  2>&1
```

```bash
echo "=== SEARCH OLD INODE UNDER WAZUH LOGS ==="
find /var/ossec/logs -xdev -inum 5409146 \
  -printf 'inode=%i size=%s owner=%u:%g path=%p\n' 2>&1

echo
echo "=== CURRENT ALERT FILE LINK INFORMATION ==="
stat -c 'path=%n inode=%i links=%h size=%s mtime=%y' \
  /var/ossec/logs/alerts/alerts.json \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json

echo
echo "=== STATE FILE TIMESTAMPS ==="
stat -c 'owner=%U:%G mode=%a size=%s mtime=%y ctime=%z' \
  /var/lib/wazuh-collector/state.json

echo
echo "=== COLLECTOR ROTATION HISTORY ==="
journalctl -u wazuh-collector --since "2026-11-19 00:00:00" \
  --no-pager -o cat \
  | grep -Ei 'rotat|inode|resume|offset|initial start|previous alert|cannot be located' \
  | tail -60
```

Replace `5409146` with the inode saved in your environment's state file. At build time it was not found, and the state file's modification time was still 23:53 on November 18.

## 2.3 Listing the Log Files

**Run on: security-core VM 220 (root)**

```bash
echo "=== ALERT LOG FILE INVENTORY ==="
find /var/ossec/logs/alerts -xdev -type f \
  -printf '%TY-%Tm-%Td %TH:%TM:%TS inode=%i size=%s owner=%u:%g mode=%m %p\n' \
  | sort

echo
echo "=== LOG ROTATION CONFIGURATION ==="
grep -RInE 'alerts\.json|ossec-alerts|rotate|compress|daily|weekly' \
  /etc/logrotate.conf /etc/logrotate.d 2>/dev/null

echo
echo "=== CURRENT ALERT FILE TIMESTAMPS ==="
python3 - <<'PY'
import json
from pathlib import Path

p = Path("/var/ossec/logs/alerts/alerts.json")
count = 0
first = None
last = None
invalid = 0

with p.open("r", encoding="utf-8") as f:
    for line in f:
        try:
            obj = json.loads(line)
            ts = obj.get("timestamp")
            if ts is not None:
                first = first or ts
                last = ts
            count += 1
        except Exception:
            invalid += 1

print(f"valid_json_lines={count}")
print(f"invalid_lines={invalid}")
print(f"first_timestamp={first}")
print(f"last_timestamp={last}")
PY
```

The files for the 17th–19th had been compressed into `.json.gz`, and an old file's inode changes when it is compressed.

## 2.4 Matching the Compressed Files Against the Saved Position

Count while decompressing the compressed files, and find out which day's file, and where in it, the saved position (offset) corresponds to.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import gzip
import json
from pathlib import Path

base = Path("/var/ossec/logs/alerts/2026/Nov")
target_offset = 2774739

for day in ("17", "18", "19"):
    path = base / f"ossec-alerts-{day}.json.gz"
    if not path.exists():
        continue

    total = 0
    lines = 0
    first = None
    last = None
    before = None
    after = None
    boundary = None

    with gzip.open(path, "rb") as f:
        while True:
            start = total
            line = f.readline()
            if not line:
                break

            total += len(line)
            lines += 1

            try:
                obj = json.loads(line)
                ts = obj.get("timestamp")
            except Exception:
                ts = None

            if first is None:
                first = ts
            last = ts

            if start <= target_offset < total:
                boundary = (start, total)
                before = ts
            elif total <= target_offset:
                before = ts
            elif after is None and start >= target_offset:
                after = ts

    print(f"FILE={path.name}")
    print(f"  uncompressed_bytes={total}")
    print(f"  lines={lines}")
    print(f"  first_timestamp={first}")
    print(f"  last_timestamp={last}")
    print(f"  saved_offset={target_offset}")
    print(f"  offset_within_file={target_offset <= total}")
    print(f"  boundary_line_byte_range={boundary}")
    print(f"  timestamp_at_or_before_offset={before}")
    print(f"  timestamp_after_offset={after}")
PY
```

Replace `target_offset` with the position saved in your environment's state file.

| Item | Value at build time |
|---|---|
| Saved position | 2,774,739 bytes |
| Decompressed size of `ossec-alerts-18.json.gz` | 2,774,739 bytes (match) |
| Time of the last alert of the 18th | 2026-11-18T23:53:10.688+0000 |
| Modification time of the state file | 2026-11-18 23:53:12 |

This showed that the 18th had been ingested to the end and that what had not been ingested was the 19th (`ossec-alerts-19.json.gz`).

## 2.5 Checking the Boundary Between the 19th and Today

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import gzip
import json
from pathlib import Path

files = [
    (Path("/var/ossec/logs/alerts/2026/Nov/ossec-alerts-19.json.gz"), True),
    (Path("/var/ossec/logs/alerts/alerts.json"), False),
]

for path, compressed in files:
    opener = gzip.open if compressed else open
    count = 0
    invalid = 0
    first = None
    last = None
    missing_id = 0
    missing_ts = 0

    with opener(path, "rb") as stream:
        for line in stream:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                event_id = event.get("id")
                timestamp = event.get("timestamp")

                if not isinstance(event_id, str) or not event_id:
                    missing_id += 1
                if not isinstance(timestamp, str):
                    missing_ts += 1
                    continue

                first = first or timestamp
                last = timestamp
                count += 1
            except Exception:
                invalid += 1

    print(f"FILE={path.name}")
    print(f"  events_with_timestamp={count}")
    print(f"  invalid_json={invalid}")
    print(f"  missing_event_id={missing_id}")
    print(f"  missing_timestamp={missing_ts}")
    print(f"  first_timestamp={first}")
    print(f"  last_timestamp={last}")
PY
```

| File | Count | Time |
|---|---:|---|
| `ossec-alerts-19.json.gz` | 9,039 | Last `00:00:01.339` (on the 20th) |
| `alerts.json` (the 20th) | 2,749 | First `00:00:07.341` |

Neither had any broken lines, lines without an ID, or lines without a time. If the 19th is ingested and then the 20th continues, nothing is missed.

# Chapter 3: Recovery Plan and Preparation

## 3.1 The Plan

Rather than adding support for compressed files to the Collector's source, recover in the following order. The Collector's source, the systemd settings and the Wazuh logs themselves are not changed.

1. Insert the 9,039 alerts of the 19th (`ossec-alerts-19.json.gz`) into the DB using the Collector's existing processing (`process_line()`).
2. Events already inserted are skipped by the existing duplicate handling (unique constraint).
3. Only if all records are processed, advance the state file to the current `alerts.json`'s inode and position `0`.
4. Through its automatic restart, the Collector returns to normal collection from the beginning of the current `alerts.json` (the saved inode is now the current file, so no directory search takes place).

If it fails partway, the state file is not advanced, so it can safely be run again thanks to duplicate handling.

## 3.2 Backing Up the Collector

**Run on: security-core VM 220 (root)**

```bash
install -d -o root -g root -m 700 /root/wazuh-collector-recovery

cp -a /usr/local/lib/wazuh-collector/collector.py \
  /root/wazuh-collector-recovery/collector.py.before-recovery

sha256sum \
  /usr/local/lib/wazuh-collector/collector.py \
  /root/wazuh-collector-recovery/collector.py.before-recovery

stat -c '%n owner=%U:%G mode=%a size=%s' \
  /root/wazuh-collector-recovery/collector.py.before-recovery
```

## 3.3 Checking the DB Connection as the Collector's User

Check only whether it connects, without showing the connection details.

**Run on: security-core VM 220 (root)**

```bash
runuser -u wazuh-collector -- python3 - <<'PY'
import sys
sys.path.insert(0, "/usr/local/lib/wazuh-collector")

import collector

try:
    with collector.psycopg.connect(**collector.DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            print("database_connection=OK")
            print("basic_query=OK")
except Exception as exc:
    print("database_connection=FAILED")
    print("error_type=" + type(exc).__name__)
PY
```

## 3.4 Adding a Read ACL to the 19th's File

**Run on: security-core VM 220 (root)**

```bash
echo "=== ARCHIVE READ ACCESS ==="
if runuser -u wazuh-collector -- test -r \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-19.json.gz; then
  echo "archive_readable=YES"
else
  echo "archive_readable=NO"
fi

echo
echo "=== ARCHIVE METADATA ==="
stat -c 'owner=%U group=%G mode=%a size=%s inode=%i' \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-19.json.gz
```

```bash
getfacl -p \
  /var/ossec/logs/alerts/2026/Nov \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-19.json.gz
```

The `Nov` directory gave the Collector read and traverse permission; only read permission on the one file was missing. Add it to that file only.

```bash
setfacl -m u:wazuh-collector:r-- \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-19.json.gz

echo "=== VERIFY ACL ==="
getfacl -p \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-19.json.gz

echo
echo "=== VERIFY COLLECTOR ACCESS ==="
if runuser -u wazuh-collector -- test -r \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-19.json.gz; then
  echo "archive_readable=YES"
else
  echo "archive_readable=NO"
fi
```

## 3.5 Validating the 19th (No Writes to the DB)

Validate all records with the Collector's `extract_event()`.

**Run on: security-core VM 220 (root)**

```bash
runuser -u wazuh-collector -- python3 - <<'PY'
import gzip
import json
import sys

sys.path.insert(0, "/usr/local/lib/wazuh-collector")
import collector

path = "/var/ossec/logs/alerts/2026/Nov/ossec-alerts-19.json.gz"

total = 0
json_errors = 0
extract_errors = 0
missing_event_id = 0
missing_timestamp = 0
valid_events = 0

with gzip.open(path, "rt", encoding="utf-8") as f:
    for line in f:
        total += 1
        try:
            raw = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            json_errors += 1
            continue

        try:
            event = collector.extract_event(raw)
        except Exception:
            extract_errors += 1
            continue

        if not event:
            extract_errors += 1
            continue

        if not event.get("event_id"):
            missing_event_id += 1
        if not event.get("event_timestamp"):
            missing_timestamp += 1

        if event.get("event_id") and event.get("event_timestamp"):
            valid_events += 1

print(f"total_lines={total}")
print(f"json_errors={json_errors}")
print(f"extract_errors={extract_errors}")
print(f"missing_event_id={missing_event_id}")
print(f"missing_timestamp={missing_timestamp}")
print(f"valid_events={valid_events}")
print("archive_validation=" +
      ("OK" if total == 9039 and json_errors == 0
       and extract_errors == 0 and missing_event_id == 0
       and missing_timestamp == 0 and valid_events == total
       else "FAILED"))
PY
```

Replace `9039` with the count in your environment counted in 2.5. At build time the result was `archive_validation=OK`.

# Chapter 4: Ingesting the 19th and Returning to Normal Collection

## 4.1 Ingestion

**Run on: security-core VM 220 (root)**

```bash
runuser -u wazuh-collector -- python3 - <<'PY'
import gzip
import logging
import os
import sys

sys.path.insert(0, "/usr/local/lib/wazuh-collector")
import collector

archive = "/var/ossec/logs/alerts/2026/Nov/ossec-alerts-19.json.gz"
expected_lines = 9039

# Save the file identity before processing
archive_inode_before = os.stat(archive).st_ino
current_inode_before = os.stat(collector.ALERT_FILE).st_ino

logging.disable(logging.CRITICAL)

processed = 0

try:
    with collector.psycopg.connect(**collector.DB_CONFIG) as conn:
        with gzip.open(archive, "rt", encoding="utf-8") as f:
            for line in f:
                collector.process_line(conn, line)
                processed += 1

    print(f"archive_lines_processed={processed}")

    if processed != expected_lines:
        raise RuntimeError("Unexpected archive line count; state not advanced")

    # Check that the file was not rotated during processing
    archive_inode_after = os.stat(archive).st_ino
    current_inode_after = os.stat(collector.ALERT_FILE).st_ino

    if archive_inode_after != archive_inode_before:
        raise RuntimeError("Archive inode changed; state not advanced")

    if current_inode_after != current_inode_before:
        raise RuntimeError("Current alert inode changed; state not advanced")

    # Only after all records are processed, start normal collection from the head of the current log
    collector.save_state(current_inode_after, 0)

    print("database_replay=COMPLETED")
    print("state_update=COMPLETED")
    print(f"current_alert_inode={current_inode_after}")
    print("recovery_result=SUCCESS")

except Exception as exc:
    print("recovery_result=FAILED")
    print("error_type=" + type(exc).__name__)
    print("state_update=NOT_CONFIRMED")
    raise
PY
```

Replace `expected_lines` with the count in your environment. At build time all 9,039 records were processed, and the state file was advanced to position `0` of the current `alerts.json` (inode `5409383`) (`recovery_result=SUCCESS`).

> Do not run this just before the date changes (just before rotation). If the current `alerts.json` is replaced during processing, it stops without advancing the state file.

## 4.2 Confirming the Return to Normal Collection

Now that the state file points to the current `alerts.json`, the Collector starts on its next automatic restart without searching the directory. At build time, the following log appeared right after ingestion, and the Collector returned to service.

```text
INFO Resuming current alert file
INFO PostgreSQL connection established
```

Check whether the read position has advanced to the end of the current file.

**Run on: security-core VM 220 (root)**

```bash
sleep 15

python3 - <<'PY'
import json
import os

state_path = "/var/lib/wazuh-collector/state.json"
alert_path = "/var/ossec/logs/alerts/alerts.json"

with open(state_path) as f:
    state = json.load(f)

st = os.stat(alert_path)

print(f"state_inode={state['inode']}")
print(f"alert_inode={st.st_ino}")
print(f"state_offset={state['offset']}")
print(f"alert_size={st.st_size}")
print(f"inode_match={state['inode'] == st.st_ino}")
print(f"at_or_near_eof={state['offset'] <= st.st_size}")
print(f"remaining_bytes={max(0, st.st_size - state['offset'])}")
PY

echo
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts
```

| Check | Result at build time |
|---|---|
| State | `active` / `running` (PID `88146`) |
| inode of the state file and `alerts.json` | `5409383` / `5409383` (match) |
| Read position | 5,879,391 bytes (matches the file size) |
| Remaining | `0` bytes |

`NRestarts` includes the automatic restarts while it was stopped, so it stays a large value. There is no problem as long as it stops increasing.

## 4.3 Checking for Errors After the Return

**Run on: security-core VM 220 (root)**

```bash
echo "=== COLLECTOR SERVICE ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p ExecMainStatus

echo
echo "=== COLLECTOR LOGS (LAST 10 MINUTES) ==="
journalctl -u wazuh-collector --since "10 minutes ago" --no-pager \
  | tail -100

echo
echo "=== RECENT ERRORS ==="
journalctl -u wazuh-collector --since "10 minutes ago" --no-pager \
  | grep -iE 'error|exception|traceback|failed|critical|permission denied' \
  | tail -50 || true
```

The log from 10 minutes earlier also includes errors from before the return. Narrow it to the log since the return (04:44:17 UTC at build time).

```bash
echo "=== LOGS AFTER RECOVERY ==="
journalctl -u wazuh-collector \
  --since "2026-11-20 04:44:17" \
  --no-pager

echo
echo "=== ERRORS AFTER RECOVERY ==="
journalctl -u wazuh-collector \
  --since "2026-11-20 04:44:17" \
  --no-pager \
  | grep -iE 'error|exception|traceback|failed|critical|permission denied' \
  || echo "No errors after recovery"

echo
echo "=== CURRENT SERVICE ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts
```

At build time, the log after the return contained only "starting", "resuming from the current file" and "connected to PostgreSQL", with no errors (`No errors after recovery`).

## 4.4 Checking the DB Table

**Run on: LXC 109 postgresql (root)**

```bash
sudo -u postgres psql -X -d security_workbench \
  -c '\dn+' \
  -c '\dt incident.*' \
  -c '\d+ incident.alert_events'
```

Confirm that the table structure (primary key, indexes on time, severity, rule and source IP) has not changed.

# Chapter 5: Checking That the SOC Platform Is Running

After the recovery, we checked, using reads only, that each component used in the next stage (the SOC data integration platform) is working correctly.

## 5.1 VictoriaMetrics and Metrics

**Run on: security-core VM 220 (root)**

```bash
echo "=== VICTORIAMETRICS HEALTH ==="
curl -sS --max-time 5 -w '\nHTTP_STATUS=%{http_code}\n' \
  http://192.168.0.171:8428/health

echo
echo "=== PROMETHEUS METRICS QUERY ==="
curl -sS --max-time 10 -G \
  'http://192.168.0.171:8428/api/v1/query' \
  --data-urlencode 'query=up' \
  -w '\nHTTP_STATUS=%{http_code}\n'
```

Get the load, free memory and free root space of the five machines.

```bash
VM='http://192.168.0.171:8428'

for QUERY in \
  'node_load1{job=~"pve-node|security-core|postgresql-node|prometheus-node|grafana-node"}' \
  'node_memory_MemAvailable_bytes{job=~"pve-node|security-core|postgresql-node|prometheus-node|grafana-node"}' \
  'node_filesystem_avail_bytes{job=~"pve-node|security-core|postgresql-node|prometheus-node|grafana-node",mountpoint="/"}'
do
  echo
  echo "=== $QUERY ==="
  curl -sS --max-time 10 -G "$VM/api/v1/query" \
    --data-urlencode "query=$QUERY"
  echo
done
```

At build time, data for all five machines was obtained.

## 5.2 Wazuh Services

**Run on: security-core VM 220 (root)**

```bash
echo "=== WAZUH SERVICES ==="
systemctl --no-pager --type=service --state=running \
  | grep -i wazuh || true

echo
echo "=== WAZUH RELATED LISTENING PORTS ==="
ss -lntp \
  | grep -E ':(55000|55001|1514|1515|514|9200|9100)\b' \
  || true

echo
echo "=== WAZUH MANAGER STATUS ==="
systemctl show wazuh-manager \
  -p ActiveState -p SubState -p MainPID -p ExecMainStatus

echo
echo "=== COLLECTOR STATUS ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts
```

## 5.3 Wazuh API Response and Certificate

Without using credentials, check only whether the API responds and requires authentication.

**Run on: security-core VM 220 (root)**

```bash
curl -k -sS \
  -o /dev/null \
  -w 'HTTP status: %{http_code}\nTLS verify result: %{ssl_verify_result}\nConnect time: %{time_connect}s\nTotal time: %{time_total}s\n' \
  https://127.0.0.1:55000/
```

If `HTTP status: 401` is returned, the API is running and rejects unauthenticated access. `TLS verify result: 18` means a self-signed certificate (verification is skipped with `-k`).

Check the contents of the certificate (public information, not the private key).

```bash
echo | openssl s_client \
  -connect 127.0.0.1:55000 \
  -servername localhost 2>/dev/null \
  | openssl x509 -noout \
      -subject -issuer -dates -fingerprint -sha256
```

```bash
openssl s_client \
  -connect 127.0.0.1:55000 \
  -servername localhost </dev/null 2>/dev/null \
  | openssl x509 -noout -ext subjectAltName
```

| Item | Result at build time |
|---|---|
| Issuer / subject | `CN=wazuh.com` (self-signed) |
| SAN | Only `DNS:localhost` |

When used as `https://localhost:55000`, the name matches. It does not match with IP addresses (127.0.0.1, 192.168.0.220). We decided to settle the server name and the trusted CA when the API is used from other hosts, and did not regenerate the certificate here.

## 5.4 Wazuh Manager Errors and Warnings

**Run on: security-core VM 220 (root)**

```bash
echo "=== WAZUH MANAGER RECENT ERRORS ==="
journalctl -u wazuh-manager --since "30 minutes ago" \
  --no-pager -p err

echo
echo "=== WAZUH MANAGER RECENT WARNINGS ==="
journalctl -u wazuh-manager --since "30 minutes ago" \
  --no-pager -p warning | tail -30
```

At build time there were no errors or warnings in the last 30 minutes.

# Chapter 6: Checking the Events in the DB

## 6.1 PostgreSQL and Table Privileges

**Run on: LXC 109 postgresql (root)**

```bash
echo "=== POSTGRESQL SERVICE ==="
systemctl show postgresql \
  -p ActiveState -p SubState

echo
echo "=== DATABASE CONNECTION CONFIGURATION (SAFE FIELDS ONLY) ==="
runuser -u postgres -- psql -X -d security_workbench -Atc \
"SELECT current_database(), current_user, version();" \
| cut -c1-180
```

```bash
echo "=== ALERT EVENTS TABLE ==="
runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
"SELECT column_name, data_type, is_nullable
 FROM information_schema.columns
 WHERE table_schema = 'incident'
   AND table_name = 'alert_events'
 ORDER BY ordinal_position;"

echo
echo "=== COLLECTOR TABLE PRIVILEGES ==="
runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
"SELECT grantee, privilege_type
 FROM information_schema.role_table_grants
 WHERE table_schema = 'incident'
   AND table_name = 'alert_events'
   AND grantee = 'wazuh_collector'
 ORDER BY privilege_type;"
```

Confirm that `wazuh_collector` has only `INSERT` (still the least privilege from Part 3).

## 6.2 Counts and Severity

**Run on: LXC 109 postgresql (root)**

```bash
runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
"SELECT
    COUNT(*) AS total_events,
    MIN(event_timestamp) AS oldest_event,
    MAX(event_timestamp) AS newest_event,
    COUNT(*) FILTER (WHERE event_timestamp > now() - interval '1 hour') AS last_1h,
    COUNT(*) FILTER (WHERE event_timestamp > now() - interval '24 hours') AS last_24h
 FROM incident.alert_events;"

echo
echo "=== EVENT COUNTS BY RULE LEVEL ==="
runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
"SELECT rule_level, COUNT(*) AS event_count
 FROM incident.alert_events
 GROUP BY rule_level
 ORDER BY rule_level DESC;"
```

```bash
runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
"SELECT
    date_trunc('minute', event_timestamp) AS minute,
    COUNT(*) AS events,
    COUNT(*) FILTER (WHERE rule_level >= 8) AS high_level_events,
    COUNT(*) FILTER (WHERE rule_level = 7) AS level_7_events,
    COUNT(*) FILTER (WHERE rule_level = 5) AS level_5_events
 FROM incident.alert_events
 WHERE event_timestamp > now() - interval '1 hour'
 GROUP BY 1
 ORDER BY 1 DESC
 LIMIT 15;"
```

```bash
runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
"SELECT
    date_bin(interval '5 minutes', event_timestamp, timestamptz '2000-01-01 00:00:00+00') AS time_bucket,
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE rule_level >= 8) AS level_8_plus,
    COUNT(*) FILTER (WHERE rule_level = 7) AS level_7,
    COUNT(*) FILTER (WHERE rule_level = 5) AS level_5,
    COUNT(*) FILTER (WHERE rule_level <= 4) AS level_4_or_lower
 FROM incident.alert_events
 WHERE event_timestamp > now() - interval '1 hour'
 GROUP BY 1
 ORDER BY 1 DESC;"
```

At build time, 5,345 level-7 events were concentrated in the five minutes 04:40–04:45 UTC.

## 6.3 What the Concentrated Events Were

Distinguish whether they came from an attack or were an effect of the recovery, using the event time and the DB insert time.

**Run on: LXC 109 postgresql (root)**

```bash
runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
"SELECT
    COUNT(*) AS events,
    MIN(event_timestamp) AS first_event_time,
    MAX(event_timestamp) AS last_event_time,
    MIN(ingested_at) AS first_ingested_at,
    MAX(ingested_at) AS last_ingested_at,
    ROUND(AVG(EXTRACT(EPOCH FROM (ingested_at - event_timestamp)))::numeric, 2) AS avg_delay_seconds,
    ROUND(MAX(EXTRACT(EPOCH FROM (ingested_at - event_timestamp)))::numeric, 2) AS max_delay_seconds
 FROM incident.alert_events
 WHERE event_timestamp >= timestamptz '2026-11-20 04:40:00+00'
   AND event_timestamp <  timestamptz '2026-11-20 04:45:00+00'
   AND rule_level = 7;"
```

```bash
runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
"SELECT
    date_trunc('minute', ingested_at) AS ingestion_minute,
    COUNT(*) AS events,
    MIN(ingested_at) AS first_ingested,
    MAX(ingested_at) AS last_ingested
 FROM incident.alert_events
 WHERE event_timestamp >= timestamptz '2026-11-20 04:40:00+00'
   AND event_timestamp <  timestamptz '2026-11-20 04:45:00+00'
   AND rule_level = 7
 GROUP BY 1
 ORDER BY 1;"
```

Replace the time range with the period where the concentration was found in your environment.

| Item | Result at build time |
|---|---|
| Count | 5,345 |
| Event times | 04:43:57–04:44:10 UTC (about 12 seconds) |
| DB inserts | 04:44:48–04:45:27 UTC |

Both the events and the inserts are concentrated around the time the Collector returned (04:44:17). They came from ingesting today's alerts in bulk right after the return, so we decided not to count them as attacks.

## 6.4 Measuring the Ingestion Delay

Excluding the concentrated events, measure the time from an event occurring to its insertion into the DB.

**Run on: LXC 109 postgresql (root)**

```bash
runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
"SELECT
    COUNT(*) AS events,
    ROUND(AVG(EXTRACT(EPOCH FROM (ingested_at - event_timestamp)))::numeric, 2) AS avg_delay_seconds,
    ROUND(
        percentile_cont(0.50) WITHIN GROUP (
            ORDER BY EXTRACT(EPOCH FROM (ingested_at - event_timestamp))
        )::numeric, 2
    ) AS p50_delay_seconds,
    ROUND(
        percentile_cont(0.95) WITHIN GROUP (
            ORDER BY EXTRACT(EPOCH FROM (ingested_at - event_timestamp))
        )::numeric, 2
    ) AS p95_delay_seconds,
    ROUND(MAX(EXTRACT(EPOCH FROM (ingested_at - event_timestamp)))::numeric, 2) AS max_delay_seconds
 FROM incident.alert_events
 WHERE ingested_at > now() - interval '1 hour'
   AND ingested_at - event_timestamp BETWEEN interval '0 seconds' AND interval '10 minutes'
   AND NOT (
       event_timestamp >= timestamptz '2026-11-20 04:40:00+00'
       AND event_timestamp < timestamptz '2026-11-20 04:45:00+00'
       AND rule_level = 7
   );"
```

At build time, the 255 events measured showed large delays: an average of 170 seconds, a median of 79 seconds and a P95 of 541 seconds. Check whether the Collector is leaving data unread.

**Run on: security-core VM 220 (root)**

```bash
echo "=== COLLECTOR STATE ==="
python3 - <<'PY'
import json
from pathlib import Path

p = Path("/var/lib/wazuh-collector/state.json")
state = json.loads(p.read_text())
print("state_inode:", state.get("inode"))
print("state_offset:", state.get("offset"))
PY

echo
echo "=== ACTIVE ALERT FILE ==="
stat -c 'inode=%i size=%s mtime=%y' \
  /var/ossec/logs/alerts/alerts.json

echo
echo "=== COLLECTOR STATUS ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts
```

At build time the read position and the file size matched (5,958,275 bytes), so nothing was left unread. The cause of the delay therefore lies elsewhere.

# Chapter 7: Checking Time Synchronization

The event time (security-core) and the DB insert time (PostgreSQL) are recorded by the clocks of different servers. If the clocks drift, the delay looks large.

## 7.1 security-core

**Run on: security-core VM 220 (root)**

```bash
timedatectl status
```

At build time it showed `System clock synchronized: yes` and `NTP service: active` (time zone UTC).

## 7.2 PostgreSQL (LXC 109)

**Run on: LXC 109 postgresql (root)**

```bash
timedatectl status
```

```bash
echo "=== TIME SYNC SERVICES ==="
systemctl is-active chrony.service systemd-timesyncd.service ntp.service 2>/dev/null

echo
echo "=== TIME SYNC STATUS ==="
systemctl list-units --type=service --all --no-legend \
  | grep -Ei 'chrony|timesyncd|ntp' \
  | sed -E 's/[[:space:]]+/ /g'
```

At build time it showed `System clock synchronized: yes` but `NTP service: inactive`, and there was no time synchronization service inside the LXC. An LXC uses the Proxmox host kernel's clock as is, so check the host side. (The time zone was Asia/Tokyo, but this is not a problem because the DB compares `timestamptz` in UTC.)

## 7.3 The Proxmox Host

**Run on: Proxmox host pve (root)**

```bash
echo "=== PVE TIME ==="
timedatectl status

echo
echo "=== TIME SYNC SERVICES ==="
systemctl is-active chrony.service systemd-timesyncd.service ntp.service 2>/dev/null

echo
echo "=== TIME SYNC PROCESSES ==="
ps -eo pid,comm,args \
  | grep -Ei '[c]hronyd|[n]tpd|[s]ystemd-timesyncd'
```

```bash
echo "=== CHRONY TRACKING ==="
chronyc tracking

echo
echo "=== CHRONY SOURCES ==="
chronyc sources -v
```

At build time it was synchronized by chrony, with a clock offset of less than 1 millisecond. Delays of several minutes cannot be explained by clock drift.

# Chapter 8: Measuring the Ingestion Delay Again

## 8.1 Preparing a Role for Aggregation

We decided to use the administrative role `dbadmin` for aggregating in the DB. Give it minimal, read-only privileges.

**Run on: LXC 109 postgresql (root)**

```bash
echo "=== DBADMIN ROLE STATUS ==="
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    rolname,
    rolsuper,
    rolcreatedb,
    rolcreaterole,
    rolcanlogin
FROM pg_roles
WHERE rolname = 'dbadmin';
"
```

```bash
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    has_schema_privilege('dbadmin', 'incident', 'USAGE')
        AS schema_usage,
    has_table_privilege(
        'dbadmin',
        'incident.alert_events',
        'SELECT'
    ) AS alert_events_select;
"
```

At build time, `dbadmin` was an ordinary role that could log in (no superuser or create-DB privileges) and had no privileges on the `incident` schema or table. Give it read access only.

```bash
sudo -u postgres psql -X -d security_workbench -v ON_ERROR_STOP=1 -c "
GRANT USAGE ON SCHEMA incident TO dbadmin;
GRANT SELECT ON TABLE incident.alert_events TO dbadmin;
"
```

```bash
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    has_schema_privilege('dbadmin', 'incident', 'USAGE')
        AS schema_usage,
    has_table_privilege(
        'dbadmin', 'incident.alert_events', 'SELECT'
    ) AS can_select,
    has_table_privilege(
        'dbadmin', 'incident.alert_events', 'INSERT'
    ) AS can_insert,
    has_table_privilege(
        'dbadmin', 'incident.alert_events', 'UPDATE'
    ) AS can_update,
    has_table_privilege(
        'dbadmin', 'incident.alert_events', 'DELETE'
    ) AS can_delete;
"
```

Confirm that only `can_select` is `t` and the rest are `f`.

## 8.2 Connecting as dbadmin

`dbadmin` is not an OS user, so you cannot connect with `sudo -u dbadmin`. Connect over TCP to localhost (`scram-sha-256` authentication) and enter the password (it is not shown on screen, and it is not written in this manual).

**Run on: LXC 109 postgresql (root)**

```bash
psql -X -h 127.0.0.1 -U dbadmin -d security_workbench -W -c "
SELECT
    current_user,
    current_database(),
    current_timestamp;
"
```

## 8.3 The Delay over the Last 15 Minutes

**Run on: LXC 109 postgresql (root)**

```bash
psql -X -h 127.0.0.1 -U dbadmin \
  -d security_workbench -W -c "
WITH recent AS (
    SELECT
        EXTRACT(EPOCH FROM (ingested_at - event_timestamp))
            AS delay_seconds
    FROM incident.alert_events
    WHERE ingested_at >= NOW() - INTERVAL '15 minutes'
)
SELECT
    COUNT(*) AS total_events,
    COUNT(*) FILTER (
        WHERE delay_seconds < 0
    ) AS negative_delay_events,
    ROUND(AVG(delay_seconds)::numeric, 2) AS avg_delay_seconds,
    ROUND(
        percentile_cont(0.50)
        WITHIN GROUP (ORDER BY delay_seconds)::numeric, 2
    ) AS p50_delay_seconds,
    ROUND(
        percentile_cont(0.95)
        WITHIN GROUP (ORDER BY delay_seconds)::numeric, 2
    ) AS p95_delay_seconds,
    ROUND(MAX(delay_seconds)::numeric, 2) AS max_delay_seconds
FROM recent;
"
```

At build time, the 69 events had an average of 1.28 seconds, a median of 1.27 seconds, a P95 of 1.79 seconds and a maximum of 1.84 seconds, with zero negative delays (time reversals).

Also check minute by minute.

```bash
psql -X -h 127.0.0.1 -U dbadmin \
  -d security_workbench -W -c "
SELECT
    date_trunc('minute', ingested_at) AS ingest_minute,
    COUNT(*) AS events,
    COUNT(*) FILTER (WHERE rule_level >= 8) AS high_level,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (ingested_at - event_timestamp)))::numeric,
        2
    ) AS avg_delay_seconds,
    ROUND(
        MAX(EXTRACT(EPOCH FROM (ingested_at - event_timestamp)))::numeric,
        2
    ) AS max_delay_seconds
FROM incident.alert_events
WHERE ingested_at >= NOW() - INTERVAL '15 minutes'
GROUP BY 1
ORDER BY 1 DESC;
"
```

The large delays seen in 6.4 were temporary, caused by the concentrated ingestion right after the recovery; in normal operation, events are inserted within 1–2 seconds.

# Chapter 9: The Cause of a Flood of Events and the Fix

## 9.1 Counts per Rule

**Run on: LXC 109 postgresql (root)**

```bash
psql -X -P pager=off -h 127.0.0.1 -U dbadmin \
  -d security_workbench -W -c "
SELECT
    rule_id,
    rule_level,
    COUNT(*) AS event_count,
    MIN(event_timestamp) AS first_event,
    MAX(event_timestamp) AS last_event
FROM incident.alert_events
WHERE event_timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY rule_id, rule_level
ORDER BY event_count DESC
LIMIT 20;
"
```

At build time, rule 40704 (level 5, `Systemd: Service exited due to a failure.`) had 11,905 events, far more than any other.

```bash
psql -X -P pager=off -h 127.0.0.1 -U dbadmin \
  -d security_workbench -W -c "
SELECT
    rule_id,
    rule_level,
    rule_description,
    rule_groups,
    agent_name,
    COUNT(*) AS event_count,
    MIN(event_timestamp) AS first_event,
    MAX(event_timestamp) AS last_event
FROM incident.alert_events
WHERE event_timestamp >= NOW() - INTERVAL '24 hours'
  AND rule_id IN (
      40704, 100103, 510, 2904, 23502,
      2902, 87203, 2901, 5501, 5502,
      5138, 550, 5407, 19011, 5901,
      5902, 100102
  )
GROUP BY
    rule_id,
    rule_level,
    rule_description,
    rule_groups,
    agent_name
ORDER BY event_count DESC
LIMIT 30;
"
```

Replace the list of `rule_id` values with the rules at the top in 9.1 in your environment.

## 9.2 Breakdown of 40704

**Run on: LXC 109 postgresql (root)**

```bash
psql -X -P pager=off -h 127.0.0.1 -U dbadmin \
  -d security_workbench -W -c "
SELECT
    agent_name,
    COUNT(*) AS total_events,
    MIN(event_timestamp) AS first_event,
    MAX(event_timestamp) AS last_event,
    MIN(ingested_at) AS first_ingested,
    MAX(ingested_at) AS last_ingested,
    COUNT(*) FILTER (
        WHERE ingested_at - event_timestamp > INTERVAL '5 minutes'
    ) AS delayed_over_5m,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (ingested_at - event_timestamp)))::numeric,
        2
    ) AS avg_delay_seconds
FROM incident.alert_events
WHERE rule_id = 40704
  AND ingested_at >= NOW() - INTERVAL '24 hours'
GROUP BY agent_name
ORDER BY total_events DESC;
"
```

| Host | Count (at build time) | Details |
|---|---:|---|
| security-core | 11,268 | About 16 hours' worth inserted in bulk by the ingestion in Chapter 4 |
| postgresql | 225 | Still occurring about once a minute |
| lxc-prometheus | 210 | Still occurring about once a minute |
| lxc-grafana | 206 | Still occurring about once a minute |

```bash
psql -X -P pager=off -h 127.0.0.1 -U dbadmin \
  -d security_workbench -W -c "
SELECT
    agent_name,
    COUNT(*) AS events,
    ROUND(
        percentile_cont(0.50)
        WITHIN GROUP (
            ORDER BY EXTRACT(EPOCH FROM (ingested_at - event_timestamp))
        )::numeric, 2
    ) AS p50_delay_seconds,
    ROUND(
        percentile_cont(0.95)
        WITHIN GROUP (
            ORDER BY EXTRACT(EPOCH FROM (ingested_at - event_timestamp))
        )::numeric, 2
    ) AS p95_delay_seconds,
    ROUND(
        MAX(EXTRACT(EPOCH FROM (ingested_at - event_timestamp)))::numeric,
        2
    ) AS max_delay_seconds,
    MAX(event_timestamp) AS last_event
FROM incident.alert_events
WHERE rule_id = 40704
  AND ingested_at >= NOW() - INTERVAL '15 minutes'
GROUP BY agent_name
ORDER BY events DESC;
"
```

Over the last 15 minutes, the delay was within 2 seconds on all three machines. So ingestion is normal, and services really are exiting abnormally over and over on the three machines.

## 9.3 Identifying the Failing Service

The DB does not store the full log (`full_log`), so extract only the names of the failed services from the Wazuh alert file.

**Run on: security-core VM 220 (root)**

```bash
grep -h '"rule":{"level":5,"description":"Systemd: Service exited due to a failure."' \
  /var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json \
  | tail -n 20 \
  | python3 -c '
import sys,json,re
pattern = re.compile(r"[A-Za-z0-9_.@:-]+\.service")
for line in sys.stdin:
    try:
        x=json.loads(line)
        raw=x.get("full_log") or ""
        units=sorted(set(pattern.findall(raw)))
        print(json.dumps({
            "timestamp": x.get("timestamp"),
            "agent": x.get("agent",{}).get("name"),
            "service_units": units,
            "full_log_present": bool(raw)
        }, ensure_ascii=False))
    except Exception:
        print("JSON_PARSE_ERROR")
'
```

Adjust the date in the file name (`ossec-alerts-20.json`) to the day you are investigating. At build time, all of them were `prometheus-node-exporter-ipmitool-sensor.service`. This is an auxiliary service that collects IPMI sensor values, installed together with the Node Exporter package in Part 8.

## 9.4 Confirming the Cause

**Run on: LXC 105 lxc-grafana (root)**

```bash
echo "=== SERVICE STATE ==="
systemctl show prometheus-node-exporter-ipmitool-sensor.service \
  -p LoadState \
  -p ActiveState \
  -p SubState \
  -p Result \
  -p ExecMainCode \
  -p ExecMainStatus \
  -p NRestarts

echo
echo "=== RECENT SERVICE LOGS ==="
journalctl -u prometheus-node-exporter-ipmitool-sensor.service \
  --since "30 minutes ago" \
  --no-pager -n 30 -o short-iso
```

The log repeatedly showed the following error (postgresql and lxc-prometheus were the same).

```text
Could not open device at /dev/ipmi0 or /dev/ipmi/0 or /dev/ipmidev/0:
No such file or directory
```

```bash
echo "=== UNIT DEFINITION ==="
systemctl cat prometheus-node-exporter-ipmitool-sensor.service

echo
echo "=== DEPENDENCY RELATIONSHIPS ==="
systemctl show prometheus-node-exporter-ipmitool-sensor.service \
  -p Requires -p Wants -p Requisite \
  -p Before -p After -p PartOf -p WantedBy \
  -p RequiredBy -p ConsistsOf
```

```bash
echo "=== TIMER DEFINITION ==="
systemctl cat prometheus-node-exporter-ipmitool-sensor.timer

echo
echo "=== TIMER STATE ==="
systemctl show prometheus-node-exporter-ipmitool-sensor.timer \
  -p LoadState -p ActiveState -p SubState \
  -p Triggers -p TriggeredBy -p OnCalendar -p OnUnitActiveSec

echo
echo "=== NODE EXPORTER STATE ==="
systemctl show prometheus-node-exporter.service \
  -p LoadState -p ActiveState -p SubState -p MainPID
```

```bash
echo "=== IPMI SYSFS ==="
ls -la /sys/class/ipmi/

echo
echo "=== IPMI DEVICE NODES ==="
for p in /dev/ipmi0 /dev/ipmi/0 /dev/ipmidev/0; do
  if [ -e "$p" ]; then
    ls -l "$p"
  else
    echo "$p : absent"
  fi
done

echo
echo "=== IPMI DEVICE REFERENCES ==="
find /sys/class/ipmi -maxdepth 2 -type l -printf '%p -> %l\n' 2>/dev/null
```

| Item | State at build time |
|---|---|
| `/sys/class/ipmi/ipmi0` | Present (the host's information is visible from the LXC) |
| `/dev/ipmi0` and similar | Absent (no device is passed to the LXC) |
| IPMI collection timer | Runs every minute |
| Node Exporter itself | Normal |

The timer's start condition (`ConditionDirectoryNotEmpty=/sys/class/ipmi`) is met, so collection ran every minute and failed because it could not open the device. Wazuh detected those failures as 40704.

## 9.5 Stopping the IPMI Collection Timer

Without changing Node Exporter itself, the Prometheus settings or forwarding, stop only the IPMI collection timer and disable its automatic start on the three LXCs (lxc-grafana, postgresql, lxc-prometheus). Run it on one machine at a time and check.

**Run on: LXC 105 lxc-grafana, LXC 109 postgresql, LXC 103 lxc-prometheus (root on each)**

```bash
systemctl disable --now prometheus-node-exporter-ipmitool-sensor.timer
```

```bash
echo "=== IPMI TIMER ==="
systemctl show prometheus-node-exporter-ipmitool-sensor.timer \
  -p LoadState -p ActiveState -p UnitFileState

echo
echo "=== NODE EXPORTER ==="
systemctl show prometheus-node-exporter.service \
  -p LoadState -p ActiveState -p SubState -p MainPID
```

At build time, on all three machines the timer was `inactive` and `disabled`, and Node Exporter was `active` / `running`.

> In the original build, only the three LXCs on which 40704 continued were dealt with. The Proxmox host (`pve`, 1 event at build time) and security-core (11,268 events were past alerts ingested in bulk) were not.

# Summary of Part 9

## Causes and Fixes

| Cause | Fix |
|---|---|
| The new `alerts.json` had no read ACL for the Collector | Added with `setfacl -m u:wazuh-collector:r--` (1.3) |
| The file with the saved inode disappeared through compression, and the search also stopped at a root-only hidden directory | Ingested the 19th with the existing processing and advanced the state file to the current `alerts.json` (Chapter 4) |

## What Was Changed

| Target | Change |
|---|---|
| `/var/ossec/logs/alerts/alerts.json` (the 20th) | Read ACL for the Collector |
| `/var/ossec/logs/alerts/2026/Nov/ossec-alerts-19.json.gz` | Read ACL for the Collector |
| `/var/lib/wazuh-collector/state.json` | inode of the current `alerts.json`, position `0` |
| DB `incident.alert_events` | Alerts of the 19th (duplicates skipped) |

The Collector's source, the systemd settings and the Wazuh logs themselves were not changed. The backup is at `/root/wazuh-collector-recovery/collector.py.before-recovery`.

## What the Checks Found (Chapters 5–9)

| Item | Result |
|---|---|
| VictoriaMetrics and the metrics of the five machines | Normal |
| Wazuh Manager and API | Normal (the API requires authentication; the certificate is self-signed with only `localhost` as SAN) |
| Large number of events right after the recovery | Caused by ingesting past alerts (not an attack) |
| Time synchronization | Normal (offset under 1 millisecond) |
| Normal ingestion delay | 1–2 seconds |
| Flood of rule 40704 | Failures of the IPMI collection timer on the LXCs; the timer was stopped on three machines |

For aggregation in the DB, `dbadmin` was given privileges to use the `incident` schema and read `incident.alert_events`.

## Remaining Issues

- **[Risk, open]** When the date changes, Wazuh creates a new `alerts.json`. If the new file does not get a read ACL for the Collector, the same stop will happen again. No permanent measure (such as a default ACL) for the daily rotation has been taken. If it stops, recover with Chapter 1 (adding the ACL) and, if needed, Chapters 2–4 (ingesting what was missed). Check the Collector's state (an increasing `NRestarts` or `PermissionError`) every day.
- **[Risk, open]** The root-only hidden directory in the `alerts` directory (`.acl-inheritance-test.bkv8vd`) has not been deleted and remains. If the Collector searches the directory again (when the saved inode is not the current `alerts.json`), it stops with the same permission error.
- The Collector still does not search compressed files (`.json.gz`). If an old file is compressed while it is stopped, recover with the same steps as Chapters 2–4.

---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 2"
subtitle: "Part 29: Restarting the Collector Without Missing Any Events"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 29 of Volume 2 of the "AI Autonomous Cyber Defense System Build Manual". In Part 28 we found that the Collector had stopped starting, for safety, because "the file it had been reading (inode 5409383) cannot be found". Here we do the following.

1. Find out what happened to the previous file, using the log files, compressed files and checksums
2. Confirm that the saved read position was **the end** of the previous file
3. After confirming PostgreSQL's mechanism for preventing duplicates, rewrite the read position to "the beginning of the current `alerts.json`"
4. Start the Collector and confirm that the events were ingested into PostgreSQL

Arbitrarily advancing the read position to the end of the current file would leave events unread. We proceed only after confirming each piece of evidence.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **postgresql**: LXC 109 (192.168.0.151), OS user `postgres`
- Alert text is not shown. The PostgreSQL password is read from `.pgpass` and not shown.
- inodes, sizes, times and counts are those at build time. Replace them with the values in your environment.

# Chapter 1: Looking for the Previous File

> **Run on: VM 220**

## 1.1 The Log Files

```bash
find /var/ossec/logs/alerts -maxdepth 3 -type f -printf '%i %s %M %u:%g %p\n' | sort -k6
```

Compressed JSON logs for November 17–20 (`2026/Nov/ossec-alerts-*.json.gz`) and the current log for the 21st remained. inode 5409383 did not exist. The Collector's search covers only files ending in `.json`, not `.json.gz`.

```bash
if command -v lsof >/dev/null 2>&1; then lsof -nP +L1 2>/dev/null | grep -E '5409383|alerts' || true; else echo "lsof_NOT_INSTALLED"; fi
```

There were also no files still held open after being deleted.

```bash
stat -c 'INODE=%i SIZE=%s MTIME=%y PATH=%n' /var/ossec/logs/alerts/2026/Nov/ossec-alerts-*.json*
```

The JSON logs switch daily: the files for the 17th–20th have been compressed, and the 21st is the current `alerts.json`.

## 1.2 The Size of the 20th's File

```bash
gzip -l /var/ossec/logs/alerts/2026/Nov/ossec-alerts-*.json.gz
```

The decompressed size of the 20th's file was **6,433,808 bytes**, the same as the saved read position.

```bash
gzip -t /var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json.gz
echo "GZIP_TEST_EXIT_CODE=$?"
```

The compressed file is not corrupted (`GZIP_TEST_EXIT_CODE=0`). While decompressing (without writing to disk), examine the number of lines and their form.

```bash
python3 - <<'PY'
import gzip, json

path = "/var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json.gz"
total = 0
lines = 0
invalid = 0
last_byte = None

with gzip.open(path, "rb") as f:
    while True:
        chunk = f.readline()
        if not chunk:
            break
        total += len(chunk)
        lines += 1
        last_byte = chunk[-1:]
        try:
            json.loads(chunk)
        except Exception:
            invalid += 1

print("UNCOMPRESSED_BYTES:", total)
print("LINE_COUNT:", lines)
print("INVALID_JSON_LINES:", invalid)
print("ENDS_WITH_NEWLINE:", last_byte == b"\n")
print("SAVED_OFFSET_MATCH:", total == 6433808)
PY
```

| Item | Result |
|---|---|
| Decompressed size | 6,433,808 bytes (matches the saved position) |
| Lines | 10,293 |
| Lines not readable as JSON | 0 |
| Final newline | Present |

## 1.3 Times and Checksum

```bash
stat -c 'MTIME=%y CTIME=%z SIZE=%s PATH=%n' /var/lib/wazuh-collector/state.json /var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json.gz /var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json.sum
file /var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json.sum
```

The state file was saved at 23:54:26 on November 20 (UTC), and the 20th's file was compressed at 00:00:10 on November 21 (UTC). When the state was saved, the 20th's file was the current file.

Look at the checksum file created by Wazuh (37 bytes).

```bash
cat /var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json.sum
```

It recorded the SHA-256 of the 20th's file before compression.

```text
7b07b435669a8c98892f4919295644c21bfdb35522f3747e21366f6ba0aafe79
```

Compute the SHA-256 while decompressing and compare it with the record. Replace the value with the value in your environment's `.sum`.

```bash
python3 - <<'PY'
import gzip, hashlib

path = "/var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json.gz"
expected = "7b07b435669a8c98892f4919295644c21bfdb35522f3747e21366f6ba0aafe79"

h = hashlib.sha256()
size = 0

with gzip.open(path, "rb") as f:
    while True:
        chunk = f.read(1024 * 1024)
        if not chunk:
            break
        h.update(chunk)
        size += len(chunk)

actual = h.hexdigest()
print("UNCOMPRESSED_BYTES:", size)
print("ACTUAL_SHA256:", actual)
print("EXPECTED_SHA256:", expected)
print("CHECKSUM_MATCH:", actual == expected)
PY
```

The result was `CHECKSUM_MATCH: True`.

## 1.4 The Current File

```bash
python3 - <<'PY'
import json
from pathlib import Path

p = Path("/var/ossec/logs/alerts/alerts.json")
size = 0
lines = 0
invalid = 0
last_byte = None

with p.open("rb") as f:
    while True:
        line = f.readline()
        if not line:
            break
        size += len(line)
        lines += 1
        last_byte = line[-1:]
        try:
            json.loads(line)
        except Exception:
            invalid += 1

print("CURRENT_INODE:", p.stat().st_ino)
print("CURRENT_BYTES:", size)
print("LINE_COUNT:", lines)
print("INVALID_JSON_LINES:", invalid)
print("ENDS_WITH_NEWLINE:", last_byte == b"\n")
PY
```

The 21st's file also had no unreadable lines. Compare the times at the boundary.

```bash
python3 - <<'PY'
import gzip, json

archive = "/var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json.gz"
current = "/var/ossec/logs/alerts/alerts.json"

last = None
with gzip.open(archive, "rb") as f:
    for line in f:
        if line.strip():
            last = json.loads(line)

with open(current, "rb") as f:
    first = json.loads(f.readline())

print("ARCHIVE_LAST_TIMESTAMP:", last.get("timestamp"))
print("CURRENT_FIRST_TIMESTAMP:", first.get("timestamp"))
PY
```

| Item | Time (UTC) |
|---|---|
| Last event in the 20th's file | 11/20 23:54:26.205 |
| State file saved | 11/20 23:54:26.714 |
| First event in the 21st's file | 11/21 00:09:26.253 |

The saved read position corresponds to the end of the 20th's file. Therefore **reading the current `alerts.json` (inode 5409517) from the beginning (offset 0) is sufficient**. However, it cannot be proved that there were no alerts during these 15 minutes.

## 1.5 The Mechanism That Prevents Duplicates

Part of the 21st's file may have been ingested while the Collector was still running. Confirm that re-reading from the beginning will not insert anything twice.

```bash
PGPASSFILE=/etc/wazuh-collector/.pgpass psql "host=postgresql.neomedia.mydns.jp hostaddr=192.168.0.151 port=5432 dbname=security_workbench user=wazuh_collector sslmode=verify-full sslrootcert=/etc/ssl/certs/postgresql-server-ca.pem" -X -A -F '|' -c "SELECT i.relname AS index_name, ix.indisunique AS is_unique, pg_get_indexdef(i.oid) AS index_definition FROM pg_class t JOIN pg_namespace n ON n.oid=t.relnamespace JOIN pg_index ix ON ix.indrelid=t.oid JOIN pg_class i ON i.oid=ix.indexrelid WHERE n.nspname='incident' AND t.relname='alert_events' ORDER BY i.relname;"
```

The result at build time (key points) was as follows: `event_id` was the primary key (unique).

```text
alert_events_pkey
UNIQUE (event_id)
```

Also check the processing on the Collector side.

```bash
grep -n -A45 -B15 'UniqueViolation\|def process_line' /usr/local/lib/wazuh-collector/collector.py
```

```bash
sed -n '555,610p' /usr/local/lib/wazuh-collector/collector.py
```

```bash
sed -n '600,665p' /usr/local/lib/wazuh-collector/collector.py
```

1. Each event is INSERTed in its own transaction
2. If `event_id` is a duplicate (SQLSTATE `23505`), the insert is rolled back and it moves on to the next
3. After either a successful INSERT or a duplicate, the read position is saved
4. If the DB or saving fails, it goes back to the start of the line and retries
5. When the file switches, it saves the new inode and offset 0 first, then switches

# Chapter 2: Rewriting the Read Position

> **Run on: VM 220**

## 2.1 Stopping It

```bash
systemctl stop wazuh-collector.service
```

```bash
systemctl is-active wazuh-collector.service
systemctl show wazuh-collector.service -p MainPID -p NRestarts -p ActiveState -p SubState
```

Confirm `inactive` and `MainPID=0`, so that no process will rewrite the state file.

## 2.2 Backup

```bash
backup="/var/lib/wazuh-collector/state.json.pre-recovery-20261121"; test ! -e "$backup" && cp -a /var/lib/wazuh-collector/state.json "$backup" && sha256sum /var/lib/wazuh-collector/state.json "$backup" && cmp -s /var/lib/wazuh-collector/state.json "$backup" && echo "BACKUP_VERIFY=OK"
```

Confirm `BACKUP_VERIFY=OK`.

## 2.3 Rewriting

The new read position is as follows.

```text
{"inode": 5409517, "offset": 0}
```

Rewrite it only if the current state file is as expected (inode 5409383, offset 6433808) and the inode of `alerts.json` is 5409517. Otherwise it stops without doing anything. The rewrite writes a temporary file and then swaps it in, keeping the original permissions and owner.

```bash
python3 - <<'PY'
import json, os, stat, tempfile

state_path = "/var/lib/wazuh-collector/state.json"
backup_path = "/var/lib/wazuh-collector/state.json.pre-recovery-20261121"
alert_path = "/var/ossec/logs/alerts/alerts.json"

with open(state_path, encoding="utf-8") as f:
    old_state = json.load(f)
with open(backup_path, "rb") as f:
    backup_bytes = f.read()

if old_state != {"inode": 5409383, "offset": 6433808}:
    raise SystemExit("ABORT: state.json differs from expected old state")
if os.stat(alert_path).st_ino != 5409517:
    raise SystemExit("ABORT: alerts.json inode changed")
if not backup_bytes:
    raise SystemExit("ABORT: backup is empty")

st = os.stat(state_path)
directory = os.path.dirname(state_path)
fd, temp_path = tempfile.mkstemp(prefix=".state.json.recovery.", dir=directory)

try:
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"inode": 5409517, "offset": 0}, f)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())

    os.chmod(temp_path, stat.S_IMODE(st.st_mode))
    os.chown(temp_path, st.st_uid, st.st_gid)
    os.replace(temp_path, state_path)

    dir_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
except Exception:
    if os.path.exists(temp_path):
        os.unlink(temp_path)
    raise

with open(state_path, encoding="utf-8") as f:
    result = json.load(f)

print("NEW_STATE:", json.dumps(result, sort_keys=True))
print("STATE_UPDATE:", "OK" if result == {"inode": 5409517, "offset": 0} else "FAILED")
print("BACKUP_PRESERVED:", os.path.exists(backup_path))
PY
```

## 2.4 Starting It

```bash
systemctl start wazuh-collector.service
```

```bash
systemctl is-active wazuh-collector.service
systemctl show wazuh-collector.service -p MainPID -p NRestarts -p ActiveState -p SubState
```

At build time it was `active` and `running` (PID 13542). `NRestarts=874` is the total count up to when it was stopped.

```bash
journalctl -u wazuh-collector.service -n 60 --no-pager -o short-iso
```

```bash
journalctl -u wazuh-collector.service --since "2026-11-21 10:45:00" --no-pager -o short-iso | tail -n 40
```

The log after starting contained the following two lines.

```text
INFO Resuming current alert file
INFO PostgreSQL connection established
```

## 2.5 Is It Reading Forward?

```bash
python3 - <<'PY'
import json, os

state_path = "/var/lib/wazuh-collector/state.json"
alert_path = "/var/ossec/logs/alerts/alerts.json"

with open(state_path, encoding="utf-8") as f:
    state = json.load(f)

st = os.stat(alert_path)
print("STATE_INODE:", state["inode"])
print("STATE_OFFSET:", state["offset"])
print("CURRENT_INODE:", st.st_ino)
print("CURRENT_SIZE:", st.st_size)
print("INODE_MATCH:", state["inode"] == st.st_ino)
print("OFFSET_WITHIN_FILE:", 0 <= state["offset"] <= st.st_size)
PY
```

The read position (858,191) became equal to the file size, showing that it had read to the end.

```bash
systemctl is-active wazuh-collector.service
journalctl -u wazuh-collector.service --since "2026-11-21 10:45:00" --no-pager -o cat | grep -E 'ERROR|WARNING|Duplicate alert skipped|PostgreSQL connection|Resuming current alert'
```

There were no errors or warnings after starting.

# Chapter 3: Confirming in PostgreSQL

> **Run on: postgresql** (OS user `postgres`)

`wazuh_collector` has only the INSERT privilege, so rather than adding privileges, run read-only SQL as the PostgreSQL administrator.

```bash
psql -d security_workbench -X -P pager=off -c "
SELECT
    COUNT(*) AS events_last_30m,
    MIN(event_timestamp) AS first_event,
    MAX(event_timestamp) AS latest_event
FROM incident.alert_events
WHERE event_timestamp >= NOW() - INTERVAL '30 minutes';
"
```

There were 143 events in the last 30 minutes. Check whether there is a column for the ingestion time.

```bash
psql -d security_workbench -X -P pager=off -c "
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'incident'
  AND table_name = 'alert_events'
ORDER BY ordinal_position;
"
```

`ingested_at` existed. Count the events ingested after the time the Collector was started (10:45:16 UTC). Replace the time with the one in your environment.

```bash
psql -d security_workbench -X -P pager=off -c "
SELECT
    COUNT(*) AS ingested_after_restart,
    COUNT(DISTINCT event_id) AS unique_event_ids,
    MIN(ingested_at) AS first_ingested_at,
    MAX(ingested_at) AS latest_ingested_at
FROM incident.alert_events
WHERE ingested_at >= TIMESTAMPTZ '2026-11-21 10:45:16+00';
"
```

| Item | Result |
|---|---|
| Inserted after starting | 1,318 |
| Distinct `event_id` | 1,318 (no duplicates) |
| First insert | 10:45:16.110 UTC |
| Last insert | 10:58:41.944 UTC |

```bash
psql -d security_workbench -X -P pager=off -c "
SELECT
    COUNT(*) AS ingested_last_5m,
    MAX(ingested_at) AS latest_ingested_at
FROM incident.alert_events
WHERE ingested_at >= NOW() - INTERVAL '5 minutes';
"
```

There was one event in the last five minutes. That may simply be because there were few new alerts, so check on VM 220 whether anything is left unread.

> **Run on: VM 220**

```bash
python3 - <<'PY'
import json, os

with open("/var/lib/wazuh-collector/state.json", encoding="utf-8") as f:
    state = json.load(f)

st = os.stat("/var/ossec/logs/alerts/alerts.json")
print("STATE_INODE:", state["inode"])
print("STATE_OFFSET:", state["offset"])
print("CURRENT_INODE:", st.st_ino)
print("CURRENT_SIZE:", st.st_size)
print("INODE_MATCH:", state["inode"] == st.st_ino)
print("OFFSET_AT_EOF:", state["offset"] == st.st_size)
print("UNPROCESSED_BYTES:", max(0, st.st_size - state["offset"]) if state["inode"] == st.st_ino else "ROTATION")
PY
```

It showed `UNPROCESSED_BYTES: 0` (nothing unread).

```bash
systemctl show wazuh-collector.service -p ActiveState -p SubState -p MainPID -p NRestarts
```

# Closing Notes

In Part 29 we restarted the Collector without leaving anything unread.

| Item | Result |
|---|---|
| Previous file | The 20th's compressed file; confirmed by size, lines and checksum |
| Read position | Rewritten to inode 5409517, offset 0 (backup `state.json.pre-recovery-20261121`) |
| PostgreSQL | 1,318 events inserted, 0 duplicates |
| Unread | 0 bytes |

It has not been proved that no events were lost around the rotation. Also, the hidden test directory still remains, so the Collector may stop for the same reason the next time the file switches. The next part prevents this.

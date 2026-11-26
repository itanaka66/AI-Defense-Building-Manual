---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 32: Confirming an Actual Switch and Recovering Missing Events"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 32 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". In Part 31 we added a Default ACL to the per-date directories so that the Collector can read the new file even after the logs are switched. This part does the following.

1. After the actual switch on November 22, confirm that the new file inherited the ACL and that the Collector kept reading
2. Compare the compressed archives (`.json.gz`) with the counts in PostgreSQL day by day, and look for events that were not saved
3. Recover the 1,898 events found, using the same checks and the same INSERT statement as the Collector, after a trial that is rolled back (a dry run)

The events were missing because when the Collector was first started at 11:00:48 on November 18, it began reading `alerts.json` **from the end** (the first start is designed to read from the end). The 520 events on the 17th and 1,378 events on the 18th before that time were not in PostgreSQL.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **postgresql**: LXC 109 (192.168.0.151)
- Unless otherwise noted, times are in UTC (Japan time is 9 hours ahead).

# Chapter 1: Confirming the Actual Switch

## 1.1 The New File

After 09:05 Japan time, run the last command from Part 31.

> **Run on: VM 220**

```bash
echo "===== DAILY JSON FILES ====="
find /var/ossec/logs/alerts/2026/Nov -maxdepth 1 -type f -name 'ossec-alerts-*.json*' -printf '%TY-%Tm-%Td %TH:%TM:%TS | inode=%i | size=%s | %f\n' | sort
echo "===== CURRENT ALERT FILE ====="
stat -c '%n | inode=%i | size=%s | mode=%a' /var/ossec/logs/alerts/alerts.json
```

- `ossec-alerts-21.json.gz` had been created at 00:00:11
- A new `ossec-alerts-22.json` (inode 5409424) existed, and `alerts.json` pointed to the same inode
- The new file's mode was `640`

## 1.2 ACL and Reading

```bash
echo "===== NEW FILE ACL ====="
getfacl -p /var/ossec/logs/alerts/2026/Nov/ossec-alerts-22.json
echo "===== COLLECTOR READ TEST ====="
runuser -u wazuh-collector -- test -r /var/ossec/logs/alerts/2026/Nov/ossec-alerts-22.json
echo "COLLECTOR_READ_TEST_EXIT=$?"
echo "===== CURRENT ALERT LINK ====="
stat -c '%n | inode=%i | size=%s | mode=%a' /var/ossec/logs/alerts/alerts.json
```

The new file had inherited `user:wazuh-collector:r-x` (effective `r--`), and `COLLECTOR_READ_TEST_EXIT=0`.

## 1.3 The Collector's Read Position

Show only the inode and position from the state file.

```bash
echo "===== COLLECTOR SERVICE ====="
systemctl show wazuh-collector.service -p MainPID -p NRestarts -p ActiveState -p SubState

echo "===== COLLECTOR STATE ====="
python3 -c 'import json; p="/var/lib/wazuh-collector/state.json"; s=json.load(open(p)); print("STATE_INODE:",s.get("inode")); print("STATE_OFFSET:",s.get("offset"))'

echo "===== CURRENT FILE ====="
stat -c 'CURRENT_INODE=%i CURRENT_SIZE=%s' /var/ossec/logs/alerts/alerts.json
```

```text
NRestarts=0
ActiveState=active
SubState=running
===== COLLECTOR STATE =====
STATE_INODE: 5409424
STATE_OFFSET: 335703
===== CURRENT FILE =====
CURRENT_INODE=5409424 CURRENT_SIZE=335703
```

The Collector switched to the new inode without restarting and had read to the end of the file.

## 1.4 Saving to PostgreSQL

> **Run on: postgresql** (OS user `postgres`)

```bash
psql -d security_workbench -c "
SELECT
    COUNT(*) AS events_after_rotation,
    COUNT(DISTINCT event_id) AS distinct_event_ids,
    MIN(ingested_at) AS first_ingested_at,
    MAX(ingested_at) AS latest_ingested_at
FROM incident.alert_events
WHERE ingested_at >= TIMESTAMPTZ '2026-11-22 00:08:18+00';
"
```

Since the new file was created, 88 events (88 distinct `event_id`s) had been saved. **The switch on November 22 was handled correctly.**

# Chapter 2: Partial Lines at Switching

## 2.1 How Partial Lines Are Handled

> **Run on: VM 220**

```bash
echo "===== ROTATION AND INCOMPLETE-LINE HANDLING ====="
grep -n -A100 -B25 -E 'def read_alert_line|Incomplete alert line discarded at rotation|read_alert_line\(' /usr/local/lib/wazuh-collector/collector.py
```

If the file is switched in the middle of a line (before the newline arrives), the Collector discards that line with a warning and moves to the start of the new file. However, if Wazuh writes each line in one go, this path is normally not taken.

```bash
echo "===== COLLECTOR READ SETTINGS ====="
grep -n -E '^(MAX_ALERT_LINE_BYTES|READ_CHUNK_BYTES|POLL_INTERVAL|ALERT_FILE|STATE_FILE)[[:space:]]*=' /usr/local/lib/wazuh-collector/collector.py
echo "===== WRITE / ROTATION SETTINGS ====="
grep -n -E 'analysisd\.min_rotate_interval|monitord\.(day_wait|size_rotate|rotate_log|compress|keep_log_days)' /var/ossec/etc/internal_options.conf
```

The Collector reads every second, and a line can be up to 1 MiB. Wazuh waits 10 seconds before switching (`day_wait=10`).

## 2.2 Are There Partial Lines in the Archives?

Check every line of the compressed archives: can it be read as JSON, and does it end with a newline?

```bash
python3 - <<'PY'
import gzip
import json
from pathlib import Path

base = Path("/var/ossec/logs/alerts/2026/Nov")

for path in sorted(base.glob("ossec-alerts-*.json.gz")):
    lines = 0
    invalid = 0
    unterminated = False

    with gzip.open(path, "rb") as f:
        for line in f:
            lines += 1
            if not line.endswith(b"\n"):
                unterminated = True
            try:
                json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                invalid += 1

    print(
        f"{path.name}: lines={lines}, "
        f"invalid_json={invalid}, "
        f"unterminated_last_line={unterminated}"
    )
PY
```

All 47,137 lines in the 5 files could be read as JSON, and no last line lacked a newline. No partial lines remain in the archives.

# Chapter 3: Looking for Events That Were Not Saved

## 3.1 Time Ranges of the Archives

```bash
python3 - <<'PY'
import gzip
import json
from pathlib import Path

base = Path("/var/ossec/logs/alerts/2026/Nov")

for path in sorted(base.glob("ossec-alerts-*.json.gz")):
    count = 0
    first = None
    last = None
    missing_timestamp = 0

    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = obj.get("timestamp")
            if not isinstance(ts, str):
                missing_timestamp += 1
                continue

            count += 1
            if first is None:
                first = ts
            last = ts

    print(
        f"{path.name}: events={count}, "
        f"first={first}, last={last}, "
        f"missing_timestamp={missing_timestamp}"
    )
PY
```

| File | Events | First | Last |
|---|---:|---|---|
| `ossec-alerts-17.json.gz` | 520 | 11-17 20:14:42 | 11-17 23:54:53 |
| `ossec-alerts-18.json.gz` | 2,144 | 11-18 00:00:31 | 11-18 23:53:10 |
| `ossec-alerts-21.json.gz` | 25,141 | 11-21 00:09:26 | 11-22 00:00:00 |

(The files for the 19th and 20th are shown the same way.)

## 3.2 Daily Counts in PostgreSQL

> **Run on: postgresql** (enter `psql` and switch to the database `security_workbench`)

```sql
\c security_workbench
```

> **Caution**: When `psql` is started without arguments, it connects to the database `postgres`. There, `incident.alert_events` cannot be found.

```sql
SELECT
    (event_timestamp AT TIME ZONE 'UTC')::date AS utc_date,
    COUNT(*) AS db_events,
    COUNT(DISTINCT event_id) AS distinct_event_ids,
    MIN(event_timestamp) AS first_event,
    MAX(event_timestamp) AS last_event
FROM incident.alert_events
WHERE event_timestamp >= TIMESTAMPTZ '2026-11-17 00:00:00+00'
  AND event_timestamp <  TIMESTAMPTZ '2026-11-23 00:00:00+00'
GROUP BY 1
ORDER BY 1;
```

The 19th, 20th and 21st had almost the same counts as the archives. But **for the 18th, the archive had 2,144 events while PostgreSQL had 766**, and the first event was at 11:00:59. There was not a single event for the 17th.

```sql
SELECT
    COUNT(*) AS db_events_before_1100_utc,
    MIN(event_timestamp) AS first_event,
    MAX(event_timestamp) AS last_event,
    MIN(ingested_at) AS first_ingested_at,
    MAX(ingested_at) AS last_ingested_at
FROM incident.alert_events
WHERE event_timestamp >= TIMESTAMPTZ '2026-11-18 00:00:00+00'
  AND event_timestamp <  TIMESTAMPTZ '2026-11-18 11:00:00+00';
```

PostgreSQL had 0 events from before 11:00 on the 18th.

## 3.3 The Cause

> **Run on: VM 220**

```bash
journalctl -u wazuh-collector.service \
  --since "2026-11-18 00:00:00 UTC" \
  --until "2026-11-18 12:00:00 UTC" \
  --no-pager -o short-iso |
grep -Ei 'starting|established|failed|error|warning|rotation|resume|stopped|exit|restart|permission|alert'
```

```text
2026-11-18 11:00:48,467 INFO Initial start at current end of alerts.json
2026-11-18 11:00:48,491 INFO PostgreSQL connection established
```

The Collector was first started at 11:00:48 on November 18 and began reading `alerts.json` **from the end**. Events before that were never read. This is due to how the first start works, separate from the ACL and switching problems. Count the 18th's events before and after the start.

```bash
python3 - <<'PY'
import gzip
import json
from pathlib import Path
from datetime import datetime, timezone

path = Path("/var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json.gz")
cutoff = datetime(2026, 11, 18, 11, 0, 48, tzinfo=timezone.utc)

before = 0
after = 0
invalid = 0

with gzip.open(path, "rt", encoding="utf-8") as f:
    for line in f:
        try:
            obj = json.loads(line)
            ts = datetime.fromisoformat(obj["timestamp"].replace("Z", "+00:00"))
            if ts < cutoff:
                before += 1
            else:
                after += 1
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            invalid += 1

print("BEFORE_COLLECTOR_START:", before)
print("AT_OR_AFTER_COLLECTOR_START:", after)
print("INVALID_RECORDS:", invalid)
print("ARCHIVE_TOTAL:", before + after + invalid)
PY
```

```text
BEFORE_COLLECTOR_START: 1378
AT_OR_AFTER_COLLECTOR_START: 766
INVALID_RECORDS: 0
ARCHIVE_TOTAL: 2144
```

The 766 events after the start matched the count in PostgreSQL. All 520 events on the 17th were also before the start. The events not saved are expected to be **520 on the 17th and 1,378 on the 18th, 1,898 in total**.

# Chapter 4: Preparing the Recovery

## 4.1 Can the Collector's Checks and INSERT Statement Be Used?

The recovery uses the same checks as the Collector (the field whitelist and input validation) and the same INSERT statement.

```bash
echo "===== EVENT EXTRACTION AND VALIDATION ====="
grep -n -A105 -B10 '^def extract_event' /usr/local/lib/wazuh-collector/collector.py
echo "===== INSERT AND DUPLICATE HANDLING ====="
grep -n -A28 -B5 '^INSERT_SQL\|^def process_line' /usr/local/lib/wazuh-collector/collector.py
```

- `extract_event()` applies the field whitelist and input validation
- `INSERT_SQL` is the same one the Collector normally uses
- `event_id` is the primary key, so existing events are detected as duplicates (SQLSTATE `23505`)
- The Collector's role (`wazuh_collector`) needs only INSERT; no SELECT, UPDATE or DELETE permission is required

## 4.2 IDs Inside the Archives

```bash
python3 - <<'PY'
import gzip
import json
from pathlib import Path
from collections import Counter

base = Path("/var/ossec/logs/alerts/2026/Nov")
files = [
    base / "ossec-alerts-17.json.gz",
    base / "ossec-alerts-18.json.gz",
]

ids = Counter()
invalid = 0
total = 0

for path in files:
    file_count = 0
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            total += 1
            file_count += 1
            try:
                obj = json.loads(line)
                event_id = obj.get("id")
                if isinstance(event_id, str) and event_id:
                    ids[event_id] += 1
                else:
                    invalid += 1
            except (json.JSONDecodeError, UnicodeDecodeError):
                invalid += 1

    print(f"{path.name}: records={file_count}")

duplicates = sum(count - 1 for count in ids.values() if count > 1)

print("TOTAL_RECORDS:", total)
print("VALID_EVENT_IDS:", sum(ids.values()))
print("UNIQUE_EVENT_IDS:", len(ids))
print("DUPLICATE_ID_OCCURRENCES:", duplicates)
print("INVALID_OR_MISSING_IDS:", invalid)
PY
```

The 2 files contained 2,664 records; all IDs were valid and there were no duplicates.

## 4.3 A Trial That Is Rolled Back (Dry Run)

We actually INSERT into PostgreSQL, but the outer transaction is **always rolled back**. The Collector's connection settings (`DB_CONFIG`) and functions are loaded from `collector.py`. Connection settings and passwords are not shown.

```bash
python3 - <<'PY'
import gzip
import json
import importlib.util
from pathlib import Path
import psycopg

spec = importlib.util.spec_from_file_location(
    "wazuh_collector",
    "/usr/local/lib/wazuh-collector/collector.py"
)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)

files = [
    Path("/var/ossec/logs/alerts/2026/Nov/ossec-alerts-17.json.gz"),
    Path("/var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json.gz"),
]

class DryRunComplete(Exception):
    pass

connection = psycopg.connect(**collector.DB_CONFIG)
inserted = 0
duplicates = 0
rejected = 0
records = 0

try:
    try:
        with connection.transaction():
            for path in files:
                with gzip.open(path, "rt", encoding="utf-8") as source:
                    for line in source:
                        records += 1
                        try:
                            alert = json.loads(line)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            rejected += 1
                            continue

                        event = collector.extract_event(alert)
                        if event is None:
                            rejected += 1
                            continue

                        try:
                            with connection.transaction():
                                connection.execute(
                                    collector.INSERT_SQL,
                                    event
                                )
                            inserted += 1
                        except psycopg.errors.UniqueViolation as error:
                            if error.sqlstate != "23505":
                                raise
                            duplicates += 1

            raise DryRunComplete()
    except DryRunComplete:
        pass

    print("DB_ROLE:", connection.info.user)
    print("ARCHIVE_RECORDS:", records)
    print("WOULD_INSERT:", inserted)
    print("ALREADY_EXISTS:", duplicates)
    print("REJECTED:", rejected)
    print("TRANSACTION: ROLLED BACK")
finally:
    connection.close()
PY
```

```text
DB_ROLE: wazuh_collector
ARCHIVE_RECORDS: 2664
WOULD_INSERT: 1898
ALREADY_EXISTS: 766
REJECTED: 0
TRANSACTION: ROLLED BACK
```

1,898 events would be newly inserted and 766 already existed, as expected. Because it was rolled back, PostgreSQL did not change.

# Chapter 5: Recovering the 1,898 Events

Because this writes to PostgreSQL, approval was obtained before running it in the original build. It is done under these conditions.

- The normal Collector is not stopped
- Only `ossec-alerts-17.json.gz` and `ossec-alerts-18.json.gz` are processed
- Abort unless the role is `wazuh_collector`
- Everything is one transaction; if the counts differ from the dry run, everything is rolled back

> **Run on: VM 220**

```bash
python3 - <<'PY'
import gzip
import json
import importlib.util
from pathlib import Path
import psycopg

spec = importlib.util.spec_from_file_location(
    "wazuh_collector",
    "/usr/local/lib/wazuh-collector/collector.py"
)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)

files = [
    Path("/var/ossec/logs/alerts/2026/Nov/ossec-alerts-17.json.gz"),
    Path("/var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json.gz"),
]

expected = {
    "records": 2664,
    "inserted": 1898,
    "duplicates": 766,
    "rejected": 0,
}

connection = psycopg.connect(**collector.DB_CONFIG)
counts = {
    "records": 0,
    "inserted": 0,
    "duplicates": 0,
    "rejected": 0,
}
seen_ids = set()

try:
    if connection.info.user != "wazuh_collector":
        raise RuntimeError("Unexpected database role; refusing recovery")

    with connection.transaction():
        for path in files:
            if not path.is_file():
                raise FileNotFoundError(path)

            with gzip.open(path, "rt", encoding="utf-8") as source:
                for line in source:
                    counts["records"] += 1
                    alert = json.loads(line)
                    event = collector.extract_event(alert)

                    if event is None:
                        counts["rejected"] += 1
                        continue

                    event_id = event["event_id"]
                    if event_id in seen_ids:
                        raise RuntimeError("Duplicate archive event ID")
                    seen_ids.add(event_id)

                    try:
                        with connection.transaction():
                            connection.execute(
                                collector.INSERT_SQL,
                                event
                            )
                        counts["inserted"] += 1
                    except psycopg.errors.UniqueViolation as error:
                        if error.sqlstate != "23505":
                            raise
                        counts["duplicates"] += 1

        if counts != expected:
            raise RuntimeError(
                f"Count mismatch; transaction will roll back: {counts}"
            )

    print("RECOVERY_STATUS: COMMITTED")
    print("DB_ROLE:", connection.info.user)
    for key, value in counts.items():
        print(f"{key.upper()}:", value)

except Exception as error:
    print("RECOVERY_STATUS: FAILED; TRANSACTION ROLLED BACK")
    print("ERROR_TYPE:", type(error).__name__)
    print("COUNTS_AT_FAILURE:", counts)

finally:
    connection.close()
PY
```

```text
RECOVERY_STATUS: COMMITTED
DB_ROLE: wazuh_collector
RECORDS: 2664
INSERTED: 1898
DUPLICATES: 766
REJECTED: 0
```

# Chapter 6: Checks After the Recovery

## 6.1 Counts in PostgreSQL

`wazuh_collector` can only INSERT, so the check is done on the PostgreSQL server.

> **Run on: postgresql** (root)

```bash
sudo -u postgres psql -d security_workbench -c "
SELECT
    (event_timestamp AT TIME ZONE 'UTC')::date AS event_date,
    COUNT(*) AS total_records,
    COUNT(DISTINCT event_id) AS unique_event_ids,
    COUNT(*) - COUNT(DISTINCT event_id) AS duplicate_ids,
    MIN(event_timestamp AT TIME ZONE 'UTC') AS first_event_utc,
    MAX(event_timestamp AT TIME ZONE 'UTC') AS last_event_utc
FROM incident.alert_events
WHERE event_timestamp >= TIMESTAMPTZ '2026-11-17 00:00:00+00'
  AND event_timestamp <  TIMESTAMPTZ '2026-11-19 00:00:00+00'
GROUP BY (event_timestamp AT TIME ZONE 'UTC')::date
ORDER BY event_date;
"
```

| Date | Events | Distinct IDs | Duplicates |
|---|---:|---:|---:|
| 2026-11-17 | 520 | 520 | 0 |
| 2026-11-18 | 2,144 | 2,144 | 0 |

All 2,664 events in the archives are saved, with no duplicates.

## 6.2 The Normal Collector

> **Run on: VM 220**

Check the service and read position with the same command as in 1.3.

```bash
echo "===== COLLECTOR SERVICE ====="
systemctl show wazuh-collector.service -p MainPID -p NRestarts -p ActiveState -p SubState

echo "===== COLLECTOR STATE ====="
python3 -c 'import json; p="/var/lib/wazuh-collector/state.json"; s=json.load(open(p)); print("STATE_INODE:",s.get("inode")); print("STATE_OFFSET:",s.get("offset"))'

echo "===== CURRENT FILE ====="
stat -c 'CURRENT_INODE=%i CURRENT_SIZE=%s' /var/ossec/logs/alerts/alerts.json
```

The service was `running`, the inode was 5409424, and the position and the file size were both 4,627,640 bytes, so nothing was left unread. The Collector's log recorded `Switched to new alerts.json inode` at 00:00:00 on November 22.

> **Run on: postgresql** (root)

```bash
sudo -u postgres psql -d security_workbench -c "
SELECT
    COUNT(*) AS records_last_30_minutes,
    COUNT(DISTINCT event_id) AS unique_event_ids,
    MAX(ingested_at) AS latest_ingested_at,
    MAX(event_timestamp) AS latest_event_timestamp
FROM incident.alert_events
WHERE ingested_at >= NOW() - INTERVAL '30 minutes';
"
```

In the last 30 minutes, 5,753 events (5,753 distinct IDs) had been saved. Normal ingestion is also continuing.

# Closing Notes

In Part 32 we confirmed an actual switch and recovered the events that had not been saved.

| Item | Result |
|---|---|
| The switch on November 22 | The new file inherited the ACL and the Collector followed it without restarting; 88 events saved |
| Archives | 5 files, 47,137 lines, no broken or partial lines |
| Why events were missing | At the first start (11:00:48 on November 18), the Collector began reading `alerts.json` from the end |
| Recovery | 520 events on the 17th and 1,378 on the 18th, 1,898 in total, saved in one transaction after a dry run |
| After the recovery | All 2,664 events for the 17th and 18th saved, 0 duplicates; normal ingestion continuing |

In Part 33 we make the Collector's state observable with Prometheus.

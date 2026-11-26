---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 36: Checking PostgreSQL"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 36 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". By Part 35, the monitoring foundation from Wazuh and the Collector through the Prometheus rules was complete. Here we check, **using reads only**, the **PostgreSQL** where the Collector stores events (LXC 109, 192.168.0.151, database `security_workbench`, table `incident.alert_events`).

| What we check | Result |
|---|---|
| Connectivity | Normal |
| Permissions of the Collector's role (`wazuh_collector`) | INSERT only; no administrative permissions |
| Table structure (primary key, indexes, constraints) | Normal |
| Data contents (duplicates, malformed values) | 55,811 rows, 0 anomalies |
| Ingestion delay | Last 30 minutes: 0.86 seconds on average |
| Size, VACUUM, connection count | Normal |
| WAL, checkpoints | Normal; WAL archiving not configured |
| Backups | **No PostgreSQL backup found** |

The last item becomes the task for Part 37.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **postgresql**: LXC 109 (192.168.0.151, root). SQL is run with `sudo -u postgres psql …`

# Chapter 1: Connectivity and the Collector's Settings

## 1.1 Can We Connect?

> **Run on: VM 220**

```bash
echo "===== POSTGRESQL CONNECTIVITY ====="
pg_isready -h 192.168.0.151 -p 5432 -t 5
echo "PG_ISREADY_EXIT=$?"
```

```text
192.168.0.151:5432 - accepting connections
PG_ISREADY_EXIT=0
```

## 1.2 Where the Collector Connects

From the Collector's `DB_CONFIG`, extract only the connection destination fields. `DB_CONFIG` contains values that reference environment variables and the like, so the file is parsed as Python syntax and only the values of fixed fields (`host`, `hostaddr`, `port`, `dbname`, `database`, `user`) are shown. Passwords and the like are not shown.

```bash
python3 - <<'PY'
import ast
from pathlib import Path

p = Path("/usr/local/lib/wazuh-collector/collector.py")
tree = ast.parse(p.read_text())

safe_keys = {"host", "hostaddr", "port", "dbname", "database", "user"}

for node in tree.body:
    if not isinstance(node, ast.Assign):
        continue
    if not any(isinstance(t, ast.Name) and t.id == "DB_CONFIG" for t in node.targets):
        continue

    if not isinstance(node.value, ast.Dict):
        print("DB_CONFIG is not a literal dictionary")
        break

    print("===== SAFE DB CONFIGURATION =====")
    for key_node, value_node in zip(node.value.keys, node.value.values):
        if not isinstance(key_node, ast.Constant):
            continue
        key = key_node.value
        if key not in safe_keys:
            continue

        if isinstance(value_node, ast.Constant):
            value = value_node.value
        elif isinstance(value_node, ast.Name):
            value = "<dynamic reference: " + value_node.id + ">"
        else:
            value = "<dynamic expression>"

        print(f"{key} = {value}")
    break
else:
    print("DB_CONFIG assignment not found")
PY
```

```text
===== SAFE DB CONFIGURATION =====
host = postgresql.neomedia.mydns.jp
hostaddr = 192.168.0.151
port = 5432
dbname = security_workbench
user = wazuh_collector
```

# Chapter 2: The Table and Permissions

## 2.1 Table Structure

> **Run on: postgresql**

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c '\d+ incident.alert_events'
```

| Item | Result |
|---|---|
| Primary key | `event_id` (the same event cannot be inserted twice) |
| Indexes | 5 |
| CHECK constraints | 3 (`rule_level` 0–16, `srcport` 0–65535, `mitre` is a JSON object) |
| Raw log columns | None (no `full_log` or similar; only fixed fields are stored) |

## 2.2 Permissions of the Collector's Role

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    current_user AS inspected_by,
    has_schema_privilege('wazuh_collector', 'incident', 'USAGE') AS schema_usage,
    has_table_privilege('wazuh_collector', 'incident.alert_events', 'INSERT') AS can_insert,
    has_table_privilege('wazuh_collector', 'incident.alert_events', 'SELECT') AS can_select,
    has_table_privilege('wazuh_collector', 'incident.alert_events', 'UPDATE') AS can_update,
    has_table_privilege('wazuh_collector', 'incident.alert_events', 'DELETE') AS can_delete;
"
```

```text
 inspected_by | schema_usage | can_insert | can_select | can_update | can_delete
--------------+--------------+------------+------------+------------+------------
 postgres     | t            | t          | f          | f          | f
```

The Collector can write events but cannot read, change or delete existing data. This is an important safeguard that makes it hard to rewrite stored events even if the Collector is compromised.

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    rolname,
    rolsuper AS is_superuser,
    rolinherit AS inherits_roles,
    rolcreaterole AS can_create_roles,
    rolcreatedb AS can_create_databases,
    rolcanlogin AS can_login,
    rolreplication AS can_replicate,
    rolbypassrls AS bypasses_row_security
FROM pg_roles
WHERE rolname = 'wazuh_collector';
"
```

Only `can_login` was `t`; superuser, role inheritance, permission to create roles or databases, replication and bypassing RLS were all `f`. These permissions are not changed.

# Chapter 3: Data Contents

## 3.1 Malformed Values and Duplicates

Individual events (IP addresses, agent names and so on) are not shown; only aggregate values are examined.

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    COUNT(*) AS total_records,
    COUNT(DISTINCT event_id) AS unique_event_ids,
    COUNT(*) FILTER (WHERE rule_level < 0 OR rule_level > 16) AS invalid_rule_levels,
    COUNT(*) FILTER (WHERE srcport < 0 OR srcport > 65535) AS invalid_source_ports,
    COUNT(*) FILTER (WHERE jsonb_typeof(mitre) <> 'object') AS invalid_mitre_objects,
    COUNT(*) FILTER (WHERE cardinality(rule_groups) = 0) AS empty_rule_groups,
    COUNT(*) FILTER (WHERE event_timestamp > now() + interval '5 minutes') AS future_events,
    COUNT(*) FILTER (WHERE ingested_at < event_timestamp) AS negative_ingestion_lag,
    ROUND(
        EXTRACT(EPOCH FROM (now() - MAX(ingested_at)))::numeric,
        2
    ) AS latest_ingestion_age_seconds,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (ingested_at - event_timestamp)))::numeric,
        3
    ) AS avg_ingestion_lag_seconds
FROM incident.alert_events;
"
```

| Item | Result |
|---|---:|
| Rows | 55,811 |
| Distinct `event_id`s | 55,811 |
| Malformed rule level, source port or MITRE | 0 |
| Empty rule groups | 0 |
| Future timestamps / ingestion before the event | 0 |
| Time since the last ingestion | 137.03 seconds |
| Average ingestion delay | 19,468.776 seconds |

The average delay comes out large, about 5.5 hours, probably because the past archives added later in Part 32 push the average up. Look at it by period.

## 3.2 Ingestion Delay by Period

> **Note**: In PostgreSQL, an alias given within the same SELECT (`ingestion_period`) cannot be referenced from a `CASE` inside `ORDER BY` (it gives `column "ingestion_period" does not exist`). The command below first classifies the period in a CTE (`WITH`) and then aggregates.

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
WITH classified AS (
    SELECT
        CASE
            WHEN ingested_at >= now() - interval '30 minutes' THEN 'last_30m'
            WHEN ingested_at >= now() - interval '24 hours' THEN 'last_24h'
            ELSE 'older'
        END AS ingestion_period,
        EXTRACT(EPOCH FROM (ingested_at - event_timestamp)) AS lag_seconds
    FROM incident.alert_events
)
SELECT
    ingestion_period,
    COUNT(*) AS records,
    ROUND(AVG(lag_seconds)::numeric, 2) AS avg_lag_seconds,
    ROUND(percentile_cont(0.50) WITHIN GROUP (ORDER BY lag_seconds)::numeric, 2) AS median_lag_seconds,
    ROUND(percentile_cont(0.95) WITHIN GROUP (ORDER BY lag_seconds)::numeric, 2) AS p95_lag_seconds,
    ROUND(MAX(lag_seconds)::numeric, 2) AS max_lag_seconds
FROM classified
GROUP BY ingestion_period
ORDER BY CASE ingestion_period
    WHEN 'last_30m' THEN 1
    WHEN 'last_24h' THEN 2
    ELSE 3
END;
"
```

| Period | Rows | Average | Median | 95% |
|---|---:|---:|---:|---:|
| Last 30 minutes | 15 | 0.86 s | 0.91 s | 0.99 s |
| Last 24 hours (excluding the 30 minutes) | 35,705 | 18,587.53 s | 1.07 s | 322,119.38 s |
| Older | 20,098 | 21,042.09 s | 11,725.46 s | 61,876.70 s |

The last 30 minutes were ingested in under a second, so current ingestion is normal. The 24-hour median is also about 1 second; the average is large because of old events added later.

# Chapter 4: Size and Connections

## 4.1 Table Size and VACUUM

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    schemaname,
    relname AS table_name,
    pg_size_pretty(pg_relation_size(relid)) AS table_size,
    pg_size_pretty(pg_indexes_size(relid)) AS indexes_size,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    n_live_tup AS estimated_live_rows,
    n_dead_tup AS estimated_dead_rows,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'incident'
  AND relname = 'alert_events';
"
```

The table was 12MB and the indexes 6008kB, 18MB in total. About 55,826 live rows and 766 dead rows (about 1.4%), and automatic VACUUM and ANALYZE were running. No manual VACUUM is needed.

## 4.2 Connection Count

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    current_setting('max_connections') AS max_connections,
    COUNT(*) AS total_connections,
    COUNT(*) FILTER (WHERE state = 'active') AS active_connections,
    COUNT(*) FILTER (WHERE state = 'idle') AS idle_connections,
    COUNT(*) FILTER (WHERE state = 'idle in transaction') AS idle_in_transaction,
    COUNT(*) FILTER (WHERE usename = 'wazuh_collector') AS collector_connections
FROM pg_stat_activity;
"
```

14 connections against a limit of 100; `idle in transaction` (connections stuck with an open transaction) was 0, and the Collector had 1 connection.

## 4.3 Database Size

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    datname AS database_name,
    pg_size_pretty(pg_database_size(datname)) AS database_size,
    pg_database_size(datname) AS database_size_bytes
FROM pg_database
WHERE datname = 'security_workbench';
"
```

The whole of `security_workbench` was 26MB.

# Chapter 5: WAL and Checkpoints

## 5.1 Replication Slots

An unused slot would keep WAL from being removed so that it piles up.

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    slot_name,
    slot_type,
    active,
    restart_lsn,
    CASE
        WHEN restart_lsn IS NOT NULL
        THEN pg_size_pretty(
            pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)::bigint
        )
        ELSE NULL
    END AS retained_wal
FROM pg_replication_slots;

SELECT
    COUNT(*) AS replication_slot_count
FROM pg_replication_slots;
"
```

There were 0 slots.

## 5.2 WAL and Checkpoint Settings

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    name,
    setting,
    unit,
    source
FROM pg_settings
WHERE name IN (
    'wal_level',
    'wal_keep_size',
    'max_wal_size',
    'min_wal_size',
    'checkpoint_timeout',
    'checkpoint_completion_target',
    'archive_mode',
    'archive_timeout',
    'full_page_writes',
    'synchronous_commit'
)
ORDER BY name;
"
```

| Setting | Value |
|---|---|
| `wal_level` | `replica` |
| `max_wal_size` / `min_wal_size` | 1GB / 80MB |
| `checkpoint_timeout` | 300 seconds |
| `checkpoint_completion_target` | 0.9 |
| `full_page_writes` | `on` |
| `synchronous_commit` | `on` |
| `archive_mode` | `off` |
| `wal_keep_size` | 0 |

`full_page_writes` and `synchronous_commit`, which matter for consistency after a crash and for durable commits, are both `on`. On the other hand, because `archive_mode` is `off`, recovery to an arbitrary point in time using archived WAL (PITR) is not possible.

## 5.3 Checkpoint History

> **Note**: In PostgreSQL 17, `pg_stat_checkpointer` has no `num_done` column (it gives `column "num_done" does not exist`). Check the column names first.

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'pg_catalog'
  AND table_name = 'pg_stat_checkpointer'
ORDER BY ordinal_position;
"
```

The columns were `num_timed`, `num_requested`, `restartpoints_timed`, `restartpoints_req`, `restartpoints_done`, `write_time`, `sync_time`, `buffers_written` and `stats_reset`.

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    stats_reset,
    num_timed AS scheduled_checkpoints,
    num_requested AS requested_checkpoints,
    restartpoints_timed,
    restartpoints_req,
    restartpoints_done,
    ROUND(write_time::numeric, 2) AS write_time_ms,
    ROUND(sync_time::numeric, 2) AS sync_time_ms,
    buffers_written,
    pg_size_pretty(
        (buffers_written * current_setting('block_size')::bigint)
    ) AS checkpoint_write_volume
FROM pg_stat_checkpointer;
"
```

Since statistics began on 2026-11-17, there had been 1,349 scheduled checkpoints and only 4 requested ones. About 241MB was written and sync time totaled about 28 seconds; checkpoints are stable.

## 5.4 WAL Files

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    pg_size_pretty(COALESCE(SUM(size), 0)::bigint) AS wal_directory_size,
    COUNT(*) AS wal_file_count,
    pg_size_pretty(
        COALESCE(MAX(size), 0)::bigint
    ) AS largest_file
FROM pg_ls_waldir();
"
```

WAL was 32MB (two 16MB files), small against the 1GB limit, and not piling up.

# Chapter 6: Looking for Backups

## 6.1 Archiving and the Data Location

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    name,
    setting,
    unit,
    source
FROM pg_settings
WHERE name IN (
    'data_directory',
    'archive_mode',
    'archive_command',
    'archive_timeout',
    'wal_level'
)
ORDER BY name;
"
```

The data is in `/var/lib/postgresql/17/main` (PostgreSQL 17); `archive_mode` was `off` and `archive_command` was `(disabled)`.

## 6.2 Backup Services and Files

```bash
echo "===== BACKUP RELATED SYSTEMD UNITS ====="
systemctl list-timers --all --no-pager | grep -Ei 'backup|postgres|pgbackrest|barman|borg|restic|rclone|snapshot'
echo "===== BACKUP RELATED SERVICES ====="
systemctl list-units --type=service --all --no-pager | grep -Ei 'backup|postgres|pgbackrest|barman|borg|restic|rclone'
echo "===== COMMON BACKUP DIRECTORIES ====="
for d in /var/backups /backup /backups /srv/backup /mnt/backup; do
    if [ -d "$d" ]; then
        stat -c '%A %U:%G %n' "$d"
    fi
done
```

What was found was only `dpkg-db-backup.timer` (a backup of Debian's package management database, not of PostgreSQL) and the PostgreSQL service itself. pgBackRest, Barman, Borg, Restic and the like were not present either. Look only at file names, times and sizes (the contents are not read).

```bash
echo "===== /var/backups FILE INVENTORY ====="
find /var/backups -maxdepth 3 -type f \
  -printf '%TY-%Tm-%Td %TH:%TM | %s bytes | %p\n' \
  2>/dev/null | sort -r

echo "===== BACKUP-RELATED CRON FILE NAMES ====="
find /etc/cron.d /etc/cron.daily /etc/cron.hourly /etc/cron.weekly \
  -maxdepth 1 -type f \
  \( -iname '*backup*' -o -iname '*postgres*' -o -iname '*pg*' \) \
  -printf '%p\n' 2>/dev/null
```

`/var/backups` held only package management files such as `alternatives.tar.0` and `dpkg.*`; there were no PostgreSQL backup files and no cron jobs.

| Item | Result |
|---|---|
| PostgreSQL backup files | None |
| cron for PostgreSQL | None |
| systemd timer for PostgreSQL | None |
| WAL archiving | Disabled |

**As far as we looked, there is no backup from which PostgreSQL data could be restored.** If the database were damaged, the events collected from Wazuh and the analysis records could be lost.

# Closing Notes

In Part 36 we checked PostgreSQL using reads only.

| Item | Result |
|---|---|
| Collector permissions | INSERT only (no SELECT, UPDATE or DELETE; no administrative permissions) |
| Data | 55,811 rows, 0 duplicates or malformed values |
| Ingestion delay | Last 30 minutes: 0.86 seconds on average |
| Size | Table 18MB, DB 26MB, 1.4% dead rows |
| Connections | 14 of 100, `idle in transaction` 0 |
| WAL, checkpoints | Normal (WAL 32MB, 0 slots) |
| Issues | No WAL archiving, no PostgreSQL backups |

In Part 37 we back up LXC 109, where PostgreSQL runs, with Proxmox, restore it to an LXC with a different number, and test whether it can really be restored.

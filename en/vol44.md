---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 44: Comparing the Restored Databases with Production"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 44 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual", and the last part of Volume 3. In Part 43 we fixed the NFS mount after a reboot and the LXC 109 backup failure. Here we check that the backup system works correctly as a whole, and compare the databases of CTID 310, restored in Part 41, in detail with the production CTID 109.

1. Check that Proxmox recognizes the backups as official backups, and that the job and the boot dependencies are still in place
2. Check the state of CTID 310 (used for the restore test) and the thin pool
3. Start CTID 310 with its network cut off and check PostgreSQL
4. Compare the tables, views, indexes, constraints, extensions and schema definitions of the 17 databases with CTID 109

No data, settings or services are changed or restarted. Everything is read-only.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)

# Chapter 1: Checking the Backup System

## 1.1 Catalog, Job and Boot Dependencies

> **Run on: pve**

```bash
echo "===== PVE BACKUP CATALOG ====="
pvesm list truenas-backup --content backup --vmid 109

echo
echo "===== LXC109 SCHEDULED JOB ====="
pvesh get /cluster/backup/lxc109-daily --output-format json-pretty

echo
echo "===== NFS MOUNT READINESS DEPENDENCY ====="
systemctl show mnt-pve-backup.mount \
  -p LoadState \
  -p ActiveState \
  -p SubState \
  -p Requires \
  -p After

echo
echo "===== TRUENAS READINESS SERVICE ====="
systemctl show truenas-nfs-ready.service \
  -p LoadState \
  -p ActiveState \
  -p SubState

echo
echo "===== BACKUP ARCHIVE AND LOG ====="
ls -lh \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_23-09_43_34.tar.zst \
  /var/log/vzdump/lxc-109.log
```

| Item | Result |
|---|---|
| Backup catalog | two generations of LXC 109 registered (November 22 20:28, November 23 09:43) |
| `lxc109-daily` | daily 03:00, snapshot, zstd, `truenas-backup`, 7 daily, 4 weekly, 3 monthly, `/var/tmp`, enabled |
| `mnt-pve-backup.mount` | `Requires=truenas-nfs-ready.service`, `After=truenas-nfs-ready.service` |
| `truenas-nfs-ready.service` | `inactive/dead` (a oneshot service that finished normally) |

The archives are not only on NFS but are also registered in Proxmox's backup catalog.

## 1.2 Restore Method and Settings Inside the Archive

> **Run on: pve**

```bash
echo "===== PCT RESTORE OPTIONS ====="
pct help restore

echo
echo "===== BACKUP ARCHIVE CONTAINER CONFIG ====="
tar --use-compress-program=unzstd \
  -xOf /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_23-09_43_34.tar.zst \
  ./etc/vzdump/pct.conf

echo
echo "===== STORAGE STATUS ====="
pvesm status

echo
echo "===== EXISTING CONTAINER 109 CONFIG ====="
pct config 109
```

The settings recorded in the archive were the same as the current CT109 (Debian, amd64, 2 vCPUs, 4GB memory, 50GB root disk, unprivileged, `nesting=1,keyctl=1`, `192.168.0.151/24`, `onboot=1`). We check with a different CTID without overwriting the production CT109.

## 1.3 CTID 310 and the Thin Pool

> **Run on: pve**

```bash
echo "===== PVE THIN POOL STATUS ====="
lvs -a -o vg_name,lv_name,lv_size,lv_attr,pool_lv,data_percent,metadata_percent pve

echo
echo "===== LOCAL-LVM POOL ONLY ====="
lvs -o vg_name,lv_name,lv_size,lv_attr,data_percent,metadata_percent pve/data

echo
echo "===== CT310 DISK VOLUME ====="
lvs -a | grep -E 'vm-310|snap_vm-310|LV'

echo
echo "===== CT109 DISK VOLUME ====="
lvs -a | grep -E 'vm-109|snap_vm-109|LV'

echo
echo "===== CT310 AND CT109 STATUS ====="
pct status 310
pct status 109
```

| Item | State |
|---|---|
| `pve/data` | 794.30GiB, data usage 61.90%, metadata 2.19% |
| Unallocated space in the VG | 16GiB |
| CTID 310 | stopped. rootfs `local-lvm:vm-310-disk-0` (50GB, 5.47% used), `link_down=1`, `onboot=0` |
| CTID 109 | running |

CTID 310, restored in Part 41, is still there with its network cut off. We use it instead of creating a new restore target.

# Chapter 2: Starting and Checking CTID 310

## 2.1 Starting It with the Network Cut Off

> **Run on: pve**

```bash
echo "===== VERIFY CT310 IS STOPPED ====="
pct status 310

echo
echo "===== VERIFY NETWORK IS DISCONNECTED ====="
pct config 310 | grep -E '^(net[0-9]+|onboot|rootfs):'

echo
echo "===== START RESTORE TEST CONTAINER CT310 ====="
pct start 310
START_EXIT=$?
echo "START_EXIT=$START_EXIT"

echo
echo "===== VERIFY CT310 STATUS ====="
pct status 310

echo
echo "===== VERIFY CT109 REMAINS RUNNING ====="
pct status 109

echo
echo "===== VERIFY CT310 NETWORK CONFIGURATION ====="
pct config 310 | grep -E '^(net[0-9]+|onboot|rootfs):'
```

CTID 310 is `running`, the production CTID 109 is also `running`, and CTID 310 remains `link_down=1`, `onboot=0`.

## 2.2 PostgreSQL State

> **Run on: pve**

```bash
echo "===== CT310 POSTGRESQL SERVICE STATUS ====="
pct exec 310 -- systemctl status postgresql --no-pager

echo
echo "===== POSTGRESQL CLUSTER LIST ====="
pct exec 310 -- pg_lsclusters

echo
echo "===== POSTGRESQL LOCAL READINESS ====="
pct exec 310 -- pg_isready -h 127.0.0.1

echo
echo "===== POSTGRESQL LISTENING SOCKETS ====="
pct exec 310 -- ss -lntp

echo
echo "===== CT310 NETWORK INTERFACES ====="
pct exec 310 -- ip -brief address

echo
echo "===== CT310 NETWORK ROUTES ====="
pct exec 310 -- ip route
```

PostgreSQL 17 `main` is `online` and accepts connections on `127.0.0.1:5432`; `eth0` is `DOWN` and there are no routes. PostgreSQL also listens on `0.0.0.0:5432` and `[::]:5432`, but the virtual NIC is disconnected, so nothing reaches it from outside. We keep this isolation during the checks.

## 2.3 List of Databases

> **Run on: pve**

```bash
echo "===== POSTGRESQL VERSION ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -c "SELECT version();"

echo
echo "===== DATABASE INVENTORY ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -c "
SELECT
    datname AS database_name,
    pg_size_pretty(pg_database_size(datname)) AS database_size,
    datallowconn AS connections_allowed
FROM pg_database
WHERE datistemplate = false
ORDER BY datname;
"

echo
echo "===== USER TABLE COUNTS BY DATABASE ====="
pct exec 310 -- bash -c '
for db in $(runuser -u postgres -- psql -X -At -d postgres -c "SELECT datname FROM pg_database WHERE datistemplate = false AND datallowconn = true ORDER BY datname"); do
    echo "--- DATABASE: $db ---"
    runuser -u postgres -- psql -X -d "$db" -c "
    SELECT
        count(*) FILTER (WHERE table_type = '\''BASE TABLE'\'') AS base_tables,
        count(*) FILTER (WHERE table_type = '\''VIEW'\'') AS views
    FROM information_schema.tables
    WHERE table_schema NOT IN ('\''pg_catalog'\'', '\''information_schema'\'');
    "
done
'

echo
echo "===== DATABASE RECOVERY STATUS ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -c "
SELECT
    pg_is_in_recovery() AS in_recovery,
    current_setting('data_directory') AS data_directory,
    current_setting('server_version') AS server_version;
"
```

PostgreSQL 17.11, cluster `17/main` `online`, 17 databases, and `pg_is_in_recovery()` was `false`. `postgresql.service` being `active (exited)` is normal for Debian's management service.

## 2.4 Owners, Extensions, Indexes and Logs

> **Run on: pve**

```bash
echo "===== DATABASE OWNERS ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -c "
SELECT datname, pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datistemplate = false
ORDER BY datname;
"

echo
echo "===== POSTGRESQL ROLES ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -c "
SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolcanlogin
FROM pg_roles
WHERE rolname !~ '^pg_'
ORDER BY rolname;
"

echo
echo "===== INSTALLED EXTENSIONS BY DATABASE ====="
pct exec 310 -- bash -c '
for db in $(runuser -u postgres -- psql -X -At -d postgres -c "SELECT datname FROM pg_database WHERE datistemplate = false AND datallowconn = true ORDER BY datname"); do
    echo "--- DATABASE: $db ---"
    runuser -u postgres -- psql -X -d "$db" -c "
    SELECT extname, extversion
    FROM pg_extension
    ORDER BY extname;
    "
done
'

echo
echo "===== INVALID INDEX CHECK ====="
pct exec 310 -- bash -c '
for db in $(runuser -u postgres -- psql -X -At -d postgres -c "SELECT datname FROM pg_database WHERE datistemplate = false AND datallowconn = true ORDER BY datname"); do
    echo "--- DATABASE: $db ---"
    runuser -u postgres -- psql -X -d "$db" -c "
    SELECT n.nspname AS schema_name, c.relname AS index_name,
           i.indisvalid, i.indisready
    FROM pg_index i
    JOIN pg_class c ON c.oid = i.indexrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE NOT i.indisvalid OR NOT i.indisready;
    "
done
'

echo
echo "===== POSTGRESQL STARTUP LOG ====="
pct exec 310 -- bash -c \
'tail -n 100 /var/log/postgresql/postgresql-17-main.log'
```

Each database has an owner, `vector` is `0.8.7` in `easywrider`, `postgres` and `vector_db`, and there were zero invalid indexes (`indisvalid=false` or `indisready=false`) in any database.

In the role list command, `!~` was interpreted by Bash as history expansion, so the condition excluding system roles did not take effect. This is not data corruption. We retrieve it again with a corrected command and also check whether `pg_amcheck` exists.

> **Run on: pve**

```bash
echo "===== POSTGRESQL ROLES (CORRECTED) ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -c "
SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolcanlogin
FROM pg_roles
WHERE left(rolname, 3) <> 'pg_'
ORDER BY rolname;
"

echo
echo "===== PG_AMCHECK AVAILABILITY ====="
pct exec 310 -- bash -c '
if command -v pg_amcheck >/dev/null 2>&1; then
    command -v pg_amcheck
    pg_amcheck --version
else
    echo "pg_amcheck: NOT INSTALLED"
fi
'

echo
echo "===== POSTGRESQL ERROR LOG SUMMARY ====="
pct exec 310 -- bash -c "
grep -Ei 'FATAL|PANIC|ERROR|corrupt|invalid page|checksum' \
  /var/log/postgresql/postgresql-17-main.log | tail -n 80
"

echo
echo "===== CT310 ROOT FILESYSTEM USAGE ====="
pct exec 310 -- df -h /
```

| Item | Result |
|---|---|
| Roles | 18 retrieved |
| CTID 310 rootfs | 45GB free |
| `pg_amcheck` | not installed (not installed here) |

## 2.5 Sorting Out the Errors in the Log

The log contained duplicate-key errors on `alert_events_pkey` (records of duplicate INSERTs by the Wazuh Collector), errors from diagnostic SQL on `security_workbench`, and `FATAL` messages from connections during startup.

> **Run on: pve**

```bash
echo "===== CT310 POSTGRESQL LOG TIMELINE ====="
pct exec 310 -- bash -c '
echo "--- First log entries ---"
head -n 25 /var/log/postgresql/postgresql-17-main.log

echo
echo "--- Latest log entries ---"
tail -n 35 /var/log/postgresql/postgresql-17-main.log
'

echo
echo "===== CT310 POSTGRESQL START TIME ====="
pct exec 310 -- systemctl show postgresql@17-main \
  -p ActiveState -p ActiveEnterTimestamp -p ExecMainStartTimestamp

echo
echo "===== CT310 SYSTEM BOOT TIME ====="
pct exec 310 -- uptime -s

echo
echo "===== BACKUP ARCHIVE TIMESTAMP ====="
stat -c 'File=%n%nSize=%s bytes%nModified=%y' \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_23-09_43_34.tar.zst

echo
echo "===== CT310 CURRENT STATUS ====="
pct status 310
```

Putting the times in order, these were things already recorded in production before the backup, failed diagnostic queries, or connections made during startup; none of them indicates database corruption.

# Chapter 3: Comparing with Production

CT109 has kept running since the backup, so we do not require the data to be exactly identical. We compare whether the structure is the same.

## 3.1 Database Names and Sizes

> **Run on: pve**

```bash
echo "===== CT109 PRODUCTION STATUS ====="
pct status 109

echo
echo "===== CT310 RESTORE TEST STATUS ====="
pct status 310

echo
echo "===== DATABASE INVENTORY COMPARISON ====="
for CT in 109 310; do
    echo
    echo "===== CT${CT} ====="
    pct exec "$CT" -- runuser -u postgres -- psql -X -d postgres -P pager=off -c "
    SELECT
        d.datname AS database_name,
        pg_database_size(d.datname) AS size_bytes,
        pg_size_pretty(pg_database_size(d.datname)) AS size,
        (
            SELECT count(*)
            FROM information_schema.tables t
            WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
              AND t.table_type = 'BASE TABLE'
              AND t.table_catalog = d.datname
        ) AS base_tables
    FROM pg_database d
    WHERE d.datistemplate = false
    ORDER BY d.datname;
    "
done

echo
echo "===== RESTORE TEST CONTAINER CONFIGURATION ====="
pct config 310 | grep -E '^(hostname|onboot|net[0-9]+|rootfs|unprivileged):'
```

Both CT109 and CT310 have 17 databases, all with the same names. Sizes differ by a few KB to about 1MB, which is considered to be due to updates in production after the backup. CT310 remains `onboot: 0`, `link_down=1`.

## 3.2 Numbers of Tables and Views

`information_schema.tables` only sees the database you are connected to, so we connect to each database and count.

> **Run on: pve**

```bash
for CT in 109 310; do
    echo
    echo "===== CT${CT}: PER-DATABASE OBJECT COUNTS ====="

    pct exec "$CT" -- bash -c '
    DB_LIST=$(runuser -u postgres -- psql -X -At -d postgres \
        -c "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname")

    while IFS= read -r DB; do
        [ -n "$DB" ] || continue

        runuser -u postgres -- psql -X -At -F "|" -d "$DB" -c "
        SELECT
            current_database(),
            count(*) FILTER (WHERE c.relkind IN (chr(114), chr(112))),
            count(*) FILTER (WHERE c.relkind = chr(118)),
            count(*) FILTER (WHERE c.relkind = chr(109))
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE left(n.nspname, 3) <> chr(112)||chr(103)||chr(95)
          AND n.nspname <> chr(105)||chr(110)||chr(102)||chr(111)||chr(114)||chr(109)||chr(97)||chr(116)||chr(105)||chr(111)||chr(110)||chr(95)||chr(115)||chr(99)||chr(104)||chr(101)||chr(109)||chr(97)
          AND c.relkind IN (chr(114), chr(112), chr(118), chr(109));
        " 2>&1
    done <<< "$DB_LIST"
    '
done
```

The output is `database|tables|views|materialized views`. **For all 17 databases, the counts in CT109 and CT310 were the same** (266 tables in total, 1 view, 0 materialized views).

| Database | Tables (CT109) | Tables (CT310) |
|---|---|---|
| agent_db | 18 | 18 |
| agent_memory | 31 (1 view) | 31 (1 view) |
| aipmo | 23 | 23 |
| easywrider | 29 | 29 |
| movie | 22 | 22 |
| novel | 22 | 22 |
| orchivio | 55 | 55 |
| winfilemgr | 8 | 8 |
| writers | 12 | 12 |

The other eight databases are also the same.

## 3.3 Indexes, Constraints and Extensions

> **Run on: pve**

```bash
for CT in 109 310; do
    echo
    echo "========================================"
    echo " CT${CT}: INDEX / CONSTRAINT / EXTENSION"
    echo "========================================"

    pct exec "$CT" -- bash -c '
    DB_LIST=$(runuser -u postgres -- psql -X -At -d postgres \
        -c "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname")

    while IFS= read -r DB; do
        [ -n "$DB" ] || continue

        echo
        echo "--- DATABASE: $DB ---"

        echo "[INDEXES]"
        runuser -u postgres -- psql -X -At -F "|" -d "$DB" -c "
        SELECT
            count(*),
            count(*) FILTER (WHERE NOT i.indisvalid),
            count(*) FILTER (WHERE NOT i.indisready)
        FROM pg_index i
        JOIN pg_class ic ON ic.oid = i.indexrelid
        JOIN pg_namespace n ON n.oid = ic.relnamespace
        WHERE left(n.nspname, 3) <> chr(112)||chr(103)||chr(95)
          AND n.nspname <> chr(105)||chr(110)||chr(102)||chr(111)||chr(114)||chr(109)||chr(97)||chr(116)||chr(105)||chr(111)||chr(110)||chr(95)||chr(115)||chr(99)||chr(104)||chr(101)||chr(109)||chr(97);
        "

        echo "[CONSTRAINTS: PRIMARY / FOREIGN / UNIQUE / CHECK / EXCLUSION]"
        runuser -u postgres -- psql -X -At -F "|" -d "$DB" -c "
        SELECT
            count(*) FILTER (WHERE contype = chr(112)),
            count(*) FILTER (WHERE contype = chr(102)),
            count(*) FILTER (WHERE contype = chr(117)),
            count(*) FILTER (WHERE contype = chr(99)),
            count(*) FILTER (WHERE contype = chr(120))
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE left(n.nspname, 3) <> chr(112)||chr(103)||chr(95)
          AND n.nspname <> chr(105)||chr(110)||chr(102)||chr(111)||chr(114)||chr(109)||chr(97)||chr(116)||chr(105)||chr(111)||chr(110)||chr(95)||chr(115)||chr(99)||chr(104)||chr(101)||chr(109)||chr(97);
        "

        echo "[EXTENSIONS]"
        runuser -u postgres -- psql -X -At -F "|" -d "$DB" -c "
        SELECT extname, extversion
        FROM pg_extension
        ORDER BY extname;
        "
    done <<< "$DB_LIST"
    '
done
```

The total of 534 indexes (0 invalid or not ready), the numbers of primary keys, foreign keys, unique constraints and CHECK constraints, and the names and versions of the extensions (`vector 0.8.7` in 3, `plpgsql 1.0` in 17) were all the same.

## 3.4 Schema Definitions

Beyond counts, we compare table definitions, columns, data types, and index and constraint definitions. We take the SHA256 of the output of `pg_dump --schema-only`. The data itself is not output.

> **Run on: pve**

```bash
for DB in agent_db agent_memory aiagent aipmo cerebrum easywrider movie nfaipmo novel orchivio postgres security_workbench tester vector_db winfilemgr writer writers; do
    echo
    echo "===== DATABASE: $DB ====="

    for CT in 109 310; do
        echo -n "CT${CT}: "

        pct exec "$CT" -- runuser -u postgres -- \
            pg_dump --schema-only --dbname="$DB" 2>/dev/null |
            sed '/^\\restrict /d; /^\\unrestrict /d' |
            sha256sum
    done
done
```

For 16 of the 17, the SHA256 of CT109 and CT310 matched. Only `novel` differed.

## 3.5 The Difference in `novel`

> **Run on: pve**

```bash
echo "===== NOVEL SCHEMA DIFFERENCE CHECK ====="

WORKDIR="$(mktemp -d /var/tmp/novel-schema-diff.XXXXXX)"
echo "WORKDIR=$WORKDIR"

echo
echo "===== EXPORT CT109 ====="
pct exec 109 -- runuser -u postgres -- \
  pg_dump --schema-only --dbname=novel \
  > "$WORKDIR/ct109.raw.sql" \
  2> "$WORKDIR/ct109.stderr"
echo "CT109_PG_DUMP_EXIT=$?"

echo
echo "===== EXPORT CT310 ====="
pct exec 310 -- runuser -u postgres -- \
  pg_dump --schema-only --dbname=novel \
  > "$WORKDIR/ct310.raw.sql" \
  2> "$WORKDIR/ct310.stderr"
echo "CT310_PG_DUMP_EXIT=$?"

echo
echo "===== NORMALIZE DUMP HEADERS ====="
sed '/^\\restrict /d; /^\\unrestrict /d' \
  "$WORKDIR/ct109.raw.sql" > "$WORKDIR/ct109.sql"
sed '/^\\restrict /d; /^\\unrestrict /d' \
  "$WORKDIR/ct310.raw.sql" > "$WORKDIR/ct310.sql"

echo
echo "===== DUMP SIZES ====="
wc -c "$WORKDIR/ct109.sql" "$WORKDIR/ct310.sql"

echo
echo "===== STDERR ====="
cat "$WORKDIR/ct109.stderr"
cat "$WORKDIR/ct310.stderr"

echo
echo "===== SCHEMA DIFF ====="
diff -u "$WORKDIR/ct109.sql" "$WORKDIR/ct310.sql" | head -240
echo "DIFF_EXIT=${PIPESTATUS[0]}"

echo
echo "===== TEMPORARY FILES ====="
echo "$WORKDIR"
```

There were two columns present in CT109 but not in CT310 (`ollama_api_key` and `controller_ollama_api_key`, `character varying(500)`). Without touching the column values (API keys), we check which table they belong to.

> **Run on: pve**

```bash
for CT in 109 310; do
    echo
    echo "===== CT${CT}: NOVEL TARGET COLUMN DEFINITIONS ====="

    pct exec "$CT" -- runuser -u postgres -- psql -X -d novel -P pager=off -c "
SELECT
    n.nspname AS schema_name,
    c.relname AS table_name,
    a.attname AS column_name,
    format_type(a.atttypid, a.atttypmod) AS data_type,
    a.attnotnull AS not_null,
    (d.adbin IS NOT NULL) AS has_default,
    a.attidentity AS identity_type,
    a.attgenerated AS generated_type
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_attrdef d
    ON d.adrelid = a.attrelid
   AND d.adnum = a.attnum
WHERE a.attnum > 0
  AND NOT a.attisdropped
  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
  AND a.attname IN (
      'translator_pool',
      'ollama_api_key',
      'controller_ollama_api_key'
  )
ORDER BY n.nspname, c.relname, a.attnum;
"
done
```

| Column | CT109 | CT310 |
|---|---|---|
| `translator_pool` | present | present |
| `ollama_api_key` | present | absent |
| `controller_ollama_api_key` | present | absent |

The table is `novel.public.runtime_config`. These two columns are a difference caused by schema changes in an application under development (in the build records they were treated as "under development"). This is neither a fault nor backup corruption, so it is not something to fix.

# Closing Notes

In Part 44 we checked the backup system and compared the restored databases with production.

| Checked | Result |
|---|---|
| Backup catalog | two generations of LXC 109 registered |
| Job and boot dependencies | `tmpdir: /var/tmp` and the service that waits for TrueNAS are in place |
| Isolation of CTID 310 | `link_down=1`, `onboot=0`, `eth0` `DOWN` |
| PostgreSQL 17.11 | starts; all 17 databases can be connected to |
| Numbers of tables and views | the same for all 17 |
| Indexes, constraints, extensions | all the same; 0 invalid indexes |
| Schema definitions | 16 identical; the difference in `novel` is a development change |

With this, the backup system built in Volume 3 is as follows.

| Time | Job | Destination |
|---|---|---|
| Daily 02:00 | PostgreSQL logical backup (17 databases and global objects) | TrueNAS NFS `postgresql/` (7 daily, 4 weekly, 3 monthly) |
| Daily 03:00 | Proxmox backup of LXC 109 (temporary directory `/var/tmp`) | TrueNAS NFS `dump/` (7 daily, 4 weekly, 3 monthly) |
| Daily 04:00, Sunday 04:10, 1st 04:20 | TrueNAS ZFS snapshots | `backup` dataset (7 days, 4 weeks, 3 months) |
| At boot | mount after waiting for TrueNAS VM 100 and NFSv3 to respond | `/mnt/pve/backup` |

CTID 310 is still running with its network cut off. When you are done with it, stop it with the procedure in 5.5 of Part 41. We have not checked whether the data in every table is the same, nor connections from the applications.

This is the end of Volume 3. Volume 4 moves on to finishing the LLM side of the AI Defense Manager (repairing Wazuh rules, the form of the input passed to the LLM, a static IP for VM 230, checking the output, API token authentication, detecting log tampering) and to building AI defense agents.

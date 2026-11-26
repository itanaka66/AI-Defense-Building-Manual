---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 41: Backing Up LXC 109 and Testing an Isolated Restore"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 41 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". In Part 40 we made the PostgreSQL logical backup run daily at 02:00. Here we finish the other backup, the **Proxmox backup of the whole of LXC 109**, and test whether it can actually be restored.

1. Back up LXC 109 to TrueNAS's NFS (`truenas-backup`) for the first time and check the archive
2. Enable the daily 03:00 job `lxc109-daily`
3. Investigate, read-only, the thin pool warning shown during the backup
4. Restore the backup to an LXC with a different number (CTID 310) **with its network cut off**
5. Confirm that the restored PostgreSQL starts and that the 17 databases, extensions and role permissions are back

The production LXC 109 is neither stopped nor changed.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)

# Chapter 1: Backing Up LXC 109 for the First Time

## 1.1 Checks Before Running

> **Run on: pve**

```bash
echo "===== NFS MOUNT ====="
findmnt -T /mnt/pve/backup

echo
echo "===== PROXMOX STORAGE ====="
pvesm status --storage truenas-backup

echo
echo "===== LXC 109 STATUS ====="
pct status 109

echo
echo "===== LXC 109 CONFIGURATION ====="
pct config 109

echo
echo "===== BACKUP JOB STATE ====="
pvesh get /cluster/backup --output-format json
```

| Checked | Result |
|---|---|
| TrueNAS NFS mount | normal |
| Storage `truenas-backup` | `active`, about 1.9TB free |
| LXC 109 | `running` |
| Target | rootfs of LXC 109 (50GB) |
| Mode, compression | snapshot, zstd |
| Generations | 7 daily, 4 weekly, 3 monthly |
| Daily 03:00 job | `disabled` |

`pvesm status` prints an error about the `windows_d/windows_d` VG partway through; this is a separate, pre-existing problem, and `truenas-backup` is `active`. We do not touch it here.

## 1.2 Running the Backup

Run it once in snapshot mode without stopping the LXC.

> **Run on: pve**

```bash
echo "===== START LXC 109 FIRST BACKUP ====="
vzdump 109 \
  --storage truenas-backup \
  --mode snapshot \
  --compress zstd

BACKUP_EXIT=$?
echo
echo "===== BACKUP EXIT CODE ====="
echo "BACKUP_EXIT=$BACKUP_EXIT"

echo
echo "===== BACKUP FILES ====="
ls -lh /mnt/pve/backup/dump/ | tail -20
```

| Item | Result |
|---|---|
| Finished | November 22, 2026, 20:29 |
| Source data | about 1.7GiB |
| Saved file | about 473MiB (`vzdump-lxc-109-2026_11_22-20_28_42.tar.zst`) |
| Duration | 31 seconds |
| Exit code | `0` |
| Temporary snapshot | removed correctly |

The log showed thin pool warnings (no protection by automatic extension; the total size of the virtual volumes exceeds the real capacity). This is not a backup failure. We look into it in Chapter 3.

## 1.3 Checking the Archive

> **Run on: pve**

```bash
BACKUP="/mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst"

echo "===== ARCHIVE EXISTENCE ====="
stat "$BACKUP"

echo
echo "===== ZSTD INTEGRITY TEST ====="
zstd -t "$BACKUP"
echo "ZSTD_TEST_EXIT=$?"

echo
echo "===== ARCHIVE CONTENTS ====="
tar --use-compress-program=unzstd -tf "$BACKUP" | head -30
echo "TAR_LIST_EXIT=${PIPESTATUS[0]}"

echo
echo "===== LXC 109 STATUS ====="
pct status 109

echo
echo "===== PROXMOX BACKUP JOB STATE ====="
pvesh get /cluster/backup --output-format json

echo
echo "===== POSTGRESQL TIMER STATE ====="
systemctl is-enabled pg-logical-backup.timer
systemctl is-active pg-logical-backup.timer
```

| Checked | Result |
|---|---|
| File | present, 495,241,299 bytes, `root:root` |
| zstd integrity | `ZSTD_TEST_EXIT=0` |
| Listing inside the archive | readable |
| LXC 109 | `running` |
| PostgreSQL timer | `enabled`, `active` |

`TAR_LIST_EXIT=141` is shown, but this is because `head -30` closed the pipe after reading 30 lines and `tar` received SIGPIPE; the archive is not broken.

# Chapter 2: Enabling the Daily 03:00 Job

Set only `enabled` of the registered job `lxc109-daily` to `1`. Nothing else is changed.

> **Run on: pve**

```bash
echo "===== ENABLE LXC 109 BACKUP JOB ====="
pvesh set /cluster/backup/lxc109-daily --enabled 1
echo "ENABLE_EXIT=$?"

echo
echo "===== VERIFY BACKUP JOB ====="
pvesh get /cluster/backup --output-format json

echo
echo "===== VERIFY NEXT RUN ====="
systemd-analyze calendar '*-*-* 03:00:00'

echo
echo "===== VERIFY STORAGE ====="
pvesm status --storage truenas-backup
```

With `ENABLE_EXIT=0`, the job is enabled. Both backups are now automatic.

| Time | Backup | Target |
|---|---|---|
| Daily 02:00 | PostgreSQL logical backup (systemd timer) | the 17 databases in LXC 109 |
| Daily 03:00 | Proxmox backup (`lxc109-daily`, snapshot, zstd) | LXC 109 |

# Chapter 3: Investigating the Thin Pool

If the thin pool fills up, disk reads and writes of several VMs and LXCs are affected. Here we change no settings and only read the current state.

## 3.1 Usage and Automatic Extension Settings

> **Run on: pve**

```bash
echo "===== PHYSICAL VOLUMES ====="
pvs -o pv_name,vg_name,pv_size,pv_free

echo
echo "===== VOLUME GROUP ====="
vgs -o vg_name,vg_size,vg_free,pv_count,lv_count pve

echo
echo "===== THIN POOL AND LOGICAL VOLUMES ====="
lvs -a -o vg_name,lv_name,lv_attr,lv_size,data_percent,metadata_percent,segtype,devices pve

echo
echo "===== THIN POOL AUTOEXTEND CONFIGURATION ====="
lvmconfig --type current activation/thin_pool_autoextend_threshold
lvmconfig --type current activation/thin_pool_autoextend_percent

echo
echo "===== LVM CONFIGURATION FILE ====="
grep -n -E 'thin_pool_autoextend_threshold|thin_pool_autoextend_percent|thin_pool_autoextend' /etc/lvm/lvm.conf

echo
echo "===== LVM MONITOR SERVICE ====="
systemctl is-enabled lvm2-monitor.service
systemctl is-active lvm2-monitor.service

echo
echo "===== DEVICE MAPPER STATUS ====="
dmsetup status
```

Data usage of thin pool `pve/data` is **61.69%** and metadata usage is **2.18%**, so capacity will not run out immediately. There was no automatic-extension setting, and VG `pve` had 16GiB free.

## 3.2 Is There Capacity to Add?

> **Run on: pve**

```bash
echo "===== NVME DISK LAYOUT ====="
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS /dev/nvme0n1

echo
echo "===== PARTITION FREE SPACE ====="
parted -s /dev/nvme0n1 unit GiB print free

echo
echo "===== PVE PHYSICAL VOLUME ====="
pvs --units g -o pv_name,pv_size,pv_free,pv_pe_count,pv_pe_alloc_count /dev/nvme0n1p3

echo
echo "===== PVE THIN POOL ====="
lvs --units g -o lv_name,lv_size,data_percent,metadata_percent,seg_monitor,lv_attr pve/data

echo
echo "===== LVM DEFAULT AUTOEXTEND VALUES ====="
lvmconfig --type default activation/thin_pool_autoextend_threshold
lvmconfig --type default activation/thin_pool_autoextend_percent

echo
echo "===== LVM MONITOR PROCESS ====="
pgrep -a dmeventd
```

```bash
echo "===== ALL PHYSICAL DISKS ====="
lsblk -d -o NAME,SIZE,MODEL,SERIAL,TYPE

echo
echo "===== ALL PARTITIONS ====="
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS

echo
echo "===== ALL VOLUME GROUPS ====="
vgs -o vg_name,vg_size,vg_free,pv_count,lv_count

echo
echo "===== ALL PHYSICAL VOLUMES ====="
pvs -o pv_name,vg_name,pv_size,pv_free

echo
echo "===== PVE THIN POOL DETAILS ====="
lvs -a -o vg_name,lv_name,lv_size,data_percent,metadata_percent,seg_monitor,lv_attr pve
```

The third NVMe partition runs to the end of the disk, and there is no unallocated space. The other physical disks were each already assigned to other VGs.

Extending the 794GiB thin pool by just 5% needs about 39.7GiB, so with only 16GiB free we do not set up automatic extension. We also do not borrow disks from other VGs or shrink existing storage. We will set it up when the PVE disk is enlarged in the future (it is listed as a check item in the operations manual).

# Chapter 4: Restoring to CTID 310

## 4.1 Checks Before Restoring

> **Run on: pve**

```bash
echo "===== TEST CTID 310 AVAILABILITY ====="
pct status 310
qm status 310

echo
echo "===== LOCAL-LVM STORAGE ====="
pvesm status --storage local-lvm

echo
echo "===== RESTORE COMMAND OPTIONS ====="
pct help restore

echo
echo "===== BACKUP ARCHIVE CONFIGURATION ====="
tar --use-compress-program=unzstd -xOf \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst \
  ./etc/vzdump/pct.conf

echo
echo "===== BACKUP ARCHIVE SIZE ====="
du -h /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst
```

| Checked | Result |
|---|---|
| CTID 310 | not in use |
| `local-lvm` | `active`, about 304GiB free |
| Backup | 473MiB |
| Settings inside the backup | Debian, 2 CPUs, 4GiB, rootfs 50GiB, unprivileged |
| Original IP address | `192.168.0.151` |

The backup contains the original IP address. If it were connected to the network as is, its IP address would clash with the production LXC 109. So we restore it with the network cut off and without automatic start.

## 4.2 Restoring

> **Run on: pve**

```bash
echo "===== RESTORE LXC 109 TO TEST CTID 310 ====="
pct restore 310 \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst \
  --storage local-lvm \
  --net0 name=eth0,bridge=vmbr0,link_down=1,ip=manual,ip6=manual \
  --onboot 0 \
  --start 0 \
  --unique 1

RESTORE_EXIT=$?
echo
echo "RESTORE_EXIT=$RESTORE_EXIT"

if [ "$RESTORE_EXIT" -eq 0 ]; then
  echo
  echo "===== RESTORED CONTAINER CONFIGURATION ====="
  pct config 310

  echo
  echo "===== RESTORED CONTAINER STATUS ====="
  pct status 310
fi
```

With `RESTORE_EXIT=0`, the rootfs of CTID 310 (50GiB) was created and about 1.7GiB of data was extracted. The container remains stopped.

However, the restored configuration **kept the settings from the backup (the same IP address as production)**, not the settings given with `--net0` (the same behavior as in Part 37). It has not been started yet, so no IP address clash has occurred.

## 4.3 Cutting Off the Network

Before starting it, explicitly cut off `net0` of CTID 310.

> **Run on: pve**

```bash
echo "===== DISABLE TEST CONTAINER NETWORK ====="
pct set 310 --net0 name=eth0,bridge=vmbr0,link_down=1,ip=manual,ip6=manual

echo
echo "===== VERIFY NETWORK CONFIGURATION ====="
pct config 310 | grep -E '^(net[0-9]+|onboot|rootfs):'

echo
echo "===== VERIFY CONTAINER IS STOPPED ====="
pct status 310
```

| Item | State |
|---|---|
| `link_down` | `1` (virtual NIC disconnected) |
| IP address | `ip=manual`, `ip6=manual` (no production IP address) |
| `onboot` | `0` |
| State | `stopped` |

# Chapter 5: Checking the Restored PostgreSQL

## 5.1 Starting It

Start only CTID 310, with its network still cut off.

> **Run on: pve**

```bash
echo "===== START ISOLATED TEST CONTAINER 310 ====="
pct start 310
START_EXIT=$?
echo "START_EXIT=$START_EXIT"

if [ "$START_EXIT" -eq 0 ]; then
  echo
  echo "===== CONTAINER STATUS ====="
  pct status 310

  echo
  echo "===== NETWORK CONFIGURATION ====="
  pct config 310 | grep -E '^(net[0-9]+|onboot):'

  echo
  echo "===== POSTGRESQL CLUSTER STATUS ====="
  pct exec 310 -- pg_lsclusters

  echo
  echo "===== POSTGRESQL SERVICE STATUS ====="
  pct exec 310 -- systemctl is-active postgresql
  echo "SERVICE_STATUS_EXIT=$?"

  echo
  echo "===== POSTGRESQL VERSION ====="
  pct exec 310 -- runuser -u postgres -- psql -Atqc "SELECT version();"

  echo
  echo "===== RESTORED DATABASE LIST ====="
  pct exec 310 -- runuser -u postgres -- psql -Atqc \
    "SELECT datname FROM pg_database WHERE datallowconn AND NOT datistemplate ORDER BY datname;"

  echo
  echo "===== RESTORED EXTENSIONS ====="
  pct exec 310 -- runuser -u postgres -- psql -Atqc \
    "SELECT current_database(), extname, extversion FROM pg_extension ORDER BY current_database(), extname;" \
    --dbname=postgres
fi
```

The start returned `START_EXIT=0`. Right after starting, SQL connections are refused with `the database system is starting up`.

## 5.2 Confirming Startup Has Finished

> **Run on: pve**

```bash
echo "===== POSTGRESQL CLUSTER STATUS ====="
pct exec 310 -- pg_lsclusters

echo
echo "===== POSTGRESQL SERVICE DETAILS ====="
pct exec 310 -- systemctl status postgresql --no-pager -l

echo
echo "===== POSTGRESQL 17 SERVICE DETAILS ====="
pct exec 310 -- systemctl status postgresql@17-main --no-pager -l

echo
echo "===== POSTGRESQL STARTUP LOG ====="
pct exec 310 -- journalctl -u postgresql@17-main -n 80 --no-pager

echo
echo "===== POSTGRESQL SERVER LOG ====="
pct exec 310 -- tail -n 80 /var/log/postgresql/postgresql-17-main.log

echo
echo "===== POSTGRESQL PROCESS ====="
pct exec 310 -- ps -eo pid,ppid,stat,etime,args | grep -E '[p]ostgres|[p]ostmaster'

echo
echo "===== POSTGRESQL READINESS ====="
pct exec 310 -- pg_isready -h /var/run/postgresql -p 5432
```

The end of the log has `database system is ready to accept connections`, and `pg_isready` also returned `accepting connections`. `automatic recovery in progress` in the log is the replay of WAL that had not been completed at backup time; after it, the end of recovery and the start of accepting connections are recorded.

`systemctl is-active postgresql` may show `inactive`, but on Debian the parent service `postgresql.service` is designed to be `active (exited)`, and the actual cluster service is `postgresql@17-main.service`. This is not an error.

## 5.3 Databases and Extensions

> **Run on: pve**

```bash
echo "===== POSTGRESQL VERSION ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -Atqc \
  "SELECT version();"

echo
echo "===== DATABASE INVENTORY ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -P pager=off -c \
  "SELECT datname, pg_size_pretty(pg_database_size(datname)) AS size
   FROM pg_database
   WHERE datallowconn AND NOT datistemplate
   ORDER BY datname;"

echo
echo "===== CONNECTIVITY TEST FOR ALL DATABASES ====="
pct exec 310 -- bash -lc '
while IFS= read -r db; do
  [ -n "$db" ] || continue
  printf "%-24s " "$db"
  runuser -u postgres -- psql -X -d "$db" -Atqc \
    "SELECT current_database() || E'\'' : CONNECTED'\'';" 2>&1
done < <(
  runuser -u postgres -- psql -X -d postgres -Atqc \
    "SELECT datname FROM pg_database WHERE datallowconn AND NOT datistemplate ORDER BY datname"
)
'

echo
echo "===== INSTALLED EXTENSIONS BY DATABASE ====="
pct exec 310 -- bash -lc '
while IFS= read -r db; do
  [ -n "$db" ] || continue
  echo "--- $db ---"
  runuser -u postgres -- psql -X -d "$db" -P pager=off -c \
    "SELECT extname, extversion FROM pg_extension ORDER BY extname;"
done < <(
  runuser -u postgres -- psql -X -d postgres -Atqc \
    "SELECT datname FROM pg_database WHERE datallowconn AND NOT datistemplate ORDER BY datname"
)
'
```

- PostgreSQL 17.11 started and all 17 databases could be connected to
- `vector 0.8.7` in three: `easywrider`, `postgres` and `vector_db`
- `plpgsql 1.0` in the other databases
- Database sizes also match the original records

## 5.4 Roles and Permissions

Password hashes are not displayed.

> **Run on: pve**

```bash
echo "===== ROLE INVENTORY (NO PASSWORD DATA) ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -P pager=off -c \
  "SELECT rolname, rolsuper, rolinherit, rolcreaterole,
          rolcreatedb, rolcanlogin, rolreplication, rolbypassrls
   FROM pg_roles
   ORDER BY rolname;"

echo
echo "===== WAZUH_COLLECTOR ROLE ATTRIBUTES ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -P pager=off -c \
  "SELECT rolname, rolsuper, rolinherit, rolcreaterole,
          rolcreatedb, rolcanlogin, rolreplication, rolbypassrls
   FROM pg_roles
   WHERE rolname = 'wazuh_collector';"

echo
echo "===== WAZUH_COLLECTOR ROLE MEMBERSHIPS ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -P pager=off -c \
  "SELECT parent.rolname AS granted_role
   FROM pg_auth_members m
   JOIN pg_roles parent ON parent.oid = m.roleid
   JOIN pg_roles member ON member.oid = m.member
   WHERE member.rolname = 'wazuh_collector';"

echo
echo "===== WAZUH_COLLECTOR TABLE PRIVILEGES ====="
pct exec 310 -- bash -lc '
while IFS= read -r db; do
  [ -n "$db" ] || continue
  echo "--- $db ---"
  runuser -u postgres -- psql -X -d "$db" -P pager=off -c \
    "SELECT table_schema, table_name, privilege_type
     FROM information_schema.role_table_grants
     WHERE grantee = '\''wazuh_collector'\''
     ORDER BY table_schema, table_name, privilege_type;"
done < <(
  runuser -u postgres -- psql -X -d postgres -Atqc \
    "SELECT datname FROM pg_database WHERE datallowconn AND NOT datistemplate ORDER BY datname"
)
'

echo
echo "===== WAZUH_COLLECTOR DATABASE CONNECT PRIVILEGES ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -P pager=off -c \
  "SELECT datname,
          has_database_privilege('wazuh_collector', datname, 'CONNECT') AS can_connect
   FROM pg_database
   WHERE datallowconn AND NOT datistemplate
   ORDER BY datname;"
```

`wazuh_collector` had `SUPERUSER`, `CREATEDB`, `CREATEROLE`, `REPLICATION` and `INHERIT` all disabled, and was not a member of any role. Its only table permission is `INSERT` on `security_workbench.incident.alert_events`.

`information_schema.role_table_grants` alone does not show permissions via PUBLIC or per-column permissions, so we also check the effective permissions.

> **Run on: pve**

```bash
echo "===== EFFECTIVE TABLE PRIVILEGES ====="
pct exec 310 -- runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
  "SELECT
     has_table_privilege('wazuh_collector', 'incident.alert_events', 'SELECT') AS can_select,
     has_table_privilege('wazuh_collector', 'incident.alert_events', 'INSERT') AS can_insert,
     has_table_privilege('wazuh_collector', 'incident.alert_events', 'UPDATE') AS can_update,
     has_table_privilege('wazuh_collector', 'incident.alert_events', 'DELETE') AS can_delete,
     has_table_privilege('wazuh_collector', 'incident.alert_events', 'TRUNCATE') AS can_truncate,
     has_table_privilege('wazuh_collector', 'incident.alert_events', 'REFERENCES') AS can_references,
     has_table_privilege('wazuh_collector', 'incident.alert_events', 'TRIGGER') AS can_trigger;"

echo
echo "===== EFFECTIVE SCHEMA PRIVILEGES ====="
pct exec 310 -- runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
  "SELECT
     has_schema_privilege('wazuh_collector', 'incident', 'USAGE') AS can_use_schema,
     has_schema_privilege('wazuh_collector', 'incident', 'CREATE') AS can_create_in_schema;"

echo
echo "===== COLUMN-LEVEL PRIVILEGES ====="
pct exec 310 -- runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
  "SELECT table_schema, table_name, column_name, privilege_type
   FROM information_schema.column_privileges
   WHERE grantee = 'wazuh_collector'
   ORDER BY table_schema, table_name, column_name, privilege_type;"

echo
echo "===== EFFECTIVE PRIVILEGES ON ALL TABLES ====="
pct exec 310 -- runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
  "SELECT n.nspname AS schema_name, c.relname AS table_name,
          has_table_privilege('wazuh_collector', c.oid, 'SELECT') AS can_select,
          has_table_privilege('wazuh_collector', c.oid, 'INSERT') AS can_insert,
          has_table_privilege('wazuh_collector', c.oid, 'UPDATE') AS can_update,
          has_table_privilege('wazuh_collector', c.oid, 'DELETE') AS can_delete
   FROM pg_class c
   JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE c.relkind IN ('r','p')
     AND n.nspname NOT IN ('pg_catalog','information_schema')
   ORDER BY n.nspname, c.relname;"
```

| Target | Result |
|---|---|
| INSERT on `incident.alert_events` | allowed |
| SELECT, UPDATE, DELETE | not allowed |
| TRUNCATE, REFERENCES, TRIGGER | not allowed |
| USAGE on schema `incident` | allowed |
| CREATE on schema `incident` | not allowed |
| Per-column permissions | INSERT on the 14 chosen columns only |

A check across all tables also found no permissions other than on `incident.alert_events`. The restored `wazuh_collector` is INSERT-only, as intended.

> **Note:** The role list also includes roles with `SUPERUSER` (`agent_user`, `aiagent` and others), but that is a separate matter from `wazuh_collector` and was not changed in this test.

## 5.5 Stopping CTID 310

The checks are done, so stop CTID 310. It is not deleted; it is kept for restore checks.

> **Run on: pve**

```bash
echo "===== SHUTDOWN RESTORE TEST CONTAINER ====="
pct shutdown 310 --timeout 60
SHUTDOWN_EXIT=$?
echo "SHUTDOWN_EXIT=$SHUTDOWN_EXIT"

echo
echo "===== VERIFY CONTAINER STATUS ====="
pct status 310

echo
echo "===== VERIFY ISOLATION AND AUTOSTART ====="
pct config 310 | grep -E '^(hostname|onboot|net0|rootfs):'

echo
echo "===== VERIFY PRODUCTION CONTAINER 109 ====="
pct status 109
```

CTID 310 stopped and remains `link_down=1`, `onboot=0`. The production CTID 109 stayed `running`.

# Closing Notes

In Part 41 we ran the Proxmox backup of LXC 109 and confirmed that it can be restored into an isolated environment.

| Checked | Result |
|---|---|
| Backup to TrueNAS NFS | passed (473MiB, 31 seconds) |
| zstd integrity of the archive | passed |
| Daily 03:00 job | enabled |
| Thin pool | 61.69% used. No capacity to add, so automatic extension is on hold |
| Restore to CTID 310 | passed (network cut off) |
| PostgreSQL 17.11 startup and automatic recovery | passed |
| Connections to 17 databases | 17/17 passed |
| pgvector 0.8.7 | confirmed in 3 databases |
| Least privilege of `wazuh_collector` | passed |
| Production CTID 109 | kept running |

In the next part, Part 42, we check read permissions on the backup files themselves and set up ZFS snapshots on the TrueNAS destination.

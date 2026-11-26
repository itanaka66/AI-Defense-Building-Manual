---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 42: Protecting the Backups and TrueNAS Snapshots"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 42 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". By Part 41, the PostgreSQL logical backup (daily 02:00) and the Proxmox backup of LXC 109 (daily 03:00) were being saved to TrueNAS's NFS, and the restore test had passed. Here we protect the saved backups themselves.

1. Check whether users other than root can read the backup files, and make the LXC backup directory root-only
2. Check the state of the scheduled backup timer and job
3. Without using the TrueNAS console, inspect datasets and snapshots **from Proxmox through the TrueNAS API**
4. Create daily, weekly and monthly ZFS snapshot tasks for TrueNAS's `backup` dataset

PostgreSQL's `globals.sql` may contain role password hashes, and LXC archives may contain settings and credentials from inside the container. So we limit who can read them to root.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)
- The TrueNAS API commands use `--user root` and ask for TrueNAS's root password each time. Type the password in the terminal; it is not shown on screen. Do not write it in commands, chats or notes.

# Chapter 1: Checking Read Permissions on the Backups

## 1.1 Current Permissions

> **Run on: pve**

```bash
echo "===== BACKUP MOUNT ====="
findmnt -T /mnt/pve/backup

echo
echo "===== BACKUP DIRECTORY PERMISSIONS ====="
namei -l /mnt/pve/backup/postgresql/daily/2026-11-22/globals.sql
namei -l /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst

echo
echo "===== POSTGRESQL BACKUP DIRECTORIES ====="
find /mnt/pve/backup/postgresql -maxdepth 3 -type d \
  -printf '%M %u:%g %p\n' | sort

echo
echo "===== POSTGRESQL BACKUP FILE PERMISSIONS ====="
find /mnt/pve/backup/postgresql -maxdepth 3 -type f \
  -printf '%M %u:%g %s bytes %p\n' | sort

echo
echo "===== LXC 109 BACKUP FILE PERMISSIONS ====="
stat -c '%A %a %U:%G %s bytes %n' \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.log

echo
echo "===== POSTGRESQL BACKUP ACL ====="
if command -v getfacl >/dev/null 2>&1; then
  getfacl -p /mnt/pve/backup/postgresql \
    /mnt/pve/backup/postgresql/daily \
    /mnt/pve/backup/postgresql/daily/2026-11-22 \
    /mnt/pve/backup/postgresql/daily/2026-11-22/globals.sql
else
  echo "getfacl is not installed; POSIX mode was checked above."
fi
```

For the PostgreSQL backups, all directories were `0700`, all files (`.dump`, `globals.sql`, `SHA256SUMS` and so on) were `0600`, and the owner was `root:root`. These need no change.

The LXC 109 archive, on the other hand, was `0644`.

## 1.2 The LXC Backup Directory

> **Run on: pve**

```bash
echo "===== DUMP DIRECTORY PERMISSIONS ====="
namei -l /mnt/pve/backup/dump
stat -c '%A %a %U:%G %n' /mnt/pve/backup/dump

echo
echo "===== LXC 109 BACKUP FILE AND LOG ====="
stat -c '%A %a %U:%G %s bytes %n' \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.log

echo
echo "===== PROXMOX BACKUP JOB ====="
pvesh get /cluster/backup/lxc109-daily --output-format yaml

echo
echo "===== VZDUMP CONFIGURATION ====="
if test -f /etc/vzdump.conf; then
  sed -n '1,160p' /etc/vzdump.conf
else
  echo "/etc/vzdump.conf does not exist"
fi
```

| Target | Permissions | Assessment |
|---|---|---|
| `/mnt/pve/backup/dump/` | `0755` | fix |
| LXC 109 archive | `0644` | fix |
| LXC 109 log | `0644` | fix |
| PostgreSQL backups | `0700`, `0600` | good |

With `dump/` at `0755` and the archive at `0644`, ordinary users on the same host can read the backup.

## 1.3 Making `dump/` Root-Only

Set only the `dump/` directory to `0700`. The owner `root:root`, ownership and ACLs on the TrueNAS side, `/etc/vzdump.conf` and the backup job are not changed. Proxmox backup, restore and generation management, which run as root, keep working.

> **Run on: pve**

```bash
chmod 700 /mnt/pve/backup/dump
```

## 1.4 Checking After the Change

> **Run on: pve**

```bash
echo "===== DUMP DIRECTORY AFTER CHANGE ====="
stat -c '%A %a %U:%G %n' /mnt/pve/backup/dump
namei -l /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst

echo
echo "===== DUMP DIRECTORY ACL ====="
getfacl -p /mnt/pve/backup/dump

echo
echo "===== POSTGRESQL BACKUP PERMISSIONS (UNCHANGED CHECK) ====="
stat -c '%A %a %U:%G %n' \
  /mnt/pve/backup/postgresql \
  /mnt/pve/backup/postgresql/daily \
  /mnt/pve/backup/postgresql/daily/2026-11-22 \
  /mnt/pve/backup/postgresql/daily/2026-11-22/globals.sql

echo
echo "===== NFS MOUNT STILL ACTIVE ====="
findmnt -T /mnt/pve/backup
```

`dump/` became `0700 root:root`, and this was reflected on NFS. The archive file itself is still `0644`, but because its parent directory is `0700`, nobody except root can reach it by the normal path. The PostgreSQL backups remain `0700` and `0600`.

> **Caution:** This `0700` later becomes one of the causes of an LXC backup failure (Part 43). The fix is not to revert `dump/` but to make the job's temporary directory local.

## 1.5 State of the Scheduled Backups

> **Run on: pve**

```bash
echo "===== POSTGRESQL BACKUP TIMER ====="
systemctl status pg-logical-backup.timer --no-pager -l

echo
echo "===== POSTGRESQL BACKUP SERVICE ====="
systemctl status pg-logical-backup.service --no-pager -l

echo
echo "===== POSTGRESQL BACKUP TIMER SCHEDULE ====="
systemctl list-timers --all pg-logical-backup.timer --no-pager

echo
echo "===== POSTGRESQL BACKUP RECENT LOG ====="
journalctl -u pg-logical-backup.service -n 40 --no-pager

echo
echo "===== PROXMOX LXC BACKUP JOB ====="
pvesh get /cluster/backup/lxc109-daily --output-format yaml

echo
echo "===== PROXMOX BACKUP TASKS ====="
pvenode task list --vmid 109 --limit 10
```

| Item | Result |
|---|---|
| `pg-logical-backup.timer` | `enabled`, `active`; next run November 23, 02:00 |
| `pg-logical-backup.service` | last run finished normally (`inactive (dead)` is normal for a oneshot service) |
| `lxc109-daily` | `enabled=1`; next run November 23, 03:00 |
| Generations | 7 daily, 4 weekly, 3 monthly |

# Chapter 2: Using the TrueNAS API from Proxmox

ZFS information inside TrueNAS (VM 100, `192.168.0.254`) is not visible with `zfs list` on Proxmox. Instead of working in the TrueNAS console, we operate from Proxmox. TrueNAS's SSH is not listening (`Connection refused`), so rather than enabling SSH we use the HTTPS management API.

## 2.1 Can We Reach the API?

No credentials are sent; we only check the response.

> **Run on: pve**

```bash
echo "===== TRUENAS HTTPS API V2 ====="
curl -k -sS --connect-timeout 5 --max-time 10 \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/system/version

echo
echo "===== TRUENAS HTTPS API V1 ====="
curl -k -sS --connect-timeout 5 --max-time 10 \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v1.0/system/version

echo
echo "===== TRUENAS HTTPS ROOT ====="
curl -k -sS -o /dev/null \
  --connect-timeout 5 --max-time 10 \
  -w 'HTTP_STATUS=%{http_code} CONNECT=%{time_connect}s TLS=%{time_appconnect}s\n' \
  https://192.168.0.254/
```

API v2.0 returned `HTTP 401` (authentication required) and v1.0 returned `302`. This is not a network problem; authentication is simply required.

## 2.2 Checking Authentication

This only reads version information.

> **Run on: pve**

```bash
echo "===== TRUENAS API AUTHENTICATION TEST ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 10 \
  --user root \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/system/version

echo "===== API TEST COMPLETED ====="
```

It returned `"TrueNAS-12.0-U8.1"` and `HTTP_STATUS=200`. We can now inspect TrueNAS through the API from Proxmox without enabling SSH.

## 2.3 The Backup Dataset

> **Run on: pve**

```bash
echo "===== TRUENAS DATASET API RAW STRUCTURE ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 20 \
  --user root \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/dataset |
jq '
  if type == "array" then
    .[] | {
      name,
      mountpoint,
      encrypted,
      encryption,
      encryptionroot,
      key_loaded,
      compression,
      acltype
    }
  else
    .
  end
'
```

| Item | Result |
|---|---|
| Dataset | `backup` |
| Mount point | `/mnt/backup` |
| Encryption | `false` (not encrypted) |
| Compression | LZ4 |
| ACL type | NFSV4 |

`key_loaded: false` is because the dataset is not encrypted; it does not mean a key has been unloaded. The `parse error` from the final `jq` is because curl's `HTTP_STATUS=` line was appended after the JSON; the dataset information was retrieved.

## 2.4 Finding the Snapshot API

TrueNAS CORE 12.0 does not have the `/pool/snapshot` path used by newer TrueNAS (SCALE and others), and it returns `HTTP 404`. We extract the snapshot-related paths from TrueNAS's own OpenAPI specification.

> **Run on: pve**

```bash
echo "===== TRUENAS SNAPSHOT API PATH INVENTORY ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -o /tmp/truenas-openapi.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0

echo
echo "===== SNAPSHOT-RELATED ENDPOINTS ====="
if jq -e '.paths | type == "object"' /tmp/truenas-openapi.json >/dev/null 2>&1; then
  jq -r '
    .paths
    | to_entries[]
    | select(.key | test("snapshot"; "i"))
    | .key as $path
    | .value
    | to_entries[]
    | select(.key | IN("get","post","put","delete"))
    | [
        $path,
        (.key | ascii_upcase),
        (.value.summary // ""),
        (.value.description // "" | split("\n")[0])
      ]
    | @tsv
  ' /tmp/truenas-openapi.json
else
  echo "OPENAPI_JSON_INVALID"
  head -c 1500 /tmp/truenas-openapi.json
  echo
fi

rm -f /tmp/truenas-openapi.json
```

The snapshot list is **`/api/v2.0/zfs/snapshot`**, and periodic snapshot tasks are **`/api/v2.0/pool/snapshottask`**.

## 2.5 Current Snapshots

> **Run on: pve**

```bash
echo "===== TRUENAS ZFS SNAPSHOT LIST ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -o /tmp/truenas-snapshots.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/zfs/snapshot

echo
echo "===== RESPONSE STRUCTURE ====="
if jq -e 'type == "array"' /tmp/truenas-snapshots.json >/dev/null 2>&1; then
  jq '{
    total_snapshots: length,
    first_entries: .[:3]
  }' /tmp/truenas-snapshots.json

  echo
  echo "===== BACKUP DATASET SNAPSHOTS ====="
  jq '
    [
      .[]
      | select(
          .dataset == "backup"
          or (.name // "" | startswith("backup@"))
          or (.id // "" | startswith("backup@"))
        )
    ]
  ' /tmp/truenas-snapshots.json
else
  echo "RESPONSE IS NOT A JSON ARRAY"
  head -c 2000 /tmp/truenas-snapshots.json
  echo
fi

rm -f /tmp/truenas-snapshots.json
```

There were two snapshots on the whole of TrueNAS: `backup/.system/samba4@…` (for managing Samba inside TrueNAS) and `boot-pool/ROOT/default` (for the boot environment). **There is no snapshot protecting the `backup` dataset itself.**

## 2.6 Current Snapshot Tasks

> **Run on: pve**

```bash
echo "===== TRUENAS PERIODIC SNAPSHOT TASKS ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -o /tmp/truenas-snapshottasks.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask

echo
echo "===== TASK CONFIGURATION ====="
if jq -e 'type == "array"' /tmp/truenas-snapshottasks.json >/dev/null 2>&1; then
  jq '
    map({
      id,
      dataset,
      recursive,
      lifetime_value,
      lifetime_unit,
      naming_schema,
      enabled,
      schedule,
      begin,
      end_time: ."end",
      exclude
    })
  ' /tmp/truenas-snapshottasks.json
else
  echo "UNEXPECTED_RESPONSE"
  head -c 2000 /tmp/truenas-snapshottasks.json
  echo
fi

rm -f /tmp/truenas-snapshottasks.json
```

The result was `[]`, that is, **zero** periodic snapshot tasks.

> **Note:** The task JSON has a field called `end`, which collides with a `jq` keyword. The command above avoids this by writing `."end"`.

In this state, if backup files are deleted by mistake, encrypted or corrupted, there is no way to roll back to an earlier state on the TrueNAS side.

# Chapter 3: Creating Snapshot Tasks

## 3.1 Fields for Creating a Task

> **Run on: pve**

```bash
echo "===== TRUENAS PERIODIC SNAPSHOT POST SCHEMA ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -o /tmp/truenas-openapi.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0

echo
echo "===== POST REQUEST BODY ====="
jq '
  .paths["/pool/snapshottask"].post
  | {
      summary,
      description,
      requestBody,
      responses
    }
' /tmp/truenas-openapi.json

echo
echo "===== REFERENCED SNAPSHOT TASK SCHEMAS ====="
jq '
  .components.schemas
  | with_entries(
      select(.key | test("snapshottask|snapshot_task|periodic"; "i"))
    )
' /tmp/truenas-openapi.json

rm -f /tmp/truenas-openapi.json
```

| Field | Meaning |
|---|---|
| `dataset` | target dataset |
| `recursive` | whether child datasets are included |
| `lifetime_value`, `lifetime_unit` | retention period |
| `naming_schema` | snapshot name format (`%Y %m %d %H %M` are required) |
| `schedule` | minute, hour, day, month, weekday |
| `enabled` | enabled or disabled |

## 3.2 Dataset Hierarchy

With `recursive` enabled, child datasets are included too. To avoid widening the scope too much, we check the hierarchy.

> **Run on: pve**

```bash
echo "===== TRUENAS BACKUP DATASET HIERARCHY ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -o /tmp/truenas-datasets.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/dataset

echo
echo "===== BACKUP DATASET AND CHILD DATASETS ====="
if jq -e 'type == "array"' /tmp/truenas-datasets.json >/dev/null 2>&1; then
  jq '
    [
      .[]
      | select(
          .name == "backup"
          or (.name | startswith("backup/"))
        )
      | {
          name,
          mountpoint,
          type,
          encrypted,
          used,
          available,
          acltype
        }
    ]
    | sort_by(.name)
  ' /tmp/truenas-datasets.json
else
  echo "UNEXPECTED_RESPONSE"
  head -c 2000 /tmp/truenas-datasets.json
  echo
fi

rm -f /tmp/truenas-datasets.json
```

`backup` has no child datasets; it is a single file system. So we use **`backup` only, with `recursive=false`**.

## 3.3 The Chosen Schedule

The backups run at 02:00 (PostgreSQL) and 03:00 (LXC 109), so snapshots are taken after them.

| Type | Runs | Retention | Name |
|---|---|---|---|
| Daily | every day 04:00 | 7 days | `daily-%Y-%m-%d_%H-%M` |
| Weekly | every Sunday 04:10 | 4 weeks | `weekly-%Y-%m-%d_%H-%M` |
| Monthly | the 1st of each month 04:20 | 3 months | `monthly-%Y-%m-%d_%H-%M` |

TrueNAS retention and the backup generation management on the Proxmox side work independently. Note that snapshots on the same pool are not an independent backup against disk failure or loss of the TrueNAS machine itself.

## 3.4 Creating the Daily Task

The following command registers all three tasks (daily, weekly, monthly) at once.

> **Run on: pve**

```bash
echo "===== CREATE DAILY SNAPSHOT TASK ====="
curl -k -sS \
  --connect-timeout 5 --max-time 30 \
  --user root \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "dataset": "backup",
    "recursive": false,
    "exclude": [],
    "lifetime_value": 7,
    "lifetime_unit": "DAY",
    "naming_schema": "daily-%Y-%m-%d_%H-%M",
    "schedule": {
      "minute": "0",
      "hour": "4",
      "dom": "*",
      "month": "*",
      "dow": "*",
      "begin": "00:00",
      "end": "23:59"
    },
    "allow_empty": false,
    "enabled": true
  }' \
  -o /tmp/truenas-task-daily.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask
cat /tmp/truenas-task-daily.json

echo
echo "===== CREATE WEEKLY SNAPSHOT TASK ====="
curl -k -sS \
  --connect-timeout 5 --max-time 30 \
  --user root \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "dataset": "backup",
    "recursive": false,
    "exclude": [],
    "lifetime_value": 4,
    "lifetime_unit": "WEEK",
    "naming_schema": "weekly-%Y-%m-%d_%H-%M",
    "schedule": {
      "minute": "10",
      "hour": "4",
      "dom": "*",
      "month": "*",
      "dow": "0",
      "begin": "00:00",
      "end": "23:59"
    },
    "allow_empty": false,
    "enabled": true
  }' \
  -o /tmp/truenas-task-weekly.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask
cat /tmp/truenas-task-weekly.json

echo
echo "===== CREATE MONTHLY SNAPSHOT TASK ====="
curl -k -sS \
  --connect-timeout 5 --max-time 30 \
  --user root \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "dataset": "backup",
    "recursive": false,
    "exclude": [],
    "lifetime_value": 3,
    "lifetime_unit": "MONTH",
    "naming_schema": "monthly-%Y-%m-%d_%H-%M",
    "schedule": {
      "minute": "20",
      "hour": "4",
      "dom": "1",
      "month": "*",
      "dow": "*",
      "begin": "00:00",
      "end": "23:59"
    },
    "allow_empty": false,
    "enabled": true
  }' \
  -o /tmp/truenas-task-monthly.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask
cat /tmp/truenas-task-monthly.json

echo
echo "===== VERIFY REGISTERED TASKS ====="
curl -k -sS \
  --connect-timeout 5 --max-time 30 \
  --user root \
  -o /tmp/truenas-task-list.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask

if jq -e 'type == "array"' /tmp/truenas-task-list.json >/dev/null 2>&1; then
  jq '
    map({
      id,
      dataset,
      recursive,
      lifetime_value,
      lifetime_unit,
      naming_schema,
      schedule,
      enabled,
      allow_empty
    })
  ' /tmp/truenas-task-list.json
else
  echo "TASK_LIST_RESPONSE_INVALID"
  head -c 2000 /tmp/truenas-task-list.json
  echo
fi

rm -f /tmp/truenas-task-daily.json \
      /tmp/truenas-task-weekly.json \
      /tmp/truenas-task-monthly.json \
      /tmp/truenas-task-list.json
```

The daily task was created with ID `1` (daily 04:00, 7 days, `enabled: true`, state `PENDING`).

> **Caution:** This command runs curl three times in a row and asks for the password each time. In the build records, the input got mixed up when everything was pasted at once: two daily tasks (IDs `1` and `2`) were created, the weekly and monthly ones were not, and the shell was left waiting for more input (`>`). In that case, stop with Ctrl+C, delete the duplicate, and then create the weekly and monthly tasks one at a time. The following command deletes only the periodic task setting (ID `2`); it does not delete any snapshots.
>
> **Run on: pve**

```bash
echo "===== DELETE DUPLICATE SNAPSHOT TASK ID 2 ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -X DELETE \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask/id/2

echo
echo "===== VERIFY REMAINING SNAPSHOT TASKS ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  https://192.168.0.254/api/v2.0/pool/snapshottask |
jq -r '.[] | [
  "ID=\(.id)",
  "NAME=\(.naming_schema)",
  "HOUR=\(.schedule.hour)",
  "MINUTE=\(.schedule.minute)",
  "ENABLED=\(.enabled)"
] | join(" ")'
```

## 3.5 Creating the Weekly Task

> **Run on: pve**

```bash
echo "===== CREATE WEEKLY SNAPSHOT TASK ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -X POST \
  -H 'Content-Type: application/json' \
  --data-binary '{"dataset":"backup","recursive":false,"exclude":[],"lifetime_value":4,"lifetime_unit":"WEEK","naming_schema":"weekly-%Y-%m-%d_%H-%M","schedule":{"minute":"10","hour":"4","dom":"*","month":"*","dow":"0","begin":"00:00","end":"23:59"},"allow_empty":false,"enabled":true}' \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask
```

It was created with ID `3` (every Sunday 04:10, 4 weeks, `recursive: false`, `PENDING`).

## 3.6 Creating the Monthly Task

> **Run on: pve**

```bash
echo "===== CREATE MONTHLY SNAPSHOT TASK ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -X POST \
  -H 'Content-Type: application/json' \
  --data-binary '{"dataset":"backup","recursive":false,"exclude":[],"lifetime_value":3,"lifetime_unit":"MONTH","naming_schema":"monthly-%Y-%m-%d_%H-%M","schedule":{"minute":"20","hour":"4","dom":"1","month":"*","dow":"*","begin":"00:00","end":"23:59"},"allow_empty":false,"enabled":true}' \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask
```

It was created with ID `4` (the 1st of each month 04:20, 3 months, `recursive: false`, `PENDING`).

## 3.7 Checking Everything

> **Run on: pve**

```bash
echo "===== VERIFY ALL TRUENAS SNAPSHOT TASKS ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -o /tmp/truenas-snapshottasks-final.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask

echo
echo "===== TASK CONFIGURATION ====="
jq -r '.[] | [
  "ID=\(.id)",
  "DATASET=\(.dataset)",
  "NAME=\(.naming_schema)",
  "SCHEDULE=\(.schedule.dow) DOM=\(.schedule.dom) \(.schedule.hour):\(.schedule.minute)",
  "RETENTION=\(.lifetime_value) \(.lifetime_unit)",
  "RECURSIVE=\(.recursive)",
  "ENABLED=\(.enabled)",
  "STATE=\(.state.state)"
] | join(" | ")' /tmp/truenas-snapshottasks-final.json

echo
echo "===== TASK COUNT ====="
jq 'length' /tmp/truenas-snapshottasks-final.json
```

| Type | Runs | Retention | ID |
|---|---|---|---|
| Daily | every day 04:00 | 7 days | 1 |
| Weekly | every Sunday 04:10 | 4 weeks | 3 |
| Monthly | the 1st of each month 04:20 | 3 months | 4 |

`HTTP 200`, three tasks registered with no duplicates. All are `dataset: backup`, `recursive: false`, `enabled: true`, do not create empty snapshots (`allow_empty: false`), and have state `PENDING`.

# Chapter 4: Checks Before the First Run

## 4.1 Backups and Destination

> **Run on: pve**

```bash
echo "===== 1. NFS MOUNT ====="
findmnt -T /mnt/pve/backup -o TARGET,SOURCE,FSTYPE,OPTIONS

echo
echo "===== 2. POSTGRESQL BACKUP GENERATIONS ====="
find /mnt/pve/backup/postgresql -maxdepth 2 -type d \
  \( -path '*/daily/*' -o -path '*/weekly/*' -o -path '*/monthly/*' \) \
  -printf '%TY-%Tm-%Td %TH:%TM %p\n' 2>/dev/null | sort

echo
echo "===== POSTGRESQL CHECKSUM VERIFICATION ====="
for f in /mnt/pve/backup/postgresql/daily/*/SHA256SUMS; do
  if [ -f "$f" ]; then
    echo "--- $f ---"
    (cd "$(dirname "$f")" && sha256sum -c SHA256SUMS)
  fi
done

echo
echo "===== 3. LXC 109 BACKUP FILES ====="
ls -lh /mnt/pve/backup/dump/vzdump-lxc-109-* 2>/dev/null

echo
echo "===== LXC 109 ARCHIVE INTEGRITY ====="
for f in /mnt/pve/backup/dump/vzdump-lxc-109-*.tar.zst; do
  if [ -f "$f" ]; then
    echo "--- $f ---"
    zstd -t "$f"
    echo "ZSTD_EXIT=$?"
  fi
done

echo
echo "===== 4. TRUENAS ZFS SNAPSHOTS ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  https://192.168.0.254/api/v2.0/zfs/snapshot |
jq -r '.[] | [
  "NAME=\(.name)",
  "CREATED=\(.creation // "unknown")",
  "REFER=\(.refer // "unknown")"
] | join(" | ")'
```

The NFS mount is normal; the PostgreSQL backup has all 21 SHA-256 entries `OK`, and the LXC 109 archive gives `0` for `zstd -t`. There are no snapshots of the `backup` dataset yet, which is normal before the first scheduled run.

## 4.2 Timer, Job and Mount

> **Run on: pve**

```bash
echo "===== SYSTEM TIME ====="
date '+%Y-%m-%d %H:%M:%S %Z'

echo
echo "===== POSTGRESQL BACKUP TIMER ====="
systemctl is-enabled pg-logical-backup.timer
systemctl is-active pg-logical-backup.timer
systemctl list-timers pg-logical-backup.timer --all

echo
echo "===== POSTGRESQL BACKUP SERVICE ====="
systemctl show pg-logical-backup.service \
  -p LoadState -p ActiveState -p SubState -p Result -p ExecStart

echo
echo "===== PROXMOX LXC 109 BACKUP JOB ====="
pvesh get /cluster/backup/lxc109-daily --output-format json |
jq '{id,enabled,schedule,storage,vmid,mode,compress,prune-backups,repeat-missed}'

echo
echo "===== NFS MOUNT UNIT ====="
systemctl is-enabled mnt-pve-backup.mount
systemctl is-active mnt-pve-backup.mount
systemctl show mnt-pve-backup.mount \
  -p What -p Where -p Type -p ActiveState -p SubState -p NeedDaemonReload

echo
echo "===== NEXT BACKUP CALENDAR TIMES ====="
systemd-analyze calendar '*-*-* 02:00:00'
systemd-analyze calendar '*-*-* 03:00:00'
```

```bash
echo "===== VERIFY LXC 109 BACKUP JOB ====="
pvesh get /cluster/backup/lxc109-daily --output-format json |
jq '{
  id: .id,
  enabled: .enabled,
  schedule: .schedule,
  storage: .storage,
  vmid: .vmid,
  mode: .mode,
  compress: .compress,
  retention: .["prune-backups"],
  repeat_missed: .["repeat-missed"]
}'
```

| Item | Result |
|---|---|
| PostgreSQL timer | `enabled`, `active`; next run November 23, 02:00 |
| Mount unit | `enabled`, `active`, `mounted` |
| `lxc109-daily` | `enabled: 1`, `*-*-* 03:00:00`, `truenas-backup`, snapshot, zstd, 7 daily, 4 weekly, 3 monthly |

# Closing Notes

In Part 42 we limited who can read the backups to root and made TrueNAS keep generations too.

| Item | Result |
|---|---|
| PostgreSQL backups | `0700`, `0600` (unchanged) |
| LXC backups | set `dump/` to `0700` |
| Operating TrueNAS | HTTPS API from Proxmox (SSH left disabled) |
| Dataset `backup` | not encrypted, LZ4, NFSV4 ACLs, no child datasets |
| Snapshot tasks | daily (ID 1), weekly (ID 3), monthly (ID 4) |
| Not yet done | check the result of the scheduled runs on November 23 |

In the next part, Part 43, we check the scheduled runs on November 23. There we find a failure of the LXC 109 backup and a problem where NFS is not mounted after a Proxmox reboot, and fix each.

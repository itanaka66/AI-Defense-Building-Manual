---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 39: Registering the Destination and Preparing Scheduled Backups"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 39 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". In Part 38 we mounted TrueNAS's NFS share `/mnt/backup` at `/mnt/pve/backup` and confirmed that Proxmox's root can write to it. This part does the following.

1. Make sure NFS is also mounted correctly at boot (fix the systemd mount unit, which still had old settings)
2. Register it with Proxmox as backup-only storage, `truenas-backup`
3. Investigate the VMs and LXCs to back up and their capacity, and decide the method, generations and times for PostgreSQL backups
4. Register a scheduled backup job for LXC 109 **while leaving it disabled**
5. Place a script for logical backups of PostgreSQL

The decisions are as follows.

| Item | Decision |
|---|---|
| Generations | 7 daily, 4 weekly, 3 monthly |
| PostgreSQL logical backup | Daily at 02:00 (Japan time) |
| Proxmox backup of LXC 109 | Daily at 03:00 (Japan time) |

This part goes as far as testing, after placing the script, whether hard links (used for the weekly and monthly generations) can be created on NFS. The first backup run and enabling the job and timer are done in Parts 40 and 41.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)

# Chapter 1: Fixing the Mount Unit

## 1.1 The Current Settings

> **Run on: pve**

```bash
echo "===== PROXMOX STORAGE CONFIGURATION ====="
cat /etc/pve/storage.cfg

echo "===== STORAGE STATUS ====="
pvesm status

echo "===== BACKUP DIRECTORY ====="
findmnt -T /mnt/pve/backup
df -hT /mnt/pve/backup

echo "===== VZDUMP CONFIGURATION ====="
if [ -f /etc/vzdump.conf ]; then
  cat /etc/vzdump.conf
else
  echo "No /etc/vzdump.conf"
fi
```

`/mnt/pve/backup` was mounted over NFS, but it was not yet registered as Proxmox storage. Find out where this mount is managed.

```bash
echo "===== FSTAB NFS ENTRIES ====="
grep -nE 'nfs|/mnt/pve/backup' /etc/fstab || true

echo "===== SYSTEMD MOUNT STATUS ====="
systemctl status mnt-pve-backup.mount --no-pager

echo "===== MOUNT UNIT FILE ====="
systemctl cat mnt-pve-backup.mount

echo "===== PROXMOX NFS STORAGE REFERENCES ====="
grep -RniE '192\.168\.0\.254|/mnt/backup|/mnt/pve/backup' \
  /etc/pve/storage.cfg /etc/fstab /etc/systemd/system 2>/dev/null
```

`/etc/fstab` had nothing, but `/etc/systemd/system/mnt-pve-backup.mount` (`Description=Mount storage 'backup' under /mnt/pve`) existed. **This unit file pointed not to NFS but to a local ext4 disk (UUID `8cab893f-75f0-478d-842b-e94558853d14`).**

## 1.2 Checking the Mismatch

```bash
echo "===== KERNEL MOUNT TABLE ====="
grep -E ' /mnt/pve/backup ' /proc/mounts

echo "===== FINDMNT DETAILS ====="
findmnt -T /mnt/pve/backup -o TARGET,SOURCE,FSTYPE,OPTIONS

echo "===== SYSTEMD MOUNT PROPERTIES ====="
systemctl show mnt-pve-backup.mount \
  -p ActiveState -p SubState -p What -p Where -p Type -p FragmentPath

echo "===== UUID DEVICE CHECK ====="
blkid -U 8cab893f-75f0-478d-842b-e94558853d14

echo "===== BLOCK DEVICE DETAILS ====="
lsblk -o NAME,TYPE,FSTYPE,UUID,SIZE,MOUNTPOINTS
```

The actual mount was `192.168.0.254:/mnt/backup` (NFS), and the settings systemd currently held were also NFS. No disk with that UUID exists.

```bash
echo "===== SYSTEMD UNIT SOURCE ====="
systemctl show mnt-pve-backup.mount \
  -p FragmentPath -p SourcePath -p DropInPaths \
  -p What -p Where -p Type -p NeedDaemonReload

echo "===== UNIT FILE AND LINKS ====="
ls -l /etc/systemd/system/mnt-pve-backup.mount
ls -l /etc/systemd/system/multi-user.target.wants/mnt-pve-backup.mount

echo "===== UNIT FILE CONTENT WITH LINE NUMBERS ====="
nl -ba /etc/systemd/system/mnt-pve-backup.mount

echo "===== SYSTEMD UNIT OVERRIDES ====="
find /etc/systemd/system/mnt-pve-backup.mount.d \
  -maxdepth 2 -type f -print 2>/dev/null

echo "===== MOUNT UNIT REFERENCES ====="
grep -RniE 'mnt-pve-backup|192\.168\.0\.254:/mnt/backup' \
  /etc/systemd /run/systemd/generator /run/systemd/transient \
  /etc/pve 2>/dev/null
```

The file had not changed since May 24 and still had `Type=ext4` and `What=/dev/disk/by-uuid/8cab893f-…`. There were no overriding settings (drop-ins) either.

```bash
echo "===== SYSTEMD UNIT STATUS ====="
systemctl status mnt-pve-backup.mount --no-pager -l

echo "===== SYSTEMD UNIT TIMESTAMPS ====="
systemctl show mnt-pve-backup.mount \
  -p FragmentPath -p ActiveState -p SubState \
  -p ActiveEnterTimestamp -p StateChangeTimestamp \
  -p InactiveEnterTimestamp -p NeedDaemonReload \
  -p What -p Where -p Type

echo "===== MOUNT UNIT JOURNAL ====="
journalctl -b -u mnt-pve-backup.mount --no-pager -o short-iso

echo "===== ACTUAL KERNEL MOUNT ====="
findmnt -T /mnt/pve/backup -o TARGET,SOURCE,FSTYPE,OPTIONS

echo "===== PID 1 MOUNT TABLE ====="
grep ' /mnt/pve/backup ' /proc/1/mountinfo
```

The current NFS mount works correctly (systemd remembers the NFS mounted by hand). However, **if the host is rebooted as it is, the file's ext4 settings will be loaded.** Make the file match the NFS settings.

> **Caution**: Here we do not run `daemon-reload`, unmount, or reboot.

## 1.3 Making the Unit File NFS

Back up the current file, rewrite it, and check it with `systemd-analyze verify`.

```bash
BACKUP="/root/mnt-pve-backup.mount.before-nfs-20261122"

echo "===== BACKUP EXISTENCE CHECK ====="
if [ -e "$BACKUP" ]; then
  echo "ERROR: backup file already exists: $BACKUP"
else
  cp -a /etc/systemd/system/mnt-pve-backup.mount "$BACKUP"
  echo "BACKUP_CREATED=$?"
fi

echo "===== WRITE NFS MOUNT UNIT ====="
if [ -f "$BACKUP" ]; then
  cat > /etc/systemd/system/mnt-pve-backup.mount <<'EOF'
[Unit]
Description=Mount TrueNAS NFS backup storage
Wants=network-online.target
After=network-online.target

[Mount]
What=192.168.0.254:/mnt/backup
Where=/mnt/pve/backup
Type=nfs
Options=defaults,_netdev,vers=3

[Install]
WantedBy=multi-user.target
EOF
  echo "WRITE_EXIT=$?"
else
  echo "WRITE_SKIPPED: backup was not created"
fi

echo "===== VERIFY UNIT SYNTAX ====="
systemd-analyze verify /etc/systemd/system/mnt-pve-backup.mount
echo "VERIFY_EXIT=$?"

echo "===== CURRENT UNIT FILE ====="
cat /etc/systemd/system/mnt-pve-backup.mount
```

The backup (`/root/mnt-pve-backup.mount.before-nfs-20261122`) was created, and the rewritten file gave `VERIFY_EXIT=0`.

## 1.4 Making systemd Load It

The current NFS mount is left running; it is not remounted or unmounted.

```bash
echo "===== RELOAD SYSTEMD CONFIGURATION ====="
systemctl daemon-reload
echo "DAEMON_RELOAD_EXIT=$?"

echo "===== LOADED UNIT CONFIGURATION ====="
systemctl show mnt-pve-backup.mount \
  -p What -p Where -p Type -p ActiveState -p SubState \
  -p NeedDaemonReload -p FragmentPath

echo "===== MOUNT STATUS ====="
findmnt -T /mnt/pve/backup -o TARGET,SOURCE,FSTYPE,OPTIONS

echo "===== ENABLED AT BOOT ====="
systemctl is-enabled mnt-pve-backup.mount
```

```text
DAEMON_RELOAD_EXIT=0
Where=/mnt/pve/backup
What=192.168.0.254:/mnt/backup
Type=nfs
ActiveState=active
SubState=mounted
NeedDaemonReload=no
===== ENABLED AT BOOT =====
enabled
```

The file and the running settings now match, and NFS will be mounted at boot as well.

# Chapter 2: Registering as Proxmox Storage

## 2.1 Is the Name Free?

The storage ID will be `truenas-backup`.

```bash
echo "===== EXISTING STORAGE CONFIGURATION ====="
cat /etc/pve/storage.cfg

echo "===== STORAGE ID COLLISION CHECK ====="
if grep -qE '^[[:space:]]*(dir|nfs|pbs|cifs):[[:space:]]+truenas-backup([[:space:]]|$)' /etc/pve/storage.cfg; then
  echo "COLLISION: truenas-backup already exists"
else
  echo "NO_COLLISION"
fi

echo "===== CURRENT STORAGE STATUS ====="
pvesm status
```

`NO_COLLISION`.

## 2.2 Registering

Register it as "directory" storage using the existing NFS mount, so that Proxmox does not mount it a second time. The content is `backup` only (not used for VM disks and the like), and `--is_mountpoint 1` is added. This prevents backups from being written to the empty local directory when NFS is not mounted. Just before registering, check the mount's source and type, and register only if they match.

```bash
echo "===== PRE-REGISTRATION SAFETY CHECK ====="
SOURCE="$(findmnt -n -o SOURCE -T /mnt/pve/backup)"
FSTYPE="$(findmnt -n -o FSTYPE -T /mnt/pve/backup)"

echo "SOURCE=$SOURCE"
echo "FSTYPE=$FSTYPE"

if [ "$SOURCE" = "192.168.0.254:/mnt/backup" ] && \
   [ "$FSTYPE" = "nfs" ] && \
   mountpoint -q /mnt/pve/backup; then

  echo "===== ADD PROXMOX DIRECTORY STORAGE ====="
  pvesm add dir truenas-backup \
    --path /mnt/pve/backup \
    --content backup \
    --is_mountpoint 1 \
    --nodes pve

  echo "===== ADD COMMAND EXIT CODE ====="
  echo "$?"

else
  echo "REGISTRATION_ABORTED: NFS mount verification failed"
fi
```

`SOURCE=192.168.0.254:/mnt/backup`, `FSTYPE=nfs`, and the exit code was `0`.

```bash
echo "===== REGISTERED STORAGE CONFIGURATION ====="
grep -A6 -B1 -n 'truenas-backup' /etc/pve/storage.cfg

echo "===== STORAGE STATUS ====="
pvesm status --storage truenas-backup

echo "===== BACKUP CONTENT LIST ====="
pvesm list truenas-backup

echo "===== MOUNTPOINT VERIFICATION ====="
findmnt -T /mnt/pve/backup -o TARGET,SOURCE,FSTYPE,OPTIONS

echo "===== BACKUP DIRECTORY CONTENTS ====="
ls -lah /mnt/pve/backup
```

```text
dir: truenas-backup
     path /mnt/pve/backup
     content backup
     is_mountpoint 1
     nodes pve
```

`truenas-backup` was `active` with about 1.89TiB free, and the list of backups was still empty. `/mnt/pve/backup/dump` was also created.

# Chapter 3: Investigating What to Back Up

## 3.1 VMs and LXCs

```bash
echo "===== VM INVENTORY ====="
qm list

echo "===== LXC INVENTORY (ID BELOW 400) ====="
pct list | awk 'NR == 1 || $1 < 400'

echo "===== VZDUMP CURRENT CONFIGURATION ====="
if [ -f /etc/vzdump.conf ]; then
  cat /etc/vzdump.conf
else
  echo "No /etc/vzdump.conf"
fi

echo "===== BACKUP STORAGE STATUS ====="
pvesm status --storage truenas-backup
```

> **Caution**: **VM 100 (TrueNAS) is the very server that provides this NFS destination.** Writing its own backup to its own NFS would make it impossible to restore if it broke (a circular dependency), so it is not a target for backups to `truenas-backup`. How to protect TrueNAS itself is considered separately.

## 3.2 Disk Configuration

```bash
echo "===== VM DISK CONFIGURATIONS ====="
for id in 101 102 104 126 220 230; do
  echo
  echo "--- VM $id ---"
  qm config "$id" | grep -E '^(name|boot|bios|machine|scsi[0-9]+|sata[0-9]+|virtio[0-9]+|ide[0-9]+|efidisk[0-9]+|tpmstate[0-9]+|unused[0-9]+):'
done

echo
echo "===== LXC ROOTFS AND MOUNT CONFIGURATIONS ====="
for id in 103 105 107 108 109 111 113 114 115 118 119 120 121 123 129 134 140 141 147 199 200 201 204 205 206 208 209 350; do
  echo
  echo "--- LXC $id ---"
  pct config "$id" | grep -E '^(hostname|rootfs|mp[0-9]+|unused[0-9]+|unprivileged|features):'
done

echo
echo "===== NFS BACKUP STORAGE CONTENT ====="
pvesm list truenas-backup
```

```bash
echo "===== VM 101 BACKUP SETTINGS ====="
qm config 101

echo "===== VM 220 BACKUP SETTINGS ====="
qm config 220

echo "===== VM 230 BACKUP SETTINGS ====="
qm config 230

echo "===== POSTGRESQL LXC 109 ====="
pct config 109

echo "===== NVIDIA LXC 208 ====="
pct config 208

echo "===== OLLAMA LXC 209 ====="
pct config 209

echo "===== NVIDIA HOST DIRECTORY ====="
ls -ld /opt/nvidia-lxc-570
du -sh /opt/nvidia-lxc-570 2>/dev/null
```

| Target | Points to note |
|---|---|
| VM 220 security-core, VM 230 ai-defense-manager | The core of this system; high priority to protect |
| LXC 109 postgresql | No additional mounts, 50GB. Needs a logical DB backup in addition to the container backup |
| VM 101 | Its GPU is passed through over PCI; when restoring, the GPU assignment and the host's drivers must be checked again |
| VM 220 | Uses two networks: `vmbr0` and the internal `vmbr1` |
| LXC 208, 209 | Mount the host's `/opt/nvidia-lxc-570` (about 72MB) via `mp8`. This is not included in LXC backups, so protect it separately |

## 3.3 Space Actually Used

```bash
echo "===== QEMU GUEST AGENT STATUS ====="
for id in 101 220 230; do
  echo
  echo "--- VM $id ---"
  if qm agent "$id" ping 2>/dev/null; then
    echo "--- FILESYSTEM USAGE ---"
    qm agent "$id" get-fsinfo
  else
    echo "GUEST_AGENT_UNAVAILABLE"
  fi
done

echo
echo "===== RUNNING LXC ROOT FILESYSTEM USAGE ====="
for id in 103 105 109 111 129 134 200 350; do
  echo
  echo "--- LXC $id ---"
  pct exec "$id" -- df -hP /
done

echo
echo "===== NVIDIA HOST DIRECTORY MOUNT ====="
findmnt -T /opt/nvidia-lxc-570 -o TARGET,SOURCE,FSTYPE,OPTIONS

echo
echo "===== VZDUMP AVAILABLE OPTIONS ====="
vzdump --help
```

(The final `vzdump --help` gives `Unknown option: help`. Read the documentation with `man vzdump`.)

| Target | Used |
|---|---:|
| VM 220 security-core | About 26.1GiB |
| LXC 103 Prometheus | 1.9GB |
| LXC 105 Grafana | 2.4GB |
| LXC 109 PostgreSQL | 1.7GB |
| LXC 111 Wiki | 2.1GB |
| LXC 129 Open WebUI | 16GB |
| LXC 134 Qdrant | 1.2GB |
| LXC 200 Novel | 39GB |
| LXC 350 easywrider | 59GB |

The measurable ones alone come to about 150GB (before compression). VMs 101 and 230 did not answer the QEMU Guest Agent and could not be measured.

# Chapter 4: The PostgreSQL Backup Method

## 4.1 PostgreSQL's State

```bash
echo "===== POSTGRESQL SERVICE STATUS ====="
pct exec 109 -- pg_isready

echo
echo "===== POSTGRESQL VERSION AND DATABASE SIZES ====="
pct exec 109 -- runuser -u postgres -- psql -X -v ON_ERROR_STOP=1 -At -F '|' -c "
SELECT version();
SELECT datname, pg_size_pretty(pg_database_size(datname))
FROM pg_database
WHERE datallowconn
ORDER BY pg_database_size(datname) DESC;
"

echo
echo "===== POSTGRESQL WAL CONFIGURATION ====="
pct exec 109 -- runuser -u postgres -- psql -X -v ON_ERROR_STOP=1 -At -F '|' -c "
SHOW archive_mode;
SHOW wal_level;
SHOW max_wal_size;
SHOW data_directory;
"

echo
echo "===== POSTGRESQL WAL DIRECTORY SIZE ====="
pct exec 109 -- runuser -u postgres -- psql -X -v ON_ERROR_STOP=1 -At -c "
SELECT pg_size_pretty(COALESCE(SUM(size), 0))
FROM pg_ls_waldir();
"
```

PostgreSQL was 17.11; the largest DB was `agent_memory` (about 205MB), followed by `novel` (about 78MB). `archive_mode` was `off`, and WAL was about 32MB.

## 4.2 Roles, Tablespaces and Extensions

Password information is not shown.

```bash
echo "===== BACKUP TOOL VERSIONS ====="
pct exec 109 -- pg_dump --version
pct exec 109 -- pg_dumpall --version

echo
echo "===== POSTGRESQL ROLES (NO PASSWORD DATA) ====="
pct exec 109 -- runuser -u postgres -- psql -X -d postgres -P pager=off -c "
SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolcanlogin
FROM pg_roles
ORDER BY rolname;
"

echo
echo "===== TABLESPACES ====="
pct exec 109 -- runuser -u postgres -- psql -X -d postgres -P pager=off -c "
SELECT spcname, pg_tablespace_location(oid) AS location
FROM pg_tablespace
ORDER BY spcname;
"

echo
echo "===== INSTALLED EXTENSIONS PER DATABASE ====="
pct exec 109 -- bash -lc '
runuser -u postgres -- psql -X -d postgres -Atc "
SELECT datname
FROM pg_database
WHERE datallowconn = true AND NOT datistemplate
ORDER BY datname;
" | while IFS= read -r db; do
  echo "--- DATABASE: $db ---"
  runuser -u postgres -- psql -X -d "$db" -Atc "
  SELECT extname || '\'' | version='\'' || extversion
  FROM pg_extension
  ORDER BY extname;
  "
done
'
```

| Item | Result |
|---|---|
| `pg_dump` / `pg_dumpall` | 17.11, same as the server |
| Roles | 33 (`wazuh_collector` is an ordinary login role) |
| Tablespaces | Only `pg_default` and `pg_global` |
| Extensions | `plpgsql` and `vector` 0.8.7 (used in `easywrider`, `postgres` and `vector_db`) |

## 4.3 Data Volume and NFS Capacity

```bash
echo "===== POSTGRESQL DATA DIRECTORY ====="
pct exec 109 -- du -sh /var/lib/postgresql/17/main
pct exec 109 -- du -sh /var/lib/postgresql/17/main/base
pct exec 109 -- du -sh /var/lib/postgresql/17/main/pg_wal

echo
echo "===== PGVECTOR PACKAGE ====="
pct exec 109 -- dpkg-query -W -f='${Package} ${Version}\n' postgresql-17-pgvector 2>/dev/null
pct exec 109 -- ls -l /usr/share/postgresql/17/extension/vector.control

echo
echo "===== NFS BACKUP CAPACITY ====="
findmnt /mnt/pve/backup
df -hP /mnt/pve/backup
pvesm status --storage truenas-backup
```

The data was 475MB (`base` 442MB, WAL 33MB), and pgvector 0.8.7 was installed. The NFS has about 1.9TB free.

## 4.4 LXC 109 Snapshots

```bash
echo "===== LXC 109 CONFIGURATION ====="
pct config 109

echo
echo "===== LOCAL-LVM STORAGE CONFIGURATION ====="
grep -A8 -B1 '^lvmthin: local-lvm' /etc/pve/storage.cfg

echo
echo "===== LOCAL-LVM STATUS ====="
pvesm status --storage local-lvm

echo
echo "===== BACKUP STORAGE CONFIGURATION ====="
grep -A8 -B1 '^dir: truenas-backup' /etc/pve/storage.cfg

echo
echo "===== BACKUP DIRECTORY ====="
ls -ld /mnt/pve/backup /mnt/pve/backup/dump
```

```bash
echo "===== LVM-THIN POOL CAPACITY ====="
lvs -a -o vg_name,lv_name,lv_attr,lv_size,data_percent,metadata_percent

echo
echo "===== LXC 109 ROOTFS VOLUME ====="
lvs -o vg_name,lv_name,lv_attr,lv_size,data_percent,metadata_percent pve/vm-109-disk-0

echo
echo "===== SNAPSHOT CAPABILITY ====="
pvesm status --storage local-lvm
```

LXC 109 is an unprivileged Debian 13 LXC, and its only disk is `pve/vm-109-disk-0` on `local-lvm` (LVM-thin). `local-lvm` is at 61.66% with metadata at 2.18%, enough room for snapshots.

## 4.5 Deciding the Method

| Target | Method | Purpose |
|---|---|---|
| All PostgreSQL DBs | `pg_dump` custom format (`-Fc`), one per DB | Restore per DB |
| PostgreSQL roles and the like | `pg_dumpall --globals-only` | Restore roles and permissions |
| LXC 109 | Proxmox `vzdump` snapshot | Restore the OS, PostgreSQL itself and settings |
| pgvector | Record the package and extension versions | Prepare the extension at the restore destination |

> **Caution**: The output of `pg_dumpall --globals-only` may include role password hashes. Saved files are made readable and writable by root only.

The generations kept are **7 daily, 4 weekly and 3 monthly** (decided after confirmation in the original build).

# Chapter 5: Deciding the Schedule

## 5.1 Current Jobs

```bash
echo "===== PROXMOX BACKUP JOBS ====="
if [ -f /etc/pve/jobs.cfg ]; then
  cat /etc/pve/jobs.cfg
else
  echo "NO jobs.cfg"
fi

echo
echo "===== VZDUMP CRON ENTRIES ====="
grep -RniE 'vzdump|pg_dump|pg_dumpall' \
  /etc/cron.d /etc/cron.daily /etc/cron.weekly /etc/cron.monthly \
  /var/spool/cron/crontabs 2>/dev/null

echo
echo "===== BACKUP-RELATED SYSTEMD TIMERS ====="
systemctl list-timers --all --no-pager | grep -Ei 'backup|vzdump|postgres|dump'
```

There were no Proxmox backup jobs, no cron for PostgreSQL, and no backup timers (`/etc/cron.d/vzdump` is the standard file and contains only comments).

The times were decided as follows (Japan time).

| Time | Task |
|---|---|
| Daily 02:00 | PostgreSQL logical backup |
| Daily 03:00 | LXC 109 snapshot backup |
| Every Sunday | That day's backup becomes the weekly generation |
| 1st of every month | That day's backup becomes the monthly generation |

## 5.2 Proxmox's Version and Backup Job Features

```bash
echo "===== PROXMOX VERSION ====="
pveversion -v

echo
echo "===== VZDUMP COMMAND OPTIONS ====="
vzdump 109 --help 2>&1

echo
echo "===== PROXMOX BACKUP API ====="
pvesh get /cluster/backup --output-format json 2>&1

echo
echo "===== SYSTEMD VERSION ====="
systemctl --version | head -1
```

Proxmox VE was 8.4.20, systemd 252, and backup jobs were `[]`.

```bash
echo "===== VZDUMP MANUAL ====="
if man -w vzdump >/dev/null 2>&1; then
  man -P cat vzdump | col -b | grep -n -A8 -B3 -E 'snapshot|prune-backups|keep-daily|keep-weekly|keep-monthly|storage|mode'
else
  echo "vzdump manual not found"
fi

echo
echo "===== BACKUP JOB API PARAMETERS ====="
pvesh usage /cluster/backup --verbose 2>&1

echo
echo "===== BACKUP JOB API SCHEMA ====="
pvesh get /cluster/backup --output-format json-pretty
```

Generations can be kept with Proxmox's standard feature (`--prune-backups 'keep-daily=7,keep-weekly=4,keep-monthly=3'`). When the daily, weekly and monthly periods overlap, the number actually kept may be less than 14.

## 5.3 Checking the Time

```bash
echo "===== HOST TIMEZONE ====="
timedatectl show -p Timezone -p LocalRTC -p NTPSynchronized

echo
echo "===== DAILY 03:00 SCHEDULE VALIDATION ====="
systemd-analyze calendar '*-*-* 03:00:00'
```

The Proxmox host was `Timezone=Asia/Tokyo` and synchronized with NTP, and `*-*-* 03:00:00` was interpreted as 03:00 every day (Japan time).

# Chapter 6: Registering the LXC 109 Job While Disabled

Because it is registered disabled (`--enabled 0`), this operation performs no backup and the schedule does not run.

> **Run on: pve**

```bash
pvesh create /cluster/backup \
  --id lxc109-daily \
  --node pve \
  --vmid 109 \
  --storage truenas-backup \
  --mode snapshot \
  --compress zstd \
  --prune-backups 'keep-daily=7,keep-weekly=4,keep-monthly=3' \
  --schedule '*-*-* 03:00:00' \
  --enabled 0 \
  --repeat-missed 0 \
  --comment 'LXC 109 daily snapshot backup to TrueNAS'
```

It finishes without output. Check what was registered.

```bash
echo "===== REGISTERED BACKUP JOB ====="
pvesh get /cluster/backup --output-format json-pretty

echo
echo "===== BACKUP JOB CONFIGURATION ====="
cat /etc/pve/jobs.cfg
```

| Item | Value |
|---|---|
| Target | LXC 109 only |
| Destination | `truenas-backup` |
| Time | Daily 03:00 |
| Mode, compression | snapshot, zstd |
| Generations | `keep-daily=7,keep-monthly=3,keep-weekly=4` |
| Making up missed runs | No (`repeat-missed 0`) |
| Enabled | `enabled 0` (disabled) |

The API response and `/etc/pve/jobs.cfg` matched.

# Chapter 7: The PostgreSQL Logical Backup Script

## 7.1 Destination and Tools

```bash
echo "===== BACKUP STORAGE DIRECTORY ====="
find /mnt/pve/backup -maxdepth 2 -printf '%M %u:%g %p\n' | sort

echo
echo "===== STORAGE MOUNT ====="
findmnt /mnt/pve/backup

echo
echo "===== STORAGE CAPACITY ====="
df -h /mnt/pve/backup
```

Only `/mnt/pve/backup` and `/mnt/pve/backup/dump` existed (both `root:root`).

```bash
echo "===== LXC 109 STATUS ====="
pct status 109

echo
echo "===== POSTGRESQL VERSION AND TIMEZONE ====="
pct exec 109 -- bash -lc '
  pg_dump --version
  pg_dumpall --version
  date "+%Y-%m-%d %H:%M:%S %Z %z"
  timedatectl show -p Timezone 2>/dev/null
'

echo
echo "===== DATABASE LIST ====="
pct exec 109 -- runuser -u postgres -- psql -X -At -d postgres -c "
SELECT datname
FROM pg_database
WHERE datallowconn
  AND NOT datistemplate
ORDER BY datname;
"

echo
echo "===== POSTGRESQL BACKUP TOOL AVAILABILITY ====="
pct exec 109 -- bash -lc '
  command -v pg_dump
  command -v pg_dumpall
  command -v psql
  command -v runuser
'
```

LXC 109 is running, and `pg_dump`, `pg_dumpall`, `psql` and `runuser` are available. Both LXC 109 and the Proxmox host are `Asia/Tokyo`. There were 17 DBs excluding templates (`agent_db`, `agent_memory`, `aiagent`, `aipmo`, `cerebrum`, `easywrider`, `movie`, `nfaipmo`, `novel`, `orchivio`, `postgres`, `security_workbench`, `tester`, `vector_db`, `winfilemgr`, `writer`, `writers`).

```bash
echo "===== DATABASE SIZES ====="
pct exec 109 -- runuser -u postgres -- psql -X -P pager=off -d postgres -c "
SELECT
  datname AS database,
  pg_size_pretty(pg_database_size(datname)) AS size
FROM pg_database
WHERE datallowconn
  AND NOT datistemplate
ORDER BY pg_database_size(datname) DESC;
"

echo
echo "===== INSTALLED EXTENSIONS ====="
pct exec 109 -- bash -lc '
for db in $(runuser -u postgres -- psql -X -At -d postgres -c "
  SELECT datname
  FROM pg_database
  WHERE datallowconn AND NOT datistemplate
  ORDER BY datname
"); do
  echo "--- $db ---"
  runuser -u postgres -- psql -X -At -d "$db" -c "
    SELECT extname || E'\'' '\''
           || extversion
    FROM pg_extension
    ORDER BY extname;
  "
done
'

echo
echo "===== PGVECTOR PACKAGE ====="
pct exec 109 -- dpkg-query -W -f='${Package} ${Version}\n' postgresql-17-pgvector
```

The 17 DBs totaled about 450MB; the three that use the `vector` extension are `easywrider`, `postgres` and `vector_db`, and the package was `postgresql-17-pgvector 0.8.7-1.pgdg13+1`.

## 7.2 What Is Saved

| File | Contents |
|---|---|
| `globals.sql` | Roles and the like (contains password hashes, so readable by root only) |
| `<DB name>.dump` | Custom-format dump per DB (17) |
| `database-list.txt`, `postgresql-version.txt`, `extensions.tsv` | DB list, PostgreSQL version, extensions and their versions |
| `SHA256SUMS` | Checksums of all files |

Daily backups go to `daily/<date>`, weekly (Sunday) to `weekly/<year-Wweek>`, and monthly (the 1st) to `monthly/<year-month>`; weekly and monthly are hard links to the daily files (`cp -al`), so the same data is not stored three times.

## 7.3 Are the Names and Directories Free?

```bash
echo "===== POSTGRESQL BACKUP UNIT COLLISION CHECK ====="
for f in \
  /usr/local/sbin/pg-logical-backup.sh \
  /etc/systemd/system/pg-logical-backup.service \
  /etc/systemd/system/pg-logical-backup.timer
do
  if [ -e "$f" ]; then
    ls -l "$f"
  else
    echo "NOT_EXISTS: $f"
  fi
done

echo
echo "===== DAILY 02:00 JST SCHEDULE VALIDATION ====="
systemd-analyze calendar '*-*-* 02:00:00'

echo
echo "===== EXISTING RELATED SYSTEMD UNITS ====="
systemctl list-unit-files --no-legend | grep -Ei 'postgres.*backup|pg.*backup' || true
```

All three were `NOT_EXISTS`, and `*-*-* 02:00:00` was interpreted as 02:00 every day (Japan time).

```bash
echo "===== BACKUP SCRIPT DIRECTORY ====="
ls -ld /usr/local/sbin

echo
echo "===== BACKUP STORAGE ROOT ====="
ls -ld /mnt/pve/backup
ls -ld /mnt/pve/backup/dump

echo
echo "===== LOCAL LOCK DIRECTORY ====="
ls -ld /run/lock
```

`/usr/local/sbin`, `/mnt/pve/backup` and `/run/lock` were all fine.

## 7.4 Placing the Script

The script's safety design is as follows.

- Stop if NFS is not mounted (also check that the mount's source is `192.168.0.254:/mnt/backup` and it is NFS)
- Lock so that two cannot run at the same time (`flock`)
- Write to a temporary directory (`.staging`), create and verify all checksums, then move it into the daily directory
- Permissions readable and writable by root only (`umask 077`, directories `700`)
- Delete only old generations beyond the number to keep

At this stage the script is only placed; no DB dump is taken.

> **Run on: pve**

```bash
cat > /usr/local/sbin/pg-logical-backup.sh <<'SCRIPT'
#!/bin/bash

# PostgreSQL logical backup for LXC 109
# Run as root on Proxmox host.

PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
umask 077

CTID=109
MOUNT=/mnt/pve/backup
BASE="$MOUNT/postgresql"
DAILY="$BASE/daily"
WEEKLY="$BASE/weekly"
MONTHLY="$BASE/monthly"
STAGING="$BASE/.staging"
LOCK=/run/lock/pg-logical-backup.lock

log() {
    printf '%s %s\n' "$(date '+%F %T %Z')" "$*"
}

fail() {
    log "ERROR: $*"
    exit 1
}

# Prevent concurrent runs.
exec 9>"$LOCK" || fail "Cannot open lock file"
flock -n 9 || fail "Another backup process is running"

# Confirm the expected NFS mount is active.
mountpoint -q "$MOUNT" || fail "Backup mount is unavailable"
findmnt -rn -T "$MOUNT" -o SOURCE,FSTYPE |
    grep -Fq '192.168.0.254:/mnt/backup nfs' ||
    fail "Unexpected backup filesystem"

# Confirm the container is running.
pct status "$CTID" | grep -q 'status: running' ||
    fail "LXC $CTID is not running"

# Prepare directories.
for dir in "$DAILY" "$WEEKLY" "$MONTHLY" "$STAGING"; do
    mkdir -p "$dir" || fail "Cannot create $dir"
    chmod 700 "$dir" || fail "Cannot secure $dir"
done

DATE=$(date '+%F')
WEEK=$(date '+%G-W%V')
MONTH=$(date '+%Y-%m')
DAY=$(date '+%d')

FINAL="$DAILY/$DATE"
WORK="$STAGING/${DATE}-$$"

[ ! -e "$FINAL" ] || fail "Daily backup already exists: $FINAL"

mkdir -m 700 "$WORK" || fail "Cannot create staging directory"

cleanup() {
    if [ -d "$WORK" ]; then
        rm -rf -- "$WORK"
    fi
}
trap cleanup EXIT

log "Starting PostgreSQL logical backup for LXC $CTID"

# Save global objects, including role password hashes.
pct exec "$CTID" -- runuser -u postgres -- \
    pg_dumpall --globals-only > "$WORK/globals.sql" ||
    fail "Global objects dump failed"

# Save database inventory.
pct exec "$CTID" -- runuser -u postgres -- \
    psql -X -At -d postgres -c "
        SELECT datname
        FROM pg_database
        WHERE datallowconn AND NOT datistemplate
        ORDER BY datname;
    " > "$WORK/database-list.txt" ||
    fail "Database inventory query failed"

[ -s "$WORK/database-list.txt" ] ||
    fail "Database inventory is empty"

# Save PostgreSQL version.
pct exec "$CTID" -- runuser -u postgres -- \
    psql -X -At -d postgres -c "SELECT version();" \
    > "$WORK/postgresql-version.txt" ||
    fail "PostgreSQL version query failed"

# Save extension inventory.
while IFS= read -r db; do
    [ -n "$db" ] || continue

    case "$db" in
        *[!A-Za-z0-9_-]*)
            fail "Unexpected database name: $db"
            ;;
    esac

    {
        printf '%s\t' "$db"
        pct exec "$CTID" -- runuser -u postgres -- \
            psql -X -At -F $'\t' -d "$db" -c \
            "SELECT extname, extversion FROM pg_extension ORDER BY extname;" ||
            fail "Extension query failed for $db"
    } >> "$WORK/extensions.tsv" ||
        fail "Cannot write extension inventory"

    log "Dumping database: $db"
    pct exec "$CTID" -- runuser -u postgres -- \
        pg_dump -Fc -d "$db" > "$WORK/${db}.dump" ||
        fail "Database dump failed: $db"

    [ -s "$WORK/${db}.dump" ] ||
        fail "Database dump is empty: $db"

done < "$WORK/database-list.txt"

[ -s "$WORK/globals.sql" ] ||
    fail "Global objects dump is empty"

# Create checksums for all backup files.
(
    cd "$WORK" || exit 1
    find . -maxdepth 1 -type f ! -name SHA256SUMS -printf '%f\n' |
        LC_ALL=C sort |
        while IFS= read -r file; do
            sha256sum -- "$file"
        done
) > "$WORK/SHA256SUMS" ||
    fail "Checksum generation failed"

# Verify checksums before publishing the backup.
(
    cd "$WORK" || exit 1
    sha256sum -c SHA256SUMS
) || fail "Checksum verification failed"

# Publish daily backup atomically.
mv "$WORK" "$FINAL" || fail "Cannot publish daily backup"
trap - EXIT
log "Daily backup published: $FINAL"

# Weekly generation: Sunday only.
if [ "$DAY" != "00" ] && [ "$(date '+%u')" = "7" ]; then
    if [ ! -e "$WEEKLY/$WEEK" ]; then
        cp -al "$FINAL" "$WEEKLY/$WEEK" ||
            fail "Cannot create weekly hard-link generation"
        log "Weekly generation created: $WEEK"
    fi
fi

# Monthly generation: first day of month only.
if [ "$DAY" = "01" ]; then
    if [ ! -e "$MONTHLY/$MONTH" ]; then
        cp -al "$FINAL" "$MONTHLY/$MONTH" ||
            fail "Cannot create monthly hard-link generation"
        log "Monthly generation created: $MONTH"
    fi
fi

prune_generations() {
    local dir="$1"
    local keep="$2"
    local remove_list

    remove_list=$(find "$dir" -mindepth 1 -maxdepth 1 -type d \
        -printf '%f\n' | LC_ALL=C sort -r | tail -n "+$((keep + 1))")

    if [ -n "$remove_list" ]; then
        while IFS= read -r name; do
            [ -n "$name" ] || continue
            case "$name" in
                *[!A-Za-z0-9_-]*)
                    fail "Unexpected generation name in $dir: $name"
                    ;;
            esac
            rm -rf -- "$dir/$name" ||
                fail "Cannot prune generation: $dir/$name"
            log "Pruned generation: $dir/$name"
        done <<< "$remove_list"
    fi
}

prune_generations "$DAILY" 7
prune_generations "$WEEKLY" 4
prune_generations "$MONTHLY" 3

log "PostgreSQL logical backup completed successfully"
SCRIPT

chmod 700 /usr/local/sbin/pg-logical-backup.sh

echo "===== SCRIPT PERMISSIONS ====="
stat -c '%A %U:%G %n' /usr/local/sbin/pg-logical-backup.sh

echo
echo "===== SCRIPT SYNTAX CHECK ====="
bash -n /usr/local/sbin/pg-logical-backup.sh
echo "BASH_SYNTAX_EXIT=$?"
```

```text
===== SCRIPT PERMISSIONS =====
-rwx------ root:root /usr/local/sbin/pg-logical-backup.sh

===== SCRIPT SYNTAX CHECK =====
BASH_SYNTAX_EXIT=0
```

The script is placed as `700`, readable and executable by root only, and passed the syntax check. **It has not been run yet.**

## 7.5 Can Hard Links Be Created on NFS?

Weekly and monthly generations are created as hard links to the daily files, so this assumes that hard links can be created on TrueNAS's NFS. Create two temporary files (the original and a link), check that they have the same inode, and delete them immediately. Backup data is not touched.

```bash
echo "===== NFS MOUNT DETECTION ====="
findmnt -rn -T /mnt/pve/backup -o SOURCE,FSTYPE
if findmnt -rn -T /mnt/pve/backup -o SOURCE,FSTYPE |
   grep -Fq '192.168.0.254:/mnt/backup nfs'; then
  echo "MOUNT_CHECK=PASS"
else
  echo "MOUNT_CHECK=FAIL"
fi

echo
echo "===== NFS HARDLINK TEST ====="
TEST_FILE="/mnt/pve/backup/.pg-hardlink-test-$$"
LINK_FILE="${TEST_FILE}.link"

cleanup_test() {
  rm -f -- "$TEST_FILE" "$LINK_FILE"
}
trap cleanup_test EXIT

printf 'temporary hardlink test\n' > "$TEST_FILE"

if ln "$TEST_FILE" "$LINK_FILE"; then
  stat -c 'inode=%i links=%h file=%n' "$TEST_FILE" "$LINK_FILE"
  if [ "$(stat -c '%i' "$TEST_FILE")" = "$(stat -c '%i' "$LINK_FILE")" ]; then
    echo "HARDLINK_TEST=PASS"
  else
    echo "HARDLINK_TEST=FAIL"
  fi
else
  echo "HARDLINK_TEST=FAIL"
fi

cleanup_test
trap - EXIT

echo
echo "===== TEST FILE CLEANUP ====="
if [ ! -e "$TEST_FILE" ] && [ ! -e "$LINK_FILE" ]; then
  echo "CLEANUP=PASS"
else
  echo "CLEANUP=FAIL"
fi
```

If it shows `MOUNT_CHECK=PASS`, `HARDLINK_TEST=PASS` and `CLEANUP=PASS`, we can proceed with the current generation management method. The test result is shown in Chapter 1 of Part 40 (it passed).

# Closing Notes

In Part 39 we registered the TrueNAS destination with Proxmox and prepared scheduled backups.

| Item | Result |
|---|---|
| Mount unit | `mnt-pve-backup.mount` changed from ext4 (a nonexistent UUID) to NFS. Backup `/root/mnt-pve-backup.mount.before-nfs-20261122`. Enabled at boot |
| Storage | `truenas-backup` (dir, `content backup`, `is_mountpoint 1`), about 1.89TiB |
| Excluded from backups | VM 100 (TrueNAS itself) |
| Generations | 7 daily, 4 weekly, 3 monthly |
| LXC 109 job | `lxc109-daily` (daily 03:00, snapshot, zstd, `truenas-backup`) registered **while disabled** |
| PostgreSQL logical backup | `/usr/local/sbin/pg-logical-backup.sh` (`700`, syntax check passed) placed; planned to run daily at 02:00 |
| Not yet done | Hard link test result, systemd service and timer, first run, enabling the job and timer, restore test |

In the next part, Part 40, we check the result of the hard-link test and make the PostgreSQL logical backup run every day under systemd.

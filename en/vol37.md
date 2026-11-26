---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 37: Backing Up PostgreSQL and Testing a Restore"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 37 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". The check in Part 36 showed that there was no PostgreSQL backup. Here we back up **LXC 109**, where PostgreSQL runs, with Proxmox's `vzdump`, **restore it to an LXC with a different number (110)**, and test that PostgreSQL starts and the data can be read. Production LXC 109 is not touched.

1. Investigate the backup settings on the Proxmox side and where backups can be stored
2. Back up LXC 109 using the `snapshot` mode
3. Check that the archive is intact and that Proxmox recognizes it as a backup
4. Restore it to LXC 110, start it with the network cut off, and check PostgreSQL and the data
5. Delete the test LXC 110

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)

# Chapter 1: Investigating the Proxmox Side

## 1.1 Confirming Where You Run

The commands from here on are run on the Proxmox host. If they are run on the PostgreSQL server (`root@postgresql`), you get errors such as `pvesm: command not found`. First check the host name.

> **Run on: pve**

```bash
hostname
```

Confirm that `pve` is shown before continuing.

## 1.2 Backup Jobs and Storage

```bash
echo "===== POSTGRESQL VM CONFIG ====="
qm config 151 2>/dev/null

echo "===== PROXMOX BACKUP JOBS ====="
pvesh get /cluster/backup --output-format yaml 2>/dev/null

echo "===== STORAGE CONTENT TYPES ====="
pvesm status
```

Backup jobs were `--- []` (none). `qm config 151` showed nothing (151 is the last part of the IP address, not a VM number).

> **Note**: `pvesm status` always prints the LVM error `no such logical volume windows_d/windows_d`. It is a separate problem from this work and is not fixed here.

```bash
qm list
```

The VMs were 100 (TrueNAS), 101 (ollama-gpu), 102, 104, 126, 220 (security-core) and 230 (ai-defense-manager); the PostgreSQL server is not a VM. PostgreSQL runs in **LXC 109**.

## 1.3 LXC 109's Configuration

```bash
echo "===== POSTGRESQL LXC 109 CONFIG ====="
pct config 109
```

| Item | Value |
|---|---|
| Disk | `local-lvm:vm-109-disk-0`, 50G |
| Type | Unprivileged LXC (`unprivileged: 1`) |
| Additional mounts | None |
| IP address | 192.168.0.151/24 |
| Start at boot | `onboot: 1` |

## 1.4 Where Backups Can Be Stored

```bash
cat /etc/pve/storage.cfg
```

The only storage that can hold `backup` content was `local` (`/var/lib/vz`). `local-lvm`, `RAID_A`, `RAID_B` and the others are for VM and LXC disks.

```bash
echo "===== LOCAL STORAGE FILESYSTEM ====="
df -hT /var/lib/vz

echo "===== LOCAL STORAGE MOUNT ====="
findmnt -T /var/lib/vz

echo "===== EXISTING BACKUP DIRECTORY ====="
ls -lah /var/lib/vz/dump/ 2>/dev/null
```

`local` is actually the Proxmox root file system (`/dev/mapper/pve-root`, 68G free of 94G), and `/var/lib/vz/dump/` was empty.

```bash
echo "===== LXC 109 ROOTFS USAGE ====="
pct exec 109 -- df -hT /

echo "===== POSTGRESQL DATA DIRECTORY ====="
pct exec 109 -- du -sh /var/lib/postgresql/17/main

echo "===== POSTGRESQL BACKUP-RELATED FILES ====="
pct exec 109 -- du -sh /var/backups /var/lib/postgresql
```

LXC 109 used 1.7G of 49G, and PostgreSQL's data was 473M. `local` has enough space. However, `local` is on the same device as the Proxmox root, so it is no protection if that disk fails (Part 38 prepares a separate destination).

# Chapter 2: The Backup Method

## 2.1 vzdump's Documentation

> **Note**: `vzdump --help` gives `Unknown option: help`. Read the documentation with `man vzdump`.

```bash
man vzdump
```

```bash
echo "===== VZDUMP MANUAL LOCATION ====="
man -w vzdump

echo "===== VZDUMP COMMAND LOCATION ====="
command -v vzdump

echo "===== VZDUMP VERSION ====="
pveversion
```

The manual page was `/usr/share/man/man1/vzdump.1.gz` and Proxmox VE was `pve-manager/8.4.20`. Extract the main options.

```bash
zcat /usr/share/man/man1/vzdump.1.gz \
  | grep -n -E 'mode|storage|dumpdir|remove|prune|compress|bwlimit'
```

| Option | Meaning |
|---|---|
| `--mode snapshot` | Create the backup from a storage snapshot. An LXC pauses briefly while the snapshot is taken (it is not entirely without interruption) |
| `--mode suspend` / `stop` | Create it with the guest suspended / stopped |
| `--compress zstd` | Compress with zstd |
| `--storage` | Destination |

For an LXC, `snapshot` requires its disks to be on storage that supports snapshots.

## 2.2 Can local-lvm Take Snapshots?

```bash
pvesm status --storage local-lvm
```

`local-lvm` (LVM-thin) was `active`, using about 514GB of about 833GB (61.66%). LVM-thin supports snapshots.

```bash
echo "===== LVM THIN POOL STATUS ====="
lvs -a -o vg_name,lv_name,lv_attr,lv_size,data_percent,metadata_percent

echo "===== PHYSICAL VOLUME STATUS ====="
pvs
```

`pve/data` was 61.66% used for data and 2.18% for metadata, with room to spare. Note that `local` and `local-lvm` are both on the same NVMe (`/dev/nvme0n1p3`).

# Chapter 3: Backing Up LXC 109

In the original build, approval was obtained before running this. The destination is `local`, the mode `snapshot`, compression `zstd`, and old backups are not deleted (`--remove 0`). LXC 109 pauses briefly while the snapshot is taken.

> **Run on: pve**

```bash
vzdump 109 --storage local --mode snapshot --compress zstd --remove 0
```

```text
INFO: Starting Backup of VM 109 (lxc)
INFO: backup mode: snapshot
INFO: cleanup temporary 'vzdump' snapshot
  Logical volume "snap_vm-109-disk-0_vzdump" successfully removed.
INFO: Finished Backup of VM 109 (00:00:17)
INFO: Backup job finished successfully
```

It finished in 17 seconds and created `/var/lib/vz/dump/vzdump-lxc-109-2026_11_22-13_25_49.tar.zst` (about 472MB).

> **Note**: LVM-thin prints two warnings: "protection against thin pools running out of space (automatic extension) is not enabled" and "the total allocated to thin volumes exceeds the actual capacity". The backup did not fail, but this is a capacity management issue (investigated in Part 38).

# Chapter 4: Checking the Backup

## 4.1 Is the Archive Intact?

```bash
BACKUP="/var/lib/vz/dump/vzdump-lxc-109-2026_11_22-13_25_49.tar.zst"

echo "===== BACKUP FILE ====="
stat -c 'File: %n%nSize: %s bytes%nModified: %y' "$BACKUP"

echo "===== ZSTD INTEGRITY TEST ====="
zstd -t "$BACKUP"
echo "ZSTD_TEST_EXIT=$?"

echo "===== TAR ARCHIVE LIST TEST ====="
tar --zstd -tf "$BACKUP" > /tmp/lxc109-backup-filelist.txt
echo "TAR_LIST_EXIT=$?"
echo "ARCHIVE_ENTRY_COUNT=$(wc -l < /tmp/lxc109-backup-filelist.txt)"
head -n 15 /tmp/lxc109-backup-filelist.txt
```

| Item | Result |
|---|---:|
| Size | 495,442,661 bytes |
| zstd test | Succeeded (0) |
| tar listing | Succeeded (0) |
| Number of entries | 37,918 |

## 4.2 Does It Contain PostgreSQL's Data?

```bash
echo "===== PROXMOX BACKUP METADATA ====="
pvesm extractconfig /var/lib/vz/dump/vzdump-lxc-109-2026_11_22-13_25_49.tar.zst

echo "===== POSTGRESQL BACKUP CONTENTS ====="
tar --zstd -tf /var/lib/vz/dump/vzdump-lxc-109-2026_11_22-13_25_49.tar.zst \
  | grep -E '^(\./)?var/lib/postgresql/|^(\./)?etc/postgresql/' \
  | head -n 30
```

It contained `./var/lib/postgresql/17/main/base/…` and `./etc/postgresql/…`. The first `pvesm extractconfig` fails with `unable to parse volume ID`, because this command takes a Proxmox volume ID (`local:backup/<file name>`), not a file path.

## 4.3 Does Proxmox Recognize It as a Backup?

```bash
echo "===== LOCAL BACKUP VOLUME ====="
pvesm list local --content backup

echo "===== BACKUP CONFIG VIA VOLUME ID ====="
pvesm extractconfig local:backup/vzdump-lxc-109-2026_11_22-13_25_49.tar.zst
```

With the volume ID, LXC 109's configuration (host name `postgresql`, 2 cores, 4GB, 50GB, 192.168.0.151, unprivileged) could be read. Besides this backup, the list also showed backups `13_22_41` and `13_24_39`, three in total. None of them is deleted.

# Chapter 5: Restoring to LXC 110 and Testing

In the original build, approval was obtained before running this, because a new LXC is created and uses space.

## 5.1 Number and Space

```bash
echo "===== TEST CTID 110 ====="
if [ -e /etc/pve/lxc/110.conf ] || [ -e /etc/pve/qemu-server/110.conf ]; then
  echo "CTID_110=IN_USE"
else
  echo "CTID_110=FREE"
fi

echo "===== LOCAL-LVM CAPACITY ====="
pvesm status --storage local-lvm

echo "===== LOCAL BACKUP STORAGE CAPACITY ====="
df -hT /var/lib/vz

echo "===== SOURCE BACKUP ====="
stat -c '%n | %s bytes' /var/lib/vz/dump/vzdump-lxc-109-2026_11_22-13_25_49.tar.zst
```

`CTID_110=FREE`, and `local-lvm` had about 319GiB free.

## 5.2 Restoring

The backup contains the same IP address as production (192.168.0.151). To avoid a conflict, generate a new MAC address (`--unique 1`), cut the network link (`link_down=1`), assign no IP, and do not start it right after restoring (`--start 0`).

```bash
pct help restore
```

```bash
pct restore 110 local:backup/vzdump-lxc-109-2026_11_22-13_25_49.tar.zst \
  --storage local-lvm \
  --unique 1 \
  --net0 name=eth0,bridge=vmbr0,link_down=1,ip=manual,ip6=manual \
  --start 0
```

About 1.7GiB was read and LXC 110 was created.

## 5.3 Checking the Network Settings

```bash
echo "===== RESTORED CT STATUS ====="
pct status 110

echo "===== RESTORED CT CONFIG ====="
pct config 110

echo "===== PRODUCTION CT STATUS ====="
pct status 109
```

LXC 110 was stopped and had a new MAC address. However, **the IP in `net0` had reverted to the value in the backup (192.168.0.151 and the same IPv6 as production), and it had `onboot: 1`.** The `--net0` given at restore time was overwritten when it was merged with the configuration in the backup. **Do not start LXC 110 yet.** Fix only LXC 110 (production LXC 109 is not touched).

> **Caution**: The `hwaddr` below is the new MAC address shown by `pct config 110` in the original build. When you run it, use the value shown in your own environment.

```bash
pct set 110 \
  --net0 name=eth0,bridge=vmbr0,hwaddr=BC:24:11:91:B7:76,link_down=1,ip=manual,ip6=manual \
  --onboot 0
```

```bash
echo "===== TEST CT 110 CONFIG ====="
pct config 110 | grep -E '^(hostname|net0|onboot|rootfs|memory|cores):'

echo "===== TEST CT 110 STATUS ====="
pct status 110

echo "===== PRODUCTION CT 109 STATUS ====="
pct status 109
```

```text
net0: name=eth0,bridge=vmbr0,hwaddr=BC:24:11:91:B7:76,ip=manual,ip6=manual,link_down=1,type=veth
onboot: 0
===== TEST CT 110 STATUS =====
status: stopped
===== PRODUCTION CT 109 STATUS =====
status: running
```

## 5.4 Starting It and Checking PostgreSQL

```bash
pct start 110
echo "===== TEST CT STATUS ====="
pct status 110
```

It became `status: running`. The network is cut off, so its IP address does not conflict with production LXC 109.

```bash
echo "===== POSTGRESQL SERVICE STATUS ====="
pct exec 110 -- systemctl is-active postgresql@17-main

echo "===== POSTGRESQL CLUSTER STATUS ====="
pct exec 110 -- pg_lsclusters

echo "===== POSTGRESQL PROCESS ====="
pct exec 110 -- pgrep -a postgres
```

`postgresql@17-main` was `active`, cluster `17/main` (port 5432) was `online`, and the checkpointer, walwriter, autovacuum and other processes were running. **PostgreSQL 17 started with the data restored from the backup.**

## 5.5 Reading the Data

```bash
pct exec 110 -- runuser -u postgres -- psql -X -d postgres -c "
SELECT datname, pg_size_pretty(pg_database_size(datname)) AS size
FROM pg_database
WHERE datallowconn
ORDER BY datname;
"

pct exec 110 -- runuser -u postgres -- psql -X -d security_workbench -c "
SELECT
  COUNT(*) AS total_records,
  COUNT(DISTINCT event_id) AS unique_event_ids,
  MIN(event_timestamp) AS oldest_event,
  MAX(event_timestamp) AS newest_event
FROM incident.alert_events;
"
```

In LXC 110, `incident.alert_events` in `security_workbench` (26MB) had 55,867 rows (55,867 distinct IDs); the oldest event was 2026-11-17 20:14:42 and the newest 2026-11-22 04:21:28. Compare with production LXC 109 (reads only).

```bash
pct exec 109 -- runuser -u postgres -- psql -X -d security_workbench -c "
SELECT
  COUNT(*) AS total_records,
  COUNT(DISTINCT event_id) AS unique_event_ids,
  MIN(event_timestamp) AS oldest_event,
  MAX(event_timestamp) AS newest_event,
  pg_size_pretty(pg_database_size('security_workbench')) AS database_size
FROM incident.alert_events;
"
```

| Item | Restored LXC 110 | Production LXC 109 |
|---|---:|---:|
| Rows | 55,867 | 55,869 |
| Distinct IDs | 55,867 | 55,869 |
| DB size | 26MB | 26MB |
| Oldest event | Same | Same |
| Newest event | 04:21:28 | 04:52:28 |

The difference is 2 events, which entered production after the backup was taken. **We confirmed that the backup can actually be restored.**

# Chapter 6: Deleting the Test LXC

## 6.1 Stopping It

```bash
pct shutdown 110 --timeout 60
echo "===== TEST CT STATUS ====="
pct status 110
echo "===== PRODUCTION CT STATUS ====="
pct status 109
```

LXC 110 was `stopped` and production LXC 109 `running`.

## 6.2 Deleting It

The test with LXC 110 is done, so it is deleted to free its 50GB allocation (in the original build, we confirmed whether to delete or keep it, and chose to delete). Only LXC 110 is deleted; the three backups are not.

```bash
pct help destroy
```

LXC 110 is stopped, so it is deleted without `--force`, `--purge` or `--destroy-unreferenced-disks`.

```bash
pct destroy 110
```

```text
  Logical volume "vm-110-disk-0" successfully removed.
```

```bash
echo "===== TEST CT 110 ====="
pct status 110

echo "===== PRODUCTION CT 109 ====="
pct status 109

echo "===== BACKUP FILES ====="
pvesm list local --content backup
```

LXC 110 gave `Configuration file 'nodes/pve/lxc/110.conf' does not exist` (deleted), LXC 109 was `running`, and all three backups remained.

# Closing Notes

In Part 37 we backed up LXC 109 and tested that it can be restored.

| Item | Result |
|---|---|
| Backup | `vzdump-lxc-109-2026_11_22-13_25_49.tar.zst` (`local`, snapshot, zstd, 17 seconds, about 472MB) |
| Archive check | zstd and tar both succeeded, 37,918 entries |
| Recognized by Proxmox | Configuration read via the volume ID |
| Restore test | Restored to LXC 110 and started with the network cut off; PostgreSQL 17 started and 55,867 rows could be read |
| Difference from production | 2 events (entered after the backup) |
| Cleanup | LXC 110 deleted; the three backups kept |

Three issues remain.

1. The backups are on the same NVMe as production, so they are no protection if that disk fails
2. There are no scheduled backups or generation management
3. LVM-thin has no automatic extension protection

In Part 38 we investigate LVM-thin capacity and prepare TrueNAS as the backup destination.

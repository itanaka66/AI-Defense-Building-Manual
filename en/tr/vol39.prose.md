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

⟦C0⟧

`/mnt/pve/backup` was mounted over NFS, but it was not yet registered as Proxmox storage. Find out where this mount is managed.

⟦C1⟧

`/etc/fstab` had nothing, but `/etc/systemd/system/mnt-pve-backup.mount` (`Description=Mount storage 'backup' under /mnt/pve`) existed. **This unit file pointed not to NFS but to a local ext4 disk (UUID `8cab893f-75f0-478d-842b-e94558853d14`).**

## 1.2 Checking the Mismatch

⟦C2⟧

The actual mount was `192.168.0.254:/mnt/backup` (NFS), and the settings systemd currently held were also NFS. No disk with that UUID exists.

⟦C3⟧

The file had not changed since May 24 and still had `Type=ext4` and `What=/dev/disk/by-uuid/8cab893f-…`. There were no overriding settings (drop-ins) either.

⟦C4⟧

The current NFS mount works correctly (systemd remembers the NFS mounted by hand). However, **if the host is rebooted as it is, the file's ext4 settings will be loaded.** Make the file match the NFS settings.

> **Caution**: Here we do not run `daemon-reload`, unmount, or reboot.

## 1.3 Making the Unit File NFS

Back up the current file, rewrite it, and check it with `systemd-analyze verify`.

⟦C5⟧

The backup (`/root/mnt-pve-backup.mount.before-nfs-20261122`) was created, and the rewritten file gave `VERIFY_EXIT=0`.

## 1.4 Making systemd Load It

The current NFS mount is left running; it is not remounted or unmounted.

⟦C6⟧

⟦C7⟧

The file and the running settings now match, and NFS will be mounted at boot as well.

# Chapter 2: Registering as Proxmox Storage

## 2.1 Is the Name Free?

The storage ID will be `truenas-backup`.

⟦C8⟧

`NO_COLLISION`.

## 2.2 Registering

Register it as "directory" storage using the existing NFS mount, so that Proxmox does not mount it a second time. The content is `backup` only (not used for VM disks and the like), and `--is_mountpoint 1` is added. This prevents backups from being written to the empty local directory when NFS is not mounted. Just before registering, check the mount's source and type, and register only if they match.

⟦C9⟧

`SOURCE=192.168.0.254:/mnt/backup`, `FSTYPE=nfs`, and the exit code was `0`.

⟦C10⟧

⟦C11⟧

`truenas-backup` was `active` with about 1.89TiB free, and the list of backups was still empty. `/mnt/pve/backup/dump` was also created.

# Chapter 3: Investigating What to Back Up

## 3.1 VMs and LXCs

⟦C12⟧

> **Caution**: **VM 100 (TrueNAS) is the very server that provides this NFS destination.** Writing its own backup to its own NFS would make it impossible to restore if it broke (a circular dependency), so it is not a target for backups to `truenas-backup`. How to protect TrueNAS itself is considered separately.

## 3.2 Disk Configuration

⟦C13⟧

⟦C14⟧

| Target | Points to note |
|---|---|
| VM 220 security-core, VM 230 ai-defense-manager | The core of this system; high priority to protect |
| LXC 109 postgresql | No additional mounts, 50GB. Needs a logical DB backup in addition to the container backup |
| VM 101 | Its GPU is passed through over PCI; when restoring, the GPU assignment and the host's drivers must be checked again |
| VM 220 | Uses two networks: `vmbr0` and the internal `vmbr1` |
| LXC 208, 209 | Mount the host's `/opt/nvidia-lxc-570` (about 72MB) via `mp8`. This is not included in LXC backups, so protect it separately |

## 3.3 Space Actually Used

⟦C15⟧

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

⟦C16⟧

PostgreSQL was 17.11; the largest DB was `agent_memory` (about 205MB), followed by `novel` (about 78MB). `archive_mode` was `off`, and WAL was about 32MB.

## 4.2 Roles, Tablespaces and Extensions

Password information is not shown.

⟦C17⟧

| Item | Result |
|---|---|
| `pg_dump` / `pg_dumpall` | 17.11, same as the server |
| Roles | 33 (`wazuh_collector` is an ordinary login role) |
| Tablespaces | Only `pg_default` and `pg_global` |
| Extensions | `plpgsql` and `vector` 0.8.7 (used in `easywrider`, `postgres` and `vector_db`) |

## 4.3 Data Volume and NFS Capacity

⟦C18⟧

The data was 475MB (`base` 442MB, WAL 33MB), and pgvector 0.8.7 was installed. The NFS has about 1.9TB free.

## 4.4 LXC 109 Snapshots

⟦C19⟧

⟦C20⟧

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

⟦C21⟧

There were no Proxmox backup jobs, no cron for PostgreSQL, and no backup timers (`/etc/cron.d/vzdump` is the standard file and contains only comments).

The times were decided as follows (Japan time).

| Time | Task |
|---|---|
| Daily 02:00 | PostgreSQL logical backup |
| Daily 03:00 | LXC 109 snapshot backup |
| Every Sunday | That day's backup becomes the weekly generation |
| 1st of every month | That day's backup becomes the monthly generation |

## 5.2 Proxmox's Version and Backup Job Features

⟦C22⟧

Proxmox VE was 8.4.20, systemd 252, and backup jobs were `[]`.

⟦C23⟧

Generations can be kept with Proxmox's standard feature (`--prune-backups 'keep-daily=7,keep-weekly=4,keep-monthly=3'`). When the daily, weekly and monthly periods overlap, the number actually kept may be less than 14.

## 5.3 Checking the Time

⟦C24⟧

The Proxmox host was `Timezone=Asia/Tokyo` and synchronized with NTP, and `*-*-* 03:00:00` was interpreted as 03:00 every day (Japan time).

# Chapter 6: Registering the LXC 109 Job While Disabled

Because it is registered disabled (`--enabled 0`), this operation performs no backup and the schedule does not run.

> **Run on: pve**

⟦C25⟧

It finishes without output. Check what was registered.

⟦C26⟧

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

⟦C27⟧

Only `/mnt/pve/backup` and `/mnt/pve/backup/dump` existed (both `root:root`).

⟦C28⟧

LXC 109 is running, and `pg_dump`, `pg_dumpall`, `psql` and `runuser` are available. Both LXC 109 and the Proxmox host are `Asia/Tokyo`. There were 17 DBs excluding templates (`agent_db`, `agent_memory`, `aiagent`, `aipmo`, `cerebrum`, `easywrider`, `movie`, `nfaipmo`, `novel`, `orchivio`, `postgres`, `security_workbench`, `tester`, `vector_db`, `winfilemgr`, `writer`, `writers`).

⟦C29⟧

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

⟦C30⟧

All three were `NOT_EXISTS`, and `*-*-* 02:00:00` was interpreted as 02:00 every day (Japan time).

⟦C31⟧

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

⟦C32⟧

⟦C33⟧

The script is placed as `700`, readable and executable by root only, and passed the syntax check. **It has not been run yet.**

## 7.5 Can Hard Links Be Created on NFS?

Weekly and monthly generations are created as hard links to the daily files, so this assumes that hard links can be created on TrueNAS's NFS. Create two temporary files (the original and a link), check that they have the same inode, and delete them immediately. Backup data is not touched.

⟦C34⟧

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

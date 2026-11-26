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

⟦C0⟧

Confirm that `pve` is shown before continuing.

## 1.2 Backup Jobs and Storage

⟦C1⟧

Backup jobs were `--- []` (none). `qm config 151` showed nothing (151 is the last part of the IP address, not a VM number).

> **Note**: `pvesm status` always prints the LVM error `no such logical volume windows_d/windows_d`. It is a separate problem from this work and is not fixed here.

⟦C2⟧

The VMs were 100 (TrueNAS), 101 (ollama-gpu), 102, 104, 126, 220 (security-core) and 230 (ai-defense-manager); the PostgreSQL server is not a VM. PostgreSQL runs in **LXC 109**.

## 1.3 LXC 109's Configuration

⟦C3⟧

| Item | Value |
|---|---|
| Disk | `local-lvm:vm-109-disk-0`, 50G |
| Type | Unprivileged LXC (`unprivileged: 1`) |
| Additional mounts | None |
| IP address | 192.168.0.151/24 |
| Start at boot | `onboot: 1` |

## 1.4 Where Backups Can Be Stored

⟦C4⟧

The only storage that can hold `backup` content was `local` (`/var/lib/vz`). `local-lvm`, `RAID_A`, `RAID_B` and the others are for VM and LXC disks.

⟦C5⟧

`local` is actually the Proxmox root file system (`/dev/mapper/pve-root`, 68G free of 94G), and `/var/lib/vz/dump/` was empty.

⟦C6⟧

LXC 109 used 1.7G of 49G, and PostgreSQL's data was 473M. `local` has enough space. However, `local` is on the same device as the Proxmox root, so it is no protection if that disk fails (Part 38 prepares a separate destination).

# Chapter 2: The Backup Method

## 2.1 vzdump's Documentation

> **Note**: `vzdump --help` gives `Unknown option: help`. Read the documentation with `man vzdump`.

⟦C7⟧

⟦C8⟧

The manual page was `/usr/share/man/man1/vzdump.1.gz` and Proxmox VE was `pve-manager/8.4.20`. Extract the main options.

⟦C9⟧

| Option | Meaning |
|---|---|
| `--mode snapshot` | Create the backup from a storage snapshot. An LXC pauses briefly while the snapshot is taken (it is not entirely without interruption) |
| `--mode suspend` / `stop` | Create it with the guest suspended / stopped |
| `--compress zstd` | Compress with zstd |
| `--storage` | Destination |

For an LXC, `snapshot` requires its disks to be on storage that supports snapshots.

## 2.2 Can local-lvm Take Snapshots?

⟦C10⟧

`local-lvm` (LVM-thin) was `active`, using about 514GB of about 833GB (61.66%). LVM-thin supports snapshots.

⟦C11⟧

`pve/data` was 61.66% used for data and 2.18% for metadata, with room to spare. Note that `local` and `local-lvm` are both on the same NVMe (`/dev/nvme0n1p3`).

# Chapter 3: Backing Up LXC 109

In the original build, approval was obtained before running this. The destination is `local`, the mode `snapshot`, compression `zstd`, and old backups are not deleted (`--remove 0`). LXC 109 pauses briefly while the snapshot is taken.

> **Run on: pve**

⟦C12⟧

⟦C13⟧

It finished in 17 seconds and created `/var/lib/vz/dump/vzdump-lxc-109-2026_11_22-13_25_49.tar.zst` (about 472MB).

> **Note**: LVM-thin prints two warnings: "protection against thin pools running out of space (automatic extension) is not enabled" and "the total allocated to thin volumes exceeds the actual capacity". The backup did not fail, but this is a capacity management issue (investigated in Part 38).

# Chapter 4: Checking the Backup

## 4.1 Is the Archive Intact?

⟦C14⟧

| Item | Result |
|---|---:|
| Size | 495,442,661 bytes |
| zstd test | Succeeded (0) |
| tar listing | Succeeded (0) |
| Number of entries | 37,918 |

## 4.2 Does It Contain PostgreSQL's Data?

⟦C15⟧

It contained `./var/lib/postgresql/17/main/base/…` and `./etc/postgresql/…`. The first `pvesm extractconfig` fails with `unable to parse volume ID`, because this command takes a Proxmox volume ID (`local:backup/<file name>`), not a file path.

## 4.3 Does Proxmox Recognize It as a Backup?

⟦C16⟧

With the volume ID, LXC 109's configuration (host name `postgresql`, 2 cores, 4GB, 50GB, 192.168.0.151, unprivileged) could be read. Besides this backup, the list also showed backups `13_22_41` and `13_24_39`, three in total. None of them is deleted.

# Chapter 5: Restoring to LXC 110 and Testing

In the original build, approval was obtained before running this, because a new LXC is created and uses space.

## 5.1 Number and Space

⟦C17⟧

`CTID_110=FREE`, and `local-lvm` had about 319GiB free.

## 5.2 Restoring

The backup contains the same IP address as production (192.168.0.151). To avoid a conflict, generate a new MAC address (`--unique 1`), cut the network link (`link_down=1`), assign no IP, and do not start it right after restoring (`--start 0`).

⟦C18⟧

⟦C19⟧

About 1.7GiB was read and LXC 110 was created.

## 5.3 Checking the Network Settings

⟦C20⟧

LXC 110 was stopped and had a new MAC address. However, **the IP in `net0` had reverted to the value in the backup (192.168.0.151 and the same IPv6 as production), and it had `onboot: 1`.** The `--net0` given at restore time was overwritten when it was merged with the configuration in the backup. **Do not start LXC 110 yet.** Fix only LXC 110 (production LXC 109 is not touched).

> **Caution**: The `hwaddr` below is the new MAC address shown by `pct config 110` in the original build. When you run it, use the value shown in your own environment.

⟦C21⟧

⟦C22⟧

⟦C23⟧

## 5.4 Starting It and Checking PostgreSQL

⟦C24⟧

It became `status: running`. The network is cut off, so its IP address does not conflict with production LXC 109.

⟦C25⟧

`postgresql@17-main` was `active`, cluster `17/main` (port 5432) was `online`, and the checkpointer, walwriter, autovacuum and other processes were running. **PostgreSQL 17 started with the data restored from the backup.**

## 5.5 Reading the Data

⟦C26⟧

In LXC 110, `incident.alert_events` in `security_workbench` (26MB) had 55,867 rows (55,867 distinct IDs); the oldest event was 2026-11-17 20:14:42 and the newest 2026-11-22 04:21:28. Compare with production LXC 109 (reads only).

⟦C27⟧

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

⟦C28⟧

LXC 110 was `stopped` and production LXC 109 `running`.

## 6.2 Deleting It

The test with LXC 110 is done, so it is deleted to free its 50GB allocation (in the original build, we confirmed whether to delete or keep it, and chose to delete). Only LXC 110 is deleted; the three backups are not.

⟦C29⟧

LXC 110 is stopped, so it is deleted without `--force`, `--purge` or `--destroy-unreferenced-disks`.

⟦C30⟧

⟦C31⟧

⟦C32⟧

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

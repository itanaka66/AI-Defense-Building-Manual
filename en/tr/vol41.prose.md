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

⟦C0⟧

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

⟦C1⟧

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

⟦C2⟧

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

⟦C3⟧

With `ENABLE_EXIT=0`, the job is enabled. Both backups are now automatic.

| Time | Backup | Target |
|---|---|---|
| Daily 02:00 | PostgreSQL logical backup (systemd timer) | the 17 databases in LXC 109 |
| Daily 03:00 | Proxmox backup (`lxc109-daily`, snapshot, zstd) | LXC 109 |

# Chapter 3: Investigating the Thin Pool

If the thin pool fills up, disk reads and writes of several VMs and LXCs are affected. Here we change no settings and only read the current state.

## 3.1 Usage and Automatic Extension Settings

> **Run on: pve**

⟦C4⟧

Data usage of thin pool `pve/data` is **61.69%** and metadata usage is **2.18%**, so capacity will not run out immediately. There was no automatic-extension setting, and VG `pve` had 16GiB free.

## 3.2 Is There Capacity to Add?

> **Run on: pve**

⟦C5⟧

⟦C6⟧

The third NVMe partition runs to the end of the disk, and there is no unallocated space. The other physical disks were each already assigned to other VGs.

Extending the 794GiB thin pool by just 5% needs about 39.7GiB, so with only 16GiB free we do not set up automatic extension. We also do not borrow disks from other VGs or shrink existing storage. We will set it up when the PVE disk is enlarged in the future (it is listed as a check item in the operations manual).

# Chapter 4: Restoring to CTID 310

## 4.1 Checks Before Restoring

> **Run on: pve**

⟦C7⟧

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

⟦C8⟧

With `RESTORE_EXIT=0`, the rootfs of CTID 310 (50GiB) was created and about 1.7GiB of data was extracted. The container remains stopped.

However, the restored configuration **kept the settings from the backup (the same IP address as production)**, not the settings given with `--net0` (the same behavior as in Part 37). It has not been started yet, so no IP address clash has occurred.

## 4.3 Cutting Off the Network

Before starting it, explicitly cut off `net0` of CTID 310.

> **Run on: pve**

⟦C9⟧

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

⟦C10⟧

The start returned `START_EXIT=0`. Right after starting, SQL connections are refused with `the database system is starting up`.

## 5.2 Confirming Startup Has Finished

> **Run on: pve**

⟦C11⟧

The end of the log has `database system is ready to accept connections`, and `pg_isready` also returned `accepting connections`. `automatic recovery in progress` in the log is the replay of WAL that had not been completed at backup time; after it, the end of recovery and the start of accepting connections are recorded.

`systemctl is-active postgresql` may show `inactive`, but on Debian the parent service `postgresql.service` is designed to be `active (exited)`, and the actual cluster service is `postgresql@17-main.service`. This is not an error.

## 5.3 Databases and Extensions

> **Run on: pve**

⟦C12⟧

- PostgreSQL 17.11 started and all 17 databases could be connected to
- `vector 0.8.7` in three: `easywrider`, `postgres` and `vector_db`
- `plpgsql 1.0` in the other databases
- Database sizes also match the original records

## 5.4 Roles and Permissions

Password hashes are not displayed.

> **Run on: pve**

⟦C13⟧

`wazuh_collector` had `SUPERUSER`, `CREATEDB`, `CREATEROLE`, `REPLICATION` and `INHERIT` all disabled, and was not a member of any role. Its only table permission is `INSERT` on `security_workbench.incident.alert_events`.

`information_schema.role_table_grants` alone does not show permissions via PUBLIC or per-column permissions, so we also check the effective permissions.

> **Run on: pve**

⟦C14⟧

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

⟦C15⟧

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

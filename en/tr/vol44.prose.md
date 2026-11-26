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

⟦C0⟧

| Item | Result |
|---|---|
| Backup catalog | two generations of LXC 109 registered (November 22 20:28, November 23 09:43) |
| `lxc109-daily` | daily 03:00, snapshot, zstd, `truenas-backup`, 7 daily, 4 weekly, 3 monthly, `/var/tmp`, enabled |
| `mnt-pve-backup.mount` | `Requires=truenas-nfs-ready.service`, `After=truenas-nfs-ready.service` |
| `truenas-nfs-ready.service` | `inactive/dead` (a oneshot service that finished normally) |

The archives are not only on NFS but are also registered in Proxmox's backup catalog.

## 1.2 Restore Method and Settings Inside the Archive

> **Run on: pve**

⟦C1⟧

The settings recorded in the archive were the same as the current CT109 (Debian, amd64, 2 vCPUs, 4GB memory, 50GB root disk, unprivileged, `nesting=1,keyctl=1`, `192.168.0.151/24`, `onboot=1`). We check with a different CTID without overwriting the production CT109.

## 1.3 CTID 310 and the Thin Pool

> **Run on: pve**

⟦C2⟧

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

⟦C3⟧

CTID 310 is `running`, the production CTID 109 is also `running`, and CTID 310 remains `link_down=1`, `onboot=0`.

## 2.2 PostgreSQL State

> **Run on: pve**

⟦C4⟧

PostgreSQL 17 `main` is `online` and accepts connections on `127.0.0.1:5432`; `eth0` is `DOWN` and there are no routes. PostgreSQL also listens on `0.0.0.0:5432` and `[::]:5432`, but the virtual NIC is disconnected, so nothing reaches it from outside. We keep this isolation during the checks.

## 2.3 List of Databases

> **Run on: pve**

⟦C5⟧

PostgreSQL 17.11, cluster `17/main` `online`, 17 databases, and `pg_is_in_recovery()` was `false`. `postgresql.service` being `active (exited)` is normal for Debian's management service.

## 2.4 Owners, Extensions, Indexes and Logs

> **Run on: pve**

⟦C6⟧

Each database has an owner, `vector` is `0.8.7` in `easywrider`, `postgres` and `vector_db`, and there were zero invalid indexes (`indisvalid=false` or `indisready=false`) in any database.

In the role list command, `!~` was interpreted by Bash as history expansion, so the condition excluding system roles did not take effect. This is not data corruption. We retrieve it again with a corrected command and also check whether `pg_amcheck` exists.

> **Run on: pve**

⟦C7⟧

| Item | Result |
|---|---|
| Roles | 18 retrieved |
| CTID 310 rootfs | 45GB free |
| `pg_amcheck` | not installed (not installed here) |

## 2.5 Sorting Out the Errors in the Log

The log contained duplicate-key errors on `alert_events_pkey` (records of duplicate INSERTs by the Wazuh Collector), errors from diagnostic SQL on `security_workbench`, and `FATAL` messages from connections during startup.

> **Run on: pve**

⟦C8⟧

Putting the times in order, these were things already recorded in production before the backup, failed diagnostic queries, or connections made during startup; none of them indicates database corruption.

# Chapter 3: Comparing with Production

CT109 has kept running since the backup, so we do not require the data to be exactly identical. We compare whether the structure is the same.

## 3.1 Database Names and Sizes

> **Run on: pve**

⟦C9⟧

Both CT109 and CT310 have 17 databases, all with the same names. Sizes differ by a few KB to about 1MB, which is considered to be due to updates in production after the backup. CT310 remains `onboot: 0`, `link_down=1`.

## 3.2 Numbers of Tables and Views

`information_schema.tables` only sees the database you are connected to, so we connect to each database and count.

> **Run on: pve**

⟦C10⟧

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

⟦C11⟧

The total of 534 indexes (0 invalid or not ready), the numbers of primary keys, foreign keys, unique constraints and CHECK constraints, and the names and versions of the extensions (`vector 0.8.7` in 3, `plpgsql 1.0` in 17) were all the same.

## 3.4 Schema Definitions

Beyond counts, we compare table definitions, columns, data types, and index and constraint definitions. We take the SHA256 of the output of `pg_dump --schema-only`. The data itself is not output.

> **Run on: pve**

⟦C12⟧

For 16 of the 17, the SHA256 of CT109 and CT310 matched. Only `novel` differed.

## 3.5 The Difference in `novel`

> **Run on: pve**

⟦C13⟧

There were two columns present in CT109 but not in CT310 (`ollama_api_key` and `controller_ollama_api_key`, `character varying(500)`). Without touching the column values (API keys), we check which table they belong to.

> **Run on: pve**

⟦C14⟧

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

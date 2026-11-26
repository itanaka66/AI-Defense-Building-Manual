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

⟦C0⟧

⟦C1⟧

## 1.2 Where the Collector Connects

From the Collector's `DB_CONFIG`, extract only the connection destination fields. `DB_CONFIG` contains values that reference environment variables and the like, so the file is parsed as Python syntax and only the values of fixed fields (`host`, `hostaddr`, `port`, `dbname`, `database`, `user`) are shown. Passwords and the like are not shown.

⟦C2⟧

⟦C3⟧

# Chapter 2: The Table and Permissions

## 2.1 Table Structure

> **Run on: postgresql**

⟦C4⟧

| Item | Result |
|---|---|
| Primary key | `event_id` (the same event cannot be inserted twice) |
| Indexes | 5 |
| CHECK constraints | 3 (`rule_level` 0–16, `srcport` 0–65535, `mitre` is a JSON object) |
| Raw log columns | None (no `full_log` or similar; only fixed fields are stored) |

## 2.2 Permissions of the Collector's Role

⟦C5⟧

⟦C6⟧

The Collector can write events but cannot read, change or delete existing data. This is an important safeguard that makes it hard to rewrite stored events even if the Collector is compromised.

⟦C7⟧

Only `can_login` was `t`; superuser, role inheritance, permission to create roles or databases, replication and bypassing RLS were all `f`. These permissions are not changed.

# Chapter 3: Data Contents

## 3.1 Malformed Values and Duplicates

Individual events (IP addresses, agent names and so on) are not shown; only aggregate values are examined.

⟦C8⟧

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

⟦C9⟧

| Period | Rows | Average | Median | 95% |
|---|---:|---:|---:|---:|
| Last 30 minutes | 15 | 0.86 s | 0.91 s | 0.99 s |
| Last 24 hours (excluding the 30 minutes) | 35,705 | 18,587.53 s | 1.07 s | 322,119.38 s |
| Older | 20,098 | 21,042.09 s | 11,725.46 s | 61,876.70 s |

The last 30 minutes were ingested in under a second, so current ingestion is normal. The 24-hour median is also about 1 second; the average is large because of old events added later.

# Chapter 4: Size and Connections

## 4.1 Table Size and VACUUM

⟦C10⟧

The table was 12MB and the indexes 6008kB, 18MB in total. About 55,826 live rows and 766 dead rows (about 1.4%), and automatic VACUUM and ANALYZE were running. No manual VACUUM is needed.

## 4.2 Connection Count

⟦C11⟧

14 connections against a limit of 100; `idle in transaction` (connections stuck with an open transaction) was 0, and the Collector had 1 connection.

## 4.3 Database Size

⟦C12⟧

The whole of `security_workbench` was 26MB.

# Chapter 5: WAL and Checkpoints

## 5.1 Replication Slots

An unused slot would keep WAL from being removed so that it piles up.

⟦C13⟧

There were 0 slots.

## 5.2 WAL and Checkpoint Settings

⟦C14⟧

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

⟦C15⟧

The columns were `num_timed`, `num_requested`, `restartpoints_timed`, `restartpoints_req`, `restartpoints_done`, `write_time`, `sync_time`, `buffers_written` and `stats_reset`.

⟦C16⟧

Since statistics began on 2026-11-17, there had been 1,349 scheduled checkpoints and only 4 requested ones. About 241MB was written and sync time totaled about 28 seconds; checkpoints are stable.

## 5.4 WAL Files

⟦C17⟧

WAL was 32MB (two 16MB files), small against the 1GB limit, and not piling up.

# Chapter 6: Looking for Backups

## 6.1 Archiving and the Data Location

⟦C18⟧

The data is in `/var/lib/postgresql/17/main` (PostgreSQL 17); `archive_mode` was `off` and `archive_command` was `(disabled)`.

## 6.2 Backup Services and Files

⟦C19⟧

What was found was only `dpkg-db-backup.timer` (a backup of Debian's package management database, not of PostgreSQL) and the PostgreSQL service itself. pgBackRest, Barman, Borg, Restic and the like were not present either. Look only at file names, times and sizes (the contents are not read).

⟦C20⟧

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

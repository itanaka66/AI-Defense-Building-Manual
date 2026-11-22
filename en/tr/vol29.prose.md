---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 2"
subtitle: "Part 29: Restarting the Collector Without Missing Any Events"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 29 of Volume 2 of the "AI Autonomous Cyber Defense System Build Manual". In Part 28 we found that the Collector had stopped starting, for safety, because "the file it had been reading (inode 5409383) cannot be found". Here we do the following.

1. Find out what happened to the previous file, using the log files, compressed files and checksums
2. Confirm that the saved read position was **the end** of the previous file
3. After confirming PostgreSQL's mechanism for preventing duplicates, rewrite the read position to "the beginning of the current `alerts.json`"
4. Start the Collector and confirm that the events were ingested into PostgreSQL

Arbitrarily advancing the read position to the end of the current file would leave events unread. We proceed only after confirming each piece of evidence.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **postgresql**: LXC 109 (192.168.0.151), OS user `postgres`
- Alert text is not shown. The PostgreSQL password is read from `.pgpass` and not shown.
- inodes, sizes, times and counts are those at build time. Replace them with the values in your environment.

# Chapter 1: Looking for the Previous File

> **Run on: VM 220**

## 1.1 The Log Files

⟦C0⟧

Compressed JSON logs for November 17–20 (`2026/Nov/ossec-alerts-*.json.gz`) and the current log for the 21st remained. inode 5409383 did not exist. The Collector's search covers only files ending in `.json`, not `.json.gz`.

⟦C1⟧

There were also no files still held open after being deleted.

⟦C2⟧

The JSON logs switch daily: the files for the 17th–20th have been compressed, and the 21st is the current `alerts.json`.

## 1.2 The Size of the 20th's File

⟦C3⟧

The decompressed size of the 20th's file was **6,433,808 bytes**, the same as the saved read position.

⟦C4⟧

The compressed file is not corrupted (`GZIP_TEST_EXIT_CODE=0`). While decompressing (without writing to disk), examine the number of lines and their form.

⟦C5⟧

| Item | Result |
|---|---|
| Decompressed size | 6,433,808 bytes (matches the saved position) |
| Lines | 10,293 |
| Lines not readable as JSON | 0 |
| Final newline | Present |

## 1.3 Times and Checksum

⟦C6⟧

The state file was saved at 23:54:26 on November 20 (UTC), and the 20th's file was compressed at 00:00:10 on November 21 (UTC). When the state was saved, the 20th's file was the current file.

Look at the checksum file created by Wazuh (37 bytes).

⟦C7⟧

It recorded the SHA-256 of the 20th's file before compression.

⟦C8⟧

Compute the SHA-256 while decompressing and compare it with the record. Replace the value with the value in your environment's `.sum`.

⟦C9⟧

The result was `CHECKSUM_MATCH: True`.

## 1.4 The Current File

⟦C10⟧

The 21st's file also had no unreadable lines. Compare the times at the boundary.

⟦C11⟧

| Item | Time (UTC) |
|---|---|
| Last event in the 20th's file | 11/20 23:54:26.205 |
| State file saved | 11/20 23:54:26.714 |
| First event in the 21st's file | 11/21 00:09:26.253 |

The saved read position corresponds to the end of the 20th's file. Therefore **reading the current `alerts.json` (inode 5409517) from the beginning (offset 0) is sufficient**. However, it cannot be proved that there were no alerts during these 15 minutes.

## 1.5 The Mechanism That Prevents Duplicates

Part of the 21st's file may have been ingested while the Collector was still running. Confirm that re-reading from the beginning will not insert anything twice.

⟦C12⟧

The result at build time (key points) was as follows: `event_id` was the primary key (unique).

⟦C13⟧

Also check the processing on the Collector side.

⟦C14⟧

⟦C15⟧

⟦C16⟧

1. Each event is INSERTed in its own transaction
2. If `event_id` is a duplicate (SQLSTATE `23505`), the insert is rolled back and it moves on to the next
3. After either a successful INSERT or a duplicate, the read position is saved
4. If the DB or saving fails, it goes back to the start of the line and retries
5. When the file switches, it saves the new inode and offset 0 first, then switches

# Chapter 2: Rewriting the Read Position

> **Run on: VM 220**

## 2.1 Stopping It

⟦C17⟧

⟦C18⟧

Confirm `inactive` and `MainPID=0`, so that no process will rewrite the state file.

## 2.2 Backup

⟦C19⟧

Confirm `BACKUP_VERIFY=OK`.

## 2.3 Rewriting

The new read position is as follows.

⟦C20⟧

Rewrite it only if the current state file is as expected (inode 5409383, offset 6433808) and the inode of `alerts.json` is 5409517. Otherwise it stops without doing anything. The rewrite writes a temporary file and then swaps it in, keeping the original permissions and owner.

⟦C21⟧

## 2.4 Starting It

⟦C22⟧

⟦C23⟧

At build time it was `active` and `running` (PID 13542). `NRestarts=874` is the total count up to when it was stopped.

⟦C24⟧

⟦C25⟧

The log after starting contained the following two lines.

⟦C26⟧

## 2.5 Is It Reading Forward?

⟦C27⟧

The read position (858,191) became equal to the file size, showing that it had read to the end.

⟦C28⟧

There were no errors or warnings after starting.

# Chapter 3: Confirming in PostgreSQL

> **Run on: postgresql** (OS user `postgres`)

`wazuh_collector` has only the INSERT privilege, so rather than adding privileges, run read-only SQL as the PostgreSQL administrator.

⟦C29⟧

There were 143 events in the last 30 minutes. Check whether there is a column for the ingestion time.

⟦C30⟧

`ingested_at` existed. Count the events ingested after the time the Collector was started (10:45:16 UTC). Replace the time with the one in your environment.

⟦C31⟧

| Item | Result |
|---|---|
| Inserted after starting | 1,318 |
| Distinct `event_id` | 1,318 (no duplicates) |
| First insert | 10:45:16.110 UTC |
| Last insert | 10:58:41.944 UTC |

⟦C32⟧

There was one event in the last five minutes. That may simply be because there were few new alerts, so check on VM 220 whether anything is left unread.

> **Run on: VM 220**

⟦C33⟧

It showed `UNPROCESSED_BYTES: 0` (nothing unread).

⟦C34⟧

# Closing Notes

In Part 29 we restarted the Collector without leaving anything unread.

| Item | Result |
|---|---|
| Previous file | The 20th's compressed file; confirmed by size, lines and checksum |
| Read position | Rewritten to inode 5409517, offset 0 (backup `state.json.pre-recovery-20261121`) |
| PostgreSQL | 1,318 events inserted, 0 duplicates |
| Unread | 0 bytes |

It has not been proved that no events were lost around the rotation. Also, the hidden test directory still remains, so the Collector may stop for the same reason the next time the file switches. The next part prevents this.

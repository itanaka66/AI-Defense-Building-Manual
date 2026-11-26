---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 32: Confirming an Actual Switch and Recovering Missing Events"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 32 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". In Part 31 we added a Default ACL to the per-date directories so that the Collector can read the new file even after the logs are switched. This part does the following.

1. After the actual switch on November 22, confirm that the new file inherited the ACL and that the Collector kept reading
2. Compare the compressed archives (`.json.gz`) with the counts in PostgreSQL day by day, and look for events that were not saved
3. Recover the 1,898 events found, using the same checks and the same INSERT statement as the Collector, after a trial that is rolled back (a dry run)

The events were missing because when the Collector was first started at 11:00:48 on November 18, it began reading `alerts.json` **from the end** (the first start is designed to read from the end). The 520 events on the 17th and 1,378 events on the 18th before that time were not in PostgreSQL.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **postgresql**: LXC 109 (192.168.0.151)
- Unless otherwise noted, times are in UTC (Japan time is 9 hours ahead).

# Chapter 1: Confirming the Actual Switch

## 1.1 The New File

After 09:05 Japan time, run the last command from Part 31.

> **Run on: VM 220**

⟦C0⟧

- `ossec-alerts-21.json.gz` had been created at 00:00:11
- A new `ossec-alerts-22.json` (inode 5409424) existed, and `alerts.json` pointed to the same inode
- The new file's mode was `640`

## 1.2 ACL and Reading

⟦C1⟧

The new file had inherited `user:wazuh-collector:r-x` (effective `r--`), and `COLLECTOR_READ_TEST_EXIT=0`.

## 1.3 The Collector's Read Position

Show only the inode and position from the state file.

⟦C2⟧

⟦C3⟧

The Collector switched to the new inode without restarting and had read to the end of the file.

## 1.4 Saving to PostgreSQL

> **Run on: postgresql** (OS user `postgres`)

⟦C4⟧

Since the new file was created, 88 events (88 distinct `event_id`s) had been saved. **The switch on November 22 was handled correctly.**

# Chapter 2: Partial Lines at Switching

## 2.1 How Partial Lines Are Handled

> **Run on: VM 220**

⟦C5⟧

If the file is switched in the middle of a line (before the newline arrives), the Collector discards that line with a warning and moves to the start of the new file. However, if Wazuh writes each line in one go, this path is normally not taken.

⟦C6⟧

The Collector reads every second, and a line can be up to 1 MiB. Wazuh waits 10 seconds before switching (`day_wait=10`).

## 2.2 Are There Partial Lines in the Archives?

Check every line of the compressed archives: can it be read as JSON, and does it end with a newline?

⟦C7⟧

All 47,137 lines in the 5 files could be read as JSON, and no last line lacked a newline. No partial lines remain in the archives.

# Chapter 3: Looking for Events That Were Not Saved

## 3.1 Time Ranges of the Archives

⟦C8⟧

| File | Events | First | Last |
|---|---:|---|---|
| `ossec-alerts-17.json.gz` | 520 | 11-17 20:14:42 | 11-17 23:54:53 |
| `ossec-alerts-18.json.gz` | 2,144 | 11-18 00:00:31 | 11-18 23:53:10 |
| `ossec-alerts-21.json.gz` | 25,141 | 11-21 00:09:26 | 11-22 00:00:00 |

(The files for the 19th and 20th are shown the same way.)

## 3.2 Daily Counts in PostgreSQL

> **Run on: postgresql** (enter `psql` and switch to the database `security_workbench`)

⟦C9⟧

> **Caution**: When `psql` is started without arguments, it connects to the database `postgres`. There, `incident.alert_events` cannot be found.

⟦C10⟧

The 19th, 20th and 21st had almost the same counts as the archives. But **for the 18th, the archive had 2,144 events while PostgreSQL had 766**, and the first event was at 11:00:59. There was not a single event for the 17th.

⟦C11⟧

PostgreSQL had 0 events from before 11:00 on the 18th.

## 3.3 The Cause

> **Run on: VM 220**

⟦C12⟧

⟦C13⟧

The Collector was first started at 11:00:48 on November 18 and began reading `alerts.json` **from the end**. Events before that were never read. This is due to how the first start works, separate from the ACL and switching problems. Count the 18th's events before and after the start.

⟦C14⟧

⟦C15⟧

The 766 events after the start matched the count in PostgreSQL. All 520 events on the 17th were also before the start. The events not saved are expected to be **520 on the 17th and 1,378 on the 18th, 1,898 in total**.

# Chapter 4: Preparing the Recovery

## 4.1 Can the Collector's Checks and INSERT Statement Be Used?

The recovery uses the same checks as the Collector (the field whitelist and input validation) and the same INSERT statement.

⟦C16⟧

- `extract_event()` applies the field whitelist and input validation
- `INSERT_SQL` is the same one the Collector normally uses
- `event_id` is the primary key, so existing events are detected as duplicates (SQLSTATE `23505`)
- The Collector's role (`wazuh_collector`) needs only INSERT; no SELECT, UPDATE or DELETE permission is required

## 4.2 IDs Inside the Archives

⟦C17⟧

The 2 files contained 2,664 records; all IDs were valid and there were no duplicates.

## 4.3 A Trial That Is Rolled Back (Dry Run)

We actually INSERT into PostgreSQL, but the outer transaction is **always rolled back**. The Collector's connection settings (`DB_CONFIG`) and functions are loaded from `collector.py`. Connection settings and passwords are not shown.

⟦C18⟧

⟦C19⟧

1,898 events would be newly inserted and 766 already existed, as expected. Because it was rolled back, PostgreSQL did not change.

# Chapter 5: Recovering the 1,898 Events

Because this writes to PostgreSQL, approval was obtained before running it in the original build. It is done under these conditions.

- The normal Collector is not stopped
- Only `ossec-alerts-17.json.gz` and `ossec-alerts-18.json.gz` are processed
- Abort unless the role is `wazuh_collector`
- Everything is one transaction; if the counts differ from the dry run, everything is rolled back

> **Run on: VM 220**

⟦C20⟧

⟦C21⟧

# Chapter 6: Checks After the Recovery

## 6.1 Counts in PostgreSQL

`wazuh_collector` can only INSERT, so the check is done on the PostgreSQL server.

> **Run on: postgresql** (root)

⟦C22⟧

| Date | Events | Distinct IDs | Duplicates |
|---|---:|---:|---:|
| 2026-11-17 | 520 | 520 | 0 |
| 2026-11-18 | 2,144 | 2,144 | 0 |

All 2,664 events in the archives are saved, with no duplicates.

## 6.2 The Normal Collector

> **Run on: VM 220**

Check the service and read position with the same command as in 1.3.

⟦C23⟧

The service was `running`, the inode was 5409424, and the position and the file size were both 4,627,640 bytes, so nothing was left unread. The Collector's log recorded `Switched to new alerts.json inode` at 00:00:00 on November 22.

> **Run on: postgresql** (root)

⟦C24⟧

In the last 30 minutes, 5,753 events (5,753 distinct IDs) had been saved. Normal ingestion is also continuing.

# Closing Notes

In Part 32 we confirmed an actual switch and recovered the events that had not been saved.

| Item | Result |
|---|---|
| The switch on November 22 | The new file inherited the ACL and the Collector followed it without restarting; 88 events saved |
| Archives | 5 files, 47,137 lines, no broken or partial lines |
| Why events were missing | At the first start (11:00:48 on November 18), the Collector began reading `alerts.json` from the end |
| Recovery | 520 events on the 17th and 1,378 on the 18th, 1,898 in total, saved in one transaction after a dry run |
| After the recovery | All 2,664 events for the 17th and 18th saved, 0 duplicates; normal ingestion continuing |

In Part 33 we make the Collector's state observable with Prometheus.

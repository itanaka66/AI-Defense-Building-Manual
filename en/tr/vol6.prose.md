---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 6: Verifying Data Integrity and Auditing Operations"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 6 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". For the hardened Collector deployed in Part 5, we confirm that no duplicates occur and that every Wazuh alert is in the DB without exception, checking not just the counts but down to individual event IDs. We also audit operation across an actual date change (rotation).

## Notation

- Commands and file contents are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Each step begins with "Run on", which says where to run it. DB checks are done inside LXC 109 as the DB administrator (`postgres`) (the prompt is `root@postgresql`).
- "Example output" is the actual output from the build. Event IDs, counts, times, inodes and so on will differ in your environment.
- The contents of credentials and the state file are not shown.

## State at the End of Part 5

| Item | State |
|---|---|
| Collector | Hardened version (`/usr/local/lib/wazuh-collector/collector.py`, 18,898 bytes) |
| Service | `wazuh-collector.service` (active, starts automatically) |
| Reconciliation | Wazuh alerts and DB rows for the same period match (230) |

# Chapter 1: Guaranteeing No Duplicates

## 1.1 How Event IDs Are Implemented

**Run on: security-core VM 220 (root)**

⟦C0⟧

| Item | Implementation |
|---|---|
| `event_id` | The Wazuh alert's `id` (up to 128 characters) |
| Duplicate detection | DB unique constraint violation (SQLSTATE `23505`) |
| Handling duplicates | Skip and log |
| `ON CONFLICT` | Not used (to keep the INSERT-only privilege) |

## 1.2 Constraints on the DB Side

**Run on: LXC 109 postgresql (root)**

⟦C1⟧

| Constraint / index | Purpose |
|---|---|
| `PRIMARY KEY (event_id)` | Prevent duplicates |
| CHECK on `mitre` | Guarantee that it is a JSON object |
| CHECK on `rule_level` | Limit to 0–16 |
| CHECK on `srcport` | Limit to the range of port numbers |
| Indexes on time, level, rule and source IP | Faster searches |

Confirm that the current data has no duplicates.

⟦C2⟧

⟦C3⟧

## 1.3 Privileges of the Collector's Role

**Run on: LXC 109 postgresql (root)**

⟦C4⟧

Confirm that `wazuh_collector` has no superuser, create-DB or create-role privileges. Also check the privilege to create temporary tables, used in the next test.

⟦C5⟧

## 1.4 Testing a Duplicate Insert on a Temporary Table

Without touching the production table, insert the same ID twice into a temporary table with `wazuh_collector`'s privileges and confirm that the second insert is rejected. The whole transaction is rolled back at the end.

The temporary table's schema name changes per connection, so take the name from `pg_my_temp_schema()` and grant privileges with `\gexec` (you cannot `GRANT` on the alias `pg_temp`).

**Run on: LXC 109 postgresql (root)**

⟦C6⟧

It has succeeded if `PASS: duplicate rejected with unique_violation` is followed by `inserted_rows` and `unique_event_ids` both being `1`.

## 1.5 Testing Duplicate Handling on the Collector Side

Process the same alert twice with `process_line()` and confirm with a mock connection that the second `UniqueViolation` is handled and does not escape. The test file is readable only by root, so run it as root.

**Run on: security-core VM 220 (root)**

⟦C7⟧

⟦C8⟧

> `/tmp/wazuh-collector-hardening-test.py` is readable only by root (permissions 600). Running it as an ordinary user gives `PermissionError`.

# Chapter 2: Reconciling Wazuh and the DB Event by Event

Even if the counts match, it is not impossible that different events have been swapped. Here we reconcile down to the set of event IDs, using reads only. No services are restarted and no settings are changed.

## 2.1 The Collector's Running State and Read Position

**Run on: security-core VM 220 (root)**

⟦C9⟧

> `NRestarts` is a cumulative value that includes the restarts during the startup failure in Part 5.

⟦C10⟧

## 2.2 Basic Integrity on the DB Side

**Run on: LXC 109 postgresql (root)**

⟦C11⟧

## 2.3 Checking That the Latest Alerts Are Ingested

Show the last five alerts in `alerts.json` and check individually whether their IDs are in the DB.

**Run on: security-core VM 220 (root)**

⟦C12⟧

**Run on: LXC 109 postgresql (root)**

⟦C13⟧

Replace the IDs inside `IN` with the IDs from your environment shown by the previous command. At build time all three were inserted, and the delay from the alert occurring to its ingestion into the DB was within about one second.

## 2.4 Fixing the Range to Reconcile

Take as the range everything after the read position at which the fixed version was started in Part 5 (`2178712` at build time). Output the count, times, and first and last IDs in the range.

**Run on: security-core VM 220 (root)**

⟦C14⟧

Replace `start_offset` with your environment's value. At build time there were 413 alerts, the oldest at `2026-11-18T15:15:10.963+0000` and the newest at `2026-11-18T20:31:14.188+0000`. Count the DB rows in the same time range.

**Run on: LXC 109 postgresql (root)**

⟦C15⟧

| Item | alerts.json | PostgreSQL |
|---|---:|---:|
| Count | 413 | 413 |
| Unique event_id | 413 | 413 |
| Oldest event | 15:15:10.963 | 15:15:10.963 |
| Newest event | 20:31:14.188 | 20:31:14.188 |

# Chapter 3: Exact Match of the Sets of Event IDs

## 3.1 The Approach

Even if the counts are the same, the IDs are not necessarily the same. Sort the event IDs in the range, join them with newlines, compute the SHA-256, and check whether it matches on both sides. If it matches, all 413 IDs are identical one by one.

> New alerts keep arriving while the hash is being computed. Unless the calculation is limited to the same **time range** as the DB, the counts drift and cannot be compared.

## 3.2 The Hash on the alerts.json Side

**Run on: security-core VM 220 (root)**

⟦C16⟧

Replace `start_offset`, `start` and `end` with your environment's values fixed in Chapter 2, 2.4.

## 3.3 The Hash on the DB Side

Hash the IDs in the same range, sorted and joined the same way.

**Run on: LXC 109 postgresql (root)**

⟦C17⟧

Results at build time:

| Item | alerts.json | PostgreSQL |
|---|---:|---:|
| Count | 413 | 413 |
| Unique IDs | 413 | 413 |
| SHA-256 | `a819b04e...34137d6` | `a819b04e...34137d6` |

⟦C18⟧

The hashes match, so the 413 target alerts are all in the DB with no gaps and no duplicates at the level of individual IDs.

# Chapter 4: The Structure of an Actual Rotation

In Part 5 we tested rotation with a simulated log in a temporary directory. Here we examine Wazuh's actual file structure and check that it matches the Collector's assumptions. The production Collector is not stopped, and no logs are deleted, moved or changed.

## 4.1 The Current State

**Run on: security-core VM 220 (root)**

⟦C19⟧

If the saved inode and read position match the inode and size of the current `alerts.json`, it has processed up to the end.

## 4.2 The Structure of the Alert Directory

**Run on: security-core VM 220 (root)**

⟦C20⟧

Results at build time:

⟦C21⟧

| Pair | Relationship |
|---|---|
| `alerts.json` and `2026/Nov/ossec-alerts-18.json` | Same inode (today's JSON) |
| `alerts.log` and `2026/Nov/ossec-alerts-18.log` | Same inode (today's text format; not used by the Collector) |
| `ossec-alerts-17.json.gz` | The previous day's JSON, compressed (`.sum` is the signature) |

When the date changes, `alerts.json` becomes a new file, and the previous day's file stays under `year/month` and is then compressed.

## 4.3 Can the Collector See It?

Check the current `find_inode_file()` and the permissions of the per-day directories.

**Run on: security-core VM 220 (root)**

⟦C22⟧

⟦C23⟧

| Target | From the Collector |
|---|---|
| `alerts/` | Can traverse |
| `alerts/2026/`, `alerts/2026/Nov/` | Cannot traverse |
| `alerts.json` | Can read |
| `2026/Nov/ossec-alerts-18.json` | Cannot read (even though it is the same file, because the directories on the way cannot be traversed) |

**Problems:**

1. `find_inode_file()` searches only directly under `alerts`. The old file is under `year/month`.
2. The Collector has no permission to traverse the `year/month` directories.
3. The default ACL on `alerts` (Part 3, 7.3) was not applied to `2026` and `Nov`, which already existed.

As it stands, if the date changes while the Collector is stopped, it cannot start because of the fail-closed behavior from Part 5, 9.3.

## 4.4 Compressed Archives and the Read Position

**Run on: security-core VM 220 (root)**

⟦C24⟧

⟦C25⟧

A compressed file gets a new inode when it is compressed. So after compression, the original file cannot be found from the old inode. We keep the design in which only uncompressed JSON files are searched and the Collector stops fail-closed if none is found.

# Chapter 5: Searching the Per-Day Directories Recursively

## 5.1 Creating a Test Copy

Create a test copy from the production code. The production Collector is not stopped.

**Run on: security-core VM 220 (root)**

⟦C26⟧

## 5.2 A Function That Searches Recursively

Replace `find_inode_file()` so that it searches subdirectories as well.

- Only regular uncompressed `.json` files are searched (`.json.gz` is excluded).
- If a permission error or similar occurs during the search, do not treat it as "not found"; pass the exception to the caller (together with the fail-closed behavior from Part 5, 9.3, so that unread data is never silently discarded).

**Run on: security-core VM 220 (root)**

⟦C27⟧

## 5.3 Unit Tests

Create a `2026/Nov` structure in a temporary directory and check three behaviors.

**Run on: security-core VM 220 (root)**

⟦C28⟧

## 5.4 Checking in the Real Environment Without Permissions

On the real directories, before the ACLs are changed, have the Collector's user search and confirm that the error is passed on safely (it does not silently return `None`).

**Run on: security-core VM 220 (root)**

⟦C29⟧

At build time, `PASS: real directory traversal denied safely` was shown, and the production Collector kept the same PID with no increase in its restart count.

# Chapter 6: Minimal ACLs on the Per-Day Directories

## 6.1 The Current ACLs

Recursive search needs both read (`r`), to list a directory's contents, and traverse (`x`). Read permission on the files themselves is already given by the default ACL from Part 3, 7.3. Check before changing anything.

**Run on: security-core VM 220 (root)**

⟦C30⟧

## 6.2 Adding the ACLs

Add `r-x` for `wazuh-collector` on the existing year and month directories. Other users' and groups' permissions are not changed. Run the commands that change ACLs as root (they fail as an ordinary user).

**Run on: security-core VM 220 (root)**

⟦C31⟧

The top-level `alerts` also cannot be listed with `os.scandir()` with the previous `--x` (traverse only), so make it `r-x`.

⟦C32⟧

| Target | Collector's permission (after the change) |
|---|---|
| `alerts` | `r-x` |
| `alerts/2026` | `r-x` |
| `alerts/2026/Nov` | `r-x` |
| JSON files | `r--` (unchanged) |

> In Part 5, assuming there was no permission to list, we changed startup to prefer opening the current file. That processing remains, so these permissions are used only when looking for the old file after a rotation.

## 6.3 Recursive Search as the Collector's User

**Run on: security-core VM 220 (root)**

⟦C33⟧

## 6.4 Inheritance by Future Year and Month Directories

Check, with a temporary directory inside `alerts`, whether directories created in the future, such as `2027/Jan`, get the same permissions through the default ACL. The temporary directory is created by `mktemp -d` with permissions 700, so give the Collector `r-x` on the top of the test tree before trying. The temporary directory is deleted automatically at the end.

**Run on: security-core VM 220 (root)**

⟦C34⟧

> This command uses `set -e` and `trap`, so running it in an interactive shell may close the shell when it ends. In that case, log in again.

# Chapter 7: Deploying the Recursive-Search Version to Production

## 7.1 Checking the Diff and the Caller

**Run on: security-core VM 220 (root)**

⟦C35⟧

The only difference is the one function `find_inode_file()`.

| Item | Production | Candidate |
|---|---|---|
| Search scope | Directly under `alerts` only | Recursively into subdirectories |
| Target | Regular files | Regular `.json` files (`.json.gz` excluded) |
| Search errors | Warn and return `None` | Pass the exception to the caller |

⟦C36⟧

The caller, `open_initial_file()`, re-checks the inode with `fstat()` before reading the old file it found, and stops with `RuntimeError` if none is found. This does not affect the normal rotation switch (Part 5).

> **Remaining limitation:** If the old file has already been compressed (become `.json.gz`), the original inode cannot be found. In that case it refuses to start (fail-closed).

## 7.2 Replacing the Production Code

Check the candidate's hash and syntax and that the service is running, preserve the current production code (`7a816056...`), and then replace it in one step. The service is not restarted yet, so the running process still uses the old code.

**Run on: security-core VM 220 (root)**

⟦C37⟧

Replace `EXPECTED` with the candidate hash for your environment shown in 5.2. Also replace `7a816056...` in the final `test` with your own production hash before the replacement.

## 7.3 Restarting and Checking

**Run on: security-core VM 220 (root)**

⟦C38⟧

⟦C39⟧

Replace the `--since` time and the PID in `ps -p` with your environment's values. At build time it ran with the new PID `90884` and 0 restarts, and the saved inode and position matched the current `alerts.json`.

⟦C40⟧

> Right after startup, `PostgreSQL connection established` may not appear in the log. In the reading loop from Part 4, Chapter 4, the DB connection is made only "when a new normal alert line is read" (checked in the next chapter).

⟦C41⟧

# Chapter 8: Auditing Ingestion After the Restart

## 8.1 When the DB Connection Is Made

In `run()`, the DB connection is first made under the following condition.

⟦C42⟧

That is, after starting and resuming from the read position, it connects when it reads a new alert line. Until a new alert arrives, no connection log appears. Wait a while and then check. This check reads the state file, so it is done as root (as an ordinary user you get `PermissionError`; this is an intended restriction).

**Run on: security-core VM 220 (root)**

⟦C43⟧

At build time, the following log appeared about two minutes after the restart.

⟦C44⟧

## 8.2 Continued Ingestion

**Run on: LXC 109 postgresql (root)**

> The `postgres` user exists only on LXC 109. Running this on security-core gives `unknown user postgres`.

⟦C45⟧

## 8.3 Duplicates and Required Fields

⟦C46⟧

At build time there were 687 rows, with zero duplicates and zero missing event IDs, ingestion times, rule IDs, agent IDs or levels.

## 8.4 Ingestion Counts per Five Minutes

⟦C47⟧

Check that there is no time period in which ingestion stopped.

## 8.5 Keeping Up with Reading and the Count After the Restart

**Run on: security-core VM 220 (root)**

⟦C48⟧

**Run on: LXC 109 postgresql (root)**

⟦C49⟧

Replace the time with when you restarted in 7.3. At build time, 14 rows were inserted after the restart, all unique.

# Chapter 9: How Rotation Works and the Restart History

Without causing a rotation yet, and using reads only, we sort out how Wazuh rotates and what caused the Collector's stops so far.

## 9.1 What Performs the Rotation

**Run on: security-core VM 220 (root)**

⟦C50⟧

Neither logrotate nor cron has settings for Wazuh alerts.

⟦C51⟧

⟦C52⟧

## 9.2 Wazuh's Rotation Settings

**Run on: security-core VM 220 (root)**

⟦C53⟧

⟦C54⟧

⟦C55⟧

| Item | Details |
|---|---|
| What rotates | The Wazuh Manager's `wazuh-monitord` (not logrotate) |
| Interval | Daily (`monitord.rotate_log=1`). At build time, `Starting new log after rotation.` was logged at `00:00:10` |
| Compression | Enabled (`monitord.compress=1`). The previous day's JSON becomes `.json.gz` |
| Signing | Enabled (`monitord.sign=1`). A `.sum` is created |
| Today's file | `alerts.json` and `year/month/ossec-alerts-day.json` share the same inode (hard link) |

## 9.3 History of the Collector's Stops

**Run on: security-core VM 220 (root)**

⟦C56⟧

⟦C57⟧

Replace the times with the period when startup failed in Part 5, 8.5. All 19 failed restarts had the same cause.

⟦C58⟧

It lacked permission to list `/var/ossec/logs/alerts` and exited with `PermissionError` (Part 5, 8.5). This problem has been resolved by the code fix in Part 5, 9.1 and the ACLs in Chapter 6.

## 9.4 Final Check of the ACLs

**Run on: security-core VM 220 (root)**

⟦C59⟧

⟦C60⟧

| Item | Result |
|---|---|
| Directories | `r-x` for the Collector (list and traverse) |
| JSON files | `r--` for the Collector (read only) |
| Write | None (cannot change or delete Wazuh's logs) |
| Future directories | Inherit the same permissions through the default ACL |

# Chapter 10: Sorting Out the Cause of the Restart Loop

## 10.1 systemd's Restart Settings

**Run on: security-core VM 220 (root)**

⟦C61⟧

| Setting | Value | Meaning |
|---|---:|---|
| `Restart` | `always` | Restart when it exits |
| `RestartSec` | 5 seconds | Wait before restarting |
| `StartLimitIntervalUSec` | 10 seconds | Period over which starts are counted |
| `StartLimitBurst` | 5 | Stop starting it if this number is exceeded |

The start limit applies when "it starts more than 5 times within 10 seconds". The restart interval is 5 seconds, so it starts only twice in 10 seconds and never reaches the limit. That is why it restarted as many as 19 times in Part 5, 8.5.

⟦C62⟧

## 10.2 The Structure of Startup Processing

**Run on: security-core VM 220 (root)**

⟦C63⟧

⟦C64⟧

The initialization part of `run()` is outside the `try/finally`.

⟦C65⟧

| Item | Current behavior | Assessment |
|---|---|---|
| Exception during initialization | Not caught; the process exits (systemd restarts it) | Intended, so that unread data is never silently discarded. But the restarts go on indefinitely |
| DB connection error | Waits 5 seconds and retries (the process does not exit) | No problem |
| Saved position larger than the file | On the next line, it silently moves to the end of the file | **Needs fixing** (may discard unread data) |

⟦C66⟧

A saved read position larger than the file size is a state that normally does not occur, for example when the file has become shorter (been truncated). Moving to the end and continuing would mean not noticing that alerts in between had been missed. In line with the fail-closed policy, we change it to refuse to start.

## 10.3 Checking the Runtime Environment

**Run on: security-core VM 220 (root)**

⟦C67⟧

At build time this was Python 3.12.3 and systemd 255.4, and the production Collector was running as PID `90884` with 0 restarts.

# Chapter 11: Validating the Read Position at Startup

The following fixes are also made on a test copy, without stopping production.

## 11.1 Creating a Test Copy

**Run on: security-core VM 220 (root)**

⟦C68⟧

⟦C69⟧

## 11.2 Reproducing the Behavior Before the Fix

In a temporary directory, check the behavior before the fix. Reproduce how it silently moves to the end when the saved position is larger than the file.

**Run on: security-core VM 220 (root)**

⟦C70⟧

At build time, with a saved position of 117 and a file size of 17, the resume position became 17, reproducing the problem.

⟦C71⟧

## 11.3 The Fix

In two places, the current file and the rotated file, check the position before `seek()` and stop with `RuntimeError` if it is larger than the file.

**Run on: security-core VM 220 (root)**

⟦C72⟧

⟦C73⟧

> For the current file, the exception is passed to the caller after `except Exception:` in `open_initial_file()` closes the file.

## 11.4 Validating the Read Position

**Run on: security-core VM 220 (root)**

⟦C74⟧

| Check | Result |
|---|---|
| Current file: correct position | Resumes |
| Current file: position larger than the file | Refuses to start |
| Rotated file: correct position | Resumes |
| Rotated file: position larger than the file | Refuses to start |
| Old inode not found | Refuses to start |

## 11.5 Checking the Diff and Production

**Run on: security-core VM 220 (root)**

⟦C75⟧

If no diff is shown, also check the exit code. `diff` returns exit code 1 when there are differences (this is not an error).

⟦C76⟧

Confirm that only two places in `open_initial_file()` changed and that production (`ac297477...`) has not changed.

## 11.6 Checking for an inode Mix-Up

Confirm that when the search for the old file returns a file with a different inode from the saved one, the Collector stops without reading that file.

**Run on: security-core VM 220 (root)**

⟦C77⟧

# Summary of Part 6

In Part 6 we confirmed, down to individual event IDs, that the hardened Collector puts alerts into the DB "with nothing missing and nothing doubled", and finished it to fit the actual structure of rotation.

| Check / change | Result |
|---|---|
| Duplicate prevention | Guaranteed by the DB primary key. Confirmed with a temporary table and a mock that a second insert is rejected |
| Completeness | The SHA-256 of the set of 413 event IDs matches between alerts.json and the DB |
| Rotation structure | `wazuh-monitord` moves files to `year/month` daily and compresses the previous day's file |
| Searching for the old file | Changed to a recursive search (`.json.gz` excluded, search errors fail-closed) and deployed to production |
| ACLs | `r-x` for the Collector on the `alerts`, year and month directories; inherited by future directories |
| After restart | The DB connection is established when a new alert is read. Ingestion continues with 0 duplicates |
| Read position validation | Confirmed in the test version a fix that refuses to start when the saved position is larger than the file (deployed to production in Part 7) |

| Production file | SHA-256 (at build time) |
|---|---|
| `collector.py` (recursive-search version) | `ac297477...` |
| `collector.py.backup-before-recursive-rotation-20261119` | `7a816056...` (the Part 5 version) |

> **Remaining limitation:** If the old file has already been compressed, the original inode cannot be found and the Collector refuses to start (Chapter 7, 7.1). Take care when stopping the Collector across a date change.

In Part 7, we continue verifying the test version `/tmp/wazuh-collector-step330-test.py`, check the release of files on abnormal exit and resistance to huge lines and deeply nested JSON, and then deploy it to production.

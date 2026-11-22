---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 2"
subtitle: "Part 30: Keeping the Collector from Stopping for the Same Reason"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 30 of Volume 2 of the "AI Autonomous Cyber Defense System Build Manual". In Parts 28 and 29 we found that the Collector had stopped because it could not enter a hidden test directory (`.acl-inheritance-test.bkv8vd`), fixed the read position and started it again. However, the directory still remains, so the Collector may stop again the next time the file switches.

Here, rather than deleting the directory or widening the Collector's permissions, we change just two lines of the Collector's code so that **when looking for the previous file, it does not search directories whose names start with `.` (hidden directories)**.

- The real locations of alerts (such as `2026/Nov`) are searched as before
- Errors when an ordinary directory cannot be entered still stop the Collector, as before (they are not swallowed)
- The design of not following symbolic links is unchanged

Finally, we check in the code the processing at log switching (rotation) and the handling of the state file and duplicates.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **postgresql**: LXC 109 (192.168.0.151), OS user `postgres`

# Chapter 1: What the Hidden Directory Is

> **Run on: VM 220**

⟦C0⟧

It was created on November 18, 2026, everything is `root:root`, and it contains only `2027/Jan/test.json` (0 bytes). It was created when testing ACL inheritance in Part 6 of Volume 1. Look for any remaining script that created it.

⟦C1⟧

There were none. Look at the ACL.

⟦C2⟧

Only the top-level directory was in the following state (key points).

⟦C3⟧

There is an ACL entry, but the mask is `---`, so it cannot actually be entered.

# Chapter 2: Fixing the Search

## 2.1 The Current Code

⟦C4⟧

In the following part, `find_inode_file()` included every directory, hidden ones too, in what it searched.

⟦C5⟧

Check what is directly under `alerts` and the shape of the real locations.

⟦C6⟧

⟦C7⟧

There were two directories directly under it, `2026` and `.acl-inheritance-test.bkv8vd`, and the real location was `2026/Nov`. Even with hidden directories excluded, the real files can be found.

⟦C8⟧

⟦C9⟧

`open_initial_file()` stops startup if the previous file is not found. This safety measure is not changed. What changes is the following form.

⟦C10⟧

## 2.2 Backup

Without touching the running Collector, back up the file.

⟦C11⟧

Confirm that the two SHA-256 values are the same.

## 2.3 The Fix

Rewrite only if there is exactly one place to fix.

⟦C12⟧

⟦C13⟧

The difference was only two lines: `if entry.name.startswith("."):` and `continue`.

## 2.4 Testing as the Collector's User

Extract only `find_inode_file()` and, as the Collector's user, have it search for an inode that does not exist. It has succeeded if it returns `None` (not found) and finishes normally even though it cannot enter the hidden directory. No DB connection is made.

⟦C14⟧

The result was `TEST: PASS`.

# Chapter 3: Applying the Fix

## 3.1 Restarting

⟦C15⟧

The current process (PID 13542) is running the code from before the fix. Restart it to load the new code. Collection stops briefly during the restart, but it continues from the position in the state file.

⟦C16⟧

⟦C17⟧

At build time it was PID 14203, `NRestarts=0`, `active` and `running`.

⟦C18⟧

⟦C19⟧

`Resuming current alert file` was present, and no `PermissionError` for the hidden directory appeared.

## 3.2 There Is No PostgreSQL Connection Log

⟦C20⟧

⟦C21⟧

The Collector connects to PostgreSQL **only when an unread line arrives**. If it has read to the end and no new alerts have arrived, no connection log appears.

⟦C22⟧

⟦C23⟧

Nothing was unread, and `alerts.json` had not been updated since before the restart.

## 3.3 Checking the Connection

As the Collector's user, using the same connection settings as the Collector (`DB_CONFIG`), run only `SELECT 1`. Connection information is not shown.

⟦C24⟧

The result was `POSTGRESQL_READ_ONLY_TEST: PASS`. After a while, look at the log once new alerts have arrived.

⟦C25⟧

⟦C26⟧

> **Run on: postgresql** (OS user `postgres`. You are already logged in as `postgres`, so `sudo` is not used)

⟦C27⟧

Three events (three distinct `event_id`s) had been saved after the restart.

# Chapter 4: Checking the Rotation Processing

> **Run on: VM 220**

⟦C28⟧

| Situation | What the Collector does |
|---|---|
| An ordinary line | Saves it to PostgreSQL, then saves the position |
| Cannot reach PostgreSQL / save fails | Goes back to the start of the line and retries |
| The end of the file is a partial line | Waits for the switch |
| The file switches while a line is partial | Discards that line and switches to the new inode |
| The file switches after reading to the end | Switches to the new inode |
| Saving the position fails | Retries without switching to the new file |

⟦C29⟧

`save_state()` writes to a temporary file in the same directory with `0600`, calls `flush()` and `fsync()`, swaps it in with `os.replace()`, and also calls `fsync()` on the directory. The order of processing is as follows.

⟦C30⟧

⟦C31⟧

`event_id` is the Wazuh alert's `alert["id"]`, and only duplicates (SQLSTATE `23505`) are treated as "already present". The position is advanced only after the INSERT is committed, so even if the Collector stops between saving the event and saving the position and re-reads the same line, nothing is inserted twice.

# Closing Notes

In Part 30 we made the Collector no longer stop at the hidden directory.

| Item | Result |
|---|---|
| What was fixed | `find_inode_file()` no longer searches directories whose names start with `.` (2 lines) |
| Backup | `collector.py.pre-hidden-dir-fix-20261121` |
| Test | `TEST: PASS` as the Collector's user |
| Applied | Restarted with `NRestarts=0`; saving to PostgreSQL also confirmed |
| Hidden directory | Not deleted (the Collector no longer stops even though it remains) |

In the original build, the work then moved on to checking the rotation method, such as whether Wazuh's log switching uses `copytruncate`, but the results are not within the records received (author's notes, item 30-B).

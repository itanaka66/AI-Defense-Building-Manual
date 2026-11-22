---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 5: Deploying the Hardened Collector to Production"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 5 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". We finish the hardening added to the test copy in Part 4, deploy it to the production Collector, and confirm that it works correctly in actual operation.

## Notation

- Commands and file contents are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Each step begins with "Run on", which says where to run it.
- "Example output" is the actual output from the build. In your environment, inodes, sizes, dates, hashes and so on will differ.
- The contents of credentials and the state file are not shown.

## State at the End of Part 4

| Item | State |
|---|---|
| Production Collector | `/usr/local/lib/wazuh-collector/collector.py` (9,626 bytes, SHA-256 `931ee3cb...`) |
| Production service | `wazuh-collector.service` (active, 0 restarts) |
| Test version | `/tmp/wazuh-collector-hardening-test.py` (all hardening from Part 4 applied) |
| Backup before the improvements | `/usr/local/lib/wazuh-collector/collector.py.backup-pre-hardening-20261118` |

> The test version is in `/tmp`. Continue from Part 4 without restarting security-core.

# Chapter 1: Improving Shutdown Handling

## 1.1 The Problem

The `finally` at the end of `run()` closes the file and then the DB connection. As it stands, if an exception occurs while closing the file, the DB connection is not closed. Fix it so that if either fails, the other is still always closed.

Back up before the fix.

**Run on: security-core VM 220 (root)**

⟦C0⟧

⟦C1⟧

⟦C2⟧

`handle` is opened before the `try`, and `connection` is initialized to `None`, so both can be referenced in `finally`. Confirm that there is exactly one place to fix.

⟦C3⟧

If `TARGET_COUNT: 1` is shown, go on.

## 1.2 Fixing the Shutdown Handling

Wrap closing the file and closing the DB connection in separate `try` blocks. Only the exception type is logged, with no sensitive information.

**Run on: security-core VM 220 (root)**

⟦C4⟧

⟦C5⟧

## 1.3 Checking the Shutdown Handling

Extract the `finally` part from the syntax tree and confirm that both closes are protected.

**Run on: security-core VM 220 (root)**

⟦C6⟧

With fake objects, confirm the order: even if closing the file fails, closing the DB connection is still executed.

⟦C7⟧

> Pasting long code into the terminal can break it partway and cause a `SyntaxError`. In that case neither the file nor production is affected; paste it again.

## 1.4 Checking the Difference from Production

**Run on: security-core VM 220 (root)**

⟦C8⟧

If `diffstat` is not installed, the summary is not shown, but that is not a problem. Check the first and second halves of the diff.

⟦C9⟧

⟦C10⟧

# Chapter 2: Protecting File Opening at Rotation

## 2.1 The Problem

The following two lines, used when rotation is detected, appear in two places: the incomplete-line case (Part 4, 5.3) and the EOF case (Part 4, 5.2).

⟦C11⟧

Neither has exception handling, so the Collector exits if the new file cannot be opened. Also, if `fstat()` fails after opening, the file stays open. Combine this processing into one function and, on failure, retry while staying on the current file.

**Run on: security-core VM 220 (root)**

⟦C12⟧

Confirm that the name of the function to be added is not yet in use. If nothing is shown, there is no problem.

⟦C13⟧

Back up before the fix.

⟦C14⟧

## 2.2 Adding a Function That Opens the File Safely

Add it after `open_initial_file()` and before `read_alert_line()`. If `open()` or `fstat()` fails, it logs only the exception type, closes the opened file and returns `(None, None)`.

**Run on: security-core VM 220 (root)**

⟦C15⟧

⟦C16⟧

Check the added function.

⟦C17⟧

> In the original build, this command showed `ABORT: function already exists`, but the following check showed that the function had been added correctly (lines 384–406). Only the safety check against adding it twice was triggered, so there is no problem as long as `grep` shows exactly one function.

⟦C18⟧

## 2.3 Replacing the Call for Incomplete Lines

Adding the function alone leaves the callers unchanged. First check the surroundings of the two places.

**Run on: security-core VM 220 (root)**

⟦C19⟧

Changing both places at once would make problems harder to isolate, so fix them one at a time. In the first place (incomplete line), if opening fails, rewind the read position with `handle.seek(line_start)` and check again on the next wait without losing the incomplete line.

⟦C20⟧

⟦C21⟧

⟦C22⟧

Confirm that if opening fails, it goes back to the start of the line and retries.

## 2.4 Replacing the Call at EOF

At EOF, unlike the incomplete-line case, there is no need to rewind the read position. If opening fails, keep the old file open and go on to the next wait.

**Run on: security-core VM 220 (root)**

⟦C23⟧

⟦C24⟧

Check the replaced part.

⟦C25⟧

> In the original build, this command showed `ABORT: target block count is not 1`, but checking showed that the EOF side had already been replaced to use `safe_open_current_alert_file()`. On `ABORT` the file is not changed, so always check the actual content with this `sed`.

⟦C26⟧

## 2.5 Checking the Replacement

**Run on: security-core VM 220 (root)**

⟦C27⟧

| Check | Meaning |
|---|---|
| `two_rotation_calls` | `run()` calls the function from two places |
| `no_direct_rotation_open` | No old code calling `ALERT_FILE.open()` directly remains |
| `helper_defined_once` | The function is defined only once |

## 2.6 Unit Tests for the Function

`ALERT_FILE` is an instance of `Path`, so when mocking `open`, patch the `Path` class rather than the instance (instance attributes are read-only).

**Run on: security-core VM 220 (root)**

When the file cannot be opened:

⟦C28⟧

When `fstat()` fails after opening:

⟦C29⟧

When it opens normally (opens the production `alerts.json` read-only and closes it immediately):

⟦C30⟧

⟦C31⟧

| Branch | When opening fails | On success |
|---|---|---|
| Incomplete line | Rewind with `handle.seek(line_start)` and retry | Switch only after the state is saved successfully |
| EOF | Keep the old file open and retry | Switch only after the state is saved successfully |

# Chapter 3: Exception Handling for stat()

## 3.1 The Problem

`ALERT_FILE.stat()`, used to detect rotation, catches only `FileNotFoundError`. If a `PermissionError` or a temporary I/O error occurs, the Collector exits. Fix it to catch all `OSError`s, log them and retry.

**Run on: security-core VM 220 (root)**

⟦C32⟧

⟦C33⟧

Back up before the fix.

⟦C34⟧

## 3.2 Fixing the Exception Handling for stat()

In the incomplete-line case it goes back to the start of the line, and at EOF it stays on the old file; in both cases it logs the error type and retries.

**Run on: security-core VM 220 (root)**

⟦C35⟧

⟦C36⟧

⟦C37⟧

## 3.3 Checking the Fix

**Run on: security-core VM 220 (root)**

⟦C38⟧

Now, whichever of `stat()`, `open()` or `fstat()` fails, the Collector retries instead of exiting.

⟦C39⟧

# Chapter 4: Failure-Case Tests Using run()

Check that the fixes in Chapters 2 and 3 work as intended inside the actual `run()`. Files, file positions, state saving and waiting are all replaced with fake objects, so the production log, DB and state file are not touched. Replacing `time.sleep` with something that raises an exception stops the infinite loop safely.

**Run on: security-core VM 220 (root)**

⟦C40⟧

## 4.1 When stat() Fails

When `ALERT_FILE.stat()` raises `PermissionError`, confirm that the state is not saved, that an incomplete line goes back to its start, and that at EOF the position does not change.

⟦C41⟧

It has succeeded if the log `Failed to stat alerts.json: PermissionError` is followed by `incomplete: PASS` and `eof: PASS`. Also confirm that production is not affected.

⟦C42⟧

## 4.2 Recovering from a stat() Failure

Confirm that when the first `stat()` fails and the second succeeds and detects an inode change (11111 → 22222), processing proceeds to rotation (incomplete-line case).

**Run on: security-core VM 220 (root)**

⟦C43⟧

⟦C44⟧

| Check | Meaning |
|---|---|
| `stat retry` | `stat()` was called twice (first failed, second succeeded) |
| `old offset restored` | On the first failure, the position in the old file was restored to 37 |
| `old handle closed` | The old file was closed at the switch |
| `new handle closed` | The new file was also closed during test cleanup |
| `new state saved` | The new inode (22222) and position 0 were saved |

⟦C45⟧

## 4.3 When the New File Cannot Be Opened

Check the case where `stat()` detects an inode change but the new `alerts.json` cannot be opened. The expectation is that the old file stays open, the position is kept, and the state is not saved.

> `run()` always closes the file in `finally` when it ends. So whether the old file is still open is recorded and judged at the retry wait (`time.sleep`), not at the end of the test.

**Run on: security-core VM 220 (root)**

Incomplete-line case:

⟦C46⟧

EOF case:

⟦C47⟧

If all five items are `PASS` in both cases, the Collector can safely retry on the old file even when the new file cannot be opened.

⟦C48⟧

# Chapter 5: Unicode Format Characters and Timestamp Length

## 5.1 The Overall Structure of the Test Version

Before deploying to production, review the test version as a whole. First list the functions and constants.

**Run on: security-core VM 220 (root)**

⟦C49⟧

At build time there were 15 functions, divided into input validation, DB storage, state management, rotation and the main loop. Check the input validation part and the imports and constants.

⟦C50⟧

⟦C51⟧

## 5.2 Checking the Current Behavior

Check how validation of timestamps, strings and IP addresses handles borderline input.

**Run on: security-core VM 220 (root)**

⟦C52⟧

Results at build time:

⟦C53⟧

| Item | Current behavior | Decision |
|---|---|---|
| Timestamps | Invalid values and a 10,000-character value are rejected | Set an explicit length limit |
| Newlines | Removed | No problem |
| Japanese text | Kept as is | No problem |
| Zero-width space (U+200B), bidirectional control character (U+202E) | Kept | Remove them, because they can disguise how logs are displayed |
| IP address with surrounding spaces | Rejected | Staying strict is fine for security |

## 5.3 Removing Format Characters

Remove characters whose Unicode category is "Cf" (format characters) in `safe_text()`. Japanese text and emoji are kept. Back up before the fix.

**Run on: security-core VM 220 (root)**

⟦C54⟧

⟦C55⟧

⟦C56⟧

`__import__("unicodedata")` also works, but for readability and maintenance, tidy it into a normal `import`.

⟦C57⟧

## 5.4 Limiting the Timestamp Length

Limit timestamp strings to 64 characters, and also reject empty strings.

**Run on: security-core VM 220 (root)**

⟦C58⟧

## 5.5 Regression Tests

**Run on: security-core VM 220 (root)**

⟦C59⟧

| Category | What was checked |
|---|---|
| Timestamps | JST and UTC accepted; empty, invalid and 65+ characters rejected |
| Strings | Japanese text and emoji kept; newlines, zero-width spaces and bidirectional control characters removed |

It is done when all 10 items are `PASS`.

# Chapter 6: Comprehensive Tests of Huge Lines and Rotation

## 6.1 Measuring the Skip Positions

Measure at which positions a line over 1 MiB is skipped. The first read reads the limit (1 MiB + 1 byte) followed by an extra 64 KiB, so less remains than you might expect.

**Run on: security-core VM 220 (root)**

⟦C60⟧

⟦C61⟧

| Stage | State | Read position | Remaining |
|---|---|---:|---:|
| 1 | `discarding` | 1,114,113 | 131,072 |
| 2 | `discarding` | 1,179,649 | 65,536 |
| 3 | `oversized` | 1,245,185 | 0 |

It discards 64 KiB at a time and finishes with `oversized` when it reaches the newline.

## 6.2 Preparing the Test Environment

Run the whole of `run()` on a simulated log in a temporary directory. State saving and the DB connection are mocked, and the production state file (`/var/lib/wazuh-collector/state.json`) and DB are not touched.

**Run on: security-core VM 220 (root)**

⟦C62⟧

⟦C63⟧

Confirm that a rotation in the temporary directory (renaming and creating a new file) changes the inode.

⟦C64⟧

⟦C65⟧

## 6.3 Rotation While Skipping

Put an incomplete line over 1 MiB in the old log, and rotate the log after `run()` starts skipping (at the first wait). Confirm that the new inode and position 0 are saved. If a DB connection is made, the test fails.

**Run on: security-core VM 220 (root)**

⟦C66⟧

The following three lines are written to the log.

⟦C67⟧

## 6.4 When Saving the State Fails at Rotation

Deliberately make saving the new inode fail, and confirm that the old file is kept open and the Collector does not switch to the new file. Whether the old file is open is recorded at the second wait (retry).

**Run on: security-core VM 220 (root)**

⟦C68⟧

If the log `ERROR State save failed during rotation: OSError` is followed by `ALL TESTS PASSED`, this confirms that while the state cannot be saved, the Collector waits on the old file and does not wrongly switch to the new one.

# Chapter 7: Comprehensive Tests of DB Failures and Reprocessing

## 7.1 Reconnecting When the DB Connection Is Lost

Deliberately make the first DB operation fail, and confirm that the connection is discarded and recreated and the same alert is processed again from its original position. The state should be saved only once, after processing succeeds.

**Run on: security-core VM 220 (root)**

⟦C69⟧

> The test connection object needs the `closed` attribute that the production code refers to. Without it you get an `AttributeError`.

## 7.2 Reprocessing After a Failed State Save and Preventing Duplicates

When the DB insert succeeds but saving the state fails, confirm with the actual `run()` that the same alert is reprocessed, the second insert is rejected by the unique constraint, and only one row is inserted (this repeats the check of Part 4, 8.6 across the whole loop).

**Run on: security-core VM 220 (root)**

⟦C70⟧

Results at build time:

⟦C71⟧

## 7.3 Confirming That Forbidden Elements Are Absent

Check the syntax, and confirm that `ON CONFLICT`, `SELECT`, `UPDATE`, `DELETE`, `full_log`, `password` and `command` do not appear in the code. If nothing is shown, there is no problem.

**Run on: security-core VM 220 (root)**

⟦C72⟧

# Chapter 8: Deploying to Production and a Startup Problem

## 8.1 Final Check of the Difference from Production

**Run on: security-core VM 220 (root)**

⟦C73⟧

If it is hard to read in `less`, show it in separate ranges.

⟦C74⟧

⟦C75⟧

| Area | Changes |
|---|---|
| Input validation | Limits on integers, strings, timestamps and Unicode |
| Arrays and MITRE | Limits on counts, lengths and keys |
| State file | Strict validation of inode and position; the inode of the file actually opened |
| Line size | 1 MiB limit, skipping in 64 KiB units |
| Rotation | Switching on an incomplete line, at EOF and while skipping; retry when open, fstat or stat fails |
| DB and shutdown | Rewind on connection failure, duplicate handling, independent closes |

## 8.2 Production Health and Preserving the Test Version

**Run on: security-core VM 220 (root)**

⟦C76⟧

Preserve the verified test version under another name inside `/tmp`.

⟦C77⟧

⟦C78⟧

| File | Owner / permissions | Size (at build time) |
|---|---|---:|
| Production `collector.py` | `root:root 755` | 9,626 bytes |
| Test version | `root:root 600` | 18,510 bytes |

## 8.3 Placing the Candidate File and Backing Up Production

Place the test version as `collector.py.candidate` with the same owner and permissions as production, and check its syntax and hash.

**Run on: security-core VM 220 (root)**

⟦C79⟧

Back up the current production code.

⟦C80⟧

⟦C81⟧

## 8.4 Replacing the Production Code

Copy the candidate file once as `collector.py.new`, check that it matches with `cmp`, and then replace in one step with `mv` (so that no partially written file exists under the production name). The service is not restarted at this point, so the running process still uses the old code.

**Run on: security-core VM 220 (root)**

⟦C82⟧

> If you run `set -e` in an interactive shell, the shell itself exits as soon as a command fails. In that case, log in again and check the state.

The SHA-256 of the production `collector.py` becomes `d404f10a...` (18,510 bytes), the same as the test version.

## 8.5 Restarting, and the Startup Failure

**Run on: security-core VM 220 (root)**

⟦C83⟧

In the original build, `activating` was shown here and it did not work correctly. Check the status and the log.

⟦C84⟧

⟦C85⟧

Set the `--since` time to when you restarted. The log at build time was as follows (excerpt).

⟦C86⟧

**Cause:** At startup, the new code's `open_initial_file()` lists the contents of `/var/ossec/logs/alerts` with `os.scandir()` through `find_inode_file()`. However, the ACL from Part 3, Chapter 7 gives `wazuh-collector` only the traverse permission (`x`) on this directory, not the read permission (`r`) needed to list it. The assumption of the new code and the least-privilege design did not match.

> In the tests, `find_inode_file()` was mocked or the tests ran as root, so this problem was not found until it ran as the production user.

## 8.6 Stopping the Automatic Restarts

systemd keeps restarting it every 5 seconds, so stop only the Collector. The Wazuh Manager, Indexer and PostgreSQL are not affected.

**Run on: security-core VM 220 (root)**

⟦C87⟧

> If you run it as an ordinary user, systemd asks for administrator authentication. In that case enter that user's password (do not keep a record of the password).

If `inactive` is shown, it has stopped.

Rather than simply adding read permission on the directory, deal with it in the code while keeping least privilege. First check the permissions and the code.

⟦C88⟧

⟦C89⟧

The saved inode (`5409146`) was the same as the current `alerts.json`. In other words, it can resume simply by opening the current file directly, without listing the directory.

⟦C90⟧

# Chapter 9: Fixing the Startup Processing

Here too, the fix is made on the test version, verified, and then deployed to production.

## 9.1 Startup That Prefers the Current File

There are two policies.

1. If the saved inode is the same as the current `alerts.json`, open the current file directly and resume, without listing the directory.
2. Even if the directory cannot be listed, `find_inode_file()` does not crash with an exception; it warns and returns `None`.

Back up the test version before the fix.

**Run on: security-core VM 220 (root)**

⟦C91⟧

Replace `find_inode_file()` and `open_initial_file()` together.

⟦C92⟧

## 9.2 Where Rotated Files Are Kept

Check the assumptions for finding the old file. The per-day archives are not directly under `alerts` but in `year/month` subdirectories.

**Run on: security-core VM 220 (root)**

⟦C93⟧

The current `alerts.json` has the same inode as the per-day archive `ossec-alerts-18.json`. When the date changes, only the new `alerts.json` remains directly under `alerts`, and the previous day's file moves under `year/month`. So `find_inode_file()`, which searches only directly under `alerts`, cannot find a rotated old file.

If, as at the end of 9.1, the Collector silently re-reads the current file from the beginning when the old file is not found, it would not notice that unread data in the old file had been lost. So we change it so that **if the old file cannot be confirmed, it errs on the safe side and refuses to start (fail-closed)**.

## 9.3 Startup That Errs on the Safe Side

**Run on: security-core VM 220 (root)**

⟦C94⟧

⟦C95⟧

Replace only `open_initial_file()` (`find_inode_file()` from 9.1 is used as is).

⟦C96⟧

## 9.4 Regression Tests for Startup

Check three conditions in a temporary directory.

**Run on: security-core VM 220 (root)**

⟦C97⟧

| Test | What is checked |
|---|---|
| 1 | If the inode is the same, resume from the saved position without listing the directory |
| 2 | If the old file is found, resume from the saved position |
| 3 | If the old file cannot be confirmed, refuse to start |

> As in test 3, if it starts when the old file cannot be confirmed, the Collector stops with an error and systemd keeps restarting it. This is intended, so that alerts are never silently lost. In that case, check the state file and the alert files, remove the cause, and then start it.

## 9.5 Placing the Candidate File and Checking as the Service User

**Run on: security-core VM 220 (root)**

⟦C98⟧

The candidate file at build time was 18,898 bytes with SHA-256 `7a816056...`.

As the same `wazuh-collector` user as production, check that it can read the production state file and open the current `alerts.json` at the correct position (this only reads; the state file is not changed). Because the extension is not `.py`, load it with an explicit loader.

⟦C99⟧

At build time this gave inode `5409146` and position `2178712`, matching the saved values.

# Chapter 10: Redeploying and Checking Operation

## 10.1 Deploying the Fixed Version to Production

After confirming that the Collector is stopped (`inactive`) and that the production code is the version deployed in 8.4 (`d404f10a...`), preserve that version under another name and replace it with the fixed version. If any condition is not met, `set -e` stops there. The service is not started yet.

**Run on: security-core VM 220 (root)**

⟦C100⟧

> The hash value `d404f10a...` is that of the version deployed in 8.4 in the original build. In your environment, replace it with your own value shown after 8.4.

| File | Contents |
|---|---|
| `collector.py` | Fixed version (`7a816056...`, 18,898 bytes) |
| `collector.py.backup-before-fail-closed-20261119` | Version deployed in 8.4 (`d404f10a...`) |
| `collector.py.backup-20261119` | Production version before Part 4 (`931ee3cb...`) |
| `collector.py.backup-pre-hardening-20261118` | Same as above (created in Part 4, 1.5) |

## 10.2 Checks Before Startup, and Starting

**Run on: security-core VM 220 (root)**

⟦C101⟧

⟦C102⟧

If the following three lines appear in the log, it has resumed normally with the fixed startup processing (output at build time).

⟦C103⟧

## 10.3 Stability After Startup and Keeping Up with Reading

**Run on: security-core VM 220 (root)**

⟦C104⟧

Check as the service user whether the read position has caught up with `alerts.json` (the state file is only read).

⟦C105⟧

Set the `--since` time to when you started it. 30 seconds later, check the running state and warnings again.

⟦C106⟧

If `unread_bytes` is 0 or a small value and `RECENT ERRORS` shows `-- No entries --`, it is keeping up with new alerts and working normally.

## 10.4 Reconciling Counts Between Wazuh and PostgreSQL

The DB-side check is done inside LXC 109 as the DB administrator (`postgres`) (the prompt is `root@postgresql`).

**Run on: LXC 109 postgresql (root)**

⟦C107⟧

⟦C108⟧

Taking the time of the oldest alert in the DB (`2026-11-18 11:00:59 UTC` at build time, right after the Collector was first started in Part 3) as the starting point, count the alerts on the Wazuh side for the same period.

**Run on: security-core VM 220 (root)**

⟦C109⟧

⟦C110⟧

Replace the `start` date and time with the time of the oldest alert in your environment's DB. Then recount the DB side for the same period.

**Run on: LXC 109 postgresql (root)**

⟦C111⟧

> If the file and the DB are counted at different times, the difference equals the alerts added in between. If there is a difference, count both again in quick succession.

Reconciliation result at build time:

| Item | Count |
|---|---:|
| Wazuh `alerts.json` (same period) | 230 |
| PostgreSQL `incident.alert_events` (same period) | 230 |
| Difference | 0 |

# Summary of Part 5

In Part 5, the hardened Collector went into production.

| Item | State |
|---|---|
| Production Collector | `/usr/local/lib/wazuh-collector/collector.py` (hardened version, 18,898 bytes) |
| Service | `wazuh-collector.service` (active, starts automatically) |
| Startup processing | Resumes preferring the current file; refuses to start if the old file cannot be confirmed (fail-closed) |
| Reconciliation | Wazuh alerts and DB rows for the same period match (230) |

Across Parts 4 and 5, the following hardening was added to the Collector.

| Area | Details |
|---|---|
| Input | Validation of type, range and length; removal of control characters (C0, DEL, C1, Unicode format characters); a timestamp length limit |
| Line size | 1 MiB per-line limit, skipping in 64 KiB units |
| Rotation | Switching on an incomplete line, at EOF and while skipping; the inode of the file actually opened; retry when `stat`, `open` or `fstat` fails |
| State file | Strict validation of values; saved only after a successful DB insert |
| DB | Rewind and reconnect on connection failure; duplicates rejected by the unique constraint (no SELECT privilege needed) |
| Startup and shutdown | Startup with least privilege, fail-closed, independent closing of the file and DB connection |

> **Operational note:** As explained in 9.2, per-day archives move to `alerts/year/month`, so if the date changes while the Collector is stopped, it cannot confirm the old file at startup and refuses to start. If it cannot start after being stopped for a long time, check the state file and the contents of `alerts` before taking action.

In the next stage, we further check duplicate prevention and data integrity for the alerts stored in the DB, and extend the monitoring.

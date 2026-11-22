---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 7: Finishing the Collector's Fault Tolerance"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 7 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". We deploy to production the "read position validation" confirmed in the test version at the end of Part 6, and then verify and finish, one by one, the remaining failure cases: DB duplicate handling, huge lines, JSON nesting depth, file descriptors, failures to save the state, and so on.

## Notation

- Commands and file contents are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Each step begins with "Run on", which says where to run it. DB checks are done inside LXC 109 as the DB administrator (`postgres`).
- "Example output" is the actual output from the build. Hashes, counts, times, inodes and so on will differ in your environment.
- Test files and scripts are created in `/tmp`. They may disappear when the VM restarts.

## State at the End of Part 6

| Item | State |
|---|---|
| Production Collector | Recursive-search version (SHA-256 `ac297477...`) |
| Test version | `/tmp/wazuh-collector-step330-test.py` (read position validation added, `df4a9ff6...`) |
| ACLs | `r-x` for the Collector on the `alerts`, year and month directories |

# Chapter 1: Deploying Read Position Validation to Production

## 1.1 Releasing the File on Abnormal Exit

Confirm that when startup is refused because of an inode mix-up, the opened file is closed (no file descriptor leaks) and the existing state file does not change.

**Run on: security-core VM 220 (root)**

⟦C0⟧

## 1.2 Checks Before Deploying

**Run on: security-core VM 220 (root)**

⟦C1⟧

| File | SHA-256 (at build time) |
|---|---|
| Production | `ac297477...` |
| Backup (the Part 5 version) | `7a816056...` |
| Candidate (test version) | `df4a9ff6...` (19,593 bytes) |

## 1.3 Deploying to Production

Check the hashes of production and the candidate, make an additional backup of the current production code, and replace it in one step. The service is not restarted yet.

**Run on: security-core VM 220 (root)**

⟦C2⟧

Replace the two hashes with your environment's values for production (before deployment) and the candidate.

## 1.4 Restarting and Checking

**Run on: security-core VM 220 (root)**

⟦C3⟧

⟦C4⟧

At build time, `Resuming current alert file` was shown with the new PID `91473`, and it resumed from the saved inode `5409146`. As in Part 6, 8.1, the DB connection is made when a new alert is read.

# Chapter 2: Checking Ingestion After Deployment

## 2.1 The DB Baseline

**Run on: LXC 109 postgresql (root)**

⟦C5⟧

At build time there were 727 rows.

## 2.2 Ingesting New Alerts

Wait for a new alert to arrive, then check the log after the restart.

**Run on: security-core VM 220 (root)**

⟦C6⟧

At build time, it detected a new alert and connected to the DB about five minutes after the restart.

⟦C7⟧

**Run on: LXC 109 postgresql (root)**

⟦C8⟧

The count had increased from 727 to 730, and the new alerts had been inserted. The position in the state file also matched the end of `alerts.json`.

# Chapter 3: Testing Duplicate Handling on the Real DB

## 3.1 The Approach

In Parts 4 and 6 we tested duplicate handling with a mock connection. Here we use the production Collector code and the real PostgreSQL (with `wazuh_collector`'s privileges), do everything inside an outer transaction, and always roll back at the end. No test data remains in the production table.

When `connection.transaction()` is called while already inside a transaction, it becomes a savepoint. So even if a duplicate causes an error, only that savepoint is rolled back, and the next event should be processable on the same connection.

## 3.2 The Test

**Run on: security-core VM 220 (root)**

⟦C9⟧

| Check | Meaning |
|---|---|
| `initial test event inserted` | The first row was inserted |
| `duplicate event handled` | The second row with the same ID was handled as `UniqueViolation` |
| `transaction remains usable after duplicate` | The transaction is still usable after the duplicate |
| `next event processed on same connection` | Another event could be inserted on the same connection |
| `no test rows committed` | Everything was rolled back at the end |

## 3.3 Confirming That No Test Data Remains

**Run on: LXC 109 postgresql (root)**

⟦C10⟧

If `remaining_test_events` is `0`, not a single test row remains.

# Chapter 4: Isolated Tests Using the Production Code

From here on, we load the production `collector.py` as a Python module, replace only the file paths with a temporary directory, and test the actual functions. `run()` is not started, so the production service, log, state file and DB are not touched.

> The old test copies (`/tmp/wazuh-collector-rotation-test.py` and others) do not contain the fixes made after deployment to production. Also, running them as they are starts the resident loop using the production paths. Always run the tests by loading the production code and replacing the paths.

## 4.1 Resuming and Refusing at Startup

**Run on: security-core VM 220 (root)**

⟦C11⟧

| Test | Result |
|---|---|
| Resume from the saved position in the current file | Resumes |
| Resume from an old file in a subdirectory | Resumes |
| Old inode not found | Refuses to start |
| Position larger than the current file | Refuses to start |
| Position larger than the old file | Refuses to start |

## 4.2 Incomplete Lines and Rotation

With the production `read_alert_line()`, `safe_open_current_alert_file()` and `save_state()`, confirm that a JSON line that was half-written just before rotation is not inserted into the DB, and that reading restarts from the normal lines of the new file.

**Run on: security-core VM 220 (root)**

⟦C12⟧

`STATE_FILE` is also replaced with the temporary directory, so the production state file does not change.

# Chapter 5: Handling Huge Alert Lines

## 5.1 The Limit and Chunked Reading

The production Collector limits a line to 1 MiB (`MAX_ALERT_LINE_BYTES` = 1,048,576 bytes) and discards lines over the limit 64 KiB (`READ_CHUNK_BYTES` = 65,536 bytes) at a time. Test a line exactly at the limit, a line over the limit, a line discarded over many reads, and a line that reaches the end of the file without a newline.

**Run on: security-core VM 220 (root)**

⟦C13⟧

## 5.2 Rotation While Discarding

Confirm that when the end of the file is reached while discarding a huge line and a rotation happens meanwhile, the Collector switches to the new file and the discarding state is reset.

**Run on: security-core VM 220 (root)**

⟦C14⟧

## 5.3 Saving the Position After Discarding and Resuming

Confirm that the position after discarding a huge line is saved and that after a restart the Collector resumes from the next line. `load_state()` returns an `(inode, offset)` pair (tuple).

**Run on: security-core VM 220 (root)**

⟦C15⟧

This test may also be run in an ordinary user's (`ag`) shell. It does not write to production files.

# Chapter 6: Boundary Values for Input Validation

## 6.1 Boundary-Value Tests

Confirm that the production `extract_event()` rejects or truncates malformed values, out-of-range values and overly long strings, and outputs only the defined fields. `full_log` and unexpected fields do not end up in what is inserted into the DB.

**Run on: security-core VM 220 (root)**

⟦C16⟧

| Item | Limit / handling |
|---|---|
| Description | 4096 characters; control characters removed |
| Groups | 64 |
| Time | Values without a time zone and invalid values are rejected |
| Rule ID / level | Out-of-range values, booleans and mixed-in strings are rejected |
| IP address / port | Invalid values become empty (`None`) |
| Output | Only the defined 13 fields |

## 6.2 Oversized Input and Abnormal Nesting

**Run on: security-core VM 220 (root)**

⟦C17⟧

At build time all six items passed. The MITRE arrays are limited to 32 `id` values, 16 `tactic` values and 32 `technique` values. No change to the production code and no restart were needed.

# Chapter 7: DB Failures and the Read Position

## 7.1 The Order of Processing in run()

Before reading a line, the production `run()` remembers the position of the start of the line (`line_start`) and goes back to it on failure. The behavior confirmed by reading the code at build time is as follows.

| Processing | Behavior |
|---|---|
| Failure to connect to PostgreSQL | Go back to the start of the line and reconnect after 5 seconds |
| Failure to insert / process | Go back to the start of the line and discard the connection |
| Failure to save the state | Go back to the start of the line and process it again |
| Duplicate event | Treat SQLSTATE `23505` as processed |
| Line over the limit | Save the state and then skip it |
| Rotation detected | Switch to the new inode |
| At exit | Close the file and the DB connection |

## 7.2 Separating DB Errors

Using a mock connection, confirm that DB failures are passed to the caller, that only duplicates are treated as processed, and that broken JSON and invalid alerts never reach the DB.

**Run on: security-core VM 220 (root)**

⟦C18⟧

## 7.3 Rewinding to the Start of the Line

Confirm that going back to the start of a failed line reads the same event again, and that after it succeeds the next event can be read.

**Run on: security-core VM 220 (root)**

⟦C19⟧

# Chapter 8: State File Anomalies

## 8.1 Anomalies When Loading the State

Confirm that broken JSON, wrong types, out-of-range numbers and permission errors on reading all lead to refusing to start (`collector state is invalid`), and that only a missing state file is treated as reading from the beginning (`None`).

**Run on: security-core VM 220 (root)**

⟦C20⟧

## 8.2 Anomalies When Restoring the inode and Position

**Run on: security-core VM 220 (root)**

⟦C21⟧

Permission errors while searching directories are not swallowed and lead to refusing to start. (This confirms that the same path that kept production from starting in Part 5 now stops correctly.)

# Chapter 9: Failures When Saving the State, and a File Descriptor Fix

## 9.1 Failures Partway Through Saving

`save_state()` creates a temporary file in the same directory, sets its permissions to `600`, writes it, calls `fsync()`, replaces the target with `os.replace()`, and finally calls `fsync()` on the directory. Check whether the old state file remains when it fails partway.

**Run on: security-core VM 220 (root)**

⟦C22⟧

| Where it failed | Result |
|---|---|
| File `fsync()` | The old state remains |
| `os.replace()` | The old state remains |
| Directory `fsync()` | Replaced with the new state (durability on power loss is not guaranteed) |

In every case, no temporary file is left behind.

## 9.2 Checking That File Descriptors Are Released

Check whether the temporary file opened by `mkstemp()` is closed even when setting the permissions (`fchmod()`) fails.

**Run on: security-core VM 220 (root)**

⟦C23⟧

At build time, `FAIL: descriptor leaked after fchmod failure` was shown. The temporary file is deleted, but when `fchmod()` fails the file descriptor is left open. This is fixed in the next section.

## 9.3 The Fix and a Backup

Change it so that the file descriptor is handed to a file object with `os.fdopen()` and `fchmod()` is done inside that `with`. Even if `fchmod()` fails, the file is closed when leaving the `with`.

First back up the production file.

**Run on: security-core VM 220 (root)**

⟦C24⟧

Confirm that the two hashes are the same (`df4a9ff6...` at build time).

## 9.4 Testing the Fix on a Temporary Copy

Rewrite the production code into a temporary copy and confirm that no file descriptor leaks.

**Run on: security-core VM 220 (root)**

⟦C25⟧

Then run the test from 9.1 against the fixed temporary copy and confirm that the previous behavior has not changed.

⟦C26⟧

## 9.5 Checks Before Deploying

**Run on: security-core VM 220 (root)**

⟦C27⟧

Confirm `inode_match: True` and `offset_within_file: True`.

## 9.6 Deploying the Fix to Production

After checking the hashes of production and the backup, rewrite only the relevant part and replace the file in one step, keeping its owner and permissions.

**Run on: security-core VM 220 (root)**

⟦C28⟧

Replace the `expected` value with your environment's production hash (before deployment). At build time, the hash after deployment was `a2015974...`, the owner `root:root` and the permissions `755`.

## 9.7 Checks After Deploying

**Run on: security-core VM 220 (root)**

⟦C29⟧

Confirm that the only difference is one place in `save_state()`.

Finally, load the production code and check the fixed behavior in a temporary directory.

⟦C30⟧

> The service has not been restarted at this point. The running Collector process (PID `91473` at build time) keeps running the pre-deployment code until it is restarted. The fixed file is used from the next time the service restarts.

# Chapter 10: Adding Validation of the Values Saved

## 10.1 Checking the Boundaries on the Loading Side

`load_state()` validates the inode and position with `safe_integer()`, but `save_state()` turns whatever values it receives into JSON as is. First check which values are rejected when loading.

**Run on: security-core VM 220 (root)**

⟦C31⟧

`safe_integer()` is designed to accept digit-only strings (such as `"123"`) as integers too. So correct the expected results for the two string cases to "accepted" before running it.

⟦C32⟧

When loading, 0, negative numbers, booleans, values above the limit and `None` were rejected.

## 10.2 Reproducing the Problem

If an invalid value is saved, it replaces a valid state file, and the next startup rejects it when loading, so the Collector stops. Check this with the current `save_state()`.

**Run on: security-core VM 220 (root)**

⟦C33⟧

At build time, all five became `SAVED`.

## 10.3 Testing the Fix on a Temporary Copy

At the start of `save_state()`, accept only integers from `1` to `2^63-1` for the inode and from `0` to `2^63-1` for the position, and raise `ValueError` for anything else before creating the temporary file. When saving, digit strings are also rejected.

**Run on: security-core VM 220 (root)**

⟦C34⟧

Then, with the same temporary copy, confirm that saving can be retried after a failure.

⟦C35⟧

## 10.4 Backup and Checks Before Deploying

**Run on: security-core VM 220 (root)**

⟦C36⟧

## 10.5 Deploying to Production

**Run on: security-core VM 220 (root)**

⟦C37⟧

At build time the hash after deployment was `faf2c203...`. Here too the service is not restarted.

## 10.6 Checking Behavior with the Production Code

**Run on: security-core VM 220 (root)**

⟦C38⟧

# Chapter 11: Activating the Fixes (Restart)

## 11.1 Checking the Diff and Running State

**Run on: security-core VM 220 (root)**

⟦C39⟧

Confirm that the only difference is the input validation in `save_state()` (14 lines). The fixes from Chapters 9 and 10 are only in the file on disk; the running process (PID `91473` at build time) still uses the old code.

## 11.2 Restarting

Just before the restart, record the service state, that the position in the state file matches `alerts.json`, and the production hash (`faf2c203...` at build time) (you can use the output from 11.1).

**Run on: security-core VM 220 (root)**

⟦C40⟧

## 11.3 Checks After the Restart

**Run on: security-core VM 220 (root)**

⟦C41⟧

At build time it started with the new PID `92423`, showed `Wazuh alert collector starting`, and resumed from the same inode and position as before the restart.

⟦C42⟧

Set the `--since` time to when you restarted. If `PostgreSQL connection established` appears after a new alert is read, the DB connection is working.

## 11.4 Ingestion and Keeping Up with the Read Position

**Run on: LXC 109 postgresql (root)**

⟦C43⟧

At build time the count had increased from 735 to 755.

**Run on: security-core VM 220 (root)**

⟦C44⟧

| Check | Result at build time |
|---|---|
| Process | PID `92423` (UID 996 / GID 987) |
| State | `active` / `running`, restart count `0` |
| Read position | Matches the end of the file (2,762,833 bytes) |
| State file permissions | `600` |
| Errors / warnings after the restart | None |

# Chapter 12: Reprocessing Duplicates and Failed State Saves

## 12.1 Checking the Design

The insert and rotation design confirmed by reading the code at build time is as follows.

| Item | Details |
|---|---|
| Event ID | The Wazuh alert's `id` (up to 128 characters). Events without an ID are rejected |
| Insert | A normal `INSERT` (no `ON CONFLICT`) |
| State save | After the DB insert succeeds |
| Duplicates | Only SQLSTATE `23505` is treated as processed |
| Rotation | Save the new file's inode and position `0` first, then switch |

If saving the state fails after the DB insert, the same line is processed again. At that point, the event with the same ID is treated as a duplicate and is not inserted twice.

## 12.2 Reprocessing a Duplicate

Using a fake DB connection, confirm that the first time the event is inserted, reprocessing the same event is treated as a processed duplicate, and the next, different event is inserted.

**Run on: security-core VM 220 (root)**

⟦C45⟧

## 12.3 A Failed State Save Combined with a Retry

In a temporary directory, reproduce the flow in which the DB insert succeeds, saving the state then fails, and the Collector goes back to the start of the line and processes the same event again.

**Run on: security-core VM 220 (root)**

⟦C46⟧

| Check | Result |
|---|---|
| Failed state save | The old state remains |
| Rewind to the start of the line | The same event is read again |
| Reprocessing | Treated as a duplicate; still only one row inserted |
| Saving on retry | Succeeds, with no temporary file left |

# Chapter 13: Failed Saves at Rotation and Final Checks

## 13.1 The Production Running State (Reads Only)

**Run on: security-core VM 220 (root)**

⟦C47⟧

At build time this showed PID `92423`, restart count `0`, and `inode_match`, `offset_within_file` and `state_at_eof` all `True`.

## 13.2 Checking the Rotation Processing

**Run on: security-core VM 220 (root)**

⟦C48⟧

Rotation is handled in two places: when the end of the file is reached, and while reading an incomplete line. In both, the old file is kept open until saving the new file's state succeeds; if saving fails, the new file is closed and the switch is retried at the next check.

## 13.3 Rotation at End of File with a Failed Save

**Run on: security-core VM 220 (root)**

⟦C49⟧

## 13.4 Rotation in the Middle of an Incomplete Line with a Failed Save

**Run on: security-core VM 220 (root)**

⟦C50⟧

In both cases, even when saving failed once, the old file and state were kept; on the second attempt it switched to the new file and correctly read the first line of the new file. No change to the production code was needed.

# Summary of Part 7

## History of Changes to the Production Collector (Part 7)

| Stage | SHA-256 | Change | Activated by |
|---|---|---|---|
| End of Part 6 | `ac297477...` | Recursive search for the old file | — |
| 1.3 | `df4a9ff6...` | Read position validation | Restart in 1.4 |
| 9.6 | `a2015974...` | File descriptor fix in state saving | Restart in 11.2 |
| 10.5 | `faf2c203...` | Validation of the values saved | Restart in 11.2 |

## Backups

| File | Contents |
|---|---|
| `collector.py.backup-before-step330-offset-20261119` | `ac297477...` |
| `collector.py.backup-before-step330-28d-20261119` | `df4a9ff6...` |
| `collector.py.backup-before-step330-29g-20261119` | `a2015974...` |

## Failure Cases Verified

| Category | Details | Chapter |
|---|---|---|
| DB | Duplicates and savepoints (real DB, rollback only) | Chapter 3 |
| Startup | Resuming, missing old inode, position too large | Chapter 4 |
| Reading | Incomplete lines, lines over 1 MiB, rotation while discarding | Chapters 4 and 5 |
| Input | Boundary values, oversized input, abnormal nesting, wrong types | Chapter 6 |
| DB failures | Propagating failures, treating only duplicates as processed, rewinding to the start of the line | Chapters 7 and 12 |
| State file | Broken contents, permission errors, search errors | Chapter 8 |
| Saving the state | Failures of `fsync` and replacement, file descriptors, invalid values | Chapters 9 and 10 |
| Rotation | Failed saves and retries (at end of file and on incomplete lines) | Chapter 13 |

## State at the End of Part 7

| Item | State |
|---|---|
| Collector | `active` / `running` (PID `92423`, restart count `0`) |
| Production code | `faf2c203...` |
| Read position | Matches the end of `alerts.json` |
| DB | 755 rows (at build time), no test data left |

## Open Issues

| Issue | Details |
|---|---|
| Resuming from an old file after compression | If, while the Collector is stopped, the old file it was partway through (`alerts/year/month/ossec-alerts-DD.json`) is compressed (`.json.gz`), the file with the saved inode cannot be found and the Collector refuses to start (a design that stops on the safe side). A recovery procedure for this case was not created at build time. |

> Do not leave the Collector stopped for a long time. If you restart it before the date changes and rotation and compression take place, this state does not occur.

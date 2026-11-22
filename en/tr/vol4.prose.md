---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 4: Auditing the Collector and Developing a Hardened Version"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 4 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". We audit the alert-storage Collector put into operation in Part 3 and fix the weaknesses found, working on a test copy without stopping production.

| Approach | Details |
|---|---|
| Audit | Check input validation, the read position and the rotation method against the actual files and code |
| Preservation | Make a complete backup of the code before the improvements |
| Development | Modify only a test copy in `/tmp` and verify it with unit tests |
| Production | Part 4 does not change the production Collector (it is deployed in Part 5) |

## Notation

- Commands and file contents are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Each step begins with "Run on", which says where to run it.
- "Example output" is the actual output from the build. In your environment, inodes, sizes, dates and so on will differ.
- The contents of credentials and the state file are not shown.

## State at the End of Part 3

| Item | State |
|---|---|
| Collector | `/usr/local/lib/wazuh-collector/collector.py` (9,626 bytes) |
| Service | `wazuh-collector.service` (active, enabled) |
| Storage | `incident.alert_events` in the `security_workbench` DB on LXC 109 |
| DB role | `wazuh_collector` (INSERT only) |

# Chapter 1: Auditing the Running Collector

This chapter only examines files. No settings are changed and no services are restarted.

## 1.1 Checking the Second Half of the Code

After the input validation (lines 78–186), check the processing for saving state, resuming and rotation.

**Run on: security-core VM 220 (root)**

⟦C0⟧

The audit found that the basic design was sound, but there was room for improvement in the following points.

| Category | Item | Assessment |
|---|---|---|
| Good | Saving the state file | Uses a temporary file, fsync and atomic replacement |
| Good | Order of DB insert and state save | Saves the read position only after the DB insert succeeds |
| Good | Duplicate handling | Treats only `UniqueViolation` as a duplicate |
| Needs work | Input line size | No limit on the length of a line |
| Needs work | Validation of numbers and strings | Accepts booleans as integers; does not remove control characters |
| Needs work | Rotation | Insufficient handling of unread data left in the old file after a switch |

## 1.2 Investigating the Rotation Method

**Run on: security-core VM 220 (root)**

⟦C1⟧

logrotate had no matching configuration, and both `alerts.json` and `alerts.log` had a link count of 2. Check the Wazuh settings and the link relationships.

⟦C2⟧

⟦C3⟧

Replace the `-inum` value with the inode of your environment shown by the previous command.

| File | inode | Link count |
|---|---:|---:|
| `alerts.json` | 5409146 | 2 |
| `2026/Nov/ossec-alerts-18.json` | 5409146 | 2 |
| `alerts.log` | 5398501 | 2 |

Wazuh **shares the current log and the per-day archive through a hard link**. When the date changes it switches to a new file, and the previous day's file is compressed.

## 1.3 Rotation Settings and Compressed Archives

**Run on: security-core VM 220 (root)**

⟦C4⟧

| Setting | Value | Meaning |
|---|---:|---|
| `monitord.day_wait` | 10 seconds | Wait after the daily rotation |
| `monitord.compress` | 1 | Compress |
| `monitord.sign` | 1 | Sign |
| `monitord.rotate_log` | 1 | Rotate daily |
| `monitord.keep_log_days` | 31 | Days to keep |

⟦C5⟧

> Rotation is not done by a separate systemd service but by the `wazuh-monitord` process inside the Wazuh Manager.

Check the format and integrity of the compressed archives.

⟦C6⟧

⟦C7⟧

If `gzip exit code: 0` is shown, the compressed data is intact.

## 1.4 Checking the Read Position and Running State

**Run on: security-core VM 220 (root)**

⟦C8⟧

It is normal if the inode in the state file is the same as the current `alerts.json` and the read position equals the end of the file.

⟦C9⟧

At build time it was running stably with 0 restarts and about 18 MiB of memory.

## 1.5 Backing Up Before the Improvements

The backup from Part 3, 9.4 predates the fix to duplicate handling. Its hash differs from the current code, so make a new backup to return to the state before the improvements.

**Run on: security-core VM 220 (root)**

⟦C10⟧

| File | Size | SHA256 (prefix) |
|---|---:|---|
| Existing backup (before the duplicate-handling fix) | 9,487 bytes | `132c9e33...` |
| Current code | 9,626 bytes | `931ee3cb...` |

⟦C11⟧

If the two SHA256 values match, you can return to the state before the improvements at any time.

## 1.6 Improvement Plan

Based on the audit, we improve the following in this order.

1. `safe_integer()`: do not accept booleans (`true`/`false`) as integers.
2. `safe_text()`: remove control characters and limit the length.
3. `rule_groups`: limit the number of elements and the length of each string.
4. `mitre`: strictly limit the allowed keys and the types and number of values.
5. Put a limit on the length of a line and safely skip huge lines.
6. Make sure nothing is left unread in the old file around a rotation.

All improvements are made on a test copy. First, check the beginning and end of the current code.

⟦C12⟧

⟦C13⟧

The end is guarded by `if __name__ == "__main__":`, so loading it as a module in tests does not start `run()`.

# Chapter 2: The Test Copy and Stronger Input Validation

## 2.1 Creating the Test Copy

Without touching the production code, create a copy just for testing in `/tmp`.

**Run on: security-core VM 220 (root)**

⟦C14⟧

Confirm that the two SHA256 values match. All subsequent changes in Part 4 are made to this test copy.

> Files in `/tmp` may disappear when the VM restarts. Do the work of Part 4 continuously, without restarting in between.

## 2.2 Improving Input Validation

Show the parts to be improved.

⟦C15⟧

| Function / item | Current problem | Improvement |
|---|---|---|
| `safe_integer` | `True` is accepted as the integer 1 | Reject booleans and accept only decimal digit strings |
| `safe_text` | Allows newlines and control characters | Remove control characters and turn empty strings into None |
| `rule_groups` | No limit on the number of elements | Up to 64 elements of up to 256 characters each (`safe_string_list`) |
| `mitre` | Accepts values of any type and number | Accept only `id`, `tactic` and `technique`, with limits on type and number (`safe_mitre`) |

Replace everything from `safe_integer()` to just before `extract_event()`, and switch the handling of `groups` and `mitre` inside `extract_event()` to the new functions.

**Run on: security-core VM 220 (root)**

⟦C16⟧

It is done when `Test copy updated successfully` and `Python syntax: PASS` are shown.

## 2.3 Unit Tests for Input Validation

**Run on: security-core VM 220 (root)**

⟦C17⟧

⟦C18⟧

## 2.4 Checking Compatibility with Real Alerts

Check that the stricter validation does not wrongly reject real Wazuh alerts. This only reads the production `alerts.json` and does not connect to the DB.

**Run on: security-core VM 220 (root)**

⟦C19⟧

At build time, all 1,406 alerts were accepted (0 rejected, 0 JSON errors), giving `READ-ONLY COMPATIBILITY TEST: PASS`.

# Chapter 3: A Size Limit per Line

## 3.1 Checking the Reading Code

**Run on: security-core VM 220 (root)**

⟦C20⟧

⟦C21⟧

Currently a whole line is read with `handle.readline()`, so memory use cannot be limited if there is a very long line. When adding a size limit, the following properties must be kept.

1. A line whose newline has not been written yet is read next time, after rewinding the read position.
2. The state file is updated only after the DB insert succeeds.
3. When the DB fails, the same line can be processed again.
4. A line over the limit is skipped up to the next newline without being held in memory.

Check the line numbers of the places to change.

⟦C22⟧

## 3.2 Adding the Limit Constants

Set the limit for one line to 1 MiB and the skip unit to 64 KiB.

**Run on: security-core VM 220 (root)**

⟦C23⟧

## 3.3 A Reading Function with a Size Limit

The reading function `read_alert_line()` returns one of the following five states.

| State | Meaning | What the Collector does |
|---|---|---|
| `line` | A normal line | Processes it and inserts it into the DB |
| `incomplete` | The newline has not been written yet | Rewinds the read position and waits |
| `oversized` | Skipped to the end of a line that exceeded the limit | Saves the position after the skip |
| `eof` | End of file | Checks for rotation and waits |
| `discarding` | In the middle of skipping a line that exceeded the limit | Continues skipping on the next read |

Add the function just before `process_line()`.

**Run on: security-core VM 220 (root)**

⟦C24⟧

## 3.4 Fixing the Newline Check

Check the contents of the added function.

⟦C25⟧

Because `\\\\n` was written inside a string enclosed in `'''`, the file contains `b"\\n"` (two characters: a backslash and `n`). This cannot detect an actual newline. Fix the three places to `b"\n"`.

**Run on: security-core VM 220 (root)**

⟦C26⟧

If `Corrected newline checks: 3` is shown, the fix is done.

## 3.5 Unit Tests for the Reading Function

Verify with data in memory, without using the actual log or DB. In the tests, the limit is reduced to 16 bytes and the skip unit to 8 bytes.

**Run on: security-core VM 220 (root)**

⟦C27⟧

It has succeeded if all five items are `PASS` and `ALL BOUNDED READER TESTS PASSED` is shown.

# Chapter 4: Building It into the Reading Loop

## 4.1 Checking and Backing Up the Loop Before the Change

Before building the reading function into `run()`, check how state is saved and loaded and how the initial file is chosen.

**Run on: security-core VM 220 (root)**

⟦C28⟧

⟦C29⟧

⟦C30⟧

`save_state()`, which saves the inode and read position atomically, `load_state()`, which restores the position on restart, and `open_initial_file()`, which looks for the previous file, can be used as they are.

⟦C31⟧

Also back up the test copy itself.

⟦C32⟧

## 4.2 The New Reading Loop

Replace `run()` so that it works in the following order.

1. First read one line of the log (`read_alert_line()`).
2. Skip a line over the limit without connecting to the DB, and save the position where the skip ended.
3. Check the DB connection only for normal lines. If the connection fails, go back to the start of that line.
4. Save the read position only after the DB insert succeeds.
5. For a line with no newline yet, go back to the start of the line and wait.

In this order, skipping huge lines makes progress even when the DB is down, and no normal line is lost.

**Run on: security-core VM 220 (root)**

⟦C33⟧

⟦C34⟧

## 4.3 Testing with the DB Down

Run the actual `run()` with a mock that always fails to connect to the DB. `save_state` is also replaced with a mock, so the production state file is not changed.

**Run on: security-core VM 220 (root)**

⟦C35⟧

| Check | Meaning |
|---|---|
| `OVERSIZED LINE PROCESSED WITHOUT DB` | A huge 41-byte line was skipped without connecting to the DB |
| `OFFSET SAVED BEFORE DB CONNECTION` | The position after the skip (41) was saved before connecting to the DB |
| `NORMAL LINE POSITION RESTORED ON DB FAILURE` | The next normal line went back to its start (41) because the DB connection failed |
| `PRODUCTION STATE FILE NOT MODIFIED BY TEST` | The test did not change the production state file |

> **Important:** If you run `run()` without replacing `module.save_state` with a mock, the real `save_state()` rewrites the production state file (`/var/lib/wazuh-collector/state.json`). In tests that use `run()`, always replace the state-saving function.

# Chapter 5: Not Leaving Data Unread at Rotation

## 5.1 The Problem

The current `run()` has two problems related to rotation.

1. If it reaches the end of the file (EOF) while skipping a huge line, it keeps waiting without checking the inode.
2. A line with no newline yet (`incomplete`) goes back to the same position every time, so it never reaches the EOF handling.

In both cases, when Wazuh moves to a new file at the date change, the Collector stays stuck on the old file. The fix is: **if the inode of the current `alerts.json` has changed, discard the incomplete line in the old file with a warning and read the new file from the beginning**. While the inode has not changed, the line may still be being written, so it keeps waiting.

**Run on: security-core VM 220 (root)**

⟦C36⟧

⟦C37⟧

Back up before the fix.

⟦C38⟧

## 5.2 Detecting Rotation at EOF

Open the new file and switch to it only after the state is saved successfully. If saving fails, close the new file and keep waiting on the old file.

**Run on: security-core VM 220 (root)**

⟦C39⟧

`py_compile` shows nothing when it succeeds, so check again.

⟦C40⟧

## 5.3 Detecting Rotation on an Incomplete Line

**Run on: security-core VM 220 (root)**

⟦C41⟧

⟦C42⟧

## 5.4 Reporting EOF While Skipping

`read_alert_line()` returned `discarding` when it reached the end of the file while skipping. That never reaches the EOF handling in `run()` (5.2). Change it to return `eof`. The fact that it is skipping is still kept in the `discarding` variable on the `run()` side, so the warning can still be given at rotation.

**Run on: security-core VM 220 (root)**

⟦C43⟧

⟦C44⟧

Check the reading function. With `READ_CHUNK_BYTES = 8`, `b"abcdefgh\n"` (9 bytes) does not reach the newline on the first read, giving `discarding`, and gives `oversized` on the second.

⟦C45⟧

## 5.5 Integration Test for Rotation

Create an old file and a new file in a temporary directory and check the switch with the actual `run()`. The production log, DB and state file are not touched.

**Run on: security-core VM 220 (root)**

⟦C46⟧

When an incomplete line remains in the old file:

⟦C47⟧

When rotation happens while skipping a huge line (40 bytes are skipped 8 bytes at a time, so the loop continues until the state is saved and then stops):

⟦C48⟧

If all four items are `PASS` in both cases, the Collector moves to the new file after rotation whether an incomplete line or a huge line remains.

## 5.6 Checking the Structure

**Run on: security-core VM 220 (root)**

⟦C49⟧

Confirm `PYTHON SYNTAX: PASS` and `REQUIRED FUNCTIONS: PASS`. At build time there were 14 functions and the test copy was 15,201 bytes.

# Chapter 6: Comprehensive Tests for Sensitive Information and Input Validation

## 6.1 Static Checks of the Source Code

Using the syntax tree, check whether `full_log` is referenced, what the INSERT statement targets, and whether there are log strings containing passwords or the like.

**Run on: security-core VM 220 (root)**

⟦C50⟧

Confirm that there is no reference to `full_log`, that the INSERT targets only the 13 permitted columns, and that there are no log strings containing secrets.

Also check the whole source by eye.

⟦C51⟧

⟦C52⟧

## 6.2 Testing That Sensitive Information Is Not Stored

Put secret values in every part of an alert and confirm that not a single character of them remains in the data inserted into the DB.

**Run on: security-core VM 220 (root)**

⟦C53⟧

## 6.3 Fixing the Control-Character Filter

Check whether control characters are removed.

**Run on: security-core VM 220 (root)**

⟦C54⟧

At build time, newlines, tabs and NUL were removed, but DEL (`0x7f`) remained (`AssertionError`).

⟦C55⟧

The cause was that `"\\\\x7f"` had been written inside `'''` in 2.2, so the file contained a comparison not with the DEL character but with the four-character string `\x7f` (the same cause as the newline check in 3.4). Check the line concerned.

⟦C56⟧

Replace it with a condition that removes C1 control characters (`0x80`–`0x9f`) as well as DEL. Back up before the fix.

⟦C57⟧

Check how the target line is actually written, using `repr`.

⟦C58⟧

If it is shown as follows, the line has the fixed condition.

⟦C59⟧

> In the original build, the replacement command showed `Expected exactly one target, found 0`, but this check showed that line 131 already had the fixed content. Even if it says "found 0", always judge the actual content with this `repr` check.

Retest C0, DEL and C1 control characters together.

⟦C60⟧

## 6.4 Boundary-Value Tests for Each Validation Function

**Run on: security-core VM 220 (root)**

Strings (`safe_text`):

⟦C61⟧

Integers (`safe_integer`):

⟦C62⟧

IP addresses (`safe_ip`):

⟦C63⟧

Lists of strings (`safe_string_list`):

⟦C64⟧

MITRE information (`safe_mitre`):

⟦C65⟧

| Function | What was checked |
|---|---|
| `safe_text` | Maximum 4,096 characters, trimming of surrounding whitespace, rejection of whitespace-only strings and non-strings |
| `safe_integer` | Boundary values; rejection of booleans, decimals, signed values, full-width digits and 21 or more digits |
| `safe_ip` | IPv4, IPv6 normalization; rejection of CIDR notation, host names and empty values |
| `safe_string_list` | Maximum 64 elements of 256 characters each; invalid elements excluded |
| `safe_mitre` | Only three keys allowed; at most 32 `id` values |

## 6.5 Checking the Test Version and the Production State

**Run on: security-core VM 220 (root)**

⟦C66⟧

⟦C67⟧

Confirm that the production Collector (`931ee3cb...`) has not changed, that its content differs from the test version (15,215 bytes at build time), and that the production service is still `active`.

Also check that the production read position matches the current `alerts.json` (the values in the state file themselves are not shown).

⟦C68⟧

# Chapter 7: Making the State File and inode Handling Strict

## 7.1 The Problems

**Run on: security-core VM 220 (root)**

⟦C69⟧

⟦C70⟧

⟦C71⟧

The check found the following three problems.

| Place | Problem | Fix |
|---|---|---|
| `load_state()` | Converts with `int()`, so `true` is also accepted as an integer | Validate range and type with `safe_integer()` |
| `open_initial_file()` | Saves the inode from `stat()` taken before opening the file | Use the inode from `os.fstat()` on the opened file |
| Rotation in `run()` | If another rotation happens between `stat()` and `open()`, the saved inode and the file actually opened differ | Save the inode from `os.fstat()` right after opening |

Back up before the fix.

⟦C72⟧

## 7.2 Validating the Values in the State File

Accept only integers within the range of a 64-bit signed integer, with the inode 1 or more and the read position 0 or more.

**Run on: security-core VM 220 (root)**

⟦C73⟧

Test with a state file in a temporary directory (the production state file is not touched).

⟦C74⟧

## 7.3 Fixing How the Initial File Is Opened

**Run on: security-core VM 220 (root)**

⟦C75⟧

Replace the whole of `open_initial_file()`. Right after opening, get the actual inode and size with `os.fstat()` and save that inode in the state. If an exception occurs partway, close the file.

⟦C76⟧

⟦C77⟧

Test three cases in a temporary directory: first startup, resuming from a rotated file, and the old file being missing.

⟦C78⟧

## 7.4 Fixing the inode at Rotation

In both the incomplete-line case (5.3) and the EOF case (5.2), get the inode again with `os.fstat()` right after opening the new file. If the opened file has the same inode as the old file, do not switch; wait.

**Run on: security-core VM 220 (root)**

For an incomplete line:

⟦C79⟧

⟦C80⟧

At EOF:

⟦C81⟧

⟦C82⟧

⟦C83⟧

## 7.5 Checking the inode Fix

Extract the source of `run()` from the syntax tree and check that both places use the actual inode.

**Run on: security-core VM 220 (root)**

⟦C84⟧

Actually run `run()`, rotate the file while it is waiting, and check that the saved inode matches that of the new file.

⟦C85⟧

If both `EOF ROTATION` and `INCOMPLETE ROTATION` are `PASS`, the inode saved after rotation matches the new file actually opened.

# Chapter 8: Overall Verification of the Test Version

By the end of Chapter 7, the main improvements are in the test version. In this chapter we verify the test version again, function by function. The DB, the production state file and the production Collector are not touched.

## 8.1 Safety on Import and the Production State

**Run on: security-core VM 220 (root)**

⟦C86⟧

Confirm that `run()` does not run when it is loaded as a module.

⟦C87⟧

Production is still `root:root 755 9626`, and the service is `active`.

## 8.2 Listing the Functions and Checking run()

**Run on: security-core VM 220 (root)**

⟦C88⟧

At build time there were 14 functions, ending with `open_initial_file` (lines 322–370), `read_alert_line` (lines 373–416), `process_line` (lines 419–438) and `run` (lines 441–618). Line numbers may differ in your environment, so adjust the `sed` ranges that follow to this output.

⟦C89⟧

⟦C90⟧

## 8.3 Boundary-Value Tests for Line Size

With the real limit (1 MiB), check four cases: exactly at the limit, over the limit, no newline, and a very large line.

**Run on: security-core VM 220 (root)**

⟦C91⟧

| Case | Result |
|---|---|
| Exactly 1 MiB (including the newline) | `line` |
| Over 1 MiB | `oversized` |
| No newline | `incomplete` |
| 1 MiB + about 200 KB | `discarding` |

Confirm that after discarding a huge line 64 KiB at a time, the next normal line can be read.

⟦C92⟧

At build time, it was discarded in four chunks, and the normal line right after it was read.

## 8.4 Managing the State File

**Run on: security-core VM 220 (root)**

⟦C93⟧

Check saving and loading, permissions `0600`, replacement and rejection of invalid values in a temporary directory.

⟦C94⟧

## 8.5 DB Insert and Duplicate Handling

Check the INSERT statement, the DB settings and how `event_id` is made.

**Run on: security-core VM 220 (root)**

⟦C95⟧

> This command only displays the file. `.pgpass` and the DB password are not shown. If the output ever contains secrets, do not paste it anywhere.

⟦C96⟧

⟦C97⟧

| Item | Result |
|---|---|
| Connection | TLS `verify-full`, dedicated user `wazuh_collector` |
| SQL | INSERT only; `ON CONFLICT` is not used |
| Target columns | Whitelist of 13 fields |
| `event_id` | The Wazuh alert's `id` (up to 128 characters); the same ID results even if reprocessed |
| Duplicate handling | `UniqueViolation` is caught outside `connection.transaction()`, so the transaction is reliably rolled back |

Mock the DB connection and check three cases: a successful insert, a duplicate, and another DB error.

⟦C98⟧

## 8.6 Reprocessing After a Failed State Save

Consider the case where the DB insert succeeds but saving the state file fails. The Collector goes back to the start of the line and processes the same alert again; the second time it is discarded as a duplicate, and only one row remains in the DB. Check this flow.

**Run on: security-core VM 220 (root)**

⟦C99⟧

| Check | Result |
|---|---|
| First insert | Succeeds |
| State save fails and rewinds | Goes back to the start of the line |
| Second processing | Detected as a duplicate and discarded |
| Rows remaining in the DB | 1 |

> Dropping `ON CONFLICT` in Part 3 and handling duplicates with `UniqueViolation` is what provides the safety here that "reprocessing never inserts twice".

## 8.7 Differences from Production

Finally, check the diff between the production code and the test version. This only displays it and changes nothing.

**Run on: security-core VM 220 (root)**

⟦C100⟧

The differences fall into the following five areas.

1. Stricter, whitelisted input values for alerts (Chapters 2 and 6)
2. Validation of the values in the state file (Chapter 7)
3. Rotation handling based on the inode of the file actually opened (Chapters 5 and 7)
4. A 1 MiB per-line limit and gradual skipping of huge lines (Chapters 3 and 4)
5. Rewinding the read position when the DB connection fails (Chapter 4)

⟦C101⟧

# Chapter 9: Exception Handling for File Operations and Final Checks

## 9.1 Listing the File Operations

Using the syntax tree, list every line that calls `stat`, `open`, `fstat`, `close`, `seek`, `tell` or `readline`.

**Run on: security-core VM 220 (root)**

⟦C102⟧

⟦C103⟧

| Place | Problem | Approach |
|---|---|---|
| Rotated file in `open_initial_file()` | If `fstat()` or `seek()` fails after opening, the file stays open | On failure, close the file and pass the exception to the caller |
| `stat()` and `open()` at rotation in `run()` | Processing stops on an `OSError` other than `FileNotFoundError` | Silently skipping an unreadable file would lose alerts, so exit with the exception and let systemd restart it (9.3) |

> We do not swallow every `OSError` uniformly. Continuing while a file cannot be read would lead to lost alerts.

## 9.2 Fixing How Rotated Files Are Opened

Back up before the fix.

**Run on: security-core VM 220 (root)**

⟦C104⟧

⟦C105⟧

⟦C106⟧

⟦C107⟧

With a fake file whose `fstat()` fails, confirm that the exception is passed on and the file is closed. No real file is used.

⟦C108⟧

## 9.3 Unexpected Exceptions and systemd's Automatic Restart

Even if the Collector exits on an unexpected `OSError`, it can resume from the saved read position once systemd restarts it. Check the restart settings of the production service (the settings are not changed).

**Run on: security-core VM 220 (root)**

⟦C109⟧

⟦C110⟧

## 9.4 Checking the Unique Constraint

Reprocessing after a restart does not insert twice because of the unique constraint on `event_id`. Check the table's indexes. The Collector's `.pgpass` is in a dedicated location, so specify it with `PGPASSFILE`.

**Run on: security-core VM 220 (root)**

⟦C111⟧

> If `PGPASSFILE` is not specified, psql looks for the standard `~/.pgpass` and fails with `fe_sendauth: no password supplied`. If the result is shown in a pager (`less`), press `q` to quit.

⟦C112⟧

`alert_events_pkey` is the unique index on `event_id`. This confirms that double inserts are prevented in the following flow.

1. The DB insert succeeds.
2. A failure occurs before the state is saved, and the Collector exits.
3. systemd restarts the Collector 5 seconds later.
4. The same alert is processed again from the saved read position.
5. It is rejected by the unique constraint on `event_id` and skipped as `Duplicate alert skipped`.

## 9.5 Checking the Production State

**Run on: security-core VM 220 (root)**

⟦C113⟧

The production Collector is `active`, has restarted 0 times, and its SHA-256 is still `931ee3cb...`, the same as at the start of Part 4. All work in Part 4 was done only on the test copy.

# Summary of Part 4

In Part 4 we audited the running Collector without stopping it and made the following improvements in the test copy `/tmp/wazuh-collector-hardening-test.py`.

| Area | Improvement | Chapter |
|---|---|---|
| Input validation | Reject booleans, remove control characters (C0, DEL, C1), limits on lists and MITRE information | Chapters 2 and 6 |
| Line size | 1 MiB per-line limit, skipping in 64 KiB units | Chapters 3 and 4 |
| DB failure | Huge lines are handled without the DB; normal lines are rewound when the connection fails | Chapter 4 |
| Rotation | Switch to the new file even with an incomplete line or while skipping | Chapter 5 |
| State file | Validate value types and ranges; save the inode of the file actually opened | Chapter 7 |
| Exception handling | Always close opened files; leave unexpected errors to systemd's restart | Chapter 9 |

| Backup | Contents |
|---|---|
| `/usr/local/lib/wazuh-collector/collector.py.backup-pre-hardening-20261118` | Production code before the improvements (1.5) |
| `/tmp/wazuh-collector-hardening-test.py.backup-before-*-20261118` | The test version just before each fix |

> The test version and backups in `/tmp` may disappear when the VM restarts. Do not restart security-core until it is deployed to production in Part 5.

In Part 5, we add improvements to shutdown handling, deploy the test version to the production Collector, and check restarts, an actual rotation and the match of DB inserts.

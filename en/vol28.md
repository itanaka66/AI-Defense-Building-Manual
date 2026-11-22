---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 2"
subtitle: "Part 28: Checking the Collector and Why It Stopped"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 28 of Volume 2 of the "AI Autonomous Cyber Defense System Build Manual". For the Collector that sends Wazuh alerts (`alerts.json`) to PostgreSQL (LXC 109) (`/usr/local/lib/wazuh-collector/collector.py`, Parts 3–9 of Volume 1), we do the following.

1. Read the code and check what it saves to PostgreSQL (reads only)
2. During the check, we found that the Collector had **stopped and was repeatedly restarting**, so we investigate the cause

There were two causes. They are the same as what happened in Part 9 of Volume 1.

| # | Cause |
|---|---|
| 1 | The `alerts.json` newly created by log rotation (daily) had no read ACL for the Collector |
| 2 | While looking for the file it had been reading (the saved inode), the Collector could not enter a hidden test directory created earlier (`.acl-inheritance-test.bkv8vd`) and stopped |

This book fixes the first and goes as far as identifying the second. Recovery is done in Part 29, and preventing recurrence in Part 30.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **security-core VM 220 (root)**.
- Programs that display code replace lines containing passwords, tokens, connection strings and the like with `[SENSITIVE LINE OMITTED]`.

# Chapter 1: Checking What Is Saved

## 1.1 The Functions

```bash
python3 - <<'PY'
import re
p = "/usr/local/lib/wazuh-collector/collector.py"
patterns = re.compile(
    r'^\s*(async\s+)?def\s+|^\s*class\s+|INSERT_SQL|'
    r'extract_event|process_line|full_log|audit_request_body|'
    r'field_names|UniqueViolation|SAVEPOINT|ROLLBACK TO'
)
with open(p, encoding="utf-8") as f:
    for n, line in enumerate(f, 1):
        if patterns.search(line):
            if re.search(r'password|passwd|secret|token|dsn|api_key', line, re.I):
                print(f"{n}: [SENSITIVE LINE OMITTED]")
            else:
                print(f"{n}: {line.rstrip()[:180]}")
PY
```

`extract_event()` extracts the event fields, and `process_line()` saves them with `INSERT_SQL`.

## 1.2 Fields Extracted and the INSERT

```bash
python3 - <<'PY'
p = "/usr/local/lib/wazuh-collector/collector.py"
ranges = [(41, 80), (191, 248), (504, 525)]
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
for start, end in ranges:
    print(f"\n===== collector.py:{start}-{end} =====")
    for n in range(start, min(end, len(lines)) + 1):
        line = lines[n-1]
        if any(x in line.lower() for x in ("password", "passwd", "secret", "token", "dsn", "api_key")):
            print(f"{n}: [SENSITIVE LINE OMITTED]")
        else:
            print(f"{n}: {line.rstrip()}")
PY
```

- The INSERT has a fixed set of 13 columns
- `full_log`, `audit_request_body` and the whole of the event's `data` are not saved (only `srcip` and `srcport` are taken from `data`)
- `UniqueViolation` is treated as a "duplicate" only for SQLSTATE `23505` (the same `event_id`)
- DB writes are done inside a transaction

## 1.3 How Strings Are Tidied

```bash
python3 - <<'PY'
p = "/usr/local/lib/wazuh-collector/collector.py"
ranges = [(126, 190)]
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
for start, end in ranges:
    print(f"===== collector.py:{start}-{end} =====")
    for n in range(start, min(end, len(lines)) + 1):
        print(f"{n}: {lines[n-1].rstrip()}")
PY
```

`safe_text()` removes control characters and invisible format characters, trims surrounding whitespace and limits the length. MITRE information is limited to `id`, `tactic` and `technique`. However, this processing only tidies the form; it does not find and remove passwords or user names by meaning (`rule.description`, `agent.name` and so on are saved as they are; author's notes, item 28-A).

## 1.4 The Continuous Reading Loop

```bash
python3 - <<'PY'
p = "/usr/local/lib/wazuh-collector/collector.py"
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
for n in range(526, min(590, len(lines)) + 1):
    line = lines[n-1]
    if any(x in line.lower() for x in ("password", "passwd", "secret", "token", "dsn", "api_key")):
        print(f"{n}: [SENSITIVE LINE OMITTED]")
    else:
        print(f"{n}: {line.rstrip()}")
PY
```

```bash
python3 - <<'PY'
p = "/usr/local/lib/wazuh-collector/collector.py"
ranges = [(249, 296), (458, 503), (579, 680)]
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
for start, end in ranges:
    print(f"\n===== collector.py:{start}-{end} =====")
    for n in range(start, min(end, len(lines)) + 1):
        print(f"{n}: {lines[n-1].rstrip()}")
PY
```

- When PostgreSQL cannot be reached, it goes back to the start of that line and retries 5 seconds later
- When processing fails, it also goes back to the start of the line, closes the connection and reconnects
- Connection error logs contain only the name of the exception type (no connection information)

```bash
python3 - <<'PY'
p = "/usr/local/lib/wazuh-collector/collector.py"
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
for n in range(675, min(760, len(lines)) + 1):
    line = lines[n-1]
    if any(x in line.lower() for x in ("password", "passwd", "secret", "token", "dsn", "api_key")):
        print(f"{n}: [SENSITIVE LINE OMITTED]")
    else:
        print(f"{n}: {line.rstrip()}")
PY
```

- The read position (state file) is written to a temporary file, `fsync`ed and then swapped in with `os.replace` (permissions `0600`)
- Lines that are too long are skipped without writing their contents to the log
- When the file is switched, reading starts from the beginning of the file with the new inode
- On exit, the file and the DB connection are closed

## 1.5 Validating the State File

```bash
python3 - <<'PY'
p = "/usr/local/lib/wazuh-collector/collector.py"
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
for n in range(297, 328):
    print(f"{n}: {lines[n-1].rstrip()}")
PY
```

If the contents are not a dictionary or `inode` / `offset` are not integers within range, `load_state()` stops with `RuntimeError` rather than re-reading from the beginning. Only when there is no state file is it treated as a first startup.

```bash
python3 - <<'PY'
p = "/usr/local/lib/wazuh-collector/collector.py"
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
for n in range(81, 116):
    print(f"{n}: {lines[n-1].rstrip()}")
PY
```

`safe_integer()` does not accept `bool` (a kind of `int` in Python) as an integer, and limits strings to ASCII digits, up to 20 digits. `parse_timestamp()` does not accept times without a time zone.

## 1.6 How the File Is Opened

```bash
python3 - <<'PY'
p = "/usr/local/lib/wazuh-collector/collector.py"
ranges = [(328, 457)]
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
for start, end in ranges:
    print(f"===== collector.py:{start}-{end} =====")
    for n in range(start, min(end, len(lines)) + 1):
        line = lines[n-1]
        if any(x in line.lower() for x in ("password", "passwd", "secret", "token", "dsn", "api_key")):
            print(f"{n}: [SENSITIVE LINE OMITTED]")
        else:
            print(f"{n}: {line.rstrip()}")
PY
```

- It compares the saved inode with the current file; if the file has switched, it looks for the file with the previous inode and reads the rest of it
- If the previous file cannot be found, or the saved position is larger than the file, it **stops rather than silently skipping**
- When searching directories, it does not follow symbolic links and does not look at compressed files

Despite its name, `safe_open_current_alert_file()` consisted of only the following two lines (part of the code).

```text
handle = ALERT_FILE.open("rb")
actual_stat = os.fstat(handle.fileno())
```

There is no `O_NOFOLLOW` (do not open symbolic links) and no check that it is a regular file. Check the permissions.

```bash
python3 - <<'PY'
import os
import stat
from pathlib import Path

p = Path("/var/ossec/logs/alerts")
for path in (Path("/var/ossec"), Path("/var/ossec/logs"), p, p / "alerts.json"):
    try:
        s = path.lstat()
        print(
            f"{path}: "
            f"type={'symlink' if stat.S_ISLNK(s.st_mode) else 'regular' if stat.S_ISREG(s.st_mode) else 'directory' if stat.S_ISDIR(s.st_mode) else 'other'} "
            f"owner={s.st_uid}:{s.st_gid} "
            f"mode={stat.S_IMODE(s.st_mode):04o}"
        )
    except OSError as e:
        print(f"{path}: {type(e).__name__}")
PY
```

| Target | Owner | Permissions |
|---|---|---|
| `/var/ossec` | root:110 | 0750 |
| `/var/ossec/logs` | 110:110 | 0770 |
| `/var/ossec/logs/alerts` | 110:110 | 0750 |
| `alerts.json` | 110:110 | 0640 |

`/var/ossec/logs` is writable by group 110. We judged that it does not need to change right away (author's notes, item 28-B).

# Chapter 2: The Collector Had Stopped

## 2.1 The Service State

```bash
id
```

The current shell is root. Look at the state of the Collector service.

```bash
systemctl list-units --type=service --all --no-legend | grep -i collector
```

`wazuh-collector.service` was `activating (auto-restart)` (restarting repeatedly).

```bash
systemctl show wazuh-collector.service \
  -p User -p Group -p DynamicUser -p MainPID \
  -p ExecMainCode -p ExecMainStatus \
  -p NRestarts -p Result
```

| Item | Value |
|---|---|
| `User`, `Group` | `wazuh-collector` |
| `MainPID` | 0 (no process) |
| `Result` | `exit-code` |
| `ExecMainStatus` | 1 |
| `NRestarts` | 350 |

## 2.2 The First Cause

```bash
journalctl -u wazuh-collector.service -n 50 --no-pager -o short-iso
```

It was exiting at startup because it could not open `alerts.json`.

```text
PermissionError: [Errno 13] Permission denied
/var/ossec/logs/alerts/alerts.json
```

```bash
printf '%s\n' '===== collector account ====='
id wazuh-collector
getent passwd wazuh-collector
getent group wazuh-collector
printf '%s\n' '===== directory permissions ====='
namei -l /var/ossec/logs/alerts/alerts.json
printf '%s\n' '===== ACL ====='
getfacl -p /var/ossec/logs /var/ossec/logs/alerts /var/ossec/logs/alerts/alerts.json
```

| Target | Collector's permission |
|---|---|
| `/var/ossec/logs` | `--x` through ACL (can traverse) |
| `/var/ossec/logs/alerts` | `r-x` through ACL (can traverse) |
| `alerts.json` | **No read permission** |

The `alerts` directory has a default ACL, but it was not applied to the `alerts.json` newly created by rotation (the same as Part 9, 1.3 of Volume 1).

```bash
runuser -u wazuh-collector -- test -r /var/ossec/logs/alerts/alerts.json
echo "READ_TEST_EXIT_CODE=$?"
```

`READ_TEST_EXIT_CODE=1` confirmed that it could not be read.

## 2.3 Adding a Read ACL

Add **read only** for the Collector's user. No write or delete permission is added.

```bash
setfacl -m u:wazuh-collector:r-- /var/ossec/logs/alerts/alerts.json
```

```bash
runuser -u wazuh-collector -- test -r /var/ossec/logs/alerts/alerts.json
echo "READ_TEST_EXIT_CODE=$?"
getfacl -p /var/ossec/logs/alerts/alerts.json
```

It became `READ_TEST_EXIT_CODE=0`, and the ACL was only `user:wazuh-collector:r--`.

## 2.4 The Second Cause

Check whether systemd's automatic restart got it running.

```bash
systemctl status wazuh-collector.service --no-pager -l
```

```bash
journalctl -u wazuh-collector.service -n 35 --no-pager -o short-iso
```

It was still failing to start. This time it stopped while looking for the file it had been reading (the saved inode), because it could not enter `/var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd`.

```bash
stat -c 'TYPE=%F OWNER=%U:%G MODE=%a INODE=%i PATH=%n' /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd
getfacl -p /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd
```

| Item | Value |
|---|---|
| Owner, permissions | `root:root`, `700` |
| Collector's ACL | `r-x` exists, but the ACL mask is `---` |
| Effective permission | `---` (cannot enter) |

This is the directory created when testing ACL inheritance in Part 6 of Volume 1 (recorded in Part 9 of Volume 1 as "still remaining").

```bash
find /var/ossec/logs/alerts -maxdepth 1 -name '.acl-inheritance-test*' -printf '%M %u:%g %p\n'
```

```bash
find /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd -maxdepth 2 -printf '%y %M %u:%g %s %p\n'
```

```bash
find /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd -printf '%y %M %u:%g %s %p\n'
```

It contained only `2027/Jan/test.json` (0 bytes), all `root:root`. It is not a real alert log.

## 2.5 The Search and the Saved Position

```bash
sed -n '1,80p;328,365p' /usr/local/lib/wazuh-collector/collector.py
```

`find_inode_file()` walks every directory under `alerts`, and if it cannot enter even one, it gives up the whole search (a design that errs on the safe side so as not to answer "not found" without having searched everywhere).

Compare the saved position with the current file (the state file as a whole is not shown).

```bash
python3 - <<'PY'
import json, os
from pathlib import Path

state_path = Path("/var/lib/wazuh-collector/state.json")
alert_path = Path("/var/ossec/logs/alerts/alerts.json")

try:
    state = json.loads(state_path.read_text())
    print("STATE_INODE:", state.get("inode"))
    print("STATE_OFFSET:", state.get("offset"))
except Exception as e:
    print("STATE_READ_ERROR:", type(e).__name__)

try:
    st = alert_path.stat()
    print("CURRENT_INODE:", st.st_ino)
    print("CURRENT_SIZE:", st.st_size)
except Exception as e:
    print("CURRENT_FILE_ERROR:", type(e).__name__)
PY
```

| Item | Value |
|---|---|
| Saved inode | 5409383 |
| inode of the current `alerts.json` | 5409517 |
| Saved position (offset) | 6,433,808 |
| Size of the current file | 564,829 bytes |

After the rotation, the Collector needs to find the file with the previous inode 5409383. Simply stopping the search could miss unread data in the previous file.

```bash
find /var/ossec/logs/alerts -xdev -type f -inum 5409383 -printf 'FOUND=%p SIZE=%s OWNER=%u:%g MODE=%m\n'
```

The file with inode 5409383 was not found.

```bash
sed -n '365,430p' /usr/local/lib/wazuh-collector/collector.py
```

When the previous inode cannot be found, it is designed to stop with `Previous alert file cannot be located; refusing unsafe resume`. This is a correct safety measure so that unread data is never silently skipped.

# Closing Notes

What Part 28 found is as follows.

| Item | Result |
|---|---|
| What is saved | Limited to 13 columns; `full_log` and the whole of `data` are not saved |
| How strings are tidied | Only tidies the form; it is not processing that finds and removes secrets |
| Cause of the stop 1 | The new `alerts.json` had no read ACL → **added** |
| Cause of the stop 2 | Cannot enter the hidden test directory, so it cannot search for the previous file |
| Previous file | inode 5409383 is not found (the Collector stops for safety) |

In the next part, we find out what happened to the previous file and restart the Collector without missing any events.

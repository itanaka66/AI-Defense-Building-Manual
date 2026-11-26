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

```bash
find /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd -maxdepth 5 -printf '%y %M %u:%g %s bytes %TY-%Tm-%Td %TH:%TM:%TS %p\n'
```

It was created on November 18, 2026, everything is `root:root`, and it contains only `2027/Jan/test.json` (0 bytes). It was created when testing ACL inheritance in Part 6 of Volume 1. Look for any remaining script that created it.

```bash
grep -R -n -F --exclude='*.pyc' --exclude='*.log' '.acl-inheritance-test' /root /usr/local /etc 2>/dev/null | head -n 40
```

There were none. Look at the ACL.

```bash
getfacl -p /var/ossec/logs/alerts /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd/2027 /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd/2027/Jan /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd/2027/Jan/test.json
```

Only the top-level directory was in the following state (key points).

```text
user:wazuh-collector:r-x
mask::---
effective:---
```

There is an ACL entry, but the mask is `---`, so it cannot actually be entered.

# Chapter 2: Fixing the Search

## 2.1 The Current Code

```bash
sed -n '300,365p' /usr/local/lib/wazuh-collector/collector.py
```

In the following part, `find_inode_file()` included every directory, hidden ones too, in what it searched.

```text
if entry.is_dir(follow_symlinks=False):
    pending.append(Path(entry.path))
    continue
```

Check what is directly under `alerts` and the shape of the real locations.

```bash
find /var/ossec/logs/alerts -mindepth 1 -maxdepth 1 -type d -printf '%f\n'
```

```bash
find /var/ossec/logs/alerts/2026 -type d -printf '%P\n' | head -50
```

There were two directories directly under it, `2026` and `.acl-inheritance-test.bkv8vd`, and the real location was `2026/Nov`. Even with hidden directories excluded, the real files can be found.

```bash
stat -c '%A %U:%G %s bytes %y %n' /usr/local/lib/wazuh-collector/collector.py && python3 -m py_compile /usr/local/lib/wazuh-collector/collector.py
```

```bash
sed -n '365,455p' /usr/local/lib/wazuh-collector/collector.py
```

`open_initial_file()` stops startup if the previous file is not found. This safety measure is not changed. What changes is the following form.

```text
if entry.is_dir(follow_symlinks=False):
    if entry.name.startswith("."):
        continue
    pending.append(Path(entry.path))
    continue
```

## 2.2 Backup

Without touching the running Collector, back up the file.

```bash
cp -a /usr/local/lib/wazuh-collector/collector.py /usr/local/lib/wazuh-collector/collector.py.pre-hidden-dir-fix-20261121 && sha256sum /usr/local/lib/wazuh-collector/collector.py /usr/local/lib/wazuh-collector/collector.py.pre-hidden-dir-fix-20261121
```

Confirm that the two SHA-256 values are the same.

## 2.3 The Fix

Rewrite only if there is exactly one place to fix.

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/usr/local/lib/wazuh-collector/collector.py")
source = path.read_text()

old = '''                if entry.is_dir(follow_symlinks=False):
                    pending.append(Path(entry.path))
                    continue
'''

new = '''                if entry.is_dir(follow_symlinks=False):
                    if entry.name.startswith("."):
                        continue
                    pending.append(Path(entry.path))
                    continue
'''

count = source.count(old)
if count != 1:
    raise SystemExit(f"安全確認失敗: 対象コードが {count} 件。変更していません")

path.write_text(source.replace(old, new, 1))
print("修正完了: 隠しディレクトリを探索対象から除外")
PY
```

```bash
python3 -m py_compile /usr/local/lib/wazuh-collector/collector.py && diff -u /usr/local/lib/wazuh-collector/collector.py.pre-hidden-dir-fix-20261121 /usr/local/lib/wazuh-collector/collector.py
```

The difference was only two lines: `if entry.name.startswith("."):` and `continue`.

## 2.4 Testing as the Collector's User

Extract only `find_inode_file()` and, as the Collector's user, have it search for an inode that does not exist. It has succeeded if it returns `None` (not found) and finishes normally even though it cannot enter the hidden directory. No DB connection is made.

```bash
runuser -u wazuh-collector -- python3 - <<'PY'
import ast
import os
from pathlib import Path

source_path = "/usr/local/lib/wazuh-collector/collector.py"
source = Path(source_path).read_text()
tree = ast.parse(source)

function = next(
    node for node in tree.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "find_inode_file"
)

namespace = {
    "os": os,
    "Path": Path,
    "ALERT_DIR": Path("/var/ossec/logs/alerts"),
}

exec(compile(ast.Module(body=[function], type_ignores=[]), source_path, "exec"), namespace)

result = namespace["find_inode_file"](9223372036854775807)

print("RESULT:", result)
print("TEST: PASS" if result is None else "TEST: UNEXPECTED MATCH")
PY
```

The result was `TEST: PASS`.

# Chapter 3: Applying the Fix

## 3.1 Restarting

```bash
systemctl show wazuh-collector.service -p MainPID -p NRestarts -p ActiveState -p SubState
```

The current process (PID 13542) is running the code from before the fix. Restart it to load the new code. Collection stops briefly during the restart, but it continues from the position in the state file.

```bash
systemctl restart wazuh-collector.service
```

```bash
systemctl show wazuh-collector.service -p MainPID -p NRestarts -p ActiveState -p SubState
```

At build time it was PID 14203, `NRestarts=0`, `active` and `running`.

```bash
journalctl -u wazuh-collector.service -n 30 --no-pager
```

```bash
journalctl -u wazuh-collector.service --since "2026-11-21 11:09:00" --no-pager
```

`Resuming current alert file` was present, and no `PermissionError` for the hidden directory appeared.

## 3.2 There Is No PostgreSQL Connection Log

```bash
systemctl status wazuh-collector.service --no-pager -l
```

```bash
sed -n '500,570p' /usr/local/lib/wazuh-collector/collector.py
```

The Collector connects to PostgreSQL **only when an unread line arrives**. If it has read to the end and no new alerts have arrived, no connection log appears.

```bash
python3 - <<'PY'
import json, os
state_path = "/var/lib/wazuh-collector/state.json"
alert_path = "/var/ossec/logs/alerts/alerts.json"

with open(state_path) as f:
    state = json.load(f)

st = os.stat(alert_path)

print("STATE_INODE:", state["inode"])
print("STATE_OFFSET:", state["offset"])
print("CURRENT_INODE:", st.st_ino)
print("CURRENT_SIZE:", st.st_size)
print("INODE_MATCH:", state["inode"] == st.st_ino)
print("OFFSET_AT_EOF:", state["offset"] == st.st_size)
print("UNPROCESSED_BYTES:", max(0, st.st_size - state["offset"]) if state["inode"] == st.st_ino else "inode mismatch")
PY
```

```bash
stat -c 'ALERT_FILE_SIZE=%s MODIFIED=%y INODE=%i' /var/ossec/logs/alerts/alerts.json && journalctl -u wazuh-collector.service --since "2026-11-21 11:09:11 UTC" --no-pager
```

Nothing was unread, and `alerts.json` had not been updated since before the restart.

## 3.3 Checking the Connection

As the Collector's user, using the same connection settings as the Collector (`DB_CONFIG`), run only `SELECT 1`. Connection information is not shown.

```bash
runuser -u wazuh-collector -- python3 - <<'PY'
import importlib.util
from pathlib import Path

path = Path("/usr/local/lib/wazuh-collector/collector.py")
spec = importlib.util.spec_from_file_location("collector_check", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

try:
    with module.psycopg.connect(**module.DB_CONFIG) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()[0]
    print("POSTGRESQL_READ_ONLY_TEST:", "PASS" if result == 1 else "FAIL")
except Exception as error:
    print("POSTGRESQL_READ_ONLY_TEST: FAIL")
    print("ERROR_TYPE:", type(error).__name__)
PY
```

The result was `POSTGRESQL_READ_ONLY_TEST: PASS`. After a while, look at the log once new alerts have arrived.

```bash
journalctl -u wazuh-collector.service --since "2026-11-21 11:09:11 UTC" --no-pager | grep -E 'ERROR|WARNING|PostgreSQL connection established|Alert processing failed|Duplicate alert skipped'
```

```text
Nov 21 11:12:08
INFO PostgreSQL connection established
```

> **Run on: postgresql** (OS user `postgres`. You are already logged in as `postgres`, so `sudo` is not used)

```bash
psql -d security_workbench -c "SELECT COUNT(*) AS recent_events, COUNT(DISTINCT event_id) AS distinct_events, MAX(ingested_at) AS latest_ingested_at FROM incident.alert_events WHERE ingested_at >= TIMESTAMPTZ '2026-11-21 11:09:11+00';"
```

Three events (three distinct `event_id`s) had been saved after the restart.

# Chapter 4: Checking the Rotation Processing

> **Run on: VM 220**

```bash
sed -n '550,735p' /usr/local/lib/wazuh-collector/collector.py
```

| Situation | What the Collector does |
|---|---|
| An ordinary line | Saves it to PostgreSQL, then saves the position |
| Cannot reach PostgreSQL / save fails | Goes back to the start of the line and retries |
| The end of the file is a partial line | Waits for the switch |
| The file switches while a line is partial | Discards that line and switches to the new inode |
| The file switches after reading to the end | Switches to the new inode |
| Saving the position fails | Retries without switching to the new file |

```bash
grep -n -A75 -B10 '^def save_state\|^def load_state\|^def read_alert_line' /usr/local/lib/wazuh-collector/collector.py
```

`save_state()` writes to a temporary file in the same directory with `0600`, calls `flush()` and `fsync()`, swaps it in with `os.replace()`, and also calls `fsync()` on the directory. The order of processing is as follows.

```text
PostgreSQL INSERT
       ↓
トランザクション確定
       ↓
save_state(inode, offset)
```

```bash
grep -n -A45 -B15 'INSERT_SQL\|event_id' /usr/local/lib/wazuh-collector/collector.py | head -120
```

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

Next, we check how Wazuh switches its logs (rotation). This continues in Part 31 of Volume 3.

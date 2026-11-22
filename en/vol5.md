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

```bash
cp -a \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-cleanup-fix-20261118
```

```bash
grep -n -A35 -B10 'finally:' \
  /tmp/wazuh-collector-hardening-test.py
```

```bash
sed -n '435,485p' \
  /tmp/wazuh-collector-hardening-test.py
```

`handle` is opened before the `try`, and `connection` is initialized to `None`, so both can be referenced in `finally`. Confirm that there is exactly one place to fix.

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

old = """    finally:
        handle.close()

        if connection is not None:
            connection.close()
"""

print("TARGET_COUNT:", source.count(old))
PY
```

If `TARGET_COUNT: 1` is shown, go on.

## 1.2 Fixing the Shutdown Handling

Wrap closing the file and closing the DB connection in separate `try` blocks. Only the exception type is logged, with no sensitive information.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

old = """    finally:
        handle.close()

        if connection is not None:
            connection.close()
"""

new = """    finally:
        try:
            handle.close()
        except Exception as error:
            logging.error(
                "Alert file close failed: %s",
                type(error).__name__,
            )

        if connection is not None:
            try:
                connection.close()
            except Exception as error:
                logging.error(
                    "PostgreSQL connection close failed: %s",
                    type(error).__name__,
                )
"""

if source.count(old) != 1:
    raise SystemExit("ABORT: target count is not 1")

path.write_text(source.replace(old, new), encoding="utf-8")
print("TEST COPY CLEANUP UPDATED: PASS")
PY
```

```bash
python3 -m py_compile \
  /tmp/wazuh-collector-hardening-test.py \
  && echo "PY_COMPILE: PASS"
```

## 1.3 Checking the Shutdown Handling

Extract the `finally` part from the syntax tree and confirm that both closes are protected.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")
tree = ast.parse(source)

run_func = next(
    node for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "run"
)

finally_node = next(
    node for node in ast.walk(run_func)
    if isinstance(node, ast.Try) and node.finalbody
)

finally_source = ast.get_source_segment(source, finally_node)

assert finally_source is not None
assert "handle.close()" in finally_source
assert "connection.close()" in finally_source
assert "Alert file close failed" in finally_source
assert "PostgreSQL connection close failed" in finally_source

print("HANDLE CLOSE PROTECTED: PASS")
print("CONNECTION CLOSE PROTECTED: PASS")
print("BOTH CLEANUP PATHS PRESENT: PASS")
PY
```

With fake objects, confirm the order: even if closing the file fails, closing the DB connection is still executed.

```bash
python3 - <<'PY'
import logging

logging.disable(logging.CRITICAL)

events = []

class FakeHandle:
    def close(self):
        events.append("handle.close")
        raise OSError("simulated")

class FakeConnection:
    def close(self):
        events.append("connection.close")

handle = FakeHandle()
connection = FakeConnection()

try:
    try:
        handle.close()
    except Exception as error:
        events.append(f"handle.error:{type(error).__name__}")

    if connection is not None:
        try:
            connection.close()
        except Exception as error:
            events.append(f"connection.error:{type(error).__name__}")

    assert events == [
        "handle.close",
        "handle.error:OSError",
        "connection.close",
    ]

    print("HANDLE CLOSE FAILURE: PASS")
    print("CONNECTION CLOSE STILL EXECUTED: PASS")
finally:
    logging.disable(logging.NOTSET)
PY
```

> Pasting long code into the terminal can break it partway and cause a `SyntaxError`. In that case neither the file nor production is affected; paste it again.

## 1.4 Checking the Difference from Production

**Run on: security-core VM 220 (root)**

```bash
echo "=== PRODUCTION SHA256 ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== TEST SHA256 ==="
sha256sum /tmp/wazuh-collector-hardening-test.py

echo
echo "=== DIFF SUMMARY ==="
diff -u \
  /usr/local/lib/wazuh-collector/collector.py \
  /tmp/wazuh-collector-hardening-test.py \
  | diffstat 2>/dev/null || true

echo
echo "=== PRODUCTION SERVICE ==="
systemctl is-active wazuh-collector.service
systemctl show wazuh-collector.service -p NRestarts
```

If `diffstat` is not installed, the summary is not shown, but that is not a problem. Check the first and second halves of the diff.

```bash
diff -u \
  /usr/local/lib/wazuh-collector/collector.py \
  /tmp/wazuh-collector-hardening-test.py \
  | grep -E '^(---|\+\+\+|@@|[+-][^+-])' \
  | head -120
```

```bash
diff -u \
  /usr/local/lib/wazuh-collector/collector.py \
  /tmp/wazuh-collector-hardening-test.py \
  | tail -180
```

# Chapter 2: Protecting File Opening at Rotation

## 2.1 The Problem

The following two lines, used when rotation is detected, appear in two places: the incomplete-line case (Part 4, 5.3) and the EOF case (Part 4, 5.2).

```python
new_handle = ALERT_FILE.open("rb")
new_stat = os.fstat(new_handle.fileno())
```

Neither has exception handling, so the Collector exits if the new file cannot be opened. Also, if `fstat()` fails after opening, the file stays open. Combine this processing into one function and, on failure, retry while staying on the current file.

**Run on: security-core VM 220 (root)**

```bash
grep -n -B8 -A28 \
  'new_handle = ALERT_FILE.open' \
  /tmp/wazuh-collector-hardening-test.py
```

Confirm that the name of the function to be added is not yet in use. If nothing is shown, there is no problem.

```bash
grep -n '^def safe_open_current_alert_file' \
  /tmp/wazuh-collector-hardening-test.py || true
```

Back up before the fix.

```bash
cp -a \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-rotation-open-fix-20261118

sha256sum \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-rotation-open-fix-20261118
```

## 2.2 Adding a Function That Opens the File Safely

Add it after `open_initial_file()` and before `read_alert_line()`. If `open()` or `fstat()` fails, it logs only the exception type, closes the opened file and returns `(None, None)`.

**Run on: security-core VM 220 (root)**

```bash
sed -n '350,430p' \
  /tmp/wazuh-collector-hardening-test.py
```

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

marker = "\ndef read_alert_line(handle, discarding=False):\n"

addition = '''

def safe_open_current_alert_file():
    handle = None

    try:
        handle = ALERT_FILE.open("rb")
        actual_stat = os.fstat(handle.fileno())
        return handle, actual_stat

    except OSError as error:
        if handle is not None:
            try:
                handle.close()
            except OSError as close_error:
                logging.error(
                    "Failed to close alert file after open error: %s",
                    type(close_error).__name__,
                )

        logging.error(
            "Failed to open current alert file: %s",
            type(error).__name__,
        )
        return None, None

'''

if source.count(marker) != 1:
    raise SystemExit("ABORT: insertion marker count is not 1")

if "def safe_open_current_alert_file(" in source:
    raise SystemExit("ABORT: function already exists")

path.write_text(
    source.replace(marker, addition + marker),
    encoding="utf-8",
)

print("SAFE OPEN FUNCTION ADDED: PASS")
PY
```

Check the added function.

```bash
grep -n -A35 -B3 \
  '^def safe_open_current_alert_file' \
  /tmp/wazuh-collector-hardening-test.py
```

> In the original build, this command showed `ABORT: function already exists`, but the following check showed that the function had been added correctly (lines 384–406). Only the safety check against adding it twice was triggered, so there is no problem as long as `grep` shows exactly one function.

```bash
python3 -m py_compile \
  /tmp/wazuh-collector-hardening-test.py \
  && echo "PY_COMPILE: PASS"
```

## 2.3 Replacing the Call for Incomplete Lines

Adding the function alone leaves the callers unchanged. First check the surroundings of the two places.

**Run on: security-core VM 220 (root)**

```bash
sed -n '495,555p' \
  /tmp/wazuh-collector-hardening-test.py

echo
echo "=== EOF ROTATION ==="

sed -n '580,635p' \
  /tmp/wazuh-collector-hardening-test.py
```

Changing both places at once would make problems harder to isolate, so fix them one at a time. In the first place (incomplete line), if opening fails, rewind the read position with `handle.seek(line_start)` and check again on the next wait without losing the incomplete line.

```bash
sed -n '525,575p' \
  /tmp/wazuh-collector-hardening-test.py
```

```bash
python3 - <<'PY'
from pathlib import Path

p = Path("/tmp/wazuh-collector-hardening-test.py")
s = p.read_text()

old = '''                    new_handle = ALERT_FILE.open("rb")
                    new_stat = os.fstat(new_handle.fileno())

                    if new_stat.st_ino == active_inode:
                        new_handle.close()
                        handle.seek(line_start)
                        time.sleep(POLL_INTERVAL)
                        continue

                    try:
                        save_state(new_stat.st_ino, 0)
                    except Exception as error:
                        new_handle.close()
                        handle.seek(line_start)
'''

new = '''                    new_handle, new_stat = safe_open_current_alert_file()

                    if new_handle is None:
                        handle.seek(line_start)
                        time.sleep(POLL_INTERVAL)
                        continue

                    if new_stat.st_ino == active_inode:
                        new_handle.close()
                        handle.seek(line_start)
                        time.sleep(POLL_INTERVAL)
                        continue

                    try:
                        save_state(new_stat.st_ino, 0)
                    except Exception as error:
                        new_handle.close()
                        handle.seek(line_start)
'''

if s.count(old) != 1:
    raise SystemExit("ABORT: target block count is not 1")

p.write_text(s.replace(old, new))
print("INCOMPLETE ROTATION OPEN FIX: PASS")
PY
```

```bash
sed -n '535,575p' \
  /tmp/wazuh-collector-hardening-test.py
```

Confirm that if opening fails, it goes back to the start of the line and retries.

## 2.4 Replacing the Call at EOF

At EOF, unlike the incomplete-line case, there is no need to rewind the read position. If opening fails, keep the old file open and go on to the next wait.

**Run on: security-core VM 220 (root)**

```bash
sed -n '585,650p' \
  /tmp/wazuh-collector-hardening-test.py
```

```bash
python3 - <<'PY'
from pathlib import Path

p = Path("/tmp/wazuh-collector-hardening-test.py")
s = p.read_text()

old = '''                    new_handle = ALERT_FILE.open("rb")
                    new_stat = os.fstat(new_handle.fileno())

                    if new_stat.st_ino == active_inode:
                        new_handle.close()
                        time.sleep(POLL_INTERVAL)
                        continue

                    try:
                        save_state(new_stat.st_ino, 0)
'''

new = '''                    new_handle, new_stat = safe_open_current_alert_file()

                    if new_handle is None:
                        time.sleep(POLL_INTERVAL)
                        continue

                    if new_stat.st_ino == active_inode:
                        new_handle.close()
                        time.sleep(POLL_INTERVAL)
                        continue

                    try:
                        save_state(new_stat.st_ino, 0)
'''

if s.count(old) != 1:
    raise SystemExit("ABORT: target block count is not 1")

p.write_text(s.replace(old, new))
print("EOF ROTATION OPEN FIX: PASS")
PY
```

Check the replaced part.

```bash
sed -n '605,635p' /tmp/wazuh-collector-hardening-test.py
```

> In the original build, this command showed `ABORT: target block count is not 1`, but checking showed that the EOF side had already been replaced to use `safe_open_current_alert_file()`. On `ABORT` the file is not changed, so always check the actual content with this `sed`.

```bash
python3 -m py_compile \
  /tmp/wazuh-collector-hardening-test.py \
  && echo "PY_COMPILE: PASS"
```

## 2.5 Checking the Replacement

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import ast
from pathlib import Path

p = Path("/tmp/wazuh-collector-hardening-test.py")
source = p.read_text()
tree = ast.parse(source)

run = next(
    n for n in tree.body
    if isinstance(n, ast.FunctionDef) and n.name == "run"
)

calls = [
    n for n in ast.walk(run)
    if isinstance(n, ast.Call)
    and isinstance(n.func, ast.Name)
    and n.func.id == "safe_open_current_alert_file"
]

checks = {
    "two_rotation_calls": len(calls) == 2,
    "no_direct_rotation_open": (
        source.count('new_handle = ALERT_FILE.open("rb")') == 0
    ),
    "helper_defined_once": source.count(
        "def safe_open_current_alert_file():"
    ) == 1,
}

for name, passed in checks.items():
    print(f"{name}: {'PASS' if passed else 'FAIL'}")

if not all(checks.values()):
    raise SystemExit(1)
PY
```

| Check | Meaning |
|---|---|
| `two_rotation_calls` | `run()` calls the function from two places |
| `no_direct_rotation_open` | No old code calling `ALERT_FILE.open()` directly remains |
| `helper_defined_once` | The function is defined only once |

## 2.6 Unit Tests for the Function

`ALERT_FILE` is an instance of `Path`, so when mocking `open`, patch the `Path` class rather than the instance (instance attributes are read-only).

**Run on: security-core VM 220 (root)**

When the file cannot be opened:

```bash
python3 - <<'PY'
import importlib.util
from unittest.mock import patch
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-hardening-test.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with patch.object(
    Path,
    "open",
    side_effect=PermissionError("test"),
):
    handle, stat = module.safe_open_current_alert_file()

assert handle is None
assert stat is None

print("OPEN FAILURE HANDLING: PASS")
PY
```

When `fstat()` fails after opening:

```bash
python3 - <<'PY'
import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-hardening-test.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

fake_handle = MagicMock()
fake_handle.fileno.return_value = 99

with patch.object(Path, "open", return_value=fake_handle), \
     patch.object(module.os, "fstat", side_effect=OSError("test")):

    handle, stat = module.safe_open_current_alert_file()

assert handle is None
assert stat is None
fake_handle.close.assert_called_once()

print("FSTAT FAILURE HANDLING: PASS")
print("HANDLE CLOSED: PASS")
PY
```

When it opens normally (opens the production `alerts.json` read-only and closes it immediately):

```bash
python3 - <<'PY'
import importlib.util

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-hardening-test.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

handle, stat = module.safe_open_current_alert_file()

assert handle is not None
assert stat is not None
assert stat.st_ino > 0
assert not handle.closed

print("NORMAL OPEN: PASS")
print("INODE VALID: PASS")

handle.close()
assert handle.closed
print("HANDLE CLOSE: PASS")
PY
```

```bash
sed -n '530,575p' /tmp/wazuh-collector-hardening-test.py

echo
echo "=== EOF ROTATION ==="

sed -n '610,655p' /tmp/wazuh-collector-hardening-test.py
```

| Branch | When opening fails | On success |
|---|---|---|
| Incomplete line | Rewind with `handle.seek(line_start)` and retry | Switch only after the state is saved successfully |
| EOF | Keep the old file open and retry | Switch only after the state is saved successfully |

# Chapter 3: Exception Handling for stat()

## 3.1 The Problem

`ALERT_FILE.stat()`, used to detect rotation, catches only `FileNotFoundError`. If a `PermissionError` or a temporary I/O error occurs, the Collector exits. Fix it to catch all `OSError`s, log them and retry.

**Run on: security-core VM 220 (root)**

```bash
echo "=== PRODUCTION SHA256 ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== TEST SHA256 ==="
sha256sum /tmp/wazuh-collector-hardening-test.py

echo
echo "=== PRODUCTION SERVICE ==="
systemctl is-active wazuh-collector.service
systemctl show wazuh-collector.service -p NRestarts
```

```bash
grep -n -B 3 -A 8 'ALERT_FILE.stat()' \
  /tmp/wazuh-collector-hardening-test.py
```

Back up before the fix.

```bash
cp -a \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-stat-hardening-20261118 \
&& sha256sum \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-stat-hardening-20261118
```

## 3.2 Fixing the Exception Handling for stat()

In the incomplete-line case it goes back to the start of the line, and at EOF it stays on the old file; in both cases it logs the error type and retries.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
from pathlib import Path

p = Path("/tmp/wazuh-collector-hardening-test.py")
s = p.read_text()

old1 = '''                except FileNotFoundError:
                    handle.seek(line_start)
                    time.sleep(POLL_INTERVAL)
                    continue
'''

new1 = '''                except OSError as error:
                    handle.seek(line_start)
                    logging.error(
                        "Failed to stat alerts.json: %s",
                        type(error).__name__,
                    )
                    time.sleep(POLL_INTERVAL)
                    continue
'''

old2 = '''                except FileNotFoundError:
                    time.sleep(POLL_INTERVAL)
                    continue
'''

new2 = '''                except OSError as error:
                    logging.error(
                        "Failed to stat alerts.json: %s",
                        type(error).__name__,
                    )
                    time.sleep(POLL_INTERVAL)
                    continue
'''

if s.count(old1) != 1 or s.count(old2) != 1:
    raise SystemExit("ABORT: target block count mismatch")

s = s.replace(old1, new1, 1)
s = s.replace(old2, new2, 1)
p.write_text(s)

print("STAT ERROR HANDLING FIX: PASS")
PY
```

```bash
sed -n '527,550p' /tmp/wazuh-collector-hardening-test.py

echo
sed -n '610,632p' /tmp/wazuh-collector-hardening-test.py
```

```bash
python3 -m py_compile \
  /tmp/wazuh-collector-hardening-test.py \
  && echo "PY_COMPILE: PASS"
```

## 3.3 Checking the Fix

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import ast
from pathlib import Path

source = Path(
    "/tmp/wazuh-collector-hardening-test.py"
).read_text()

tree = ast.parse(source)
run = next(
    n for n in tree.body
    if isinstance(n, ast.FunctionDef) and n.name == "run"
)

checks = {
    "stat_calls": source.count("current_stat = ALERT_FILE.stat()") == 2,
    "oserror_handlers": source.count("except OSError as error:") >= 3,
    "stat_error_log": source.count(
        '"Failed to stat alerts.json: %s"'
    ) == 2,
}

for name, passed in checks.items():
    print(f"{name}: {'PASS' if passed else 'FAIL'}")

if not all(checks.values()):
    raise SystemExit(1)
PY
```

Now, whichever of `stat()`, `open()` or `fstat()` fails, the Collector retries instead of exiting.

```bash
sed -n '440,500p' /tmp/wazuh-collector-hardening-test.py

echo
echo "=== RUN END ==="

sed -n '650,690p' /tmp/wazuh-collector-hardening-test.py
```

# Chapter 4: Failure-Case Tests Using run()

Check that the fixes in Chapters 2 and 3 work as intended inside the actual `run()`. Files, file positions, state saving and waiting are all replaced with fake objects, so the production log, DB and state file are not touched. Replacing `time.sleep` with something that raises an exception stops the infinite loop safely.

**Run on: security-core VM 220 (root)**

```bash
sed -n '480,670p' /tmp/wazuh-collector-hardening-test.py
```

## 4.1 When stat() Fails

When `ALERT_FILE.stat()` raises `PermissionError`, confirm that the state is not saved, that an incomplete line goes back to its start, and that at EOF the position does not change.

```bash
python3 - <<'PY'
import importlib.util

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-hardening-test.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class StopTest(Exception):
    pass


class FakeHandle:
    def __init__(self, position):
        self.position = position
        self.seek_calls = []
        self.closed = False

    def tell(self):
        return self.position

    def seek(self, position):
        self.seek_calls.append(position)
        self.position = position

    def close(self):
        self.closed = True


class FakeAlertPath:
    def stat(self):
        raise PermissionError("simulated stat failure")


def test_branch(status, initial_position):
    handle = FakeHandle(initial_position)
    module.ALERT_FILE = FakeAlertPath()

    module.load_state = lambda: None
    module.open_initial_file = lambda state: (handle, 12345)
    module.read_alert_line = lambda *args, **kwargs: (
        status, None, False
    )
    module.save_state = lambda *args: (_ for _ in ()).throw(
        AssertionError("save_state must not be called")
    )

    def stop_sleep(_):
        raise StopTest()

    module.time.sleep = stop_sleep

    try:
        module.run()
    except StopTest:
        pass

    assert handle.closed
    assert handle.position == initial_position

    if status == "incomplete":
        assert handle.seek_calls == [initial_position]
    else:
        assert handle.seek_calls == []

    print(f"{status}: PASS")


test_branch("incomplete", 17)
test_branch("eof", 23)
PY
```

It has succeeded if the log `Failed to stat alerts.json: PermissionError` is followed by `incomplete: PASS` and `eof: PASS`. Also confirm that production is not affected.

```bash
echo "=== PRODUCTION COLLECTOR SHA256 ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== PRODUCTION SERVICE ==="
systemctl is-active wazuh-collector.service

echo
echo "=== RESTART COUNT ==="
systemctl show wazuh-collector.service -p NRestarts --value
```

## 4.2 Recovering from a stat() Failure

Confirm that when the first `stat()` fails and the second succeeds and detects an inode change (11111 → 22222), processing proceeds to rotation (incomplete-line case).

**Run on: security-core VM 220 (root)**

```bash
grep -n -A45 -B8 \
    'current_stat = ALERT_FILE.stat()' \
    /tmp/wazuh-collector-hardening-test.py
```

```bash
python3 - <<'PY'
import importlib.util

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-hardening-test.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class StopTest(Exception):
    pass


class FakeStat:
    def __init__(self, inode):
        self.st_ino = inode


class FakePath:
    def __init__(self):
        self.calls = 0

    def stat(self):
        self.calls += 1
        if self.calls == 1:
            raise PermissionError("temporary failure")
        return FakeStat(22222)


class FakeHandle:
    def __init__(self):
        self.position = 37
        self.seek_calls = []
        self.closed = False

    def tell(self):
        return self.position

    def seek(self, position):
        self.seek_calls.append(position)
        self.position = position

    def close(self):
        self.closed = True


path = FakePath()
old_handle = FakeHandle()
new_handle = FakeHandle()
saved_states = []
statuses = iter(["incomplete", "incomplete"])

module.ALERT_FILE = path
module.load_state = lambda: None
module.open_initial_file = lambda state: (old_handle, 11111)
module.read_alert_line = lambda *args, **kwargs: (
    next(statuses), None, False
)
module.safe_open_current_alert_file = lambda: (
    new_handle,
    FakeStat(22222),
)
module.save_state = lambda inode, offset: saved_states.append(
    (inode, offset)
)


def stop_sleep(_):
    if path.calls == 2:
        raise StopTest()


module.time.sleep = stop_sleep

try:
    module.run()
except StopTest:
    pass

checks = {
    "stat retry": path.calls == 2,
    "old offset restored": old_handle.seek_calls == [37],
    "old handle closed": old_handle.closed,
    "new handle closed": new_handle.closed,
    "new state saved": saved_states == [(22222, 0)],
}

for name, passed in checks.items():
    print(f"{name}: {'PASS' if passed else 'FAIL'}")

if not all(checks.values()):
    raise SystemExit(1)
PY
```

| Check | Meaning |
|---|---|
| `stat retry` | `stat()` was called twice (first failed, second succeeded) |
| `old offset restored` | On the first failure, the position in the old file was restored to 37 |
| `old handle closed` | The old file was closed at the switch |
| `new handle closed` | The new file was also closed during test cleanup |
| `new state saved` | The new inode (22222) and position 0 were saved |

```bash
python3 -m py_compile /tmp/wazuh-collector-hardening-test.py \
&& echo "PY_COMPILE: PASS"
```

## 4.3 When the New File Cannot Be Opened

Check the case where `stat()` detects an inode change but the new `alerts.json` cannot be opened. The expectation is that the old file stays open, the position is kept, and the state is not saved.

> `run()` always closes the file in `finally` when it ends. So whether the old file is still open is recorded and judged at the retry wait (`time.sleep`), not at the end of the test.

**Run on: security-core VM 220 (root)**

Incomplete-line case:

```bash
python3 - <<'PY'
import importlib.util

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-hardening-test.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class StopTest(Exception):
    pass


class FakeStat:
    st_ino = 22222


class FakePath:
    def stat(self):
        return FakeStat()


class FakeHandle:
    def __init__(self):
        self.position = 41
        self.seek_calls = []
        self.closed = False

    def tell(self):
        return self.position

    def seek(self, position):
        self.seek_calls.append(position)
        self.position = position

    def close(self):
        self.closed = True


path = FakePath()
old_handle = FakeHandle()
saved_states = []
open_calls = 0
retry_state = {}


def fake_open():
    global open_calls
    open_calls += 1
    return None, None


module.ALERT_FILE = path
module.load_state = lambda: None
module.open_initial_file = lambda state: (old_handle, 11111)
module.read_alert_line = lambda *args, **kwargs: (
    "incomplete", None, False
)
module.safe_open_current_alert_file = fake_open
module.save_state = lambda *args: saved_states.append(args)


def stop_sleep(_):
    retry_state["handle_open"] = not old_handle.closed
    retry_state["position"] = old_handle.position
    raise StopTest()


module.time.sleep = stop_sleep

try:
    module.run()
except StopTest:
    pass

checks = {
    "open attempted": open_calls == 1,
    "old handle open during retry": retry_state.get("handle_open") is True,
    "old offset restored during retry": retry_state.get("position") == 41,
    "state not modified": saved_states == [],
    "handle closed during final cleanup": old_handle.closed,
}

for name, passed in checks.items():
    print(f"{name}: {'PASS' if passed else 'FAIL'}")

if not all(checks.values()):
    raise SystemExit(1)
PY
```

EOF case:

```bash
python3 - <<'PY'
import importlib.util

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-hardening-test.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class StopTest(Exception):
    pass


class FakeStat:
    st_ino = 22222


class FakePath:
    def stat(self):
        return FakeStat()


class FakeHandle:
    def __init__(self):
        self.position = 41
        self.closed = False

    def tell(self):
        return self.position

    def close(self):
        self.closed = True


old_handle = FakeHandle()
saved_states = []
open_calls = 0
retry_state = {}


def fake_open():
    global open_calls
    open_calls += 1
    return None, None


module.ALERT_FILE = FakePath()
module.load_state = lambda: None
module.open_initial_file = lambda state: (old_handle, 11111)
module.read_alert_line = lambda *args, **kwargs: (
    "eof", None, False
)
module.safe_open_current_alert_file = fake_open
module.save_state = lambda *args: saved_states.append(args)


def stop_sleep(_):
    retry_state["handle_open"] = not old_handle.closed
    retry_state["position"] = old_handle.position
    raise StopTest()


module.time.sleep = stop_sleep

try:
    module.run()
except StopTest:
    pass

checks = {
    "open attempted": open_calls == 1,
    "old handle open during retry": retry_state.get("handle_open") is True,
    "old position preserved": retry_state.get("position") == 41,
    "state not modified": saved_states == [],
    "handle closed during final cleanup": old_handle.closed,
}

for name, passed in checks.items():
    print(f"{name}: {'PASS' if passed else 'FAIL'}")

if not all(checks.values()):
    raise SystemExit(1)
PY
```

If all five items are `PASS` in both cases, the Collector can safely retry on the old file even when the new file cannot be opened.

```bash
echo "=== TEST SCRIPT ==="
python3 -m py_compile /tmp/wazuh-collector-hardening-test.py \
  && echo "TEST PY_COMPILE: PASS"

echo
echo "=== PRODUCTION SCRIPT SHA256 ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== PRODUCTION SERVICE ==="
systemctl is-active wazuh-collector.service

echo
echo "=== PRODUCTION RESTART COUNT ==="
systemctl show wazuh-collector.service -p NRestarts --value
```

# Chapter 5: Unicode Format Characters and Timestamp Length

## 5.1 The Overall Structure of the Test Version

Before deploying to production, review the test version as a whole. First list the functions and constants.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")
tree = ast.parse(source)

print("=== FUNCTIONS ===")
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        print(
            f"{node.lineno:4}-{node.end_lineno:4} "
            f"{node.name}"
        )

print()
print("=== GLOBAL CONSTANTS ===")
for node in tree.body:
    if isinstance(node, ast.Assign):
        names = [
            target.id
            for target in node.targets
            if isinstance(target, ast.Name)
        ]
        if names:
            print(f"{node.lineno:4} {', '.join(names)}")
PY
```

At build time there were 15 functions, divided into input validation, DB storage, state management, rotation and the main loop. Check the input validation part and the imports and constants.

```bash
sed -n '80,245p' /tmp/wazuh-collector-hardening-test.py
```

```bash
sed -n '1,80p' /tmp/wazuh-collector-hardening-test.py
```

## 5.2 Checking the Current Behavior

Check how validation of timestamps, strings and IP addresses handles borderline input.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

print("=== TIMESTAMP ===")
for value in (
    "2026-11-18T12:00:00+09:00",
    "2026-11-18T03:00:00Z",
    "invalid",
    "9" * 10000,
):
    try:
        result = module.parse_timestamp(value)
        print(f"accepted: length={len(value)}")
    except Exception as error:
        print(f"rejected: length={len(value)}, error={type(error).__name__}")

print()
print("=== TEXT ===")
for value in (
    "normal text",
    "line1\nline2",
    "日本語テスト",
    "zero\u200bwidth",
    "bidi\u202econtrol",
):
    result = module.safe_text(value)
    print(f"input={value!r} output={result!r}")

print()
print("=== IP ===")
for value in ("192.0.2.1", " 192.0.2.1 ", "2001:db8::1"):
    print(f"{value!r} -> {module.safe_ip(value)!r}")
PY
```

Results at build time:

```text
=== TEXT ===
input='normal text' output='normal text'
input='line1\nline2' output='line1line2'
input='日本語テスト' output='日本語テスト'
input='zero\u200bwidth' output='zero\u200bwidth'
input='bidi\u202econtrol' output='bidi\u202econtrol'

=== IP ===
'192.0.2.1' -> '192.0.2.1'
' 192.0.2.1 ' -> None
'2001:db8::1' -> '2001:db8::1'
```

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

```bash
cp -a /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-unicode-fix-20261118

sha256sum \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-unicode-fix-20261118
```

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

old = '''def safe_text(value, limit=4096):
    if not isinstance(value, str):
        return None

    value = "".join(
        char for char in value
        if char >= " " and not 0x7f <= ord(char) <= 0x9f
    )

    value = value.strip()

    if not value:
        return None

    return value[:limit]
'''

new = '''def safe_text(value, limit=4096):
    if not isinstance(value, str):
        return None

    value = "".join(
        char for char in value
        if (
            char >= " "
            and not 0x7f <= ord(char) <= 0x9f
            and __import__("unicodedata").category(char) != "Cf"
        )
    )

    value = value.strip()

    if not value:
        return None

    return value[:limit]
'''

if source.count(old) != 1:
    raise SystemExit("ERROR: safe_text target not unique; no changes made")

path.write_text(source.replace(old, new), encoding="utf-8")
print("safe_text updated in test copy only")
PY
```

```bash
sed -n '1,18p' /tmp/wazuh-collector-hardening-test.py
sed -n '125,155p' /tmp/wazuh-collector-hardening-test.py
python3 -m py_compile /tmp/wazuh-collector-hardening-test.py
```

`__import__("unicodedata")` also works, but for readability and maintenance, tidy it into a normal `import`.

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

old_import = "import ipaddress\n"
new_import = "import ipaddress\nimport unicodedata\n"

old_call = '__import__("unicodedata").category(char)'
new_call = 'unicodedata.category(char)'

if source.count(old_import) != 1:
    raise SystemExit("ERROR: import target not unique")

if source.count(old_call) != 1:
    raise SystemExit("ERROR: Unicode call target not unique")

source = source.replace(old_import, new_import, 1)
source = source.replace(old_call, new_call, 1)

path.write_text(source, encoding="utf-8")
print("unicodedata import normalized")
PY
```

## 5.4 Limiting the Timestamp Length

Limit timestamp strings to 64 characters, and also reject empty strings.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

old = '''def parse_timestamp(value):
    if not isinstance(value, str):
        raise ValueError("invalid timestamp")

    result = datetime.fromisoformat(
'''

new = '''def parse_timestamp(value):
    if not isinstance(value, str) or not value or len(value) > 64:
        raise ValueError("invalid timestamp")

    result = datetime.fromisoformat(
'''

if source.count(old) != 1:
    raise SystemExit("ERROR: timestamp target not unique; no changes made")

path.write_text(source.replace(old, new, 1), encoding="utf-8")
print("Timestamp length limit added: 64 characters")
PY
```

## 5.5 Regression Tests

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util

path = "/tmp/wazuh-collector-hardening-test.py"
spec = importlib.util.spec_from_file_location("collector_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

print("=== TIMESTAMP TEST ===")
timestamp_cases = [
    ("valid JST", "2026-11-18T12:00:00+09:00", True),
    ("valid UTC", "2026-11-18T03:00:00Z", True),
    ("empty", "", False),
    ("invalid", "invalid", False),
    ("over limit", "9" * 65, False),
]

for name, value, expected in timestamp_cases:
    try:
        module.parse_timestamp(value)
        actual = True
    except (ValueError, TypeError):
        actual = False

    print(f"{name}: {'PASS' if actual == expected else 'FAIL'}")

print()
print("=== SAFE TEXT TEST ===")
text_cases = [
    ("Japanese", "日本語テスト", "日本語テスト"),
    ("newline", "line1\nline2", "line1line2"),
    ("zero width", "zero\u200bwidth", "zerowidth"),
    ("bidi control", "bidi\u202econtrol", "bidicontrol"),
    ("emoji", "安全🔐テスト", "安全🔐テスト"),
]

for name, value, expected in text_cases:
    actual = module.safe_text(value)
    print(f"{name}: {'PASS' if actual == expected else 'FAIL'}")
    if actual != expected:
        print(f"  expected={expected!r}")
        print(f"  actual  ={actual!r}")
PY
```

| Category | What was checked |
|---|---|
| Timestamps | JST and UTC accepted; empty, invalid and 65+ characters rejected |
| Strings | Japanese text and emoji kept; newlines, zero-width spaces and bidirectional control characters removed |

It is done when all 10 items are `PASS`.

# Chapter 6: Comprehensive Tests of Huge Lines and Rotation

## 6.1 Measuring the Skip Positions

Measure at which positions a line over 1 MiB is skipped. The first read reads the limit (1 MiB + 1 byte) followed by an extra 64 KiB, so less remains than you might expect.

**Run on: security-core VM 220 (root)**

```bash
nl -ba /tmp/wazuh-collector-hardening-test.py | sed -n '390,490p'
```

```bash
python3 - <<'PY'
import importlib.util
import io

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-hardening-test.py",
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

payload = b"A" * (
    m.MAX_ALERT_LINE_BYTES + m.READ_CHUNK_BYTES * 3
) + b"\n"

h = io.BytesIO(payload)

for i in range(6):
    status, _, discarding = m.read_alert_line(
        h,
        discarding=(i > 0),
    )
    print(
        f"step={i + 1}",
        f"status={status}",
        f"discarding={discarding}",
        f"position={h.tell()}",
        f"remaining={len(payload) - h.tell()}",
    )
    if status in ("oversized", "eof"):
        break
PY
```

| Stage | State | Read position | Remaining |
|---|---|---:|---:|
| 1 | `discarding` | 1,114,113 | 131,072 |
| 2 | `discarding` | 1,179,649 | 65,536 |
| 3 | `oversized` | 1,245,185 | 0 |

It discards 64 KiB at a time and finishes with `oversized` when it reaches the newline.

## 6.2 Preparing the Test Environment

Run the whole of `run()` on a simulated log in a temporary directory. State saving and the DB connection are mocked, and the production state file (`/var/lib/wazuh-collector/state.json`) and DB are not touched.

**Run on: security-core VM 220 (root)**

```bash
grep -n -A65 '^def save_state' /tmp/wazuh-collector-hardening-test.py
```

```bash
sed -n '1,65p' /tmp/wazuh-collector-hardening-test.py
```

Confirm that a rotation in the temporary directory (renaming and creating a new file) changes the inode.

```bash
python3 - <<'PY'
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory(prefix="wazuh-rotation-test-") as tmp:
    root = Path(tmp)
    alert_dir = root / "alerts"
    alert_dir.mkdir()

    active = alert_dir / "alerts.json"
    rotated = alert_dir / "alerts.json.1"

    active.write_bytes(b"A" * 1024)
    active.rename(rotated)
    active.write_bytes(b'{"test":"new"}\n')

    assert rotated.exists()
    assert active.exists()
    assert rotated.stat().st_ino != active.stat().st_ino

    print("PASS: temporary log rotation")
    print("PASS: old inode =", rotated.stat().st_ino)
    print("PASS: new inode =", active.stat().st_ino)
    print("PASS: no production files accessed")
PY
```

```bash
grep -nE '^(def run|def save_state|def open_initial_file|def safe_open_current_alert_file|def read_alert_line|def process_line)' /tmp/wazuh-collector-hardening-test.py
```

## 6.3 Rotation While Skipping

Put an incomplete line over 1 MiB in the old log, and rotate the log after `run()` starts skipping (at the first wait). Confirm that the new inode and position 0 are saved. If a DB connection is made, the test fails.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch
import os

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-hardening-test.py",
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

saved_states = []
sleep_count = 0
rotation_info = {}

class StopTest(Exception):
    pass

def fake_save_state(inode, offset):
    saved_states.append((inode, offset))

def forbidden_connect(*args, **kwargs):
    raise AssertionError("DB connection must not occur")

with tempfile.TemporaryDirectory(prefix="wazuh-rotation-run-") as tmp:
    root = Path(tmp)
    alert_dir = root / "alerts"
    alert_dir.mkdir()

    alert_file = alert_dir / "alerts.json"
    rotated_file = alert_dir / "alerts.json.1"

    # Huge incomplete line, long enough to hit EOF after the first read.
    alert_file.write_bytes(
        b"A" * (m.MAX_ALERT_LINE_BYTES + 1 + m.READ_CHUNK_BYTES)
    )

    def fake_open_initial_file(state):
        handle = alert_file.open("rb")
        inode = os.fstat(handle.fileno()).st_ino
        return handle, inode

    def fake_sleep(seconds):
        global sleep_count
        sleep_count += 1

        if sleep_count == 1:
            old_inode = alert_file.stat().st_ino
            alert_file.rename(rotated_file)
            alert_file.write_bytes(b"")
            rotation_info["old_inode"] = old_inode
            rotation_info["new_inode"] = alert_file.stat().st_ino
            print("TEST: log rotated during oversized-line discard")

        elif sleep_count == 2:
            raise StopTest()

    with (
        patch.object(m, "ALERT_FILE", alert_file),
        patch.object(m, "ALERT_DIR", alert_dir),
        patch.object(m, "STATE_FILE", root / "state.json"),
        patch.object(m, "load_state", lambda: None),
        patch.object(m, "open_initial_file", fake_open_initial_file),
        patch.object(m, "save_state", fake_save_state),
        patch.object(m.psycopg, "connect", forbidden_connect),
        patch.object(m.time, "sleep", fake_sleep),
    ):
        try:
            m.run()
        except StopTest:
            pass

    assert rotation_info["old_inode"] != rotation_info["new_inode"]
    assert saved_states == [(rotation_info["new_inode"], 0)]
    assert not (root / "state.json").exists()

    print("PASS: oversized line entered discard mode")
    print("PASS: rotation detected during discard")
    print("PASS: new inode saved with offset 0")
    print("PASS: production DB was not accessed")
    print("PASS: production state file was not modified")
    print("ALL ROTATION TESTS PASSED")
PY
```

The following three lines are written to the log.

```text
Oversized alert line detected; discarding
Incomplete oversized line discarded at rotation
Switched to new alerts.json inode
```

## 6.4 When Saving the State Fails at Rotation

Deliberately make saving the new inode fail, and confirm that the old file is kept open and the Collector does not switch to the new file. Whether the old file is open is recorded at the second wait (retry).

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch
import os

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-hardening-test.py",
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

saved_attempts = []
rotation_info = {}
sleep_count = 0
old_handle_info = {}

class StopTest(Exception):
    pass

def fake_save_state(inode, offset):
    saved_attempts.append((inode, offset))
    if rotation_info and inode == rotation_info["new_inode"]:
        raise OSError("simulated state-save failure")

def forbidden_connect(*args, **kwargs):
    raise AssertionError("DB connection must not occur")

with tempfile.TemporaryDirectory(prefix="wazuh-rotation-fail-") as tmp:
    root = Path(tmp)
    alert_dir = root / "alerts"
    alert_dir.mkdir()

    alert_file = alert_dir / "alerts.json"
    rotated_file = alert_dir / "alerts.json.1"

    alert_file.write_bytes(
        b"A" * (m.MAX_ALERT_LINE_BYTES + 1 + m.READ_CHUNK_BYTES)
    )

    def fake_open_initial_file(state):
        handle = alert_file.open("rb")
        old_handle_info["handle"] = handle
        old_handle_info["inode"] = os.fstat(handle.fileno()).st_ino
        return handle, old_handle_info["inode"]

    def fake_sleep(seconds):
        global sleep_count
        sleep_count += 1

        if sleep_count == 1:
            alert_file.rename(rotated_file)
            alert_file.write_bytes(b"")
            rotation_info["new_inode"] = alert_file.stat().st_ino
            rotation_info["old_inode"] = rotated_file.stat().st_ino
            print("TEST: rotation completed")

        elif sleep_count == 2:
            old_handle_info["open_during_retry"] = (
                not old_handle_info["handle"].closed
            )
            old_handle_info["position_during_retry"] = (
                old_handle_info["handle"].tell()
            )
            raise StopTest()

    with (
        patch.object(m, "ALERT_FILE", alert_file),
        patch.object(m, "ALERT_DIR", alert_dir),
        patch.object(m, "STATE_FILE", root / "state.json"),
        patch.object(m, "load_state", lambda: None),
        patch.object(m, "open_initial_file", fake_open_initial_file),
        patch.object(m, "save_state", fake_save_state),
        patch.object(m.psycopg, "connect", forbidden_connect),
        patch.object(m.time, "sleep", fake_sleep),
    ):
        try:
            m.run()
        except StopTest:
            pass

    assert rotation_info["old_inode"] != rotation_info["new_inode"]
    assert saved_attempts == [(rotation_info["new_inode"], 0)]
    assert old_handle_info["open_during_retry"] is True
    assert old_handle_info["position_during_retry"] > 0
    assert old_handle_info["handle"].closed is True
    assert not (root / "state.json").exists()

    print("PASS: state-save failure detected")
    print("PASS: old file handle retained during retry")
    print("PASS: old file position preserved")
    print("PASS: old handle closed only during final cleanup")
    print("PASS: production DB untouched")
    print("PASS: production state untouched")
    print("ALL TESTS PASSED")
PY
```

If the log `ERROR State save failed during rotation: OSError` is followed by `ALL TESTS PASSED`, this confirms that while the state cannot be saved, the Collector waits on the old file and does not wrongly switch to the new one.

# Chapter 7: Comprehensive Tests of DB Failures and Reprocessing

## 7.1 Reconnecting When the DB Connection Is Lost

Deliberately make the first DB operation fail, and confirm that the connection is discarded and recreated and the same alert is processed again from its original position. The state should be saved only once, after processing succeeds.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch
import os

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-hardening-test.py",
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

saved_states = []
processed_lines = []
connections = []
sleep_count = 0
connection_attempts = 0

class StopTest(Exception):
    pass

class FakeConnection:
    def __init__(self, number):
        self.number = number
        self.closed = False
        self.close_count = 0

    def close(self):
        self.close_count += 1
        self.closed = True

def fake_connect(*args, **kwargs):
    global connection_attempts
    connection_attempts += 1
    connection = FakeConnection(connection_attempts)
    connections.append(connection)
    return connection

def fake_process_line(connection, line):
    processed_lines.append((connection.number, line))

    if len(processed_lines) == 1:
        raise OSError("simulated database connection failure")

def fake_save_state(inode, offset):
    saved_states.append((inode, offset))

def fake_sleep(seconds):
    global sleep_count
    sleep_count += 1

    if sleep_count == 2:
        raise StopTest()

with tempfile.TemporaryDirectory(prefix="wazuh-db-reconnect-") as tmp:
    root = Path(tmp)
    alert_dir = root / "alerts"
    alert_dir.mkdir()

    alert_file = alert_dir / "alerts.json"
    line = b'{"id":"retry-event","rule":{"id":"200003","level":7}}\n'
    alert_file.write_bytes(line)

    def fake_open_initial_file(state):
        handle = alert_file.open("rb")
        inode = os.fstat(handle.fileno()).st_ino
        return handle, inode

    with (
        patch.object(m, "ALERT_FILE", alert_file),
        patch.object(m, "ALERT_DIR", alert_dir),
        patch.object(m, "STATE_FILE", root / "state.json"),
        patch.object(m, "load_state", lambda: None),
        patch.object(m, "open_initial_file", fake_open_initial_file),
        patch.object(m, "save_state", fake_save_state),
        patch.object(m.psycopg, "connect", fake_connect),
        patch.object(m, "process_line", fake_process_line),
        patch.object(m.time, "sleep", fake_sleep),
    ):
        try:
            m.run()
        except StopTest:
            pass

    print("Connection attempts:", connection_attempts)
    print("Processed attempts:", len(processed_lines))
    print("Saved states:", saved_states)

    assert connection_attempts == 2
    assert len(processed_lines) == 2
    assert processed_lines[0][1] == line
    assert processed_lines[1][1] == line
    assert processed_lines[0][0] == 1
    assert processed_lines[1][0] == 2
    assert connections[0].closed is True
    assert connections[0].close_count >= 1
    assert connections[1].closed is True
    assert saved_states == [
        (os.stat(alert_file).st_ino, len(line))
    ]
    assert not (root / "state.json").exists()

    print("PASS: first DB processing attempt failed")
    print("PASS: failed connection was closed")
    print("PASS: new DB connection established")
    print("PASS: same event retried from original position")
    print("PASS: state saved only after successful processing")
    print("PASS: all test connections closed")
    print("PASS: production state file untouched")
    print("ALL TESTS PASSED")
PY
```

> The test connection object needs the `closed` attribute that the production code refers to. Without it you get an `AttributeError`.

## 7.2 Reprocessing After a Failed State Save and Preventing Duplicates

When the DB insert succeeds but saving the state fails, confirm with the actual `run()` that the same alert is reprocessed, the second insert is rejected by the unique constraint, and only one row is inserted (this repeats the check of Part 4, 8.6 across the whole loop).

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch
import os
import json

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-hardening-test.py",
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

inserted_ids = set()
insert_attempts = []
successful_inserts = []
duplicate_count = 0
save_attempts = []
sleep_count = 0
connections = []

class StopTest(Exception):
    pass

class FakeTransaction:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

class FakeConnection:
    def __init__(self):
        self.closed = False

    def transaction(self):
        return FakeTransaction()

    def execute(self, sql, event):
        global duplicate_count
        event_id = event["event_id"]
        insert_attempts.append(event_id)

        if event_id in inserted_ids:
            duplicate_count += 1
            raise m.psycopg.errors.UniqueViolation(
                "duplicate event"
            )

        inserted_ids.add(event_id)
        successful_inserts.append(event_id)

    def close(self):
        self.closed = True

def fake_connect(*args, **kwargs):
    connection = FakeConnection()
    connections.append(connection)
    return connection

def fake_save_state(inode, offset):
    save_attempts.append((inode, offset))
    if len(save_attempts) == 1:
        raise OSError("simulated state save failure")

def fake_sleep(seconds):
    global sleep_count
    sleep_count += 1
    if sleep_count == 2:
        raise StopTest()

with tempfile.TemporaryDirectory(prefix="wazuh-state-retry-") as tmp:
    root = Path(tmp)
    alert_dir = root / "alerts"
    alert_dir.mkdir()

    alert_file = alert_dir / "alerts.json"
    line = (
        b'{"id":"step315-run-event",'
        b'"timestamp":"2026-11-18T15:00:00+09:00",'
        b'"rule":{"id":"100001","level":5,"description":"test"},'
        b'"agent":{"id":"001","name":"test-agent"},'
        b'"manager":{"name":"test-manager"},'
        b'"decoder":{"name":"test-decoder"}}\n'
    )
    alert_file.write_bytes(line)
    inode = alert_file.stat().st_ino

    def fake_open_initial_file(state):
        handle = alert_file.open("rb")
        return handle, os.fstat(handle.fileno()).st_ino

    with (
        patch.object(m, "ALERT_FILE", alert_file),
        patch.object(m, "ALERT_DIR", alert_dir),
        patch.object(m, "STATE_FILE", root / "state.json"),
        patch.object(m, "load_state", lambda: None),
        patch.object(m, "open_initial_file", fake_open_initial_file),
        patch.object(m, "save_state", fake_save_state),
        patch.object(m.psycopg, "connect", fake_connect),
        patch.object(m.time, "sleep", fake_sleep),
    ):
        try:
            m.run()
        except StopTest:
            pass

    print("Insert attempts:", insert_attempts)
    print("Successful inserts:", successful_inserts)
    print("Duplicate count:", duplicate_count)
    print("State save attempts:", save_attempts)

    assert insert_attempts == [
        "step315-run-event",
        "step315-run-event",
    ]
    assert successful_inserts == ["step315-run-event"]
    assert duplicate_count == 1
    assert len(save_attempts) == 2
    assert save_attempts[0] == (inode, len(line))
    assert save_attempts[1] == (inode, len(line))
    assert not (root / "state.json").exists()
    assert all(c.closed for c in connections)

    print("PASS: DB insert succeeded once")
    print("PASS: failed state save caused event retry")
    print("PASS: duplicate was rejected")
    print("PASS: second state save succeeded")
    print("PASS: production state untouched")
    print("ALL TESTS PASSED")
PY
```

Results at build time:

```text
Insert attempts: ['step315-run-event', 'step315-run-event']
Successful inserts: ['step315-run-event']
Duplicate count: 1
State save attempts: [(5778632, 230), (5778632, 230)]
ALL TESTS PASSED
```

## 7.3 Confirming That Forbidden Elements Are Absent

Check the syntax, and confirm that `ON CONFLICT`, `SELECT`, `UPDATE`, `DELETE`, `full_log`, `password` and `command` do not appear in the code. If nothing is shown, there is no problem.

**Run on: security-core VM 220 (root)**

```bash
python3 -m py_compile /tmp/wazuh-collector-hardening-test.py &&
echo "PASS: Python syntax" &&
grep -nE 'ON CONFLICT|SELECT |UPDATE |DELETE |full_log|password|command' \
  /tmp/wazuh-collector-hardening-test.py || true
```

# Chapter 8: Deploying to Production and a Startup Problem

## 8.1 Final Check of the Difference from Production

**Run on: security-core VM 220 (root)**

```bash
diff -u \
  /usr/local/lib/wazuh-collector/collector.py \
  /tmp/wazuh-collector-hardening-test.py \
  | less
```

If it is hard to read in `less`, show it in separate ranges.

```bash
diff -u \
  /usr/local/lib/wazuh-collector/collector.py \
  /tmp/wazuh-collector-hardening-test.py \
  | sed -n '80,260p'
```

```bash
diff -u \
  /usr/local/lib/wazuh-collector/collector.py \
  /tmp/wazuh-collector-hardening-test.py \
  | sed -n '260,480p'
```

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

```bash
systemctl is-active wazuh-collector &&
systemctl show wazuh-collector \
  -p MainPID -p NRestarts -p ActiveEnterTimestamp &&
sha256sum /usr/local/lib/wazuh-collector/collector.py &&
stat -c '%U:%G %a %s %y' \
  /var/lib/wazuh-collector/state.json
```

Preserve the verified test version under another name inside `/tmp`.

```bash
cp -a \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.verified-20261119 &&
sha256sum \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.verified-20261119
```

```bash
stat -c '%n | %U:%G | %a | %s bytes' \
  /usr/local/lib/wazuh-collector/collector.py \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.verified-20261119
```

| File | Owner / permissions | Size (at build time) |
|---|---|---:|
| Production `collector.py` | `root:root 755` | 9,626 bytes |
| Test version | `root:root 600` | 18,510 bytes |

## 8.3 Placing the Candidate File and Backing Up Production

Place the test version as `collector.py.candidate` with the same owner and permissions as production, and check its syntax and hash.

**Run on: security-core VM 220 (root)**

```bash
install -o root -g root -m 755 \
  /tmp/wazuh-collector-hardening-test.py \
  /usr/local/lib/wazuh-collector/collector.py.candidate &&
python3 -m py_compile \
  /usr/local/lib/wazuh-collector/collector.py.candidate &&
stat -c '%n | %U:%G | %a | %s bytes' \
  /usr/local/lib/wazuh-collector/collector.py.candidate &&
sha256sum \
  /tmp/wazuh-collector-hardening-test.py \
  /usr/local/lib/wazuh-collector/collector.py.candidate
```

Back up the current production code.

```bash
cp -a \
  /usr/local/lib/wazuh-collector/collector.py \
  /usr/local/lib/wazuh-collector/collector.py.backup-20261119 &&
sha256sum \
  /usr/local/lib/wazuh-collector/collector.py \
  /usr/local/lib/wazuh-collector/collector.py.backup-20261119
```

```text
本番:
931ee3cb381be2dd059ad76669bf00e19f2da2c949cf264abb235061f88c95a8

バックアップ:
931ee3cb381be2dd059ad76669bf00e19f2da2c949cf264abb235061f88c95a8
```

## 8.4 Replacing the Production Code

Copy the candidate file once as `collector.py.new`, check that it matches with `cmp`, and then replace in one step with `mv` (so that no partially written file exists under the production name). The service is not restarted at this point, so the running process still uses the old code.

**Run on: security-core VM 220 (root)**

```bash
set -e

install -o root -g root -m 755 \
  /usr/local/lib/wazuh-collector/collector.py.candidate \
  /usr/local/lib/wazuh-collector/collector.py.new

cmp \
  /usr/local/lib/wazuh-collector/collector.py.candidate \
  /usr/local/lib/wazuh-collector/collector.py.new

mv -f \
  /usr/local/lib/wazuh-collector/collector.py.new \
  /usr/local/lib/wazuh-collector/collector.py

echo "=== FILE ==="
stat -c '%n | %U:%G | %a | %s bytes' \
  /usr/local/lib/wazuh-collector/collector.py

echo "=== SHA256 ==="
sha256sum \
  /usr/local/lib/wazuh-collector/collector.py \
  /usr/local/lib/wazuh-collector/collector.py.backup-20261119
```

> If you run `set -e` in an interactive shell, the shell itself exits as soon as a command fails. In that case, log in again and check the state.

The SHA-256 of the production `collector.py` becomes `d404f10a...` (18,510 bytes), the same as the test version.

## 8.5 Restarting, and the Startup Failure

**Run on: security-core VM 220 (root)**

```bash
systemctl restart wazuh-collector &&
sleep 2 &&
echo "=== SERVICE ===" &&
systemctl is-active wazuh-collector &&
systemctl show wazuh-collector \
  -p MainPID \
  -p NRestarts \
  -p ActiveEnterTimestamp &&
echo "=== JOURNAL ===" &&
journalctl -u wazuh-collector -n 30 --no-pager
```

In the original build, `activating` was shown here and it did not work correctly. Check the status and the log.

```bash
echo "=== SYSTEMD STATUS ==="
systemctl status wazuh-collector --no-pager -l

echo
echo "=== SERVICE PROPERTIES ==="
systemctl show wazuh-collector \
  -p ActiveState \
  -p SubState \
  -p Result \
  -p MainPID \
  -p NRestarts \
  -p ExecMainStatus

echo
echo "=== RECENT JOURNAL ==="
journalctl -u wazuh-collector -n 60 --no-pager -o short-iso
```

```bash
journalctl -u wazuh-collector \
  --since "2026-11-18 15:14:00" \
  --no-pager -o cat
```

Set the `--since` time to when you restarted. The log at build time was as follows (excerpt).

```text
  File "/usr/local/lib/wazuh-collector/collector.py", line 316, in find_inode_file
    for entry in os.scandir(ALERT_DIR):
                 ^^^^^^^^^^^^^^^^^^^^^
PermissionError: [Errno 13] Permission denied: '/var/ossec/logs/alerts'
```

**Cause:** At startup, the new code's `open_initial_file()` lists the contents of `/var/ossec/logs/alerts` with `os.scandir()` through `find_inode_file()`. However, the ACL from Part 3, Chapter 7 gives `wazuh-collector` only the traverse permission (`x`) on this directory, not the read permission (`r`) needed to list it. The assumption of the new code and the least-privilege design did not match.

> In the tests, `find_inode_file()` was mocked or the tests ran as root, so this problem was not found until it ran as the production user.

## 8.6 Stopping the Automatic Restarts

systemd keeps restarting it every 5 seconds, so stop only the Collector. The Wazuh Manager, Indexer and PostgreSQL are not affected.

**Run on: security-core VM 220 (root)**

```bash
systemctl stop wazuh-collector &&
systemctl is-active wazuh-collector
```

> If you run it as an ordinary user, systemd asks for administrator authentication. In that case enter that user's password (do not keep a record of the password).

If `inactive` is shown, it has stopped.

Rather than simply adding read permission on the directory, deal with it in the code while keeping least privilege. First check the permissions and the code.

```bash
sudo bash -c '
echo "=== ALERT DIRECTORY PERMISSIONS ==="
namei -l /var/ossec/logs/alerts
getfacl -p /var/ossec/logs/alerts
echo
echo "=== ALERT FILE PERMISSIONS ==="
stat -c "%n | %U:%G | %a | %s bytes" /var/ossec/logs/alerts/alerts.json
getfacl -p /var/ossec/logs/alerts/alerts.json
echo
echo "=== INODE SEARCH FUNCTION ==="
sed -n "290,375p" /usr/local/lib/wazuh-collector/collector.py
echo
echo "=== SYSTEMD ACCESS RULES ==="
systemctl cat wazuh-collector
'
```

```bash
echo "=== ALERT FILES (NAME / INODE / SIZE) ==="
find /var/ossec/logs/alerts \
  -maxdepth 1 -type f \
  -printf '%f | inode=%i | size=%s bytes\n' |
  sort

echo
echo "=== COLLECTOR STATE ==="
stat -c '%U:%G | %a | %s bytes' \
  /var/lib/wazuh-collector/state.json

python3 - <<'PY'
import json
from pathlib import Path

p = Path("/var/lib/wazuh-collector/state.json")
state = json.loads(p.read_text())
print("state inode:", state.get("inode"))
print("state offset:", state.get("offset"))
PY

echo
echo "=== CURRENT ALERT FILE ==="
stat -c 'inode=%i | size=%s bytes' \
  /var/ossec/logs/alerts/alerts.json
```

The saved inode (`5409146`) was the same as the current `alerts.json`. In other words, it can resume simply by opening the current file directly, without listing the directory.

```bash
echo "=== STARTUP FILE HANDLING ==="
sed -n '300,390p' /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== INODE SEARCH REFERENCES ==="
grep -n -C 4 'find_inode_file\|open_initial_file' \
  /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== ROTATION HANDLING ==="
sed -n '500,680p' /usr/local/lib/wazuh-collector/collector.py
```

# Chapter 9: Fixing the Startup Processing

Here too, the fix is made on the test version, verified, and then deployed to production.

## 9.1 Startup That Prefers the Current File

There are two policies.

1. If the saved inode is the same as the current `alerts.json`, open the current file directly and resume, without listing the directory.
2. Even if the directory cannot be listed, `find_inode_file()` does not crash with an exception; it warns and returns `None`.

Back up the test version before the fix.

**Run on: security-core VM 220 (root)**

```bash
set -e

cp -a \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-startup-permission-fix-20261119

sha256sum \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-startup-permission-fix-20261119
```

Replace `find_inode_file()` and `open_initial_file()` together.

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text()

start = source.index("def find_inode_file(inode):")
end = source.index("def safe_open_current_alert_file():", start)

replacement = '''def find_inode_file(inode):
    try:
        entries = os.scandir(ALERT_DIR)
    except OSError as error:
        logging.warning(
            "Cannot scan alert directory for previous inode: %s",
            type(error).__name__,
        )
        return None

    with entries:
        for entry in entries:
            try:
                if entry.is_file(follow_symlinks=False):
                    if entry.inode() == inode:
                        return Path(entry.path)
            except OSError:
                continue

    return None


def open_initial_file(state):
    if state is None:
        handle = ALERT_FILE.open("rb")
        try:
            actual_stat = os.fstat(handle.fileno())
            handle.seek(0, os.SEEK_END)
            offset = handle.tell()
            save_state(actual_stat.st_ino, offset)
            logging.info("Initial start at current end of alerts.json")
            return handle, actual_stat.st_ino
        except Exception:
            handle.close()
            raise

    old_inode, old_offset = state

    # Prefer the current alerts.json. This avoids directory enumeration
    # when the saved inode is still the active file.
    handle = ALERT_FILE.open("rb")
    try:
        actual_stat = os.fstat(handle.fileno())
        if actual_stat.st_ino == old_inode:
            handle.seek(min(old_offset, actual_stat.st_size))
            logging.info("Resuming current alert file")
            return handle, actual_stat.st_ino
        handle.close()
        handle = None
    except Exception:
        if handle is not None:
            handle.close()
        raise

    # The active file changed. Try to resume the previous rotated file.
    old_path = find_inode_file(old_inode)

    if old_path is not None:
        handle = None
        try:
            handle = old_path.open("rb")
            actual_stat = os.fstat(handle.fileno())

            if actual_stat.st_ino == old_inode:
                handle.seek(min(old_offset, actual_stat.st_size))
                logging.info("Resuming previous rotated alert file")
                return handle, actual_stat.st_ino

            handle.close()
            handle = None
            logging.warning(
                "Previous rotated file changed while opening; using current file"
            )
        except Exception:
            if handle is not None:
                try:
                    handle.close()
                except OSError:
                    pass
            raise

    handle = ALERT_FILE.open("rb")
    try:
        actual_stat = os.fstat(handle.fileno())

        if actual_stat.st_ino == old_inode:
            handle.seek(min(old_offset, actual_stat.st_size))
        else:
            handle.seek(0)
            logging.warning(
                "Previous rotated alert file unavailable; replaying current file"
            )

        return handle, actual_stat.st_ino
    except Exception:
        handle.close()
        raise


'''

path.write_text(source[:start] + replacement + source[end:])
print("Patched test copy only:", path)
PY

python3 -m py_compile /tmp/wazuh-collector-hardening-test.py &&
sha256sum /tmp/wazuh-collector-hardening-test.py &&
sed -n '310,420p' /tmp/wazuh-collector-hardening-test.py
```

## 9.2 Where Rotated Files Are Kept

Check the assumptions for finding the old file. The per-day archives are not directly under `alerts` but in `year/month` subdirectories.

**Run on: security-core VM 220 (root)**

```bash
find /var/ossec/logs/alerts/2026/Nov \
  -maxdepth 1 -type f \
  -printf '%f | inode=%i | size=%s bytes\n' \
  | sort
```

The current `alerts.json` has the same inode as the per-day archive `ossec-alerts-18.json`. When the date changes, only the new `alerts.json` remains directly under `alerts`, and the previous day's file moves under `year/month`. So `find_inode_file()`, which searches only directly under `alerts`, cannot find a rotated old file.

If, as at the end of 9.1, the Collector silently re-reads the current file from the beginning when the old file is not found, it would not notice that unread data in the old file had been lost. So we change it so that **if the old file cannot be confirmed, it errs on the safe side and refuses to start (fail-closed)**.

## 9.3 Startup That Errs on the Safe Side

**Run on: security-core VM 220 (root)**

```bash
sed -n '300,430p' \
  /tmp/wazuh-collector-hardening-test.py
```

```bash
set -e

cp -a \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-fail-closed-20261119

sha256sum \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-fail-closed-20261119

cmp \
  /tmp/wazuh-collector-hardening-test.py \
  /tmp/wazuh-collector-hardening-test.py.backup-before-fail-closed-20261119

echo "PASS: backup verified"
```

Replace only `open_initial_file()` (`find_inode_file()` from 9.1 is used as is).

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/wazuh-collector-hardening-test.py")
source = path.read_text(encoding="utf-8")

start = source.index("def open_initial_file(state):\n")
end = source.index("\ndef safe_open_current_alert_file():\n", start)

replacement = '''def open_initial_file(state):
    if state is None:
        handle = ALERT_FILE.open("rb")
        try:
            actual_stat = os.fstat(handle.fileno())
            handle.seek(0, os.SEEK_END)
            offset = handle.tell()
            save_state(actual_stat.st_ino, offset)
            logging.info("Initial start at current end of alerts.json")
            return handle, actual_stat.st_ino
        except Exception:
            handle.close()
            raise

    old_inode, old_offset = state

    # First check whether the saved inode is still the current file.
    handle = ALERT_FILE.open("rb")
    try:
        actual_stat = os.fstat(handle.fileno())
        if actual_stat.st_ino == old_inode:
            handle.seek(min(old_offset, actual_stat.st_size))
            logging.info("Resuming current alert file")
            return handle, actual_stat.st_ino
    except Exception:
        handle.close()
        raise

    handle.close()

    # The current file changed. Resume only if the previous inode
    # can be located and verified. Never silently skip its remaining data.
    old_path = find_inode_file(old_inode)

    if old_path is None:
        raise RuntimeError(
            "Previous alert file cannot be located; refusing unsafe resume"
        )

    handle = None
    try:
        handle = old_path.open("rb")
        actual_stat = os.fstat(handle.fileno())

        if actual_stat.st_ino != old_inode:
            raise RuntimeError(
                "Previous alert file inode changed; refusing unsafe resume"
            )

        handle.seek(min(old_offset, actual_stat.st_size))
        logging.info("Resuming previous rotated alert file")
        return handle, actual_stat.st_ino

    except Exception:
        if handle is not None:
            try:
                handle.close()
            except OSError:
                pass
        raise

'''
path.write_text(source[:start] + replacement + source[end:], encoding="utf-8")
print("PASS: open_initial_file replaced")
PY

python3 -m py_compile /tmp/wazuh-collector-hardening-test.py

sha256sum /tmp/wazuh-collector-hardening-test.py
```

## 9.4 Regression Tests for Startup

Check three conditions in a temporary directory.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-hardening-test.py",
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

with tempfile.TemporaryDirectory() as tmp:
    directory = Path(tmp)
    current = directory / "alerts.json"
    current.write_bytes(b"current-event\n")

    rotated = directory / "ossec-alerts-18.json"
    rotated.write_bytes(b"old-event\n")

    m.ALERT_DIR = directory
    m.ALERT_FILE = current
    m.save_state = lambda inode, offset: None

    current_inode = current.stat().st_ino
    rotated_inode = rotated.stat().st_ino

    # Test 1: same inode resumes without directory enumeration.
    with patch.object(
        m.os,
        "scandir",
        side_effect=AssertionError("unexpected directory scan"),
    ):
        handle, inode = m.open_initial_file((current_inode, 3))
        try:
            assert inode == current_inode
            assert handle.tell() == 3
        finally:
            handle.close()
    print("PASS: same inode resumes without directory scan")

    # Test 2: previous rotated inode is located and resumed.
    handle, inode = m.open_initial_file((rotated_inode, 4))
    try:
        assert inode == rotated_inode
        assert Path(handle.name) == rotated
        assert handle.tell() == 4
    finally:
        handle.close()
    print("PASS: previous rotated file resumes at saved offset")

    # Test 3: denied directory scan must fail closed.
    with patch.object(
        m.os,
        "scandir",
        side_effect=PermissionError("test permission denial"),
    ):
        try:
            m.open_initial_file((999999999, 7))
        except RuntimeError as error:
            assert "refusing unsafe resume" in str(error)
        else:
            raise AssertionError("unsafe fallback was not rejected")
    print("PASS: inaccessible previous inode is rejected")

print("ALL STEP324-22 TESTS PASSED")
PY
```

| Test | What is checked |
|---|---|
| 1 | If the inode is the same, resume from the saved position without listing the directory |
| 2 | If the old file is found, resume from the saved position |
| 3 | If the old file cannot be confirmed, refuse to start |

> As in test 3, if it starts when the old file cannot be confirmed, the Collector stops with an error and systemd keeps restarting it. This is intended, so that alerts are never silently lost. In that case, check the state file and the alert files, remove the cause, and then start it.

## 9.5 Placing the Candidate File and Checking as the Service User

**Run on: security-core VM 220 (root)**

```bash
set -e

install -o root -g root -m 755 \
  /tmp/wazuh-collector-hardening-test.py \
  /usr/local/lib/wazuh-collector/collector.py.candidate

python3 -m py_compile \
  /usr/local/lib/wazuh-collector/collector.py.candidate

echo "=== HASH VERIFICATION ==="
sha256sum \
  /tmp/wazuh-collector-hardening-test.py \
  /usr/local/lib/wazuh-collector/collector.py.candidate

echo "=== FILE PERMISSIONS ==="
stat -c '%n | %U:%G | %a | %s bytes' \
  /usr/local/lib/wazuh-collector/collector.py.candidate
```

The candidate file at build time was 18,898 bytes with SHA-256 `7a816056...`.

As the same `wazuh-collector` user as production, check that it can read the production state file and open the current `alerts.json` at the correct position (this only reads; the state file is not changed). Because the extension is not `.py`, load it with an explicit loader.

```bash
sudo -u wazuh-collector /usr/bin/python3 - <<'PY'
import importlib.util
import importlib.machinery

path = "/usr/local/lib/wazuh-collector/collector.py.candidate"

loader = importlib.machinery.SourceFileLoader(
    "collector_candidate",
    path,
)
spec = importlib.util.spec_from_loader(loader.name, loader)

m = importlib.util.module_from_spec(spec)
loader.exec_module(m)

state = m.load_state()
assert state is not None, "collector state is missing"

saved_inode, saved_offset = state
handle, active_inode = m.open_initial_file(state)

try:
    actual_offset = handle.tell()

    assert active_inode == saved_inode, "inode mismatch"
    assert actual_offset == saved_offset, "offset mismatch"

    print("PASS: service user loaded state")
    print("PASS: service user opened alerts.json")
    print("PASS: saved inode matched current inode")
    print("PASS: saved offset restored")
    print("inode:", active_inode)
    print("offset:", actual_offset)
finally:
    handle.close()

print("ALL STEP324-24 TESTS PASSED")
PY
```

At build time this gave inode `5409146` and position `2178712`, matching the saved values.

# Chapter 10: Redeploying and Checking Operation

## 10.1 Deploying the Fixed Version to Production

After confirming that the Collector is stopped (`inactive`) and that the production code is the version deployed in 8.4 (`d404f10a...`), preserve that version under another name and replace it with the fixed version. If any condition is not met, `set -e` stops there. The service is not started yet.

**Run on: security-core VM 220 (root)**

```bash
set -e

PROD=/usr/local/lib/wazuh-collector/collector.py
CANDIDATE=/usr/local/lib/wazuh-collector/collector.py.candidate
NEW=/usr/local/lib/wazuh-collector/collector.py.new
BACKUP=/usr/local/lib/wazuh-collector/collector.py.backup-before-fail-closed-20261119

echo "=== PRECHECK ==="

test "$(sha256sum "$PROD" | awk '{print $1}')" = \
  "d404f10ac8aea659a227665e617b2cb9c996b7b989f42dc4a3b8abd648a0796b"

test "$(systemctl is-active wazuh-collector.service)" = "inactive"

test ! -e "$BACKUP"

echo "PASS: production hash verified"
echo "PASS: collector service is inactive"

echo
echo "=== PRESERVE CURRENT PRODUCTION ==="

cp -a "$PROD" "$BACKUP"

echo "=== INSTALL NEW VERSION ==="

install -o root -g root -m 755 "$CANDIDATE" "$NEW"
cmp "$CANDIDATE" "$NEW"
mv -f "$NEW" "$PROD"

echo
echo "=== VERIFY DEPLOYMENT ==="

sha256sum "$PROD" "$BACKUP"

stat -c '%n | %U:%G | %a | %s bytes' "$PROD" "$BACKUP"

echo "PASS: atomic deployment completed"
```

> The hash value `d404f10a...` is that of the version deployed in 8.4 in the original build. In your environment, replace it with your own value shown after 8.4.

| File | Contents |
|---|---|
| `collector.py` | Fixed version (`7a816056...`, 18,898 bytes) |
| `collector.py.backup-before-fail-closed-20261119` | Version deployed in 8.4 (`d404f10a...`) |
| `collector.py.backup-20261119` | Production version before Part 4 (`931ee3cb...`) |
| `collector.py.backup-pre-hardening-20261118` | Same as above (created in Part 4, 1.5) |

## 10.2 Checks Before Startup, and Starting

**Run on: security-core VM 220 (root)**

```bash
set -e

echo "=== PYTHON SYNTAX ==="
python3 -m py_compile \
  /usr/local/lib/wazuh-collector/collector.py

echo "PASS: Python syntax"

echo
echo "=== PRODUCTION HASH ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== SERVICE STATUS ==="
systemctl is-active wazuh-collector.service || true
systemctl show wazuh-collector.service \
  -p User -p Group -p ExecStart -p Restart -p RestartSec

echo
echo "=== STATE FILE PERMISSIONS ==="
stat -c '%n | %U:%G | %a | %s bytes' \
  /var/lib/wazuh-collector/state.json
```

```bash
systemctl start wazuh-collector.service

sleep 3

echo "=== SERVICE STATUS ==="
systemctl is-active wazuh-collector.service

echo
echo "=== SERVICE DETAILS ==="
systemctl show wazuh-collector.service \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p NRestarts \
  -p ExecMainStatus

echo
echo "=== RECENT JOURNAL ==="
journalctl -u wazuh-collector.service -n 20 --no-pager
```

If the following three lines appear in the log, it has resumed normally with the fixed startup processing (output at build time).

```text
Nov 18 15:31:53 security-core python3[87457]: 2026-11-18 15:31:53,441 INFO Wazuh alert collector starting
Nov 18 15:31:53 security-core python3[87457]: 2026-11-18 15:31:53,441 INFO Resuming current alert file
Nov 18 15:31:53 security-core python3[87457]: 2026-11-18 15:31:53,463 INFO PostgreSQL connection established
```

## 10.3 Stability After Startup and Keeping Up with Reading

**Run on: security-core VM 220 (root)**

```bash
echo "=== SERVICE RUNTIME ==="
systemctl show wazuh-collector.service \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p NRestarts \
  -p ActiveEnterTimestamp \
  -p ExecMainStartTimestamp

echo
echo "=== PROCESS ==="
ps -p "$(systemctl show -p MainPID --value wazuh-collector.service)" \
  -o pid,etime,%cpu,%mem,stat,cmd

echo
echo "=== LATEST COLLECTOR LOGS ==="
journalctl -u wazuh-collector.service -n 15 --no-pager
```

Check as the service user whether the read position has caught up with `alerts.json` (the state file is only read).

```bash
echo "=== COLLECTOR READ POSITION ==="

sudo -u wazuh-collector /usr/bin/python3 - <<'PY'
import importlib.util
import importlib.machinery
import os

path = "/usr/local/lib/wazuh-collector/collector.py"
loader = importlib.machinery.SourceFileLoader("collector_check", path)
spec = importlib.util.spec_from_loader(loader.name, loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)

state = m.load_state()
assert state is not None, "state missing"

saved_inode, saved_offset = state
current = os.stat(m.ALERT_FILE)

print("saved_inode:", saved_inode)
print("current_inode:", current.st_ino)
print("saved_offset:", saved_offset)
print("current_file_size:", current.st_size)

if saved_inode == current.st_ino:
    print("unread_bytes:", max(0, current.st_size - saved_offset))
    print("PASS: state refers to current alerts.json")
else:
    print("NOTICE: state refers to a rotated file")
PY

echo
echo "=== LOGS SINCE CURRENT START ==="
journalctl -u wazuh-collector.service \
  --since "2026-11-18 15:31:53 UTC" \
  --no-pager
```

Set the `--since` time to when you started it. 30 seconds later, check the running state and warnings again.

```bash
sleep 30

echo "=== SERVICE HEALTH ==="
systemctl show wazuh-collector.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts

echo
echo "=== READ POSITION ==="
sudo -u wazuh-collector /usr/bin/python3 - <<'PY'
import json
import os

state_path = "/var/lib/wazuh-collector/state.json"
alert_path = "/var/ossec/logs/alerts/alerts.json"

with open(state_path, "r", encoding="utf-8") as f:
    state = json.load(f)

st = os.stat(alert_path)

print("saved_inode:", state["inode"])
print("current_inode:", st.st_ino)
print("saved_offset:", state["offset"])
print("current_file_size:", st.st_size)

if state["inode"] == st.st_ino:
    print("unread_bytes:", max(0, st.st_size - state["offset"]))
else:
    print("NOTICE: rotation detected")
PY

echo
echo "=== RECENT ERRORS ==="
journalctl -u wazuh-collector.service \
  --since "1 minute ago" \
  -p warning --no-pager
```

If `unread_bytes` is 0 or a small value and `RECENT ERRORS` shows `-- No entries --`, it is keeping up with new alerts and working normally.

## 10.4 Reconciling Counts Between Wazuh and PostgreSQL

The DB-side check is done inside LXC 109 as the DB administrator (`postgres`) (the prompt is `root@postgresql`).

**Run on: LXC 109 postgresql (root)**

```bash
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    COUNT(*) AS total_events,
    MAX(event_timestamp) AS latest_event_timestamp,
    MAX(ingested_at) AS latest_ingested_at,
    COUNT(*) FILTER (
        WHERE ingested_at >= NOW() - INTERVAL '15 minutes'
    ) AS ingested_last_15m
FROM incident.alert_events;
"
```

```bash
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    COUNT(*) AS total_events,
    MIN(event_timestamp) AS earliest_event,
    MAX(event_timestamp) AS latest_event,
    MIN(ingested_at) AS earliest_ingested,
    MAX(ingested_at) AS latest_ingested
FROM incident.alert_events;
"
```

Taking the time of the oldest alert in the DB (`2026-11-18 11:00:59 UTC` at build time, right after the Collector was first started in Part 3) as the starting point, count the alerts on the Wazuh side for the same period.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import json

path = "/var/ossec/logs/alerts/alerts.json"
count = 0
invalid = 0

with open(path, "rb") as f:
    for line in f:
        if not line.strip():
            continue
        try:
            json.loads(line)
            count += 1
        except (json.JSONDecodeError, UnicodeDecodeError):
            invalid += 1

print("valid_json_records:", count)
print("invalid_records:", invalid)
PY
```

```bash
python3 - <<'PY'
import json
from datetime import datetime, timezone

path = "/var/ossec/logs/alerts/alerts.json"
start = datetime(2026, 11, 18, 11, 0, 59, tzinfo=timezone.utc)

total = 0
matched = 0
invalid = 0
missing_timestamp = 0

with open(path, "rb") as f:
    for line in f:
        if not line.strip():
            continue

        try:
            obj = json.loads(line)
            total += 1
            value = obj.get("timestamp")

            if not isinstance(value, str):
                missing_timestamp += 1
                continue

            ts = datetime.fromisoformat(value.replace("Z", "+00:00"))

            if ts.tzinfo is None:
                continue

            if ts.astimezone(timezone.utc) >= start:
                matched += 1

        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            invalid += 1

print("total_records:", total)
print("records_since_2026-11-18_11:00:59_UTC:", matched)
print("missing_timestamp:", missing_timestamp)
print("invalid_records:", invalid)
PY
```

Replace the `start` date and time with the time of the oldest alert in your environment's DB. Then recount the DB side for the same period.

**Run on: LXC 109 postgresql (root)**

```bash
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    COUNT(*) AS total_events,
    COUNT(*) FILTER (
        WHERE event_timestamp >= TIMESTAMPTZ '2026-11-18 11:00:59+00'
    ) AS events_in_comparison_period,
    MAX(event_timestamp) AS latest_event_timestamp,
    MAX(ingested_at) AS latest_ingested_at,
    COUNT(*) FILTER (
        WHERE ingested_at >= NOW() - INTERVAL '5 minutes'
    ) AS ingested_last_5m
FROM incident.alert_events;
"
```

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

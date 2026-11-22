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

```bash
cat > /tmp/test_step330_cleanup.py <<'PY'
import importlib.util
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "collector_test",
    "/tmp/wazuh-collector-step330-test.py",
)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)

with tempfile.TemporaryDirectory(prefix="step330-cleanup-") as tmp:
    root = Path(tmp)
    alert_dir = root / "alerts"
    alert_dir.mkdir()

    current = alert_dir / "alerts.json"
    impostor = alert_dir / "impostor.json"
    current.write_bytes(b'{"current":true}\n')
    impostor.write_bytes(b'{"impostor":true}\n')

    collector.ALERT_FILE = current
    collector.ALERT_DIR = alert_dir
    collector.STATE_FILE = root / "state" / "state.json"
    collector.STATE_FILE.parent.mkdir()

    sentinel = b'{"inode":123,"offset":456}\n'
    collector.STATE_FILE.write_bytes(sentinel)

    wrong_inode = impostor.stat().st_ino + 1
    before = len(os.listdir("/proc/self/fd"))

    with patch.object(
        collector,
        "find_inode_file",
        return_value=impostor,
    ):
        try:
            collector.open_initial_file((wrong_inode, 0))
        except RuntimeError:
            pass
        else:
            raise AssertionError("Expected inode mismatch rejection")

    after = len(os.listdir("/proc/self/fd"))

    assert after == before, (before, after)
    print("PASS: no file descriptor leak")

    assert collector.STATE_FILE.read_bytes() == sentinel
    print("PASS: existing state file unchanged")

print("PASS: cleanup tests completed")
PY

python3 /tmp/test_step330_cleanup.py
```

## 1.2 Checks Before Deploying

**Run on: security-core VM 220 (root)**

```bash
echo "=== PRODUCTION ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== BACKUP ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py.backup-before-recursive-rotation-20261119

echo
echo "=== TEST CANDIDATE ==="
sha256sum /tmp/wazuh-collector-step330-test.py

echo
echo "=== FILE PERMISSIONS ==="
stat -c '%n | %U:%G | %a | %s bytes' \
  /usr/local/lib/wazuh-collector/collector.py \
  /usr/local/lib/wazuh-collector/collector.py.backup-before-recursive-rotation-20261119 \
  /tmp/wazuh-collector-step330-test.py
```

| File | SHA-256 (at build time) |
|---|---|
| Production | `ac297477...` |
| Backup (the Part 5 version) | `7a816056...` |
| Candidate (test version) | `df4a9ff6...` (19,593 bytes) |

## 1.3 Deploying to Production

Check the hashes of production and the candidate, make an additional backup of the current production code, and replace it in one step. The service is not restarted yet.

**Run on: security-core VM 220 (root)**

```bash
set -euo pipefail

PROD=/usr/local/lib/wazuh-collector/collector.py
CANDIDATE=/tmp/wazuh-collector-step330-test.py
BACKUP=/usr/local/lib/wazuh-collector/collector.py.backup-before-step330-offset-20261119
TEMP=/usr/local/lib/wazuh-collector/.collector.py.step330.tmp

echo "=== PRE-INSTALL VALIDATION ==="
test "$(sha256sum "$PROD" | awk '{print $1}')" = \
  "ac2974775d46b902ee69b3e7219bf9cb550c7d8a65c38cbdf8ac89ecc67a5e96"
test "$(sha256sum "$CANDIDATE" | awk '{print $1}')" = \
  "df4a9ff6c55767851bf9c9831c1d96862e876a4f030d52aa9e394224e51d0a3e"
test ! -e "$BACKUP"
test ! -e "$TEMP"

echo "PASS: source hashes and backup path"

echo
echo "=== CREATE ADDITIONAL BACKUP ==="
cp -a "$PROD" "$BACKUP"
test "$(sha256sum "$BACKUP" | awk '{print $1}')" = \
  "ac2974775d46b902ee69b3e7219bf9cb550c7d8a65c38cbdf8ac89ecc67a5e96"
echo "PASS: additional backup created"

echo
echo "=== INSTALL CANDIDATE ATOMICALLY ==="
install -o root -g root -m 755 "$CANDIDATE" "$TEMP"
python3 -c 'from pathlib import Path; p=Path("'"$TEMP"'"); compile(p.read_text(encoding="utf-8"), str(p), "exec")'
mv -f "$TEMP" "$PROD"

echo
echo "=== POST-INSTALL VALIDATION ==="
sha256sum "$PROD" "$BACKUP"
stat -c '%n | %U:%G | %a | %s bytes' "$PROD" "$BACKUP"
python3 -c 'from pathlib import Path; p=Path("'"$PROD"'"); compile(p.read_text(encoding="utf-8"), str(p), "exec"); print("PASS: production syntax")'

echo
echo "=== SERVICE STATUS (NOT RESTARTED) ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts
```

Replace the two hashes with your environment's values for production (before deployment) and the candidate.

## 1.4 Restarting and Checking

**Run on: security-core VM 220 (root)**

```bash
systemctl restart wazuh-collector

echo "=== SERVICE STATUS ==="
systemctl show wazuh-collector \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p NRestarts \
  -p ExecMainStatus

echo
echo "=== RECENT JOURNAL ==="
journalctl -u wazuh-collector -n 30 --no-pager
```

```bash
echo "=== JOURNAL SINCE RESTART ==="
journalctl -u wazuh-collector \
  --since "2026-11-18 21:53:00" \
  --no-pager

echo
echo "=== STATE FILE METADATA ==="
stat -c '%n | %U:%G | %a | %s bytes | modified=%y' \
  /var/lib/wazuh-collector/state.json

echo
echo "=== STATE VALUES ==="
python3 - <<'PY'
import json
from pathlib import Path

p = Path("/var/lib/wazuh-collector/state.json")
s = json.loads(p.read_text())
print("inode:", s["inode"])
print("offset:", s["offset"])
PY

echo
echo "=== SERVICE STATUS ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts
```

At build time, `Resuming current alert file` was shown with the new PID `91473`, and it resumed from the saved inode `5409146`. As in Part 6, 8.1, the DB connection is made when a new alert is read.

# Chapter 2: Checking Ingestion After Deployment

## 2.1 The DB Baseline

**Run on: LXC 109 postgresql (root)**

```bash
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    COUNT(*) AS total_events,
    MAX(ingested_at) AS latest_ingested_at,
    MAX(event_timestamp) AS latest_event_timestamp
FROM incident.alert_events;
"
```

At build time there were 727 rows.

## 2.2 Ingesting New Alerts

Wait for a new alert to arrive, then check the log after the restart.

**Run on: security-core VM 220 (root)**

```bash
journalctl -u wazuh-collector \
  --since "2026-11-18 21:53:13" \
  --no-pager
```

At build time, it detected a new alert and connected to the DB about five minutes after the restart.

```text
21:58:08 INFO PostgreSQL connection established
```

**Run on: LXC 109 postgresql (root)**

```bash
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    COUNT(*) AS total_events,
    MAX(ingested_at) AS latest_ingested_at,
    MAX(event_timestamp) AS latest_event_timestamp
FROM incident.alert_events;
"
```

The count had increased from 727 to 730, and the new alerts had been inserted. The position in the state file also matched the end of `alerts.json`.

# Chapter 3: Testing Duplicate Handling on the Real DB

## 3.1 The Approach

In Parts 4 and 6 we tested duplicate handling with a mock connection. Here we use the production Collector code and the real PostgreSQL (with `wazuh_collector`'s privileges), do everything inside an outer transaction, and always roll back at the end. No test data remains in the production table.

When `connection.transaction()` is called while already inside a transaction, it becomes a savepoint. So even if a duplicate causes an error, only that savepoint is rolled back, and the next event should be processable on the same connection.

## 3.2 The Test

**Run on: security-core VM 220 (root)**

```bash
cat > /tmp/test_step330_20e.py <<'PY'
import importlib.util
import json
import uuid
from datetime import datetime, timezone

import psycopg


SOURCE = "/usr/local/lib/wazuh-collector/collector.py"

spec = importlib.util.spec_from_file_location(
    "collector_step330_20e",
    SOURCE,
)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class RollbackOnly(Exception):
    pass


def make_alert(event_id):
    return {
        "id": event_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rule": {
            "id": 100001,
            "level": 3,
            "description": "STEP330-20E rollback-only test",
            "groups": ["step330-test"],
            "mitre": {},
        },
        "agent": {
            "id": "000",
            "name": "security-core",
        },
        "manager": {
            "name": "security-core",
        },
        "decoder": {
            "name": "json",
        },
    }


prefix = "step33020e-" + uuid.uuid4().hex

first_alert = make_alert(prefix + "-duplicate")
next_alert = make_alert(prefix + "-next")

first_event = collector.extract_event(first_alert)

if first_event is None:
    raise RuntimeError("Test fixture validation failed")

connection = psycopg.connect(**collector.DB_CONFIG)

try:
    try:
        with connection.transaction():
            # Seed one event inside the outer transaction.
            connection.execute(
                collector.INSERT_SQL,
                first_event,
            )

            print("PASS: initial test event inserted")

            # Same event_id must trigger UniqueViolation.
            collector.process_line(
                connection,
                json.dumps(first_alert).encode("utf-8"),
            )

            print("PASS: duplicate event handled")

            if (
                connection.info.transaction_status
                != psycopg.pq.TransactionStatus.INTRANS
            ):
                raise AssertionError(
                    "Transaction did not recover after duplicate"
                )

            print("PASS: transaction remains usable after duplicate")

            # A different event must succeed on the same connection.
            collector.process_line(
                connection,
                json.dumps(next_alert).encode("utf-8"),
            )

            print("PASS: next event processed on same connection")

            if (
                connection.info.transaction_status
                != psycopg.pq.TransactionStatus.INTRANS
            ):
                raise AssertionError(
                    "Transaction unexpectedly left active state"
                )

            # Force rollback of every test INSERT.
            raise RollbackOnly()

    except RollbackOnly:
        pass

    if (
        connection.info.transaction_status
        != psycopg.pq.TransactionStatus.IDLE
    ):
        raise AssertionError("Connection did not return to IDLE")

    print("PASS: outer transaction rolled back")
    print("PASS: connection returned to IDLE")
    print("PASS: no test rows committed")

finally:
    connection.close()

print("PASS: STEP330-20E")
PY

python3 /tmp/test_step330_20e.py
```

| Check | Meaning |
|---|---|
| `initial test event inserted` | The first row was inserted |
| `duplicate event handled` | The second row with the same ID was handled as `UniqueViolation` |
| `transaction remains usable after duplicate` | The transaction is still usable after the duplicate |
| `next event processed on same connection` | Another event could be inserted on the same connection |
| `no test rows committed` | Everything was rolled back at the end |

## 3.3 Confirming That No Test Data Remains

**Run on: LXC 109 postgresql (root)**

```bash
sudo -u postgres psql -X -d security_workbench -c "
SELECT
    COUNT(*) AS total_events,
    COUNT(*) FILTER (
        WHERE event_id LIKE 'step33020e-%'
    ) AS remaining_test_events,
    MAX(ingested_at) AS latest_ingested_at
FROM incident.alert_events;
"
```

If `remaining_test_events` is `0`, not a single test row remains.

# Chapter 4: Isolated Tests Using the Production Code

From here on, we load the production `collector.py` as a Python module, replace only the file paths with a temporary directory, and test the actual functions. `run()` is not started, so the production service, log, state file and DB are not touched.

> The old test copies (`/tmp/wazuh-collector-rotation-test.py` and others) do not contain the fixes made after deployment to production. Also, running them as they are starts the resident loop using the production paths. Always run the tests by loading the production code and replacing the paths.

## 4.1 Resuming and Refusing at Startup

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "collector_rotation_test",
    "/usr/local/lib/wazuh-collector/collector.py",
)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


def setup():
    tmp = tempfile.TemporaryDirectory(prefix="step330-22e-")
    root = Path(tmp.name)
    current = root / "alerts.json"
    current.write_bytes(b"new-file-data")

    collector.ALERT_FILE = current
    collector.ALERT_DIR = root
    collector.STATE_FILE = root / "state.json"

    return tmp, root, current


def expect_refusal(state, label):
    try:
        handle, _ = collector.open_initial_file(state)
    except RuntimeError:
        print(f"PASS: {label}")
        return
    else:
        handle.close()
        raise AssertionError(f"FAIL: {label} was accepted")


# 1. Current file resume
tmp, root, current = setup()
try:
    inode = current.stat().st_ino
    handle, active_inode = collector.open_initial_file((inode, 4))
    assert active_inode == inode
    assert handle.tell() == 4
    assert handle.read() == b"file-data"
    handle.close()
    print("PASS: current file resume")
finally:
    tmp.cleanup()


# 2. Previous rotated file resume
tmp, root, current = setup()
try:
    old_dir = root / "archive" / "2026"
    old_dir.mkdir(parents=True)
    old_file = old_dir / "alerts-old.json"
    old_file.write_bytes(b"old-file-data")

    old_inode = old_file.stat().st_ino
    handle, active_inode = collector.open_initial_file((old_inode, 4))
    assert active_inode == old_inode
    assert handle.tell() == 4
    assert handle.read() == b"file-data"
    handle.close()
    print("PASS: previous rotated file resume")
finally:
    tmp.cleanup()


# 3. Previous inode missing
tmp, root, current = setup()
try:
    expect_refusal((999999999, 0), "missing previous inode refused")
finally:
    tmp.cleanup()


# 4. Current file offset exceeds size
tmp, root, current = setup()
try:
    expect_refusal(
        (current.stat().st_ino, current.stat().st_size + 1),
        "current file oversized offset refused",
    )
finally:
    tmp.cleanup()


# 5. Previous rotated file offset exceeds size
tmp, root, current = setup()
try:
    old_dir = root / "archive"
    old_dir.mkdir()
    old_file = old_dir / "alerts-old.json"
    old_file.write_bytes(b"old-data")

    expect_refusal(
        (old_file.stat().st_ino, old_file.stat().st_size + 1),
        "rotated file oversized offset refused",
    )
finally:
    tmp.cleanup()


print("PASS: STEP330-22E ALL TESTS")
PY
```

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

```bash
python3 - <<'PY'
import importlib.util
import json
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "collector_step330_23",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

with tempfile.TemporaryDirectory(prefix="step330-23d-") as tmp:
    root = Path(tmp)
    archive = root / "archive"
    archive.mkdir()

    old_file = root / "alerts.json"
    new_file = root / "new-alerts.json"

    old_file.write_bytes(b'{"id":"incomplete')
    c.ALERT_FILE = old_file
    c.ALERT_DIR = root
    c.STATE_FILE = root / "state.json"

    # Open old file and detect incomplete JSON line.
    handle = old_file.open("rb")
    old_inode = handle.fileno()
    old_inode = __import__("os").fstat(old_inode).st_ino

    status, line, _ = c.read_alert_line(handle)
    assert status == "incomplete"
    assert line is None
    print("PASS: incomplete old line detected")

    # Simulate log rotation: preserve old inode and create new alerts.json.
    old_path = archive / "alerts-old.json"
    old_file.rename(old_path)

    valid_alert = (
        b'{"id":"new-event","timestamp":"2026-11-19T00:00:00+00:00",'
        b'"rule":{"id":"100001","level":5},'
        b'"agent":{"id":"000","name":"test"},'
        b'"manager":{"name":"test"},'
        b'"decoder":{"name":"test"}}\n'
    )
    old_file.write_bytes(valid_alert)

    # Follow the production incomplete-line rotation branch.
    current_stat = c.ALERT_FILE.stat()
    assert current_stat.st_ino != old_inode

    new_handle, new_stat = c.safe_open_current_alert_file()
    assert new_handle is not None
    assert new_stat.st_ino == current_stat.st_ino

    c.save_state(new_stat.st_ino, 0)

    handle.close()
    handle = new_handle

    state = json.loads(c.STATE_FILE.read_text())
    assert state == {"inode": new_stat.st_ino, "offset": 0}
    print("PASS: new inode and offset 0 saved")

    # Ensure the old incomplete fragment is never returned as an event.
    status, line, _ = c.read_alert_line(handle)
    assert status == "line"
    parsed = json.loads(line)
    assert parsed["id"] == "new-event"
    assert parsed["id"] != "incomplete"
    print("PASS: valid new-file JSON read")
    print("PASS: incomplete old fragment not processed")

    handle.close()

print("PASS: STEP330-23D ALL TESTS")
PY
```

`STATE_FILE` is also replaced with the temporary directory, so the production state file does not change.

# Chapter 5: Handling Huge Alert Lines

## 5.1 The Limit and Chunked Reading

The production Collector limits a line to 1 MiB (`MAX_ALERT_LINE_BYTES` = 1,048,576 bytes) and discards lines over the limit 64 KiB (`READ_CHUNK_BYTES` = 65,536 bytes) at a time. Test a line exactly at the limit, a line over the limit, a line discarded over many reads, and a line that reaches the end of the file without a newline.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "collector_step330_24a",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

MAX = c.MAX_ALERT_LINE_BYTES
CHUNK = c.READ_CHUNK_BYTES
valid = b'{"id":"after-oversized"}\n'

with tempfile.TemporaryDirectory(prefix="step330-24a-") as tmp:
    path = Path(tmp) / "alerts.json"

    # Test 1: exactly the configured maximum, including newline.
    path.write_bytes(b"x" * (MAX - 1) + b"\n")
    with path.open("rb") as handle:
        status, line, discarding = c.read_alert_line(handle)
        assert status == "line"
        assert len(line) == MAX
        assert discarding is False
        print("PASS: maximum-size line accepted")

    # Test 2: oversized line followed by a valid line.
    path.write_bytes(b"x" * MAX + b"\n" + valid)
    with path.open("rb") as handle:
        status, line, discarding = c.read_alert_line(handle)
        assert status == "oversized"
        assert line is None
        assert discarding is False

        status, line, discarding = c.read_alert_line(handle)
        assert status == "line"
        assert line == valid
        print("PASS: oversized line rejected; next valid line preserved")

    # Test 3: very large line requiring repeated chunk discards.
    huge = b"x" * (MAX + CHUNK * 3 + 17) + b"\n"
    path.write_bytes(huge + valid)

    with path.open("rb") as handle:
        status, line, discarding = c.read_alert_line(handle)
        assert status == "discarding"
        assert line is None
        assert discarding is True

        discard_calls = 0
        while True:
            status, line, discarding = c.read_alert_line(
                handle, discarding=True
            )
            discard_calls += 1

            if status == "oversized":
                break

            assert status == "discarding"
            assert line is None
            assert discarding is True

        assert discard_calls >= 3

        status, line, discarding = c.read_alert_line(handle)
        assert status == "line"
        assert line == valid
        print(
            "PASS: multi-chunk oversized line discarded; "
            "next valid line preserved"
        )

    # Test 4: oversized incomplete line ending at EOF.
    path.write_bytes(b"x" * (MAX + 1))

    with path.open("rb") as handle:
        status, line, discarding = c.read_alert_line(handle)
        assert status == "discarding"
        assert discarding is True

        status, line, discarding = c.read_alert_line(
            handle, discarding=True
        )
        assert status == "eof"
        assert line is None
        assert discarding is False
        print("PASS: oversized incomplete line reaches EOF safely")

print("PASS: STEP330-24A ALL TESTS")
PY
```

## 5.2 Rotation While Discarding

Confirm that when the end of the file is reached while discarding a huge line and a rotation happens meanwhile, the Collector switches to the new file and the discarding state is reset.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util
import json
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "collector_step330_24b",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

with tempfile.TemporaryDirectory(prefix="step330-24b-") as tmp:
    root = Path(tmp)
    c.ALERT_FILE = root / "alerts.json"
    c.STATE_FILE = root / "state.json"

    old_path = c.ALERT_FILE
    archive_path = root / "alerts.json.1"
    valid = b'{"id":"after-rotation"}\n'

    # Create an oversized, incomplete old-file line.
    old_path.write_bytes(
        b"x" * (
            c.MAX_ALERT_LINE_BYTES
            + c.READ_CHUNK_BYTES * 2
            + 17
        )
    )

    old_handle = old_path.open("rb")
    old_inode = old_path.stat().st_ino

    status, line, discarding = c.read_alert_line(old_handle)
    assert status == "discarding"
    assert line is None
    assert discarding is True
    print("PASS: oversized line enters discard mode")

    # Continue discarding until the old file reaches EOF.
    while True:
        status, line, next_discarding = c.read_alert_line(
            old_handle,
            discarding=discarding,
        )
        if status == "eof":
            break
        assert status == "discarding"
        assert line is None
        assert next_discarding is True
        discarding = next_discarding

    print("PASS: old oversized line reaches EOF")

    # Rotate old file and create a new file with a valid alert.
    old_path.rename(archive_path)
    old_path.write_bytes(valid)
    new_inode = old_path.stat().st_ino
    assert new_inode != old_inode

    # Exercise the same file-switch operations as production run().
    new_handle, new_stat = c.safe_open_current_alert_file()
    assert new_handle is not None
    assert new_stat.st_ino == new_inode

    c.save_state(new_stat.st_ino, 0)

    old_handle.close()
    active_handle = new_handle
    active_inode = new_stat.st_ino
    discarding = False
    discard_start = None

    assert active_inode == new_inode
    assert discarding is False
    assert discard_start is None
    print("PASS: new inode saved and discard state reset")

    # The first line in the new file must be read normally.
    status, line, _ = c.read_alert_line(active_handle)
    assert status == "line"
    assert line == valid
    assert json.loads(line)["id"] == "after-rotation"
    print("PASS: valid new-file alert read successfully")

    state = json.loads(c.STATE_FILE.read_text())
    assert state["inode"] == new_inode
    assert state["offset"] == 0
    print("PASS: persisted state references new inode at offset 0")

    active_handle.close()

print("PASS: STEP330-24B ALL TESTS")
PY
```

## 5.3 Saving the Position After Discarding and Resuming

Confirm that the position after discarding a huge line is saved and that after a restart the Collector resumes from the next line. `load_state()` returns an `(inode, offset)` pair (tuple).

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util
import json
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "collector_step330_24c_retry",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

with tempfile.TemporaryDirectory(prefix="step330-24c-retry-") as tmp:
    root = Path(tmp)
    c.STATE_FILE = root / "state.json"
    alert_path = root / "alerts.json"

    valid = b'{"id":"after-large-line"}\n'
    oversized = (
        b"x" * (c.MAX_ALERT_LINE_BYTES + c.READ_CHUNK_BYTES * 2)
        + b"\n"
    )
    alert_path.write_bytes(oversized + valid)

    with alert_path.open("rb") as handle:
        status, line, discarding = c.read_alert_line(handle)
        assert status == "discarding"
        assert discarding is True

        while True:
            status, line, next_discarding = c.read_alert_line(
                handle,
                discarding=True,
            )
            if status == "oversized":
                break
            assert status == "discarding"
            assert next_discarding is True

        c.save_state(alert_path.stat().st_ino, handle.tell())

        state = json.loads(c.STATE_FILE.read_text())
        assert state["inode"] == alert_path.stat().st_ino
        assert state["offset"] == len(oversized)
        print("PASS: oversized-line offset persisted")

        status, line, _ = c.read_alert_line(handle)
        assert status == "line"
        assert line == valid
        print("PASS: following valid alert preserved")

    # Production load_state returns (inode, offset).
    saved_inode, saved_offset = c.load_state()
    assert saved_inode == alert_path.stat().st_ino
    assert saved_offset == len(oversized)
    print("PASS: load_state restored inode and offset")

    with alert_path.open("rb") as resumed:
        resumed.seek(saved_offset)
        status, line, _ = c.read_alert_line(resumed)
        assert status == "line"
        assert line == valid
        print("PASS: restart resumes after oversized line")

print("PASS: STEP330-24C ALL TESTS")
PY
```

This test may also be run in an ordinary user's (`ag`) shell. It does not write to production files.

# Chapter 6: Boundary Values for Input Validation

## 6.1 Boundary-Value Tests

Confirm that the production `extract_event()` rejects or truncates malformed values, out-of-range values and overly long strings, and outputs only the defined fields. `full_log` and unexpected fields do not end up in what is inserted into the DB.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import copy
import importlib.util
from datetime import datetime

spec = importlib.util.spec_from_file_location(
    "collector_step330_25a",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

baseline = {
    "id": "step330-25a-test",
    "timestamp": "2026-11-19T07:00:00+09:00",
    "rule": {
        "id": "100001",
        "level": 10,
        "description": "test alert",
        "groups": ["syslog", "authentication"],
        "mitre": {
            "id": ["T1110"],
            "tactic": ["Credential Access"],
            "technique": ["Brute Force"],
            "unexpected": "must not persist",
        },
    },
    "agent": {"id": "001", "name": "test-agent"},
    "manager": {"name": "test-manager"},
    "decoder": {"name": "test-decoder"},
    "data": {"srcip": "192.0.2.10", "srcport": 443},
    "full_log": "must never persist",
    "unexpected": {"secret": "must never persist"},
}

# 1. Valid baseline.
event = c.extract_event(copy.deepcopy(baseline))
assert event is not None
assert isinstance(event["event_timestamp"], datetime)
print("PASS: valid baseline accepted")

# 2. Invalid top-level structures.
for value in (None, [], "text", 123):
    assert c.extract_event(value) is None
print("PASS: non-object top-level input rejected")

# 3. Required nested objects.
for key in ("rule", "agent", "manager", "decoder"):
    test = copy.deepcopy(baseline)
    test[key] = []
    assert c.extract_event(test) is None
print("PASS: invalid required nested objects rejected")

# 4. Invalid required numeric fields.
for key, value in (
    ("id", True),
    ("id", -1),
    ("id", 2147483648),
    ("id", "1;DROP"),
    ("level", True),
    ("level", 17),
    ("level", -1),
):
    test = copy.deepcopy(baseline)
    test["rule"][key] = value
    assert c.extract_event(test) is None
print("PASS: invalid rule IDs and levels rejected")

# 5. Invalid timestamps.
for value in (
    None,
    "",
    "not-a-timestamp",
    "2026-11-19T07:00:00",
    "x" * 65,
):
    test = copy.deepcopy(baseline)
    test["timestamp"] = value
    assert c.extract_event(test) is None
print("PASS: invalid timestamps rejected")

# 6. Text length and control-character handling.
test = copy.deepcopy(baseline)
test["rule"]["description"] = "A" * 5000 + "\x00"
event = c.extract_event(test)
assert event is not None
assert len(event["rule_description"]) == 4096
assert "\x00" not in event["rule_description"]
print("PASS: text sanitized and limited to 4096 characters")

# 7. String-list limits.
test = copy.deepcopy(baseline)
test["rule"]["groups"] = ["G" + str(i) for i in range(100)]
event = c.extract_event(test)
assert len(event["rule_groups"]) == 64
print("PASS: rule groups limited to 64 items")

# 8. Invalid IP and port.
test = copy.deepcopy(baseline)
test["data"] = {"srcip": "999.999.999.999", "srcport": 70000}
event = c.extract_event(test)
assert event["srcip"] is None
assert event["srcport"] is None
print("PASS: invalid IP and port discarded")

# 9. Unexpected fields never enter the output.
event = c.extract_event(copy.deepcopy(baseline))
allowed = {
    "event_id", "event_timestamp", "rule_id", "rule_level",
    "rule_description", "agent_id", "agent_name", "manager_name",
    "decoder_name", "rule_groups", "srcip", "srcport", "mitre",
}
assert set(event) == allowed
assert "full_log" not in event
assert "unexpected" not in event
mitre = event["mitre"].obj
assert "unexpected" not in mitre
print("PASS: output restricted to whitelist fields")

print("PASS: STEP330-25A ALL TESTS")
PY
```

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

```bash
python3 - <<'PY'
import copy
import importlib.util

spec = importlib.util.spec_from_file_location(
    "collector_step330_25b",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

baseline = {
    "id": "step330-25b-test",
    "timestamp": "2026-11-19T07:00:00+09:00",
    "rule": {
        "id": 100001,
        "level": 10,
        "description": "normal",
        "groups": ["normal"],
        "mitre": {},
    },
    "agent": {"id": "001", "name": "agent"},
    "manager": {"name": "manager"},
    "decoder": {"name": "decoder"},
    "data": {},
}

# 1. Oversized description is bounded.
test = copy.deepcopy(baseline)
test["rule"]["description"] = "A" * 900_000
event = c.extract_event(test)
assert event is not None
assert len(event["rule_description"]) == 4096
print("PASS: oversized description bounded")

# 2. Large group list is bounded.
test = copy.deepcopy(baseline)
test["rule"]["groups"] = ["G" + str(i) for i in range(100_000)]
event = c.extract_event(test)
assert len(event["rule_groups"]) == 64
print("PASS: large group list bounded to 64 items")

# 3. Oversized MITRE arrays are bounded by key.
test = copy.deepcopy(baseline)
test["rule"]["mitre"] = {
    "id": ["I"] * 1000,
    "tactic": ["T"] * 1000,
    "technique": ["X"] * 1000,
}
event = c.extract_event(test)
mitre = event["mitre"].obj
assert len(mitre["id"]) == 32
assert len(mitre["tactic"]) == 16
assert len(mitre["technique"]) == 32
print("PASS: MITRE arrays bounded by key")

# 4. Unexpected deeply nested data is ignored.
test = copy.deepcopy(baseline)
test["unexpected"] = {
    "level1": {
        "level2": {
            "level3": ["secret"] * 1000
        }
    }
}
test["data"] = {
    "srcip": {"nested": "192.0.2.1"},
    "srcport": ["443"],
    "unexpected": {"secret": "value"},
}
event = c.extract_event(test)
assert event is not None
assert event["srcip"] is None
assert event["srcport"] is None
assert set(event) == {
    "event_id", "event_timestamp", "rule_id", "rule_level",
    "rule_description", "agent_id", "agent_name", "manager_name",
    "decoder_name", "rule_groups", "srcip", "srcport", "mitre",
}
print("PASS: nested unexpected structures ignored")

# 5. Wrong types in optional fields do not crash extraction.
test = copy.deepcopy(baseline)
test["rule"]["description"] = {"text": "unexpected"}
test["rule"]["groups"] = {"not": "a list"}
test["rule"]["mitre"] = ["not", "a", "dict"]
test["data"] = "not a dictionary"
event = c.extract_event(test)
assert event is not None
assert event["rule_description"] is None
assert event["rule_groups"] == []
assert event["srcip"] is None
assert event["srcport"] is None
assert event["mitre"].obj == {}
print("PASS: malformed optional fields safely discarded")

# 6. Non-string MITRE entries are discarded.
test = copy.deepcopy(baseline)
test["rule"]["mitre"] = {
    "id": [None, 123, "T1110"],
    "tactic": {"unexpected": "object"},
    "technique": ["Valid", False],
}
event = c.extract_event(test)
mitre = event["mitre"].obj
assert mitre["id"] == ["T1110"]
assert "tactic" not in mitre
assert mitre["technique"] == ["Valid"]
print("PASS: malformed MITRE entries filtered")

print("PASS: STEP330-25B ALL TESTS")
PY
```

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

```bash
cat > /tmp/test_step330_26b.py <<'PY'
import copy
import importlib.util
from unittest.mock import MagicMock

spec = importlib.util.spec_from_file_location(
    "collector_step330_26b",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

alert = {
    "id": "step330-26b-test",
    "timestamp": "2026-11-19T07:00:00+09:00",
    "rule": {
        "id": 100001,
        "level": 10,
        "description": "test",
        "groups": [],
        "mitre": {},
    },
    "agent": {"id": "001", "name": "agent"},
    "manager": {"name": "manager"},
    "decoder": {"name": "decoder"},
    "data": {},
}

import json
line = (json.dumps(alert) + "\n").encode()

# 1. DB failure must propagate to run() caller.
connection = MagicMock()
connection.transaction.side_effect = RuntimeError("simulated DB failure")

try:
    c.process_line(connection, line)
except RuntimeError as error:
    assert str(error) == "simulated DB failure"
else:
    raise AssertionError("DB failure was swallowed")

print("PASS: DB failure propagates")

# 2. Duplicate event is handled without propagating.
connection = MagicMock()
duplicate = c.psycopg.errors.UniqueViolation("duplicate")
duplicate.sqlstate = "23505"
connection.transaction.side_effect = duplicate

c.process_line(connection, line)
print("PASS: duplicate event handled")

# 3. Non-duplicate database errors must propagate.
connection = MagicMock()
other_error = c.psycopg.errors.InsufficientPrivilege("permission denied")
connection.transaction.side_effect = other_error

try:
    c.process_line(connection, line)
except c.psycopg.errors.InsufficientPrivilege:
    pass
else:
    raise AssertionError("Non-duplicate DB error was swallowed")

print("PASS: non-duplicate DB error propagates")

# 4. Invalid JSON must not reach the database.
connection = MagicMock()
c.process_line(connection, b'{"broken":')
connection.execute.assert_not_called()
print("PASS: invalid JSON does not reach DB")

# 5. Invalid alert must not reach the database.
connection = MagicMock()
c.process_line(connection, b'{"id":"invalid"}\n')
connection.execute.assert_not_called()
print("PASS: invalid alert does not reach DB")

print("PASS: STEP330-26B ALL TESTS")
PY

python3 /tmp/test_step330_26b.py
```

## 7.3 Rewinding to the Start of the Line

Confirm that going back to the start of a failed line reads the same event again, and that after it succeeds the next event can be read.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import tempfile
from pathlib import Path

first = b'{"id":"first"}\n'
second = b'{"id":"second"}\n'

with tempfile.TemporaryDirectory(prefix="step330-26c-") as tmp:
    path = Path(tmp) / "alerts.json"
    path.write_bytes(first + second)

    with path.open("rb") as handle:
        line_start = handle.tell()
        line = handle.readline()

        assert line == first

        # Simulate the run() exception path.
        handle.seek(line_start)
        assert handle.tell() == 0

        # Retry must read the exact same event.
        retry = handle.readline()
        assert retry == first

        # After successful processing, the next event is readable.
        next_line = handle.readline()
        assert next_line == second

        print("PASS: failed event rewound to line_start")
        print("PASS: retry reads identical event")
        print("PASS: subsequent event remains readable")

print("PASS: STEP330-26C ALL TESTS")
PY
```

# Chapter 8: State File Anomalies

## 8.1 Anomalies When Loading the State

Confirm that broken JSON, wrong types, out-of-range numbers and permission errors on reading all lead to refusing to start (`collector state is invalid`), and that only a missing state file is treated as reading from the beginning (`None`).

**Run on: security-core VM 220 (root)**

```bash
cat > /tmp/test_step330_27b.py <<'PY'
import importlib.util
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "collector_step330_27b",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

with tempfile.TemporaryDirectory(prefix="step330-27b-") as tmp:
    state_path = Path(tmp) / "state.json"
    c.STATE_FILE = state_path

    # 1. Valid state.
    state_path.write_text(
        json.dumps({"inode": 12345, "offset": 67890}),
        encoding="utf-8",
    )
    assert c.load_state() == (12345, 67890)
    print("PASS: valid state loaded")

    # 2. Missing state.
    state_path.unlink()
    assert c.load_state() is None
    print("PASS: missing state returns None")

    # 3. Corrupt JSON.
    invalid_documents = [
        "{broken json",
        "[]",
        '"text"',
        "null",
        '{"inode": true, "offset": 10}',
        '{"inode": 123, "offset": false}',
        '{"inode": 0, "offset": 10}',
        '{"inode": 123, "offset": -1}',
        '{"inode": 9223372036854775808, "offset": 10}',
        '{"inode": 123, "offset": 9223372036854775808}',
        '{"inode": "123;DROP", "offset": 10}',
        '{"inode": 123}',
    ]

    for document in invalid_documents:
        state_path.write_text(document, encoding="utf-8")
        try:
            c.load_state()
        except RuntimeError as error:
            assert str(error) == "collector state is invalid"
        else:
            raise AssertionError(
                f"Invalid state accepted: {document!r}"
            )

    print("PASS: malformed and out-of-range states rejected")

    # 4. Simulated permission failure.
    state_path.write_text(
        json.dumps({"inode": 12345, "offset": 67890}),
        encoding="utf-8",
    )
    original_open = Path.open

    def controlled_open(self, *args, **kwargs):
        if self == state_path:
            raise PermissionError("simulated permission failure")
        return original_open(self, *args, **kwargs)

    with patch.object(Path, "open", controlled_open):
        try:
            c.load_state()
        except RuntimeError as error:
            assert str(error) == "collector state is invalid"
        else:
            raise AssertionError("Permission failure was accepted")

    print("PASS: permission failure rejected safely")

print("PASS: STEP330-27B ALL TESTS")
PY

python3 /tmp/test_step330_27b.py
```

## 8.2 Anomalies When Restoring the inode and Position

**Run on: security-core VM 220 (root)**

```bash
cat > /tmp/test_step330_27c.py <<'PY'
import importlib.util
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "collector_step330_27c",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

with tempfile.TemporaryDirectory(prefix="step330-27c-") as tmp:
    root = Path(tmp)
    current = root / "alerts.json"
    state = root / "state.json"

    current.write_bytes(b'{"id":"one"}\n{"id":"two"}\n')

    c.ALERT_FILE = current
    c.ALERT_DIR = root
    c.STATE_FILE = state

    inode = current.stat().st_ino
    size = current.stat().st_size

    # 1. Valid current inode and offset.
    handle, active_inode = c.open_initial_file((inode, 0))
    assert active_inode == inode
    assert handle.tell() == 0
    assert handle.readline() == b'{"id":"one"}\n'
    handle.close()
    print("PASS: valid current inode resumed")

    # 2. Missing previous inode must be refused.
    try:
        c.open_initial_file((inode + 999999, 0))
    except RuntimeError as error:
        assert "cannot be located" in str(error)
    else:
        raise AssertionError("Missing inode was accepted")
    print("PASS: missing previous inode refused")

    # 3. Current file offset beyond EOF must be refused.
    try:
        c.open_initial_file((inode, size + 1))
    except RuntimeError as error:
        assert "exceeds current" in str(error)
    else:
        raise AssertionError("Oversized current offset accepted")
    print("PASS: current offset beyond EOF refused")

    # 4. Different inode with no matching old file must be refused.
    other = root / "other.json"
    other.write_bytes(b'{"id":"other"}\n')
    other_inode = other.stat().st_ino

    try:
        c.open_initial_file((other_inode + 999999, 0))
    except RuntimeError:
        pass
    else:
        raise AssertionError("Unverified inode accepted")
    print("PASS: unverified inode refused")

    # 5. Traversal permission error must propagate.
    original_scandir = c.os.scandir

    def failing_scandir(path):
        if Path(path) == root:
            raise PermissionError("simulated traversal failure")
        return original_scandir(path)

    with patch.object(c.os, "scandir", failing_scandir):
        try:
            c.find_inode_file(999999999)
        except PermissionError:
            pass
        else:
            raise AssertionError("Traversal error was swallowed")

    print("PASS: traversal permission error propagated")

print("PASS: STEP330-27C ALL TESTS")
PY

python3 /tmp/test_step330_27c.py
```

Permission errors while searching directories are not swallowed and lead to refusing to start. (This confirms that the same path that kept production from starting in Part 5 now stops correctly.)

# Chapter 9: Failures When Saving the State, and a File Descriptor Fix

## 9.1 Failures Partway Through Saving

`save_state()` creates a temporary file in the same directory, sets its permissions to `600`, writes it, calls `fsync()`, replaces the target with `os.replace()`, and finally calls `fsync()` on the directory. Check whether the old state file remains when it fails partway.

**Run on: security-core VM 220 (root)**

```bash
cat > /tmp/test_step330_28b.py <<'PY'
import importlib.util
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "collector_step330_28b",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

with tempfile.TemporaryDirectory(prefix="step330-28b-") as tmp:
    root = Path(tmp)
    c.STATE_FILE = root / "state.json"
    state = c.STATE_FILE

    old = {"inode": 111, "offset": 222}
    new = {"inode": 333, "offset": 444}

    # 1. Normal save and JSON integrity.
    c.save_state(new["inode"], new["offset"])
    assert json.loads(state.read_text()) == new
    print("PASS: normal save and JSON integrity")

    # 2. Temporary file permissions and no leftovers.
    assert state.stat().st_mode & 0o777 == 0o600
    assert list(root.glob(".state-*")) == []
    print("PASS: mode 600 and no temporary leftovers")

    # Prepare an existing state for failure tests.
    state.write_text(json.dumps(old), encoding="utf-8")

    # 3. File fsync failure: old state must remain.
    original_fsync = os.fsync
    calls = {"count": 0}

    def fail_first_fsync(fd):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("simulated file fsync failure")
        return original_fsync(fd)

    with patch.object(c.os, "fsync", fail_first_fsync):
        try:
            c.save_state(new["inode"], new["offset"])
        except OSError:
            pass
        else:
            raise AssertionError("fsync failure was not propagated")

    assert json.loads(state.read_text()) == old
    assert list(root.glob(".state-*")) == []
    print("PASS: file fsync failure preserves old state")

    # 4. os.replace failure: old state must remain.
    with patch.object(
        c.os,
        "replace",
        side_effect=OSError("simulated replace failure"),
    ):
        try:
            c.save_state(new["inode"], new["offset"])
        except OSError:
            pass
        else:
            raise AssertionError("replace failure was not propagated")

    assert json.loads(state.read_text()) == old
    assert list(root.glob(".state-*")) == []
    print("PASS: replace failure preserves old state")

    # 5. Directory fsync failure happens after replacement.
    calls = {"count": 0}

    def fail_second_fsync(fd):
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("simulated directory fsync failure")
        return original_fsync(fd)

    with patch.object(c.os, "fsync", fail_second_fsync):
        try:
            c.save_state(new["inode"], new["offset"])
        except OSError:
            pass
        else:
            raise AssertionError("directory fsync failure was not propagated")

    # Replacement already happened; new JSON should be visible.
    assert json.loads(state.read_text()) == new
    assert list(root.glob(".state-*")) == []
    print("PASS: directory fsync failure propagated after replacement")
    print("INFO: replacement is visible; crash durability is not guaranteed")

print("PASS: STEP330-28B ALL TESTS")
PY

python3 /tmp/test_step330_28b.py
```

| Where it failed | Result |
|---|---|
| File `fsync()` | The old state remains |
| `os.replace()` | The old state remains |
| Directory `fsync()` | Replaced with the new state (durability on power loss is not guaranteed) |

In every case, no temporary file is left behind.

## 9.2 Checking That File Descriptors Are Released

Check whether the temporary file opened by `mkstemp()` is closed even when setting the permissions (`fchmod()`) fails.

**Run on: security-core VM 220 (root)**

```bash
cat > /tmp/test_step330_28c.py <<'PY'
import importlib.util
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "collector_step330_28c",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

with tempfile.TemporaryDirectory(prefix="step330-28c-") as tmp:
    c.STATE_FILE = Path(tmp) / "state.json"

    original_mkstemp = tempfile.mkstemp
    captured = {}

    def capture_mkstemp(*args, **kwargs):
        fd, path = original_mkstemp(*args, **kwargs)
        captured["fd"] = fd
        captured["path"] = path
        return fd, path

    with patch.object(c.tempfile, "mkstemp", capture_mkstemp):
        with patch.object(
            c.os,
            "fchmod",
            side_effect=OSError("simulated fchmod failure"),
        ):
            try:
                c.save_state(12345, 67890)
            except OSError:
                pass
            else:
                raise AssertionError("fchmod failure was not propagated")

    # Check whether the descriptor was closed.
    try:
        os.fstat(captured["fd"])
    except OSError:
        print("PASS: descriptor closed after fchmod failure")
    else:
        os.close(captured["fd"])
        print("FAIL: descriptor leaked after fchmod failure")

    assert not Path(captured["path"]).exists()
    print("PASS: temporary file removed after fchmod failure")

print("PASS: STEP330-28C TEST COMPLETED")
PY

python3 /tmp/test_step330_28c.py
```

At build time, `FAIL: descriptor leaked after fchmod failure` was shown. The temporary file is deleted, but when `fchmod()` fails the file descriptor is left open. This is fixed in the next section.

## 9.3 The Fix and a Backup

Change it so that the file descriptor is handed to a file object with `os.fdopen()` and `fchmod()` is done inside that `with`. Even if `fchmod()` fails, the file is closed when leaving the `with`.

First back up the production file.

**Run on: security-core VM 220 (root)**

```bash
cp -a /usr/local/lib/wazuh-collector/collector.py \
  /usr/local/lib/wazuh-collector/collector.py.backup-before-step330-28d-20261119

sha256sum \
  /usr/local/lib/wazuh-collector/collector.py \
  /usr/local/lib/wazuh-collector/collector.py.backup-before-step330-28d-20261119
```

Confirm that the two hashes are the same (`df4a9ff6...` at build time).

## 9.4 Testing the Fix on a Temporary Copy

Rewrite the production code into a temporary copy and confirm that no file descriptor leaks.

**Run on: security-core VM 220 (root)**

```bash
cat > /tmp/test_step330_28d.py <<'PY'
import importlib.util
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

source = Path("/usr/local/lib/wazuh-collector/collector.py")
patched = Path("/tmp/collector_step330_28d.py")

code = source.read_text(encoding="utf-8")

old = '''        os.fchmod(fd, 0o600)

        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(
                {"inode": inode, "offset": offset},
                output,
            )
            output.flush()
            os.fsync(output.fileno())
'''

new = '''        with os.fdopen(fd, "w", encoding="utf-8") as output:
            os.fchmod(output.fileno(), 0o600)
            json.dump(
                {"inode": inode, "offset": offset},
                output,
            )
            output.flush()
            os.fsync(output.fileno())
'''

assert code.count(old) == 1, "Target code block mismatch"
patched.write_text(code.replace(old, new), encoding="utf-8")

spec = importlib.util.spec_from_file_location(
    "collector_step330_28d",
    patched,
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

with tempfile.TemporaryDirectory(prefix="step330-28d-") as tmp:
    c.STATE_FILE = Path(tmp) / "state.json"

    before = set(os.listdir("/proc/self/fd"))

    with patch.object(
        c.os,
        "fchmod",
        side_effect=OSError("simulated fchmod failure"),
    ):
        try:
            c.save_state(12345, 67890)
        except OSError:
            pass
        else:
            raise AssertionError("fchmod failure was not propagated")

    after = set(os.listdir("/proc/self/fd"))

    assert before == after, (
        f"FD leak detected: before={before}, after={after}"
    )
    assert list(Path(tmp).glob(".state-*")) == []

    print("PASS: no FD leak after fchmod failure")
    print("PASS: temporary file removed")

    c.save_state(12345, 67890)
    assert c.STATE_FILE.stat().st_mode & 0o777 == 0o600
    print("PASS: normal save and mode 600")

print("PASS: STEP330-28D ALL TESTS")
PY

python3 /tmp/test_step330_28d.py
```

Then run the test from 9.1 against the fixed temporary copy and confirm that the previous behavior has not changed.

```bash
sed \
  's|/usr/local/lib/wazuh-collector/collector.py|/tmp/collector_step330_28d.py|' \
  /tmp/test_step330_28b.py \
  > /tmp/test_step330_28e.py

python3 /tmp/test_step330_28e.py
```

## 9.5 Checks Before Deploying

**Run on: security-core VM 220 (root)**

```bash
echo "=== SERVICE ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts

echo
echo "=== PRODUCTION HASH ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== STATE METADATA ==="
stat -c 'owner=%U:%G mode=%a size=%s' \
  /var/lib/wazuh-collector/state.json

echo
echo "=== STATE / ALERT FILE CONSISTENCY ==="
python3 - <<'PY'
import json
from pathlib import Path

state_path = Path("/var/lib/wazuh-collector/state.json")
alert_path = Path("/var/ossec/logs/alerts/alerts.json")

state = json.loads(state_path.read_text())
st = alert_path.stat()

print("state_inode:", state["inode"])
print("file_inode:", st.st_ino)
print("state_offset:", state["offset"])
print("file_size:", st.st_size)
print("inode_match:", state["inode"] == st.st_ino)
print("offset_within_file:", 0 <= state["offset"] <= st.st_size)
PY
```

Confirm `inode_match: True` and `offset_within_file: True`.

## 9.6 Deploying the Fix to Production

After checking the hashes of production and the backup, rewrite only the relevant part and replace the file in one step, keeping its owner and permissions.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import os
import tempfile
from pathlib import Path

target = Path("/usr/local/lib/wazuh-collector/collector.py")
backup = Path(
    "/usr/local/lib/wazuh-collector/"
    "collector.py.backup-before-step330-28d-20261119"
)

expected = "df4a9ff6c55767851bf9c9831c1d96862e876a4f030d52aa9e394224e51d0a3e"

import hashlib

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert sha256(target) == expected, "Production file changed unexpectedly"
assert sha256(backup) == expected, "Backup hash mismatch"

old = '''        os.fchmod(fd, 0o600)

        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(
                {"inode": inode, "offset": offset},
                output,
            )
            output.flush()
            os.fsync(output.fileno())
'''

new = '''        with os.fdopen(fd, "w", encoding="utf-8") as output:
            os.fchmod(output.fileno(), 0o600)
            json.dump(
                {"inode": inode, "offset": offset},
                output,
            )
            output.flush()
            os.fsync(output.fileno())
'''

source = target.read_text(encoding="utf-8")
assert source.count(old) == 1, "Target code block mismatch"
updated = source.replace(old, new)

metadata = target.stat()
fd, temporary = tempfile.mkstemp(
    prefix=".collector-step330-28g-",
    dir=str(target.parent),
)

try:
    os.fchown(fd, metadata.st_uid, metadata.st_gid)
    os.fchmod(fd, metadata.st_mode & 0o7777)

    with os.fdopen(fd, "w", encoding="utf-8") as output:
        output.write(updated)
        output.flush()
        os.fsync(output.fileno())

    os.replace(temporary, target)

    directory_fd = os.open(target.parent, os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)

except Exception:
    try:
        os.unlink(temporary)
    except FileNotFoundError:
        pass
    raise

print("PASS: production patch installed")
print("SHA256:", sha256(target))
print("OWNER:", target.stat().st_uid, target.stat().st_gid)
print("MODE:", oct(target.stat().st_mode & 0o7777))
PY

python3 -m py_compile /usr/local/lib/wazuh-collector/collector.py
```

Replace the `expected` value with your environment's production hash (before deployment). At build time, the hash after deployment was `a2015974...`, the owner `root:root` and the permissions `755`.

## 9.7 Checks After Deploying

**Run on: security-core VM 220 (root)**

```bash
echo "=== PRODUCTION DIFF ==="
diff -u \
  /usr/local/lib/wazuh-collector/collector.py.backup-before-step330-28d-20261119 \
  /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== SAVE_STATE ==="
sed -n '249,283p' /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== SERVICE ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts

echo
echo "=== PRODUCTION HASH ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== STATE FILE ==="
stat -c 'owner=%U:%G mode=%a size=%s' \
  /var/lib/wazuh-collector/state.json
```

Confirm that the only difference is one place in `save_state()`.

Finally, load the production code and check the fixed behavior in a temporary directory.

```bash
cat > /tmp/test_step330_28i.py <<'PY'
import importlib.util
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "collector_step330_28i",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

with tempfile.TemporaryDirectory(prefix="step330-28i-") as tmp:
    c.STATE_FILE = Path(tmp) / "state.json"

    c.save_state(12345, 67890)
    assert c.STATE_FILE.stat().st_mode & 0o777 == 0o600
    print("PASS: production save_state normal operation")

    before = set(os.listdir("/proc/self/fd"))

    with patch.object(
        c.os,
        "fchmod",
        side_effect=OSError("simulated fchmod failure"),
    ):
        try:
            c.save_state(12346, 67891)
        except OSError:
            pass
        else:
            raise AssertionError("Expected fchmod failure")

    after = set(os.listdir("/proc/self/fd"))

    assert before == after, (before, after)
    assert list(Path(tmp).glob(".state-*")) == []
    print("PASS: production save_state FD cleanup")
    print("PASS: temporary file cleanup")

print("PASS: STEP330-28I ALL TESTS")
PY

python3 /tmp/test_step330_28i.py
```

> The service has not been restarted at this point. The running Collector process (PID `91473` at build time) keeps running the pre-deployment code until it is restarted. The fixed file is used from the next time the service restarts.

# Chapter 10: Adding Validation of the Values Saved

## 10.1 Checking the Boundaries on the Loading Side

`load_state()` validates the inode and position with `safe_integer()`, but `save_state()` turns whatever values it receives into JSON as is. First check which values are rejected when loading.

**Run on: security-core VM 220 (root)**

```bash
cat > /tmp/test_step330_29b.py <<'PY'
import importlib.util
import json
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "collector_step330_29b",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

with tempfile.TemporaryDirectory(prefix="step330-29b-") as tmp:
    c.STATE_FILE = Path(tmp) / "state.json"

    cases = [
        ("valid", 123, 456, True),
        ("inode_zero", 0, 456, False),
        ("inode_negative", -1, 456, False),
        ("inode_bool", True, 456, False),
        ("offset_negative", 123, -1, False),
        ("offset_bool", 123, False, False),
        ("inode_too_large", 2**63, 456, False),
        ("offset_too_large", 123, 2**63, False),
        ("inode_string", "123", 456, False),
        ("offset_string", 123, "456", False),
        ("inode_none", None, 456, False),
        ("offset_none", 123, None, False),
    ]

    for name, inode, offset, expected_valid in cases:
        c.save_state(inode, offset)

        try:
            loaded = c.load_state()
            actual_valid = loaded is not None
        except RuntimeError:
            loaded = None
            actual_valid = False

        print(
            name,
            "accepted" if actual_valid else "rejected",
            "loaded=", repr(loaded),
        )

        assert actual_valid == expected_valid, (
            name,
            expected_valid,
            actual_valid,
        )

    # Non-JSON-serializable object.
    try:
        c.save_state(object(), 1)
    except TypeError:
        print("PASS: non-serializable inode rejected by JSON")
    else:
        raise AssertionError("non-serializable inode unexpectedly saved")

print("PASS: STEP330-29B ALL TESTS")
PY
```

`safe_integer()` is designed to accept digit-only strings (such as `"123"`) as integers too. So correct the expected results for the two string cases to "accepted" before running it.

```bash
sed -i \
  -e 's/("inode_string", "123", 456, False)/("inode_string", "123", 456, True)/' \
  -e 's/("offset_string", 123, "456", False)/("offset_string", 123, "456", True)/' \
  /tmp/test_step330_29b.py

python3 /tmp/test_step330_29b.py
```

When loading, 0, negative numbers, booleans, values above the limit and `None` were rejected.

## 10.2 Reproducing the Problem

If an invalid value is saved, it replaces a valid state file, and the next startup rejects it when loading, so the Collector stops. Check this with the current `save_state()`.

**Run on: security-core VM 220 (root)**

```bash
cat > /tmp/test_step330_29d.py <<'PY'
import importlib.util
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "collector_step330_29d",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

with tempfile.TemporaryDirectory(prefix="step330-29d-") as tmp:
    root = Path(tmp)
    c.STATE_FILE = root / "state.json"

    c.save_state(123, 456)
    print("baseline:", c.load_state())

    for name, inode, offset in [
        ("negative_inode", -1, 456),
        ("boolean_inode", True, 456),
        ("negative_offset", 123, -1),
        ("boolean_offset", 123, True),
        ("string_inode", "123", 456),
    ]:
        try:
            c.save_state(inode, offset)
            print(name, "SAVED", "state=", c.STATE_FILE.read_text())
        except Exception as error:
            print(name, "REJECTED", type(error).__name__)

    print("temporary_files:", list(root.glob(".state-*")))

print("STEP330-29D REPRODUCTION COMPLETED")
PY

python3 /tmp/test_step330_29d.py
```

At build time, all five became `SAVED`.

## 10.3 Testing the Fix on a Temporary Copy

At the start of `save_state()`, accept only integers from `1` to `2^63-1` for the inode and from `0` to `2^63-1` for the position, and raise `ValueError` for anything else before creating the temporary file. When saving, digit strings are also rejected.

**Run on: security-core VM 220 (root)**

```bash
cat > /tmp/test_step330_29e.py <<'PY'
import importlib.util
import tempfile
from pathlib import Path

source = Path("/usr/local/lib/wazuh-collector/collector.py")
patched = Path("/tmp/collector_step330_29e.py")

code = source.read_text(encoding="utf-8")

old = '''def save_state(inode, offset):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
'''

new = '''def save_state(inode, offset):
    if (
        isinstance(inode, bool)
        or not isinstance(inode, int)
        or not 1 <= inode <= 9223372036854775807
    ):
        raise ValueError("invalid state inode")

    if (
        isinstance(offset, bool)
        or not isinstance(offset, int)
        or not 0 <= offset <= 9223372036854775807
    ):
        raise ValueError("invalid state offset")

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
'''

assert code.count(old) == 1
patched.write_text(code.replace(old, new), encoding="utf-8")

spec = importlib.util.spec_from_file_location(
    "collector_step330_29e",
    patched,
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

with tempfile.TemporaryDirectory(prefix="step330-29e-") as tmp:
    root = Path(tmp)
    c.STATE_FILE = root / "state.json"

    c.save_state(123, 456)
    original = c.STATE_FILE.read_text()
    assert c.load_state() == (123, 456)
    print("PASS: valid integer state")

    invalid = [
        ("negative_inode", -1, 456),
        ("zero_inode", 0, 456),
        ("boolean_inode", True, 456),
        ("string_inode", "123", 456),
        ("none_inode", None, 456),
        ("large_inode", 2**63, 456),
        ("negative_offset", 123, -1),
        ("boolean_offset", 123, False),
        ("string_offset", 123, "456"),
        ("none_offset", 123, None),
        ("large_offset", 123, 2**63),
    ]

    for name, inode, offset in invalid:
        try:
            c.save_state(inode, offset)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{name}: invalid value accepted")

        assert c.STATE_FILE.read_text() == original, (
            f"{name}: existing state changed"
        )
        assert list(root.glob(".state-*")) == [], (
            f"{name}: temporary file remains"
        )
        print("PASS:", name, "rejected; old state preserved")

    c.save_state(1, 0)
    assert c.load_state() == (1, 0)
    c.save_state(2**63 - 1, 2**63 - 1)
    assert c.load_state() == (2**63 - 1, 2**63 - 1)
    print("PASS: integer boundary values")

print("PASS: STEP330-29E ALL TESTS")
PY

python3 /tmp/test_step330_29e.py
```

Then, with the same temporary copy, confirm that saving can be retried after a failure.

```bash
cat > /tmp/test_step330_29f.py <<'PY'
import importlib.util
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "collector_step330_29f",
    "/tmp/collector_step330_29e.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

with tempfile.TemporaryDirectory(prefix="step330-29f-") as tmp:
    root = Path(tmp)
    c.STATE_FILE = root / "state.json"

    old = {"inode": 100, "offset": 200}
    new = {"inode": 300, "offset": 400}

    c.save_state(old["inode"], old["offset"])

    # 1. os.replace failure, followed by retry.
    with patch.object(
        c.os,
        "replace",
        side_effect=OSError("simulated replace failure"),
    ):
        try:
            c.save_state(new["inode"], new["offset"])
        except OSError:
            pass
        else:
            raise AssertionError("replace failure not propagated")

    assert json.loads(c.STATE_FILE.read_text()) == old
    assert list(root.glob(".state-*")) == []
    print("PASS: replace failure preserves old state")

    c.save_state(new["inode"], new["offset"])
    assert json.loads(c.STATE_FILE.read_text()) == new
    print("PASS: retry after replace failure")

    # 2. File fsync failure, followed by retry.
    c.save_state(old["inode"], old["offset"])
    original_fsync = os.fsync
    calls = {"count": 0}

    def fail_first_fsync(fd):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("simulated file fsync failure")
        return original_fsync(fd)

    with patch.object(c.os, "fsync", fail_first_fsync):
        try:
            c.save_state(new["inode"], new["offset"])
        except OSError:
            pass
        else:
            raise AssertionError("fsync failure not propagated")

    assert json.loads(c.STATE_FILE.read_text()) == old
    assert list(root.glob(".state-*")) == []
    print("PASS: fsync failure preserves old state")

    c.save_state(new["inode"], new["offset"])
    assert json.loads(c.STATE_FILE.read_text()) == new
    print("PASS: retry after fsync failure")

print("PASS: STEP330-29F ALL TESTS")
PY

python3 /tmp/test_step330_29f.py
```

## 10.4 Backup and Checks Before Deploying

**Run on: security-core VM 220 (root)**

```bash
cp -a /usr/local/lib/wazuh-collector/collector.py \
  /usr/local/lib/wazuh-collector/collector.py.backup-before-step330-29g-20261119

echo "=== HASH ==="
sha256sum \
  /usr/local/lib/wazuh-collector/collector.py \
  /usr/local/lib/wazuh-collector/collector.py.backup-before-step330-29g-20261119

echo
echo "=== SERVICE ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts

echo
echo "=== STATE ==="
stat -c 'owner=%U:%G mode=%a size=%s' \
  /var/lib/wazuh-collector/state.json

python3 - <<'PY'
import json
from pathlib import Path

state = json.loads(
    Path("/var/lib/wazuh-collector/state.json").read_text()
)
st = Path("/var/ossec/logs/alerts/alerts.json").stat()

print("state_inode:", state["inode"])
print("file_inode:", st.st_ino)
print("state_offset:", state["offset"])
print("file_size:", st.st_size)
print("inode_match:", state["inode"] == st.st_ino)
print("offset_within_file:", 0 <= state["offset"] <= st.st_size)
PY
```

## 10.5 Deploying to Production

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import hashlib
import os
import tempfile
from pathlib import Path

target = Path("/usr/local/lib/wazuh-collector/collector.py")
backup = Path(
    "/usr/local/lib/wazuh-collector/"
    "collector.py.backup-before-step330-29g-20261119"
)

expected = "a20159748087c4c26df7103cc5c5314f67a41b5cf56a98c2afea98ce4724bcb3"

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert sha256(target) == expected, "Production file changed"
assert sha256(backup) == expected, "Backup mismatch"

old = '''def save_state(inode, offset):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
'''

new = '''def save_state(inode, offset):
    if (
        isinstance(inode, bool)
        or not isinstance(inode, int)
        or not 1 <= inode <= 9223372036854775807
    ):
        raise ValueError("invalid state inode")

    if (
        isinstance(offset, bool)
        or not isinstance(offset, int)
        or not 0 <= offset <= 9223372036854775807
    ):
        raise ValueError("invalid state offset")

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
'''

source = target.read_text(encoding="utf-8")
assert source.count(old) == 1, "Target block mismatch"

updated = source.replace(old, new)
metadata = target.stat()

fd, temporary = tempfile.mkstemp(
    prefix=".collector-step330-29h-",
    dir=str(target.parent),
)

try:
    os.fchown(fd, metadata.st_uid, metadata.st_gid)
    os.fchmod(fd, metadata.st_mode & 0o7777)

    with os.fdopen(fd, "w", encoding="utf-8") as output:
        output.write(updated)
        output.flush()
        os.fsync(output.fileno())

    os.replace(temporary, target)

    directory_fd = os.open(target.parent, os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)

except Exception:
    try:
        os.unlink(temporary)
    except FileNotFoundError:
        pass
    raise

print("PASS: production patch installed")
print("SHA256:", sha256(target))
print("OWNER:", target.stat().st_uid, target.stat().st_gid)
print("MODE:", oct(target.stat().st_mode & 0o7777))
PY

python3 -m py_compile /usr/local/lib/wazuh-collector/collector.py
```

At build time the hash after deployment was `faf2c203...`. Here too the service is not restarted.

## 10.6 Checking Behavior with the Production Code

**Run on: security-core VM 220 (root)**

```bash
cat > /tmp/test_step330_29i.py <<'PY'
import importlib.util
import json
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "collector_step330_29i",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

with tempfile.TemporaryDirectory(prefix="step330-29i-") as tmp:
    root = Path(tmp)
    c.STATE_FILE = root / "state.json"

    # Valid state
    c.save_state(100, 200)
    assert json.loads(c.STATE_FILE.read_text()) == {
        "inode": 100,
        "offset": 200,
    }
    assert (c.STATE_FILE.stat().st_mode & 0o777) == 0o600
    print("PASS: valid state saved with mode 600")

    # Invalid inode and offset values
    invalid_cases = [
        (0, 0),
        (-1, 0),
        (True, 0),
        ("100", 0),
        (None, 0),
        (9223372036854775808, 0),
        (100, -1),
        (100, True),
        (100, "200"),
        (100, None),
        (100, 9223372036854775808),
    ]

    for inode, offset in invalid_cases:
        before = c.STATE_FILE.read_bytes()
        try:
            c.save_state(inode, offset)
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"Invalid state accepted: {inode!r}, {offset!r}"
            )

        assert c.STATE_FILE.read_bytes() == before

    assert json.loads(c.STATE_FILE.read_text()) == {
        "inode": 100,
        "offset": 200,
    }
    assert list(root.iterdir()) == [c.STATE_FILE]
    print("PASS: invalid values rejected; old state preserved; no temp files")

    # Boundary values
    c.save_state(1, 0)
    assert json.loads(c.STATE_FILE.read_text()) == {
        "inode": 1,
        "offset": 0,
    }

    c.save_state(9223372036854775807, 9223372036854775807)
    assert json.loads(c.STATE_FILE.read_text()) == {
        "inode": 9223372036854775807,
        "offset": 9223372036854775807,
    }
    print("PASS: minimum and maximum boundaries")

print("PASS: STEP330-29I ALL TESTS")
PY

python3 /tmp/test_step330_29i.py
```

# Chapter 11: Activating the Fixes (Restart)

## 11.1 Checking the Diff and Running State

**Run on: security-core VM 220 (root)**

```bash
echo "=== PRODUCTION DIFF ==="
diff -u \
  /usr/local/lib/wazuh-collector/collector.py.backup-before-step330-29g-20261119 \
  /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== SYNTAX ==="
python3 -m py_compile /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== PRODUCTION HASH ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== SERVICE ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p ExecMainStatus

echo
echo "=== STATE INTEGRITY ==="
python3 - <<'PY'
import json
from pathlib import Path

state_path = Path("/var/lib/wazuh-collector/state.json")
alerts_path = Path("/var/ossec/logs/alerts/alerts.json")

state = json.loads(state_path.read_text())
st = alerts_path.stat()

print("state_owner:", state_path.stat().st_uid, state_path.stat().st_gid)
print("state_mode:", oct(state_path.stat().st_mode & 0o777))
print("state_inode:", state["inode"])
print("file_inode:", st.st_ino)
print("state_offset:", state["offset"])
print("file_size:", st.st_size)
print("inode_match:", state["inode"] == st.st_ino)
print("offset_within_file:", 0 <= state["offset"] <= st.st_size)
PY
```

Confirm that the only difference is the input validation in `save_state()` (14 lines). The fixes from Chapters 9 and 10 are only in the file on disk; the running process (PID `91473` at build time) still uses the old code.

## 11.2 Restarting

Just before the restart, record the service state, that the position in the state file matches `alerts.json`, and the production hash (`faf2c203...` at build time) (you can use the output from 11.1).

**Run on: security-core VM 220 (root)**

```bash
systemctl restart wazuh-collector
```

## 11.3 Checks After the Restart

**Run on: security-core VM 220 (root)**

```bash
echo "=== SERVICE ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p ExecMainStatus

echo
echo "=== RECENT LOGS ==="
journalctl -u wazuh-collector -n 20 --no-pager

echo
echo "=== PRODUCTION CODE HASH ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== STATE AND ALERT FILE ==="
python3 - <<'PY'
import json
from pathlib import Path

state_path = Path("/var/lib/wazuh-collector/state.json")
alerts_path = Path("/var/ossec/logs/alerts/alerts.json")

state = json.loads(state_path.read_text())
st = alerts_path.stat()

print("state:", state)
print("file_inode:", st.st_ino)
print("file_size:", st.st_size)
print("inode_match:", state["inode"] == st.st_ino)
print("offset_within_file:", 0 <= state["offset"] <= st.st_size)
print("state_owner:", state_path.stat().st_uid, state_path.stat().st_gid)
print("state_mode:", oct(state_path.stat().st_mode & 0o777))
PY
```

At build time it started with the new PID `92423`, showed `Wazuh alert collector starting`, and resumed from the same inode and position as before the restart.

```bash
echo "=== SERVICE ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts

echo
echo "=== LOGS SINCE RESTART ==="
journalctl -u wazuh-collector --since "2026-11-18 23:04:00" --no-pager

echo
echo "=== DATABASE CONNECTION MESSAGES ==="
journalctl -u wazuh-collector --since "2026-11-18 23:04:00" --no-pager \
  | grep -E 'PostgreSQL connection established|ERROR|WARNING|Duplicate alert|Invalid JSON|Alert rejected' \
  || true
```

Set the `--since` time to when you restarted. If `PostgreSQL connection established` appears after a new alert is read, the DB connection is working.

## 11.4 Ingestion and Keeping Up with the Read Position

**Run on: LXC 109 postgresql (root)**

```bash
sudo -u postgres psql -d security_workbench -c "
SELECT
    COUNT(*) AS total_events,
    MAX(ingested_at) AS latest_ingested_at
FROM incident.alert_events;
"
```

At build time the count had increased from 735 to 755.

**Run on: security-core VM 220 (root)**

```bash
echo "=== SERVICE ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p ExecMainStatus

echo
echo "=== STATE AND ALERT FILE ==="
python3 - <<'PY'
import json
from pathlib import Path

state_path = Path("/var/lib/wazuh-collector/state.json")
alerts_path = Path("/var/ossec/logs/alerts/alerts.json")

state = json.loads(state_path.read_text())
st = alerts_path.stat()

print("state:", state)
print("file_inode:", st.st_ino)
print("file_size:", st.st_size)
print("inode_match:", state["inode"] == st.st_ino)
print("offset_within_file:", 0 <= state["offset"] <= st.st_size)
print("state_at_eof:", state["offset"] == st.st_size)
print("state_owner:", state_path.stat().st_uid, state_path.stat().st_gid)
print("state_mode:", oct(state_path.stat().st_mode & 0o777))
PY

echo
echo "=== POST-RESTART WARNINGS / ERRORS ==="
journalctl -u wazuh-collector --since "2026-11-18 23:04:00" --no-pager \
  | grep -Ei 'error|warning|traceback|failed|duplicate|invalid json|alert rejected' \
  || true

echo
echo "=== ACTIVE PROCESS ==="
ps -o pid,uid,gid,etimes,stat,cmd -p "$(systemctl show -p MainPID --value wazuh-collector)"
```

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

```bash
cat > /tmp/test_step330_31d.py <<'PY'
import importlib.util
from contextlib import contextmanager

import psycopg

spec = importlib.util.spec_from_file_location(
    "collector_step330_31d",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class FakeConnection:
    def __init__(self):
        self.ids = set()
        self.calls = 0

    @contextmanager
    def transaction(self):
        yield

    def execute(self, sql, event):
        self.calls += 1
        event_id = event["event_id"]

        if event_id in self.ids:
            raise psycopg.errors.UniqueViolation(
                "duplicate event_id"
            )

        self.ids.add(event_id)


connection = FakeConnection()

event = {
    "event_id": "step330-31d-test-event",
}

# Mock extraction to isolate process_line's DB behavior.
original_extract = c.extract_event
c.extract_event = lambda alert: event

try:
    # First delivery.
    c.process_line(connection, b'{"id":"step330-31d-test-event"}')
    assert connection.ids == {event["event_id"]}
    assert connection.calls == 1
    print("PASS: first insert")

    # Retry after simulated state-save failure.
    c.process_line(connection, b'{"id":"step330-31d-test-event"}')
    assert connection.ids == {event["event_id"]}
    assert connection.calls == 2
    print("PASS: duplicate retry handled")

    # A subsequent different event must still be accepted.
    next_event = {"event_id": "step330-31d-next-event"}
    c.extract_event = lambda alert: next_event

    c.process_line(connection, b'{"id":"step330-31d-next-event"}')
    assert connection.ids == {
        "step330-31d-test-event",
        "step330-31d-next-event",
    }
    assert connection.calls == 3
    print("PASS: subsequent event accepted")

finally:
    c.extract_event = original_extract

print("PASS: STEP330-31D ALL TESTS")
PY

python3 /tmp/test_step330_31d.py
```

## 12.3 A Failed State Save Combined with a Retry

In a temporary directory, reproduce the flow in which the DB insert succeeds, saving the state then fails, and the Collector goes back to the start of the line and processes the same event again.

**Run on: security-core VM 220 (root)**

```bash
cat > /tmp/test_step330_31e.py <<'PY'
import importlib.util
import io
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import psycopg

spec = importlib.util.spec_from_file_location(
    "collector_step330_31e",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class FakeConnection:
    def __init__(self):
        self.ids = set()
        self.insert_count = 0

    @contextmanager
    def transaction(self):
        yield

    def execute(self, sql, event):
        event_id = event["event_id"]

        if event_id in self.ids:
            raise psycopg.errors.UniqueViolation(
                "duplicate event_id"
            )

        self.ids.add(event_id)
        self.insert_count += 1


with tempfile.TemporaryDirectory(
    prefix="step330-31e-"
) as temp_dir:

    # Use a temporary area; do not touch the production state file.
    c.STATE_FILE = Path(temp_dir) / "state.json"

    connection = FakeConnection()
    event = {"event_id": "step330-31e-test-event"}

    original_extract = c.extract_event
    c.extract_event = lambda alert: event

    line = b'{"id":"step330-31e-test-event"}\n'
    stream = io.BytesIO(line)

    try:
        # Create the initial state.
        c.save_state(12345, 0)
        assert c.load_state() == (12345, 0)
        print("PASS: initial state")

        # First DB insert.
        c.process_line(connection, line)
        assert connection.insert_count == 1
        assert len(connection.ids) == 1
        print("PASS: first DB insert")

        # Make the first fsync fail on purpose.
        real_fsync = os.fsync
        fsync_calls = {"count": 0}

        def fail_first_fsync(fd):
            fsync_calls["count"] += 1
            if fsync_calls["count"] == 1:
                raise OSError("simulated fsync failure")
            return real_fsync(fd)

        try:
            with patch.object(c.os, "fsync", fail_first_fsync):
                c.save_state(12345, len(line))
            raise AssertionError("expected fsync failure")
        except OSError:
            pass

        # The old state must be kept.
        assert c.load_state() == (12345, 0)
        print("PASS: failed state save preserves old state")

        # Rewind the read position as the Collector does.
        stream.seek(0)
        assert stream.tell() == 0
        print("PASS: input position rewound")

        # Reprocess the same event. It is skipped as a duplicate.
        retry_line = stream.readline()
        c.process_line(connection, retry_line)

        assert connection.insert_count == 1
        assert len(connection.ids) == 1
        print("PASS: duplicate retry skipped")

        # Saving the state on retry succeeds.
        c.save_state(12345, stream.tell())

        saved = c.load_state()
        assert saved == (12345, len(line))
        print("PASS: state saved after retry")

        # No temporary file must remain.
        leftovers = list(Path(temp_dir).glob(".state-*"))
        assert leftovers == []
        print("PASS: no temporary state files")

    finally:
        c.extract_event = original_extract

print("PASS: STEP330-31E ALL TESTS")
PY

python3 /tmp/test_step330_31e.py
```

| Check | Result |
|---|---|
| Failed state save | The old state remains |
| Rewind to the start of the line | The same event is read again |
| Reprocessing | Treated as a duplicate; still only one row inserted |
| Saving on retry | Succeeds, with no temporary file left |

# Chapter 13: Failed Saves at Rotation and Final Checks

## 13.1 The Production Running State (Reads Only)

**Run on: security-core VM 220 (root)**

```bash
echo "=== SERVICE STATUS ==="
systemctl show wazuh-collector \
  -p ActiveState -p SubState -p MainPID -p NRestarts

echo
echo "=== PRODUCTION CODE HASH ==="
sha256sum /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== STATE AND ALERT FILE ==="
python3 - <<'PY'
import json
import os
from pathlib import Path

state_path = Path("/var/lib/wazuh-collector/state.json")
alert_path = Path("/var/ossec/logs/alerts/alerts.json")

state = json.loads(state_path.read_text())
state_stat = state_path.stat()
alert_stat = alert_path.stat()

print("state_owner_uid:", state_stat.st_uid)
print("state_owner_gid:", state_stat.st_gid)
print("state_mode:", oct(state_stat.st_mode & 0o777))
print("state_inode:", state["inode"])
print("state_offset:", state["offset"])
print("alert_inode:", alert_stat.st_ino)
print("alert_size:", alert_stat.st_size)
print("inode_match:", state["inode"] == alert_stat.st_ino)
print("offset_within_file:", 0 <= state["offset"] <= alert_stat.st_size)
print("state_at_eof:", state["offset"] == alert_stat.st_size)
PY
```

At build time this showed PID `92423`, restart count `0`, and `inode_match`, `offset_within_file` and `state_at_eof` all `True`.

## 13.2 Checking the Rotation Processing

**Run on: security-core VM 220 (root)**

```bash
echo "=== ROTATION FUNCTIONS ==="
grep -n -A45 -B5 -E 'def safe_open_current_alert_file|def open_initial_file|def save_state' \
  /usr/local/lib/wazuh-collector/collector.py

echo
echo "=== ROTATION CALL SITES ==="
grep -n -A55 -B15 -E 'safe_open_current_alert_file|Switched to new alerts.json inode|State save failed during rotation' \
  /usr/local/lib/wazuh-collector/collector.py
```

Rotation is handled in two places: when the end of the file is reached, and while reading an incomplete line. In both, the old file is kept open until saving the new file's state succeeds; if saving fails, the new file is closed and the switch is retried at the next check.

## 13.3 Rotation at End of File with a Failed Save

**Run on: security-core VM 220 (root)**

```bash
cat > /tmp/test_step330_33a.py <<'PY'
import importlib.util
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "collector_step330_33a",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

with tempfile.TemporaryDirectory(prefix="step330-33a-") as tmp:
    root = Path(tmp)
    c.ALERT_FILE = root / "alerts.json"
    c.STATE_FILE = root / "state.json"

    old_path = c.ALERT_FILE
    rotated_path = root / "alerts.json.1"

    old_path.write_bytes(b'{"id":"old-event"}\n')
    old_handle = old_path.open("rb")
    old_inode = old_handle.fileno()
    import os
    old_inode = os.fstat(old_inode).st_ino
    old_offset = old_handle.seek(0, 2)

    c.save_state(old_inode, old_offset)
    assert c.load_state() == (old_inode, old_offset)
    print("PASS: initial old-file state")

    # Simulate rename and creation of a new alerts.json.
    old_path.rename(rotated_path)
    old_path.write_bytes(b'{"id":"new-event"}\n')

    new_inode = old_path.stat().st_ino
    assert new_inode != old_inode
    print("PASS: new inode created")

    original_save_state = c.save_state
    attempts = {"count": 0}

    def fail_once(inode, offset):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise OSError("simulated state save failure")
        return original_save_state(inode, offset)

    c.save_state = fail_once
    active_handle = old_handle
    active_inode = old_inode

    try:
        # First rotation attempt: state save fails.
        new_handle, new_stat = c.safe_open_current_alert_file()
        assert new_handle is not None
        assert new_stat.st_ino == new_inode

        try:
            c.save_state(new_stat.st_ino, 0)
        except OSError:
            new_handle.close()

        assert not active_handle.closed
        assert active_inode == old_inode
        assert c.load_state() == (old_inode, old_offset)
        print("PASS: failed save preserves old handle and state")

        # Second attempt: state save succeeds.
        new_handle, new_stat = c.safe_open_current_alert_file()
        assert new_handle is not None
        assert new_stat.st_ino == new_inode

        c.save_state(new_stat.st_ino, 0)

        active_handle.close()
        active_handle = new_handle
        active_inode = new_stat.st_ino

        assert active_inode == new_inode
        assert c.load_state() == (new_inode, 0)
        print("PASS: retry switches to new inode")

        # Verify new file can be read from offset zero.
        line = active_handle.readline()
        assert line == b'{"id":"new-event"}\n'
        print("PASS: new file starts at offset zero")

        assert attempts["count"] == 2
        print("PASS: exactly one failed save and one successful retry")

    finally:
        c.save_state = original_save_state
        if not active_handle.closed:
            active_handle.close()

print("PASS: STEP330-33A ALL TESTS")
PY

python3 /tmp/test_step330_33a.py
```

## 13.4 Rotation in the Middle of an Incomplete Line with a Failed Save

**Run on: security-core VM 220 (root)**

```bash
cat > /tmp/test_step330_33b.py <<'PY'
import importlib.util
import os
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "collector_step330_33b",
    "/usr/local/lib/wazuh-collector/collector.py",
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

with tempfile.TemporaryDirectory(prefix="step330-33b-") as tmp:
    root = Path(tmp)
    c.ALERT_FILE = root / "alerts.json"
    c.STATE_FILE = root / "state.json"

    old_path = c.ALERT_FILE
    rotated_path = root / "alerts.json.1"

    # Old file contains an incomplete JSON line.
    old_path.write_bytes(b'{"id":"incomplete-old')
    old_handle = old_path.open("rb")
    old_inode = os.fstat(old_handle.fileno()).st_ino

    c.save_state(old_inode, 0)

    status, line, discarding = c.read_alert_line(old_handle)
    assert status == "incomplete"
    assert line is None
    assert not discarding
    line_start = 0
    print("PASS: incomplete line detected")

    # Simulate rotation and creation of a complete new event.
    old_path.rename(rotated_path)
    old_path.write_bytes(b'{"id":"new-event"}\n')
    new_inode = old_path.stat().st_ino

    assert new_inode != old_inode
    print("PASS: rotation detected")

    original_save_state = c.save_state
    attempts = {"count": 0}

    def fail_once(inode, offset):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise OSError("simulated state save failure")
        return original_save_state(inode, offset)

    c.save_state = fail_once
    active_handle = old_handle
    active_inode = old_inode

    try:
        # First attempt: state save fails.
        new_handle, new_stat = c.safe_open_current_alert_file()
        assert new_handle is not None
        assert new_stat.st_ino == new_inode

        try:
            c.save_state(new_stat.st_ino, 0)
        except OSError:
            new_handle.close()
            active_handle.seek(line_start)

        assert not active_handle.closed
        assert active_handle.tell() == line_start
        assert active_inode == old_inode
        assert c.load_state() == (old_inode, 0)
        print("PASS: failure preserves old handle and rewinds")

        # Second attempt: state save succeeds.
        new_handle, new_stat = c.safe_open_current_alert_file()
        assert new_handle is not None
        assert new_stat.st_ino == new_inode

        c.save_state(new_stat.st_ino, 0)

        active_handle.close()
        active_handle = new_handle
        active_inode = new_stat.st_ino

        assert active_inode == new_inode
        assert c.load_state() == (new_inode, 0)
        print("PASS: retry switches to new inode")

        # New file begins with a complete event.
        status, line, discarding = c.read_alert_line(active_handle)
        assert status == "line"
        assert line == b'{"id":"new-event"}\n'
        assert not discarding
        print("PASS: new event read from beginning")

        assert attempts["count"] == 2
        print("PASS: one failed save followed by successful retry")

    finally:
        c.save_state = original_save_state
        if not active_handle.closed:
            active_handle.close()

print("PASS: STEP330-33B ALL TESTS")
PY

python3 /tmp/test_step330_33b.py
```

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

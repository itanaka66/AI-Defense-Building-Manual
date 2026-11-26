---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 58: Hardening Token Handling and the CLI"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 58 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 57 we built token authentication for the API and tested it in an independent environment. Before putting it into production, we examine token handling and the CLI in detail and fix the weaknesses found.

| Found | Fix |
|---|---|
| If the parent directory of the token file is a symbolic link, the file is created at its target and permissions are changed there | open directories in turn with `O_DIRECTORY` and `O_NOFOLLOW`, and create the file through `dir_fd` |
| A literal `\n` was written to the file instead of a newline | write a real newline |
| A non-string element in `scopes` in the DB causes `TypeError` | check first that elements are strings |
| Passing `True` as the expiry is accepted as 1 day | reject `bool` |
| An invalid JSON in `scopes` stops the listing | handle it without stopping the listing |
| A failure partway through writing leaves a partial token file | on failure, remove only that file |

Everything is tested with a temporary DB and temporary files; the production DB and tokens are not touched. The service is not restarted.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: Reading the CLI and Token Handling

## 1.1 The CLI

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API TOKEN CLI SECURITY REVIEW ====="

echo
echo "--- 1. CLI implementation ---"
nl -ba app/cli/api_tokens.py | sed -n '1,300p'

echo
echo "--- 2. CLI entry point ---"
nl -ba app/cli/__init__.py | sed -n '1,160p'

echo
echo "--- 3. Executable wrapper ---"
stat -c '%A %a %U:%G %n' /usr/local/sbin/aidm-api-token
sed -n '1,160p' /usr/local/sbin/aidm-api-token

echo
echo "--- 4. Token-related directory permissions ---"
for p in \
  /root/.local \
  /root/.local/share \
  /root/.local/share/ai-defense-manager \
  /root/.local/share/ai-defense-manager/tokens
do
  if [ -e "$p" ]; then
    stat -c '%A %a %U:%G %n' "$p"
  else
    echo "NOT_PRESENT $p"
  fi
done

echo
echo "--- 5. Token service public functions ---"
grep -n '^def ' app/services/api_tokens.py

echo
echo "TOKEN_VALUES_DISPLAYED=NO"
echo "TOKEN_ISSUED=NO"
echo "TOKEN_REVOKED=NO"
echo "FILES_MODIFIED=NO"
echo "DATABASE_ACCESSED=NO"
```

`O_NOFOLLOW` applied only to the final file, so symbolic links in parent directories could be followed. Also, `os.chmod(directory, 0o700)` could change the permissions of an unintended directory.

## 1.2 Token Handling

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API TOKEN SERVICE SECURITY REVIEW ====="

echo
echo "--- 1. Token service source ---"
nl -ba app/services/api_tokens.py | sed -n '1,260p'

echo
echo "--- 2. Database path configuration ---"
grep -R -n \
  "DB_PATH\|DATABASE_PATH\|ai-defense.db" \
  app/core app/services --include='*.py'

echo
echo "--- 3. CLI and wrapper ownership ---"
stat -c '%A %a %U:%G %n' \
  app/cli \
  app/cli/api_tokens.py \
  app/services/api_tokens.py \
  /usr/local/sbin/aidm-api-token

echo
echo "--- 4. Root home directory permissions ---"
namei -l /root/.local/share/ai-defense-manager/tokens

echo
echo "SOURCE_FILES_MODIFIED=NO"
echo "TOKEN_VALUES_DISPLAYED=NO"
echo "TOKEN_ISSUED=NO"
echo "TOKEN_REVOKED=NO"
echo "DATABASE_CHANGED=NO"
```

We confirmed random values equivalent to 256 bits, storing only SHA-256 hashes, `hmac.compare_digest`, checks of scope/expiry/revocation, not showing secret values in listings, and rejecting scopes other than `read` and `analyze`. The CLI itself and the wrapper are owned by root, and the wrapper is `700`.

# Chapter 2: Fixing How the Token File Is Written

## 2.1 Testing the Current Method

Only dummy values are written to a temporary directory.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN FILE WRITER ISOLATED SECURITY TEST ====="

./venv/bin/python - <<'PY'
import os
import stat
import tempfile
from pathlib import Path

from app.cli.api_tokens import _write_token_file

with tempfile.TemporaryDirectory(prefix="aidm-token-file-test-") as tmp:
    root = Path(tmp)
    results = []

    def check(name, condition):
        results.append(bool(condition))
        print(f"{name}={'PASS' if condition else 'FAIL'}")

    # 1. Normal creation
    normal_dir = root / "normal"
    normal_file = normal_dir / "token.txt"
    _write_token_file("dummy.token-secret", normal_file)

    mode = stat.S_IMODE(normal_file.stat().st_mode)
    dir_mode = stat.S_IMODE(normal_dir.stat().st_mode)

    check("NORMAL_FILE_CREATED", normal_file.is_file())
    check("NORMAL_FILE_MODE_0600", mode == 0o600)
    check("NORMAL_DIR_MODE_0700", dir_mode == 0o700)

    # 2. Existing file must not be overwritten
    existing_result = False
    try:
        _write_token_file("replacement", normal_file)
    except FileExistsError:
        existing_result = normal_file.read_text() == "dummy.token-secret\n"

    check("EXISTING_FILE_NOT_OVERWRITTEN", existing_result)

    # 3. Final-component symlink must not be followed
    target = root / "target.txt"
    target.write_text("unchanged")
    link = root / "linked-token.txt"
    link.symlink_to(target)

    symlink_result = False
    try:
        _write_token_file("replacement", link)
    except (FileExistsError, OSError):
        symlink_result = (
            link.is_symlink()
            and target.read_text() == "unchanged"
        )

    check("FINAL_SYMLINK_NOT_FOLLOWED", symlink_result)

    # 4. Parent-component symlink behavior (diagnostic)
    real_parent = root / "real-parent"
    real_parent.mkdir()
    linked_parent = root / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)

    parent_result = "NOT_TESTED"
    try:
        _write_token_file("dummy", linked_parent / "token.txt")
        parent_result = "FOLLOWED"
    except Exception as exc:
        parent_result = type(exc).__name__

    print(f"PARENT_SYMLINK_BEHAVIOR={parent_result}")

    # 5. Directory outside root ownership is not tested by chown;
    # inspect current effective ownership only.
    print(f"TEST_PROCESS_EUID={os.geteuid()}")

    print(f"PASS_COUNT={sum(results)}")
    print(f"FAIL_COUNT={len(results) - sum(results)}")

print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("PRODUCTION_TOKEN_REVOKED=NO")
print("PRODUCTION_FILES_MODIFIED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

`PARENT_SYMLINK_BEHAVIOR=FOLLOWED`; that is, we confirmed that if the parent directory is a symbolic link, the token file is created at its target.

## 2.2 Testing a Safe Method with Temporary Code

The production token location and DB are not touched.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: SAFE TOKEN DIRECTORY WALK PROTOTYPE ====="

./venv/bin/python - <<'PY'
import os
import stat
import tempfile
from pathlib import Path

BASE_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
FILE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW

def safe_write(token: str, output: Path):
    if not output.is_absolute() or ".." in output.parts:
        raise ValueError("Absolute path without '..' is required")

    parts = output.parts[1:]
    if not parts:
        raise ValueError("Output file path is required")

    fd = os.open("/", BASE_FLAGS)
    try:
        for component in parts[:-1]:
            try:
                next_fd = os.open(
                    component, BASE_FLAGS, dir_fd=fd
                )
            except FileNotFoundError:
                os.mkdir(component, 0o700, dir_fd=fd)
                next_fd = os.open(
                    component, BASE_FLAGS, dir_fd=fd
                )

            info = os.fstat(next_fd)
            if not stat.S_ISDIR(info.st_mode):
                os.close(next_fd)
                raise PermissionError("Path component is not a directory")
            if info.st_uid != 0 or stat.S_IMODE(info.st_mode) & 0o077:
                os.close(next_fd)
                raise PermissionError("Directory ownership or mode is unsafe")

            os.close(fd)
            fd = next_fd

        file_fd = os.open(
            parts[-1], FILE_FLAGS, 0o600, dir_fd=fd
        )
        try:
            os.fchmod(file_fd, 0o600)
            with os.fdopen(file_fd, "w", encoding="ascii") as stream:
                file_fd = -1
                stream.write(token + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            if file_fd >= 0:
                os.close(file_fd)
        os.fsync(fd)
    finally:
        os.close(fd)

with tempfile.TemporaryDirectory(
    prefix="aidm-safe-walk-", dir="/root"
) as tmp:
    root = Path(tmp)
    results = []

    def check(name, condition):
        results.append(bool(condition))
        print(f"{name}={'PASS' if condition else 'FAIL'}")

    # Normal creation
    target = root / "a" / "b" / "token.txt"
    safe_write("dummy.secret", target)
    check("NORMAL_CREATE", target.read_text() == "dummy.secret\n")
    check("FILE_MODE_0600", stat.S_IMODE(target.stat().st_mode) == 0o600)
    check("DIR_MODE_0700", stat.S_IMODE(target.parent.stat().st_mode) == 0o700)

    # Parent symlink must be rejected
    real = root / "real"
    real.mkdir()
    link = root / "link"
    link.symlink_to(real, target_is_directory=True)
    rejected = False
    try:
        safe_write("dummy", link / "token.txt")
    except OSError:
        rejected = True
    check("PARENT_SYMLINK_REJECTED", rejected)
    check("LINK_TARGET_UNCHANGED", not (real / "token.txt").exists())

    # Existing final file must not be overwritten
    existing_rejected = False
    try:
        safe_write("replacement", target)
    except FileExistsError:
        existing_rejected = target.read_text() == "dummy.secret\n"
    check("EXISTING_FILE_PROTECTED", existing_rejected)

    # Parent directory permissions must not be changed
    shared = root / "shared"
    shared.mkdir(mode=0o700)
    os.chmod(shared, 0o700)
    before = stat.S_IMODE(shared.stat().st_mode)
    safe_write("dummy", shared / "another-token.txt")
    after = stat.S_IMODE(shared.stat().st_mode)
    check("EXISTING_DIR_MODE_UNCHANGED", before == after)

    print(f"PASS_COUNT={sum(results)}")
    print(f"FAIL_COUNT={len(results) - sum(results)}")

print("PRODUCTION_FILES_MODIFIED=NO")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

All 7 passed (rejecting symbolic links in parents and the final file, not overwriting existing files, new directories `0700`, files `0600`, not changing permissions of existing directories).

## 2.3 Integrating into the CLI

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN CLI SAFE WRITER PATCH ====="

BACKUP_DIR="/var/backups/ai-defense-manager/token-cli-hardening-20261124"
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

cp -a app/cli/api_tokens.py "$BACKUP_DIR/api_tokens.py.before"
sha256sum app/cli/api_tokens.py > "$BACKUP_DIR/SHA256.before"
chmod 600 "$BACKUP_DIR/api_tokens.py.before" "$BACKUP_DIR/SHA256.before"

./venv/bin/python - <<'PY'
from pathlib import Path

path = Path("app/cli/api_tokens.py")
source = path.read_text()

start = source.index("def _write_token_file(")
end = source.index("\n\ndef main():", start)

replacement = '''def _write_token_file(token: str, output: Path) -> None:
    if not output.is_absolute() or ".." in output.parts:
        raise ValueError("Token output path must be absolute and normalized")

    parts = output.parts[1:]
    if not parts:
        raise ValueError("Token output file path is required")

    directory_fd = os.open(
        "/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    )

    try:
        for component in parts[:-1]:
            try:
                next_fd = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory_fd,
                )
            except FileNotFoundError:
                os.mkdir(component, 0o700, dir_fd=directory_fd)
                next_fd = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory_fd,
                )

            info = os.fstat(next_fd)
            if not stat.S_ISDIR(info.st_mode):
                os.close(next_fd)
                raise PermissionError("Token path component is not a directory")
            if info.st_uid != 0 or stat.S_IMODE(info.st_mode) & 0o077:
                os.close(next_fd)
                raise PermissionError(
                    "Token directory must be root-owned and inaccessible to group/others"
                )

            os.close(directory_fd)
            directory_fd = next_fd

        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        file_fd = os.open(
            parts[-1], flags, 0o600, dir_fd=directory_fd
        )

        try:
            os.fchmod(file_fd, 0o600)
            with os.fdopen(file_fd, "w", encoding="ascii") as stream:
                file_fd = -1
                stream.write(token + "\\\\n")
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            if file_fd >= 0:
                os.close(file_fd)

        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
'''

path.write_text(source[:start] + replacement + source[end:])
print("SOURCE_PATCHED=YES")
PY

echo
echo "--- Syntax check ---"
./venv/bin/python -m py_compile app/cli/api_tokens.py
echo "PYTHON_SYNTAX=PASS"

echo
echo "--- New source hash ---"
sha256sum app/cli/api_tokens.py

echo
echo "--- Backup verification ---"
sha256sum -c "$BACKUP_DIR/SHA256.before"

echo
echo "DATABASE_CHANGED=NO"
echo "TOKEN_ISSUED=NO"
echo "TOKEN_REVOKED=NO"
echo "SERVICE_RESTARTED=NO"
```

## 2.4 Checking the Copy and Imports

The `sha256sum -c` at the end of the script above compares against the same path after the change, so it gives `FAIL`. We compare again against the pre-change copy itself.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN CLI BACKUP AND IMPORT VERIFICATION ====="

BACKUP_DIR="/var/backups/ai-defense-manager/token-cli-hardening-20261124"

echo
echo "--- 1. Recorded original hash ---"
cat "$BACKUP_DIR/SHA256.before"

echo
echo "--- 2. Actual backup hash ---"
sha256sum "$BACKUP_DIR/api_tokens.py.before"

echo
echo "--- 3. Compare recorded hash with backup ---"
EXPECTED="$(awk '{print $1}' "$BACKUP_DIR/SHA256.before")"
ACTUAL="$(sha256sum "$BACKUP_DIR/api_tokens.py.before" | awk '{print $1}')"
if [ "$EXPECTED" = "$ACTUAL" ]; then
    echo "BACKUP_INTEGRITY=PASS"
else
    echo "BACKUP_INTEGRITY=FAIL"
fi

echo
echo "--- 4. Current imports ---"
sed -n '1,35p' app/cli/api_tokens.py

echo
echo "--- 5. Writer implementation ---"
sed -n '/^def _write_token_file/,/^def main/p' app/cli/api_tokens.py

echo
echo "--- 6. Required module availability ---"
./venv/bin/python - <<'PY'
import app.cli.api_tokens as module
print("OS_IMPORT=" + ("PASS" if hasattr(module, "os") else "FAIL"))
print("STAT_IMPORT=" + ("PASS" if hasattr(module, "stat") else "FAIL"))
print("PATH_IMPORT=" + ("PASS" if hasattr(module, "Path") else "FAIL"))
PY

echo
echo "PRODUCTION_DATABASE_ACCESSED=NO"
echo "TOKEN_ISSUED=NO"
echo "SERVICE_RESTARTED=NO"
```

The integrity of the copy passed, and there were no problems importing `os`, `stat` and `Path`. Reading the source, `stream.write(token + "\\n")` was written so that it writes the characters `\n` rather than a newline.

## 2.5 Fixing the Newline and Retesting

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN FILE NEWLINE FIX AND REGRESSION TEST ====="

./venv/bin/python - <<'PY'
import os
import stat
import tempfile
from pathlib import Path

path = Path("app/cli/api_tokens.py")
source = path.read_text()

old = r'stream.write(token + "\\n")'
new = r'stream.write(token + "\n")'

if source.count(old) != 1:
    print("PATCH=ABORTED")
    print("EXPECTED_SOURCE_PATTERN_COUNT=" + str(source.count(old)))
    raise SystemExit(1)

path.write_text(source.replace(old, new, 1))
print("NEWLINE_SOURCE_PATCH=PASS")
PY

./venv/bin/python -m py_compile app/cli/api_tokens.py
echo "PYTHON_SYNTAX=PASS"

./venv/bin/python - <<'PY'
import os
import stat
import tempfile
from pathlib import Path
from app.cli.api_tokens import _write_token_file

results = []

def check(name, ok):
    results.append(bool(ok))
    print(f"{name}={'PASS' if ok else 'FAIL'}")

with tempfile.TemporaryDirectory(prefix="aidm-cli-regression-", dir="/root") as tmp:
    root = Path(tmp)

    # Normal creation and an exact newline
    output = root / "tokens" / "token.txt"
    _write_token_file("dummy.secret", output)
    check("TOKEN_CONTENT_EXACT", output.read_bytes() == b"dummy.secret\n")
    check("TOKEN_FILE_MODE_0600", stat.S_IMODE(output.stat().st_mode) == 0o600)
    check("CREATED_DIR_MODE_0700", stat.S_IMODE(output.parent.stat().st_mode) == 0o700)

    # Prevent overwriting an existing file
    overwrite_blocked = False
    try:
        _write_token_file("replacement", output)
    except FileExistsError:
        overwrite_blocked = output.read_bytes() == b"dummy.secret\n"
    check("EXISTING_FILE_PROTECTED", overwrite_blocked)

    # Reject a parent symbolic link
    real = root / "real"
    real.mkdir(mode=0o700)
    link = root / "link"
    link.symlink_to(real, target_is_directory=True)
    symlink_blocked = False
    try:
        _write_token_file("dummy", link / "token.txt")
    except OSError:
        symlink_blocked = True
    check("PARENT_SYMLINK_REJECTED", symlink_blocked)
    check("SYMLINK_TARGET_UNCHANGED", not (real / "token.txt").exists())

    # Reject a symbolic link in the final component
    target = root / "target.txt"
    target.write_text("unchanged")
    final_link = root / "final-link"
    final_link.symlink_to(target)
    final_blocked = False
    try:
        _write_token_file("replacement", final_link)
    except OSError:
        final_blocked = target.read_text() == "unchanged"
    check("FINAL_SYMLINK_REJECTED", final_blocked)

print(f"PASS_COUNT={sum(results)}")
print(f"FAIL_COUNT={len(results) - sum(results)}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("SERVICE_RESTARTED=NO")
PY

echo
echo "--- Updated source hash ---"
sha256sum app/cli/api_tokens.py

echo "PRODUCTION_TOKEN_STORE_MODIFIED=NO"
```

All 7 passed (correct newline, `0600`, new directory `0700`, no overwriting, symbolic links rejected, link targets unaffected).

# Chapter 3: Checking Scope Types

## 3.1 The Current Check

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API TOKEN SCOPE VALIDATION SOURCE AUDIT ====="

echo
echo "--- 1. verify_token implementation ---"
grep -n -A100 -B10 '^def verify_token' app/services/api_tokens.py

echo
echo "--- 2. Scope parsing and validation references ---"
grep -n -E 'json.loads|ALLOWED_SCOPES|scopes|compare_digest|PermissionError' app/services/api_tokens.py

echo
echo "--- 3. Token table schema initialization ---"
grep -n -A35 -B5 'CREATE TABLE' app/services/api_tokens.py

echo
echo "--- 4. Current source hash ---"
sha256sum app/services/api_tokens.py app/cli/api_tokens.py

echo
echo "PRODUCTION_DATABASE_ACCESSED=NO"
echo "PRODUCTION_TOKEN_STORE_MODIFIED=NO"
echo "TOKEN_ISSUED=NO"
echo "SERVICE_RESTARTED=NO"
```

The following check could raise `TypeError: unhashable type` if the `scopes` array contains dictionaries or lists.

```python
all(scope in ALLOWED_SCOPES for scope in scopes)
```

## 3.2 Reproducing It

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: MALFORMED TOKEN SCOPE ISOLATED TEST ====="

./venv/bin/python - <<'PY'
import hashlib
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import app.services.api_tokens as tokens

original_db_path = tokens.DB_PATH

with tempfile.TemporaryDirectory(prefix="aidm-scope-test-", dir="/root") as tmp:
    test_db = Path(tmp) / "isolated.db"
    tokens.DB_PATH = test_db

    tokens.initialize_api_token_store()

    token_id = "a" * 32
    secret = "isolated-dummy-secret"
    plaintext = token_id + "." + secret
    secret_hash = hashlib.sha256(secret.encode()).hexdigest()

    expiry = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    cases = [
        ("VALID_STRING_SCOPES", '["read","analyze"]'),
        ("UNKNOWN_STRING_SCOPE", '["read","admin"]'),
        ("DICT_SCOPE", '[{"scope":"read"}]'),
        ("LIST_SCOPE", '[["read"]]'),
        ("NON_LIST_SCOPE", '{"scope":"read"}'),
        ("INVALID_JSON", '{invalid'),
    ]

    results = []

    try:
        for index, (name, scopes_json) in enumerate(cases):
            current_id = format(index + 1, "032x")
            current_token = current_id + "." + secret

            with sqlite3.connect(test_db) as conn:
                conn.execute(
                    """
                    INSERT INTO api_tokens
                    (token_id, secret_hash, name, scopes, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        current_id,
                        secret_hash,
                        "isolated-test",
                        scopes_json,
                        datetime.now(timezone.utc).isoformat(),
                        expiry,
                    ),
                )

            try:
                result = tokens.verify_token(current_token, "read")
                outcome = f"RETURNED_{result}"
            except Exception as exc:
                outcome = "EXCEPTION_" + type(exc).__name__

            print(f"{name}={outcome}")
            results.append((name, outcome))

        print()
        print("UNHASHABLE_SCOPE_EXCEPTION=" + (
            "DETECTED"
            if any(
                outcome == "EXCEPTION_TypeError"
                for _, outcome in results
            )
            else "NOT_DETECTED"
        ))

    finally:
        tokens.DB_PATH = original_db_path

print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_STORE_MODIFIED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

`TypeError` occurred for both `DICT_SCOPE` and `LIST_SCOPE`. This means invalid authentication data would cause a `500` error.

## 3.3 Fixing

We check first that elements are strings, then compare against the allowlist.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN SCOPE TYPE VALIDATION PATCH ====="

BACKUP_DIR="/var/backups/ai-defense-manager/token-cli-hardening-20261124"
cp -a app/services/api_tokens.py "$BACKUP_DIR/api_tokens.py.before-scope-fix"
sha256sum app/services/api_tokens.py > "$BACKUP_DIR/SHA256.scope-before"
chmod 600 "$BACKUP_DIR/api_tokens.py.before-scope-fix" "$BACKUP_DIR/SHA256.scope-before"

./venv/bin/python - <<'PY'
from pathlib import Path

path = Path("app/services/api_tokens.py")
source = path.read_text()

old = '''        if (
            not isinstance(scopes, list)
            or not all(scope in ALLOWED_SCOPES for scope in scopes)
        ):
            return False
'''

new = '''        if (
            not isinstance(scopes, list)
            or not all(
                isinstance(scope, str) and scope in ALLOWED_SCOPES
                for scope in scopes
            )
        ):
            return False
'''

if source.count(old) != 1:
    raise SystemExit("PATCH_ABORTED: expected source block not found exactly once")

path.write_text(source.replace(old, new, 1))
print("SOURCE_PATCHED=YES")
PY

echo
echo "--- Syntax check ---"
./venv/bin/python -m py_compile app/services/api_tokens.py
echo "PYTHON_SYNTAX=PASS"

echo
echo "--- Isolated malformed-scope regression test ---"
./venv/bin/python - <<'PY'
import hashlib
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import app.services.api_tokens as tokens

original_db_path = tokens.DB_PATH
results = []

def check(name, condition):
    results.append(bool(condition))
    print(f"{name}={'PASS' if condition else 'FAIL'}")

with tempfile.TemporaryDirectory(prefix="aidm-scope-fixed-", dir="/root") as tmp:
    test_db = Path(tmp) / "isolated.db"
    tokens.DB_PATH = test_db
    tokens.initialize_api_token_store()

    secret = "isolated-dummy-secret"
    secret_hash = hashlib.sha256(secret.encode()).hexdigest()
    expiry = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    cases = [
        ("VALID_STRING_SCOPES", '["read","analyze"]', True),
        ("UNKNOWN_STRING_SCOPE", '["read","admin"]', False),
        ("DICT_SCOPE", '[{"scope":"read"}]', False),
        ("LIST_SCOPE", '[["read"]]', False),
        ("NON_LIST_SCOPE", '{"scope":"read"}', False),
        ("INVALID_JSON", '{invalid', False),
    ]

    try:
        for index, (name, scopes_json, expected) in enumerate(cases):
            token_id = format(index + 1, "032x")
            with sqlite3.connect(test_db) as conn:
                conn.execute(
                    """
                    INSERT INTO api_tokens
                    (token_id, secret_hash, name, scopes, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        token_id,
                        secret_hash,
                        "isolated-test",
                        scopes_json,
                        datetime.now(timezone.utc).isoformat(),
                        expiry,
                    ),
                )

            try:
                actual = tokens.verify_token(token_id + "." + secret, "read")
                check(name, actual is expected)
            except Exception as exc:
                print(f"{name}=FAIL EXCEPTION={type(exc).__name__}")
                results.append(False)
    finally:
        tokens.DB_PATH = original_db_path

print(f"PASS_COUNT={sum(results)}")
print(f"FAIL_COUNT={len(results) - sum(results)}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_STORE_MODIFIED=NO")
print("TOKEN_ISSUED=NO")
print("SERVICE_RESTARTED=NO")
PY

echo
echo "--- Source hash ---"
sha256sum app/services/api_tokens.py
```

All 6 passed (valid scopes pass, disallowed scopes are rejected, dictionaries, lists and the like are rejected without exceptions, and invalid JSON is also rejected).

# Chapter 4: Expiry, Listing and Write Failures

## 4.1 Testing Edge Values

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN SERVICE EDGE CASE ISOLATED AUDIT ====="

./venv/bin/python - <<'PY'
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import app.services.api_tokens as tokens
from app.cli.api_tokens import _write_token_file

original_db_path = tokens.DB_PATH
results = []

def report(name, outcome):
    print(f"{name}={outcome}")
    results.append(outcome == "EXPECTED")

with tempfile.TemporaryDirectory(prefix="aidm-edge-audit-", dir="/root") as tmp:
    root = Path(tmp)
    tokens.DB_PATH = root / "isolated.db"

    try:
        tokens.initialize_api_token_store()

        # 1. bool is a subclass of int
        try:
            tokens.issue_token("bool-expiry-test", {"read"}, True)
            report("BOOLEAN_EXPIRY_ACCEPTED", "DETECTED")
        except (ValueError, TypeError):
            report("BOOLEAN_EXPIRY_REJECTED", "EXPECTED")

        # 2. Invalid name type must not reach production DB
        try:
            tokens.issue_token(None, {"read"}, 1)
            report("NON_STRING_NAME_HANDLING", "UNEXPECTED_ACCEPT")
        except (ValueError, TypeError, AttributeError):
            report("NON_STRING_NAME_HANDLING", "EXPECTED")

        # 3. Corrupt scopes JSON in isolated DB
        with sqlite3.connect(tokens.DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO api_tokens
                (token_id, secret_hash, name, scopes, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "b" * 32,
                    "a" * 64,
                    "corrupt-test",
                    "{invalid-json",
                    datetime.now(timezone.utc).isoformat(),
                    "2099-01-01T00:00:00+00:00",
                ),
            )

        try:
            tokens.list_tokens()
            report("CORRUPT_SCOPE_LIST_HANDLING", "UNEXPECTED_SUCCESS")
        except Exception as exc:
            print("CORRUPT_SCOPE_LIST_EXCEPTION=" + type(exc).__name__)
            report("CORRUPT_SCOPE_LIST_HANDLING", "DETECTED")

        # 4. Writer failure cleanup: use a directory as final filename.
        blocked = root / "blocked"
        blocked.mkdir()
        try:
            _write_token_file("dummy-secret", blocked)
            report("WRITER_DIRECTORY_TARGET", "UNEXPECTED_SUCCESS")
        except (OSError, ValueError):
            report("WRITER_DIRECTORY_TARGET", "EXPECTED")

    finally:
        tokens.DB_PATH = original_db_path

print()
print("EXPECTED_CASES=" + str(sum(results)))
print("UNEXPECTED_CASES=" + str(len(results) - sum(results)))
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_STORE_MODIFIED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("PRODUCTION_FILES_MODIFIED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

- In Python, `bool` is a kind of `int`, so `True` is accepted as an expiry of 1 day
- If `scopes` in the DB is invalid JSON, `list_tokens()` stops with `JSONDecodeError`

## 4.2 Fixing Expiry and Listing

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN EXPIRY AND LIST CORRUPTION HARDENING ====="

BACKUP_DIR="/var/backups/ai-defense-manager/token-cli-hardening-20261124"
cp -a app/services/api_tokens.py "$BACKUP_DIR/api_tokens.py.before-edge-fix"
sha256sum app/services/api_tokens.py > "$BACKUP_DIR/SHA256.edge-before"
chmod 600 "$BACKUP_DIR/api_tokens.py.before-edge-fix" "$BACKUP_DIR/SHA256.edge-before"

./venv/bin/python - <<'PY'
from pathlib import Path

path = Path("app/services/api_tokens.py")
source = path.read_text()

old_expiry = '''    if not isinstance(expires_in_days, int) or not 1 <= expires_in_days <= 365:
        raise ValueError("Expiry must be between 1 and 365 days")
'''

new_expiry = '''    if type(expires_in_days) is not int or not 1 <= expires_in_days <= 365:
        raise ValueError("Expiry must be between 1 and 365 days")
'''

old_list = '''    return [
        {
            "token_id": row["token_id"],
            "name": row["name"],
            "scopes": json.loads(row["scopes"]),
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "revoked_at": row["revoked_at"],
            "last_used_at": row["last_used_at"],
        }
        for row in rows
    ]
'''

new_list = '''    result = []
    for row in rows:
        try:
            scopes = json.loads(row["scopes"])
        except (ValueError, TypeError):
            scopes = []

        if (
            not isinstance(scopes, list)
            or not all(
                isinstance(scope, str) and scope in ALLOWED_SCOPES
                for scope in scopes
            )
        ):
            scopes = []

        result.append({
            "token_id": row["token_id"],
            "name": row["name"],
            "scopes": scopes,
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "revoked_at": row["revoked_at"],
            "last_used_at": row["last_used_at"],
        })

    return result
'''

if source.count(old_expiry) != 1:
    raise SystemExit("PATCH_ABORTED: expiry block mismatch")
if source.count(old_list) != 1:
    raise SystemExit("PATCH_ABORTED: list block mismatch")

source = source.replace(old_expiry, new_expiry, 1)
source = source.replace(old_list, new_list, 1)
path.write_text(source)

print("SOURCE_PATCHED=YES")
PY

echo
echo "--- Syntax check ---"
./venv/bin/python -m py_compile app/services/api_tokens.py
echo "PYTHON_SYNTAX=PASS"

echo
echo "--- Isolated regression tests ---"
./venv/bin/python - <<'PY'
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import app.services.api_tokens as tokens

original_db_path = tokens.DB_PATH
results = []

def check(name, condition):
    results.append(bool(condition))
    print(f"{name}={'PASS' if condition else 'FAIL'}")

with tempfile.TemporaryDirectory(prefix="aidm-edge-fixed-", dir="/root") as tmp:
    tokens.DB_PATH = Path(tmp) / "isolated.db"

    try:
        tokens.initialize_api_token_store()

        for value, expected in [
            (True, False),
            (False, False),
            (1, True),
            (90, True),
            (365, True),
            (0, False),
            (366, False),
        ]:
            try:
                tokens.issue_token("expiry-test", {"read"}, value)
                actual = True
            except (ValueError, TypeError):
                actual = False
            check(f"EXPIRY_{value!r}_ACCEPTANCE", actual is expected)

        with sqlite3.connect(tokens.DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO api_tokens
                (token_id, secret_hash, name, scopes, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "c" * 32,
                    "b" * 64,
                    "corrupt-json",
                    "{invalid-json",
                    datetime.now(timezone.utc).isoformat(),
                    "2099-01-01T00:00:00+00:00",
                ),
            )
            conn.execute(
                """
                INSERT INTO api_tokens
                (token_id, secret_hash, name, scopes, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "d" * 32,
                    "c" * 64,
                    "corrupt-type",
                    '[{"scope":"read"}]',
                    datetime.now(timezone.utc).isoformat(),
                    "2099-01-01T00:00:00+00:00",
                ),
            )

        items = tokens.list_tokens()
        by_id = {item["token_id"]: item for item in items}

        check(
            "CORRUPT_JSON_LIST_SAFE",
            by_id["c" * 32]["scopes"] == [],
        )
        check(
            "CORRUPT_SCOPE_TYPE_LIST_SAFE",
            by_id["d" * 32]["scopes"] == [],
        )
        check(
            "TOKEN_SECRET_NOT_INCLUDED",
            all("secret_hash" not in item for item in items),
        )

    finally:
        tokens.DB_PATH = original_db_path

print(f"PASS_COUNT={sum(results)}")
print(f"FAIL_COUNT={len(results) - sum(results)}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_STORE_MODIFIED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("SERVICE_RESTARTED=NO")
PY

echo
echo "--- Source hash ---"
sha256sum app/services/api_tokens.py
```

| Checked | Result |
|---|---|
| Rejecting `True` and `False` as expiry | passed |
| 1, 90, 365 days | passed |
| Rejecting 0 and 366 days | passed |
| Listing that includes invalid JSON | passed |
| Listing that includes invalid scope types | passed |
| No secrets in the listing | passed |

All 10 passed.

## 4.3 When Writing Fails

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN ISSUE FAILURE CLEANUP ISOLATED AUDIT ====="

./venv/bin/python - <<'PY'
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import app.cli.api_tokens as cli

results = []

def check(name, condition):
    results.append(bool(condition))
    print(f"{name}={'PASS' if condition else 'FAIL'}")

with tempfile.TemporaryDirectory(prefix="aidm-cleanup-audit-", dir="/root") as tmp:
    root = Path(tmp)
    output = root / "blocked-parent" / "token.txt"

    issued = {"token_id": "a" * 32, "plaintext": "dummy.secret"}
    revoked = []

    def fake_issue(*args):
        return issued["token_id"], issued["plaintext"]

    def fake_revoke(token_id):
        revoked.append(token_id)
        return True

    def failing_writer(token, path):
        path.parent.mkdir(mode=0o700)
        partial = path.with_name(path.name + ".partial")
        partial.write_text("partial")
        raise OSError("simulated write failure")

    with (
        patch.object(cli, "issue_token", side_effect=fake_issue),
        patch.object(cli, "revoke_token", side_effect=fake_revoke),
        patch.object(cli, "_write_token_file", side_effect=failing_writer),
        patch.object(cli, "initialize_api_token_store"),
        patch.object(cli, "_require_root"),
    ):
        import sys
        original_argv = sys.argv
        sys.argv = [
            "aidm-api-token",
            "issue",
            "--name", "isolated-test",
            "--scopes", "read",
            "--output", str(output),
        ]
        try:
            exit_code = cli.main()
        finally:
            sys.argv = original_argv

    check("ISSUE_COMMAND_FAILED", exit_code == 1)
    check("TOKEN_REVOKE_ATTEMPTED", revoked == [issued["token_id"]])
    check(
        "PARTIAL_FILE_REMAINS",
        (output.with_name(output.name + ".partial")).exists(),
    )

print()
print(f"PASS_COUNT={sum(results)}")
print(f"FAIL_COUNT={len(results) - sum(results)}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_STORE_MODIFIED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

If writing the file fails during issuance, the issued token is revoked and the CLI exits with an error, but a partial file could be left behind.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN FILE FAILURE CLEANUP SOURCE INSPECTION ====="

echo "--- _write_token_file ---"
sed -n '1,145p' app/cli/api_tokens.py

echo
echo "--- issue command exception handling ---"
grep -n -A75 -B15 'def _issue\|def main\|_write_token_file\|revoke_token' app/cli/api_tokens.py

echo
echo "--- Current source hash ---"
sha256sum app/cli/api_tokens.py

echo
echo "SOURCE_MODIFIED=NO"
echo "PRODUCTION_DATABASE_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

`_write_token_file()` had no step to remove the file when `write()`, `flush()` or `fsync()` failed after the file was created.

## 4.4 Removing the Partial File on Failure

If an exception occurs after newly creating the file, only that file is removed using the FD of the same directory. Existing files and symbolic links are not removed.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN FILE PARTIAL WRITE CLEANUP PATCH ====="

./venv/bin/python - <<'PY'
from pathlib import Path

path = Path("app/cli/api_tokens.py")
source = path.read_text()

old = '''        try:
            os.fchmod(file_fd, 0o600)
            with os.fdopen(file_fd, "w", encoding="ascii") as stream:
                file_fd = -1
                stream.write(token + "\\n")
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            if file_fd >= 0:
                os.close(file_fd)

        os.fsync(directory_fd)
'''

new = '''        try:
            try:
                os.fchmod(file_fd, 0o600)
                with os.fdopen(file_fd, "w", encoding="ascii") as stream:
                    file_fd = -1
                    stream.write(token + "\\n")
                    stream.flush()
                    os.fsync(stream.fileno())

                os.fsync(directory_fd)
            except BaseException:
                if file_fd >= 0:
                    os.close(file_fd)
                    file_fd = -1

                try:
                    os.unlink(parts[-1], dir_fd=directory_fd)
                except FileNotFoundError:
                    pass

                try:
                    os.fsync(directory_fd)
                except OSError:
                    pass

                raise
        finally:
            if file_fd >= 0:
                os.close(file_fd)
'''

if source.count(old) != 1:
    raise SystemExit("PATCH_ABORTED: writer block mismatch")

path.write_text(source.replace(old, new, 1))
print("SOURCE_PATCHED=YES")
PY

echo
echo "--- Syntax check ---"
./venv/bin/python -m py_compile app/cli/api_tokens.py
echo "PYTHON_SYNTAX=PASS"

echo
echo "--- Isolated actual writer failure tests ---"
./venv/bin/python - <<'PY'
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from app.cli.api_tokens import _write_token_file

results = []

def check(name, condition):
    results.append(bool(condition))
    print(f"{name}={'PASS' if condition else 'FAIL'}")

with tempfile.TemporaryDirectory(prefix="aidm-writer-cleanup-", dir="/root") as tmp:
    root = Path(tmp)
    output = root / "tokens" / "issued.txt"

    real_fsync = os.fsync
    calls = {"count": 0}

    def fail_first_fsync(fd):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("isolated fsync failure")
        return real_fsync(fd)

    try:
        with patch("app.cli.api_tokens.os.fsync", side_effect=fail_first_fsync):
            _write_token_file("isolated-dummy-token", output)
        check("INJECTED_FAILURE_TRIGGERED", False)
    except OSError:
        check("INJECTED_FAILURE_TRIGGERED", calls["count"] >= 1)

    check("PARTIAL_TOKEN_FILE_REMOVED", not output.exists())
    check("TOKEN_DIRECTORY_REMAINS", output.parent.is_dir())
    check(
        "TOKEN_DIRECTORY_EMPTY",
        output.parent.is_dir() and not any(output.parent.iterdir()),
    )

    normal = root / "normal" / "token.txt"
    _write_token_file("normal-dummy-token", normal)
    check(
        "NORMAL_WRITE_CONTENT",
        normal.read_text() == "normal-dummy-token\n",
    )
    check(
        "NORMAL_WRITE_MODE_0600",
        (normal.stat().st_mode & 0o777) == 0o600,
    )

print()
print(f"PASS_COUNT={sum(results)}")
print(f"FAIL_COUNT={len(results) - sum(results)}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_STORE_MODIFIED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("SERVICE_RESTARTED=NO")
PY

echo
echo "--- Source hash ---"
sha256sum app/cli/api_tokens.py
```

We actually caused `fsync()` to fail and confirmed that the partial file is removed, and that on success the contents are saved with `0600` (all 6 passed).

# Chapter 5: Whole Tests and the Final Check

## 5.1 Token Lifecycle Tests (17 Cases)

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN LIFECYCLE API INSPECTION ====="

./venv/bin/python - <<'PY'
import inspect
import app.services.api_tokens as tokens

for name in ("issue_token", "verify_token", "revoke_token", "list_tokens"):
    fn = getattr(tokens, name)
    print(f"\n--- {name}{inspect.signature(fn)} ---")
    print(inspect.getsource(fn))

print("\nPRODUCTION_DATABASE_ACCESSED=NO")
print("TOKEN_ISSUED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

On successful authentication `last_used_at` is updated; insufficient scope raises `PermissionError`; invalid or revoked tokens give `False`. We check with a temporary SQLite DB. Token plaintext and hashes are not displayed.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED TOKEN LIFECYCLE REGRESSION TEST ====="

./venv/bin/python - <<'PY'
import hashlib
import sqlite3
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import app.services.api_tokens as tokens

original_db_path = tokens.DB_PATH
results = []

def check(name, condition):
    results.append(bool(condition))
    print(f"{name}={'PASS' if condition else 'FAIL'}")

with tempfile.TemporaryDirectory(prefix="aidm-lifecycle-", dir="/root") as tmp:
    tokens.DB_PATH = Path(tmp) / "isolated.db"

    try:
        tokens.initialize_api_token_store()

        token_id, plaintext = tokens.issue_token(
            "isolated-lifecycle-test", {"read"}, 90
        )

        check("TOKEN_ID_FORMAT", len(token_id) == 32)
        check("PLAINTEXT_NOT_EMPTY", isinstance(plaintext, str) and "." in plaintext)

        secret = plaintext.partition(".")[2]
        expected_hash = hashlib.sha256(secret.encode("ascii")).hexdigest()

        with sqlite3.connect(tokens.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT secret_hash, scopes, last_used_at, revoked_at "
                "FROM api_tokens WHERE token_id = ?",
                (token_id,),
            ).fetchone()

        check("HASH_ONLY_STORED", row["secret_hash"] == expected_hash)
        check("PLAINTEXT_NOT_STORED", plaintext not in row["secret_hash"])
        check("READ_SCOPE_STORED", row["scopes"] == '["read"]')

        check("VALID_READ_TOKEN_ACCEPTED", tokens.verify_token(plaintext, "read"))

        with sqlite3.connect(tokens.DB_PATH) as conn:
            last_used = conn.execute(
                "SELECT last_used_at FROM api_tokens WHERE token_id = ?",
                (token_id,),
            ).fetchone()[0]

        check("LAST_USED_UPDATED", last_used is not None)

        try:
            tokens.verify_token(plaintext, "analyze")
            scope_denied = False
        except PermissionError:
            scope_denied = True

        check("MISSING_SCOPE_DENIED", scope_denied)
        check("WRONG_SECRET_REJECTED", not tokens.verify_token(
            token_id + ".wrong-secret", "read"
        ))
        check("MALFORMED_TOKEN_REJECTED", not tokens.verify_token(
            "malformed", "read"
        ))
        check("UNKNOWN_TOKEN_REJECTED", not tokens.verify_token(
            "f" * 32 + ".unknown-secret", "read"
        ))

        check("FIRST_REVOCATION_SUCCEEDS", tokens.revoke_token(token_id))
        check("SECOND_REVOCATION_NO_CHANGE", not tokens.revoke_token(token_id))
        check("REVOKED_TOKEN_REJECTED", not tokens.verify_token(plaintext, "read"))

        listed = tokens.list_tokens()
        item = next((x for x in listed if x["token_id"] == token_id), None)

        check("REVOKED_STATE_LISTED", item is not None and item["revoked_at"] is not None)
        check(
            "LIST_EXCLUDES_SECRET_FIELDS",
            item is not None and "secret_hash" not in item and "token" not in item,
        )

        # Expiry boundary: force expiry into the past in the isolated DB.
        expired_id, expired_plaintext = tokens.issue_token(
            "isolated-expiry-test", {"read"}, 1
        )
        with sqlite3.connect(tokens.DB_PATH) as conn:
            conn.execute(
                "UPDATE api_tokens SET expires_at = ? WHERE token_id = ?",
                ((datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
                 expired_id),
            )

        check("EXPIRED_TOKEN_REJECTED", not tokens.verify_token(
            expired_plaintext, "read"
        ))

    finally:
        tokens.DB_PATH = original_db_path

print()
print(f"PASS_COUNT={sum(results)}")
print(f"FAIL_COUNT={len(results) - sum(results)}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_STORE_MODIFIED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("LIVE_API_REQUESTS=NO")
print("SERVICE_RESTARTED=NO")
PY
```

All 17 passed (ID format and issuing, storing as hashes, passing with the correct scope, rejecting insufficient scope, rejecting invalid and unknown tokens, updating last-used time, revocation and more).

## 5.2 Tests Through the CLI (14 Cases)

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED TOKEN CLI END-TO-END TEST ====="

./venv/bin/python - <<'PY'
import contextlib
import io
import tempfile
from pathlib import Path
from unittest.mock import patch

import app.services.api_tokens as token_service
import app.cli.api_tokens as cli

original_db_path = token_service.DB_PATH
results = []

def check(name, condition):
    results.append(bool(condition))
    print(f"{name}={'PASS' if condition else 'FAIL'}")

with tempfile.TemporaryDirectory(prefix="aidm-cli-e2e-", dir="/root") as tmp:
    root = Path(tmp)
    token_service.DB_PATH = root / "isolated.db"
    token_file = root / "private" / "client.token"

    def run_cli(argv):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch("sys.argv", ["aidm-api-token", *argv]):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = cli.main()
        return code, stdout.getvalue(), stderr.getvalue()

    try:
        code, out, err = run_cli([
            "issue",
            "--name", "cli-e2e-test",
            "--scopes", "read",
            "--expires-in-days", "30",
            "--output", str(token_file),
        ])

        check("CLI_ISSUE_EXIT_ZERO", code == 0)
        check("CLI_ISSUE_SUCCESS_MARKER", "TOKEN_ISSUED=YES" in out)
        check("TOKEN_FILE_CREATED", token_file.is_file())
        check(
            "TOKEN_FILE_MODE_0600",
            token_file.is_file() and (token_file.stat().st_mode & 0o777) == 0o600,
        )

        plaintext = token_file.read_text().strip() if token_file.is_file() else ""
        token_id = plaintext.partition(".")[0]

        check("TOKEN_FILE_FORMAT", bool(token_id) and "." in plaintext)
        check(
            "TOKEN_VALUE_NOT_PRINTED",
            bool(plaintext) and plaintext not in out and plaintext not in err,
        )

        code, out, err = run_cli(["list"])
        check("CLI_LIST_EXIT_ZERO", code == 0)
        check("CLI_LIST_CONTAINS_TOKEN_ID", token_id in out)
        check("CLI_LIST_DOES_NOT_EXPOSE_SECRET", plaintext not in out)
        check("CLI_LIST_SECRET_NOTICE", "NOT_STORED_OR_DISPLAYED" in out)

        code, out, err = run_cli(["revoke", "--token-id", token_id])
        check("CLI_REVOKE_EXIT_ZERO", code == 0)
        check("CLI_REVOKE_SUCCESS", "TOKEN_REVOKED= YES" in out)

        check(
            "REVOKED_TOKEN_REJECTED",
            not token_service.verify_token(plaintext, "read"),
        )

        code, out, err = run_cli(["revoke", "--token-id", token_id])
        check("CLI_SECOND_REVOKE_NO_CHANGE", code == 0 and "NO_CHANGE" in out)

    finally:
        token_service.DB_PATH = original_db_path

print()
print(f"PASS_COUNT={sum(results)}")
print(f"FAIL_COUNT={len(results) - sum(results)}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_STORE_MODIFIED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("LIVE_API_REQUESTS=NO")
print("SERVICE_RESTARTED=NO")
PY
```

| Operation | Result |
|---|---|
| `issue` | issued; secret file saved with `0600` |
| `list` | shows IDs, does not show plaintext tokens |
| `revoke` | revoked successfully |
| `revoke` again | `NO_CHANGE` |
| Authentication after revocation | rejected |

All 14 passed. The independent tests of the service and the CLI, 31 in total (17 and 14), all passed.

## 5.3 Final Check Before Production

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API AUTH PRE-DEPLOYMENT STATIC AUDIT ====="

echo
echo "--- 1. Python compile check ---"
./venv/bin/python -m compileall -q app
echo "COMPILEALL=PASS"

echo
echo "--- 2. API route authentication declarations ---"
grep -n -E -B3 -A5 \
  'require_scope|@router\.(get|post)|include_in_schema' \
  app/api/analysis.py app/api/wazuh.py

echo
echo "--- 3. Documentation endpoints configuration ---"
grep -n -A8 -B3 \
  'FastAPI(' app/main.py

echo
echo "--- 4. Modified source permissions and ownership ---"
stat -c '%U:%G %a %n' \
  app/main.py \
  app/api/analysis.py \
  app/api/wazuh.py \
  app/core/api_auth.py \
  app/services/api_tokens.py \
  app/cli/api_tokens.py \
  app/cli/__init__.py \
  /usr/local/sbin/aidm-api-token

echo
echo "--- 5. Source hashes ---"
sha256sum \
  app/main.py \
  app/api/analysis.py \
  app/api/wazuh.py \
  app/core/api_auth.py \
  app/services/api_tokens.py \
  app/cli/api_tokens.py \
  app/cli/__init__.py \
  /usr/local/sbin/aidm-api-token

echo
echo "--- 6. Service state (read-only metadata) ---"
systemctl show ai-defense-manager.service \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p ExecMainStartTimestamp \
  -p User \
  -p Group \
  -p FragmentPath

echo
echo "PRODUCTION_DATABASE_ACCESSED=NO"
echo "PRODUCTION_TOKEN_STORE_MODIFIED=NO"
echo "TOKEN_ISSUED=NO"
echo "SERVICE_RESTARTED=NO"
echo "LIVE_WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
```

| Check | Result |
|---|---|
| Syntax of all Python | passed |
| `/api/v1/wazuh/events`: `read` | passed |
| `/api/v1/analysis`: `analyze` | passed |
| `/api/v1/wazuh/analyze`: `analyze` | passed |
| `/health` | still outside authentication |
| Swagger, ReDoc, OpenAPI | disabled |
| Service | `active (running)`; not restarted |

`app/main.py` and `app/api/wazuh.py` are `root:ai-defense`, `640`, while some authentication files are `root:root`, `644`; they are not uniform. In both cases the service account can read but not write them, so we do not change them now.

# Closing Notes

In Part 58 we fixed weaknesses in token handling and the CLI, and are ready for production.

| Item | Result |
|---|---|
| Token file | rejects symbolic links, no overwriting, `0600` and directory `0700`; removes partial files on failure |
| Scopes and expiry | types checked, no stopping on exceptions; expiry 1–365 days |
| Listing | does not stop on broken data and does not show secret values |
| Tests | 31 in total (plus tests of each fix), all passed |
| Production | not yet deployed |

In the next part, Part 59, we create the authentication table in the production DB, issue tokens, and deploy to the service.

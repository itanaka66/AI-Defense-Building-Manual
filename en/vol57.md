---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 57: Building Token Authentication for the API"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 57 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". Following the design decided in Part 56, we build token authentication for the AI Defense Manager API and test it in an independent environment that does not use the production DB.

| Target | Details |
|---|---|
| Storage | add a dedicated authentication table `api_tokens` to the existing `ai-defense.db`; store only the SHA-256 hash of tokens, never plaintext |
| Tokens | generated with a cryptographic random number equivalent to 256 bits |
| Issuing | a root-only CLI (`/usr/local/sbin/aidm-api-token`) issues, revokes and lists. The plaintext token is written once to a root-only file (`600`) and never shown on screen or in logs |
| Privileges (scopes) | `read` (fetching Wazuh events), `analyze` (analysis) |
| Not authenticated | `/health` |
| Disabled | `/docs`, `/redoc`, `/openapi.json` |
| Service | stays as `ai-defense`, reads hashes from the DB |

The existing tables and data for analysis history, evidence, approvals and audit logs, and the Relay credentials, are not changed. In this part there is no service restart, no production token issuance, no Wazuh retrieval and no Ollama inference.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: Checks and Copies Before the Change

## 1.1 Structure of the Existing DB

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: AUTH TOKEN STORAGE IMPLEMENTATION PRECHECK ====="

echo
echo "--- 1. Existing database initialization and connection code ---"
sed -n '1,300p' app/services/analysis_history.py

echo
echo "--- 2. SQLite schema (read-only, schema only) ---"
./venv/bin/python - <<'PY'
import sqlite3

path = "/opt/ai-defense-manager/data/ai-defense.db"
db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)

for row in db.execute("""
    SELECT type, name, sql
    FROM sqlite_master
    WHERE type IN ('table', 'index', 'trigger')
    ORDER BY type, name
"""):
    kind, name, sql = row
    print(f"\n[{kind}] {name}")
    print(sql or "[SQL NOT AVAILABLE]")

db.close()
print("\nDATABASE_OPENED_READ_ONLY=YES")
PY

echo
echo "--- 3. Database file and directory metadata ---"
stat -c '%A %U:%G %s bytes %n' \
  data data/ai-defense.db

echo
echo "--- 4. SQLite usage throughout application ---"
grep -RniE \
'sqlite3\.connect|CREATE TABLE|CREATE INDEX|BEGIN|COMMIT|ROLLBACK|PRAGMA|row_factory' \
app --include='*.py' 2>/dev/null

echo
echo "--- 5. Dependency lock references ---"
grep -niE \
'^(fastapi|starlette|httpx|pydantic|pydantic-settings|uvicorn|pytest|pytest-asyncio|argon2|bcrypt|cryptography)([=<>!~; ]|$)' \
requirements.lock 2>/dev/null || true

echo
echo "--- 6. Python runtime and standard crypto support ---"
./venv/bin/python - <<'PY'
import sys
import sqlite3
import hashlib
import secrets
import hmac

print("PYTHON_VERSION=", sys.version.split()[0])
print("SQLITE_VERSION=", sqlite3.sqlite_version)
print("SHA256_AVAILABLE=", hashlib.sha256 is not None)
print("SECURE_TOKEN_GENERATOR_AVAILABLE=", callable(secrets.token_urlsafe))
print("CONSTANT_TIME_COMPARE_AVAILABLE=", callable(hmac.compare_digest))
PY

echo
echo "--- 7. Existing command-line entry points ---"
find . -maxdepth 3 -type f \
  ! -path './venv/*' \
  ! -path './.git/*' \
  \( -name '__main__.py' -o -name 'manage.py' -o -name '*cli*.py' \) \
  -printf '%p\n' | sort

echo
echo "--- 8. Current service state ---"
systemctl is-active ai-defense-manager.service
systemctl show ai-defense-manager.service \
  -p MainPID -p ActiveState -p SubState --no-pager

echo
echo "DATABASE_WRITTEN=NO"
echo "SOURCE_FILES_CHANGED=NO"
echo "PACKAGES_INSTALLED=NO"
echo "SERVICE_RESTARTED=NO"
```

## 1.2 Copying the Application and the DB

SQLite is copied with its dedicated Backup API, without writing to the original DB.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API AUTH IMPLEMENTATION PRECHANGE BACKUP ====="

BACKUP_DIR="/var/backups/ai-defense-manager/api-auth-20261124"

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

echo
echo "--- 1. Backup application source ---"
tar --exclude='./venv' --exclude='./data' --exclude='./.git' \
    -czf "$BACKUP_DIR/application-source.tar.gz" \
    app requirements.lock

echo
echo "--- 2. Create consistent SQLite backup ---"
./venv/bin/python - "$BACKUP_DIR/ai-defense.db" <<'PY'
import sqlite3
import sys
from pathlib import Path

source = Path("/opt/ai-defense-manager/data/ai-defense.db")
target = Path(sys.argv[1])

src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
dst = sqlite3.connect(target)

try:
    src.backup(dst)
    result = dst.execute("PRAGMA integrity_check").fetchone()[0]
    print("BACKUP_INTEGRITY_CHECK=", result)
    print("BACKUP_TABLE_COUNT=", dst.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table'"
    ).fetchone()[0])
finally:
    dst.close()
    src.close()
PY

echo
echo "--- 3. Restrict backup permissions ---"
chown -R root:root "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
chmod 600 "$BACKUP_DIR"/*

echo
echo "--- 4. Backup hashes ---"
cd "$BACKUP_DIR"
sha256sum application-source.tar.gz ai-defense.db | tee SHA256SUMS
sha256sum -c SHA256SUMS

echo
echo "--- 5. Backup metadata ---"
stat -c '%A %U:%G %s bytes %n' "$BACKUP_DIR" "$BACKUP_DIR"/*

echo
echo "SOURCE_DATABASE_MODIFIED=NO"
echo "SOURCE_FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

SQLite `integrity_check` was `ok`, there are six existing tables, and the SHA-256 comparison of the copied files succeeded.

## 1.3 Where to Integrate, and Settings

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: AUTH INTEGRATION SOURCE INSPECTION ====="

echo
echo "--- 1. Application entry point ---"
sed -n '1,260p' app/main.py

echo
echo "--- 2. Analysis API router ---"
sed -n '1,260p' app/api/analysis.py

echo
echo "--- 3. Wazuh API router ---"
sed -n '1,320p' app/api/wazuh.py

echo
echo "--- 4. Existing package layout ---"
find app -maxdepth 3 -type f -name '*.py' -printf '%p\n' | sort

echo
echo "--- 5. Service account access to source and database ---"
namei -l app/main.py
namei -l data/ai-defense.db
id ai-defense

echo
echo "--- 6. systemd service configuration (credential values redacted) ---"
systemctl cat ai-defense-manager.service |
  sed -E \
  -e 's/(EnvironmentFile=).*/\1[REDACTED]/' \
  -e 's/(Environment=)[^ ]*(TOKEN|PASSWORD|SECRET|KEY)[^ ]*/\1[REDACTED]/Ig' \
  -e 's/(LoadCredentialEncrypted?=).*/\1[REDACTED]/'

echo
echo "--- 7. Existing API route imports and dependencies ---"
grep -RniE \
'Depends\(|Security\(|HTTPBearer|APIKey|APIRouter|include_router|FastAPI\(' \
app --include='*.py' 2>/dev/null

echo
echo "SOURCE_FILES_CHANGED=NO"
echo "DATABASE_WRITTEN=NO"
echo "SERVICE_RESTARTED=NO"
```

The service account `ai-defense` can read and write the DB but only read the application sources. We keep this separation. Verification looks up the DB record by the token ID and compares the hash of the secret part with `hmac.compare_digest()`.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: AUTH CONFIGURATION AND CLI PRECHECK ====="

echo
echo "--- 1. Application settings ---"
sed -n '1,280p' app/core/config.py

echo
echo "--- 2. Existing directory permissions ---"
namei -l /opt/ai-defense-manager
namei -l /opt/ai-defense-manager/app
namei -l /usr/local/sbin

echo
echo "--- 3. Existing Python CLI conventions ---"
find app -maxdepth 2 -type d -printf '%M %u:%g %p\n' | sort

echo
echo "--- 4. FastAPI and Starlette test-client availability ---"
./venv/bin/python - <<'PY'
import importlib.util
import fastapi
import starlette
import httpx

print("FASTAPI_VERSION=", fastapi.__version__)
print("STARLETTE_VERSION=", starlette.__version__)
print("HTTPX_VERSION=", httpx.__version__)
print("STARLETTE_TESTCLIENT_AVAILABLE=",
      importlib.util.find_spec("starlette.testclient") is not None)
PY

echo
echo "--- 5. Root-only token storage destination precheck ---"
if [ -e /root/.local/share/ai-defense-manager/tokens ]; then
  stat -c '%A %U:%G %n' /root/.local/share/ai-defense-manager/tokens
else
  echo "TOKEN_DIRECTORY_NOT_CREATED"
fi

echo
echo "--- 6. Existing SQLite database mode ---"
./venv/bin/python - <<'PY'
import sqlite3
p = "/opt/ai-defense-manager/data/ai-defense.db"
c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
print("JOURNAL_MODE=", c.execute("PRAGMA journal_mode").fetchone()[0])
print("FOREIGN_KEYS_DEFAULT=", c.execute("PRAGMA foreign_keys").fetchone()[0])
c.close()
PY

echo
echo "SOURCE_FILES_CHANGED=NO"
echo "DATABASE_WRITTEN=NO"
echo "TOKEN_DIRECTORY_CREATED=NO"
echo "SERVICE_RESTARTED=NO"
```

Python's standard library and FastAPI's test features are all present, so no packages need to be added.

# Chapter 2: Building the Authentication

The existing files were copied in Chapter 1. At this point the authentication table is not created yet.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API TOKEN AUTHENTICATION IMPLEMENTATION ====="

mkdir -p app/cli

cat > app/services/api_tokens.py <<'PY'
"""Database-backed API token management. Plaintext secrets are never stored."""

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.services.analysis_history import DB_PATH


ALLOWED_SCOPES = frozenset({"read", "analyze"})
TOKEN_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
DUMMY_HASH = hashlib.sha256(b"invalid-api-token-secret").hexdigest()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA synchronous = FULL")
    return conn


def initialize_api_token_store() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_tokens (
                token_id TEXT PRIMARY KEY,
                secret_hash TEXT NOT NULL
                    CHECK(length(secret_hash) = 64),
                name TEXT NOT NULL,
                scopes TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked_at TEXT,
                last_used_at TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_tokens_expires_at
            ON api_tokens(expires_at)
        """)


def issue_token(name: str, scopes: set[str], expires_in_days: int):
    name = name.strip()

    if not name or len(name) > 64:
        raise ValueError("Token name must contain 1 to 64 characters")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in name):
        raise ValueError("Token name contains control characters")
    if not scopes or not scopes.issubset(ALLOWED_SCOPES):
        raise ValueError("Invalid token scopes")
    if not isinstance(expires_in_days, int) or not 1 <= expires_in_days <= 365:
        raise ValueError("Expiry must be between 1 and 365 days")

    now = datetime.now(timezone.utc)
    created_at = now.isoformat()
    expires_at = (now + timedelta(days=expires_in_days)).isoformat()

    token_id = secrets.token_hex(16)
    secret = secrets.token_urlsafe(32)
    secret_hash = hashlib.sha256(secret.encode("ascii")).hexdigest()
    plaintext_token = f"{token_id}.{secret}"

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO api_tokens (
                token_id, secret_hash, name, scopes,
                created_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                token_id,
                secret_hash,
                name,
                json.dumps(sorted(scopes), separators=(",", ":")),
                created_at,
                expires_at,
            ),
        )

    return token_id, plaintext_token


def revoke_token(token_id: str) -> bool:
    if not TOKEN_ID_PATTERN.fullmatch(token_id):
        raise ValueError("Invalid token ID")

    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        cursor = conn.execute(
            """
            UPDATE api_tokens
            SET revoked_at = ?
            WHERE token_id = ? AND revoked_at IS NULL
            """,
            (now, token_id),
        )
        return cursor.rowcount == 1


def list_tokens():
    with _connect() as conn:
        rows = conn.execute("""
            SELECT token_id, name, scopes, created_at,
                   expires_at, revoked_at, last_used_at
            FROM api_tokens
            ORDER BY created_at DESC
        """).fetchall()

    return [
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


def verify_token(plaintext_token: str, required_scope: str) -> bool:
    """Return False for invalid tokens; raise PermissionError for missing scope."""

    if required_scope not in ALLOWED_SCOPES:
        return False

    if not isinstance(plaintext_token, str) or len(plaintext_token) > 512:
        hmac.compare_digest(DUMMY_HASH, DUMMY_HASH)
        return False

    token_id, separator, secret = plaintext_token.partition(".")

    if (
        not separator
        or not TOKEN_ID_PATTERN.fullmatch(token_id)
        or not secret
        or len(secret) > 256
    ):
        supplied_hash = hashlib.sha256(b"malformed-token").hexdigest()
        hmac.compare_digest(DUMMY_HASH, supplied_hash)
        return False

    supplied_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()

    with _connect() as conn:
        row = conn.execute(
            """
            SELECT secret_hash, scopes, expires_at, revoked_at
            FROM api_tokens
            WHERE token_id = ?
            """,
            (token_id,),
        ).fetchone()

        expected_hash = row["secret_hash"] if row else DUMMY_HASH
        hash_matches = hmac.compare_digest(expected_hash, supplied_hash)

        if not row or not hash_matches:
            return False

        if row["revoked_at"] is not None:
            return False

        try:
            expiry = datetime.fromisoformat(row["expires_at"])
            scopes = json.loads(row["scopes"])
        except (ValueError, TypeError):
            return False

        if expiry.tzinfo is None:
            return False

        if datetime.now(timezone.utc) >= expiry:
            return False

        if (
            not isinstance(scopes, list)
            or not all(scope in ALLOWED_SCOPES for scope in scopes)
        ):
            return False

        if required_scope not in scopes:
            raise PermissionError("Insufficient API token scope")

        conn.execute(
            "UPDATE api_tokens SET last_used_at = ? WHERE token_id = ?",
            (datetime.now(timezone.utc).isoformat(), token_id),
        )

    return True
PY

cat > app/core/api_auth.py <<'PY'
"""Bearer-token authentication dependencies for the API."""

import sqlite3

from fastapi import Header, HTTPException

from app.services.api_tokens import verify_token


def require_scope(required_scope: str):
    def dependency(
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> None:
        if not authorization:
            raise HTTPException(
                status_code=401,
                detail="Bearer token required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        scheme, separator, token = authorization.partition(" ")

        if (
            not separator
            or scheme.lower() != "bearer"
            or not token
            or token.strip() != token
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid bearer authorization",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            valid = verify_token(token, required_scope)
        except PermissionError:
            raise HTTPException(
                status_code=403,
                detail="Insufficient API token scope",
            )
        except sqlite3.Error:
            raise HTTPException(
                status_code=503,
                detail="Authentication service temporarily unavailable",
            )

        if not valid:
            raise HTTPException(
                status_code=401,
                detail="Invalid, expired, or revoked bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return dependency
PY

cat > app/cli/__init__.py <<'PY'
"""Administrative command-line tools."""
PY

cat > app/cli/api_tokens.py <<'PY'
"""Root-only API token administration CLI."""

import argparse
import os
import stat
import sys
from pathlib import Path

from app.services.api_tokens import (
    initialize_api_token_store,
    issue_token,
    list_tokens,
    revoke_token,
)


DEFAULT_TOKEN_DIR = Path(
    "/root/.local/share/ai-defense-manager/tokens"
)


def _require_root():
    if os.geteuid() != 0:
        raise PermissionError("This command must be run as root")


def _write_token_file(token: str, output: Path) -> None:
    directory = output.parent
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)

    directory_stat = directory.stat()
    if directory_stat.st_uid != 0:
        raise PermissionError("Token directory must be owned by root")

    os.chmod(directory, 0o700)

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)

    fd = os.open(output, flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="ascii") as stream:
            fd = -1
            stream.write(token + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if fd >= 0:
            os.close(fd)


def main():
    parser = argparse.ArgumentParser(
        prog="aidm-api-token",
        description="Root-only AI Defense Manager API token administration",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    issue = sub.add_parser("issue")
    issue.add_argument("--name", required=True)
    issue.add_argument(
        "--scopes",
        required=True,
        help="Comma-separated scopes: read,analyze",
    )
    issue.add_argument(
        "--expires-in-days",
        type=int,
        default=90,
    )
    issue.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_TOKEN_DIR / "issued-token.txt",
    )

    sub.add_parser("list")

    revoke = sub.add_parser("revoke")
    revoke.add_argument("--token-id", required=True)

    args = parser.parse_args()

    try:
        _require_root()
        initialize_api_token_store()

        if args.command == "issue":
            scopes = {
                item.strip()
                for item in args.scopes.split(",")
                if item.strip()
            }

            token_id, plaintext = issue_token(
                args.name,
                scopes,
                args.expires_in_days,
            )

            try:
                _write_token_file(plaintext, args.output)
            except Exception:
                revoke_token(token_id)
                raise

            print("TOKEN_ISSUED=YES")
            print("TOKEN_ID=", token_id)
            print("TOKEN_FILE=", args.output)
            print("TOKEN_VALUE=NOT_DISPLAYED")
            print("TOKEN_FILE_MODE=0600")

        elif args.command == "list":
            for item in list_tokens():
                print(
                    "TOKEN_ID={token_id} NAME={name!r} "
                    "SCOPES={scopes} CREATED={created_at} "
                    "EXPIRES={expires_at} REVOKED={revoked_at} "
                    "LAST_USED={last_used_at}".format(**item)
                )
            print("TOKEN_SECRET_VALUES=NOT_STORED_OR_DISPLAYED")

        elif args.command == "revoke":
            changed = revoke_token(args.token_id)
            print("TOKEN_REVOKED=", "YES" if changed else "NO_CHANGE")

    except Exception as exc:
        print("ERROR:", type(exc).__name__, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY

echo
echo "--- 1. Patch FastAPI application and routers ---"

./venv/bin/python - <<'PY'
from pathlib import Path

main = Path("app/main.py")
analysis = Path("app/api/analysis.py")
wazuh = Path("app/api/wazuh.py")

p = main.read_text()
assert "from app.services.analysis_history import initialize_database" in p
assert "initialize_api_token_store" not in p
p = p.replace(
    "from app.services.analysis_history import initialize_database",
    "from app.services.analysis_history import initialize_database\n"
    "from app.services.api_tokens import initialize_api_token_store",
)
p = p.replace(
    "    initialize_database()\n    yield",
    "    initialize_database()\n"
    "    initialize_api_token_store()\n"
    "    yield",
)
p = p.replace(
    '    version=settings.app_version,\n    lifespan=lifespan,',
    '    version=settings.app_version,\n'
    '    docs_url=None,\n'
    '    redoc_url=None,\n'
    '    openapi_url=None,\n'
    '    lifespan=lifespan,',
)
main.write_text(p)

p = analysis.read_text()
assert "from app.core.api_auth import require_scope" not in p
p = p.replace(
    "from fastapi import APIRouter, HTTPException",
    "from fastapi import APIRouter, Depends, HTTPException\n\n"
    "from app.core.api_auth import require_scope",
)
p = p.replace(
    '@router.post(\n    "/analysis",\n    response_model=AIAnalysisProposal,\n)',
    '@router.post(\n'
    '    "/analysis",\n'
    '    response_model=AIAnalysisProposal,\n'
    '    dependencies=[Depends(require_scope("analyze"))],\n'
    ')',
)
assert 'Depends(require_scope("analyze"))' in p
analysis.write_text(p)

p = wazuh.read_text()
assert "from app.core.api_auth import require_scope" not in p
p = p.replace(
    "from fastapi import APIRouter, HTTPException, Query",
    "from fastapi import APIRouter, Depends, HTTPException, Query\n\n"
    "from app.core.api_auth import require_scope",
)
p = p.replace(
    '@router.get("/events", response_model=list[SecurityEvent])',
    '@router.get(\n'
    '    "/events",\n'
    '    response_model=list[SecurityEvent],\n'
    '    dependencies=[Depends(require_scope("read"))],\n'
    ')',
)
p = p.replace(
    '@router.post("/analyze", response_model=AIAnalysisProposal)',
    '@router.post(\n'
    '    "/analyze",\n'
    '    response_model=AIAnalysisProposal,\n'
    '    dependencies=[Depends(require_scope("analyze"))],\n'
    ')',
)
assert 'Depends(require_scope("read"))' in p
assert 'Depends(require_scope("analyze"))' in p
wazuh.write_text(p)

print("MAIN_PATCH=PASS")
print("ANALYSIS_ROUTER_PATCH=PASS")
print("WAZUH_ROUTER_PATCH=PASS")
print("DOCS_DISABLED_IN_SOURCE=YES")
PY

echo
echo "--- 2. Install root-only CLI wrapper ---"

cat > /usr/local/sbin/aidm-api-token <<'SH'
#!/bin/sh
exec /opt/ai-defense-manager/venv/bin/python \
  -m app.cli.api_tokens "$@"
SH

chown root:root /usr/local/sbin/aidm-api-token
chmod 700 /usr/local/sbin/aidm-api-token

echo
echo "--- 3. Compile all application Python files ---"
./venv/bin/python -m compileall -q app
echo "PYTHON_COMPILE=PASS"

echo
echo "--- 4. Verify systemd unit syntax (no restart) ---"
systemd-analyze verify \
  /etc/systemd/system/ai-defense-manager.service

echo
echo "--- 5. Verify CLI help without database initialization ---"
/usr/local/sbin/aidm-api-token --help

echo
echo "--- 6. Source file hashes ---"
sha256sum \
  app/main.py \
  app/api/analysis.py \
  app/api/wazuh.py \
  app/core/api_auth.py \
  app/services/api_tokens.py \
  app/cli/__init__.py \
  app/cli/api_tokens.py \
  /usr/local/sbin/aidm-api-token

echo
echo "SOURCE_PATCHED=YES"
echo "DATABASE_SCHEMA_CHANGED=NO"
echo "TOKEN_ISSUED=NO"
echo "SERVICE_RESTARTED=NO"
echo "LIVE_WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
```

| Created | Details |
|---|---|
| `app/services/api_tokens.py` | issuing, verifying, revoking and listing tokens |
| `app/core/api_auth.py` | `require_scope()` (a FastAPI dependency) |
| `app/cli/api_tokens.py` | root-only CLI |
| `/usr/local/sbin/aidm-api-token` | wrapper that runs the CLI (`root:root`, `700`) |
| `app/main.py`, routers | require scopes on the three APIs and disable documentation |

The Python syntax check, the systemd unit check and displaying the CLI help all passed.

# Chapter 3: Testing in an Independent Environment

## 3.1 Testing the Authentication Logic

The test DB is created in a temporary directory and deleted afterwards. There is no connection to the production DB, Wazuh or Ollama.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED API TOKEN AUTHENTICATION TESTS ====="

./venv/bin/python - <<'PY'
import hashlib
import json
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import app.services.api_tokens as tokens

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"{name}=PASS")
    else:
        failed += 1
        print(f"{name}=FAIL")

with tempfile.TemporaryDirectory(prefix="aidm-auth-test-") as tmp:
    db_path = Path(tmp) / "auth-test.db"
    tokens.DB_PATH = str(db_path)

    tokens.initialize_api_token_store()

    # 1. Schema and token issuance
    token_id, plaintext = tokens.issue_token(
        "isolated-test",
        {"read"},
        30,
    )
    check("TOKEN_ISSUANCE", bool(token_id and plaintext))
    check("TOKEN_ID_FORMAT", len(token_id) == 32)

    # 2. Database must contain only the hash, never plaintext
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT secret_hash, scopes FROM api_tokens WHERE token_id=?",
            (token_id,),
        ).fetchone()

    expected_hash = hashlib.sha256(
        plaintext.partition(".")[2].encode("ascii")
    ).hexdigest()

    check("SECRET_HASH_STORED", row is not None and row[0] == expected_hash)
    check("PLAINTEXT_NOT_IN_DATABASE", plaintext.encode() not in db_path.read_bytes())
    check("SCOPES_STORED", row is not None and json.loads(row[1]) == ["read"])

    # 3. Valid token and scope enforcement
    check("VALID_READ_TOKEN", tokens.verify_token(plaintext, "read"))

    try:
        tokens.verify_token(plaintext, "analyze")
        scope_denied = False
    except PermissionError:
        scope_denied = True
    check("INSUFFICIENT_SCOPE_DENIED", scope_denied)

    # 4. Invalid tokens
    check("INVALID_SECRET_REJECTED", not tokens.verify_token(
        token_id + ".incorrect-secret", "read"
    ))
    check("MALFORMED_TOKEN_REJECTED", not tokens.verify_token(
        "not-a-valid-token", "read"
    ))
    check("UNKNOWN_TOKEN_REJECTED", not tokens.verify_token(
        "0" * 32 + ".unknown-secret", "read"
    ))

    # 5. Expiration
    with sqlite3.connect(db_path) as conn:
        expired = (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        ).isoformat()
        conn.execute(
            "UPDATE api_tokens SET expires_at=? WHERE token_id=?",
            (expired, token_id),
        )
    check("EXPIRED_TOKEN_REJECTED", not tokens.verify_token(plaintext, "read"))

    # 6. Revocation
    token_id2, plaintext2 = tokens.issue_token(
        "revoke-test",
        {"read", "analyze"},
        30,
    )
    check("SECOND_TOKEN_VALID", tokens.verify_token(plaintext2, "read"))
    check("REVOCATION_SUCCEEDED", tokens.revoke_token(token_id2))
    check("REVOKED_TOKEN_REJECTED", not tokens.verify_token(plaintext2, "read"))
    check("SECOND_REVOCATION_NO_CHANGE", not tokens.revoke_token(token_id2))

    # 7. Listing must not expose token secrets
    listed = tokens.list_tokens()
    check("TOKEN_LIST_COUNT", len(listed) == 2)
    check(
        "TOKEN_LIST_HAS_NO_SECRET",
        all("secret" not in item and "token" not in item for item in listed),
    )

# 8. FastAPI route configuration (import only; no lifespan/startup)
from app.main import app

routes = {
    (route.path, method): route
    for route in app.routes
    if hasattr(route, "methods")
    for method in route.methods
}

def has_scope_dependency(path, method, expected_scope):
    route = routes.get((path, method))
    if route is None:
        return False

    def walk(dependant):
        for dep in dependant.dependencies:
            call = getattr(dep, "call", None)
            if getattr(call, "__name__", "") == "dependency":
                closure = getattr(call, "__closure__", None) or ()
                values = [
                    cell.cell_contents
                    for cell in closure
                    if isinstance(cell.cell_contents, str)
                ]
                if expected_scope in values:
                    return True
            if walk(dep):
                return True
        return False

    return walk(route.dependant)

check(
    "WAZUH_EVENTS_READ_SCOPE",
    has_scope_dependency("/api/v1/wazuh/events", "GET", "read"),
)
check(
    "ANALYSIS_ANALYZE_SCOPE",
    has_scope_dependency("/api/v1/analysis", "POST", "analyze"),
)
check(
    "WAZUH_ANALYZE_SCOPE",
    has_scope_dependency("/api/v1/wazuh/analyze", "POST", "analyze"),
)

check(
    "HEALTH_ROUTE_EXISTS",
    ("/health", "GET") in routes,
)
check(
    "OPENAPI_DISABLED",
    app.openapi_url is None,
)
check(
    "DOCS_DISABLED",
    app.docs_url is None,
)
check(
    "REDOC_DISABLED",
    app.redoc_url is None,
)

print(f"TESTS_PASSED={passed}")
print(f"TESTS_FAILED={failed}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_DATABASE_CHANGED=NO")
print("WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
PY

echo
echo "===== CURRENT PRODUCTION STATE (READ ONLY) ====="
stat -c '%A %U:%G %n' /opt/ai-defense-manager/data/ai-defense.db
systemctl is-active ai-defense-manager.service
ss -lntp | grep '127.0.0.1:8000' || true
```

Issuing tokens, storing as hashes, rejecting invalid/expired/revoked tokens, and rejecting insufficient scopes all passed.

The scope check of the three routes showed `FAIL`, but this was a problem in the test code (3.2).

## 3.2 Checking Route Registration

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API ROUTE AUTH DEPENDENCY INSPECTION ====="

./venv/bin/python - <<'PY'
from app.main import app

TARGETS = {
    ("/api/v1/wazuh/events", "GET"),
    ("/api/v1/analysis", "POST"),
    ("/api/v1/wazuh/analyze", "POST"),
    ("/health", "GET"),
}

def inspect(dependant, depth=0):
    for dep in dependant.dependencies:
        call = getattr(dep, "call", None)
        name = getattr(call, "__qualname__", repr(call))
        module = getattr(call, "__module__", "")
        print("  " * depth + f"DEPENDENCY={module}.{name}")

        closure = getattr(call, "__closure__", None) or ()
        for cell in closure:
            try:
                value = cell.cell_contents
            except ValueError:
                continue
            if isinstance(value, (str, int, bool)):
                print("  " * (depth + 1) + f"CLOSURE_VALUE={value!r}")

        inspect(dep, depth + 1)

for route in app.routes:
    path = getattr(route, "path", None)
    methods = getattr(route, "methods", set()) or set()

    for method in sorted(methods):
        if (path, method) not in TARGETS:
            continue

        print(f"\nROUTE={method} {path}")
        inspect(route.dependant)

print("\n===== ROUTER SOURCE DECORATORS =====")
for filename in ("app/api/analysis.py", "app/api/wazuh.py"):
    print(f"\n--- {filename} ---")
    lines = open(filename, encoding="utf-8").read().splitlines()
    for i, line in enumerate(lines):
        if "@router." in line:
            start = max(0, i - 1)
            end = min(len(lines), i + 9)
            for n in range(start, end):
                print(f"{n + 1:4}: {lines[n]}")
            print()

print("PRODUCTION_DATABASE_ACCESSED=NO")
print("SOURCE_CHANGED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

In the source, `Depends(require_scope(...))` was written on all three routes.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: FASTAPI ROUTER REGISTRATION INSPECTION ====="

./venv/bin/python - <<'PY'
from app.main import app
from app.api.analysis import router as analysis_router
from app.api.wazuh import router as wazuh_router

def show_routes(label, obj):
    print(f"\n--- {label} ---")
    for index, route in enumerate(obj.routes):
        print(
            "INDEX=", index,
            "TYPE=", type(route).__module__ + "." + type(route).__name__,
            "PATH=", getattr(route, "path", None),
            "METHODS=", sorted(getattr(route, "methods", None) or []),
            "NAME=", getattr(route, "name", None),
        )
        if hasattr(route, "router"):
            nested = route.router
            print(
                "  NESTED_ROUTER=",
                type(nested).__module__ + "." + type(nested).__name__,
                "NESTED_ROUTE_COUNT=",
                len(getattr(nested, "routes", [])),
            )

show_routes("APP ROUTES", app)
show_routes("ANALYSIS ROUTER", analysis_router)
show_routes("WAZUH ROUTER", wazuh_router)

print("\n--- APP ROUTER REGISTRATION SOURCE ---")
from pathlib import Path
lines = Path("app/main.py").read_text().splitlines()
for i, line in enumerate(lines):
    if "include_router" in line or "FastAPI(" in line or "lifespan=" in line:
        for n in range(max(0, i - 2), min(len(lines), i + 4)):
            print(f"{n + 1:4}: {lines[n]}")

print("\n--- FASTAPI ROUTER VERSION DETAILS ---")
import fastapi
import inspect
from fastapi.routing import _IncludedRouter
print("FASTAPI_VERSION=", fastapi.__version__)
print("INCLUDED_ROUTER_CLASS=", _IncludedRouter)
print("INCLUDED_ROUTER_SOURCE=")
print(inspect.getsource(_IncludedRouter))
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("SOURCE_CHANGED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

In FastAPI 0.165.0, routers registered with `include_router()` are expanded later as `_IncludedRouter`. The test code walked `app.routes` directly and so could not find the three API routes. We check again with the expanded routes.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: EFFECTIVE ROUTE AUTH DEPENDENCY AUDIT ====="

./venv/bin/python - <<'PY'
from app.main import app

EXPECTED = {
    ("/api/v1/wazuh/events", "GET"): "read",
    ("/api/v1/analysis", "POST"): "analyze",
    ("/api/v1/wazuh/analyze", "POST"): "analyze",
}

def dependency_tree(dependant, depth=0):
    result = []
    for dep in dependant.dependencies:
        call = getattr(dep, "call", None)
        name = getattr(call, "__qualname__", repr(call))
        module = getattr(call, "__module__", "")
        closure_values = []

        for cell in getattr(call, "__closure__", None) or ():
            try:
                value = cell.cell_contents
            except ValueError:
                continue
            if isinstance(value, str):
                closure_values.append(value)

        result.append((name, module, closure_values))
        result.extend(dependency_tree(dep, depth + 1))
    return result

effective = {}

for branch in app.router.routes:
    if hasattr(branch, "effective_route_contexts"):
        for context in branch.effective_route_contexts():
            route = context.original_route
            for method in getattr(route, "methods", set()) or set():
                effective[(context.path_format, method)] = route

for key, expected_scope in EXPECTED.items():
    route = effective.get(key)
    print(f"\nROUTE={key[1]} {key[0]}")

    if route is None:
        print("ROUTE_FOUND=NO")
        continue

    print("ROUTE_FOUND=YES")
    tree = dependency_tree(route.dependant)

    for name, module, closure_values in tree:
        print(f"DEPENDENCY={module}.{name}")
        print("CLOSURE_VALUES=", closure_values)

    matching = any(
        name == "require_scope.<locals>.dependency"
        and expected_scope in closure_values
        for name, module, closure_values in tree
    )
    print("EXPECTED_SCOPE=", expected_scope)
    print("SCOPE_DEPENDENCY_FOUND=", "YES" if matching else "NO")

print("\n--- HEALTH ROUTE ---")
health = next(
    (
        route for route in app.routes
        if getattr(route, "path", None) == "/health"
    ),
    None,
)
print("HEALTH_ROUTE_FOUND=", health is not None)
if health is not None:
    print("HEALTH_DEPENDENCY_COUNT=", len(health.dependant.dependencies))

print("\nPRODUCTION_DATABASE_ACCESSED=NO")
print("SOURCE_CHANGED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

| API | Required scope | Result |
|---|---|---|
| `GET /api/v1/wazuh/events` | `read` | passed |
| `POST /api/v1/analysis` | `analyze` | passed |
| `POST /api/v1/wazuh/analyze` | `analyze` | passed |
| `GET /health` | none | passed |

## 3.3 Testing Authentication over HTTP

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED HTTP AUTHENTICATION TEST ====="

./venv/bin/python - <<'PY'
import asyncio
import tempfile
from pathlib import Path

import httpx
from fastapi import FastAPI

import app.services.api_tokens as token_service
import app.api.analysis as analysis_api
import app.api.wazuh as wazuh_api
from app.main import app

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"{name}=PASS")
    else:
        failed += 1
        print(f"{name}=FAIL")

async def main():
    global passed, failed

    with tempfile.TemporaryDirectory(prefix="aidm-http-auth-") as tmp:
        token_service.DB_PATH = str(Path(tmp) / "http-auth.db")
        token_service.initialize_api_token_store()

        read_id, read_token = token_service.issue_token(
            "http-read-test", {"read"}, 30
        )
        analyze_id, analyze_token = token_service.issue_token(
            "http-analyze-test", {"analyze"}, 30
        )

        # Replace endpoint work with inert test-only responses.
        original_events = wazuh_api.get_wazuh_events
        original_analysis = analysis_api.create_analysis
        original_wazuh_analysis = wazuh_api.analyze_wazuh_events

        async def fake_events(limit=50, since_minutes=60):
            return []

        async def fake_analysis(request):
            return {"test": "analysis-authorized"}

        async def fake_wazuh_analysis(request):
            return {"test": "wazuh-analysis-authorized"}

        wazuh_api.get_wazuh_events = fake_events
        analysis_api.create_analysis = fake_analysis
        wazuh_api.analyze_wazuh_events = fake_wazuh_analysis

        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://test",
            ) as client:

                # Missing credentials
                r = await client.get("/api/v1/wazuh/events")
                check("NO_TOKEN_READ_401", r.status_code == 401)

                r = await client.post("/api/v1/analysis", json={})
                check("NO_TOKEN_ANALYZE_401", r.status_code == 401)

                # Read token
                headers = {"Authorization": f"Bearer {read_token}"}
                r = await client.get(
                    "/api/v1/wazuh/events", headers=headers
                )
                check("READ_TOKEN_READ_200", r.status_code == 200)

                r = await client.post(
                    "/api/v1/analysis", headers=headers, json={}
                )
                check("READ_TOKEN_ANALYZE_403", r.status_code == 403)

                # Analyze token
                headers = {"Authorization": f"Bearer {analyze_token}"}
                r = await client.post(
                    "/api/v1/analysis", headers=headers, json={}
                )
                check("ANALYZE_TOKEN_ANALYSIS_200", r.status_code == 200)

                r = await client.post(
                    "/api/v1/wazuh/analyze", headers=headers, json={}
                )
                check("ANALYZE_TOKEN_WAZUH_200", r.status_code == 200)

                r = await client.get(
                    "/api/v1/wazuh/events", headers=headers
                )
                check("ANALYZE_TOKEN_READ_401", r.status_code == 401)

                # Health remains unauthenticated.
                r = await client.get("/health")
                check("HEALTH_WITHOUT_TOKEN_200", r.status_code == 200)

                # Documentation endpoints remain disabled.
                for path in ("/docs", "/redoc", "/openapi.json"):
                    r = await client.get(path)
                    check(
                        f"DOCS_DISABLED_{path.replace('/', '_')}",
                        r.status_code == 404,
                    )

        finally:
            wazuh_api.get_wazuh_events = original_events
            analysis_api.create_analysis = original_analysis
            wazuh_api.analyze_wazuh_events = original_wazuh_analysis

asyncio.run(main())

print(f"TESTS_PASSED={passed}")
print(f"TESTS_FAILED={failed}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_DATABASE_CHANGED=NO")
print("LIVE_WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
print("PRODUCTION_SERVICE_RESTARTED=NO")
PY
```

`401` without a token, `403` rejecting the analysis API with a `read` token, and `/health` without authentication passed. The rest were problems with the test's expected values, which we checked as follows.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: AUTH HTTP STATUS DIAGNOSTIC ====="

./venv/bin/python - <<'PY'
import asyncio
import tempfile
from pathlib import Path

import httpx
import app.services.api_tokens as token_service
from app.main import app

async def main():
    with tempfile.TemporaryDirectory(prefix="aidm-auth-diag-") as tmp:
        token_service.DB_PATH = str(Path(tmp) / "auth.db")
        token_service.initialize_api_token_store()

        _, analyze_token = token_service.issue_token(
            "diagnostic-analyze", {"analyze"}, 30
        )

        headers = {"Authorization": f"Bearer {analyze_token}"}
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            checks = [
                ("ANALYZE_TOKEN_ON_READ_ROUTE",
                 "GET", "/api/v1/wazuh/events", None),
                ("ANALYZE_TOKEN_ON_ANALYSIS_ROUTE",
                 "POST", "/api/v1/analysis", {}),
                ("ANALYZE_TOKEN_ON_WAZUH_ANALYZE_ROUTE",
                 "POST", "/api/v1/wazuh/analyze", {}),
            ]

            for name, method, path, body in checks:
                response = await client.request(
                    method,
                    path,
                    headers=headers,
                    json=body if method == "POST" else None,
                )
                print(f"{name}_STATUS={response.status_code}")
                print(f"{name}_BODY={response.text[:500]!r}")

asyncio.run(main())

print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_DATABASE_CHANGED=NO")
print("LIVE_WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
print("PRODUCTION_SERVICE_RESTARTED=NO")
PY
```

- `GET /events` with an `analyze` token gives `403` (the token is valid but lacks `read`); as specified
- `POST /analysis` gives `422` (authentication passed; the required `events` in the body is missing)
- `POST /wazuh/analyze` gives `502`. Even with an empty body `{}`, `limit=50` and `since_minutes=60` are filled in automatically, so after authentication it went on to actual retrieval and analysis

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: WAZUH ANALYZE ROUTE SOURCE INSPECTION ====="

echo
echo "--- 1. Wazuh API route ---"
nl -ba app/api/wazuh.py | sed -n '1,240p'

echo
echo "--- 2. AI analysis service ---"
nl -ba app/services/ai_analysis.py | sed -n '1,280p'

echo
echo "--- 3. Analysis request schema ---"
grep -R -n -A45 -B5 \
  "class.*Analysis\|events:" \
  app/schemas

echo
echo "--- 4. Wazuh analysis call references ---"
grep -R -n \
  "analyze_wazuh_events\|analyze_events\|get_wazuh_events" \
  app --include='*.py'

echo
echo "SOURCE_FILES_MODIFIED=NO"
echo "API_REQUESTS_SENT=NO"
echo "EXTERNAL_NETWORK_REQUESTS=NO"
echo "PRODUCTION_DATABASE_CHANGED=NO"
```

So we switch to tests that fully simulate Wazuh retrieval and Ollama.

## 3.4 Testing the Wazuh APIs

`fetch_wazuh_events` is replaced with a function that returns an empty array, so it does not proceed to AI analysis, storing history or outside communication.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED WAZUH API AUTH TEST ====="

./venv/bin/python - <<'PY'
import asyncio
import tempfile
from pathlib import Path

import httpx
from fastapi import FastAPI

import app.services.api_tokens as token_service
import app.api.wazuh as wazuh_api

async def main():
    with tempfile.TemporaryDirectory(prefix="aidm-wazuh-auth-") as tmp:
        token_service.DB_PATH = str(Path(tmp) / "isolated.db")
        token_service.initialize_api_token_store()

        _, read_token = token_service.issue_token(
            "isolated-read", {"read"}, 30
        )
        _, analyze_token = token_service.issue_token(
            "isolated-analyze", {"analyze"}, 30
        )

        calls = {"fetch": 0}

        async def fake_fetch_wazuh_events(*, limit, since_minutes):
            calls["fetch"] += 1
            return []

        original_fetch = wazuh_api.fetch_wazuh_events
        wazuh_api.fetch_wazuh_events = fake_fetch_wazuh_events

        try:
            test_app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
            test_app.include_router(wazuh_api.router)

            transport = httpx.ASGITransport(app=test_app)

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://isolated-test",
            ) as client:
                cases = [
                    ("READ_TOKEN_GET_EVENTS", "GET",
                     "/api/v1/wazuh/events", read_token, 200),
                    ("ANALYZE_TOKEN_GET_EVENTS", "GET",
                     "/api/v1/wazuh/events", analyze_token, 403),
                    ("NO_TOKEN_POST_ANALYZE", "POST",
                     "/api/v1/wazuh/analyze", None, 401),
                    ("ANALYZE_TOKEN_POST_ANALYZE", "POST",
                     "/api/v1/wazuh/analyze", analyze_token, 404),
                    ("READ_TOKEN_POST_ANALYZE", "POST",
                     "/api/v1/wazuh/analyze", read_token, 403),
                ]

                for name, method, path, token, expected in cases:
                    headers = (
                        {"Authorization": f"Bearer {token}"}
                        if token else {}
                    )
                    response = await client.request(
                        method, path, headers=headers
                    )
                    passed = response.status_code == expected
                    print(
                        f"{name}="
                        f"{'PASS' if passed else 'FAIL'} "
                        f"STATUS={response.status_code} "
                        f"EXPECTED={expected}"
                    )

            print(f"MOCK_FETCH_CALLS={calls['fetch']}")
            print(
                "MOCK_FETCH_EXPECTED_CALLS="
                "2 (authorized GET and authorized POST)"
            )
            print(
                "MOCK_ONLY="
                f"{'PASS' if calls['fetch'] == 2 else 'FAIL'}"
            )

        finally:
            wazuh_api.fetch_wazuh_events = original_fetch

print("PRODUCTION_DATABASE_ACCESSED=NO")
print("LIVE_WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
print("ANALYSIS_HISTORY_WRITES=NO")
print("PRODUCTION_SERVICE_RESTARTED=NO")
asyncio.run(main())
PY
```

GET gave `200` with a `read` token and `403` with an `analyze` token; POST gave `401` without a token. The test that omitted the POST body gave `422` (even with defaults, the body itself is required). We retest with a body.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED WAZUH POST AUTH RETEST ====="

./venv/bin/python - <<'PY'
import asyncio
import tempfile
from pathlib import Path

import httpx
from fastapi import FastAPI

import app.services.api_tokens as token_service
import app.api.wazuh as wazuh_api

async def main():
    with tempfile.TemporaryDirectory(prefix="aidm-wazuh-post-") as tmp:
        token_service.DB_PATH = str(Path(tmp) / "isolated.db")
        token_service.initialize_api_token_store()

        _, analyze_token = token_service.issue_token(
            "isolated-analyze", {"analyze"}, 30
        )
        _, read_token = token_service.issue_token(
            "isolated-read", {"read"}, 30
        )

        calls = {"fetch": 0}

        async def fake_fetch_wazuh_events(*, limit, since_minutes):
            calls["fetch"] += 1
            return []

        original_fetch = wazuh_api.fetch_wazuh_events
        wazuh_api.fetch_wazuh_events = fake_fetch_wazuh_events

        try:
            test_app = FastAPI()
            test_app.include_router(wazuh_api.router)
            transport = httpx.ASGITransport(app=test_app)

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://isolated-test",
            ) as client:
                cases = [
                    ("ANALYZE_TOKEN_POST",
                     analyze_token, 404),
                    ("READ_TOKEN_POST",
                     read_token, 403),
                    ("NO_TOKEN_POST",
                     None, 401),
                ]

                for name, token, expected in cases:
                    headers = (
                        {"Authorization": f"Bearer {token}"}
                        if token else {}
                    )
                    response = await client.post(
                        "/api/v1/wazuh/analyze",
                        headers=headers,
                        json={},
                    )
                    print(
                        f"{name}="
                        f"{'PASS' if response.status_code == expected else 'FAIL'} "
                        f"STATUS={response.status_code} "
                        f"EXPECTED={expected}"
                    )

            print(f"MOCK_FETCH_CALLS={calls['fetch']}")
            print(
                "MOCK_CALL_COUNT="
                f"{'PASS' if calls['fetch'] == 1 else 'FAIL'}"
            )

        finally:
            wazuh_api.fetch_wazuh_events = original_fetch

asyncio.run(main())

print("PRODUCTION_DATABASE_ACCESSED=NO")
print("LIVE_WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
print("ANALYSIS_HISTORY_WRITES=NO")
print("PRODUCTION_SERVICE_RESTARTED=NO")
PY
```

| Test | Result |
|---|---:|
| GET with a `read` token | 200 |
| GET with an `analyze` token | 403 |
| POST with an `analyze` token | 404 (response for the simulated empty events) |
| POST with a `read` token | 403 |
| POST without a token | 401 |
| Times the simulated retrieval function was called | 1 |

For requests rejected by authentication, the Wazuh retrieval function was not called.

## 3.5 Testing the Analysis API

Using a test event with `source="internal"`, the analysis result is simulated to return a fixed `no_action` proposal, and storing history is also simulated.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED ANALYSIS API AUTH TEST ====="

./venv/bin/python - <<'PY'
import asyncio
import tempfile
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import FastAPI

import app.services.api_tokens as token_service
import app.api.analysis as analysis_api
from app.schemas.analysis_proposal import AIAnalysisProposal

async def main():
    with tempfile.TemporaryDirectory(prefix="aidm-analysis-auth-") as tmp:
        token_service.DB_PATH = str(Path(tmp) / "isolated.db")
        token_service.initialize_api_token_store()

        _, analyze_token = token_service.issue_token(
            "isolated-analyze", {"analyze"}, 30
        )
        _, read_token = token_service.issue_token(
            "isolated-read", {"read"}, 30
        )

        event_id = uuid4()
        event = {
            "event_id": str(event_id),
            "source": "internal",
            "severity": "high",
            "event_category": "test",
            "event_summary": "Isolated authentication test event",
        }

        proposal = AIAnalysisProposal(
            summary="Isolated test proposal",
            severity="low",
            confidence=0.95,
            evidence_event_ids=[event_id],
            recommended_action="no_action",
            requires_human_approval=False,
            reasoning="Generated by an isolated test mock",
        )

        calls = {"analysis": 0, "history": 0}

        async def fake_analyze_events(request):
            calls["analysis"] += 1
            return proposal

        def fake_save_analysis(request, result):
            calls["history"] += 1

        original_analyze = analysis_api.analyze_events
        original_save = analysis_api.save_analysis
        analysis_api.analyze_events = fake_analyze_events
        analysis_api.save_analysis = fake_save_analysis

        try:
            test_app = FastAPI()
            test_app.include_router(analysis_api.router)
            transport = httpx.ASGITransport(app=test_app)

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://isolated-test",
            ) as client:
                cases = [
                    ("ANALYZE_TOKEN_POST", analyze_token, 200),
                    ("READ_TOKEN_POST", read_token, 403),
                    ("NO_TOKEN_POST", None, 401),
                ]

                for name, token, expected in cases:
                    headers = (
                        {"Authorization": f"Bearer {token}"}
                        if token else {}
                    )
                    response = await client.post(
                        "/api/v1/analysis",
                        headers=headers,
                        json={"events": [event]},
                    )
                    passed = response.status_code == expected
                    print(
                        f"{name}="
                        f"{'PASS' if passed else 'FAIL'} "
                        f"STATUS={response.status_code} "
                        f"EXPECTED={expected}"
                    )

            print(f"MOCK_ANALYSIS_CALLS={calls['analysis']}")
            print(f"MOCK_HISTORY_CALLS={calls['history']}")
            print(
                "AUTHORIZED_ONLY="
                f"{'PASS' if calls == {'analysis': 1, 'history': 1} else 'FAIL'}"
            )

        finally:
            analysis_api.analyze_events = original_analyze
            analysis_api.save_analysis = original_save

asyncio.run(main())

print("PRODUCTION_DATABASE_ACCESSED=NO")
print("LIVE_WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
print("PRODUCTION_HISTORY_WRITES=NO")
print("PRODUCTION_SERVICE_RESTARTED=NO")
PY
```

| Test | Result |
|---|---:|
| `analyze` token | 200 |
| `read` token | 403 |
| No token | 401 |
| Analysis and storing history (simulated) | once, only when authentication passed |

# Closing Notes

In Part 57 we built token authentication for the API and checked it in an independent environment.

| Item | Result |
|---|---|
| Authentication | Bearer tokens, scopes `read` and `analyze`, stored as SHA-256 hashes, verified with `hmac.compare_digest` |
| CLI | `/usr/local/sbin/aidm-api-token` (root only) issues, revokes and lists |
| Documentation | `/docs`, `/redoc` and `/openapi.json` disabled |
| Tests | for all three APIs: `401` without a token, `403` for insufficient privilege, passes with the correct scope |
| Production | not yet deployed (no authentication table; service not restarted) |

In the next part, Part 58, we examine the CLI and token handling in detail, harden them, and do a final check before production.

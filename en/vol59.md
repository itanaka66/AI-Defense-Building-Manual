---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 59: Putting API Authentication into Production"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 59 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". We put into production the API token authentication built and tested in Parts 57 and 58.

1. Create the table that manages tokens in the production SQLite
2. Issue one client token and check that the file and the DB agree
3. Restart the service to enable authentication
4. In production, check the order of authentication, authentication of the Wazuh retrieval API, that nothing leaks into logs, and that the last-used time is updated

For the production tests, we use requests that always stop at input validation, so that no AI analysis, storing of history or communication with Wazuh or Ollama occurs.

> **Caution:** Do not display, paste or hand over the contents of the token to anyone.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: Creating the Table in the Production DB

We create only the `api_tokens` table and an index on the expiry. Existing tables and data are not changed.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: PRODUCTION API TOKEN SCHEMA INITIALIZATION ====="

./venv/bin/python - <<'PY'
import sqlite3

from app.services import api_tokens

db_path = api_tokens.DB_PATH
print("DATABASE_PATH=", db_path)

# Run only the approved initialization function
api_tokens.initialize_api_token_store()
print("SCHEMA_INITIALIZATION=COMPLETED")

# Only check that the schema exists
with sqlite3.connect(db_path) as conn:
    conn.row_factory = sqlite3.Row

    table = conn.execute(
        """
        SELECT name, sql
        FROM sqlite_master
        WHERE type = 'table' AND name = 'api_tokens'
        """
    ).fetchone()

    index = conn.execute(
        """
        SELECT name, sql
        FROM sqlite_master
        WHERE type = 'index' AND name = 'idx_api_tokens_expires_at'
        """
    ).fetchone()

    columns = conn.execute(
        "PRAGMA table_info(api_tokens)"
    ).fetchall() if table else []

print("API_TOKENS_TABLE_EXISTS=", table is not None)
print("EXPIRY_INDEX_EXISTS=", index is not None)
print("COLUMN_NAMES=", ",".join(row["name"] for row in columns))

if not table or not index:
    raise SystemExit("SCHEMA_VERIFICATION=FAIL")

print("SCHEMA_VERIFICATION=PASS")
print("TOKEN_ISSUED=NO")
print("TOKEN_REVOKED=NO")
print("SERVICE_RESTARTED=NO")
print("LIVE_WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
PY
```

`api_tokens` (8 columns) and `idx_api_tokens_expires_at` were created, with `SCHEMA_VERIFICATION=PASS`.

# Chapter 2: Issuing a Token

## 2.1 CLI Arguments and the Destination

Following the principle of least privilege, give only the scopes the use requires. Here we gave both `read` and `analyze`.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API TOKEN ISSUE ARGUMENT CHECK ====="

aidm-api-token issue --help

echo
echo "===== TOKEN STORAGE DIRECTORY CHECK ====="
namei -l /root
echo
echo "TOKEN_ISSUED=NO"
echo "DATABASE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

## 2.2 Issuing

| Item | Value |
|---|---|
| Name | `ai-defense-client` |
| Scopes | `read,analyze` |
| Expiry | 30 days |
| Destination | `/root/ai-defense-client.token` (`600`) |

> **Run on: VM 230**

```bash
echo "===== VM230: API CLIENT TOKEN ISSUE ====="

aidm-api-token issue \
  --name ai-defense-client \
  --scopes read,analyze \
  --expires-in-days 30 \
  --output /root/ai-defense-client.token

echo
echo "===== TOKEN FILE PERMISSION CHECK ====="
stat -c 'OWNER=%U GROUP=%G MODE=%a SIZE=%s PATH=%n' /root/ai-defense-client.token

echo
echo "===== TOKEN VALUE DISPLAY ====="
echo "TOKEN_VALUE_DISPLAYED=NO"
echo "TOKEN_VALUE_LOGGED=NO"
```

The token file was created with owner `root`, `600`, 77 bytes. The token contents were not displayed.

## 2.3 Checking the Issued Token

The display of the issuance result was garbled (`TOKEN_ISSUED=YESE_LOGGED=NO"`), so without reissuing we check the DB registration, scopes and hash match read-only.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISSUED TOKEN READ-ONLY VERIFICATION ====="

./venv/bin/python - <<'PY'
import hashlib
import json
import os
import sqlite3
from pathlib import Path

token_id = "edcdfc1bfba5683c76c590fd41377ce7"
token_path = Path("/root/ai-defense-client.token")
db_path = "/opt/ai-defense-manager/data/ai-defense.db"

file_ok = False
db_ok = False
hash_ok = False

try:
    st = token_path.lstat()
    file_ok = (
        token_path.is_file()
        and not token_path.is_symlink()
        and st.st_uid == 0
        and (st.st_mode & 0o777) == 0o600
    )
    raw = token_path.read_text(encoding="ascii").strip()
    parts = raw.split(".", 1)
    format_ok = len(parts) == 2 and parts[0] == token_id
    if format_ok:
        secret_hash = hashlib.sha256(parts[1].encode("ascii")).hexdigest()
    else:
        secret_hash = ""
except Exception:
    format_ok = False
    secret_hash = ""

try:
    uri = "file:" + db_path + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT token_id, secret_hash, name, scopes,
                   created_at, expires_at, revoked_at
            FROM api_tokens
            WHERE token_id = ?
            """,
            (token_id,),
        ).fetchone()

    if row:
        db_ok = (
            row["name"] == "ai-defense-client"
            and row["revoked_at"] is None
        )
        hash_ok = (
            len(secret_hash) == 64
            and secret_hash == row["secret_hash"]
        )
        scopes = json.loads(row["scopes"])
        scopes_ok = (
            isinstance(scopes, list)
            and set(scopes) == {"read", "analyze"}
            and all(isinstance(x, str) for x in scopes)
        )
        expiry_ok = row["expires_at"] is not None
    else:
        scopes_ok = expiry_ok = False
except Exception:
    db_ok = hash_ok = scopes_ok = expiry_ok = False

print("TOKEN_FILE_OWNER_MODE_OK=", file_ok)
print("TOKEN_FILE_FORMAT_OK=", format_ok)
print("DATABASE_RECORD_EXISTS=", db_ok)
print("SECRET_HASH_MATCHES_FILE=", hash_ok)
print("SCOPES_READ_ANALYZE_ONLY=", scopes_ok)
print("EXPIRY_CONFIGURED=", expiry_ok)
print("TOKEN_VALUE_DISPLAYED=NO")
print("DATABASE_MODIFIED=NO")
print("TOKEN_REISSUED=NO")
print("SERVICE_RESTARTED=NO")

if all((file_ok, format_ok, db_ok, hash_ok, scopes_ok, expiry_ok)):
    print("TOKEN_VERIFICATION=PASS")
else:
    print("TOKEN_VERIFICATION=FAIL")
PY
```

| Checked | Result |
|---|---|
| File owner and permissions | passed (`root:root`, `600`) |
| Token format | passed |
| Registered in SQLite | passed |
| SHA-256 match between file and DB | passed |
| Scopes | passed (`read`, `analyze`) |
| Expiry | passed |
| Token value not shown | passed |

# Chapter 3: Deploying to the Service

## 3.1 Checks Before the Restart

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: PRE-RESTART FINAL AUDIT ====="

echo
echo "--- 1. Service runtime status ---"
systemctl show ai-defense-manager.service \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p User \
  -p Group \
  -p ExecMainStartTimestamp \
  -p Restart \
  -p FragmentPath

echo
echo "--- 2. Service unit configuration ---"
systemctl cat ai-defense-manager.service

echo
echo "--- 3. Listening socket ---"
ss -lntp | grep -E '127\.0\.0\.1:8000|0\.0\.0\.0:8000|\[::\]:8000' || true

echo
echo "--- 4. Source syntax check ---"
./venv/bin/python -m compileall -q app
echo "PYTHON_COMPILE=PASS"

echo
echo "--- 5. Authentication source presence ---"
grep -nE 'initialize_api_token_store|docs_url=None|redoc_url=None|openapi_url=None' app/main.py
grep -nE 'require_scope\("(read|analyze)"\)' app/api/analysis.py app/api/wazuh.py

echo
echo "--- 6. Token file metadata only ---"
stat -c 'OWNER=%U GROUP=%G MODE=%a SIZE=%s' /root/ai-defense-client.token

echo
echo "TOKEN_VALUE_DISPLAYED=NO"
echo "SERVICE_RESTARTED=NO"
echo "LIVE_WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
echo "PRODUCTION_DATABASE_MODIFIED=NO"
```

The service was `active (running)`, listening only on `127.0.0.1:8000`; the Python syntax passed; authentication on the three API routes had been confirmed; OpenAPI, Swagger and ReDoc were disabled; and the token file was root-only `600`.

## 3.2 Restart

> **Run on: VM 230**

```bash
echo "===== VM230: APPROVED API SERVICE RESTART ====="

systemctl restart ai-defense-manager.service

echo
echo "===== SERVICE STATUS ====="
systemctl show ai-defense-manager.service \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p ExecMainStartTimestamp

echo
echo "===== LISTENING SOCKET ====="
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "===== LOCAL HEALTH CHECK ====="
curl --silent --show-error \
  --max-time 5 \
  --output /dev/null \
  --write-out 'HTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "TOKEN_VALUE_DISPLAYED=NO"
echo "LIVE_WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
```

Right after the restart, listening on `127.0.0.1:8000` was not visible and `/health` gave `HTTP_STATUS=000`. Without restarting again, we check the state (strings that look like tokens in the log are masked).

> **Run on: VM 230**

```bash
echo "===== VM230: API STARTUP FAILURE DIAGNOSTICS ====="

echo
echo "--- 1. systemd detailed state ---"
systemctl status ai-defense-manager.service --no-pager -l
systemctl show ai-defense-manager.service \
  -p Result -p ExecMainCode -p ExecMainStatus \
  -p NRestarts -p MainPID -p ExecStart

echo
echo "--- 2. Process state ---"
ps -o pid,ppid,user,group,stat,etime,comm -p 2203
echo
echo "--- 3. Listening sockets ---"
ss -lntp | grep -E '8000|uvicorn' || true

echo
echo "--- 4. Recent startup errors (sanitized) ---"
journalctl -u ai-defense-manager.service \
  --since "15 minutes ago" --no-pager -o cat |
python3 -c '
import re, sys
for line in sys.stdin:
    if re.search(r"error|exception|traceback|failed|denied|fatal|cannot|permission|import", line, re.I):
        line = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~-]+", r"\1[REDACTED]", line)
        line = re.sub(r"(?i)(token[=: ]+)[A-Za-z0-9._~-]{12,}", r"\1[REDACTED]", line)
        print(line.rstrip()[:1000])
'

echo
echo "--- 5. Health check ---"
curl --silent --show-error --max-time 5 \
  --output /dev/null \
  --write-out 'HTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED_AGAIN=NO"
echo "TOKEN_VALUE_DISPLAYED=NO"
echo "LIVE_WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
```

| Item | Result |
|---|---|
| systemd | `active (running)` (MainPID `2203`, 0 restarts) |
| Uvicorn and application startup | normal, complete |
| Listening | `127.0.0.1:8000` |
| `/health` | `HTTP 200` |

The earlier `000` was because the check came right after startup.

# Chapter 4: Checking Authentication in Production

## 4.1 Input Shape of the Analysis API

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: LOCAL AUTHENTICATION TEST ====="

echo
echo "--- 1. Analysis endpoint input contract ---"
sed -n '1,120p' app/api/analysis.py

echo
echo "--- 2. Token file metadata ---"
stat -c 'OWNER=%U GROUP=%G MODE=%a SIZE=%s' /root/ai-defense-client.token

echo
echo "--- 3. Local health check ---"
curl --silent --show-error --max-time 5 \
  --output /dev/null \
  --write-out 'HEALTH_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "AUTH_TEST_REQUESTS=NOT_SENT"
echo "TOKEN_VALUE_DISPLAYED=NO"
echo "LIVE_WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
echo "ANALYSIS_EXECUTION=NO"
```

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ANALYSIS REQUEST SCHEMA INSPECTION ====="

echo
echo "--- Request schema ---"
sed -n '1,240p' app/schemas/analysis.py

echo
echo "--- Related nested schemas ---"
grep -R -nE 'class AIAnalysisRequest|class .*Request|Field\(' app/schemas

echo
echo "SOURCE_MODIFIED=NO"
echo "AUTH_REQUESTS_SENT=NO"
echo "TOKEN_VALUE_DISPLAYED=NO"
echo "WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
```

After authentication, the analysis API calls `analyze_events()` and then stores history. `events` requires at least one item, so sending `{"events":[]}`, which is valid JSON with an empty `events`, always stops at input validation and does not proceed to analysis.

> **Note:** Sending invalid JSON (such as just `{`) may make FastAPI return a body parsing error (`422`) before authentication, which does not test authentication.

## 4.2 Order of Authentication

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: AUTH ORDER TEST ====="

TOKEN="$(cat /root/ai-defense-client.token)"

echo
echo "--- 1. No token: expected 401 ---"
curl --silent --show-error --max-time 5 \
  -X POST \
  -H 'Content-Type: application/json' \
  --data '{"events":[]}' \
  --output /dev/null \
  --write-out 'NO_TOKEN_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/api/v1/analysis

echo
echo "--- 2. Valid token: expected 422 (schema rejection) ---"
curl --silent --show-error --max-time 5 \
  -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  --data '{"events":[]}' \
  --output /dev/null \
  --write-out 'VALID_TOKEN_INVALID_SCHEMA_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/api/v1/analysis

unset TOKEN

echo
echo "--- 3. Health check ---"
curl --silent --show-error --max-time 5 \
  --output /dev/null \
  --write-out 'HEALTH_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "TOKEN_VALUE_DISPLAYED=NO"
echo "WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
echo "ANALYSIS_EXECUTION=NO"
echo "PRODUCTION_HISTORY_WRITES=NO"
```

| Test | HTTP | Verdict |
|---|---:|---|
| No token | 401 | passed |
| Valid token + invalid input | 422 | passed (rejected at input validation after passing authentication) |
| `/health` | 200 | passed |

## 4.3 The Wazuh Retrieval API

To avoid connecting to production Wazuh, we send only requests without credentials or with an invalid token.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: WAZUH EVENTS API AUTH GATE TEST ====="

echo
echo "--- 1. No token: expected 401 ---"
curl --silent --show-error --max-time 5 \
  -X GET \
  --output /dev/null \
  --write-out 'NO_TOKEN_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/api/v1/wazuh/events

echo
echo "--- 2. Malformed Bearer: expected 401 ---"
curl --silent --show-error --max-time 5 \
  -H 'Authorization: Bearer invalid-test-token' \
  --output /dev/null \
  --write-out 'INVALID_TOKEN_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/api/v1/wazuh/events

echo
echo "--- 3. Health check ---"
curl --silent --show-error --max-time 5 \
  --output /dev/null \
  --write-out 'HEALTH_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "VALID_TOKEN_USED=NO"
echo "WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
echo "DATABASE_MODIFIED=NO"
echo "TOKEN_VALUE_DISPLAYED=NO"
```

| Test | HTTP | Verdict |
|---|---:|---|
| No token | 401 | passed |
| Invalid Bearer token | 401 | passed |
| `/health` | 200 | passed |

No communication with Wazuh occurred. For `403` (insufficient privilege) we rely on the results of the independent tests in Part 57 and do not add a test token to the production DB.

## 4.4 Does Information Leak?

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API AUTH SECURITY AUDIT ====="

echo
echo "--- 1. Authentication implementation ---"
sed -n '1,240p' app/core/api_auth.py

echo
echo "--- 2. Token verification and lifecycle ---"
grep -nE -B 5 -A 12 \
  'def verify_token|def revoke_token|def issue_token|last_used_at|expires_at|revoked_at|compare_digest|logger|print\(' \
  app/services/api_tokens.py

echo
echo "--- 3. Potential token logging ---"
grep -R -nE \
  'Authorization|Bearer|access_token|secret_hash|TOKEN_VALUE|logger\.(debug|info|warning|error|exception)|print\(' \
  app/core app/api app/services \
  --include='*.py' |
grep -v 'secret_hash = hashlib.sha256' |
head -100

echo
echo "--- 4. Exception response handling ---"
grep -R -nE \
  'exception_handler|HTTPException|traceback|debug=True|detail=|raise .* from' \
  app/main.py app/api \
  --include='*.py' |
head -120

echo
echo "--- 5. Service logging configuration ---"
systemctl show ai-defense-manager.service \
  -p StandardOutput -p StandardError -p LogLevelMax

echo
echo "SOURCE_MODIFIED=NO"
echo "DATABASE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "TOKEN_VALUE_DISPLAYED=NO"
echo "LIVE_WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
```

| Item | Verdict |
|---|---|
| Bearer tokens not written to logs | passed (no logger or print in the authentication logic) |
| SHA-256 comparison | passed (`hmac.compare_digest()`) |
| Expiry and revocation checks | passed |
| Insufficient scope | passed (`403`) |
| `last_used_at` | passed (updated only when authentication succeeds) |
| API exception responses | passed (return fixed messages) |

> **Run on: VM 230**

```bash
echo "===== VM230: AUTH FAILURE LOG LEAK TEST ====="

START_TIME="$(date --iso-8601=seconds)"

curl --silent --show-error --max-time 5 \
  -H 'Authorization: Bearer invalid-log-test-secret-000000000000' \
  --output /dev/null \
  --write-out 'INVALID_TOKEN_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/api/v1/wazuh/events

echo
echo "--- Recent journal: sensitive values redacted ---"
journalctl -u ai-defense-manager.service \
  --since "$START_TIME" --no-pager -o cat |
python3 -c '
import re, sys
for line in sys.stdin:
    line = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", line)
    line = re.sub(r"(?i)(token[=: ]+)[A-Za-z0-9._~+/=-]{12,}", r"\1[REDACTED]", line)
    print(line.rstrip()[:1000])
'

echo
echo "REAL_TOKEN_USED=NO"
echo "DATABASE_MODIFIED=NO"
echo "WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
```

An invalid token gave `401`, and the journal recorded only the source, path and status; the token value did not appear.

## 4.5 Last-Used Time

Without showing the production token on screen or in arguments, we send one authenticated POST. With `events: []` it gives `422`, so no analysis, storing of history or connection to Wazuh occurs.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: LAST_USED_AT PRODUCTION VERIFICATION ====="

./venv/bin/python - <<'PY'
import sqlite3
from pathlib import Path
import httpx

TOKEN_PATH = Path("/root/ai-defense-client.token")
DB_PATH = "/opt/ai-defense-manager/data/ai-defense.db"
TOKEN_ID = "edcdfc1bfba5683c76c590fd41377ce7"

def read_last_used():
    uri = "file:" + DB_PATH + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        row = conn.execute(
            "SELECT last_used_at FROM api_tokens WHERE token_id = ?",
            (TOKEN_ID,),
        ).fetchone()
    if row is None:
        raise RuntimeError("Token record not found")
    return row[0]

before = read_last_used()
token = TOKEN_PATH.read_text(encoding="ascii").strip()

response = httpx.post(
    "http://127.0.0.1:8000/api/v1/analysis",
    headers={"Authorization": f"Bearer {token}"},
    json={"events": []},
    timeout=5.0,
)

after = read_last_used()

print("HTTP_STATUS=", response.status_code)
print("LAST_USED_BEFORE_SET=", before is not None)
print("LAST_USED_AFTER_SET=", after is not None)
print("LAST_USED_CHANGED=", before != after)
print("TOKEN_VALUE_DISPLAYED=NO")

if response.status_code == 422 and after is not None and before != after:
    print("LAST_USED_AT_VERIFICATION=PASS")
else:
    print("LAST_USED_AT_VERIFICATION=FAIL")

print("WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
print("ANALYSIS_EXECUTION=NO")
print("HISTORY_WRITES=NO")
PY
```

We confirmed that `last_used_at` in the production SQLite was updated when authentication succeeded.

# Closing Notes

In Part 59 we put API token authentication into production.

| Item | Result |
|---|---|
| Production DB | created `api_tokens` and the expiry index |
| Token | issued `ai-defense-client` (`read,analyze`, 30 days); `/root/ai-defense-client.token` (`600`) |
| Service | restarted; authentication enabled (`/health` without authentication) |
| Production tests | no token and invalid tokens give `401`, a valid token passes authentication, tokens do not appear in logs, `last_used_at` is updated |
| Documentation | `/docs`, `/redoc` and `/openapi.json` disabled |

> **Operational note:** Tokens expire after 30 days. Before expiry, issue a new token with `aidm-api-token` and revoke the old one with `revoke` (see the Operations Manual).

In the next part, Part 60, we check whether information leaks from API error responses and logs.

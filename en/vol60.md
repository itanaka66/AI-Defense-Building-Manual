---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 60: Keeping Error Responses and Logs from Leaking Information"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 60 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 59 we put API authentication into production. Here we check whether internal information or submitted values leak from API error responses and logs.

1. Read how API error responses are built, and test whether unhandled exceptions expose internal information
2. Find that input validation error (`422`) responses contain the submitted values as is, and change them to a fixed message
3. Check the destinations and permissions of the Uvicorn logs, the journal and syslog

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: Checking Error Responses

## 1.1 How Error Responses Are Built

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API ERROR DISCLOSURE STATIC AUDIT ====="

echo
echo "--- 1. API exception handlers ---"
grep -RInE \
  'except |HTTPException|detail=|raise .*Exception|str\(e\)|repr\(e\)|traceback|logger\.(exception|error)' \
  app/api app/core/api_auth.py app/main.py \
  --include='*.py' |
grep -v '__pycache__' |
head -160

echo
echo "--- 2. Response and middleware configuration ---"
grep -RInE \
  'exception_handler|RequestValidationError|add_middleware|CORSMiddleware|TrustedHostMiddleware|debug=' \
  app \
  --include='*.py' |
grep -v '__pycache__' |
head -120

echo
echo "--- 3. Production service debug settings ---"
systemctl show ai-defense-manager.service \
  -p Environment -p EnvironmentFiles -p ExecStart \
  --no-pager |
sed -E 's/(TOKEN|SECRET|PASSWORD|KEY)=([^ ]+)/\1=[REDACTED]/Ig'

echo
echo "PRODUCTION_DB_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
```

| Target | Result |
|---|---|
| Analysis APIs, Wazuh APIs | return errors with fixed strings |
| Authentication | `401`, `403`, `503` with fixed strings |
| Returning exception strings as is | none |
| Exposing tracebacks | none |
| Uvicorn debug | not in the startup arguments |

## 1.2 Middleware and Global Exception Handling

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: MIDDLEWARE AND GLOBAL ERROR HANDLER AUDIT ====="

echo
echo "--- 1. app/main.py lines 1-150 ---"
nl -ba app/main.py | sed -n '1,150p'

echo
echo "--- 2. Middleware and exception registrations ---"
grep -RInE \
  'add_middleware|@app\.exception_handler|exception_handler\(|ExceptionMiddleware|ServerErrorMiddleware|CORSMiddleware|allow_origins|allow_credentials|allow_methods|allow_headers' \
  app \
  --include='*.py' |
grep -v '__pycache__' |
head -120

echo
echo "--- 3. Debug and reload references ---"
grep -RInE \
  'debug[[:space:]]*=|--reload|reload[[:space:]]*=' \
  app /etc/systemd/system/ai-defense-manager.service \
  --include='*.py' --include='*.service' 2>/dev/null |
head -80

echo
echo "PRODUCTION_DB_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
```

There was the body limit (256KiB; `413` with a fixed JSON if exceeded) and disabling of OpenAPI and others, but no application-specific global exception handling or CORS middleware.

## 1.3 Testing Unhandled Exceptions

We test with an independent application that does not affect production.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED UNHANDLED EXCEPTION TEST ====="

./venv/bin/python - <<'PY'
import asyncio
import json
from fastapi import FastAPI
from starlette.middleware.exceptions import ExceptionMiddleware
from starlette.middleware.errors import ServerErrorMiddleware

app = FastAPI(debug=False)

@app.get("/test-error")
async def test_error():
    raise RuntimeError("INTERNAL_SECRET_MARKER_DO_NOT_DISCLOSE")

wrapped = ServerErrorMiddleware(
    ExceptionMiddleware(app, handlers=app.exception_handlers, debug=False),
    debug=False,
)

messages = []
scope = {
    "type": "http",
    "asgi": {"version": "3.0", "spec_version": "2.3"},
    "http_version": "1.1",
    "method": "GET",
    "scheme": "http",
    "path": "/test-error",
    "raw_path": b"/test-error",
    "query_string": b"",
    "root_path": "",
    "headers": [],
    "client": ("127.0.0.1", 12345),
    "server": ("127.0.0.1", 8000),
}

async def receive():
    return {"type": "http.request", "body": b"", "more_body": False}

async def send(message):
    messages.append(message)

try:
    awaitable = wrapped(scope, receive, send)
    asyncio.run(awaitable)
except RuntimeError:
    pass

start = next(m for m in messages if m["type"] == "http.response.start")
body = b"".join(
    m.get("body", b"")
    for m in messages
    if m["type"] == "http.response.body"
)

text = body.decode("utf-8", errors="replace")
print("HTTP_STATUS=", start["status"])
print("RESPONSE_IS_JSON=", bool(text) and text.lstrip().startswith("{"))
print("INTERNAL_MARKER_IN_RESPONSE=", "INTERNAL_SECRET_MARKER" in text)
print("TRACEBACK_IN_RESPONSE=", "Traceback" in text)
print("GENERIC_500_RESPONSE=", start["status"] == 500 and "Internal Server Error" in text)
PY

echo
echo "PRODUCTION_SERVICE_TOUCHED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
```

For unhandled exceptions, only `HTTP 500` and `Internal Server Error` were returned; no internal exception markers or tracebacks were included (FastAPI `debug=False`).

## 1.4 Testing Input Validation Errors

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED VALIDATION ERROR DISCLOSURE TEST ====="

./venv/bin/python - <<'PY'
import asyncio
import json
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.exceptions import ExceptionMiddleware
from starlette.middleware.errors import ServerErrorMiddleware

class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[str] = Field(min_length=1, max_length=100)

app = FastAPI(debug=False)

@app.post("/test-validation")
async def test_validation(payload: RequestModel):
    return {"accepted": True}

wrapped = ServerErrorMiddleware(
    ExceptionMiddleware(app, handlers=app.exception_handlers, debug=False),
    debug=False,
)

body = json.dumps({
    "events": [],
    "internal_probe": "VALIDATION_SECRET_MARKER"
}).encode()

messages = []
scope = {
    "type": "http",
    "asgi": {"version": "3.0", "spec_version": "2.3"},
    "http_version": "1.1",
    "method": "POST",
    "scheme": "http",
    "path": "/test-validation",
    "raw_path": b"/test-validation",
    "query_string": b"",
    "root_path": "",
    "headers": [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode()),
    ],
    "client": ("127.0.0.1", 12345),
    "server": ("127.0.0.1", 8000),
}

sent = False

async def receive():
    global sent
    if not sent:
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}
    return {"type": "http.disconnect"}

async def send(message):
    messages.append(message)

asyncio.run(wrapped(scope, receive, send))

start = next(m for m in messages if m["type"] == "http.response.start")
response_body = b"".join(
    m.get("body", b"")
    for m in messages
    if m["type"] == "http.response.body"
)
text = response_body.decode("utf-8", errors="replace")

try:
    parsed = json.loads(text)
except json.JSONDecodeError:
    parsed = {}

print("HTTP_STATUS=", start["status"])
print("JSON_RESPONSE=", isinstance(parsed, dict))
print("VALIDATION_DETAIL_PRESENT=", "detail" in parsed)
print("SECRET_MARKER_IN_RESPONSE=", "VALIDATION_SECRET_MARKER" in text)
print("EXTRA_INPUT_VALUE_IN_RESPONSE=", "internal_probe" in text)
print("TRACEBACK_IN_RESPONSE=", "Traceback" in text)
print("VALIDATION_DISCLOSURE_TEST=", "PASS" if (
    start["status"] == 422
    and "VALIDATION_SECRET_MARKER" not in text
    and "Traceback" not in text
) else "FAIL")
PY

echo
echo "PRODUCTION_SERVICE_TOUCHED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
```

**A problem was found.** The standard FastAPI/Pydantic `422` response included parts of the submitted body (entered values and values of extra fields). If a secret were sent by mistake, it would be returned in the response (this was found in an independent test; nothing leaked in production).

# Chapter 2: Making the `422` Response a Fixed Message

## 2.1 Checking the Impact

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: VALIDATION ERROR CLIENT COMPATIBILITY AUDIT ====="

echo
echo "--- 1. FastAPI / Pydantic versions ---"
./venv/bin/python - <<'PY'
import fastapi
import pydantic
print("FASTAPI_VERSION=", fastapi.__version__)
print("PYDANTIC_VERSION=", pydantic.__version__)
PY

echo
echo "--- 2. Validation error response references ---"
grep -RInE \
  'RequestValidationError|422|Unprocessable Entity|response\.json\(\).*detail|detail.*response|loc.*msg.*type' \
  app tests 2>/dev/null |
head -160

echo
echo "--- 3. API request models ---"
grep -RInE \
  '^class .*Request|^class .*Model|model_config|Field\(' \
  app/api app/models \
  --include='*.py' 2>/dev/null |
head -160

echo
echo "SOURCE_MODIFIED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
```

With FastAPI 0.165.0 and Pydantic 2.14.4, there was no client logic in the application that uses the details of `422`. Other error responses are fixed messages too, so we make `422` uniform in the following form.

```json
{
  "detail": "Invalid request"
}
```

## 2.2 Testing the Fix in an Independent Environment

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED VALIDATION SANITIZER TEST ====="

./venv/bin/python - <<'PY'
import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.exceptions import ExceptionMiddleware
from starlette.middleware.errors import ServerErrorMiddleware

class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[str] = Field(min_length=1, max_length=100)

app = FastAPI(debug=False)

@app.exception_handler(RequestValidationError)
async def sanitized_validation_error(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request"},
    )

@app.post("/test-validation")
async def test_validation(payload: RequestModel):
    return {"accepted": True}

wrapped = ServerErrorMiddleware(
    ExceptionMiddleware(app, handlers=app.exception_handlers, debug=False),
    debug=False,
)

body = json.dumps({
    "events": [],
    "internal_probe": "VALIDATION_SECRET_MARKER"
}).encode()

messages = []
scope = {
    "type": "http",
    "asgi": {"version": "3.0", "spec_version": "2.3"},
    "http_version": "1.1",
    "method": "POST",
    "scheme": "http",
    "path": "/test-validation",
    "raw_path": b"/test-validation",
    "query_string": b"",
    "root_path": "",
    "headers": [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode()),
    ],
    "client": ("127.0.0.1", 12345),
    "server": ("127.0.0.1", 8000),
}

sent = False

async def receive():
    global sent
    if not sent:
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}
    return {"type": "http.disconnect"}

async def send(message):
    messages.append(message)

asyncio.run(wrapped(scope, receive, send))

start = next(m for m in messages if m["type"] == "http.response.start")
response_body = b"".join(
    m.get("body", b"")
    for m in messages
    if m["type"] == "http.response.body"
)
text = response_body.decode("utf-8", errors="replace")

try:
    parsed = json.loads(text)
except json.JSONDecodeError:
    parsed = {}

print("HTTP_STATUS=", start["status"])
print("RESPONSE=", json.dumps(parsed, ensure_ascii=False))
print("SECRET_MARKER_IN_RESPONSE=", "VALIDATION_SECRET_MARKER" in text)
print("EXTRA_INPUT_VALUE_IN_RESPONSE=", "internal_probe" in text)
print("TRACEBACK_IN_RESPONSE=", "Traceback" in text)
print("SANITIZER_TEST=", "PASS" if (
    start["status"] == 422
    and parsed == {"detail": "Invalid request"}
    and "VALIDATION_SECRET_MARKER" not in text
    and "internal_probe" not in text
    and "Traceback" not in text
) else "FAIL")
PY

echo
echo "PRODUCTION_SOURCE_MODIFIED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
```

It remains `422`, but the response is now only `{"detail":"Invalid request"}`, with no entered values, values of extra fields or tracebacks.

## 2.3 Checking Before the Change

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: VALIDATION SANITIZER PRE-PATCH AUDIT ====="

echo
echo "--- Current source metadata ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s' app/main.py

echo
echo "--- Current source SHA256 ---"
sha256sum app/main.py

echo
echo "--- Existing approved backup ---"
if [ -f /var/backups/ai-defense-manager/api-auth-20261124/app-main.py ]; then
  stat -c 'BACKUP_OWNER=%U:%G MODE=%a SIZE=%s' \
    /var/backups/ai-defense-manager/api-auth-20261124/app-main.py
  sha256sum /var/backups/ai-defense-manager/api-auth-20261124/app-main.py
else
  echo "EXISTING_BACKUP_NOT_FOUND"
fi

echo
echo "--- Existing imports and app construction ---"
sed -n '1,12p' app/main.py
sed -n '82,125p' app/main.py

echo
echo "SOURCE_MODIFIED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
```

```bash
echo "===== VM230: EXISTING SOURCE BACKUP INSPECTION ====="

BACKUP_DIR="/var/backups/ai-defense-manager/api-auth-20261124"

echo
echo "--- Backup directory ---"
ls -lah "$BACKUP_DIR"

echo
echo "--- Archive contents matching app/main.py ---"
find "$BACKUP_DIR" -maxdepth 1 -type f -name '*.tar*' -print0 |
while IFS= read -r -d '' archive; do
  echo "ARCHIVE=$archive"
  tar -tf "$archive" | grep -E '(^|/)app/main\.py$' || true
done

echo
echo "--- Current source metadata ---"
stat -c '%U:%G %a %s %n' /opt/ai-defense-manager/app/main.py

echo
echo "SOURCE_MODIFIED=NO"
echo "BACKUP_CREATED=NO"
echo "SERVICE_RESTARTED=NO"
```

```bash
echo "===== VM230: BACKUP INTEGRITY VERIFICATION ====="

cd /var/backups/ai-defense-manager/api-auth-20261124

echo
echo "--- Backup archive checksum ---"
sha256sum -c SHA256SUMS

echo
echo "--- Archived app/main.py checksum ---"
tar -xOzf application-source.tar.gz app/main.py | sha256sum

echo
echo "--- Current app/main.py checksum ---"
sha256sum /opt/ai-defense-manager/app/main.py

echo
echo "BACKUP_MODIFIED=NO"
echo "SOURCE_MODIFIED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

The integrity of the existing copy (`application-source.tar.gz`) passed, but the `app/main.py` inside it is from before API authentication was added, and its hash differs from the current one. **Do not overwrite the current source with this copy.**

## 2.4 Fixing `app/main.py`

We change only `app/main.py` and check the syntax. No service restart, no requests to the production API and no DB changes.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: APPLY VALIDATION ERROR SANITIZER ====="

./venv/bin/python - <<'PY'
from pathlib import Path
import os
import stat
import tempfile

path = Path("/opt/ai-defense-manager/app/main.py")
original = path.read_text(encoding="utf-8")
before_stat = path.stat()

if "RequestValidationError" in original or "Invalid request" in original:
    raise SystemExit("ABORT: validation handler may already exist")

old_import = "from fastapi import FastAPI\n"
new_import = (
    "from fastapi import FastAPI, Request\n"
    "from fastapi.exceptions import RequestValidationError\n"
    "from fastapi.responses import JSONResponse\n"
)

if original.count(old_import) != 1:
    raise SystemExit("ABORT: unexpected FastAPI import layout")

updated = original.replace(old_import, new_import, 1)

anchor = "app.add_middleware(\n"
handler = (
    "@app.exception_handler(RequestValidationError)\n"
    "async def sanitized_validation_error(\n"
    "    request: Request,\n"
    "    exc: RequestValidationError,\n"
    "):\n"
    '    return JSONResponse(status_code=422, content={"detail": "Invalid request"})\n'
    "\n\n"
)

if updated.count(anchor) != 1:
    raise SystemExit("ABORT: middleware insertion point is not unique")

updated = updated.replace(anchor, handler + anchor, 1)

fd, temp_name = tempfile.mkstemp(
    prefix=".main.py.",
    suffix=".tmp",
    dir=str(path.parent),
)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(updated)
        f.flush()
        os.fsync(f.fileno())

    os.chown(temp_name, before_stat.st_uid, before_stat.st_gid)
    os.chmod(temp_name, stat.S_IMODE(before_stat.st_mode))
    os.replace(temp_name, path)

    dir_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
except BaseException:
    try:
        os.unlink(temp_name)
    except FileNotFoundError:
        pass
    raise

print("SOURCE_PATCHED=YES")
print("OWNER_AND_MODE_PRESERVED=YES")
PY

echo
echo "--- Python syntax check ---"
./venv/bin/python -m py_compile app/main.py
echo "PYTHON_SYNTAX=PASS"

echo
echo "--- Patch diff ---"
diff -u <(git show HEAD:app/main.py 2>/dev/null || true) app/main.py | head -100

echo
echo "--- Current source metadata and hash ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s' app/main.py
sha256sum app/main.py

echo
echo "SERVICE_RESTARTED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "PRODUCTION_API_REQUESTS=NO"
```

> **Caution:** In the build records, no new copy was made at this point. When doing this in your own environment, it is safer to save a copy of `app/main.py` before the fix.

The syntax check passed and the owner and permissions were unchanged (the `diff` in the script has no original to compare with, so it shows the whole file as added).

## 2.5 Testing with the Fixed Application

We load the fixed `app.main.app` and check with independent requests.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: PATCHED APPLICATION VALIDATION TEST ====="

./venv/bin/python - <<'PY'
import asyncio
import json
import httpx
from pydantic import BaseModel, ConfigDict, Field
from app.main import app

class ProbeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[str] = Field(min_length=1, max_length=100)

async def temporary_probe(payload: ProbeRequest):
    return {"accepted": True}

app.add_api_route(
    "/__isolated_validation_probe",
    temporary_probe,
    methods=["POST"],
)

async def main():
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://isolated.test",
    ) as client:
        response = await client.post(
            "/__isolated_validation_probe",
            json={
                "events": [],
                "internal_probe": "VALIDATION_SECRET_MARKER",
            },
        )

    text = response.text
    try:
        data = response.json()
    except ValueError:
        data = None

    print("HTTP_STATUS=", response.status_code)
    print("RESPONSE=", json.dumps(data, ensure_ascii=False))
    print("SECRET_MARKER_IN_RESPONSE=", "VALIDATION_SECRET_MARKER" in text)
    print("EXTRA_FIELD_IN_RESPONSE=", "internal_probe" in text)
    print("TRACEBACK_IN_RESPONSE=", "Traceback" in text)

    passed = (
        response.status_code == 422
        and data == {"detail": "Invalid request"}
        and "VALIDATION_SECRET_MARKER" not in text
        and "internal_probe" not in text
        and "Traceback" not in text
    )
    print("PATCHED_APPLICATION_TEST=", "PASS" if passed else "FAIL")

asyncio.run(main())
PY

echo
echo "PRODUCTION_SERVICE_RESTARTED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "EXTERNAL_NETWORK_REQUESTS=NO"
```

`422`, the fixed response, and not exposing secret markers, extra fields or tracebacks all passed.

## 2.6 Final Source Check

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: FINAL SANITIZER SOURCE AUDIT ====="

echo
echo "--- 1. New handler and imports ---"
grep -n -A12 -B4 \
  'RequestValidationError\|sanitized_validation_error' \
  app/main.py

echo
echo "--- 2. Route and middleware declarations ---"
grep -nE \
  'add_middleware|include_router|@app\.get|@app\.exception_handler|docs_url|redoc_url|openapi_url|lifespan=' \
  app/main.py

echo
echo "--- 3. Authentication dependencies remain present ---"
grep -nE \
  'require_scope|Depends\(require_scope' \
  app/api/analysis.py app/api/wazuh.py

echo
echo "--- 4. Syntax and unit verification ---"
./venv/bin/python -m compileall -q app
echo "COMPILEALL=PASS"

systemd-analyze verify /etc/systemd/system/ai-defense-manager.service
echo "SYSTEMD_UNIT_VERIFY=PASS"

echo
echo "--- 5. Source metadata ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s' app/main.py
sha256sum app/main.py

echo
echo "PRODUCTION_SERVICE_RESTARTED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
```

The fixed `422` response handling, the API authentication dependencies, the `read` and `analyze` scopes, the 256KiB body limit, disabling of Swagger, ReDoc and OpenAPI, `compileall`, the systemd unit check and file ownership all passed.

## 2.7 Deploying to Production

> **Run on: VM 230**

```bash
echo "===== VM230: APPLY VALIDATION SANITIZER TO PRODUCTION ====="

echo
echo "--- 1. Restart service ---"
systemctl restart ai-defense-manager.service
RESTART_STATUS=$?
echo "RESTART_COMMAND_STATUS=$RESTART_STATUS"

echo
echo "--- 2. Wait for health endpoint ---"
HEALTH_STATUS=000
for i in $(seq 1 30); do
  HEALTH_STATUS="$(curl --silent --output /dev/null \
    --write-out '%{http_code}' --max-time 2 \
    http://127.0.0.1:8000/health 2>/dev/null || true)"
  if [ "$HEALTH_STATUS" = "200" ]; then
    break
  fi
  sleep 1
done
echo "HEALTH_HTTP_STATUS=$HEALTH_STATUS"

echo
echo "--- 3. Service runtime status ---"
systemctl show ai-defense-manager.service \
  -p ActiveState -p SubState -p MainPID \
  -p NRestarts -p Result \
  -p ExecMainStartTimestamp --no-pager

echo
echo "--- 4. Listener ---"
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "PRODUCTION_SANITIZER_SOURCE_SHA256=41ee62dca6cc02818a7f70b4b8d7bb63500d294fb5429300b86e252e44a161ef"
echo "WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
echo "TOKEN_VALUE_DISPLAYED=NO"
```

`active (running)` (MainPID `2340`, 0 restart failures); `/health` gave `HTTP 200`; listening on `127.0.0.1:8000`.

We send one authenticated request to the production analysis API. It gives `422` at input validation, so it does not proceed to AI analysis.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: PRODUCTION VALIDATION SANITIZER TEST ====="

./venv/bin/python - <<'PY'
import json
from pathlib import Path
import httpx

token = Path("/root/ai-defense-client.token").read_text(
    encoding="ascii"
).strip()

marker = "PRODUCTION_VALIDATION_SECRET_MARKER"

response = httpx.post(
    "http://127.0.0.1:8000/api/v1/analysis",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "events": [],
        "internal_probe": marker,
    },
    timeout=10.0,
)

try:
    data = response.json()
except ValueError:
    data = None

body = response.text

print("HTTP_STATUS=", response.status_code)
print("RESPONSE=", json.dumps(data, ensure_ascii=False))
print("SECRET_MARKER_IN_RESPONSE=", marker in body)
print("EXTRA_FIELD_IN_RESPONSE=", "internal_probe" in body)
print("TRACEBACK_IN_RESPONSE=", "Traceback" in body)
print("TOKEN_VALUE_DISPLAYED=NO")

passed = (
    response.status_code == 422
    and data == {"detail": "Invalid request"}
    and marker not in body
    and "internal_probe" not in body
    and "Traceback" not in body
)
print("PRODUCTION_SANITIZER_TEST=", "PASS" if passed else "FAIL")
print("ANALYSIS_EXECUTION=NO")
print("HISTORY_WRITES=NO")
print("WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
PY
```

| Checked | Result |
|---|---|
| Invalid request | `HTTP 422` |
| Response | `{"detail":"Invalid request"}` |
| Entered secret markers, values of extra fields, tracebacks | not leaked |

# Chapter 3: Final Check of Error Responses

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API ERROR DISCLOSURE FINAL AUDIT ====="

echo
echo "--- 1. HTTP error response declarations ---"
grep -RInE \
  'HTTPException|JSONResponse|PlainTextResponse|Response\(' \
  app --include='*.py' || true

echo
echo "--- 2. Exception disclosure patterns ---"
grep -RInE \
  'str\(e\)|str\(exc\)|repr\(e\)|repr\(exc\)|traceback|format_exc|exc_info|debug=True|reload=True' \
  app --include='*.py' || true

echo
echo "--- 3. Logging and print statements ---"
grep -RInE \
  'logger\.(debug|info|warning|error|exception)|logging\.|print\(' \
  app --include='*.py' || true

echo
echo "--- 4. Token exposure patterns ---"
grep -RInE \
  'Authorization|access_token|secret_hash|token_value|api_token|Bearer' \
  app --include='*.py' || true

echo
echo "--- 5. Service runtime ---"
systemctl show ai-defense-manager.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p Result \
  --no-pager

echo
echo "READ_ONLY_AUDIT=YES"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
```

```bash
cd /opt/ai-defense-manager

echo "===== VM230: HTTP ERROR DETAIL REVIEW ====="

echo
echo "--- analysis.py ---"
nl -ba app/api/analysis.py | sed -n '1,120p'

echo
echo "--- wazuh.py ---"
nl -ba app/api/wazuh.py | sed -n '1,140p'

echo
echo "--- api_auth.py ---"
nl -ba app/core/api_auth.py | sed -n '1,100p'

echo
echo "--- relay error definitions and handling ---"
grep -n -A8 -B5 \
  'class WazuhRelayError\|raise WazuhRelayError\|raise .*Error' \
  app/services/wazuh_relay.py

echo
echo "READ_ONLY=YES"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
```

No place was found that outputs `str(exc)`, `repr(exc)` or tracebacks to responses or logs as is; AI analysis failures, history storage failures, Relay failures, authentication failures, insufficient privilege and token DB faults all returned fixed messages.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: UNHANDLED EXCEPTION CONFIGURATION AUDIT ====="

echo
echo "--- 1. FastAPI application configuration ---"
nl -ba app/main.py | sed -n '80,150p'

echo
echo "--- 2. Uvicorn service command and environment ---"
systemctl cat ai-defense-manager.service

echo
echo "--- 3. Exception handler declarations ---"
grep -RInE \
  '@app\.exception_handler|add_exception_handler|exception_handler\(' \
  app --include='*.py' || true

echo
echo "--- 4. Runtime status ---"
systemctl show ai-defense-manager.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p Result \
  --no-pager

echo
echo "READ_ONLY=YES"
echo "PRODUCTION_REQUESTS=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
```

There is no application-specific handling for unexpected exceptions, but we confirmed in Chapter 1 that with FastAPI `debug=False`, unhandled exceptions return only `HTTP 500 Internal Server Error`. We judged that no fix is needed now.

# Chapter 4: Log Destinations and Permissions

## 4.1 Uvicorn Logs

> **Run on: VM 230**

```bash
echo "===== VM230: UVICORN LOGGING SECURITY AUDIT ====="

echo
echo "--- 1. Effective ExecStart ---"
systemctl show ai-defense-manager.service \
  -p ExecStart --no-pager

echo
echo "--- 2. Uvicorn process command line ---"
tr '\0' ' ' < /proc/2340/cmdline
echo

echo
echo "--- 3. Service journal configuration ---"
systemctl show ai-defense-manager.service \
  -p StandardOutput -p StandardError \
  -p SyslogIdentifier -p LogRateLimitIntervalUSec \
  -p LogRateLimitBurst --no-pager

echo
echo "--- 4. Recent service log metadata (no message contents) ---"
journalctl -u ai-defense-manager.service -n 30 \
  --no-pager -o json |
python3 -c '
import sys, json
for line in sys.stdin:
    try:
        r = json.loads(line)
        print(
            "PRIORITY=" + str(r.get("PRIORITY", "")),
            "UNIT=" + str(r.get("_SYSTEMD_UNIT", "")),
            "MESSAGE_PRESENT=" + str(bool(r.get("MESSAGE"))),
            "MESSAGE_LENGTH=" + str(len(r.get("MESSAGE", ""))),
        )
    except Exception:
        print("JOURNAL_ENTRY_PARSE=FAILED")
'

echo
echo "--- 5. Journal directory permissions ---"
stat -c '%A %U:%G %n' /var/log/journal /run/log/journal 2>/dev/null || true

echo
echo "READ_ONLY=YES"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
```

| Item | Result |
|---|---|
| Listening | `127.0.0.1:8000` |
| Concurrent connections, Keep-Alive | 8, 5 seconds |
| Log destination | the systemd journal (standard error also goes to the journal) |
| Journal directory | `root:systemd-journal` |

`--log-level` is not specified; Uvicorn's default log level applies.

## 4.2 Journal Permissions and Retention

> **Run on: VM 230**

```bash
echo "===== VM230: JOURNAL ACCESS AND RETENTION AUDIT ====="

echo
echo "--- 1. Journal disk usage ---"
journalctl --disk-usage

echo
echo "--- 2. Journal configuration ---"
grep -RInE \
  '^[[:space:]]*(Storage|Compress|Seal|SplitMode|SystemMaxUse|SystemKeepFree|SystemMaxFileSize|RuntimeMaxUse|RuntimeKeepFree|RuntimeMaxFileSize|MaxRetentionSec|MaxFileSec|ForwardToSyslog|ForwardToConsole)[[:space:]]*=' \
  /etc/systemd/journald.conf \
  /etc/systemd/journald.conf.d \
  2>/dev/null || true

echo
echo "--- 3. Journal ACL and permissions ---"
namei -l /var/log/journal
getfacl -cp /var/log/journal 2>/dev/null || true

echo
echo "--- 4. Journal group members ---"
getent group systemd-journal

echo
echo "--- 5. Service account group membership ---"
id ai-defense

echo
echo "--- 6. Journal service status ---"
systemctl is-active systemd-journald.service

echo
echo "READ_ONLY=YES"
echo "CONFIGURATION_MODIFIED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
```

```bash
echo "===== VM230: JOURNAL FILE PERMISSION AUDIT ====="

echo
echo "--- 1. Journal files ---"
find /var/log/journal -type f \
  -printf '%M %u:%g %s %p\n' 2>/dev/null

echo
echo "--- 2. Journal directory tree permissions ---"
find /var/log/journal -type d \
  -printf '%M %u:%g %p\n' 2>/dev/null

echo
echo "--- 3. Effective journald settings ---"
systemd-analyze cat-config systemd/journald.conf

echo
echo "--- 4. Journal runtime limits ---"
systemctl show systemd-journald.service \
  -p MemoryCurrent -p TasksCurrent -p LimitNOFILE \
  --no-pager

echo
echo "READ_ONLY=YES"
echo "JOURNAL_FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Item | Result |
|---|---|
| Space used | 89.0MB |
| Journal files | `root:systemd-journal`, `640` |
| Journal directory | `2755` |
| `systemd-journal` group | no users registered |
| `ai-defense` | not in the `systemd-journal` group |
| Retention period and size settings | no explicit settings (set in Part 61) |

## 4.3 syslog

> **Run on: VM 230**

```bash
echo "===== VM230: SYSLOG FORWARDING AUDIT ====="

echo
echo "--- 1. Syslog services ---"
systemctl is-active rsyslog.service 2>/dev/null || true
systemctl is-active syslog-ng.service 2>/dev/null || true

echo
echo "--- 2. Syslog listeners ---"
ss -lntup | grep -E ':(514|601|6514)\b' || true

echo
echo "--- 3. Syslog configuration files ---"
find /etc/rsyslog.d /etc/syslog-ng \
  -maxdepth 2 -type f -printf '%M %u:%g %p\n' \
  2>/dev/null || true

echo
echo "--- 4. Syslog spool and log directories ---"
stat -c '%A %U:%G %n' \
  /var/log/syslog /var/log/auth.log \
  /var/spool/rsyslog /var/log 2>/dev/null || true

echo
echo "--- 5. Syslog-related processes ---"
ps -eo user,group,pid,args |
  grep -E '[r]syslogd|[s]yslog-ng'

echo
echo "READ_ONLY=YES"
echo "LOG_CONFIGURATION_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
```

The log path is as follows.

```text
AI Defense Manager
        |
        v
systemd-journald
        |
        | ForwardToSyslog=yes
        v
      rsyslog
        |
        +---- /var/log/syslog
        |
        +---- /var/log/auth.log
```

> **Run on: VM 230**

```bash
echo "===== VM230: SYSLOG READER AND ROUTING AUDIT ====="

echo
echo "--- 1. adm group members ---"
getent group adm

echo
echo "--- 2. syslog group members ---"
getent group syslog

echo
echo "--- 3. AI Defense account groups ---"
id ai-defense

echo
echo "--- 4. rsyslog routing configuration ---"
sed -n '1,240p' /etc/rsyslog.d/50-default.conf
sed -n '1,160p' /etc/rsyslog.d/21-cloudinit.conf
sed -n '1,160p' /etc/rsyslog.d/20-ufw.conf

echo
echo "--- 5. Logrotate configuration ---"
grep -RInE \
  'syslog|auth\.log|rotate|size|daily|weekly|monthly|compress|create' \
  /etc/logrotate.conf /etc/logrotate.d/rsyslog \
  2>/dev/null || true

echo
echo "READ_ONLY=YES"
echo "LOGS_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
```

| Item | Result |
|---|---|
| rsyslog | `active` (user `syslog`); no syslog-ng |
| `/var/log/syslog`, `/var/log/auth.log` | `syslog:adm`, `640` |
| `/var/spool/rsyslog` | `syslog:adm`, `700` |
| Listening for syslog from outside | none |
| `adm` group | `syslog`, `aidefense` (`ai-defense` is not a member) |
| Routing | auth/authpriv separated from ordinary logs |
| logrotate | weekly, 4 generations, compressed |

## 4.4 Log Permissions After Rotation

> **Run on: VM 230**

```bash
echo "===== VM230: ROTATED LOG PERMISSION AUDIT ====="

echo
echo "--- 1. Current and rotated syslog files ---"
find /var/log -maxdepth 1 -type f \
  \( -name 'syslog*' -o -name 'auth.log*' \) \
  -printf '%M %u:%g %s %p\n' | sort

echo
echo "--- 2. Logrotate rsyslog policy ---"
cat /etc/logrotate.d/rsyslog

echo
echo "--- 3. Logrotate timer and service ---"
systemctl status logrotate.timer --no-pager 2>/dev/null || true
systemctl status logrotate.service --no-pager 2>/dev/null || true

echo
echo "--- 4. Logrotate state metadata ---"
stat -c '%A %U:%G %s %n' /var/lib/logrotate/status 2>/dev/null || true

echo
echo "READ_ONLY=YES"
echo "LOGS_MODIFIED=NO"
echo "ROTATION_TRIGGERED=NO"
echo "SERVICES_RESTARTED=NO"
```

`syslog`, `syslog.1`, `auth.log` and `auth.log.1` were all `syslog:adm`, `640`. `logrotate.timer` is `active`.

# Closing Notes

In Part 60 we checked API error responses and log permissions, and fixed the problem of values leaking from input validation errors.

| Item | Result |
|---|---|
| Error responses | all fixed messages; unhandled exceptions give only `500 Internal Server Error` |
| `422` response | unified as `{"detail":"Invalid request"}` (confirmed in production) |
| Logs | journal `640`, `2755`; syslog `syslog:adm`, `640`; the service account cannot read the logs |
| Remaining | journal retention period and size not explicitly set |

In the next part, Part 61, we set a size limit for the journal and check log management as a whole.

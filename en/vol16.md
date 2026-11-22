---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 16: Connecting Wazuh Alerts to AI Analysis"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 16 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". Using the Relay connection details placed on VM 230 in Part 15, we add the following functions to the AI Defense Manager (FastAPI).

```text
VM220 security-core
  Wazuh Indexer
       ↓
  Read-only Relay API
       ↓ HTTPS + Token
VM230 ai-defense-manager
  Wazuh Connector
       ↓
  SecurityEvent conversion and validation
       ↓
  AIAnalysisRequest
       ↓
  Existing AI Analysis Service
       ↓
  Defense proposal in JSON
```

Two APIs are added. The existing `/health` and `/api/v1/analysis` remain as they are.

- `GET /api/v1/wazuh/events`: fetches alerts from the Relay, converts them to `SecurityEvent` and returns them
- `POST /api/v1/wazuh/analyze`: passes the fetched alerts to the existing AI analysis (`analyze_events()`) and returns a defense proposal

Only validated events are passed to the AI. The Relay's token and connection target are not passed. The AI is also not given permission to carry out defensive operations (such as blocking IPs).

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code, and the Japanese labels in diagrams, have been translated into English.)
- Unless otherwise noted, everything is run on **ai-defense-manager VM 230 (root)**.

# Chapter 1: Checking the Current Application

## 1.1 File Layout

```bash
find /opt/ai-defense-manager -maxdepth 3 -type f ! -path '*/venv/*' ! -path '*/__pycache__/*' ! -name '*.pyc' -printf '%P\n' | sort | head -n 100
```

Read the settings, the event schema, the application itself, the analysis API, the analysis service and the analysis schema (nothing is changed).

```bash
sed -n '1,240p' /opt/ai-defense-manager/app/core/config.py
```

```bash
sed -n '1,260p' /opt/ai-defense-manager/app/schemas/security_event.py
```

```bash
sed -n '1,260p' /opt/ai-defense-manager/app/main.py
```

```bash
sed -n '1,300p' /opt/ai-defense-manager/app/api/analysis.py
```

```bash
sed -n '1,320p' /opt/ai-defense-manager/app/services/ai_analysis.py
```

```bash
sed -n '1,260p' /opt/ai-defense-manager/app/schemas/analysis.py
```

`AIAnalysisRequest` is built to accept 1–100 `SecurityEvent`s. The Relay also returns at most 100, so they can be connected as they are.

## 1.2 Dependencies

```bash
cat /opt/ai-defense-manager/requirements.lock
```

`httpx` (HTTPS communication), `pydantic` (validation and conversion) and `fastapi` (API) are already installed. Nothing more is installed.

## 1.3 Is It Running?

```bash
systemctl list-units --type=service --all | grep -iE 'ai-defense|uvicorn'
```

```bash
ss -lntp '( sport = :8000 )'
```

```bash
ps -eo pid,ppid,user,args --sort=pid | grep -E '[u]vicorn|[g]unicorn|[a]pp.main|[a]i-defense-manager'
```

At build time there was no systemd service and no process listening on port 8000 (the application was stopped).

```bash
ls -la /opt/ai-defense-manager && ls -ld /opt/ai-defense-manager/venv /etc/ai-defense-manager /etc/ai-defense-manager/credentials
```

```bash
find /opt/ai-defense-manager/tests /opt/ai-defense-manager/config -maxdepth 3 -type f -printf '%p\n' | sort
```

`tests` and `config` were empty.

## 1.4 The Defense Proposal Schema

```bash
sed -n '1,280p' /opt/ai-defense-manager/app/schemas/analysis_proposal.py
```

```bash
sed -n '1,280p' /opt/ai-defense-manager/app/schemas/action.py
```

The following safety constraints are already in place. They are not changed.

- The AI's proposal is returned as JSON
- `temporary_block_ip` (temporary IP block) applies only to global IPs and requires two or more distinct supporting event IDs
- The TTL is 1–900 seconds
- Block proposals always require human approval (the initial state of `ActionProposal` is `PENDING`)
- No code that actually blocks is included

## 1.5 Users and Permissions

```bash
id ai-defense && stat -c '%A %U:%G %n' /opt/ai-defense-manager /opt/ai-defense-manager/app /opt/ai-defense-manager/venv /opt/ai-defense-manager/data /opt/ai-defense-manager/logs /etc/ai-defense-manager/credentials
```

| Target | Owner | Meaning |
|---|---|---|
| Application | `root:ai-defense` | The run-as user cannot modify the code |
| Virtual environment | `root:root` | The run-as user cannot modify packages |
| `data`, `logs` | `ai-defense:ai-defense` | Where the application writes |
| Relay connection details | `root:ai-defense` | The run-as user can read them; other users cannot |

```bash
/opt/ai-defense-manager/venv/bin/python -c 'import fastapi,httpx,pydantic,pydantic_settings; print("FastAPI",fastapi.__version__); print("httpx",httpx.__version__); print("Pydantic",pydantic.__version__); print("DEPENDENCIES_OK")'
```

```bash
stat -c '%A %U:%G %s bytes %n' /etc/ai-defense-manager/credentials/relay-ca.crt /etc/ai-defense-manager/credentials/relay-api.token && runuser -u ai-defense -- test -r /etc/ai-defense-manager/credentials/relay-ca.crt && runuser -u ai-defense -- test -r /etc/ai-defense-manager/credentials/relay-api.token && echo CREDENTIAL_ACCESS_OK
```

# Chapter 2: Fetching from the Relay and Converting to SecurityEvent

## 2.1 The Shape of the Actual Data

Fetch just one alert to check the shape of the values the Relay returns.

```bash
python3 - <<'PY'
import json
import ssl
import urllib.request
from pathlib import Path

base = "https://192.168.0.220:8765"
credentials = Path("/etc/ai-defense-manager/credentials")
token = (credentials / "relay-api.token").read_text().strip()
context = ssl.create_default_context(cafile=str(credentials / "relay-ca.crt"))
request = urllib.request.Request(
    base + "/v1/alerts?limit=1&since_minutes=60",
    headers={"Authorization": f"Bearer {token}"},
)
with urllib.request.urlopen(request, context=context, timeout=10) as response:
    data = json.load(response)

print("STATUS: OK")
print("COUNT:", data.get("count"))
if data.get("alerts"):
    alert = data["alerts"][0]
    print("FIELDS:", sorted(alert.keys()))
    for key in ("timestamp", "rule.level", "rule.id", "rule.description",
                "agent.id", "agent.name", "manager.name", "location", "decoder.name"):
        value = alert.get(key)
        print(f"{key}: {value!r} ({type(value).__name__})")
PY
```

The results at build time (excerpt) were as follows.

| Field | Value |
|---|---|
| `timestamp` | `'2026-11-20T23:54:26.205+0000'` (string with time zone) |
| `rule.level` | `3` (integer) |
| `rule.id` | `'87203'` |
| `rule.description` | `'Proxmox VE authentication succeeded.'` |
| `agent.name` | `'pve'` |
| `decoder.name` | `'pvedaemon'` |

`agent.ip` is the agent's own IP address, so it is not treated as the attacker's IP.

## 2.2 Conversion Rules

Map Wazuh levels to `SecurityEvent` severities as follows.

| Wazuh level | Severity |
|---:|---|
| 0–3 | `info` |
| 4–7 | `low` |
| 8–11 | `medium` |
| 12–14 | `high` |
| 15–16 | `critical` |

## 2.3 wazuh_relay.py

```bash
cat > /opt/ai-defense-manager/app/services/wazuh_relay.py <<'PY'
from datetime import datetime
from pathlib import Path

import httpx

from app.core.config import settings
from app.schemas.security_event import SecurityEvent


class WazuhRelayError(Exception):
    pass


def _severity(level: int) -> str:
    if not 0 <= level <= 16:
        raise ValueError("Wazuh rule level is outside the accepted range")

    if level <= 3:
        return "info"
    if level <= 7:
        return "low"
    if level <= 11:
        return "medium"
    if level <= 14:
        return "high"
    return "critical"


def _convert_alert(alert: dict) -> SecurityEvent:
    if not isinstance(alert, dict):
        raise ValueError("Alert must be an object")

    timestamp = alert.get("timestamp")
    level = alert.get("rule.level")
    rule_id = alert.get("rule.id")
    description = alert.get("rule.description")
    agent_id = alert.get("agent.id")
    agent_name = alert.get("agent.name")
    location = alert.get("location")
    decoder = alert.get("decoder.name")

    if not isinstance(timestamp, str):
        raise ValueError("Invalid alert timestamp")
    if isinstance(level, bool) or not isinstance(level, int):
        raise ValueError("Invalid Wazuh rule level")

    observed_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("Alert timestamp must include a timezone")

    if rule_id is not None and not isinstance(rule_id, str):
        raise ValueError("Invalid rule ID")
    if description is not None and not isinstance(description, str):
        raise ValueError("Invalid rule description")
    if agent_id is not None and not isinstance(agent_id, str):
        raise ValueError("Invalid agent ID")
    if agent_name is not None and not isinstance(agent_name, str):
        raise ValueError("Invalid agent name")
    if location is not None and not isinstance(location, str):
        raise ValueError("Invalid alert location")
    if decoder is not None and not isinstance(decoder, str):
        raise ValueError("Invalid decoder name")

    category = (decoder or location or "wazuh")[:64]
    summary = (description or "Wazuh security alert")[:512]

    return SecurityEvent(
        source="wazuh",
        observed_at=observed_at,
        severity=_severity(level),
        rule_id=rule_id,
        rule_description=description[:512] if description else None,
        agent_id=agent_id,
        agent_name=agent_name,
        event_category=category,
        event_summary=summary,
    )


async def fetch_wazuh_events(
    limit: int = 50,
    since_minutes: int = 60,
) -> list[SecurityEvent]:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    if not 1 <= since_minutes <= 1440:
        raise ValueError("since_minutes must be between 1 and 1440")

    ca_file = Path(settings.wazuh_relay_ca_file)
    token_file = Path(settings.wazuh_relay_token_file)

    if not ca_file.is_file() or not token_file.is_file():
        raise WazuhRelayError("Relay credentials are unavailable")

    try:
        token = token_file.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise WazuhRelayError("Unable to read Relay credentials") from exc

    if not token or len(token) > 512:
        raise WazuhRelayError("Relay token is invalid")

    url = (
        f"{str(settings.wazuh_relay_base_url).rstrip('/')}"
        "/v1/alerts"
    )

    try:
        async with httpx.AsyncClient(
            verify=str(ca_file),
            timeout=settings.wazuh_relay_timeout_seconds,
            follow_redirects=False,
        ) as client:
            response = await client.get(
                url,
                params={
                    "limit": limit,
                    "since_minutes": since_minutes,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            payload = response.json()

        alerts = payload.get("alerts")
        if not isinstance(alerts, list):
            raise WazuhRelayError("Relay returned an invalid response")

        if len(alerts) > limit:
            raise WazuhRelayError("Relay returned more alerts than requested")

        return [_convert_alert(alert) for alert in alerts]

    except WazuhRelayError:
        raise
    except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
        raise WazuhRelayError("Wazuh Relay retrieval or validation failed") from exc
PY
```

The terminal display can get garbled when pasting. Check by line count and the end of the file that it was written completely (137 lines at build time).

```bash
wc -l /opt/ai-defense-manager/app/services/wazuh_relay.py && tail -n 20 /opt/ai-defense-manager/app/services/wazuh_relay.py
```

```bash
 /opt/ai-defense-manager/venv/bin/python -m py_compile /opt/ai-defense-manager/app/services/wazuh_relay.py && echo WAZUH_RELAY_SYNTAX_OK
```

## 2.4 Adding Settings

Add the connection target and the locations of the connection-detail files to the settings. The token itself is not written in the settings.

```bash
python3 - <<'PY'
from pathlib import Path

p = Path("/opt/ai-defense-manager/app/core/config.py")
s = p.read_text()

marker = '    analysis_timeout_seconds: int = Field(default=60, ge=1, le=600)\n'
addition = '''    analysis_timeout_seconds: int = Field(default=60, ge=1, le=600)

    wazuh_relay_base_url: HttpUrl = "https://192.168.0.220:8765/"
    wazuh_relay_ca_file: str = "/etc/ai-defense-manager/credentials/relay-ca.crt"
    wazuh_relay_token_file: str = "/etc/ai-defense-manager/credentials/relay-api.token"
    wazuh_relay_timeout_seconds: int = Field(default=15, ge=1, le=60)
'''

if "wazuh_relay_base_url" in s:
    raise SystemExit("Relay settings already exist; no changes made")
if marker not in s:
    raise SystemExit("Expected insertion point not found; no changes made")

p.write_text(s.replace(marker, addition, 1))
print("WAZUH_RELAY_SETTINGS_ADDED")
PY
```

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
from app.core.config import settings

assert str(settings.wazuh_relay_base_url) == "https://192.168.0.220:8765/"
assert settings.wazuh_relay_ca_file == "/etc/ai-defense-manager/credentials/relay-ca.crt"
assert settings.wazuh_relay_token_file == "/etc/ai-defense-manager/credentials/relay-api.token"
assert settings.wazuh_relay_timeout_seconds == 15

print("RELAY_URL:", settings.wazuh_relay_base_url)
print("CA_FILE:", settings.wazuh_relay_ca_file)
print("TOKEN_FILE_CONFIGURED:", bool(settings.wazuh_relay_token_file))
print("TIMEOUT:", settings.wazuh_relay_timeout_seconds)
print("CONFIG_VALID")
PY
```

# Chapter 3: The Fetch API

## 3.1 wazuh.py (Fetch Only)

`limit` is 1–100 (default 50) and `since_minutes` is 1–1440 minutes (default 60). If communication with the Relay fails, it returns `502` and does not return connection details or the Relay's raw data.

```bash
cat > /opt/ai-defense-manager/app/api/wazuh.py <<'PY'
from fastapi import APIRouter, HTTPException, Query

from app.schemas.security_event import SecurityEvent
from app.services.wazuh_relay import WazuhRelayError, fetch_wazuh_events

router = APIRouter(prefix="/api/v1/wazuh", tags=["Wazuh"])


@router.get("/events", response_model=list[SecurityEvent])
async def get_wazuh_events(
    limit: int = Query(default=50, ge=1, le=100),
    since_minutes: int = Query(default=60, ge=1, le=1440),
) -> list[SecurityEvent]:
    try:
        return await fetch_wazuh_events(
            limit=limit,
            since_minutes=since_minutes,
        )
    except WazuhRelayError as exc:
        raise HTTPException(
            status_code=502,
            detail="Wazuh alert retrieval or validation failed",
        ) from exc
PY
```

```bash
cd /opt/ai-defense-manager && ./venv/bin/python -m py_compile app/core/config.py app/services/wazuh_relay.py app/api/wazuh.py && ./venv/bin/python -c 'from app.api.wazuh import router; print("ROUTES:", [(r.path, sorted(r.methods)) for r in router.routes]); print("WAZUH_API_IMPORT_OK")'
```

## 3.2 Registering It in the Application

```bash
python3 - <<'PY'
from pathlib import Path

p = Path("/opt/ai-defense-manager/app/main.py")
s = p.read_text()

if "from app.api.wazuh import router as wazuh_router" in s:
    raise SystemExit("Wazuh router import already exists; no changes made")

s = s.replace(
    "from app.api.analysis import router as analysis_router\n",
    "from app.api.analysis import router as analysis_router\n"
    "from app.api.wazuh import router as wazuh_router\n",
    1,
)

s = s.replace(
    "app.include_router(analysis_router)\n",
    "app.include_router(analysis_router)\n"
    "app.include_router(wazuh_router)\n",
    1,
)

if "app.include_router(wazuh_router)" not in s:
    raise SystemExit("Router registration failed; no file written")

p.write_text(s)
print("WAZUH_ROUTER_REGISTERED")
PY
```

## 3.3 Checking the Registration

In FastAPI 0.165.0, used at build time, routers registered with `include_router()` are incorporated lazily, so `/api/v1/...` does not appear in `app.routes`. Check with the OpenAPI specification generated by FastAPI instead.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
from app.main import app

schema = app.openapi()
paths = schema.get("paths", {})

for path in sorted(paths):
    print(path, sorted(paths[path].keys()))

required = {
    ("/health", "get"),
    ("/api/v1/analysis", "post"),
    ("/api/v1/wazuh/events", "get"),
}
actual = {
    (path, method.lower())
    for path, operations in paths.items()
    for method in operations
}
missing = required - actual

if missing:
    raise SystemExit(f"MISSING_OPENAPI_OPERATIONS: {missing}")

print("OPENAPI_ROUTE_REGISTRATION_OK")
PY
```

## 3.4 Fetching as the Run-As User

As the `ai-defense` user, fetch five alerts from the Relay and convert them to `SecurityEvent`.

```bash
cd /opt/ai-defense-manager && runuser -u ai-defense -- ./venv/bin/python - <<'PY'
import asyncio
from app.services.wazuh_relay import fetch_wazuh_events

async def main():
    events = await fetch_wazuh_events(limit=5, since_minutes=60)
    print("EVENT_COUNT:", len(events))
    for event in events:
        print({
            "source": event.source,
            "severity": event.severity,
            "rule_id": event.rule_id,
            "agent_id": event.agent_id,
            "agent_name": event.agent_name,
            "event_category": event.event_category,
            "event_summary": event.event_summary,
            "observed_at": event.observed_at.isoformat(),
            "source_ip": event.source_ip,
        })
    print("SECURITY_EVENT_CONVERSION_OK")

asyncio.run(main())
PY
```

At build time all five were converted, and `rule.level=3` became `info`. The Relay does not return the attacker's IP, so `source_ip` stays `None`.

# Chapter 4: The Analysis API

## 4.1 The Request Schema

```bash
cat > /opt/ai-defense-manager/app/schemas/wazuh.py <<'PY'
from pydantic import BaseModel, ConfigDict, Field


class WazuhAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=50, ge=1, le=100)
    since_minutes: int = Field(default=60, ge=1, le=1440)
    analysis_context: str | None = Field(default=None, max_length=2000)
    requested_language: str = Field(default="ja", pattern=r"^(ja|en)$")
PY
```

```bash
cd /opt/ai-defense-manager && ./venv/bin/python -m py_compile app/schemas/wazuh.py && ./venv/bin/python -c 'from app.schemas.wazuh import WazuhAnalysisRequest; r=WazuhAnalysisRequest(); print(r.model_dump()); print("WAZUH_ANALYSIS_SCHEMA_OK")'
```

## 4.2 wazuh.py (Analysis Added)

`POST /api/v1/wazuh/analyze` processes in the following order.

1. Fetch Wazuh alerts from the Relay
2. Convert them to `SecurityEvent` and validate them
3. If there are zero, finish with `404` without calling the AI
4. Pass them to the existing `analyze_events()`
5. Return an `AIAnalysisProposal` (defense proposal)

```bash
cat > /opt/ai-defense-manager/app/api/wazuh.py <<'PY'
from fastapi import APIRouter, HTTPException, Query

from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal
from app.schemas.security_event import SecurityEvent
from app.schemas.wazuh import WazuhAnalysisRequest
from app.services.ai_analysis import AIAnalysisError, analyze_events
from app.services.wazuh_relay import WazuhRelayError, fetch_wazuh_events

router = APIRouter(prefix="/api/v1/wazuh", tags=["Wazuh"])


@router.get("/events", response_model=list[SecurityEvent])
async def get_wazuh_events(
    limit: int = Query(default=50, ge=1, le=100),
    since_minutes: int = Query(default=60, ge=1, le=1440),
) -> list[SecurityEvent]:
    try:
        return await fetch_wazuh_events(
            limit=limit,
            since_minutes=since_minutes,
        )
    except WazuhRelayError as exc:
        raise HTTPException(
            status_code=502,
            detail="Wazuh alert retrieval or validation failed",
        ) from exc


@router.post("/analyze", response_model=AIAnalysisProposal)
async def analyze_wazuh_events(
    request: WazuhAnalysisRequest,
) -> AIAnalysisProposal:
    try:
        events = await fetch_wazuh_events(
            limit=request.limit,
            since_minutes=request.since_minutes,
        )

        if not events:
            raise HTTPException(
                status_code=404,
                detail="No Wazuh alerts found in the requested time range",
            )

        analysis_request = AIAnalysisRequest(
            events=events,
            analysis_context=request.analysis_context,
            requested_language=request.requested_language,
        )

        return await analyze_events(analysis_request)

    except WazuhRelayError as exc:
        raise HTTPException(
            status_code=502,
            detail="Wazuh alert retrieval or validation failed",
        ) from exc
    except AIAnalysisError as exc:
        raise HTTPException(
            status_code=502,
            detail="AI analysis failed or returned an invalid response",
        ) from exc
PY
```

```bash
wc -l /opt/ai-defense-manager/app/api/wazuh.py && tail -n 35 /opt/ai-defense-manager/app/api/wazuh.py
```

At build time the file had 63 lines and had been written to the end.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python -m py_compile app/api/wazuh.py app/schemas/wazuh.py app/services/wazuh_relay.py app/core/config.py && ./venv/bin/python - <<'PY'
from app.main import app

paths = app.openapi()["paths"]

for path in sorted(paths):
    print(path, sorted(paths[path].keys()))

required = {
    ("/health", "get"),
    ("/api/v1/analysis", "post"),
    ("/api/v1/wazuh/events", "get"),
    ("/api/v1/wazuh/analyze", "post"),
}
actual = {
    (path, method.lower())
    for path, operations in paths.items()
    for method in operations
}
missing = required - actual

if missing:
    raise SystemExit(f"MISSING_OPERATIONS: {missing}")

print("WAZUH_INTEGRATION_OPENAPI_OK")
PY
```

# Chapter 5: Checking Wazuh → Ollama → AI Analysis

## 5.1 Is the Model There?

Check whether `qwen3:8b`, used for analysis, is present on Ollama (VM 101). No analysis request is sent yet.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
import json
import urllib.request
from app.core.config import settings

url = str(settings.ollama_base_url).rstrip("/") + "/api/tags"
try:
    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.load(response)
    models = [m.get("name") for m in data.get("models", [])]
    print("OLLAMA_STATUS: OK")
    print("AVAILABLE_MODELS:")
    for model in models:
        print(" -", model)
    print("QWEN3_8B_AVAILABLE:", any(
        name == "qwen3:8b" or name.startswith("qwen3:8b-")
        for name in models
    ))
except Exception as exc:
    print("OLLAMA_CHECK_FAILED:", type(exc).__name__, str(exc))
    raise SystemExit(1)
PY
```

## 5.2 Connecting and Analyzing

As the run-as user, fetch five alerts and pass them to the existing analysis. The alert contents are sent to the LLM, but no defensive operations, IP blocks or setting changes are performed at all.

```bash
cd /opt/ai-defense-manager && runuser -u ai-defense -- ./venv/bin/python - <<'PY'
import asyncio
from app.schemas.analysis import AIAnalysisRequest
from app.services.wazuh_relay import fetch_wazuh_events
from app.services.ai_analysis import analyze_events

async def main():
    events = await fetch_wazuh_events(limit=5, since_minutes=60)
    if not events:
        raise RuntimeError("No Wazuh events available for analysis")

    request = AIAnalysisRequest(
        events=events,
        analysis_context="Wazuhから取得した直近のセキュリティイベントを分析してください。実行済みの操作として扱わず、防御操作は提案だけにしてください。",
        requested_language="ja",
    )

    print("INPUT_EVENT_COUNT:", len(events))
    proposal = await analyze_events(request)

    print("ANALYSIS_RESULT:")
    print("severity:", proposal.severity)
    print("confidence:", proposal.confidence)
    print("recommended_action:", proposal.recommended_action.value)
    print("requires_human_approval:", proposal.requires_human_approval)
    print("evidence_event_count:", len(proposal.evidence_event_ids))
    print("target_ip:", proposal.target_ip)
    print("ttl_seconds:", proposal.ttl_seconds)
    print("summary:", proposal.summary)
    print("reasoning:", proposal.reasoning)
    print("WAZUH_TO_AI_ANALYSIS_OK")

asyncio.run(main())
PY
```

The results at build time were as follows. The alerts were mostly records of successful authentication and login sessions, so it is reasonable that no block was proposed.

| Item | Result |
|---|---|
| `severity` | `info` |
| `confidence` | `0.8` |
| `recommended_action` | `no_action` |
| `evidence_event_count` | `5` |
| `target_ip`, `ttl_seconds` | `None` |

## 5.3 Permissions of the Added Files

```bash
stat -c '%A %U:%G %n' \
  /opt/ai-defense-manager/app/main.py \
  /opt/ai-defense-manager/app/core/config.py \
  /opt/ai-defense-manager/app/api/wazuh.py \
  /opt/ai-defense-manager/app/schemas/wazuh.py \
  /opt/ai-defense-manager/app/services/wazuh_relay.py \
  /etc/ai-defense-manager/credentials/relay-ca.crt \
  /etc/ai-defense-manager/credentials/relay-api.token
```

At build time, the three newly created API-related files were `root:root` with `644`. Aligning their owner with the existing files is done in the next part.

# Closing Notes

In Part 16 we added the following APIs to the AI Defense Manager.

| API | Details |
|---|---|
| `GET /api/v1/wazuh/events` | Fetches alerts from the Relay and returns them as `SecurityEvent` |
| `POST /api/v1/wazuh/analyze` | Analyzes the fetched alerts with AI and returns a defense proposal |

In the next part, we align the file permissions and run the AI Defense Manager as a systemd service.

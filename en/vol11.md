---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 11: Laying the Groundwork for the AI Defense Manager"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 11 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". On VM 230 (`ai-defense-manager`, 192.168.0.33), created in Part 10, we lay the groundwork for the "AI Defense Manager", the application responsible for AI analysis, decisions and responses.

This part builds the following.

- A dedicated Python virtual environment and a dedicated run-as user
- A minimal API with FastAPI, and configuration management
- The types (schemas) of the data passed to and received from the AI, and their validation

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Unless otherwise noted, everything is run on **VM 230 ai-defense-manager (root)**.

## Permission Policy

| Target | Owner | Permissions | Reason |
|---|---|---|---|
| Application (`app`) | `root:ai-defense` | Directories `750`, files `640` | The run-as user can read but not modify it |
| Configuration (`config`) | root | root only | Where secrets are kept |
| Data and logs (`data`, `logs`) | `ai-defense` | — | Written by the run-as user |
| Virtual environment (`venv`) | root | `755` | The run-as user can use but not change it |

# Chapter 1: The Python Virtual Environment

## 1.1 Checking

```bash
python3 -m pip --version
```

`pip` is not installed on the system (on Ubuntu 24.04 you do not install packages into the system Python; you use a virtual environment).

```bash
python3 -m venv --help
```

```bash
ls -ld /opt/ai-defense-manager
```

## 1.2 Creating It

```bash
install -d -m 0755 /opt/ai-defense-manager
```

Creating a virtual environment requires `python3.12-venv` (`ensurepip`). Without it creation fails, so install it first, after checking what would be installed.

```bash
apt-get -s install python3.12-venv
```

```bash
apt-get install -y python3.12-venv
```

```bash
python3 -m venv /opt/ai-defense-manager/venv
```

```bash
/opt/ai-defense-manager/venv/bin/pip --version
```

```bash
/opt/ai-defense-manager/venv/bin/python --version
```

At build time this was pip 24.0 and Python 3.12.3.

# Chapter 2: Directories and the Run-As User

## 2.1 Directory Layout

```bash
find /opt/ai-defense-manager -maxdepth 2 -type d -print
```

Use the following layout.

```text
/opt/ai-defense-manager/
├── venv/          # Python virtual environment
├── app/           # FastAPI application
│   ├── api/       # REST API
│   ├── core/      # Settings and shared code
│   ├── agents/    # AI agents
│   ├── schemas/   # JSON schemas
│   ├── services/  # External system integration
│   └── policies/  # Deterministic policy validation
├── config/        # Configuration files
├── data/          # Application data
├── logs/          # Application logs
└── tests/         # Tests
```

```bash
install -d -m 0750 /opt/ai-defense-manager/{app/{api,core,agents,schemas,services,policies},config,data,logs,tests}
```

```bash
find /opt/ai-defense-manager -maxdepth 2 -type d -not -path '*/venv*' | sort
```

## 2.2 A Dedicated Run-As User

`aidefense`, which is used for logging in, is an ordinary user that also belongs to administrative groups. The application runs as a dedicated system user, `ai-defense`, which cannot log in.

```bash
id aidefense
```

```bash
ls -ld /opt/ai-defense-manager /opt/ai-defense-manager/{app,config,data,logs,tests}
```

```bash
useradd --system --user-group --home-dir /opt/ai-defense-manager --no-create-home --shell /usr/sbin/nologin ai-defense
```

```bash
id ai-defense
```

## 2.3 Owners and Permissions

Make data and logs writable by the run-as user.

```bash
chown ai-defense:ai-defense /opt/ai-defense-manager/data /opt/ai-defense-manager/logs
```

```bash
ls -ld /opt/ai-defense-manager/{app,config,data,logs,tests}
```

Set the application to `root:ai-defense` so that the run-as user can read it but not modify it.

```bash
find /opt/ai-defense-manager/app -maxdepth 2 -type d -printf '%M %u:%g %p\n' | sort
```

```bash
getent group ai-defense
```

```bash
chown -R root:ai-defense /opt/ai-defense-manager/app
```

```bash
find /opt/ai-defense-manager/app -type d -exec chmod 750 {} +
```

```bash
find /opt/ai-defense-manager/app -type f -exec chmod 640 {} +
```

```bash
find /opt/ai-defense-manager/app -printf '%M %u:%g %p\n' | sort
```

Keep the virtual environment owned by root with `755` (the run-as user can use it but cannot change it).

```bash
ls -ld /opt/ai-defense-manager/venv
```

```bash
find /opt/ai-defense-manager/venv -maxdepth 2 -type d -printf '%M %u:%g %p\n' | sort
```

```bash
runuser -u ai-defense -- /opt/ai-defense-manager/venv/bin/python --version
```

# Chapter 3: Base Packages

## 3.1 Installation

```bash
/opt/ai-defense-manager/venv/bin/pip list
```

```bash
/opt/ai-defense-manager/venv/bin/pip config list
```

```bash
curl -I --max-time 10 https://pypi.org/simple/fastapi/
```

If `HTTP/2 200` is returned, PyPI can be reached.

```bash
/opt/ai-defense-manager/venv/bin/pip install fastapi uvicorn[standard] pydantic pydantic-settings httpx
```

## 3.2 Checking

```bash
/opt/ai-defense-manager/venv/bin/pip check
```

Confirm `No broken requirements found.`

```bash
/opt/ai-defense-manager/venv/bin/pip show fastapi uvicorn pydantic pydantic-settings httpx
```

```bash
runuser -u ai-defense -- /opt/ai-defense-manager/venv/bin/python -c "import fastapi, uvicorn, pydantic, pydantic_settings, httpx; print('FastAPI:', fastapi.__version__); print('Uvicorn:', uvicorn.__version__); print('Pydantic:', pydantic.__version__); print('HTTPX:', httpx.__version__); print('IMPORT_OK')"
```

```bash
stat -c '%A %U:%G %n' /opt/ai-defense-manager/config
```

## 3.3 Recording the Installed Packages

```bash
/opt/ai-defense-manager/venv/bin/pip freeze
```

```bash
/opt/ai-defense-manager/venv/bin/pip freeze > /opt/ai-defense-manager/requirements.lock
```

```bash
ls -l /opt/ai-defense-manager/requirements.lock
```

```bash
chown root:ai-defense /opt/ai-defense-manager/requirements.lock && chmod 640 /opt/ai-defense-manager/requirements.lock
```

```bash
runuser -u ai-defense -- cat /opt/ai-defense-manager/requirements.lock
```

At build time there were 24 packages, including dependencies.

# Chapter 4: A Minimal API

## 4.1 main.py

First create a minimal API that has only `/health`, which returns the status.

```bash
ls -l /opt/ai-defense-manager/app/main.py
```

```bash
cat > /opt/ai-defense-manager/app/main.py <<'PY'
from fastapi import FastAPI

app = FastAPI(
    title="AI Defense Manager",
    description="Autonomous AI Cyber Defense Management API",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "ai-defense-manager",
        "version": "0.1.0",
    }
PY
```

```bash
chown root:ai-defense /opt/ai-defense-manager/app/main.py && chmod 640 /opt/ai-defense-manager/app/main.py
```

```bash
runuser -u ai-defense -- /opt/ai-defense-manager/venv/bin/python -c "import sys; sys.path.insert(0, '/opt/ai-defense-manager'); from app.main import app; print('APP_IMPORT_OK:', app.title, app.version)"
```

## 4.2 Starting and Checking

Confirm that port 8000 is free, and start it as the dedicated user, listening only on the machine itself (127.0.0.1).

```bash
ss -lntp 'sport = :8000'
```

```bash
runuser -u ai-defense -- /opt/ai-defense-manager/venv/bin/uvicorn app.main:app --app-dir /opt/ai-defense-manager --host 127.0.0.1 --port 8000
```

This command keeps running and does not return, so do the check from another terminal (a second SSH connection).

```bash
curl -i http://127.0.0.1:8000/health
```

It has succeeded if `HTTP/1.1 200 OK` and the following content are returned.

```text
{
  "status": "ok",
  "service": "ai-defense-manager",
  "version": "0.1.0"
}
```

```bash
find /opt/ai-defense-manager/app -maxdepth 2 -type f -printf '%M %u:%g %p\n'
```

# Chapter 5: Configuration Management

## 5.1 config.py

Gather settings such as connection targets in one place, and allow them to be overridden by environment variables (names starting with `AIDM_`). Secrets such as passwords are not written here.

```bash
runuser -u ai-defense -- /opt/ai-defense-manager/venv/bin/python -c "from pydantic_settings import BaseSettings; print('PYDANTIC_SETTINGS_OK')"
```

```bash
cat > /opt/ai-defense-manager/app/core/config.py <<'PY'
from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AIDM_",
        env_file=None,
        extra="ignore",
    )

    app_name: str = "AI Defense Manager"
    app_version: str = "0.1.0"

    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1024, le=65535)

    ollama_base_url: HttpUrl = "http://192.168.0.180:11434/"

    wazuh_base_url: HttpUrl | None = None
    postgres_host: str | None = None
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_database: str | None = None

    analysis_timeout_seconds: int = Field(default=60, ge=1, le=600)


settings = Settings()
PY
```

```bash
chown root:ai-defense /opt/ai-defense-manager/app/core/config.py && chmod 640 /opt/ai-defense-manager/app/core/config.py
```

## 5.2 Checking Loading and Overriding

```bash
runuser -u ai-defense -- /opt/ai-defense-manager/venv/bin/python -c "import sys; sys.path.insert(0, '/opt/ai-defense-manager'); from app.core.config import settings; print('CONFIG_OK'); print('APP:', settings.app_name); print('OLLAMA:', settings.ollama_base_url); print('API:', settings.api_host, settings.api_port); print('WAZUH:', settings.wazuh_base_url); print('POSTGRES:', settings.postgres_host)"
```

```bash
runuser -u ai-defense -- env AIDM_API_PORT=8100 /opt/ai-defense-manager/venv/bin/python -c "import sys; sys.path.insert(0, '/opt/ai-defense-manager'); from app.core.config import Settings; s=Settings(); print('ENV_OVERRIDE_OK' if s.api_port == 8100 else 'ENV_OVERRIDE_FAILED'); print('TEST_PORT:', s.api_port)"
```

Confirm `CONFIG_OK` and `ENV_OVERRIDE_OK`.

## 5.3 Building It into main.py

```bash
curl -sS http://127.0.0.1:8000/health
```

```bash
cat > /opt/ai-defense-manager/app/main.py <<'PY'
from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Autonomous AI Cyber Defense Management API",
    version=settings.app_version,
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "ai-defense-manager",
        "version": settings.app_version,
    }
PY
```

```bash
chown root:ai-defense /opt/ai-defense-manager/app/main.py && chmod 640 /opt/ai-defense-manager/app/main.py
```

```bash
runuser -u ai-defense -- /opt/ai-defense-manager/venv/bin/python -c "import sys; sys.path.insert(0, '/opt/ai-defense-manager'); from app.main import app; from app.core.config import settings; print('APP_CONFIG_INTEGRATION_OK'); print('TITLE:', app.title); print('VERSION:', app.version); print('OLLAMA:', settings.ollama_base_url)"
```

Stop the running Uvicorn by pressing `Ctrl+C` in the terminal where it was started, and start it again.

```bash
runuser -u ai-defense -- /opt/ai-defense-manager/venv/bin/uvicorn app.main:app --app-dir /opt/ai-defense-manager --host 127.0.0.1 --port 8000
```

```bash
curl -i http://127.0.0.1:8000/health
```

```bash
curl -sS http://127.0.0.1:8000/health
```

After the settings are built in, the same content as in 4.2 is returned.

# Chapter 6: Data Types (Schemas)

Define strictly, with Pydantic models, the shape of the data passed to the AI and received from the AI. Fields that are not defined (for example the full log `full_log`) are not accepted (`extra="forbid"`).

```bash
find /opt/ai-defense-manager/app/schemas -maxdepth 1 -type f -printf '%f\n'
```

## 6.1 Security Events (security_event.py)

```bash
cat > /opt/ai-defense-manager/app/schemas/security_event.py <<'PY'
from datetime import datetime, timezone
from ipaddress import ip_address
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SecurityEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID = Field(default_factory=uuid4)
    source: Literal["wazuh", "prometheus", "victoriametrics", "internal"]
    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    severity: Literal["info", "low", "medium", "high", "critical"]
    rule_id: str | None = Field(default=None, max_length=64)
    rule_description: str | None = Field(default=None, max_length=512)

    source_ip: str | None = None
    destination_ip: str | None = None

    agent_id: str | None = Field(default=None, max_length=64)
    agent_name: str | None = Field(default=None, max_length=128)

    event_category: str = Field(min_length=1, max_length=64)
    event_summary: str = Field(min_length=1, max_length=512)

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observed_at must include a timezone")
        return value

    @field_validator("source_ip", "destination_ip")
    @classmethod
    def validate_ip_address(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return str(ip_address(value))
PY
```

Check the syntax. The run-as user cannot write to the application directory, so check it with a method that does not write bytecode, instead of `py_compile` (which writes bytecode).

```bash
runuser -u ai-defense -- /opt/ai-defense-manager/venv/bin/python -c "from pathlib import Path; p=Path('/opt/ai-defense-manager/app/schemas/security_event.py'); compile(p.read_text(), str(p), 'exec'); print('SYNTAX_OK')"
```

Pasting can break the terminal display, so also check that the end of the file was written correctly.

```bash
tail -n 15 /opt/ai-defense-manager/app/schemas/security_event.py
```

It was written correctly if the last three lines are as follows.

```text
if value is None:
    return None
return str(ip_address(value))
```

```bash
chown root:ai-defense /opt/ai-defense-manager/app/schemas/security_event.py && chmod 640 /opt/ai-defense-manager/app/schemas/security_event.py
```

Confirm that an invalid IP address and undefined fields are rejected.

```bash
runuser -u ai-defense -- /opt/ai-defense-manager/venv/bin/python -B - <<'PY'
import sys
sys.path.insert(0, "/opt/ai-defense-manager")

from app.schemas.security_event import SecurityEvent
from pydantic import ValidationError

base = {
    "source": "wazuh",
    "severity": "high",
    "event_category": "authentication",
    "event_summary": "Test event",
}

tests = [
    ("INVALID_IP_REJECTED", {**base, "source_ip": "invalid"}),
    ("EXTRA_FIELD_REJECTED", {**base, "full_log": "sensitive data"}),
]

for expected, data in tests:
    try:
        SecurityEvent(**data)
        print("FAILED:", expected)
    except ValidationError:
        print("PASS:", expected)
PY
```

## 6.2 AI Analysis Requests (analysis.py)

The events passed to the AI at one time are limited to 1–100, and the language to Japanese or English.

```bash
cat > /opt/ai-defense-manager/app/schemas/analysis.py <<'PY'
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.security_event import SecurityEvent


class AIAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: UUID = Field(default_factory=uuid4)
    events: list[SecurityEvent] = Field(min_length=1, max_length=100)
    analysis_context: str | None = Field(default=None, max_length=2000)
    requested_language: str = Field(default="ja", pattern=r"^(ja|en)$")
PY
```

```bash
chown root:ai-defense /opt/ai-defense-manager/app/schemas/analysis.py && chmod 640 /opt/ai-defense-manager/app/schemas/analysis.py
```

```bash
runuser -u ai-defense -- /opt/ai-defense-manager/venv/bin/python -B - <<'PY'
import sys
sys.path.insert(0, "/opt/ai-defense-manager")

from app.schemas.analysis import AIAnalysisRequest

request = AIAnalysisRequest(
    events=[
        {
            "source": "wazuh",
            "severity": "high",
            "event_category": "authentication",
            "event_summary": "Repeated authentication failures",
            "source_ip": "192.0.2.10",
        }
    ]
)

print("ANALYSIS_REQUEST_OK")
print("REQUEST_ID:", request.request_id)
print("EVENT_COUNT:", len(request.events))
print("LANGUAGE:", request.requested_language)
PY
```

## 6.3 AI Analysis Results (analysis_proposal.py)

The proposals returned by the AI carry the following safety constraints.

- Recommended actions are limited to six defined types
- Confidence (`confidence`) is 0.0–1.0
- The IDs of the supporting events are required
- A proposal to temporarily block an IP is allowed only for internet addresses (global IPs), with two or more supporting events, an expiry of at most 900 seconds (15 minutes), and human approval required
- The actual blocking is not implemented here

```bash
cat > /opt/ai-defense-manager/app/schemas/analysis_proposal.py <<'PY'
from enum import Enum
from ipaddress import ip_address
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RecommendedAction(str, Enum):
    NO_ACTION = "no_action"
    MONITOR = "monitor"
    COLLECT_EVIDENCE = "collect_evidence"
    NOTIFY = "notify"
    HUMAN_REVIEW = "human_review"
    TEMPORARY_BLOCK_IP = "temporary_block_ip"


class AIAnalysisProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=2000)
    severity: str = Field(pattern=r"^(info|low|medium|high|critical)$")
    confidence: float = Field(ge=0.0, le=1.0)

    evidence_event_ids: list[UUID] = Field(min_length=1, max_length=100)

    recommended_action: RecommendedAction

    target_ip: str | None = None
    ttl_seconds: int | None = Field(default=None, ge=1, le=900)

    requires_human_approval: bool = True
    reasoning: str = Field(min_length=1, max_length=4000)

    @model_validator(mode="after")
    def validate_action_constraints(self):
        if self.recommended_action == RecommendedAction.TEMPORARY_BLOCK_IP:
            if self.target_ip is None:
                raise ValueError("target_ip is required for block proposals")

            if self.ttl_seconds is None:
                raise ValueError("ttl_seconds is required for block proposals")

            if len(set(self.evidence_event_ids)) < 2:
                raise ValueError("block proposals require at least two distinct evidence events")

            address = ip_address(self.target_ip)

            if not address.is_global:
                raise ValueError("only globally routable IP addresses may be proposed for blocking")

            if not self.requires_human_approval:
                raise ValueError("block proposals must require human approval")

        elif self.target_ip is not None or self.ttl_seconds is not None:
            raise ValueError("target_ip and ttl_seconds are only valid for block proposals")

        return self
PY
```

```bash
tail -n 25 /opt/ai-defense-manager/app/schemas/analysis_proposal.py
```

```bash
chown root:ai-defense /opt/ai-defense-manager/app/schemas/analysis_proposal.py && chmod 640 /opt/ai-defense-manager/app/schemas/analysis_proposal.py
```

```bash
runuser -u ai-defense -- /opt/ai-defense-manager/venv/bin/python -B -c "from pathlib import Path; p=Path('/opt/ai-defense-manager/app/schemas/analysis_proposal.py'); compile(p.read_text(), str(p), 'exec'); print('PROPOSAL_SYNTAX_OK')"
```

Confirm that a normal proposal and a proposal to block a global IP are accepted, and a proposal to block a private IP is rejected.

```bash
runuser -u ai-defense -- /opt/ai-defense-manager/venv/bin/python -B - <<'PY'
import sys
from uuid import uuid4

sys.path.insert(0, "/opt/ai-defense-manager")

from app.schemas.analysis_proposal import AIAnalysisProposal

base = {
    "summary": "Repeated suspicious authentication attempts",
    "severity": "high",
    "confidence": 0.95,
    "evidence_event_ids": [uuid4(), uuid4()],
    "recommended_action": "human_review",
    "requires_human_approval": True,
    "reasoning": "Multiple correlated security events",
}

normal = AIAnalysisProposal(**{
    **base,
    "evidence_event_ids": [base["evidence_event_ids"][0]],
})
print("NORMAL_PROPOSAL_OK")

block = AIAnalysisProposal(**{
    **base,
    "recommended_action": "temporary_block_ip",
    "target_ip": "8.8.8.8",
    "ttl_seconds": 300,
})
print("PUBLIC_IP_BLOCK_PROPOSAL_OK")

try:
    AIAnalysisProposal(**{
        **base,
        "recommended_action": "temporary_block_ip",
        "target_ip": "192.168.0.1",
        "ttl_seconds": 300,
    })
    print("FAILED: PRIVATE_IP_ACCEPTED")
except ValueError:
    print("PRIVATE_IP_REJECTED")
PY
```

## 6.4 Action Candidates (action.py)

This is the type of the "action candidate" passed, based on the AI's proposal, to the Action Gateway (the part that carries out actual responses). A temporary IP block starts as pending approval (`pending`) and is not executed until a person approves it.

```bash
ls -l /opt/ai-defense-manager/app/schemas/action.py
```

```bash
cat > /opt/ai-defense-manager/app/schemas/action.py <<'PY'
from enum import Enum
from ipaddress import ip_address
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ActionType(str, Enum):
    NOTIFY = "notify"
    COLLECT_EVIDENCE = "collect_evidence"
    TEMPORARY_BLOCK_IP = "temporary_block_ip"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ActionProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: UUID = Field(default_factory=uuid4)
    source_analysis_id: UUID

    action_type: ActionType
    target_ip: str | None = None
    ttl_seconds: int | None = Field(default=None, ge=1, le=900)

    evidence_event_ids: list[UUID] = Field(min_length=1, max_length=100)

    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    requires_human_approval: bool = True

    @model_validator(mode="after")
    def validate_action(self):
        if self.action_type == ActionType.TEMPORARY_BLOCK_IP:
            if self.target_ip is None:
                raise ValueError("target_ip is required")

            if self.ttl_seconds is None:
                raise ValueError("ttl_seconds is required")

            if len(set(self.evidence_event_ids)) < 2:
                raise ValueError("at least two distinct evidence events are required")

            if not ip_address(self.target_ip).is_global:
                raise ValueError("only globally routable IP addresses are allowed")

            if not self.requires_human_approval:
                raise ValueError("human approval is mandatory")

            if self.approval_status != ApprovalStatus.PENDING:
                raise ValueError("block proposals must start as pending")

        elif self.target_ip is not None or self.ttl_seconds is not None:
            raise ValueError("target_ip and ttl_seconds are only valid for block actions")

        return self
PY
```

```bash
tail -n 30 /opt/ai-defense-manager/app/schemas/action.py
```

```bash
chown root:ai-defense /opt/ai-defense-manager/app/schemas/action.py && chmod 640 /opt/ai-defense-manager/app/schemas/action.py
```

```bash
runuser -u ai-defense -- /opt/ai-defense-manager/venv/bin/python -B -c "from pathlib import Path; p=Path('/opt/ai-defense-manager/app/schemas/action.py'); compile(p.read_text(), str(p), 'exec'); print('ACTION_SYNTAX_OK')"
```

Confirm that a notification candidate and a global IP block candidate (pending approval) are accepted, and that a private IP block, a block that is approved from the start, and a block with only one supporting event are rejected.

```bash
runuser -u ai-defense -- /opt/ai-defense-manager/venv/bin/python -B - <<'PY'
import sys
from uuid import uuid4

sys.path.insert(0, "/opt/ai-defense-manager")

from app.schemas.action import ActionProposal

analysis_id = uuid4()
event_ids = [uuid4(), uuid4()]

base = {
    "source_analysis_id": analysis_id,
    "evidence_event_ids": event_ids,
}

ActionProposal(**{
    **base,
    "action_type": "notify",
})
print("NOTIFY_ACTION_OK")

ActionProposal(**{
    **base,
    "action_type": "temporary_block_ip",
    "target_ip": "8.8.8.8",
    "ttl_seconds": 300,
})
print("PUBLIC_IP_BLOCK_PENDING_OK")

def must_reject(name, payload):
    try:
        ActionProposal(**payload)
    except ValueError:
        print(f"{name}_REJECTED")
    else:
        raise AssertionError(f"{name}_WAS_ACCEPTED")

must_reject("PRIVATE_IP", {
    **base,
    "action_type": "temporary_block_ip",
    "target_ip": "192.168.0.1",
    "ttl_seconds": 300,
})

must_reject("PREAPPROVED_BLOCK", {
    **base,
    "action_type": "temporary_block_ip",
    "target_ip": "8.8.8.8",
    "ttl_seconds": 300,
    "approval_status": "approved",
})

must_reject("INSUFFICIENT_EVIDENCE", {
    **base,
    "evidence_event_ids": [event_ids[0]],
    "action_type": "temporary_block_ip",
    "target_ip": "8.8.8.8",
    "ttl_seconds": 300,
})

print("ALL_ACTION_TESTS_PASSED")
PY
```

If `ALL_ACTION_TESTS_PASSED` is shown, all five items have passed.

## 6.5 Checking the Files and Cleaning Up

```bash
find /opt/ai-defense-manager/app -maxdepth 2 -type f -printf '%P\n' | sort
```

In the original build, an empty temporary file `analysis.py.tmp` had been created during the work, so it was deleted (not needed if it does not exist).

```bash
rm -f /opt/ai-defense-manager/app/schemas/analysis.py.tmp
```

# Summary of Part 11

## What Was Built

| File | Contents |
|---|---|
| `/opt/ai-defense-manager/venv` | Python virtual environment (FastAPI, Uvicorn, Pydantic, pydantic-settings, HTTPX) |
| `/opt/ai-defense-manager/requirements.lock` | List of installed packages |
| `app/main.py` | API (`/health`) |
| `app/core/config.py` | Settings (can be overridden by `AIDM_` environment variables) |
| `app/schemas/security_event.py` | Security events |
| `app/schemas/analysis.py` | AI analysis requests |
| `app/schemas/analysis_proposal.py` | AI analysis results |
| `app/schemas/action.py` | Action candidates |

## Safety Rules

- The application runs as the dedicated user `ai-defense`, which cannot log in, and cannot modify its own code.
- The API listens only on the machine itself (127.0.0.1).
- Only AI output that passes the defined types and constraints is accepted.
- IP blocks require a global IP, two or more supporting events, at most 15 minutes and human approval, and start as pending approval.

## What Remains

- Uvicorn is started by hand (it has not been made a systemd service). After Part 12 it was stopped with `kill`.
- The AI analysis processing (integration with Ollama) is built in the next part.

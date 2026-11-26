---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 55: Integration Checks and Preparing for High Request Volumes"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 55 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 54 we added masking of LLM output and the approval policy. Here we do the following.

1. Before moving on to real alerts and AI analysis, check VM 230 as an integrated whole
2. Check the safety boundaries with tests that make no outside communication (25 synthetic events, 9 analysis cases with simulated Ollama answers)
3. Check access control to the API and preparation for high request volumes (DoS)
4. Add a limit on Uvicorn concurrent connections, a limit on concurrent AI analyses, and a limit on HTTP body size

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: Integration Checks

## 1.1 Integration of Masking, Approval and Input

> **Run on: VM 230**

```bash
echo "===== VM230: AI DEFENSE FINAL INTEGRATION AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- 1. Sanitizer integration points ---"
grep -RInE \
  'sanitize_event_summary|sanitize_analysis_text|_convert_alert|event_summary=|rule_description=' \
  app --include='*.py'

echo
echo "--- 2. AI analysis trust boundary ---"
nl -ba app/services/ai_analysis.py | sed -n '1,260p'

echo
echo "--- 3. Analysis persistence and approval policy ---"
nl -ba app/services/analysis_history.py | sed -n '100,260p'

echo
echo "--- 4. Proposal validation ---"
nl -ba app/schemas/analysis_proposal.py | sed -n '1,180p'

echo
echo "--- 5. Wazuh API response boundary ---"
nl -ba app/api/wazuh.py | sed -n '1,130p'

echo
echo "--- 6. Potential action execution paths ---"
grep -RInE \
  'subprocess|os\.system|create_subprocess|iptables|nftables|firewall|execute_action|ActionGateway|action_gateway|approve_action|approval' \
  app --include='*.py' 2>/dev/null | head -200

echo
echo "--- 7. Modified source integrity and permissions ---"
stat -c '%n OWNER=%U GROUP=%G MODE=%a' \
  app/services/wazuh_relay.py \
  app/services/event_sanitizer.py \
  app/services/ai_analysis.py \
  app/services/analysis_history.py \
  app/schemas/analysis_proposal.py

sha256sum \
  app/services/wazuh_relay.py \
  app/services/event_sanitizer.py \
  app/services/ai_analysis.py \
  app/services/analysis_history.py \
  app/schemas/analysis_proposal.py

echo
echo "--- 8. Runtime status ---"
systemctl is-active ai-defense-manager.service
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "FILES_MODIFIED=NO"
echo "REAL_WAZUH_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "DATABASE_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

We confirmed that masking is used on each path, and that even if the LLM returns `requires_human_approval=false`, the server side overrides it so that approval is required, both when returning analysis results and when storing in the DB. There is no automatic execution; it goes only as far as storing proposals.

## 1.2 Schemas and Masking

> **Run on: VM 230**

```bash
echo "===== VM230: EVENT SCHEMA AND SANITIZER SECURITY AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- 1. Event sanitizer implementation ---"
nl -ba app/services/event_sanitizer.py

echo
echo "--- 2. SecurityEvent schema ---"
nl -ba app/schemas/security_event.py

echo
echo "--- 3. Analysis request schema ---"
nl -ba app/schemas/analysis.py

echo
echo "--- 4. Wazuh relay conversion and validation ---"
nl -ba app/services/wazuh_relay.py | sed -n '1,190p'

echo
echo "--- 5. Analysis API response boundary ---"
nl -ba app/api/analysis.py

echo
echo "--- 6. Wazuh request schema ---"
nl -ba app/schemas/wazuh.py

echo
echo "--- 7. Existing test inventory ---"
find . -maxdepth 4 -type f \
  \( -name 'test_*.py' -o -name '*_test.py' \) \
  -not -path './venv/*' -print | sort

echo
echo "--- 8. Runtime status ---"
systemctl is-active ai-defense-manager.service
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "FILES_MODIFIED=NO"
echo "REAL_WAZUH_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "DATABASE_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

Wazuh events are masked at conversion, the AI input is built from an allowlist, and `SecurityEvent` and analysis requests reject unknown fields. There are no test files, and the masking looks for common patterns, so there is no guarantee it can remove secrets in unknown forms.

# Chapter 2: Tests Without Outside Communication

## 2.1 Safety Boundary Tests (25 Cases)

No outside communication, DB writes or file changes.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED SECURITY BOUNDARY TESTS ====="

./venv/bin/python - <<'PY'
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import ValidationError

from app.services.event_sanitizer import (
    sanitize_event_summary,
    sanitize_analysis_text,
)
from app.services.wazuh_relay import _convert_alert
from app.services.ai_analysis import _build_event_payload, AIAnalysisError
from app.schemas.security_event import SecurityEvent
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import (
    AIAnalysisProposal,
    RecommendedAction,
)

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

def rejects(fn):
    try:
        fn()
    except (ValueError, ValidationError, AIAnalysisError):
        return True
    return False

# 1. Sanitizer behavior
sample = (
    "Bearer abc.def password=hunter2 "
    "contact=user@example.com host=203.0.113.10"
)
clean = sanitize_event_summary(sample)

check("BEARER_REDACTION", "abc.def" not in clean)
check("PASSWORD_REDACTION", "hunter2" not in clean)
check("EMAIL_REDACTION", "user@example.com" not in clean)
check("IP_REDACTION", "203.0.113.10" not in clean)
check("EVENT_LENGTH_LIMIT", len(sanitize_event_summary("x" * 900)) <= 512)
check("EMPTY_EVENT_FALLBACK", sanitize_event_summary("   ") == "[REDACTED_EVENT]")
check("NONSTRING_EVENT_FALLBACK", sanitize_event_summary(None) == "[REDACTED_EVENT]")
check(
    "INVALID_ANALYSIS_LENGTH_REJECTED",
    rejects(lambda: sanitize_analysis_text("test", True)),
)

# 2. Wazuh alert conversion: extra fields must not propagate
alert = {
    "timestamp": "2026-11-24T00:00:00Z",
    "rule.level": 10,
    "rule.id": "5710",
    "rule.description": "Bearer sampletoken password=secret123",
    "rule.groups": ["sshd"],
    "agent.id": "001",
    "full_log": "SENSITIVE_TEST_DATA",
    "data": {"password": "SENSITIVE_TEST_DATA"},
    "agent.name": "SENSITIVE_TEST_DATA",
}
event = _convert_alert(alert)

check("WAZUH_EVENT_CONVERSION", event.source == "wazuh")
check("WAZUH_EXTRA_FIELDS_NOT_PROPAGATED", not hasattr(event, "full_log"))
check("WAZUH_SUMMARY_SANITIZED", "secret123" not in event.event_summary)
check(
    "WAZUH_DESCRIPTION_SANITIZED",
    event.rule_description is not None and "sampletoken" not in event.rule_description,
)
check("WAZUH_AGENT_ID_ALLOWLIST", event.agent_id == "001")
check("WAZUH_CATEGORY_MAPPING", event.event_category == "remote_access")

# 3. Invalid Wazuh alert rejection
check(
    "NAIVE_TIMESTAMP_REJECTED",
    rejects(lambda: _convert_alert({
        **alert, "timestamp": "2026-11-24T00:00:00"
    })),
)
check(
    "BOOLEAN_RULE_LEVEL_REJECTED",
    rejects(lambda: _convert_alert({**alert, "rule.level": True})),
)
check(
    "INVALID_GROUP_REJECTED",
    rejects(lambda: _convert_alert({**alert, "rule.groups": ["sshd;admin"]})),
)

# 4. LLM payload allowlist and prohibited Wazuh fields
payload = _build_event_payload(event)
check(
    "LLM_PAYLOAD_EXACT_ALLOWLIST",
    set(payload) == {
        "event_id", "observed_at", "severity",
        "rule_id", "event_category", "event_summary"
    },
)
check("LLM_PAYLOAD_SANITIZED", "secret123" not in payload["event_summary"])

prohibited_event = SecurityEvent(
    source="wazuh",
    observed_at=datetime.now(timezone.utc),
    severity="high",
    event_category="authentication",
    event_summary="synthetic test",
    source_ip="203.0.113.10",
)
check(
    "WAZUH_SOURCE_IP_REJECTED_FROM_LLM",
    rejects(lambda: _build_event_payload(prohibited_event)),
)

# 5. Schema boundary checks
check(
    "UNKNOWN_SECURITY_EVENT_FIELD_REJECTED",
    rejects(lambda: SecurityEvent(
        source="internal",
        severity="low",
        event_category="other",
        event_summary="test",
        unexpected_field="value",
    )),
)

check(
    "ANALYSIS_REQUEST_EVENT_LIMIT",
    rejects(lambda: AIAnalysisRequest(events=[])),
)

# 6. Proposal policy schema checks (no execution)
ids = [uuid4(), uuid4()]

valid_block = AIAnalysisProposal(
    summary="synthetic proposal",
    severity="high",
    confidence=0.9,
    evidence_event_ids=ids,
    recommended_action=RecommendedAction.TEMPORARY_BLOCK_IP,
    target_ip="8.8.8.8",
    ttl_seconds=300,
    requires_human_approval=True,
    reasoning="synthetic test",
)
check(
    "PUBLIC_IP_BLOCK_PROPOSAL_SCHEMA",
    valid_block.requires_human_approval and valid_block.ttl_seconds == 300,
)
check(
    "PRIVATE_IP_BLOCK_REJECTED",
    rejects(lambda: AIAnalysisProposal(
        summary="test",
        severity="high",
        confidence=0.9,
        evidence_event_ids=ids,
        recommended_action=RecommendedAction.TEMPORARY_BLOCK_IP,
        target_ip="192.168.1.1",
        ttl_seconds=300,
        requires_human_approval=True,
        reasoning="test",
    )),
)
check(
    "SINGLE_EVIDENCE_BLOCK_REJECTED",
    rejects(lambda: AIAnalysisProposal(
        summary="test",
        severity="high",
        confidence=0.9,
        evidence_event_ids=[ids[0]],
        recommended_action=RecommendedAction.TEMPORARY_BLOCK_IP,
        target_ip="8.8.8.8",
        ttl_seconds=300,
        requires_human_approval=True,
        reasoning="test",
    )),
)

print()
print(f"TESTS_PASSED={passed}")
print(f"TESTS_FAILED={failed}")
print("EXTERNAL_NETWORK_REQUESTS=0")
print("OLLAMA_REQUESTS=0")
print("DATABASE_WRITES=0")
PY

echo
echo "--- Service remains active ---"
systemctl is-active ai-defense-manager.service
echo "===== TEST RUN COMPLETE ====="
```

All 25 passed. We confirmed removal of extra fields in Wazuh events, masking of secrets, the LLM input allowlist, and rejection of invalid events and dangerous blocking proposals.

## 2.2 Analysis Tests (Simulated Ollama Answers, 9 Cases)

We test `analyze_events()` with simulated Ollama answers.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: MOCKED AI ANALYSIS PIPELINE TEST ====="

./venv/bin/python - <<'PY'
import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.analysis import AIAnalysisRequest
from app.schemas.security_event import SecurityEvent
from app.services import ai_analysis

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

class FakeResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass

    def json(self):
        return {"message": {"content": self.content}}

class FakeAsyncClient:
    response_content = None
    captured_payload = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, json):
        FakeAsyncClient.captured_payload = json
        return FakeResponse(FakeAsyncClient.response_content)

async def main():
    original_client = ai_analysis.httpx.AsyncClient
    ai_analysis.httpx.AsyncClient = FakeAsyncClient

    try:
        event = SecurityEvent(
            source="wazuh",
            observed_at=datetime.now(timezone.utc),
            severity="high",
            rule_id="5710",
            agent_id="001",
            event_category="authentication",
            event_summary="Synthetic authentication alert",
        )

        request = AIAnalysisRequest(
            events=[event],
            analysis_context="CONTEXT_SECRET_SHOULD_NOT_BE_FORWARDED",
            requested_language="en",
        )

        # Case 1: A model tries to waive approval for a notify action.
        FakeAsyncClient.response_content = json.dumps({
            "summary": "password=hunter2 contact=test@example.com host=8.8.8.8",
            "severity": "high",
            "confidence": 0.91,
            "evidence_event_ids": [str(event.event_id)],
            "recommended_action": "notify",
            "target_ip": None,
            "ttl_seconds": None,
            "requires_human_approval": False,
            "reasoning": "Bearer synthetic-token should be redacted",
        })

        proposal = await ai_analysis.analyze_events(request)

        check(
            "LLM_RESPONSE_SUMMARY_SECRET_REDACTION",
            "hunter2" not in proposal.summary,
        )
        check(
            "LLM_RESPONSE_EMAIL_REDACTION",
            "test@example.com" not in proposal.summary,
        )
        check(
            "LLM_RESPONSE_IP_REDACTION",
            "8.8.8.8" not in proposal.summary,
        )
        check(
            "LLM_RESPONSE_REASONING_REDACTION",
            "synthetic-token" not in proposal.reasoning,
        )
        check(
            "SERVER_FORCES_NOTIFY_APPROVAL",
            proposal.requires_human_approval is True,
        )
        check(
            "LLM_INPUT_USES_ALLOWLIST",
            set(FakeAsyncClient.captured_payload["messages"][1]["content"]
                and json.loads(FakeAsyncClient.captured_payload["messages"][1]["content"])["events"][0])
            == {
                "event_id", "observed_at", "severity",
                "rule_id", "event_category", "event_summary"
            },
        )
        check(
            "ANALYSIS_CONTEXT_NOT_FORWARDED",
            "CONTEXT_SECRET_SHOULD_NOT_BE_FORWARDED"
            not in json.dumps(FakeAsyncClient.captured_payload),
        )

        # Case 2: A no_action response remains non-approval-required.
        FakeAsyncClient.response_content = json.dumps({
            "summary": "No action required",
            "severity": "info",
            "confidence": 0.8,
            "evidence_event_ids": [str(event.event_id)],
            "recommended_action": "no_action",
            "target_ip": None,
            "ttl_seconds": None,
            "requires_human_approval": True,
            "reasoning": "Synthetic no-action test",
        })

        no_action = await ai_analysis.analyze_events(request)
        check(
            "SERVER_NO_ACTION_POLICY",
            no_action.requires_human_approval is False,
        )

        # Case 3: Unknown evidence IDs must be rejected.
        FakeAsyncClient.response_content = json.dumps({
            "summary": "Invalid evidence test",
            "severity": "high",
            "confidence": 0.9,
            "evidence_event_ids": [str(uuid4())],
            "recommended_action": "notify",
            "target_ip": None,
            "ttl_seconds": None,
            "requires_human_approval": True,
            "reasoning": "Synthetic invalid evidence",
        })

        try:
            await ai_analysis.analyze_events(request)
            unknown_evidence_rejected = False
        except ai_analysis.AIAnalysisError:
            unknown_evidence_rejected = True

        check("UNKNOWN_EVIDENCE_ID_REJECTED", unknown_evidence_rejected)

    finally:
        ai_analysis.httpx.AsyncClient = original_client

    print()
    print(f"TESTS_PASSED={passed}")
    print(f"TESTS_FAILED={failed}")

asyncio.run(main())
PY

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service

echo "REAL_OLLAMA_REQUESTS=0"
echo "REAL_WAZUH_REQUESTS=0"
echo "DATABASE_WRITES=0"
echo "SOURCE_FILES_MODIFIED=NO"
echo "===== MOCKED ANALYSIS TEST COMPLETE ====="
```

| Checked | Result |
|---|---|
| Masking of secrets, email and IPs in LLM output | passed |
| For `notify`, even if the LLM says no approval is needed, the server side requires approval | passed |
| Unknown evidence event IDs are rejected | passed |
| Actual connections to Wazuh or Ollama, DB writes, source changes | none |

In total, **all 34 passed** (0 failures). We also confirmed that the `analysis_context` accepted by the API is not passed into the LLM input.

# Chapter 3: Access Control and DoS Checks

## 3.1 Access Control

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API ACCESS CONTROL AUDIT ====="

echo
echo "--- 1. Application entrypoint and middleware ---"
nl -ba app/main.py

echo
echo "--- 2. Authentication and authorization references ---"
grep -RInE \
  'HTTPBearer|OAuth2|APIKey|HTTPBasic|Depends\(|Security\(|middleware|authentication|authorization|CORS|CORSMiddleware' \
  app --include='*.py' || true

echo
echo "--- 3. All API route declarations ---"
grep -RInE \
  '@router\.(get|post|put|patch|delete)|APIRouter\(' \
  app/api --include='*.py'

echo
echo "--- 4. Runtime configuration definitions ---"
nl -ba app/core/config.py

echo
echo "--- 5. Service bind and execution settings ---"
systemctl show ai-defense-manager.service \
  -p User -p Group -p ExecStart -p EnvironmentFiles \
  -p NoNewPrivileges -p ProtectSystem \
  -p RestrictAddressFamilies -p ReadWritePaths

echo
echo "--- 6. Listener verification ---"
ss -lntp | grep ':8000' || true

echo
echo "--- 7. Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "FILES_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

The API listens only on `127.0.0.1:8000`, runs as `ai-defense`, with `NoNewPrivileges=yes` and `ProtectSystem=strict`, but there was no authentication, authorization or CORS middleware within the application.

## 3.2 Documentation and Routes

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: FASTAPI DOCUMENTATION AND ROUTE AUDIT ====="

./venv/bin/python - <<'PY'
from app.main import app

print("--- FastAPI documentation configuration ---")
print("DOCS_URL =", app.docs_url)
print("REDOC_URL =", app.redoc_url)
print("OPENAPI_URL =", app.openapi_url)

print()
print("--- Registered routes ---")
for route in app.routes:
    methods = sorted(getattr(route, "methods", []) or [])
    path = getattr(route, "path", "<unknown>")
    name = getattr(route, "name", "<unknown>")
    print(f"PATH={path} METHODS={','.join(methods)} NAME={name}")

print()
print("--- OpenAPI security schemes ---")
schema = app.openapi()
components = schema.get("components", {})
print("SECURITY_SCHEMES =", list(components.get("securitySchemes", {}).keys()))
print("GLOBAL_SECURITY =", schema.get("security", []))
PY

echo
echo "--- Listener addresses ---"
ss -lntp | grep -E 'uvicorn|:8000' || true

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "FILES_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Endpoint | State |
|---|---|
| `/docs` | enabled |
| `/redoc` | enabled |
| `/openapi.json` | enabled |
| `/health` | enabled |
| API authentication scheme | none |

It is `127.0.0.1` only, but the API specification can be viewed without authentication. Our policy is to disable `/docs`, `/redoc` and `/openapi.json` in production.

## 3.3 Preparing for High Request Volumes

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API RESOURCE AND DOS RESILIENCE AUDIT ====="

echo
echo "--- 1. Uvicorn startup arguments ---"
systemctl show ai-defense-manager.service -p ExecStart

echo
echo "--- 2. Request size and rate limiting references ---"
grep -RInE \
  'Content-Length|content-length|RequestSize|Body\(|max_body|rate.limit|slowapi|Limiter|Semaphore|asyncio\.Semaphore|timeout|concurrency|limit_concurrency|limit_max_requests' \
  app /etc/systemd/system/ai-defense-manager.service \
  --include='*.py' --include='*.service' 2>/dev/null || true

echo
echo "--- 3. API input constraints ---"
grep -RInE \
  'Field\(|Query\(|max_length|min_length|ge=|le=|max_items|list\[' \
  app/api app/schemas --include='*.py'

echo
echo "--- 4. Dependency versions ---"
./venv/bin/python - <<'PY'
from importlib.metadata import PackageNotFoundError, version

for package in ("fastapi", "starlette", "uvicorn", "pydantic", "httpx"):
    try:
        print(f"{package}={version(package)}")
    except PackageNotFoundError:
        print(f"{package}=NOT_INSTALLED")
PY

echo
echo "--- 5. Runtime limits ---"
systemctl show ai-defense-manager.service \
  -p MemoryMax -p TasksMax -p LimitNOFILE -p CPUQuota \
  -p TimeoutStartUSec -p TimeoutStopUSec

echo
echo "--- 6. Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "FILES_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

```bash
cd /opt/ai-defense-manager

echo "===== VM230: UVICORN AND CONCURRENCY DETAIL AUDIT ====="

echo
echo "--- 1. Full service unit ---"
systemctl cat ai-defense-manager.service

echo
echo "--- 2. Actual running process arguments ---"
PID="$(systemctl show ai-defense-manager.service -p MainPID --value)"
python3 - "$PID" <<'PY'
import pathlib
import sys

pid = sys.argv[1]
raw = pathlib.Path(f"/proc/{pid}/cmdline").read_bytes()
args = raw.decode(errors="replace").split("\0")
print("PROCESS_ARGUMENTS:")
for arg in args:
    if arg:
        print(arg)
PY

echo
echo "--- 3. Analysis endpoint execution flow ---"
nl -ba app/api/analysis.py
nl -ba app/api/wazuh.py | sed -n '30,100p'

echo
echo "--- 4. Ollama request lifecycle ---"
nl -ba app/services/ai_analysis.py | sed -n '70,145p'

echo
echo "--- 5. Uvicorn concurrency controls available ---"
./venv/bin/uvicorn --help | grep -E \
  'limit-concurrency|limit-max-requests|backlog|timeout-keep-alive|workers'

echo
echo "--- 6. Existing middleware inventory ---"
grep -RInE \
  'BaseHTTPMiddleware|@app\.middleware|add_middleware|asyncio\.Lock|Semaphore|CapacityLimiter' \
  app --include='*.py' || true

echo
echo "--- 7. Runtime status ---"
systemctl is-active ai-defense-manager.service
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "FILES_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Item | State |
|---|---|
| Maximum number of events | 100 |
| Maximum fetched from Wazuh | 100 |
| LLM response timeout | 60 seconds |
| Relay communication timeout | 15 seconds |
| Maximum wait for SQLite lock | 5 seconds |
| Memory limit | 1GiB |
| HTTP body size limit | **none** |
| Concurrent connection limit (`--limit-concurrency`) | **not specified** |
| Concurrent AI analysis limit | **none** |

Even with one worker, the API is asynchronous and processes several requests at once. The two analysis APIs ask Ollama for analysis, so when requests pile up, waits and timeouts increase (Ollama's parallelism is 1).

## 3.4 The Limits to Add

| Measure | Value |
|---|---|
| Uvicorn concurrent connections | 8 |
| Connection backlog | 32 |
| Keep-Alive timeout | 5 seconds |
| Concurrent AI analyses | 1 (excess requests wait) |
| HTTP body size | 256KiB (`HTTP 413` if exceeded) |
| Number of workers | stays at 1 |

Uvicorn's connection limits alone cannot limit body size, so we add an ASGI middleware that counts the size while reading the body. Storage in SQLite, communication with the Relay, LLM prompts and the safety policy are not changed.

# Chapter 4: Adding the Limits

## 4.1 Checking Before the Change

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: DOS PROTECTION IMPLEMENTATION PRECHECK ====="

echo
echo "--- 1. Application entrypoint ---"
cat app/main.py

echo
echo "--- 2. Complete AI analysis service ---"
cat app/services/ai_analysis.py

echo
echo "--- 3. Systemd unit and drop-ins ---"
systemctl cat ai-defense-manager.service

echo
echo "--- 4. Source file metadata ---"
stat -c '%n owner=%U group=%G mode=%a size=%s' \
  app/main.py \
  app/services/ai_analysis.py \
  /etc/systemd/system/ai-defense-manager.service

echo
echo "--- 5. Python runtime ---"
./venv/bin/python --version

echo
echo "--- 6. Existing test directories ---"
find . -maxdepth 3 -type d \
  \( -name tests -o -name test \) -print

echo
echo "--- 7. Current service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "FILES_MODIFIED=NO"
echo "BACKUPS_CREATED=NO"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

```bash
cd /opt/ai-defense-manager

echo "===== VM230: DOS PATCH FINAL PRECHECK ====="

echo
echo "--- 1. Existing test files ---"
find tests -maxdepth 3 -type f -printf '%p\n' | sort

echo
echo "--- 2. Existing test configuration ---"
find . -maxdepth 2 -type f \
  \( -name 'pytest.ini' -o -name 'pyproject.toml' -o -name 'tox.ini' -o -name 'conftest.py' \) \
  -print

echo
echo "--- 3. Full systemd ExecStart ---"
systemctl show ai-defense-manager.service -p ExecStart --value

echo
echo "--- 4. Existing drop-in files ---"
find /etc/systemd/system/ai-defense-manager.service.d \
  -maxdepth 1 -type f -printf '%f\n' 2>/dev/null | sort

echo
echo "--- 5. Current source hashes ---"
sha256sum app/main.py app/services/ai_analysis.py

echo
echo "--- 6. Current service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "FILES_MODIFIED=NO"
echo "BACKUPS_CREATED=NO"
echo "SERVICE_RESTARTED=NO"
```

The waiting for AI analysis is placed at the entry of the existing analysis function, so there is only one concurrent request to Ollama. The body limit applies to the whole application. Uvicorn settings are overridden with a dedicated drop-in rather than rewriting the systemd unit itself (easy to save, compare and revert).

## 4.2 Applying the Patch

After making copies, we change the code and the systemd settings. The service is not restarted yet.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: APPLY DOS PROTECTION PATCH ====="

BACKUP_DIR="/var/backups/ai-defense-manager/dos-protection-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR/systemd"

cp -a app/main.py app/services/ai_analysis.py "$BACKUP_DIR/"
cp -a /etc/systemd/system/ai-defense-manager.service "$BACKUP_DIR/systemd/"
cp -a /etc/systemd/system/ai-defense-manager.service.d/20-sqlite.conf "$BACKUP_DIR/systemd/"

sha256sum \
  "$BACKUP_DIR/main.py" \
  "$BACKUP_DIR/ai_analysis.py" \
  "$BACKUP_DIR/systemd/ai-defense-manager.service" \
  "$BACKUP_DIR/systemd/20-sqlite.conf" \
  > "$BACKUP_DIR/SHA256SUMS"

echo "BACKUP_DIR=$BACKUP_DIR"
echo "BACKUP_VERIFICATION:"
sha256sum -c "$BACKUP_DIR/SHA256SUMS"

echo
echo "--- Apply application patches ---"

./venv/bin/python - <<'PY'
from pathlib import Path

main_path = Path("app/main.py")
analysis_path = Path("app/services/ai_analysis.py")

main = main_path.read_text()
analysis = analysis_path.read_text()

old_import = "from fastapi import FastAPI\n"
new_import = """from fastapi import FastAPI


class RequestBodyLimitMiddleware:
    def __init__(self, app, max_body_bytes: int = 256 * 1024):
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")

        if content_length is not None:
            try:
                declared_length = int(content_length)
            except ValueError:
                declared_length = None

            if declared_length is not None and declared_length > self.max_body_bytes:
                await self._reject(send)
                return

        body = bytearray()

        while True:
            message = await receive()

            if message["type"] == "http.disconnect":
                return

            if message["type"] != "http.request":
                continue

            chunk = message.get("body", b"")

            if len(body) + len(chunk) > self.max_body_bytes:
                await self._reject(send)
                return

            body.extend(chunk)

            if not message.get("more_body", False):
                break

        body_bytes = bytes(body)
        replayed = False

        async def replay_receive():
            nonlocal replayed
            if not replayed:
                replayed = True
                return {
                    "type": "http.request",
                    "body": body_bytes,
                    "more_body": False,
                }
            return await receive()

        await self.app(scope, replay_receive, send)

    async def _reject(self, send):
        body = b'{"detail":"Request body exceeds 256 KiB limit"}'
        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })
"""

if main.count(old_import) != 1:
    raise RuntimeError("Unexpected FastAPI import block; no main.py changes made")

main = main.replace(old_import, new_import, 1)

app_marker = """    lifespan=lifespan,
)

app.include_router(analysis_router)
"""
app_replacement = """    lifespan=lifespan,
)

app.add_middleware(
    RequestBodyLimitMiddleware,
    max_body_bytes=256 * 1024,
)

app.include_router(analysis_router)
"""

if main.count(app_marker) != 1:
    raise RuntimeError("Unexpected FastAPI app construction; no main.py changes made")

main = main.replace(app_marker, app_replacement, 1)

if "RequestBodyLimitMiddleware" in analysis:
    raise RuntimeError("Unexpected existing analysis semaphore patch")

analysis = analysis.replace(
    "import json\n",
    "import asyncio\nimport json\n",
    1,
)

analysis = analysis.replace(
    'MODEL_NAME = "qwen3:8b"\n',
    'MODEL_NAME = "qwen3:8b"\n\n_ANALYSIS_SEMAPHORE = asyncio.Semaphore(1)\n',
    1,
)

function_marker = "async def analyze_events(\n"
if analysis.count(function_marker) != 1:
    raise RuntimeError("Unexpected analyze_events declaration")

analysis = analysis.replace(
    function_marker,
    "async def _analyze_events_unlimited(\n",
    1,
)

analysis += """


async def analyze_events(
    request: AIAnalysisRequest,
) -> AIAnalysisProposal:
    # Serialize Ollama inference; excess analysis requests wait here.
    async with _ANALYSIS_SEMAPHORE:
        return await _analyze_events_unlimited(request)
"""

main_path.write_text(main)
analysis_path.write_text(analysis)

print("MAIN_BODY_LIMIT_PATCH=APPLIED")
print("ANALYSIS_SEMAPHORE_PATCH=APPLIED")
PY

PATCH_STATUS=$?

if [ "$PATCH_STATUS" -ne 0 ]; then
  echo "APPLICATION_PATCH=FAILED"
else
  echo
  echo "--- Install Uvicorn systemd drop-in ---"

  cat > /etc/systemd/system/ai-defense-manager.service.d/30-dos-protection.conf <<'EOF'
[Service]
ExecStart=
ExecStart=/opt/ai-defense-manager/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --limit-concurrency 8 --backlog 32 --timeout-keep-alive 5
EOF

  chmod 644 /etc/systemd/system/ai-defense-manager.service.d/30-dos-protection.conf

  echo
  echo "--- Python syntax validation ---"
  ./venv/bin/python -m py_compile app/main.py app/services/ai_analysis.py
  echo "PYTHON_SYNTAX_EXIT=$?"

  echo
  echo "--- Ownership and permissions ---"
  stat -c '%n owner=%U group=%G mode=%a size=%s' \
    app/main.py \
    app/services/ai_analysis.py \
    /etc/systemd/system/ai-defense-manager.service.d/30-dos-protection.conf

  echo
  echo "--- New source hashes ---"
  sha256sum app/main.py app/services/ai_analysis.py \
    /etc/systemd/system/ai-defense-manager.service.d/30-dos-protection.conf

  echo
  echo "--- systemd configuration verification ---"
  systemd-analyze verify ai-defense-manager.service
  echo "SYSTEMD_VERIFY_EXIT=$?"

  echo
  echo "--- Effective ExecStart ---"
  systemctl show ai-defense-manager.service -p ExecStart

  echo
  echo "--- Existing service state (not restarted) ---"
  systemctl is-active ai-defense-manager.service
fi

echo
echo "BACKUP_DIR=$BACKUP_DIR"
echo "SERVICE_RESTARTED=NO"
echo "OLLAMA_REQUESTED=NO"
echo "WAZUH_REQUESTED=NO"
echo "DATABASE_TEST_WRITES=NO"
```

The SHA256 comparison of the copies of the four files, the Python syntax check and the systemd settings check all passed. The copies are in `/var/backups/ai-defense-manager/dos-protection-20261123-205302`.

## 4.3 Independent Tests (8 Cases)

Without actual communication or Ollama, we test by calling the ASGI middleware and the semaphore directly.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: DOS PROTECTION ISOLATED TESTS ====="

./venv/bin/python - <<'PY'
import asyncio
from unittest.mock import patch

from app.main import RequestBodyLimitMiddleware
import app.services.ai_analysis as ai


MAX = 256 * 1024
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


async def run_middleware(body_chunks, headers=None):
    messages = [
        {
            "type": "http.request",
            "body": chunk,
            "more_body": index < len(body_chunks) - 1,
        }
        for index, chunk in enumerate(body_chunks)
    ]
    if not messages:
        messages = [{"type": "http.request", "body": b"", "more_body": False}]

    index = 0
    received_body = bytearray()
    sent = []

    async def receive():
        nonlocal index
        if index < len(messages):
            message = messages[index]
            index += 1
            return message
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    async def app(scope, receive_inner, send_inner):
        while True:
            message = await receive_inner()
            if message["type"] == "http.disconnect":
                break
            if message["type"] == "http.request":
                received_body.extend(message.get("body", b""))
                if not message.get("more_body", False):
                    break
        await send_inner({
            "type": "http.response.start",
            "status": 200,
            "headers": [],
        })
        await send_inner({
            "type": "http.response.body",
            "body": b"ok",
        })

    middleware = RequestBodyLimitMiddleware(app, MAX)
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/test",
        "headers": headers or [],
    }
    await middleware(scope, receive, send)

    status = next(
        (m["status"] for m in sent if m["type"] == "http.response.start"),
        None,
    )
    return status, bytes(received_body), sent


async def test_middleware():
    status, body, _ = await run_middleware([b"x" * MAX])
    check("BODY_EXACT_LIMIT_ACCEPTED", status == 200 and len(body) == MAX)

    status, body, _ = await run_middleware([b"x" * (MAX + 1)])
    check("BODY_OVER_LIMIT_REJECTED_413", status == 413 and not body)

    status, body, _ = await run_middleware(
        [b"x"],
        [(b"content-length", str(MAX + 1).encode())],
    )
    check("CONTENT_LENGTH_EARLY_REJECTION", status == 413 and not body)

    status, body, _ = await run_middleware([b"a" * 100, b"b" * 200])
    check("CHUNKED_BODY_REPLAY", status == 200 and body == b"a" * 100 + b"b" * 200)

    status, body, _ = await run_middleware(
        [b"x" * 200, b"y" * (MAX - 199)]
    )
    check("CHUNKED_BODY_OVER_LIMIT", status == 413 and not body)


async def test_semaphore():
    active = 0
    maximum_active = 0
    entered = 0
    release = asyncio.Event()

    async def fake_analysis(request):
        nonlocal active, maximum_active, entered
        active += 1
        entered += 1
        maximum_active = max(maximum_active, active)
        if entered == 3:
            release.set()
        await release.wait()
        await asyncio.sleep(0)
        active -= 1
        return "mock-result"

    class DummyRequest:
        pass

    async with ai._ANALYSIS_SEMAPHORE:
        pass

    with patch.object(ai, "_analyze_events_unlimited", fake_analysis):
        tasks = [
            asyncio.create_task(ai.analyze_events(DummyRequest()))
            for _ in range(3)
        ]

        for _ in range(100):
            await asyncio.sleep(0.01)
            if entered == 1:
                break

        first_wave = entered
        check("ANALYSIS_ONLY_ONE_ACTIVE", first_wave == 1 and active == 1)

        release.set()
        results = await asyncio.gather(*tasks)

    check("ANALYSIS_SEMAPHORE_MAX_ONE", maximum_active == 1)
    check("ANALYSIS_WAITERS_COMPLETED", results == ["mock-result"] * 3)


async def main():
    await test_middleware()
    await test_semaphore()

asyncio.run(main())

print(f"TESTS_PASSED={passed}")
print(f"TESTS_FAILED={failed}")
PY

echo
echo "--- Service state (unchanged) ---"
systemctl is-active ai-defense-manager.service

echo
echo "--- Current listener ---"
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "NETWORK_REQUESTS=NO"
echo "OLLAMA_REQUESTED=NO"
echo "WAZUH_REQUESTED=NO"
echo "DATABASE_WRITES=NO"
echo "SERVICE_RESTARTED=NO"
```

| Checked | Result |
|---|---|
| Exactly 256KiB | accepted |
| Over 256KiB | `HTTP 413` |
| Early rejection by Content-Length | succeeded |
| Body sent in chunks | processed correctly |
| Concurrent AI analyses | at most 1 |
| Waiting analyses | finish in order |

**All 8 passed.**

## 4.4 Having systemd Load the Settings

This only loads the new settings, not a restart. The current API process is unaffected.

> **Run on: VM 230**

```bash
echo "===== VM230: DOS PROTECTION SYSTEMD CONFIGURATION LOAD ====="

echo
echo "--- Reload systemd configuration ---"
systemctl daemon-reload
echo "DAEMON_RELOAD_EXIT=$?"

echo
echo "--- Effective service configuration ---"
systemctl cat ai-defense-manager.service

echo
echo "--- Verify unit configuration ---"
systemd-analyze verify ai-defense-manager.service
echo "SYSTEMD_VERIFY_EXIT=$?"

echo
echo "--- Running process ---"
systemctl show ai-defense-manager.service -p MainPID -p ActiveState -p SubState

echo
echo "--- Current listener ---"
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "SERVICE_RESTARTED=NO"
echo "OLLAMA_REQUESTED=NO"
echo "WAZUH_REQUESTED=NO"
echo "DATABASE_WRITES=NO"
```

## 4.5 Restarting

> **Run on: VM 230**

```bash
echo "===== VM230: ACTIVATE DOS PROTECTION ====="

systemctl restart ai-defense-manager.service
RESTART_EXIT=$?

echo "RESTART_EXIT=$RESTART_EXIT"

echo
echo "--- Service status ---"
systemctl status ai-defense-manager.service --no-pager -l

echo
echo "--- Process and listener ---"
systemctl show ai-defense-manager.service \
  -p MainPID -p ActiveState -p SubState

ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "--- Health endpoint ---"
curl --max-time 5 -sS -w '\nHTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "--- Effective Uvicorn arguments ---"
PID="$(systemctl show ai-defense-manager.service -p MainPID --value)"
python3 - "$PID" <<'PY'
import pathlib
import sys

raw = pathlib.Path(f"/proc/{sys.argv[1]}/cmdline").read_bytes()
for arg in raw.decode(errors="replace").split("\0"):
    if arg:
        print(arg)
PY

echo
echo "OLLAMA_CONFIGURATION_CHANGED=NO"
echo "WAZUH_CONFIGURATION_CHANGED=NO"
echo "POSTGRES_CONFIGURATION_CHANGED=NO"
echo "FIREWALL_CONFIGURATION_CHANGED=NO"
```

The restart finished normally, and Uvicorn's new startup arguments included 8 concurrent connections, a backlog of 32 and Keep-Alive 5 seconds. The check right after (9 milliseconds after startup) showed port 8000 not yet listening, and `/health` gave `HTTP 000`.

> **Run on: VM 230**

```bash
echo "===== VM230: DOS PROTECTION POST-RESTART VERIFICATION ====="

echo
echo "--- Wait for listener (maximum 30 seconds) ---"

READY=0
for i in $(seq 1 30); do
    if ss -lnt | grep -q '127.0.0.1:8000'; then
        READY=1
        echo "LISTENER_READY=YES"
        echo "WAIT_SECONDS=$i"
        break
    fi
    sleep 1
done

echo
echo "--- Listener ---"
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "--- Health endpoint ---"
curl --max-time 5 -sS -w '\nHTTP_STATUS=%{http_code}\n' \
    http://127.0.0.1:8000/health

echo
echo "--- Recent startup logs ---"
journalctl -u ai-defense-manager.service -n 35 --no-pager

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "LISTENER_READY=$READY"
```

Uvicorn was PID `1681`, `active`, listening on `127.0.0.1:8000`, `/health` gave `HTTP 200`, and completion of application startup was also confirmed.

## 4.6 Testing the Body Limit on the Running Server

Without connecting to Ollama, Wazuh or the DB, we send requests to a test URL that does not exist.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: LIVE HTTP BODY LIMIT VERIFICATION ====="

./venv/bin/python - <<'PY'
import http.client
import json

HOST = "127.0.0.1"
PORT = 8000
LIMIT = 256 * 1024
PATH = "/__dos_protection_test__"

passed = 0
failed = 0

def check(name, expected, actual):
    global passed, failed
    ok = expected == actual
    print(f"{name}={'PASS' if ok else 'FAIL'} EXPECTED={expected} ACTUAL={actual}")
    if ok:
        passed += 1
    else:
        failed += 1

def fixed_request(body, declared_length=None):
    conn = http.client.HTTPConnection(HOST, PORT, timeout=10)
    headers = {}
    if declared_length is not None:
        headers["Content-Length"] = str(declared_length)
    conn.request("POST", PATH, body=body, headers=headers)
    response = conn.getresponse()
    status = response.status
    response.read()
    conn.close()
    return status

def chunked_request(chunks):
    conn = http.client.HTTPConnection(HOST, PORT, timeout=10)
    conn.putrequest("POST", PATH)
    conn.putheader("Transfer-Encoding", "chunked")
    conn.endheaders()
    for chunk in chunks:
        conn.send(f"{len(chunk):X}\r\n".encode("ascii"))
        conn.send(chunk)
        conn.send(b"\r\n")
    conn.send(b"0\r\n\r\n")
    response = conn.getresponse()
    status = response.status
    response.read()
    conn.close()
    return status

check(
    "HTTP_BODY_EXACT_LIMIT",
    404,
    fixed_request(b"x" * LIMIT),
)

check(
    "HTTP_BODY_OVER_LIMIT",
    413,
    fixed_request(b"x" * (LIMIT + 1)),
)

check(
    "HTTP_CONTENT_LENGTH_EARLY_REJECTION",
    413,
    fixed_request(b"", declared_length=LIMIT + 1),
)

check(
    "HTTP_CHUNKED_BODY_WITHIN_LIMIT",
    404,
    chunked_request([b"a" * 100, b"b" * 200]),
)

check(
    "HTTP_CHUNKED_BODY_OVER_LIMIT",
    413,
    chunked_request([b"a" * 200, b"b" * (LIMIT - 199)]),
)

print(f"TESTS_PASSED={passed}")
print(f"TESTS_FAILED={failed}")
PY

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "--- Listener ---"
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "OLLAMA_REQUESTED=NO"
echo "WAZUH_REQUESTED=NO"
echo "DATABASE_WRITES=NO"
echo "SERVICE_RESTARTED=NO"
```

| Test | Result |
|---|---|
| Exactly 256KiB | passed (`404`; the body was accepted) |
| Over 256KiB | `HTTP 413`, passed |
| Early rejection by Content-Length | `HTTP 413`, passed |
| Chunked body (within the limit) | passed |
| Chunked body (over the limit) | `HTTP 413`, passed |

**All 5 passed.**

# Closing Notes

In Part 55 we checked VM 230 as a whole and prepared for high request volumes.

| Item | Result |
|---|---|
| Integration tests | all 34 passed (no outside communication) |
| API exposure | `127.0.0.1:8000` only; no application authentication yet |
| Uvicorn | 8 concurrent connections, backlog 32, Keep-Alive 5 seconds (systemd drop-in) |
| AI analysis | one at a time (excess requests wait) |
| HTTP body | up to 256KiB (`413` if exceeded) |
| Tests | 8 independent and 5 on the running server, all passed |

In the next part, Part 56, we start by checking API authentication and authorization, and build token authentication for the API.

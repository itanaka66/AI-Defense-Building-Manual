---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 19: Minimizing the Information Passed to the LLM"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 19 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". By the end of Part 18, Wazuh alerts could be analyzed by the AI (Ollama's qwen3:8b) and the results kept in SQLite. Here we check **what remains in SQLite** and **what is being passed to the LLM**, and fix things so that no unnecessary information is passed.

1. Check the SQLite columns and the saving code
2. Limit the event fields sent to the LLM to six defined fields
3. Replace event categories with defined fixed values
4. Mask secrets, email addresses and IP addresses in the event summaries sent to the LLM

The original Wazuh events and the SQLite storage specification are not changed.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **ai-defense-manager VM 230 (root)**.

# Chapter 1: Reviewing Storage and Input

## 1.1 SQLite Columns

```bash
cd /opt/ai-defense-manager && runuser -u ai-defense -- ./venv/bin/python - <<'PY'
import sqlite3

db = "/opt/ai-defense-manager/data/ai-defense.db"
conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)

for table in (
    "analysis_runs",
    "analysis_evidence",
    "action_proposals",
    "action_approvals",
    "audit_logs",
):
    print(f"\n[{table}]")
    for row in conn.execute(f"PRAGMA table_info({table})"):
        print(f"  {row[1]} ({row[2]})")

conn.close()
PY
```

There are no columns that store Wazuh's `full_log`, arbitrary `data`, user names, commands or passwords. The contents that need checking are `summary` and `reasoning`, produced by the AI, and `event_summary`, which comes from Wazuh.

## 1.2 Saving, Retrieval, Data Model and Analysis Code

```bash
sed -n '1,300p' /opt/ai-defense-manager/app/services/analysis_history.py
```

All SQL uses placeholders, so SQL injection is handled.

```bash
sed -n '1,320p' /opt/ai-defense-manager/app/services/wazuh_relay.py
```

`full_log`, arbitrary `data`, commands and passwords are not referenced. However, `rule.description` (the source of the summary) and `decoder.name` / `location` (the source of the category) are strings from outside, so unexpected information could still get mixed in.

```bash
cat /opt/ai-defense-manager/app/schemas/security_event.py
```

```bash
sed -n '1,360p' /opt/ai-defense-manager/app/services/ai_analysis.py
```

The AI analysis service has the following good points.

- It instructs the model to treat event descriptions and context as "untrusted data"
- It defines the output shape with a JSON Schema
- It validates that the evidence event IDs are in the input
- It prohibits blocking internal IPs, and block proposals require multiple pieces of evidence, a global IP, a TTL of at most 900 seconds and human approval

On the other hand, `request.model_dump(mode="json")` is passed to the LLM as is, so `agent_name`, `agent_id`, `rule_description`, IP addresses and so on, which are not needed for analysis, are also being sent.

```bash
cat /opt/ai-defense-manager/app/schemas/analysis.py
```

| Field | Currently sent to the LLM | Saved in SQLite |
|---|---|---|
| `event_id` | Yes | Yes |
| `source` | Yes | Yes |
| `observed_at` | Yes | Yes |
| `severity` | Yes | Yes |
| `rule_id` | Yes | Yes |
| `rule_description` | Yes | No |
| `source_ip`, `destination_ip` | Yes | No |
| `agent_id`, `agent_name` | Yes | No |
| `event_category` | Yes | No |
| `event_summary` | Yes | Yes |

# Chapter 2: Sending Only Six Fields to the LLM

## 2.1 Backup

```bash
cp -a /opt/ai-defense-manager/app/services/ai_analysis.py /root/ai-analysis-backup-20261121.py && sha256sum /opt/ai-defense-manager/app/services/ai_analysis.py /root/ai-analysis-backup-20261121.py
```

If the two SHA-256 values match, the backup was taken correctly.

## 2.2 Deciding the Fields to Send

Send the LLM only the following six fields and the analysis language. `agent_name`, `agent_id`, IP addresses, `rule_description` and the optional `analysis_context` are not sent.

- `event_id`
- `observed_at`
- `severity`
- `rule_id`
- `event_category`
- `event_summary`

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
from pathlib import Path

path = Path("app/services/ai_analysis.py")
source = path.read_text(encoding="utf-8")

old = '''                "content": json.dumps(
                    request.model_dump(mode="json"),
                    ensure_ascii=False,
                ),'''

new = '''                "content": json.dumps(
                    {
                        "requested_language": request.requested_language,
                        "events": [
                            {
                                "event_id": str(event.event_id),
                                "observed_at": event.observed_at.isoformat(),
                                "severity": event.severity,
                                "rule_id": event.rule_id,
                                "event_category": event.event_category,
                                "event_summary": event.event_summary,
                            }
                            for event in request.events
                        ],
                    },
                    ensure_ascii=False,
                ),'''

if source.count(old) != 1:
    raise SystemExit("PATCH_ABORTED: expected source block not found exactly once")

path.write_text(source.replace(old, new), encoding="utf-8")
print("LLM_INPUT_ALLOWLIST_PATCH: OK")
PY
```

```bash
cd /opt/ai-defense-manager && ./venv/bin/python -m py_compile app/services/ai_analysis.py && echo "PY_COMPILE_OK"
```

## 2.3 Checking in the Code

Parse the source code and confirm that only six fields are sent and that the names of the excluded fields do not appear.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
import ast
import json
from pathlib import Path

source = Path("app/services/ai_analysis.py").read_text(encoding="utf-8")
tree = ast.parse(source)

expected = {
    "event_id",
    "observed_at",
    "severity",
    "rule_id",
    "event_category",
    "event_summary",
}

found = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Dict):
        for key in node.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                if key.value in expected:
                    found.add(key.value)

assert found == expected, f"Unexpected allowlist: {found}"
assert "request.model_dump(mode=\"json\")" not in source
assert '"analysis_context"' not in source
assert '"agent_name"' not in source
assert '"agent_id"' not in source
assert '"source_ip"' not in source
assert '"destination_ip"' not in source
assert '"rule_description"' not in source

print("LLM_EVENT_FIELDS:", ", ".join(sorted(found)))
print("EXCLUDED_FIELDS_CHECK: OK")
print("LLM_PAYLOAD_ALLOWLIST_TEST: OK")
PY
```

## 2.4 Checking by Running It (Mock)

There are no existing tests.

```bash
cd /opt/ai-defense-manager && find . -maxdepth 3 -type f \( -name 'test_*.py' -o -name '*_test.py' \) -not -path './venv/*' -print | sort
```

```bash
cd /opt/ai-defense-manager && sed -n '1,260p' app/schemas/analysis_proposal.py && sed -n '1,220p' app/schemas/security_event.py
```

Temporarily replace the HTTP client with a fake (mock), capture the content actually sent, and examine it. The test events deliberately contain fields that should be excluded (`PRIVATE_...` and IP addresses), and we confirm they are not in what is sent. No communication with Ollama, no DB writes and no service restart occur.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

import httpx

from app.schemas.analysis import AIAnalysisRequest
from app.schemas.security_event import SecurityEvent
from app.services import ai_analysis


event_id = uuid4()

request = AIAnalysisRequest(
    events=[
        SecurityEvent(
            event_id=event_id,
            source="wazuh",
            observed_at=datetime.now(timezone.utc),
            severity="high",
            rule_id="5710",
            rule_description="PRIVATE_RULE_DESCRIPTION",
            source_ip="203.0.113.10",
            destination_ip="198.51.100.20",
            agent_id="PRIVATE_AGENT_ID",
            agent_name="PRIVATE_AGENT_NAME",
            event_category="authentication",
            event_summary="Repeated authentication failures",
        )
    ],
    analysis_context="PRIVATE_ANALYSIS_CONTEXT",
    requested_language="ja",
)

captured = {}


class MockResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {
            "message": {
                "content": json.dumps({
                    "summary": "認証失敗イベントを検出",
                    "severity": "high",
                    "confidence": 0.9,
                    "evidence_event_ids": [str(event_id)],
                    "recommended_action": "human_review",
                    "target_ip": None,
                    "ttl_seconds": None,
                    "requires_human_approval": True,
                    "reasoning": "確認が必要です",
                })
            }
        }


class MockAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def post(self, url, json):
        captured["url"] = url
        captured["payload"] = json
        return MockResponse()


async def main():
    original_client = ai_analysis.httpx.AsyncClient
    ai_analysis.httpx.AsyncClient = MockAsyncClient
    try:
        proposal = await ai_analysis.analyze_events(request)
    finally:
        ai_analysis.httpx.AsyncClient = original_client

    payload = captured["payload"]
    user_content = next(
        message["content"]
        for message in payload["messages"]
        if message["role"] == "user"
    )
    sent = json.loads(user_content)

    expected_fields = {
        "event_id",
        "observed_at",
        "severity",
        "rule_id",
        "event_category",
        "event_summary",
    }

    assert set(sent) == {"requested_language", "events"}
    assert set(sent["events"][0]) == expected_fields
    assert sent["events"][0]["event_id"] == str(event_id)
    assert sent["requested_language"] == "ja"

    serialized = json.dumps(sent, ensure_ascii=False)
    for secret in (
        "PRIVATE_RULE_DESCRIPTION",
        "PRIVATE_AGENT_ID",
        "PRIVATE_AGENT_NAME",
        "PRIVATE_ANALYSIS_CONTEXT",
        "203.0.113.10",
        "198.51.100.20",
    ):
        assert secret not in serialized, f"Excluded value leaked: {secret}"

    assert proposal.evidence_event_ids == [event_id]

    print("MOCK_HTTP_CALL: OK")
    print("SENT_EVENT_FIELDS:", ", ".join(sorted(sent["events"][0])))
    print("SENSITIVE_FIELD_EXCLUSION: OK")
    print("PROPOSAL_VALIDATION: OK")
    print("LLM_PAYLOAD_RUNTIME_TEST: OK")


asyncio.run(main())
PY
```

## 2.5 Checking the Diff and Applying

```bash
diff -u /root/ai-analysis-backup-20261121.py /opt/ai-defense-manager/app/services/ai_analysis.py
```

Only the part that builds what is sent to the LLM has changed. Restart the service to apply it (the API stops briefly).

```bash
systemctl restart ai-defense-manager.service && systemctl is-active ai-defense-manager.service
```

```bash
curl -sS -i http://127.0.0.1:8000/health
```

Fetch actual Wazuh events and analyze them with the new way of sending. The analysis result is recorded in SQLite, but no firewall changes or IP blocks are made.

```bash
curl -sS -i -X POST http://127.0.0.1:8000/api/v1/wazuh/analyze -H 'Content-Type: application/json' -d '{}'
```

At build time it returned `HTTP 200`, analyzed seven Proxmox VE authentication-success events, and returned `severity: info`, `confidence: 0.9` and `recommended_action: no_action`.

```bash
cd /opt/ai-defense-manager && runuser -u ai-defense -- ./venv/bin/python - <<'PY'
import sqlite3

path = "/opt/ai-defense-manager/data/ai-defense.db"
db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)

for table in (
    "analysis_runs",
    "analysis_evidence",
    "action_proposals",
    "action_approvals",
    "audit_logs",
):
    count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count}")

latest = db.execute("""
    SELECT severity, recommended_action, evidence_count, status
    FROM analysis_runs
    ORDER BY created_at DESC
    LIMIT 1
""").fetchone()

print("LATEST_ANALYSIS:", latest)
db.close()
PY
```

At build time `analysis_runs` had three rows, and the latest record was `('info', 'no_action', 7, 'completed')`.

# Chapter 3: Protecting the Contents of Categories and Summaries

## 3.1 Where Information Can Get Mixed In

```bash
sed -n '1,320p' /opt/ai-defense-manager/app/services/wazuh_relay.py
```

- `description` → `event_summary`: up to 512 characters, sent to the LLM as is
- `decoder` or `location` → `event_category`: up to 64 characters, sent to the LLM as is. `location` is where the log came from, so it can contain file paths or host information

The policy is as follows.

1. Replace `event_category` with defined fixed categories
2. In `event_summary`, find and mask API keys, tokens, passwords, email addresses, IP addresses and so on
3. Keep to the length limit even after masking
4. Do not change the original Wazuh events or the SQLite saving code

## 3.2 Available Libraries

```bash
cd /opt/ai-defense-manager && ls -la
```

```bash
cd /opt/ai-defense-manager && find tests -maxdepth 3 -type f -printf '%p\n' | sort && echo '--- REQUIREMENTS LOCK ---' && cat requirements.lock
```

Dependencies are managed with `requirements.lock`. There is no dedicated library for finding secrets, so build it with Python's standard `re` and `ipaddress`.

Deleting IP addresses and email addresses would also lose information needed to identify an attacker, so instead of deleting them, replace them with the following masks.

| Information | Replacement |
|---|---|
| API keys, Bearer tokens, passwords | `[REDACTED_SECRET]` |
| Email addresses | `[REDACTED_EMAIL]` |
| IP addresses (both internal and external) | `[REDACTED_IP]` |
| Non-string input and the like | `[REDACTED_EVENT]` |

## 3.3 Examining the Actual Categories

Count the categories of 50 events over the last 24 hours.

```bash
cd /opt/ai-defense-manager && runuser -u ai-defense -- ./venv/bin/python - <<'PY'
import asyncio
from collections import Counter
from app.services.wazuh_relay import fetch_wazuh_events

async def main():
    events = await fetch_wazuh_events(limit=50, since_minutes=1440)
    categories = Counter(event.event_category for event in events)
    print("EVENT_COUNT:", len(events))
    print("CATEGORY_COUNTS:")
    for category, count in sorted(categories.items()):
        print(f"{category!r}: {count}")

asyncio.run(main())
PY
```

At build time there were five kinds. Replace them as follows.

| Current category | Count | Value sent to the LLM |
|---|---:|---|
| `pvedaemon` | 34 | `virtualization_management` |
| `pam` | 11 | `authentication` |
| `sshd` | 2 | `remote_access` |
| `useradd` | 2 | `account_management` |
| `open-userdel` | 1 | `account_management` |
| Anything else | — | `other` |

## 3.4 Backup

```bash
cd /opt/ai-defense-manager && cp -a app/services/wazuh_relay.py /root/wazuh-relay-backup-20261121.py && cp -a app/services/ai_analysis.py /root/ai-analysis-backup-privacy-20261121.py && sha256sum app/services/wazuh_relay.py /root/wazuh-relay-backup-20261121.py app/services/ai_analysis.py /root/ai-analysis-backup-privacy-20261121.py
```

Confirm that the four SHA-256 values match in pairs.

```bash
cd /opt/ai-defense-manager && sed -n '1,240p' app/services/wazuh_relay.py
```

```bash
cd /opt/ai-defense-manager && sed -n '1,280p' app/services/ai_analysis.py
```

## 3.5 Fixing the Categories

Because the replacement is done in `wazuh_relay.py`, the categories of events saved from now on also become fixed values, not just those sent to the LLM.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
from pathlib import Path

path = Path("app/services/wazuh_relay.py")
text = path.read_text(encoding="utf-8")

old = '''    category = (decoder or location or "wazuh")[:64]
    summary = (description or "Wazuh security alert")[:512]
'''

new = '''    raw_category = (decoder or location or "").strip().lower()
    category_map = {
        "pvedaemon": "virtualization_management",
        "pam": "authentication",
        "sshd": "remote_access",
        "useradd": "account_management",
        "open-userdel": "account_management",
    }
    category = category_map.get(raw_category, "other")
    summary = (description or "Wazuh security alert")[:512]
'''

if old not in text:
    raise SystemExit("PATCH_ABORTED: expected source block not found")

path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("WAZUH_CATEGORY_ALLOWLIST_PATCH: OK")
PY
```

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
from datetime import datetime, timezone
from app.services.wazuh_relay import _convert_alert

cases = {
    "pvedaemon": "virtualization_management",
    "pam": "authentication",
    "sshd": "remote_access",
    "useradd": "account_management",
    "open-userdel": "account_management",
    "unknown-sensitive-hostname": "other",
}

for decoder, expected in cases.items():
    alert = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rule.level": 5,
        "rule.id": "100001",
        "rule.description": "Test security event",
        "decoder.name": decoder,
    }
    event = _convert_alert(alert)
    assert event.event_category == expected, (
        decoder, event.event_category, expected
    )
    print(f"{decoder}: {event.event_category} OK")

print("PYTHON_COMPILE_AND_CATEGORY_TEST: OK")
PY
```

Unknown decoder names also become `other`, so arbitrary strings such as host names no longer enter the category.

## 3.6 Masking the Summary

Add `_sanitize_event_summary()` to `ai_analysis.py` and apply it to `event_summary` just before sending to the LLM. It finds information of known shapes; it cannot find secrets or user names of unknown shapes. Note that this is not complete anonymization.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
from pathlib import Path

path = Path("app/services/ai_analysis.py")
text = path.read_text(encoding="utf-8")

if "def _sanitize_event_summary(" in text:
    raise SystemExit("PATCH_ABORTED: sanitizer already exists")

marker = "\n\nclass AIAnalysisError(Exception):\n    pass\n"

helper = r'''

def _sanitize_event_summary(value: str) -> str:
    """Redact common secrets and personal identifiers before LLM submission."""
    import ipaddress
    import re

    if not isinstance(value, str):
        return "[REDACTED_EVENT]"

    # Remove control characters that can interfere with prompt boundaries.
    value = "".join(
        char if char.isprintable() or char in "\t " else " "
        for char in value
    )

    # Authorization credentials.
    value = re.sub(
        r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+",
        "Bearer [REDACTED_SECRET]",
        value,
    )

    # Common secret assignments.
    value = re.sub(
        r"""(?i)\b(?:password|passwd|pwd|secret|api[_-]?key|access[_-]?token|refresh[_-]?token)\b\s*[:=]\s*["']?[^\s,;"'<>]+""",
        "[REDACTED_SECRET]",
        value,
    )

    # Recognizable provider key formats.
    value = re.sub(r"\bAKIA[0-9A-Z]{16}\b", "[REDACTED_SECRET]", value)
    value = re.sub(
        r"\bgh[pousr]_[A-Za-z0-9]{20,}\b",
        "[REDACTED_SECRET]",
        value,
    )
    value = re.sub(r"\bsk-[A-Za-z0-9_-]{20,}\b", "[REDACTED_SECRET]", value)

    # Email addresses.
    value = re.sub(
        r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "[REDACTED_EMAIL]",
        value,
    )

    # Replace valid IPv4/IPv6 literals, leaving surrounding punctuation intact.
    candidates = re.compile(
        r"(?<![A-Za-z0-9_])(?:"
        r"(?:\d{1,3}\.){3}\d{1,3}"
        r"|"
        r"[0-9A-Fa-f:]{2,}"
        r")(?![A-Za-z0-9_])"
    )

    def redact_ip(match):
        candidate = match.group(0)
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            return candidate
        return "[REDACTED_IP]"

    value = candidates.sub(redact_ip, value)

    return value[:512] if value.strip() else "[REDACTED_EVENT]"
'''

if marker not in text:
    raise SystemExit("PATCH_ABORTED: insertion point not found")

text = text.replace(marker, helper + marker, 1)

old = '"event_summary": event.event_summary,'
new = '"event_summary": _sanitize_event_summary(event.event_summary),'

if old not in text:
    raise SystemExit("PATCH_ABORTED: event_summary payload field not found")

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("LLM_SUMMARY_SANITIZER_PATCH: OK")
PY
```

Pasting can break the terminal display, so check the contents of the file.

```bash
cd /opt/ai-defense-manager && sed -n '1,180p' app/services/ai_analysis.py
```

## 3.7 Tests for Masking

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
from app.services.ai_analysis import _sanitize_event_summary

cases = [
    ("Bearer abc.def-123", "Bearer [REDACTED_SECRET]"),
    ("password=hunter2", "[REDACTED_SECRET]"),
    ('password="my secret phrase"', "[REDACTED_SECRET]"),
    ("api_key: sk-abcdefghijklmnopqrstuvwxyz123456", "[REDACTED_SECRET]"),
    ("AWS AKIA1234567890ABCDEF", "[REDACTED_SECRET]"),
    ("GitHub ghp_abcdefghijklmnopqrstuvwxyz123456", "[REDACTED_SECRET]"),
    ("user admin@example.com login", "[REDACTED_EMAIL]"),
    ("connection from 203.0.113.10", "[REDACTED_IP]"),
    ("connection from 2001:db8::1", "[REDACTED_IP]"),
]

for source, expected in cases:
    result = _sanitize_event_summary(source)
    assert expected in result, (source, result, expected)
    print("REDACTION_TEST: OK")

normal = "SSH authentication failed for invalid user"
assert _sanitize_event_summary(normal) == normal
print("NORMAL_EVENT_PRESERVATION: OK")

assert _sanitize_event_summary(None) == "[REDACTED_EVENT]"
print("INVALID_INPUT_FAILSAFE: OK")

print("SANITIZER_TESTS: ALL PASSED")
PY
```

```bash
cd /opt/ai-defense-manager && ./venv/bin/python -m py_compile app/services/wazuh_relay.py app/services/ai_analysis.py && echo "PYTHON_COMPILE: OK"
```

## 3.8 Tests of the Content Sent (Mock)

```bash
cd /opt/ai-defense-manager && sed -n '1,240p' app/schemas/analysis.py && sed -n '1,240p' app/schemas/security_event.py && sed -n '1,260p' app/schemas/analysis_proposal.py
```

Go through the actual `analyze_events()` and confirm that no secrets remain in the JSON passed to Ollama. There is no communication with Ollama and no writing to SQLite.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import patch

from app.schemas.analysis import AIAnalysisRequest
from app.schemas.security_event import SecurityEvent
from app.services.ai_analysis import analyze_events


event_id = uuid4()

event = SecurityEvent(
    event_id=event_id,
    source="wazuh",
    observed_at=datetime.now(timezone.utc),
    severity="high",
    rule_id="5710",
    rule_description="PRIVATE_RULE_DESCRIPTION",
    source_ip="203.0.113.10",
    destination_ip="198.51.100.20",
    agent_id="PRIVATE_AGENT_ID",
    agent_name="PRIVATE_AGENT_NAME",
    event_category="remote_access",
    event_summary=(
        "SSH login failed password=hunter2 "
        "user@example.com from 203.0.113.10"
    ),
)

request = AIAnalysisRequest(
    events=[event],
    analysis_context="PRIVATE_ANALYSIS_CONTEXT",
    requested_language="ja",
)

captured = {}

class FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {
            "message": {
                "content": json.dumps({
                    "summary": "SSH authentication failure",
                    "severity": "high",
                    "confidence": 0.9,
                    "evidence_event_ids": [str(event_id)],
                    "recommended_action": "monitor",
                    "target_ip": None,
                    "ttl_seconds": None,
                    "requires_human_approval": True,
                    "reasoning": "Authentication failure detected",
                })
            }
        }


class FakeClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def post(self, url, json):
        captured["url"] = url
        captured["payload"] = json
        return FakeResponse()


async def main():
    with patch("app.services.ai_analysis.httpx.AsyncClient", FakeClient):
        proposal = await analyze_events(request)

    assert proposal.recommended_action.value == "monitor"

    user_content = captured["payload"]["messages"][1]["content"]
    sent = json.loads(user_content)
    sent_event = sent["events"][0]

    expected_fields = {
        "event_id",
        "observed_at",
        "severity",
        "rule_id",
        "event_category",
        "event_summary",
    }
    assert set(sent_event) == expected_fields

    summary = sent_event["event_summary"]
    assert "[REDACTED_SECRET]" in summary
    assert "[REDACTED_EMAIL]" in summary
    assert "[REDACTED_IP]" in summary

    serialized = json.dumps(sent, ensure_ascii=False)
    forbidden = [
        "PRIVATE_RULE_DESCRIPTION",
        "PRIVATE_AGENT_ID",
        "PRIVATE_AGENT_NAME",
        "PRIVATE_ANALYSIS_CONTEXT",
        "203.0.113.10",
        "198.51.100.20",
        "hunter2",
        "user@example.com",
    ]
    for value in forbidden:
        assert value not in serialized, f"Sensitive value leaked: {value}"

    print("MOCK_HTTP_CALL: OK")
    print("LLM_EVENT_FIELDS: ", ", ".join(sorted(sent_event)))
    print("SECRET_REDACTION: OK")
    print("PRIVATE_FIELD_EXCLUSION: OK")
    print("PROPOSAL_VALIDATION: OK")
    print("LLM_PAYLOAD_RUNTIME_TEST: OK")


asyncio.run(main())
PY
```

## 3.9 Masking Quoted Values to the End

With the regular expression from 3.6, a quoted value such as `password="my secret phrase"` is masked only up to the first space. Rewrite just that one line so that when the value is `"..."` or `'...'`, the whole contents of the quotes are masked.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
from pathlib import Path

path = Path("app/services/ai_analysis.py")
lines = path.read_text(encoding="utf-8").splitlines()

matches = [
    i for i, line in enumerate(lines)
    if "refresh[_-]?token" in line and line.strip().startswith('r"""')
]

if len(matches) != 1:
    raise SystemExit(f"PATCH_ABORTED: expected one regex line, found {len(matches)}")

lines[matches[0]] = (
    r'''        r"""(?i)\b(?:password|passwd|pwd|secret|api[_-]?key|access[_-]?token|refresh[_-]?token)\b\s*[:=]\s*(?:"[^"]*"|'[^']*'|[^\s,;<>]+)""",'''
)

path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("QUOTED_SECRET_REDACTION_PATCH: OK")
PY
```

Confirm that the result becomes `[REDACTED_SECRET]` as a whole.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
from app.services.ai_analysis import _sanitize_event_summary

cases = {
    'password="my secret phrase"': "[REDACTED_SECRET]",
    "password='another secret phrase'": "[REDACTED_SECRET]",
    "api_key=abc123": "[REDACTED_SECRET]",
    "password=hunter2": "[REDACTED_SECRET]",
}

for source, expected in cases.items():
    result = _sanitize_event_summary(source)
    assert result == expected, (
        f"FAIL source={source!r}, result={result!r}, expected={expected!r}"
    )
    print("EXACT_REDACTION: OK")

print("QUOTED_SECRET_TEST: ALL PASSED")
PY
```

## 3.10 Checking the Diff and Applying

```bash
cd /opt/ai-defense-manager && diff -u /root/wazuh-relay-backup-20261121.py app/services/wazuh_relay.py; diff -u /root/ai-analysis-backup-privacy-20261121.py app/services/ai_analysis.py
```

Confirm that in `wazuh_relay.py` only the category replacement has changed, and in `ai_analysis.py` only the addition of the masking function and the processing of `event_summary`. Masking is used only when sending to the LLM; the `event_summary` saved in SQLite is as before (handled in the next part).

```bash
cd /opt/ai-defense-manager && ./venv/bin/python -m py_compile app/services/wazuh_relay.py app/services/ai_analysis.py && echo "FINAL_COMPILE: OK"
```

```bash
systemctl restart ai-defense-manager.service && systemctl is-active ai-defense-manager.service
```

```bash
curl -sS -i http://127.0.0.1:8000/health
```

```bash
curl -sS http://127.0.0.1:8000/api/v1/wazuh/events?limit=5\&since_minutes=60
```

At build time, the `event_category` of all five events had become `virtualization_management`. This API fetches and returns events and includes `agent_id` and `agent_name`, but these are not sent to the LLM.

# Closing Notes

In Part 19 we narrowed the information passed to the LLM as follows.

| Measure | Details |
|---|---|
| Fields sent | Only six fields and the analysis language |
| Categories | Fixed values (unknown ones become `other`) |
| Summaries | Secrets, email addresses and IP addresses are masked before sending |

In the next part, we fix a problem that makes AI analysis fail, and also apply masking to the summaries saved in SQLite.

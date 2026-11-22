---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 20: Fixing Confidence Scores and Protecting Stored Data"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 20 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". After Part 19, we found that analysis with real Wazuh events failed (`502`). Here we do the following.

1. Investigate and fix the cause of the analysis failure (the AI returns confidence on a 0–100 scale)
2. Move the masking from Part 19 into a common module and also use it when saving to SQLite
3. Check the saved history, the DB files, the service settings and the listening ports

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **ai-defense-manager VM 230 (root)**.

# Chapter 1: Why the Analysis Fails

## 1.1 Symptoms

At the end of Part 19 we confirmed that the categories had been replaced. Next, run the AI analysis.

```bash
curl -fsS http://127.0.0.1:8000/openapi.json | python3 -c 'import json,sys; d=json.load(sys.stdin); p=d["paths"]["/api/v1/wazuh/analyze"]["post"]; print(json.dumps({"summary":p.get("summary"),"requestBody":p.get("requestBody"),"responses":p.get("responses")},ensure_ascii=False,indent=2))'
```

```bash
curl -fsS http://127.0.0.1:8000/openapi.json | python3 -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps(d["components"]["schemas"]["WazuhAnalysisRequest"],ensure_ascii=False,indent=2))'
```

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/wazuh/analyze \
  -H 'Content-Type: application/json' \
  -d '{"limit":5,"since_minutes":60,"requested_language":"ja"}'
```

At build time it returned `{"detail":"AI analysis failed or returned an invalid response"}` (`502`).

## 1.2 Log and Connection Target

```bash
journalctl -u ai-defense-manager.service --since "5 minutes ago" --no-pager -n 100
```

The log records `200` for `/health` and for fetching events, and `502` for analysis, but the details of the Python exception are not shown (because the application is designed not to expose details externally).

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
from app.core.config import settings

for name in ("ollama_base_url", "ollama_url", "ollama_host", "ollama_model"):
    if hasattr(settings, name):
        print(f"{name}: {getattr(settings, name)}")
PY
```

The connection target was `http://192.168.0.180:11434/`. Check whether VM 230 can reach Ollama.

```bash
curl -sS --connect-timeout 5 --max-time 10 http://192.168.0.180:11434/api/tags
```

The list of models was returned, showing that `qwen3:8b` is present. It is not a network problem.

## 1.3 Model and Schema

```bash
cd /opt/ai-defense-manager && grep -nE 'model|format|json_schema|response_format|ollama' app/services/ai_analysis.py
```

```bash
cd /opt/ai-defense-manager && sed -n '1,165p' app/services/ai_analysis.py
```

The model name is `qwen3:8b`, which matches what is on Ollama. The API is Ollama's `/api/chat`, the output shape is specified with `AIAnalysisProposal.model_json_schema()`, and the reply is validated with Pydantic's `model_validate()`.

```bash
cd /opt/ai-defense-manager && sed -n '1,240p' app/schemas/analysis_proposal.py
```

| Field | Constraint |
|---|---|
| `summary` | 1–2000 characters |
| `severity` | `info`, `low`, `medium`, `high`, `critical` |
| `confidence` | 0.0–1.0 |
| `evidence_event_ids` | 1–100 (required) |
| `reasoning` | 1–4000 characters |

## 1.4 Asking Ollama Directly

Without writing to the application's DB, ask Ollama directly with the same schema.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
import httpx, json
from app.schemas.analysis_proposal import AIAnalysisProposal

payload = {
    "model": "qwen3:8b",
    "stream": False,
    "think": False,
    "format": AIAnalysisProposal.model_json_schema(),
    "messages": [{"role": "user", "content": "Return a valid JSON proposal. Use event ID 11111111-1111-4111-8111-111111111111. Choose no_action and provide all required fields."}]
}

try:
    r = httpx.post("http://192.168.0.180:11434/api/chat", json=payload, timeout=180)
    print("HTTP_STATUS:", r.status_code)
    print("RESPONSE:", r.text[:4000])
except Exception as e:
    print("ERROR:", type(e).__name__, str(e))
PY
```

At build time it returned `HTTP_STATUS: 200` and JSON, but the JSON contained `"confidence": 100`. The schema allows 0.0–1.0, so `100` fails validation. This is the cause of the `502`.

# Chapter 2: Adding an Instruction About Confidence

## 2.1 Fixing SYSTEM_PROMPT

Without changing the Pydantic constraint (0.0–1.0), add three lines to the AI's instructions (`SYSTEM_PROMPT`) saying that confidence must be answered as a decimal. Also take a backup.

```bash
cd /opt/ai-defense-manager && cp -a app/services/ai_analysis.py /root/ai-analysis-backup-confidence-20261121.py && ./venv/bin/python - <<'PY'
from pathlib import Path

path = Path("app/services/ai_analysis.py")
source = path.read_text()

old = """Return exactly one JSON object matching the supplied JSON Schema.

Never recommend blocking private, local, or internal IP addresses."""

new = """Return exactly one JSON object matching the supplied JSON Schema.

The confidence field must be a decimal number between 0.0 and 1.0.
Never express confidence as a percentage from 0 to 100.
For example, use 0.85 instead of 85.

Never recommend blocking private, local, or internal IP addresses."""

if source.count(old) != 1:
    raise SystemExit("ERROR: Expected prompt section not found exactly once. No changes made.")

path.write_text(source.replace(old, new))
print("SYSTEM_PROMPT_UPDATE: OK")
PY
diff -u /root/ai-analysis-backup-confidence-20261121.py app/services/ai_analysis.py
```

The only difference is the three added lines of instructions.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python -m py_compile app/services/ai_analysis.py && echo "CONFIDENCE_PROMPT_COMPILE: OK"
```

## 2.2 Checking with the Fixed Instructions

Ask Ollama using the fixed `SYSTEM_PROMPT` and validate the reply against the actual schema. Nothing is saved to SQLite and the service is not restarted.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
import httpx, json
from app.services.ai_analysis import SYSTEM_PROMPT
from app.schemas.analysis_proposal import AIAnalysisProposal

payload = {
    "model": "qwen3:8b",
    "stream": False,
    "think": False,
    "format": AIAnalysisProposal.model_json_schema(),
    "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Return a valid harmless test proposal. Use event ID 11111111-1111-4111-8111-111111111111. Choose no_action and provide all required fields."}
    ]
}

try:
    r = httpx.post("http://192.168.0.180:11434/api/chat", json=payload, timeout=180)
    print("HTTP_STATUS:", r.status_code)
    r.raise_for_status()
    content = r.json()["message"]["content"]
    print("MODEL_RESPONSE:", content)
    proposal = AIAnalysisProposal.model_validate_json(content)
    print("SCHEMA_VALIDATION: OK")
    print("CONFIDENCE:", proposal.confidence)
except Exception as e:
    print("ERROR:", type(e).__name__, str(e))
PY
```

At build time it returned `"confidence": 0.95` and `SCHEMA_VALIDATION: OK`.

## 2.3 Applying

```bash
systemctl restart ai-defense-manager.service && systemctl is-active ai-defense-manager.service
```

```bash
curl -sS -i http://127.0.0.1:8000/health
```

Analyze five real Wazuh events. The result is saved in SQLite.

```bash
curl -sS -i -X POST http://127.0.0.1:8000/api/v1/wazuh/analyze \
  -H 'Content-Type: application/json' \
  -d '{"limit":5,"since_minutes":60,"requested_language":"ja"}'
```

The results at build time were as follows. Successful authentication alone does not establish unauthorized access, so it was a cautious judgment that recommended "monitoring" rather than immediate blocking.

| Item | Result |
|---|---|
| HTTP | `200 OK` |
| `severity` | `info` |
| `confidence` | `0.85` |
| `recommended_action` | `monitor` |
| `target_ip`, `ttl_seconds` | `null` |
| `requires_human_approval` | `true` |

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
import sqlite3

db = sqlite3.connect(
    "file:/opt/ai-defense-manager/data/ai-defense.db?mode=ro",
    uri=True
)

for table in (
    "analysis_runs",
    "analysis_evidence",
    "action_proposals",
    "action_approvals",
    "audit_logs",
):
    count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count}")

db.close()
print("DATABASE_READ_ONLY_CHECK: OK")
PY
```

At build time `analysis_runs` had 4 rows and `analysis_evidence` 28.

# Chapter 3: Masking the Saved Summaries Too

## 3.1 The Current Design

```bash
cd /opt/ai-defense-manager && grep -R -n -C 5 "event_summary" app/services app/api
```

```bash
cd /opt/ai-defense-manager && sed -n '1,65p' app/services/analysis_history.py && sed -n '150,195p' app/services/analysis_history.py && sed -n '1,100p' app/services/ai_analysis.py
```

When sending to the LLM, masking is done with `_sanitize_event_summary()`, but when saving to SQLite, `event.event_summary` is written as is.

```bash
cd /opt/ai-defense-manager && grep -R -n "analysis_history\|ai_analysis" app --include="*.py"
```

```bash
cd /opt/ai-defense-manager && grep -n "_sanitize_event_summary" app/services/ai_analysis.py
```

`analysis_history.py` and `ai_analysis.py` do not import each other. Rather than having one import the other, move the masking function into a new `app/services/event_sanitizer.py` and use it from both places. Existing SQLite data is not changed; only data saved from now on is protected.

## 3.2 Backup

```bash
cd /opt/ai-defense-manager && mkdir -p /root/ai-defense-backup-privacy-sqlite-20261121 && cp -a app/services/ai_analysis.py app/services/analysis_history.py /root/ai-defense-backup-privacy-sqlite-20261121/ && sha256sum app/services/ai_analysis.py app/services/analysis_history.py
```

```bash
cd /opt/ai-defense-manager && sed -n '30,100p' app/services/ai_analysis.py
```

## 3.3 Moving It to a Common Module

Without changing the body of the function (the masking rules), move it under the name `sanitize_event_summary()`.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
from pathlib import Path

base = Path("/opt/ai-defense-manager/app/services")
ai_path = base / "ai_analysis.py"
history_path = base / "analysis_history.py"
sanitizer_path = base / "event_sanitizer.py"

ai = ai_path.read_text()
history = history_path.read_text()

start = ai.index("def _sanitize_event_summary(value: str) -> str:")
end = ai.index("\n\nclass AIAnalysisError", start)

function = ai[start:end]
function = function.replace(
    "def _sanitize_event_summary(value: str) -> str:",
    "def sanitize_event_summary(value: str) -> str:",
    1,
)
function = function.replace(
    "before LLM submission.",
    "before storage or LLM submission.",
    1,
)

assert ai.count("_sanitize_event_summary(event.event_summary)") == 1
assert history.count("                    event.event_summary,") == 1
assert not sanitizer_path.exists()

sanitizer_path.write_text(
    '"""Shared sanitization for security event summaries."""\n\n'
    + function
    + "\n"
)

ai = ai[:start] + ai[end + 2:]
ai = ai.replace(
    "from app.schemas.analysis import AIAnalysisRequest",
    "from app.services.event_sanitizer import sanitize_event_summary\n"
    "from app.schemas.analysis import AIAnalysisRequest",
    1,
)
ai = ai.replace(
    "_sanitize_event_summary(event.event_summary)",
    "sanitize_event_summary(event.event_summary)",
    1,
)

history = history.replace(
    "from uuid import uuid4",
    "from uuid import uuid4\n\n"
    "from app.services.event_sanitizer import sanitize_event_summary",
    1,
)
history = history.replace(
    "                    event.event_summary,",
    "                    sanitize_event_summary(event.event_summary),",
    1,
)

ai_path.write_text(ai)
history_path.write_text(history)

print("SANITIZER_MODULE_CREATED: OK")
print("LLM_SANITIZATION_CONNECTED: OK")
print("SQLITE_SANITIZATION_CONNECTED: OK")
PY
```

```bash
cd /opt/ai-defense-manager && ./venv/bin/python -m py_compile app/services/event_sanitizer.py app/services/ai_analysis.py app/services/analysis_history.py && echo "PRIVACY_SANITIZER_COMPILE: OK"
```

## 3.4 Tests for Masking

Check with made-up data, not real data.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
from app.services.event_sanitizer import sanitize_event_summary

tests = {
    "bearer": ("Bearer abc.def_123", "[REDACTED_SECRET]"),
    "password": ("password='my secret value'", "[REDACTED_SECRET]"),
    "api_key": ("api_key=example-secret-123", "[REDACTED_SECRET]"),
    "aws": ("AKIAIOSFODNN7EXAMPLE", "[REDACTED_SECRET]"),
    "github": ("ghp_abcdefghijklmnopqrstuvwxyz123456", "[REDACTED_SECRET]"),
    "openai": ("sk-abcdefghijklmnopqrstuvwxyz123456", "[REDACTED_SECRET]"),
    "email": ("user@example.com", "[REDACTED_EMAIL]"),
    "ipv4": ("source=203.0.113.10", "[REDACTED_IP]"),
    "ipv6": ("source=2001:db8::1", "[REDACTED_IP]"),
}

for name, (source, expected) in tests.items():
    result = sanitize_event_summary(source)
    assert expected in result, (name, result)
    assert source not in result, (name, result)
    print(f"{name}: OK -> {result}")

normal = "Multiple authentication failures detected"
assert sanitize_event_summary(normal) == normal
print("normal_text: OK")

assert sanitize_event_summary(None) == "[REDACTED_EVENT]"
print("invalid_input: OK")

control = sanitize_event_summary("event\x00summary")
assert "\x00" not in control
print("control_characters: OK")

print("SANITIZER_TESTS: ALL PASSED")
PY
```

## 3.5 Checking the Diff

`/opt/ai-defense-manager` is not managed with Git, so compare with the backups from 3.2.

```bash
cd /opt/ai-defense-manager && diff -u /root/ai-defense-backup-privacy-sqlite-20261121/ai_analysis.py app/services/ai_analysis.py; diff -u /root/ai-defense-backup-privacy-sqlite-20261121/analysis_history.py app/services/analysis_history.py; echo "----- SHARED SANITIZER -----"; sed -n '1,120p' app/services/event_sanitizer.py
```

- `ai_analysis.py`: uses the common function
- `analysis_history.py`: masks just before the INSERT into SQLite
- `event_sanitizer.py`: the masking rules are unchanged

## 3.6 Checking Saving with a Temporary DB

```bash
cd /opt/ai-defense-manager && grep -n -A 100 "^def save_analysis" app/services/analysis_history.py
```

```bash
cd /opt/ai-defense-manager && sed -n '65,120p' app/services/analysis_history.py && sed -n '209,290p' app/services/analysis_history.py
```

`save_analysis()` commits automatically when it finishes normally. Rather than trying it on the production DB and undoing it, use a temporary DB.

```bash
cd /opt/ai-defense-manager && sed -n '1,240p' app/schemas/analysis.py && sed -n '1,220p' app/schemas/analysis_proposal.py
```

```bash
cd /opt/ai-defense-manager && sed -n '1,220p' app/schemas/security_event.py
```

Save an event containing an email address, a password, an API key and an IPv4 address, read it back, and confirm that the original values do not remain.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
import sqlite3
import tempfile
from pathlib import Path
from uuid import uuid4

from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal
from app.schemas.security_event import SecurityEvent
import app.services.analysis_history as history

original_db_path = history.DB_PATH

try:
    with tempfile.TemporaryDirectory(prefix="ai-defense-privacy-test-") as tmp:
        history.DB_PATH = Path(tmp) / "test.db"
        history.initialize_database()

        event_id = uuid4()
        request = AIAnalysisRequest(
            events=[
                SecurityEvent(
                    source="wazuh",
                    severity="low",
                    rule_id="TEST-001",
                    event_category="authentication",
                    event_summary=(
                        "Login from 203.0.113.10 "
                        "email=user@example.com "
                        "password='test secret value' "
                        "api_key=example-secret-123"
                    ),
                )
            ]
        )
        event_id = request.events[0].event_id

        proposal = AIAnalysisProposal(
            summary="Synthetic privacy test",
            severity="low",
            confidence=0.95,
            evidence_event_ids=[event_id],
            recommended_action="no_action",
            target_ip=None,
            ttl_seconds=None,
            requires_human_approval=False,
            reasoning="Test only. No action required.",
        )

        run_id = history.save_analysis(request, proposal)

        with sqlite3.connect(history.DB_PATH) as conn:
            row = conn.execute(
                "SELECT event_summary FROM analysis_evidence WHERE run_id = ?",
                (run_id,),
            ).fetchone()

        assert row is not None
        saved = row[0]

        for secret in (
            "203.0.113.10",
            "user@example.com",
            "test secret value",
            "example-secret-123",
        ):
            assert secret not in saved, f"Unmasked value found: {secret}"

        assert "[REDACTED_IP]" in saved
        assert "[REDACTED_EMAIL]" in saved
        assert saved.count("[REDACTED_SECRET]") == 2

        print("SQLITE_SAVED_SUMMARY:", saved)
        print("SQLITE_SECRET_REDACTION: OK")
        print("SQLITE_TEMP_DB_TEST: PASSED")

finally:
    history.DB_PATH = original_db_path
PY
```

## 3.7 Applying

```bash
systemctl restart ai-defense-manager.service && systemctl is-active ai-defense-manager.service
```

```bash
curl -sS -i http://127.0.0.1:8000/health
```

Analyses saved from now on are masked at save time as well. Records already saved are not changed.

# Chapter 4: Checks

## 4.1 Saved History

Run the saved `analysis_evidence.event_summary` values through the common function and count the rows that would need masking. The DB is opened read-only, and the secrets themselves are not shown.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
import sqlite3
from collections import Counter

from app.services.analysis_history import DB_PATH
from app.services.event_sanitizer import sanitize_event_summary

db_uri = DB_PATH.resolve().as_uri() + "?mode=ro"

with sqlite3.connect(db_uri, uri=True) as conn:
    rows = conn.execute(
        "SELECT event_summary FROM analysis_evidence"
    ).fetchall()

total = len(rows)
needs_masking = 0
patterns = Counter()

for (original,) in rows:
    sanitized = sanitize_event_summary(original)

    if sanitized != original:
        needs_masking += 1
        for marker, label in (
            ("[REDACTED_SECRET]", "secret"),
            ("[REDACTED_EMAIL]", "email"),
            ("[REDACTED_IP]", "ip"),
            ("[REDACTED_EVENT]", "invalid_or_empty"),
        ):
            if marker in sanitized:
                patterns[label] += 1

print("DATABASE_READ_ONLY: YES")
print("EVIDENCE_ROWS_SCANNED:", total)
print("ROWS_REQUIRING_MASKING:", needs_masking)
print("DETECTION_COUNTS:", dict(patterns))
print("PRODUCTION_DATABASE_MODIFIED: NO")
PY
```

At build time 28 rows were examined, and 0 needed masking.

## 4.2 DB Files

```bash
stat -c '%A (%a) %U:%G %n' /opt/ai-defense-manager/data /opt/ai-defense-manager/data/ai-defense.db /opt/ai-defense-manager/data/ai-defense.db-wal /opt/ai-defense-manager/data/ai-defense.db-shm 2>&1
```

| Target | Owner | Permissions |
|---|---|---:|
| `data` directory | `ai-defense:ai-defense` | 750 |
| DB file | `ai-defense:ai-defense` | 600 |
| WAL | `ai-defense:ai-defense` | 600 |
| SHM | `ai-defense:ai-defense` | 600 |

## 4.3 Service Settings

```bash
systemctl show ai-defense-manager.service -p User -p Group -p NoNewPrivileges -p ProtectSystem -p ProtectHome -p PrivateTmp -p PrivateDevices -p RestrictSUIDSGID -p LockPersonality -p ReadWritePaths
```

It runs as `ai-defense`, not root; the file system is read-only in principle; and only the `data` directory is writable.

## 4.4 Listening Ports

```bash
ss -lntp
```

| Port | Listening on | Assessment |
|---|---|---|
| 8000 (FastAPI) | `127.0.0.1` | Cannot be reached directly from outside |
| 22 (SSH) | `0.0.0.0`, `[::]` | Checked in the next part |
| 53 (DNS) | `127.0.0.53`, `127.0.0.54` | Local only |

# Closing Notes

In Part 20 we did the following.

| Item | Result |
|---|---|
| Analysis failure (`502`) | Resolved by adding an instruction to return confidence as 0.0–1.0 |
| Masking | Made common in `event_sanitizer.py` and used both before sending to the LLM and before saving to SQLite |
| Saved history | 28 rows checked; none needed masking |
| DB, service, ports | Checked; no problems |

In the next part, we switch SSH on VM 230 to log in with a public key instead of a password.

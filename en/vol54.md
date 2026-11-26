---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 54: Masking LLM Output and the Approval Policy"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 54 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". The checks in Part 53 showed that LLM output (`summary`, `reasoning`) is stored and returned without masking, and that the LLM can decide whether approval is required. Here we fix these as follows.

| Target | Fix |
|---|---|
| Event input | keep the current masking (512 characters) |
| LLM `summary`, `reasoning` | remove secrets and personal information through a dedicated entry point, limited to 2,000 and 4,000 characters |
| API return values, storage in SQLite | only masked proposals |
| Whether approval is required | decided on the server side; everything other than `no_action` requires human approval |
| Temporary IP blocking | always requires human approval; TTL at most 900 seconds |
| Wazuh event retrieval API | the returned summaries and descriptions are also masked |

The LLM is limited to analysis, and the AI Defense Manager side guarantees output safety and approval decisions. The Action Gateway (actual execution of actions) is not built yet.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: Saving Copies Before the Change

We save copies of the four target files and record syntax, owner, permissions and hashes. The sources, DB and services are not touched.

> **Run on: VM 230**

```bash
echo "===== VM230: PRE-CHANGE BACKUP AND INTEGRITY CHECK ====="

cd /opt/ai-defense-manager

BACKUP_DIR="/var/backups/ai-defense-manager/llm-output-policy-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

FILES=(
  app/services/event_sanitizer.py
  app/services/ai_analysis.py
  app/services/analysis_history.py
  app/schemas/analysis_proposal.py
)

echo
echo "--- Source metadata and hashes ---"
for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    stat -c 'FILE=%n OWNER=%U:%G MODE=%a SIZE=%s' "$file"
    sha256sum "$file"
  else
    echo "MISSING=$file"
  fi
done

echo
echo "--- Creating metadata-preserving backups ---"
for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    mkdir -p "$BACKUP_DIR/$(dirname "$file")"
    cp -a "$file" "$BACKUP_DIR/$file"
  fi
done

echo
echo "--- Backup integrity verification ---"
for file in "${FILES[@]}"; do
  if [ -f "$file" ] && [ -f "$BACKUP_DIR/$file" ]; then
    ORIGINAL_HASH="$(sha256sum "$file" | awk '{print $1}')"
    BACKUP_HASH="$(sha256sum "$BACKUP_DIR/$file" | awk '{print $1}')"
    if [ "$ORIGINAL_HASH" = "$BACKUP_HASH" ]; then
      echo "BACKUP=PASS FILE=$file"
    else
      echo "BACKUP=FAIL FILE=$file"
    fi
  else
    echo "BACKUP=FAIL FILE=$file"
  fi
done

echo
echo "--- Backup directory ---"
printf '%s\n' "$BACKUP_DIR"
stat -c 'OWNER=%U:%G MODE=%a' "$BACKUP_DIR"

echo
echo "--- Test tooling ---"
if [ -x venv/bin/pytest ]; then
  echo "PYTEST=AVAILABLE"
else
  echo "PYTEST=NOT_FOUND"
fi

echo
echo "SOURCE_MODIFIED=NO"
echo "DATABASE_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

The copies of all four files matched, and the original owners and permissions were recorded.

# Chapter 2: Adding LLM Output Masking and the Approval Policy

## 2.1 Rewriting the Four Files

Keeping the 512-character limit of the event masking, we add dedicated entry points for LLM output with 2,000 and 4,000 characters. We do not trust the LLM's value for whether approval is required; everything other than `no_action` always requires approval on the server side, and the same rule is applied again when storing in the DB.

> **Run on: VM 230**

```bash
echo "===== VM230: APPLY LLM OUTPUT SANITIZATION AND APPROVAL POLICY ====="

cd /opt/ai-defense-manager

venv/bin/python - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager")
backup = Path("/var/backups/ai-defense-manager/llm-output-policy-20261123-141801")

files = [
    "app/services/event_sanitizer.py",
    "app/services/ai_analysis.py",
    "app/services/analysis_history.py",
    "app/schemas/analysis_proposal.py",
]

for rel in files:
    if not (root / rel).is_file() or not (backup / rel).is_file():
        raise RuntimeError(f"Source or verified backup missing: {rel}")

changes = {}

# 1. Preserve the existing redaction expressions and add length-specific entry points.
rel = "app/services/event_sanitizer.py"
s = (root / rel).read_text(encoding="utf-8")

old = "def sanitize_event_summary(value: str) -> str:"
new = "def _sanitize_text(value: str, max_length: int) -> str:"
if s.count(old) != 1:
    raise RuntimeError("Sanitizer function definition mismatch")
s = s.replace(old, new)

old = "return value[:512] if value.strip() else \"[REDACTED_EVENT]\""
new = "return value[:max_length] if value.strip() else \"[REDACTED_EVENT]\""
if s.count(old) != 1:
    raise RuntimeError("Sanitizer length limit expression mismatch")
s = s.replace(old, new)

s += '''

def sanitize_event_summary(value: str) -> str:
    """Sanitize event summaries using the established 512-character limit."""
    return _sanitize_text(value, 512)


def sanitize_analysis_text(value: str, max_length: int) -> str:
    """Sanitize untrusted LLM text with a caller-defined field limit."""
    if (
        not isinstance(max_length, int)
        or isinstance(max_length, bool)
        or max_length < 1
    ):
        raise ValueError("max_length must be a positive integer")
    return _sanitize_text(value, max_length)
'''
changes[rel] = s

# 2. Sanitize LLM output and override its approval flag before API return.
rel = "app/services/ai_analysis.py"
s = (root / rel).read_text(encoding="utf-8")

old = "from app.services.event_sanitizer import sanitize_event_summary"
new = (
    "from app.services.event_sanitizer import "
    "sanitize_analysis_text, sanitize_event_summary"
)
if s.count(old) != 1:
    raise RuntimeError("AI analysis sanitizer import mismatch")
s = s.replace(old, new)

old = "        return proposal\n"
new = '''        # Server policy is authoritative; the model cannot waive approval.
        return proposal.model_copy(
            update={
                "summary": sanitize_analysis_text(proposal.summary, 2000),
                "reasoning": sanitize_analysis_text(proposal.reasoning, 4000),
                "requires_human_approval": (
                    proposal.recommended_action.value != "no_action"
                ),
            }
        )
'''
if s.count(old) != 1:
    raise RuntimeError("AI analysis return point mismatch")
s = s.replace(old, new)
changes[rel] = s

# 3. Reapply sanitization and approval policy at the persistence boundary.
rel = "app/services/analysis_history.py"
s = (root / rel).read_text(encoding="utf-8")

old = "from app.services.event_sanitizer import sanitize_event_summary"
new = (
    "from app.services.event_sanitizer import "
    "sanitize_analysis_text, sanitize_event_summary"
)
if s.count(old) != 1:
    raise RuntimeError("Analysis history sanitizer import mismatch")
s = s.replace(old, new)

old = '''    action_requires_approval = (
        proposal.requires_human_approval
        and proposal.recommended_action.value != "no_action"
    )
'''
new = '''    # Never trust the LLM's approval flag when persisting policy state.
    action_requires_approval = proposal.recommended_action.value != "no_action"
    safe_summary = sanitize_analysis_text(proposal.summary, 2000)
    safe_reasoning = sanitize_analysis_text(proposal.reasoning, 4000)
'''
if s.count(old) != 1:
    raise RuntimeError("Analysis history approval policy mismatch")
s = s.replace(old, new)

for old, new in (
    ("                proposal.summary,", "                safe_summary,"),
    ("                proposal.reasoning,", "                safe_reasoning,"),
    (
        "                int(proposal.requires_human_approval),",
        "                int(action_requires_approval),",
    ),
):
    if s.count(old) != 1:
        raise RuntimeError(f"Analysis history SQL value mismatch: {old.strip()}")
    s = s.replace(old, new)

changes[rel] = s

# 4. Document that the model-provided flag is advisory only.
rel = "app/schemas/analysis_proposal.py"
s = (root / rel).read_text(encoding="utf-8")

old = "    requires_human_approval: bool = True\n"
new = '''    requires_human_approval: bool = Field(
        default=True,
        description=(
            "Advisory model field only. Server policy overrides this value: "
            "all actions except no_action require human approval."
        ),
    )
'''
if s.count(old) != 1:
    raise RuntimeError("Proposal schema approval field mismatch")
s = s.replace(old, new)
changes[rel] = s

# Validate all proposed contents before writing any file.
for rel, source in changes.items():
    ast.parse(source, filename=rel)
    print(f"PREWRITE_SYNTAX=PASS FILE={rel}")

# Write only after every replacement and syntax check has passed.
for rel, source in changes.items():
    (root / rel).write_text(source, encoding="utf-8")
    print(f"WRITE=PASS FILE={rel}")

print("ALL_FOUR_FILES_UPDATED=YES")
PY

echo
echo "--- Post-edit syntax compilation ---"
venv/bin/python -m compileall -q \
  app/services/event_sanitizer.py \
  app/services/ai_analysis.py \
  app/services/analysis_history.py \
  app/schemas/analysis_proposal.py

echo "COMPILEALL_EXIT=$?"

echo
echo "--- File ownership, modes and hashes ---"
stat -c 'FILE=%n OWNER=%U:%G MODE=%a SIZE=%s' \
  app/services/event_sanitizer.py \
  app/services/ai_analysis.py \
  app/services/analysis_history.py \
  app/schemas/analysis_proposal.py

sha256sum \
  app/services/event_sanitizer.py \
  app/services/ai_analysis.py \
  app/services/analysis_history.py \
  app/schemas/analysis_proposal.py

echo
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

Writing the four files and the Python syntax check succeeded, and the owners and permissions were unchanged.

## 2.2 Functional Tests (10 Cases)

We do not connect to the real DB; we check with a fake DB for testing.

> **Run on: VM 230**

```bash
echo "===== VM230: LLM OUTPUT AND APPROVAL POLICY TEST ====="

cd /opt/ai-defense-manager

venv/bin/python - <<'PY'
import ast
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from app.services.event_sanitizer import (
    sanitize_analysis_text,
    sanitize_event_summary,
)
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import (
    AIAnalysisProposal,
    RecommendedAction,
)
from app.services import analysis_history

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    print(f"{name}={'PASS' if condition else 'FAIL'}")
    if condition:
        passed += 1
    else:
        failed += 1

# 1. Preserve the established event sanitizer behavior.
event_text = sanitize_event_summary("A" * 600)
check("EVENT_LIMIT_512", len(event_text) == 512)

# 2. LLM output redaction and independent field limits.
summary = sanitize_analysis_text(
    "password=synthetic-secret user@example.com 203.0.113.10",
    2000,
)
reasoning = sanitize_analysis_text(
    "Bearer synthetic.token.value " + ("R" * 5000),
    4000,
)
check(
    "LLM_SUMMARY_REDACTION",
    "synthetic-secret" not in summary
    and "user@example.com" not in summary
    and "203.0.113.10" not in summary,
)
check(
    "LLM_REASONING_REDACTION",
    "synthetic.token.value" not in reasoning
    and "Bearer [REDACTED_SECRET]" in reasoning,
)
check("LLM_SUMMARY_LIMIT", len(sanitize_analysis_text("S" * 3000, 2000)) == 2000)
check("LLM_REASONING_LIMIT", len(reasoning) == 4000)

# 3. Schema permits advisory false for a non-block action;
# server-side persistence must override it.
event_id = uuid4()
request = AIAnalysisRequest(
    events=[{
        "source": "wazuh",
        "observed_at": "2026-11-23T12:00:00Z",
        "severity": "high",
        "rule_id": "5710",
        "event_category": "authentication",
        "event_summary": "Authentication failure",
    }]
)
event_id = request.events[0].event_id

proposal = AIAnalysisProposal(
    summary="password=proposal-secret",
    severity="high",
    confidence=0.9,
    evidence_event_ids=[event_id],
    recommended_action=RecommendedAction.NOTIFY,
    requires_human_approval=False,
    reasoning="Bearer reasoning.secret.value",
)

captured = []

class FakeConnection:
    def execute(self, sql, params=()):
        captured.append((sql, params))
        return self

@contextmanager
def fake_connection():
    yield FakeConnection()

original_connection = analysis_history._connection
analysis_history._connection = fake_connection

try:
    run_id = analysis_history.save_analysis(request, proposal)
finally:
    analysis_history._connection = original_connection

analysis_insert = next(
    params for sql, params in captured if "INSERT INTO analysis_runs" in sql
)
proposal_insert = next(
    params for sql, params in captured if "INSERT INTO action_proposals" in sql
)
approval_insert = next(
    params for sql, params in captured if "INSERT INTO action_approvals" in sql
)

check("SAVE_ANALYSIS_RETURNS_RUN_ID", isinstance(run_id, str) and len(run_id) > 0)
check(
    "DB_SUMMARY_SANITIZED",
    "proposal-secret" not in analysis_insert[5],
)
check(
    "DB_REASONING_SANITIZED",
    "reasoning.secret.value" not in analysis_insert[7],
)
check(
    "DB_NON_NO_ACTION_APPROVAL_FORCED",
    proposal_insert[5] == 1
    and proposal_insert[6] == "pending"
    and approval_insert[2] == "pending",
)

# 4. Static check of the AI return-boundary override.
tree = ast.parse(
    Path("app/services/ai_analysis.py").read_text(encoding="utf-8")
)
source = Path("app/services/ai_analysis.py").read_text(encoding="utf-8")
analyze = next(
    n for n in ast.walk(tree)
    if isinstance(n, ast.AsyncFunctionDef) and n.name == "analyze_events"
)
segment = ast.get_source_segment(source, analyze)
check(
    "AI_RETURN_BOUNDARY_POLICY_PRESENT",
    "model_copy" in segment
    and 'proposal.recommended_action.value != "no_action"' in segment
    and "sanitize_analysis_text(proposal.summary, 2000)" in segment
    and "sanitize_analysis_text(proposal.reasoning, 4000)" in segment,
)

print()
print(f"TESTS_PASSED={passed}")
print(f"TESTS_FAILED={failed}")
print("REAL_DATABASE_ACCESSED=NO")
print("OLLAMA_ACCESSED=NO")
print("LIVE_WAZUH_ACCESSED=NO")
PY

echo
echo "SERVICE_RESTARTED=NO"
echo "SOURCE_MODIFIED_BY_TEST=NO"
```

**All 10 passed.**

- The 512-character limit on event summaries is unchanged
- The LLM's `summary` and `reasoning` are limited to 2,000 and 4,000 characters, and secrets are masked
- For anything other than `no_action`, approval is required on the server side even if the LLM returns `requires_human_approval=false`
- The same approval rule and masking are applied when storing in SQLite

## 2.3 Edges of the Approval Policy (5 Cases)

> **Run on: VM 230**

```bash
echo "===== VM230: APPROVAL POLICY BOUNDARY TEST ====="

cd /opt/ai-defense-manager

venv/bin/python - <<'PY'
from contextlib import contextmanager
from uuid import uuid4

from pydantic import ValidationError

from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import (
    AIAnalysisProposal,
    RecommendedAction,
)
from app.services import analysis_history

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    print(f"{name}={'PASS' if condition else 'FAIL'}")
    if condition:
        passed += 1
    else:
        failed += 1

request = AIAnalysisRequest(events=[
    {
        "source": "wazuh",
        "observed_at": "2026-11-23T12:00:00Z",
        "severity": "high",
        "rule_id": "5710",
        "event_category": "authentication",
        "event_summary": "Synthetic event one",
    },
    {
        "source": "wazuh",
        "observed_at": "2026-11-23T12:01:00Z",
        "severity": "high",
        "rule_id": "5711",
        "event_category": "authentication",
        "event_summary": "Synthetic event two",
    },
])

captured = []

class FakeConnection:
    def execute(self, sql, params=()):
        captured.append((sql, params))
        return self

@contextmanager
def fake_connection():
    yield FakeConnection()

original_connection = analysis_history._connection
analysis_history._connection = fake_connection

try:
    no_action = AIAnalysisProposal(
        summary="No action required",
        severity="low",
        confidence=0.95,
        evidence_event_ids=[request.events[0].event_id],
        recommended_action=RecommendedAction("no_action"),
        requires_human_approval=True,
        reasoning="Synthetic no-action test",
    )

    captured.clear()
    analysis_history.save_analysis(request, no_action)

    proposal_row = next(
        p for s, p in captured if "INSERT INTO action_proposals" in s
    )
    approval_row = next(
        p for s, p in captured if "INSERT INTO action_approvals" in s
    )

    check(
        "NO_ACTION_FORCES_APPROVAL_NOT_REQUIRED",
        proposal_row[5] == 0
        and proposal_row[6] == "not_required"
        and approval_row[2] == "not_required",
    )

    valid_block = AIAnalysisProposal(
        summary="Synthetic public IP block proposal",
        severity="critical",
        confidence=0.99,
        evidence_event_ids=[
            request.events[0].event_id,
            request.events[1].event_id,
        ],
        recommended_action=RecommendedAction("temporary_block_ip"),
        target_ip="8.8.8.8",
        ttl_seconds=300,
        requires_human_approval=True,
        reasoning="Synthetic test only",
    )

    captured.clear()
    analysis_history.save_analysis(request, valid_block)

    proposal_row = next(
        p for s, p in captured if "INSERT INTO action_proposals" in s
    )
    approval_row = next(
        p for s, p in captured if "INSERT INTO action_approvals" in s
    )

    check(
        "PUBLIC_IP_BLOCK_REQUIRES_PENDING_APPROVAL",
        proposal_row[5] == 1
        and proposal_row[6] == "pending"
        and approval_row[2] == "pending",
    )

    try:
        AIAnalysisProposal(
            summary="Invalid block without approval",
            severity="critical",
            confidence=0.99,
            evidence_event_ids=[
                request.events[0].event_id,
                request.events[1].event_id,
            ],
            recommended_action=RecommendedAction("temporary_block_ip"),
            target_ip="8.8.8.8",
            ttl_seconds=300,
            requires_human_approval=False,
            reasoning="Synthetic invalid test",
        )
        approval_false_rejected = False
    except ValidationError:
        approval_false_rejected = True

    check(
        "BLOCK_REJECTS_MISSING_HUMAN_APPROVAL",
        approval_false_rejected,
    )

    try:
        AIAnalysisProposal(
            summary="Invalid private IP block",
            severity="critical",
            confidence=0.99,
            evidence_event_ids=[
                request.events[0].event_id,
                request.events[1].event_id,
            ],
            recommended_action=RecommendedAction("temporary_block_ip"),
            target_ip="192.168.0.10",
            ttl_seconds=300,
            requires_human_approval=True,
            reasoning="Synthetic invalid test",
        )
        private_ip_rejected = False
    except ValidationError:
        private_ip_rejected = True

    check(
        "BLOCK_REJECTS_PRIVATE_IP",
        private_ip_rejected,
    )

    try:
        AIAnalysisProposal(
            summary="Invalid block with one evidence",
            severity="critical",
            confidence=0.99,
            evidence_event_ids=[request.events[0].event_id],
            recommended_action=RecommendedAction("temporary_block_ip"),
            target_ip="8.8.8.8",
            ttl_seconds=300,
            requires_human_approval=True,
            reasoning="Synthetic invalid test",
        )
        single_evidence_rejected = False
    except ValidationError:
        single_evidence_rejected = True

    check(
        "BLOCK_REJECTS_SINGLE_EVIDENCE",
        single_evidence_rejected,
    )

finally:
    analysis_history._connection = original_connection

print()
print(f"TESTS_PASSED={passed}")
print(f"TESTS_FAILED={failed}")
print("REAL_DATABASE_ACCESSED=NO")
print("OLLAMA_ACCESSED=NO")
print("LIVE_WAZUH_ACCESSED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

| Checked | Result |
|---|---|
| `no_action` requires no approval | passed |
| Temporary blocking of a public IP waits for approval | passed |
| A blocking proposal without approval is rejected | passed |
| A blocking proposal for a private IP is rejected | passed |
| A blocking proposal with only one evidence event is rejected | passed |

All 15 functional tests so far have passed.

# Chapter 3: Masking the Wazuh Event Retrieval API Too

## 3.1 Checking the API Return Values

> **Run on: VM 230**

```bash
echo "===== VM230: API RESPONSE BOUNDARY STATIC AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- Analysis API routes ---"
for f in app/api/analysis.py app/api/wazuh.py; do
    if [ -f "$f" ]; then
        echo
        echo "### $f"
        nl -ba "$f" | sed -n '1,300p'
    fi
done

echo
echo "--- Response and request schemas ---"
for f in \
    app/schemas/analysis.py \
    app/schemas/analysis_proposal.py \
    app/schemas/security_event.py \
    app/schemas/wazuh.py
do
    if [ -f "$f" ]; then
        echo
        echo "### $f"
        nl -ba "$f" | sed -n '1,260p'
    fi
done

echo
echo "--- Router registration and exception handling ---"
grep -RInE \
    'include_router|exception_handler|HTTPException|response_model|return proposal|return .*analysis|save_analysis' \
    app/main.py app/api app/core \
    --include='*.py' 2>/dev/null | head -240

echo
echo "--- API response boundary audit complete ---"
echo "FILES_MODIFIED=NO"
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "LIVE_WAZUH_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

The two analysis APIs store the proposal returned by `analyze_events()` before returning it, so the masking and approval policy of Chapter 2 also apply to the responses. However, `GET /api/v1/wazuh/events` does not go through AI analysis and returns the result of `fetch_wazuh_events()` as is.

## 3.2 The Conversion in the Retrieval API

> **Run on: VM 230**

```bash
echo "===== VM230: WAZUH EVENT RESPONSE SANITIZATION AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- Wazuh relay conversion ---"
nl -ba app/services/wazuh_relay.py | sed -n '1,280p'

echo
echo "--- Event sanitizer implementation ---"
nl -ba app/services/event_sanitizer.py | sed -n '1,240p'

echo
echo "--- Sanitizer usage across application ---"
grep -RInE \
    'sanitize_event_summary|event_summary\s*=|event_summary=' \
    app --include='*.py' 2>/dev/null

echo
echo "--- Wazuh event endpoint response path ---"
grep -RInE \
    'fetch_wazuh_events|@router.get\("/events"|response_model=list\[SecurityEvent\]' \
    app --include='*.py' 2>/dev/null

echo
echo "FILES_MODIFIED=NO"
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "LIVE_WAZUH_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

`_convert_alert()` put Wazuh's `rule.description` into `event_summary` and `rule_description` as is. So `GET /api/v1/wazuh/events` could return unmasked strings.

## 3.3 Fixing

We fix only `wazuh_relay.py`, after making a copy, applying `sanitize_event_summary()` to both `event_summary` and `rule_description`. We check with synthetic data.

> **Run on: VM 230**

```bash
echo "===== VM230: WAZUH EVENT RESPONSE SANITIZATION FIX ====="

cd /opt/ai-defense-manager

venv/bin/python - <<'PY'
import ast
import hashlib
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone

path = Path("app/services/wazuh_relay.py")
source = path.read_text(encoding="utf-8")

backup_dir = Path(
    "/var/backups/ai-defense-manager/wazuh-response-sanitization-20261123"
)
backup_dir.mkdir(parents=True, exist_ok=True)
backup = backup_dir / "wazuh_relay.py"

if backup.exists():
    raise RuntimeError(f"Backup already exists: {backup}")

shutil.copy2(path, backup)

def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

backup_hash = sha256(backup)
original_hash = sha256(path)

if backup_hash != original_hash:
    raise RuntimeError("Backup integrity check failed")

print("BACKUP_CREATED=PASS")
print("BACKUP_SHA256_MATCH=PASS")

updated = source

import_anchor = "from app.schemas.security_event import SecurityEvent\n"
if updated.count(import_anchor) != 1:
    raise RuntimeError("Could not uniquely locate SecurityEvent import")

updated = updated.replace(
    import_anchor,
    import_anchor
    + "from app.services.event_sanitizer import sanitize_event_summary\n",
    1,
)

old_summary = '    summary = (description or "Wazuh security alert")[:512]\n'
new_summary = (
    '    summary = sanitize_event_summary(\n'
    '        description or "Wazuh security alert"\n'
    '    )\n'
)
if updated.count(old_summary) != 1:
    raise RuntimeError("Could not uniquely locate event summary assignment")

updated = updated.replace(old_summary, new_summary, 1)

old_description = (
    '        rule_description=description[:512] if description else None,\n'
)
new_description = (
    '        rule_description=(\n'
    '            sanitize_event_summary(description) if description else None\n'
    '        ),\n'
)
if updated.count(old_description) != 1:
    raise RuntimeError("Could not uniquely locate rule_description assignment")

updated = updated.replace(old_description, new_description, 1)

# Validate syntax before writing.
ast.parse(updated)

path.write_text(updated, encoding="utf-8")

# Preserve the original file's ownership and mode.
shutil.copystat(backup, path)
try:
    st = backup.stat()
    os.chown(path, st.st_uid, st.st_gid)
except PermissionError:
    raise RuntimeError("Unable to preserve source ownership")

print("SOURCE_PATCH=APPLIED")
print("PYTHON_SYNTAX=PASS")
print("SOURCE_SHA256_BEFORE=" + original_hash)
print("SOURCE_SHA256_AFTER=" + sha256(path))
PY

echo
echo "--- Synthetic sanitizer behavior test ---"

venv/bin/python - <<'PY'
from datetime import datetime, timezone

from app.services.wazuh_relay import _convert_alert

description = (
    "Failed login password=synthetic-secret "
    "contact=user@example.com source=203.0.113.10"
)

event = _convert_alert({
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "rule.level": 10,
    "rule.id": "5710",
    "rule.description": description,
    "rule.groups": ["authentication_failed"],
    "agent.id": "001",
})

checks = {
    "EVENT_SUMMARY_SECRET_REDACTED":
        "synthetic-secret" not in event.event_summary,
    "RULE_DESCRIPTION_SECRET_REDACTED":
        "synthetic-secret" not in (event.rule_description or ""),
    "EVENT_SUMMARY_EMAIL_REDACTED":
        "user@example.com" not in event.event_summary,
    "RULE_DESCRIPTION_EMAIL_REDACTED":
        "user@example.com" not in (event.rule_description or ""),
    "EVENT_SUMMARY_IP_REDACTED":
        "203.0.113.10" not in event.event_summary,
    "RULE_DESCRIPTION_IP_REDACTED":
        "203.0.113.10" not in (event.rule_description or ""),
    "EVENT_SUMMARY_LIMIT_512":
        len(event.event_summary) <= 512,
    "RULE_DESCRIPTION_LIMIT_512":
        len(event.rule_description or "") <= 512,
    "EVENT_CATEGORY_PRESERVED":
        event.event_category == "authentication",
}

for name, ok in checks.items():
    print(f"{name}={'PASS' if ok else 'FAIL'}")

print()
print(f"TESTS_PASSED={sum(checks.values())}")
print(f"TESTS_FAILED={len(checks) - sum(checks.values())}")
PY

echo
echo "--- Final source metadata ---"
stat -c 'OWNER=%U GROUP=%G MODE=%a SIZE=%s' app/services/wazuh_relay.py
sha256sum app/services/wazuh_relay.py

echo
echo "REAL_WAZUH_ACCESSED=NO"
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

The synthetic tests after the fix **all 9 passed**, confirming masking of secrets, email addresses and IP addresses and the 512-character limit.

# Chapter 4: Checking Permissions and Restarting

## 4.1 File Permissions

> **Run on: VM 230**

```bash
echo "===== VM230: WAZUH RELAY SOURCE PERMISSION PRECHECK ====="

cd /opt/ai-defense-manager

echo
echo "--- Service identity ---"
systemctl show ai-defense-manager.service \
  -p User -p Group -p SupplementaryGroups -p MainPID

echo
echo "--- Source and backup metadata ---"
stat -c '%n OWNER=%U GROUP=%G MODE=%a' \
  app/services/wazuh_relay.py \
  /var/backups/ai-defense-manager/wazuh-response-sanitization-20261123/wazuh_relay.py

echo
echo "--- Parent directory permissions ---"
namei -l /opt/ai-defense-manager/app/services/wazuh_relay.py

echo
echo "--- Read access as service user ---"
runuser -u ai-defense -- test -r app/services/wazuh_relay.py
echo "SERVICE_USER_SOURCE_READABLE=$?"

echo
echo "--- Backup and source hashes ---"
sha256sum \
  app/services/wazuh_relay.py \
  /var/backups/ai-defense-manager/wazuh-response-sanitization-20261123/wazuh_relay.py

echo
echo "FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

The fixed `wazuh_relay.py` had become `root:root`, `640`, so the service user `ai-defense` could not read it. **It cannot be restarted in this state.**

## 4.2 Restoring the Group

Keeping owner `root` and mode `640`, we restore only the group to `ai-defense`.

> **Run on: VM 230**

```bash
echo "===== VM230: RESTORE WAZUH RELAY SOURCE READ PERMISSION ====="

cd /opt/ai-defense-manager

chgrp ai-defense app/services/wazuh_relay.py

echo
echo "--- Updated source metadata ---"
stat -c 'OWNER=%U GROUP=%G MODE=%a' app/services/wazuh_relay.py

echo
echo "--- Service user read test ---"
if runuser -u ai-defense -- test -r app/services/wazuh_relay.py; then
    echo "SERVICE_USER_SOURCE_READABLE=PASS"
else
    echo "SERVICE_USER_SOURCE_READABLE=FAIL"
fi

echo
echo "--- Source integrity ---"
sha256sum app/services/wazuh_relay.py

echo
echo "SOURCE_CONTENT_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Item | Result |
|---|---|
| Owner | `root` (unchanged) |
| Group | `ai-defense` (restored) |
| Mode | `640` (unchanged) |
| Read by the service user | passed |
| Source SHA256 | matches the value after the fix (contents not changed) |

## 4.3 Restarting

> **Run on: VM 230**

```bash
echo "===== VM230: AI DEFENSE MANAGER RESTART ====="

systemctl restart ai-defense-manager.service
echo "RESTART_EXIT_CODE=$?"

echo
echo "--- Service status ---"
systemctl is-active ai-defense-manager.service
systemctl show ai-defense-manager.service \
  -p MainPID -p User -p Group -p ActiveState -p SubState

echo
echo "--- API listener ---"
ss -lntp | grep ':8000' || echo "API_LISTENER_NOT_FOUND"

echo
echo "--- Health check ---"
curl --silent --show-error \
  --connect-timeout 3 --max-time 10 \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "WAZUH_ALERTS_FETCHED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "ANALYSIS_TRIGGERED=NO"
echo "DATABASE_WRITE_TRIGGERED=NO"
```

The restart gave exit code `0`, but the check right after showed nothing listening on port 8000, and `/health` gave `HTTP 000`.

## 4.4 Checking the Startup

> **Run on: VM 230**

```bash
echo "===== VM230: AI DEFENSE MANAGER STARTUP FAILURE DIAGNOSTICS ====="

echo
echo "--- Full service status ---"
systemctl status ai-defense-manager.service --no-pager -l

echo
echo "--- Recent service journal ---"
journalctl -u ai-defense-manager.service \
  --since "-15 minutes" --no-pager -n 120

echo
echo "--- Process details ---"
ps -o pid,ppid,user,group,stat,lstart,args -p 1469

echo
echo "--- Listening sockets ---"
ss -lntp

echo
echo "--- Service unit ---"
systemctl cat ai-defense-manager.service

echo
echo "--- Recent application errors ---"
journalctl -u ai-defense-manager.service \
  --since "-15 minutes" --no-pager |
  grep -iE 'error|exception|traceback|failed|permission|import|uvicorn|startup|shutdown' |
  tail -80

echo
echo "CONFIGURATION_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "LIVE_WAZUH_ACCESSED=NO"
```

systemd showed `active (running)`, Uvicorn showed `Application startup complete`, the PID was `1469`, and it was listening on `127.0.0.1:8000`. The earlier result was because the check came right after the restart.

> **Run on: VM 230**

```bash
echo "===== VM230: POST-RESTART API HEALTH VERIFICATION ====="

echo
echo "--- Listener ---"
ss -lntp | grep '127.0.0.1:8000'

echo
echo "--- Health endpoint ---"
curl --silent --show-error \
  --connect-timeout 3 --max-time 10 \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "API_BINDING=127.0.0.1:8000"
echo "WAZUH_ALERTS_FETCHED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "ANALYSIS_TRIGGERED=NO"
echo "DATABASE_WRITE_TRIGGERED=NO"
```

| Item | Result |
|---|---|
| AI Defense Manager | `active` (PID `1469`) |
| Listening | `127.0.0.1:8000` |
| `/health` | `HTTP 200` |
| Running as | `ai-defense` |

# Closing Notes

In Part 54 we made the AI Defense Manager side protect the LLM output and approval decisions.

| Item | Result |
|---|---|
| LLM `summary`, `reasoning` | masked; limited to 2,000 and 4,000 characters |
| Approval | everything other than `no_action` always requires approval on the server side (applied again when storing in the DB) |
| Temporary blocking | requires a public IP, two pieces of evidence and approval; private IPs are rejected |
| Wazuh event retrieval API | `event_summary` and `rule_description` are also masked |
| Tests | all 10, 5 and 9 cases passed |
| Permissions | `wazuh_relay.py` is `root:ai-defense`, `640` |
| Service | restarted; `/health` is `HTTP 200` |

> **Caution:** After rewriting source files, check that owner, group and mode are `root:ai-defense`, `640` before restarting. With `root:root` the service cannot read them.

In the next part, Part 55, we check the integration as a whole and add limits that protect the API from high request volumes.

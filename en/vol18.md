---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 18: Keeping the Analysis History in SQLite"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 18 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". We record the results of AI analysis, the events they were based on, and the defense proposals and their approval state in SQLite inside VM 230.

The PostgreSQL server is not used for now (at build time we adopted the policy "store in SQLite inside VM 230 for now"). SQLite can be used with Python's standard library alone (`sqlite3`), so no packages need to be added.

| Item | Design |
|---|---|
| DB | SQLite 3 |
| Location | `/opt/ai-defense-manager/data/ai-defense.db` |
| Journal | WAL |
| DB access | Python's standard `sqlite3` |
| Run-as user | `ai-defense` |
| Transactions | The analysis result and its evidence events are saved together |
| Repeated analyses | Each analysis becomes a separate record |
| Approval | Initial state is `pending` |
| Executing defenses | Not built this time |

There are five tables.

| Table | Contents |
|---|---|
| `analysis_runs` | Records of AI analysis runs |
| `analysis_evidence` | Identifiers and summaries of the events analyzed |
| `action_proposals` | The defenses proposed by the AI |
| `action_approvals` | Approval / rejection state by people |
| `audit_logs` | Records of operations (audit log) |

Wazuh's raw log (`full_log`), arbitrary `data`, commands, user names and authentication information are not stored.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **ai-defense-manager VM 230 (root)**.

# Chapter 1: Checking the Current State

## 1.1 PostgreSQL Settings

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
from app.core.config import settings

print("POSTGRES_HOST:", settings.postgres_host or "NOT_CONFIGURED")
print("POSTGRES_PORT:", settings.postgres_port)
print("POSTGRES_DATABASE:", settings.postgres_database or "NOT_CONFIGURED")
print("POSTGRES_CONFIG_CHECK_OK")
PY
```

At build time the host and database name were not set.

## 1.2 Existing DBs and DB Code

```bash
cd /opt/ai-defense-manager && find . -maxdepth 3 -type f \( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \) -printf '%p\n' | sort
```

```bash
cd /opt/ai-defense-manager && grep -RInE 'sqlalchemy|sqlite3|create_engine|AsyncSession|sessionmaker|DATABASE_URL|postgres' app requirements.lock --exclude='*.pyc' | head -n 100
```

At build time there was no SQLite file, no SQLAlchemy and no code that handles a DB (PostgreSQL existed only as setting fields).

## 1.3 Where to Store It

```bash
ls -ld /var/lib /var/lib/ai-defense-manager /opt/ai-defense-manager/data /opt/ai-defense-manager/logs 2>/dev/null
```

`/opt/ai-defense-manager/data` is `ai-defense:ai-defense` with `750`. It belongs to the run-as user, so the DB goes here.

```text
/opt/ai-defense-manager/data/ai-defense.db
```

```bash
cd /opt/ai-defense-manager && runuser -u ai-defense -- ./venv/bin/python - <<'PY'
import sqlite3

print("SQLITE_VERSION:", sqlite3.sqlite_version)
print("THREAD_SAFETY:", sqlite3.threadsafety)

conn = sqlite3.connect(":memory:")
print("JOURNAL_MODE:", conn.execute("PRAGMA journal_mode").fetchone()[0])
conn.close()

print("SQLITE_CHECK_OK")
PY
```

At build time this was SQLite 3.45.1 with `THREAD_SAFETY: 3`.

## 1.4 Checking Where to Build It In

```bash
cd /opt/ai-defense-manager && find app -maxdepth 3 -type f -name '*.py' -printf '%p\n' | sort
```

```bash
cd /opt/ai-defense-manager && sed -n '1,260p' app/api/wazuh.py
```

```bash
cd /opt/ai-defense-manager && sed -n '1,280p' app/schemas/analysis_proposal.py && echo '===== SECURITY EVENT =====' && sed -n '1,260p' app/schemas/security_event.py
```

```bash
cd /opt/ai-defense-manager && sed -n '1,240p' app/main.py && echo '===== ANALYSIS API =====' && sed -n '1,240p' app/api/analysis.py
```

```bash
cd /opt/ai-defense-manager && sed -n '1,300p' app/services/wazuh_relay.py
```

```bash
cd /opt/ai-defense-manager && sed -n '1,320p' app/services/ai_analysis.py
```

The findings were as follows.

- `SecurityEvent.event_id` is an ID generated on VM 230 by `uuid4()`. It is not Wazuh's original event ID, and fetching the same alert again may give a different ID. So column names that could be mistaken for Wazuh's original ID are not used.
- `ai_analysis.py` only queries the AI and validates the JSON. DB processing is not mixed in there; saving is done in the API layer after the analysis succeeds.

# Chapter 2: A Service That Saves the History

## 2.1 Backup

Back up the files to be changed.

```bash
BACKUP="/root/ai-defense-backup-$(date +%Y%m%d-%H%M%S)" && install -d -m 700 "$BACKUP" && cd /opt/ai-defense-manager && cp --parents app/main.py app/api/analysis.py app/api/wazuh.py app/schemas/analysis.py app/schemas/analysis_proposal.py app/schemas/security_event.py app/core/config.py "$BACKUP" && chmod -R go-rwx "$BACKUP" && echo "BACKUP_DIR=$BACKUP" && find "$BACKUP" -type f -printf '%P\n' | sort
```

## 2.2 analysis_history.py

Build DB initialization and saving of analysis results.

- All SQL uses placeholders (`?`)
- Writes to the five tables are combined into one transaction; if it fails partway, nothing is left
- If a proposal's evidence event IDs are not among the input events, nothing is saved
- For a `no_action` proposal, the approval is set to `not_required`

```bash
cd /opt/ai-defense-manager && cat > app/services/analysis_history.py <<'PY'
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal


DB_PATH = Path("/opt/ai-defense-manager/data/ai-defense.db")


SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis_runs (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    severity TEXT NOT NULL,
    confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 1),
    summary TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    evidence_count INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed'
);

CREATE TABLE IF NOT EXISTS analysis_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    source TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    severity TEXT NOT NULL,
    rule_id TEXT,
    event_summary TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES analysis_runs(run_id),
    UNIQUE(run_id, event_id)
);

CREATE TABLE IF NOT EXISTS action_proposals (
    proposal_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE,
    action_type TEXT NOT NULL,
    target_ip TEXT,
    ttl_seconds INTEGER,
    requires_human_approval INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES analysis_runs(run_id)
);

CREATE TABLE IF NOT EXISTS action_approvals (
    approval_id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL UNIQUE,
    decision TEXT NOT NULL,
    decided_by TEXT,
    decided_at TEXT,
    FOREIGN KEY(proposal_id) REFERENCES action_proposals(proposal_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_created_at
    ON analysis_runs(created_at);

CREATE INDEX IF NOT EXISTS idx_analysis_evidence_event_id
    ON analysis_evidence(event_id);

CREATE INDEX IF NOT EXISTS idx_action_proposals_status
    ON action_proposals(status);

CREATE INDEX IF NOT EXISTS idx_audit_logs_occurred_at
    ON audit_logs(occurred_at);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(
        DB_PATH,
        timeout=5.0,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA synchronous = FULL")
    return conn


def initialize_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with _connect() as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA)


def save_analysis(
    request: AIAnalysisRequest,
    proposal: AIAnalysisProposal,
) -> str:
    event_ids = {event.event_id for event in request.events}

    if not set(proposal.evidence_event_ids).issubset(event_ids):
        raise ValueError("Proposal contains unknown evidence event IDs")

    run_id = str(uuid4())
    proposal_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    action_requires_approval = (
        proposal.requires_human_approval
        and proposal.recommended_action.value != "no_action"
    )

    proposal_status = (
        "pending"
        if action_requires_approval
        else "not_required"
    )

    approval_decision = (
        "pending"
        if action_requires_approval
        else "not_required"
    )

    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")

        conn.execute(
            """
            INSERT INTO analysis_runs (
                run_id, created_at, severity, confidence, summary,
                recommended_action, reasoning, evidence_count, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'completed')
            """,
            (
                run_id,
                now,
                proposal.severity,
                proposal.confidence,
                proposal.summary,
                proposal.recommended_action.value,
                proposal.reasoning,
                len(request.events),
            ),
        )

        for event in request.events:
            conn.execute(
                """
                INSERT INTO analysis_evidence (
                    run_id, event_id, source, observed_at,
                    severity, rule_id, event_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    str(event.event_id),
                    event.source,
                    event.observed_at.isoformat(),
                    event.severity,
                    event.rule_id,
                    event.event_summary,
                ),
            )

        conn.execute(
            """
            INSERT INTO action_proposals (
                proposal_id, run_id, action_type, target_ip,
                ttl_seconds, requires_human_approval,
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal_id,
                run_id,
                proposal.recommended_action.value,
                proposal.target_ip,
                proposal.ttl_seconds,
                int(proposal.requires_human_approval),
                proposal_status,
                now,
            ),
        )

        conn.execute(
            """
            INSERT INTO action_approvals (
                approval_id, proposal_id, decision
            ) VALUES (?, ?, ?)
            """,
            (
                str(uuid4()),
                proposal_id,
                approval_decision,
            ),
        )

        conn.execute(
            """
            INSERT INTO audit_logs (
                occurred_at, actor, action, target_type, target_id
            ) VALUES (?, 'ai-defense-manager', 'analysis_created',
                      'analysis_run', ?)
            """,
            (now, run_id),
        )

    return run_id
PY
chown root:ai-defense app/services/analysis_history.py
chmod 640 app/services/analysis_history.py
```

```bash
cd /opt/ai-defense-manager && ls -l app/services/analysis_history.py && ./venv/bin/python -m py_compile app/services/analysis_history.py
```

## 2.3 Closing Connections Reliably

A `sqlite3` connection is not closed by a `with` statement alone (`with` only commits or rolls back the transaction). Add `_connection()`, which always closes the connection, and remove the unused `import json`.

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
from pathlib import Path

path = Path("app/services/analysis_history.py")
source = path.read_text(encoding="utf-8")

source = source.replace(
    "import json\nimport sqlite3\n",
    "import sqlite3\nfrom contextlib import contextmanager\n",
)
source = source.replace(
    "\ndef initialize_database() -> None:\n",
    """
@contextmanager
def _connection():
    conn = _connect()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def initialize_database() -> None:
""",
)
source = source.replace("with _connect() as conn:", "with _connection() as conn:")

path.write_text(source, encoding="utf-8")
print("CONNECTION_CLOSE_PATCH_APPLIED")
PY
```

```bash
cd /opt/ai-defense-manager && ./venv/bin/python -m py_compile app/services/analysis_history.py && grep -nE '^(import|from contextlib|def _connection|def initialize_database|def save_analysis)|with _connection' app/services/analysis_history.py
```

## 2.4 Testing with a Temporary DB

Without creating the production DB yet, check the following with a DB in a temporary directory.

1. The five tables are created
2. The analysis result, evidence events and approval state are saved
3. When saving fails partway (inserting the same event twice), no partial data remains

```bash
cd /opt/ai-defense-manager && runuser -u ai-defense -- ./venv/bin/python - <<'PY'
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal, RecommendedAction
from app.schemas.security_event import SecurityEvent
import app.services.analysis_history as history

with tempfile.TemporaryDirectory() as tmp:
    history.DB_PATH = Path(tmp) / "test.db"
    history.initialize_database()

    event_id = uuid4()
    event = SecurityEvent(
        event_id=event_id,
        source="wazuh",
        observed_at=datetime.now(timezone.utc),
        severity="medium",
        rule_id="100001",
        event_category="authentication",
        event_summary="Test security event",
    )

    request = AIAnalysisRequest(
        events=[event],
        requested_language="ja",
    )
    proposal = AIAnalysisProposal(
        summary="Test analysis",
        severity="medium",
        confidence=0.95,
        evidence_event_ids=[event_id],
        recommended_action=RecommendedAction.MONITOR,
        requires_human_approval=True,
        reasoning="Test only",
    )

    run_id = history.save_analysis(request, proposal)
    print("SAVE_TEST: OK")
    print("RUN_ID_CREATED:", bool(run_id))

    duplicate_request = AIAnalysisRequest(
        events=[event, event],
        requested_language="ja",
    )

    try:
        history.save_analysis(duplicate_request, proposal)
        raise AssertionError("Expected transaction failure did not occur")
    except sqlite3.IntegrityError:
        print("ROLLBACK_TEST: OK")

    with sqlite3.connect(history.DB_PATH) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        expected = {
            "analysis_runs",
            "analysis_evidence",
            "action_proposals",
            "action_approvals",
            "audit_logs",
        }
        assert expected.issubset(tables), tables

        counts = {
            table: conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            for table in sorted(expected)
        }
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]

    print("TABLES:", sorted(expected))
    print("COUNTS:", counts)
    print("JOURNAL_MODE:", mode)

    assert counts["analysis_runs"] == 1
    assert counts["analysis_evidence"] == 1
    assert counts["action_proposals"] == 1
    assert counts["action_approvals"] == 1
    assert counts["audit_logs"] == 1
    assert mode.lower() == "wal"

print("SQLITE_HISTORY_TESTS_OK")
PY
```

It has succeeded if `SQLITE_HISTORY_TESTS_OK` is shown. The temporary DB is deleted automatically.

# Chapter 3: Building It into the API

## 3.1 Saving request_id Too

```bash
cd /opt/ai-defense-manager && sed -n '1,220p' app/schemas/analysis.py
```

`AIAnalysisRequest` has a `request_id`, so save it to identify resent requests. Writes to SQLite are done with `asyncio.to_thread()` so that FastAPI's processing is not blocked for long.

It is built into the API as follows.

- Save after the analysis succeeds
- If saving fails, return `503` (do not return an analysis result that could not be saved as a success)
- Initialize the DB at application startup (`lifespan`)

```bash
cd /opt/ai-defense-manager && ./venv/bin/python - <<'PY'
from pathlib import Path

p = Path("app/services/analysis_history.py")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "    run_id TEXT PRIMARY KEY,\n    created_at TEXT NOT NULL,",
    "    run_id TEXT PRIMARY KEY,\n    request_id TEXT NOT NULL,\n    created_at TEXT NOT NULL,",
)
s = s.replace(
    "                run_id, created_at, severity, confidence, summary,\n                recommended_action, reasoning, evidence_count, status\n            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'completed')",
    "                run_id, request_id, created_at, severity, confidence, summary,\n                recommended_action, reasoning, evidence_count, status\n            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed')",
)
s = s.replace(
    "                run_id,\n                now,\n                proposal.severity,",
    "                run_id,\n                str(request.request_id),\n                now,\n                proposal.severity,",
)
p.write_text(s, encoding="utf-8")

Path("app/api/analysis.py").write_text('''import asyncio
import sqlite3

from fastapi import APIRouter, HTTPException

from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal
from app.services.ai_analysis import AIAnalysisError, analyze_events
from app.services.analysis_history import save_analysis

router = APIRouter(prefix="/api/v1", tags=["AI Analysis"])


@router.post(
    "/analysis",
    response_model=AIAnalysisProposal,
)
async def create_analysis(
    request: AIAnalysisRequest,
) -> AIAnalysisProposal:
    try:
        proposal = await analyze_events(request)
    except AIAnalysisError as exc:
        raise HTTPException(
            status_code=502,
            detail="AI analysis failed or returned an invalid response",
        ) from exc

    try:
        await asyncio.to_thread(save_analysis, request, proposal)
    except (sqlite3.Error, OSError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Analysis succeeded but history could not be saved",
        ) from exc

    return proposal
''', encoding="utf-8")

Path("app/api/wazuh.py").write_text('''import asyncio
import sqlite3

from fastapi import APIRouter, HTTPException, Query

from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal
from app.schemas.security_event import SecurityEvent
from app.schemas.wazuh import WazuhAnalysisRequest
from app.services.ai_analysis import AIAnalysisError, analyze_events
from app.services.analysis_history import save_analysis
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

        proposal = await analyze_events(analysis_request)

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

    try:
        await asyncio.to_thread(
            save_analysis,
            analysis_request,
            proposal,
        )
    except (sqlite3.Error, OSError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Analysis succeeded but history could not be saved",
        ) from exc

    return proposal
''', encoding="utf-8")

Path("app/main.py").write_text('''from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.api.analysis import router as analysis_router
from app.api.wazuh import router as wazuh_router
from app.services.analysis_history import initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Autonomous AI Cyber Defense Management API",
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(analysis_router)
app.include_router(wazuh_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "ai-defense-manager",
        "version": settings.app_version,
    }
''', encoding="utf-8")

print("API_HISTORY_INTEGRATION_WRITTEN")
PY
```

## 3.2 Checking the Syntax and Routes

```bash
cd /opt/ai-defense-manager && ./venv/bin/python -m py_compile app/main.py app/api/analysis.py app/api/wazuh.py app/services/analysis_history.py && runuser -u ai-defense -- ./venv/bin/python - <<'PY'
from app.main import app

for route in app.routes:
    methods = getattr(route, "methods", None)
    path = getattr(route, "path", None)
    if path:
        print(",".join(sorted(methods or [])), path)

print("API_IMPORT_CHECK_OK")
PY
```

As in Part 16, 3.3, `/api/v1/...` does not appear in this list (because FastAPI incorporates routers lazily). Check with the routers and OpenAPI.

```bash
cd /opt/ai-defense-manager && runuser -u ai-defense -- ./venv/bin/python - <<'PY'
from app.main import app
from app.api.analysis import router as analysis_router
from app.api.wazuh import router as wazuh_router

print("===== ANALYSIS ROUTER =====")
for route in analysis_router.routes:
    print(getattr(route, "path", None), getattr(route, "methods", None))

print("===== WAZUH ROUTER =====")
for route in wazuh_router.routes:
    print(getattr(route, "path", None), getattr(route, "methods", None))

print("===== OPENAPI PATHS =====")
for path, methods in app.openapi()["paths"].items():
    print(path, sorted(methods.keys()))

PY
```

It is normal if `/api/v1/analysis` (POST), `/api/v1/wazuh/events` (GET), `/api/v1/wazuh/analyze` (POST) and `/health` (GET) are all present.

## 3.3 Testing Saving After the Change

Using a temporary DB, confirm that `request_id` is saved and the initial approval state is `pending`.

```bash
cd /opt/ai-defense-manager && runuser -u ai-defense -- ./venv/bin/python - <<'PY'
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal, RecommendedAction
from app.schemas.security_event import SecurityEvent
import app.services.analysis_history as history

with tempfile.TemporaryDirectory() as tmp:
    history.DB_PATH = Path(tmp) / "test.db"
    history.initialize_database()

    event_id = uuid4()
    request = AIAnalysisRequest(
        events=[
            SecurityEvent(
                event_id=event_id,
                source="wazuh",
                observed_at=datetime.now(timezone.utc),
                severity="medium",
                rule_id="100001",
                event_category="authentication",
                event_summary="Test event",
            )
        ],
        requested_language="ja",
    )

    proposal = AIAnalysisProposal(
        summary="Test analysis",
        severity="medium",
        confidence=0.95,
        evidence_event_ids=[event_id],
        recommended_action=RecommendedAction.MONITOR,
        requires_human_approval=True,
        reasoning="Test only",
    )

    run_id = history.save_analysis(request, proposal)

    with sqlite3.connect(history.DB_PATH) as conn:
        row = conn.execute(
            "SELECT request_id, severity, evidence_count FROM analysis_runs WHERE run_id=?",
            (run_id,),
        ).fetchone()
        approval = conn.execute(
            "SELECT decision FROM action_approvals"
        ).fetchone()[0]

    assert row[0] == str(request.request_id)
    assert row[1:] == ("medium", 1)
    assert approval == "pending"

    print("REQUEST_ID_PERSISTENCE: OK")
    print("ANALYSIS_RECORD: OK")
    print("APPROVAL_DEFAULT:", approval)
    print("UPDATED_SCHEMA_TEST_OK")
PY
```

# Chapter 4: Allowing Writes in systemd

## 4.1 ReadWritePaths

The service from Part 17 has `ProtectSystem=strict` and cannot write to the file system.

```bash
systemctl cat ai-defense-manager.service | grep -E '^(User|Group|ProtectSystem|ReadWritePaths|ReadOnlyPaths|WorkingDirectory|ExecStart)='
```

Allow writes only to the `data` directory where the DB is stored. Other protection settings are not changed. Rather than rewriting the unit file itself, use an additional settings file (a drop-in).

```bash
install -d -o root -g root -m 755 /etc/systemd/system/ai-defense-manager.service.d && cat > /etc/systemd/system/ai-defense-manager.service.d/20-sqlite.conf <<'EOF'
[Service]
ReadWritePaths=/opt/ai-defense-manager/data
EOF
chmod 644 /etc/systemd/system/ai-defense-manager.service.d/20-sqlite.conf && cat /etc/systemd/system/ai-defense-manager.service.d/20-sqlite.conf
```

```bash
systemd-analyze verify ai-defense-manager.service && systemctl daemon-reload && systemctl show ai-defense-manager.service -p ProtectSystem -p ReadWritePaths -p User -p Group
```

It has succeeded if `ReadWritePaths=/opt/ai-defense-manager/data` is in effect while `ProtectSystem=strict` remains.

## 4.2 Permissions of the Storage Location

```bash
stat -c '%A %a %U:%G %n' /opt/ai-defense-manager/data
```

```bash
runuser -u ai-defense -- test -w /opt/ai-defense-manager/data && echo "SQLITE_DATA_WRITABLE: OK" || echo "SQLITE_DATA_WRITABLE: NG"
```

# Chapter 5: Creating the Production DB

## 5.1 Initialization

```bash
cd /opt/ai-defense-manager && runuser -u ai-defense -- ./venv/bin/python -c 'from app.services.analysis_history import initialize_database; initialize_database(); print("SQLITE_INITIALIZATION: OK")'
```

```bash
stat -c '%A %a %U:%G %s bytes %n' /opt/ai-defense-manager/data/ai-defense.db && cd /opt/ai-defense-manager && runuser -u ai-defense -- ./venv/bin/python -c 'import sqlite3; p="/opt/ai-defense-manager/data/ai-defense.db"; c=sqlite3.connect(p); print("JOURNAL_MODE:", c.execute("PRAGMA journal_mode").fetchone()[0]); print("TABLES:", ", ".join(r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type=\"table\" ORDER BY name"))); c.close()'
```

It has succeeded if `JOURNAL_MODE: wal` and the five tables are shown.

## 5.2 DB File Permissions

At build time the DB file was created with `644`. The directory is `750`, so other users cannot enter it, but it will contain analysis and audit records, so make it `600` (owner only).

```bash
chmod 600 /opt/ai-defense-manager/data/ai-defense.db && stat -c '%A %a %U:%G %n' /opt/ai-defense-manager/data/ai-defense.db && ls -la /opt/ai-defense-manager/data/
```

The WAL and SHM files (`-wal`, `-shm`) may disappear when connections end. It is normal for them to be absent.

# Chapter 6: Applying It to the Service

## 6.1 Before the Restart

```bash
systemctl status ai-defense-manager.service --no-pager -l
```

```bash
curl -sS -i http://127.0.0.1:8000/health
```

The currently running process was started before the history function was added. A restart is needed to use the new code.

## 6.2 Restarting

During the restart, the API on `127.0.0.1:8000` stops briefly.

```bash
systemctl restart ai-defense-manager.service && systemctl status ai-defense-manager.service --no-pager -l
```

```bash
journalctl -u ai-defense-manager.service -n 30 --no-pager
```

It has succeeded if `Application startup complete` appears and there is no error in DB initialization.

```bash
curl -sS -i http://127.0.0.1:8000/health
```

```bash
curl -sS -i 'http://127.0.0.1:8000/api/v1/wazuh/events?limit=5&since_minutes=60'
```

## 6.3 Does Analysis Get Saved?

`POST /api/v1/wazuh/analyze` requires a JSON body (sending without a body gives `422`). Every field has a default value, so sending `{}` analyzes the last 60 minutes, up to 50 alerts, in Japanese.

```bash
sed -n '1,240p' /opt/ai-defense-manager/app/api/wazuh.py
```

```bash
cat /opt/ai-defense-manager/app/schemas/wazuh.py
```

```bash
curl -sS -i -X POST http://127.0.0.1:8000/api/v1/wazuh/analyze -H 'Content-Type: application/json' -d '{}'
```

At build time it returned `HTTP 200`, `severity: info`, `recommended_action: no_action`, with 8 evidence events.

Open the DB read-only and confirm that it was saved.

```bash
cd /opt/ai-defense-manager && runuser -u ai-defense -- ./venv/bin/python - <<'PY'
import sqlite3

db = "/opt/ai-defense-manager/data/ai-defense.db"
conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)

for table in ("analysis_runs", "analysis_evidence", "action_proposals", "action_approvals", "audit_logs"):
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count}")

row = conn.execute("""
    SELECT severity, recommended_action, evidence_count, status
    FROM analysis_runs
    ORDER BY created_at DESC
    LIMIT 1
""").fetchone()

print("LATEST_ANALYSIS:", row)
conn.close()
PY
```

The counts at build time were as follows, and the latest record was `('info', 'no_action', 8, 'completed')`.

| Table | Rows |
|---|---:|
| `analysis_runs` | 2 |
| `analysis_evidence` | 16 |
| `action_proposals` | 2 |
| `action_approvals` | 2 |
| `audit_logs` | 2 |

# Closing Notes

In Part 18, we made the results of AI analysis remain in SQLite.

| Item | State |
|---|---|
| DB | `/opt/ai-defense-manager/data/ai-defense.db` (`ai-defense`, `600`, WAL) |
| Tables | Five (analysis, evidence, proposals, approvals, audit) |
| systemd | `ProtectSystem=strict` kept; writes allowed only to `data` |
| Saving | Saved after the analysis succeeds; `503` on failure |

In the next part, we review what is saved in SQLite and what is sent to the LLM, so that no unnecessary information goes out.

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

⟦C0⟧

At build time the host and database name were not set.

## 1.2 Existing DBs and DB Code

⟦C1⟧

⟦C2⟧

At build time there was no SQLite file, no SQLAlchemy and no code that handles a DB (PostgreSQL existed only as setting fields).

## 1.3 Where to Store It

⟦C3⟧

`/opt/ai-defense-manager/data` is `ai-defense:ai-defense` with `750`. It belongs to the run-as user, so the DB goes here.

⟦C4⟧

⟦C5⟧

At build time this was SQLite 3.45.1 with `THREAD_SAFETY: 3`.

## 1.4 Checking Where to Build It In

⟦C6⟧

⟦C7⟧

⟦C8⟧

⟦C9⟧

⟦C10⟧

⟦C11⟧

The findings were as follows.

- `SecurityEvent.event_id` is an ID generated on VM 230 by `uuid4()`. It is not Wazuh's original event ID, and fetching the same alert again may give a different ID. So column names that could be mistaken for Wazuh's original ID are not used.
- `ai_analysis.py` only queries the AI and validates the JSON. DB processing is not mixed in there; saving is done in the API layer after the analysis succeeds.

# Chapter 2: A Service That Saves the History

## 2.1 Backup

Back up the files to be changed.

⟦C12⟧

## 2.2 analysis_history.py

Build DB initialization and saving of analysis results.

- All SQL uses placeholders (`?`)
- Writes to the five tables are combined into one transaction; if it fails partway, nothing is left
- If a proposal's evidence event IDs are not among the input events, nothing is saved
- For a `no_action` proposal, the approval is set to `not_required`

⟦C13⟧

⟦C14⟧

## 2.3 Closing Connections Reliably

A `sqlite3` connection is not closed by a `with` statement alone (`with` only commits or rolls back the transaction). Add `_connection()`, which always closes the connection, and remove the unused `import json`.

⟦C15⟧

⟦C16⟧

## 2.4 Testing with a Temporary DB

Without creating the production DB yet, check the following with a DB in a temporary directory.

1. The five tables are created
2. The analysis result, evidence events and approval state are saved
3. When saving fails partway (inserting the same event twice), no partial data remains

⟦C17⟧

It has succeeded if `SQLITE_HISTORY_TESTS_OK` is shown. The temporary DB is deleted automatically.

# Chapter 3: Building It into the API

## 3.1 Saving request_id Too

⟦C18⟧

`AIAnalysisRequest` has a `request_id`, so save it to identify resent requests. Writes to SQLite are done with `asyncio.to_thread()` so that FastAPI's processing is not blocked for long.

It is built into the API as follows.

- Save after the analysis succeeds
- If saving fails, return `503` (do not return an analysis result that could not be saved as a success)
- Initialize the DB at application startup (`lifespan`)

⟦C19⟧

## 3.2 Checking the Syntax and Routes

⟦C20⟧

As in Part 16, 3.3, `/api/v1/...` does not appear in this list (because FastAPI incorporates routers lazily). Check with the routers and OpenAPI.

⟦C21⟧

It is normal if `/api/v1/analysis` (POST), `/api/v1/wazuh/events` (GET), `/api/v1/wazuh/analyze` (POST) and `/health` (GET) are all present.

## 3.3 Testing Saving After the Change

Using a temporary DB, confirm that `request_id` is saved and the initial approval state is `pending`.

⟦C22⟧

# Chapter 4: Allowing Writes in systemd

## 4.1 ReadWritePaths

The service from Part 17 has `ProtectSystem=strict` and cannot write to the file system.

⟦C23⟧

Allow writes only to the `data` directory where the DB is stored. Other protection settings are not changed. Rather than rewriting the unit file itself, use an additional settings file (a drop-in).

⟦C24⟧

⟦C25⟧

It has succeeded if `ReadWritePaths=/opt/ai-defense-manager/data` is in effect while `ProtectSystem=strict` remains.

## 4.2 Permissions of the Storage Location

⟦C26⟧

⟦C27⟧

# Chapter 5: Creating the Production DB

## 5.1 Initialization

⟦C28⟧

⟦C29⟧

It has succeeded if `JOURNAL_MODE: wal` and the five tables are shown.

## 5.2 DB File Permissions

At build time the DB file was created with `644`. The directory is `750`, so other users cannot enter it, but it will contain analysis and audit records, so make it `600` (owner only).

⟦C30⟧

The WAL and SHM files (`-wal`, `-shm`) may disappear when connections end. It is normal for them to be absent.

# Chapter 6: Applying It to the Service

## 6.1 Before the Restart

⟦C31⟧

⟦C32⟧

The currently running process was started before the history function was added. A restart is needed to use the new code.

## 6.2 Restarting

During the restart, the API on `127.0.0.1:8000` stops briefly.

⟦C33⟧

⟦C34⟧

It has succeeded if `Application startup complete` appears and there is no error in DB initialization.

⟦C35⟧

⟦C36⟧

## 6.3 Does Analysis Get Saved?

`POST /api/v1/wazuh/analyze` requires a JSON body (sending without a body gives `422`). Every field has a default value, so sending `{}` analyzes the last 60 minutes, up to 50 alerts, in Japanese.

⟦C37⟧

⟦C38⟧

⟦C39⟧

At build time it returned `HTTP 200`, `severity: info`, `recommended_action: no_action`, with 8 evidence events.

Open the DB read-only and confirm that it was saved.

⟦C40⟧

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

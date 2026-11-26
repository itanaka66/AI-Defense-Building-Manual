---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 57: Building Token Authentication for the API"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 57 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". Following the design decided in Part 56, we build token authentication for the AI Defense Manager API and test it in an independent environment that does not use the production DB.

| Target | Details |
|---|---|
| Storage | add a dedicated authentication table `api_tokens` to the existing `ai-defense.db`; store only the SHA-256 hash of tokens, never plaintext |
| Tokens | generated with a cryptographic random number equivalent to 256 bits |
| Issuing | a root-only CLI (`/usr/local/sbin/aidm-api-token`) issues, revokes and lists. The plaintext token is written once to a root-only file (`600`) and never shown on screen or in logs |
| Privileges (scopes) | `read` (fetching Wazuh events), `analyze` (analysis) |
| Not authenticated | `/health` |
| Disabled | `/docs`, `/redoc`, `/openapi.json` |
| Service | stays as `ai-defense`, reads hashes from the DB |

The existing tables and data for analysis history, evidence, approvals and audit logs, and the Relay credentials, are not changed. In this part there is no service restart, no production token issuance, no Wazuh retrieval and no Ollama inference.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: Checks and Copies Before the Change

## 1.1 Structure of the Existing DB

> **Run on: VM 230**

⟦C0⟧

## 1.2 Copying the Application and the DB

SQLite is copied with its dedicated Backup API, without writing to the original DB.

> **Run on: VM 230**

⟦C1⟧

SQLite `integrity_check` was `ok`, there are six existing tables, and the SHA-256 comparison of the copied files succeeded.

## 1.3 Where to Integrate, and Settings

> **Run on: VM 230**

⟦C2⟧

The service account `ai-defense` can read and write the DB but only read the application sources. We keep this separation. Verification looks up the DB record by the token ID and compares the hash of the secret part with `hmac.compare_digest()`.

> **Run on: VM 230**

⟦C3⟧

Python's standard library and FastAPI's test features are all present, so no packages need to be added.

# Chapter 2: Building the Authentication

The existing files were copied in Chapter 1. At this point the authentication table is not created yet.

> **Run on: VM 230**

⟦C4⟧

| Created | Details |
|---|---|
| `app/services/api_tokens.py` | issuing, verifying, revoking and listing tokens |
| `app/core/api_auth.py` | `require_scope()` (a FastAPI dependency) |
| `app/cli/api_tokens.py` | root-only CLI |
| `/usr/local/sbin/aidm-api-token` | wrapper that runs the CLI (`root:root`, `700`) |
| `app/main.py`, routers | require scopes on the three APIs and disable documentation |

The Python syntax check, the systemd unit check and displaying the CLI help all passed.

# Chapter 3: Testing in an Independent Environment

## 3.1 Testing the Authentication Logic

The test DB is created in a temporary directory and deleted afterwards. There is no connection to the production DB, Wazuh or Ollama.

> **Run on: VM 230**

⟦C5⟧

Issuing tokens, storing as hashes, rejecting invalid/expired/revoked tokens, and rejecting insufficient scopes all passed.

The scope check of the three routes showed `FAIL`, but this was a problem in the test code (3.2).

## 3.2 Checking Route Registration

> **Run on: VM 230**

⟦C6⟧

In the source, `Depends(require_scope(...))` was written on all three routes.

> **Run on: VM 230**

⟦C7⟧

In FastAPI 0.165.0, routers registered with `include_router()` are expanded later as `_IncludedRouter`. The test code walked `app.routes` directly and so could not find the three API routes. We check again with the expanded routes.

> **Run on: VM 230**

⟦C8⟧

| API | Required scope | Result |
|---|---|---|
| `GET /api/v1/wazuh/events` | `read` | passed |
| `POST /api/v1/analysis` | `analyze` | passed |
| `POST /api/v1/wazuh/analyze` | `analyze` | passed |
| `GET /health` | none | passed |

## 3.3 Testing Authentication over HTTP

> **Run on: VM 230**

⟦C9⟧

`401` without a token, `403` rejecting the analysis API with a `read` token, and `/health` without authentication passed. The rest were problems with the test's expected values, which we checked as follows.

> **Run on: VM 230**

⟦C10⟧

- `GET /events` with an `analyze` token gives `403` (the token is valid but lacks `read`); as specified
- `POST /analysis` gives `422` (authentication passed; the required `events` in the body is missing)
- `POST /wazuh/analyze` gives `502`. Even with an empty body `{}`, `limit=50` and `since_minutes=60` are filled in automatically, so after authentication it went on to actual retrieval and analysis

> **Run on: VM 230**

⟦C11⟧

So we switch to tests that fully simulate Wazuh retrieval and Ollama.

## 3.4 Testing the Wazuh APIs

`fetch_wazuh_events` is replaced with a function that returns an empty array, so it does not proceed to AI analysis, storing history or outside communication.

> **Run on: VM 230**

⟦C12⟧

GET gave `200` with a `read` token and `403` with an `analyze` token; POST gave `401` without a token. The test that omitted the POST body gave `422` (even with defaults, the body itself is required). We retest with a body.

> **Run on: VM 230**

⟦C13⟧

| Test | Result |
|---|---:|
| GET with a `read` token | 200 |
| GET with an `analyze` token | 403 |
| POST with an `analyze` token | 404 (response for the simulated empty events) |
| POST with a `read` token | 403 |
| POST without a token | 401 |
| Times the simulated retrieval function was called | 1 |

For requests rejected by authentication, the Wazuh retrieval function was not called.

## 3.5 Testing the Analysis API

Using a test event with `source="internal"`, the analysis result is simulated to return a fixed `no_action` proposal, and storing history is also simulated.

> **Run on: VM 230**

⟦C14⟧

| Test | Result |
|---|---:|
| `analyze` token | 200 |
| `read` token | 403 |
| No token | 401 |
| Analysis and storing history (simulated) | once, only when authentication passed |

# Closing Notes

In Part 57 we built token authentication for the API and checked it in an independent environment.

| Item | Result |
|---|---|
| Authentication | Bearer tokens, scopes `read` and `analyze`, stored as SHA-256 hashes, verified with `hmac.compare_digest` |
| CLI | `/usr/local/sbin/aidm-api-token` (root only) issues, revokes and lists |
| Documentation | `/docs`, `/redoc` and `/openapi.json` disabled |
| Tests | for all three APIs: `401` without a token, `403` for insufficient privilege, passes with the correct scope |
| Production | not yet deployed (no authentication table; service not restarted) |

In the next part, Part 58, we examine the CLI and token handling in detail, harden them, and do a final check before production.

---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 59: Putting API Authentication into Production"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 59 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". We put into production the API token authentication built and tested in Parts 57 and 58.

1. Create the table that manages tokens in the production SQLite
2. Issue one client token and check that the file and the DB agree
3. Restart the service to enable authentication
4. In production, check the order of authentication, authentication of the Wazuh retrieval API, that nothing leaks into logs, and that the last-used time is updated

For the production tests, we use requests that always stop at input validation, so that no AI analysis, storing of history or communication with Wazuh or Ollama occurs.

> **Caution:** Do not display, paste or hand over the contents of the token to anyone.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: Creating the Table in the Production DB

We create only the `api_tokens` table and an index on the expiry. Existing tables and data are not changed.

> **Run on: VM 230**

⟦C0⟧

`api_tokens` (8 columns) and `idx_api_tokens_expires_at` were created, with `SCHEMA_VERIFICATION=PASS`.

# Chapter 2: Issuing a Token

## 2.1 CLI Arguments and the Destination

Following the principle of least privilege, give only the scopes the use requires. Here we gave both `read` and `analyze`.

> **Run on: VM 230**

⟦C1⟧

## 2.2 Issuing

| Item | Value |
|---|---|
| Name | `ai-defense-client` |
| Scopes | `read,analyze` |
| Expiry | 30 days |
| Destination | `/root/ai-defense-client.token` (`600`) |

> **Run on: VM 230**

⟦C2⟧

The token file was created with owner `root`, `600`, 77 bytes. The token contents were not displayed.

## 2.3 Checking the Issued Token

The display of the issuance result was garbled (`TOKEN_ISSUED=YESE_LOGGED=NO"`), so without reissuing we check the DB registration, scopes and hash match read-only.

> **Run on: VM 230**

⟦C3⟧

| Checked | Result |
|---|---|
| File owner and permissions | passed (`root:root`, `600`) |
| Token format | passed |
| Registered in SQLite | passed |
| SHA-256 match between file and DB | passed |
| Scopes | passed (`read`, `analyze`) |
| Expiry | passed |
| Token value not shown | passed |

# Chapter 3: Deploying to the Service

## 3.1 Checks Before the Restart

> **Run on: VM 230**

⟦C4⟧

The service was `active (running)`, listening only on `127.0.0.1:8000`; the Python syntax passed; authentication on the three API routes had been confirmed; OpenAPI, Swagger and ReDoc were disabled; and the token file was root-only `600`.

## 3.2 Restart

> **Run on: VM 230**

⟦C5⟧

Right after the restart, listening on `127.0.0.1:8000` was not visible and `/health` gave `HTTP_STATUS=000`. Without restarting again, we check the state (strings that look like tokens in the log are masked).

> **Run on: VM 230**

⟦C6⟧

| Item | Result |
|---|---|
| systemd | `active (running)` (MainPID `2203`, 0 restarts) |
| Uvicorn and application startup | normal, complete |
| Listening | `127.0.0.1:8000` |
| `/health` | `HTTP 200` |

The earlier `000` was because the check came right after startup.

# Chapter 4: Checking Authentication in Production

## 4.1 Input Shape of the Analysis API

> **Run on: VM 230**

⟦C7⟧

⟦C8⟧

After authentication, the analysis API calls `analyze_events()` and then stores history. `events` requires at least one item, so sending `{"events":[]}`, which is valid JSON with an empty `events`, always stops at input validation and does not proceed to analysis.

> **Note:** Sending invalid JSON (such as just `{`) may make FastAPI return a body parsing error (`422`) before authentication, which does not test authentication.

## 4.2 Order of Authentication

> **Run on: VM 230**

⟦C9⟧

| Test | HTTP | Verdict |
|---|---:|---|
| No token | 401 | passed |
| Valid token + invalid input | 422 | passed (rejected at input validation after passing authentication) |
| `/health` | 200 | passed |

## 4.3 The Wazuh Retrieval API

To avoid connecting to production Wazuh, we send only requests without credentials or with an invalid token.

> **Run on: VM 230**

⟦C10⟧

| Test | HTTP | Verdict |
|---|---:|---|
| No token | 401 | passed |
| Invalid Bearer token | 401 | passed |
| `/health` | 200 | passed |

No communication with Wazuh occurred. For `403` (insufficient privilege) we rely on the results of the independent tests in Part 57 and do not add a test token to the production DB.

## 4.4 Does Information Leak?

> **Run on: VM 230**

⟦C11⟧

| Item | Verdict |
|---|---|
| Bearer tokens not written to logs | passed (no logger or print in the authentication logic) |
| SHA-256 comparison | passed (`hmac.compare_digest()`) |
| Expiry and revocation checks | passed |
| Insufficient scope | passed (`403`) |
| `last_used_at` | passed (updated only when authentication succeeds) |
| API exception responses | passed (return fixed messages) |

> **Run on: VM 230**

⟦C12⟧

An invalid token gave `401`, and the journal recorded only the source, path and status; the token value did not appear.

## 4.5 Last-Used Time

Without showing the production token on screen or in arguments, we send one authenticated POST. With `events: []` it gives `422`, so no analysis, storing of history or connection to Wazuh occurs.

> **Run on: VM 230**

⟦C13⟧

We confirmed that `last_used_at` in the production SQLite was updated when authentication succeeded.

# Closing Notes

In Part 59 we put API token authentication into production.

| Item | Result |
|---|---|
| Production DB | created `api_tokens` and the expiry index |
| Token | issued `ai-defense-client` (`read,analyze`, 30 days); `/root/ai-defense-client.token` (`600`) |
| Service | restarted; authentication enabled (`/health` without authentication) |
| Production tests | no token and invalid tokens give `401`, a valid token passes authentication, tokens do not appear in logs, `last_used_at` is updated |
| Documentation | `/docs`, `/redoc` and `/openapi.json` disabled |

> **Operational note:** Tokens expire after 30 days. Before expiry, issue a new token with `aidm-api-token` and revoke the old one with `revoke` (see the Operations Manual).

In the next part, Part 60, we check whether information leaks from API error responses and logs.

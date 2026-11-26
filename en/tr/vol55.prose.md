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

⟦C0⟧

We confirmed that masking is used on each path, and that even if the LLM returns `requires_human_approval=false`, the server side overrides it so that approval is required, both when returning analysis results and when storing in the DB. There is no automatic execution; it goes only as far as storing proposals.

## 1.2 Schemas and Masking

> **Run on: VM 230**

⟦C1⟧

Wazuh events are masked at conversion, the AI input is built from an allowlist, and `SecurityEvent` and analysis requests reject unknown fields. There are no test files, and the masking looks for common patterns, so there is no guarantee it can remove secrets in unknown forms.

# Chapter 2: Tests Without Outside Communication

## 2.1 Safety Boundary Tests (25 Cases)

No outside communication, DB writes or file changes.

> **Run on: VM 230**

⟦C2⟧

All 25 passed. We confirmed removal of extra fields in Wazuh events, masking of secrets, the LLM input allowlist, and rejection of invalid events and dangerous blocking proposals.

## 2.2 Analysis Tests (Simulated Ollama Answers, 9 Cases)

We test `analyze_events()` with simulated Ollama answers.

> **Run on: VM 230**

⟦C3⟧

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

⟦C4⟧

The API listens only on `127.0.0.1:8000`, runs as `ai-defense`, with `NoNewPrivileges=yes` and `ProtectSystem=strict`, but there was no authentication, authorization or CORS middleware within the application.

## 3.2 Documentation and Routes

> **Run on: VM 230**

⟦C5⟧

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

⟦C6⟧

⟦C7⟧

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

⟦C8⟧

⟦C9⟧

The waiting for AI analysis is placed at the entry of the existing analysis function, so there is only one concurrent request to Ollama. The body limit applies to the whole application. Uvicorn settings are overridden with a dedicated drop-in rather than rewriting the systemd unit itself (easy to save, compare and revert).

## 4.2 Applying the Patch

After making copies, we change the code and the systemd settings. The service is not restarted yet.

> **Run on: VM 230**

⟦C10⟧

The SHA256 comparison of the copies of the four files, the Python syntax check and the systemd settings check all passed. The copies are in `/var/backups/ai-defense-manager/dos-protection-20261123-205302`.

## 4.3 Independent Tests (8 Cases)

Without actual communication or Ollama, we test by calling the ASGI middleware and the semaphore directly.

> **Run on: VM 230**

⟦C11⟧

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

⟦C12⟧

## 4.5 Restarting

> **Run on: VM 230**

⟦C13⟧

The restart finished normally, and Uvicorn's new startup arguments included 8 concurrent connections, a backlog of 32 and Keep-Alive 5 seconds. The check right after (9 milliseconds after startup) showed port 8000 not yet listening, and `/health` gave `HTTP 000`.

> **Run on: VM 230**

⟦C14⟧

Uvicorn was PID `1681`, `active`, listening on `127.0.0.1:8000`, `/health` gave `HTTP 200`, and completion of application startup was also confirmed.

## 4.6 Testing the Body Limit on the Running Server

Without connecting to Ollama, Wazuh or the DB, we send requests to a test URL that does not exist.

> **Run on: VM 230**

⟦C15⟧

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

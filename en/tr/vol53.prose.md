---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 53: Checking the Flow from Analysis to Storage"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 53 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 52, VM 230 became able to receive real Wazuh alerts. Before moving on to LLM analysis, we check, read-only, how received alerts lead to analysis, storage and defense proposals inside VM 230.

1. Trace the processing from event conversion to AI analysis
2. Check the path from the API to storage and defensive action proposals, external exposure and DB permissions
3. Check systemd isolation settings
4. Test the masking step with synthetic data
5. Check the safety of where LLM output is stored and returned

No refetching of real alerts, no DB access, no Ollama inference, no configuration changes and no service restarts.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: The Processing Flow

## 1.1 Functions and Call Relationships

> **Run on: VM 230**

⟦C0⟧

There was no separate `event_service.py`; processing happened mainly in two stages.

1. `_convert_alert()` in `wazuh_relay.py` converts received alerts into `SecurityEvent`
2. `analyze_events()` in `ai_analysis.py` builds the content used for analysis and validates the model's output against the schema

## 1.2 Reading the Implementation

> **Run on: VM 230**

⟦C1⟧

- `SecurityEvent` is built from Wazuh's seven fields; fields not allowed are rejected by `extra="forbid"`
- What is passed to the AI is only six explicitly chosen fields
- Event summaries are masked before being sent to the AI and before being stored in history
- AI proposals are validated with Pydantic, including that the evidence event IDs are among the inputs
- A proposal for temporary blocking requires a global IP, a TTL of 1–900 seconds and two separate pieces of evidence

# Chapter 2: APIs, Storage and Exposure

## 2.1 From the API to Analysis and Storage

> **Run on: VM 230**

⟦C2⟧

| API | Processing |
|---|---|
| `/api/v1/wazuh/events` | only fetches Wazuh events |
| `/api/v1/wazuh/analyze` | passes fetched events to AI analysis |
| `/api/v1/analysis` | analyzes received events directly with the AI |

The DB is initialized when the application starts. `save_analysis()` stores the analysis results, evidence, action proposals, approval records and audit logs.

## 2.2 Routes and the Boundary of Action Execution

> **Run on: VM 230**

⟦C3⟧

Both analysis APIs called `save_analysis()`. On the other hand, we found the following two things.

1. **API authentication**: FastAPI routes have no authentication dependencies or middleware
2. **Action execution**: it goes only as far as recording approval state in the DB; there is no Action Gateway, no approval API and no firewall operation

## 2.3 External Exposure and DB Permissions

> **Run on: VM 230**

⟦C4⟧

| Item | Result |
|---|---|
| API listening | `127.0.0.1:8000` only (not exposed on the LAN) |
| Running as | dedicated user `ai-defense` |
| SQLite DB | `ai-defense:ai-defense`, `600` |
| DB directory | `750` |

The lack of API authentication remains. Even with localhost only, other processes on the same VM can access it, so authentication must be considered before integrating with other systems (done from Part 56 onward).

## 2.4 Approval State and Storage

> **Run on: VM 230**

⟦C5⟧

Analysis results are stored inside a transaction, and there was no API for executing actions or firewall operation in the code.

# Chapter 3: Isolation by systemd

> **Run on: VM 230**

⟦C6⟧

| Setting | State |
|---|---|
| `ProtectSystem=strict`, `ProtectHome=yes` | present |
| Writable locations | only the DB's `/opt/ai-defense-manager/data` |
| Linux capabilities | empty |
| `NoNewPrivileges=yes` | present |
| `PrivateTmp`, `PrivateDevices`, `ProtectProc=invisible` | present |
| Memory and task limits | 1GiB, 64 |
| `RestrictAddressFamilies` | `AF_INET` (IPv4 only) |

The AI Defense Manager has no root privileges and no network administration capability. With only `AF_INET`, IPv6 sockets cannot be used, but the current connections to the Relay and Ollama are IPv4.

# Chapter 4: Testing the Masking Step

## 4.1 Checking Input and Output Safety

> **Run on: VM 230**

⟦C7⟧

The event input side was as follows.

- Event summaries are masked before being sent to the LLM (Bearer tokens, common secrets, email addresses, IP addresses)
- What is passed to the LLM is built from an allowlist
- IPs and agent names of Wazuh events are not sent to the LLM
- The LLM's answer is validated with JSON Schema and Pydantic

On the other hand, we found that the LLM output side needs measures (Chapter 5).

## 4.2 Model and Settings

> **Run on: VM 230**

⟦C8⟧

The model name is written in `ai_analysis.py` as `qwen3:8b`, and there was no setting for it in `config.py`. Ollama's endpoint is `192.168.0.180:11434`. We do not change these here.

## 4.3 Testing with Synthetic Data (14 Cases)

Without changing the production code, we test with synthetic data the masking of secrets, email and IPv4/IPv6, control characters, the 512-character limit, and that ordinary text remains.

> **Run on: VM 230**

⟦C9⟧

All 14 passed.

## 4.4 Do the Original Values Remain? (10 Cases)

> **Run on: VM 230**

⟦C10⟧

All 10 passed; we confirmed that mask markers appear and the original secrets do not remain. It only works on known patterns, so it cannot necessarily remove secrets in unknown forms.

# Chapter 5: Checking the LLM Output

## 5.1 Processing Just Before Storage

> **Run on: VM 230**

⟦C11⟧

Two problems were found.

1. **LLM output is stored as is**: `proposal.summary` and `proposal.reasoning` are stored in SQLite without masking, even if they contain secrets
2. **The LLM can decide whether approval is required**: for proposals other than IP blocking, `requires_human_approval=false` passes, and the storage step uses that value

There is currently neither an Action Gateway nor an execution function, so this does not immediately lead to firewall operations.

## 5.2 API Return Values and Approval

> **Run on: VM 230**

⟦C12⟧

⟦C13⟧

The routers were actually in `app/api/analysis.py` and `app/api/wazuh.py`.

## 5.3 Handler Bodies

> **Run on: VM 230**

⟦C14⟧

- `/api/v1/analysis`: stores the LLM's proposal and then returns it as is
- `/api/v1/wazuh/analyze`: fetches Wazuh events, analyzes them with the LLM, stores, and returns the same proposal
- Both have `response_model=AIAnalysisProposal`, but that schema only checks lengths and types and does not remove secrets

So the proposal must be masked **right after receiving the LLM's answer**, not just right before storage.

## 5.4 Checks to Decide the Fix

> **Run on: VM 230**

⟦C15⟧

| Problem | Details |
|---|---|
| Masking of LLM output | `summary` (up to 2,000 characters) and `reasoning` (up to 4,000 characters) are stored and returned unmasked. The current masking is for event input and truncates to 512 characters, so it cannot be used as is |
| Whether approval is required | the LLM can return `requires_human_approval=false` |

With the policy that the LLM is limited to analysis and the AI Defense Manager side guarantees output safety and approval decisions, we fix this in the next part, Part 54.

# Closing Notes

In Part 53 we checked the flow from analysis to storage inside VM 230.

| Item | Result |
|---|---|
| Input | narrowed to seven fields, unknown fields rejected; summaries masked; six fields sent to the AI |
| Exposure | `127.0.0.1:8000` only; DB is `600` |
| Isolation | systemd restricts writable locations, capabilities, memory and more |
| Masking tests | all 14 and 10 cases passed |
| Problems found | LLM output stored and returned unmasked; the LLM can decide whether approval is required; the API has no authentication |
| Action execution | no such function (only storing proposals) |

In the next part, Part 54, we fix the masking of LLM output and the approval policy.

---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 70: Starting to Build the AI Defense Agents"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 70 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". By Part 69 we had put in order the Wazuh defense foundation and the protection of the AI Defense Manager's (VM 230) input, output, authentication and logs. From here, we build **AI defense agents** on top of it.

In this part we build the first two agents.

| Agent | Role |
|---|---|
| `LogAnalysisAgent` | log analysis. A thin, read-only layer that delegates to the existing AI analysis (`analyze_events()`) |
| `ThreatAnalysisAgent` | threat analysis and evidence validation. Independently checks the log analysis result for duplicate, missing or inconsistent evidence event IDs relative to the input |

The principles decided are as follows.

1. Agents only read and analyze; they do not execute defensive actions
2. Even if they can propose `TEMPORARY_BLOCK_IP`, they do not actually block. Defensive actions follow the existing `ActionProposal` constraints (approval required, start in `PENDING`)
3. Existing APIs, DB, settings and services are not changed. Tests use simulated analysis and make no communication with Ollama or DB access
4. Existing files are not overwritten

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root. When logged in as `aidefense`, become root with `sudo -i`)

# Chapter 1: Examining the Existing Structure

## 1.1 Service and Application

> **Run on: VM 230**

⟦C0⟧

The API runs on `127.0.0.1:8000` (Main PID `2340`, NRestarts 0), and the working directory is `/opt/ai-defense-manager`.

> **Run on: VM 230**

⟦C1⟧

`/opt/ai-defense-manager/app` and `tests` are owned by root and cannot be read by `aidefense` (a structure that protects the application code). We keep this protection.

## 1.2 Source Listing and AI Analysis Structure

> **Run on: VM 230**

⟦C2⟧

⟦C3⟧

| Existing | Role |
|---|---|
| `app/services/ai_analysis.py` | AI analysis engine |
| `app/services/wazuh_relay.py` | fetching Wazuh events |
| `app/services/event_sanitizer.py` | masking events |
| `app/services/analysis_history.py` | storing analysis history |
| `app/agents`, `app/policies` | directories only, no Python files |

## 1.3 Input/Output Types and Validation

> **Run on: VM 230**

⟦C4⟧

⟦C5⟧

The first agents can use the existing `AIAnalysisRequest` and `AIAnalysisProposal` for input and output. `AIAnalysisProposal` has `confidence`, `evidence_event_ids`, `requires_human_approval` and others.

> **Run on: VM 230**

⟦C6⟧

- An IP blocking proposal requires two or more separate evidence events
- Only global IPs can be blocking targets
- `target_ip` and `ttl_seconds` are required
- Human approval is required
- Execution proposals start in `PENDING`

## 1.4 The Flow of Model Queries

> **Run on: VM 230**

⟦C7⟧

⟦C8⟧

Querying Ollama (`httpx.AsyncClient`), parsing the JSON answer and validating with `AIAnalysisProposal` are already done by `ai_analysis.py`. The first agent does not duplicate model calls; it uses the existing `analyze_events()`.

## 1.5 Test Environment

> **Run on: VM 230**

⟦C9⟧

Python 3.12.3, Pydantic 2.14.4, FastAPI 0.165.0; there is no `pytest`, so we use the standard `unittest`.

# Chapter 2: The Log Analysis Agent

## 2.1 Building and Testing

We create only two new files, `app/agents/log_analysis.py` and `tests/test_log_analysis_agent.py`, after checking that they do not exist yet.

> **Run on: VM 230**

⟦C10⟧

## 2.2 Fixing the Test Data

The test in 2.1 failed before the agent's processing because of mistakes in how the test data was built. Without changing the agent itself, we fix only the test file, in three steps.

1. Put one valid `SecurityEvent` into the required `events` of `AIAnalysisRequest`

> **Run on: VM 230**

⟦C11⟧

2. Fill in the required fields of `AIAnalysisProposal` (`summary`, `severity`, `confidence`, `evidence_event_ids`, `reasoning`)

> **Run on: VM 230**

⟦C12⟧

3. `evidence_event_ids` requires at least one item, so use the test event's `event_id` as the evidence ID

> **Run on: VM 230**

⟦C13⟧

Both `test_delegates_request_and_returns_proposal` and `test_propagates_analysis_error` were `OK`. There were no actual requests to Ollama, no DB reads and no service restarts.

## 2.3 Checking the Contents

> **Run on: VM 230**

⟦C14⟧

`LogAnalysisAgent` is a thin, read-only agent that delegates to the existing `analyze_events()`, with no functions for executing or approving defensive actions.

# Chapter 3: The Threat Analysis Agent

## 3.1 Design

> **Run on: VM 230**

⟦C15⟧

⟦C16⟧

The existing `AIAnalysisProposal` has severity, confidence, evidence event IDs and recommended actions, so we do not create a new schema. The two analysis APIs still call `analyze_events()` directly, and `LogAnalysisAgent` is not used by the APIs.

`ThreatAnalysisAgent` is given the role of independently checking the log analysis result, not merely rewrapping the AI's answer.

- Delegate analysis to `LogAnalysisAgent`
- For the returned proposal, check for duplicate evidence IDs, duplicate input event IDs, and evidence IDs not in the input
- Reject inconsistencies with a dedicated exception

## 3.2 Building and Testing

> **Run on: VM 230**

⟦C17⟧

| Test | Result |
|---|---|
| Accepts valid evidence IDs | passed |
| Delegates to the log analysis agent | passed |
| Rejects duplicate evidence IDs | passed |
| Rejects duplicate input event IDs | passed |
| Rejects evidence IDs not in the input | passed |

All 5 passed.

## 3.3 All Tests

> **Run on: VM 230**

⟦C18⟧

All 7 tests of the two agents passed, and within this scope no effect on each other or on existing functions was seen.

# Closing Notes

In Part 70 we built the first two AI defense agents.

| Agent | File | Tests |
|---|---|---|
| `LogAnalysisAgent` | `app/agents/log_analysis.py` | 2 passed |
| `ThreatAnalysisAgent` | `app/agents/threat_analysis.py` | 5 passed |

Both only read and analyze and do not execute defensive actions. They are not yet connected to the API, and the service has not been restarted. In the next part, Part 71, we move on to an event correlation agent, an agent that orchestrates the whole, and a defense decision policy agent.

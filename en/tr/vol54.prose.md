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

⟦C0⟧

The copies of all four files matched, and the original owners and permissions were recorded.

# Chapter 2: Adding LLM Output Masking and the Approval Policy

## 2.1 Rewriting the Four Files

Keeping the 512-character limit of the event masking, we add dedicated entry points for LLM output with 2,000 and 4,000 characters. We do not trust the LLM's value for whether approval is required; everything other than `no_action` always requires approval on the server side, and the same rule is applied again when storing in the DB.

> **Run on: VM 230**

⟦C1⟧

Writing the four files and the Python syntax check succeeded, and the owners and permissions were unchanged.

## 2.2 Functional Tests (10 Cases)

We do not connect to the real DB; we check with a fake DB for testing.

> **Run on: VM 230**

⟦C2⟧

**All 10 passed.**

- The 512-character limit on event summaries is unchanged
- The LLM's `summary` and `reasoning` are limited to 2,000 and 4,000 characters, and secrets are masked
- For anything other than `no_action`, approval is required on the server side even if the LLM returns `requires_human_approval=false`
- The same approval rule and masking are applied when storing in SQLite

## 2.3 Edges of the Approval Policy (5 Cases)

> **Run on: VM 230**

⟦C3⟧

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

⟦C4⟧

The two analysis APIs store the proposal returned by `analyze_events()` before returning it, so the masking and approval policy of Chapter 2 also apply to the responses. However, `GET /api/v1/wazuh/events` does not go through AI analysis and returns the result of `fetch_wazuh_events()` as is.

## 3.2 The Conversion in the Retrieval API

> **Run on: VM 230**

⟦C5⟧

`_convert_alert()` put Wazuh's `rule.description` into `event_summary` and `rule_description` as is. So `GET /api/v1/wazuh/events` could return unmasked strings.

## 3.3 Fixing

We fix only `wazuh_relay.py`, after making a copy, applying `sanitize_event_summary()` to both `event_summary` and `rule_description`. We check with synthetic data.

> **Run on: VM 230**

⟦C6⟧

The synthetic tests after the fix **all 9 passed**, confirming masking of secrets, email addresses and IP addresses and the 512-character limit.

# Chapter 4: Checking Permissions and Restarting

## 4.1 File Permissions

> **Run on: VM 230**

⟦C7⟧

The fixed `wazuh_relay.py` had become `root:root`, `640`, so the service user `ai-defense` could not read it. **It cannot be restarted in this state.**

## 4.2 Restoring the Group

Keeping owner `root` and mode `640`, we restore only the group to `ai-defense`.

> **Run on: VM 230**

⟦C8⟧

| Item | Result |
|---|---|
| Owner | `root` (unchanged) |
| Group | `ai-defense` (restored) |
| Mode | `640` (unchanged) |
| Read by the service user | passed |
| Source SHA256 | matches the value after the fix (contents not changed) |

## 4.3 Restarting

> **Run on: VM 230**

⟦C9⟧

The restart gave exit code `0`, but the check right after showed nothing listening on port 8000, and `/health` gave `HTTP 000`.

## 4.4 Checking the Startup

> **Run on: VM 230**

⟦C10⟧

systemd showed `active (running)`, Uvicorn showed `Application startup complete`, the PID was `1469`, and it was listening on `127.0.0.1:8000`. The earlier result was because the check came right after the restart.

> **Run on: VM 230**

⟦C11⟧

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

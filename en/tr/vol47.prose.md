---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 47: Examining the Existing AI Defense Manager Implementation"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 47 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 46 we decided on seven Wazuh alert fields to pass to the LLM. Here, to decide where to integrate that allowlist, we examine the existing implementation of the AI Defense Manager on VM 230, read-only.

1. Check VM 230's network and listening services
2. Examine the list of APIs and the input shapes (schemas)
3. Trace the module structure, the dependencies, and the data flow from Wazuh alerts to the LLM
4. Check the current conversion (fields, event IDs, severity, classification) and decide the target specification
5. Confirm that there are no tests and no Git, and decide the preparations before changing anything

Source bodies, SQL and secrets are not displayed. No files are changed, no services restarted and nothing is sent to the LLM.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: VM 230's Network and Services

## 1.1 Address and Listening Ports

> **Run on: VM 230**

⟦C0⟧

| Item | Result |
|---|---|
| IPv4 | `192.168.0.33/24` (`enp6s18`). At this point an address received by DHCP (fixed to `192.168.0.221` in a later part) |
| Gateway | `192.168.0.1` |
| SSH | `0.0.0.0:22` |
| Application | `127.0.0.1:8000` only |

Port 8000 listens only on the loopback address and is not set up for direct connection from VM 220. **Port 8000 is not exposed externally.**

## 1.2 The Service on Port 8000

> **Run on: VM 230**

⟦C1⟧

The FastAPI/Uvicorn `AI Defense Manager API` is started automatically by systemd and running, the project is in `/opt/ai-defense-manager`, and `/health` and `/openapi.json` returned `HTTP 200`. There is no need to add a new API server.

# Chapter 2: APIs and Input Shapes

## 2.1 List of APIs

> **Run on: VM 230**

⟦C2⟧

| API | Method | Purpose |
|---|---|---|
| `/api/v1/analysis` | POST | AI analysis |
| `/api/v1/wazuh/analyze` | POST | analysis of Wazuh events |
| `/api/v1/wazuh/events` | GET | retrieval of Wazuh events |
| `/health` | GET | status check |

APIs that integrate with Wazuh already exist. Rather than building a new entry point, we examine whether these fit the seven-field allowlist.

## 2.2 Input Shape

> **Run on: VM 230**

⟦C3⟧

The existing `SecurityEvent` has the following shape, which differs in both names and structure from the seven fields of Part 46.

- Required: `source`, `severity`, `event_category`, `event_summary`
- Optional: `event_id`, `observed_at`, `agent_id`, `agent_name`, `source_ip`, `destination_ip`, `rule_id`, `rule_description`

# Chapter 3: Modules and Data Flow

## 3.1 Source Layout

> **Run on: VM 230**

⟦C4⟧

The APIs are split into `api/analysis.py` and `api/wazuh.py`, the input shapes are in `schemas/`, and the analysis history is in `services/analysis_history.py`.

## 3.2 Internal Structure

Using Python's AST, we extract only the names of functions, classes, modules used and functions that access the DB.

> **Run on: VM 230**

⟦C5⟧

SQLite was used to store the analysis history.

## 3.3 Dependencies

> **Run on: VM 230**

⟦C6⟧

| Module | Role |
|---|---|
| `services/wazuh_relay.py` | retrieving and converting Wazuh alerts |
| `services/event_sanitizer.py` | masking event summaries, masking IP addresses |
| `services/ai_analysis.py` | AI analysis |
| `services/analysis_history.py` | SQLite analysis history |
| `schemas/action.py` | defensive action proposals, approval state, validation |
| `schemas/analysis_proposal.py` | AI analysis results and action constraints |

## 3.4 Masking, Retrieval and Analysis

> **Run on: VM 230**

⟦C7⟧

| Function | Current implementation | Assessment |
|---|---|---|
| Wazuh retrieval | `fetch_wazuh_events()` | use as is |
| Wazuh conversion | `_convert_alert()` | where the allowlist goes |
| IP address masking | `sanitize_event_summary()` | use as is |
| AI analysis | `analyze_events()` | use as is |
| AI output validation | Pydantic `model_validate()` | use as is |
| Action constraints | `validate_action` | an important foundation for safety |
| Approval management | `ApprovalStatus` | used for human approval |

The target flow is as follows.

⟦C8⟧

## 3.5 Tracing the Data Flow

> **Run on: VM 230**

⟦C9⟧

Raw Wazuh alerts are converted to `SecurityEvent` in `wazuh_relay.py`, then `ai_analysis.py` masks `event_summary` and sends it to the AI. Masking just before sending to the AI cannot guarantee that no extra fields slip in, so we use the following two stages.

1. Right after Wazuh retrieval: extract and check only the allowed fields
2. Right before sending to the AI: keep the current masking and check the input once more

# Chapter 4: The Current Conversion

## 4.1 Input and Output Fields

> **Run on: VM 230**

⟦C10⟧

Besides the seven fields, `_convert_alert()` also passed `agent_name` to `SecurityEvent`. What is sent to the AI is six fields: `event_id`, `observed_at`, `severity`, `rule_id`, `event_category` and `event_summary`. The raw Wazuh data is not sent wholesale, but this is not an input boundary limited to the seven fields.

| Wazuh field | Field inside VM 230 |
|---|---|
| `timestamp` | `observed_at` |
| `rule.id` | `rule_id` |
| `rule.level` | `severity` |
| `rule.groups` | `event_category` |
| `rule.description` | `rule_description` |
| `decoder.name` | not stored |
| `agent.id` | `agent_id` |

`agent_name`, IP addresses, `full_log`, `data`, `location` and `predecoder` are removed at the input boundary.

## 4.2 Event IDs

> **Run on: VM 230**

⟦C11⟧

- `SecurityEvent.event_id` is generated automatically with `uuid4`
- Wazuh's `rule.id` is kept as a separate field
- `evidence_event_ids` in AI proposals require UUIDs

**Do not use Wazuh rule IDs as event UUIDs.** Also, `ttl_seconds` in AI proposals has a maximum of 900 seconds, and `requires_human_approval` defaults to `True`. These constraints are kept.

## 4.3 How the Wazuh Fields Are Used

> **Run on: VM 230**

⟦C12⟧

`_convert_alert()` referred to `timestamp`, `rule.level`, `rule.id`, `rule.description`, `agent.id`, `agent.name`, `location` and `decoder.name`. It did not read `rule.groups` directly but went through a dictionary for classification.

## 4.4 Severity and Classification Mapping

> **Run on: VM 230**

⟦C13⟧

Kept as the current specification:

| Wazuh Level | Internal severity |
|---|---|
| 0–3 | info |
| 4–7 | low |
| 8–11 | medium |
| 12–14 | high |
| 15–16 | critical |

| Classification from Wazuh | Internal classification |
|---|---|
| pvedaemon | virtualization_management |
| pam | authentication |
| sshd | remote_access |
| useradd | account_management |
| open-userdel | account_management |

`rule.groups` has multiple values, so we classify only by allowed groups and do not let unknown values flow into the internal classification as is.

# Chapter 5: Preparing Before the Change

## 5.1 Tests and Version Control

> **Run on: VM 230**

⟦C14⟧

There were no test files and no Git repository. When the code is changed, it can neither be reverted with Git nor protected by existing tests. So our policy is to prepare the following new tests.

| Test | What it checks |
|---|---|
| Input allowlist | nothing beyond the seven fields is mixed in |
| Required fields | missing values, wrong types and invalid values are rejected |
| Removing secrets | `full_log`, `data`, IPs, user names and so on are not sent to the AI |
| Severity mapping | the boundaries of 0–16 |
| Classification mapping | the current five classifications and unknown classifications |
| UUID | correspondence between event IDs and evidence IDs |
| What is sent to the AI | inspect the JSON to be sent without actually communicating |
| Action safety | keep the 900-second TTL limit and the approval requirement |

## 5.2 Free Space and Target Files

> **Run on: VM 230**

⟦C15⟧

| Item | Result |
|---|---|
| Free space on VM 230 | about 39GB |
| Target files | 5 |
| SHA256 | taken for all 5 |
| Dedicated backup directory | not yet present |
| AI Defense Manager | `active` |
| Git | none |

# Closing Notes

In Part 47 we examined the existing implementation of the AI Defense Manager on VM 230.

| Item | Result |
|---|---|
| API | FastAPI/Uvicorn, `127.0.0.1:8000` only; APIs for Wazuh retrieval and analysis exist |
| Where the allowlist goes | `_convert_alert()` in `services/wazuh_relay.py` (right after retrieval) and right before sending to the AI in `services/ai_analysis.py` |
| Kept | the masking, `uuid4` event IDs, the severity mapping, the 900-second TTL, human approval |
| Preparation | no tests or Git, so take a backup before changing and check with independent tests |

In the next part, Part 48, we take a backup before the change, narrow the Wazuh event conversion to seven fields, and test it with synthetic data.

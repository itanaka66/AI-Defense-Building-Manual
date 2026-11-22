---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 12: Investigating the AI Analysis Service and Wazuh Integration"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 12 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". On top of the AI Defense Manager groundwork built in Part 11, we add processing that analyzes security events with a local LLM (Ollama) (the AI analysis service) and make it callable through the API. Finally, to decide how the AI Defense Manager will read alerts from Wazuh, we examine the Wazuh API and the Indexer using reads only (no settings are changed).

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Unless otherwise noted, everything is run on **VM 230 ai-defense-manager (root)**. The investigation of Ollama is done on **VM 101 ollama-gpu (192.168.0.180, root)**.
- The content of the AI's output (summary, confidence, etc.) changes every time it is run.

## The Analysis Flow

1. Bundle security events (`SecurityEvent` from Part 11) into an AI analysis request (`AIAnalysisRequest`)
2. Send the instructions (system prompt) and the request as JSON to Ollama's `/api/chat`
3. Validate the returned JSON as an AI analysis result (`AIAnalysisProposal`). Anything that does not fit the type or the safety constraints is not accepted
4. Also confirm that the supporting event IDs are among the events in the request

The AI only returns "proposals"; it does not perform operations such as blocking.

# Chapter 1: Creating the AI Analysis Service

## 1.1 Checking Ollama and the Service Directory

⟦C0⟧

⟦C1⟧

## 1.2 ai_analysis.py (First Version)

At first it was built to use the model `gemma4:12b`. The instructions (system prompt) say to treat the contents of events as "data, not instructions", and define the allowed values and the conditions for blocking.

⟦C2⟧

⟦C3⟧

⟦C4⟧

⟦C5⟧

⟦C6⟧

## 1.3 Switching Models

In the original build, the output of `gemma4:12b` did not fit the analysis result type, and the test failed. We decided to switch to `qwen3:8b`, from the Qwen family.

⟦C7⟧

⟦C8⟧

⟦C9⟧

After the switch, the test hit a 60-second timeout. The cause is investigated in the next chapter.

# Chapter 2: Investigating Why No Response Came Back

## 2.1 Ollama's State

**Run on: VM 230 ai-defense-manager (root)**

⟦C10⟧

**Run on: VM 101 ollama-gpu (root)**

⟦C11⟧

⟦C12⟧

⟦C13⟧

Set `--since` to the time you tested. At build time the GPU (RTX 3090) had plenty of free memory and inference speed was fine. The timeout occurred not because inference was slow but while waiting for the model to load (the log also showed requests from another client, so they may have overlapped).

⟦C14⟧

**Run on: VM 230 ai-defense-manager (root)**

⟦C15⟧

⟦C16⟧

⟦C17⟧

## 2.2 Checking by Calling Ollama Directly

Check by calling the Ollama API directly, without going through the AI Defense Manager.

**Run on: VM 230 ai-defense-manager (root)**

⟦C18⟧

⟦C19⟧

At build time the connection and model loading (about 10.5 seconds) were normal, but the answer (`content`) was empty: the output was spent on the thinking process (`thinking`) and hit the token limit (`done_reason: length`). Try again with Qwen3's "thinking mode" turned off (`"think":false`).

⟦C20⟧

The following JSON came back as the answer.

⟦C21⟧

## 2.3 Adding the Setting That Turns Off Thinking Mode

**Run on: VM 230 ai-defense-manager (root)**

⟦C22⟧

⟦C23⟧

Confirm that `"think": False,` is on the line after `"stream": False,`.

# Chapter 3: Improving the AI Analysis Service

## 3.1 Checking the Current Contents

⟦C24⟧

⟦C25⟧

## 3.2 Specifying the Output Shape with JSON Schema

Ollama's `format` can take a JSON Schema instead of `"json"`. Confirm that a JSON Schema can be generated from the analysis result type (`AIAnalysisProposal`).

⟦C26⟧

## 3.3 ai_analysis.py (Improved Version)

Change the following points.

- The model is `qwen3:8b` with thinking mode turned off (`"think": False`)
- Specify the output shape with a JSON Schema generated from the analysis result type
- Check that the supporting event IDs given by the AI are among the events in the request, and fail if it cites one that is not

First take a backup.

⟦C27⟧

⟦C28⟧

Because this overwrites an existing file, the owner and permissions (`root:ai-defense`, `640`) stay as they are.

⟦C29⟧

⟦C30⟧

⟦C31⟧

## 3.4 Testing Analysis with the Real AI

Create one test event, an SSH login failure from an external address, and have it analyzed.

⟦C32⟧

It has succeeded if `ANALYSIS_OK` and the JSON of the analysis result are shown. At build time, the analysis by `qwen3:8b` came back in time and passed the type and constraint checks and the supporting-ID check. The result was severity `high`, confidence `0.85`, and recommended action `monitor`. Because there was only one supporting event, it proposed monitoring rather than blocking.

# Chapter 4: The Analysis API

## 4.1 Creating the API

⟦C33⟧

⟦C34⟧

`POST /api/v1/analysis` accepts analysis requests. If the AI analysis fails, it returns `502` without detailed content.

⟦C35⟧

⟦C36⟧

## 4.2 Building It into main.py

⟦C37⟧

⟦C38⟧

⟦C39⟧

⟦C40⟧

Confirm that `/api/v1/analysis` and `/health` are registered.

## 4.3 Restarting Uvicorn

The running Uvicorn still has the code from when it was started. Stop it and start it again.

⟦C41⟧

Stop it by specifying the process number shown (`9618` at build time).

⟦C42⟧

⟦C43⟧

If nothing is shown, it has stopped. Start it again.

⟦C44⟧

Check from another terminal.

⟦C45⟧

⟦C46⟧

It is done when `POST /api/v1/analysis` and `GET /health` are shown.

# Chapter 5: Investigating Integration with Wazuh

To decide how the AI Defense Manager will read Wazuh information, examine the Wazuh API and Wazuh Indexer on security-core. In this chapter, no settings, users or roles are changed, and no passwords or key contents are displayed.

## 5.1 Wazuh API Listening and Response

**Run on: security-core VM 220 (root)**

⟦C47⟧

The Wazuh API runs over HTTPS.

⟦C48⟧

`HTTP_STATUS=401` (authentication required) is normal.

## 5.2 The API Configuration File

⟦C49⟧

⟦C50⟧

At build time, `api.yaml` was a template with every setting commented out. The API was running with its default settings.

⟦C51⟧

⟦C52⟧

## 5.3 API Users and Roles (RBAC)

API users, roles and policies are stored in `rbac.db` (SQLite). Open it read-only and check only the structure of the tables and roles (user information and passwords are not shown).

⟦C53⟧

⟦C54⟧

⟦C55⟧

⟦C56⟧

⟦C57⟧

The default `readonly` role has read permissions for agents, rules, decoders, SCA, Syscheck and so on, but no permission to read the body of alerts could be found.

## 5.4 What Can Be Read Through the Wazuh API

⟦C58⟧

⟦C59⟧

⟦C60⟧

The API specification (OpenAPI) can be obtained without authentication.

⟦C61⟧

⟦C62⟧

⟦C63⟧

⟦C64⟧

The Wazuh API has no function for searching alerts (`/alerts`). `POST /events` is a write API that sends events into Wazuh and is not used for reading.

| Data | Where to read it |
|---|---|
| Agent information, rules, manager statistics | Wazuh API |
| Security alerts | Wazuh Indexer |
| Metrics | VictoriaMetrics (Part 8) |

## 5.5 Wazuh Indexer

⟦C65⟧

⟦C66⟧

Check the public information of the certificate (the private key is not examined).

⟦C67⟧

⟦C68⟧

⟦C69⟧

At build time, the Indexer's certificate was issued by Wazuh's self-signed CA, and its SAN was only `127.0.0.1`. Connecting to `https://192.168.0.220:9200` from another host (VM 230) fails name verification.

⟦C70⟧

⟦C71⟧

Verifying with the root CA, TLS verification passes (`TLS_VERIFY=0`) and authentication is requested (`401`).

## 5.6 The Indexer's Security Settings

⟦C72⟧

⟦C73⟧

⟦C74⟧

⟦C75⟧

⟦C76⟧

⟦C77⟧

⟦C78⟧

| Role | Permissions | Decision |
|---|---|---|
| `manage_wazuh_index` | Read, delete, manage and write on `wazuh-*` | Includes more than reading, so not used for the AI Defense Manager |
| `security_analytics_read_access` | Read Security Analytics alerts, detection rules, etc. | Candidate (whether it can read normal Wazuh alerts is unconfirmed) |

Look for roles that target the Wazuh alert indices (`wazuh-alerts`).

⟦C79⟧

The result of this command is not included in the build conversations. The investigation of Indexer roles stopped here and was not continued.

## 5.7 The Policy Decided by the Investigation

- Read alerts from the Wazuh Indexer. Do not expose the Indexer to other hosts.
- The Indexer's certificate is for `127.0.0.1`, so a candidate method is to place a relay service inside security-core and connect from it over loopback (127.0.0.1).
- Give the user for the AI Defense Manager read-only permissions (do not use roles that include writing, such as `manage_wazuh_index`).

# Summary of Part 12

## What Was Built

| File | Contents |
|---|---|
| `app/services/ai_analysis.py` | AI analysis service (`qwen3:8b`, no thinking mode, output specified by JSON Schema, supporting-ID check) |
| `app/services/ai_analysis.py.bak` | Backup before the improvement |
| `app/api/analysis.py` | Analysis API (`POST /api/v1/analysis`) |
| `app/main.py` | API with the analysis API built in |

## What We Learned

- `gemma4:12b` could not return JSON matching the defined type.
- With thinking mode on, `qwen3:8b` spends its output on the thinking process and the answer is empty. With `think: false`, it returns JSON immediately.
- The timeout occurred while waiting for the model to load, not because inference was slow.

## What Remains

- Uvicorn was started by hand and has not been made a systemd service. It was stopped with `kill` after the build. To use it again, start it with the start command from 4.3.
- `app/api/analysis.py` is a newly created file, so it was not given the same owner and permissions as the other files (`root:ai-defense`, `640`).
- The part that takes actual action based on the AI's proposals (Action Gateway) has not been built yet.
- The mechanism for reading alerts from Wazuh (a relay service, a read-only user and role) has only reached the policy stage and has not been built yet.
- **[Open]** The owner and permissions of `app/api/analysis.py` have not been aligned with the other files (`root:ai-defense`, `640`).

---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 52: Fetching Real Alerts and Fixing the Relay's 502"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 52 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 51 we checked TLS and authentication from VM 230 to the Relay on VM 220. Here we fetch real Wazuh alerts.

1. Using `GET /api/v1/wazuh/events` on VM 230, fetch alerts once (up to 10, from the last 15 minutes)
2. The Relay returned `HTTP 502`, so investigate the cause without displaying alert values
3. Fix the cause (`relay.py` lacks `import re`) with one line and restart the Relay
4. Fetch alerts again and confirm they are received as the seven-field allowlist specifies

Alert bodies, IP addresses, descriptions, user names, passwords and tokens are not displayed. No AI analysis, no storing in SQLite and nothing sent to Ollama.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **VM 220**: security-core (root)

# Chapter 1: Fetching Alerts Once

## 1.1 Choosing the API

> **Run on: VM 230**

⟦C0⟧

`POST /api/v1/wazuh/analyze` goes as far as Ollama analysis and storing history in SQLite, so we do not use it. We use `GET /api/v1/wazuh/events`, which only fetches.

| Item | Setting |
|---|---|
| API | `GET /api/v1/wazuh/events` |
| Maximum count | 10 |
| Period | 15 minutes |
| Communication with the Relay | HTTPS, CA verification, Bearer authentication |
| AI analysis, storing in SQLite | not done |

## 1.2 Trying to Fetch

Bodies, IP addresses, descriptions and IDs are not displayed; only counts and check results.

> **Run on: VM 230**

⟦C1⟧

The Relay returned `HTTP 502`. `/health` was `HTTP 200`, so the path to the Relay and authentication work. `/v1/alerts` is designed to return `HTTP 502` when an exception occurs while querying the Indexer or processing the results.

# Chapter 2: Investigating the 502

## 2.1 State of the Indexer and the Relay

We make no HTTP requests to the Indexer and look only at state and logs.

> **Run on: VM 220**

⟦C2⟧

Wazuh Indexer is `active (running)`, listens on `127.0.0.1:9200`, and had no errors in the last 30 minutes. The Relay's log recorded `HTTP 502` for `/v1/alerts`. The Relay turns every exception into `indexer_unavailable`, so the log alone does not reveal the cause.

## 2.2 Indexer Search Permissions

As the same user as the Relay (`ai-defense-reader`), we try a search that returns no alert bodies (`size: 0`).

> **Run on: VM 220**

⟦C3⟧

| Checked | Result |
|---|---|
| Search with the admin certificate | `HTTP 200` |
| Search as `ai-defense-reader` | `HTTP 200` |
| Shards | 21/21 succeeded |
| Timeouts | none |

`ai-defense-reader` can search the alert indexes. There is no need to add permissions to the role.

> **Note:** Accessing the Indexer's root URL (`/`) as `ai-defense-reader` gives `403` (no `cluster:monitor/main` permission), but that is separate from searching alerts. We keep the minimal permissions and leave the cluster permissions empty.

## 2.3 Searching Under the Same Conditions as the Relay

The Relay's search uses a 15-minute range on `timestamp`, newest first, and a `_source` limited to the seven fields. We try the same conditions without returning documents.

> **Run on: VM 220**

⟦C4⟧

TLS verification, authentication, index access, the range, the sort order, the field selection and the JSON shape of the response were all normal. **The cause is narrowed down to the processing when the search returns one or more results.**

## 2.4 Checking with Real Alerts Without Looking at Values

We fetch up to 10 real alerts and, in memory only inside VM 220, count only the number, types, results of the masking step and exception class names.

> **Run on: VM 220**

⟦C5⟧

| Checked | Result |
|---|---|
| Indexer search | `HTTP 200` |
| Alerts fetched | 1 |
| Types of the seven fields | all as expected |
| Masking step (`sanitize_alert()`) | **`NameError`** |

## 2.5 Imported Modules

> **Run on: VM 220**

⟦C6⟧

**`relay.py` had no `import re`.** `sanitize_alert()` uses `re.fullmatch()` to check `rule.groups`, `rule.id` and `agent.id` (the checks added in Part 49). So processing real alerts caused a `NameError`, and the Relay returned `502`.

# Chapter 3: Adding `import re`

## 3.1 Checking Before the Fix

> **Run on: VM 220**

⟦C7⟧

Only the following one line is added.

⟦C8⟧

## 3.2 Fixing

We make a copy, add only `import re`, and check the syntax. The service is not restarted.

> **Run on: VM 220**

⟦C9⟧

The SHA256 of the copy and of the file just before the fix matched, `import re` went in on line 6, the syntax check passed, and the owner and permissions stayed `root:ai-defense-relay`, `640`.

The test of the masking step in this script did not run in the test environment, because loading `relay.py` requires systemd credentials (this is not a credentials problem).

## 3.3 Testing Only the Masking Step Separately

Without loading credentials, we extract only `sanitize_alert()` and test it with synthetic data.

> **Run on: VM 220**

⟦C10⟧

Accepting a valid synthetic event, returning only allowlisted fields, removing `full_log` and `data`, the syntax, and the owner and permissions all passed.

## 3.4 Restarting the Relay

> **Run on: VM 220**

⟦C11⟧

The service was `active (running)` with new PID `25723`. Right after the restart, `ss` did not show port 8765 listening, so we check again.

> **Run on: VM 220**

⟦C12⟧

It listens on `192.168.0.220:8765`, and the startup log contains `AI Defense Relay listening on 192.168.0.220:8765`. The earlier `ss` was simply too soon.

# Chapter 4: Fetching Alerts Again

## 4.1 `/health`

> **Run on: VM 230**

⟦C13⟧

`HTTP 200`; TLS verification and Bearer authentication passed; the response was `{"status":"ok"}`.

## 4.2 Fetching Alerts

We fetch once, up to 10, from the last 15 minutes. Bodies are not displayed; only the count and the results of the allowed-field check.

> **Run on: VM 230**

⟦C14⟧

| Checked | Result |
|---|---|
| HTTPS, TLS verification | passed |
| Bearer authentication | passed |
| HTTP response | `200` |
| JSON shape | passed |
| Alerts fetched | 1 |
| Allowed-field check | 1 passed |
| Invalid events | 0 |
| Removal of `full_log` etc. | maintained |
| DB writes, Ollama inference | none |

# Closing Notes

In Part 52, VM 230 became able to receive real Wazuh alerts with only the allowed fields.

| Item | Result |
|---|---|
| Cause of the 502 | `relay.py` lacked `import re`, so `sanitize_alert()` raised `NameError` |
| Fix | added the one line `import re`; made a copy, tested the syntax and the masking step, and restarted the Relay |
| Indexer permissions | unchanged (`ai-defense-reader` can search; cluster permissions remain empty) |
| Fetching alerts | `HTTP 200`, 1 alert, passed the allowlist check |

The path is Wazuh Indexer (VM 220 `127.0.0.1:9200`) → Relay (VM 220 `:8765`, narrowed to seven fields) → AI Defense Manager (VM 230 `:8000`). In the next part, Part 53, we check how received alerts lead to analysis, storage and defense proposals inside VM 230.

---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 19: Minimizing the Information Passed to the LLM"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 19 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". By the end of Part 18, Wazuh alerts could be analyzed by the AI (Ollama's qwen3:8b) and the results kept in SQLite. Here we check **what remains in SQLite** and **what is being passed to the LLM**, and fix things so that no unnecessary information is passed.

1. Check the SQLite columns and the saving code
2. Limit the event fields sent to the LLM to six defined fields
3. Replace event categories with defined fixed values
4. Mask secrets, email addresses and IP addresses in the event summaries sent to the LLM

The original Wazuh events and the SQLite storage specification are not changed.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **ai-defense-manager VM 230 (root)**.

# Chapter 1: Reviewing Storage and Input

## 1.1 SQLite Columns

⟦C0⟧

There are no columns that store Wazuh's `full_log`, arbitrary `data`, user names, commands or passwords. The contents that need checking are `summary` and `reasoning`, produced by the AI, and `event_summary`, which comes from Wazuh.

## 1.2 Saving, Retrieval, Data Model and Analysis Code

⟦C1⟧

All SQL uses placeholders, so SQL injection is handled.

⟦C2⟧

`full_log`, arbitrary `data`, commands and passwords are not referenced. However, `rule.description` (the source of the summary) and `decoder.name` / `location` (the source of the category) are strings from outside, so unexpected information could still get mixed in.

⟦C3⟧

⟦C4⟧

The AI analysis service has the following good points.

- It instructs the model to treat event descriptions and context as "untrusted data"
- It defines the output shape with a JSON Schema
- It validates that the evidence event IDs are in the input
- It prohibits blocking internal IPs, and block proposals require multiple pieces of evidence, a global IP, a TTL of at most 900 seconds and human approval

On the other hand, `request.model_dump(mode="json")` is passed to the LLM as is, so `agent_name`, `agent_id`, `rule_description`, IP addresses and so on, which are not needed for analysis, are also being sent.

⟦C5⟧

| Field | Currently sent to the LLM | Saved in SQLite |
|---|---|---|
| `event_id` | Yes | Yes |
| `source` | Yes | Yes |
| `observed_at` | Yes | Yes |
| `severity` | Yes | Yes |
| `rule_id` | Yes | Yes |
| `rule_description` | Yes | No |
| `source_ip`, `destination_ip` | Yes | No |
| `agent_id`, `agent_name` | Yes | No |
| `event_category` | Yes | No |
| `event_summary` | Yes | Yes |

# Chapter 2: Sending Only Six Fields to the LLM

## 2.1 Backup

⟦C6⟧

If the two SHA-256 values match, the backup was taken correctly.

## 2.2 Deciding the Fields to Send

Send the LLM only the following six fields and the analysis language. `agent_name`, `agent_id`, IP addresses, `rule_description` and the optional `analysis_context` are not sent.

- `event_id`
- `observed_at`
- `severity`
- `rule_id`
- `event_category`
- `event_summary`

⟦C7⟧

⟦C8⟧

## 2.3 Checking in the Code

Parse the source code and confirm that only six fields are sent and that the names of the excluded fields do not appear.

⟦C9⟧

## 2.4 Checking by Running It (Mock)

There are no existing tests.

⟦C10⟧

⟦C11⟧

Temporarily replace the HTTP client with a fake (mock), capture the content actually sent, and examine it. The test events deliberately contain fields that should be excluded (`PRIVATE_...` and IP addresses), and we confirm they are not in what is sent. No communication with Ollama, no DB writes and no service restart occur.

⟦C12⟧

## 2.5 Checking the Diff and Applying

⟦C13⟧

Only the part that builds what is sent to the LLM has changed. Restart the service to apply it (the API stops briefly).

⟦C14⟧

⟦C15⟧

Fetch actual Wazuh events and analyze them with the new way of sending. The analysis result is recorded in SQLite, but no firewall changes or IP blocks are made.

⟦C16⟧

At build time it returned `HTTP 200`, analyzed seven Proxmox VE authentication-success events, and returned `severity: info`, `confidence: 0.9` and `recommended_action: no_action`.

⟦C17⟧

At build time `analysis_runs` had three rows, and the latest record was `('info', 'no_action', 7, 'completed')`.

# Chapter 3: Protecting the Contents of Categories and Summaries

## 3.1 Where Information Can Get Mixed In

⟦C18⟧

- `description` → `event_summary`: up to 512 characters, sent to the LLM as is
- `decoder` or `location` → `event_category`: up to 64 characters, sent to the LLM as is. `location` is where the log came from, so it can contain file paths or host information

The policy is as follows.

1. Replace `event_category` with defined fixed categories
2. In `event_summary`, find and mask API keys, tokens, passwords, email addresses, IP addresses and so on
3. Keep to the length limit even after masking
4. Do not change the original Wazuh events or the SQLite saving code

## 3.2 Available Libraries

⟦C19⟧

⟦C20⟧

Dependencies are managed with `requirements.lock`. There is no dedicated library for finding secrets, so build it with Python's standard `re` and `ipaddress`.

Deleting IP addresses and email addresses would also lose information needed to identify an attacker, so instead of deleting them, replace them with the following masks.

| Information | Replacement |
|---|---|
| API keys, Bearer tokens, passwords | `[REDACTED_SECRET]` |
| Email addresses | `[REDACTED_EMAIL]` |
| IP addresses (both internal and external) | `[REDACTED_IP]` |
| Non-string input and the like | `[REDACTED_EVENT]` |

## 3.3 Examining the Actual Categories

Count the categories of 50 events over the last 24 hours.

⟦C21⟧

At build time there were five kinds. Replace them as follows.

| Current category | Count | Value sent to the LLM |
|---|---:|---|
| `pvedaemon` | 34 | `virtualization_management` |
| `pam` | 11 | `authentication` |
| `sshd` | 2 | `remote_access` |
| `useradd` | 2 | `account_management` |
| `open-userdel` | 1 | `account_management` |
| Anything else | — | `other` |

## 3.4 Backup

⟦C22⟧

Confirm that the four SHA-256 values match in pairs.

⟦C23⟧

⟦C24⟧

## 3.5 Fixing the Categories

Because the replacement is done in `wazuh_relay.py`, the categories of events saved from now on also become fixed values, not just those sent to the LLM.

⟦C25⟧

⟦C26⟧

Unknown decoder names also become `other`, so arbitrary strings such as host names no longer enter the category.

## 3.6 Masking the Summary

Add `_sanitize_event_summary()` to `ai_analysis.py` and apply it to `event_summary` just before sending to the LLM. It finds information of known shapes; it cannot find secrets or user names of unknown shapes. Note that this is not complete anonymization.

⟦C27⟧

Pasting can break the terminal display, so check the contents of the file.

⟦C28⟧

## 3.7 Tests for Masking

⟦C29⟧

⟦C30⟧

## 3.8 Tests of the Content Sent (Mock)

⟦C31⟧

Go through the actual `analyze_events()` and confirm that no secrets remain in the JSON passed to Ollama. There is no communication with Ollama and no writing to SQLite.

⟦C32⟧

## 3.9 Masking Quoted Values to the End

With the regular expression from 3.6, a quoted value such as `password="my secret phrase"` is masked only up to the first space. Rewrite just that one line so that when the value is `"..."` or `'...'`, the whole contents of the quotes are masked.

⟦C33⟧

Confirm that the result becomes `[REDACTED_SECRET]` as a whole.

⟦C34⟧

## 3.10 Checking the Diff and Applying

⟦C35⟧

Confirm that in `wazuh_relay.py` only the category replacement has changed, and in `ai_analysis.py` only the addition of the masking function and the processing of `event_summary`. Masking is used only when sending to the LLM; the `event_summary` saved in SQLite is as before (handled in the next part).

⟦C36⟧

⟦C37⟧

⟦C38⟧

⟦C39⟧

At build time, the `event_category` of all five events had become `virtualization_management`. This API fetches and returns events and includes `agent_id` and `agent_name`, but these are not sent to the LLM.

# Closing Notes

In Part 19 we narrowed the information passed to the LLM as follows.

| Measure | Details |
|---|---|
| Fields sent | Only six fields and the analysis language |
| Categories | Fixed values (unknown ones become `other`) |
| Summaries | Secrets, email addresses and IP addresses are masked before sending |

In the next part, we fix a problem that makes AI analysis fail, and also apply masking to the summaries saved in SQLite.

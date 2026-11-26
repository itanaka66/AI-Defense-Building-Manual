---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 48: Narrowing the Wazuh Event Conversion to Seven Fields"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 48 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 47 we examined the existing implementation of the AI Defense Manager (VM 230) and decided where to put the allowlist. Here we actually change the code.

1. Before changing anything, save copies of the five target files
2. Check the environment for running tests and the module import path
3. Tally the actual groups, in order to switch classification from `location` and `decoder.name` to `rule.groups`
4. Using Python syntax analysis (AST), rewrite only two files (`wazuh_relay.py` and `ai_analysis.py`)
5. Run 26 unit tests with synthetic events and check the diff

No actual communication with Wazuh or Ollama, no writes to PostgreSQL or SQLite, and no service restarts.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **VM 220**: security-core (root)

# Chapter 1: Saving the Files Before the Change

We create a directory per date and time under `/var/backups/ai-defense-manager/`, copy with `cp -a` to keep owner, permissions and times, and compare the SHA256 with the originals.

> **Run on: VM 230**

⟦C0⟧

The copies and SHA256 comparisons of all five files succeeded. The copies are in `/var/backups/ai-defense-manager/20261123-031115`. The `root:ai-defense`, `640` of `wazuh_relay.py` and the others are also preserved.

# Chapter 2: Checking the Test Environment

## 2.1 Python and Test Tools

No new packages are installed.

> **Run on: VM 230**

⟦C1⟧

Python 3.12.3, FastAPI, Pydantic and HTTPX are available, but `pytest` was not installed. We do not install `pytest` and use Python's standard `unittest` instead.

## 2.2 Module Import Path

> **Run on: VM 230**

⟦C2⟧

All existing modules could be imported from `/opt/ai-defense-manager`, and `unittest` was usable. The service runs as the user `ai-defense` with working directory `/opt/ai-defense-manager`, so the tests match these conditions.

## 2.3 The Current Classification and Summary

> **Run on: VM 230**

⟦C3⟧

The current classification used `decoder.name` first and fell back to `location`. If `location` is removed, events that were classified only by `location` could become `other`, so we change the classification to use `rule.groups`.

# Chapter 3: Designing the Classification

## 3.1 Tallying the Actual Groups

Wazuh's `alerts.json` is `wazuh:wazuh`, `640`, so run this as **root** on VM 220 (an ordinary user gets `PermissionError`). No values are displayed.

> **Run on: VM 220**

⟦C4⟧

| Item | Count |
|---|---:|
| Valid JSON | 268 |
| Invalid JSON | 0 |
| No `rule.groups` | 0 |
| `pam` | 228 |
| `proxmox-ve` | 16 |
| `sshd` | 1 |
| `sudo` | 3 |
| `postgresql` | 34 |
| `authentication_failed` | 4 |

Groups are counted with overlap, so the total does not match the number of events.

## 3.2 Classification and Schema Compatibility

> **Run on: VM 230**

⟦C5⟧

`event_category` is a string of 1–64 characters, so adding classifications requires no change to the Pydantic schema. The classifications we decided on are as follows. When there are several specific groups, the higher row takes priority.

| Priority | Wazuh `rule.groups` | Classification |
|---:|---|---|
| 1 | `pvedaemon`, `proxmox-ve` | `virtualization_management` |
| 2 | `pam`, `authentication_success`, `authentication_failed` | `authentication` |
| 3 | `sshd` | `remote_access` |
| 4 | `sudo` | `privilege_escalation` |
| 5 | `useradd`, `open-userdel` | `account_management` |
| 6 | `postgresql` | `database` |
| 7 | other | `other` |

General groups such as `syslog`, `local`, `error` and `access_control` alone do not produce a specific classification.

## 3.3 The Input Boundary

> **Run on: VM 230**

⟦C6⟧

`SecurityEvent` and `AIAnalysisRequest` use `extra='forbid'` (reject unknown fields), which is a good design. However, `/api/v1/analysis` is not Wazuh-specific; it also accepts input from Prometheus and others. So we decide that:

- **Wazuh-specific constraints are applied at Wazuh retrieval (`wazuh_relay.py`)**
- **Where data is sent to the AI, only allowed fields common to all events are sent**

# Chapter 4: Rewriting the Two Files

## 4.1 Last Check Before the Change

> **Run on: VM 230**

⟦C7⟧

The SHA256 of the three files matched the copies.

## 4.2 Reading the Function Definitions

The definition of `analyze_events` spans several lines and cannot be found by a replacement that searches for a one-line string. We read the actual definition and the part that sends to the AI.

> **Run on: VM 230**

⟦C8⟧

⟦C9⟧

## 4.3 Rewriting with the AST

We drop broad regex-based replacement and, using the result of Python syntax analysis, replace only the function bodies and the part that builds the list of events. The proposed changes to both files are **written only after both pass the syntax check**. The APIs, schemas and masking (`event_sanitizer.py`) are not changed.

> **Run on: VM 230**

⟦C10⟧

> **Caution:** This script checks the backup directory and the pre-change SHA256 of the three files (the values at build time) before rewriting. If they do not match, it stops without writing anything. When using it in your own environment, adjust these to the values from when you saved the copies in Chapter 1.

| File | What changed |
|---|---|
| `wazuh_relay.py` | validates the seven-field input; classifies by `rule.groups`; does not use `agent.name`, `location` or `decoder.name` |
| `ai_analysis.py` | builds what is sent to the AI from six fields only (`_build_event_payload()`); checks Wazuh event classification and forbidden fields |
| `event_sanitizer.py` | unchanged |

All syntax checks passed; no service restart, communication or DB connection took place.

# Chapter 5: Testing with Synthetic Events

## 5.1 26 Unit Tests

No actual Wazuh event retrieval, LLM calls or DB writes.

> **Run on: VM 230**

⟦C11⟧

**All 26 passed** (0 failures, 0 errors).

- the six specific classifications and their priority order
- general groups become `other`
- invalid times, time zones, severities, IDs and groups are rejected
- extra fields such as `agent.name`, IPs, `full_log` and `data` are ignored
- what is sent to the AI is only the six allowed fields
- invalid classifications and forbidden fields in Wazuh events are rejected
- classification constraints for other input sources are unchanged
- synthetic IPs and passwords are masked

The SHA256 of the three files was the same before and after the tests.

## 5.2 Checking the Diff

> **Run on: VM 230**

⟦C12⟧

The diffs of `wazuh_relay.py` and `ai_analysis.py` were within the intended scope, and `event_sanitizer.py` matched the copy exactly. `_build_event_payload()` is called in one place. Exit code `1` from `diff` means there are differences, not an error.

## 5.3 The Shape Received from the Relay

> **Run on: VM 230**

⟦C13⟧

`fetch_wazuh_events()` calls the Relay's `GET /v1/alerts` and passes each element of the JSON `alerts` array to `_convert_alert()`. Each element is in the following **flat, dot-separated form**.

⟦C14⟧

The new `_convert_alert()` requires `rule.groups`. In the next part, Part 49, we check whether the Relay returns this field.

# Closing Notes

In Part 48 we narrowed the Wazuh event conversion to seven fields and fixed what is sent to the AI at six fields.

| Item | Result |
|---|---|
| Copies | `/var/backups/ai-defense-manager/20261123-031115` (5 files, SHA256 match) |
| Classification | seven classifications using `rule.groups` (with priority order) |
| Changed files | `wazuh_relay.py`, `ai_analysis.py` (rewritten via AST; passed syntax check) |
| Unit tests | all 26 passed |
| Service | not restarted (still running the old code) |

In the next part, Part 49, we fix the Relay on VM 220 so that it returns `rule.groups`.

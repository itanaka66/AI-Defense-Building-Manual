---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 20: Fixing Confidence Scores and Protecting Stored Data"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 20 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". After Part 19, we found that analysis with real Wazuh events failed (`502`). Here we do the following.

1. Investigate and fix the cause of the analysis failure (the AI returns confidence on a 0–100 scale)
2. Move the masking from Part 19 into a common module and also use it when saving to SQLite
3. Check the saved history, the DB files, the service settings and the listening ports

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **ai-defense-manager VM 230 (root)**.

# Chapter 1: Why the Analysis Fails

## 1.1 Symptoms

At the end of Part 19 we confirmed that the categories had been replaced. Next, run the AI analysis.

⟦C0⟧

⟦C1⟧

⟦C2⟧

At build time it returned `{"detail":"AI analysis failed or returned an invalid response"}` (`502`).

## 1.2 Log and Connection Target

⟦C3⟧

The log records `200` for `/health` and for fetching events, and `502` for analysis, but the details of the Python exception are not shown (because the application is designed not to expose details externally).

⟦C4⟧

The connection target was `http://192.168.0.180:11434/`. Check whether VM 230 can reach Ollama.

⟦C5⟧

The list of models was returned, showing that `qwen3:8b` is present. It is not a network problem.

## 1.3 Model and Schema

⟦C6⟧

⟦C7⟧

The model name is `qwen3:8b`, which matches what is on Ollama. The API is Ollama's `/api/chat`, the output shape is specified with `AIAnalysisProposal.model_json_schema()`, and the reply is validated with Pydantic's `model_validate()`.

⟦C8⟧

| Field | Constraint |
|---|---|
| `summary` | 1–2000 characters |
| `severity` | `info`, `low`, `medium`, `high`, `critical` |
| `confidence` | 0.0–1.0 |
| `evidence_event_ids` | 1–100 (required) |
| `reasoning` | 1–4000 characters |

## 1.4 Asking Ollama Directly

Without writing to the application's DB, ask Ollama directly with the same schema.

⟦C9⟧

At build time it returned `HTTP_STATUS: 200` and JSON, but the JSON contained `"confidence": 100`. The schema allows 0.0–1.0, so `100` fails validation. This is the cause of the `502`.

# Chapter 2: Adding an Instruction About Confidence

## 2.1 Fixing SYSTEM_PROMPT

Without changing the Pydantic constraint (0.0–1.0), add three lines to the AI's instructions (`SYSTEM_PROMPT`) saying that confidence must be answered as a decimal. Also take a backup.

⟦C10⟧

The only difference is the three added lines of instructions.

⟦C11⟧

## 2.2 Checking with the Fixed Instructions

Ask Ollama using the fixed `SYSTEM_PROMPT` and validate the reply against the actual schema. Nothing is saved to SQLite and the service is not restarted.

⟦C12⟧

At build time it returned `"confidence": 0.95` and `SCHEMA_VALIDATION: OK`.

## 2.3 Applying

⟦C13⟧

⟦C14⟧

Analyze five real Wazuh events. The result is saved in SQLite.

⟦C15⟧

The results at build time were as follows. Successful authentication alone does not establish unauthorized access, so it was a cautious judgment that recommended "monitoring" rather than immediate blocking.

| Item | Result |
|---|---|
| HTTP | `200 OK` |
| `severity` | `info` |
| `confidence` | `0.85` |
| `recommended_action` | `monitor` |
| `target_ip`, `ttl_seconds` | `null` |
| `requires_human_approval` | `true` |

⟦C16⟧

At build time `analysis_runs` had 4 rows and `analysis_evidence` 28.

# Chapter 3: Masking the Saved Summaries Too

## 3.1 The Current Design

⟦C17⟧

⟦C18⟧

When sending to the LLM, masking is done with `_sanitize_event_summary()`, but when saving to SQLite, `event.event_summary` is written as is.

⟦C19⟧

⟦C20⟧

`analysis_history.py` and `ai_analysis.py` do not import each other. Rather than having one import the other, move the masking function into a new `app/services/event_sanitizer.py` and use it from both places. Existing SQLite data is not changed; only data saved from now on is protected.

## 3.2 Backup

⟦C21⟧

⟦C22⟧

## 3.3 Moving It to a Common Module

Without changing the body of the function (the masking rules), move it under the name `sanitize_event_summary()`.

⟦C23⟧

⟦C24⟧

## 3.4 Tests for Masking

Check with made-up data, not real data.

⟦C25⟧

## 3.5 Checking the Diff

`/opt/ai-defense-manager` is not managed with Git, so compare with the backups from 3.2.

⟦C26⟧

- `ai_analysis.py`: uses the common function
- `analysis_history.py`: masks just before the INSERT into SQLite
- `event_sanitizer.py`: the masking rules are unchanged

## 3.6 Checking Saving with a Temporary DB

⟦C27⟧

⟦C28⟧

`save_analysis()` commits automatically when it finishes normally. Rather than trying it on the production DB and undoing it, use a temporary DB.

⟦C29⟧

⟦C30⟧

Save an event containing an email address, a password, an API key and an IPv4 address, read it back, and confirm that the original values do not remain.

⟦C31⟧

## 3.7 Applying

⟦C32⟧

⟦C33⟧

Analyses saved from now on are masked at save time as well. Records already saved are not changed.

# Chapter 4: Checks

## 4.1 Saved History

Run the saved `analysis_evidence.event_summary` values through the common function and count the rows that would need masking. The DB is opened read-only, and the secrets themselves are not shown.

⟦C34⟧

At build time 28 rows were examined, and 0 needed masking.

## 4.2 DB Files

⟦C35⟧

| Target | Owner | Permissions |
|---|---|---:|
| `data` directory | `ai-defense:ai-defense` | 750 |
| DB file | `ai-defense:ai-defense` | 600 |
| WAL | `ai-defense:ai-defense` | 600 |
| SHM | `ai-defense:ai-defense` | 600 |

## 4.3 Service Settings

⟦C36⟧

It runs as `ai-defense`, not root; the file system is read-only in principle; and only the `data` directory is writable.

## 4.4 Listening Ports

⟦C37⟧

| Port | Listening on | Assessment |
|---|---|---|
| 8000 (FastAPI) | `127.0.0.1` | Cannot be reached directly from outside |
| 22 (SSH) | `0.0.0.0`, `[::]` | Checked in the next part |
| 53 (DNS) | `127.0.0.53`, `127.0.0.54` | Local only |

# Closing Notes

In Part 20 we did the following.

| Item | Result |
|---|---|
| Analysis failure (`502`) | Resolved by adding an instruction to return confidence as 0.0–1.0 |
| Masking | Made common in `event_sanitizer.py` and used both before sending to the LLM and before saving to SQLite |
| Saved history | 28 rows checked; none needed masking |
| DB, service, ports | Checked; no problems |

In the next part, we switch SSH on VM 230 to log in with a public key instead of a password.

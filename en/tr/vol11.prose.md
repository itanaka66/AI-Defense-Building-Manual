---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 11: Laying the Groundwork for the AI Defense Manager"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 11 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". On VM 230 (`ai-defense-manager`, 192.168.0.33), created in Part 10, we lay the groundwork for the "AI Defense Manager", the application responsible for AI analysis, decisions and responses.

This part builds the following.

- A dedicated Python virtual environment and a dedicated run-as user
- A minimal API with FastAPI, and configuration management
- The types (schemas) of the data passed to and received from the AI, and their validation

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Unless otherwise noted, everything is run on **VM 230 ai-defense-manager (root)**.

## Permission Policy

| Target | Owner | Permissions | Reason |
|---|---|---|---|
| Application (`app`) | `root:ai-defense` | Directories `750`, files `640` | The run-as user can read but not modify it |
| Configuration (`config`) | root | root only | Where secrets are kept |
| Data and logs (`data`, `logs`) | `ai-defense` | — | Written by the run-as user |
| Virtual environment (`venv`) | root | `755` | The run-as user can use but not change it |

# Chapter 1: The Python Virtual Environment

## 1.1 Checking

⟦C0⟧

`pip` is not installed on the system (on Ubuntu 24.04 you do not install packages into the system Python; you use a virtual environment).

⟦C1⟧

⟦C2⟧

## 1.2 Creating It

⟦C3⟧

Creating a virtual environment requires `python3.12-venv` (`ensurepip`). Without it creation fails, so install it first, after checking what would be installed.

⟦C4⟧

⟦C5⟧

⟦C6⟧

⟦C7⟧

⟦C8⟧

At build time this was pip 24.0 and Python 3.12.3.

# Chapter 2: Directories and the Run-As User

## 2.1 Directory Layout

⟦C9⟧

Use the following layout.

⟦C10⟧

⟦C11⟧

⟦C12⟧

## 2.2 A Dedicated Run-As User

`aidefense`, which is used for logging in, is an ordinary user that also belongs to administrative groups. The application runs as a dedicated system user, `ai-defense`, which cannot log in.

⟦C13⟧

⟦C14⟧

⟦C15⟧

⟦C16⟧

## 2.3 Owners and Permissions

Make data and logs writable by the run-as user.

⟦C17⟧

⟦C18⟧

Set the application to `root:ai-defense` so that the run-as user can read it but not modify it.

⟦C19⟧

⟦C20⟧

⟦C21⟧

⟦C22⟧

⟦C23⟧

⟦C24⟧

Keep the virtual environment owned by root with `755` (the run-as user can use it but cannot change it).

⟦C25⟧

⟦C26⟧

⟦C27⟧

# Chapter 3: Base Packages

## 3.1 Installation

⟦C28⟧

⟦C29⟧

⟦C30⟧

If `HTTP/2 200` is returned, PyPI can be reached.

⟦C31⟧

## 3.2 Checking

⟦C32⟧

Confirm `No broken requirements found.`

⟦C33⟧

⟦C34⟧

⟦C35⟧

## 3.3 Recording the Installed Packages

⟦C36⟧

⟦C37⟧

⟦C38⟧

⟦C39⟧

⟦C40⟧

At build time there were 24 packages, including dependencies.

# Chapter 4: A Minimal API

## 4.1 main.py

First create a minimal API that has only `/health`, which returns the status.

⟦C41⟧

⟦C42⟧

⟦C43⟧

⟦C44⟧

## 4.2 Starting and Checking

Confirm that port 8000 is free, and start it as the dedicated user, listening only on the machine itself (127.0.0.1).

⟦C45⟧

⟦C46⟧

This command keeps running and does not return, so do the check from another terminal (a second SSH connection).

⟦C47⟧

It has succeeded if `HTTP/1.1 200 OK` and the following content are returned.

⟦C48⟧

⟦C49⟧

# Chapter 5: Configuration Management

## 5.1 config.py

Gather settings such as connection targets in one place, and allow them to be overridden by environment variables (names starting with `AIDM_`). Secrets such as passwords are not written here.

⟦C50⟧

⟦C51⟧

⟦C52⟧

## 5.2 Checking Loading and Overriding

⟦C53⟧

⟦C54⟧

Confirm `CONFIG_OK` and `ENV_OVERRIDE_OK`.

## 5.3 Building It into main.py

⟦C55⟧

⟦C56⟧

⟦C57⟧

⟦C58⟧

Stop the running Uvicorn by pressing `Ctrl+C` in the terminal where it was started, and start it again.

⟦C59⟧

⟦C60⟧

⟦C61⟧

After the settings are built in, the same content as in 4.2 is returned.

# Chapter 6: Data Types (Schemas)

Define strictly, with Pydantic models, the shape of the data passed to the AI and received from the AI. Fields that are not defined (for example the full log `full_log`) are not accepted (`extra="forbid"`).

⟦C62⟧

## 6.1 Security Events (security_event.py)

⟦C63⟧

Check the syntax. The run-as user cannot write to the application directory, so check it with a method that does not write bytecode, instead of `py_compile` (which writes bytecode).

⟦C64⟧

Pasting can break the terminal display, so also check that the end of the file was written correctly.

⟦C65⟧

It was written correctly if the last three lines are as follows.

⟦C66⟧

⟦C67⟧

Confirm that an invalid IP address and undefined fields are rejected.

⟦C68⟧

## 6.2 AI Analysis Requests (analysis.py)

The events passed to the AI at one time are limited to 1–100, and the language to Japanese or English.

⟦C69⟧

⟦C70⟧

⟦C71⟧

## 6.3 AI Analysis Results (analysis_proposal.py)

The proposals returned by the AI carry the following safety constraints.

- Recommended actions are limited to six defined types
- Confidence (`confidence`) is 0.0–1.0
- The IDs of the supporting events are required
- A proposal to temporarily block an IP is allowed only for internet addresses (global IPs), with two or more supporting events, an expiry of at most 900 seconds (15 minutes), and human approval required
- The actual blocking is not implemented here

⟦C72⟧

⟦C73⟧

⟦C74⟧

⟦C75⟧

Confirm that a normal proposal and a proposal to block a global IP are accepted, and a proposal to block a private IP is rejected.

⟦C76⟧

## 6.4 Action Candidates (action.py)

This is the type of the "action candidate" passed, based on the AI's proposal, to the Action Gateway (the part that carries out actual responses). A temporary IP block starts as pending approval (`pending`) and is not executed until a person approves it.

⟦C77⟧

⟦C78⟧

⟦C79⟧

⟦C80⟧

⟦C81⟧

Confirm that a notification candidate and a global IP block candidate (pending approval) are accepted, and that a private IP block, a block that is approved from the start, and a block with only one supporting event are rejected.

⟦C82⟧

If `ALL_ACTION_TESTS_PASSED` is shown, all five items have passed.

## 6.5 Checking the Files and Cleaning Up

⟦C83⟧

In the original build, an empty temporary file `analysis.py.tmp` had been created during the work, so it was deleted (not needed if it does not exist).

⟦C84⟧

# Summary of Part 11

## What Was Built

| File | Contents |
|---|---|
| `/opt/ai-defense-manager/venv` | Python virtual environment (FastAPI, Uvicorn, Pydantic, pydantic-settings, HTTPX) |
| `/opt/ai-defense-manager/requirements.lock` | List of installed packages |
| `app/main.py` | API (`/health`) |
| `app/core/config.py` | Settings (can be overridden by `AIDM_` environment variables) |
| `app/schemas/security_event.py` | Security events |
| `app/schemas/analysis.py` | AI analysis requests |
| `app/schemas/analysis_proposal.py` | AI analysis results |
| `app/schemas/action.py` | Action candidates |

## Safety Rules

- The application runs as the dedicated user `ai-defense`, which cannot log in, and cannot modify its own code.
- The API listens only on the machine itself (127.0.0.1).
- Only AI output that passes the defined types and constraints is accepted.
- IP blocks require a global IP, two or more supporting events, at most 15 minutes and human approval, and start as pending approval.

## What Remains

- Uvicorn is started by hand (it has not been made a systemd service). After Part 12 it was stopped with `kill`.
- The AI analysis processing (integration with Ollama) is built in the next part.

---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 60: Keeping Error Responses and Logs from Leaking Information"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 60 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 59 we put API authentication into production. Here we check whether internal information or submitted values leak from API error responses and logs.

1. Read how API error responses are built, and test whether unhandled exceptions expose internal information
2. Find that input validation error (`422`) responses contain the submitted values as is, and change them to a fixed message
3. Check the destinations and permissions of the Uvicorn logs, the journal and syslog

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: Checking Error Responses

## 1.1 How Error Responses Are Built

> **Run on: VM 230**

⟦C0⟧

| Target | Result |
|---|---|
| Analysis APIs, Wazuh APIs | return errors with fixed strings |
| Authentication | `401`, `403`, `503` with fixed strings |
| Returning exception strings as is | none |
| Exposing tracebacks | none |
| Uvicorn debug | not in the startup arguments |

## 1.2 Middleware and Global Exception Handling

> **Run on: VM 230**

⟦C1⟧

There was the body limit (256KiB; `413` with a fixed JSON if exceeded) and disabling of OpenAPI and others, but no application-specific global exception handling or CORS middleware.

## 1.3 Testing Unhandled Exceptions

We test with an independent application that does not affect production.

> **Run on: VM 230**

⟦C2⟧

For unhandled exceptions, only `HTTP 500` and `Internal Server Error` were returned; no internal exception markers or tracebacks were included (FastAPI `debug=False`).

## 1.4 Testing Input Validation Errors

> **Run on: VM 230**

⟦C3⟧

**A problem was found.** The standard FastAPI/Pydantic `422` response included parts of the submitted body (entered values and values of extra fields). If a secret were sent by mistake, it would be returned in the response (this was found in an independent test; nothing leaked in production).

# Chapter 2: Making the `422` Response a Fixed Message

## 2.1 Checking the Impact

> **Run on: VM 230**

⟦C4⟧

With FastAPI 0.165.0 and Pydantic 2.14.4, there was no client logic in the application that uses the details of `422`. Other error responses are fixed messages too, so we make `422` uniform in the following form.

⟦C5⟧

## 2.2 Testing the Fix in an Independent Environment

> **Run on: VM 230**

⟦C6⟧

It remains `422`, but the response is now only `{"detail":"Invalid request"}`, with no entered values, values of extra fields or tracebacks.

## 2.3 Checking Before the Change

> **Run on: VM 230**

⟦C7⟧

⟦C8⟧

⟦C9⟧

The integrity of the existing copy (`application-source.tar.gz`) passed, but the `app/main.py` inside it is from before API authentication was added, and its hash differs from the current one. **Do not overwrite the current source with this copy.**

## 2.4 Fixing `app/main.py`

We change only `app/main.py` and check the syntax. No service restart, no requests to the production API and no DB changes.

> **Run on: VM 230**

⟦C10⟧

> **Caution:** In the build records, no new copy was made at this point. When doing this in your own environment, it is safer to save a copy of `app/main.py` before the fix.

The syntax check passed and the owner and permissions were unchanged (the `diff` in the script has no original to compare with, so it shows the whole file as added).

## 2.5 Testing with the Fixed Application

We load the fixed `app.main.app` and check with independent requests.

> **Run on: VM 230**

⟦C11⟧

`422`, the fixed response, and not exposing secret markers, extra fields or tracebacks all passed.

## 2.6 Final Source Check

> **Run on: VM 230**

⟦C12⟧

The fixed `422` response handling, the API authentication dependencies, the `read` and `analyze` scopes, the 256KiB body limit, disabling of Swagger, ReDoc and OpenAPI, `compileall`, the systemd unit check and file ownership all passed.

## 2.7 Deploying to Production

> **Run on: VM 230**

⟦C13⟧

`active (running)` (MainPID `2340`, 0 restart failures); `/health` gave `HTTP 200`; listening on `127.0.0.1:8000`.

We send one authenticated request to the production analysis API. It gives `422` at input validation, so it does not proceed to AI analysis.

> **Run on: VM 230**

⟦C14⟧

| Checked | Result |
|---|---|
| Invalid request | `HTTP 422` |
| Response | `{"detail":"Invalid request"}` |
| Entered secret markers, values of extra fields, tracebacks | not leaked |

# Chapter 3: Final Check of Error Responses

> **Run on: VM 230**

⟦C15⟧

⟦C16⟧

No place was found that outputs `str(exc)`, `repr(exc)` or tracebacks to responses or logs as is; AI analysis failures, history storage failures, Relay failures, authentication failures, insufficient privilege and token DB faults all returned fixed messages.

> **Run on: VM 230**

⟦C17⟧

There is no application-specific handling for unexpected exceptions, but we confirmed in Chapter 1 that with FastAPI `debug=False`, unhandled exceptions return only `HTTP 500 Internal Server Error`. We judged that no fix is needed now.

# Chapter 4: Log Destinations and Permissions

## 4.1 Uvicorn Logs

> **Run on: VM 230**

⟦C18⟧

| Item | Result |
|---|---|
| Listening | `127.0.0.1:8000` |
| Concurrent connections, Keep-Alive | 8, 5 seconds |
| Log destination | the systemd journal (standard error also goes to the journal) |
| Journal directory | `root:systemd-journal` |

`--log-level` is not specified; Uvicorn's default log level applies.

## 4.2 Journal Permissions and Retention

> **Run on: VM 230**

⟦C19⟧

⟦C20⟧

| Item | Result |
|---|---|
| Space used | 89.0MB |
| Journal files | `root:systemd-journal`, `640` |
| Journal directory | `2755` |
| `systemd-journal` group | no users registered |
| `ai-defense` | not in the `systemd-journal` group |
| Retention period and size settings | no explicit settings (set in Part 61) |

## 4.3 syslog

> **Run on: VM 230**

⟦C21⟧

The log path is as follows.

⟦C22⟧

> **Run on: VM 230**

⟦C23⟧

| Item | Result |
|---|---|
| rsyslog | `active` (user `syslog`); no syslog-ng |
| `/var/log/syslog`, `/var/log/auth.log` | `syslog:adm`, `640` |
| `/var/spool/rsyslog` | `syslog:adm`, `700` |
| Listening for syslog from outside | none |
| `adm` group | `syslog`, `aidefense` (`ai-defense` is not a member) |
| Routing | auth/authpriv separated from ordinary logs |
| logrotate | weekly, 4 generations, compressed |

## 4.4 Log Permissions After Rotation

> **Run on: VM 230**

⟦C24⟧

`syslog`, `syslog.1`, `auth.log` and `auth.log.1` were all `syslog:adm`, `640`. `logrotate.timer` is `active`.

# Closing Notes

In Part 60 we checked API error responses and log permissions, and fixed the problem of values leaking from input validation errors.

| Item | Result |
|---|---|
| Error responses | all fixed messages; unhandled exceptions give only `500 Internal Server Error` |
| `422` response | unified as `{"detail":"Invalid request"}` (confirmed in production) |
| Logs | journal `640`, `2755`; syslog `syslog:adm`, `640`; the service account cannot read the logs |
| Remaining | journal retention period and size not explicitly set |

In the next part, Part 61, we set a size limit for the journal and check log management as a whole.

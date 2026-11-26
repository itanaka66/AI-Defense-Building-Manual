---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 66: Automating FSS Verification Every 15 Minutes"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 66 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 65 we checked the FSS-sealed journal on another host. Here we make VM 230 run FSS verification **automatically every 15 minutes**.

1. Examine the structure of the existing AI Defense Manager and decide where to integrate verification
2. Use the headers to decide which journals are verification targets
3. Create the verification script, a systemd service and a timer, and run it once by hand
4. Enable the timer and confirm that it ran automatically
5. Investigate whether verification results can be reported to Wazuh

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root. When logged in as `aidefense`, become root with `sudo -i`)

# Chapter 1: Deciding Where to Integrate

## 1.1 Service Structure

> **Run on: VM 230**

⟦C0⟧

The AI Defense Manager is running (0 restarts), FastAPI listens only on `127.0.0.1:8000`, and there was no FSS-related systemd timer.

## 1.2 Application Structure

Run as root (as `aidefense`, `app`, `config`, `data` and so on cannot be read).

> **Run on: VM 230**

⟦C1⟧

`app/services/` contained services such as Wazuh integration and analysis history, and `app/api/` had the Wazuh and analysis APIs, but there was no scheduler or FSS verification module.

## 1.3 Service Security Settings

> **Run on: VM 230**

⟦C2⟧

The existing API is strongly isolated with `ProtectSystem=strict`, `ProtectHome=yes` and `RestrictAddressFamilies=AF_INET`. The FSS verification key and the journal are root-only, so we do not add permissions to the `ai-defense` user. Therefore, rather than integrating it into the existing FastAPI service, we use **a separate verification service that only reads, running as root, and a systemd timer**.

# Chapter 2: Deciding the Verification Targets

## 2.1 Journal Files

> **Run on: VM 230**

⟦C3⟧

There were 14 archived system journals and the current journal.

## 2.2 Sorting by Header

> **Run on: VM 230**

⟦C4⟧

| Category | Count | Automatic handling |
|---|---:|---|
| FSS-sealed archive | 1 | check cryptographically |
| Old archives from before FSS | 13 | record as out of scope (`SKIP`) |
| Current system journal | 1 | check cryptographically |

Old archives (`Tag objects` 0) can give `PASS` with `--verify-key` through the ordinary integrity check, so we treat them as neither "verification failure" nor "FSS pass", but as `SKIP`.

## 2.3 Checking the Current Journal as a Baseline

> **Run on: VM 230**

⟦C5⟧

The current journal was `ONLINE`, `SEALED`, `SEALED_CONTINUOUS`, `Tag objects` 8, and verification gave `PASS` (exit code `0`). "final 5min … entries not sealed" is the last, not-yet-sealed part of an active journal and is normal.

# Chapter 3: Building the Verification Mechanism

## 3.1 Creating Three Files

| File | Content |
|---|---|
| `/usr/local/sbin/ai-defense-fss-verify` | verification script (`root:root`, `0750`) |
| `/etc/systemd/system/ai-defense-fss-verify.service` | oneshot service, read-only sandbox (`0644`) |
| `/etc/systemd/system/ai-defense-fss-verify.timer` | 5 minutes after boot, then every 15 minutes (`0644`) |

Targets are limited to system journals whose headers have `SEALED` and `SEALED_CONTINUOUS` and whose `Tag objects` is 1 or more. If a file already exists at the same path, it stops without overwriting. At this stage there is no `daemon-reload`, no service run and no timer enabling.

> **Run on: VM 230**

⟦C6⟧

> **Caution:** If this script is not run as root, it stops at the first check (the three files are not created). When logged in as `aidefense`, become root with the following before running it.

⟦C7⟧

## 3.2 Static Checks

> **Run on: VM 230**

⟦C8⟧

| Check | Result |
|---|---|
| Bash syntax | passed |
| systemd unit syntax | passed |
| File owner and permissions | passed |
| Verification key readable only by root | passed |
| Timer, service | `disabled`, `inactive` / `inactive` |
| Changes to existing services | none |

The value passed to `--verify-key` is the verification key, which may be public, not the secret sealing key. However, the verification key may appear in process arguments.

## 3.3 Registering and Running It Once by Hand

The timer is not enabled.

> **Run on: VM 230**

⟦C9⟧

| Result | Count |
|---|---:|
| Cryptographic verification `PASS` | 2 (sealed archive, current journal) |
| Old archives `SKIP` | 13 |
| Verification failures | 0 |

The service exited with code `0`, and systemd's result was `success`. From inside the systemd sandbox, it can read the root-only key and journal and verify them.

# Chapter 4: Enabling the Timer

## 4.1 Enabling

> **Run on: VM 230**

⟦C10⟧

Inside, it does the following two things.

⟦C11⟧

The timer became `enabled` and `active`. The existing `ai-defense-manager.service` also remains `active (running)`, PID `2340`, 0 restarts. The display right after showed `Trigger: n/a`, `NEXT: -`.

## 4.2 Checking That It Ran Automatically

> **Run on: VM 230**

⟦C12⟧

| Item | Result |
|---|---:|
| Time of automatic run | 03:45:58 UTC (right after the timer was started) |
| Cryptographic verification `PASS` | 2 |
| Old archives `SKIP` | 13 |
| Verification failures | 0 |
| Service exit | `0` (`Result=success`) |
| Timer | `active (waiting)`, next in about 14 minutes |

The `OnBootSec=5min` condition had already passed, so the first run happened when the timer was started, and it runs every 15 minutes after that. `ExecMainCode=1` means the process exited normally; the exit status is `ExecMainStatus=0`.

# Chapter 5: Can Wazuh Be Notified?

We investigate, read-only, whether Wazuh can detect verification failures (`VERIFY_FAIL`, `HEADER_ERROR`, `FATAL`).

> **Run on: VM 230**

⟦C13⟧

| Investigated | Result |
|---|---|
| `wazuh-agent` package | not installed |
| Agent service and process | none |
| `ossec.conf` | none |
| Configuration to collect journald | none |
| FSS verification timer | enabled and running |

VM 230 has no Wazuh agent, and there is not yet a mechanism to send FSS verification results to Wazuh Manager (VM 220). This is not a problem with the verification itself; the integration path simply does not exist yet.

# Closing Notes

In Part 66 we made FSS verification run automatically every 15 minutes.

| Item | Result |
|---|---|
| Verification script | `/usr/local/sbin/ai-defense-fss-verify` (`0750`) |
| Service and timer | `ai-defense-fss-verify.service` (oneshot, read-only) and `.timer` (5 minutes after boot, then every 15 minutes) |
| Targets | system journals with `SEALED`, `SEALED_CONTINUOUS` and `Tag objects` 1 or more (older ones are `SKIP`) |
| Results | `PASS` 2, `SKIP` 13, 0 failures (once by hand, once automatically) |
| Integration with Wazuh | none yet; VM 230 has no agent |

In the next part, Part 67, before integration, we examine the Wazuh Manager side on VM 220. There, a problem is found in Wazuh's local rules file.

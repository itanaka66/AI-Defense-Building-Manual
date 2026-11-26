---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 64: Running and Checking FSS Sealing"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 64 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 62 we created the FSS keys, and in Part 63 we moved the verification key to the Proxmox host. Here we have journald start sealing and check it with the verification key.

1. Restart journald and check the sealing state
2. Investigate why the seal tags (`Tag objects`) stayed at 0
3. Switch the journal (`journalctl --rotate`) to create a new file and confirm it is sealed
4. Check the sealed journal cryptographically with the verification key

No log deletion, size cleanup or key changes.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: Restarting journald

## 1.1 Restart and Sealing State

We restart only journald on VM 230, once.

> **Run on: VM 230**

⟦C0⟧

The restart succeeded, but `Tag objects` was `0` in every journal file.

## 1.2 Checking After Some Time

> **Run on: VM 230**

⟦C1⟧

About 43 minutes after the restart, `Tag objects` was still `0`. journald was `active (running)` with `NRestarts=0`, the FSS key file existed (`root:systemd-journal`, `600`), and there were no FSS-related errors. systemd was built with `+GCRYPT`, and `libgcrypt` was loaded in journald.

> **Note:** `--interval=15min` when creating the keys is the interval for changing the sealing key, not the interval for writing tags. Also, `journalctl --verify --verify-key=…` may return `PASS` even for journals not using FSS if the ordinary integrity check passes, so `PASS` alone is not evidence that FSS is working.

# Chapter 2: Why the Tags Were 0

> **Run on: VM 230**

⟦C2⟧

| Item | Time (UTC) |
|---|---|
| Current `system.journal` created | November 23 20:40:55 |
| FSS key file created | November 24 00:03:37 |
| journald restarted | November 24 00:50:23 |
| Current journal last updated | November 24 01:40:03 |

The current `system.journal` was **a file that existed since about 3 hours 23 minutes before the FSS keys were created**, and even after restarting journald it kept using that file. The FSS marker (`SEALED`) is set when the header of a new file is created; it is not added to an existing file afterwards. So we switch the journal to create a new file.

# Chapter 3: Switching the Journal

We archive the current journal file and switch to a new file. No logs are lost.

> **Run on: VM 230**

⟦C3⟧

After the switch, `system.journal` was as follows.

| Item | Result |
|---|---|
| `Compatible flags` | `SEALED SEALED_CONTINUOUS TAIL_ENTRY_BOOT_ID` |
| `Tag objects` | 7 |
| `State` | `ONLINE` |

**FSS is enabled and tags are actually being created.** The `user-1000` journal did not support FSS at this time.

# Chapter 4: Checking with the Verification Key

We check the current sealed `system.journal` with the verification key (the key contents are not displayed).

> **Run on: VM 230**

⟦C4⟧

| Checked | Result |
|---|---|
| Journal state | `ONLINE` |
| `SEALED`, `SEALED_CONTINUOUS` | present |
| `Tag objects` | 7 |
| `journalctl --verify --verify-key` | `PASS` (exit code `0`) |

The output was as follows.

⟦C5⟧

"final 13min … entries not sealed" is not a failure. It means the roughly 13 minutes of logs added after the last seal have not yet been sealed; they will be included in the next seal.

# Closing Notes

In Part 64 we started FSS sealing of VM 230's journal and checked it cryptographically.

| Item | Result |
|---|---|
| Why the tags were 0 | it kept using a journal file created before the FSS keys |
| Fix | created a new file with `journalctl --rotate` |
| Sealing | `SEALED SEALED_CONTINUOUS`, `Tag objects` 7 |
| Verification | `journalctl --verify --verify-key` gave `PASS` |

However, this verification was done inside VM 230. In case VM 230 is compromised, in the next part, Part 65, we check it **on a host other than VM 230**.

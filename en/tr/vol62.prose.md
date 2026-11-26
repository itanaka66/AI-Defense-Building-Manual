---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 62: Creating FSS Keys to Guard Against Log Tampering"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 62 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 61 we set a size limit for the journal. Here, after a final check of who can read the logs, we prepare **a mechanism for detecting that logs have been rewritten**.

The systemd journal has a mechanism called **FSS (Forward Secure Sealing)**.

- The secret sealing key (Seal key) is kept inside the VM and seals the journal at fixed intervals (here, 15 minutes). The key moves forward with time, and keys for earlier intervals do not remain
- The verification key is stored outside the VM, and `journalctl --verify --verify-key=…` checks that nothing was rewritten after sealing

The setting `Seal=yes` (default) alone does not make FSS work; the keys must be created with `journalctl --setup-keys`.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

> **Caution:** Do not display or paste the contents of the verification key.

# Chapter 1: Final Check of Who Can Read the Logs

## 1.1 syslog

> **Run on: VM 230**

⟦C0⟧

`/var/log/syslog`, `/var/log/auth.log` and the rotated logs are `syslog:adm`, `640`, with no additional ACLs, and the service account `ai-defense` has no permission to read the logs.

## 1.2 The Journal

> **Run on: VM 230**

⟦C1⟧

| Item | Result |
|---|---|
| `/var/log/journal`, `/run/log/journal` | `root:systemd-journal`, `2755` |
| Journal files | `root:systemd-journal`, `640` |
| `systemd-journal` group | no members |
| `ai-defense` | not in a group that can read the journal |

No permission changes are needed.

## 1.3 Integrity and Persistent Storage

> **Run on: VM 230**

⟦C2⟧

The size limits (512MB, 2GB free, 64MB per file) were in place, all files shown passed the check, there were no immutable attributes, and `/var/log` is ext4 mounted read-write.

# Chapter 2: Is FSS Supported?

> **Run on: VM 230**

⟦C3⟧

| Item | Verdict |
|---|---|
| systemd FSS support | supported (systemd 255) |
| Seal default | enabled |
| Explicit Seal setting | none |
| FSS key file | not found |
| `Tag objects` in the journal header | 0 |
| Is FSS working? | no |

Passing the journal integrity check is different from tamper detection by FSS. We proceed in the following order.

1. Create the FSS keys
2. Store the verification key somewhere safe, separate from VM 230 (Part 63)
3. Check the permissions and location of the secret key
4. Confirm that newly created journals are sealed (Part 64)
5. Build a procedure to check with `journalctl --verify --verify-key=...`

FSS protection is not applied retroactively to existing journals.

# Chapter 3: Creating the FSS Keys

## 3.1 Creating the Keys

We create the keys with the standard 15-minute interval. The verification key is saved temporarily to a root-only file on VM 230 and not displayed on screen. journald is not restarted.

> **Run on: VM 230**

⟦C4⟧

| Checked | Result |
|---|---|
| Exit code | `0` |
| Secret-side FSS file | `/var/log/journal/…/fss`, `root:systemd-journal`, `600` |
| Verification key file | `/root/fss-verification-key-20261124.txt`, `root:root`, `600` |
| journald | still running; not restarted |

## 3.2 Checking the Key Format

> **Run on: VM 230**

⟦C5⟧

The format check in this script assumed "43 characters of standard Base64", which does not match the format systemd actually outputs, so it gave `FAIL`. We change the check and verify again.

> **Run on: VM 230**

⟦C6⟧

It decoded correctly to 32 bytes, and the format of the verification key was normal (the file is 44 bytes, ASCII only, with a trailing newline).

# Closing Notes

In Part 62 we checked who can read the logs and created the FSS keys.

| Item | Result |
|---|---|
| Log permissions | the service account cannot read either syslog or the journal |
| FSS support | supported in systemd 255; `Seal` enabled by default |
| FSS keys | created with a 15-minute interval. The secret side is in VM 230's journal directory (`600`); the verification key is `/root/fss-verification-key-20261124.txt` (`600`) |
| Still to do | store the verification key outside the VM; confirm that sealing begins |

We decided to store the verification key in **a root-only location on the Proxmox host `pve`**. In the next part, Part 63, we move it safely from VM 230.

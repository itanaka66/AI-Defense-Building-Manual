---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 65: Checking FSS from Another Host (VM 240)"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 65 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 64 we started FSS sealing of VM 230's journal and checked it inside VM 230. So that the result can be trusted even if VM 230 is compromised, we check it **on a host other than VM 230**.

1. Bundle the sealed journal (switch it into an archive) and move it to the Proxmox host `pve`
2. systemd 252 on `pve` cannot verify this form of journal, so create VM 240 (Ubuntu 24.04, systemd 255) dedicated to verification
3. Move the journal and verification key from `pve` to VM 240 and check them cryptographically on VM 240
4. Confirm that the files have not changed in all three places: VM 230 (where it was made), `pve` (where it is stored) and VM 240 (where it was checked)

The contents of the verification key are not displayed.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **pve**: the Proxmox host (root)
  - **VM 240**: fss-verification (`192.168.0.222`, root. When logged in as an ordinary user, become root with `sudo -i`)

# Chapter 1: Moving the Sealed Journal to `pve`

## 1.1 Creating an Archive for Verification

Copying the active journal as is may let logs be added while it is being copied. We switch the journal to create a sealed archive. No log deletion, service restarts or key changes.

> **Run on: VM 230**

⟦C0⟧

The archive was `ARCHIVED`, `SEALED SEALED_CONTINUOUS`, `Tag objects` 9, 8,388,608 bytes.

## 1.2 Moving It to `pve`

> **Run on: VM 230**

⟦C1⟧

The transfer succeeded, and the SHA-256 matched on VM 230 and `pve`.

## 1.3 `pve` Cannot Verify It

`pve`'s systemd is 252.39; it showed the header of this archive as `SEALED ???`, and verification stopped as follows.

⟦C2⟧

With systemd 255.4 on VM 230, verification of the same archive succeeds as follows.

⟦C3⟧

The journal key is not wrong and the file is not broken; it is a difference in systemd versions, and 252 cannot read the new format. So we create a VM dedicated to verification with systemd 255.

# Chapter 2: Creating VM 240 for Verification

## 2.1 Resources and the ISO

No settings are changed; read-only.

> **Run on: pve**

⟦C4⟧

⟦C5⟧

There are 64 CPU threads, about 101GiB of free memory, about 317GiB free on `local-lvm`, and an Ubuntu Server 24.04.5 ISO. To match VM 230's Ubuntu generation and systemd 255, we use Ubuntu 24.04.5.

## 2.2 Is VMID 240 Free?

> **Run on: pve**

⟦C6⟧

VMID 240 was not used by any VM or LXC.

## 2.3 Creating VM 240

| Item | Setting |
|---|---|
| VMID, name | 240, `fss-verification` |
| OS | Ubuntu Server 24.04.5 |
| CPU, memory | 2 vCPUs, 4GiB |
| Disk | 32GiB (`local-lvm`) |
| Network | `vmbr0` |

> **Run on: pve**

⟦C7⟧

The following warning appears at creation (no protection by thin pool autoextend, and total allocation exceeds actual capacity; the same state investigated in Part 41).

⟦C8⟧

## 2.4 Starting It and Installing the OS

> **Run on: pve**

⟦C9⟧

Install Ubuntu from **VM 240 → Console** in the Proxmox web interface. In the build records, it was installed with IP address `192.168.0.222`, with OpenSSH server installed and configured to accept connections.

## 2.5 Checking After Installation

> **Run on: VM 240**

⟦C10⟧

| Item | VM 230 | VM 240 |
|---|---|---|
| Ubuntu | 24.04 | 24.04.5 LTS |
| systemd | 255.4 | 255.4 |
| FSS verification option | supported | supported |
| IP address | `192.168.0.221` | `192.168.0.222` |

## 2.6 Checking SSH

> **Run on: VM 240**

⟦C11⟧

SSH is `active (running)` and listening on TCP 22, root's home is `root:root`, `700`, and there are no received files yet. We note the fingerprint of the ED25519 host key.

# Chapter 3: Moving to VM 240 and Checking

## 3.1 Checks on the `pve` Side

> **Run on: pve**

⟦C12⟧

The two source files (journal and verification key) are present, and the journal's SHA-256 is the same as at the previous transfer. VM 240's host key also matched the noted fingerprint.

## 3.2 Moving

Using the verified host key, we move them to `/home/ag/` of user `ag` on VM 240. When asked for a password, enter the password of `ag` on VM 240 (do not write it in chats or notes).

> **Run on: pve**

⟦C13⟧

Both files were moved with exit code `0`.

## 3.3 Confirming the Match on VM 240

> **Run on: VM 240**

⟦C14⟧

Both the journal and the verification key matched the SHA-256 of the original files on `pve` (journal 8MiB, key 44 bytes).

## 3.4 Placing Them in a Root-Only Location

> **Run on: VM 240**

⟦C15⟧

The journal and verification key were placed in `/root/` as `root:root`, `600`, and the hashes matched. The original files in `/home/ag/` are kept.

## 3.5 Checking on VM 240

> **Run on: VM 240**

⟦C16⟧

| Checked | Result |
|---|---|
| Checking host | VM 240 `192.168.0.222` (systemd 255.4) |
| Archive | `ARCHIVED`, `SEALED`, `SEALED_CONTINUOUS`, `Tag objects` 9 |
| Period checked | 2026-11-24 01:43:04 – 02:00:00 UTC |
| `journalctl --verify --verify-key` | `PASS` |

**On a host other than VM 230, FSS verification of the archive moved from VM 230 succeeded.**

# Chapter 4: Final Check in Three Places

## 4.1 VM 240

> **Run on: VM 240**

⟦C17⟧

As in the first verification, FSS verification passed again, and hashes, owner and permissions were unchanged.

## 4.2 `pve`

> **Run on: pve**

⟦C18⟧

The SHA-256 of the original journal and the verification key matched, and owner and permissions were unchanged (systemd 252 on `pve` cannot perform cryptographic verification).

## 4.3 VM 230

> **Run on: VM 230**

⟦C19⟧

| Place | Role | Result |
|---|---|---|
| VM 230 | origin | SHA-256 match, `SEALED`, `SEALED_CONTINUOUS`, `Tag objects` 9, verification exit code `0` |
| `pve` | storage | journal and key SHA-256 match; original unchanged |
| VM 240 | verification on another host | passed with systemd 255.4 |

# Closing Notes

In Part 65 we checked VM 230's FSS-sealed journal on another host (VM 240).

| Item | Result |
|---|---|
| Archive for verification | VM 230 → `pve` → VM 240, SHA-256 matching everywhere |
| `pve` | cannot verify this form of journal because of systemd 252 (storage only) |
| VM 240 | Ubuntu 24.04.5, systemd 255.4, 2 vCPUs, 4GiB, 32GiB, `192.168.0.222` |
| Verification on another host | passed |

In the next part, Part 66, we make this verification run automatically every 15 minutes.

---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 63: Moving the FSS Verification Key to the Proxmox Host"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 63 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". We move the FSS verification key created in Part 62 outside VM 230, to **`/root` on the Proxmox host `pve`** (root only).

1. Check the destination `pve` and the path from VM 230
2. Compare `pve`'s SSH host key with the value seen on its console, then register it on VM 230
3. On VM 230, create an SSH key used only for moving files to `pve`, and register the public key on `pve` with restrictions (`restrict`)
4. Move the verification key and confirm the match with SHA-256

Methods that disable SSH host key checking are not used.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **pve**: the Proxmox host (root). The Shell (console) of node `pve` in the Proxmox web interface

> **Caution:** Run the VM 230 commands only after checking that the prompt is `root@ai-defense-manager`. Running them on `pve` would check a connection to `pve` itself. Running them as an ordinary user (`aidefense`) fails because the root-only key cannot be read.

# Chapter 1: Destination and Path

## 1.1 The `pve` Side

> **Run on: pve**

⟦C0⟧

| Item | Result |
|---|---|
| `pve` IP address | `192.168.0.240` |
| VM 230 IP address | `192.168.0.221` |
| `pve` SSH | running, listening on TCP 22 |
| `/root` | `root:root`, `700` |

## 1.2 The VM 230 Side

> **Run on: VM 230**

⟦C1⟧

VM 230 reaches `pve` (`192.168.0.240`) directly. VM 230's root had no SSH key, and `pve`'s ED25519 host key was not registered in `known_hosts`.

# Chapter 2: Checking and Registering `pve`'s Host Key

## 2.1 Viewing the Fingerprint on the Console

As the trusted value, we take the fingerprint on `pve`'s console.

> **Run on: pve**

⟦C2⟧

## 2.2 Comparing with the Value Seen from VM 230

> **Run on: VM 230**

⟦C3⟧

The value seen on the console and the ED25519 fingerprint obtained over the network from VM 230 matched exactly.

> **Caution:** This script contains the fingerprint from the time of the build. In your own environment, replace it with the value seen in 2.1.

## 2.3 Registering in `known_hosts`

> **Run on: VM 230**

⟦C4⟧

We registered `pve`'s ED25519 host key in VM 230's `/root/.ssh/known_hosts` and compared again; it matched (directory `700`, file `600`).

# Chapter 3: The SSH Key for Moving Files

## 3.1 Creating the Key on VM 230

We create an Ed25519 key dedicated to VM 230. The secret key is kept in a root-only location on VM 230 and is neither displayed nor transferred.

> **Run on: VM 230**

⟦C5⟧

The secret key is `/root/.ssh/id_ed25519_pve_fss` (`600`), and the public key is `/root/.ssh/id_ed25519_pve_fss.pub`.

## 3.2 The Structure of `authorized_keys` on `pve`

> **Run on: pve**

⟦C6⟧

⟦C7⟧

`pve`'s SSH had `PermitRootLogin yes`, `PubkeyAuthentication yes` and `AuthorizedKeysFile .ssh/authorized_keys`, but `/root/.ssh/authorized_keys` was not an ordinary file; it was **a symbolic link to `/etc/pve/priv/authorized_keys`**. This file is managed by the Proxmox cluster file system (pmxcfs).

> **Run on: pve**

⟦C8⟧

`pve` was not a cluster using Corosync but a single-node configuration. `pve-cluster` is running normally, and `/etc/pve` is mounted by pmxcfs.

## 3.3 Registering the Public Key

We specify the link target `/etc/pve/priv/authorized_keys` directly and add the public key with `restrict` (restricting port forwarding, PTY and so on). The existing RSA key is kept.

> **Run on: pve**

⟦C9⟧

> **Caution:** `KEY_BLOB` and `KEY_LINE` in the script are the public key from the time of the build. In your own environment, replace them with the contents of the `.pub` created in 3.1. Using other methods intended to write to `/root/.ssh/authorized_keys` sometimes did not leave the key on the pmxcfs side.

We confirmed reading it back right after writing, the public key fingerprint match, reading it back through `/root/.ssh/authorized_keys`, and that the existing RSA key remains. No SSH configuration changes or restarts were made.

## 3.4 Testing Authentication

Run as root.

> **Run on: VM 230**

⟦C10⟧

`PVE_SSH_AUTH=PASS`, the target was `pve`, and the user was UID `0`.

# Chapter 4: Moving the Verification Key

We move the verification key, not the secret key. After moving, we compare permissions, owner and SHA-256 without displaying the contents.

> **Run on: VM 230**

⟦C11⟧

| Checked | Result |
|---|---|
| SSH public key authentication to `pve` | succeeded |
| Transfer of the verification key | succeeded |
| File on `pve` | `/root/fss-verification-key-20261124.txt`, `root:root`, `600` |
| SHA-256 | match |
| Original file on VM 230 | kept |

# Closing Notes

In Part 63 we stored the FSS verification key outside VM 230 (in `/root` on `pve`).

| Item | Result |
|---|---|
| `pve` host key | registered in `known_hosts` after comparing with the console value |
| Key for moving files | VM 230 `/root/.ssh/id_ed25519_pve_fss`; registered in `pve`'s `/etc/pve/priv/authorized_keys` with `restrict` |
| Verification key | `pve` `/root/fss-verification-key-20261124.txt` (`600`, SHA-256 match) |
| Still to do | have journald load the sealing key and confirm that sealing begins |

In the next part, Part 64, we start FSS sealing.

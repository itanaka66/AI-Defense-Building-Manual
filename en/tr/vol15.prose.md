---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 15: Passing the Relay Connection Details Safely to VM 230"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 15 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". We make the relay API (Relay), built on security-core (VM 220) in Part 14, usable from the AI Defense Manager (VM 230).

For VM 230 to call the Relay, it needs the following two things.

- The Relay's CA certificate (to verify the server certificate)
- The Bearer token (a secret)

We carry these two from VM 220 to VM 230 **using a temporary transfer-only account that can use SFTP only**, without enabling root SSH login. Once they have been carried over, the transfer account and its settings are all removed.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **VM 230**: ai-defense-manager (root)
- The contents of tokens and private keys appear neither on screen nor in this manual.

# Chapter 1: The Receiving Location on VM 230

## 1.1 The Configuration Directory

> **Run on: VM 230**

⟦C0⟧

At build time `/etc/ai-defense-manager` did not exist yet. Separately from the application itself (`/opt/ai-defense-manager`), create a directory to hold connection details.

⟦C1⟧

## 1.2 Checking the Run-As User

Check the dedicated user `ai-defense` that runs the AI Defense Manager.

⟦C2⟧

⟦C3⟧

At build time this was user `ai-defense` (UID 999), group `ai-defense` (GID 988), home `/opt/ai-defense-manager`, shell `/usr/sbin/nologin`.

## 1.3 The Directory for Connection Details

Make it `root:ai-defense` with `750` so that only the run-as user can read it.

⟦C4⟧

# Chapter 2: Verifying the SSH Host Key

Before connecting from VM 230 to VM 220 with SSH (SFTP), verify VM 220's host key through a separate path and then register it. We do not skip verification with `StrictHostKeyChecking=no`.

## 2.1 Showing the Fingerprint on VM 220

> **Run on: VM 220**

⟦C5⟧

## 2.2 Comparing with the Key Obtained on VM 230

> **Run on: VM 230**

⟦C6⟧

Confirm that it matches the ED25519 fingerprint (`SHA256:...`) shown in 2.1. If it matches, register it in `known_hosts`.

⟦C7⟧

Also confirm that VM 230 has no other usable SSH public keys.

⟦C8⟧

# Chapter 3: The Transfer-Only Account

## 3.1 A Dedicated User

> **Run on: VM 220**

⟦C9⟧

Create a user that cannot log in and whose password is locked. Only `incoming` inside the chroot is used for the transfer.

⟦C10⟧

Check the current SSH settings.

⟦C11⟧

Create the location for registering the public key.

⟦C12⟧

## 3.2 A Transfer-Only Key

> **Run on: VM 230**

Do not use an existing key; create an Ed25519 key used only for this transfer.

⟦C13⟧

Show only the public key (the private key is not shown).

⟦C14⟧

## 3.3 Registering the Public Key

> **Run on: VM 220**

Register the public key shown in 3.2. The public key in the following command is the one from the original build. **Replace it with the public key line shown in your own environment.**

⟦C15⟧

## 3.4 SSH Settings

> **Run on: VM 220**

⟦C16⟧

Add a `Match` block at the end that applies only to `ai-defense-transfer`. Other users' settings are not changed.

- `ChrootDirectory`: cannot leave `/srv/ai-defense-transfer`
- `ForceCommand internal-sftp`: SFTP only; no shell
- Public-key authentication only; no passwords
- Port forwarding, agent forwarding, X11 and tunnels are prohibited

⟦C17⟧

⟦C18⟧

Check the values that actually take effect when connecting from VM 230.

⟦C19⟧

The chroot directory must be owned by root and not writable.

⟦C20⟧

⟦C21⟧

Apply with a reload (re-reading the settings) rather than a restart. Existing SSH connections are not dropped.

⟦C22⟧

## 3.5 Permissions of the Public Key File

In the original build, connecting from VM 230 with SFTP in this state was rejected at public-key authentication. VM 220's SSH log recorded that the public key file could not be opened (`Could not open user 'ai-defense-transfer' authorized keys ... Permission denied`).

⟦C23⟧

`AuthorizedKeysFile` is read with that user's permissions. With `root:root` `600`, `ai-defense-transfer` cannot read it, so set the group to `ai-defense-transfer` and the permissions to `640`.

> **Run on: VM 220**

⟦C24⟧

## 3.6 Checking the SFTP Connection

> **Run on: VM 230**

⟦C25⟧

If it finishes without errors, the connection works.

# Chapter 4: Carrying the CA Certificate and Token

## 4.1 Placing Them in the Transfer Location

> **Run on: VM 220**

⟦C26⟧

## 4.2 Receiving Them on VM 230

> **Run on: VM 230**

⟦C27⟧

Place the received files as `root:ai-defense` with `640`, and delete what remains in `/root`.

⟦C28⟧

## 4.3 Confirming That the CA Certificate Is the Same

> **Run on: VM 230**

⟦C29⟧

> **Run on: VM 220**

⟦C30⟧

If both `subject` values (`CN = AI-Defense-Relay-Internal-CA`) and the SHA256 fingerprints match, it was carried over correctly.

# Chapter 5: Calling the Relay from VM 230

## 5.1 /health

> **Run on: VM 230**

Without showing the token's value, check HTTPS, CA verification and Bearer authentication.

⟦C31⟧

The result at build time was `HTTP_STATUS: 200`, `RESPONSE: {"status": "ok"}`.

## 5.2 /v1/alerts

Fetch five alerts from the last 60 minutes and show only the names of the fields returned.

⟦C32⟧

At build time five alerts were returned, and the fields of each alert were `agent.id`, `agent.name`, `decoder.name`, `location`, `manager.name`, `rule.description`, `rule.id`, `rule.level` and `timestamp`. The Relay returns the fields flat, with dotted names such as `rule.level`, so `RULE_FIELDS` and `AGENT_FIELDS` are empty. Fields with no value (`agent.ip` in this case) are not returned.

# Chapter 6: Removing the Transfer Account

The transfer is done, so clean up the whole temporary transfer mechanism.

## 6.1 Restoring the SSH Settings

> **Run on: VM 220**

⟦C33⟧

Take a backup and remove the `Match` block added in 3.4.

⟦C34⟧

⟦C35⟧

## 6.2 Deleting the User and Files

Confirm that no transfer sessions remain.

⟦C36⟧

⟦C37⟧

In the original build, `userdel` also removed the group, so `groupdel: group 'ai-defense-transfer' does not exist` was shown and the following `rm -rf` did not run. Check the state and delete the remaining directory.

⟦C38⟧

⟦C39⟧

## 6.3 Confirming That the Relay Is Still Running

⟦C40⟧

It is done if it is `active` and listening on `192.168.0.220:8765`.

# Closing Notes

In Part 15 we placed the following connection details on VM 230.

| File (VM 230) | Permissions | Contents |
|---|---|---|
| `/etc/ai-defense-manager/credentials/relay-ca.crt` | `root:ai-defense 640` | The Relay's CA certificate |
| `/etc/ai-defense-manager/credentials/relay-api.token` | `root:ai-defense 640` | Bearer token |

The transfer user, the key registration, the SSH settings and the directories have been removed (the key `/root/.ssh/ai-defense-transfer` on VM 230 remains). Also, automatic start (`enable`) for the Relay service has not been set up at this point.

In the next part, we bring alerts taken from the Relay into the AI Defense Manager and connect them to AI analysis.

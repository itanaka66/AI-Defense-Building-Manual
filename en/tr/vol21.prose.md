---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 21: Switching SSH on VM 230 to Public-Key Authentication"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 21 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". The checks in Part 20 showed that SSH on the AI Defense Manager (VM 230) allowed password login. Here we switch to public-key authentication using an existing key on the Windows PC used for administration, and then prohibit password authentication and root SSH login.

A mistake in the SSH settings can lock you out of the VM. Proceed while keeping to the following.

- Do not close VM 230's root console (the Proxmox console or similar) during the work
- Stop password authentication only after confirming that public-key login works
- Take a backup before changing settings
- Apply with a reload, not a restart

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root console)
  - **Windows**: the Windows PC used for administration (PowerShell)
- The contents of private keys appear neither on screen nor in chats. A public key's fingerprint is not secret.
- The Windows user folder in the original build is `C:\Users\HP ELITEBOOK`. Replace it with your own (many of the commands use `$env:USERPROFILE`, so they can be used as they are).

# Chapter 1: The Current State of SSH

> **Run on: VM 230**

⟦C0⟧

The values at build time were as follows.

| Setting | Value |
|---|---|
| `permitrootlogin` | `without-password` (root can log in with a public key) |
| `pubkeyauthentication` | `yes` |
| `passwordauthentication` | `yes` (to be changed) |
| `kbdinteractiveauthentication` | `no` |
| `authenticationmethods` | `any` |

Check whether the current shell is over SSH.

⟦C1⟧

At build time both were empty: it was a root shell entered from the VM console.

⟦C2⟧

The only line explicitly enabling password authentication was one in `/etc/ssh/sshd_config.d/50-cloud-init.conf` (`PasswordAuthentication yes`).

⟦C3⟧

In the log at build time, every login used password authentication. The current administrative connection depends on passwords, so it cannot be stopped right away.

## 1.1 The State of Public Key Registration

⟦C4⟧

⟦C5⟧

⟦C6⟧

The permissions (home 750, `.ssh` 700, `authorized_keys` 600) were correct, but `authorized_keys` was **0 bytes (empty)**. No public key had been registered yet.

# Chapter 2: Checking the Key on Windows

## 2.1 The Key Files

> **Run on: Windows** (PowerShell)

⟦C7⟧

At build time there was a PuTTY-format private key `rsa_private.ppk` and a public key `rsa_public`.

⟦C8⟧

`rsa_public` was not in OpenSSH format but in RFC4716 format (the SSH2 public key format). Without changing the private key, convert only the public key to OpenSSH format.

⟦C9⟧

At build time it was RSA 4096-bit with the fingerprint `SHA256:4dkitn2a46fogsJbEepnpQygeqyBXDFEtqkVylty0y0`.

## 2.2 PuTTYgen

`.ppk` is PuTTY's own format and cannot be read by Windows' standard `ssh-keygen`. To use PuTTYgen, install PuTTY (in an administrator PowerShell).

⟦C10⟧

With PuTTY 0.85 (Windows version), used at build time, the `-O` option of PuTTYgen's command line was not available, so use the GUI.

⟦C11⟧

1. Press **Load** and load `C:\Users\HP ELITEBOOK\.ssh\rsa_private.ppk` (enter the passphrase if there is one).
2. Confirm that the **Key fingerprint** shown matches the fingerprint from 2.1.

⟦C12⟧

If they match, `rsa_private.ppk` and `rsa_public` are the same key pair.

## 2.3 Saving and Converting the Public Key

Press **Save public key** in PuTTYgen and save it with the following name. **Do not press Save private key.**

⟦C13⟧

Convert the saved public key to OpenSSH format and check its fingerprint.

⟦C14⟧

The expected fingerprint is as follows.

⟦C15⟧

# Chapter 3: Registering the Public Key on VM 230

## 3.1 Sending the Public Key

> **Run on: Windows**

Only the public key is sent. When asked for a password, enter the password of `aidefense` on VM 230 (at this point the connection still uses a password).

⟦C16⟧

## 3.2 Checking the Fingerprint and Registering

> **Run on: VM 230**

⟦C17⟧

Confirm that the fingerprint is the same as on the Windows side. `authorized_keys` was empty, so replace it with this public key.

⟦C18⟧

⟦C19⟧

It is correct if the fingerprint matches, the file is `aidefense:aidefense` with `600`, and `.ssh` is `700`.

# Chapter 4: Logging In with the Public Key

## 4.1 Exporting the Private Key in OpenSSH Format

Windows' standard `ssh` cannot read `.ppk`. Without changing the original `.ppk`, export an OpenSSH-format private key from the PuTTYgen GUI.

1. In PuTTYgen, press **Load** and load `rsa_private.ppk`.
2. From the **Conversions** menu, choose **Export OpenSSH key**.
3. Save it with the following name (if asked for a passphrase, set and enter one).

⟦C20⟧

This `rsa_private_openssh` is a private key. Do not show its contents to anyone or send it.

> **Run on: Windows**

Without showing the contents, confirm only that the file exists and its fingerprint.

⟦C21⟧

## 4.2 Logging In with the Public Key Only

Connect with options that do not use password authentication.

⟦C22⟧

It has succeeded if `aidefense@ai-defense-manager:~$` is shown without being asked for a password.

# Chapter 5: Stopping Password Authentication and Root Login

## 5.1 The Order in Which Settings Are Read

> **Run on: VM 230**

⟦C23⟧

⟦C24⟧

`/etc/ssh/sshd_config` includes `sshd_config.d/*.conf`, and `50-cloud-init.conf` among them sets `PasswordAuthentication yes`. When the same option appears more than once, OpenSSH in principle uses **the first value it reads**. So create a new `00-local-hardening.conf`, which is read before `50-cloud-init.conf`. `50-cloud-init.conf` is not changed.

## 5.2 Backup

⟦C25⟧

⟦C26⟧

⟦C27⟧

## 5.3 The Configuration File

| Setting | Now | After the change |
|---|---|---|
| `PermitRootLogin` | `without-password` | `no` |
| `PasswordAuthentication` | `yes` | `no` |
| `PubkeyAuthentication` | `yes` | `yes` |
| `KbdInteractiveAuthentication` | `no` | `no` |

⟦C28⟧

⟦C29⟧

⟦C30⟧

Before the reload, check the values that will actually take effect.

⟦C31⟧

⟦C32⟧

## 5.4 Applying

A reload does not restart SSH; it only re-reads the settings. Keep the root console and the connection from Windows open.

⟦C33⟧

⟦C34⟧

If it is `active (running)`, the change has been applied.

## 5.5 Checking with a New Connection

> **Run on: Windows** (a new PowerShell window)

⟦C35⟧

Always run this command in Windows PowerShell (`PS C:\Users\...>`). In the original build it was run by mistake in the window still logged in to VM 230 (`aidefense@ai-defense-manager:~$`), where `$env:USERPROFILE` cannot be used, and it failed. In that case, return to Windows with `exit` and then run it.

It is done when the following prompt appears without being asked for a password.

⟦C36⟧

# Chapter 6: Checking the SSH Log

> **Run on: VM 230**

⟦C37⟧

At build time there were six password logins before the switch, one failed login with a nonexistent user name (`aidefence`, a misspelling), and two public-key logins after the switch. After the switch there were no successful password logins.

# Closing Notes

In Part 21 we put SSH on VM 230 into the following state.

| Item | State |
|---|---|
| Public-key authentication | Enabled (the existing RSA 4096-bit key on Windows) |
| Password authentication | Disabled |
| Root SSH login | Prohibited |
| Keyboard-interactive authentication | Disabled |
| Configuration file | `/etc/ssh/sshd_config.d/00-local-hardening.conf` |
| Backup | `/root/ssh-config-backup-20261121` |

In the next part, we check the settings and permissions of the Relay and Wazuh Indexer.

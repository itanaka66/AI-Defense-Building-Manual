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

```bash
sshd -T | grep -E '^(permitrootlogin|passwordauthentication|pubkeyauthentication|kbdinteractiveauthentication|authenticationmethods|allowusers|denyusers) '
```

The values at build time were as follows.

| Setting | Value |
|---|---|
| `permitrootlogin` | `without-password` (root can log in with a public key) |
| `pubkeyauthentication` | `yes` |
| `passwordauthentication` | `yes` (to be changed) |
| `kbdinteractiveauthentication` | `no` |
| `authenticationmethods` | `any` |

Check whether the current shell is over SSH.

```bash
printf 'SSH_CONNECTION=%s\n' "$SSH_CONNECTION"; printf 'SSH_CLIENT=%s\n' "$SSH_CLIENT"; id
```

At build time both were empty: it was a root shell entered from the VM console.

```bash
grep -RniE '^[[:space:]]*(PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|AuthenticationMethods|AllowUsers|DenyUsers)[[:space:]]+' /etc/ssh/sshd_config /etc/ssh/sshd_config.d 2>/dev/null
```

The only line explicitly enabling password authentication was one in `/etc/ssh/sshd_config.d/50-cloud-init.conf` (`PasswordAuthentication yes`).

```bash
journalctl -u ssh.service --since "24 hours ago" --no-pager | grep -Ei 'Accepted|Failed|Invalid user|authentication failure|Connection closed' | tail -30
```

In the log at build time, every login used password authentication. The current administrative connection depends on passwords, so it cannot be stopped right away.

## 1.1 The State of Public Key Registration

```bash
stat -c '%A (%a) %U:%G %n' /home/aidefense /home/aidefense/.ssh /home/aidefense/.ssh/authorized_keys 2>&1
```

```bash
ssh-keygen -lf /home/aidefense/.ssh/authorized_keys
```

```bash
wc -l -c /home/aidefense/.ssh/authorized_keys && awk '{print "LINE", NR, "FIELD1=" $1, "LENGTH=" length($0)}' /home/aidefense/.ssh/authorized_keys
```

The permissions (home 750, `.ssh` 700, `authorized_keys` 600) were correct, but `authorized_keys` was **0 bytes (empty)**. No public key had been registered yet.

# Chapter 2: Checking the Key on Windows

## 2.1 The Key Files

> **Run on: Windows** (PowerShell)

```powershell
Get-ChildItem "$env:USERPROFILE\.ssh" -Force | Select-Object Name, Length
```

At build time there was a PuTTY-format private key `rsa_private.ppk` and a public key `rsa_public`.

```powershell
Get-Content "$env:USERPROFILE\.ssh\rsa_public" -TotalCount 1
```

`rsa_public` was not in OpenSSH format but in RFC4716 format (the SSH2 public key format). Without changing the private key, convert only the public key to OpenSSH format.

```powershell
$converted = ssh-keygen -i -m RFC4716 -f "$env:USERPROFILE\.ssh\rsa_public"; if ($LASTEXITCODE -eq 0) { [System.IO.File]::WriteAllText("$env:USERPROFILE\.ssh\rsa_public_openssh", $converted + [Environment]::NewLine, [System.Text.Encoding]::ASCII); ssh-keygen -lf "$env:USERPROFILE\.ssh\rsa_public_openssh" }
```

At build time it was RSA 4096-bit with the fingerprint `SHA256:4dkitn2a46fogsJbEepnpQygeqyBXDFEtqkVylty0y0`.

## 2.2 PuTTYgen

`.ppk` is PuTTY's own format and cannot be read by Windows' standard `ssh-keygen`. To use PuTTYgen, install PuTTY (in an administrator PowerShell).

```powershell
winget install --id PuTTY.PuTTY --exact --source winget
```

With PuTTY 0.85 (Windows version), used at build time, the `-O` option of PuTTYgen's command line was not available, so use the GUI.

```powershell
Start-Process "C:\Program Files\PuTTY\puttygen.exe"
```

1. Press **Load** and load `C:\Users\HP ELITEBOOK\.ssh\rsa_private.ppk` (enter the passphrase if there is one).
2. Confirm that the **Key fingerprint** shown matches the fingerprint from 2.1.

```text
SHA256:4dkitn2a46fogsJbEepnpQygeqyBXDFEtqkVylty0y0
```

If they match, `rsa_private.ppk` and `rsa_public` are the same key pair.

## 2.3 Saving and Converting the Public Key

Press **Save public key** in PuTTYgen and save it with the following name. **Do not press Save private key.**

```text
C:\Users\HP ELITEBOOK\.ssh\rsa_private_derived_ssh2.pub
```

Convert the saved public key to OpenSSH format and check its fingerprint.

```powershell
$src="$env:USERPROFILE\.ssh\rsa_private_derived_ssh2.pub"; $dst="$env:USERPROFILE\.ssh\rsa_private_derived.pub"; if (Test-Path $src) { $key=ssh-keygen -i -m RFC4716 -f $src; if ($LASTEXITCODE -eq 0) { [System.IO.File]::WriteAllText($dst,$key+[Environment]::NewLine,[System.Text.Encoding]::ASCII); ssh-keygen -lf $dst } } else { Write-Host "公開鍵ファイルが見つかりません: $src" }
```

The expected fingerprint is as follows.

```text
SHA256:4dkitn2a46fogsJbEepnpQygeqyBXDFEtqkVylty0y0
```

# Chapter 3: Registering the Public Key on VM 230

## 3.1 Sending the Public Key

> **Run on: Windows**

Only the public key is sent. When asked for a password, enter the password of `aidefense` on VM 230 (at this point the connection still uses a password).

```powershell
scp "$env:USERPROFILE\.ssh\rsa_private_derived.pub" aidefense@192.168.0.33:/tmp/aidefense_rsa_public.pub
```

## 3.2 Checking the Fingerprint and Registering

> **Run on: VM 230**

```bash
ssh-keygen -lf /tmp/aidefense_rsa_public.pub && stat -c 'Owner=%U:%G Mode=%a Size=%s' /tmp/aidefense_rsa_public.pub
```

Confirm that the fingerprint is the same as on the Windows side. `authorized_keys` was empty, so replace it with this public key.

```bash
install -o aidefense -g aidefense -m 600 /tmp/aidefense_rsa_public.pub /home/aidefense/.ssh/authorized_keys
```

```bash
ssh-keygen -lf /home/aidefense/.ssh/authorized_keys && stat -c 'Owner=%U:%G Mode=%a Size=%s' /home/aidefense/.ssh/authorized_keys && namei -l /home/aidefense/.ssh/authorized_keys
```

It is correct if the fingerprint matches, the file is `aidefense:aidefense` with `600`, and `.ssh` is `700`.

# Chapter 4: Logging In with the Public Key

## 4.1 Exporting the Private Key in OpenSSH Format

Windows' standard `ssh` cannot read `.ppk`. Without changing the original `.ppk`, export an OpenSSH-format private key from the PuTTYgen GUI.

1. In PuTTYgen, press **Load** and load `rsa_private.ppk`.
2. From the **Conversions** menu, choose **Export OpenSSH key**.
3. Save it with the following name (if asked for a passphrase, set and enter one).

```text
C:\Users\HP ELITEBOOK\.ssh\rsa_private_openssh
```

This `rsa_private_openssh` is a private key. Do not show its contents to anyone or send it.

> **Run on: Windows**

Without showing the contents, confirm only that the file exists and its fingerprint.

```powershell
$key="$env:USERPROFILE\.ssh\rsa_private_openssh"; if (Test-Path $key) { Get-Item $key | Select-Object Name,Length; ssh-keygen -lf $key } else { Write-Host "秘密鍵ファイルがまだありません: $key" }
```

## 4.2 Logging In with the Public Key Only

Connect with options that do not use password authentication.

```powershell
ssh -i "$env:USERPROFILE\.ssh\rsa_private_openssh" -o IdentitiesOnly=yes -o PreferredAuthentications=publickey -o PasswordAuthentication=no aidefense@192.168.0.33
```

It has succeeded if `aidefense@ai-defense-manager:~$` is shown without being asked for a password.

# Chapter 5: Stopping Password Authentication and Root Login

## 5.1 The Order in Which Settings Are Read

> **Run on: VM 230**

```bash
sshd -T | grep -E '^(permitrootlogin|pubkeyauthentication|passwordauthentication|kbdinteractiveauthentication|authenticationmethods|allowusers|allowgroups|authorizedkeysfile) '
```

```bash
grep -nE '^[[:space:]]*(Include|PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|KbdInteractiveAuthentication|AuthenticationMethods)' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf 2>/dev/null
```

`/etc/ssh/sshd_config` includes `sshd_config.d/*.conf`, and `50-cloud-init.conf` among them sets `PasswordAuthentication yes`. When the same option appears more than once, OpenSSH in principle uses **the first value it reads**. So create a new `00-local-hardening.conf`, which is read before `50-cloud-init.conf`. `50-cloud-init.conf` is not changed.

## 5.2 Backup

```bash
ls -ld /root/ssh-config-backup-20261121 /etc/ssh/sshd_config /etc/ssh/sshd_config.d/50-cloud-init.conf
```

```bash
install -d -o root -g root -m 700 /root/ssh-config-backup-20261121 && cp -a /etc/ssh/sshd_config /etc/ssh/sshd_config.d /root/ssh-config-backup-20261121/
```

```bash
diff -r /etc/ssh/sshd_config /root/ssh-config-backup-20261121/sshd_config && diff -r /etc/ssh/sshd_config.d /root/ssh-config-backup-20261121/sshd_config.d && echo "SSH_CONFIG_BACKUP_VERIFY_OK"
```

## 5.3 The Configuration File

| Setting | Now | After the change |
|---|---|---|
| `PermitRootLogin` | `without-password` | `no` |
| `PasswordAuthentication` | `yes` | `no` |
| `PubkeyAuthentication` | `yes` | `yes` |
| `KbdInteractiveAuthentication` | `no` | `no` |

```bash
cat > /etc/ssh/sshd_config.d/00-local-hardening.conf <<'EOF'
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
KbdInteractiveAuthentication no
EOF
```

```bash
chown root:root /etc/ssh/sshd_config.d/00-local-hardening.conf && chmod 600 /etc/ssh/sshd_config.d/00-local-hardening.conf && stat -c 'Owner=%U:%G Mode=%a' /etc/ssh/sshd_config.d/00-local-hardening.conf && sshd -t && echo "SSHD_CONFIG_SYNTAX_OK"
```

```text
Owner=root:root Mode=600
SSHD_CONFIG_SYNTAX_OK
```

Before the reload, check the values that will actually take effect.

```bash
sshd -T | grep -E '^(permitrootlogin|pubkeyauthentication|passwordauthentication|kbdinteractiveauthentication|authenticationmethods) '
```

```text
permitrootlogin no
pubkeyauthentication yes
passwordauthentication no
kbdinteractiveauthentication no
authenticationmethods any
```

## 5.4 Applying

A reload does not restart SSH; it only re-reads the settings. Keep the root console and the connection from Windows open.

```bash
systemctl reload ssh.service && systemctl is-active ssh.service
```

```bash
systemctl is-active ssh.service && systemctl status ssh.service --no-pager -l
```

If it is `active (running)`, the change has been applied.

## 5.5 Checking with a New Connection

> **Run on: Windows** (a new PowerShell window)

```powershell
ssh -i "$env:USERPROFILE\.ssh\rsa_private_openssh" -o IdentitiesOnly=yes -o PreferredAuthentications=publickey -o PasswordAuthentication=no aidefense@192.168.0.33
```

Always run this command in Windows PowerShell (`PS C:\Users\...>`). In the original build it was run by mistake in the window still logged in to VM 230 (`aidefense@ai-defense-manager:~$`), where `$env:USERPROFILE` cannot be used, and it failed. In that case, return to Windows with `exit` and then run it.

It is done when the following prompt appears without being asked for a password.

```text
aidefense@ai-defense-manager:~$
```

# Chapter 6: Checking the SSH Log

> **Run on: VM 230**

```bash
journalctl -u ssh.service --since "24 hours ago" --no-pager | grep -Ei 'Accepted|Failed|Invalid user|authentication failure|Connection closed|Disconnected|maximum authentication attempts'
```

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

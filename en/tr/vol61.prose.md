---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 61: Checking Logs for Secrets and Capping the Journal Size"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 61 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 60 we checked API error responses and log permissions. Here we do the following.

1. Check, by counts only, whether token-like strings remain in syslog and the journal
2. Examine the journal's retention period and growth, decide a size limit and set it
3. Restart journald to apply the settings, and check the integrity of the journal
4. Check log management as a whole: journald, rsyslog and logrotate

Log bodies are not displayed. Existing logs are not deleted.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: Do Secrets Remain in the Logs?

## 1.1 The Current syslog and auth.log

We count only the number of matches.

> **Run on: VM 230**

⟦C0⟧

Matches for token and secret patterns were **0**, and the test string `VALIDATION_SECRET_MARKER` also had 0. There are 14,184 AI Defense-related entries in syslog and 830 in auth.log, but that does not mean they contain secrets.

## 1.2 Rotated Logs

> **Run on: VM 230**

⟦C1⟧

| Target | Token patterns | Test string |
|---|---:|---:|
| syslog | 0 | 0 |
| syslog.1 | 0 | 0 |
| auth.log | 0 | 0 |
| auth.log.1 | 0 | 0 |

## 1.3 The Journal

> **Run on: VM 230**

⟦C2⟧

The journal also had 0 matches. It uses 89.0MB, and the file system has 39GB free (15% used). We cannot say that secrets in unknown forms, other than the patterns checked, are absent.

# Chapter 2: Journal Settings and Retention

## 2.1 The Current Settings

> **Run on: VM 230**

⟦C3⟧

| Setting | Now |
|---|---|
| Storage | `auto` (default) |
| Compress | `yes` (default) |
| Seal | `yes` (default) |
| SystemMaxUse | not specified |
| SystemKeepFree | not specified |
| SystemMaxFiles | default 100 |
| MaxRetentionSec | not specified |

The size limit had not been explicitly decided and was left to systemd's defaults.

## 2.2 Storage State and Integrity

> **Run on: VM 230**

⟦C4⟧

Persistent storage is `/var/log/journal`, with 17 files (one `.journal~` from an abnormal termination), all `root:systemd-journal`, `640`, and all files shown passed the integrity check. `Unused data (entry_offset==0)` is a notice that there is unused data, not a sign of corruption.

## 2.3 How Many Days Are Kept

> **Run on: VM 230**

⟦C5⟧

⟦C6⟧

| Item | Result |
|---|---|
| Oldest entry | 2026-11-20 07:38:48 UTC |
| Newest entry | 2026-11-23 23:10:13 UTC |
| Period | about 4 days |
| Number of entries | 46,133 |
| Boot history | 11 |
| Space used | 89MB |

# Chapter 3: Setting the Size Limit

## 3.1 Checking Before the Change

> **Run on: VM 230**

⟦C7⟧

systemd is 255.4 and supports the settings we use. There is no local drop-in and no size setting yet. `systemd-journald.service` has `Restart=always`, but restarting to apply the settings is decided separately. The values decided are as follows.

⟦C8⟧

## 3.2 Adding the Configuration File

No deletion or change of existing logs, and no restart or reload of journald.

> **Run on: VM 230**

⟦C9⟧

| Setting | Effective value |
|---|---:|
| `SystemMaxUse` | 512MB |
| `SystemKeepFree` | 2GB |
| `SystemMaxFileSize` | 64MB |

The file is `/etc/systemd/journald.conf.d/60-ai-defense-retention.conf` (`root:root`, `644`). journald's PID has not changed (not yet applied to the running process).

## 3.3 Checks Before Applying

> **Run on: VM 230**

⟦C10⟧

The current usage of 89.0MB is well below the 512MB limit, so applying it will not immediately delete old logs.

## 3.4 Restarting journald

Log collection may be affected briefly. No deletion of existing logs (vacuum) or configuration changes.

> **Run on: VM 230**

⟦C11⟧

| Item | Result |
|---|---|
| Restart | succeeded (status 0) |
| New MainPID | `2572` |
| State | `active (running)`, Result `success`, NRestarts 0 |
| Limit, free space, file limit | 512MB, 2GB, 64MB |
| Journal startup record | present |

## 3.5 Integrity After the Restart

> **Run on: VM 230**

⟦C12⟧

| Checked | Result |
|---|---:|
| Journal files passing the check | 18 |
| Journal files failing the check | 0 |
| `Unused data` notices | 31 |
| journald errors and warnings | 0 |
| AI Defense Manager | `active (running)`, 0 restarts, `/health` `HTTP 200` |

# Chapter 4: Log Management as a Whole

## 4.1 Storage Locations and logrotate

> **Run on: VM 230**

⟦C13⟧

`/var/log/journal` and `/run/log/journal` are `root:systemd-journal`, `2755`, journal files are `640`, and there was no logrotate setting that touches the journal directly.

## 4.2 Size and Retention Period

> **Run on: VM 230**

⟦C14⟧

⟦C15⟧

| Item | Result |
|---|---|
| Oldest entry | 2026-11-20 07:38:48 UTC |
| Newest entry | 2026-11-23 23:17:01 UTC |
| Period | about 3 days 15 hours 38 minutes |
| Free disk space | 39GB |
| inode usage | 4% |

## 4.3 logrotate

> **Run on: VM 230**

⟦C16⟧

⟦C17⟧

| Item | Result |
|---|---|
| logrotate | 3.21.0 |
| Cycle and generations | weekly, 4 generations |
| Compression | gzip, `delaycompress` |
| Empty logs | not rotated |
| rsyslog targets | 6 kinds; rsyslog notified in postrotate |
| Duplicate definitions | none |
| Log owner and permissions | `syslog:adm`, `640` |

## 4.4 rsyslog

> **Run on: VM 230**

⟦C18⟧

rsyslog was `active (running)` (MainPID `774`, 0 restarts, user `syslog`), the `rsyslogd -N1` syntax check passed, forwarding from journald (`ForwardToSyslog=yes`) and the split between auth.log and syslog were normal, and there were no errors.

# Closing Notes

In Part 61 we confirmed that no secrets remain in the logs and set a size limit for the journal.

| Item | Result |
|---|---|
| Checking logs for secrets | 0 matches in syslog, auth.log and the journal |
| Journal limits | `SystemMaxUse=512M`, `SystemKeepFree=2G`, `SystemMaxFileSize=64M` (`60-ai-defense-retention.conf`) |
| Applying | journald restarted; integrity check: 18 passed, 0 failed |
| syslog | weekly, 4 generations, compressed, `syslog:adm`, `640` |

The journald settings showed `Seal=yes` (default), but whether a sealing key is actually in use is checked in the next part, Part 62. This is to make log tampering detectable.

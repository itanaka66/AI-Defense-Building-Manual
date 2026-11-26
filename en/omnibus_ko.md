---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Omnibus Edition: Parts 31–44"
author: "Isamu Tanaka"
lang: en-US
---

# About Volume 3

This book collects Volume 3 (Parts 31–44) of the "AI Autonomous Cyber Defense System Build Manual" in a single omnibus edition. It keeps the Collector fixed in Volume 2 from stopping when Wazuh switches its logs and recovers the events that were missing. It then makes the state of the Collector and the Wazuh platform observable with Prometheus and tests the alert rules, checks the PostgreSQL that stores the events, prepares TrueNAS as the backup destination, and completes scheduled backups (logical, LXC and ZFS snapshots), isolated restore tests, and handling of failures after a reboot.

It assumes the same environment as Volumes 1 and 2 (Proxmox, VM 220 security-core, LXC 109 PostgreSQL and so on). For the underlying configuration and procedures, see Volumes 1 and 2.

## Downloading the Scripts

The scripts used in this book can be downloaded from:

https://github.com/itanaka66/AI-Defense-Building-Manual/releases

## Volumes and Parts

Because the build records are long, this manual is divided into the following four volumes. Part numbers run continuously across volumes.

| Volume | Parts | Main topics |
|---|---|---|
| Volume 1 | Parts 1–23 | Defense foundation (Wazuh, Collector, PostgreSQL, monitoring), AI Defense Manager, a search user for Wazuh, the relay API (Relay), AI analysis and its protection, checks |
| Volume 2 | Parts 24–30 | Enabling and verifying the Wazuh Indexer audit log; checking, recovering and preventing recurrence for the Collector |
| Volume 3 | Parts 31–44 | Handling log switching and recovering missing events, monitoring with Prometheus and testing the rules, checking PostgreSQL, backups (logical, LXC, ZFS snapshots) and restore testing, the TrueNAS destination, handling failures after a reboot |
| Volume 4 | Parts 45–71 | Safe input and output for LLM analysis (allowlists, masking, approval policy), integration with the Relay, API token authentication, checking errors and logs, detecting log tampering (FSS), repairing Wazuh local rules, AI defense agents |

**Volume 1**

| Part | Title |
|---|---|
| Part 1 | Building the Defense Foundation and Monitoring with Wazuh |
| Part 2 | Safely Monitoring PostgreSQL Logs and Correlation Detection |
| Part 3 | Building the Alert-Storage Collector |
| Part 4 | Auditing the Collector and Developing a Hardened Version |
| Part 5 | Deploying the Hardened Collector to Production |
| Part 6 | Verifying Data Integrity and Auditing Operations |
| Part 7 | Finishing the Collector's Fault Tolerance |
| Part 8 | Building the Integrated Monitoring Platform |
| Part 9 | Recovering from a Collector Stop and Checking Operations |
| Part 10 | Handling a Disk Failure and Preparing the AI Defense Manager |
| Part 11 | Laying the Groundwork for the AI Defense Manager |
| Part 12 | Investigating the AI Analysis Service and Wazuh Integration |
| Part 13 | A Read-Only User for Wazuh Indexer |
| Part 14 | Building the Alert Relay API (Relay) |
| Part 15 | Passing the Relay Connection Details Safely to VM 230 |
| Part 16 | Connecting Wazuh Alerts to AI Analysis |
| Part 17 | Running the AI Defense Manager as a Service and Its Startup Order |
| Part 18 | Keeping the Analysis History in SQLite |
| Part 19 | Minimizing the Information Passed to the LLM |
| Part 20 | Fixing Confidence Scores and Protecting Stored Data |
| Part 21 | Switching SSH on VM 230 to Public-Key Authentication |
| Part 22 | Checking the Relay and Its Connection Details |
| Part 23 | Investigating Indexer Permissions and the Audit Log |

**Volume 2**

| Part | Title |
|---|---|
| Part 24 | Finding Out Why the Audit Log Is Not Saved |
| Part 25 | Setting Where the Audit Log Is Saved |
| Part 26 | Not Recording Request Bodies in the Audit Log |
| Part 27 | Confirming That the Audit Log Is Saved |
| Part 28 | Checking the Collector and Why It Stopped |
| Part 29 | Restarting the Collector Without Missing Any Events |
| Part 30 | Keeping the Collector from Stopping for the Same Reason |

**Volume 3**

| Part | Title |
|---|---|
| Part 31 | Why the Collector Cannot Read After Log Switching, and the Fix |
| Part 32 | Confirming an Actual Switch and Recovering Missing Events |
| Part 33 | Monitoring the Collector's State with Prometheus |
| Part 34 | Monitoring the Wazuh Platform's State with Prometheus |
| Part 35 | Testing the Alert Rules and Checking in Production |
| Part 36 | Checking PostgreSQL |
| Part 37 | Backing Up PostgreSQL and Testing a Restore |
| Part 38 | Using TrueNAS as the Backup Destination |
| Part 39 | Registering the Destination and Preparing Scheduled Backups |
| Part 40 | Completing the PostgreSQL Logical Backup |
| Part 41 | Backing Up LXC 109 and Testing an Isolated Restore |
| Part 42 | Protecting the Backups and TrueNAS Snapshots |
| Part 43 | Backup Failures After a Reboot and the Recovery |
| Part 44 | Comparing the Restored Databases with Production |

**Volume 4**

| Part | Title |
|---|---|
| Part 45 | Preparing for LLM Analysis and Repairing the Wazuh Configuration File |
| Part 46 | Classifying Alerts and Deciding Which Fields to Pass to the LLM |
| Part 47 | Examining the Existing AI Defense Manager Implementation |
| Part 48 | Narrowing the Wazuh Event Conversion to Seven Fields |
| Part 49 | Narrowing the Fields Returned by the Relay to Seven |
| Part 50 | Deploying the New Code and a Static Address for VM 230 |
| Part 51 | Verifying TLS and Authentication from VM 230 to the Relay |
| Part 52 | Fetching Real Alerts and Fixing the Relay's 502 |
| Part 53 | Checking the Flow from Analysis to Storage |
| Part 54 | Masking LLM Output and the Approval Policy |
| Part 55 | Integration Checks and Preparing for High Request Volumes |
| Part 56 | Reviewing and Designing API Authentication |
| Part 57 | Building Token Authentication for the API |
| Part 58 | Hardening Token Handling and the CLI |
| Part 59 | Putting API Authentication into Production |
| Part 60 | Keeping Error Responses and Logs from Leaking Information |
| Part 61 | Checking Logs for Secrets and Capping the Journal Size |
| Part 62 | Creating FSS Keys to Guard Against Log Tampering |
| Part 63 | Moving the FSS Verification Key to the Proxmox Host |
| Part 64 | Running and Checking FSS Sealing |
| Part 65 | Checking FSS from Another Host (VM 240) |
| Part 66 | Automating FSS Verification Every 15 Minutes |
| Part 67 | Finding the Breakage in Wazuh's Local Rules |
| Part 68 | Testing the Fixed Rules in an Isolated Environment |
| Part 69 | Putting the Fixed Rules into Production |
| Part 70 | Starting to Build the AI Defense Agents |
| Part 71 | Correlation, Orchestration and Defense Decision Agents |


# Part 31: Why the Collector Cannot Read After Log Switching, and the Fix
## Introduction

### About This Book

This is Part 31 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". At the end of Part 30 in Volume 2, after checking how the Collector reads, we began to investigate how Wazuh's alert logs are switched (rotated). Continuing from there, this part does the following.

1. Find out, using reads only, when and how Wazuh's alert logs are switched
2. Find out why, after the switch on November 21, the Collector could not open the new file and kept reporting `PermissionError`
3. Add a **Default ACL** (an ACL inherited by newly created files and directories) to the per-date directories (`2026`, `2026/Nov`)
4. Test with temporary files that the ACL is inherited, and record the state before an actual switch

The cause turned out to be as follows.

- Alert files are created per date, such as `alerts/2026/Nov/ossec-alerts-21.json`, and `alerts.json` is a hard link to that file (the same inode)
- `/var/ossec/logs/alerts` had a Default ACL, but `2026` and `2026/Nov` below it did not
- So when the date changed and a new file was created, the Collector's user (`wazuh-collector`) was not given read permission on it

### About Volume 3

Volume 3 starts with this book. In Volume 2 (Parts 24–30), we got the Wazuh Indexer audit log working and fixed a Collector stop. In Volume 3, we keep the Collector from stopping at log switching and make the Collector and the Wazuh platform observable with Prometheus. We then check the PostgreSQL that stores the events, and build backups (logical, LXC and ZFS snapshots), a place to keep them (TrueNAS) and restore tests.

| Part | Content |
|---|---|
| Part 31 | Why the Collector cannot read after log switching, and the fix |
| Part 32 | Confirming an actual switch and recovering missing events |
| Part 33 | Monitoring the Collector's state with Prometheus |
| Part 34 | Monitoring the Wazuh platform's state with Prometheus |
| Part 35 | Testing the alert rules and checking in production |
| Part 36 | Checking PostgreSQL |
| Part 37 | Backing up PostgreSQL and testing a restore |
| Part 38 | Using TrueNAS as the backup destination |
| Part 39 | Registering the destination and preparing scheduled backups |
| Part 40 | Completing the PostgreSQL logical backup |
| Part 41 | Backing up LXC 109 and testing an isolated restore |
| Part 42 | Protecting the backups and TrueNAS snapshots |
| Part 43 | Backup failures after a reboot and the recovery |
| Part 44 | Comparing the restored databases with production |

It assumes the same environment as Volumes 1 and 2 (Proxmox, VM 220 security-core, LXC 109 PostgreSQL and so on). For adapting it to ordinary PCs, see "Building with Ordinary PCs" in Part 1 of Volume 1.


### Volumes and Parts

Because the build records are long, this manual is divided into the following four volumes. Part numbers run continuously across volumes.

| Volume | Parts | Main topics |
|---|---|---|
| Volume 1 | Parts 1–23 | Defense foundation (Wazuh, Collector, PostgreSQL, monitoring), AI Defense Manager, a search user for Wazuh, the relay API (Relay), AI analysis and its protection, checks |
| Volume 2 | Parts 24–30 | Enabling and verifying the Wazuh Indexer audit log; checking, recovering and preventing recurrence for the Collector |
| Volume 3 | Parts 31–44 | Handling log switching and recovering missing events, monitoring with Prometheus and testing the rules, checking PostgreSQL, backups (logical, LXC, ZFS snapshots) and restore testing, the TrueNAS destination, handling failures after a reboot |
| Volume 4 | Parts 45–71 | Safe input and output for LLM analysis (allowlists, masking, approval policy), integration with the Relay, API token authentication, checking errors and logs, detecting log tampering (FSS), repairing Wazuh local rules, AI defense agents |

**Volume 1**

| Part | Title |
|---|---|
| Part 1 | Building the Defense Foundation and Monitoring with Wazuh |
| Part 2 | Safely Monitoring PostgreSQL Logs and Correlation Detection |
| Part 3 | Building the Alert-Storage Collector |
| Part 4 | Auditing the Collector and Developing a Hardened Version |
| Part 5 | Deploying the Hardened Collector to Production |
| Part 6 | Verifying Data Integrity and Auditing Operations |
| Part 7 | Finishing the Collector's Fault Tolerance |
| Part 8 | Building the Integrated Monitoring Platform |
| Part 9 | Recovering from a Collector Stop and Checking Operations |
| Part 10 | Handling a Disk Failure and Preparing the AI Defense Manager |
| Part 11 | Laying the Groundwork for the AI Defense Manager |
| Part 12 | Investigating the AI Analysis Service and Wazuh Integration |
| Part 13 | A Read-Only User for Wazuh Indexer |
| Part 14 | Building the Alert Relay API (Relay) |
| Part 15 | Passing the Relay Connection Details Safely to VM 230 |
| Part 16 | Connecting Wazuh Alerts to AI Analysis |
| Part 17 | Running the AI Defense Manager as a Service and Its Startup Order |
| Part 18 | Keeping the Analysis History in SQLite |
| Part 19 | Minimizing the Information Passed to the LLM |
| Part 20 | Fixing Confidence Scores and Protecting Stored Data |
| Part 21 | Switching SSH on VM 230 to Public-Key Authentication |
| Part 22 | Checking the Relay and Its Connection Details |
| Part 23 | Investigating Indexer Permissions and the Audit Log |

**Volume 2**

| Part | Title |
|---|---|
| Part 24 | Finding Out Why the Audit Log Is Not Saved |
| Part 25 | Setting Where the Audit Log Is Saved |
| Part 26 | Not Recording Request Bodies in the Audit Log |
| Part 27 | Confirming That the Audit Log Is Saved |
| Part 28 | Checking the Collector and Why It Stopped |
| Part 29 | Restarting the Collector Without Missing Any Events |
| Part 30 | Keeping the Collector from Stopping for the Same Reason |

**Volume 3**

| Part | Title |
|---|---|
| Part 31 | Why the Collector Cannot Read After Log Switching, and the Fix |
| Part 32 | Confirming an Actual Switch and Recovering Missing Events |
| Part 33 | Monitoring the Collector's State with Prometheus |
| Part 34 | Monitoring the Wazuh Platform's State with Prometheus |
| Part 35 | Testing the Alert Rules and Checking in Production |
| Part 36 | Checking PostgreSQL |
| Part 37 | Backing Up PostgreSQL and Testing a Restore |
| Part 38 | Using TrueNAS as the Backup Destination |
| Part 39 | Registering the Destination and Preparing Scheduled Backups |
| Part 40 | Completing the PostgreSQL Logical Backup |
| Part 41 | Backing Up LXC 109 and Testing an Isolated Restore |
| Part 42 | Protecting the Backups and TrueNAS Snapshots |
| Part 43 | Backup Failures After a Reboot and the Recovery |
| Part 44 | Comparing the Restored Databases with Production |

**Volume 4**

| Part | Title |
|---|---|
| Part 45 | Preparing for LLM Analysis and Repairing the Wazuh Configuration File |
| Part 46 | Classifying Alerts and Deciding Which Fields to Pass to the LLM |
| Part 47 | Examining the Existing AI Defense Manager Implementation |
| Part 48 | Narrowing the Wazuh Event Conversion to Seven Fields |
| Part 49 | Narrowing the Fields Returned by the Relay to Seven |
| Part 50 | Deploying the New Code and a Static Address for VM 230 |
| Part 51 | Verifying TLS and Authentication from VM 230 to the Relay |
| Part 52 | Fetching Real Alerts and Fixing the Relay's 502 |
| Part 53 | Checking the Flow from Analysis to Storage |
| Part 54 | Masking LLM Output and the Approval Policy |
| Part 55 | Integration Checks and Preparing for High Request Volumes |
| Part 56 | Reviewing and Designing API Authentication |
| Part 57 | Building Token Authentication for the API |
| Part 58 | Hardening Token Handling and the CLI |
| Part 59 | Putting API Authentication into Production |
| Part 60 | Keeping Error Responses and Logs from Leaking Information |
| Part 61 | Checking Logs for Secrets and Capping the Journal Size |
| Part 62 | Creating FSS Keys to Guard Against Log Tampering |
| Part 63 | Moving the FSS Verification Key to the Proxmox Host |
| Part 64 | Running and Checking FSS Sealing |
| Part 65 | Checking FSS from Another Host (VM 240) |
| Part 66 | Automating FSS Verification Every 15 Minutes |
| Part 67 | Finding the Breakage in Wazuh's Local Rules |
| Part 68 | Testing the Fixed Rules in an Isolated Environment |
| Part 69 | Putting the Fixed Rules into Production |
| Part 70 | Starting to Build the AI Defense Agents |
| Part 71 | Correlation, Orchestration and Defense Decision Agents |

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **postgresql**: LXC 109 (192.168.0.151), OS user `postgres`
- Unless otherwise noted, times are in UTC (Japan time is 9 hours ahead).

## Chapter 1: Finding Out How the Logs Are Switched

### 1.1 The logrotate Settings

> **Run on: VM 220**

Look for settings for Wazuh's alert logs in the OS logrotate.

```bash
grep -R -n -E 'alerts\.json|/var/ossec/logs/alerts|copytruncate|rotate|compress' /etc/logrotate.conf /etc/logrotate.d /var/ossec/etc 2>/dev/null | head -160
```

There was no setting in `/etc/logrotate.d` targeting `alerts.json`, and no `copytruncate` (truncating the file in place) setting either. The alert logs are switched by Wazuh itself, not by the OS logrotate.

### 1.2 The List of Alert Files

```bash
find /var/ossec/logs/alerts -maxdepth 2 -type f -printf '%i %s %TY-%Tm-%Td %TH:%TM:%TS %p\n' | sort -k3,4
```

Directly under `alerts` there were only `alerts.log` (inode 5409380) and `alerts.json` (inode 5409517). Look again including subdirectories.

```bash
find /var/ossec/logs/alerts -type f -printf '%i %s %TY-%Tm-%Td %TH:%TM:%TS %p\n' | sort -k3,4
```

This showed the following.

- The logs for the 17th to the 20th are compressed, such as `2026/Nov/ossec-alerts-17.json.gz` (with a `.sum` file as well)
- `alerts.json` and `2026/Nov/ossec-alerts-21.json` have the same inode (5409517); they are hard links

Old logs that have been switched out do not remain as ordinary `.json` files.

### 1.3 What the Collector Does When the Old Inode Is Not Found

```bash
sed -n '350,460p' /usr/local/lib/wazuh-collector/collector.py
```

When the saved inode differs from the current file, `open_initial_file()` looks for the old inode among uncompressed `.json` files and, if found, resumes from the saved position. If not found, it raises an exception and stops; **it does not silently skip to the end of the current file**. It is designed on the safe side, so that no data is skipped.

### 1.4 Wazuh's Switching Settings

```bash
sed -n '270,300p' /var/ossec/etc/internal_options.conf
```

| Setting | Value | Meaning |
|---|---|---|
| `monitord.day_wait` | 10 | Wait 10 seconds before switching, compressing and signing |
| `monitord.compress` | 1 | Compress |
| `monitord.sign` | 1 | Sign |
| `monitord.rotate_log` | 1 | Switch the plain and JSON logs daily |

Look at the switching records in the log.

```bash
grep -Ei 'rotat|compress|alerts\.json|alerts.*json' /var/ossec/logs/ossec.log | tail -80
```

```text
2026/11/21 00:00:10 wazuh-monitord: INFO: Starting new log after rotation.
```

The switch took place at 00:00:10 on November 21.

## Chapter 2: Why the Collector Could Not Read After the Switch

### 2.1 The Collector's Log Around the Switch

```bash
journalctl -u wazuh-collector.service --since "2026-11-20 23:55:00" --until "2026-11-21 00:15:00" --no-pager -o short-iso
```

From 00:14:24 to 00:14:59 the following error appeared every second.

```text
ERROR Failed to open current alert file: PermissionError
```

The Collector could not open the file newly created by the switch.

### 2.2 Checking the ACL

```bash
getfacl -p /var/ossec/logs/alerts /var/ossec/logs/alerts/alerts.json /var/ossec/logs/alerts/2026/Nov/ossec-alerts-21.json
```

`/var/ossec/logs/alerts` has a Default ACL (`default:user:wazuh-collector:r-x` and so on), and the current files (`alerts.json` and `ossec-alerts-21.json`) have `user:wazuh-collector:r--` (added in Part 29). However, the per-date files are created inside `2026/Nov`.

```bash
getfacl -p /var/ossec/logs/alerts/2026 /var/ossec/logs/alerts/2026/Nov
```

`2026` and `2026/Nov` had an ordinary ACL (`user:wazuh-collector:r-x`), but **no Default ACL**. So files newly created inside `2026/Nov` do not inherit the Collector's read permission.

### 2.3 The Process That Creates the Files

```bash
ps -eo pid,ppid,user,group,comm,args | grep -E '[w]azuh-monitord|[w]azuh-analysisd'
```

`wazuh-analysisd` (PID 1701) and `wazuh-monitord` (PID 1873) both ran as the `wazuh` user. See which of them has the files open.

```bash
for p in 1701 1873; do echo "===== PID $p ====="; ls -l /proc/$p/fd 2>/dev/null | grep -E 'alerts(\.json|/)|ossec-alerts'; done
```

`wazuh-analysisd` had `ossec-alerts-21.json` and `ossec-alerts-21.log` open for writing. The JSON alert file is created by `wazuh-analysisd`. Look at that process's umask.

```bash
grep -E '^(Umask|Uid|Gid):' /proc/1701/status
```

```text
Umask:  0027
Uid:    110     110     110     110
Gid:    110     110     110     110
```

```bash
stat -c '%n | mode=%a (%A) | owner=%U:%G | inode=%i' /var/ossec/logs/alerts/2026/Nov/ossec-alerts-21.json /var/ossec/logs/alerts/alerts.json
```

The files were `0640` (`-rw-r-----`) and owned by `wazuh:wazuh`. The umask alone does not give `wazuh-collector` read permission.

## Chapter 3: Adding a Default ACL

Add the following Default ACL to `2026` and `2026/Nov`. The ordinary ACL is not changed; we only add inheritance for newly created items. No Wazuh restart is needed.

| Who | Permission to inherit |
|---|---|
| Owner | `rwx` |
| `wazuh-collector` | `r-x` (read and traverse only; no write) |
| Group | `r-x` |
| Others | None |

Because files are created as `0640`, the mask makes `wazuh-collector`'s effective permission `r--`.

> **Run on: VM 220**

```bash
setfacl -m d:u::rwx,d:u:wazuh-collector:r-x,d:g::r-x,d:m::r-x,d:o::--- /var/ossec/logs/alerts/2026 /var/ossec/logs/alerts/2026/Nov
```

It finishes without output. Check it.

```bash
getfacl -p /var/ossec/logs/alerts/2026 /var/ossec/logs/alerts/2026/Nov
```

Both directories kept their ordinary ACL and gained the following Default ACL.

```text
default:user::rwx
default:user:wazuh-collector:r-x
default:group::r-x
default:mask::r-x
default:other::---
```

Check that the Collector is running and can read the current file.

```bash
systemctl is-active wazuh-collector.service; runuser -u wazuh-collector -- test -r /var/ossec/logs/alerts/alerts.json; echo "ALERT_READABLE=$?"
```

`active` and `ALERT_READABLE=0` were shown.

## Chapter 4: Recording the State Before the Switch

### 4.1 Time and Files

```bash
echo '===== SYSTEM TIME ====='; date --iso-8601=seconds; timedatectl show -p Timezone -p NTPSynchronized; echo '===== ALERT FILES ====='; stat -c '%n | inode=%i | size=%s | mtime=%y | mode=%a' /var/ossec/logs/alerts/alerts.json /var/ossec/logs/alerts/2026/Nov/ossec-alerts-21.json; echo '===== ROTATION SETTINGS ====='; grep -E '^monitord\.(day_wait|compress|rotate_log|size_rotate|daily_rotations|keep_log_days)=' /var/ossec/etc/internal_options.conf
```

The time is UTC and synchronized with NTP; `alerts.json` and the per-date file had the same inode (5409517) and were 883,525 bytes.

### 4.2 The Collector's Read Position

Show only the inode and the position (offset) from the state file and compare them with the current file.

```bash
python3 - <<'PY'
import json, os
state_path = "/var/lib/wazuh-collector/state.json"
alert_path = "/var/ossec/logs/alerts/alerts.json"
with open(state_path) as f:
    state = json.load(f)
st = os.stat(alert_path)
print("STATE_INODE:", state.get("inode"))
print("STATE_OFFSET:", state.get("offset"))
print("CURRENT_INODE:", st.st_ino)
print("CURRENT_SIZE:", st.st_size)
print("INODE_MATCH:", state.get("inode") == st.st_ino)
print("OFFSET_AT_EOF:", state.get("offset") == st.st_size)
print("UNPROCESSED_BYTES:", max(0, st.st_size - state.get("offset", 0)) if state.get("inode") == st.st_ino else "inode mismatch")
PY
```

```text
STATE_INODE: 5409517
STATE_OFFSET: 883525
CURRENT_INODE: 5409517
CURRENT_SIZE: 883525
INODE_MATCH: True
OFFSET_AT_EOF: True
UNPROCESSED_BYTES: 0
```

The Collector had read to the end of the file.

### 4.3 Service and Storage Status

```bash
journalctl -u wazuh-collector.service --since "2026-11-21 12:45:00 UTC" --no-pager | grep -Ei 'starting|connected|insert|duplicate|error|exception|rotation|warning' | tail -60
```

There were no matching log lines (this is not abnormal; the Collector does not log simply because it saved new alerts).

```bash
systemctl show wazuh-collector.service -p ActiveState -p SubState -p MainPID -p NRestarts -p ExecMainStatus
```

`ActiveState=active`, `SubState=running`, `NRestarts=0` and `ExecMainStatus=0`.

> **Run on: postgresql** (OS user `postgres`; you are already logged in as `postgres`, so `sudo` is not used)

```bash
psql -d security_workbench -c "SELECT COUNT(*) AS events_last_15m, COUNT(DISTINCT event_id) AS distinct_event_ids, MAX(ingested_at) AS latest_ingested_at FROM incident.alert_events WHERE ingested_at >= NOW() - INTERVAL '15 minutes';"
```

In the last 15 minutes, 4 events (4 distinct `event_id`s) had been saved.

## Chapter 5: Testing That the ACL Is Inherited

### 5.1 A New File

As the `wazuh` user, create a temporary file with `0640`, the same as real log files, and test whether the Collector's user can read it. Delete it after the test.

> **Caution**: The commands below avoid `exit` and `set -e`. Commands that end the shell can close the console. Also, `mktemp` creates files as `0600`, which makes the mask `---` and the file unreadable. Always `chmod 640` before testing.

> **Run on: VM 220**

```bash
f=$(runuser -u wazuh -- mktemp /var/ossec/logs/alerts/2026/Nov/.acl-inherit-test.XXXXXX)
echo "TEST_FILE=$f"
chmod 640 "$f"
echo "===== ACL ====="
getfacl -p "$f"
echo "===== READ TEST ====="
runuser -u wazuh-collector -- test -r "$f"
echo "COLLECTOR_READ_TEST_EXIT=$?"
rm -f "$f"
echo "TEST_FILE_REMOVED"
```

```text
user:wazuh-collector:r-x        #effective:r--
group::r-x                      #effective:r--
mask::r--
other::---

===== READ TEST =====
COLLECTOR_READ_TEST_EXIT=0
TEST_FILE_REMOVED
```

The ACL was inherited, the effective permission was `r--`, and the Collector's user could read the file.

### 5.2 A New Month Directory

In December, `2026/Dec` will be created. Create a temporary directory inside `2026` and test whether inheritance reaches the files inside it.

```bash
d=$(runuser -u wazuh -- mktemp -d /var/ossec/logs/alerts/2026/.acl-month-test.XXXXXX)
echo "TEST_DIR=$d"
chmod 750 "$d"
echo "===== NEW DIRECTORY ACL ====="
getfacl -p "$d"
runuser -u wazuh -- sh -c 'umask 0027; : > "$1/test.json"' sh "$d"
echo "===== NEW FILE ACL ====="
getfacl -p "$d/test.json"
runuser -u wazuh-collector -- test -r "$d/test.json"
echo "COLLECTOR_READ_TEST_EXIT=$?"
rm -f "$d/test.json"
rmdir "$d"
echo "TEST_DIRECTORY_REMOVED"
```

`COLLECTOR_READ_TEST_EXIT=0` and `TEST_DIRECTORY_REMOVED` were shown. Files inside a new month directory can also be read by the Collector's user.

## Chapter 6: Checks Before Waiting for the Switch

### 6.1 Wazuh's Records and Processes

```bash
grep -E 'wazuh-monitord:|wazuh-analysisd:' /var/ossec/logs/ossec.log | grep -Ei 'rotation|rotate|compress|archive|new log|error|warn' | tail -40
```

The only switching record was the one at 00:00:10 on November 21.

```bash
for p in 1701 1873; do
  echo "===== PID $p ====="
  ps -p "$p" -o pid,user,group,comm
  ls -l "/proc/$p/fd" 2>/dev/null | grep -E 'alerts.*json|ossec-alerts.*json'
done
```

The only process with the JSON file open was still `wazuh-analysisd` (PID 1701). Record the ACL of the current file to compare it after the switch.

```bash
getfacl -p /var/ossec/logs/alerts/2026/Nov/ossec-alerts-21.json
```

```text
user::rw-
user:wazuh-collector:r--
group::r--
mask::r--
other::---
```

### 6.2 Wazuh's Version and Settings

```bash
echo "===== WAZUH VERSION ====="
 /var/ossec/bin/wazuh-analysisd -V 2>&1 | head -20
echo "===== PROCESS DETAILS ====="
ps -p 1701 -o pid,ppid,user,group,lstart,args
echo "===== EXECUTABLE ====="
readlink -f /proc/1701/exe
```

Wazuh was v4.14.10, and `wazuh-analysisd` had started at 09:17:10 on November 21, 2026.

```bash
grep -n -A8 -B4 -E 'jsonout_output|alerts_log|log_alert_level' /var/ossec/etc/ossec.conf
```

| Setting | Value |
|---|---|
| `jsonout_output` | `yes` (output JSON alerts) |
| `alerts_log` | `yes` |
| `logall` / `logall_json` | `no` (not saving every event) |
| `log_alert_level` | 3 (record level 3 and above) |

```bash
getfacl -p /var/ossec/logs/alerts
```

`alerts` also has a Default ACL. Now `alerts` → `2026` → `Nov` all have a Default ACL, so future year and month directories will inherit it too.

### 6.3 The Baseline Just Before the Switch

```bash
python3 - <<'PY'
import json, os
p = "/var/ossec/logs/alerts/alerts.json"
s = "/var/lib/wazuh-collector/state.json"
st = os.stat(p)
with open(s) as f:
    state = json.load(f)
print("CURRENT_INODE:", st.st_ino)
print("CURRENT_SIZE:", st.st_size)
print("STATE_INODE:", state.get("inode"))
print("STATE_OFFSET:", state.get("offset"))
print("INODE_MATCH:", state.get("inode") == st.st_ino)
print("OFFSET_AT_EOF:", state.get("offset") == st.st_size)
print("UNPROCESSED_BYTES:", st.st_size - state.get("offset", 0) if state.get("inode") == st.st_ino else "inode mismatch")
PY
```

Inode 5409517; the size and the position were both 9,471,550 bytes, and nothing was left unread.

```bash
find /var/ossec/logs/alerts/2026/Nov -maxdepth 1 -type f -printf '%TY-%Tm-%Td %TH:%TM:%TS | inode=%i | size=%s | %f\n' | sort
```

`ossec-alerts-22.json` had not been created yet. All previous switches happened around 00:00:10, so the next is expected around 00:00:10 on November 22 (09:00:10 Japan time). After the switch (09:05 Japan time or later), check with the following command.

```bash
echo "===== DAILY JSON FILES ====="
find /var/ossec/logs/alerts/2026/Nov -maxdepth 1 -type f -name 'ossec-alerts-*.json*' -printf '%TY-%Tm-%Td %TH:%TM:%TS | inode=%i | size=%s | %f\n' | sort
echo "===== CURRENT ALERT FILE ====="
stat -c '%n | inode=%i | size=%s | mode=%a' /var/ossec/logs/alerts/alerts.json
```

Do not trigger a switch by hand or restart Wazuh; wait for the normal switch.

## Closing Notes

In Part 31 we found why the Collector could not read the new file after log switching, and fixed it.

| Item | Result |
|---|---|
| How logs are switched | Wazuh (`wazuh-monitord`) switches daily around 00:00:10 and compresses old logs to `.json.gz` |
| `alerts.json` | A hard link to the per-date file (`2026/Nov/ossec-alerts-DD.json`) |
| Why it stopped | `2026` and `2026/Nov` had no Default ACL, so new files did not get the Collector's read permission |
| Fix | Added a Default ACL to `2026` and `2026/Nov` (Collector `r-x`, no write) |
| Tests | Both a new file and a new month directory were readable by the Collector's user |
| Before the switch | Nothing unread, `NRestarts=0`, saving to PostgreSQL continuing |

In Part 32 we confirm that the Collector read the new file after an actual switch, and recover events that were not saved in the past.

# Part 32: Confirming an Actual Switch and Recovering Missing Events
## Introduction

### About This Book

This is Part 32 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". In Part 31 we added a Default ACL to the per-date directories so that the Collector can read the new file even after the logs are switched. This part does the following.

1. After the actual switch on November 22, confirm that the new file inherited the ACL and that the Collector kept reading
2. Compare the compressed archives (`.json.gz`) with the counts in PostgreSQL day by day, and look for events that were not saved
3. Recover the 1,898 events found, using the same checks and the same INSERT statement as the Collector, after a trial that is rolled back (a dry run)

The events were missing because when the Collector was first started at 11:00:48 on November 18, it began reading `alerts.json` **from the end** (the first start is designed to read from the end). The 520 events on the 17th and 1,378 events on the 18th before that time were not in PostgreSQL.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **postgresql**: LXC 109 (192.168.0.151)
- Unless otherwise noted, times are in UTC (Japan time is 9 hours ahead).

## Chapter 1: Confirming the Actual Switch

### 1.1 The New File

After 09:05 Japan time, run the last command from Part 31.

> **Run on: VM 220**

```bash
echo "===== DAILY JSON FILES ====="
find /var/ossec/logs/alerts/2026/Nov -maxdepth 1 -type f -name 'ossec-alerts-*.json*' -printf '%TY-%Tm-%Td %TH:%TM:%TS | inode=%i | size=%s | %f\n' | sort
echo "===== CURRENT ALERT FILE ====="
stat -c '%n | inode=%i | size=%s | mode=%a' /var/ossec/logs/alerts/alerts.json
```

- `ossec-alerts-21.json.gz` had been created at 00:00:11
- A new `ossec-alerts-22.json` (inode 5409424) existed, and `alerts.json` pointed to the same inode
- The new file's mode was `640`

### 1.2 ACL and Reading

```bash
echo "===== NEW FILE ACL ====="
getfacl -p /var/ossec/logs/alerts/2026/Nov/ossec-alerts-22.json
echo "===== COLLECTOR READ TEST ====="
runuser -u wazuh-collector -- test -r /var/ossec/logs/alerts/2026/Nov/ossec-alerts-22.json
echo "COLLECTOR_READ_TEST_EXIT=$?"
echo "===== CURRENT ALERT LINK ====="
stat -c '%n | inode=%i | size=%s | mode=%a' /var/ossec/logs/alerts/alerts.json
```

The new file had inherited `user:wazuh-collector:r-x` (effective `r--`), and `COLLECTOR_READ_TEST_EXIT=0`.

### 1.3 The Collector's Read Position

Show only the inode and position from the state file.

```bash
echo "===== COLLECTOR SERVICE ====="
systemctl show wazuh-collector.service -p MainPID -p NRestarts -p ActiveState -p SubState

echo "===== COLLECTOR STATE ====="
python3 -c 'import json; p="/var/lib/wazuh-collector/state.json"; s=json.load(open(p)); print("STATE_INODE:",s.get("inode")); print("STATE_OFFSET:",s.get("offset"))'

echo "===== CURRENT FILE ====="
stat -c 'CURRENT_INODE=%i CURRENT_SIZE=%s' /var/ossec/logs/alerts/alerts.json
```

```text
NRestarts=0
ActiveState=active
SubState=running
===== COLLECTOR STATE =====
STATE_INODE: 5409424
STATE_OFFSET: 335703
===== CURRENT FILE =====
CURRENT_INODE=5409424 CURRENT_SIZE=335703
```

The Collector switched to the new inode without restarting and had read to the end of the file.

### 1.4 Saving to PostgreSQL

> **Run on: postgresql** (OS user `postgres`)

```bash
psql -d security_workbench -c "
SELECT
    COUNT(*) AS events_after_rotation,
    COUNT(DISTINCT event_id) AS distinct_event_ids,
    MIN(ingested_at) AS first_ingested_at,
    MAX(ingested_at) AS latest_ingested_at
FROM incident.alert_events
WHERE ingested_at >= TIMESTAMPTZ '2026-11-22 00:08:18+00';
"
```

Since the new file was created, 88 events (88 distinct `event_id`s) had been saved. **The switch on November 22 was handled correctly.**

## Chapter 2: Partial Lines at Switching

### 2.1 How Partial Lines Are Handled

> **Run on: VM 220**

```bash
echo "===== ROTATION AND INCOMPLETE-LINE HANDLING ====="
grep -n -A100 -B25 -E 'def read_alert_line|Incomplete alert line discarded at rotation|read_alert_line\(' /usr/local/lib/wazuh-collector/collector.py
```

If the file is switched in the middle of a line (before the newline arrives), the Collector discards that line with a warning and moves to the start of the new file. However, if Wazuh writes each line in one go, this path is normally not taken.

```bash
echo "===== COLLECTOR READ SETTINGS ====="
grep -n -E '^(MAX_ALERT_LINE_BYTES|READ_CHUNK_BYTES|POLL_INTERVAL|ALERT_FILE|STATE_FILE)[[:space:]]*=' /usr/local/lib/wazuh-collector/collector.py
echo "===== WRITE / ROTATION SETTINGS ====="
grep -n -E 'analysisd\.min_rotate_interval|monitord\.(day_wait|size_rotate|rotate_log|compress|keep_log_days)' /var/ossec/etc/internal_options.conf
```

The Collector reads every second, and a line can be up to 1 MiB. Wazuh waits 10 seconds before switching (`day_wait=10`).

### 2.2 Are There Partial Lines in the Archives?

Check every line of the compressed archives: can it be read as JSON, and does it end with a newline?

```bash
python3 - <<'PY'
import gzip
import json
from pathlib import Path

base = Path("/var/ossec/logs/alerts/2026/Nov")

for path in sorted(base.glob("ossec-alerts-*.json.gz")):
    lines = 0
    invalid = 0
    unterminated = False

    with gzip.open(path, "rb") as f:
        for line in f:
            lines += 1
            if not line.endswith(b"\n"):
                unterminated = True
            try:
                json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                invalid += 1

    print(
        f"{path.name}: lines={lines}, "
        f"invalid_json={invalid}, "
        f"unterminated_last_line={unterminated}"
    )
PY
```

All 47,137 lines in the 5 files could be read as JSON, and no last line lacked a newline. No partial lines remain in the archives.

## Chapter 3: Looking for Events That Were Not Saved

### 3.1 Time Ranges of the Archives

```bash
python3 - <<'PY'
import gzip
import json
from pathlib import Path

base = Path("/var/ossec/logs/alerts/2026/Nov")

for path in sorted(base.glob("ossec-alerts-*.json.gz")):
    count = 0
    first = None
    last = None
    missing_timestamp = 0

    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = obj.get("timestamp")
            if not isinstance(ts, str):
                missing_timestamp += 1
                continue

            count += 1
            if first is None:
                first = ts
            last = ts

    print(
        f"{path.name}: events={count}, "
        f"first={first}, last={last}, "
        f"missing_timestamp={missing_timestamp}"
    )
PY
```

| File | Events | First | Last |
|---|---:|---|---|
| `ossec-alerts-17.json.gz` | 520 | 11-17 20:14:42 | 11-17 23:54:53 |
| `ossec-alerts-18.json.gz` | 2,144 | 11-18 00:00:31 | 11-18 23:53:10 |
| `ossec-alerts-21.json.gz` | 25,141 | 11-21 00:09:26 | 11-22 00:00:00 |

(The files for the 19th and 20th are shown the same way.)

### 3.2 Daily Counts in PostgreSQL

> **Run on: postgresql** (enter `psql` and switch to the database `security_workbench`)

```sql
\c security_workbench
```

> **Caution**: When `psql` is started without arguments, it connects to the database `postgres`. There, `incident.alert_events` cannot be found.

```sql
SELECT
    (event_timestamp AT TIME ZONE 'UTC')::date AS utc_date,
    COUNT(*) AS db_events,
    COUNT(DISTINCT event_id) AS distinct_event_ids,
    MIN(event_timestamp) AS first_event,
    MAX(event_timestamp) AS last_event
FROM incident.alert_events
WHERE event_timestamp >= TIMESTAMPTZ '2026-11-17 00:00:00+00'
  AND event_timestamp <  TIMESTAMPTZ '2026-11-23 00:00:00+00'
GROUP BY 1
ORDER BY 1;
```

The 19th, 20th and 21st had almost the same counts as the archives. But **for the 18th, the archive had 2,144 events while PostgreSQL had 766**, and the first event was at 11:00:59. There was not a single event for the 17th.

```sql
SELECT
    COUNT(*) AS db_events_before_1100_utc,
    MIN(event_timestamp) AS first_event,
    MAX(event_timestamp) AS last_event,
    MIN(ingested_at) AS first_ingested_at,
    MAX(ingested_at) AS last_ingested_at
FROM incident.alert_events
WHERE event_timestamp >= TIMESTAMPTZ '2026-11-18 00:00:00+00'
  AND event_timestamp <  TIMESTAMPTZ '2026-11-18 11:00:00+00';
```

PostgreSQL had 0 events from before 11:00 on the 18th.

### 3.3 The Cause

> **Run on: VM 220**

```bash
journalctl -u wazuh-collector.service \
  --since "2026-11-18 00:00:00 UTC" \
  --until "2026-11-18 12:00:00 UTC" \
  --no-pager -o short-iso |
grep -Ei 'starting|established|failed|error|warning|rotation|resume|stopped|exit|restart|permission|alert'
```

```text
2026-11-18 11:00:48,467 INFO Initial start at current end of alerts.json
2026-11-18 11:00:48,491 INFO PostgreSQL connection established
```

The Collector was first started at 11:00:48 on November 18 and began reading `alerts.json` **from the end**. Events before that were never read. This is due to how the first start works, separate from the ACL and switching problems. Count the 18th's events before and after the start.

```bash
python3 - <<'PY'
import gzip
import json
from pathlib import Path
from datetime import datetime, timezone

path = Path("/var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json.gz")
cutoff = datetime(2026, 11, 18, 11, 0, 48, tzinfo=timezone.utc)

before = 0
after = 0
invalid = 0

with gzip.open(path, "rt", encoding="utf-8") as f:
    for line in f:
        try:
            obj = json.loads(line)
            ts = datetime.fromisoformat(obj["timestamp"].replace("Z", "+00:00"))
            if ts < cutoff:
                before += 1
            else:
                after += 1
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            invalid += 1

print("BEFORE_COLLECTOR_START:", before)
print("AT_OR_AFTER_COLLECTOR_START:", after)
print("INVALID_RECORDS:", invalid)
print("ARCHIVE_TOTAL:", before + after + invalid)
PY
```

```text
BEFORE_COLLECTOR_START: 1378
AT_OR_AFTER_COLLECTOR_START: 766
INVALID_RECORDS: 0
ARCHIVE_TOTAL: 2144
```

The 766 events after the start matched the count in PostgreSQL. All 520 events on the 17th were also before the start. The events not saved are expected to be **520 on the 17th and 1,378 on the 18th, 1,898 in total**.

## Chapter 4: Preparing the Recovery

### 4.1 Can the Collector's Checks and INSERT Statement Be Used?

The recovery uses the same checks as the Collector (the field whitelist and input validation) and the same INSERT statement.

```bash
echo "===== EVENT EXTRACTION AND VALIDATION ====="
grep -n -A105 -B10 '^def extract_event' /usr/local/lib/wazuh-collector/collector.py
echo "===== INSERT AND DUPLICATE HANDLING ====="
grep -n -A28 -B5 '^INSERT_SQL\|^def process_line' /usr/local/lib/wazuh-collector/collector.py
```

- `extract_event()` applies the field whitelist and input validation
- `INSERT_SQL` is the same one the Collector normally uses
- `event_id` is the primary key, so existing events are detected as duplicates (SQLSTATE `23505`)
- The Collector's role (`wazuh_collector`) needs only INSERT; no SELECT, UPDATE or DELETE permission is required

### 4.2 IDs Inside the Archives

```bash
python3 - <<'PY'
import gzip
import json
from pathlib import Path
from collections import Counter

base = Path("/var/ossec/logs/alerts/2026/Nov")
files = [
    base / "ossec-alerts-17.json.gz",
    base / "ossec-alerts-18.json.gz",
]

ids = Counter()
invalid = 0
total = 0

for path in files:
    file_count = 0
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            total += 1
            file_count += 1
            try:
                obj = json.loads(line)
                event_id = obj.get("id")
                if isinstance(event_id, str) and event_id:
                    ids[event_id] += 1
                else:
                    invalid += 1
            except (json.JSONDecodeError, UnicodeDecodeError):
                invalid += 1

    print(f"{path.name}: records={file_count}")

duplicates = sum(count - 1 for count in ids.values() if count > 1)

print("TOTAL_RECORDS:", total)
print("VALID_EVENT_IDS:", sum(ids.values()))
print("UNIQUE_EVENT_IDS:", len(ids))
print("DUPLICATE_ID_OCCURRENCES:", duplicates)
print("INVALID_OR_MISSING_IDS:", invalid)
PY
```

The 2 files contained 2,664 records; all IDs were valid and there were no duplicates.

### 4.3 A Trial That Is Rolled Back (Dry Run)

We actually INSERT into PostgreSQL, but the outer transaction is **always rolled back**. The Collector's connection settings (`DB_CONFIG`) and functions are loaded from `collector.py`. Connection settings and passwords are not shown.

```bash
python3 - <<'PY'
import gzip
import json
import importlib.util
from pathlib import Path
import psycopg

spec = importlib.util.spec_from_file_location(
    "wazuh_collector",
    "/usr/local/lib/wazuh-collector/collector.py"
)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)

files = [
    Path("/var/ossec/logs/alerts/2026/Nov/ossec-alerts-17.json.gz"),
    Path("/var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json.gz"),
]

class DryRunComplete(Exception):
    pass

connection = psycopg.connect(**collector.DB_CONFIG)
inserted = 0
duplicates = 0
rejected = 0
records = 0

try:
    try:
        with connection.transaction():
            for path in files:
                with gzip.open(path, "rt", encoding="utf-8") as source:
                    for line in source:
                        records += 1
                        try:
                            alert = json.loads(line)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            rejected += 1
                            continue

                        event = collector.extract_event(alert)
                        if event is None:
                            rejected += 1
                            continue

                        try:
                            with connection.transaction():
                                connection.execute(
                                    collector.INSERT_SQL,
                                    event
                                )
                            inserted += 1
                        except psycopg.errors.UniqueViolation as error:
                            if error.sqlstate != "23505":
                                raise
                            duplicates += 1

            raise DryRunComplete()
    except DryRunComplete:
        pass

    print("DB_ROLE:", connection.info.user)
    print("ARCHIVE_RECORDS:", records)
    print("WOULD_INSERT:", inserted)
    print("ALREADY_EXISTS:", duplicates)
    print("REJECTED:", rejected)
    print("TRANSACTION: ROLLED BACK")
finally:
    connection.close()
PY
```

```text
DB_ROLE: wazuh_collector
ARCHIVE_RECORDS: 2664
WOULD_INSERT: 1898
ALREADY_EXISTS: 766
REJECTED: 0
TRANSACTION: ROLLED BACK
```

1,898 events would be newly inserted and 766 already existed, as expected. Because it was rolled back, PostgreSQL did not change.

## Chapter 5: Recovering the 1,898 Events

Because this writes to PostgreSQL, approval was obtained before running it in the original build. It is done under these conditions.

- The normal Collector is not stopped
- Only `ossec-alerts-17.json.gz` and `ossec-alerts-18.json.gz` are processed
- Abort unless the role is `wazuh_collector`
- Everything is one transaction; if the counts differ from the dry run, everything is rolled back

> **Run on: VM 220**

```bash
python3 - <<'PY'
import gzip
import json
import importlib.util
from pathlib import Path
import psycopg

spec = importlib.util.spec_from_file_location(
    "wazuh_collector",
    "/usr/local/lib/wazuh-collector/collector.py"
)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)

files = [
    Path("/var/ossec/logs/alerts/2026/Nov/ossec-alerts-17.json.gz"),
    Path("/var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json.gz"),
]

expected = {
    "records": 2664,
    "inserted": 1898,
    "duplicates": 766,
    "rejected": 0,
}

connection = psycopg.connect(**collector.DB_CONFIG)
counts = {
    "records": 0,
    "inserted": 0,
    "duplicates": 0,
    "rejected": 0,
}
seen_ids = set()

try:
    if connection.info.user != "wazuh_collector":
        raise RuntimeError("Unexpected database role; refusing recovery")

    with connection.transaction():
        for path in files:
            if not path.is_file():
                raise FileNotFoundError(path)

            with gzip.open(path, "rt", encoding="utf-8") as source:
                for line in source:
                    counts["records"] += 1
                    alert = json.loads(line)
                    event = collector.extract_event(alert)

                    if event is None:
                        counts["rejected"] += 1
                        continue

                    event_id = event["event_id"]
                    if event_id in seen_ids:
                        raise RuntimeError("Duplicate archive event ID")
                    seen_ids.add(event_id)

                    try:
                        with connection.transaction():
                            connection.execute(
                                collector.INSERT_SQL,
                                event
                            )
                        counts["inserted"] += 1
                    except psycopg.errors.UniqueViolation as error:
                        if error.sqlstate != "23505":
                            raise
                        counts["duplicates"] += 1

        if counts != expected:
            raise RuntimeError(
                f"Count mismatch; transaction will roll back: {counts}"
            )

    print("RECOVERY_STATUS: COMMITTED")
    print("DB_ROLE:", connection.info.user)
    for key, value in counts.items():
        print(f"{key.upper()}:", value)

except Exception as error:
    print("RECOVERY_STATUS: FAILED; TRANSACTION ROLLED BACK")
    print("ERROR_TYPE:", type(error).__name__)
    print("COUNTS_AT_FAILURE:", counts)

finally:
    connection.close()
PY
```

```text
RECOVERY_STATUS: COMMITTED
DB_ROLE: wazuh_collector
RECORDS: 2664
INSERTED: 1898
DUPLICATES: 766
REJECTED: 0
```

## Chapter 6: Checks After the Recovery

### 6.1 Counts in PostgreSQL

`wazuh_collector` can only INSERT, so the check is done on the PostgreSQL server.

> **Run on: postgresql** (root)

```bash
sudo -u postgres psql -d security_workbench -c "
SELECT
    (event_timestamp AT TIME ZONE 'UTC')::date AS event_date,
    COUNT(*) AS total_records,
    COUNT(DISTINCT event_id) AS unique_event_ids,
    COUNT(*) - COUNT(DISTINCT event_id) AS duplicate_ids,
    MIN(event_timestamp AT TIME ZONE 'UTC') AS first_event_utc,
    MAX(event_timestamp AT TIME ZONE 'UTC') AS last_event_utc
FROM incident.alert_events
WHERE event_timestamp >= TIMESTAMPTZ '2026-11-17 00:00:00+00'
  AND event_timestamp <  TIMESTAMPTZ '2026-11-19 00:00:00+00'
GROUP BY (event_timestamp AT TIME ZONE 'UTC')::date
ORDER BY event_date;
"
```

| Date | Events | Distinct IDs | Duplicates |
|---|---:|---:|---:|
| 2026-11-17 | 520 | 520 | 0 |
| 2026-11-18 | 2,144 | 2,144 | 0 |

All 2,664 events in the archives are saved, with no duplicates.

### 6.2 The Normal Collector

> **Run on: VM 220**

Check the service and read position with the same command as in 1.3.

```bash
echo "===== COLLECTOR SERVICE ====="
systemctl show wazuh-collector.service -p MainPID -p NRestarts -p ActiveState -p SubState

echo "===== COLLECTOR STATE ====="
python3 -c 'import json; p="/var/lib/wazuh-collector/state.json"; s=json.load(open(p)); print("STATE_INODE:",s.get("inode")); print("STATE_OFFSET:",s.get("offset"))'

echo "===== CURRENT FILE ====="
stat -c 'CURRENT_INODE=%i CURRENT_SIZE=%s' /var/ossec/logs/alerts/alerts.json
```

The service was `running`, the inode was 5409424, and the position and the file size were both 4,627,640 bytes, so nothing was left unread. The Collector's log recorded `Switched to new alerts.json inode` at 00:00:00 on November 22.

> **Run on: postgresql** (root)

```bash
sudo -u postgres psql -d security_workbench -c "
SELECT
    COUNT(*) AS records_last_30_minutes,
    COUNT(DISTINCT event_id) AS unique_event_ids,
    MAX(ingested_at) AS latest_ingested_at,
    MAX(event_timestamp) AS latest_event_timestamp
FROM incident.alert_events
WHERE ingested_at >= NOW() - INTERVAL '30 minutes';
"
```

In the last 30 minutes, 5,753 events (5,753 distinct IDs) had been saved. Normal ingestion is also continuing.

## Closing Notes

In Part 32 we confirmed an actual switch and recovered the events that had not been saved.

| Item | Result |
|---|---|
| The switch on November 22 | The new file inherited the ACL and the Collector followed it without restarting; 88 events saved |
| Archives | 5 files, 47,137 lines, no broken or partial lines |
| Why events were missing | At the first start (11:00:48 on November 18), the Collector began reading `alerts.json` from the end |
| Recovery | 520 events on the 17th and 1,378 on the 18th, 1,898 in total, saved in one transaction after a dry run |
| After the recovery | All 2,664 events for the 17th and 18th saved, 0 duplicates; normal ingestion continuing |

In Part 33 we make the Collector's state observable with Prometheus.

# Part 33: Monitoring the Collector's State with Prometheus
## Introduction

### About This Book

This is Part 33 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". By Part 32 we had kept the Collector from stopping at log switching and recovered the missing events. Here we build **a way to watch the Collector's state with Prometheus**, so that we notice when the Collector stops or falls behind.

We do not add a new monitoring system; we use what already exists.

- The **Node Exporter** running on VM 220 (`192.168.0.220:9100`) and its **Textfile Collector** (a feature that publishes the numbers in `.prom` files placed in a set directory)
- **Prometheus 3.12.0** on LXC 103 (`lxc-prometheus`), which already collects VM 220's Node Exporter under the job name `security-core`

We build the following.

1. A script that extracts only numbers from the Collector's state and writes them to a `.prom` file (run as root)
2. A systemd service and timer that run it every 15 seconds
3. Prometheus alert rules (9 of them)

The Collector's state file (`state.json`) can be read and written only by `wazuh-collector` (directory `0700`, file `0600`). We keep this restriction and let Node Exporter (the `prometheus` user) read a file containing only numbers.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **pve**: the Proxmox host (root). Commands inside LXC 103 (`lxc-prometheus`, 192.168.0.197) are run with `pct exec 103 -- bash -lc '…'`

## Chapter 1: Investigating the Existing Monitoring

### 1.1 Services and Timers

> **Run on: VM 220**

```bash
echo "===== MONITORING SERVICES ====="
systemctl list-units --type=service --all --no-pager | grep -Ei 'wazuh|prometheus|victoria|grafana|node.exporter|zabbix|monitor' || true

echo "===== SYSTEMD TIMERS ====="
systemctl list-timers --all --no-pager

echo "===== COLLECTOR SERVICE CONFIG ====="
systemctl show wazuh-collector.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts \
  -p Restart -p RestartUSec -p StartLimitBurst -p StartLimitIntervalUSec
```

| Item | State |
|---|---|
| Collector | `active` / `running`, 0 restarts |
| Automatic restart | `Restart=always`, up to 5 times in 10 seconds |
| Node Exporter | Running |
| AI Defense Relay | Running |

### 1.2 Listening Ports

```bash
echo "===== NODE EXPORTER ====="
systemctl status prometheus-node-exporter.service --no-pager -l

echo "===== AI DEFENSE RELAY ====="
systemctl status ai-defense-relay.service --no-pager -l

echo "===== LISTENING PORTS ====="
ss -lntp | grep -E ':(9100|9200|5601|8000|9090|9187)\b' || true
```

Node Exporter was listening on `192.168.0.220:9100`, the Relay on `192.168.0.220:8765`, and Wazuh Indexer on `127.0.0.1:9200`.

### 1.3 The Relay's `/health`

Check whether the Relay's `/health` can also show the Collector's state.

```bash
echo "===== RELAY ROUTES AND HEALTH FUNCTIONS ====="
grep -nE '(^@app|@.*route|def health|def metrics|health|metrics|prometheus|8765)' \
  /opt/ai-defense-relay/relay.py
```

```bash
sed -n '1,150p' /opt/ai-defense-relay/relay.py
```

`/health` only returned the following fixed answer.

```json
{"status": "ok"}
```

It only tells us that the Relay itself is answering, not the state of the Collector or PostgreSQL. We leave the Relay as it is and use Node Exporter.

### 1.4 Node Exporter's Settings

```bash
echo "===== NODE EXPORTER UNIT ====="
systemctl cat prometheus-node-exporter.service

echo "===== NODE EXPORTER COMMAND LINE ====="
tr '\0' ' ' < /proc/806/cmdline
echo

echo "===== TEXTFILE COLLECTOR DIRECTORIES ====="
find /etc/prometheus /var/lib/prometheus \
  -maxdepth 3 -type d -iname '*textfile*' -print 2>/dev/null
```

(`806` is Node Exporter's PID shown in 1.2.)

```bash
echo "===== EXPORTER DEFAULT CONFIG ====="
cat /etc/default/prometheus-node-exporter

echo "===== PROMETHEUS DIRECTORIES ====="
ls -ld /etc/prometheus /var/lib/prometheus 2>&1

echo "===== EXPORTER USER ====="
id prometheus

echo "===== COLLECTOR STATE PERMISSIONS ====="
stat -c '%A %U:%G %n' \
  /var/lib/wazuh-collector \
  /var/lib/wazuh-collector/state.json
```

Node Exporter runs as the `prometheus` user. The Collector's state file is `drwx------ wazuh-collector:wazuh-collector` (directory) and `-rw------- wazuh-collector:wazuh-collector` (file), so Node Exporter cannot read it directly.

```bash
echo "===== NODE EXPORTER VERSION ====="
/usr/bin/prometheus-node-exporter --version

echo "===== TEXTFILE COLLECTOR OPTION ====="
/usr/bin/prometheus-node-exporter --help 2>&1 | grep -A3 -B2 textfile

echo "===== PROMETHEUS DATA DIRECTORY ====="
find /var/lib/prometheus -maxdepth 3 -printf '%M %u:%g %p\n'
```

Node Exporter was 1.7.0, and the Textfile Collector was already enabled. The directory it reads is `/var/lib/prometheus/node-exporter`, which already held `apt.prom`, `nvme.prom` and `smartmon.prom`. Placing a file there adds numbers without restarting Node Exporter.

### 1.5 Checking Permissions

```bash
echo "===== TEXTFILE DIRECTORY PERMISSIONS ====="
namei -l /var/lib/prometheus/node-exporter

echo "===== EXISTING METRIC FILES ====="
ls -l /var/lib/prometheus/node-exporter/

echo "===== NODE EXPORTER TEXTFILE METRICS ====="
curl -fsS http://192.168.0.220:9100/metrics \
  | grep -E '^(node_textfile_|node_scrape_collector_success)' \
  | head -40

echo "===== COLLECTOR STATE FILE METADATA ====="
stat -c 'mtime=%y size=%s mode=%a owner=%U:%G' \
  /var/lib/wazuh-collector/state.json
```

```bash
echo "===== PROMETHEUS READ ACCESS ====="
runuser -u prometheus -- test -r /var/lib/prometheus/node-exporter/apt.prom
echo "EXISTING_METRIC_READ_EXIT=$?"

echo "===== PROMETHEUS DIRECTORY ACCESS ====="
runuser -u prometheus -- test -x /var/lib/prometheus/node-exporter
echo "DIRECTORY_TRAVERSE_EXIT=$?"

echo "===== METRIC DIRECTORY WRITE ACCESS ====="
runuser -u prometheus -- test -w /var/lib/prometheus/node-exporter
echo "DIRECTORY_WRITE_EXIT=$?"
```

The results were `0` (readable), `0` (traversable) and `1` (not writable). Node Exporter can read a file written by root without being given write permission.

### 1.6 The Collector's Unit and the Shape of the State File

Without showing the state file's values, check only its shape.

```bash
echo "===== COLLECTOR UNIT ====="
systemctl cat wazuh-collector.service

echo "===== STATE JSON STRUCTURE ====="
python3 -c '
import json
p="/var/lib/wazuh-collector/state.json"
with open(p) as f:
    d=json.load(f)
print("keys:", sorted(d.keys()))
print("inode_type:", type(d.get("inode")).__name__)
print("offset_type:", type(d.get("offset")).__name__)
print("inode_positive:", isinstance(d.get("inode"), int) and d["inode"] > 0)
print("offset_nonnegative:", isinstance(d.get("offset"), int) and d["offset"] >= 0)
'
```

```text
keys: ['inode', 'offset']
inode_type: int
offset_type: int
inode_positive: True
offset_nonnegative: True
```

## Chapter 2: A Script That Writes Out the Numbers

### 2.1 The Numbers to Publish

| Metric | Meaning |
|---|---|
| `wazuh_collector_service_up` | Whether the Collector is running (1/0) |
| `wazuh_collector_restarts_total` | Number of restarts by systemd |
| `wazuh_collector_state_valid` | Whether the state file has the correct shape (1/0) |
| `wazuh_collector_inode_match` | Whether the state file's inode matches the current `alerts.json` (1/0) |
| `wazuh_collector_unread_bytes` | Unread bytes (-1 when unknown) |
| `wazuh_collector_state_mtime_seconds` | Modification time of the state file |

Alert contents, IP addresses and connection details are not published. The script writes to a temporary file and then replaces (`os.replace`); if it fails midway it also deletes the old `.prom`, so that normal-looking values do not remain.

### 2.2 Creating the Script

In the original build, approval was obtained before running this.

> **Run on: VM 220**

```bash
cat > /usr/local/sbin/wazuh-collector-metrics.py <<'PY'
#!/usr/bin/python3
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

STATE = Path("/var/lib/wazuh-collector/state.json")
ALERTS = Path("/var/ossec/logs/alerts/alerts.json")
OUTPUT_DIR = Path("/var/lib/prometheus/node-exporter")
OUTPUT = OUTPUT_DIR / "wazuh_collector.prom"

def systemd_status():
    result = subprocess.run(
        [
            "/usr/bin/systemctl", "show", "wazuh-collector.service",
            "-p", "ActiveState", "-p", "SubState", "-p", "NRestarts",
        ],
        capture_output=True, text=True, timeout=5, check=True
    )
    values = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value

    active = int(
        values.get("ActiveState") == "active"
        and values.get("SubState") == "running"
    )
    restarts = int(values["NRestarts"])
    return active, restarts

def build_metrics():
    service_up, restarts = systemd_status()

    state_valid = 0
    inode_match = 0
    unread_bytes = -1
    state_mtime = 0

    try:
        with STATE.open("r", encoding="utf-8") as handle:
            state = json.load(handle)

        if (
            isinstance(state, dict)
            and set(state) == {"inode", "offset"}
            and isinstance(state["inode"], int)
            and not isinstance(state["inode"], bool)
            and state["inode"] > 0
            and isinstance(state["offset"], int)
            and not isinstance(state["offset"], bool)
            and state["offset"] >= 0
        ):
            state_valid = 1
            state_mtime = STATE.stat().st_mtime
            alert_stat = ALERTS.stat()

            if state["inode"] == alert_stat.st_ino:
                inode_match = 1
                if state["offset"] <= alert_stat.st_size:
                    unread_bytes = alert_stat.st_size - state["offset"]
                else:
                    state_valid = 0
                    inode_match = 0
                    unread_bytes = -1
    except (OSError, ValueError, TypeError, KeyError):
        pass

    lines = [
        "# HELP wazuh_collector_service_up Collector service running state.",
        "# TYPE wazuh_collector_service_up gauge",
        f"wazuh_collector_service_up {service_up}",
        "# HELP wazuh_collector_restarts_total systemd collector restart count.",
        "# TYPE wazuh_collector_restarts_total gauge",
        f"wazuh_collector_restarts_total {restarts}",
        "# HELP wazuh_collector_state_valid Collector state file validity.",
        "# TYPE wazuh_collector_state_valid gauge",
        f"wazuh_collector_state_valid {state_valid}",
        "# HELP wazuh_collector_inode_match State inode matches current alert file.",
        "# TYPE wazuh_collector_inode_match gauge",
        f"wazuh_collector_inode_match {inode_match}",
        "# HELP wazuh_collector_unread_bytes Unread bytes; -1 means unavailable.",
        "# TYPE wazuh_collector_unread_bytes gauge",
        f"wazuh_collector_unread_bytes {unread_bytes}",
        "# HELP wazuh_collector_state_mtime_seconds State file modification time.",
        "# TYPE wazuh_collector_state_mtime_seconds gauge",
        f"wazuh_collector_state_mtime_seconds {state_mtime}",
    ]
    return "\n".join(lines) + "\n"

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    content = build_metrics()
    fd, temporary = tempfile.mkstemp(
        prefix=".wazuh_collector.", suffix=".tmp", dir=OUTPUT_DIR
    )
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, OUTPUT)
        directory_fd = os.open(OUTPUT_DIR, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        try:
            OUTPUT.unlink()
        except FileNotFoundError:
            pass
        raise

if __name__ == "__main__":
    main()
PY
chmod 0755 /usr/local/sbin/wazuh-collector-metrics.py
python3 -m py_compile /usr/local/sbin/wazuh-collector-metrics.py
echo "SCRIPT_SYNTAX_EXIT=$?"
stat -c '%A %U:%G %n' /usr/local/sbin/wazuh-collector-metrics.py
```

`SCRIPT_SYNTAX_EXIT=0` and `-rwxr-xr-x root:root`.

### 2.3 Running It Once

```bash
python3 /usr/local/sbin/wazuh-collector-metrics.py
echo "SCRIPT_EXIT=$?"
echo "===== METRICS FILE ====="
stat -c '%A %U:%G size=%s %n' /var/lib/prometheus/node-exporter/wazuh_collector.prom
cat /var/lib/prometheus/node-exporter/wazuh_collector.prom
echo "===== PROMETHEUS READ ACCESS ====="
runuser -u prometheus -- test -r /var/lib/prometheus/node-exporter/wazuh_collector.prom
echo "PROMETHEUS_READ_EXIT=$?"
```

The file contained `wazuh_collector_service_up 1`, `restarts_total 0`, `state_valid 1`, `inode_match 1` and `unread_bytes 0`, and the `prometheus` user could read it (`PROMETHEUS_READ_EXIT=0`).

## Chapter 3: Running It Every 15 Seconds

### 3.1 The Service

It runs as root, but where it can read and write is narrowed (the state file and the alerts directory are read-only; only the `.prom` directory is writable).

```bash
cat > /etc/systemd/system/wazuh-collector-metrics.service <<'EOF'
[Unit]
Description=Export Wazuh Collector metrics for Node Exporter
After=network-online.target

[Service]
Type=oneshot
User=root
Group=root
UMask=0022
ExecStart=/usr/bin/python3 /usr/local/sbin/wazuh-collector-metrics.py

NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
ProtectHostname=true
ProtectClock=true
RestrictSUIDSGID=true
LockPersonality=true
MemoryDenyWriteExecute=true
RestrictAddressFamilies=AF_UNIX

ReadOnlyPaths=/var/lib/wazuh-collector
ReadOnlyPaths=/var/ossec/logs/alerts
ReadWritePaths=/var/lib/prometheus/node-exporter

[Install]
WantedBy=multi-user.target
EOF

systemd-analyze verify /etc/systemd/system/wazuh-collector-metrics.service
echo "VERIFY_EXIT=$?"
```

### 3.2 The Timer

```bash
cat > /etc/systemd/system/wazuh-collector-metrics.timer <<'EOF'
[Unit]
Description=Periodic Wazuh Collector metrics update

[Timer]
OnBootSec=30s
OnUnitActiveSec=15s
AccuracySec=1s
Unit=wazuh-collector-metrics.service

[Install]
WantedBy=timers.target
EOF

systemd-analyze verify /etc/systemd/system/wazuh-collector-metrics.timer
echo "VERIFY_EXIT=$?"
```

Both gave `VERIFY_EXIT=0`.

### 3.3 Enabling It

```bash
systemctl daemon-reload
systemctl enable --now wazuh-collector-metrics.timer
echo "ENABLE_EXIT=$?"
echo "===== TIMER STATUS ====="
systemctl status wazuh-collector-metrics.timer --no-pager -l
echo "===== NEXT ACTIVATION ====="
systemctl list-timers wazuh-collector-metrics.timer --no-pager
```

```bash
echo "===== METRICS SERVICE ====="
systemctl status wazuh-collector-metrics.service --no-pager -l
echo "===== TIMER PROPERTIES ====="
systemctl show wazuh-collector-metrics.timer \
  -p ActiveState -p SubState -p LastTriggerUSec \
  -p NextElapseUSecRealtime -p NextElapseUSecMonotonic
echo "===== RECENT JOURNAL ====="
journalctl -u wazuh-collector-metrics.service -n 20 --no-pager
```

The service finished with `status=0/SUCCESS`, and the timer was `active (waiting)`.

> **Note**: The next run time in `systemctl list-timers` may be shown as `-`. Because `OnUnitActiveSec` is measured from the previous run (on the monotonic clock), `NextElapseUSecRealtime` is empty and the value goes into `NextElapseUSecMonotonic` instead. This is not abnormal.

### 3.4 Visible from Node Exporter?

```bash
echo "===== TIMER SCHEDULE ====="
systemctl list-timers --all wazuh-collector-metrics.timer --no-pager
echo "===== NODE EXPORTER METRICS ====="
curl -fsS http://192.168.0.220:9100/metrics \
  | grep -E '^wazuh_collector_|^node_scrape_collector_success\{collector="textfile"\}'
echo "===== METRICS FILE TIME ====="
stat -c '%y %A %U:%G %n' /var/lib/prometheus/node-exporter/wazuh_collector.prom
```

The `wazuh_collector_` numbers appeared in Node Exporter's `/metrics`, and `node_scrape_collector_success{collector="textfile"}` was 1. The `.prom` file was also being rewritten every 15 seconds.

## Chapter 4: Ingesting into Prometheus

### 4.1 Where Prometheus Is

Prometheus runs in LXC 103 on Proxmox. If you run Prometheus commands directly on the Proxmox host (`root@pve`), neither the configuration file nor `promtool` will be found. Check with the list of LXCs.

> **Run on: pve**

```bash
pct list
```

LXC 103 was `lxc-prometheus`.

### 4.2 The Collection Settings

```bash
pct exec 103 -- bash -lc '
echo "===== PROMETHEUS SERVICE ====="
systemctl is-active prometheus
echo "===== PROMETHEUS CONFIG ====="
grep -n -B 8 -A 12 "192.168.0.220:9100" /etc/prometheus/prometheus.yml
echo "===== CONFIG VALIDATION ====="
promtool check config /etc/prometheus/prometheus.yml
'
```

Prometheus was running, and `192.168.0.220:9100` was already registered as job `security-core`. The configuration check was also `SUCCESS`. The new numbers are ingested without changing Prometheus's settings.

```bash
pct exec 103 -- bash -lc '
for metric in \
  wazuh_collector_service_up \
  wazuh_collector_restarts_total \
  wazuh_collector_state_valid \
  wazuh_collector_inode_match \
  wazuh_collector_unread_bytes
do
  echo "===== $metric ====="
  curl -fsS --get http://127.0.0.1:9090/api/v1/query \
    --data-urlencode "query=$metric"
  echo
done
'
```

All five were ingested with the labels `job="security-core"` and `instance="192.168.0.220:9100"`.

### 4.3 The Current Alert Settings

```bash
pct exec 103 -- bash -lc '
echo "===== RULE FILE CONFIGURATION ====="
grep -n -A 8 -B 3 "rule_files:" /etc/prometheus/prometheus.yml
echo "===== EXISTING RULE FILES ====="
find /etc/prometheus -maxdepth 3 -type f \
  \( -name "*.yml" -o -name "*.yaml" \) -printf "%p\n"
echo "===== ALERTMANAGER SERVICE ====="
systemctl is-active prometheus-alertmanager 2>/dev/null || true
echo "===== ALERTMANAGER TARGET CONFIG ====="
grep -n -A 8 -B 3 "alertmanagers:" /etc/prometheus/prometheus.yml
'
```

`rule_files` was still commented out (no rules), and Alertmanager was not running either. With rules added, alerts can be seen in Prometheus's screens (notifications such as e-mail are not delivered until Alertmanager is set up; we do not set up notifications this time).

## Chapter 5: Alert Rules

### 5.1 Checks Before Creating

In the original build, approval was obtained before adding the rules.

```bash
pct exec 103 -- bash -lc '
echo "===== PROMETHEUS VERSION ====="
prometheus --version
echo "===== GLOBAL CONFIG ====="
sed -n "1,24p" /etc/prometheus/prometheus.yml
echo "===== RULE DIRECTORY ====="
ls -ld /etc/prometheus /etc/prometheus/rules 2>&1
echo "===== TARGET TEXTFILE METRICS ====="
curl -fsS http://192.168.0.220:9100/metrics \
  | grep -E "^node_textfile_mtime_seconds|^wazuh_collector_"
echo "===== RULE FILE COLLISION ====="
ls -l /etc/prometheus/rules/wazuh-collector-alerts.yml 2>&1
'
```

Prometheus was 3.12.0 and the evaluation interval was 15 seconds. `/etc/prometheus/rules` did not exist yet, nor did a file with the same name.

### 5.2 The Rule File

| Alert | Condition |
|---|---|
| `WazuhCollectorDown` | The Collector has been stopped for 1 minute or more |
| `WazuhCollectorStateInvalid` | The state file has been invalid for 1 minute or more |
| `WazuhCollectorInodeMismatch` | The inode has not matched for 1 minute or more |
| `WazuhCollectorBacklog` | Unread data has exceeded 1 MiB for 2 minutes or more |
| `WazuhCollectorRestarted` | The restart count increased within 5 minutes |
| `WazuhCollectorMetricsStale` | The `.prom` file has not been rewritten for 60 seconds or more |
| `WazuhCollectorMetricsMissing` | The Collector's numbers have not arrived for 1 minute or more |
| `SecurityCoreNodeExporterDown` | Node Exporter could not be scraped for 1 minute or more |
| `SecurityCoreTargetMissing` | The scrape target `security-core` itself has been absent for 1 minute or more |

> **Run on: pve**

```bash
pct exec 103 -- bash -lc '
install -d -o root -g root -m 0755 /etc/prometheus/rules

cat > /etc/prometheus/rules/wazuh-collector-alerts.yml <<'"'"'EOF'"'"'
groups:
  - name: wazuh-collector
    interval: 15s
    rules:
      - alert: WazuhCollectorDown
        expr: wazuh_collector_service_up{job="security-core"} == 0
        for: 1m
        labels:
          severity: critical
          component: wazuh-collector
        annotations:
          summary: "Wazuh Collector is not running"
          description: "The Wazuh Collector service has been down for at least 1 minute."

      - alert: WazuhCollectorStateInvalid
        expr: wazuh_collector_state_valid{job="security-core"} == 0
        for: 1m
        labels:
          severity: critical
          component: wazuh-collector
        annotations:
          summary: "Wazuh Collector state is invalid"
          description: "The Collector state file or its position validation has failed."

      - alert: WazuhCollectorInodeMismatch
        expr: wazuh_collector_inode_match{job="security-core"} == 0
        for: 1m
        labels:
          severity: warning
          component: wazuh-collector
        annotations:
          summary: "Wazuh alert file inode mismatch"
          description: "The Collector state inode does not match the current alerts.json inode."

      - alert: WazuhCollectorBacklog
        expr: wazuh_collector_unread_bytes{job="security-core"} > 1048576
        for: 2m
        labels:
          severity: warning
          component: wazuh-collector
        annotations:
          summary: "Wazuh Collector backlog is growing"
          description: "Unread alert data exceeds 1 MiB for at least 2 minutes."

      - alert: WazuhCollectorRestarted
        expr: increase(wazuh_collector_restarts_total{job="security-core"}[5m]) > 0
        for: 0m
        labels:
          severity: warning
          component: wazuh-collector
        annotations:
          summary: "Wazuh Collector restarted"
          description: "The systemd restart counter increased during the last 5 minutes."

      - alert: WazuhCollectorMetricsStale
        expr: time() - node_textfile_mtime_seconds{job="security-core",file="/var/lib/prometheus/node-exporter/wazuh_collector.prom"} > 60
        for: 0m
        labels:
          severity: critical
          component: wazuh-collector
        annotations:
          summary: "Wazuh Collector metrics file is stale"
          description: "The Collector metrics textfile has not been updated for more than 60 seconds."

      - alert: WazuhCollectorMetricsMissing
        expr: absent(wazuh_collector_service_up{job="security-core"})
        for: 1m
        labels:
          severity: critical
          component: wazuh-collector
        annotations:
          summary: "Wazuh Collector metrics are missing"
          description: "Prometheus has not received the Collector service metric for at least 1 minute."

      - alert: SecurityCoreNodeExporterDown
        expr: up{job="security-core"} == 0
        for: 1m
        labels:
          severity: critical
          component: node-exporter
        annotations:
          summary: "Security-core Node Exporter is unreachable"
          description: "Prometheus cannot scrape security-core Node Exporter."

      - alert: SecurityCoreTargetMissing
        expr: absent(up{job="security-core"})
        for: 1m
        labels:
          severity: critical
          component: node-exporter
        annotations:
          summary: "Security-core scrape target is missing"
          description: "The security-core scrape target is absent from Prometheus."
EOF

echo "===== FILE PERMISSIONS ====="
stat -c "%A %U:%G %n" /etc/prometheus/rules/wazuh-collector-alerts.yml
echo "===== RULE FILE ====="
cat /etc/prometheus/rules/wazuh-collector-alerts.yml
'
```

The file was created as `root:root`, `0644`.

### 5.3 Checking the Rules

> **Caution**: Running it directly, as in `pct exec 103 -- promtool …`, fails with `Failed to exec "promtool"` (exit code 127) because `promtool` is not found in the PATH. Run it through `bash -lc`.

```bash
pct exec 103 -- bash -lc '
echo "===== PROMTOOL PATH ====="
command -v promtool
echo "===== RULE VALIDATION ====="
promtool check rules /etc/prometheus/rules/wazuh-collector-alerts.yml
echo "RULE_CHECK_EXIT=$?"
'
```

`SUCCESS: 9 rules found` and `RULE_CHECK_EXIT=0`.

### 5.4 Registering in the Prometheus Configuration

Back up the configuration file, then replace only the commented-out `rule_files` part. If the part to replace is not found exactly once, nothing is changed.

```bash
pct exec 103 -- bash -lc '
cp -a /etc/prometheus/prometheus.yml \
  /etc/prometheus/prometheus.yml.pre-wazuh-rules-20261122

python3 - <<'"'"'PY'"'"'
from pathlib import Path

path = Path("/etc/prometheus/prometheus.yml")
content = path.read_text()

old = """rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"
"""
new = """rule_files:
  - "/etc/prometheus/rules/*.yml"
"""

if content.count(old) != 1:
    print("CONFIG_EDIT_ABORTED: expected rule_files block not found exactly once")
else:
    path.write_text(content.replace(old, new, 1))
    print("CONFIG_EDIT: SUCCESS")
PY

echo "===== CONFIG VALIDATION ====="
promtool check config /etc/prometheus/prometheus.yml
echo "CONFIG_CHECK_EXIT=$?"
echo "===== RULE VALIDATION ====="
promtool check rules /etc/prometheus/rules/wazuh-collector-alerts.yml
echo "RULE_CHECK_EXIT=$?"
echo "===== RULE FILE REGISTRATION ====="
grep -n -A 3 "^rule_files:" /etc/prometheus/prometheus.yml
'
```

`CONFIG_EDIT: SUCCESS`, and both the configuration and rule checks were `SUCCESS`. Under `rule_files:` there is now `- "/etc/prometheus/rules/*.yml"`.

### 5.5 Reloading Without a Restart

```bash
pct exec 103 -- bash -lc '
echo "===== RELOAD CAPABILITY ====="
systemctl show prometheus -p CanReload -p ExecReload -p ActiveState -p MainPID
echo "===== SERVICE UNIT ====="
systemctl cat prometheus
'
```

`CanReload=yes`, with `ExecReload=/bin/kill -HUP $MAINPID` (sending SIGHUP).

```bash
pct exec 103 -- bash -lc '
systemctl reload prometheus
echo "RELOAD_EXIT=$?"
echo "===== SERVICE STATUS ====="
systemctl is-active prometheus
echo "===== PROMETHEUS PID ====="
systemctl show prometheus -p MainPID
echo "===== RECENT LOG ====="
journalctl -u prometheus -n 15 --no-pager
'
```

Prometheus stayed `active`, its PID stayed `98`, and `Completed loading of configuration file` appeared in the log.

### 5.6 Were the Rules Registered?

```bash
pct exec 103 -- bash -lc '
echo "===== LOADED RULES ====="
curl -fsS http://127.0.0.1:9090/api/v1/rules |
python3 -c "
import json,sys
d=json.load(sys.stdin)
groups=d.get(\"data\",{}).get(\"groups\",[])
rules=[r for g in groups for r in g.get(\"rules\",[]) if r.get(\"name\", \"\").startswith((\"WazuhCollector\", \"SecurityCore\"))]
print(\"RULE_COUNT:\",len(rules))
for r in rules:
    print(r.get(\"name\"), \"|\", r.get(\"health\"), \"|\", r.get(\"state\"))
"

echo "===== ACTIVE ALERTS ====="
curl -fsS http://127.0.0.1:9090/api/v1/alerts |
python3 -c "
import json,sys
d=json.load(sys.stdin)
alerts=d.get(\"data\",{}).get(\"alerts\",[])
selected=[a for a in alerts if a.get(\"labels\",{}).get(\"component\") in (\"wazuh-collector\", \"node-exporter\")]
print(\"ACTIVE_ALERT_COUNT:\",len(selected))
for a in selected:
    print(a.get(\"labels\",{}).get(\"alertname\"), \"|\", a.get(\"state\"), \"|\", a.get(\"labels\",{}).get(\"severity\"))
"
'
```

`RULE_COUNT: 9`; all 9 had `health` `ok` and `state` `inactive` (nothing abnormal at present), and `ACTIVE_ALERT_COUNT: 0`.

## Closing Notes

In Part 33 we made the Collector's state observable with Prometheus.

| Item | Result |
|---|---|
| Script that writes the numbers | `/usr/local/sbin/wazuh-collector-metrics.py` (root, `0755`) |
| Output | `/var/lib/prometheus/node-exporter/wazuh_collector.prom` (`0644`, 6 numbers) |
| Scheduled runs | `wazuh-collector-metrics.service` (oneshot) and `.timer` (every 15 seconds) |
| Permissions | The state file's restriction is unchanged; Node Exporter only reads |
| Prometheus | LXC 103; ingested under job `security-core`; configuration backup `prometheus.yml.pre-wazuh-rules-20261122` |
| Alert rules | `/etc/prometheus/rules/wazuh-collector-alerts.yml` (9 rules, all `ok`, `inactive`) |
| Notifications | Alertmanager not set up (not done this time) |

In Part 34 we use the same approach to watch the state of the Wazuh platform itself (Manager, Indexer, Dashboard and API).

# Part 34: Monitoring the Wazuh Platform's State with Prometheus
## Introduction

### About This Book

This is Part 34 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". In Part 33 we made the Collector's state observable with Prometheus. Here we use the same approach (Node Exporter's Textfile Collector and the Prometheus on LXC 103) to watch **the Wazuh platform itself**.

| What we watch | How |
|---|---|
| Wazuh Manager | Whether the 9 required daemons are running |
| Wazuh Indexer | Whether `https://127.0.0.1:9200/` answers (401 also counts as normal) |
| Wazuh Dashboard | Whether `https://127.0.0.1:443/` answers (302 also counts as normal) |
| Wazuh API | Whether `https://127.0.0.1:55000/` answers (401 also counts as normal) |

No credentials are put into the script; only the HTTP status of the answer is checked. 401 (authentication required) and 302 (redirect) are also counted as normal, as evidence that the service is answering.

Along the way, a version that checked the Manager with `wazuh-control status` failed when run by the timer, because it waited on a lock for more than 10 seconds. We solve this by changing it to look at Wazuh's PID files directly.

Finally, we add 7 alert rules for the Wazuh platform, making 16 rules together with the 9 for the Collector.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **pve**: the Proxmox host (root). Commands inside LXC 103 are run with `pct exec 103 -- bash -lc '…'`

## Chapter 1: Investigating the Current State

The monitoring configuration so far is as follows.

```text
Wazuh Manager
    │
    ▼
Wazuh Collector
    │
    ├── Save alerts to PostgreSQL
    │
    └── Generate metrics (every 15 seconds)
             │
             ▼
       Node Exporter
             │
             ▼
       Prometheus
             │
             ▼
       9 monitoring rules
```

### 1.1 Services and Disks

> **Run on: VM 220**

```bash
echo "===== WAZUH RELATED SERVICES ====="
systemctl list-units --type=service --all --no-pager | grep -Ei 'wazuh|opensearch|indexer|filebeat|dashboard'

echo "===== INSTALLED WAZUH PACKAGES ====="
dpkg-query -W -f='${Package} ${Status} ${Version}\n' 2>/dev/null | grep -Ei 'wazuh|opensearch|filebeat'

echo "===== FILESYSTEM USAGE ====="
df -hT

echo "===== MEMORY ====="
free -h
```

Wazuh Manager, Indexer, Dashboard, Filebeat and the Collector were all running. The root file system was 12% used, and about 12 GiB of memory was available.

### 1.2 The Manager's Daemons and Ports

```bash
echo "===== WAZUH MANAGER INTERNAL STATUS ====="
/var/ossec/bin/wazuh-control status

echo "===== SERVICE DETAILS ====="
for s in wazuh-manager wazuh-indexer wazuh-dashboard filebeat; do
  echo "--- $s ---"
  systemctl show "$s" \
    -p ActiveState -p SubState -p MainPID -p ExecMainStatus
done

echo "===== LISTENING PORTS ====="
ss -lntp | grep -E ':(443|55000|5601|9200|9300|1514|1515|514|55000)\b'
```

`wazuh-analysisd`, `wazuh-remoted` (1514), `wazuh-authd` (1515) and others were running, and the API (55000), Indexer (9200, 9300) and Dashboard (443) were listening. `wazuh-clusterd`, `wazuh-maild`, `wazuh-agentlessd` and others were stopped, but these do not run unless their features are used; this is not abnormal.

### 1.3 HTTP Answers

```bash
echo "===== WAZUH INDEXER HTTP ====="
curl -k -sS -o /dev/null -w 'HTTP_STATUS=%{http_code}\n' \
  --connect-timeout 3 https://127.0.0.1:9200/

echo "===== WAZUH DASHBOARD HTTPS ====="
curl -k -sS -o /dev/null -w 'HTTP_STATUS=%{http_code}\n' \
  --connect-timeout 3 https://127.0.0.1:443/

echo "===== WAZUH API HTTP ====="
curl -sS -o /dev/null -w 'HTTP_STATUS=%{http_code}\n' \
  --connect-timeout 3 http://127.0.0.1:55000/
```

The Indexer answered 401 and the Dashboard 302. The API gave no answer (`000`) because the request used `http://`; the API listens on HTTPS, so check again with HTTPS.

```bash
echo "===== WAZUH API HTTPS ====="
curl -k -sS -o /dev/null \
  -w 'HTTP_STATUS=%{http_code}\n' \
  --connect-timeout 3 https://127.0.0.1:55000/
```

`HTTP_STATUS=401`. All three are answering.

### 1.4 Existing Monitoring Tools

```bash
echo "===== AVAILABLE MONITORING TOOLS ====="
for cmd in curl python3 systemctl ss; do
  command -v "$cmd"
done

echo "===== NODE EXPORTER SERVICE ====="
systemctl show prometheus-node-exporter \
  -p ActiveState -p SubState -p MainPID

echo "===== NODE EXPORTER TEXTFILE DIRECTORY ====="
ls -ld /var/lib/prometheus/node-exporter

echo "===== EXISTING TEXTFILE METRICS ====="
find /var/lib/prometheus/node-exporter \
  -maxdepth 1 -type f -name '*.prom' \
  -printf '%f\n' | sort
```

There were four `.prom` files: `apt.prom`, `nvme.prom`, `smartmon.prom` and `wazuh_collector.prom`.

```bash
echo "===== EXISTING METRICS SCRIPT ====="
sed -n '1,240p' /usr/local/sbin/wazuh-collector-metrics.py

echo "===== NODE EXPORTER STARTUP ====="
systemctl show prometheus-node-exporter -p ExecStart

echo "===== NODE EXPORTER UNIT ====="
systemctl cat prometheus-node-exporter
```

The new script is built the same way as the one in Part 33: run as root, write only numbers to a temporary file and then replace.

```bash
echo "===== NODE EXPORTER ARGUMENTS ====="
grep -vE '^[[:space:]]*(#|$)' /etc/default/prometheus-node-exporter

echo "===== TEXTFILE COLLECTOR CONFIGURATION ====="
grep -oE -- '--collector.textfile[^ ]*' \
  /etc/default/prometheus-node-exporter

echo "===== WAZUH MANAGER CONTROL STATUS EXIT ====="
/var/ossec/bin/wazuh-control status >/dev/null 2>&1
echo "WAZUH_CONTROL_EXIT=$?"
```

The exit code of `wazuh-control status` was `1`. This is because its judgment includes optional daemons that are stopped; it does not mean the whole Manager is abnormal. The monitoring checks only the required daemons, one by one.

```bash
echo "===== NODE EXPORTER PROCESS ARGUMENTS ====="
ps -ww -p 806 -o pid=,user=,args=

echo "===== TEXTFILE COLLECTOR METRICS ====="
curl -fsS http://192.168.0.220:9100/metrics \
  | grep -E '^node_scrape_collector_success\{collector="textfile"\}|^node_textfile_mtime_seconds'

echo "===== NODE EXPORTER VERSION ====="
/usr/bin/prometheus-node-exporter --version
```

`node_scrape_collector_success{collector="textfile"}` was 1, and all four files were being read. Node Exporter's startup arguments do not need to change. For disks and memory, Node Exporter's standard numbers are used as they are.

## Chapter 2: A Script That Writes Out the Wazuh Platform's Numbers

In the original build, approval was obtained before creating it.

### 2.1 Creating the Script

> **Run on: VM 220**

```bash
cat > /usr/local/sbin/wazuh-platform-metrics.py <<'PY'
#!/usr/bin/python3
import os
import re
import subprocess
import tempfile
from pathlib import Path

OUTPUT_DIR = Path("/var/lib/prometheus/node-exporter")
OUTPUT = OUTPUT_DIR / "wazuh_platform.prom"

REQUIRED_DAEMONS = [
    "wazuh-analysisd",
    "wazuh-remoted",
    "wazuh-syscheckd",
    "wazuh-logcollector",
    "wazuh-modulesd",
    "wazuh-db",
    "wazuh-execd",
    "wazuh-monitord",
    "wazuh-authd",
]

ENDPOINTS = {
    "indexer": {
        "url": "https://127.0.0.1:9200/",
        "expected": {200, 401, 403},
    },
    "dashboard": {
        "url": "https://127.0.0.1:443/",
        "expected": {200, 301, 302, 303, 307, 308},
    },
    "api": {
        "url": "https://127.0.0.1:55000/",
        "expected": {200, 401, 403},
    },
}

def manager_status():
    result = subprocess.run(
        ["/var/ossec/bin/wazuh-control", "status"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    statuses = {}
    for line in result.stdout.splitlines():
        match = re.fullmatch(
            r"(wazuh-[A-Za-z0-9_-]+) is (running|not running)\.\.\.",
            line.strip(),
        )
        if match:
            statuses[match.group(1)] = int(match.group(2) == "running")

    daemon_values = {
        daemon: statuses.get(daemon, 0)
        for daemon in REQUIRED_DAEMONS
    }
    manager_up = int(all(daemon_values.values()))
    return manager_up, daemon_values

def endpoint_status(name, config):
    result = subprocess.run(
        [
            "/usr/bin/curl",
            "--silent",
            "--show-error",
            "--output", "/dev/null",
            "--write-out", "%{http_code}",
            "--insecure",
            "--connect-timeout", "3",
            "--max-time", "5",
            config["url"],
        ],
        capture_output=True,
        text=True,
        timeout=7,
        check=False,
    )

    raw = result.stdout.strip()
    try:
        code = int(raw)
    except (ValueError, TypeError):
        code = 0

    up = int(result.returncode == 0 and code in config["expected"])
    return up, code

def build_metrics():
    manager_up, daemon_values = manager_status()

    lines = [
        "# HELP wazuh_manager_up All required Wazuh Manager daemons are running.",
        "# TYPE wazuh_manager_up gauge",
        f"wazuh_manager_up {manager_up}",
        "# HELP wazuh_manager_daemon_up Required Wazuh Manager daemon state.",
        "# TYPE wazuh_manager_daemon_up gauge",
    ]

    for daemon, value in daemon_values.items():
        lines.append(
            f'wazuh_manager_daemon_up{{daemon="{daemon}"}} {value}'
        )

    for name, config in ENDPOINTS.items():
        up, code = endpoint_status(name, config)
        lines.extend([
            f"# HELP wazuh_{name}_up Endpoint returned an expected HTTP status.",
            f"# TYPE wazuh_{name}_up gauge",
            f"wazuh_{name}_up {up}",
            f"# HELP wazuh_{name}_http_status HTTP status code; zero means no response.",
            f"# TYPE wazuh_{name}_http_status gauge",
            f"wazuh_{name}_http_status {code}",
        ])

    return "\n".join(lines) + "\n"

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    content = build_metrics()
    fd, temporary = tempfile.mkstemp(
        prefix=".wazuh_platform.", suffix=".tmp", dir=OUTPUT_DIR
    )
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, OUTPUT)
        directory_fd = os.open(OUTPUT_DIR, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        try:
            OUTPUT.unlink()
        except FileNotFoundError:
            pass
        raise

if __name__ == "__main__":
    main()
PY

chmod 0755 /usr/local/sbin/wazuh-platform-metrics.py

echo "===== PYTHON SYNTAX CHECK ====="
python3 -m py_compile /usr/local/sbin/wazuh-platform-metrics.py
echo "SYNTAX_EXIT=$?"

echo "===== SCRIPT PERMISSIONS ====="
stat -c '%A %U:%G %n' /usr/local/sbin/wazuh-platform-metrics.py
```

`SYNTAX_EXIT=0` and `-rwxr-xr-x root:root`. Pasting long content can garble the terminal display, so check the file's contents with line numbers.

```bash
nl -ba /usr/local/sbin/wazuh-platform-metrics.py
```

It was 150 lines, as intended.

### 2.2 Running It Once

```bash
echo "===== RUN PLATFORM METRICS ====="
/usr/bin/python3 /usr/local/sbin/wazuh-platform-metrics.py
echo "SCRIPT_EXIT=$?"

echo "===== GENERATED METRICS ====="
cat /var/lib/prometheus/node-exporter/wazuh_platform.prom

echo "===== FILE PERMISSIONS ====="
stat -c '%A %U:%G %s bytes %n' \
  /var/lib/prometheus/node-exporter/wazuh_platform.prom
```

`wazuh_manager_up 1`, all 9 daemons 1, `wazuh_indexer_up 1` (401), `wazuh_dashboard_up 1` (302) and `wazuh_api_up 1` (401). The file was `-rw-r--r-- root:root`, 1,446 bytes.

### 2.3 Service and Timer

```bash
cat > /etc/systemd/system/wazuh-platform-metrics.service <<'UNIT'
[Unit]
Description=Export Wazuh Platform health metrics for Node Exporter

[Service]
Type=oneshot
User=root
Group=root
UMask=0022
ExecStart=/usr/bin/python3 /usr/local/sbin/wazuh-platform-metrics.py
TimeoutStartSec=30

NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
ProtectHostname=true
ProtectClock=true
RestrictSUIDSGID=true
LockPersonality=true
MemoryDenyWriteExecute=true
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6

ReadOnlyPaths=/var/ossec
ReadWritePaths=/var/lib/prometheus/node-exporter
UNIT

cat > /etc/systemd/system/wazuh-platform-metrics.timer <<'UNIT'
[Unit]
Description=Periodic Wazuh Platform metrics update

[Timer]
OnBootSec=45s
OnUnitActiveSec=15s
AccuracySec=1s
Unit=wazuh-platform-metrics.service

[Install]
WantedBy=timers.target
UNIT

echo "===== SYSTEMD UNIT VALIDATION ====="
systemd-analyze verify \
  /etc/systemd/system/wazuh-platform-metrics.service \
  /etc/systemd/system/wazuh-platform-metrics.timer
echo "VERIFY_EXIT=$?"

echo "===== CREATED FILES ====="
stat -c '%A %U:%G %n' \
  /etc/systemd/system/wazuh-platform-metrics.service \
  /etc/systemd/system/wazuh-platform-metrics.timer
```

`VERIFY_EXIT=0`. The pasted display was garbled here too, so check the contents.

```bash
echo "===== SERVICE UNIT ====="
cat /etc/systemd/system/wazuh-platform-metrics.service

echo "===== TIMER UNIT ====="
cat /etc/systemd/system/wazuh-platform-metrics.timer

echo "===== TIMER UNIT VALIDATION ====="
systemd-analyze verify /etc/systemd/system/wazuh-platform-metrics.timer
echo "TIMER_VERIFY_EXIT=$?"
```

Both were written correctly, and `TIMER_VERIFY_EXIT=0`. Enable the timer.

```bash
systemctl daemon-reload
systemctl enable --now wazuh-platform-metrics.timer

echo "===== TIMER STATE ====="
systemctl is-active wazuh-platform-metrics.timer
systemctl is-enabled wazuh-platform-metrics.timer

echo "===== TIMER SCHEDULE ====="
systemctl list-timers wazuh-platform-metrics.timer --no-pager
```

It became `active` and `enabled`.

## Chapter 3: Failing When Run by the Timer

### 3.1 Finding the Failure

```bash
echo "===== TIMER DETAILS ====="
systemctl show wazuh-platform-metrics.timer \
  -p ActiveState -p SubState -p LastTriggerUSec \
  -p NextElapseUSecRealtime -p Result

echo "===== SERVICE RESULT ====="
systemctl show wazuh-platform-metrics.service \
  -p ActiveState -p SubState -p Result -p ExecMainStatus

echo "===== RECENT SERVICE LOG ====="
journalctl -u wazuh-platform-metrics.service -n 15 --no-pager

echo "===== METRICS FILE UPDATE ====="
stat -c '%y %s bytes %n' \
  /var/lib/prometheus/node-exporter/wazuh_platform.prom
```

The service had failed, and the log contained the following error. The `.prom` file had not been rewritten either.

```text
subprocess.TimeoutExpired:
wazuh-control status timed out after 10 seconds
```

```bash
echo "===== PLATFORM METRICS PROCESSES ====="
ps -eo pid,ppid,stat,etime,args | grep -E '[w]azuh-platform-metrics|[w]azuh-control|[w]azuh-control status'

echo "===== WAZUH MANAGER SERVICE ====="
systemctl show wazuh-manager.service \
  -p ActiveState -p SubState -p MainPID -p Result

echo "===== MANAGER PROCESS SUMMARY ====="
ps -eo stat,comm | grep -E 'wazuh|PID' | head -40
```

Wazuh Manager was `active` / `running`, and the 9 daemons were running. What was stuck was `/bin/sh /var/ossec/bin/wazuh-control status`, waiting for an answer.

### 3.2 Stopping Only the Monitoring Service

While investigating, stop only the monitoring timer and service. Wazuh Manager and the Collector are not stopped.

```bash
systemctl stop wazuh-platform-metrics.timer

echo "===== TIMER STATE ====="
systemctl is-active wazuh-platform-metrics.timer

echo "===== METRICS SERVICE STATE ====="
systemctl show wazuh-platform-metrics.service \
  -p ActiveState -p SubState -p Result -p ExecMainStatus

echo "===== REMAINING PROCESSES ====="
ps -eo pid,ppid,stat,etime,args | grep -E '[w]azuh-platform-metrics|[w]azuh-control'
```

The timer stopped, but the service that had already started (`activating`) and `wazuh-control status` remained.

```bash
systemctl stop wazuh-platform-metrics.service

echo "===== METRICS SERVICE ====="
systemctl show wazuh-platform-metrics.service \
  -p ActiveState -p SubState -p Result -p ExecMainStatus

echo "===== REMAINING PROCESSES ====="
ps -eo pid,ppid,stat,etime,args | grep -E '[w]azuh-platform-metrics|[w]azuh-control'
```

The service became `failed`, and no processes remained.

### 3.3 Investigating the Cause

```bash
echo "===== STATUS IMPLEMENTATION ====="
grep -n -A100 -B20 'status)' /var/ossec/bin/wazuh-control | head -140

echo "===== STATUS RELATED FUNCTIONS ====="
grep -n -E 'status|is_running|pid|timeout|sleep' \
  /var/ossec/bin/wazuh-control | head -100

echo "===== MANAGER PROCESS DETAILS ====="
ps -eo pid,ppid,stat,wchan:24,etime,comm | grep -E 'wazuh|PID'
```

`status` first takes a lock and then checks all daemons.

```bash
echo "===== LOCK IMPLEMENTATION ====="
sed -n '35,110p' /var/ossec/bin/wazuh-control

echo "===== STATUS FUNCTION ====="
sed -n '180,235p' /var/ossec/bin/wazuh-control

echo "===== LOCK FILE STATE ====="
ls -la /var/ossec/var/run/wazuh-control* \
  /var/ossec/var/run/*.lock 2>/dev/null
```

It **waits up to 60 seconds** for the lock, exceeding the script's 10-second limit. The monitoring has no need to call `wazuh-control`. Check how Wazuh itself checks daemon state (PID files).

```bash
echo "===== WAZUH PID FILES ====="
find /var/ossec/var/run -maxdepth 1 -type f \
  -name 'wazuh-*.pid' -printf '%f\n' | sort

echo "===== PSTATUS IMPLEMENTATION ====="
sed -n '460,498p' /var/ossec/bin/wazuh-control

echo "===== START SCRIPT LOCK DIRECTORY ====="
ls -ld /var/ossec/var/start-script-lock 2>&1
```

All 9 daemons had a `wazuh-<name>-<PID>.pid` file, and the PIDs matched the process list. `pstatus()` simply reads the PID file and checks with `kill -0` that the process is alive.

## Chapter 4: Changing It to Look at PID Files

### 4.1 Replacing the Function

Replace only `manager_status()` with a version that checks the PID files and `os.kill(pid, 0)`. The HTTP checks and the writing code stay as they are.

In the original build, the script was first backed up with the following command, and then a regular-expression replacement was attempted.

`cp -a /usr/local/sbin/wazuh-platform-metrics.py /usr/local/sbin/wazuh-platform-metrics.py.pre-pid-check-20261122`

At that time the replacement failed because of a mistake in the regular expression, and the script was not changed (the backup was made). So, without regular expressions, we replace from the start of the function to the start of the next function.

> **Run on: VM 220**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/usr/local/sbin/wazuh-platform-metrics.py")
source = path.read_text()

start = source.index("def manager_status():")
end = source.index("def endpoint_status(", start)

replacement = '''def manager_status():
    statuses = {}

    for daemon in REQUIRED_DAEMONS:
        running = False
        pid_files = sorted(
            Path("/var/ossec/var/run").glob(f"{daemon}-*.pid")
        )

        for pid_file in pid_files:
            try:
                pid = int(pid_file.read_text().strip())
                if pid > 1:
                    os.kill(pid, 0)
                    running = True
                    break
            except (ValueError, OSError):
                continue

        statuses[daemon] = int(running)

    manager_up = int(all(statuses.values()))
    return manager_up, statuses

'''

path.write_text(source[:start] + replacement + source[end:])
print("REPLACEMENT=SUCCESS")
PY

echo "===== SYNTAX CHECK ====="
python3 -m py_compile /usr/local/sbin/wazuh-platform-metrics.py
echo "SYNTAX_EXIT=$?"

echo "===== UPDATED FUNCTION ====="
sed -n '35,75p' /usr/local/sbin/wazuh-platform-metrics.py
```

`REPLACEMENT=SUCCESS` and `SYNTAX_EXIT=0`.

### 4.2 Testing the Fixed Script

The timer stays stopped.

```bash
echo "===== RUN UPDATED METRICS SCRIPT ====="
/usr/bin/python3 /usr/local/sbin/wazuh-platform-metrics.py
echo "SCRIPT_EXIT=$?"

echo "===== MANAGER METRICS ====="
grep -E '^wazuh_manager_' \
  /var/lib/prometheus/node-exporter/wazuh_platform.prom

echo "===== ENDPOINT METRICS ====="
grep -E '^wazuh_(indexer|dashboard|api)_' \
  /var/lib/prometheus/node-exporter/wazuh_platform.prom

echo "===== FILE UPDATE ====="
stat -c '%y %s bytes %n' \
  /var/lib/prometheus/node-exporter/wazuh_platform.prom
```

`SCRIPT_EXIT=0`, with `wazuh_manager_up 1`, all 9 daemons 1, and all three HTTP checks `up 1`.

Test whether it also works under systemd's restrictions.

```bash
systemctl reset-failed wazuh-platform-metrics.service

echo "===== RUN SYSTEMD SERVICE ====="
systemctl start wazuh-platform-metrics.service
echo "START_EXIT=$?"

echo "===== SERVICE RESULT ====="
systemctl show wazuh-platform-metrics.service \
  -p ActiveState -p SubState -p Result -p ExecMainStatus

echo "===== SERVICE LOG ====="
journalctl -u wazuh-platform-metrics.service -n 15 --no-pager

echo "===== METRICS FILE ====="
stat -c '%y %s bytes %n' \
  /var/lib/prometheus/node-exporter/wazuh_platform.prom
```

`START_EXIT=0`, `Result=success` and `ExecMainStatus=0` (for a oneshot, becoming `inactive` / `dead` after finishing is normal).

### 4.3 Restoring the Timer

```bash
systemctl enable --now wazuh-platform-metrics.timer

echo "===== TIMER STATE ====="
systemctl is-active wazuh-platform-metrics.timer
systemctl is-enabled wazuh-platform-metrics.timer

echo "===== TIMER SCHEDULE ====="
systemctl list-timers --all wazuh-platform-metrics.timer --no-pager
```

After a short while, check that it keeps running.

```bash
echo "===== TIMER DETAILS ====="
systemctl show wazuh-platform-metrics.timer \
  -p ActiveState -p SubState -p LastTriggerUSec \
  -p NextElapseUSecRealtime -p Result

echo "===== SERVICE RESULT ====="
systemctl show wazuh-platform-metrics.service \
  -p ActiveState -p SubState -p Result -p ExecMainStatus

echo "===== RECENT LOG ====="
journalctl -u wazuh-platform-metrics.service -n 12 --no-pager

echo "===== METRICS FILE ====="
stat -c '%y %s bytes %n' \
  /var/lib/prometheus/node-exporter/wazuh_platform.prom
```

The timer was `active` / `waiting`, the service `success`, and the `.prom` file was being rewritten every 15 seconds.

### 4.4 Visible from Node Exporter?

> **Caution**: Node Exporter listens on `192.168.0.220:9100`, not `127.0.0.1`. `http://127.0.0.1:9100/metrics` cannot connect.

```bash
echo "===== NODE EXPORTER PLATFORM METRICS ====="
curl -fsS http://192.168.0.220:9100/metrics \
  | grep -E '^wazuh_(manager|indexer|dashboard|api)_'
```

`wazuh_manager_up`, the 9 `wazuh_manager_daemon_up` series, `wazuh_indexer_up`, `wazuh_dashboard_up`, `wazuh_api_up` and others were shown.

## Chapter 5: Ingesting into Prometheus

### 5.1 Were They Ingested?

> **Run on: pve** (run at `root@pve:~#`; `pct` cannot be used on VM 220)

```bash
pct exec 103 -- bash -lc '
echo "===== PROMETHEUS TARGET ====="
curl -fsS "http://127.0.0.1:9090/api/v1/query?query=up%7Bjob%3D%22security-core%22%7D"

echo
echo "===== WAZUH MANAGER ====="
curl -fsS "http://127.0.0.1:9090/api/v1/query?query=wazuh_manager_up"

echo
echo "===== WAZUH INDEXER ====="
curl -fsS "http://127.0.0.1:9090/api/v1/query?query=wazuh_indexer_up"

echo
echo "===== WAZUH DASHBOARD ====="
curl -fsS "http://127.0.0.1:9090/api/v1/query?query=wazuh_dashboard_up"

echo
echo "===== WAZUH API ====="
curl -fsS "http://127.0.0.1:9090/api/v1/query?query=wazuh_api_up"
echo
'
```

All were `status=success` with value `1`, ingested with `job="security-core"` and `instance="192.168.0.220:9100"`. Prometheus's settings were not changed.

```bash
pct exec 103 -- bash -lc '
echo "===== WAZUH MANAGER DAEMON METRICS ====="
curl -fsS -G "http://127.0.0.1:9090/api/v1/query" \
  --data-urlencode "query=wazuh_manager_daemon_up"

echo
echo "===== DAEMON METRIC COUNT ====="
curl -fsS -G "http://127.0.0.1:9090/api/v1/query" \
  --data-urlencode "query=count(wazuh_manager_daemon_up)"
echo
'
```

There were 9 `wazuh_manager_daemon_up` series, all 1, and `count(wazuh_manager_daemon_up)` was `9`.

## Chapter 6: Alert Rules for the Wazuh Platform

In the original build, approval was obtained before adding the rules.

### 6.1 The Current Rules

```bash
pct exec 103 -- bash -lc '
echo "===== EXISTING WAZUH COLLECTOR RULES ====="
cat /etc/prometheus/rules/wazuh-collector-alerts.yml

echo
echo "===== REGISTERED RULE FILES ====="
grep -n -A5 -B2 "rule_files:" /etc/prometheus/prometheus.yml
'
```

Following the naming and labels of the Collector rules (Part 33), we add them in a separate file, `/etc/prometheus/rules/wazuh-platform-alerts.yml`. `rule_files` is `/etc/prometheus/rules/*.yml`, so the file is loaded without changing Prometheus's settings.

### 6.2 The Rule File

| Rule | Condition | Severity |
|---|---|---|
| `WazuhManagerDown` | The Manager has been stopped for 1 minute | critical |
| `WazuhManagerDaemonDown` | A required daemon has been stopped for 1 minute | critical |
| `WazuhIndexerDown` | The Indexer has not answered for 1 minute | critical |
| `WazuhDashboardDown` | The Dashboard has not answered for 1 minute | warning |
| `WazuhAPIDown` | The API has not answered for 1 minute | critical |
| `WazuhPlatformMetricsMissing` | The numbers have not arrived for 1 minute | critical |
| `WazuhPlatformMetricsStale` | The `.prom` file has not been rewritten for over 60 seconds | critical |

If a file with the same name exists, it stops without overwriting.

```bash
pct exec 103 -- bash -lc '
FILE=/etc/prometheus/rules/wazuh-platform-alerts.yml

if [ -e "$FILE" ]; then
    echo "ERROR: File already exists; refusing to overwrite."
    stat "$FILE"
else
    cat > "$FILE" <<'"'"'YAML'"'"'
groups:
  - name: wazuh-platform
    interval: 15s
    rules:
      - alert: WazuhManagerDown
        expr: wazuh_manager_up{job="security-core"} == 0
        for: 1m
        labels:
          severity: critical
          component: wazuh-manager
        annotations:
          summary: "Wazuh Manager is not running"
          description: "Wazuh Manager has been unavailable for at least 1 minute."

      - alert: WazuhManagerDaemonDown
        expr: wazuh_manager_daemon_up{job="security-core"} == 0
        for: 1m
        labels:
          severity: critical
          component: wazuh-manager
        annotations:
          summary: "A required Wazuh Manager daemon is down"
          description: "A required Wazuh Manager daemon has been down for at least 1 minute. Check the daemon label."

      - alert: WazuhIndexerDown
        expr: wazuh_indexer_up{job="security-core"} == 0
        for: 1m
        labels:
          severity: critical
          component: wazuh-indexer
        annotations:
          summary: "Wazuh Indexer is unreachable"
          description: "Wazuh Indexer health endpoint has failed for at least 1 minute."

      - alert: WazuhDashboardDown
        expr: wazuh_dashboard_up{job="security-core"} == 0
        for: 1m
        labels:
          severity: warning
          component: wazuh-dashboard
        annotations:
          summary: "Wazuh Dashboard is unreachable"
          description: "Wazuh Dashboard endpoint has failed for at least 1 minute."

      - alert: WazuhAPIDown
        expr: wazuh_api_up{job="security-core"} == 0
        for: 1m
        labels:
          severity: critical
          component: wazuh-api
        annotations:
          summary: "Wazuh API is unreachable"
          description: "Wazuh API endpoint has failed for at least 1 minute."

      - alert: WazuhPlatformMetricsMissing
        expr: absent(wazuh_manager_up{job="security-core"}) or absent(wazuh_indexer_up{job="security-core"}) or absent(wazuh_dashboard_up{job="security-core"}) or absent(wazuh_api_up{job="security-core"})
        for: 1m
        labels:
          severity: critical
          component: wazuh-platform
        annotations:
          summary: "Wazuh Platform metrics are missing"
          description: "One or more Wazuh Platform health metrics have been absent from Prometheus for at least 1 minute."

      - alert: WazuhPlatformMetricsStale
        expr: time() - node_textfile_mtime_seconds{job="security-core",file="/var/lib/prometheus/node-exporter/wazuh_platform.prom"} > 60
        for: 0m
        labels:
          severity: critical
          component: wazuh-platform
        annotations:
          summary: "Wazuh Platform metrics file is stale"
          description: "The Wazuh Platform metrics textfile has not been updated for more than 60 seconds."
YAML
    echo "FILE_CREATED=$?"
    chmod 0644 "$FILE"
    echo "===== FILE DETAILS ====="
    stat -c "%A %U:%G %s bytes %n" "$FILE"
fi
'
```

It was created as `-rw-r--r-- root:root 2823 bytes`.

### 6.3 Checking and Loading

```bash
pct exec 103 -- bash -lc '
echo "===== PLATFORM RULE VALIDATION ====="
promtool check rules /etc/prometheus/rules/wazuh-platform-alerts.yml
echo "PLATFORM_RULE_EXIT=$?"

echo
echo "===== FULL PROMETHEUS CONFIG VALIDATION ====="
promtool check config /etc/prometheus/prometheus.yml
echo "CONFIG_EXIT=$?"
'
```

The Wazuh platform rules gave `SUCCESS: 7 rules found`; the whole-configuration check also read the Collector rules (9) and the two files, and all exit codes were 0.

```bash
pct exec 103 -- bash -lc '
echo "===== PROMETHEUS RELOAD ====="
systemctl reload prometheus
echo "RELOAD_EXIT=$?"

echo
echo "===== SERVICE STATUS ====="
systemctl is-active prometheus

echo
echo "===== MAIN PID ====="
systemctl show prometheus -p MainPID

echo
echo "===== RECENT LOG ====="
journalctl -u prometheus -n 15 --no-pager
'
```

`RELOAD_EXIT=0`; Prometheus was `active`, its PID stayed `98`, and `Completed loading of configuration file` appeared.

### 6.4 Checking the 16 Rules

```bash
pct exec 103 -- bash -lc '
echo "===== WAZUH ALERT RULES ====="
curl -fsS "http://127.0.0.1:9090/api/v1/rules" \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
groups=data.get(\"data\",{}).get(\"groups\",[])
for group in groups:
    if group.get(\"name\", \"\").startswith(\"wazuh-\"):
        rules=group.get(\"rules\",[])
        print(\"GROUP:\", group[\"name\"])
        for rule in rules:
            print(
                rule.get(\"name\"),
                \"health=\" + str(rule.get(\"health\")),
                \"state=\" + str(rule.get(\"state\"))
            )
        print(\"COUNT:\", len(rules))
"

echo
echo "===== ACTIVE ALERT COUNT ====="
curl -fsS "http://127.0.0.1:9090/api/v1/alerts" \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
alerts=data.get(\"data\",{}).get(\"alerts\",[])
print(\"ACTIVE_ALERT_COUNT:\",len(alerts))
"
'
```

| Group | Rules | State |
|---|---:|---|
| `wazuh-collector` | 9 | All `health=ok`, `state=inactive` |
| `wazuh-platform` | 7 | All `health=ok`, `state=inactive` |

`ACTIVE_ALERT_COUNT: 0`. `inactive` means that no rule's condition is currently met.

## Closing Notes

In Part 34 we made the state of the Wazuh platform itself observable with Prometheus too.

| Item | Result |
|---|---|
| Script | `/usr/local/sbin/wazuh-platform-metrics.py` (root, `0755`); backup `wazuh-platform-metrics.py.pre-pid-check-20261122` |
| How the Manager is checked | PID files and `kill -0` instead of `wazuh-control status` (does not touch Wazuh's lock) |
| Output | `/var/lib/prometheus/node-exporter/wazuh_platform.prom` |
| Scheduled runs | `wazuh-platform-metrics.service` (oneshot) and `.timer` (every 15 seconds) |
| Prometheus | Ingested without changing settings; rule file `/etc/prometheus/rules/wazuh-platform-alerts.yml` (7 rules) |
| Total rules | Collector 9 + Wazuh platform 7 = 16, all `ok`, `inactive`, 0 firing |
| Notifications | Alertmanager not set up |

In Part 35 we test, without stopping production services, whether the rules fire correctly with test data, and check the production values.

# Part 35: Testing the Alert Rules and Checking in Production
## Introduction

### About This Book

This is Part 35 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". In Parts 33 and 34 we put 16 alert rules into Prometheus: 9 for the Collector and 7 for the Wazuh platform. However, since nothing is currently wrong, we do not yet know whether the rules really fire.

Here we test the rules **without stopping production services**. Prometheus's `promtool test rules` is a tool that evaluates the rules against test time series written in a file and compares the results with expected ones.

1. For the 7 Wazuh platform rules, test that they do not fire when things are normal and do fire when they are not
2. In production Prometheus, check the actual values and the state of the 16 rules

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root). Commands inside LXC 103 (`lxc-prometheus`) are run with `pct exec 103 -- …`

## Chapter 1: Preparing the Rule Tests

### 1.1 promtool's Features

> **Run on: pve**

```bash
pct exec 103 -- bash -lc '
echo "===== PROMETHEUS VERSION ====="
promtool --version

echo
echo "===== RULE TEST HELP ====="
promtool test rules --help
'
```

promtool is 3.12.0, and `test rules` is available.

### 1.2 The Test File

The 7 rules are tested in the following 4 scenarios.

| Scenario | Data supplied | Expected result |
|---|---|---|
| `normal-no-alerts` | All 1, and the `.prom` file is fresh | None of the 7 fires |
| `service-down-alerts` | Manager, daemon, Indexer, Dashboard and API all 0 | 5 rules fire |
| `metrics-missing-alert` | Only the API number is missing | `WazuhPlatformMetricsMissing` fires |
| `metrics-stale-alert` | The `.prom` file's modification time is old | `WazuhPlatformMetricsStale` fires |

The test file is placed in `/tmp`; the production rule file is not changed.

```bash
pct exec 103 -- bash -lc '
cat > /tmp/wazuh-platform-alerts.test.yml <<'"'"'YAML'"'"'
rule_files:
  - /etc/prometheus/rules/wazuh-platform-alerts.yml

evaluation_interval: 15s

tests:
  - name: normal-no-alerts
    interval: 15s
    input_series:
      - series: wazuh_manager_up{job="security-core"}
        values: "1+0x8"
      - series: wazuh_manager_daemon_up{job="security-core",daemon="wazuh-analysisd"}
        values: "1+0x8"
      - series: wazuh_indexer_up{job="security-core"}
        values: "1+0x8"
      - series: wazuh_dashboard_up{job="security-core"}
        values: "1+0x8"
      - series: wazuh_api_up{job="security-core"}
        values: "1+0x8"
      - series: node_textfile_mtime_seconds{job="security-core",file="/var/lib/prometheus/node-exporter/wazuh_platform.prom"}
        values: "120+0x8"
    alert_rule_test:
      - eval_time: 2m
        alertname: WazuhManagerDown
        exp_alerts: []
      - eval_time: 2m
        alertname: WazuhManagerDaemonDown
        exp_alerts: []
      - eval_time: 2m
        alertname: WazuhIndexerDown
        exp_alerts: []
      - eval_time: 2m
        alertname: WazuhDashboardDown
        exp_alerts: []
      - eval_time: 2m
        alertname: WazuhAPIDown
        exp_alerts: []
      - eval_time: 2m
        alertname: WazuhPlatformMetricsMissing
        exp_alerts: []
      - eval_time: 2m
        alertname: WazuhPlatformMetricsStale
        exp_alerts: []

  - name: service-down-alerts
    interval: 15s
    input_series:
      - series: wazuh_manager_up{job="security-core"}
        values: "0+0x8"
      - series: wazuh_manager_daemon_up{job="security-core",daemon="wazuh-analysisd"}
        values: "0+0x8"
      - series: wazuh_indexer_up{job="security-core"}
        values: "0+0x8"
      - series: wazuh_dashboard_up{job="security-core"}
        values: "0+0x8"
      - series: wazuh_api_up{job="security-core"}
        values: "0+0x8"
    alert_rule_test:
      - eval_time: 1m
        alertname: WazuhManagerDown
        exp_alerts:
          - exp_labels:
              job: security-core
              severity: critical
              component: wazuh-manager
      - eval_time: 1m
        alertname: WazuhManagerDaemonDown
        exp_alerts:
          - exp_labels:
              job: security-core
              daemon: wazuh-analysisd
              severity: critical
              component: wazuh-manager
      - eval_time: 1m
        alertname: WazuhIndexerDown
        exp_alerts:
          - exp_labels:
              job: security-core
              severity: critical
              component: wazuh-indexer
      - eval_time: 1m
        alertname: WazuhDashboardDown
        exp_alerts:
          - exp_labels:
              job: security-core
              severity: warning
              component: wazuh-dashboard
      - eval_time: 1m
        alertname: WazuhAPIDown
        exp_alerts:
          - exp_labels:
              job: security-core
              severity: critical
              component: wazuh-api

  - name: metrics-missing-alert
    interval: 15s
    input_series:
      - series: wazuh_manager_up{job="security-core"}
        values: "1+0x8"
      - series: wazuh_indexer_up{job="security-core"}
        values: "1+0x8"
      - series: wazuh_dashboard_up{job="security-core"}
        values: "1+0x8"
    alert_rule_test:
      - eval_time: 1m
        alertname: WazuhPlatformMetricsMissing
        exp_alerts:
          - exp_labels:
              job: security-core
              severity: critical
              component: wazuh-platform

  - name: metrics-stale-alert
    interval: 15s
    input_series:
      - series: node_textfile_mtime_seconds{job="security-core",file="/var/lib/prometheus/node-exporter/wazuh_platform.prom"}
        values: "0+0x8"
    alert_rule_test:
      - eval_time: 2m
        alertname: WazuhPlatformMetricsStale
        exp_alerts:
          - exp_labels:
              job: security-core
              file: /var/lib/prometheus/node-exporter/wazuh_platform.prom
              severity: critical
              component: wazuh-platform
YAML

echo "===== TEST FILE SYNTAX CHECK ====="
python3 -c "import yaml; yaml.safe_load(open(\"/tmp/wazuh-platform-alerts.test.yml\")); print(\"YAML_SYNTAX=OK\")"
echo "===== TEST FILE DETAILS ====="
stat -c "%A %U:%G %s bytes %n" /tmp/wazuh-platform-alerts.test.yml
'
```

The file was created as `-rw-r--r-- root:root 4001 bytes`. The final YAML check in Python gives `ModuleNotFoundError: No module named 'yaml'` because `python3-yaml` is not installed in LXC 103, but this is not a problem. The YAML is read by the next command, `promtool test rules` (no packages are added).

## Chapter 2: Testing the Rules

### 2.1 First Run

```bash
pct exec 103 -- bash -lc '
echo "===== PROMETHEUS RULE UNIT TEST ====="
promtool test rules /tmp/wazuh-platform-alerts.test.yml
echo "PROMTOOL_TEST_EXIT=$?"
'
```

It was `FAILED` (`PROMTOOL_TEST_EXIT=1`). Looking at the details, **all 7 abnormal-case rules fired as expected**, and the normal case's "does not fire" also matched. The mismatch was because the test file did not specify `exp_annotations` (`summary` and `description`). promtool also compares the annotations attached to the actual alert.

### 2.2 Adding the Expected Annotations

First, read the relevant part of the test file.

```bash
pct exec 103 -- bash -lc '
echo "===== TEST FILE: ALERT EXPECTATIONS ====="
grep -n -A12 -B2 "alertname:\|exp_alerts:" /tmp/wazuh-platform-alerts.test.yml
'
```

In the abnormal cases, the expectations are under `exp_labels`. Add `exp_annotations` at the same level. The normal case's `exp_alerts: []` stays as it is. The annotation texts are the same as in the production rules (Part 34).

```bash
pct exec 103 -- bash -lc '
python3 - <<'"'"'PY'"'"'
from pathlib import Path

p = Path("/tmp/wazuh-platform-alerts.test.yml")
lines = p.read_text().splitlines()

annotations = {
    "WazuhManagerDown": (
        "Wazuh Manager is not running",
        "Wazuh Manager has been unavailable for at least 1 minute."
    ),
    "WazuhManagerDaemonDown": (
        "A required Wazuh Manager daemon is down",
        "A required Wazuh Manager daemon has been down for at least 1 minute. Check the daemon label."
    ),
    "WazuhIndexerDown": (
        "Wazuh Indexer is unreachable",
        "Wazuh Indexer health endpoint has failed for at least 1 minute."
    ),
    "WazuhDashboardDown": (
        "Wazuh Dashboard is unreachable",
        "Wazuh Dashboard endpoint has failed for at least 1 minute."
    ),
    "WazuhAPIDown": (
        "Wazuh API is unreachable",
        "Wazuh API endpoint has failed for at least 1 minute."
    ),
    "WazuhPlatformMetricsMissing": (
        "Wazuh Platform metrics are missing",
        "One or more Wazuh Platform health metrics have been absent from Prometheus for at least 1 minute."
    ),
    "WazuhPlatformMetricsStale": (
        "Wazuh Platform metrics file is stale",
        "The Wazuh Platform metrics textfile has not been updated for more than 60 seconds."
    ),
}

out = []
current = None
added = set()

for line in lines:
    out.append(line)
    stripped = line.strip()

    if stripped.startswith("alertname: "):
        current = stripped.split(": ", 1)[1]

    if current in annotations and stripped.startswith("component: "):
        summary, description = annotations[current]
        out.extend([
            "            exp_annotations:",
            "              summary: " + summary,
            "              description: " + description
        ])
        added.add(current)
        current = None

missing = set(annotations) - added
if missing:
    raise RuntimeError("Could not update: " + ", ".join(sorted(missing)))

p.write_text("\n".join(out) + "\n")
print("ANNOTATIONS_ADDED:", len(added))
PY

echo "===== ANNOTATION COUNT ====="
grep -c "exp_annotations:" /tmp/wazuh-platform-alerts.test.yml
echo "===== UPDATED EXPECTATIONS ====="
grep -n -A8 "alertname: WazuhManagerDown" /tmp/wazuh-platform-alerts.test.yml
'
```

`ANNOTATIONS_ADDED: 7`, and the count of `exp_annotations:` was also `7`.

### 2.3 Second Run

Test with the same command as the first run.

```bash
pct exec 103 -- bash -lc '
echo "===== PROMETHEUS RULE UNIT TEST ====="
promtool test rules /tmp/wazuh-platform-alerts.test.yml
echo "PROMTOOL_TEST_EXIT=$?"
'
```

```text
===== PROMETHEUS RULE UNIT TEST =====
  SUCCESS

PROMTOOL_TEST_EXIT=0
```

| What was tested | Result |
|---|---|
| Not firing when normal (7) | Pass |
| Manager stopped | Pass |
| Manager daemon stopped | Pass |
| Indexer stopped | Pass |
| Dashboard stopped | Pass |
| API stopped | Pass |
| Numbers not arriving | Pass |
| `.prom` file stale | Pass |

This test uses test data; production services and numbers were not changed.

## Chapter 3: Checking the Production Values

### 3.1 The Wazuh Platform and the 16 Rules

Query production Prometheus for the values it is currently collecting (reads only).

> **Caution**: If you use `'` in strings inside Python, it collides with the outer `'` of `pct exec 103 -- python3 -c '…'`, and from that point on the text is run as bash commands (a series of `syntax error near unexpected token` appears). The command below avoids `'` inside the Python. If input stops at a `>` continuation prompt, press `Ctrl+C` to get out before running it.

```bash
pct exec 103 -- python3 -c '
import json, urllib.request, urllib.parse

base = "http://127.0.0.1:9090"

def get(path, params=None):
    url = base + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.load(r)["data"]

def query(expr):
    return get("/api/v1/query", {"query": expr})["result"]

print("===== SECURITY-CORE SCRAPE =====")
for x in query("up{job=\"security-core\"}"):
    print(x["metric"].get("instance"), "UP=", x["value"][1])

print("===== WAZUH PLATFORM HEALTH =====")
for metric in ["wazuh_manager_up", "wazuh_indexer_up", "wazuh_dashboard_up", "wazuh_api_up"]:
    for x in query(metric + "{job=\"security-core\"}"):
        print(metric, "=", x["value"][1])

print("===== MANAGER DAEMONS =====")
daemons = query("wazuh_manager_daemon_up{job=\"security-core\"}")
print("DAEMON_COUNT:", len(daemons))
for x in sorted(daemons, key=lambda x: x["metric"].get("daemon", "")):
    print(x["metric"].get("daemon"), "=", x["value"][1])

print("===== PLATFORM METRICS AGE =====")
expr = "time() - node_textfile_mtime_seconds{job=\"security-core\",file=\"/var/lib/prometheus/node-exporter/wazuh_platform.prom\"}"
for x in query(expr):
    print("AGE_SECONDS:", x["value"][1])

print("===== LOADED ALERT RULES =====")
rules = get("/api/v1/rules", {"type": "alert"})
total = 0
for group in rules["groups"]:
    total += len(group["rules"])
    print("GROUP:", group["name"], "RULES:", len(group["rules"]))
    for rule in group["rules"]:
        print(rule["name"], "health=", rule.get("health"), "state=", rule.get("state"))
print("TOTAL_ALERT_RULES:", total)

print("===== ACTIVE ALERTS =====")
alerts = get("/api/v1/alerts")["alerts"]
active = [a for a in alerts if a.get("state") == "firing"]
print("FIRING_ALERT_COUNT:", len(active))
for alert in active:
    print(alert.get("labels", {}).get("alertname"), alert.get("labels", {}))
'
```

| Item | Actual value |
|---|---|
| Node Exporter (`192.168.0.220:9100`) | `UP= 1` |
| Wazuh Manager, Indexer, Dashboard, API | All `1` |
| Manager daemons | All 9 `1` |
| Age of `wazuh_platform.prom` | About 16.3 seconds |
| Alert rules | 16 (all `health=ok`, `state=inactive`) |
| Firing alerts | 0 |

### 3.2 The Collector's Values

```bash
pct exec 103 -- python3 -c '
import json, urllib.request, urllib.parse

base = "http://127.0.0.1:9090"
metrics = [
    "wazuh_collector_service_up",
    "wazuh_collector_restarts_total",
    "wazuh_collector_state_valid",
    "wazuh_collector_inode_match",
    "wazuh_collector_unread_bytes",
    "wazuh_collector_state_mtime_seconds",
]

for metric in metrics:
    params = urllib.parse.urlencode({"query": metric + "{job=\"security-core\"}"})
    url = base + "/api/v1/query?" + params
    with urllib.request.urlopen(url, timeout=5) as r:
        result = json.load(r)["data"]["result"]
    print("===== " + metric + " =====")
    if not result:
        print("MISSING")
    for item in result:
        print("value=", item["value"][1])
'
```

| Metric | Actual value |
|---|---:|
| `wazuh_collector_service_up` | 1 |
| `wazuh_collector_restarts_total` | 0 |
| `wazuh_collector_state_valid` | 1 |
| `wazuh_collector_inode_match` | 1 |
| `wazuh_collector_unread_bytes` | 0 |
| `wazuh_collector_state_mtime_seconds` | Obtained |

## Closing Notes

In Part 35 we tested the alert rules and checked the production values.

| Item | Result |
|---|---|
| Test file | `/tmp/wazuh-platform-alerts.test.yml` (the production rules were not changed) |
| Rule test | `SUCCESS` with `promtool test rules` (7 normal and 7 abnormal checks) |
| Why the first run failed | The test file had no expected annotations (`exp_annotations`) |
| Production values | Wazuh platform, the 9 daemons and the Collector all normal |
| Rules | All 16 `ok`, `inactive`, 0 firing |
| Notifications | Alertmanager not set up (deliberately deferred) |

The monitoring foundation from Wazuh and the Collector through the Prometheus rules is now complete. In Part 36 we check, using reads only, the PostgreSQL that stores the events.

# Part 36: Checking PostgreSQL
## Introduction

### About This Book

This is Part 36 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". By Part 35, the monitoring foundation from Wazuh and the Collector through the Prometheus rules was complete. Here we check, **using reads only**, the **PostgreSQL** where the Collector stores events (LXC 109, 192.168.0.151, database `security_workbench`, table `incident.alert_events`).

| What we check | Result |
|---|---|
| Connectivity | Normal |
| Permissions of the Collector's role (`wazuh_collector`) | INSERT only; no administrative permissions |
| Table structure (primary key, indexes, constraints) | Normal |
| Data contents (duplicates, malformed values) | 55,811 rows, 0 anomalies |
| Ingestion delay | Last 30 minutes: 0.86 seconds on average |
| Size, VACUUM, connection count | Normal |
| WAL, checkpoints | Normal; WAL archiving not configured |
| Backups | **No PostgreSQL backup found** |

The last item becomes the task for Part 37.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **postgresql**: LXC 109 (192.168.0.151, root). SQL is run with `sudo -u postgres psql …`

## Chapter 1: Connectivity and the Collector's Settings

### 1.1 Can We Connect?

> **Run on: VM 220**

```bash
echo "===== POSTGRESQL CONNECTIVITY ====="
pg_isready -h 192.168.0.151 -p 5432 -t 5
echo "PG_ISREADY_EXIT=$?"
```

```text
192.168.0.151:5432 - accepting connections
PG_ISREADY_EXIT=0
```

### 1.2 Where the Collector Connects

From the Collector's `DB_CONFIG`, extract only the connection destination fields. `DB_CONFIG` contains values that reference environment variables and the like, so the file is parsed as Python syntax and only the values of fixed fields (`host`, `hostaddr`, `port`, `dbname`, `database`, `user`) are shown. Passwords and the like are not shown.

```bash
python3 - <<'PY'
import ast
from pathlib import Path

p = Path("/usr/local/lib/wazuh-collector/collector.py")
tree = ast.parse(p.read_text())

safe_keys = {"host", "hostaddr", "port", "dbname", "database", "user"}

for node in tree.body:
    if not isinstance(node, ast.Assign):
        continue
    if not any(isinstance(t, ast.Name) and t.id == "DB_CONFIG" for t in node.targets):
        continue

    if not isinstance(node.value, ast.Dict):
        print("DB_CONFIG is not a literal dictionary")
        break

    print("===== SAFE DB CONFIGURATION =====")
    for key_node, value_node in zip(node.value.keys, node.value.values):
        if not isinstance(key_node, ast.Constant):
            continue
        key = key_node.value
        if key not in safe_keys:
            continue

        if isinstance(value_node, ast.Constant):
            value = value_node.value
        elif isinstance(value_node, ast.Name):
            value = "<dynamic reference: " + value_node.id + ">"
        else:
            value = "<dynamic expression>"

        print(f"{key} = {value}")
    break
else:
    print("DB_CONFIG assignment not found")
PY
```

```text
===== SAFE DB CONFIGURATION =====
host = postgresql.neomedia.mydns.jp
hostaddr = 192.168.0.151
port = 5432
dbname = security_workbench
user = wazuh_collector
```

## Chapter 2: The Table and Permissions

### 2.1 Table Structure

> **Run on: postgresql**

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c '\d+ incident.alert_events'
```

| Item | Result |
|---|---|
| Primary key | `event_id` (the same event cannot be inserted twice) |
| Indexes | 5 |
| CHECK constraints | 3 (`rule_level` 0–16, `srcport` 0–65535, `mitre` is a JSON object) |
| Raw log columns | None (no `full_log` or similar; only fixed fields are stored) |

### 2.2 Permissions of the Collector's Role

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    current_user AS inspected_by,
    has_schema_privilege('wazuh_collector', 'incident', 'USAGE') AS schema_usage,
    has_table_privilege('wazuh_collector', 'incident.alert_events', 'INSERT') AS can_insert,
    has_table_privilege('wazuh_collector', 'incident.alert_events', 'SELECT') AS can_select,
    has_table_privilege('wazuh_collector', 'incident.alert_events', 'UPDATE') AS can_update,
    has_table_privilege('wazuh_collector', 'incident.alert_events', 'DELETE') AS can_delete;
"
```

```text
 inspected_by | schema_usage | can_insert | can_select | can_update | can_delete
--------------+--------------+------------+------------+------------+------------
 postgres     | t            | t          | f          | f          | f
```

The Collector can write events but cannot read, change or delete existing data. This is an important safeguard that makes it hard to rewrite stored events even if the Collector is compromised.

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    rolname,
    rolsuper AS is_superuser,
    rolinherit AS inherits_roles,
    rolcreaterole AS can_create_roles,
    rolcreatedb AS can_create_databases,
    rolcanlogin AS can_login,
    rolreplication AS can_replicate,
    rolbypassrls AS bypasses_row_security
FROM pg_roles
WHERE rolname = 'wazuh_collector';
"
```

Only `can_login` was `t`; superuser, role inheritance, permission to create roles or databases, replication and bypassing RLS were all `f`. These permissions are not changed.

## Chapter 3: Data Contents

### 3.1 Malformed Values and Duplicates

Individual events (IP addresses, agent names and so on) are not shown; only aggregate values are examined.

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    COUNT(*) AS total_records,
    COUNT(DISTINCT event_id) AS unique_event_ids,
    COUNT(*) FILTER (WHERE rule_level < 0 OR rule_level > 16) AS invalid_rule_levels,
    COUNT(*) FILTER (WHERE srcport < 0 OR srcport > 65535) AS invalid_source_ports,
    COUNT(*) FILTER (WHERE jsonb_typeof(mitre) <> 'object') AS invalid_mitre_objects,
    COUNT(*) FILTER (WHERE cardinality(rule_groups) = 0) AS empty_rule_groups,
    COUNT(*) FILTER (WHERE event_timestamp > now() + interval '5 minutes') AS future_events,
    COUNT(*) FILTER (WHERE ingested_at < event_timestamp) AS negative_ingestion_lag,
    ROUND(
        EXTRACT(EPOCH FROM (now() - MAX(ingested_at)))::numeric,
        2
    ) AS latest_ingestion_age_seconds,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (ingested_at - event_timestamp)))::numeric,
        3
    ) AS avg_ingestion_lag_seconds
FROM incident.alert_events;
"
```

| Item | Result |
|---|---:|
| Rows | 55,811 |
| Distinct `event_id`s | 55,811 |
| Malformed rule level, source port or MITRE | 0 |
| Empty rule groups | 0 |
| Future timestamps / ingestion before the event | 0 |
| Time since the last ingestion | 137.03 seconds |
| Average ingestion delay | 19,468.776 seconds |

The average delay comes out large, about 5.5 hours, probably because the past archives added later in Part 32 push the average up. Look at it by period.

### 3.2 Ingestion Delay by Period

> **Note**: In PostgreSQL, an alias given within the same SELECT (`ingestion_period`) cannot be referenced from a `CASE` inside `ORDER BY` (it gives `column "ingestion_period" does not exist`). The command below first classifies the period in a CTE (`WITH`) and then aggregates.

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
WITH classified AS (
    SELECT
        CASE
            WHEN ingested_at >= now() - interval '30 minutes' THEN 'last_30m'
            WHEN ingested_at >= now() - interval '24 hours' THEN 'last_24h'
            ELSE 'older'
        END AS ingestion_period,
        EXTRACT(EPOCH FROM (ingested_at - event_timestamp)) AS lag_seconds
    FROM incident.alert_events
)
SELECT
    ingestion_period,
    COUNT(*) AS records,
    ROUND(AVG(lag_seconds)::numeric, 2) AS avg_lag_seconds,
    ROUND(percentile_cont(0.50) WITHIN GROUP (ORDER BY lag_seconds)::numeric, 2) AS median_lag_seconds,
    ROUND(percentile_cont(0.95) WITHIN GROUP (ORDER BY lag_seconds)::numeric, 2) AS p95_lag_seconds,
    ROUND(MAX(lag_seconds)::numeric, 2) AS max_lag_seconds
FROM classified
GROUP BY ingestion_period
ORDER BY CASE ingestion_period
    WHEN 'last_30m' THEN 1
    WHEN 'last_24h' THEN 2
    ELSE 3
END;
"
```

| Period | Rows | Average | Median | 95% |
|---|---:|---:|---:|---:|
| Last 30 minutes | 15 | 0.86 s | 0.91 s | 0.99 s |
| Last 24 hours (excluding the 30 minutes) | 35,705 | 18,587.53 s | 1.07 s | 322,119.38 s |
| Older | 20,098 | 21,042.09 s | 11,725.46 s | 61,876.70 s |

The last 30 minutes were ingested in under a second, so current ingestion is normal. The 24-hour median is also about 1 second; the average is large because of old events added later.

## Chapter 4: Size and Connections

### 4.1 Table Size and VACUUM

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    schemaname,
    relname AS table_name,
    pg_size_pretty(pg_relation_size(relid)) AS table_size,
    pg_size_pretty(pg_indexes_size(relid)) AS indexes_size,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    n_live_tup AS estimated_live_rows,
    n_dead_tup AS estimated_dead_rows,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'incident'
  AND relname = 'alert_events';
"
```

The table was 12MB and the indexes 6008kB, 18MB in total. About 55,826 live rows and 766 dead rows (about 1.4%), and automatic VACUUM and ANALYZE were running. No manual VACUUM is needed.

### 4.2 Connection Count

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    current_setting('max_connections') AS max_connections,
    COUNT(*) AS total_connections,
    COUNT(*) FILTER (WHERE state = 'active') AS active_connections,
    COUNT(*) FILTER (WHERE state = 'idle') AS idle_connections,
    COUNT(*) FILTER (WHERE state = 'idle in transaction') AS idle_in_transaction,
    COUNT(*) FILTER (WHERE usename = 'wazuh_collector') AS collector_connections
FROM pg_stat_activity;
"
```

14 connections against a limit of 100; `idle in transaction` (connections stuck with an open transaction) was 0, and the Collector had 1 connection.

### 4.3 Database Size

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    datname AS database_name,
    pg_size_pretty(pg_database_size(datname)) AS database_size,
    pg_database_size(datname) AS database_size_bytes
FROM pg_database
WHERE datname = 'security_workbench';
"
```

The whole of `security_workbench` was 26MB.

## Chapter 5: WAL and Checkpoints

### 5.1 Replication Slots

An unused slot would keep WAL from being removed so that it piles up.

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    slot_name,
    slot_type,
    active,
    restart_lsn,
    CASE
        WHEN restart_lsn IS NOT NULL
        THEN pg_size_pretty(
            pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)::bigint
        )
        ELSE NULL
    END AS retained_wal
FROM pg_replication_slots;

SELECT
    COUNT(*) AS replication_slot_count
FROM pg_replication_slots;
"
```

There were 0 slots.

### 5.2 WAL and Checkpoint Settings

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    name,
    setting,
    unit,
    source
FROM pg_settings
WHERE name IN (
    'wal_level',
    'wal_keep_size',
    'max_wal_size',
    'min_wal_size',
    'checkpoint_timeout',
    'checkpoint_completion_target',
    'archive_mode',
    'archive_timeout',
    'full_page_writes',
    'synchronous_commit'
)
ORDER BY name;
"
```

| Setting | Value |
|---|---|
| `wal_level` | `replica` |
| `max_wal_size` / `min_wal_size` | 1GB / 80MB |
| `checkpoint_timeout` | 300 seconds |
| `checkpoint_completion_target` | 0.9 |
| `full_page_writes` | `on` |
| `synchronous_commit` | `on` |
| `archive_mode` | `off` |
| `wal_keep_size` | 0 |

`full_page_writes` and `synchronous_commit`, which matter for consistency after a crash and for durable commits, are both `on`. On the other hand, because `archive_mode` is `off`, recovery to an arbitrary point in time using archived WAL (PITR) is not possible.

### 5.3 Checkpoint History

> **Note**: In PostgreSQL 17, `pg_stat_checkpointer` has no `num_done` column (it gives `column "num_done" does not exist`). Check the column names first.

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'pg_catalog'
  AND table_name = 'pg_stat_checkpointer'
ORDER BY ordinal_position;
"
```

The columns were `num_timed`, `num_requested`, `restartpoints_timed`, `restartpoints_req`, `restartpoints_done`, `write_time`, `sync_time`, `buffers_written` and `stats_reset`.

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    stats_reset,
    num_timed AS scheduled_checkpoints,
    num_requested AS requested_checkpoints,
    restartpoints_timed,
    restartpoints_req,
    restartpoints_done,
    ROUND(write_time::numeric, 2) AS write_time_ms,
    ROUND(sync_time::numeric, 2) AS sync_time_ms,
    buffers_written,
    pg_size_pretty(
        (buffers_written * current_setting('block_size')::bigint)
    ) AS checkpoint_write_volume
FROM pg_stat_checkpointer;
"
```

Since statistics began on 2026-11-17, there had been 1,349 scheduled checkpoints and only 4 requested ones. About 241MB was written and sync time totaled about 28 seconds; checkpoints are stable.

### 5.4 WAL Files

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    pg_size_pretty(COALESCE(SUM(size), 0)::bigint) AS wal_directory_size,
    COUNT(*) AS wal_file_count,
    pg_size_pretty(
        COALESCE(MAX(size), 0)::bigint
    ) AS largest_file
FROM pg_ls_waldir();
"
```

WAL was 32MB (two 16MB files), small against the 1GB limit, and not piling up.

## Chapter 6: Looking for Backups

### 6.1 Archiving and the Data Location

```bash
sudo -u postgres psql -X -d security_workbench -P pager=off -c "
SELECT
    name,
    setting,
    unit,
    source
FROM pg_settings
WHERE name IN (
    'data_directory',
    'archive_mode',
    'archive_command',
    'archive_timeout',
    'wal_level'
)
ORDER BY name;
"
```

The data is in `/var/lib/postgresql/17/main` (PostgreSQL 17); `archive_mode` was `off` and `archive_command` was `(disabled)`.

### 6.2 Backup Services and Files

```bash
echo "===== BACKUP RELATED SYSTEMD UNITS ====="
systemctl list-timers --all --no-pager | grep -Ei 'backup|postgres|pgbackrest|barman|borg|restic|rclone|snapshot'
echo "===== BACKUP RELATED SERVICES ====="
systemctl list-units --type=service --all --no-pager | grep -Ei 'backup|postgres|pgbackrest|barman|borg|restic|rclone'
echo "===== COMMON BACKUP DIRECTORIES ====="
for d in /var/backups /backup /backups /srv/backup /mnt/backup; do
    if [ -d "$d" ]; then
        stat -c '%A %U:%G %n' "$d"
    fi
done
```

What was found was only `dpkg-db-backup.timer` (a backup of Debian's package management database, not of PostgreSQL) and the PostgreSQL service itself. pgBackRest, Barman, Borg, Restic and the like were not present either. Look only at file names, times and sizes (the contents are not read).

```bash
echo "===== /var/backups FILE INVENTORY ====="
find /var/backups -maxdepth 3 -type f \
  -printf '%TY-%Tm-%Td %TH:%TM | %s bytes | %p\n' \
  2>/dev/null | sort -r

echo "===== BACKUP-RELATED CRON FILE NAMES ====="
find /etc/cron.d /etc/cron.daily /etc/cron.hourly /etc/cron.weekly \
  -maxdepth 1 -type f \
  \( -iname '*backup*' -o -iname '*postgres*' -o -iname '*pg*' \) \
  -printf '%p\n' 2>/dev/null
```

`/var/backups` held only package management files such as `alternatives.tar.0` and `dpkg.*`; there were no PostgreSQL backup files and no cron jobs.

| Item | Result |
|---|---|
| PostgreSQL backup files | None |
| cron for PostgreSQL | None |
| systemd timer for PostgreSQL | None |
| WAL archiving | Disabled |

**As far as we looked, there is no backup from which PostgreSQL data could be restored.** If the database were damaged, the events collected from Wazuh and the analysis records could be lost.

## Closing Notes

In Part 36 we checked PostgreSQL using reads only.

| Item | Result |
|---|---|
| Collector permissions | INSERT only (no SELECT, UPDATE or DELETE; no administrative permissions) |
| Data | 55,811 rows, 0 duplicates or malformed values |
| Ingestion delay | Last 30 minutes: 0.86 seconds on average |
| Size | Table 18MB, DB 26MB, 1.4% dead rows |
| Connections | 14 of 100, `idle in transaction` 0 |
| WAL, checkpoints | Normal (WAL 32MB, 0 slots) |
| Issues | No WAL archiving, no PostgreSQL backups |

In Part 37 we back up LXC 109, where PostgreSQL runs, with Proxmox, restore it to an LXC with a different number, and test whether it can really be restored.

# Part 37: Backing Up PostgreSQL and Testing a Restore
## Introduction

### About This Book

This is Part 37 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". The check in Part 36 showed that there was no PostgreSQL backup. Here we back up **LXC 109**, where PostgreSQL runs, with Proxmox's `vzdump`, **restore it to an LXC with a different number (110)**, and test that PostgreSQL starts and the data can be read. Production LXC 109 is not touched.

1. Investigate the backup settings on the Proxmox side and where backups can be stored
2. Back up LXC 109 using the `snapshot` mode
3. Check that the archive is intact and that Proxmox recognizes it as a backup
4. Restore it to LXC 110, start it with the network cut off, and check PostgreSQL and the data
5. Delete the test LXC 110

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)

## Chapter 1: Investigating the Proxmox Side

### 1.1 Confirming Where You Run

The commands from here on are run on the Proxmox host. If they are run on the PostgreSQL server (`root@postgresql`), you get errors such as `pvesm: command not found`. First check the host name.

> **Run on: pve**

```bash
hostname
```

Confirm that `pve` is shown before continuing.

### 1.2 Backup Jobs and Storage

```bash
echo "===== POSTGRESQL VM CONFIG ====="
qm config 151 2>/dev/null

echo "===== PROXMOX BACKUP JOBS ====="
pvesh get /cluster/backup --output-format yaml 2>/dev/null

echo "===== STORAGE CONTENT TYPES ====="
pvesm status
```

Backup jobs were `--- []` (none). `qm config 151` showed nothing (151 is the last part of the IP address, not a VM number).

> **Note**: `pvesm status` always prints the LVM error `no such logical volume windows_d/windows_d`. It is a separate problem from this work and is not fixed here.

```bash
qm list
```

The VMs were 100 (TrueNAS), 101 (ollama-gpu), 102, 104, 126, 220 (security-core) and 230 (ai-defense-manager); the PostgreSQL server is not a VM. PostgreSQL runs in **LXC 109**.

### 1.3 LXC 109's Configuration

```bash
echo "===== POSTGRESQL LXC 109 CONFIG ====="
pct config 109
```

| Item | Value |
|---|---|
| Disk | `local-lvm:vm-109-disk-0`, 50G |
| Type | Unprivileged LXC (`unprivileged: 1`) |
| Additional mounts | None |
| IP address | 192.168.0.151/24 |
| Start at boot | `onboot: 1` |

### 1.4 Where Backups Can Be Stored

```bash
cat /etc/pve/storage.cfg
```

The only storage that can hold `backup` content was `local` (`/var/lib/vz`). `local-lvm`, `RAID_A`, `RAID_B` and the others are for VM and LXC disks.

```bash
echo "===== LOCAL STORAGE FILESYSTEM ====="
df -hT /var/lib/vz

echo "===== LOCAL STORAGE MOUNT ====="
findmnt -T /var/lib/vz

echo "===== EXISTING BACKUP DIRECTORY ====="
ls -lah /var/lib/vz/dump/ 2>/dev/null
```

`local` is actually the Proxmox root file system (`/dev/mapper/pve-root`, 68G free of 94G), and `/var/lib/vz/dump/` was empty.

```bash
echo "===== LXC 109 ROOTFS USAGE ====="
pct exec 109 -- df -hT /

echo "===== POSTGRESQL DATA DIRECTORY ====="
pct exec 109 -- du -sh /var/lib/postgresql/17/main

echo "===== POSTGRESQL BACKUP-RELATED FILES ====="
pct exec 109 -- du -sh /var/backups /var/lib/postgresql
```

LXC 109 used 1.7G of 49G, and PostgreSQL's data was 473M. `local` has enough space. However, `local` is on the same device as the Proxmox root, so it is no protection if that disk fails (Part 38 prepares a separate destination).

## Chapter 2: The Backup Method

### 2.1 vzdump's Documentation

> **Note**: `vzdump --help` gives `Unknown option: help`. Read the documentation with `man vzdump`.

```bash
man vzdump
```

```bash
echo "===== VZDUMP MANUAL LOCATION ====="
man -w vzdump

echo "===== VZDUMP COMMAND LOCATION ====="
command -v vzdump

echo "===== VZDUMP VERSION ====="
pveversion
```

The manual page was `/usr/share/man/man1/vzdump.1.gz` and Proxmox VE was `pve-manager/8.4.20`. Extract the main options.

```bash
zcat /usr/share/man/man1/vzdump.1.gz \
  | grep -n -E 'mode|storage|dumpdir|remove|prune|compress|bwlimit'
```

| Option | Meaning |
|---|---|
| `--mode snapshot` | Create the backup from a storage snapshot. An LXC pauses briefly while the snapshot is taken (it is not entirely without interruption) |
| `--mode suspend` / `stop` | Create it with the guest suspended / stopped |
| `--compress zstd` | Compress with zstd |
| `--storage` | Destination |

For an LXC, `snapshot` requires its disks to be on storage that supports snapshots.

### 2.2 Can local-lvm Take Snapshots?

```bash
pvesm status --storage local-lvm
```

`local-lvm` (LVM-thin) was `active`, using about 514GB of about 833GB (61.66%). LVM-thin supports snapshots.

```bash
echo "===== LVM THIN POOL STATUS ====="
lvs -a -o vg_name,lv_name,lv_attr,lv_size,data_percent,metadata_percent

echo "===== PHYSICAL VOLUME STATUS ====="
pvs
```

`pve/data` was 61.66% used for data and 2.18% for metadata, with room to spare. Note that `local` and `local-lvm` are both on the same NVMe (`/dev/nvme0n1p3`).

## Chapter 3: Backing Up LXC 109

In the original build, approval was obtained before running this. The destination is `local`, the mode `snapshot`, compression `zstd`, and old backups are not deleted (`--remove 0`). LXC 109 pauses briefly while the snapshot is taken.

> **Run on: pve**

```bash
vzdump 109 --storage local --mode snapshot --compress zstd --remove 0
```

```text
INFO: Starting Backup of VM 109 (lxc)
INFO: backup mode: snapshot
INFO: cleanup temporary 'vzdump' snapshot
  Logical volume "snap_vm-109-disk-0_vzdump" successfully removed.
INFO: Finished Backup of VM 109 (00:00:17)
INFO: Backup job finished successfully
```

It finished in 17 seconds and created `/var/lib/vz/dump/vzdump-lxc-109-2026_11_22-13_25_49.tar.zst` (about 472MB).

> **Note**: LVM-thin prints two warnings: "protection against thin pools running out of space (automatic extension) is not enabled" and "the total allocated to thin volumes exceeds the actual capacity". The backup did not fail, but this is a capacity management issue (investigated in Part 38).

## Chapter 4: Checking the Backup

### 4.1 Is the Archive Intact?

```bash
BACKUP="/var/lib/vz/dump/vzdump-lxc-109-2026_11_22-13_25_49.tar.zst"

echo "===== BACKUP FILE ====="
stat -c 'File: %n%nSize: %s bytes%nModified: %y' "$BACKUP"

echo "===== ZSTD INTEGRITY TEST ====="
zstd -t "$BACKUP"
echo "ZSTD_TEST_EXIT=$?"

echo "===== TAR ARCHIVE LIST TEST ====="
tar --zstd -tf "$BACKUP" > /tmp/lxc109-backup-filelist.txt
echo "TAR_LIST_EXIT=$?"
echo "ARCHIVE_ENTRY_COUNT=$(wc -l < /tmp/lxc109-backup-filelist.txt)"
head -n 15 /tmp/lxc109-backup-filelist.txt
```

| Item | Result |
|---|---:|
| Size | 495,442,661 bytes |
| zstd test | Succeeded (0) |
| tar listing | Succeeded (0) |
| Number of entries | 37,918 |

### 4.2 Does It Contain PostgreSQL's Data?

```bash
echo "===== PROXMOX BACKUP METADATA ====="
pvesm extractconfig /var/lib/vz/dump/vzdump-lxc-109-2026_11_22-13_25_49.tar.zst

echo "===== POSTGRESQL BACKUP CONTENTS ====="
tar --zstd -tf /var/lib/vz/dump/vzdump-lxc-109-2026_11_22-13_25_49.tar.zst \
  | grep -E '^(\./)?var/lib/postgresql/|^(\./)?etc/postgresql/' \
  | head -n 30
```

It contained `./var/lib/postgresql/17/main/base/…` and `./etc/postgresql/…`. The first `pvesm extractconfig` fails with `unable to parse volume ID`, because this command takes a Proxmox volume ID (`local:backup/<file name>`), not a file path.

### 4.3 Does Proxmox Recognize It as a Backup?

```bash
echo "===== LOCAL BACKUP VOLUME ====="
pvesm list local --content backup

echo "===== BACKUP CONFIG VIA VOLUME ID ====="
pvesm extractconfig local:backup/vzdump-lxc-109-2026_11_22-13_25_49.tar.zst
```

With the volume ID, LXC 109's configuration (host name `postgresql`, 2 cores, 4GB, 50GB, 192.168.0.151, unprivileged) could be read. Besides this backup, the list also showed backups `13_22_41` and `13_24_39`, three in total. None of them is deleted.

## Chapter 5: Restoring to LXC 110 and Testing

In the original build, approval was obtained before running this, because a new LXC is created and uses space.

### 5.1 Number and Space

```bash
echo "===== TEST CTID 110 ====="
if [ -e /etc/pve/lxc/110.conf ] || [ -e /etc/pve/qemu-server/110.conf ]; then
  echo "CTID_110=IN_USE"
else
  echo "CTID_110=FREE"
fi

echo "===== LOCAL-LVM CAPACITY ====="
pvesm status --storage local-lvm

echo "===== LOCAL BACKUP STORAGE CAPACITY ====="
df -hT /var/lib/vz

echo "===== SOURCE BACKUP ====="
stat -c '%n | %s bytes' /var/lib/vz/dump/vzdump-lxc-109-2026_11_22-13_25_49.tar.zst
```

`CTID_110=FREE`, and `local-lvm` had about 319GiB free.

### 5.2 Restoring

The backup contains the same IP address as production (192.168.0.151). To avoid a conflict, generate a new MAC address (`--unique 1`), cut the network link (`link_down=1`), assign no IP, and do not start it right after restoring (`--start 0`).

```bash
pct help restore
```

```bash
pct restore 110 local:backup/vzdump-lxc-109-2026_11_22-13_25_49.tar.zst \
  --storage local-lvm \
  --unique 1 \
  --net0 name=eth0,bridge=vmbr0,link_down=1,ip=manual,ip6=manual \
  --start 0
```

About 1.7GiB was read and LXC 110 was created.

### 5.3 Checking the Network Settings

```bash
echo "===== RESTORED CT STATUS ====="
pct status 110

echo "===== RESTORED CT CONFIG ====="
pct config 110

echo "===== PRODUCTION CT STATUS ====="
pct status 109
```

LXC 110 was stopped and had a new MAC address. However, **the IP in `net0` had reverted to the value in the backup (192.168.0.151 and the same IPv6 as production), and it had `onboot: 1`.** The `--net0` given at restore time was overwritten when it was merged with the configuration in the backup. **Do not start LXC 110 yet.** Fix only LXC 110 (production LXC 109 is not touched).

> **Caution**: The `hwaddr` below is the new MAC address shown by `pct config 110` in the original build. When you run it, use the value shown in your own environment.

```bash
pct set 110 \
  --net0 name=eth0,bridge=vmbr0,hwaddr=BC:24:11:91:B7:76,link_down=1,ip=manual,ip6=manual \
  --onboot 0
```

```bash
echo "===== TEST CT 110 CONFIG ====="
pct config 110 | grep -E '^(hostname|net0|onboot|rootfs|memory|cores):'

echo "===== TEST CT 110 STATUS ====="
pct status 110

echo "===== PRODUCTION CT 109 STATUS ====="
pct status 109
```

```text
net0: name=eth0,bridge=vmbr0,hwaddr=BC:24:11:91:B7:76,ip=manual,ip6=manual,link_down=1,type=veth
onboot: 0
===== TEST CT 110 STATUS =====
status: stopped
===== PRODUCTION CT 109 STATUS =====
status: running
```

### 5.4 Starting It and Checking PostgreSQL

```bash
pct start 110
echo "===== TEST CT STATUS ====="
pct status 110
```

It became `status: running`. The network is cut off, so its IP address does not conflict with production LXC 109.

```bash
echo "===== POSTGRESQL SERVICE STATUS ====="
pct exec 110 -- systemctl is-active postgresql@17-main

echo "===== POSTGRESQL CLUSTER STATUS ====="
pct exec 110 -- pg_lsclusters

echo "===== POSTGRESQL PROCESS ====="
pct exec 110 -- pgrep -a postgres
```

`postgresql@17-main` was `active`, cluster `17/main` (port 5432) was `online`, and the checkpointer, walwriter, autovacuum and other processes were running. **PostgreSQL 17 started with the data restored from the backup.**

### 5.5 Reading the Data

```bash
pct exec 110 -- runuser -u postgres -- psql -X -d postgres -c "
SELECT datname, pg_size_pretty(pg_database_size(datname)) AS size
FROM pg_database
WHERE datallowconn
ORDER BY datname;
"

pct exec 110 -- runuser -u postgres -- psql -X -d security_workbench -c "
SELECT
  COUNT(*) AS total_records,
  COUNT(DISTINCT event_id) AS unique_event_ids,
  MIN(event_timestamp) AS oldest_event,
  MAX(event_timestamp) AS newest_event
FROM incident.alert_events;
"
```

In LXC 110, `incident.alert_events` in `security_workbench` (26MB) had 55,867 rows (55,867 distinct IDs); the oldest event was 2026-11-17 20:14:42 and the newest 2026-11-22 04:21:28. Compare with production LXC 109 (reads only).

```bash
pct exec 109 -- runuser -u postgres -- psql -X -d security_workbench -c "
SELECT
  COUNT(*) AS total_records,
  COUNT(DISTINCT event_id) AS unique_event_ids,
  MIN(event_timestamp) AS oldest_event,
  MAX(event_timestamp) AS newest_event,
  pg_size_pretty(pg_database_size('security_workbench')) AS database_size
FROM incident.alert_events;
"
```

| Item | Restored LXC 110 | Production LXC 109 |
|---|---:|---:|
| Rows | 55,867 | 55,869 |
| Distinct IDs | 55,867 | 55,869 |
| DB size | 26MB | 26MB |
| Oldest event | Same | Same |
| Newest event | 04:21:28 | 04:52:28 |

The difference is 2 events, which entered production after the backup was taken. **We confirmed that the backup can actually be restored.**

## Chapter 6: Deleting the Test LXC

### 6.1 Stopping It

```bash
pct shutdown 110 --timeout 60
echo "===== TEST CT STATUS ====="
pct status 110
echo "===== PRODUCTION CT STATUS ====="
pct status 109
```

LXC 110 was `stopped` and production LXC 109 `running`.

### 6.2 Deleting It

The test with LXC 110 is done, so it is deleted to free its 50GB allocation (in the original build, we confirmed whether to delete or keep it, and chose to delete). Only LXC 110 is deleted; the three backups are not.

```bash
pct help destroy
```

LXC 110 is stopped, so it is deleted without `--force`, `--purge` or `--destroy-unreferenced-disks`.

```bash
pct destroy 110
```

```text
  Logical volume "vm-110-disk-0" successfully removed.
```

```bash
echo "===== TEST CT 110 ====="
pct status 110

echo "===== PRODUCTION CT 109 ====="
pct status 109

echo "===== BACKUP FILES ====="
pvesm list local --content backup
```

LXC 110 gave `Configuration file 'nodes/pve/lxc/110.conf' does not exist` (deleted), LXC 109 was `running`, and all three backups remained.

## Closing Notes

In Part 37 we backed up LXC 109 and tested that it can be restored.

| Item | Result |
|---|---|
| Backup | `vzdump-lxc-109-2026_11_22-13_25_49.tar.zst` (`local`, snapshot, zstd, 17 seconds, about 472MB) |
| Archive check | zstd and tar both succeeded, 37,918 entries |
| Recognized by Proxmox | Configuration read via the volume ID |
| Restore test | Restored to LXC 110 and started with the network cut off; PostgreSQL 17 started and 55,867 rows could be read |
| Difference from production | 2 events (entered after the backup) |
| Cleanup | LXC 110 deleted; the three backups kept |

Three issues remain.

1. The backups are on the same NVMe as production, so they are no protection if that disk fails
2. There are no scheduled backups or generation management
3. LVM-thin has no automatic extension protection

In Part 38 we investigate LVM-thin capacity and prepare TrueNAS as the backup destination.

# Part 38: Using TrueNAS as the Backup Destination
## Introduction

### About This Book

This is Part 38 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". In Part 37 we tested backing up and restoring LXC 109 (PostgreSQL), but the backups were stored (`local`) on the same NVMe as production. This part does the following.

1. Investigate, using reads only, LVM-thin (`pve/data`) capacity and its automatic extension settings
2. Make the NFS share `/mnt/backup` on **TrueNAS** (VM 100, 192.168.0.254) usable from Proxmox
3. Find out why it could not be written to (the NFS root mapping) and confirm that it can be written

TrueNAS receives one virtual disk of about 2TB each from Proxmox's `RAID_A` and `RAID_B` and mirrors them. It is empty, and we decided it could be used for backups. Without logging in to TrueNAS's screens or Shell, we check it from the Proxmox host (only the operation that changes TrueNAS's settings was done on the TrueNAS side).

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)

## Chapter 1: LVM-thin Capacity

### 1.1 The Thin Pool and Automatic Extension

> **Run on: pve**

```bash
echo "===== LVM THIN POOL ====="
lvs -a -o vg_name,lv_name,lv_attr,lv_size,data_percent,metadata_percent,seg_monitor

echo "===== PHYSICAL VOLUME ====="
pvs -o pv_name,vg_name,pv_size,pv_free

echo "===== THIN POOL AUTOEXTEND SETTINGS ====="
grep -nE 'thin_pool_autoextend_threshold|thin_pool_autoextend_percent|monitoring' /etc/lvm/lvm.conf
```

`pve/data`, where production LXC 109 lives, was 61.66% used for data and 2.18% for metadata, and VG `pve` had 16GiB free. `thin_pool_autoextend_threshold` and `thin_pool_autoextend_percent` in `lvm.conf` are still commented out.

```bash
echo "===== LVM MONITOR SERVICE ====="
systemctl is-active lvm2-monitor
systemctl status lvm2-monitor --no-pager -l

echo "===== DMEVENTD PROCESS ====="
pgrep -a dmeventd

echo "===== EFFECTIVE AUTOEXTEND SETTINGS ====="
lvmconfig --type current activation/thin_pool_autoextend_threshold
lvmconfig --type current activation/thin_pool_autoextend_percent
lvmconfig --type current activation/monitoring

echo "===== PVE DATA POOL ====="
lvs -o vg_name,lv_name,lv_size,data_percent,metadata_percent,seg_monitor pve/data
vgs -o vg_name,vg_size,vg_free pve
```

`lvm2-monitor` and `dmeventd` were running, and `pve/data` is monitored (`monitored`). However, no automatic extension values are set (`Configuration node … not found`). Being monitored and being extended automatically are different things.

### 1.2 Room to Grow

```bash
echo "===== PVE PHYSICAL DISK ====="
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL

echo "===== PVE PV DETAILS ====="
pvdisplay /dev/nvme0n1p3

echo "===== NVME PARTITION TABLE ====="
parted /dev/nvme0n1 unit GiB print free
```

The Proxmox disk is an NVMe (FIKWOT FN950 1TB), and partition 3 extends to the end of the disk. There is no free space left on the NVMe, and the VG has only 16GiB free. Enabling automatic extension would not solve a physical shortage of capacity, so **the automatic extension settings are left unchanged for now**.

```bash
echo "===== PVE DATA THIN POOL DETAILS ====="
lvs -o vg_name,lv_name,lv_size,data_percent,metadata_percent,chunksize,discards pve/data

echo "===== PVE STORAGE CONFIGURATION ====="
cat /etc/pve/storage.cfg

echo "===== PVE DATA POOL FREE SPACE ====="
vgs pve
```

`pve/data` is 794.30GiB, of which about 489.6GiB is used, leaving about 304.7GiB. It is not about to run out of space.

### 1.3 Where Backups Are Kept, and Jobs

```bash
echo "===== ROOT FILESYSTEM ====="
df -hT /

echo "===== BACKUP DIRECTORY ====="
df -hT /var/lib/vz
du -sh /var/lib/vz/dump

echo "===== PROXMOX STORAGE STATUS ====="
pvesm status
```

The root (`local`) used 24GiB of 94GiB, with 66GiB free, and `/var/lib/vz/dump` was 1.4GiB (three backups). `pvesm status` prints the following error and exits with code 5, but `local` and `local-lvm` are `active` (this error is treated as a separate problem).

```text
command '/sbin/vgscan --ignorelockingfailure --mknodes' failed: exit code 5
no such logical volume windows_d/windows_d
```

```bash
echo "===== VZDUMP CONFIGURATION ====="
cat /etc/vzdump.conf

echo "===== SCHEDULED BACKUP JOBS ====="
pvesh get /cluster/backup --output-format json-pretty
```

`/etc/vzdump.conf` was all comments, and scheduled backup jobs were `[]` (none).

## Chapter 2: Connecting to TrueNAS over NFS

### 2.1 The TrueNAS VM

```bash
echo "===== TRUENAS VM CONFIGURATION ====="
qm config 100
```

| Inside TrueNAS | On the Proxmox side | Size |
|---|---|---:|
| SCSI1 | `RAID_A` | 2,018G |
| SCSI2 | `RAID_B` | 2,018G |

> **Caution**: TrueNAS is a VM on the same Proxmox host. It protects against failure of the Proxmox NVMe, but not against failure of the whole host (it is not a backup to a separate machine).

### 2.2 Can We Reach It?

TrueNAS's IP address is 192.168.0.254.

```bash
echo "===== TRUENAS CONNECTIVITY ====="
ping -c 4 -W 2 192.168.0.254
```

All four replies came back (about 0.3–0.7 ms).

### 2.3 Choosing the Sharing Method

TrueNAS offers AFP, iSCSI, NFS, WebDAV and SMB shares; we use **NFS** as the destination for Proxmox backups.

| Method | Suitability |
|---|---|
| NFS | Suited to file sharing between Linux systems; usable directly as a Proxmox destination |
| SMB | Usable, but geared to sharing with Windows |
| iSCSI | Attaches a block device; complicated for file backups |
| WebDAV | Web-oriented; not suited as a Proxmox destination |
| AFP | Apple's old protocol; no reason to choose it for new builds |

```bash
showmount -e 192.168.0.254
```

```text
Export list for 192.168.0.254:
/mnt/backup (everyone)
```

`/mnt/backup` was shared. `(everyone)` is the scope of the share; it does not tell us whether we can write.

### 2.4 NFS Client and Server

```bash
echo "===== NFS CLIENT UTILITIES ====="
command -v mount.nfs
command -v nfsstat

echo "===== EXISTING NFS MOUNTS ====="
findmnt -t nfs,nfs4
```

`mount.nfs` and `nfsstat` were present, and there were no NFS mounts yet.

```bash
echo "===== NFS SERVER RPC SERVICES ====="
rpcinfo -p 192.168.0.254
```

TrueNAS answered with NFSv3 (TCP 2049, mountd on TCP 708). We use NFSv3.

### 2.5 Where to Mount

```bash
echo "===== TEMPORARY MOUNT POINT ====="
findmnt /mnt
ls -ld /mnt

echo "===== PROXMOX MOUNT DIRECTORY ====="
ls -ld /mnt/pve
```

```bash
echo "===== EXISTING PROXMOX MOUNTS ====="
findmnt -R /mnt/pve

echo "===== EXISTING MOUNT DIRECTORIES ====="
ls -la /mnt/pve
```

There were no mounts under `/mnt/pve`, and a directory `/mnt/pve/backup` already existed. Check its contents.

```bash
echo "===== EXISTING BACKUP MOUNTPOINT CONTENTS ====="
ls -la /mnt/pve/backup
du -sh /mnt/pve/backup
```

It was empty. We use it as the NFS mount point.

## Chapter 3: Mounting Read-Only

### 3.1 First Attempt

First mount read-only (`ro`) and check the contents.

```bash
mount -t nfs \
  -o ro,vers=3,proto=tcp \
  192.168.0.254:/mnt/backup \
  /mnt/pve/backup

echo "===== MOUNT RESULT ====="
findmnt /mnt/pve/backup

echo "===== EXPORTED BACKUP CONTENTS ====="
ls -lah /mnt/pve/backup
```

The mount failed with the following error.

```text
mount.nfs: Cannot allocate memory
```

### 3.2 Looking for the Cause

```bash
echo "===== NFS KERNEL MESSAGES ====="
dmesg -T | grep -iE 'nfs|rpc|memory|alloc' | tail -60

echo "===== MEMORY STATUS ====="
free -h

echo "===== NFS CLIENT STATUS ====="
nfsstat -c
```

About 96GiB of memory was free (about 119GiB available), and there were no NFS errors from the kernel. We also checked the NFS kernel modules (`nfs`, `nfsv3`, `sunrpc`, `lockd`), `rpc_pipefs` (mounted at `/run/rpc_pipefs`), the packages (`nfs-common` 2.6.2), slab memory, and memory pressure and OOM records; all were normal.

```bash
echo "===== ROUTE TO TRUENAS ====="
ip route get 192.168.0.254

echo "===== NFS TCP PORT ====="
nc -vz -w 3 192.168.0.254 2049

echo "===== MOUNTD TCP PORT ====="
nc -vz -w 3 192.168.0.254 708
```

Traffic to TrueNAS goes through `vmbr0` (source 192.168.0.240), and 2049 and 708 were both `open`. TrueNAS is running, so it is not restarted.

### 3.3 Trying Again

In the original build, approval was obtained before trying again. Trying with verbose output (`-v`) failed the same way with `mount(2): Cannot allocate memory`. So we try while recording system calls with `strace` (the record goes in `/tmp`).

```bash
strace -f -s 256 -o /tmp/nfs-mount-trace.log \
  mount -v -t nfs \
  -o ro,vers=3,proto=tcp,timeo=10,retrans=1 \
  192.168.0.254:/mnt/backup \
  /mnt/pve/backup

echo "===== MOUNT RESULT ====="
findmnt /mnt/pve/backup

echo "===== FAILED SYSTEM CALLS ====="
grep -E 'mount\(|ENOMEM|EFAULT|EINVAL|ENODEV|EPERM' /tmp/nfs-mount-trace.log | tail -40
```

This time **the mount succeeded**.

```text
mount("192.168.0.254:/mnt/backup", "/mnt/pve/backup",
      "nfs", MS_RDONLY, "...") = 0
```

```text
/mnt/pve/backup 192.168.0.254:/mnt/backup nfs ro,...
```

The `Cannot allocate memory` of the previous two attempts did not occur this time. Why it failed before is not known.

```bash
echo "===== NFS MOUNT STATUS ====="
findmnt -no SOURCE,FSTYPE,OPTIONS /mnt/pve/backup

echo "===== NFS DIRECTORY CONTENTS ====="
ls -lah /mnt/pve/backup

echo "===== NFS FILESYSTEM CAPACITY ====="
df -hT /mnt/pve/backup
```

It was mounted with NFSv3 over TCP; the size was 1.9T, 128K used, and it was empty.

## Chapter 4: Can We Write?

### 4.1 Remounting Read-Write

In the original build, approval was obtained before the temporary write test. Only the mount on the Proxmox side changes; TrueNAS's settings are not changed.

```bash
echo "===== REMOUNT NFS AS READ-WRITE ====="
mount -o remount,rw /mnt/pve/backup
echo "REMOUNT_EXIT=$?"

echo "===== CURRENT MOUNT OPTIONS ====="
findmnt -no SOURCE,FSTYPE,OPTIONS /mnt/pve/backup
```

`REMOUNT_EXIT=0`, and it became `rw`.

### 4.2 First Write Test

Create one test file, read it back, then delete it.

```bash
TEST_FILE="/mnt/pve/backup/.pve-nfs-write-test-20261122"

echo "===== NFS WRITE TEST ====="
if [ -e "$TEST_FILE" ]; then
  echo "TEST_ABORTED: test file already exists"
else
  printf 'Proxmox NFS write test\n' > "$TEST_FILE"
  echo "WRITE_EXIT=$?"

  echo "===== READ BACK TEST ====="
  printf 'Proxmox NFS write test\n' | cmp -s - "$TEST_FILE"
  echo "VERIFY_EXIT=$?"

  echo "===== DELETE TEST FILE ====="
  rm -f -- "$TEST_FILE"
  echo "DELETE_EXIT=$?"

  echo "===== FINAL CHECK ====="
  if [ ! -e "$TEST_FILE" ]; then
    echo "TEST_FILE_REMOVED"
  else
    echo "WARNING: TEST_FILE_REMAINS"
  fi
fi
```

`Permission denied` (`WRITE_EXIT=1`); we could not write (the file was not created).

### 4.3 Owner of the Shared Directory

```bash
echo "===== NFS SHARE DIRECTORY PERMISSIONS ====="
stat -c 'PATH=%n OWNER=%U GROUP=%G MODE=%a (%A) UID=%u GID=%g' /mnt/pve/backup

echo "===== NUMERIC OWNERSHIP ====="
ls -ldn /mnt/pve/backup

echo "===== NFS EXPORT ====="
showmount -e 192.168.0.254
```

The shared directory was `root:root` (UID 0, GID 0) and `755` (only the owner can write). Access from Proxmox's root is probably being mapped to a different user on the TrueNAS side (the NFS root mapping).

## Chapter 5: Reading TrueNAS's Settings from Proxmox

In the original build, approval was obtained to investigate and fix TrueNAS's NFS permissions. Without logging in to TrueNAS's screens or Shell, we read them through TrueNAS's API from the Proxmox host.

### 5.1 Management Entry Points

```bash
echo "===== TRUENAS MANAGEMENT PORT CHECK ====="
for port in 22 80 443; do
  nc -z -w 2 192.168.0.254 "$port"
  echo "PORT_${port}_EXIT=$?"
done

echo "===== TRUENAS API RESPONSE ====="
curl -k -sS --connect-timeout 3 -o /dev/null \
  -w 'HTTPS_API_HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/system/version
```

SSH (22) could not be reached; HTTP (80) and HTTPS (443) could. The API returned `401` (authentication required).

### 5.2 API Authentication

Enter the TrueNAS administrator's user name and password in the Proxmox terminal. The password is not displayed (`read -s`) and is never pasted into chats or elsewhere. The variables are cleared after use.

```bash
read -r -p "TrueNAS管理者ユーザー名: " TN_USER
read -r -s -p "TrueNAS管理者パスワード: " TN_PASS
echo

echo "===== TRUENAS API AUTHENTICATION ====="
HTTP_CODE=$(
  curl -k -sS --connect-timeout 5 \
    -u "$TN_USER:$TN_PASS" \
    -o /tmp/truenas-api-auth-check.json \
    -w '%{http_code}' \
    https://192.168.0.254/api/v2.0/system/version
)
echo "HTTP_STATUS=$HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
  echo "===== TRUENAS VERSION ====="
  jq . /tmp/truenas-api-auth-check.json
else
  echo "API authentication was not successful."
fi

rm -f /tmp/truenas-api-auth-check.json
unset TN_USER TN_PASS
```

`HTTP_STATUS=200`, and TrueNAS was `TrueNAS-12.0-U8.1` (TrueNAS CORE 12).

### 5.3 The API's Paths

Find the correct paths of the TrueNAS 12 API from its specification (`/api/v2.0`).

```bash
read -r -p "TrueNAS管理者ユーザー名: " TN_USER
read -r -s -p "TrueNAS管理者パスワード: " TN_PASS
echo

curl -k -sS --connect-timeout 10 \
  -u "$TN_USER:$TN_PASS" \
  -o /tmp/truenas-api-schema.json \
  -w 'HTTP_STATUS=%{http_code}\nCONTENT_TYPE=%{content_type}\n' \
  https://192.168.0.254/api/v2.0

echo "===== API SCHEMA STRUCTURE ====="
jq '{
  swagger,
  openapi,
  info,
  basePath,
  nfs_paths: ((.paths // {}) | keys | map(select(test("nfs|sharing|dataset"; "i"))))
}' /tmp/truenas-api-schema.json

rm -f /tmp/truenas-api-schema.json
unset TN_USER TN_PASS
```

An OpenAPI 3.0.0 specification was obtained; NFS shares are at `/sharing/nfs`, the NFS service at `/nfs`, and datasets at `/pool/dataset`.

### 5.4 NFS Settings, Shares and Datasets

```bash
read -r -p "TrueNAS管理者ユーザー名: " TN_USER
read -r -s -p "TrueNAS管理者パスワード: " TN_PASS
echo

echo "===== NFS SERVICE CONFIGURATION ====="
curl -k -sS --connect-timeout 10 \
  -u "$TN_USER:$TN_PASS" \
  https://192.168.0.254/api/v2.0/nfs | jq .

echo "===== NFS SHARE LIST ====="
curl -k -sS --connect-timeout 10 \
  -u "$TN_USER:$TN_PASS" \
  https://192.168.0.254/api/v2.0/sharing/nfs | jq .

echo "===== DATASET LIST ====="
curl -k -sS --connect-timeout 10 \
  -u "$TN_USER:$TN_PASS" \
  https://192.168.0.254/api/v2.0/pool/dataset \
  | jq '[.[] | {
      id,
      name,
      mountpoint,
      aclmode,
      acltype,
      readonly
    }]'

unset TN_USER TN_PASS
```

| Item | Value |
|---|---|
| NFS share (id 1) | `/mnt/backup` |
| `maproot_user` / `maproot_group` | `itanaka` / `itanaka` (UID/GID 1000) |
| Dataset | `backup` (NFSv4 ACL, `readonly=OFF`) |

**This is the cause.** Access from Proxmox's root is treated as `itanaka` on TrueNAS. The shared directory is `root:root`, `755`, so `itanaka` cannot write.

> **Note**: In the original build we also tried keeping the owner as `root:root` and adding a write ACL for `itanaka` (UID 1000). However, TrueNAS CORE 12 does not allow changing the ACL of the top-level dataset of a pool (`/mnt/backup`) (`root level dataset is not permitted`), and the ACL was not changed.

## Chapter 6: Allowing Writes as root

### 6.1 Changing the NFS Share Settings

On the TrueNAS side, we changed the root mapping (Maproot) of the NFS share `/mnt/backup`. The shared directory's owner remains `root:root`. Read the settings after the change from Proxmox through the API.

In this step, so that the password does not appear in `curl`'s command arguments, it is put in a temporary file with `chmod 600` and passed with `--config`; the file is deleted at the end.

> **Run on: pve**

```bash
read -r -p "TrueNAS管理者ユーザー名: " TN_USER
read -r -s -p "TrueNAS管理者パスワード: " TN_PASS
echo

AUTH_CFG=$(mktemp)
chmod 600 "$AUTH_CFG"
printf 'user = "%s:%s"\n' "$TN_USER" "$TN_PASS" > "$AUTH_CFG"
unset TN_PASS

echo "===== EXISTING NFS SHARE ====="
curl -k -sS --connect-timeout 10 \
  --config "$AUTH_CFG" \
  https://192.168.0.254/api/v2.0/sharing/nfs \
  | jq '[.[] | {
      id, paths, enabled, ro, alldirs,
      networks, hosts,
      maproot_user, maproot_group,
      mapall_user, mapall_group
    }]'

echo "===== PARENT DATASET PROPERTIES ====="
curl -k -sS --connect-timeout 10 \
  --config "$AUTH_CFG" \
  https://192.168.0.254/api/v2.0/pool/dataset/id/backup \
  | jq '{
      id, mountpoint, type, acltype, aclmode,
      compression, sync, readonly, casesensitivity
    }'

rm -f "$AUTH_CFG"
unset TN_USER AUTH_CFG
```

```text
"paths": ["/mnt/backup"],
"enabled": true,
"ro": false,
"alldirs": true,
"maproot_user": "root",
"maproot_group": "builtin_administrators",
```

Proxmox's root is now treated as `root` on TrueNAS too (group `builtin_administrators`).

### 6.2 Write Test

```bash
TEST_FILE="/mnt/pve/backup/.pve-root-write-test-20261122"

echo "===== NFS WRITE TEST ====="
if [ -e "$TEST_FILE" ]; then
  echo "TEST_ABORTED: test file already exists"
else
  printf 'Proxmox root NFS write test\n' > "$TEST_FILE"
  WRITE_RC=$?
  echo "WRITE_EXIT=$WRITE_RC"

  if [ "$WRITE_RC" -eq 0 ]; then
    echo "===== READ BACK TEST ====="
    cat "$TEST_FILE"

    echo "===== FILE OWNERSHIP ====="
    stat -c 'owner=%U:%G uid=%u gid=%g mode=%a' "$TEST_FILE"

    echo "===== CLEANUP ====="
    rm -f "$TEST_FILE"
    echo "REMOVE_EXIT=$?"
    if [ ! -e "$TEST_FILE" ]; then
      echo "CLEANUP_VERIFIED"
    else
      echo "CLEANUP_FAILED"
    fi
  fi
fi
```

```text
===== NFS WRITE TEST =====
WRITE_EXIT=0
===== READ BACK TEST =====
Proxmox root NFS write test
===== FILE OWNERSHIP =====
owner=root:root uid=0 gid=0 mode=644
===== CLEANUP =====
REMOVE_EXIT=0
CLEANUP_VERIFIED
```

**Proxmox's root could write to TrueNAS's `/mnt/backup`.** There is no need to create a child dataset or change ACLs.

## Closing Notes

In Part 38 we prepared TrueNAS as the backup destination.

| Item | Result |
|---|---|
| LVM-thin | `pve/data` 61.66%. Automatic extension not set, but deferred because the VG has only 16GiB free |
| Scheduled backups | None (`vzdump.conf` also at defaults) |
| Destination | TrueNAS (VM 100, 192.168.0.254) NFS `/mnt/backup` (1.9T, empty) |
| Mount | NFSv3 over TCP at `/mnt/pve/backup`. The first two attempts gave `Cannot allocate memory` (cause unknown); the third succeeded |
| Why writes failed | The NFS root mapping was `itanaka`, and the shared directory was `root:root`, `755` |
| What was changed | The NFS share's Maproot on TrueNAS set to `root` / `builtin_administrators` |
| Write test | Succeeded (created as `root:root` and deleted) |

However, the current mount was made by hand and is not yet registered as Proxmox storage. In Part 39 we make sure NFS is mounted correctly at boot, register it with Proxmox as backup-only storage, and prepare scheduled backups.

# Part 39: Registering the Destination and Preparing Scheduled Backups
## Introduction

### About This Book

This is Part 39 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". In Part 38 we mounted TrueNAS's NFS share `/mnt/backup` at `/mnt/pve/backup` and confirmed that Proxmox's root can write to it. This part does the following.

1. Make sure NFS is also mounted correctly at boot (fix the systemd mount unit, which still had old settings)
2. Register it with Proxmox as backup-only storage, `truenas-backup`
3. Investigate the VMs and LXCs to back up and their capacity, and decide the method, generations and times for PostgreSQL backups
4. Register a scheduled backup job for LXC 109 **while leaving it disabled**
5. Place a script for logical backups of PostgreSQL

The decisions are as follows.

| Item | Decision |
|---|---|
| Generations | 7 daily, 4 weekly, 3 monthly |
| PostgreSQL logical backup | Daily at 02:00 (Japan time) |
| Proxmox backup of LXC 109 | Daily at 03:00 (Japan time) |

This part goes as far as testing, after placing the script, whether hard links (used for the weekly and monthly generations) can be created on NFS. The first backup run and enabling the job and timer are done in Parts 40 and 41.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)

## Chapter 1: Fixing the Mount Unit

### 1.1 The Current Settings

> **Run on: pve**

```bash
echo "===== PROXMOX STORAGE CONFIGURATION ====="
cat /etc/pve/storage.cfg

echo "===== STORAGE STATUS ====="
pvesm status

echo "===== BACKUP DIRECTORY ====="
findmnt -T /mnt/pve/backup
df -hT /mnt/pve/backup

echo "===== VZDUMP CONFIGURATION ====="
if [ -f /etc/vzdump.conf ]; then
  cat /etc/vzdump.conf
else
  echo "No /etc/vzdump.conf"
fi
```

`/mnt/pve/backup` was mounted over NFS, but it was not yet registered as Proxmox storage. Find out where this mount is managed.

```bash
echo "===== FSTAB NFS ENTRIES ====="
grep -nE 'nfs|/mnt/pve/backup' /etc/fstab || true

echo "===== SYSTEMD MOUNT STATUS ====="
systemctl status mnt-pve-backup.mount --no-pager

echo "===== MOUNT UNIT FILE ====="
systemctl cat mnt-pve-backup.mount

echo "===== PROXMOX NFS STORAGE REFERENCES ====="
grep -RniE '192\.168\.0\.254|/mnt/backup|/mnt/pve/backup' \
  /etc/pve/storage.cfg /etc/fstab /etc/systemd/system 2>/dev/null
```

`/etc/fstab` had nothing, but `/etc/systemd/system/mnt-pve-backup.mount` (`Description=Mount storage 'backup' under /mnt/pve`) existed. **This unit file pointed not to NFS but to a local ext4 disk (UUID `8cab893f-75f0-478d-842b-e94558853d14`).**

### 1.2 Checking the Mismatch

```bash
echo "===== KERNEL MOUNT TABLE ====="
grep -E ' /mnt/pve/backup ' /proc/mounts

echo "===== FINDMNT DETAILS ====="
findmnt -T /mnt/pve/backup -o TARGET,SOURCE,FSTYPE,OPTIONS

echo "===== SYSTEMD MOUNT PROPERTIES ====="
systemctl show mnt-pve-backup.mount \
  -p ActiveState -p SubState -p What -p Where -p Type -p FragmentPath

echo "===== UUID DEVICE CHECK ====="
blkid -U 8cab893f-75f0-478d-842b-e94558853d14

echo "===== BLOCK DEVICE DETAILS ====="
lsblk -o NAME,TYPE,FSTYPE,UUID,SIZE,MOUNTPOINTS
```

The actual mount was `192.168.0.254:/mnt/backup` (NFS), and the settings systemd currently held were also NFS. No disk with that UUID exists.

```bash
echo "===== SYSTEMD UNIT SOURCE ====="
systemctl show mnt-pve-backup.mount \
  -p FragmentPath -p SourcePath -p DropInPaths \
  -p What -p Where -p Type -p NeedDaemonReload

echo "===== UNIT FILE AND LINKS ====="
ls -l /etc/systemd/system/mnt-pve-backup.mount
ls -l /etc/systemd/system/multi-user.target.wants/mnt-pve-backup.mount

echo "===== UNIT FILE CONTENT WITH LINE NUMBERS ====="
nl -ba /etc/systemd/system/mnt-pve-backup.mount

echo "===== SYSTEMD UNIT OVERRIDES ====="
find /etc/systemd/system/mnt-pve-backup.mount.d \
  -maxdepth 2 -type f -print 2>/dev/null

echo "===== MOUNT UNIT REFERENCES ====="
grep -RniE 'mnt-pve-backup|192\.168\.0\.254:/mnt/backup' \
  /etc/systemd /run/systemd/generator /run/systemd/transient \
  /etc/pve 2>/dev/null
```

The file had not changed since May 24 and still had `Type=ext4` and `What=/dev/disk/by-uuid/8cab893f-…`. There were no overriding settings (drop-ins) either.

```bash
echo "===== SYSTEMD UNIT STATUS ====="
systemctl status mnt-pve-backup.mount --no-pager -l

echo "===== SYSTEMD UNIT TIMESTAMPS ====="
systemctl show mnt-pve-backup.mount \
  -p FragmentPath -p ActiveState -p SubState \
  -p ActiveEnterTimestamp -p StateChangeTimestamp \
  -p InactiveEnterTimestamp -p NeedDaemonReload \
  -p What -p Where -p Type

echo "===== MOUNT UNIT JOURNAL ====="
journalctl -b -u mnt-pve-backup.mount --no-pager -o short-iso

echo "===== ACTUAL KERNEL MOUNT ====="
findmnt -T /mnt/pve/backup -o TARGET,SOURCE,FSTYPE,OPTIONS

echo "===== PID 1 MOUNT TABLE ====="
grep ' /mnt/pve/backup ' /proc/1/mountinfo
```

The current NFS mount works correctly (systemd remembers the NFS mounted by hand). However, **if the host is rebooted as it is, the file's ext4 settings will be loaded.** Make the file match the NFS settings.

> **Caution**: Here we do not run `daemon-reload`, unmount, or reboot.

### 1.3 Making the Unit File NFS

Back up the current file, rewrite it, and check it with `systemd-analyze verify`.

```bash
BACKUP="/root/mnt-pve-backup.mount.before-nfs-20261122"

echo "===== BACKUP EXISTENCE CHECK ====="
if [ -e "$BACKUP" ]; then
  echo "ERROR: backup file already exists: $BACKUP"
else
  cp -a /etc/systemd/system/mnt-pve-backup.mount "$BACKUP"
  echo "BACKUP_CREATED=$?"
fi

echo "===== WRITE NFS MOUNT UNIT ====="
if [ -f "$BACKUP" ]; then
  cat > /etc/systemd/system/mnt-pve-backup.mount <<'EOF'
[Unit]
Description=Mount TrueNAS NFS backup storage
Wants=network-online.target
After=network-online.target

[Mount]
What=192.168.0.254:/mnt/backup
Where=/mnt/pve/backup
Type=nfs
Options=defaults,_netdev,vers=3

[Install]
WantedBy=multi-user.target
EOF
  echo "WRITE_EXIT=$?"
else
  echo "WRITE_SKIPPED: backup was not created"
fi

echo "===== VERIFY UNIT SYNTAX ====="
systemd-analyze verify /etc/systemd/system/mnt-pve-backup.mount
echo "VERIFY_EXIT=$?"

echo "===== CURRENT UNIT FILE ====="
cat /etc/systemd/system/mnt-pve-backup.mount
```

The backup (`/root/mnt-pve-backup.mount.before-nfs-20261122`) was created, and the rewritten file gave `VERIFY_EXIT=0`.

### 1.4 Making systemd Load It

The current NFS mount is left running; it is not remounted or unmounted.

```bash
echo "===== RELOAD SYSTEMD CONFIGURATION ====="
systemctl daemon-reload
echo "DAEMON_RELOAD_EXIT=$?"

echo "===== LOADED UNIT CONFIGURATION ====="
systemctl show mnt-pve-backup.mount \
  -p What -p Where -p Type -p ActiveState -p SubState \
  -p NeedDaemonReload -p FragmentPath

echo "===== MOUNT STATUS ====="
findmnt -T /mnt/pve/backup -o TARGET,SOURCE,FSTYPE,OPTIONS

echo "===== ENABLED AT BOOT ====="
systemctl is-enabled mnt-pve-backup.mount
```

```text
DAEMON_RELOAD_EXIT=0
Where=/mnt/pve/backup
What=192.168.0.254:/mnt/backup
Type=nfs
ActiveState=active
SubState=mounted
NeedDaemonReload=no
===== ENABLED AT BOOT =====
enabled
```

The file and the running settings now match, and NFS will be mounted at boot as well.

## Chapter 2: Registering as Proxmox Storage

### 2.1 Is the Name Free?

The storage ID will be `truenas-backup`.

```bash
echo "===== EXISTING STORAGE CONFIGURATION ====="
cat /etc/pve/storage.cfg

echo "===== STORAGE ID COLLISION CHECK ====="
if grep -qE '^[[:space:]]*(dir|nfs|pbs|cifs):[[:space:]]+truenas-backup([[:space:]]|$)' /etc/pve/storage.cfg; then
  echo "COLLISION: truenas-backup already exists"
else
  echo "NO_COLLISION"
fi

echo "===== CURRENT STORAGE STATUS ====="
pvesm status
```

`NO_COLLISION`.

### 2.2 Registering

Register it as "directory" storage using the existing NFS mount, so that Proxmox does not mount it a second time. The content is `backup` only (not used for VM disks and the like), and `--is_mountpoint 1` is added. This prevents backups from being written to the empty local directory when NFS is not mounted. Just before registering, check the mount's source and type, and register only if they match.

```bash
echo "===== PRE-REGISTRATION SAFETY CHECK ====="
SOURCE="$(findmnt -n -o SOURCE -T /mnt/pve/backup)"
FSTYPE="$(findmnt -n -o FSTYPE -T /mnt/pve/backup)"

echo "SOURCE=$SOURCE"
echo "FSTYPE=$FSTYPE"

if [ "$SOURCE" = "192.168.0.254:/mnt/backup" ] && \
   [ "$FSTYPE" = "nfs" ] && \
   mountpoint -q /mnt/pve/backup; then

  echo "===== ADD PROXMOX DIRECTORY STORAGE ====="
  pvesm add dir truenas-backup \
    --path /mnt/pve/backup \
    --content backup \
    --is_mountpoint 1 \
    --nodes pve

  echo "===== ADD COMMAND EXIT CODE ====="
  echo "$?"

else
  echo "REGISTRATION_ABORTED: NFS mount verification failed"
fi
```

`SOURCE=192.168.0.254:/mnt/backup`, `FSTYPE=nfs`, and the exit code was `0`.

```bash
echo "===== REGISTERED STORAGE CONFIGURATION ====="
grep -A6 -B1 -n 'truenas-backup' /etc/pve/storage.cfg

echo "===== STORAGE STATUS ====="
pvesm status --storage truenas-backup

echo "===== BACKUP CONTENT LIST ====="
pvesm list truenas-backup

echo "===== MOUNTPOINT VERIFICATION ====="
findmnt -T /mnt/pve/backup -o TARGET,SOURCE,FSTYPE,OPTIONS

echo "===== BACKUP DIRECTORY CONTENTS ====="
ls -lah /mnt/pve/backup
```

```text
dir: truenas-backup
     path /mnt/pve/backup
     content backup
     is_mountpoint 1
     nodes pve
```

`truenas-backup` was `active` with about 1.89TiB free, and the list of backups was still empty. `/mnt/pve/backup/dump` was also created.

## Chapter 3: Investigating What to Back Up

### 3.1 VMs and LXCs

```bash
echo "===== VM INVENTORY ====="
qm list

echo "===== LXC INVENTORY (ID BELOW 400) ====="
pct list | awk 'NR == 1 || $1 < 400'

echo "===== VZDUMP CURRENT CONFIGURATION ====="
if [ -f /etc/vzdump.conf ]; then
  cat /etc/vzdump.conf
else
  echo "No /etc/vzdump.conf"
fi

echo "===== BACKUP STORAGE STATUS ====="
pvesm status --storage truenas-backup
```

> **Caution**: **VM 100 (TrueNAS) is the very server that provides this NFS destination.** Writing its own backup to its own NFS would make it impossible to restore if it broke (a circular dependency), so it is not a target for backups to `truenas-backup`. How to protect TrueNAS itself is considered separately.

### 3.2 Disk Configuration

```bash
echo "===== VM DISK CONFIGURATIONS ====="
for id in 101 102 104 126 220 230; do
  echo
  echo "--- VM $id ---"
  qm config "$id" | grep -E '^(name|boot|bios|machine|scsi[0-9]+|sata[0-9]+|virtio[0-9]+|ide[0-9]+|efidisk[0-9]+|tpmstate[0-9]+|unused[0-9]+):'
done

echo
echo "===== LXC ROOTFS AND MOUNT CONFIGURATIONS ====="
for id in 103 105 107 108 109 111 113 114 115 118 119 120 121 123 129 134 140 141 147 199 200 201 204 205 206 208 209 350; do
  echo
  echo "--- LXC $id ---"
  pct config "$id" | grep -E '^(hostname|rootfs|mp[0-9]+|unused[0-9]+|unprivileged|features):'
done

echo
echo "===== NFS BACKUP STORAGE CONTENT ====="
pvesm list truenas-backup
```

```bash
echo "===== VM 101 BACKUP SETTINGS ====="
qm config 101

echo "===== VM 220 BACKUP SETTINGS ====="
qm config 220

echo "===== VM 230 BACKUP SETTINGS ====="
qm config 230

echo "===== POSTGRESQL LXC 109 ====="
pct config 109

echo "===== NVIDIA LXC 208 ====="
pct config 208

echo "===== OLLAMA LXC 209 ====="
pct config 209

echo "===== NVIDIA HOST DIRECTORY ====="
ls -ld /opt/nvidia-lxc-570
du -sh /opt/nvidia-lxc-570 2>/dev/null
```

| Target | Points to note |
|---|---|
| VM 220 security-core, VM 230 ai-defense-manager | The core of this system; high priority to protect |
| LXC 109 postgresql | No additional mounts, 50GB. Needs a logical DB backup in addition to the container backup |
| VM 101 | Its GPU is passed through over PCI; when restoring, the GPU assignment and the host's drivers must be checked again |
| VM 220 | Uses two networks: `vmbr0` and the internal `vmbr1` |
| LXC 208, 209 | Mount the host's `/opt/nvidia-lxc-570` (about 72MB) via `mp8`. This is not included in LXC backups, so protect it separately |

### 3.3 Space Actually Used

```bash
echo "===== QEMU GUEST AGENT STATUS ====="
for id in 101 220 230; do
  echo
  echo "--- VM $id ---"
  if qm agent "$id" ping 2>/dev/null; then
    echo "--- FILESYSTEM USAGE ---"
    qm agent "$id" get-fsinfo
  else
    echo "GUEST_AGENT_UNAVAILABLE"
  fi
done

echo
echo "===== RUNNING LXC ROOT FILESYSTEM USAGE ====="
for id in 103 105 109 111 129 134 200 350; do
  echo
  echo "--- LXC $id ---"
  pct exec "$id" -- df -hP /
done

echo
echo "===== NVIDIA HOST DIRECTORY MOUNT ====="
findmnt -T /opt/nvidia-lxc-570 -o TARGET,SOURCE,FSTYPE,OPTIONS

echo
echo "===== VZDUMP AVAILABLE OPTIONS ====="
vzdump --help
```

(The final `vzdump --help` gives `Unknown option: help`. Read the documentation with `man vzdump`.)

| Target | Used |
|---|---:|
| VM 220 security-core | About 26.1GiB |
| LXC 103 Prometheus | 1.9GB |
| LXC 105 Grafana | 2.4GB |
| LXC 109 PostgreSQL | 1.7GB |
| LXC 111 Wiki | 2.1GB |
| LXC 129 Open WebUI | 16GB |
| LXC 134 Qdrant | 1.2GB |
| LXC 200 Novel | 39GB |
| LXC 350 easywrider | 59GB |

The measurable ones alone come to about 150GB (before compression). VMs 101 and 230 did not answer the QEMU Guest Agent and could not be measured.

## Chapter 4: The PostgreSQL Backup Method

### 4.1 PostgreSQL's State

```bash
echo "===== POSTGRESQL SERVICE STATUS ====="
pct exec 109 -- pg_isready

echo
echo "===== POSTGRESQL VERSION AND DATABASE SIZES ====="
pct exec 109 -- runuser -u postgres -- psql -X -v ON_ERROR_STOP=1 -At -F '|' -c "
SELECT version();
SELECT datname, pg_size_pretty(pg_database_size(datname))
FROM pg_database
WHERE datallowconn
ORDER BY pg_database_size(datname) DESC;
"

echo
echo "===== POSTGRESQL WAL CONFIGURATION ====="
pct exec 109 -- runuser -u postgres -- psql -X -v ON_ERROR_STOP=1 -At -F '|' -c "
SHOW archive_mode;
SHOW wal_level;
SHOW max_wal_size;
SHOW data_directory;
"

echo
echo "===== POSTGRESQL WAL DIRECTORY SIZE ====="
pct exec 109 -- runuser -u postgres -- psql -X -v ON_ERROR_STOP=1 -At -c "
SELECT pg_size_pretty(COALESCE(SUM(size), 0))
FROM pg_ls_waldir();
"
```

PostgreSQL was 17.11; the largest DB was `agent_memory` (about 205MB), followed by `novel` (about 78MB). `archive_mode` was `off`, and WAL was about 32MB.

### 4.2 Roles, Tablespaces and Extensions

Password information is not shown.

```bash
echo "===== BACKUP TOOL VERSIONS ====="
pct exec 109 -- pg_dump --version
pct exec 109 -- pg_dumpall --version

echo
echo "===== POSTGRESQL ROLES (NO PASSWORD DATA) ====="
pct exec 109 -- runuser -u postgres -- psql -X -d postgres -P pager=off -c "
SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolcanlogin
FROM pg_roles
ORDER BY rolname;
"

echo
echo "===== TABLESPACES ====="
pct exec 109 -- runuser -u postgres -- psql -X -d postgres -P pager=off -c "
SELECT spcname, pg_tablespace_location(oid) AS location
FROM pg_tablespace
ORDER BY spcname;
"

echo
echo "===== INSTALLED EXTENSIONS PER DATABASE ====="
pct exec 109 -- bash -lc '
runuser -u postgres -- psql -X -d postgres -Atc "
SELECT datname
FROM pg_database
WHERE datallowconn = true AND NOT datistemplate
ORDER BY datname;
" | while IFS= read -r db; do
  echo "--- DATABASE: $db ---"
  runuser -u postgres -- psql -X -d "$db" -Atc "
  SELECT extname || '\'' | version='\'' || extversion
  FROM pg_extension
  ORDER BY extname;
  "
done
'
```

| Item | Result |
|---|---|
| `pg_dump` / `pg_dumpall` | 17.11, same as the server |
| Roles | 33 (`wazuh_collector` is an ordinary login role) |
| Tablespaces | Only `pg_default` and `pg_global` |
| Extensions | `plpgsql` and `vector` 0.8.7 (used in `easywrider`, `postgres` and `vector_db`) |

### 4.3 Data Volume and NFS Capacity

```bash
echo "===== POSTGRESQL DATA DIRECTORY ====="
pct exec 109 -- du -sh /var/lib/postgresql/17/main
pct exec 109 -- du -sh /var/lib/postgresql/17/main/base
pct exec 109 -- du -sh /var/lib/postgresql/17/main/pg_wal

echo
echo "===== PGVECTOR PACKAGE ====="
pct exec 109 -- dpkg-query -W -f='${Package} ${Version}\n' postgresql-17-pgvector 2>/dev/null
pct exec 109 -- ls -l /usr/share/postgresql/17/extension/vector.control

echo
echo "===== NFS BACKUP CAPACITY ====="
findmnt /mnt/pve/backup
df -hP /mnt/pve/backup
pvesm status --storage truenas-backup
```

The data was 475MB (`base` 442MB, WAL 33MB), and pgvector 0.8.7 was installed. The NFS has about 1.9TB free.

### 4.4 LXC 109 Snapshots

```bash
echo "===== LXC 109 CONFIGURATION ====="
pct config 109

echo
echo "===== LOCAL-LVM STORAGE CONFIGURATION ====="
grep -A8 -B1 '^lvmthin: local-lvm' /etc/pve/storage.cfg

echo
echo "===== LOCAL-LVM STATUS ====="
pvesm status --storage local-lvm

echo
echo "===== BACKUP STORAGE CONFIGURATION ====="
grep -A8 -B1 '^dir: truenas-backup' /etc/pve/storage.cfg

echo
echo "===== BACKUP DIRECTORY ====="
ls -ld /mnt/pve/backup /mnt/pve/backup/dump
```

```bash
echo "===== LVM-THIN POOL CAPACITY ====="
lvs -a -o vg_name,lv_name,lv_attr,lv_size,data_percent,metadata_percent

echo
echo "===== LXC 109 ROOTFS VOLUME ====="
lvs -o vg_name,lv_name,lv_attr,lv_size,data_percent,metadata_percent pve/vm-109-disk-0

echo
echo "===== SNAPSHOT CAPABILITY ====="
pvesm status --storage local-lvm
```

LXC 109 is an unprivileged Debian 13 LXC, and its only disk is `pve/vm-109-disk-0` on `local-lvm` (LVM-thin). `local-lvm` is at 61.66% with metadata at 2.18%, enough room for snapshots.

### 4.5 Deciding the Method

| Target | Method | Purpose |
|---|---|---|
| All PostgreSQL DBs | `pg_dump` custom format (`-Fc`), one per DB | Restore per DB |
| PostgreSQL roles and the like | `pg_dumpall --globals-only` | Restore roles and permissions |
| LXC 109 | Proxmox `vzdump` snapshot | Restore the OS, PostgreSQL itself and settings |
| pgvector | Record the package and extension versions | Prepare the extension at the restore destination |

> **Caution**: The output of `pg_dumpall --globals-only` may include role password hashes. Saved files are made readable and writable by root only.

The generations kept are **7 daily, 4 weekly and 3 monthly** (decided after confirmation in the original build).

## Chapter 5: Deciding the Schedule

### 5.1 Current Jobs

```bash
echo "===== PROXMOX BACKUP JOBS ====="
if [ -f /etc/pve/jobs.cfg ]; then
  cat /etc/pve/jobs.cfg
else
  echo "NO jobs.cfg"
fi

echo
echo "===== VZDUMP CRON ENTRIES ====="
grep -RniE 'vzdump|pg_dump|pg_dumpall' \
  /etc/cron.d /etc/cron.daily /etc/cron.weekly /etc/cron.monthly \
  /var/spool/cron/crontabs 2>/dev/null

echo
echo "===== BACKUP-RELATED SYSTEMD TIMERS ====="
systemctl list-timers --all --no-pager | grep -Ei 'backup|vzdump|postgres|dump'
```

There were no Proxmox backup jobs, no cron for PostgreSQL, and no backup timers (`/etc/cron.d/vzdump` is the standard file and contains only comments).

The times were decided as follows (Japan time).

| Time | Task |
|---|---|
| Daily 02:00 | PostgreSQL logical backup |
| Daily 03:00 | LXC 109 snapshot backup |
| Every Sunday | That day's backup becomes the weekly generation |
| 1st of every month | That day's backup becomes the monthly generation |

### 5.2 Proxmox's Version and Backup Job Features

```bash
echo "===== PROXMOX VERSION ====="
pveversion -v

echo
echo "===== VZDUMP COMMAND OPTIONS ====="
vzdump 109 --help 2>&1

echo
echo "===== PROXMOX BACKUP API ====="
pvesh get /cluster/backup --output-format json 2>&1

echo
echo "===== SYSTEMD VERSION ====="
systemctl --version | head -1
```

Proxmox VE was 8.4.20, systemd 252, and backup jobs were `[]`.

```bash
echo "===== VZDUMP MANUAL ====="
if man -w vzdump >/dev/null 2>&1; then
  man -P cat vzdump | col -b | grep -n -A8 -B3 -E 'snapshot|prune-backups|keep-daily|keep-weekly|keep-monthly|storage|mode'
else
  echo "vzdump manual not found"
fi

echo
echo "===== BACKUP JOB API PARAMETERS ====="
pvesh usage /cluster/backup --verbose 2>&1

echo
echo "===== BACKUP JOB API SCHEMA ====="
pvesh get /cluster/backup --output-format json-pretty
```

Generations can be kept with Proxmox's standard feature (`--prune-backups 'keep-daily=7,keep-weekly=4,keep-monthly=3'`). When the daily, weekly and monthly periods overlap, the number actually kept may be less than 14.

### 5.3 Checking the Time

```bash
echo "===== HOST TIMEZONE ====="
timedatectl show -p Timezone -p LocalRTC -p NTPSynchronized

echo
echo "===== DAILY 03:00 SCHEDULE VALIDATION ====="
systemd-analyze calendar '*-*-* 03:00:00'
```

The Proxmox host was `Timezone=Asia/Tokyo` and synchronized with NTP, and `*-*-* 03:00:00` was interpreted as 03:00 every day (Japan time).

## Chapter 6: Registering the LXC 109 Job While Disabled

Because it is registered disabled (`--enabled 0`), this operation performs no backup and the schedule does not run.

> **Run on: pve**

```bash
pvesh create /cluster/backup \
  --id lxc109-daily \
  --node pve \
  --vmid 109 \
  --storage truenas-backup \
  --mode snapshot \
  --compress zstd \
  --prune-backups 'keep-daily=7,keep-weekly=4,keep-monthly=3' \
  --schedule '*-*-* 03:00:00' \
  --enabled 0 \
  --repeat-missed 0 \
  --comment 'LXC 109 daily snapshot backup to TrueNAS'
```

It finishes without output. Check what was registered.

```bash
echo "===== REGISTERED BACKUP JOB ====="
pvesh get /cluster/backup --output-format json-pretty

echo
echo "===== BACKUP JOB CONFIGURATION ====="
cat /etc/pve/jobs.cfg
```

| Item | Value |
|---|---|
| Target | LXC 109 only |
| Destination | `truenas-backup` |
| Time | Daily 03:00 |
| Mode, compression | snapshot, zstd |
| Generations | `keep-daily=7,keep-monthly=3,keep-weekly=4` |
| Making up missed runs | No (`repeat-missed 0`) |
| Enabled | `enabled 0` (disabled) |

The API response and `/etc/pve/jobs.cfg` matched.

## Chapter 7: The PostgreSQL Logical Backup Script

### 7.1 Destination and Tools

```bash
echo "===== BACKUP STORAGE DIRECTORY ====="
find /mnt/pve/backup -maxdepth 2 -printf '%M %u:%g %p\n' | sort

echo
echo "===== STORAGE MOUNT ====="
findmnt /mnt/pve/backup

echo
echo "===== STORAGE CAPACITY ====="
df -h /mnt/pve/backup
```

Only `/mnt/pve/backup` and `/mnt/pve/backup/dump` existed (both `root:root`).

```bash
echo "===== LXC 109 STATUS ====="
pct status 109

echo
echo "===== POSTGRESQL VERSION AND TIMEZONE ====="
pct exec 109 -- bash -lc '
  pg_dump --version
  pg_dumpall --version
  date "+%Y-%m-%d %H:%M:%S %Z %z"
  timedatectl show -p Timezone 2>/dev/null
'

echo
echo "===== DATABASE LIST ====="
pct exec 109 -- runuser -u postgres -- psql -X -At -d postgres -c "
SELECT datname
FROM pg_database
WHERE datallowconn
  AND NOT datistemplate
ORDER BY datname;
"

echo
echo "===== POSTGRESQL BACKUP TOOL AVAILABILITY ====="
pct exec 109 -- bash -lc '
  command -v pg_dump
  command -v pg_dumpall
  command -v psql
  command -v runuser
'
```

LXC 109 is running, and `pg_dump`, `pg_dumpall`, `psql` and `runuser` are available. Both LXC 109 and the Proxmox host are `Asia/Tokyo`. There were 17 DBs excluding templates (`agent_db`, `agent_memory`, `aiagent`, `aipmo`, `cerebrum`, `easywrider`, `movie`, `nfaipmo`, `novel`, `orchivio`, `postgres`, `security_workbench`, `tester`, `vector_db`, `winfilemgr`, `writer`, `writers`).

```bash
echo "===== DATABASE SIZES ====="
pct exec 109 -- runuser -u postgres -- psql -X -P pager=off -d postgres -c "
SELECT
  datname AS database,
  pg_size_pretty(pg_database_size(datname)) AS size
FROM pg_database
WHERE datallowconn
  AND NOT datistemplate
ORDER BY pg_database_size(datname) DESC;
"

echo
echo "===== INSTALLED EXTENSIONS ====="
pct exec 109 -- bash -lc '
for db in $(runuser -u postgres -- psql -X -At -d postgres -c "
  SELECT datname
  FROM pg_database
  WHERE datallowconn AND NOT datistemplate
  ORDER BY datname
"); do
  echo "--- $db ---"
  runuser -u postgres -- psql -X -At -d "$db" -c "
    SELECT extname || E'\'' '\''
           || extversion
    FROM pg_extension
    ORDER BY extname;
  "
done
'

echo
echo "===== PGVECTOR PACKAGE ====="
pct exec 109 -- dpkg-query -W -f='${Package} ${Version}\n' postgresql-17-pgvector
```

The 17 DBs totaled about 450MB; the three that use the `vector` extension are `easywrider`, `postgres` and `vector_db`, and the package was `postgresql-17-pgvector 0.8.7-1.pgdg13+1`.

### 7.2 What Is Saved

| File | Contents |
|---|---|
| `globals.sql` | Roles and the like (contains password hashes, so readable by root only) |
| `<DB name>.dump` | Custom-format dump per DB (17) |
| `database-list.txt`, `postgresql-version.txt`, `extensions.tsv` | DB list, PostgreSQL version, extensions and their versions |
| `SHA256SUMS` | Checksums of all files |

Daily backups go to `daily/<date>`, weekly (Sunday) to `weekly/<year-Wweek>`, and monthly (the 1st) to `monthly/<year-month>`; weekly and monthly are hard links to the daily files (`cp -al`), so the same data is not stored three times.

### 7.3 Are the Names and Directories Free?

```bash
echo "===== POSTGRESQL BACKUP UNIT COLLISION CHECK ====="
for f in \
  /usr/local/sbin/pg-logical-backup.sh \
  /etc/systemd/system/pg-logical-backup.service \
  /etc/systemd/system/pg-logical-backup.timer
do
  if [ -e "$f" ]; then
    ls -l "$f"
  else
    echo "NOT_EXISTS: $f"
  fi
done

echo
echo "===== DAILY 02:00 JST SCHEDULE VALIDATION ====="
systemd-analyze calendar '*-*-* 02:00:00'

echo
echo "===== EXISTING RELATED SYSTEMD UNITS ====="
systemctl list-unit-files --no-legend | grep -Ei 'postgres.*backup|pg.*backup' || true
```

All three were `NOT_EXISTS`, and `*-*-* 02:00:00` was interpreted as 02:00 every day (Japan time).

```bash
echo "===== BACKUP SCRIPT DIRECTORY ====="
ls -ld /usr/local/sbin

echo
echo "===== BACKUP STORAGE ROOT ====="
ls -ld /mnt/pve/backup
ls -ld /mnt/pve/backup/dump

echo
echo "===== LOCAL LOCK DIRECTORY ====="
ls -ld /run/lock
```

`/usr/local/sbin`, `/mnt/pve/backup` and `/run/lock` were all fine.

### 7.4 Placing the Script

The script's safety design is as follows.

- Stop if NFS is not mounted (also check that the mount's source is `192.168.0.254:/mnt/backup` and it is NFS)
- Lock so that two cannot run at the same time (`flock`)
- Write to a temporary directory (`.staging`), create and verify all checksums, then move it into the daily directory
- Permissions readable and writable by root only (`umask 077`, directories `700`)
- Delete only old generations beyond the number to keep

At this stage the script is only placed; no DB dump is taken.

> **Run on: pve**

```bash
cat > /usr/local/sbin/pg-logical-backup.sh <<'SCRIPT'
#!/bin/bash

# PostgreSQL logical backup for LXC 109
# Run as root on Proxmox host.

PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
umask 077

CTID=109
MOUNT=/mnt/pve/backup
BASE="$MOUNT/postgresql"
DAILY="$BASE/daily"
WEEKLY="$BASE/weekly"
MONTHLY="$BASE/monthly"
STAGING="$BASE/.staging"
LOCK=/run/lock/pg-logical-backup.lock

log() {
    printf '%s %s\n' "$(date '+%F %T %Z')" "$*"
}

fail() {
    log "ERROR: $*"
    exit 1
}

# Prevent concurrent runs.
exec 9>"$LOCK" || fail "Cannot open lock file"
flock -n 9 || fail "Another backup process is running"

# Confirm the expected NFS mount is active.
mountpoint -q "$MOUNT" || fail "Backup mount is unavailable"
findmnt -rn -T "$MOUNT" -o SOURCE,FSTYPE |
    grep -Fq '192.168.0.254:/mnt/backup nfs' ||
    fail "Unexpected backup filesystem"

# Confirm the container is running.
pct status "$CTID" | grep -q 'status: running' ||
    fail "LXC $CTID is not running"

# Prepare directories.
for dir in "$DAILY" "$WEEKLY" "$MONTHLY" "$STAGING"; do
    mkdir -p "$dir" || fail "Cannot create $dir"
    chmod 700 "$dir" || fail "Cannot secure $dir"
done

DATE=$(date '+%F')
WEEK=$(date '+%G-W%V')
MONTH=$(date '+%Y-%m')
DAY=$(date '+%d')

FINAL="$DAILY/$DATE"
WORK="$STAGING/${DATE}-$$"

[ ! -e "$FINAL" ] || fail "Daily backup already exists: $FINAL"

mkdir -m 700 "$WORK" || fail "Cannot create staging directory"

cleanup() {
    if [ -d "$WORK" ]; then
        rm -rf -- "$WORK"
    fi
}
trap cleanup EXIT

log "Starting PostgreSQL logical backup for LXC $CTID"

# Save global objects, including role password hashes.
pct exec "$CTID" -- runuser -u postgres -- \
    pg_dumpall --globals-only > "$WORK/globals.sql" ||
    fail "Global objects dump failed"

# Save database inventory.
pct exec "$CTID" -- runuser -u postgres -- \
    psql -X -At -d postgres -c "
        SELECT datname
        FROM pg_database
        WHERE datallowconn AND NOT datistemplate
        ORDER BY datname;
    " > "$WORK/database-list.txt" ||
    fail "Database inventory query failed"

[ -s "$WORK/database-list.txt" ] ||
    fail "Database inventory is empty"

# Save PostgreSQL version.
pct exec "$CTID" -- runuser -u postgres -- \
    psql -X -At -d postgres -c "SELECT version();" \
    > "$WORK/postgresql-version.txt" ||
    fail "PostgreSQL version query failed"

# Save extension inventory.
while IFS= read -r db; do
    [ -n "$db" ] || continue

    case "$db" in
        *[!A-Za-z0-9_-]*)
            fail "Unexpected database name: $db"
            ;;
    esac

    {
        printf '%s\t' "$db"
        pct exec "$CTID" -- runuser -u postgres -- \
            psql -X -At -F $'\t' -d "$db" -c \
            "SELECT extname, extversion FROM pg_extension ORDER BY extname;" ||
            fail "Extension query failed for $db"
    } >> "$WORK/extensions.tsv" ||
        fail "Cannot write extension inventory"

    log "Dumping database: $db"
    pct exec "$CTID" -- runuser -u postgres -- \
        pg_dump -Fc -d "$db" > "$WORK/${db}.dump" ||
        fail "Database dump failed: $db"

    [ -s "$WORK/${db}.dump" ] ||
        fail "Database dump is empty: $db"

done < "$WORK/database-list.txt"

[ -s "$WORK/globals.sql" ] ||
    fail "Global objects dump is empty"

# Create checksums for all backup files.
(
    cd "$WORK" || exit 1
    find . -maxdepth 1 -type f ! -name SHA256SUMS -printf '%f\n' |
        LC_ALL=C sort |
        while IFS= read -r file; do
            sha256sum -- "$file"
        done
) > "$WORK/SHA256SUMS" ||
    fail "Checksum generation failed"

# Verify checksums before publishing the backup.
(
    cd "$WORK" || exit 1
    sha256sum -c SHA256SUMS
) || fail "Checksum verification failed"

# Publish daily backup atomically.
mv "$WORK" "$FINAL" || fail "Cannot publish daily backup"
trap - EXIT
log "Daily backup published: $FINAL"

# Weekly generation: Sunday only.
if [ "$DAY" != "00" ] && [ "$(date '+%u')" = "7" ]; then
    if [ ! -e "$WEEKLY/$WEEK" ]; then
        cp -al "$FINAL" "$WEEKLY/$WEEK" ||
            fail "Cannot create weekly hard-link generation"
        log "Weekly generation created: $WEEK"
    fi
fi

# Monthly generation: first day of month only.
if [ "$DAY" = "01" ]; then
    if [ ! -e "$MONTHLY/$MONTH" ]; then
        cp -al "$FINAL" "$MONTHLY/$MONTH" ||
            fail "Cannot create monthly hard-link generation"
        log "Monthly generation created: $MONTH"
    fi
fi

prune_generations() {
    local dir="$1"
    local keep="$2"
    local remove_list

    remove_list=$(find "$dir" -mindepth 1 -maxdepth 1 -type d \
        -printf '%f\n' | LC_ALL=C sort -r | tail -n "+$((keep + 1))")

    if [ -n "$remove_list" ]; then
        while IFS= read -r name; do
            [ -n "$name" ] || continue
            case "$name" in
                *[!A-Za-z0-9_-]*)
                    fail "Unexpected generation name in $dir: $name"
                    ;;
            esac
            rm -rf -- "$dir/$name" ||
                fail "Cannot prune generation: $dir/$name"
            log "Pruned generation: $dir/$name"
        done <<< "$remove_list"
    fi
}

prune_generations "$DAILY" 7
prune_generations "$WEEKLY" 4
prune_generations "$MONTHLY" 3

log "PostgreSQL logical backup completed successfully"
SCRIPT

chmod 700 /usr/local/sbin/pg-logical-backup.sh

echo "===== SCRIPT PERMISSIONS ====="
stat -c '%A %U:%G %n' /usr/local/sbin/pg-logical-backup.sh

echo
echo "===== SCRIPT SYNTAX CHECK ====="
bash -n /usr/local/sbin/pg-logical-backup.sh
echo "BASH_SYNTAX_EXIT=$?"
```

```text
===== SCRIPT PERMISSIONS =====
-rwx------ root:root /usr/local/sbin/pg-logical-backup.sh

===== SCRIPT SYNTAX CHECK =====
BASH_SYNTAX_EXIT=0
```

The script is placed as `700`, readable and executable by root only, and passed the syntax check. **It has not been run yet.**

### 7.5 Can Hard Links Be Created on NFS?

Weekly and monthly generations are created as hard links to the daily files, so this assumes that hard links can be created on TrueNAS's NFS. Create two temporary files (the original and a link), check that they have the same inode, and delete them immediately. Backup data is not touched.

```bash
echo "===== NFS MOUNT DETECTION ====="
findmnt -rn -T /mnt/pve/backup -o SOURCE,FSTYPE
if findmnt -rn -T /mnt/pve/backup -o SOURCE,FSTYPE |
   grep -Fq '192.168.0.254:/mnt/backup nfs'; then
  echo "MOUNT_CHECK=PASS"
else
  echo "MOUNT_CHECK=FAIL"
fi

echo
echo "===== NFS HARDLINK TEST ====="
TEST_FILE="/mnt/pve/backup/.pg-hardlink-test-$$"
LINK_FILE="${TEST_FILE}.link"

cleanup_test() {
  rm -f -- "$TEST_FILE" "$LINK_FILE"
}
trap cleanup_test EXIT

printf 'temporary hardlink test\n' > "$TEST_FILE"

if ln "$TEST_FILE" "$LINK_FILE"; then
  stat -c 'inode=%i links=%h file=%n' "$TEST_FILE" "$LINK_FILE"
  if [ "$(stat -c '%i' "$TEST_FILE")" = "$(stat -c '%i' "$LINK_FILE")" ]; then
    echo "HARDLINK_TEST=PASS"
  else
    echo "HARDLINK_TEST=FAIL"
  fi
else
  echo "HARDLINK_TEST=FAIL"
fi

cleanup_test
trap - EXIT

echo
echo "===== TEST FILE CLEANUP ====="
if [ ! -e "$TEST_FILE" ] && [ ! -e "$LINK_FILE" ]; then
  echo "CLEANUP=PASS"
else
  echo "CLEANUP=FAIL"
fi
```

If it shows `MOUNT_CHECK=PASS`, `HARDLINK_TEST=PASS` and `CLEANUP=PASS`, we can proceed with the current generation management method. The test result is shown in Chapter 1 of Part 40 (it passed).

## Closing Notes

In Part 39 we registered the TrueNAS destination with Proxmox and prepared scheduled backups.

| Item | Result |
|---|---|
| Mount unit | `mnt-pve-backup.mount` changed from ext4 (a nonexistent UUID) to NFS. Backup `/root/mnt-pve-backup.mount.before-nfs-20261122`. Enabled at boot |
| Storage | `truenas-backup` (dir, `content backup`, `is_mountpoint 1`), about 1.89TiB |
| Excluded from backups | VM 100 (TrueNAS itself) |
| Generations | 7 daily, 4 weekly, 3 monthly |
| LXC 109 job | `lxc109-daily` (daily 03:00, snapshot, zstd, `truenas-backup`) registered **while disabled** |
| PostgreSQL logical backup | `/usr/local/sbin/pg-logical-backup.sh` (`700`, syntax check passed) placed; planned to run daily at 02:00 |
| Not yet done | Hard link test result, systemd service and timer, first run, enabling the job and timer, restore test |

In the next part, Part 40, we check the result of the hard-link test and make the PostgreSQL logical backup run every day under systemd.

# Part 40: Completing the PostgreSQL Logical Backup
## Introduction

### About This Book

This is Part 40 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". In Part 39 we placed the PostgreSQL logical backup script `/usr/local/sbin/pg-logical-backup.sh` and got as far as testing whether the hard links used for the weekly and monthly generations can be created on NFS. This part does the following.

1. Check the result of the hard-link test
2. Check the script statically and register the systemd service and timer **while leaving them disabled**
3. Run the first backup by hand and check the file permissions, checksums and dump format
4. Replace the script with a safer version that can be repaired by re-running it if it fails partway
5. Enable the daily 02:00 timer

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)

## Chapter 1: Result of the Hard-Link Test

The result of the last test in Part 39 (create two temporary files on NFS, check that they share the same inode, then delete them) was as follows.

| Checked | Result |
|---|---|
| Mount | `192.168.0.254:/mnt/backup nfs`, `MOUNT_CHECK=PASS` |
| Hard link | both files `inode=5 links=2`, `HARDLINK_TEST=PASS` |
| Cleanup | `CLEANUP=PASS` |

Hard links work on TrueNAS's NFS, so we keep the method in which the daily, weekly and monthly generations share the same data. The test files have been removed.

## Chapter 2: Checking the Script and Registering the Units

### 2.1 Syntax and Permissions

> **Run on: pve**

```bash
echo "===== SCRIPT CONTENT ====="
nl -ba /usr/local/sbin/pg-logical-backup.sh

echo
echo "===== SHELLCHECK AVAILABILITY ====="
if command -v shellcheck >/dev/null 2>&1; then
  shellcheck /usr/local/sbin/pg-logical-backup.sh
  echo "SHELLCHECK_EXIT=$?"
else
  echo "SHELLCHECK_NOT_INSTALLED"
fi

echo
echo "===== SCRIPT SYNTAX ====="
bash -n /usr/local/sbin/pg-logical-backup.sh
echo "BASH_SYNTAX_EXIT=$?"

echo
echo "===== SCRIPT PERMISSIONS ====="
stat -c '%A %U:%G %n' /usr/local/sbin/pg-logical-backup.sh
```

The result was `BASH_SYNTAX_EXIT=0` and the permissions were `-rwx------ root:root`. ShellCheck was not installed, and we do not install it here.

### 2.2 Checking How 02:00 Is Written

> **Run on: pve**

```bash
echo "===== BACKUP TARGET AND DATABASE DUMP ====="
grep -n -E '^(CTID|MOUNT|BASE|DAILY|WEEKLY|MONTHLY|STAGING|LOCK)=|pct exec|pg_dump|pg_dumpall|database-list|extensions.tsv|SHA256SUMS' \
  /usr/local/sbin/pg-logical-backup.sh

echo
echo "===== PUBLISH AND RETENTION LOGIC ====="
grep -n -A35 -B5 -E 'Publish daily|prune_generations|rm -rf' \
  /usr/local/sbin/pg-logical-backup.sh

echo
echo "===== SYSTEMD SCHEDULE VALIDATION ====="
systemd-analyze calendar '*-*-* 02:00:00'
```

It showed `Normalized form: *-*-* 02:00:00`, and the next run as `Mon 2026-11-23 02:00:00 JST`.

### 2.3 Reading the Save and Delete Logic

> **Run on: pve**

```bash
echo "===== BACKUP TARGET AND DUMP COMMANDS ====="
grep -n -E '^(CTID|MOUNT|BASE|DAILY|WEEKLY|MONTHLY|STAGING|LOCK)=|pct exec|pg_dump|pg_dumpall|database-list|extensions.tsv|SHA256SUMS' \
  /usr/local/sbin/pg-logical-backup.sh

echo
echo "===== PUBLISH AND DELETE OPERATIONS ====="
grep -n -A35 -B5 -E 'Publish daily|prune_generations|rm -rf' \
  /usr/local/sbin/pg-logical-backup.sh
```

From the output we confirmed the following.

- Only LXC 109 is backed up
- Global objects (roles and so on) and a dump for each database are saved
- Checksums are created and verified before moving the data to the official daily location
- Deletion only targets the inside of each daily, weekly and monthly generation directory

### 2.4 Registering the Service and Timer While Disabled

Here we do not run the script and do not enable the timer.

> **Run on: pve**

```bash
cat > /etc/systemd/system/pg-logical-backup.service <<'EOF'
[Unit]
Description=PostgreSQL logical backup from LXC 109 to TrueNAS
Wants=network-online.target
After=network-online.target mnt-pve-backup.mount
Requires=mnt-pve-backup.mount

[Service]
Type=oneshot
User=root
Group=root
UMask=0077
ExecStart=/usr/local/sbin/pg-logical-backup.sh
TimeoutStartSec=3h
EOF

cat > /etc/systemd/system/pg-logical-backup.timer <<'EOF'
[Unit]
Description=Daily PostgreSQL logical backup at 02:00 JST

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=false
Unit=pg-logical-backup.service

[Install]
WantedBy=timers.target
EOF

echo "===== SYSTEMD UNIT SYNTAX CHECK ====="
systemd-analyze verify \
  /etc/systemd/system/pg-logical-backup.service \
  /etc/systemd/system/pg-logical-backup.timer
echo "VERIFY_EXIT=$?"

echo
echo "===== SYSTEMD DAEMON RELOAD ====="
systemctl daemon-reload
echo "DAEMON_RELOAD_EXIT=$?"

echo
echo "===== TIMER ENABLEMENT STATE ====="
systemctl is-enabled pg-logical-backup.timer 2>&1
echo "TIMER_ACTIVE_STATE:"
systemctl is-active pg-logical-backup.timer 2>&1
```

`systemd-analyze verify` and `daemon-reload` returned `0`, and the timer was `disabled` and `inactive`.

### 2.5 Checking What Was Registered

> **Run on: pve**

```bash
echo "===== SERVICE UNIT ====="
systemctl cat pg-logical-backup.service

echo
echo "===== TIMER UNIT ====="
systemctl cat pg-logical-backup.timer

echo
echo "===== TIMER STATUS ====="
systemctl status pg-logical-backup.timer --no-pager

echo
echo "===== TIMER LIST ====="
systemctl list-timers --all pg-logical-backup.timer

echo
echo "===== SERVICE EXECUTION STATE ====="
systemctl show pg-logical-backup.service \
  -p ActiveState -p SubState -p Result -p ExecMainStartTimestamp
```

The service showed `Result=success` with an empty `ExecMainStartTimestamp` (it has never run), and the timer showed `0 timers listed.`. `preset: enabled` is displayed, but this is only systemd's default recommendation and does not change the current `disabled`.

## Chapter 3: The First Backup

### 3.1 Running It by Hand

With the timer still disabled, we start the service once. The PostgreSQL service is not stopped.

> **Run on: pve**

```bash
echo "===== START FIRST POSTGRESQL LOGICAL BACKUP ====="
systemctl start pg-logical-backup.service
echo "BACKUP_START_EXIT=$?"

echo
echo "===== SERVICE RESULT ====="
systemctl show pg-logical-backup.service \
  -p ActiveState -p SubState -p Result \
  -p ExecMainStartTimestamp -p ExecMainExitTimestamp

echo
echo "===== BACKUP LOG ====="
journalctl -u pg-logical-backup.service -n 100 --no-pager

echo
echo "===== TIMER REMAINS DISABLED ====="
systemctl is-enabled pg-logical-backup.timer 2>&1
systemctl is-active pg-logical-backup.timer 2>&1
```

In the log we confirmed that the dumps of the 17 databases and the global objects were saved and that all SHA-256 checksums were `OK`. It took about one minute. The data was saved in two places:

- Daily: `/mnt/pve/backup/postgresql/daily/2026-11-22`
- Weekly: `/mnt/pve/backup/postgresql/weekly/2026-W47`

November 22 was a Sunday, so a weekly generation was also created.

### 3.2 Checking the Saved Files

This only reads files. No restore and no writes to the database.

> **Run on: pve**

```bash
BACKUP="/mnt/pve/backup/postgresql/daily/2026-11-22"
WEEKLY="/mnt/pve/backup/postgresql/weekly/2026-W47"

echo "===== BACKUP FILE PERMISSIONS ====="
find "$BACKUP" -maxdepth 1 -type f -printf '%M %u:%g %s %f\n' | sort

echo
echo "===== SHA256 VERIFICATION ====="
(
  cd "$BACKUP" && sha256sum -c SHA256SUMS
)
echo "SHA256_EXIT=$?"

echo
echo "===== DATABASE DUMP READABILITY ====="
for file in "$BACKUP"/*.dump; do
  name=$(basename "$file")
  if pct exec 109 -- runuser -u postgres -- pg_restore --list < "$file" >/dev/null 2>&1; then
    echo "RESTORE_LIST_OK: $name"
  else
    echo "RESTORE_LIST_FAILED: $name"
  fi
done

echo
echo "===== DATABASE DUMP COUNT ====="
find "$BACKUP" -maxdepth 1 -type f -name '*.dump' | wc -l

echo
echo "===== WEEKLY HARDLINK CHECK ====="
stat -c '%i %h %n' "$BACKUP/globals.sql" "$WEEKLY/globals.sql"

echo
echo "===== TIMER STATE ====="
systemctl is-enabled pg-logical-backup.timer 2>&1
systemctl is-active pg-logical-backup.timer 2>&1
```

| Checked | Result |
|---|---|
| File permissions | all `root:root`, `600` |
| SHA256 checksums | all 21 entries `OK` |
| `pg_restore --list` | succeeded for all 17 databases |
| Number of dumps | 17 |
| Hard links between daily and weekly | same inode, link count 2 |
| Timer | `disabled`, `inactive` |

Because `pg_restore --list` succeeded for all of them, we know the files not only exist but can also be read as PostgreSQL custom-format dumps.

### 3.3 Checking the Generation Directories

> **Run on: pve**

```bash
BASE="/mnt/pve/backup/postgresql"

echo "===== DAILY GENERATIONS ====="
find "$BASE/daily" -mindepth 1 -maxdepth 1 -printf '%f  %y\n' | sort

echo
echo "===== WEEKLY GENERATIONS ====="
find "$BASE/weekly" -mindepth 1 -maxdepth 1 -printf '%f  %y\n' | sort

echo
echo "===== MONTHLY GENERATIONS ====="
find "$BASE/monthly" -mindepth 1 -maxdepth 1 -printf '%f  %y\n' | sort

echo
echo "===== STAGING CONTENTS ====="
find "$BASE/.staging" -mindepth 1 -maxdepth 2 -printf '%y %p\n' 2>/dev/null

echo
echo "===== BACKUP ROOT FILESYSTEM ====="
findmnt -T "$BASE" -o TARGET,SOURCE,FSTYPE,OPTIONS
```

daily had `2026-11-22`, weekly had `2026-W47`, monthly was empty (correct, because it is created on the 1st of each month), and staging was empty.

## Chapter 4: Making the Script Safer

### 4.1 What We Want to Fix

Re-reading the script, we found two points to fix before starting scheduled runs.

1. If creating a weekly or monthly generation with `cp -al` fails partway, an incomplete directory is left behind. On the next run, the mere existence of the directory is taken as "already created"
2. If the daily generation already exists, processing ends, so if the weekly or monthly step fails after the daily one was created, re-running on the same day cannot repair it

We fix it as follows.

- Create the weekly and monthly generations in a temporary directory, check them, and then publish them with `mv -T`
- Remove the temporary directory on failure
- If the daily generation already exists, verify its SHA256, reuse it, and create any missing weekly or monthly generations
- When deleting generations, check the directory names and the deletion target
- Do not change existing backups, owners, permissions or the number of generations

> **Caution:** Lines in the script such as `cp -al "$FINAL" "$WEEKLY/$WEEK"` are processing that uses the script's variables. Typed directly into a shell, the variables are empty and you get `cp: cannot stat ''` (the backups are not changed).

### 4.2 Replacing It

Save the original script to `/root/pg-logical-backup.sh.before-safety-fix-20261122`, syntax-check the new version, and replace it. The backup is not run and the timer is not enabled.

> **Run on: pve**

```bash
SCRIPT="/usr/local/sbin/pg-logical-backup.sh"
NEW="/root/pg-logical-backup.sh.new"
BACKUP="/root/pg-logical-backup.sh.before-safety-fix-20261122"

echo "===== 1. PRESERVE CURRENT SCRIPT ====="
if [ -e "$BACKUP" ]; then
  echo "ABORT: backup copy already exists: $BACKUP"
else
  cp -a "$SCRIPT" "$BACKUP"
  echo "SCRIPT_BACKUP_EXIT=$?"
fi

if [ -f "$BACKUP" ]; then
  cat > "$NEW" <<'SCRIPT_EOF'
#!/bin/bash

# PostgreSQL logical backup for LXC 109
# Run as root on Proxmox host.

PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
umask 077

CTID=109
MOUNT=/mnt/pve/backup
BASE="$MOUNT/postgresql"
DAILY="$BASE/daily"
WEEKLY="$BASE/weekly"
MONTHLY="$BASE/monthly"
STAGING="$BASE/.staging"
LOCK=/run/lock/pg-logical-backup.lock

log() {
    printf '%s %s\n' "$(date '+%F %T %Z')" "$*"
}

fail() {
    log "ERROR: $*"
    exit 1
}

verify_backup_dir() {
    local dir="$1"

    [ -d "$dir" ] && [ ! -L "$dir" ] ||
        return 1
    [ -f "$dir/SHA256SUMS" ] && [ ! -L "$dir/SHA256SUMS" ] ||
        return 1

    (
        cd "$dir" &&
        sha256sum --status -c SHA256SUMS
    )
}

# Prevent concurrent runs.
exec 9>"$LOCK" || fail "Cannot open lock file"
flock -n 9 || fail "Another backup process is running"

# Confirm the expected NFS mount is active.
mountpoint -q "$MOUNT" || fail "Backup mount is unavailable"
findmnt -rn -T "$MOUNT" -o SOURCE,FSTYPE |
    grep -Fqx '192.168.0.254:/mnt/backup nfs' ||
    fail "Unexpected backup filesystem"

# Confirm the container is running.
pct status "$CTID" | grep -q 'status: running' ||
    fail "LXC $CTID is not running"

# Prepare directories.
for dir in "$DAILY" "$WEEKLY" "$MONTHLY" "$STAGING"; do
    mkdir -p "$dir" || fail "Cannot create $dir"
    [ -d "$dir" ] && [ ! -L "$dir" ] ||
        fail "Backup directory is not a real directory: $dir"
    chmod 700 "$dir" || fail "Cannot secure $dir"
done

DATE=$(date '+%F')
WEEK=$(date '+%G-W%V')
MONTH=$(date '+%Y-%m')
DAY=$(date '+%d')

FINAL="$DAILY/$DATE"
WORK=""
ACTIVE_TMP=""

cleanup() {
    if [ -n "$WORK" ] &&
       [[ "$WORK" == "$STAGING/"* ]] &&
       [ -d "$WORK" ] && [ ! -L "$WORK" ]; then
        rm -rf -- "$WORK"
    fi

    if [ -n "$ACTIVE_TMP" ] &&
       { [[ "$ACTIVE_TMP" == "$WEEKLY/"* ]] ||
         [[ "$ACTIVE_TMP" == "$MONTHLY/"* ]]; } &&
       [ -d "$ACTIVE_TMP" ] && [ ! -L "$ACTIVE_TMP" ]; then
        rm -rf -- "$ACTIVE_TMP"
    fi
}
trap cleanup EXIT

# Reuse an existing daily generation only after checksum verification.
if [ -e "$FINAL" ]; then
    verify_backup_dir "$FINAL" ||
        fail "Existing daily backup failed verification: $FINAL"
    log "Existing daily backup verified; reusing: $FINAL"
else
    WORK="$STAGING/${DATE}-$$"
    mkdir -m 700 "$WORK" ||
        fail "Cannot create staging directory"

    log "Starting PostgreSQL logical backup for LXC $CTID"

    # Save global objects, including role password hashes.
    pct exec "$CTID" -- runuser -u postgres -- \
        pg_dumpall --globals-only > "$WORK/globals.sql" ||
        fail "Global objects dump failed"

    # Save database inventory.
    pct exec "$CTID" -- runuser -u postgres -- \
        psql -X -At -d postgres -c "
            SELECT datname
            FROM pg_database
            WHERE datallowconn AND NOT datistemplate
            ORDER BY datname;
        " > "$WORK/database-list.txt" ||
        fail "Database inventory query failed"

    [ -s "$WORK/database-list.txt" ] ||
        fail "Database inventory is empty"

    # Save PostgreSQL version.
    pct exec "$CTID" -- runuser -u postgres -- \
        psql -X -At -d postgres -c "SELECT version();" \
        > "$WORK/postgresql-version.txt" ||
        fail "PostgreSQL version query failed"

    # Save extension inventory and database dumps.
    while IFS= read -r db; do
        [ -n "$db" ] || continue

        case "$db" in
            *[!A-Za-z0-9_-]*)
                fail "Unexpected database name: $db"
                ;;
        esac

        {
            printf '%s\t' "$db"
            pct exec "$CTID" -- runuser -u postgres -- \
                psql -X -At -F $'\t' -d "$db" -c \
                "SELECT extname, extversion FROM pg_extension ORDER BY extname;" ||
                fail "Extension query failed for $db"
        } >> "$WORK/extensions.tsv" ||
            fail "Cannot write extension inventory"

        log "Dumping database: $db"
        pct exec "$CTID" -- runuser -u postgres -- \
            pg_dump -Fc -d "$db" > "$WORK/${db}.dump" ||
            fail "Database dump failed: $db"

        [ -s "$WORK/${db}.dump" ] ||
            fail "Database dump is empty: $db"

    done < "$WORK/database-list.txt"

    [ -s "$WORK/globals.sql" ] ||
        fail "Global objects dump is empty"

    # Create checksums for all backup files.
    (
        cd "$WORK" || exit 1
        find . -maxdepth 1 -type f ! -name SHA256SUMS -printf '%f\n' |
            LC_ALL=C sort |
            while IFS= read -r file; do
                sha256sum -- "$file"
            done
    ) > "$WORK/SHA256SUMS" ||
        fail "Checksum generation failed"

    verify_backup_dir "$WORK" ||
        fail "Staging checksum verification failed"

    # Publish daily backup atomically.
    [ ! -e "$FINAL" ] ||
        fail "Daily backup appeared during this run: $FINAL"

    mv -T -- "$WORK" "$FINAL" ||
        fail "Cannot publish daily backup"

    WORK=""
    log "Daily backup published: $FINAL"
fi

# Create a verified hard-link generation and publish it atomically.
create_generation() {
    local source="$1"
    local parent="$2"
    local name="$3"
    local target="$parent/$name"
    local tmp="$parent/.${name}.tmp.$$"

    case "$parent:$name" in
        "$WEEKLY":????-W??|"$MONTHLY":????-??)
            ;;
        *)
            fail "Invalid generation target: $target"
            ;;
    esac

    if [ -e "$target" ]; then
        verify_backup_dir "$target" ||
            fail "Existing generation failed verification: $target"
        log "Existing generation verified: $target"
        return 0
    fi

    [ ! -e "$tmp" ] ||
        fail "Temporary generation already exists: $tmp"

    ACTIVE_TMP="$tmp"

    cp -al -- "$source" "$tmp" ||
        fail "Cannot create temporary hard-link generation: $tmp"

    verify_backup_dir "$tmp" ||
        fail "Temporary generation failed verification: $tmp"

    [ ! -e "$target" ] ||
        fail "Generation target appeared during creation: $target"

    mv -T -- "$tmp" "$target" ||
        fail "Cannot publish generation: $target"

    ACTIVE_TMP=""
    log "Generation published: $target"
}

# Weekly generation: Sunday only.
if [ "$(date '+%u')" = "7" ]; then
    create_generation "$FINAL" "$WEEKLY" "$WEEK"
fi

# Monthly generation: first day of month only.
if [ "$DAY" = "01" ]; then
    create_generation "$FINAL" "$MONTHLY" "$MONTH"
fi

# Prune only validated generation directories.
prune_generations() {
    local dir="$1"
    local kind="$2"
    local keep="$3"
    local name
    local target
    local -a generations=()

    mapfile -t generations < <(
        find "$dir" -mindepth 1 -maxdepth 1 -type d \
            -printf '%f\n' | LC_ALL=C sort -r
    )

    for name in "${generations[@]}"; do
        case "$kind:$name" in
            daily:????-??-??|weekly:????-W??|monthly:????-??)
                ;;
            *)
                fail "Unexpected generation name in $dir: $name"
                ;;
        esac
    done

    if [ "${#generations[@]}" -gt "$keep" ]; then
        for name in "${generations[@]:$keep}"; do
            target="$dir/$name"

            [ -d "$target" ] && [ ! -L "$target" ] ||
                fail "Prune target is not a real directory: $target"

            rm -rf -- "$target" ||
                fail "Cannot prune generation: $target"

            log "Pruned generation: $target"
        done
    fi
}

prune_generations "$DAILY" daily 7
prune_generations "$WEEKLY" weekly 4
prune_generations "$MONTHLY" monthly 3

log "PostgreSQL logical backup completed successfully"
SCRIPT_EOF

  echo
  echo "===== 2. CHECK NEW SCRIPT SYNTAX ====="
  bash -n "$NEW"
  SYNTAX_EXIT=$?
  echo "BASH_SYNTAX_EXIT=$SYNTAX_EXIT"

  if [ "$SYNTAX_EXIT" -eq 0 ]; then
    echo
    echo "===== 3. INSTALL NEW SCRIPT ====="
    install -o root -g root -m 700 "$NEW" "$SCRIPT"
    INSTALL_EXIT=$?
    echo "INSTALL_EXIT=$INSTALL_EXIT"

    if [ "$INSTALL_EXIT" -eq 0 ]; then
      rm -f -- "$NEW"
      echo
      echo "===== 4. VERIFY INSTALLED SCRIPT ====="
      stat -c '%A %U:%G %n' "$SCRIPT"
      bash -n "$SCRIPT"
      echo "INSTALLED_SYNTAX_EXIT=$?"
    fi
  fi
else
  echo "ABORT: original script backup was not created"
fi

echo
echo "===== TIMER STATE (MUST REMAIN DISABLED) ====="
systemctl is-enabled pg-logical-backup.timer
systemctl is-active pg-logical-backup.timer
```

Saving the original, replacing it and the Bash syntax check all returned exit code `0`. The owner and permissions are `root:root`, `700`.

### 4.3 Checking What Was Placed

We check the contents of the file to make sure no characters were mixed in when pasting into the terminal.

> **Run on: pve**

```bash
SCRIPT="/usr/local/sbin/pg-logical-backup.sh"

echo "===== INSTALLED SCRIPT: FULL CONTENT ====="
nl -ba "$SCRIPT"

echo
echo "===== SCRIPT CHECKSUM ====="
sha256sum "$SCRIPT"

echo
echo "===== ORIGINAL SCRIPT BACKUP CHECKSUM ====="
sha256sum /root/pg-logical-backup.sh.before-safety-fix-20261122

echo
echo "===== IMPORTANT FUNCTION MARKERS ====="
grep -nE '^(verify_backup_dir|cleanup|create_generation|prune_generations)\(\)|Daily backup|Weekly generation|Monthly generation|completed successfully|rm -rf|cp -al|mv -T' "$SCRIPT"

echo
echo "===== TIMER STATE ====="
systemctl is-enabled pg-logical-backup.timer
systemctl is-active pg-logical-backup.timer
```

We checked all 279 lines and confirmed that all the intended safeguards are present.

| Safeguard | Result |
|---|---|
| Verify the SHA256 of an existing daily generation | present |
| Reuse the daily generation | present |
| Create weekly and monthly in a temporary directory | present |
| Verify checksums before publishing | present |
| Publish generations with `mv -T` | present |
| Remove temporary data on abnormal exit | present |
| Check generation names | present |
| Number of generations | 7 days, 4 weeks, 3 months |

## Chapter 5: Enabling the Daily 02:00 Timer

This operation does not start a backup immediately. The next run is Monday, November 23, 2026, at 02:00. The Proxmox backup job for LXC 109 stays disabled for now.

> **Run on: pve**

```bash
echo "===== ENABLE POSTGRESQL BACKUP TIMER ====="
systemctl enable --now pg-logical-backup.timer
echo "ENABLE_EXIT=$?"

echo
echo "===== ENABLED STATE ====="
systemctl is-enabled pg-logical-backup.timer

echo
echo "===== ACTIVE STATE ====="
systemctl is-active pg-logical-backup.timer

echo
echo "===== TIMER STATUS ====="
systemctl status pg-logical-backup.timer --no-pager -l

echo
echo "===== NEXT SCHEDULE ====="
systemctl list-timers --all pg-logical-backup.timer --no-pager
```

| Item | State |
|---|---|
| Timer | `enabled`, `active (waiting)` |
| Run time | daily at 02:00 (Japan time) |
| Next run | November 23, 2026, 02:00 |
| Target | PostgreSQL in LXC 109 |
| Destination | TrueNAS NFS `/mnt/pve/backup/postgresql` |
| Generations | daily 7, weekly 4, monthly 3 |

The result of the next day's run is checked in Part 43.

## Closing Notes

In Part 40 we completed the PostgreSQL logical backup and made it run automatically.

| Item | Result |
|---|---|
| Hard-link test | passed (same inode, link count 2) |
| Service and timer | registered `pg-logical-backup.service` and `.timer` (daily 02:00) |
| First backup | 17 databases and the global objects. 21 checksum entries `OK`, `pg_restore --list` succeeded for 17, permissions `600` |
| Script | replaced with a safer version (279 lines) that can be repaired by re-running. The original is `/root/pg-logical-backup.sh.before-safety-fix-20261122` |
| Timer | enabled (`enabled`, `active`) |
| Not yet done | Proxmox backup of LXC 109, restore test |

In the next part, Part 41, we back up LXC 109 to TrueNAS with Proxmox and test restoring it to an LXC with a different number.

# Part 41: Backing Up LXC 109 and Testing an Isolated Restore
## Introduction

### About This Book

This is Part 41 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". In Part 40 we made the PostgreSQL logical backup run daily at 02:00. Here we finish the other backup, the **Proxmox backup of the whole of LXC 109**, and test whether it can actually be restored.

1. Back up LXC 109 to TrueNAS's NFS (`truenas-backup`) for the first time and check the archive
2. Enable the daily 03:00 job `lxc109-daily`
3. Investigate, read-only, the thin pool warning shown during the backup
4. Restore the backup to an LXC with a different number (CTID 310) **with its network cut off**
5. Confirm that the restored PostgreSQL starts and that the 17 databases, extensions and role permissions are back

The production LXC 109 is neither stopped nor changed.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)

## Chapter 1: Backing Up LXC 109 for the First Time

### 1.1 Checks Before Running

> **Run on: pve**

```bash
echo "===== NFS MOUNT ====="
findmnt -T /mnt/pve/backup

echo
echo "===== PROXMOX STORAGE ====="
pvesm status --storage truenas-backup

echo
echo "===== LXC 109 STATUS ====="
pct status 109

echo
echo "===== LXC 109 CONFIGURATION ====="
pct config 109

echo
echo "===== BACKUP JOB STATE ====="
pvesh get /cluster/backup --output-format json
```

| Checked | Result |
|---|---|
| TrueNAS NFS mount | normal |
| Storage `truenas-backup` | `active`, about 1.9TB free |
| LXC 109 | `running` |
| Target | rootfs of LXC 109 (50GB) |
| Mode, compression | snapshot, zstd |
| Generations | 7 daily, 4 weekly, 3 monthly |
| Daily 03:00 job | `disabled` |

`pvesm status` prints an error about the `windows_d/windows_d` VG partway through; this is a separate, pre-existing problem, and `truenas-backup` is `active`. We do not touch it here.

### 1.2 Running the Backup

Run it once in snapshot mode without stopping the LXC.

> **Run on: pve**

```bash
echo "===== START LXC 109 FIRST BACKUP ====="
vzdump 109 \
  --storage truenas-backup \
  --mode snapshot \
  --compress zstd

BACKUP_EXIT=$?
echo
echo "===== BACKUP EXIT CODE ====="
echo "BACKUP_EXIT=$BACKUP_EXIT"

echo
echo "===== BACKUP FILES ====="
ls -lh /mnt/pve/backup/dump/ | tail -20
```

| Item | Result |
|---|---|
| Finished | November 22, 2026, 20:29 |
| Source data | about 1.7GiB |
| Saved file | about 473MiB (`vzdump-lxc-109-2026_11_22-20_28_42.tar.zst`) |
| Duration | 31 seconds |
| Exit code | `0` |
| Temporary snapshot | removed correctly |

The log showed thin pool warnings (no protection by automatic extension; the total size of the virtual volumes exceeds the real capacity). This is not a backup failure. We look into it in Chapter 3.

### 1.3 Checking the Archive

> **Run on: pve**

```bash
BACKUP="/mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst"

echo "===== ARCHIVE EXISTENCE ====="
stat "$BACKUP"

echo
echo "===== ZSTD INTEGRITY TEST ====="
zstd -t "$BACKUP"
echo "ZSTD_TEST_EXIT=$?"

echo
echo "===== ARCHIVE CONTENTS ====="
tar --use-compress-program=unzstd -tf "$BACKUP" | head -30
echo "TAR_LIST_EXIT=${PIPESTATUS[0]}"

echo
echo "===== LXC 109 STATUS ====="
pct status 109

echo
echo "===== PROXMOX BACKUP JOB STATE ====="
pvesh get /cluster/backup --output-format json

echo
echo "===== POSTGRESQL TIMER STATE ====="
systemctl is-enabled pg-logical-backup.timer
systemctl is-active pg-logical-backup.timer
```

| Checked | Result |
|---|---|
| File | present, 495,241,299 bytes, `root:root` |
| zstd integrity | `ZSTD_TEST_EXIT=0` |
| Listing inside the archive | readable |
| LXC 109 | `running` |
| PostgreSQL timer | `enabled`, `active` |

`TAR_LIST_EXIT=141` is shown, but this is because `head -30` closed the pipe after reading 30 lines and `tar` received SIGPIPE; the archive is not broken.

## Chapter 2: Enabling the Daily 03:00 Job

Set only `enabled` of the registered job `lxc109-daily` to `1`. Nothing else is changed.

> **Run on: pve**

```bash
echo "===== ENABLE LXC 109 BACKUP JOB ====="
pvesh set /cluster/backup/lxc109-daily --enabled 1
echo "ENABLE_EXIT=$?"

echo
echo "===== VERIFY BACKUP JOB ====="
pvesh get /cluster/backup --output-format json

echo
echo "===== VERIFY NEXT RUN ====="
systemd-analyze calendar '*-*-* 03:00:00'

echo
echo "===== VERIFY STORAGE ====="
pvesm status --storage truenas-backup
```

With `ENABLE_EXIT=0`, the job is enabled. Both backups are now automatic.

| Time | Backup | Target |
|---|---|---|
| Daily 02:00 | PostgreSQL logical backup (systemd timer) | the 17 databases in LXC 109 |
| Daily 03:00 | Proxmox backup (`lxc109-daily`, snapshot, zstd) | LXC 109 |

## Chapter 3: Investigating the Thin Pool

If the thin pool fills up, disk reads and writes of several VMs and LXCs are affected. Here we change no settings and only read the current state.

### 3.1 Usage and Automatic Extension Settings

> **Run on: pve**

```bash
echo "===== PHYSICAL VOLUMES ====="
pvs -o pv_name,vg_name,pv_size,pv_free

echo
echo "===== VOLUME GROUP ====="
vgs -o vg_name,vg_size,vg_free,pv_count,lv_count pve

echo
echo "===== THIN POOL AND LOGICAL VOLUMES ====="
lvs -a -o vg_name,lv_name,lv_attr,lv_size,data_percent,metadata_percent,segtype,devices pve

echo
echo "===== THIN POOL AUTOEXTEND CONFIGURATION ====="
lvmconfig --type current activation/thin_pool_autoextend_threshold
lvmconfig --type current activation/thin_pool_autoextend_percent

echo
echo "===== LVM CONFIGURATION FILE ====="
grep -n -E 'thin_pool_autoextend_threshold|thin_pool_autoextend_percent|thin_pool_autoextend' /etc/lvm/lvm.conf

echo
echo "===== LVM MONITOR SERVICE ====="
systemctl is-enabled lvm2-monitor.service
systemctl is-active lvm2-monitor.service

echo
echo "===== DEVICE MAPPER STATUS ====="
dmsetup status
```

Data usage of thin pool `pve/data` is **61.69%** and metadata usage is **2.18%**, so capacity will not run out immediately. There was no automatic-extension setting, and VG `pve` had 16GiB free.

### 3.2 Is There Capacity to Add?

> **Run on: pve**

```bash
echo "===== NVME DISK LAYOUT ====="
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS /dev/nvme0n1

echo
echo "===== PARTITION FREE SPACE ====="
parted -s /dev/nvme0n1 unit GiB print free

echo
echo "===== PVE PHYSICAL VOLUME ====="
pvs --units g -o pv_name,pv_size,pv_free,pv_pe_count,pv_pe_alloc_count /dev/nvme0n1p3

echo
echo "===== PVE THIN POOL ====="
lvs --units g -o lv_name,lv_size,data_percent,metadata_percent,seg_monitor,lv_attr pve/data

echo
echo "===== LVM DEFAULT AUTOEXTEND VALUES ====="
lvmconfig --type default activation/thin_pool_autoextend_threshold
lvmconfig --type default activation/thin_pool_autoextend_percent

echo
echo "===== LVM MONITOR PROCESS ====="
pgrep -a dmeventd
```

```bash
echo "===== ALL PHYSICAL DISKS ====="
lsblk -d -o NAME,SIZE,MODEL,SERIAL,TYPE

echo
echo "===== ALL PARTITIONS ====="
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS

echo
echo "===== ALL VOLUME GROUPS ====="
vgs -o vg_name,vg_size,vg_free,pv_count,lv_count

echo
echo "===== ALL PHYSICAL VOLUMES ====="
pvs -o pv_name,vg_name,pv_size,pv_free

echo
echo "===== PVE THIN POOL DETAILS ====="
lvs -a -o vg_name,lv_name,lv_size,data_percent,metadata_percent,seg_monitor,lv_attr pve
```

The third NVMe partition runs to the end of the disk, and there is no unallocated space. The other physical disks were each already assigned to other VGs.

Extending the 794GiB thin pool by just 5% needs about 39.7GiB, so with only 16GiB free we do not set up automatic extension. We also do not borrow disks from other VGs or shrink existing storage. We will set it up when the PVE disk is enlarged in the future (it is listed as a check item in the operations manual).

## Chapter 4: Restoring to CTID 310

### 4.1 Checks Before Restoring

> **Run on: pve**

```bash
echo "===== TEST CTID 310 AVAILABILITY ====="
pct status 310
qm status 310

echo
echo "===== LOCAL-LVM STORAGE ====="
pvesm status --storage local-lvm

echo
echo "===== RESTORE COMMAND OPTIONS ====="
pct help restore

echo
echo "===== BACKUP ARCHIVE CONFIGURATION ====="
tar --use-compress-program=unzstd -xOf \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst \
  ./etc/vzdump/pct.conf

echo
echo "===== BACKUP ARCHIVE SIZE ====="
du -h /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst
```

| Checked | Result |
|---|---|
| CTID 310 | not in use |
| `local-lvm` | `active`, about 304GiB free |
| Backup | 473MiB |
| Settings inside the backup | Debian, 2 CPUs, 4GiB, rootfs 50GiB, unprivileged |
| Original IP address | `192.168.0.151` |

The backup contains the original IP address. If it were connected to the network as is, its IP address would clash with the production LXC 109. So we restore it with the network cut off and without automatic start.

### 4.2 Restoring

> **Run on: pve**

```bash
echo "===== RESTORE LXC 109 TO TEST CTID 310 ====="
pct restore 310 \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst \
  --storage local-lvm \
  --net0 name=eth0,bridge=vmbr0,link_down=1,ip=manual,ip6=manual \
  --onboot 0 \
  --start 0 \
  --unique 1

RESTORE_EXIT=$?
echo
echo "RESTORE_EXIT=$RESTORE_EXIT"

if [ "$RESTORE_EXIT" -eq 0 ]; then
  echo
  echo "===== RESTORED CONTAINER CONFIGURATION ====="
  pct config 310

  echo
  echo "===== RESTORED CONTAINER STATUS ====="
  pct status 310
fi
```

With `RESTORE_EXIT=0`, the rootfs of CTID 310 (50GiB) was created and about 1.7GiB of data was extracted. The container remains stopped.

However, the restored configuration **kept the settings from the backup (the same IP address as production)**, not the settings given with `--net0` (the same behavior as in Part 37). It has not been started yet, so no IP address clash has occurred.

### 4.3 Cutting Off the Network

Before starting it, explicitly cut off `net0` of CTID 310.

> **Run on: pve**

```bash
echo "===== DISABLE TEST CONTAINER NETWORK ====="
pct set 310 --net0 name=eth0,bridge=vmbr0,link_down=1,ip=manual,ip6=manual

echo
echo "===== VERIFY NETWORK CONFIGURATION ====="
pct config 310 | grep -E '^(net[0-9]+|onboot|rootfs):'

echo
echo "===== VERIFY CONTAINER IS STOPPED ====="
pct status 310
```

| Item | State |
|---|---|
| `link_down` | `1` (virtual NIC disconnected) |
| IP address | `ip=manual`, `ip6=manual` (no production IP address) |
| `onboot` | `0` |
| State | `stopped` |

## Chapter 5: Checking the Restored PostgreSQL

### 5.1 Starting It

Start only CTID 310, with its network still cut off.

> **Run on: pve**

```bash
echo "===== START ISOLATED TEST CONTAINER 310 ====="
pct start 310
START_EXIT=$?
echo "START_EXIT=$START_EXIT"

if [ "$START_EXIT" -eq 0 ]; then
  echo
  echo "===== CONTAINER STATUS ====="
  pct status 310

  echo
  echo "===== NETWORK CONFIGURATION ====="
  pct config 310 | grep -E '^(net[0-9]+|onboot):'

  echo
  echo "===== POSTGRESQL CLUSTER STATUS ====="
  pct exec 310 -- pg_lsclusters

  echo
  echo "===== POSTGRESQL SERVICE STATUS ====="
  pct exec 310 -- systemctl is-active postgresql
  echo "SERVICE_STATUS_EXIT=$?"

  echo
  echo "===== POSTGRESQL VERSION ====="
  pct exec 310 -- runuser -u postgres -- psql -Atqc "SELECT version();"

  echo
  echo "===== RESTORED DATABASE LIST ====="
  pct exec 310 -- runuser -u postgres -- psql -Atqc \
    "SELECT datname FROM pg_database WHERE datallowconn AND NOT datistemplate ORDER BY datname;"

  echo
  echo "===== RESTORED EXTENSIONS ====="
  pct exec 310 -- runuser -u postgres -- psql -Atqc \
    "SELECT current_database(), extname, extversion FROM pg_extension ORDER BY current_database(), extname;" \
    --dbname=postgres
fi
```

The start returned `START_EXIT=0`. Right after starting, SQL connections are refused with `the database system is starting up`.

### 5.2 Confirming Startup Has Finished

> **Run on: pve**

```bash
echo "===== POSTGRESQL CLUSTER STATUS ====="
pct exec 310 -- pg_lsclusters

echo
echo "===== POSTGRESQL SERVICE DETAILS ====="
pct exec 310 -- systemctl status postgresql --no-pager -l

echo
echo "===== POSTGRESQL 17 SERVICE DETAILS ====="
pct exec 310 -- systemctl status postgresql@17-main --no-pager -l

echo
echo "===== POSTGRESQL STARTUP LOG ====="
pct exec 310 -- journalctl -u postgresql@17-main -n 80 --no-pager

echo
echo "===== POSTGRESQL SERVER LOG ====="
pct exec 310 -- tail -n 80 /var/log/postgresql/postgresql-17-main.log

echo
echo "===== POSTGRESQL PROCESS ====="
pct exec 310 -- ps -eo pid,ppid,stat,etime,args | grep -E '[p]ostgres|[p]ostmaster'

echo
echo "===== POSTGRESQL READINESS ====="
pct exec 310 -- pg_isready -h /var/run/postgresql -p 5432
```

The end of the log has `database system is ready to accept connections`, and `pg_isready` also returned `accepting connections`. `automatic recovery in progress` in the log is the replay of WAL that had not been completed at backup time; after it, the end of recovery and the start of accepting connections are recorded.

`systemctl is-active postgresql` may show `inactive`, but on Debian the parent service `postgresql.service` is designed to be `active (exited)`, and the actual cluster service is `postgresql@17-main.service`. This is not an error.

### 5.3 Databases and Extensions

> **Run on: pve**

```bash
echo "===== POSTGRESQL VERSION ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -Atqc \
  "SELECT version();"

echo
echo "===== DATABASE INVENTORY ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -P pager=off -c \
  "SELECT datname, pg_size_pretty(pg_database_size(datname)) AS size
   FROM pg_database
   WHERE datallowconn AND NOT datistemplate
   ORDER BY datname;"

echo
echo "===== CONNECTIVITY TEST FOR ALL DATABASES ====="
pct exec 310 -- bash -lc '
while IFS= read -r db; do
  [ -n "$db" ] || continue
  printf "%-24s " "$db"
  runuser -u postgres -- psql -X -d "$db" -Atqc \
    "SELECT current_database() || E'\'' : CONNECTED'\'';" 2>&1
done < <(
  runuser -u postgres -- psql -X -d postgres -Atqc \
    "SELECT datname FROM pg_database WHERE datallowconn AND NOT datistemplate ORDER BY datname"
)
'

echo
echo "===== INSTALLED EXTENSIONS BY DATABASE ====="
pct exec 310 -- bash -lc '
while IFS= read -r db; do
  [ -n "$db" ] || continue
  echo "--- $db ---"
  runuser -u postgres -- psql -X -d "$db" -P pager=off -c \
    "SELECT extname, extversion FROM pg_extension ORDER BY extname;"
done < <(
  runuser -u postgres -- psql -X -d postgres -Atqc \
    "SELECT datname FROM pg_database WHERE datallowconn AND NOT datistemplate ORDER BY datname"
)
'
```

- PostgreSQL 17.11 started and all 17 databases could be connected to
- `vector 0.8.7` in three: `easywrider`, `postgres` and `vector_db`
- `plpgsql 1.0` in the other databases
- Database sizes also match the original records

### 5.4 Roles and Permissions

Password hashes are not displayed.

> **Run on: pve**

```bash
echo "===== ROLE INVENTORY (NO PASSWORD DATA) ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -P pager=off -c \
  "SELECT rolname, rolsuper, rolinherit, rolcreaterole,
          rolcreatedb, rolcanlogin, rolreplication, rolbypassrls
   FROM pg_roles
   ORDER BY rolname;"

echo
echo "===== WAZUH_COLLECTOR ROLE ATTRIBUTES ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -P pager=off -c \
  "SELECT rolname, rolsuper, rolinherit, rolcreaterole,
          rolcreatedb, rolcanlogin, rolreplication, rolbypassrls
   FROM pg_roles
   WHERE rolname = 'wazuh_collector';"

echo
echo "===== WAZUH_COLLECTOR ROLE MEMBERSHIPS ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -P pager=off -c \
  "SELECT parent.rolname AS granted_role
   FROM pg_auth_members m
   JOIN pg_roles parent ON parent.oid = m.roleid
   JOIN pg_roles member ON member.oid = m.member
   WHERE member.rolname = 'wazuh_collector';"

echo
echo "===== WAZUH_COLLECTOR TABLE PRIVILEGES ====="
pct exec 310 -- bash -lc '
while IFS= read -r db; do
  [ -n "$db" ] || continue
  echo "--- $db ---"
  runuser -u postgres -- psql -X -d "$db" -P pager=off -c \
    "SELECT table_schema, table_name, privilege_type
     FROM information_schema.role_table_grants
     WHERE grantee = '\''wazuh_collector'\''
     ORDER BY table_schema, table_name, privilege_type;"
done < <(
  runuser -u postgres -- psql -X -d postgres -Atqc \
    "SELECT datname FROM pg_database WHERE datallowconn AND NOT datistemplate ORDER BY datname"
)
'

echo
echo "===== WAZUH_COLLECTOR DATABASE CONNECT PRIVILEGES ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -P pager=off -c \
  "SELECT datname,
          has_database_privilege('wazuh_collector', datname, 'CONNECT') AS can_connect
   FROM pg_database
   WHERE datallowconn AND NOT datistemplate
   ORDER BY datname;"
```

`wazuh_collector` had `SUPERUSER`, `CREATEDB`, `CREATEROLE`, `REPLICATION` and `INHERIT` all disabled, and was not a member of any role. Its only table permission is `INSERT` on `security_workbench.incident.alert_events`.

`information_schema.role_table_grants` alone does not show permissions via PUBLIC or per-column permissions, so we also check the effective permissions.

> **Run on: pve**

```bash
echo "===== EFFECTIVE TABLE PRIVILEGES ====="
pct exec 310 -- runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
  "SELECT
     has_table_privilege('wazuh_collector', 'incident.alert_events', 'SELECT') AS can_select,
     has_table_privilege('wazuh_collector', 'incident.alert_events', 'INSERT') AS can_insert,
     has_table_privilege('wazuh_collector', 'incident.alert_events', 'UPDATE') AS can_update,
     has_table_privilege('wazuh_collector', 'incident.alert_events', 'DELETE') AS can_delete,
     has_table_privilege('wazuh_collector', 'incident.alert_events', 'TRUNCATE') AS can_truncate,
     has_table_privilege('wazuh_collector', 'incident.alert_events', 'REFERENCES') AS can_references,
     has_table_privilege('wazuh_collector', 'incident.alert_events', 'TRIGGER') AS can_trigger;"

echo
echo "===== EFFECTIVE SCHEMA PRIVILEGES ====="
pct exec 310 -- runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
  "SELECT
     has_schema_privilege('wazuh_collector', 'incident', 'USAGE') AS can_use_schema,
     has_schema_privilege('wazuh_collector', 'incident', 'CREATE') AS can_create_in_schema;"

echo
echo "===== COLUMN-LEVEL PRIVILEGES ====="
pct exec 310 -- runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
  "SELECT table_schema, table_name, column_name, privilege_type
   FROM information_schema.column_privileges
   WHERE grantee = 'wazuh_collector'
   ORDER BY table_schema, table_name, column_name, privilege_type;"

echo
echo "===== EFFECTIVE PRIVILEGES ON ALL TABLES ====="
pct exec 310 -- runuser -u postgres -- psql -X -d security_workbench -P pager=off -c \
  "SELECT n.nspname AS schema_name, c.relname AS table_name,
          has_table_privilege('wazuh_collector', c.oid, 'SELECT') AS can_select,
          has_table_privilege('wazuh_collector', c.oid, 'INSERT') AS can_insert,
          has_table_privilege('wazuh_collector', c.oid, 'UPDATE') AS can_update,
          has_table_privilege('wazuh_collector', c.oid, 'DELETE') AS can_delete
   FROM pg_class c
   JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE c.relkind IN ('r','p')
     AND n.nspname NOT IN ('pg_catalog','information_schema')
   ORDER BY n.nspname, c.relname;"
```

| Target | Result |
|---|---|
| INSERT on `incident.alert_events` | allowed |
| SELECT, UPDATE, DELETE | not allowed |
| TRUNCATE, REFERENCES, TRIGGER | not allowed |
| USAGE on schema `incident` | allowed |
| CREATE on schema `incident` | not allowed |
| Per-column permissions | INSERT on the 14 chosen columns only |

A check across all tables also found no permissions other than on `incident.alert_events`. The restored `wazuh_collector` is INSERT-only, as intended.

> **Note:** The role list also includes roles with `SUPERUSER` (`agent_user`, `aiagent` and others), but that is a separate matter from `wazuh_collector` and was not changed in this test.

### 5.5 Stopping CTID 310

The checks are done, so stop CTID 310. It is not deleted; it is kept for restore checks.

> **Run on: pve**

```bash
echo "===== SHUTDOWN RESTORE TEST CONTAINER ====="
pct shutdown 310 --timeout 60
SHUTDOWN_EXIT=$?
echo "SHUTDOWN_EXIT=$SHUTDOWN_EXIT"

echo
echo "===== VERIFY CONTAINER STATUS ====="
pct status 310

echo
echo "===== VERIFY ISOLATION AND AUTOSTART ====="
pct config 310 | grep -E '^(hostname|onboot|net0|rootfs):'

echo
echo "===== VERIFY PRODUCTION CONTAINER 109 ====="
pct status 109
```

CTID 310 stopped and remains `link_down=1`, `onboot=0`. The production CTID 109 stayed `running`.

## Closing Notes

In Part 41 we ran the Proxmox backup of LXC 109 and confirmed that it can be restored into an isolated environment.

| Checked | Result |
|---|---|
| Backup to TrueNAS NFS | passed (473MiB, 31 seconds) |
| zstd integrity of the archive | passed |
| Daily 03:00 job | enabled |
| Thin pool | 61.69% used. No capacity to add, so automatic extension is on hold |
| Restore to CTID 310 | passed (network cut off) |
| PostgreSQL 17.11 startup and automatic recovery | passed |
| Connections to 17 databases | 17/17 passed |
| pgvector 0.8.7 | confirmed in 3 databases |
| Least privilege of `wazuh_collector` | passed |
| Production CTID 109 | kept running |

In the next part, Part 42, we check read permissions on the backup files themselves and set up ZFS snapshots on the TrueNAS destination.

# Part 42: Protecting the Backups and TrueNAS Snapshots
## Introduction

### About This Book

This is Part 42 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". By Part 41, the PostgreSQL logical backup (daily 02:00) and the Proxmox backup of LXC 109 (daily 03:00) were being saved to TrueNAS's NFS, and the restore test had passed. Here we protect the saved backups themselves.

1. Check whether users other than root can read the backup files, and make the LXC backup directory root-only
2. Check the state of the scheduled backup timer and job
3. Without using the TrueNAS console, inspect datasets and snapshots **from Proxmox through the TrueNAS API**
4. Create daily, weekly and monthly ZFS snapshot tasks for TrueNAS's `backup` dataset

PostgreSQL's `globals.sql` may contain role password hashes, and LXC archives may contain settings and credentials from inside the container. So we limit who can read them to root.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)
- The TrueNAS API commands use `--user root` and ask for TrueNAS's root password each time. Type the password in the terminal; it is not shown on screen. Do not write it in commands, chats or notes.

## Chapter 1: Checking Read Permissions on the Backups

### 1.1 Current Permissions

> **Run on: pve**

```bash
echo "===== BACKUP MOUNT ====="
findmnt -T /mnt/pve/backup

echo
echo "===== BACKUP DIRECTORY PERMISSIONS ====="
namei -l /mnt/pve/backup/postgresql/daily/2026-11-22/globals.sql
namei -l /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst

echo
echo "===== POSTGRESQL BACKUP DIRECTORIES ====="
find /mnt/pve/backup/postgresql -maxdepth 3 -type d \
  -printf '%M %u:%g %p\n' | sort

echo
echo "===== POSTGRESQL BACKUP FILE PERMISSIONS ====="
find /mnt/pve/backup/postgresql -maxdepth 3 -type f \
  -printf '%M %u:%g %s bytes %p\n' | sort

echo
echo "===== LXC 109 BACKUP FILE PERMISSIONS ====="
stat -c '%A %a %U:%G %s bytes %n' \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.log

echo
echo "===== POSTGRESQL BACKUP ACL ====="
if command -v getfacl >/dev/null 2>&1; then
  getfacl -p /mnt/pve/backup/postgresql \
    /mnt/pve/backup/postgresql/daily \
    /mnt/pve/backup/postgresql/daily/2026-11-22 \
    /mnt/pve/backup/postgresql/daily/2026-11-22/globals.sql
else
  echo "getfacl is not installed; POSIX mode was checked above."
fi
```

For the PostgreSQL backups, all directories were `0700`, all files (`.dump`, `globals.sql`, `SHA256SUMS` and so on) were `0600`, and the owner was `root:root`. These need no change.

The LXC 109 archive, on the other hand, was `0644`.

### 1.2 The LXC Backup Directory

> **Run on: pve**

```bash
echo "===== DUMP DIRECTORY PERMISSIONS ====="
namei -l /mnt/pve/backup/dump
stat -c '%A %a %U:%G %n' /mnt/pve/backup/dump

echo
echo "===== LXC 109 BACKUP FILE AND LOG ====="
stat -c '%A %a %U:%G %s bytes %n' \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.log

echo
echo "===== PROXMOX BACKUP JOB ====="
pvesh get /cluster/backup/lxc109-daily --output-format yaml

echo
echo "===== VZDUMP CONFIGURATION ====="
if test -f /etc/vzdump.conf; then
  sed -n '1,160p' /etc/vzdump.conf
else
  echo "/etc/vzdump.conf does not exist"
fi
```

| Target | Permissions | Assessment |
|---|---|---|
| `/mnt/pve/backup/dump/` | `0755` | fix |
| LXC 109 archive | `0644` | fix |
| LXC 109 log | `0644` | fix |
| PostgreSQL backups | `0700`, `0600` | good |

With `dump/` at `0755` and the archive at `0644`, ordinary users on the same host can read the backup.

### 1.3 Making `dump/` Root-Only

Set only the `dump/` directory to `0700`. The owner `root:root`, ownership and ACLs on the TrueNAS side, `/etc/vzdump.conf` and the backup job are not changed. Proxmox backup, restore and generation management, which run as root, keep working.

> **Run on: pve**

```bash
chmod 700 /mnt/pve/backup/dump
```

### 1.4 Checking After the Change

> **Run on: pve**

```bash
echo "===== DUMP DIRECTORY AFTER CHANGE ====="
stat -c '%A %a %U:%G %n' /mnt/pve/backup/dump
namei -l /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst

echo
echo "===== DUMP DIRECTORY ACL ====="
getfacl -p /mnt/pve/backup/dump

echo
echo "===== POSTGRESQL BACKUP PERMISSIONS (UNCHANGED CHECK) ====="
stat -c '%A %a %U:%G %n' \
  /mnt/pve/backup/postgresql \
  /mnt/pve/backup/postgresql/daily \
  /mnt/pve/backup/postgresql/daily/2026-11-22 \
  /mnt/pve/backup/postgresql/daily/2026-11-22/globals.sql

echo
echo "===== NFS MOUNT STILL ACTIVE ====="
findmnt -T /mnt/pve/backup
```

`dump/` became `0700 root:root`, and this was reflected on NFS. The archive file itself is still `0644`, but because its parent directory is `0700`, nobody except root can reach it by the normal path. The PostgreSQL backups remain `0700` and `0600`.

> **Caution:** This `0700` later becomes one of the causes of an LXC backup failure (Part 43). The fix is not to revert `dump/` but to make the job's temporary directory local.

### 1.5 State of the Scheduled Backups

> **Run on: pve**

```bash
echo "===== POSTGRESQL BACKUP TIMER ====="
systemctl status pg-logical-backup.timer --no-pager -l

echo
echo "===== POSTGRESQL BACKUP SERVICE ====="
systemctl status pg-logical-backup.service --no-pager -l

echo
echo "===== POSTGRESQL BACKUP TIMER SCHEDULE ====="
systemctl list-timers --all pg-logical-backup.timer --no-pager

echo
echo "===== POSTGRESQL BACKUP RECENT LOG ====="
journalctl -u pg-logical-backup.service -n 40 --no-pager

echo
echo "===== PROXMOX LXC BACKUP JOB ====="
pvesh get /cluster/backup/lxc109-daily --output-format yaml

echo
echo "===== PROXMOX BACKUP TASKS ====="
pvenode task list --vmid 109 --limit 10
```

| Item | Result |
|---|---|
| `pg-logical-backup.timer` | `enabled`, `active`; next run November 23, 02:00 |
| `pg-logical-backup.service` | last run finished normally (`inactive (dead)` is normal for a oneshot service) |
| `lxc109-daily` | `enabled=1`; next run November 23, 03:00 |
| Generations | 7 daily, 4 weekly, 3 monthly |

## Chapter 2: Using the TrueNAS API from Proxmox

ZFS information inside TrueNAS (VM 100, `192.168.0.254`) is not visible with `zfs list` on Proxmox. Instead of working in the TrueNAS console, we operate from Proxmox. TrueNAS's SSH is not listening (`Connection refused`), so rather than enabling SSH we use the HTTPS management API.

### 2.1 Can We Reach the API?

No credentials are sent; we only check the response.

> **Run on: pve**

```bash
echo "===== TRUENAS HTTPS API V2 ====="
curl -k -sS --connect-timeout 5 --max-time 10 \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/system/version

echo
echo "===== TRUENAS HTTPS API V1 ====="
curl -k -sS --connect-timeout 5 --max-time 10 \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v1.0/system/version

echo
echo "===== TRUENAS HTTPS ROOT ====="
curl -k -sS -o /dev/null \
  --connect-timeout 5 --max-time 10 \
  -w 'HTTP_STATUS=%{http_code} CONNECT=%{time_connect}s TLS=%{time_appconnect}s\n' \
  https://192.168.0.254/
```

API v2.0 returned `HTTP 401` (authentication required) and v1.0 returned `302`. This is not a network problem; authentication is simply required.

### 2.2 Checking Authentication

This only reads version information.

> **Run on: pve**

```bash
echo "===== TRUENAS API AUTHENTICATION TEST ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 10 \
  --user root \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/system/version

echo "===== API TEST COMPLETED ====="
```

It returned `"TrueNAS-12.0-U8.1"` and `HTTP_STATUS=200`. We can now inspect TrueNAS through the API from Proxmox without enabling SSH.

### 2.3 The Backup Dataset

> **Run on: pve**

```bash
echo "===== TRUENAS DATASET API RAW STRUCTURE ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 20 \
  --user root \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/dataset |
jq '
  if type == "array" then
    .[] | {
      name,
      mountpoint,
      encrypted,
      encryption,
      encryptionroot,
      key_loaded,
      compression,
      acltype
    }
  else
    .
  end
'
```

| Item | Result |
|---|---|
| Dataset | `backup` |
| Mount point | `/mnt/backup` |
| Encryption | `false` (not encrypted) |
| Compression | LZ4 |
| ACL type | NFSV4 |

`key_loaded: false` is because the dataset is not encrypted; it does not mean a key has been unloaded. The `parse error` from the final `jq` is because curl's `HTTP_STATUS=` line was appended after the JSON; the dataset information was retrieved.

### 2.4 Finding the Snapshot API

TrueNAS CORE 12.0 does not have the `/pool/snapshot` path used by newer TrueNAS (SCALE and others), and it returns `HTTP 404`. We extract the snapshot-related paths from TrueNAS's own OpenAPI specification.

> **Run on: pve**

```bash
echo "===== TRUENAS SNAPSHOT API PATH INVENTORY ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -o /tmp/truenas-openapi.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0

echo
echo "===== SNAPSHOT-RELATED ENDPOINTS ====="
if jq -e '.paths | type == "object"' /tmp/truenas-openapi.json >/dev/null 2>&1; then
  jq -r '
    .paths
    | to_entries[]
    | select(.key | test("snapshot"; "i"))
    | .key as $path
    | .value
    | to_entries[]
    | select(.key | IN("get","post","put","delete"))
    | [
        $path,
        (.key | ascii_upcase),
        (.value.summary // ""),
        (.value.description // "" | split("\n")[0])
      ]
    | @tsv
  ' /tmp/truenas-openapi.json
else
  echo "OPENAPI_JSON_INVALID"
  head -c 1500 /tmp/truenas-openapi.json
  echo
fi

rm -f /tmp/truenas-openapi.json
```

The snapshot list is **`/api/v2.0/zfs/snapshot`**, and periodic snapshot tasks are **`/api/v2.0/pool/snapshottask`**.

### 2.5 Current Snapshots

> **Run on: pve**

```bash
echo "===== TRUENAS ZFS SNAPSHOT LIST ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -o /tmp/truenas-snapshots.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/zfs/snapshot

echo
echo "===== RESPONSE STRUCTURE ====="
if jq -e 'type == "array"' /tmp/truenas-snapshots.json >/dev/null 2>&1; then
  jq '{
    total_snapshots: length,
    first_entries: .[:3]
  }' /tmp/truenas-snapshots.json

  echo
  echo "===== BACKUP DATASET SNAPSHOTS ====="
  jq '
    [
      .[]
      | select(
          .dataset == "backup"
          or (.name // "" | startswith("backup@"))
          or (.id // "" | startswith("backup@"))
        )
    ]
  ' /tmp/truenas-snapshots.json
else
  echo "RESPONSE IS NOT A JSON ARRAY"
  head -c 2000 /tmp/truenas-snapshots.json
  echo
fi

rm -f /tmp/truenas-snapshots.json
```

There were two snapshots on the whole of TrueNAS: `backup/.system/samba4@…` (for managing Samba inside TrueNAS) and `boot-pool/ROOT/default` (for the boot environment). **There is no snapshot protecting the `backup` dataset itself.**

### 2.6 Current Snapshot Tasks

> **Run on: pve**

```bash
echo "===== TRUENAS PERIODIC SNAPSHOT TASKS ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -o /tmp/truenas-snapshottasks.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask

echo
echo "===== TASK CONFIGURATION ====="
if jq -e 'type == "array"' /tmp/truenas-snapshottasks.json >/dev/null 2>&1; then
  jq '
    map({
      id,
      dataset,
      recursive,
      lifetime_value,
      lifetime_unit,
      naming_schema,
      enabled,
      schedule,
      begin,
      end_time: ."end",
      exclude
    })
  ' /tmp/truenas-snapshottasks.json
else
  echo "UNEXPECTED_RESPONSE"
  head -c 2000 /tmp/truenas-snapshottasks.json
  echo
fi

rm -f /tmp/truenas-snapshottasks.json
```

The result was `[]`, that is, **zero** periodic snapshot tasks.

> **Note:** The task JSON has a field called `end`, which collides with a `jq` keyword. The command above avoids this by writing `."end"`.

In this state, if backup files are deleted by mistake, encrypted or corrupted, there is no way to roll back to an earlier state on the TrueNAS side.

## Chapter 3: Creating Snapshot Tasks

### 3.1 Fields for Creating a Task

> **Run on: pve**

```bash
echo "===== TRUENAS PERIODIC SNAPSHOT POST SCHEMA ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -o /tmp/truenas-openapi.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0

echo
echo "===== POST REQUEST BODY ====="
jq '
  .paths["/pool/snapshottask"].post
  | {
      summary,
      description,
      requestBody,
      responses
    }
' /tmp/truenas-openapi.json

echo
echo "===== REFERENCED SNAPSHOT TASK SCHEMAS ====="
jq '
  .components.schemas
  | with_entries(
      select(.key | test("snapshottask|snapshot_task|periodic"; "i"))
    )
' /tmp/truenas-openapi.json

rm -f /tmp/truenas-openapi.json
```

| Field | Meaning |
|---|---|
| `dataset` | target dataset |
| `recursive` | whether child datasets are included |
| `lifetime_value`, `lifetime_unit` | retention period |
| `naming_schema` | snapshot name format (`%Y %m %d %H %M` are required) |
| `schedule` | minute, hour, day, month, weekday |
| `enabled` | enabled or disabled |

### 3.2 Dataset Hierarchy

With `recursive` enabled, child datasets are included too. To avoid widening the scope too much, we check the hierarchy.

> **Run on: pve**

```bash
echo "===== TRUENAS BACKUP DATASET HIERARCHY ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -o /tmp/truenas-datasets.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/dataset

echo
echo "===== BACKUP DATASET AND CHILD DATASETS ====="
if jq -e 'type == "array"' /tmp/truenas-datasets.json >/dev/null 2>&1; then
  jq '
    [
      .[]
      | select(
          .name == "backup"
          or (.name | startswith("backup/"))
        )
      | {
          name,
          mountpoint,
          type,
          encrypted,
          used,
          available,
          acltype
        }
    ]
    | sort_by(.name)
  ' /tmp/truenas-datasets.json
else
  echo "UNEXPECTED_RESPONSE"
  head -c 2000 /tmp/truenas-datasets.json
  echo
fi

rm -f /tmp/truenas-datasets.json
```

`backup` has no child datasets; it is a single file system. So we use **`backup` only, with `recursive=false`**.

### 3.3 The Chosen Schedule

The backups run at 02:00 (PostgreSQL) and 03:00 (LXC 109), so snapshots are taken after them.

| Type | Runs | Retention | Name |
|---|---|---|---|
| Daily | every day 04:00 | 7 days | `daily-%Y-%m-%d_%H-%M` |
| Weekly | every Sunday 04:10 | 4 weeks | `weekly-%Y-%m-%d_%H-%M` |
| Monthly | the 1st of each month 04:20 | 3 months | `monthly-%Y-%m-%d_%H-%M` |

TrueNAS retention and the backup generation management on the Proxmox side work independently. Note that snapshots on the same pool are not an independent backup against disk failure or loss of the TrueNAS machine itself.

### 3.4 Creating the Daily Task

The following command registers all three tasks (daily, weekly, monthly) at once.

> **Run on: pve**

```bash
echo "===== CREATE DAILY SNAPSHOT TASK ====="
curl -k -sS \
  --connect-timeout 5 --max-time 30 \
  --user root \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "dataset": "backup",
    "recursive": false,
    "exclude": [],
    "lifetime_value": 7,
    "lifetime_unit": "DAY",
    "naming_schema": "daily-%Y-%m-%d_%H-%M",
    "schedule": {
      "minute": "0",
      "hour": "4",
      "dom": "*",
      "month": "*",
      "dow": "*",
      "begin": "00:00",
      "end": "23:59"
    },
    "allow_empty": false,
    "enabled": true
  }' \
  -o /tmp/truenas-task-daily.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask
cat /tmp/truenas-task-daily.json

echo
echo "===== CREATE WEEKLY SNAPSHOT TASK ====="
curl -k -sS \
  --connect-timeout 5 --max-time 30 \
  --user root \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "dataset": "backup",
    "recursive": false,
    "exclude": [],
    "lifetime_value": 4,
    "lifetime_unit": "WEEK",
    "naming_schema": "weekly-%Y-%m-%d_%H-%M",
    "schedule": {
      "minute": "10",
      "hour": "4",
      "dom": "*",
      "month": "*",
      "dow": "0",
      "begin": "00:00",
      "end": "23:59"
    },
    "allow_empty": false,
    "enabled": true
  }' \
  -o /tmp/truenas-task-weekly.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask
cat /tmp/truenas-task-weekly.json

echo
echo "===== CREATE MONTHLY SNAPSHOT TASK ====="
curl -k -sS \
  --connect-timeout 5 --max-time 30 \
  --user root \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "dataset": "backup",
    "recursive": false,
    "exclude": [],
    "lifetime_value": 3,
    "lifetime_unit": "MONTH",
    "naming_schema": "monthly-%Y-%m-%d_%H-%M",
    "schedule": {
      "minute": "20",
      "hour": "4",
      "dom": "1",
      "month": "*",
      "dow": "*",
      "begin": "00:00",
      "end": "23:59"
    },
    "allow_empty": false,
    "enabled": true
  }' \
  -o /tmp/truenas-task-monthly.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask
cat /tmp/truenas-task-monthly.json

echo
echo "===== VERIFY REGISTERED TASKS ====="
curl -k -sS \
  --connect-timeout 5 --max-time 30 \
  --user root \
  -o /tmp/truenas-task-list.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask

if jq -e 'type == "array"' /tmp/truenas-task-list.json >/dev/null 2>&1; then
  jq '
    map({
      id,
      dataset,
      recursive,
      lifetime_value,
      lifetime_unit,
      naming_schema,
      schedule,
      enabled,
      allow_empty
    })
  ' /tmp/truenas-task-list.json
else
  echo "TASK_LIST_RESPONSE_INVALID"
  head -c 2000 /tmp/truenas-task-list.json
  echo
fi

rm -f /tmp/truenas-task-daily.json \
      /tmp/truenas-task-weekly.json \
      /tmp/truenas-task-monthly.json \
      /tmp/truenas-task-list.json
```

The daily task was created with ID `1` (daily 04:00, 7 days, `enabled: true`, state `PENDING`).

> **Caution:** This command runs curl three times in a row and asks for the password each time. In the build records, the input got mixed up when everything was pasted at once: two daily tasks (IDs `1` and `2`) were created, the weekly and monthly ones were not, and the shell was left waiting for more input (`>`). In that case, stop with Ctrl+C, delete the duplicate, and then create the weekly and monthly tasks one at a time. The following command deletes only the periodic task setting (ID `2`); it does not delete any snapshots.
>
> **Run on: pve**

```bash
echo "===== DELETE DUPLICATE SNAPSHOT TASK ID 2 ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -X DELETE \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask/id/2

echo
echo "===== VERIFY REMAINING SNAPSHOT TASKS ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  https://192.168.0.254/api/v2.0/pool/snapshottask |
jq -r '.[] | [
  "ID=\(.id)",
  "NAME=\(.naming_schema)",
  "HOUR=\(.schedule.hour)",
  "MINUTE=\(.schedule.minute)",
  "ENABLED=\(.enabled)"
] | join(" ")'
```

### 3.5 Creating the Weekly Task

> **Run on: pve**

```bash
echo "===== CREATE WEEKLY SNAPSHOT TASK ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -X POST \
  -H 'Content-Type: application/json' \
  --data-binary '{"dataset":"backup","recursive":false,"exclude":[],"lifetime_value":4,"lifetime_unit":"WEEK","naming_schema":"weekly-%Y-%m-%d_%H-%M","schedule":{"minute":"10","hour":"4","dom":"*","month":"*","dow":"0","begin":"00:00","end":"23:59"},"allow_empty":false,"enabled":true}' \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask
```

It was created with ID `3` (every Sunday 04:10, 4 weeks, `recursive: false`, `PENDING`).

### 3.6 Creating the Monthly Task

> **Run on: pve**

```bash
echo "===== CREATE MONTHLY SNAPSHOT TASK ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -X POST \
  -H 'Content-Type: application/json' \
  --data-binary '{"dataset":"backup","recursive":false,"exclude":[],"lifetime_value":3,"lifetime_unit":"MONTH","naming_schema":"monthly-%Y-%m-%d_%H-%M","schedule":{"minute":"20","hour":"4","dom":"1","month":"*","dow":"*","begin":"00:00","end":"23:59"},"allow_empty":false,"enabled":true}' \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask
```

It was created with ID `4` (the 1st of each month 04:20, 3 months, `recursive: false`, `PENDING`).

### 3.7 Checking Everything

> **Run on: pve**

```bash
echo "===== VERIFY ALL TRUENAS SNAPSHOT TASKS ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  -o /tmp/truenas-snapshottasks-final.json \
  -w 'HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/pool/snapshottask

echo
echo "===== TASK CONFIGURATION ====="
jq -r '.[] | [
  "ID=\(.id)",
  "DATASET=\(.dataset)",
  "NAME=\(.naming_schema)",
  "SCHEDULE=\(.schedule.dow) DOM=\(.schedule.dom) \(.schedule.hour):\(.schedule.minute)",
  "RETENTION=\(.lifetime_value) \(.lifetime_unit)",
  "RECURSIVE=\(.recursive)",
  "ENABLED=\(.enabled)",
  "STATE=\(.state.state)"
] | join(" | ")' /tmp/truenas-snapshottasks-final.json

echo
echo "===== TASK COUNT ====="
jq 'length' /tmp/truenas-snapshottasks-final.json
```

| Type | Runs | Retention | ID |
|---|---|---|---|
| Daily | every day 04:00 | 7 days | 1 |
| Weekly | every Sunday 04:10 | 4 weeks | 3 |
| Monthly | the 1st of each month 04:20 | 3 months | 4 |

`HTTP 200`, three tasks registered with no duplicates. All are `dataset: backup`, `recursive: false`, `enabled: true`, do not create empty snapshots (`allow_empty: false`), and have state `PENDING`.

## Chapter 4: Checks Before the First Run

### 4.1 Backups and Destination

> **Run on: pve**

```bash
echo "===== 1. NFS MOUNT ====="
findmnt -T /mnt/pve/backup -o TARGET,SOURCE,FSTYPE,OPTIONS

echo
echo "===== 2. POSTGRESQL BACKUP GENERATIONS ====="
find /mnt/pve/backup/postgresql -maxdepth 2 -type d \
  \( -path '*/daily/*' -o -path '*/weekly/*' -o -path '*/monthly/*' \) \
  -printf '%TY-%Tm-%Td %TH:%TM %p\n' 2>/dev/null | sort

echo
echo "===== POSTGRESQL CHECKSUM VERIFICATION ====="
for f in /mnt/pve/backup/postgresql/daily/*/SHA256SUMS; do
  if [ -f "$f" ]; then
    echo "--- $f ---"
    (cd "$(dirname "$f")" && sha256sum -c SHA256SUMS)
  fi
done

echo
echo "===== 3. LXC 109 BACKUP FILES ====="
ls -lh /mnt/pve/backup/dump/vzdump-lxc-109-* 2>/dev/null

echo
echo "===== LXC 109 ARCHIVE INTEGRITY ====="
for f in /mnt/pve/backup/dump/vzdump-lxc-109-*.tar.zst; do
  if [ -f "$f" ]; then
    echo "--- $f ---"
    zstd -t "$f"
    echo "ZSTD_EXIT=$?"
  fi
done

echo
echo "===== 4. TRUENAS ZFS SNAPSHOTS ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  https://192.168.0.254/api/v2.0/zfs/snapshot |
jq -r '.[] | [
  "NAME=\(.name)",
  "CREATED=\(.creation // "unknown")",
  "REFER=\(.refer // "unknown")"
] | join(" | ")'
```

The NFS mount is normal; the PostgreSQL backup has all 21 SHA-256 entries `OK`, and the LXC 109 archive gives `0` for `zstd -t`. There are no snapshots of the `backup` dataset yet, which is normal before the first scheduled run.

### 4.2 Timer, Job and Mount

> **Run on: pve**

```bash
echo "===== SYSTEM TIME ====="
date '+%Y-%m-%d %H:%M:%S %Z'

echo
echo "===== POSTGRESQL BACKUP TIMER ====="
systemctl is-enabled pg-logical-backup.timer
systemctl is-active pg-logical-backup.timer
systemctl list-timers pg-logical-backup.timer --all

echo
echo "===== POSTGRESQL BACKUP SERVICE ====="
systemctl show pg-logical-backup.service \
  -p LoadState -p ActiveState -p SubState -p Result -p ExecStart

echo
echo "===== PROXMOX LXC 109 BACKUP JOB ====="
pvesh get /cluster/backup/lxc109-daily --output-format json |
jq '{id,enabled,schedule,storage,vmid,mode,compress,prune-backups,repeat-missed}'

echo
echo "===== NFS MOUNT UNIT ====="
systemctl is-enabled mnt-pve-backup.mount
systemctl is-active mnt-pve-backup.mount
systemctl show mnt-pve-backup.mount \
  -p What -p Where -p Type -p ActiveState -p SubState -p NeedDaemonReload

echo
echo "===== NEXT BACKUP CALENDAR TIMES ====="
systemd-analyze calendar '*-*-* 02:00:00'
systemd-analyze calendar '*-*-* 03:00:00'
```

```bash
echo "===== VERIFY LXC 109 BACKUP JOB ====="
pvesh get /cluster/backup/lxc109-daily --output-format json |
jq '{
  id: .id,
  enabled: .enabled,
  schedule: .schedule,
  storage: .storage,
  vmid: .vmid,
  mode: .mode,
  compress: .compress,
  retention: .["prune-backups"],
  repeat_missed: .["repeat-missed"]
}'
```

| Item | Result |
|---|---|
| PostgreSQL timer | `enabled`, `active`; next run November 23, 02:00 |
| Mount unit | `enabled`, `active`, `mounted` |
| `lxc109-daily` | `enabled: 1`, `*-*-* 03:00:00`, `truenas-backup`, snapshot, zstd, 7 daily, 4 weekly, 3 monthly |

## Closing Notes

In Part 42 we limited who can read the backups to root and made TrueNAS keep generations too.

| Item | Result |
|---|---|
| PostgreSQL backups | `0700`, `0600` (unchanged) |
| LXC backups | set `dump/` to `0700` |
| Operating TrueNAS | HTTPS API from Proxmox (SSH left disabled) |
| Dataset `backup` | not encrypted, LZ4, NFSV4 ACLs, no child datasets |
| Snapshot tasks | daily (ID 1), weekly (ID 3), monthly (ID 4) |
| Not yet done | check the result of the scheduled runs on November 23 |

In the next part, Part 43, we check the scheduled runs on November 23. There we find a failure of the LXC 109 backup and a problem where NFS is not mounted after a Proxmox reboot, and fix each.

# Part 43: Backup Failures After a Reboot and the Recovery
## Introduction

### About This Book

This is Part 43 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". By Part 42 we had set up three scheduled jobs (PostgreSQL logical backup at 02:00, LXC 109 backup at 03:00, TrueNAS ZFS snapshots from 04:00). Here we fix two separate problems found when checking the results of the first scheduled runs on the morning of November 23.

| Problem | What happened | Cause | Fix |
|---|---|---|---|
| 1 | After Proxmox rebooted at 06:50, NFS was not mounted | The NFS mount started before TrueNAS's VM 100 had booted and timed out after 90 seconds | Add a service that waits for TrueNAS to boot and NFS to respond before mounting |
| 2 | The 03:00 LXC 109 backup failed with `Permission denied` | The `tar` that reads an unprivileged LXC's files runs as UID 100000, but the temporary directory was created under the root-only NFS `dump/` | Set the temporary directory of job `lxc109-daily` to Proxmox's local `/var/tmp` |

The 02:00 PostgreSQL backup had succeeded.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)
- The TrueNAS API commands ask for TrueNAS's root password each time. Type it in the terminal and do not write it anywhere else.

## Chapter 1: Checking the Results of November 23

### 1.1 The Three Scheduled Jobs

At 08:58 on November 23, we read the logs, the saved files and the ZFS snapshots.

> **Run on: pve**

```bash
echo "===== CURRENT TIME ====="
date '+%Y-%m-%d %H:%M:%S %Z'

echo
echo "===== POSTGRESQL BACKUP RESULT ====="
systemctl show pg-logical-backup.service \
  -p Result -p ExecMainCode -p ExecMainStatus -p ExecMainStartTimestamp -p ExecMainExitTimestamp

journalctl -u pg-logical-backup.service \
  --since "2026-11-23 00:00:00" \
  --no-pager -o short-iso

echo
echo "===== POSTGRESQL BACKUP GENERATIONS ====="
find /mnt/pve/backup/postgresql \
  -mindepth 2 -maxdepth 2 -type d \
  -printf '%TY-%Tm-%Td %TH:%TM %p\n' 2>/dev/null | sort

echo
echo "===== TODAY'S POSTGRESQL CHECKSUM ====="
if [ -f /mnt/pve/backup/postgresql/daily/2026-11-23/SHA256SUMS ]; then
  cd /mnt/pve/backup/postgresql/daily/2026-11-23
  sha256sum -c SHA256SUMS
else
  echo "TODAY_BACKUP_NOT_FOUND"
fi

echo
echo "===== LXC 109 BACKUP ARCHIVES ====="
find /mnt/pve/backup/dump -maxdepth 1 -type f \
  -name 'vzdump-lxc-109-*' \
  -printf '%TY-%Tm-%Td %TH:%TM %s %p\n' | sort

echo
echo "===== PROXMOX LXC 109 TASK HISTORY ====="
pvenode task list --vmid 109 --limit 10

echo
echo "===== TODAY'S ZFS SNAPSHOTS ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  https://192.168.0.254/api/v2.0/zfs/snapshot |
jq -r '.[] | select(.name | startswith("backup@") or startswith("backup/")) |
  ["NAME=\(.name)", "CREATED=\(.creation // "unknown")"] | join(" | ")'
```

The PostgreSQL logical backup finished dumping the 17 databases at 02:01 with `Result=success`. On the other hand, we found the following.

- The generation list under `/mnt/pve/backup/postgresql` is empty
- `/mnt/pve/backup/dump` does not exist
- The 03:00 LXC 109 backup is recorded as `ERR`

### 1.2 Is NFS Mounted?

> **Run on: pve**

```bash
echo "===== NFS MOUNT STATUS ====="
findmnt -T /mnt/pve/backup
mountpoint /mnt/pve/backup
systemctl status mnt-pve-backup.mount --no-pager -l

echo
echo "===== BACKUP PATH STATUS ====="
ls -ld /mnt/pve/backup
ls -la /mnt/pve/backup
df -hT /mnt/pve/backup

echo
echo "===== PROXMOX STORAGE STATUS ====="
pvesm status --storage truenas-backup

echo
echo "===== FAILED LXC 109 BACKUP TASK LOG ====="
pvenode task log 'UPID:pve:0010D698:00B3FB4F:6B032DA9:vzdump:109:root@pam:'

echo
echo "===== NFS MOUNT UNIT JOURNAL ====="
journalctl -u mnt-pve-backup.mount \
  --since "2026-11-23 01:30:00" \
  --no-pager -o short-iso
```

NFS was not mounted. `mnt-pve-backup.mount` started mounting at 06:50:27 and failed with a timeout at 06:51:57. What we see now is the empty local directory under the mount point. The backups on TrueNAS have not disappeared.

> **Caution:** While it is not mounted, do not create files in the local `/mnt/pve/backup`.

## Chapter 2: Why NFS Was Not Mounted

### 2.1 TrueNAS and the Logs

> **Run on: pve**

```bash
echo "===== NETWORK ROUTE TO TRUENAS ====="
ip route get 192.168.0.254

echo
echo "===== TRUENAS PING ====="
ping -c 3 -W 2 192.168.0.254

echo
echo "===== RPC SERVICES ====="
if command -v rpcinfo >/dev/null 2>&1; then
  timeout 10 rpcinfo -p 192.168.0.254
else
  echo "rpcinfo command not installed"
fi

echo
echo "===== NFS EXPORTS ====="
if command -v showmount >/dev/null 2>&1; then
  timeout 10 showmount -e 192.168.0.254
else
  echo "showmount command not installed"
fi

echo
echo "===== TRUENAS HTTPS API ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 15 \
  --user root \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/system/version
```

Ping to TrueNAS had 0% loss, RPC (NFSv3, mountd) responded, and `/mnt/backup` was exported. The TrueNAS API also returned `HTTP 200`. Neither TrueNAS as a whole nor its NFS service is down.

> **Run on: pve**

```bash
echo "===== NFS KERNEL LOG ====="
journalctl -k --since "2026-11-23 01:30:00" --no-pager \
  | grep -Ei 'nfs|rpc|mount|not responding|timed out|server' \
  | tail -n 150

echo
echo "===== NFS SYSTEMD MOUNT LOG ====="
journalctl -u mnt-pve-backup.mount \
  --since "2026-11-23 01:30:00" \
  --no-pager -o short-iso

echo
echo "===== NFS CLIENT MOUNT STATUS ====="
if command -v nfsstat >/dev/null 2>&1; then
  nfsstat -m
else
  echo "nfsstat command not installed"
fi

echo
echo "===== NFS CLIENT SERVER STATE ====="
for f in /proc/fs/nfsfs/servers /proc/fs/nfsfs/volumes; do
  if [ -r "$f" ]; then
    echo "--- $f ---"
    cat "$f"
  else
    echo "$f not available"
  fi
done
```

The kernel log showed that **the Proxmox host had rebooted at about 06:50:22 on November 23**.

### 2.2 The Network at Boot

> **Run on: pve**

```bash
echo "===== PVE UPTIME ====="
uptime
who -b

echo
echo "===== NETWORK INTERFACES ====="
ip -br address
ip route

echo
echo "===== NETWORK ONLINE TARGET ====="
systemctl status network-online.target --no-pager
systemctl show network-online.target -p ActiveState -p ActiveEnterTimestamp

echo
echo "===== NETWORK SERVICES ====="
systemctl status networking.service --no-pager
systemctl status systemd-networkd.service --no-pager

echo
echo "===== BOOT NETWORK JOURNAL ====="
journalctl -b --since "2026-11-23 06:49:30" --until "2026-11-23 06:53:30" --no-pager -o short-iso | grep -Ei 'network|vmbr|eno|link|carrier|dhcp|online|nfs|rpc|mount'

echo
echo "===== NFS MOUNT UNIT ====="
systemctl cat mnt-pve-backup.mount

echo
echo "===== RPC STATD STATUS ====="
systemctl status rpc-statd.service --no-pager
```

`networking.service` finished at 06:50:27, and `network-online.target` was reached at the same time. The link of the physical NIC `eno1` came up at 06:50:29, about two seconds after the mount started.

### 2.3 Host Load

> **Run on: pve**

```bash
echo "===== LOAD AND CPU ====="
uptime
nproc
vmstat 1 5

echo
echo "===== TOP CPU PROCESSES ====="
ps -eo pid,ppid,stat,pcpu,pmem,etime,comm,args --sort=-pcpu | head -25

echo
echo "===== PROCESSES IN UNINTERRUPTIBLE SLEEP ====="
ps -eo pid,ppid,stat,wchan:32,etime,comm,args | awk '$3 ~ /^D/ {print}' | head -40

echo
echo "===== SYSTEMD JOBS ====="
systemctl list-jobs --no-pager

echo
echo "===== DISK IO SUMMARY ====="
iostat -xz 1 3

echo
echo "===== RECENT KERNEL STORAGE ERRORS ====="
journalctl -k -b --since "2026-11-23 06:50:00" --no-pager | grep -Ei 'I/O error|reset|timeout|blocked for more|hung task|buffer I/O|nvme|ata.*error|ext4.*error' | tail -60
```

The load average was about 137, with 132–146 runnable processes (`r` in `vmstat`) for 64 logical CPUs. I/O wait was 0%; what stood out was VM 101 (`ollama-gpu`) and the multiple `llama-server` processes inside it. In the build records, the overloaded LXC was stopped here and the load average dropped to 39. We treat this as separate from the NFS problem.

### 2.4 When the TrueNAS VM Started

> **Run on: pve**

```bash
echo "===== VM100 STATUS AND CONFIG ====="
qm status 100
qm config 100 | grep -E '^(onboot|startup|boot|cores|sockets|memory):'

echo
echo "===== VM100 PROCESS START TIME ====="
ps -p 8278 -o pid,lstart,etime,stat,pcpu,comm

echo
echo "===== VM100 QEMU START JOURNAL ====="
journalctl -b --no-pager | grep -E '100 \(TrueNAS\)|vm-100|VM 100|qmstart|QEMU.*100' | head -60

echo
echo "===== NETWORK ONLINE SERVICES ====="
systemctl status networking.service network-online.target --no-pager -l
systemctl status ifupdown-wait-online.service --no-pager -l

echo
echo "===== NETWORK ONLINE UNIT CONFIGURATION ====="
systemctl cat networking.service
systemctl cat ifupdown-wait-online.service

echo
echo "===== NFS MOUNT UNIT CONFIGURATION ====="
systemctl cat mnt-pve-backup.mount
```

```bash
echo "===== PVE GUEST STARTUP SERVICE ====="
systemctl status pve-guests.service --no-pager -l
systemctl cat pve-guests.service

echo
echo "===== PVE GUEST STARTUP SERVICE DEPENDENCIES ====="
systemctl show pve-guests.service \
  -p After -p Before -p Wants -p Requires -p Type -p TimeoutStartUSec

echo
echo "===== VM100 STARTUP OPTIONS ====="
qm config 100 | grep -E '^(onboot|startup|boot|cores|sockets|memory):'

echo
echo "===== VM STARTUP TASK TIMELINE ====="
journalctl -b --no-pager | grep -E 'Starting VM 100|VM 100 started|start VM 100|starting task.*qmstart:100|Started pve-guests'

echo
echo "===== MOUNT UNIT DEPENDENCIES ====="
systemctl show mnt-pve-backup.mount \
  -p After -p Before -p Wants -p Requires -p TimeoutUSec -p JobTimeoutUSec

echo
echo "===== CURRENT NFS RPC READINESS ====="
timeout 5 rpcinfo -t 192.168.0.254 100005 3
timeout 5 rpcinfo -t 192.168.0.254 100003 3
```

| Time | Event |
|---|---|
| 06:50:27 | `network-online.target` reached; NFS mount started |
| 06:50:29 | `eno1` link up |
| 06:51:57 | NFS mount timed out after 90 seconds |
| 06:54:12 | TrueNAS VM 100 started |
| 07:21:17 | `pve-guests.service` finished starting all guests |

When the NFS mount started, **the destination TrueNAS VM had not started yet**. That is the direct reason for the timeout.

### 2.5 The Approach

We do not wait for `pve-guests.service` to finish. In this boot it took about 29 minutes to start all guests, which would delay the backup destination too much. Also, even after the VM start completes, it takes time until NFS inside TrueNAS is usable. So we do the following.

1. Before mounting, check whether TrueNAS's VM 100 is running
2. Wait until it starts
3. Repeat until TrueNAS's NFSv3 RPC (mountd and NFS) responds
4. Mount only when both respond
5. If it is not ready within the set time (900 seconds), let the mount fail. `is_mountpoint 1` still prevents accidental writes to the local directory

## Chapter 3: Mounting After Waiting for TrueNAS

### 3.1 Placing the Wait Script and Service

We place the following three files. No mount is performed and no VM is restarted.

| File | Role |
|---|---|
| `/usr/local/sbin/truenas-nfs-ready.sh` | wait for VM 100 to start and NFSv3 RPC to respond (up to 900 seconds, every 5 seconds) |
| `/etc/systemd/system/truenas-nfs-ready.service` | run the script above as a oneshot |
| `/etc/systemd/system/mnt-pve-backup.mount.d/10-truenas-readiness.conf` | order the mount after the service above (`Requires`, `After`) |

> **Run on: pve**

```bash
BACKUP_DIR="/root/nfs-config-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "===== BACKUP EXISTING CONFIGURATION ====="
for f in \
  /etc/systemd/system/mnt-pve-backup.mount \
  /etc/systemd/system/mnt-pve-backup.mount.d/10-truenas-readiness.conf \
  /etc/systemd/system/truenas-nfs-ready.service \
  /usr/local/sbin/truenas-nfs-ready.sh
do
  if [ -e "$f" ]; then
    cp -a --parents "$f" "$BACKUP_DIR/"
    echo "BACKED_UP: $f"
  else
    echo "NOT_EXISTED: $f"
  fi
done
echo "BACKUP_DIR=$BACKUP_DIR"

echo
echo "===== INSTALL READINESS SCRIPT ====="
cat > /usr/local/sbin/truenas-nfs-ready.sh <<'EOF'
#!/bin/bash

TRUENAS_IP="192.168.0.254"
VMID="100"
TIMEOUT_SECONDS=900
INTERVAL_SECONDS=5
DEADLINE=$(( $(date +%s) + TIMEOUT_SECONDS ))

echo "Waiting for TrueNAS VM ${VMID} and NFSv3 readiness."

while [ "$(date +%s)" -lt "$DEADLINE" ]; do
    VM_STATUS="$(qm status "$VMID" 2>/dev/null)"

    if [[ "$VM_STATUS" == *"status: running"* ]]; then
        echo "TrueNAS VM ${VMID} is running."

        if timeout 5 rpcinfo -t "$TRUENAS_IP" 100005 3 >/dev/null 2>&1 &&
           timeout 5 rpcinfo -t "$TRUENAS_IP" 100003 3 >/dev/null 2>&1; then
            echo "TrueNAS NFSv3 mountd and NFS RPC are ready."
            exit 0
        fi

        echo "NFSv3 RPC services are not ready yet."
    else
        echo "Waiting for TrueNAS VM ${VMID}: ${VM_STATUS:-status unavailable}"
    fi

    sleep "$INTERVAL_SECONDS"
done

echo "ERROR: TrueNAS/NFSv3 readiness timeout after ${TIMEOUT_SECONDS}s." >&2
exit 1
EOF
chmod 0755 /usr/local/sbin/truenas-nfs-ready.sh

echo
echo "===== INSTALL SYSTEMD READINESS SERVICE ====="
cat > /etc/systemd/system/truenas-nfs-ready.service <<'EOF'
[Unit]
Description=Wait for TrueNAS VM and NFSv3 readiness
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/truenas-nfs-ready.sh
TimeoutStartSec=16min
EOF

echo
echo "===== INSTALL NFS MOUNT DEPENDENCY ====="
mkdir -p /etc/systemd/system/mnt-pve-backup.mount.d
cat > /etc/systemd/system/mnt-pve-backup.mount.d/10-truenas-readiness.conf <<'EOF'
[Unit]
Requires=truenas-nfs-ready.service
After=truenas-nfs-ready.service
EOF

echo
echo "===== SCRIPT SYNTAX CHECK ====="
bash -n /usr/local/sbin/truenas-nfs-ready.sh
echo "BASH_SYNTAX_EXIT=$?"

echo
echo "===== RELOAD SYSTEMD ====="
systemctl daemon-reload
echo "DAEMON_RELOAD_EXIT=$?"

echo
echo "===== VERIFY SYSTEMD UNIT FILES ====="
systemd-analyze verify \
  /etc/systemd/system/truenas-nfs-ready.service \
  /etc/systemd/system/mnt-pve-backup.mount

echo
echo "===== VERIFY MOUNT DEPENDENCIES ====="
systemctl show mnt-pve-backup.mount -p Requires -p After -p Wants
systemctl show truenas-nfs-ready.service -p Type -p TimeoutStartUSec -p ExecStart

echo
echo "===== VERIFY INSTALLED FILES ====="
ls -l \
  /usr/local/sbin/truenas-nfs-ready.sh \
  /etc/systemd/system/truenas-nfs-ready.service \
  /etc/systemd/system/mnt-pve-backup.mount.d/10-truenas-readiness.conf
```

The syntax check and the dependency update worked, but `cp --parents` failed in the initial backup step, so we could not confirm that a copy of the original mount settings had been made (the original settings were not changed).

### 3.2 Saving the Original Settings and Testing the Script

Save the original mount settings reliably under another name and run the wait script without mounting.

> **Run on: pve**

```bash
BACKUP_DIR="/root/nfs-config-backup-20261123-091709"

echo "===== CREATE VERIFIED BACKUP OF ORIGINAL MOUNT UNIT ====="
install -D -m 0644 \
  /etc/systemd/system/mnt-pve-backup.mount \
  "$BACKUP_DIR/original-mnt-pve-backup.mount"

cmp -s \
  /etc/systemd/system/mnt-pve-backup.mount \
  "$BACKUP_DIR/original-mnt-pve-backup.mount"
echo "ORIGINAL_CONFIG_BACKUP_MATCH=$?"

echo
echo "===== VERIFY ORIGINAL MOUNT CONFIGURATION ====="
cat "$BACKUP_DIR/original-mnt-pve-backup.mount"

echo
echo "===== VERIFY READINESS SCRIPT CONTENT ====="
sed -n '1,200p' /usr/local/sbin/truenas-nfs-ready.sh

echo
echo "===== VERIFY SYSTEMD CONFIGURATION SYNTAX ====="
systemd-analyze verify \
  /etc/systemd/system/truenas-nfs-ready.service \
  /etc/systemd/system/mnt-pve-backup.mount
echo "SYSTEMD_VERIFY_EXIT=$?"

echo
echo "===== RUN READINESS CHECK ONLY (NO MOUNT) ====="
 /usr/local/sbin/truenas-nfs-ready.sh
echo "READINESS_CHECK_EXIT=$?"

echo
echo "===== VERIFY BACKUP FILE ====="
ls -l "$BACKUP_DIR/original-mnt-pve-backup.mount"
sha256sum \
  "$BACKUP_DIR/original-mnt-pve-backup.mount" \
  /etc/systemd/system/mnt-pve-backup.mount
```

| Checked | Result |
|---|---|
| Copy of the original mount settings | SHA256 matches |
| `systemd-analyze verify` | `0` |
| Wait script | `0` |
| TrueNAS VM 100 | running |
| NFSv3 mountd and NFS RPC | both respond |

### 3.3 Testing the Mount

Mount once through systemd and test writing, reading and deleting. The backup job is not run.

> **Run on: pve**

```bash
echo "===== PRE-MOUNT SAFETY CHECK ====="
findmnt -T /mnt/pve/backup
mountpoint -q /mnt/pve/backup
echo "ALREADY_MOUNTED=$?"

echo
echo "===== CHECK STORAGE ACTIVATION BEFORE MOUNT ====="
pvesm status --storage truenas-backup

echo
echo "===== START NFS MOUNT THROUGH SYSTEMD ====="
systemctl start mnt-pve-backup.mount
MOUNT_EXIT=$?
echo "MOUNT_START_EXIT=$MOUNT_EXIT"

echo
echo "===== VERIFY ACTUAL MOUNT SOURCE ====="
findmnt -T /mnt/pve/backup -o TARGET,SOURCE,FSTYPE,OPTIONS
mountpoint -q /mnt/pve/backup
echo "IS_MOUNTPOINT=$?"

echo
echo "===== VERIFY NFS STORAGE STATUS ====="
pvesm status --storage truenas-backup

echo
echo "===== VERIFY READ AND WRITE ACCESS ====="
if mountpoint -q /mnt/pve/backup; then
  TEST_FILE="/mnt/pve/backup/.pve-nfs-write-test-$(date +%s)"
  if printf 'PVE NFS write test\n' > "$TEST_FILE"; then
    echo "WRITE_TEST=PASS"
    cat "$TEST_FILE"
    rm -f "$TEST_FILE"
    echo "READ_DELETE_TEST=PASS"
  else
    echo "WRITE_TEST=FAIL"
  fi
else
  echo "NFS_NOT_MOUNTED: write test skipped"
fi

echo
echo "===== FINAL MOUNT UNIT STATUS ====="
systemctl status mnt-pve-backup.mount --no-pager -l
```

| Checked | Result |
|---|---|
| Mount through systemd | `0` |
| Connected to | `192.168.0.254:/mnt/backup` (NFSv3, TCP) |
| `truenas-backup` | `active` |
| Write, read, delete | all succeeded |
| Wait service | finished normally |

### 3.4 Effect on the November 23 Backups

> **Run on: pve**

```bash
echo "===== NFS MOUNT CONFIRMATION ====="
findmnt -T /mnt/pve/backup -o TARGET,SOURCE,FSTYPE,OPTIONS

echo
echo "===== POSTGRESQL BACKUP SCRIPT ====="
sed -n '1,260p' /usr/local/sbin/pg-logical-backup.sh

echo
echo "===== POSTGRESQL DAILY BACKUP DIRECTORIES ====="
find /mnt/pve/backup/postgresql/daily \
  -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>&1 | sort

echo
echo "===== NOVEMBER 23 POSTGRESQL BACKUP FILES ====="
if [ -d /mnt/pve/backup/postgresql/daily/2026-11-23 ]; then
  find /mnt/pve/backup/postgresql/daily/2026-11-23 \
    -maxdepth 2 -type f -printf '%P %s bytes\n' | sort
else
  echo "2026-11-23 DAILY DIRECTORY NOT FOUND"
fi

echo
echo "===== POSTGRESQL BACKUP MANIFESTS ====="
find /mnt/pve/backup/postgresql/daily/2026-11-23 \
  -maxdepth 2 -type f \( -iname '*sha256*' -o -iname '*manifest*' -o -iname '*metadata*' \) \
  -print 2>&1

echo
echo "===== LXC109 BACKUP ARCHIVES ====="
find /mnt/pve/backup/dump \
  -maxdepth 1 -type f -name 'vzdump-lxc-109-*' \
  -printf '%f %s bytes\n' 2>&1 | sort

echo
echo "===== LXC109 TEMPORARY FILES ====="
find /mnt/pve/backup/dump \
  -maxdepth 1 -name 'vzdump-lxc-109-*.tmp' \
  -printf '%f %s bytes\n' 2>&1

echo
echo "===== LATEST LXC109 BACKUP TASK LOG ====="
pvenode task log 'UPID:pve:0010D698:00B3FB4F:6B032DA9:vzdump:109:root@pam:' 2>&1 | tail -60

echo
echo "===== TRUE NAS BACKUP DATASET SNAPSHOTS ====="
zfs list -t snapshot -o name,creation \
  | grep '^backup@' | sort
```

```bash
BACKUP_DIR="/mnt/pve/backup/postgresql/daily/2026-11-23"

echo "===== VERIFY POSTGRESQL BACKUP CHECKSUMS ====="
cd "$BACKUP_DIR" && sha256sum -c SHA256SUMS
CHECKSUM_EXIT=$?
echo "CHECKSUM_EXIT=$CHECKSUM_EXIT"

echo
echo "===== COUNT DATABASE DUMP FILES ====="
find "$BACKUP_DIR" -maxdepth 1 -type f -name '*.dump' | wc -l

echo
echo "===== CHECK BACKUP FILES FOR ZERO SIZE ====="
find "$BACKUP_DIR" -maxdepth 1 -type f -size 0 -printf '%f\n'

echo
echo "===== POSTGRESQL BACKUP SERVICE RESULT ====="
journalctl -u pg-logical-backup.service \
  --since "2026-11-23 00:00:00" \
  --until "2026-11-23 23:59:59" \
  --no-pager -o short-iso | tail -100
```

- For PostgreSQL on November 23, the 17 dumps and `SHA256SUMS` exist, all checksums are `OK`, and there are no zero-byte files. It finished normally at 02:01:03
- The 03:00 LXC 109 backup had failed. The temporary snapshot is gone and no `.tmp` remains. The successful archive from November 22 is still there

Putting the times side by side, the LXC 109 failure was at 03:00 and the reboot at 06:50. **The 03:00 failure cannot be explained by the NFS mount failure.** We investigate it as a separate cause.

## Chapter 4: Why the LXC 109 Backup Failed

### 4.1 Differences from the Previous Success

> **Run on: pve**

```bash
echo "===== NFS MOUNT OPTIONS ====="
findmnt -T /mnt/pve/backup -o TARGET,SOURCE,FSTYPE,OPTIONS

echo
echo "===== BACKUP DIRECTORY PERMISSIONS ====="
namei -l /mnt/pve/backup/dump

echo
echo "===== BACKUP DIRECTORY METADATA ====="
stat -c '%A %a %U:%G uid=%u gid=%g %n' \
  /mnt/pve/backup \
  /mnt/pve/backup/dump

echo
echo "===== ACL OF BACKUP DIRECTORIES ====="
if command -v getfacl >/dev/null 2>&1; then
  getfacl -p /mnt/pve/backup /mnt/pve/backup/dump
else
  echo "getfacl command not installed"
fi

echo
echo "===== PREVIOUS SUCCESSFUL LXC109 BACKUP LOG ====="
cat /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.log

echo
echo "===== FAILED LXC109 BACKUP LOG ====="
cat /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_23-03_00_09.log

echo
echo "===== LXC109 CONFIGURATION (READ ONLY) ====="
pct config 109 | grep -E '^(unprivileged|rootfs|mp[0-9]+|features):'

echo
echo "===== NFS EXPORT VISIBILITY ====="
showmount -e 192.168.0.254
```

The log shows the backup's `tar` running in the following user namespace.

```text
lxc-usernsexec
u:0:100000:65536
g:0:100000:65536
```

LXC 109 is an unprivileged container (`unprivileged: 1`), so root inside the container is UID/GID `100000` on the host. Meanwhile, the NFS `dump/` had been set as follows in Part 42.

```text
drwx------ 700 root:root /mnt/pve/backup/dump
```

### 4.2 Can UID 100000 Write?

Without changing permissions, test whether a temporary file can be created as UID/GID `100000:100000`.

> **Run on: pve**

```bash
echo "===== UID/GID 100000 WRITE ACCESS TEST ====="
TEST_FILE="/mnt/pve/backup/dump/.uid100000-write-test-$(date +%s)"

setpriv --reuid=100000 --regid=100000 --clear-groups \
  -- sh -c 'umask 077; printf "UID 100000 NFS permission test\n" > "$1"' \
  sh "$TEST_FILE"
WRITE_EXIT=$?

echo "UID100000_WRITE_EXIT=$WRITE_EXIT"

if [ "$WRITE_EXIT" -eq 0 ]; then
  echo "===== TEST FILE OWNER ====="
  stat -c '%A %a %U:%G uid=%u gid=%g %n' "$TEST_FILE"

  echo
  echo "===== REMOVE TEST FILE ====="
  rm -f "$TEST_FILE"
  echo "TEST_FILE_REMOVED=$?"
else
  echo "UID 100000 cannot create a file in the dump directory."
fi

echo
echo "===== DUMP DIRECTORY TIMESTAMPS ====="
stat -c 'birth=%w modify=%y change=%z access=%x %n' \
  /mnt/pve/backup/dump

echo
echo "===== NFS4 ACL TOOL AVAILABILITY ====="
if command -v nfs4_getfacl >/dev/null 2>&1; then
  nfs4_getfacl /mnt/pve/backup/dump
else
  echo "nfs4_getfacl is not installed"
fi

echo
echo "===== VERIFY EXISTING BACKUP ARCHIVE REMAINS ====="
stat -c '%A %a %U:%G %s bytes %n' \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst
```

It gave `cannot create`, confirming that UID 100000 cannot enter `dump/`.

### 4.3 TrueNAS ACLs and the NFS Share

In TrueNAS CORE 12, ACLs are retrieved with a POST call. This is read-only; the ACLs are not changed.

> **Run on: pve**

```bash
echo "===== TRUENAS ACL: BACKUP DATASET ROOT (POST) ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 20 \
  --user root \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"path":"/mnt/backup"}' \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  'https://192.168.0.254/api/v2.0/filesystem/getacl'

echo
echo "===== TRUENAS ACL: DUMP DIRECTORY (POST) ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 20 \
  --user root \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"path":"/mnt/backup/dump"}' \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  'https://192.168.0.254/api/v2.0/filesystem/getacl'
```

Both `/mnt/backup` and `/mnt/backup/dump` are `acltype: NFS4` with owner `0:0`. `dump` gives no permission to traverse the directory (`EXECUTE`) to anyone other than owner@.

> **Run on: pve**

```bash
echo "===== FETCH TRUENAS NFS SHARES ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 20 \
  --user root \
  -o /tmp/truenas-nfs-shares.json \
  -w 'HTTP_STATUS=%{http_code}\nCONTENT_TYPE=%{content_type}\n' \
  'https://192.168.0.254/api/v2.0/sharing/nfs'

echo
echo "===== PARSE NFS SHARE CONFIGURATION ====="
python3 - <<'PY'
import json
from pathlib import Path

p = Path("/tmp/truenas-nfs-shares.json")
try:
    data = json.loads(p.read_text())
    print("RESPONSE_TYPE:", type(data).__name__)
    if isinstance(data, list):
        print("SHARE_COUNT:", len(data))
        for item in data:
            if "/mnt/backup" in str(item.get("path", "")):
                print(json.dumps(item, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print("JSON_PARSE_ERROR:", e)
    print(p.read_text(errors="replace")[:4000])
PY

echo
echo "===== VERIFY NFS EXPORT ====="
showmount -e 192.168.0.254

echo
echo "===== CURRENT DUMP DIRECTORY PERMISSIONS ====="
stat -c '%A %a %U:%G uid=%u gid=%g %n' /mnt/pve/backup/dump
```

```bash
echo "===== RAW TRUENAS NFS SHARE JSON ====="
python3 -m json.tool /tmp/truenas-nfs-shares.json

echo
echo "===== TOP-LEVEL KEYS AND PATH VALUES ====="
python3 - <<'PY'
import json
with open("/tmp/truenas-nfs-shares.json") as f:
    data = json.load(f)

for i, item in enumerate(data):
    print(f"ITEM {i}:")
    print("TYPE:", type(item).__name__)
    if isinstance(item, dict):
        print("KEYS:", list(item.keys()))
        for key, value in item.items():
            if "path" in key.lower() or "map" in key.lower() or "security" in key.lower():
                print(f"{key} = {value!r}")
PY
```

The NFS share has `maproot_user = root` (only the client's UID 0 is mapped to root on the server), and `mapall_user` is empty. UID 100000 is not treated as root.

### 4.4 The Log of the Failure

> **Run on: pve**

```bash
echo "===== FAILED LXC109 BACKUP LOG ====="
grep -R -n -C 8 \
  '2026_11_23-03_00_09\|Cannot open: Permission denied\|vzdump-lxc-109' \
  /var/log/vzdump \
  /var/log/pve \
  2>/dev/null | tail -180

echo
echo "===== LXC ARCHIVE CALLER ====="
grep -n -C 10 -E '->archive\(|archive\(\$task|tmptar|target\}' \
  /usr/share/perl5/PVE/VZDump.pm \
  /usr/share/perl5/PVE/VZDump/LXC.pm 2>/dev/null | head -220

echo
echo "===== VZDUMP ARCHIVE PIPELINE ====="
grep -n -C 8 -E 'compress|tmptar|rename|target.*tmp|file.*target' \
  /usr/share/perl5/PVE/VZDump.pm | tail -220
```

The log showed that what failed was not the destination of the archive but the **temporary directory** that `tar` reads.

```text
--directory=/mnt/pve/backup/dump/vzdump-lxc-109-2026_11_23-03_00_09.tmp
...
tar: /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_23-03_00_09.tmp: Cannot open: Permission denied
```

Proxmox runs the `tar` that reads an unprivileged LXC's files inside a namespace with UID/GID 100000. The temporary directory is created under the destination `dump/`, and because `dump/` is root-only `0700`, UID 100000 cannot reach it. The final archive (`.tar.dat`), by contrast, is the output of a pipe opened by root on the host, so it is not a problem.

Therefore there is no need to change TrueNAS ownership, ACLs or the NFS share. **It is enough to put just the temporary directory on a local disk.**

### 4.5 Can the Temporary Directory Be Set per Job?

> **Run on: pve**

```bash
echo "===== TMPDIR PARAMETER DEFINITION ====="
sed -n '225,265p' /usr/share/perl5/PVE/VZDump/Common.pm

echo
echo "===== VZDUMP JOB API SCHEMA ====="
grep -R -n -C 5 -E 'tmpdir|job.*param|prune-backups|schedule' \
  /usr/share/perl5/PVE/API2/VZDump.pm \
  /usr/share/perl5/PVE/Jobs \
  2>/dev/null | head -240

echo
echo "===== LOCAL TMP DIRECTORY ====="
stat -c '%A %a %U:%G %n' /var/tmp
findmnt -T /var/tmp
df -h /var/tmp
```

`/var/tmp` is on Proxmox's local ext4 with about 66GB free. The temporary directory mainly holds the LXC's configuration files, so it does not need space for the backup data itself.

> **Run on: pve**

```bash
echo "===== BACKUP JOB UPDATE API ====="
sed -n '344,475p' /usr/share/perl5/PVE/API2/Backup.pm

echo
echo "===== JOB CONFIG PROPERTY INHERITANCE ====="
grep -n -A 45 -B 8 'sub json_config_properties' \
  /usr/share/perl5/PVE/VZDump/Common.pm

echo
echo "===== STORAGE CONFIGURATION ====="
cat /etc/pve/storage.cfg

echo
echo "===== CURRENT JOB DETAILS ====="
pvesh get /cluster/backup/lxc109-daily --output-format json-pretty
```

We confirmed that the backup job update API (`update_job`) takes `tmpdir` from the common settings (`json_config_properties()`), so **`tmpdir` can be set per job**. We can change only `lxc109-daily` without making it a global setting in `/etc/vzdump.conf`.

## Chapter 5: Making the Job's Temporary Directory Local

### 5.1 What We Change

```text
Target job: lxc109-daily
Changed item: tmpdir
Value: /var/tmp
```

### 5.2 Setting It

Save `/etc/pve/jobs.cfg` before the change, set the value, and confirm it through both the API and the configuration file. No backup is run.

> **Run on: pve**

```bash
echo "===== BACKUP CURRENT JOB CONFIGURATION ====="
BACKUP_DIR="/root/lxc109-job-config-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

if cp -a /etc/pve/jobs.cfg "$BACKUP_DIR/jobs.cfg"; then
    sha256sum /etc/pve/jobs.cfg "$BACKUP_DIR/jobs.cfg"
    echo "CONFIG_BACKUP=$BACKUP_DIR/jobs.cfg"
else
    echo "ERROR: Configuration backup failed. No changes made."
fi

if [ -f "$BACKUP_DIR/jobs.cfg" ]; then
    echo
    echo "===== APPLY TMPDIR TO LXC109 JOB ONLY ====="
    pvesh set /cluster/backup/lxc109-daily --tmpdir /var/tmp
    UPDATE_EXIT=$?
    echo "UPDATE_EXIT=$UPDATE_EXIT"

    if [ "$UPDATE_EXIT" -eq 0 ]; then
        echo
        echo "===== VERIFY JOB THROUGH API ====="
        pvesh get /cluster/backup/lxc109-daily --output-format json-pretty

        echo
        echo "===== VERIFY PERSISTED JOB CONFIG ====="
        grep -A 16 '^vzdump: lxc109-daily' /etc/pve/jobs.cfg
    fi
fi
```

- `/etc/pve/jobs.cfg` before the change was saved (SHA256 matches)
- The API response contains `"tmpdir": "/var/tmp"`
- `tmpdir /var/tmp` was written to `/etc/pve/jobs.cfg`
- Schedule, compression, destination, generations and target CTID are unchanged

### 5.3 Can the Namespace Read `/var/tmp`?

> **Run on: pve**

```bash
echo "===== LOCAL TMPDIR NAMESPACE ACCESS TEST ====="
TEST_DIR="$(mktemp -d /var/tmp/lxc109-tmpdir-check.XXXXXX)"
TEST_FILE="$TEST_DIR/metadata-test"

if [ -d "$TEST_DIR" ]; then
    chmod 755 "$TEST_DIR"
    printf 'LXC109 temporary metadata access test\n' > "$TEST_FILE"
    chmod 644 "$TEST_FILE"

    echo "--- Host permissions ---"
    stat -c '%A %a %U:%G %n' "$TEST_DIR" "$TEST_FILE"

    echo
    echo "--- Read test from LXC unprivileged user namespace ---"
    lxc-usernsexec \
      -m u:0:100000:65536 \
      -m g:0:100000:65536 \
      -- sh -c 'test -r "$1" && cat "$1"' sh "$TEST_FILE"
    TEST_EXIT=$?
    echo "NAMESPACE_READ_EXIT=$TEST_EXIT"

    rm -f "$TEST_FILE"
    rmdir "$TEST_DIR"
    echo "TEST_CLEANUP=completed"
else
    echo "ERROR: Could not create local test directory."
fi

echo
echo "===== VERIFY JOB SETTINGS AGAIN ====="
pvesh get /cluster/backup/lxc109-daily --output-format json-pretty

echo
echo "===== VERIFY NO BACKUP WAS STARTED BY THIS CHECK ====="
pgrep -af 'vzdump.*109' || echo "No matching vzdump process found."
```

From the unprivileged LXC's namespace, a file in a temporary directory under `/var/tmp` could be read. The test file was removed and no backup ran.

The current backup configuration is as follows.

```text
Target: LXC 109 (PostgreSQL)
Mode: snapshot
Compression: zstd

Temporary directory:
  /var/tmp              ← PVE local

Final destination:
  /mnt/pve/backup/dump  ← TrueNAS NFS

Schedule:
  Daily 03:00

Generations:
  daily   7
  weekly  4
  monthly 3
```

> **Caution:** The configuration list above is for explanation and is not a command. Pasting it into a shell gives `command not found` (no settings or data are harmed).

### 5.4 Running the Backup Again

Run it once with the same destination and mode as the scheduled job, with `/var/tmp` as the temporary directory, and then check the compression integrity of the archive. Existing generations are not deleted.

> **Run on: pve**

```bash
echo "===== PRE-BACKUP SAFETY CHECK ====="

if ! mountpoint -q /mnt/pve/backup; then
    echo "ERROR: TrueNAS backup mount is not mounted. Backup skipped."
else
    findmnt -T /mnt/pve/backup
    pvesm status --storage truenas-backup

    if pgrep -x vzdump >/dev/null 2>&1; then
        echo "ERROR: Another vzdump process is running. Backup skipped."
    else
        echo
        echo "===== START LXC109 BACKUP ====="
        START_TIME="$(date '+%Y-%m-%d %H:%M:%S')"
        START_EPOCH="$(date +%s)"

        vzdump 109 \
          --storage truenas-backup \
          --mode snapshot \
          --compress zstd \
          --tmpdir /var/tmp

        BACKUP_EXIT=$?
        echo "BACKUP_EXIT=$BACKUP_EXIT"

        echo
        echo "===== NEW ARCHIVE CHECK ====="
        ARCHIVE="$(find /mnt/pve/backup/dump \
          -maxdepth 1 -type f \
          -name 'vzdump-lxc-109-*.tar.zst' \
          -newermt "@$START_EPOCH" \
          -printf '%T@ %p\n' 2>/dev/null |
          sort -nr | head -1 | cut -d' ' -f2-)"

        if [ -n "$ARCHIVE" ]; then
            echo "ARCHIVE=$ARCHIVE"
            ls -lh "$ARCHIVE"

            echo
            echo "===== ZSTD INTEGRITY TEST ====="
            zstd -t "$ARCHIVE"
            echo "ZSTD_TEST_EXIT=$?"
        else
            echo "No new LXC109 archive found."
        fi

        echo
        echo "===== BACKUP LOGS ====="
        find /var/log/vzdump -maxdepth 1 -type f \
          -newermt "@$START_EPOCH" -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' \
          2>/dev/null | sort
    fi
fi
```

| Item | Result |
|---|---|
| Run at | 2026-11-23 09:43:34 |
| Temporary directory | `/var/tmp` |
| Duration | 20 seconds |
| Exit code | `0` |
| Archive | `vzdump-lxc-109-2026_11_23-09_43_34.tar.zst` (about 473MiB) |
| zstd integrity | `ZSTD_TEST_EXIT=0` |

### 5.5 Checking the Contents and Cleanup

> **Run on: pve**

```bash
ARCHIVE="/mnt/pve/backup/dump/vzdump-lxc-109-2026_11_23-09_43_34.tar.zst"
LOG="/var/log/vzdump/lxc-109.log"

echo "===== VERIFY ARCHIVE CONTENTS ====="
tar --use-compress-program=unzstd -tf "$ARCHIVE" | sed -n '1,30p'
TAR_LIST_EXIT=${PIPESTATUS[0]}
echo "TAR_LIST_EXIT=$TAR_LIST_EXIT"

echo
echo "===== VERIFY BACKUP LOG ====="
grep -nE '09:43:34|09:43:54|tmpdir|archive file size|Finished Backup|successfully' "$LOG" | tail -60

echo
echo "===== VERIFY TEMPORARY ARTIFACTS ====="
find /mnt/pve/backup/dump -maxdepth 1 \
  \( -name 'vzdump-lxc-109-2026_11_23-09_43_34.tmp' \
     -o -name 'vzdump-lxc-109-2026_11_23-09_43_34.tar.dat' \) \
  -print

echo
echo "===== VERIFY FINAL ARCHIVE ====="
stat -c 'FILE=%n SIZE=%s bytes MODE=%a OWNER=%U:%G' "$ARCHIVE"
```

| Checked | Result |
|---|---|
| tar listing | `TAR_LIST_EXIT=0` |
| Log | finished normally |
| Temporary files | none left |
| Archive | `root:root`, 495,748,185 bytes |

We also confirmed that the archive contains `./etc/vzdump/pct.conf`, `./etc/vzdump/pct.fw`, Wazuh-related data under `./var/ossec/`, and the root file system of the PostgreSQL container.

## Closing Notes

In Part 43 we fixed the two backup problems found on November 23.

| Item | Result |
|---|---|
| PostgreSQL 02:00 backup | succeeded (17 databases, checksums `OK`) |
| NFS after a reboot | `truenas-nfs-ready.service` now waits for TrueNAS VM 100 to start and NFSv3 to respond before mounting. Mount test passed |
| LXC 109 03:00 backup | Cause: the UID 100000 `tar` cannot reach a temporary directory on NFS. Set `tmpdir: /var/tmp` on the job; re-run succeeded |
| TrueNAS ownership, ACLs, NFS share | unchanged |
| Other issues | the `windows_d/windows_d` VG error and the thin pool capacity warning (settings unchanged) |

In the next part, Part 44, we check that Proxmox recognizes the backups correctly and compare the restored databases with production in detail.

# Part 44: Comparing the Restored Databases with Production
## Introduction

### About This Book

This is Part 44 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual", and the last part of Volume 3. In Part 43 we fixed the NFS mount after a reboot and the LXC 109 backup failure. Here we check that the backup system works correctly as a whole, and compare the databases of CTID 310, restored in Part 41, in detail with the production CTID 109.

1. Check that Proxmox recognizes the backups as official backups, and that the job and the boot dependencies are still in place
2. Check the state of CTID 310 (used for the restore test) and the thin pool
3. Start CTID 310 with its network cut off and check PostgreSQL
4. Compare the tables, views, indexes, constraints, extensions and schema definitions of the 17 databases with CTID 109

No data, settings or services are changed or restarted. Everything is read-only.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)

## Chapter 1: Checking the Backup System

### 1.1 Catalog, Job and Boot Dependencies

> **Run on: pve**

```bash
echo "===== PVE BACKUP CATALOG ====="
pvesm list truenas-backup --content backup --vmid 109

echo
echo "===== LXC109 SCHEDULED JOB ====="
pvesh get /cluster/backup/lxc109-daily --output-format json-pretty

echo
echo "===== NFS MOUNT READINESS DEPENDENCY ====="
systemctl show mnt-pve-backup.mount \
  -p LoadState \
  -p ActiveState \
  -p SubState \
  -p Requires \
  -p After

echo
echo "===== TRUENAS READINESS SERVICE ====="
systemctl show truenas-nfs-ready.service \
  -p LoadState \
  -p ActiveState \
  -p SubState

echo
echo "===== BACKUP ARCHIVE AND LOG ====="
ls -lh \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_23-09_43_34.tar.zst \
  /var/log/vzdump/lxc-109.log
```

| Item | Result |
|---|---|
| Backup catalog | two generations of LXC 109 registered (November 22 20:28, November 23 09:43) |
| `lxc109-daily` | daily 03:00, snapshot, zstd, `truenas-backup`, 7 daily, 4 weekly, 3 monthly, `/var/tmp`, enabled |
| `mnt-pve-backup.mount` | `Requires=truenas-nfs-ready.service`, `After=truenas-nfs-ready.service` |
| `truenas-nfs-ready.service` | `inactive/dead` (a oneshot service that finished normally) |

The archives are not only on NFS but are also registered in Proxmox's backup catalog.

### 1.2 Restore Method and Settings Inside the Archive

> **Run on: pve**

```bash
echo "===== PCT RESTORE OPTIONS ====="
pct help restore

echo
echo "===== BACKUP ARCHIVE CONTAINER CONFIG ====="
tar --use-compress-program=unzstd \
  -xOf /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_23-09_43_34.tar.zst \
  ./etc/vzdump/pct.conf

echo
echo "===== STORAGE STATUS ====="
pvesm status

echo
echo "===== EXISTING CONTAINER 109 CONFIG ====="
pct config 109
```

The settings recorded in the archive were the same as the current CT109 (Debian, amd64, 2 vCPUs, 4GB memory, 50GB root disk, unprivileged, `nesting=1,keyctl=1`, `192.168.0.151/24`, `onboot=1`). We check with a different CTID without overwriting the production CT109.

### 1.3 CTID 310 and the Thin Pool

> **Run on: pve**

```bash
echo "===== PVE THIN POOL STATUS ====="
lvs -a -o vg_name,lv_name,lv_size,lv_attr,pool_lv,data_percent,metadata_percent pve

echo
echo "===== LOCAL-LVM POOL ONLY ====="
lvs -o vg_name,lv_name,lv_size,lv_attr,data_percent,metadata_percent pve/data

echo
echo "===== CT310 DISK VOLUME ====="
lvs -a | grep -E 'vm-310|snap_vm-310|LV'

echo
echo "===== CT109 DISK VOLUME ====="
lvs -a | grep -E 'vm-109|snap_vm-109|LV'

echo
echo "===== CT310 AND CT109 STATUS ====="
pct status 310
pct status 109
```

| Item | State |
|---|---|
| `pve/data` | 794.30GiB, data usage 61.90%, metadata 2.19% |
| Unallocated space in the VG | 16GiB |
| CTID 310 | stopped. rootfs `local-lvm:vm-310-disk-0` (50GB, 5.47% used), `link_down=1`, `onboot=0` |
| CTID 109 | running |

CTID 310, restored in Part 41, is still there with its network cut off. We use it instead of creating a new restore target.

## Chapter 2: Starting and Checking CTID 310

### 2.1 Starting It with the Network Cut Off

> **Run on: pve**

```bash
echo "===== VERIFY CT310 IS STOPPED ====="
pct status 310

echo
echo "===== VERIFY NETWORK IS DISCONNECTED ====="
pct config 310 | grep -E '^(net[0-9]+|onboot|rootfs):'

echo
echo "===== START RESTORE TEST CONTAINER CT310 ====="
pct start 310
START_EXIT=$?
echo "START_EXIT=$START_EXIT"

echo
echo "===== VERIFY CT310 STATUS ====="
pct status 310

echo
echo "===== VERIFY CT109 REMAINS RUNNING ====="
pct status 109

echo
echo "===== VERIFY CT310 NETWORK CONFIGURATION ====="
pct config 310 | grep -E '^(net[0-9]+|onboot|rootfs):'
```

CTID 310 is `running`, the production CTID 109 is also `running`, and CTID 310 remains `link_down=1`, `onboot=0`.

### 2.2 PostgreSQL State

> **Run on: pve**

```bash
echo "===== CT310 POSTGRESQL SERVICE STATUS ====="
pct exec 310 -- systemctl status postgresql --no-pager

echo
echo "===== POSTGRESQL CLUSTER LIST ====="
pct exec 310 -- pg_lsclusters

echo
echo "===== POSTGRESQL LOCAL READINESS ====="
pct exec 310 -- pg_isready -h 127.0.0.1

echo
echo "===== POSTGRESQL LISTENING SOCKETS ====="
pct exec 310 -- ss -lntp

echo
echo "===== CT310 NETWORK INTERFACES ====="
pct exec 310 -- ip -brief address

echo
echo "===== CT310 NETWORK ROUTES ====="
pct exec 310 -- ip route
```

PostgreSQL 17 `main` is `online` and accepts connections on `127.0.0.1:5432`; `eth0` is `DOWN` and there are no routes. PostgreSQL also listens on `0.0.0.0:5432` and `[::]:5432`, but the virtual NIC is disconnected, so nothing reaches it from outside. We keep this isolation during the checks.

### 2.3 List of Databases

> **Run on: pve**

```bash
echo "===== POSTGRESQL VERSION ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -c "SELECT version();"

echo
echo "===== DATABASE INVENTORY ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -c "
SELECT
    datname AS database_name,
    pg_size_pretty(pg_database_size(datname)) AS database_size,
    datallowconn AS connections_allowed
FROM pg_database
WHERE datistemplate = false
ORDER BY datname;
"

echo
echo "===== USER TABLE COUNTS BY DATABASE ====="
pct exec 310 -- bash -c '
for db in $(runuser -u postgres -- psql -X -At -d postgres -c "SELECT datname FROM pg_database WHERE datistemplate = false AND datallowconn = true ORDER BY datname"); do
    echo "--- DATABASE: $db ---"
    runuser -u postgres -- psql -X -d "$db" -c "
    SELECT
        count(*) FILTER (WHERE table_type = '\''BASE TABLE'\'') AS base_tables,
        count(*) FILTER (WHERE table_type = '\''VIEW'\'') AS views
    FROM information_schema.tables
    WHERE table_schema NOT IN ('\''pg_catalog'\'', '\''information_schema'\'');
    "
done
'

echo
echo "===== DATABASE RECOVERY STATUS ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -c "
SELECT
    pg_is_in_recovery() AS in_recovery,
    current_setting('data_directory') AS data_directory,
    current_setting('server_version') AS server_version;
"
```

PostgreSQL 17.11, cluster `17/main` `online`, 17 databases, and `pg_is_in_recovery()` was `false`. `postgresql.service` being `active (exited)` is normal for Debian's management service.

### 2.4 Owners, Extensions, Indexes and Logs

> **Run on: pve**

```bash
echo "===== DATABASE OWNERS ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -c "
SELECT datname, pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datistemplate = false
ORDER BY datname;
"

echo
echo "===== POSTGRESQL ROLES ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -c "
SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolcanlogin
FROM pg_roles
WHERE rolname !~ '^pg_'
ORDER BY rolname;
"

echo
echo "===== INSTALLED EXTENSIONS BY DATABASE ====="
pct exec 310 -- bash -c '
for db in $(runuser -u postgres -- psql -X -At -d postgres -c "SELECT datname FROM pg_database WHERE datistemplate = false AND datallowconn = true ORDER BY datname"); do
    echo "--- DATABASE: $db ---"
    runuser -u postgres -- psql -X -d "$db" -c "
    SELECT extname, extversion
    FROM pg_extension
    ORDER BY extname;
    "
done
'

echo
echo "===== INVALID INDEX CHECK ====="
pct exec 310 -- bash -c '
for db in $(runuser -u postgres -- psql -X -At -d postgres -c "SELECT datname FROM pg_database WHERE datistemplate = false AND datallowconn = true ORDER BY datname"); do
    echo "--- DATABASE: $db ---"
    runuser -u postgres -- psql -X -d "$db" -c "
    SELECT n.nspname AS schema_name, c.relname AS index_name,
           i.indisvalid, i.indisready
    FROM pg_index i
    JOIN pg_class c ON c.oid = i.indexrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE NOT i.indisvalid OR NOT i.indisready;
    "
done
'

echo
echo "===== POSTGRESQL STARTUP LOG ====="
pct exec 310 -- bash -c \
'tail -n 100 /var/log/postgresql/postgresql-17-main.log'
```

Each database has an owner, `vector` is `0.8.7` in `easywrider`, `postgres` and `vector_db`, and there were zero invalid indexes (`indisvalid=false` or `indisready=false`) in any database.

In the role list command, `!~` was interpreted by Bash as history expansion, so the condition excluding system roles did not take effect. This is not data corruption. We retrieve it again with a corrected command and also check whether `pg_amcheck` exists.

> **Run on: pve**

```bash
echo "===== POSTGRESQL ROLES (CORRECTED) ====="
pct exec 310 -- runuser -u postgres -- psql -X -d postgres -c "
SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolcanlogin
FROM pg_roles
WHERE left(rolname, 3) <> 'pg_'
ORDER BY rolname;
"

echo
echo "===== PG_AMCHECK AVAILABILITY ====="
pct exec 310 -- bash -c '
if command -v pg_amcheck >/dev/null 2>&1; then
    command -v pg_amcheck
    pg_amcheck --version
else
    echo "pg_amcheck: NOT INSTALLED"
fi
'

echo
echo "===== POSTGRESQL ERROR LOG SUMMARY ====="
pct exec 310 -- bash -c "
grep -Ei 'FATAL|PANIC|ERROR|corrupt|invalid page|checksum' \
  /var/log/postgresql/postgresql-17-main.log | tail -n 80
"

echo
echo "===== CT310 ROOT FILESYSTEM USAGE ====="
pct exec 310 -- df -h /
```

| Item | Result |
|---|---|
| Roles | 18 retrieved |
| CTID 310 rootfs | 45GB free |
| `pg_amcheck` | not installed (not installed here) |

### 2.5 Sorting Out the Errors in the Log

The log contained duplicate-key errors on `alert_events_pkey` (records of duplicate INSERTs by the Wazuh Collector), errors from diagnostic SQL on `security_workbench`, and `FATAL` messages from connections during startup.

> **Run on: pve**

```bash
echo "===== CT310 POSTGRESQL LOG TIMELINE ====="
pct exec 310 -- bash -c '
echo "--- First log entries ---"
head -n 25 /var/log/postgresql/postgresql-17-main.log

echo
echo "--- Latest log entries ---"
tail -n 35 /var/log/postgresql/postgresql-17-main.log
'

echo
echo "===== CT310 POSTGRESQL START TIME ====="
pct exec 310 -- systemctl show postgresql@17-main \
  -p ActiveState -p ActiveEnterTimestamp -p ExecMainStartTimestamp

echo
echo "===== CT310 SYSTEM BOOT TIME ====="
pct exec 310 -- uptime -s

echo
echo "===== BACKUP ARCHIVE TIMESTAMP ====="
stat -c 'File=%n%nSize=%s bytes%nModified=%y' \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_23-09_43_34.tar.zst

echo
echo "===== CT310 CURRENT STATUS ====="
pct status 310
```

Putting the times in order, these were things already recorded in production before the backup, failed diagnostic queries, or connections made during startup; none of them indicates database corruption.

## Chapter 3: Comparing with Production

CT109 has kept running since the backup, so we do not require the data to be exactly identical. We compare whether the structure is the same.

### 3.1 Database Names and Sizes

> **Run on: pve**

```bash
echo "===== CT109 PRODUCTION STATUS ====="
pct status 109

echo
echo "===== CT310 RESTORE TEST STATUS ====="
pct status 310

echo
echo "===== DATABASE INVENTORY COMPARISON ====="
for CT in 109 310; do
    echo
    echo "===== CT${CT} ====="
    pct exec "$CT" -- runuser -u postgres -- psql -X -d postgres -P pager=off -c "
    SELECT
        d.datname AS database_name,
        pg_database_size(d.datname) AS size_bytes,
        pg_size_pretty(pg_database_size(d.datname)) AS size,
        (
            SELECT count(*)
            FROM information_schema.tables t
            WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
              AND t.table_type = 'BASE TABLE'
              AND t.table_catalog = d.datname
        ) AS base_tables
    FROM pg_database d
    WHERE d.datistemplate = false
    ORDER BY d.datname;
    "
done

echo
echo "===== RESTORE TEST CONTAINER CONFIGURATION ====="
pct config 310 | grep -E '^(hostname|onboot|net[0-9]+|rootfs|unprivileged):'
```

Both CT109 and CT310 have 17 databases, all with the same names. Sizes differ by a few KB to about 1MB, which is considered to be due to updates in production after the backup. CT310 remains `onboot: 0`, `link_down=1`.

### 3.2 Numbers of Tables and Views

`information_schema.tables` only sees the database you are connected to, so we connect to each database and count.

> **Run on: pve**

```bash
for CT in 109 310; do
    echo
    echo "===== CT${CT}: PER-DATABASE OBJECT COUNTS ====="

    pct exec "$CT" -- bash -c '
    DB_LIST=$(runuser -u postgres -- psql -X -At -d postgres \
        -c "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname")

    while IFS= read -r DB; do
        [ -n "$DB" ] || continue

        runuser -u postgres -- psql -X -At -F "|" -d "$DB" -c "
        SELECT
            current_database(),
            count(*) FILTER (WHERE c.relkind IN (chr(114), chr(112))),
            count(*) FILTER (WHERE c.relkind = chr(118)),
            count(*) FILTER (WHERE c.relkind = chr(109))
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE left(n.nspname, 3) <> chr(112)||chr(103)||chr(95)
          AND n.nspname <> chr(105)||chr(110)||chr(102)||chr(111)||chr(114)||chr(109)||chr(97)||chr(116)||chr(105)||chr(111)||chr(110)||chr(95)||chr(115)||chr(99)||chr(104)||chr(101)||chr(109)||chr(97)
          AND c.relkind IN (chr(114), chr(112), chr(118), chr(109));
        " 2>&1
    done <<< "$DB_LIST"
    '
done
```

The output is `database|tables|views|materialized views`. **For all 17 databases, the counts in CT109 and CT310 were the same** (266 tables in total, 1 view, 0 materialized views).

| Database | Tables (CT109) | Tables (CT310) |
|---|---|---|
| agent_db | 18 | 18 |
| agent_memory | 31 (1 view) | 31 (1 view) |
| aipmo | 23 | 23 |
| easywrider | 29 | 29 |
| movie | 22 | 22 |
| novel | 22 | 22 |
| orchivio | 55 | 55 |
| winfilemgr | 8 | 8 |
| writers | 12 | 12 |

The other eight databases are also the same.

### 3.3 Indexes, Constraints and Extensions

> **Run on: pve**

```bash
for CT in 109 310; do
    echo
    echo "========================================"
    echo " CT${CT}: INDEX / CONSTRAINT / EXTENSION"
    echo "========================================"

    pct exec "$CT" -- bash -c '
    DB_LIST=$(runuser -u postgres -- psql -X -At -d postgres \
        -c "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname")

    while IFS= read -r DB; do
        [ -n "$DB" ] || continue

        echo
        echo "--- DATABASE: $DB ---"

        echo "[INDEXES]"
        runuser -u postgres -- psql -X -At -F "|" -d "$DB" -c "
        SELECT
            count(*),
            count(*) FILTER (WHERE NOT i.indisvalid),
            count(*) FILTER (WHERE NOT i.indisready)
        FROM pg_index i
        JOIN pg_class ic ON ic.oid = i.indexrelid
        JOIN pg_namespace n ON n.oid = ic.relnamespace
        WHERE left(n.nspname, 3) <> chr(112)||chr(103)||chr(95)
          AND n.nspname <> chr(105)||chr(110)||chr(102)||chr(111)||chr(114)||chr(109)||chr(97)||chr(116)||chr(105)||chr(111)||chr(110)||chr(95)||chr(115)||chr(99)||chr(104)||chr(101)||chr(109)||chr(97);
        "

        echo "[CONSTRAINTS: PRIMARY / FOREIGN / UNIQUE / CHECK / EXCLUSION]"
        runuser -u postgres -- psql -X -At -F "|" -d "$DB" -c "
        SELECT
            count(*) FILTER (WHERE contype = chr(112)),
            count(*) FILTER (WHERE contype = chr(102)),
            count(*) FILTER (WHERE contype = chr(117)),
            count(*) FILTER (WHERE contype = chr(99)),
            count(*) FILTER (WHERE contype = chr(120))
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE left(n.nspname, 3) <> chr(112)||chr(103)||chr(95)
          AND n.nspname <> chr(105)||chr(110)||chr(102)||chr(111)||chr(114)||chr(109)||chr(97)||chr(116)||chr(105)||chr(111)||chr(110)||chr(95)||chr(115)||chr(99)||chr(104)||chr(101)||chr(109)||chr(97);
        "

        echo "[EXTENSIONS]"
        runuser -u postgres -- psql -X -At -F "|" -d "$DB" -c "
        SELECT extname, extversion
        FROM pg_extension
        ORDER BY extname;
        "
    done <<< "$DB_LIST"
    '
done
```

The total of 534 indexes (0 invalid or not ready), the numbers of primary keys, foreign keys, unique constraints and CHECK constraints, and the names and versions of the extensions (`vector 0.8.7` in 3, `plpgsql 1.0` in 17) were all the same.

### 3.4 Schema Definitions

Beyond counts, we compare table definitions, columns, data types, and index and constraint definitions. We take the SHA256 of the output of `pg_dump --schema-only`. The data itself is not output.

> **Run on: pve**

```bash
for DB in agent_db agent_memory aiagent aipmo cerebrum easywrider movie nfaipmo novel orchivio postgres security_workbench tester vector_db winfilemgr writer writers; do
    echo
    echo "===== DATABASE: $DB ====="

    for CT in 109 310; do
        echo -n "CT${CT}: "

        pct exec "$CT" -- runuser -u postgres -- \
            pg_dump --schema-only --dbname="$DB" 2>/dev/null |
            sed '/^\\restrict /d; /^\\unrestrict /d' |
            sha256sum
    done
done
```

For 16 of the 17, the SHA256 of CT109 and CT310 matched. Only `novel` differed.

### 3.5 The Difference in `novel`

> **Run on: pve**

```bash
echo "===== NOVEL SCHEMA DIFFERENCE CHECK ====="

WORKDIR="$(mktemp -d /var/tmp/novel-schema-diff.XXXXXX)"
echo "WORKDIR=$WORKDIR"

echo
echo "===== EXPORT CT109 ====="
pct exec 109 -- runuser -u postgres -- \
  pg_dump --schema-only --dbname=novel \
  > "$WORKDIR/ct109.raw.sql" \
  2> "$WORKDIR/ct109.stderr"
echo "CT109_PG_DUMP_EXIT=$?"

echo
echo "===== EXPORT CT310 ====="
pct exec 310 -- runuser -u postgres -- \
  pg_dump --schema-only --dbname=novel \
  > "$WORKDIR/ct310.raw.sql" \
  2> "$WORKDIR/ct310.stderr"
echo "CT310_PG_DUMP_EXIT=$?"

echo
echo "===== NORMALIZE DUMP HEADERS ====="
sed '/^\\restrict /d; /^\\unrestrict /d' \
  "$WORKDIR/ct109.raw.sql" > "$WORKDIR/ct109.sql"
sed '/^\\restrict /d; /^\\unrestrict /d' \
  "$WORKDIR/ct310.raw.sql" > "$WORKDIR/ct310.sql"

echo
echo "===== DUMP SIZES ====="
wc -c "$WORKDIR/ct109.sql" "$WORKDIR/ct310.sql"

echo
echo "===== STDERR ====="
cat "$WORKDIR/ct109.stderr"
cat "$WORKDIR/ct310.stderr"

echo
echo "===== SCHEMA DIFF ====="
diff -u "$WORKDIR/ct109.sql" "$WORKDIR/ct310.sql" | head -240
echo "DIFF_EXIT=${PIPESTATUS[0]}"

echo
echo "===== TEMPORARY FILES ====="
echo "$WORKDIR"
```

There were two columns present in CT109 but not in CT310 (`ollama_api_key` and `controller_ollama_api_key`, `character varying(500)`). Without touching the column values (API keys), we check which table they belong to.

> **Run on: pve**

```bash
for CT in 109 310; do
    echo
    echo "===== CT${CT}: NOVEL TARGET COLUMN DEFINITIONS ====="

    pct exec "$CT" -- runuser -u postgres -- psql -X -d novel -P pager=off -c "
SELECT
    n.nspname AS schema_name,
    c.relname AS table_name,
    a.attname AS column_name,
    format_type(a.atttypid, a.atttypmod) AS data_type,
    a.attnotnull AS not_null,
    (d.adbin IS NOT NULL) AS has_default,
    a.attidentity AS identity_type,
    a.attgenerated AS generated_type
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_attrdef d
    ON d.adrelid = a.attrelid
   AND d.adnum = a.attnum
WHERE a.attnum > 0
  AND NOT a.attisdropped
  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
  AND a.attname IN (
      'translator_pool',
      'ollama_api_key',
      'controller_ollama_api_key'
  )
ORDER BY n.nspname, c.relname, a.attnum;
"
done
```

| Column | CT109 | CT310 |
|---|---|---|
| `translator_pool` | present | present |
| `ollama_api_key` | present | absent |
| `controller_ollama_api_key` | present | absent |

The table is `novel.public.runtime_config`. These two columns are a difference caused by schema changes in an application under development (in the build records they were treated as "under development"). This is neither a fault nor backup corruption, so it is not something to fix.

## Closing Notes

In Part 44 we checked the backup system and compared the restored databases with production.

| Checked | Result |
|---|---|
| Backup catalog | two generations of LXC 109 registered |
| Job and boot dependencies | `tmpdir: /var/tmp` and the service that waits for TrueNAS are in place |
| Isolation of CTID 310 | `link_down=1`, `onboot=0`, `eth0` `DOWN` |
| PostgreSQL 17.11 | starts; all 17 databases can be connected to |
| Numbers of tables and views | the same for all 17 |
| Indexes, constraints, extensions | all the same; 0 invalid indexes |
| Schema definitions | 16 identical; the difference in `novel` is a development change |

With this, the backup system built in Volume 3 is as follows.

| Time | Job | Destination |
|---|---|---|
| Daily 02:00 | PostgreSQL logical backup (17 databases and global objects) | TrueNAS NFS `postgresql/` (7 daily, 4 weekly, 3 monthly) |
| Daily 03:00 | Proxmox backup of LXC 109 (temporary directory `/var/tmp`) | TrueNAS NFS `dump/` (7 daily, 4 weekly, 3 monthly) |
| Daily 04:00, Sunday 04:10, 1st 04:20 | TrueNAS ZFS snapshots | `backup` dataset (7 days, 4 weeks, 3 months) |
| At boot | mount after waiting for TrueNAS VM 100 and NFSv3 to respond | `/mnt/pve/backup` |

CTID 310 is still running with its network cut off. When you are done with it, stop it with the procedure in 5.5 of Part 41. We have not checked whether the data in every table is the same, nor connections from the applications.

This is the end of Volume 3. Volume 4 moves on to finishing the LLM side of the AI Defense Manager (repairing Wazuh rules, the form of the input passed to the LLM, a static IP for VM 230, checking the output, API token authentication, detecting log tampering) and to building AI defense agents.

---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 31: Why the Collector Cannot Read After Log Switching, and the Fix"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 31 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". At the end of Part 30 in Volume 2, after checking how the Collector reads, we began to investigate how Wazuh's alert logs are switched (rotated). Continuing from there, this part does the following.

1. Find out, using reads only, when and how Wazuh's alert logs are switched
2. Find out why, after the switch on November 21, the Collector could not open the new file and kept reporting `PermissionError`
3. Add a **Default ACL** (an ACL inherited by newly created files and directories) to the per-date directories (`2026`, `2026/Nov`)
4. Test with temporary files that the ACL is inherited, and record the state before an actual switch

The cause turned out to be as follows.

- Alert files are created per date, such as `alerts/2026/Nov/ossec-alerts-21.json`, and `alerts.json` is a hard link to that file (the same inode)
- `/var/ossec/logs/alerts` had a Default ACL, but `2026` and `2026/Nov` below it did not
- So when the date changed and a new file was created, the Collector's user (`wazuh-collector`) was not given read permission on it

## About Volume 3

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

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **postgresql**: LXC 109 (192.168.0.151), OS user `postgres`
- Unless otherwise noted, times are in UTC (Japan time is 9 hours ahead).

# Chapter 1: Finding Out How the Logs Are Switched

## 1.1 The logrotate Settings

> **Run on: VM 220**

Look for settings for Wazuh's alert logs in the OS logrotate.

```bash
grep -R -n -E 'alerts\.json|/var/ossec/logs/alerts|copytruncate|rotate|compress' /etc/logrotate.conf /etc/logrotate.d /var/ossec/etc 2>/dev/null | head -160
```

There was no setting in `/etc/logrotate.d` targeting `alerts.json`, and no `copytruncate` (truncating the file in place) setting either. The alert logs are switched by Wazuh itself, not by the OS logrotate.

## 1.2 The List of Alert Files

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

## 1.3 What the Collector Does When the Old Inode Is Not Found

```bash
sed -n '350,460p' /usr/local/lib/wazuh-collector/collector.py
```

When the saved inode differs from the current file, `open_initial_file()` looks for the old inode among uncompressed `.json` files and, if found, resumes from the saved position. If not found, it raises an exception and stops; **it does not silently skip to the end of the current file**. It is designed on the safe side, so that no data is skipped.

## 1.4 Wazuh's Switching Settings

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

# Chapter 2: Why the Collector Could Not Read After the Switch

## 2.1 The Collector's Log Around the Switch

```bash
journalctl -u wazuh-collector.service --since "2026-11-20 23:55:00" --until "2026-11-21 00:15:00" --no-pager -o short-iso
```

From 00:14:24 to 00:14:59 the following error appeared every second.

```text
ERROR Failed to open current alert file: PermissionError
```

The Collector could not open the file newly created by the switch.

## 2.2 Checking the ACL

```bash
getfacl -p /var/ossec/logs/alerts /var/ossec/logs/alerts/alerts.json /var/ossec/logs/alerts/2026/Nov/ossec-alerts-21.json
```

`/var/ossec/logs/alerts` has a Default ACL (`default:user:wazuh-collector:r-x` and so on), and the current files (`alerts.json` and `ossec-alerts-21.json`) have `user:wazuh-collector:r--` (added in Part 29). However, the per-date files are created inside `2026/Nov`.

```bash
getfacl -p /var/ossec/logs/alerts/2026 /var/ossec/logs/alerts/2026/Nov
```

`2026` and `2026/Nov` had an ordinary ACL (`user:wazuh-collector:r-x`), but **no Default ACL**. So files newly created inside `2026/Nov` do not inherit the Collector's read permission.

## 2.3 The Process That Creates the Files

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

# Chapter 3: Adding a Default ACL

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

# Chapter 4: Recording the State Before the Switch

## 4.1 Time and Files

```bash
echo '===== SYSTEM TIME ====='; date --iso-8601=seconds; timedatectl show -p Timezone -p NTPSynchronized; echo '===== ALERT FILES ====='; stat -c '%n | inode=%i | size=%s | mtime=%y | mode=%a' /var/ossec/logs/alerts/alerts.json /var/ossec/logs/alerts/2026/Nov/ossec-alerts-21.json; echo '===== ROTATION SETTINGS ====='; grep -E '^monitord\.(day_wait|compress|rotate_log|size_rotate|daily_rotations|keep_log_days)=' /var/ossec/etc/internal_options.conf
```

The time is UTC and synchronized with NTP; `alerts.json` and the per-date file had the same inode (5409517) and were 883,525 bytes.

## 4.2 The Collector's Read Position

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

## 4.3 Service and Storage Status

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

# Chapter 5: Testing That the ACL Is Inherited

## 5.1 A New File

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

## 5.2 A New Month Directory

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

# Chapter 6: Checks Before Waiting for the Switch

## 6.1 Wazuh's Records and Processes

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

## 6.2 Wazuh's Version and Settings

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

## 6.3 The Baseline Just Before the Switch

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

# Closing Notes

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

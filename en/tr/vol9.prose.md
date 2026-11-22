---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 9: Recovering from a Collector Stop and Checking Operations"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 9 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". After the monitoring platform was completed in Part 8, a check made before moving on to the next stage (the SOC data integration platform) found that the Wazuh Collector had stopped. Part 9 covers finding the cause, ingesting the missed alerts into the DB, returning to normal collection, then checking monitoring, the DB, time and event contents, and dealing with the problem found (a flood of events).

This is an actual occurrence of "resuming after the old file has been compressed", listed under "Open Issues" in Part 7.

## Notation

- Commands and file contents are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Each step begins with "Run on", which says where to run it.
- "Example output" is the actual output from the build. Inodes, counts, times and so on will differ in your environment.
- Commands that display the contents of the state file (`state.json`) or connection details are not included.

## What Had Happened (Summary)

| Order | Details |
|---|---|
| 1 | At 23:53 on November 18, the Collector read the 18th's `alerts.json` to the end and saved its state |
| 2 | When the date changed, a new `alerts.json` was created, but it had no read ACL for the Collector, so the Collector could not read it and kept exiting abnormally (10,005 automatic restarts) |
| 3 | Meanwhile, the 18th's file was compressed (`.json.gz`), and the file with the saved inode disappeared |
| 4 | The 19th's file was also compressed, and the 19th's alerts (9,039) remained un-ingested |

# Chapter 1: Confirming the Stop and the First Cause

## 1.1 The Collector's State

**Run on: security-core VM 220 (root)**

⟦C0⟧

At build time it showed `NRestarts=10005`, `MainPID=0` and `SubState=auto-restart`, and a `PermissionError` when reading `alerts.json` was being logged repeatedly.

## 1.2 Checking the Permissions

**Run on: security-core VM 220 (root)**

⟦C1⟧

The parent directories had traverse permission, and systemd's restrictions were not the cause. The cause was that the new `alerts.json` (`wazuh:wazuh`, `640`) had no read ACL for the Collector.

## 1.3 Adding a Read ACL to alerts.json

Without changing the owner, group or normal permissions, add only read permission for `wazuh-collector`.

**Run on: security-core VM 220 (root)**

⟦C2⟧

If `read_test_exit_code=0`, it can be read. Check whether the automatic restart brings it back.

⟦C3⟧

In the original build, this alone did not bring it back, because the cause described in the next chapter remained.

# Chapter 2: The Second Cause: The Saved inode Had Disappeared

## 2.1 What the Investigation Found

At startup, if the saved inode is not the current `alerts.json`, the Collector searches the `alerts` directory recursively (Part 6). At build time, the following two problems coincided.

| Problem | Details |
|---|---|
| Search failure | A root-only hidden directory created by an earlier test (`.acl-inheritance-test.bkv8vd`, `root:root`, `0700`) remained in `alerts`, and the search stopped with a permission error |
| inode gone | The file with the saved inode (`5409146`) was nowhere under `/var/ossec/logs` |

The hidden directory was not deleted and was left as is (because later steps return the Collector to a state in which it can start without searching).

## 2.2 Looking for the Saved inode

**Run on: security-core VM 220 (root)**

⟦C4⟧

⟦C5⟧

Replace `5409146` with the inode saved in your environment's state file. At build time it was not found, and the state file's modification time was still 23:53 on November 18.

## 2.3 Listing the Log Files

**Run on: security-core VM 220 (root)**

⟦C6⟧

The files for the 17th–19th had been compressed into `.json.gz`, and an old file's inode changes when it is compressed.

## 2.4 Matching the Compressed Files Against the Saved Position

Count while decompressing the compressed files, and find out which day's file, and where in it, the saved position (offset) corresponds to.

**Run on: security-core VM 220 (root)**

⟦C7⟧

Replace `target_offset` with the position saved in your environment's state file.

| Item | Value at build time |
|---|---|
| Saved position | 2,774,739 bytes |
| Decompressed size of `ossec-alerts-18.json.gz` | 2,774,739 bytes (match) |
| Time of the last alert of the 18th | 2026-11-18T23:53:10.688+0000 |
| Modification time of the state file | 2026-11-18 23:53:12 |

This showed that the 18th had been ingested to the end and that what had not been ingested was the 19th (`ossec-alerts-19.json.gz`).

## 2.5 Checking the Boundary Between the 19th and Today

**Run on: security-core VM 220 (root)**

⟦C8⟧

| File | Count | Time |
|---|---:|---|
| `ossec-alerts-19.json.gz` | 9,039 | Last `00:00:01.339` (on the 20th) |
| `alerts.json` (the 20th) | 2,749 | First `00:00:07.341` |

Neither had any broken lines, lines without an ID, or lines without a time. If the 19th is ingested and then the 20th continues, nothing is missed.

# Chapter 3: Recovery Plan and Preparation

## 3.1 The Plan

Rather than adding support for compressed files to the Collector's source, recover in the following order. The Collector's source, the systemd settings and the Wazuh logs themselves are not changed.

1. Insert the 9,039 alerts of the 19th (`ossec-alerts-19.json.gz`) into the DB using the Collector's existing processing (`process_line()`).
2. Events already inserted are skipped by the existing duplicate handling (unique constraint).
3. Only if all records are processed, advance the state file to the current `alerts.json`'s inode and position `0`.
4. Through its automatic restart, the Collector returns to normal collection from the beginning of the current `alerts.json` (the saved inode is now the current file, so no directory search takes place).

If it fails partway, the state file is not advanced, so it can safely be run again thanks to duplicate handling.

## 3.2 Backing Up the Collector

**Run on: security-core VM 220 (root)**

⟦C9⟧

## 3.3 Checking the DB Connection as the Collector's User

Check only whether it connects, without showing the connection details.

**Run on: security-core VM 220 (root)**

⟦C10⟧

## 3.4 Adding a Read ACL to the 19th's File

**Run on: security-core VM 220 (root)**

⟦C11⟧

⟦C12⟧

The `Nov` directory gave the Collector read and traverse permission; only read permission on the one file was missing. Add it to that file only.

⟦C13⟧

## 3.5 Validating the 19th (No Writes to the DB)

Validate all records with the Collector's `extract_event()`.

**Run on: security-core VM 220 (root)**

⟦C14⟧

Replace `9039` with the count in your environment counted in 2.5. At build time the result was `archive_validation=OK`.

# Chapter 4: Ingesting the 19th and Returning to Normal Collection

## 4.1 Ingestion

**Run on: security-core VM 220 (root)**

⟦C15⟧

Replace `expected_lines` with the count in your environment. At build time all 9,039 records were processed, and the state file was advanced to position `0` of the current `alerts.json` (inode `5409383`) (`recovery_result=SUCCESS`).

> Do not run this just before the date changes (just before rotation). If the current `alerts.json` is replaced during processing, it stops without advancing the state file.

## 4.2 Confirming the Return to Normal Collection

Now that the state file points to the current `alerts.json`, the Collector starts on its next automatic restart without searching the directory. At build time, the following log appeared right after ingestion, and the Collector returned to service.

⟦C16⟧

Check whether the read position has advanced to the end of the current file.

**Run on: security-core VM 220 (root)**

⟦C17⟧

| Check | Result at build time |
|---|---|
| State | `active` / `running` (PID `88146`) |
| inode of the state file and `alerts.json` | `5409383` / `5409383` (match) |
| Read position | 5,879,391 bytes (matches the file size) |
| Remaining | `0` bytes |

`NRestarts` includes the automatic restarts while it was stopped, so it stays a large value. There is no problem as long as it stops increasing.

## 4.3 Checking for Errors After the Return

**Run on: security-core VM 220 (root)**

⟦C18⟧

The log from 10 minutes earlier also includes errors from before the return. Narrow it to the log since the return (04:44:17 UTC at build time).

⟦C19⟧

At build time, the log after the return contained only "starting", "resuming from the current file" and "connected to PostgreSQL", with no errors (`No errors after recovery`).

## 4.4 Checking the DB Table

**Run on: LXC 109 postgresql (root)**

⟦C20⟧

Confirm that the table structure (primary key, indexes on time, severity, rule and source IP) has not changed.

# Chapter 5: Checking That the SOC Platform Is Running

After the recovery, we checked, using reads only, that each component used in the next stage (the SOC data integration platform) is working correctly.

## 5.1 VictoriaMetrics and Metrics

**Run on: security-core VM 220 (root)**

⟦C21⟧

Get the load, free memory and free root space of the five machines.

⟦C22⟧

At build time, data for all five machines was obtained.

## 5.2 Wazuh Services

**Run on: security-core VM 220 (root)**

⟦C23⟧

## 5.3 Wazuh API Response and Certificate

Without using credentials, check only whether the API responds and requires authentication.

**Run on: security-core VM 220 (root)**

⟦C24⟧

If `HTTP status: 401` is returned, the API is running and rejects unauthenticated access. `TLS verify result: 18` means a self-signed certificate (verification is skipped with `-k`).

Check the contents of the certificate (public information, not the private key).

⟦C25⟧

⟦C26⟧

| Item | Result at build time |
|---|---|
| Issuer / subject | `CN=wazuh.com` (self-signed) |
| SAN | Only `DNS:localhost` |

When used as `https://localhost:55000`, the name matches. It does not match with IP addresses (127.0.0.1, 192.168.0.220). We decided to settle the server name and the trusted CA when the API is used from other hosts, and did not regenerate the certificate here.

## 5.4 Wazuh Manager Errors and Warnings

**Run on: security-core VM 220 (root)**

⟦C27⟧

At build time there were no errors or warnings in the last 30 minutes.

# Chapter 6: Checking the Events in the DB

## 6.1 PostgreSQL and Table Privileges

**Run on: LXC 109 postgresql (root)**

⟦C28⟧

⟦C29⟧

Confirm that `wazuh_collector` has only `INSERT` (still the least privilege from Part 3).

## 6.2 Counts and Severity

**Run on: LXC 109 postgresql (root)**

⟦C30⟧

⟦C31⟧

⟦C32⟧

At build time, 5,345 level-7 events were concentrated in the five minutes 04:40–04:45 UTC.

## 6.3 What the Concentrated Events Were

Distinguish whether they came from an attack or were an effect of the recovery, using the event time and the DB insert time.

**Run on: LXC 109 postgresql (root)**

⟦C33⟧

⟦C34⟧

Replace the time range with the period where the concentration was found in your environment.

| Item | Result at build time |
|---|---|
| Count | 5,345 |
| Event times | 04:43:57–04:44:10 UTC (about 12 seconds) |
| DB inserts | 04:44:48–04:45:27 UTC |

Both the events and the inserts are concentrated around the time the Collector returned (04:44:17). They came from ingesting today's alerts in bulk right after the return, so we decided not to count them as attacks.

## 6.4 Measuring the Ingestion Delay

Excluding the concentrated events, measure the time from an event occurring to its insertion into the DB.

**Run on: LXC 109 postgresql (root)**

⟦C35⟧

At build time, the 255 events measured showed large delays: an average of 170 seconds, a median of 79 seconds and a P95 of 541 seconds. Check whether the Collector is leaving data unread.

**Run on: security-core VM 220 (root)**

⟦C36⟧

At build time the read position and the file size matched (5,958,275 bytes), so nothing was left unread. The cause of the delay therefore lies elsewhere.

# Chapter 7: Checking Time Synchronization

The event time (security-core) and the DB insert time (PostgreSQL) are recorded by the clocks of different servers. If the clocks drift, the delay looks large.

## 7.1 security-core

**Run on: security-core VM 220 (root)**

⟦C37⟧

At build time it showed `System clock synchronized: yes` and `NTP service: active` (time zone UTC).

## 7.2 PostgreSQL (LXC 109)

**Run on: LXC 109 postgresql (root)**

⟦C38⟧

⟦C39⟧

At build time it showed `System clock synchronized: yes` but `NTP service: inactive`, and there was no time synchronization service inside the LXC. An LXC uses the Proxmox host kernel's clock as is, so check the host side. (The time zone was Asia/Tokyo, but this is not a problem because the DB compares `timestamptz` in UTC.)

## 7.3 The Proxmox Host

**Run on: Proxmox host pve (root)**

⟦C40⟧

⟦C41⟧

At build time it was synchronized by chrony, with a clock offset of less than 1 millisecond. Delays of several minutes cannot be explained by clock drift.

# Chapter 8: Measuring the Ingestion Delay Again

## 8.1 Preparing a Role for Aggregation

We decided to use the administrative role `dbadmin` for aggregating in the DB. Give it minimal, read-only privileges.

**Run on: LXC 109 postgresql (root)**

⟦C42⟧

⟦C43⟧

At build time, `dbadmin` was an ordinary role that could log in (no superuser or create-DB privileges) and had no privileges on the `incident` schema or table. Give it read access only.

⟦C44⟧

⟦C45⟧

Confirm that only `can_select` is `t` and the rest are `f`.

## 8.2 Connecting as dbadmin

`dbadmin` is not an OS user, so you cannot connect with `sudo -u dbadmin`. Connect over TCP to localhost (`scram-sha-256` authentication) and enter the password (it is not shown on screen, and it is not written in this manual).

**Run on: LXC 109 postgresql (root)**

⟦C46⟧

## 8.3 The Delay over the Last 15 Minutes

**Run on: LXC 109 postgresql (root)**

⟦C47⟧

At build time, the 69 events had an average of 1.28 seconds, a median of 1.27 seconds, a P95 of 1.79 seconds and a maximum of 1.84 seconds, with zero negative delays (time reversals).

Also check minute by minute.

⟦C48⟧

The large delays seen in 6.4 were temporary, caused by the concentrated ingestion right after the recovery; in normal operation, events are inserted within 1–2 seconds.

# Chapter 9: The Cause of a Flood of Events and the Fix

## 9.1 Counts per Rule

**Run on: LXC 109 postgresql (root)**

⟦C49⟧

At build time, rule 40704 (level 5, `Systemd: Service exited due to a failure.`) had 11,905 events, far more than any other.

⟦C50⟧

Replace the list of `rule_id` values with the rules at the top in 9.1 in your environment.

## 9.2 Breakdown of 40704

**Run on: LXC 109 postgresql (root)**

⟦C51⟧

| Host | Count (at build time) | Details |
|---|---:|---|
| security-core | 11,268 | About 16 hours' worth inserted in bulk by the ingestion in Chapter 4 |
| postgresql | 225 | Still occurring about once a minute |
| lxc-prometheus | 210 | Still occurring about once a minute |
| lxc-grafana | 206 | Still occurring about once a minute |

⟦C52⟧

Over the last 15 minutes, the delay was within 2 seconds on all three machines. So ingestion is normal, and services really are exiting abnormally over and over on the three machines.

## 9.3 Identifying the Failing Service

The DB does not store the full log (`full_log`), so extract only the names of the failed services from the Wazuh alert file.

**Run on: security-core VM 220 (root)**

⟦C53⟧

Adjust the date in the file name (`ossec-alerts-20.json`) to the day you are investigating. At build time, all of them were `prometheus-node-exporter-ipmitool-sensor.service`. This is an auxiliary service that collects IPMI sensor values, installed together with the Node Exporter package in Part 8.

## 9.4 Confirming the Cause

**Run on: LXC 105 lxc-grafana (root)**

⟦C54⟧

The log repeatedly showed the following error (postgresql and lxc-prometheus were the same).

⟦C55⟧

⟦C56⟧

⟦C57⟧

⟦C58⟧

| Item | State at build time |
|---|---|
| `/sys/class/ipmi/ipmi0` | Present (the host's information is visible from the LXC) |
| `/dev/ipmi0` and similar | Absent (no device is passed to the LXC) |
| IPMI collection timer | Runs every minute |
| Node Exporter itself | Normal |

The timer's start condition (`ConditionDirectoryNotEmpty=/sys/class/ipmi`) is met, so collection ran every minute and failed because it could not open the device. Wazuh detected those failures as 40704.

## 9.5 Stopping the IPMI Collection Timer

Without changing Node Exporter itself, the Prometheus settings or forwarding, stop only the IPMI collection timer and disable its automatic start on the three LXCs (lxc-grafana, postgresql, lxc-prometheus). Run it on one machine at a time and check.

**Run on: LXC 105 lxc-grafana, LXC 109 postgresql, LXC 103 lxc-prometheus (root on each)**

⟦C59⟧

⟦C60⟧

At build time, on all three machines the timer was `inactive` and `disabled`, and Node Exporter was `active` / `running`.

> In the original build, only the three LXCs on which 40704 continued were dealt with. The Proxmox host (`pve`, 1 event at build time) and security-core (11,268 events were past alerts ingested in bulk) were not.

# Summary of Part 9

## Causes and Fixes

| Cause | Fix |
|---|---|
| The new `alerts.json` had no read ACL for the Collector | Added with `setfacl -m u:wazuh-collector:r--` (1.3) |
| The file with the saved inode disappeared through compression, and the search also stopped at a root-only hidden directory | Ingested the 19th with the existing processing and advanced the state file to the current `alerts.json` (Chapter 4) |

## What Was Changed

| Target | Change |
|---|---|
| `/var/ossec/logs/alerts/alerts.json` (the 20th) | Read ACL for the Collector |
| `/var/ossec/logs/alerts/2026/Nov/ossec-alerts-19.json.gz` | Read ACL for the Collector |
| `/var/lib/wazuh-collector/state.json` | inode of the current `alerts.json`, position `0` |
| DB `incident.alert_events` | Alerts of the 19th (duplicates skipped) |

The Collector's source, the systemd settings and the Wazuh logs themselves were not changed. The backup is at `/root/wazuh-collector-recovery/collector.py.before-recovery`.

## What the Checks Found (Chapters 5–9)

| Item | Result |
|---|---|
| VictoriaMetrics and the metrics of the five machines | Normal |
| Wazuh Manager and API | Normal (the API requires authentication; the certificate is self-signed with only `localhost` as SAN) |
| Large number of events right after the recovery | Caused by ingesting past alerts (not an attack) |
| Time synchronization | Normal (offset under 1 millisecond) |
| Normal ingestion delay | 1–2 seconds |
| Flood of rule 40704 | Failures of the IPMI collection timer on the LXCs; the timer was stopped on three machines |

For aggregation in the DB, `dbadmin` was given privileges to use the `incident` schema and read `incident.alert_events`.

## Remaining Issues

- **[Risk, open]** When the date changes, Wazuh creates a new `alerts.json`. If the new file does not get a read ACL for the Collector, the same stop will happen again. No permanent measure (such as a default ACL) for the daily rotation has been taken. If it stops, recover with Chapter 1 (adding the ACL) and, if needed, Chapters 2–4 (ingesting what was missed). Check the Collector's state (an increasing `NRestarts` or `PermissionError`) every day.
- **[Risk, open]** The root-only hidden directory in the `alerts` directory (`.acl-inheritance-test.bkv8vd`) has not been deleted and remains. If the Collector searches the directory again (when the saved inode is not the current `alerts.json`), it stops with the same permission error.
- The Collector still does not search compressed files (`.json.gz`). If an old file is compressed while it is stopped, recover with the same steps as Chapters 2–4.

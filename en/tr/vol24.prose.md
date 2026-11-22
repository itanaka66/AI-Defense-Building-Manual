---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 2"
subtitle: "Part 24: Finding Out Why the Audit Log Is Not Saved"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 24 of Volume 2 of the "AI Autonomous Cyber Defense System Build Manual". In Part 23 of Volume 1, we found that the security audit log of Wazuh Indexer (OpenSearch) is "enabled", yet no place where it is saved could be found. Here we find out why, **using reads only**, without changing any settings.

The investigation has three stages.

1. Use the administrator API to check the audit settings, indices, Data Streams and cluster settings
2. Use `javap` (a tool that disassembles Java classes) from the JDK bundled with the Indexer to read the Security plugin's code and find out how the audit log's output destination (Sink) is chosen
3. Connect to the running Indexer's JVM with `jcmd` and check which classes are loaded (read-only)

The conclusions are as follows.

- The audit log's output destination is chosen by the setting `plugins.security.audit.type`. **This setting has no default value**
- Without it, the main output destination (default Sink) is not created, and the mechanism that distributes audit messages (the router) is disabled
- When the router is disabled, **audit events are saved nowhere**, even though the audit API shows `enabled: true`
- In this environment, the output destination was not specified anywhere: not in the configuration files, the cluster settings, the startup arguments or the environment variables

## About Volume 2

Volume 2 starts with this book. In Volume 1 (Parts 1–23), we built a defense foundation centered on Wazuh and AI analysis with the AI Defense Manager and the relay API (Relay), and at the end of Volume 1 (Part 23) we found that the Wazuh Indexer audit log appeared not to be saved anywhere. In Volume 2, we get this audit log working and fix a Collector stop found along the way.

| Part | Contents |
|---|---|
| Part 24 | Find out in the code why the audit log is not saved |
| Part 25 | Set where the audit log is saved |
| Part 26 | Do not record request bodies in the audit log |
| Part 27 | Confirm that the audit log is being saved |
| Part 28 | Check the Collector and find why it stopped |
| Part 29 | Restart the Collector without missing any events |
| Part 30 | Keep the Collector from stopping for the same reason |

This volume assumes the same environment as the procedures in Volume 1 (Proxmox, VM 220 security-core, LXC 109 PostgreSQL and so on). For adapting it to ordinary PCs, see "Building on Ordinary PCs" in Part 1 of Volume 1.

## Downloading the Scripts

The scripts used in this book can be downloaded from:

https://github.com/itanaka66/AI-Defense-Building-Manual/releases

## Volumes and Parts

Because the build records are long, this manual is divided into the following two volumes. Part numbers run continuously across volumes.

| Volume | Parts | Main topics |
|---|---|---|
| Volume 1 | Parts 1–23 | Defense foundation (Wazuh, Collector, PostgreSQL, monitoring), AI Defense Manager, a search user for Wazuh, the relay API (Relay), AI analysis and its protection, checks |
| Volume 2 | Parts 24–30 | Enabling and verifying the Wazuh Indexer audit log; checking, recovering and preventing recurrence for the Collector |

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

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **security-core VM 220 (root)**.
- The administrator certificate (`admin.pem`, `admin-key.pem`) is used only to make read queries to the Indexer, and its contents are not shown.
- The output of `javap` is very long, so this book gives only the key points of the results.

# Chapter 1: Checking Through the API

## 1.1 The List of Indices

⟦C0⟧

There were no indices for the audit log, such as `auditlog6` or `auditlog6-YYYY.MM.dd`.

## 1.2 The Audit Settings

⟦C1⟧

It returned `HTTP_STATUS: 200`, but the settings are inside `config`, so this program did not show the values. Look inside `config`.

⟦C2⟧

Auditing is enabled, and `log_request_body` (recording request bodies) was `true`.

## 1.3 All Indices

⟦C3⟧

Among all 25 indices, none could be identified as belonging to the audit log.

⟦C4⟧

The Indexer's log had no records of audit initialization or errors either.

## 1.4 Every Item of the Audit Settings

⟦C5⟧

| Item | Value |
|---|---|
| Auditing overall | Enabled |
| REST and Transport auditing | Enabled |
| Categories not recorded | `AUTHENTICATED`, `GRANTED_PRIVILEGES` |
| `compliance.read_metadata_only`, `write_metadata_only` | `true` |

None of the items decides the output destination (Sink).

# Chapter 2: Reading the Security Plugin's Code

## 2.1 The Plugin Files

⟦C6⟧

A plugin is a JAR (ZIP format), so you cannot search inside it with `grep`.

⟦C7⟧

The Security plugin was `opensearch-security-2.19.6.0.jar`. `unzip` is not installed, so without adding packages, list the contents of the JAR with Python's standard library.

⟦C8⟧

The following implementations existed as output destinations for the audit log.

| Class | Output destination |
|---|---|
| `InternalOpenSearchSink` | An index inside the Indexer |
| `InternalOpenSearchDataStreamSink` | A Data Stream inside the Indexer |
| `ExternalOpenSearchSink` | An external OpenSearch |
| `Log4JSink` | A log file |
| `KafkaSink`, `WebhookSink` | Kafka, Webhook |
| `DebugSink`, `NoopSink` | For debugging / does nothing |

⟦C9⟧

The standard audit configuration (`static_audit.yml`) contained only `_readonly: []`, which did not reveal the output destination.

## 2.2 Is the Output Destination Specified in a Configuration File?

⟦C10⟧

Only the example settings file (`opensearch.yml.example`) was found.

## 2.3 javap

`javap` is not installed in the OS, but it is in the JDK bundled with the Indexer.

⟦C11⟧

## 2.4 The Code That Chooses the Output Destination (SinkProvider)

⟦C12⟧

- `plugins.security.audit.type` chooses the output destination
- `internal_opensearch` outputs to `InternalOpenSearchSink`, and `internal_opensearch_data_stream` to a Data Stream

⟦C13⟧

There were zero log lines about the output destination. Check the configuration file that is actually loaded (values are not shown).

⟦C14⟧

The configuration file is `/etc/wazuh-indexer/opensearch.yml`, and it had no `plugins.security.audit.*` settings.

## 2.5 The Setting's Default Value

Look at the part where settings are registered.

⟦C15⟧

⟦C16⟧

`plugins.security.audit.type` is registered with `Setting.simpleString()`, and **no default value is given**. Unless it is written in a configuration file, something like `internal_opensearch` is never chosen automatically.

⟦C17⟧

- If the output destination type is not specified, `createSink()` returns `null`
- `DebugSink` is not created in place of the main output destination but as a spare (fallback) for when saving fails
- If the main output destination cannot be created, an error is logged and initialization ends

# Chapter 3: Is It Set Through Another Path?

## 3.1 Data Streams

⟦C18⟧

`/_data_stream` returned `HTTP 200` with zero Data Streams (`_cat/data_streams` returned `400`, but the former shows that there are none).

## 3.2 Startup Arguments and Environment Variables

⟦C19⟧

For environment variables, only the names are shown (the values are hidden).

⟦C20⟧

Neither specified an audit output destination.

## 3.3 Cluster Settings

Search the persistent settings, transient settings and default values for anything containing `plugins.security.audit`.

⟦C21⟧

None of them specified it.

## 3.4 When the Output Destination Is null

⟦C22⟧

`createSink()` first sets the output destination to `null`, and returns as is if the type is `null`. Also check the other way of specifying it (`plugins.security.audit.endpoints`).

⟦C23⟧

There were zero.

⟦C24⟧

The initialization of `SinkProvider` is as follows.

1. If no fallback is specified, create a `DebugSink`
2. Create the main output destination (default) from `plugins.security.audit.type`
3. If the main output destination cannot be created, log an error and end initialization

⟦C25⟧

There were zero log lines about auditing.

# Chapter 4: How Events Are Distributed

## 4.1 The Audit Classes

`jar` is not installed in the OS, so use `jar` from the Indexer's JDK.

⟦C26⟧

`AuditLogImpl` receives audit events, and `AuditMessageRouter` distributes them to the output destinations.

⟦C27⟧

⟦C28⟧

Decoding the bytecode, the saving process takes the following form (rewritten in Java).

⟦C29⟧

## 4.2 The Router

⟦C30⟧

- If the main output destination is `null`, the router is disabled (`isEnabled()` is false)
- If an event arrives while it is disabled, it logs the error `#route(AuditMessage) called but message router is disabled` and stops

⟦C31⟧

`setConfig()` had the following form.

⟦C32⟧

In other words, even with `enabled: true` in the audit API, if there is no main output destination, `messageRouterEnabled` becomes false and auditing does not actually work.

## 4.3 Messages at Startup

⟦C33⟧

⟦C34⟧

There were no matching messages in either the journal or the log files.

# Chapter 5: Looking at the Running JVM

## 5.1 Startup Time

⟦C35⟧

At build time the Indexer was PID 1238 and had started at 06:56:11 on November 20, 2026 (the startup is within the period examined).

## 5.2 jcmd

`jcmd` is a tool that connects to a running JVM and obtains information. Only read commands are used here. Replace the PID with the one in your environment.

⟦C36⟧

⟦C37⟧

At build time this was OpenJDK 21.0.11. Check the loaded audit classes.

⟦C38⟧

`AuditLogImpl`, `AuditMessageRouter`, `SinkProvider`, `DebugSink`, `InternalOpenSearchSink`, `ExternalOpenSearchSink` and others were loaded. However, a class being loaded is different from an output destination actually being chosen and working.

# Closing Notes

What Part 24 found is as follows.

| Item | Result |
|---|---|
| Audit API settings | Enabled (`log_request_body: true`) |
| `plugins.security.audit.type` | Not specified anywhere (and no default value) |
| Main output destination (default Sink) | Not created |
| Router | Disabled |
| Audit log | Considered **not to be saved** |

In the next part, we set `plugins.security.audit.type` so that the audit log is saved inside the Indexer, and stop recording request bodies.

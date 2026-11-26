---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 45: Preparing for LLM Analysis and Repairing the Wazuh Configuration File"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 45 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Volume 3 (Parts 31–44), we finished the backup and restore of the PostgreSQL that stores the events. Volume 4 moves on to threat analysis using an LLM (large language model).

We do not give the LLM direct authority over defensive operations. The LLM only produces material for decisions and proposals, kept separate from the actual operations. As a precondition, we check the reliability of the data passed to the LLM. Part 45 does the following.

1. Check the layout and state of the existing environment (Wazuh, PostgreSQL, Ollama, AI Defense Manager), read-only
2. Find that the Wazuh Manager configuration file `/var/ossec/etc/ossec.conf` is broken as XML, and investigate why
3. Save a copy of the configuration file, repair it, and check it with Wazuh's test command (Wazuh is not restarted)

## About Volume 4

In Volume 4, centered on the AI Defense Manager (VM 230), we build the mechanisms for running LLM analysis safely. We narrow the input passed to the LLM with an allowlist, mask the LLM's output and keep approval decisions on the server side, and add token authentication to the API. We then build a mechanism for detecting log tampering (FSS), fix Wazuh's local rules, and finally start building AI defense agents.

| Part | Content |
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

It assumes the same environment as Volumes 1, 2 and 3 (Proxmox, VM 220 security-core, VM 230 ai-defense-manager, VM 101 ollama-gpu, LXC 109 PostgreSQL and so on).

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
  - **pve**: the Proxmox host (root)
  - **VM 220**: security-core (root). Log in as root from the Console of VM 220 in the Proxmox web interface

# Chapter 1: Checking the Current Environment

Here we create no new VMs or containers, and change or restart nothing.

## 1.1 Layout of Containers and VMs

> **Run on: pve**

⟦C0⟧

| Role | Location |
|---|---|
| Wazuh | VM 220 `security-core` |
| AI Defense Manager | VM 230 `ai-defense-manager` |
| LLM inference (Ollama) | VM 101 `ollama-gpu` (running) |
| PostgreSQL | CT 109 (production), CT 310 (for verifying the isolated restore) |
| Vector search | CT 134 `qdrant` |
| Monitoring | CT 103 Prometheus, CT 105 Grafana |

## 1.2 State of Each Node

> **Run on: pve**

⟦C1⟧

PostgreSQL, Qdrant and Open WebUI are running and can be used as they are. VMs 220, 230 and 101 did not respond through the QEMU Guest Agent at this point (which does not mean the VMs are stopped).

## 1.3 Wazuh State

VM 220's address is `192.168.0.220`. Through the Guest Agent, we check the Wazuh services and listening ports.

> **Run on: pve**

⟦C2⟧

The three services, Wazuh Manager 4.14.10, Indexer and Dashboard, were all `active`, and the agent communication ports 1514/1515 and the API port 55000 were listening. The Indexer's 9200/9300 are localhost only.

## 1.4 The Path from Wazuh to PostgreSQL

We do not display secrets in configuration files or alert bodies; we only check service names and whether processes exist.

> **Run on: pve**

⟦C3⟧

On CT 109, `wazuh-agent.service`, `postgresql-wazuh-filter.service` and PostgreSQL (5432) were running. For LLM analysis, rather than passing data directly from Wazuh Manager to the LLM, our policy is to use masked events as the input boundary.

On the other hand, retrieving a summary of `ossec.conf` on VM 220 gave `CONFIG_READ_ERROR: ParseError`.

# Chapter 2: Finding Where the Configuration File Is Broken

## 2.1 Position of the Error

> **Run on: pve**

⟦C4⟧

`/var/ossec/etc/ossec.conf` could not be read by a standard XML parser because **after line 323 there is content outside the XML document's root element**. Even though the Wazuh services are `active`, the configuration cannot be called correct.

## 2.2 Structure Around the Error

We look only at the tag structure without showing values.

> **Run on: pve**

⟦C5⟧

After the first root element closed with `</ossec_config>` on line 321, a second `<ossec_config>` began on line 323. The configuration block added last had been placed outside the original root element.

## 2.3 How Long It Has Been Like This

> **Run on: pve**

⟦C6⟧

| Item | Result |
|---|---|
| `ossec.conf` last modified | November 17 |
| Wazuh Manager start records | every day, November 18–22 |
| Last start | November 22 21:52 UTC (November 23 06:52 JST) |

Wazuh Manager had been starting with the broken XML since at least November 18.

## 2.4 Contents of the Added Block

> **Run on: pve**

⟦C7⟧

⟦C8⟧

Lines 323–339 contained three `<localfile>` entries enclosed in the second `<ossec_config>`.

| Target | Format | Purpose |
|---|---|---|
| journald | journald | the systemd journal |
| `/var/ossec/logs/active-responses.log` | syslog | Wazuh Active Response records |
| `/var/log/dpkg.log` | syslog | records of Debian package operations |

The natural fix is to move these into the first `<ossec_config>` rather than delete them. Before that, we check whether the original block already has the same settings.

## 2.5 Checking from the Console

At this point, running commands through the Guest Agent (`guest-exec`) began to time out. VM 220 is `running` and the Guest Agent ping succeeds, so instead of restarting VM 220 or reinstalling the Guest Agent, we log in as root from **VM 220 → Console** in the Proxmox web interface and check there.

> **Run on: VM 220**

⟦C9⟧

Both the Guest Agent (`qemu-guest-agent`) and Wazuh Manager were running.

> **Run on: VM 220**

⟦C10⟧

| Block | Number of `localfile` | Contents |
|---|---|---|
| First (the proper root element) | 3 | 1 `command`, 2 `full_command` |
| Second (after line 323) | 3 | 1 journald, 2 syslog |

The formats and sources differ, so these are not duplicates. We keep all six.

# Chapter 3: Repairing the Configuration File

## 3.1 Saving a Copy and Repairing

We do the following. Wazuh is not restarted and no services are changed.

1. Save the current `ossec.conf` to another file
2. Remove only the outer frame of the second `<ossec_config>` and move the three entries inside it into the first block
3. Check the XML syntax, the number of settings and the SHA256

> **Run on: VM 220**

⟦C11⟧

The XML syntax is valid, there are six `localfile` entries, and the SHA256 of the saved copy matched the file before the repair. Wazuh Manager is still running.

## 3.2 Root Element, Owner and Permissions

> **Run on: VM 220**

⟦C12⟧

| Item | Result |
|---|---|
| `<ossec_config>` start and end | one each |
| Root element | `ossec_config` |
| `localfile` | 6 |
| Owner and permissions | `root:wazuh` (GID 110), `660` |
| Saved copy | present, matches the SHA256 before the repair |

## 3.3 Testing the Logcollector Configuration

Wazuh's `-t` is an option that only tests the configuration; it does not restart the running service.

> **Run on: VM 220**

⟦C13⟧

`wazuh-logcollector -t` gave exit code `0`. The `pgrep` warning means that the process name exceeds 15 characters and so an ordinary search does not match it; it is not a configuration error.

## 3.4 Running Processes and Logs

> **Run on: VM 220**

⟦C14⟧

⟦C15⟧

| Checked | Result |
|---|---|
| Logcollector process | running |
| Errors and warnings after the repair | none in the range examined |
| `wazuh-analysisd`, `remoted`, `db`, `modulesd`, `syscheckd`, `api` | running |
| Wazuh Manager | `active` |

That `wazuh-clusterd`, `wazuh-maild` and others are stopped is normal in a single-Manager configuration.

# Closing Notes

In Part 45, before moving on to LLM analysis, we checked the environment and fixed the broken XML of the Wazuh configuration file.

| Item | Result |
|---|---|
| Environment | use Wazuh (VM 220), AI Defense Manager (VM 230), Ollama (VM 101) and PostgreSQL (CT 109); no new VMs |
| `ossec.conf` | the second `<ossec_config>` merged into the first, keeping the six `localfile` entries; copy saved; `root:wazuh`, `660` |
| Wazuh test | `wazuh-logcollector -t` gave `0` |
| Wazuh restart | not done (the running processes will not reflect the change until Wazuh rereads its configuration) |

In the next part, Part 46, we classify the contents of Wazuh alerts and decide which fields may be passed to the LLM.

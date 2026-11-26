---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 46: Classifying Alerts and Deciding Which Fields to Pass to the LLM"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 46 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 45 we repaired the Wazuh configuration file. Here, to decide what data to pass to the LLM, we examine the contents of Wazuh alerts by counts and types only, **without displaying values**.

1. Tally the alerts by count, severity, rule and classification group
2. Check the definitions of the most frequent rules and run Wazuh's own test (`wazuh-analysisd -t`)
3. Examine the field names in the alert JSON and separate the fields that may be passed to the LLM from those that must not
4. Decide the types and constraints of the seven allowed fields, and try the conversion on real alerts in memory only

Event bodies, IP addresses, user names and commands are not displayed. Nothing is written to files, registered in a DB or sent to the LLM.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **pve**: the Proxmox host (root)

# Chapter 1: Tallying the Alerts

## 1.1 Count and Severity

> **Run on: VM 220**

⟦C0⟧

The current `alerts.json` had **245** correctly readable alerts (228 at severity Level 3, 17 at Level 7, 0 unreadable). This is the number left in the file; not all of them necessarily occurred recently.

## 1.2 Rules and Classification Groups

> **Run on: VM 220**

⟦C1⟧

- 220 of the 245 have the `pam` group (groups are counted with overlap)
- Rules `5501` and `5502` account for 220 together
- All 17 at Level 7 are rule `100103` (groups `local`, `error`)
- Rule `87203` appears 6 times (group `proxmox-ve`)

Rule IDs and group names alone do not tell us whether something is an attack.

# Chapter 2: Checking the Rule Definitions

## 2.1 Rule Descriptions and Classification Conditions

Without reading event bodies, we extract only the descriptions and classification conditions from the rule definitions.

> **Run on: VM 220**

⟦C2⟧

| Rule | Meaning |
|---|---|
| `5501` | PAM login session opened |
| `5502` | PAM login session closed |
| `5715` | SSH authentication succeeded |
| `87203` | Proxmox VE authentication succeeded |

## 2.2 Location of the Rule Files

> **Run on: VM 220**

⟦C3⟧

`100103` is in `/var/ossec/etc/rules/local_rules.xml`, and `5402` is in the standard rule file `0020-syslog_rules.xml`.

Python's standard XML parser gives `ParseError` for 27 rule files, but Wazuh rule files put several top-level elements in one file, so this alone does not mean they are broken. We check with Wazuh's own test.

## 2.3 Wazuh's Own Test

> **Run on: VM 220**

⟦C4⟧

`wazuh-analysisd -t` gave exit code `0`. Wazuh reads the rule configuration correctly.

## 2.4 Definitions of the Local Rules

> **Run on: VM 220**

⟦C5⟧

| Rule | Count | Meaning | Assessment |
|---|---:|---|---|
| 5501 | 112 | PAM login session opened | ordinary authentication record |
| 5502 | 108 | PAM login session closed | ordinary authentication record |
| 100103 | 17 | PostgreSQL ERROR event | to be examined |
| 87203 | 6 | Proxmox VE authentication succeeded | ordinary authentication record |
| 5715 | 1 | SSH authentication succeeded | ordinary authentication record |
| 5402 | 1 | root privileges obtained with sudo | check whether the operation was legitimate |

`100100` is the Level 0 "PostgreSQL sanitized JSON event base rule", and `100103` is the Level 7 "PostgreSQL ERROR event detected". The 17 are Wazuh detections of the masked PostgreSQL events from CT 109; we treat them as application or database errors, not attacks.

# Chapter 3: Deciding the Fields to Pass to the LLM

## 3.1 Field Names in the Alert JSON

We count only field names without showing values.

> **Run on: VM 220**

⟦C6⟧

All 245 had `full_log` and `data`. They also contain information that must not be passed to the LLM as is, such as `agent.ip`, `agent.name`, `data.dstuser`, `data.srcuser`, `data.command` and `data.pwd`. Therefore **we do not send the alert JSON to the LLM as it is**.

| Field | Handling |
|---|---|
| `timestamp` | pass (after checking the format) |
| `rule.id` | pass |
| `rule.level` | pass |
| `rule.groups` | pass (restricted by an allowlist) |
| `rule.description` | pass (check length and characters) |
| `decoder.name` | pass (restricted by an allowlist) |
| `agent.id` | pass |
| `agent.ip`, `agent.name` | exclude |
| `full_log` | always exclude |
| `data` | exclude entirely |
| `predecoder`, `manager`, `location`, `id` | exclude as a rule |

## 3.2 Types and Missing Values of the Seven Fields

> **Run on: VM 220**

⟦C7⟧

In all 245, the seven fields were present, with the expected types.

## 3.3 Constraints of the Seven Fields

> **Run on: VM 220**

⟦C8⟧

For all seven fields, 245 of 245 satisfied the constraints, with 0 non-conforming values. With this we fix the LLM input allowlist (v1).

| Field | Type | Constraint |
|---|---|---|
| `timestamp` | string | ISO 8601 date and time |
| `rule_id` | string | 1–16 digits |
| `severity` | integer | 0–16 |
| `groups` | array of strings | alphanumerics and `_.-`, up to 64 characters each |
| `description` | string | up to 160 characters |
| `decoder` | string | alphanumerics and `_.-`, up to 64 characters |
| `agent_id` | string | 1–16 digits |

The important point is **not to copy anything other than the allowed fields**. Not only do we exclude `data` and `full_log`, we discard every unknown field.

## 3.4 Trying the Conversion in Memory

We convert the actual 245 in memory only.

> **Run on: VM 220**

⟦C9⟧

| Checked | Result |
|---|---|
| Converted | all 245 |
| Conversion errors, key structure errors | 0 |
| Forbidden fields leaked | 0 |
| JSON re-read errors | 0 |
| Total size after conversion | 46,848 bytes |
| Maximum size of one | 225 bytes |

We confirmed that the events passed to the LLM can be made small and of a fixed shape. However, this was confirmed on the current 245; when actually integrated, the input is checked every time.

# Chapter 4: The Data Path

We build no new services and use the current environment. The planned data path is as follows.

⟦C10⟧

The PostgreSQL filter on CT 109 keeps its current role as the boundary that masks PostgreSQL events. We do not mix it with the Wazuh alert conversion or change the filter.

Finally, we check the layout of the three VMs involved.

> **Run on: pve**

⟦C11⟧

| VM | Role | State | vCPU | Memory | Network |
|---|---|---|---:|---:|---|
| 220 | Wazuh (security-core) | running | 8 | 16GB | vmbr0, vmbr1 |
| 230 | AI Defense Manager | running | 4 | 8GB | vmbr0 |
| 101 | Ollama (GPU) | running | 16 | 128GB | vmbr0 |

> **Caution:** `qm` is a command on the Proxmox host. Running it inside VM 220 gives `qm: command not found`. Check that the prompt is `root@pve:~#` before running it.

# Closing Notes

In Part 46 we examined the contents of the alerts without looking at values, and decided the fields to pass to the LLM.

| Item | Result |
|---|---|
| Alerts | 245 (mostly PAM, SSH and Proxmox authentication records; the 17 at Level 7 are PostgreSQL ERRORs) |
| Wazuh test | `wazuh-analysisd -t` gave `0` |
| Fields passed to the LLM | 7 (`timestamp`, `rule_id`, `severity`, `groups`, `description`, `decoder`, `agent_id`); everything else is discarded |
| Conversion test | all 245 succeeded; 0 forbidden fields leaked |

In the next part, Part 47, we examine the existing implementation of the AI Defense Manager on VM 230 and decide where to integrate the allowlist.

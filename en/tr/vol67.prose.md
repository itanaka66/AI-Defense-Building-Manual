---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 67: Finding the Breakage in Wazuh's Local Rules"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 67 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 66 we automated FSS verification on VM 230, but there was no path to report its results to Wazuh. Here, before integration, we examine the Wazuh Manager side on VM 220, read-only.

1. Check whether Wazuh Manager is configured to accept agents
2. Investigate the role of the Relay (8765) (a read-only API, not an entry point for events)
3. Find that the local rules `local_rules.xml` are broken as XML, and examine their structure
4. Without touching the production file, create a fixed candidate file

No configuration changes, agent registration, communication tests or service restarts. Credentials and secret keys are not displayed.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)

# Chapter 1: Wazuh Manager and the Relay

## 1.1 Configuration for Accepting Agents

> **Run on: VM 220**

⟦C0⟧

| Item | Result |
|---|---|
| Wazuh Manager 4.14.10 | `active (running)` |
| Agent communication | listening on TCP 1514 (`secure`) |
| Agent registration | listening on TCP 1515 |
| Registered agents | 5 |
| Relay | `ai-defense-relay.service`, `192.168.0.220:8765` |

## 1.2 The Relay's Structure

> **Run on: VM 220**

⟦C1⟧

The Relay runs `/opt/ai-defense-relay/relay.py` with Python 3.12 as the dedicated user `ai-defense-relay`. Wazuh had `local_rules.xml` and `local_decoder.xml`.

## 1.3 The Relay's GET and POST

> **Run on: VM 220**

⟦C2⟧

| Item | Result |
|---|---|
| `GET /health` | status check |
| `GET /v1/alerts` | search of Wazuh alerts (Indexer `127.0.0.1:9200`, `wazuh-alerts-4.x-*`) |
| Authentication | client IP restriction and token |
| `POST`, `PUT`, `DELETE` | `HTTP 405` |

The Relay is the side that **reads** Wazuh alerts, and cannot be used to POST FSS verification results into Wazuh.

# Chapter 2: The Breakage in `local_rules.xml`

## 2.1 Local Rules and Decoders

> **Run on: VM 220**

⟦C3⟧

`local_rules.xml` could not be read by Python's XML parser. `local_decoder.xml` is normal, and the decoder is `local_decoder_example`. Wazuh Manager is running (0 restarts).

## 2.2 Where It Is Broken

> **Run on: VM 220**

⟦C4⟧

- The current `local_rules.xml` fails XML parsing at line 21
- `backup-pre-reload` has the same SHA256 as the current file
- Several other copies also fail at the same line 21
- `backup-20261118-062100` is valid XML

## 2.3 Examining the Structure

> **Run on: VM 220**

⟦C5⟧

The current file had **two top-level elements**, as follows.

⟦C6⟧

An XML document needs exactly one root element. After the first root element closes at line 19, another root element begins at line 21, which causes the parse error.

> **Run on: VM 220**

⟦C7⟧

| Rule | Purpose | Level |
|---|---|---:|
| 100001 | SSH authentication failure | 5 |
| 100100 | base for PostgreSQL JSON events | 0 |
| 100101 | PostgreSQL authentication failure | 8 |
| 100106 | 5 authentication failures from the same IP | 12 |
| 100102 | PostgreSQL FATAL | 10 |
| 100103 | PostgreSQL ERROR | 7 |
| 100104 | PostgreSQL WARNING | 4 |
| 100105 | PostgreSQL PANIC | 12 |

There are no overlapping rule IDs.

# Chapter 3: Creating a Fixed Candidate

## 3.1 The Fix

According to the Wazuh documentation, the groups in a rules file are wrapped in one `<group>`, and per-rule classification is given by `<group>` inside each rule. To preserve the current classifications (SSH and PostgreSQL), we use the following form.

⟦C8⟧

Rule 100106 also had the following element.

⟦C9⟧

`<same_source_ip />` is an old name, but in current Wazuh it still works as an alias of `<same_srcip />`. It does not need to change, but we make it the newer `<same_srcip />` without changing the detection conditions.

> **Note:** In the build records, the first repair script found an unexpected group structure and stopped with `ABORT: unexpected group structure`. We confirmed that the SHA256, modification time and size of the production file had not changed.

## 3.2 Creating the Candidate File

Without changing the production file, we create a candidate in `/tmp` and check the XML syntax, the eight rule IDs, the group classification and `same_srcip`.

> **Run on: VM 220**

⟦C10⟧

| Checked | Result |
|---|---|
| XML syntax | valid |
| Number of rules | 8 (all IDs the same) |
| Root element | one `<group>` |
| SSH and PostgreSQL classification | moved inside each rule |
| Rule 100106 | `<same_srcip />` |
| Production file | SHA256 as original |
| Wazuh Manager | not restarted |

Being valid XML and being accepted as rules by Wazuh are separate matters. In the next part, Part 68, we check with Wazuh without placing it in production.

# Closing Notes

In Part 67 we examined the Wazuh side on VM 220 and found the breakage in the local rules file.

| Item | Result |
|---|---|
| Wazuh Manager | configured to accept agents (1514, 1515) |
| Relay | only reads alerts (POST gives `405`); cannot be used as an entry point for FSS results |
| `local_rules.xml` | had two top-level `<group>` elements; broken as XML |
| Candidate | `/tmp/local_rules.xml.candidate-20261124` (one root, 8 rules, classifications preserved, `<same_srcip />`) |
| Production | not changed yet |

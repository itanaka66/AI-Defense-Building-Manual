---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 69: Putting the Fixed Rules into Production"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 69 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 68 we checked the fixed `local_rules.xml` candidate in an isolated environment. Here we put it into production.

1. Save a copy of the current `local_rules.xml` and replace it with the candidate in one step
2. Run `wazuh-analysisd -t` with the production configuration
3. With `wazuh-logtest`, test whether the PostgreSQL rules fire as expected
4. Investigate what a Wazuh Manager reload does, perform it once, and have it load the rules

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)

# Chapter 1: Replacing the Production File

## 1.1 Replacing

We save a copy of the current `local_rules.xml`, with attributes and permissions, and replace it with the checked candidate in one step. No Manager restart or reload, and no other configuration changes.

> **Run on: VM 220**

⟦C0⟧

| Item | Result |
|---|---|
| New `local_rules.xml` | same SHA256 as the candidate |
| Old file | fully saved as a copy |
| Owner and permissions | `wazuh:wazuh`, `660` |
| XML parsing | passed |
| Rule IDs | all 8 remain |

## 1.2 Testing with the Production Configuration

> **Run on: VM 220**

⟦C1⟧

The production `wazuh-analysisd -t` gave exit code `0`; the whole production configuration, including the fixed `local_rules.xml`, passed Wazuh's test.

## 1.3 Running Processes

> **Run on: VM 220**

⟦C2⟧

`wazuh-manager.service` was `active (running)`, and `wazuh-analysisd` was running as PID `1721`. Whether the running process has loaded the new rules is not yet known.

# Chapter 2: Testing Rule Behavior

With `wazuh-logtest`, we feed test events one at a time. Actual PostgreSQL logs and other systems are not affected (the documentation IP address `192.0.2.10` is used).

## 2.1 Authentication Failure (100101)

> **Run on: VM 220**

⟦C3⟧

The decoder was `json`, rule `100101`, Level `8`.

## 2.2 Brute Force (100106)

We feed five in a row from the same IP.

> **Run on: VM 220**

⟦C4⟧

| Attempt | Rule, Level |
|---|---|
| 1st–4th | 100101, 8 |
| 5th | 100106, 12 (frequency 5, MITRE ATT&CK T1110 Brute Force) |

## 2.3 PANIC (100105)

> **Run on: VM 220**

⟦C5⟧

## 2.4 FATAL (100102)

> **Run on: VM 220**

⟦C6⟧

## 2.5 ERROR (100103)

> **Run on: VM 220**

⟦C7⟧

## 2.6 WARNING (100104)

> **Run on: VM 220**

⟦C8⟧

| Rule | Event | Level | Result |
|---|---|---:|---|
| 100101 | authentication failure | 8 | passed |
| 100106 | 5 authentication failures from the same IP | 12 | passed |
| 100105 | PANIC | 12 | passed |
| 100102 | FATAL | 10 | passed |
| 100103 | ERROR | 7 | passed |
| 100104 | WARNING | 4 | passed |

# Chapter 3: Having Wazuh Manager Load the Rules

## 3.1 What a Reload Does

> **Run on: VM 220**

⟦C9⟧

⟦C10⟧

The systemd unit had the following `ExecReload`.

⟦C11⟧

> **Run on: VM 220**

⟦C12⟧

`wazuh-control`'s reload calls `restart_service` for everything except `wazuh-execd`, as follows.

⟦C13⟧

It creates a `.restart` marker, checks the configuration with `testconfig`, stops and then starts the target daemons, and removes the marker. Because `wazuh-analysisd`, `wazuh-remoted` (agent communication), `wazuh-logcollector`, `wazuh-modulesd`, `wazuh-db`, `wazuh-authd` and others stop and start again, **this is not just rereading rules but a restart of a wide range of Manager daemons**. It also temporarily affects communication with agents.

## 3.2 Recording the State Before the Reload

> **Run on: VM 220**

⟦C14⟧

| Item | State |
|---|---|
| Wazuh Manager | `active (running)`, NRestarts 0 |
| Analysisd | PID `1721` |
| Agents | all 4 Active |
| `local_rules.xml` | matches the SHA256 after the fix |

## 3.3 Performing One Reload

> **Run on: VM 220**

⟦C15⟧

The reload gave exit code `0`; the Manager was `active (running)`; `wazuh-analysisd` changed from PID `1721` to `60112` (a new process); NRestarts stayed at 0. Right after, agent 002 (`lxc-prometheus`) was `Pending`.

## 3.4 Agent and Rule State

> **Run on: VM 220**

⟦C16⟧

Agent 002 also returned to Active, all 4 were normal, and there were no Manager error logs.

## 3.5 Rule Loading Records

> **Run on: VM 220**

⟦C17⟧

⟦C18⟧

It was recorded that the new `wazuh-analysisd` (PID `60112`) started and loaded the rules.

# Closing Notes

In Part 69 we put the fixed local rules into production and had Wazuh Manager load them.

| Item | Result |
|---|---|
| `local_rules.xml` | replaced with the fixed version (old one saved); `wazuh:wazuh`, `660` |
| Production test | `wazuh-analysisd -t` gave `0` |
| Rule tests | 100101, 100106, 100105, 100102, 100103 and 100104 all passed |
| Reload | once (restarts daemons other than `wazuh-execd`); analysisd is a new process; the 4 agents are Active |
| Rules loaded | `Total rules enabled: '8461'` |

> **Operational note:** A Wazuh Manager reload restarts a wide range of daemons, including agent communication. Record the state before doing it, and afterwards confirm that the agents have returned to Active.

In the next part, Part 70, we start building AI defense agents on top of the AI Defense Manager.

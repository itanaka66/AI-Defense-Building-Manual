---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 49: Narrowing the Fields Returned by the Relay to Seven"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 49 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 48 we changed the AI Defense Manager on VM 230 to receive Wazuh events narrowed to seven fields and to classify them by `rule.groups`. Here we make the data returned by the relay API (Relay) on VM 220 match that.

1. Identify the Relay listening on port 8765 and its implementation file
2. Compare the data the Relay returns with the shape VM 230 expects
3. Save a copy of `relay.py`, then limit the returned fields to seven and add a check of `rule.groups`
4. Check the diff and restart only the Relay service

Apart from restarting the Relay, there is no communication with the Indexer and no actual communication from VM 230.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)

# Chapter 1: Examining the Relay

## 1.1 The Service on Port 8765

Authentication details and process arguments are not displayed.

> **Run on: VM 220**

⟦C0⟧

What listens on `192.168.0.220:8765` is the running `ai-defense-relay.service`.

## 1.2 The Implementation File

> **Run on: VM 220**

⟦C1⟧

The implementation was `/opt/ai-defense-relay/relay.py`.

## 1.3 How the Returned Data Is Built

Rather than the whole file, we extract only the parts related to route definitions, JSON generation and event normalization. Tokens and secret keys are not displayed.

> **Run on: VM 220**

⟦C2⟧

The new `_convert_alert()` on VM 230 requires `rule.groups`, but the Relay was in the following state.

| Field | Now | Needed |
|---|---|---|
| `timestamp`, `agent.id`, `rule.level`, `rule.description`, `rule.id`, `decoder.name` | retrieved and returned | keep |
| `rule.groups` | **not retrieved** | add |
| `agent.ip`, `agent.name`, `manager.name`, `location` | retrieved and returned | **remove** |

# Chapter 2: Fixing the Relay

## 2.1 Saving a Copy

The service is not stopped and there is no communication.

> **Run on: VM 220**

⟦C3⟧

The copy is `/var/backups/ai-defense-relay/20261123-044701/relay.py`; its SHA256 matches the original, and the owner and permissions are `root:ai-defense-relay`, `640`.

## 2.2 Reading the Parts to Fix

> **Run on: VM 220**

⟦C4⟧

## 2.3 Fixing

We fix the following three things.

1. Limit `ALLOWED_FIELDS` to seven fields and stop retrieving `agent.ip`, `agent.name`, `manager.name` and `location`
2. Add checks to `sanitize_alert()`, such as that `rule.groups` is a list. Invalid events are dropped while processing of other valid events continues
3. Do not include dropped events in the returned `alerts`

`decoder.name` is checked and passed through by the Relay, but VM 230 does not send it to the AI. After checking the copy we make the fix, and before writing we run a syntax check and a test with synthetic data.

> **Run on: VM 220**

⟦C5⟧

| Checked | Result |
|---|---|
| Syntax and allowlist before writing | passed |
| Synthetic data (valid and invalid events) | passed |
| `ALLOWED_FIELDS` | 7 fields |
| `rule.groups` | checks list type, number of elements, number of characters and character types |
| Fields not returned | `agent.ip`, `agent.name`, `manager.name`, `location`, `full_log`, `data` |
| Owner and permissions | still `root:ai-defense-relay`, `640` |

## 2.4 Checking the Diff

> **Run on: VM 220**

⟦C6⟧

| Checked | Result |
|---|---|
| The seven allowed fields | passed |
| Forbidden fields not retrieved | passed |
| Checking and normalizing `rule.groups` | passed |
| Invalid events dropped and not returned | passed |
| Python syntax check | passed |
| Owner, permissions, copy | passed |

`DIFF_EXIT=1` means there are the intended differences from the copy.

# Chapter 3: Restarting the Relay

## 3.1 Restart

We restart only the Relay service on VM 220.

> **Run on: VM 220**

⟦C7⟧

| Item | Result |
|---|---|
| Restart | succeeded (exit code `0`) |
| State | `active`, `running` |
| New MainPID | `17052` |
| Running as | `ai-defense-relay` |
| Working directory | `/opt/ai-defense-relay` |

## 3.2 Checking the Listening Port

> **Run on: VM 220**

⟦C8⟧

It listens on `192.168.0.220:8765`, systemd shows `active (running)`, and the PIDs of the running process and the service are the same. The Relay on VM 220 is running with the new seven-field processing.

# Closing Notes

In Part 49 we made the data returned by the Relay match the shape VM 230 receives.

| Item | Result |
|---|---|
| Implementation | `/opt/ai-defense-relay/relay.py` |
| Copy | `/var/backups/ai-defense-relay/20261123-044701/relay.py` |
| Returned fields | 7 (`timestamp`, `rule.id`, `rule.level`, `rule.groups`, `rule.description`, `decoder.name`, `agent.id`) |
| Invalid events | dropped and not returned |
| Relay | restarted and running the new code |
| VM 230 | code fixed, but the service has not been restarted yet |

Before restarting the service on VM 230, we change VM 230's address from DHCP to a static address. We do this in the next part, Part 50.

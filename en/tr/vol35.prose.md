---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 35: Testing the Alert Rules and Checking in Production"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 35 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". In Parts 33 and 34 we put 16 alert rules into Prometheus: 9 for the Collector and 7 for the Wazuh platform. However, since nothing is currently wrong, we do not yet know whether the rules really fire.

Here we test the rules **without stopping production services**. Prometheus's `promtool test rules` is a tool that evaluates the rules against test time series written in a file and compares the results with expected ones.

1. For the 7 Wazuh platform rules, test that they do not fire when things are normal and do fire when they are not
2. In production Prometheus, check the actual values and the state of the 16 rules

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root). Commands inside LXC 103 (`lxc-prometheus`) are run with `pct exec 103 -- …`

# Chapter 1: Preparing the Rule Tests

## 1.1 promtool's Features

> **Run on: pve**

⟦C0⟧

promtool is 3.12.0, and `test rules` is available.

## 1.2 The Test File

The 7 rules are tested in the following 4 scenarios.

| Scenario | Data supplied | Expected result |
|---|---|---|
| `normal-no-alerts` | All 1, and the `.prom` file is fresh | None of the 7 fires |
| `service-down-alerts` | Manager, daemon, Indexer, Dashboard and API all 0 | 5 rules fire |
| `metrics-missing-alert` | Only the API number is missing | `WazuhPlatformMetricsMissing` fires |
| `metrics-stale-alert` | The `.prom` file's modification time is old | `WazuhPlatformMetricsStale` fires |

The test file is placed in `/tmp`; the production rule file is not changed.

⟦C1⟧

The file was created as `-rw-r--r-- root:root 4001 bytes`. The final YAML check in Python gives `ModuleNotFoundError: No module named 'yaml'` because `python3-yaml` is not installed in LXC 103, but this is not a problem. The YAML is read by the next command, `promtool test rules` (no packages are added).

# Chapter 2: Testing the Rules

## 2.1 First Run

⟦C2⟧

It was `FAILED` (`PROMTOOL_TEST_EXIT=1`). Looking at the details, **all 7 abnormal-case rules fired as expected**, and the normal case's "does not fire" also matched. The mismatch was because the test file did not specify `exp_annotations` (`summary` and `description`). promtool also compares the annotations attached to the actual alert.

## 2.2 Adding the Expected Annotations

First, read the relevant part of the test file.

⟦C3⟧

In the abnormal cases, the expectations are under `exp_labels`. Add `exp_annotations` at the same level. The normal case's `exp_alerts: []` stays as it is. The annotation texts are the same as in the production rules (Part 34).

⟦C4⟧

`ANNOTATIONS_ADDED: 7`, and the count of `exp_annotations:` was also `7`.

## 2.3 Second Run

Test with the same command as the first run.

⟦C5⟧

⟦C6⟧

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

# Chapter 3: Checking the Production Values

## 3.1 The Wazuh Platform and the 16 Rules

Query production Prometheus for the values it is currently collecting (reads only).

> **Caution**: If you use `'` in strings inside Python, it collides with the outer `'` of `pct exec 103 -- python3 -c '…'`, and from that point on the text is run as bash commands (a series of `syntax error near unexpected token` appears). The command below avoids `'` inside the Python. If input stops at a `>` continuation prompt, press `Ctrl+C` to get out before running it.

⟦C7⟧

| Item | Actual value |
|---|---|
| Node Exporter (`192.168.0.220:9100`) | `UP= 1` |
| Wazuh Manager, Indexer, Dashboard, API | All `1` |
| Manager daemons | All 9 `1` |
| Age of `wazuh_platform.prom` | About 16.3 seconds |
| Alert rules | 16 (all `health=ok`, `state=inactive`) |
| Firing alerts | 0 |

## 3.2 The Collector's Values

⟦C8⟧

| Metric | Actual value |
|---|---:|
| `wazuh_collector_service_up` | 1 |
| `wazuh_collector_restarts_total` | 0 |
| `wazuh_collector_state_valid` | 1 |
| `wazuh_collector_inode_match` | 1 |
| `wazuh_collector_unread_bytes` | 0 |
| `wazuh_collector_state_mtime_seconds` | Obtained |

# Closing Notes

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

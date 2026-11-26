---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 71: Correlation, Orchestration and Defense Decision Agents"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 71 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual", and the last part of Volume 4. In Part 70 we built two agents, for log analysis and threat analysis. Here we build the following agents.

| Agent | Role |
|---|---|
| `IncidentCorrelationAgent` | relates multiple events by time, agent and classification; deterministic processing without an LLM |
| `SecurityAnalysisOrchestrator` | combines correlation and AI analysis (orchestrating the analysis) |
| `DefensePolicyAgent` | does not trust AI proposals as is; decides by server-side rules |

None of these agents performs defensive actions, IP blocking, notification or DB storage. Existing APIs, DB, settings and services are not changed either.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (`192.168.0.221`, root. When logged in as `aidefense`, become root with `sudo -i`)

# Chapter 1: The Event Correlation Agent

## 1.1 Available Fields

> **Run on: VM 230**

⟦C0⟧

`SecurityEvent` has time, source IP, destination IP, agent ID and classification, but the current Wazuh conversion uses only `timestamp`, rule information, groups and `agent.id`, and does not pass IP addresses (because we narrowed it to seven fields in Part 48). **With the current Wazuh events alone, correlation by IP address is not possible.** We correlate using only the available fields.

| Item | Initial specification |
|---|---|
| Correlation key | same `agent_id` and same `event_category` |
| Time window | within 10 minutes of the first event |
| Minimum number of events | 2 |
| Time | time-zone-aware `observed_at` (normalized to UTC) |
| Correlation by IP | not used for now |
| Output | incident candidates, the event IDs they contain, the time range |

Events without `agent_id` are excluded so as not to relate them by mistake. Ten minutes is the value of this initial design.

## 1.2 Building

We create `app/agents/incident_correlation.py` and `tests/test_incident_correlation_agent.py` as new files.

> **Run on: VM 230**

⟦C1⟧

The module name imported by the test file differed from the actual one, and the import failed.

⟦C2⟧

## 1.3 Fixing the Test Import

`SecurityEvent` is in `app.schemas.security_event`.

⟦C3⟧

We fix only the one import line of the test file. The agent itself, the API, the DB and the service are not touched.

> **Run on: VM 230**

⟦C4⟧

| Agent | Tests |
|---|---:|
| `LogAnalysisAgent` | 2 passed |
| `ThreatAnalysisAgent` | 5 passed |
| `IncidentCorrelationAgent` | 7 passed |

All 14 passed. The specifications confirmed were: relating events of the same agent and classification within 10 minutes, normalizing time zones to UTC, not chaining beyond 10 minutes, excluding events without `agent_id`, rejecting duplicate event IDs, and not performing defensive actions.

# Chapter 2: The Analysis Orchestration Agent

## 2.1 Design

> **Run on: VM 230**

⟦C5⟧

`ThreatAnalysisAgent` calls `LogAnalysisAgent` internally. If the orchestration agent called both separately, the AI analysis would run twice. So we do the following.

1. Run the correlation analysis first
2. Call `ThreatAnalysisAgent` only once (`LogAnalysisAgent` runs inside it)
3. Return both results together
4. If either fails, propagate the exception; do not treat incomplete results as success
5. No defensive actions, IP blocking, notification or DB storage

## 2.2 Building and Testing

We create `app/agents/security_analysis_orchestrator.py` and `tests/test_security_analysis_orchestrator.py` as new files.

> **Run on: VM 230**

⟦C6⟧

| Test target | Result |
|---|---:|
| `IncidentCorrelationAgent` | 7 passed |
| `LogAnalysisAgent` | 2 passed |
| `ThreatAnalysisAgent` | 5 passed |
| `SecurityAnalysisOrchestrator` | 4 passed |
| Total | 18 passed, 0 failed |

We confirmed that the AI analysis runs only once, that when correlation fails the AI analysis is not run, and that when the AI analysis fails the exception is propagated.

# Chapter 3: The Defense Decision Agent

## 3.1 Existing Policy and Action Definitions

> **Run on: VM 230**

⟦C7⟧

| Item | Existing rule |
|---|---|
| IP blocking target | global IPs only |
| TTL | 1–900 seconds |
| Evidence | two or more separate event IDs |
| Approval | required |
| Initial approval state | `PENDING` |
| AI's approval decision | the server-side policy takes precedence |

`app/policies/` was empty, and there was no `DefensePolicyAgent` yet.

## 3.2 Design

`DefensePolicyAgent` decides independently before an AI proposal is turned into an `ActionProposal`. Whatever the result, this agent itself performs no defensive actions.

| AI proposal | Decision |
|---|---|
| `NO_ACTION` | create no action |
| `MONITOR`, `HUMAN_REVIEW` | there is no corresponding existing `ActionType`, so err on the safe side and reject |
| `COLLECT_EVIDENCE`, `NOTIFY` | create a proposal |
| `TEMPORARY_BLOCK_IP` | check the IP, TTL, evidence IDs and correlation result, and always set `PENDING` |

IP blocking is further allowed only when all of the following hold.

- Two or more pieces of evidence are in the same correlation group (cluster)
- Severity is `high` or `critical`
- Confidence is `0.90` or higher

This is a fixed criterion on the defense policy side and cannot be changed by the AI's approval flag.

## 3.3 The Script to Build It

This script creates two files, `app/agents/defense_policy.py` and `tests/test_defense_policy_agent.py`, and also tests the edge conditions.

> **Run on: VM 230**

⟦C8⟧

**The result of running this script is not within the build records received** (see the Missing Information Memo).

# Closing Notes

In Part 71 we built the event correlation and analysis orchestration agents and designed the defense decision agent.

| Agent | File | Tests |
|---|---|---|
| `LogAnalysisAgent` | `app/agents/log_analysis.py` | 2 passed |
| `ThreatAnalysisAgent` | `app/agents/threat_analysis.py` | 5 passed |
| `IncidentCorrelationAgent` | `app/agents/incident_correlation.py` | 7 passed |
| `SecurityAnalysisOrchestrator` | `app/agents/security_analysis_orchestrator.py` | 4 passed |
| `DefensePolicyAgent` | `app/agents/defense_policy.py` (up to the build script; the result is not in the records) | — |

None of the agents is connected to the API yet, and none performs defensive actions.

This is the end of the build records.

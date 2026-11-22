---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 17: Running the AI Defense Manager as a Service and Its Startup Order"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 17 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". In Part 16 we connected Wazuh alerts to AI analysis. Here we do the following three things so that the integration keeps working even after the VMs or Proxmox restart.

1. Make the AI Defense Manager a systemd service (listening only on `127.0.0.1:8000`)
2. Enable automatic start for the Relay (VM 220) and the AI Defense Manager (VM 230)
3. In Proxmox, set the order so that VM 220 starts first and VM 230 afterwards

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code, and the Japanese labels in diagrams, have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **VM 220**: security-core (root)
  - **pve**: the Proxmox host (root)

# Chapter 1: Aligning File Permissions

> **Run on: VM 230**

The three files created in Part 16 were `root:root` with `644`. Align them with the other application files: `root:ai-defense` with `640`.

⟦C0⟧

Before making it a service, confirm that the run-as user `ai-defense` can load the whole application (the server is not started).

⟦C1⟧

At build time, four routes were shown: `/health`, `/api/v1/analysis`, `/api/v1/wazuh/events` and `/api/v1/wazuh/analyze`.

# Chapter 2: The systemd Service

## 2.1 The Unit File

> **Run on: VM 230**

Confirm that no unit with the same name exists.

⟦C2⟧

Following the same approach as the Relay in Part 14, make it a tightly restricted service.

- Runs as `ai-defense`
- Listens only on `127.0.0.1:8000` (not exposed externally)
- The file system is read-only in principle (`ProtectSystem=strict`)
- No privileges; no access to the kernel or devices
- Memory limit of 1 GiB; restarts automatically only on abnormal exit

⟦C3⟧

Pasting can make the end look garbled, so check that it was written to the end.

⟦C4⟧

⟦C5⟧

## 2.2 Registering

⟦C6⟧

If it shows `LoadState=loaded`, `ActiveState=inactive` (still stopped), `UnitFileState=disabled` and `User=ai-defense`, it has been registered.

## 2.3 Starting

⟦C7⟧

If it becomes `active (running)`, it has started.

⟦C8⟧

At build time it listened only on `127.0.0.1:8000` and returned `{"status":"ok","service":"ai-defense-manager","version":"0.1.0"}`.

# Chapter 3: Checking over HTTP

> **Run on: VM 230** (run in `/opt/ai-defense-manager`)

## 3.1 Fetching Alerts

Fetch five Wazuh alerts without AI analysis.

⟦C9⟧

At build time five alerts were returned: two Proxmox VE authentication successes, one deletion of a user (group), and one each for the start and end of a PAM login session.

## 3.2 AI Analysis

Pass up to five alerts to `qwen3:8b`. The AI only analyzes and proposes; it does not carry out defensive operations.

⟦C10⟧

At build time it returned `severity: info`, `confidence: 0.8`, `recommended_action: no_action` and `evidence_event_count: 5`.

At this point the following flow is connected.

⟦C11⟧

# Chapter 4: Automatic Start

## 4.1 The Current State

> **Run on: VM 230**

⟦C12⟧

> **Run on: VM 220**

⟦C13⟧

At build time, both were `active` and `disabled` (no automatic start). The Relay starts after the Indexer because of `After=wazuh-indexer.service`.

## 4.2 Enabling It

> **Run on: VM 220**

⟦C14⟧

> **Run on: VM 230**

⟦C15⟧

It is done when both show `enabled`. The running services are not affected.

# Chapter 5: Proxmox Startup Order

Make VM 220 (Wazuh and the Relay) start before VM 230 (the AI Defense Manager).

## 5.1 The Current Settings

> **Run on: pve**

⟦C16⟧

At build time, VM 220 had `onboot: 1` (automatic start) with no order set, and VM 230 had neither automatic start nor an order set.

## 5.2 Setting the Order

Running VMs are not stopped.

- VM 220: automatic start, order 1, wait 120 seconds after starting before the next VM
- VM 230: automatic start, order 2

⟦C17⟧

⟦C18⟧

⟦C19⟧

The results at build time were as follows.

| Item | VM 220 security-core | VM 230 ai-defense-manager |
|---|---|---|
| `onboot` | `1` | `1` |
| `startup` | `order=1,up=120` | `order=2` |

# Closing Notes

After Part 17, the state is as follows.

| Target | State |
|---|---|
| `ai-defense-manager.service` (VM 230) | Running, starts automatically, `127.0.0.1:8000` |
| `ai-defense-relay.service` (VM 220) | Running, starts automatically, `192.168.0.220:8765` |
| Proxmox startup order | VM 220 → wait 120 seconds → VM 230 |

In the next part, we build a mechanism that keeps the results of AI analysis as records.

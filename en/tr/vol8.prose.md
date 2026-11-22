---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 8: Building the Integrated Monitoring Platform"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 8 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". By the end of Part 7, the mechanism for saving Wazuh alerts into PostgreSQL was complete. In Part 8, we collect the state of the servers that make up the defense system themselves (CPU, memory, disk, network) and make it viewable on an integrated Grafana dashboard.

## Notation

- Commands and file contents are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Each step begins with "Run on", which says where to run it.
- "Example output" is the actual output from the build. Numbers of series, times and so on will differ in your environment.

## Monitoring Targets and Policy

The integrated dashboard monitors the following five machines.

| Target | IP address | Role |
|---|---|---|
| Proxmox host `pve` | 192.168.0.240 | Hypervisor |
| VM 220 `security-core` | 192.168.0.220 | Wazuh, Collector |
| LXC 109 `postgresql` | 192.168.0.151 | PostgreSQL (storage for Wazuh events) |
| LXC 103 `lxc-prometheus` | 192.168.0.197 | Prometheus |
| LXC 105 `lxc-grafana` | 192.168.0.199 | Grafana |

- Install Node Exporter on each server, and have Prometheus (LXC 103) collect from them.
- Prometheus forwards the collected data to the existing VictoriaMetrics (Remote Write), which stores it. Grafana reads from VictoriaMetrics.
- Grafana and VictoriaMetrics are not exposed externally. This is an internal-only monitoring platform.
- The LXC 400 series is out of scope. VictoriaMetrics runs on the existing LXC 406, but this book only connects to it at its `vmbr0`-side address `192.168.0.171:8428` and does not change LXC 406's own settings.
- `192.168.1.25` (PostgreSQL and PostgreSQL Exporter of a separate system) is also out of scope.

# Chapter 1: Connecting Grafana and VictoriaMetrics

## 1.1 Checking Grafana's State

**Run on: LXC 105 lxc-grafana (root)**

⟦C0⟧

At build time, Grafana 13.0.2 was `active (running)` and `/api/health` was also normal.

## 1.2 Checking That VictoriaMetrics Is Reachable

From Grafana (`vmbr0`, 192.168.0.0/24), VictoriaMetrics' `vmbr1`-side address (192.168.1.23) cannot be reached. Without changing the network, check whether Grafana can connect to the `vmbr0`-side address `192.168.0.171`.

**Run on: LXC 105 lxc-grafana (root)**

⟦C1⟧

If `/health` returns HTTP 200 (`OK`) and `/api/v1/query` returns `status: success`, the connection works.

## 1.3 Registering the Data Source

Log in to the Grafana web UI (`http://192.168.0.199:3000`) and configure the following.

1. Left menu **Connections → Data sources**
2. **Add data source**
3. Select **Prometheus**
4. Set the following

| Item | Value |
|---|---|
| Name | VictoriaMetrics |
| Prometheus server URL | `http://192.168.0.171:8428` |
| Access | Server (default) |

5. Click **Save & test**

It is done when `Successfully queried the Prometheus API.` is shown.

# Chapter 2: Checking the Current State of the Targets

## 2.1 Data Arriving at VictoriaMetrics

**Run on: LXC 105 lxc-grafana (root)**

⟦C2⟧

At build time there were 11 series, but none of them came from the five machines (they came from out-of-scope servers). CPU, memory and disk data for the five machines was not yet being collected.

## 2.2 Checking the Ports

**Run on: LXC 105 lxc-grafana (root)**

⟦C3⟧

At build time, Node Exporter (9100) was `CLOSED` on all five machines. Checking each server showed that none had Node Exporter installed. From the next chapter, we install it on one server at a time, confirm that it works, and then move on to the next.

# Chapter 3: Installing Node Exporter on the Proxmox Host

## 3.1 Checking the Package

**Run on: Proxmox host pve (root)**

⟦C4⟧

At build time this was Debian 12 (bookworm), and `prometheus-node-exporter 1.5.0-1+b6` from the official repository could be installed.

## 3.2 Installation

As soon as the package is installed, it starts listening on all addresses. So first mask it temporarily to keep it from starting, and then install it.

**Run on: Proxmox host pve (root)**

⟦C5⟧

⟦C6⟧

Check the settings (it does not start yet).

⟦C7⟧

The Debian package takes its startup options from `ARGS` in `/etc/default/prometheus-node-exporter`. Confirm that `MASK STATUS` is `masked-runtime`.

## 3.3 Limiting the Listen Address and Starting

Limit listening to `192.168.0.240:9100` only.

**Run on: Proxmox host pve (root)**

⟦C8⟧

⟦C9⟧

⟦C10⟧

`curl: (23) Failure writing output to destination` appears at the end, but this is because `head` stopped reading after 15 lines; it is not a fault.

## 3.4 Checking Reachability from Prometheus

**Run on: LXC 103 lxc-prometheus (root)**

⟦C11⟧

If `SUCCESS: metrics received` is shown, the metrics are arriving.

# Chapter 4: Adding a Scrape Job to Prometheus

## 4.1 Adding the Job

Leave the existing jobs (`prometheus`, `ollama-gpu`) as they are and add a job for PVE.

**Run on: LXC 103 lxc-prometheus (root)**

⟦C12⟧

Confirm that `SUCCESS` is shown (Prometheus 3.12.0 at build time).

## 4.2 Reloading the Configuration

This Prometheus has reloading through the web API (Lifecycle API) disabled (it returns HTTP 403). The systemd unit has the following setting, so send SIGHUP with `systemctl reload` to reload.

⟦C13⟧

**Run on: LXC 103 lxc-prometheus (root)**

⟦C14⟧

Right after the reload, it may not be shown yet. In that case, check all jobs with the following command.

⟦C15⟧

At build time, all three jobs were `health: up`.

# Chapter 5: Forwarding to VictoriaMetrics (Remote Write)

## 5.1 Checking the Current State and Backing Up

**Run on: LXC 103 lxc-prometheus (root)**

⟦C16⟧

⟦C17⟧

## 5.2 Adding the Forwarding Settings

Add the forwarding destination and a label to identify the source (`prometheus_source`).

**Run on: LXC 103 lxc-prometheus (root)**

⟦C18⟧

In the original build, `promtool` gave an error here. `external_labels` is not a top-level item; it must be placed inside `global`. Move it into `global` with the following command.

⟦C19⟧

⟦C20⟧

## 5.3 Applying and Checking the Forwarding

**Run on: LXC 103 lxc-prometheus (root)**

⟦C21⟧

⟦C22⟧

| Job | Series in VictoriaMetrics (at build time) |
|---|---:|
| `pve-node` | 8,909 |
| `ollama-gpu` | 865 |
| `prometheus` | 791 |

> When searching in VictoriaMetrics, use `job="pve-node"` as the condition, not `host="pve"`. In the original build, searching with `host="pve"` returned 0 results.

## 5.4 Checking the Stored Data

**Run on: LXC 103 lxc-prometheus (root)**

⟦C23⟧

If there is at least one series each for file systems, network and disk I/O, the data needed for the dashboard is in place.

# Chapter 6: Creating the PVE Dashboard

The dashboard is created not in the Grafana UI but from files (provisioning), so that the settings remain as files.

## 6.1 Checking the Data Source UID

The dashboard JSON contains the data source's UID. Open Grafana's database read-only to check it.

**Run on: LXC 105 lxc-grafana (root)**

⟦C24⟧

The UID at build time was `dfsldbphmj9c0e`. Replace `"uid": "dfsldbphmj9c0e"` in the next step with your environment's UID.

## 6.2 Creating the Dashboard and the Provisioning Settings

Create the `PVE Host Overview` dashboard (six panels: CPU, memory, file systems, network, disk I/O and uptime) and the settings that load it. If a file with the same name exists, it stops without overwriting.

**Run on: LXC 105 lxc-grafana (root)**

⟦C25⟧

## 6.3 Fixing the File Owner

6.2 sets the owner to UID 472, but on this LXC the Grafana user `grafana` is UID 102. As it stands Grafana cannot read the JSON, so change the owner to `grafana`.

**Run on: LXC 105 lxc-grafana (root)**

⟦C26⟧

## 6.4 Restarting Grafana and Checking

**Run on: LXC 105 lxc-grafana (root)**

⟦C27⟧

Right after the restart, it may not yet be listening on port 3000, so `/api/health` may be unreachable. Wait a little and then check.

⟦C28⟧

If the log contains `finished to provision dashboards`, loading is complete.

## 6.5 Checking in the UI

In the Grafana UI, open **Dashboards → Infrastructure → PVE Host Overview** and confirm that data is shown in all six panels. At build time, all panels were shown.

# Chapter 7: Adding Monitoring of security-core

Add only Node Exporter, without touching Wazuh itself or its settings.

## 7.1 Checking and Installing

**Run on: security-core VM 220 (root)**

⟦C29⟧

⟦C30⟧

At build time this was Ubuntu 24.04.5 LTS, and the candidate was `1.7.0-1ubuntu0.3`. As with PVE, mask it temporarily before installing.

⟦C31⟧

## 7.2 Limiting the Listen Address and Starting

**Run on: security-core VM 220 (root)**

⟦C32⟧

The temporary mask is in `/run/systemd/system/`, so add `--runtime` when unmasking as well (without it, the mask is not removed and startup is refused).

⟦C33⟧

## 7.3 Checking Reachability from Prometheus

**Run on: LXC 103 lxc-prometheus (root)**

⟦C34⟧

## 7.4 Adding the Job

Add the following job right after the `pve-node` job.

⟦C35⟧

**Run on: LXC 103 lxc-prometheus (root)**

⟦C36⟧

> Because it starts with `set -e`, do not paste this command directly into your interactive shell; start `bash` first or run it as a script. If it fails partway, it exits along with the shell you are logged in to.

## 7.5 Applying and Checking

**Run on: LXC 103 lxc-prometheus (root)**

⟦C37⟧

Right afterwards it shows `health: unknown`. Wait until the first scrape has finished, then check.

⟦C38⟧

⟦C39⟧

At build time, `up` was `1`, there were 64 CPU series, and there were no forwarding errors.

# Chapter 8: Adding Monitoring of PostgreSQL (LXC 109)

Add only Node Exporter, without touching PostgreSQL itself.

## 8.1 Installation

**Run on: LXC 109 postgresql (root)**

⟦C40⟧

At build time this was Debian 13 (trixie), and the candidate was `1.9.0-1+b4`.

⟦C41⟧

⟦C42⟧

Confirm `ARGS=""` and `masked-runtime`.

## 8.2 Limiting the Listen Address and Starting

**Run on: LXC 109 postgresql (root)**

⟦C43⟧

⟦C44⟧

## 8.3 Checking Reachability from Prometheus

**Run on: LXC 103 lxc-prometheus (root)**

⟦C45⟧

## 8.4 Adding and Applying the Job

Add `postgresql-node` after the `security-core` job.

**Run on: LXC 103 lxc-prometheus (root)**

⟦C46⟧

⟦C47⟧

## 8.5 Checking

**Run on: LXC 103 lxc-prometheus (root)**

⟦C48⟧

⟦C49⟧

It is done when it shows `health: up`, `up` is `1`, and `NO REMOTE WRITE ERRORS FOUND` is shown.

# Chapter 9: Adding Monitoring of Prometheus (LXC 103) Itself

So that its port does not overlap with Prometheus (9090), Node Exporter listens on `192.168.0.197:9100`.

## 9.1 Installing and Starting

**Run on: LXC 103 lxc-prometheus (root)**

⟦C50⟧

⟦C51⟧

⟦C52⟧

⟦C53⟧

## 9.2 Adding and Applying the Job

**Run on: LXC 103 lxc-prometheus (root)**

⟦C54⟧

⟦C55⟧

⟦C56⟧

## 9.3 Checking

**Run on: LXC 103 lxc-prometheus (root)**

⟦C57⟧

⟦C58⟧

# Chapter 10: Adding Monitoring of Grafana (LXC 105) Itself

Without changing Grafana itself (port 3000), Node Exporter listens on `192.168.0.199:9100`.

## 10.1 Installing and Starting

**Run on: LXC 105 lxc-grafana (root)**

⟦C59⟧

⟦C60⟧

⟦C61⟧

⟦C62⟧

## 10.2 Checking Reachability from Prometheus

**Run on: LXC 103 lxc-prometheus (root)**

⟦C63⟧

## 10.3 Adding and Applying the Job

This job is added just before `remote_write:` (at the end of the list of jobs).

⟦C64⟧

**Run on: LXC 103 lxc-prometheus (root)**

⟦C65⟧

`marker` matches the fact that, in the configuration file at build time, there were two blank lines before `remote_write:`. Adjust it to the shape of your own file (if the shape differs, it stops without changing anything).

⟦C66⟧

⟦C67⟧

## 10.4 Checking

**Run on: LXC 103 lxc-prometheus (root)**

⟦C68⟧

⟦C69⟧

All five machines are now being monitored.

# Chapter 11: Creating the Integrated Infrastructure Dashboard

Keep the PVE dashboard as it is, and create a new "Integrated Infrastructure Overview" that compares the five machines together. Each host is displayed separately using the `host` label given to it.

## 11.1 Checking the Existing Settings

**Run on: LXC 105 lxc-grafana (root)**

⟦C70⟧

The provisioning settings from 6.2 automatically load every JSON file in `/var/lib/grafana/dashboards` (folder `Infrastructure`). So no settings need to change; you can add a dashboard just by placing a JSON file.

## 11.2 Creating the Dashboard

Create seven panels (host status, CPU, memory, file systems, network, disk I/O and uptime). If a file with the same name exists, it stops without overwriting. Replace `"uid": "dfsldbphmj9c0e"` with your environment's UID checked in 6.1.

**Run on: LXC 105 lxc-grafana (root)**

⟦C71⟧

> Because it starts with `set -e`, start `bash` before running it (same as the note in 7.4).

## 11.3 Checking That It Loaded

Provisioning checks the files every 30 seconds, so there is no need to restart Grafana.

**Run on: LXC 105 lxc-grafana (root)**

⟦C72⟧

If you want to check after some time has passed, widen the log range (set `--since` to when you did the work).

⟦C73⟧

At build time, the log showed that the dashboard search index had grown to `size=3`.

## 11.4 Checking in the UI

In the Grafana UI, open **Dashboards → Infrastructure → Integrated Infrastructure Overview** and confirm that data for all five machines is shown in all seven panels. At build time, all panels were shown.

# Summary of Part 8

## The Completed Monitoring Configuration

| Target | Address | Prometheus job | `host` / `role` |
|---|---|---|---|
| Proxmox host | 192.168.0.240:9100 | `pve-node` | `pve` / `hypervisor` |
| security-core | 192.168.0.220:9100 | `security-core` | `security-core` / `security` |
| PostgreSQL | 192.168.0.151:9100 | `postgresql-node` | `postgresql` / `database` |
| Prometheus | 192.168.0.197:9100 | `prometheus-node` | `prometheus` / `monitoring` |
| Grafana | 192.168.0.199:9100 | `grafana-node` | `grafana` / `visualization` |

Data flow: Node Exporter → Prometheus (LXC 103) → Remote Write → VictoriaMetrics (`192.168.0.171:8428`) → Grafana (LXC 105)

## Dashboards Created

| Dashboard | UID | Panels |
|---|---|---|
| PVE Host Overview | `pve-host-overview` | 6 |
| Integrated Infrastructure Overview | `infra-unified-overview` | 7 |

## Policies Followed

- Each Node Exporter listens only on its own `vmbr0`-side address.
- The existing jobs (`prometheus`, `ollama-gpu`), existing services and the PVE dashboard are not changed.
- Prometheus is not restarted; it reloads its configuration on SIGHUP (`systemctl reload`).
- Grafana and VictoriaMetrics are not exposed externally. The LXC 400 series and `192.168.1.25` are not touched.

## Files Changed

| Server | File |
|---|---|
| All five | `/etc/default/prometheus-node-exporter` |
| LXC 103 | `/etc/prometheus/prometheus.yml` (a backup is made for each change) |
| LXC 105 | `/etc/grafana/provisioning/dashboards/pve.yaml`, `/var/lib/grafana/dashboards/pve-overview.json`, `/var/lib/grafana/dashboards/infrastructure-overview.json` |

---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 33: Monitoring the Collector's State with Prometheus"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 33 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". By Part 32 we had kept the Collector from stopping at log switching and recovered the missing events. Here we build **a way to watch the Collector's state with Prometheus**, so that we notice when the Collector stops or falls behind.

We do not add a new monitoring system; we use what already exists.

- The **Node Exporter** running on VM 220 (`192.168.0.220:9100`) and its **Textfile Collector** (a feature that publishes the numbers in `.prom` files placed in a set directory)
- **Prometheus 3.12.0** on LXC 103 (`lxc-prometheus`), which already collects VM 220's Node Exporter under the job name `security-core`

We build the following.

1. A script that extracts only numbers from the Collector's state and writes them to a `.prom` file (run as root)
2. A systemd service and timer that run it every 15 seconds
3. Prometheus alert rules (9 of them)

The Collector's state file (`state.json`) can be read and written only by `wazuh-collector` (directory `0700`, file `0600`). We keep this restriction and let Node Exporter (the `prometheus` user) read a file containing only numbers.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **pve**: the Proxmox host (root). Commands inside LXC 103 (`lxc-prometheus`, 192.168.0.197) are run with `pct exec 103 -- bash -lc '…'`

# Chapter 1: Investigating the Existing Monitoring

## 1.1 Services and Timers

> **Run on: VM 220**

⟦C0⟧

| Item | State |
|---|---|
| Collector | `active` / `running`, 0 restarts |
| Automatic restart | `Restart=always`, up to 5 times in 10 seconds |
| Node Exporter | Running |
| AI Defense Relay | Running |

## 1.2 Listening Ports

⟦C1⟧

Node Exporter was listening on `192.168.0.220:9100`, the Relay on `192.168.0.220:8765`, and Wazuh Indexer on `127.0.0.1:9200`.

## 1.3 The Relay's `/health`

Check whether the Relay's `/health` can also show the Collector's state.

⟦C2⟧

⟦C3⟧

`/health` only returned the following fixed answer.

⟦C4⟧

It only tells us that the Relay itself is answering, not the state of the Collector or PostgreSQL. We leave the Relay as it is and use Node Exporter.

## 1.4 Node Exporter's Settings

⟦C5⟧

(`806` is Node Exporter's PID shown in 1.2.)

⟦C6⟧

Node Exporter runs as the `prometheus` user. The Collector's state file is `drwx------ wazuh-collector:wazuh-collector` (directory) and `-rw------- wazuh-collector:wazuh-collector` (file), so Node Exporter cannot read it directly.

⟦C7⟧

Node Exporter was 1.7.0, and the Textfile Collector was already enabled. The directory it reads is `/var/lib/prometheus/node-exporter`, which already held `apt.prom`, `nvme.prom` and `smartmon.prom`. Placing a file there adds numbers without restarting Node Exporter.

## 1.5 Checking Permissions

⟦C8⟧

⟦C9⟧

The results were `0` (readable), `0` (traversable) and `1` (not writable). Node Exporter can read a file written by root without being given write permission.

## 1.6 The Collector's Unit and the Shape of the State File

Without showing the state file's values, check only its shape.

⟦C10⟧

⟦C11⟧

# Chapter 2: A Script That Writes Out the Numbers

## 2.1 The Numbers to Publish

| Metric | Meaning |
|---|---|
| `wazuh_collector_service_up` | Whether the Collector is running (1/0) |
| `wazuh_collector_restarts_total` | Number of restarts by systemd |
| `wazuh_collector_state_valid` | Whether the state file has the correct shape (1/0) |
| `wazuh_collector_inode_match` | Whether the state file's inode matches the current `alerts.json` (1/0) |
| `wazuh_collector_unread_bytes` | Unread bytes (-1 when unknown) |
| `wazuh_collector_state_mtime_seconds` | Modification time of the state file |

Alert contents, IP addresses and connection details are not published. The script writes to a temporary file and then replaces (`os.replace`); if it fails midway it also deletes the old `.prom`, so that normal-looking values do not remain.

## 2.2 Creating the Script

In the original build, approval was obtained before running this.

> **Run on: VM 220**

⟦C12⟧

`SCRIPT_SYNTAX_EXIT=0` and `-rwxr-xr-x root:root`.

## 2.3 Running It Once

⟦C13⟧

The file contained `wazuh_collector_service_up 1`, `restarts_total 0`, `state_valid 1`, `inode_match 1` and `unread_bytes 0`, and the `prometheus` user could read it (`PROMETHEUS_READ_EXIT=0`).

# Chapter 3: Running It Every 15 Seconds

## 3.1 The Service

It runs as root, but where it can read and write is narrowed (the state file and the alerts directory are read-only; only the `.prom` directory is writable).

⟦C14⟧

## 3.2 The Timer

⟦C15⟧

Both gave `VERIFY_EXIT=0`.

## 3.3 Enabling It

⟦C16⟧

⟦C17⟧

The service finished with `status=0/SUCCESS`, and the timer was `active (waiting)`.

> **Note**: The next run time in `systemctl list-timers` may be shown as `-`. Because `OnUnitActiveSec` is measured from the previous run (on the monotonic clock), `NextElapseUSecRealtime` is empty and the value goes into `NextElapseUSecMonotonic` instead. This is not abnormal.

## 3.4 Visible from Node Exporter?

⟦C18⟧

The `wazuh_collector_` numbers appeared in Node Exporter's `/metrics`, and `node_scrape_collector_success{collector="textfile"}` was 1. The `.prom` file was also being rewritten every 15 seconds.

# Chapter 4: Ingesting into Prometheus

## 4.1 Where Prometheus Is

Prometheus runs in LXC 103 on Proxmox. If you run Prometheus commands directly on the Proxmox host (`root@pve`), neither the configuration file nor `promtool` will be found. Check with the list of LXCs.

> **Run on: pve**

⟦C19⟧

LXC 103 was `lxc-prometheus`.

## 4.2 The Collection Settings

⟦C20⟧

Prometheus was running, and `192.168.0.220:9100` was already registered as job `security-core`. The configuration check was also `SUCCESS`. The new numbers are ingested without changing Prometheus's settings.

⟦C21⟧

All five were ingested with the labels `job="security-core"` and `instance="192.168.0.220:9100"`.

## 4.3 The Current Alert Settings

⟦C22⟧

`rule_files` was still commented out (no rules), and Alertmanager was not running either. With rules added, alerts can be seen in Prometheus's screens (notifications such as e-mail are not delivered until Alertmanager is set up; we do not set up notifications this time).

# Chapter 5: Alert Rules

## 5.1 Checks Before Creating

In the original build, approval was obtained before adding the rules.

⟦C23⟧

Prometheus was 3.12.0 and the evaluation interval was 15 seconds. `/etc/prometheus/rules` did not exist yet, nor did a file with the same name.

## 5.2 The Rule File

| Alert | Condition |
|---|---|
| `WazuhCollectorDown` | The Collector has been stopped for 1 minute or more |
| `WazuhCollectorStateInvalid` | The state file has been invalid for 1 minute or more |
| `WazuhCollectorInodeMismatch` | The inode has not matched for 1 minute or more |
| `WazuhCollectorBacklog` | Unread data has exceeded 1 MiB for 2 minutes or more |
| `WazuhCollectorRestarted` | The restart count increased within 5 minutes |
| `WazuhCollectorMetricsStale` | The `.prom` file has not been rewritten for 60 seconds or more |
| `WazuhCollectorMetricsMissing` | The Collector's numbers have not arrived for 1 minute or more |
| `SecurityCoreNodeExporterDown` | Node Exporter could not be scraped for 1 minute or more |
| `SecurityCoreTargetMissing` | The scrape target `security-core` itself has been absent for 1 minute or more |

> **Run on: pve**

⟦C24⟧

The file was created as `root:root`, `0644`.

## 5.3 Checking the Rules

> **Caution**: Running it directly, as in `pct exec 103 -- promtool …`, fails with `Failed to exec "promtool"` (exit code 127) because `promtool` is not found in the PATH. Run it through `bash -lc`.

⟦C25⟧

`SUCCESS: 9 rules found` and `RULE_CHECK_EXIT=0`.

## 5.4 Registering in the Prometheus Configuration

Back up the configuration file, then replace only the commented-out `rule_files` part. If the part to replace is not found exactly once, nothing is changed.

⟦C26⟧

`CONFIG_EDIT: SUCCESS`, and both the configuration and rule checks were `SUCCESS`. Under `rule_files:` there is now `- "/etc/prometheus/rules/*.yml"`.

## 5.5 Reloading Without a Restart

⟦C27⟧

`CanReload=yes`, with `ExecReload=/bin/kill -HUP $MAINPID` (sending SIGHUP).

⟦C28⟧

Prometheus stayed `active`, its PID stayed `98`, and `Completed loading of configuration file` appeared in the log.

## 5.6 Were the Rules Registered?

⟦C29⟧

`RULE_COUNT: 9`; all 9 had `health` `ok` and `state` `inactive` (nothing abnormal at present), and `ACTIVE_ALERT_COUNT: 0`.

# Closing Notes

In Part 33 we made the Collector's state observable with Prometheus.

| Item | Result |
|---|---|
| Script that writes the numbers | `/usr/local/sbin/wazuh-collector-metrics.py` (root, `0755`) |
| Output | `/var/lib/prometheus/node-exporter/wazuh_collector.prom` (`0644`, 6 numbers) |
| Scheduled runs | `wazuh-collector-metrics.service` (oneshot) and `.timer` (every 15 seconds) |
| Permissions | The state file's restriction is unchanged; Node Exporter only reads |
| Prometheus | LXC 103; ingested under job `security-core`; configuration backup `prometheus.yml.pre-wazuh-rules-20261122` |
| Alert rules | `/etc/prometheus/rules/wazuh-collector-alerts.yml` (9 rules, all `ok`, `inactive`) |
| Notifications | Alertmanager not set up (not done this time) |

In Part 34 we use the same approach to watch the state of the Wazuh platform itself (Manager, Indexer, Dashboard and API).

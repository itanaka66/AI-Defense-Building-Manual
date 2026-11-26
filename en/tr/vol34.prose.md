---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 34: Monitoring the Wazuh Platform's State with Prometheus"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 34 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". In Part 33 we made the Collector's state observable with Prometheus. Here we use the same approach (Node Exporter's Textfile Collector and the Prometheus on LXC 103) to watch **the Wazuh platform itself**.

| What we watch | How |
|---|---|
| Wazuh Manager | Whether the 9 required daemons are running |
| Wazuh Indexer | Whether `https://127.0.0.1:9200/` answers (401 also counts as normal) |
| Wazuh Dashboard | Whether `https://127.0.0.1:443/` answers (302 also counts as normal) |
| Wazuh API | Whether `https://127.0.0.1:55000/` answers (401 also counts as normal) |

No credentials are put into the script; only the HTTP status of the answer is checked. 401 (authentication required) and 302 (redirect) are also counted as normal, as evidence that the service is answering.

Along the way, a version that checked the Manager with `wazuh-control status` failed when run by the timer, because it waited on a lock for more than 10 seconds. We solve this by changing it to look at Wazuh's PID files directly.

Finally, we add 7 alert rules for the Wazuh platform, making 16 rules together with the 9 for the Collector.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **pve**: the Proxmox host (root). Commands inside LXC 103 are run with `pct exec 103 -- bash -lc '…'`

# Chapter 1: Investigating the Current State

The monitoring configuration so far is as follows.

⟦C0⟧

## 1.1 Services and Disks

> **Run on: VM 220**

⟦C1⟧

Wazuh Manager, Indexer, Dashboard, Filebeat and the Collector were all running. The root file system was 12% used, and about 12 GiB of memory was available.

## 1.2 The Manager's Daemons and Ports

⟦C2⟧

`wazuh-analysisd`, `wazuh-remoted` (1514), `wazuh-authd` (1515) and others were running, and the API (55000), Indexer (9200, 9300) and Dashboard (443) were listening. `wazuh-clusterd`, `wazuh-maild`, `wazuh-agentlessd` and others were stopped, but these do not run unless their features are used; this is not abnormal.

## 1.3 HTTP Answers

⟦C3⟧

The Indexer answered 401 and the Dashboard 302. The API gave no answer (`000`) because the request used `http://`; the API listens on HTTPS, so check again with HTTPS.

⟦C4⟧

`HTTP_STATUS=401`. All three are answering.

## 1.4 Existing Monitoring Tools

⟦C5⟧

There were four `.prom` files: `apt.prom`, `nvme.prom`, `smartmon.prom` and `wazuh_collector.prom`.

⟦C6⟧

The new script is built the same way as the one in Part 33: run as root, write only numbers to a temporary file and then replace.

⟦C7⟧

The exit code of `wazuh-control status` was `1`. This is because its judgment includes optional daemons that are stopped; it does not mean the whole Manager is abnormal. The monitoring checks only the required daemons, one by one.

⟦C8⟧

`node_scrape_collector_success{collector="textfile"}` was 1, and all four files were being read. Node Exporter's startup arguments do not need to change. For disks and memory, Node Exporter's standard numbers are used as they are.

# Chapter 2: A Script That Writes Out the Wazuh Platform's Numbers

In the original build, approval was obtained before creating it.

## 2.1 Creating the Script

> **Run on: VM 220**

⟦C9⟧

`SYNTAX_EXIT=0` and `-rwxr-xr-x root:root`. Pasting long content can garble the terminal display, so check the file's contents with line numbers.

⟦C10⟧

It was 150 lines, as intended.

## 2.2 Running It Once

⟦C11⟧

`wazuh_manager_up 1`, all 9 daemons 1, `wazuh_indexer_up 1` (401), `wazuh_dashboard_up 1` (302) and `wazuh_api_up 1` (401). The file was `-rw-r--r-- root:root`, 1,446 bytes.

## 2.3 Service and Timer

⟦C12⟧

`VERIFY_EXIT=0`. The pasted display was garbled here too, so check the contents.

⟦C13⟧

Both were written correctly, and `TIMER_VERIFY_EXIT=0`. Enable the timer.

⟦C14⟧

It became `active` and `enabled`.

# Chapter 3: Failing When Run by the Timer

## 3.1 Finding the Failure

⟦C15⟧

The service had failed, and the log contained the following error. The `.prom` file had not been rewritten either.

⟦C16⟧

⟦C17⟧

Wazuh Manager was `active` / `running`, and the 9 daemons were running. What was stuck was `/bin/sh /var/ossec/bin/wazuh-control status`, waiting for an answer.

## 3.2 Stopping Only the Monitoring Service

While investigating, stop only the monitoring timer and service. Wazuh Manager and the Collector are not stopped.

⟦C18⟧

The timer stopped, but the service that had already started (`activating`) and `wazuh-control status` remained.

⟦C19⟧

The service became `failed`, and no processes remained.

## 3.3 Investigating the Cause

⟦C20⟧

`status` first takes a lock and then checks all daemons.

⟦C21⟧

It **waits up to 60 seconds** for the lock, exceeding the script's 10-second limit. The monitoring has no need to call `wazuh-control`. Check how Wazuh itself checks daemon state (PID files).

⟦C22⟧

All 9 daemons had a `wazuh-<name>-<PID>.pid` file, and the PIDs matched the process list. `pstatus()` simply reads the PID file and checks with `kill -0` that the process is alive.

# Chapter 4: Changing It to Look at PID Files

## 4.1 Replacing the Function

Replace only `manager_status()` with a version that checks the PID files and `os.kill(pid, 0)`. The HTTP checks and the writing code stay as they are.

In the original build, the script was first backed up with the following command, and then a regular-expression replacement was attempted.

`cp -a /usr/local/sbin/wazuh-platform-metrics.py /usr/local/sbin/wazuh-platform-metrics.py.pre-pid-check-20261122`

At that time the replacement failed because of a mistake in the regular expression, and the script was not changed (the backup was made). So, without regular expressions, we replace from the start of the function to the start of the next function.

> **Run on: VM 220**

⟦C23⟧

`REPLACEMENT=SUCCESS` and `SYNTAX_EXIT=0`.

## 4.2 Testing the Fixed Script

The timer stays stopped.

⟦C24⟧

`SCRIPT_EXIT=0`, with `wazuh_manager_up 1`, all 9 daemons 1, and all three HTTP checks `up 1`.

Test whether it also works under systemd's restrictions.

⟦C25⟧

`START_EXIT=0`, `Result=success` and `ExecMainStatus=0` (for a oneshot, becoming `inactive` / `dead` after finishing is normal).

## 4.3 Restoring the Timer

⟦C26⟧

After a short while, check that it keeps running.

⟦C27⟧

The timer was `active` / `waiting`, the service `success`, and the `.prom` file was being rewritten every 15 seconds.

## 4.4 Visible from Node Exporter?

> **Caution**: Node Exporter listens on `192.168.0.220:9100`, not `127.0.0.1`. `http://127.0.0.1:9100/metrics` cannot connect.

⟦C28⟧

`wazuh_manager_up`, the 9 `wazuh_manager_daemon_up` series, `wazuh_indexer_up`, `wazuh_dashboard_up`, `wazuh_api_up` and others were shown.

# Chapter 5: Ingesting into Prometheus

## 5.1 Were They Ingested?

> **Run on: pve** (run at `root@pve:~#`; `pct` cannot be used on VM 220)

⟦C29⟧

All were `status=success` with value `1`, ingested with `job="security-core"` and `instance="192.168.0.220:9100"`. Prometheus's settings were not changed.

⟦C30⟧

There were 9 `wazuh_manager_daemon_up` series, all 1, and `count(wazuh_manager_daemon_up)` was `9`.

# Chapter 6: Alert Rules for the Wazuh Platform

In the original build, approval was obtained before adding the rules.

## 6.1 The Current Rules

⟦C31⟧

Following the naming and labels of the Collector rules (Part 33), we add them in a separate file, `/etc/prometheus/rules/wazuh-platform-alerts.yml`. `rule_files` is `/etc/prometheus/rules/*.yml`, so the file is loaded without changing Prometheus's settings.

## 6.2 The Rule File

| Rule | Condition | Severity |
|---|---|---|
| `WazuhManagerDown` | The Manager has been stopped for 1 minute | critical |
| `WazuhManagerDaemonDown` | A required daemon has been stopped for 1 minute | critical |
| `WazuhIndexerDown` | The Indexer has not answered for 1 minute | critical |
| `WazuhDashboardDown` | The Dashboard has not answered for 1 minute | warning |
| `WazuhAPIDown` | The API has not answered for 1 minute | critical |
| `WazuhPlatformMetricsMissing` | The numbers have not arrived for 1 minute | critical |
| `WazuhPlatformMetricsStale` | The `.prom` file has not been rewritten for over 60 seconds | critical |

If a file with the same name exists, it stops without overwriting.

⟦C32⟧

It was created as `-rw-r--r-- root:root 2823 bytes`.

## 6.3 Checking and Loading

⟦C33⟧

The Wazuh platform rules gave `SUCCESS: 7 rules found`; the whole-configuration check also read the Collector rules (9) and the two files, and all exit codes were 0.

⟦C34⟧

`RELOAD_EXIT=0`; Prometheus was `active`, its PID stayed `98`, and `Completed loading of configuration file` appeared.

## 6.4 Checking the 16 Rules

⟦C35⟧

| Group | Rules | State |
|---|---:|---|
| `wazuh-collector` | 9 | All `health=ok`, `state=inactive` |
| `wazuh-platform` | 7 | All `health=ok`, `state=inactive` |

`ACTIVE_ALERT_COUNT: 0`. `inactive` means that no rule's condition is currently met.

# Closing Notes

In Part 34 we made the state of the Wazuh platform itself observable with Prometheus too.

| Item | Result |
|---|---|
| Script | `/usr/local/sbin/wazuh-platform-metrics.py` (root, `0755`); backup `wazuh-platform-metrics.py.pre-pid-check-20261122` |
| How the Manager is checked | PID files and `kill -0` instead of `wazuh-control status` (does not touch Wazuh's lock) |
| Output | `/var/lib/prometheus/node-exporter/wazuh_platform.prom` |
| Scheduled runs | `wazuh-platform-metrics.service` (oneshot) and `.timer` (every 15 seconds) |
| Prometheus | Ingested without changing settings; rule file `/etc/prometheus/rules/wazuh-platform-alerts.yml` (7 rules) |
| Total rules | Collector 9 + Wazuh platform 7 = 16, all `ok`, `inactive`, 0 firing |
| Notifications | Alertmanager not set up |

In Part 35 we test, without stopping production services, whether the rules fire correctly with test data, and check the production values.

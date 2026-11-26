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

```bash
pct exec 103 -- bash -lc '
echo "===== PROMETHEUS VERSION ====="
promtool --version

echo
echo "===== RULE TEST HELP ====="
promtool test rules --help
'
```

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

```bash
pct exec 103 -- bash -lc '
cat > /tmp/wazuh-platform-alerts.test.yml <<'"'"'YAML'"'"'
rule_files:
  - /etc/prometheus/rules/wazuh-platform-alerts.yml

evaluation_interval: 15s

tests:
  - name: normal-no-alerts
    interval: 15s
    input_series:
      - series: wazuh_manager_up{job="security-core"}
        values: "1+0x8"
      - series: wazuh_manager_daemon_up{job="security-core",daemon="wazuh-analysisd"}
        values: "1+0x8"
      - series: wazuh_indexer_up{job="security-core"}
        values: "1+0x8"
      - series: wazuh_dashboard_up{job="security-core"}
        values: "1+0x8"
      - series: wazuh_api_up{job="security-core"}
        values: "1+0x8"
      - series: node_textfile_mtime_seconds{job="security-core",file="/var/lib/prometheus/node-exporter/wazuh_platform.prom"}
        values: "120+0x8"
    alert_rule_test:
      - eval_time: 2m
        alertname: WazuhManagerDown
        exp_alerts: []
      - eval_time: 2m
        alertname: WazuhManagerDaemonDown
        exp_alerts: []
      - eval_time: 2m
        alertname: WazuhIndexerDown
        exp_alerts: []
      - eval_time: 2m
        alertname: WazuhDashboardDown
        exp_alerts: []
      - eval_time: 2m
        alertname: WazuhAPIDown
        exp_alerts: []
      - eval_time: 2m
        alertname: WazuhPlatformMetricsMissing
        exp_alerts: []
      - eval_time: 2m
        alertname: WazuhPlatformMetricsStale
        exp_alerts: []

  - name: service-down-alerts
    interval: 15s
    input_series:
      - series: wazuh_manager_up{job="security-core"}
        values: "0+0x8"
      - series: wazuh_manager_daemon_up{job="security-core",daemon="wazuh-analysisd"}
        values: "0+0x8"
      - series: wazuh_indexer_up{job="security-core"}
        values: "0+0x8"
      - series: wazuh_dashboard_up{job="security-core"}
        values: "0+0x8"
      - series: wazuh_api_up{job="security-core"}
        values: "0+0x8"
    alert_rule_test:
      - eval_time: 1m
        alertname: WazuhManagerDown
        exp_alerts:
          - exp_labels:
              job: security-core
              severity: critical
              component: wazuh-manager
      - eval_time: 1m
        alertname: WazuhManagerDaemonDown
        exp_alerts:
          - exp_labels:
              job: security-core
              daemon: wazuh-analysisd
              severity: critical
              component: wazuh-manager
      - eval_time: 1m
        alertname: WazuhIndexerDown
        exp_alerts:
          - exp_labels:
              job: security-core
              severity: critical
              component: wazuh-indexer
      - eval_time: 1m
        alertname: WazuhDashboardDown
        exp_alerts:
          - exp_labels:
              job: security-core
              severity: warning
              component: wazuh-dashboard
      - eval_time: 1m
        alertname: WazuhAPIDown
        exp_alerts:
          - exp_labels:
              job: security-core
              severity: critical
              component: wazuh-api

  - name: metrics-missing-alert
    interval: 15s
    input_series:
      - series: wazuh_manager_up{job="security-core"}
        values: "1+0x8"
      - series: wazuh_indexer_up{job="security-core"}
        values: "1+0x8"
      - series: wazuh_dashboard_up{job="security-core"}
        values: "1+0x8"
    alert_rule_test:
      - eval_time: 1m
        alertname: WazuhPlatformMetricsMissing
        exp_alerts:
          - exp_labels:
              job: security-core
              severity: critical
              component: wazuh-platform

  - name: metrics-stale-alert
    interval: 15s
    input_series:
      - series: node_textfile_mtime_seconds{job="security-core",file="/var/lib/prometheus/node-exporter/wazuh_platform.prom"}
        values: "0+0x8"
    alert_rule_test:
      - eval_time: 2m
        alertname: WazuhPlatformMetricsStale
        exp_alerts:
          - exp_labels:
              job: security-core
              file: /var/lib/prometheus/node-exporter/wazuh_platform.prom
              severity: critical
              component: wazuh-platform
YAML

echo "===== TEST FILE SYNTAX CHECK ====="
python3 -c "import yaml; yaml.safe_load(open(\"/tmp/wazuh-platform-alerts.test.yml\")); print(\"YAML_SYNTAX=OK\")"
echo "===== TEST FILE DETAILS ====="
stat -c "%A %U:%G %s bytes %n" /tmp/wazuh-platform-alerts.test.yml
'
```

The file was created as `-rw-r--r-- root:root 4001 bytes`. The final YAML check in Python gives `ModuleNotFoundError: No module named 'yaml'` because `python3-yaml` is not installed in LXC 103, but this is not a problem. The YAML is read by the next command, `promtool test rules` (no packages are added).

# Chapter 2: Testing the Rules

## 2.1 First Run

```bash
pct exec 103 -- bash -lc '
echo "===== PROMETHEUS RULE UNIT TEST ====="
promtool test rules /tmp/wazuh-platform-alerts.test.yml
echo "PROMTOOL_TEST_EXIT=$?"
'
```

It was `FAILED` (`PROMTOOL_TEST_EXIT=1`). Looking at the details, **all 7 abnormal-case rules fired as expected**, and the normal case's "does not fire" also matched. The mismatch was because the test file did not specify `exp_annotations` (`summary` and `description`). promtool also compares the annotations attached to the actual alert.

## 2.2 Adding the Expected Annotations

First, read the relevant part of the test file.

```bash
pct exec 103 -- bash -lc '
echo "===== TEST FILE: ALERT EXPECTATIONS ====="
grep -n -A12 -B2 "alertname:\|exp_alerts:" /tmp/wazuh-platform-alerts.test.yml
'
```

In the abnormal cases, the expectations are under `exp_labels`. Add `exp_annotations` at the same level. The normal case's `exp_alerts: []` stays as it is. The annotation texts are the same as in the production rules (Part 34).

```bash
pct exec 103 -- bash -lc '
python3 - <<'"'"'PY'"'"'
from pathlib import Path

p = Path("/tmp/wazuh-platform-alerts.test.yml")
lines = p.read_text().splitlines()

annotations = {
    "WazuhManagerDown": (
        "Wazuh Manager is not running",
        "Wazuh Manager has been unavailable for at least 1 minute."
    ),
    "WazuhManagerDaemonDown": (
        "A required Wazuh Manager daemon is down",
        "A required Wazuh Manager daemon has been down for at least 1 minute. Check the daemon label."
    ),
    "WazuhIndexerDown": (
        "Wazuh Indexer is unreachable",
        "Wazuh Indexer health endpoint has failed for at least 1 minute."
    ),
    "WazuhDashboardDown": (
        "Wazuh Dashboard is unreachable",
        "Wazuh Dashboard endpoint has failed for at least 1 minute."
    ),
    "WazuhAPIDown": (
        "Wazuh API is unreachable",
        "Wazuh API endpoint has failed for at least 1 minute."
    ),
    "WazuhPlatformMetricsMissing": (
        "Wazuh Platform metrics are missing",
        "One or more Wazuh Platform health metrics have been absent from Prometheus for at least 1 minute."
    ),
    "WazuhPlatformMetricsStale": (
        "Wazuh Platform metrics file is stale",
        "The Wazuh Platform metrics textfile has not been updated for more than 60 seconds."
    ),
}

out = []
current = None
added = set()

for line in lines:
    out.append(line)
    stripped = line.strip()

    if stripped.startswith("alertname: "):
        current = stripped.split(": ", 1)[1]

    if current in annotations and stripped.startswith("component: "):
        summary, description = annotations[current]
        out.extend([
            "            exp_annotations:",
            "              summary: " + summary,
            "              description: " + description
        ])
        added.add(current)
        current = None

missing = set(annotations) - added
if missing:
    raise RuntimeError("Could not update: " + ", ".join(sorted(missing)))

p.write_text("\n".join(out) + "\n")
print("ANNOTATIONS_ADDED:", len(added))
PY

echo "===== ANNOTATION COUNT ====="
grep -c "exp_annotations:" /tmp/wazuh-platform-alerts.test.yml
echo "===== UPDATED EXPECTATIONS ====="
grep -n -A8 "alertname: WazuhManagerDown" /tmp/wazuh-platform-alerts.test.yml
'
```

`ANNOTATIONS_ADDED: 7`, and the count of `exp_annotations:` was also `7`.

## 2.3 Second Run

Test with the same command as the first run.

```bash
pct exec 103 -- bash -lc '
echo "===== PROMETHEUS RULE UNIT TEST ====="
promtool test rules /tmp/wazuh-platform-alerts.test.yml
echo "PROMTOOL_TEST_EXIT=$?"
'
```

```text
===== PROMETHEUS RULE UNIT TEST =====
  SUCCESS

PROMTOOL_TEST_EXIT=0
```

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

```bash
pct exec 103 -- python3 -c '
import json, urllib.request, urllib.parse

base = "http://127.0.0.1:9090"

def get(path, params=None):
    url = base + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.load(r)["data"]

def query(expr):
    return get("/api/v1/query", {"query": expr})["result"]

print("===== SECURITY-CORE SCRAPE =====")
for x in query("up{job=\"security-core\"}"):
    print(x["metric"].get("instance"), "UP=", x["value"][1])

print("===== WAZUH PLATFORM HEALTH =====")
for metric in ["wazuh_manager_up", "wazuh_indexer_up", "wazuh_dashboard_up", "wazuh_api_up"]:
    for x in query(metric + "{job=\"security-core\"}"):
        print(metric, "=", x["value"][1])

print("===== MANAGER DAEMONS =====")
daemons = query("wazuh_manager_daemon_up{job=\"security-core\"}")
print("DAEMON_COUNT:", len(daemons))
for x in sorted(daemons, key=lambda x: x["metric"].get("daemon", "")):
    print(x["metric"].get("daemon"), "=", x["value"][1])

print("===== PLATFORM METRICS AGE =====")
expr = "time() - node_textfile_mtime_seconds{job=\"security-core\",file=\"/var/lib/prometheus/node-exporter/wazuh_platform.prom\"}"
for x in query(expr):
    print("AGE_SECONDS:", x["value"][1])

print("===== LOADED ALERT RULES =====")
rules = get("/api/v1/rules", {"type": "alert"})
total = 0
for group in rules["groups"]:
    total += len(group["rules"])
    print("GROUP:", group["name"], "RULES:", len(group["rules"]))
    for rule in group["rules"]:
        print(rule["name"], "health=", rule.get("health"), "state=", rule.get("state"))
print("TOTAL_ALERT_RULES:", total)

print("===== ACTIVE ALERTS =====")
alerts = get("/api/v1/alerts")["alerts"]
active = [a for a in alerts if a.get("state") == "firing"]
print("FIRING_ALERT_COUNT:", len(active))
for alert in active:
    print(alert.get("labels", {}).get("alertname"), alert.get("labels", {}))
'
```

| Item | Actual value |
|---|---|
| Node Exporter (`192.168.0.220:9100`) | `UP= 1` |
| Wazuh Manager, Indexer, Dashboard, API | All `1` |
| Manager daemons | All 9 `1` |
| Age of `wazuh_platform.prom` | About 16.3 seconds |
| Alert rules | 16 (all `health=ok`, `state=inactive`) |
| Firing alerts | 0 |

## 3.2 The Collector's Values

```bash
pct exec 103 -- python3 -c '
import json, urllib.request, urllib.parse

base = "http://127.0.0.1:9090"
metrics = [
    "wazuh_collector_service_up",
    "wazuh_collector_restarts_total",
    "wazuh_collector_state_valid",
    "wazuh_collector_inode_match",
    "wazuh_collector_unread_bytes",
    "wazuh_collector_state_mtime_seconds",
]

for metric in metrics:
    params = urllib.parse.urlencode({"query": metric + "{job=\"security-core\"}"})
    url = base + "/api/v1/query?" + params
    with urllib.request.urlopen(url, timeout=5) as r:
        result = json.load(r)["data"]["result"]
    print("===== " + metric + " =====")
    if not result:
        print("MISSING")
    for item in result:
        print("value=", item["value"][1])
'
```

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

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

```bash
echo "===== MONITORING SERVICES ====="
systemctl list-units --type=service --all --no-pager | grep -Ei 'wazuh|prometheus|victoria|grafana|node.exporter|zabbix|monitor' || true

echo "===== SYSTEMD TIMERS ====="
systemctl list-timers --all --no-pager

echo "===== COLLECTOR SERVICE CONFIG ====="
systemctl show wazuh-collector.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts \
  -p Restart -p RestartUSec -p StartLimitBurst -p StartLimitIntervalUSec
```

| Item | State |
|---|---|
| Collector | `active` / `running`, 0 restarts |
| Automatic restart | `Restart=always`, up to 5 times in 10 seconds |
| Node Exporter | Running |
| AI Defense Relay | Running |

## 1.2 Listening Ports

```bash
echo "===== NODE EXPORTER ====="
systemctl status prometheus-node-exporter.service --no-pager -l

echo "===== AI DEFENSE RELAY ====="
systemctl status ai-defense-relay.service --no-pager -l

echo "===== LISTENING PORTS ====="
ss -lntp | grep -E ':(9100|9200|5601|8000|9090|9187)\b' || true
```

Node Exporter was listening on `192.168.0.220:9100`, the Relay on `192.168.0.220:8765`, and Wazuh Indexer on `127.0.0.1:9200`.

## 1.3 The Relay's `/health`

Check whether the Relay's `/health` can also show the Collector's state.

```bash
echo "===== RELAY ROUTES AND HEALTH FUNCTIONS ====="
grep -nE '(^@app|@.*route|def health|def metrics|health|metrics|prometheus|8765)' \
  /opt/ai-defense-relay/relay.py
```

```bash
sed -n '1,150p' /opt/ai-defense-relay/relay.py
```

`/health` only returned the following fixed answer.

```json
{"status": "ok"}
```

It only tells us that the Relay itself is answering, not the state of the Collector or PostgreSQL. We leave the Relay as it is and use Node Exporter.

## 1.4 Node Exporter's Settings

```bash
echo "===== NODE EXPORTER UNIT ====="
systemctl cat prometheus-node-exporter.service

echo "===== NODE EXPORTER COMMAND LINE ====="
tr '\0' ' ' < /proc/806/cmdline
echo

echo "===== TEXTFILE COLLECTOR DIRECTORIES ====="
find /etc/prometheus /var/lib/prometheus \
  -maxdepth 3 -type d -iname '*textfile*' -print 2>/dev/null
```

(`806` is Node Exporter's PID shown in 1.2.)

```bash
echo "===== EXPORTER DEFAULT CONFIG ====="
cat /etc/default/prometheus-node-exporter

echo "===== PROMETHEUS DIRECTORIES ====="
ls -ld /etc/prometheus /var/lib/prometheus 2>&1

echo "===== EXPORTER USER ====="
id prometheus

echo "===== COLLECTOR STATE PERMISSIONS ====="
stat -c '%A %U:%G %n' \
  /var/lib/wazuh-collector \
  /var/lib/wazuh-collector/state.json
```

Node Exporter runs as the `prometheus` user. The Collector's state file is `drwx------ wazuh-collector:wazuh-collector` (directory) and `-rw------- wazuh-collector:wazuh-collector` (file), so Node Exporter cannot read it directly.

```bash
echo "===== NODE EXPORTER VERSION ====="
/usr/bin/prometheus-node-exporter --version

echo "===== TEXTFILE COLLECTOR OPTION ====="
/usr/bin/prometheus-node-exporter --help 2>&1 | grep -A3 -B2 textfile

echo "===== PROMETHEUS DATA DIRECTORY ====="
find /var/lib/prometheus -maxdepth 3 -printf '%M %u:%g %p\n'
```

Node Exporter was 1.7.0, and the Textfile Collector was already enabled. The directory it reads is `/var/lib/prometheus/node-exporter`, which already held `apt.prom`, `nvme.prom` and `smartmon.prom`. Placing a file there adds numbers without restarting Node Exporter.

## 1.5 Checking Permissions

```bash
echo "===== TEXTFILE DIRECTORY PERMISSIONS ====="
namei -l /var/lib/prometheus/node-exporter

echo "===== EXISTING METRIC FILES ====="
ls -l /var/lib/prometheus/node-exporter/

echo "===== NODE EXPORTER TEXTFILE METRICS ====="
curl -fsS http://192.168.0.220:9100/metrics \
  | grep -E '^(node_textfile_|node_scrape_collector_success)' \
  | head -40

echo "===== COLLECTOR STATE FILE METADATA ====="
stat -c 'mtime=%y size=%s mode=%a owner=%U:%G' \
  /var/lib/wazuh-collector/state.json
```

```bash
echo "===== PROMETHEUS READ ACCESS ====="
runuser -u prometheus -- test -r /var/lib/prometheus/node-exporter/apt.prom
echo "EXISTING_METRIC_READ_EXIT=$?"

echo "===== PROMETHEUS DIRECTORY ACCESS ====="
runuser -u prometheus -- test -x /var/lib/prometheus/node-exporter
echo "DIRECTORY_TRAVERSE_EXIT=$?"

echo "===== METRIC DIRECTORY WRITE ACCESS ====="
runuser -u prometheus -- test -w /var/lib/prometheus/node-exporter
echo "DIRECTORY_WRITE_EXIT=$?"
```

The results were `0` (readable), `0` (traversable) and `1` (not writable). Node Exporter can read a file written by root without being given write permission.

## 1.6 The Collector's Unit and the Shape of the State File

Without showing the state file's values, check only its shape.

```bash
echo "===== COLLECTOR UNIT ====="
systemctl cat wazuh-collector.service

echo "===== STATE JSON STRUCTURE ====="
python3 -c '
import json
p="/var/lib/wazuh-collector/state.json"
with open(p) as f:
    d=json.load(f)
print("keys:", sorted(d.keys()))
print("inode_type:", type(d.get("inode")).__name__)
print("offset_type:", type(d.get("offset")).__name__)
print("inode_positive:", isinstance(d.get("inode"), int) and d["inode"] > 0)
print("offset_nonnegative:", isinstance(d.get("offset"), int) and d["offset"] >= 0)
'
```

```text
keys: ['inode', 'offset']
inode_type: int
offset_type: int
inode_positive: True
offset_nonnegative: True
```

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

```bash
cat > /usr/local/sbin/wazuh-collector-metrics.py <<'PY'
#!/usr/bin/python3
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

STATE = Path("/var/lib/wazuh-collector/state.json")
ALERTS = Path("/var/ossec/logs/alerts/alerts.json")
OUTPUT_DIR = Path("/var/lib/prometheus/node-exporter")
OUTPUT = OUTPUT_DIR / "wazuh_collector.prom"

def systemd_status():
    result = subprocess.run(
        [
            "/usr/bin/systemctl", "show", "wazuh-collector.service",
            "-p", "ActiveState", "-p", "SubState", "-p", "NRestarts",
        ],
        capture_output=True, text=True, timeout=5, check=True
    )
    values = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value

    active = int(
        values.get("ActiveState") == "active"
        and values.get("SubState") == "running"
    )
    restarts = int(values["NRestarts"])
    return active, restarts

def build_metrics():
    service_up, restarts = systemd_status()

    state_valid = 0
    inode_match = 0
    unread_bytes = -1
    state_mtime = 0

    try:
        with STATE.open("r", encoding="utf-8") as handle:
            state = json.load(handle)

        if (
            isinstance(state, dict)
            and set(state) == {"inode", "offset"}
            and isinstance(state["inode"], int)
            and not isinstance(state["inode"], bool)
            and state["inode"] > 0
            and isinstance(state["offset"], int)
            and not isinstance(state["offset"], bool)
            and state["offset"] >= 0
        ):
            state_valid = 1
            state_mtime = STATE.stat().st_mtime
            alert_stat = ALERTS.stat()

            if state["inode"] == alert_stat.st_ino:
                inode_match = 1
                if state["offset"] <= alert_stat.st_size:
                    unread_bytes = alert_stat.st_size - state["offset"]
                else:
                    state_valid = 0
                    inode_match = 0
                    unread_bytes = -1
    except (OSError, ValueError, TypeError, KeyError):
        pass

    lines = [
        "# HELP wazuh_collector_service_up Collector service running state.",
        "# TYPE wazuh_collector_service_up gauge",
        f"wazuh_collector_service_up {service_up}",
        "# HELP wazuh_collector_restarts_total systemd collector restart count.",
        "# TYPE wazuh_collector_restarts_total gauge",
        f"wazuh_collector_restarts_total {restarts}",
        "# HELP wazuh_collector_state_valid Collector state file validity.",
        "# TYPE wazuh_collector_state_valid gauge",
        f"wazuh_collector_state_valid {state_valid}",
        "# HELP wazuh_collector_inode_match State inode matches current alert file.",
        "# TYPE wazuh_collector_inode_match gauge",
        f"wazuh_collector_inode_match {inode_match}",
        "# HELP wazuh_collector_unread_bytes Unread bytes; -1 means unavailable.",
        "# TYPE wazuh_collector_unread_bytes gauge",
        f"wazuh_collector_unread_bytes {unread_bytes}",
        "# HELP wazuh_collector_state_mtime_seconds State file modification time.",
        "# TYPE wazuh_collector_state_mtime_seconds gauge",
        f"wazuh_collector_state_mtime_seconds {state_mtime}",
    ]
    return "\n".join(lines) + "\n"

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    content = build_metrics()
    fd, temporary = tempfile.mkstemp(
        prefix=".wazuh_collector.", suffix=".tmp", dir=OUTPUT_DIR
    )
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, OUTPUT)
        directory_fd = os.open(OUTPUT_DIR, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        try:
            OUTPUT.unlink()
        except FileNotFoundError:
            pass
        raise

if __name__ == "__main__":
    main()
PY
chmod 0755 /usr/local/sbin/wazuh-collector-metrics.py
python3 -m py_compile /usr/local/sbin/wazuh-collector-metrics.py
echo "SCRIPT_SYNTAX_EXIT=$?"
stat -c '%A %U:%G %n' /usr/local/sbin/wazuh-collector-metrics.py
```

`SCRIPT_SYNTAX_EXIT=0` and `-rwxr-xr-x root:root`.

## 2.3 Running It Once

```bash
python3 /usr/local/sbin/wazuh-collector-metrics.py
echo "SCRIPT_EXIT=$?"
echo "===== METRICS FILE ====="
stat -c '%A %U:%G size=%s %n' /var/lib/prometheus/node-exporter/wazuh_collector.prom
cat /var/lib/prometheus/node-exporter/wazuh_collector.prom
echo "===== PROMETHEUS READ ACCESS ====="
runuser -u prometheus -- test -r /var/lib/prometheus/node-exporter/wazuh_collector.prom
echo "PROMETHEUS_READ_EXIT=$?"
```

The file contained `wazuh_collector_service_up 1`, `restarts_total 0`, `state_valid 1`, `inode_match 1` and `unread_bytes 0`, and the `prometheus` user could read it (`PROMETHEUS_READ_EXIT=0`).

# Chapter 3: Running It Every 15 Seconds

## 3.1 The Service

It runs as root, but where it can read and write is narrowed (the state file and the alerts directory are read-only; only the `.prom` directory is writable).

```bash
cat > /etc/systemd/system/wazuh-collector-metrics.service <<'EOF'
[Unit]
Description=Export Wazuh Collector metrics for Node Exporter
After=network-online.target

[Service]
Type=oneshot
User=root
Group=root
UMask=0022
ExecStart=/usr/bin/python3 /usr/local/sbin/wazuh-collector-metrics.py

NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
ProtectHostname=true
ProtectClock=true
RestrictSUIDSGID=true
LockPersonality=true
MemoryDenyWriteExecute=true
RestrictAddressFamilies=AF_UNIX

ReadOnlyPaths=/var/lib/wazuh-collector
ReadOnlyPaths=/var/ossec/logs/alerts
ReadWritePaths=/var/lib/prometheus/node-exporter

[Install]
WantedBy=multi-user.target
EOF

systemd-analyze verify /etc/systemd/system/wazuh-collector-metrics.service
echo "VERIFY_EXIT=$?"
```

## 3.2 The Timer

```bash
cat > /etc/systemd/system/wazuh-collector-metrics.timer <<'EOF'
[Unit]
Description=Periodic Wazuh Collector metrics update

[Timer]
OnBootSec=30s
OnUnitActiveSec=15s
AccuracySec=1s
Unit=wazuh-collector-metrics.service

[Install]
WantedBy=timers.target
EOF

systemd-analyze verify /etc/systemd/system/wazuh-collector-metrics.timer
echo "VERIFY_EXIT=$?"
```

Both gave `VERIFY_EXIT=0`.

## 3.3 Enabling It

```bash
systemctl daemon-reload
systemctl enable --now wazuh-collector-metrics.timer
echo "ENABLE_EXIT=$?"
echo "===== TIMER STATUS ====="
systemctl status wazuh-collector-metrics.timer --no-pager -l
echo "===== NEXT ACTIVATION ====="
systemctl list-timers wazuh-collector-metrics.timer --no-pager
```

```bash
echo "===== METRICS SERVICE ====="
systemctl status wazuh-collector-metrics.service --no-pager -l
echo "===== TIMER PROPERTIES ====="
systemctl show wazuh-collector-metrics.timer \
  -p ActiveState -p SubState -p LastTriggerUSec \
  -p NextElapseUSecRealtime -p NextElapseUSecMonotonic
echo "===== RECENT JOURNAL ====="
journalctl -u wazuh-collector-metrics.service -n 20 --no-pager
```

The service finished with `status=0/SUCCESS`, and the timer was `active (waiting)`.

> **Note**: The next run time in `systemctl list-timers` may be shown as `-`. Because `OnUnitActiveSec` is measured from the previous run (on the monotonic clock), `NextElapseUSecRealtime` is empty and the value goes into `NextElapseUSecMonotonic` instead. This is not abnormal.

## 3.4 Visible from Node Exporter?

```bash
echo "===== TIMER SCHEDULE ====="
systemctl list-timers --all wazuh-collector-metrics.timer --no-pager
echo "===== NODE EXPORTER METRICS ====="
curl -fsS http://192.168.0.220:9100/metrics \
  | grep -E '^wazuh_collector_|^node_scrape_collector_success\{collector="textfile"\}'
echo "===== METRICS FILE TIME ====="
stat -c '%y %A %U:%G %n' /var/lib/prometheus/node-exporter/wazuh_collector.prom
```

The `wazuh_collector_` numbers appeared in Node Exporter's `/metrics`, and `node_scrape_collector_success{collector="textfile"}` was 1. The `.prom` file was also being rewritten every 15 seconds.

# Chapter 4: Ingesting into Prometheus

## 4.1 Where Prometheus Is

Prometheus runs in LXC 103 on Proxmox. If you run Prometheus commands directly on the Proxmox host (`root@pve`), neither the configuration file nor `promtool` will be found. Check with the list of LXCs.

> **Run on: pve**

```bash
pct list
```

LXC 103 was `lxc-prometheus`.

## 4.2 The Collection Settings

```bash
pct exec 103 -- bash -lc '
echo "===== PROMETHEUS SERVICE ====="
systemctl is-active prometheus
echo "===== PROMETHEUS CONFIG ====="
grep -n -B 8 -A 12 "192.168.0.220:9100" /etc/prometheus/prometheus.yml
echo "===== CONFIG VALIDATION ====="
promtool check config /etc/prometheus/prometheus.yml
'
```

Prometheus was running, and `192.168.0.220:9100` was already registered as job `security-core`. The configuration check was also `SUCCESS`. The new numbers are ingested without changing Prometheus's settings.

```bash
pct exec 103 -- bash -lc '
for metric in \
  wazuh_collector_service_up \
  wazuh_collector_restarts_total \
  wazuh_collector_state_valid \
  wazuh_collector_inode_match \
  wazuh_collector_unread_bytes
do
  echo "===== $metric ====="
  curl -fsS --get http://127.0.0.1:9090/api/v1/query \
    --data-urlencode "query=$metric"
  echo
done
'
```

All five were ingested with the labels `job="security-core"` and `instance="192.168.0.220:9100"`.

## 4.3 The Current Alert Settings

```bash
pct exec 103 -- bash -lc '
echo "===== RULE FILE CONFIGURATION ====="
grep -n -A 8 -B 3 "rule_files:" /etc/prometheus/prometheus.yml
echo "===== EXISTING RULE FILES ====="
find /etc/prometheus -maxdepth 3 -type f \
  \( -name "*.yml" -o -name "*.yaml" \) -printf "%p\n"
echo "===== ALERTMANAGER SERVICE ====="
systemctl is-active prometheus-alertmanager 2>/dev/null || true
echo "===== ALERTMANAGER TARGET CONFIG ====="
grep -n -A 8 -B 3 "alertmanagers:" /etc/prometheus/prometheus.yml
'
```

`rule_files` was still commented out (no rules), and Alertmanager was not running either. With rules added, alerts can be seen in Prometheus's screens (notifications such as e-mail are not delivered until Alertmanager is set up; we do not set up notifications this time).

# Chapter 5: Alert Rules

## 5.1 Checks Before Creating

In the original build, approval was obtained before adding the rules.

```bash
pct exec 103 -- bash -lc '
echo "===== PROMETHEUS VERSION ====="
prometheus --version
echo "===== GLOBAL CONFIG ====="
sed -n "1,24p" /etc/prometheus/prometheus.yml
echo "===== RULE DIRECTORY ====="
ls -ld /etc/prometheus /etc/prometheus/rules 2>&1
echo "===== TARGET TEXTFILE METRICS ====="
curl -fsS http://192.168.0.220:9100/metrics \
  | grep -E "^node_textfile_mtime_seconds|^wazuh_collector_"
echo "===== RULE FILE COLLISION ====="
ls -l /etc/prometheus/rules/wazuh-collector-alerts.yml 2>&1
'
```

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

```bash
pct exec 103 -- bash -lc '
install -d -o root -g root -m 0755 /etc/prometheus/rules

cat > /etc/prometheus/rules/wazuh-collector-alerts.yml <<'"'"'EOF'"'"'
groups:
  - name: wazuh-collector
    interval: 15s
    rules:
      - alert: WazuhCollectorDown
        expr: wazuh_collector_service_up{job="security-core"} == 0
        for: 1m
        labels:
          severity: critical
          component: wazuh-collector
        annotations:
          summary: "Wazuh Collector is not running"
          description: "The Wazuh Collector service has been down for at least 1 minute."

      - alert: WazuhCollectorStateInvalid
        expr: wazuh_collector_state_valid{job="security-core"} == 0
        for: 1m
        labels:
          severity: critical
          component: wazuh-collector
        annotations:
          summary: "Wazuh Collector state is invalid"
          description: "The Collector state file or its position validation has failed."

      - alert: WazuhCollectorInodeMismatch
        expr: wazuh_collector_inode_match{job="security-core"} == 0
        for: 1m
        labels:
          severity: warning
          component: wazuh-collector
        annotations:
          summary: "Wazuh alert file inode mismatch"
          description: "The Collector state inode does not match the current alerts.json inode."

      - alert: WazuhCollectorBacklog
        expr: wazuh_collector_unread_bytes{job="security-core"} > 1048576
        for: 2m
        labels:
          severity: warning
          component: wazuh-collector
        annotations:
          summary: "Wazuh Collector backlog is growing"
          description: "Unread alert data exceeds 1 MiB for at least 2 minutes."

      - alert: WazuhCollectorRestarted
        expr: increase(wazuh_collector_restarts_total{job="security-core"}[5m]) > 0
        for: 0m
        labels:
          severity: warning
          component: wazuh-collector
        annotations:
          summary: "Wazuh Collector restarted"
          description: "The systemd restart counter increased during the last 5 minutes."

      - alert: WazuhCollectorMetricsStale
        expr: time() - node_textfile_mtime_seconds{job="security-core",file="/var/lib/prometheus/node-exporter/wazuh_collector.prom"} > 60
        for: 0m
        labels:
          severity: critical
          component: wazuh-collector
        annotations:
          summary: "Wazuh Collector metrics file is stale"
          description: "The Collector metrics textfile has not been updated for more than 60 seconds."

      - alert: WazuhCollectorMetricsMissing
        expr: absent(wazuh_collector_service_up{job="security-core"})
        for: 1m
        labels:
          severity: critical
          component: wazuh-collector
        annotations:
          summary: "Wazuh Collector metrics are missing"
          description: "Prometheus has not received the Collector service metric for at least 1 minute."

      - alert: SecurityCoreNodeExporterDown
        expr: up{job="security-core"} == 0
        for: 1m
        labels:
          severity: critical
          component: node-exporter
        annotations:
          summary: "Security-core Node Exporter is unreachable"
          description: "Prometheus cannot scrape security-core Node Exporter."

      - alert: SecurityCoreTargetMissing
        expr: absent(up{job="security-core"})
        for: 1m
        labels:
          severity: critical
          component: node-exporter
        annotations:
          summary: "Security-core scrape target is missing"
          description: "The security-core scrape target is absent from Prometheus."
EOF

echo "===== FILE PERMISSIONS ====="
stat -c "%A %U:%G %n" /etc/prometheus/rules/wazuh-collector-alerts.yml
echo "===== RULE FILE ====="
cat /etc/prometheus/rules/wazuh-collector-alerts.yml
'
```

The file was created as `root:root`, `0644`.

## 5.3 Checking the Rules

> **Caution**: Running it directly, as in `pct exec 103 -- promtool …`, fails with `Failed to exec "promtool"` (exit code 127) because `promtool` is not found in the PATH. Run it through `bash -lc`.

```bash
pct exec 103 -- bash -lc '
echo "===== PROMTOOL PATH ====="
command -v promtool
echo "===== RULE VALIDATION ====="
promtool check rules /etc/prometheus/rules/wazuh-collector-alerts.yml
echo "RULE_CHECK_EXIT=$?"
'
```

`SUCCESS: 9 rules found` and `RULE_CHECK_EXIT=0`.

## 5.4 Registering in the Prometheus Configuration

Back up the configuration file, then replace only the commented-out `rule_files` part. If the part to replace is not found exactly once, nothing is changed.

```bash
pct exec 103 -- bash -lc '
cp -a /etc/prometheus/prometheus.yml \
  /etc/prometheus/prometheus.yml.pre-wazuh-rules-20261122

python3 - <<'"'"'PY'"'"'
from pathlib import Path

path = Path("/etc/prometheus/prometheus.yml")
content = path.read_text()

old = """rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"
"""
new = """rule_files:
  - "/etc/prometheus/rules/*.yml"
"""

if content.count(old) != 1:
    print("CONFIG_EDIT_ABORTED: expected rule_files block not found exactly once")
else:
    path.write_text(content.replace(old, new, 1))
    print("CONFIG_EDIT: SUCCESS")
PY

echo "===== CONFIG VALIDATION ====="
promtool check config /etc/prometheus/prometheus.yml
echo "CONFIG_CHECK_EXIT=$?"
echo "===== RULE VALIDATION ====="
promtool check rules /etc/prometheus/rules/wazuh-collector-alerts.yml
echo "RULE_CHECK_EXIT=$?"
echo "===== RULE FILE REGISTRATION ====="
grep -n -A 3 "^rule_files:" /etc/prometheus/prometheus.yml
'
```

`CONFIG_EDIT: SUCCESS`, and both the configuration and rule checks were `SUCCESS`. Under `rule_files:` there is now `- "/etc/prometheus/rules/*.yml"`.

## 5.5 Reloading Without a Restart

```bash
pct exec 103 -- bash -lc '
echo "===== RELOAD CAPABILITY ====="
systemctl show prometheus -p CanReload -p ExecReload -p ActiveState -p MainPID
echo "===== SERVICE UNIT ====="
systemctl cat prometheus
'
```

`CanReload=yes`, with `ExecReload=/bin/kill -HUP $MAINPID` (sending SIGHUP).

```bash
pct exec 103 -- bash -lc '
systemctl reload prometheus
echo "RELOAD_EXIT=$?"
echo "===== SERVICE STATUS ====="
systemctl is-active prometheus
echo "===== PROMETHEUS PID ====="
systemctl show prometheus -p MainPID
echo "===== RECENT LOG ====="
journalctl -u prometheus -n 15 --no-pager
'
```

Prometheus stayed `active`, its PID stayed `98`, and `Completed loading of configuration file` appeared in the log.

## 5.6 Were the Rules Registered?

```bash
pct exec 103 -- bash -lc '
echo "===== LOADED RULES ====="
curl -fsS http://127.0.0.1:9090/api/v1/rules |
python3 -c "
import json,sys
d=json.load(sys.stdin)
groups=d.get(\"data\",{}).get(\"groups\",[])
rules=[r for g in groups for r in g.get(\"rules\",[]) if r.get(\"name\", \"\").startswith((\"WazuhCollector\", \"SecurityCore\"))]
print(\"RULE_COUNT:\",len(rules))
for r in rules:
    print(r.get(\"name\"), \"|\", r.get(\"health\"), \"|\", r.get(\"state\"))
"

echo "===== ACTIVE ALERTS ====="
curl -fsS http://127.0.0.1:9090/api/v1/alerts |
python3 -c "
import json,sys
d=json.load(sys.stdin)
alerts=d.get(\"data\",{}).get(\"alerts\",[])
selected=[a for a in alerts if a.get(\"labels\",{}).get(\"component\") in (\"wazuh-collector\", \"node-exporter\")]
print(\"ACTIVE_ALERT_COUNT:\",len(selected))
for a in selected:
    print(a.get(\"labels\",{}).get(\"alertname\"), \"|\", a.get(\"state\"), \"|\", a.get(\"labels\",{}).get(\"severity\"))
"
'
```

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

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

```bash
echo "=== HOST ==="
hostname
ip -br addr

echo
echo "=== GRAFANA SERVICE ==="
systemctl is-active grafana-server
systemctl status grafana-server --no-pager -l | head -25

echo
echo "=== GRAFANA HTTP ==="
curl -sS --max-time 5 http://127.0.0.1:3000/api/health

echo
echo
echo "=== LISTEN PORT ==="
ss -lntp | grep ':3000' || true

echo
echo "=== GRAFANA PROVISIONING FILES ==="
find /etc/grafana/provisioning -maxdepth 3 -type f \
  -printf '%p\n' 2>/dev/null | sort
```

At build time, Grafana 13.0.2 was `active (running)` and `/api/health` was also normal.

## 1.2 Checking That VictoriaMetrics Is Reachable

From Grafana (`vmbr0`, 192.168.0.0/24), VictoriaMetrics' `vmbr1`-side address (192.168.1.23) cannot be reached. Without changing the network, check whether Grafana can connect to the `vmbr0`-side address `192.168.0.171`.

**Run on: LXC 105 lxc-grafana (root)**

```bash
echo "=== VICTORIAMETRICS VMbr0 HEALTH ==="
curl -sS --max-time 5 \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  http://192.168.0.171:8428/health

echo
echo "=== VICTORIAMETRICS VMbr0 METRICS QUERY ==="
curl -sS --max-time 5 \
  -G 'http://192.168.0.171:8428/api/v1/query' \
  --data-urlencode 'query=up' \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  | head -c 1000
```

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

```bash
echo "=== UP TARGETS ==="
curl -sS --max-time 10 \
  'http://192.168.0.171:8428/api/v1/query?query=up' \
  | python3 -c '
import json,sys
d=json.load(sys.stdin)
for r in d.get("data",{}).get("result",[]):
    m=r["metric"]
    job=m.get("job","-")
    instance=m.get("instance","-")
    value=r["value"][1]
    print("{:<20} {:<30} UP={}".format(job,instance,value))
'
```

At build time there were 11 series, but none of them came from the five machines (they came from out-of-scope servers). CPU, memory and disk data for the five machines was not yet being collected.

## 2.2 Checking the Ports

**Run on: LXC 105 lxc-grafana (root)**

```bash
python3 - <<'PY'
import socket

targets = {
    "pve": "192.168.0.240",
    "security-core": "192.168.0.220",
    "postgresql": "192.168.0.151",
    "prometheus": "192.168.0.197",
    "grafana": "192.168.0.199",
}

ports = {
    "node_exporter": 9100,
    "postgres_exporter": 9187,
    "prometheus": 9090,
    "grafana": 3000,
}

for name, ip in targets.items():
    print(f"\n=== {name} ({ip}) ===")
    for service, port in ports.items():
        try:
            with socket.create_connection((ip, port), timeout=2):
                result = "OPEN"
        except OSError:
            result = "CLOSED/UNREACHABLE"
        print(f"{service:20} {ip}:{port:<5} {result}")
PY
```

At build time, Node Exporter (9100) was `CLOSED` on all five machines. Checking each server showed that none had Node Exporter installed. From the next chapter, we install it on one server at a time, confirm that it works, and then move on to the next.

# Chapter 3: Installing Node Exporter on the Proxmox Host

## 3.1 Checking the Package

**Run on: Proxmox host pve (root)**

```bash
echo "=== OS VERSION ==="
cat /etc/os-release | grep -E '^(PRETTY_NAME|VERSION_CODENAME)='

echo
echo "=== NODE EXPORTER PACKAGE CANDIDATE ==="
apt-cache policy prometheus-node-exporter
```

At build time this was Debian 12 (bookworm), and `prometheus-node-exporter 1.5.0-1+b6` from the official repository could be installed.

## 3.2 Installation

As soon as the package is installed, it starts listening on all addresses. So first mask it temporarily to keep it from starting, and then install it.

**Run on: Proxmox host pve (root)**

```bash
systemctl mask --runtime prometheus-node-exporter.service
```

```bash
apt-get install -y prometheus-node-exporter
```

Check the settings (it does not start yet).

```bash
echo "=== SERVICE UNIT ==="
systemctl cat prometheus-node-exporter.service

echo
echo "=== DEFAULT CONFIG ==="
if [ -f /etc/default/prometheus-node-exporter ]; then
  cat /etc/default/prometheus-node-exporter
else
  echo "No default config"
fi

echo
echo "=== MASK STATUS ==="
systemctl is-enabled prometheus-node-exporter.service
```

The Debian package takes its startup options from `ARGS` in `/etc/default/prometheus-node-exporter`. Confirm that `MASK STATUS` is `masked-runtime`.

## 3.3 Limiting the Listen Address and Starting

Limit listening to `192.168.0.240:9100` only.

**Run on: Proxmox host pve (root)**

```bash
cp -a /etc/default/prometheus-node-exporter \
  /etc/default/prometheus-node-exporter.bak

sed -i \
  's/^ARGS=.*/ARGS="--web.listen-address=192.168.0.240:9100"/' \
  /etc/default/prometheus-node-exporter

echo "=== UPDATED CONFIG ==="
cat /etc/default/prometheus-node-exporter
```

```bash
systemctl unmask --runtime prometheus-node-exporter.service
systemctl daemon-reload
systemctl enable --now prometheus-node-exporter.service
```

```bash
echo "=== SERVICE STATUS ==="
systemctl status prometheus-node-exporter.service --no-pager -l

echo
echo "=== LISTEN SOCKET ==="
ss -lntp | grep ':9100'

echo
echo "=== METRICS TEST ==="
curl -fsS http://192.168.0.240:9100/metrics | head -n 15
```

`curl: (23) Failure writing output to destination` appears at the end, but this is because `head` stopped reading after 15 lines; it is not a fault.

## 3.4 Checking Reachability from Prometheus

**Run on: LXC 103 lxc-prometheus (root)**

```bash
echo "=== PVE NODE EXPORTER CONNECTIVITY ==="
curl -fsS --max-time 5 \
  http://192.168.0.240:9100/metrics \
  -o /tmp/pve-node-metrics.prom \
  && grep -E '^(node_uname_info|node_cpu_seconds_total|node_memory_MemTotal_bytes)' \
     /tmp/pve-node-metrics.prom | head -n 10

echo
echo "=== HTTP RESULT ==="
test -s /tmp/pve-node-metrics.prom && echo "SUCCESS: metrics received"
```

If `SUCCESS: metrics received` is shown, the metrics are arriving.

# Chapter 4: Adding a Scrape Job to Prometheus

## 4.1 Adding the Job

Leave the existing jobs (`prometheus`, `ollama-gpu`) as they are and add a job for PVE.

**Run on: LXC 103 lxc-prometheus (root)**

```bash
cp -a /etc/prometheus/prometheus.yml \
  /etc/prometheus/prometheus.yml.bak.$(date +%Y%m%d-%H%M%S)

cat >> /etc/prometheus/prometheus.yml <<'EOF'

  - job_name: "pve-node"
    static_configs:
      - targets:
          - 192.168.0.240:9100
        labels:
          host: "pve"
          role: "hypervisor"
EOF

echo "=== VALIDATE CONFIG ==="
promtool check config /etc/prometheus/prometheus.yml
```

Confirm that `SUCCESS` is shown (Prometheus 3.12.0 at build time).

## 4.2 Reloading the Configuration

This Prometheus has reloading through the web API (Lifecycle API) disabled (it returns HTTP 403). The systemd unit has the following setting, so send SIGHUP with `systemctl reload` to reload.

```text
ExecReload=/bin/kill -HUP $MAINPID
```

**Run on: LXC 103 lxc-prometheus (root)**

```bash
systemctl reload prometheus

echo "=== SERVICE STATUS ==="
systemctl is-active prometheus

echo
echo "=== PVE TARGET STATUS ==="
curl -fsS 'http://127.0.0.1:9090/api/v1/targets?state=active' \
  | python3 -c '
import json, sys
data = json.load(sys.stdin)
for target in data["data"]["activeTargets"]:
    if target["labels"].get("job") == "pve-node":
        print("health:", target["health"])
        print("scrapeUrl:", target["scrapeUrl"])
        print("lastError:", target["lastError"])
'
```

Right after the reload, it may not be shown yet. In that case, check all jobs with the following command.

```bash
echo "=== PROMETHEUS JOBS ==="
curl -fsS 'http://127.0.0.1:9090/api/v1/targets?state=any' \
  | python3 -c '
import json, sys
data = json.load(sys.stdin)
print("API status:", data.get("status"))
for target in data.get("data", {}).get("activeTargets", []):
    print(
        "job:", target.get("labels", {}).get("job"),
        "health:", target.get("health"),
        "url:", target.get("scrapeUrl"),
        "error:", target.get("lastError")
    )
'

echo
echo "=== RECENT PROMETHEUS LOGS ==="
journalctl -u prometheus -n 30 --no-pager
```

At build time, all three jobs were `health: up`.

# Chapter 5: Forwarding to VictoriaMetrics (Remote Write)

## 5.1 Checking the Current State and Backing Up

**Run on: LXC 103 lxc-prometheus (root)**

```bash
echo "=== REMOTE WRITE CONFIG ==="
grep -n -A 8 -B 2 'remote_write' /etc/prometheus/prometheus.yml \
  || echo "remote_write is not configured"

echo
echo "=== VICTORIAMETRICS CONNECTIVITY ==="
curl -sS --max-time 5 \
  -o /dev/null \
  -w 'HTTP_STATUS=%{http_code}\n' \
  http://192.168.0.171:8428/health
```

```bash
echo "=== CONFIG BACKUP ==="
cp -a /etc/prometheus/prometheus.yml \
  /etc/prometheus/prometheus.yml.pre-remote-write.$(date +%Y%m%d-%H%M%S)

echo "=== CONFIG TAIL ==="
tail -n 35 /etc/prometheus/prometheus.yml
```

## 5.2 Adding the Forwarding Settings

Add the forwarding destination and a label to identify the source (`prometheus_source`).

**Run on: LXC 103 lxc-prometheus (root)**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/etc/prometheus/prometheus.yml")
text = path.read_text()

if "\nremote_write:" in text or text.startswith("remote_write:"):
    raise SystemExit("ERROR: remote_write already exists; no change made")

addition = '''
external_labels:
  prometheus_source: "lxc-prometheus"

remote_write:
  - url: "http://192.168.0.171:8428/api/v1/write"
'''

path.write_text(text.rstrip() + "\n\n" + addition)
print("remote_write configuration added")
PY

echo
echo "=== VALIDATE CONFIG ==="
promtool check config /etc/prometheus/prometheus.yml
```

In the original build, `promtool` gave an error here. `external_labels` is not a top-level item; it must be placed inside `global`. Move it into `global` with the following command.

```bash
python3 - <<'PY'
from pathlib import Path
import re

path = Path("/etc/prometheus/prometheus.yml")
text = path.read_text()

text = re.sub(
    r'\nexternal_labels:\n  prometheus_source: "lxc-prometheus"\n',
    '\n',
    text,
    count=1
)

pattern = r'(?m)^global:\n'
if not re.search(pattern, text):
    raise SystemExit("ERROR: global section not found")

text = re.sub(
    pattern,
    'global:\n  external_labels:\n    prometheus_source: "lxc-prometheus"\n',
    text,
    count=1
)

path.write_text(text)
print("external_labels moved under global")
PY

echo
echo "=== VALIDATE CONFIG ==="
promtool check config /etc/prometheus/prometheus.yml
```

```bash
echo "=== GLOBAL CONFIG ==="
sed -n '1,12p' /etc/prometheus/prometheus.yml

echo
echo "=== REMOTE WRITE CONFIG ==="
tail -n 12 /etc/prometheus/prometheus.yml

echo
echo "=== FINAL VALIDATION ==="
promtool check config /etc/prometheus/prometheus.yml
```

## 5.3 Applying and Checking the Forwarding

**Run on: LXC 103 lxc-prometheus (root)**

```bash
systemctl reload prometheus

echo "=== SERVICE STATUS ==="
systemctl is-active prometheus

echo
echo "=== RECENT REMOTE WRITE LOGS ==="
journalctl -u prometheus --since "2 minutes ago" --no-pager \
  | grep -Ei 'remote|write|error|failed' \
  | tail -n 20
```

```bash
echo "=== REMOTE WRITE DATA ARRIVAL ==="
curl -fsSG 'http://192.168.0.171:8428/api/v1/query' \
  --data-urlencode 'query=count by (job) ({prometheus_source="lxc-prometheus"})' \
  | python3 -m json.tool

echo
echo "=== REMOTE WRITE ERRORS ==="
journalctl -u prometheus --since "10 minutes ago" --no-pager \
  | grep -Ei 'remote|write|retry|failed|error|dropped' \
  | tail -n 30
```

| Job | Series in VictoriaMetrics (at build time) |
|---|---:|
| `pve-node` | 8,909 |
| `ollama-gpu` | 865 |
| `prometheus` | 791 |

> When searching in VictoriaMetrics, use `job="pve-node"` as the condition, not `host="pve"`. In the original build, searching with `host="pve"` returned 0 results.

## 5.4 Checking the Stored Data

**Run on: LXC 103 lxc-prometheus (root)**

```bash
echo "=== PVE FILESYSTEM METRICS ==="
curl -fsSG 'http://192.168.0.171:8428/api/v1/query' \
  --data-urlencode 'query=count(node_filesystem_size_bytes{job="pve-node"})' \
  | python3 -m json.tool

echo
echo "=== PVE NETWORK METRICS ==="
curl -fsSG 'http://192.168.0.171:8428/api/v1/query' \
  --data-urlencode 'query=count(node_network_receive_bytes_total{job="pve-node"})' \
  | python3 -m json.tool

echo
echo "=== PVE DISK I/O METRICS ==="
curl -fsSG 'http://192.168.0.171:8428/api/v1/query' \
  --data-urlencode 'query=count(node_disk_read_bytes_total{job="pve-node"})' \
  | python3 -m json.tool
```

If there is at least one series each for file systems, network and disk I/O, the data needed for the dashboard is in place.

# Chapter 6: Creating the PVE Dashboard

The dashboard is created not in the Grafana UI but from files (provisioning), so that the settings remain as files.

## 6.1 Checking the Data Source UID

The dashboard JSON contains the data source's UID. Open Grafana's database read-only to check it.

**Run on: LXC 105 lxc-grafana (root)**

```bash
python3 - <<'PY'
import sqlite3

con = sqlite3.connect(
    "file:/var/lib/grafana/grafana.db?mode=ro", uri=True
)

try:
    columns = {
        row[1] for row in
        con.execute("PRAGMA table_info(data_source)").fetchall()
    }

    fields = [
        name for name in
        ("id", "uid", "name", "type", "url", "is_default")
        if name in columns
    ]

    sql = (
        "SELECT " + ", ".join(fields) +
        " FROM data_source WHERE name = ?"
    )

    row = con.execute(sql, ("VictoriaMetrics",)).fetchone()

    print("=== VICTORIAMETRICS DATASOURCE ===")
    if row:
        print(dict(zip(fields, row)))
    else:
        print("Datasource not found")
finally:
    con.close()
PY
```

The UID at build time was `dfsldbphmj9c0e`. Replace `"uid": "dfsldbphmj9c0e"` in the next step with your environment's UID.

## 6.2 Creating the Dashboard and the Provisioning Settings

Create the `PVE Host Overview` dashboard (six panels: CPU, memory, file systems, network, disk I/O and uptime) and the settings that load it. If a file with the same name exists, it stops without overwriting.

**Run on: LXC 105 lxc-grafana (root)**

```bash
python3 - <<'PY'
import json
import os
from pathlib import Path

provider = Path("/etc/grafana/provisioning/dashboards/pve.yaml")
directory = Path("/var/lib/grafana/dashboards")
dashboard_file = directory / "pve-overview.json"

if provider.exists() or dashboard_file.exists():
    raise SystemExit("ABORT: 同名ファイルが存在します。上書きしません。")

directory.mkdir(parents=True, exist_ok=True)

ds = {"type": "prometheus", "uid": "dfsldbphmj9c0e"}

def panel(pid, title, expr, unit, x, y, w=12, h=8, kind="timeseries"):
    return {
        "id": pid,
        "title": title,
        "type": kind,
        "datasource": ds,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "targets": [{
            "refId": "A",
            "expr": expr,
            "legendFormat": "{{instance}} {{device}} {{mountpoint}}",
            "range": True
        }],
        "fieldConfig": {
            "defaults": {"unit": unit},
            "overrides": []
        },
        "options": {
            "legend": {"showLegend": True},
            "tooltip": {"mode": "multi"}
        }
    }

panels = [
    panel(1, "CPU Usage", 
          '100 * (1 - avg by(instance) (rate(node_cpu_seconds_total{job="pve-node",mode="idle"}[5m])))',
          "percent", 0, 0),
    panel(2, "Memory Usage",
          '100 * (1 - node_memory_MemAvailable_bytes{job="pve-node"} / node_memory_MemTotal_bytes{job="pve-node"})',
          "percent", 12, 0),
    panel(3, "Filesystem Usage",
          '100 * (1 - node_filesystem_avail_bytes{job="pve-node",fstype!~"tmpfs|overlay|squashfs"} / node_filesystem_size_bytes{job="pve-node",fstype!~"tmpfs|overlay|squashfs"})',
          "percent", 0, 8),
    panel(4, "Network Traffic",
          'rate(node_network_receive_bytes_total{job="pve-node",device!~"lo"}[5m])',
          "Bps", 12, 8),
    panel(5, "Disk I/O",
          'rate(node_disk_read_bytes_total{job="pve-node"}[5m])',
          "Bps", 0, 16),
    panel(6, "Host Uptime",
          'time() - node_boot_time_seconds{job="pve-node"}',
          "s", 12, 16, kind="stat")
]

dashboard = {
    "id": None,
    "uid": "pve-host-overview",
    "title": "PVE Host Overview",
    "tags": ["proxmox", "pve", "infrastructure"],
    "timezone": "browser",
    "schemaVersion": 41,
    "version": 1,
    "refresh": "30s",
    "time": {"from": "now-6h", "to": "now"},
    "panels": panels
}

provider_text = """apiVersion: 1
providers:
  - name: 'pve'
    orgId: 1
    folder: 'Infrastructure'
    type: file
    disableDeletion: true
    editable: true
    updateIntervalSeconds: 30
    options:
      path: /var/lib/grafana/dashboards
"""

dashboard_file.write_text(
    json.dumps(dashboard, ensure_ascii=False, indent=2) + "\n"
)
provider.write_text(provider_text)

os.chown(directory, 472, 472)
os.chmod(directory, 0o750)
os.chown(dashboard_file, 472, 472)
os.chmod(dashboard_file, 0o640)
os.chown(provider, 0,  gid := __import__("grp").getgrnam("grafana").gr_gid)
os.chmod(provider, 0o640)

# Verify by re-reading the JSON
json.loads(dashboard_file.read_text())

print("SUCCESS: Dashboard JSON created and validated")
print("Dashboard:", dashboard_file)
print("Provider:", provider)
print("Panels:", len(panels))
print("Grafana service was not restarted.")
PY

echo
echo "=== CREATED FILES ==="
ls -l /etc/grafana/provisioning/dashboards/pve.yaml \
      /var/lib/grafana/dashboards/pve-overview.json
```

## 6.3 Fixing the File Owner

6.2 sets the owner to UID 472, but on this LXC the Grafana user `grafana` is UID 102. As it stands Grafana cannot read the JSON, so change the owner to `grafana`.

**Run on: LXC 105 lxc-grafana (root)**

```bash
echo "=== CORRECT DASHBOARD FILE OWNERSHIP ==="
chown grafana:grafana \
  /var/lib/grafana/dashboards \
  /var/lib/grafana/dashboards/pve-overview.json

echo
echo "=== VERIFY OWNERSHIP ==="
stat -c '%U:%G %a %n' \
  /var/lib/grafana/dashboards \
  /var/lib/grafana/dashboards/pve-overview.json

echo
echo "=== VERIFY GRAFANA READ ACCESS ==="
runuser -u grafana -- test -r \
  /var/lib/grafana/dashboards/pve-overview.json \
  && echo "SUCCESS: grafana can read dashboard JSON" \
  || echo "ERROR: grafana cannot read dashboard JSON"
```

## 6.4 Restarting Grafana and Checking

**Run on: LXC 105 lxc-grafana (root)**

```bash
echo "=== RESTART GRAFANA ==="
systemctl restart grafana-server

echo
echo "=== SERVICE STATUS ==="
systemctl is-active grafana-server

echo
echo "=== GRAFANA HEALTH ==="
curl -fsS http://127.0.0.1:3000/api/health \
  | python3 -m json.tool

echo
echo "=== DASHBOARD PROVISIONING LOGS ==="
journalctl -u grafana-server --since "3 minutes ago" --no-pager \
  | grep -Ei 'provision|dashboard|error|failed' \
  | tail -n 30
```

Right after the restart, it may not yet be listening on port 3000, so `/api/health` may be unreachable. Wait a little and then check.

```bash
echo "=== GRAFANA HEALTH ==="
curl -fsS http://127.0.0.1:3000/api/health \
  | python3 -m json.tool

echo
echo "=== DASHBOARD PROVISIONING RESULT ==="
journalctl -u grafana-server --since "5 minutes ago" --no-pager \
  | grep -Ei 'pve|provisioning.dashboard|finished to provision|error' \
  | tail -n 30

echo
echo "=== DASHBOARD FILE ACCESS ==="
runuser -u grafana -- test -r \
  /var/lib/grafana/dashboards/pve-overview.json \
  && echo "SUCCESS"
```

If the log contains `finished to provision dashboards`, loading is complete.

## 6.5 Checking in the UI

In the Grafana UI, open **Dashboards → Infrastructure → PVE Host Overview** and confirm that data is shown in all six panels. At build time, all panels were shown.

# Chapter 7: Adding Monitoring of security-core

Add only Node Exporter, without touching Wazuh itself or its settings.

## 7.1 Checking and Installing

**Run on: security-core VM 220 (root)**

```bash
echo "=== OS VERSION ==="
cat /etc/os-release | grep -E '^(PRETTY_NAME|VERSION_CODENAME)='

echo
echo "=== NODE EXPORTER PACKAGE ==="
dpkg-query -W -f='${Status} ${Version}\n' prometheus-node-exporter 2>/dev/null \
  || echo "NOT INSTALLED"

echo
echo "=== PORT 9100 ==="
ss -lntp | grep ':9100' || echo "NOT LISTENING"
```

```bash
apt-get update
apt-cache policy prometheus-node-exporter
```

At build time this was Ubuntu 24.04.5 LTS, and the candidate was `1.7.0-1ubuntu0.3`. As with PVE, mask it temporarily before installing.

```bash
systemctl mask --runtime prometheus-node-exporter.service

apt-get install -y prometheus-node-exporter
```

## 7.2 Limiting the Listen Address and Starting

**Run on: security-core VM 220 (root)**

```bash
echo "=== CURRENT NODE EXPORTER CONFIG ==="
cat /etc/default/prometheus-node-exporter

echo
echo "=== SET LISTEN ADDRESS ==="
cat > /etc/default/prometheus-node-exporter <<'EOF'
ARGS="--web.listen-address=192.168.0.220:9100"
EOF

echo
echo "=== VERIFY CONFIG ==="
cat /etc/default/prometheus-node-exporter
```

The temporary mask is in `/run/systemd/system/`, so add `--runtime` when unmasking as well (without it, the mask is not removed and startup is refused).

```bash
echo "=== REMOVE RUNTIME MASK ==="
systemctl unmask --runtime prometheus-node-exporter.service

echo
echo "=== VERIFY UNMASK ==="
systemctl is-enabled prometheus-node-exporter.service

echo
echo "=== ENABLE AND START ==="
systemctl enable --now prometheus-node-exporter.service

echo
echo "=== SERVICE STATUS ==="
systemctl is-active prometheus-node-exporter.service

echo
echo "=== LISTEN ADDRESS ==="
ss -lntp | grep ':9100'
```

## 7.3 Checking Reachability from Prometheus

**Run on: LXC 103 lxc-prometheus (root)**

```bash
echo "=== SECURITY CORE NODE EXPORTER CONNECTIVITY ==="
curl -fsS --max-time 5 \
  http://192.168.0.220:9100/metrics \
  -o /tmp/security-core-node-metrics.prom \
  && echo "SUCCESS: metrics received"

echo
echo "=== METRIC SAMPLE ==="
grep -m 5 '^node_cpu_seconds_total' \
  /tmp/security-core-node-metrics.prom

echo
echo "=== METRIC COUNTS ==="
wc -l /tmp/security-core-node-metrics.prom
```

## 7.4 Adding the Job

Add the following job right after the `pve-node` job.

```yaml
  - job_name: "security-core"
    static_configs:
      - targets:
          - 192.168.0.220:9100
        labels:
          host: "security-core"
          role: "security"
```

**Run on: LXC 103 lxc-prometheus (root)**

```bash
set -e

CONFIG=/etc/prometheus/prometheus.yml
BACKUP="${CONFIG}.pre-security-core.$(date +%Y%m%d-%H%M%S)"

cp -a "$CONFIG" "$BACKUP"
echo "BACKUP: $BACKUP"

python3 - <<'PY'
from pathlib import Path

path = Path("/etc/prometheus/prometheus.yml")
text = path.read_text()

if 'job_name: "security-core"' in text:
    raise SystemExit("ABORT: security-core job already exists")

anchor = '''  - job_name: "pve-node"
    static_configs:
      - targets:
          - 192.168.0.240:9100
        labels:
          host: "pve"
          role: "hypervisor"
'''

if text.count(anchor) != 1:
    raise SystemExit("ABORT: expected pve-node block not found exactly once")

addition = anchor + '''
  - job_name: "security-core"
    static_configs:
      - targets:
          - 192.168.0.220:9100
        labels:
          host: "security-core"
          role: "security"
'''

path.write_text(text.replace(anchor, addition, 1))
print("SUCCESS: security-core job added")
PY

echo
echo "=== VALIDATE PROMETHEUS CONFIG ==="
/usr/local/bin/promtool check config "$CONFIG"
```

> Because it starts with `set -e`, do not paste this command directly into your interactive shell; start `bash` first or run it as a script. If it fails partway, it exits along with the shell you are logged in to.

## 7.5 Applying and Checking

**Run on: LXC 103 lxc-prometheus (root)**

```bash
echo "=== RELOAD PROMETHEUS ==="
systemctl reload prometheus

echo
echo "=== SERVICE STATUS ==="
systemctl is-active prometheus

echo
echo "=== SECURITY CORE TARGET ==="
sleep 3
curl -fsSG 'http://127.0.0.1:9090/api/v1/targets' \
  --data-urlencode 'state=any' \
  | python3 -c '
import json,sys
data=json.load(sys.stdin)
for group in data["data"]["activeTargets"]:
    if group["labels"].get("job") == "security-core":
        print(json.dumps({
            "job": group["labels"].get("job"),
            "instance": group["labels"].get("instance"),
            "health": group["health"],
            "lastError": group["lastError"]
        }, indent=2))
'
```

Right afterwards it shows `health: unknown`. Wait until the first scrape has finished, then check.

```bash
sleep 20

echo "=== SECURITY CORE TARGET STATUS ==="
curl -fsSG 'http://127.0.0.1:9090/api/v1/targets' \
  --data-urlencode 'state=any' \
  | python3 -c '
import json,sys
data=json.load(sys.stdin)
for target in data["data"]["activeTargets"]:
    if target["labels"].get("job") == "security-core":
        print(json.dumps({
            "job": target["labels"].get("job"),
            "instance": target["labels"].get("instance"),
            "health": target["health"],
            "lastScrape": target["lastScrape"],
            "lastError": target["lastError"]
        }, indent=2))
'

echo
echo "=== SECURITY CORE UP METRIC ==="
curl -fsSG 'http://127.0.0.1:9090/api/v1/query' \
  --data-urlencode 'query=up{job="security-core"}' \
  | python3 -m json.tool
```

```bash
echo "=== SECURITY CORE REMOTE WRITE ARRIVAL ==="
curl -fsSG 'http://192.168.0.171:8428/api/v1/query' \
  --data-urlencode 'query=up{job="security-core",prometheus_source="lxc-prometheus"}' \
  | python3 -m json.tool

echo
echo "=== SECURITY CORE CPU SERIES ==="
curl -fsSG 'http://192.168.0.171:8428/api/v1/query' \
  --data-urlencode 'query=count(node_cpu_seconds_total{job="security-core"})' \
  | python3 -m json.tool

echo
echo "=== REMOTE WRITE ERRORS ==="
journalctl -u prometheus --since "10 minutes ago" --no-pager \
  | grep -Ei 'remote.*error|write.*failed|retrying' \
  | tail -n 20 || true
```

At build time, `up` was `1`, there were 64 CPU series, and there were no forwarding errors.

# Chapter 8: Adding Monitoring of PostgreSQL (LXC 109)

Add only Node Exporter, without touching PostgreSQL itself.

## 8.1 Installation

**Run on: LXC 109 postgresql (root)**

```bash
apt-get update
apt-cache policy prometheus-node-exporter
```

At build time this was Debian 13 (trixie), and the candidate was `1.9.0-1+b4`.

```bash
systemctl mask --runtime prometheus-node-exporter.service

apt-get install -y prometheus-node-exporter
```

```bash
echo "=== CURRENT CONFIG ==="
cat /etc/default/prometheus-node-exporter

echo
echo "=== SERVICE MASK ==="
systemctl is-enabled prometheus-node-exporter.service || true
```

Confirm `ARGS=""` and `masked-runtime`.

## 8.2 Limiting the Listen Address and Starting

**Run on: LXC 109 postgresql (root)**

```bash
cat > /etc/default/prometheus-node-exporter <<'EOF'
ARGS="--web.listen-address=192.168.0.151:9100"
EOF

echo "=== CONFIGURATION ==="
cat /etc/default/prometheus-node-exporter

echo
echo "=== REMOVE RUNTIME MASK ==="
systemctl unmask --runtime prometheus-node-exporter.service

echo
echo "=== ENABLE AND START ==="
systemctl enable --now prometheus-node-exporter.service
```

```bash
echo "=== SERVICE STATUS ==="
systemctl show prometheus-node-exporter \
  -p ActiveState -p SubState -p MainPID

echo
echo "=== LISTEN ADDRESS ==="
ss -lntp | grep ':9100' || echo "NOT LISTENING"

echo
echo "=== METRICS TEST ==="
curl -fsS --max-time 5 http://192.168.0.151:9100/metrics \
  | grep -m 3 '^node_cpu_seconds_total'
```

## 8.3 Checking Reachability from Prometheus

**Run on: LXC 103 lxc-prometheus (root)**

```bash
echo "=== POSTGRESQL NODE EXPORTER CONNECTIVITY ==="
curl -fsS --max-time 5 http://192.168.0.151:9100/metrics \
  -o /tmp/postgresql-node-exporter.metrics

echo "HTTP metrics: OK"
echo "Metric lines:"
wc -l /tmp/postgresql-node-exporter.metrics

echo
echo "=== CPU METRIC SAMPLE ==="
grep -m 3 '^node_cpu_seconds_total' \
  /tmp/postgresql-node-exporter.metrics
```

## 8.4 Adding and Applying the Job

Add `postgresql-node` after the `security-core` job.

**Run on: LXC 103 lxc-prometheus (root)**

```bash
set -e

BACKUP="/etc/prometheus/prometheus.yml.pre-postgresql-node.$(date +%Y%m%d-%H%M%S)"
cp -a /etc/prometheus/prometheus.yml "$BACKUP"

python3 - <<'PY'
from pathlib import Path

p = Path("/etc/prometheus/prometheus.yml")
s = p.read_text()

marker = '''  - job_name: "security-core"
    static_configs:
      - targets:
          - 192.168.0.220:9100
        labels:
          host: "security-core"
          role: "security"
'''

addition = marker + '''
  - job_name: "postgresql-node"
    static_configs:
      - targets:
          - 192.168.0.151:9100
        labels:
          host: "postgresql"
          role: "database"
'''

if s.count(marker) != 1:
    raise SystemExit("ERROR: security-core block is not unique; no change made")
if 'job_name: "postgresql-node"' in s:
    raise SystemExit("ERROR: postgresql-node already exists; no change made")

p.write_text(s.replace(marker, addition, 1))
print("Added postgresql-node scrape job.")
PY

echo
echo "=== PROMETHEUS CONFIG VALIDATION ==="
promtool check config /etc/prometheus/prometheus.yml

echo
echo "=== BACKUP ==="
echo "$BACKUP"
```

```bash
systemctl reload prometheus

echo "=== SERVICE STATUS ==="
systemctl show prometheus -p ActiveState -p SubState -p MainPID

echo
echo "=== RELOAD LOG ==="
journalctl -u prometheus --since "2 minutes ago" --no-pager \
  | tail -30
```

## 8.5 Checking

**Run on: LXC 103 lxc-prometheus (root)**

```bash
echo "=== POSTGRESQL TARGET STATUS ==="
curl -fsSG 'http://127.0.0.1:9090/api/v1/targets' \
  --data-urlencode 'state=active' \
  | python3 -c '
import json,sys
data=json.load(sys.stdin)
for t in data["data"]["activeTargets"]:
    if t["labels"].get("job") == "postgresql-node":
        print(json.dumps({
            "health": t["health"],
            "scrapeUrl": t["scrapeUrl"],
            "lastError": t["lastError"],
            "labels": t["labels"]
        }, indent=2))
'

echo
echo "=== PROMETHEUS UP QUERY ==="
curl -fsSG 'http://127.0.0.1:9090/api/v1/query' \
  --data-urlencode 'query=up{job="postgresql-node"}' \
  | python3 -m json.tool
```

```bash
echo "=== VICTORIAMETRICS POSTGRESQL TARGET ==="
curl -fsSG 'http://192.168.0.171:8428/api/v1/query' \
  --data-urlencode 'query=up{job="postgresql-node",prometheus_source="lxc-prometheus"}' \
  | python3 -m json.tool

echo
echo "=== POSTGRESQL CPU METRIC COUNT ==="
curl -fsSG 'http://192.168.0.171:8428/api/v1/query' \
  --data-urlencode 'query=count(node_cpu_seconds_total{job="postgresql-node"})' \
  | python3 -m json.tool

echo
echo "=== REMOTE WRITE ERRORS ==="
journalctl -u prometheus --since "10 minutes ago" --no-pager \
  | grep -Ei 'remote.?write.*(error|fail)|non-recoverable' \
  || echo "NO REMOTE WRITE ERRORS FOUND"
```

It is done when it shows `health: up`, `up` is `1`, and `NO REMOTE WRITE ERRORS FOUND` is shown.

# Chapter 9: Adding Monitoring of Prometheus (LXC 103) Itself

So that its port does not overlap with Prometheus (9090), Node Exporter listens on `192.168.0.197:9100`.

## 9.1 Installing and Starting

**Run on: LXC 103 lxc-prometheus (root)**

```bash
apt-get update
apt-cache policy prometheus-node-exporter
```

```bash
systemctl mask --runtime prometheus-node-exporter.service

apt-get install -y prometheus-node-exporter
```

```bash
cat > /etc/default/prometheus-node-exporter <<'EOF'
ARGS="--web.listen-address=192.168.0.197:9100"
EOF

echo "=== CONFIGURATION ==="
cat /etc/default/prometheus-node-exporter

echo
echo "=== REMOVE RUNTIME MASK ==="
systemctl unmask --runtime prometheus-node-exporter.service

echo
echo "=== ENABLE AND START ==="
systemctl enable --now prometheus-node-exporter.service
```

```bash
echo "=== SERVICE STATUS ==="
systemctl show prometheus-node-exporter \
  -p ActiveState -p SubState -p MainPID

echo
echo "=== LISTEN ADDRESS ==="
ss -lntp | grep ':9100' || echo "NOT LISTENING"

echo
echo "=== METRICS TEST ==="
curl -fsS --max-time 5 http://192.168.0.197:9100/metrics \
  -o /tmp/prometheus-node-exporter.metrics

echo "Metric lines:"
wc -l /tmp/prometheus-node-exporter.metrics

echo
echo "=== CPU METRIC SAMPLE ==="
grep -m 3 '^node_cpu_seconds_total' \
  /tmp/prometheus-node-exporter.metrics
```

## 9.2 Adding and Applying the Job

**Run on: LXC 103 lxc-prometheus (root)**

```bash
echo "=== CURRENT SCRAPE JOBS ==="
grep -nE 'job_name:|targets:|remote_write:|192\.168\.0\.197' \
  /etc/prometheus/prometheus.yml
```

```bash
set -e

BACKUP="/etc/prometheus/prometheus.yml.pre-prometheus-node.$(date +%Y%m%d-%H%M%S)"
cp -a /etc/prometheus/prometheus.yml "$BACKUP"

python3 - <<'PY'
from pathlib import Path

p = Path("/etc/prometheus/prometheus.yml")
s = p.read_text()

marker = '''  - job_name: "postgresql-node"
    static_configs:
      - targets:
          - 192.168.0.151:9100
        labels:
          host: "postgresql"
          role: "database"
'''

addition = marker + '''
  - job_name: "prometheus-node"
    static_configs:
      - targets:
          - 192.168.0.197:9100
        labels:
          host: "prometheus"
          role: "monitoring"
'''

if s.count(marker) != 1:
    raise SystemExit("ERROR: postgresql-node block is not unique; no change made")
if 'job_name: "prometheus-node"' in s:
    raise SystemExit("ERROR: prometheus-node already exists; no change made")

p.write_text(s.replace(marker, addition, 1))
print("Added prometheus-node scrape job.")
PY

echo
echo "=== CONFIG VALIDATION ==="
promtool check config /etc/prometheus/prometheus.yml

echo
echo "=== BACKUP ==="
echo "$BACKUP"
```

```bash
systemctl reload prometheus

echo "=== SERVICE STATUS ==="
systemctl show prometheus -p ActiveState -p SubState -p MainPID

echo
echo "=== RELOAD LOG ==="
journalctl -u prometheus --since "2 minutes ago" --no-pager \
  | tail -20
```

## 9.3 Checking

**Run on: LXC 103 lxc-prometheus (root)**

```bash
echo "=== PROMETHEUS NODE TARGET STATUS ==="
curl -fsSG 'http://127.0.0.1:9090/api/v1/targets' \
  --data-urlencode 'state=active' \
  | python3 -c '
import json,sys
data=json.load(sys.stdin)
for t in data["data"]["activeTargets"]:
    if t["labels"].get("job") == "prometheus-node":
        print(json.dumps({
            "health": t["health"],
            "scrapeUrl": t["scrapeUrl"],
            "lastError": t["lastError"],
            "labels": t["labels"]
        }, indent=2))
'

echo
echo "=== PROMETHEUS UP QUERY ==="
curl -fsSG 'http://127.0.0.1:9090/api/v1/query' \
  --data-urlencode 'query=up{job="prometheus-node"}' \
  | python3 -m json.tool
```

```bash
echo "=== VICTORIAMETRICS PROMETHEUS TARGET ==="
curl -fsSG 'http://192.168.0.171:8428/api/v1/query' \
  --data-urlencode 'query=up{job="prometheus-node",prometheus_source="lxc-prometheus"}' \
  | python3 -m json.tool

echo
echo "=== CPU METRIC COUNT ==="
curl -fsSG 'http://192.168.0.171:8428/api/v1/query' \
  --data-urlencode 'query=count(node_cpu_seconds_total{job="prometheus-node"})' \
  | python3 -m json.tool

echo
echo "=== REMOTE WRITE ERRORS ==="
journalctl -u prometheus --since "10 minutes ago" --no-pager \
  | grep -Ei 'remote.?write.*(error|fail)|non-recoverable' \
  || echo "NO REMOTE WRITE ERRORS FOUND"
```

# Chapter 10: Adding Monitoring of Grafana (LXC 105) Itself

Without changing Grafana itself (port 3000), Node Exporter listens on `192.168.0.199:9100`.

## 10.1 Installing and Starting

**Run on: LXC 105 lxc-grafana (root)**

```bash
apt-get update
apt-cache policy prometheus-node-exporter
```

```bash
systemctl mask --runtime prometheus-node-exporter.service

apt-get install -y prometheus-node-exporter
```

```bash
cat > /etc/default/prometheus-node-exporter <<'EOF'
ARGS="--web.listen-address=192.168.0.199:9100"
EOF

echo "=== CONFIGURATION ==="
cat /etc/default/prometheus-node-exporter

echo
echo "=== REMOVE RUNTIME MASK ==="
systemctl unmask --runtime prometheus-node-exporter.service

echo
echo "=== ENABLE AND START ==="
systemctl enable --now prometheus-node-exporter.service
```

```bash
echo "=== SERVICE STATUS ==="
systemctl show prometheus-node-exporter \
  -p ActiveState -p SubState -p MainPID

echo
echo "=== LISTEN ADDRESS ==="
ss -lntp | grep ':9100' || echo "NOT LISTENING"

echo
echo "=== METRICS TEST ==="
curl -fsS --max-time 5 http://192.168.0.199:9100/metrics \
  -o /tmp/grafana-node-exporter.metrics

echo "Metric lines:"
wc -l /tmp/grafana-node-exporter.metrics

echo
echo "=== CPU METRIC SAMPLE ==="
grep -m 3 '^node_cpu_seconds_total' \
  /tmp/grafana-node-exporter.metrics
```

## 10.2 Checking Reachability from Prometheus

**Run on: LXC 103 lxc-prometheus (root)**

```bash
echo "=== GRAFANA NODE EXPORTER CONNECTIVITY ==="
curl -fsS --max-time 5 http://192.168.0.199:9100/metrics \
  -o /tmp/grafana-node-exporter.metrics

echo "Metric lines:"
wc -l /tmp/grafana-node-exporter.metrics

echo
echo "=== CPU METRIC SAMPLE ==="
grep -m 3 '^node_cpu_seconds_total' \
  /tmp/grafana-node-exporter.metrics
```

## 10.3 Adding and Applying the Job

This job is added just before `remote_write:` (at the end of the list of jobs).

```yaml
  - job_name: "grafana-node"
    static_configs:
      - targets:
          - 192.168.0.199:9100
        labels:
          host: "grafana"
          role: "visualization"
```

**Run on: LXC 103 lxc-prometheus (root)**

```bash
set -e

CONFIG=/etc/prometheus/prometheus.yml
BACKUP="${CONFIG}.pre-grafana-node.$(date +%Y%m%d-%H%M%S)"

cp -a "$CONFIG" "$BACKUP"
echo "Backup: $BACKUP"

python3 - <<'PY'
from pathlib import Path

p = Path("/etc/prometheus/prometheus.yml")
s = p.read_text()

marker = '\n\n\nremote_write:\n'
job = '''
  - job_name: "grafana-node"
    static_configs:
      - targets:
          - 192.168.0.199:9100
        labels:
          host: "grafana"
          role: "visualization"
'''

if 'job_name: "grafana-node"' in s:
    raise SystemExit("ERROR: grafana-node already exists; no changes made.")

if s.count(marker) != 1:
    raise SystemExit("ERROR: expected insertion point not found uniquely; no changes made.")

p.write_text(s.replace(marker, '\n' + job + marker, 1))
print("grafana-node job added.")
PY

echo
echo "=== UPDATED JOB CONFIGURATION ==="
grep -nA9 'job_name: "grafana-node"' "$CONFIG"
```

`marker` matches the fact that, in the configuration file at build time, there were two blank lines before `remote_write:`. Adjust it to the shape of your own file (if the shape differs, it stops without changing anything).

```bash
echo "=== PROMETHEUS CONFIG VALIDATION ==="
promtool check config /etc/prometheus/prometheus.yml
```

```bash
echo "=== RELOAD PROMETHEUS CONFIGURATION ==="
systemctl reload prometheus

echo
echo "=== SERVICE STATUS ==="
systemctl show prometheus \
  -p ActiveState -p SubState -p MainPID

echo
echo "=== RECENT CONFIGURATION LOGS ==="
journalctl -u prometheus --since "2 minutes ago" --no-pager \
  | tail -30
```

## 10.4 Checking

**Run on: LXC 103 lxc-prometheus (root)**

```bash
echo "=== GRAFANA TARGET STATUS ==="
curl -fsSG 'http://127.0.0.1:9090/api/v1/targets' \
  --data-urlencode 'state=active' \
  | python3 -c '
import json, sys
data = json.load(sys.stdin)
for target in data["data"]["activeTargets"]:
    if target["labels"].get("job") == "grafana-node":
        print("health:", target["health"])
        print("scrapeUrl:", target["scrapeUrl"])
        print("lastError:", target["lastError"])
        print("lastScrape:", target["lastScrape"])
'

echo
echo "=== PROMETHEUS UP QUERY ==="
curl -fsSG 'http://127.0.0.1:9090/api/v1/query' \
  --data-urlencode 'query=up{job="grafana-node"}' \
  | python3 -m json.tool
```

```bash
echo "=== VICTORIAMETRICS: GRAFANA TARGET ==="
curl -fsSG 'http://192.168.0.171:8428/api/v1/query' \
  --data-urlencode 'query=up{job="grafana-node",prometheus_source="lxc-prometheus"}' \
  | python3 -m json.tool

echo
echo "=== GRAFANA CPU METRIC COUNT ==="
curl -fsSG 'http://192.168.0.171:8428/api/v1/query' \
  --data-urlencode 'query=count(node_cpu_seconds_total{job="grafana-node"})' \
  | python3 -m json.tool

echo
echo "=== REMOTE WRITE ERRORS ==="
journalctl -u prometheus --since "10 minutes ago" --no-pager \
  | grep -Ei 'remote.?write.*(error|fail)|non-recoverable' \
  || echo "No remote_write errors found"
```

All five machines are now being monitored.

# Chapter 11: Creating the Integrated Infrastructure Dashboard

Keep the PVE dashboard as it is, and create a new "Integrated Infrastructure Overview" that compares the five machines together. Each host is displayed separately using the `host` label given to it.

## 11.1 Checking the Existing Settings

**Run on: LXC 105 lxc-grafana (root)**

```bash
echo "=== DASHBOARD PROVISIONING ==="
cat /etc/grafana/provisioning/dashboards/pve.yaml

echo
echo "=== EXISTING DASHBOARD FILES ==="
find /var/lib/grafana/dashboards -maxdepth 1 -type f \
  -printf '%f (%s bytes)\n'

echo
echo "=== EXISTING PVE DASHBOARD SUMMARY ==="
python3 - <<'PY'
import json
from pathlib import Path

p = Path("/var/lib/grafana/dashboards/pve-overview.json")
d = json.loads(p.read_text())

print("title:", d.get("title"))
print("uid:", d.get("uid"))
print("schemaVersion:", d.get("schemaVersion"))
print("panels:", len(d.get("panels", [])))
for panel in d.get("panels", []):
    print("-", panel.get("title"), "| type:", panel.get("type"))
PY
```

The provisioning settings from 6.2 automatically load every JSON file in `/var/lib/grafana/dashboards` (folder `Infrastructure`). So no settings need to change; you can add a dashboard just by placing a JSON file.

## 11.2 Creating the Dashboard

Create seven panels (host status, CPU, memory, file systems, network, disk I/O and uptime). If a file with the same name exists, it stops without overwriting. Replace `"uid": "dfsldbphmj9c0e"` with your environment's UID checked in 6.1.

**Run on: LXC 105 lxc-grafana (root)**

```bash
set -e

python3 - <<'PY'
import json
from pathlib import Path

path = Path("/var/lib/grafana/dashboards/infrastructure-overview.json")

if path.exists():
    raise SystemExit(f"ERROR: {path} already exists. No overwrite performed.")

ds = {"type": "prometheus", "uid": "dfsldbphmj9c0e"}
jobs = '(pve-node|security-core|postgresql-node|prometheus-node|grafana-node)'

def panel(pid, title, ptype, x, y, w, h, exprs, unit, instant=False):
    targets = []
    for i, (expr, legend) in enumerate(exprs):
        targets.append({
            "refId": chr(65+i),
            "expr": expr,
            "legendFormat": legend,
            "instant": instant,
            "range": not instant
        })

    defaults = {
        "unit": unit,
        "color": {"mode": "palette-classic"},
        "custom": {
            "drawStyle": "line",
            "lineInterpolation": "smooth",
            "lineWidth": 2,
            "fillOpacity": 12,
            "showPoints": "never",
            "spanNulls": False
        }
    }

    if title == "Host Availability":
        defaults["color"] = {"mode": "thresholds"}
        defaults["thresholds"] = {
            "mode": "absolute",
            "steps": [
                {"color": "red", "value": None},
                {"color": "green", "value": 1}
            ]
        }
    elif unit == "percent":
        defaults["min"] = 0
        defaults["max"] = 100

    options = (
        {
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": ""
            },
            "orientation": "auto",
            "textMode": "auto",
            "colorMode": "background" if title == "Host Availability" else "value",
            "graphMode": "area",
            "justifyMode": "auto",
            "showPercentChange": False,
            "percentChangeColorMode": "standard"
        }
        if ptype == "stat"
        else {
            "legend": {
                "showLegend": True,
                "displayMode": "list",
                "placement": "bottom",
                "calcs": []
            },
            "tooltip": {"mode": "multi", "sort": "desc"}
        }
    )

    return {
        "id": pid,
        "title": title,
        "type": ptype,
        "datasource": ds,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "fieldConfig": {"defaults": defaults, "overrides": []},
        "targets": targets,
        "options": options
    }

panels = [
    panel(1, "Host Availability", "stat", 0, 0, 24, 5, [
        (f'up{{job=~"{jobs}"}}', "{{host}}")
    ], "short", True),

    panel(2, "CPU Usage by Host", "timeseries", 0, 5, 12, 8, [
        (f'100 * (1 - avg by (host) (rate(node_cpu_seconds_total{{job=~"{jobs}",mode="idle"}}[5m])))',
         "{{host}}")
    ], "percent"),

    panel(3, "Memory Usage by Host", "timeseries", 12, 5, 12, 8, [
        (f'100 * (1 - max by (host) (node_memory_MemAvailable_bytes{{job=~"{jobs}"}}) / max by (host) (node_memory_MemTotal_bytes{{job=~"{jobs}"}}))',
         "{{host}}")
    ], "percent"),

    panel(4, "Maximum Filesystem Usage by Host", "timeseries", 0, 13, 12, 8, [
        (f'max by (host) (100 * (1 - node_filesystem_avail_bytes{{job=~"{jobs}",fstype!~"tmpfs|overlay|squashfs"}} / node_filesystem_size_bytes{{job=~"{jobs}",fstype!~"tmpfs|overlay|squashfs"}}))',
         "{{host}}")
    ], "percent"),

    panel(5, "Network Traffic by Host", "timeseries", 12, 13, 12, 8, [
        (f'sum by (host) (rate(node_network_receive_bytes_total{{job=~"{jobs}",device!~"lo"}}[5m]))',
         "{{host}} RX"),
        (f'sum by (host) (rate(node_network_transmit_bytes_total{{job=~"{jobs}",device!~"lo"}}[5m]))',
         "{{host}} TX")
    ], "Bps"),

    panel(6, "Disk I/O by Host", "timeseries", 0, 21, 12, 8, [
        (f'sum by (host) (rate(node_disk_read_bytes_total{{job=~"{jobs}"}}[5m]))',
         "{{host}} Read"),
        (f'sum by (host) (rate(node_disk_written_bytes_total{{job=~"{jobs}"}}[5m]))',
         "{{host}} Write")
    ], "Bps"),

    panel(7, "Host Uptime", "stat", 12, 21, 12, 8, [
        (f'time() - node_boot_time_seconds{{job=~"{jobs}"}}',
         "{{host}}")
    ], "s", True)
]

dashboard = {
    "uid": "infra-unified-overview",
    "title": "Integrated Infrastructure Overview",
    "description": "Unified monitoring for PVE, Security Core, PostgreSQL, Prometheus and Grafana.",
    "tags": ["infrastructure", "node-exporter", "victoriametrics"],
    "timezone": "browser",
    "schemaVersion": 41,
    "version": 1,
    "refresh": "30s",
    "time": {"from": "now-1h", "to": "now"},
    "panels": panels,
    "annotations": {
        "list": [{
            "builtIn": 1,
            "datasource": {"type": "grafana", "uid": "-- Grafana --"},
            "enable": True,
            "hide": True,
            "iconColor": "rgba(0, 211, 255, 1)",
            "name": "Annotations & Alerts",
            "type": "dashboard"
        }]
    }
}

path.write_text(json.dumps(dashboard, indent=2) + "\n")
print("Created:", path)
print("UID:", dashboard["uid"])
print("Panels:", len(panels))
for p in panels:
    print("-", p["title"])
PY

chown grafana:grafana /var/lib/grafana/dashboards/infrastructure-overview.json
chmod 640 /var/lib/grafana/dashboards/infrastructure-overview.json

echo
echo "=== JSON VALIDATION ==="
python3 -m json.tool \
  /var/lib/grafana/dashboards/infrastructure-overview.json \
  >/dev/null && echo "JSON: VALID"

echo
echo "=== FILE PERMISSIONS ==="
ls -l /var/lib/grafana/dashboards/infrastructure-overview.json

echo
echo "=== GRAFANA READ ACCESS ==="
runuser -u grafana -- test -r \
  /var/lib/grafana/dashboards/infrastructure-overview.json \
  && echo "READABLE: YES"
```

> Because it starts with `set -e`, start `bash` before running it (same as the note in 7.4).

## 11.3 Checking That It Loaded

Provisioning checks the files every 30 seconds, so there is no need to restart Grafana.

**Run on: LXC 105 lxc-grafana (root)**

```bash
echo "=== WAIT FOR DASHBOARD PROVISIONING ==="
sleep 35

echo
echo "=== PROVISIONING LOGS ==="
journalctl -u grafana-server --since "3 minutes ago" --no-pager \
  | grep -Ei 'provisioning.dashboard|finished to provision|error|infrastructure-overview'

echo
echo "=== GRAFANA HEALTH ==="
curl -fsS http://127.0.0.1:3000/api/health \
  | python3 -m json.tool
```

If you want to check after some time has passed, widen the log range (set `--since` to when you did the work).

```bash
echo "=== DASHBOARD PROVISIONING HISTORY ==="
journalctl -u grafana-server \
  --since "2026-11-20 10:20:00" --no-pager \
  | grep -Ei 'provision|dashboard|infrastructure-overview' \
  | tail -60

echo
echo "=== NEW DASHBOARD FILE ==="
stat /var/lib/grafana/dashboards/infrastructure-overview.json
```

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

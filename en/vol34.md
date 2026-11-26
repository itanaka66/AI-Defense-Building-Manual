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

```text
Wazuh Manager
    │
    ▼
Wazuh Collector
    │
    ├── Save alerts to PostgreSQL
    │
    └── Generate metrics (every 15 seconds)
             │
             ▼
       Node Exporter
             │
             ▼
       Prometheus
             │
             ▼
       9 monitoring rules
```

## 1.1 Services and Disks

> **Run on: VM 220**

```bash
echo "===== WAZUH RELATED SERVICES ====="
systemctl list-units --type=service --all --no-pager | grep -Ei 'wazuh|opensearch|indexer|filebeat|dashboard'

echo "===== INSTALLED WAZUH PACKAGES ====="
dpkg-query -W -f='${Package} ${Status} ${Version}\n' 2>/dev/null | grep -Ei 'wazuh|opensearch|filebeat'

echo "===== FILESYSTEM USAGE ====="
df -hT

echo "===== MEMORY ====="
free -h
```

Wazuh Manager, Indexer, Dashboard, Filebeat and the Collector were all running. The root file system was 12% used, and about 12 GiB of memory was available.

## 1.2 The Manager's Daemons and Ports

```bash
echo "===== WAZUH MANAGER INTERNAL STATUS ====="
/var/ossec/bin/wazuh-control status

echo "===== SERVICE DETAILS ====="
for s in wazuh-manager wazuh-indexer wazuh-dashboard filebeat; do
  echo "--- $s ---"
  systemctl show "$s" \
    -p ActiveState -p SubState -p MainPID -p ExecMainStatus
done

echo "===== LISTENING PORTS ====="
ss -lntp | grep -E ':(443|55000|5601|9200|9300|1514|1515|514|55000)\b'
```

`wazuh-analysisd`, `wazuh-remoted` (1514), `wazuh-authd` (1515) and others were running, and the API (55000), Indexer (9200, 9300) and Dashboard (443) were listening. `wazuh-clusterd`, `wazuh-maild`, `wazuh-agentlessd` and others were stopped, but these do not run unless their features are used; this is not abnormal.

## 1.3 HTTP Answers

```bash
echo "===== WAZUH INDEXER HTTP ====="
curl -k -sS -o /dev/null -w 'HTTP_STATUS=%{http_code}\n' \
  --connect-timeout 3 https://127.0.0.1:9200/

echo "===== WAZUH DASHBOARD HTTPS ====="
curl -k -sS -o /dev/null -w 'HTTP_STATUS=%{http_code}\n' \
  --connect-timeout 3 https://127.0.0.1:443/

echo "===== WAZUH API HTTP ====="
curl -sS -o /dev/null -w 'HTTP_STATUS=%{http_code}\n' \
  --connect-timeout 3 http://127.0.0.1:55000/
```

The Indexer answered 401 and the Dashboard 302. The API gave no answer (`000`) because the request used `http://`; the API listens on HTTPS, so check again with HTTPS.

```bash
echo "===== WAZUH API HTTPS ====="
curl -k -sS -o /dev/null \
  -w 'HTTP_STATUS=%{http_code}\n' \
  --connect-timeout 3 https://127.0.0.1:55000/
```

`HTTP_STATUS=401`. All three are answering.

## 1.4 Existing Monitoring Tools

```bash
echo "===== AVAILABLE MONITORING TOOLS ====="
for cmd in curl python3 systemctl ss; do
  command -v "$cmd"
done

echo "===== NODE EXPORTER SERVICE ====="
systemctl show prometheus-node-exporter \
  -p ActiveState -p SubState -p MainPID

echo "===== NODE EXPORTER TEXTFILE DIRECTORY ====="
ls -ld /var/lib/prometheus/node-exporter

echo "===== EXISTING TEXTFILE METRICS ====="
find /var/lib/prometheus/node-exporter \
  -maxdepth 1 -type f -name '*.prom' \
  -printf '%f\n' | sort
```

There were four `.prom` files: `apt.prom`, `nvme.prom`, `smartmon.prom` and `wazuh_collector.prom`.

```bash
echo "===== EXISTING METRICS SCRIPT ====="
sed -n '1,240p' /usr/local/sbin/wazuh-collector-metrics.py

echo "===== NODE EXPORTER STARTUP ====="
systemctl show prometheus-node-exporter -p ExecStart

echo "===== NODE EXPORTER UNIT ====="
systemctl cat prometheus-node-exporter
```

The new script is built the same way as the one in Part 33: run as root, write only numbers to a temporary file and then replace.

```bash
echo "===== NODE EXPORTER ARGUMENTS ====="
grep -vE '^[[:space:]]*(#|$)' /etc/default/prometheus-node-exporter

echo "===== TEXTFILE COLLECTOR CONFIGURATION ====="
grep -oE -- '--collector.textfile[^ ]*' \
  /etc/default/prometheus-node-exporter

echo "===== WAZUH MANAGER CONTROL STATUS EXIT ====="
/var/ossec/bin/wazuh-control status >/dev/null 2>&1
echo "WAZUH_CONTROL_EXIT=$?"
```

The exit code of `wazuh-control status` was `1`. This is because its judgment includes optional daemons that are stopped; it does not mean the whole Manager is abnormal. The monitoring checks only the required daemons, one by one.

```bash
echo "===== NODE EXPORTER PROCESS ARGUMENTS ====="
ps -ww -p 806 -o pid=,user=,args=

echo "===== TEXTFILE COLLECTOR METRICS ====="
curl -fsS http://192.168.0.220:9100/metrics \
  | grep -E '^node_scrape_collector_success\{collector="textfile"\}|^node_textfile_mtime_seconds'

echo "===== NODE EXPORTER VERSION ====="
/usr/bin/prometheus-node-exporter --version
```

`node_scrape_collector_success{collector="textfile"}` was 1, and all four files were being read. Node Exporter's startup arguments do not need to change. For disks and memory, Node Exporter's standard numbers are used as they are.

# Chapter 2: A Script That Writes Out the Wazuh Platform's Numbers

In the original build, approval was obtained before creating it.

## 2.1 Creating the Script

> **Run on: VM 220**

```bash
cat > /usr/local/sbin/wazuh-platform-metrics.py <<'PY'
#!/usr/bin/python3
import os
import re
import subprocess
import tempfile
from pathlib import Path

OUTPUT_DIR = Path("/var/lib/prometheus/node-exporter")
OUTPUT = OUTPUT_DIR / "wazuh_platform.prom"

REQUIRED_DAEMONS = [
    "wazuh-analysisd",
    "wazuh-remoted",
    "wazuh-syscheckd",
    "wazuh-logcollector",
    "wazuh-modulesd",
    "wazuh-db",
    "wazuh-execd",
    "wazuh-monitord",
    "wazuh-authd",
]

ENDPOINTS = {
    "indexer": {
        "url": "https://127.0.0.1:9200/",
        "expected": {200, 401, 403},
    },
    "dashboard": {
        "url": "https://127.0.0.1:443/",
        "expected": {200, 301, 302, 303, 307, 308},
    },
    "api": {
        "url": "https://127.0.0.1:55000/",
        "expected": {200, 401, 403},
    },
}

def manager_status():
    result = subprocess.run(
        ["/var/ossec/bin/wazuh-control", "status"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    statuses = {}
    for line in result.stdout.splitlines():
        match = re.fullmatch(
            r"(wazuh-[A-Za-z0-9_-]+) is (running|not running)\.\.\.",
            line.strip(),
        )
        if match:
            statuses[match.group(1)] = int(match.group(2) == "running")

    daemon_values = {
        daemon: statuses.get(daemon, 0)
        for daemon in REQUIRED_DAEMONS
    }
    manager_up = int(all(daemon_values.values()))
    return manager_up, daemon_values

def endpoint_status(name, config):
    result = subprocess.run(
        [
            "/usr/bin/curl",
            "--silent",
            "--show-error",
            "--output", "/dev/null",
            "--write-out", "%{http_code}",
            "--insecure",
            "--connect-timeout", "3",
            "--max-time", "5",
            config["url"],
        ],
        capture_output=True,
        text=True,
        timeout=7,
        check=False,
    )

    raw = result.stdout.strip()
    try:
        code = int(raw)
    except (ValueError, TypeError):
        code = 0

    up = int(result.returncode == 0 and code in config["expected"])
    return up, code

def build_metrics():
    manager_up, daemon_values = manager_status()

    lines = [
        "# HELP wazuh_manager_up All required Wazuh Manager daemons are running.",
        "# TYPE wazuh_manager_up gauge",
        f"wazuh_manager_up {manager_up}",
        "# HELP wazuh_manager_daemon_up Required Wazuh Manager daemon state.",
        "# TYPE wazuh_manager_daemon_up gauge",
    ]

    for daemon, value in daemon_values.items():
        lines.append(
            f'wazuh_manager_daemon_up{{daemon="{daemon}"}} {value}'
        )

    for name, config in ENDPOINTS.items():
        up, code = endpoint_status(name, config)
        lines.extend([
            f"# HELP wazuh_{name}_up Endpoint returned an expected HTTP status.",
            f"# TYPE wazuh_{name}_up gauge",
            f"wazuh_{name}_up {up}",
            f"# HELP wazuh_{name}_http_status HTTP status code; zero means no response.",
            f"# TYPE wazuh_{name}_http_status gauge",
            f"wazuh_{name}_http_status {code}",
        ])

    return "\n".join(lines) + "\n"

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    content = build_metrics()
    fd, temporary = tempfile.mkstemp(
        prefix=".wazuh_platform.", suffix=".tmp", dir=OUTPUT_DIR
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

chmod 0755 /usr/local/sbin/wazuh-platform-metrics.py

echo "===== PYTHON SYNTAX CHECK ====="
python3 -m py_compile /usr/local/sbin/wazuh-platform-metrics.py
echo "SYNTAX_EXIT=$?"

echo "===== SCRIPT PERMISSIONS ====="
stat -c '%A %U:%G %n' /usr/local/sbin/wazuh-platform-metrics.py
```

`SYNTAX_EXIT=0` and `-rwxr-xr-x root:root`. Pasting long content can garble the terminal display, so check the file's contents with line numbers.

```bash
nl -ba /usr/local/sbin/wazuh-platform-metrics.py
```

It was 150 lines, as intended.

## 2.2 Running It Once

```bash
echo "===== RUN PLATFORM METRICS ====="
/usr/bin/python3 /usr/local/sbin/wazuh-platform-metrics.py
echo "SCRIPT_EXIT=$?"

echo "===== GENERATED METRICS ====="
cat /var/lib/prometheus/node-exporter/wazuh_platform.prom

echo "===== FILE PERMISSIONS ====="
stat -c '%A %U:%G %s bytes %n' \
  /var/lib/prometheus/node-exporter/wazuh_platform.prom
```

`wazuh_manager_up 1`, all 9 daemons 1, `wazuh_indexer_up 1` (401), `wazuh_dashboard_up 1` (302) and `wazuh_api_up 1` (401). The file was `-rw-r--r-- root:root`, 1,446 bytes.

## 2.3 Service and Timer

```bash
cat > /etc/systemd/system/wazuh-platform-metrics.service <<'UNIT'
[Unit]
Description=Export Wazuh Platform health metrics for Node Exporter

[Service]
Type=oneshot
User=root
Group=root
UMask=0022
ExecStart=/usr/bin/python3 /usr/local/sbin/wazuh-platform-metrics.py
TimeoutStartSec=30

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
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6

ReadOnlyPaths=/var/ossec
ReadWritePaths=/var/lib/prometheus/node-exporter
UNIT

cat > /etc/systemd/system/wazuh-platform-metrics.timer <<'UNIT'
[Unit]
Description=Periodic Wazuh Platform metrics update

[Timer]
OnBootSec=45s
OnUnitActiveSec=15s
AccuracySec=1s
Unit=wazuh-platform-metrics.service

[Install]
WantedBy=timers.target
UNIT

echo "===== SYSTEMD UNIT VALIDATION ====="
systemd-analyze verify \
  /etc/systemd/system/wazuh-platform-metrics.service \
  /etc/systemd/system/wazuh-platform-metrics.timer
echo "VERIFY_EXIT=$?"

echo "===== CREATED FILES ====="
stat -c '%A %U:%G %n' \
  /etc/systemd/system/wazuh-platform-metrics.service \
  /etc/systemd/system/wazuh-platform-metrics.timer
```

`VERIFY_EXIT=0`. The pasted display was garbled here too, so check the contents.

```bash
echo "===== SERVICE UNIT ====="
cat /etc/systemd/system/wazuh-platform-metrics.service

echo "===== TIMER UNIT ====="
cat /etc/systemd/system/wazuh-platform-metrics.timer

echo "===== TIMER UNIT VALIDATION ====="
systemd-analyze verify /etc/systemd/system/wazuh-platform-metrics.timer
echo "TIMER_VERIFY_EXIT=$?"
```

Both were written correctly, and `TIMER_VERIFY_EXIT=0`. Enable the timer.

```bash
systemctl daemon-reload
systemctl enable --now wazuh-platform-metrics.timer

echo "===== TIMER STATE ====="
systemctl is-active wazuh-platform-metrics.timer
systemctl is-enabled wazuh-platform-metrics.timer

echo "===== TIMER SCHEDULE ====="
systemctl list-timers wazuh-platform-metrics.timer --no-pager
```

It became `active` and `enabled`.

# Chapter 3: Failing When Run by the Timer

## 3.1 Finding the Failure

```bash
echo "===== TIMER DETAILS ====="
systemctl show wazuh-platform-metrics.timer \
  -p ActiveState -p SubState -p LastTriggerUSec \
  -p NextElapseUSecRealtime -p Result

echo "===== SERVICE RESULT ====="
systemctl show wazuh-platform-metrics.service \
  -p ActiveState -p SubState -p Result -p ExecMainStatus

echo "===== RECENT SERVICE LOG ====="
journalctl -u wazuh-platform-metrics.service -n 15 --no-pager

echo "===== METRICS FILE UPDATE ====="
stat -c '%y %s bytes %n' \
  /var/lib/prometheus/node-exporter/wazuh_platform.prom
```

The service had failed, and the log contained the following error. The `.prom` file had not been rewritten either.

```text
subprocess.TimeoutExpired:
wazuh-control status timed out after 10 seconds
```

```bash
echo "===== PLATFORM METRICS PROCESSES ====="
ps -eo pid,ppid,stat,etime,args | grep -E '[w]azuh-platform-metrics|[w]azuh-control|[w]azuh-control status'

echo "===== WAZUH MANAGER SERVICE ====="
systemctl show wazuh-manager.service \
  -p ActiveState -p SubState -p MainPID -p Result

echo "===== MANAGER PROCESS SUMMARY ====="
ps -eo stat,comm | grep -E 'wazuh|PID' | head -40
```

Wazuh Manager was `active` / `running`, and the 9 daemons were running. What was stuck was `/bin/sh /var/ossec/bin/wazuh-control status`, waiting for an answer.

## 3.2 Stopping Only the Monitoring Service

While investigating, stop only the monitoring timer and service. Wazuh Manager and the Collector are not stopped.

```bash
systemctl stop wazuh-platform-metrics.timer

echo "===== TIMER STATE ====="
systemctl is-active wazuh-platform-metrics.timer

echo "===== METRICS SERVICE STATE ====="
systemctl show wazuh-platform-metrics.service \
  -p ActiveState -p SubState -p Result -p ExecMainStatus

echo "===== REMAINING PROCESSES ====="
ps -eo pid,ppid,stat,etime,args | grep -E '[w]azuh-platform-metrics|[w]azuh-control'
```

The timer stopped, but the service that had already started (`activating`) and `wazuh-control status` remained.

```bash
systemctl stop wazuh-platform-metrics.service

echo "===== METRICS SERVICE ====="
systemctl show wazuh-platform-metrics.service \
  -p ActiveState -p SubState -p Result -p ExecMainStatus

echo "===== REMAINING PROCESSES ====="
ps -eo pid,ppid,stat,etime,args | grep -E '[w]azuh-platform-metrics|[w]azuh-control'
```

The service became `failed`, and no processes remained.

## 3.3 Investigating the Cause

```bash
echo "===== STATUS IMPLEMENTATION ====="
grep -n -A100 -B20 'status)' /var/ossec/bin/wazuh-control | head -140

echo "===== STATUS RELATED FUNCTIONS ====="
grep -n -E 'status|is_running|pid|timeout|sleep' \
  /var/ossec/bin/wazuh-control | head -100

echo "===== MANAGER PROCESS DETAILS ====="
ps -eo pid,ppid,stat,wchan:24,etime,comm | grep -E 'wazuh|PID'
```

`status` first takes a lock and then checks all daemons.

```bash
echo "===== LOCK IMPLEMENTATION ====="
sed -n '35,110p' /var/ossec/bin/wazuh-control

echo "===== STATUS FUNCTION ====="
sed -n '180,235p' /var/ossec/bin/wazuh-control

echo "===== LOCK FILE STATE ====="
ls -la /var/ossec/var/run/wazuh-control* \
  /var/ossec/var/run/*.lock 2>/dev/null
```

It **waits up to 60 seconds** for the lock, exceeding the script's 10-second limit. The monitoring has no need to call `wazuh-control`. Check how Wazuh itself checks daemon state (PID files).

```bash
echo "===== WAZUH PID FILES ====="
find /var/ossec/var/run -maxdepth 1 -type f \
  -name 'wazuh-*.pid' -printf '%f\n' | sort

echo "===== PSTATUS IMPLEMENTATION ====="
sed -n '460,498p' /var/ossec/bin/wazuh-control

echo "===== START SCRIPT LOCK DIRECTORY ====="
ls -ld /var/ossec/var/start-script-lock 2>&1
```

All 9 daemons had a `wazuh-<name>-<PID>.pid` file, and the PIDs matched the process list. `pstatus()` simply reads the PID file and checks with `kill -0` that the process is alive.

# Chapter 4: Changing It to Look at PID Files

## 4.1 Replacing the Function

Replace only `manager_status()` with a version that checks the PID files and `os.kill(pid, 0)`. The HTTP checks and the writing code stay as they are.

In the original build, the script was first backed up with the following command, and then a regular-expression replacement was attempted.

`cp -a /usr/local/sbin/wazuh-platform-metrics.py /usr/local/sbin/wazuh-platform-metrics.py.pre-pid-check-20261122`

At that time the replacement failed because of a mistake in the regular expression, and the script was not changed (the backup was made). So, without regular expressions, we replace from the start of the function to the start of the next function.

> **Run on: VM 220**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/usr/local/sbin/wazuh-platform-metrics.py")
source = path.read_text()

start = source.index("def manager_status():")
end = source.index("def endpoint_status(", start)

replacement = '''def manager_status():
    statuses = {}

    for daemon in REQUIRED_DAEMONS:
        running = False
        pid_files = sorted(
            Path("/var/ossec/var/run").glob(f"{daemon}-*.pid")
        )

        for pid_file in pid_files:
            try:
                pid = int(pid_file.read_text().strip())
                if pid > 1:
                    os.kill(pid, 0)
                    running = True
                    break
            except (ValueError, OSError):
                continue

        statuses[daemon] = int(running)

    manager_up = int(all(statuses.values()))
    return manager_up, statuses

'''

path.write_text(source[:start] + replacement + source[end:])
print("REPLACEMENT=SUCCESS")
PY

echo "===== SYNTAX CHECK ====="
python3 -m py_compile /usr/local/sbin/wazuh-platform-metrics.py
echo "SYNTAX_EXIT=$?"

echo "===== UPDATED FUNCTION ====="
sed -n '35,75p' /usr/local/sbin/wazuh-platform-metrics.py
```

`REPLACEMENT=SUCCESS` and `SYNTAX_EXIT=0`.

## 4.2 Testing the Fixed Script

The timer stays stopped.

```bash
echo "===== RUN UPDATED METRICS SCRIPT ====="
/usr/bin/python3 /usr/local/sbin/wazuh-platform-metrics.py
echo "SCRIPT_EXIT=$?"

echo "===== MANAGER METRICS ====="
grep -E '^wazuh_manager_' \
  /var/lib/prometheus/node-exporter/wazuh_platform.prom

echo "===== ENDPOINT METRICS ====="
grep -E '^wazuh_(indexer|dashboard|api)_' \
  /var/lib/prometheus/node-exporter/wazuh_platform.prom

echo "===== FILE UPDATE ====="
stat -c '%y %s bytes %n' \
  /var/lib/prometheus/node-exporter/wazuh_platform.prom
```

`SCRIPT_EXIT=0`, with `wazuh_manager_up 1`, all 9 daemons 1, and all three HTTP checks `up 1`.

Test whether it also works under systemd's restrictions.

```bash
systemctl reset-failed wazuh-platform-metrics.service

echo "===== RUN SYSTEMD SERVICE ====="
systemctl start wazuh-platform-metrics.service
echo "START_EXIT=$?"

echo "===== SERVICE RESULT ====="
systemctl show wazuh-platform-metrics.service \
  -p ActiveState -p SubState -p Result -p ExecMainStatus

echo "===== SERVICE LOG ====="
journalctl -u wazuh-platform-metrics.service -n 15 --no-pager

echo "===== METRICS FILE ====="
stat -c '%y %s bytes %n' \
  /var/lib/prometheus/node-exporter/wazuh_platform.prom
```

`START_EXIT=0`, `Result=success` and `ExecMainStatus=0` (for a oneshot, becoming `inactive` / `dead` after finishing is normal).

## 4.3 Restoring the Timer

```bash
systemctl enable --now wazuh-platform-metrics.timer

echo "===== TIMER STATE ====="
systemctl is-active wazuh-platform-metrics.timer
systemctl is-enabled wazuh-platform-metrics.timer

echo "===== TIMER SCHEDULE ====="
systemctl list-timers --all wazuh-platform-metrics.timer --no-pager
```

After a short while, check that it keeps running.

```bash
echo "===== TIMER DETAILS ====="
systemctl show wazuh-platform-metrics.timer \
  -p ActiveState -p SubState -p LastTriggerUSec \
  -p NextElapseUSecRealtime -p Result

echo "===== SERVICE RESULT ====="
systemctl show wazuh-platform-metrics.service \
  -p ActiveState -p SubState -p Result -p ExecMainStatus

echo "===== RECENT LOG ====="
journalctl -u wazuh-platform-metrics.service -n 12 --no-pager

echo "===== METRICS FILE ====="
stat -c '%y %s bytes %n' \
  /var/lib/prometheus/node-exporter/wazuh_platform.prom
```

The timer was `active` / `waiting`, the service `success`, and the `.prom` file was being rewritten every 15 seconds.

## 4.4 Visible from Node Exporter?

> **Caution**: Node Exporter listens on `192.168.0.220:9100`, not `127.0.0.1`. `http://127.0.0.1:9100/metrics` cannot connect.

```bash
echo "===== NODE EXPORTER PLATFORM METRICS ====="
curl -fsS http://192.168.0.220:9100/metrics \
  | grep -E '^wazuh_(manager|indexer|dashboard|api)_'
```

`wazuh_manager_up`, the 9 `wazuh_manager_daemon_up` series, `wazuh_indexer_up`, `wazuh_dashboard_up`, `wazuh_api_up` and others were shown.

# Chapter 5: Ingesting into Prometheus

## 5.1 Were They Ingested?

> **Run on: pve** (run at `root@pve:~#`; `pct` cannot be used on VM 220)

```bash
pct exec 103 -- bash -lc '
echo "===== PROMETHEUS TARGET ====="
curl -fsS "http://127.0.0.1:9090/api/v1/query?query=up%7Bjob%3D%22security-core%22%7D"

echo
echo "===== WAZUH MANAGER ====="
curl -fsS "http://127.0.0.1:9090/api/v1/query?query=wazuh_manager_up"

echo
echo "===== WAZUH INDEXER ====="
curl -fsS "http://127.0.0.1:9090/api/v1/query?query=wazuh_indexer_up"

echo
echo "===== WAZUH DASHBOARD ====="
curl -fsS "http://127.0.0.1:9090/api/v1/query?query=wazuh_dashboard_up"

echo
echo "===== WAZUH API ====="
curl -fsS "http://127.0.0.1:9090/api/v1/query?query=wazuh_api_up"
echo
'
```

All were `status=success` with value `1`, ingested with `job="security-core"` and `instance="192.168.0.220:9100"`. Prometheus's settings were not changed.

```bash
pct exec 103 -- bash -lc '
echo "===== WAZUH MANAGER DAEMON METRICS ====="
curl -fsS -G "http://127.0.0.1:9090/api/v1/query" \
  --data-urlencode "query=wazuh_manager_daemon_up"

echo
echo "===== DAEMON METRIC COUNT ====="
curl -fsS -G "http://127.0.0.1:9090/api/v1/query" \
  --data-urlencode "query=count(wazuh_manager_daemon_up)"
echo
'
```

There were 9 `wazuh_manager_daemon_up` series, all 1, and `count(wazuh_manager_daemon_up)` was `9`.

# Chapter 6: Alert Rules for the Wazuh Platform

In the original build, approval was obtained before adding the rules.

## 6.1 The Current Rules

```bash
pct exec 103 -- bash -lc '
echo "===== EXISTING WAZUH COLLECTOR RULES ====="
cat /etc/prometheus/rules/wazuh-collector-alerts.yml

echo
echo "===== REGISTERED RULE FILES ====="
grep -n -A5 -B2 "rule_files:" /etc/prometheus/prometheus.yml
'
```

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

```bash
pct exec 103 -- bash -lc '
FILE=/etc/prometheus/rules/wazuh-platform-alerts.yml

if [ -e "$FILE" ]; then
    echo "ERROR: File already exists; refusing to overwrite."
    stat "$FILE"
else
    cat > "$FILE" <<'"'"'YAML'"'"'
groups:
  - name: wazuh-platform
    interval: 15s
    rules:
      - alert: WazuhManagerDown
        expr: wazuh_manager_up{job="security-core"} == 0
        for: 1m
        labels:
          severity: critical
          component: wazuh-manager
        annotations:
          summary: "Wazuh Manager is not running"
          description: "Wazuh Manager has been unavailable for at least 1 minute."

      - alert: WazuhManagerDaemonDown
        expr: wazuh_manager_daemon_up{job="security-core"} == 0
        for: 1m
        labels:
          severity: critical
          component: wazuh-manager
        annotations:
          summary: "A required Wazuh Manager daemon is down"
          description: "A required Wazuh Manager daemon has been down for at least 1 minute. Check the daemon label."

      - alert: WazuhIndexerDown
        expr: wazuh_indexer_up{job="security-core"} == 0
        for: 1m
        labels:
          severity: critical
          component: wazuh-indexer
        annotations:
          summary: "Wazuh Indexer is unreachable"
          description: "Wazuh Indexer health endpoint has failed for at least 1 minute."

      - alert: WazuhDashboardDown
        expr: wazuh_dashboard_up{job="security-core"} == 0
        for: 1m
        labels:
          severity: warning
          component: wazuh-dashboard
        annotations:
          summary: "Wazuh Dashboard is unreachable"
          description: "Wazuh Dashboard endpoint has failed for at least 1 minute."

      - alert: WazuhAPIDown
        expr: wazuh_api_up{job="security-core"} == 0
        for: 1m
        labels:
          severity: critical
          component: wazuh-api
        annotations:
          summary: "Wazuh API is unreachable"
          description: "Wazuh API endpoint has failed for at least 1 minute."

      - alert: WazuhPlatformMetricsMissing
        expr: absent(wazuh_manager_up{job="security-core"}) or absent(wazuh_indexer_up{job="security-core"}) or absent(wazuh_dashboard_up{job="security-core"}) or absent(wazuh_api_up{job="security-core"})
        for: 1m
        labels:
          severity: critical
          component: wazuh-platform
        annotations:
          summary: "Wazuh Platform metrics are missing"
          description: "One or more Wazuh Platform health metrics have been absent from Prometheus for at least 1 minute."

      - alert: WazuhPlatformMetricsStale
        expr: time() - node_textfile_mtime_seconds{job="security-core",file="/var/lib/prometheus/node-exporter/wazuh_platform.prom"} > 60
        for: 0m
        labels:
          severity: critical
          component: wazuh-platform
        annotations:
          summary: "Wazuh Platform metrics file is stale"
          description: "The Wazuh Platform metrics textfile has not been updated for more than 60 seconds."
YAML
    echo "FILE_CREATED=$?"
    chmod 0644 "$FILE"
    echo "===== FILE DETAILS ====="
    stat -c "%A %U:%G %s bytes %n" "$FILE"
fi
'
```

It was created as `-rw-r--r-- root:root 2823 bytes`.

## 6.3 Checking and Loading

```bash
pct exec 103 -- bash -lc '
echo "===== PLATFORM RULE VALIDATION ====="
promtool check rules /etc/prometheus/rules/wazuh-platform-alerts.yml
echo "PLATFORM_RULE_EXIT=$?"

echo
echo "===== FULL PROMETHEUS CONFIG VALIDATION ====="
promtool check config /etc/prometheus/prometheus.yml
echo "CONFIG_EXIT=$?"
'
```

The Wazuh platform rules gave `SUCCESS: 7 rules found`; the whole-configuration check also read the Collector rules (9) and the two files, and all exit codes were 0.

```bash
pct exec 103 -- bash -lc '
echo "===== PROMETHEUS RELOAD ====="
systemctl reload prometheus
echo "RELOAD_EXIT=$?"

echo
echo "===== SERVICE STATUS ====="
systemctl is-active prometheus

echo
echo "===== MAIN PID ====="
systemctl show prometheus -p MainPID

echo
echo "===== RECENT LOG ====="
journalctl -u prometheus -n 15 --no-pager
'
```

`RELOAD_EXIT=0`; Prometheus was `active`, its PID stayed `98`, and `Completed loading of configuration file` appeared.

## 6.4 Checking the 16 Rules

```bash
pct exec 103 -- bash -lc '
echo "===== WAZUH ALERT RULES ====="
curl -fsS "http://127.0.0.1:9090/api/v1/rules" \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
groups=data.get(\"data\",{}).get(\"groups\",[])
for group in groups:
    if group.get(\"name\", \"\").startswith(\"wazuh-\"):
        rules=group.get(\"rules\",[])
        print(\"GROUP:\", group[\"name\"])
        for rule in rules:
            print(
                rule.get(\"name\"),
                \"health=\" + str(rule.get(\"health\")),
                \"state=\" + str(rule.get(\"state\"))
            )
        print(\"COUNT:\", len(rules))
"

echo
echo "===== ACTIVE ALERT COUNT ====="
curl -fsS "http://127.0.0.1:9090/api/v1/alerts" \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
alerts=data.get(\"data\",{}).get(\"alerts\",[])
print(\"ACTIVE_ALERT_COUNT:\",len(alerts))
"
'
```

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

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

```bash
chown root:ai-defense \
  /opt/ai-defense-manager/app/api/wazuh.py \
  /opt/ai-defense-manager/app/schemas/wazuh.py \
  /opt/ai-defense-manager/app/services/wazuh_relay.py \
&& chmod 640 \
  /opt/ai-defense-manager/app/api/wazuh.py \
  /opt/ai-defense-manager/app/schemas/wazuh.py \
  /opt/ai-defense-manager/app/services/wazuh_relay.py \
&& stat -c '%A %U:%G %n' \
  /opt/ai-defense-manager/app/api/wazuh.py \
  /opt/ai-defense-manager/app/schemas/wazuh.py \
  /opt/ai-defense-manager/app/services/wazuh_relay.py
```

Before making it a service, confirm that the run-as user `ai-defense` can load the whole application (the server is not started).

```bash
cd /opt/ai-defense-manager && runuser -u ai-defense -- ./venv/bin/python - <<'PY'
from app.main import app
from app.core.config import settings

print("APP_IMPORT_OK")
print("APP_NAME:", settings.app_name)
print("API_HOST:", settings.api_host)
print("API_PORT:", settings.api_port)
print("OLLAMA_URL:", settings.ollama_base_url)
print("OPENAPI_PATH_COUNT:", len(app.openapi()["paths"]))

for path in sorted(app.openapi()["paths"]):
    print("ROUTE:", path)

print("SERVICE_USER_IMPORT_TEST_OK")
PY
```

At build time, four routes were shown: `/health`, `/api/v1/analysis`, `/api/v1/wazuh/events` and `/api/v1/wazuh/analyze`.

# Chapter 2: The systemd Service

## 2.1 The Unit File

> **Run on: VM 230**

Confirm that no unit with the same name exists.

```bash
systemctl list-unit-files --type=service | grep -E 'ai-defense-manager|ai-defense' || true
```

Following the same approach as the Relay in Part 14, make it a tightly restricted service.

- Runs as `ai-defense`
- Listens only on `127.0.0.1:8000` (not exposed externally)
- The file system is read-only in principle (`ProtectSystem=strict`)
- No privileges; no access to the kernel or devices
- Memory limit of 1 GiB; restarts automatically only on abnormal exit

```bash
cat > /etc/systemd/system/ai-defense-manager.service <<'UNIT'
[Unit]
Description=AI Defense Manager API
After=network.target
Wants=network.target

[Service]
Type=simple
User=ai-defense
Group=ai-defense
WorkingDirectory=/opt/ai-defense-manager

ExecStart=/opt/ai-defense-manager/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=5
UMask=0077

NoNewPrivileges=yes
CapabilityBoundingSet=
AmbientCapabilities=
PrivateTmp=yes
PrivateDevices=yes
ProtectSystem=strict
ProtectHome=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
ProtectControlGroups=yes
ProtectClock=yes
ProtectHostname=yes
ProtectProc=invisible
ProcSubset=pid
RestrictSUIDSGID=yes
LockPersonality=yes
MemoryDenyWriteExecute=yes
RestrictRealtime=yes
SystemCallArchitectures=native
RestrictAddressFamilies=AF_INET

MemoryMax=1G
TasksMax=64
LimitNOFILE=4096

[Install]
WantedBy=multi-user.target
UNIT
```

Pasting can make the end look garbled, so check that it was written to the end.

```bash
tail -n 15 /etc/systemd/system/ai-defense-manager.service
```

```bash
systemd-analyze verify /etc/systemd/system/ai-defense-manager.service
```

## 2.2 Registering

```bash
systemctl daemon-reload && systemctl show ai-defense-manager.service -p LoadState -p ActiveState -p UnitFileState -p User -p Group -p ExecStart
```

If it shows `LoadState=loaded`, `ActiveState=inactive` (still stopped), `UnitFileState=disabled` and `User=ai-defense`, it has been registered.

## 2.3 Starting

```bash
systemctl start ai-defense-manager.service && systemctl status ai-defense-manager.service --no-pager -l
```

If it becomes `active (running)`, it has started.

```bash
ss -lntp '( sport = :8000 )' && curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8000/health
```

At build time it listened only on `127.0.0.1:8000` and returned `{"status":"ok","service":"ai-defense-manager","version":"0.1.0"}`.

# Chapter 3: Checking over HTTP

> **Run on: VM 230** (run in `/opt/ai-defense-manager`)

## 3.1 Fetching Alerts

Fetch five Wazuh alerts without AI analysis.

```bash
curl --fail --silent --show-error --max-time 20 \
  'http://127.0.0.1:8000/api/v1/wazuh/events?limit=5&since_minutes=60' \
  | ./venv/bin/python -c 'import json,sys; data=json.load(sys.stdin); print("EVENT_COUNT:",len(data)); [print({"severity":e["severity"],"rule_id":e["rule_id"],"agent_name":e["agent_name"],"event_category":e["event_category"],"event_summary":e["event_summary"]}) for e in data]; print("WAZUH_HTTP_API_OK")'
```

At build time five alerts were returned: two Proxmox VE authentication successes, one deletion of a user (group), and one each for the start and end of a PAM login session.

## 3.2 AI Analysis

Pass up to five alerts to `qwen3:8b`. The AI only analyzes and proposes; it does not carry out defensive operations.

```bash
curl --fail --silent --show-error --max-time 180 \
  -X POST 'http://127.0.0.1:8000/api/v1/wazuh/analyze' \
  -H 'Content-Type: application/json' \
  -d '{
    "limit": 5,
    "since_minutes": 60,
    "analysis_context": "直近のWazuhセキュリティイベントを分析してください。防御操作は提案のみとし、実行しないでください。",
    "requested_language": "ja"
  }' \
  | ./venv/bin/python -c 'import json,sys; d=json.load(sys.stdin); print("severity:",d.get("severity")); print("confidence:",d.get("confidence")); print("recommended_action:",d.get("recommended_action")); print("requires_human_approval:",d.get("requires_human_approval")); print("evidence_event_count:",len(d.get("evidence_event_ids",[]))); print("target_ip:",d.get("target_ip")); print("ttl_seconds:",d.get("ttl_seconds")); print("summary:",d.get("summary")); print("reasoning:",d.get("reasoning")); print("WAZUH_HTTP_AI_ANALYSIS_OK")'
```

At build time it returned `severity: info`, `confidence: 0.8`, `recommended_action: no_action` and `evidence_event_count: 5`.

At this point the following flow is connected.

```text
Wazuh Indexer (VM 220)
  → Relay (VM 220, HTTPS + Bearer)
  → AI Defense Manager (VM 230, 127.0.0.1:8000)
  → Ollama qwen3:8b (VM 101)
  → Defense proposal (JSON; not executed)
```

# Chapter 4: Automatic Start

## 4.1 The Current State

> **Run on: VM 230**

```bash
systemctl is-enabled ai-defense-manager.service; systemctl is-active ai-defense-manager.service; systemctl show ai-defense-manager.service -p After -p Wants -p Restart -p RestartSec -p User -p Group
```

> **Run on: VM 220**

```bash
systemctl is-enabled ai-defense-relay.service; systemctl is-active ai-defense-relay.service; systemctl show ai-defense-relay.service -p After -p Wants -p Restart -p RestartSec -p User -p Group
```

At build time, both were `active` and `disabled` (no automatic start). The Relay starts after the Indexer because of `After=wazuh-indexer.service`.

## 4.2 Enabling It

> **Run on: VM 220**

```bash
systemctl enable ai-defense-relay.service && systemctl is-enabled ai-defense-relay.service
```

> **Run on: VM 230**

```bash
systemctl enable ai-defense-manager.service && systemctl is-enabled ai-defense-manager.service
```

It is done when both show `enabled`. The running services are not affected.

# Chapter 5: Proxmox Startup Order

Make VM 220 (Wazuh and the Relay) start before VM 230 (the AI Defense Manager).

## 5.1 The Current Settings

> **Run on: pve**

```bash
for id in 220 230; do
  echo "===== VM $id ====="
  qm status "$id"
  qm config "$id" | grep -E '^(onboot|startup):' || echo "onboot/startup not configured"
done
```

At build time, VM 220 had `onboot: 1` (automatic start) with no order set, and VM 230 had neither automatic start nor an order set.

## 5.2 Setting the Order

Running VMs are not stopped.

- VM 220: automatic start, order 1, wait 120 seconds after starting before the next VM
- VM 230: automatic start, order 2

```bash
qm set 220 --onboot 1 --startup order=1,up=120
```

```bash
qm set 230 --onboot 1 --startup order=2
```

```bash
for id in 220 230; do
  echo "===== VM $id ====="
  qm status "$id"
  qm config "$id" | grep -E '^(onboot|startup):'
done
```

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

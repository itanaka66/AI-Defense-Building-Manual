---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 50: Deploying the New Code and a Static Address for VM 230"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 50 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". By Part 49 we had fixed the code of the Relay on VM 220 and the AI Defense Manager on VM 230, and restarted only the Relay. Here we do the following.

1. Restart `ai-defense-manager.service` on VM 230 so that it loads the new code
2. Change VM 230's address from the DHCP-assigned `192.168.0.33` to a static `192.168.0.221` (DHCP is not used)
3. Fix the old address (the client allowed to connect) left in the Relay on VM 220 to the new address

Numbering it next to VM 220 (`192.168.0.220`) makes it easier to manage.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **VM 230 (console)**: logged in as root from the Console of VM 230 in the Proxmox web interface
  - **VM 220**: security-core (root)

# Chapter 1: Restarting the AI Defense Manager

## 1.1 Restart

We restart only the AI Defense Manager service. At this point the address is still `192.168.0.33`.

> **Run on: VM 230**

```bash
echo "===== VM230: APPROVED AI DEFENSE MANAGER RESTART ====="

echo
echo "--- Restart service ---"
systemctl restart ai-defense-manager.service
echo "RESTART_EXIT=$?"

echo
echo "--- Active state ---"
systemctl is-active ai-defense-manager.service

echo
echo "--- Service status ---"
systemctl status ai-defense-manager.service --no-pager -l

echo
echo "--- Process metadata ---"
systemctl show ai-defense-manager.service \
  -p MainPID \
  -p ActiveState \
  -p SubState \
  -p User \
  -p WorkingDirectory

echo
echo "--- Local health endpoint ---"
curl --max-time 5 -sS -i http://127.0.0.1:8000/health

echo
echo "NETWORK_CONFIGURATION_CHANGED=NO"
echo "WAZUH_RELAY_REQUEST=NO"
echo "OLLAMA_REQUEST=NO"
echo "DATABASE_ACCESSED=NO"
```

The restart succeeded and systemd showed `active (running)`, but `/health` could not be reached. It was checked about 15ms after the restart, so presumably Uvicorn had not yet started listening on port 8000.

## 1.2 Checking the Startup

> **Run on: VM 230**

```bash
echo "===== VM230: POST-RESTART API HEALTH VERIFICATION ====="

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "--- Listener port 8000 ---"
ss -lntp '( sport = :8000 )'

echo
echo "--- Health endpoint retry ---"
for i in 1 2 3 4 5; do
  echo "ATTEMPT=$i"
  curl --max-time 3 -sS -i http://127.0.0.1:8000/health
  CURL_STATUS=$?
  echo "CURL_EXIT=$CURL_STATUS"
  if [ "$CURL_STATUS" -eq 0 ]; then
    break
  fi
  sleep 2
done

echo
echo "--- Recent service logs ---"
journalctl -u ai-defense-manager.service -n 40 --no-pager

echo
echo "--- Process metadata ---"
systemctl show ai-defense-manager.service \
  -p MainPID -p ActiveState -p SubState

echo
echo "WAZUH_RELAY_REQUEST=NO"
echo "OLLAMA_REQUEST=NO"
echo "DATABASE_ACCESSED=NO"
```

| Item | Result |
|---|---|
| systemd | `active (running)` |
| MainPID | `1640` |
| Uvicorn startup, application startup | succeeded |
| Listening | `127.0.0.1:8000` |
| `/health` | `HTTP 200` |
| Version | `0.1.0` |

Now the code fixed in Parts 48 and 49 is running on both VM 220 and VM 230.

# Chapter 2: Fixing VM 230's Address

## 2.1 The Current Settings

> **Run on: VM 230**

```bash
echo "===== VM230: NETWORK CONFIGURATION AUDIT ====="

echo
echo "--- Interface addresses ---"
ip -br address

echo
echo "--- Interface MAC ---"
ip link show enp6s18

echo
echo "--- Routing ---"
ip route

echo
echo "--- DHCP client configuration ---"
grep -RniE 'dhcp|192\.168\.0\.33|192\.168\.0\.221' \
  /etc/network/interfaces \
  /etc/network/interfaces.d \
  /etc/systemd/network \
  /etc/NetworkManager/system-connections \
  2>/dev/null

echo
echo "--- Current listener addresses ---"
ss -lntp

echo
echo "NETWORK_CONFIGURATION_CHANGED=NO"
```

VM 230 received `192.168.0.33/24` by DHCP (NIC `enp6s18`). The API listens only on `127.0.0.1:8000`, so changing the address does not expose the API. However, SSH may be cut temporarily.

## 2.2 DNS and the Management Method

> **Run on: VM 230**

```bash
echo "===== VM230: STATIC IPv4 PREPARATION ====="

echo
echo "--- DNS ---"
resolvectl status enp6s18

echo
echo "--- Netplan files ---"
ls -la /etc/netplan 2>/dev/null
grep -RniE 'dhcp4|dhcp6|addresses|routes|gateway|nameservers|renderer' \
  /etc/netplan 2>/dev/null

echo
echo "--- Network management ---"
systemctl is-active systemd-networkd
systemctl is-active NetworkManager

echo
echo "--- Cloud-init ---"
cloud-init status --long 2>/dev/null

echo
echo "--- Current IPv4 and IPv6 ---"
ip -4 address show dev enp6s18
ip -6 address show dev enp6s18

echo
echo "CONFIGURATION_CHANGED=NO"
```

VM 230 is managed by **Netplan and systemd-networkd**, and `/etc/netplan/50-cloud-init.yaml` had `dhcp4: true`. DNS is `192.168.0.1`, `2404:1a8:7f01:a::3` and `2404:1a8:7f01:b::3`. IPv6 is left on automatic configuration via router advertisements (RA); only IPv4 is made static.

## 2.3 The Whole Configuration, and Address Conflicts

> **Run on: VM 230**

```bash
echo "===== VM230: STATIC IP PRECHANGE AUDIT ====="

echo
echo "--- Complete Netplan configuration ---"
cat /etc/netplan/50-cloud-init.yaml

echo
echo "--- Netplan configuration validation ---"
netplan get

echo
echo "--- IPv4 and IPv6 routes ---"
ip -4 route
ip -6 route

echo
echo "--- Networkd link status ---"
networkctl status enp6s18 --no-pager

echo
echo "--- Current DNS configuration ---"
resolvectl dns enp6s18
resolvectl domain enp6s18

echo
echo "--- Check whether arping is available ---"
command -v arping

echo
echo "--- Check target address 192.168.0.221 ---"
if command -v arping >/dev/null 2>&1; then
  arping -D -I enp6s18 -c 3 -w 5 192.168.0.221
  echo "ARPING_EXIT=$?"
else
  echo "ARPING_NOT_INSTALLED"
fi

echo
echo "NETWORK_CONFIGURATION_CHANGED=NO"
```

`arping` was not installed, so we check with ping and the neighbor cache.

> **Run on: VM 230**

```bash
echo "===== VM230: TARGET IPv4 CONFLICT PRECHECK ====="

echo
echo "--- ICMP reachability ---"
ping -c 3 -W 2 192.168.0.221
echo "PING_EXIT=$?"

echo
echo "--- Neighbor cache ---"
ip neigh show 192.168.0.221

echo
echo "--- Current interface and gateway ---"
ip -br address show enp6s18
ip route show default

echo
echo "NETWORK_CONFIGURATION_CHANGED=NO"
```

There was no ping reply from `192.168.0.221`, and the neighbor cache showed `FAILED`. It does not appear to be in use (devices that do not answer ICMP or that are powered off are possible, so we cannot say for certain there is no conflict).

| Item | After the change |
|---|---|
| IPv4 | `192.168.0.221/24` (static) |
| Gateway | `192.168.0.1` |
| IPv4 DHCP | disabled |
| IPv6 | still automatic via RA |
| DNS | the current three addresses |
| DNS search domain | still `iptvf.jp` |

## 2.4 Creating the Configuration File

We save a copy of the configuration file before rewriting it. At this stage **the configuration is not applied and the interface is not restarted**.

> **Run on: VM 230**

```bash
echo "===== VM230: STATIC IPv4 CONFIGURATION PREPARATION ====="

BACKUP_DIR="/var/backups/ai-defense-manager/netplan-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo
echo "--- Backup original configuration ---"
cp -a /etc/netplan/50-cloud-init.yaml "$BACKUP_DIR/50-cloud-init.yaml"
sha256sum /etc/netplan/50-cloud-init.yaml "$BACKUP_DIR/50-cloud-init.yaml"

echo
echo "--- Write static IPv4 configuration ---"
cat > /tmp/50-cloud-init.yaml.new <<'YAML'
network:
  version: 2
  ethernets:
    enp6s18:
      dhcp4: false
      dhcp6: false
      accept-ra: true
      addresses:
        - 192.168.0.221/24
      routes:
        - to: default
          via: 192.168.0.1
      nameservers:
        addresses:
          - 192.168.0.1
          - 2404:1a8:7f01:a::3
          - 2404:1a8:7f01:b::3
        search:
          - iptvf.jp
YAML

install -o root -g root -m 600 \
  /tmp/50-cloud-init.yaml.new \
  /etc/netplan/50-cloud-init.yaml

echo
echo "--- New configuration ---"
cat /etc/netplan/50-cloud-init.yaml

echo
echo "--- Netplan parse validation ---"
netplan get

echo
echo "--- Netplan generation validation ---"
netplan generate
echo "NETPLAN_GENERATE_EXIT=$?"

echo
echo "--- Backup location ---"
echo "$BACKUP_DIR"

echo
echo "NETWORK_APPLIED=NO"
echo "INTERFACE_RESTARTED=NO"
```

The copy of the original configuration (SHA256 match), the Netplan syntax check and `netplan generate` (exit code `0`) all succeeded.

## 2.5 Applying with `netplan try`

SSH is cut when the address changes, so run this from **VM 230's Console in the Proxmox web interface**. `netplan try` asks for confirmation after applying and reverts if you do not confirm.

> **Run on: VM 230 (console)**

```bash
echo "===== VM230: STATIC IPv4 APPLY WITH ROLLBACK ====="

echo
echo "--- Confirm current and target configuration ---"
ip -br address show enp6s18
cat /etc/netplan/50-cloud-init.yaml

echo
echo "--- Apply using netplan try ---"
netplan try --timeout 120

echo
echo "--- Apply command exit status ---"
echo "NETPLAN_TRY_EXIT=$?"

echo
echo "--- Current IPv4 address ---"
ip -4 address show dev enp6s18

echo
echo "--- Default route ---"
ip -4 route show default

echo
echo "CHECK_API_AFTER_NETWORK_CHANGE=REQUIRED"
```

> **Important:** When `netplan try` asks for confirmation, confirm only after checking that the address has become `.221` and communication works. If it is still `.33`, do not confirm.

`netplan try` finished normally and the configuration was confirmed. It did not revert automatically.

## 2.6 Checking After Applying

> **Run on: VM 230 (console)**

```bash
echo "===== VM230: STATIC IPv4 POST-APPLY VERIFICATION ====="

echo
echo "--- IPv4 address ---"
ip -4 address show dev enp6s18

echo
echo "--- DHCP status in Netplan ---"
netplan get

echo
echo "--- Default route ---"
ip -4 route show default

echo
echo "--- IPv6 status ---"
ip -6 address show dev enp6s18
ip -6 route show default

echo
echo "--- DNS ---"
resolvectl status enp6s18

echo
echo "--- Gateway connectivity ---"
ping -c 3 -W 2 192.168.0.1

echo
echo "--- API listener ---"
ss -lntp '( sport = :8000 )'

echo
echo "--- API health ---"
curl --max-time 5 -sS -i http://127.0.0.1:8000/health

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "NETWORK_CONFIGURATION_CHANGED=YES"
echo "WAZUH_RELAY_REQUEST=NO"
echo "OLLAMA_REQUEST=NO"
echo "DATABASE_ACCESSED=NO"
```

| Checked | Result |
|---|---|
| IPv4 | `192.168.0.221/24` (lifetime `forever`) |
| IPv4 DHCP | disabled |
| Default route | `192.168.0.1`; ping to the gateway succeeded 3/3 |
| IPv6 RA | normal |
| DNS | normal with the three addresses |
| API listening | `127.0.0.1:8000` |
| `/health` | `HTTP 200` |
| systemd | `active` |

# Chapter 3: Fixing the Address the Relay Allows

## 3.1 Where the Old Address Remains

The Relay on VM 220 is the side VM 230 connects to, so we check whether VM 230's old address remains in its settings.

> **Run on: VM 220**

```bash
echo "===== VM220: VM230 OLD IP REFERENCE AUDIT ====="

echo
echo "--- Relay application references ---"
grep -RInE \
  '192\.168\.0\.(33|221)' \
  /opt/ai-defense-relay \
  --exclude='*.pyc' \
  2>/dev/null

echo
echo "--- Systemd unit references ---"
grep -nE '192\.168\.0\.(33|221)' \
  /etc/systemd/system/ai-defense-relay.service \
  /etc/systemd/system/ai-defense-relay.service.d/* \
  2>/dev/null

echo
echo "--- Relay service metadata (environment values excluded) ---"
systemctl show ai-defense-relay.service \
  -p MainPID \
  -p ActiveState \
  -p SubState \
  -p User \
  -p WorkingDirectory \
  -p FragmentPath

echo
echo "--- Current Relay listener ---"
ss -lntp '( sport = :8765 )'

echo
echo "CONFIGURATION_CHANGED=NO"
echo "NETWORK_REQUESTS=NO"
echo "CREDENTIALS_DISPLAYED=NO"
```

Line 16 of `/opt/ai-defense-relay/relay.py` still had `ALLOWED_CLIENT = "192.168.0.33"`.

## 3.2 How It Is Used

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY CLIENT IP AUTHORIZATION AUDIT ====="

cd /opt/ai-defense-relay || true

echo
echo "--- ALLOWED_CLIENT definition and references ---"
grep -n -C 8 'ALLOWED_CLIENT' relay.py

echo
echo "--- Request client address handling ---"
grep -n -C 5 -E 'client\.host|remote_addr|X-Forwarded-For|request\.client' relay.py

echo
echo "--- Source metadata and current hash ---"
stat -c 'owner=%U:%G mode=%a size=%s' relay.py
sha256sum relay.py

echo
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
```

The Relay checks clients in two stages.

1. The source IP address matches `ALLOWED_CLIENT`
2. The `Authorization: Bearer ...` token matches

As it is, connections from VM 230's new address would be refused. Only one line of `relay.py` is changed; the API token, Wazuh settings, allowed fields, and listening address and port are not changed.

## 3.3 Fixing One Line and Restarting

We make a copy, check that only one line changed, the Python syntax and the file permissions, and then restart the Relay.

> **Run on: VM 220**

```bash
echo "===== VM220: UPDATE ALLOWED CLIENT IP ====="

cd /opt/ai-defense-relay || true

echo
echo "--- Create verified backup and update exactly one line ---"

python3 - <<'PY'
from pathlib import Path
from datetime import datetime
import shutil
import hashlib
import os
import sys

src = Path("/opt/ai-defense-relay/relay.py")
backup_dir = Path("/var/backups/ai-defense-relay/20261123-client-ip-1403")
backup = backup_dir / "relay.py"

if not src.is_file():
    print("ERROR: source file missing")
    sys.exit(1)

original = src.read_text(encoding="utf-8")
old = 'ALLOWED_CLIENT = "192.168.0.33"'
new = 'ALLOWED_CLIENT = "192.168.0.221"'

if original.count(old) != 1:
    print(f"ERROR: expected exactly one old setting, found {original.count(old)}")
    sys.exit(1)

if 'ALLOWED_CLIENT = "192.168.0.221"' in original:
    print("ERROR: target setting already exists")
    sys.exit(1)

backup_dir.mkdir(parents=True, exist_ok=False)
shutil.copy2(src, backup)

original_hash = hashlib.sha256(src.read_bytes()).hexdigest()
backup_hash = hashlib.sha256(backup.read_bytes()).hexdigest()

if original_hash != backup_hash:
    print("ERROR: backup hash mismatch; source not changed")
    sys.exit(1)

updated = original.replace(old, new, 1)
compile(updated, str(src), "exec")

tmp = src.with_suffix(".py.tmp")
tmp.write_text(updated, encoding="utf-8")
os.chown(tmp, src.stat().st_uid, src.stat().st_gid)
os.chmod(tmp, src.stat().st_mode)
os.replace(tmp, src)

final = src.read_text(encoding="utf-8")
if final.count(new) != 1 or old in final:
    print("ERROR: post-write verification failed")
    sys.exit(1)

print("BACKUP_PATH=" + str(backup))
print("BACKUP_SHA256=" + backup_hash)
print("ORIGINAL_SHA256=" + original_hash)
print("UPDATED_SHA256=" + hashlib.sha256(src.read_bytes()).hexdigest())
print("CLIENT_IP_CHANGE=192.168.0.33 -> 192.168.0.221")
print("PYTHON_SYNTAX=PASS")
print("FILE_METADATA=" + str(src.stat().st_mode & 0o777))
print("BACKUP_INTEGRITY=PASS")
print("SOURCE_UPDATE=PASS")
PY

PATCH_STATUS=$?
echo "PATCH_EXIT=$PATCH_STATUS"

if [ "$PATCH_STATUS" -eq 0 ]; then
    echo
    echo "--- Restart approved Relay service ---"
    systemctl restart ai-defense-relay.service
    echo "RESTART_EXIT=$?"

    echo
    echo "--- Service state ---"
    systemctl is-active ai-defense-relay.service
    systemctl status ai-defense-relay.service --no-pager -l | head -25

    echo
    echo "--- Listener ---"
    ss -lntp '( sport = :8765 )'

    echo
    echo "--- Final source verification ---"
    grep -n '^ALLOWED_CLIENT' /opt/ai-defense-relay/relay.py
    sha256sum /opt/ai-defense-relay/relay.py
else
    echo "SERVICE_RESTARTED=NO"
fi

echo
echo "WAZUH_INDEXER_REQUEST=NO"
echo "VM230_API_REQUEST=NO"
echo "DATABASE_ACCESSED=NO"
```

It changed to `ALLOWED_CLIENT = "192.168.0.221"`, the copy's SHA256 matched, the syntax check passed, permissions stayed `640`, the restart gave exit code `0`, and the state was `active`.

## 3.4 Checking the Listening Port

Right after the restart, `ss` did not yet show port 8765 listening, so we wait a little and check.

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY POST-RESTART LISTENER VERIFICATION ====="

echo
echo "--- Wait briefly for service initialization ---"
sleep 3

echo
echo "--- Service state and process ---"
systemctl is-active ai-defense-relay.service
systemctl show ai-defense-relay.service \
  -p MainPID -p ActiveState -p SubState

echo
echo "--- TCP listener ---"
ss -lntp '( sport = :8765 )'

echo
echo "--- Recent service journal ---"
journalctl -u ai-defense-relay.service -n 20 --no-pager

echo
echo "--- Authorized client setting ---"
grep -n '^ALLOWED_CLIENT' /opt/ai-defense-relay/relay.py

echo
echo "SOURCE_MODIFIED=NO"
echo "WAZUH_INDEXER_REQUEST=NO"
echo "VM230_API_REQUEST=NO"
echo "DATABASE_ACCESSED=NO"
```

| Item | Result |
|---|---|
| Relay | `active (running)`, MainPID `17962` |
| Listening | `192.168.0.220:8765` |
| Allowed client | `192.168.0.221` |

# Closing Notes

In Part 50 we deployed the new code to VM 230 and gave VM 230 a static address.

| Item | Result |
|---|---|
| VM 230 service | restarted and running the new code (`/health` is `HTTP 200`) |
| VM 230 address | `192.168.0.221/24` (static, no DHCP). Copy of the settings in `/var/backups/ai-defense-manager/netplan-…` |
| Relay's allowed client | `192.168.0.33` → `192.168.0.221` |
| Layout | VM 220 `192.168.0.220` (Wazuh, Relay :8765), VM 230 `192.168.0.221` (AI Defense Manager :8000, localhost only) |

In the next part, Part 51, we check TLS and authentication from VM 230 to VM 220 and try fetching real alerts.

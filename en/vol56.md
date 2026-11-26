---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 56: Reviewing and Designing API Authentication"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 56 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". By Part 55 we had put in order the input, output and high-volume protection of the AI Defense Manager on VM 230. The major remaining issue is that **the API has no authentication**. Here, before building authentication, we check the following read-only and decide the design.

1. API authentication and authorization, and the paths that reach the API
2. Local account privileges, and protection of credentials and the DB
3. The network boundary (firewall, IPv6, SSH)
4. Where to integrate authentication, and the token scheme

During the build we decided the following.

- The API is designed on the assumption that **it will later also be used from a Web UI on another VM and from management terminals**
- The Web UI VM has not been decided yet, so source IP restrictions will be added once it is

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: API Authentication and Paths to the API

## 1.1 Authentication and Authorization

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API AUTHENTICATION AND AUTHORIZATION AUDIT ====="

echo
echo "--- 1. API route files ---"
find app/api -maxdepth 3 -type f -name '*.py' -print | sort

echo
echo "--- 2. Analysis API ---"
if [ -f app/api/analysis.py ]; then
    nl -ba app/api/analysis.py
fi

echo
echo "--- 3. Wazuh API ---"
if [ -f app/api/wazuh.py ]; then
    nl -ba app/api/wazuh.py
fi

echo
echo "--- 4. Main application and middleware ---"
nl -ba app/main.py

echo
echo "--- 5. Authentication and authorization references ---"
grep -RInE \
'AuthenticationMiddleware|BaseHTTPMiddleware|HTTPBearer|HTTPBasic|OAuth2|APIKey|Depends\(|Security\(|authenticate|authorize|permission|current_user|CORS|allow_origins' \
app --include='*.py' \
| grep -vE '(__pycache__|test_)' || true

echo
echo "--- 6. Route declarations ---"
grep -RInE \
'@router\.(get|post|put|delete|patch)|@app\.(get|post|put|delete|patch)' \
app --include='*.py' || true

echo
echo "--- 7. OpenAPI security declaration ---"
./venv/bin/python - <<'PY'
from app.main import app

schema = app.openapi()
print("GLOBAL_SECURITY =", schema.get("security", []))
print("SECURITY_SCHEMES =", schema.get("components", {}).get("securitySchemes", {}))

for path, methods in sorted(schema.get("paths", {}).items()):
    for method, operation in sorted(methods.items()):
        if method.lower() in {"get", "post", "put", "patch", "delete"}:
            print(
                method.upper(),
                path,
                "SECURITY =", operation.get("security", "<not declared>")
            )
PY

echo
echo "--- 8. Runtime exposure ---"
ss -lntp | grep ':8000' || true
systemctl is-active ai-defense-manager.service

echo
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
echo "OLLAMA_REQUESTED=NO"
echo "WAZUH_REQUESTED=NO"
echo "DATABASE_WRITES=NO"
```

| Item | Now | Verdict |
|---|---|---|
| API authentication | none | needs action |
| API authorization | none | needs action |
| OpenAPI Security | not defined | needs action |
| Listening | `127.0.0.1` only | good |
| `/health` | no authentication | acceptable if internal only |
| Body size limit | 256KiB | done |
| Concurrent analysis limit | 1 | done |

Through the analysis APIs, local processes can request Ollama inference and SQLite writes without authentication.

## 1.2 Paths to the API

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API INGRESS AND LOCAL CALLER AUDIT ====="

echo
echo "--- 1. All listening TCP sockets ---"
ss -lntp

echo
echo "--- 2. Current connections to API port ---"
ss -tnp | grep -E '(:8000[[:space:]]|:8000$)' || true

echo
echo "--- 3. Local references to AI Defense API ---"
for DIR in \
    /etc/systemd/system \
    /etc/nginx \
    /etc/apache2 \
    /etc/caddy \
    /etc/cloudflared \
    /opt
do
    if [ -d "$DIR" ]; then
        echo "### $DIR"
        grep -RIlE \
            '127\.0\.0\.1:8000|localhost:8000|ai-defense-manager:8000' \
            "$DIR" \
            --exclude='*.pyc' \
            --exclude-dir=venv \
            --exclude-dir=.git \
            --exclude-dir=__pycache__ \
            2>/dev/null | head -80
    fi
done

echo
echo "--- 4. Proxy service status ---"
for SERVICE in nginx apache2 caddy cloudflared; do
    if systemctl list-unit-files "${SERVICE}.service" --no-legend 2>/dev/null | grep -q "${SERVICE}.service"; then
        printf '%s: ' "$SERVICE"
        systemctl is-active "${SERVICE}.service" 2>/dev/null || true
    fi
done

echo
echo "--- 5. Local user accounts with interactive shells ---"
awk -F: '
    $7 ~ /(bash|sh|zsh)$/ {
        print "USER=" $1, "UID=" $3, "SHELL=" $7
    }
' /etc/passwd

echo
echo "--- 6. AI Defense service identity and permissions ---"
systemctl show ai-defense-manager.service \
    -p User -p Group -p MainPID -p ProtectSystem \
    -p ProtectHome -p NoNewPrivileges

namei -l /opt/ai-defense-manager/app/main.py
namei -l /opt/ai-defense-manager/data/ai-defense.db

echo
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
echo "CREDENTIALS_READ=NO"
echo "DATABASE_ACCESSED=NO"
```

No Nginx, Apache, Caddy or Cloudflared is running on VM 230, and no existing client that calls the API was found. SSH listens on all IPv4 and IPv6 interfaces. The main current threat is not direct access from outside but **unauthorized use by local accounts and processes inside VM 230**.

# Chapter 2: Accounts, Credentials and the DB

## 2.1 Local Account Privileges

Passwords and SSH secret keys are not displayed.

> **Run on: VM 230**

```bash
echo "===== VM230: LOCAL ACCOUNT PRIVILEGE AUDIT ====="

echo
echo "--- 1. Interactive account identity ---"
id aidefense
getent passwd aidefense
passwd -S aidefense

echo
echo "--- 2. Service account identity ---"
id ai-defense
getent passwd ai-defense
passwd -S ai-defense

echo
echo "--- 3. Administrative groups ---"
getent group sudo
getent group adm
getent group docker
getent group lxd

echo
echo "--- 4. Sudo privileges for aidefense ---"
sudo -n -l -U aidefense 2>&1

echo
echo "--- 5. Sudoers configuration references ---"
grep -RInE 'aidefense|ai-defense|ALL[[:space:]]*=' \
    /etc/sudoers /etc/sudoers.d \
    2>/dev/null | sed -E 's/(NOPASSWD:|PASSWD:)/[SUDO_TAG]/g'

echo
echo "--- 6. Relevant running processes ---"
ps -eo user,pid,ppid,comm --sort=user \
    | grep -E '^(USER|root|aidefense|ai-defense)'

echo
echo "--- 7. AI Defense service account isolation ---"
systemctl show ai-defense-manager.service \
    -p User -p Group -p SupplementaryGroups \
    -p NoNewPrivileges -p CapabilityBoundingSet \
    -p AmbientCapabilities -p ProtectSystem \
    -p ProtectHome -p PrivateTmp -p PrivateDevices

echo
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
echo "CREDENTIAL_CONTENTS_DISPLAYED=NO"
echo "SSH_PRIVATE_KEYS_READ=NO"
```

| Account | Privileges |
|---|---|
| `aidefense` (used for login) | `sudo` (can become root), `lxd`, `adm` |
| `ai-defense` (for the service) | `/usr/sbin/nologin`, only its dedicated group |

`aidefense` is effectively an administrator, so adding authentication to the API does not prevent this account from becoming root. The purpose of authentication is to prevent unauthorized calls from ordinary users and local processes with limited privileges. `sudo` and `lxd` may be needed for operation, so they are not changed.

## 2.2 Protection of Credentials

> **Run on: VM 230**

```bash
echo "===== VM230: SERVICE CREDENTIAL PERMISSION AUDIT ====="

echo
echo "--- 1. Service credential configuration ---"
systemctl show ai-defense-manager.service \
    -p LoadCredential \
    -p LoadCredentialEncrypted \
    -p EnvironmentFiles

echo
echo "--- 2. Credential directory metadata ---"
for DIR in \
    /etc/ai-defense-manager \
    /etc/ai-defense-manager/credentials \
    /run/credentials/ai-defense-manager.service
do
    if [ -e "$DIR" ]; then
        stat -c '%A %a %U:%G %n' "$DIR"
        namei -l "$DIR"
    else
        echo "NOT_FOUND=$DIR"
    fi
done

echo
echo "--- 3. Credential file metadata only ---"
for DIR in \
    /etc/ai-defense-manager/credentials \
    /run/credentials/ai-defense-manager.service
do
    if [ -d "$DIR" ]; then
        find "$DIR" -maxdepth 1 -type f \
            -printf '%M %u:%g %s bytes %f\n'
    fi
done

echo
echo "--- 4. Access checks as service account ---"
for PATH_TO_CHECK in \
    /etc/ai-defense-manager/credentials \
    /run/credentials/ai-defense-manager.service
do
    if [ -e "$PATH_TO_CHECK" ]; then
        runuser -u aidefense -- test -r "$PATH_TO_CHECK"
        echo "AIDEFENSE_READ_ACCESS $PATH_TO_CHECK=$?"
    fi
done

echo
echo "--- 5. Access checks as service identity ---"
for PATH_TO_CHECK in \
    /etc/ai-defense-manager/credentials \
    /run/credentials/ai-defense-manager.service
do
    if [ -e "$PATH_TO_CHECK" ]; then
        runuser -u ai-defense -- test -r "$PATH_TO_CHECK"
        echo "AI_DEFENSE_READ_ACCESS $PATH_TO_CHECK=$?"
    fi
done

echo
echo "--- 6. Service executable and application permissions ---"
namei -l /opt/ai-defense-manager/venv/bin/uvicorn
namei -l /opt/ai-defense-manager/app/services/ai_analysis.py

echo
echo "CREDENTIAL_CONTENTS_DISPLAYED=NO"
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Target | State |
|---|---|
| `/etc/ai-defense-manager/credentials` | `root:ai-defense`, `750` |
| Relay token, CA certificate | `640` |
| Readable by `ai-defense` | yes |
| Readable by `aidefense` (ordinary privileges) | no |
| Application Python sources | `root:ai-defense`, `640` |

## 2.3 How Credentials Are Passed, and the DB

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: SYSTEMD CREDENTIAL DELIVERY INSPECTION ====="

echo
echo "--- 1. LoadCredential directives (paths only) ---"
systemctl cat ai-defense-manager.service \
  | grep -E '^[[:space:]]*LoadCredential(Encrypted)?=' \
  | sed -E 's/(:[^:]*\/[^:]*)$/:[PATH_REDACTED]/'

echo
echo "--- 2. Credential environment variable ---"
PID="$(systemctl show ai-defense-manager.service -p MainPID --value)"
python3 - "$PID" <<'PY'
import pathlib
import sys

pid = sys.argv[1]
env = pathlib.Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
for item in env:
    if item.startswith(b"CREDENTIALS_DIRECTORY="):
        print("CREDENTIALS_DIRECTORY is configured")
        print("PATH=" + item.split(b"=", 1)[1].decode(errors="replace"))
        break
else:
    print("CREDENTIALS_DIRECTORY is NOT present")
PY

echo
echo "--- 3. Config credential handling (values redacted) ---"
sed -n '1,45p' app/core/config.py \
  | sed -E \
    -e '/wazuh_relay_token/s/=.*/=[REDACTED]/' \
    -e '/password/s/=.*/=[REDACTED]/' \
    -e '/secret/s/=.*/=[REDACTED]/'

echo
echo "--- 4. Relay credential loading implementation ---"
sed -n '110,155p' app/services/wazuh_relay.py \
  | sed -E \
    -e 's/(token[[:space:]]*=[[:space:]]*).*/\1[REDACTED]/' \
    -e 's/(read_text|read_bytes).*/\1([REDACTED])/'

echo
echo "--- 5. Credential directory and files ---"
find /etc/ai-defense-manager/credentials \
  -maxdepth 1 -type f \
  -printf '%M %u:%g %s bytes %f\n'

echo
echo "--- 6. Current service state ---"
systemctl is-active ai-defense-manager.service
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "CREDENTIAL_VALUES_DISPLAYED=NO"
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
```

- systemd `LoadCredential` is not used, and the running process has no `CREDENTIALS_DIRECTORY`
- The Relay credentials are read directly from `/etc/ai-defense-manager/credentials/` and protected by file permissions
- `aidefense` has no direct access to the Relay credentials directory or to the DB files and directory

API authentication tokens are managed separately from the Relay token.

# Chapter 3: The Network Boundary

## 3.1 Interfaces and Listening Ports

> **Run on: VM 230**

```bash
echo "===== VM230: INTERNAL API NETWORK BOUNDARY AUDIT ====="

echo
echo "--- 1. Network interfaces ---"
ip -br address

echo
echo "--- 2. IPv4 routes ---"
ip -4 route show

echo
echo "--- 3. IPv6 routes ---"
ip -6 route show

echo
echo "--- 4. Neighbor table ---"
ip neigh show

echo
echo "--- 5. Firewall service status ---"
for SERVICE in ufw firewalld nftables; do
    printf '%s: ' "$SERVICE"
    systemctl is-active "${SERVICE}.service" 2>/dev/null || true
done

echo
echo "--- 6. UFW status ---"
if command -v ufw >/dev/null 2>&1; then
    ufw status verbose
else
    echo "UFW_NOT_INSTALLED"
fi

echo
echo "--- 7. nftables ruleset (if available) ---"
if command -v nft >/dev/null 2>&1; then
    nft list ruleset
else
    echo "NFT_NOT_INSTALLED"
fi

echo
echo "--- 8. Current listening sockets ---"
ss -lntup

echo
echo "NETWORK_CONFIGURATION_CHANGED=NO"
echo "FIREWALL_CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
```

VM 230 is `192.168.0.221/24`, and the API listens only on `127.0.0.1:8000`. Other VMs cannot connect to port 8000 directly. We do not suddenly change the API to `0.0.0.0:8000`.

## 3.2 Firewall and IPv6

> **Run on: VM 230**

```bash
echo "===== VM230: KERNEL FIREWALL AND IPV6 SECURITY AUDIT ====="

echo
echo "--- 1. IPv4 iptables rules ---"
if command -v iptables-save >/dev/null 2>&1; then
    iptables-save
else
    echo "IPTABLES_SAVE_NOT_AVAILABLE"
fi

echo
echo "--- 2. IPv6 ip6tables rules ---"
if command -v ip6tables-save >/dev/null 2>&1; then
    ip6tables-save
else
    echo "IP6TABLES_SAVE_NOT_AVAILABLE"
fi

echo
echo "--- 3. Firewall backend ---"
iptables --version 2>/dev/null || true
ip6tables --version 2>/dev/null || true

echo
echo "--- 4. UFW unit details ---"
systemctl show ufw.service \
  -p ActiveState -p SubState -p UnitFileState -p ExecStart \
  --no-pager

echo
echo "--- 5. IPv4/IPv6 forwarding settings ---"
sysctl net.ipv4.ip_forward \
       net.ipv6.conf.all.forwarding \
       net.ipv6.conf.default.forwarding \
       net.ipv6.conf.enp6s18.forwarding

echo
echo "--- 6. IPv6 address scope ---"
ip -6 address show dev enp6s18

echo
echo "FIREWALL_CONFIGURATION_CHANGED=NO"
echo "NETWORK_CONFIGURATION_CHANGED=NO"
```

| Item | Result | Assessment |
|---|---|---|
| API listening | `127.0.0.1:8000` | good |
| IPv4 iptables | no rules | needs measures |
| IPv6 ip6tables | no rules | needs measures |
| nftables | iptables-compatible, no actual rules | — |
| UFW | enabled but shown as `inactive` | investigate |
| IPv4/IPv6 forwarding | 0 (disabled) | good |
| IPv6 address | global | caution |

No inbound filtering inside VM 230 could be confirmed. We cannot say that firewalls on Proxmox or the upstream router are also disabled, but we treat this as a remaining issue (Chapter 6 of the Operations Manual).

## 3.3 SSH

> **Run on: VM 230**

```bash
echo "===== VM230: SSH EXPOSURE AND AUTHENTICATION AUDIT ====="

echo
echo "--- 1. SSH effective authentication settings ---"
sshd -T 2>/dev/null | grep -E \
'^(port|addressfamily|listenaddress|permitrootlogin|passwordauthentication|pubkeyauthentication|kbdinteractiveauthentication|authenticationmethods|allowusers|allowgroups|denyusers|denygroups) '

echo
echo "--- 2. SSH configuration files (security settings only) ---"
grep -RniE \
'^[[:space:]]*(PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|KbdInteractiveAuthentication|AuthenticationMethods|AllowUsers|AllowGroups|DenyUsers|DenyGroups|ListenAddress|Port)[[:space:]]' \
/etc/ssh/sshd_config /etc/ssh/sshd_config.d 2>/dev/null

echo
echo "--- 3. Current SSH connections ---"
ss -tnp state established '( sport = :22 or dport = :22 )'

echo
echo "--- 4. SSH service status ---"
systemctl is-active ssh.service 2>/dev/null || \
systemctl is-active sshd.service 2>/dev/null

echo
echo "--- 5. SSH listening sockets ---"
ss -lntp '( sport = :22 )'

echo
echo "--- 6. Proxmox guest firewall configuration visibility ---"
if command -v systemd-detect-virt >/dev/null 2>&1; then
    systemd-detect-virt
fi

echo
echo "SSH_CONFIGURATION_CHANGED=NO"
echo "FIREWALL_CONFIGURATION_CHANGED=NO"
```

The settings were `PermitRootLogin no`, `PasswordAuthentication no` (`00-local-hardening.conf`), `PubkeyAuthentication yes` and `KbdInteractiveAuthentication no`.

> **Run on: VM 230**

```bash
echo "===== VM230: SSH SYSTEMD SOCKET ACTIVATION AUDIT ====="

echo
echo "--- 1. SSH-related units ---"
systemctl list-units --all --no-legend | grep -E 'ssh|sshd' || true

echo
echo "--- 2. SSH socket status ---"
systemctl status ssh.socket sshd.socket --no-pager 2>&1

echo
echo "--- 3. SSH socket unit configuration ---"
systemctl cat ssh.socket sshd.socket 2>&1

echo
echo "--- 4. Socket properties ---"
for UNIT in ssh.socket sshd.socket; do
    echo "[$UNIT]"
    systemctl show "$UNIT" \
      -p LoadState -p ActiveState -p SubState \
      -p Listen -p BindIPv6Only -p Triggers \
      --no-pager 2>/dev/null
done

echo
echo "--- 5. SSH daemon binary and configuration validation ---"
command -v sshd
/usr/sbin/sshd -t 2>&1
echo "SSHD_CONFIG_TEST_EXIT=$?"

echo
echo "--- 6. Effective SSH configuration ---"
/usr/sbin/sshd -T 2>&1 | grep -E \
'^(port|addressfamily|listenaddress|permitrootlogin|passwordauthentication|pubkeyauthentication|kbdinteractiveauthentication|authenticationmethods) '
echo "SSHD_EFFECTIVE_CONFIG_PIPE_EXIT=${PIPESTATUS[0]}"

echo
echo "SSH_CONFIGURATION_CHANGED=NO"
echo "SOCKET_CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
```

On VM 230, `ssh.service` does not run all the time; `ssh.socket` holds port 22 and starts `ssh.service` when a connection arrives (IPv4 `0.0.0.0:22`, IPv6 `[::]:22`). Even when `ssh.service` is `inactive`, SSH is not stopped.

> **Run on: VM 230**

```bash
echo "===== VM230: SSH SERVICE RUNTIME CONFIGURATION AUDIT ====="

echo
echo "--- 1. SSH service unit ---"
systemctl cat ssh.service

echo
echo "--- 2. SSH service effective properties ---"
systemctl show ssh.service \
  -p LoadState \
  -p ActiveState \
  -p SubState \
  -p ExecStart \
  -p ExecStartPre \
  -p RuntimeDirectory \
  -p RuntimeDirectoryMode \
  -p User \
  -p Group \
  --no-pager

echo
echo "--- 3. Runtime privilege separation directory ---"
if [ -e /run/sshd ]; then
    stat -c '%A %U:%G %n' /run/sshd
else
    echo "/run/sshd DOES NOT EXIST"
fi

echo
echo "--- 4. SSH configuration include order ---"
grep -nE '^[[:space:]]*(Include|Match|Port|AddressFamily|ListenAddress|PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|KbdInteractiveAuthentication|AuthenticationMethods)' \
  /etc/ssh/sshd_config \
  /etc/ssh/sshd_config.d/*.conf 2>/dev/null

echo
echo "--- 5. SSH socket activation dependencies ---"
systemctl list-dependencies ssh.socket --no-pager

echo
echo "SSH_CONFIGURATION_CHANGED=NO"
echo "RUNTIME_DIRECTORY_CREATED=NO"
echo "SERVICE_RESTARTED=NO"
```

`/run/sshd` is created by systemd when `ssh.service` starts (`RuntimeDirectory`). The configuration files are read in the order `00-local-hardening.conf`, `50-cloud-init.conf`, and OpenSSH uses the first value set, so `PasswordAuthentication no` takes precedence. The SSH settings are not changed.

# Chapter 4: Designing Authentication

## 4.1 Where to Integrate

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API AUTHENTICATION IMPLEMENTATION PRECHECK ====="

echo
echo "--- 1. Main application structure ---"
sed -n '1,260p' app/main.py

echo
echo "--- 2. API route declarations ---"
grep -RniE \
'^[[:space:]]*(@router\.|router[[:space:]]*=|include_router|def |async def )' \
app/api app/main.py 2>/dev/null

echo
echo "--- 3. Authentication and security references ---"
grep -RniE \
'HTTPBearer|HTTPAuthorizationCredentials|OAuth2|APIKey|Depends|Security\(|middleware|exception_handler|status_code' \
app --include='*.py' 2>/dev/null

echo
echo "--- 4. API schema files ---"
find app/schemas -maxdepth 2 -type f -name '*.py' -printf '%p\n' | sort

echo
echo "--- 5. Test directory structure ---"
find . -maxdepth 3 -type f \
  \( -path './tests/*' -o -name 'conftest.py' \) \
  -printf '%p\n' | sort | head -200

echo
echo "--- 6. Existing API test references ---"
grep -RniE \
'/api/v1/analysis|/api/v1/wazuh|/health|TestClient|AsyncClient|Authorization|401|403' \
tests --include='*.py' 2>/dev/null | head -200

echo
echo "--- 7. Installed test dependencies ---"
./venv/bin/python -m pip show pytest pytest-asyncio httpx fastapi pydantic-settings 2>/dev/null \
  | grep -E '^(Name|Version):'

echo
echo "--- 8. Service status ---"
systemctl is-active ai-defense-manager.service
systemctl show ai-defense-manager.service -p MainPID -p ActiveState -p SubState --no-pager

echo
echo "SOURCE_FILES_CHANGED=NO"
echo "TESTS_EXECUTED=NO"
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "WAZUH_RELAY_ACCESSED=NO"
```

- There are two API routers (`/api/v1`: AI analysis; `/api/v1/wazuh`: Wazuh event retrieval and analysis)
- There is no authentication middleware, `Depends`, `HTTPBearer` or the like yet
- `/health` is outside the routers and can be separated from authentication
- The body size limit middleware can stay
- There is no `tests/` directory

## 4.2 The Design Decided

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API AUTHENTICATION DESIGN AUDIT ====="

echo
echo "--- 1. Analysis API ---"
sed -n '1,220p' app/api/analysis.py

echo
echo "--- 2. Wazuh API ---"
sed -n '1,240p' app/api/wazuh.py

echo
echo "--- 3. Application settings (secret values redacted) ---"
sed -n '1,180p' app/core/config.py \
  | sed -E '/token|secret|password|credential|api_key/I s/(=).*/\1[REDACTED]/'

echo
echo "--- 4. Project dependency files ---"
for FILE in pyproject.toml requirements.txt requirements-dev.txt setup.cfg tox.ini pytest.ini; do
    if [ -f "$FILE" ]; then
        echo "[$FILE]"
        grep -niE 'fastapi|starlette|pydantic|httpx|pytest|test|uvicorn|cryptography' "$FILE" \
          | sed -E 's/(token|password|secret|key)[^=]*=.*/\1=[REDACTED]/I'
    fi
done

echo
echo "--- 5. Project root files ---"
find . -maxdepth 2 -type f \
  ! -path './venv/*' \
  ! -path './.git/*' \
  -printf '%p\n' | sort | head -160

echo
echo "--- 6. FastAPI documentation routes ---"
./venv/bin/python - <<'PY'
from app.main import app

for route in app.routes:
    methods = sorted(getattr(route, "methods", []) or [])
    print(
        "PATH=", getattr(route, "path", "[unknown]"),
        "METHODS=", ",".join(methods),
        "NAME=", getattr(route, "name", "[unknown]"),
    )

print("DOCS_URL=", app.docs_url)
print("REDOC_URL=", app.redoc_url)
print("OPENAPI_URL=", app.openapi_url)
PY

echo
echo "--- 7. Test tooling availability ---"
for PACKAGE in pytest pytest_asyncio; do
    ./venv/bin/python -c \
      "import importlib.util; print('$PACKAGE:', 'AVAILABLE' if importlib.util.find_spec('$PACKAGE') else 'NOT_INSTALLED')"
done

echo
echo "--- 8. Service state ---"
systemctl is-active ai-defense-manager.service
ss -lntp '( sport = :8000 )'

echo
echo "SOURCE_FILES_CHANGED=NO"
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "WAZUH_RELAY_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Target | Now | Policy |
|---|---|---|
| AI analysis API | no authentication | requires authentication (`analyze`) |
| Wazuh event retrieval | no authentication | requires authentication (`read`) |
| Wazuh analysis | no authentication | requires authentication (`analyze`) |
| `/health` | no authentication | unchanged |
| `/docs`, `/redoc`, `/openapi.json` | no authentication | disabled in production |
| Per-client revocation | none | build it |
| Separation of privileges | none | build it (`read`, `analyze`) |

The token scheme is as follows.

- Issue an unguessable random Bearer token per client
- Store only the SHA-256 hash in SQLite, not the token itself
- Use `hmac.compare_digest` for comparison
- Give tokens expiry and revocation
- Keep them completely separate from the Relay token
- Do not give the LLM credentials or execution privileges
- Keep the API on `127.0.0.1:8000`; when used from other VMs, provide a separate entry point with TLS

# Closing Notes

In Part 56 we carried out the checks before building API authentication and decided the design.

| Item | Result |
|---|---|
| API | no authentication or authorization; `127.0.0.1:8000` only |
| Accounts | `aidefense` is an administrator, `ai-defense` is service-only (privileges are separated) |
| Credentials | protected by file permissions (`root:ai-defense`, `640`) |
| Network | no firewall rules inside VM 230 (an issue); SSH is socket-activated with password authentication disabled |
| Authentication design | per-client Bearer tokens (`read`, `analyze`), stored as hashes, with revocation and expiry; documentation APIs disabled |

In the next part, Part 57, we build token authentication and test it in an independent environment.

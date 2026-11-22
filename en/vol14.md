---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 14: Building the Alert Relay API (Relay)"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 14 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". Using the read-only Indexer user created in Part 13, we build inside security-core a "relay API (Relay)" that passes alerts to the AI Defense Manager (VM 230).

The Indexer is not exposed to other hosts; only the Relay accepts external connections, under the following conditions.

- It listens only on `192.168.0.220:8765` (HTTPS)
- Its server certificate is issued by an internal CA dedicated to the Relay
- Calls require a Bearer token
- It returns only the 10 fields decided in Part 13, 6.1. Search conditions and the maximum count are decided on the Relay side
- Secrets (the Indexer password, the token, private keys) are passed with systemd's `LoadCredential`

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Unless otherwise noted, everything is run on **security-core VM 220 (root)**.
- The contents of passwords, tokens and private keys appear neither on screen nor in this manual.

# Chapter 1: Certificates and the Token

## 1.1 Where They Are Kept

```bash
openssl version
```

```bash
ls -ld /etc/ai-defense-relay /etc/ai-defense-relay/* 2>/dev/null
```

```bash
install -d -m 700 -o root -g root /etc/ai-defense-relay
```

## 1.2 The Internal CA

Create a certificate authority (CA) dedicated to the Relay. It is managed separately from the Indexer's CA.

```bash
openssl req -x509 -newkey rsa:3072 -sha256 -days 3650 -nodes -keyout /etc/ai-defense-relay/ca.key -out /etc/ai-defense-relay/ca.crt -subj "/CN=AI-Defense-Relay-Internal-CA" -addext "basicConstraints=critical,CA:TRUE" -addext "keyUsage=critical,keyCertSign,cRLSign" && chmod 600 /etc/ai-defense-relay/ca.key && chmod 644 /etc/ai-defense-relay/ca.crt
```

## 1.3 The Server Certificate

Because clients connect with `192.168.0.220`, put the IP address in the SAN.

```bash
openssl req -new -newkey rsa:2048 -nodes -keyout /etc/ai-defense-relay/server.key -out /etc/ai-defense-relay/server.csr -subj "/CN=192.168.0.220" -addext "subjectAltName=IP:192.168.0.220" && chmod 600 /etc/ai-defense-relay/server.key /etc/ai-defense-relay/server.csr
```

```bash
printf '%s\n' 'subjectAltName=IP:192.168.0.220' 'extendedKeyUsage=serverAuth' 'keyUsage=critical,digitalSignature,keyEncipherment' 'basicConstraints=critical,CA:FALSE' > /etc/ai-defense-relay/server.ext && openssl x509 -req -in /etc/ai-defense-relay/server.csr -CA /etc/ai-defense-relay/ca.crt -CAkey /etc/ai-defense-relay/ca.key -CAcreateserial -out /etc/ai-defense-relay/server.crt -days 825 -sha256 -extfile /etc/ai-defense-relay/server.ext && chmod 644 /etc/ai-defense-relay/server.crt /etc/ai-defense-relay/server.ext
```

Check the CA signature, the IP address, the usage, and that it matches the private key.

```bash
openssl verify -CAfile /etc/ai-defense-relay/ca.crt -verify_ip 192.168.0.220 -purpose sslserver /etc/ai-defense-relay/server.crt && test "$(openssl x509 -in /etc/ai-defense-relay/server.crt -pubkey -noout | openssl sha256)" = "$(openssl pkey -in /etc/ai-defense-relay/server.key -pubout | openssl sha256)" && echo "CERTIFICATE_AND_PRIVATE_KEY_VALID"
```

## 1.4 The Bearer Token

Create the token that VM 230 uses when calling the Relay. It is not shown on screen.

```bash
python3 -c 'import secrets,pathlib,os; p=pathlib.Path("/etc/ai-defense-relay/api.token"); p.write_text(secrets.token_urlsafe(48)+"\n"); os.chmod(p,0o600); print("RELAY_TOKEN_CREATED; mode=600")'
```

# Chapter 2: The Run-As User and Runtime Environment

## 2.1 A Dedicated User

```bash
systemd --version
```

At build time this was systemd 255, so `LoadCredential` could be used.

```bash
getent passwd ai-defense-relay || echo "SERVICE_USER_NOT_FOUND"
```

```bash
useradd --system --user-group --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin ai-defense-relay
```

```bash
id ai-defense-relay
```

## 2.2 A Python Virtual Environment

The system Python on security-core does not have FastAPI or similar installed. We decided to build the Relay with the standard library only, and prepare a dedicated virtual environment.

```bash
python3 -c 'import sys; print(sys.version); import fastapi,uvicorn,httpx; print("FASTAPI",fastapi.__version__); print("UVICORN",uvicorn.__version__); print("HTTPX",httpx.__version__)'
```

```bash
python3 -m venv --help >/dev/null && echo "VENV_AVAILABLE"
```

Creating the virtual environment requires `python3.12-venv`.

```bash
dpkg-query -W -f='${Status} ${Version}\n' python3.12-venv 2>/dev/null || echo "PACKAGE_NOT_INSTALLED"
```

```bash
apt-cache policy python3.12-venv
```

```bash
apt-get install -y python3.12-venv
```

Create the directory and create the virtual environment as the dedicated user.

```bash
install -d -o ai-defense-relay -g ai-defense-relay -m 750 /opt/ai-defense-relay && runuser -u ai-defense-relay -- python3 -m venv /opt/ai-defense-relay/venv
```

In the original build, this command was run before `python3.12-venv` was installed, so only the directory was created; after installing it, only the creation of the virtual environment was redone.

```bash
runuser -u ai-defense-relay -- python3 -m venv /opt/ai-defense-relay/venv
```

```bash
runuser -u ai-defense-relay -- /opt/ai-defense-relay/venv/bin/python -m pip --version
```

```bash
runuser -u ai-defense-relay -- /opt/ai-defense-relay/venv/bin/python -c 'import http.server,ssl,urllib.request,json,ipaddress; print("HTTPS_SERVER_AND_REQUIRED_STDLIB_AVAILABLE")'
```

# Chapter 3: Secrets Passed by systemd

## 3.1 Where They Are Kept

The Relay runs as a dedicated user. Secrets stay in files readable only by root and are passed only at startup through systemd's `LoadCredential`.

```bash
stat -c '%A %a %U:%G %n' /etc/ai-defense-relay /etc/ai-defense-relay/ca.crt /etc/ai-defense-relay/ca.key /etc/ai-defense-relay/server.crt /etc/ai-defense-relay/server.key /etc/ai-defense-relay/api.token /root/ai-defense-reader.password
```

```bash
install -d -o root -g root -m 700 /etc/credstore
```

## 3.2 Placing the Files

```bash
install -o root -g root -m 600 /root/ai-defense-reader.password /etc/credstore/ai-defense-indexer-password && install -o root -g root -m 600 /etc/ai-defense-relay/api.token /etc/credstore/ai-defense-relay-token && install -o root -g root -m 600 /etc/ai-defense-relay/server.key /etc/credstore/ai-defense-relay-server-key && echo "SYSTEMD_CREDENTIAL_FILES_PREPARED"
```

```bash
stat -c '%A %a %U:%G %s bytes %n' /etc/credstore/ai-defense-indexer-password /etc/credstore/ai-defense-relay-token /etc/credstore/ai-defense-relay-server-key
```

```bash
install -o root -g root -m 600 /etc/ai-defense-relay/server.crt /etc/credstore/ai-defense-relay-server-cert && install -o root -g root -m 600 /etc/wazuh-indexer/certs/root-ca.pem /etc/credstore/ai-defense-indexer-ca && echo "TLS_CERTIFICATE_CREDENTIALS_PREPARED"
```

```bash
stat -c '%A %a %U:%G %s bytes %n' /etc/credstore/ai-defense-*
```

To verify the Relay's server certificate, use the Relay's own CA, not the Indexer's CA (in the original build, the first attempt verified with the Indexer's CA and failed). Place the Relay's CA as well.

```bash
install -o root -g root -m 600 /etc/ai-defense-relay/ca.crt /etc/credstore/ai-defense-relay-ca && echo "RELAY_CA_CREDENTIAL_PREPARED"
```

```bash
openssl verify -CAfile /etc/credstore/ai-defense-relay-ca -verify_ip 192.168.0.220 -purpose sslserver /etc/credstore/ai-defense-relay-server-cert && test "$(openssl x509 -in /etc/credstore/ai-defense-relay-server-cert -pubkey -noout | openssl sha256)" = "$(openssl pkey -in /etc/credstore/ai-defense-relay-server-key -pubout | openssl sha256)" && echo "RELAY_TLS_CREDENTIALS_VALID"
```

| File (`/etc/credstore/`) | Contents |
|---|---|
| `ai-defense-indexer-password` | Password of the Indexer user `ai-defense-reader` |
| `ai-defense-indexer-ca` | The Indexer's CA certificate |
| `ai-defense-relay-token` | Bearer token |
| `ai-defense-relay-server-cert` | The Relay's server certificate |
| `ai-defense-relay-server-key` | The Relay's server private key |
| `ai-defense-relay-ca` | The Relay's CA certificate |

## 3.3 Checking the Listening State

```bash
ss -lntp | grep -E '(:8765[[:space:]]|:8765$)' || echo "PORT_8765_AVAILABLE"
```

```bash
ip -brief address show | grep '192\.168\.0\.220/'
```

# Chapter 4: The Relay Program

## 4.1 relay.py

An HTTPS server written with the Python standard library only.

- Connections are accepted only from VM 230 (`192.168.0.33`). Anything else gets `403`
- If `Authorization: Bearer <token>` does not match, it returns `401` (the comparison uses `hmac.compare_digest`)
- Only `GET /health` and `GET /v1/alerts` are available. `POST`, `PUT`, `DELETE` and `HEAD` return `405`
- The only parameters of `/v1/alerts` are `limit` (1–100, default 50) and `since_minutes` (1–1440, default 15)
- The query to the Indexer is built inside the Relay, and only the 10 defined fields are returned (strings up to 512 characters)
- If the Indexer's response exceeds 2 MB, nothing is returned

```bash
cat > /opt/ai-defense-relay/relay.py <<'PY'
#!/usr/bin/env python3
import os
import json
import ssl
import hmac
import base64
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BIND_HOST = "192.168.0.220"
BIND_PORT = 8765
ALLOWED_CLIENT = "192.168.0.33"
INDEXER_URL = "https://127.0.0.1:9200/wazuh-alerts-4.x-*/_search"

ALLOWED_FIELDS = (
    "timestamp",
    "agent.id",
    "agent.ip",
    "agent.name",
    "manager.name",
    "rule.level",
    "rule.description",
    "rule.id",
    "location",
    "decoder.name",
)

def credential(name):
    directory = os.environ.get("CREDENTIALS_DIRECTORY")
    if not directory:
        raise RuntimeError("Systemd credentials unavailable")
    return (Path(directory) / name).read_bytes().strip()

API_TOKEN = credential("relay-token")
INDEXER_PASSWORD = credential("indexer-password").decode("utf-8")

INDEXER_AUTH = "Basic " + base64.b64encode(
    ("ai-defense-reader:" + INDEXER_PASSWORD).encode()
).decode()

INDEXER_TLS = ssl.create_default_context(
    cafile=os.environ["CREDENTIALS_DIRECTORY"] + "/indexer-ca"
)

SERVER_TLS = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
SERVER_TLS.minimum_version = ssl.TLSVersion.TLSv1_2
SERVER_TLS.load_cert_chain(
    os.environ["CREDENTIALS_DIRECTORY"] + "/server-cert",
    os.environ["CREDENTIALS_DIRECTORY"] + "/server-key",
)

def sanitize_alert(source):
    result = {}
    for field in ALLOWED_FIELDS:
        value = source
        for part in field.split("."):
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(part)

        if value is None:
            continue

        if field == "rule.level":
            if isinstance(value, int) and not isinstance(value, bool):
                result[field] = value
        elif isinstance(value, str):
            result[field] = value[:512]

    return result

class RelayHandler(BaseHTTPRequestHandler):
    server_version = "AI-Defense-Relay"
    sys_version = ""

    def log_message(self, fmt, *args):
        print("relay client=%s %s" % (self.client_address[0], fmt % args),
              flush=True)

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.client_address[0] != ALLOWED_CLIENT:
            self.send_json(403, {"error": "forbidden"})
            return

        auth = self.headers.get("Authorization", "")
        expected = "Bearer " + API_TOKEN.decode("utf-8")
        if not hmac.compare_digest(auth, expected):
            self.send_json(401, {"error": "unauthorized"})
            return

        parsed = urlsplit(self.path)

        if parsed.path == "/health":
            self.send_json(200, {"status": "ok"})
            return

        if parsed.path != "/v1/alerts":
            self.send_json(404, {"error": "not_found"})
            return

        params = parse_qs(parsed.query, strict_parsing=True)
        if set(params) - {"limit", "since_minutes"}:
            self.send_json(400, {"error": "unsupported_parameter"})
            return
        if any(len(v) != 1 for v in params.values()):
            self.send_json(400, {"error": "invalid_parameter"})
            return

        try:
            limit = int(params.get("limit", ["50"])[0])
            since = int(params.get("since_minutes", ["15"])[0])
        except ValueError:
            self.send_json(400, {"error": "invalid_parameter"})
            return

        if not 1 <= limit <= 100 or not 1 <= since <= 1440:
            self.send_json(400, {"error": "parameter_out_of_range"})
            return

        query = {
            "size": limit,
            "track_total_hits": False,
            "sort": [{"timestamp": {"order": "desc"}}],
            "_source": list(ALLOWED_FIELDS),
            "query": {
                "range": {
                    "timestamp": {
                        "gte": "now-%dm" % since
                    }
                }
            }
        }

        request = urllib.request.Request(
            INDEXER_URL,
            data=json.dumps(query).encode("utf-8"),
            headers={
                "Authorization": INDEXER_AUTH,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request, context=INDEXER_TLS, timeout=10
            ) as response:
                raw = response.read(2 * 1024 * 1024 + 1)

            if len(raw) > 2 * 1024 * 1024:
                self.send_json(502, {"error": "upstream_response_too_large"})
                return

            data = json.loads(raw)
            hits = data.get("hits", {}).get("hits", [])
            alerts = [
                sanitize_alert(hit.get("_source", {}))
                for hit in hits
                if isinstance(hit.get("_source"), dict)
            ]
            self.send_json(200, {
                "count": len(alerts),
                "alerts": alerts
            })

        except Exception:
            self.send_json(502, {"error": "indexer_unavailable"})

    def do_POST(self):
        self.send_json(405, {"error": "method_not_allowed"})

    def do_PUT(self):
        self.send_json(405, {"error": "method_not_allowed"})

    def do_DELETE(self):
        self.send_json(405, {"error": "method_not_allowed"})

    def do_HEAD(self):
        self.send_json(405, {"error": "method_not_allowed"})

class RelayServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

def main():
    server = RelayServer((BIND_HOST, BIND_PORT), RelayHandler)
    server.socket = SERVER_TLS.wrap_socket(
        server.socket, server_side=True
    )
    print("AI Defense Relay listening on %s:%s" %
          (BIND_HOST, BIND_PORT), flush=True)
    server.serve_forever()

if __name__ == "__main__":
    main()
PY
chown root:ai-defense-relay /opt/ai-defense-relay/relay.py
chmod 640 /opt/ai-defense-relay/relay.py
```

## 4.2 Checking the Syntax

```bash
python3 -m py_compile /opt/ai-defense-relay/relay.py
```

```bash
stat -c '%A %a %U:%G %s bytes' /opt/ai-defense-relay/relay.py && tail -n 25 /opt/ai-defense-relay/relay.py
```

```bash
sed -n '1,150p' /opt/ai-defense-relay/relay.py
```

```bash
sed -n '151,260p' /opt/ai-defense-relay/relay.py
```

## 4.3 Stricter Checking of the Query String

`parse_qs(..., strict_parsing=True)` raises `ValueError` on a malformed query string. As it stands, processing would stop, so change it to return `400`.

```bash
python3 - <<'PY'
from pathlib import Path

p = Path("/opt/ai-defense-relay/relay.py")
s = p.read_text()
old = '''        params = parse_qs(parsed.query, strict_parsing=True)
        if set(params) - {"limit", "since_minutes"}:
'''
new = '''        try:
            params = parse_qs(parsed.query, strict_parsing=True)
        except ValueError:
            self.send_json(400, {"error": "invalid_query"})
            return

        if set(params) - {"limit", "since_minutes"}:
'''
if old not in s:
    raise SystemExit("EXPECTED_CODE_NOT_FOUND; FILE_UNCHANGED")
p.write_text(s.replace(old, new, 1))
print("QUERY_VALIDATION_HARDENED")
PY
```

```bash
python3 -m py_compile /opt/ai-defense-relay/relay.py && echo "RELAY_SYNTAX_OK"
```

In addition, limit the query string to 128 characters and the number of parameters to two.

```bash
python3 - <<'PY'
from pathlib import Path

p = Path("/opt/ai-defense-relay/relay.py")
s = p.read_text()
old = '''        try:
            params = parse_qs(parsed.query, strict_parsing=True)
        except ValueError:
'''
new = '''        if len(parsed.query) > 128:
            self.send_json(400, {"error": "query_too_long"})
            return

        try:
            params = parse_qs(
                parsed.query, strict_parsing=True, max_num_fields=2
            )
        except ValueError:
'''
if old not in s:
    raise SystemExit("EXPECTED_CODE_NOT_FOUND; FILE_UNCHANGED")
p.write_text(s.replace(old, new, 1))
print("QUERY_LENGTH_AND_FIELD_LIMITS_ADDED")
PY
```

```bash
python3 -m py_compile /opt/ai-defense-relay/relay.py && echo "RELAY_SYNTAX_OK"
```

# Chapter 5: The systemd Service

## 5.1 The Unit File

```bash
test ! -e /etc/systemd/system/ai-defense-relay.service && echo "SERVICE_UNIT_NAME_AVAILABLE" || echo "SERVICE_UNIT_ALREADY_EXISTS"
```

Secrets are passed with `LoadCredential`, and the process's privileges are tightly restricted.

- `LoadCredential=<name>:<path>`: readable only at runtime as `$CREDENTIALS_DIRECTORY/<name>`
- `ProtectSystem=strict`, `ProtectHome=yes`: make the file system read-only and hide home directories
- `CapabilityBoundingSet=` (empty), `NoNewPrivileges=yes`: no privileges
- `RestrictAddressFamilies=AF_INET`: IPv4 communication only
- `MemoryMax=256M`, `TasksMax=32`: limits on the resources used

```bash
cat > /etc/systemd/system/ai-defense-relay.service <<'UNIT'
[Unit]
Description=AI Defense Wazuh Alert Read-only Relay
After=network.target wazuh-indexer.service
Wants=network.target

[Service]
Type=simple
User=ai-defense-relay
Group=ai-defense-relay
WorkingDirectory=/opt/ai-defense-relay

LoadCredential=relay-token:/etc/credstore/ai-defense-relay-token
LoadCredential=indexer-password:/etc/credstore/ai-defense-indexer-password
LoadCredential=indexer-ca:/etc/credstore/ai-defense-indexer-ca
LoadCredential=server-cert:/etc/credstore/ai-defense-relay-server-cert
LoadCredential=server-key:/etc/credstore/ai-defense-relay-server-key

ExecStart=/opt/ai-defense-relay/venv/bin/python /opt/ai-defense-relay/relay.py
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

MemoryMax=256M
TasksMax=32
LimitNOFILE=1024

[Install]
WantedBy=multi-user.target
UNIT
```

```bash
tail -n 25 /etc/systemd/system/ai-defense-relay.service
```

```bash
systemd-analyze verify /etc/systemd/system/ai-defense-relay.service
```

## 5.2 Checks Before Starting

Check the file permissions and that the dedicated user can read Python and relay.py.

```bash
stat -c '%a %U:%G %n' \
  /etc/credstore/ai-defense-relay-token \
  /etc/credstore/ai-defense-indexer-password \
  /etc/credstore/ai-defense-indexer-ca \
  /etc/credstore/ai-defense-relay-server-cert \
  /etc/credstore/ai-defense-relay-server-key
```

```bash
stat -c '%a %U:%G %n' \
  /opt/ai-defense-relay \
  /opt/ai-defense-relay/relay.py \
  /opt/ai-defense-relay/venv \
  /opt/ai-defense-relay/venv/bin/python
```

```bash
ls -l /opt/ai-defense-relay/venv/bin/python && readlink -f /opt/ai-defense-relay/venv/bin/python
```

```bash
runuser -u ai-defense-relay -- /opt/ai-defense-relay/venv/bin/python -c 'import sys; print(sys.version); print("PYTHON_EXECUTION_OK")'
```

```bash
runuser -u ai-defense-relay -- /opt/ai-defense-relay/venv/bin/python -c 'import ast, pathlib, ssl, urllib.request, http.server; p=pathlib.Path("/opt/ai-defense-relay/relay.py"); ast.parse(p.read_text()); print("RELAY_READ_OK"); print("STANDARD_LIBRARIES_OK")'
```

Confirm that the unit's contents match the credential names read by relay.py.

```bash
systemd-analyze cat-config systemd/system/ai-defense-relay.service
```

```bash
grep -nE 'CREDENTIALS_DIRECTORY|credential\(|indexer-ca|server-cert|server-key|relay-token|indexer-password' /opt/ai-defense-relay/relay.py
```

Also confirm that query strings and authentication information do not remain in the access log.

> **Note:** At the time this check was done in the original build, relay.py had already changed from the content in 4.1–4.3 (an override of `log_request` that limits the access log to "source IP address and status", and the addition of `threading.BoundedSemaphore(8)` that limits concurrent requests to eight). The steps for these changes were not recorded in the build history, so they are not included in this book (author's notes, item 14-A).

```bash
grep -nA12 -B3 'def log_message' /opt/ai-defense-relay/relay.py
```

```bash
systemctl daemon-reload && systemctl show ai-defense-relay.service -p LoadCredential -p User -p Group -p FragmentPath
```

`LoadCredential` is shown as `[unprintable]` to protect its contents.

# Chapter 6: Starting and Checking Connections

## 6.1 Starting

When started, it begins listening on `192.168.0.220:8765`.

```bash
systemctl start ai-defense-relay.service && systemctl status ai-defense-relay.service --no-pager -l
```

The result at build time was `Active: active (running)`. Note that at this point it is still `disabled` (does not start automatically).

```bash
ss -lntp '( sport = :8765 )' && echo && journalctl -u ai-defense-relay.service -n 20 --no-pager
```

## 6.2 Checking TLS

```bash
timeout 5 openssl s_client -connect 192.168.0.220:8765 -CAfile /etc/ai-defense-relay/ca.crt -verify_ip 192.168.0.220 -verify_return_error -brief </dev/null
```

The results at build time were as follows.

- `Protocol version: TLSv1.3`
- `Peer certificate: CN = 192.168.0.220`
- `Verification: OK`

`Can't use SSL_get_servername` is a notice that the SNI name cannot be used because the connection was made with an IP address; it is not a verification failure.

## 6.3 Connecting from VM 230

> **Run on: ai-defense-manager VM 230 (root)**

```bash
nc -vz -w 3 192.168.0.220 8765
```

If `succeeded!` is shown, VM 230 can reach the Relay's listening port.

# Closing Notes

In Part 14 we built the following relay API on security-core.

| Item | Details |
|---|---|
| Listening on | `https://192.168.0.220:8765` (TLS 1.2 or later) |
| Allowed source | Only `192.168.0.33` (VM 230) |
| Authentication | Bearer token |
| API | `GET /health`, `GET /v1/alerts?limit=&since_minutes=` |
| Runs as | `ai-defense-relay.service` (dedicated user, `LoadCredential`) |

In the next part, we safely pass the token and CA certificate to VM 230 so that it can receive alerts from the Relay.

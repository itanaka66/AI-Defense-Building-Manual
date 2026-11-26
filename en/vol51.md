---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 51: Verifying TLS and Authentication from VM 230 to the Relay"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 51 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 50 we gave VM 230 the static address `192.168.0.221` and fixed the allowed client of the Relay on VM 220. Here, before actually fetching alerts, we check the conditions for connecting from VM 230 to the Relay on VM 220.

1. Check VM 230's connection settings and the HTTPS implementation of the Relay on VM 220
2. Check that the Relay's server certificate matches `192.168.0.220` and is signed by a CA that VM 230 trusts
3. Using `/health`, which does not query the Indexer, test TLS, the source IP restriction and Bearer authentication once

Secret keys, Bearer tokens and Indexer credentials are not displayed.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **VM 220**: security-core (root)

# Chapter 1: Connection Settings and the HTTPS Implementation

## 1.1 VM 230's Connection Target

> **Run on: VM 230**

```bash
echo "===== VM230: WAZUH RELAY CONNECTION CONFIGURATION AUDIT ====="

cd /opt/ai-defense-manager || true

echo
echo "--- Relay configuration references (secrets excluded) ---"
grep -RInE \
  '192\.168\.0\.220|8765|WAZUH.*(URL|HOST|PORT)|RELAY.*(URL|HOST|PORT)' \
  app \
  --include='*.py' \
  --exclude='*.pyc' \
  2>/dev/null

echo
echo "--- Relay service implementation: connection and auth structure ---"
grep -n -C 4 -E \
  'urlopen|Request\(|Authorization|Bearer|timeout|https?://' \
  app/services/wazuh_relay.py

echo
echo "--- VM230 process and service state ---"
systemctl is-active ai-defense-manager.service
systemctl show ai-defense-manager.service \
  -p MainPID -p ActiveState -p SubState -p User -p WorkingDirectory

echo
echo "--- Network route to VM220 ---"
ip route get 192.168.0.220

echo
echo "CONFIGURATION_CHANGED=NO"
echo "HTTP_REQUEST=NO"
echo "WAZUH_INDEXER_REQUEST=NO"
echo "OLLAMA_REQUEST=NO"
echo "DATABASE_ACCESSED=NO"
echo "SECRETS_DISPLAYED=NO"
```

| Item | Result |
|---|---|
| Relay URL | `https://192.168.0.220:8765/` |
| Path | VM 230 `.221` → VM 220 `.220` |
| Authentication | Bearer token |
| TLS certificate verification | enabled (`verify=str(ca_file)`) |

The old address `.33` did not remain on the VM 230 side.

## 1.2 The Relay's HTTPS Implementation

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY TLS IMPLEMENTATION AUDIT ====="

cd /opt/ai-defense-relay || true

echo
echo "--- TLS and server implementation references ---"
grep -n -C 3 -E \
  'ssl|HTTPServer|ThreadingHTTPServer|wrap_socket|certfile|keyfile|load_cert|serve_forever|API_TOKEN' \
  relay.py | sed -E \
  's/(API_TOKEN[[:space:]]*=).*/\1 <REDACTED>/'

echo
echo "--- Relay server startup section ---"
tail -70 relay.py | sed -E \
  's/(API_TOKEN[[:space:]]*=).*/\1 <REDACTED>/'

echo
echo "--- Service unit TLS-related metadata ---"
systemctl show ai-defense-relay.service \
  -p FragmentPath -p ExecStart -p EnvironmentFiles

echo
echo "--- Listener protocol metadata ---"
ss -lntp '( sport = :8765 )'

echo
echo "SOURCE_MODIFIED=NO"
echo "HTTP_REQUEST=NO"
echo "TLS_HANDSHAKE=NO"
echo "WAZUH_INDEXER_REQUEST=NO"
echo "SECRETS_DISPLAYED=NO"
```

The Relay is an HTTPS server that requires TLS 1.2 or later, and it loaded its server certificate and secret key from systemd credentials.

# Chapter 2: Checking the Certificate and CA

## 2.1 The Server Certificate

We look only at public information.

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY SERVER CERTIFICATE AUDIT ====="

PID=$(systemctl show ai-defense-relay.service -p MainPID --value)
CRED_DIR=$(tr '\0' '\n' < "/proc/${PID}/environ" | sed -n 's/^CREDENTIALS_DIRECTORY=//p' | head -1)

echo
echo "--- Credential directory availability ---"
if [ -n "$CRED_DIR" ] && [ -r "$CRED_DIR/server-cert" ]; then
    echo "SERVER_CERTIFICATE=AVAILABLE"
else
    echo "SERVER_CERTIFICATE=NOT_AVAILABLE"
fi

echo
echo "--- Server certificate public metadata ---"
if [ -n "$CRED_DIR" ] && [ -r "$CRED_DIR/server-cert" ]; then
    openssl x509 -in "$CRED_DIR/server-cert" -noout \
      -subject -issuer -serial -dates -ext subjectAltName
else
    echo "CERTIFICATE_METADATA=NOT_CHECKED"
fi

echo
echo "--- Certificate file metadata ---"
if [ -n "$CRED_DIR" ] && [ -r "$CRED_DIR/server-cert" ]; then
    stat -c 'owner=%U:%G mode=%a size=%s' "$CRED_DIR/server-cert"
fi

echo
echo "PRIVATE_KEY_CONTENT_DISPLAYED=NO"
echo "API_TOKEN_DISPLAYED=NO"
echo "INDEXER_CREDENTIALS_DISPLAYED=NO"
echo "NETWORK_REQUEST=NO"
echo "CONFIGURATION_CHANGED=NO"
```

| Item | Result |
|---|---|
| SAN | `IP Address:192.168.0.220` |
| Issuer | `AI-Defense-Relay-Internal-CA` |
| Validity | November 20, 2026 – February 22, 2029 |

## 2.2 The CA That VM 230 Trusts

> **Run on: VM 230**

```bash
echo "===== VM230: RELAY CA TRUST CONFIGURATION AUDIT ====="

cd /opt/ai-defense-manager || true

echo
echo "--- CA file resolution in relay client ---"
grep -n -B 8 -A 12 'ca_file' app/services/wazuh_relay.py

echo
echo "--- Relay TLS settings definitions ---"
grep -n -i -B 3 -A 5 'wazuh_relay' app/core/config.py

echo
echo "--- CA-related configuration names (values excluded) ---"
grep -RInE \
  'ca_file|ca_bundle|ca_cert|certificate|cert_path|ssl_context|verify=' \
  app \
  --include='*.py' \
  --exclude='*.pyc' \
  2>/dev/null | sed -E 's/(=|:)[[:space:]]*["'\''][^"'\'']*["'\'']/=\<VALUE REDACTED\>/g'

echo
echo "--- Relevant CA certificate file metadata ---"
find /etc/ssl /opt/ai-defense-manager \
  -type f \( -iname '*ca*.crt' -o -iname '*ca*.pem' -o -iname '*ca*.cer' \) \
  -printf '%p\n' 2>/dev/null | head -40

echo
echo "CA_PRIVATE_KEY_DISPLAYED=NO"
echo "BEARER_TOKEN_DISPLAYED=NO"
echo "NETWORK_REQUEST=NO"
echo "CONFIGURATION_CHANGED=NO"
```

VM 230 loads the internal CA certificate from `/etc/ai-defense-manager/credentials/relay-ca.crt`, and TLS verification is not disabled.

> **Run on: VM 230**

```bash
echo "===== VM230: RELAY CREDENTIAL FILE AVAILABILITY ====="

echo
echo "--- Credential directory ---"
if [ -d /etc/ai-defense-manager/credentials ]; then
    stat -c 'directory owner=%U:%G mode=%a' \
      /etc/ai-defense-manager/credentials
else
    echo "CREDENTIAL_DIRECTORY=MISSING"
fi

echo
echo "--- Expected CA certificate ---"
if [ -f /etc/ai-defense-manager/credentials/relay-ca.crt ]; then
    stat -c 'CA owner=%U:%G mode=%a size=%s' \
      /etc/ai-defense-manager/credentials/relay-ca.crt
    openssl x509 \
      -in /etc/ai-defense-manager/credentials/relay-ca.crt \
      -noout -subject -issuer -fingerprint -sha256
else
    echo "RELAY_CA_FILE=MISSING"
fi

echo
echo "--- Expected API token file (contents hidden) ---"
if [ -f /etc/ai-defense-manager/credentials/relay-api.token ]; then
    stat -c 'TOKEN_FILE owner=%U:%G mode=%a size=%s' \
      /etc/ai-defense-manager/credentials/relay-api.token
else
    echo "RELAY_TOKEN_FILE=MISSING"
fi

echo
echo "--- Service credential-related metadata (values excluded) ---"
systemctl show ai-defense-manager.service \
  -p User -p Group -p LoadCredential -p LoadCredentialEncrypted

echo
echo "CREDENTIAL_CONTENTS_DISPLAYED=NO"
echo "NETWORK_REQUEST=NO"
echo "CONFIGURATION_CHANGED=NO"
```

| Item | State |
|---|---|
| CA certificate | present and readable; issuer `AI-Defense-Relay-Internal-CA` |
| API token | present (contents not displayed) |
| Credentials directory | `root:ai-defense`, `750` |
| CA and token files | `root:ai-defense`, `640` |

The SHA-256 fingerprint of VM 230's CA certificate was as follows.

```text
71:E8:CE:68:FA:56:0D:13:98:5A:1C:C5:18:D3:24:4B:BA:DA:6F:29:DE:49:97:71:0C:29:F9:21:D2:84:61:54
```

## 2.3 The Original CA File on VM 220

> **Run on: VM 220**

```bash
echo "===== VM220: INTERNAL CA CERTIFICATE FINGERPRINT AUDIT ====="

PID=$(systemctl show ai-defense-relay.service -p MainPID --value)
CRED_DIR=$(tr '\0' '\n' < "/proc/${PID}/environ" | sed -n 's/^CREDENTIALS_DIRECTORY=//p' | head -1)

echo
echo "--- Credential directory path ---"
if [ -n "$CRED_DIR" ] && [ -d "$CRED_DIR" ]; then
    echo "CREDENTIAL_DIRECTORY=AVAILABLE"
    find "$CRED_DIR" -maxdepth 1 -type f -printf '%f\n' | sort
else
    echo "CREDENTIAL_DIRECTORY=NOT_AVAILABLE"
fi

echo
echo "--- Public certificate fingerprints in credential directory ---"
if [ -n "$CRED_DIR" ] && [ -d "$CRED_DIR" ]; then
    find "$CRED_DIR" -maxdepth 1 -type f \
      \( -iname '*.crt' -o -iname '*.pem' -o -iname '*ca*' \) \
      ! -iname '*key*' -print0 |
    while IFS= read -r -d '' cert; do
        echo "CERTIFICATE_FILE=$(basename "$cert")"
        openssl x509 -in "$cert" -noout \
          -subject -issuer -fingerprint -sha256 2>/dev/null
    done
fi

echo
echo "--- Relay systemd credential declarations (paths only) ---"
systemctl cat ai-defense-relay.service |
  grep -E '^[[:space:]]*(LoadCredential|LoadCredentialEncrypted)=' |
  sed -E 's/:[^ ]*(token|password|key)[^ ]*/:<REDACTED>/Ig'

echo
echo "PRIVATE_KEY_CONTENT_DISPLAYED=NO"
echo "TOKEN_CONTENT_DISPLAYED=NO"
echo "INDEXER_PASSWORD_DISPLAYED=NO"
echo "NETWORK_REQUEST=NO"
echo "CONFIGURATION_CHANGED=NO"
```

`indexer-ca` in VM 220's credentials is for Wazuh Indexer, not the Relay's CA. We look for the original file of the Relay's CA.

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY CA SOURCE FILE AUDIT ====="

echo
echo "--- Candidate CA certificate files ---"
find /etc/credstore /etc/ssl /usr/local/share/ca-certificates \
  -maxdepth 3 -type f \
  \( -iname '*relay*ca*' -o -iname '*defense*ca*' -o -iname '*internal*ca*' \) \
  -printf '%p\n' 2>/dev/null

echo
echo "--- Systemd credential source declarations ---"
systemctl cat ai-defense-relay.service |
  grep -E '^[[:space:]]*LoadCredential(Encrypted)?=' |
  sed -E 's/:[^ ]*(token|password|key)[^ ]*/:<REDACTED>/Ig'

echo
echo "--- Server certificate issuer and SAN ---"
PID=$(systemctl show ai-defense-relay.service -p MainPID --value)
CRED_DIR=$(tr '\0' '\n' < "/proc/${PID}/environ" |
  sed -n 's/^CREDENTIALS_DIRECTORY=//p' | head -1)

openssl x509 -in "$CRED_DIR/server-cert" -noout \
  -issuer -subject -ext subjectAltName

echo
echo "PRIVATE_KEY_DISPLAYED=NO"
echo "CREDENTIAL_CONTENTS_DISPLAYED=NO"
echo "NETWORK_REQUEST=NO"
echo "CONFIGURATION_CHANGED=NO"
```

The Relay's dedicated CA was in `/etc/credstore/ai-defense-relay-ca`.

## 2.4 Matching Fingerprints and Signatures

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY CA CRYPTOGRAPHIC VERIFICATION ====="

CA=/etc/credstore/ai-defense-relay-ca

PID=$(systemctl show ai-defense-relay.service -p MainPID --value)
CRED_DIR=$(tr '\0' '\n' < "/proc/${PID}/environ" |
  sed -n 's/^CREDENTIALS_DIRECTORY=//p' | head -1)

echo
echo "--- Relay CA file metadata ---"
stat -c 'owner=%U:%G mode=%a size=%s' "$CA"

echo
echo "--- Relay CA identity and fingerprint ---"
openssl x509 -in "$CA" -noout \
  -subject -issuer -serial -fingerprint -sha256

echo
echo "--- Server certificate verification against Relay CA ---"
openssl verify -CAfile "$CA" "$CRED_DIR/server-cert"

echo
echo "--- Server certificate fingerprint ---"
openssl x509 -in "$CRED_DIR/server-cert" -noout -fingerprint -sha256

echo
echo "PRIVATE_KEY_DISPLAYED=NO"
echo "CREDENTIAL_CONTENTS_DISPLAYED=NO"
echo "NETWORK_REQUEST=NO"
echo "CONFIGURATION_CHANGED=NO"
```

| Checked | Result |
|---|---|
| SHA-256 of VM 220's CA | `71:E8:CE:68:…:84:61:54` |
| SHA-256 of VM 230's CA | the same |
| CA Subject | `AI-Defense-Relay-Internal-CA` |
| Server certificate verified by the CA | `OK` |
| Server certificate SAN | `192.168.0.220` |
| Minimum TLS version | TLS 1.2 |

We confirmed that the trust relationship is correct cryptographically, not just that the issuer names are the same.

# Chapter 3: Testing with `/health`

## 3.1 An Endpoint That Does Not Query the Indexer

Calling `/v1/alerts` queries Wazuh Indexer. First we check whether there is an endpoint that does not.

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY NON-INDEXER TEST ENDPOINT AUDIT ====="

cd /opt/ai-defense-relay || true

echo
echo "--- HTTP handler routes and response paths ---"
grep -n -E \
  'def do_|urlsplit|parse_qs|send_json|indexer|alerts|health|status|method_not_allowed' \
  relay.py

echo
echo "--- Route dispatch context ---"
sed -n '125,265p' relay.py |
  sed -E 's/(API_TOKEN|INDEXER_PASSWORD|INDEXER_AUTH)[[:space:]]*=.*/\1 = <REDACTED>/'

echo
echo "SOURCE_MODIFIED=NO"
echo "HTTP_REQUEST=NO"
echo "WAZUH_INDEXER_REQUEST=NO"
echo "DATABASE_ACCESSED=NO"
echo "CREDENTIALS_DISPLAYED=NO"
```

The Relay processes requests in the following order; for `/health` it returns `200 OK` before querying the Indexer.

1. Check that the source IP address is `192.168.0.221`
2. Check the Bearer token
3. For `/health`, return `200 OK` and finish
4. Query Wazuh Indexer only for `/v1/alerts`

## 3.2 Testing TLS and Bearer Authentication

With CA certificate verification and Bearer authentication enabled, the token is read from the file and used in memory only.

> **Run on: VM 230**

```bash
echo "===== VM230 -> VM220: TLS + BEARER AUTH HEALTH TEST ====="

cd /opt/ai-defense-manager || true

venv/bin/python - <<'PY'
from pathlib import Path
import httpx
import sys

base_url = "https://192.168.0.220:8765"
ca_file = Path("/etc/ai-defense-manager/credentials/relay-ca.crt")
token_file = Path("/etc/ai-defense-manager/credentials/relay-api.token")

print("CA_FILE_EXISTS =", ca_file.is_file())
print("TOKEN_FILE_EXISTS =", token_file.is_file())

if not ca_file.is_file() or not token_file.is_file():
    print("RESULT=PRECHECK_FAILED")
    sys.exit(0)

token = token_file.read_text(encoding="utf-8").strip()

if not token:
    print("RESULT=EMPTY_TOKEN")
    sys.exit(0)

try:
    with httpx.Client(
        verify=str(ca_file),
        timeout=10.0,
        follow_redirects=False,
    ) as client:
        response = client.get(
            base_url + "/health",
            headers={"Authorization": "Bearer " + token},
        )

    print("HTTP_STATUS =", response.status_code)
    print("RESPONSE_BODY =", response.text[:512])

    if response.status_code == 200 and response.json() == {"status": "ok"}:
        print("TLS_VERIFICATION=PASS")
        print("BEARER_AUTHENTICATION=PASS")
        print("RELAY_HEALTH=PASS")
        print("RESULT=PASS")
    else:
        print("RESULT=FAIL")

except httpx.ConnectError as exc:
    print("CONNECTION_OR_TLS_ERROR =", type(exc).__name__)
    print("RESULT=FAIL")
except httpx.TimeoutException:
    print("ERROR=TIMEOUT")
    print("RESULT=FAIL")
except Exception as exc:
    print("ERROR_TYPE =", type(exc).__name__)
    print("RESULT=FAIL")

print("TOKEN_DISPLAYED=NO")
print("WAZUH_INDEXER_REQUEST=NO")
print("DATABASE_ACCESSED=NO")
print("OLLAMA_REQUEST=NO")
PY
```

| Checked | Result |
|---|---|
| Loading the CA certificate | passed |
| TLS certificate verification | passed |
| Source IP restriction | passed (200 response) |
| Bearer authentication | passed |
| Relay `/health` | `HTTP 200` |
| Access to Wazuh Indexer, PostgreSQL, Ollama | none |

# Closing Notes

In Part 51 we confirmed that a secure HTTPS path from VM 230 to the Relay on VM 220 is in place.

| Item | Result |
|---|---|
| Connection target | `https://192.168.0.220:8765/` (TLS 1.2 or later) |
| Server certificate | SAN `192.168.0.220`, signed by `AI-Defense-Relay-Internal-CA` |
| CA | VM 220 `/etc/credstore/ai-defense-relay-ca` and VM 230 `relay-ca.crt` are the same |
| Authentication | source IP (`192.168.0.221`) and Bearer token |
| `/health` | `HTTP 200` |

In the next part, Part 52, we fetch real Wazuh alerts once.

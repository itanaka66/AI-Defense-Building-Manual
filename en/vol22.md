---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 22: Checking the Relay and Its Connection Details"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 22 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". We check the Wazuh → Relay → AI Defense Manager chain built in Parts 14–21 **using reads only**, without changing any settings.

| What is checked | Where |
|---|---|
| Connection from VM 230 to the Relay (connection details, TLS) | VM 230 |
| The Relay's service, program, listening and secrets | VM 220 |
| The Indexer's read-only user (authentication, search permissions, fields returned) | VM 220 |

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **VM 220**: security-core (root)
- The contents of passwords and tokens are not shown. Programs that use a password only read it from a file and do not display it.

# Chapter 1: The VM 230 Side

## 1.1 Are There Wazuh Services?

> **Run on: VM 230**

```bash
systemctl list-units --type=service --all --no-pager | grep -Ei 'wazuh|filebeat|ossec'
```

At build time nothing was shown. VM 230 is not a Wazuh agent; it receives alerts by calling the Relay's `/v1/alerts` over HTTPS.

## 1.2 The Code and Settings That Call the Relay

```bash
cd /opt/ai-defense-manager && sed -n '1,260p' app/services/wazuh_relay.py
```

```bash
cd /opt/ai-defense-manager && grep -n -B 3 -A 5 -E 'wazuh_relay_(base_url|ca_file|token_file|timeout_seconds)' app/core/config.py
```

The following was confirmed.

- TLS is verified with the CA certificate
- The Bearer token is read from a file and never appears in code or logs
- Redirects are not followed; there is a timeout (1–60 seconds)
- At most 100 alerts are fetched, over at most 24 hours
- `full_log` and arbitrary `data` are not taken in

## 1.3 Permissions of the Connection Details

```bash
stat -c '%A %a %U:%G %n' /etc/ai-defense-manager /etc/ai-defense-manager/credentials /etc/ai-defense-manager/credentials/relay-ca.crt /etc/ai-defense-manager/credentials/relay-api.token
```

| Target | Permissions |
|---|---|
| `/etc/ai-defense-manager` | `755 root:root` |
| `credentials/` | `750 root:ai-defense` |
| `relay-ca.crt` | `640 root:ai-defense` |
| `relay-api.token` | `640 root:ai-defense` |

## 1.4 Checking TLS

Without sending the token, check only the certificate.

```bash
openssl x509 -in /etc/ai-defense-manager/credentials/relay-ca.crt -noout -subject -issuer -dates -fingerprint -sha256
```

At build time this was the self-signed CA certificate of `AI-Defense-Relay-Internal-CA`, valid from November 20, 2026 to November 17, 2036.

```bash
openssl s_client -connect 192.168.0.220:8765 -CAfile /etc/ai-defense-manager/credentials/relay-ca.crt -verify_return_error -brief </dev/null
```

It connected with TLS 1.3 and showed `Verification: OK`. The application connects by IP address, so also check that the certificate's SAN contains the IP address.

```bash
openssl s_client -connect 192.168.0.220:8765 -CAfile /etc/ai-defense-manager/credentials/relay-ca.crt -showcerts </dev/null 2>/dev/null | openssl x509 -noout -subject -ext subjectAltName
```

If `IP Address:192.168.0.220` is present, it matches the URL in the settings (`https://192.168.0.220:8765/`).

# Chapter 2: The Relay Side

## 2.1 The Service

> **Run on: VM 220**

```bash
hostnamectl && systemctl status ai-defense-relay.service --no-pager -l
```

At build time this was Ubuntu 24.04.5 LTS, `ai-defense-relay.service` was `active (running)`, and requests from VM 230 (`192.168.0.33`) were logged with `200`.

## 2.2 The Program

```bash
sed -n '1,300p' /opt/ai-defense-relay/relay.py
```

The safety measures confirmed were as follows.

- Sources are limited to `192.168.0.33`
- The Bearer token is compared with `hmac.compare_digest()`
- TLS to the Indexer is also verified with a CA certificate
- The number and time range of Indexer searches are limited
- The fields returned are limited by both `_source` and `sanitize_alert()` (`full_log` and arbitrary `data` are not returned)
- Modifying requests such as `POST`, `PUT` and `DELETE` are refused; TLS older than 1.2 is refused
- At most eight requests are processed concurrently; Indexer responses are limited to 2 MiB
- Error responses contain no internal exceptions or authentication information

> **Note:** The relay.py shown at build time contained, in addition to the content of Part 14, 4.1–4.3, a change that limits the access log to "source IP address and status" and a change that limits concurrent requests to eight (`threading.BoundedSemaphore(8)`). The steps for these changes are not in the build records (author's notes, item 14-A).

## 2.3 The Service Definition

```bash
systemctl cat ai-defense-relay.service
```

It runs as a dedicated user (not root), secrets are passed with `LoadCredential`, it has no privileges, the file system is read-only in principle, and there are limits on memory and number of tasks (Part 14, 5.1).

## 2.4 Listening

```bash
ss -lntp | grep -E '(:8765|:9200)\b'
```

| Service | Listening on |
|---|---|
| Relay | `192.168.0.220:8765` (only the designated IP) |
| Wazuh Indexer | `127.0.0.1:9200` (local only) |

Other hosts cannot connect to the Indexer directly; everything goes through the Relay.

```bash
ufw status verbose
```

At build time UFW on VM 220 was disabled. The Relay listens only on the designated IP and the application also limits sources, but network-layer restriction is a separate matter. Enabling UFW could affect Wazuh's traffic and so on, so it is not changed here (author's notes, item 22-A).

## 2.5 Permissions of the Secrets

```bash
stat -c '%A %a %U:%G %n' /etc/credstore /etc/credstore/ai-defense-relay-token /etc/credstore/ai-defense-indexer-password /etc/credstore/ai-defense-indexer-ca /etc/credstore/ai-defense-relay-server-cert /etc/credstore/ai-defense-relay-server-key
```

`/etc/credstore` was `700 root:root`, and all files inside were `600 root:root`.

# Chapter 3: The Indexer's Read-Only User

## 3.1 Configuration Files on Disk

> **Run on: VM 220**

```bash
grep -n -A 12 -B 4 'ai-defense-reader' /etc/wazuh-indexer/opensearch-security/roles.yml /etc/wazuh-indexer/opensearch-security/roles_mapping.yml
```

```bash
grep -RIl --include='*.yml' --include='*.yaml' 'ai-defense-reader' /etc/wazuh-indexer/opensearch-security/
```

Neither showed anything. Check by displaying only the user names (password hashes are not shown).

```bash
find /etc/wazuh-indexer/opensearch-security -maxdepth 2 -type f -printf '%f\n' | sort
```

```bash
awk '/^[^[:space:]#][^:]*:/{name=$1; sub(/:$/,"",name); if(name!="") print name}' /etc/wazuh-indexer/opensearch-security/internal_users.yml
```

```bash
sed -n '1,260p' /etc/wazuh-indexer/opensearch-security/roles.yml && printf '\n--- ROLE MAPPINGS ---\n' && sed -n '1,260p' /etc/wazuh-indexer/opensearch-security/roles_mapping.yml
```

The on-disk `internal_users.yml`, `roles.yml` and `roles_mapping.yml` contain neither `ai-defense-reader` nor `ai_defense_alerts_read`. This is because in Part 13 these three files were not edited directly; instead, the merged files prepared in `/root` (`/root/ai_defense_merged_*.yml`) were sent to the Indexer with `securityadmin.sh`.

```bash
grep -nE 'authc:|authentication_backend|http_authenticator|type:|order:|http_enabled|transport_enabled|roles_key|userbase|usersearch|username_attribute|backend' /etc/wazuh-indexer/opensearch-security/config.yml
```

HTTP authentication is Basic authentication with the internal user database (`type: intern`).

## 3.2 Authentication on the Running Indexer

Check whether the running Indexer, not the files on disk, authenticates `ai-defense-reader`. The password is read from `/etc/credstore` and not displayed.

```bash
python3 - <<'PY'
import base64, json, ssl, urllib.request, urllib.error

password = open(
    "/etc/credstore/ai-defense-indexer-password", "r"
).read().strip()

token = base64.b64encode(
    ("ai-defense-reader:" + password).encode()
).decode()

request = urllib.request.Request(
    "https://127.0.0.1:9200/_plugins/_security/authinfo",
    headers={"Authorization": "Basic " + token},
)

context = ssl.create_default_context(
    cafile="/etc/credstore/ai-defense-indexer-ca"
)

try:
    with urllib.request.urlopen(request, context=context, timeout=10) as response:
        data = json.loads(response.read())
        print("HTTP_STATUS:", response.status)
        for key in ("user_name", "backend_roles", "roles", "is_admin"):
            if key in data:
                print(f"{key}: {data[key]}")
except urllib.error.HTTPError as exc:
    print("HTTP_STATUS:", exc.code)
    print("AUTHENTICATION_OR_AUTHORIZATION_FAILED")
except Exception as exc:
    print("CHECK_ERROR:", type(exc).__name__)
PY
```

At build time it returned `HTTP_STATUS: 200`, and the roles were `own_index` and `ai_defense_alerts_read`.

## 3.3 The Management API Cannot Be Used

```bash
python3 - <<'PY'
import base64, json, ssl, urllib.request, urllib.error

password = open("/etc/credstore/ai-defense-indexer-password").read().strip()
auth = base64.b64encode(("ai-defense-reader:" + password).encode()).decode()
request = urllib.request.Request(
    "https://127.0.0.1:9200/_plugins/_security/api/roles/ai_defense_alerts_read",
    headers={"Authorization": "Basic " + auth},
)
context = ssl.create_default_context(cafile="/etc/credstore/ai-defense-indexer-ca")

try:
    with urllib.request.urlopen(request, context=context, timeout=10) as response:
        data = json.loads(response.read())
        print("HTTP_STATUS:", response.status)
        print(json.dumps(data, indent=2))
except urllib.error.HTTPError as exc:
    print("HTTP_STATUS:", exc.code)
    print("ROLE_DEFINITION_NOT_READABLE_BY_THIS_ACCOUNT")
except Exception as exc:
    print("CHECK_ERROR:", type(exc).__name__)
PY
```

It returned `HTTP_STATUS: 403`. A user that only reads alerts does not need administrative permission to view role definitions. No permissions are added.

## 3.4 Searching Alerts

Without fetching the body (`_source: False`), check only whether searching is allowed.

```bash
python3 - <<'PY'
import base64, json, ssl, urllib.request, urllib.error

password = open("/etc/credstore/ai-defense-indexer-password").read().strip()
auth = base64.b64encode(("ai-defense-reader:" + password).encode()).decode()

query = {
    "size": 1,
    "track_total_hits": False,
    "_source": False,
    "query": {
        "range": {
            "timestamp": {"gte": "now-15m"}
        }
    }
}

request = urllib.request.Request(
    "https://127.0.0.1:9200/wazuh-alerts-4.x-*/_search",
    data=json.dumps(query).encode(),
    headers={
        "Authorization": "Basic " + auth,
        "Content-Type": "application/json",
    },
    method="POST",
)

context = ssl.create_default_context(
    cafile="/etc/credstore/ai-defense-indexer-ca"
)

try:
    with urllib.request.urlopen(request, context=context, timeout=10) as response:
        data = json.loads(response.read())
        hits = data.get("hits", {}).get("hits", [])
        print("HTTP_STATUS:", response.status)
        print("SEARCH_API_ACCESS: OK")
        print("RETURNED_HITS:", len(hits))
except urllib.error.HTTPError as exc:
    print("HTTP_STATUS:", exc.code)
    print("SEARCH_API_ACCESS: DENIED")
except Exception as exc:
    print("CHECK_ERROR:", type(exc).__name__)
PY
```

## 3.5 Fields Returned

Specify the same 10 fields as the Relay, fetch one alert, and show only the names of the fields returned (values are not shown).

```bash
python3 - <<'PY'
import base64, json, ssl, urllib.request

password = open("/etc/credstore/ai-defense-indexer-password").read().strip()
auth = base64.b64encode(("ai-defense-reader:" + password).encode()).decode()

fields = [
    "timestamp", "agent.id", "agent.ip", "agent.name",
    "manager.name", "rule.level", "rule.description",
    "rule.id", "location", "decoder.name"
]

query = {
    "size": 1,
    "track_total_hits": False,
    "_source": fields,
    "query": {"range": {"timestamp": {"gte": "now-15m"}}}
}

request = urllib.request.Request(
    "https://127.0.0.1:9200/wazuh-alerts-4.x-*/_search",
    data=json.dumps(query).encode(),
    headers={"Authorization": "Basic " + auth, "Content-Type": "application/json"},
    method="POST"
)

context = ssl.create_default_context(
    cafile="/etc/credstore/ai-defense-indexer-ca"
)

with urllib.request.urlopen(request, context=context, timeout=10) as response:
    data = json.loads(response.read())
    hits = data.get("hits", {}).get("hits", [])
    print("HTTP_STATUS:", response.status)
    print("RETURNED_HITS:", len(hits))
    if hits:
        source = hits[0].get("_source", {})
        print("RETURNED_FIELDS:", sorted(source.keys()))
        forbidden = {"full_log", "data", "command", "pwd", "user"}
        print("FORBIDDEN_FIELDS_PRESENT:", sorted(forbidden.intersection(source)))
PY
```

At build time six were returned: `agent`, `decoder`, `location`, `manager`, `rule` and `timestamp`. `full_log`, `data`, `command`, `pwd` and `user` were not returned.

## 3.6 Configuration Files and Backups

```bash
ls -ld /etc/wazuh-indexer /etc/wazuh-indexer/opensearch-security
```

```bash
find /etc/wazuh-indexer/opensearch-security -maxdepth 1 -type f -printf '%f  %TY-%Tm-%Td %TH:%TM  %m\n' | sort
```

Check whether the on-disk `internal_users.yml` defines this user, without showing password hashes.

```bash
python3 - <<'PY'
import yaml

path = "/etc/wazuh-indexer/opensearch-security/internal_users.yml"

with open(path, encoding="utf-8") as f:
    users = yaml.safe_load(f)

user = users.get("ai-defense-reader")

if user is None:
    print("DISK_USER_DEFINITION: NOT_FOUND")
else:
    print("DISK_USER_DEFINITION: FOUND")
    for key in ("reserved", "hidden", "backend_roles", "attributes"):
        if key in user:
            print(f"{key}: {user[key]}")
    print("PASSWORD_FIELD: PRESENT" if "hash" in user else "PASSWORD_FIELD: ABSENT")
PY
```

```bash
find /etc/wazuh-indexer -maxdepth 3 -type f \( -iname '*internal_users*' -o -iname '*roles*' -o -iname '*security*' \) -printf '%p\n' | sort
```

```bash
python3 - <<'PY'
import yaml
from pathlib import Path

base = Path("/etc/wazuh-indexer/internalusers-backup")

for path in sorted(base.glob("internal_users_*.yml.bkp")):
    with path.open(encoding="utf-8") as f:
        users = yaml.safe_load(f) or {}

    user = users.get("ai-defense-reader")
    print(f"\nFILE: {path.name}")
    print("USER_FOUND:", user is not None)

    if user is not None:
        for key in ("reserved", "hidden", "backend_roles", "attributes"):
            if key in user:
                print(f"{key}: {user[key]}")
        print("PASSWORD_HASH_PRESENT:", "hash" in user)
PY
```

At build time, `ai-defense-reader` was not in the on-disk `internal_users.yml` or in any of the three backups.

| Check | Result |
|---|---|
| `ai-defense-reader` on the running Indexer | Present (can authenticate) |
| `ai_defense_alerts_read` role | In effect (can search) |
| On-disk `internal_users.yml`, `roles.yml` | No definition |

The running configuration and the YAML on disk do not match. If the YAML is reapplied with `securityadmin.sh` in this state, `ai-defense-reader` disappears and the Relay stops working. **Do not reapply the on-disk YAML as is** (author's notes, item 22-B).

# Closing Notes

The results of the checks in Part 22 are as follows.

| Target | Result |
|---|---|
| Permissions of connection details, TLS and SAN on VM 230 | No problems |
| The Relay's service, program, listening and permissions of secrets | No problems |
| Authentication, searching and fields returned for `ai-defense-reader` | No problems (management API returns `403`) |
| UFW on VM 220 | Disabled (not changed here) |
| The Indexer's running configuration vs. YAML on disk | Do not match |

In the next part, we examine the contents of the Indexer's roles and where records of configuration changes (the audit log) are kept.

---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 23: Investigating Indexer Permissions and the Audit Log"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 23 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". In Part 22 we found that the running Indexer has `ai-defense-reader` and `ai_defense_alerts_read`, while the YAML on disk has no definitions for them. Here we investigate the following **using reads only**, without changing settings.

1. How records of configuration changes (the OpenSearch Security audit log) are configured, and where they are kept
2. The actual definitions of the roles and the user, using the administrator certificate
3. Records about `ai-defense-reader` remaining in the Indexer's logs

As of this part, where the audit log is saved has not been identified. This part records the steps taken and what was learned.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **security-core VM 220 (root)**.
- Log text, passwords and the contents of private keys are not shown.

# Chapter 1: Audit Log Settings

## 1.1 Audit Log Files

```bash
find /var/log/wazuh-indexer -maxdepth 2 -type f \( -iname '*audit*' -o -iname '*security*' \) -printf '%p  %TY-%Tm-%Td %TH:%TM  %s bytes\n' 2>/dev/null | sort
```

At build time no files that looked like audit logs were found.

## 1.2 audit.yml

```bash
grep -nEi -A 3 -B 2 'audit|compliance|external_config|enabled|log4j' /etc/wazuh-indexer/opensearch-security/audit.yml
```

```bash
sed -n '25,130p' /etc/wazuh-indexer/opensearch-security/audit.yml
```

| Setting | Value |
|---|---|
| Auditing of the REST API | Enabled |
| Auditing of the Transport API | Enabled |
| Recording changes to internal security configuration (`internal_config`) | Enabled |
| Recording changes to external configuration files (`external_config`) | Disabled |
| Recording request bodies (`log_request_body`) | Enabled |
| Events for successful authentication and granted privileges | Not recorded |

`log_request_body: true` is a setting that also records the bodies of REST API requests. The handling of these records needs care (author's notes, item 23-A).

```bash
grep -nEi 'audit|appender|fileName|filePattern' /etc/wazuh-indexer/log4j2.properties
```

No output destination dedicated to audit logs can be found in `log4j2.properties`.

```bash
sed -n '1,28p' /etc/wazuh-indexer/opensearch-security/audit.yml
```

Read it as YAML and show the items related to the output method.

```bash
python3 - <<'PY'
import yaml

path = "/etc/wazuh-indexer/opensearch-security/audit.yml"

with open(path, encoding="utf-8") as f:
    data = yaml.safe_load(f) or {}

config = data.get("config", {})
audit = config.get("audit", {})
compliance = config.get("compliance", {})

print("AUDIT_ENABLED:", config.get("enabled"))
print("AUDIT_CONFIG_KEYS:", sorted(audit.keys()))
print("AUDIT_OUTPUT_TYPE:", audit.get("type", "NOT_EXPLICITLY_CONFIGURED"))
print("COMPLIANCE_ENABLED:", compliance.get("enabled"))
print("INTERNAL_CONFIG_AUDIT:", compliance.get("internal_config"))
PY
```

Auditing is enabled, but the output method is not written in `audit.yml`.

## 1.3 The Indexer's Operational Logs

Show them with strings that look like secrets masked.

```bash
journalctl -u wazuh-indexer --since "2026-11-17" --no-pager | grep -Ei 'audit|compliance|securityanalytics|internalusers|rolesmapping|roles' | tail -80 | sed -E 's/(password|token|authorization)([=: ]+)[^ ,"]+/\1\2[REDACTED]/Ig'
```

At build time no records about auditing or role changes were found.

# Chapter 2: Checking Roles and Users with the Administrator Certificate

## 2.1 ai-defense-reader Cannot View the List

```bash
python3 - <<'PY'
import base64, json, ssl, urllib.request, urllib.error

password = open("/etc/credstore/ai-defense-indexer-password").read().strip()
auth = base64.b64encode(("ai-defense-reader:" + password).encode()).decode()

request = urllib.request.Request(
    "https://127.0.0.1:9200/_cat/indices?format=json&h=index",
    headers={"Authorization": "Basic " + auth},
)

context = ssl.create_default_context(
    cafile="/etc/credstore/ai-defense-indexer-ca"
)

try:
    with urllib.request.urlopen(request, context=context, timeout=10) as response:
        indices = json.loads(response.read())
        names = sorted(
            item.get("index", "")
            for item in indices
            if any(word in item.get("index", "").lower()
                   for word in ("audit", "security", "compliance"))
        )
        print("HTTP_STATUS:", response.status)
        print("MATCHING_INDEX_COUNT:", len(names))
        for name in names:
            print(name)
except urllib.error.HTTPError as exc:
    print("HTTP_STATUS:", exc.code)
    print("INDEX_LIST_ACCESS_DENIED")
except Exception as exc:
    print("CHECK_ERROR:", type(exc).__name__)
PY
```

It returned `HTTP_STATUS: 403`. A user that only reads alerts does not need permission to view the list of indices. Rather than adding permissions, check from the administrator's side.

## 2.2 The Administrator Certificate

Show only file names and permissions.

```bash
find /etc/wazuh-indexer -maxdepth 3 -type f \( -iname '*admin*.pem' -o -iname '*admin*.crt' -o -iname '*admin*.key' \) -printf '%p  %m  %u:%g\n' | sort
```

```bash
find /etc/wazuh-indexer/certs -maxdepth 1 -type f -printf '%f  %m  %u:%g\n' | sort
```

`admin.pem` and `admin-key.pem` are owned by `wazuh-indexer` with permissions `400`. The following programs make read-only queries to the Indexer with this certificate.

## 2.3 The Definition of ai_defense_alerts_read

```bash
python3 - <<'PY'
import json
import ssl
import urllib.request
import urllib.error

context = ssl.create_default_context(
    cafile="/etc/wazuh-indexer/certs/root-ca.pem"
)
context.load_cert_chain(
    certfile="/etc/wazuh-indexer/certs/admin.pem",
    keyfile="/etc/wazuh-indexer/certs/admin-key.pem"
)

url = "https://127.0.0.1:9200/_plugins/_security/api/roles/ai_defense_alerts_read"
request = urllib.request.Request(url)

try:
    with urllib.request.urlopen(request, context=context, timeout=10) as response:
        data = json.loads(response.read())
        print("HTTP_STATUS:", response.status)
        print(json.dumps(data, indent=2))
except urllib.error.HTTPError as exc:
    print("HTTP_STATUS:", exc.code)
    print("ADMIN_ROLE_READ_FAILED")
except Exception as exc:
    print("CHECK_ERROR:", type(exc).__name__)
PY
```

| Item | Value |
|---|---|
| `cluster_permissions` | Empty |
| `index_patterns` | Only `wazuh-alerts-4.x-*` |
| `allowed_actions` | Only `read` |
| `tenant_permissions` | Empty |
| `reserved`, `static` | `false` |

Nothing other than Wazuh alerts is targeted, and there are no write, delete or cluster management permissions.

## 2.4 The Definition of own_index

`ai-defense-reader` also has the standard role `own_index`.

```bash
python3 - <<'PY'
import json
import ssl
import urllib.request

context = ssl.create_default_context(
    cafile="/etc/wazuh-indexer/certs/root-ca.pem"
)
context.load_cert_chain(
    certfile="/etc/wazuh-indexer/certs/admin.pem",
    keyfile="/etc/wazuh-indexer/certs/admin-key.pem"
)

url = "https://127.0.0.1:9200/_plugins/_security/api/roles/own_index"
request = urllib.request.Request(url)

with urllib.request.urlopen(request, context=context, timeout=10) as response:
    data = json.loads(response.read())
    print("HTTP_STATUS:", response.status)
    print(json.dumps(data, indent=2))
PY
```

`own_index` is a standard role (`reserved: true`) that allows `indices_all` on an index with the same name as the user (`${user_name}`), and also allows `cluster_composite_ops`. So check whether an index named `ai-defense-reader` exists.

```bash
python3 - <<'PY'
import ssl
import urllib.request
import urllib.error

context = ssl.create_default_context(
    cafile="/etc/wazuh-indexer/certs/root-ca.pem"
)
context.load_cert_chain(
    certfile="/etc/wazuh-indexer/certs/admin.pem",
    keyfile="/etc/wazuh-indexer/certs/admin-key.pem"
)

url = "https://127.0.0.1:9200/ai-defense-reader"
request = urllib.request.Request(url, method="HEAD")

try:
    with urllib.request.urlopen(request, context=context, timeout=10) as response:
        print("INDEX_EXISTS: yes")
        print("HTTP_STATUS:", response.status)
except urllib.error.HTTPError as exc:
    if exc.code == 404:
        print("INDEX_EXISTS: no")
        print("HTTP_STATUS:", exc.code)
    else:
        print("HTTP_STATUS:", exc.code)
except Exception as exc:
    print("CHECK_ERROR:", type(exc).__name__)
PY
```

It returned `INDEX_EXISTS: no` (`404`). At present there is no index that `own_index` can touch. However, if an index with this name were ever created, `ai-defense-reader` would be able to perform every operation on it (author's notes, item 23-B).

## 2.5 The User Definition

Password hashes are not shown.

```bash
python3 - <<'PY'
import json
import ssl
import urllib.request

context = ssl.create_default_context(
    cafile="/etc/wazuh-indexer/certs/root-ca.pem"
)
context.load_cert_chain(
    certfile="/etc/wazuh-indexer/certs/admin.pem",
    keyfile="/etc/wazuh-indexer/certs/admin-key.pem"
)

url = "https://127.0.0.1:9200/_plugins/_security/api/internalusers/ai-defense-reader"
request = urllib.request.Request(url)

with urllib.request.urlopen(request, context=context, timeout=10) as response:
    data = json.loads(response.read())
    user = data.get("ai-defense-reader", {})
    print("HTTP_STATUS:", response.status)
    print(json.dumps({
        "reserved": user.get("reserved"),
        "backend_roles": user.get("backend_roles", []),
        "attributes": user.get("attributes", {}),
        "description": user.get("description")
    }, indent=2))
PY
```

At build time it was `reserved: false`, `backend_roles` and `attributes` were empty, and `description` was `Read-only access to Wazuh alert indices for AI Defense Manager`.

# Chapter 3: Looking for Where the Audit Log Is Saved

## 3.1 Indices

```bash
python3 - <<'PY'
import json
import ssl
import urllib.request

context = ssl.create_default_context(
    cafile="/etc/wazuh-indexer/certs/root-ca.pem"
)
context.load_cert_chain(
    certfile="/etc/wazuh-indexer/certs/admin.pem",
    keyfile="/etc/wazuh-indexer/certs/admin-key.pem"
)

url = "https://127.0.0.1:9200/_cat/indices?format=json&h=index"
request = urllib.request.Request(url)

with urllib.request.urlopen(request, context=context, timeout=10) as response:
    indices = json.loads(response.read())
    print("HTTP_STATUS:", response.status)
    for item in indices:
        name = item.get("index", "")
        if "audit" in name.lower() or "security" in name.lower():
            print(name)
PY
```

Only `.opendistro_security` (the internal index holding the security configuration) and `wazuh-states-*` (Wazuh state and asset information) appeared. No index has `audit` in its name.

## 3.2 The Running Audit Configuration

```bash
python3 - <<'PY'
import json
import ssl
import urllib.request
import urllib.error

context = ssl.create_default_context(
    cafile="/etc/wazuh-indexer/certs/root-ca.pem"
)
context.load_cert_chain(
    certfile="/etc/wazuh-indexer/certs/admin.pem",
    keyfile="/etc/wazuh-indexer/certs/admin-key.pem"
)

url = "https://127.0.0.1:9200/_plugins/_security/api/audit"
request = urllib.request.Request(url)

try:
    with urllib.request.urlopen(request, context=context, timeout=10) as response:
        data = json.loads(response.read())
        print("HTTP_STATUS:", response.status)
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in ("audit", "config"):
                    print(key + ":")
                    print(json.dumps(value, indent=2))
                elif isinstance(value, (str, int, bool, type(None))):
                    print(f"{key}: {value}")
                else:
                    print(f"{key}: [structured configuration]")
        else:
            print("RESPONSE_TYPE:", type(data).__name__)
except urllib.error.HTTPError as exc:
    print("HTTP_STATUS:", exc.code)
    print("AUDIT_API_READ_FAILED")
except Exception as exc:
    print("CHECK_ERROR:", type(exc).__name__)
PY
```

The running audit configuration matched `audit.yml` on disk (auditing enabled, recording of internal configuration changes enabled, recording of request bodies enabled, sensitive headers excluded from records).

## 3.3 Log Files

```bash
grep -nEi 'audit|compliance|logger|appender|fileName|filePattern' /etc/wazuh-indexer/log4j2.properties
```

```bash
find /var/log/wazuh-indexer -maxdepth 2 -type f -printf '%f  %m  %u:%g\n' 2>/dev/null | sort
```

There is a normal log (`wazuh-cluster.log`) and a JSON-format log (`wazuh-cluster_server.json`), both `640 wazuh-indexer:wazuh-indexer`. There is no file dedicated to auditing.

In the JSON log, count only the number of lines containing relevant words (the text is not shown).

```bash
python3 - <<'PY'
from pathlib import Path

p = Path("/var/log/wazuh-indexer/wazuh-cluster_server.json")
terms = ("audit", "compliance", "ai-defense-reader", "ai_defense_alerts_read")

counts = {term: 0 for term in terms}

with p.open(errors="replace") as f:
    for line in f:
        lower = line.lower()
        for term in terms:
            if term in lower:
                counts[term] += 1

print("FILE:", p.name)
for term, count in counts.items():
    print(f"{term}: {count}")
PY
```

| Word | Lines |
|---|---:|
| `audit` | 0 |
| `compliance` | 0 |
| `ai-defense-reader` | 3 |
| `ai_defense_alerts_read` | 3 |

## 3.4 What Are Those Three Lines?

Extract only metadata such as time and level.

```bash
python3 - <<'PY'
import json
from pathlib import Path

p = Path("/var/log/wazuh-indexer/wazuh-cluster_server.json")
terms = ("ai-defense-reader", "ai_defense_alerts_read")

with p.open(errors="replace") as f:
    for line in f:
        if not any(term in line.lower() for term in terms):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        print({
            "timestamp": obj.get("@timestamp") or obj.get("timestamp"),
            "level": obj.get("log.level") or obj.get("level"),
            "logger": obj.get("log.logger") or obj.get("logger"),
            "event_dataset": obj.get("event.dataset"),
        })
PY
```

```bash
python3 - <<'PY'
import json
from pathlib import Path

p = Path("/var/log/wazuh-indexer/wazuh-cluster_server.json")
terms = ("ai-defense-reader", "ai_defense_alerts_read")

with p.open(errors="replace") as f:
    for line in f:
        if not any(term in line.lower() for term in terms):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        print("TOP_LEVEL_KEYS:", sorted(obj.keys()))

        for key in ("log", "event", "error", "opensearch"):
            value = obj.get(key)
            if isinstance(value, dict):
                print(f"{key.upper()}_KEYS:", sorted(value.keys()))
        print("---")
PY
```

```bash
python3 - <<'PY'
import json
from pathlib import Path
from collections import Counter

p = Path("/var/log/wazuh-indexer/wazuh-cluster_server.json")
terms = ("ai-defense-reader", "ai_defense_alerts_read")
counts = Counter()

with p.open(errors="replace") as f:
    for line in f:
        if not any(term in line.lower() for term in terms):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        counts[(
            obj.get("component", "<missing>"),
            obj.get("type", "<missing>"),
            obj.get("level", "<missing>")
        )] += 1

print("MATCHED_LOG_CATEGORIES:")
for (component, log_type, level), count in sorted(counts.items()):
    print({
        "component": component,
        "type": log_type,
        "level": level,
        "count": count
    })
PY
```

All three lines were logs related to OpenSearch Security's privilege evaluation.

| Component | Level | Count |
|---|---|---:|
| `RestApiPrivilegesEvaluator` | INFO | 1 |
| `PrivilegesEvaluatorImpl` | INFO | 1 |
| `AbstractApiAction` | ERROR | 1 |

## 3.5 Classifying the ERROR Line

Without showing the text, check only for the name of an exception class, words indicating permission denial or authentication failure, and an HTTP status.

```bash
python3 - <<'PY'
import json
import re
from pathlib import Path

p = Path("/var/log/wazuh-indexer/wazuh-cluster_server.json")
terms = ("ai-defense-reader", "ai_defense_alerts_read")

with p.open(errors="replace") as f:
    for line in f:
        if not any(term in line.lower() for term in terms):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        if obj.get("level") != "ERROR":
            continue

        message = obj.get("message", "")
        match = re.search(
            r'([A-Za-z_$][A-Za-z0-9_.$]*(?:Exception|Error))',
            message
        )

        print({
            "timestamp": obj.get("timestamp"),
            "component": obj.get("component"),
            "exception_class": match.group(1) if match else "not_identified"
        })
PY
```

```bash
python3 - <<'PY'
import json
import re
from pathlib import Path

p = Path("/var/log/wazuh-indexer/wazuh-cluster_server.json")
terms = ("ai-defense-reader", "ai_defense_alerts_read")

with p.open(errors="replace") as f:
    for line in f:
        if not any(term in line.lower() for term in terms):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        if obj.get("level") != "ERROR":
            continue

        message = str(obj.get("message", "")).lower()

        flags = {
            "permission_denied": any(x in message for x in (
                "no permissions", "permission denied", "forbidden"
            )),
            "authentication_failure": any(x in message for x in (
                "authentication failed", "unauthorized", "invalid credentials"
            )),
            "resource_not_found": any(x in message for x in (
                "not found", "does not exist"
            )),
            "internal_error": any(x in message for x in (
                "internal server error", "unexpected exception"
            )),
        }

        action = re.search(r'\[(indices:[a-z_/*-]+)\]', message)
        status = re.search(r'\b(401|403|404|500|502|503)\b', message)

        print({
            "timestamp": obj.get("timestamp"),
            "component": obj.get("component"),
            "message_length": len(message),
            "classification_flags": flags,
            "index_action": action.group(1) if action else None,
            "http_status_if_logged": status.group(1) if status else None
        })
PY
```

```bash
python3 - <<'PY'
import json
import re
from pathlib import Path

p = Path("/var/log/wazuh-indexer/wazuh-cluster_server.json")
terms = ("ai-defense-reader", "ai_defense_alerts_read")

with p.open(errors="replace") as f:
    for line in f:
        if not any(term in line.lower() for term in terms):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("level") != "ERROR":
            continue

        message = str(obj.get("message", ""))
        patterns = [
            r'(?i)\b(?:exception|error)\s*:\s*([A-Za-z0-9_.$]+)',
            r'(?i)\bstatus(?:_code)?\s*[=:]\s*(\d{3})',
            r'(?i)\bHTTP\s+(\d{3})\b',
            r'(?i)\b(?:denied|forbidden|unauthorized|bad request)\b',
            r'(?i)\b(?:GET|POST|PUT|DELETE)\s+(/[A-Za-z0-9_./?*-]*)',
        ]

        print("TIMESTAMP:", obj.get("timestamp"))
        for pattern in patterns:
            matches = re.findall(pattern, message)
            print("PATTERN_MATCH:", matches if matches else "none")
PY
```

At build time none of these methods identified the cause of the ERROR (no exception class name, permission denial, authentication failure or HTTP status was found). It may be the record of `ai-defense-reader` getting `403` when trying to read role definitions in Part 22, 3.3, but this has not been confirmed (author's notes, item 23-C).

## 3.6 The Audit Output Method

```bash
grep -nEi 'audit|opensearch\.logs|path\.logs|plugins\.security' /etc/wazuh-indexer/opensearch.yml
```

`opensearch.yml` has no setting for the audit output method (`plugins.security.audit.type`).

```bash
grep -RniE 'plugins\.security\.audit\.type|internal_opensearch|external_opensearch|audit.*type' /etc/wazuh-indexer /usr/share/wazuh-indexer 2>/dev/null | head -80
```

```bash
sed -n '78,105p' /etc/wazuh-indexer/opensearch-security/opensearch.yml.example
```

The example settings file contains `plugins.security.audit.type: internal_opensearch`, which saves into the Indexer. However, this is an example and is not necessarily the actual setting.

Check the settings of the running node.

```bash
python3 - <<'PY'
import json
import ssl
import urllib.request

context = ssl.create_default_context(
    cafile="/etc/wazuh-indexer/certs/root-ca.pem"
)
context.load_cert_chain(
    certfile="/etc/wazuh-indexer/certs/admin.pem",
    keyfile="/etc/wazuh-indexer/certs/admin-key.pem"
)

url = "https://127.0.0.1:9200/_nodes/settings?flat_settings=true&filter_path=nodes.*.settings.plugins.security.audit*"
request = urllib.request.Request(url)

with urllib.request.urlopen(request, context=context, timeout=10) as response:
    data = json.loads(response.read())
    print("HTTP_STATUS:", response.status)
    print(json.dumps(data, indent=2))
PY
```

It returned `HTTP_STATUS: 200` with the content `{}` (no explicit setting).

Check whether the Indexer process's startup arguments include anything related to auditing (not all arguments are shown).

```bash
python3 - <<'PY'
from pathlib import Path

for p in Path("/proc").glob("[0-9]*/cmdline"):
    try:
        raw = p.read_bytes().replace(b"\0", b" ").decode(errors="replace")
    except (PermissionError, FileNotFoundError, ProcessLookupError):
        continue

    if "org.opensearch.bootstrap.OpenSearch" in raw:
        print("PID:", p.parent.name)
        for arg in raw.split():
            if "audit" in arg.lower():
                print("AUDIT_ARGUMENT:", arg)
        print("PROCESS_FOUND")
        break
else:
    print("OPENSEARCH_PROCESS_NOT_FOUND")
PY
```

The process was found, but there were no arguments related to auditing.

## 3.7 Plugins

```bash
/usr/share/wazuh-indexer/bin/opensearch-plugin list
```

Running it as the `wazuh-indexer` user fails because `/etc/default/wazuh-indexer` cannot be read, so run it as root. We confirmed that `opensearch-security` (the plugin that provides auditing) is installed.

# Closing Notes

The results of the investigation in Part 23 are as follows.

| Item | Result |
|---|---|
| `ai_defense_alerts_read` | Only `read` on `wazuh-alerts-4.x-*` (appropriate) |
| `own_index` | No index with the same name, so no effect for now |
| Definition of `ai-defense-reader` | Not reserved, no backend roles |
| Audit settings | Enabled (internal configuration changes and request bodies are also recorded) |
| Audit output method and location | No explicit setting. The location is **not yet determined** |
| One ERROR in the JSON log | Cause **not identified** |

Where the audit log is saved is tracked down in Part 24 of Volume 2, and it is made savable in Parts 25–27. The cause of the ERROR remains unidentified (author's notes, item 23-C).

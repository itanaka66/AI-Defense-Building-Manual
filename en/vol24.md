---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 2"
subtitle: "Part 24: Finding Out Why the Audit Log Is Not Saved"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 24 of Volume 2 of the "AI Autonomous Cyber Defense System Build Manual". In Part 23 of Volume 1, we found that the security audit log of Wazuh Indexer (OpenSearch) is "enabled", yet no place where it is saved could be found. Here we find out why, **using reads only**, without changing any settings.

The investigation has three stages.

1. Use the administrator API to check the audit settings, indices, Data Streams and cluster settings
2. Use `javap` (a tool that disassembles Java classes) from the JDK bundled with the Indexer to read the Security plugin's code and find out how the audit log's output destination (Sink) is chosen
3. Connect to the running Indexer's JVM with `jcmd` and check which classes are loaded (read-only)

The conclusions are as follows.

- The audit log's output destination is chosen by the setting `plugins.security.audit.type`. **This setting has no default value**
- Without it, the main output destination (default Sink) is not created, and the mechanism that distributes audit messages (the router) is disabled
- When the router is disabled, **audit events are saved nowhere**, even though the audit API shows `enabled: true`
- In this environment, the output destination was not specified anywhere: not in the configuration files, the cluster settings, the startup arguments or the environment variables

## About Volume 2

Volume 2 starts with this book. In Volume 1 (Parts 1–23), we built a defense foundation centered on Wazuh and AI analysis with the AI Defense Manager and the relay API (Relay), and at the end of Volume 1 (Part 23) we found that the Wazuh Indexer audit log appeared not to be saved anywhere. In Volume 2, we get this audit log working and fix a Collector stop found along the way.

| Part | Contents |
|---|---|
| Part 24 | Find out in the code why the audit log is not saved |
| Part 25 | Set where the audit log is saved |
| Part 26 | Do not record request bodies in the audit log |
| Part 27 | Confirm that the audit log is being saved |
| Part 28 | Check the Collector and find why it stopped |
| Part 29 | Restart the Collector without missing any events |
| Part 30 | Keep the Collector from stopping for the same reason |

This volume assumes the same environment as the procedures in Volume 1 (Proxmox, VM 220 security-core, LXC 109 PostgreSQL and so on). For adapting it to ordinary PCs, see "Building on Ordinary PCs" in Part 1 of Volume 1.

## Downloading the Scripts

The scripts used in this book can be downloaded from:

https://github.com/itanaka66/AI-Defense-Building-Manual/releases

## Volumes and Parts

Because the build records are long, this manual is divided into the following four volumes. Part numbers run continuously across volumes.

| Volume | Parts | Main topics |
|---|---|---|
| Volume 1 | Parts 1–23 | Defense foundation (Wazuh, Collector, PostgreSQL, monitoring), AI Defense Manager, a search user for Wazuh, the relay API (Relay), AI analysis and its protection, checks |
| Volume 2 | Parts 24–30 | Enabling and verifying the Wazuh Indexer audit log; checking, recovering and preventing recurrence for the Collector |
| Volume 3 | Parts 31–44 | Handling log switching and recovering missing events, monitoring with Prometheus and testing the rules, checking PostgreSQL, backups (logical, LXC, ZFS snapshots) and restore testing, the TrueNAS destination, handling failures after a reboot |
| Volume 4 | Parts 45–71 | Safe input and output for LLM analysis (allowlists, masking, approval policy), integration with the Relay, API token authentication, checking errors and logs, detecting log tampering (FSS), repairing Wazuh local rules, AI defense agents |

**Volume 1**

| Part | Title |
|---|---|
| Part 1 | Building the Defense Foundation and Monitoring with Wazuh |
| Part 2 | Safely Monitoring PostgreSQL Logs and Correlation Detection |
| Part 3 | Building the Alert-Storage Collector |
| Part 4 | Auditing the Collector and Developing a Hardened Version |
| Part 5 | Deploying the Hardened Collector to Production |
| Part 6 | Verifying Data Integrity and Auditing Operations |
| Part 7 | Finishing the Collector's Fault Tolerance |
| Part 8 | Building the Integrated Monitoring Platform |
| Part 9 | Recovering from a Collector Stop and Checking Operations |
| Part 10 | Handling a Disk Failure and Preparing the AI Defense Manager |
| Part 11 | Laying the Groundwork for the AI Defense Manager |
| Part 12 | Investigating the AI Analysis Service and Wazuh Integration |
| Part 13 | A Read-Only User for Wazuh Indexer |
| Part 14 | Building the Alert Relay API (Relay) |
| Part 15 | Passing the Relay Connection Details Safely to VM 230 |
| Part 16 | Connecting Wazuh Alerts to AI Analysis |
| Part 17 | Running the AI Defense Manager as a Service and Its Startup Order |
| Part 18 | Keeping the Analysis History in SQLite |
| Part 19 | Minimizing the Information Passed to the LLM |
| Part 20 | Fixing Confidence Scores and Protecting Stored Data |
| Part 21 | Switching SSH on VM 230 to Public-Key Authentication |
| Part 22 | Checking the Relay and Its Connection Details |
| Part 23 | Investigating Indexer Permissions and the Audit Log |

**Volume 2**

| Part | Title |
|---|---|
| Part 24 | Finding Out Why the Audit Log Is Not Saved |
| Part 25 | Setting Where the Audit Log Is Saved |
| Part 26 | Not Recording Request Bodies in the Audit Log |
| Part 27 | Confirming That the Audit Log Is Saved |
| Part 28 | Checking the Collector and Why It Stopped |
| Part 29 | Restarting the Collector Without Missing Any Events |
| Part 30 | Keeping the Collector from Stopping for the Same Reason |

**Volume 3**

| Part | Title |
|---|---|
| Part 31 | Why the Collector Cannot Read After Log Switching, and the Fix |
| Part 32 | Confirming an Actual Switch and Recovering Missing Events |
| Part 33 | Monitoring the Collector's State with Prometheus |
| Part 34 | Monitoring the Wazuh Platform's State with Prometheus |
| Part 35 | Testing the Alert Rules and Checking in Production |
| Part 36 | Checking PostgreSQL |
| Part 37 | Backing Up PostgreSQL and Testing a Restore |
| Part 38 | Using TrueNAS as the Backup Destination |
| Part 39 | Registering the Destination and Preparing Scheduled Backups |
| Part 40 | Completing the PostgreSQL Logical Backup |
| Part 41 | Backing Up LXC 109 and Testing an Isolated Restore |
| Part 42 | Protecting the Backups and TrueNAS Snapshots |
| Part 43 | Backup Failures After a Reboot and the Recovery |
| Part 44 | Comparing the Restored Databases with Production |

**Volume 4**

| Part | Title |
|---|---|
| Part 45 | Preparing for LLM Analysis and Repairing the Wazuh Configuration File |
| Part 46 | Classifying Alerts and Deciding Which Fields to Pass to the LLM |
| Part 47 | Examining the Existing AI Defense Manager Implementation |
| Part 48 | Narrowing the Wazuh Event Conversion to Seven Fields |
| Part 49 | Narrowing the Fields Returned by the Relay to Seven |
| Part 50 | Deploying the New Code and a Static Address for VM 230 |
| Part 51 | Verifying TLS and Authentication from VM 230 to the Relay |
| Part 52 | Fetching Real Alerts and Fixing the Relay's 502 |
| Part 53 | Checking the Flow from Analysis to Storage |
| Part 54 | Masking LLM Output and the Approval Policy |
| Part 55 | Integration Checks and Preparing for High Request Volumes |
| Part 56 | Reviewing and Designing API Authentication |
| Part 57 | Building Token Authentication for the API |
| Part 58 | Hardening Token Handling and the CLI |
| Part 59 | Putting API Authentication into Production |
| Part 60 | Keeping Error Responses and Logs from Leaking Information |
| Part 61 | Checking Logs for Secrets and Capping the Journal Size |
| Part 62 | Creating FSS Keys to Guard Against Log Tampering |
| Part 63 | Moving the FSS Verification Key to the Proxmox Host |
| Part 64 | Running and Checking FSS Sealing |
| Part 65 | Checking FSS from Another Host (VM 240) |
| Part 66 | Automating FSS Verification Every 15 Minutes |
| Part 67 | Finding the Breakage in Wazuh's Local Rules |
| Part 68 | Testing the Fixed Rules in an Isolated Environment |
| Part 69 | Putting the Fixed Rules into Production |
| Part 70 | Starting to Build the AI Defense Agents |
| Part 71 | Correlation, Orchestration and Defense Decision Agents |

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **security-core VM 220 (root)**.
- The administrator certificate (`admin.pem`, `admin-key.pem`) is used only to make read queries to the Indexer, and its contents are not shown.
- The output of `javap` is very long, so this book gives only the key points of the results.

# Chapter 1: Checking Through the API

## 1.1 The List of Indices

```bash
python3 - <<'PY'
import json
import ssl
import urllib.request

ctx = ssl.create_default_context(cafile="/etc/wazuh-indexer/certs/root-ca.pem")
ctx.load_cert_chain(
    certfile="/etc/wazuh-indexer/certs/admin.pem",
    keyfile="/etc/wazuh-indexer/certs/admin-key.pem"
)

url = (
    "https://127.0.0.1:9200/_cat/indices"
    "?format=json&h=index,health,status,docs.count,store.size&s=index"
)
req = urllib.request.Request(url)

with urllib.request.urlopen(req, context=ctx, timeout=10) as res:
    indices = json.loads(res.read())
    print("HTTP_STATUS:", res.status)
    for item in indices:
        name = item.get("index", "")
        if any(word in name.lower() for word in ("audit", "security", "compliance")):
            print(json.dumps(item, ensure_ascii=False))
PY
```

There were no indices for the audit log, such as `auditlog6` or `auditlog6-YYYY.MM.dd`.

## 1.2 The Audit Settings

```bash
python3 - <<'PY'
import json
import ssl
import urllib.request

ctx = ssl.create_default_context(cafile="/etc/wazuh-indexer/certs/root-ca.pem")
ctx.load_cert_chain(
    certfile="/etc/wazuh-indexer/certs/admin.pem",
    keyfile="/etc/wazuh-indexer/certs/admin-key.pem"
)

url = "https://127.0.0.1:9200/_plugins/_security/api/audit"
req = urllib.request.Request(url)

with urllib.request.urlopen(req, context=ctx, timeout=10) as res:
    data = json.loads(res.read())
    audit = data.get("audit", {})
    print("HTTP_STATUS:", res.status)
    for key in (
        "enabled",
        "enable_rest",
        "enable_transport",
        "log_request_body",
        "resolve_indices",
        "disabled_rest_categories",
        "disabled_transport_categories",
    ):
        if key in audit:
            print(f"{key}: {json.dumps(audit[key], ensure_ascii=False)}")
    print("OTHER_TOP_LEVEL_KEYS:", sorted(k for k in data if k not in ("audit", "_readonly")))
PY
```

It returned `HTTP_STATUS: 200`, but the settings are inside `config`, so this program did not show the values. Look inside `config`.

```bash
python3 - <<'PY'
import json
import ssl
import urllib.request

ctx = ssl.create_default_context(cafile="/etc/wazuh-indexer/certs/root-ca.pem")
ctx.load_cert_chain(
    certfile="/etc/wazuh-indexer/certs/admin.pem",
    keyfile="/etc/wazuh-indexer/certs/admin-key.pem"
)

req = urllib.request.Request(
    "https://127.0.0.1:9200/_plugins/_security/api/audit"
)

with urllib.request.urlopen(req, context=ctx, timeout=10) as res:
    data = json.loads(res.read())
    config = data.get("config", {})
    print("HTTP_STATUS:", res.status)
    print("CONFIG_TYPE:", type(config).__name__)
    if isinstance(config, dict):
        for key, value in config.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for subkey, subvalue in value.items():
                    if any(word in subkey.lower() for word in ("index", "type", "enabled", "log", "audit")):
                        print(f"  {subkey}: {json.dumps(subvalue, ensure_ascii=False)}")
            elif any(word in key.lower() for word in ("index", "type", "enabled", "log", "audit")):
                print(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    else:
        print("CONFIG_VALUE_TYPE:", type(config).__name__)
PY
```

Auditing is enabled, and `log_request_body` (recording request bodies) was `true`.

## 1.3 All Indices

```bash
python3 - <<'PY'
import json
import ssl
import urllib.request

ctx = ssl.create_default_context(cafile="/etc/wazuh-indexer/certs/root-ca.pem")
ctx.load_cert_chain(
    certfile="/etc/wazuh-indexer/certs/admin.pem",
    keyfile="/etc/wazuh-indexer/certs/admin-key.pem"
)

url = "https://127.0.0.1:9200/_cat/indices?format=json&h=index,docs.count,store.size&s=index"
req = urllib.request.Request(url)

with urllib.request.urlopen(req, context=ctx, timeout=10) as res:
    indices = json.loads(res.read())
    print("HTTP_STATUS:", res.status)
    print("TOTAL_INDICES:", len(indices))
    for item in indices:
        name = item.get("index", "")
        if name.startswith(".") or any(
            word in name.lower()
            for word in ("audit", "security", "compliance", "log")
        ):
            print(json.dumps(item, ensure_ascii=False))
PY
```

Among all 25 indices, none could be identified as belonging to the audit log.

```bash
journalctl -u wazuh-indexer --since "2026-11-20 00:00:00" --no-pager -o cat | grep -Ei 'audit|compliance|auditlog|opensearch.security.audit|security audit' | sed -E 's/(password|token|authorization)([=: ]+)[^ ]+/\1\2[REDACTED]/Ig' | tail -n 40
```

The Indexer's log had no records of audit initialization or errors either.

## 1.4 Every Item of the Audit Settings

```bash
python3 - <<'PY'
import json
import ssl
import urllib.request

ctx = ssl.create_default_context(cafile="/etc/wazuh-indexer/certs/root-ca.pem")
ctx.load_cert_chain(
    certfile="/etc/wazuh-indexer/certs/admin.pem",
    keyfile="/etc/wazuh-indexer/certs/admin-key.pem"
)

req = urllib.request.Request(
    "https://127.0.0.1:9200/_plugins/_security/api/audit"
)

with urllib.request.urlopen(req, context=ctx, timeout=10) as res:
    data = json.loads(res.read())
    print("HTTP_STATUS:", res.status)

    def show_keys(obj, prefix=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                path = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    print(path + ":")
                    show_keys(value, path)
                else:
                    print(path, "=", json.dumps(value, ensure_ascii=False))
        else:
            print("CONFIG_TYPE:", type(obj).__name__)

    show_keys(data.get("config", {}))
PY
```

| Item | Value |
|---|---|
| Auditing overall | Enabled |
| REST and Transport auditing | Enabled |
| Categories not recorded | `AUTHENTICATED`, `GRANTED_PRIVILEGES` |
| `compliance.read_metadata_only`, `write_metadata_only` | `true` |

None of the items decides the output destination (Sink).

# Chapter 2: Reading the Security Plugin's Code

## 2.1 The Plugin Files

```bash
grep -RniE 'auditlog6|internal_opensearch|audit.*index|index.*audit' /usr/share/wazuh-indexer/plugins/opensearch-security 2>/dev/null | head -n 40
```

A plugin is a JAR (ZIP format), so you cannot search inside it with `grep`.

```bash
find /usr/share/wazuh-indexer/plugins/opensearch-security -maxdepth 2 -type f \( -name '*.jar' -o -name 'plugin-descriptor.properties' \) -printf '%f\n' | sort
```

The Security plugin was `opensearch-security-2.19.6.0.jar`. `unzip` is not installed, so without adding packages, list the contents of the JAR with Python's standard library.

```bash
python3 - <<'PY'
from zipfile import ZipFile

path = "/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar"
keywords = ("audit", "compliance", "indexhandler", "indexmanager", "logsink", "logwriter")

with ZipFile(path) as jar:
    matches = [
        name for name in jar.namelist()
        if any(word in name.lower().replace("_", "") for word in keywords)
    ]

print("MATCH_COUNT:", len(matches))
for name in matches[:80]:
    print(name)
PY
```

The following implementations existed as output destinations for the audit log.

| Class | Output destination |
|---|---|
| `InternalOpenSearchSink` | An index inside the Indexer |
| `InternalOpenSearchDataStreamSink` | A Data Stream inside the Indexer |
| `ExternalOpenSearchSink` | An external OpenSearch |
| `Log4JSink` | A log file |
| `KafkaSink`, `WebhookSink` | Kafka, Webhook |
| `DebugSink`, `NoopSink` | For debugging / does nothing |

```bash
python3 - <<'PY'
from zipfile import ZipFile

path = "/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar"
with ZipFile(path) as jar:
    print(jar.read("static_config/static_audit.yml").decode("utf-8"))
PY
```

The standard audit configuration (`static_audit.yml`) contained only `_readonly: []`, which did not reveal the output destination.

## 2.2 Is the Output Destination Specified in a Configuration File?

```bash
grep -RniE 'plugins\.security\.audit\.(type|config\.type|config\.index)|audit\.type|auditlog6|internal_opensearch|external_opensearch' /etc/wazuh-indexer /etc/default 2>/dev/null
```

Only the example settings file (`opensearch.yml.example`) was found.

## 2.3 javap

`javap` is not installed in the OS, but it is in the JDK bundled with the Indexer.

```bash
find /usr/share/wazuh-indexer /usr/lib/jvm -type f \( -name 'jcmd' -o -name 'jstack' -o -name 'javap' \) -print 2>/dev/null | head -n 30
```

## 2.4 The Code That Chooses the Output Destination (SinkProvider)

```bash
 /usr/share/wazuh-indexer/jdk/bin/javap -classpath /usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar -p -c org.opensearch.security.auditlog.sink.SinkProvider
```

- `plugins.security.audit.type` chooses the output destination
- `internal_opensearch` outputs to `InternalOpenSearchSink`, and `internal_opensearch_data_stream` to a Data Stream

```bash
journalctl -u wazuh-indexer --since "2026-11-17 00:00:00" --no-pager -o cat | grep -Ei 'SinkProvider|sink .*created|Default endpoint could not be created|Audit logging unavailable|InternalOpenSearchSink|DebugSink|NoopSink'
```

There were zero log lines about the output destination. Check the configuration file that is actually loaded (values are not shown).

```bash
python3 - <<'PY'
from pathlib import Path

paths = [
    Path("/etc/wazuh-indexer/opensearch.yml"),
    Path("/usr/share/wazuh-indexer/config/opensearch.yml"),
]

for path in paths:
    print(f"\nFILE: {path}")
    print("EXISTS:", path.exists())
    if not path.exists():
        continue

    for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        stripped = line.strip()
        if "plugins.security.audit" in stripped:
            print(f"{number}: {stripped.split(':', 1)[0]}: [VALUE HIDDEN]")
PY
```

The configuration file is `/etc/wazuh-indexer/opensearch.yml`, and it had no `plugins.security.audit.*` settings.

## 2.5 The Setting's Default Value

Look at the part where settings are registered.

```bash
 /usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/lib/*:/usr/share/wazuh-indexer/plugins/opensearch-security/*' -p -c org.opensearch.security.OpenSearchSecurityPlugin | grep -n -B 5 -A 8 'plugins.security.audit.type'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/lib/*:/usr/share/wazuh-indexer/plugins/opensearch-security/*' -p -c org.opensearch.security.OpenSearchSecurityPlugin | sed -n '2400,2455p'
```

`plugins.security.audit.type` is registered with `Setting.simpleString()`, and **no default value is given**. Unless it is written in a configuration file, something like `internal_opensearch` is never chosen automatically.

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/lib/*:/usr/share/wazuh-indexer/plugins/opensearch-security/*' -p -c org.opensearch.security.auditlog.sink.SinkProvider | grep -n -B 12 -A 18 -E 'DebugSink|NoopSink|createSink|Default endpoint could not be created|Audit logging unavailable'
```

- If the output destination type is not specified, `createSink()` returns `null`
- `DebugSink` is not created in place of the main output destination but as a spare (fallback) for when saving fails
- If the main output destination cannot be created, an error is logged and initialization ends

# Chapter 3: Is It Set Through Another Path?

## 3.1 Data Streams

```bash
python3 - <<'PY'
import json
import ssl
import urllib.request
import urllib.error

ctx = ssl.create_default_context(cafile="/etc/wazuh-indexer/certs/root-ca.pem")
ctx.load_cert_chain(
    certfile="/etc/wazuh-indexer/certs/admin.pem",
    keyfile="/etc/wazuh-indexer/certs/admin-key.pem"
)

for path in ("/_data_stream", "/_cat/data_streams?format=json"):
    req = urllib.request.Request("https://127.0.0.1:9200" + path)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            data = json.loads(r.read())
            if path == "/_data_stream":
                names = [x.get("name") for x in data.get("data_streams", [])]
            else:
                names = [x.get("name") for x in data]
            print(path, "HTTP", r.status)
            print("DATA_STREAM_NAMES:", names)
    except urllib.error.HTTPError as e:
        print(path, "HTTP", e.code)
    except Exception as e:
        print(path, "ERROR:", type(e).__name__)
PY
```

`/_data_stream` returned `HTTP 200` with zero Data Streams (`_cat/data_streams` returned `400`, but the former shows that there are none).

## 3.2 Startup Arguments and Environment Variables

```bash
pid=$(systemctl show wazuh-indexer -p MainPID --value); if [ "$pid" -gt 0 ]; then tr '\0' '\n' < "/proc/$pid/cmdline" | grep -Ei 'audit|opensearch.yml|config' | sed -E 's/(password|token|secret)([^=]*)=.*/\1\2=[REDACTED]/I'; else echo "Indexer PID not found"; fi
```

For environment variables, only the names are shown (the values are hidden).

```bash
pid=$(systemctl show wazuh-indexer -p MainPID --value); if [ "$pid" -gt 0 ]; then tr '\0' '\n' < "/proc/$pid/environ" | grep -Ei 'audit|opensearch|config' | sed -E 's/=.*/=[VALUE HIDDEN]/'; else echo "Indexer PID not found"; fi
```

Neither specified an audit output destination.

## 3.3 Cluster Settings

Search the persistent settings, transient settings and default values for anything containing `plugins.security.audit`.

```bash
python3 - <<'PY'
import json
import ssl
import urllib.request

ctx = ssl.create_default_context(cafile="/etc/wazuh-indexer/certs/root-ca.pem")
ctx.load_cert_chain(
    certfile="/etc/wazuh-indexer/certs/admin.pem",
    keyfile="/etc/wazuh-indexer/certs/admin-key.pem"
)

url = "https://127.0.0.1:9200/_cluster/settings?include_defaults=true&flat_settings=true"
req = urllib.request.Request(url)

with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
    data = json.loads(r.read())

for section in ("persistent", "transient", "defaults"):
    settings = data.get(section, {})
    matches = {
        k: ("[VALUE HIDDEN]" if any(x in k.lower() for x in ("password", "token", "secret")) else v)
        for k, v in settings.items()
        if "plugins.security.audit" in k.lower()
    }
    print(section.upper(), json.dumps(matches, ensure_ascii=False))
PY
```

None of them specified it.

## 3.4 When the Output Destination Is null

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/lib/*:/usr/share/wazuh-indexer/plugins/opensearch-security/*' -p -c org.opensearch.security.auditlog.sink.SinkProvider | sed -n '251,380p'
```

`createSink()` first sets the output destination to `null`, and returns as is if the type is `null`. Also check the other way of specifying it (`plugins.security.audit.endpoints`).

```bash
grep -nEi 'plugins\.security\.audit\.(type|endpoints)|audit.*(type|endpoint)' /etc/wazuh-indexer/opensearch.yml /etc/wazuh-indexer/opensearch-security/opensearch.yml 2>/dev/null
```

There were zero.

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/lib/*:/usr/share/wazuh-indexer/plugins/opensearch-security/*' -p -c org.opensearch.security.auditlog.sink.SinkProvider | sed -n '1,115p'
```

The initialization of `SinkProvider` is as follows.

1. If no fallback is specified, create a `DebugSink`
2. Create the main output destination (default) from `plugins.security.audit.type`
3. If the main output destination cannot be created, log an error and end initialization

```bash
journalctl -u wazuh-indexer --since "2026-11-17 00:00:00" --no-pager -o cat | grep -Ei 'AuditLog|AuditLogger|AuditLogSink|SinkProvider|auditlog|audit logger|audit logging'
```

There were zero log lines about auditing.

# Chapter 4: How Events Are Distributed

## 4.1 The Audit Classes

`jar` is not installed in the OS, so use `jar` from the Indexer's JDK.

```bash
/usr/share/wazuh-indexer/jdk/bin/jar tf /usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar | grep -Ei 'audit.*(logger|log|sink)|Audit.*(Logger|Log|Sink)|AuditLog'
```

`AuditLogImpl` receives audit events, and `AuditMessageRouter` distributes them to the output destinations.

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/lib/*:/usr/share/wazuh-indexer/plugins/opensearch-security/*' -p org.opensearch.security.auditlog.impl.AuditLogImpl
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/lib/*:/usr/share/wazuh-indexer/plugins/opensearch-security/*' -p -c org.opensearch.security.auditlog.impl.AuditLogImpl | grep -n -A 45 -B 8 -E 'enableRoutes|save\('
```

Decoding the bytecode, the saving process takes the following form (rewritten in Java).

```text
protected void save(AuditMessage message) {
    if (enabled) {
        messageRouter.route(message);
    }
}
```

## 4.2 The Router

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/lib/*:/usr/share/wazuh-indexer/plugins/opensearch-security/*' -p -c org.opensearch.security.auditlog.routing.AuditMessageRouter
```

- If the main output destination is `null`, the router is disabled (`isEnabled()` is false)
- If an event arrives while it is disabled, it logs the error `#route(AuditMessage) called but message router is disabled` and stops

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/lib/*:/usr/share/wazuh-indexer/plugins/opensearch-security/*' -p -c org.opensearch.security.auditlog.impl.AuditLogImpl | sed -n '1,110p'
```

`setConfig()` had the following form.

```text
enabled = auditConfig.isEnabled() && messageRouterEnabled;
```

In other words, even with `enabled: true` in the audit API, if there is no main output destination, `messageRouterEnabled` becomes false and auditing does not actually work.

## 4.3 Messages at Startup

```bash
journalctl -u wazuh-indexer --since "2026-11-17 00:00:00" --no-pager -o cat | grep -Ei 'Message routing enabled|No default storage available|Default endpoint could not be created|audit log may not work properly|message router is disabled'
```

```bash
grep -RniE 'Message routing enabled|No default storage available|Default endpoint could not be created|message router is disabled|audit log may not work properly' /var/log/wazuh-indexer/ 2>/dev/null
```

There were no matching messages in either the journal or the log files.

# Chapter 5: Looking at the Running JVM

## 5.1 Startup Time

```bash
ps -eo pid,lstart,etime,args | grep '[o]rg.opensearch.bootstrap.OpenSearch'
```

At build time the Indexer was PID 1238 and had started at 06:56:11 on November 20, 2026 (the startup is within the period examined).

## 5.2 jcmd

`jcmd` is a tool that connects to a running JVM and obtains information. Only read commands are used here. Replace the PID with the one in your environment.

```bash
/usr/share/wazuh-indexer/jdk/bin/jcmd 1238 VM.version
```

```bash
/usr/share/wazuh-indexer/jdk/bin/jcmd 1238 help
```

At build time this was OpenJDK 21.0.11. Check the loaded audit classes.

```bash
/usr/share/wazuh-indexer/jdk/bin/jcmd 1238 VM.classes | grep -Ei 'org\.opensearch\.security\.auditlog|SinkProvider|AuditMessageRouter'
```

`AuditLogImpl`, `AuditMessageRouter`, `SinkProvider`, `DebugSink`, `InternalOpenSearchSink`, `ExternalOpenSearchSink` and others were loaded. However, a class being loaded is different from an output destination actually being chosen and working.

# Closing Notes

What Part 24 found is as follows.

| Item | Result |
|---|---|
| Audit API settings | Enabled (`log_request_body: true`) |
| `plugins.security.audit.type` | Not specified anywhere (and no default value) |
| Main output destination (default Sink) | Not created |
| Router | Disabled |
| Audit log | Considered **not to be saved** |

In the next part, we set `plugins.security.audit.type` so that the audit log is saved inside the Indexer, and stop recording request bodies.

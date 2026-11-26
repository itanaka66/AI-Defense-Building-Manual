---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 2"
subtitle: "Omnibus Edition: Parts 24–30"
author: "Isamu Tanaka"
lang: en-US
---

# About Volume 2

This book collects Volume 2 (Parts 24–30) of the "AI Autonomous Cyber Defense System Build Manual" in a single omnibus edition. On top of the environment built in Volume 1, it finds in the code why the Wazuh Indexer audit log was not being saved and makes it savable, then recovers the Collector that was found stopped during those checks without missing any events, and fixes it so that it does not stop for the same reason again.

It assumes the same environment as Volume 1 (Proxmox, VM 220 security-core, LXC 109 PostgreSQL and so on). For the underlying configuration and procedures, see Volume 1.

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


# Part 24: Finding Out Why the Audit Log Is Not Saved
## Introduction

### About This Book

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

### About Volume 2

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


### Volumes and Parts

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

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **security-core VM 220 (root)**.
- The administrator certificate (`admin.pem`, `admin-key.pem`) is used only to make read queries to the Indexer, and its contents are not shown.
- The output of `javap` is very long, so this book gives only the key points of the results.

## Chapter 1: Checking Through the API

### 1.1 The List of Indices

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

### 1.2 The Audit Settings

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

### 1.3 All Indices

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

### 1.4 Every Item of the Audit Settings

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

## Chapter 2: Reading the Security Plugin's Code

### 2.1 The Plugin Files

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

### 2.2 Is the Output Destination Specified in a Configuration File?

```bash
grep -RniE 'plugins\.security\.audit\.(type|config\.type|config\.index)|audit\.type|auditlog6|internal_opensearch|external_opensearch' /etc/wazuh-indexer /etc/default 2>/dev/null
```

Only the example settings file (`opensearch.yml.example`) was found.

### 2.3 javap

`javap` is not installed in the OS, but it is in the JDK bundled with the Indexer.

```bash
find /usr/share/wazuh-indexer /usr/lib/jvm -type f \( -name 'jcmd' -o -name 'jstack' -o -name 'javap' \) -print 2>/dev/null | head -n 30
```

### 2.4 The Code That Chooses the Output Destination (SinkProvider)

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

### 2.5 The Setting's Default Value

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

## Chapter 3: Is It Set Through Another Path?

### 3.1 Data Streams

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

### 3.2 Startup Arguments and Environment Variables

```bash
pid=$(systemctl show wazuh-indexer -p MainPID --value); if [ "$pid" -gt 0 ]; then tr '\0' '\n' < "/proc/$pid/cmdline" | grep -Ei 'audit|opensearch.yml|config' | sed -E 's/(password|token|secret)([^=]*)=.*/\1\2=[REDACTED]/I'; else echo "Indexer PID not found"; fi
```

For environment variables, only the names are shown (the values are hidden).

```bash
pid=$(systemctl show wazuh-indexer -p MainPID --value); if [ "$pid" -gt 0 ]; then tr '\0' '\n' < "/proc/$pid/environ" | grep -Ei 'audit|opensearch|config' | sed -E 's/=.*/=[VALUE HIDDEN]/'; else echo "Indexer PID not found"; fi
```

Neither specified an audit output destination.

### 3.3 Cluster Settings

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

### 3.4 When the Output Destination Is null

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

## Chapter 4: How Events Are Distributed

### 4.1 The Audit Classes

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

### 4.2 The Router

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

### 4.3 Messages at Startup

```bash
journalctl -u wazuh-indexer --since "2026-11-17 00:00:00" --no-pager -o cat | grep -Ei 'Message routing enabled|No default storage available|Default endpoint could not be created|audit log may not work properly|message router is disabled'
```

```bash
grep -RniE 'Message routing enabled|No default storage available|Default endpoint could not be created|message router is disabled|audit log may not work properly' /var/log/wazuh-indexer/ 2>/dev/null
```

There were no matching messages in either the journal or the log files.

## Chapter 5: Looking at the Running JVM

### 5.1 Startup Time

```bash
ps -eo pid,lstart,etime,args | grep '[o]rg.opensearch.bootstrap.OpenSearch'
```

At build time the Indexer was PID 1238 and had started at 06:56:11 on November 20, 2026 (the startup is within the period examined).

### 5.2 jcmd

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

## Closing Notes

What Part 24 found is as follows.

| Item | Result |
|---|---|
| Audit API settings | Enabled (`log_request_body: true`) |
| `plugins.security.audit.type` | Not specified anywhere (and no default value) |
| Main output destination (default Sink) | Not created |
| Router | Disabled |
| Audit log | Considered **not to be saved** |

In the next part, we set `plugins.security.audit.type` so that the audit log is saved inside the Indexer, and stop recording request bodies.

# Part 25: Setting Where the Audit Log Is Saved
## Introduction

### About This Book

This is Part 25 of Volume 2 of the "AI Autonomous Cyber Defense System Build Manual". In Part 24 we found that the audit log was not being saved because its output destination (`plugins.security.audit.type`) was not set. Here we do the following.

1. Confirm in the code where, and what, the candidate output destination (`internal_opensearch`) saves
2. Confirm where audit messages go when saving fails
3. Confirm which items are recorded (request bodies, headers, categories)
4. Add two lines to the configuration file and restart the Indexer

The conditions to keep are as follows.

- Keep the audit log separate from the Wazuh alert indices
- Do not give `ai-defense-reader` permission to read the audit log
- Do not stop Wazuh alert collection or the Relay (except during the restart)
- Do not record request bodies (because secrets could be mixed in)
- Take a backup before changing anything

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **security-core VM 220 (root)**.
- The output of `javap` is long, so only the key points of the results are given.
- Two of the build conversations, (109) and (112), were not available. The decisions made in between (such as approving the configuration policy) are written to the extent that they can be read from the surrounding conversations.

## Chapter 1: Checking the Configuration File

The setting planned for use is the following line (it is finalized in 3.4).

```text
plugins.security.audit.type: internal_opensearch
```

```bash
stat -c '%n | owner=%U:%G | mode=%a | size=%s bytes | modified=%y' /etc/wazuh-indexer/opensearch.yml
```

At build time the file was `wazuh-indexer:wazuh-indexer` with `660`, 2152 bytes. These permissions are not changed.

```bash
sed -n '1,240p' /etc/wazuh-indexer/opensearch.yml
```

There is no audit output destination specified, and the Indexer listens only on `127.0.0.1`. The TLS, authentication and network settings are not touched.

## Chapter 2: How internal_opensearch Works

### 2.1 The Target Index

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c org.opensearch.security.auditlog.sink.InternalOpenSearchSink | grep -n -B 5 -A 8 -Ei 'auditlog6|index|createIndex|mapping'
```

In Security plugin 2.19.6.0, `internal_opensearch` saves into a per-day **`security-auditlog-YYYY.MM.dd`** if no index name is specified (not `auditlog6`).

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c org.opensearch.security.auditlog.sink.AbstractInternalOpenSearchSink
```

- Audit events are written into the Indexer with `Client.prepareIndex()`
- The contents of the audit message (`AuditMessage.getAsMap()`) are saved as they are
- If writing fails, `Unable to index audit log` appears in the error log

### 2.2 When Saving Fails

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c org.opensearch.security.auditlog.sink.AuditLogSink
```

`AuditLogSink.store()` processes in the following order.

1. Save to the main output destination
2. If that fails, save to the spare (fallback) output destination
3. If that also fails, write the full audit message to `System.err` (standard error)

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c org.opensearch.security.auditlog.sink.DebugSink
```

The spare `DebugSink` writes the full audit message to Log4j at `INFO`.

```bash
grep -nEi 'rootLogger|logger\..*(auditlog|DebugSink)|appender|fileName|filePattern|console' /etc/wazuh-indexer/log4j2.properties
```

| Item | Current setting |
|---|---|
| rootLogger | `INFO` |
| Console output | Enabled |
| File output | Enabled (`/var/log/wazuh-indexer/`, every 128 MB, up to 2 GB in total) |

In other words, if saving to the main output destination fails, the full audit message may appear in the normal logs.

### 2.3 How the Spare Output Destination Is Chosen

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c org.opensearch.security.auditlog.sink.SinkProvider | grep -n -B 8 -A 15 -E 'FALLBACKSINK_NAME|fallback|DebugSink|createSink'
```

| Spare setting | Behavior |
|---|---|
| None | Creates a `DebugSink` automatically |
| `debug` | Writes the full text to Log4j |
| `noop` | Discards audit messages |

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c org.opensearch.security.auditlog.sink.NoopSink
```

`NoopSink` outputs nothing and returns "success". It prevents leaks into logs, but it hides the fact that audit records were lost, so it is not adopted here (the spare is left at its default).

## Chapter 3: What Is Recorded

### 3.1 Request Bodies and Headers

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c org.opensearch.security.auditlog.impl.AuditMessage
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c org.opensearch.security.auditlog.impl.AuditMessage | grep -n -B 5 -A 35 -E 'addRestHeaders|addRestParams|addPath|addTransportHeaders'
```

- If `log_request_body` is enabled, the body of REST requests is turned into JSON and put in `audit_request_body`
- Only some Security APIs that handle passwords replace the body with `__SENSITIVE__`. Other bodies (search conditions, data being added or updated, etc.) are recorded as they are
- If `exclude_sensitive_headers` is enabled, the `Authorization` header is not recorded

### 3.2 Filter Defaults

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c 'org.opensearch.security.auditlog.config.AuditConfig$Filter'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c 'org.opensearch.security.auditlog.config.AuditConfig$Filter$FilterEntries'
```

- The default value of `log_request_body` is **true**
- The default value of `exclude_sensitive_headers` is true
- `ignore_headers`, `ignore_url_params`, `ignore_requests` and `ignore_users` can exclude things from records using wildcards

### 3.3 Audit Categories

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c 'org.opensearch.security.auditlog.impl.AuditCategory'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p org.opensearch.security.auditlog.impl.AuditLogImpl
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c org.opensearch.security.auditlog.impl.AuditLogImpl | grep -n -A 45 -E 'logFailedLogin|logSucceededLogin|logMissingPrivileges|logGrantedPrivileges|logIndexEvent|logSecurityIndexAttempt|logSSLException'
```

`AuditLogImpl` checks whether auditing is enabled and then leaves creating the event to its parent class `AbstractAuditLog`.

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c org.opensearch.security.auditlog.impl.AbstractAuditLog | grep -n -B 4 -A 35 -E 'logFailedLogin|logSucceededLogin|logMissingPrivileges|logGrantedPrivileges|logIndexEvent|logBadHeaders|logSecurityIndexAttempt|logSSLException|logDocumentRead|logDocumentWritten|logDocumentDeleted'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c org.opensearch.security.auditlog.impl.AbstractAuditLog | grep -oE 'AuditCategory\.[A-Z_]+' | sort -u
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c org.opensearch.security.auditlog.impl.AuditCategory
```

There are 13 categories. The ones especially useful for this system are as follows.

| Category | Meaning |
|---|---|
| `FAILED_LOGIN` | Authentication failure |
| `MISSING_PRIVILEGES` | An operation refused for lack of privileges |
| `BAD_HEADERS` | Invalid headers |
| `OPENDISTRO_SECURITY_INDEX_ATTEMPT` | An attempt to operate on the internal security index |
| `SSL_EXCEPTION` | A TLS exception |
| `INDEX_EVENT` | Index operations |
| `COMPLIANCE_*` | Reading and writing documents; reading and writing internal configuration |

Successful authentication (`AUTHENTICATED`) and granted privileges (`GRANTED_PRIVILEGES`) are excluded from records by the current settings (Part 23 of Volume 1).

### 3.4 The Names of the Setting Keys

First, confirm that there is no router initialization message in the log files, including compressed logs.

```bash
python3 - <<'PY'
from pathlib import Path
import gzip

base = Path("/var/log/wazuh-indexer")
patterns = (
    "Default endpoint could not be created",
    "No default storage available",
    "Message routing enabled",
    "audit log may not work",
    "message router is disabled",
)

count = 0
for path in sorted(base.glob("*server*")):
    try:
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8", errors="replace") as f:
            for line in f:
                if any(p.lower() in line.lower() for p in patterns):
                    print(f"{path.name}: {line.rstrip()}")
                    count += 1
    except (OSError, EOFError):
        pass

print("MATCH_COUNT:", count)
PY
```

```bash
grep -nEi '^[[:space:]]*plugins\.security\.audit\.|^[[:space:]]*opendistro_security\.audit\.' /etc/wazuh-indexer/opensearch.yml
```

```bash
stat -c '%n | owner=%U:%G | mode=%a | size=%s | modified=%y' /etc/wazuh-indexer/opensearch.yml
```

```bash
tail -n 35 /etc/wazuh-indexer/opensearch.yml | nl -ba
```

The settings are added at the end of the file. Check in the code the key for the setting that stops recording request bodies.

```bash
/usr/share/wazuh-indexer/jdk/bin/jar tf /usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar | grep -E 'AuditConfig.*FilterEntries|FilterEntries.*class'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c 'org.opensearch.security.auditlog.config.AuditConfig$Filter$FilterEntries'
```

The old-style key was `opendistro_security.audit.log_request_body`.

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c 'org.opensearch.security.auditlog.config.AuditConfig$Filter' | grep -n -A90 -B8 'from(org.opensearch.common.settings.Settings)'
```

`fromSettingBoolean()` looks at the new-style key first and, if it is absent, the old-style key. Check how the new-style names are formed.

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c 'org.opensearch.security.auditlog.config.AuditConfig$Filter$FilterEntries' | grep -n -A35 -B5 'getKeyWithNamespace'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -v 'org.opensearch.security.auditlog.config.AuditConfig$Filter$FilterEntries' | grep -n -A18 -B3 'BootstrapMethods:'
```

`getKeyWithNamespace()` used the prefix `plugins.security.audit.config.`. The setting that stops recording request bodies is therefore as follows.

```text
plugins.security.audit.config.log_request_body: false
```

The output destination setting is in a different namespace.

```text
plugins.security.audit.type: internal_opensearch
```

## Chapter 4: Setting It and Restarting

### 4.1 The Current Value

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

req = urllib.request.Request("https://127.0.0.1:9200/_plugins/_security/api/audit")
with urllib.request.urlopen(req, context=ctx, timeout=10) as res:
    data = json.load(res)

audit = data.get("config", {}).get("audit", {})
print("audit.enabled:", data.get("config", {}).get("enabled"))
print("audit.log_request_body:", audit.get("log_request_body"))
print("audit.exclude_sensitive_headers:", audit.get("exclude_sensitive_headers"))
print("audit.enable_rest:", audit.get("enable_rest"))
print("audit.enable_transport:", audit.get("enable_transport"))
PY
```

`log_request_body` was `True`.

### 4.2 Backup

```bash
cp -a /etc/wazuh-indexer/opensearch.yml "/etc/wazuh-indexer/opensearch.yml.pre-audit-$(date +%Y%m%d-%H%M%S)"
```

```bash
bash -c 'f=$(ls -1t /etc/wazuh-indexer/opensearch.yml.pre-audit-* | head -n 1); echo "BACKUP: $f"; stat -c "owner=%U:%G mode=%a size=%s" "$f"; cmp -s /etc/wazuh-indexer/opensearch.yml "$f" && echo "CONTENT_MATCH: yes" || echo "CONTENT_MATCH: no"'
```

The backup at build time was `opensearch.yml.pre-audit-20261121-082142`, and it matched the original file.

### 4.3 Adding Two Lines

Confirm that the same keys do not already exist.

```bash
grep -nE '^[[:space:]]*plugins\.security\.audit\.(type|config\.log_request_body):' /etc/wazuh-indexer/opensearch.yml
```

The two lines to add are as follows.

```text
plugins.security.audit.type: internal_opensearch
plugins.security.audit.config.log_request_body: false
```

```bash
printf '\n# AI Defense: audit logging with request-body protection\nplugins.security.audit.type: internal_opensearch\nplugins.security.audit.config.log_request_body: false\n' >> /etc/wazuh-indexer/opensearch.yml
```

Confirm that the difference from the backup is only one comment line and two setting lines. Replace the file name with the name of your own backup.

```bash
diff -u /etc/wazuh-indexer/opensearch.yml.pre-audit-20261121-082142 /etc/wazuh-indexer/opensearch.yml
```

```bash
python3 - <<'PY'
import yaml

path = "/etc/wazuh-indexer/opensearch.yml"
with open(path, encoding="utf-8") as f:
    config = yaml.safe_load(f)

assert config["plugins.security.audit.type"] == "internal_opensearch"
assert config["plugins.security.audit.config.log_request_body"] is False

print("YAML_SYNTAX: OK")
print("AUDIT_TYPE: OK")
print("REQUEST_BODY_LOGGING: disabled")
PY
```

### 4.4 Restarting

Record the state before the restart.

```bash
systemctl show wazuh-indexer -p ActiveState -p SubState -p MainPID -p NRestarts -p ActiveEnterTimestamp
```

During the restart, the Indexer API, Wazuh searches and the Relay are temporarily unavailable.

```bash
systemctl restart wazuh-indexer
```

```bash
systemctl show wazuh-indexer -p ActiveState -p SubState -p MainPID -p NRestarts -p ActiveEnterTimestamp
```

At build time it was `active` and `running`, with the new PID 51059 and `NRestarts=0`.

### 4.5 Was It Applied?

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

req = urllib.request.Request("https://127.0.0.1:9200/_plugins/_security/api/audit")
with urllib.request.urlopen(req, context=ctx, timeout=15) as res:
    data = json.load(res)

config = data.get("config", {})
audit = config.get("audit", {})

print("API: OK")
print("AUDIT_ENABLED:", config.get("enabled"))
print("LOG_REQUEST_BODY:", audit.get("log_request_body"))
print("EXCLUDE_SENSITIVE_HEADERS:", audit.get("exclude_sensitive_headers"))
print("ENABLE_REST:", audit.get("enable_rest"))
print("ENABLE_TRANSPORT:", audit.get("enable_transport"))
PY
```

At build time it still showed `LOG_REQUEST_BODY: True`. The `false` written in the configuration file is not reflected in the settings returned by the audit API. The next part investigates and fixes the reason.

## Closing Notes

In Part 25 we added the following settings to `/etc/wazuh-indexer/opensearch.yml` and restarted the Indexer.

| Setting | Value | Result |
|---|---|---|
| `plugins.security.audit.type` | `internal_opensearch` | The audit log is saved inside the Indexer (`security-auditlog-YYYY.MM.dd`) |
| `plugins.security.audit.config.log_request_body` | `false` | Not yet reflected in the audit API |

The backup is `/etc/wazuh-indexer/opensearch.yml.pre-audit-*`.

# Part 26: Not Recording Request Bodies in the Audit Log
## Introduction

### About This Book

This is Part 26 of Volume 2 of the "AI Autonomous Cyber Defense System Build Manual". In Part 25 we wrote `plugins.security.audit.config.log_request_body: false` in `opensearch.yml` and restarted the Indexer, but the audit API still returned `log_request_body: true`. Here we find the reason in the code, and **set only `log_request_body` to `false` through the audit API (PATCH)**.

The reason turned out to be as follows.

- The audit settings are also stored in the document `audit` in the Indexer's internal index `.opendistro_security` (dynamic configuration)
- At startup, the Indexer uses this document **if it exists**, and builds the settings from `opensearch.yml` **only if it does not**
- In this environment the document `audit` exists, so `log_request_body: false` in `opensearch.yml` is not used

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **security-core VM 220 (root)**.
- The Indexer is accessed with the administrator certificate (`admin.pem`, `admin-key.pem`). The password of the `admin` user is not used.
- The output of `javap` is long, so only the key points of the results are given.

## Chapter 1: Where the Settings Are Read From

### 1.1 Node Settings and the File

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

url = "https://127.0.0.1:9200/_nodes/settings?flat_settings=true"
req = urllib.request.Request(url)

with urllib.request.urlopen(req, context=ctx, timeout=15) as res:
    data = json.load(res)

for node_id, node in data.get("nodes", {}).items():
    settings = node.get("settings", {})
    print("NODE:", node.get("name", node_id))
    for key in sorted(settings):
        if "audit" in key.lower():
            value = settings[key]
            if any(x in key.lower() for x in ("password", "token", "secret", "credential")):
                value = "[REDACTED]"
            print(f"{key} = {value}")
PY
```

None of the audit settings appeared in the node settings API (the fact that they do not appear does not by itself mean they are not loaded).

```bash
grep -nE '^[[:space:]]*plugins\.security\.audit\.(type|config\.log_request_body):' /etc/wazuh-indexer/opensearch.yml && stat -c '%U:%G %a %s' /etc/wazuh-indexer/opensearch.yml
```

The file has the two lines, and its owner and permissions have not changed.

### 1.2 How AuditConfig Is Created

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p 'org.opensearch.security.auditlog.config.AuditConfig'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c 'org.opensearch.security.auditlog.config.AuditConfig' | sed -n '/public static org.opensearch.security.auditlog.config.AuditConfig from(/,/public static java.util.Set/p'
```

`AuditConfig.from(Settings)` builds the audit settings from the node settings (`opensearch.yml`).

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c 'org.opensearch.security.auditlog.impl.AuditLogImpl' | sed -n '/setConfig(/,/enableRoutes(/p'
```

`setConfig()` uses the settings it receives as they are. `AuditLogImpl` does not change the value back to `true`.

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/lib/*:/usr/share/wazuh-indexer/plugins/opensearch-security/*' -p -c org.opensearch.security.OpenSearchSecurityPlugin | grep -n -B 8 -A 12 'AuditLogImpl.setConfig\|setConfig:(Lorg/opensearch/security/auditlog/config/AuditConfig'
```

It is not called directly from `OpenSearchSecurityPlugin`. Look for the classes that handle the configuration.

```bash
/usr/share/wazuh-indexer/jdk/bin/jar tf /usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar | grep -Ei 'Audit|ConfigurationRepository|DynamicConfig|ConfigUpdate'
```

`ConfigurationRepository` loads the dynamic configuration, and `AuditApiAction` is the audit API.

### 1.3 ConfigurationRepository

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c org.opensearch.security.configuration.ConfigurationRepository | grep -n -B 8 -A 12 -Ei 'AuditConfig|auditLog|auditLogImpl|setConfig|onChange'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c org.opensearch.security.configuration.ConfigurationRepository | sed -n '/private void setupAuditConfigurationIfAny/,/private boolean createSecurityIndexIfAbsent/p'
```

`setupAuditConfigurationIfAny()` branches on whether `.opendistro_security` contains an audit configuration document.

| Document | Behavior |
|---|---|
| Exists | Does not call `AuditConfig.from(settings)` (uses the settings in the document) |
| Does not exist | Builds the settings from `opensearch.yml` and uses them |

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c org.opensearch.security.configuration.ConfigurationLoaderSecurity7 | sed -n '/isAuditConfigDocPresentInIndex/,/^[[:space:]]*public/p'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c 'org.opensearch.security.configuration.ConfigurationLoaderSecurity7$2' | grep -n -B 10 -A 18 -Ei 'audit|isAuditConfigDocPresentInIndex|set\(|toConfig|AUDIT'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c 'org.opensearch.security.configuration.ConfigurationLoaderSecurity7$1' | grep -n -B 8 -A 16 -Ei 'audit|isAuditConfigDocPresentInIndex|success|CType|set\('
```

If the document `audit` can be read, `isAuditConfigDocPresentInIndex = true`; otherwise it is set to `false` and the initial settings are built from `opensearch.yml`.

```bash
journalctl -u wazuh-indexer --since "2026-11-21 08:20:00" --no-pager | grep -Ei 'Hot-reloading of audit configuration|Audit configuration settings found|Using configuration with defaults from opensearch settings'
```

The log had no record of which path was taken.

## Chapter 2: Checking Whether the Document Exists

### 2.1 The Administrator Certificate

Connect with the administrator certificate, without using the `admin` user's password (even if it is unknown, it is not reset).

```bash
find /etc/wazuh-indexer -maxdepth 3 -type f \( -iname '*admin*.pem' -o -iname '*root-ca*.pem' -o -iname '*admin*.crt' -o -iname '*admin*.key' \) -printf '%p\n'
```

```bash
openssl x509 -in /etc/wazuh-indexer/certs/admin.pem -noout -subject -issuer -dates -ext extendedKeyUsage
```

At build time the CN was `admin`, valid from November 17, 2026 to November 14, 2036.

### 2.2 The Document audit

Without fetching the document's contents, check only whether it exists.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/.opendistro_security/_doc/audit?filter_path=_index,_id,found'
```

The result at build time was as follows: the document existed.

```text
_index: .opendistro_security
_id: audit
found: true
```

This explains why the change to `opensearch.yml` was not reflected. Note that `audit` in this document was stored not as JSON but as a string in an internal format (940 characters), so no values were extracted from it here. The values are checked through the audit API.

### 2.3 The Values in the Audit API

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/_plugins/_security/api/audit' | python3 -c 'import json,sys; d=json.load(sys.stdin); print("log_request_body =",d["config"]["audit"].get("log_request_body","<not found>"))'
```

It showed `log_request_body = True`. In the API response, the settings are directly under `audit` beneath `config`.

```text
config
 ├─ compliance
 ├─ enabled
 └─ audit
```

## Chapter 3: Changing It Through the Audit API

### 3.1 Checking How to Change It

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c org.opensearch.security.dlic.rest.api.AuditApiAction
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c 'org.opensearch.security.dlic.rest.api.AuditApiAction$2'
```

- The audit API accepts `PUT /_plugins/_security/api/audit/config` and `PATCH /_plugins/_security/api/audit`
- Changes are possible only when reloading of the audit configuration (hot reload) is enabled (it is enabled because the document exists)

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c org.opensearch.security.dlic.rest.api.AuditApiAction | grep -A100 -B10 'processPatchRequest\|lambda\$auditApiRequestHandlers\$2'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c org.opensearch.security.dlic.rest.api.AbstractApiAction | grep -A100 -B10 -E 'processPatchRequest|processPutRequest|processChangeRequest'
```

| Method | Behavior |
|---|---|
| `PUT` | Replaces the whole configuration (not used this time) |
| `PATCH` | Reads the current configuration and applies a JSON Patch (`add`, `replace`, `remove`). Only the changed items are validated |

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c 'org.opensearch.security.dlic.rest.api.AuditApiAction$AuditRequestContentValidator'
```

The whole configuration after the change is also validated. Other settings, such as the categories not recorded for REST and Transport, must remain as they are.

### 3.2 The Current Configuration

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/_plugins/_security/api/audit' | python3 -c 'import json,sys; d=json.load(sys.stdin); a=d["config"]["audit"]; print("log_request_body:",a.get("log_request_body")); print("exclude_sensitive_headers:",a.get("exclude_sensitive_headers")); print("enable_rest:",a.get("enable_rest")); print("enable_transport:",a.get("enable_transport")); print("disabled_rest_categories:",a.get("disabled_rest_categories")); print("disabled_transport_categories:",a.get("disabled_transport_categories")); print("ignore_users_count:",len(a.get("ignore_users",[]))); print("ignore_requests_count:",len(a.get("ignore_requests",[]))); print("ignore_headers_count:",len(a.get("ignore_headers",[]))); print("ignore_url_params_count:",len(a.get("ignore_url_params",[])))'
```

| Item | Current value |
|---|---|
| `log_request_body` | `true` |
| `exclude_sensitive_headers` | `true` |
| `enable_rest`, `enable_transport` | `true` |
| Categories not recorded (REST, Transport) | `AUTHENTICATED`, `GRANTED_PRIVILEGES` |
| `ignore_users` | 1 entry |

Check the location for the JSON Patch (JSON Pointer) and any read-only items.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/_plugins/_security/api/audit' | python3 -c 'import json,sys; d=json.load(sys.stdin); c=d.get("config",{}); print("config_keys:",list(c)); print("audit_is_object:",isinstance(c.get("audit"),dict)); print("audit_pointer_value:",c.get("audit",{}).get("log_request_body")); print("readonly_paths:",d.get("_readonly"))'
```

It showed `readonly_paths: []` (no read-only items). The location to change is `/config/audit/log_request_body`.

### 3.3 PATCH

Set only `log_request_body` to `false`. No other audit settings are touched. No Indexer restart is needed.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem -X PATCH 'https://127.0.0.1:9200/_plugins/_security/api/audit' -H 'Content-Type: application/json' -d '[{"op":"replace","path":"/config/audit/log_request_body","value":false}]' -w '\nHTTP_STATUS:%{http_code}\n'
```

At build time it returned `Resource updated.` and `HTTP_STATUS:200`.

### 3.4 Confirming the Change

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/_plugins/_security/api/audit' | python3 -c 'import json,sys; d=json.load(sys.stdin); a=d["config"]["audit"]; print("AUDIT_ENABLED:",d["config"].get("enabled")); print("LOG_REQUEST_BODY:",a.get("log_request_body")); print("EXCLUDE_SENSITIVE_HEADERS:",a.get("exclude_sensitive_headers")); print("ENABLE_REST:",a.get("enable_rest")); print("ENABLE_TRANSPORT:",a.get("enable_transport")); print("DISABLED_REST_CATEGORIES:",a.get("disabled_rest_categories")); print("DISABLED_TRANSPORT_CATEGORIES:",a.get("disabled_transport_categories"))'
```

| Item | Result |
|---|---|
| Auditing overall | Enabled |
| `LOG_REQUEST_BODY` | `False` |
| `EXCLUDE_SENSITIVE_HEADERS` | `True` |
| REST and Transport auditing | Enabled |
| Categories not recorded | Unchanged |

This setting stops request bodies from being recorded in the audit log. It does not guarantee that bodies never appear in other places, such as other applications' logs.

## Closing Notes

In Part 26 we found where the audit settings are read from, and set `log_request_body` to `false` with a PATCH to the audit API (without a restart).

| Where the setting lives | Role |
|---|---|
| `opensearch.yml` | Output destination (`plugins.security.audit.type`); initial values when there is no audit document |
| Document `audit` in `.opendistro_security` | The audit settings in effect; changed through the audit API (PATCH) |

In the next part, we confirm that the audit log is actually being saved and that bodies are not recorded.

# Part 27: Confirming That the Audit Log Is Saved
## Introduction

### About This Book

This is Part 27 of Volume 2 of the "AI Autonomous Cyber Defense System Build Manual". In Part 25 we set the audit log's output destination, and in Part 26 we stopped request bodies from being recorded. Here we confirm the following **using reads only**, without changing settings.

1. The audit log index (`security-auditlog-YYYY.MM.dd`) has been created and events are being saved
2. The saved events contain no request bodies or authentication headers
3. The audit settings are stored in `.opendistro_security` and the design loads them again after a restart

The "values" of bodies and headers are not shown; only field names, counts, lengths and shapes are examined.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **security-core VM 220 (root)**.
- The index name `security-auditlog-2026.11.21` is from the day of the build. Replace it with the date in your environment.

## Chapter 1: Has the Destination Been Created?

### 1.1 The Startup Log

```bash
journalctl -u wazuh-indexer -b --no-pager | grep -Ei 'audit|sink|message routing|default storage' | tail -n 60
```

At build time nothing was shown. The absence of a log line does not by itself mean that the output destination was not created.

### 1.2 The Audit Log Index

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/_cat/indices?format=json&h=index,health,status,docs.count,store.size' | python3 -c 'import json,sys; d=json.load(sys.stdin); rows=[x for x in d if "audit" in x.get("index","").lower()]; print("AUDIT_INDEX_COUNT:",len(rows)); [print(x) for x in rows]'
```

At build time `security-auditlog-2026.11.21` existed, holding 24 events and 103.7 KB. The audit log is being saved inside the Indexer.

### 1.3 Why It Is yellow

The index's state was `yellow`. Check the shards.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/_cat/shards/security-auditlog-2026.11.21?format=json&h=index,shard,prirep,state,node,unassigned.reason'
```

| Shard | State |
|---|---|
| Primary (p) | `STARTED` (node-1) |
| Replica (r) | `UNASSIGNED` (`INDEX_CREATED`) |

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/_cluster/health?pretty'
```

There is one node, all 36 primary shards are running, and the only unassigned shard is this index's one replica. With only one node, there is nowhere to place the replica. This is not a save failure. The number of replicas is not changed, and the state is left `yellow` (author's notes, item 27-A).

## Chapter 2: What Is Being Saved

### 2.1 One Sample

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=1&filter_path=hits.hits._source' | python3 -c 'import json,sys; d=json.load(sys.stdin); h=d.get("hits",{}).get("hits",[]); print("SAMPLE_COUNT:",len(h)); s=h[0].get("_source",{}) if h else {}; print("TOP_LEVEL_FIELDS:",sorted(s)); print("BODY_FIELD_NAMES:",sorted(k for k in s if any(x in k.lower() for x in ("body","payload","request"))))'
```

This one event had no body field; it held information such as the REST method, path, source and user. For headers and URL parameters, look only at the names.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=1&filter_path=hits.hits._source.audit_rest_request_headers,hits.hits._source.audit_rest_request_params' | python3 -c 'import json,sys; d=json.load(sys.stdin); h=d.get("hits",{}).get("hits",[]); s=h[0].get("_source",{}) if h else {}; headers=s.get("audit_rest_request_headers"); params=s.get("audit_rest_request_params"); print("HEADER_FIELD_TYPE:",type(headers).__name__); print("HEADER_NAMES:",sorted(headers.keys()) if isinstance(headers,dict) else "not a map"); print("PARAM_FIELD_TYPE:",type(params).__name__); print("PARAM_NAMES:",sorted(params.keys()) if isinstance(params,dict) else "not a map")'
```

The headers were only `Accept`, `Host` and `User-Agent`, and the only parameter was `filter_path`; there was no `Authorization` or `Cookie`.

### 2.2 All Events

Count body-like fields, authentication headers, header and parameter names, and categories.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=100&filter_path=hits.hits._source' | python3 -c 'import json,sys,collections; d=json.load(sys.stdin); hs=d.get("hits",{}).get("hits",[]); body=[]; sensitive=[]; params=collections.Counter(); cats=collections.Counter(); headers=collections.Counter(); [cats.update([h.get("_source",{}).get("audit_category","UNKNOWN")]) for h in hs]; 
for h in hs:
 s=h.get("_source",{}); 
 for k in s:
  if any(x in k.lower() for x in ("request_body","requestbody","payload")): body.append(k)
 hd=s.get("audit_rest_request_headers",{}); 
 if isinstance(hd,dict):
  for k in hd:
   headers[k.lower()]+=1
   if k.lower() in ("authorization","proxy-authorization","cookie","set-cookie"): sensitive.append(k)
 p=s.get("audit_rest_request_params",{})
 if isinstance(p,dict): params.update(p.keys())
print("EVENTS_SCANNED:",len(hs)); print("BODY_FIELD_EVENT_COUNT:",len(body)); print("SENSITIVE_HEADER_EVENT_COUNT:",len(sensitive)); print("HEADER_NAME_COUNTS:",dict(headers)); print("PARAMETER_NAME_COUNTS:",dict(params)); print("AUDIT_CATEGORY_COUNTS:",dict(cats))'
```

At build time 86 events were examined. There were zero authentication headers, but **15 events had a body-like field**. Examine these 15 in detail.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=100&filter_path=hits.hits._source' | python3 -c 'import json,sys; d=json.load(sys.stdin); hs=d.get("hits",{}).get("hits",[]); n=0
for h in hs:
 s=h.get("_source",{}); ks=[k for k in s if any(x in k.lower() for x in ("request_body","requestbody","payload"))]
 if ks:
  n+=1
  print("EVENT",n,"TIMESTAMP:",s.get("@timestamp"),"CATEGORY:",s.get("audit_category"),"MATCHING_FIELD_NAMES:",ks)
print("MATCHING_EVENTS:",n,"SCANNED:",len(hs))'
```

All 15 had the category `COMPLIANCE_INTERNAL_CONFIG_READ` (reading internal configuration), and the field was `audit_request_body`.

### 2.3 What audit_request_body Really Is

Without showing the values, examine only their shape.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=100&filter_path=hits.hits._source' | python3 -c 'import json,sys; d=json.load(sys.stdin); hs=d.get("hits",{}).get("hits",[]); n=0
for h in hs:
 s=h.get("_source",{})
 if "audit_request_body" in s:
  v=s["audit_request_body"]; n+=1
  empty=(v is None or v=="" or v=={} or v==[])
  length=len(v) if isinstance(v,(str,dict,list)) else None
  print("EVENT",n,"TIMESTAMP:",s.get("@timestamp"),"TYPE:",type(v).__name__,"IS_NULL:",v is None,"IS_EMPTY:",empty,"LENGTH:",length)
print("BODY_FIELD_EVENTS:",n)'
```

All 15 were 25-character strings. Compare their contents with hashes.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=100&filter_path=hits.hits._source' | python3 -c 'import json,sys,hashlib,collections; d=json.load(sys.stdin); vals=[h.get("_source",{}).get("audit_request_body") for h in d.get("hits",{}).get("hits",[]) if "audit_request_body" in h.get("_source",{})]; hashes=collections.Counter(hashlib.sha256(v.encode()).hexdigest() for v in vals if isinstance(v,str)); print("BODY_FIELD_COUNT:",len(vals)); print("UNIQUE_VALUE_COUNT:",len(hashes)); print("VALUE_FREQUENCIES:",sorted(hashes.values(),reverse=True)); print("ALL_VALUES_IDENTICAL:",len(hashes)==1 and len(vals)>0)'
```

All 15 had the same value. Examine the kinds of characters and the shape.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=100&filter_path=hits.hits._source' | python3 -c 'import json,sys; d=json.load(sys.stdin); vals=[h["_source"]["audit_request_body"] for h in d.get("hits",{}).get("hits",[]) if "audit_request_body" in h.get("_source",{})]; v=vals[0] if vals else ""; print("LENGTH:",len(v)); print("ASCII_ONLY:",v.isascii()); print("ALPHANUMERIC_ONLY:",v.isalnum()); print("JSON_PARSEABLE:",end=" "); 
try: json.loads(v); print("yes")
except Exception: print("no")
print("HAS_WHITESPACE:",any(c.isspace() for c in v)); print("HAS_BRACES:",any(c in "{}[]" for c in v)); print("HAS_COLON:",":" in v); print("HAS_QUOTES:",any(c in chr(34)+chr(39) for c in v))'
```

It could be read as JSON. Look only at the key names and types.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=100&filter_path=hits.hits._source' | python3 -c 'import json,sys; d=json.load(sys.stdin); vals=[h["_source"]["audit_request_body"] for h in d.get("hits",{}).get("hits",[]) if "audit_request_body" in h.get("_source",{})]; v=json.loads(vals[0]) if vals else None; print("PARSED_TYPE:",type(v).__name__); print("TOP_LEVEL_KEYS:",sorted(v.keys()) if isinstance(v,dict) else "not_object"); 
for k,x in (v.items() if isinstance(v,dict) else []): print("FIELD:",k,"TYPE:",type(x).__name__,"LENGTH:",len(x) if isinstance(x,(str,dict,list)) else "n/a","NESTED_KEYS:",sorted(x.keys()) if isinstance(x,dict) else "n/a")'
```

The shape was as follows (values masked).

```text
{"field_names":[...]}
```

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=100&filter_path=hits.hits._source' | python3 -c 'import json,sys; d=json.load(sys.stdin); vals=[json.loads(h["_source"]["audit_request_body"]) for h in d.get("hits",{}).get("hits",[]) if "audit_request_body" in h.get("_source",{})]; x=vals[0].get("field_names",[]) if vals else []; print("FIELD_NAMES_COUNT:",len(x)); print("ELEMENT_TYPES:",[type(v).__name__ for v in x]); print("ELEMENT_LENGTHS:",[len(v) if isinstance(v,(str,dict,list)) else None for v in x]); print("ALL_15_EVENTS_SAME_STRUCTURE:",all(v==vals[0] for v in vals))'
```

The `field_names` array contained a single five-character string, and all 15 had the same shape. This is considered to be not the body of an HTTP request but information about field names when the internal configuration was read.

### 2.4 Counts by Category

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=500&sort=@timestamp:desc&filter_path=hits.hits._source' | python3 -c 'import json,sys,collections; d=json.load(sys.stdin); hits=d.get("hits",{}).get("hits",[]); counts=collections.Counter(); body_counts=collections.Counter(); samples=collections.Counter(); 
for h in hits:
 s=h.get("_source",{}); c=s.get("audit_category","UNKNOWN"); counts[c]+=1
 if "audit_request_body" in s: body_counts[c]+=1
print("SCANNED_EVENTS:",len(hits)); print("CATEGORY_COUNTS:",dict(sorted(counts.items()))); print("BODY_FIELD_COUNTS_BY_CATEGORY:",dict(sorted(body_counts.items()))); print("BODY_FIELD_TOTAL:",sum(body_counts.values())); print("NON_COMPLIANCE_BODY_EVENTS:",sum(n for c,n in body_counts.items() if not c.startswith("COMPLIANCE_")))'
```

| Category | Count | With `audit_request_body` |
|---|---:|---:|
| `COMPLIANCE_INTERNAL_CONFIG_READ` | 15 | 15 |
| `COMPLIANCE_INTERNAL_CONFIG_WRITE` | 1 | 0 |
| `FAILED_LOGIN` | 8 | 0 |
| `INDEX_EVENT` | 62 | 0 |

Ordinary events (`FAILED_LOGIN`, `INDEX_EVENT`) have no body field.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search?size=500&sort=@timestamp:asc&filter_path=hits.hits._source.@timestamp,hits.hits._source.audit_category,hits.hits._source.audit_request_body' | python3 -c 'import json,sys,collections; d=json.load(sys.stdin); rows=[h["_source"] for h in d.get("hits",{}).get("hits",[]) if "audit_request_body" in h.get("_source",{})]; print("EVENT_COUNT:",len(rows)); print("FIRST_TIMESTAMP:",rows[0].get("@timestamp") if rows else "none"); print("LAST_TIMESTAMP:",rows[-1].get("@timestamp") if rows else "none"); print("CATEGORIES:",dict(collections.Counter(r.get("audit_category","UNKNOWN") for r in rows)))'
```

The 15 events were from 2026-11-21 08:27:45 to 08:56:05 (UTC).

## Chapter 3: Is the Design One in Which the Settings Persist?

### 3.1 The Current Settings

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/_plugins/_security/api/audit' | python3 -c 'import json,sys; d=json.load(sys.stdin); c=d.get("config",{}); a=c.get("audit",{}); print("AUDIT_ENABLED:",c.get("enabled")); print("LOG_REQUEST_BODY:",a.get("log_request_body")); print("EXCLUDE_SENSITIVE_HEADERS:",a.get("exclude_sensitive_headers")); print("ENABLE_REST:",a.get("enable_rest")); print("ENABLE_TRANSPORT:",a.get("enable_transport")); print("DISABLED_REST_CATEGORIES:",a.get("disabled_rest_categories")); print("DISABLED_TRANSPORT_CATEGORIES:",a.get("disabled_transport_categories"))'
```

It still showed `LOG_REQUEST_BODY: False`.

### 3.2 The Configuration Document

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/.opendistro_security/_doc/audit?filter_path=_index,_id,_version,_seq_no,_primary_term,found'
```

At build time it showed `found: true` and `_version: 2`. The change made by PATCH is saved as a document.

### 3.3 Loading at Startup

```bash
 /usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c org.opensearch.security.configuration.ConfigurationRepository | grep -n -A45 -B12 'setupAuditConfigurationIfAny'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c org.opensearch.security.configuration.ConfigurationLoaderSecurity7 | grep -n -A55 -B15 'isAuditConfigDocPresentInIndex'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c 'org.opensearch.security.configuration.ConfigurationLoaderSecurity7$1' | grep -n -A35 -B15 -E 'AUDIT|isAuditConfigDocPresentInIndex|AtomicBoolean|set:|noData|success'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar:/usr/share/wazuh-indexer/lib/*' -p -c org.opensearch.security.configuration.ConfigurationRepository | grep -n -A35 -B15 -E 'auditLog\.setConfig|AuditConfig|onChange|executeConfigurationInitialization'
```

1. The settings are saved in the document `audit` in `.opendistro_security`
2. At startup, `ConfigurationLoaderSecurity7` reads the document and sets a flag saying "the document exists"
3. `ConfigurationRepository` applies the settings read and enables reloading of the audit configuration (hot reload)

Because of this design, the settings changed with PATCH are used after a restart as well (this was not confirmed by actually restarting).

At build time we also searched the code for the class that calls `AuditLogImpl.setConfig()` when the settings change, but did not pin it down and stopped as it was of low necessity. Those steps are not included in this book.

## Chapter 4: Confirming with Aggregations

### 4.1 The Aggregation Does Not Work

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem -w '\nHTTP_STATUS:%{http_code}\n' 'https://127.0.0.1:9200/security-auditlog-*/_search?size=0&track_total_hits=true' | python3 -c 'import json,sys; s=sys.stdin.read(); body=s.split("\nHTTP_STATUS:")[0]; status=s.split("\nHTTP_STATUS:")[-1].strip() if "\nHTTP_STATUS:" in s else "unknown"; print("HTTP_STATUS:",status); d=json.loads(body); print("TOP_LEVEL_KEYS:",list(d.keys())); print("ERROR_TYPE:",d.get("error",{}).get("type") if isinstance(d.get("error"),dict) else None); print("ERROR_REASON:",d.get("error",{}).get("reason") if isinstance(d.get("error"),dict) else None); print("HITS_KEYS:",list(d.get("hits",{}).keys()))'
```

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/_cat/indices/security-auditlog-*?format=json&h=index,docs.count,status' | python3 -c 'import json,sys; d=json.load(sys.stdin); print("INDEX_COUNT:",len(d)); [print("INDEX:",x.get("index"),"DOCS:",x.get("docs.count"),"STATUS:",x.get("status")) for x in d]'
```

The search returned `HTTP 200`, and the index had 88 events. However, aggregating by `audit_category` returned no results. Look at the error in the response.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem -H 'Content-Type: application/json' 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search' -d '{"size":0,"track_total_hits":true,"aggs":{"categories":{"terms":{"field":"audit_category","size":30}}}}' | python3 -c 'import json,sys; d=json.load(sys.stdin); print("TOP_LEVEL_KEYS:",list(d)); print("ERROR:",d.get("error")); h=d.get("hits"); print("HITS_TYPE:",type(h).__name__); print("HITS_TOTAL:",h.get("total") if isinstance(h,dict) else None); print("AGGREGATIONS_TYPE:",type(d.get("aggregations")).__name__); print("AGGREGATION_KEYS:",list(d.get("aggregations",{})) if isinstance(d.get("aggregations"),dict) else None); print("SHARDS:",d.get("_shards"))'
```

`audit_category` is of type `text`, and `fielddata`, which the aggregation needs, is disabled, so the aggregation failed on every shard. Rather than enabling `fielddata` (which uses a lot of memory), check whether a `keyword`-type field exists.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_mapping' | python3 -c 'import json,sys; d=json.load(sys.stdin); m=next(iter(d.values())).get("mappings",{}).get("properties",{}); print("audit_category:",m.get("audit_category")); print("audit_request_body:",m.get("audit_request_body")); print("audit_rest_request_headers:",m.get("audit_rest_request_headers"))'
```

`audit_category.keyword` and `audit_request_body.keyword` existed.

### 4.2 Aggregating with keyword

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem -H 'Content-Type: application/json' 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search' -d '{"size":0,"track_total_hits":true,"aggs":{"categories":{"terms":{"field":"audit_category.keyword","size":30}},"request_body_present":{"filter":{"exists":{"field":"audit_request_body"}}}}}' | python3 -c 'import json,sys; d=json.load(sys.stdin); print("ERROR_TYPE:",d.get("error",{}).get("type") if isinstance(d.get("error"),dict) else None); h=d.get("hits",{}); t=h.get("total"); print("TOTAL_EVENTS:",t.get("value") if isinstance(t,dict) else t); a=d.get("aggregations",{}); print("CATEGORIES:",{x["key"]:x["doc_count"] for x in a.get("categories",{}).get("buckets",[])}); print("REQUEST_BODY_PRESENT:",a.get("request_body_present",{}).get("doc_count"))'
```

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem -H 'Content-Type: application/json' 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search' -d '{"size":0,"aggs":{"categories":{"terms":{"field":"audit_category.keyword","size":30},"aggs":{"body_present":{"filter":{"exists":{"field":"audit_request_body"}}}}}}}' | python3 -c 'import json,sys; d=json.load(sys.stdin); print("ERROR_TYPE:",d.get("error",{}).get("type") if isinstance(d.get("error"),dict) else None); b=d.get("aggregations",{}).get("categories",{}).get("buckets",[]); [print("CATEGORY:",x["key"],"EVENTS:",x["doc_count"],"BODY_PRESENT:",x["body_present"]["doc_count"]) for x in b]'
```

| Category | Count | With a body field |
|---|---:|---:|
| `INDEX_EVENT` | 63 | 0 |
| `COMPLIANCE_INTERNAL_CONFIG_READ` | 17 | 17 |
| `FAILED_LOGIN` | 8 | 0 |
| `COMPLIANCE_INTERNAL_CONFIG_WRITE` | 1 | 0 |

### 4.3 The Shape of the 17

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem -H 'Content-Type: application/json' 'https://127.0.0.1:9200/security-auditlog-2026.11.21/_search' -d '{"size":20,"_source":["audit_category","audit_request_body"],"query":{"bool":{"filter":[{"term":{"audit_category.keyword":"COMPLIANCE_INTERNAL_CONFIG_READ"}},{"exists":{"field":"audit_request_body"}}]}}}' | python3 -c 'import json,sys; d=json.load(sys.stdin); h=d.get("hits",{}).get("hits",[]); print("SAMPLED_DOCS:",len(h)); import collections; stats=collections.Counter(); keys=collections.Counter(); shapes=collections.Counter(); 
for x in h:
 v=x.get("_source",{}).get("audit_request_body")
 if isinstance(v,str):
  stats[len(v)]+=1
  try:
   import json as j
   o=j.loads(v); shapes[type(o).__name__]+=1
   if isinstance(o,dict): keys[tuple(sorted(o.keys()))]+=1
  except Exception: shapes["invalid_json"]+=1
 else: shapes[type(v).__name__]+=1
print("LENGTH_COUNTS:",dict(stats)); print("JSON_SHAPES:",dict(shapes)); print("TOP_LEVEL_KEY_SETS:",{str(k):v for k,v in keys.items()})'
```

All 17 were 25-character JSON whose only key was `field_names`.

### 4.4 Matching Settings and Logs

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem 'https://127.0.0.1:9200/_plugins/_security/api/audit' | python3 -c 'import json,sys; d=json.load(sys.stdin); c=d.get("config",{}); a=c.get("audit",{}); m=c.get("compliance",{}); print("AUDIT_ENABLED:",c.get("enabled")); print("LOG_REQUEST_BODY:",a.get("log_request_body")); print("EXCLUDE_SENSITIVE_HEADERS:",a.get("exclude_sensitive_headers")); print("REST_ENABLED:",a.get("enable_rest")); print("TRANSPORT_ENABLED:",a.get("enable_transport")); print("COMPLIANCE_ENABLED:",m.get("enabled")); print("COMPLIANCE_READ_METADATA_ONLY:",m.get("read_metadata_only")); print("COMPLIANCE_WRITE_METADATA_ONLY:",m.get("write_metadata_only"))'
```

| Item | Value |
|---|---|
| Auditing | Enabled |
| REST and Transport auditing | Enabled |
| Recording request bodies | `false` |
| Excluding sensitive headers | `true` |
| Compliance | Enabled (metadata only for both reads and writes) |

## Closing Notes

In Part 27 we confirmed the following.

| Item | Result |
|---|---|
| Saving the audit log | Saved in `security-auditlog-YYYY.MM.dd` (89 events at build time) |
| Request bodies | Not recorded for ordinary events |
| The 17 events with `audit_request_body` | Only the fixed shape of internal configuration reads (`{"field_names":[...]}`) |
| Authentication headers | Not recorded |
| Settings | Saved in `.opendistro_security`; the design loads them at startup |
| Index state | `yellow` because there is only one node (replicas cannot be placed) |

Not every REST operation or every type of event was tested. In the next part, we check the Collector that sends Wazuh alerts to PostgreSQL.

# Part 28: Checking the Collector and Why It Stopped
## Introduction

### About This Book

This is Part 28 of Volume 2 of the "AI Autonomous Cyber Defense System Build Manual". For the Collector that sends Wazuh alerts (`alerts.json`) to PostgreSQL (LXC 109) (`/usr/local/lib/wazuh-collector/collector.py`, Parts 3–9 of Volume 1), we do the following.

1. Read the code and check what it saves to PostgreSQL (reads only)
2. During the check, we found that the Collector had **stopped and was repeatedly restarting**, so we investigate the cause

There were two causes. They are the same as what happened in Part 9 of Volume 1.

| # | Cause |
|---|---|
| 1 | The `alerts.json` newly created by log rotation (daily) had no read ACL for the Collector |
| 2 | While looking for the file it had been reading (the saved inode), the Collector could not enter a hidden test directory created earlier (`.acl-inheritance-test.bkv8vd`) and stopped |

This book fixes the first and goes as far as identifying the second. Recovery is done in Part 29, and preventing recurrence in Part 30.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **security-core VM 220 (root)**.
- Programs that display code replace lines containing passwords, tokens, connection strings and the like with `[SENSITIVE LINE OMITTED]`.

## Chapter 1: Checking What Is Saved

### 1.1 The Functions

```bash
python3 - <<'PY'
import re
p = "/usr/local/lib/wazuh-collector/collector.py"
patterns = re.compile(
    r'^\s*(async\s+)?def\s+|^\s*class\s+|INSERT_SQL|'
    r'extract_event|process_line|full_log|audit_request_body|'
    r'field_names|UniqueViolation|SAVEPOINT|ROLLBACK TO'
)
with open(p, encoding="utf-8") as f:
    for n, line in enumerate(f, 1):
        if patterns.search(line):
            if re.search(r'password|passwd|secret|token|dsn|api_key', line, re.I):
                print(f"{n}: [SENSITIVE LINE OMITTED]")
            else:
                print(f"{n}: {line.rstrip()[:180]}")
PY
```

`extract_event()` extracts the event fields, and `process_line()` saves them with `INSERT_SQL`.

### 1.2 Fields Extracted and the INSERT

```bash
python3 - <<'PY'
p = "/usr/local/lib/wazuh-collector/collector.py"
ranges = [(41, 80), (191, 248), (504, 525)]
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
for start, end in ranges:
    print(f"\n===== collector.py:{start}-{end} =====")
    for n in range(start, min(end, len(lines)) + 1):
        line = lines[n-1]
        if any(x in line.lower() for x in ("password", "passwd", "secret", "token", "dsn", "api_key")):
            print(f"{n}: [SENSITIVE LINE OMITTED]")
        else:
            print(f"{n}: {line.rstrip()}")
PY
```

- The INSERT has a fixed set of 13 columns
- `full_log`, `audit_request_body` and the whole of the event's `data` are not saved (only `srcip` and `srcport` are taken from `data`)
- `UniqueViolation` is treated as a "duplicate" only for SQLSTATE `23505` (the same `event_id`)
- DB writes are done inside a transaction

### 1.3 How Strings Are Tidied

```bash
python3 - <<'PY'
p = "/usr/local/lib/wazuh-collector/collector.py"
ranges = [(126, 190)]
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
for start, end in ranges:
    print(f"===== collector.py:{start}-{end} =====")
    for n in range(start, min(end, len(lines)) + 1):
        print(f"{n}: {lines[n-1].rstrip()}")
PY
```

`safe_text()` removes control characters and invisible format characters, trims surrounding whitespace and limits the length. MITRE information is limited to `id`, `tactic` and `technique`. However, this processing only tidies the form; it does not find and remove passwords or user names by meaning (`rule.description`, `agent.name` and so on are saved as they are; author's notes, item 28-A).

### 1.4 The Continuous Reading Loop

```bash
python3 - <<'PY'
p = "/usr/local/lib/wazuh-collector/collector.py"
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
for n in range(526, min(590, len(lines)) + 1):
    line = lines[n-1]
    if any(x in line.lower() for x in ("password", "passwd", "secret", "token", "dsn", "api_key")):
        print(f"{n}: [SENSITIVE LINE OMITTED]")
    else:
        print(f"{n}: {line.rstrip()}")
PY
```

```bash
python3 - <<'PY'
p = "/usr/local/lib/wazuh-collector/collector.py"
ranges = [(249, 296), (458, 503), (579, 680)]
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
for start, end in ranges:
    print(f"\n===== collector.py:{start}-{end} =====")
    for n in range(start, min(end, len(lines)) + 1):
        print(f"{n}: {lines[n-1].rstrip()}")
PY
```

- When PostgreSQL cannot be reached, it goes back to the start of that line and retries 5 seconds later
- When processing fails, it also goes back to the start of the line, closes the connection and reconnects
- Connection error logs contain only the name of the exception type (no connection information)

```bash
python3 - <<'PY'
p = "/usr/local/lib/wazuh-collector/collector.py"
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
for n in range(675, min(760, len(lines)) + 1):
    line = lines[n-1]
    if any(x in line.lower() for x in ("password", "passwd", "secret", "token", "dsn", "api_key")):
        print(f"{n}: [SENSITIVE LINE OMITTED]")
    else:
        print(f"{n}: {line.rstrip()}")
PY
```

- The read position (state file) is written to a temporary file, `fsync`ed and then swapped in with `os.replace` (permissions `0600`)
- Lines that are too long are skipped without writing their contents to the log
- When the file is switched, reading starts from the beginning of the file with the new inode
- On exit, the file and the DB connection are closed

### 1.5 Validating the State File

```bash
python3 - <<'PY'
p = "/usr/local/lib/wazuh-collector/collector.py"
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
for n in range(297, 328):
    print(f"{n}: {lines[n-1].rstrip()}")
PY
```

If the contents are not a dictionary or `inode` / `offset` are not integers within range, `load_state()` stops with `RuntimeError` rather than re-reading from the beginning. Only when there is no state file is it treated as a first startup.

```bash
python3 - <<'PY'
p = "/usr/local/lib/wazuh-collector/collector.py"
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
for n in range(81, 116):
    print(f"{n}: {lines[n-1].rstrip()}")
PY
```

`safe_integer()` does not accept `bool` (a kind of `int` in Python) as an integer, and limits strings to ASCII digits, up to 20 digits. `parse_timestamp()` does not accept times without a time zone.

### 1.6 How the File Is Opened

```bash
python3 - <<'PY'
p = "/usr/local/lib/wazuh-collector/collector.py"
ranges = [(328, 457)]
with open(p, encoding="utf-8") as f:
    lines = f.readlines()
for start, end in ranges:
    print(f"===== collector.py:{start}-{end} =====")
    for n in range(start, min(end, len(lines)) + 1):
        line = lines[n-1]
        if any(x in line.lower() for x in ("password", "passwd", "secret", "token", "dsn", "api_key")):
            print(f"{n}: [SENSITIVE LINE OMITTED]")
        else:
            print(f"{n}: {line.rstrip()}")
PY
```

- It compares the saved inode with the current file; if the file has switched, it looks for the file with the previous inode and reads the rest of it
- If the previous file cannot be found, or the saved position is larger than the file, it **stops rather than silently skipping**
- When searching directories, it does not follow symbolic links and does not look at compressed files

Despite its name, `safe_open_current_alert_file()` consisted of only the following two lines (part of the code).

```text
handle = ALERT_FILE.open("rb")
actual_stat = os.fstat(handle.fileno())
```

There is no `O_NOFOLLOW` (do not open symbolic links) and no check that it is a regular file. Check the permissions.

```bash
python3 - <<'PY'
import os
import stat
from pathlib import Path

p = Path("/var/ossec/logs/alerts")
for path in (Path("/var/ossec"), Path("/var/ossec/logs"), p, p / "alerts.json"):
    try:
        s = path.lstat()
        print(
            f"{path}: "
            f"type={'symlink' if stat.S_ISLNK(s.st_mode) else 'regular' if stat.S_ISREG(s.st_mode) else 'directory' if stat.S_ISDIR(s.st_mode) else 'other'} "
            f"owner={s.st_uid}:{s.st_gid} "
            f"mode={stat.S_IMODE(s.st_mode):04o}"
        )
    except OSError as e:
        print(f"{path}: {type(e).__name__}")
PY
```

| Target | Owner | Permissions |
|---|---|---|
| `/var/ossec` | root:110 | 0750 |
| `/var/ossec/logs` | 110:110 | 0770 |
| `/var/ossec/logs/alerts` | 110:110 | 0750 |
| `alerts.json` | 110:110 | 0640 |

`/var/ossec/logs` is writable by group 110. We judged that it does not need to change right away (author's notes, item 28-B).

## Chapter 2: The Collector Had Stopped

### 2.1 The Service State

```bash
id
```

The current shell is root. Look at the state of the Collector service.

```bash
systemctl list-units --type=service --all --no-legend | grep -i collector
```

`wazuh-collector.service` was `activating (auto-restart)` (restarting repeatedly).

```bash
systemctl show wazuh-collector.service \
  -p User -p Group -p DynamicUser -p MainPID \
  -p ExecMainCode -p ExecMainStatus \
  -p NRestarts -p Result
```

| Item | Value |
|---|---|
| `User`, `Group` | `wazuh-collector` |
| `MainPID` | 0 (no process) |
| `Result` | `exit-code` |
| `ExecMainStatus` | 1 |
| `NRestarts` | 350 |

### 2.2 The First Cause

```bash
journalctl -u wazuh-collector.service -n 50 --no-pager -o short-iso
```

It was exiting at startup because it could not open `alerts.json`.

```text
PermissionError: [Errno 13] Permission denied
/var/ossec/logs/alerts/alerts.json
```

```bash
printf '%s\n' '===== collector account ====='
id wazuh-collector
getent passwd wazuh-collector
getent group wazuh-collector
printf '%s\n' '===== directory permissions ====='
namei -l /var/ossec/logs/alerts/alerts.json
printf '%s\n' '===== ACL ====='
getfacl -p /var/ossec/logs /var/ossec/logs/alerts /var/ossec/logs/alerts/alerts.json
```

| Target | Collector's permission |
|---|---|
| `/var/ossec/logs` | `--x` through ACL (can traverse) |
| `/var/ossec/logs/alerts` | `r-x` through ACL (can traverse) |
| `alerts.json` | **No read permission** |

The `alerts` directory has a default ACL, but it was not applied to the `alerts.json` newly created by rotation (the same as Part 9, 1.3 of Volume 1).

```bash
runuser -u wazuh-collector -- test -r /var/ossec/logs/alerts/alerts.json
echo "READ_TEST_EXIT_CODE=$?"
```

`READ_TEST_EXIT_CODE=1` confirmed that it could not be read.

### 2.3 Adding a Read ACL

Add **read only** for the Collector's user. No write or delete permission is added.

```bash
setfacl -m u:wazuh-collector:r-- /var/ossec/logs/alerts/alerts.json
```

```bash
runuser -u wazuh-collector -- test -r /var/ossec/logs/alerts/alerts.json
echo "READ_TEST_EXIT_CODE=$?"
getfacl -p /var/ossec/logs/alerts/alerts.json
```

It became `READ_TEST_EXIT_CODE=0`, and the ACL was only `user:wazuh-collector:r--`.

### 2.4 The Second Cause

Check whether systemd's automatic restart got it running.

```bash
systemctl status wazuh-collector.service --no-pager -l
```

```bash
journalctl -u wazuh-collector.service -n 35 --no-pager -o short-iso
```

It was still failing to start. This time it stopped while looking for the file it had been reading (the saved inode), because it could not enter `/var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd`.

```bash
stat -c 'TYPE=%F OWNER=%U:%G MODE=%a INODE=%i PATH=%n' /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd
getfacl -p /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd
```

| Item | Value |
|---|---|
| Owner, permissions | `root:root`, `700` |
| Collector's ACL | `r-x` exists, but the ACL mask is `---` |
| Effective permission | `---` (cannot enter) |

This is the directory created when testing ACL inheritance in Part 6 of Volume 1 (recorded in Part 9 of Volume 1 as "still remaining").

```bash
find /var/ossec/logs/alerts -maxdepth 1 -name '.acl-inheritance-test*' -printf '%M %u:%g %p\n'
```

```bash
find /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd -maxdepth 2 -printf '%y %M %u:%g %s %p\n'
```

```bash
find /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd -printf '%y %M %u:%g %s %p\n'
```

It contained only `2027/Jan/test.json` (0 bytes), all `root:root`. It is not a real alert log.

### 2.5 The Search and the Saved Position

```bash
sed -n '1,80p;328,365p' /usr/local/lib/wazuh-collector/collector.py
```

`find_inode_file()` walks every directory under `alerts`, and if it cannot enter even one, it gives up the whole search (a design that errs on the safe side so as not to answer "not found" without having searched everywhere).

Compare the saved position with the current file (the state file as a whole is not shown).

```bash
python3 - <<'PY'
import json, os
from pathlib import Path

state_path = Path("/var/lib/wazuh-collector/state.json")
alert_path = Path("/var/ossec/logs/alerts/alerts.json")

try:
    state = json.loads(state_path.read_text())
    print("STATE_INODE:", state.get("inode"))
    print("STATE_OFFSET:", state.get("offset"))
except Exception as e:
    print("STATE_READ_ERROR:", type(e).__name__)

try:
    st = alert_path.stat()
    print("CURRENT_INODE:", st.st_ino)
    print("CURRENT_SIZE:", st.st_size)
except Exception as e:
    print("CURRENT_FILE_ERROR:", type(e).__name__)
PY
```

| Item | Value |
|---|---|
| Saved inode | 5409383 |
| inode of the current `alerts.json` | 5409517 |
| Saved position (offset) | 6,433,808 |
| Size of the current file | 564,829 bytes |

After the rotation, the Collector needs to find the file with the previous inode 5409383. Simply stopping the search could miss unread data in the previous file.

```bash
find /var/ossec/logs/alerts -xdev -type f -inum 5409383 -printf 'FOUND=%p SIZE=%s OWNER=%u:%g MODE=%m\n'
```

The file with inode 5409383 was not found.

```bash
sed -n '365,430p' /usr/local/lib/wazuh-collector/collector.py
```

When the previous inode cannot be found, it is designed to stop with `Previous alert file cannot be located; refusing unsafe resume`. This is a correct safety measure so that unread data is never silently skipped.

## Closing Notes

What Part 28 found is as follows.

| Item | Result |
|---|---|
| What is saved | Limited to 13 columns; `full_log` and the whole of `data` are not saved |
| How strings are tidied | Only tidies the form; it is not processing that finds and removes secrets |
| Cause of the stop 1 | The new `alerts.json` had no read ACL → **added** |
| Cause of the stop 2 | Cannot enter the hidden test directory, so it cannot search for the previous file |
| Previous file | inode 5409383 is not found (the Collector stops for safety) |

In the next part, we find out what happened to the previous file and restart the Collector without missing any events.

# Part 29: Restarting the Collector Without Missing Any Events
## Introduction

### About This Book

This is Part 29 of Volume 2 of the "AI Autonomous Cyber Defense System Build Manual". In Part 28 we found that the Collector had stopped starting, for safety, because "the file it had been reading (inode 5409383) cannot be found". Here we do the following.

1. Find out what happened to the previous file, using the log files, compressed files and checksums
2. Confirm that the saved read position was **the end** of the previous file
3. After confirming PostgreSQL's mechanism for preventing duplicates, rewrite the read position to "the beginning of the current `alerts.json`"
4. Start the Collector and confirm that the events were ingested into PostgreSQL

Arbitrarily advancing the read position to the end of the current file would leave events unread. We proceed only after confirming each piece of evidence.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **postgresql**: LXC 109 (192.168.0.151), OS user `postgres`
- Alert text is not shown. The PostgreSQL password is read from `.pgpass` and not shown.
- inodes, sizes, times and counts are those at build time. Replace them with the values in your environment.

## Chapter 1: Looking for the Previous File

> **Run on: VM 220**

### 1.1 The Log Files

```bash
find /var/ossec/logs/alerts -maxdepth 3 -type f -printf '%i %s %M %u:%g %p\n' | sort -k6
```

Compressed JSON logs for November 17–20 (`2026/Nov/ossec-alerts-*.json.gz`) and the current log for the 21st remained. inode 5409383 did not exist. The Collector's search covers only files ending in `.json`, not `.json.gz`.

```bash
if command -v lsof >/dev/null 2>&1; then lsof -nP +L1 2>/dev/null | grep -E '5409383|alerts' || true; else echo "lsof_NOT_INSTALLED"; fi
```

There were also no files still held open after being deleted.

```bash
stat -c 'INODE=%i SIZE=%s MTIME=%y PATH=%n' /var/ossec/logs/alerts/2026/Nov/ossec-alerts-*.json*
```

The JSON logs switch daily: the files for the 17th–20th have been compressed, and the 21st is the current `alerts.json`.

### 1.2 The Size of the 20th's File

```bash
gzip -l /var/ossec/logs/alerts/2026/Nov/ossec-alerts-*.json.gz
```

The decompressed size of the 20th's file was **6,433,808 bytes**, the same as the saved read position.

```bash
gzip -t /var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json.gz
echo "GZIP_TEST_EXIT_CODE=$?"
```

The compressed file is not corrupted (`GZIP_TEST_EXIT_CODE=0`). While decompressing (without writing to disk), examine the number of lines and their form.

```bash
python3 - <<'PY'
import gzip, json

path = "/var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json.gz"
total = 0
lines = 0
invalid = 0
last_byte = None

with gzip.open(path, "rb") as f:
    while True:
        chunk = f.readline()
        if not chunk:
            break
        total += len(chunk)
        lines += 1
        last_byte = chunk[-1:]
        try:
            json.loads(chunk)
        except Exception:
            invalid += 1

print("UNCOMPRESSED_BYTES:", total)
print("LINE_COUNT:", lines)
print("INVALID_JSON_LINES:", invalid)
print("ENDS_WITH_NEWLINE:", last_byte == b"\n")
print("SAVED_OFFSET_MATCH:", total == 6433808)
PY
```

| Item | Result |
|---|---|
| Decompressed size | 6,433,808 bytes (matches the saved position) |
| Lines | 10,293 |
| Lines not readable as JSON | 0 |
| Final newline | Present |

### 1.3 Times and Checksum

```bash
stat -c 'MTIME=%y CTIME=%z SIZE=%s PATH=%n' /var/lib/wazuh-collector/state.json /var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json.gz /var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json.sum
file /var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json.sum
```

The state file was saved at 23:54:26 on November 20 (UTC), and the 20th's file was compressed at 00:00:10 on November 21 (UTC). When the state was saved, the 20th's file was the current file.

Look at the checksum file created by Wazuh (37 bytes).

```bash
cat /var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json.sum
```

It recorded the SHA-256 of the 20th's file before compression.

```text
7b07b435669a8c98892f4919295644c21bfdb35522f3747e21366f6ba0aafe79
```

Compute the SHA-256 while decompressing and compare it with the record. Replace the value with the value in your environment's `.sum`.

```bash
python3 - <<'PY'
import gzip, hashlib

path = "/var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json.gz"
expected = "7b07b435669a8c98892f4919295644c21bfdb35522f3747e21366f6ba0aafe79"

h = hashlib.sha256()
size = 0

with gzip.open(path, "rb") as f:
    while True:
        chunk = f.read(1024 * 1024)
        if not chunk:
            break
        h.update(chunk)
        size += len(chunk)

actual = h.hexdigest()
print("UNCOMPRESSED_BYTES:", size)
print("ACTUAL_SHA256:", actual)
print("EXPECTED_SHA256:", expected)
print("CHECKSUM_MATCH:", actual == expected)
PY
```

The result was `CHECKSUM_MATCH: True`.

### 1.4 The Current File

```bash
python3 - <<'PY'
import json
from pathlib import Path

p = Path("/var/ossec/logs/alerts/alerts.json")
size = 0
lines = 0
invalid = 0
last_byte = None

with p.open("rb") as f:
    while True:
        line = f.readline()
        if not line:
            break
        size += len(line)
        lines += 1
        last_byte = line[-1:]
        try:
            json.loads(line)
        except Exception:
            invalid += 1

print("CURRENT_INODE:", p.stat().st_ino)
print("CURRENT_BYTES:", size)
print("LINE_COUNT:", lines)
print("INVALID_JSON_LINES:", invalid)
print("ENDS_WITH_NEWLINE:", last_byte == b"\n")
PY
```

The 21st's file also had no unreadable lines. Compare the times at the boundary.

```bash
python3 - <<'PY'
import gzip, json

archive = "/var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json.gz"
current = "/var/ossec/logs/alerts/alerts.json"

last = None
with gzip.open(archive, "rb") as f:
    for line in f:
        if line.strip():
            last = json.loads(line)

with open(current, "rb") as f:
    first = json.loads(f.readline())

print("ARCHIVE_LAST_TIMESTAMP:", last.get("timestamp"))
print("CURRENT_FIRST_TIMESTAMP:", first.get("timestamp"))
PY
```

| Item | Time (UTC) |
|---|---|
| Last event in the 20th's file | 11/20 23:54:26.205 |
| State file saved | 11/20 23:54:26.714 |
| First event in the 21st's file | 11/21 00:09:26.253 |

The saved read position corresponds to the end of the 20th's file. Therefore **reading the current `alerts.json` (inode 5409517) from the beginning (offset 0) is sufficient**. However, it cannot be proved that there were no alerts during these 15 minutes.

### 1.5 The Mechanism That Prevents Duplicates

Part of the 21st's file may have been ingested while the Collector was still running. Confirm that re-reading from the beginning will not insert anything twice.

```bash
PGPASSFILE=/etc/wazuh-collector/.pgpass psql "host=postgresql.neomedia.mydns.jp hostaddr=192.168.0.151 port=5432 dbname=security_workbench user=wazuh_collector sslmode=verify-full sslrootcert=/etc/ssl/certs/postgresql-server-ca.pem" -X -A -F '|' -c "SELECT i.relname AS index_name, ix.indisunique AS is_unique, pg_get_indexdef(i.oid) AS index_definition FROM pg_class t JOIN pg_namespace n ON n.oid=t.relnamespace JOIN pg_index ix ON ix.indrelid=t.oid JOIN pg_class i ON i.oid=ix.indexrelid WHERE n.nspname='incident' AND t.relname='alert_events' ORDER BY i.relname;"
```

The result at build time (key points) was as follows: `event_id` was the primary key (unique).

```text
alert_events_pkey
UNIQUE (event_id)
```

Also check the processing on the Collector side.

```bash
grep -n -A45 -B15 'UniqueViolation\|def process_line' /usr/local/lib/wazuh-collector/collector.py
```

```bash
sed -n '555,610p' /usr/local/lib/wazuh-collector/collector.py
```

```bash
sed -n '600,665p' /usr/local/lib/wazuh-collector/collector.py
```

1. Each event is INSERTed in its own transaction
2. If `event_id` is a duplicate (SQLSTATE `23505`), the insert is rolled back and it moves on to the next
3. After either a successful INSERT or a duplicate, the read position is saved
4. If the DB or saving fails, it goes back to the start of the line and retries
5. When the file switches, it saves the new inode and offset 0 first, then switches

## Chapter 2: Rewriting the Read Position

> **Run on: VM 220**

### 2.1 Stopping It

```bash
systemctl stop wazuh-collector.service
```

```bash
systemctl is-active wazuh-collector.service
systemctl show wazuh-collector.service -p MainPID -p NRestarts -p ActiveState -p SubState
```

Confirm `inactive` and `MainPID=0`, so that no process will rewrite the state file.

### 2.2 Backup

```bash
backup="/var/lib/wazuh-collector/state.json.pre-recovery-20261121"; test ! -e "$backup" && cp -a /var/lib/wazuh-collector/state.json "$backup" && sha256sum /var/lib/wazuh-collector/state.json "$backup" && cmp -s /var/lib/wazuh-collector/state.json "$backup" && echo "BACKUP_VERIFY=OK"
```

Confirm `BACKUP_VERIFY=OK`.

### 2.3 Rewriting

The new read position is as follows.

```text
{"inode": 5409517, "offset": 0}
```

Rewrite it only if the current state file is as expected (inode 5409383, offset 6433808) and the inode of `alerts.json` is 5409517. Otherwise it stops without doing anything. The rewrite writes a temporary file and then swaps it in, keeping the original permissions and owner.

```bash
python3 - <<'PY'
import json, os, stat, tempfile

state_path = "/var/lib/wazuh-collector/state.json"
backup_path = "/var/lib/wazuh-collector/state.json.pre-recovery-20261121"
alert_path = "/var/ossec/logs/alerts/alerts.json"

with open(state_path, encoding="utf-8") as f:
    old_state = json.load(f)
with open(backup_path, "rb") as f:
    backup_bytes = f.read()

if old_state != {"inode": 5409383, "offset": 6433808}:
    raise SystemExit("ABORT: state.json differs from expected old state")
if os.stat(alert_path).st_ino != 5409517:
    raise SystemExit("ABORT: alerts.json inode changed")
if not backup_bytes:
    raise SystemExit("ABORT: backup is empty")

st = os.stat(state_path)
directory = os.path.dirname(state_path)
fd, temp_path = tempfile.mkstemp(prefix=".state.json.recovery.", dir=directory)

try:
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"inode": 5409517, "offset": 0}, f)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())

    os.chmod(temp_path, stat.S_IMODE(st.st_mode))
    os.chown(temp_path, st.st_uid, st.st_gid)
    os.replace(temp_path, state_path)

    dir_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
except Exception:
    if os.path.exists(temp_path):
        os.unlink(temp_path)
    raise

with open(state_path, encoding="utf-8") as f:
    result = json.load(f)

print("NEW_STATE:", json.dumps(result, sort_keys=True))
print("STATE_UPDATE:", "OK" if result == {"inode": 5409517, "offset": 0} else "FAILED")
print("BACKUP_PRESERVED:", os.path.exists(backup_path))
PY
```

### 2.4 Starting It

```bash
systemctl start wazuh-collector.service
```

```bash
systemctl is-active wazuh-collector.service
systemctl show wazuh-collector.service -p MainPID -p NRestarts -p ActiveState -p SubState
```

At build time it was `active` and `running` (PID 13542). `NRestarts=874` is the total count up to when it was stopped.

```bash
journalctl -u wazuh-collector.service -n 60 --no-pager -o short-iso
```

```bash
journalctl -u wazuh-collector.service --since "2026-11-21 10:45:00" --no-pager -o short-iso | tail -n 40
```

The log after starting contained the following two lines.

```text
INFO Resuming current alert file
INFO PostgreSQL connection established
```

### 2.5 Is It Reading Forward?

```bash
python3 - <<'PY'
import json, os

state_path = "/var/lib/wazuh-collector/state.json"
alert_path = "/var/ossec/logs/alerts/alerts.json"

with open(state_path, encoding="utf-8") as f:
    state = json.load(f)

st = os.stat(alert_path)
print("STATE_INODE:", state["inode"])
print("STATE_OFFSET:", state["offset"])
print("CURRENT_INODE:", st.st_ino)
print("CURRENT_SIZE:", st.st_size)
print("INODE_MATCH:", state["inode"] == st.st_ino)
print("OFFSET_WITHIN_FILE:", 0 <= state["offset"] <= st.st_size)
PY
```

The read position (858,191) became equal to the file size, showing that it had read to the end.

```bash
systemctl is-active wazuh-collector.service
journalctl -u wazuh-collector.service --since "2026-11-21 10:45:00" --no-pager -o cat | grep -E 'ERROR|WARNING|Duplicate alert skipped|PostgreSQL connection|Resuming current alert'
```

There were no errors or warnings after starting.

## Chapter 3: Confirming in PostgreSQL

> **Run on: postgresql** (OS user `postgres`)

`wazuh_collector` has only the INSERT privilege, so rather than adding privileges, run read-only SQL as the PostgreSQL administrator.

```bash
psql -d security_workbench -X -P pager=off -c "
SELECT
    COUNT(*) AS events_last_30m,
    MIN(event_timestamp) AS first_event,
    MAX(event_timestamp) AS latest_event
FROM incident.alert_events
WHERE event_timestamp >= NOW() - INTERVAL '30 minutes';
"
```

There were 143 events in the last 30 minutes. Check whether there is a column for the ingestion time.

```bash
psql -d security_workbench -X -P pager=off -c "
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'incident'
  AND table_name = 'alert_events'
ORDER BY ordinal_position;
"
```

`ingested_at` existed. Count the events ingested after the time the Collector was started (10:45:16 UTC). Replace the time with the one in your environment.

```bash
psql -d security_workbench -X -P pager=off -c "
SELECT
    COUNT(*) AS ingested_after_restart,
    COUNT(DISTINCT event_id) AS unique_event_ids,
    MIN(ingested_at) AS first_ingested_at,
    MAX(ingested_at) AS latest_ingested_at
FROM incident.alert_events
WHERE ingested_at >= TIMESTAMPTZ '2026-11-21 10:45:16+00';
"
```

| Item | Result |
|---|---|
| Inserted after starting | 1,318 |
| Distinct `event_id` | 1,318 (no duplicates) |
| First insert | 10:45:16.110 UTC |
| Last insert | 10:58:41.944 UTC |

```bash
psql -d security_workbench -X -P pager=off -c "
SELECT
    COUNT(*) AS ingested_last_5m,
    MAX(ingested_at) AS latest_ingested_at
FROM incident.alert_events
WHERE ingested_at >= NOW() - INTERVAL '5 minutes';
"
```

There was one event in the last five minutes. That may simply be because there were few new alerts, so check on VM 220 whether anything is left unread.

> **Run on: VM 220**

```bash
python3 - <<'PY'
import json, os

with open("/var/lib/wazuh-collector/state.json", encoding="utf-8") as f:
    state = json.load(f)

st = os.stat("/var/ossec/logs/alerts/alerts.json")
print("STATE_INODE:", state["inode"])
print("STATE_OFFSET:", state["offset"])
print("CURRENT_INODE:", st.st_ino)
print("CURRENT_SIZE:", st.st_size)
print("INODE_MATCH:", state["inode"] == st.st_ino)
print("OFFSET_AT_EOF:", state["offset"] == st.st_size)
print("UNPROCESSED_BYTES:", max(0, st.st_size - state["offset"]) if state["inode"] == st.st_ino else "ROTATION")
PY
```

It showed `UNPROCESSED_BYTES: 0` (nothing unread).

```bash
systemctl show wazuh-collector.service -p ActiveState -p SubState -p MainPID -p NRestarts
```

## Closing Notes

In Part 29 we restarted the Collector without leaving anything unread.

| Item | Result |
|---|---|
| Previous file | The 20th's compressed file; confirmed by size, lines and checksum |
| Read position | Rewritten to inode 5409517, offset 0 (backup `state.json.pre-recovery-20261121`) |
| PostgreSQL | 1,318 events inserted, 0 duplicates |
| Unread | 0 bytes |

It has not been proved that no events were lost around the rotation. Also, the hidden test directory still remains, so the Collector may stop for the same reason the next time the file switches. The next part prevents this.

# Part 30: Keeping the Collector from Stopping for the Same Reason
## Introduction

### About This Book

This is Part 30 of Volume 2 of the "AI Autonomous Cyber Defense System Build Manual". In Parts 28 and 29 we found that the Collector had stopped because it could not enter a hidden test directory (`.acl-inheritance-test.bkv8vd`), fixed the read position and started it again. However, the directory still remains, so the Collector may stop again the next time the file switches.

Here, rather than deleting the directory or widening the Collector's permissions, we change just two lines of the Collector's code so that **when looking for the previous file, it does not search directories whose names start with `.` (hidden directories)**.

- The real locations of alerts (such as `2026/Nov`) are searched as before
- Errors when an ordinary directory cannot be entered still stop the Collector, as before (they are not swallowed)
- The design of not following symbolic links is unchanged

Finally, we check in the code the processing at log switching (rotation) and the handling of the state file and duplicates.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **postgresql**: LXC 109 (192.168.0.151), OS user `postgres`

## Chapter 1: What the Hidden Directory Is

> **Run on: VM 220**

```bash
find /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd -maxdepth 5 -printf '%y %M %u:%g %s bytes %TY-%Tm-%Td %TH:%TM:%TS %p\n'
```

It was created on November 18, 2026, everything is `root:root`, and it contains only `2027/Jan/test.json` (0 bytes). It was created when testing ACL inheritance in Part 6 of Volume 1. Look for any remaining script that created it.

```bash
grep -R -n -F --exclude='*.pyc' --exclude='*.log' '.acl-inheritance-test' /root /usr/local /etc 2>/dev/null | head -n 40
```

There were none. Look at the ACL.

```bash
getfacl -p /var/ossec/logs/alerts /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd/2027 /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd/2027/Jan /var/ossec/logs/alerts/.acl-inheritance-test.bkv8vd/2027/Jan/test.json
```

Only the top-level directory was in the following state (key points).

```text
user:wazuh-collector:r-x
mask::---
effective:---
```

There is an ACL entry, but the mask is `---`, so it cannot actually be entered.

## Chapter 2: Fixing the Search

### 2.1 The Current Code

```bash
sed -n '300,365p' /usr/local/lib/wazuh-collector/collector.py
```

In the following part, `find_inode_file()` included every directory, hidden ones too, in what it searched.

```text
if entry.is_dir(follow_symlinks=False):
    pending.append(Path(entry.path))
    continue
```

Check what is directly under `alerts` and the shape of the real locations.

```bash
find /var/ossec/logs/alerts -mindepth 1 -maxdepth 1 -type d -printf '%f\n'
```

```bash
find /var/ossec/logs/alerts/2026 -type d -printf '%P\n' | head -50
```

There were two directories directly under it, `2026` and `.acl-inheritance-test.bkv8vd`, and the real location was `2026/Nov`. Even with hidden directories excluded, the real files can be found.

```bash
stat -c '%A %U:%G %s bytes %y %n' /usr/local/lib/wazuh-collector/collector.py && python3 -m py_compile /usr/local/lib/wazuh-collector/collector.py
```

```bash
sed -n '365,455p' /usr/local/lib/wazuh-collector/collector.py
```

`open_initial_file()` stops startup if the previous file is not found. This safety measure is not changed. What changes is the following form.

```text
if entry.is_dir(follow_symlinks=False):
    if entry.name.startswith("."):
        continue
    pending.append(Path(entry.path))
    continue
```

### 2.2 Backup

Without touching the running Collector, back up the file.

```bash
cp -a /usr/local/lib/wazuh-collector/collector.py /usr/local/lib/wazuh-collector/collector.py.pre-hidden-dir-fix-20261121 && sha256sum /usr/local/lib/wazuh-collector/collector.py /usr/local/lib/wazuh-collector/collector.py.pre-hidden-dir-fix-20261121
```

Confirm that the two SHA-256 values are the same.

### 2.3 The Fix

Rewrite only if there is exactly one place to fix.

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/usr/local/lib/wazuh-collector/collector.py")
source = path.read_text()

old = '''                if entry.is_dir(follow_symlinks=False):
                    pending.append(Path(entry.path))
                    continue
'''

new = '''                if entry.is_dir(follow_symlinks=False):
                    if entry.name.startswith("."):
                        continue
                    pending.append(Path(entry.path))
                    continue
'''

count = source.count(old)
if count != 1:
    raise SystemExit(f"安全確認失敗: 対象コードが {count} 件。変更していません")

path.write_text(source.replace(old, new, 1))
print("修正完了: 隠しディレクトリを探索対象から除外")
PY
```

```bash
python3 -m py_compile /usr/local/lib/wazuh-collector/collector.py && diff -u /usr/local/lib/wazuh-collector/collector.py.pre-hidden-dir-fix-20261121 /usr/local/lib/wazuh-collector/collector.py
```

The difference was only two lines: `if entry.name.startswith("."):` and `continue`.

### 2.4 Testing as the Collector's User

Extract only `find_inode_file()` and, as the Collector's user, have it search for an inode that does not exist. It has succeeded if it returns `None` (not found) and finishes normally even though it cannot enter the hidden directory. No DB connection is made.

```bash
runuser -u wazuh-collector -- python3 - <<'PY'
import ast
import os
from pathlib import Path

source_path = "/usr/local/lib/wazuh-collector/collector.py"
source = Path(source_path).read_text()
tree = ast.parse(source)

function = next(
    node for node in tree.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "find_inode_file"
)

namespace = {
    "os": os,
    "Path": Path,
    "ALERT_DIR": Path("/var/ossec/logs/alerts"),
}

exec(compile(ast.Module(body=[function], type_ignores=[]), source_path, "exec"), namespace)

result = namespace["find_inode_file"](9223372036854775807)

print("RESULT:", result)
print("TEST: PASS" if result is None else "TEST: UNEXPECTED MATCH")
PY
```

The result was `TEST: PASS`.

## Chapter 3: Applying the Fix

### 3.1 Restarting

```bash
systemctl show wazuh-collector.service -p MainPID -p NRestarts -p ActiveState -p SubState
```

The current process (PID 13542) is running the code from before the fix. Restart it to load the new code. Collection stops briefly during the restart, but it continues from the position in the state file.

```bash
systemctl restart wazuh-collector.service
```

```bash
systemctl show wazuh-collector.service -p MainPID -p NRestarts -p ActiveState -p SubState
```

At build time it was PID 14203, `NRestarts=0`, `active` and `running`.

```bash
journalctl -u wazuh-collector.service -n 30 --no-pager
```

```bash
journalctl -u wazuh-collector.service --since "2026-11-21 11:09:00" --no-pager
```

`Resuming current alert file` was present, and no `PermissionError` for the hidden directory appeared.

### 3.2 There Is No PostgreSQL Connection Log

```bash
systemctl status wazuh-collector.service --no-pager -l
```

```bash
sed -n '500,570p' /usr/local/lib/wazuh-collector/collector.py
```

The Collector connects to PostgreSQL **only when an unread line arrives**. If it has read to the end and no new alerts have arrived, no connection log appears.

```bash
python3 - <<'PY'
import json, os
state_path = "/var/lib/wazuh-collector/state.json"
alert_path = "/var/ossec/logs/alerts/alerts.json"

with open(state_path) as f:
    state = json.load(f)

st = os.stat(alert_path)

print("STATE_INODE:", state["inode"])
print("STATE_OFFSET:", state["offset"])
print("CURRENT_INODE:", st.st_ino)
print("CURRENT_SIZE:", st.st_size)
print("INODE_MATCH:", state["inode"] == st.st_ino)
print("OFFSET_AT_EOF:", state["offset"] == st.st_size)
print("UNPROCESSED_BYTES:", max(0, st.st_size - state["offset"]) if state["inode"] == st.st_ino else "inode mismatch")
PY
```

```bash
stat -c 'ALERT_FILE_SIZE=%s MODIFIED=%y INODE=%i' /var/ossec/logs/alerts/alerts.json && journalctl -u wazuh-collector.service --since "2026-11-21 11:09:11 UTC" --no-pager
```

Nothing was unread, and `alerts.json` had not been updated since before the restart.

### 3.3 Checking the Connection

As the Collector's user, using the same connection settings as the Collector (`DB_CONFIG`), run only `SELECT 1`. Connection information is not shown.

```bash
runuser -u wazuh-collector -- python3 - <<'PY'
import importlib.util
from pathlib import Path

path = Path("/usr/local/lib/wazuh-collector/collector.py")
spec = importlib.util.spec_from_file_location("collector_check", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

try:
    with module.psycopg.connect(**module.DB_CONFIG) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()[0]
    print("POSTGRESQL_READ_ONLY_TEST:", "PASS" if result == 1 else "FAIL")
except Exception as error:
    print("POSTGRESQL_READ_ONLY_TEST: FAIL")
    print("ERROR_TYPE:", type(error).__name__)
PY
```

The result was `POSTGRESQL_READ_ONLY_TEST: PASS`. After a while, look at the log once new alerts have arrived.

```bash
journalctl -u wazuh-collector.service --since "2026-11-21 11:09:11 UTC" --no-pager | grep -E 'ERROR|WARNING|PostgreSQL connection established|Alert processing failed|Duplicate alert skipped'
```

```text
Nov 21 11:12:08
INFO PostgreSQL connection established
```

> **Run on: postgresql** (OS user `postgres`. You are already logged in as `postgres`, so `sudo` is not used)

```bash
psql -d security_workbench -c "SELECT COUNT(*) AS recent_events, COUNT(DISTINCT event_id) AS distinct_events, MAX(ingested_at) AS latest_ingested_at FROM incident.alert_events WHERE ingested_at >= TIMESTAMPTZ '2026-11-21 11:09:11+00';"
```

Three events (three distinct `event_id`s) had been saved after the restart.

## Chapter 4: Checking the Rotation Processing

> **Run on: VM 220**

```bash
sed -n '550,735p' /usr/local/lib/wazuh-collector/collector.py
```

| Situation | What the Collector does |
|---|---|
| An ordinary line | Saves it to PostgreSQL, then saves the position |
| Cannot reach PostgreSQL / save fails | Goes back to the start of the line and retries |
| The end of the file is a partial line | Waits for the switch |
| The file switches while a line is partial | Discards that line and switches to the new inode |
| The file switches after reading to the end | Switches to the new inode |
| Saving the position fails | Retries without switching to the new file |

```bash
grep -n -A75 -B10 '^def save_state\|^def load_state\|^def read_alert_line' /usr/local/lib/wazuh-collector/collector.py
```

`save_state()` writes to a temporary file in the same directory with `0600`, calls `flush()` and `fsync()`, swaps it in with `os.replace()`, and also calls `fsync()` on the directory. The order of processing is as follows.

```text
PostgreSQL INSERT
       ↓
トランザクション確定
       ↓
save_state(inode, offset)
```

```bash
grep -n -A45 -B15 'INSERT_SQL\|event_id' /usr/local/lib/wazuh-collector/collector.py | head -120
```

`event_id` is the Wazuh alert's `alert["id"]`, and only duplicates (SQLSTATE `23505`) are treated as "already present". The position is advanced only after the INSERT is committed, so even if the Collector stops between saving the event and saving the position and re-reads the same line, nothing is inserted twice.

## Closing Notes

In Part 30 we made the Collector no longer stop at the hidden directory.

| Item | Result |
|---|---|
| What was fixed | `find_inode_file()` no longer searches directories whose names start with `.` (2 lines) |
| Backup | `collector.py.pre-hidden-dir-fix-20261121` |
| Test | `TEST: PASS` as the Collector's user |
| Applied | Restarted with `NRestarts=0`; saving to PostgreSQL also confirmed |
| Hidden directory | Not deleted (the Collector no longer stops even though it remains) |

Next, we check how Wazuh switches its logs (rotation). This continues in Part 31 of Volume 3.

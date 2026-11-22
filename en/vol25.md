---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 2"
subtitle: "Part 25: Setting Where the Audit Log Is Saved"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

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

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **security-core VM 220 (root)**.
- The output of `javap` is long, so only the key points of the results are given.
- Two of the build conversations, (109) and (112), were not available. The decisions made in between (such as approving the configuration policy) are written to the extent that they can be read from the surrounding conversations.

# Chapter 1: Checking the Configuration File

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

# Chapter 2: How internal_opensearch Works

## 2.1 The Target Index

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

## 2.2 When Saving Fails

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

## 2.3 How the Spare Output Destination Is Chosen

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

# Chapter 3: What Is Recorded

## 3.1 Request Bodies and Headers

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c org.opensearch.security.auditlog.impl.AuditMessage
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c org.opensearch.security.auditlog.impl.AuditMessage | grep -n -B 5 -A 35 -E 'addRestHeaders|addRestParams|addPath|addTransportHeaders'
```

- If `log_request_body` is enabled, the body of REST requests is turned into JSON and put in `audit_request_body`
- Only some Security APIs that handle passwords replace the body with `__SENSITIVE__`. Other bodies (search conditions, data being added or updated, etc.) are recorded as they are
- If `exclude_sensitive_headers` is enabled, the `Authorization` header is not recorded

## 3.2 Filter Defaults

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c 'org.opensearch.security.auditlog.config.AuditConfig$Filter'
```

```bash
/usr/share/wazuh-indexer/jdk/bin/javap -classpath '/usr/share/wazuh-indexer/plugins/opensearch-security/opensearch-security-2.19.6.0.jar' -p -c 'org.opensearch.security.auditlog.config.AuditConfig$Filter$FilterEntries'
```

- The default value of `log_request_body` is **true**
- The default value of `exclude_sensitive_headers` is true
- `ignore_headers`, `ignore_url_params`, `ignore_requests` and `ignore_users` can exclude things from records using wildcards

## 3.3 Audit Categories

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

## 3.4 The Names of the Setting Keys

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

# Chapter 4: Setting It and Restarting

## 4.1 The Current Value

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

## 4.2 Backup

```bash
cp -a /etc/wazuh-indexer/opensearch.yml "/etc/wazuh-indexer/opensearch.yml.pre-audit-$(date +%Y%m%d-%H%M%S)"
```

```bash
bash -c 'f=$(ls -1t /etc/wazuh-indexer/opensearch.yml.pre-audit-* | head -n 1); echo "BACKUP: $f"; stat -c "owner=%U:%G mode=%a size=%s" "$f"; cmp -s /etc/wazuh-indexer/opensearch.yml "$f" && echo "CONTENT_MATCH: yes" || echo "CONTENT_MATCH: no"'
```

The backup at build time was `opensearch.yml.pre-audit-20261121-082142`, and it matched the original file.

## 4.3 Adding Two Lines

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

## 4.4 Restarting

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

## 4.5 Was It Applied?

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

# Closing Notes

In Part 25 we added the following settings to `/etc/wazuh-indexer/opensearch.yml` and restarted the Indexer.

| Setting | Value | Result |
|---|---|---|
| `plugins.security.audit.type` | `internal_opensearch` | The audit log is saved inside the Indexer (`security-auditlog-YYYY.MM.dd`) |
| `plugins.security.audit.config.log_request_body` | `false` | Not yet reflected in the audit API |

The backup is `/etc/wazuh-indexer/opensearch.yml.pre-audit-*`.

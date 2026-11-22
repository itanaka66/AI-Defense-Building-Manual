---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 2"
subtitle: "Part 26: Not Recording Request Bodies in the Audit Log"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 26 of Volume 2 of the "AI Autonomous Cyber Defense System Build Manual". In Part 25 we wrote `plugins.security.audit.config.log_request_body: false` in `opensearch.yml` and restarted the Indexer, but the audit API still returned `log_request_body: true`. Here we find the reason in the code, and **set only `log_request_body` to `false` through the audit API (PATCH)**.

The reason turned out to be as follows.

- The audit settings are also stored in the document `audit` in the Indexer's internal index `.opendistro_security` (dynamic configuration)
- At startup, the Indexer uses this document **if it exists**, and builds the settings from `opensearch.yml` **only if it does not**
- In this environment the document `audit` exists, so `log_request_body: false` in `opensearch.yml` is not used

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **security-core VM 220 (root)**.
- The Indexer is accessed with the administrator certificate (`admin.pem`, `admin-key.pem`). The password of the `admin` user is not used.
- The output of `javap` is long, so only the key points of the results are given.

# Chapter 1: Where the Settings Are Read From

## 1.1 Node Settings and the File

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

## 1.2 How AuditConfig Is Created

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

## 1.3 ConfigurationRepository

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

# Chapter 2: Checking Whether the Document Exists

## 2.1 The Administrator Certificate

Connect with the administrator certificate, without using the `admin` user's password (even if it is unknown, it is not reset).

```bash
find /etc/wazuh-indexer -maxdepth 3 -type f \( -iname '*admin*.pem' -o -iname '*root-ca*.pem' -o -iname '*admin*.crt' -o -iname '*admin*.key' \) -printf '%p\n'
```

```bash
openssl x509 -in /etc/wazuh-indexer/certs/admin.pem -noout -subject -issuer -dates -ext extendedKeyUsage
```

At build time the CN was `admin`, valid from November 17, 2026 to November 14, 2036.

## 2.2 The Document audit

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

## 2.3 The Values in the Audit API

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

# Chapter 3: Changing It Through the Audit API

## 3.1 Checking How to Change It

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

## 3.2 The Current Configuration

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

## 3.3 PATCH

Set only `log_request_body` to `false`. No other audit settings are touched. No Indexer restart is needed.

```bash
curl -sS --cacert /etc/wazuh-indexer/certs/root-ca.pem --cert /etc/wazuh-indexer/certs/admin.pem --key /etc/wazuh-indexer/certs/admin-key.pem -X PATCH 'https://127.0.0.1:9200/_plugins/_security/api/audit' -H 'Content-Type: application/json' -d '[{"op":"replace","path":"/config/audit/log_request_body","value":false}]' -w '\nHTTP_STATUS:%{http_code}\n'
```

At build time it returned `Resource updated.` and `HTTP_STATUS:200`.

## 3.4 Confirming the Change

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

# Closing Notes

In Part 26 we found where the audit settings are read from, and set `log_request_body` to `false` with a PATCH to the audit API (without a restart).

| Where the setting lives | Role |
|---|---|
| `opensearch.yml` | Output destination (`plugins.security.audit.type`); initial values when there is no audit document |
| Document `audit` in `.opendistro_security` | The audit settings in effect; changed through the audit API (PATCH) |

In the next part, we confirm that the audit log is actually being saved and that bodies are not recorded.

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

⟦C0⟧

⟦C1⟧

At build time the file was `wazuh-indexer:wazuh-indexer` with `660`, 2152 bytes. These permissions are not changed.

⟦C2⟧

There is no audit output destination specified, and the Indexer listens only on `127.0.0.1`. The TLS, authentication and network settings are not touched.

# Chapter 2: How internal_opensearch Works

## 2.1 The Target Index

⟦C3⟧

In Security plugin 2.19.6.0, `internal_opensearch` saves into a per-day **`security-auditlog-YYYY.MM.dd`** if no index name is specified (not `auditlog6`).

⟦C4⟧

- Audit events are written into the Indexer with `Client.prepareIndex()`
- The contents of the audit message (`AuditMessage.getAsMap()`) are saved as they are
- If writing fails, `Unable to index audit log` appears in the error log

## 2.2 When Saving Fails

⟦C5⟧

`AuditLogSink.store()` processes in the following order.

1. Save to the main output destination
2. If that fails, save to the spare (fallback) output destination
3. If that also fails, write the full audit message to `System.err` (standard error)

⟦C6⟧

The spare `DebugSink` writes the full audit message to Log4j at `INFO`.

⟦C7⟧

| Item | Current setting |
|---|---|
| rootLogger | `INFO` |
| Console output | Enabled |
| File output | Enabled (`/var/log/wazuh-indexer/`, every 128 MB, up to 2 GB in total) |

In other words, if saving to the main output destination fails, the full audit message may appear in the normal logs.

## 2.3 How the Spare Output Destination Is Chosen

⟦C8⟧

| Spare setting | Behavior |
|---|---|
| None | Creates a `DebugSink` automatically |
| `debug` | Writes the full text to Log4j |
| `noop` | Discards audit messages |

⟦C9⟧

`NoopSink` outputs nothing and returns "success". It prevents leaks into logs, but it hides the fact that audit records were lost, so it is not adopted here (the spare is left at its default).

# Chapter 3: What Is Recorded

## 3.1 Request Bodies and Headers

⟦C10⟧

⟦C11⟧

- If `log_request_body` is enabled, the body of REST requests is turned into JSON and put in `audit_request_body`
- Only some Security APIs that handle passwords replace the body with `__SENSITIVE__`. Other bodies (search conditions, data being added or updated, etc.) are recorded as they are
- If `exclude_sensitive_headers` is enabled, the `Authorization` header is not recorded

## 3.2 Filter Defaults

⟦C12⟧

⟦C13⟧

- The default value of `log_request_body` is **true**
- The default value of `exclude_sensitive_headers` is true
- `ignore_headers`, `ignore_url_params`, `ignore_requests` and `ignore_users` can exclude things from records using wildcards

## 3.3 Audit Categories

⟦C14⟧

⟦C15⟧

⟦C16⟧

`AuditLogImpl` checks whether auditing is enabled and then leaves creating the event to its parent class `AbstractAuditLog`.

⟦C17⟧

⟦C18⟧

⟦C19⟧

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

⟦C20⟧

⟦C21⟧

⟦C22⟧

⟦C23⟧

The settings are added at the end of the file. Check in the code the key for the setting that stops recording request bodies.

⟦C24⟧

⟦C25⟧

The old-style key was `opendistro_security.audit.log_request_body`.

⟦C26⟧

`fromSettingBoolean()` looks at the new-style key first and, if it is absent, the old-style key. Check how the new-style names are formed.

⟦C27⟧

⟦C28⟧

`getKeyWithNamespace()` used the prefix `plugins.security.audit.config.`. The setting that stops recording request bodies is therefore as follows.

⟦C29⟧

The output destination setting is in a different namespace.

⟦C30⟧

# Chapter 4: Setting It and Restarting

## 4.1 The Current Value

⟦C31⟧

`log_request_body` was `True`.

## 4.2 Backup

⟦C32⟧

⟦C33⟧

The backup at build time was `opensearch.yml.pre-audit-20261121-082142`, and it matched the original file.

## 4.3 Adding Two Lines

Confirm that the same keys do not already exist.

⟦C34⟧

The two lines to add are as follows.

⟦C35⟧

⟦C36⟧

Confirm that the difference from the backup is only one comment line and two setting lines. Replace the file name with the name of your own backup.

⟦C37⟧

⟦C38⟧

## 4.4 Restarting

Record the state before the restart.

⟦C39⟧

During the restart, the Indexer API, Wazuh searches and the Relay are temporarily unavailable.

⟦C40⟧

⟦C41⟧

At build time it was `active` and `running`, with the new PID 51059 and `NRestarts=0`.

## 4.5 Was It Applied?

⟦C42⟧

At build time it still showed `LOG_REQUEST_BODY: True`. The `false` written in the configuration file is not reflected in the settings returned by the audit API. The next part investigates and fixes the reason.

# Closing Notes

In Part 25 we added the following settings to `/etc/wazuh-indexer/opensearch.yml` and restarted the Indexer.

| Setting | Value | Result |
|---|---|---|
| `plugins.security.audit.type` | `internal_opensearch` | The audit log is saved inside the Indexer (`security-auditlog-YYYY.MM.dd`) |
| `plugins.security.audit.config.log_request_body` | `false` | Not yet reflected in the audit API |

The backup is `/etc/wazuh-indexer/opensearch.yml.pre-audit-*`.

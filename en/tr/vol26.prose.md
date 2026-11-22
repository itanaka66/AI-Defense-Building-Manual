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

⟦C0⟧

None of the audit settings appeared in the node settings API (the fact that they do not appear does not by itself mean they are not loaded).

⟦C1⟧

The file has the two lines, and its owner and permissions have not changed.

## 1.2 How AuditConfig Is Created

⟦C2⟧

⟦C3⟧

`AuditConfig.from(Settings)` builds the audit settings from the node settings (`opensearch.yml`).

⟦C4⟧

`setConfig()` uses the settings it receives as they are. `AuditLogImpl` does not change the value back to `true`.

⟦C5⟧

It is not called directly from `OpenSearchSecurityPlugin`. Look for the classes that handle the configuration.

⟦C6⟧

`ConfigurationRepository` loads the dynamic configuration, and `AuditApiAction` is the audit API.

## 1.3 ConfigurationRepository

⟦C7⟧

⟦C8⟧

`setupAuditConfigurationIfAny()` branches on whether `.opendistro_security` contains an audit configuration document.

| Document | Behavior |
|---|---|
| Exists | Does not call `AuditConfig.from(settings)` (uses the settings in the document) |
| Does not exist | Builds the settings from `opensearch.yml` and uses them |

⟦C9⟧

⟦C10⟧

⟦C11⟧

If the document `audit` can be read, `isAuditConfigDocPresentInIndex = true`; otherwise it is set to `false` and the initial settings are built from `opensearch.yml`.

⟦C12⟧

The log had no record of which path was taken.

# Chapter 2: Checking Whether the Document Exists

## 2.1 The Administrator Certificate

Connect with the administrator certificate, without using the `admin` user's password (even if it is unknown, it is not reset).

⟦C13⟧

⟦C14⟧

At build time the CN was `admin`, valid from November 17, 2026 to November 14, 2036.

## 2.2 The Document audit

Without fetching the document's contents, check only whether it exists.

⟦C15⟧

The result at build time was as follows: the document existed.

⟦C16⟧

This explains why the change to `opensearch.yml` was not reflected. Note that `audit` in this document was stored not as JSON but as a string in an internal format (940 characters), so no values were extracted from it here. The values are checked through the audit API.

## 2.3 The Values in the Audit API

⟦C17⟧

It showed `log_request_body = True`. In the API response, the settings are directly under `audit` beneath `config`.

⟦C18⟧

# Chapter 3: Changing It Through the Audit API

## 3.1 Checking How to Change It

⟦C19⟧

⟦C20⟧

- The audit API accepts `PUT /_plugins/_security/api/audit/config` and `PATCH /_plugins/_security/api/audit`
- Changes are possible only when reloading of the audit configuration (hot reload) is enabled (it is enabled because the document exists)

⟦C21⟧

⟦C22⟧

| Method | Behavior |
|---|---|
| `PUT` | Replaces the whole configuration (not used this time) |
| `PATCH` | Reads the current configuration and applies a JSON Patch (`add`, `replace`, `remove`). Only the changed items are validated |

⟦C23⟧

The whole configuration after the change is also validated. Other settings, such as the categories not recorded for REST and Transport, must remain as they are.

## 3.2 The Current Configuration

⟦C24⟧

| Item | Current value |
|---|---|
| `log_request_body` | `true` |
| `exclude_sensitive_headers` | `true` |
| `enable_rest`, `enable_transport` | `true` |
| Categories not recorded (REST, Transport) | `AUTHENTICATED`, `GRANTED_PRIVILEGES` |
| `ignore_users` | 1 entry |

Check the location for the JSON Patch (JSON Pointer) and any read-only items.

⟦C25⟧

It showed `readonly_paths: []` (no read-only items). The location to change is `/config/audit/log_request_body`.

## 3.3 PATCH

Set only `log_request_body` to `false`. No other audit settings are touched. No Indexer restart is needed.

⟦C26⟧

At build time it returned `Resource updated.` and `HTTP_STATUS:200`.

## 3.4 Confirming the Change

⟦C27⟧

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

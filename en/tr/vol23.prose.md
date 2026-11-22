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

⟦C0⟧

At build time no files that looked like audit logs were found.

## 1.2 audit.yml

⟦C1⟧

⟦C2⟧

| Setting | Value |
|---|---|
| Auditing of the REST API | Enabled |
| Auditing of the Transport API | Enabled |
| Recording changes to internal security configuration (`internal_config`) | Enabled |
| Recording changes to external configuration files (`external_config`) | Disabled |
| Recording request bodies (`log_request_body`) | Enabled |
| Events for successful authentication and granted privileges | Not recorded |

`log_request_body: true` is a setting that also records the bodies of REST API requests. The handling of these records needs care (author's notes, item 23-A).

⟦C3⟧

No output destination dedicated to audit logs can be found in `log4j2.properties`.

⟦C4⟧

Read it as YAML and show the items related to the output method.

⟦C5⟧

Auditing is enabled, but the output method is not written in `audit.yml`.

## 1.3 The Indexer's Operational Logs

Show them with strings that look like secrets masked.

⟦C6⟧

At build time no records about auditing or role changes were found.

# Chapter 2: Checking Roles and Users with the Administrator Certificate

## 2.1 ai-defense-reader Cannot View the List

⟦C7⟧

It returned `HTTP_STATUS: 403`. A user that only reads alerts does not need permission to view the list of indices. Rather than adding permissions, check from the administrator's side.

## 2.2 The Administrator Certificate

Show only file names and permissions.

⟦C8⟧

⟦C9⟧

`admin.pem` and `admin-key.pem` are owned by `wazuh-indexer` with permissions `400`. The following programs make read-only queries to the Indexer with this certificate.

## 2.3 The Definition of ai_defense_alerts_read

⟦C10⟧

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

⟦C11⟧

`own_index` is a standard role (`reserved: true`) that allows `indices_all` on an index with the same name as the user (`${user_name}`), and also allows `cluster_composite_ops`. So check whether an index named `ai-defense-reader` exists.

⟦C12⟧

It returned `INDEX_EXISTS: no` (`404`). At present there is no index that `own_index` can touch. However, if an index with this name were ever created, `ai-defense-reader` would be able to perform every operation on it (author's notes, item 23-B).

## 2.5 The User Definition

Password hashes are not shown.

⟦C13⟧

At build time it was `reserved: false`, `backend_roles` and `attributes` were empty, and `description` was `Read-only access to Wazuh alert indices for AI Defense Manager`.

# Chapter 3: Looking for Where the Audit Log Is Saved

## 3.1 Indices

⟦C14⟧

Only `.opendistro_security` (the internal index holding the security configuration) and `wazuh-states-*` (Wazuh state and asset information) appeared. No index has `audit` in its name.

## 3.2 The Running Audit Configuration

⟦C15⟧

The running audit configuration matched `audit.yml` on disk (auditing enabled, recording of internal configuration changes enabled, recording of request bodies enabled, sensitive headers excluded from records).

## 3.3 Log Files

⟦C16⟧

⟦C17⟧

There is a normal log (`wazuh-cluster.log`) and a JSON-format log (`wazuh-cluster_server.json`), both `640 wazuh-indexer:wazuh-indexer`. There is no file dedicated to auditing.

In the JSON log, count only the number of lines containing relevant words (the text is not shown).

⟦C18⟧

| Word | Lines |
|---|---:|
| `audit` | 0 |
| `compliance` | 0 |
| `ai-defense-reader` | 3 |
| `ai_defense_alerts_read` | 3 |

## 3.4 What Are Those Three Lines?

Extract only metadata such as time and level.

⟦C19⟧

⟦C20⟧

⟦C21⟧

All three lines were logs related to OpenSearch Security's privilege evaluation.

| Component | Level | Count |
|---|---|---:|
| `RestApiPrivilegesEvaluator` | INFO | 1 |
| `PrivilegesEvaluatorImpl` | INFO | 1 |
| `AbstractApiAction` | ERROR | 1 |

## 3.5 Classifying the ERROR Line

Without showing the text, check only for the name of an exception class, words indicating permission denial or authentication failure, and an HTTP status.

⟦C22⟧

⟦C23⟧

⟦C24⟧

At build time none of these methods identified the cause of the ERROR (no exception class name, permission denial, authentication failure or HTTP status was found). It may be the record of `ai-defense-reader` getting `403` when trying to read role definitions in Part 22, 3.3, but this has not been confirmed (author's notes, item 23-C).

## 3.6 The Audit Output Method

⟦C25⟧

`opensearch.yml` has no setting for the audit output method (`plugins.security.audit.type`).

⟦C26⟧

⟦C27⟧

The example settings file contains `plugins.security.audit.type: internal_opensearch`, which saves into the Indexer. However, this is an example and is not necessarily the actual setting.

Check the settings of the running node.

⟦C28⟧

It returned `HTTP_STATUS: 200` with the content `{}` (no explicit setting).

Check whether the Indexer process's startup arguments include anything related to auditing (not all arguments are shown).

⟦C29⟧

The process was found, but there were no arguments related to auditing.

## 3.7 Plugins

⟦C30⟧

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

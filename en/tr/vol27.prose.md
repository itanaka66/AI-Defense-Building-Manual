---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 2"
subtitle: "Part 27: Confirming That the Audit Log Is Saved"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 27 of Volume 2 of the "AI Autonomous Cyber Defense System Build Manual". In Part 25 we set the audit log's output destination, and in Part 26 we stopped request bodies from being recorded. Here we confirm the following **using reads only**, without changing settings.

1. The audit log index (`security-auditlog-YYYY.MM.dd`) has been created and events are being saved
2. The saved events contain no request bodies or authentication headers
3. The audit settings are stored in `.opendistro_security` and the design loads them again after a restart

The "values" of bodies and headers are not shown; only field names, counts, lengths and shapes are examined.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **security-core VM 220 (root)**.
- The index name `security-auditlog-2026.11.21` is from the day of the build. Replace it with the date in your environment.

# Chapter 1: Has the Destination Been Created?

## 1.1 The Startup Log

⟦C0⟧

At build time nothing was shown. The absence of a log line does not by itself mean that the output destination was not created.

## 1.2 The Audit Log Index

⟦C1⟧

At build time `security-auditlog-2026.11.21` existed, holding 24 events and 103.7 KB. The audit log is being saved inside the Indexer.

## 1.3 Why It Is yellow

The index's state was `yellow`. Check the shards.

⟦C2⟧

| Shard | State |
|---|---|
| Primary (p) | `STARTED` (node-1) |
| Replica (r) | `UNASSIGNED` (`INDEX_CREATED`) |

⟦C3⟧

There is one node, all 36 primary shards are running, and the only unassigned shard is this index's one replica. With only one node, there is nowhere to place the replica. This is not a save failure. The number of replicas is not changed, and the state is left `yellow` (author's notes, item 27-A).

# Chapter 2: What Is Being Saved

## 2.1 One Sample

⟦C4⟧

This one event had no body field; it held information such as the REST method, path, source and user. For headers and URL parameters, look only at the names.

⟦C5⟧

The headers were only `Accept`, `Host` and `User-Agent`, and the only parameter was `filter_path`; there was no `Authorization` or `Cookie`.

## 2.2 All Events

Count body-like fields, authentication headers, header and parameter names, and categories.

⟦C6⟧

At build time 86 events were examined. There were zero authentication headers, but **15 events had a body-like field**. Examine these 15 in detail.

⟦C7⟧

All 15 had the category `COMPLIANCE_INTERNAL_CONFIG_READ` (reading internal configuration), and the field was `audit_request_body`.

## 2.3 What audit_request_body Really Is

Without showing the values, examine only their shape.

⟦C8⟧

All 15 were 25-character strings. Compare their contents with hashes.

⟦C9⟧

All 15 had the same value. Examine the kinds of characters and the shape.

⟦C10⟧

It could be read as JSON. Look only at the key names and types.

⟦C11⟧

The shape was as follows (values masked).

⟦C12⟧

⟦C13⟧

The `field_names` array contained a single five-character string, and all 15 had the same shape. This is considered to be not the body of an HTTP request but information about field names when the internal configuration was read.

## 2.4 Counts by Category

⟦C14⟧

| Category | Count | With `audit_request_body` |
|---|---:|---:|
| `COMPLIANCE_INTERNAL_CONFIG_READ` | 15 | 15 |
| `COMPLIANCE_INTERNAL_CONFIG_WRITE` | 1 | 0 |
| `FAILED_LOGIN` | 8 | 0 |
| `INDEX_EVENT` | 62 | 0 |

Ordinary events (`FAILED_LOGIN`, `INDEX_EVENT`) have no body field.

⟦C15⟧

The 15 events were from 2026-11-21 08:27:45 to 08:56:05 (UTC).

# Chapter 3: Is the Design One in Which the Settings Persist?

## 3.1 The Current Settings

⟦C16⟧

It still showed `LOG_REQUEST_BODY: False`.

## 3.2 The Configuration Document

⟦C17⟧

At build time it showed `found: true` and `_version: 2`. The change made by PATCH is saved as a document.

## 3.3 Loading at Startup

⟦C18⟧

⟦C19⟧

⟦C20⟧

⟦C21⟧

1. The settings are saved in the document `audit` in `.opendistro_security`
2. At startup, `ConfigurationLoaderSecurity7` reads the document and sets a flag saying "the document exists"
3. `ConfigurationRepository` applies the settings read and enables reloading of the audit configuration (hot reload)

Because of this design, the settings changed with PATCH are used after a restart as well (this was not confirmed by actually restarting).

At build time we also searched the code for the class that calls `AuditLogImpl.setConfig()` when the settings change, but did not pin it down and stopped as it was of low necessity. Those steps are not included in this book.

# Chapter 4: Confirming with Aggregations

## 4.1 The Aggregation Does Not Work

⟦C22⟧

⟦C23⟧

The search returned `HTTP 200`, and the index had 88 events. However, aggregating by `audit_category` returned no results. Look at the error in the response.

⟦C24⟧

`audit_category` is of type `text`, and `fielddata`, which the aggregation needs, is disabled, so the aggregation failed on every shard. Rather than enabling `fielddata` (which uses a lot of memory), check whether a `keyword`-type field exists.

⟦C25⟧

`audit_category.keyword` and `audit_request_body.keyword` existed.

## 4.2 Aggregating with keyword

⟦C26⟧

⟦C27⟧

| Category | Count | With a body field |
|---|---:|---:|
| `INDEX_EVENT` | 63 | 0 |
| `COMPLIANCE_INTERNAL_CONFIG_READ` | 17 | 17 |
| `FAILED_LOGIN` | 8 | 0 |
| `COMPLIANCE_INTERNAL_CONFIG_WRITE` | 1 | 0 |

## 4.3 The Shape of the 17

⟦C28⟧

All 17 were 25-character JSON whose only key was `field_names`.

## 4.4 Matching Settings and Logs

⟦C29⟧

| Item | Value |
|---|---|
| Auditing | Enabled |
| REST and Transport auditing | Enabled |
| Recording request bodies | `false` |
| Excluding sensitive headers | `true` |
| Compliance | Enabled (metadata only for both reads and writes) |

# Closing Notes

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

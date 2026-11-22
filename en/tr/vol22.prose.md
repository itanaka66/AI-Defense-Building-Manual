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

⟦C0⟧

At build time nothing was shown. VM 230 is not a Wazuh agent; it receives alerts by calling the Relay's `/v1/alerts` over HTTPS.

## 1.2 The Code and Settings That Call the Relay

⟦C1⟧

⟦C2⟧

The following was confirmed.

- TLS is verified with the CA certificate
- The Bearer token is read from a file and never appears in code or logs
- Redirects are not followed; there is a timeout (1–60 seconds)
- At most 100 alerts are fetched, over at most 24 hours
- `full_log` and arbitrary `data` are not taken in

## 1.3 Permissions of the Connection Details

⟦C3⟧

| Target | Permissions |
|---|---|
| `/etc/ai-defense-manager` | `755 root:root` |
| `credentials/` | `750 root:ai-defense` |
| `relay-ca.crt` | `640 root:ai-defense` |
| `relay-api.token` | `640 root:ai-defense` |

## 1.4 Checking TLS

Without sending the token, check only the certificate.

⟦C4⟧

At build time this was the self-signed CA certificate of `AI-Defense-Relay-Internal-CA`, valid from November 20, 2026 to November 17, 2036.

⟦C5⟧

It connected with TLS 1.3 and showed `Verification: OK`. The application connects by IP address, so also check that the certificate's SAN contains the IP address.

⟦C6⟧

If `IP Address:192.168.0.220` is present, it matches the URL in the settings (`https://192.168.0.220:8765/`).

# Chapter 2: The Relay Side

## 2.1 The Service

> **Run on: VM 220**

⟦C7⟧

At build time this was Ubuntu 24.04.5 LTS, `ai-defense-relay.service` was `active (running)`, and requests from VM 230 (`192.168.0.33`) were logged with `200`.

## 2.2 The Program

⟦C8⟧

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

⟦C9⟧

It runs as a dedicated user (not root), secrets are passed with `LoadCredential`, it has no privileges, the file system is read-only in principle, and there are limits on memory and number of tasks (Part 14, 5.1).

## 2.4 Listening

⟦C10⟧

| Service | Listening on |
|---|---|
| Relay | `192.168.0.220:8765` (only the designated IP) |
| Wazuh Indexer | `127.0.0.1:9200` (local only) |

Other hosts cannot connect to the Indexer directly; everything goes through the Relay.

⟦C11⟧

At build time UFW on VM 220 was disabled. The Relay listens only on the designated IP and the application also limits sources, but network-layer restriction is a separate matter. Enabling UFW could affect Wazuh's traffic and so on, so it is not changed here (author's notes, item 22-A).

## 2.5 Permissions of the Secrets

⟦C12⟧

`/etc/credstore` was `700 root:root`, and all files inside were `600 root:root`.

# Chapter 3: The Indexer's Read-Only User

## 3.1 Configuration Files on Disk

> **Run on: VM 220**

⟦C13⟧

⟦C14⟧

Neither showed anything. Check by displaying only the user names (password hashes are not shown).

⟦C15⟧

⟦C16⟧

⟦C17⟧

The on-disk `internal_users.yml`, `roles.yml` and `roles_mapping.yml` contain neither `ai-defense-reader` nor `ai_defense_alerts_read`. This is because in Part 13 these three files were not edited directly; instead, the merged files prepared in `/root` (`/root/ai_defense_merged_*.yml`) were sent to the Indexer with `securityadmin.sh`.

⟦C18⟧

HTTP authentication is Basic authentication with the internal user database (`type: intern`).

## 3.2 Authentication on the Running Indexer

Check whether the running Indexer, not the files on disk, authenticates `ai-defense-reader`. The password is read from `/etc/credstore` and not displayed.

⟦C19⟧

At build time it returned `HTTP_STATUS: 200`, and the roles were `own_index` and `ai_defense_alerts_read`.

## 3.3 The Management API Cannot Be Used

⟦C20⟧

It returned `HTTP_STATUS: 403`. A user that only reads alerts does not need administrative permission to view role definitions. No permissions are added.

## 3.4 Searching Alerts

Without fetching the body (`_source: False`), check only whether searching is allowed.

⟦C21⟧

## 3.5 Fields Returned

Specify the same 10 fields as the Relay, fetch one alert, and show only the names of the fields returned (values are not shown).

⟦C22⟧

At build time six were returned: `agent`, `decoder`, `location`, `manager`, `rule` and `timestamp`. `full_log`, `data`, `command`, `pwd` and `user` were not returned.

## 3.6 Configuration Files and Backups

⟦C23⟧

⟦C24⟧

Check whether the on-disk `internal_users.yml` defines this user, without showing password hashes.

⟦C25⟧

⟦C26⟧

⟦C27⟧

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

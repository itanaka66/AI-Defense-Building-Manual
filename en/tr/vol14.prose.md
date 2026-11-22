---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 14: Building the Alert Relay API (Relay)"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 14 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". Using the read-only Indexer user created in Part 13, we build inside security-core a "relay API (Relay)" that passes alerts to the AI Defense Manager (VM 230).

The Indexer is not exposed to other hosts; only the Relay accepts external connections, under the following conditions.

- It listens only on `192.168.0.220:8765` (HTTPS)
- Its server certificate is issued by an internal CA dedicated to the Relay
- Calls require a Bearer token
- It returns only the 10 fields decided in Part 13, 6.1. Search conditions and the maximum count are decided on the Relay side
- Secrets (the Indexer password, the token, private keys) are passed with systemd's `LoadCredential`

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Unless otherwise noted, everything is run on **security-core VM 220 (root)**.
- The contents of passwords, tokens and private keys appear neither on screen nor in this manual.

# Chapter 1: Certificates and the Token

## 1.1 Where They Are Kept

⟦C0⟧

⟦C1⟧

⟦C2⟧

## 1.2 The Internal CA

Create a certificate authority (CA) dedicated to the Relay. It is managed separately from the Indexer's CA.

⟦C3⟧

## 1.3 The Server Certificate

Because clients connect with `192.168.0.220`, put the IP address in the SAN.

⟦C4⟧

⟦C5⟧

Check the CA signature, the IP address, the usage, and that it matches the private key.

⟦C6⟧

## 1.4 The Bearer Token

Create the token that VM 230 uses when calling the Relay. It is not shown on screen.

⟦C7⟧

# Chapter 2: The Run-As User and Runtime Environment

## 2.1 A Dedicated User

⟦C8⟧

At build time this was systemd 255, so `LoadCredential` could be used.

⟦C9⟧

⟦C10⟧

⟦C11⟧

## 2.2 A Python Virtual Environment

The system Python on security-core does not have FastAPI or similar installed. We decided to build the Relay with the standard library only, and prepare a dedicated virtual environment.

⟦C12⟧

⟦C13⟧

Creating the virtual environment requires `python3.12-venv`.

⟦C14⟧

⟦C15⟧

⟦C16⟧

Create the directory and create the virtual environment as the dedicated user.

⟦C17⟧

In the original build, this command was run before `python3.12-venv` was installed, so only the directory was created; after installing it, only the creation of the virtual environment was redone.

⟦C18⟧

⟦C19⟧

⟦C20⟧

# Chapter 3: Secrets Passed by systemd

## 3.1 Where They Are Kept

The Relay runs as a dedicated user. Secrets stay in files readable only by root and are passed only at startup through systemd's `LoadCredential`.

⟦C21⟧

⟦C22⟧

## 3.2 Placing the Files

⟦C23⟧

⟦C24⟧

⟦C25⟧

⟦C26⟧

To verify the Relay's server certificate, use the Relay's own CA, not the Indexer's CA (in the original build, the first attempt verified with the Indexer's CA and failed). Place the Relay's CA as well.

⟦C27⟧

⟦C28⟧

| File (`/etc/credstore/`) | Contents |
|---|---|
| `ai-defense-indexer-password` | Password of the Indexer user `ai-defense-reader` |
| `ai-defense-indexer-ca` | The Indexer's CA certificate |
| `ai-defense-relay-token` | Bearer token |
| `ai-defense-relay-server-cert` | The Relay's server certificate |
| `ai-defense-relay-server-key` | The Relay's server private key |
| `ai-defense-relay-ca` | The Relay's CA certificate |

## 3.3 Checking the Listening State

⟦C29⟧

⟦C30⟧

# Chapter 4: The Relay Program

## 4.1 relay.py

An HTTPS server written with the Python standard library only.

- Connections are accepted only from VM 230 (`192.168.0.33`). Anything else gets `403`
- If `Authorization: Bearer <token>` does not match, it returns `401` (the comparison uses `hmac.compare_digest`)
- Only `GET /health` and `GET /v1/alerts` are available. `POST`, `PUT`, `DELETE` and `HEAD` return `405`
- The only parameters of `/v1/alerts` are `limit` (1–100, default 50) and `since_minutes` (1–1440, default 15)
- The query to the Indexer is built inside the Relay, and only the 10 defined fields are returned (strings up to 512 characters)
- If the Indexer's response exceeds 2 MB, nothing is returned

⟦C31⟧

## 4.2 Checking the Syntax

⟦C32⟧

⟦C33⟧

⟦C34⟧

⟦C35⟧

## 4.3 Stricter Checking of the Query String

`parse_qs(..., strict_parsing=True)` raises `ValueError` on a malformed query string. As it stands, processing would stop, so change it to return `400`.

⟦C36⟧

⟦C37⟧

In addition, limit the query string to 128 characters and the number of parameters to two.

⟦C38⟧

⟦C39⟧

# Chapter 5: The systemd Service

## 5.1 The Unit File

⟦C40⟧

Secrets are passed with `LoadCredential`, and the process's privileges are tightly restricted.

- `LoadCredential=<name>:<path>`: readable only at runtime as `$CREDENTIALS_DIRECTORY/<name>`
- `ProtectSystem=strict`, `ProtectHome=yes`: make the file system read-only and hide home directories
- `CapabilityBoundingSet=` (empty), `NoNewPrivileges=yes`: no privileges
- `RestrictAddressFamilies=AF_INET`: IPv4 communication only
- `MemoryMax=256M`, `TasksMax=32`: limits on the resources used

⟦C41⟧

⟦C42⟧

⟦C43⟧

## 5.2 Checks Before Starting

Check the file permissions and that the dedicated user can read Python and relay.py.

⟦C44⟧

⟦C45⟧

⟦C46⟧

⟦C47⟧

⟦C48⟧

Confirm that the unit's contents match the credential names read by relay.py.

⟦C49⟧

⟦C50⟧

Also confirm that query strings and authentication information do not remain in the access log.

> **Note:** At the time this check was done in the original build, relay.py had already changed from the content in 4.1–4.3 (an override of `log_request` that limits the access log to "source IP address and status", and the addition of `threading.BoundedSemaphore(8)` that limits concurrent requests to eight). The steps for these changes were not recorded in the build history, so they are not included in this book (author's notes, item 14-A).

⟦C51⟧

⟦C52⟧

`LoadCredential` is shown as `[unprintable]` to protect its contents.

# Chapter 6: Starting and Checking Connections

## 6.1 Starting

When started, it begins listening on `192.168.0.220:8765`.

⟦C53⟧

The result at build time was `Active: active (running)`. Note that at this point it is still `disabled` (does not start automatically).

⟦C54⟧

## 6.2 Checking TLS

⟦C55⟧

The results at build time were as follows.

- `Protocol version: TLSv1.3`
- `Peer certificate: CN = 192.168.0.220`
- `Verification: OK`

`Can't use SSL_get_servername` is a notice that the SNI name cannot be used because the connection was made with an IP address; it is not a verification failure.

## 6.3 Connecting from VM 230

> **Run on: ai-defense-manager VM 230 (root)**

⟦C56⟧

If `succeeded!` is shown, VM 230 can reach the Relay's listening port.

# Closing Notes

In Part 14 we built the following relay API on security-core.

| Item | Details |
|---|---|
| Listening on | `https://192.168.0.220:8765` (TLS 1.2 or later) |
| Allowed source | Only `192.168.0.33` (VM 230) |
| Authentication | Bearer token |
| API | `GET /health`, `GET /v1/alerts?limit=&since_minutes=` |
| Runs as | `ai-defense-relay.service` (dedicated user, `LoadCredential`) |

In the next part, we safely pass the token and CA certificate to VM 230 so that it can receive alerts from the Relay.

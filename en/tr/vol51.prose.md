---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 51: Verifying TLS and Authentication from VM 230 to the Relay"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 51 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 50 we gave VM 230 the static address `192.168.0.221` and fixed the allowed client of the Relay on VM 220. Here, before actually fetching alerts, we check the conditions for connecting from VM 230 to the Relay on VM 220.

1. Check VM 230's connection settings and the HTTPS implementation of the Relay on VM 220
2. Check that the Relay's server certificate matches `192.168.0.220` and is signed by a CA that VM 230 trusts
3. Using `/health`, which does not query the Indexer, test TLS, the source IP restriction and Bearer authentication once

Secret keys, Bearer tokens and Indexer credentials are not displayed.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **VM 220**: security-core (root)

# Chapter 1: Connection Settings and the HTTPS Implementation

## 1.1 VM 230's Connection Target

> **Run on: VM 230**

⟦C0⟧

| Item | Result |
|---|---|
| Relay URL | `https://192.168.0.220:8765/` |
| Path | VM 230 `.221` → VM 220 `.220` |
| Authentication | Bearer token |
| TLS certificate verification | enabled (`verify=str(ca_file)`) |

The old address `.33` did not remain on the VM 230 side.

## 1.2 The Relay's HTTPS Implementation

> **Run on: VM 220**

⟦C1⟧

The Relay is an HTTPS server that requires TLS 1.2 or later, and it loaded its server certificate and secret key from systemd credentials.

# Chapter 2: Checking the Certificate and CA

## 2.1 The Server Certificate

We look only at public information.

> **Run on: VM 220**

⟦C2⟧

| Item | Result |
|---|---|
| SAN | `IP Address:192.168.0.220` |
| Issuer | `AI-Defense-Relay-Internal-CA` |
| Validity | November 20, 2026 – February 22, 2029 |

## 2.2 The CA That VM 230 Trusts

> **Run on: VM 230**

⟦C3⟧

VM 230 loads the internal CA certificate from `/etc/ai-defense-manager/credentials/relay-ca.crt`, and TLS verification is not disabled.

> **Run on: VM 230**

⟦C4⟧

| Item | State |
|---|---|
| CA certificate | present and readable; issuer `AI-Defense-Relay-Internal-CA` |
| API token | present (contents not displayed) |
| Credentials directory | `root:ai-defense`, `750` |
| CA and token files | `root:ai-defense`, `640` |

The SHA-256 fingerprint of VM 230's CA certificate was as follows.

⟦C5⟧

## 2.3 The Original CA File on VM 220

> **Run on: VM 220**

⟦C6⟧

`indexer-ca` in VM 220's credentials is for Wazuh Indexer, not the Relay's CA. We look for the original file of the Relay's CA.

> **Run on: VM 220**

⟦C7⟧

The Relay's dedicated CA was in `/etc/credstore/ai-defense-relay-ca`.

## 2.4 Matching Fingerprints and Signatures

> **Run on: VM 220**

⟦C8⟧

| Checked | Result |
|---|---|
| SHA-256 of VM 220's CA | `71:E8:CE:68:…:84:61:54` |
| SHA-256 of VM 230's CA | the same |
| CA Subject | `AI-Defense-Relay-Internal-CA` |
| Server certificate verified by the CA | `OK` |
| Server certificate SAN | `192.168.0.220` |
| Minimum TLS version | TLS 1.2 |

We confirmed that the trust relationship is correct cryptographically, not just that the issuer names are the same.

# Chapter 3: Testing with `/health`

## 3.1 An Endpoint That Does Not Query the Indexer

Calling `/v1/alerts` queries Wazuh Indexer. First we check whether there is an endpoint that does not.

> **Run on: VM 220**

⟦C9⟧

The Relay processes requests in the following order; for `/health` it returns `200 OK` before querying the Indexer.

1. Check that the source IP address is `192.168.0.221`
2. Check the Bearer token
3. For `/health`, return `200 OK` and finish
4. Query Wazuh Indexer only for `/v1/alerts`

## 3.2 Testing TLS and Bearer Authentication

With CA certificate verification and Bearer authentication enabled, the token is read from the file and used in memory only.

> **Run on: VM 230**

⟦C10⟧

| Checked | Result |
|---|---|
| Loading the CA certificate | passed |
| TLS certificate verification | passed |
| Source IP restriction | passed (200 response) |
| Bearer authentication | passed |
| Relay `/health` | `HTTP 200` |
| Access to Wazuh Indexer, PostgreSQL, Ollama | none |

# Closing Notes

In Part 51 we confirmed that a secure HTTPS path from VM 230 to the Relay on VM 220 is in place.

| Item | Result |
|---|---|
| Connection target | `https://192.168.0.220:8765/` (TLS 1.2 or later) |
| Server certificate | SAN `192.168.0.220`, signed by `AI-Defense-Relay-Internal-CA` |
| CA | VM 220 `/etc/credstore/ai-defense-relay-ca` and VM 230 `relay-ca.crt` are the same |
| Authentication | source IP (`192.168.0.221`) and Bearer token |
| `/health` | `HTTP 200` |

In the next part, Part 52, we fetch real Wazuh alerts once.

---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 56: Reviewing and Designing API Authentication"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 56 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". By Part 55 we had put in order the input, output and high-volume protection of the AI Defense Manager on VM 230. The major remaining issue is that **the API has no authentication**. Here, before building authentication, we check the following read-only and decide the design.

1. API authentication and authorization, and the paths that reach the API
2. Local account privileges, and protection of credentials and the DB
3. The network boundary (firewall, IPv6, SSH)
4. Where to integrate authentication, and the token scheme

During the build we decided the following.

- The API is designed on the assumption that **it will later also be used from a Web UI on another VM and from management terminals**
- The Web UI VM has not been decided yet, so source IP restrictions will be added once it is

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: API Authentication and Paths to the API

## 1.1 Authentication and Authorization

> **Run on: VM 230**

⟦C0⟧

| Item | Now | Verdict |
|---|---|---|
| API authentication | none | needs action |
| API authorization | none | needs action |
| OpenAPI Security | not defined | needs action |
| Listening | `127.0.0.1` only | good |
| `/health` | no authentication | acceptable if internal only |
| Body size limit | 256KiB | done |
| Concurrent analysis limit | 1 | done |

Through the analysis APIs, local processes can request Ollama inference and SQLite writes without authentication.

## 1.2 Paths to the API

> **Run on: VM 230**

⟦C1⟧

No Nginx, Apache, Caddy or Cloudflared is running on VM 230, and no existing client that calls the API was found. SSH listens on all IPv4 and IPv6 interfaces. The main current threat is not direct access from outside but **unauthorized use by local accounts and processes inside VM 230**.

# Chapter 2: Accounts, Credentials and the DB

## 2.1 Local Account Privileges

Passwords and SSH secret keys are not displayed.

> **Run on: VM 230**

⟦C2⟧

| Account | Privileges |
|---|---|
| `aidefense` (used for login) | `sudo` (can become root), `lxd`, `adm` |
| `ai-defense` (for the service) | `/usr/sbin/nologin`, only its dedicated group |

`aidefense` is effectively an administrator, so adding authentication to the API does not prevent this account from becoming root. The purpose of authentication is to prevent unauthorized calls from ordinary users and local processes with limited privileges. `sudo` and `lxd` may be needed for operation, so they are not changed.

## 2.2 Protection of Credentials

> **Run on: VM 230**

⟦C3⟧

| Target | State |
|---|---|
| `/etc/ai-defense-manager/credentials` | `root:ai-defense`, `750` |
| Relay token, CA certificate | `640` |
| Readable by `ai-defense` | yes |
| Readable by `aidefense` (ordinary privileges) | no |
| Application Python sources | `root:ai-defense`, `640` |

## 2.3 How Credentials Are Passed, and the DB

> **Run on: VM 230**

⟦C4⟧

- systemd `LoadCredential` is not used, and the running process has no `CREDENTIALS_DIRECTORY`
- The Relay credentials are read directly from `/etc/ai-defense-manager/credentials/` and protected by file permissions
- `aidefense` has no direct access to the Relay credentials directory or to the DB files and directory

API authentication tokens are managed separately from the Relay token.

# Chapter 3: The Network Boundary

## 3.1 Interfaces and Listening Ports

> **Run on: VM 230**

⟦C5⟧

VM 230 is `192.168.0.221/24`, and the API listens only on `127.0.0.1:8000`. Other VMs cannot connect to port 8000 directly. We do not suddenly change the API to `0.0.0.0:8000`.

## 3.2 Firewall and IPv6

> **Run on: VM 230**

⟦C6⟧

| Item | Result | Assessment |
|---|---|---|
| API listening | `127.0.0.1:8000` | good |
| IPv4 iptables | no rules | needs measures |
| IPv6 ip6tables | no rules | needs measures |
| nftables | iptables-compatible, no actual rules | — |
| UFW | enabled but shown as `inactive` | investigate |
| IPv4/IPv6 forwarding | 0 (disabled) | good |
| IPv6 address | global | caution |

No inbound filtering inside VM 230 could be confirmed. We cannot say that firewalls on Proxmox or the upstream router are also disabled, but we treat this as a remaining issue (Chapter 6 of the Operations Manual).

## 3.3 SSH

> **Run on: VM 230**

⟦C7⟧

The settings were `PermitRootLogin no`, `PasswordAuthentication no` (`00-local-hardening.conf`), `PubkeyAuthentication yes` and `KbdInteractiveAuthentication no`.

> **Run on: VM 230**

⟦C8⟧

On VM 230, `ssh.service` does not run all the time; `ssh.socket` holds port 22 and starts `ssh.service` when a connection arrives (IPv4 `0.0.0.0:22`, IPv6 `[::]:22`). Even when `ssh.service` is `inactive`, SSH is not stopped.

> **Run on: VM 230**

⟦C9⟧

`/run/sshd` is created by systemd when `ssh.service` starts (`RuntimeDirectory`). The configuration files are read in the order `00-local-hardening.conf`, `50-cloud-init.conf`, and OpenSSH uses the first value set, so `PasswordAuthentication no` takes precedence. The SSH settings are not changed.

# Chapter 4: Designing Authentication

## 4.1 Where to Integrate

> **Run on: VM 230**

⟦C10⟧

- There are two API routers (`/api/v1`: AI analysis; `/api/v1/wazuh`: Wazuh event retrieval and analysis)
- There is no authentication middleware, `Depends`, `HTTPBearer` or the like yet
- `/health` is outside the routers and can be separated from authentication
- The body size limit middleware can stay
- There is no `tests/` directory

## 4.2 The Design Decided

> **Run on: VM 230**

⟦C11⟧

| Target | Now | Policy |
|---|---|---|
| AI analysis API | no authentication | requires authentication (`analyze`) |
| Wazuh event retrieval | no authentication | requires authentication (`read`) |
| Wazuh analysis | no authentication | requires authentication (`analyze`) |
| `/health` | no authentication | unchanged |
| `/docs`, `/redoc`, `/openapi.json` | no authentication | disabled in production |
| Per-client revocation | none | build it |
| Separation of privileges | none | build it (`read`, `analyze`) |

The token scheme is as follows.

- Issue an unguessable random Bearer token per client
- Store only the SHA-256 hash in SQLite, not the token itself
- Use `hmac.compare_digest` for comparison
- Give tokens expiry and revocation
- Keep them completely separate from the Relay token
- Do not give the LLM credentials or execution privileges
- Keep the API on `127.0.0.1:8000`; when used from other VMs, provide a separate entry point with TLS

# Closing Notes

In Part 56 we carried out the checks before building API authentication and decided the design.

| Item | Result |
|---|---|
| API | no authentication or authorization; `127.0.0.1:8000` only |
| Accounts | `aidefense` is an administrator, `ai-defense` is service-only (privileges are separated) |
| Credentials | protected by file permissions (`root:ai-defense`, `640`) |
| Network | no firewall rules inside VM 230 (an issue); SSH is socket-activated with password authentication disabled |
| Authentication design | per-client Bearer tokens (`read`, `analyze`), stored as hashes, with revocation and expiry; documentation APIs disabled |

In the next part, Part 57, we build token authentication and test it in an independent environment.

---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 50: Deploying the New Code and a Static Address for VM 230"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 50 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". By Part 49 we had fixed the code of the Relay on VM 220 and the AI Defense Manager on VM 230, and restarted only the Relay. Here we do the following.

1. Restart `ai-defense-manager.service` on VM 230 so that it loads the new code
2. Change VM 230's address from the DHCP-assigned `192.168.0.33` to a static `192.168.0.221` (DHCP is not used)
3. Fix the old address (the client allowed to connect) left in the Relay on VM 220 to the new address

Numbering it next to VM 220 (`192.168.0.220`) makes it easier to manage.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **VM 230 (console)**: logged in as root from the Console of VM 230 in the Proxmox web interface
  - **VM 220**: security-core (root)

# Chapter 1: Restarting the AI Defense Manager

## 1.1 Restart

We restart only the AI Defense Manager service. At this point the address is still `192.168.0.33`.

> **Run on: VM 230**

⟦C0⟧

The restart succeeded and systemd showed `active (running)`, but `/health` could not be reached. It was checked about 15ms after the restart, so presumably Uvicorn had not yet started listening on port 8000.

## 1.2 Checking the Startup

> **Run on: VM 230**

⟦C1⟧

| Item | Result |
|---|---|
| systemd | `active (running)` |
| MainPID | `1640` |
| Uvicorn startup, application startup | succeeded |
| Listening | `127.0.0.1:8000` |
| `/health` | `HTTP 200` |
| Version | `0.1.0` |

Now the code fixed in Parts 48 and 49 is running on both VM 220 and VM 230.

# Chapter 2: Fixing VM 230's Address

## 2.1 The Current Settings

> **Run on: VM 230**

⟦C2⟧

VM 230 received `192.168.0.33/24` by DHCP (NIC `enp6s18`). The API listens only on `127.0.0.1:8000`, so changing the address does not expose the API. However, SSH may be cut temporarily.

## 2.2 DNS and the Management Method

> **Run on: VM 230**

⟦C3⟧

VM 230 is managed by **Netplan and systemd-networkd**, and `/etc/netplan/50-cloud-init.yaml` had `dhcp4: true`. DNS is `192.168.0.1`, `2404:1a8:7f01:a::3` and `2404:1a8:7f01:b::3`. IPv6 is left on automatic configuration via router advertisements (RA); only IPv4 is made static.

## 2.3 The Whole Configuration, and Address Conflicts

> **Run on: VM 230**

⟦C4⟧

`arping` was not installed, so we check with ping and the neighbor cache.

> **Run on: VM 230**

⟦C5⟧

There was no ping reply from `192.168.0.221`, and the neighbor cache showed `FAILED`. It does not appear to be in use (devices that do not answer ICMP or that are powered off are possible, so we cannot say for certain there is no conflict).

| Item | After the change |
|---|---|
| IPv4 | `192.168.0.221/24` (static) |
| Gateway | `192.168.0.1` |
| IPv4 DHCP | disabled |
| IPv6 | still automatic via RA |
| DNS | the current three addresses |
| DNS search domain | still `iptvf.jp` |

## 2.4 Creating the Configuration File

We save a copy of the configuration file before rewriting it. At this stage **the configuration is not applied and the interface is not restarted**.

> **Run on: VM 230**

⟦C6⟧

The copy of the original configuration (SHA256 match), the Netplan syntax check and `netplan generate` (exit code `0`) all succeeded.

## 2.5 Applying with `netplan try`

SSH is cut when the address changes, so run this from **VM 230's Console in the Proxmox web interface**. `netplan try` asks for confirmation after applying and reverts if you do not confirm.

> **Run on: VM 230 (console)**

⟦C7⟧

> **Important:** When `netplan try` asks for confirmation, confirm only after checking that the address has become `.221` and communication works. If it is still `.33`, do not confirm.

`netplan try` finished normally and the configuration was confirmed. It did not revert automatically.

## 2.6 Checking After Applying

> **Run on: VM 230 (console)**

⟦C8⟧

| Checked | Result |
|---|---|
| IPv4 | `192.168.0.221/24` (lifetime `forever`) |
| IPv4 DHCP | disabled |
| Default route | `192.168.0.1`; ping to the gateway succeeded 3/3 |
| IPv6 RA | normal |
| DNS | normal with the three addresses |
| API listening | `127.0.0.1:8000` |
| `/health` | `HTTP 200` |
| systemd | `active` |

# Chapter 3: Fixing the Address the Relay Allows

## 3.1 Where the Old Address Remains

The Relay on VM 220 is the side VM 230 connects to, so we check whether VM 230's old address remains in its settings.

> **Run on: VM 220**

⟦C9⟧

Line 16 of `/opt/ai-defense-relay/relay.py` still had `ALLOWED_CLIENT = "192.168.0.33"`.

## 3.2 How It Is Used

> **Run on: VM 220**

⟦C10⟧

The Relay checks clients in two stages.

1. The source IP address matches `ALLOWED_CLIENT`
2. The `Authorization: Bearer ...` token matches

As it is, connections from VM 230's new address would be refused. Only one line of `relay.py` is changed; the API token, Wazuh settings, allowed fields, and listening address and port are not changed.

## 3.3 Fixing One Line and Restarting

We make a copy, check that only one line changed, the Python syntax and the file permissions, and then restart the Relay.

> **Run on: VM 220**

⟦C11⟧

It changed to `ALLOWED_CLIENT = "192.168.0.221"`, the copy's SHA256 matched, the syntax check passed, permissions stayed `640`, the restart gave exit code `0`, and the state was `active`.

## 3.4 Checking the Listening Port

Right after the restart, `ss` did not yet show port 8765 listening, so we wait a little and check.

> **Run on: VM 220**

⟦C12⟧

| Item | Result |
|---|---|
| Relay | `active (running)`, MainPID `17962` |
| Listening | `192.168.0.220:8765` |
| Allowed client | `192.168.0.221` |

# Closing Notes

In Part 50 we deployed the new code to VM 230 and gave VM 230 a static address.

| Item | Result |
|---|---|
| VM 230 service | restarted and running the new code (`/health` is `HTTP 200`) |
| VM 230 address | `192.168.0.221/24` (static, no DHCP). Copy of the settings in `/var/backups/ai-defense-manager/netplan-…` |
| Relay's allowed client | `192.168.0.33` → `192.168.0.221` |
| Layout | VM 220 `192.168.0.220` (Wazuh, Relay :8765), VM 230 `192.168.0.221` (AI Defense Manager :8000, localhost only) |

In the next part, Part 51, we check TLS and authentication from VM 230 to VM 220 and try fetching real alerts.

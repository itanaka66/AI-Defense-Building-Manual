---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 1: Building the Defense Foundation and Monitoring with Wazuh"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This manual describes how to build an AI autonomous cyber defense system on Proxmox VE. (How to adapt it to a set of ordinary PCs is explained in the second half of this Introduction.) It was compiled from the records of the actual build, keeping only the steps that succeeded, in chronological order. The manual is divided into four volumes, Volume 1 to Volume 4, and each volume is further divided into parts (see "Volumes and Parts" in this Introduction). This book (Part 1 of Volume 1) covers the following.

- Deciding the design policy of the defense system (Chapter 1)
- Surveying the Proxmox host and finalizing the configuration of the new VMs (Chapters 2–3)
- Creating the Security Core VM (VMID 220) and installing and setting up Ubuntu Server 24.04.5 LTS (Chapters 4–6)
- Building Wazuh 4.14.10 All-in-One and checking that it works (Chapters 7–10)
- Installing the Wazuh agent on the Proxmox host and taking inventory of the VMs and LXCs (Chapters 11–12)
- Deploying the Wazuh agent to LXC containers (Prometheus, Grafana, PostgreSQL) (Chapters 13–16)

## Downloading the Scripts

The scripts used in this book can be downloaded from:

https://github.com/itanaka66/AI-Defense-Building-Manual/releases

## Volumes and Parts

Because the build records are long, this manual is divided into the following four volumes. Part numbers run continuously across volumes.

| Volume | Parts | Main topics |
|---|---|---|
| Volume 1 | Parts 1–23 | Defense foundation (Wazuh, Collector, PostgreSQL, monitoring), AI Defense Manager, a search user for Wazuh, the relay API (Relay), AI analysis and its protection, checks |
| Volume 2 | Parts 24–30 | Enabling and verifying the Wazuh Indexer audit log; checking, recovering and preventing recurrence for the Collector |
| Volume 3 | Parts 31–44 | Handling log switching and recovering missing events, monitoring with Prometheus and testing the rules, checking PostgreSQL, backups (logical, LXC, ZFS snapshots) and restore testing, the TrueNAS destination, handling failures after a reboot |
| Volume 4 | Parts 45–71 | Safe input and output for LLM analysis (allowlists, masking, approval policy), integration with the Relay, API token authentication, checking errors and logs, detecting log tampering (FSS), repairing Wazuh local rules, AI defense agents |

**Volume 1**

| Part | Title |
|---|---|
| Part 1 | Building the Defense Foundation and Monitoring with Wazuh |
| Part 2 | Safely Monitoring PostgreSQL Logs and Correlation Detection |
| Part 3 | Building the Alert-Storage Collector |
| Part 4 | Auditing the Collector and Developing a Hardened Version |
| Part 5 | Deploying the Hardened Collector to Production |
| Part 6 | Verifying Data Integrity and Auditing Operations |
| Part 7 | Finishing the Collector's Fault Tolerance |
| Part 8 | Building the Integrated Monitoring Platform |
| Part 9 | Recovering from a Collector Stop and Checking Operations |
| Part 10 | Handling a Disk Failure and Preparing the AI Defense Manager |
| Part 11 | Laying the Groundwork for the AI Defense Manager |
| Part 12 | Investigating the AI Analysis Service and Wazuh Integration |
| Part 13 | A Read-Only User for Wazuh Indexer |
| Part 14 | Building the Alert Relay API (Relay) |
| Part 15 | Passing the Relay Connection Details Safely to VM 230 |
| Part 16 | Connecting Wazuh Alerts to AI Analysis |
| Part 17 | Running the AI Defense Manager as a Service and Its Startup Order |
| Part 18 | Keeping the Analysis History in SQLite |
| Part 19 | Minimizing the Information Passed to the LLM |
| Part 20 | Fixing Confidence Scores and Protecting Stored Data |
| Part 21 | Switching SSH on VM 230 to Public-Key Authentication |
| Part 22 | Checking the Relay and Its Connection Details |
| Part 23 | Investigating Indexer Permissions and the Audit Log |

**Volume 2**

| Part | Title |
|---|---|
| Part 24 | Finding Out Why the Audit Log Is Not Saved |
| Part 25 | Setting Where the Audit Log Is Saved |
| Part 26 | Not Recording Request Bodies in the Audit Log |
| Part 27 | Confirming That the Audit Log Is Saved |
| Part 28 | Checking the Collector and Why It Stopped |
| Part 29 | Restarting the Collector Without Missing Any Events |
| Part 30 | Keeping the Collector from Stopping for the Same Reason |

**Volume 3**

| Part | Title |
|---|---|
| Part 31 | Why the Collector Cannot Read After Log Switching, and the Fix |
| Part 32 | Confirming an Actual Switch and Recovering Missing Events |
| Part 33 | Monitoring the Collector's State with Prometheus |
| Part 34 | Monitoring the Wazuh Platform's State with Prometheus |
| Part 35 | Testing the Alert Rules and Checking in Production |
| Part 36 | Checking PostgreSQL |
| Part 37 | Backing Up PostgreSQL and Testing a Restore |
| Part 38 | Using TrueNAS as the Backup Destination |
| Part 39 | Registering the Destination and Preparing Scheduled Backups |
| Part 40 | Completing the PostgreSQL Logical Backup |
| Part 41 | Backing Up LXC 109 and Testing an Isolated Restore |
| Part 42 | Protecting the Backups and TrueNAS Snapshots |
| Part 43 | Backup Failures After a Reboot and the Recovery |
| Part 44 | Comparing the Restored Databases with Production |

**Volume 4**

| Part | Title |
|---|---|
| Part 45 | Preparing for LLM Analysis and Repairing the Wazuh Configuration File |
| Part 46 | Classifying Alerts and Deciding Which Fields to Pass to the LLM |
| Part 47 | Examining the Existing AI Defense Manager Implementation |
| Part 48 | Narrowing the Wazuh Event Conversion to Seven Fields |
| Part 49 | Narrowing the Fields Returned by the Relay to Seven |
| Part 50 | Deploying the New Code and a Static Address for VM 230 |
| Part 51 | Verifying TLS and Authentication from VM 230 to the Relay |
| Part 52 | Fetching Real Alerts and Fixing the Relay's 502 |
| Part 53 | Checking the Flow from Analysis to Storage |
| Part 54 | Masking LLM Output and the Approval Policy |
| Part 55 | Integration Checks and Preparing for High Request Volumes |
| Part 56 | Reviewing and Designing API Authentication |
| Part 57 | Building Token Authentication for the API |
| Part 58 | Hardening Token Handling and the CLI |
| Part 59 | Putting API Authentication into Production |
| Part 60 | Keeping Error Responses and Logs from Leaking Information |
| Part 61 | Checking Logs for Secrets and Capping the Journal Size |
| Part 62 | Creating FSS Keys to Guard Against Log Tampering |
| Part 63 | Moving the FSS Verification Key to the Proxmox Host |
| Part 64 | Running and Checking FSS Sealing |
| Part 65 | Checking FSS from Another Host (VM 240) |
| Part 66 | Automating FSS Verification Every 15 Minutes |
| Part 67 | Finding the Breakage in Wazuh's Local Rules |
| Part 68 | Testing the Fixed Rules in an Isolated Environment |
| Part 69 | Putting the Fixed Rules into Production |
| Part 70 | Starting to Build the AI Defense Agents |
| Part 71 | Correlation, Orchestration and Defense Decision Agents |

## Notation

- Commands and file contents are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Each step begins with "Run on", which says where to run it. `root@pve` is the Proxmox host, `root@security-core` is VM 220, and prompts such as `root@lxc-prometheus` mean inside an LXC container.
- "Example output" is the actual output from the build. In your environment, IDs, MAC addresses, sizes, dates and so on will differ.
- The IP addresses, VMIDs and storage names in this book are the values of the environment that was built. Replace them with the values of your own environment.

## Assumed Build Environment

| Item | Details |
|---|---|
| Virtualization platform | Proxmox VE 8.4 (host name `pve`) |
| CPU | AMD EPYC 7301 (16 cores / 64 threads) |
| Memory | About 267 GiB |
| Management network | `vmbr0` (eno1) `192.168.0.0/24`, host IP `192.168.0.240` |
| Internal network | `vmbr1` (eno2) `192.168.1.0/24`, host IP `192.168.1.254` |
| Default gateway | `192.168.0.1` |
| Guest OS | Ubuntu Server 24.04.5 LTS |

## Building on Ordinary PCs

This book is written for a setup in which Proxmox VE runs on one large server and each function is placed in a virtual machine (VM) or container (LXC) on it. The same system **can also easily be built by combining several ordinary PCs (mini PCs or desktop PCs)**. Think of one VM or LXC as one PC.

### Mapping VMs and LXCs to PCs

| Name in this book | Location in this book | Role | Mapping (example) |
|---|---|---|---|
| security-core | VM 220 (192.168.0.220) | Wazuh (Manager, Indexer, Dashboard), Collector | PC1 |
| postgresql | LXC 109 (192.168.0.151) | PostgreSQL (alert storage) | PC2 |
| lxc-prometheus | LXC 103 (192.168.0.197) | Prometheus | PC2 |
| lxc-grafana | LXC 105 (192.168.0.199) | Grafana | PC2 |
| VictoriaMetrics | Existing LXC (192.168.0.171) | Metrics storage | PC2 |
| ai-defense-manager | VM 230 (192.168.0.33) | AI Defense Manager | PC3 |
| ollama-gpu | VM 101 (192.168.0.180) | Ollama (local LLM) | PC4 |
| pve | Proxmox host (192.168.0.240) | Virtualization platform (one of the monitored machines) | Not needed (each PC becomes a monitored machine) |

The table above is an example of a four-PC setup in which the monitoring and storage roles (PostgreSQL, Prometheus, Grafana, VictoriaMetrics) are combined on one machine (PC2). If you have enough machines, you may split them one role per machine, as in this book. Even when they are combined on one machine, the ports they use (PostgreSQL 5432, Prometheus 9090, Grafana 3000, VictoriaMetrics 8428) do not overlap. However, run only one Node Exporter (9100) per machine, and combine the Prometheus jobs into one machine's worth.

Where the text says "Run on: LXC 103 lxc-prometheus" and so on, read it as the PC that holds that role (PC2 in the example above).

### Reference PC Specifications

The following table is a rough guide. It is based on the resources assigned to each VM in the build environment of this book and on Wazuh's official guideline shown in the text (8 vCPU, 8 GiB RAM and 100–200 GB for 25–100 agents). It has not been tested with this number of machines or this configuration. Increase the resources to match the number of monitored servers, the volume of logs and the retention period.

| PC | Role | CPU | Memory | Disk | Notes |
|---|---|---|---|---|---|
| PC1 | Wazuh, Collector | 8 cores or more | 16 GB or more | SSD 250 GB or more | Same as VM 220 in this book. The Indexer stores logs, so allow plenty of disk |
| PC2 | PostgreSQL, Prometheus, Grafana, VictoriaMetrics | 4 cores or more | 16 GB or more | SSD 500 GB or more | Increase the disk according to the retention period |
| PC3 | AI Defense Manager | 4 cores or more | 8 GB or more | SSD 100 GB or more | Same as VM 230 in this book |
| PC4 | Ollama | 8 cores or more | 32 GB or more | SSD 500 GB or more | NVIDIA GPU (about 12 GB VRAM or more as a guide). This book uses `qwen3:8b` on an RTX 3090 (24 GB) |

The simplest OS choice is Ubuntu Server 24.04 LTS, as in this book. (In this book, some LXCs ran Debian 13. Package names and versions can be checked with the same steps.)

### Notes on Adapting the Steps

- **Proxmox-only commands**: `qm`, `pct` and `pvesm` are Proxmox commands. Replace the steps that create VMs or LXCs (Part 1 Chapters 2–4, Part 10 Chapter 6, etc.) with installing an OS on each PC. The steps that monitor the Proxmox host itself (Part 1 Chapter 11, Part 8 Chapter 3) are not needed.
- **IP addresses**: The IP addresses in this book are those of the environment that was built. Assign a fixed IP address to each PC and substitute it for the addresses in the text. This book uses two networks (192.168.0.0/24 and 192.168.1.0/24), but you may put all PCs on the same network (for example 192.168.0.0/24).
- **Listen addresses**: Node Exporter, the relay API and others are configured to listen only on the PC's own address (for example `--web.listen-address=192.168.0.240:9100`). Replace it with the address of that PC.
- **Disk monitoring**: The disk failure detection and handling in Part 10 works the same way on PCs. Check device names (`/dev/sdg` and so on) in your own environment.
- **GPU**: On PC4, install the NVIDIA driver and confirm with `nvidia-smi` that the GPU is visible before installing Ollama. (Ollama had already been installed before the scope of this build, so its installation steps are not included.)

## Wazuh Version Used

| Item | Version |
|---|---|
| Wazuh (Manager, Indexer, Dashboard, Agent) | 4.14.10 |
| Filebeat | 7.10.2 |
| Proxmox host | Proxmox VE 8.4.0 (Debian 12 Bookworm) |

The Manager and the agents use the same version, 4.14.10.

# Chapter 1: System Design Policy

## 1.1 Goal

We build an "AI SOC (Security Operations Center)" that monitors the network for intrusions 24 hours a day, with AI agents assisting in detection, analysis, blocking, investigation and recording. The basic principle is not to give the AI unlimited control, but to have it take defensive actions based on evidence, within the network we manage ourselves.

The automated processing flow is as follows.

**Detection → Correlation analysis → Risk assessment → Defense decision → Blocking → Verification → Recording**

## 1.2 Design Conditions

The system was designed under the following conditions.

| Item | Decision |
|---|---|
| Autonomy level | Level 3 (automatically block and isolate suspicious sources) |
| Execution model | Block automatically according to severity; a human approves critical operations |
| Platform | Proxmox VE, mainly open-source software |
| Kubernetes (RKE2) | Retired. Removed from the scope of defense |

Because RKE2 was retired, the scope of defense is as follows.

- The Proxmox host
- VMs and LXC containers on Proxmox (the LXC 400 series is out of scope)
- LAN, routers and firewalls
- Databases
- AI platforms such as Ollama and vLLM
- Publicly exposed web services

The VMs for RKE2 are not deleted merely because of the retirement decision. They will be handled after checking the migration status of existing data and services.

## 1.3 Components

| Product | Role |
|---|---|
| Wazuh | SIEM, host monitoring, log analysis |
| Suricata | IDS/IPS, traffic monitoring |
| CrowdSec | Detecting and blocking suspicious IPs |
| AI Defense Manager | AI analysis, correlation, risk assessment, defense control |
| SOAR / Incident DB | Defensive actions, approvals, audit records |

The AI model never executes a block command directly. The AI only proposes a decision; an independent policy engine verifies that it may be executed and then calls the defense API.

## 1.4 Phased Rollout

Automatic blocking is not enabled from the start. We proceed in the following stages.

1. Monitoring only
2. AI analysis and defense proposals
3. Automatic blocking of suspicious IPs based on approved rules
4. Isolation of VMs and LXCs with approval

The build order is as follows.

1. Build the Security Core (Wazuh Server, Indexer, Dashboard)
2. Install agents on the Proxmox host, VMs and LXCs
3. Install Suricata in IDS mode and make traffic visible
4. Build the AI Defense Manager (working with the existing Ollama)
5. Start automation with temporary blocking of suspicious external IPs (isolation of VMs and LXCs requires approval)

## 1.5 Safety Design Rules

- Limit blocking targets to the network we manage.
- Do not identify an attacker from an IP address alone.
- Do not accidentally block our own management IPs or important traffic. The gateway (`192.168.0.1`), the Proxmox host (`192.168.0.240`), the management IPs of the security VMs and so on are excluded from automatic blocking.
- Do not give the AI unlimited root privileges.
- Store the operation history somewhere it is hard to tamper with.
- Give every automatic block an expiry and a rollback (unblock) function.
- Do not conclude that an intruder has been removed just because an IP address was blocked. Also investigate accounts, processes and persistent malicious programs.

# Chapter 2: Surveying the Proxmox Environment

Before creating VMs, we examine the state of the Proxmox host so that nothing conflicts with the existing environment. All commands in this chapter are read-only and do not change any settings.

## 2.1 Collecting Environment Information

**Run on: the Proxmox host (root@pve)**

⟦C0⟧

The survey showed the following.

| Item | Result |
|---|---|
| Proxmox | VE 8.4.0 (pve-manager 8.4.20) |
| Memory | 267 GiB (about 115 GiB available) |
| Network | Two networks: `vmbr0` (eno1) and `vmbr1` (eno2) |
| Proxmox Firewall | Disabled (`disabled/running`) |
| Kubernetes | No nodes (as planned for retirement) |

The Proxmox Firewall is currently disabled. To avoid losing management access, we do not enable it at this stage.

## 2.2 Checking Storage, Networks and Existing Guests

**Run on: the Proxmox host (root@pve)**

Check the free space of the storage.

⟦C1⟧

Check the network interfaces and the bridge connections.

⟦C2⟧

The check showed the following.

- `eno2` was link-down (`NO-CARRIER`). `vmbr1` works only as a virtual network inside Proxmox.

At this point, we do not change the settings of `eno2` or `vmbr1`.

## 2.3 Checking Disks and Link State in Detail

**Run on: the Proxmox host (root@pve)**

Check the block devices and the LVM configuration.

⟦C3⟧

> **Note:** `pvesm config` is not a Proxmox command, so it fails. The storage definitions are checked from the configuration file in 2.4.

Check the configuration of the stopped LXCs (to decide whether the AI-related containers can be reused).

⟦C4⟧

Check what `vmbr1` is connected to.

⟦C5⟧

Although the physical port is not connected, IPv6 neighbors of existing virtual machines and containers are visible on `vmbr1`, which confirms that it works as an internal bridge.

## 2.4 Checking the Storage Definitions

**Run on: the Proxmox host (root@pve)**

⟦C6⟧

The registered storage is as follows.

| Storage | Type | Use |
|---|---|---|
| `local` | Directory | ISOs, templates, backups |
| `local-lvm` | LVM-thin | VM disks, LXC rootfs |
| `models` | LVM-thin | VM disks, LXC rootfs |
| `osx` | LVM-thin | VM disks, LXC rootfs |
| `ubuntu` | LVM-thin | VM disks, LXC rootfs |
| `backup` | Directory | Backups, ISOs, VM disks, etc. |
| `windows_d` / `windows_c` | LVM-thin | VM disks, LXC rootfs |
| `RAID_A` / `RAID_B` | LVM-thin | VM disks, LXC rootfs |

## 2.5 Checking Physical Disk Types and Thin Pools

**Run on: the Proxmox host (root@pve)**

Check the free space of each storage.

⟦C7⟧

Check whether each physical disk is an SSD or an HDD. `ROTA` `0` means SSD/NVMe and `1` means a rotating HDD.

⟦C8⟧

Check the usage of the data and metadata areas of the thin pools.

⟦C9⟧

From the results, the mapping between physical disks and storage was as follows.

| Device | Size | Type | Storage | Assessment |
|---|---:|---|---|---|
| `nvme0n1` | 931GB | NVMe SSD | `local-lvm` | Fast. About 324 GB free (61.10% used) |
| `sda` | 1.9TB | SATA SSD | `ubuntu` | Fast. About 987 GB free (49.82% used) |
| `sdf` | 931GB | SATA SSD | `osx` | SSD. About 637 GB free |
| `sdb` | 5.5TB | HDD | `models` | For AI models and large data |
| `sdc` | 1.8TB | HDD | `RAID_A` | For TrueNAS |
| `sdd` | 1.8TB | HDD | `RAID_B` | For TrueNAS |
| `sdg` | 1.8TB | HDD | `backup` | Backups |
| `sdh` | 3.6TB | HDD | `windows_d` | — |
| `sde` | 223GB | SATA SSD | `windows_c` | — |

The metadata usage of the candidates `ubuntu`, `local-lvm` and `osx` was about 1–2% in each case, which is no problem.

## 2.6 Decisions Based on the Survey

**Use of the networks**

| Network | Use |
|---|---|
| `vmbr0` / eno1 | Production and management network (`192.168.0.0/24`, with internet access) |
| `vmbr1` / eno2 | Network dedicated to internal servers (`192.168.1.0/24`). eno2 is currently unconnected; a PostgreSQL server will be connected in the future |

`vmbr1` has no default gateway and is used only for internal traffic.

**Use of the storage**

- `RAID_A` and `RAID_B` are slow HDDs for TrueNAS, dedicated to backups and archives. They are not used for the defense system's VMs.
- Wazuh Indexer does a lot of log I/O, so it goes on an SSD.
- `local-lvm` (NVMe) has only about 324 GB free, so we do not put both VMs (350 GB) on it.

# Chapter 3: Finalizing the Configuration

## 3.1 The Final Configuration

After consideration, we decided on two new VMs with the following configuration. VMIDs 220 and 221 are VM IDs (not LXCs).

| Item | VM 220: Security Core | VM 221: AI Defense Manager |
|---|---|---|
| Role | Wazuh Server / Indexer / Dashboard | Python / FastAPI / AI agents |
| VMID | 220 | 221 |
| vCPU | 8 | 4 |
| RAM | 16GB | 8GB |
| Disk | 250GB | 100GB |
| Storage | `ubuntu` (SATA SSD) | `local-lvm` (NVMe) |
| NIC 1 | vmbr0 | vmbr0 |
| IP 1 | `192.168.0.220/24` | `192.168.0.221/24` |
| NIC 2 | vmbr1 | vmbr1 |
| IP 2 | `192.168.1.220/24` | `192.168.1.221/24` |
| Gateway | `192.168.0.1` | `192.168.0.1` |

- Both use fixed IP addresses and two NICs, `vmbr0` and `vmbr1`.
- The only default gateway is `192.168.0.1` on the `vmbr0` side; none is set on the `vmbr1` side.
- Against Wazuh's official guideline (8 vCPU, 8 GiB RAM and 100–200 GB for 25–100 agents), we chose 16 GB and 250 GB to leave headroom for log volume and retention.
- The AI Defense Manager uses the existing Ollama. We do not allocate a GPU or large memory twice.

The following existing services are reused.

- PostgreSQL (LXC 109)
- Ollama / RTX 3090

## 3.2 OS Configuration

| Item | VM 220 | VM 221 |
|---|---|---|
| OS | Ubuntu Server 24.04.5 LTS | Ubuntu Server 24.04.5 LTS |
| BIOS | OVMF (UEFI) | OVMF (UEFI) |
| Machine | q35 | q35 |
| SCSI Controller | VirtIO SCSI Single | VirtIO SCSI Single |
| QEMU Guest Agent | Enabled | Enabled |

> **Why 24.04 LTS:** The official Quickstart for the current stable Wazuh (4.14 series) recommends operating systems up to Ubuntu 24.04. Ubuntu 26.04 is supported by the 5.x series and is not part of the recommended configuration for 4.14. Because this is a security platform that will run for a long time, we prioritize stability and choose **Ubuntu Server 24.04.5 LTS + Wazuh 4.14.10**.

# Chapter 4: Creating VM 220 (Security Core)

## 4.1 Checking the ISO Image

**Run on: the Proxmox host (root@pve)**

⟦C10⟧

If there is no Ubuntu Server 24.04 ISO on the `local` storage, obtain it with the steps in 4.2.

## 4.2 Obtaining the Ubuntu Server 24.04.5 LTS ISO

**Run on: the Proxmox host (root@pve)**

> **Note:** Downloading from the Japanese mirror (`jp.releases.ubuntu.com`) stops with the error "The certificate's owner does not match hostname". The certificate returned by the server covers only `releases.ubuntu.com` and `www.releases.ubuntu.com`, not `jp.releases.ubuntu.com`. Do not disable certificate verification with `--no-check-certificate`; download from the official host name `releases.ubuntu.com` instead.

Move to the ISO storage directory.

⟦C11⟧

Check the server's certificate. Confirm that `DNS:releases.ubuntu.com` is shown.

⟦C12⟧

Download the ISO (about 3.9 GB).

⟦C13⟧

Check the file.

⟦C14⟧

Verify the SHA256 checksum to make sure the file has not been tampered with or corrupted during download.

⟦C15⟧

The check has succeeded if you see the following.

⟦C16⟧

## 4.3 Confirming That the VMIDs Are Unused

**Run on: the Proxmox host (root@pve)**

⟦C17⟧

If nothing is shown, 220 and 221 are free.

## 4.4 Checking the Storage for the EFI Disk

**Run on: the Proxmox host (root@pve)**

⟦C18⟧

We confirmed that `ubuntu` has enough free space (about 987 GB). The EFI disk also goes on `ubuntu`.

## 4.5 Creating the VM

**Run on: the Proxmox host (root@pve)**

> These operations create the new VM 220. They do not change the settings of existing VMs or LXCs. Run them one at a time and make sure there is no error before going on.

Create the VM itself.

⟦C19⟧

Add the EFI disk.

⟦C20⟧

Create the 250 GB system disk.

⟦C21⟧

Attach the Ubuntu Server 24.04.5 ISO.

⟦C22⟧

Set the boot order.

⟦C23⟧

## 4.6 About the Thin Pool Warning

When the system disk is created, the following warning appears.

⟦C24⟧

This warning means that, because of thin provisioning, the total allocated size of the virtual disks exceeds the physical capacity. The disk itself was created successfully.

- Creating a 250 GB disk does not physically consume all 250 GB at once.
- However, as the actual data of all VMs, including existing ones, grows, the thin pool may fill up. If it does, the VMs and LXCs on that storage will be seriously affected.
- At this stage we do not change the autoextend settings. We keep monitoring the thin pool usage.

## 4.7 Checking the VM Settings

**Run on: the Proxmox host (root@pve)**

> Do not start VM 220 yet. Check the settings first.

⟦C25⟧

Check the following items.

| Item | Expected value |
|---|---|
| CPU / RAM | `cores: 8` / `memory: 16384` |
| EFI | `bios: ovmf`, `efidisk0` exists |
| Disk | `scsi0` is `size=250G` on `ubuntu` |
| SCSI | `scsihw: virtio-scsi-single` |
| NIC | `net0` on vmbr0, `net1` on vmbr1 |
| Guest Agent | `agent: enabled=1` |
| ISO | `ubuntu-24.04.5-live-server-amd64.iso` on `ide2` |
| Boot | `boot: order=ide2;scsi0` (ISO first) |

You can also check only the ISO, boot order and disk.

⟦C26⟧

Example output:

⟦C27⟧

## 4.8 Starting the VM

**Run on: the Proxmox host (root@pve)**

⟦C28⟧

If you return to the prompt without an error, it has succeeded.

# Chapter 5: Installing Ubuntu Server

## 5.1 Starting the Installer

Do the following in the Proxmox web UI.

1. Select `VM 220 security-core`.
2. Open the **Console**.
3. In the installer menu, select `Try or Install Ubuntu Server`.

## 5.2 Settings During Installation

The screen-by-screen steps of the installer are the same as a standard Ubuntu Server installation and are omitted. Use the values in the following table.

| Item | Setting |
|---|---|
| Language | English (for consistency with logs and technical information) |
| Keyboard | Japanese (or the layout of the keyboard you use) |
| Installation type | Ubuntu Server |
| Network | Configure only the first NIC (`enp6s18`, vmbr0 side) |
| IP | `192.168.0.220/24` |
| Gateway | `192.168.0.1` |
| Host name | `security-core` |
| Storage | Use the entire 250 GB disk (LVM) |
| OpenSSH Server | Install |
| Additional packages | None |

> **Important:** `192.168.1.220` on the second NIC (`enp6s19`, vmbr1 side) is configured after installation. The default gateway is on the vmbr0 side only.

## 5.3 Removing the Installation Media

When the installation finishes, the Console shows the following message and stops.

⟦C29⟧

This is not an installation failure; the installer is waiting for the virtual CD-ROM (ISO) to be removed.

> **Note:** If you repeatedly run Shutdown or Reset from the web UI in this state, Proxmox may show the error "can't lock file '/var/lock...". Do not repeat Reset or Shutdown, and do not delete files in `/var/lock`. Remove the ISO with the following step instead.

**Run on: the Proxmox host (root@pve)**

⟦C30⟧

Only the virtual CD-ROM is removed. The 250 GB virtual disk is not affected.

Go back to the Proxmox Console and press `Enter`. Ubuntu reboots and the installed OS starts.

# Chapter 6: Initial OS Setup

The commands in this chapter are run as root on Ubuntu in VM 220, not on the Proxmox host.

## 6.1 Checking the OS and Network

**Run on: security-core VM 220 (root)**

⟦C31⟧

Also check the resources.

⟦C32⟧

Confirm the following state.

| Item | Expected value |
|---|---|
| OS | `PRETTY_NAME="Ubuntu 24.04.5 LTS"` |
| Host name | `security-core` |
| enp6s18 (vmbr0) | `192.168.0.220/24` |
| enp6s19 (vmbr1) | The NIC exists but has no IP address (DOWN) |
| Default route | `default via 192.168.0.1 dev enp6s18` |
| Memory | About 15 GiB, swap 4 GiB |

> **About NIC names:** On Ubuntu 24.04, the NICs are named `enp6s18` (vmbr0 side) and `enp6s19` (vmbr1 side). Their MAC addresses match Proxmox's `net0` and `net1`.

## 6.2 Checking the Netplan Settings

**Run on: security-core VM 220 (root)**

⟦C33⟧

⟦C34⟧

⟦C35⟧

Confirm that `50-cloud-init.yaml`, created by the installer, contains only the fixed IP and default route for `enp6s18`.

## 6.3 Adding a Fixed IP to the Internal LAN (enp6s19)

**Run on: security-core VM 220 (root)**

Set `192.168.1.220/24` on `enp6s19`. No gateway is set on `enp6s19`.

> If you are connected over SSH, also keep the Proxmox Console open in case the network is disconnected.

First, back up the configuration file.

⟦C36⟧

Rewrite the configuration file.

⟦C37⟧

Validate the configuration and apply it on trial.

⟦C38⟧

When the following confirmation appears, **press Enter immediately** to accept the settings.

⟦C39⟧

> **Note:** If you do not press Enter in time, "Reverting." is shown and the previous settings are restored automatically. This is not an error. In that case, run `netplan try --timeout 60` again.

## 6.4 Checking the Network Settings

**Run on: security-core VM 220 (root)**

⟦C40⟧

| Item | Expected value |
|---|---|
| enp6s18 / vmbr0 | `192.168.0.220/24` |
| enp6s19 / vmbr1 | `192.168.1.220/24` (UP) |
| Default gateway | Only `192.168.0.1` (enp6s18) |
| Internal LAN route | `192.168.1.0/24 dev enp6s19` |
| ping (Proxmox internal bridge `192.168.1.254`) | `3 packets transmitted, 3 received, 0% packet loss` |

## 6.5 Updating the OS

**Run on: security-core VM 220 (root)**

⟦C41⟧

When it finishes, reboot.

⟦C42⟧

After the reboot, check the state.

⟦C43⟧

| Item | Expected value |
|---|---|
| IP addresses | `192.168.0.220` and `192.168.1.220` are kept |
| Default gateway | `192.168.0.1` |
| `systemd-timesyncd` (time sync) | `active` |
| `qemu-guest-agent` | `inactive` at this point (installed in 6.7) |
| Root volume (`/`) | About 98 GB (extended in 6.6) |

## 6.6 Extending the Root Volume

With the installer's LVM layout, only 100 GB of the 250 GB virtual disk is assigned to the root volume. To make room for Wazuh Indexer's log storage, add all of the rest to the root volume.

**Run on: security-core VM 220 (root)**

Check the free space in LVM.

⟦C44⟧

Example output:

⟦C45⟧

There are about 146.95 GB unused. Add all of it to the root volume and extend the file system at the same time.

⟦C46⟧

Check the result.

⟦C47⟧

| Item | Expected value |
|---|---|
| Root volume | 243G |
| Free space | About 225G |
| Logical volume | `<246.95g` |

No reboot is needed.

## 6.7 Installing the QEMU Guest Agent

This is needed for Proxmox to obtain the VM's IP addresses and running state.

**Run on: security-core VM 220 (root)**

⟦C48⟧

Enable it at boot and start it.

⟦C49⟧

Check the status.

⟦C50⟧

If `Active: active (running)` is shown, it has succeeded.

## 6.8 State After the Initial OS Setup

| Item | State |
|---|---|
| OS | Ubuntu Server 24.04.5 LTS |
| Host name | `security-core` |
| enp6s18 | `192.168.0.220/24` (default gateway `192.168.0.1`) |
| enp6s19 | `192.168.1.220/24` (no gateway) |
| Root volume | 243 GB (about 225 GB free) |
| Time sync | active |
| QEMU Guest Agent | active (running) |
| OS updates | Done |

# Chapter 7: Installing Wazuh

## 7.1 Checking the Connection to the Distribution Server

Before downloading the installer, check DNS and HTTPS connectivity.

**Run on: security-core VM 220 (root)**

⟦C51⟧

Confirm that `packages.wazuh.com` resolves and that an HTTP response (`200`) is returned.

## 7.2 Downloading the Installer

Download the official installer. Do not run the installation yet.

**Run on: security-core VM 220 (root)**

⟦C52⟧

Check the file size (about 211 KB), the SHA256 and the first five lines (`#!/bin/bash` and `# Wazuh installer`).

## 7.3 Checking the Installer Version

**Run on: security-core VM 220 (root)**

⟦C53⟧

Example output:

⟦C54⟧

## 7.4 All-in-One Installation

The `-a` option installs the following three components together on the same host.

1. **Wazuh Indexer**: stores and searches security events
2. **Wazuh Server (Manager)**: manages agents and detects threats
3. **Wazuh Dashboard**: web management interface

**Run on: security-core VM 220 (root)**

⟦C55⟧

> **Notes when running**
>
> - The installation takes from a few minutes to a few tens of minutes.
> - If an error occurs on the way, check the log instead of running it again.
> - `wazuh-install-files.tar` contains certificates and the credentials of internal users. Do not expose it.

The installation has succeeded if `INFO: --- Summary ---` appears at the end, followed by the web URL, the user name `admin` and the initial password, and it finishes with `INFO: Installation finished.`

> **Important:** The initial password is shown on screen. Do not paste this output into chats or documents. The initial password is changed in Chapter 9.

# Chapter 8: Checking Services and Listening Ports

## 8.1 Checking That the Three Services Are Running

**Run on: security-core VM 220 (root)**

⟦C56⟧

All three lines showing `active` is normal.

## 8.2 Checking the Listening Ports

VM 220 has two networks, the normal LAN and the internal network, so check which interface each service listens on.

**Run on: security-core VM 220 (root)**

⟦C57⟧

⟦C58⟧

At build time the listening state was as follows.

| Port | Service | Listening on | Assessment |
|---|---|---|---|
| 443 | Dashboard | `0.0.0.0:443` | Reachable on all IPv4 interfaces |
| 55000 | Manager API | `0.0.0.0:55000` / `[::]:55000` | Reachable on all IPv4 and IPv6 interfaces |
| 9200 | Indexer | `127.0.0.1:9200` | Local only (good) |

It is desirable that the Indexer's port 9200 is limited to localhost. Access restrictions for the Manager API (55000) and the Dashboard (443) will be considered later.

## 8.3 Checking the API and Dashboard Settings

To consider access restrictions, check the current values in the Manager API and Dashboard configuration files and the state of the firewall. This is a check only; we do not edit configuration files or enable UFW.

**Run on: security-core VM 220 (root)**

⟦C59⟧

| Target | Future policy |
|---|---|
| Dashboard | Allow access from the management terminal |
| Manager API | In principle, restrict to localhost and the necessary internal sources |
| Indexer | Keep it limited to localhost |
| IPv6 | Prevent unintended external exposure |

> This check was done during the build, but its output was not recorded. Check the listen addresses and the UFW state with the output of your own environment. No settings are changed at this stage.

# Chapter 9: Changing the admin Password

## 9.1 How to Change It

`admin` is a reserved internal user of Wazuh Indexer. Trying to change it from the Dashboard's user management screen gives the following error.

⟦C60⟧

Change the `admin` password with the password management tool that comes with Wazuh. In an All-in-One setup, this tool also updates the credentials of related components such as Filebeat automatically.

## 9.2 Checking the Password Management Tool

**Run on: security-core VM 220 (root)**

⟦C61⟧

⟦C62⟧

Confirm that `wazuh-passwords-tool.sh` exists.

Check its usage.

⟦C63⟧

`-u` specifies the target user. Without `-p`, a new password is generated automatically.

## 9.3 Reissuing the Password (Without Showing It on Screen)

Generate the password automatically and save the output to a file readable only by root. This keeps the new password out of the screen and out of pasted logs.

**Run on: security-core VM 220 (root)**

⟦C64⟧

It has succeeded if the output includes the following.

- `INFO: Updating the internal users.`
- Creation of a backup of the internal users (`/etc/wazuh-indexer/internalusers-backup`)
- `The filebeat.yml file has been updated to use the Filebeat Keystore username and password.`
- `WARNING: Password changed. Remember to update the password ...` (a message asking you to restart the services)

Check the new password only on the VM's terminal.

⟦C65⟧

Save the displayed password in a secure password store. **Do not paste this output into chats or documents.**

## 9.4 Restarting the Services

To apply the password change, restart the services one at a time in the order Indexer → Manager → Filebeat → Dashboard. Confirm that each one is `active` before going on to the next.

**Run on: security-core VM 220 (root)**

Restart the Indexer.

⟦C66⟧

⟦C67⟧

Restart the Manager.

⟦C68⟧

⟦C69⟧

Restart Filebeat.

⟦C70⟧

⟦C71⟧

Restart the Dashboard.

⟦C72⟧

⟦C73⟧

The step is complete when all four services are `active`.

# Chapter 10: Checking Operation

## 10.1 Checking Internal Connections

Check whether each service responds over HTTP.

**Run on: security-core VM 220 (root)**

⟦C74⟧

Example output:

⟦C75⟧

| Component | Response | Meaning |
|---|---:|---|
| Indexer | 401 | Rejects access without credentials (authentication is responding) |
| Wazuh API | 401 | Same as above |
| Dashboard | 302 | Redirects to the login screen |

All of these are normal responses.

## 10.2 Checking the Connection from Filebeat to the Indexer

**Run on: security-core VM 220 (root)**

⟦C76⟧

Example output:

⟦C77⟧

If the TLS handshake and `talk to server... OK` are confirmed, the log forwarding path is working.

## 10.3 Logging In to the Dashboard

Open `https://192.168.0.220` in a browser on the management terminal.

- User name: `admin`
- Password: the password reissued in 9.3

A self-signed certificate warning may appear; this is expected at this stage. Confirm that you are connecting to `192.168.0.220` before proceeding.

Check the following three points.

1. You can log in.
2. The Wazuh Overview screen appears.
3. No Indexer or API connection errors are shown.

# Chapter 11: Installing the Wazuh Agent on the Proxmox Host

As the first monitored machine, register the Proxmox host `pve` (`192.168.0.240`), which manages the virtual machines. Wazuh will then be able to monitor the host OS's logs, file changes, security settings and so on. We add only the agent, without changing the existing Proxmox settings or network configuration.

| Traffic | Port | Purpose |
|---|---|---|
| Agent → Manager | TCP 1514 | Sending events |
| Agent → Manager | TCP 1515 | Agent registration (enrollment) |

## 11.1 Checking the Ports on the Manager Side

**Run on: security-core VM 220 (root)**

⟦C78⟧

| Port | Process | State |
|---|---|---|
| TCP 1514 | `wazuh-remoted` | LISTEN |
| TCP 1515 | `wazuh-authd` | LISTEN |

## 11.2 Checking the Proxmox Host Environment

At this stage, we do not install packages or change Proxmox settings.

**Run on: the Proxmox host (root@pve)**

⟦C79⟧

| Item | Expected value |
|---|---|
| Proxmox VE | 8.4.0 |
| OS | Debian 12 Bookworm |
| Architecture | `amd64` |
| Connectivity to VM 220 | 0% packet loss |
| Existing Wazuh agent | None (nothing is shown) |

## 11.3 Registering the Official Wazuh APT Repository

**Run on: the Proxmox host (root@pve)**

Install the required packages.

⟦C80⟧

Register the official signing key.

⟦C81⟧

Register the APT repository.

⟦C82⟧

Update the package information.

⟦C83⟧

Check the available versions.

⟦C84⟧

Confirm that `4.14.10-1` is shown as a candidate. Do not install the agent yet.

## 11.4 Checking Connectivity to the Agent Ports

Check that TCP 1514 and 1515 on VM 220 can be reached from the Proxmox host.

**Run on: the Proxmox host (root@pve)**

⟦C85⟧

The following output is normal.

⟦C86⟧

## 11.5 Installing Wazuh Agent 4.14.10

Install it pinned to the same version as the Manager.

**Run on: the Proxmox host (root@pve)**

⟦C87⟧

Check the version.

⟦C88⟧

If `Wazuh v4.14.10 - Wazuh Inc.` is shown, it has succeeded. Do not start the agent yet.

## 11.6 Setting the Manager Address

**Run on: the Proxmox host (root@pve)**

Back up the configuration file.

⟦C89⟧

Check the current settings.

⟦C90⟧

Confirm that it contains the initial value `<address>MANAGER_IP</address>`.

Replace it with the Manager's IP address, `192.168.0.220`.

⟦C91⟧

Check the result.

⟦C92⟧

Example output:

⟦C93⟧

## 11.7 Registering the Agent

First, check the settings of the registration service on the Manager side.

**Run on: security-core VM 220 (root)**

⟦C94⟧

| Setting | Value | Meaning |
|---|---|---|
| `disabled` | `no` | The registration service is enabled |
| `port` | `1515` | Registration port |
| `use_password` | `no` | No registration password is required |
| `use_source_ip` | `no` | The source IP is not registered as fixed |
| `purge` | `yes` | Old registrations are cleaned up |

From the Proxmox host, register the agent with the name `pve`.

**Run on: the Proxmox host (root@pve)**

⟦C95⟧

Example output:

⟦C96⟧

If `Valid key received` is shown, the agent's authentication key has been obtained from the Manager.

## 11.8 Starting the Agent

**Run on: the Proxmox host (root@pve)**

Enable it at boot and start it.

⟦C97⟧

Check the status.

⟦C98⟧

It has succeeded if `Active: active (running)` is shown and `wazuh-agentd`, `wazuh-syscheckd`, `wazuh-logcollector` and `wazuh-modulesd` are running.

> Memory use right after startup was about 844 MB. Keep the effect on memory in mind when installing it on other LXCs and so on.

## 11.9 Checking the Connection on the Manager Side

**Run on: security-core VM 220 (root)**

⟦C99⟧

Example output:

⟦C100⟧

Specify the ID shown in the list to check the details (`001` in the original build).

⟦C101⟧

Confirm `Status: Active` and that there are records of `Last keep alive` and Syscheck runs. `IP address: any` is normal because the source IP is not registered as fixed.

## 11.10 Checking the Agent Log

**Run on: the Proxmox host (root@pve)**

⟦C102⟧

Confirm that the following log entries appear.

| Function | Log to check |
|---|---|
| File integrity monitoring (FIM) | End of the initial scan (`File integrity monitoring scan ended`) |
| SCA security assessment | `Evaluation finished for policy '/var/ossec/ruleset/sca/cis_debian12.yml'`, `Security Configuration Assessment scan finished.` |
| Syscollector | System information collection complete |

Check the Rootcheck state and whether there are errors or warnings.

⟦C103⟧

⟦C104⟧

In the original build, Rootcheck showed only the start log `Starting rootcheck scan.`, and there were zero `ERROR`, `WARNING` or `CRITICAL` entries. The completion of Rootcheck will continue to be checked.

This completes the first stage of monitoring the Proxmox host.

# Chapter 12: Inventory of VMs and LXCs to Monitor

Before deploying agents to existing VMs and LXCs, list the targets. We do not install in bulk; we check the running guests one at a time and install individually.

**Run on: the Proxmox host (root@pve)**

⟦C105⟧

Based on the inventory taken at build time, we decided on the following policy.

| Category | Target | Policy |
|---|---|---|
| Proxmox host | `pve` | Installed |
| Wazuh management server | VM 220 `security-core` | Running |
| GPU / AI platform | VM 101 `ollama-gpu` | Decide after checking the OS and memory |
| Virtual machine | VM 104 `vs-ubuntu` | Decide after checking the OS |
| Monitoring platform | LXC 103 `lxc-prometheus`, LXC 105 `lxc-grafana` | Candidates for monitoring |
| Databases | LXC 109 `postgresql`, 503 `demo-postgresql` | Decide after checking importance and load |
| Applications | LXC 200, 129, 500, etc. | Select after checking status, OS and purpose |
| Storage / search | LXC 134, 502 | Decide after checking memory and purpose |

- Stopped VMs and LXCs are not included for now.
- TrueNAS, Windows and macOS are not targets for installing the Linux agent as is.
- RKE2 is out of scope. We also do not stop or delete its existing resources.

# Chapter 13: Approach for Installing on LXCs

Following the inventory in Chapter 12, install the Wazuh agent on the existing LXC containers one at a time. This chapter summarizes the approach common to Chapter 14 onward.

## 13.1 Two Ways to Run Commands

There are two ways to work on an LXC. This book shows the method actually used in the build.

| Method | Prompt example | Description |
|---|---|---|
| Run from the Proxmox host | `root@pve` | Prefix with `pct exec <CTID> --` to run a command inside the container from the host |
| Run inside the container | `root@lxc-prometheus` | Log in to the container as root and run commands directly |

> **Note:** `pct` is a command only on the Proxmox host. Running `pct exec ...` inside a container gives `-bash: pct: command not found`. Always check the prompt to see where you are.

## 13.2 Policy Common to All LXCs

- Do not change the settings of existing services (Prometheus, Grafana, PostgreSQL).
- Pin the agent version to 4.14.10-1, the same as the Manager.
- Before installing, check the OS, memory, whether an agent already exists and connectivity to the Manager.
- Install one at a time, and go on to the next only after confirming that it is `Active` on the Manager side.
- The Wazuh repository registered on the PVE host is not inherited inside LXCs. Register the signing key and repository for each LXC.

# Chapter 14: Installing on LXC 103 (lxc-prometheus)

## 14.1 Checking the Container

This step neither changes settings nor installs the agent.

**Run on: the Proxmox host (root@pve)**

⟦C106⟧

Results at build time:

| Item | Result |
|---|---|
| OS | Debian 13.5 (trixie) |
| CPU | 2 cores |
| Memory allocated | 4 GB (79 MiB used, 3.9 GiB available) |
| IP address | `192.168.0.197` |
| LXC type | unprivileged (nesting enabled) |

> In an unprivileged LXC, the results of Rootcheck, FIM (file integrity monitoring) and so on may differ from those of a normal VM because of restrictions on the host side.

## 14.2 Checking for an Existing Agent and the Route

**Run on: the Proxmox host (root@pve)**

⟦C107⟧

Example output:

⟦C108⟧

## 14.3 Checking Connectivity to the Manager

Check that TCP 1514 (agent traffic) and 1515 (agent registration) can be reached.

**Run on: the Proxmox host (root@pve)**

⟦C109⟧

The following output is normal.

⟦C110⟧

## 14.4 Checking the Repository Registration

**Run on: the Proxmox host (root@pve)**

⟦C111⟧

If only the headings are shown and neither the repository nor a candidate version appears, it is not registered. Register it with the following steps.

## 14.5 Registering the Signing Key

From here, work inside LXC 103. Select LXC 103 in the Proxmox web UI and log in as root from the **Console** (the prompt becomes `root@lxc-prometheus`).

**Run on: inside LXC 103 (root@lxc-prometheus)**

⟦C112⟧

If `Wazuh signing key installed.` is shown at the end, it has succeeded.

## 14.6 Registering the APT Repository

**Run on: inside LXC 103 (root@lxc-prometheus)**

⟦C113⟧

If `https://packages.wazuh.com/4.x/apt stable InRelease` is fetched, it has succeeded.

## 14.7 Checking the Candidate Version and Dependencies

**Run on: inside LXC 103 (root@lxc-prometheus)**

⟦C114⟧

Confirm that `Candidate: 4.14.10-1` is shown and that the dependencies are standard Debian packages (`libc6`, `lsb-release`, `debconf`, `adduser`, `procps`).

## 14.8 Installing the Agent

**Run on: inside LXC 103 (root@lxc-prometheus)**

⟦C115⟧

Only two packages are added: `lsb-release` and `wazuh-agent`. Do not register or start it yet.

## 14.9 Setting the Manager Address

**Run on: inside LXC 103 (root@lxc-prometheus)**

⟦C116⟧

Example output:

⟦C117⟧

## 14.10 Registering the Agent

Register the agent with the name `lxc-prometheus`.

**Run on: inside LXC 103 (root@lxc-prometheus)**

⟦C118⟧

If `INFO: Valid key received` is shown at the end, it has succeeded.

## 14.11 Starting the Agent

**Run on: inside LXC 103 (root@lxc-prometheus)**

⟦C119⟧

If `Active: active (running)` is shown, it has succeeded. Memory use at build time was about 84 MB, much lighter than on the Proxmox host (about 844 MB).

## 14.12 Checking on the Manager Side

**Run on: security-core VM 220 (root)**

⟦C120⟧

Example output:

⟦C121⟧

When `lxc-prometheus` is `Active`, installation on LXC 103 is complete.

# Chapter 15: Installing on LXC 105 (lxc-grafana)

## 15.1 Checking the Container

**Run on: inside LXC 105 (root@lxc-grafana)**

⟦C122⟧

**Run on: the Proxmox host (root@pve)**

⟦C123⟧

Results at build time:

| Item | Result |
|---|---|
| OS | Debian 13.5 (trixie) |
| CPU | 1 core |
| Memory allocated | 512 MB (170 MiB used, 341 MiB available) |
| Swap | 512 MB |
| RootFS | 4 GB (`osx` storage) |
| IP address | `192.168.0.199` |
| LXC type | unprivileged |

## 15.2 Adding Memory

Only 341 MiB of memory is available, and the agent used about 84 MB on LXC 103, so as things stand Grafana might stop for lack of memory. Increase the memory allocation before installing the agent.

| Item | Before | After |
|---|---:|---:|
| RAM | 512MB | **1,024MB** |
| Swap | 512MB | 512MB (unchanged) |
| CPU | 1 core | 1 core (unchanged) |
| RootFS | 4GB | 4GB (unchanged) |

Select LXC 105 in the Proxmox web UI and change **Memory** under **Resources** to 1,024 MB (do not change Swap, CPU or RootFS).

> **Guideline:** 1 GB is the minimum recommended value for the installation. For more headroom, consider 1.5 GB, or 2 GB if Grafana's data sources and dashboards will grow. Grafana may need to be stopped and restarted when the setting is changed.

Confirm that the change has been applied and that Grafana is running.

**Run on: the Proxmox host (root@pve)**

⟦C124⟧

Example output:

⟦C125⟧

Available memory has increased to about 802 MB, and Grafana is `active`.

## 15.3 Checks Before Installation

Check the required commands and whether an agent is already installed.

**Run on: the Proxmox host (root@pve)**

⟦C126⟧

Confirm that `curl` and `gpg` are found (`/bin/curl`, `/bin/gpg`) and that `Wazuh Agent not installed` is shown.

## 15.4 Registering the Signing Key and Repository

**Run on: the Proxmox host (root@pve)**

⟦C127⟧

If `Wazuh repository configured.` is shown, it has succeeded.

## 15.5 Checking the Candidate Version

**Run on: the Proxmox host (root@pve)**

⟦C128⟧

Confirm that `4.14.10-1` is shown as a candidate. We do not upgrade the whole system.

## 15.6 Installing the Agent

Install only the agent.

**Run on: the Proxmox host (root@pve)**

⟦C129⟧

Only two packages are added, `lsb-release` and `wazuh-agent`; the Grafana packages are not updated.

## 15.7 Setting the Manager Address

**Run on: the Proxmox host (root@pve)**

⟦C130⟧

Example output:

⟦C131⟧

## 15.8 Registering the Agent

**Run on: the Proxmox host (root@pve)**

⟦C132⟧

If `INFO: Valid key received` is shown at the end, it has succeeded.

## 15.9 Starting the Agent

**Run on: the Proxmox host (root@pve)**

⟦C133⟧

Confirm `Active: active (running)` and `enabled`. Memory use at build time was about 95 MB (peak about 97 MB).

## 15.10 Checking on the Manager Side

> VM 220 is a virtual machine (not an LXC), so commands cannot be run with `pct exec 220`. Log in to security-core directly and run them there.

**Run on: security-core VM 220 (root)**

⟦C134⟧

Example output:

⟦C135⟧

## 15.11 Checking Monitoring and Memory

Check not only that the agent is `Active`, but that monitoring is actually working.

**Run on: the Proxmox host (root@pve)**

⟦C136⟧

Results at build time:

| Item | Result |
|---|---|
| FIM | Initial scan complete |
| Rootcheck | `Ending rootcheck scan.` confirmed |
| SCA | Evaluation of `cis_debian13.yml` complete |
| Grafana | `active` |

The memory (RSS) of each process was as follows, about 58.9 MiB in total (this may double-count shared memory).

| Process | RSS |
|---|---:|
| wazuh-agentd | About 7.6 MiB |
| wazuh-syscheckd | About 13.6 MiB |
| wazuh-logcollector | About 16.6 MiB |
| wazuh-modulesd | About 21.1 MiB |

# Chapter 16: Installing on LXC 109 (postgresql)

PostgreSQL is an important platform that stores the AI defense system's audit logs and incident information. We do not change the database's existing data or settings.

## 16.1 Checking the Container

**Run on: the Proxmox host (root@pve)**

⟦C137⟧

⟦C138⟧

Results at build time:

| Item | Result |
|---|---|
| OS | Debian 13 (trixie) |
| PostgreSQL | 17.11, `active` |
| CPU | 2 cores |
| Memory allocated | 4,096 MB (139 MiB used, 3.9 GiB available) |
| Swap | 512 MB |
| RootFS | 50 GB (`local-lvm`) |
| IP address | `192.168.0.151` |
| LXC type | unprivileged |

There is plenty of memory, so no increase is needed.

## 16.2 Checks Before Installation

**Run on: the Proxmox host (root@pve)**

⟦C139⟧

Example output:

⟦C140⟧

## 16.3 Registering the Signing Key and Repository

**Run on: the Proxmox host (root@pve)**

⟦C141⟧

Example output:

⟦C142⟧

## 16.4 Checking the Candidate Version

**Run on: the Proxmox host (root@pve)**

⟦C143⟧

Confirm that `4.14.10-1` is shown as a candidate.

## 16.5 Installing the Agent

**Run on: the Proxmox host (root@pve)**

⟦C144⟧

If `Wazuh v4.14.10 - Wazuh Inc.` is shown, it has succeeded.

## 16.6 Setting the Manager Address

**Run on: the Proxmox host (root@pve)**

⟦C145⟧

Confirm that `<address>` in the `<client>` block is now `192.168.0.220` and that the backup file `ossec.conf.backup-before-manager` has been created.

## 16.7 Registering the Agent

Register the agent with the name `postgresql`.

**Run on: the Proxmox host (root@pve)**

⟦C146⟧

If `INFO: Valid key received` is shown at the end, it has succeeded.

## 16.8 Starting the Agent

**Run on: the Proxmox host (root@pve)**

⟦C147⟧

Confirm `active (running)` and `enabled`. Memory use at build time was about 93.3 MB.

## 16.9 Checking on the Manager Side

**Run on: security-core VM 220 (root)**

⟦C148⟧

Example output:

⟦C149⟧

## 16.10 Checking the Initial Scans

**Run on: the Proxmox host (root@pve)**

⟦C150⟧

Results at build time:

| Monitoring function | Result |
|---|---|
| FIM (file tampering detection) | Complete |
| Rootcheck | Complete |
| SCA (Debian 13 CIS benchmark assessment) | Complete |
| Syscollector | Complete |
| PostgreSQL service | `active` |

> **Reading the log:**
>
> - `netstat not available` means the port check function was skipped. It is not a fatal error.
> - The log entry about starting to monitor `/var/log/apache2/error.log` comes from the agent's default settings. PostgreSQL log monitoring is configured separately (Part 2).
> - An INFO line about starting Apache log monitoring may appear in the "WARNINGS / ERRORS" section, but it only matched the search words and is not an actual error.

## State at the End of Part 1

| Agent ID | Name | Target | State |
|---:|---|---|---|
| 000 | security-core | VM 220 (Manager) | Active/Local |
| 001 | pve | Proxmox host | Active |
| 002 | lxc-prometheus | LXC 103 | Active |
| 003 | lxc-grafana | LXC 105 (RAM increased to 1 GB) | Active |
| 004 | postgresql | LXC 109 | Active |

| Item | State |
|---|---|
| Wazuh Indexer / Manager / Dashboard | 4.14.10, active |
| Filebeat | active, connection to the Indexer OK |
| `admin` password | Reissued (without showing it on screen) |
| Dashboard | Login possible at `https://192.168.0.220` |

Wazuh now monitors five machines, including the Manager itself.

In Part 2, we monitor the PostgreSQL logs of LXC 109 with Wazuh. To avoid forwarding SQL statements and parameter values to the Wazuh Manager, we build a mechanism that sanitizes the logs locally (removes unneeded information) before sending them.

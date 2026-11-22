---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 10: Handling a Disk Failure and Preparing the AI Defense Manager"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 10 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". During the checks in Part 9, we found that Wazuh rule 5138 (`General SATA disk failure`) was firing on the Proxmox host. The first half of Part 10 covers investigating the cause, safely detaching and removing the failed backup HDD, and tidying up the Proxmox settings. In the second half, we resume the build, create a new VM, the "AI Defense Manager" (VM 230), which handles AI analysis and decisions, and do its initial setup and checks.

This is a case in which the defense system detected a failure in the infrastructure it runs on.

## Notation

- Commands are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Each step begins with "Run on", which says where to run it.
- Disk models, serial numbers, sizes and so on are those at build time and will differ in your environment. Replace device names (`/dev/sdg`) and SATA ports (`ata11`) with the ones you confirm in your own environment.

## Conclusion (Up Front)

| Item | Details |
|---|---|
| What failed | The backup HDD (Hitachi HDS722020ALA330, 2 TB, `/dev/sdg`, Proxmox storage `backup`) |
| Symptoms | Recognized with a capacity of 0 bytes; reads fail with `I/O error`. SATA communication errors (`BadCRC` and others) repeat, and the link speed drops to 1.5 Gbps |
| Action | Stop writes and make it read-only, unmount it, shut down the host and remove the HDD, delete the storage definition |
| Data | It could not be read, so the backups on the HDD were abandoned |

# Chapter 1: The Disk Anomaly Detected by Wazuh

## 1.1 Rule 5138 Messages

Show the kernel messages recorded by Wazuh, grouping identical ones. Long alphanumeric strings such as serial numbers are masked.

**Run on: security-core VM 220 (root)**

⟦C0⟧

At build time these were SATA disk read/write errors, such as failures of `READ FPDMA QUEUED` and `WRITE FPDMA QUEUED`. Rather than treating them as false positives, check on the Proxmox host.

## 1.2 Kernel Log on the Proxmox Host

**Run on: Proxmox host pve (root)**

⟦C1⟧

⟦C2⟧

At build time, real I/O errors were occurring on `/dev/sdg`.

# Chapter 2: Diagnosing the Disk

## 2.1 SMART

**Run on: Proxmox host pve (root)**

⟦C3⟧

At build time the following was shown, and SMART information could not be obtained.

⟦C4⟧

Relax the checks and query it as ATA as well.

⟦C5⟧

⟦C6⟧

⟦C7⟧

From the OS's point of view, the disk could not return its own information.

## 2.2 Capacity Mismatch

**Run on: Proxmox host pve (root)**

⟦C8⟧

⟦C9⟧

⟦C10⟧

At build time, `/dev/sdg` was treated as 0 bytes (0 sectors), while the partition on it (`/dev/sdg1`, about 2 TB) was still mounted at `/mnt/pve/backup`. Because the whole disk's capacity is 0, merely reading the start of the partition (sector 2048) gives an "attempt to access beyond end of device" error.

## 2.3 The Connection Path

**Run on: Proxmox host pve (root)**

⟦C11⟧

⟦C12⟧

At build time, a Hitachi HDS722020ALA330 (about 2 TB) was connected to `ata11` (SCSI host 10) of the AMD FCH SATA controller on the motherboard (Supermicro H12SSL-i).

# Chapter 3: Preserving the Backup Area

## 3.1 How Proxmox Uses It

**Run on: Proxmox host pve (root)**

⟦C13⟧

Only the kernel mount was using it; there were no user processes.

⟦C14⟧

⟦C15⟧

`backup` was a directory-type storage registered in Proxmox (`dir: backup`, `path /mnt/pve/backup`), with state `active` and a capacity of about 1.92 TB.

## 3.2 File System State

**Run on: Proxmox host pve (root)**

⟦C16⟧

⟦C17⟧

At build time, merely reading the directory's contents gave the following error.

⟦C18⟧

⟦C19⟧

## 3.3 Switching to Read-Only

To prevent any further writes, remount it read-only (`ro`). No repair (`fsck`) or deletion is done.

**Run on: Proxmox host pve (root)**

⟦C20⟧

⟦C21⟧

⟦C22⟧

## 3.4 Preparing a Rescue Destination (Detaching a TrueNAS Disk)

The host had no file system with enough free space to receive 2 TB. We decided to use RAID_A (about 2.17 TB), the data virtual disk of TrueNAS (VM 100), as the rescue destination.

**Run on: Proxmox host pve (root)**

⟦C23⟧

⟦C24⟧

Shut down TrueNAS cleanly.

⟦C25⟧

⟦C26⟧

Confirm `status: stopped`. Check the contents of RAID_A and RAID_B.

⟦C27⟧

⟦C28⟧

Detach RAID_A (`scsi1`) from VM 100. The virtual disk itself is not deleted; it remains as `unused0`.

⟦C29⟧

⟦C30⟧

⟦C31⟧

At build time the underlying device was `/dev/RAID_A/vm-100-disk-0`.

> The rescue was not carried out after all, because it turned out that the original disk could not be read (Chapter 4). RAID_A remains detached from VM 100 (`unused0`). We decided to consider what to do with TrueNAS (VM 100) separately, and that RAID_A and RAID_B may be used freely for other purposes from now on (they are used in a later part).

# Chapter 4: Isolating the Cause

## 4.1 The Size of What Would Be Rescued

**Run on: Proxmox host pve (root)**

⟦C32⟧

⟦C33⟧

⟦C34⟧

`df` showed about 123 GB used, but both `du` and listing the `dump` directory gave `Input/output error`, and nothing could be read out as files. Without unplugging and replugging cables, investigate the state from the software side.

## 4.2 Device and Link State

**Run on: Proxmox host pve (root)**

⟦C35⟧

⟦C36⟧

## 4.3 Unmounting

Unmount it so that the file system no longer accesses the disk.

**Run on: Proxmox host pve (root)**

⟦C37⟧

## 4.4 Link Records Since Boot

**Run on: Proxmox host pve (root)**

⟦C38⟧

At boot it was recognized correctly.

⟦C39⟧

After that, communication errors repeated.

⟦C40⟧

`BadCRC` and `10B8B` indicate that data was corrupted in the middle of SATA communication.

⟦C41⟧

## 4.5 Re-reading the Capacity

Make it re-read the capacity and see whether it comes back.

**Run on: Proxmox host pve (root)**

⟦C42⟧

⟦C43⟧

At build time it stayed at 0 bytes.

⟦C44⟧

⟦C45⟧

## 4.6 SATA Link Speed and Ports

**Run on: Proxmox host pve (root)**

⟦C46⟧

The link, which was 3.0 Gbps at boot, had dropped to 1.5 Gbps.

⟦C47⟧

SCSI identification information could be obtained, but getting the capacity failed.

⟦C48⟧

⟦C49⟧

Compare with the speeds of the other ports.

⟦C50⟧

At build time the AMD FCH SATA controller had eight ports, `ata11`–`ata18`, and only `ata11` (this HDD) had dropped to 1.5 Gbps.

## 4.7 Decision

The capacity stayed at 0, SATA communication errors kept repeating, and the link speed had dropped. We judged that the backups on the HDD could not be read and decided **to abandon both the HDD and the backups on it**.

> The data on the HDD cannot be erased by software. To prevent information leaks, physically destroy the platters of the removed HDD, or ask a specialist that handles physical destruction to dispose of it.

# Chapter 5: Removing the HDD and Tidying Up the Storage

## 5.1 Removal

Do not pull it out while it is connected to SATA. Stop the running VMs and containers, shut down the Proxmox host cleanly, and remove the HDD. After removing it, start the host.

## 5.2 Checks After Removal

**Run on: Proxmox host pve (root)**

⟦C51⟧

After a reboot, device names may be reassigned (at build time, another disk became `sdg`). Use the model and serial number to confirm that the failed HDD is gone.

⟦C52⟧

At build time we confirmed that the 2 TB Hitachi HDD was not in the list.

## 5.3 Deleting the Storage Definition

**Run on: Proxmox host pve (root)**

⟦C53⟧

The `backup` definition for the removed HDD remains.

⟦C54⟧

⟦C55⟧

Delete only the `backup` storage definition. No other disks, files or storage settings are touched.

⟦C56⟧

⟦C57⟧

Confirm that `backup` is gone from the list and that the other storage remains `active`.

# Chapter 6: Creating the AI Defense Manager (VM 230)

The part responsible for AI analysis, decisions and responses is built as an independent new VM rather than placed in an existing one.

## 6.1 Checking the Location and Free Space

**Run on: Proxmox host pve (root)**

⟦C58⟧

⟦C59⟧

`local-lvm` (volume group `pve`) is on an NVMe SSD (`/dev/nvme0n1p3`). At build time the thin pool was about 794 GiB, 60.86% used.

⟦C60⟧

Confirm that VMID 230 is not in use (that no configuration exists for it).

⟦C61⟧

⟦C62⟧

At build time `ubuntu-24.04.5-live-server-amd64.iso` was present, and about 124 GiB of the host's roughly 283 GiB of memory was free.

## 6.2 Creating and Starting the VM

| Item | Setting |
|---|---|
| VMID / name | 230 / `ai-defense-manager` |
| CPU / memory | 4 cores (`host`) / 8 GB |
| Disk | 100 GB on `local-lvm` (`discard=on`, `iothread=1`) |
| Network | `vmbr0` (virtio) |
| QEMU Guest Agent | Enabled |

**Run on: Proxmox host pve (root)**

⟦C63⟧

A warning says that protection against the thin pool running out of space is disabled, but the VM is created.

⟦C64⟧

⟦C65⟧

⟦C66⟧

⟦C67⟧

## 6.3 Installing Ubuntu Server

Open the "Console" of VM 230 in the Proxmox web UI, choose `Try or Install Ubuntu Server`, and install with the following settings.

| Item | Setting |
|---|---|
| Language | English |
| Keyboard | Japanese |
| Network | DHCP |
| Proxy | Blank |
| Mirror | Default |
| Storage | Use an entire disk (target only the 100 GB virtual disk), LVM enabled |
| User name | `aidefense` |
| Host name | `ai-defense-manager` |
| OpenSSH Server | Install |
| Featured snaps | Select none |

On the storage screen, take care not to select anything other than the 100 GB virtual disk (such as host disks or RAID_A/RAID_B).

# Chapter 7: Network and Reachability of Neighboring Servers

## 7.1 Addresses and Routes

**Run on: VM 230 ai-defense-manager (root)**

⟦C68⟧

⟦C69⟧

At build time, DHCP assigned `192.168.0.33/24`, and the default gateway was `192.168.0.1`.

## 7.2 Reachability of security-core and Ollama

**Run on: VM 230 ai-defense-manager (root)**

⟦C70⟧

⟦C71⟧

Connect to the API of the existing Ollama (GPU server, `192.168.0.180`) and get the list of available models.

⟦C72⟧

# Chapter 8: OS Updates and Initial Checks

## 8.1 Updating Packages

**Run on: VM 230 ai-defense-manager (root)**

⟦C73⟧

⟦C74⟧

First check what would change with a trial run (simulation) only.

⟦C75⟧

At build time there were 29 upgrades, 0 new installs and 0 removals, with 11 systemd-related packages held back (not included).

⟦C76⟧

⟦C77⟧

At build time it showed `REBOOT_NOT_REQUIRED`, so no reboot was needed.

## 8.2 SSH State

**Run on: VM 230 ai-defense-manager (root)**

⟦C78⟧

⟦C79⟧

⟦C80⟧

⟦C81⟧

⟦C82⟧

At build time, a Windows PC (`192.168.0.251`) was connected over SSH as `aidefense` with password authentication, and no public keys were registered for either root or `aidefense`. To keep the current connection, the SSH settings, such as switching to public-key authentication, were not changed.

## 8.3 Checking Resources

**Run on: VM 230 ai-defense-manager (root)**

⟦C83⟧

⟦C84⟧

⟦C85⟧

⟦C86⟧

⟦C87⟧

At build time the root allocation was 48 GB, and space remained in the volume group `ubuntu-vg` (about 98 GB) (this is the installer's default behavior). Memory was 7.8 GiB and the CPU was four AMD EPYC cores.

## 8.4 Network, Time and Host Name

**Run on: VM 230 ai-defense-manager (root)**

⟦C88⟧

⟦C89⟧

At build time the setting was simple DHCP (no change needed).

⟦C90⟧

⟦C91⟧

## 8.5 Reachability of the Wazuh API and the Ollama API

**Run on: VM 230 ai-defense-manager (root)**

⟦C92⟧

⟦C93⟧

If both show `succeeded`, they are reachable.

## 8.6 Python

**Run on: VM 230 ai-defense-manager (root)**

⟦C94⟧

⟦C95⟧

At build time this was Python 3.12.3.

# Summary of Part 10

## What Was Done

| Order | Details |
|---|---|
| 1 | Found an anomaly in the Proxmox host's backup HDD from Wazuh rule 5138 |
| 2 | Examined SMART, capacity and the SATA link, and judged the HDD to have failed (capacity 0, communication errors, reduced speed) |
| 3 | Made it read-only and then unmounted it to stop writes |
| 4 | Shut down the host, removed the HDD, and deleted Proxmox's `backup` definition |
| 5 | Created the AI Defense Manager (VM 230, `192.168.0.33`), installed Ubuntu Server 24.04.5, and updated and checked it |

## Remaining Issues

- The backups on the HDD were lost. A replacement storage location will be prepared separately from this book (we judged that operating without one is not a problem).
- What to do with TrueNAS (VM 100) will be considered separately. We decided that RAID_A (`unused0`) and RAID_B may be used for other purposes from now on.
- Physically destroy the removed HDD when disposing of it.
- **[Risk, open]** SSH on VM 230 still uses password authentication. It has not been switched to public-key authentication.

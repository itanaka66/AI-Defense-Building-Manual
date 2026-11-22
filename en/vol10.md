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

```bash
python3 - <<'PY'
import json
from pathlib import Path
from collections import Counter

p = Path("/var/ossec/logs/alerts/2026/Nov/ossec-alerts-20.json")
messages = Counter()
first = {}
last = {}

with p.open() as f:
    for line in f:
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue

        if str((e.get("rule") or {}).get("id")) != "5138":
            continue

        ts = e.get("timestamp", "")
        msg = e.get("full_log") or ""

        # Mask long alphanumeric strings that look like serial numbers
        import re
        msg = re.sub(r'\b[A-Fa-f0-9]{12,}\b', '[REDACTED_ID]', msg)

        messages[msg] += 1
        first[msg] = min(first.get(msg, ts), ts)
        last[msg] = max(last.get(msg, ts), ts)

print("=== UNIQUE KERNEL MESSAGES ===")
for msg, count in messages.most_common():
    print(f"count={count} first={first[msg]} last={last[msg]}")
    print(msg[:1000])
    print("---")
PY
```

At build time these were SATA disk read/write errors, such as failures of `READ FPDMA QUEUED` and `WRITE FPDMA QUEUED`. Rather than treating them as false positives, check on the Proxmox host.

## 1.2 Kernel Log on the Proxmox Host

**Run on: Proxmox host pve (root)**

```bash
echo "=== JOURNAL BOOTS ==="
journalctl --list-boots --no-pager

echo
echo "=== RETAINED SATA ERROR LOGS ==="
journalctl -k --no-pager \
  | grep -Ei 'ata7|ata11|I/O error|blk_update|Buffer I/O|reset|failed command|exception|SError|Emask|EH complete' \
  | tail -n 100
```

```bash
echo "=== BLOCK DEVICE INVENTORY ==="
lsblk -o NAME,MAJ:MIN,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL,TRAN,RO

echo
echo "=== SDG DEVICE LINKS ==="
find -L /dev/disk/by-id -maxdepth 1 -type b -samefile /dev/sdg -printf '%p\n' 2>/dev/null

echo
echo "=== SDG SYSFS DETAILS ==="
for f in vendor model rev state; do
  p="/sys/block/sdg/device/$f"
  [ -r "$p" ] && printf '%s=' "$f" && cat "$p"
done
```

At build time, real I/O errors were occurring on `/dev/sdg`.

# Chapter 2: Diagnosing the Disk

## 2.1 SMART

**Run on: Proxmox host pve (root)**

```bash
smartctl -x /dev/sdg
```

At build time the following was shown, and SMART information could not be obtained.

```text
Short INQUIRY response, skip product id
A mandatory SMART command failed
```

Relax the checks and query it as ATA as well.

```bash
smartctl -x -T permissive /dev/sdg
```

```bash
smartctl -x -d sat -T permissive /dev/sdg
```

```text
Read Device Identity failed: empty IDENTIFY data
Device Model: [No Information Found]
```

From the OS's point of view, the disk could not return its own information.

## 2.2 Capacity Mismatch

**Run on: Proxmox host pve (root)**

```bash
journalctl -k -b --no-pager | grep -Ei 'sdg|ata[0-9]+.*(error|failed|reset|exception|link)'
```

```text
[sdg] access beyond end of device
I/O error, dev sdg, sector 2048
```

```bash
echo "=== BACKUP MOUNT ==="
findmnt -T /mnt/pve/backup -o SOURCE,TARGET,FSTYPE,OPTIONS

echo
echo "=== DEVICE CAPACITY ==="
printf 'sdg sectors: '
cat /sys/block/sdg/size
printf 'sdg1 sectors: '
cat /sys/block/sdg/sdg1/size
printf 'sdg bytes: '
blockdev --getsize64 /dev/sdg
printf 'sdg1 bytes: '
blockdev --getsize64 /dev/sdg1

echo
echo "=== DEVICE TREE ==="
lsblk -o NAME,MAJ:MIN,SIZE,TYPE,FSTYPE,MOUNTPOINTS /dev/sdg
```

At build time, `/dev/sdg` was treated as 0 bytes (0 sectors), while the partition on it (`/dev/sdg1`, about 2 TB) was still mounted at `/mnt/pve/backup`. Because the whole disk's capacity is 0, merely reading the start of the partition (sector 2048) gives an "attempt to access beyond end of device" error.

## 2.3 The Connection Path

**Run on: Proxmox host pve (root)**

```bash
echo "=== SCSI DEVICE PATH ==="
readlink -f /sys/block/sdg/device

echo
echo "=== UDEV DEVICE ATTRIBUTES ==="
udevadm info --query=property --name=/dev/sdg \
  | grep -E '^(DEVNAME|DEVPATH|ID_BUS|ID_MODEL|ID_SERIAL|ID_VENDOR|ID_WWN|ID_PATH|ID_TYPE)='

echo
echo "=== SCSI HOST INFORMATION ==="
for f in /sys/class/scsi_host/host10/proc_name \
         /sys/class/scsi_host/host10/unique_id; do
  if [ -r "$f" ]; then
    printf '%s=' "$f"
    cat "$f"
  fi
done
```

```bash
echo "=== ATA11 SYSFS ==="
for f in /sys/class/ata_link/link*/device; do
  [ "$(readlink -f "$f")" = "$(readlink -f /sys/class/ata_port/ata11)" ] && echo "$f"
done

echo
echo "=== ATA11 LINK ATTRIBUTES ==="
find /sys/class/ata_port/ata11 -maxdepth 3 -type f \
  \( -name 'sata_spd' -o -name 'sata_spd_limit' -o -name 'hw_sata_spd_limit' -o -name 'enabled' \) \
  -print -exec cat {} \; 2>/dev/null

echo
echo "=== ATA11 KERNEL LOG ==="
journalctl -k -b --no-pager | grep -Ei 'ata11|52:00.2|sdg' | tail -80
```

At build time, a Hitachi HDS722020ALA330 (about 2 TB) was connected to `ata11` (SCSI host 10) of the AMD FCH SATA controller on the motherboard (Supermicro H12SSL-i).

# Chapter 3: Preserving the Backup Area

## 3.1 How Proxmox Uses It

**Run on: Proxmox host pve (root)**

```bash
fuser -vm /mnt/pve/backup
```

Only the kernel mount was using it; there were no user processes.

```bash
echo "=== PVE STORAGE CONFIGURATION ==="
grep -n -B 3 -A 8 -E 'backup|/mnt/pve/backup' /etc/pve/storage.cfg

echo
echo "=== BACKUP DIRECTORY METADATA ==="
stat /mnt/pve/backup
```

```bash
pvesm status --storage backup
```

`backup` was a directory-type storage registered in Proxmox (`dir: backup`, `path /mnt/pve/backup`), with state `active` and a capacity of about 1.92 TB.

## 3.2 File System State

**Run on: Proxmox host pve (root)**

```bash
journalctl -k -b --no-pager | grep -Ei 'EXT4-fs.*(error|warning|abort)|sdg'
```

```bash
echo "=== DIRECTORY ENTRIES ==="
ls -la /mnt/pve/backup

echo
echo "=== MOUNT SUPERBLOCK ==="
findmnt -T /mnt/pve/backup -o SOURCE,FSTYPE,OPTIONS,FSROOT
```

At build time, merely reading the directory's contents gave the following error.

```text
ls: cannot access '/mnt/pve/backup/lost+found': Input/output error

d????????? ? ? ? ? lost+found
```

```bash
echo "=== EXT4 MOUNT STATUS ==="
grep -F '/mnt/pve/backup' /proc/mounts

echo
echo "=== EXT4 SUPERBLOCK PARAMETERS ==="
tune2fs -l /dev/sdg1 2>&1 \
  | grep -Ei 'Filesystem state|Errors behavior|Filesystem features|Block count|Block size|Last checked'
```

## 3.3 Switching to Read-Only

To prevent any further writes, remount it read-only (`ro`). No repair (`fsck`) or deletion is done.

**Run on: Proxmox host pve (root)**

```bash
mount -o remount,ro /mnt/pve/backup && \
findmnt -T /mnt/pve/backup -o SOURCE,TARGET,FSTYPE,OPTIONS
```

```text
/dev/sdg1 /mnt/pve/backup ext4 ro,relatime
```

```bash
echo "=== BLOCK DEVICES ==="
lsblk -e 7 -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL,RO

echo
echo "=== FILESYSTEM CAPACITY ==="
df -hT
```

## 3.4 Preparing a Rescue Destination (Detaching a TrueNAS Disk)

The host had no file system with enough free space to receive 2 TB. We decided to use RAID_A (about 2.17 TB), the data virtual disk of TrueNAS (VM 100), as the rescue destination.

**Run on: Proxmox host pve (root)**

```bash
qm config 100
```

```bash
qm status 100
```

Shut down TrueNAS cleanly.

```bash
qm shutdown 100 --timeout 120
```

```bash
qm status 100
```

Confirm `status: stopped`. Check the contents of RAID_A and RAID_B.

```bash
pvesm list RAID_A --vmid 100
```

```bash
pvesm list RAID_B --vmid 100
```

Detach RAID_A (`scsi1`) from VM 100. The virtual disk itself is not deleted; it remains as `unused0`.

```bash
qm set 100 --delete scsi1
```

```bash
qm config 100
```

```bash
pvesm path RAID_A:vm-100-disk-0
```

At build time the underlying device was `/dev/RAID_A/vm-100-disk-0`.

> The rescue was not carried out after all, because it turned out that the original disk could not be read (Chapter 4). RAID_A remains detached from VM 100 (`unused0`). We decided to consider what to do with TrueNAS (VM 100) separately, and that RAID_A and RAID_B may be used freely for other purposes from now on (they are used in a later part).

# Chapter 4: Isolating the Cause

## 4.1 The Size of What Would Be Rescued

**Run on: Proxmox host pve (root)**

```bash
echo "=== TARGET DEVICE SIZE ==="
blockdev --getsize64 /dev/RAID_A/vm-100-disk-0

echo
echo "=== TARGET LOGICAL VOLUME ==="
lvs -a -o lv_name,vg_name,lv_size,lv_attr,pool_lv,data_percent,metadata_percent RAID_A
```

```bash
echo "=== BACKUP DIRECTORY SIZES ==="
du -x -h -d 2 /mnt/pve/backup 2>&1

echo
echo "=== FILESYSTEM USAGE ==="
df -hT /mnt/pve/backup
```

```bash
ls -lah /mnt/pve/backup/dump
```

`df` showed about 123 GB used, but both `du` and listing the `dump` directory gave `Input/output error`, and nothing could be read out as files. Without unplugging and replugging cables, investigate the state from the software side.

## 4.2 Device and Link State

**Run on: Proxmox host pve (root)**

```bash
echo "=== SDG DEVICE STATE ==="
for f in size ro device/state device/model device/rev; do
  p="/sys/block/sdg/$f"
  if [ -r "$p" ]; then
    printf '%s=' "$f"
    cat "$p"
  fi
done

echo
echo "=== SATA LINK STATE ==="
for f in /sys/class/ata_link/link*/{sata_spd,sata_spd_limit}; do
  [ -r "$f" ] && printf '%s=' "$f" && cat "$f"
done
```

```bash
journalctl -k -b --no-pager | grep -Ei 'ata11|sdg|hard resetting link|SATA link down|failed command|IDENTIFY' | tail -n 100
```

## 4.3 Unmounting

Unmount it so that the file system no longer accesses the disk.

**Run on: Proxmox host pve (root)**

```bash
umount /mnt/pve/backup
```

## 4.4 Link Records Since Boot

**Run on: Proxmox host pve (root)**

```bash
journalctl -k -b --no-pager | grep -Ei 'ata11|scsi 10:|sdg:|sd 10:0:0:0' | head -n 80
```

At boot it was recognized correctly.

```text
ata11: SATA link up 3.0 Gbps
ata11.00: ATA-8: Hitachi HDS722020ALA330
ata11.00: 3907029168 sectors
```

After that, communication errors repeated.

```text
interface fatal error
SError: { UnrecovData CommWake 10B8B BadCRC }
failed command: READ FPDMA QUEUED
hard resetting link
```

`BadCRC` and `10B8B` indicate that data was corrupted in the middle of SATA communication.

```bash
echo "=== SCSI HOST 10 DEVICES ==="
ls -la /sys/class/scsi_host/host10/device/

echo
echo "=== CURRENT SDG DEVICE ==="
ls -la /sys/block/sdg/device/
```

## 4.5 Re-reading the Capacity

Make it re-read the capacity and see whether it comes back.

**Run on: Proxmox host pve (root)**

```bash
echo 1 > /sys/block/sdg/device/rescan
```

```bash
echo "=== DEVICE CAPACITY ==="
blockdev --getsize64 /dev/sdg

echo
echo "=== KERNEL SECTOR COUNT ==="
cat /sys/block/sdg/size

echo
echo "=== PARTITION CAPACITY ==="
blockdev --getsize64 /dev/sdg1 2>&1
```

At build time it stayed at 0 bytes.

```bash
journalctl -k --since "2026-11-20 15:20:00" --no-pager | grep -Ei 'ata11|sdg|I/O error|reset|failed command|hard resetting|BadCRC|CommWake' | tail -80
```

```text
Read Capacity(16) failed
```

## 4.6 SATA Link Speed and Ports

**Run on: Proxmox host pve (root)**

```bash
echo "=== ATA LINK 11 ERROR COUNTERS ==="
for f in /sys/class/ata_link/link11/{hw_sata_spd_limit,sata_spd,sata_spd_limit}; do
  if [ -r "$f" ]; then
    printf '%s: ' "$f"
    cat "$f"
  fi
done

echo
echo "=== ATA PORT ERROR HISTORY ==="
journalctl -k --no-pager | grep -E 'ata11.*(SError|BadCRC|CommWake|hard resetting|SATA link up)' | tail -30
```

The link, which was 3.0 Gbps at boot, had dropped to 1.5 Gbps.

```bash
echo "=== SCSI DEVICE STATE ==="
cat /sys/block/sdg/device/state

echo
echo "=== DEVICE INQUIRY ==="
cat /sys/block/sdg/device/inquiry | od -An -tx1

echo
echo "=== DEVICE IDENTITY ==="
for f in vendor model rev; do
  printf '%s: ' "$f"
  cat "/sys/block/sdg/device/$f"
done
```

SCSI identification information could be obtained, but getting the capacity failed.

```bash
lspci -nnk -s 52:00.2
```

```bash
echo "=== ATA PORT NUMBER ==="
cat /sys/class/ata_port/ata11/port_no

echo
echo "=== PMP LINKS ==="
cat /sys/class/ata_port/ata11/nr_pmp_links

echo
echo "=== ATA LINK DIRECTORY ==="
ls -la /sys/class/ata_link/link11/
```

Compare with the speeds of the other ports.

```bash
for n in 11 12 13 14 15 16 17 18; do
  printf 'ata%s: ' "$n"
  if [ -r "/sys/class/ata_link/link$n/sata_spd" ]; then
    cat "/sys/class/ata_link/link$n/sata_spd"
  else
    echo "no link"
  fi
done
```

At build time the AMD FCH SATA controller had eight ports, `ata11`–`ata18`, and only `ata11` (this HDD) had dropped to 1.5 Gbps.

## 4.7 Decision

The capacity stayed at 0, SATA communication errors kept repeating, and the link speed had dropped. We judged that the backups on the HDD could not be read and decided **to abandon both the HDD and the backups on it**.

> The data on the HDD cannot be erased by software. To prevent information leaks, physically destroy the platters of the removed HDD, or ask a specialist that handles physical destruction to dispose of it.

# Chapter 5: Removing the HDD and Tidying Up the Storage

## 5.1 Removal

Do not pull it out while it is connected to SATA. Stop the running VMs and containers, shut down the Proxmox host cleanly, and remove the HDD. After removing it, start the host.

## 5.2 Checks After Removal

**Run on: Proxmox host pve (root)**

```bash
echo "=== REMOVED HDD DEVICE CHECK ==="
if [ -e /sys/block/sdg ]; then
  echo "WARNING: sdg still exists"
else
  echo "OK: sdg is no longer detected"
fi

echo
echo "=== BACKUP MOUNT CHECK ==="
if findmnt /mnt/pve/backup; then
  echo "WARNING: backup is still mounted"
else
  echo "OK: backup is not mounted"
fi
```

After a reboot, device names may be reassigned (at build time, another disk became `sdg`). Use the model and serial number to confirm that the failed HDD is gone.

```bash
lsblk -d -o NAME,SIZE,MODEL,SERIAL,WWN,TRAN
```

At build time we confirmed that the 2 TB Hitachi HDD was not in the list.

## 5.3 Deleting the Storage Definition

**Run on: Proxmox host pve (root)**

```bash
cat /etc/pve/storage.cfg
```

The `backup` definition for the removed HDD remains.

```text
dir: backup
        path /mnt/pve/backup
        content snippets,images,iso,backup,vztmpl,rootdir
        is_mountpoint 1
        nodes pve
```

```bash
pvesm status
```

Delete only the `backup` storage definition. No other disks, files or storage settings are touched.

```bash
pvesm remove backup
```

```bash
pvesm status
```

Confirm that `backup` is gone from the list and that the other storage remains `active`.

# Chapter 6: Creating the AI Defense Manager (VM 230)

The part responsible for AI analysis, decisions and responses is built as an independent new VM rather than placed in an existing one.

## 6.1 Checking the Location and Free Space

**Run on: Proxmox host pve (root)**

```bash
lvs -a -o vg_name,lv_name,lv_size,data_percent,metadata_percent
```

```bash
pvs -o pv_name,vg_name,pv_size,pv_free
```

`local-lvm` (volume group `pve`) is on an NVMe SSD (`/dev/nvme0n1p3`). At build time the thin pool was about 794 GiB, 60.86% used.

```bash
qm config 230
```

Confirm that VMID 230 is not in use (that no configuration exists for it).

```bash
pvesm list local --content iso
```

```bash
free -h
```

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

```bash
qm create 230 --name ai-defense-manager --ostype l26 --memory 8192 --cores 4 --cpu host --machine q35 --scsihw virtio-scsi-single --scsi0 local-lvm:100,discard=on,iothread=1 --ide2 local:iso/ubuntu-24.04.5-live-server-amd64.iso,media=cdrom --boot 'order=scsi0;ide2' --net0 virtio,bridge=vmbr0 --agent enabled=1
```

A warning says that protection against the thin pool running out of space is disabled, but the VM is created.

```text
You have not turned on protection against thin pools running out of space.
```

```bash
qm config 230
```

```bash
qm start 230
```

```bash
qm status 230
```

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

```bash
ip -br addr
```

```bash
ip route
```

At build time, DHCP assigned `192.168.0.33/24`, and the default gateway was `192.168.0.1`.

## 7.2 Reachability of security-core and Ollama

**Run on: VM 230 ai-defense-manager (root)**

```bash
ping -c 3 192.168.0.220
```

```bash
ping -c 3 192.168.0.180
```

Connect to the API of the existing Ollama (GPU server, `192.168.0.180`) and get the list of available models.

```bash
curl -sS --max-time 5 http://192.168.0.180:11434/api/tags
```

# Chapter 8: OS Updates and Initial Checks

## 8.1 Updating Packages

**Run on: VM 230 ai-defense-manager (root)**

```bash
cat /etc/os-release
```

```bash
apt list --upgradable
```

First check what would change with a trial run (simulation) only.

```bash
apt-get -s upgrade
```

At build time there were 29 upgrades, 0 new installs and 0 removals, with 11 systemd-related packages held back (not included).

```bash
apt-get upgrade
```

```bash
if [ -f /var/run/reboot-required ]; then cat /var/run/reboot-required; else echo "REBOOT_NOT_REQUIRED"; fi
```

At build time it showed `REBOOT_NOT_REQUIRED`, so no reboot was needed.

## 8.2 SSH State

**Run on: VM 230 ai-defense-manager (root)**

```bash
systemctl status ssh --no-pager
```

```bash
sshd -T | grep -E '^(permitrootlogin|passwordauthentication|pubkeyauthentication|kbdinteractiveauthentication|permitemptyPasswords|allowtcpforwarding|maxauthtries)'
```

```bash
if [ -s /root/.ssh/authorized_keys ]; then echo "AUTHORIZED_KEYS_PRESENT"; wc -l < /root/.ssh/authorized_keys; else echo "NO_ROOT_AUTHORIZED_KEYS"; fi
```

```bash
who
```

```bash
if [ -s /home/aidefense/.ssh/authorized_keys ]; then echo "AUTHORIZED_KEYS_PRESENT"; wc -l < /home/aidefense/.ssh/authorized_keys; else echo "NO_USER_AUTHORIZED_KEYS"; fi
```

At build time, a Windows PC (`192.168.0.251`) was connected over SSH as `aidefense` with password authentication, and no public keys were registered for either root or `aidefense`. To keep the current connection, the SSH settings, such as switching to public-key authentication, were not changed.

## 8.3 Checking Resources

**Run on: VM 230 ai-defense-manager (root)**

```bash
df -h /
```

```bash
free -h
```

```bash
lscpu
```

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS
```

```bash
vgs
```

At build time the root allocation was 48 GB, and space remained in the volume group `ubuntu-vg` (about 98 GB) (this is the installer's default behavior). Memory was 7.8 GiB and the CPU was four AMD EPYC cores.

## 8.4 Network, Time and Host Name

**Run on: VM 230 ai-defense-manager (root)**

```bash
networkctl status enp6s18 --no-pager
```

```bash
netplan get
```

At build time the setting was simple DHCP (no change needed).

```bash
timedatectl status
```

```bash
hostnamectl
```

## 8.5 Reachability of the Wazuh API and the Ollama API

**Run on: VM 230 ai-defense-manager (root)**

```bash
nc -zv -w 3 192.168.0.220 55000
```

```bash
nc -zv -w 3 192.168.0.180 11434
```

If both show `succeeded`, they are reachable.

## 8.6 Python

**Run on: VM 230 ai-defense-manager (root)**

```bash
python3 --version
```

```bash
python3 -m pip --version
```

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

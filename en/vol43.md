---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 43: Backup Failures After a Reboot and the Recovery"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 43 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". By Part 42 we had set up three scheduled jobs (PostgreSQL logical backup at 02:00, LXC 109 backup at 03:00, TrueNAS ZFS snapshots from 04:00). Here we fix two separate problems found when checking the results of the first scheduled runs on the morning of November 23.

| Problem | What happened | Cause | Fix |
|---|---|---|---|
| 1 | After Proxmox rebooted at 06:50, NFS was not mounted | The NFS mount started before TrueNAS's VM 100 had booted and timed out after 90 seconds | Add a service that waits for TrueNAS to boot and NFS to respond before mounting |
| 2 | The 03:00 LXC 109 backup failed with `Permission denied` | The `tar` that reads an unprivileged LXC's files runs as UID 100000, but the temporary directory was created under the root-only NFS `dump/` | Set the temporary directory of job `lxc109-daily` to Proxmox's local `/var/tmp` |

The 02:00 PostgreSQL backup had succeeded.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)
- The TrueNAS API commands ask for TrueNAS's root password each time. Type it in the terminal and do not write it anywhere else.

# Chapter 1: Checking the Results of November 23

## 1.1 The Three Scheduled Jobs

At 08:58 on November 23, we read the logs, the saved files and the ZFS snapshots.

> **Run on: pve**

```bash
echo "===== CURRENT TIME ====="
date '+%Y-%m-%d %H:%M:%S %Z'

echo
echo "===== POSTGRESQL BACKUP RESULT ====="
systemctl show pg-logical-backup.service \
  -p Result -p ExecMainCode -p ExecMainStatus -p ExecMainStartTimestamp -p ExecMainExitTimestamp

journalctl -u pg-logical-backup.service \
  --since "2026-11-23 00:00:00" \
  --no-pager -o short-iso

echo
echo "===== POSTGRESQL BACKUP GENERATIONS ====="
find /mnt/pve/backup/postgresql \
  -mindepth 2 -maxdepth 2 -type d \
  -printf '%TY-%Tm-%Td %TH:%TM %p\n' 2>/dev/null | sort

echo
echo "===== TODAY'S POSTGRESQL CHECKSUM ====="
if [ -f /mnt/pve/backup/postgresql/daily/2026-11-23/SHA256SUMS ]; then
  cd /mnt/pve/backup/postgresql/daily/2026-11-23
  sha256sum -c SHA256SUMS
else
  echo "TODAY_BACKUP_NOT_FOUND"
fi

echo
echo "===== LXC 109 BACKUP ARCHIVES ====="
find /mnt/pve/backup/dump -maxdepth 1 -type f \
  -name 'vzdump-lxc-109-*' \
  -printf '%TY-%Tm-%Td %TH:%TM %s %p\n' | sort

echo
echo "===== PROXMOX LXC 109 TASK HISTORY ====="
pvenode task list --vmid 109 --limit 10

echo
echo "===== TODAY'S ZFS SNAPSHOTS ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 30 \
  --user root \
  https://192.168.0.254/api/v2.0/zfs/snapshot |
jq -r '.[] | select(.name | startswith("backup@") or startswith("backup/")) |
  ["NAME=\(.name)", "CREATED=\(.creation // "unknown")"] | join(" | ")'
```

The PostgreSQL logical backup finished dumping the 17 databases at 02:01 with `Result=success`. On the other hand, we found the following.

- The generation list under `/mnt/pve/backup/postgresql` is empty
- `/mnt/pve/backup/dump` does not exist
- The 03:00 LXC 109 backup is recorded as `ERR`

## 1.2 Is NFS Mounted?

> **Run on: pve**

```bash
echo "===== NFS MOUNT STATUS ====="
findmnt -T /mnt/pve/backup
mountpoint /mnt/pve/backup
systemctl status mnt-pve-backup.mount --no-pager -l

echo
echo "===== BACKUP PATH STATUS ====="
ls -ld /mnt/pve/backup
ls -la /mnt/pve/backup
df -hT /mnt/pve/backup

echo
echo "===== PROXMOX STORAGE STATUS ====="
pvesm status --storage truenas-backup

echo
echo "===== FAILED LXC 109 BACKUP TASK LOG ====="
pvenode task log 'UPID:pve:0010D698:00B3FB4F:6B032DA9:vzdump:109:root@pam:'

echo
echo "===== NFS MOUNT UNIT JOURNAL ====="
journalctl -u mnt-pve-backup.mount \
  --since "2026-11-23 01:30:00" \
  --no-pager -o short-iso
```

NFS was not mounted. `mnt-pve-backup.mount` started mounting at 06:50:27 and failed with a timeout at 06:51:57. What we see now is the empty local directory under the mount point. The backups on TrueNAS have not disappeared.

> **Caution:** While it is not mounted, do not create files in the local `/mnt/pve/backup`.

# Chapter 2: Why NFS Was Not Mounted

## 2.1 TrueNAS and the Logs

> **Run on: pve**

```bash
echo "===== NETWORK ROUTE TO TRUENAS ====="
ip route get 192.168.0.254

echo
echo "===== TRUENAS PING ====="
ping -c 3 -W 2 192.168.0.254

echo
echo "===== RPC SERVICES ====="
if command -v rpcinfo >/dev/null 2>&1; then
  timeout 10 rpcinfo -p 192.168.0.254
else
  echo "rpcinfo command not installed"
fi

echo
echo "===== NFS EXPORTS ====="
if command -v showmount >/dev/null 2>&1; then
  timeout 10 showmount -e 192.168.0.254
else
  echo "showmount command not installed"
fi

echo
echo "===== TRUENAS HTTPS API ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 15 \
  --user root \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/system/version
```

Ping to TrueNAS had 0% loss, RPC (NFSv3, mountd) responded, and `/mnt/backup` was exported. The TrueNAS API also returned `HTTP 200`. Neither TrueNAS as a whole nor its NFS service is down.

> **Run on: pve**

```bash
echo "===== NFS KERNEL LOG ====="
journalctl -k --since "2026-11-23 01:30:00" --no-pager \
  | grep -Ei 'nfs|rpc|mount|not responding|timed out|server' \
  | tail -n 150

echo
echo "===== NFS SYSTEMD MOUNT LOG ====="
journalctl -u mnt-pve-backup.mount \
  --since "2026-11-23 01:30:00" \
  --no-pager -o short-iso

echo
echo "===== NFS CLIENT MOUNT STATUS ====="
if command -v nfsstat >/dev/null 2>&1; then
  nfsstat -m
else
  echo "nfsstat command not installed"
fi

echo
echo "===== NFS CLIENT SERVER STATE ====="
for f in /proc/fs/nfsfs/servers /proc/fs/nfsfs/volumes; do
  if [ -r "$f" ]; then
    echo "--- $f ---"
    cat "$f"
  else
    echo "$f not available"
  fi
done
```

The kernel log showed that **the Proxmox host had rebooted at about 06:50:22 on November 23**.

## 2.2 The Network at Boot

> **Run on: pve**

```bash
echo "===== PVE UPTIME ====="
uptime
who -b

echo
echo "===== NETWORK INTERFACES ====="
ip -br address
ip route

echo
echo "===== NETWORK ONLINE TARGET ====="
systemctl status network-online.target --no-pager
systemctl show network-online.target -p ActiveState -p ActiveEnterTimestamp

echo
echo "===== NETWORK SERVICES ====="
systemctl status networking.service --no-pager
systemctl status systemd-networkd.service --no-pager

echo
echo "===== BOOT NETWORK JOURNAL ====="
journalctl -b --since "2026-11-23 06:49:30" --until "2026-11-23 06:53:30" --no-pager -o short-iso | grep -Ei 'network|vmbr|eno|link|carrier|dhcp|online|nfs|rpc|mount'

echo
echo "===== NFS MOUNT UNIT ====="
systemctl cat mnt-pve-backup.mount

echo
echo "===== RPC STATD STATUS ====="
systemctl status rpc-statd.service --no-pager
```

`networking.service` finished at 06:50:27, and `network-online.target` was reached at the same time. The link of the physical NIC `eno1` came up at 06:50:29, about two seconds after the mount started.

## 2.3 Host Load

> **Run on: pve**

```bash
echo "===== LOAD AND CPU ====="
uptime
nproc
vmstat 1 5

echo
echo "===== TOP CPU PROCESSES ====="
ps -eo pid,ppid,stat,pcpu,pmem,etime,comm,args --sort=-pcpu | head -25

echo
echo "===== PROCESSES IN UNINTERRUPTIBLE SLEEP ====="
ps -eo pid,ppid,stat,wchan:32,etime,comm,args | awk '$3 ~ /^D/ {print}' | head -40

echo
echo "===== SYSTEMD JOBS ====="
systemctl list-jobs --no-pager

echo
echo "===== DISK IO SUMMARY ====="
iostat -xz 1 3

echo
echo "===== RECENT KERNEL STORAGE ERRORS ====="
journalctl -k -b --since "2026-11-23 06:50:00" --no-pager | grep -Ei 'I/O error|reset|timeout|blocked for more|hung task|buffer I/O|nvme|ata.*error|ext4.*error' | tail -60
```

The load average was about 137, with 132–146 runnable processes (`r` in `vmstat`) for 64 logical CPUs. I/O wait was 0%; what stood out was VM 101 (`ollama-gpu`) and the multiple `llama-server` processes inside it. In the build records, the overloaded LXC was stopped here and the load average dropped to 39. We treat this as separate from the NFS problem.

## 2.4 When the TrueNAS VM Started

> **Run on: pve**

```bash
echo "===== VM100 STATUS AND CONFIG ====="
qm status 100
qm config 100 | grep -E '^(onboot|startup|boot|cores|sockets|memory):'

echo
echo "===== VM100 PROCESS START TIME ====="
ps -p 8278 -o pid,lstart,etime,stat,pcpu,comm

echo
echo "===== VM100 QEMU START JOURNAL ====="
journalctl -b --no-pager | grep -E '100 \(TrueNAS\)|vm-100|VM 100|qmstart|QEMU.*100' | head -60

echo
echo "===== NETWORK ONLINE SERVICES ====="
systemctl status networking.service network-online.target --no-pager -l
systemctl status ifupdown-wait-online.service --no-pager -l

echo
echo "===== NETWORK ONLINE UNIT CONFIGURATION ====="
systemctl cat networking.service
systemctl cat ifupdown-wait-online.service

echo
echo "===== NFS MOUNT UNIT CONFIGURATION ====="
systemctl cat mnt-pve-backup.mount
```

```bash
echo "===== PVE GUEST STARTUP SERVICE ====="
systemctl status pve-guests.service --no-pager -l
systemctl cat pve-guests.service

echo
echo "===== PVE GUEST STARTUP SERVICE DEPENDENCIES ====="
systemctl show pve-guests.service \
  -p After -p Before -p Wants -p Requires -p Type -p TimeoutStartUSec

echo
echo "===== VM100 STARTUP OPTIONS ====="
qm config 100 | grep -E '^(onboot|startup|boot|cores|sockets|memory):'

echo
echo "===== VM STARTUP TASK TIMELINE ====="
journalctl -b --no-pager | grep -E 'Starting VM 100|VM 100 started|start VM 100|starting task.*qmstart:100|Started pve-guests'

echo
echo "===== MOUNT UNIT DEPENDENCIES ====="
systemctl show mnt-pve-backup.mount \
  -p After -p Before -p Wants -p Requires -p TimeoutUSec -p JobTimeoutUSec

echo
echo "===== CURRENT NFS RPC READINESS ====="
timeout 5 rpcinfo -t 192.168.0.254 100005 3
timeout 5 rpcinfo -t 192.168.0.254 100003 3
```

| Time | Event |
|---|---|
| 06:50:27 | `network-online.target` reached; NFS mount started |
| 06:50:29 | `eno1` link up |
| 06:51:57 | NFS mount timed out after 90 seconds |
| 06:54:12 | TrueNAS VM 100 started |
| 07:21:17 | `pve-guests.service` finished starting all guests |

When the NFS mount started, **the destination TrueNAS VM had not started yet**. That is the direct reason for the timeout.

## 2.5 The Approach

We do not wait for `pve-guests.service` to finish. In this boot it took about 29 minutes to start all guests, which would delay the backup destination too much. Also, even after the VM start completes, it takes time until NFS inside TrueNAS is usable. So we do the following.

1. Before mounting, check whether TrueNAS's VM 100 is running
2. Wait until it starts
3. Repeat until TrueNAS's NFSv3 RPC (mountd and NFS) responds
4. Mount only when both respond
5. If it is not ready within the set time (900 seconds), let the mount fail. `is_mountpoint 1` still prevents accidental writes to the local directory

# Chapter 3: Mounting After Waiting for TrueNAS

## 3.1 Placing the Wait Script and Service

We place the following three files. No mount is performed and no VM is restarted.

| File | Role |
|---|---|
| `/usr/local/sbin/truenas-nfs-ready.sh` | wait for VM 100 to start and NFSv3 RPC to respond (up to 900 seconds, every 5 seconds) |
| `/etc/systemd/system/truenas-nfs-ready.service` | run the script above as a oneshot |
| `/etc/systemd/system/mnt-pve-backup.mount.d/10-truenas-readiness.conf` | order the mount after the service above (`Requires`, `After`) |

> **Run on: pve**

```bash
BACKUP_DIR="/root/nfs-config-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "===== BACKUP EXISTING CONFIGURATION ====="
for f in \
  /etc/systemd/system/mnt-pve-backup.mount \
  /etc/systemd/system/mnt-pve-backup.mount.d/10-truenas-readiness.conf \
  /etc/systemd/system/truenas-nfs-ready.service \
  /usr/local/sbin/truenas-nfs-ready.sh
do
  if [ -e "$f" ]; then
    cp -a --parents "$f" "$BACKUP_DIR/"
    echo "BACKED_UP: $f"
  else
    echo "NOT_EXISTED: $f"
  fi
done
echo "BACKUP_DIR=$BACKUP_DIR"

echo
echo "===== INSTALL READINESS SCRIPT ====="
cat > /usr/local/sbin/truenas-nfs-ready.sh <<'EOF'
#!/bin/bash

TRUENAS_IP="192.168.0.254"
VMID="100"
TIMEOUT_SECONDS=900
INTERVAL_SECONDS=5
DEADLINE=$(( $(date +%s) + TIMEOUT_SECONDS ))

echo "Waiting for TrueNAS VM ${VMID} and NFSv3 readiness."

while [ "$(date +%s)" -lt "$DEADLINE" ]; do
    VM_STATUS="$(qm status "$VMID" 2>/dev/null)"

    if [[ "$VM_STATUS" == *"status: running"* ]]; then
        echo "TrueNAS VM ${VMID} is running."

        if timeout 5 rpcinfo -t "$TRUENAS_IP" 100005 3 >/dev/null 2>&1 &&
           timeout 5 rpcinfo -t "$TRUENAS_IP" 100003 3 >/dev/null 2>&1; then
            echo "TrueNAS NFSv3 mountd and NFS RPC are ready."
            exit 0
        fi

        echo "NFSv3 RPC services are not ready yet."
    else
        echo "Waiting for TrueNAS VM ${VMID}: ${VM_STATUS:-status unavailable}"
    fi

    sleep "$INTERVAL_SECONDS"
done

echo "ERROR: TrueNAS/NFSv3 readiness timeout after ${TIMEOUT_SECONDS}s." >&2
exit 1
EOF
chmod 0755 /usr/local/sbin/truenas-nfs-ready.sh

echo
echo "===== INSTALL SYSTEMD READINESS SERVICE ====="
cat > /etc/systemd/system/truenas-nfs-ready.service <<'EOF'
[Unit]
Description=Wait for TrueNAS VM and NFSv3 readiness
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/truenas-nfs-ready.sh
TimeoutStartSec=16min
EOF

echo
echo "===== INSTALL NFS MOUNT DEPENDENCY ====="
mkdir -p /etc/systemd/system/mnt-pve-backup.mount.d
cat > /etc/systemd/system/mnt-pve-backup.mount.d/10-truenas-readiness.conf <<'EOF'
[Unit]
Requires=truenas-nfs-ready.service
After=truenas-nfs-ready.service
EOF

echo
echo "===== SCRIPT SYNTAX CHECK ====="
bash -n /usr/local/sbin/truenas-nfs-ready.sh
echo "BASH_SYNTAX_EXIT=$?"

echo
echo "===== RELOAD SYSTEMD ====="
systemctl daemon-reload
echo "DAEMON_RELOAD_EXIT=$?"

echo
echo "===== VERIFY SYSTEMD UNIT FILES ====="
systemd-analyze verify \
  /etc/systemd/system/truenas-nfs-ready.service \
  /etc/systemd/system/mnt-pve-backup.mount

echo
echo "===== VERIFY MOUNT DEPENDENCIES ====="
systemctl show mnt-pve-backup.mount -p Requires -p After -p Wants
systemctl show truenas-nfs-ready.service -p Type -p TimeoutStartUSec -p ExecStart

echo
echo "===== VERIFY INSTALLED FILES ====="
ls -l \
  /usr/local/sbin/truenas-nfs-ready.sh \
  /etc/systemd/system/truenas-nfs-ready.service \
  /etc/systemd/system/mnt-pve-backup.mount.d/10-truenas-readiness.conf
```

The syntax check and the dependency update worked, but `cp --parents` failed in the initial backup step, so we could not confirm that a copy of the original mount settings had been made (the original settings were not changed).

## 3.2 Saving the Original Settings and Testing the Script

Save the original mount settings reliably under another name and run the wait script without mounting.

> **Run on: pve**

```bash
BACKUP_DIR="/root/nfs-config-backup-20261123-091709"

echo "===== CREATE VERIFIED BACKUP OF ORIGINAL MOUNT UNIT ====="
install -D -m 0644 \
  /etc/systemd/system/mnt-pve-backup.mount \
  "$BACKUP_DIR/original-mnt-pve-backup.mount"

cmp -s \
  /etc/systemd/system/mnt-pve-backup.mount \
  "$BACKUP_DIR/original-mnt-pve-backup.mount"
echo "ORIGINAL_CONFIG_BACKUP_MATCH=$?"

echo
echo "===== VERIFY ORIGINAL MOUNT CONFIGURATION ====="
cat "$BACKUP_DIR/original-mnt-pve-backup.mount"

echo
echo "===== VERIFY READINESS SCRIPT CONTENT ====="
sed -n '1,200p' /usr/local/sbin/truenas-nfs-ready.sh

echo
echo "===== VERIFY SYSTEMD CONFIGURATION SYNTAX ====="
systemd-analyze verify \
  /etc/systemd/system/truenas-nfs-ready.service \
  /etc/systemd/system/mnt-pve-backup.mount
echo "SYSTEMD_VERIFY_EXIT=$?"

echo
echo "===== RUN READINESS CHECK ONLY (NO MOUNT) ====="
 /usr/local/sbin/truenas-nfs-ready.sh
echo "READINESS_CHECK_EXIT=$?"

echo
echo "===== VERIFY BACKUP FILE ====="
ls -l "$BACKUP_DIR/original-mnt-pve-backup.mount"
sha256sum \
  "$BACKUP_DIR/original-mnt-pve-backup.mount" \
  /etc/systemd/system/mnt-pve-backup.mount
```

| Checked | Result |
|---|---|
| Copy of the original mount settings | SHA256 matches |
| `systemd-analyze verify` | `0` |
| Wait script | `0` |
| TrueNAS VM 100 | running |
| NFSv3 mountd and NFS RPC | both respond |

## 3.3 Testing the Mount

Mount once through systemd and test writing, reading and deleting. The backup job is not run.

> **Run on: pve**

```bash
echo "===== PRE-MOUNT SAFETY CHECK ====="
findmnt -T /mnt/pve/backup
mountpoint -q /mnt/pve/backup
echo "ALREADY_MOUNTED=$?"

echo
echo "===== CHECK STORAGE ACTIVATION BEFORE MOUNT ====="
pvesm status --storage truenas-backup

echo
echo "===== START NFS MOUNT THROUGH SYSTEMD ====="
systemctl start mnt-pve-backup.mount
MOUNT_EXIT=$?
echo "MOUNT_START_EXIT=$MOUNT_EXIT"

echo
echo "===== VERIFY ACTUAL MOUNT SOURCE ====="
findmnt -T /mnt/pve/backup -o TARGET,SOURCE,FSTYPE,OPTIONS
mountpoint -q /mnt/pve/backup
echo "IS_MOUNTPOINT=$?"

echo
echo "===== VERIFY NFS STORAGE STATUS ====="
pvesm status --storage truenas-backup

echo
echo "===== VERIFY READ AND WRITE ACCESS ====="
if mountpoint -q /mnt/pve/backup; then
  TEST_FILE="/mnt/pve/backup/.pve-nfs-write-test-$(date +%s)"
  if printf 'PVE NFS write test\n' > "$TEST_FILE"; then
    echo "WRITE_TEST=PASS"
    cat "$TEST_FILE"
    rm -f "$TEST_FILE"
    echo "READ_DELETE_TEST=PASS"
  else
    echo "WRITE_TEST=FAIL"
  fi
else
  echo "NFS_NOT_MOUNTED: write test skipped"
fi

echo
echo "===== FINAL MOUNT UNIT STATUS ====="
systemctl status mnt-pve-backup.mount --no-pager -l
```

| Checked | Result |
|---|---|
| Mount through systemd | `0` |
| Connected to | `192.168.0.254:/mnt/backup` (NFSv3, TCP) |
| `truenas-backup` | `active` |
| Write, read, delete | all succeeded |
| Wait service | finished normally |

## 3.4 Effect on the November 23 Backups

> **Run on: pve**

```bash
echo "===== NFS MOUNT CONFIRMATION ====="
findmnt -T /mnt/pve/backup -o TARGET,SOURCE,FSTYPE,OPTIONS

echo
echo "===== POSTGRESQL BACKUP SCRIPT ====="
sed -n '1,260p' /usr/local/sbin/pg-logical-backup.sh

echo
echo "===== POSTGRESQL DAILY BACKUP DIRECTORIES ====="
find /mnt/pve/backup/postgresql/daily \
  -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>&1 | sort

echo
echo "===== NOVEMBER 23 POSTGRESQL BACKUP FILES ====="
if [ -d /mnt/pve/backup/postgresql/daily/2026-11-23 ]; then
  find /mnt/pve/backup/postgresql/daily/2026-11-23 \
    -maxdepth 2 -type f -printf '%P %s bytes\n' | sort
else
  echo "2026-11-23 DAILY DIRECTORY NOT FOUND"
fi

echo
echo "===== POSTGRESQL BACKUP MANIFESTS ====="
find /mnt/pve/backup/postgresql/daily/2026-11-23 \
  -maxdepth 2 -type f \( -iname '*sha256*' -o -iname '*manifest*' -o -iname '*metadata*' \) \
  -print 2>&1

echo
echo "===== LXC109 BACKUP ARCHIVES ====="
find /mnt/pve/backup/dump \
  -maxdepth 1 -type f -name 'vzdump-lxc-109-*' \
  -printf '%f %s bytes\n' 2>&1 | sort

echo
echo "===== LXC109 TEMPORARY FILES ====="
find /mnt/pve/backup/dump \
  -maxdepth 1 -name 'vzdump-lxc-109-*.tmp' \
  -printf '%f %s bytes\n' 2>&1

echo
echo "===== LATEST LXC109 BACKUP TASK LOG ====="
pvenode task log 'UPID:pve:0010D698:00B3FB4F:6B032DA9:vzdump:109:root@pam:' 2>&1 | tail -60

echo
echo "===== TRUE NAS BACKUP DATASET SNAPSHOTS ====="
zfs list -t snapshot -o name,creation \
  | grep '^backup@' | sort
```

```bash
BACKUP_DIR="/mnt/pve/backup/postgresql/daily/2026-11-23"

echo "===== VERIFY POSTGRESQL BACKUP CHECKSUMS ====="
cd "$BACKUP_DIR" && sha256sum -c SHA256SUMS
CHECKSUM_EXIT=$?
echo "CHECKSUM_EXIT=$CHECKSUM_EXIT"

echo
echo "===== COUNT DATABASE DUMP FILES ====="
find "$BACKUP_DIR" -maxdepth 1 -type f -name '*.dump' | wc -l

echo
echo "===== CHECK BACKUP FILES FOR ZERO SIZE ====="
find "$BACKUP_DIR" -maxdepth 1 -type f -size 0 -printf '%f\n'

echo
echo "===== POSTGRESQL BACKUP SERVICE RESULT ====="
journalctl -u pg-logical-backup.service \
  --since "2026-11-23 00:00:00" \
  --until "2026-11-23 23:59:59" \
  --no-pager -o short-iso | tail -100
```

- For PostgreSQL on November 23, the 17 dumps and `SHA256SUMS` exist, all checksums are `OK`, and there are no zero-byte files. It finished normally at 02:01:03
- The 03:00 LXC 109 backup had failed. The temporary snapshot is gone and no `.tmp` remains. The successful archive from November 22 is still there

Putting the times side by side, the LXC 109 failure was at 03:00 and the reboot at 06:50. **The 03:00 failure cannot be explained by the NFS mount failure.** We investigate it as a separate cause.

# Chapter 4: Why the LXC 109 Backup Failed

## 4.1 Differences from the Previous Success

> **Run on: pve**

```bash
echo "===== NFS MOUNT OPTIONS ====="
findmnt -T /mnt/pve/backup -o TARGET,SOURCE,FSTYPE,OPTIONS

echo
echo "===== BACKUP DIRECTORY PERMISSIONS ====="
namei -l /mnt/pve/backup/dump

echo
echo "===== BACKUP DIRECTORY METADATA ====="
stat -c '%A %a %U:%G uid=%u gid=%g %n' \
  /mnt/pve/backup \
  /mnt/pve/backup/dump

echo
echo "===== ACL OF BACKUP DIRECTORIES ====="
if command -v getfacl >/dev/null 2>&1; then
  getfacl -p /mnt/pve/backup /mnt/pve/backup/dump
else
  echo "getfacl command not installed"
fi

echo
echo "===== PREVIOUS SUCCESSFUL LXC109 BACKUP LOG ====="
cat /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.log

echo
echo "===== FAILED LXC109 BACKUP LOG ====="
cat /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_23-03_00_09.log

echo
echo "===== LXC109 CONFIGURATION (READ ONLY) ====="
pct config 109 | grep -E '^(unprivileged|rootfs|mp[0-9]+|features):'

echo
echo "===== NFS EXPORT VISIBILITY ====="
showmount -e 192.168.0.254
```

The log shows the backup's `tar` running in the following user namespace.

```text
lxc-usernsexec
u:0:100000:65536
g:0:100000:65536
```

LXC 109 is an unprivileged container (`unprivileged: 1`), so root inside the container is UID/GID `100000` on the host. Meanwhile, the NFS `dump/` had been set as follows in Part 42.

```text
drwx------ 700 root:root /mnt/pve/backup/dump
```

## 4.2 Can UID 100000 Write?

Without changing permissions, test whether a temporary file can be created as UID/GID `100000:100000`.

> **Run on: pve**

```bash
echo "===== UID/GID 100000 WRITE ACCESS TEST ====="
TEST_FILE="/mnt/pve/backup/dump/.uid100000-write-test-$(date +%s)"

setpriv --reuid=100000 --regid=100000 --clear-groups \
  -- sh -c 'umask 077; printf "UID 100000 NFS permission test\n" > "$1"' \
  sh "$TEST_FILE"
WRITE_EXIT=$?

echo "UID100000_WRITE_EXIT=$WRITE_EXIT"

if [ "$WRITE_EXIT" -eq 0 ]; then
  echo "===== TEST FILE OWNER ====="
  stat -c '%A %a %U:%G uid=%u gid=%g %n' "$TEST_FILE"

  echo
  echo "===== REMOVE TEST FILE ====="
  rm -f "$TEST_FILE"
  echo "TEST_FILE_REMOVED=$?"
else
  echo "UID 100000 cannot create a file in the dump directory."
fi

echo
echo "===== DUMP DIRECTORY TIMESTAMPS ====="
stat -c 'birth=%w modify=%y change=%z access=%x %n' \
  /mnt/pve/backup/dump

echo
echo "===== NFS4 ACL TOOL AVAILABILITY ====="
if command -v nfs4_getfacl >/dev/null 2>&1; then
  nfs4_getfacl /mnt/pve/backup/dump
else
  echo "nfs4_getfacl is not installed"
fi

echo
echo "===== VERIFY EXISTING BACKUP ARCHIVE REMAINS ====="
stat -c '%A %a %U:%G %s bytes %n' \
  /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_22-20_28_42.tar.zst
```

It gave `cannot create`, confirming that UID 100000 cannot enter `dump/`.

## 4.3 TrueNAS ACLs and the NFS Share

In TrueNAS CORE 12, ACLs are retrieved with a POST call. This is read-only; the ACLs are not changed.

> **Run on: pve**

```bash
echo "===== TRUENAS ACL: BACKUP DATASET ROOT (POST) ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 20 \
  --user root \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"path":"/mnt/backup"}' \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  'https://192.168.0.254/api/v2.0/filesystem/getacl'

echo
echo "===== TRUENAS ACL: DUMP DIRECTORY (POST) ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 20 \
  --user root \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"path":"/mnt/backup/dump"}' \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  'https://192.168.0.254/api/v2.0/filesystem/getacl'
```

Both `/mnt/backup` and `/mnt/backup/dump` are `acltype: NFS4` with owner `0:0`. `dump` gives no permission to traverse the directory (`EXECUTE`) to anyone other than owner@.

> **Run on: pve**

```bash
echo "===== FETCH TRUENAS NFS SHARES ====="
curl -k -sS \
  --connect-timeout 5 \
  --max-time 20 \
  --user root \
  -o /tmp/truenas-nfs-shares.json \
  -w 'HTTP_STATUS=%{http_code}\nCONTENT_TYPE=%{content_type}\n' \
  'https://192.168.0.254/api/v2.0/sharing/nfs'

echo
echo "===== PARSE NFS SHARE CONFIGURATION ====="
python3 - <<'PY'
import json
from pathlib import Path

p = Path("/tmp/truenas-nfs-shares.json")
try:
    data = json.loads(p.read_text())
    print("RESPONSE_TYPE:", type(data).__name__)
    if isinstance(data, list):
        print("SHARE_COUNT:", len(data))
        for item in data:
            if "/mnt/backup" in str(item.get("path", "")):
                print(json.dumps(item, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print("JSON_PARSE_ERROR:", e)
    print(p.read_text(errors="replace")[:4000])
PY

echo
echo "===== VERIFY NFS EXPORT ====="
showmount -e 192.168.0.254

echo
echo "===== CURRENT DUMP DIRECTORY PERMISSIONS ====="
stat -c '%A %a %U:%G uid=%u gid=%g %n' /mnt/pve/backup/dump
```

```bash
echo "===== RAW TRUENAS NFS SHARE JSON ====="
python3 -m json.tool /tmp/truenas-nfs-shares.json

echo
echo "===== TOP-LEVEL KEYS AND PATH VALUES ====="
python3 - <<'PY'
import json
with open("/tmp/truenas-nfs-shares.json") as f:
    data = json.load(f)

for i, item in enumerate(data):
    print(f"ITEM {i}:")
    print("TYPE:", type(item).__name__)
    if isinstance(item, dict):
        print("KEYS:", list(item.keys()))
        for key, value in item.items():
            if "path" in key.lower() or "map" in key.lower() or "security" in key.lower():
                print(f"{key} = {value!r}")
PY
```

The NFS share has `maproot_user = root` (only the client's UID 0 is mapped to root on the server), and `mapall_user` is empty. UID 100000 is not treated as root.

## 4.4 The Log of the Failure

> **Run on: pve**

```bash
echo "===== FAILED LXC109 BACKUP LOG ====="
grep -R -n -C 8 \
  '2026_11_23-03_00_09\|Cannot open: Permission denied\|vzdump-lxc-109' \
  /var/log/vzdump \
  /var/log/pve \
  2>/dev/null | tail -180

echo
echo "===== LXC ARCHIVE CALLER ====="
grep -n -C 10 -E '->archive\(|archive\(\$task|tmptar|target\}' \
  /usr/share/perl5/PVE/VZDump.pm \
  /usr/share/perl5/PVE/VZDump/LXC.pm 2>/dev/null | head -220

echo
echo "===== VZDUMP ARCHIVE PIPELINE ====="
grep -n -C 8 -E 'compress|tmptar|rename|target.*tmp|file.*target' \
  /usr/share/perl5/PVE/VZDump.pm | tail -220
```

The log showed that what failed was not the destination of the archive but the **temporary directory** that `tar` reads.

```text
--directory=/mnt/pve/backup/dump/vzdump-lxc-109-2026_11_23-03_00_09.tmp
...
tar: /mnt/pve/backup/dump/vzdump-lxc-109-2026_11_23-03_00_09.tmp: Cannot open: Permission denied
```

Proxmox runs the `tar` that reads an unprivileged LXC's files inside a namespace with UID/GID 100000. The temporary directory is created under the destination `dump/`, and because `dump/` is root-only `0700`, UID 100000 cannot reach it. The final archive (`.tar.dat`), by contrast, is the output of a pipe opened by root on the host, so it is not a problem.

Therefore there is no need to change TrueNAS ownership, ACLs or the NFS share. **It is enough to put just the temporary directory on a local disk.**

## 4.5 Can the Temporary Directory Be Set per Job?

> **Run on: pve**

```bash
echo "===== TMPDIR PARAMETER DEFINITION ====="
sed -n '225,265p' /usr/share/perl5/PVE/VZDump/Common.pm

echo
echo "===== VZDUMP JOB API SCHEMA ====="
grep -R -n -C 5 -E 'tmpdir|job.*param|prune-backups|schedule' \
  /usr/share/perl5/PVE/API2/VZDump.pm \
  /usr/share/perl5/PVE/Jobs \
  2>/dev/null | head -240

echo
echo "===== LOCAL TMP DIRECTORY ====="
stat -c '%A %a %U:%G %n' /var/tmp
findmnt -T /var/tmp
df -h /var/tmp
```

`/var/tmp` is on Proxmox's local ext4 with about 66GB free. The temporary directory mainly holds the LXC's configuration files, so it does not need space for the backup data itself.

> **Run on: pve**

```bash
echo "===== BACKUP JOB UPDATE API ====="
sed -n '344,475p' /usr/share/perl5/PVE/API2/Backup.pm

echo
echo "===== JOB CONFIG PROPERTY INHERITANCE ====="
grep -n -A 45 -B 8 'sub json_config_properties' \
  /usr/share/perl5/PVE/VZDump/Common.pm

echo
echo "===== STORAGE CONFIGURATION ====="
cat /etc/pve/storage.cfg

echo
echo "===== CURRENT JOB DETAILS ====="
pvesh get /cluster/backup/lxc109-daily --output-format json-pretty
```

We confirmed that the backup job update API (`update_job`) takes `tmpdir` from the common settings (`json_config_properties()`), so **`tmpdir` can be set per job**. We can change only `lxc109-daily` without making it a global setting in `/etc/vzdump.conf`.

# Chapter 5: Making the Job's Temporary Directory Local

## 5.1 What We Change

```text
Target job: lxc109-daily
Changed item: tmpdir
Value: /var/tmp
```

## 5.2 Setting It

Save `/etc/pve/jobs.cfg` before the change, set the value, and confirm it through both the API and the configuration file. No backup is run.

> **Run on: pve**

```bash
echo "===== BACKUP CURRENT JOB CONFIGURATION ====="
BACKUP_DIR="/root/lxc109-job-config-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

if cp -a /etc/pve/jobs.cfg "$BACKUP_DIR/jobs.cfg"; then
    sha256sum /etc/pve/jobs.cfg "$BACKUP_DIR/jobs.cfg"
    echo "CONFIG_BACKUP=$BACKUP_DIR/jobs.cfg"
else
    echo "ERROR: Configuration backup failed. No changes made."
fi

if [ -f "$BACKUP_DIR/jobs.cfg" ]; then
    echo
    echo "===== APPLY TMPDIR TO LXC109 JOB ONLY ====="
    pvesh set /cluster/backup/lxc109-daily --tmpdir /var/tmp
    UPDATE_EXIT=$?
    echo "UPDATE_EXIT=$UPDATE_EXIT"

    if [ "$UPDATE_EXIT" -eq 0 ]; then
        echo
        echo "===== VERIFY JOB THROUGH API ====="
        pvesh get /cluster/backup/lxc109-daily --output-format json-pretty

        echo
        echo "===== VERIFY PERSISTED JOB CONFIG ====="
        grep -A 16 '^vzdump: lxc109-daily' /etc/pve/jobs.cfg
    fi
fi
```

- `/etc/pve/jobs.cfg` before the change was saved (SHA256 matches)
- The API response contains `"tmpdir": "/var/tmp"`
- `tmpdir /var/tmp` was written to `/etc/pve/jobs.cfg`
- Schedule, compression, destination, generations and target CTID are unchanged

## 5.3 Can the Namespace Read `/var/tmp`?

> **Run on: pve**

```bash
echo "===== LOCAL TMPDIR NAMESPACE ACCESS TEST ====="
TEST_DIR="$(mktemp -d /var/tmp/lxc109-tmpdir-check.XXXXXX)"
TEST_FILE="$TEST_DIR/metadata-test"

if [ -d "$TEST_DIR" ]; then
    chmod 755 "$TEST_DIR"
    printf 'LXC109 temporary metadata access test\n' > "$TEST_FILE"
    chmod 644 "$TEST_FILE"

    echo "--- Host permissions ---"
    stat -c '%A %a %U:%G %n' "$TEST_DIR" "$TEST_FILE"

    echo
    echo "--- Read test from LXC unprivileged user namespace ---"
    lxc-usernsexec \
      -m u:0:100000:65536 \
      -m g:0:100000:65536 \
      -- sh -c 'test -r "$1" && cat "$1"' sh "$TEST_FILE"
    TEST_EXIT=$?
    echo "NAMESPACE_READ_EXIT=$TEST_EXIT"

    rm -f "$TEST_FILE"
    rmdir "$TEST_DIR"
    echo "TEST_CLEANUP=completed"
else
    echo "ERROR: Could not create local test directory."
fi

echo
echo "===== VERIFY JOB SETTINGS AGAIN ====="
pvesh get /cluster/backup/lxc109-daily --output-format json-pretty

echo
echo "===== VERIFY NO BACKUP WAS STARTED BY THIS CHECK ====="
pgrep -af 'vzdump.*109' || echo "No matching vzdump process found."
```

From the unprivileged LXC's namespace, a file in a temporary directory under `/var/tmp` could be read. The test file was removed and no backup ran.

The current backup configuration is as follows.

```text
Target: LXC 109 (PostgreSQL)
Mode: snapshot
Compression: zstd

Temporary directory:
  /var/tmp              ← PVE local

Final destination:
  /mnt/pve/backup/dump  ← TrueNAS NFS

Schedule:
  Daily 03:00

Generations:
  daily   7
  weekly  4
  monthly 3
```

> **Caution:** The configuration list above is for explanation and is not a command. Pasting it into a shell gives `command not found` (no settings or data are harmed).

## 5.4 Running the Backup Again

Run it once with the same destination and mode as the scheduled job, with `/var/tmp` as the temporary directory, and then check the compression integrity of the archive. Existing generations are not deleted.

> **Run on: pve**

```bash
echo "===== PRE-BACKUP SAFETY CHECK ====="

if ! mountpoint -q /mnt/pve/backup; then
    echo "ERROR: TrueNAS backup mount is not mounted. Backup skipped."
else
    findmnt -T /mnt/pve/backup
    pvesm status --storage truenas-backup

    if pgrep -x vzdump >/dev/null 2>&1; then
        echo "ERROR: Another vzdump process is running. Backup skipped."
    else
        echo
        echo "===== START LXC109 BACKUP ====="
        START_TIME="$(date '+%Y-%m-%d %H:%M:%S')"
        START_EPOCH="$(date +%s)"

        vzdump 109 \
          --storage truenas-backup \
          --mode snapshot \
          --compress zstd \
          --tmpdir /var/tmp

        BACKUP_EXIT=$?
        echo "BACKUP_EXIT=$BACKUP_EXIT"

        echo
        echo "===== NEW ARCHIVE CHECK ====="
        ARCHIVE="$(find /mnt/pve/backup/dump \
          -maxdepth 1 -type f \
          -name 'vzdump-lxc-109-*.tar.zst' \
          -newermt "@$START_EPOCH" \
          -printf '%T@ %p\n' 2>/dev/null |
          sort -nr | head -1 | cut -d' ' -f2-)"

        if [ -n "$ARCHIVE" ]; then
            echo "ARCHIVE=$ARCHIVE"
            ls -lh "$ARCHIVE"

            echo
            echo "===== ZSTD INTEGRITY TEST ====="
            zstd -t "$ARCHIVE"
            echo "ZSTD_TEST_EXIT=$?"
        else
            echo "No new LXC109 archive found."
        fi

        echo
        echo "===== BACKUP LOGS ====="
        find /var/log/vzdump -maxdepth 1 -type f \
          -newermt "@$START_EPOCH" -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' \
          2>/dev/null | sort
    fi
fi
```

| Item | Result |
|---|---|
| Run at | 2026-11-23 09:43:34 |
| Temporary directory | `/var/tmp` |
| Duration | 20 seconds |
| Exit code | `0` |
| Archive | `vzdump-lxc-109-2026_11_23-09_43_34.tar.zst` (about 473MiB) |
| zstd integrity | `ZSTD_TEST_EXIT=0` |

## 5.5 Checking the Contents and Cleanup

> **Run on: pve**

```bash
ARCHIVE="/mnt/pve/backup/dump/vzdump-lxc-109-2026_11_23-09_43_34.tar.zst"
LOG="/var/log/vzdump/lxc-109.log"

echo "===== VERIFY ARCHIVE CONTENTS ====="
tar --use-compress-program=unzstd -tf "$ARCHIVE" | sed -n '1,30p'
TAR_LIST_EXIT=${PIPESTATUS[0]}
echo "TAR_LIST_EXIT=$TAR_LIST_EXIT"

echo
echo "===== VERIFY BACKUP LOG ====="
grep -nE '09:43:34|09:43:54|tmpdir|archive file size|Finished Backup|successfully' "$LOG" | tail -60

echo
echo "===== VERIFY TEMPORARY ARTIFACTS ====="
find /mnt/pve/backup/dump -maxdepth 1 \
  \( -name 'vzdump-lxc-109-2026_11_23-09_43_34.tmp' \
     -o -name 'vzdump-lxc-109-2026_11_23-09_43_34.tar.dat' \) \
  -print

echo
echo "===== VERIFY FINAL ARCHIVE ====="
stat -c 'FILE=%n SIZE=%s bytes MODE=%a OWNER=%U:%G' "$ARCHIVE"
```

| Checked | Result |
|---|---|
| tar listing | `TAR_LIST_EXIT=0` |
| Log | finished normally |
| Temporary files | none left |
| Archive | `root:root`, 495,748,185 bytes |

We also confirmed that the archive contains `./etc/vzdump/pct.conf`, `./etc/vzdump/pct.fw`, Wazuh-related data under `./var/ossec/`, and the root file system of the PostgreSQL container.

# Closing Notes

In Part 43 we fixed the two backup problems found on November 23.

| Item | Result |
|---|---|
| PostgreSQL 02:00 backup | succeeded (17 databases, checksums `OK`) |
| NFS after a reboot | `truenas-nfs-ready.service` now waits for TrueNAS VM 100 to start and NFSv3 to respond before mounting. Mount test passed |
| LXC 109 03:00 backup | Cause: the UID 100000 `tar` cannot reach a temporary directory on NFS. Set `tmpdir: /var/tmp` on the job; re-run succeeded |
| TrueNAS ownership, ACLs, NFS share | unchanged |
| Other issues | the `windows_d/windows_d` VG error and the thin pool capacity warning (settings unchanged) |

In the next part, Part 44, we check that Proxmox recognizes the backups correctly and compare the restored databases with production in detail.

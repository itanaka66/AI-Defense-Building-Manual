---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 38: Using TrueNAS as the Backup Destination"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 38 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". In Part 37 we tested backing up and restoring LXC 109 (PostgreSQL), but the backups were stored (`local`) on the same NVMe as production. This part does the following.

1. Investigate, using reads only, LVM-thin (`pve/data`) capacity and its automatic extension settings
2. Make the NFS share `/mnt/backup` on **TrueNAS** (VM 100, 192.168.0.254) usable from Proxmox
3. Find out why it could not be written to (the NFS root mapping) and confirm that it can be written

TrueNAS receives one virtual disk of about 2TB each from Proxmox's `RAID_A` and `RAID_B` and mirrors them. It is empty, and we decided it could be used for backups. Without logging in to TrueNAS's screens or Shell, we check it from the Proxmox host (only the operation that changes TrueNAS's settings was done on the TrueNAS side).

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)

# Chapter 1: LVM-thin Capacity

## 1.1 The Thin Pool and Automatic Extension

> **Run on: pve**

```bash
echo "===== LVM THIN POOL ====="
lvs -a -o vg_name,lv_name,lv_attr,lv_size,data_percent,metadata_percent,seg_monitor

echo "===== PHYSICAL VOLUME ====="
pvs -o pv_name,vg_name,pv_size,pv_free

echo "===== THIN POOL AUTOEXTEND SETTINGS ====="
grep -nE 'thin_pool_autoextend_threshold|thin_pool_autoextend_percent|monitoring' /etc/lvm/lvm.conf
```

`pve/data`, where production LXC 109 lives, was 61.66% used for data and 2.18% for metadata, and VG `pve` had 16GiB free. `thin_pool_autoextend_threshold` and `thin_pool_autoextend_percent` in `lvm.conf` are still commented out.

```bash
echo "===== LVM MONITOR SERVICE ====="
systemctl is-active lvm2-monitor
systemctl status lvm2-monitor --no-pager -l

echo "===== DMEVENTD PROCESS ====="
pgrep -a dmeventd

echo "===== EFFECTIVE AUTOEXTEND SETTINGS ====="
lvmconfig --type current activation/thin_pool_autoextend_threshold
lvmconfig --type current activation/thin_pool_autoextend_percent
lvmconfig --type current activation/monitoring

echo "===== PVE DATA POOL ====="
lvs -o vg_name,lv_name,lv_size,data_percent,metadata_percent,seg_monitor pve/data
vgs -o vg_name,vg_size,vg_free pve
```

`lvm2-monitor` and `dmeventd` were running, and `pve/data` is monitored (`monitored`). However, no automatic extension values are set (`Configuration node … not found`). Being monitored and being extended automatically are different things.

## 1.2 Room to Grow

```bash
echo "===== PVE PHYSICAL DISK ====="
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL

echo "===== PVE PV DETAILS ====="
pvdisplay /dev/nvme0n1p3

echo "===== NVME PARTITION TABLE ====="
parted /dev/nvme0n1 unit GiB print free
```

The Proxmox disk is an NVMe (FIKWOT FN950 1TB), and partition 3 extends to the end of the disk. There is no free space left on the NVMe, and the VG has only 16GiB free. Enabling automatic extension would not solve a physical shortage of capacity, so **the automatic extension settings are left unchanged for now**.

```bash
echo "===== PVE DATA THIN POOL DETAILS ====="
lvs -o vg_name,lv_name,lv_size,data_percent,metadata_percent,chunksize,discards pve/data

echo "===== PVE STORAGE CONFIGURATION ====="
cat /etc/pve/storage.cfg

echo "===== PVE DATA POOL FREE SPACE ====="
vgs pve
```

`pve/data` is 794.30GiB, of which about 489.6GiB is used, leaving about 304.7GiB. It is not about to run out of space.

## 1.3 Where Backups Are Kept, and Jobs

```bash
echo "===== ROOT FILESYSTEM ====="
df -hT /

echo "===== BACKUP DIRECTORY ====="
df -hT /var/lib/vz
du -sh /var/lib/vz/dump

echo "===== PROXMOX STORAGE STATUS ====="
pvesm status
```

The root (`local`) used 24GiB of 94GiB, with 66GiB free, and `/var/lib/vz/dump` was 1.4GiB (three backups). `pvesm status` prints the following error and exits with code 5, but `local` and `local-lvm` are `active` (this error is treated as a separate problem).

```text
command '/sbin/vgscan --ignorelockingfailure --mknodes' failed: exit code 5
no such logical volume windows_d/windows_d
```

```bash
echo "===== VZDUMP CONFIGURATION ====="
cat /etc/vzdump.conf

echo "===== SCHEDULED BACKUP JOBS ====="
pvesh get /cluster/backup --output-format json-pretty
```

`/etc/vzdump.conf` was all comments, and scheduled backup jobs were `[]` (none).

# Chapter 2: Connecting to TrueNAS over NFS

## 2.1 The TrueNAS VM

```bash
echo "===== TRUENAS VM CONFIGURATION ====="
qm config 100
```

| Inside TrueNAS | On the Proxmox side | Size |
|---|---|---:|
| SCSI1 | `RAID_A` | 2,018G |
| SCSI2 | `RAID_B` | 2,018G |

> **Caution**: TrueNAS is a VM on the same Proxmox host. It protects against failure of the Proxmox NVMe, but not against failure of the whole host (it is not a backup to a separate machine).

## 2.2 Can We Reach It?

TrueNAS's IP address is 192.168.0.254.

```bash
echo "===== TRUENAS CONNECTIVITY ====="
ping -c 4 -W 2 192.168.0.254
```

All four replies came back (about 0.3–0.7 ms).

## 2.3 Choosing the Sharing Method

TrueNAS offers AFP, iSCSI, NFS, WebDAV and SMB shares; we use **NFS** as the destination for Proxmox backups.

| Method | Suitability |
|---|---|
| NFS | Suited to file sharing between Linux systems; usable directly as a Proxmox destination |
| SMB | Usable, but geared to sharing with Windows |
| iSCSI | Attaches a block device; complicated for file backups |
| WebDAV | Web-oriented; not suited as a Proxmox destination |
| AFP | Apple's old protocol; no reason to choose it for new builds |

```bash
showmount -e 192.168.0.254
```

```text
Export list for 192.168.0.254:
/mnt/backup (everyone)
```

`/mnt/backup` was shared. `(everyone)` is the scope of the share; it does not tell us whether we can write.

## 2.4 NFS Client and Server

```bash
echo "===== NFS CLIENT UTILITIES ====="
command -v mount.nfs
command -v nfsstat

echo "===== EXISTING NFS MOUNTS ====="
findmnt -t nfs,nfs4
```

`mount.nfs` and `nfsstat` were present, and there were no NFS mounts yet.

```bash
echo "===== NFS SERVER RPC SERVICES ====="
rpcinfo -p 192.168.0.254
```

TrueNAS answered with NFSv3 (TCP 2049, mountd on TCP 708). We use NFSv3.

## 2.5 Where to Mount

```bash
echo "===== TEMPORARY MOUNT POINT ====="
findmnt /mnt
ls -ld /mnt

echo "===== PROXMOX MOUNT DIRECTORY ====="
ls -ld /mnt/pve
```

```bash
echo "===== EXISTING PROXMOX MOUNTS ====="
findmnt -R /mnt/pve

echo "===== EXISTING MOUNT DIRECTORIES ====="
ls -la /mnt/pve
```

There were no mounts under `/mnt/pve`, and a directory `/mnt/pve/backup` already existed. Check its contents.

```bash
echo "===== EXISTING BACKUP MOUNTPOINT CONTENTS ====="
ls -la /mnt/pve/backup
du -sh /mnt/pve/backup
```

It was empty. We use it as the NFS mount point.

# Chapter 3: Mounting Read-Only

## 3.1 First Attempt

First mount read-only (`ro`) and check the contents.

```bash
mount -t nfs \
  -o ro,vers=3,proto=tcp \
  192.168.0.254:/mnt/backup \
  /mnt/pve/backup

echo "===== MOUNT RESULT ====="
findmnt /mnt/pve/backup

echo "===== EXPORTED BACKUP CONTENTS ====="
ls -lah /mnt/pve/backup
```

The mount failed with the following error.

```text
mount.nfs: Cannot allocate memory
```

## 3.2 Looking for the Cause

```bash
echo "===== NFS KERNEL MESSAGES ====="
dmesg -T | grep -iE 'nfs|rpc|memory|alloc' | tail -60

echo "===== MEMORY STATUS ====="
free -h

echo "===== NFS CLIENT STATUS ====="
nfsstat -c
```

About 96GiB of memory was free (about 119GiB available), and there were no NFS errors from the kernel. We also checked the NFS kernel modules (`nfs`, `nfsv3`, `sunrpc`, `lockd`), `rpc_pipefs` (mounted at `/run/rpc_pipefs`), the packages (`nfs-common` 2.6.2), slab memory, and memory pressure and OOM records; all were normal.

```bash
echo "===== ROUTE TO TRUENAS ====="
ip route get 192.168.0.254

echo "===== NFS TCP PORT ====="
nc -vz -w 3 192.168.0.254 2049

echo "===== MOUNTD TCP PORT ====="
nc -vz -w 3 192.168.0.254 708
```

Traffic to TrueNAS goes through `vmbr0` (source 192.168.0.240), and 2049 and 708 were both `open`. TrueNAS is running, so it is not restarted.

## 3.3 Trying Again

In the original build, approval was obtained before trying again. Trying with verbose output (`-v`) failed the same way with `mount(2): Cannot allocate memory`. So we try while recording system calls with `strace` (the record goes in `/tmp`).

```bash
strace -f -s 256 -o /tmp/nfs-mount-trace.log \
  mount -v -t nfs \
  -o ro,vers=3,proto=tcp,timeo=10,retrans=1 \
  192.168.0.254:/mnt/backup \
  /mnt/pve/backup

echo "===== MOUNT RESULT ====="
findmnt /mnt/pve/backup

echo "===== FAILED SYSTEM CALLS ====="
grep -E 'mount\(|ENOMEM|EFAULT|EINVAL|ENODEV|EPERM' /tmp/nfs-mount-trace.log | tail -40
```

This time **the mount succeeded**.

```text
mount("192.168.0.254:/mnt/backup", "/mnt/pve/backup",
      "nfs", MS_RDONLY, "...") = 0
```

```text
/mnt/pve/backup 192.168.0.254:/mnt/backup nfs ro,...
```

The `Cannot allocate memory` of the previous two attempts did not occur this time. Why it failed before is not known.

```bash
echo "===== NFS MOUNT STATUS ====="
findmnt -no SOURCE,FSTYPE,OPTIONS /mnt/pve/backup

echo "===== NFS DIRECTORY CONTENTS ====="
ls -lah /mnt/pve/backup

echo "===== NFS FILESYSTEM CAPACITY ====="
df -hT /mnt/pve/backup
```

It was mounted with NFSv3 over TCP; the size was 1.9T, 128K used, and it was empty.

# Chapter 4: Can We Write?

## 4.1 Remounting Read-Write

In the original build, approval was obtained before the temporary write test. Only the mount on the Proxmox side changes; TrueNAS's settings are not changed.

```bash
echo "===== REMOUNT NFS AS READ-WRITE ====="
mount -o remount,rw /mnt/pve/backup
echo "REMOUNT_EXIT=$?"

echo "===== CURRENT MOUNT OPTIONS ====="
findmnt -no SOURCE,FSTYPE,OPTIONS /mnt/pve/backup
```

`REMOUNT_EXIT=0`, and it became `rw`.

## 4.2 First Write Test

Create one test file, read it back, then delete it.

```bash
TEST_FILE="/mnt/pve/backup/.pve-nfs-write-test-20261122"

echo "===== NFS WRITE TEST ====="
if [ -e "$TEST_FILE" ]; then
  echo "TEST_ABORTED: test file already exists"
else
  printf 'Proxmox NFS write test\n' > "$TEST_FILE"
  echo "WRITE_EXIT=$?"

  echo "===== READ BACK TEST ====="
  printf 'Proxmox NFS write test\n' | cmp -s - "$TEST_FILE"
  echo "VERIFY_EXIT=$?"

  echo "===== DELETE TEST FILE ====="
  rm -f -- "$TEST_FILE"
  echo "DELETE_EXIT=$?"

  echo "===== FINAL CHECK ====="
  if [ ! -e "$TEST_FILE" ]; then
    echo "TEST_FILE_REMOVED"
  else
    echo "WARNING: TEST_FILE_REMAINS"
  fi
fi
```

`Permission denied` (`WRITE_EXIT=1`); we could not write (the file was not created).

## 4.3 Owner of the Shared Directory

```bash
echo "===== NFS SHARE DIRECTORY PERMISSIONS ====="
stat -c 'PATH=%n OWNER=%U GROUP=%G MODE=%a (%A) UID=%u GID=%g' /mnt/pve/backup

echo "===== NUMERIC OWNERSHIP ====="
ls -ldn /mnt/pve/backup

echo "===== NFS EXPORT ====="
showmount -e 192.168.0.254
```

The shared directory was `root:root` (UID 0, GID 0) and `755` (only the owner can write). Access from Proxmox's root is probably being mapped to a different user on the TrueNAS side (the NFS root mapping).

# Chapter 5: Reading TrueNAS's Settings from Proxmox

In the original build, approval was obtained to investigate and fix TrueNAS's NFS permissions. Without logging in to TrueNAS's screens or Shell, we read them through TrueNAS's API from the Proxmox host.

## 5.1 Management Entry Points

```bash
echo "===== TRUENAS MANAGEMENT PORT CHECK ====="
for port in 22 80 443; do
  nc -z -w 2 192.168.0.254 "$port"
  echo "PORT_${port}_EXIT=$?"
done

echo "===== TRUENAS API RESPONSE ====="
curl -k -sS --connect-timeout 3 -o /dev/null \
  -w 'HTTPS_API_HTTP_STATUS=%{http_code}\n' \
  https://192.168.0.254/api/v2.0/system/version
```

SSH (22) could not be reached; HTTP (80) and HTTPS (443) could. The API returned `401` (authentication required).

## 5.2 API Authentication

Enter the TrueNAS administrator's user name and password in the Proxmox terminal. The password is not displayed (`read -s`) and is never pasted into chats or elsewhere. The variables are cleared after use.

```bash
read -r -p "TrueNAS管理者ユーザー名: " TN_USER
read -r -s -p "TrueNAS管理者パスワード: " TN_PASS
echo

echo "===== TRUENAS API AUTHENTICATION ====="
HTTP_CODE=$(
  curl -k -sS --connect-timeout 5 \
    -u "$TN_USER:$TN_PASS" \
    -o /tmp/truenas-api-auth-check.json \
    -w '%{http_code}' \
    https://192.168.0.254/api/v2.0/system/version
)
echo "HTTP_STATUS=$HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
  echo "===== TRUENAS VERSION ====="
  jq . /tmp/truenas-api-auth-check.json
else
  echo "API authentication was not successful."
fi

rm -f /tmp/truenas-api-auth-check.json
unset TN_USER TN_PASS
```

`HTTP_STATUS=200`, and TrueNAS was `TrueNAS-12.0-U8.1` (TrueNAS CORE 12).

## 5.3 The API's Paths

Find the correct paths of the TrueNAS 12 API from its specification (`/api/v2.0`).

```bash
read -r -p "TrueNAS管理者ユーザー名: " TN_USER
read -r -s -p "TrueNAS管理者パスワード: " TN_PASS
echo

curl -k -sS --connect-timeout 10 \
  -u "$TN_USER:$TN_PASS" \
  -o /tmp/truenas-api-schema.json \
  -w 'HTTP_STATUS=%{http_code}\nCONTENT_TYPE=%{content_type}\n' \
  https://192.168.0.254/api/v2.0

echo "===== API SCHEMA STRUCTURE ====="
jq '{
  swagger,
  openapi,
  info,
  basePath,
  nfs_paths: ((.paths // {}) | keys | map(select(test("nfs|sharing|dataset"; "i"))))
}' /tmp/truenas-api-schema.json

rm -f /tmp/truenas-api-schema.json
unset TN_USER TN_PASS
```

An OpenAPI 3.0.0 specification was obtained; NFS shares are at `/sharing/nfs`, the NFS service at `/nfs`, and datasets at `/pool/dataset`.

## 5.4 NFS Settings, Shares and Datasets

```bash
read -r -p "TrueNAS管理者ユーザー名: " TN_USER
read -r -s -p "TrueNAS管理者パスワード: " TN_PASS
echo

echo "===== NFS SERVICE CONFIGURATION ====="
curl -k -sS --connect-timeout 10 \
  -u "$TN_USER:$TN_PASS" \
  https://192.168.0.254/api/v2.0/nfs | jq .

echo "===== NFS SHARE LIST ====="
curl -k -sS --connect-timeout 10 \
  -u "$TN_USER:$TN_PASS" \
  https://192.168.0.254/api/v2.0/sharing/nfs | jq .

echo "===== DATASET LIST ====="
curl -k -sS --connect-timeout 10 \
  -u "$TN_USER:$TN_PASS" \
  https://192.168.0.254/api/v2.0/pool/dataset \
  | jq '[.[] | {
      id,
      name,
      mountpoint,
      aclmode,
      acltype,
      readonly
    }]'

unset TN_USER TN_PASS
```

| Item | Value |
|---|---|
| NFS share (id 1) | `/mnt/backup` |
| `maproot_user` / `maproot_group` | `itanaka` / `itanaka` (UID/GID 1000) |
| Dataset | `backup` (NFSv4 ACL, `readonly=OFF`) |

**This is the cause.** Access from Proxmox's root is treated as `itanaka` on TrueNAS. The shared directory is `root:root`, `755`, so `itanaka` cannot write.

> **Note**: In the original build we also tried keeping the owner as `root:root` and adding a write ACL for `itanaka` (UID 1000). However, TrueNAS CORE 12 does not allow changing the ACL of the top-level dataset of a pool (`/mnt/backup`) (`root level dataset is not permitted`), and the ACL was not changed.

# Chapter 6: Allowing Writes as root

## 6.1 Changing the NFS Share Settings

On the TrueNAS side, we changed the root mapping (Maproot) of the NFS share `/mnt/backup`. The shared directory's owner remains `root:root`. Read the settings after the change from Proxmox through the API.

In this step, so that the password does not appear in `curl`'s command arguments, it is put in a temporary file with `chmod 600` and passed with `--config`; the file is deleted at the end.

> **Run on: pve**

```bash
read -r -p "TrueNAS管理者ユーザー名: " TN_USER
read -r -s -p "TrueNAS管理者パスワード: " TN_PASS
echo

AUTH_CFG=$(mktemp)
chmod 600 "$AUTH_CFG"
printf 'user = "%s:%s"\n' "$TN_USER" "$TN_PASS" > "$AUTH_CFG"
unset TN_PASS

echo "===== EXISTING NFS SHARE ====="
curl -k -sS --connect-timeout 10 \
  --config "$AUTH_CFG" \
  https://192.168.0.254/api/v2.0/sharing/nfs \
  | jq '[.[] | {
      id, paths, enabled, ro, alldirs,
      networks, hosts,
      maproot_user, maproot_group,
      mapall_user, mapall_group
    }]'

echo "===== PARENT DATASET PROPERTIES ====="
curl -k -sS --connect-timeout 10 \
  --config "$AUTH_CFG" \
  https://192.168.0.254/api/v2.0/pool/dataset/id/backup \
  | jq '{
      id, mountpoint, type, acltype, aclmode,
      compression, sync, readonly, casesensitivity
    }'

rm -f "$AUTH_CFG"
unset TN_USER AUTH_CFG
```

```text
"paths": ["/mnt/backup"],
"enabled": true,
"ro": false,
"alldirs": true,
"maproot_user": "root",
"maproot_group": "builtin_administrators",
```

Proxmox's root is now treated as `root` on TrueNAS too (group `builtin_administrators`).

## 6.2 Write Test

```bash
TEST_FILE="/mnt/pve/backup/.pve-root-write-test-20261122"

echo "===== NFS WRITE TEST ====="
if [ -e "$TEST_FILE" ]; then
  echo "TEST_ABORTED: test file already exists"
else
  printf 'Proxmox root NFS write test\n' > "$TEST_FILE"
  WRITE_RC=$?
  echo "WRITE_EXIT=$WRITE_RC"

  if [ "$WRITE_RC" -eq 0 ]; then
    echo "===== READ BACK TEST ====="
    cat "$TEST_FILE"

    echo "===== FILE OWNERSHIP ====="
    stat -c 'owner=%U:%G uid=%u gid=%g mode=%a' "$TEST_FILE"

    echo "===== CLEANUP ====="
    rm -f "$TEST_FILE"
    echo "REMOVE_EXIT=$?"
    if [ ! -e "$TEST_FILE" ]; then
      echo "CLEANUP_VERIFIED"
    else
      echo "CLEANUP_FAILED"
    fi
  fi
fi
```

```text
===== NFS WRITE TEST =====
WRITE_EXIT=0
===== READ BACK TEST =====
Proxmox root NFS write test
===== FILE OWNERSHIP =====
owner=root:root uid=0 gid=0 mode=644
===== CLEANUP =====
REMOVE_EXIT=0
CLEANUP_VERIFIED
```

**Proxmox's root could write to TrueNAS's `/mnt/backup`.** There is no need to create a child dataset or change ACLs.

# Closing Notes

In Part 38 we prepared TrueNAS as the backup destination.

| Item | Result |
|---|---|
| LVM-thin | `pve/data` 61.66%. Automatic extension not set, but deferred because the VG has only 16GiB free |
| Scheduled backups | None (`vzdump.conf` also at defaults) |
| Destination | TrueNAS (VM 100, 192.168.0.254) NFS `/mnt/backup` (1.9T, empty) |
| Mount | NFSv3 over TCP at `/mnt/pve/backup`. The first two attempts gave `Cannot allocate memory` (cause unknown); the third succeeded |
| Why writes failed | The NFS root mapping was `itanaka`, and the shared directory was `root:root`, `755` |
| What was changed | The NFS share's Maproot on TrueNAS set to `root` / `builtin_administrators` |
| Write test | Succeeded (created as `root:root` and deleted) |

However, the current mount was made by hand and is not yet registered as Proxmox storage. In Part 39 we make sure NFS is mounted correctly at boot, register it with Proxmox as backup-only storage, and prepare scheduled backups.

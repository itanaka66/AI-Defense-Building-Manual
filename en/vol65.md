---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 65: Checking FSS from Another Host (VM 240)"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 65 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 64 we started FSS sealing of VM 230's journal and checked it inside VM 230. So that the result can be trusted even if VM 230 is compromised, we check it **on a host other than VM 230**.

1. Bundle the sealed journal (switch it into an archive) and move it to the Proxmox host `pve`
2. systemd 252 on `pve` cannot verify this form of journal, so create VM 240 (Ubuntu 24.04, systemd 255) dedicated to verification
3. Move the journal and verification key from `pve` to VM 240 and check them cryptographically on VM 240
4. Confirm that the files have not changed in all three places: VM 230 (where it was made), `pve` (where it is stored) and VM 240 (where it was checked)

The contents of the verification key are not displayed.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **pve**: the Proxmox host (root)
  - **VM 240**: fss-verification (`192.168.0.222`, root. When logged in as an ordinary user, become root with `sudo -i`)

# Chapter 1: Moving the Sealed Journal to `pve`

## 1.1 Creating an Archive for Verification

Copying the active journal as is may let logs be added while it is being copied. We switch the journal to create a sealed archive. No log deletion, service restarts or key changes.

> **Run on: VM 230**

```bash
echo "===== VM230: APPROVED FSS VERIFICATION SNAPSHOT ROTATION ====="

JDIR="/var/log/journal/b21f0e30faf4447bbe59cc1be7a0b169"

echo
echo "--- 1. Rotate journal ---"
journalctl --rotate
ROTATE_STATUS=$?
echo "ROTATE_EXIT_STATUS=$ROTATE_STATUS"

if [ "$ROTATE_STATUS" -ne 0 ]; then
    echo "ROTATION_FAILED=YES"
    exit "$ROTATE_STATUS"
fi

echo
echo "--- 2. Identify newest archived system journal ---"
ARCHIVE="$(find "$JDIR" -maxdepth 1 -type f \
  -name 'system@*.journal' -printf '%T@ %p\n' |
  sort -nr | head -n 1 | cut -d' ' -f2-)"

if [ -z "$ARCHIVE" ]; then
    echo "ARCHIVE_NOT_FOUND=YES"
    exit 1
fi

echo "ARCHIVE_PATH=$ARCHIVE"

echo
echo "--- 3. Verify archive FSS header ---"
journalctl --header --file="$ARCHIVE" |
  grep -E '^(State|Compatible flags|Incompatible flags|Tag objects):'

echo
echo "--- 4. Archive metadata ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s MTIME=%y' "$ARCHIVE"

echo
echo "FSS_KEY_CONTENT_DISPLAYED=NO"
echo "JOURNAL_DELETION=NO"
echo "SERVICE_RESTARTED=NO"
```

The archive was `ARCHIVED`, `SEALED SEALED_CONTINUOUS`, `Tag objects` 9, 8,388,608 bytes.

## 1.2 Moving It to `pve`

> **Run on: VM 230**

```bash
echo "===== VM230: TRANSFER FSS ARCHIVE TO PVE ====="

ARCHIVE="/var/log/journal/b21f0e30faf4447bbe59cc1be7a0b169/system@a5afdaa8e8854b2dadf2e328b59278c6-0000000000005850-000660fbd4d4fbe3.journal"
DEST="/root/fss-independent-system-20261124.journal"
SSH_KEY="/root/.ssh/id_ed25519_pve_fss"
KNOWN_HOSTS="/root/.ssh/known_hosts"

echo
echo "--- 1. Source archive preflight ---"
test -f "$ARCHIVE" || { echo "SOURCE_ARCHIVE_MISSING"; exit 1; }
stat -c 'SIZE=%s OWNER=%U:%G MODE=%a' "$ARCHIVE"

echo
echo "--- 2. Transfer archive to PVE ---"
scp -p \
  -i "$SSH_KEY" \
  -o BatchMode=yes \
  -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" \
  "$ARCHIVE" \
  "root@192.168.0.240:$DEST"
SCP_STATUS=$?
echo "SCP_EXIT_STATUS=$SCP_STATUS"

if [ "$SCP_STATUS" -ne 0 ]; then
    echo "TRANSFER_FAILED=YES"
    exit "$SCP_STATUS"
fi

echo
echo "--- 3. Compare source and destination SHA-256 ---"
LOCAL_HASH="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
REMOTE_HASH="$(ssh \
  -i "$SSH_KEY" \
  -o BatchMode=yes \
  -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" \
  root@192.168.0.240 \
  "sha256sum '$DEST' | awk '{print \$1}'")"
SSH_STATUS=$?

echo "LOCAL_SHA256=$LOCAL_HASH"
echo "REMOTE_SHA256=$REMOTE_HASH"
echo "REMOTE_CHECK_EXIT_STATUS=$SSH_STATUS"

if [ "$SSH_STATUS" -eq 0 ] && [ "$LOCAL_HASH" = "$REMOTE_HASH" ]; then
    echo "TRANSFER_INTEGRITY=PASS"
else
    echo "TRANSFER_INTEGRITY=FAIL"
fi

echo
echo "FSS_KEY_CONTENT_DISPLAYED=NO"
echo "SOURCE_JOURNAL_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

The transfer succeeded, and the SHA-256 matched on VM 230 and `pve`.

## 1.3 `pve` Cannot Verify It

`pve`'s systemd is 252.39; it showed the header of this archive as `SEALED ???`, and verification stopped as follows.

```text
Cannot verify file with unknown extensions.
File corruption detected ... :000000
FAIL ... (Operation not supported)
```

With systemd 255.4 on VM 230, verification of the same archive succeeds as follows.

```text
PASS: ...system@a5afdaa8e8854b2dadf2e328b59278c6-0000000000005850-000660fbd4d4fbe3.journal
=> Validated from Tue 2026-11-24 01:43:04 UTC to Tue 2026-11-24 02:00:00 UTC, final 0 entries not sealed.
VM230_ARCHIVE_VERIFY_EXIT_STATUS=0
```

The journal key is not wrong and the file is not broken; it is a difference in systemd versions, and 252 cannot read the new format. So we create a VM dedicated to verification with systemd 255.

# Chapter 2: Creating VM 240 for Verification

## 2.1 Resources and the ISO

No settings are changed; read-only.

> **Run on: pve**

```bash
echo "===== PVE: READ-ONLY RESOURCE AND VM INVENTORY ====="

echo
echo "--- 1. Host identity and system version ---"
hostname
pveversion
uname -r

echo
echo "--- 2. Host CPU and memory ---"
nproc
free -h
uptime

echo
echo "--- 3. Existing virtual machines ---"
qm list

echo
echo "--- 4. VM resource configuration (read-only) ---"
for VMID in $(qm list | awk 'NR > 1 {print $1}'); do
    echo
    echo "### VM $VMID"
    qm config "$VMID" |
      grep -E '^(name|memory|cores|sockets|cpu|numa|ostype|bios|machine|scsi[0-9]+|virtio[0-9]+|sata[0-9]+|ide[0-9]+|boot):'
done

echo
echo "--- 5. Proxmox storage status ---"
pvesm status

echo
echo "--- 6. LVM logical volumes ---"
lvs --units g -o lv_name,vg_name,lv_size,lv_attr,data_percent,metadata_percent

echo
echo "--- 7. Filesystem capacity ---"
df -hT

echo
echo "--- 8. Storage mount points ---"
findmnt -o TARGET,SOURCE,FSTYPE,OPTIONS / /var/lib/vz

echo
echo "READ_ONLY_INVENTORY=COMPLETED"
echo "VM_CONFIGURATION_MODIFIED=NO"
echo "STORAGE_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
```

```bash
echo "===== PVE: READ-ONLY VERIFICATION VM PREREQUISITES ====="

echo
echo "--- 1. Available ISO images in local storage ---"
pvesm list local --content iso

echo
echo "--- 2. Available ISO images in ubuntu storage ---"
pvesm list ubuntu --content iso

echo
echo "--- 3. ISO files in local ISO directory ---"
if [ -d /var/lib/vz/template/iso ]; then
    ls -lh /var/lib/vz/template/iso/
else
    echo "LOCAL_ISO_DIRECTORY_NOT_FOUND"
fi

echo
echo "--- 4. Registered QEMU VM configuration IDs ---"
find /etc/pve/qemu-server -maxdepth 1 -type f \
  -name '*.conf' -printf '%f\n' | sort -V

echo
echo "--- 5. Proxmox suggested next VMID ---"
pvesh get /cluster/nextid

echo
echo "--- 6. Network bridge status (read-only) ---"
ip -brief address show vmbr0
ip -brief link show vmbr0

echo
echo "VM_CONFIGURATION_MODIFIED=NO"
echo "STORAGE_MODIFIED=NO"
echo "NETWORK_MODIFIED=NO"
```

There are 64 CPU threads, about 101GiB of free memory, about 317GiB free on `local-lvm`, and an Ubuntu Server 24.04.5 ISO. To match VM 230's Ubuntu generation and systemd 255, we use Ubuntu 24.04.5.

## 2.2 Is VMID 240 Free?

> **Run on: pve**

```bash
echo "===== PVE: VMID 240 COLLISION PREFLIGHT ====="

echo
echo "--- 1. QEMU VMID 240 ---"
if [ -f /etc/pve/qemu-server/240.conf ]; then
    echo "QEMU_VMID_240=IN_USE"
    qm config 240
else
    echo "QEMU_VMID_240=NOT_REGISTERED"
fi

echo
echo "--- 2. LXC CTID 240 ---"
if [ -f /etc/pve/lxc/240.conf ]; then
    echo "LXC_CTID_240=IN_USE"
    pct config 240
else
    echo "LXC_CTID_240=NOT_REGISTERED"
fi

echo
echo "--- 3. Existing VM and container list matches ---"
qm list | awk '$1 == 240'
pct list | awk '$1 == 240'

echo
echo "--- 4. Required storage status ---"
pvesm status --storage local-lvm
pvesm status --storage local

echo
echo "VMID_240_PREFLIGHT=COMPLETED"
echo "VM_CREATED=NO"
echo "STORAGE_MODIFIED=NO"
```

VMID 240 was not used by any VM or LXC.

## 2.3 Creating VM 240

| Item | Setting |
|---|---|
| VMID, name | 240, `fss-verification` |
| OS | Ubuntu Server 24.04.5 |
| CPU, memory | 2 vCPUs, 4GiB |
| Disk | 32GiB (`local-lvm`) |
| Network | `vmbr0` |

> **Run on: pve**

```bash
echo "===== PVE: CREATE FSS VERIFICATION VM 240 ====="

echo
echo "--- 1. Create VM 240 ---"
qm create 240 \
  --name fss-verification \
  --ostype l26 \
  --machine q35 \
  --cpu host \
  --cores 2 \
  --memory 4096 \
  --scsihw virtio-scsi-single \
  --scsi0 local-lvm:32,discard=on,iothread=1 \
  --ide2 local:iso/ubuntu-24.04.5-live-server-amd64.iso,media=cdrom \
  --boot 'order=scsi0;ide2' \
  --net0 virtio,bridge=vmbr0

CREATE_STATUS=$?
echo "VM_CREATE_EXIT_STATUS=$CREATE_STATUS"

if [ "$CREATE_STATUS" -ne 0 ]; then
    echo "VM_CREATE=FAILED"
    exit "$CREATE_STATUS"
fi

echo
echo "--- 2. Verify VM configuration ---"
qm config 240

echo
echo "--- 3. Verify VM registration ---"
qm list | awk 'NR == 1 || $1 == 240'

echo
echo "--- 4. Verify VM state ---"
qm status 240

echo
echo "VM_240_CREATE=COMPLETED"
echo "OS_INSTALLED=NO"
echo "VM_STARTED=NO"
echo "EXISTING_VMS_MODIFIED=NO"
```

The following warning appears at creation (no protection by thin pool autoextend, and total allocation exceeds actual capacity; the same state investigated in Part 41).

```text
You have not turned on protection against thin pools running out of space.
Sum of all thin volume sizes ... exceeds the size of thin pool ...
```

## 2.4 Starting It and Installing the OS

> **Run on: pve**

```bash
echo "===== PVE: START VM 240 UBUNTU INSTALLER ====="

echo
echo "--- 1. Confirm VM configuration ---"
qm config 240

echo
echo "--- 2. Start VM 240 ---"
qm start 240
START_STATUS=$?
echo "VM_START_EXIT_STATUS=$START_STATUS"

if [ "$START_STATUS" -ne 0 ]; then
    echo "VM_START=FAILED"
    exit "$START_STATUS"
fi

echo
echo "--- 3. Wait for VM state ---"
sleep 5
qm status 240

echo
echo "--- 4. Verify QEMU process ---"
qm list | awk 'NR == 1 || $1 == 240'

echo
echo "VM_240_STARTED=YES"
echo "OS_INSTALLATION=NOT_STARTED"
echo "EXISTING_VMS_MODIFIED=NO"
```

Install Ubuntu from **VM 240 → Console** in the Proxmox web interface. In the build records, it was installed with IP address `192.168.0.222`, with OpenSSH server installed and configured to accept connections.

## 2.5 Checking After Installation

> **Run on: VM 240**

```bash
echo "===== VM240: UBUNTU INSTALLATION VERIFICATION ====="

echo
echo "--- 1. Host identity ---"
hostname
id

echo
echo "--- 2. OS version ---"
cat /etc/os-release

echo
echo "--- 3. systemd and journalctl versions ---"
systemd --version | head -n 3
journalctl --version

echo
echo "--- 4. Network configuration ---"
ip -brief address
ip route

echo
echo "--- 5. SSH service status ---"
systemctl is-active ssh
systemctl is-enabled ssh

echo
echo "--- 6. Disk and filesystem ---"
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS
df -h /

echo
echo "--- 7. journal verification option ---"
journalctl --help | grep -E -- '--verify|--verify-key'

echo
echo "INSTALLATION_VERIFICATION=COMPLETED"
echo "CONFIGURATION_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
```

| Item | VM 230 | VM 240 |
|---|---|---|
| Ubuntu | 24.04 | 24.04.5 LTS |
| systemd | 255.4 | 255.4 |
| FSS verification option | supported | supported |
| IP address | `192.168.0.221` | `192.168.0.222` |

## 2.6 Checking SSH

> **Run on: VM 240**

```bash
echo "===== VM240: SSH TRANSFER READINESS CHECK ====="

echo
echo "--- 1. SSH service status ---"
systemctl status ssh --no-pager -l
echo
systemctl is-active ssh
systemctl is-enabled ssh

echo
echo "--- 2. SSH listening sockets ---"
ss -lntp | grep -E '(:22[[:space:]]|:22$)' || true

echo
echo "--- 3. SSH host key fingerprints ---"
for KEY in /etc/ssh/ssh_host_*_key.pub; do
    [ -f "$KEY" ] && ssh-keygen -lf "$KEY"
done

echo
echo "--- 4. Transfer destination directory ---"
if [ -d /root ]; then
    stat -c 'PATH=%n OWNER=%U:%G MODE=%a' /root
fi

echo
echo "--- 5. Existing target files ---"
for FILE in \
  /root/fss-independent-system-20261124.journal \
  /root/fss-verification-key-20261124.txt; do
    if [ -e "$FILE" ]; then
        stat -c 'EXISTS PATH=%n OWNER=%U:%G MODE=%a SIZE=%s' "$FILE"
    else
        echo "NOT_PRESENT: $FILE"
    fi
done

echo
echo "SSH_CONFIGURATION_MODIFIED=NO"
echo "FILES_MODIFIED=NO"
echo "SECRETS_DISPLAYED=NO"
```

SSH is `active (running)` and listening on TCP 22, root's home is `root:root`, `700`, and there are no received files yet. We note the fingerprint of the ED25519 host key.

# Chapter 3: Moving to VM 240 and Checking

## 3.1 Checks on the `pve` Side

> **Run on: pve**

```bash
echo "===== PVE: VM240 TRANSFER SOURCE AND HOST IDENTITY PREFLIGHT ====="

JOURNAL="/root/fss-independent-system-20261124.journal"
KEY="/root/fss-verification-key-20261124.txt"

echo
echo "--- 1. Verify source files ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s PATH=%n' "$JOURNAL" "$KEY"

echo
echo "--- 2. Verify source journal hash ---"
sha256sum "$JOURNAL"

echo
echo "--- 3. Verify source key hash (hash only; never display key) ---"
sha256sum "$KEY"

echo
echo "--- 4. Retrieve VM240 ED25519 host key ---"
SCAN="$(ssh-keyscan -t ed25519 192.168.0.222 2>/dev/null)"
if [ -z "$SCAN" ]; then
    echo "HOST_KEY_SCAN=FAILED"
    exit 1
fi

printf '%s\n' "$SCAN" | ssh-keygen -lf -
ACTUAL="$(printf '%s\n' "$SCAN" | ssh-keygen -lf - | awk '{print $2}')"
EXPECTED="SHA256:EgIQy0eg6otMhyALG3QvpE5YbGslDJllQZSwi/KWxHw"

if [ "$ACTUAL" = "$EXPECTED" ]; then
    echo "VM240_HOST_KEY_MATCH=PASS"
else
    echo "VM240_HOST_KEY_MATCH=FAIL"
    exit 1
fi

echo
echo "SOURCE_FILES_MODIFIED=NO"
echo "REMOTE_FILES_MODIFIED=NO"
echo "KEY_CONTENT_DISPLAYED=NO"
```

The two source files (journal and verification key) are present, and the journal's SHA-256 is the same as at the previous transfer. VM 240's host key also matched the noted fingerprint.

## 3.2 Moving

Using the verified host key, we move them to `/home/ag/` of user `ag` on VM 240. When asked for a password, enter the password of `ag` on VM 240 (do not write it in chats or notes).

> **Run on: pve**

```bash
echo "===== PVE: TRANSFER FSS VERIFICATION MATERIAL TO VM240 ====="

JOURNAL="/root/fss-independent-system-20261124.journal"
KEY="/root/fss-verification-key-20261124.txt"
KNOWN="/root/.ssh/known_hosts_vm240_fss_20261124"
EXPECTED="SHA256:EgIQy0eg6otMhyALG3QvpE5YbGslDJllQZSwi/KWxHw"

echo
echo "--- 1. Pin verified VM240 host key ---"
SCAN="$(ssh-keyscan -t ed25519 192.168.0.222 2>/dev/null)"
ACTUAL="$(printf '%s\n' "$SCAN" | ssh-keygen -lf - | awk '{print $2}')"

if [ "$ACTUAL" != "$EXPECTED" ]; then
    echo "HOST_KEY_MATCH=FAIL"
    exit 1
fi

printf '%s\n' "$SCAN" > "$KNOWN"
chmod 600 "$KNOWN"
echo "HOST_KEY_MATCH=PASS"

echo
echo "--- 2. Transfer journal archive ---"
scp -o UserKnownHostsFile="$KNOWN" \
    -o StrictHostKeyChecking=yes \
    "$JOURNAL" ag@192.168.0.222:/home/ag/
JOURNAL_STATUS=$?
echo "JOURNAL_TRANSFER_STATUS=$JOURNAL_STATUS"

if [ "$JOURNAL_STATUS" -ne 0 ]; then
    echo "TRANSFER=FAILED"
    exit "$JOURNAL_STATUS"
fi

echo
echo "--- 3. Transfer FSS verification key ---"
scp -o UserKnownHostsFile="$KNOWN" \
    -o StrictHostKeyChecking=yes \
    "$KEY" ag@192.168.0.222:/home/ag/
KEY_STATUS=$?
echo "KEY_TRANSFER_STATUS=$KEY_STATUS"

if [ "$KEY_STATUS" -ne 0 ]; then
    echo "TRANSFER=PARTIAL"
    exit "$KEY_STATUS"
fi

echo
echo "TRANSFER=COMPLETED"
echo "KEY_CONTENT_DISPLAYED=NO"
echo "SOURCE_FILES_MODIFIED=NO"
```

Both files were moved with exit code `0`.

## 3.3 Confirming the Match on VM 240

> **Run on: VM 240**

```bash
echo "===== VM240: VERIFY TRANSFERRED FSS MATERIAL ====="

JOURNAL="/home/ag/fss-independent-system-20261124.journal"
KEY="/home/ag/fss-verification-key-20261124.txt"

echo
echo "--- 1. Verify transferred files ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s PATH=%n' "$JOURNAL" "$KEY" || exit 1

echo
echo "--- 2. Verify journal SHA256 ---"
JOURNAL_HASH="$(sha256sum "$JOURNAL" | awk '{print $1}')"
echo "JOURNAL_SHA256=$JOURNAL_HASH"
if [ "$JOURNAL_HASH" = "cc1afcff0a9a8608a344ae43298a60ad212236d87c78235f400f7b3e170b96da" ]; then
    echo "JOURNAL_HASH_MATCH=PASS"
else
    echo "JOURNAL_HASH_MATCH=FAIL"
    exit 1
fi

echo
echo "--- 3. Verify key SHA256 (content not displayed) ---"
KEY_HASH="$(sha256sum "$KEY" | awk '{print $1}')"
echo "KEY_SHA256=$KEY_HASH"
if [ "$KEY_HASH" = "35918d59c7591bcf90b40600fd82d792fcb058f063cf7d624cf720408c0c22d3" ]; then
    echo "KEY_HASH_MATCH=PASS"
else
    echo "KEY_HASH_MATCH=FAIL"
    exit 1
fi

echo
echo "TRANSFERRED_FILES_INTEGRITY=PASS"
echo "KEY_CONTENT_DISPLAYED=NO"
echo "FILES_MOVED_OR_MODIFIED=NO"
```

Both the journal and the verification key matched the SHA-256 of the original files on `pve` (journal 8MiB, key 44 bytes).

## 3.4 Placing Them in a Root-Only Location

> **Run on: VM 240**

```bash
echo "===== VM240: INSTALL FSS VERIFICATION MATERIAL ====="

SRC_JOURNAL="/home/ag/fss-independent-system-20261124.journal"
SRC_KEY="/home/ag/fss-verification-key-20261124.txt"
DST_JOURNAL="/root/fss-independent-system-20261124.journal"
DST_KEY="/root/fss-verification-key-20261124.txt"

echo
echo "--- 1. Check destination paths ---"
for f in "$DST_JOURNAL" "$DST_KEY"; do
    if [ -e "$f" ]; then
        echo "DESTINATION_ALREADY_EXISTS=$f"
        exit 1
    fi
done

echo
echo "--- 2. Copy verified files into root-only area ---"
install -o root -g root -m 600 "$SRC_JOURNAL" "$DST_JOURNAL" || exit 1
install -o root -g root -m 600 "$SRC_KEY" "$DST_KEY" || exit 1

echo
echo "--- 3. Verify installed file hashes ---"
sha256sum "$DST_JOURNAL" "$DST_KEY"

JOURNAL_HASH="$(sha256sum "$DST_JOURNAL" | awk '{print $1}')"
KEY_HASH="$(sha256sum "$DST_KEY" | awk '{print $1}')"

[ "$JOURNAL_HASH" = "cc1afcff0a9a8608a344ae43298a60ad212236d87c78235f400f7b3e170b96da" ] || exit 1
[ "$KEY_HASH" = "35918d59c7591bcf90b40600fd82d792fcb058f063cf7d624cf720408c0c22d3" ] || exit 1

echo
echo "--- 4. Verify ownership and permissions ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s PATH=%n' "$DST_JOURNAL" "$DST_KEY"

echo
echo "ROOT_COPY_HASH_MATCH=PASS"
echo "ROOT_COPY_PERMISSIONS=SET"
echo "SOURCE_FILES_PRESERVED=YES"
echo "KEY_CONTENT_DISPLAYED=NO"
```

The journal and verification key were placed in `/root/` as `root:root`, `600`, and the hashes matched. The original files in `/home/ag/` are kept.

## 3.5 Checking on VM 240

> **Run on: VM 240**

```bash
echo "===== VM240: INDEPENDENT FSS ARCHIVE VERIFICATION ====="

JOURNAL="/root/fss-independent-system-20261124.journal"
KEY="/root/fss-verification-key-20261124.txt"

echo
echo "--- 1. Verify systemd version ---"
systemd --version | head -n 1

echo
echo "--- 2. Inspect archived journal header ---"
journalctl --header --file="$JOURNAL" | grep -E '^(File path|State|Compatible flags|Incompatible flags|Tag objects):'

echo
echo "--- 3. Verify FSS authenticity ---"
journalctl --verify \
    --verify-key="$(cat "$KEY")" \
    --file="$JOURNAL"
VERIFY_STATUS=$?

echo
echo "VM240_FSS_VERIFY_EXIT_STATUS=$VERIFY_STATUS"

if [ "$VERIFY_STATUS" -eq 0 ]; then
    echo "VM240_INDEPENDENT_FSS_VERIFICATION=PASS"
else
    echo "VM240_INDEPENDENT_FSS_VERIFICATION=FAIL"
fi

echo "KEY_CONTENT_DISPLAYED=NO"
echo "ARCHIVE_MODIFIED=NO"
exit "$VERIFY_STATUS"
```

| Checked | Result |
|---|---|
| Checking host | VM 240 `192.168.0.222` (systemd 255.4) |
| Archive | `ARCHIVED`, `SEALED`, `SEALED_CONTINUOUS`, `Tag objects` 9 |
| Period checked | 2026-11-24 01:43:04 – 02:00:00 UTC |
| `journalctl --verify --verify-key` | `PASS` |

**On a host other than VM 230, FSS verification of the archive moved from VM 230 succeeded.**

# Chapter 4: Final Check in Three Places

## 4.1 VM 240

> **Run on: VM 240**

```bash
echo "===== VM240: FINAL READ-ONLY FSS AUDIT ====="

JOURNAL="/root/fss-independent-system-20261124.journal"
KEY="/root/fss-verification-key-20261124.txt"

echo
echo "--- 1. Host identity and systemd ---"
hostname
date -u '+UTC_TIME=%Y-%m-%dT%H:%M:%SZ'
systemd --version | head -n 1

echo
echo "--- 2. Verification material metadata ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s PATH=%n' "$JOURNAL" "$KEY"

echo
echo "--- 3. SHA256 integrity ---"
sha256sum "$JOURNAL" "$KEY"

echo
echo "--- 4. Archive FSS header ---"
journalctl --header --file="$JOURNAL" |
    grep -E '^(State|Compatible flags|Incompatible flags|Tag objects):'

echo
echo "--- 5. Repeat cryptographic verification ---"
journalctl --verify \
    --verify-key="$(cat "$KEY")" \
    --file="$JOURNAL"
VERIFY_STATUS=$?

echo
echo "FINAL_AUDIT_VERIFY_EXIT_STATUS=$VERIFY_STATUS"

if [ "$VERIFY_STATUS" -eq 0 ]; then
    echo "FINAL_AUDIT_RESULT=PASS"
else
    echo "FINAL_AUDIT_RESULT=FAIL"
fi

echo
echo "FILES_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
echo "KEY_CONTENT_DISPLAYED=NO"

exit "$VERIFY_STATUS"
```

As in the first verification, FSS verification passed again, and hashes, owner and permissions were unchanged.

## 4.2 `pve`

> **Run on: pve**

```bash
echo "===== PVE: FINAL FSS SOURCE PRESERVATION AUDIT ====="

JOURNAL="/root/fss-independent-system-20261124.journal"
KEY="/root/fss-verification-key-20261124.txt"

echo
echo "--- 1. Host identity and systemd ---"
hostname
date -u '+UTC_TIME=%Y-%m-%dT%H:%M:%SZ'
systemd --version | head -n 1

echo
echo "--- 2. Source file metadata ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s PATH=%n' "$JOURNAL" "$KEY" || exit 1

echo
echo "--- 3. Source SHA256 integrity ---"
JOURNAL_HASH="$(sha256sum "$JOURNAL" | awk '{print $1}')"
KEY_HASH="$(sha256sum "$KEY" | awk '{print $1}')"

echo "JOURNAL_SHA256=$JOURNAL_HASH"
echo "KEY_SHA256=$KEY_HASH"

if [ "$JOURNAL_HASH" = "cc1afcff0a9a8608a344ae43298a60ad212236d87c78235f400f7b3e170b96da" ] &&
   [ "$KEY_HASH" = "35918d59c7591bcf90b40600fd82d792fcb058f063cf7d624cf720408c0c22d3" ]; then
    echo "PVE_SOURCE_HASH_MATCH=PASS"
else
    echo "PVE_SOURCE_HASH_MATCH=FAIL"
    exit 1
fi

echo
echo "--- 4. Archive header compatibility ---"
journalctl --header --file="$JOURNAL" 2>&1 |
    grep -E '^(State|Compatible flags|Incompatible flags|Tag objects):|unknown extensions|corruption detected'

echo
echo "PVE_SOURCE_FILES_MODIFIED=NO"
echo "KEY_CONTENT_DISPLAYED=NO"
```

The SHA-256 of the original journal and the verification key matched, and owner and permissions were unchanged (systemd 252 on `pve` cannot perform cryptographic verification).

## 4.3 VM 230

> **Run on: VM 230**

```bash
echo "===== VM230: FINAL FSS ORIGIN AUDIT ====="

KEY="/root/fss-verification-key-20261124.txt"
ARCHIVE="/var/log/journal/b21f0e30faf4447bbe59cc1be7a0b169/system@a5afdaa8e8854b2dadf2e328b59278c6-0000000000005850-000660fbd4d4fbe3.journal"
CURRENT="/var/log/journal/b21f0e30faf4447bbe59cc1be7a0b169/system.journal"

echo
echo "--- 1. Host identity and systemd ---"
hostname
date -u '+UTC_TIME=%Y-%m-%dT%H:%M:%SZ'
systemd --version | head -n 1

echo
echo "--- 2. Verify source archive and key metadata ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s PATH=%n' "$ARCHIVE" "$KEY" || exit 1

echo
echo "--- 3. Verify source archive SHA256 ---"
sha256sum "$ARCHIVE"
ARCHIVE_HASH="$(sha256sum "$ARCHIVE" | awk '{print $1}')"

if [ "$ARCHIVE_HASH" = "cc1afcff0a9a8608a344ae43298a60ad212236d87c78235f400f7b3e170b96da" ]; then
    echo "VM230_ARCHIVE_HASH_MATCH=PASS"
else
    echo "VM230_ARCHIVE_HASH_MATCH=FAIL"
    exit 1
fi

echo
echo "--- 4. Inspect archived journal FSS header ---"
journalctl --header --file="$ARCHIVE" |
    grep -E '^(State|Compatible flags|Incompatible flags|Tag objects):'

echo
echo "--- 5. Re-verify archived journal cryptographically ---"
journalctl --verify --verify-key="$(cat "$KEY")" --file="$ARCHIVE"
ARCHIVE_STATUS=$?
echo "VM230_ARCHIVE_VERIFY_EXIT_STATUS=$ARCHIVE_STATUS"

echo
echo "--- 6. Inspect current system journal FSS header ---"
journalctl --header --file="$CURRENT" |
    grep -E '^(State|Compatible flags|Incompatible flags|Tag objects):'

echo
echo "KEY_CONTENT_DISPLAYED=NO"
echo "JOURNAL_FILES_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"

exit "$ARCHIVE_STATUS"
```

| Place | Role | Result |
|---|---|---|
| VM 230 | origin | SHA-256 match, `SEALED`, `SEALED_CONTINUOUS`, `Tag objects` 9, verification exit code `0` |
| `pve` | storage | journal and key SHA-256 match; original unchanged |
| VM 240 | verification on another host | passed with systemd 255.4 |

# Closing Notes

In Part 65 we checked VM 230's FSS-sealed journal on another host (VM 240).

| Item | Result |
|---|---|
| Archive for verification | VM 230 → `pve` → VM 240, SHA-256 matching everywhere |
| `pve` | cannot verify this form of journal because of systemd 252 (storage only) |
| VM 240 | Ubuntu 24.04.5, systemd 255.4, 2 vCPUs, 4GiB, 32GiB, `192.168.0.222` |
| Verification on another host | passed |

In the next part, Part 66, we make this verification run automatically every 15 minutes.

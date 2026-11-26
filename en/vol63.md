---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 63: Moving the FSS Verification Key to the Proxmox Host"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 63 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". We move the FSS verification key created in Part 62 outside VM 230, to **`/root` on the Proxmox host `pve`** (root only).

1. Check the destination `pve` and the path from VM 230
2. Compare `pve`'s SSH host key with the value seen on its console, then register it on VM 230
3. On VM 230, create an SSH key used only for moving files to `pve`, and register the public key on `pve` with restrictions (`restrict`)
4. Move the verification key and confirm the match with SHA-256

Methods that disable SSH host key checking are not used.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **pve**: the Proxmox host (root). The Shell (console) of node `pve` in the Proxmox web interface

> **Caution:** Run the VM 230 commands only after checking that the prompt is `root@ai-defense-manager`. Running them on `pve` would check a connection to `pve` itself. Running them as an ordinary user (`aidefense`) fails because the root-only key cannot be read.

# Chapter 1: Destination and Path

## 1.1 The `pve` Side

> **Run on: pve**

```bash
echo "===== PVE: FSS VERIFICATION KEY DESTINATION PREFLIGHT ====="

echo
echo "--- 1. Host identity ---"
hostname
id

echo
echo "--- 2. Network addresses ---"
ip -brief address

echo
echo "--- 3. SSH service state ---"
systemctl show ssh.service \
  -p ActiveState -p SubState -p MainPID 2>/dev/null ||
systemctl show sshd.service \
  -p ActiveState -p SubState -p MainPID 2>/dev/null

echo
echo "--- 4. SSH listening sockets ---"
ss -lntp | grep -E '(:22[[:space:]]|:22$)' || true

echo
echo "--- 5. Root directory permissions ---"
stat -c '%A %a %U:%G %n' /root

echo
echo "FSS_KEY_TRANSFERRED=NO"
echo "FILES_CREATED=NO"
echo "CONFIGURATION_MODIFIED=NO"
```

| Item | Result |
|---|---|
| `pve` IP address | `192.168.0.240` |
| VM 230 IP address | `192.168.0.221` |
| `pve` SSH | running, listening on TCP 22 |
| `/root` | `root:root`, `700` |

## 1.2 The VM 230 Side

> **Run on: VM 230**

```bash
echo "===== VM230: HOST IDENTITY AND PVE ROUTE CHECK ====="

echo
echo "--- 1. Confirm execution host ---"
hostname
ip -brief address

echo
echo "--- 2. Route to PVE ---"
ip route get 192.168.0.240

echo
echo "--- 3. Existing SSH identity metadata ---"
for f in /root/.ssh/id_ed25519 /root/.ssh/id_rsa \
         /root/.ssh/known_hosts; do
    if [ -e "$f" ]; then
        stat -c '%A %a %U:%G %s bytes %n' "$f"
    else
        echo "ABSENT: $f"
    fi
done

echo
echo "FSS_KEY_TRANSFERRED=NO"
echo "REMOTE_FILES_CREATED=NO"
echo "SSH_CONFIGURATION_MODIFIED=NO"
```

VM 230 reaches `pve` (`192.168.0.240`) directly. VM 230's root had no SSH key, and `pve`'s ED25519 host key was not registered in `known_hosts`.

# Chapter 2: Checking and Registering `pve`'s Host Key

## 2.1 Viewing the Fingerprint on the Console

As the trusted value, we take the fingerprint on `pve`'s console.

> **Run on: pve**

```bash
echo "===== PVE: SSH HOST KEY FINGERPRINTS ====="

echo
echo "--- ED25519 host key ---"
if [ -f /etc/ssh/ssh_host_ed25519_key.pub ]; then
    ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
else
    echo "ED25519_HOST_KEY=ABSENT"
fi

echo
echo "--- RSA host key ---"
if [ -f /etc/ssh/ssh_host_rsa_key.pub ]; then
    ssh-keygen -lf /etc/ssh/ssh_host_rsa_key.pub
else
    echo "RSA_HOST_KEY=ABSENT"
fi

echo
echo "--- ECDSA host key ---"
if [ -f /etc/ssh/ssh_host_ecdsa_key.pub ]; then
    ssh-keygen -lf /etc/ssh/ssh_host_ecdsa_key.pub
else
    echo "ECDSA_HOST_KEY=ABSENT"
fi

echo
echo "PRIVATE_HOST_KEY_DISPLAYED=NO"
echo "SSH_CONFIGURATION_MODIFIED=NO"
echo "FSS_KEY_TRANSFERRED=NO"
```

## 2.2 Comparing with the Value Seen from VM 230

> **Run on: VM 230**

```bash
echo "===== VM230: PVE SSH HOST KEY FINGERPRINT COMPARISON ====="

echo
echo "--- 1. Console-verified ED25519 fingerprint ---"
echo "SHA256:fK1KIJ/SzYtX7qbjGn1siW1vV2zIdpv9HdsR28wCFWA"

echo
echo "--- 2. Network-observed ED25519 fingerprint ---"
ssh-keyscan -T 5 -t ed25519 192.168.0.240 2>/dev/null |
    ssh-keygen -lf -

echo
echo "--- 3. Existing known_hosts entry ---"
ssh-keygen -F 192.168.0.240 \
    -f /root/.ssh/known_hosts 2>/dev/null ||
    echo "NO_EXISTING_IP_ENTRY"

echo
echo "KNOWN_HOSTS_MODIFIED=NO"
echo "SSH_AUTHENTICATION_ATTEMPTED=NO"
echo "FSS_KEY_TRANSFERRED=NO"
```

The value seen on the console and the ED25519 fingerprint obtained over the network from VM 230 matched exactly.

> **Caution:** This script contains the fingerprint from the time of the build. In your own environment, replace it with the value seen in 2.1.

## 2.3 Registering in `known_hosts`

> **Run on: VM 230**

```bash
echo "===== VM230: REGISTER VERIFIED PVE SSH HOST KEY ====="

EXPECTED="SHA256:fK1KIJ/SzYtX7qbjGn1siW1vV2zIdpv9HdsR28wCFWA"
KNOWN_HOSTS="/root/.ssh/known_hosts"

KEY_LINE="$(ssh-keyscan -T 5 -t ed25519 192.168.0.240 2>/dev/null |
    awk '$2 == "ssh-ed25519" {print; exit}')"

if [ -z "$KEY_LINE" ]; then
    echo "HOST_KEY_FETCH=FAIL"
    exit 1
fi

ACTUAL="$(printf '%s\n' "$KEY_LINE" | ssh-keygen -lf - | awk '{print $2}')"

if [ "$ACTUAL" != "$EXPECTED" ]; then
    echo "HOST_KEY_MATCH=FAIL"
    exit 1
fi

install -d -m 700 -o root -g root /root/.ssh
touch "$KNOWN_HOSTS"
chmod 600 "$KNOWN_HOSTS"

if ssh-keygen -F 192.168.0.240 -f "$KNOWN_HOSTS" >/dev/null 2>&1; then
    echo "EXISTING_ENTRY=PRESENT"
else
    printf '%s\n' "$KEY_LINE" >> "$KNOWN_HOSTS"
    echo "HOST_KEY_REGISTERED=YES"
fi

echo
echo "--- Registration verification ---"
ssh-keygen -F 192.168.0.240 -f "$KNOWN_HOSTS" |
    ssh-keygen -lf -

echo
stat -c '%A %a %U:%G %n' /root/.ssh "$KNOWN_HOSTS"

echo
echo "HOST_KEY_CONTENT_DISPLAYED=NO"
echo "SSH_AUTHENTICATION_ATTEMPTED=NO"
echo "FSS_KEY_TRANSFERRED=NO"
```

We registered `pve`'s ED25519 host key in VM 230's `/root/.ssh/known_hosts` and compared again; it matched (directory `700`, file `600`).

# Chapter 3: The SSH Key for Moving Files

## 3.1 Creating the Key on VM 230

We create an Ed25519 key dedicated to VM 230. The secret key is kept in a root-only location on VM 230 and is neither displayed nor transferred.

> **Run on: VM 230**

```bash
echo "===== VM230: GENERATE TEMPORARY PVE TRANSFER KEY ====="

KEY="/root/.ssh/id_ed25519_pve_fss"

if [ -e "$KEY" ] || [ -e "$KEY.pub" ]; then
    echo "KEY_PATH_ALREADY_EXISTS=ABORT"
    exit 1
fi

umask 077
ssh-keygen -q -t ed25519 -a 100 -N "" \
    -C "vm230-fss-key-transfer-20261124" \
    -f "$KEY" || exit 1

chmod 600 "$KEY"
chmod 644 "$KEY.pub"

echo
echo "--- Key metadata (private content hidden) ---"
stat -c '%A %a %U:%G %s bytes %n' "$KEY" "$KEY.pub"

echo
echo "--- Public key fingerprint ---"
ssh-keygen -lf "$KEY.pub"

echo
echo "--- Public key (safe to register on PVE) ---"
cat "$KEY.pub"

echo
echo "PRIVATE_KEY_DISPLAYED=NO"
echo "PRIVATE_KEY_TRANSFERRED=NO"
echo "PVE_AUTHORIZED_KEYS_MODIFIED=NO"
echo "FSS_VERIFICATION_KEY_TRANSFERRED=NO"
```

The secret key is `/root/.ssh/id_ed25519_pve_fss` (`600`), and the public key is `/root/.ssh/id_ed25519_pve_fss.pub`.

## 3.2 The Structure of `authorized_keys` on `pve`

> **Run on: pve**

```bash
echo "===== PVE: SSH ROOT AUTHENTICATION DIAGNOSTICS ====="

echo
echo "--- 1. Effective SSH authentication policy ---"
sshd -T -C user=root,addr=192.168.0.221,host=ai-defense-manager |
  grep -E '^(permitrootlogin|pubkeyauthentication|passwordauthentication|authorizedkeysfile|authenticationmethods|strictmodes|allowusers|denyusers) '

echo
echo "--- 2. Authorized keys metadata ---"
stat -c '%A %a %U:%G %n' \
  /root /root/.ssh /root/.ssh/authorized_keys

echo
echo "--- 3. Registered key fingerprint (matching key only) ---"
ssh-keygen -lf /root/.ssh/authorized_keys 2>/dev/null |
  grep 'eMxXY8eMoiEXClIBdttWHUZXJFYiPFR48m+y2hxQV1s' ||
  echo "EXPECTED_KEY_FINGERPRINT_NOT_FOUND"

echo
echo "--- 4. Recent SSH authentication log (sanitized) ---"
journalctl -u ssh.service --since "-10 minutes" --no-pager -o cat |
  tail -40 |
  sed -E 's/(Accepted|Failed) publickey for [^ ]+ from [^ ]+ port [0-9]+/\1 publickey [REDACTED]/g'

echo
echo "SSH_CONFIGURATION_MODIFIED=NO"
echo "AUTHORIZED_KEYS_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "FSS_VERIFICATION_KEY_TRANSFERRED=NO"
```

```bash
echo "===== PVE: AUTHORIZED_KEYS SYMLINK INVESTIGATION ====="

AUTH="/root/.ssh/authorized_keys"

echo
echo "--- 1. Symlink target ---"
readlink "$AUTH"
readlink -e "$AUTH" || true

TARGET="$(readlink -e "$AUTH" || true)"

if [ -n "$TARGET" ]; then
    echo
    echo "--- 2. Target metadata ---"
    namei -l "$AUTH"
    stat -c '%F %A %a %U:%G %s bytes %n' "$TARGET"

    echo
    echo "--- 3. Registered public key presence ---"
    if grep -Fq \
      'AAAAC3NzaC1lZDI1NTE5AAAAIOFOZUEp31Bgv68F0Xh+H4+A/6FGitHwN+VTVTiUTT/f' \
      "$TARGET"; then
        echo "PUBLIC_KEY_PRESENT=YES"
    else
        echo "PUBLIC_KEY_PRESENT=NO"
    fi

    echo
    echo "--- 4. Matching key fingerprint ---"
    awk '
      $0 ~ /AAAAC3NzaC1lZDI1NTE5AAAAIOFOZUEp31Bgv68F0Xh\+H4\+A\/6FGitHwN\+VTVTiUTT\/f/ {
        print $2, $3
      }
    ' "$TARGET" | ssh-keygen -lf - 2>/dev/null ||
      echo "FINGERPRINT_EXTRACTION_FAILED"
fi

echo
echo "--- 5. PVE SSH key management references ---"
grep -RIl --exclude='authorized_keys' \
  'authorized_keys' /etc/ssh /etc/pve 2>/dev/null |
  head -20

echo
echo "AUTHORIZED_KEYS_MODIFIED=NO"
echo "SSH_CONFIGURATION_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "FSS_VERIFICATION_KEY_TRANSFERRED=NO"
```

`pve`'s SSH had `PermitRootLogin yes`, `PubkeyAuthentication yes` and `AuthorizedKeysFile .ssh/authorized_keys`, but `/root/.ssh/authorized_keys` was not an ordinary file; it was **a symbolic link to `/etc/pve/priv/authorized_keys`**. This file is managed by the Proxmox cluster file system (pmxcfs).

> **Run on: pve**

```bash
echo "===== PVE: PMXCFS AND CLUSTER AUTHORIZED KEYS AUDIT ====="

echo
echo "--- 1. Cluster status ---"
pvecm status 2>&1

echo
echo "--- 2. PVE cluster filesystem service ---"
systemctl show pve-cluster.service \
  -p ActiveState -p SubState -p MainPID -p Result

echo
echo "--- 3. pmxcfs mount ---"
findmnt -T /etc/pve -o TARGET,SOURCE,FSTYPE,OPTIONS

echo
echo "--- 4. Authorized keys file metadata ---"
stat -c '%F %A %a %U:%G %s bytes %n' \
  /etc/pve/priv/authorized_keys

echo
echo "--- 5. Authorized key fingerprints (no key contents) ---"
ssh-keygen -lf /etc/pve/priv/authorized_keys 2>/dev/null ||
  echo "AUTHORIZED_KEYS_FINGERPRINT_READ=FAIL"

echo
echo "--- 6. Recent pmxcfs messages ---"
journalctl -u pve-cluster.service --since "-15 minutes" \
  --no-pager -o cat | tail -30

echo
echo "AUTHORIZED_KEYS_MODIFIED=NO"
echo "SSH_CONFIGURATION_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "FSS_VERIFICATION_KEY_TRANSFERRED=NO"
```

`pve` was not a cluster using Corosync but a single-node configuration. `pve-cluster` is running normally, and `/etc/pve` is mounted by pmxcfs.

## 3.3 Registering the Public Key

We specify the link target `/etc/pve/priv/authorized_keys` directly and add the public key with `restrict` (restricting port forwarding, PTY and so on). The existing RSA key is kept.

> **Run on: pve**

```bash
echo "===== PVE: DIRECT PMXCFS AUTHORIZED KEY REGISTRATION ====="

set -eu

TARGET="/etc/pve/priv/authorized_keys"
KEY_BLOB='AAAAC3NzaC1lZDI1NTE5AAAAIOFOZUEp31Bgv68F0Xh+H4+A/6FGitHwN+VTVTiUTT/f'
KEY_LINE='restrict ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOFOZUEp31Bgv68F0Xh+H4+A/6FGitHwN+VTVTiUTT/f vm230-fss-key-transfer-20261124'

echo
echo "--- 1. Pre-write checks ---"
test -f "$TARGET"
test "$(stat -c '%U' "$TARGET")" = root

if grep -Fq "$KEY_BLOB" "$TARGET"; then
    echo "KEY_ALREADY_PRESENT=YES"
else
    printf '%s\n' "$KEY_LINE" >> "$TARGET"
    echo "DIRECT_APPEND=EXECUTED"
fi

echo
echo "--- 2. Immediate persistence check ---"
if grep -Fq "$KEY_BLOB" "$TARGET"; then
    echo "IMMEDIATE_READBACK=PASS"
else
    echo "IMMEDIATE_READBACK=FAIL"
    exit 1
fi

echo
echo "--- 3. File metadata after write ---"
stat -c 'size=%s modify=%y change=%z inode=%i' "$TARGET"

echo
echo "--- 4. Key fingerprint ---"
ssh-keygen -lf "$TARGET" |
    grep 'eMxXY8eMoiEXClIBdttWHUZXJFYiPFR48m+y2hxQV1s'

echo
echo "--- 5. Re-read through PVE symlink ---"
grep -Fq "$KEY_BLOB" /root/.ssh/authorized_keys
echo "SYMLINK_READBACK=PASS"

echo
echo "EXISTING_KEYS_REMOVED=NO"
echo "SSH_CONFIGURATION_MODIFIED=NO"
echo "SSH_SERVICE_RESTARTED=NO"
echo "FSS_VERIFICATION_KEY_TRANSFERRED=NO"
```

> **Caution:** `KEY_BLOB` and `KEY_LINE` in the script are the public key from the time of the build. In your own environment, replace them with the contents of the `.pub` created in 3.1. Using other methods intended to write to `/root/.ssh/authorized_keys` sometimes did not leave the key on the pmxcfs side.

We confirmed reading it back right after writing, the public key fingerprint match, reading it back through `/root/.ssh/authorized_keys`, and that the existing RSA key remains. No SSH configuration changes or restarts were made.

## 3.4 Testing Authentication

Run as root.

> **Run on: VM 230**

```bash
echo "===== VM230: RETEST PVE SSH AS ROOT ====="

sudo -H ssh \
    -i /root/.ssh/id_ed25519_pve_fss \
    -o IdentitiesOnly=yes \
    -o BatchMode=yes \
    -o StrictHostKeyChecking=yes \
    -o UserKnownHostsFile=/root/.ssh/known_hosts \
    -o ConnectTimeout=5 \
    root@192.168.0.240 \
    'printf "PVE_SSH_AUTH=PASS\n"; hostname; id -u'

STATUS=$?

echo
echo "SSH_EXIT_STATUS=$STATUS"
echo "FSS_VERIFICATION_KEY_TRANSFERRED=NO"
echo "REMOTE_FILES_CREATED=NO"
```

`PVE_SSH_AUTH=PASS`, the target was `pve`, and the user was UID `0`.

# Chapter 4: Moving the Verification Key

We move the verification key, not the secret key. After moving, we compare permissions, owner and SHA-256 without displaying the contents.

> **Run on: VM 230**

```bash
echo "===== VM230: SECURE FSS VERIFICATION KEY ESCROW TO PVE ====="

set -eu

SOURCE="/root/fss-verification-key-20261124.txt"
DEST="root@192.168.0.240:/root/fss-verification-key-20261124.txt"
REMOTE="/root/fss-verification-key-20261124.txt"

echo
echo "--- 1. Source file preflight ---"
test -f "$SOURCE"
test "$(stat -c '%U:%G' "$SOURCE")" = "root:root"
test "$(stat -c '%a' "$SOURCE")" = "600"
echo "SOURCE_FILE=PASS"
echo "SOURCE_SIZE=$(stat -c '%s' "$SOURCE")"

echo
echo "--- 2. Destination preflight ---"
if ssh -i /root/.ssh/id_ed25519_pve_fss \
    -o IdentitiesOnly=yes -o BatchMode=yes \
    -o StrictHostKeyChecking=yes \
    -o UserKnownHostsFile=/root/.ssh/known_hosts \
    root@192.168.0.240 "test ! -e '$REMOTE'"; then
    echo "DESTINATION_ABSENT=YES"
else
    echo "DESTINATION_ALREADY_EXISTS_OR_CHECK_FAILED"
    exit 1
fi

echo
echo "--- 3. Transfer with source permissions preserved ---"
scp -p \
    -i /root/.ssh/id_ed25519_pve_fss \
    -o IdentitiesOnly=yes \
    -o BatchMode=yes \
    -o StrictHostKeyChecking=yes \
    -o UserKnownHostsFile=/root/.ssh/known_hosts \
    "$SOURCE" "$DEST"

echo
echo "--- 4. Remote ownership and permission enforcement ---"
ssh -i /root/.ssh/id_ed25519_pve_fss \
    -o IdentitiesOnly=yes -o BatchMode=yes \
    -o StrictHostKeyChecking=yes \
    -o UserKnownHostsFile=/root/.ssh/known_hosts \
    root@192.168.0.240 \
    "chown root:root '$REMOTE' && chmod 600 '$REMOTE' && test \"\$(stat -c '%U:%G:%a' '$REMOTE')\" = 'root:root:600' && echo REMOTE_PERMISSIONS=PASS"

echo
echo "--- 5. SHA-256 comparison (key contents not displayed) ---"
LOCAL_HASH="$(sha256sum "$SOURCE" | awk '{print $1}')"
REMOTE_HASH="$(ssh -i /root/.ssh/id_ed25519_pve_fss \
    -o IdentitiesOnly=yes -o BatchMode=yes \
    -o StrictHostKeyChecking=yes \
    -o UserKnownHostsFile=/root/.ssh/known_hosts \
    root@192.168.0.240 \
    "sha256sum '$REMOTE'" | awk '{print $1}')"

if [ "$LOCAL_HASH" = "$REMOTE_HASH" ]; then
    echo "SHA256_MATCH=PASS"
else
    echo "SHA256_MATCH=FAIL"
    exit 1
fi

echo
echo "LOCAL_SOURCE_RETAINED=YES"
echo "FSS_VERIFICATION_KEY_ESCROW=PASS"
echo "JOURNALD_RESTARTED=NO"
echo "FSS_SEALING_ACTIVATION_VERIFIED=NO"
```

| Checked | Result |
|---|---|
| SSH public key authentication to `pve` | succeeded |
| Transfer of the verification key | succeeded |
| File on `pve` | `/root/fss-verification-key-20261124.txt`, `root:root`, `600` |
| SHA-256 | match |
| Original file on VM 230 | kept |

# Closing Notes

In Part 63 we stored the FSS verification key outside VM 230 (in `/root` on `pve`).

| Item | Result |
|---|---|
| `pve` host key | registered in `known_hosts` after comparing with the console value |
| Key for moving files | VM 230 `/root/.ssh/id_ed25519_pve_fss`; registered in `pve`'s `/etc/pve/priv/authorized_keys` with `restrict` |
| Verification key | `pve` `/root/fss-verification-key-20261124.txt` (`600`, SHA-256 match) |
| Still to do | have journald load the sealing key and confirm that sealing begins |

In the next part, Part 64, we start FSS sealing.

---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 62: Creating FSS Keys to Guard Against Log Tampering"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 62 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 61 we set a size limit for the journal. Here, after a final check of who can read the logs, we prepare **a mechanism for detecting that logs have been rewritten**.

The systemd journal has a mechanism called **FSS (Forward Secure Sealing)**.

- The secret sealing key (Seal key) is kept inside the VM and seals the journal at fixed intervals (here, 15 minutes). The key moves forward with time, and keys for earlier intervals do not remain
- The verification key is stored outside the VM, and `journalctl --verify --verify-key=…` checks that nothing was rewritten after sealing

The setting `Seal=yes` (default) alone does not make FSS work; the keys must be created with `journalctl --setup-keys`.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

> **Caution:** Do not display or paste the contents of the verification key.

# Chapter 1: Final Check of Who Can Read the Logs

## 1.1 syslog

> **Run on: VM 230**

```bash
echo "===== VM230: LOG ACCESS CONTROL FINAL AUDIT ====="

echo
echo "--- 1. Log directory permissions ---"
namei -l /var/log/syslog
namei -l /var/log/auth.log

echo
echo "--- 2. Log directory ACL ---"
getfacl -cp /var/log 2>/dev/null
getfacl -cp /var/log/syslog /var/log/auth.log 2>/dev/null

echo
echo "--- 3. Log file permissions ---"
stat -c '%A %a %U:%G %n' \
  /var/log \
  /var/log/syslog \
  /var/log/auth.log \
  /var/log/syslog.1 \
  /var/log/auth.log.1

echo
echo "--- 4. Relevant group membership ---"
getent group adm
getent group syslog
id ai-defense
id aidefense
id syslog

echo
echo "--- 5. Rsyslog spool permissions ---"
namei -l /var/spool/rsyslog
stat -c '%A %a %U:%G %n' /var/spool/rsyslog

echo
echo "--- 6. Log access-related capabilities ---"
getcap -r /usr/sbin/rsyslogd /usr/bin/journalctl 2>/dev/null || true

echo
echo "LOG_FILES_MODIFIED=NO"
echo "ACL_MODIFIED=NO"
echo "PERMISSIONS_MODIFIED=NO"
echo "CONFIGURATION_MODIFIED=NO"
```

`/var/log/syslog`, `/var/log/auth.log` and the rotated logs are `syslog:adm`, `640`, with no additional ACLs, and the service account `ai-defense` has no permission to read the logs.

## 1.2 The Journal

> **Run on: VM 230**

```bash
echo "===== VM230: JOURNAL ACCESS CONTROL AUDIT ====="

echo
echo "--- 1. Journal-related group membership ---"
getent group systemd-journal
getent group adm
id ai-defense
id aidefense
id syslog

echo
echo "--- 2. Persistent journal directory ---"
if [ -d /var/log/journal ]; then
  namei -l /var/log/journal
  stat -c '%A %a %U:%G %n' /var/log/journal
else
  echo "PERSISTENT_JOURNAL_DIRECTORY=ABSENT"
fi

echo
echo "--- 3. Runtime journal directory ---"
if [ -d /run/log/journal ]; then
  namei -l /run/log/journal
  stat -c '%A %a %U:%G %n' /run/log/journal
else
  echo "RUNTIME_JOURNAL_DIRECTORY=ABSENT"
fi

echo
echo "--- 4. Journal file ownership and permissions ---"
find /var/log/journal /run/log/journal \
  -type f \( -name '*.journal' -o -name '*.journal~' \) \
  -exec stat -c '%A %a %U:%G %s %n' {} + \
  2>/dev/null | head -60

echo
echo "--- 5. Journal directory ACL ---"
getfacl -cp /var/log/journal /run/log/journal \
  2>/dev/null || true

echo
echo "--- 6. Journal access policy ---"
systemd-analyze cat-config systemd/journald.conf |
  grep -E '^[[:space:]]*(Storage|ReadKMsg|Seal|ForwardToSyslog)=' || true

echo
echo "JOURNAL_FILES_MODIFIED=NO"
echo "ACL_MODIFIED=NO"
echo "PERMISSIONS_MODIFIED=NO"
echo "CONFIGURATION_MODIFIED=NO"
```

| Item | Result |
|---|---|
| `/var/log/journal`, `/run/log/journal` | `root:systemd-journal`, `2755` |
| Journal files | `root:systemd-journal`, `640` |
| `systemd-journal` group | no members |
| `ai-defense` | not in a group that can read the journal |

No permission changes are needed.

## 1.3 Integrity and Persistent Storage

> **Run on: VM 230**

```bash
echo "===== VM230: LOG INTEGRITY AND PERSISTENCE AUDIT ====="

echo
echo "--- 1. Journald sealing configuration ---"
systemd-analyze cat-config systemd/journald.conf |
  grep -E '^[[:space:]]*(Seal|Storage|SystemMaxUse|SystemKeepFree|SystemMaxFileSize)=' || true

echo
echo "--- 2. Journal verification ---"
journalctl --verify --no-pager 2>&1 | tail -35

echo
echo "--- 3. Log file immutable attributes ---"
lsattr \
  /var/log/syslog \
  /var/log/auth.log \
  /var/log/journal 2>&1

echo
echo "--- 4. Filesystem mount options ---"
findmnt -T /var/log -o TARGET,SOURCE,FSTYPE,OPTIONS

echo
echo "--- 5. Log filesystem capacity ---"
df -h /var/log
df -i /var/log

echo
echo "--- 6. Rsyslog output destinations ---"
grep -RInE '^[[:space:]]*[^#].*(/var/log/|@@?[^[:space:]]+)' \
  /etc/rsyslog.conf /etc/rsyslog.d \
  2>/dev/null || true

echo
echo "--- 7. Journal file count and size ---"
find /var/log/journal -type f \
  \( -name '*.journal' -o -name '*.journal~' \) \
  -printf '%s %p\n' 2>/dev/null |
  awk '{count++; total+=$1} END {
    printf "FILE_COUNT=%d\nTOTAL_BYTES=%d\nTOTAL_MiB=%.2f\n",
    count, total, total/1048576
  }'

echo
echo "JOURNAL_FILES_MODIFIED=NO"
echo "LOG_FILES_MODIFIED=NO"
echo "CONFIGURATION_MODIFIED=NO"
```

The size limits (512MB, 2GB free, 64MB per file) were in place, all files shown passed the check, there were no immutable attributes, and `/var/log` is ext4 mounted read-write.

# Chapter 2: Is FSS Supported?

> **Run on: VM 230**

```bash
echo "===== VM230: JOURNAL FSS CAPABILITY AND KEY AUDIT ====="

echo
echo "--- 1. Systemd version ---"
systemd --version | head -3

echo
echo "--- 2. Installed journald.conf documentation ---"
if command -v col >/dev/null 2>&1; then
  MANPAGER=cat man journald.conf 2>/dev/null |
    col -b |
    grep -A12 -B4 -E '^[[:space:]]*Seal=|Forward Secure Sealing'
else
  echo "col command unavailable; checking compressed manual"
  zcat /usr/share/man/man5/journald.conf.5.gz 2>/dev/null |
    grep -A12 -B4 -E 'Seal=|Forward Secure Sealing' |
    head -60
fi

echo
echo "--- 3. Seal configuration in all journald config files ---"
grep -RInE '^[[:space:]]*Seal[[:space:]]*=' \
  /etc/systemd/journald.conf \
  /etc/systemd/journald.conf.d \
  /usr/lib/systemd/journald.conf.d \
  /lib/systemd/journald.conf.d \
  2>/dev/null || true

echo
echo "--- 4. Existing FSS-related file metadata ---"
find /var/log /var/lib/systemd /etc/systemd \
  -maxdepth 4 -type f \
  \( -iname '*seal*' -o -iname '*fss*' -o -iname '*journal*key*' \) \
  -printf '%M %u:%g %s %p\n' 2>/dev/null |
  head -60

echo
echo "--- 5. Journal header metadata ---"
journalctl --header --no-pager 2>&1 | head -60

echo
echo "--- 6. Journald service state ---"
systemctl show systemd-journald.service \
  -p ActiveState -p SubState -p MainPID -p Result -p NRestarts

echo
echo "FSS_KEYS_DISPLAYED=NO"
echo "KEY_CONTENT_READ=NO"
echo "CONFIGURATION_MODIFIED=NO"
echo "JOURNAL_FILES_MODIFIED=NO"
```

| Item | Verdict |
|---|---|
| systemd FSS support | supported (systemd 255) |
| Seal default | enabled |
| Explicit Seal setting | none |
| FSS key file | not found |
| `Tag objects` in the journal header | 0 |
| Is FSS working? | no |

Passing the journal integrity check is different from tamper detection by FSS. We proceed in the following order.

1. Create the FSS keys
2. Store the verification key somewhere safe, separate from VM 230 (Part 63)
3. Check the permissions and location of the secret key
4. Confirm that newly created journals are sealed (Part 64)
5. Build a procedure to check with `journalctl --verify --verify-key=...`

FSS protection is not applied retroactively to existing journals.

# Chapter 3: Creating the FSS Keys

## 3.1 Creating the Keys

We create the keys with the standard 15-minute interval. The verification key is saved temporarily to a root-only file on VM 230 and not displayed on screen. journald is not restarted.

> **Run on: VM 230**

```bash
echo "===== VM230: GENERATE JOURNAL FSS KEY PAIR ====="

VERIFY_FILE="/root/fss-verification-key-20261124.txt"
ERROR_FILE="/root/fss-setup-diagnostics-20261124.txt"

echo
echo "--- 1. Pre-generation checks ---"

if [ -e "$VERIFY_FILE" ] || [ -e "$ERROR_FILE" ]; then
  echo "ABORT=TARGET_FILE_ALREADY_EXISTS"
  exit 1
fi

if [ "$(id -u)" -ne 0 ]; then
  echo "ABORT=ROOT_REQUIRED"
  exit 1
fi

umask 077

echo "RUN_AS=root"
echo "INTERVAL=15min"
echo "FORCE_OVERWRITE=NO"

echo
echo "--- 2. Generate FSS keys ---"

journalctl --setup-keys --interval=15min \
  > "$VERIFY_FILE" 2> "$ERROR_FILE"
SETUP_STATUS=$?

chmod 600 "$VERIFY_FILE" "$ERROR_FILE"
chown root:root "$VERIFY_FILE" "$ERROR_FILE"

echo "SETUP_EXIT_STATUS=$SETUP_STATUS"

echo
echo "--- 3. Verification key file metadata (content hidden) ---"
stat -c '%A %a %U:%G %s bytes %n' "$VERIFY_FILE"

echo
echo "--- 4. Diagnostic file metadata (content hidden) ---"
stat -c '%A %a %U:%G %s bytes %n' "$ERROR_FILE"

echo
echo "--- 5. FSS-related journal file metadata ---"
find /var/log/journal -maxdepth 3 -type f \
  \( -iname '*fss*' -o -iname '*seal*' \) \
  -exec stat -c '%A %a %U:%G %s bytes %n' {} + \
  2>/dev/null || true

echo
echo "--- 6. Journald service state ---"
systemctl show systemd-journald.service \
  -p ActiveState -p SubState -p MainPID -p Result -p NRestarts

echo
echo "VERIFICATION_KEY_CONTENT_DISPLAYED=NO"
echo "JOURNAL_FILES_DELETED=NO"
echo "JOURNAL_VACUUM_EXECUTED=NO"
echo "SERVICE_RESTARTED=NO"
echo "CONFIGURATION_MODIFIED=NO"
```

| Checked | Result |
|---|---|
| Exit code | `0` |
| Secret-side FSS file | `/var/log/journal/…/fss`, `root:systemd-journal`, `600` |
| Verification key file | `/root/fss-verification-key-20261124.txt`, `root:root`, `600` |
| journald | still running; not restarted |

## 3.2 Checking the Key Format

> **Run on: VM 230**

```bash
echo "===== VM230: FSS KEY GENERATION VERIFICATION ====="

echo
echo "--- 1. Verification key format (content hidden) ---"
python3 - <<'PY'
from pathlib import Path
import base64

p = Path("/root/fss-verification-key-20261124.txt")
data = p.read_bytes()

try:
    text = data.decode("ascii").strip()
    decoded = base64.b64decode(text, validate=True)
    valid = (
        len(data) == 44
        and len(text) == 43
        and len(decoded) == 32
    )
except Exception:
    valid = False

print("VERIFICATION_KEY_FORMAT=" + ("PASS" if valid else "FAIL"))
print("KEY_CONTENT_DISPLAYED=NO")
PY

echo
echo "--- 2. Sanitized setup diagnostics ---"
sed -E 's/[A-Za-z0-9+\/=_-]{24,}/[REDACTED]/g' \
  /root/fss-setup-diagnostics-20261124.txt

echo
echo "--- 3. FSS secret file metadata ---"
stat -c '%A %a %U:%G %s bytes %n' \
  /var/log/journal/*/fss

echo
echo "--- 4. Journal header sealing indicators ---"
journalctl --header --no-pager 2>/dev/null |
  grep -E '^(File path:|State:|Tag objects:)' |
  head -45

echo
echo "--- 5. Journald runtime state ---"
systemctl show systemd-journald.service \
  -p ActiveState -p SubState -p MainPID -p Result -p NRestarts

echo
echo "FSS_KEY_CONTENT_DISPLAYED=NO"
echo "FSS_SECRET_MODIFIED=NO"
echo "JOURNAL_FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "CONFIGURATION_MODIFIED=NO"
```

The format check in this script assumed "43 characters of standard Base64", which does not match the format systemd actually outputs, so it gave `FAIL`. We change the check and verify again.

> **Run on: VM 230**

```bash
echo "===== VM230: FSS VERIFICATION KEY FORMAT RECHECK ====="

python3 - <<'PY'
from pathlib import Path
import base64
import re

p = Path("/root/fss-verification-key-20261124.txt")
data = p.read_bytes()

print("FILE_SIZE=", len(data))
print("ASCII_ONLY=", all(b < 128 for b in data))
print("TRAILING_NEWLINE=", data.endswith(b"\n"))

try:
    value = data.decode("ascii").strip()
    print("CHARACTER_COUNT=", len(value))
    print("BASE64URL_CHARSET=",
          bool(re.fullmatch(r"[A-Za-z0-9_-]+", value)))

    padded = value + "=" * ((4 - len(value) % 4) % 4)
    decoded = base64.urlsafe_b64decode(padded)

    print("DECODED_LENGTH=", len(decoded))
    print("BASE64URL_FORMAT=",
          "PASS" if len(decoded) == 32 else "FAIL")
except Exception:
    print("BASE64URL_FORMAT=FAIL")

print("KEY_CONTENT_DISPLAYED=NO")
PY

echo
echo "--- FSS secret file metadata ---"
stat -c '%A %a %U:%G %s %n' /var/log/journal/*/fss

echo
echo "--- Journald service state ---"
systemctl show systemd-journald.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts

echo
echo "KEY_REGENERATED=NO"
echo "KEY_CONTENT_DISPLAYED=NO"
echo "SERVICE_RESTARTED=NO"
echo "JOURNAL_FILES_MODIFIED=NO"
```

It decoded correctly to 32 bytes, and the format of the verification key was normal (the file is 44 bytes, ASCII only, with a trailing newline).

# Closing Notes

In Part 62 we checked who can read the logs and created the FSS keys.

| Item | Result |
|---|---|
| Log permissions | the service account cannot read either syslog or the journal |
| FSS support | supported in systemd 255; `Seal` enabled by default |
| FSS keys | created with a 15-minute interval. The secret side is in VM 230's journal directory (`600`); the verification key is `/root/fss-verification-key-20261124.txt` (`600`) |
| Still to do | store the verification key outside the VM; confirm that sealing begins |

We decided to store the verification key in **a root-only location on the Proxmox host `pve`**. In the next part, Part 63, we move it safely from VM 230.

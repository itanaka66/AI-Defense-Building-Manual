---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 64: Running and Checking FSS Sealing"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 64 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 62 we created the FSS keys, and in Part 63 we moved the verification key to the Proxmox host. Here we have journald start sealing and check it with the verification key.

1. Restart journald and check the sealing state
2. Investigate why the seal tags (`Tag objects`) stayed at 0
3. Switch the journal (`journalctl --rotate`) to create a new file and confirm it is sealed
4. Check the sealed journal cryptographically with the verification key

No log deletion, size cleanup or key changes.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: Restarting journald

## 1.1 Restart and Sealing State

We restart only journald on VM 230, once.

> **Run on: VM 230**

```bash
echo "===== VM230: RESTART JOURNALD AND CHECK FSS SEALING ====="

echo
echo "--- 1. Restart systemd-journald ---"
systemctl restart systemd-journald.service
RESTART_STATUS=$?
echo "RESTART_EXIT_STATUS=$RESTART_STATUS"

if [ "$RESTART_STATUS" -ne 0 ]; then
    echo "JOURNALD_RESTART=FAIL"
    exit "$RESTART_STATUS"
fi

echo
echo "--- 2. Service runtime status ---"
systemctl show systemd-journald.service \
  -p ActiveState -p SubState -p MainPID -p Result -p NRestarts \
  -p ExecMainStartTimestamp

echo
echo "--- 3. Journal files and FSS tag counts ---"
find /var/log/journal -type f -name '*.journal' -print0 |
while IFS= read -r -d '' f; do
    echo
    echo "FILE=$(basename "$f")"
    journalctl --header --file="$f" 2>/dev/null |
      grep -E '^(File path|State|Compatible flags|Incompatible flags|Tag objects):' ||
      true
done

echo
echo "--- 4. Recent journald messages ---"
journalctl -u systemd-journald.service -n 12 --no-pager

echo
echo "JOURNALD_RESTARTED=YES"
echo "FSS_TAG_VERIFICATION=NOT_YET_CONFIRMED"
echo "AI_DEFENSE_MANAGER_RESTARTED=NO"
echo "RSYSLOG_RESTARTED=NO"
echo "CONFIGURATION_MODIFIED=NO"
```

The restart succeeded, but `Tag objects` was `0` in every journal file.

## 1.2 Checking After Some Time

> **Run on: VM 230**

```bash
echo "===== VM230: FSS POST-RESTART SEALING AUDIT ====="

echo
echo "--- 1. Current time ---"
date --iso-8601=seconds

echo
echo "--- 2. FSS sealing key metadata ---"
stat -c 'owner=%U:%G mode=%a size=%s modified=%y' \
  /var/log/journal/b21f0e30faf4447bbe59cc1be7a0b169/fss

echo
echo "--- 3. Current journal header ---"
journalctl --header --file=/var/log/journal/b21f0e30faf4447bbe59cc1be7a0b169/system.journal |
  grep -E '^(State|Compatible flags|Incompatible flags|Tag objects):'

echo
echo "--- 4. Journal entry timestamps ---"
journalctl -n 5 --no-pager -o short-iso

echo
echo "--- 5. journald runtime health ---"
systemctl show systemd-journald.service \
  -p ActiveState -p SubState -p MainPID -p Result -p NRestarts

echo
echo "FSS_KEY_CONTENT_DISPLAYED=NO"
echo "CONFIGURATION_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

About 43 minutes after the restart, `Tag objects` was still `0`. journald was `active (running)` with `NRestarts=0`, the FSS key file existed (`root:systemd-journal`, `600`), and there were no FSS-related errors. systemd was built with `+GCRYPT`, and `libgcrypt` was loaded in journald.

> **Note:** `--interval=15min` when creating the keys is the interval for changing the sealing key, not the interval for writing tags. Also, `journalctl --verify --verify-key=…` may return `PASS` even for journals not using FSS if the ordinary integrity check passes, so `PASS` alone is not evidence that FSS is working.

# Chapter 2: Why the Tags Were 0

> **Run on: VM 230**

```bash
echo "===== VM230: FSS KEY AND JOURNAL CREATION TIMELINE ====="

JDIR="/var/log/journal/b21f0e30faf4447bbe59cc1be7a0b169"
FSS="$JDIR/fss"
JOURNAL="$JDIR/system.journal"

echo
echo "--- 1. FSS key metadata (contents hidden) ---"
stat -c 'PATH=%n%nOWNER=%U:%G MODE=%a SIZE=%s%nBIRTH=%w%nMTIME=%y' "$FSS"

echo
echo "--- 2. Current journal metadata ---"
stat -c 'PATH=%n%nOWNER=%U:%G MODE=%a SIZE=%s%nBIRTH=%w%nMTIME=%y' "$JOURNAL"

echo
echo "--- 3. Journald startup time ---"
systemctl show systemd-journald.service \
  -p ActiveState -p MainPID -p ExecMainStartTimestamp

echo
echo "--- 4. FSS-related journald messages ---"
journalctl -u systemd-journald.service \
  --since "2026-11-24 00:00:00" --no-pager -o short-iso |
  grep -iE 'seal|fss|journal|key|error|fail|warning' |
  tail -n 80

echo
echo "--- 5. Effective Seal configuration ---"
systemd-analyze cat-config systemd/journald.conf |
  grep -n -i -B3 -A3 'Seal'

echo
echo "FSS_KEY_CONTENT_DISPLAYED=NO"
echo "CONFIGURATION_MODIFIED=NO"
echo "JOURNAL_FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Item | Time (UTC) |
|---|---|
| Current `system.journal` created | November 23 20:40:55 |
| FSS key file created | November 24 00:03:37 |
| journald restarted | November 24 00:50:23 |
| Current journal last updated | November 24 01:40:03 |

The current `system.journal` was **a file that existed since about 3 hours 23 minutes before the FSS keys were created**, and even after restarting journald it kept using that file. The FSS marker (`SEALED`) is set when the header of a new file is created; it is not added to an existing file afterwards. So we switch the journal to create a new file.

# Chapter 3: Switching the Journal

We archive the current journal file and switch to a new file. No logs are lost.

> **Run on: VM 230**

```bash
echo "===== VM230: APPROVED JOURNAL ROTATION AND FSS VERIFICATION ====="

JDIR="/var/log/journal/b21f0e30faf4447bbe59cc1be7a0b169"

echo
echo "--- 1. Execute approved journal rotation ---"
journalctl --rotate
ROTATE_STATUS=$?
echo "ROTATE_EXIT_STATUS=$ROTATE_STATUS"

if [ "$ROTATE_STATUS" -ne 0 ]; then
    echo "ROTATION_FAILED=YES"
    exit "$ROTATE_STATUS"
fi

echo
echo "--- 2. Current system journal header ---"
journalctl --header --file="$JDIR/system.journal"

echo
echo "--- 3. Current user journal headers ---"
for f in "$JDIR"/user-*.journal; do
    [ -f "$f" ] || continue
    echo
    echo "FILE=$f"
    journalctl --header --file="$f" |
      grep -E '^(State|Compatible flags|Incompatible flags|Objects|Tag objects|Entry objects):'
done

echo
echo "--- 4. Journal files created or archived ---"
find "$JDIR" -maxdepth 1 -type f \
  \( -name 'system*.journal' -o -name 'user-*.journal' \) \
  -printf '%TY-%Tm-%Td %TH:%TM:%TS %s %f\n' |
  sort

echo
echo "FSS_KEY_CONTENT_DISPLAYED=NO"
echo "VACUUM_OR_DELETION=NO"
echo "SERVICE_RESTARTED=NO"
```

After the switch, `system.journal` was as follows.

| Item | Result |
|---|---|
| `Compatible flags` | `SEALED SEALED_CONTINUOUS TAIL_ENTRY_BOOT_ID` |
| `Tag objects` | 7 |
| `State` | `ONLINE` |

**FSS is enabled and tags are actually being created.** The `user-1000` journal did not support FSS at this time.

# Chapter 4: Checking with the Verification Key

We check the current sealed `system.journal` with the verification key (the key contents are not displayed).

> **Run on: VM 230**

```bash
echo "===== VM230: FSS VERIFICATION OF SEALED CURRENT JOURNAL ====="

JDIR="/var/log/journal/b21f0e30faf4447bbe59cc1be7a0b169"
KEY="/root/fss-verification-key-20261124.txt"
JOURNAL="$JDIR/system.journal"

echo
echo "--- 1. Confirm current journal is FSS sealed ---"
journalctl --header --file="$JOURNAL" |
  grep -E '^(State|Compatible flags|Tag objects):'

echo
echo "--- 2. Verify current journal using FSS verification key ---"
journalctl --verify \
  --verify-key="$(cat "$KEY")" \
  --file="$JOURNAL"
VERIFY_STATUS=$?
echo "FSS_VERIFY_EXIT_STATUS=$VERIFY_STATUS"

echo
echo "FSS_KEY_CONTENT_DISPLAYED=NO"
echo "JOURNAL_FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Checked | Result |
|---|---|
| Journal state | `ONLINE` |
| `SEALED`, `SEALED_CONTINUOUS` | present |
| `Tag objects` | 7 |
| `journalctl --verify --verify-key` | `PASS` (exit code `0`) |

The output was as follows.

```text
PASS: /var/log/journal/.../system.journal
=> Validated from Tue 2026-11-24 01:43:04 UTC
   to Tue 2026-11-24 01:30:00 UTC,
   final 13min 4.084593s entries not sealed.
```

"final 13min … entries not sealed" is not a failure. It means the roughly 13 minutes of logs added after the last seal have not yet been sealed; they will be included in the next seal.

# Closing Notes

In Part 64 we started FSS sealing of VM 230's journal and checked it cryptographically.

| Item | Result |
|---|---|
| Why the tags were 0 | it kept using a journal file created before the FSS keys |
| Fix | created a new file with `journalctl --rotate` |
| Sealing | `SEALED SEALED_CONTINUOUS`, `Tag objects` 7 |
| Verification | `journalctl --verify --verify-key` gave `PASS` |

However, this verification was done inside VM 230. In case VM 230 is compromised, in the next part, Part 65, we check it **on a host other than VM 230**.

---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 61: Checking Logs for Secrets and Capping the Journal Size"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 61 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 60 we checked API error responses and log permissions. Here we do the following.

1. Check, by counts only, whether token-like strings remain in syslog and the journal
2. Examine the journal's retention period and growth, decide a size limit and set it
3. Restart journald to apply the settings, and check the integrity of the journal
4. Check log management as a whole: journald, rsyslog and logrotate

Log bodies are not displayed. Existing logs are not deleted.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: Do Secrets Remain in the Logs?

## 1.1 The Current syslog and auth.log

We count only the number of matches.

> **Run on: VM 230**

```bash
echo "===== VM230: SECRET DISCLOSURE LOG AUDIT ====="

echo
echo "--- 1. Token-like patterns (counts only) ---"
for f in /var/log/syslog /var/log/auth.log; do
  [ -f "$f" ] || continue
  printf '%s: ' "$f"
  grep -Eic \
    'Bearer[[:space:]]+[A-Za-z0-9._~+/-]{16,}|(api[_-]?key|access[_-]?token|refresh[_-]?token|secret)[[:space:]=:]+[^[:space:]]{12,}' \
    "$f" 2>/dev/null || true
done

echo
echo "--- 2. Known test marker check (counts only) ---"
for f in /var/log/syslog /var/log/auth.log; do
  [ -f "$f" ] || continue
  printf '%s: ' "$f"
  grep -Fic 'VALIDATION_SECRET_MARKER' "$f" 2>/dev/null || true
done

echo
echo "--- 3. AI Defense application log entries (counts only) ---"
for f in /var/log/syslog /var/log/auth.log; do
  [ -f "$f" ] || continue
  printf '%s: ' "$f"
  grep -Eic 'ai-defense-manager|uvicorn|fastapi' "$f" 2>/dev/null || true
done

echo
echo "LOG_CONTENT_DISPLAYED=NO"
echo "LOGS_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
```

Matches for token and secret patterns were **0**, and the test string `VALIDATION_SECRET_MARKER` also had 0. There are 14,184 AI Defense-related entries in syslog and 830 in auth.log, but that does not mean they contain secrets.

## 1.2 Rotated Logs

> **Run on: VM 230**

```bash
echo "===== VM230: ROTATED LOG SECRET DISCLOSURE AUDIT ====="

echo
echo "--- 1. Current and rotated log files ---"

find /var/log -maxdepth 1 -type f \
  \( -name 'syslog*' -o -name 'auth.log*' \) \
  -printf '%f\n' | sort

echo
echo "--- 2. Token-like pattern counts ---"

find /var/log -maxdepth 1 -type f \
  \( -name 'syslog*' -o -name 'auth.log*' \) -print0 |
while IFS= read -r -d '' f; do
  case "$f" in
    *.gz) count=$(zgrep -Eic \
      'Bearer[[:space:]]+[A-Za-z0-9._~+/-]{16,}|(api[_-]?key|access[_-]?token|refresh[_-]?token|secret)[[:space:]=:]+[^[:space:]]{12,}' \
      "$f" 2>/dev/null || true) ;;
    *) count=$(grep -Eic \
      'Bearer[[:space:]]+[A-Za-z0-9._~+/-]{16,}|(api[_-]?key|access[_-]?token|refresh[_-]?token|secret)[[:space:]=:]+[^[:space:]]{12,}' \
      "$f" 2>/dev/null || true) ;;
  esac
  printf '%s: %s\n' "$(basename "$f")" "${count:-0}"
done

echo
echo "--- 3. Known test marker counts ---"

find /var/log -maxdepth 1 -type f \
  \( -name 'syslog*' -o -name 'auth.log*' \) -print0 |
while IFS= read -r -d '' f; do
  case "$f" in
    *.gz) count=$(zgrep -Fic 'VALIDATION_SECRET_MARKER' "$f" 2>/dev/null || true) ;;
    *) count=$(grep -Fic 'VALIDATION_SECRET_MARKER' "$f" 2>/dev/null || true) ;;
  esac
  printf '%s: %s\n' "$(basename "$f")" "${count:-0}"
done

echo
echo "LOG_CONTENT_DISPLAYED=NO"
echo "LOGS_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
```

| Target | Token patterns | Test string |
|---|---:|---:|
| syslog | 0 | 0 |
| syslog.1 | 0 | 0 |
| auth.log | 0 | 0 |
| auth.log.1 | 0 | 0 |

## 1.3 The Journal

> **Run on: VM 230**

```bash
echo "===== VM230: JOURNAL SECRET AND RETENTION AUDIT ====="

echo
echo "--- 1. Journald token-like pattern count ---"
journalctl --no-pager -o cat 2>/dev/null |
  grep -Eic \
  'Bearer[[:space:]]+[A-Za-z0-9._~+/-]{16,}|(api[_-]?key|access[_-]?token|refresh[_-]?token|secret)[[:space:]=:]+[^[:space:]]{12,}' \
  || true

echo
echo "--- 2. Known test marker count ---"
journalctl --no-pager -o cat 2>/dev/null |
  grep -Fic 'VALIDATION_SECRET_MARKER' || true

echo
echo "--- 3. Journald disk usage ---"
journalctl --disk-usage

echo
echo "--- 4. Effective journald storage limits ---"
systemd-analyze cat-config systemd/journald.conf |
  grep -E '^[[:space:]]*(Storage|SystemMaxUse|SystemKeepFree|SystemMaxFileSize|SystemMaxFiles|RuntimeMaxUse|RuntimeKeepFree|RuntimeMaxFileSize|RuntimeMaxFiles|MaxRetentionSec|MaxFileSec|RateLimitIntervalSec|RateLimitBurst)[[:space:]]*=' \
  || true

echo
echo "--- 5. Journal filesystem capacity ---"
df -h /var/log/journal

echo
echo "JOURNAL_CONTENT_DISPLAYED=NO"
echo "LOGS_MODIFIED=NO"
echo "JOURNAL_VACUUMED=NO"
echo "SERVICES_RESTARTED=NO"
```

The journal also had 0 matches. It uses 89.0MB, and the file system has 39GB free (15% used). We cannot say that secrets in unknown forms, other than the patterns checked, are absent.

# Chapter 2: Journal Settings and Retention

## 2.1 The Current Settings

> **Run on: VM 230**

```bash
echo "===== VM230: JOURNALD EFFECTIVE CONFIGURATION AUDIT ====="

echo
echo "--- 1. Journald configuration files ---"
find /etc/systemd/journald.conf.d /usr/lib/systemd/journald.conf.d \
  -maxdepth 1 -type f -printf '%p\n' 2>/dev/null | sort

echo
echo "--- 2. Main configuration ---"
sed -n '1,220p' /etc/systemd/journald.conf

echo
echo "--- 3. Drop-in configurations ---"
for f in /etc/systemd/journald.conf.d/*.conf \
         /usr/lib/systemd/journald.conf.d/*.conf; do
  [ -f "$f" ] || continue
  echo "### $f"
  sed -n '1,180p' "$f"
done

echo
echo "--- 4. Compiled defaults ---"
systemd-analyze cat-config systemd/journald.conf

echo
echo "--- 5. Runtime journald properties ---"
systemctl show systemd-journald.service \
  -p ActiveState \
  -p MemoryCurrent \
  -p TasksCurrent \
  -p FragmentPath

echo
echo "READ_ONLY=YES"
echo "CONFIGURATION_MODIFIED=NO"
echo "JOURNAL_VACUUMED=NO"
echo "SERVICES_RESTARTED=NO"
```

| Setting | Now |
|---|---|
| Storage | `auto` (default) |
| Compress | `yes` (default) |
| Seal | `yes` (default) |
| SystemMaxUse | not specified |
| SystemKeepFree | not specified |
| SystemMaxFiles | default 100 |
| MaxRetentionSec | not specified |

The size limit had not been explicitly decided and was left to systemd's defaults.

## 2.2 Storage State and Integrity

> **Run on: VM 230**

```bash
echo "===== VM230: JOURNAL ARCHIVE AND STORAGE AUDIT ====="

echo
echo "--- 1. Journal storage directories ---"
stat -c '%A %U:%G %n' \
  /var/log/journal \
  /run/log/journal 2>/dev/null || true

echo
echo "--- 2. Journal files by type ---"
find /var/log/journal -type f \
  -printf '%f %s bytes %u:%g %m\n' 2>/dev/null |
  sort

echo
echo "--- 3. Active and archived journal counts ---"
find /var/log/journal -type f -name '*.journal' |
  wc -l

find /var/log/journal -type f -name '*.journal~' |
  wc -l

echo
echo "--- 4. Journal verification (read-only) ---"
journalctl --verify --no-pager 2>&1 |
  tail -30

echo
echo "--- 5. Current journal usage ---"
journalctl --disk-usage

echo
echo "READ_ONLY=YES"
echo "JOURNAL_MODIFIED=NO"
echo "VACUUM_EXECUTED=NO"
echo "SERVICES_RESTARTED=NO"
```

Persistent storage is `/var/log/journal`, with 17 files (one `.journal~` from an abnormal termination), all `root:systemd-journal`, `640`, and all files shown passed the integrity check. `Unused data (entry_offset==0)` is a notice that there is unused data, not a sign of corruption.

## 2.3 How Many Days Are Kept

> **Run on: VM 230**

```bash
echo "===== VM230: JOURNAL RETENTION PERIOD AUDIT ====="

echo
echo "--- 1. Available boot history ---"
journalctl --list-boots --no-pager

echo
echo "--- 2. Oldest journal timestamp ---"
journalctl --no-pager -o short-unix |
  head -1 | sed -E 's/^[0-9]+\.[0-9]+ /TIMESTAMP=/'

echo
echo "--- 3. Newest journal timestamp ---"
journalctl --no-pager -n 1 -o short-unix |
  sed -E 's/^[0-9]+\.[0-9]+ /TIMESTAMP=/'

echo
echo "--- 4. Journal file age and size ---"
find /var/log/journal -type f -name '*.journal*' \
  -printf '%TY-%Tm-%Td %TH:%TM:%TS %s %f\n' |
  sort

echo
echo "--- 5. Logrotate last execution timestamps ---"
grep -E '^(/var/log/(syslog|auth\.log)) ' \
  /var/lib/logrotate/status 2>/dev/null || true

echo
echo "--- 6. Current disk usage ---"
df -h /var/log/journal
journalctl --disk-usage

echo
echo "READ_ONLY=YES"
echo "LOGS_MODIFIED=NO"
echo "JOURNAL_VACUUMED=NO"
echo "CONFIGURATION_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
```

```bash
echo "===== VM230: JOURNAL TIMESTAMP AND VOLUME AUDIT ====="

echo
echo "--- 1. Oldest journal entry ---"
journalctl --no-pager -o short-iso-precise |
  head -1

echo
echo "--- 2. Newest journal entry ---"
journalctl --no-pager -n 1 -o short-iso-precise

echo
echo "--- 3. Entries per boot ---"
journalctl --list-boots --no-pager

echo
echo "--- 4. Entries by priority ---"
for p in 0 1 2 3 4 5 6 7; do
  printf "priority=%s count=" "$p"
  journalctl -p "$p" --no-pager -o cat 2>/dev/null | wc -l
done

echo
echo "--- 5. Journal size ---"
journalctl --disk-usage

echo
echo "READ_ONLY=YES"
echo "LOGS_MODIFIED=NO"
echo "JOURNAL_VACUUMED=NO"
echo "CONFIGURATION_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
```

| Item | Result |
|---|---|
| Oldest entry | 2026-11-20 07:38:48 UTC |
| Newest entry | 2026-11-23 23:10:13 UTC |
| Period | about 4 days |
| Number of entries | 46,133 |
| Boot history | 11 |
| Space used | 89MB |

# Chapter 3: Setting the Size Limit

## 3.1 Checking Before the Change

> **Run on: VM 230**

```bash
echo "===== VM230: JOURNALD CHANGE PRECHECK ====="

echo
echo "--- 1. systemd version ---"
systemd --version | head -2

echo
echo "--- 2. Journald service state ---"
systemctl show systemd-journald.service \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p Restart \
  -p FragmentPath

echo
echo "--- 3. Existing local drop-ins ---"
find /etc/systemd/journald.conf.d \
  -maxdepth 1 -type f -printf '%f\n' 2>/dev/null || true

echo
echo "--- 4. Existing local settings ---"
grep -RInE \
  '^[[:space:]]*(Storage|SystemMaxUse|SystemKeepFree|SystemMaxFileSize|MaxRetentionSec)[[:space:]]*=' \
  /etc/systemd/journald.conf \
  /etc/systemd/journald.conf.d \
  2>/dev/null || true

echo
echo "--- 5. Supported journald configuration options ---"
man journald.conf 2>/dev/null |
  col -b |
  grep -A5 -E 'SystemMaxUse=|SystemKeepFree=|SystemMaxFileSize=|MaxRetentionSec=' |
  head -50

echo
echo "READ_ONLY=YES"
echo "CONFIGURATION_MODIFIED=NO"
echo "JOURNAL_VACUUMED=NO"
echo "SERVICES_RESTARTED=NO"
```

systemd is 255.4 and supports the settings we use. There is no local drop-in and no size setting yet. `systemd-journald.service` has `Restart=always`, but restarting to apply the settings is decided separately. The values decided are as follows.

```ini
[Journal]
SystemMaxUse=512M
SystemKeepFree=2G
SystemMaxFileSize=64M
```

## 3.2 Adding the Configuration File

No deletion or change of existing logs, and no restart or reload of journald.

> **Run on: VM 230**

```bash
echo "===== VM230: APPLY JOURNALD RETENTION CONFIGURATION ====="

python3 - <<'PY'
import os
from pathlib import Path

directory = Path("/etc/systemd/journald.conf.d")
target = directory / "60-ai-defense-retention.conf"

os.makedirs(directory, mode=0o755, exist_ok=True)

content = (
    "[Journal]\n"
    "SystemMaxUse=512M\n"
    "SystemKeepFree=2G\n"
    "SystemMaxFileSize=64M\n"
)

fd = os.open(
    target,
    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
    0o644,
)

try:
    os.write(fd, content.encode())
    os.fsync(fd)
    os.fchown(fd, 0, 0)
    os.fchmod(fd, 0o644)
finally:
    os.close(fd)

dirfd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
try:
    os.fsync(dirfd)
finally:
    os.close(dirfd)

print("CONFIGURATION_CREATED=YES")
print(f"PATH={target}")
PY

echo
echo "--- 1. Configuration file ---"
stat -c '%A %U:%G %n' \
  /etc/systemd/journald.conf.d/60-ai-defense-retention.conf

cat /etc/systemd/journald.conf.d/60-ai-defense-retention.conf

echo
echo "--- 2. Effective configuration ---"
systemd-analyze cat-config systemd/journald.conf |
  grep -E '^(SystemMaxUse|SystemKeepFree|SystemMaxFileSize)=' || true

echo
echo "--- 3. Journald runtime state ---"
systemctl show systemd-journald.service \
  -p ActiveState -p SubState -p MainPID

echo
echo "CONFIGURATION_ADDED=YES"
echo "JOURNAL_VACUUMED=NO"
echo "JOURNALD_RESTARTED=NO"
echo "JOURNALD_RELOADED=NO"
```

| Setting | Effective value |
|---|---:|
| `SystemMaxUse` | 512MB |
| `SystemKeepFree` | 2GB |
| `SystemMaxFileSize` | 64MB |

The file is `/etc/systemd/journald.conf.d/60-ai-defense-retention.conf` (`root:root`, `644`). journald's PID has not changed (not yet applied to the running process).

## 3.3 Checks Before Applying

> **Run on: VM 230**

```bash
echo "===== VM230: JOURNALD CONFIGURATION PRE-APPLY AUDIT ====="

echo
echo "--- 1. Current journal usage ---"
journalctl --disk-usage

echo
echo "--- 2. Effective configuration ---"
systemd-analyze cat-config systemd/journald.conf |
  grep -E '^(SystemMaxUse|SystemKeepFree|SystemMaxFileSize)='

echo
echo "--- 3. Configuration file integrity ---"
sha256sum /etc/systemd/journald.conf.d/60-ai-defense-retention.conf
stat -c '%A %U:%G %s %n' \
  /etc/systemd/journald.conf.d/60-ai-defense-retention.conf

echo
echo "--- 4. Journald process state ---"
systemctl show systemd-journald.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts

echo
echo "CONFIGURATION_MODIFIED=NO"
echo "JOURNAL_VACUUMED=NO"
echo "SERVICES_RESTARTED=NO"
```

The current usage of 89.0MB is well below the 512MB limit, so applying it will not immediately delete old logs.

## 3.4 Restarting journald

Log collection may be affected briefly. No deletion of existing logs (vacuum) or configuration changes.

> **Run on: VM 230**

```bash
echo "===== VM230: RESTART JOURNALD TO APPLY RETENTION CONFIGURATION ====="

echo
echo "--- 1. Restart journald ---"
systemctl restart systemd-journald.service
RESTART_STATUS=$?
echo "RESTART_COMMAND_STATUS=$RESTART_STATUS"

echo
echo "--- 2. Service runtime state ---"
systemctl show systemd-journald.service \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p NRestarts \
  -p Result

echo
echo "--- 3. Effective configuration ---"
systemd-analyze cat-config systemd/journald.conf |
  grep -E '^(SystemMaxUse|SystemKeepFree|SystemMaxFileSize)='

echo
echo "--- 4. Journal availability and usage ---"
journalctl --disk-usage
journalctl -n 3 --no-pager -o short-iso

echo
echo "--- 5. Filesystem free space ---"
df -h /var/log/journal

echo
echo "CONFIGURATION_APPLY_ATTEMPTED=YES"
echo "JOURNAL_VACUUMED=NO"
```

| Item | Result |
|---|---|
| Restart | succeeded (status 0) |
| New MainPID | `2572` |
| State | `active (running)`, Result `success`, NRestarts 0 |
| Limit, free space, file limit | 512MB, 2GB, 64MB |
| Journal startup record | present |

## 3.5 Integrity After the Restart

> **Run on: VM 230**

```bash
echo "===== VM230: POST-RESTART JOURNAL INTEGRITY AUDIT ====="

echo
echo "--- 1. Journal file integrity verification ---"
journalctl --verify --no-pager 2>&1 |
  awk '
    /PASS:/ { pass++ }
    /FAIL:/ { fail++ }
    /Unused data/ { unused++ }
    END {
      print "JOURNAL_FILES_PASS=" pass
      print "JOURNAL_FILES_FAIL=" fail
      print "UNUSED_DATA_NOTICES=" unused
      if (fail > 0) print "INTEGRITY_RESULT=FAIL"
      else if (pass > 0) print "INTEGRITY_RESULT=PASS"
      else print "INTEGRITY_RESULT=UNKNOWN"
    }
  '

echo
echo "--- 2. Journald errors since restart ---"
for priority in err warning; do
  count=$(journalctl --since "2026-11-23 23:15:09 UTC" \
    -u systemd-journald.service \
    -p "$priority" --no-pager -o cat 2>/dev/null | wc -l)
  echo "JOURNALD_${priority^^}_COUNT=$count"
done

echo
echo "--- 3. Journald runtime state ---"
systemctl show systemd-journald.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p Result

echo
echo "--- 4. AI Defense Manager service state ---"
systemctl show ai-defense-manager.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p Result

echo
echo "--- 5. Local health endpoint ---"
curl --silent --show-error \
  --max-time 5 \
  --output /dev/null \
  --write-out 'HEALTH_HTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "--- 6. Current journal usage ---"
journalctl --disk-usage

echo
echo "CONFIGURATION_MODIFIED=NO"
echo "JOURNAL_VACUUMED=NO"
echo "SERVICES_RESTARTED=NO"
echo "PRODUCTION_DATABASE_ACCESSED=NO"
echo "WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
```

| Checked | Result |
|---|---:|
| Journal files passing the check | 18 |
| Journal files failing the check | 0 |
| `Unused data` notices | 31 |
| journald errors and warnings | 0 |
| AI Defense Manager | `active (running)`, 0 restarts, `/health` `HTTP 200` |

# Chapter 4: Log Management as a Whole

## 4.1 Storage Locations and logrotate

> **Run on: VM 230**

```bash
echo "===== VM230: JOURNAL STORAGE AND LOGROTATE AUDIT ====="

echo
echo "--- 1. Journal directory permissions ---"
stat -c '%A %a %U:%G %n' \
  /var/log/journal \
  /run/log/journal

echo
echo "--- 2. Journal files: ownership, permissions and sizes ---"
find /var/log/journal \
  -type f \
  -printf '%M %u:%g %s %p\n' |
  sort

echo
echo "--- 3. Active and archived journal files ---"
find /var/log/journal \
  -type f \
  \( -name '*.journal' -o -name '*.journal~' \) \
  -printf '%f\n' |
  sort

echo
echo "--- 4. Journald storage and retention settings ---"
systemd-analyze cat-config systemd/journald.conf |
  grep -E '^[[:space:]]*(Storage|SystemMaxUse|SystemKeepFree|SystemMaxFileSize|SystemMaxFiles|MaxRetentionSec|MaxFileSec)=' ||
  true

echo
echo "--- 5. Logrotate journald-related configuration references ---"
grep -RInE \
  '(/var/log/journal|systemd-journald|journalctl|journal.*rotate)' \
  /etc/logrotate.conf \
  /etc/logrotate.d \
  2>/dev/null || true

echo
echo "--- 6. Journald capacity-related messages ---"
journalctl -u systemd-journald.service \
  --since "2026-11-23 23:15:09 UTC" \
  --no-pager -o cat |
  grep -Ei 'max|limit|space|vacuum|rotation|journal started' |
  tail -30

echo
echo "--- 7. Current journal usage and filesystem ---"
journalctl --disk-usage
df -h /var/log/journal

echo
echo "CONFIGURATION_MODIFIED=NO"
echo "JOURNAL_FILES_MODIFIED=NO"
echo "LOGROTATE_EXECUTED=NO"
echo "JOURNAL_VACUUMED=NO"
echo "SERVICES_RESTARTED=NO"
```

`/var/log/journal` and `/run/log/journal` are `root:systemd-journal`, `2755`, journal files are `640`, and there was no logrotate setting that touches the journal directly.

## 4.2 Size and Retention Period

> **Run on: VM 230**

```bash
echo "===== VM230: JOURNAL RETENTION CAPACITY AUDIT ====="

echo
echo "--- 1. Journal file time ranges ---"
journalctl --file=/var/log/journal/b21f0e30faf4447bbe59cc1be7a0b169/system.journal \
  --no-pager -o short-iso -n 1

echo
echo "--- 2. Overall journal time range ---"
journalctl --no-pager -o short-iso --reverse -n 1
journalctl --no-pager -o short-iso -n 1

echo
echo "--- 3. Journal file inventory count ---"
find /var/log/journal -type f -name '*.journal*' | wc -l

echo
echo "--- 4. Filesystem inode capacity ---"
df -i /var/log/journal

echo
echo "--- 5. Journal retention settings ---"
systemd-analyze cat-config systemd/journald.conf |
  grep -E '^[[:space:]]*(SystemMaxUse|SystemKeepFree|SystemMaxFileSize|SystemMaxFiles|MaxRetentionSec|MaxFileSec)=' ||
  true

echo
echo "--- 6. Current journal usage ---"
journalctl --disk-usage

echo
echo "CONFIGURATION_MODIFIED=NO"
echo "JOURNAL_FILES_MODIFIED=NO"
echo "JOURNAL_VACUUMED=NO"
echo "SERVICES_RESTARTED=NO"
```

```bash
echo "===== VM230: JOURNAL GLOBAL TIME RANGE VERIFICATION ====="

echo
echo "--- 1. Earliest journal timestamp ---"
journalctl --no-pager -o short-iso |
  head -1

echo
echo "--- 2. Latest journal timestamp ---"
journalctl --no-pager -o short-iso |
  tail -1

echo
echo "--- 3. Boot history ---"
journalctl --list-boots --no-pager

echo
echo "--- 4. Journal file verification summary ---"
journalctl --verify --no-pager 2>&1 |
  awk '
    /PASS:/ { pass++ }
    /FAIL:/ { fail++ }
    /Unused data/ { unused++ }
    END {
      print "PASS=" pass
      print "FAIL=" fail
      print "UNUSED_DATA_NOTICES=" unused
    }
  '

echo
echo "--- 5. Current journald state ---"
systemctl show systemd-journald.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts

echo
echo "CONFIGURATION_MODIFIED=NO"
echo "JOURNAL_FILES_MODIFIED=NO"
echo "JOURNAL_VACUUMED=NO"
echo "SERVICES_RESTARTED=NO"
```

| Item | Result |
|---|---|
| Oldest entry | 2026-11-20 07:38:48 UTC |
| Newest entry | 2026-11-23 23:17:01 UTC |
| Period | about 3 days 15 hours 38 minutes |
| Free disk space | 39GB |
| inode usage | 4% |

## 4.3 logrotate

> **Run on: VM 230**

```bash
echo "===== VM230: LOG MANAGEMENT CROSS-SYSTEM AUDIT ====="

echo
echo "--- 1. Global logrotate configuration ---"
sed -n '1,200p' /etc/logrotate.conf

echo
echo "--- 2. Rsyslog rotation configuration ---"
sed -n '1,200p' /etc/logrotate.d/rsyslog

echo
echo "--- 3. Logrotate configuration inventory ---"
find /etc/logrotate.d \
  -maxdepth 1 -type f \
  -printf '%M %u:%g %s %f\n' |
  sort

echo
echo "--- 4. Logrotate timer and service ---"
systemctl show logrotate.timer \
  -p ActiveState -p SubState -p NextElapseUSecRealtime -p LastTriggerUSec

systemctl show logrotate.service \
  -p ActiveState -p SubState -p Result -p ExecMainStatus

echo
echo "--- 5. Logrotate execution history ---"
journalctl -u logrotate.service \
  --no-pager -n 15 -o short-iso

echo
echo "--- 6. Logrotate state file metadata ---"
stat -c '%A %a %U:%G %s %n' /var/lib/logrotate/status

echo
echo "--- 7. Current syslog and auth.log files ---"
find /var/log \
  -maxdepth 1 \
  -type f \
  \( -name 'syslog*' -o -name 'auth.log*' \) \
  -printf '%M %u:%g %s %f\n' |
  sort

echo
echo "--- 8. Filesystem usage ---"
df -h /var/log
df -i /var/log

echo
echo "LOGROTATE_EXECUTED=NO"
echo "CONFIGURATION_MODIFIED=NO"
echo "LOG_FILES_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
```

```bash
echo "===== VM230: LOGROTATE STATIC VALIDATION ====="

echo
echo "--- 1. Logrotate version ---"
logrotate --version

echo
echo "--- 2. Configuration syntax validation (debug mode) ---"
logrotate --debug /etc/logrotate.conf 2>&1 |
  tail -80

echo
echo "--- 3. Rsyslog log rotation ownership ---"
stat -c '%A %a %U:%G %n' \
  /var/log/syslog \
  /var/log/syslog.1 \
  /var/log/auth.log \
  /var/log/auth.log.1

echo
echo "--- 4. Rotation state for syslog and auth.log ---"
grep -E '/var/log/(syslog|auth.log)' \
  /var/lib/logrotate/status || true

echo
echo "--- 5. Duplicate rotation definitions ---"
grep -RInE \
  '/var/log/(syslog|auth.log)' \
  /etc/logrotate.conf \
  /etc/logrotate.d \
  2>/dev/null || true

echo
echo "LOGROTATE_EXECUTED=NO"
echo "LOG_FILES_MODIFIED=NO"
echo "STATE_FILE_MODIFIED=NO"
echo "CONFIGURATION_MODIFIED=NO"
```

| Item | Result |
|---|---|
| logrotate | 3.21.0 |
| Cycle and generations | weekly, 4 generations |
| Compression | gzip, `delaycompress` |
| Empty logs | not rotated |
| rsyslog targets | 6 kinds; rsyslog notified in postrotate |
| Duplicate definitions | none |
| Log owner and permissions | `syslog:adm`, `640` |

## 4.4 rsyslog

> **Run on: VM 230**

```bash
echo "===== VM230: RSYSLOG RUNTIME HEALTH AUDIT ====="

echo
echo "--- 1. Rsyslog service state ---"
systemctl show rsyslog.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p Result

echo
echo "--- 2. Rsyslog process identity ---"
ps -o pid,ppid,user,group,comm -C rsyslogd

echo
echo "--- 3. Rsyslog configuration validation ---"
rsyslogd -N1

echo
echo "--- 4. Journald forwarding configuration ---"
systemd-analyze cat-config systemd/journald.conf |
  grep -E '^[[:space:]]*ForwardToSyslog=' || true

echo
echo "--- 5. Rsyslog routing configuration ---"
grep -RInE \
  'auth,authpriv|syslog|/var/log/auth.log|ForwardToSyslog' \
  /etc/rsyslog.conf /etc/rsyslog.d \
  2>/dev/null || true

echo
echo "--- 6. Recent rsyslog service errors ---"
journalctl -u rsyslog.service \
  -p err --since "2026-11-20 00:00:00 UTC" \
  --no-pager -o short-iso

echo
echo "--- 7. Recent log file modification times ---"
stat -c '%y %s %n' \
  /var/log/syslog /var/log/auth.log

echo
echo "LOG_FILES_MODIFIED=NO"
echo "RSYSLOG_RESTARTED=NO"
echo "CONFIGURATION_MODIFIED=NO"
```

rsyslog was `active (running)` (MainPID `774`, 0 restarts, user `syslog`), the `rsyslogd -N1` syntax check passed, forwarding from journald (`ForwardToSyslog=yes`) and the split between auth.log and syslog were normal, and there were no errors.

# Closing Notes

In Part 61 we confirmed that no secrets remain in the logs and set a size limit for the journal.

| Item | Result |
|---|---|
| Checking logs for secrets | 0 matches in syslog, auth.log and the journal |
| Journal limits | `SystemMaxUse=512M`, `SystemKeepFree=2G`, `SystemMaxFileSize=64M` (`60-ai-defense-retention.conf`) |
| Applying | journald restarted; integrity check: 18 passed, 0 failed |
| syslog | weekly, 4 generations, compressed, `syslog:adm`, `640` |

The journald settings showed `Seal=yes` (default), but whether a sealing key is actually in use is checked in the next part, Part 62. This is to make log tampering detectable.

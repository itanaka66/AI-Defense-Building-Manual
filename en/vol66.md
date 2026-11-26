---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 66: Automating FSS Verification Every 15 Minutes"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 66 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 65 we checked the FSS-sealed journal on another host. Here we make VM 230 run FSS verification **automatically every 15 minutes**.

1. Examine the structure of the existing AI Defense Manager and decide where to integrate verification
2. Use the headers to decide which journals are verification targets
3. Create the verification script, a systemd service and a timer, and run it once by hand
4. Enable the timer and confirm that it ran automatically
5. Investigate whether verification results can be reported to Wazuh

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root. When logged in as `aidefense`, become root with `sudo -i`)

# Chapter 1: Deciding Where to Integrate

## 1.1 Service Structure

> **Run on: VM 230**

```bash
echo "===== VM230: AI DEFENSE MANAGER READ-ONLY ARCHITECTURE DISCOVERY ====="

SERVICE="ai-defense-manager.service"

echo
echo "--- 1. Service runtime properties ---"
systemctl show "$SERVICE" \
  -p LoadState \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p User \
  -p Group \
  -p WorkingDirectory \
  -p FragmentPath \
  -p DropInPaths \
  -p ExecStart \
  -p NRestarts

echo
echo "--- 2. Process identity ---"
PID="$(systemctl show "$SERVICE" -p MainPID --value)"
if [ "$PID" -gt 0 ] 2>/dev/null; then
    ps -o pid,ppid,user,group,lstart,comm -p "$PID"
else
    echo "SERVICE_MAIN_PROCESS_NOT_RUNNING"
fi

echo
echo "--- 3. Listening TCP sockets ---"
ss -ltnp | grep -E '(:8000|:8765|State)' || true

echo
echo "--- 4. Relevant systemd timers ---"
systemctl list-timers --all --no-pager |
  grep -Ei 'NEXT|ai-defense|journal|fss|audit|security' || true

echo
echo "--- 5. FSS-related file metadata ---"
find /root /var/log/journal \
  -maxdepth 3 \
  -type f \
  \( -iname '*fss*' -o -iname '*journal*verify*' \) \
  -printf '%u:%g %m %s %p\n' 2>/dev/null |
  head -n 60

echo
echo "DISCOVERY_MODE=READ_ONLY"
echo "SERVICE_RESTARTED=NO"
echo "CONFIGURATION_MODIFIED=NO"
echo "SECRET_CONTENT_DISPLAYED=NO"
```

The AI Defense Manager is running (0 restarts), FastAPI listens only on `127.0.0.1:8000`, and there was no FSS-related systemd timer.

## 1.2 Application Structure

Run as root (as `aidefense`, `app`, `config`, `data` and so on cannot be read).

> **Run on: VM 230**

```bash
echo "===== VM230: PRIVILEGED READ-ONLY APPLICATION DISCOVERY ====="

sudo bash <<'ROOT'
APP="/opt/ai-defense-manager"

echo
echo "--- 1. Effective execution identity ---"
id

echo
echo "--- 2. Application directory permissions ---"
namei -l "$APP"
stat -c 'OWNER=%U:%G MODE=%a PATH=%n' \
  "$APP" "$APP/app" "$APP/config" "$APP/data" "$APP/logs" "$APP/tests"

echo
echo "--- 3. Application directory structure ---"
find "$APP" -maxdepth 2 -type d \
  ! -path '*/venv*' \
  ! -path '*/.git*' \
  -printf '%p\n' | sort | head -n 100

echo
echo "--- 4. Application source file names ---"
find "$APP" -maxdepth 3 -type f \
  ! -path '*/venv/*' \
  ! -path '*/.git/*' \
  ! -path '*/__pycache__/*' \
  ! -name '.env' \
  ! -name '*.db' \
  ! -name '*.sqlite*' \
  -printf '%p\n' | sort | head -n 160

echo
echo "--- 5. Audit and scheduler related source file paths ---"
grep -RIlE \
  'journalctl|systemd|scheduler|BackgroundTasks|APScheduler|audit|integrity|verification|security_event|asyncio\.create_task' \
  "$APP" \
  --include='*.py' \
  --exclude-dir=venv \
  --exclude-dir=.git \
  --exclude-dir=__pycache__ \
  2>/dev/null | head -n 100

echo
echo "SOURCE_CONTENT_DISPLAYED=NO"
echo "DATABASE_CONTENT_DISPLAYED=NO"
echo "SECRETS_DISPLAYED=NO"
echo "FILES_MODIFIED=NO"
ROOT
```

`app/services/` contained services such as Wazuh integration and analysis history, and `app/api/` had the Wazuh and analysis APIs, but there was no scheduler or FSS verification module.

## 1.3 Service Security Settings

> **Run on: VM 230**

```bash
echo "===== VM230: SERVICE SECURITY AND MODULE INTERFACE AUDIT ====="

APP="/opt/ai-defense-manager"

echo
echo "--- 1. Existing service security properties ---"
systemctl show ai-defense-manager.service \
  -p User \
  -p Group \
  -p NoNewPrivileges \
  -p ProtectSystem \
  -p ProtectHome \
  -p PrivateTmp \
  -p PrivateDevices \
  -p CapabilityBoundingSet \
  -p ReadOnlyPaths \
  -p ReadWritePaths \
  -p RestrictAddressFamilies \
  -p IPAddressDeny \
  -p DynamicUser \
  -p UMask

echo
echo "--- 2. Application module interfaces (definitions only) ---"
for f in \
  "$APP/app/main.py" \
  "$APP/app/services/analysis_history.py" \
  "$APP/app/services/wazuh_relay.py" \
  "$APP/app/api/wazuh.py" \
  "$APP/app/api/analysis.py"; do
    if [ -f "$f" ]; then
        echo
        echo "FILE=$f"
        grep -nE '^(async[[:space:]]+)?def[[:space:]]|^class[[:space:]]' "$f" |
          head -n 100 || true
    fi
done

echo
echo "--- 3. Service and application file ownership ---"
stat -c 'OWNER=%U:%G MODE=%a PATH=%n' \
  "$APP/app" \
  "$APP/app/main.py" \
  "$APP/app/services" \
  "$APP/app/services/analysis_history.py" \
  "$APP/app/services/wazuh_relay.py" \
  /etc/systemd/system/ai-defense-manager.service

echo
echo "SOURCE_CODE_CONTENT_DISPLAYED=NO"
echo "DATABASE_ACCESSED=NO"
echo "SERVICE_STATE_CHANGED=NO"
echo "FILES_MODIFIED=NO"
```

The existing API is strongly isolated with `ProtectSystem=strict`, `ProtectHome=yes` and `RestrictAddressFamilies=AF_INET`. The FSS verification key and the journal are root-only, so we do not add permissions to the `ai-defense` user. Therefore, rather than integrating it into the existing FastAPI service, we use **a separate verification service that only reads, running as root, and a systemd timer**.

# Chapter 2: Deciding the Verification Targets

## 2.1 Journal Files

> **Run on: VM 230**

```bash
echo "===== VM230: FSS AUTOMATION TARGET DISCOVERY ====="

JDIR="/var/log/journal/b21f0e30faf4447bbe59cc1be7a0b169"

echo
echo "--- 1. Journal directory metadata ---"
stat -c 'OWNER=%U:%G MODE=%a PATH=%n' "$JDIR"

echo
echo "--- 2. Archived system journal inventory ---"
find "$JDIR" -maxdepth 1 -type f \
  -name 'system@*.journal' \
  -printf 'OWNER=%u:%g MODE=%m SIZE=%s FILE=%f\n' |
  sort

echo
echo "--- 3. Current system journal metadata ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s PATH=%n' \
  "$JDIR/system.journal"

echo
echo "--- 4. Existing systemd timer inventory ---"
systemctl list-timers --all --no-pager

echo
echo "--- 5. Existing custom systemd unit inventory ---"
systemctl list-unit-files --type=service --no-pager |
  grep -Ei 'ai-defense|fss|journal|audit' || true

echo
echo "JOURNAL_CONTENT_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
echo "DATABASE_ACCESSED=NO"
echo "SECRETS_DISPLAYED=NO"
```

There were 14 archived system journals and the current journal.

## 2.2 Sorting by Header

> **Run on: VM 230**

```bash
echo "===== VM230: ALL JOURNAL ARCHIVE FSS HEADER CLASSIFICATION ====="

JDIR="/var/log/journal/b21f0e30faf4447bbe59cc1be7a0b169"

inspect_journal() {
    FILE="$1"
    HEADER="$(journalctl --header --file="$FILE" 2>&1)"
    STATE="$(printf '%s\n' "$HEADER" | awk -F': ' '/^State:/ {print $2; exit}')"
    FLAGS="$(printf '%s\n' "$HEADER" | awk -F': ' '/^Compatible flags:/ {print $2; exit}')"
    TAGS="$(printf '%s\n' "$HEADER" | awk -F': ' '/^Tag objects:/ {print $2; exit}')"

    printf 'FILE=%s\n' "$(basename "$FILE")"
    printf 'STATE=%s\n' "${STATE:-UNKNOWN}"
    printf 'FLAGS=%s\n' "${FLAGS:-UNKNOWN}"
    printf 'TAG_OBJECTS=%s\n' "${TAGS:-UNKNOWN}"
    echo
}

echo
echo "--- 1. Archived system journals ---"
while IFS= read -r -d '' FILE; do
    inspect_journal "$FILE"
done < <(find "$JDIR" -maxdepth 1 -type f -name 'system@*.journal' -print0 | sort -z)

echo "--- 2. Current system journal ---"
inspect_journal "$JDIR/system.journal"

echo "HEADER_CLASSIFICATION_ONLY=YES"
echo "JOURNAL_CONTENT_READ=NO"
echo "FILES_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
echo "KEY_CONTENT_DISPLAYED=NO"
```

| Category | Count | Automatic handling |
|---|---:|---|
| FSS-sealed archive | 1 | check cryptographically |
| Old archives from before FSS | 13 | record as out of scope (`SKIP`) |
| Current system journal | 1 | check cryptographically |

Old archives (`Tag objects` 0) can give `PASS` with `--verify-key` through the ordinary integrity check, so we treat them as neither "verification failure" nor "FSS pass", but as `SKIP`.

## 2.3 Checking the Current Journal as a Baseline

> **Run on: VM 230**

```bash
echo "===== VM230: CURRENT SYSTEM JOURNAL FSS CRYPTOGRAPHIC BASELINE ====="

JDIR="/var/log/journal/b21f0e30faf4447bbe59cc1be7a0b169"
CURRENT="$JDIR/system.journal"
KEY="/root/fss-verification-key-20261124.txt"

echo
echo "--- 1. Confirm current journal FSS header ---"
journalctl --header --file="$CURRENT" |
  grep -E '^(State|Compatible flags|Tag objects):'

echo
echo "--- 2. Verify current journal with FSS key ---"
journalctl --verify \
  --verify-key="$(cat "$KEY")" \
  --file="$CURRENT"
VERIFY_STATUS=$?

echo
echo "CURRENT_JOURNAL_VERIFY_EXIT_STATUS=$VERIFY_STATUS"

if [ "$VERIFY_STATUS" -eq 0 ]; then
    echo "CURRENT_JOURNAL_FSS_BASELINE=PASS"
else
    echo "CURRENT_JOURNAL_FSS_BASELINE=FAIL"
fi

echo
echo "CURRENT_JOURNAL_MODIFIED=NO"
echo "JOURNAL_ROTATED=NO"
echo "SERVICES_RESTARTED=NO"
echo "KEY_CONTENT_DISPLAYED=NO"

exit "$VERIFY_STATUS"
```

The current journal was `ONLINE`, `SEALED`, `SEALED_CONTINUOUS`, `Tag objects` 8, and verification gave `PASS` (exit code `0`). "final 5min … entries not sealed" is the last, not-yet-sealed part of an active journal and is normal.

# Chapter 3: Building the Verification Mechanism

## 3.1 Creating Three Files

| File | Content |
|---|---|
| `/usr/local/sbin/ai-defense-fss-verify` | verification script (`root:root`, `0750`) |
| `/etc/systemd/system/ai-defense-fss-verify.service` | oneshot service, read-only sandbox (`0644`) |
| `/etc/systemd/system/ai-defense-fss-verify.timer` | 5 minutes after boot, then every 15 minutes (`0644`) |

Targets are limited to system journals whose headers have `SEALED` and `SEALED_CONTINUOUS` and whose `Tag objects` is 1 or more. If a file already exists at the same path, it stops without overwriting. At this stage there is no `daemon-reload`, no service run and no timer enabling.

> **Run on: VM 230**

```bash
set -euo pipefail

echo "===== VM230: CREATE FSS VERIFICATION FILES ====="

SCRIPT="/usr/local/sbin/ai-defense-fss-verify"
SERVICE="/etc/systemd/system/ai-defense-fss-verify.service"
TIMER="/etc/systemd/system/ai-defense-fss-verify.timer"
JDIR="/var/log/journal/b21f0e30faf4447bbe59cc1be7a0b169"
KEY="/root/fss-verification-key-20261124.txt"

echo "--- 1. Preflight ---"
test "$(id -u)" -eq 0
test -d "$JDIR"
test -r "$KEY"
test -x /usr/bin/journalctl
test ! -e "$SCRIPT"
test ! -e "$SERVICE"
test ! -e "$TIMER"

echo "PREFLIGHT=PASS"
echo "TARGET_FILES_ABSENT=YES"
echo "VERIFICATION_KEY_READABLE=YES"

echo
echo "--- 2. Create verification script ---"
install -d -o root -g root -m 0755 /usr/local/sbin

cat > "$SCRIPT" <<'SCRIPT_EOF'
#!/usr/bin/env bash
set -uo pipefail

JDIR="/var/log/journal/b21f0e30faf4447bbe59cc1be7a0b169"
KEY_FILE="/root/fss-verification-key-20261124.txt"

PASS_COUNT=0
SKIP_COUNT=0
FAIL_COUNT=0

echo "FSS_VERIFICATION_START=$(date --iso-8601=seconds)"
echo "FSS_VERIFICATION_SCOPE=SYSTEM_JOURNALS_ONLY"

if [[ ! -r "$KEY_FILE" || ! -s "$KEY_FILE" ]]; then
    echo "FATAL=VERIFICATION_KEY_UNAVAILABLE"
    exit 2
fi

if [[ ! -d "$JDIR" ]]; then
    echo "FATAL=JOURNAL_DIRECTORY_UNAVAILABLE"
    exit 2
fi

VERIFY_KEY="$(<"$KEY_FILE")"
if [[ -z "$VERIFY_KEY" ]]; then
    echo "FATAL=VERIFICATION_KEY_EMPTY"
    exit 2
fi

inspect_and_verify() {
    local file="$1"
    local header state flags tags verify_status

    echo
    echo "FILE=$(basename "$file")"

    if ! header="$(/usr/bin/journalctl --header --file="$file" 2>&1)"; then
        echo "RESULT=HEADER_ERROR"
        echo "DETAIL=Unable to read journal header"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return
    fi

    state="$(printf '%s\n' "$header" | awk -F': ' '/^State:/ {print $2; exit}')"
    flags="$(printf '%s\n' "$header" | awk -F': ' '/^Compatible flags:/ {print $2; exit}')"
    tags="$(printf '%s\n' "$header" | awk -F': ' '/^Tag objects:/ {print $2; exit}')"

    echo "STATE=${state:-UNKNOWN}"
    echo "FLAGS=${flags:-UNKNOWN}"
    echo "TAG_OBJECTS=${tags:-UNKNOWN}"

    if [[ ! "$tags" =~ ^[0-9]+$ ]]; then
        echo "RESULT=HEADER_ERROR"
        echo "DETAIL=Invalid Tag objects field"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return
    fi

    if [[ " $flags " != *" SEALED "* ||
          " $flags " != *" SEALED_CONTINUOUS "* ||
          "$tags" -eq 0 ]]; then
        echo "RESULT=SKIP_LEGACY_UNSEALED"
        SKIP_COUNT=$((SKIP_COUNT + 1))
        return
    fi

    echo "CRYPTOGRAPHIC_VERIFICATION=START"

    if /usr/bin/journalctl --verify \
        --verify-key="$VERIFY_KEY" \
        --file="$file"; then
        echo "RESULT=VERIFY_PASS"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        verify_status=$?
        echo "RESULT=VERIFY_FAIL"
        echo "VERIFY_EXIT_STATUS=$verify_status"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

while IFS= read -r -d '' file; do
    inspect_and_verify "$file"
done < <(find "$JDIR" -maxdepth 1 -type f -name 'system@*.journal' -print0 | sort -z)

inspect_and_verify "$JDIR/system.journal"

echo
echo "===== FSS VERIFICATION SUMMARY ====="
echo "VERIFY_PASS_COUNT=$PASS_COUNT"
echo "SKIP_LEGACY_COUNT=$SKIP_COUNT"
echo "VERIFY_FAIL_COUNT=$FAIL_COUNT"
echo "FSS_VERIFICATION_END=$(date --iso-8601=seconds)"

if [[ "$FAIL_COUNT" -gt 0 ]]; then
    echo "FSS_VERIFICATION_STATUS=FAIL"
    exit 1
fi

echo "FSS_VERIFICATION_STATUS=PASS"
exit 0
SCRIPT_EOF

chown root:root "$SCRIPT"
chmod 0750 "$SCRIPT"

echo "SCRIPT_CREATED=YES"

echo
echo "--- 3. Create systemd service unit ---"
cat > "$SERVICE" <<'SERVICE_EOF'
[Unit]
Description=AI Defense FSS Journal Cryptographic Verification
Documentation=man:journalctl(1)
After=local-fs.target

[Service]
Type=oneshot
User=root
Group=root
ExecStart=/usr/local/sbin/ai-defense-fss-verify
TimeoutStartSec=5min
UMask=0077

NoNewPrivileges=yes
PrivateTmp=yes
PrivateDevices=yes
PrivateNetwork=yes
ProtectSystem=strict
ProtectHome=read-only
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
LockPersonality=yes
MemoryDenyWriteExecute=yes
RestrictSUIDSGID=yes
CapabilityBoundingSet=
SERVICE_EOF

chown root:root "$SERVICE"
chmod 0644 "$SERVICE"

echo "SERVICE_UNIT_CREATED=YES"

echo
echo "--- 4. Create systemd timer unit ---"
cat > "$TIMER" <<'TIMER_EOF'
[Unit]
Description=Periodic AI Defense FSS Journal Verification

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min
AccuracySec=1min
Unit=ai-defense-fss-verify.service

[Install]
WantedBy=timers.target
TIMER_EOF

chown root:root "$TIMER"
chmod 0644 "$TIMER"

echo "TIMER_UNIT_CREATED=YES"

echo
echo "--- 5. File metadata audit ---"
stat -c '%A %U:%G %s %n' "$SCRIPT" "$SERVICE" "$TIMER"

echo
echo "FILES_CREATED=3"
echo "SYSTEMD_DAEMON_RELOAD=NOT_PERFORMED"
echo "TIMER_ENABLED=NO"
echo "SERVICE_STARTED=NO"
echo "PRODUCTION_SERVICE_RESTARTED=NO"
echo "VERIFICATION_KEY_CONTENT_DISPLAYED=NO"
```

> **Caution:** If this script is not run as root, it stops at the first check (the three files are not created). When logged in as `aidefense`, become root with the following before running it.

```bash
sudo -i
```

## 3.2 Static Checks

> **Run on: VM 230**

```bash
echo "===== VM230: FSS VERIFIER STATIC SECURITY AUDIT ====="

SCRIPT="/usr/local/sbin/ai-defense-fss-verify"
SERVICE="/etc/systemd/system/ai-defense-fss-verify.service"
TIMER="/etc/systemd/system/ai-defense-fss-verify.timer"

echo
echo "--- 1. Verification script source ---"
nl -ba "$SCRIPT"

echo
echo "--- 2. Shell syntax validation ---"
bash -n "$SCRIPT"
echo "SCRIPT_SYNTAX_STATUS=$?"

echo
echo "--- 3. systemd unit syntax validation ---"
systemd-analyze verify "$SERVICE" "$TIMER"
echo "SYSTEMD_UNIT_VERIFY_STATUS=$?"

echo
echo "--- 4. File ownership and permissions ---"
stat -c '%A %a %U:%G %n' "$SCRIPT" "$SERVICE" "$TIMER" \
  /root/fss-verification-key-20261124.txt \
  /var/log/journal/b21f0e30faf4447bbe59cc1be7a0b169

echo
echo "--- 5. Timer and service runtime state ---"
systemctl is-enabled ai-defense-fss-verify.timer 2>&1 || true
systemctl is-active ai-defense-fss-verify.timer 2>&1 || true
systemctl is-active ai-defense-fss-verify.service 2>&1 || true

echo
echo "STATIC_AUDIT_ONLY=YES"
echo "VERIFICATION_SCRIPT_EXECUTED=NO"
echo "SYSTEMD_DAEMON_RELOAD=NO"
echo "FILES_MODIFIED=NO"
echo "KEY_CONTENT_DISPLAYED=NO"
```

| Check | Result |
|---|---|
| Bash syntax | passed |
| systemd unit syntax | passed |
| File owner and permissions | passed |
| Verification key readable only by root | passed |
| Timer, service | `disabled`, `inactive` / `inactive` |
| Changes to existing services | none |

The value passed to `--verify-key` is the verification key, which may be public, not the secret sealing key. However, the verification key may appear in process arguments.

## 3.3 Registering and Running It Once by Hand

The timer is not enabled.

> **Run on: VM 230**

```bash
echo "===== VM230: REGISTER AND MANUAL FSS VERIFICATION TEST ====="

echo
echo "--- 1. Register systemd unit definitions ---"
systemctl daemon-reload
DAEMON_RELOAD_STATUS=$?
echo "DAEMON_RELOAD_EXIT_STATUS=$DAEMON_RELOAD_STATUS"

if [ "$DAEMON_RELOAD_STATUS" -ne 0 ]; then
    echo "SYSTEMD_REGISTRATION=FAIL"
    exit "$DAEMON_RELOAD_STATUS"
fi

echo
echo "--- 2. Confirm unit definitions are recognized ---"
systemctl show ai-defense-fss-verify.service \
  -p LoadState -p FragmentPath -p User -p ProtectSystem -p ProtectHome

systemctl show ai-defense-fss-verify.timer \
  -p LoadState -p FragmentPath -p Unit -p ActiveState

echo
echo "--- 3. Run verification service once ---"
systemctl start ai-defense-fss-verify.service
SERVICE_START_STATUS=$?
echo "SERVICE_START_COMMAND_EXIT_STATUS=$SERVICE_START_STATUS"

echo
echo "--- 4. Service execution result ---"
systemctl show ai-defense-fss-verify.service \
  -p ActiveState -p SubState -p Result -p ExecMainCode -p ExecMainStatus

echo
echo "--- 5. Verification journal output ---"
journalctl -u ai-defense-fss-verify.service \
  --no-pager -o cat -n 100

echo
echo "--- 6. Confirm timer remains disabled and inactive ---"
systemctl is-enabled ai-defense-fss-verify.timer 2>&1 || true
systemctl is-active ai-defense-fss-verify.timer 2>&1 || true

echo
echo "TIMER_ENABLE_REQUESTED=NO"
echo "TIMER_START_REQUESTED=NO"
echo "AI_DEFENSE_MANAGER_RESTARTED=NO"
echo "VERIFICATION_KEY_CONTENT_DISPLAYED=NO"
```

| Result | Count |
|---|---:|
| Cryptographic verification `PASS` | 2 (sealed archive, current journal) |
| Old archives `SKIP` | 13 |
| Verification failures | 0 |

The service exited with code `0`, and systemd's result was `success`. From inside the systemd sandbox, it can read the root-only key and journal and verify them.

# Chapter 4: Enabling the Timer

## 4.1 Enabling

> **Run on: VM 230**

```bash
echo "===== VM230: ENABLE PERIODIC FSS VERIFICATION TIMER ====="

echo
echo "--- 1. Enable timer ---"
systemctl enable ai-defense-fss-verify.timer
ENABLE_STATUS=$?
echo "TIMER_ENABLE_EXIT_STATUS=$ENABLE_STATUS"

if [ "$ENABLE_STATUS" -ne 0 ]; then
    exit "$ENABLE_STATUS"
fi

echo
echo "--- 2. Start timer ---"
systemctl start ai-defense-fss-verify.timer
START_STATUS=$?
echo "TIMER_START_EXIT_STATUS=$START_STATUS"

if [ "$START_STATUS" -ne 0 ]; then
    exit "$START_STATUS"
fi

echo
echo "--- 3. Timer status ---"
systemctl status ai-defense-fss-verify.timer --no-pager

echo
echo "--- 4. Scheduled execution ---"
systemctl list-timers ai-defense-fss-verify.timer --all --no-pager

echo
echo "--- 5. Enabled and active state ---"
systemctl is-enabled ai-defense-fss-verify.timer
systemctl is-active ai-defense-fss-verify.timer

echo
echo "--- 6. Existing AI Defense Manager health ---"
systemctl show ai-defense-manager.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts

echo
echo "FSS_TIMER_ENABLED=YES"
echo "FSS_TIMER_STARTED=YES"
echo "AI_DEFENSE_MANAGER_RESTARTED=NO"
echo "VERIFICATION_KEY_CONTENT_DISPLAYED=NO"
```

Inside, it does the following two things.

```bash
systemctl enable ai-defense-fss-verify.timer
systemctl start ai-defense-fss-verify.timer
```

The timer became `enabled` and `active`. The existing `ai-defense-manager.service` also remains `active (running)`, PID `2340`, 0 restarts. The display right after showed `Trigger: n/a`, `NEXT: -`.

## 4.2 Checking That It Ran Automatically

> **Run on: VM 230**

```bash
echo "===== VM230: FSS TIMER FIRST ACTIVATION AUDIT ====="

echo
echo "--- 1. Timer scheduling properties ---"
systemctl show ai-defense-fss-verify.timer \
  -p ActiveState -p SubState -p LastTriggerUSec \
  -p NextElapseUSecRealtime -p NextElapseUSecMonotonic \
  -p TimersCalendar -p TimersMonotonic

echo
echo "--- 2. Verification service state ---"
systemctl show ai-defense-fss-verify.service \
  -p ActiveState -p SubState -p Result \
  -p ExecMainCode -p ExecMainStatus -p ExecMainStartTimestamp \
  -p ExecMainExitTimestamp

echo
echo "--- 3. Recent timer and service journal ---"
journalctl \
  -u ai-defense-fss-verify.timer \
  -u ai-defense-fss-verify.service \
  --since "10 minutes ago" \
  --no-pager -o short-iso

echo
echo "--- 4. Timer listing ---"
systemctl list-timers ai-defense-fss-verify.timer --all --no-pager

echo
echo "READ_ONLY_AUDIT=YES"
echo "TIMER_CONFIGURATION_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
```

| Item | Result |
|---|---:|
| Time of automatic run | 03:45:58 UTC (right after the timer was started) |
| Cryptographic verification `PASS` | 2 |
| Old archives `SKIP` | 13 |
| Verification failures | 0 |
| Service exit | `0` (`Result=success`) |
| Timer | `active (waiting)`, next in about 14 minutes |

The `OnBootSec=5min` condition had already passed, so the first run happened when the timer was started, and it runs every 15 minutes after that. `ExecMainCode=1` means the process exited normally; the exit status is `ExecMainStatus=0`.

# Chapter 5: Can Wazuh Be Notified?

We investigate, read-only, whether Wazuh can detect verification failures (`VERIFY_FAIL`, `HEADER_ERROR`, `FATAL`).

> **Run on: VM 230**

```bash
echo "===== VM230: WAZUH AGENT AND JOURNAL INTEGRATION DISCOVERY ====="

echo
echo "--- 1. Wazuh agent package ---"
dpkg-query -W -f='${Status} ${Version}\n' wazuh-agent 2>&1 || true

echo
echo "--- 2. Wazuh agent service state ---"
systemctl show wazuh-agent.service \
  -p LoadState -p ActiveState -p SubState \
  -p MainPID -p NRestarts -p FragmentPath 2>&1

echo
echo "--- 3. Wazuh agent process ---"
pgrep -a -f 'wazuh-agentd|wazuh-logcollector|wazuh-modulesd' \
  || echo "NO_WAZUH_AGENT_PROCESS_FOUND"

echo
echo "--- 4. Wazuh configuration file metadata ---"
if [ -f /var/ossec/etc/ossec.conf ]; then
    stat -c '%A %a %U:%G %s %n' /var/ossec/etc/ossec.conf
    echo "WAZUH_CONFIG_EXISTS=YES"
else
    echo "WAZUH_CONFIG_EXISTS=NO"
fi

echo
echo "--- 5. Existing localfile collection configuration ---"
if [ -f /var/ossec/etc/ossec.conf ]; then
    awk '
      /<localfile>/ { inside=1; print; next }
      inside { 
        if ($0 ~ /<location>|<\/location>|<log_format>|<\/log_format>|<query>|<\/query>/)
          print
        if (/<\/localfile>/) { print; inside=0 }
      }
    ' /var/ossec/etc/ossec.conf
fi

echo
echo "--- 6. Wazuh journal/log collector related configuration references ---"
if [ -d /var/ossec/etc ]; then
    grep -RIlE 'journald|journalctl|/var/log/journal|ai-defense-fss' \
      /var/ossec/etc 2>/dev/null \
      | head -30 || true
fi

echo
echo "--- 7. Existing FSS verifier timer and service ---"
systemctl is-enabled ai-defense-fss-verify.timer 2>&1 || true
systemctl is-active ai-defense-fss-verify.timer 2>&1 || true
systemctl show ai-defense-fss-verify.service \
  -p Result -p ExecMainStatus -p ActiveState

echo
echo "READ_ONLY_DISCOVERY=YES"
echo "WAZUH_CONFIG_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
echo "SECRETS_DISPLAYED=NO"
```

| Investigated | Result |
|---|---|
| `wazuh-agent` package | not installed |
| Agent service and process | none |
| `ossec.conf` | none |
| Configuration to collect journald | none |
| FSS verification timer | enabled and running |

VM 230 has no Wazuh agent, and there is not yet a mechanism to send FSS verification results to Wazuh Manager (VM 220). This is not a problem with the verification itself; the integration path simply does not exist yet.

# Closing Notes

In Part 66 we made FSS verification run automatically every 15 minutes.

| Item | Result |
|---|---|
| Verification script | `/usr/local/sbin/ai-defense-fss-verify` (`0750`) |
| Service and timer | `ai-defense-fss-verify.service` (oneshot, read-only) and `.timer` (5 minutes after boot, then every 15 minutes) |
| Targets | system journals with `SEALED`, `SEALED_CONTINUOUS` and `Tag objects` 1 or more (older ones are `SKIP`) |
| Results | `PASS` 2, `SKIP` 13, 0 failures (once by hand, once automatically) |
| Integration with Wazuh | none yet; VM 230 has no agent |

In the next part, Part 67, before integration, we examine the Wazuh Manager side on VM 220. There, a problem is found in Wazuh's local rules file.

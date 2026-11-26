---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 40: Completing the PostgreSQL Logical Backup"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 40 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". In Part 39 we placed the PostgreSQL logical backup script `/usr/local/sbin/pg-logical-backup.sh` and got as far as testing whether the hard links used for the weekly and monthly generations can be created on NFS. This part does the following.

1. Check the result of the hard-link test
2. Check the script statically and register the systemd service and timer **while leaving them disabled**
3. Run the first backup by hand and check the file permissions, checksums and dump format
4. Replace the script with a safer version that can be repaired by re-running it if it fails partway
5. Enable the daily 02:00 timer

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)

# Chapter 1: Result of the Hard-Link Test

The result of the last test in Part 39 (create two temporary files on NFS, check that they share the same inode, then delete them) was as follows.

| Checked | Result |
|---|---|
| Mount | `192.168.0.254:/mnt/backup nfs`, `MOUNT_CHECK=PASS` |
| Hard link | both files `inode=5 links=2`, `HARDLINK_TEST=PASS` |
| Cleanup | `CLEANUP=PASS` |

Hard links work on TrueNAS's NFS, so we keep the method in which the daily, weekly and monthly generations share the same data. The test files have been removed.

# Chapter 2: Checking the Script and Registering the Units

## 2.1 Syntax and Permissions

> **Run on: pve**

```bash
echo "===== SCRIPT CONTENT ====="
nl -ba /usr/local/sbin/pg-logical-backup.sh

echo
echo "===== SHELLCHECK AVAILABILITY ====="
if command -v shellcheck >/dev/null 2>&1; then
  shellcheck /usr/local/sbin/pg-logical-backup.sh
  echo "SHELLCHECK_EXIT=$?"
else
  echo "SHELLCHECK_NOT_INSTALLED"
fi

echo
echo "===== SCRIPT SYNTAX ====="
bash -n /usr/local/sbin/pg-logical-backup.sh
echo "BASH_SYNTAX_EXIT=$?"

echo
echo "===== SCRIPT PERMISSIONS ====="
stat -c '%A %U:%G %n' /usr/local/sbin/pg-logical-backup.sh
```

The result was `BASH_SYNTAX_EXIT=0` and the permissions were `-rwx------ root:root`. ShellCheck was not installed, and we do not install it here.

## 2.2 Checking How 02:00 Is Written

> **Run on: pve**

```bash
echo "===== BACKUP TARGET AND DATABASE DUMP ====="
grep -n -E '^(CTID|MOUNT|BASE|DAILY|WEEKLY|MONTHLY|STAGING|LOCK)=|pct exec|pg_dump|pg_dumpall|database-list|extensions.tsv|SHA256SUMS' \
  /usr/local/sbin/pg-logical-backup.sh

echo
echo "===== PUBLISH AND RETENTION LOGIC ====="
grep -n -A35 -B5 -E 'Publish daily|prune_generations|rm -rf' \
  /usr/local/sbin/pg-logical-backup.sh

echo
echo "===== SYSTEMD SCHEDULE VALIDATION ====="
systemd-analyze calendar '*-*-* 02:00:00'
```

It showed `Normalized form: *-*-* 02:00:00`, and the next run as `Mon 2026-11-23 02:00:00 JST`.

## 2.3 Reading the Save and Delete Logic

> **Run on: pve**

```bash
echo "===== BACKUP TARGET AND DUMP COMMANDS ====="
grep -n -E '^(CTID|MOUNT|BASE|DAILY|WEEKLY|MONTHLY|STAGING|LOCK)=|pct exec|pg_dump|pg_dumpall|database-list|extensions.tsv|SHA256SUMS' \
  /usr/local/sbin/pg-logical-backup.sh

echo
echo "===== PUBLISH AND DELETE OPERATIONS ====="
grep -n -A35 -B5 -E 'Publish daily|prune_generations|rm -rf' \
  /usr/local/sbin/pg-logical-backup.sh
```

From the output we confirmed the following.

- Only LXC 109 is backed up
- Global objects (roles and so on) and a dump for each database are saved
- Checksums are created and verified before moving the data to the official daily location
- Deletion only targets the inside of each daily, weekly and monthly generation directory

## 2.4 Registering the Service and Timer While Disabled

Here we do not run the script and do not enable the timer.

> **Run on: pve**

```bash
cat > /etc/systemd/system/pg-logical-backup.service <<'EOF'
[Unit]
Description=PostgreSQL logical backup from LXC 109 to TrueNAS
Wants=network-online.target
After=network-online.target mnt-pve-backup.mount
Requires=mnt-pve-backup.mount

[Service]
Type=oneshot
User=root
Group=root
UMask=0077
ExecStart=/usr/local/sbin/pg-logical-backup.sh
TimeoutStartSec=3h
EOF

cat > /etc/systemd/system/pg-logical-backup.timer <<'EOF'
[Unit]
Description=Daily PostgreSQL logical backup at 02:00 JST

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=false
Unit=pg-logical-backup.service

[Install]
WantedBy=timers.target
EOF

echo "===== SYSTEMD UNIT SYNTAX CHECK ====="
systemd-analyze verify \
  /etc/systemd/system/pg-logical-backup.service \
  /etc/systemd/system/pg-logical-backup.timer
echo "VERIFY_EXIT=$?"

echo
echo "===== SYSTEMD DAEMON RELOAD ====="
systemctl daemon-reload
echo "DAEMON_RELOAD_EXIT=$?"

echo
echo "===== TIMER ENABLEMENT STATE ====="
systemctl is-enabled pg-logical-backup.timer 2>&1
echo "TIMER_ACTIVE_STATE:"
systemctl is-active pg-logical-backup.timer 2>&1
```

`systemd-analyze verify` and `daemon-reload` returned `0`, and the timer was `disabled` and `inactive`.

## 2.5 Checking What Was Registered

> **Run on: pve**

```bash
echo "===== SERVICE UNIT ====="
systemctl cat pg-logical-backup.service

echo
echo "===== TIMER UNIT ====="
systemctl cat pg-logical-backup.timer

echo
echo "===== TIMER STATUS ====="
systemctl status pg-logical-backup.timer --no-pager

echo
echo "===== TIMER LIST ====="
systemctl list-timers --all pg-logical-backup.timer

echo
echo "===== SERVICE EXECUTION STATE ====="
systemctl show pg-logical-backup.service \
  -p ActiveState -p SubState -p Result -p ExecMainStartTimestamp
```

The service showed `Result=success` with an empty `ExecMainStartTimestamp` (it has never run), and the timer showed `0 timers listed.`. `preset: enabled` is displayed, but this is only systemd's default recommendation and does not change the current `disabled`.

# Chapter 3: The First Backup

## 3.1 Running It by Hand

With the timer still disabled, we start the service once. The PostgreSQL service is not stopped.

> **Run on: pve**

```bash
echo "===== START FIRST POSTGRESQL LOGICAL BACKUP ====="
systemctl start pg-logical-backup.service
echo "BACKUP_START_EXIT=$?"

echo
echo "===== SERVICE RESULT ====="
systemctl show pg-logical-backup.service \
  -p ActiveState -p SubState -p Result \
  -p ExecMainStartTimestamp -p ExecMainExitTimestamp

echo
echo "===== BACKUP LOG ====="
journalctl -u pg-logical-backup.service -n 100 --no-pager

echo
echo "===== TIMER REMAINS DISABLED ====="
systemctl is-enabled pg-logical-backup.timer 2>&1
systemctl is-active pg-logical-backup.timer 2>&1
```

In the log we confirmed that the dumps of the 17 databases and the global objects were saved and that all SHA-256 checksums were `OK`. It took about one minute. The data was saved in two places:

- Daily: `/mnt/pve/backup/postgresql/daily/2026-11-22`
- Weekly: `/mnt/pve/backup/postgresql/weekly/2026-W47`

November 22 was a Sunday, so a weekly generation was also created.

## 3.2 Checking the Saved Files

This only reads files. No restore and no writes to the database.

> **Run on: pve**

```bash
BACKUP="/mnt/pve/backup/postgresql/daily/2026-11-22"
WEEKLY="/mnt/pve/backup/postgresql/weekly/2026-W47"

echo "===== BACKUP FILE PERMISSIONS ====="
find "$BACKUP" -maxdepth 1 -type f -printf '%M %u:%g %s %f\n' | sort

echo
echo "===== SHA256 VERIFICATION ====="
(
  cd "$BACKUP" && sha256sum -c SHA256SUMS
)
echo "SHA256_EXIT=$?"

echo
echo "===== DATABASE DUMP READABILITY ====="
for file in "$BACKUP"/*.dump; do
  name=$(basename "$file")
  if pct exec 109 -- runuser -u postgres -- pg_restore --list < "$file" >/dev/null 2>&1; then
    echo "RESTORE_LIST_OK: $name"
  else
    echo "RESTORE_LIST_FAILED: $name"
  fi
done

echo
echo "===== DATABASE DUMP COUNT ====="
find "$BACKUP" -maxdepth 1 -type f -name '*.dump' | wc -l

echo
echo "===== WEEKLY HARDLINK CHECK ====="
stat -c '%i %h %n' "$BACKUP/globals.sql" "$WEEKLY/globals.sql"

echo
echo "===== TIMER STATE ====="
systemctl is-enabled pg-logical-backup.timer 2>&1
systemctl is-active pg-logical-backup.timer 2>&1
```

| Checked | Result |
|---|---|
| File permissions | all `root:root`, `600` |
| SHA256 checksums | all 21 entries `OK` |
| `pg_restore --list` | succeeded for all 17 databases |
| Number of dumps | 17 |
| Hard links between daily and weekly | same inode, link count 2 |
| Timer | `disabled`, `inactive` |

Because `pg_restore --list` succeeded for all of them, we know the files not only exist but can also be read as PostgreSQL custom-format dumps.

## 3.3 Checking the Generation Directories

> **Run on: pve**

```bash
BASE="/mnt/pve/backup/postgresql"

echo "===== DAILY GENERATIONS ====="
find "$BASE/daily" -mindepth 1 -maxdepth 1 -printf '%f  %y\n' | sort

echo
echo "===== WEEKLY GENERATIONS ====="
find "$BASE/weekly" -mindepth 1 -maxdepth 1 -printf '%f  %y\n' | sort

echo
echo "===== MONTHLY GENERATIONS ====="
find "$BASE/monthly" -mindepth 1 -maxdepth 1 -printf '%f  %y\n' | sort

echo
echo "===== STAGING CONTENTS ====="
find "$BASE/.staging" -mindepth 1 -maxdepth 2 -printf '%y %p\n' 2>/dev/null

echo
echo "===== BACKUP ROOT FILESYSTEM ====="
findmnt -T "$BASE" -o TARGET,SOURCE,FSTYPE,OPTIONS
```

daily had `2026-11-22`, weekly had `2026-W47`, monthly was empty (correct, because it is created on the 1st of each month), and staging was empty.

# Chapter 4: Making the Script Safer

## 4.1 What We Want to Fix

Re-reading the script, we found two points to fix before starting scheduled runs.

1. If creating a weekly or monthly generation with `cp -al` fails partway, an incomplete directory is left behind. On the next run, the mere existence of the directory is taken as "already created"
2. If the daily generation already exists, processing ends, so if the weekly or monthly step fails after the daily one was created, re-running on the same day cannot repair it

We fix it as follows.

- Create the weekly and monthly generations in a temporary directory, check them, and then publish them with `mv -T`
- Remove the temporary directory on failure
- If the daily generation already exists, verify its SHA256, reuse it, and create any missing weekly or monthly generations
- When deleting generations, check the directory names and the deletion target
- Do not change existing backups, owners, permissions or the number of generations

> **Caution:** Lines in the script such as `cp -al "$FINAL" "$WEEKLY/$WEEK"` are processing that uses the script's variables. Typed directly into a shell, the variables are empty and you get `cp: cannot stat ''` (the backups are not changed).

## 4.2 Replacing It

Save the original script to `/root/pg-logical-backup.sh.before-safety-fix-20261122`, syntax-check the new version, and replace it. The backup is not run and the timer is not enabled.

> **Run on: pve**

```bash
SCRIPT="/usr/local/sbin/pg-logical-backup.sh"
NEW="/root/pg-logical-backup.sh.new"
BACKUP="/root/pg-logical-backup.sh.before-safety-fix-20261122"

echo "===== 1. PRESERVE CURRENT SCRIPT ====="
if [ -e "$BACKUP" ]; then
  echo "ABORT: backup copy already exists: $BACKUP"
else
  cp -a "$SCRIPT" "$BACKUP"
  echo "SCRIPT_BACKUP_EXIT=$?"
fi

if [ -f "$BACKUP" ]; then
  cat > "$NEW" <<'SCRIPT_EOF'
#!/bin/bash

# PostgreSQL logical backup for LXC 109
# Run as root on Proxmox host.

PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
umask 077

CTID=109
MOUNT=/mnt/pve/backup
BASE="$MOUNT/postgresql"
DAILY="$BASE/daily"
WEEKLY="$BASE/weekly"
MONTHLY="$BASE/monthly"
STAGING="$BASE/.staging"
LOCK=/run/lock/pg-logical-backup.lock

log() {
    printf '%s %s\n' "$(date '+%F %T %Z')" "$*"
}

fail() {
    log "ERROR: $*"
    exit 1
}

verify_backup_dir() {
    local dir="$1"

    [ -d "$dir" ] && [ ! -L "$dir" ] ||
        return 1
    [ -f "$dir/SHA256SUMS" ] && [ ! -L "$dir/SHA256SUMS" ] ||
        return 1

    (
        cd "$dir" &&
        sha256sum --status -c SHA256SUMS
    )
}

# Prevent concurrent runs.
exec 9>"$LOCK" || fail "Cannot open lock file"
flock -n 9 || fail "Another backup process is running"

# Confirm the expected NFS mount is active.
mountpoint -q "$MOUNT" || fail "Backup mount is unavailable"
findmnt -rn -T "$MOUNT" -o SOURCE,FSTYPE |
    grep -Fqx '192.168.0.254:/mnt/backup nfs' ||
    fail "Unexpected backup filesystem"

# Confirm the container is running.
pct status "$CTID" | grep -q 'status: running' ||
    fail "LXC $CTID is not running"

# Prepare directories.
for dir in "$DAILY" "$WEEKLY" "$MONTHLY" "$STAGING"; do
    mkdir -p "$dir" || fail "Cannot create $dir"
    [ -d "$dir" ] && [ ! -L "$dir" ] ||
        fail "Backup directory is not a real directory: $dir"
    chmod 700 "$dir" || fail "Cannot secure $dir"
done

DATE=$(date '+%F')
WEEK=$(date '+%G-W%V')
MONTH=$(date '+%Y-%m')
DAY=$(date '+%d')

FINAL="$DAILY/$DATE"
WORK=""
ACTIVE_TMP=""

cleanup() {
    if [ -n "$WORK" ] &&
       [[ "$WORK" == "$STAGING/"* ]] &&
       [ -d "$WORK" ] && [ ! -L "$WORK" ]; then
        rm -rf -- "$WORK"
    fi

    if [ -n "$ACTIVE_TMP" ] &&
       { [[ "$ACTIVE_TMP" == "$WEEKLY/"* ]] ||
         [[ "$ACTIVE_TMP" == "$MONTHLY/"* ]]; } &&
       [ -d "$ACTIVE_TMP" ] && [ ! -L "$ACTIVE_TMP" ]; then
        rm -rf -- "$ACTIVE_TMP"
    fi
}
trap cleanup EXIT

# Reuse an existing daily generation only after checksum verification.
if [ -e "$FINAL" ]; then
    verify_backup_dir "$FINAL" ||
        fail "Existing daily backup failed verification: $FINAL"
    log "Existing daily backup verified; reusing: $FINAL"
else
    WORK="$STAGING/${DATE}-$$"
    mkdir -m 700 "$WORK" ||
        fail "Cannot create staging directory"

    log "Starting PostgreSQL logical backup for LXC $CTID"

    # Save global objects, including role password hashes.
    pct exec "$CTID" -- runuser -u postgres -- \
        pg_dumpall --globals-only > "$WORK/globals.sql" ||
        fail "Global objects dump failed"

    # Save database inventory.
    pct exec "$CTID" -- runuser -u postgres -- \
        psql -X -At -d postgres -c "
            SELECT datname
            FROM pg_database
            WHERE datallowconn AND NOT datistemplate
            ORDER BY datname;
        " > "$WORK/database-list.txt" ||
        fail "Database inventory query failed"

    [ -s "$WORK/database-list.txt" ] ||
        fail "Database inventory is empty"

    # Save PostgreSQL version.
    pct exec "$CTID" -- runuser -u postgres -- \
        psql -X -At -d postgres -c "SELECT version();" \
        > "$WORK/postgresql-version.txt" ||
        fail "PostgreSQL version query failed"

    # Save extension inventory and database dumps.
    while IFS= read -r db; do
        [ -n "$db" ] || continue

        case "$db" in
            *[!A-Za-z0-9_-]*)
                fail "Unexpected database name: $db"
                ;;
        esac

        {
            printf '%s\t' "$db"
            pct exec "$CTID" -- runuser -u postgres -- \
                psql -X -At -F $'\t' -d "$db" -c \
                "SELECT extname, extversion FROM pg_extension ORDER BY extname;" ||
                fail "Extension query failed for $db"
        } >> "$WORK/extensions.tsv" ||
            fail "Cannot write extension inventory"

        log "Dumping database: $db"
        pct exec "$CTID" -- runuser -u postgres -- \
            pg_dump -Fc -d "$db" > "$WORK/${db}.dump" ||
            fail "Database dump failed: $db"

        [ -s "$WORK/${db}.dump" ] ||
            fail "Database dump is empty: $db"

    done < "$WORK/database-list.txt"

    [ -s "$WORK/globals.sql" ] ||
        fail "Global objects dump is empty"

    # Create checksums for all backup files.
    (
        cd "$WORK" || exit 1
        find . -maxdepth 1 -type f ! -name SHA256SUMS -printf '%f\n' |
            LC_ALL=C sort |
            while IFS= read -r file; do
                sha256sum -- "$file"
            done
    ) > "$WORK/SHA256SUMS" ||
        fail "Checksum generation failed"

    verify_backup_dir "$WORK" ||
        fail "Staging checksum verification failed"

    # Publish daily backup atomically.
    [ ! -e "$FINAL" ] ||
        fail "Daily backup appeared during this run: $FINAL"

    mv -T -- "$WORK" "$FINAL" ||
        fail "Cannot publish daily backup"

    WORK=""
    log "Daily backup published: $FINAL"
fi

# Create a verified hard-link generation and publish it atomically.
create_generation() {
    local source="$1"
    local parent="$2"
    local name="$3"
    local target="$parent/$name"
    local tmp="$parent/.${name}.tmp.$$"

    case "$parent:$name" in
        "$WEEKLY":????-W??|"$MONTHLY":????-??)
            ;;
        *)
            fail "Invalid generation target: $target"
            ;;
    esac

    if [ -e "$target" ]; then
        verify_backup_dir "$target" ||
            fail "Existing generation failed verification: $target"
        log "Existing generation verified: $target"
        return 0
    fi

    [ ! -e "$tmp" ] ||
        fail "Temporary generation already exists: $tmp"

    ACTIVE_TMP="$tmp"

    cp -al -- "$source" "$tmp" ||
        fail "Cannot create temporary hard-link generation: $tmp"

    verify_backup_dir "$tmp" ||
        fail "Temporary generation failed verification: $tmp"

    [ ! -e "$target" ] ||
        fail "Generation target appeared during creation: $target"

    mv -T -- "$tmp" "$target" ||
        fail "Cannot publish generation: $target"

    ACTIVE_TMP=""
    log "Generation published: $target"
}

# Weekly generation: Sunday only.
if [ "$(date '+%u')" = "7" ]; then
    create_generation "$FINAL" "$WEEKLY" "$WEEK"
fi

# Monthly generation: first day of month only.
if [ "$DAY" = "01" ]; then
    create_generation "$FINAL" "$MONTHLY" "$MONTH"
fi

# Prune only validated generation directories.
prune_generations() {
    local dir="$1"
    local kind="$2"
    local keep="$3"
    local name
    local target
    local -a generations=()

    mapfile -t generations < <(
        find "$dir" -mindepth 1 -maxdepth 1 -type d \
            -printf '%f\n' | LC_ALL=C sort -r
    )

    for name in "${generations[@]}"; do
        case "$kind:$name" in
            daily:????-??-??|weekly:????-W??|monthly:????-??)
                ;;
            *)
                fail "Unexpected generation name in $dir: $name"
                ;;
        esac
    done

    if [ "${#generations[@]}" -gt "$keep" ]; then
        for name in "${generations[@]:$keep}"; do
            target="$dir/$name"

            [ -d "$target" ] && [ ! -L "$target" ] ||
                fail "Prune target is not a real directory: $target"

            rm -rf -- "$target" ||
                fail "Cannot prune generation: $target"

            log "Pruned generation: $target"
        done
    fi
}

prune_generations "$DAILY" daily 7
prune_generations "$WEEKLY" weekly 4
prune_generations "$MONTHLY" monthly 3

log "PostgreSQL logical backup completed successfully"
SCRIPT_EOF

  echo
  echo "===== 2. CHECK NEW SCRIPT SYNTAX ====="
  bash -n "$NEW"
  SYNTAX_EXIT=$?
  echo "BASH_SYNTAX_EXIT=$SYNTAX_EXIT"

  if [ "$SYNTAX_EXIT" -eq 0 ]; then
    echo
    echo "===== 3. INSTALL NEW SCRIPT ====="
    install -o root -g root -m 700 "$NEW" "$SCRIPT"
    INSTALL_EXIT=$?
    echo "INSTALL_EXIT=$INSTALL_EXIT"

    if [ "$INSTALL_EXIT" -eq 0 ]; then
      rm -f -- "$NEW"
      echo
      echo "===== 4. VERIFY INSTALLED SCRIPT ====="
      stat -c '%A %U:%G %n' "$SCRIPT"
      bash -n "$SCRIPT"
      echo "INSTALLED_SYNTAX_EXIT=$?"
    fi
  fi
else
  echo "ABORT: original script backup was not created"
fi

echo
echo "===== TIMER STATE (MUST REMAIN DISABLED) ====="
systemctl is-enabled pg-logical-backup.timer
systemctl is-active pg-logical-backup.timer
```

Saving the original, replacing it and the Bash syntax check all returned exit code `0`. The owner and permissions are `root:root`, `700`.

## 4.3 Checking What Was Placed

We check the contents of the file to make sure no characters were mixed in when pasting into the terminal.

> **Run on: pve**

```bash
SCRIPT="/usr/local/sbin/pg-logical-backup.sh"

echo "===== INSTALLED SCRIPT: FULL CONTENT ====="
nl -ba "$SCRIPT"

echo
echo "===== SCRIPT CHECKSUM ====="
sha256sum "$SCRIPT"

echo
echo "===== ORIGINAL SCRIPT BACKUP CHECKSUM ====="
sha256sum /root/pg-logical-backup.sh.before-safety-fix-20261122

echo
echo "===== IMPORTANT FUNCTION MARKERS ====="
grep -nE '^(verify_backup_dir|cleanup|create_generation|prune_generations)\(\)|Daily backup|Weekly generation|Monthly generation|completed successfully|rm -rf|cp -al|mv -T' "$SCRIPT"

echo
echo "===== TIMER STATE ====="
systemctl is-enabled pg-logical-backup.timer
systemctl is-active pg-logical-backup.timer
```

We checked all 279 lines and confirmed that all the intended safeguards are present.

| Safeguard | Result |
|---|---|
| Verify the SHA256 of an existing daily generation | present |
| Reuse the daily generation | present |
| Create weekly and monthly in a temporary directory | present |
| Verify checksums before publishing | present |
| Publish generations with `mv -T` | present |
| Remove temporary data on abnormal exit | present |
| Check generation names | present |
| Number of generations | 7 days, 4 weeks, 3 months |

# Chapter 5: Enabling the Daily 02:00 Timer

This operation does not start a backup immediately. The next run is Monday, November 23, 2026, at 02:00. The Proxmox backup job for LXC 109 stays disabled for now.

> **Run on: pve**

```bash
echo "===== ENABLE POSTGRESQL BACKUP TIMER ====="
systemctl enable --now pg-logical-backup.timer
echo "ENABLE_EXIT=$?"

echo
echo "===== ENABLED STATE ====="
systemctl is-enabled pg-logical-backup.timer

echo
echo "===== ACTIVE STATE ====="
systemctl is-active pg-logical-backup.timer

echo
echo "===== TIMER STATUS ====="
systemctl status pg-logical-backup.timer --no-pager -l

echo
echo "===== NEXT SCHEDULE ====="
systemctl list-timers --all pg-logical-backup.timer --no-pager
```

| Item | State |
|---|---|
| Timer | `enabled`, `active (waiting)` |
| Run time | daily at 02:00 (Japan time) |
| Next run | November 23, 2026, 02:00 |
| Target | PostgreSQL in LXC 109 |
| Destination | TrueNAS NFS `/mnt/pve/backup/postgresql` |
| Generations | daily 7, weekly 4, monthly 3 |

The result of the next day's run is checked in Part 43.

# Closing Notes

In Part 40 we completed the PostgreSQL logical backup and made it run automatically.

| Item | Result |
|---|---|
| Hard-link test | passed (same inode, link count 2) |
| Service and timer | registered `pg-logical-backup.service` and `.timer` (daily 02:00) |
| First backup | 17 databases and the global objects. 21 checksum entries `OK`, `pg_restore --list` succeeded for 17, permissions `600` |
| Script | replaced with a safer version (279 lines) that can be repaired by re-running. The original is `/root/pg-logical-backup.sh.before-safety-fix-20261122` |
| Timer | enabled (`enabled`, `active`) |
| Not yet done | Proxmox backup of LXC 109, restore test |

In the next part, Part 41, we back up LXC 109 to TrueNAS with Proxmox and test restoring it to an LXC with a different number.

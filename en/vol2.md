---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 2: Safely Monitoring PostgreSQL Logs and Correlation Detection"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 2 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". We add PostgreSQL (LXC 109) log monitoring to the Wazuh environment built in Part 1. Without sending SQL statements, user names and so on to Wazuh, we safely extract only events such as authentication failures, and build brute-force detection per source IP.

- Investigating the PostgreSQL logs and deciding on a method that does not forward SQL statements (Chapter 1)
- Creating the sanitizing filter and running it as a service (Chapters 2–3)
- Wazuh agent monitoring settings and detection rules on the Manager side (Chapters 4–5)
- Correlation detection of authentication failures (Chapter 6)
- Obtaining the source IP and putting per-source-IP correlation detection into production (Chapters 7–8)

## Notation

- Commands and file contents are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Each step begins with "Run on", which says where to run it. `root@pve` is the Proxmox host and `root@security-core` is VM 220. Operations on LXC 109 are run from the Proxmox host with `pct exec 109 --`.
- "Example output" is the actual output from the build. In your environment, counts, dates and so on will differ.

## State at the End of Part 1

| Agent ID | Name | Target | State |
|---:|---|---|---|
| 000 | security-core | VM 220 (Manager, `192.168.0.220`) | Active/Local |
| 001 | pve | Proxmox host | Active |
| 002 | lxc-prometheus | LXC 103 | Active |
| 003 | lxc-grafana | LXC 105 | Active |
| 004 | postgresql | LXC 109 (PostgreSQL 17, `192.168.0.151`) | Active |

# Chapter 1: Investigating the PostgreSQL Logs

In this chapter we find out where and in what format PostgreSQL writes its logs. We do not change the PostgreSQL settings yet.

## 1.1 Checking the Log Settings and Configuration Files

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
echo "===== POSTGRESQL LOG SETTINGS ====="
runuser -u postgres -- psql -X -At -c "
SHOW log_destination;
SHOW logging_collector;
SHOW log_directory;
SHOW log_filename;
SHOW log_rotation_age;
SHOW log_rotation_size;
"

echo "===== POSTGRESQL CONFIG FILES ====="
ls -lh /etc/postgresql/17/main/postgresql.conf \
       /etc/postgresql/17/main/pg_hba.conf \
       /etc/postgresql/17/main/pg_ident.conf

echo "===== POSTGRESQL LOG DIRECTORIES ====="
ls -ld /var/log/postgresql /var/lib/postgresql/17/main/log 2>/dev/null || true
'
```

The settings at build time were as follows.

| Item | Setting |
|---|---|
| log_destination | `stderr` |
| logging_collector | `off` |
| log_directory | `log` |
| log_filename | `postgresql-%Y-%m-%d_%H%M%S.log` |
| Rotation | 1 day / 10 MB |

Because `logging_collector=off`, PostgreSQL itself does not create log files. The next step checks where the Debian service records the standard error output.

## 1.2 Checking the Log File and Logging Parameters

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
echo "===== POSTGRESQL LOG FILES ====="
ls -lah /var/log/postgresql/

echo "===== POSTGRESQL LOG FILE TYPES ====="
file /var/log/postgresql/* 2>/dev/null || true

echo "===== RECENT POSTGRESQL JOURNAL ====="
journalctl -u postgresql@17-main --no-pager -n 30

echo "===== POSTGRESQL LOGGING PARAMETERS ====="
runuser -u postgres -- psql -X -At -c "
SHOW log_line_prefix;
SHOW log_connections;
SHOW log_disconnections;
SHOW log_min_messages;
SHOW data_directory;
SHOW config_file;
"
'
```

The check showed the following.

- The log file to monitor is `/var/log/postgresql/postgresql-17-main.log`.
- Daily rotation is in effect.
- `log_line_prefix` is `%m [%p] %q%u@%d `.
- `log_connections=off`, `log_disconnections=off`, `log_min_messages=warning`. Connections and disconnections are not recorded, which limits monitoring of authentication failures and connection anomalies.

## 1.3 Checking the Log Contents and Existing Wazuh Settings

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
echo "===== POSTGRESQL LOG SAMPLE ====="
tail -n 15 /var/log/postgresql/postgresql-17-main.log

echo "===== WAZUH LOCALFILE CONFIGURATION ====="
grep -n -A 8 -B 2 "<localfile>" /var/ossec/etc/ossec.conf

echo "===== WAZUH POSTGRESQL DECODERS ====="
grep -Ril "postgresql" /var/ossec/ruleset/decoders 2>/dev/null || true
'
```

The PostgreSQL log contains the following kinds of lines.

| Kind | Content |
|---|---|
| `ERROR` | SQL execution errors |
| `FATAL` | Serious errors such as authentication failures |
| `LOG` | Connections, disconnections and internal database events |
| `STATEMENT` | Executed SQL statements |

Wazuh had no PostgreSQL-specific decoder or log collection settings.

> **Important:** The current log records even actual SQL statements and application data. If this log is forwarded to the Wazuh Manager as is, the database information is duplicated on the SIEM side as well.

## 1.4 Deciding the Monitoring Method

We decided to build it as follows.

**A method that does not forward SQL statements or parameter values to the Wazuh Manager**

1. Keep the raw log only inside LXC 109.
2. An independent filter running inside LXC 109 reads the log and writes only permitted events to a separate file.
3. The Wazuh agent monitors only the file written by the filter.

The filter passes to Wazuh only the time, the severity and a predefined event category. It does not forward SQL statements, `STATEMENT`, `DETAIL` or `CONTEXT` lines, user names, or raw error messages.

## 1.5 Checking the Rotation Method and Log Output Method

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
echo "===== POSTGRESQL LOGROTATE ====="
cat /etc/logrotate.d/postgresql-common 2>/dev/null

echo "===== POSTGRESQL LOGGING CONFIG ====="
grep -nE "^[[:space:]]*#?[[:space:]]*(logging_collector|log_destination|log_statement|log_min_messages|log_line_prefix|log_connections|log_disconnections|syslog_facility|syslog_ident)" \
  /etc/postgresql/17/main/postgresql.conf

echo "===== RSYSLOG STATUS ====="
systemctl is-active rsyslog 2>/dev/null || true

echo "===== LOG FILE OWNERSHIP ====="
stat -c "%U:%G %a %n" /var/log/postgresql/postgresql-17-main.log
'
```

| Item | Result | Decision |
|---|---|---|
| Rotation method | `copytruncate` | The filter must follow truncation of the file |
| rsyslog | `inactive` | Do not use rsyslog forwarding rules |
| Log file permissions | `postgres:adm 640` | Do not let Wazuh read the original log directly |

## 1.6 Checking the Effective Settings

Check the log settings that PostgreSQL actually uses.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- sudo -u postgres psql -X -At -c "
SELECT name || '=' || setting
FROM pg_settings
WHERE name IN (
  'logging_collector',
  'log_destination',
  'log_statement',
  'log_min_messages',
  'log_min_error_statement',
  'log_line_prefix',
  'log_connections',
  'log_disconnections',
  'log_directory',
  'log_filename'
)
ORDER BY name;
"
```

Because `log_min_error_statement=error`, whenever an SQL error occurs, the SQL statement is recorded on a separate `STATEMENT:` line. The filter must reliably exclude this line.

## 1.7 Counting by Severity

Count only the number of lines per severity, without showing log text or SQL statements.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
LOG=/var/log/postgresql/postgresql-17-main.log

echo "===== LOG EVENT COUNTS ====="
for level in PANIC FATAL ERROR WARNING LOG STATEMENT; do
    count=$(grep -cE " ${level}:" "$LOG" 2>/dev/null || true)
    printf "%-12s %s\n" "$level" "$count"
done
'
```

Example output:

```text
===== LOG EVENT COUNTS =====
PANIC        0
FATAL        20
ERROR        88
WARNING      3
LOG          2280
STATEMENT    88
```

`ERROR` and `STATEMENT` have the same count (88), which shows that an SQL statement is recorded with every error.

## 1.8 Checking the Kinds of FATAL

To distinguish authentication failures from other connection failures, count only `FATAL` lines by keyword. The log text is not shown.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
LOG=/var/log/postgresql/postgresql-17-main.log

echo "===== FATAL EVENT CLASSIFICATION COUNTS ====="
for pattern in \
  "password authentication failed" \
  "authentication failed" \
  "no pg_hba.conf entry" \
  "role .* does not exist" \
  "database .* does not exist" \
  "too many connections" \
  "SSL"
do
    count=$(grep " FATAL:" "$LOG" | grep -ciE "$pattern" || true)
    printf "%-38s %s\n" "$pattern" "$count"
done
'
```

At build time, 8 of the 20 `FATAL` lines were password authentication failures. All other patterns were 0.

From this result, we decided on the following events to send to Wazuh.

| What is detected | Event name sent to Wazuh |
|---|---|
| Password authentication failure | `POSTGRESQL_AUTH_FAILURE` |
| Other FATAL | `POSTGRESQL_FATAL` |
| ERROR | `POSTGRESQL_ERROR` |
| WARNING | `POSTGRESQL_WARNING` |
| PANIC | `POSTGRESQL_PANIC` |

Logs that cannot be classified are not forwarded.

# Chapter 2: Preparing the Filter

## 2.1 Checking the Existing Settings and Output Location

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
echo "===== EXISTING POSTGRESQL LOCALFILE REFERENCES ====="
grep -n -i -B 3 -A 5 "postgresql" /var/ossec/etc/ossec.conf || true

echo "===== FILTER OUTPUT DIRECTORY ====="
if [ -e /var/log/postgresql-wazuh ]; then
    stat -c "%U:%G %a %n" /var/log/postgresql-wazuh
else
    echo "Not created"
fi

echo "===== WAZUH LOGCOLLECTOR STATUS ====="
systemctl is-active wazuh-agent
'
```

Confirm that there are no Wazuh monitoring settings for PostgreSQL yet and that the filter's output location is `Not created`.

## 2.2 Checking the User the Wazuh Agent Runs As

To decide the owner and permissions of the output file, check the user Wazuh runs as.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
echo "===== WAZUH SERVICE USER ====="
systemctl show wazuh-agent -p User -p Group

echo "===== WAZUH ACCOUNT ====="
getent passwd wazuh || true
id wazuh 2>/dev/null || true

echo "===== AGENT PROCESS ====="
ps -eo user,group,pid,comm | grep -E "wazuh-logcollector|wazuh-agentd" | grep -v grep
'
```

```bash
pct exec 109 -- bash -c '
echo "===== WAZUH AGENT STATUS ====="
systemctl status wazuh-agent --no-pager -l

echo "===== WAZUH PROCESSES ====="
pgrep -a -f "wazuh|ossec" || true

echo "===== WAZUH GROUP MEMBERSHIP ====="
getent group wazuh
'
```

Check the user the log collection process (`wazuh-logcollector`) runs as, and whether it can access the original log.

> `pgrep -x wazuh-logcollector` does not work, because `pgrep -x` cannot search for process names longer than 15 characters. Get the PID from the path of the executable instead.

```bash
pct exec 109 -- bash -c '
PID=$(ps -eo pid,args | awk '\''$2=="/var/ossec/bin/wazuh-logcollector" {print $1; exit}'\'')
echo "===== WAZUH LOGCOLLECTOR IDENTITY ====="
if [ -n "$PID" ]; then
    ps -o pid,ppid,user,group,comm,args -p "$PID"
else
    echo "wazuh-logcollector process not found"
fi

echo "===== WAZUH ORIGINAL LOG ACCESS ====="
runuser -u wazuh -- test -r /var/log/postgresql/postgresql-17-main.log \
  && echo "Readable" || echo "Not readable (expected)"
'
```

Example output:

```text
    PID    PPID USER     GROUP    COMMAND         COMMAND
  10336       1 root     wazuh    wazuh-logcollec /var/ossec/bin/wazuh-logcollector
===== WAZUH ORIGINAL LOG ACCESS =====
Not readable (expected)
```

| Item | Result |
|---|---|
| Wazuh user | `wazuh` (UID 103, GID 107) |
| `wazuh-logcollector` | Runs as root, group `wazuh` |
| Original PostgreSQL log | Not readable by the `wazuh` user (desirable) |

We do not change the permissions of the original log. Only the filter service, running as root, reads the original log, and Wazuh reads only the filter's output file.

## 2.3 Creating the Filter Output Location

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
install -d -o root -g wazuh -m 0750 /var/log/postgresql-wazuh
install -o root -g wazuh -m 0640 /dev/null /var/log/postgresql-wazuh/events.log

echo "===== FILTER DIRECTORY ====="
stat -c "%U:%G %a %n" /var/log/postgresql-wazuh

echo "===== FILTER OUTPUT FILE ====="
stat -c "%U:%G %a %n" /var/log/postgresql-wazuh/events.log

echo "===== WAZUH READ TEST ====="
runuser -u wazuh -- test -r /var/log/postgresql-wazuh/events.log \
  && echo "PASS: Wazuh can read filtered log" \
  || echo "FAIL: Wazuh cannot read filtered log"
'
```

Example output:

```text
===== FILTER DIRECTORY =====
root:wazuh 750 /var/log/postgresql-wazuh
===== FILTER OUTPUT FILE =====
root:wazuh 640 /var/log/postgresql-wazuh/events.log
===== WAZUH READ TEST =====
PASS: Wazuh can read filtered log
```

## 2.4 Checking the Python Runtime

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
echo "===== PYTHON ====="
python3 --version

echo "===== SYSTEMD ====="
systemctl --version | head -n 1

echo "===== FILTER OUTPUT ====="
ls -l /var/log/postgresql-wazuh/
'
```

At build time, with Python 3.13.5 and systemd 257, the filter could be implemented without additional packages.

# Chapter 3: Creating the Filter and Running It as a Service

## 3.1 How the Filter Works

1. Read the PostgreSQL log.
2. Parse only the standard PostgreSQL log prefix at the start of each line (time, PID, severity) to identify `FATAL`, `ERROR`, `WARNING` and `PANIC`. The string "ERROR" in the body is not used for the decision, so SQL statements and multi-line `STATEMENT`s are never mistaken for events.
3. Classify authentication failures as a dedicated event.
4. Do not output SQL statements, `STATEMENT`, `DETAIL`, `CONTEXT`, user names or error text.
5. Do not forward past logs written before startup; process only new logs.
6. Follow file replacement and file truncation by `copytruncate`.

## 3.2 Creating the Filter

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c 'cat > /usr/local/sbin/postgresql-wazuh-filter.py <<'"'"'PY'"'"'
#!/usr/bin/env python3

import os
import re
import time

SOURCE = "/var/log/postgresql/postgresql-17-main.log"
OUTPUT = "/var/log/postgresql-wazuh/events.log"

# Parse only the leading part of the standard PostgreSQL log.
PREFIX = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?(?: [A-Z]{2,5})?)"
    r" \[\d+\] (?:\S+ )?"
    r"(PANIC|FATAL|ERROR|WARNING):"
)

AUTH_FAILURE = re.compile(
    r"\bpassword authentication failed\b",
    re.IGNORECASE
)

EVENTS = {
    "PANIC": "POSTGRESQL_PANIC",
    "FATAL": "POSTGRESQL_FATAL",
    "ERROR": "POSTGRESQL_ERROR",
    "WARNING": "POSTGRESQL_WARNING",
}

def classify(line):
    match = PREFIX.match(line)
    if not match:
        return None

    timestamp, severity = match.groups()

    if severity == "FATAL" and AUTH_FAILURE.search(line):
        event = "POSTGRESQL_AUTH_FAILURE"
    else:
        event = EVENTS[severity]

    # Do not output the original log message, SQL, user names, etc.
    return f"{timestamp} {event}\n"


def main():
    os.umask(0o027)

    with open(SOURCE, "r", encoding="utf-8", errors="replace") as source:
        # Do not forward past logs written before startup.
        source.seek(0, os.SEEK_END)

        with open(OUTPUT, "a", encoding="utf-8") as output:
            current_inode = os.stat(SOURCE).st_ino

            while True:
                line = source.readline()

                if line:
                    event = classify(line)
                    if event:
                        output.write(event)
                        output.flush()
                    continue

                time.sleep(1)

                try:
                    info = os.stat(SOURCE)
                except FileNotFoundError:
                    continue

                # Follow log file replacement and rotation.
                if info.st_ino != current_inode:
                    source.close()
                    source = open(
                        SOURCE, "r",
                        encoding="utf-8",
                        errors="replace"
                    )
                    source.seek(0, os.SEEK_END)
                    current_inode = info.st_ino

                # Follow truncation by copytruncate.
                elif info.st_size < source.tell():
                    source.seek(0)


if __name__ == "__main__":
    main()
PY

chmod 0750 /usr/local/sbin/postgresql-wazuh-filter.py
chown root:root /usr/local/sbin/postgresql-wazuh-filter.py

echo "===== SCRIPT PERMISSIONS ====="
stat -c "%U:%G %a %n" /usr/local/sbin/postgresql-wazuh-filter.py

echo "===== PYTHON SYNTAX CHECK ====="
python3 -m py_compile /usr/local/sbin/postgresql-wazuh-filter.py
echo "Python syntax OK"
'
```

If `root:root 750 /usr/local/sbin/postgresql-wazuh-filter.py` and `Python syntax OK` are shown at the end, it has succeeded.

## 3.3 Confirming That the File Was Written to the End

When a long command is pasted, the terminal display can break partway through. Besides the syntax check, confirm that the file was written all the way to the end.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
echo "===== SCRIPT LINE COUNT ====="
wc -l /usr/local/sbin/postgresql-wazuh-filter.py

echo "===== SCRIPT END ====="
tail -n 50 /usr/local/sbin/postgresql-wazuh-filter.py

echo "===== MAIN FUNCTION CHECK ====="
grep -nE "^def main|^if __name__|output.write|source.readline|source.seek" \
  /usr/local/sbin/postgresql-wazuh-filter.py || true
'
```

If the file has 89 lines and ends with `if __name__ == "__main__":`, it is correct.

## 3.4 Testing Against the Actual Log Format

Check whether the filter's patterns match the format of the current PostgreSQL log. Only the counts are examined; no log text or SQL statements are shown.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- python3 - <<'PY'
import importlib.util
from collections import Counter

path = "/usr/local/sbin/postgresql-wazuh-filter.py"
spec = importlib.util.spec_from_file_location("pgfilter", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

counts = Counter()
unmatched = Counter()

with open(module.SOURCE, encoding="utf-8", errors="replace") as f:
    for line in f:
        event = module.classify(line)
        if event:
            name = event.strip().split()[-1]
            counts[name] += 1
        else:
            for level in ("PANIC", "FATAL", "ERROR", "WARNING"):
                if f" {level}:" in line:
                    unmatched[level] += 1

print("===== FILTER MATCH COUNTS =====")
for name, count in sorted(counts.items()):
    print(f"{name}: {count}")

print("===== UNMATCHED SEVERITY COUNTS =====")
for name, count in sorted(unmatched.items()):
    print(f"{name}: {count}")

print("===== RESULT =====")
print("PASS" if not unmatched else "REVIEW REQUIRED")
PY
```

If `PASS` is shown, the filter handles the actual log format. If `REVIEW REQUIRED` is shown, fix the patterns before going on. The counts at build time were as follows.

| Event | Count |
|---|---:|
| Authentication failure | 8 |
| Other FATAL | 12 |
| ERROR | 88 |
| WARNING | 3 |

## 3.5 Testing That SQL Statements Are Not Output

Without writing to the actual PostgreSQL log, test only the Python functions with dummy data.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- python3 - <<'PY'
import importlib.util

path = "/usr/local/sbin/postgresql-wazuh-filter.py"
spec = importlib.util.spec_from_file_location("pgfilter", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

tests = [
    (
        "2026-11-18 14:00:00 JST [1234] app@db ERROR: test error "
        "STATEMENT: UPDATE secret_table SET password='SECRET_SQL_VALUE'",
        "POSTGRESQL_ERROR"
    ),
    (
        "2026-11-18 14:01:00 JST [1235] app@db FATAL: password authentication failed for user SECRET_USER",
        "POSTGRESQL_AUTH_FAILURE"
    ),
    (
        "2026-11-18 14:02:00 JST [1236] app@db WARNING: test warning",
        "POSTGRESQL_WARNING"
    ),
]

for raw, expected in tests:
    result = module.classify(raw)
    assert result is not None and expected in result, "Classification failed"
    assert "SECRET_SQL_VALUE" not in result
    assert "SECRET_USER" not in result
    assert "UPDATE" not in result
    assert "password authentication failed" not in result

print("PASS: SQL text excluded")
print("PASS: User information excluded")
print("PASS: Raw error messages excluded")
print("PASS: Only fixed event names are emitted")
PY
```

Example output:

```text
PASS: SQL text excluded
PASS: User information excluded
PASS: Raw error messages excluded
PASS: Only fixed event names are emitted
```

## 3.6 Registering the systemd Service

Register a systemd service to keep the filter running. It sets security restrictions such as a read-only file system and limited write locations.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c 'cat > /etc/systemd/system/postgresql-wazuh-filter.service <<'"'"'EOF'"'"'
[Unit]
Description=PostgreSQL sanitized event filter for Wazuh
After=local-fs.target
Wants=local-fs.target

[Service]
Type=simple
User=root
Group=root
ExecStart=/usr/bin/python3 /usr/local/sbin/postgresql-wazuh-filter.py
Restart=always
RestartSec=5
UMask=0027

# Security restrictions
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
ProtectHostname=true
ProtectClock=true
PrivateDevices=true
RestrictSUIDSGID=true
LockPersonality=true
MemoryDenyWriteExecute=true
ReadOnlyPaths=/var/log/postgresql
ReadWritePaths=/var/log/postgresql-wazuh

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

echo "===== SYSTEMD UNIT VALIDATION ====="
systemd-analyze verify /etc/systemd/system/postgresql-wazuh-filter.service

echo "===== SERVICE DEFINITION ====="
systemctl cat postgresql-wazuh-filter.service
'
```

Confirm that `systemd-analyze verify` shows no errors.

## 3.7 Starting the Service

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
systemctl enable --now postgresql-wazuh-filter.service

echo "===== SERVICE STATUS ====="
systemctl status postgresql-wazuh-filter.service --no-pager -l

echo "===== FILTER OUTPUT ====="
ls -l /var/log/postgresql-wazuh/events.log

echo "===== RECENT SERVICE LOG ====="
journalctl -u postgresql-wazuh-filter.service -n 10 --no-pager
'
```

It has succeeded if the service is `active (running)` and `Started postgresql-wazuh-filter.service - PostgreSQL sanitized event filter for Wazuh.` is logged. Memory use at build time was about 1.6 MB.

## 3.8 Changing the Output Format to JSON

To use Wazuh's JSON log collection, standardize the output format on JSON. The change is made while the output file is still empty, so it does not affect existing events.

Stop the service, rewrite the output part, and test the JSON output.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
systemctl stop postgresql-wazuh-filter.service

python3 - <<'"'"'PY'"'"'
from pathlib import Path

p = Path("/usr/local/sbin/postgresql-wazuh-filter.py")
s = p.read_text()

s = s.replace("import os\nimport re\nimport time", "import json\nimport os\nimport re\nimport time")

s = s.replace(
    "return f\"{timestamp} {event}\\n\"",
    "return json.dumps({\"timestamp\": timestamp, \"event\": event}, ensure_ascii=True) + \"\\n\""
)

p.write_text(s)
PY

python3 -m py_compile /usr/local/sbin/postgresql-wazuh-filter.py

echo "===== JSON OUTPUT TEST ====="
python3 - <<'"'"'PY'"'"'
import importlib.util
import json

path = "/usr/local/sbin/postgresql-wazuh-filter.py"
spec = importlib.util.spec_from_file_location("pgfilter", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

sample = "2026-11-18 15:10:00 JST [1234] app@db FATAL: password authentication failed for user SECRET_USER"
result = module.classify(sample)
obj = json.loads(result)

assert obj["event"] == "POSTGRESQL_AUTH_FAILURE"
assert "SECRET_USER" not in result
assert "password authentication failed" not in result

print(json.dumps(obj, ensure_ascii=False))
print("PASS: valid JSON; sensitive message excluded")
PY
'
```

Example output:

```text
===== JSON OUTPUT TEST =====
{"timestamp": "2026-11-18 15:10:00 JST", "event": "POSTGRESQL_AUTH_FAILURE"}
PASS: valid JSON; sensitive message excluded
```

## 3.9 Restarting the Service

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
systemctl restart postgresql-wazuh-filter.service

echo "===== SERVICE STATUS ====="
systemctl is-active postgresql-wazuh-filter.service

echo "===== SERVICE DETAILS ====="
systemctl status postgresql-wazuh-filter.service --no-pager -l

echo "===== OUTPUT FILE ====="
ls -l /var/log/postgresql-wazuh/events.log
'
```

If `active` is shown, the filter is ready. In the next chapter we have the Wazuh agent monitor this file.

# Chapter 4: Monitoring Settings for the Wazuh Agent

Have the Wazuh agent on LXC 109 monitor only the JSON file written by the filter. It does not monitor the original PostgreSQL log.

## 4.1 Backing Up the Configuration File

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
BACKUP="/var/ossec/etc/ossec.conf.backup-$(date +%Y%m%d-%H%M%S)"
cp -a /var/ossec/etc/ossec.conf "$BACKUP"
echo "Backup created: $BACKUP"
'
```

## 4.2 Adding the Monitoring Settings

Leave the existing configuration blocks untouched and add a new `<ossec_config>` block at the end of the configuration file.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
cat >> /var/ossec/etc/ossec.conf <<'"'"'EOF'"'"'

<ossec_config>
  <localfile>
    <location>/var/log/postgresql-wazuh/events.log</location>
    <log_format>json</log_format>
  </localfile>
</ossec_config>
EOF

echo "===== ADDED CONFIGURATION ====="
tail -n 12 /var/ossec/etc/ossec.conf
'
```

## 4.3 Validating the Settings

Wazuh's `ossec.conf` may contain several `<ossec_config>` blocks. Parsing it as a normal XML document therefore gives the error `junk after document element`. This is not a configuration error. Wrap the whole thing in a temporary root element before validating.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
echo "===== WAZUH CONFIG STRUCTURE VALIDATION ====="
python3 - <<'"'"'PY'"'"'
from pathlib import Path
import xml.etree.ElementTree as ET

content = Path("/var/ossec/etc/ossec.conf").read_text()
ET.fromstring("<config_root>\n" + content + "\n</config_root>")
print("PASS: all ossec_config blocks are well-formed")

root = ET.fromstring("<config_root>\n" + content + "\n</config_root>")
for localfile in root.findall(".//localfile"):
    location = localfile.findtext("location")
    if location == "/var/log/postgresql-wazuh/events.log":
        print("PASS: PostgreSQL JSON localfile configuration found")
        print("log_format:", localfile.findtext("log_format"))
        break
else:
    raise SystemExit("FAIL: PostgreSQL localfile configuration not found")
PY

echo
echo "===== WAZUH AGENT CONFIG TEST ====="
/var/ossec/bin/wazuh-agentd -t
RESULT=$?
echo "Exit code: $RESULT"
exit "$RESULT"
'
```

Example output:

```text
===== WAZUH CONFIG STRUCTURE VALIDATION =====
PASS: all ossec_config blocks are well-formed
PASS: PostgreSQL JSON localfile configuration found
log_format: json

===== WAZUH AGENT CONFIG TEST =====
Exit code: 0
```

## 4.4 Restarting the Wazuh Agent

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
systemctl restart wazuh-agent

echo "===== SERVICE STATUS ====="
systemctl is-active wazuh-agent

echo
echo "===== RECENT AGENT LOG ====="
journalctl -u wazuh-agent -n 20 --no-pager
'
```

It has succeeded if `active` is shown and `Started wazuh-agent.service - Wazuh agent.` is logged.

## 4.5 Confirming That Monitoring Has Started

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
echo "===== LOGCOLLECTOR PROCESS ====="
pgrep -af wazuh-logcollector

echo
echo "===== POSTGRESQL LOG MONITOR REFERENCES ====="
grep -Ei "postgresql-wazuh/events.log|events.log" /var/ossec/logs/ossec.log | tail -n 20

echo
echo "===== FILTER OUTPUT PERMISSIONS ====="
stat -c "%U:%G %a %n" /var/log/postgresql-wazuh/events.log

echo
echo "===== WAZUH USER READ TEST ====="
runuser -u wazuh -- test -r /var/log/postgresql-wazuh/events.log \
  && echo "PASS: wazuh can read sanitized events"
'
```

| Item | Expected value |
|---|---|
| Log collection | `Analyzing file: '/var/log/postgresql-wazuh/events.log'.` is logged |
| File permissions | `root:wazuh 640` |
| Read by the Wazuh user | `PASS: wazuh can read sanitized events` |

# Chapter 5: Detection Rules on the Manager Side

Add PostgreSQL-specific detection rules to the Wazuh Manager on VM 220. In this chapter, operations on VM 220 are run from the Proxmox host with `qm guest exec 220` (a way to run commands inside the VM through the QEMU Guest Agent). The result is returned as JSON, with the command output in `out-data`.

## 5.1 Checking That the QEMU Guest Agent Responds

**Run on: the Proxmox host (root@pve)**

```bash
qm guest cmd 220 get-osinfo
```

If `"pretty-name" : "Ubuntu 24.04.5 LTS"` is returned, VM 220 can be operated through the Guest Agent.

## 5.2 Checking the Existing Rules

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
echo "===== WAZUH MANAGER STATUS ====="
systemctl is-active wazuh-manager

echo
echo "===== LOCAL RULE FILE ====="
ls -lh /var/ossec/etc/rules/local_rules.xml

echo
echo "===== EXISTING LOCAL RULES ====="
sed -n "1,220p" /var/ossec/etc/rules/local_rules.xml
'
```

At build time, `local_rules.xml` contained only one sample rule for SSH authentication failures, `100001`. For PostgreSQL we use `100100`–`100105`, separate from the existing rules.

## 5.3 Checking for Duplicate Rule IDs

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
echo "===== CHECK RULE ID COLLISIONS ====="
grep -RhnE "<rule[[:space:]]+id=\"10010[0-4]\"" \
  /var/ossec/etc/rules /var/ossec/ruleset/rules 2>/dev/null \
  || echo "PASS: IDs 100100-100104 are not in use"
'
```

Confirm that `PASS: IDs 100100-100104 are not in use` is returned.

## 5.4 Backing Up the Rule File

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
BACKUP="/var/ossec/etc/rules/local_rules.xml.backup-$(date +%Y%m%d-%H%M%S)"
cp -a /var/ossec/etc/rules/local_rules.xml "$BACKUP"
echo "Backup created: $BACKUP"
ls -l "$BACKUP"
'
```

## 5.5 Adding the Detection Rules

Add rules that use the JSON decoder as the parent rule and fire only when the `event` field matches exactly.

| Rule ID | Event | Level |
|---|---|---:|
| 100100 | Parent rule (common to JSON events) | 0 |
| 100101 | Authentication failure | 8 |
| 100102 | FATAL | 10 |
| 100103 | ERROR | 7 |
| 100104 | WARNING | 4 |
| 100105 | PANIC | 12 |

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
cat >> /var/ossec/etc/rules/local_rules.xml <<'"'"'EOF'"'"'

<group name="local,postgresql,">

  <rule id="100100" level="0">
    <decoded_as>json</decoded_as>
    <description>PostgreSQL sanitized JSON event base rule</description>
  </rule>

  <rule id="100101" level="8">
    <if_sid>100100</if_sid>
    <field name="event">^POSTGRESQL_AUTH_FAILURE$</field>
    <description>PostgreSQL authentication failure detected</description>
    <group>authentication_failed,postgresql,</group>
  </rule>

  <rule id="100102" level="10">
    <if_sid>100100</if_sid>
    <field name="event">^POSTGRESQL_FATAL$</field>
    <description>PostgreSQL FATAL event detected</description>
    <group>postgresql,fatal,</group>
  </rule>

  <rule id="100103" level="7">
    <if_sid>100100</if_sid>
    <field name="event">^POSTGRESQL_ERROR$</field>
    <description>PostgreSQL ERROR event detected</description>
    <group>postgresql,error,</group>
  </rule>

  <rule id="100104" level="4">
    <if_sid>100100</if_sid>
    <field name="event">^POSTGRESQL_WARNING$</field>
    <description>PostgreSQL WARNING event detected</description>
    <group>postgresql,warning,</group>
  </rule>

  <rule id="100105" level="12">
    <if_sid>100100</if_sid>
    <field name="event">^POSTGRESQL_PANIC$</field>
    <description>PostgreSQL PANIC event detected</description>
    <group>postgresql,critical,</group>
  </rule>

</group>
EOF

echo "===== POSTGRESQL RULES ADDED ====="
tail -n 65 /var/ossec/etc/rules/local_rules.xml
'
```

Do not restart the Manager yet.

## 5.6 Validating the Rules

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
echo "===== XML STRUCTURE VALIDATION ====="
python3 - <<'"'"'PY'"'"'
from pathlib import Path
import xml.etree.ElementTree as ET

content = Path("/var/ossec/etc/rules/local_rules.xml").read_text()
root = ET.fromstring("<config_root>\n" + content + "\n</config_root>")

rules = {
    rule.get("id"): rule
    for rule in root.findall(".//rule")
}

expected = ["100100", "100101", "100102", "100103", "100104", "100105"]

for rule_id in expected:
    if rule_id not in rules:
        raise SystemExit(f"FAIL: missing rule {rule_id}")
    print(f"PASS: rule {rule_id}")

print("PASS: XML structure is valid")
PY

echo
echo "===== WAZUH MANAGER CONFIGURATION TEST ====="
/var/ossec/bin/wazuh-analysisd -t
RESULT=$?
echo "Exit code: $RESULT"
exit "$RESULT"
'
```

It is correct if all six rules show `PASS` and `Exit code: 0`. The message about `Rule tree threshold` is an INFO message about memory use, not an error.

## 5.7 Testing with wazuh-logtest

Before restarting the Manager, use Wazuh's rule testing function to check that the five kinds of event match the intended rules. No test data enters the production log.

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
printf "%s\n" \
  "{\"timestamp\":\"2026-11-18 15:20:00 JST\",\"event\":\"POSTGRESQL_AUTH_FAILURE\"}" \
  "{\"timestamp\":\"2026-11-18 15:20:01 JST\",\"event\":\"POSTGRESQL_FATAL\"}" \
  "{\"timestamp\":\"2026-11-18 15:20:02 JST\",\"event\":\"POSTGRESQL_ERROR\"}" \
  "{\"timestamp\":\"2026-11-18 15:20:03 JST\",\"event\":\"POSTGRESQL_WARNING\"}" \
  "{\"timestamp\":\"2026-11-18 15:20:04 JST\",\"event\":\"POSTGRESQL_PANIC\"}" \
  | /var/ossec/bin/wazuh-logtest
'
```

| Event | Rule ID | Level | Result |
|---|---:|---:|---|
| Authentication failure | 100101 | 8 | Match |
| FATAL | 100102 | 10 | Match |
| ERROR | 100103 | 7 | Match |
| WARNING | 100104 | 4 | Match |
| PANIC | 100105 | 12 | Match |

Because PANIC is level 12, `mail: True` is shown. This means it would be notified if email notification were configured; no email has been sent.

## 5.8 Restarting the Manager

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
systemctl restart wazuh-manager

echo "===== MANAGER STATUS ====="
systemctl is-active wazuh-manager

echo
echo "===== RECENT MANAGER LOG ====="
journalctl -u wazuh-manager -n 25 --no-pager
'
```

It has succeeded if `active` is shown and `Started wazuh-manager.service - Wazuh manager.` is logged.

## 5.9 Checking the Agent Connection

**Run on: the Proxmox host (root@pve)**

```bash
echo "===== POSTGRESQL AGENT LOG ====="
pct exec 109 -- bash -c '
tail -n 35 /var/ossec/logs/ossec.log
'

echo
echo "===== MANAGER AGENT STATUS ====="
qm guest exec 220 -- /var/ossec/bin/agent_control -lc
```

It is normal if the LXC 109 agent log has `Connected to the server ([192.168.0.220]:1514/tcp)` and the Manager's list shows `ID: 004, Name: postgresql, IP: any, Active`. The agent is temporarily disconnected right after the Manager restarts, but it reconnects automatically.

## 5.10 End-to-End Forwarding Test

Instead of causing test SQL or authentication failures in PostgreSQL, append one fixed JSON line to the filter's output file and check everything from forwarding to detection.

> **Note:** This test records one test WARNING alert in Wazuh. Treat it as a test event so that it is not confused with a real incident.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
printf "%s\n" \
  "{\"timestamp\":\"2026-11-18 15:25:00 JST\",\"event\":\"POSTGRESQL_WARNING\"}" \
  >> /var/log/postgresql-wazuh/events.log

echo "===== TEST EVENT ====="
tail -n 1 /var/log/postgresql-wazuh/events.log

echo
echo "===== FILE PERMISSIONS ====="
stat -c "%U:%G %a %n" /var/log/postgresql-wazuh/events.log
'
```

Check whether an alert with agent ID `004` and rule ID `100104` was recorded in `alerts.json` on VM 220.

```bash
qm guest exec 220 -- bash -c '
python3 - <<'"'"'PY'"'"'
import json
from pathlib import Path

path = Path("/var/ossec/logs/alerts/alerts.json")

if not path.exists():
    raise SystemExit("FAIL: alerts.json not found")

matches = []

with path.open() as f:
    for line in f:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        rule = obj.get("rule", {})
        agent = obj.get("agent", {})

        if (
            str(rule.get("id")) == "100104"
            and str(agent.get("id")) == "004"
            and "POSTGRESQL_WARNING" in obj.get("full_log", "")
        ):
            matches.append(obj)

if matches:
    print("PASS: PostgreSQL test alert received")
    for obj in matches[-3:]:
        print(json.dumps({
            "timestamp": obj.get("timestamp"),
            "agent": obj.get("agent", {}).get("name"),
            "agent_id": obj.get("agent", {}).get("id"),
            "rule_id": obj.get("rule", {}).get("id"),
            "level": obj.get("rule", {}).get("level"),
            "description": obj.get("rule", {}).get("description")
        }, ensure_ascii=False, indent=2))
else:
    print("NOT FOUND: alert has not appeared yet")
PY
'
```

If `PASS: PostgreSQL test alert received`, `"rule_id": "100104"` and `"agent": "postgresql"` are shown, forwarding and detection from LXC 109 to VM 220 are working.

By the end of this chapter, the following mechanism is complete.

- A filter that does not forward SQL statements from the original PostgreSQL log
- JSON events that contain no user names, SQL statements or error messages
- Collection of the events by the Wazuh agent
- Classification of five kinds of events and alert generation by the Wazuh Manager

# Chapter 6: Correlation Detection of Authentication Failures

Besides single authentication failures, we detect authentication failures repeated in a short time as "suspected brute-force attacks". The current filter does not output SQL statements, user names or source IPs, so in this chapter we use the method **detect five or more authentication failures within 60 seconds on the same agent (LXC 109)**. Correlation per source IP is covered in Chapter 7.

| Item | Setting |
|---|---|
| Target event | Rule `100101` (`POSTGRESQL_AUTH_FAILURE`) |
| Grouping | Same agent |
| Time window | 60 seconds |
| Occurrences | 5 |
| Correlation rule ID | `100106` |
| Level | 12 |

We do not change the PostgreSQL settings, forward the original log, or change the firewall.

## 6.1 Checking the Existing Rules

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
echo "===== EXISTING POSTGRESQL RULES ====="
grep -n -A 65 -B 3 "PostgreSQL sanitized JSON event base rule" \
  /var/ossec/etc/rules/local_rules.xml

echo
echo "===== RULE ID COLLISION CHECK ====="
grep -nE "id=\"10010[6-9]\"|id=\"10011[0-9]\"" \
  /var/ossec/etc/rules/local_rules.xml || true

echo
echo "===== EXISTING FREQUENCY RULES ====="
grep -R -nE "frequency=|timeframe=|same_agent|same_source_ip" \
  /var/ossec/etc/rules/local_rules.xml
'
```

Confirm that the existing PostgreSQL rules `100100`–`100105` exist, that `100106`–`100119` are not in use, and that there is no existing correlation rule.

## 6.2 Backing Up the Rule File

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
BACKUP="/var/ossec/etc/rules/local_rules.xml.backup-auth-correlation-$(date +%Y%m%d-%H%M%S)"
cp -a /var/ossec/etc/rules/local_rules.xml "$BACKUP"
echo "===== BACKUP CREATED ====="
ls -l "$BACKUP"
'
```

## 6.3 Checking How Correlation Rules Are Written

Check how the standard Wazuh rules write correlation rules with `frequency` (count) and `timeframe` (time window).

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
echo "===== WAZUH CORRELATION RULE EXAMPLES ====="
grep -R -n -B 3 -A 8 \
  "frequency=.*timeframe=" \
  /var/ossec/ruleset/rules \
  --include="*.xml" | head -n 100
'
```

## 6.4 Adding the Correlation Rule

Insert rule `100106` just before the existing `100102`.

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
python3 - <<'"'"'PY'"'"'
from pathlib import Path

p = Path("/var/ossec/etc/rules/local_rules.xml")
s = p.read_text()

if "<rule id=\"100106\"" in s:
    raise SystemExit("STOP: Rule 100106 already exists")

anchor = """  <rule id="100102" level="10">"""

rule = """  <rule id="100106" level="12" frequency="5" timeframe="60">
    <if_matched_sid>100101</if_matched_sid>
    <same_agent />
    <description>PostgreSQL: Multiple authentication failures from the same agent within 60 seconds.</description>
    <mitre>
      <id>T1110</id>
    </mitre>
    <group>postgresql,authentication_failures,brute_force,</group>
  </rule>

"""

if s.count(anchor) != 1:
    raise SystemExit("STOP: Expected insertion point not found uniquely")

p.write_text(s.replace(anchor, rule + anchor, 1))
print("PASS: Rule 100106 added")
PY

echo
echo "===== NEW RULE ====="
grep -n -A 10 -B 2 "id=\"100106\"" \
  /var/ossec/etc/rules/local_rules.xml
'
```

Do not restart the Manager yet.

## 6.5 Validating the Rules

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
echo "===== XML STRUCTURE CHECK ====="
python3 - <<'"'"'PY'"'"'
from pathlib import Path
import xml.etree.ElementTree as ET

p = Path("/var/ossec/etc/rules/local_rules.xml")
content = p.read_text()

ET.fromstring("<config_root>" + content + "</config_root>")
print("PASS: XML structure")

root = ET.fromstring("<config_root>" + content + "</config_root>")
rules = [
    r for r in root.iter("rule")
    if r.get("id") == "100106"
]

if len(rules) != 1:
    raise SystemExit("FAIL: Rule 100106 count is not 1")

r = rules[0]
print("Rule ID:", r.get("id"))
print("Level:", r.get("level"))
print("Frequency:", r.get("frequency"))
print("Timeframe:", r.get("timeframe"))
PY

echo
echo "===== WAZUH RULE VALIDATION ====="
/var/ossec/bin/wazuh-analysisd -t
'
```

The XML structure and rule IDs are correct, but `wazuh-analysisd -t` gives the following warning.

```text
WARNING: Detected a deprecated field option for rule,
same_agent is not longer available.
```

In Wazuh 4.14.10, `same_agent` is deprecated. In Wazuh 4.x, correlation rules **count only events from the same agent** by default (you specify `<global_frequency />` only when you want to count across all agents). So removing the `same_agent` line does not change the counting condition.

> **Note:** Do not restart the Manager while the warning remains. Fix it with the next step before applying.

## 6.6 Removing the Deprecated Setting

Remove only the `same_agent` line. The condition of 5 times in 60 seconds stays the same.

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
python3 - <<'"'"'PY'"'"'
from pathlib import Path

p = Path("/var/ossec/etc/rules/local_rules.xml")
s = p.read_text()

old = """    <if_matched_sid>100101</if_matched_sid>
    <same_agent />
"""

new = """    <if_matched_sid>100101</if_matched_sid>
"""

if s.count(old) != 1:
    raise SystemExit("STOP: Expected rule block not found exactly once")

p.write_text(s.replace(old, new, 1))
print("PASS: Deprecated same_agent removed")
PY

echo
echo "===== CORRELATION RULE ====="
grep -n -A 9 -B 2 "id=\"100106\"" \
  /var/ossec/etc/rules/local_rules.xml

echo
echo "===== WAZUH RULE VALIDATION ====="
/var/ossec/bin/wazuh-analysisd -t
'
```

The fix is complete when `PASS: Deprecated same_agent removed` is shown and `wazuh-analysisd -t` no longer warns.

## 6.7 Correlation Test with wazuh-logtest

Send five authentication failures in a row, only inside `wazuh-logtest`. Nothing is written to the actual PostgreSQL or agent logs.

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
printf "%s\n" \
  "{\"timestamp\":\"2026-11-18 15:31:01 JST\",\"event\":\"POSTGRESQL_AUTH_FAILURE\"}" \
  "{\"timestamp\":\"2026-11-18 15:31:02 JST\",\"event\":\"POSTGRESQL_AUTH_FAILURE\"}" \
  "{\"timestamp\":\"2026-11-18 15:31:03 JST\",\"event\":\"POSTGRESQL_AUTH_FAILURE\"}" \
  "{\"timestamp\":\"2026-11-18 15:31:04 JST\",\"event\":\"POSTGRESQL_AUTH_FAILURE\"}" \
  "{\"timestamp\":\"2026-11-18 15:31:05 JST\",\"event\":\"POSTGRESQL_AUTH_FAILURE\"}" \
  | /var/ossec/bin/wazuh-logtest
'
```

| Attempt | Matched rule | Level |
|---:|---|---:|
| 1st–4th | 100101 | 8 |
| 5th | 100106 | 12 |

It has succeeded if `100106` fires on the 5th attempt with MITRE ATT&CK `T1110` (Credential Access / Brute Force).

## 6.8 Checks Before Applying

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
echo "===== WAZUH MANAGER STATUS ====="
systemctl is-active wazuh-manager

echo
echo "===== CORRELATION RULE ====="
grep -n -A 8 "id=\"100106\"" \
  /var/ossec/etc/rules/local_rules.xml

echo
echo "===== RULE VALIDATION ====="
/var/ossec/bin/wazuh-analysisd -t
'
```

## 6.9 Restarting the Manager

During the restart, the Wazuh Manager's detection stops temporarily. The agent-side settings and PostgreSQL itself are not changed.

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
systemctl restart wazuh-manager

echo "===== MANAGER STATUS ====="
systemctl is-active wazuh-manager

echo
echo "===== MANAGER START TIME ====="
systemctl show wazuh-manager -p ActiveEnterTimestamp
'
```

## 6.10 Checking That the Agents Reconnect

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
echo "===== WAZUH AGENTS ====="
/var/ossec/bin/agent_control -lc

echo
echo "===== MANAGER ERRORS ====="
journalctl -u wazuh-manager --since "2026-11-18 06:32:20" --no-pager \
  | grep -Ei "error|critical|failed|started|running" \
  | tail -n 30
'
```

Set the `--since` time slightly before the start time (UTC) shown in 6.9.

> **If an agent is not listed or shows Pending:** Right after the Manager restarts, some agents may temporarily be `Pending` (waiting to connect). In the original build, the Proxmox host's agent (001) was temporarily Pending as well, but it reconnected automatically after about a minute and a half. Do not re-register or delete the agent; check its state with the following steps.

Check the registration state of all agents.

```bash
qm guest exec 220 -- /var/ossec/bin/agent_control -l
```

If one is Pending, check the connection on that agent's side (example for the Proxmox host).

**Run on: the Proxmox host (root@pve)**

```bash
echo "===== WAZUH AGENT CONNECTION LOG ====="
grep -Ei "connect|disconnect|error|critical|server|duplicate|key" \
  /var/ossec/logs/ossec.log | tail -n 50

echo
echo "===== MANAGER CONFIGURATION ====="
grep -n -A 8 '<server>' /var/ossec/etc/ossec.conf

echo
echo "===== TCP 1514 CONNECTIVITY ====="
timeout 5 bash -c '</dev/tcp/192.168.0.220/1514' \
  && echo "TCP 1514 CONNECT OK" \
  || echo "TCP 1514 CONNECT FAILED"
```

If the log shows a reconnection and `TCP 1514 CONNECT OK`, wait a little and check the list again.

```bash
qm guest exec 220 -- /var/ossec/bin/agent_control -lc
```

It is normal when agents 001–004 are all `Active`.

## 6.11 Correlation Test over the Actual Forwarding Path

Append five test authentication-failure events to the filter's output file and check whether `100106` fires over the actual path from LXC 109 to the Manager.

> **Note:** The test events are recorded in Wazuh's production alerts. Mark them clearly as a "synthetic test" in your operation records and do not treat them as a real attack. The PostgreSQL log and database are not changed.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
for i in 1 2 3 4 5; do
  printf "{\"timestamp\":\"2026-11-18 15:34:%02d JST\",\"event\":\"POSTGRESQL_AUTH_FAILURE\"}\n" "$i" \
    >> /var/log/postgresql-wazuh/events.log
done

echo "===== SYNTHETIC TEST EVENTS ====="
tail -n 5 /var/log/postgresql-wazuh/events.log
'
```

Check the Manager's alerts.

```bash
qm guest exec 220 -- bash -c '
python3 - <<'"'"'PY'"'"'
import json
from collections import deque
from pathlib import Path

path = Path("/var/ossec/logs/alerts/alerts.json")
matches = deque(maxlen=20)

with path.open(encoding="utf-8") as f:
    for line in f:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        agent = event.get("agent", {})
        rule = event.get("rule", {})

        if agent.get("id") == "004" and rule.get("id") in ("100101", "100106"):
            matches.append({
                "timestamp": event.get("timestamp"),
                "agent": agent.get("name"),
                "rule_id": rule.get("id"),
                "level": rule.get("level"),
                "description": rule.get("description")
            })

print("===== POSTGRESQL AUTHENTICATION ALERTS =====")
for item in matches:
    print(json.dumps(item, ensure_ascii=False))

print("===== CORRELATION RESULT =====")
if any(item["rule_id"] == "100106" for item in matches):
    print("SUCCESS: Rule 100106 detected")
else:
    print("NOT YET DETECTED: Rule 100106 not found")
PY
'
```

If `SUCCESS: Rule 100106 detected` is shown, brute-force correlation detection works over the actual forwarding path as well. At build time, four single detections (100101) and one correlation detection (100106, level 12) were recorded.

By the end of this chapter, the following can be detected.

| Rule ID | Detection |
|---|---|
| 100101 | PostgreSQL authentication failure (single) |
| 100106 | Five or more authentication failures within 60 seconds on the same agent (suspected brute force, MITRE T1110) |

However, this method does not reveal the attacker's IP address. In the next chapter we safely add the source IP to the events.

# Chapter 7: Obtaining the Source IP and Prototyping an IP-Aware Filter

The correlation detection in Chapter 6 works per agent, so it does not reveal the attacker's IP address. In this chapter, while keeping the policy of not sending SQL statements or user names to Wazuh, we prepare to add the source IP to authentication-failure events.

| Item | Policy |
|---|---|
| Information forwarded | Time, event type, source IP |
| Information not forwarded | SQL statements, user names, passwords, DB names, source ports, PIDs, original log text |
| Correlation unit | Source IP address |
| Detection condition | Five or more from the same IP within 60 seconds |
| IPv4 / IPv6 | Both supported |
| Existing rules | Keep 100101 and 100106 |

## 7.1 Checking Whether Authentication-Failure Logs Contain IP Addresses

First, check whether authentication-failure lines and connection-received lines in the current log contain IP addresses. The log text and SQL statements are not shown.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- python3 - <<'PY'
import ipaddress
import re
from collections import deque
from pathlib import Path

path = Path("/var/log/postgresql/postgresql-17-main.log")

prefix = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)"
    r" \[(\d+)\]"
)

auth_re = re.compile(r"password authentication failed", re.I)
received_re = re.compile(r"connection received:", re.I)
host_re = re.compile(r'\bhost[= ]+"?([^\s",]+)"?', re.I)

def extract_ips(line):
    result = []
    for candidate in re.findall(
        r'(?<![0-9A-Fa-f:.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}'
        r'|(?<![0-9A-Fa-f:])[0-9A-Fa-f:]{2,}(?:%[0-9A-Za-z_.-]+)?',
        line
    ):
        try:
            ip = ipaddress.ip_address(candidate.split("%")[0])
            if str(ip) not in result:
                result.append(str(ip))
        except ValueError:
            pass
    return result

recent_connection = {}
matches = deque(maxlen=10)

with path.open(encoding="utf-8", errors="replace") as f:
    for line in f:
        m = prefix.match(line)
        if not m:
            continue

        timestamp, pid = m.groups()

        if received_re.search(line):
            ips = extract_ips(line)
            if ips:
                recent_connection[pid] = ips

        if auth_re.search(line):
            matches.append({
                "timestamp": timestamp,
                "pid": pid,
                "ip_in_auth_line": extract_ips(line),
                "ip_from_connection_received": recent_connection.get(pid, [])
            })

print("===== SANITIZED AUTHENTICATION LOG ANALYSIS =====")
print("auth_failure_count_in_file:", len(matches))
for item in matches:
    print(item)

print("===== RESULT =====")
if not matches:
    print("No matching authentication failure lines found.")
elif any(
    x["ip_in_auth_line"] or x["ip_from_connection_received"]
    for x in matches
):
    print("IP candidate found. Review PID association before implementation.")
else:
    print("No IP found in inspected authentication/connection lines.")
PY
```

At build time, the current log file had zero authentication failures (earlier failures had been moved to older files by rotation). So count including the rotated logs.

```bash
pct exec 109 -- python3 - <<'PY'
import gzip
import ipaddress
import re
from pathlib import Path

base = Path("/var/log/postgresql")
files = sorted(base.glob("postgresql-17-main.log*"))

auth_re = re.compile(r"password authentication failed", re.I)
prefix_re = re.compile(r"^(\S+)\s+\[(\d+)\]")
ip_re = re.compile(
    r'(?<![0-9A-Fa-f:.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}'
    r'|(?<![0-9A-Fa-f:])[0-9A-Fa-f:]{2,}'
)

def lines(path):
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
            yield from f
    else:
        with path.open(encoding="utf-8", errors="replace") as f:
            yield from f

def valid_ips(line):
    found = []
    for value in ip_re.findall(line):
        try:
            ip = str(ipaddress.ip_address(value))
            if ip not in found:
                found.append(ip)
        except ValueError:
            pass
    return found

total_auth = 0
total_connection = 0
auth_with_ip = 0

print("===== LOG FILE SUMMARY =====")

for path in files:
    count_auth = 0
    count_connection = 0
    count_auth_ip = 0

    for line in lines(path):
        if auth_re.search(line):
            count_auth += 1
            total_auth += 1
            if valid_ips(line):
                count_auth_ip += 1
                auth_with_ip += 1

        if "connection received:" in line.lower():
            count_connection += 1
            total_connection += 1

    print({
        "file": path.name,
        "auth_failures": count_auth,
        "auth_lines_with_ip": count_auth_ip,
        "connection_received": count_connection
    })

print("===== TOTAL =====")
print({
    "auth_failures": total_auth,
    "auth_lines_with_ip": auth_with_ip,
    "connection_received": total_connection
})
PY
```

Totals from the example output:

```text
===== TOTAL =====
{'auth_failures': 28, 'auth_lines_with_ip': 0, 'connection_received': 0}
```

None of the 28 past authentication failures had an IP address, and there were zero connection-received log lines. This is because `log_connections=off`, so connection-received logs are not recorded.

## 7.2 The Method Adopted

Enable PostgreSQL's `log_connections` and obtain the IP as follows.

1. When PostgreSQL accepts a connection, it logs a line containing the PID and the source IP (`LOG: connection received`).
2. If authentication fails on the same connection, an authentication-failure line is logged with the same PID.
3. The filter keeps the PID-to-IP mapping only temporarily in memory and attaches the source IP to the authentication-failure event.

Authentication failures whose IP cannot be obtained are not used for per-IP correlation; only single detection is done for them, as before.

## 7.3 Checking the PostgreSQL Settings

Before changing settings, check the current values and the conditions under which a setting takes effect (`context`).

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- runuser -u postgres -- \
  psql -X -d postgres -P pager=off -c "
SELECT
  name,
  setting,
  context,
  source
FROM pg_settings
WHERE name IN (
  'log_connections',
  'log_line_prefix',
  'log_hostname',
  'logging_collector',
  'log_destination'
)
ORDER BY name;
"
```

| Setting | Current value | Action |
|---|---|---|
| `log_connections` | off | Enable (Chapter 8) |
| `log_line_prefix` | `%m [%p] %q%u@%d ` | Contains `%p` (PID), so connection-received and authentication-failure lines can be matched by PID |
| `log_hostname` | off | Do not change (record the IP, not the DNS name) |
| `logging_collector` | off | Do not change |
| `log_destination` | stderr | Do not change |

## 7.4 Checking and Backing Up the Existing Filter

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
echo "===== FILTER SCRIPT ====="
sed -n "1,240p" /usr/local/sbin/postgresql-wazuh-filter.py

echo
echo "===== FILTER SERVICE ====="
systemctl is-active postgresql-wazuh-filter.service

echo
echo "===== FILTER OUTPUT PERMISSIONS ====="
stat -c "%U:%G %a %n" \
  /var/log/postgresql-wazuh \
  /var/log/postgresql-wazuh/events.log
'
```

Save the script before modifying it. The service is not stopped and no settings are changed.

```bash
pct exec 109 -- bash -c '
set -e

BACKUP="/usr/local/sbin/postgresql-wazuh-filter.py.backup-ip-$(date +%Y%m%d-%H%M%S)"

cp -a /usr/local/sbin/postgresql-wazuh-filter.py "$BACKUP"

echo "===== BACKUP CREATED ====="
stat -c "%U:%G %a %n" "$BACKUP"

echo
echo "===== ORIGINAL SCRIPT CHECKSUM ====="
sha256sum /usr/local/sbin/postgresql-wazuh-filter.py "$BACKUP"
'
```

If the SHA-256 of the original script and the backup match, you can restore it.

## 7.5 Prototyping the IP-Aware Filter

Do not rewrite the running script. Create the IP-aware version as a temporary file (`/tmp/postgresql-wazuh-filter-ip.py`) and test it. Even if the test fails, current log collection does not stop.

The prototype's specification is as follows.

- Get the PID and IP address from `LOG: connection received` lines.
- Match them against the PID of `FATAL: password authentication failed` lines.
- Validate IPv4 and IPv6 with the `ipaddress` module.
- Keep the PID-to-IP mapping in memory for at most 300 seconds.
- Do not output SQL statements, user names, DB names, port numbers or the original log text.
- If the IP cannot be obtained, do not output the IP field.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c 'cat > /tmp/postgresql-wazuh-filter-ip.py <<'"'"'PY'"'"'
#!/usr/bin/env python3

import ipaddress
import json
import re
import time

PREFIX = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} "
    r"\d{2}:\d{2}:\d{2}(?:\.\d+)?(?: [A-Z]{2,5})?)"
    r" \[(?P<pid>\d+)\] "
    r"(?:\S+ )?"
    r"(?P<severity>PANIC|FATAL|ERROR|WARNING|LOG):"
)

HOST = re.compile(
    r"\bhost=(?:\"([^\"]+)\"|([^\s,]+))",
    re.IGNORECASE
)

AUTH_FAILURE = re.compile(
    r"\bpassword authentication failed\b",
    re.IGNORECASE
)

EVENTS = {
    "PANIC": "POSTGRESQL_PANIC",
    "FATAL": "POSTGRESQL_FATAL",
    "ERROR": "POSTGRESQL_ERROR",
    "WARNING": "POSTGRESQL_WARNING",
}

IP_TTL = 300
MAX_CONNECTIONS = 10000

connections = {}

def extract_ip(line):
    match = HOST.search(line)
    if not match:
        return None

    value = (match.group(1) or match.group(2) or "").strip()
    value = value.strip("[]")

    if "%" in value:
        value = value.split("%", 1)[0]

    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def classify(line, now=None):
    if now is None:
        now = time.monotonic()

    match = PREFIX.match(line)
    if not match:
        return None

    timestamp = match.group("timestamp")
    pid = match.group("pid")
    severity = match.group("severity")

    # Discard stale PID/IP mappings.
    expired = [
        key for key, (_, created) in connections.items()
        if now - created > IP_TTL
    ]
    for key in expired:
        connections.pop(key, None)

    # Record the PID and source IP from the connection-received log.
    if severity == "LOG" and "connection received:" in line.lower():
        ip = extract_ip(line)

        # Do not keep an old IP when a PID is reused.
        connections.pop(pid, None)

        if ip:
            connections[pid] = (ip, now)

            while len(connections) > MAX_CONNECTIONS:
                oldest = next(iter(connections))
                connections.pop(oldest, None)

        return None

    # Discard the mapping on disconnect.
    if severity == "LOG" and "disconnection:" in line.lower():
        connections.pop(pid, None)
        return None

    if severity == "FATAL" and AUTH_FAILURE.search(line):
        event = {
            "timestamp": timestamp,
            "event": "POSTGRESQL_AUTH_FAILURE",
        }

        connection = connections.get(pid)
        if connection:
            event["source_ip"] = connection[0]

        return json.dumps(event, ensure_ascii=True) + "\n"

    if severity in EVENTS:
        event = {
            "timestamp": timestamp,
            "event": EVENTS[severity],
        }
        return json.dumps(event, ensure_ascii=True) + "\n"

    return None
PY

python3 -m py_compile /tmp/postgresql-wazuh-filter-ip.py &&
echo "Temporary filter syntax: PASS"
'
```

If `Temporary filter syntax: PASS` is shown, it has succeeded.

## 7.6 Confirming That the Temporary File Was Written to the End

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
echo "===== TEMPORARY SCRIPT: LINE COUNT ====="
wc -l /tmp/postgresql-wazuh-filter-ip.py

echo
echo "===== TEMPORARY SCRIPT: LAST 100 LINES ====="
tail -n 100 /tmp/postgresql-wazuh-filter-ip.py

echo
echo "===== PYTHON SYNTAX CHECK ====="
python3 -m py_compile /tmp/postgresql-wazuh-filter-ip.py
echo "EXIT CODE: $?"
'
```

It is correct if the file has 115 lines, the end of the `classify()` function (`return None`) is present, and `EXIT CODE: 0` is shown.

## 7.7 Discarding the PID-to-IP Mapping Right After Use

So that an old IP is not wrongly attached to another connection when the OS reuses a PID, discard the PID-to-IP mapping right after processing the authentication failure (change `connections.get` to `connections.pop`).

> Replacing a whole string can fail because of differences in how newline characters are handled. Here we rewrite the one relevant line directly.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
set -e

python3 - <<'"'"'PY'"'"'
from pathlib import Path

p = Path("/tmp/postgresql-wazuh-filter-ip.py")
lines = p.read_text().splitlines()

start = next(
    i for i, line in enumerate(lines)
    if line.strip() == "connection = connections.get(pid)"
)

if lines[start + 1].strip() != "if connection:":
    raise SystemExit("Unexpected filter structure; aborted")

lines[start] = "        connection = connections.pop(pid, None)"

p.write_text("\n".join(lines) + "\n")
PY

python3 -m py_compile /tmp/postgresql-wazuh-filter-ip.py

echo "===== UPDATED AUTH BLOCK ====="
grep -n -A 12 -B 2 "AUTH_FAILURE.search" \
  /tmp/postgresql-wazuh-filter-ip.py

echo
echo "===== SYNTAX CHECK ====="
echo "PASS"
'
```

If the updated block contains `connection = connections.pop(pid, None)`, it has succeeded.

## 7.8 Testing IPv4, IPv6 and Leak Prevention

Use simulated logs to check the following points.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
set -e

python3 - <<'"'"'PY'"'"'
import importlib.util
import json

path = "/tmp/postgresql-wazuh-filter-ip.py"
spec = importlib.util.spec_from_file_location("pgfilter", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def check(condition, message):
    if not condition:
        raise SystemExit("FAIL: " + message)
    print("PASS:", message)

# IPv4
m.connections.clear()
m.classify(
    "2026-11-18 15:40:00 JST [12345] postgres@postgres LOG: connection received: host=192.0.2.10 port=54321",
    now=100
)
result = m.classify(
    "2026-11-18 15:40:01 JST [12345] attacker@postgres FATAL: password authentication failed for user SECRET_USER",
    now=101
)
obj = json.loads(result)
check(obj.get("source_ip") == "192.0.2.10", "IPv4 PID correlation")
check(set(obj) == {"timestamp", "event", "source_ip"}, "Only approved JSON fields emitted")
check("SECRET_USER" not in result and "password authentication failed" not in result, "No username or raw authentication message")
check("54321" not in result and "12345" not in result, "No port or PID emitted")
check("12345" not in m.connections, "PID mapping cleared after authentication failure")

# IPv6
m.connections.clear()
m.classify(
    "2026-11-18 15:41:00 JST [23456] postgres@postgres LOG: connection received: host=2001:0db8:0000:0000:0000:0000:0000:0001 port=54322",
    now=200
)
result6 = m.classify(
    "2026-11-18 15:41:01 JST [23456] attacker@postgres FATAL: password authentication failed for user SECRET_USER",
    now=201
)
obj6 = json.loads(result6)
check(obj6.get("source_ip") == "2001:db8::1", "IPv6 extraction and canonicalization")

# Expired mapping
m.connections.clear()
m.classify(
    "2026-11-18 15:42:00 JST [34567] postgres@postgres LOG: connection received: host=198.51.100.20 port=54323",
    now=10
)
expired = m.classify(
    "2026-11-18 15:47:01 JST [34567] attacker@postgres FATAL: password authentication failed for user SECRET_USER",
    now=311
)
check("source_ip" not in json.loads(expired), "Expired PID mapping rejected")

# Hostname is not accepted as an IP
m.connections.clear()
m.classify(
    "2026-11-18 15:48:00 JST [45678] postgres@postgres LOG: connection received: host=attacker.example port=54324",
    now=400
)
invalid = m.classify(
    "2026-11-18 15:48:01 JST [45678] attacker@postgres FATAL: password authentication failed for user SECRET_USER",
    now=401
)
check("source_ip" not in json.loads(invalid), "Non-IP hostname rejected")

print("ALL FILTER TESTS PASSED")
PY
'
```

| Test | Expected result |
|---|---|
| IPv4 PID matching | `192.0.2.10` is attached |
| Restriction of output fields | Only three: `timestamp`, `event`, `source_ip` |
| User names and text not output | `SECRET_USER` and so on are not included |
| Port and PID not output | `54321` and `12345` are not included |
| Discard after use | After an authentication failure is processed, the PID mapping is gone |
| IPv6 normalization | Normalized to `2001:db8::1` |
| Expiry | Mappings older than 300 seconds are not used |
| Host names rejected | Host names that are not IPs are not output |

If `ALL FILTER TESTS PASSED` is shown at the end, it has succeeded. Note that this test uses simulated logs. Checking against the actual PostgreSQL log is done in the next step.

## 7.9 Checks on the Wazuh Side

To correlate per source IP in Wazuh, check the current rules and version on the Manager side.

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
echo "===== POSTGRESQL CORRELATION RULE ====="
grep -n -A 15 -B 3 -E "100101|100106" \
  /var/ossec/etc/rules/local_rules.xml

echo
echo "===== WAZUH VERSION ====="
/var/ossec/bin/wazuh-control info
'
```

Back up the rule file.

```bash
qm guest exec 220 -- bash -c '
set -e

BACKUP="/var/ossec/etc/rules/local_rules.xml.backup-ip-$(date +%Y%m%d-%H%M%S)"

cp -a /var/ossec/etc/rules/local_rules.xml "$BACKUP"

echo "===== BACKUP ====="
stat -c "%U:%G %a %n" "$BACKUP"

echo
echo "===== CHECKSUM ====="
sha256sum \
  /var/ossec/etc/rules/local_rules.xml \
  "$BACKUP"
'
```

Confirm that the standard Wazuh rules use per-source-IP correlation (`same_source_ip`).

```bash
qm guest exec 220 -- bash -c '
echo "===== SAME SOURCE IP RULE EXAMPLES ====="
grep -R -n -B 4 -A 8 "<same_source_ip" \
  /var/ossec/ruleset/rules \
  /var/ossec/etc/rules 2>/dev/null \
  | head -n 100

echo
echo "===== WAZUH LOGTEST AVAILABLE ====="
ls -l /var/ossec/bin/wazuh-logtest
'
```

If standard rules such as those for Apache or Microsoft SQL Server use `same_source_ip`, the same method can be used for PostgreSQL source-IP correlation.

> **Choice of field name:** For compatibility with Wazuh's standard source-IP correlation, the IP field name in the events is standardized on **`srcip`** rather than `source_ip` (changed in Chapter 8).

## 7.10 Checking Against the Actual Log Format

Check the leading part of the `LOG` and `FATAL` lines in the existing log. Authentication-failure lines are shown with their text replaced by `[REDACTED]`.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
echo "===== EXISTING LOG PREFIX SAMPLES ====="

grep -h -E " LOG:| FATAL:" \
  /var/log/postgresql/postgresql-17-main.log \
  | tail -n 15 \
  | sed -E "s/(password authentication failed).*/\1 [REDACTED]/"

echo
echo "===== LOG LINE PREFIX SETTING ====="

runuser -u postgres -- psql -X -d postgres -Atc \
  "SHOW log_line_prefix;"
'
```

The actual log had the following format.

```text
2026-11-18 06:07:47.992 UTC [198] LOG:  checkpoint complete: ...
```

Check whether the temporary filter's regular expression can extract the timestamp, PID and severity from the existing log.

```bash
pct exec 109 -- bash -c '
python3 - <<'"'"'PY'"'"'
import importlib.util

path = "/tmp/postgresql-wazuh-filter-ip.py"
spec = importlib.util.spec_from_file_location("pgfilter", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

count = 0

with open(
    "/var/log/postgresql/postgresql-17-main.log",
    encoding="utf-8",
    errors="replace"
) as f:
    for line in f:
        if " LOG:" not in line and " FATAL:" not in line:
            continue

        match = m.PREFIX.match(line)
        if not match:
            print("UNMATCHED:", line.rstrip()[:160])
            continue

        print(
            "MATCH:",
            "timestamp=", match.group("timestamp"),
            "pid=", match.group("pid"),
            "severity=", match.group("severity")
        )
        count += 1

        if count >= 10:
            break

print("MATCHED_LINES:", count)
PY
'
```

If `MATCHED_LINES: 10` is shown and the timestamp, PID and `LOG` are extracted from all 10 lines, the filter handles the actual log format.

> **When `log_connections` takes effect:** The `context` of `log_connections` is `superuser-backend`. In PostgreSQL 17, settings of this kind can be changed in `postgresql.conf` and take effect on a configuration reload (SIGHUP). They apply only to connections that start afterwards, not to existing connections. **No PostgreSQL restart is needed.**

In this chapter we built a prototype of the IP-aware filter and checked its behavior with both simulated logs and the actual log format. In the next chapter, we change the prototype's field name to `srcip`, put it into production, enable `log_connections`, and add a per-source-IP correlation rule.

# Chapter 8: Putting Per-Source-IP Correlation Detection into Production

Based on the prototype from Chapter 7, we put it into production in the following order.

1. Fix the prototype's regular expression and field name (`srcip`), and test
2. Change Wazuh correlation rule `100106` to work per source IP, and test
3. Enable PostgreSQL's `log_connections` (without a restart)
4. Create, test and switch production to the integrated filter (IP support plus the existing monitoring loop)
5. Apply the rules to the Wazuh Manager and do a final check with real authentication failures

## 8.1 Fixing the Prototype

Support the format in which several spaces follow the PID, and change the output IP field name to `srcip`.

> Pasting a long Python script into the terminal can break it partway so that it does not run (in the original build, too, the here-document was cut off and caused a `SyntaxError`). Here we rewrite only the two lines concerned with `sed`.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
set -e

FILE=/tmp/postgresql-wazuh-filter-ip.py

sed -i "/(?P<pid>/c\\    r\" \\\\[(?P<pid>\\\\d+)\\\\]\\\\s+\"" "$FILE"
sed -i "s/event\\[\"source_ip\"\\]/event[\"srcip\"]/" "$FILE"

python3 -m py_compile "$FILE"

echo "===== PREFIX ====="
sed -n "11,16p" "$FILE"

echo
echo "===== IP FIELD ====="
grep -nE "srcip|source_ip" "$FILE"

echo
echo "===== SYNTAX ====="
echo PASS
'
```

Example output:

```text
===== PREFIX =====
    r" \[(?P<pid>\d+)\]\s+"
    r"(?:\S+ )?"
    r"(?P<severity>PANIC|FATAL|ERROR|WARNING|LOG):"
)

HOST = re.compile(

===== IP FIELD =====
104:            event["srcip"] = connection[0]

===== SYNTAX =====
PASS
```

## 8.2 Testing the Regular Expression

Check that the following three formats are recognized.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
python3 - <<'"'"'PY'"'"'
import importlib.util

path = "/tmp/postgresql-wazuh-filter-ip.py"
spec = importlib.util.spec_from_file_location("pgfilter", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

samples = [
    "2026-11-18 06:07:47.992 UTC [198]  LOG: connection received: host=192.0.2.10",
    "2026-11-18 06:07:47.992 UTC [198] postgres@postgres LOG: connection authenticated",
    "2026-11-18 06:07:47.992 UTC [198]  FATAL: password authentication failed for user \"test\"",
]

for line in samples:
    match = m.PREFIX.match(line)
    if not match:
        print("FAIL:", line)
        raise SystemExit(1)

    print(
        "PASS:",
        "PID=", match.group("pid"),
        "SEVERITY=", match.group("severity")
    )

print("ALL PREFIX TESTS PASSED")
PY
'
```

| Format | Expected result |
|---|---|
| `LOG` with several spaces after the PID | `PID= 198 SEVERITY= LOG` |
| `LOG` with user and DB name | `PID= 198 SEVERITY= LOG` |
| Authentication-failure `FATAL` | `PID= 198 SEVERITY= FATAL` |

If `ALL PREFIX TESTS PASSED` is shown at the end, it has succeeded.

## 8.3 Testing the IP Correlation Logic

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
python3 - <<'"'"'PY'"'"'
import importlib.util
import json
import time

path = "/tmp/postgresql-wazuh-filter-ip.py"
spec = importlib.util.spec_from_file_location("pgfilter", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

now = time.monotonic()
m.connections.clear()

def check(name, condition):
    if not condition:
        raise SystemExit("FAIL: " + name)
    print("PASS:", name)

# IPv4: from connection received to authentication failure
m.classify(
    "2026-11-18 06:07:47.992 UTC [198]  LOG: connection received: host=192.0.2.10",
    now
)
event = m.classify(
    "2026-11-18 06:07:48.100 UTC [198]  FATAL: password authentication failed for user \"secret-user\"",
    now + 1
)
data = json.loads(event)
check("IPv4 PID correlation", data.get("srcip") == "192.0.2.10")
check("Sensitive text excluded", "secret-user" not in event and "password" not in event)
check("PID mapping cleared", "198" not in m.connections)

# IPv6
m.classify(
    "2026-11-18 06:08:00.000 UTC [199]  LOG: connection received: host=2001:db8::10",
    now + 2
)
event = m.classify(
    "2026-11-18 06:08:01.000 UTC [199]  FATAL: password authentication failed",
    now + 3
)
data = json.loads(event)
check("IPv6 PID correlation", data.get("srcip") == "2001:db8::10")

# TTL expiration
m.classify(
    "2026-11-18 06:09:00.000 UTC [200]  LOG: connection received: host=192.0.2.20",
    now + 4
)
event = m.classify(
    "2026-11-18 06:15:00.000 UTC [200]  FATAL: password authentication failed",
    now + 305
)
data = json.loads(event)
check("Expired IP is not attached", "srcip" not in data)

# Invalid hostname
m.classify(
    "2026-11-18 06:16:00.000 UTC [201]  LOG: connection received: host=invalid.example",
    now + 306
)
check("Invalid host rejected", "201" not in m.connections)

print("ALL IP CORRELATION TESTS PASSED")
PY
'
```

If all six items show `PASS` and `ALL IP CORRELATION TESTS PASSED` is shown, it has succeeded.

## 8.4 Changing the Correlation Rule to Work per Source IP

Add `<same_source_ip />` to rule `100106` so that the condition becomes "five or more from the same source IP within 60 seconds".

Check the current rule.

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
echo "===== POSTGRESQL CORRELATION RULE ====="

grep -n -A 14 -B 3 "100106" \
  /var/ossec/etc/rules/local_rules.xml

echo
echo "===== WAZUH LOGTEST ====="

ls -l /var/ossec/bin/wazuh-logtest

echo
echo "===== RULE FILE CHECKSUM ====="

sha256sum /var/ossec/etc/rules/local_rules.xml
'
```

Take a backup, change the rule and validate the syntax.

```bash
qm guest exec 220 -- bash -c '
set -e

RULE=/var/ossec/etc/rules/local_rules.xml
BACKUP="${RULE}.backup-sameip-$(date +%Y%m%d-%H%M%S)"

cp -a "$RULE" "$BACKUP"

python3 - <<'"'"'PY'"'"'
from pathlib import Path

p = Path("/var/ossec/etc/rules/local_rules.xml")
s = p.read_text()

old = """    <if_matched_sid>100101</if_matched_sid>
    <description>PostgreSQL: Multiple authentication failures from the same agent within 60 seconds.</description>"""

new = """    <if_matched_sid>100101</if_matched_sid>
    <same_source_ip />
    <description>PostgreSQL: 5 authentication failures from the same source IP within 60 seconds.</description>"""

if s.count(old) != 1:
    raise SystemExit("FAIL: Expected rule block not found exactly once")

p.write_text(s.replace(old, new, 1))
PY

echo "===== UPDATED RULE ====="
grep -n -A 10 -B 2 "100106" "$RULE"

echo
echo "===== BACKUP ====="
echo "$BACKUP"

echo
echo "===== RULE VALIDATION ====="
/var/ossec/bin/wazuh-analysisd -t
'
```

The rule after the change is as follows.

```xml
<rule id="100106" level="12" frequency="5" timeframe="60">
  <if_matched_sid>100101</if_matched_sid>
  <same_source_ip />
  <description>PostgreSQL: 5 authentication failures from the same source IP within 60 seconds.</description>
```

> At this point only the rule file has changed; it is not yet applied to the running Manager. The Manager is restarted in 8.9.

## 8.5 Testing the Correlation Rule

`wazuh-logtest` loads the rule file as it is at that moment. Check the following three cases.

**Five times from the same IP (100106 fires on the 5th)**

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
printf "%s\n" \
"{\"timestamp\":\"2026-11-18 07:00:01 UTC\",\"event\":\"POSTGRESQL_AUTH_FAILURE\",\"srcip\":\"192.0.2.10\"}" \
"{\"timestamp\":\"2026-11-18 07:00:02 UTC\",\"event\":\"POSTGRESQL_AUTH_FAILURE\",\"srcip\":\"192.0.2.10\"}" \
"{\"timestamp\":\"2026-11-18 07:00:03 UTC\",\"event\":\"POSTGRESQL_AUTH_FAILURE\",\"srcip\":\"192.0.2.10\"}" \
"{\"timestamp\":\"2026-11-18 07:00:04 UTC\",\"event\":\"POSTGRESQL_AUTH_FAILURE\",\"srcip\":\"192.0.2.10\"}" \
"{\"timestamp\":\"2026-11-18 07:00:05 UTC\",\"event\":\"POSTGRESQL_AUTH_FAILURE\",\"srcip\":\"192.0.2.10\"}" \
| /var/ossec/bin/wazuh-logtest
'
```

It has succeeded if the 1st to 4th are `100101` (level 8) and the 5th is `100106` (level 12, MITRE `T1110`).

**Mixed IPs (100106 does not fire)**

```bash
qm guest exec 220 -- bash -c '
printf "%s\n" \
"{\"timestamp\":\"2026-11-18 07:01:01 UTC\",\"event\":\"POSTGRESQL_AUTH_FAILURE\",\"srcip\":\"192.0.2.10\"}" \
"{\"timestamp\":\"2026-11-18 07:01:02 UTC\",\"event\":\"POSTGRESQL_AUTH_FAILURE\",\"srcip\":\"192.0.2.10\"}" \
"{\"timestamp\":\"2026-11-18 07:01:03 UTC\",\"event\":\"POSTGRESQL_AUTH_FAILURE\",\"srcip\":\"192.0.2.10\"}" \
"{\"timestamp\":\"2026-11-18 07:01:04 UTC\",\"event\":\"POSTGRESQL_AUTH_FAILURE\",\"srcip\":\"192.0.2.10\"}" \
"{\"timestamp\":\"2026-11-18 07:01:05 UTC\",\"event\":\"POSTGRESQL_AUTH_FAILURE\",\"srcip\":\"192.0.2.20\"}" \
| /var/ossec/bin/wazuh-logtest \
| grep -E "id:|level:|description:|firedtimes:"
'
```

`192.0.2.10` appears four times and `192.0.2.20` once, so it has succeeded if all five are `100101` and `100106` does not appear.

**No source IP (100106 does not fire)**

```bash
qm guest exec 220 -- bash -c '
printf "%s\n" \
"{\"timestamp\":\"2026-11-18 07:02:01 UTC\",\"event\":\"POSTGRESQL_AUTH_FAILURE\"}" \
"{\"timestamp\":\"2026-11-18 07:02:02 UTC\",\"event\":\"POSTGRESQL_AUTH_FAILURE\"}" \
"{\"timestamp\":\"2026-11-18 07:02:03 UTC\",\"event\":\"POSTGRESQL_AUTH_FAILURE\"}" \
"{\"timestamp\":\"2026-11-18 07:02:04 UTC\",\"event\":\"POSTGRESQL_AUTH_FAILURE\"}" \
"{\"timestamp\":\"2026-11-18 07:02:05 UTC\",\"event\":\"POSTGRESQL_AUTH_FAILURE\"}" \
| /var/ossec/bin/wazuh-logtest
'
```

It has succeeded if all five are `100101` and `100106` does not appear. This confirms that events with an unknown source IP are not wrongly counted as coming from the same attacker.

Finally, validate the Manager's configuration.

```bash
qm guest exec 220 -- /var/ossec/bin/wazuh-analysisd -t
```

`"exitcode" : 0` is correct (`Rule tree threshold` in `err-data` is INFO, not an error).

> `"exited" : 1` in the `qm guest exec` result means "the command has finished running". Judge the command's success by `"exitcode"`. Also, pasting the JSON shown as the result into the shell gives `command not found`, but this does not affect the system.

## 8.6 Enabling log_connections

Have PostgreSQL log connection-received entries (`connection received`) without restarting it.

### Checking the current setting and the configuration file layout

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
echo "===== POSTGRESQL CONNECTION LOG SETTINGS ====="
runuser -u postgres -- psql -X -d postgres -P pager=off -c "
SELECT name, setting, context, source, pending_restart
FROM pg_settings
WHERE name IN (
  '\''log_connections'\'',
  '\''log_disconnections'\'',
  '\''log_line_prefix'\'',
  '\''logging_collector'\''
)
ORDER BY name;
"
'
```

```bash
pct exec 109 -- bash -c '
runuser -u postgres -- psql -X -d postgres -P pager=off -c "
SHOW config_file;
SELECT name, setting, applied, error, sourcefile, sourceline
FROM pg_file_settings
WHERE name IN ('\''log_connections'\'', '\''log_disconnections'\'')
ORDER BY name, sourceline;
"
'
```

If `pg_file_settings` has no matching row, the setting is not written in any configuration file and the default `off` is used.

```bash
pct exec 109 -- bash -c '
CONF=/etc/postgresql/17/main/postgresql.conf
AUTO=/var/lib/postgresql/17/main/postgresql.auto.conf

echo "===== MAIN CONFIG ====="
grep -nEi "^[[:space:]]*(include|include_dir|include_if_exists|log_connections|log_disconnections)" "$CONF" || true

echo
echo "===== AUTO CONFIG ====="
if [ -f "$AUTO" ]; then
    grep -nEi "^[[:space:]]*(log_connections|log_disconnections)" "$AUTO" || true
else
    echo "postgresql.auto.conf not found"
fi

echo
echo "===== CONFIG DIRECTORY ====="
ls -la /etc/postgresql/17/main/conf.d 2>/dev/null || true
'
```

Confirm that `include_dir = 'conf.d'` is present and that `conf.d` is empty. Instead of editing the existing `postgresql.conf` directly, we place a dedicated configuration file in `conf.d`.

### Backup and creating the dedicated configuration file

```bash
pct exec 109 -- bash -c '
set -e
CONF=/etc/postgresql/17/main/postgresql.conf
BACKUP="${CONF}.backup-before-log-connections-$(date +%Y%m%d-%H%M%S)"

cp -a "$CONF" "$BACKUP"

echo "===== BACKUP ====="
stat -c "%U:%G %a %s %n" "$BACKUP"

echo
echo "===== CONFIG DIRECTORY PERMISSIONS ====="
stat -c "%U:%G %a %n" /etc/postgresql/17/main/conf.d
'
```

```bash
pct exec 109 -- bash -c '
set -e

CONF=/etc/postgresql/17/main/conf.d/99-wazuh-connection-logging.conf

printf "%s\n" \
  "# Wazuh PostgreSQL connection source IP collection" \
  "log_connections = on" \
  > "$CONF"

chown postgres:postgres "$CONF"
chmod 640 "$CONF"

echo "===== CREATED CONFIG ====="
stat -c "%U:%G %a %s bytes %n" "$CONF"
cat "$CONF"
'
```

### Validation before applying

```bash
pct exec 109 -- bash -c '
runuser -u postgres -- psql -X -d postgres -P pager=off -c "
SELECT sourcefile, sourceline, name, setting, applied, error
FROM pg_file_settings
WHERE name = '\''log_connections'\''
   OR error IS NOT NULL
ORDER BY sourcefile, sourceline;
"
'
```

It is correct if `log_connections` in `99-wazuh-connection-logging.conf` is `on`, `applied` is `t`, and `error` is empty.

### Reloading the configuration (no restart)

```bash
pct exec 109 -- bash -c '
set -e
runuser -u postgres -- psql -X -d postgres -v ON_ERROR_STOP=1 -c "SELECT pg_reload_conf();"
'
```

If `t` is returned, the reload has succeeded. Existing connections are not dropped; the setting applies to connections that start afterwards.

```bash
pct exec 109 -- bash -c '
runuser -u postgres -- psql -X -d postgres -P pager=off -c "
SELECT name, setting, context, source, pending_restart
FROM pg_settings
WHERE name = '\''log_connections'\'';
"
'
```

| Item | Expected value |
|---|---|
| setting | `on` |
| source | `configuration file` |
| pending_restart | `f` |

### Checking the connection-received log

```bash
pct exec 109 -- bash -c '
set -e

echo "===== CREATE TEST CONNECTION ====="
runuser -u postgres -- psql -X -d postgres -v ON_ERROR_STOP=1 -c "SELECT 1;"

echo
echo "===== RECENT CONNECTION LOG ====="
grep -E "connection received:|connection authenticated:" \
  /var/log/postgresql/postgresql-17-main.log \
  | tail -n 10
'
```

At build time, the PID and source IP were recorded as follows.

```text
[15614] [unknown]@[unknown] LOG: connection received: host=192.168.0.211 port=54188
[15614] agent@agent_memory LOG: connection authenticated: ...
```

Connections from the local socket are recorded as `host=[local]`. This is not an IP address, so the filter does not treat it as an IP.

## 8.7 Creating the Integrated Filter and Switching Production to It

The prototype has no `main()` (monitoring loop) that keeps reading the log. So we create an integrated version that keeps the production monitoring loop as is (skipping past logs, following file replacement and `copytruncate`) and adds only the IP handling.

### Backing up the production filter

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
BACKUP="/usr/local/sbin/postgresql-wazuh-filter.py.backup-before-ip-$(date +%Y%m%d-%H%M%S)"
cp -a /usr/local/sbin/postgresql-wazuh-filter.py "$BACKUP"
echo "===== BACKUP CREATED ====="
stat -c "%U:%G %a %n" "$BACKUP"
echo
echo "===== CURRENT PRODUCTION FILTER ====="
stat -c "%U:%G %a %s bytes %n" /usr/local/sbin/postgresql-wazuh-filter.py
'
```

### The integrated filter (full text of the final version)

Inside LXC 109, create `/tmp/postgresql-wazuh-filter-integrated.py` with the following content (160 lines, 3,785 bytes, SHA-256 `98481b5042866fde348a03b909a19faef54f3f24da661488481bd6c5b2bf9bf4`).

> Pasting a long file into the terminal can break it. Create it with an editor, or transfer the file into place. After creating it, always confirm with the following step that its SHA-256 matches the value above.

```python
#!/usr/bin/env python3

import ipaddress
import json
import os
import re
import time

SOURCE = "/var/log/postgresql/postgresql-17-main.log"
OUTPUT = "/var/log/postgresql-wazuh/events.log"

PREFIX = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} "
    r"\d{2}:\d{2}:\d{2}(?:\.\d+)?(?: [A-Z]{2,5})?)"
    r" \[(?P<pid>\d+)\]\s+"
    r"(?:\S+ )?"
    r"(?P<severity>PANIC|FATAL|ERROR|WARNING|LOG):"
)

HOST = re.compile(
    r"\bhost=(?:\"([^\"]+)\"|([^\s,]+))",
    re.IGNORECASE
)

AUTH_FAILURE = re.compile(
    r"\bpassword authentication failed\b",
    re.IGNORECASE
)

EVENTS = {
    "PANIC": "POSTGRESQL_PANIC",
    "FATAL": "POSTGRESQL_FATAL",
    "ERROR": "POSTGRESQL_ERROR",
    "WARNING": "POSTGRESQL_WARNING",
}

IP_TTL = 300
MAX_CONNECTIONS = 10000

connections = {}


def extract_ip(line):
    match = HOST.search(line)
    if not match:
        return None

    value = (match.group(1) or match.group(2) or "").strip()
    value = value.strip("[]")

    if "%" in value:
        value = value.split("%", 1)[0]

    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def classify(line, now=None):
    if now is None:
        now = time.monotonic()

    match = PREFIX.match(line)
    if not match:
        return None

    timestamp = match.group("timestamp")
    pid = match.group("pid")
    severity = match.group("severity")

    expired = [
        key for key, (_, created) in connections.items()
        if now - created > IP_TTL
    ]
    for key in expired:
        connections.pop(key, None)

    if severity == "LOG" and "connection received:" in line.lower():
        ip = extract_ip(line)

        connections.pop(pid, None)

        if ip:
            connections[pid] = (ip, now)

            while len(connections) > MAX_CONNECTIONS:
                oldest = next(iter(connections))
                connections.pop(oldest, None)

        return None

    if severity == "LOG" and "disconnection:" in line.lower():
        connections.pop(pid, None)
        return None

    if severity == "FATAL" and AUTH_FAILURE.search(line):
        event = {
            "timestamp": timestamp,
            "event": "POSTGRESQL_AUTH_FAILURE",
        }

        connection = connections.pop(pid, None)
        if connection:
            event["srcip"] = connection[0]

        return json.dumps(event, ensure_ascii=True) + "\n"

    if severity in EVENTS:
        event = {
            "timestamp": timestamp,
            "event": EVENTS[severity],
        }
        return json.dumps(event, ensure_ascii=True) + "\n"

    return None


def main():
    os.umask(0o027)

    with open(SOURCE, "r", encoding="utf-8", errors="replace") as source:
        source.seek(0, os.SEEK_END)

        with open(OUTPUT, "a", encoding="utf-8") as output:
            current_inode = os.stat(SOURCE).st_ino

            while True:
                line = source.readline()

                if line:
                    event = classify(line)
                    if event:
                        output.write(event)
                        output.flush()
                    continue

                time.sleep(1)

                try:
                    info = os.stat(SOURCE)
                except FileNotFoundError:
                    continue

                if info.st_ino != current_inode:
                    source.close()
                    source = open(
                        SOURCE, "r",
                        encoding="utf-8",
                        errors="replace"
                    )
                    source.seek(0, os.SEEK_END)
                    current_inode = info.st_ino

                elif info.st_size < source.tell():
                    source.seek(0)


if __name__ == "__main__":
    main()
```

### Setting owner and permissions and validating the syntax

```bash
pct exec 109 -- bash -c '
set -e

FILE=/tmp/postgresql-wazuh-filter-integrated.py

chown root:root "$FILE"
chmod 750 "$FILE"

python3 -m py_compile "$FILE"

echo "===== INTEGRATED FILTER ====="
stat -c "%U:%G %a %s bytes %n" "$FILE"
sha256sum "$FILE"

echo
echo "===== MAIN FUNCTION ====="
grep -nE "^def (classify|main)|^if __name__" "$FILE"

echo
echo "===== SYNTAX ====="
echo "PYTHON SYNTAX OK"
'
```

| Item | Expected value |
|---|---|
| Owner, permissions, size | `root:root 750 3785 bytes` |
| SHA-256 | `98481b5042866fde348a03b909a19faef54f3f24da661488481bd6c5b2bf9bf4` |
| Functions | `def classify` on line 60, `def main` on line 119, `if __name__` on line 159 |

### Checking the difference from the production version

```bash
pct exec 109 -- bash -c '
diff -u \
  /usr/local/sbin/postgresql-wazuh-filter.py \
  /tmp/postgresql-wazuh-filter-integrated.py || true
'
```

Confirm that the existing monitoring loop (skipping past logs, detecting inode changes, following `copytruncate`, JSON output) is kept and that only the IP handling has been added.

### Functional tests

```bash
pct exec 109 -- python3 - <<'PY'
import importlib.util
import json

path = "/tmp/postgresql-wazuh-filter-integrated.py"
spec = importlib.util.spec_from_file_location("pgfilter", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print("PASS:", message)

# IPv4
mod.connections.clear()
mod.classify(
    "2026-11-18 07:14:03.621 UTC [15614] [unknown]@[unknown] "
    "LOG:  connection received: host=192.168.0.211 port=54188",
    now=100
)
result = mod.classify(
    "2026-11-18 07:14:04.000 UTC [15614] FATAL: "
    "password authentication failed for user \"secret_user\" "
    "STATEMENT: SELECT 'secret_password';",
    now=101
)
event = json.loads(result)
check(event.get("srcip") == "192.168.0.211", "IPv4 PID correlation")
check(set(event) == {"timestamp", "event", "srcip"}, "No SQL or credentials in output")
check("secret" not in result, "Sensitive text excluded")

# IPv6
mod.connections.clear()
mod.classify(
    "2026-11-18 07:15:00 UTC [20001] [unknown]@[unknown] "
    "LOG:  connection received: host=2001:db8::10 port=54321",
    now=200
)
result = mod.classify(
    "2026-11-18 07:15:01 UTC [20001] FATAL: "
    "password authentication failed for user \"test\"",
    now=201
)
check(json.loads(result).get("srcip") == "2001:db8::10", "IPv6 PID correlation")

# Local connection
mod.connections.clear()
mod.classify(
    "2026-11-18 07:16:00 UTC [20002] [unknown]@[unknown] "
    "LOG:  connection received: host=[local]",
    now=300
)
check("20002" not in mod.connections, "Local socket is not treated as an IP")

# Missing IP
result = mod.classify(
    "2026-11-18 07:16:01 UTC [20002] FATAL: "
    "password authentication failed for user \"test\"",
    now=301
)
check("srcip" not in json.loads(result), "Missing IP does not create a false source")

# Normal warning
result = mod.classify(
    "2026-11-18 07:17:00 UTC [20003] postgres@postgres WARNING: "
    "synthetic warning with private details",
    now=400
)
event = json.loads(result)
check(event["event"] == "POSTGRESQL_WARNING", "WARNING event preserved")
check(set(event) == {"timestamp", "event"}, "WARNING details are sanitized")

print("ALL TESTS PASSED")
PY
```

If all eight items show `PASS` and `ALL TESTS PASSED` is shown, it has succeeded.

### Edge-case tests

Check PID reuse, expiry, invalid IPs and the mapping limit (10,000 entries).

```bash
pct exec 109 -- python3 - <<'PY'
import importlib.util
import json

path = "/tmp/postgresql-wazuh-filter-integrated.py"
spec = importlib.util.spec_from_file_location("pgfilter", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def check(condition, message):
    if not condition:
        raise AssertionError("FAIL: " + message)
    print("PASS:", message)

def received(pid, host, now):
    return mod.classify(
        f"2026-11-18 07:14:03 UTC [{pid}] "
        f"[unknown]@[unknown] LOG: connection received: host={host} port=54321",
        now=now
    )

def auth_failure(pid, now):
    result = mod.classify(
        f"2026-11-18 07:14:04 UTC [{pid}] FATAL: "
        "password authentication failed for user test",
        now=now
    )
    return json.loads(result)

# PID reuse
mod.connections.clear()
received(30001, "192.0.2.10", 100)
received(30001, "192.0.2.20", 101)
event = auth_failure(30001, 102)
check(event.get("srcip") == "192.0.2.20", "PID reuse uses latest IP")

# TTL expiration
mod.connections.clear()
received(30002, "192.0.2.30", 100)
event = auth_failure(30002, 401)
check("srcip" not in event, "Expired IP is not attached")

# Invalid host
mod.connections.clear()
received(30003, "not-an-ip", 100)
check("30003" not in mod.connections, "Invalid IP is rejected")

# Maximum connection count
mod.connections.clear()
for i in range(mod.MAX_CONNECTIONS):
    mod.connections[str(i)] = ("192.0.2.1", 100)

received(40000, "192.0.2.40", 101)
check(len(mod.connections) == mod.MAX_CONNECTIONS, "Connection map stays within limit")
check("40000" in mod.connections, "Newest connection is retained")

print("ALL EDGE TESTS PASSED")
PY
```

If `ALL EDGE TESTS PASSED` is shown, it has succeeded.

### Checking the state of the production service

```bash
pct exec 109 -- bash -c '
echo "===== SERVICE STATUS ====="
systemctl status postgresql-wazuh-filter.service --no-pager

echo
echo "===== SERVICE DEFINITION ====="
systemctl cat postgresql-wazuh-filter.service

echo
echo "===== OUTPUT FILE ====="
stat -c "%U:%G %a %s bytes %n" /var/log/postgresql-wazuh/events.log
'
```

The systemd service definition (security restrictions, limits on read and write paths) is not changed.

### Preparing to deploy to production

Place a candidate file (`.new`) next to the production file. The current service keeps running.

```bash
pct exec 109 -- bash -c '
set -e

PROD=/usr/local/sbin/postgresql-wazuh-filter.py
NEW=/usr/local/sbin/postgresql-wazuh-filter.py.new
BACKUP="${PROD}.backup-before-ip-deploy-$(date +%Y%m%d-%H%M%S)"

echo "===== CREATE BACKUP ====="
cp -a "$PROD" "$BACKUP"
stat -c "%U:%G %a %s %n" "$BACKUP"

echo
echo "===== STAGE INTEGRATED FILTER ====="
install -o root -g root -m 750 \
  /tmp/postgresql-wazuh-filter-integrated.py "$NEW"

python3 -m py_compile "$NEW"

echo
echo "===== VERIFY CHECKSUMS ====="
sha256sum /tmp/postgresql-wazuh-filter-integrated.py "$NEW"

echo
echo "===== VERIFY STAGED FILE ====="
stat -c "%U:%G %a %s %n" "$NEW"

echo
echo "===== SERVICE STILL RUNNING ====="
systemctl is-active postgresql-wazuh-filter.service
'
```

Confirm that the SHA-256 of the two files match. Note down the backup file name shown (`postgresql-wazuh-filter.py.backup-before-ip-deploy-<date-time>`), because it is used in the next step.

### Switching production

Replace the production file in one operation (`mv`) and restart only the filter service. If the restart fails, the backup is restored automatically.

> **Note 1:** `BACKUP=` in the following command contains the backup file name from the original build. Always replace it with **the file name from your own environment** shown in the previous step before running it.
>
> **Note 2:** The filter starts reading from the end of the log when it starts, so PostgreSQL events that occur during the restart (a few seconds) may not be forwarded. PostgreSQL itself, the Wazuh Manager and the Wazuh agent are not restarted.

```bash
pct exec 109 -- bash -c '
set -e

PROD=/usr/local/sbin/postgresql-wazuh-filter.py
NEW=/usr/local/sbin/postgresql-wazuh-filter.py.new
BACKUP=/usr/local/sbin/postgresql-wazuh-filter.py.backup-before-ip-deploy-20261118-162149

echo "===== FINAL CHECK ====="
test -f "$NEW"
test -f "$BACKUP"
python3 -m py_compile "$NEW"

echo
echo "===== ATOMIC DEPLOYMENT ====="
mv -f "$NEW" "$PROD"

echo
echo "===== RESTART FILTER SERVICE ====="
if ! systemctl restart postgresql-wazuh-filter.service; then
    echo "RESTART FAILED - ROLLING BACK"
    cp -a "$BACKUP" "$PROD"
    systemctl restart postgresql-wazuh-filter.service || true
    exit 1
fi

echo
echo "===== SERVICE STATUS ====="
systemctl is-active postgresql-wazuh-filter.service
systemctl status postgresql-wazuh-filter.service --no-pager -l

echo
echo "===== DEPLOYED FILE ====="
stat -c "%U:%G %a %s bytes %n" "$PROD"
sha256sum "$PROD"

echo
echo "===== RECENT SERVICE LOG ====="
journalctl -u postgresql-wazuh-filter.service -n 15 --no-pager

echo
echo "DEPLOYMENT CHECK COMPLETE"
'
```

The switch is complete if the service is `active (running)`, the SHA-256 of the production file is the same as the integrated version, and `DEPLOYMENT CHECK COMPLETE` is shown at the end.

```bash
pct exec 109 -- bash -c '
echo "===== FILTER SERVICE ====="
systemctl is-active postgresql-wazuh-filter.service

echo
echo "===== FILTER PROCESS ====="
ps -eo pid,etime,rss,args | grep "[p]ostgresql-wazuh-filter.py"

echo
echo "===== SANITIZED EVENTS ====="
tail -n 15 /var/log/postgresql-wazuh/events.log

echo
echo "===== OUTPUT PERMISSIONS ====="
stat -c "%U:%G %a %s bytes %n" /var/log/postgresql-wazuh/events.log
'
```

## 8.8 Checking with a Real Authentication Failure

### Causing one authentication failure

Try a local TCP connection to the existing user `agent` with a wrong password. No database data is changed.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
set +e

echo "===== BEFORE ====="
date -u
wc -l /var/log/postgresql-wazuh/events.log

echo
echo "===== CONTROLLED AUTH FAILURE ====="
PGPASSWORD="Wazuh-Invalid-Test-Only-2026" \
psql -h 127.0.0.1 -p 5432 -U agent -d agent_memory \
  -c "SELECT 1;" 2>&1

echo
echo "===== RECENT POSTGRESQL LOG ====="
tail -n 12 /var/log/postgresql/postgresql-17-main.log

echo
echo "===== RECENT SANITIZED EVENTS ====="
sleep 2
tail -n 8 /var/log/postgresql-wazuh/events.log
'
```

Replace the user name and database name with ones that exist in your environment. It has succeeded if an event with `srcip` is recorded in the output file, like this:

```text
{"timestamp": "2026-11-18 07:27:22.703 UTC", "event": "POSTGRESQL_AUTH_FAILURE", "srcip": "127.0.0.1"}
{"timestamp": "2026-11-18 07:27:22.716 UTC", "event": "POSTGRESQL_AUTH_FAILURE", "srcip": "127.0.0.1"}
```

> **Why one attempt records two events:** In the original build, each run of `psql` recorded two authentication failures. Both carry the same source IP, and neither contains SQL statements, user names or passwords.

### Checking that it reaches the Manager

```bash
qm guest exec 220 -- bash -c '
python3 -c "
import json
from pathlib import Path

p = Path(\"/var/ossec/logs/alerts/alerts.json\")
if not p.exists():
    raise SystemExit(\"FAIL: alerts.json not found\")

count = 0
with p.open() as f:
    for line in f:
        try:
            e = json.loads(line)
        except Exception:
            continue

        rule = e.get(\"rule\", {})
        data = e.get(\"data\", {})

        if rule.get(\"id\") in (\"100101\", \"100106\") and data.get(\"event\") == \"POSTGRESQL_AUTH_FAILURE\":
            print(json.dumps({
                \"timestamp\": e.get(\"timestamp\"),
                \"rule_id\": rule.get(\"id\"),
                \"level\": rule.get(\"level\"),
                \"srcip\": data.get(\"srcip\"),
                \"agent\": e.get(\"agent\", {}).get(\"name\")
            }, ensure_ascii=False))
            count += 1

print(\"MATCH_COUNT:\", count)
"
'
```

If this authentication failure is recorded as `"rule_id": "100101"`, `"srcip": "127.0.0.1"` and `"agent": "postgresql"`, it has reached the Manager.

## 8.9 Applying the Rules to the Manager

The rule file was changed in 8.4, but the running process uses the old rules until the Manager is restarted. Note that `wazuh-logtest` reads the file as it is at that moment, so the tests used the new rules.

> `wazuh-control reload` does not just re-read the rules. Internally it stops and restarts the Manager's services. Here we restart the Manager with systemd.

### Backup before restarting

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
echo "===== RULE BACKUPS ====="
ls -lht /var/ossec/etc/rules/local_rules.xml.backup* 2>/dev/null | head -n 10

echo
echo "===== CURRENT RULE FILE ====="
stat -c "%U:%G %a %s bytes %y %n" \
  /var/ossec/etc/rules/local_rules.xml
'
```

```bash
qm guest exec 220 -- bash -c '
set -e

BACKUP="/var/ossec/etc/rules/local_rules.xml.backup-pre-reload-$(date +%Y%m%d-%H%M%S)"

cp -a /var/ossec/etc/rules/local_rules.xml "$BACKUP"

echo "===== BACKUP CREATED ====="
stat -c "%U:%G %a %s bytes %n" "$BACKUP"

echo
echo "===== CHECKSUM ====="
sha256sum \
  /var/ossec/etc/rules/local_rules.xml \
  "$BACKUP"
'
```

Confirm that the SHA-256 of the original file and the backup match.

### Restarting the Manager

During the restart, receiving events from agents, analysis and alert generation stop temporarily.

```bash
qm guest exec 220 -- bash -c '
set -e

echo "===== RESTART WAZUH MANAGER ====="
systemctl restart wazuh-manager

echo
echo "===== SERVICE STATUS ====="
systemctl is-active wazuh-manager

echo
echo "===== ANALYSISD PROCESS ====="
pgrep -a wazuh-analysisd
'
```

It has succeeded if `active` and a new `wazuh-analysisd` process are shown.

```bash
qm guest exec 220 -- bash -c '
echo "===== WAZUH AGENT STATUS ====="
/var/ossec/bin/agent_control -lc

echo
echo "===== MANAGER RECENT ERRORS ====="
journalctl -u wazuh-manager --since "5 minutes ago" --no-pager \
  | grep -Ei "error|critical|failed" \
  | tail -n 30 || true
'
```

It is normal if agents 001–004 are all `Active` and there is no `error`, `critical` or `failed` in the last five minutes.

## 8.10 Final Check of Source-IP Correlation

Cause five authentication failures from the same source IP.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
for i in 1 2 3 4 5; do
    echo "===== FINAL AUTH FAILURE TEST $i ====="
    PGPASSWORD="Wazuh-Invalid-Test-Only-2026" \
    psql -h 127.0.0.1 -p 5432 -U agent -d agent_memory \
      -c "SELECT 1;" >/dev/null 2>&1 || true
    sleep 1
done

echo "===== TEST COMPLETED ====="
'
```

Check the correlation alert on the Manager.

```bash
qm guest exec 220 -- bash -c '
python3 - <<'"'"'PY'"'"'
import json
from pathlib import Path

path = Path("/var/ossec/logs/alerts/alerts.json")
matches = []

with path.open() as f:
    for line in f:
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue

        rule = e.get("rule", {})
        data = e.get("data", {})

        if rule.get("id") == "100106" and data.get("event") == "POSTGRESQL_AUTH_FAILURE":
            matches.append({
                "timestamp": e.get("timestamp"),
                "rule_id": rule.get("id"),
                "level": rule.get("level"),
                "srcip": data.get("srcip"),
                "agent": e.get("agent", {}).get("name"),
                "description": rule.get("description")
            })

print("===== LATEST CORRELATION ALERTS =====")
for item in matches[-5:]:
    print(json.dumps(item, ensure_ascii=False))

print("TOTAL_CORRELATION_ALERTS:", len(matches))
PY
'
```

It is complete if `100106` with the description "same source IP" is recorded, like this:

```json
{
  "timestamp": "2026-11-18T07:39:03.945+0000",
  "rule_id": "100106",
  "level": 12,
  "srcip": "127.0.0.1",
  "agent": "postgresql",
  "description": "PostgreSQL: 5 authentication failures from the same source IP within 60 seconds."
}
```

> The JSON shown as the result is output for checking. It is not something to paste into the shell and run.

## State at the End of Part 2

PostgreSQL monitoring has been completed with the following configuration.

| Stage | Processing |
|---|---|
| PostgreSQL 17 (LXC 109) | Logs authentication failures and connection-received entries (PID, source IP) |
| Sanitizing filter | Matches PIDs to source IPs, removes SQL statements, user names, passwords, etc., and converts to JSON |
| Wazuh agent (ID 004) | Forwards the JSON events to the Manager |
| Wazuh Manager (VM 220) | Single detection and per-source-IP correlation detection |

| Rule ID | Level | Detection |
|---|---:|---|
| 100101 | 8 | PostgreSQL authentication failure (single) |
| 100102 | 10 | Other FATAL |
| 100103 | 7 | ERROR |
| 100104 | 4 | WARNING |
| 100105 | 12 | PANIC |
| 100106 | 12 | Five or more authentication failures from the same source IP within 60 seconds (MITRE T1110) |

Automatic blocking has not been enabled yet. In Part 3, we build the Collector, which saves the alerts produced by Wazuh into PostgreSQL and manages them as incidents.

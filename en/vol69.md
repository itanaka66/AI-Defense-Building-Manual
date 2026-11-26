---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 69: Putting the Fixed Rules into Production"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 69 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 68 we checked the fixed `local_rules.xml` candidate in an isolated environment. Here we put it into production.

1. Save a copy of the current `local_rules.xml` and replace it with the candidate in one step
2. Run `wazuh-analysisd -t` with the production configuration
3. With `wazuh-logtest`, test whether the PostgreSQL rules fire as expected
4. Investigate what a Wazuh Manager reload does, perform it once, and have it load the rules

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)

# Chapter 1: Replacing the Production File

## 1.1 Replacing

We save a copy of the current `local_rules.xml`, with attributes and permissions, and replace it with the checked candidate in one step. No Manager restart or reload, and no other configuration changes.

> **Run on: VM 220**

```bash
set -euo pipefail

PRODUCTION=/var/ossec/etc/rules/local_rules.xml
CANDIDATE=/tmp/wazuh-rule-validation-20261124/etc/rules/local_rules.xml
BACKUP=/var/ossec/etc/rules/local_rules.xml.backup-pre-repair-20261124
TEMP=/var/ossec/etc/rules/.local_rules.xml.replacement-20261124

EXPECTED_OLD=8c78cf3147f9f81f7610d8ad1da8e1bef7a174ffd885e036abf70c76df65f8c8
EXPECTED_NEW=57fd6e21310ae595ef7e48e34f22f22f2087cde099b32aa87df249c932af3b8b

echo "===== VM220: AUTHORISED LOCAL RULES PRODUCTION REPLACEMENT ====="

test "$(id -u)" -eq 0
test -f "$PRODUCTION"
test -f "$CANDIDATE"
test ! -e "$BACKUP"
test ! -e "$TEMP"

echo
echo "--- 1. Verify source hashes ---"
test "$(sha256sum "$PRODUCTION" | awk '{print $1}')" = "$EXPECTED_OLD"
test "$(sha256sum "$CANDIDATE" | awk '{print $1}')" = "$EXPECTED_NEW"
echo "SOURCE_HASHES=PASS"

echo
echo "--- 2. Create metadata-preserving backup ---"
cp -a "$PRODUCTION" "$BACKUP"
test "$(sha256sum "$BACKUP" | awk '{print $1}')" = "$EXPECTED_OLD"
echo "BACKUP_CREATED=$BACKUP"
echo "BACKUP_HASH=PASS"

echo
echo "--- 3. Install validated candidate atomically ---"
install -o wazuh -g wazuh -m 660 "$CANDIDATE" "$TEMP"
test "$(sha256sum "$TEMP" | awk '{print $1}')" = "$EXPECTED_NEW"
mv -T "$TEMP" "$PRODUCTION"

echo
echo "--- 4. Verify production replacement ---"
stat -c '%A %U:%G %a %n' "$PRODUCTION" "$BACKUP"
sha256sum "$PRODUCTION" "$BACKUP"
test "$(sha256sum "$PRODUCTION" | awk '{print $1}')" = "$EXPECTED_NEW"
test "$(sha256sum "$BACKUP" | awk '{print $1}')" = "$EXPECTED_OLD"

python3 - "$PRODUCTION" <<'PY'
import sys
import xml.etree.ElementTree as ET

root = ET.parse(sys.argv[1]).getroot()
rules = root.findall(".//rule")
ids = [r.get("id") for r in rules]

assert root.tag == "group"
assert len(ids) == 8
assert len(ids) == len(set(ids))

print("PRODUCTION_XML_PARSE=PASS")
print("PRODUCTION_RULE_COUNT=" + str(len(ids)))
print("PRODUCTION_RULE_IDS=" + ",".join(ids))
PY

echo
echo "PRODUCTION_REPLACEMENT=PASS"
echo "BACKUP_PRESERVED=YES"
echo "WAZUH_MANAGER_RESTARTED=NO"
echo "WAZUH_MANAGER_RELOADED=NO"
```

| Item | Result |
|---|---|
| New `local_rules.xml` | same SHA256 as the candidate |
| Old file | fully saved as a copy |
| Owner and permissions | `wazuh:wazuh`, `660` |
| XML parsing | passed |
| Rule IDs | all 8 remain |

## 1.2 Testing with the Production Configuration

> **Run on: VM 220**

```bash
set -uo pipefail

PRODUCTION=/var/ossec/etc/rules/local_rules.xml
EXPECTED=57fd6e21310ae595ef7e48e34f22f22f2087cde099b32aa87df249c932af3b8b

echo "===== VM220: PRODUCTION WAZUH ANALYSISD CONFIGURATION TEST ====="

echo
echo "--- 1. Manager state before test ---"
systemctl show wazuh-manager.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p Result

PID_BEFORE=$(systemctl show wazuh-manager.service -p MainPID --value)
RESTARTS_BEFORE=$(systemctl show wazuh-manager.service -p NRestarts --value)

echo
echo "--- 2. Verify production rules hash ---"
ACTUAL=$(sha256sum "$PRODUCTION" | awk '{print $1}')
echo "PRODUCTION_RULES_SHA256=$ACTUAL"
test "$ACTUAL" = "$EXPECTED"
echo "PRODUCTION_RULES_HASH=PASS"

echo
echo "--- 3. Run Wazuh analysisd configuration test ---"
/var/ossec/bin/wazuh-analysisd -t
TEST_STATUS=$?
echo "ANALYSISD_TEST_EXIT=$TEST_STATUS"

echo
echo "--- 4. Manager state after test ---"
systemctl show wazuh-manager.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p Result

PID_AFTER=$(systemctl show wazuh-manager.service -p MainPID --value)
RESTARTS_AFTER=$(systemctl show wazuh-manager.service -p NRestarts --value)

echo
echo "--- 5. Compare manager process state ---"
echo "MAINPID_BEFORE=$PID_BEFORE"
echo "MAINPID_AFTER=$PID_AFTER"
echo "NRESTARTS_BEFORE=$RESTARTS_BEFORE"
echo "NRESTARTS_AFTER=$RESTARTS_AFTER"

if [ "$TEST_STATUS" -eq 0 ]; then
  echo "PRODUCTION_ANALYSISD_TEST=PASS"
else
  echo "PRODUCTION_ANALYSISD_TEST=FAIL"
fi

if [ "$PID_BEFORE" = "$PID_AFTER" ] && [ "$RESTARTS_BEFORE" = "$RESTARTS_AFTER" ]; then
  echo "MANAGER_PROCESS_UNCHANGED=YES"
else
  echo "MANAGER_PROCESS_UNCHANGED=NO"
fi

echo "MANAGER_RESTART_OR_RELOAD_REQUESTED=NO"
exit 0
```

The production `wazuh-analysisd -t` gave exit code `0`; the whole production configuration, including the fixed `local_rules.xml`, passed Wazuh's test.

## 1.3 Running Processes

> **Run on: VM 220**

```bash
set -euo pipefail

echo "===== VM220: WAZUH MANAGER LIVE PROCESS VERIFICATION ====="

echo
echo "--- 1. systemd service status ---"
systemctl status wazuh-manager.service --no-pager -l

echo
echo "--- 2. Actual Wazuh manager processes ---"
pgrep -a -f 'wazuh-(analysisd|remoted|logcollector|db|modulesd)' || true

echo
echo "--- 3. Service properties ---"
systemctl show wazuh-manager.service \
  -p Type -p ActiveState -p SubState -p MainPID \
  -p ControlPID -p ExecMainPID -p NRestarts -p Result

echo
echo "--- 4. Recent manager log entries ---"
tail -60 /var/ossec/logs/ossec.log

echo
echo "READ_ONLY_AUDIT=YES"
echo "MANAGER_RESTARTED=NO"
echo "MANAGER_RELOADED=NO"
```

`wazuh-manager.service` was `active (running)`, and `wazuh-analysisd` was running as PID `1721`. Whether the running process has loaded the new rules is not yet known.

# Chapter 2: Testing Rule Behavior

With `wazuh-logtest`, we feed test events one at a time. Actual PostgreSQL logs and other systems are not affected (the documentation IP address `192.0.2.10` is used).

## 2.1 Authentication Failure (100101)

> **Run on: VM 220**

```bash
set -uo pipefail

echo "===== VM220: POSTGRESQL AUTH FAILURE RULE TEST ====="

echo
echo "--- 1. Confirm rule file ---"
grep -n -A12 -B2 '<rule id="100101"' \
  /var/ossec/etc/rules/local_rules.xml

echo
echo "--- 2. Submit one synthetic JSON event to wazuh-logtest ---"
printf '%s\n' \
  '{"event":"POSTGRESQL_AUTH_FAILURE","srcip":"192.0.2.10"}' \
  | /var/ossec/bin/wazuh-logtest

echo
echo "LOGTEST_INPUT_COMPLETE=YES"
echo "PRODUCTION_DATABASE_TOUCHED=NO"
echo "MANAGER_RESTARTED=NO"
echo "MANAGER_RELOADED=NO"
```

The decoder was `json`, rule `100101`, Level `8`.

## 2.2 Brute Force (100106)

We feed five in a row from the same IP.

> **Run on: VM 220**

```bash
set -uo pipefail

echo "===== VM220: POSTGRESQL BRUTE FORCE CORRELATION TEST ====="

EVENT='{"event":"POSTGRESQL_AUTH_FAILURE","srcip":"192.0.2.10"}'

echo
echo "--- 1. Submit five events in one logtest session ---"
for i in 1 2 3 4 5; do
  printf '%s\n' "$EVENT"
done | /var/ossec/bin/wazuh-logtest

echo
echo "EXPECTED_RULE=100106"
echo "EXPECTED_LEVEL=12"
echo "EXPECTED_FREQUENCY=5"
echo "EXPECTED_SOURCE_IP=192.0.2.10"
echo "PRODUCTION_DATABASE_TOUCHED=NO"
echo "MANAGER_RESTARTED=NO"
echo "MANAGER_RELOADED=NO"
```

| Attempt | Rule, Level |
|---|---|
| 1st–4th | 100101, 8 |
| 5th | 100106, 12 (frequency 5, MITRE ATT&CK T1110 Brute Force) |

## 2.3 PANIC (100105)

> **Run on: VM 220**

```bash
set -uo pipefail

echo "===== VM220: POSTGRESQL PANIC RULE TEST ====="

echo
echo "--- 1. Confirm PANIC rule definition ---"
grep -n -A8 -B2 '<rule id="100105"' \
  /var/ossec/etc/rules/local_rules.xml

echo
echo "--- 2. Submit synthetic PANIC event ---"
printf '%s\n' \
  '{"event":"POSTGRESQL_PANIC","srcip":"192.0.2.20"}' \
  | /var/ossec/bin/wazuh-logtest

echo
echo "EXPECTED_RULE=100105"
echo "EXPECTED_LEVEL=12"
echo "EXPECTED_EVENT=POSTGRESQL_PANIC"
echo "PRODUCTION_DATABASE_TOUCHED=NO"
echo "MANAGER_RESTARTED=NO"
echo "MANAGER_RELOADED=NO"
```

## 2.4 FATAL (100102)

> **Run on: VM 220**

```bash
set -uo pipefail

echo "===== VM220: POSTGRESQL FATAL RULE TEST ====="

echo
echo "--- 1. Confirm FATAL rule definition ---"
grep -n -A7 -B2 '<rule id="100102"' \
  /var/ossec/etc/rules/local_rules.xml

echo
echo "--- 2. Submit synthetic FATAL event ---"
printf '%s\n' \
  '{"event":"POSTGRESQL_FATAL","srcip":"192.0.2.30"}' \
  | /var/ossec/bin/wazuh-logtest

echo
echo "EXPECTED_RULE=100102"
echo "EXPECTED_LEVEL=10"
echo "EXPECTED_EVENT=POSTGRESQL_FATAL"
echo "PRODUCTION_DATABASE_TOUCHED=NO"
echo "MANAGER_RESTARTED=NO"
echo "MANAGER_RELOADED=NO"
```

## 2.5 ERROR (100103)

> **Run on: VM 220**

```bash
set -uo pipefail

echo "===== VM220: POSTGRESQL ERROR RULE TEST ====="

echo
echo "--- 1. Confirm ERROR rule definition ---"
grep -n -A7 -B2 '<rule id="100103"' \
  /var/ossec/etc/rules/local_rules.xml

echo
echo "--- 2. Submit synthetic ERROR event ---"
printf '%s\n' \
  '{"event":"POSTGRESQL_ERROR","srcip":"192.0.2.31"}' \
  | /var/ossec/bin/wazuh-logtest

echo
echo "EXPECTED_RULE=100103"
echo "EXPECTED_LEVEL=7"
echo "EXPECTED_EVENT=POSTGRESQL_ERROR"
echo "PRODUCTION_DATABASE_TOUCHED=NO"
echo "MANAGER_RESTARTED=NO"
echo "MANAGER_RELOADED=NO"
```

## 2.6 WARNING (100104)

> **Run on: VM 220**

```bash
set -uo pipefail

echo "===== VM220: POSTGRESQL WARNING RULE TEST ====="

echo
echo "--- 1. Confirm WARNING rule definition ---"
grep -n -A7 -B2 '<rule id="100104"' \
  /var/ossec/etc/rules/local_rules.xml

echo
echo "--- 2. Submit synthetic WARNING event ---"
printf '%s\n' \
  '{"event":"POSTGRESQL_WARNING","srcip":"192.0.2.32"}' \
  | /var/ossec/bin/wazuh-logtest

echo
echo "EXPECTED_RULE=100104"
echo "EXPECTED_LEVEL=4"
echo "EXPECTED_EVENT=POSTGRESQL_WARNING"
echo "PRODUCTION_DATABASE_TOUCHED=NO"
echo "MANAGER_RESTARTED=NO"
echo "MANAGER_RELOADED=NO"
```

| Rule | Event | Level | Result |
|---|---|---:|---|
| 100101 | authentication failure | 8 | passed |
| 100106 | 5 authentication failures from the same IP | 12 | passed |
| 100105 | PANIC | 12 | passed |
| 100102 | FATAL | 10 | passed |
| 100103 | ERROR | 7 | passed |
| 100104 | WARNING | 4 | passed |

# Chapter 3: Having Wazuh Manager Load the Rules

## 3.1 What a Reload Does

> **Run on: VM 220**

```bash
set -uo pipefail

echo "===== VM220: WAZUH RULE RELOAD MECHANISM DISCOVERY ====="

echo
echo "--- 1. wazuh-control reload references ---"
grep -n -i -C 4 'reload' /var/ossec/bin/wazuh-control || true

echo
echo "--- 2. wazuh-control usage ---"
/var/ossec/bin/wazuh-control -h 2>&1 | head -80

echo
echo "--- 3. Current manager service state ---"
systemctl status wazuh-manager --no-pager -l | head -35

echo
echo "MANAGER_RESTARTED=NO"
echo "MANAGER_RELOADED=NO"
echo "CONFIG_CHANGED=NO"
```

```bash
set -uo pipefail

echo "===== VM220: WAZUH RELOAD IMPLEMENTATION INSPECTION ====="

echo
echo "--- 1. Reload branch ---"
sed -n '620,690p' /var/ossec/bin/wazuh-control

echo
echo "--- 2. Reload-related function definitions ---"
grep -n -E '^[[:space:]]*(reload_service|restart_service|is_systemd)\(\)' \
  /var/ossec/bin/wazuh-control || true

echo
echo "--- 3. Reload-related systemd units ---"
grep -R -n -i 'ExecReload\|reload' \
  /usr/lib/systemd/system/wazuh-manager.service \
  /lib/systemd/system/wazuh-manager.service 2>/dev/null || true

echo
echo "READ_ONLY_INSPECTION=YES"
echo "MANAGER_RESTARTED=NO"
echo "MANAGER_RELOADED=NO"
```

The systemd unit had the following `ExecReload`.

```text
ExecReload=/usr/bin/env /var/ossec/bin/wazuh-control reload
```

> **Run on: VM 220**

```bash
echo "===== VM220: WAZUH RELOAD IMPLEMENTATION ====="

echo
echo "--- 1. Reload branch ---"
sed -n '640,675p' /var/ossec/bin/wazuh-control

echo
echo "--- 2. Reload function definitions ---"
grep -n -E 'reload_service|restart_service|is_systemd' \
  /var/ossec/bin/wazuh-control | head -60

echo
echo "--- 3. Script permissions ---"
stat -c '%A %U:%G %n' /var/ossec/bin/wazuh-control

echo
echo "READ_ONLY_INSPECTION=YES"
echo "MANAGER_RESTARTED=NO"
echo "MANAGER_RELOADED=NO"
```

`wazuh-control`'s reload calls `restart_service` for everything except `wazuh-execd`, as follows.

```bash
reload)
    DAEMONS=$(echo $DAEMONS | sed 's/wazuh-execd//')
    ...
    restart_service
    ;;
```

It creates a `.restart` marker, checks the configuration with `testconfig`, stops and then starts the target daemons, and removes the marker. Because `wazuh-analysisd`, `wazuh-remoted` (agent communication), `wazuh-logcollector`, `wazuh-modulesd`, `wazuh-db`, `wazuh-authd` and others stop and start again, **this is not just rereading rules but a restart of a wide range of Manager daemons**. It also temporarily affects communication with agents.

## 3.2 Recording the State Before the Reload

> **Run on: VM 220**

```bash
set -uo pipefail

echo "===== VM220: PRE-ACTIVATION BASELINE ====="

echo
echo "--- 1. Manager service state ---"
systemctl is-active wazuh-manager
systemctl show wazuh-manager \
  -p ActiveState -p SubState -p NRestarts -p ActiveEnterTimestamp

echo
echo "--- 2. Active Wazuh agents ---"
/var/ossec/bin/agent_control -l

echo
echo "--- 3. Analysisd process ---"
pgrep -a -x wazuh-analysisd || true

echo
echo "--- 4. Current local rules hash ---"
sha256sum /var/ossec/etc/rules/local_rules.xml

echo
echo "BASELINE_ONLY=YES"
echo "MANAGER_RESTARTED=NO"
echo "MANAGER_RELOADED=NO"
```

| Item | State |
|---|---|
| Wazuh Manager | `active (running)`, NRestarts 0 |
| Analysisd | PID `1721` |
| Agents | all 4 Active |
| `local_rules.xml` | matches the SHA256 after the fix |

## 3.3 Performing One Reload

> **Run on: VM 220**

```bash
set -uo pipefail

echo "===== VM220: APPROVED WAZUH MANAGER RELOAD ====="

echo
echo "--- 1. Execute approved reload ---"
systemctl reload wazuh-manager
RELOAD_EXIT=$?
echo "RELOAD_EXIT_STATUS=$RELOAD_EXIT"

echo
echo "--- 2. Manager service state ---"
systemctl is-active wazuh-manager
systemctl show wazuh-manager \
  -p ActiveState -p SubState -p NRestarts -p ActiveEnterTimestamp

echo
echo "--- 3. Analysisd process ---"
pgrep -a -x wazuh-analysisd || true

echo
echo "--- 4. Agent connectivity ---"
/var/ossec/bin/agent_control -l

echo
echo "MANAGER_RELOAD_REQUESTED=YES"
echo "MANAGER_RESTARTED_BY_OPERATOR=NO"
```

The reload gave exit code `0`; the Manager was `active (running)`; `wazuh-analysisd` changed from PID `1721` to `60112` (a new process); NRestarts stayed at 0. Right after, agent 002 (`lxc-prometheus`) was `Pending`.

## 3.4 Agent and Rule State

> **Run on: VM 220**

```bash
set -uo pipefail

echo "===== VM220: POST-RELOAD AGENT AND RULE STATUS ====="

sleep 15

echo
echo "--- 1. Manager service ---"
systemctl is-active wazuh-manager
systemctl show wazuh-manager -p NRestarts -p ActiveState -p SubState

echo
echo "--- 2. Agent connectivity ---"
/var/ossec/bin/agent_control -l

echo
echo "--- 3. Analysisd process ---"
pgrep -a -x wazuh-analysisd || true

echo
echo "--- 4. Recent Wazuh manager errors ---"
grep -iE 'error|critical|invalid|failed|local_rules' \
  /var/ossec/logs/ossec.log | tail -40 || true

echo
echo "READ_ONLY_CHECK=YES"
```

Agent 002 also returned to Active, all 4 were normal, and there were no Manager error logs.

## 3.5 Rule Loading Records

> **Run on: VM 220**

```bash
set -uo pipefail

echo "===== VM220: POST-RELOAD RULE LOADING LOG ====="

echo
echo "--- 1. Analysisd startup and rule loading messages ---"
grep -iE 'analysisd|rules loaded|loaded.*rules|rules.*loaded|loading.*rule' \
  /var/ossec/logs/ossec.log | tail -60

echo
echo "--- 2. Current analysisd process start time ---"
ps -p "$(pgrep -xo wazuh-analysisd)" \
  -o pid=,lstart=,etime=,stat=

echo
echo "--- 3. Production rules file identity ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s' \
  /var/ossec/etc/rules/local_rules.xml
sha256sum /var/ossec/etc/rules/local_rules.xml

echo
echo "READ_ONLY_VERIFICATION=YES"
echo "MANAGER_RESTARTED_BY_OPERATOR=NO"
```

```text
2026/11/24 05:03:40 wazuh-analysisd:
INFO: Total rules enabled: '8461'

2026/11/24 05:03:40 wazuh-analysisd:
INFO: Started (pid: 60112).
```

It was recorded that the new `wazuh-analysisd` (PID `60112`) started and loaded the rules.

# Closing Notes

In Part 69 we put the fixed local rules into production and had Wazuh Manager load them.

| Item | Result |
|---|---|
| `local_rules.xml` | replaced with the fixed version (old one saved); `wazuh:wazuh`, `660` |
| Production test | `wazuh-analysisd -t` gave `0` |
| Rule tests | 100101, 100106, 100105, 100102, 100103 and 100104 all passed |
| Reload | once (restarts daemons other than `wazuh-execd`); analysisd is a new process; the 4 agents are Active |
| Rules loaded | `Total rules enabled: '8461'` |

> **Operational note:** A Wazuh Manager reload restarts a wide range of daemons, including agent communication. Record the state before doing it, and afterwards confirm that the agents have returned to Active.

In the next part, Part 70, we start building AI defense agents on top of the AI Defense Manager.

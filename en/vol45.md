---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 45: Preparing for LLM Analysis and Repairing the Wazuh Configuration File"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 45 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Volume 3 (Parts 31–44), we finished the backup and restore of the PostgreSQL that stores the events. Volume 4 moves on to threat analysis using an LLM (large language model).

We do not give the LLM direct authority over defensive operations. The LLM only produces material for decisions and proposals, kept separate from the actual operations. As a precondition, we check the reliability of the data passed to the LLM. Part 45 does the following.

1. Check the layout and state of the existing environment (Wazuh, PostgreSQL, Ollama, AI Defense Manager), read-only
2. Find that the Wazuh Manager configuration file `/var/ossec/etc/ossec.conf` is broken as XML, and investigate why
3. Save a copy of the configuration file, repair it, and check it with Wazuh's test command (Wazuh is not restarted)

## About Volume 4

In Volume 4, centered on the AI Defense Manager (VM 230), we build the mechanisms for running LLM analysis safely. We narrow the input passed to the LLM with an allowlist, mask the LLM's output and keep approval decisions on the server side, and add token authentication to the API. We then build a mechanism for detecting log tampering (FSS), fix Wazuh's local rules, and finally start building AI defense agents.

| Part | Content |
|---|---|
| Part 45 | Preparing for LLM Analysis and Repairing the Wazuh Configuration File |
| Part 46 | Classifying Alerts and Deciding Which Fields to Pass to the LLM |
| Part 47 | Examining the Existing AI Defense Manager Implementation |
| Part 48 | Narrowing the Wazuh Event Conversion to Seven Fields |
| Part 49 | Narrowing the Fields Returned by the Relay to Seven |
| Part 50 | Deploying the New Code and a Static Address for VM 230 |
| Part 51 | Verifying TLS and Authentication from VM 230 to the Relay |
| Part 52 | Fetching Real Alerts and Fixing the Relay's 502 |
| Part 53 | Checking the Flow from Analysis to Storage |
| Part 54 | Masking LLM Output and the Approval Policy |
| Part 55 | Integration Checks and Preparing for High Request Volumes |
| Part 56 | Reviewing and Designing API Authentication |
| Part 57 | Building Token Authentication for the API |
| Part 58 | Hardening Token Handling and the CLI |
| Part 59 | Putting API Authentication into Production |
| Part 60 | Keeping Error Responses and Logs from Leaking Information |
| Part 61 | Checking Logs for Secrets and Capping the Journal Size |
| Part 62 | Creating FSS Keys to Guard Against Log Tampering |
| Part 63 | Moving the FSS Verification Key to the Proxmox Host |
| Part 64 | Running and Checking FSS Sealing |
| Part 65 | Checking FSS from Another Host (VM 240) |
| Part 66 | Automating FSS Verification Every 15 Minutes |
| Part 67 | Finding the Breakage in Wazuh's Local Rules |
| Part 68 | Testing the Fixed Rules in an Isolated Environment |
| Part 69 | Putting the Fixed Rules into Production |
| Part 70 | Starting to Build the AI Defense Agents |
| Part 71 | Correlation, Orchestration and Defense Decision Agents |

It assumes the same environment as Volumes 1, 2 and 3 (Proxmox, VM 220 security-core, VM 230 ai-defense-manager, VM 101 ollama-gpu, LXC 109 PostgreSQL and so on).

## Downloading the Scripts

The scripts used in this book can be downloaded from:

https://github.com/itanaka66/AI-Defense-Building-Manual/releases

## Volumes and Parts

Because the build records are long, this manual is divided into the following four volumes. Part numbers run continuously across volumes.

| Volume | Parts | Main topics |
|---|---|---|
| Volume 1 | Parts 1–23 | Defense foundation (Wazuh, Collector, PostgreSQL, monitoring), AI Defense Manager, a search user for Wazuh, the relay API (Relay), AI analysis and its protection, checks |
| Volume 2 | Parts 24–30 | Enabling and verifying the Wazuh Indexer audit log; checking, recovering and preventing recurrence for the Collector |
| Volume 3 | Parts 31–44 | Handling log switching and recovering missing events, monitoring with Prometheus and testing the rules, checking PostgreSQL, backups (logical, LXC, ZFS snapshots) and restore testing, the TrueNAS destination, handling failures after a reboot |
| Volume 4 | Parts 45–71 | Safe input and output for LLM analysis (allowlists, masking, approval policy), integration with the Relay, API token authentication, checking errors and logs, detecting log tampering (FSS), repairing Wazuh local rules, AI defense agents |

**Volume 1**

| Part | Title |
|---|---|
| Part 1 | Building the Defense Foundation and Monitoring with Wazuh |
| Part 2 | Safely Monitoring PostgreSQL Logs and Correlation Detection |
| Part 3 | Building the Alert-Storage Collector |
| Part 4 | Auditing the Collector and Developing a Hardened Version |
| Part 5 | Deploying the Hardened Collector to Production |
| Part 6 | Verifying Data Integrity and Auditing Operations |
| Part 7 | Finishing the Collector's Fault Tolerance |
| Part 8 | Building the Integrated Monitoring Platform |
| Part 9 | Recovering from a Collector Stop and Checking Operations |
| Part 10 | Handling a Disk Failure and Preparing the AI Defense Manager |
| Part 11 | Laying the Groundwork for the AI Defense Manager |
| Part 12 | Investigating the AI Analysis Service and Wazuh Integration |
| Part 13 | A Read-Only User for Wazuh Indexer |
| Part 14 | Building the Alert Relay API (Relay) |
| Part 15 | Passing the Relay Connection Details Safely to VM 230 |
| Part 16 | Connecting Wazuh Alerts to AI Analysis |
| Part 17 | Running the AI Defense Manager as a Service and Its Startup Order |
| Part 18 | Keeping the Analysis History in SQLite |
| Part 19 | Minimizing the Information Passed to the LLM |
| Part 20 | Fixing Confidence Scores and Protecting Stored Data |
| Part 21 | Switching SSH on VM 230 to Public-Key Authentication |
| Part 22 | Checking the Relay and Its Connection Details |
| Part 23 | Investigating Indexer Permissions and the Audit Log |

**Volume 2**

| Part | Title |
|---|---|
| Part 24 | Finding Out Why the Audit Log Is Not Saved |
| Part 25 | Setting Where the Audit Log Is Saved |
| Part 26 | Not Recording Request Bodies in the Audit Log |
| Part 27 | Confirming That the Audit Log Is Saved |
| Part 28 | Checking the Collector and Why It Stopped |
| Part 29 | Restarting the Collector Without Missing Any Events |
| Part 30 | Keeping the Collector from Stopping for the Same Reason |

**Volume 3**

| Part | Title |
|---|---|
| Part 31 | Why the Collector Cannot Read After Log Switching, and the Fix |
| Part 32 | Confirming an Actual Switch and Recovering Missing Events |
| Part 33 | Monitoring the Collector's State with Prometheus |
| Part 34 | Monitoring the Wazuh Platform's State with Prometheus |
| Part 35 | Testing the Alert Rules and Checking in Production |
| Part 36 | Checking PostgreSQL |
| Part 37 | Backing Up PostgreSQL and Testing a Restore |
| Part 38 | Using TrueNAS as the Backup Destination |
| Part 39 | Registering the Destination and Preparing Scheduled Backups |
| Part 40 | Completing the PostgreSQL Logical Backup |
| Part 41 | Backing Up LXC 109 and Testing an Isolated Restore |
| Part 42 | Protecting the Backups and TrueNAS Snapshots |
| Part 43 | Backup Failures After a Reboot and the Recovery |
| Part 44 | Comparing the Restored Databases with Production |

**Volume 4**

| Part | Title |
|---|---|
| Part 45 | Preparing for LLM Analysis and Repairing the Wazuh Configuration File |
| Part 46 | Classifying Alerts and Deciding Which Fields to Pass to the LLM |
| Part 47 | Examining the Existing AI Defense Manager Implementation |
| Part 48 | Narrowing the Wazuh Event Conversion to Seven Fields |
| Part 49 | Narrowing the Fields Returned by the Relay to Seven |
| Part 50 | Deploying the New Code and a Static Address for VM 230 |
| Part 51 | Verifying TLS and Authentication from VM 230 to the Relay |
| Part 52 | Fetching Real Alerts and Fixing the Relay's 502 |
| Part 53 | Checking the Flow from Analysis to Storage |
| Part 54 | Masking LLM Output and the Approval Policy |
| Part 55 | Integration Checks and Preparing for High Request Volumes |
| Part 56 | Reviewing and Designing API Authentication |
| Part 57 | Building Token Authentication for the API |
| Part 58 | Hardening Token Handling and the CLI |
| Part 59 | Putting API Authentication into Production |
| Part 60 | Keeping Error Responses and Logs from Leaking Information |
| Part 61 | Checking Logs for Secrets and Capping the Journal Size |
| Part 62 | Creating FSS Keys to Guard Against Log Tampering |
| Part 63 | Moving the FSS Verification Key to the Proxmox Host |
| Part 64 | Running and Checking FSS Sealing |
| Part 65 | Checking FSS from Another Host (VM 240) |
| Part 66 | Automating FSS Verification Every 15 Minutes |
| Part 67 | Finding the Breakage in Wazuh's Local Rules |
| Part 68 | Testing the Fixed Rules in an Isolated Environment |
| Part 69 | Putting the Fixed Rules into Production |
| Part 70 | Starting to Build the AI Defense Agents |
| Part 71 | Correlation, Orchestration and Defense Decision Agents |

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)
  - **VM 220**: security-core (root). Log in as root from the Console of VM 220 in the Proxmox web interface

# Chapter 1: Checking the Current Environment

Here we create no new VMs or containers, and change or restart nothing.

## 1.1 Layout of Containers and VMs

> **Run on: pve**

```bash
echo "===== PVE CONTAINERS (ID < 400) ====="
pct list | awk 'NR == 1 || $1 < 400'

echo
echo "===== CONTAINER IDENTITIES AND NETWORK CONFIG ====="
for CT in $(pct list | awk 'NR > 1 && $1 < 400 {print $1}'); do
    echo
    echo "--- CT${CT} ---"
    pct config "$CT" | grep -E '^(hostname|net[0-9]+|unprivileged|onboot):'
done

echo
echo "===== VIRTUAL MACHINES ====="
qm list

echo
echo "===== OLLAMA VM101 STATUS ====="
qm status 101

echo
echo "===== CT109 STATUS ====="
pct status 109

echo
echo "===== CT310 STATUS ====="
pct status 310
```

| Role | Location |
|---|---|
| Wazuh | VM 220 `security-core` |
| AI Defense Manager | VM 230 `ai-defense-manager` |
| LLM inference (Ollama) | VM 101 `ollama-gpu` (running) |
| PostgreSQL | CT 109 (production), CT 310 (for verifying the isolated restore) |
| Vector search | CT 134 `qdrant` |
| Monitoring | CT 103 Prometheus, CT 105 Grafana |

## 1.2 State of Each Node

> **Run on: pve**

```bash
echo "===== VM CONFIGURATION: SECURITY CORE ====="
qm config 220 | grep -E '^(name|memory|cores|net[0-9]+|agent|onboot):'

echo
echo "===== VM CONFIGURATION: AI DEFENSE MANAGER ====="
qm config 230 | grep -E '^(name|memory|cores|net[0-9]+|agent|onboot):'

echo
echo "===== VM CONFIGURATION: OLLAMA ====="
qm config 101 | grep -E '^(name|memory|cores|net[0-9]+|agent|onboot):'

echo
echo "===== QEMU GUEST AGENT AVAILABILITY ====="
for VM in 220 230 101; do
    echo "--- VM${VM} ---"
    qm guest cmd "$VM" ping 2>&1
done

echo
echo "===== CT109 POSTGRESQL HEALTH ====="
pct exec 109 -- bash -c '
systemctl is-active postgresql
pg_isready -h 127.0.0.1
ss -lntp | grep ":5432 "
'

echo
echo "===== CT134 QDRANT HEALTH ====="
pct exec 134 -- bash -c '
systemctl is-active qdrant 2>/dev/null || true
ss -lntp | grep -E ":6333|:6334" || true
'

echo
echo "===== CT129 OPEN WEBUI PROCESS ====="
pct exec 129 -- bash -c '
systemctl --no-pager --type=service --state=running 2>/dev/null |
grep -Ei "open.?webui|docker|podman" || true
'
```

PostgreSQL, Qdrant and Open WebUI are running and can be used as they are. VMs 220, 230 and 101 did not respond through the QEMU Guest Agent at this point (which does not mean the VMs are stopped).

## 1.3 Wazuh State

VM 220's address is `192.168.0.220`. Through the Guest Agent, we check the Wazuh services and listening ports.

> **Run on: pve**

```bash
echo "===== VM220 NETWORK INTERFACES ====="
qm guest cmd 220 network-get-interfaces

echo
echo "===== VM220 WAZUH SERVICE STATUS ====="
qm guest exec 220 -- bash -lc '
for SVC in wazuh-manager wazuh-indexer wazuh-dashboard; do
    printf "%-20s " "$SVC"
    systemctl is-active "$SVC" 2>/dev/null || true
done
'

echo
echo "===== VM220 WAZUH LISTENING PORTS ====="
qm guest exec 220 -- bash -lc '
ss -lntup 2>/dev/null |
grep -E ":(1514|1515|55000|9200|9300|443|55001)([[:space:]]|$)" || true
'

echo
echo "===== VM220 WAZUH VERSION ====="
qm guest exec 220 -- bash -lc '
if command -v /var/ossec/bin/wazuh-control >/dev/null 2>&1; then
    /var/ossec/bin/wazuh-control info 2>/dev/null | head -30
else
    echo "wazuh-control not found"
fi
'
```

The three services, Wazuh Manager 4.14.10, Indexer and Dashboard, were all `active`, and the agent communication ports 1514/1515 and the API port 55000 were listening. The Indexer's 9200/9300 are localhost only.

## 1.4 The Path from Wazuh to PostgreSQL

We do not display secrets in configuration files or alert bodies; we only check service names and whether processes exist.

> **Run on: pve**

```bash
echo "===== CT109: WAZUH / COLLECTOR SERVICES ====="
pct exec 109 -- bash -c '
systemctl list-units --type=service --state=running --no-pager |
grep -Ei "wazuh|collector|security|alert|agent" || true
'

echo
echo "===== CT109: RELATED PROCESSES (NAMES ONLY) ====="
pct exec 109 -- bash -c '
ps -eo comm= |
sort -u |
grep -Ei "wazuh|collector|python|postgres" || true
'

echo
echo "===== CT109: LISTENING PORTS ====="
pct exec 109 -- bash -c '
ss -lntp |
grep -E ":5432([[:space:]]|$)" || true
'

echo
echo "===== VM220: WAZUH INTEGRATION CONFIGURATION (SAFE SUMMARY) ====="
qm guest exec 220 -- bash -lc '
python3 - <<'"'"'PY'"'"'
import xml.etree.ElementTree as ET
p="/var/ossec/etc/ossec.conf"
try:
    root=ET.parse(p).getroot()
    for tag in ("alerts","logging","integration","remote","auth"):
        for e in root.findall(tag):
            if tag == "integration":
                print("integration:",
                      "name="+str(e.findtext("name")),
                      "group="+str(e.findtext("group")),
                      "alert_format="+str(e.findtext("alert_format")))
            elif tag == "alerts":
                print("alerts:",
                      {x.tag:x.text for x in e if x.tag in
                       ("log_alert_level","email_alert_level","use_geoip","jsonout","alerts_log")})
            elif tag == "logging":
                print("logging:",
                      {x.tag:x.text for x in e if x.tag in
                       ("log_format","log_level","jsonout_output")})
            else:
                print(tag+": configured")
except Exception as ex:
    print("CONFIG_READ_ERROR:",type(ex).__name__)
PY
'
```

On CT 109, `wazuh-agent.service`, `postgresql-wazuh-filter.service` and PostgreSQL (5432) were running. For LLM analysis, rather than passing data directly from Wazuh Manager to the LLM, our policy is to use masked events as the input boundary.

On the other hand, retrieving a summary of `ossec.conf` on VM 220 gave `CONFIG_READ_ERROR: ParseError`.

# Chapter 2: Finding Where the Configuration File Is Broken

## 2.1 Position of the Error

> **Run on: pve**

```bash
echo "===== CT109: FILTER SERVICE METADATA ====="
pct exec 109 -- systemctl show postgresql-wazuh-filter.service \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p User \
  -p FragmentPath

echo
echo "===== CT109: FILTER PROCESS EXECUTABLE ====="
pct exec 109 -- bash -c '
PID=$(systemctl show postgresql-wazuh-filter.service -p MainPID --value)
if [ -n "$PID" ] && [ "$PID" != "0" ]; then
    printf "PID=%s\n" "$PID"
    readlink "/proc/$PID/exe"
    readlink "/proc/$PID/cwd"
fi
'

echo
echo "===== VM220: OSSEC XML PARSE ERROR LOCATION ====="
qm guest exec 220 -- bash -lc '
python3 - <<'"'"'PY'"'"'
import xml.etree.ElementTree as ET
p="/var/ossec/etc/ossec.conf"
try:
    ET.parse(p)
    print("XML_PARSE=OK")
except ET.ParseError as e:
    print("XML_PARSE=ERROR")
    print("DETAIL=",str(e))
    print("POSITION=",getattr(e,"position",None))
PY
'

echo
echo "===== VM220: OSSEC CONFIG FILE METADATA ====="
qm guest exec 220 -- bash -lc '
stat -c "SIZE=%s bytes MODIFIED=%y OWNER=%U:%G MODE=%a" /var/ossec/etc/ossec.conf
'
```

`/var/ossec/etc/ossec.conf` could not be read by a standard XML parser because **after line 323 there is content outside the XML document's root element**. Even though the Wazuh services are `active`, the configuration cannot be called correct.

## 2.2 Structure Around the Error

We look only at the tag structure without showing values.

> **Run on: pve**

```bash
echo "===== VM220: XML STRUCTURE AROUND PARSE ERROR ====="
qm guest exec 220 -- bash -lc '
python3 - <<'"'"'PY'"'"'
import re
p="/var/ossec/etc/ossec.conf"
with open(p, encoding="utf-8", errors="replace") as f:
    lines=f.readlines()

for n in range(315, min(len(lines), 335)+1):
    s=lines[n-1].strip()
    if not s or s.startswith("<!--"):
        continue
    tags=re.findall(r"<\s*/?\s*[A-Za-z_][\w:.-]*", s)
    if tags:
        print(f"{n}: TAGS={tags}")
    else:
        print(f"{n}: NON_TAG_LINE (content hidden)")
print("TOTAL_LINES=",len(lines))
PY
'

echo
echo "===== CT109: FILTER SERVICE EXECUTION METADATA ====="
pct exec 109 -- systemctl show postgresql-wazuh-filter.service \
  -p ExecStart \
  -p ExecStartPre \
  -p Restart \
  -p RestartUSec

echo
echo "===== CT109: FILTER SERVICE JOURNAL SUMMARY ====="
pct exec 109 -- journalctl -u postgresql-wazuh-filter.service \
  --since "2026-11-23 00:00:00" \
  --no-pager -o short-iso |
tail -30 |
sed -E 's/(password|token|secret|api[_-]?key)[=:][^ ]*/\1=[REDACTED]/Ig'
```

After the first root element closed with `</ossec_config>` on line 321, a second `<ossec_config>` began on line 323. The configuration block added last had been placed outside the original root element.

## 2.3 How Long It Has Been Like This

> **Run on: pve**

```bash
echo "===== VM220: WAZUH MANAGER PROCESS TIMESTAMPS ====="
qm guest exec 220 -- bash -lc '
systemctl show wazuh-manager \
  -p ActiveState \
  -p SubState \
  -p ActiveEnterTimestamp \
  -p ExecMainStartTimestamp \
  -p MainPID
'

echo
echo "===== VM220: WAZUH MANAGER CONFIG-RELATED JOURNAL ====="
qm guest exec 220 -- bash -lc '
journalctl -u wazuh-manager --since "2026-11-17 00:00:00" \
  --no-pager -o short-iso 2>/dev/null |
grep -Ei "error|invalid|xml|configuration|config.*fail|started|reload" |
tail -60
'

echo
echo "===== VM220: WAZUH CONFIG FILE TIMESTAMP ====="
qm guest exec 220 -- bash -lc '
stat -c "MODIFIED=%y SIZE=%s" /var/ossec/etc/ossec.conf
'

echo
echo "===== VM220: WAZUH MANAGER PID START ====="
qm guest exec 220 -- bash -lc '
PID=$(systemctl show wazuh-manager -p MainPID --value)
if [ -n "$PID" ] && [ "$PID" != "0" ]; then
    ps -p "$PID" -o pid=,lstart=,comm=
fi
'
```

| Item | Result |
|---|---|
| `ossec.conf` last modified | November 17 |
| Wazuh Manager start records | every day, November 18–22 |
| Last start | November 22 21:52 UTC (November 23 06:52 JST) |

Wazuh Manager had been starting with the broken XML since at least November 18.

## 2.4 Contents of the Added Block

> **Run on: pve**

```bash
echo "===== VM220: OSSEC CONFIG EXTRA BLOCK TAGS ====="
qm guest exec 220 -- /usr/bin/python3 -c '
import re
p="/var/ossec/etc/ossec.conf"
with open(p, encoding="utf-8") as f:
    lines=f.readlines()
for i,line in enumerate(lines[322:],323):
    tags=re.findall(r"</?([A-Za-z_][A-Za-z0-9_.:-]*)\b",line)
    if tags:
        print(i, tags)
    elif line.strip():
        print(i, "CONTENT_PRESENT")
'
```

```bash
echo "===== VM220: EXTRA LOCALFILE INPUTS (SAFE FIELDS ONLY) ====="
qm guest exec 220 -- /usr/bin/python3 -c '
import re
p="/var/ossec/etc/ossec.conf"
with open(p, encoding="utf-8") as f:
    lines=f.readlines()

for start,end in [(324,327),(329,332),(334,337)]:
    block="".join(lines[start-1:end])
    fmt=re.search(r"<log_format>\s*(.*?)\s*</log_format>",block,re.S)
    loc=re.search(r"<location>\s*(.*?)\s*</location>",block,re.S)
    print("BLOCK_LINES=%d-%d" % (start,end))
    print("LOG_FORMAT=%s" % (fmt.group(1).strip() if fmt else "NOT_FOUND"))
    print("LOCATION=%s" % (loc.group(1).strip() if loc else "NOT_FOUND"))
'
```

Lines 323–339 contained three `<localfile>` entries enclosed in the second `<ossec_config>`.

| Target | Format | Purpose |
|---|---|---|
| journald | journald | the systemd journal |
| `/var/ossec/logs/active-responses.log` | syslog | Wazuh Active Response records |
| `/var/log/dpkg.log` | syslog | records of Debian package operations |

The natural fix is to move these into the first `<ossec_config>` rather than delete them. Before that, we check whether the original block already has the same settings.

## 2.5 Checking from the Console

At this point, running commands through the Guest Agent (`guest-exec`) began to time out. VM 220 is `running` and the Guest Agent ping succeeds, so instead of restarting VM 220 or reinstalling the Guest Agent, we log in as root from **VM 220 → Console** in the Proxmox web interface and check there.

> **Run on: VM 220**

```bash
echo "===== GUEST AGENT SERVICE ====="
systemctl is-active qemu-guest-agent
systemctl status qemu-guest-agent --no-pager -l | head -25

echo
echo "===== WAZUH MANAGER STATUS ====="
systemctl is-active wazuh-manager
systemctl status wazuh-manager --no-pager -l | head -25

echo
echo "===== OSSEC LOCALFILE DEFINITIONS ====="
python3 - <<'PY'
import xml.etree.ElementTree as ET

p = "/var/ossec/etc/ossec.conf"
s = open(p, encoding="utf-8").read()
s = s.split("</ossec_config>", 1)[0] + "</ossec_config>"

root = ET.fromstring(s)
for i, e in enumerate(root.findall("localfile"), 1):
    print(
        f"LOCALFILE {i}: "
        f"FORMAT={e.findtext('log_format')} "
        f"LOCATION={e.findtext('location')}"
    )
PY
```

Both the Guest Agent (`qemu-guest-agent`) and Wazuh Manager were running.

> **Run on: VM 220**

```bash
python3 - <<'PY'
import re
import xml.etree.ElementTree as ET

p = "/var/ossec/etc/ossec.conf"
with open(p, encoding="utf-8") as f:
    content = f.read()

blocks = re.findall(
    r"<ossec_config\b[^>]*>.*?</ossec_config\s*>",
    content,
    flags=re.DOTALL
)

print(f"OSSEC_CONFIG_BLOCKS={len(blocks)}")

for block_no, block in enumerate(blocks, 1):
    print(f"\n===== BLOCK {block_no} =====")
    try:
        root = ET.fromstring(block)
    except ET.ParseError as e:
        print(f"PARSE_ERROR={e}")
        continue

    entries = root.findall("localfile")
    print(f"LOCALFILE_COUNT={len(entries)}")

    for i, entry in enumerate(entries, 1):
        fmt = entry.findtext("log_format")
        location = entry.findtext("location")
        child_tags = [child.tag for child in entry]
        print(
            f"LOCALFILE {i}: "
            f"FORMAT={fmt!r} "
            f"LOCATION={location!r} "
            f"CHILD_TAGS={child_tags}"
        )
PY
```

| Block | Number of `localfile` | Contents |
|---|---|---|
| First (the proper root element) | 3 | 1 `command`, 2 `full_command` |
| Second (after line 323) | 3 | 1 journald, 2 syslog |

The formats and sources differ, so these are not duplicates. We keep all six.

# Chapter 3: Repairing the Configuration File

## 3.1 Saving a Copy and Repairing

We do the following. Wazuh is not restarted and no services are changed.

1. Save the current `ossec.conf` to another file
2. Remove only the outer frame of the second `<ossec_config>` and move the three entries inside it into the first block
3. Check the XML syntax, the number of settings and the SHA256

> **Run on: VM 220**

```bash
echo "===== WAZUH CONFIG BACKUP AND REPAIR ====="

python3 - <<'PY'
import os
import re
import stat
import shutil
import hashlib
import tempfile
import datetime
import xml.etree.ElementTree as ET

path = "/var/ossec/etc/ossec.conf"

with open(path, "rb") as f:
    original = f.read()

text = original.decode("utf-8")

opens = list(re.finditer(r"<ossec_config\s*>", text))
closes = list(re.finditer(r"</ossec_config\s*>", text))

if len(opens) != 2 or len(closes) != 2:
    raise SystemExit(
        f"ABORT: Expected exactly 2 config blocks; "
        f"found opens={len(opens)}, closes={len(closes)}"
    )

if not (
    opens[0].start() < closes[0].start()
    < opens[1].start() < closes[1].start()
):
    raise SystemExit("ABORT: Unexpected config block ordering")

if text[closes[1].end():].strip():
    raise SystemExit("ABORT: Unexpected content after second config block")

# Extract the contents of the second block, excluding its outer tags.
second_content = text[opens[1].end():closes[1].start()]

# Preserve the first block and insert the second block's contents
# immediately before the first block's closing tag.
repaired = (
    text[:closes[0].start()]
    + "\n"
    + second_content.strip("\n")
    + "\n"
    + text[closes[0].start():closes[0].end()]
    + text[closes[1].end():]
)

# Validate the complete XML before touching the original file.
root = ET.fromstring(repaired)

if root.tag != "ossec_config":
    raise SystemExit("ABORT: Unexpected XML root element")

localfiles = root.findall("localfile")
if len(localfiles) != 6:
    raise SystemExit(
        f"ABORT: Expected 6 localfile entries, found {len(localfiles)}"
    )

for i, entry in enumerate(localfiles, 1):
    print(
        f"VALIDATED LOCALFILE {i}: "
        f"FORMAT={entry.findtext('log_format')} "
        f"LOCATION={entry.findtext('location')}"
    )

# Create a timestamped backup before replacing the original.
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup = f"{path}.pre-repair-{stamp}"

shutil.copy2(path, backup)

before_hash = hashlib.sha256(original).hexdigest()
backup_hash = hashlib.sha256(open(backup, "rb").read()).hexdigest()

if before_hash != backup_hash:
    raise SystemExit("ABORT: Backup SHA256 does not match original")

# Write a temporary file in the same directory, preserving ownership
# and permissions, then atomically replace the original.
directory = os.path.dirname(path)
st = os.stat(path)

fd, temp_path = tempfile.mkstemp(prefix=".ossec.conf.repair.", dir=directory)

try:
    with os.fdopen(fd, "wb") as f:
        f.write(repaired.encode("utf-8"))
        f.flush()
        os.fsync(f.fileno())

    os.chmod(temp_path, stat.S_IMODE(st.st_mode))
    os.chown(temp_path, st.st_uid, st.st_gid)
    os.replace(temp_path, path)

except Exception:
    if os.path.exists(temp_path):
        os.unlink(temp_path)
    raise

# Re-read and verify the installed file.
with open(path, "rb") as f:
    installed = f.read()

installed_root = ET.fromstring(installed.decode("utf-8"))
installed_localfiles = installed_root.findall("localfile")

print()
print("===== REPAIR RESULT =====")
print("XML_PARSE=OK")
print(f"ROOT_ELEMENT={installed_root.tag}")
print(f"OSSEC_CONFIG_BLOCKS={len(re.findall(rb'<ossec_config\\s*>', installed))}")
print(f"LOCALFILE_COUNT={len(installed_localfiles)}")
print(f"BACKUP={backup}")
print(f"BACKUP_SHA256={backup_hash}")
print(f"REPAIRED_SHA256={hashlib.sha256(installed).hexdigest()}")
print(f"FILE_MODE={oct(stat.S_IMODE(os.stat(path).st_mode))}")
print("WAZUH_RESTART=NOT_PERFORMED")
PY

echo
echo "===== WAZUH SERVICE STATE (NO RESTART) ====="
systemctl is-active wazuh-manager
```

The XML syntax is valid, there are six `localfile` entries, and the SHA256 of the saved copy matched the file before the repair. Wazuh Manager is still running.

## 3.2 Root Element, Owner and Permissions

> **Run on: VM 220**

```bash
echo "===== XML ROOT TAG VERIFICATION ====="
python3 - <<'PY'
import re
import xml.etree.ElementTree as ET

p = "/var/ossec/etc/ossec.conf"
s = open(p, encoding="utf-8").read()

print("OPEN_TAG_COUNT =", len(re.findall(r"<ossec_config\s*>", s)))
print("CLOSE_TAG_COUNT =", len(re.findall(r"</ossec_config\s*>", s)))

root = ET.parse(p).getroot()
print("XML_ROOT =", root.tag)
print("LOCALFILE_COUNT =", len(root.findall("localfile")))
PY

echo
echo "===== FILE GROUP VERIFICATION ====="
getent group 110

echo
echo "===== WAZUH LOGCOLLECTOR OPTIONS ====="
/var/ossec/bin/wazuh-logcollector -h 2>&1 | head -45
```

| Item | Result |
|---|---|
| `<ossec_config>` start and end | one each |
| Root element | `ossec_config` |
| `localfile` | 6 |
| Owner and permissions | `root:wazuh` (GID 110), `660` |
| Saved copy | present, matches the SHA256 before the repair |

## 3.3 Testing the Logcollector Configuration

Wazuh's `-t` is an option that only tests the configuration; it does not restart the running service.

> **Run on: VM 220**

```bash
echo "===== WAZUH LOGCOLLECTOR CONFIG TEST ====="
/var/ossec/bin/wazuh-logcollector -t
RESULT=$?

echo
echo "LOGCOLLECTOR_TEST_EXIT_CODE=$RESULT"

echo
echo "===== WAZUH MANAGER STATE ====="
systemctl is-active wazuh-manager

echo
echo "===== WAZUH LOGCOLLECTOR PROCESS ====="
pgrep -a wazuh-logcollector
```

`wazuh-logcollector -t` gave exit code `0`. The `pgrep` warning means that the process name exceeds 15 characters and so an ordinary search does not match it; it is not a configuration error.

## 3.4 Running Processes and Logs

> **Run on: VM 220**

```bash
echo "===== LOGCOLLECTOR PROCESS ====="
ps -eo pid,ppid,stat,comm,args | grep '[w]azuh-logcollector'

echo
echo "===== RECENT WAZUH MANAGER JOURNAL ====="
journalctl -u wazuh-manager --since "2026-11-23 01:00:00 UTC" --no-pager \
  | grep -Ei 'error|warning|invalid|failed|started|logcollector|configuration' \
  | tail -80

echo
echo "===== WAZUH LOG FILE ERRORS ====="
grep -Ei 'error|invalid|failed|warning' \
  /var/ossec/logs/ossec.log 2>/dev/null | tail -60

echo
echo "===== MANAGER SERVICE STATE ====="
systemctl is-active wazuh-manager
```

```bash
echo "===== WAZUH PROCESS HEALTH ====="
ps -eo pid,stat,%cpu,%mem,comm | grep -E 'wazuh-(analysisd|remoted|logcollector|db|modulesd|syscheckd)'

echo
echo "===== WAZUH INTERNAL QUEUE STATUS ====="
if [ -x /var/ossec/bin/wazuh-control ]; then
    /var/ossec/bin/wazuh-control status
fi

echo
echo "===== WAZUH ALERT FILE METADATA ====="
stat -c 'FILE=%n SIZE=%s OWNER=%U:%G MODE=%a MTIME=%y' \
  /var/ossec/logs/alerts/alerts.json \
  /var/ossec/logs/alerts/alerts.log 2>/dev/null

echo
echo "===== WAZUH MANAGER STATE ====="
systemctl is-active wazuh-manager
```

| Checked | Result |
|---|---|
| Logcollector process | running |
| Errors and warnings after the repair | none in the range examined |
| `wazuh-analysisd`, `remoted`, `db`, `modulesd`, `syscheckd`, `api` | running |
| Wazuh Manager | `active` |

That `wazuh-clusterd`, `wazuh-maild` and others are stopped is normal in a single-Manager configuration.

# Closing Notes

In Part 45, before moving on to LLM analysis, we checked the environment and fixed the broken XML of the Wazuh configuration file.

| Item | Result |
|---|---|
| Environment | use Wazuh (VM 220), AI Defense Manager (VM 230), Ollama (VM 101) and PostgreSQL (CT 109); no new VMs |
| `ossec.conf` | the second `<ossec_config>` merged into the first, keeping the six `localfile` entries; copy saved; `root:wazuh`, `660` |
| Wazuh test | `wazuh-logcollector -t` gave `0` |
| Wazuh restart | not done (the running processes will not reflect the change until Wazuh rereads its configuration) |

In the next part, Part 46, we classify the contents of Wazuh alerts and decide which fields may be passed to the LLM.

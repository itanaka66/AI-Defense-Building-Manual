---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Omnibus Edition: Parts 45–71"
author: "Isamu Tanaka"
lang: en-US
---

# About Volume 4

This book collects Volume 4 (Parts 45–71) of the "AI Autonomous Cyber Defense System Build Manual" in a single omnibus edition. Centered on the AI Defense Manager (VM 230), it builds the mechanisms for running LLM analysis safely: narrowing the input passed to the LLM with an allowlist, masking the LLM's output and keeping approval decisions on the server side, integration with the Relay, and token authentication for the API. It then checks error responses and logs, builds tamper detection for logs with FSS (Forward Secure Sealing), repairs Wazuh's local rules, and starts building AI defense agents.

It assumes the same environment as Volumes 1, 2 and 3 (Proxmox, VM 220 security-core, VM 230 ai-defense-manager, VM 101 ollama-gpu, LXC 109 PostgreSQL and so on). For the underlying configuration and procedures, see the earlier volumes.

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


# Part 45: Preparing for LLM Analysis and Repairing the Wazuh Configuration File
## Introduction

### About This Book

This is Part 45 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Volume 3 (Parts 31–44), we finished the backup and restore of the PostgreSQL that stores the events. Volume 4 moves on to threat analysis using an LLM (large language model).

We do not give the LLM direct authority over defensive operations. The LLM only produces material for decisions and proposals, kept separate from the actual operations. As a precondition, we check the reliability of the data passed to the LLM. Part 45 does the following.

1. Check the layout and state of the existing environment (Wazuh, PostgreSQL, Ollama, AI Defense Manager), read-only
2. Find that the Wazuh Manager configuration file `/var/ossec/etc/ossec.conf` is broken as XML, and investigate why
3. Save a copy of the configuration file, repair it, and check it with Wazuh's test command (Wazuh is not restarted)

### About Volume 4

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


### Volumes and Parts

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

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)
  - **VM 220**: security-core (root). Log in as root from the Console of VM 220 in the Proxmox web interface

## Chapter 1: Checking the Current Environment

Here we create no new VMs or containers, and change or restart nothing.

### 1.1 Layout of Containers and VMs

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

### 1.2 State of Each Node

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

### 1.3 Wazuh State

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

### 1.4 The Path from Wazuh to PostgreSQL

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

## Chapter 2: Finding Where the Configuration File Is Broken

### 2.1 Position of the Error

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

### 2.2 Structure Around the Error

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

### 2.3 How Long It Has Been Like This

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

### 2.4 Contents of the Added Block

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

### 2.5 Checking from the Console

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

## Chapter 3: Repairing the Configuration File

### 3.1 Saving a Copy and Repairing

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

### 3.2 Root Element, Owner and Permissions

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

### 3.3 Testing the Logcollector Configuration

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

### 3.4 Running Processes and Logs

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

## Closing Notes

In Part 45, before moving on to LLM analysis, we checked the environment and fixed the broken XML of the Wazuh configuration file.

| Item | Result |
|---|---|
| Environment | use Wazuh (VM 220), AI Defense Manager (VM 230), Ollama (VM 101) and PostgreSQL (CT 109); no new VMs |
| `ossec.conf` | the second `<ossec_config>` merged into the first, keeping the six `localfile` entries; copy saved; `root:wazuh`, `660` |
| Wazuh test | `wazuh-logcollector -t` gave `0` |
| Wazuh restart | not done (the running processes will not reflect the change until Wazuh rereads its configuration) |

In the next part, Part 46, we classify the contents of Wazuh alerts and decide which fields may be passed to the LLM.

# Part 46: Classifying Alerts and Deciding Which Fields to Pass to the LLM
## Introduction

### About This Book

This is Part 46 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 45 we repaired the Wazuh configuration file. Here, to decide what data to pass to the LLM, we examine the contents of Wazuh alerts by counts and types only, **without displaying values**.

1. Tally the alerts by count, severity, rule and classification group
2. Check the definitions of the most frequent rules and run Wazuh's own test (`wazuh-analysisd -t`)
3. Examine the field names in the alert JSON and separate the fields that may be passed to the LLM from those that must not
4. Decide the types and constraints of the seven allowed fields, and try the conversion on real alerts in memory only

Event bodies, IP addresses, user names and commands are not displayed. Nothing is written to files, registered in a DB or sent to the LLM.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **pve**: the Proxmox host (root)

## Chapter 1: Tallying the Alerts

### 1.1 Count and Severity

> **Run on: VM 220**

```bash
echo "===== WAZUH ALERT AGGREGATION (SANITIZED) ====="

python3 - <<'PY'
import json
import os
from collections import Counter

path = "/var/ossec/logs/alerts/alerts.json"

counts = Counter()
total = 0
malformed = 0

if not os.path.isfile(path):
    print("ALERT_FILE=NOT_FOUND")
else:
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                level = obj.get("rule", {}).get("level")
                if isinstance(level, int):
                    counts[level] += 1
                    total += 1
                else:
                    malformed += 1
            except Exception:
                malformed += 1

    print(f"ALERT_RECORDS_WITH_LEVEL={total}")
    print(f"RECORDS_WITHOUT_VALID_LEVEL={malformed}")
    print("LEVEL_COUNTS:")
    for level in sorted(counts):
        print(f"  LEVEL_{level}={counts[level]}")

print()
print("RAW_EVENT_CONTENT=NOT_DISPLAYED")
PY

echo
echo "===== LOGCOLLECTOR PID CHECK ====="
ps -p 1876 -o pid,ppid,stat,comm,args

echo
echo "===== ALERT FILE METADATA ====="
stat -c 'SIZE=%s MTIME=%y OWNER=%U:%G MODE=%a' \
  /var/ossec/logs/alerts/alerts.json
```

The current `alerts.json` had **245** correctly readable alerts (228 at severity Level 3, 17 at Level 7, 0 unreadable). This is the number left in the file; not all of them necessarily occurred recently.

### 1.2 Rules and Classification Groups

> **Run on: VM 220**

```bash
echo "===== WAZUH RULE CLASSIFICATION SUMMARY ====="

python3 - <<'PY'
import json
from collections import Counter
from datetime import datetime, timezone

path = "/var/ossec/logs/alerts/alerts.json"

rule_ids = Counter()
groups = Counter()
levels = Counter()
timestamps = []

total = 0
invalid = 0

with open(path, encoding="utf-8", errors="replace") as f:
    for line in f:
        if not line.strip():
            continue

        try:
            obj = json.loads(line)
            rule = obj.get("rule") or {}

            level = rule.get("level")
            if not isinstance(level, int):
                invalid += 1
                continue

            total += 1
            levels[level] += 1

            rid = rule.get("id")
            if rid is not None:
                rule_ids[str(rid)] += 1

            rule_groups = rule.get("groups", [])
            if isinstance(rule_groups, list):
                for group in rule_groups:
                    if isinstance(group, str):
                        groups[group] += 1

            ts = obj.get("timestamp")
            if isinstance(ts, str):
                try:
                    timestamps.append(
                        datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    )
                except ValueError:
                    pass

        except Exception:
            invalid += 1

print(f"VALID_ALERTS={total}")
print(f"INVALID_RECORDS={invalid}")

print("LEVEL_DISTRIBUTION:")
for key, value in sorted(levels.items()):
    print(f"  LEVEL_{key}={value}")

print("TOP_RULE_IDS:")
for key, value in rule_ids.most_common(15):
    print(f"  RULE_ID={key} COUNT={value}")

print("TOP_RULE_GROUPS:")
for key, value in groups.most_common(15):
    print(f"  GROUP={key} COUNT={value}")

if timestamps:
    print("OLDEST_TIMESTAMP=" + min(timestamps).isoformat())
    print("NEWEST_TIMESTAMP=" + max(timestamps).isoformat())

print("EVENT_BODY_DISPLAYED=NO")
print("FULL_LOG_DISPLAYED=NO")
print("ARBITRARY_DATA_DISPLAYED=NO")
PY
```

- 220 of the 245 have the `pam` group (groups are counted with overlap)
- Rules `5501` and `5502` account for 220 together
- All 17 at Level 7 are rule `100103` (groups `local`, `error`)
- Rule `87203` appears 6 times (group `proxmox-ve`)

Rule IDs and group names alone do not tell us whether something is an attack.

## Chapter 2: Checking the Rule Definitions

### 2.1 Rule Descriptions and Classification Conditions

Without reading event bodies, we extract only the descriptions and classification conditions from the rule definitions.

> **Run on: VM 220**

```bash
echo "===== WAZUH RULE DEFINITIONS (METADATA ONLY) ====="

python3 - <<'PY'
import os
import xml.etree.ElementTree as ET
from collections import defaultdict

targets = {"5501", "5502", "100103", "87203", "5715", "5402"}
roots = [
    "/var/ossec/ruleset/rules",
    "/var/ossec/etc/rules",
]

safe_tags = {
    "description",
    "group",
    "if_sid",
    "if_group",
    "if_matched_sid",
    "if_matched_group",
    "if_level",
    "level",
    "frequency",
    "timeframe",
    "same_srcip",
    "same_user",
    "same_location",
    "same_field",
    "different_srcip",
    "different_user",
    "options",
}

found = defaultdict(list)
parse_errors = 0
files_scanned = 0

for base in roots:
    if not os.path.isdir(base):
        continue

    for directory, _, filenames in os.walk(base):
        for filename in filenames:
            if not filename.endswith(".xml"):
                continue

            path = os.path.join(directory, filename)
            files_scanned += 1

            try:
                root = ET.parse(path).getroot()
            except Exception:
                parse_errors += 1
                continue

            for rule in root.iter("rule"):
                rid = rule.get("id")
                if rid not in targets:
                    continue

                metadata = {
                    "file": filename,
                    "id": rid,
                    "attributes": {
                        k: v for k, v in rule.attrib.items()
                        if k in {"id", "level", "overwrite"}
                    },
                    "fields": [],
                }

                for child in rule:
                    if child.tag not in safe_tags:
                        continue

                    value = " ".join("".join(child.itertext()).split())
                    if value:
                        metadata["fields"].append(
                            (child.tag, value[:300])
                        )

                found[rid].append(metadata)

print(f"XML_FILES_SCANNED={files_scanned}")
print(f"XML_PARSE_ERRORS={parse_errors}")

for rid in sorted(targets, key=int):
    print(f"\n===== RULE ID {rid} =====")

    entries = found.get(rid, [])
    if not entries:
        print("DEFINITION=NOT_FOUND_IN_SCANNED_DIRECTORIES")
        continue

    for item in entries:
        print(f"FILE={item['file']}")
        print(f"ATTRIBUTES={item['attributes']}")
        for tag, value in item["fields"]:
            print(f"{tag.upper()}={value}")

print("\nRULE_REGEX_DISPLAYED=NO")
print("EVENT_DATA_DISPLAYED=NO")
print("COMMAND_CONTENT_DISPLAYED=NO")
PY
```

| Rule | Meaning |
|---|---|
| `5501` | PAM login session opened |
| `5502` | PAM login session closed |
| `5715` | SSH authentication succeeded |
| `87203` | Proxmox VE authentication succeeded |

### 2.2 Location of the Rule Files

> **Run on: VM 220**

```bash
echo "===== WAZUH RULE FILE LOCATIONS ====="

python3 - <<'PY'
import os
import re
import xml.etree.ElementTree as ET

targets = {"5402", "100103"}
roots = [
    "/var/ossec/etc",
    "/var/ossec/ruleset/rules",
]

seen = set()
parse_errors = []
matches = []

for base in roots:
    print(f"\nROOT={base} EXISTS={os.path.isdir(base)}")
    if not os.path.isdir(base):
        continue

    for directory, _, files in os.walk(base):
        for name in files:
            if not name.endswith(".xml"):
                continue

            path = os.path.join(directory, name)
            if path in seen:
                continue
            seen.add(path)

            try:
                root = ET.parse(path).getroot()
                for rule in root.iter("rule"):
                    rid = rule.get("id")
                    if rid in targets:
                        matches.append((rid, path, "XML_PARSED"))
            except Exception as e:
                parse_errors.append((path, type(e).__name__))

                # Malformed XML: search only for target rule ID markers.
                # Do not print any rule contents or matching lines.
                try:
                    with open(path, encoding="utf-8", errors="replace") as f:
                        for line_no, line in enumerate(f, 1):
                            for rid in targets:
                                if re.search(
                                    r'<rule\b[^>]*\bid=["\']'
                                    + re.escape(rid)
                                    + r'["\']',
                                    line
                                ):
                                    matches.append(
                                        (rid, path, f"LINE_{line_no}_XML_PARSE_FAILED")
                                    )
                except OSError:
                    pass

print("\n===== TARGET RULE FILE MATCHES =====")
for rid, path, status in sorted(matches):
    print(f"RULE_ID={rid} FILE={path} STATUS={status}")

if not matches:
    print("TARGET_RULE_FILES=NOT_FOUND")

print("\n===== XML PARSE ERROR FILE SUMMARY =====")
print(f"PARSE_ERROR_FILE_COUNT={len(parse_errors)}")
for path, error in parse_errors:
    print(f"FILE={path} ERROR_TYPE={error}")

print("\nRULE_CONTENT_DISPLAYED=NO")
print("EVENT_DATA_DISPLAYED=NO")
PY
```

`100103` is in `/var/ossec/etc/rules/local_rules.xml`, and `5402` is in the standard rule file `0020-syslog_rules.xml`.

Python's standard XML parser gives `ParseError` for 27 rule files, but Wazuh rule files put several top-level elements in one file, so this alone does not mean they are broken. We check with Wazuh's own test.

### 2.3 Wazuh's Own Test

> **Run on: VM 220**

```bash
echo "===== WAZUH ANALYSISD CONFIG TEST ====="
/var/ossec/bin/wazuh-analysisd -t
RESULT=$?
echo "ANALYSISD_TEST_EXIT_CODE=$RESULT"

echo
echo "===== LOCAL RULE 100103 METADATA ====="
python3 - <<'PY'
import re

path = "/var/ossec/etc/rules/local_rules.xml"
lines = open(path, encoding="utf-8", errors="replace").readlines()

start = None
for i, line in enumerate(lines):
    if re.search(r'<rule\b[^>]*\bid=["\']100103["\']', line):
        start = i
        break

if start is None:
    print("RULE_100103=NOT_FOUND")
else:
    block = "".join(lines[start:start+80])
    match = re.search(r'<rule\b([^>]*)>', block)
    print(f"RULE_LINE={start+1}")
    print(f"ATTRIBUTES={match.group(1) if match else 'NOT_PARSED'}")

    for tag in ("if_sid", "if_group", "if_level", "level",
                "description", "group", "frequency", "timeframe"):
        values = re.findall(
            rf'<{tag}\b[^>]*>(.*?)</{tag}>',
            block,
            flags=re.S
        )
        for value in values:
            value = " ".join(value.split())
            print(f"{tag.upper()}={value[:250]}")

    print("REGEX_AND_MATCH_CONDITIONS=NOT_DISPLAYED")
PY

echo
echo "===== LOCAL RULE FILE XML PARSER DIAGNOSTIC ====="
python3 - <<'PY'
import xml.etree.ElementTree as ET

for path in (
    "/var/ossec/etc/rules/local_rules.xml",
    "/var/ossec/ruleset/rules/0020-syslog_rules.xml",
):
    try:
        ET.parse(path)
        print(f"{path}: PYTHON_XML_PARSE=OK")
    except ET.ParseError as e:
        print(f"{path}: PYTHON_XML_PARSE_ERROR={e}")
PY
```

`wazuh-analysisd -t` gave exit code `0`. Wazuh reads the rule configuration correctly.

### 2.4 Definitions of the Local Rules

> **Run on: VM 220**

```bash
echo "===== EXACT WAZUH RULE METADATA ====="

python3 - <<'PY'
import re

targets = {"100100", "100103", "5402"}
files = {
    "/var/ossec/etc/rules/local_rules.xml",
    "/var/ossec/ruleset/rules/0020-syslog_rules.xml",
}

for path in sorted(files):
    text = open(path, encoding="utf-8", errors="replace").read()

    print(f"\nFILE={path}")

    for rid in sorted(targets):
        pattern = (
            r'<rule\b(?=[^>]*\bid=["\']'
            + re.escape(rid)
            + r'["\'])[^>]*>.*?</rule>'
        )
        matches = list(re.finditer(pattern, text, re.S))

        for index, match in enumerate(matches, 1):
            block = match.group(0)
            opening = re.search(r'<rule\b([^>]*)>', block)
            attrs = opening.group(1) if opening else "UNKNOWN"

            print(f"\nRULE_ID={rid} OCCURRENCE={index}")
            print(f"ATTRIBUTES={attrs}")

            for tag in (
                "if_sid", "if_group", "if_level",
                "level", "description", "group",
                "frequency", "timeframe"
            ):
                values = re.findall(
                    rf'<{tag}\b[^>]*>(.*?)</{tag}>',
                    block,
                    re.S
                )
                for value in values:
                    value = " ".join(value.split())
                    print(f"{tag.upper()}={value[:250]}")

        if not matches:
            print(f"RULE_ID={rid} NOT_FOUND_IN_THIS_FILE")

print("\nREGEX_CONDITIONS=NOT_DISPLAYED")
print("EVENT_CONTENT=NOT_DISPLAYED")
PY
```

| Rule | Count | Meaning | Assessment |
|---|---:|---|---|
| 5501 | 112 | PAM login session opened | ordinary authentication record |
| 5502 | 108 | PAM login session closed | ordinary authentication record |
| 100103 | 17 | PostgreSQL ERROR event | to be examined |
| 87203 | 6 | Proxmox VE authentication succeeded | ordinary authentication record |
| 5715 | 1 | SSH authentication succeeded | ordinary authentication record |
| 5402 | 1 | root privileges obtained with sudo | check whether the operation was legitimate |

`100100` is the Level 0 "PostgreSQL sanitized JSON event base rule", and `100103` is the Level 7 "PostgreSQL ERROR event detected". The 17 are Wazuh detections of the masked PostgreSQL events from CT 109; we treat them as application or database errors, not attacks.

## Chapter 3: Deciding the Fields to Pass to the LLM

### 3.1 Field Names in the Alert JSON

We count only field names without showing values.

> **Run on: VM 220**

```bash
echo "===== WAZUH ALERT JSON FIELD INVENTORY ====="

python3 - <<'PY'
import json
from collections import Counter

path = "/var/ossec/logs/alerts/alerts.json"

top = Counter()
nested = Counter()
records = 0
invalid = 0

with open(path, encoding="utf-8", errors="replace") as f:
    for line in f:
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            records += 1

            for key, value in obj.items():
                top[key] += 1
                if isinstance(value, dict):
                    for child in value:
                        nested[f"{key}.{child}"] += 1
        except Exception:
            invalid += 1

print(f"RECORDS={records}")
print(f"INVALID_JSON={invalid}")

print("\nTOP_LEVEL_FIELD_NAMES:")
for key, count in sorted(top.items()):
    print(f"  {key}: {count}")

print("\nNESTED_FIELD_NAMES:")
for key, count in sorted(nested.items()):
    print(f"  {key}: {count}")

print("\nFIELD_VALUES_DISPLAYED=NO")
print("FULL_LOG_DISPLAYED=NO")
print("ARBITRARY_DATA_DISPLAYED=NO")
PY
```

All 245 had `full_log` and `data`. They also contain information that must not be passed to the LLM as is, such as `agent.ip`, `agent.name`, `data.dstuser`, `data.srcuser`, `data.command` and `data.pwd`. Therefore **we do not send the alert JSON to the LLM as it is**.

| Field | Handling |
|---|---|
| `timestamp` | pass (after checking the format) |
| `rule.id` | pass |
| `rule.level` | pass |
| `rule.groups` | pass (restricted by an allowlist) |
| `rule.description` | pass (check length and characters) |
| `decoder.name` | pass (restricted by an allowlist) |
| `agent.id` | pass |
| `agent.ip`, `agent.name` | exclude |
| `full_log` | always exclude |
| `data` | exclude entirely |
| `predecoder`, `manager`, `location`, `id` | exclude as a rule |

### 3.2 Types and Missing Values of the Seven Fields

> **Run on: VM 220**

```bash
echo "===== LLM SAFE-FIELD SCHEMA VALIDATION ====="

python3 - <<'PY'
import json
from collections import Counter

path = "/var/ossec/logs/alerts/alerts.json"

fields = {
    "timestamp": lambda o: o.get("timestamp"),
    "rule.id": lambda o: (o.get("rule") or {}).get("id"),
    "rule.level": lambda o: (o.get("rule") or {}).get("level"),
    "rule.groups": lambda o: (o.get("rule") or {}).get("groups"),
    "rule.description": lambda o: (o.get("rule") or {}).get("description"),
    "decoder.name": lambda o: (o.get("decoder") or {}).get("name"),
    "agent.id": lambda o: (o.get("agent") or {}).get("id"),
}

stats = {
    name: {
        "types": Counter(),
        "missing": 0,
        "max_length": 0,
        "invalid": 0,
    }
    for name in fields
}

records = 0
bad_json = 0

with open(path, encoding="utf-8", errors="replace") as f:
    for line in f:
        if not line.strip():
            continue

        try:
            obj = json.loads(line)
            records += 1
        except Exception:
            bad_json += 1
            continue

        for name, getter in fields.items():
            value = getter(obj)
            item = stats[name]

            if value is None:
                item["missing"] += 1
                continue

            item["types"][type(value).__name__] += 1

            if isinstance(value, str):
                item["max_length"] = max(
                    item["max_length"], len(value)
                )
                if len(value) > 512:
                    item["invalid"] += 1
            elif isinstance(value, list):
                if not all(isinstance(x, str) for x in value):
                    item["invalid"] += 1
                else:
                    item["max_length"] = max(
                        item["max_length"],
                        max((len(x) for x in value), default=0)
                    )
            elif name == "rule.level":
                if not isinstance(value, int) or not 0 <= value <= 16:
                    item["invalid"] += 1
            elif name == "rule.id":
                if not isinstance(value, (str, int)):
                    item["invalid"] += 1

print(f"RECORDS={records}")
print(f"INVALID_JSON={bad_json}")

for name, item in stats.items():
    print(f"\nFIELD={name}")
    print(f"  TYPES={dict(item['types'])}")
    print(f"  MISSING={item['missing']}")
    print(f"  MAX_STRING_LENGTH={item['max_length']}")
    print(f"  INVALID_VALUES={item['invalid']}")

print("\nFIELD_VALUES_DISPLAYED=NO")
print("EVENT_CONTENT_DISPLAYED=NO")
print("FULL_LOG_DISPLAYED=NO")
print("ARBITRARY_DATA_DISPLAYED=NO")
PY
```

In all 245, the seven fields were present, with the expected types.

### 3.3 Constraints of the Seven Fields

> **Run on: VM 220**

```bash
echo "===== LLM SAFE-FIELD CONSTRAINT VALIDATION ====="

python3 - <<'PY'
import json
import re
from datetime import datetime
from collections import Counter

path = "/var/ossec/logs/alerts/alerts.json"

stats = Counter()
max_lengths = Counter()
max_groups = 0
bad_examples = Counter()

def check_string(value, pattern=None, max_length=None):
    if not isinstance(value, str):
        return False
    if max_length is not None and len(value) > max_length:
        return False
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        return False
    if pattern and not re.fullmatch(pattern, value):
        return False
    return True

with open(path, encoding="utf-8", errors="replace") as f:
    for line in f:
        if not line.strip():
            continue

        obj = json.loads(line)
        rule = obj.get("rule") or {}
        decoder = obj.get("decoder") or {}
        agent = obj.get("agent") or {}

        ts = obj.get("timestamp")
        rid = rule.get("id")
        level = rule.get("level")
        groups = rule.get("groups")
        desc = rule.get("description")
        dec = decoder.get("name")
        aid = agent.get("id")

        checks = {
            "timestamp": False,
            "rule.id": check_string(rid, r"[0-9]{1,16}", 16),
            "rule.level": isinstance(level, int) and not isinstance(level, bool) and 0 <= level <= 16,
            "rule.groups": isinstance(groups, list) and all(
                check_string(x, r"[A-Za-z0-9_.-]{1,64}", 64)
                for x in groups
            ),
            "rule.description": check_string(desc, max_length=160),
            "decoder.name": check_string(dec, r"[A-Za-z0-9_.-]{1,64}", 64),
            "agent.id": check_string(aid, r"[0-9]{1,16}", 16),
        }

        if isinstance(ts, str):
            try:
                datetime.fromisoformat(ts.replace("Z", "+00:00"))
                checks["timestamp"] = True
            except ValueError:
                pass

        for name, valid in checks.items():
            stats[name + (".valid" if valid else ".invalid")] += 1

        for name, value in (
            ("rule.id", rid),
            ("rule.description", desc),
            ("decoder.name", dec),
            ("agent.id", aid),
        ):
            if isinstance(value, str):
                max_lengths[name] = max(max_lengths[name], len(value))

        if isinstance(groups, list):
            max_groups = max(max_groups, len(groups))

print("FIELD_VALIDATION_COUNTS:")
for name in (
    "timestamp",
    "rule.id",
    "rule.level",
    "rule.groups",
    "rule.description",
    "decoder.name",
    "agent.id",
):
    print(
        f"{name}: "
        f"valid={stats[name + '.valid']} "
        f"invalid={stats[name + '.invalid']}"
    )

print("\nMAX_STRING_LENGTHS:")
for name, length in sorted(max_lengths.items()):
    print(f"{name}: {length}")

print(f"\nMAX_GROUPS_PER_EVENT={max_groups}")
print("FIELD_VALUES_DISPLAYED=NO")
print("EVENT_CONTENT_DISPLAYED=NO")
PY
```

For all seven fields, 245 of 245 satisfied the constraints, with 0 non-conforming values. With this we fix the LLM input allowlist (v1).

| Field | Type | Constraint |
|---|---|---|
| `timestamp` | string | ISO 8601 date and time |
| `rule_id` | string | 1–16 digits |
| `severity` | integer | 0–16 |
| `groups` | array of strings | alphanumerics and `_.-`, up to 64 characters each |
| `description` | string | up to 160 characters |
| `decoder` | string | alphanumerics and `_.-`, up to 64 characters |
| `agent_id` | string | 1–16 digits |

The important point is **not to copy anything other than the allowed fields**. Not only do we exclude `data` and `full_log`, we discard every unknown field.

### 3.4 Trying the Conversion in Memory

We convert the actual 245 in memory only.

> **Run on: VM 220**

```bash
echo "===== LLM WHITELIST TRANSFORMATION DRY RUN ====="

python3 - <<'PY'
import json
from collections import Counter

SOURCE = "/var/ossec/logs/alerts/alerts.json"

ALLOWED_KEYS = {
    "timestamp",
    "rule_id",
    "severity",
    "groups",
    "description",
    "decoder",
    "agent_id",
}

FORBIDDEN_KEYS = {
    "full_log",
    "data",
    "predecoder",
    "location",
    "manager",
}

def transform(obj):
    rule = obj.get("rule") or {}
    decoder = obj.get("decoder") or {}
    agent = obj.get("agent") or {}

    return {
        "timestamp": obj.get("timestamp"),
        "rule_id": rule.get("id"),
        "severity": rule.get("level"),
        "groups": rule.get("groups"),
        "description": rule.get("description"),
        "decoder": decoder.get("name"),
        "agent_id": agent.get("id"),
    }

records = 0
transformed = 0
errors = Counter()
total_bytes = 0
max_bytes = 0

with open(SOURCE, encoding="utf-8", errors="replace") as f:
    for line in f:
        if not line.strip():
            continue

        records += 1

        try:
            source = json.loads(line)
            payload = transform(source)

            if set(payload) != ALLOWED_KEYS:
                errors["unexpected_or_missing_keys"] += 1

            if set(payload) & FORBIDDEN_KEYS:
                errors["forbidden_keys_present"] += 1

            encoded = json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")

            # Verify serialization by re-reading the JSON
            decoded = json.loads(encoded)

            if set(decoded) != ALLOWED_KEYS:
                errors["roundtrip_key_mismatch"] += 1

            total_bytes += len(encoded)
            max_bytes = max(max_bytes, len(encoded))
            transformed += 1

        except Exception:
            errors["transformation_error"] += 1

print(f"SOURCE_RECORDS={records}")
print(f"TRANSFORMED_RECORDS={transformed}")
print(f"TRANSFORMATION_ERRORS={errors['transformation_error']}")
print(f"KEY_SCHEMA_ERRORS={errors['unexpected_or_missing_keys']}")
print(f"FORBIDDEN_KEY_ERRORS={errors['forbidden_keys_present']}")
print(f"ROUNDTRIP_ERRORS={errors['roundtrip_key_mismatch']}")
print(f"TOTAL_SERIALIZED_BYTES={total_bytes}")
print(f"MAX_RECORD_BYTES={max_bytes}")
print("FILE_WRITTEN=NO")
print("DATABASE_WRITTEN=NO")
print("LLM_REQUEST_SENT=NO")
print("PAYLOAD_VALUES_DISPLAYED=NO")
PY
```

| Checked | Result |
|---|---|
| Converted | all 245 |
| Conversion errors, key structure errors | 0 |
| Forbidden fields leaked | 0 |
| JSON re-read errors | 0 |
| Total size after conversion | 46,848 bytes |
| Maximum size of one | 225 bytes |

We confirmed that the events passed to the LLM can be made small and of a fixed shape. However, this was confirmed on the current 245; when actually integrated, the input is checked every time.

## Chapter 4: The Data Path

We build no new services and use the current environment. The planned data path is as follows.

```text
VM220 Wazuh
    │
    │ alerts.json (raw data, including sensitive fields)
    ▼
Dedicated whitelist conversion boundary
    │
    │ Normalized JSON with 7 fields only
    ▼
VM230 AI Defense Manager
    │
    ├── Rule-based pre-assessment
    │
    ├── Ollama VM101 (Gemma 4 12B)
    │       └── Threat analysis and JSON proposals only
    │
    ▼
Deterministic policy validation
    │
    ▼
Action Gateway (allowlist, TTL, approval)
```

The PostgreSQL filter on CT 109 keeps its current role as the boundary that masks PostgreSQL events. We do not mix it with the Wazuh alert conversion or change the filter.

Finally, we check the layout of the three VMs involved.

> **Run on: pve**

```bash
echo "===== VM230 AI DEFENSE MANAGER ====="
qm status 230
qm config 230 | grep -E '^(name|memory|cores|sockets|net[0-9]+|agent|onboot):'

echo
echo "===== VM101 OLLAMA ====="
qm status 101
qm config 101 | grep -E '^(name|memory|cores|sockets|net[0-9]+|agent|onboot):'

echo
echo "===== VM220 SECURITY CORE ====="
qm status 220
qm config 220 | grep -E '^(name|memory|cores|sockets|net[0-9]+|agent|onboot):'
```

| VM | Role | State | vCPU | Memory | Network |
|---|---|---|---:|---:|---|
| 220 | Wazuh (security-core) | running | 8 | 16GB | vmbr0, vmbr1 |
| 230 | AI Defense Manager | running | 4 | 8GB | vmbr0 |
| 101 | Ollama (GPU) | running | 16 | 128GB | vmbr0 |

> **Caution:** `qm` is a command on the Proxmox host. Running it inside VM 220 gives `qm: command not found`. Check that the prompt is `root@pve:~#` before running it.

## Closing Notes

In Part 46 we examined the contents of the alerts without looking at values, and decided the fields to pass to the LLM.

| Item | Result |
|---|---|
| Alerts | 245 (mostly PAM, SSH and Proxmox authentication records; the 17 at Level 7 are PostgreSQL ERRORs) |
| Wazuh test | `wazuh-analysisd -t` gave `0` |
| Fields passed to the LLM | 7 (`timestamp`, `rule_id`, `severity`, `groups`, `description`, `decoder`, `agent_id`); everything else is discarded |
| Conversion test | all 245 succeeded; 0 forbidden fields leaked |

In the next part, Part 47, we examine the existing implementation of the AI Defense Manager on VM 230 and decide where to integrate the allowlist.

# Part 47: Examining the Existing AI Defense Manager Implementation
## Introduction

### About This Book

This is Part 47 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 46 we decided on seven Wazuh alert fields to pass to the LLM. Here, to decide where to integrate that allowlist, we examine the existing implementation of the AI Defense Manager on VM 230, read-only.

1. Check VM 230's network and listening services
2. Examine the list of APIs and the input shapes (schemas)
3. Trace the module structure, the dependencies, and the data flow from Wazuh alerts to the LLM
4. Check the current conversion (fields, event IDs, severity, classification) and decide the target specification
5. Confirm that there are no tests and no Git, and decide the preparations before changing anything

Source bodies, SQL and secrets are not displayed. No files are changed, no services restarted and nothing is sent to the LLM.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

## Chapter 1: VM 230's Network and Services

### 1.1 Address and Listening Ports

> **Run on: VM 230**

```bash
echo "===== VM230 IDENTITY ====="
hostname
ip -br -4 addr

echo
echo "===== VM230 ROUTING ====="
ip route

echo
echo "===== VM230 LISTENING PORTS ====="
ss -lnt
```

| Item | Result |
|---|---|
| IPv4 | `192.168.0.33/24` (`enp6s18`). At this point an address received by DHCP (fixed to `192.168.0.221` in a later part) |
| Gateway | `192.168.0.1` |
| SSH | `0.0.0.0:22` |
| Application | `127.0.0.1:8000` only |

Port 8000 listens only on the loopback address and is not set up for direct connection from VM 220. **Port 8000 is not exposed externally.**

### 1.2 The Service on Port 8000

> **Run on: VM 230**

```bash
echo "===== PORT 8000 PROCESS ====="
PID="$(ss -lntp 2>/dev/null | sed -n 's/.*127\.0\.0\.1:8000.*pid=\([0-9]*\).*/\1/p' | head -1)"

if [ -n "$PID" ]; then
    ps -p "$PID" -o pid,ppid,user,comm,args
    echo
    echo "===== PROCESS EXECUTABLE AND WORKDIR ====="
    readlink -f "/proc/$PID/exe"
    readlink -f "/proc/$PID/cwd"
    echo
    echo "===== SYSTEMD UNIT ====="
    systemctl status "$PID" --no-pager -l 2>&1 | head -35
else
    echo "PORT_8000_PID_NOT_IDENTIFIED"
fi

echo
echo "===== RELEVANT SYSTEMD SERVICES ====="
systemctl list-units --type=service --state=running --no-legend |
    grep -Ei 'ai|defense|uvicorn|fastapi|python|gunicorn' |
    head -40

echo
echo "===== LOCAL HTTP RESPONSE ====="
for path in / /health /openapi.json; do
    echo "--- PATH=$path ---"
    curl -sS --connect-timeout 2 --max-time 5 \
        -o /dev/null \
        -w 'HTTP_STATUS=%{http_code} CONTENT_TYPE=%{content_type}\n' \
        "http://127.0.0.1:8000$path" || true
done

echo
echo "RESPONSE_BODY_DISPLAYED=NO"
echo "ENVIRONMENT_VARIABLES_DISPLAYED=NO"
```

The FastAPI/Uvicorn `AI Defense Manager API` is started automatically by systemd and running, the project is in `/opt/ai-defense-manager`, and `/health` and `/openapi.json` returned `HTTP 200`. There is no need to add a new API server.

## Chapter 2: APIs and Input Shapes

### 2.1 List of APIs

> **Run on: VM 230**

```bash
echo "===== AI DEFENSE MANAGER OPENAPI ROUTE INVENTORY ====="

python3 - <<'PY'
import json
import urllib.request

url = "http://127.0.0.1:8000/openapi.json"

try:
    with urllib.request.urlopen(url, timeout=5) as response:
        spec = json.load(response)
except Exception as exc:
    print("OPENAPI_READ_FAILED=" + type(exc).__name__)
    raise SystemExit(0)

print("API_TITLE=" + str(spec.get("info", {}).get("title", "unknown")))
print("API_VERSION=" + str(spec.get("info", {}).get("version", "unknown")))

paths = spec.get("paths", {})
print(f"PATH_COUNT={len(paths)}")

for path, methods in sorted(paths.items()):
    for method, operation in sorted(methods.items()):
        if method.lower() not in {
            "get", "post", "put", "patch", "delete", "options", "head"
        }:
            continue

        tags = operation.get("tags", [])
        operation_id = operation.get("operationId", "")
        request_body = operation.get("requestBody", {})
        body_required = request_body.get("required", False)

        print(
            f"{method.upper():7} {path} "
            f"TAGS={','.join(tags)} "
            f"OPERATION_ID={operation_id} "
            f"REQUEST_BODY={bool(request_body)} "
            f"BODY_REQUIRED={body_required}"
        )

print("SCHEMA_PROPERTY_VALUES_DISPLAYED=NO")
print("REQUEST_EXAMPLES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
PY
```

| API | Method | Purpose |
|---|---|---|
| `/api/v1/analysis` | POST | AI analysis |
| `/api/v1/wazuh/analyze` | POST | analysis of Wazuh events |
| `/api/v1/wazuh/events` | GET | retrieval of Wazuh events |
| `/health` | GET | status check |

APIs that integrate with Wazuh already exist. Rather than building a new entry point, we examine whether these fit the seven-field allowlist.

### 2.2 Input Shape

> **Run on: VM 230**

```bash
echo "===== EXISTING API INPUT SCHEMA INVENTORY ====="

python3 - <<'PY'
import json
import urllib.request

url = "http://127.0.0.1:8000/openapi.json"

with urllib.request.urlopen(url, timeout=5) as response:
    spec = json.load(response)

schemas = spec.get("components", {}).get("schemas", {})

print("===== REQUEST BODY REFERENCES =====")
for path, methods in sorted(spec.get("paths", {}).items()):
    for method, operation in sorted(methods.items()):
        body = operation.get("requestBody")
        if not body:
            continue

        content = body.get("content", {})
        for content_type, details in content.items():
            schema = details.get("schema", {})
            print(
                f"{method.upper()} {path} "
                f"CONTENT_TYPE={content_type} "
                f"SCHEMA_REF={schema.get('$ref', 'inline')}"
            )

print("\n===== COMPONENT SCHEMAS =====")
for name, schema in sorted(schemas.items()):
    print(f"\nSCHEMA={name}")
    print(f"TYPE={schema.get('type', 'unspecified')}")
    print(f"REQUIRED_FIELDS={','.join(schema.get('required', []))}")

    for prop, definition in sorted(schema.get("properties", {}).items()):
        prop_type = definition.get("type", "unspecified")
        if "$ref" in definition:
            prop_type = definition["$ref"]
        elif "items" in definition:
            item_type = definition["items"].get(
                "type",
                definition["items"].get("$ref", "unspecified")
            )
            prop_type += f"[{item_type}]"

        print(f"  FIELD={prop} TYPE={prop_type}")

print("\nVALUES_AND_EXAMPLES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
print("DATABASE_CONTENT_DISPLAYED=NO")
PY
```

The existing `SecurityEvent` has the following shape, which differs in both names and structure from the seven fields of Part 46.

- Required: `source`, `severity`, `event_category`, `event_summary`
- Optional: `event_id`, `observed_at`, `agent_id`, `agent_name`, `source_ip`, `destination_ip`, `rule_id`, `rule_description`

## Chapter 3: Modules and Data Flow

### 3.1 Source Layout

> **Run on: VM 230**

```bash
echo "===== AI DEFENSE MANAGER SOURCE STRUCTURE ====="

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

targets = {
    "SecurityEvent",
    "WazuhAnalysisRequest",
    "AIAnalysisRequest",
    "AIAnalysisProposal",
    "analyze_wazuh_events_api_v1_wazuh_analyze_post",
    "get_wazuh_events_api_v1_wazuh_events_get",
    "create_analysis_api_v1_analysis_post",
}

if not root.is_dir():
    print("APP_DIRECTORY_NOT_FOUND")
else:
    for path in sorted(root.rglob("*.py")):
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception as exc:
            print(f"PARSE_ERROR_FILE={path.relative_to(root)} TYPE={type(exc).__name__}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in targets:
                    kind = type(node).__name__
                    print(
                        f"DEFINITION={node.name} "
                        f"KIND={kind} "
                        f"FILE={path.relative_to(root)} "
                        f"LINE={node.lineno}"
                    )

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = []
                if isinstance(node, ast.Import):
                    names = [x.name for x in node.names]
                else:
                    names = [node.module or ""] + [x.name for x in node.names]

                joined = " ".join(names).lower()
                if any(x in joined for x in (
                    "sqlalchemy", "sqlite", "psycopg",
                    "asyncpg", "qdrant", "wazuh"
                )):
                    print(
                        f"RELEVANT_IMPORT_FILE={path.relative_to(root)} "
                        f"LINE={node.lineno} "
                        f"MODULE_CATEGORY="
                        f"{','.join(x for x in ('sqlalchemy','sqlite','postgresql','qdrant','wazuh') if x in joined)}"
                    )

print("SOURCE_CODE_CONTENT_DISPLAYED=NO")
print("ENVIRONMENT_VARIABLES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
PY
```

The APIs are split into `api/analysis.py` and `api/wazuh.py`, the input shapes are in `schemas/`, and the analysis history is in `services/analysis_history.py`.

### 3.2 Internal Structure

Using Python's AST, we extract only the names of functions, classes, modules used and functions that access the DB.

> **Run on: VM 230**

```bash
echo "===== AI DEFENSE MANAGER INTERNAL STRUCTURE ====="

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

files = [
    "api/analysis.py",
    "api/wazuh.py",
    "services/analysis_history.py",
    "schemas/security_event.py",
    "schemas/wazuh.py",
    "schemas/analysis.py",
]

interesting_calls = {
    "connect", "execute", "executemany", "commit", "rollback",
    "fetchone", "fetchall", "get_alerts", "get_agents",
    "analyze", "create_analysis", "save", "load",
}

for relative in files:
    path = root / relative
    print(f"\nFILE={relative}")

    if not path.is_file():
        print("STATUS=NOT_FOUND")
        continue

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"PARSE_ERROR={type(exc).__name__}")
        continue

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            print(f"DEFINITION={type(node).__name__}:{node.name}:LINE={node.lineno}")

    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])

    selected = sorted(
        m for m in modules
        if m in {
            "sqlite3", "sqlalchemy", "psycopg", "asyncpg",
            "requests", "httpx", "wazuh", "json", "pydantic"
        }
    )
    print("RELEVANT_MODULES=" + ",".join(selected))

    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            else:
                continue

            if name in interesting_calls:
                calls.add(name)

    print("RELEVANT_CALL_NAMES=" + ",".join(sorted(calls)))

print("\nSOURCE_CODE_DISPLAYED=NO")
print("SQL_TEXT_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
PY
```

SQLite was used to store the analysis history.

### 3.3 Dependencies

> **Run on: VM 230**

```bash
echo "===== AI DEFENSE MANAGER MODULE DEPENDENCY MAP ====="

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

if not root.is_dir():
    print("APP_DIRECTORY_NOT_FOUND")
else:
    for path in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"PARSE_ERROR={path.relative_to(root)}:{type(exc).__name__}")
            continue

        rel = path.relative_to(root)
        definitions = []
        imports = set()
        calls = set()
        routes = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name not in definitions:
                    definitions.append(node.name)

            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith(("api", "schemas", "services", "core")):
                    imports.add(node.module)

            if isinstance(node, ast.Call):
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else (
                    func.id if isinstance(func, ast.Name) else ""
                )
                if any(x in name.lower() for x in (
                    "wazuh", "analysis", "history", "ollama",
                    "sqlite", "database", "client", "request"
                )):
                    calls.add(name)

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        func = decorator.func
                        name = func.attr if isinstance(func, ast.Attribute) else (
                            func.id if isinstance(func, ast.Name) else ""
                        )
                        if name in ("get", "post", "put", "delete", "patch"):
                            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                routes.append(f"{name.upper()} {decorator.args[0].value}")

        if definitions or imports or calls or routes:
            print(f"\nMODULE={rel}")
            if definitions:
                print("DEFINITIONS=" + ",".join(definitions))
            if imports:
                print("LOCAL_IMPORTS=" + ",".join(sorted(imports)))
            if calls:
                print("RELEVANT_CALLS=" + ",".join(sorted(calls)))
            if routes:
                print("ROUTES=" + ",".join(routes))

print("\nSOURCE_CODE_DISPLAYED=NO")
print("SQL_TEXT_DISPLAYED=NO")
print("ENVIRONMENT_VARIABLES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
PY
```

| Module | Role |
|---|---|
| `services/wazuh_relay.py` | retrieving and converting Wazuh alerts |
| `services/event_sanitizer.py` | masking event summaries, masking IP addresses |
| `services/ai_analysis.py` | AI analysis |
| `services/analysis_history.py` | SQLite analysis history |
| `schemas/action.py` | defensive action proposals, approval state, validation |
| `schemas/analysis_proposal.py` | AI analysis results and action constraints |

### 3.4 Masking, Retrieval and Analysis

> **Run on: VM 230**

```bash
echo "===== SANITIZER / RELAY / ANALYSIS INTERFACE AUDIT ====="

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

targets = [
    "services/event_sanitizer.py",
    "services/wazuh_relay.py",
    "services/ai_analysis.py",
    "schemas/security_event.py",
    "schemas/action.py",
    "schemas/analysis_proposal.py",
    "core/config.py",
]

def annotation(node):
    if node is None:
        return "unspecified"
    try:
        result = ast.unparse(node)
        return result[:100]
    except Exception:
        return "unavailable"

for relative in targets:
    path = root / relative
    print(f"\nFILE={relative}")

    if not path.is_file():
        print("STATUS=NOT_FOUND")
        continue

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"PARSE_ERROR={type(exc).__name__}")
        continue

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [
                arg.arg for arg in (
                    node.args.posonlyargs
                    + node.args.args
                    + node.args.kwonlyargs
                )
            ]
            print(
                f"FUNCTION={node.name} "
                f"ARGS={','.join(args)} "
                f"RETURN={annotation(node.returns)} "
                f"LINE={node.lineno}"
            )

        elif isinstance(node, ast.ClassDef):
            print(f"CLASS={node.name} LINE={node.lineno}")

            for child in node.body:
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    print(
                        f"  FIELD={child.target.id} "
                        f"TYPE={annotation(child.annotation)}"
                    )

                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if child.name.startswith("validate") or child.name.startswith("model_"):
                        print(f"  METHOD={child.name}")

    calls = set()
    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = (
                func.attr if isinstance(func, ast.Attribute)
                else func.id if isinstance(func, ast.Name)
                else ""
            )
            if name:
                calls.add(name)

        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith(("services", "schemas", "core")):
                imports.add(node.module)

    print("LOCAL_IMPORTS=" + ",".join(sorted(imports)))
    print("CALL_NAMES=" + ",".join(sorted(calls)))

print("\nSOURCE_CODE_DISPLAYED=NO")
print("FUNCTION_BODIES_DISPLAYED=NO")
print("CONFIGURATION_VALUES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
PY
```

| Function | Current implementation | Assessment |
|---|---|---|
| Wazuh retrieval | `fetch_wazuh_events()` | use as is |
| Wazuh conversion | `_convert_alert()` | where the allowlist goes |
| IP address masking | `sanitize_event_summary()` | use as is |
| AI analysis | `analyze_events()` | use as is |
| AI output validation | Pydantic `model_validate()` | use as is |
| Action constraints | `validate_action` | an important foundation for safety |
| Approval management | `ApprovalStatus` | used for human approval |

The target flow is as follows.

```text
Wazuh alerts.json
       │
       ▼
wazuh_relay.py
       │
       ▼
Dedicated Wazuh normalization and validation
       │
       ▼
LLM input DTO limited to 7 fields
       │
       ▼
ai_analysis.py
       │
       ▼
AIAnalysisProposal
       │
       ▼
Deterministic policy validation
       │
       ▼
Action Gateway
```

### 3.5 Tracing the Data Flow

> **Run on: VM 230**

```bash
echo "===== EXISTING EVENT DATAFLOW AUDIT ====="

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

targets = [
    "api/wazuh.py",
    "api/analysis.py",
    "services/wazuh_relay.py",
    "services/ai_analysis.py",
    "services/event_sanitizer.py",
]

for relative in targets:
    path = root / relative
    print(f"\nMODULE={relative}")

    if not path.is_file():
        print("STATUS=NOT_FOUND")
        continue

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"PARSE_ERROR={type(exc).__name__}")
        continue

    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            names = ",".join(alias.name for alias in node.names)
            print(
                f"IMPORT_FROM={node.module or '.'} "
                f"SYMBOLS={names}"
            )

        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            print(f"\nFUNCTION={node.name}")

            for child in ast.walk(node):
                if isinstance(child, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                    targets_list = []

                    raw_targets = (
                        child.targets if isinstance(child, ast.Assign)
                        else [child.target]
                    )

                    for target in raw_targets:
                        if isinstance(target, ast.Name):
                            targets_list.append(target.id)
                        elif isinstance(target, ast.Attribute):
                            targets_list.append(target.attr)

                    if targets_list:
                        print("  ASSIGN_TARGETS=" + ",".join(targets_list))

                elif isinstance(child, ast.Call):
                    func = child.func
                    name = (
                        func.attr if isinstance(func, ast.Attribute)
                        else func.id if isinstance(func, ast.Name)
                        else "dynamic"
                    )
                    keywords = ",".join(
                        keyword.arg or "**kwargs"
                        for keyword in child.keywords
                    )
                    if name in (
                        "SecurityEvent", "AIAnalysisRequest",
                        "analyze_events", "fetch_wazuh_events",
                        "_convert_alert", "sanitize_event_summary",
                        "model_validate", "model_dump", "post",
                        "json", "dumps", "loads"
                    ):
                        print(
                            f"  CALL={name} "
                            f"KEYWORDS={keywords or 'none'}"
                        )

                elif isinstance(child, ast.Attribute):
                    if child.attr in (
                        "event_summary", "source", "severity",
                        "event_category", "rule_id",
                        "rule_description", "agent_id",
                        "agent_name", "source_ip", "destination_ip",
                        "full_log", "data", "timestamp"
                    ):
                        print(f"  FIELD_ACCESS={child.attr}")

print("\nSOURCE_CODE_DISPLAYED=NO")
print("FUNCTION_BODIES_DISPLAYED=NO")
print("SQL_AND_CONFIGURATION_VALUES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
PY
```

Raw Wazuh alerts are converted to `SecurityEvent` in `wazuh_relay.py`, then `ai_analysis.py` masks `event_summary` and sends it to the AI. Masking just before sending to the AI cannot guarantee that no extra fields slip in, so we use the following two stages.

1. Right after Wazuh retrieval: extract and check only the allowed fields
2. Right before sending to the AI: keep the current masking and check the input once more

## Chapter 4: The Current Conversion

### 4.1 Input and Output Fields

> **Run on: VM 230**

```bash
echo "===== WAZUH INPUT / AI OUTPUT FIELD AUDIT ====="

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

targets = {
    "services/wazuh_relay.py": ["_convert_alert"],
    "services/ai_analysis.py": ["analyze_events"],
}

for relative, wanted in targets.items():
    path = root / relative
    print(f"\nMODULE={relative}")

    if not path.is_file():
        print("STATUS=NOT_FOUND")
        continue

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"PARSE_ERROR={type(exc).__name__}")
        continue

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name not in wanted:
            continue

        print(f"\nFUNCTION={node.name}")

        for child in ast.walk(node):
            if isinstance(child, ast.Subscript):
                value = child.value
                base = (
                    ast.unparse(value)
                    if isinstance(value, (ast.Name, ast.Attribute))
                    else "complex"
                )
                key = child.slice
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    print(f"  INPUT_KEY={base}[{key.value!r}]")

            elif isinstance(child, ast.Call):
                func = child.func
                name = (
                    func.attr if isinstance(func, ast.Attribute)
                    else func.id if isinstance(func, ast.Name)
                    else "dynamic"
                )

                if name in (
                    "SecurityEvent", "sanitize_event_summary",
                    "model_dump", "dumps", "post", "json"
                ):
                    print(f"  CALL={name}")
                    for keyword in child.keywords:
                        if keyword.arg:
                            try:
                                expression = ast.unparse(keyword.value)
                            except Exception:
                                expression = "unavailable"
                            print(
                                f"    ARG={keyword.arg} "
                                f"EXPRESSION={expression[:180]}"
                            )

            elif isinstance(child, ast.Dict):
                keys = []
                for key in child.keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        keys.append(key.value)
                if keys:
                    print("  DICT_KEYS=" + ",".join(keys))

print("\nALERT_VALUES_DISPLAYED=NO")
print("TOKENS_OR_CREDENTIALS_DISPLAYED=NO")
print("SOURCE_FILES_MODIFIED=NO")
print("DATABASE_ACCESSED=NO")
PY
```

Besides the seven fields, `_convert_alert()` also passed `agent_name` to `SecurityEvent`. What is sent to the AI is six fields: `event_id`, `observed_at`, `severity`, `rule_id`, `event_category` and `event_summary`. The raw Wazuh data is not sent wholesale, but this is not an input boundary limited to the seven fields.

| Wazuh field | Field inside VM 230 |
|---|---|
| `timestamp` | `observed_at` |
| `rule.id` | `rule_id` |
| `rule.level` | `severity` |
| `rule.groups` | `event_category` |
| `rule.description` | `rule_description` |
| `decoder.name` | not stored |
| `agent.id` | `agent_id` |

`agent_name`, IP addresses, `full_log`, `data`, `location` and `predecoder` are removed at the input boundary.

### 4.2 Event IDs

> **Run on: VM 230**

```bash
echo "===== EVENT ID / WAZUH KEY / SANITIZER AUDIT ====="

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

targets = {
    "services/wazuh_relay.py": ["_severity", "_convert_alert"],
    "services/event_sanitizer.py": ["sanitize_event_summary"],
    "schemas/security_event.py": [],
    "schemas/analysis_proposal.py": [],
}

for relative, wanted in targets.items():
    path = root / relative
    print(f"\nMODULE={relative}")

    if not path.is_file():
        print("STATUS=NOT_FOUND")
        continue

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"PARSE_ERROR={type(exc).__name__}")
        continue

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if wanted and node.name not in wanted:
                continue

            print(f"\nFUNCTION={node.name}")

            for child in ast.walk(node):
                if isinstance(child, ast.Subscript):
                    try:
                        expression = ast.unparse(child)
                    except Exception:
                        expression = "unavailable"
                    print(f"  SUBSCRIPT={expression[:160]}")

                elif isinstance(child, ast.Call):
                    func = child.func
                    name = (
                        func.attr if isinstance(func, ast.Attribute)
                        else func.id if isinstance(func, ast.Name)
                        else ""
                    )
                    if name in (
                        "UUID", "uuid4", "Field", "ip_address",
                        "sanitize_event_summary", "strip", "sub",
                        "SecurityEvent"
                    ):
                        print(f"  CALL={name}")

        elif isinstance(node, ast.ClassDef):
            print(f"\nCLASS={node.name}")
            for child in node.body:
                if isinstance(child, ast.AnnAssign):
                    if isinstance(child.target, ast.Name):
                        try:
                            default = (
                                ast.unparse(child.value)
                                if child.value is not None else "REQUIRED"
                            )
                        except Exception:
                            default = "UNAVAILABLE"
                        print(
                            f"  FIELD={child.target.id} "
                            f"DEFAULT={default[:100]}"
                        )

                elif isinstance(child, ast.FunctionDef):
                    print(f"  METHOD={child.name}")

print("\nEVENT_CONTENT_DISPLAYED=NO")
print("SOURCE_CODE_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
print("FILES_MODIFIED=NO")
PY
```

- `SecurityEvent.event_id` is generated automatically with `uuid4`
- Wazuh's `rule.id` is kept as a separate field
- `evidence_event_ids` in AI proposals require UUIDs

**Do not use Wazuh rule IDs as event UUIDs.** Also, `ttl_seconds` in AI proposals has a maximum of 900 seconds, and `requires_human_approval` defaults to `True`. These constraints are kept.

### 4.3 How the Wazuh Fields Are Used

> **Run on: VM 230**

```bash
echo "===== WAZUH RELAY FIELD ACCESS AUDIT ====="

python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/opt/ai-defense-manager/app/services/wazuh_relay.py")
tree = ast.parse(path.read_text(encoding="utf-8"))

wanted = {"_convert_alert", "fetch_wazuh_events"}

for node in tree.body:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    if node.name not in wanted:
        continue

    print(f"\nFUNCTION={node.name}")

    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            name = (
                func.attr if isinstance(func, ast.Attribute)
                else func.id if isinstance(func, ast.Name)
                else ""
            )

            if name == "get":
                base = (
                    ast.unparse(func.value)
                    if isinstance(func, ast.Attribute)
                    else "unknown"
                )
                key = (
                    ast.literal_eval(child.args[0])
                    if child.args and isinstance(child.args[0], ast.Constant)
                    else "dynamic"
                )
                print(f"  GET_BASE={base} KEY={key!r}")

            elif name == "SecurityEvent":
                for keyword in child.keywords:
                    print(f"  SECURITY_EVENT_FIELD={keyword.arg}")

            elif name in ("json", "loads", "read_text"):
                print(f"  CALL={name}")

        elif isinstance(child, ast.Subscript):
            try:
                base = ast.unparse(child.value)
                key = ast.literal_eval(child.slice)
            except Exception:
                continue
            if isinstance(key, str):
                print(f"  SUBSCRIPT_BASE={base} KEY={key!r}")

print("\nALERT_VALUES_DISPLAYED=NO")
print("TOKEN_CONTENT_DISPLAYED=NO")
print("SOURCE_CODE_DISPLAYED=NO")
print("FILES_MODIFIED=NO")
PY
```

`_convert_alert()` referred to `timestamp`, `rule.level`, `rule.id`, `rule.description`, `agent.id`, `agent.name`, `location` and `decoder.name`. It did not read `rule.groups` directly but went through a dictionary for classification.

### 4.4 Severity and Classification Mapping

> **Run on: VM 230**

```bash
echo "===== EXISTING CATEGORY / SEVERITY MAPPING AUDIT ====="

python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/opt/ai-defense-manager/app/services/wazuh_relay.py")
tree = ast.parse(path.read_text(encoding="utf-8"))

for node in tree.body:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue

    if node.name not in ("_severity", "_convert_alert"):
        continue

    print(f"\nFUNCTION={node.name}")

    for child in ast.walk(node):
        if isinstance(child, ast.Assign):
            for target in child.targets:
                if not isinstance(target, ast.Name):
                    continue

                if target.id not in ("category_map",):
                    continue

                print(f"  CONSTANT_MAP={target.id}")

                if isinstance(child.value, ast.Dict):
                    for key, value in zip(child.value.keys, child.value.values):
                        try:
                            k = ast.literal_eval(key)
                            v = ast.literal_eval(value)
                            print(f"    {k!r} -> {v!r}")
                        except Exception:
                            print("    NON_LITERAL_ENTRY=YES")

        elif isinstance(child, ast.Match):
            print("  MATCH_STATEMENT=YES")

        elif isinstance(child, ast.Compare):
            try:
                expression = ast.unparse(child)
            except Exception:
                continue

            if any(term in expression.lower() for term in ("level", "severity")):
                print(f"  COMPARISON={expression[:180]}")

print("\nALERT_VALUES_DISPLAYED=NO")
print("SOURCE_CODE_DISPLAYED=NO")
print("CONFIGURATION_VALUES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
print("FILES_MODIFIED=NO")
PY
```

Kept as the current specification:

| Wazuh Level | Internal severity |
|---|---|
| 0–3 | info |
| 4–7 | low |
| 8–11 | medium |
| 12–14 | high |
| 15–16 | critical |

| Classification from Wazuh | Internal classification |
|---|---|
| pvedaemon | virtualization_management |
| pam | authentication |
| sshd | remote_access |
| useradd | account_management |
| open-userdel | account_management |

`rule.groups` has multiple values, so we classify only by allowed groups and do not let unknown values flow into the internal classification as is.

## Chapter 5: Preparing Before the Change

### 5.1 Tests and Version Control

> **Run on: VM 230**

```bash
echo "===== AI DEFENSE MANAGER TEST INVENTORY ====="

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager")

test_dirs = [
    root / "tests",
    root / "app" / "tests",
]

found = set()

for directory in test_dirs:
    if not directory.is_dir():
        continue

    for path in sorted(directory.rglob("test_*.py")):
        found.add(path)

for path in sorted(found):
    print(f"\nTEST_FILE={path.relative_to(root)}")

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"PARSE_ERROR={type(exc).__name__}")
        continue

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                print(f"  TEST={node.name}")

                names = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Name):
                        names.add(child.id)
                    elif isinstance(child, ast.Attribute):
                        names.add(child.attr)

                relevant = sorted(
                    name for name in names
                    if any(term in name.lower() for term in (
                        "wazuh", "severity", "category", "analysis",
                        "event", "sanitize", "proposal", "payload",
                        "uuid", "ollama"
                    ))
                )
                if relevant:
                    print("    REFERENCES=" + ",".join(relevant))

print(f"\nTEST_FILE_COUNT={len(found)}")
print("TESTS_EXECUTED=NO")
print("SOURCE_CODE_DISPLAYED=NO")
print("DATABASE_ACCESSED=NO")
print("FILES_MODIFIED=NO")
PY

echo
echo "===== PROJECT VERSION CONTROL STATUS ====="
if git -C /opt/ai-defense-manager rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git -C /opt/ai-defense-manager status --short
else
    echo "GIT_REPOSITORY=NO"
fi
```

There were no test files and no Git repository. When the code is changed, it can neither be reverted with Git nor protected by existing tests. So our policy is to prepare the following new tests.

| Test | What it checks |
|---|---|
| Input allowlist | nothing beyond the seven fields is mixed in |
| Required fields | missing values, wrong types and invalid values are rejected |
| Removing secrets | `full_log`, `data`, IPs, user names and so on are not sent to the AI |
| Severity mapping | the boundaries of 0–16 |
| Classification mapping | the current five classifications and unknown classifications |
| UUID | correspondence between event IDs and evidence IDs |
| What is sent to the AI | inspect the JSON to be sent without actually communicating |
| Action safety | keep the 900-second TTL limit and the approval requirement |

### 5.2 Free Space and Target Files

> **Run on: VM 230**

```bash
echo "===== PRE-IMPLEMENTATION SAFETY INVENTORY ====="

echo "--- Project filesystem ---"
df -h /opt/ai-defense-manager /var/backups

echo
echo "--- Target file metadata ---"
for f in \
  /opt/ai-defense-manager/app/services/wazuh_relay.py \
  /opt/ai-defense-manager/app/services/event_sanitizer.py \
  /opt/ai-defense-manager/app/services/ai_analysis.py \
  /opt/ai-defense-manager/app/schemas/security_event.py \
  /opt/ai-defense-manager/app/api/wazuh.py
do
  if [ -f "$f" ]; then
    stat -c 'FILE=%n SIZE=%s MODE=%a OWNER=%U:%G MTIME=%y' "$f"
    sha256sum "$f"
  else
    echo "MISSING=$f"
  fi
done

echo
echo "--- Existing backup directories ---"
for d in /var/backups/ai-defense-manager /opt/ai-defense-manager/backups; do
  if [ -d "$d" ]; then
    stat -c 'DIRECTORY=%n MODE=%a OWNER=%U:%G' "$d"
  else
    echo "NOT_FOUND=$d"
  fi
done

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service
```

| Item | Result |
|---|---|
| Free space on VM 230 | about 39GB |
| Target files | 5 |
| SHA256 | taken for all 5 |
| Dedicated backup directory | not yet present |
| AI Defense Manager | `active` |
| Git | none |

## Closing Notes

In Part 47 we examined the existing implementation of the AI Defense Manager on VM 230.

| Item | Result |
|---|---|
| API | FastAPI/Uvicorn, `127.0.0.1:8000` only; APIs for Wazuh retrieval and analysis exist |
| Where the allowlist goes | `_convert_alert()` in `services/wazuh_relay.py` (right after retrieval) and right before sending to the AI in `services/ai_analysis.py` |
| Kept | the masking, `uuid4` event IDs, the severity mapping, the 900-second TTL, human approval |
| Preparation | no tests or Git, so take a backup before changing and check with independent tests |

In the next part, Part 48, we take a backup before the change, narrow the Wazuh event conversion to seven fields, and test it with synthetic data.

# Part 48: Narrowing the Wazuh Event Conversion to Seven Fields
## Introduction

### About This Book

This is Part 48 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 47 we examined the existing implementation of the AI Defense Manager (VM 230) and decided where to put the allowlist. Here we actually change the code.

1. Before changing anything, save copies of the five target files
2. Check the environment for running tests and the module import path
3. Tally the actual groups, in order to switch classification from `location` and `decoder.name` to `rule.groups`
4. Using Python syntax analysis (AST), rewrite only two files (`wazuh_relay.py` and `ai_analysis.py`)
5. Run 26 unit tests with synthetic events and check the diff

No actual communication with Wazuh or Ollama, no writes to PostgreSQL or SQLite, and no service restarts.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **VM 220**: security-core (root)

## Chapter 1: Saving the Files Before the Change

We create a directory per date and time under `/var/backups/ai-defense-manager/`, copy with `cp -a` to keep owner, permissions and times, and compare the SHA256 with the originals.

> **Run on: VM 230**

```bash
echo "===== AI DEFENSE MANAGER PRE-CHANGE BACKUP ====="

BACKUP_ROOT="/var/backups/ai-defense-manager"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$STAMP"

echo "--- Create protected backup directory ---"
install -d -m 700 "$BACKUP_ROOT"
install -d -m 700 "$BACKUP_DIR"

echo "BACKUP_DIR=$BACKUP_DIR"

FILES=(
  "app/services/wazuh_relay.py"
  "app/services/event_sanitizer.py"
  "app/services/ai_analysis.py"
  "app/schemas/security_event.py"
  "app/api/wazuh.py"
)

BACKUP_OK=1

for REL in "${FILES[@]}"; do
  SRC="/opt/ai-defense-manager/$REL"
  DST="$BACKUP_DIR/$REL"

  echo
  echo "--- BACKUP: $REL ---"

  if [ ! -f "$SRC" ]; then
    echo "ERROR=SOURCE_NOT_FOUND"
    BACKUP_OK=0
    continue
  fi

  install -d -m 700 "$(dirname "$DST")"

  if cp -a "$SRC" "$DST"; then
    echo "COPY=OK"
  else
    echo "COPY=FAILED"
    BACKUP_OK=0
    continue
  fi

  SRC_HASH="$(sha256sum "$SRC" | awk '{print $1}')"
  DST_HASH="$(sha256sum "$DST" | awk '{print $1}')"

  echo "SOURCE_SHA256=$SRC_HASH"
  echo "BACKUP_SHA256=$DST_HASH"

  if [ "$SRC_HASH" = "$DST_HASH" ] && cmp -s "$SRC" "$DST"; then
    echo "VERIFY=PASS"
  else
    echo "VERIFY=FAILED"
    BACKUP_OK=0
  fi

  stat -c 'BACKUP_OWNER=%U:%G MODE=%a SIZE=%s' "$DST"
done

echo
echo "===== BACKUP RESULT ====="

if [ "$BACKUP_OK" -eq 1 ]; then
  echo "BACKUP_STATUS=SUCCESS"
else
  echo "BACKUP_STATUS=FAILED"
fi

echo "BACKUP_DIR=$BACKUP_DIR"
echo "PRODUCTION_SERVICE_MODIFIED=NO"
echo "APPLICATION_FILES_MODIFIED=NO"
echo "DATABASE_ACCESSED=NO"
```

The copies and SHA256 comparisons of all five files succeeded. The copies are in `/var/backups/ai-defense-manager/20261123-031115`. The `root:ai-defense`, `640` of `wazuh_relay.py` and the others are also preserved.

## Chapter 2: Checking the Test Environment

### 2.1 Python and Test Tools

No new packages are installed.

> **Run on: VM 230**

```bash
echo "===== ISOLATED TEST ENVIRONMENT AUDIT ====="

APP="/opt/ai-defense-manager"
VENV="$APP/venv"

echo "--- Python and test runner ---"
"$VENV/bin/python" --version
"$VENV/bin/python" -m pytest --version 2>&1

echo
echo "--- Required module availability ---"
"$VENV/bin/python" - <<'PY'
import importlib.util

modules = [
    "pytest",
    "pydantic",
    "httpx",
    "fastapi",
    "app",
]

for name in modules:
    try:
        spec = importlib.util.find_spec(name)
        print(f"{name}={'AVAILABLE' if spec else 'NOT_FOUND'}")
    except Exception as exc:
        print(f"{name}=CHECK_ERROR:{type(exc).__name__}")
PY

echo
echo "--- Project test/config metadata ---"
for f in \
  "$APP/pyproject.toml" \
  "$APP/pytest.ini" \
  "$APP/setup.cfg" \
  "$APP/requirements.txt" \
  "$APP/requirements-dev.txt"
do
  if [ -f "$f" ]; then
    stat -c 'FOUND=%n SIZE=%s MODE=%a' "$f"
  else
    echo "NOT_FOUND=$f"
  fi
done

echo
echo "--- Backup integrity summary ---"
find /var/backups/ai-defense-manager/20261123-031115 \
  -type f -printf '%P %s bytes\n' | sort

echo
echo "APPLICATION_FILES_MODIFIED=NO"
echo "PACKAGES_INSTALLED=NO"
echo "SERVICE_RESTARTED=NO"
```

Python 3.12.3, FastAPI, Pydantic and HTTPX are available, but `pytest` was not installed. We do not install `pytest` and use Python's standard `unittest` instead.

### 2.2 Module Import Path

> **Run on: VM 230**

```bash
echo "===== APPLICATION IMPORT PATH AUDIT ====="

APP="/opt/ai-defense-manager"
VENV="$APP/venv"

echo "--- Import from project root ---"
cd "$APP" && "$VENV/bin/python" - <<'PY'
import importlib
import sys

print("PYTHON_EXECUTABLE=" + sys.executable)
print("WORKING_DIRECTORY=" + __import__("os").getcwd())

modules = [
    "app",
    "app.main",
    "app.schemas.security_event",
    "app.schemas.analysis_proposal",
    "app.services.event_sanitizer",
    "app.services.wazuh_relay",
    "app.services.ai_analysis",
]

for name in modules:
    try:
        importlib.import_module(name)
        print(f"IMPORT={name}:PASS")
    except Exception as exc:
        print(f"IMPORT={name}:FAIL:{type(exc).__name__}")
PY

echo
echo "--- Systemd application execution context ---"
systemctl show ai-defense-manager.service \
  --property=WorkingDirectory \
  --property=User \
  --property=Group \
  --property=ExecStart \
  --no-pager

echo
echo "--- Standard unittest availability ---"
"$VENV/bin/python" -m unittest --help >/dev/null 2>&1
if [ "$?" -eq 0 ]; then
  echo "UNITTEST=AVAILABLE"
else
  echo "UNITTEST=UNAVAILABLE"
fi

echo
echo "APPLICATION_FILES_MODIFIED=NO"
echo "PACKAGES_INSTALLED=NO"
echo "SERVICE_RESTARTED=NO"
```

All existing modules could be imported from `/opt/ai-defense-manager`, and `unittest` was usable. The service runs as the user `ai-defense` with working directory `/opt/ai-defense-manager`, so the tests match these conditions.

### 2.3 The Current Classification and Summary

> **Run on: VM 230**

```bash
echo "===== EXISTING TRANSFORMATION EXPRESSION AUDIT ====="

cd /opt/ai-defense-manager && venv/bin/python - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

def show_assignments(relative, function_name, selected):
    path = root / relative
    tree = ast.parse(path.read_text(encoding="utf-8"))

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != function_name:
            continue

        print(f"\nMODULE={relative} FUNCTION={function_name}")

        for child in ast.walk(node):
            if not isinstance(child, ast.Assign):
                continue

            names = [
                target.id for target in child.targets
                if isinstance(target, ast.Name)
            ]

            for name in names:
                if name not in selected:
                    continue
                try:
                    expression = ast.unparse(child.value)
                except Exception:
                    expression = "UNAVAILABLE"
                print(f"{name} = {expression[:300]}")

            if "category_map" in names and isinstance(child.value, ast.Dict):
                print("CATEGORY_MAP_ENTRIES:")
                for key, value in zip(child.value.keys, child.value.values):
                    try:
                        print(
                            "  "
                            + repr(ast.literal_eval(key))
                            + " -> "
                            + repr(ast.literal_eval(value))
                        )
                    except Exception:
                        print("  NON_LITERAL_ENTRY")

        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                try:
                    expression = ast.unparse(child.value) if child.value else "None"
                except Exception:
                    expression = "UNAVAILABLE"
                print(f"RETURN={expression[:300]}")

show_assignments(
    "services/wazuh_relay.py",
    "_severity",
    {"level"},
)

show_assignments(
    "services/wazuh_relay.py",
    "_convert_alert",
    {
        "timestamp", "level", "rule_id", "description",
        "agent_id", "agent_name", "location", "decoder",
        "observed_at", "raw_category", "category_map",
        "category", "summary",
    },
)

print("\nRAW_ALERT_VALUES_DISPLAYED=NO")
print("CONFIGURATION_VALUES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
print("FILES_MODIFIED=NO")
PY
```

The current classification used `decoder.name` first and fell back to `location`. If `location` is removed, events that were classified only by `location` could become `other`, so we change the classification to use `rule.groups`.

## Chapter 3: Designing the Classification

### 3.1 Tallying the Actual Groups

Wazuh's `alerts.json` is `wazuh:wazuh`, `640`, so run this as **root** on VM 220 (an ordinary user gets `PermissionError`). No values are displayed.

> **Run on: VM 220**

```bash
echo "===== WAZUH CATEGORY MAPPING AGGREGATION ====="

python3 - <<'PY'
import json
from collections import Counter

path = "/var/ossec/logs/alerts/alerts.json"

groups_count = Counter()
decoders = Counter()
locations = Counter()
missing_groups = 0
invalid_records = 0
records = 0

with open(path, encoding="utf-8", errors="replace") as f:
    for line in f:
        if not line.strip():
            continue

        try:
            alert = json.loads(line)
            records += 1
        except Exception:
            invalid_records += 1
            continue

        rule = alert.get("rule")
        if not isinstance(rule, dict):
            rule = {}

        groups = rule.get("groups")
        if isinstance(groups, list):
            for group in groups:
                if isinstance(group, str):
                    groups_count[group.strip().lower()] += 1
        else:
            missing_groups += 1

        decoder = alert.get("decoder")
        if isinstance(decoder, dict):
            name = decoder.get("name")
            if isinstance(name, str):
                decoders[name.strip().lower()] += 1

        location = alert.get("location")
        if isinstance(location, str):
            locations[location.strip().lower()] += 1

print(f"VALID_JSON_RECORDS={records}")
print(f"INVALID_JSON_RECORDS={invalid_records}")
print(f"RECORDS_WITHOUT_GROUPS={missing_groups}")

print("\n--- RULE GROUP COUNTS ---")
for name, count in groups_count.most_common():
    print(f"{name}: {count}")

print("\n--- DECODER NAME COUNTS ---")
for name, count in decoders.most_common():
    print(f"{name}: {count}")

print("\n--- LOCATION COUNTS (NAMES ONLY) ---")
for name, count in locations.most_common(30):
    print(f"{name}: {count}")

print("\nRAW_EVENT_CONTENT_DISPLAYED=NO")
print("FILES_MODIFIED=NO")
PY
```

| Item | Count |
|---|---:|
| Valid JSON | 268 |
| Invalid JSON | 0 |
| No `rule.groups` | 0 |
| `pam` | 228 |
| `proxmox-ve` | 16 |
| `sshd` | 1 |
| `sudo` | 3 |
| `postgresql` | 34 |
| `authentication_failed` | 4 |

Groups are counted with overlap, so the total does not match the number of events.

### 3.2 Classification and Schema Compatibility

> **Run on: VM 230**

```bash
echo "===== CATEGORY AND SCHEMA COMPATIBILITY AUDIT ====="

cd /opt/ai-defense-manager && venv/bin/python - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

targets = {
    "schemas/security_event.py": [
        "SecurityEvent",
        "event_category",
        "source",
    ],
    "services/wazuh_relay.py": [
        "_convert_alert",
        "category_map",
        "raw_category",
        "event_category",
    ],
    "services/ai_analysis.py": [
        "analyze_events",
        "event_category",
    ],
}

for relative, terms in targets.items():
    path = root / relative
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    print(f"\n--- {relative} ---")

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "SecurityEvent":
            print("CLASS=SecurityEvent")
            for item in node.body:
                if isinstance(item, (ast.Assign, ast.AnnAssign)):
                    names = []
                    if isinstance(item, ast.Assign):
                        names = [
                            t.id for t in item.targets
                            if isinstance(t, ast.Name)
                        ]
                    elif isinstance(item.target, ast.Name):
                        names = [item.target.id]

                    if any(term in names for term in terms):
                        print(ast.unparse(item)[:500])

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in terms:
                print(f"\nFUNCTION={node.name}")
                print(ast.unparse(node)[:5000])

    for term in terms:
        if term == "event_category":
            print("EVENT_CATEGORY_LITERAL_OCCURRENCES:")
            for lineno, line in enumerate(source.splitlines(), 1):
                if "event_category" in line:
                    print(f"  LINE={lineno}: {line.strip()[:200]}")

print("\nSOURCE_EVENT_CONTENT_DISPLAYED=NO")
print("CONFIGURATION_VALUES_DISPLAYED=NO")
print("FILES_MODIFIED=NO")
PY
```

`event_category` is a string of 1–64 characters, so adding classifications requires no change to the Pydantic schema. The classifications we decided on are as follows. When there are several specific groups, the higher row takes priority.

| Priority | Wazuh `rule.groups` | Classification |
|---:|---|---|
| 1 | `pvedaemon`, `proxmox-ve` | `virtualization_management` |
| 2 | `pam`, `authentication_success`, `authentication_failed` | `authentication` |
| 3 | `sshd` | `remote_access` |
| 4 | `sudo` | `privilege_escalation` |
| 5 | `useradd`, `open-userdel` | `account_management` |
| 6 | `postgresql` | `database` |
| 7 | other | `other` |

General groups such as `syslog`, `local`, `error` and `access_control` alone do not produce a specific classification.

### 3.3 The Input Boundary

> **Run on: VM 230**

```bash
echo "===== SECURITY EVENT INPUT AND AI BOUNDARY AUDIT ====="

cd /opt/ai-defense-manager && venv/bin/python - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

targets = [
    "schemas/security_event.py",
    "schemas/analysis.py",
    "schemas/analysis_proposal.py",
    "api/analysis.py",
    "api/wazuh.py",
    "services/ai_analysis.py",
]

for relative in targets:
    path = root / relative
    tree = ast.parse(path.read_text(encoding="utf-8"))

    print(f"\n--- {relative} ---")

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            if node.name in {
                "SecurityEvent",
                "AIAnalysisRequest",
                "AIAnalysisProposal",
            }:
                print(ast.unparse(node)[:6500])

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in {
                "create_analysis",
                "analyze_wazuh_events",
                "get_wazuh_events",
                "analyze_events",
            }:
                print(ast.unparse(node)[:6500])

print("\nCONFIGURATION_VALUES_DISPLAYED=NO")
print("CREDENTIALS_DISPLAYED=NO")
print("FILES_MODIFIED=NO")
PY
```

`SecurityEvent` and `AIAnalysisRequest` use `extra='forbid'` (reject unknown fields), which is a good design. However, `/api/v1/analysis` is not Wazuh-specific; it also accepts input from Prometheus and others. So we decide that:

- **Wazuh-specific constraints are applied at Wazuh retrieval (`wazuh_relay.py`)**
- **Where data is sent to the AI, only allowed fields common to all events are sent**

## Chapter 4: Rewriting the Two Files

### 4.1 Last Check Before the Change

> **Run on: VM 230**

```bash
echo "===== PRE-IMPLEMENTATION SOURCE AND BACKUP AUDIT ====="

cd /opt/ai-defense-manager && venv/bin/python - <<'PY'
import ast
import hashlib
from pathlib import Path

app = Path("/opt/ai-defense-manager/app")
backup = Path("/var/backups/ai-defense-manager/20261123-031115")

targets = {
    "services/wazuh_relay.py": [
        "_severity",
        "_convert_alert",
        "fetch_wazuh_events",
    ],
    "services/event_sanitizer.py": [
        "sanitize_event_summary",
        "redact_ip",
    ],
    "services/ai_analysis.py": [
        "analyze_events",
    ],
}

for relative, functions in targets.items():
    source_path = app / relative
    backup_path = backup / "app" / relative

    print(f"\n===== {relative} =====")
    print(f"SOURCE_EXISTS={source_path.is_file()}")
    print(f"BACKUP_EXISTS={backup_path.is_file()}")

    if not source_path.is_file() or not backup_path.is_file():
        print("AUDIT=FAILED")
        continue

    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    backup_hash = hashlib.sha256(backup_path.read_bytes()).hexdigest()

    print(f"BACKUP_HASH_MATCH={source_hash == backup_hash}")
    print(f"SOURCE_SHA256={source_hash}")

    tree = ast.parse(source_path.read_text(encoding="utf-8"))

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in functions:
                print(f"\n--- FUNCTION {node.name} ---")
                print(ast.unparse(node))

    print("\n--- IMPORTS ---")
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            print(ast.unparse(node))

print("\nSERVICE_STATE=NOT_CHANGED")
print("DATABASE_ACCESSED=NO")
print("NETWORK_REQUESTS=NO")
print("FILES_MODIFIED=NO")
PY
```

The SHA256 of the three files matched the copies.

### 4.2 Reading the Function Definitions

The definition of `analyze_events` spans several lines and cannot be found by a replacement that searches for a one-line string. We read the actual definition and the part that sends to the AI.

> **Run on: VM 230**

```bash
echo "===== AI ANALYSIS FUNCTION SIGNATURES ====="

cd /opt/ai-defense-manager && venv/bin/python - <<'PY'
import ast
from pathlib import Path

targets = [
    Path("app/services/ai_analysis.py"),
    Path("app/services/wazuh_relay.py"),
]

for path in targets:
    print(f"\n--- {path} ---")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in {
                "analyze_events",
                "_convert_alert",
                "_build_event_payload",
            }:
                print(
                    f"FUNCTION={node.name} "
                    f"LINE={node.lineno} "
                    f"ASYNC={isinstance(node, ast.AsyncFunctionDef)}"
                )
                print(ast.get_source_segment(source, node).splitlines()[0])

    lines = source.splitlines()
    if path.name == "ai_analysis.py":
        print("\n--- AI payload construction context ---")
        for i, line in enumerate(lines, 1):
            if (
                "'events':" in line
                or '"events":' in line
                or "sanitize_event_summary" in line
                or "messages" in line
            ):
                start = max(1, i - 3)
                end = min(len(lines), i + 3)
                print(f"[lines {start}-{end}]")
                for n in range(start, end + 1):
                    print(f"{n}: {lines[n-1]}")
    else:
        print("\n--- Wazuh conversion function context ---")
        for i, line in enumerate(lines, 1):
            if line.startswith("def _convert_alert"):
                start = i
                end = min(len(lines), i + 65)
                for n in range(start, end + 1):
                    print(f"{n}: {lines[n-1]}")
                break
PY

echo
echo "===== FILE HASHES (VERIFY NO CHANGES) ====="
sha256sum \
  app/services/wazuh_relay.py \
  app/services/event_sanitizer.py \
  app/services/ai_analysis.py

echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

```bash
echo "===== AI ANALYSIS SOURCE ====="
cd /opt/ai-defense-manager

nl -ba app/services/ai_analysis.py | sed -n '1,125p'

echo
echo "===== WAZUH RELAY IMPORTS AND CONVERSION ====="
nl -ba app/services/wazuh_relay.py | sed -n '1,110p'

echo
echo "===== AI ANALYSIS ERROR DEFINITION ====="
grep -R -n -E 'class AIAnalysisError|AIAnalysisError' app/services/ai_analysis.py app/

echo
echo "===== ORIGINAL BACKUP HASH COMPARISON ====="
sha256sum \
  app/services/wazuh_relay.py \
  /var/backups/ai-defense-manager/20261123-031115/app/services/wazuh_relay.py \
  app/services/ai_analysis.py \
  /var/backups/ai-defense-manager/20261123-031115/app/services/ai_analysis.py

echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

### 4.3 Rewriting with the AST

We drop broad regex-based replacement and, using the result of Python syntax analysis, replace only the function bodies and the part that builds the list of events. The proposed changes to both files are **written only after both pass the syntax check**. The APIs, schemas and masking (`event_sanitizer.py`) are not changed.

> **Run on: VM 230**

```bash
echo "===== AST-BASED WAZUH NORMALIZATION IMPLEMENTATION ====="

cd /opt/ai-defense-manager && venv/bin/python - <<'PY'
import ast
import hashlib
import re
from pathlib import Path

root = Path("/opt/ai-defense-manager")
backup = Path("/var/backups/ai-defense-manager/20261123-031115")

expected = {
    "app/services/wazuh_relay.py":
        "599b63978b10745223da8a9c7ce44e39003c864146facfbe518a170e764febcd",
    "app/services/event_sanitizer.py":
        "ecc8a9d46e75c833a0f478901518bb818fe05cdf1710f7d95bc33623f63fb7b4",
    "app/services/ai_analysis.py":
        "e5c83f063c0a23b8c99521571909dc90b77eea9d94108fa3ac7bd04ec79939bc",
}

for relative, expected_hash in expected.items():
    current_hash = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    backup_hash = hashlib.sha256((backup / relative).read_bytes()).hexdigest()
    if current_hash != expected_hash or backup_hash != expected_hash:
        raise RuntimeError(f"Precondition failed: {relative}")

print("BACKUP_INTEGRITY=PASS")


def line_offset(source, line_number, column=0):
    lines = source.splitlines(keepends=True)
    return sum(len(line) for line in lines[:line_number - 1]) + column


# ------------------------------------------------------------
# Prepare Wazuh relay replacement using AST function boundaries.
# ------------------------------------------------------------
relay_path = root / "app/services/wazuh_relay.py"
relay_source = relay_path.read_text(encoding="utf-8")
relay_tree = ast.parse(relay_source)

relay_functions = [
    node for node in relay_tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "_convert_alert"
]
if len(relay_functions) != 1:
    raise RuntimeError(
        f"Expected one top-level _convert_alert, found {len(relay_functions)}"
    )

new_relay_function = '''def _convert_alert(alert: dict) -> SecurityEvent:
    """Convert only the seven approved normalized Wazuh fields."""
    import re

    if not isinstance(alert, dict):
        raise ValueError("Alert must be an object")

    timestamp = alert.get("timestamp")
    level = alert.get("rule.level")
    rule_id = alert.get("rule.id")
    description = alert.get("rule.description")
    groups = alert.get("rule.groups")
    agent_id = alert.get("agent.id")

    if not isinstance(timestamp, str) or not timestamp or len(timestamp) > 64:
        raise ValueError("Invalid alert timestamp")

    if isinstance(level, bool) or not isinstance(level, int) or not 0 <= level <= 16:
        raise ValueError("Invalid Wazuh rule level")

    observed_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("Alert timestamp must include a timezone")

    if rule_id is not None:
        if not isinstance(rule_id, str) or not re.fullmatch(r"[0-9]{1,16}", rule_id):
            raise ValueError("Invalid rule ID")

    if description is not None:
        if not isinstance(description, str) or len(description) > 512:
            raise ValueError("Invalid rule description")

    if agent_id is not None:
        if not isinstance(agent_id, str) or not re.fullmatch(r"[0-9]{1,16}", agent_id):
            raise ValueError("Invalid agent ID")

    if not isinstance(groups, list) or len(groups) > 32:
        raise ValueError("Invalid Wazuh rule groups")

    normalized_groups = set()
    for group in groups:
        if not isinstance(group, str):
            raise ValueError("Invalid Wazuh rule group")
        normalized = group.strip().lower()
        if not normalized or len(normalized) > 64:
            raise ValueError("Invalid Wazuh rule group")
        if not re.fullmatch(r"[a-z0-9_-]+", normalized):
            raise ValueError("Invalid Wazuh rule group")
        normalized_groups.add(normalized)

    category_rules = (
        ({"pvedaemon", "proxmox-ve"}, "virtualization_management"),
        ({"pam", "authentication_success", "authentication_failed"}, "authentication"),
        ({"sshd"}, "remote_access"),
        ({"sudo"}, "privilege_escalation"),
        ({"useradd", "open-userdel"}, "account_management"),
        ({"postgresql"}, "database"),
    )

    category = "other"
    for group_names, mapped_category in category_rules:
        if normalized_groups.intersection(group_names):
            category = mapped_category
            break

    summary = (description or "Wazuh security alert")[:512]

    return SecurityEvent(
        source="wazuh",
        observed_at=observed_at,
        severity=_severity(level),
        rule_id=rule_id,
        rule_description=description[:512] if description else None,
        agent_id=agent_id,
        event_category=category,
        event_summary=summary,
    )
'''

relay_node = relay_functions[0]
relay_start = line_offset(relay_source, relay_node.lineno)
relay_end = line_offset(relay_source, relay_node.end_lineno + 1) if relay_node.end_lineno < len(relay_source.splitlines()) else len(relay_source)
relay_new = relay_source[:relay_start] + new_relay_function + "\n\n" + relay_source[relay_end:]
ast.parse(relay_new)
print("WAZUH_RELAY_TRANSFORM=PASS")


# ------------------------------------------------------------
# Prepare AI payload helper and replace only the event list.
# ------------------------------------------------------------
ai_path = root / "app/services/ai_analysis.py"
ai_source = ai_path.read_text(encoding="utf-8")
ai_tree = ast.parse(ai_source)

if "_ALLOWED_WAZUH_CATEGORIES" in ai_source or "_build_event_payload" in ai_source:
    raise RuntimeError("AI payload helper already exists; refusing duplicate edit")

analyze_functions = [
    node for node in ai_tree.body
    if isinstance(node, ast.AsyncFunctionDef) and node.name == "analyze_events"
]
if len(analyze_functions) != 1:
    raise RuntimeError(
        f"Expected one top-level async analyze_events, found {len(analyze_functions)}"
    )

helper = '''_ALLOWED_WAZUH_CATEGORIES = frozenset({
    "virtualization_management",
    "authentication",
    "remote_access",
    "privilege_escalation",
    "account_management",
    "database",
    "other",
})


def _build_event_payload(event) -> dict:
    """Build an explicit LLM allowlist payload from a validated event."""
    if event.source == "wazuh":
        if event.event_category not in _ALLOWED_WAZUH_CATEGORIES:
            raise AIAnalysisError("Invalid Wazuh event category")
        if (
            event.agent_name is not None
            or event.source_ip is not None
            or event.destination_ip is not None
        ):
            raise AIAnalysisError(
                "Wazuh event contains prohibited identity or IP fields"
            )

    return {
        "event_id": str(event.event_id),
        "observed_at": event.observed_at.isoformat(),
        "severity": event.severity,
        "rule_id": event.rule_id,
        "event_category": event.event_category,
        "event_summary": sanitize_event_summary(event.event_summary),
    }


'''

analyze_node = analyze_functions[0]
ai_insert_at = line_offset(ai_source, analyze_node.lineno)
ai_new = ai_source[:ai_insert_at] + helper + ai_source[ai_insert_at:]
ai_tree_new = ast.parse(ai_new)

# Find the exact list comprehension that builds the LLM event objects.
event_list_comprehensions = []
for node in ast.walk(ai_tree_new):
    if not isinstance(node, ast.ListComp) or not isinstance(node.elt, ast.Dict):
        continue
    keys = {
        key.value for key in node.elt.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    if {
        "event_id", "observed_at", "severity",
        "rule_id", "event_category", "event_summary"
    }.issubset(keys):
        event_list_comprehensions.append(node)

if len(event_list_comprehensions) != 1:
    raise RuntimeError(
        "Expected one six-field AI event payload list, found "
        f"{len(event_list_comprehensions)}"
    )

event_node = event_list_comprehensions[0]
ai_start = line_offset(ai_new, event_node.lineno, event_node.col_offset)
ai_end = line_offset(ai_new, event_node.end_lineno, event_node.end_col_offset)
ai_new = ai_new[:ai_start] + "[_build_event_payload(event) for event in request.events]" + ai_new[ai_end:]

ast.parse(ai_new)
print("AI_ANALYSIS_TRANSFORM=PASS")


# Both prepared files are now syntax-checked. Write only the two approved files.
relay_path.write_text(relay_new, encoding="utf-8")
print("WAZUH_RELAY_UPDATED=YES")

ai_path.write_text(ai_new, encoding="utf-8")
print("AI_ANALYSIS_UPDATED=YES")

print("EVENT_SANITIZER_CHANGED=NO")
print("SCHEMAS_CHANGED=NO")
print("API_ROUTES_CHANGED=NO")
PY

echo
echo "===== POST-EDIT SYNTAX CHECK ====="
venv/bin/python - <<'PY'
import ast
from pathlib import Path

for relative in (
    "app/services/wazuh_relay.py",
    "app/services/ai_analysis.py",
    "app/services/event_sanitizer.py",
):
    ast.parse(Path(relative).read_text(encoding="utf-8"))
    print(f"SYNTAX={relative}:PASS")
PY

echo
echo "===== RESULTING FILE HASHES ====="
sha256sum \
  app/services/wazuh_relay.py \
  app/services/event_sanitizer.py \
  app/services/ai_analysis.py

echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

> **Caution:** This script checks the backup directory and the pre-change SHA256 of the three files (the values at build time) before rewriting. If they do not match, it stops without writing anything. When using it in your own environment, adjust these to the values from when you saved the copies in Chapter 1.

| File | What changed |
|---|---|
| `wazuh_relay.py` | validates the seven-field input; classifies by `rule.groups`; does not use `agent.name`, `location` or `decoder.name` |
| `ai_analysis.py` | builds what is sent to the AI from six fields only (`_build_event_payload()`); checks Wazuh event classification and forbidden fields |
| `event_sanitizer.py` | unchanged |

All syntax checks passed; no service restart, communication or DB connection took place.

## Chapter 5: Testing with Synthetic Events

### 5.1 26 Unit Tests

No actual Wazuh event retrieval, LLM calls or DB writes.

> **Run on: VM 230**

```bash
echo "===== SYNTHETIC WAZUH NORMALIZATION TESTS ====="

cd /opt/ai-defense-manager && venv/bin/python - <<'PY'
import unittest
from datetime import datetime, timezone

from app.services.wazuh_relay import _convert_alert
from app.services.ai_analysis import (
    AIAnalysisError,
    _build_event_payload,
)
from app.schemas.security_event import SecurityEvent
from app.services.event_sanitizer import sanitize_event_summary


BASE_ALERT = {
    "timestamp": "2026-11-23T12:00:00+09:00",
    "rule.id": "100103",
    "rule.level": 7,
    "rule.groups": ["postgresql", "error"],
    "rule.description": "PostgreSQL ERROR event detected",
    "decoder.name": "json",
    "agent.id": "001",
}


class WazuhNormalizationTests(unittest.TestCase):

    def test_postgresql_category(self):
        event = _convert_alert(BASE_ALERT)
        self.assertEqual(event.event_category, "database")

    def test_virtualization_category(self):
        alert = {**BASE_ALERT, "rule.groups": ["syslog", "proxmox-ve"]}
        self.assertEqual(
            _convert_alert(alert).event_category,
            "virtualization_management",
        )

    def test_authentication_category(self):
        alert = {**BASE_ALERT, "rule.groups": ["authentication_failed"]}
        self.assertEqual(
            _convert_alert(alert).event_category,
            "authentication",
        )

    def test_remote_access_category(self):
        alert = {**BASE_ALERT, "rule.groups": ["sshd"]}
        self.assertEqual(
            _convert_alert(alert).event_category,
            "remote_access",
        )

    def test_privilege_escalation_category(self):
        alert = {**BASE_ALERT, "rule.groups": ["sudo"]}
        self.assertEqual(
            _convert_alert(alert).event_category,
            "privilege_escalation",
        )

    def test_account_management_category(self):
        alert = {**BASE_ALERT, "rule.groups": ["useradd"]}
        self.assertEqual(
            _convert_alert(alert).event_category,
            "account_management",
        )

    def test_category_precedence(self):
        alert = {
            **BASE_ALERT,
            "rule.groups": ["sudo", "pam", "postgresql"],
        }
        self.assertEqual(
            _convert_alert(alert).event_category,
            "authentication",
        )

    def test_generic_groups_fallback(self):
        alert = {
            **BASE_ALERT,
            "rule.groups": ["syslog", "local", "error", "access_control"],
        }
        self.assertEqual(_convert_alert(alert).event_category, "other")

    def test_missing_groups_rejected(self):
        alert = dict(BASE_ALERT)
        del alert["rule.groups"]
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_non_list_groups_rejected(self):
        alert = {**BASE_ALERT, "rule.groups": "postgresql"}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_too_many_groups_rejected(self):
        alert = {**BASE_ALERT, "rule.groups": ["syslog"] * 33}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_malformed_group_rejected(self):
        alert = {**BASE_ALERT, "rule.groups": ["postgresql;sudo"]}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_non_string_group_rejected(self):
        alert = {**BASE_ALERT, "rule.groups": ["postgresql", 7]}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_invalid_timestamp_rejected(self):
        alert = {**BASE_ALERT, "timestamp": "not-a-timestamp"}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_timezone_required(self):
        alert = {**BASE_ALERT, "timestamp": "2026-11-23T12:00:00"}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_boolean_level_rejected(self):
        alert = {**BASE_ALERT, "rule.level": True}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_out_of_range_level_rejected(self):
        alert = {**BASE_ALERT, "rule.level": 17}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_invalid_rule_id_rejected(self):
        alert = {**BASE_ALERT, "rule.id": "100;103"}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_invalid_agent_id_rejected(self):
        alert = {**BASE_ALERT, "agent.id": "../001"}
        with self.assertRaises(ValueError):
            _convert_alert(alert)

    def test_hostile_extra_fields_ignored(self):
        alert = {
            **BASE_ALERT,
            "agent.name": "hostile-agent-name",
            "location": "/private/path",
            "full_log": "synthetic raw log",
            "data": {"command": "synthetic command"},
            "predecoder": {"hostname": "synthetic-host"},
            "agent.ip": "203.0.113.77",
        }
        event = _convert_alert(alert)
        self.assertEqual(event.agent_id, "001")
        self.assertIsNone(event.agent_name)
        self.assertIsNone(event.source_ip)
        self.assertIsNone(event.destination_ip)

    def test_ai_payload_exact_allowlist(self):
        event = _convert_alert(BASE_ALERT)
        payload = _build_event_payload(event)
        self.assertEqual(
            set(payload),
            {
                "event_id",
                "observed_at",
                "severity",
                "rule_id",
                "event_category",
                "event_summary",
            },
        )

    def test_ai_rejects_unknown_wazuh_category(self):
        event = SecurityEvent(
            source="wazuh",
            observed_at=datetime.now(timezone.utc),
            severity="low",
            event_category="unexpected_category",
            event_summary="Synthetic event",
        )
        with self.assertRaises(AIAnalysisError):
            _build_event_payload(event)

    def test_ai_rejects_wazuh_agent_name(self):
        event = SecurityEvent(
            source="wazuh",
            observed_at=datetime.now(timezone.utc),
            severity="low",
            event_category="authentication",
            event_summary="Synthetic event",
            agent_name="synthetic-agent",
        )
        with self.assertRaises(AIAnalysisError):
            _build_event_payload(event)

    def test_ai_rejects_wazuh_source_ip(self):
        event = SecurityEvent(
            source="wazuh",
            observed_at=datetime.now(timezone.utc),
            severity="low",
            event_category="authentication",
            event_summary="Synthetic event",
            source_ip="203.0.113.77",
        )
        with self.assertRaises(AIAnalysisError):
            _build_event_payload(event)

    def test_non_wazuh_category_remains_unrestricted(self):
        event = SecurityEvent(
            source="prometheus",
            observed_at=datetime.now(timezone.utc),
            severity="low",
            event_category="custom_prometheus_category",
            event_summary="Synthetic monitoring event",
        )
        payload = _build_event_payload(event)
        self.assertEqual(
            payload["event_category"],
            "custom_prometheus_category",
        )

    def test_sanitizer_redacts_synthetic_secret_and_ip(self):
        original = (
            "Synthetic alert from 203.0.113.77 "
            "password=SuperSecret123"
        )
        sanitized = sanitize_event_summary(original)
        self.assertNotIn("203.0.113.77", sanitized)
        self.assertNotIn("SuperSecret123", sanitized)


suite = unittest.defaultTestLoader.loadTestsFromTestCase(
    WazuhNormalizationTests
)
result = unittest.TextTestRunner(verbosity=2).run(suite)

print()
print(f"TESTS_RUN={result.testsRun}")
print(f"TEST_FAILURES={len(result.failures)}")
print(f"TEST_ERRORS={len(result.errors)}")

if not result.wasSuccessful():
    print("SYNTHETIC_TEST_RESULT=FAIL")
else:
    print("SYNTHETIC_TEST_RESULT=PASS")
PY

echo
echo "===== POST-TEST FILE HASHES ====="
sha256sum \
  app/services/wazuh_relay.py \
  app/services/event_sanitizer.py \
  app/services/ai_analysis.py

echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

**All 26 passed** (0 failures, 0 errors).

- the six specific classifications and their priority order
- general groups become `other`
- invalid times, time zones, severities, IDs and groups are rejected
- extra fields such as `agent.name`, IPs, `full_log` and `data` are ignored
- what is sent to the AI is only the six allowed fields
- invalid classifications and forbidden fields in Wazuh events are rejected
- classification constraints for other input sources are unchanged
- synthetic IPs and passwords are masked

The SHA256 of the three files was the same before and after the tests.

### 5.2 Checking the Diff

> **Run on: VM 230**

```bash
echo "===== FINAL SOURCE DIFF REVIEW ====="
cd /opt/ai-defense-manager

echo
echo "--- WAZUH RELAY DIFF ---"
diff -u \
  /var/backups/ai-defense-manager/20261123-031115/app/services/wazuh_relay.py \
  app/services/wazuh_relay.py
echo "WAZUH_DIFF_EXIT=$?"

echo
echo "--- AI ANALYSIS DIFF ---"
diff -u \
  /var/backups/ai-defense-manager/20261123-031115/app/services/ai_analysis.py \
  app/services/ai_analysis.py
echo "AI_ANALYSIS_DIFF_EXIT=$?"

echo
echo "--- SANITIZER UNCHANGED CHECK ---"
cmp -s \
  /var/backups/ai-defense-manager/20261123-031115/app/services/event_sanitizer.py \
  app/services/event_sanitizer.py
echo "SANITIZER_UNCHANGED=$?"

echo
echo "===== IMPORT AND CALL-SITE CHECK ====="
venv/bin/python - <<'PY'
import ast
import importlib

modules = (
    "app.services.wazuh_relay",
    "app.services.ai_analysis",
)

for name in modules:
    importlib.import_module(name)
    print(f"IMPORT={name}:PASS")

from pathlib import Path

source = Path("app/services/ai_analysis.py").read_text(encoding="utf-8")
tree = ast.parse(source)

calls = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "_build_event_payload":
            calls.append(node)

print(f"AI_PAYLOAD_HELPER_CALLS={len(calls)}")
if len(calls) != 1:
    raise RuntimeError("Expected exactly one AI payload helper call")

print("IMPORT_AND_CALLSITE=PASS")
PY

echo
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

The diffs of `wazuh_relay.py` and `ai_analysis.py` were within the intended scope, and `event_sanitizer.py` matched the copy exactly. `_build_event_payload()` is called in one place. Exit code `1` from `diff` means there are differences, not an error.

### 5.3 The Shape Received from the Relay

> **Run on: VM 230**

```bash
echo "===== WAZUH RELAY INPUT SHAPE AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- fetch_wazuh_events implementation ---"
nl -ba app/services/wazuh_relay.py | sed -n '88,230p'

echo
echo "--- Wazuh API response extraction and conversion call sites ---"
grep -R -n -E 'affected_items|_convert_alert|fetch_wazuh_events|rule\.groups|rule\.level' \
  app --include='*.py' \
  --exclude-dir='__pycache__'

echo
echo "--- Relay configuration field names only ---"
grep -n -E 'wazuh_relay|wazuh_api' app/core/config.py

echo
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

`fetch_wazuh_events()` calls the Relay's `GET /v1/alerts` and passes each element of the JSON `alerts` array to `_convert_alert()`. Each element is in the following **flat, dot-separated form**.

```json
{
  "timestamp": "2026-11-23T04:00:00+09:00",
  "rule.id": "100103",
  "rule.level": 7,
  "rule.groups": ["postgresql", "error"],
  "rule.description": "PostgreSQL ERROR event detected",
  "decoder.name": "json",
  "agent.id": "001"
}
```

The new `_convert_alert()` requires `rule.groups`. In the next part, Part 49, we check whether the Relay returns this field.

## Closing Notes

In Part 48 we narrowed the Wazuh event conversion to seven fields and fixed what is sent to the AI at six fields.

| Item | Result |
|---|---|
| Copies | `/var/backups/ai-defense-manager/20261123-031115` (5 files, SHA256 match) |
| Classification | seven classifications using `rule.groups` (with priority order) |
| Changed files | `wazuh_relay.py`, `ai_analysis.py` (rewritten via AST; passed syntax check) |
| Unit tests | all 26 passed |
| Service | not restarted (still running the old code) |

In the next part, Part 49, we fix the Relay on VM 220 so that it returns `rule.groups`.

# Part 49: Narrowing the Fields Returned by the Relay to Seven
## Introduction

### About This Book

This is Part 49 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 48 we changed the AI Defense Manager on VM 230 to receive Wazuh events narrowed to seven fields and to classify them by `rule.groups`. Here we make the data returned by the relay API (Relay) on VM 220 match that.

1. Identify the Relay listening on port 8765 and its implementation file
2. Compare the data the Relay returns with the shape VM 230 expects
3. Save a copy of `relay.py`, then limit the returned fields to seven and add a check of `rule.groups`
4. Check the diff and restart only the Relay service

Apart from restarting the Relay, there is no communication with the Indexer and no actual communication from VM 230.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)

## Chapter 1: Examining the Relay

### 1.1 The Service on Port 8765

Authentication details and process arguments are not displayed.

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY ENDPOINT SERVICE AUDIT ====="

echo
echo "--- TCP listener on port 8765 ---"
ss -ltnp '( sport = :8765 )'

echo
echo "--- Candidate service units ---"
systemctl list-units --type=service --all --no-legend |
  grep -Ei 'relay|wazuh|filter' |
  sed -E 's/[[:space:]]+/ /g'

echo
echo "--- Candidate installed unit files ---"
systemctl list-unit-files --type=service --no-legend |
  grep -Ei 'relay|wazuh|filter'

echo
echo "NO_SERVICE_RESTART=YES"
echo "NO_NETWORK_REQUESTS=YES"
echo "NO_CONFIGURATION_CHANGES=YES"
```

What listens on `192.168.0.220:8765` is the running `ai-defense-relay.service`.

### 1.2 The Implementation File

> **Run on: VM 220**

```bash
echo "===== VM220: AI DEFENSE RELAY IMPLEMENTATION LOCATION ====="

echo
echo "--- Service metadata (no command arguments or environment) ---"
systemctl show ai-defense-relay.service \
  -p MainPID \
  -p User \
  -p Group \
  -p WorkingDirectory \
  -p FragmentPath

echo
echo "--- Running process executable and working directory ---"
RELAY_PID="$(systemctl show ai-defense-relay.service -p MainPID --value)"
if [ -n "$RELAY_PID" ] && [ "$RELAY_PID" != "0" ]; then
  readlink -f "/proc/$RELAY_PID/exe"
  readlink -f "/proc/$RELAY_PID/cwd"
  echo
  echo "--- Python source files under service working directory ---"
  RELAY_CWD="$(readlink -f "/proc/$RELAY_PID/cwd")"
  find "$RELAY_CWD" -maxdepth 3 -type f -name '*.py' -printf '%p\n' 2>/dev/null | sort
else
  echo "RELAY_MAINPID_UNAVAILABLE"
fi

echo
echo "NO_SERVICE_RESTART=YES"
echo "NO_NETWORK_REQUESTS=YES"
echo "NO_CONFIGURATION_CHANGES=YES"
```

The implementation was `/opt/ai-defense-relay/relay.py`.

### 1.3 How the Returned Data Is Built

Rather than the whole file, we extract only the parts related to route definitions, JSON generation and event normalization. Tokens and secret keys are not displayed.

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY RESPONSE CONTRACT REVIEW ====="

cd /opt/ai-defense-relay

echo
echo "--- Endpoint and response construction locations ---"
grep -n -E \
  '(/v1/alerts|alerts|JSONResponse|jsonify|return |rule\.groups|rule\.level|rule\.id|decoder\.name|agent\.id)' \
  relay.py

echo
echo "--- Source with line numbers ---"
nl -ba relay.py | sed -n '1,280p'

echo
echo "NO_SERVICE_RESTART=YES"
echo "NO_NETWORK_REQUESTS=YES"
echo "NO_CONFIGURATION_CHANGES=YES"
```

The new `_convert_alert()` on VM 230 requires `rule.groups`, but the Relay was in the following state.

| Field | Now | Needed |
|---|---|---|
| `timestamp`, `agent.id`, `rule.level`, `rule.description`, `rule.id`, `decoder.name` | retrieved and returned | keep |
| `rule.groups` | **not retrieved** | add |
| `agent.ip`, `agent.name`, `manager.name`, `location` | retrieved and returned | **remove** |

## Chapter 2: Fixing the Relay

### 2.1 Saving a Copy

The service is not stopped and there is no communication.

> **Run on: VM 220**

```bash
echo "===== AI DEFENSE RELAY PRE-CHANGE BACKUP ====="

SOURCE="/opt/ai-defense-relay/relay.py"
BACKUP_DIR="/var/backups/ai-defense-relay"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$BACKUP_DIR/$STAMP"

echo
echo "--- Source metadata ---"
stat -c 'PATH=%n OWNER=%U:%G MODE=%a SIZE=%s' "$SOURCE"

echo
echo "--- Create backup ---"
mkdir -p "$BACKUP"
cp -a "$SOURCE" "$BACKUP/relay.py"

echo
echo "--- SHA256 verification ---"
SOURCE_HASH="$(sha256sum "$SOURCE" | awk '{print $1}')"
BACKUP_HASH="$(sha256sum "$BACKUP/relay.py" | awk '{print $1}')"

echo "SOURCE_SHA256=$SOURCE_HASH"
echo "BACKUP_SHA256=$BACKUP_HASH"

if [ "$SOURCE_HASH" = "$BACKUP_HASH" ]; then
  echo "BACKUP_INTEGRITY=PASS"
else
  echo "BACKUP_INTEGRITY=FAIL"
fi

echo
echo "--- Backup metadata ---"
stat -c 'PATH=%n OWNER=%U:%G MODE=%a SIZE=%s' "$BACKUP/relay.py"

echo
echo "BACKUP_PATH=$BACKUP"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "SOURCE_MODIFIED=NO"
```

The copy is `/var/backups/ai-defense-relay/20261123-044701/relay.py`; its SHA256 matches the original, and the owner and permissions are `root:ai-defense-relay`, `640`.

### 2.2 Reading the Parts to Fix

> **Run on: VM 220**

```bash
echo "===== AI DEFENSE RELAY: PRE-EDIT SOURCE REVIEW ====="

cd /opt/ai-defense-relay

echo
echo "--- Field allowlist and sanitizer definitions ---"
grep -n -E 'ALLOWED_FIELDS|def sanitize_alert|def .*alert|def .*event' relay.py

echo
echo "--- Relevant source sections ---"
nl -ba relay.py | sed -n '1,250p'

echo
echo "--- Backup integrity recheck ---"
sha256sum relay.py \
  /var/backups/ai-defense-relay/20261123-044701/relay.py

echo
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
```

### 2.3 Fixing

We fix the following three things.

1. Limit `ALLOWED_FIELDS` to seven fields and stop retrieving `agent.ip`, `agent.name`, `manager.name` and `location`
2. Add checks to `sanitize_alert()`, such as that `rule.groups` is a list. Invalid events are dropped while processing of other valid events continues
3. Do not include dropped events in the returned `alerts`

`decoder.name` is checked and passed through by the Relay, but VM 230 does not send it to the AI. After checking the copy we make the fix, and before writing we run a syntax check and a test with synthetic data.

> **Run on: VM 220**

```bash
echo "===== AI DEFENSE RELAY: SAFE NORMALIZATION PATCH ====="

cd /opt/ai-defense-relay

python3 - <<'PY'
import ast
import hashlib
import os
import re
import stat
import tempfile
from pathlib import Path

source_path = Path("/opt/ai-defense-relay/relay.py")
backup_path = Path(
    "/var/backups/ai-defense-relay/20261123-044701/relay.py"
)

original = source_path.read_text(encoding="utf-8")
backup = backup_path.read_bytes()

def sha256(data):
    return hashlib.sha256(data).hexdigest()

if sha256(original.encode("utf-8")) != sha256(backup):
    raise RuntimeError("Backup/source mismatch; refusing modification")

old_fields = '''ALLOWED_FIELDS = (
    "timestamp",
    "agent.id",
    "agent.ip",
    "agent.name",
    "manager.name",
    "rule.level",
    "rule.description",
    "rule.id",
    "location",
    "decoder.name",
)'''

new_fields = '''ALLOWED_FIELDS = (
    "timestamp",
    "rule.id",
    "rule.level",
    "rule.groups",
    "rule.description",
    "decoder.name",
    "agent.id",
)'''

old_function = '''def sanitize_alert(source):
    result = {}
    for field in ALLOWED_FIELDS:
        value = source
        for part in field.split("."):
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(part)

        if value is None:
            continue

        if field == "rule.level":
            if isinstance(value, int) and not isinstance(value, bool):
                result[field] = value
        elif isinstance(value, str):
            result[field] = value[:512]

    return result'''

new_function = '''def sanitize_alert(source):
    if not isinstance(source, dict):
        return None

    result = {}

    for field in ALLOWED_FIELDS:
        value = source
        for part in field.split("."):
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(part)

        if value is None:
            continue

        if field == "timestamp":
            if not isinstance(value, str) or not value or len(value) > 64:
                return None
            result[field] = value

        elif field == "rule.level":
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 16
            ):
                return None
            result[field] = value

        elif field == "rule.groups":
            if not isinstance(value, list) or len(value) > 32:
                return None

            normalized_groups = []
            for group in value:
                if not isinstance(group, str):
                    return None
                group = group.strip().lower()
                if (
                    not group
                    or len(group) > 64
                    or not re.fullmatch(r"[a-z0-9_-]+", group)
                ):
                    return None
                normalized_groups.append(group)

            result[field] = normalized_groups

        elif field in ("rule.id", "agent.id"):
            if not isinstance(value, str):
                return None
            if not re.fullmatch(r"[0-9]{1,16}", value):
                return None
            result[field] = value

        elif field == "rule.description":
            if not isinstance(value, str):
                return None
            result[field] = value[:512]

        elif field == "decoder.name":
            if not isinstance(value, str) or len(value) > 64:
                return None
            result[field] = value

    # VM230 requires timestamp, rule.level, and rule.groups.
    if not all(
        field in result
        for field in ("timestamp", "rule.level", "rule.groups")
    ):
        return None

    return result'''

old_alerts = '''            alerts = [
                sanitize_alert(hit.get("_source", {}))
                for hit in hits
                if isinstance(hit.get("_source"), dict)
            ]'''

new_alerts = '''            alerts = [
                sanitized
                for hit in hits
                if isinstance(hit.get("_source"), dict)
                for sanitized in [sanitize_alert(hit["_source"])]
                if sanitized is not None
            ]'''

for label, old, new in (
    ("allowlist", old_fields, new_fields),
    ("sanitizer", old_function, new_function),
    ("alerts filter", old_alerts, new_alerts),
):
    count = original.count(old)
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one {label} target; found {count}"
        )

proposed = original.replace(old_fields, new_fields)
proposed = proposed.replace(old_function, new_function)
proposed = proposed.replace(old_alerts, new_alerts)

# Syntax validation before writing.
compile(proposed, str(source_path), "exec")
tree = ast.parse(proposed)

# Isolated synthetic tests of the actual proposed sanitizer.
selected = []
for node in tree.body:
    if isinstance(node, (ast.Assign, ast.FunctionDef)):
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name)
                and target.id == "ALLOWED_FIELDS"
                for target in node.targets
            ):
                selected.append(node)
        elif node.name == "sanitize_alert":
            selected.append(node)

namespace = {"re": re}
exec(
    compile(
        ast.Module(body=selected, type_ignores=[]),
        "<isolated-sanitizer-test>",
        "exec",
    ),
    namespace,
)

allowed = namespace["ALLOWED_FIELDS"]
sanitize = namespace["sanitize_alert"]

expected = (
    "timestamp",
    "rule.id",
    "rule.level",
    "rule.groups",
    "rule.description",
    "decoder.name",
    "agent.id",
)
assert allowed == expected, allowed

sample = {
    "timestamp": "2026-11-23T04:00:00+09:00",
    "agent": {
        "id": "001",
        "ip": "203.0.113.10",
        "name": "must-not-leak",
    },
    "manager": {"name": "must-not-leak"},
    "location": "must-not-leak",
    "rule": {
        "id": "100103",
        "level": 7,
        "groups": [" PostgreSQL ", "ERROR"],
        "description": "PostgreSQL ERROR event detected",
    },
    "decoder": {"name": "json"},
    "full_log": "must-not-leak",
    "data": {"command": "must-not-leak"},
}

result = sanitize(sample)
assert result is not None
assert set(result) == set(expected), set(result)
assert result["rule.groups"] == ["postgresql", "error"]
assert result["agent.id"] == "001"
assert result["decoder.name"] == "json"

assert sanitize({**sample, "rule": {
    **sample["rule"], "groups": ["valid", "bad group"]
}}) is None

assert sanitize({**sample, "rule": {
    **sample["rule"], "groups": ["x" * 65]
}}) is None

assert sanitize({**sample, "rule": {
    **sample["rule"], "groups": ["valid"] * 33
}}) is None

assert sanitize({**sample, "rule": {
    **sample["rule"], "level": True
}}) is None

assert sanitize({**sample, "rule": {
    **sample["rule"], "groups": "postgresql"
}}) is None

assert sanitize({"rule": sample["rule"]}) is None

print("PREWRITE_SYNTAX=PASS")
print("PREWRITE_ALLOWLIST=PASS")
print("SYNTHETIC_VALID_EVENT=PASS")
print("SYNTHETIC_FORBIDDEN_FIELDS=PASS")
print("SYNTHETIC_INVALID_GROUPS_REJECTED=PASS")
print("SYNTHETIC_INVALID_LEVEL_REJECTED=PASS")
print("SYNTHETIC_REQUIRED_FIELDS=PASS")

# Preserve existing owner and mode; replace atomically.
metadata = source_path.stat()
fd, temporary_name = tempfile.mkstemp(
    prefix=".relay.py.",
    suffix=".tmp",
    dir=str(source_path.parent),
)

try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(proposed)
        handle.flush()
        os.fsync(handle.fileno())

    os.chown(temporary_name, metadata.st_uid, metadata.st_gid)
    os.chmod(temporary_name, stat.S_IMODE(metadata.st_mode))
    os.replace(temporary_name, source_path)

    directory_fd = os.open(source_path.parent, os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)

except Exception:
    try:
        os.unlink(temporary_name)
    except FileNotFoundError:
        pass
    raise

final = source_path.read_bytes()
compile(final, str(source_path), "exec")

if final != proposed.encode("utf-8"):
    raise RuntimeError("Post-write content mismatch")

if sha256(backup) != sha256(backup_path.read_bytes()):
    raise RuntimeError("Backup integrity changed")

print("SOURCE_WRITE=PASS")
print("POSTWRITE_SYNTAX=PASS")
print("BACKUP_INTEGRITY=PASS")
print("SOURCE_SHA256=" + sha256(final))
print("BACKUP_SHA256=" + sha256(backup))
print("SOURCE_OWNER_MODE=" + oct(stat.S_IMODE(source_path.stat().st_mode)))
print("PATCH_RESULT=SUCCESS")
PY

echo
echo "===== SERVICE AND NETWORK SAFETY ====="
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

| Checked | Result |
|---|---|
| Syntax and allowlist before writing | passed |
| Synthetic data (valid and invalid events) | passed |
| `ALLOWED_FIELDS` | 7 fields |
| `rule.groups` | checks list type, number of elements, number of characters and character types |
| Fields not returned | `agent.ip`, `agent.name`, `manager.name`, `location`, `full_log`, `data` |
| Owner and permissions | still `root:ai-defense-relay`, `640` |

### 2.4 Checking the Diff

> **Run on: VM 220**

```bash
echo "===== AI DEFENSE RELAY: POST-PATCH REVIEW ====="

cd /opt/ai-defense-relay

echo
echo "--- Source diff ---"
diff -u \
  /var/backups/ai-defense-relay/20261123-044701/relay.py \
  relay.py
DIFF_STATUS=$?
echo "DIFF_EXIT=$DIFF_STATUS"

echo
echo "--- Allowlist ---"
sed -n '19,115p' relay.py

echo
echo "--- Response filtering ---"
sed -n '205,240p' relay.py

echo
echo "--- Syntax check ---"
python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/opt/ai-defense-relay/relay.py")
source = path.read_text(encoding="utf-8")
ast.parse(source, filename=str(path))
compile(source, str(path), "exec")
print("SYNTAX=PASS")
PY

echo
echo "--- File metadata and hashes ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s' relay.py
sha256sum relay.py \
  /var/backups/ai-defense-relay/20261123-044701/relay.py

echo
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

| Checked | Result |
|---|---|
| The seven allowed fields | passed |
| Forbidden fields not retrieved | passed |
| Checking and normalizing `rule.groups` | passed |
| Invalid events dropped and not returned | passed |
| Python syntax check | passed |
| Owner, permissions, copy | passed |

`DIFF_EXIT=1` means there are the intended differences from the copy.

## Chapter 3: Restarting the Relay

### 3.1 Restart

We restart only the Relay service on VM 220.

> **Run on: VM 220**

```bash
echo "===== AI DEFENSE RELAY: APPROVED SERVICE RESTART ====="

echo
echo "--- Restart service ---"
systemctl restart ai-defense-relay.service
RESTART_STATUS=$?
echo "RESTART_COMMAND_EXIT=$RESTART_STATUS"

echo
echo "--- Active state ---"
systemctl is-active ai-defense-relay.service
ACTIVE_STATUS=$?
echo "ACTIVE_CHECK_EXIT=$ACTIVE_STATUS"

echo
echo "--- Service status ---"
systemctl status ai-defense-relay.service --no-pager -l

echo
echo "--- Main process metadata ---"
systemctl show ai-defense-relay.service \
  -p MainPID \
  -p ActiveState \
  -p SubState \
  -p User \
  -p WorkingDirectory

echo
echo "INDEXER_TEST=NOT_PERFORMED"
echo "VM230_RELAY_REQUEST=NOT_PERFORMED"
echo "DATABASE_ACCESSED=NO"
```

| Item | Result |
|---|---|
| Restart | succeeded (exit code `0`) |
| State | `active`, `running` |
| New MainPID | `17052` |
| Running as | `ai-defense-relay` |
| Working directory | `/opt/ai-defense-relay` |

### 3.2 Checking the Listening Port

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY POST-RESTART LISTENER CHECK ====="

echo
echo "--- TCP listener ---"
ss -ltnp '( sport = :8765 )'

echo
echo "--- Process metadata ---"
systemctl show ai-defense-relay.service \
  -p MainPID \
  -p ActiveState \
  -p SubState

echo
echo "--- Source hash ---"
sha256sum /opt/ai-defense-relay/relay.py

echo
echo "INDEXER_TEST=NOT_PERFORMED"
echo "VM230_REQUEST=NOT_PERFORMED"
```

It listens on `192.168.0.220:8765`, systemd shows `active (running)`, and the PIDs of the running process and the service are the same. The Relay on VM 220 is running with the new seven-field processing.

## Closing Notes

In Part 49 we made the data returned by the Relay match the shape VM 230 receives.

| Item | Result |
|---|---|
| Implementation | `/opt/ai-defense-relay/relay.py` |
| Copy | `/var/backups/ai-defense-relay/20261123-044701/relay.py` |
| Returned fields | 7 (`timestamp`, `rule.id`, `rule.level`, `rule.groups`, `rule.description`, `decoder.name`, `agent.id`) |
| Invalid events | dropped and not returned |
| Relay | restarted and running the new code |
| VM 230 | code fixed, but the service has not been restarted yet |

Before restarting the service on VM 230, we change VM 230's address from DHCP to a static address. We do this in the next part, Part 50.

# Part 50: Deploying the New Code and a Static Address for VM 230
## Introduction

### About This Book

This is Part 50 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". By Part 49 we had fixed the code of the Relay on VM 220 and the AI Defense Manager on VM 230, and restarted only the Relay. Here we do the following.

1. Restart `ai-defense-manager.service` on VM 230 so that it loads the new code
2. Change VM 230's address from the DHCP-assigned `192.168.0.33` to a static `192.168.0.221` (DHCP is not used)
3. Fix the old address (the client allowed to connect) left in the Relay on VM 220 to the new address

Numbering it next to VM 220 (`192.168.0.220`) makes it easier to manage.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **VM 230 (console)**: logged in as root from the Console of VM 230 in the Proxmox web interface
  - **VM 220**: security-core (root)

## Chapter 1: Restarting the AI Defense Manager

### 1.1 Restart

We restart only the AI Defense Manager service. At this point the address is still `192.168.0.33`.

> **Run on: VM 230**

```bash
echo "===== VM230: APPROVED AI DEFENSE MANAGER RESTART ====="

echo
echo "--- Restart service ---"
systemctl restart ai-defense-manager.service
echo "RESTART_EXIT=$?"

echo
echo "--- Active state ---"
systemctl is-active ai-defense-manager.service

echo
echo "--- Service status ---"
systemctl status ai-defense-manager.service --no-pager -l

echo
echo "--- Process metadata ---"
systemctl show ai-defense-manager.service \
  -p MainPID \
  -p ActiveState \
  -p SubState \
  -p User \
  -p WorkingDirectory

echo
echo "--- Local health endpoint ---"
curl --max-time 5 -sS -i http://127.0.0.1:8000/health

echo
echo "NETWORK_CONFIGURATION_CHANGED=NO"
echo "WAZUH_RELAY_REQUEST=NO"
echo "OLLAMA_REQUEST=NO"
echo "DATABASE_ACCESSED=NO"
```

The restart succeeded and systemd showed `active (running)`, but `/health` could not be reached. It was checked about 15ms after the restart, so presumably Uvicorn had not yet started listening on port 8000.

### 1.2 Checking the Startup

> **Run on: VM 230**

```bash
echo "===== VM230: POST-RESTART API HEALTH VERIFICATION ====="

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "--- Listener port 8000 ---"
ss -lntp '( sport = :8000 )'

echo
echo "--- Health endpoint retry ---"
for i in 1 2 3 4 5; do
  echo "ATTEMPT=$i"
  curl --max-time 3 -sS -i http://127.0.0.1:8000/health
  CURL_STATUS=$?
  echo "CURL_EXIT=$CURL_STATUS"
  if [ "$CURL_STATUS" -eq 0 ]; then
    break
  fi
  sleep 2
done

echo
echo "--- Recent service logs ---"
journalctl -u ai-defense-manager.service -n 40 --no-pager

echo
echo "--- Process metadata ---"
systemctl show ai-defense-manager.service \
  -p MainPID -p ActiveState -p SubState

echo
echo "WAZUH_RELAY_REQUEST=NO"
echo "OLLAMA_REQUEST=NO"
echo "DATABASE_ACCESSED=NO"
```

| Item | Result |
|---|---|
| systemd | `active (running)` |
| MainPID | `1640` |
| Uvicorn startup, application startup | succeeded |
| Listening | `127.0.0.1:8000` |
| `/health` | `HTTP 200` |
| Version | `0.1.0` |

Now the code fixed in Parts 48 and 49 is running on both VM 220 and VM 230.

## Chapter 2: Fixing VM 230's Address

### 2.1 The Current Settings

> **Run on: VM 230**

```bash
echo "===== VM230: NETWORK CONFIGURATION AUDIT ====="

echo
echo "--- Interface addresses ---"
ip -br address

echo
echo "--- Interface MAC ---"
ip link show enp6s18

echo
echo "--- Routing ---"
ip route

echo
echo "--- DHCP client configuration ---"
grep -RniE 'dhcp|192\.168\.0\.33|192\.168\.0\.221' \
  /etc/network/interfaces \
  /etc/network/interfaces.d \
  /etc/systemd/network \
  /etc/NetworkManager/system-connections \
  2>/dev/null

echo
echo "--- Current listener addresses ---"
ss -lntp

echo
echo "NETWORK_CONFIGURATION_CHANGED=NO"
```

VM 230 received `192.168.0.33/24` by DHCP (NIC `enp6s18`). The API listens only on `127.0.0.1:8000`, so changing the address does not expose the API. However, SSH may be cut temporarily.

### 2.2 DNS and the Management Method

> **Run on: VM 230**

```bash
echo "===== VM230: STATIC IPv4 PREPARATION ====="

echo
echo "--- DNS ---"
resolvectl status enp6s18

echo
echo "--- Netplan files ---"
ls -la /etc/netplan 2>/dev/null
grep -RniE 'dhcp4|dhcp6|addresses|routes|gateway|nameservers|renderer' \
  /etc/netplan 2>/dev/null

echo
echo "--- Network management ---"
systemctl is-active systemd-networkd
systemctl is-active NetworkManager

echo
echo "--- Cloud-init ---"
cloud-init status --long 2>/dev/null

echo
echo "--- Current IPv4 and IPv6 ---"
ip -4 address show dev enp6s18
ip -6 address show dev enp6s18

echo
echo "CONFIGURATION_CHANGED=NO"
```

VM 230 is managed by **Netplan and systemd-networkd**, and `/etc/netplan/50-cloud-init.yaml` had `dhcp4: true`. DNS is `192.168.0.1`, `2404:1a8:7f01:a::3` and `2404:1a8:7f01:b::3`. IPv6 is left on automatic configuration via router advertisements (RA); only IPv4 is made static.

### 2.3 The Whole Configuration, and Address Conflicts

> **Run on: VM 230**

```bash
echo "===== VM230: STATIC IP PRECHANGE AUDIT ====="

echo
echo "--- Complete Netplan configuration ---"
cat /etc/netplan/50-cloud-init.yaml

echo
echo "--- Netplan configuration validation ---"
netplan get

echo
echo "--- IPv4 and IPv6 routes ---"
ip -4 route
ip -6 route

echo
echo "--- Networkd link status ---"
networkctl status enp6s18 --no-pager

echo
echo "--- Current DNS configuration ---"
resolvectl dns enp6s18
resolvectl domain enp6s18

echo
echo "--- Check whether arping is available ---"
command -v arping

echo
echo "--- Check target address 192.168.0.221 ---"
if command -v arping >/dev/null 2>&1; then
  arping -D -I enp6s18 -c 3 -w 5 192.168.0.221
  echo "ARPING_EXIT=$?"
else
  echo "ARPING_NOT_INSTALLED"
fi

echo
echo "NETWORK_CONFIGURATION_CHANGED=NO"
```

`arping` was not installed, so we check with ping and the neighbor cache.

> **Run on: VM 230**

```bash
echo "===== VM230: TARGET IPv4 CONFLICT PRECHECK ====="

echo
echo "--- ICMP reachability ---"
ping -c 3 -W 2 192.168.0.221
echo "PING_EXIT=$?"

echo
echo "--- Neighbor cache ---"
ip neigh show 192.168.0.221

echo
echo "--- Current interface and gateway ---"
ip -br address show enp6s18
ip route show default

echo
echo "NETWORK_CONFIGURATION_CHANGED=NO"
```

There was no ping reply from `192.168.0.221`, and the neighbor cache showed `FAILED`. It does not appear to be in use (devices that do not answer ICMP or that are powered off are possible, so we cannot say for certain there is no conflict).

| Item | After the change |
|---|---|
| IPv4 | `192.168.0.221/24` (static) |
| Gateway | `192.168.0.1` |
| IPv4 DHCP | disabled |
| IPv6 | still automatic via RA |
| DNS | the current three addresses |
| DNS search domain | still `iptvf.jp` |

### 2.4 Creating the Configuration File

We save a copy of the configuration file before rewriting it. At this stage **the configuration is not applied and the interface is not restarted**.

> **Run on: VM 230**

```bash
echo "===== VM230: STATIC IPv4 CONFIGURATION PREPARATION ====="

BACKUP_DIR="/var/backups/ai-defense-manager/netplan-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo
echo "--- Backup original configuration ---"
cp -a /etc/netplan/50-cloud-init.yaml "$BACKUP_DIR/50-cloud-init.yaml"
sha256sum /etc/netplan/50-cloud-init.yaml "$BACKUP_DIR/50-cloud-init.yaml"

echo
echo "--- Write static IPv4 configuration ---"
cat > /tmp/50-cloud-init.yaml.new <<'YAML'
network:
  version: 2
  ethernets:
    enp6s18:
      dhcp4: false
      dhcp6: false
      accept-ra: true
      addresses:
        - 192.168.0.221/24
      routes:
        - to: default
          via: 192.168.0.1
      nameservers:
        addresses:
          - 192.168.0.1
          - 2404:1a8:7f01:a::3
          - 2404:1a8:7f01:b::3
        search:
          - iptvf.jp
YAML

install -o root -g root -m 600 \
  /tmp/50-cloud-init.yaml.new \
  /etc/netplan/50-cloud-init.yaml

echo
echo "--- New configuration ---"
cat /etc/netplan/50-cloud-init.yaml

echo
echo "--- Netplan parse validation ---"
netplan get

echo
echo "--- Netplan generation validation ---"
netplan generate
echo "NETPLAN_GENERATE_EXIT=$?"

echo
echo "--- Backup location ---"
echo "$BACKUP_DIR"

echo
echo "NETWORK_APPLIED=NO"
echo "INTERFACE_RESTARTED=NO"
```

The copy of the original configuration (SHA256 match), the Netplan syntax check and `netplan generate` (exit code `0`) all succeeded.

### 2.5 Applying with `netplan try`

SSH is cut when the address changes, so run this from **VM 230's Console in the Proxmox web interface**. `netplan try` asks for confirmation after applying and reverts if you do not confirm.

> **Run on: VM 230 (console)**

```bash
echo "===== VM230: STATIC IPv4 APPLY WITH ROLLBACK ====="

echo
echo "--- Confirm current and target configuration ---"
ip -br address show enp6s18
cat /etc/netplan/50-cloud-init.yaml

echo
echo "--- Apply using netplan try ---"
netplan try --timeout 120

echo
echo "--- Apply command exit status ---"
echo "NETPLAN_TRY_EXIT=$?"

echo
echo "--- Current IPv4 address ---"
ip -4 address show dev enp6s18

echo
echo "--- Default route ---"
ip -4 route show default

echo
echo "CHECK_API_AFTER_NETWORK_CHANGE=REQUIRED"
```

> **Important:** When `netplan try` asks for confirmation, confirm only after checking that the address has become `.221` and communication works. If it is still `.33`, do not confirm.

`netplan try` finished normally and the configuration was confirmed. It did not revert automatically.

### 2.6 Checking After Applying

> **Run on: VM 230 (console)**

```bash
echo "===== VM230: STATIC IPv4 POST-APPLY VERIFICATION ====="

echo
echo "--- IPv4 address ---"
ip -4 address show dev enp6s18

echo
echo "--- DHCP status in Netplan ---"
netplan get

echo
echo "--- Default route ---"
ip -4 route show default

echo
echo "--- IPv6 status ---"
ip -6 address show dev enp6s18
ip -6 route show default

echo
echo "--- DNS ---"
resolvectl status enp6s18

echo
echo "--- Gateway connectivity ---"
ping -c 3 -W 2 192.168.0.1

echo
echo "--- API listener ---"
ss -lntp '( sport = :8000 )'

echo
echo "--- API health ---"
curl --max-time 5 -sS -i http://127.0.0.1:8000/health

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "NETWORK_CONFIGURATION_CHANGED=YES"
echo "WAZUH_RELAY_REQUEST=NO"
echo "OLLAMA_REQUEST=NO"
echo "DATABASE_ACCESSED=NO"
```

| Checked | Result |
|---|---|
| IPv4 | `192.168.0.221/24` (lifetime `forever`) |
| IPv4 DHCP | disabled |
| Default route | `192.168.0.1`; ping to the gateway succeeded 3/3 |
| IPv6 RA | normal |
| DNS | normal with the three addresses |
| API listening | `127.0.0.1:8000` |
| `/health` | `HTTP 200` |
| systemd | `active` |

## Chapter 3: Fixing the Address the Relay Allows

### 3.1 Where the Old Address Remains

The Relay on VM 220 is the side VM 230 connects to, so we check whether VM 230's old address remains in its settings.

> **Run on: VM 220**

```bash
echo "===== VM220: VM230 OLD IP REFERENCE AUDIT ====="

echo
echo "--- Relay application references ---"
grep -RInE \
  '192\.168\.0\.(33|221)' \
  /opt/ai-defense-relay \
  --exclude='*.pyc' \
  2>/dev/null

echo
echo "--- Systemd unit references ---"
grep -nE '192\.168\.0\.(33|221)' \
  /etc/systemd/system/ai-defense-relay.service \
  /etc/systemd/system/ai-defense-relay.service.d/* \
  2>/dev/null

echo
echo "--- Relay service metadata (environment values excluded) ---"
systemctl show ai-defense-relay.service \
  -p MainPID \
  -p ActiveState \
  -p SubState \
  -p User \
  -p WorkingDirectory \
  -p FragmentPath

echo
echo "--- Current Relay listener ---"
ss -lntp '( sport = :8765 )'

echo
echo "CONFIGURATION_CHANGED=NO"
echo "NETWORK_REQUESTS=NO"
echo "CREDENTIALS_DISPLAYED=NO"
```

Line 16 of `/opt/ai-defense-relay/relay.py` still had `ALLOWED_CLIENT = "192.168.0.33"`.

### 3.2 How It Is Used

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY CLIENT IP AUTHORIZATION AUDIT ====="

cd /opt/ai-defense-relay || true

echo
echo "--- ALLOWED_CLIENT definition and references ---"
grep -n -C 8 'ALLOWED_CLIENT' relay.py

echo
echo "--- Request client address handling ---"
grep -n -C 5 -E 'client\.host|remote_addr|X-Forwarded-For|request\.client' relay.py

echo
echo "--- Source metadata and current hash ---"
stat -c 'owner=%U:%G mode=%a size=%s' relay.py
sha256sum relay.py

echo
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
```

The Relay checks clients in two stages.

1. The source IP address matches `ALLOWED_CLIENT`
2. The `Authorization: Bearer ...` token matches

As it is, connections from VM 230's new address would be refused. Only one line of `relay.py` is changed; the API token, Wazuh settings, allowed fields, and listening address and port are not changed.

### 3.3 Fixing One Line and Restarting

We make a copy, check that only one line changed, the Python syntax and the file permissions, and then restart the Relay.

> **Run on: VM 220**

```bash
echo "===== VM220: UPDATE ALLOWED CLIENT IP ====="

cd /opt/ai-defense-relay || true

echo
echo "--- Create verified backup and update exactly one line ---"

python3 - <<'PY'
from pathlib import Path
from datetime import datetime
import shutil
import hashlib
import os
import sys

src = Path("/opt/ai-defense-relay/relay.py")
backup_dir = Path("/var/backups/ai-defense-relay/20261123-client-ip-1403")
backup = backup_dir / "relay.py"

if not src.is_file():
    print("ERROR: source file missing")
    sys.exit(1)

original = src.read_text(encoding="utf-8")
old = 'ALLOWED_CLIENT = "192.168.0.33"'
new = 'ALLOWED_CLIENT = "192.168.0.221"'

if original.count(old) != 1:
    print(f"ERROR: expected exactly one old setting, found {original.count(old)}")
    sys.exit(1)

if 'ALLOWED_CLIENT = "192.168.0.221"' in original:
    print("ERROR: target setting already exists")
    sys.exit(1)

backup_dir.mkdir(parents=True, exist_ok=False)
shutil.copy2(src, backup)

original_hash = hashlib.sha256(src.read_bytes()).hexdigest()
backup_hash = hashlib.sha256(backup.read_bytes()).hexdigest()

if original_hash != backup_hash:
    print("ERROR: backup hash mismatch; source not changed")
    sys.exit(1)

updated = original.replace(old, new, 1)
compile(updated, str(src), "exec")

tmp = src.with_suffix(".py.tmp")
tmp.write_text(updated, encoding="utf-8")
os.chown(tmp, src.stat().st_uid, src.stat().st_gid)
os.chmod(tmp, src.stat().st_mode)
os.replace(tmp, src)

final = src.read_text(encoding="utf-8")
if final.count(new) != 1 or old in final:
    print("ERROR: post-write verification failed")
    sys.exit(1)

print("BACKUP_PATH=" + str(backup))
print("BACKUP_SHA256=" + backup_hash)
print("ORIGINAL_SHA256=" + original_hash)
print("UPDATED_SHA256=" + hashlib.sha256(src.read_bytes()).hexdigest())
print("CLIENT_IP_CHANGE=192.168.0.33 -> 192.168.0.221")
print("PYTHON_SYNTAX=PASS")
print("FILE_METADATA=" + str(src.stat().st_mode & 0o777))
print("BACKUP_INTEGRITY=PASS")
print("SOURCE_UPDATE=PASS")
PY

PATCH_STATUS=$?
echo "PATCH_EXIT=$PATCH_STATUS"

if [ "$PATCH_STATUS" -eq 0 ]; then
    echo
    echo "--- Restart approved Relay service ---"
    systemctl restart ai-defense-relay.service
    echo "RESTART_EXIT=$?"

    echo
    echo "--- Service state ---"
    systemctl is-active ai-defense-relay.service
    systemctl status ai-defense-relay.service --no-pager -l | head -25

    echo
    echo "--- Listener ---"
    ss -lntp '( sport = :8765 )'

    echo
    echo "--- Final source verification ---"
    grep -n '^ALLOWED_CLIENT' /opt/ai-defense-relay/relay.py
    sha256sum /opt/ai-defense-relay/relay.py
else
    echo "SERVICE_RESTARTED=NO"
fi

echo
echo "WAZUH_INDEXER_REQUEST=NO"
echo "VM230_API_REQUEST=NO"
echo "DATABASE_ACCESSED=NO"
```

It changed to `ALLOWED_CLIENT = "192.168.0.221"`, the copy's SHA256 matched, the syntax check passed, permissions stayed `640`, the restart gave exit code `0`, and the state was `active`.

### 3.4 Checking the Listening Port

Right after the restart, `ss` did not yet show port 8765 listening, so we wait a little and check.

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY POST-RESTART LISTENER VERIFICATION ====="

echo
echo "--- Wait briefly for service initialization ---"
sleep 3

echo
echo "--- Service state and process ---"
systemctl is-active ai-defense-relay.service
systemctl show ai-defense-relay.service \
  -p MainPID -p ActiveState -p SubState

echo
echo "--- TCP listener ---"
ss -lntp '( sport = :8765 )'

echo
echo "--- Recent service journal ---"
journalctl -u ai-defense-relay.service -n 20 --no-pager

echo
echo "--- Authorized client setting ---"
grep -n '^ALLOWED_CLIENT' /opt/ai-defense-relay/relay.py

echo
echo "SOURCE_MODIFIED=NO"
echo "WAZUH_INDEXER_REQUEST=NO"
echo "VM230_API_REQUEST=NO"
echo "DATABASE_ACCESSED=NO"
```

| Item | Result |
|---|---|
| Relay | `active (running)`, MainPID `17962` |
| Listening | `192.168.0.220:8765` |
| Allowed client | `192.168.0.221` |

## Closing Notes

In Part 50 we deployed the new code to VM 230 and gave VM 230 a static address.

| Item | Result |
|---|---|
| VM 230 service | restarted and running the new code (`/health` is `HTTP 200`) |
| VM 230 address | `192.168.0.221/24` (static, no DHCP). Copy of the settings in `/var/backups/ai-defense-manager/netplan-…` |
| Relay's allowed client | `192.168.0.33` → `192.168.0.221` |
| Layout | VM 220 `192.168.0.220` (Wazuh, Relay :8765), VM 230 `192.168.0.221` (AI Defense Manager :8000, localhost only) |

In the next part, Part 51, we check TLS and authentication from VM 230 to VM 220 and try fetching real alerts.

# Part 51: Verifying TLS and Authentication from VM 230 to the Relay
## Introduction

### About This Book

This is Part 51 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 50 we gave VM 230 the static address `192.168.0.221` and fixed the allowed client of the Relay on VM 220. Here, before actually fetching alerts, we check the conditions for connecting from VM 230 to the Relay on VM 220.

1. Check VM 230's connection settings and the HTTPS implementation of the Relay on VM 220
2. Check that the Relay's server certificate matches `192.168.0.220` and is signed by a CA that VM 230 trusts
3. Using `/health`, which does not query the Indexer, test TLS, the source IP restriction and Bearer authentication once

Secret keys, Bearer tokens and Indexer credentials are not displayed.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **VM 220**: security-core (root)

## Chapter 1: Connection Settings and the HTTPS Implementation

### 1.1 VM 230's Connection Target

> **Run on: VM 230**

```bash
echo "===== VM230: WAZUH RELAY CONNECTION CONFIGURATION AUDIT ====="

cd /opt/ai-defense-manager || true

echo
echo "--- Relay configuration references (secrets excluded) ---"
grep -RInE \
  '192\.168\.0\.220|8765|WAZUH.*(URL|HOST|PORT)|RELAY.*(URL|HOST|PORT)' \
  app \
  --include='*.py' \
  --exclude='*.pyc' \
  2>/dev/null

echo
echo "--- Relay service implementation: connection and auth structure ---"
grep -n -C 4 -E \
  'urlopen|Request\(|Authorization|Bearer|timeout|https?://' \
  app/services/wazuh_relay.py

echo
echo "--- VM230 process and service state ---"
systemctl is-active ai-defense-manager.service
systemctl show ai-defense-manager.service \
  -p MainPID -p ActiveState -p SubState -p User -p WorkingDirectory

echo
echo "--- Network route to VM220 ---"
ip route get 192.168.0.220

echo
echo "CONFIGURATION_CHANGED=NO"
echo "HTTP_REQUEST=NO"
echo "WAZUH_INDEXER_REQUEST=NO"
echo "OLLAMA_REQUEST=NO"
echo "DATABASE_ACCESSED=NO"
echo "SECRETS_DISPLAYED=NO"
```

| Item | Result |
|---|---|
| Relay URL | `https://192.168.0.220:8765/` |
| Path | VM 230 `.221` → VM 220 `.220` |
| Authentication | Bearer token |
| TLS certificate verification | enabled (`verify=str(ca_file)`) |

The old address `.33` did not remain on the VM 230 side.

### 1.2 The Relay's HTTPS Implementation

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY TLS IMPLEMENTATION AUDIT ====="

cd /opt/ai-defense-relay || true

echo
echo "--- TLS and server implementation references ---"
grep -n -C 3 -E \
  'ssl|HTTPServer|ThreadingHTTPServer|wrap_socket|certfile|keyfile|load_cert|serve_forever|API_TOKEN' \
  relay.py | sed -E \
  's/(API_TOKEN[[:space:]]*=).*/\1 <REDACTED>/'

echo
echo "--- Relay server startup section ---"
tail -70 relay.py | sed -E \
  's/(API_TOKEN[[:space:]]*=).*/\1 <REDACTED>/'

echo
echo "--- Service unit TLS-related metadata ---"
systemctl show ai-defense-relay.service \
  -p FragmentPath -p ExecStart -p EnvironmentFiles

echo
echo "--- Listener protocol metadata ---"
ss -lntp '( sport = :8765 )'

echo
echo "SOURCE_MODIFIED=NO"
echo "HTTP_REQUEST=NO"
echo "TLS_HANDSHAKE=NO"
echo "WAZUH_INDEXER_REQUEST=NO"
echo "SECRETS_DISPLAYED=NO"
```

The Relay is an HTTPS server that requires TLS 1.2 or later, and it loaded its server certificate and secret key from systemd credentials.

## Chapter 2: Checking the Certificate and CA

### 2.1 The Server Certificate

We look only at public information.

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY SERVER CERTIFICATE AUDIT ====="

PID=$(systemctl show ai-defense-relay.service -p MainPID --value)
CRED_DIR=$(tr '\0' '\n' < "/proc/${PID}/environ" | sed -n 's/^CREDENTIALS_DIRECTORY=//p' | head -1)

echo
echo "--- Credential directory availability ---"
if [ -n "$CRED_DIR" ] && [ -r "$CRED_DIR/server-cert" ]; then
    echo "SERVER_CERTIFICATE=AVAILABLE"
else
    echo "SERVER_CERTIFICATE=NOT_AVAILABLE"
fi

echo
echo "--- Server certificate public metadata ---"
if [ -n "$CRED_DIR" ] && [ -r "$CRED_DIR/server-cert" ]; then
    openssl x509 -in "$CRED_DIR/server-cert" -noout \
      -subject -issuer -serial -dates -ext subjectAltName
else
    echo "CERTIFICATE_METADATA=NOT_CHECKED"
fi

echo
echo "--- Certificate file metadata ---"
if [ -n "$CRED_DIR" ] && [ -r "$CRED_DIR/server-cert" ]; then
    stat -c 'owner=%U:%G mode=%a size=%s' "$CRED_DIR/server-cert"
fi

echo
echo "PRIVATE_KEY_CONTENT_DISPLAYED=NO"
echo "API_TOKEN_DISPLAYED=NO"
echo "INDEXER_CREDENTIALS_DISPLAYED=NO"
echo "NETWORK_REQUEST=NO"
echo "CONFIGURATION_CHANGED=NO"
```

| Item | Result |
|---|---|
| SAN | `IP Address:192.168.0.220` |
| Issuer | `AI-Defense-Relay-Internal-CA` |
| Validity | November 20, 2026 – February 22, 2029 |

### 2.2 The CA That VM 230 Trusts

> **Run on: VM 230**

```bash
echo "===== VM230: RELAY CA TRUST CONFIGURATION AUDIT ====="

cd /opt/ai-defense-manager || true

echo
echo "--- CA file resolution in relay client ---"
grep -n -B 8 -A 12 'ca_file' app/services/wazuh_relay.py

echo
echo "--- Relay TLS settings definitions ---"
grep -n -i -B 3 -A 5 'wazuh_relay' app/core/config.py

echo
echo "--- CA-related configuration names (values excluded) ---"
grep -RInE \
  'ca_file|ca_bundle|ca_cert|certificate|cert_path|ssl_context|verify=' \
  app \
  --include='*.py' \
  --exclude='*.pyc' \
  2>/dev/null | sed -E 's/(=|:)[[:space:]]*["'\''][^"'\'']*["'\'']/=\<VALUE REDACTED\>/g'

echo
echo "--- Relevant CA certificate file metadata ---"
find /etc/ssl /opt/ai-defense-manager \
  -type f \( -iname '*ca*.crt' -o -iname '*ca*.pem' -o -iname '*ca*.cer' \) \
  -printf '%p\n' 2>/dev/null | head -40

echo
echo "CA_PRIVATE_KEY_DISPLAYED=NO"
echo "BEARER_TOKEN_DISPLAYED=NO"
echo "NETWORK_REQUEST=NO"
echo "CONFIGURATION_CHANGED=NO"
```

VM 230 loads the internal CA certificate from `/etc/ai-defense-manager/credentials/relay-ca.crt`, and TLS verification is not disabled.

> **Run on: VM 230**

```bash
echo "===== VM230: RELAY CREDENTIAL FILE AVAILABILITY ====="

echo
echo "--- Credential directory ---"
if [ -d /etc/ai-defense-manager/credentials ]; then
    stat -c 'directory owner=%U:%G mode=%a' \
      /etc/ai-defense-manager/credentials
else
    echo "CREDENTIAL_DIRECTORY=MISSING"
fi

echo
echo "--- Expected CA certificate ---"
if [ -f /etc/ai-defense-manager/credentials/relay-ca.crt ]; then
    stat -c 'CA owner=%U:%G mode=%a size=%s' \
      /etc/ai-defense-manager/credentials/relay-ca.crt
    openssl x509 \
      -in /etc/ai-defense-manager/credentials/relay-ca.crt \
      -noout -subject -issuer -fingerprint -sha256
else
    echo "RELAY_CA_FILE=MISSING"
fi

echo
echo "--- Expected API token file (contents hidden) ---"
if [ -f /etc/ai-defense-manager/credentials/relay-api.token ]; then
    stat -c 'TOKEN_FILE owner=%U:%G mode=%a size=%s' \
      /etc/ai-defense-manager/credentials/relay-api.token
else
    echo "RELAY_TOKEN_FILE=MISSING"
fi

echo
echo "--- Service credential-related metadata (values excluded) ---"
systemctl show ai-defense-manager.service \
  -p User -p Group -p LoadCredential -p LoadCredentialEncrypted

echo
echo "CREDENTIAL_CONTENTS_DISPLAYED=NO"
echo "NETWORK_REQUEST=NO"
echo "CONFIGURATION_CHANGED=NO"
```

| Item | State |
|---|---|
| CA certificate | present and readable; issuer `AI-Defense-Relay-Internal-CA` |
| API token | present (contents not displayed) |
| Credentials directory | `root:ai-defense`, `750` |
| CA and token files | `root:ai-defense`, `640` |

The SHA-256 fingerprint of VM 230's CA certificate was as follows.

```text
71:E8:CE:68:FA:56:0D:13:98:5A:1C:C5:18:D3:24:4B:BA:DA:6F:29:DE:49:97:71:0C:29:F9:21:D2:84:61:54
```

### 2.3 The Original CA File on VM 220

> **Run on: VM 220**

```bash
echo "===== VM220: INTERNAL CA CERTIFICATE FINGERPRINT AUDIT ====="

PID=$(systemctl show ai-defense-relay.service -p MainPID --value)
CRED_DIR=$(tr '\0' '\n' < "/proc/${PID}/environ" | sed -n 's/^CREDENTIALS_DIRECTORY=//p' | head -1)

echo
echo "--- Credential directory path ---"
if [ -n "$CRED_DIR" ] && [ -d "$CRED_DIR" ]; then
    echo "CREDENTIAL_DIRECTORY=AVAILABLE"
    find "$CRED_DIR" -maxdepth 1 -type f -printf '%f\n' | sort
else
    echo "CREDENTIAL_DIRECTORY=NOT_AVAILABLE"
fi

echo
echo "--- Public certificate fingerprints in credential directory ---"
if [ -n "$CRED_DIR" ] && [ -d "$CRED_DIR" ]; then
    find "$CRED_DIR" -maxdepth 1 -type f \
      \( -iname '*.crt' -o -iname '*.pem' -o -iname '*ca*' \) \
      ! -iname '*key*' -print0 |
    while IFS= read -r -d '' cert; do
        echo "CERTIFICATE_FILE=$(basename "$cert")"
        openssl x509 -in "$cert" -noout \
          -subject -issuer -fingerprint -sha256 2>/dev/null
    done
fi

echo
echo "--- Relay systemd credential declarations (paths only) ---"
systemctl cat ai-defense-relay.service |
  grep -E '^[[:space:]]*(LoadCredential|LoadCredentialEncrypted)=' |
  sed -E 's/:[^ ]*(token|password|key)[^ ]*/:<REDACTED>/Ig'

echo
echo "PRIVATE_KEY_CONTENT_DISPLAYED=NO"
echo "TOKEN_CONTENT_DISPLAYED=NO"
echo "INDEXER_PASSWORD_DISPLAYED=NO"
echo "NETWORK_REQUEST=NO"
echo "CONFIGURATION_CHANGED=NO"
```

`indexer-ca` in VM 220's credentials is for Wazuh Indexer, not the Relay's CA. We look for the original file of the Relay's CA.

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY CA SOURCE FILE AUDIT ====="

echo
echo "--- Candidate CA certificate files ---"
find /etc/credstore /etc/ssl /usr/local/share/ca-certificates \
  -maxdepth 3 -type f \
  \( -iname '*relay*ca*' -o -iname '*defense*ca*' -o -iname '*internal*ca*' \) \
  -printf '%p\n' 2>/dev/null

echo
echo "--- Systemd credential source declarations ---"
systemctl cat ai-defense-relay.service |
  grep -E '^[[:space:]]*LoadCredential(Encrypted)?=' |
  sed -E 's/:[^ ]*(token|password|key)[^ ]*/:<REDACTED>/Ig'

echo
echo "--- Server certificate issuer and SAN ---"
PID=$(systemctl show ai-defense-relay.service -p MainPID --value)
CRED_DIR=$(tr '\0' '\n' < "/proc/${PID}/environ" |
  sed -n 's/^CREDENTIALS_DIRECTORY=//p' | head -1)

openssl x509 -in "$CRED_DIR/server-cert" -noout \
  -issuer -subject -ext subjectAltName

echo
echo "PRIVATE_KEY_DISPLAYED=NO"
echo "CREDENTIAL_CONTENTS_DISPLAYED=NO"
echo "NETWORK_REQUEST=NO"
echo "CONFIGURATION_CHANGED=NO"
```

The Relay's dedicated CA was in `/etc/credstore/ai-defense-relay-ca`.

### 2.4 Matching Fingerprints and Signatures

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY CA CRYPTOGRAPHIC VERIFICATION ====="

CA=/etc/credstore/ai-defense-relay-ca

PID=$(systemctl show ai-defense-relay.service -p MainPID --value)
CRED_DIR=$(tr '\0' '\n' < "/proc/${PID}/environ" |
  sed -n 's/^CREDENTIALS_DIRECTORY=//p' | head -1)

echo
echo "--- Relay CA file metadata ---"
stat -c 'owner=%U:%G mode=%a size=%s' "$CA"

echo
echo "--- Relay CA identity and fingerprint ---"
openssl x509 -in "$CA" -noout \
  -subject -issuer -serial -fingerprint -sha256

echo
echo "--- Server certificate verification against Relay CA ---"
openssl verify -CAfile "$CA" "$CRED_DIR/server-cert"

echo
echo "--- Server certificate fingerprint ---"
openssl x509 -in "$CRED_DIR/server-cert" -noout -fingerprint -sha256

echo
echo "PRIVATE_KEY_DISPLAYED=NO"
echo "CREDENTIAL_CONTENTS_DISPLAYED=NO"
echo "NETWORK_REQUEST=NO"
echo "CONFIGURATION_CHANGED=NO"
```

| Checked | Result |
|---|---|
| SHA-256 of VM 220's CA | `71:E8:CE:68:…:84:61:54` |
| SHA-256 of VM 230's CA | the same |
| CA Subject | `AI-Defense-Relay-Internal-CA` |
| Server certificate verified by the CA | `OK` |
| Server certificate SAN | `192.168.0.220` |
| Minimum TLS version | TLS 1.2 |

We confirmed that the trust relationship is correct cryptographically, not just that the issuer names are the same.

## Chapter 3: Testing with `/health`

### 3.1 An Endpoint That Does Not Query the Indexer

Calling `/v1/alerts` queries Wazuh Indexer. First we check whether there is an endpoint that does not.

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY NON-INDEXER TEST ENDPOINT AUDIT ====="

cd /opt/ai-defense-relay || true

echo
echo "--- HTTP handler routes and response paths ---"
grep -n -E \
  'def do_|urlsplit|parse_qs|send_json|indexer|alerts|health|status|method_not_allowed' \
  relay.py

echo
echo "--- Route dispatch context ---"
sed -n '125,265p' relay.py |
  sed -E 's/(API_TOKEN|INDEXER_PASSWORD|INDEXER_AUTH)[[:space:]]*=.*/\1 = <REDACTED>/'

echo
echo "SOURCE_MODIFIED=NO"
echo "HTTP_REQUEST=NO"
echo "WAZUH_INDEXER_REQUEST=NO"
echo "DATABASE_ACCESSED=NO"
echo "CREDENTIALS_DISPLAYED=NO"
```

The Relay processes requests in the following order; for `/health` it returns `200 OK` before querying the Indexer.

1. Check that the source IP address is `192.168.0.221`
2. Check the Bearer token
3. For `/health`, return `200 OK` and finish
4. Query Wazuh Indexer only for `/v1/alerts`

### 3.2 Testing TLS and Bearer Authentication

With CA certificate verification and Bearer authentication enabled, the token is read from the file and used in memory only.

> **Run on: VM 230**

```bash
echo "===== VM230 -> VM220: TLS + BEARER AUTH HEALTH TEST ====="

cd /opt/ai-defense-manager || true

venv/bin/python - <<'PY'
from pathlib import Path
import httpx
import sys

base_url = "https://192.168.0.220:8765"
ca_file = Path("/etc/ai-defense-manager/credentials/relay-ca.crt")
token_file = Path("/etc/ai-defense-manager/credentials/relay-api.token")

print("CA_FILE_EXISTS =", ca_file.is_file())
print("TOKEN_FILE_EXISTS =", token_file.is_file())

if not ca_file.is_file() or not token_file.is_file():
    print("RESULT=PRECHECK_FAILED")
    sys.exit(0)

token = token_file.read_text(encoding="utf-8").strip()

if not token:
    print("RESULT=EMPTY_TOKEN")
    sys.exit(0)

try:
    with httpx.Client(
        verify=str(ca_file),
        timeout=10.0,
        follow_redirects=False,
    ) as client:
        response = client.get(
            base_url + "/health",
            headers={"Authorization": "Bearer " + token},
        )

    print("HTTP_STATUS =", response.status_code)
    print("RESPONSE_BODY =", response.text[:512])

    if response.status_code == 200 and response.json() == {"status": "ok"}:
        print("TLS_VERIFICATION=PASS")
        print("BEARER_AUTHENTICATION=PASS")
        print("RELAY_HEALTH=PASS")
        print("RESULT=PASS")
    else:
        print("RESULT=FAIL")

except httpx.ConnectError as exc:
    print("CONNECTION_OR_TLS_ERROR =", type(exc).__name__)
    print("RESULT=FAIL")
except httpx.TimeoutException:
    print("ERROR=TIMEOUT")
    print("RESULT=FAIL")
except Exception as exc:
    print("ERROR_TYPE =", type(exc).__name__)
    print("RESULT=FAIL")

print("TOKEN_DISPLAYED=NO")
print("WAZUH_INDEXER_REQUEST=NO")
print("DATABASE_ACCESSED=NO")
print("OLLAMA_REQUEST=NO")
PY
```

| Checked | Result |
|---|---|
| Loading the CA certificate | passed |
| TLS certificate verification | passed |
| Source IP restriction | passed (200 response) |
| Bearer authentication | passed |
| Relay `/health` | `HTTP 200` |
| Access to Wazuh Indexer, PostgreSQL, Ollama | none |

## Closing Notes

In Part 51 we confirmed that a secure HTTPS path from VM 230 to the Relay on VM 220 is in place.

| Item | Result |
|---|---|
| Connection target | `https://192.168.0.220:8765/` (TLS 1.2 or later) |
| Server certificate | SAN `192.168.0.220`, signed by `AI-Defense-Relay-Internal-CA` |
| CA | VM 220 `/etc/credstore/ai-defense-relay-ca` and VM 230 `relay-ca.crt` are the same |
| Authentication | source IP (`192.168.0.221`) and Bearer token |
| `/health` | `HTTP 200` |

In the next part, Part 52, we fetch real Wazuh alerts once.

# Part 52: Fetching Real Alerts and Fixing the Relay's 502
## Introduction

### About This Book

This is Part 52 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 51 we checked TLS and authentication from VM 230 to the Relay on VM 220. Here we fetch real Wazuh alerts.

1. Using `GET /api/v1/wazuh/events` on VM 230, fetch alerts once (up to 10, from the last 15 minutes)
2. The Relay returned `HTTP 502`, so investigate the cause without displaying alert values
3. Fix the cause (`relay.py` lacks `import re`) with one line and restart the Relay
4. Fetch alerts again and confirm they are received as the seven-field allowlist specifies

Alert bodies, IP addresses, descriptions, user names, passwords and tokens are not displayed. No AI analysis, no storing in SQLite and nothing sent to Ollama.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **VM 220**: security-core (root)

## Chapter 1: Fetching Alerts Once

### 1.1 Choosing the API

> **Run on: VM 230**

```bash
echo "===== VM230: LIVE WAZUH FETCH PRE-FLIGHT ====="

cd /opt/ai-defense-manager || true

echo
echo "--- Relay client configuration ---"
grep -n -E \
  'wazuh_relay_base_url|wazuh_relay_ca_file|wazuh_relay_token_file|wazuh_relay_timeout' \
  app/core/config.py

echo
echo "--- Relay fetch limits and normalization ---"
grep -n -E \
  'limit|since_minutes|sanitize|normalize|/v1/alerts|AsyncClient' \
  app/services/wazuh_relay.py

echo
echo "--- API route behavior ---"
sed -n '1,240p' app/api/wazuh.py

echo
echo "NETWORK_REQUEST=NO"
echo "DATABASE_WRITE=NO"
echo "OLLAMA_REQUEST=NO"
echo "SOURCE_MODIFIED=NO"
```

`POST /api/v1/wazuh/analyze` goes as far as Ollama analysis and storing history in SQLite, so we do not use it. We use `GET /api/v1/wazuh/events`, which only fetches.

| Item | Setting |
|---|---|
| API | `GET /api/v1/wazuh/events` |
| Maximum count | 10 |
| Period | 15 minutes |
| Communication with the Relay | HTTPS, CA verification, Bearer authentication |
| AI analysis, storing in SQLite | not done |

### 1.2 Trying to Fetch

Bodies, IP addresses, descriptions and IDs are not displayed; only counts and check results.

> **Run on: VM 230**

```bash
echo "===== VM230: ONE-TIME LIVE WAZUH EVENT FETCH ====="

cd /opt/ai-defense-manager || true

venv/bin/python - <<'PY'
import asyncio
from collections import Counter
from app.services.wazuh_relay import fetch_wazuh_events

async def main():
    events = await fetch_wazuh_events(limit=10, since_minutes=15)

    severity = Counter()
    categories = Counter()
    invalid = 0

    for event in events:
        try:
            severity[str(event.severity)] += 1
            categories[str(event.event_category)] += 1
            if not event.event_id or not event.observed_at:
                invalid += 1
        except Exception:
            invalid += 1

    print("FETCH=SUCCESS")
    print(f"EVENT_COUNT={len(events)}")
    print(f"SEVERITY_COUNTS={dict(sorted(severity.items()))}")
    print(f"CATEGORY_COUNTS={dict(sorted(categories.items()))}")
    print(f"INVALID_EVENT_COUNT={invalid}")
    print(f"LIMIT=10")
    print(f"WINDOW_MINUTES=15")
    print("EVENT_CONTENT_DISPLAYED=NO")
    print("AI_ANALYSIS=NOT_RUN")
    print("OLLAMA_REQUEST=NO")
    print("DATABASE_WRITE=NO")

asyncio.run(main())
PY
```

The Relay returned `HTTP 502`. `/health` was `HTTP 200`, so the path to the Relay and authentication work. `/v1/alerts` is designed to return `HTTP 502` when an exception occurs while querying the Indexer or processing the results.

## Chapter 2: Investigating the 502

### 2.1 State of the Indexer and the Relay

We make no HTTP requests to the Indexer and look only at state and logs.

> **Run on: VM 220**

```bash
echo "===== VM220: WAZUH INDEXER CONNECTIVITY DIAGNOSTICS ====="

echo
echo "--- Indexer service state ---"
systemctl is-active wazuh-indexer
systemctl show wazuh-indexer \
  -p ActiveState -p SubState -p MainPID -p Result

echo
echo "--- Local TCP listener on port 9200 ---"
ss -lntp | grep -E '127\.0\.0\.1:9200|:9200[[:space:]]' || true

echo
echo "--- Indexer recent service errors ---"
journalctl -u wazuh-indexer --since "30 minutes ago" \
  --no-pager -p err | tail -40

echo
echo "--- Relay recent service logs ---"
journalctl -u ai-defense-relay.service --since "15 minutes ago" \
  --no-pager | tail -40

echo
echo "--- Indexer CA certificate metadata ---"
stat -c 'owner=%U:%G mode=%a size=%s' \
  /etc/credstore/ai-defense-indexer-ca

openssl x509 -in /etc/credstore/ai-defense-indexer-ca \
  -noout -subject -issuer -dates

echo
echo "INDEXER_HTTP_REQUEST=NO"
echo "CREDENTIALS_DISPLAYED=NO"
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
```

Wazuh Indexer is `active (running)`, listens on `127.0.0.1:9200`, and had no errors in the last 30 minutes. The Relay's log recorded `HTTP 502` for `/v1/alerts`. The Relay turns every exception into `indexer_unavailable`, so the log alone does not reveal the cause.

### 2.2 Indexer Search Permissions

As the same user as the Relay (`ai-defense-reader`), we try a search that returns no alert bodies (`size: 0`).

> **Run on: VM 220**

```bash
echo "===== VM220: READ-ONLY ALERT SEARCH PERMISSION TEST ====="

python3 - <<'PY'
import ssl
import json
import base64
import urllib.request
import urllib.error
from pathlib import Path

base = "https://127.0.0.1:9200"
ctx_admin = ssl.create_default_context(
    cafile="/etc/wazuh-indexer/certs/root-ca.pem"
)
ctx_admin.load_cert_chain(
    "/etc/wazuh-indexer/certs/admin.pem",
    "/etc/wazuh-indexer/certs/admin-key.pem"
)

# Refer to the Relay systemd credential. Do not display secrets.
import subprocess
pid = subprocess.check_output(
    ["systemctl", "show", "ai-defense-relay.service",
     "-p", "MainPID", "--value"], text=True
).strip()

env = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
cred_dir = next(
    x.split(b"=", 1)[1].decode()
    for x in env if x.startswith(b"CREDENTIALS_DIRECTORY=")
)
password = (Path(cred_dir) / "indexer-password").read_bytes().strip()
reader_auth = base64.b64encode(
    b"ai-defense-reader:" + password
).decode()

body = json.dumps({
    "size": 0,
    "track_total_hits": False,
    "query": {"match_all": {}}
}).encode()

endpoint = base + "/wazuh-alerts-4.x-*/_search"

tests = [
    ("ADMIN_CERT", ctx_admin, {}),
    ("READER_USER", ssl.create_default_context(
        cafile=str(Path(cred_dir) / "indexer-ca")
    ), {"Authorization": "Basic " + reader_auth}),
]

for name, ctx, headers in tests:
    print("\n---", name, "---")
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            **headers
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            result = json.loads(r.read())
            print("HTTP_STATUS =", r.status)
            print("TIMED_OUT =", result.get("timed_out"))
            print("SHARDS =", result.get("_shards"))
            print("TOTAL_HITS =", result.get("hits", {}).get("total"))
    except urllib.error.HTTPError as e:
        print("HTTP_STATUS =", e.code)
        print("RESPONSE_BODY_DISPLAYED=NO")
    except Exception as e:
        print("ERROR_TYPE =", type(e).__name__)

print("\nSEARCH_SIZE=0")
print("ALERT_DOCUMENTS_RETURNED=NO")
print("PASSWORD_DISPLAYED=NO")
print("CONFIGURATION_CHANGED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

| Checked | Result |
|---|---|
| Search with the admin certificate | `HTTP 200` |
| Search as `ai-defense-reader` | `HTTP 200` |
| Shards | 21/21 succeeded |
| Timeouts | none |

`ai-defense-reader` can search the alert indexes. There is no need to add permissions to the role.

> **Note:** Accessing the Indexer's root URL (`/`) as `ai-defense-reader` gives `403` (no `cluster:monitor/main` permission), but that is separate from searching alerts. We keep the minimal permissions and leave the cluster permissions empty.

### 2.3 Searching Under the Same Conditions as the Relay

The Relay's search uses a 15-minute range on `timestamp`, newest first, and a `_source` limited to the seven fields. We try the same conditions without returning documents.

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY-IDENTICAL QUERY VALIDATION (ZERO DOCUMENTS) ====="

python3 - <<'PY'
import os
import ssl
import json
import base64
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

pid = subprocess.check_output(
    ["systemctl", "show", "ai-defense-relay.service",
     "-p", "MainPID", "--value"], text=True
).strip()

env = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
cred_dir = next(
    x.split(b"=", 1)[1].decode()
    for x in env if x.startswith(b"CREDENTIALS_DIRECTORY=")
)

password = (Path(cred_dir) / "indexer-password").read_bytes().strip()
auth = base64.b64encode(
    b"ai-defense-reader:" + password
).decode()

fields = [
    "timestamp",
    "rule.id",
    "rule.level",
    "rule.groups",
    "rule.description",
    "decoder.name",
    "agent.id",
]

query = {
    "size": 0,
    "track_total_hits": False,
    "sort": [{"timestamp": {"order": "desc"}}],
    "_source": fields,
    "query": {
        "range": {
            "timestamp": {"gte": "now-15m"}
        }
    }
}

ctx = ssl.create_default_context(
    cafile=str(Path(cred_dir) / "indexer-ca")
)

req = urllib.request.Request(
    "https://127.0.0.1:9200/wazuh-alerts-4.x-*/_search",
    data=json.dumps(query).encode(),
    headers={
        "Authorization": "Basic " + auth,
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        result = json.loads(r.read())
        print("HTTP_STATUS =", r.status)
        print("TIMED_OUT =", result.get("timed_out"))
        print("SHARDS =", result.get("_shards"))
        print("RESPONSE_KEYS =", sorted(result.keys()))
        print("HITS_CONTAINER_TYPE =", type(result.get("hits")).__name__)
        print("DOCUMENTS_RETURNED =", len(
            result.get("hits", {}).get("hits", [])
        ))
except urllib.error.HTTPError as e:
    print("HTTP_STATUS =", e.code)
    print("RESPONSE_BODY_DISPLAYED=NO")
except Exception as e:
    print("ERROR_TYPE =", type(e).__name__)

print("\nQUERY_SIZE=0")
print("ALERT_DOCUMENTS_RETURNED=NO")
print("PASSWORD_DISPLAYED=NO")
print("CONFIGURATION_CHANGED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

TLS verification, authentication, index access, the range, the sort order, the field selection and the JSON shape of the response were all normal. **The cause is narrowed down to the processing when the search returns one or more results.**

### 2.4 Checking with Real Alerts Without Looking at Values

We fetch up to 10 real alerts and, in memory only inside VM 220, count only the number, types, results of the masking step and exception class names.

> **Run on: VM 220**

```bash
echo "===== VM220: APPROVED PRIVATE ALERT SANITIZATION TEST ====="

cd /opt/ai-defense-relay

python3 - <<'PY'
import os
import sys
import json
import ssl
import base64
import importlib.util
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from collections import Counter

# systemd credential directory
pid = subprocess.check_output(
    ["systemctl", "show", "ai-defense-relay.service",
     "-p", "MainPID", "--value"], text=True
).strip()

env = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
cred_dir = next(
    x.split(b"=", 1)[1].decode()
    for x in env if x.startswith(b"CREDENTIALS_DIRECTORY=")
)
os.environ["CREDENTIALS_DIRECTORY"] = cred_dir

# Load the actual Relay sanitizer without starting its HTTP server.
spec = importlib.util.spec_from_file_location(
    "relay_audit_module", "/opt/ai-defense-relay/relay.py"
)
relay = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = relay
spec.loader.exec_module(relay)

password = (Path(cred_dir) / "indexer-password").read_bytes().strip()
auth = base64.b64encode(
    b"ai-defense-reader:" + password
).decode()

query = {
    "size": 10,
    "track_total_hits": False,
    "sort": [{"timestamp": {"order": "desc"}}],
    "_source": list(relay.ALLOWED_FIELDS),
    "query": {
        "range": {
            "timestamp": {"gte": "now-15m"}
        }
    }
}

ctx = ssl.create_default_context(
    cafile=str(Path(cred_dir) / "indexer-ca")
)

req = urllib.request.Request(
    relay.INDEXER_URL,
    data=json.dumps(query).encode("utf-8"),
    headers={
        "Authorization": "Basic " + auth,
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
    method="POST",
)

print("QUERY_LIMIT=10")
print("QUERY_WINDOW_MINUTES=15")
print("SOURCE_FIELDS_COUNT=", len(relay.ALLOWED_FIELDS))

try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
        raw = response.read(2 * 1024 * 1024 + 1)
        print("INDEXER_HTTP_STATUS=", response.status)

    if len(raw) > 2 * 1024 * 1024:
        print("RESULT=RESPONSE_TOO_LARGE")
    else:
        data = json.loads(raw)
        hits_container = data.get("hits", {})
        hits = hits_container.get("hits", [])

        print("TIMED_OUT=", data.get("timed_out"))
        print("SHARD_FAILURES=",
              data.get("_shards", {}).get("failed"))
        print("HIT_CONTAINER_TYPE=", type(hits).__name__)
        print("RAW_HIT_COUNT=", len(hits))

        source_types = Counter()
        field_types = {f: Counter() for f in relay.ALLOWED_FIELDS}
        sanitized_ok = 0
        sanitized_rejected = 0
        sanitizer_exceptions = Counter()
        non_dict_hits = 0
        non_dict_sources = 0

        for hit in hits:
            if not isinstance(hit, dict):
                non_dict_hits += 1
                continue

            source = hit.get("_source")
            source_types[type(source).__name__] += 1

            if not isinstance(source, dict):
                non_dict_sources += 1
                continue

            for field in relay.ALLOWED_FIELDS:
                value = source
                for part in field.split("."):
                    if not isinstance(value, dict):
                        value = None
                        break
                    value = value.get(part)

                if value is not None:
                    field_types[field][type(value).__name__] += 1

            try:
                result = relay.sanitize_alert(source)
                if result is None:
                    sanitized_rejected += 1
                else:
                    sanitized_ok += 1
            except Exception as exc:
                sanitizer_exceptions[type(exc).__name__] += 1

        print("SOURCE_TYPES=", dict(source_types))
        print("NON_DICT_HITS=", non_dict_hits)
        print("NON_DICT_SOURCES=", non_dict_sources)
        print("SANITIZED_ACCEPTED=", sanitized_ok)
        print("SANITIZED_REJECTED=", sanitized_rejected)
        print("SANITIZER_EXCEPTION_TYPES=", dict(sanitizer_exceptions))

        print("--- ALLOWED FIELD VALUE TYPES ONLY ---")
        for field in relay.ALLOWED_FIELDS:
            print(field, dict(field_types[field]))

        print("--- RESPONSE STRUCTURE ---")
        print("TOP_LEVEL_TYPE=", type(data).__name__)
        print("HITS_TYPE=", type(hits_container).__name__)

except urllib.error.HTTPError as exc:
    print("INDEXER_HTTP_STATUS=", exc.code)
    print("INDEXER_ERROR_BODY_DISPLAYED=NO")
except Exception as exc:
    print("TEST_EXCEPTION_TYPE=", type(exc).__name__)

print("\nALERT_VALUES_DISPLAYED=NO")
print("PASSWORD_DISPLAYED=NO")
print("DATABASE_WRITES=NO")
print("OLLAMA_REQUESTED=NO")
print("CONFIGURATION_CHANGED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

| Checked | Result |
|---|---|
| Indexer search | `HTTP 200` |
| Alerts fetched | 1 |
| Types of the seven fields | all as expected |
| Masking step (`sanitize_alert()`) | **`NameError`** |

### 2.5 Imported Modules

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY IMPORT DEPENDENCY AUDIT ====="

cd /opt/ai-defense-relay

echo
echo "--- First 55 lines of relay.py ---"
sed -n '1,55p' relay.py

echo
echo "--- AST import inventory ---"
python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/opt/ai-defense-relay/relay.py")
tree = ast.parse(path.read_text(encoding="utf-8"))

imports = set()

for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for item in node.names:
            imports.add(item.name.split(".")[0])
    elif isinstance(node, ast.ImportFrom) and node.module:
        imports.add(node.module.split(".")[0])

print("IMPORTED_MODULES =", sorted(imports))
print("RE_IMPORTED =", "re" in imports)
print("SOURCE_SYNTAX=PASS")
PY

echo
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "CREDENTIALS_DISPLAYED=NO"
```

**`relay.py` had no `import re`.** `sanitize_alert()` uses `re.fullmatch()` to check `rule.groups`, `rule.id` and `agent.id` (the checks added in Part 49). So processing real alerts caused a `NameError`, and the Relay returned `502`.

## Chapter 3: Adding `import re`

### 3.1 Checking Before the Fix

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY MINIMAL FIX PRECHECK ====="

cd /opt/ai-defense-relay

echo
echo "--- Existing import block ---"
sed -n '1,25p' relay.py

echo
echo "--- Backup directory availability ---"
install -d -m 700 /var/backups/ai-defense-relay
stat -c 'owner=%U:%G mode=%a path=%n' \
  /var/backups/ai-defense-relay

echo
echo "--- Current source hash ---"
sha256sum relay.py

echo
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

Only the following one line is added.

```python
import re
```

### 3.2 Fixing

We make a copy, add only `import re`, and check the syntax. The service is not restarted.

> **Run on: VM 220**

```bash
echo "===== VM220: APPLY MINIMAL RELAY IMPORT FIX ====="

cd /opt/ai-defense-relay

BACKUP_DIR="/var/backups/ai-defense-relay/20261123-import-re-fix"
install -d -m 700 "$BACKUP_DIR"

echo
echo "--- Create backup ---"
cp -a relay.py "$BACKUP_DIR/relay.py"
sha256sum relay.py "$BACKUP_DIR/relay.py"

echo
echo "--- Add only import re ---"
python3 - <<'PY'
from pathlib import Path

p = Path("/opt/ai-defense-relay/relay.py")
text = p.read_text(encoding="utf-8")

if "\nimport re\n" in text:
    raise SystemExit("ABORT: import re already exists")

anchor = "import hmac\n"
if text.count(anchor) != 1:
    raise SystemExit("ABORT: import anchor is not unique")

updated = text.replace(anchor, anchor + "import re\n", 1)
p.write_text(updated, encoding="utf-8")
print("IMPORT_RE_ADDED=YES")
PY

echo
echo "--- Python syntax check ---"
python3 -m py_compile relay.py
echo "PYTHON_COMPILE=PASS"

echo
echo "--- Sanitizer unit test (synthetic data only) ---"
python3 - <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location(
    "relay_test_module", "/opt/ai-defense-relay/relay.py"
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

sample = {
    "timestamp": "2026-11-23T00:00:00Z",
    "rule": {
        "id": "5710",
        "level": 5,
        "groups": ["syslog", "authentication"],
        "description": "synthetic test event",
    },
    "decoder": {"name": "test-decoder"},
    "agent": {"id": "001"},
    "full_log": "MUST_NOT_BE_INCLUDED",
    "data": {"secret": "MUST_NOT_BE_INCLUDED"},
}

result = module.sanitize_alert(sample)

assert result is not None
assert set(result).issubset(set(module.ALLOWED_FIELDS))
assert "full_log" not in result
assert "data" not in result
assert result["rule.groups"] == ["syslog", "authentication"]

print("SANITIZER_TEST=PASS")
print("ALLOWLIST_ONLY=PASS")
print("SENSITIVE_FIELDS_EXCLUDED=PASS")
print("TEST_EVENT_VALUES_DISPLAYED=NO")
PY

echo
echo "--- Final source integrity ---"
sha256sum relay.py "$BACKUP_DIR/relay.py"
stat -c 'owner=%U:%G mode=%a size=%s' relay.py
grep -n '^import re$' relay.py

echo
echo "BACKUP=$BACKUP_DIR/relay.py"
echo "SERVICE_RESTARTED=NO"
echo "INDEXER_REQUESTED=NO"
echo "DATABASE_WRITES=NO"
echo "OLLAMA_REQUESTED=NO"
```

The SHA256 of the copy and of the file just before the fix matched, `import re` went in on line 6, the syntax check passed, and the owner and permissions stayed `root:ai-defense-relay`, `640`.

The test of the masking step in this script did not run in the test environment, because loading `relay.py` requires systemd credentials (this is not a credentials problem).

### 3.3 Testing Only the Masking Step Separately

Without loading credentials, we extract only `sanitize_alert()` and test it with synthetic data.

> **Run on: VM 220**

```bash
echo "===== VM220: ISOLATED SANITIZER UNIT TEST ====="

cd /opt/ai-defense-relay

python3 - <<'PY'
import ast
from pathlib import Path

path = Path("/opt/ai-defense-relay/relay.py")
tree = ast.parse(path.read_text(encoding="utf-8"))

allowed = [
    node for node in tree.body
    if isinstance(node, ast.Assign)
    and any(
        isinstance(target, ast.Name) and target.id == "ALLOWED_FIELDS"
        for target in node.targets
    )
]

sanitizers = [
    node for node in tree.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "sanitize_alert"
]

if len(allowed) != 1 or len(sanitizers) != 1:
    raise RuntimeError("Could not uniquely locate sanitizer dependencies")

isolated = ast.Module(
    body=[
        ast.Import(names=[ast.alias(name="re")]),
        allowed[0],
        sanitizers[0],
    ],
    type_ignores=[],
)
ast.fix_missing_locations(isolated)

namespace = {}
exec(compile(isolated, str(path), "exec"), namespace)

sample = {
    "timestamp": "2026-11-23T00:00:00Z",
    "rule": {
        "id": "5710",
        "level": 5,
        "groups": ["syslog", "authentication"],
        "description": "synthetic test event",
    },
    "decoder": {"name": "test-decoder"},
    "agent": {"id": "001"},
    "full_log": "MUST_NOT_BE_INCLUDED",
    "data": {"secret": "MUST_NOT_BE_INCLUDED"},
}

result = namespace["sanitize_alert"](sample)

assert result is not None, "Valid synthetic event was rejected"
assert set(result).issubset(set(namespace["ALLOWED_FIELDS"]))
assert "full_log" not in result
assert "data" not in result
assert result["rule.groups"] == ["syslog", "authentication"]

print("SANITIZER_VALID_EVENT=PASS")
print("ALLOWLIST_ONLY=PASS")
print("SENSITIVE_FIELDS_EXCLUDED=PASS")
print("SYNTHETIC_VALUES_DISPLAYED=NO")
PY

echo
echo "===== SOURCE INTEGRITY ====="
python3 -m py_compile relay.py
echo "PYTHON_COMPILE=PASS"
sha256sum relay.py
stat -c 'owner=%U:%G mode=%a size=%s' relay.py

echo "SERVICE_RESTARTED=NO"
echo "LIVE_INDEXER_REQUESTED=NO"
```

Accepting a valid synthetic event, returning only allowlisted fields, removing `full_log` and `data`, the syntax, and the owner and permissions all passed.

### 3.4 Restarting the Relay

> **Run on: VM 220**

```bash
echo "===== VM220: RESTART AI DEFENSE RELAY ====="

systemctl restart ai-defense-relay.service

echo
echo "--- Service status ---"
systemctl is-active ai-defense-relay.service
systemctl show ai-defense-relay.service \
  -p MainPID \
  -p ActiveState \
  -p SubState \
  -p User \
  -p Group

echo
echo "--- Listener verification ---"
ss -lntp '( sport = :8765 )'

echo
echo "--- Recent service journal (no credentials) ---"
journalctl -u ai-defense-relay.service -n 15 --no-pager \
  -o short-iso-precise

echo
echo "--- Source integrity ---"
sha256sum /opt/ai-defense-relay/relay.py

echo
echo "INDEXER_REQUESTED=NO"
echo "DATABASE_REQUESTED=NO"
echo "OLLAMA_REQUESTED=NO"
```

The service was `active (running)` with new PID `25723`. Right after the restart, `ss` did not show port 8765 listening, so we check again.

> **Run on: VM 220**

```bash
echo "===== VM220: RELAY LISTENER DIAGNOSTICS ====="

echo
echo "--- systemd detailed status ---"
systemctl status ai-defense-relay.service --no-pager -l

echo
echo "--- Process state ---"
ps -p 25723 -o pid,ppid,user,group,stat,etime,comm

echo
echo "--- All TCP listeners ---"
ss -lntp

echo
echo "--- Relay process file descriptors (socket metadata only) ---"
find /proc/25723/fd -maxdepth 1 -type l -printf '%f -> %l\n' 2>/dev/null \
  | grep 'socket:' || true

echo
echo "--- Startup journal since 06:50 UTC ---"
journalctl -u ai-defense-relay.service \
  --since "2026-11-23 06:50:00 UTC" \
  --no-pager -o short-iso-precise

echo
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
echo "INDEXER_REQUESTED=NO"
echo "DATABASE_REQUESTED=NO"
echo "OLLAMA_REQUESTED=NO"
```

It listens on `192.168.0.220:8765`, and the startup log contains `AI Defense Relay listening on 192.168.0.220:8765`. The earlier `ss` was simply too soon.

## Chapter 4: Fetching Alerts Again

### 4.1 `/health`

> **Run on: VM 230**

```bash
echo "===== VM230: POST-RESTART RELAY HEALTH CHECK ====="

python3 - <<'PY'
import json
import ssl
import urllib.request
from pathlib import Path

base = "https://192.168.0.220:8765"
credentials = Path("/etc/ai-defense-manager/credentials")
ca_file = credentials / "relay-ca.crt"
token_file = credentials / "relay-api.token"

if not ca_file.is_file() or not token_file.is_file():
    raise RuntimeError("Required credential file is unavailable")

token = token_file.read_text(encoding="utf-8").strip()
if not token:
    raise RuntimeError("Relay token is empty")

context = ssl.create_default_context(cafile=str(ca_file))
request = urllib.request.Request(
    base + "/health",
    headers={"Authorization": "Bearer " + token},
    method="GET",
)

try:
    with urllib.request.urlopen(
        request, context=context, timeout=10
    ) as response:
        body = response.read(4096)
        print("HTTP_STATUS =", response.status)
        print("TLS_VERIFICATION = PASS")
        print("BEARER_AUTH = PASS")
        try:
            print("BODY =", json.dumps(
                json.loads(body.decode("utf-8")),
                ensure_ascii=False
            ))
        except Exception:
            print("BODY_JSON = INVALID")
except Exception as exc:
    print("HEALTH_CHECK = FAILED")
    print("ERROR_TYPE =", type(exc).__name__)
    if hasattr(exc, "code"):
        print("HTTP_STATUS =", exc.code)

print("ALERTS_ENDPOINT_REQUESTED = NO")
print("INDEXER_SEARCH_REQUESTED = NO")
print("DATABASE_REQUESTED = NO")
print("OLLAMA_REQUESTED = NO")
PY
```

`HTTP 200`; TLS verification and Bearer authentication passed; the response was `{"status":"ok"}`.

### 4.2 Fetching Alerts

We fetch once, up to 10, from the last 15 minutes. Bodies are not displayed; only the count and the results of the allowed-field check.

> **Run on: VM 230**

```bash
echo "===== VM230: POST-FIX LIVE ALERT RETRIEVAL ====="

python3 - <<'PY'
import json
import ssl
import urllib.request
import urllib.error
from pathlib import Path

BASE = "https://192.168.0.220:8765"
CREDENTIALS = Path("/etc/ai-defense-manager/credentials")
ALLOWED = {
    "timestamp",
    "rule.id",
    "rule.level",
    "rule.groups",
    "rule.description",
    "decoder.name",
    "agent.id",
}

token = (CREDENTIALS / "relay-api.token").read_text().strip()
ca_file = CREDENTIALS / "relay-ca.crt"

context = ssl.create_default_context(cafile=str(ca_file))
url = BASE + "/v1/alerts?limit=10&since_minutes=15"
request = urllib.request.Request(
    url,
    headers={"Authorization": "Bearer " + token},
    method="GET",
)

try:
    with urllib.request.urlopen(
        request, context=context, timeout=20
    ) as response:
        status = response.status
        raw = response.read(2 * 1024 * 1024 + 1)

    print("HTTP_STATUS =", status)
    print("TLS_VERIFICATION = PASS")
    print("RESPONSE_SIZE_WITHIN_LIMIT =", len(raw) <= 2 * 1024 * 1024)

    if len(raw) > 2 * 1024 * 1024:
        print("RESULT = RESPONSE_TOO_LARGE")
    else:
        payload = json.loads(raw.decode("utf-8"))
        print("JSON_VALID = PASS")

        candidates = []

        def inspect(value, path="$"):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == "alerts" and isinstance(child, list):
                        candidates.append((path + ".alerts", child))
                    else:
                        inspect(child, path + "." + str(key))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    if isinstance(child, dict):
                        inspect(child, path + "[" + str(index) + "]")

        inspect(payload)

        if not isinstance(payload, dict):
            print("RESPONSE_SHAPE = UNEXPECTED")
        else:
            print("TOP_LEVEL_KEYS =", sorted(payload.keys()))

        if len(candidates) == 1:
            path, events = candidates[0]
            print("ALERT_COUNT =", len(events))

            valid = 0
            invalid = 0
            for event in events:
                if not isinstance(event, dict):
                    invalid += 1
                    continue
                if set(event).issubset(ALLOWED):
                    valid += 1
                else:
                    invalid += 1

            print("ALLOWLIST_VALID_EVENTS =", valid)
            print("INVALID_EVENTS =", invalid)
            print("ALLOWLIST_VALIDATION =", "PASS" if invalid == 0 else "FAIL")
            print("EVENT_VALUES_DISPLAYED = NO")
        else:
            print("ALERT_LIST_COUNT =", len(candidates))
            print("RESPONSE_SHAPE = NEEDS_REVIEW")

except urllib.error.HTTPError as exc:
    print("HTTP_STATUS =", exc.code)
    print("REQUEST_RESULT = HTTP_ERROR")
except Exception as exc:
    print("REQUEST_RESULT = FAILED")
    print("ERROR_TYPE =", type(exc).__name__)

print("DATABASE_WRITES = NO")
print("OLLAMA_REQUESTED = NO")
print("AI_ANALYSIS_REQUESTED = NO")
PY
```

| Checked | Result |
|---|---|
| HTTPS, TLS verification | passed |
| Bearer authentication | passed |
| HTTP response | `200` |
| JSON shape | passed |
| Alerts fetched | 1 |
| Allowed-field check | 1 passed |
| Invalid events | 0 |
| Removal of `full_log` etc. | maintained |
| DB writes, Ollama inference | none |

## Closing Notes

In Part 52, VM 230 became able to receive real Wazuh alerts with only the allowed fields.

| Item | Result |
|---|---|
| Cause of the 502 | `relay.py` lacked `import re`, so `sanitize_alert()` raised `NameError` |
| Fix | added the one line `import re`; made a copy, tested the syntax and the masking step, and restarted the Relay |
| Indexer permissions | unchanged (`ai-defense-reader` can search; cluster permissions remain empty) |
| Fetching alerts | `HTTP 200`, 1 alert, passed the allowlist check |

The path is Wazuh Indexer (VM 220 `127.0.0.1:9200`) → Relay (VM 220 `:8765`, narrowed to seven fields) → AI Defense Manager (VM 230 `:8000`). In the next part, Part 53, we check how received alerts lead to analysis, storage and defense proposals inside VM 230.

# Part 53: Checking the Flow from Analysis to Storage
## Introduction

### About This Book

This is Part 53 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 52, VM 230 became able to receive real Wazuh alerts. Before moving on to LLM analysis, we check, read-only, how received alerts lead to analysis, storage and defense proposals inside VM 230.

1. Trace the processing from event conversion to AI analysis
2. Check the path from the API to storage and defensive action proposals, external exposure and DB permissions
3. Check systemd isolation settings
4. Test the masking step with synthetic data
5. Check the safety of where LLM output is stored and returned

No refetching of real alerts, no DB access, no Ollama inference, no configuration changes and no service restarts.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

## Chapter 1: The Processing Flow

### 1.1 Functions and Call Relationships

> **Run on: VM 230**

```bash
echo "===== VM230: EVENT PIPELINE STATIC AUDIT ====="

cd /opt/ai-defense-manager

python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")
targets = [
    "services/wazuh_relay.py",
    "services/event_sanitizer.py",
    "services/event_service.py",
    "services/ai_analysis.py",
    "schemas/security_event.py",
    "schemas/action.py",
]

keywords = (
    "alert", "event", "sanitize", "normal", "valid", "analy",
    "process", "save", "insert", "persist", "transform",
    "schema", "model", "proposal", "action"
)

for relative in targets:
    path = root / relative
    print(f"\n--- {relative} ---")
    if not path.is_file():
        print("FILE=NOT_FOUND")
        continue

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print("AST_PARSE=FAILED", type(exc).__name__)
        continue

    print("AST_PARSE=PASS")

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [arg.arg for arg in node.args.args]
            print(
                f"FUNCTION line={node.lineno} "
                f"name={node.name} args={args}"
            )
        elif isinstance(node, ast.ClassDef):
            print(f"CLASS line={node.lineno} name={node.name}")
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [arg.arg for arg in child.args.args]
                    print(
                        f"  METHOD line={child.lineno} "
                        f"name={child.name} args={args}"
                    )

    print("RELEVANT_CALLS:")
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            else:
                continue
            if any(word in name.lower() for word in keywords):
                print(f"  line={node.lineno} call={name}")

print("\n--- Service and schema file inventory ---")
for folder in (root / "services", root / "schemas"):
    if folder.is_dir():
        print(f"[{folder.name}]")
        for path in sorted(folder.glob("*.py")):
            print(path.name)

print("\nSOURCE_MODIFIED=NO")
print("DATABASE_REQUESTED=NO")
print("OLLAMA_REQUESTED=NO")
print("LIVE_ALERTS_REQUESTED=NO")
PY
```

There was no separate `event_service.py`; processing happened mainly in two stages.

1. `_convert_alert()` in `wazuh_relay.py` converts received alerts into `SecurityEvent`
2. `analyze_events()` in `ai_analysis.py` builds the content used for analysis and validates the model's output against the schema

### 1.2 Reading the Implementation

> **Run on: VM 230**

```bash
echo "===== VM230: EVENT PIPELINE IMPLEMENTATION REVIEW ====="

cd /opt/ai-defense-manager

echo
echo "--- Wazuh Relay: conversion and fetch ---"
nl -ba app/services/wazuh_relay.py | sed -n '1,190p'

echo
echo "--- Event sanitizer ---"
nl -ba app/services/event_sanitizer.py | sed -n '1,180p'

echo
echo "--- AI analysis: payload and analysis flow ---"
nl -ba app/services/ai_analysis.py | sed -n '1,190p'

echo
echo "--- Security event schema ---"
nl -ba app/schemas/security_event.py | sed -n '1,150p'

echo
echo "--- Analysis schema ---"
nl -ba app/schemas/analysis.py | sed -n '1,200p'

echo
echo "--- Analysis proposal schema ---"
nl -ba app/schemas/analysis_proposal.py | sed -n '1,200p'

echo
echo "--- Analysis history service ---"
nl -ba app/services/analysis_history.py | sed -n '1,200p'

echo
echo "SOURCE_MODIFIED=NO"
echo "DATABASE_REQUESTED=NO"
echo "OLLAMA_REQUESTED=NO"
echo "LIVE_ALERTS_REQUESTED=NO"
```

- `SecurityEvent` is built from Wazuh's seven fields; fields not allowed are rejected by `extra="forbid"`
- What is passed to the AI is only six explicitly chosen fields
- Event summaries are masked before being sent to the AI and before being stored in history
- AI proposals are validated with Pydantic, including that the evidence event IDs are among the inputs
- A proposal for temporary blocking requires a global IP, a TTL of 1–900 seconds and two separate pieces of evidence

## Chapter 2: APIs, Storage and Exposure

### 2.1 From the API to Analysis and Storage

> **Run on: VM 230**

```bash
echo "===== VM230: API TO ANALYSIS AND ACTION FLOW AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- API/router file inventory ---"
find app -maxdepth 4 -type f -name '*.py' -print | sort

echo
echo "--- Route decorators and relevant service calls ---"
python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")
keywords = (
    "fetch_wazuh_events",
    "analyze_events",
    "save_analysis",
    "initialize_database",
    "action",
    "approval",
    "execute",
    "gateway",
    "rollback",
)

for path in sorted(root.rglob("*.py")):
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception:
        continue

    matches = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            calls = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    func = child.func
                    name = (
                        func.id if isinstance(func, ast.Name)
                        else func.attr if isinstance(func, ast.Attribute)
                        else ""
                    )
                    if any(k in name.lower() for k in keywords):
                        calls.append(name)
            decorators = []
            for dec in node.decorator_list:
                try:
                    decorators.append(ast.unparse(dec))
                except Exception:
                    pass
            if calls or decorators:
                matches.append((
                    node.lineno, node.name, decorators, sorted(set(calls))
                ))

    if matches:
        print(f"\n--- {path.relative_to(root)} ---")
        for line, name, decorators, calls in matches:
            print(f"line={line} function={name}")
            for dec in decorators:
                print(f"  ROUTE_OR_DECORATOR={dec}")
            if calls:
                print(f"  RELEVANT_CALLS={calls}")

print("\nSOURCE_MODIFIED=NO")
print("DATABASE_REQUESTED=NO")
print("OLLAMA_REQUESTED=NO")
print("LIVE_ALERTS_REQUESTED=NO")
PY

echo
echo "--- Analysis history: remaining save logic ---"
nl -ba app/services/analysis_history.py | sed -n '185,360p'

echo
echo "--- Main application entrypoint ---"
if [ -f app/main.py ]; then
    nl -ba app/main.py | sed -n '1,240p'
else
    echo "app/main.py not found"
fi

echo
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

| API | Processing |
|---|---|
| `/api/v1/wazuh/events` | only fetches Wazuh events |
| `/api/v1/wazuh/analyze` | passes fetched events to AI analysis |
| `/api/v1/analysis` | analyzes received events directly with the AI |

The DB is initialized when the application starts. `save_analysis()` stores the analysis results, evidence, action proposals, approval records and audit logs.

### 2.2 Routes and the Boundary of Action Execution

> **Run on: VM 230**

```bash
echo "===== VM230: API ROUTE AND ACTION EXECUTION BOUNDARY AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- Wazuh API routes ---"
nl -ba app/api/wazuh.py | sed -n '1,240p'

echo
echo "--- Analysis API routes ---"
nl -ba app/api/analysis.py | sed -n '1,240p'

echo
echo "--- Action schema ---"
nl -ba app/schemas/action.py | sed -n '1,180p'

echo
echo "--- All references to history persistence ---"
grep -RInE 'save_analysis|initialize_database' app \
  --include='*.py' || true

echo
echo "--- Action execution / gateway references ---"
grep -RInEi 'execute_action|action_gateway|firewall|iptables|nft|block_ip|rollback|approve|approval' app \
  --include='*.py' || true

echo
echo "--- API route registration and middleware ---"
grep -RInE 'include_router|add_middleware|Depends\(|APIKey|HTTPBearer|OAuth2|CORSMiddleware' app \
  --include='*.py' || true

echo
echo "SOURCE_MODIFIED=NO"
echo "DATABASE_REQUESTED=NO"
echo "OLLAMA_REQUESTED=NO"
echo "LIVE_ALERTS_REQUESTED=NO"
```

Both analysis APIs called `save_analysis()`. On the other hand, we found the following two things.

1. **API authentication**: FastAPI routes have no authentication dependencies or middleware
2. **Action execution**: it goes only as far as recording approval state in the DB; there is no Action Gateway, no approval API and no firewall operation

### 2.3 External Exposure and DB Permissions

> **Run on: VM 230**

```bash
echo "===== VM230: API EXPOSURE AND DATABASE PERMISSION AUDIT ====="

echo
echo "--- API listener ---"
ss -lntp '( sport = :8000 )'

echo
echo "--- AI Defense Manager process ---"
systemctl show ai-defense-manager.service \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p User \
  -p Group

PID="$(systemctl show ai-defense-manager.service -p MainPID --value)"

if [ -n "$PID" ] && [ "$PID" != "0" ]; then
    echo
    echo "--- Process identity ---"
    ps -p "$PID" -o pid,ppid,user,group,stat,comm
fi

echo
echo "--- Database file metadata only ---"
if [ -e /opt/ai-defense-manager/data/ai-defense.db ]; then
    stat -c 'type=%F owner=%U:%G mode=%a size=%s' \
      /opt/ai-defense-manager/data/ai-defense.db
else
    echo "DATABASE_FILE=NOT_FOUND"
fi

if [ -d /opt/ai-defense-manager/data ]; then
    stat -c 'directory_owner=%U:%G directory_mode=%a' \
      /opt/ai-defense-manager/data
fi

echo
echo "DATABASE_CONTENT_READ=NO"
echo "DATABASE_MODIFIED=NO"
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
echo "OLLAMA_REQUESTED=NO"
```

| Item | Result |
|---|---|
| API listening | `127.0.0.1:8000` only (not exposed on the LAN) |
| Running as | dedicated user `ai-defense` |
| SQLite DB | `ai-defense:ai-defense`, `600` |
| DB directory | `750` |

The lack of API authentication remains. Even with localhost only, other processes on the same VM can access it, so authentication must be considered before integrating with other systems (done from Part 56 onward).

### 2.4 Approval State and Storage

> **Run on: VM 230**

```bash
echo "===== VM230: APPROVAL STATE AND PERSISTENCE CONSISTENCY AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- Analysis proposal schema ---"
nl -ba app/schemas/analysis_proposal.py | sed -n '1,180p'

echo
echo "--- Database schema and save logic ---"
nl -ba app/services/analysis_history.py | sed -n '1,245p'

echo
echo "--- Action schema references ---"
grep -RInE 'ActionProposal|ApprovalStatus|requires_human_approval|proposal_status|approval_decision' app \
  --include='*.py' || true

echo
echo "SOURCE_MODIFIED=NO"
echo "DATABASE_READ=NO"
echo "DATABASE_MODIFIED=NO"
echo "OLLAMA_REQUESTED=NO"
echo "LIVE_ALERTS_REQUESTED=NO"
```

Analysis results are stored inside a transaction, and there was no API for executing actions or firewall operation in the code.

## Chapter 3: Isolation by systemd

> **Run on: VM 230**

```bash
echo "===== VM230: SERVICE SANDBOX AND CONFIGURATION AUDIT ====="

echo
echo "--- Service security properties ---"
systemctl show ai-defense-manager.service \
  -p User -p Group -p NoNewPrivileges \
  -p PrivateTmp -p PrivateDevices \
  -p ProtectSystem -p ProtectHome \
  -p ReadWritePaths -p ReadOnlyPaths \
  -p RestrictAddressFamilies \
  -p CapabilityBoundingSet \
  -p AmbientCapabilities \
  -p SystemCallFilter \
  -p ProtectKernelTunables \
  -p ProtectKernelModules \
  -p ProtectControlGroups

echo
echo "--- Unit file (environment values redacted) ---"
UNIT="$(systemctl show ai-defense-manager.service -p FragmentPath --value)"
if [ -n "$UNIT" ] && [ -f "$UNIT" ]; then
    sed -E \
      -e '/^[[:space:]]*Environment=/s/=.*/=<REDACTED>/' \
      -e '/^[[:space:]]*EnvironmentFile=/s/=.*/=<REDACTED>/' \
      "$UNIT"
else
    echo "UNIT_FILE_NOT_FOUND"
fi

echo
echo "--- Configuration declarations (values redacted) ---"
grep -nE '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*:' \
  /opt/ai-defense-manager/app/core/config.py |
  sed -E 's/(:|=).*/\1 <VALUE_REDACTED>/'

echo
echo "--- Sensitive output guard ---"
echo "CREDENTIAL_VALUES=NOT_DISPLAYED"
echo "ENVIRONMENT_VALUES=NOT_DISPLAYED"
echo "CONFIGURATION_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "DATABASE_READ=NO"
echo "OLLAMA_REQUESTED=NO"
```

| Setting | State |
|---|---|
| `ProtectSystem=strict`, `ProtectHome=yes` | present |
| Writable locations | only the DB's `/opt/ai-defense-manager/data` |
| Linux capabilities | empty |
| `NoNewPrivileges=yes` | present |
| `PrivateTmp`, `PrivateDevices`, `ProtectProc=invisible` | present |
| Memory and task limits | 1GiB, 64 |
| `RestrictAddressFamilies` | `AF_INET` (IPv4 only) |

The AI Defense Manager has no root privileges and no network administration capability. With only `AF_INET`, IPv6 sockets cannot be used, but the current connections to the Relay and Ollama are IPv4.

## Chapter 4: Testing the Masking Step

### 4.1 Checking Input and Output Safety

> **Run on: VM 230**

```bash
echo "===== VM230: LLM OUTPUT AND DATA FLOW SAFETY AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- AI analysis service ---"
nl -ba app/services/ai_analysis.py | sed -n '1,300p'

echo
echo "--- Event sanitizer ---"
nl -ba app/services/event_sanitizer.py | sed -n '1,240p'

echo
echo "--- Analysis request schema ---"
nl -ba app/schemas/analysis.py | sed -n '1,220p'

echo
echo "--- Security event schema ---"
nl -ba app/schemas/security_event.py | sed -n '1,220p'

echo
echo "--- Sanitizer call sites ---"
grep -RInE 'sanitize_event_summary|sanitize.*summary|sanitize.*reasoning|sanitize.*proposal' \
  app --include='*.py' || true

echo
echo "SOURCE_MODIFIED=NO"
echo "DATABASE_READ=NO"
echo "DATABASE_MODIFIED=NO"
echo "OLLAMA_REQUESTED=NO"
echo "LIVE_ALERTS_REQUESTED=NO"
```

The event input side was as follows.

- Event summaries are masked before being sent to the LLM (Bearer tokens, common secrets, email addresses, IP addresses)
- What is passed to the LLM is built from an allowlist
- IPs and agent names of Wazuh events are not sent to the LLM
- The LLM's answer is validated with JSON Schema and Pydantic

On the other hand, we found that the LLM output side needs measures (Chapter 5).

### 4.2 Model and Settings

> **Run on: VM 230**

```bash
echo "===== VM230: SANITIZER AND MODEL CONFIGURATION STATIC AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- Configuration source (secret values masked) ---"
sed -E \
  -e 's/(password|token|secret|api[_-]?key)([[:space:]]*:[[:space:]]*).*/\1\2<REDACTED>/I' \
  -e 's/(password|token|secret|api[_-]?key)([[:space:]]*=[[:space:]]*).*/\1\2<REDACTED>/I' \
  app/core/config.py

echo
echo "--- Model and Ollama configuration references ---"
grep -RInE 'MODEL_NAME|ollama_base_url|analysis_timeout_seconds|OLLAMA_MODEL|qwen3:8b' \
  app /etc/systemd/system/ai-defense-manager.service \
  --include='*.py' --include='*.service' 2>/dev/null |
  sed -E 's/(token|password|secret|api[_-]?key)([^,; ]*)/REDACTED/Ig'

echo
echo "--- Existing sanitizer tests ---"
find . -maxdepth 4 -type f \
  \( -iname '*sanitiz*test*.py' -o -iname 'test*sanitiz*.py' \) \
  -print

echo
echo "--- Test framework configuration ---"
grep -nE 'pytest|testpaths|python_files|ruff|mypy' \
  pyproject.toml pytest.ini setup.cfg tox.ini 2>/dev/null || true

echo
echo "SOURCE_MODIFIED=NO"
echo "TESTS_EXECUTED=NO"
echo "DATABASE_READ=NO"
echo "OLLAMA_REQUESTED=NO"
```

The model name is written in `ai_analysis.py` as `qwen3:8b`, and there was no setting for it in `config.py`. Ollama's endpoint is `192.168.0.180:11434`. We do not change these here.

### 4.3 Testing with Synthetic Data (14 Cases)

Without changing the production code, we test with synthetic data the masking of secrets, email and IPv4/IPv6, control characters, the 512-character limit, and that ordinary text remains.

> **Run on: VM 230**

```bash
echo "===== VM230: EVENT SANITIZER SYNTHETIC TEST ====="

cd /opt/ai-defense-manager

venv/bin/python - <<'PY'
from app.services.event_sanitizer import sanitize_event_summary

tests = [
    ("bearer_token", "Authorization Bearer abc.def-123"),
    ("password_assignment", "password=hunter2"),
    ("api_key_assignment", "api_key: secret-value"),
    ("aws_key", "AKIA1234567890ABCDEF"),
    ("github_key", "ghp_" + "A" * 30),
    ("openai_key", "sk-" + "B" * 30),
    ("email", "contact user@example.com"),
    ("ipv4", "connection from 203.0.113.10"),
    ("ipv6", "connection from 2001:db8::1"),
    ("control_chars", "alpha\x00beta\ncharlie"),
    ("length_limit", "A" * 600),
    ("empty_string", ""),
    ("non_string", None),
    ("normal_text", "Wazuh authentication failure detected"),
]

checks = {}

for name, value in tests:
    try:
        result = sanitize_event_summary(value)

        if name in {
            "bearer_token", "password_assignment", "api_key_assignment",
            "aws_key", "github_key", "openai_key"
        }:
            passed = "[REDACTED_SECRET]" in result

        elif name == "email":
            passed = "[REDACTED_EMAIL]" in result

        elif name in {"ipv4", "ipv6"}:
            passed = "[REDACTED_IP]" in result

        elif name == "control_chars":
            passed = "\x00" not in result and "\n" not in result

        elif name == "length_limit":
            passed = len(result) <= 512

        elif name in {"empty_string", "non_string"}:
            passed = result == "[REDACTED_EVENT]"

        elif name == "normal_text":
            passed = result == value

        else:
            passed = False

        checks[name] = passed
        print(f"{name}={'PASS' if passed else 'FAIL'}")

    except Exception as exc:
        checks[name] = False
        print(f"{name}=ERROR ({type(exc).__name__})")

print()
print(f"TESTS_TOTAL={len(checks)}")
print(f"TESTS_PASSED={sum(checks.values())}")
print(f"TESTS_FAILED={len(checks) - sum(checks.values())}")
print("TEST_INPUT_VALUES_DISPLAYED=NO")
print("DATABASE_ACCESSED=NO")
print("OLLAMA_ACCESSED=NO")
PY

echo
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

All 14 passed.

### 4.4 Do the Original Values Remain? (10 Cases)

> **Run on: VM 230**

```bash
echo "===== VM230: SANITIZER REDACTION COMPLETENESS TEST ====="

cd /opt/ai-defense-manager

venv/bin/python - <<'PY'
from app.services.event_sanitizer import sanitize_event_summary

cases = [
    ("bearer", "Bearer abc.def-123", "abc.def-123"),
    ("password", "password=hunter2", "hunter2"),
    ("quoted_secret", 'secret: "quoted-secret-value"', "quoted-secret-value"),
    ("api_key", "api_key=synthetic-api-key-123", "synthetic-api-key-123"),
    ("aws_key", "AKIA1234567890ABCDEF", "AKIA1234567890ABCDEF"),
    ("github_key", "ghp_" + "A" * 30, "ghp_" + "A" * 30),
    ("openai_key", "sk-" + "B" * 30, "sk-" + "B" * 30),
    ("email", "user@example.com", "user@example.com"),
    ("ipv4", "203.0.113.10", "203.0.113.10"),
    ("ipv6", "2001:db8::1", "2001:db8::1"),
]

failed = []

for name, source, secret in cases:
    result = sanitize_event_summary(source)
    marker = (
        "[REDACTED_SECRET]" if name in {
            "bearer", "password", "quoted_secret", "api_key",
            "aws_key", "github_key", "openai_key"
        }
        else "[REDACTED_EMAIL]" if name == "email"
        else "[REDACTED_IP]"
    )

    marker_present = marker in result
    original_absent = secret not in result
    passed = marker_present and original_absent

    print(
        f"{name}={'PASS' if passed else 'FAIL'} "
        f"marker={marker_present} original_absent={original_absent}"
    )

    if not passed:
        failed.append(name)

print()
print(f"TESTS_TOTAL={len(cases)}")
print(f"TESTS_FAILED={len(failed)}")
print(f"FAILED_CASE_NAMES={failed}")
print("SECRET_VALUES_DISPLAYED=NO")
print("DATABASE_ACCESSED=NO")
print("OLLAMA_ACCESSED=NO")
PY

echo
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

All 10 passed; we confirmed that mask markers appear and the original secrets do not remain. It only works on known patterns, so it cannot necessarily remove secrets in unknown forms.

## Chapter 5: Checking the LLM Output

### 5.1 Processing Just Before Storage

> **Run on: VM 230**

```bash
echo "===== VM230: LLM OUTPUT TRUST-BOUNDARY AUDIT ====="

cd /opt/ai-defense-manager

venv/bin/python - <<'PY'
import ast
from pathlib import Path

targets = {
    "app/services/ai_analysis.py": {
        "analyze_events",
        "_build_event_payload",
    },
    "app/services/analysis_history.py": {
        "save_analysis",
    },
    "app/schemas/analysis_proposal.py": {
        "AIAnalysisProposal",
        "validate_action_constraints",
    },
}

for filename, wanted in targets.items():
    path = Path(filename)
    print(f"\n--- {filename} ---")

    if not path.is_file():
        print("FILE_NOT_FOUND")
        continue

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    found = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in wanted:
                found.add(node.name)
                print(f"\n### {node.name} (line {node.lineno})")
                print(ast.get_source_segment(source, node))

    missing = wanted - found
    if missing:
        print("NOT_FOUND:", sorted(missing))

print("\n--- OUTPUT SANITIZER REFERENCES ---")
for filename in [
    "app/services/ai_analysis.py",
    "app/services/analysis_history.py",
    "app/routers/analysis.py",
]:
    path = Path(filename)
    if not path.is_file():
        continue

    for number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if any(word in line.lower() for word in (
            "sanitize", "model_validate", "model_dump",
            "summary", "reasoning", "save_analysis"
        )):
            print(f"{filename}:{number}: {line.strip()[:240]}")

PY

echo
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

Two problems were found.

1. **LLM output is stored as is**: `proposal.summary` and `proposal.reasoning` are stored in SQLite without masking, even if they contain secrets
2. **The LLM can decide whether approval is required**: for proposals other than IP blocking, `requires_human_approval=false` passes, and the storage step uses that value

There is currently neither an Action Gateway nor an execution function, so this does not immediately lead to firewall operations.

### 5.2 API Return Values and Approval

> **Run on: VM 230**

```bash
echo "===== VM230: API RESPONSE AND APPROVAL FLOW AUDIT ====="

cd /opt/ai-defense-manager

venv/bin/python - <<'PY'
import ast
from pathlib import Path

root = Path("app")

for path in sorted((root / "routers").glob("*.py")):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    print(f"\n--- {path} ---")

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            segment = ast.get_source_segment(source, node) or ""
            if any(term in segment.lower() for term in (
                "analyze_events",
                "save_analysis",
                "proposal",
                "approval",
                "analysis_history",
                "summary",
                "reasoning",
            )):
                print(f"\n### {node.name} (line {node.lineno})")
                print(segment)

print("\n--- ROUTE AND APPROVAL REFERENCES ---")

for path in sorted(root.rglob("*.py")):
    if "__pycache__" in str(path):
        continue

    for number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        lower = line.lower()
        if any(term in lower for term in (
            "include_router",
            "approval",
            "action_proposals",
            "analysis_runs",
            "get_analysis",
            "list_analysis",
        )):
            print(f"{path}:{number}: {line.strip()[:220]}")

PY

echo
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

```bash
echo "===== VM230: ROUTER FILE AND ENDPOINT INVENTORY ====="

cd /opt/ai-defense-manager

echo
echo "--- Router-related files ---"
find app -maxdepth 4 -type f \
  \( -name '*router*.py' -o -name '*route*.py' -o -name 'api.py' \) \
  -print | sort

echo
echo "--- Router registrations ---"
sed -n '1,180p' app/main.py

echo
echo "--- FastAPI endpoint decorators and handler definitions ---"
grep -RInE \
  '^[[:space:]]*@.*\.(get|post|put|patch|delete)|^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+' \
  app/routers app/api app 2>/dev/null \
  | grep -v '__pycache__' \
  | head -200

echo
echo "--- Router directory listing ---"
ls -la app/routers app/api 2>/dev/null

echo
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

The routers were actually in `app/api/analysis.py` and `app/api/wazuh.py`.

### 5.3 Handler Bodies

> **Run on: VM 230**

```bash
echo "===== VM230: ANALYSIS API HANDLER AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- app/api/analysis.py ---"
nl -ba app/api/analysis.py

echo
echo "--- app/api/wazuh.py ---"
nl -ba app/api/wazuh.py

echo
echo "--- API route configuration ---"
grep -RInE \
  'APIRouter|prefix=|response_model=|status_code=|dependencies=|include_in_schema' \
  app/api app/main.py

echo
echo "--- Authentication and authorization references ---"
grep -RInE \
  'HTTPBearer|OAuth2|APIKey|Depends\(|Security\(|authenticate|authorize|middleware|permission' \
  app --include='*.py' \
  | grep -v '__pycache__' || true

echo
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

- `/api/v1/analysis`: stores the LLM's proposal and then returns it as is
- `/api/v1/wazuh/analyze`: fetches Wazuh events, analyzes them with the LLM, stores, and returns the same proposal
- Both have `response_model=AIAnalysisProposal`, but that schema only checks lengths and types and does not remove secrets

So the proposal must be masked **right after receiving the LLM's answer**, not just right before storage.

### 5.4 Checks to Decide the Fix

> **Run on: VM 230**

```bash
echo "===== VM230: SANITIZER AND ACTION POLICY DESIGN AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- Existing sanitizer ---"
nl -ba app/services/event_sanitizer.py

echo
echo "--- Recommended action definitions ---"
nl -ba app/schemas/analysis_proposal.py

echo
echo "--- Action schema and validation ---"
nl -ba app/schemas/action.py

echo
echo "--- Sanitizer usage throughout application ---"
grep -RInE \
  'sanitize_event_summary|RecommendedAction|requires_human_approval' \
  app --include='*.py' \
  | grep -v '__pycache__'

echo
echo "--- Test tooling inventory ---"
find . -maxdepth 3 -type f \
  \( -name 'pytest.ini' -o -name 'pyproject.toml' \
     -o -name 'conftest.py' -o -name 'test_*.py' \
     -o -name '*_test.py' \) \
  -print | sort

echo
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "SOURCE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Problem | Details |
|---|---|
| Masking of LLM output | `summary` (up to 2,000 characters) and `reasoning` (up to 4,000 characters) are stored and returned unmasked. The current masking is for event input and truncates to 512 characters, so it cannot be used as is |
| Whether approval is required | the LLM can return `requires_human_approval=false` |

With the policy that the LLM is limited to analysis and the AI Defense Manager side guarantees output safety and approval decisions, we fix this in the next part, Part 54.

## Closing Notes

In Part 53 we checked the flow from analysis to storage inside VM 230.

| Item | Result |
|---|---|
| Input | narrowed to seven fields, unknown fields rejected; summaries masked; six fields sent to the AI |
| Exposure | `127.0.0.1:8000` only; DB is `600` |
| Isolation | systemd restricts writable locations, capabilities, memory and more |
| Masking tests | all 14 and 10 cases passed |
| Problems found | LLM output stored and returned unmasked; the LLM can decide whether approval is required; the API has no authentication |
| Action execution | no such function (only storing proposals) |

In the next part, Part 54, we fix the masking of LLM output and the approval policy.

# Part 54: Masking LLM Output and the Approval Policy
## Introduction

### About This Book

This is Part 54 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". The checks in Part 53 showed that LLM output (`summary`, `reasoning`) is stored and returned without masking, and that the LLM can decide whether approval is required. Here we fix these as follows.

| Target | Fix |
|---|---|
| Event input | keep the current masking (512 characters) |
| LLM `summary`, `reasoning` | remove secrets and personal information through a dedicated entry point, limited to 2,000 and 4,000 characters |
| API return values, storage in SQLite | only masked proposals |
| Whether approval is required | decided on the server side; everything other than `no_action` requires human approval |
| Temporary IP blocking | always requires human approval; TTL at most 900 seconds |
| Wazuh event retrieval API | the returned summaries and descriptions are also masked |

The LLM is limited to analysis, and the AI Defense Manager side guarantees output safety and approval decisions. The Action Gateway (actual execution of actions) is not built yet.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

## Chapter 1: Saving Copies Before the Change

We save copies of the four target files and record syntax, owner, permissions and hashes. The sources, DB and services are not touched.

> **Run on: VM 230**

```bash
echo "===== VM230: PRE-CHANGE BACKUP AND INTEGRITY CHECK ====="

cd /opt/ai-defense-manager

BACKUP_DIR="/var/backups/ai-defense-manager/llm-output-policy-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

FILES=(
  app/services/event_sanitizer.py
  app/services/ai_analysis.py
  app/services/analysis_history.py
  app/schemas/analysis_proposal.py
)

echo
echo "--- Source metadata and hashes ---"
for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    stat -c 'FILE=%n OWNER=%U:%G MODE=%a SIZE=%s' "$file"
    sha256sum "$file"
  else
    echo "MISSING=$file"
  fi
done

echo
echo "--- Creating metadata-preserving backups ---"
for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    mkdir -p "$BACKUP_DIR/$(dirname "$file")"
    cp -a "$file" "$BACKUP_DIR/$file"
  fi
done

echo
echo "--- Backup integrity verification ---"
for file in "${FILES[@]}"; do
  if [ -f "$file" ] && [ -f "$BACKUP_DIR/$file" ]; then
    ORIGINAL_HASH="$(sha256sum "$file" | awk '{print $1}')"
    BACKUP_HASH="$(sha256sum "$BACKUP_DIR/$file" | awk '{print $1}')"
    if [ "$ORIGINAL_HASH" = "$BACKUP_HASH" ]; then
      echo "BACKUP=PASS FILE=$file"
    else
      echo "BACKUP=FAIL FILE=$file"
    fi
  else
    echo "BACKUP=FAIL FILE=$file"
  fi
done

echo
echo "--- Backup directory ---"
printf '%s\n' "$BACKUP_DIR"
stat -c 'OWNER=%U:%G MODE=%a' "$BACKUP_DIR"

echo
echo "--- Test tooling ---"
if [ -x venv/bin/pytest ]; then
  echo "PYTEST=AVAILABLE"
else
  echo "PYTEST=NOT_FOUND"
fi

echo
echo "SOURCE_MODIFIED=NO"
echo "DATABASE_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

The copies of all four files matched, and the original owners and permissions were recorded.

## Chapter 2: Adding LLM Output Masking and the Approval Policy

### 2.1 Rewriting the Four Files

Keeping the 512-character limit of the event masking, we add dedicated entry points for LLM output with 2,000 and 4,000 characters. We do not trust the LLM's value for whether approval is required; everything other than `no_action` always requires approval on the server side, and the same rule is applied again when storing in the DB.

> **Run on: VM 230**

```bash
echo "===== VM230: APPLY LLM OUTPUT SANITIZATION AND APPROVAL POLICY ====="

cd /opt/ai-defense-manager

venv/bin/python - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager")
backup = Path("/var/backups/ai-defense-manager/llm-output-policy-20261123-141801")

files = [
    "app/services/event_sanitizer.py",
    "app/services/ai_analysis.py",
    "app/services/analysis_history.py",
    "app/schemas/analysis_proposal.py",
]

for rel in files:
    if not (root / rel).is_file() or not (backup / rel).is_file():
        raise RuntimeError(f"Source or verified backup missing: {rel}")

changes = {}

# 1. Preserve the existing redaction expressions and add length-specific entry points.
rel = "app/services/event_sanitizer.py"
s = (root / rel).read_text(encoding="utf-8")

old = "def sanitize_event_summary(value: str) -> str:"
new = "def _sanitize_text(value: str, max_length: int) -> str:"
if s.count(old) != 1:
    raise RuntimeError("Sanitizer function definition mismatch")
s = s.replace(old, new)

old = "return value[:512] if value.strip() else \"[REDACTED_EVENT]\""
new = "return value[:max_length] if value.strip() else \"[REDACTED_EVENT]\""
if s.count(old) != 1:
    raise RuntimeError("Sanitizer length limit expression mismatch")
s = s.replace(old, new)

s += '''

def sanitize_event_summary(value: str) -> str:
    """Sanitize event summaries using the established 512-character limit."""
    return _sanitize_text(value, 512)


def sanitize_analysis_text(value: str, max_length: int) -> str:
    """Sanitize untrusted LLM text with a caller-defined field limit."""
    if (
        not isinstance(max_length, int)
        or isinstance(max_length, bool)
        or max_length < 1
    ):
        raise ValueError("max_length must be a positive integer")
    return _sanitize_text(value, max_length)
'''
changes[rel] = s

# 2. Sanitize LLM output and override its approval flag before API return.
rel = "app/services/ai_analysis.py"
s = (root / rel).read_text(encoding="utf-8")

old = "from app.services.event_sanitizer import sanitize_event_summary"
new = (
    "from app.services.event_sanitizer import "
    "sanitize_analysis_text, sanitize_event_summary"
)
if s.count(old) != 1:
    raise RuntimeError("AI analysis sanitizer import mismatch")
s = s.replace(old, new)

old = "        return proposal\n"
new = '''        # Server policy is authoritative; the model cannot waive approval.
        return proposal.model_copy(
            update={
                "summary": sanitize_analysis_text(proposal.summary, 2000),
                "reasoning": sanitize_analysis_text(proposal.reasoning, 4000),
                "requires_human_approval": (
                    proposal.recommended_action.value != "no_action"
                ),
            }
        )
'''
if s.count(old) != 1:
    raise RuntimeError("AI analysis return point mismatch")
s = s.replace(old, new)
changes[rel] = s

# 3. Reapply sanitization and approval policy at the persistence boundary.
rel = "app/services/analysis_history.py"
s = (root / rel).read_text(encoding="utf-8")

old = "from app.services.event_sanitizer import sanitize_event_summary"
new = (
    "from app.services.event_sanitizer import "
    "sanitize_analysis_text, sanitize_event_summary"
)
if s.count(old) != 1:
    raise RuntimeError("Analysis history sanitizer import mismatch")
s = s.replace(old, new)

old = '''    action_requires_approval = (
        proposal.requires_human_approval
        and proposal.recommended_action.value != "no_action"
    )
'''
new = '''    # Never trust the LLM's approval flag when persisting policy state.
    action_requires_approval = proposal.recommended_action.value != "no_action"
    safe_summary = sanitize_analysis_text(proposal.summary, 2000)
    safe_reasoning = sanitize_analysis_text(proposal.reasoning, 4000)
'''
if s.count(old) != 1:
    raise RuntimeError("Analysis history approval policy mismatch")
s = s.replace(old, new)

for old, new in (
    ("                proposal.summary,", "                safe_summary,"),
    ("                proposal.reasoning,", "                safe_reasoning,"),
    (
        "                int(proposal.requires_human_approval),",
        "                int(action_requires_approval),",
    ),
):
    if s.count(old) != 1:
        raise RuntimeError(f"Analysis history SQL value mismatch: {old.strip()}")
    s = s.replace(old, new)

changes[rel] = s

# 4. Document that the model-provided flag is advisory only.
rel = "app/schemas/analysis_proposal.py"
s = (root / rel).read_text(encoding="utf-8")

old = "    requires_human_approval: bool = True\n"
new = '''    requires_human_approval: bool = Field(
        default=True,
        description=(
            "Advisory model field only. Server policy overrides this value: "
            "all actions except no_action require human approval."
        ),
    )
'''
if s.count(old) != 1:
    raise RuntimeError("Proposal schema approval field mismatch")
s = s.replace(old, new)
changes[rel] = s

# Validate all proposed contents before writing any file.
for rel, source in changes.items():
    ast.parse(source, filename=rel)
    print(f"PREWRITE_SYNTAX=PASS FILE={rel}")

# Write only after every replacement and syntax check has passed.
for rel, source in changes.items():
    (root / rel).write_text(source, encoding="utf-8")
    print(f"WRITE=PASS FILE={rel}")

print("ALL_FOUR_FILES_UPDATED=YES")
PY

echo
echo "--- Post-edit syntax compilation ---"
venv/bin/python -m compileall -q \
  app/services/event_sanitizer.py \
  app/services/ai_analysis.py \
  app/services/analysis_history.py \
  app/schemas/analysis_proposal.py

echo "COMPILEALL_EXIT=$?"

echo
echo "--- File ownership, modes and hashes ---"
stat -c 'FILE=%n OWNER=%U:%G MODE=%a SIZE=%s' \
  app/services/event_sanitizer.py \
  app/services/ai_analysis.py \
  app/services/analysis_history.py \
  app/schemas/analysis_proposal.py

sha256sum \
  app/services/event_sanitizer.py \
  app/services/ai_analysis.py \
  app/services/analysis_history.py \
  app/schemas/analysis_proposal.py

echo
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

Writing the four files and the Python syntax check succeeded, and the owners and permissions were unchanged.

### 2.2 Functional Tests (10 Cases)

We do not connect to the real DB; we check with a fake DB for testing.

> **Run on: VM 230**

```bash
echo "===== VM230: LLM OUTPUT AND APPROVAL POLICY TEST ====="

cd /opt/ai-defense-manager

venv/bin/python - <<'PY'
import ast
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from app.services.event_sanitizer import (
    sanitize_analysis_text,
    sanitize_event_summary,
)
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import (
    AIAnalysisProposal,
    RecommendedAction,
)
from app.services import analysis_history

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    print(f"{name}={'PASS' if condition else 'FAIL'}")
    if condition:
        passed += 1
    else:
        failed += 1

# 1. Preserve the established event sanitizer behavior.
event_text = sanitize_event_summary("A" * 600)
check("EVENT_LIMIT_512", len(event_text) == 512)

# 2. LLM output redaction and independent field limits.
summary = sanitize_analysis_text(
    "password=synthetic-secret user@example.com 203.0.113.10",
    2000,
)
reasoning = sanitize_analysis_text(
    "Bearer synthetic.token.value " + ("R" * 5000),
    4000,
)
check(
    "LLM_SUMMARY_REDACTION",
    "synthetic-secret" not in summary
    and "user@example.com" not in summary
    and "203.0.113.10" not in summary,
)
check(
    "LLM_REASONING_REDACTION",
    "synthetic.token.value" not in reasoning
    and "Bearer [REDACTED_SECRET]" in reasoning,
)
check("LLM_SUMMARY_LIMIT", len(sanitize_analysis_text("S" * 3000, 2000)) == 2000)
check("LLM_REASONING_LIMIT", len(reasoning) == 4000)

# 3. Schema permits advisory false for a non-block action;
# server-side persistence must override it.
event_id = uuid4()
request = AIAnalysisRequest(
    events=[{
        "source": "wazuh",
        "observed_at": "2026-11-23T12:00:00Z",
        "severity": "high",
        "rule_id": "5710",
        "event_category": "authentication",
        "event_summary": "Authentication failure",
    }]
)
event_id = request.events[0].event_id

proposal = AIAnalysisProposal(
    summary="password=proposal-secret",
    severity="high",
    confidence=0.9,
    evidence_event_ids=[event_id],
    recommended_action=RecommendedAction.NOTIFY,
    requires_human_approval=False,
    reasoning="Bearer reasoning.secret.value",
)

captured = []

class FakeConnection:
    def execute(self, sql, params=()):
        captured.append((sql, params))
        return self

@contextmanager
def fake_connection():
    yield FakeConnection()

original_connection = analysis_history._connection
analysis_history._connection = fake_connection

try:
    run_id = analysis_history.save_analysis(request, proposal)
finally:
    analysis_history._connection = original_connection

analysis_insert = next(
    params for sql, params in captured if "INSERT INTO analysis_runs" in sql
)
proposal_insert = next(
    params for sql, params in captured if "INSERT INTO action_proposals" in sql
)
approval_insert = next(
    params for sql, params in captured if "INSERT INTO action_approvals" in sql
)

check("SAVE_ANALYSIS_RETURNS_RUN_ID", isinstance(run_id, str) and len(run_id) > 0)
check(
    "DB_SUMMARY_SANITIZED",
    "proposal-secret" not in analysis_insert[5],
)
check(
    "DB_REASONING_SANITIZED",
    "reasoning.secret.value" not in analysis_insert[7],
)
check(
    "DB_NON_NO_ACTION_APPROVAL_FORCED",
    proposal_insert[5] == 1
    and proposal_insert[6] == "pending"
    and approval_insert[2] == "pending",
)

# 4. Static check of the AI return-boundary override.
tree = ast.parse(
    Path("app/services/ai_analysis.py").read_text(encoding="utf-8")
)
source = Path("app/services/ai_analysis.py").read_text(encoding="utf-8")
analyze = next(
    n for n in ast.walk(tree)
    if isinstance(n, ast.AsyncFunctionDef) and n.name == "analyze_events"
)
segment = ast.get_source_segment(source, analyze)
check(
    "AI_RETURN_BOUNDARY_POLICY_PRESENT",
    "model_copy" in segment
    and 'proposal.recommended_action.value != "no_action"' in segment
    and "sanitize_analysis_text(proposal.summary, 2000)" in segment
    and "sanitize_analysis_text(proposal.reasoning, 4000)" in segment,
)

print()
print(f"TESTS_PASSED={passed}")
print(f"TESTS_FAILED={failed}")
print("REAL_DATABASE_ACCESSED=NO")
print("OLLAMA_ACCESSED=NO")
print("LIVE_WAZUH_ACCESSED=NO")
PY

echo
echo "SERVICE_RESTARTED=NO"
echo "SOURCE_MODIFIED_BY_TEST=NO"
```

**All 10 passed.**

- The 512-character limit on event summaries is unchanged
- The LLM's `summary` and `reasoning` are limited to 2,000 and 4,000 characters, and secrets are masked
- For anything other than `no_action`, approval is required on the server side even if the LLM returns `requires_human_approval=false`
- The same approval rule and masking are applied when storing in SQLite

### 2.3 Edges of the Approval Policy (5 Cases)

> **Run on: VM 230**

```bash
echo "===== VM230: APPROVAL POLICY BOUNDARY TEST ====="

cd /opt/ai-defense-manager

venv/bin/python - <<'PY'
from contextlib import contextmanager
from uuid import uuid4

from pydantic import ValidationError

from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import (
    AIAnalysisProposal,
    RecommendedAction,
)
from app.services import analysis_history

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    print(f"{name}={'PASS' if condition else 'FAIL'}")
    if condition:
        passed += 1
    else:
        failed += 1

request = AIAnalysisRequest(events=[
    {
        "source": "wazuh",
        "observed_at": "2026-11-23T12:00:00Z",
        "severity": "high",
        "rule_id": "5710",
        "event_category": "authentication",
        "event_summary": "Synthetic event one",
    },
    {
        "source": "wazuh",
        "observed_at": "2026-11-23T12:01:00Z",
        "severity": "high",
        "rule_id": "5711",
        "event_category": "authentication",
        "event_summary": "Synthetic event two",
    },
])

captured = []

class FakeConnection:
    def execute(self, sql, params=()):
        captured.append((sql, params))
        return self

@contextmanager
def fake_connection():
    yield FakeConnection()

original_connection = analysis_history._connection
analysis_history._connection = fake_connection

try:
    no_action = AIAnalysisProposal(
        summary="No action required",
        severity="low",
        confidence=0.95,
        evidence_event_ids=[request.events[0].event_id],
        recommended_action=RecommendedAction("no_action"),
        requires_human_approval=True,
        reasoning="Synthetic no-action test",
    )

    captured.clear()
    analysis_history.save_analysis(request, no_action)

    proposal_row = next(
        p for s, p in captured if "INSERT INTO action_proposals" in s
    )
    approval_row = next(
        p for s, p in captured if "INSERT INTO action_approvals" in s
    )

    check(
        "NO_ACTION_FORCES_APPROVAL_NOT_REQUIRED",
        proposal_row[5] == 0
        and proposal_row[6] == "not_required"
        and approval_row[2] == "not_required",
    )

    valid_block = AIAnalysisProposal(
        summary="Synthetic public IP block proposal",
        severity="critical",
        confidence=0.99,
        evidence_event_ids=[
            request.events[0].event_id,
            request.events[1].event_id,
        ],
        recommended_action=RecommendedAction("temporary_block_ip"),
        target_ip="8.8.8.8",
        ttl_seconds=300,
        requires_human_approval=True,
        reasoning="Synthetic test only",
    )

    captured.clear()
    analysis_history.save_analysis(request, valid_block)

    proposal_row = next(
        p for s, p in captured if "INSERT INTO action_proposals" in s
    )
    approval_row = next(
        p for s, p in captured if "INSERT INTO action_approvals" in s
    )

    check(
        "PUBLIC_IP_BLOCK_REQUIRES_PENDING_APPROVAL",
        proposal_row[5] == 1
        and proposal_row[6] == "pending"
        and approval_row[2] == "pending",
    )

    try:
        AIAnalysisProposal(
            summary="Invalid block without approval",
            severity="critical",
            confidence=0.99,
            evidence_event_ids=[
                request.events[0].event_id,
                request.events[1].event_id,
            ],
            recommended_action=RecommendedAction("temporary_block_ip"),
            target_ip="8.8.8.8",
            ttl_seconds=300,
            requires_human_approval=False,
            reasoning="Synthetic invalid test",
        )
        approval_false_rejected = False
    except ValidationError:
        approval_false_rejected = True

    check(
        "BLOCK_REJECTS_MISSING_HUMAN_APPROVAL",
        approval_false_rejected,
    )

    try:
        AIAnalysisProposal(
            summary="Invalid private IP block",
            severity="critical",
            confidence=0.99,
            evidence_event_ids=[
                request.events[0].event_id,
                request.events[1].event_id,
            ],
            recommended_action=RecommendedAction("temporary_block_ip"),
            target_ip="192.168.0.10",
            ttl_seconds=300,
            requires_human_approval=True,
            reasoning="Synthetic invalid test",
        )
        private_ip_rejected = False
    except ValidationError:
        private_ip_rejected = True

    check(
        "BLOCK_REJECTS_PRIVATE_IP",
        private_ip_rejected,
    )

    try:
        AIAnalysisProposal(
            summary="Invalid block with one evidence",
            severity="critical",
            confidence=0.99,
            evidence_event_ids=[request.events[0].event_id],
            recommended_action=RecommendedAction("temporary_block_ip"),
            target_ip="8.8.8.8",
            ttl_seconds=300,
            requires_human_approval=True,
            reasoning="Synthetic invalid test",
        )
        single_evidence_rejected = False
    except ValidationError:
        single_evidence_rejected = True

    check(
        "BLOCK_REJECTS_SINGLE_EVIDENCE",
        single_evidence_rejected,
    )

finally:
    analysis_history._connection = original_connection

print()
print(f"TESTS_PASSED={passed}")
print(f"TESTS_FAILED={failed}")
print("REAL_DATABASE_ACCESSED=NO")
print("OLLAMA_ACCESSED=NO")
print("LIVE_WAZUH_ACCESSED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

| Checked | Result |
|---|---|
| `no_action` requires no approval | passed |
| Temporary blocking of a public IP waits for approval | passed |
| A blocking proposal without approval is rejected | passed |
| A blocking proposal for a private IP is rejected | passed |
| A blocking proposal with only one evidence event is rejected | passed |

All 15 functional tests so far have passed.

## Chapter 3: Masking the Wazuh Event Retrieval API Too

### 3.1 Checking the API Return Values

> **Run on: VM 230**

```bash
echo "===== VM230: API RESPONSE BOUNDARY STATIC AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- Analysis API routes ---"
for f in app/api/analysis.py app/api/wazuh.py; do
    if [ -f "$f" ]; then
        echo
        echo "### $f"
        nl -ba "$f" | sed -n '1,300p'
    fi
done

echo
echo "--- Response and request schemas ---"
for f in \
    app/schemas/analysis.py \
    app/schemas/analysis_proposal.py \
    app/schemas/security_event.py \
    app/schemas/wazuh.py
do
    if [ -f "$f" ]; then
        echo
        echo "### $f"
        nl -ba "$f" | sed -n '1,260p'
    fi
done

echo
echo "--- Router registration and exception handling ---"
grep -RInE \
    'include_router|exception_handler|HTTPException|response_model|return proposal|return .*analysis|save_analysis' \
    app/main.py app/api app/core \
    --include='*.py' 2>/dev/null | head -240

echo
echo "--- API response boundary audit complete ---"
echo "FILES_MODIFIED=NO"
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "LIVE_WAZUH_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

The two analysis APIs store the proposal returned by `analyze_events()` before returning it, so the masking and approval policy of Chapter 2 also apply to the responses. However, `GET /api/v1/wazuh/events` does not go through AI analysis and returns the result of `fetch_wazuh_events()` as is.

### 3.2 The Conversion in the Retrieval API

> **Run on: VM 230**

```bash
echo "===== VM230: WAZUH EVENT RESPONSE SANITIZATION AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- Wazuh relay conversion ---"
nl -ba app/services/wazuh_relay.py | sed -n '1,280p'

echo
echo "--- Event sanitizer implementation ---"
nl -ba app/services/event_sanitizer.py | sed -n '1,240p'

echo
echo "--- Sanitizer usage across application ---"
grep -RInE \
    'sanitize_event_summary|event_summary\s*=|event_summary=' \
    app --include='*.py' 2>/dev/null

echo
echo "--- Wazuh event endpoint response path ---"
grep -RInE \
    'fetch_wazuh_events|@router.get\("/events"|response_model=list\[SecurityEvent\]' \
    app --include='*.py' 2>/dev/null

echo
echo "FILES_MODIFIED=NO"
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "LIVE_WAZUH_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

`_convert_alert()` put Wazuh's `rule.description` into `event_summary` and `rule_description` as is. So `GET /api/v1/wazuh/events` could return unmasked strings.

### 3.3 Fixing

We fix only `wazuh_relay.py`, after making a copy, applying `sanitize_event_summary()` to both `event_summary` and `rule_description`. We check with synthetic data.

> **Run on: VM 230**

```bash
echo "===== VM230: WAZUH EVENT RESPONSE SANITIZATION FIX ====="

cd /opt/ai-defense-manager

venv/bin/python - <<'PY'
import ast
import hashlib
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone

path = Path("app/services/wazuh_relay.py")
source = path.read_text(encoding="utf-8")

backup_dir = Path(
    "/var/backups/ai-defense-manager/wazuh-response-sanitization-20261123"
)
backup_dir.mkdir(parents=True, exist_ok=True)
backup = backup_dir / "wazuh_relay.py"

if backup.exists():
    raise RuntimeError(f"Backup already exists: {backup}")

shutil.copy2(path, backup)

def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

backup_hash = sha256(backup)
original_hash = sha256(path)

if backup_hash != original_hash:
    raise RuntimeError("Backup integrity check failed")

print("BACKUP_CREATED=PASS")
print("BACKUP_SHA256_MATCH=PASS")

updated = source

import_anchor = "from app.schemas.security_event import SecurityEvent\n"
if updated.count(import_anchor) != 1:
    raise RuntimeError("Could not uniquely locate SecurityEvent import")

updated = updated.replace(
    import_anchor,
    import_anchor
    + "from app.services.event_sanitizer import sanitize_event_summary\n",
    1,
)

old_summary = '    summary = (description or "Wazuh security alert")[:512]\n'
new_summary = (
    '    summary = sanitize_event_summary(\n'
    '        description or "Wazuh security alert"\n'
    '    )\n'
)
if updated.count(old_summary) != 1:
    raise RuntimeError("Could not uniquely locate event summary assignment")

updated = updated.replace(old_summary, new_summary, 1)

old_description = (
    '        rule_description=description[:512] if description else None,\n'
)
new_description = (
    '        rule_description=(\n'
    '            sanitize_event_summary(description) if description else None\n'
    '        ),\n'
)
if updated.count(old_description) != 1:
    raise RuntimeError("Could not uniquely locate rule_description assignment")

updated = updated.replace(old_description, new_description, 1)

# Validate syntax before writing.
ast.parse(updated)

path.write_text(updated, encoding="utf-8")

# Preserve the original file's ownership and mode.
shutil.copystat(backup, path)
try:
    st = backup.stat()
    os.chown(path, st.st_uid, st.st_gid)
except PermissionError:
    raise RuntimeError("Unable to preserve source ownership")

print("SOURCE_PATCH=APPLIED")
print("PYTHON_SYNTAX=PASS")
print("SOURCE_SHA256_BEFORE=" + original_hash)
print("SOURCE_SHA256_AFTER=" + sha256(path))
PY

echo
echo "--- Synthetic sanitizer behavior test ---"

venv/bin/python - <<'PY'
from datetime import datetime, timezone

from app.services.wazuh_relay import _convert_alert

description = (
    "Failed login password=synthetic-secret "
    "contact=user@example.com source=203.0.113.10"
)

event = _convert_alert({
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "rule.level": 10,
    "rule.id": "5710",
    "rule.description": description,
    "rule.groups": ["authentication_failed"],
    "agent.id": "001",
})

checks = {
    "EVENT_SUMMARY_SECRET_REDACTED":
        "synthetic-secret" not in event.event_summary,
    "RULE_DESCRIPTION_SECRET_REDACTED":
        "synthetic-secret" not in (event.rule_description or ""),
    "EVENT_SUMMARY_EMAIL_REDACTED":
        "user@example.com" not in event.event_summary,
    "RULE_DESCRIPTION_EMAIL_REDACTED":
        "user@example.com" not in (event.rule_description or ""),
    "EVENT_SUMMARY_IP_REDACTED":
        "203.0.113.10" not in event.event_summary,
    "RULE_DESCRIPTION_IP_REDACTED":
        "203.0.113.10" not in (event.rule_description or ""),
    "EVENT_SUMMARY_LIMIT_512":
        len(event.event_summary) <= 512,
    "RULE_DESCRIPTION_LIMIT_512":
        len(event.rule_description or "") <= 512,
    "EVENT_CATEGORY_PRESERVED":
        event.event_category == "authentication",
}

for name, ok in checks.items():
    print(f"{name}={'PASS' if ok else 'FAIL'}")

print()
print(f"TESTS_PASSED={sum(checks.values())}")
print(f"TESTS_FAILED={len(checks) - sum(checks.values())}")
PY

echo
echo "--- Final source metadata ---"
stat -c 'OWNER=%U GROUP=%G MODE=%a SIZE=%s' app/services/wazuh_relay.py
sha256sum app/services/wazuh_relay.py

echo
echo "REAL_WAZUH_ACCESSED=NO"
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

The synthetic tests after the fix **all 9 passed**, confirming masking of secrets, email addresses and IP addresses and the 512-character limit.

## Chapter 4: Checking Permissions and Restarting

### 4.1 File Permissions

> **Run on: VM 230**

```bash
echo "===== VM230: WAZUH RELAY SOURCE PERMISSION PRECHECK ====="

cd /opt/ai-defense-manager

echo
echo "--- Service identity ---"
systemctl show ai-defense-manager.service \
  -p User -p Group -p SupplementaryGroups -p MainPID

echo
echo "--- Source and backup metadata ---"
stat -c '%n OWNER=%U GROUP=%G MODE=%a' \
  app/services/wazuh_relay.py \
  /var/backups/ai-defense-manager/wazuh-response-sanitization-20261123/wazuh_relay.py

echo
echo "--- Parent directory permissions ---"
namei -l /opt/ai-defense-manager/app/services/wazuh_relay.py

echo
echo "--- Read access as service user ---"
runuser -u ai-defense -- test -r app/services/wazuh_relay.py
echo "SERVICE_USER_SOURCE_READABLE=$?"

echo
echo "--- Backup and source hashes ---"
sha256sum \
  app/services/wazuh_relay.py \
  /var/backups/ai-defense-manager/wazuh-response-sanitization-20261123/wazuh_relay.py

echo
echo "FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

The fixed `wazuh_relay.py` had become `root:root`, `640`, so the service user `ai-defense` could not read it. **It cannot be restarted in this state.**

### 4.2 Restoring the Group

Keeping owner `root` and mode `640`, we restore only the group to `ai-defense`.

> **Run on: VM 230**

```bash
echo "===== VM230: RESTORE WAZUH RELAY SOURCE READ PERMISSION ====="

cd /opt/ai-defense-manager

chgrp ai-defense app/services/wazuh_relay.py

echo
echo "--- Updated source metadata ---"
stat -c 'OWNER=%U GROUP=%G MODE=%a' app/services/wazuh_relay.py

echo
echo "--- Service user read test ---"
if runuser -u ai-defense -- test -r app/services/wazuh_relay.py; then
    echo "SERVICE_USER_SOURCE_READABLE=PASS"
else
    echo "SERVICE_USER_SOURCE_READABLE=FAIL"
fi

echo
echo "--- Source integrity ---"
sha256sum app/services/wazuh_relay.py

echo
echo "SOURCE_CONTENT_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Item | Result |
|---|---|
| Owner | `root` (unchanged) |
| Group | `ai-defense` (restored) |
| Mode | `640` (unchanged) |
| Read by the service user | passed |
| Source SHA256 | matches the value after the fix (contents not changed) |

### 4.3 Restarting

> **Run on: VM 230**

```bash
echo "===== VM230: AI DEFENSE MANAGER RESTART ====="

systemctl restart ai-defense-manager.service
echo "RESTART_EXIT_CODE=$?"

echo
echo "--- Service status ---"
systemctl is-active ai-defense-manager.service
systemctl show ai-defense-manager.service \
  -p MainPID -p User -p Group -p ActiveState -p SubState

echo
echo "--- API listener ---"
ss -lntp | grep ':8000' || echo "API_LISTENER_NOT_FOUND"

echo
echo "--- Health check ---"
curl --silent --show-error \
  --connect-timeout 3 --max-time 10 \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "WAZUH_ALERTS_FETCHED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "ANALYSIS_TRIGGERED=NO"
echo "DATABASE_WRITE_TRIGGERED=NO"
```

The restart gave exit code `0`, but the check right after showed nothing listening on port 8000, and `/health` gave `HTTP 000`.

### 4.4 Checking the Startup

> **Run on: VM 230**

```bash
echo "===== VM230: AI DEFENSE MANAGER STARTUP FAILURE DIAGNOSTICS ====="

echo
echo "--- Full service status ---"
systemctl status ai-defense-manager.service --no-pager -l

echo
echo "--- Recent service journal ---"
journalctl -u ai-defense-manager.service \
  --since "-15 minutes" --no-pager -n 120

echo
echo "--- Process details ---"
ps -o pid,ppid,user,group,stat,lstart,args -p 1469

echo
echo "--- Listening sockets ---"
ss -lntp

echo
echo "--- Service unit ---"
systemctl cat ai-defense-manager.service

echo
echo "--- Recent application errors ---"
journalctl -u ai-defense-manager.service \
  --since "-15 minutes" --no-pager |
  grep -iE 'error|exception|traceback|failed|permission|import|uvicorn|startup|shutdown' |
  tail -80

echo
echo "CONFIGURATION_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "LIVE_WAZUH_ACCESSED=NO"
```

systemd showed `active (running)`, Uvicorn showed `Application startup complete`, the PID was `1469`, and it was listening on `127.0.0.1:8000`. The earlier result was because the check came right after the restart.

> **Run on: VM 230**

```bash
echo "===== VM230: POST-RESTART API HEALTH VERIFICATION ====="

echo
echo "--- Listener ---"
ss -lntp | grep '127.0.0.1:8000'

echo
echo "--- Health endpoint ---"
curl --silent --show-error \
  --connect-timeout 3 --max-time 10 \
  -w '\nHTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "API_BINDING=127.0.0.1:8000"
echo "WAZUH_ALERTS_FETCHED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "ANALYSIS_TRIGGERED=NO"
echo "DATABASE_WRITE_TRIGGERED=NO"
```

| Item | Result |
|---|---|
| AI Defense Manager | `active` (PID `1469`) |
| Listening | `127.0.0.1:8000` |
| `/health` | `HTTP 200` |
| Running as | `ai-defense` |

## Closing Notes

In Part 54 we made the AI Defense Manager side protect the LLM output and approval decisions.

| Item | Result |
|---|---|
| LLM `summary`, `reasoning` | masked; limited to 2,000 and 4,000 characters |
| Approval | everything other than `no_action` always requires approval on the server side (applied again when storing in the DB) |
| Temporary blocking | requires a public IP, two pieces of evidence and approval; private IPs are rejected |
| Wazuh event retrieval API | `event_summary` and `rule_description` are also masked |
| Tests | all 10, 5 and 9 cases passed |
| Permissions | `wazuh_relay.py` is `root:ai-defense`, `640` |
| Service | restarted; `/health` is `HTTP 200` |

> **Caution:** After rewriting source files, check that owner, group and mode are `root:ai-defense`, `640` before restarting. With `root:root` the service cannot read them.

In the next part, Part 55, we check the integration as a whole and add limits that protect the API from high request volumes.

# Part 55: Integration Checks and Preparing for High Request Volumes
## Introduction

### About This Book

This is Part 55 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 54 we added masking of LLM output and the approval policy. Here we do the following.

1. Before moving on to real alerts and AI analysis, check VM 230 as an integrated whole
2. Check the safety boundaries with tests that make no outside communication (25 synthetic events, 9 analysis cases with simulated Ollama answers)
3. Check access control to the API and preparation for high request volumes (DoS)
4. Add a limit on Uvicorn concurrent connections, a limit on concurrent AI analyses, and a limit on HTTP body size

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

## Chapter 1: Integration Checks

### 1.1 Integration of Masking, Approval and Input

> **Run on: VM 230**

```bash
echo "===== VM230: AI DEFENSE FINAL INTEGRATION AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- 1. Sanitizer integration points ---"
grep -RInE \
  'sanitize_event_summary|sanitize_analysis_text|_convert_alert|event_summary=|rule_description=' \
  app --include='*.py'

echo
echo "--- 2. AI analysis trust boundary ---"
nl -ba app/services/ai_analysis.py | sed -n '1,260p'

echo
echo "--- 3. Analysis persistence and approval policy ---"
nl -ba app/services/analysis_history.py | sed -n '100,260p'

echo
echo "--- 4. Proposal validation ---"
nl -ba app/schemas/analysis_proposal.py | sed -n '1,180p'

echo
echo "--- 5. Wazuh API response boundary ---"
nl -ba app/api/wazuh.py | sed -n '1,130p'

echo
echo "--- 6. Potential action execution paths ---"
grep -RInE \
  'subprocess|os\.system|create_subprocess|iptables|nftables|firewall|execute_action|ActionGateway|action_gateway|approve_action|approval' \
  app --include='*.py' 2>/dev/null | head -200

echo
echo "--- 7. Modified source integrity and permissions ---"
stat -c '%n OWNER=%U GROUP=%G MODE=%a' \
  app/services/wazuh_relay.py \
  app/services/event_sanitizer.py \
  app/services/ai_analysis.py \
  app/services/analysis_history.py \
  app/schemas/analysis_proposal.py

sha256sum \
  app/services/wazuh_relay.py \
  app/services/event_sanitizer.py \
  app/services/ai_analysis.py \
  app/services/analysis_history.py \
  app/schemas/analysis_proposal.py

echo
echo "--- 8. Runtime status ---"
systemctl is-active ai-defense-manager.service
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "FILES_MODIFIED=NO"
echo "REAL_WAZUH_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "DATABASE_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

We confirmed that masking is used on each path, and that even if the LLM returns `requires_human_approval=false`, the server side overrides it so that approval is required, both when returning analysis results and when storing in the DB. There is no automatic execution; it goes only as far as storing proposals.

### 1.2 Schemas and Masking

> **Run on: VM 230**

```bash
echo "===== VM230: EVENT SCHEMA AND SANITIZER SECURITY AUDIT ====="

cd /opt/ai-defense-manager

echo
echo "--- 1. Event sanitizer implementation ---"
nl -ba app/services/event_sanitizer.py

echo
echo "--- 2. SecurityEvent schema ---"
nl -ba app/schemas/security_event.py

echo
echo "--- 3. Analysis request schema ---"
nl -ba app/schemas/analysis.py

echo
echo "--- 4. Wazuh relay conversion and validation ---"
nl -ba app/services/wazuh_relay.py | sed -n '1,190p'

echo
echo "--- 5. Analysis API response boundary ---"
nl -ba app/api/analysis.py

echo
echo "--- 6. Wazuh request schema ---"
nl -ba app/schemas/wazuh.py

echo
echo "--- 7. Existing test inventory ---"
find . -maxdepth 4 -type f \
  \( -name 'test_*.py' -o -name '*_test.py' \) \
  -not -path './venv/*' -print | sort

echo
echo "--- 8. Runtime status ---"
systemctl is-active ai-defense-manager.service
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "FILES_MODIFIED=NO"
echo "REAL_WAZUH_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "DATABASE_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

Wazuh events are masked at conversion, the AI input is built from an allowlist, and `SecurityEvent` and analysis requests reject unknown fields. There are no test files, and the masking looks for common patterns, so there is no guarantee it can remove secrets in unknown forms.

## Chapter 2: Tests Without Outside Communication

### 2.1 Safety Boundary Tests (25 Cases)

No outside communication, DB writes or file changes.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED SECURITY BOUNDARY TESTS ====="

./venv/bin/python - <<'PY'
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import ValidationError

from app.services.event_sanitizer import (
    sanitize_event_summary,
    sanitize_analysis_text,
)
from app.services.wazuh_relay import _convert_alert
from app.services.ai_analysis import _build_event_payload, AIAnalysisError
from app.schemas.security_event import SecurityEvent
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import (
    AIAnalysisProposal,
    RecommendedAction,
)

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"{name}=PASS")
    else:
        failed += 1
        print(f"{name}=FAIL")

def rejects(fn):
    try:
        fn()
    except (ValueError, ValidationError, AIAnalysisError):
        return True
    return False

# 1. Sanitizer behavior
sample = (
    "Bearer abc.def password=hunter2 "
    "contact=user@example.com host=203.0.113.10"
)
clean = sanitize_event_summary(sample)

check("BEARER_REDACTION", "abc.def" not in clean)
check("PASSWORD_REDACTION", "hunter2" not in clean)
check("EMAIL_REDACTION", "user@example.com" not in clean)
check("IP_REDACTION", "203.0.113.10" not in clean)
check("EVENT_LENGTH_LIMIT", len(sanitize_event_summary("x" * 900)) <= 512)
check("EMPTY_EVENT_FALLBACK", sanitize_event_summary("   ") == "[REDACTED_EVENT]")
check("NONSTRING_EVENT_FALLBACK", sanitize_event_summary(None) == "[REDACTED_EVENT]")
check(
    "INVALID_ANALYSIS_LENGTH_REJECTED",
    rejects(lambda: sanitize_analysis_text("test", True)),
)

# 2. Wazuh alert conversion: extra fields must not propagate
alert = {
    "timestamp": "2026-11-24T00:00:00Z",
    "rule.level": 10,
    "rule.id": "5710",
    "rule.description": "Bearer sampletoken password=secret123",
    "rule.groups": ["sshd"],
    "agent.id": "001",
    "full_log": "SENSITIVE_TEST_DATA",
    "data": {"password": "SENSITIVE_TEST_DATA"},
    "agent.name": "SENSITIVE_TEST_DATA",
}
event = _convert_alert(alert)

check("WAZUH_EVENT_CONVERSION", event.source == "wazuh")
check("WAZUH_EXTRA_FIELDS_NOT_PROPAGATED", not hasattr(event, "full_log"))
check("WAZUH_SUMMARY_SANITIZED", "secret123" not in event.event_summary)
check(
    "WAZUH_DESCRIPTION_SANITIZED",
    event.rule_description is not None and "sampletoken" not in event.rule_description,
)
check("WAZUH_AGENT_ID_ALLOWLIST", event.agent_id == "001")
check("WAZUH_CATEGORY_MAPPING", event.event_category == "remote_access")

# 3. Invalid Wazuh alert rejection
check(
    "NAIVE_TIMESTAMP_REJECTED",
    rejects(lambda: _convert_alert({
        **alert, "timestamp": "2026-11-24T00:00:00"
    })),
)
check(
    "BOOLEAN_RULE_LEVEL_REJECTED",
    rejects(lambda: _convert_alert({**alert, "rule.level": True})),
)
check(
    "INVALID_GROUP_REJECTED",
    rejects(lambda: _convert_alert({**alert, "rule.groups": ["sshd;admin"]})),
)

# 4. LLM payload allowlist and prohibited Wazuh fields
payload = _build_event_payload(event)
check(
    "LLM_PAYLOAD_EXACT_ALLOWLIST",
    set(payload) == {
        "event_id", "observed_at", "severity",
        "rule_id", "event_category", "event_summary"
    },
)
check("LLM_PAYLOAD_SANITIZED", "secret123" not in payload["event_summary"])

prohibited_event = SecurityEvent(
    source="wazuh",
    observed_at=datetime.now(timezone.utc),
    severity="high",
    event_category="authentication",
    event_summary="synthetic test",
    source_ip="203.0.113.10",
)
check(
    "WAZUH_SOURCE_IP_REJECTED_FROM_LLM",
    rejects(lambda: _build_event_payload(prohibited_event)),
)

# 5. Schema boundary checks
check(
    "UNKNOWN_SECURITY_EVENT_FIELD_REJECTED",
    rejects(lambda: SecurityEvent(
        source="internal",
        severity="low",
        event_category="other",
        event_summary="test",
        unexpected_field="value",
    )),
)

check(
    "ANALYSIS_REQUEST_EVENT_LIMIT",
    rejects(lambda: AIAnalysisRequest(events=[])),
)

# 6. Proposal policy schema checks (no execution)
ids = [uuid4(), uuid4()]

valid_block = AIAnalysisProposal(
    summary="synthetic proposal",
    severity="high",
    confidence=0.9,
    evidence_event_ids=ids,
    recommended_action=RecommendedAction.TEMPORARY_BLOCK_IP,
    target_ip="8.8.8.8",
    ttl_seconds=300,
    requires_human_approval=True,
    reasoning="synthetic test",
)
check(
    "PUBLIC_IP_BLOCK_PROPOSAL_SCHEMA",
    valid_block.requires_human_approval and valid_block.ttl_seconds == 300,
)
check(
    "PRIVATE_IP_BLOCK_REJECTED",
    rejects(lambda: AIAnalysisProposal(
        summary="test",
        severity="high",
        confidence=0.9,
        evidence_event_ids=ids,
        recommended_action=RecommendedAction.TEMPORARY_BLOCK_IP,
        target_ip="192.168.1.1",
        ttl_seconds=300,
        requires_human_approval=True,
        reasoning="test",
    )),
)
check(
    "SINGLE_EVIDENCE_BLOCK_REJECTED",
    rejects(lambda: AIAnalysisProposal(
        summary="test",
        severity="high",
        confidence=0.9,
        evidence_event_ids=[ids[0]],
        recommended_action=RecommendedAction.TEMPORARY_BLOCK_IP,
        target_ip="8.8.8.8",
        ttl_seconds=300,
        requires_human_approval=True,
        reasoning="test",
    )),
)

print()
print(f"TESTS_PASSED={passed}")
print(f"TESTS_FAILED={failed}")
print("EXTERNAL_NETWORK_REQUESTS=0")
print("OLLAMA_REQUESTS=0")
print("DATABASE_WRITES=0")
PY

echo
echo "--- Service remains active ---"
systemctl is-active ai-defense-manager.service
echo "===== TEST RUN COMPLETE ====="
```

All 25 passed. We confirmed removal of extra fields in Wazuh events, masking of secrets, the LLM input allowlist, and rejection of invalid events and dangerous blocking proposals.

### 2.2 Analysis Tests (Simulated Ollama Answers, 9 Cases)

We test `analyze_events()` with simulated Ollama answers.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: MOCKED AI ANALYSIS PIPELINE TEST ====="

./venv/bin/python - <<'PY'
import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.analysis import AIAnalysisRequest
from app.schemas.security_event import SecurityEvent
from app.services import ai_analysis

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"{name}=PASS")
    else:
        failed += 1
        print(f"{name}=FAIL")

class FakeResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass

    def json(self):
        return {"message": {"content": self.content}}

class FakeAsyncClient:
    response_content = None
    captured_payload = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, json):
        FakeAsyncClient.captured_payload = json
        return FakeResponse(FakeAsyncClient.response_content)

async def main():
    original_client = ai_analysis.httpx.AsyncClient
    ai_analysis.httpx.AsyncClient = FakeAsyncClient

    try:
        event = SecurityEvent(
            source="wazuh",
            observed_at=datetime.now(timezone.utc),
            severity="high",
            rule_id="5710",
            agent_id="001",
            event_category="authentication",
            event_summary="Synthetic authentication alert",
        )

        request = AIAnalysisRequest(
            events=[event],
            analysis_context="CONTEXT_SECRET_SHOULD_NOT_BE_FORWARDED",
            requested_language="en",
        )

        # Case 1: A model tries to waive approval for a notify action.
        FakeAsyncClient.response_content = json.dumps({
            "summary": "password=hunter2 contact=test@example.com host=8.8.8.8",
            "severity": "high",
            "confidence": 0.91,
            "evidence_event_ids": [str(event.event_id)],
            "recommended_action": "notify",
            "target_ip": None,
            "ttl_seconds": None,
            "requires_human_approval": False,
            "reasoning": "Bearer synthetic-token should be redacted",
        })

        proposal = await ai_analysis.analyze_events(request)

        check(
            "LLM_RESPONSE_SUMMARY_SECRET_REDACTION",
            "hunter2" not in proposal.summary,
        )
        check(
            "LLM_RESPONSE_EMAIL_REDACTION",
            "test@example.com" not in proposal.summary,
        )
        check(
            "LLM_RESPONSE_IP_REDACTION",
            "8.8.8.8" not in proposal.summary,
        )
        check(
            "LLM_RESPONSE_REASONING_REDACTION",
            "synthetic-token" not in proposal.reasoning,
        )
        check(
            "SERVER_FORCES_NOTIFY_APPROVAL",
            proposal.requires_human_approval is True,
        )
        check(
            "LLM_INPUT_USES_ALLOWLIST",
            set(FakeAsyncClient.captured_payload["messages"][1]["content"]
                and json.loads(FakeAsyncClient.captured_payload["messages"][1]["content"])["events"][0])
            == {
                "event_id", "observed_at", "severity",
                "rule_id", "event_category", "event_summary"
            },
        )
        check(
            "ANALYSIS_CONTEXT_NOT_FORWARDED",
            "CONTEXT_SECRET_SHOULD_NOT_BE_FORWARDED"
            not in json.dumps(FakeAsyncClient.captured_payload),
        )

        # Case 2: A no_action response remains non-approval-required.
        FakeAsyncClient.response_content = json.dumps({
            "summary": "No action required",
            "severity": "info",
            "confidence": 0.8,
            "evidence_event_ids": [str(event.event_id)],
            "recommended_action": "no_action",
            "target_ip": None,
            "ttl_seconds": None,
            "requires_human_approval": True,
            "reasoning": "Synthetic no-action test",
        })

        no_action = await ai_analysis.analyze_events(request)
        check(
            "SERVER_NO_ACTION_POLICY",
            no_action.requires_human_approval is False,
        )

        # Case 3: Unknown evidence IDs must be rejected.
        FakeAsyncClient.response_content = json.dumps({
            "summary": "Invalid evidence test",
            "severity": "high",
            "confidence": 0.9,
            "evidence_event_ids": [str(uuid4())],
            "recommended_action": "notify",
            "target_ip": None,
            "ttl_seconds": None,
            "requires_human_approval": True,
            "reasoning": "Synthetic invalid evidence",
        })

        try:
            await ai_analysis.analyze_events(request)
            unknown_evidence_rejected = False
        except ai_analysis.AIAnalysisError:
            unknown_evidence_rejected = True

        check("UNKNOWN_EVIDENCE_ID_REJECTED", unknown_evidence_rejected)

    finally:
        ai_analysis.httpx.AsyncClient = original_client

    print()
    print(f"TESTS_PASSED={passed}")
    print(f"TESTS_FAILED={failed}")

asyncio.run(main())
PY

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service

echo "REAL_OLLAMA_REQUESTS=0"
echo "REAL_WAZUH_REQUESTS=0"
echo "DATABASE_WRITES=0"
echo "SOURCE_FILES_MODIFIED=NO"
echo "===== MOCKED ANALYSIS TEST COMPLETE ====="
```

| Checked | Result |
|---|---|
| Masking of secrets, email and IPs in LLM output | passed |
| For `notify`, even if the LLM says no approval is needed, the server side requires approval | passed |
| Unknown evidence event IDs are rejected | passed |
| Actual connections to Wazuh or Ollama, DB writes, source changes | none |

In total, **all 34 passed** (0 failures). We also confirmed that the `analysis_context` accepted by the API is not passed into the LLM input.

## Chapter 3: Access Control and DoS Checks

### 3.1 Access Control

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API ACCESS CONTROL AUDIT ====="

echo
echo "--- 1. Application entrypoint and middleware ---"
nl -ba app/main.py

echo
echo "--- 2. Authentication and authorization references ---"
grep -RInE \
  'HTTPBearer|OAuth2|APIKey|HTTPBasic|Depends\(|Security\(|middleware|authentication|authorization|CORS|CORSMiddleware' \
  app --include='*.py' || true

echo
echo "--- 3. All API route declarations ---"
grep -RInE \
  '@router\.(get|post|put|patch|delete)|APIRouter\(' \
  app/api --include='*.py'

echo
echo "--- 4. Runtime configuration definitions ---"
nl -ba app/core/config.py

echo
echo "--- 5. Service bind and execution settings ---"
systemctl show ai-defense-manager.service \
  -p User -p Group -p ExecStart -p EnvironmentFiles \
  -p NoNewPrivileges -p ProtectSystem \
  -p RestrictAddressFamilies -p ReadWritePaths

echo
echo "--- 6. Listener verification ---"
ss -lntp | grep ':8000' || true

echo
echo "--- 7. Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "FILES_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

The API listens only on `127.0.0.1:8000`, runs as `ai-defense`, with `NoNewPrivileges=yes` and `ProtectSystem=strict`, but there was no authentication, authorization or CORS middleware within the application.

### 3.2 Documentation and Routes

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: FASTAPI DOCUMENTATION AND ROUTE AUDIT ====="

./venv/bin/python - <<'PY'
from app.main import app

print("--- FastAPI documentation configuration ---")
print("DOCS_URL =", app.docs_url)
print("REDOC_URL =", app.redoc_url)
print("OPENAPI_URL =", app.openapi_url)

print()
print("--- Registered routes ---")
for route in app.routes:
    methods = sorted(getattr(route, "methods", []) or [])
    path = getattr(route, "path", "<unknown>")
    name = getattr(route, "name", "<unknown>")
    print(f"PATH={path} METHODS={','.join(methods)} NAME={name}")

print()
print("--- OpenAPI security schemes ---")
schema = app.openapi()
components = schema.get("components", {})
print("SECURITY_SCHEMES =", list(components.get("securitySchemes", {}).keys()))
print("GLOBAL_SECURITY =", schema.get("security", []))
PY

echo
echo "--- Listener addresses ---"
ss -lntp | grep -E 'uvicorn|:8000' || true

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "FILES_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Endpoint | State |
|---|---|
| `/docs` | enabled |
| `/redoc` | enabled |
| `/openapi.json` | enabled |
| `/health` | enabled |
| API authentication scheme | none |

It is `127.0.0.1` only, but the API specification can be viewed without authentication. Our policy is to disable `/docs`, `/redoc` and `/openapi.json` in production.

### 3.3 Preparing for High Request Volumes

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API RESOURCE AND DOS RESILIENCE AUDIT ====="

echo
echo "--- 1. Uvicorn startup arguments ---"
systemctl show ai-defense-manager.service -p ExecStart

echo
echo "--- 2. Request size and rate limiting references ---"
grep -RInE \
  'Content-Length|content-length|RequestSize|Body\(|max_body|rate.limit|slowapi|Limiter|Semaphore|asyncio\.Semaphore|timeout|concurrency|limit_concurrency|limit_max_requests' \
  app /etc/systemd/system/ai-defense-manager.service \
  --include='*.py' --include='*.service' 2>/dev/null || true

echo
echo "--- 3. API input constraints ---"
grep -RInE \
  'Field\(|Query\(|max_length|min_length|ge=|le=|max_items|list\[' \
  app/api app/schemas --include='*.py'

echo
echo "--- 4. Dependency versions ---"
./venv/bin/python - <<'PY'
from importlib.metadata import PackageNotFoundError, version

for package in ("fastapi", "starlette", "uvicorn", "pydantic", "httpx"):
    try:
        print(f"{package}={version(package)}")
    except PackageNotFoundError:
        print(f"{package}=NOT_INSTALLED")
PY

echo
echo "--- 5. Runtime limits ---"
systemctl show ai-defense-manager.service \
  -p MemoryMax -p TasksMax -p LimitNOFILE -p CPUQuota \
  -p TimeoutStartUSec -p TimeoutStopUSec

echo
echo "--- 6. Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "FILES_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

```bash
cd /opt/ai-defense-manager

echo "===== VM230: UVICORN AND CONCURRENCY DETAIL AUDIT ====="

echo
echo "--- 1. Full service unit ---"
systemctl cat ai-defense-manager.service

echo
echo "--- 2. Actual running process arguments ---"
PID="$(systemctl show ai-defense-manager.service -p MainPID --value)"
python3 - "$PID" <<'PY'
import pathlib
import sys

pid = sys.argv[1]
raw = pathlib.Path(f"/proc/{pid}/cmdline").read_bytes()
args = raw.decode(errors="replace").split("\0")
print("PROCESS_ARGUMENTS:")
for arg in args:
    if arg:
        print(arg)
PY

echo
echo "--- 3. Analysis endpoint execution flow ---"
nl -ba app/api/analysis.py
nl -ba app/api/wazuh.py | sed -n '30,100p'

echo
echo "--- 4. Ollama request lifecycle ---"
nl -ba app/services/ai_analysis.py | sed -n '70,145p'

echo
echo "--- 5. Uvicorn concurrency controls available ---"
./venv/bin/uvicorn --help | grep -E \
  'limit-concurrency|limit-max-requests|backlog|timeout-keep-alive|workers'

echo
echo "--- 6. Existing middleware inventory ---"
grep -RInE \
  'BaseHTTPMiddleware|@app\.middleware|add_middleware|asyncio\.Lock|Semaphore|CapacityLimiter' \
  app --include='*.py' || true

echo
echo "--- 7. Runtime status ---"
systemctl is-active ai-defense-manager.service
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "FILES_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Item | State |
|---|---|
| Maximum number of events | 100 |
| Maximum fetched from Wazuh | 100 |
| LLM response timeout | 60 seconds |
| Relay communication timeout | 15 seconds |
| Maximum wait for SQLite lock | 5 seconds |
| Memory limit | 1GiB |
| HTTP body size limit | **none** |
| Concurrent connection limit (`--limit-concurrency`) | **not specified** |
| Concurrent AI analysis limit | **none** |

Even with one worker, the API is asynchronous and processes several requests at once. The two analysis APIs ask Ollama for analysis, so when requests pile up, waits and timeouts increase (Ollama's parallelism is 1).

### 3.4 The Limits to Add

| Measure | Value |
|---|---|
| Uvicorn concurrent connections | 8 |
| Connection backlog | 32 |
| Keep-Alive timeout | 5 seconds |
| Concurrent AI analyses | 1 (excess requests wait) |
| HTTP body size | 256KiB (`HTTP 413` if exceeded) |
| Number of workers | stays at 1 |

Uvicorn's connection limits alone cannot limit body size, so we add an ASGI middleware that counts the size while reading the body. Storage in SQLite, communication with the Relay, LLM prompts and the safety policy are not changed.

## Chapter 4: Adding the Limits

### 4.1 Checking Before the Change

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: DOS PROTECTION IMPLEMENTATION PRECHECK ====="

echo
echo "--- 1. Application entrypoint ---"
cat app/main.py

echo
echo "--- 2. Complete AI analysis service ---"
cat app/services/ai_analysis.py

echo
echo "--- 3. Systemd unit and drop-ins ---"
systemctl cat ai-defense-manager.service

echo
echo "--- 4. Source file metadata ---"
stat -c '%n owner=%U group=%G mode=%a size=%s' \
  app/main.py \
  app/services/ai_analysis.py \
  /etc/systemd/system/ai-defense-manager.service

echo
echo "--- 5. Python runtime ---"
./venv/bin/python --version

echo
echo "--- 6. Existing test directories ---"
find . -maxdepth 3 -type d \
  \( -name tests -o -name test \) -print

echo
echo "--- 7. Current service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "FILES_MODIFIED=NO"
echo "BACKUPS_CREATED=NO"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
echo "DATABASE_ACCESSED=NO"
```

```bash
cd /opt/ai-defense-manager

echo "===== VM230: DOS PATCH FINAL PRECHECK ====="

echo
echo "--- 1. Existing test files ---"
find tests -maxdepth 3 -type f -printf '%p\n' | sort

echo
echo "--- 2. Existing test configuration ---"
find . -maxdepth 2 -type f \
  \( -name 'pytest.ini' -o -name 'pyproject.toml' -o -name 'tox.ini' -o -name 'conftest.py' \) \
  -print

echo
echo "--- 3. Full systemd ExecStart ---"
systemctl show ai-defense-manager.service -p ExecStart --value

echo
echo "--- 4. Existing drop-in files ---"
find /etc/systemd/system/ai-defense-manager.service.d \
  -maxdepth 1 -type f -printf '%f\n' 2>/dev/null | sort

echo
echo "--- 5. Current source hashes ---"
sha256sum app/main.py app/services/ai_analysis.py

echo
echo "--- 6. Current service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "FILES_MODIFIED=NO"
echo "BACKUPS_CREATED=NO"
echo "SERVICE_RESTARTED=NO"
```

The waiting for AI analysis is placed at the entry of the existing analysis function, so there is only one concurrent request to Ollama. The body limit applies to the whole application. Uvicorn settings are overridden with a dedicated drop-in rather than rewriting the systemd unit itself (easy to save, compare and revert).

### 4.2 Applying the Patch

After making copies, we change the code and the systemd settings. The service is not restarted yet.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: APPLY DOS PROTECTION PATCH ====="

BACKUP_DIR="/var/backups/ai-defense-manager/dos-protection-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR/systemd"

cp -a app/main.py app/services/ai_analysis.py "$BACKUP_DIR/"
cp -a /etc/systemd/system/ai-defense-manager.service "$BACKUP_DIR/systemd/"
cp -a /etc/systemd/system/ai-defense-manager.service.d/20-sqlite.conf "$BACKUP_DIR/systemd/"

sha256sum \
  "$BACKUP_DIR/main.py" \
  "$BACKUP_DIR/ai_analysis.py" \
  "$BACKUP_DIR/systemd/ai-defense-manager.service" \
  "$BACKUP_DIR/systemd/20-sqlite.conf" \
  > "$BACKUP_DIR/SHA256SUMS"

echo "BACKUP_DIR=$BACKUP_DIR"
echo "BACKUP_VERIFICATION:"
sha256sum -c "$BACKUP_DIR/SHA256SUMS"

echo
echo "--- Apply application patches ---"

./venv/bin/python - <<'PY'
from pathlib import Path

main_path = Path("app/main.py")
analysis_path = Path("app/services/ai_analysis.py")

main = main_path.read_text()
analysis = analysis_path.read_text()

old_import = "from fastapi import FastAPI\n"
new_import = """from fastapi import FastAPI


class RequestBodyLimitMiddleware:
    def __init__(self, app, max_body_bytes: int = 256 * 1024):
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")

        if content_length is not None:
            try:
                declared_length = int(content_length)
            except ValueError:
                declared_length = None

            if declared_length is not None and declared_length > self.max_body_bytes:
                await self._reject(send)
                return

        body = bytearray()

        while True:
            message = await receive()

            if message["type"] == "http.disconnect":
                return

            if message["type"] != "http.request":
                continue

            chunk = message.get("body", b"")

            if len(body) + len(chunk) > self.max_body_bytes:
                await self._reject(send)
                return

            body.extend(chunk)

            if not message.get("more_body", False):
                break

        body_bytes = bytes(body)
        replayed = False

        async def replay_receive():
            nonlocal replayed
            if not replayed:
                replayed = True
                return {
                    "type": "http.request",
                    "body": body_bytes,
                    "more_body": False,
                }
            return await receive()

        await self.app(scope, replay_receive, send)

    async def _reject(self, send):
        body = b'{"detail":"Request body exceeds 256 KiB limit"}'
        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })
"""

if main.count(old_import) != 1:
    raise RuntimeError("Unexpected FastAPI import block; no main.py changes made")

main = main.replace(old_import, new_import, 1)

app_marker = """    lifespan=lifespan,
)

app.include_router(analysis_router)
"""
app_replacement = """    lifespan=lifespan,
)

app.add_middleware(
    RequestBodyLimitMiddleware,
    max_body_bytes=256 * 1024,
)

app.include_router(analysis_router)
"""

if main.count(app_marker) != 1:
    raise RuntimeError("Unexpected FastAPI app construction; no main.py changes made")

main = main.replace(app_marker, app_replacement, 1)

if "RequestBodyLimitMiddleware" in analysis:
    raise RuntimeError("Unexpected existing analysis semaphore patch")

analysis = analysis.replace(
    "import json\n",
    "import asyncio\nimport json\n",
    1,
)

analysis = analysis.replace(
    'MODEL_NAME = "qwen3:8b"\n',
    'MODEL_NAME = "qwen3:8b"\n\n_ANALYSIS_SEMAPHORE = asyncio.Semaphore(1)\n',
    1,
)

function_marker = "async def analyze_events(\n"
if analysis.count(function_marker) != 1:
    raise RuntimeError("Unexpected analyze_events declaration")

analysis = analysis.replace(
    function_marker,
    "async def _analyze_events_unlimited(\n",
    1,
)

analysis += """


async def analyze_events(
    request: AIAnalysisRequest,
) -> AIAnalysisProposal:
    # Serialize Ollama inference; excess analysis requests wait here.
    async with _ANALYSIS_SEMAPHORE:
        return await _analyze_events_unlimited(request)
"""

main_path.write_text(main)
analysis_path.write_text(analysis)

print("MAIN_BODY_LIMIT_PATCH=APPLIED")
print("ANALYSIS_SEMAPHORE_PATCH=APPLIED")
PY

PATCH_STATUS=$?

if [ "$PATCH_STATUS" -ne 0 ]; then
  echo "APPLICATION_PATCH=FAILED"
else
  echo
  echo "--- Install Uvicorn systemd drop-in ---"

  cat > /etc/systemd/system/ai-defense-manager.service.d/30-dos-protection.conf <<'EOF'
[Service]
ExecStart=
ExecStart=/opt/ai-defense-manager/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --limit-concurrency 8 --backlog 32 --timeout-keep-alive 5
EOF

  chmod 644 /etc/systemd/system/ai-defense-manager.service.d/30-dos-protection.conf

  echo
  echo "--- Python syntax validation ---"
  ./venv/bin/python -m py_compile app/main.py app/services/ai_analysis.py
  echo "PYTHON_SYNTAX_EXIT=$?"

  echo
  echo "--- Ownership and permissions ---"
  stat -c '%n owner=%U group=%G mode=%a size=%s' \
    app/main.py \
    app/services/ai_analysis.py \
    /etc/systemd/system/ai-defense-manager.service.d/30-dos-protection.conf

  echo
  echo "--- New source hashes ---"
  sha256sum app/main.py app/services/ai_analysis.py \
    /etc/systemd/system/ai-defense-manager.service.d/30-dos-protection.conf

  echo
  echo "--- systemd configuration verification ---"
  systemd-analyze verify ai-defense-manager.service
  echo "SYSTEMD_VERIFY_EXIT=$?"

  echo
  echo "--- Effective ExecStart ---"
  systemctl show ai-defense-manager.service -p ExecStart

  echo
  echo "--- Existing service state (not restarted) ---"
  systemctl is-active ai-defense-manager.service
fi

echo
echo "BACKUP_DIR=$BACKUP_DIR"
echo "SERVICE_RESTARTED=NO"
echo "OLLAMA_REQUESTED=NO"
echo "WAZUH_REQUESTED=NO"
echo "DATABASE_TEST_WRITES=NO"
```

The SHA256 comparison of the copies of the four files, the Python syntax check and the systemd settings check all passed. The copies are in `/var/backups/ai-defense-manager/dos-protection-20261123-205302`.

### 4.3 Independent Tests (8 Cases)

Without actual communication or Ollama, we test by calling the ASGI middleware and the semaphore directly.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: DOS PROTECTION ISOLATED TESTS ====="

./venv/bin/python - <<'PY'
import asyncio
from unittest.mock import patch

from app.main import RequestBodyLimitMiddleware
import app.services.ai_analysis as ai


MAX = 256 * 1024
passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"{name}=PASS")
    else:
        failed += 1
        print(f"{name}=FAIL")


async def run_middleware(body_chunks, headers=None):
    messages = [
        {
            "type": "http.request",
            "body": chunk,
            "more_body": index < len(body_chunks) - 1,
        }
        for index, chunk in enumerate(body_chunks)
    ]
    if not messages:
        messages = [{"type": "http.request", "body": b"", "more_body": False}]

    index = 0
    received_body = bytearray()
    sent = []

    async def receive():
        nonlocal index
        if index < len(messages):
            message = messages[index]
            index += 1
            return message
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    async def app(scope, receive_inner, send_inner):
        while True:
            message = await receive_inner()
            if message["type"] == "http.disconnect":
                break
            if message["type"] == "http.request":
                received_body.extend(message.get("body", b""))
                if not message.get("more_body", False):
                    break
        await send_inner({
            "type": "http.response.start",
            "status": 200,
            "headers": [],
        })
        await send_inner({
            "type": "http.response.body",
            "body": b"ok",
        })

    middleware = RequestBodyLimitMiddleware(app, MAX)
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/test",
        "headers": headers or [],
    }
    await middleware(scope, receive, send)

    status = next(
        (m["status"] for m in sent if m["type"] == "http.response.start"),
        None,
    )
    return status, bytes(received_body), sent


async def test_middleware():
    status, body, _ = await run_middleware([b"x" * MAX])
    check("BODY_EXACT_LIMIT_ACCEPTED", status == 200 and len(body) == MAX)

    status, body, _ = await run_middleware([b"x" * (MAX + 1)])
    check("BODY_OVER_LIMIT_REJECTED_413", status == 413 and not body)

    status, body, _ = await run_middleware(
        [b"x"],
        [(b"content-length", str(MAX + 1).encode())],
    )
    check("CONTENT_LENGTH_EARLY_REJECTION", status == 413 and not body)

    status, body, _ = await run_middleware([b"a" * 100, b"b" * 200])
    check("CHUNKED_BODY_REPLAY", status == 200 and body == b"a" * 100 + b"b" * 200)

    status, body, _ = await run_middleware(
        [b"x" * 200, b"y" * (MAX - 199)]
    )
    check("CHUNKED_BODY_OVER_LIMIT", status == 413 and not body)


async def test_semaphore():
    active = 0
    maximum_active = 0
    entered = 0
    release = asyncio.Event()

    async def fake_analysis(request):
        nonlocal active, maximum_active, entered
        active += 1
        entered += 1
        maximum_active = max(maximum_active, active)
        if entered == 3:
            release.set()
        await release.wait()
        await asyncio.sleep(0)
        active -= 1
        return "mock-result"

    class DummyRequest:
        pass

    async with ai._ANALYSIS_SEMAPHORE:
        pass

    with patch.object(ai, "_analyze_events_unlimited", fake_analysis):
        tasks = [
            asyncio.create_task(ai.analyze_events(DummyRequest()))
            for _ in range(3)
        ]

        for _ in range(100):
            await asyncio.sleep(0.01)
            if entered == 1:
                break

        first_wave = entered
        check("ANALYSIS_ONLY_ONE_ACTIVE", first_wave == 1 and active == 1)

        release.set()
        results = await asyncio.gather(*tasks)

    check("ANALYSIS_SEMAPHORE_MAX_ONE", maximum_active == 1)
    check("ANALYSIS_WAITERS_COMPLETED", results == ["mock-result"] * 3)


async def main():
    await test_middleware()
    await test_semaphore()

asyncio.run(main())

print(f"TESTS_PASSED={passed}")
print(f"TESTS_FAILED={failed}")
PY

echo
echo "--- Service state (unchanged) ---"
systemctl is-active ai-defense-manager.service

echo
echo "--- Current listener ---"
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "NETWORK_REQUESTS=NO"
echo "OLLAMA_REQUESTED=NO"
echo "WAZUH_REQUESTED=NO"
echo "DATABASE_WRITES=NO"
echo "SERVICE_RESTARTED=NO"
```

| Checked | Result |
|---|---|
| Exactly 256KiB | accepted |
| Over 256KiB | `HTTP 413` |
| Early rejection by Content-Length | succeeded |
| Body sent in chunks | processed correctly |
| Concurrent AI analyses | at most 1 |
| Waiting analyses | finish in order |

**All 8 passed.**

### 4.4 Having systemd Load the Settings

This only loads the new settings, not a restart. The current API process is unaffected.

> **Run on: VM 230**

```bash
echo "===== VM230: DOS PROTECTION SYSTEMD CONFIGURATION LOAD ====="

echo
echo "--- Reload systemd configuration ---"
systemctl daemon-reload
echo "DAEMON_RELOAD_EXIT=$?"

echo
echo "--- Effective service configuration ---"
systemctl cat ai-defense-manager.service

echo
echo "--- Verify unit configuration ---"
systemd-analyze verify ai-defense-manager.service
echo "SYSTEMD_VERIFY_EXIT=$?"

echo
echo "--- Running process ---"
systemctl show ai-defense-manager.service -p MainPID -p ActiveState -p SubState

echo
echo "--- Current listener ---"
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "SERVICE_RESTARTED=NO"
echo "OLLAMA_REQUESTED=NO"
echo "WAZUH_REQUESTED=NO"
echo "DATABASE_WRITES=NO"
```

### 4.5 Restarting

> **Run on: VM 230**

```bash
echo "===== VM230: ACTIVATE DOS PROTECTION ====="

systemctl restart ai-defense-manager.service
RESTART_EXIT=$?

echo "RESTART_EXIT=$RESTART_EXIT"

echo
echo "--- Service status ---"
systemctl status ai-defense-manager.service --no-pager -l

echo
echo "--- Process and listener ---"
systemctl show ai-defense-manager.service \
  -p MainPID -p ActiveState -p SubState

ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "--- Health endpoint ---"
curl --max-time 5 -sS -w '\nHTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "--- Effective Uvicorn arguments ---"
PID="$(systemctl show ai-defense-manager.service -p MainPID --value)"
python3 - "$PID" <<'PY'
import pathlib
import sys

raw = pathlib.Path(f"/proc/{sys.argv[1]}/cmdline").read_bytes()
for arg in raw.decode(errors="replace").split("\0"):
    if arg:
        print(arg)
PY

echo
echo "OLLAMA_CONFIGURATION_CHANGED=NO"
echo "WAZUH_CONFIGURATION_CHANGED=NO"
echo "POSTGRES_CONFIGURATION_CHANGED=NO"
echo "FIREWALL_CONFIGURATION_CHANGED=NO"
```

The restart finished normally, and Uvicorn's new startup arguments included 8 concurrent connections, a backlog of 32 and Keep-Alive 5 seconds. The check right after (9 milliseconds after startup) showed port 8000 not yet listening, and `/health` gave `HTTP 000`.

> **Run on: VM 230**

```bash
echo "===== VM230: DOS PROTECTION POST-RESTART VERIFICATION ====="

echo
echo "--- Wait for listener (maximum 30 seconds) ---"

READY=0
for i in $(seq 1 30); do
    if ss -lnt | grep -q '127.0.0.1:8000'; then
        READY=1
        echo "LISTENER_READY=YES"
        echo "WAIT_SECONDS=$i"
        break
    fi
    sleep 1
done

echo
echo "--- Listener ---"
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "--- Health endpoint ---"
curl --max-time 5 -sS -w '\nHTTP_STATUS=%{http_code}\n' \
    http://127.0.0.1:8000/health

echo
echo "--- Recent startup logs ---"
journalctl -u ai-defense-manager.service -n 35 --no-pager

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "LISTENER_READY=$READY"
```

Uvicorn was PID `1681`, `active`, listening on `127.0.0.1:8000`, `/health` gave `HTTP 200`, and completion of application startup was also confirmed.

### 4.6 Testing the Body Limit on the Running Server

Without connecting to Ollama, Wazuh or the DB, we send requests to a test URL that does not exist.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: LIVE HTTP BODY LIMIT VERIFICATION ====="

./venv/bin/python - <<'PY'
import http.client
import json

HOST = "127.0.0.1"
PORT = 8000
LIMIT = 256 * 1024
PATH = "/__dos_protection_test__"

passed = 0
failed = 0

def check(name, expected, actual):
    global passed, failed
    ok = expected == actual
    print(f"{name}={'PASS' if ok else 'FAIL'} EXPECTED={expected} ACTUAL={actual}")
    if ok:
        passed += 1
    else:
        failed += 1

def fixed_request(body, declared_length=None):
    conn = http.client.HTTPConnection(HOST, PORT, timeout=10)
    headers = {}
    if declared_length is not None:
        headers["Content-Length"] = str(declared_length)
    conn.request("POST", PATH, body=body, headers=headers)
    response = conn.getresponse()
    status = response.status
    response.read()
    conn.close()
    return status

def chunked_request(chunks):
    conn = http.client.HTTPConnection(HOST, PORT, timeout=10)
    conn.putrequest("POST", PATH)
    conn.putheader("Transfer-Encoding", "chunked")
    conn.endheaders()
    for chunk in chunks:
        conn.send(f"{len(chunk):X}\r\n".encode("ascii"))
        conn.send(chunk)
        conn.send(b"\r\n")
    conn.send(b"0\r\n\r\n")
    response = conn.getresponse()
    status = response.status
    response.read()
    conn.close()
    return status

check(
    "HTTP_BODY_EXACT_LIMIT",
    404,
    fixed_request(b"x" * LIMIT),
)

check(
    "HTTP_BODY_OVER_LIMIT",
    413,
    fixed_request(b"x" * (LIMIT + 1)),
)

check(
    "HTTP_CONTENT_LENGTH_EARLY_REJECTION",
    413,
    fixed_request(b"", declared_length=LIMIT + 1),
)

check(
    "HTTP_CHUNKED_BODY_WITHIN_LIMIT",
    404,
    chunked_request([b"a" * 100, b"b" * 200]),
)

check(
    "HTTP_CHUNKED_BODY_OVER_LIMIT",
    413,
    chunked_request([b"a" * 200, b"b" * (LIMIT - 199)]),
)

print(f"TESTS_PASSED={passed}")
print(f"TESTS_FAILED={failed}")
PY

echo
echo "--- Service state ---"
systemctl is-active ai-defense-manager.service

echo
echo "--- Listener ---"
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "OLLAMA_REQUESTED=NO"
echo "WAZUH_REQUESTED=NO"
echo "DATABASE_WRITES=NO"
echo "SERVICE_RESTARTED=NO"
```

| Test | Result |
|---|---|
| Exactly 256KiB | passed (`404`; the body was accepted) |
| Over 256KiB | `HTTP 413`, passed |
| Early rejection by Content-Length | `HTTP 413`, passed |
| Chunked body (within the limit) | passed |
| Chunked body (over the limit) | `HTTP 413`, passed |

**All 5 passed.**

## Closing Notes

In Part 55 we checked VM 230 as a whole and prepared for high request volumes.

| Item | Result |
|---|---|
| Integration tests | all 34 passed (no outside communication) |
| API exposure | `127.0.0.1:8000` only; no application authentication yet |
| Uvicorn | 8 concurrent connections, backlog 32, Keep-Alive 5 seconds (systemd drop-in) |
| AI analysis | one at a time (excess requests wait) |
| HTTP body | up to 256KiB (`413` if exceeded) |
| Tests | 8 independent and 5 on the running server, all passed |

In the next part, Part 56, we start by checking API authentication and authorization, and build token authentication for the API.

# Part 56: Reviewing and Designing API Authentication
## Introduction

### About This Book

This is Part 56 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". By Part 55 we had put in order the input, output and high-volume protection of the AI Defense Manager on VM 230. The major remaining issue is that **the API has no authentication**. Here, before building authentication, we check the following read-only and decide the design.

1. API authentication and authorization, and the paths that reach the API
2. Local account privileges, and protection of credentials and the DB
3. The network boundary (firewall, IPv6, SSH)
4. Where to integrate authentication, and the token scheme

During the build we decided the following.

- The API is designed on the assumption that **it will later also be used from a Web UI on another VM and from management terminals**
- The Web UI VM has not been decided yet, so source IP restrictions will be added once it is

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

## Chapter 1: API Authentication and Paths to the API

### 1.1 Authentication and Authorization

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API AUTHENTICATION AND AUTHORIZATION AUDIT ====="

echo
echo "--- 1. API route files ---"
find app/api -maxdepth 3 -type f -name '*.py' -print | sort

echo
echo "--- 2. Analysis API ---"
if [ -f app/api/analysis.py ]; then
    nl -ba app/api/analysis.py
fi

echo
echo "--- 3. Wazuh API ---"
if [ -f app/api/wazuh.py ]; then
    nl -ba app/api/wazuh.py
fi

echo
echo "--- 4. Main application and middleware ---"
nl -ba app/main.py

echo
echo "--- 5. Authentication and authorization references ---"
grep -RInE \
'AuthenticationMiddleware|BaseHTTPMiddleware|HTTPBearer|HTTPBasic|OAuth2|APIKey|Depends\(|Security\(|authenticate|authorize|permission|current_user|CORS|allow_origins' \
app --include='*.py' \
| grep -vE '(__pycache__|test_)' || true

echo
echo "--- 6. Route declarations ---"
grep -RInE \
'@router\.(get|post|put|delete|patch)|@app\.(get|post|put|delete|patch)' \
app --include='*.py' || true

echo
echo "--- 7. OpenAPI security declaration ---"
./venv/bin/python - <<'PY'
from app.main import app

schema = app.openapi()
print("GLOBAL_SECURITY =", schema.get("security", []))
print("SECURITY_SCHEMES =", schema.get("components", {}).get("securitySchemes", {}))

for path, methods in sorted(schema.get("paths", {}).items()):
    for method, operation in sorted(methods.items()):
        if method.lower() in {"get", "post", "put", "patch", "delete"}:
            print(
                method.upper(),
                path,
                "SECURITY =", operation.get("security", "<not declared>")
            )
PY

echo
echo "--- 8. Runtime exposure ---"
ss -lntp | grep ':8000' || true
systemctl is-active ai-defense-manager.service

echo
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
echo "OLLAMA_REQUESTED=NO"
echo "WAZUH_REQUESTED=NO"
echo "DATABASE_WRITES=NO"
```

| Item | Now | Verdict |
|---|---|---|
| API authentication | none | needs action |
| API authorization | none | needs action |
| OpenAPI Security | not defined | needs action |
| Listening | `127.0.0.1` only | good |
| `/health` | no authentication | acceptable if internal only |
| Body size limit | 256KiB | done |
| Concurrent analysis limit | 1 | done |

Through the analysis APIs, local processes can request Ollama inference and SQLite writes without authentication.

### 1.2 Paths to the API

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API INGRESS AND LOCAL CALLER AUDIT ====="

echo
echo "--- 1. All listening TCP sockets ---"
ss -lntp

echo
echo "--- 2. Current connections to API port ---"
ss -tnp | grep -E '(:8000[[:space:]]|:8000$)' || true

echo
echo "--- 3. Local references to AI Defense API ---"
for DIR in \
    /etc/systemd/system \
    /etc/nginx \
    /etc/apache2 \
    /etc/caddy \
    /etc/cloudflared \
    /opt
do
    if [ -d "$DIR" ]; then
        echo "### $DIR"
        grep -RIlE \
            '127\.0\.0\.1:8000|localhost:8000|ai-defense-manager:8000' \
            "$DIR" \
            --exclude='*.pyc' \
            --exclude-dir=venv \
            --exclude-dir=.git \
            --exclude-dir=__pycache__ \
            2>/dev/null | head -80
    fi
done

echo
echo "--- 4. Proxy service status ---"
for SERVICE in nginx apache2 caddy cloudflared; do
    if systemctl list-unit-files "${SERVICE}.service" --no-legend 2>/dev/null | grep -q "${SERVICE}.service"; then
        printf '%s: ' "$SERVICE"
        systemctl is-active "${SERVICE}.service" 2>/dev/null || true
    fi
done

echo
echo "--- 5. Local user accounts with interactive shells ---"
awk -F: '
    $7 ~ /(bash|sh|zsh)$/ {
        print "USER=" $1, "UID=" $3, "SHELL=" $7
    }
' /etc/passwd

echo
echo "--- 6. AI Defense service identity and permissions ---"
systemctl show ai-defense-manager.service \
    -p User -p Group -p MainPID -p ProtectSystem \
    -p ProtectHome -p NoNewPrivileges

namei -l /opt/ai-defense-manager/app/main.py
namei -l /opt/ai-defense-manager/data/ai-defense.db

echo
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
echo "CREDENTIALS_READ=NO"
echo "DATABASE_ACCESSED=NO"
```

No Nginx, Apache, Caddy or Cloudflared is running on VM 230, and no existing client that calls the API was found. SSH listens on all IPv4 and IPv6 interfaces. The main current threat is not direct access from outside but **unauthorized use by local accounts and processes inside VM 230**.

## Chapter 2: Accounts, Credentials and the DB

### 2.1 Local Account Privileges

Passwords and SSH secret keys are not displayed.

> **Run on: VM 230**

```bash
echo "===== VM230: LOCAL ACCOUNT PRIVILEGE AUDIT ====="

echo
echo "--- 1. Interactive account identity ---"
id aidefense
getent passwd aidefense
passwd -S aidefense

echo
echo "--- 2. Service account identity ---"
id ai-defense
getent passwd ai-defense
passwd -S ai-defense

echo
echo "--- 3. Administrative groups ---"
getent group sudo
getent group adm
getent group docker
getent group lxd

echo
echo "--- 4. Sudo privileges for aidefense ---"
sudo -n -l -U aidefense 2>&1

echo
echo "--- 5. Sudoers configuration references ---"
grep -RInE 'aidefense|ai-defense|ALL[[:space:]]*=' \
    /etc/sudoers /etc/sudoers.d \
    2>/dev/null | sed -E 's/(NOPASSWD:|PASSWD:)/[SUDO_TAG]/g'

echo
echo "--- 6. Relevant running processes ---"
ps -eo user,pid,ppid,comm --sort=user \
    | grep -E '^(USER|root|aidefense|ai-defense)'

echo
echo "--- 7. AI Defense service account isolation ---"
systemctl show ai-defense-manager.service \
    -p User -p Group -p SupplementaryGroups \
    -p NoNewPrivileges -p CapabilityBoundingSet \
    -p AmbientCapabilities -p ProtectSystem \
    -p ProtectHome -p PrivateTmp -p PrivateDevices

echo
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
echo "CREDENTIAL_CONTENTS_DISPLAYED=NO"
echo "SSH_PRIVATE_KEYS_READ=NO"
```

| Account | Privileges |
|---|---|
| `aidefense` (used for login) | `sudo` (can become root), `lxd`, `adm` |
| `ai-defense` (for the service) | `/usr/sbin/nologin`, only its dedicated group |

`aidefense` is effectively an administrator, so adding authentication to the API does not prevent this account from becoming root. The purpose of authentication is to prevent unauthorized calls from ordinary users and local processes with limited privileges. `sudo` and `lxd` may be needed for operation, so they are not changed.

### 2.2 Protection of Credentials

> **Run on: VM 230**

```bash
echo "===== VM230: SERVICE CREDENTIAL PERMISSION AUDIT ====="

echo
echo "--- 1. Service credential configuration ---"
systemctl show ai-defense-manager.service \
    -p LoadCredential \
    -p LoadCredentialEncrypted \
    -p EnvironmentFiles

echo
echo "--- 2. Credential directory metadata ---"
for DIR in \
    /etc/ai-defense-manager \
    /etc/ai-defense-manager/credentials \
    /run/credentials/ai-defense-manager.service
do
    if [ -e "$DIR" ]; then
        stat -c '%A %a %U:%G %n' "$DIR"
        namei -l "$DIR"
    else
        echo "NOT_FOUND=$DIR"
    fi
done

echo
echo "--- 3. Credential file metadata only ---"
for DIR in \
    /etc/ai-defense-manager/credentials \
    /run/credentials/ai-defense-manager.service
do
    if [ -d "$DIR" ]; then
        find "$DIR" -maxdepth 1 -type f \
            -printf '%M %u:%g %s bytes %f\n'
    fi
done

echo
echo "--- 4. Access checks as service account ---"
for PATH_TO_CHECK in \
    /etc/ai-defense-manager/credentials \
    /run/credentials/ai-defense-manager.service
do
    if [ -e "$PATH_TO_CHECK" ]; then
        runuser -u aidefense -- test -r "$PATH_TO_CHECK"
        echo "AIDEFENSE_READ_ACCESS $PATH_TO_CHECK=$?"
    fi
done

echo
echo "--- 5. Access checks as service identity ---"
for PATH_TO_CHECK in \
    /etc/ai-defense-manager/credentials \
    /run/credentials/ai-defense-manager.service
do
    if [ -e "$PATH_TO_CHECK" ]; then
        runuser -u ai-defense -- test -r "$PATH_TO_CHECK"
        echo "AI_DEFENSE_READ_ACCESS $PATH_TO_CHECK=$?"
    fi
done

echo
echo "--- 6. Service executable and application permissions ---"
namei -l /opt/ai-defense-manager/venv/bin/uvicorn
namei -l /opt/ai-defense-manager/app/services/ai_analysis.py

echo
echo "CREDENTIAL_CONTENTS_DISPLAYED=NO"
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Target | State |
|---|---|
| `/etc/ai-defense-manager/credentials` | `root:ai-defense`, `750` |
| Relay token, CA certificate | `640` |
| Readable by `ai-defense` | yes |
| Readable by `aidefense` (ordinary privileges) | no |
| Application Python sources | `root:ai-defense`, `640` |

### 2.3 How Credentials Are Passed, and the DB

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: SYSTEMD CREDENTIAL DELIVERY INSPECTION ====="

echo
echo "--- 1. LoadCredential directives (paths only) ---"
systemctl cat ai-defense-manager.service \
  | grep -E '^[[:space:]]*LoadCredential(Encrypted)?=' \
  | sed -E 's/(:[^:]*\/[^:]*)$/:[PATH_REDACTED]/'

echo
echo "--- 2. Credential environment variable ---"
PID="$(systemctl show ai-defense-manager.service -p MainPID --value)"
python3 - "$PID" <<'PY'
import pathlib
import sys

pid = sys.argv[1]
env = pathlib.Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
for item in env:
    if item.startswith(b"CREDENTIALS_DIRECTORY="):
        print("CREDENTIALS_DIRECTORY is configured")
        print("PATH=" + item.split(b"=", 1)[1].decode(errors="replace"))
        break
else:
    print("CREDENTIALS_DIRECTORY is NOT present")
PY

echo
echo "--- 3. Config credential handling (values redacted) ---"
sed -n '1,45p' app/core/config.py \
  | sed -E \
    -e '/wazuh_relay_token/s/=.*/=[REDACTED]/' \
    -e '/password/s/=.*/=[REDACTED]/' \
    -e '/secret/s/=.*/=[REDACTED]/'

echo
echo "--- 4. Relay credential loading implementation ---"
sed -n '110,155p' app/services/wazuh_relay.py \
  | sed -E \
    -e 's/(token[[:space:]]*=[[:space:]]*).*/\1[REDACTED]/' \
    -e 's/(read_text|read_bytes).*/\1([REDACTED])/'

echo
echo "--- 5. Credential directory and files ---"
find /etc/ai-defense-manager/credentials \
  -maxdepth 1 -type f \
  -printf '%M %u:%g %s bytes %f\n'

echo
echo "--- 6. Current service state ---"
systemctl is-active ai-defense-manager.service
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "CREDENTIAL_VALUES_DISPLAYED=NO"
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
```

- systemd `LoadCredential` is not used, and the running process has no `CREDENTIALS_DIRECTORY`
- The Relay credentials are read directly from `/etc/ai-defense-manager/credentials/` and protected by file permissions
- `aidefense` has no direct access to the Relay credentials directory or to the DB files and directory

API authentication tokens are managed separately from the Relay token.

## Chapter 3: The Network Boundary

### 3.1 Interfaces and Listening Ports

> **Run on: VM 230**

```bash
echo "===== VM230: INTERNAL API NETWORK BOUNDARY AUDIT ====="

echo
echo "--- 1. Network interfaces ---"
ip -br address

echo
echo "--- 2. IPv4 routes ---"
ip -4 route show

echo
echo "--- 3. IPv6 routes ---"
ip -6 route show

echo
echo "--- 4. Neighbor table ---"
ip neigh show

echo
echo "--- 5. Firewall service status ---"
for SERVICE in ufw firewalld nftables; do
    printf '%s: ' "$SERVICE"
    systemctl is-active "${SERVICE}.service" 2>/dev/null || true
done

echo
echo "--- 6. UFW status ---"
if command -v ufw >/dev/null 2>&1; then
    ufw status verbose
else
    echo "UFW_NOT_INSTALLED"
fi

echo
echo "--- 7. nftables ruleset (if available) ---"
if command -v nft >/dev/null 2>&1; then
    nft list ruleset
else
    echo "NFT_NOT_INSTALLED"
fi

echo
echo "--- 8. Current listening sockets ---"
ss -lntup

echo
echo "NETWORK_CONFIGURATION_CHANGED=NO"
echo "FIREWALL_CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
```

VM 230 is `192.168.0.221/24`, and the API listens only on `127.0.0.1:8000`. Other VMs cannot connect to port 8000 directly. We do not suddenly change the API to `0.0.0.0:8000`.

### 3.2 Firewall and IPv6

> **Run on: VM 230**

```bash
echo "===== VM230: KERNEL FIREWALL AND IPV6 SECURITY AUDIT ====="

echo
echo "--- 1. IPv4 iptables rules ---"
if command -v iptables-save >/dev/null 2>&1; then
    iptables-save
else
    echo "IPTABLES_SAVE_NOT_AVAILABLE"
fi

echo
echo "--- 2. IPv6 ip6tables rules ---"
if command -v ip6tables-save >/dev/null 2>&1; then
    ip6tables-save
else
    echo "IP6TABLES_SAVE_NOT_AVAILABLE"
fi

echo
echo "--- 3. Firewall backend ---"
iptables --version 2>/dev/null || true
ip6tables --version 2>/dev/null || true

echo
echo "--- 4. UFW unit details ---"
systemctl show ufw.service \
  -p ActiveState -p SubState -p UnitFileState -p ExecStart \
  --no-pager

echo
echo "--- 5. IPv4/IPv6 forwarding settings ---"
sysctl net.ipv4.ip_forward \
       net.ipv6.conf.all.forwarding \
       net.ipv6.conf.default.forwarding \
       net.ipv6.conf.enp6s18.forwarding

echo
echo "--- 6. IPv6 address scope ---"
ip -6 address show dev enp6s18

echo
echo "FIREWALL_CONFIGURATION_CHANGED=NO"
echo "NETWORK_CONFIGURATION_CHANGED=NO"
```

| Item | Result | Assessment |
|---|---|---|
| API listening | `127.0.0.1:8000` | good |
| IPv4 iptables | no rules | needs measures |
| IPv6 ip6tables | no rules | needs measures |
| nftables | iptables-compatible, no actual rules | — |
| UFW | enabled but shown as `inactive` | investigate |
| IPv4/IPv6 forwarding | 0 (disabled) | good |
| IPv6 address | global | caution |

No inbound filtering inside VM 230 could be confirmed. We cannot say that firewalls on Proxmox or the upstream router are also disabled, but we treat this as a remaining issue (Chapter 6 of the Operations Manual).

### 3.3 SSH

> **Run on: VM 230**

```bash
echo "===== VM230: SSH EXPOSURE AND AUTHENTICATION AUDIT ====="

echo
echo "--- 1. SSH effective authentication settings ---"
sshd -T 2>/dev/null | grep -E \
'^(port|addressfamily|listenaddress|permitrootlogin|passwordauthentication|pubkeyauthentication|kbdinteractiveauthentication|authenticationmethods|allowusers|allowgroups|denyusers|denygroups) '

echo
echo "--- 2. SSH configuration files (security settings only) ---"
grep -RniE \
'^[[:space:]]*(PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|KbdInteractiveAuthentication|AuthenticationMethods|AllowUsers|AllowGroups|DenyUsers|DenyGroups|ListenAddress|Port)[[:space:]]' \
/etc/ssh/sshd_config /etc/ssh/sshd_config.d 2>/dev/null

echo
echo "--- 3. Current SSH connections ---"
ss -tnp state established '( sport = :22 or dport = :22 )'

echo
echo "--- 4. SSH service status ---"
systemctl is-active ssh.service 2>/dev/null || \
systemctl is-active sshd.service 2>/dev/null

echo
echo "--- 5. SSH listening sockets ---"
ss -lntp '( sport = :22 )'

echo
echo "--- 6. Proxmox guest firewall configuration visibility ---"
if command -v systemd-detect-virt >/dev/null 2>&1; then
    systemd-detect-virt
fi

echo
echo "SSH_CONFIGURATION_CHANGED=NO"
echo "FIREWALL_CONFIGURATION_CHANGED=NO"
```

The settings were `PermitRootLogin no`, `PasswordAuthentication no` (`00-local-hardening.conf`), `PubkeyAuthentication yes` and `KbdInteractiveAuthentication no`.

> **Run on: VM 230**

```bash
echo "===== VM230: SSH SYSTEMD SOCKET ACTIVATION AUDIT ====="

echo
echo "--- 1. SSH-related units ---"
systemctl list-units --all --no-legend | grep -E 'ssh|sshd' || true

echo
echo "--- 2. SSH socket status ---"
systemctl status ssh.socket sshd.socket --no-pager 2>&1

echo
echo "--- 3. SSH socket unit configuration ---"
systemctl cat ssh.socket sshd.socket 2>&1

echo
echo "--- 4. Socket properties ---"
for UNIT in ssh.socket sshd.socket; do
    echo "[$UNIT]"
    systemctl show "$UNIT" \
      -p LoadState -p ActiveState -p SubState \
      -p Listen -p BindIPv6Only -p Triggers \
      --no-pager 2>/dev/null
done

echo
echo "--- 5. SSH daemon binary and configuration validation ---"
command -v sshd
/usr/sbin/sshd -t 2>&1
echo "SSHD_CONFIG_TEST_EXIT=$?"

echo
echo "--- 6. Effective SSH configuration ---"
/usr/sbin/sshd -T 2>&1 | grep -E \
'^(port|addressfamily|listenaddress|permitrootlogin|passwordauthentication|pubkeyauthentication|kbdinteractiveauthentication|authenticationmethods) '
echo "SSHD_EFFECTIVE_CONFIG_PIPE_EXIT=${PIPESTATUS[0]}"

echo
echo "SSH_CONFIGURATION_CHANGED=NO"
echo "SOCKET_CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED=NO"
```

On VM 230, `ssh.service` does not run all the time; `ssh.socket` holds port 22 and starts `ssh.service` when a connection arrives (IPv4 `0.0.0.0:22`, IPv6 `[::]:22`). Even when `ssh.service` is `inactive`, SSH is not stopped.

> **Run on: VM 230**

```bash
echo "===== VM230: SSH SERVICE RUNTIME CONFIGURATION AUDIT ====="

echo
echo "--- 1. SSH service unit ---"
systemctl cat ssh.service

echo
echo "--- 2. SSH service effective properties ---"
systemctl show ssh.service \
  -p LoadState \
  -p ActiveState \
  -p SubState \
  -p ExecStart \
  -p ExecStartPre \
  -p RuntimeDirectory \
  -p RuntimeDirectoryMode \
  -p User \
  -p Group \
  --no-pager

echo
echo "--- 3. Runtime privilege separation directory ---"
if [ -e /run/sshd ]; then
    stat -c '%A %U:%G %n' /run/sshd
else
    echo "/run/sshd DOES NOT EXIST"
fi

echo
echo "--- 4. SSH configuration include order ---"
grep -nE '^[[:space:]]*(Include|Match|Port|AddressFamily|ListenAddress|PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|KbdInteractiveAuthentication|AuthenticationMethods)' \
  /etc/ssh/sshd_config \
  /etc/ssh/sshd_config.d/*.conf 2>/dev/null

echo
echo "--- 5. SSH socket activation dependencies ---"
systemctl list-dependencies ssh.socket --no-pager

echo
echo "SSH_CONFIGURATION_CHANGED=NO"
echo "RUNTIME_DIRECTORY_CREATED=NO"
echo "SERVICE_RESTARTED=NO"
```

`/run/sshd` is created by systemd when `ssh.service` starts (`RuntimeDirectory`). The configuration files are read in the order `00-local-hardening.conf`, `50-cloud-init.conf`, and OpenSSH uses the first value set, so `PasswordAuthentication no` takes precedence. The SSH settings are not changed.

## Chapter 4: Designing Authentication

### 4.1 Where to Integrate

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API AUTHENTICATION IMPLEMENTATION PRECHECK ====="

echo
echo "--- 1. Main application structure ---"
sed -n '1,260p' app/main.py

echo
echo "--- 2. API route declarations ---"
grep -RniE \
'^[[:space:]]*(@router\.|router[[:space:]]*=|include_router|def |async def )' \
app/api app/main.py 2>/dev/null

echo
echo "--- 3. Authentication and security references ---"
grep -RniE \
'HTTPBearer|HTTPAuthorizationCredentials|OAuth2|APIKey|Depends|Security\(|middleware|exception_handler|status_code' \
app --include='*.py' 2>/dev/null

echo
echo "--- 4. API schema files ---"
find app/schemas -maxdepth 2 -type f -name '*.py' -printf '%p\n' | sort

echo
echo "--- 5. Test directory structure ---"
find . -maxdepth 3 -type f \
  \( -path './tests/*' -o -name 'conftest.py' \) \
  -printf '%p\n' | sort | head -200

echo
echo "--- 6. Existing API test references ---"
grep -RniE \
'/api/v1/analysis|/api/v1/wazuh|/health|TestClient|AsyncClient|Authorization|401|403' \
tests --include='*.py' 2>/dev/null | head -200

echo
echo "--- 7. Installed test dependencies ---"
./venv/bin/python -m pip show pytest pytest-asyncio httpx fastapi pydantic-settings 2>/dev/null \
  | grep -E '^(Name|Version):'

echo
echo "--- 8. Service status ---"
systemctl is-active ai-defense-manager.service
systemctl show ai-defense-manager.service -p MainPID -p ActiveState -p SubState --no-pager

echo
echo "SOURCE_FILES_CHANGED=NO"
echo "TESTS_EXECUTED=NO"
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "WAZUH_RELAY_ACCESSED=NO"
```

- There are two API routers (`/api/v1`: AI analysis; `/api/v1/wazuh`: Wazuh event retrieval and analysis)
- There is no authentication middleware, `Depends`, `HTTPBearer` or the like yet
- `/health` is outside the routers and can be separated from authentication
- The body size limit middleware can stay
- There is no `tests/` directory

### 4.2 The Design Decided

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API AUTHENTICATION DESIGN AUDIT ====="

echo
echo "--- 1. Analysis API ---"
sed -n '1,220p' app/api/analysis.py

echo
echo "--- 2. Wazuh API ---"
sed -n '1,240p' app/api/wazuh.py

echo
echo "--- 3. Application settings (secret values redacted) ---"
sed -n '1,180p' app/core/config.py \
  | sed -E '/token|secret|password|credential|api_key/I s/(=).*/\1[REDACTED]/'

echo
echo "--- 4. Project dependency files ---"
for FILE in pyproject.toml requirements.txt requirements-dev.txt setup.cfg tox.ini pytest.ini; do
    if [ -f "$FILE" ]; then
        echo "[$FILE]"
        grep -niE 'fastapi|starlette|pydantic|httpx|pytest|test|uvicorn|cryptography' "$FILE" \
          | sed -E 's/(token|password|secret|key)[^=]*=.*/\1=[REDACTED]/I'
    fi
done

echo
echo "--- 5. Project root files ---"
find . -maxdepth 2 -type f \
  ! -path './venv/*' \
  ! -path './.git/*' \
  -printf '%p\n' | sort | head -160

echo
echo "--- 6. FastAPI documentation routes ---"
./venv/bin/python - <<'PY'
from app.main import app

for route in app.routes:
    methods = sorted(getattr(route, "methods", []) or [])
    print(
        "PATH=", getattr(route, "path", "[unknown]"),
        "METHODS=", ",".join(methods),
        "NAME=", getattr(route, "name", "[unknown]"),
    )

print("DOCS_URL=", app.docs_url)
print("REDOC_URL=", app.redoc_url)
print("OPENAPI_URL=", app.openapi_url)
PY

echo
echo "--- 7. Test tooling availability ---"
for PACKAGE in pytest pytest_asyncio; do
    ./venv/bin/python -c \
      "import importlib.util; print('$PACKAGE:', 'AVAILABLE' if importlib.util.find_spec('$PACKAGE') else 'NOT_INSTALLED')"
done

echo
echo "--- 8. Service state ---"
systemctl is-active ai-defense-manager.service
ss -lntp '( sport = :8000 )'

echo
echo "SOURCE_FILES_CHANGED=NO"
echo "DATABASE_ACCESSED=NO"
echo "OLLAMA_ACCESSED=NO"
echo "WAZUH_RELAY_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Target | Now | Policy |
|---|---|---|
| AI analysis API | no authentication | requires authentication (`analyze`) |
| Wazuh event retrieval | no authentication | requires authentication (`read`) |
| Wazuh analysis | no authentication | requires authentication (`analyze`) |
| `/health` | no authentication | unchanged |
| `/docs`, `/redoc`, `/openapi.json` | no authentication | disabled in production |
| Per-client revocation | none | build it |
| Separation of privileges | none | build it (`read`, `analyze`) |

The token scheme is as follows.

- Issue an unguessable random Bearer token per client
- Store only the SHA-256 hash in SQLite, not the token itself
- Use `hmac.compare_digest` for comparison
- Give tokens expiry and revocation
- Keep them completely separate from the Relay token
- Do not give the LLM credentials or execution privileges
- Keep the API on `127.0.0.1:8000`; when used from other VMs, provide a separate entry point with TLS

## Closing Notes

In Part 56 we carried out the checks before building API authentication and decided the design.

| Item | Result |
|---|---|
| API | no authentication or authorization; `127.0.0.1:8000` only |
| Accounts | `aidefense` is an administrator, `ai-defense` is service-only (privileges are separated) |
| Credentials | protected by file permissions (`root:ai-defense`, `640`) |
| Network | no firewall rules inside VM 230 (an issue); SSH is socket-activated with password authentication disabled |
| Authentication design | per-client Bearer tokens (`read`, `analyze`), stored as hashes, with revocation and expiry; documentation APIs disabled |

In the next part, Part 57, we build token authentication and test it in an independent environment.

# Part 57: Building Token Authentication for the API
## Introduction

### About This Book

This is Part 57 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". Following the design decided in Part 56, we build token authentication for the AI Defense Manager API and test it in an independent environment that does not use the production DB.

| Target | Details |
|---|---|
| Storage | add a dedicated authentication table `api_tokens` to the existing `ai-defense.db`; store only the SHA-256 hash of tokens, never plaintext |
| Tokens | generated with a cryptographic random number equivalent to 256 bits |
| Issuing | a root-only CLI (`/usr/local/sbin/aidm-api-token`) issues, revokes and lists. The plaintext token is written once to a root-only file (`600`) and never shown on screen or in logs |
| Privileges (scopes) | `read` (fetching Wazuh events), `analyze` (analysis) |
| Not authenticated | `/health` |
| Disabled | `/docs`, `/redoc`, `/openapi.json` |
| Service | stays as `ai-defense`, reads hashes from the DB |

The existing tables and data for analysis history, evidence, approvals and audit logs, and the Relay credentials, are not changed. In this part there is no service restart, no production token issuance, no Wazuh retrieval and no Ollama inference.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

## Chapter 1: Checks and Copies Before the Change

### 1.1 Structure of the Existing DB

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: AUTH TOKEN STORAGE IMPLEMENTATION PRECHECK ====="

echo
echo "--- 1. Existing database initialization and connection code ---"
sed -n '1,300p' app/services/analysis_history.py

echo
echo "--- 2. SQLite schema (read-only, schema only) ---"
./venv/bin/python - <<'PY'
import sqlite3

path = "/opt/ai-defense-manager/data/ai-defense.db"
db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)

for row in db.execute("""
    SELECT type, name, sql
    FROM sqlite_master
    WHERE type IN ('table', 'index', 'trigger')
    ORDER BY type, name
"""):
    kind, name, sql = row
    print(f"\n[{kind}] {name}")
    print(sql or "[SQL NOT AVAILABLE]")

db.close()
print("\nDATABASE_OPENED_READ_ONLY=YES")
PY

echo
echo "--- 3. Database file and directory metadata ---"
stat -c '%A %U:%G %s bytes %n' \
  data data/ai-defense.db

echo
echo "--- 4. SQLite usage throughout application ---"
grep -RniE \
'sqlite3\.connect|CREATE TABLE|CREATE INDEX|BEGIN|COMMIT|ROLLBACK|PRAGMA|row_factory' \
app --include='*.py' 2>/dev/null

echo
echo "--- 5. Dependency lock references ---"
grep -niE \
'^(fastapi|starlette|httpx|pydantic|pydantic-settings|uvicorn|pytest|pytest-asyncio|argon2|bcrypt|cryptography)([=<>!~; ]|$)' \
requirements.lock 2>/dev/null || true

echo
echo "--- 6. Python runtime and standard crypto support ---"
./venv/bin/python - <<'PY'
import sys
import sqlite3
import hashlib
import secrets
import hmac

print("PYTHON_VERSION=", sys.version.split()[0])
print("SQLITE_VERSION=", sqlite3.sqlite_version)
print("SHA256_AVAILABLE=", hashlib.sha256 is not None)
print("SECURE_TOKEN_GENERATOR_AVAILABLE=", callable(secrets.token_urlsafe))
print("CONSTANT_TIME_COMPARE_AVAILABLE=", callable(hmac.compare_digest))
PY

echo
echo "--- 7. Existing command-line entry points ---"
find . -maxdepth 3 -type f \
  ! -path './venv/*' \
  ! -path './.git/*' \
  \( -name '__main__.py' -o -name 'manage.py' -o -name '*cli*.py' \) \
  -printf '%p\n' | sort

echo
echo "--- 8. Current service state ---"
systemctl is-active ai-defense-manager.service
systemctl show ai-defense-manager.service \
  -p MainPID -p ActiveState -p SubState --no-pager

echo
echo "DATABASE_WRITTEN=NO"
echo "SOURCE_FILES_CHANGED=NO"
echo "PACKAGES_INSTALLED=NO"
echo "SERVICE_RESTARTED=NO"
```

### 1.2 Copying the Application and the DB

SQLite is copied with its dedicated Backup API, without writing to the original DB.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API AUTH IMPLEMENTATION PRECHANGE BACKUP ====="

BACKUP_DIR="/var/backups/ai-defense-manager/api-auth-20261124"

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

echo
echo "--- 1. Backup application source ---"
tar --exclude='./venv' --exclude='./data' --exclude='./.git' \
    -czf "$BACKUP_DIR/application-source.tar.gz" \
    app requirements.lock

echo
echo "--- 2. Create consistent SQLite backup ---"
./venv/bin/python - "$BACKUP_DIR/ai-defense.db" <<'PY'
import sqlite3
import sys
from pathlib import Path

source = Path("/opt/ai-defense-manager/data/ai-defense.db")
target = Path(sys.argv[1])

src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
dst = sqlite3.connect(target)

try:
    src.backup(dst)
    result = dst.execute("PRAGMA integrity_check").fetchone()[0]
    print("BACKUP_INTEGRITY_CHECK=", result)
    print("BACKUP_TABLE_COUNT=", dst.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table'"
    ).fetchone()[0])
finally:
    dst.close()
    src.close()
PY

echo
echo "--- 3. Restrict backup permissions ---"
chown -R root:root "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
chmod 600 "$BACKUP_DIR"/*

echo
echo "--- 4. Backup hashes ---"
cd "$BACKUP_DIR"
sha256sum application-source.tar.gz ai-defense.db | tee SHA256SUMS
sha256sum -c SHA256SUMS

echo
echo "--- 5. Backup metadata ---"
stat -c '%A %U:%G %s bytes %n' "$BACKUP_DIR" "$BACKUP_DIR"/*

echo
echo "SOURCE_DATABASE_MODIFIED=NO"
echo "SOURCE_FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

SQLite `integrity_check` was `ok`, there are six existing tables, and the SHA-256 comparison of the copied files succeeded.

### 1.3 Where to Integrate, and Settings

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: AUTH INTEGRATION SOURCE INSPECTION ====="

echo
echo "--- 1. Application entry point ---"
sed -n '1,260p' app/main.py

echo
echo "--- 2. Analysis API router ---"
sed -n '1,260p' app/api/analysis.py

echo
echo "--- 3. Wazuh API router ---"
sed -n '1,320p' app/api/wazuh.py

echo
echo "--- 4. Existing package layout ---"
find app -maxdepth 3 -type f -name '*.py' -printf '%p\n' | sort

echo
echo "--- 5. Service account access to source and database ---"
namei -l app/main.py
namei -l data/ai-defense.db
id ai-defense

echo
echo "--- 6. systemd service configuration (credential values redacted) ---"
systemctl cat ai-defense-manager.service |
  sed -E \
  -e 's/(EnvironmentFile=).*/\1[REDACTED]/' \
  -e 's/(Environment=)[^ ]*(TOKEN|PASSWORD|SECRET|KEY)[^ ]*/\1[REDACTED]/Ig' \
  -e 's/(LoadCredentialEncrypted?=).*/\1[REDACTED]/'

echo
echo "--- 7. Existing API route imports and dependencies ---"
grep -RniE \
'Depends\(|Security\(|HTTPBearer|APIKey|APIRouter|include_router|FastAPI\(' \
app --include='*.py' 2>/dev/null

echo
echo "SOURCE_FILES_CHANGED=NO"
echo "DATABASE_WRITTEN=NO"
echo "SERVICE_RESTARTED=NO"
```

The service account `ai-defense` can read and write the DB but only read the application sources. We keep this separation. Verification looks up the DB record by the token ID and compares the hash of the secret part with `hmac.compare_digest()`.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: AUTH CONFIGURATION AND CLI PRECHECK ====="

echo
echo "--- 1. Application settings ---"
sed -n '1,280p' app/core/config.py

echo
echo "--- 2. Existing directory permissions ---"
namei -l /opt/ai-defense-manager
namei -l /opt/ai-defense-manager/app
namei -l /usr/local/sbin

echo
echo "--- 3. Existing Python CLI conventions ---"
find app -maxdepth 2 -type d -printf '%M %u:%g %p\n' | sort

echo
echo "--- 4. FastAPI and Starlette test-client availability ---"
./venv/bin/python - <<'PY'
import importlib.util
import fastapi
import starlette
import httpx

print("FASTAPI_VERSION=", fastapi.__version__)
print("STARLETTE_VERSION=", starlette.__version__)
print("HTTPX_VERSION=", httpx.__version__)
print("STARLETTE_TESTCLIENT_AVAILABLE=",
      importlib.util.find_spec("starlette.testclient") is not None)
PY

echo
echo "--- 5. Root-only token storage destination precheck ---"
if [ -e /root/.local/share/ai-defense-manager/tokens ]; then
  stat -c '%A %U:%G %n' /root/.local/share/ai-defense-manager/tokens
else
  echo "TOKEN_DIRECTORY_NOT_CREATED"
fi

echo
echo "--- 6. Existing SQLite database mode ---"
./venv/bin/python - <<'PY'
import sqlite3
p = "/opt/ai-defense-manager/data/ai-defense.db"
c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
print("JOURNAL_MODE=", c.execute("PRAGMA journal_mode").fetchone()[0])
print("FOREIGN_KEYS_DEFAULT=", c.execute("PRAGMA foreign_keys").fetchone()[0])
c.close()
PY

echo
echo "SOURCE_FILES_CHANGED=NO"
echo "DATABASE_WRITTEN=NO"
echo "TOKEN_DIRECTORY_CREATED=NO"
echo "SERVICE_RESTARTED=NO"
```

Python's standard library and FastAPI's test features are all present, so no packages need to be added.

## Chapter 2: Building the Authentication

The existing files were copied in Chapter 1. At this point the authentication table is not created yet.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API TOKEN AUTHENTICATION IMPLEMENTATION ====="

mkdir -p app/cli

cat > app/services/api_tokens.py <<'PY'
"""Database-backed API token management. Plaintext secrets are never stored."""

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.services.analysis_history import DB_PATH


ALLOWED_SCOPES = frozenset({"read", "analyze"})
TOKEN_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
DUMMY_HASH = hashlib.sha256(b"invalid-api-token-secret").hexdigest()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA synchronous = FULL")
    return conn


def initialize_api_token_store() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_tokens (
                token_id TEXT PRIMARY KEY,
                secret_hash TEXT NOT NULL
                    CHECK(length(secret_hash) = 64),
                name TEXT NOT NULL,
                scopes TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked_at TEXT,
                last_used_at TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_tokens_expires_at
            ON api_tokens(expires_at)
        """)


def issue_token(name: str, scopes: set[str], expires_in_days: int):
    name = name.strip()

    if not name or len(name) > 64:
        raise ValueError("Token name must contain 1 to 64 characters")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in name):
        raise ValueError("Token name contains control characters")
    if not scopes or not scopes.issubset(ALLOWED_SCOPES):
        raise ValueError("Invalid token scopes")
    if not isinstance(expires_in_days, int) or not 1 <= expires_in_days <= 365:
        raise ValueError("Expiry must be between 1 and 365 days")

    now = datetime.now(timezone.utc)
    created_at = now.isoformat()
    expires_at = (now + timedelta(days=expires_in_days)).isoformat()

    token_id = secrets.token_hex(16)
    secret = secrets.token_urlsafe(32)
    secret_hash = hashlib.sha256(secret.encode("ascii")).hexdigest()
    plaintext_token = f"{token_id}.{secret}"

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO api_tokens (
                token_id, secret_hash, name, scopes,
                created_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                token_id,
                secret_hash,
                name,
                json.dumps(sorted(scopes), separators=(",", ":")),
                created_at,
                expires_at,
            ),
        )

    return token_id, plaintext_token


def revoke_token(token_id: str) -> bool:
    if not TOKEN_ID_PATTERN.fullmatch(token_id):
        raise ValueError("Invalid token ID")

    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        cursor = conn.execute(
            """
            UPDATE api_tokens
            SET revoked_at = ?
            WHERE token_id = ? AND revoked_at IS NULL
            """,
            (now, token_id),
        )
        return cursor.rowcount == 1


def list_tokens():
    with _connect() as conn:
        rows = conn.execute("""
            SELECT token_id, name, scopes, created_at,
                   expires_at, revoked_at, last_used_at
            FROM api_tokens
            ORDER BY created_at DESC
        """).fetchall()

    return [
        {
            "token_id": row["token_id"],
            "name": row["name"],
            "scopes": json.loads(row["scopes"]),
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "revoked_at": row["revoked_at"],
            "last_used_at": row["last_used_at"],
        }
        for row in rows
    ]


def verify_token(plaintext_token: str, required_scope: str) -> bool:
    """Return False for invalid tokens; raise PermissionError for missing scope."""

    if required_scope not in ALLOWED_SCOPES:
        return False

    if not isinstance(plaintext_token, str) or len(plaintext_token) > 512:
        hmac.compare_digest(DUMMY_HASH, DUMMY_HASH)
        return False

    token_id, separator, secret = plaintext_token.partition(".")

    if (
        not separator
        or not TOKEN_ID_PATTERN.fullmatch(token_id)
        or not secret
        or len(secret) > 256
    ):
        supplied_hash = hashlib.sha256(b"malformed-token").hexdigest()
        hmac.compare_digest(DUMMY_HASH, supplied_hash)
        return False

    supplied_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()

    with _connect() as conn:
        row = conn.execute(
            """
            SELECT secret_hash, scopes, expires_at, revoked_at
            FROM api_tokens
            WHERE token_id = ?
            """,
            (token_id,),
        ).fetchone()

        expected_hash = row["secret_hash"] if row else DUMMY_HASH
        hash_matches = hmac.compare_digest(expected_hash, supplied_hash)

        if not row or not hash_matches:
            return False

        if row["revoked_at"] is not None:
            return False

        try:
            expiry = datetime.fromisoformat(row["expires_at"])
            scopes = json.loads(row["scopes"])
        except (ValueError, TypeError):
            return False

        if expiry.tzinfo is None:
            return False

        if datetime.now(timezone.utc) >= expiry:
            return False

        if (
            not isinstance(scopes, list)
            or not all(scope in ALLOWED_SCOPES for scope in scopes)
        ):
            return False

        if required_scope not in scopes:
            raise PermissionError("Insufficient API token scope")

        conn.execute(
            "UPDATE api_tokens SET last_used_at = ? WHERE token_id = ?",
            (datetime.now(timezone.utc).isoformat(), token_id),
        )

    return True
PY

cat > app/core/api_auth.py <<'PY'
"""Bearer-token authentication dependencies for the API."""

import sqlite3

from fastapi import Header, HTTPException

from app.services.api_tokens import verify_token


def require_scope(required_scope: str):
    def dependency(
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> None:
        if not authorization:
            raise HTTPException(
                status_code=401,
                detail="Bearer token required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        scheme, separator, token = authorization.partition(" ")

        if (
            not separator
            or scheme.lower() != "bearer"
            or not token
            or token.strip() != token
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid bearer authorization",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            valid = verify_token(token, required_scope)
        except PermissionError:
            raise HTTPException(
                status_code=403,
                detail="Insufficient API token scope",
            )
        except sqlite3.Error:
            raise HTTPException(
                status_code=503,
                detail="Authentication service temporarily unavailable",
            )

        if not valid:
            raise HTTPException(
                status_code=401,
                detail="Invalid, expired, or revoked bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return dependency
PY

cat > app/cli/__init__.py <<'PY'
"""Administrative command-line tools."""
PY

cat > app/cli/api_tokens.py <<'PY'
"""Root-only API token administration CLI."""

import argparse
import os
import stat
import sys
from pathlib import Path

from app.services.api_tokens import (
    initialize_api_token_store,
    issue_token,
    list_tokens,
    revoke_token,
)


DEFAULT_TOKEN_DIR = Path(
    "/root/.local/share/ai-defense-manager/tokens"
)


def _require_root():
    if os.geteuid() != 0:
        raise PermissionError("This command must be run as root")


def _write_token_file(token: str, output: Path) -> None:
    directory = output.parent
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)

    directory_stat = directory.stat()
    if directory_stat.st_uid != 0:
        raise PermissionError("Token directory must be owned by root")

    os.chmod(directory, 0o700)

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)

    fd = os.open(output, flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="ascii") as stream:
            fd = -1
            stream.write(token + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if fd >= 0:
            os.close(fd)


def main():
    parser = argparse.ArgumentParser(
        prog="aidm-api-token",
        description="Root-only AI Defense Manager API token administration",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    issue = sub.add_parser("issue")
    issue.add_argument("--name", required=True)
    issue.add_argument(
        "--scopes",
        required=True,
        help="Comma-separated scopes: read,analyze",
    )
    issue.add_argument(
        "--expires-in-days",
        type=int,
        default=90,
    )
    issue.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_TOKEN_DIR / "issued-token.txt",
    )

    sub.add_parser("list")

    revoke = sub.add_parser("revoke")
    revoke.add_argument("--token-id", required=True)

    args = parser.parse_args()

    try:
        _require_root()
        initialize_api_token_store()

        if args.command == "issue":
            scopes = {
                item.strip()
                for item in args.scopes.split(",")
                if item.strip()
            }

            token_id, plaintext = issue_token(
                args.name,
                scopes,
                args.expires_in_days,
            )

            try:
                _write_token_file(plaintext, args.output)
            except Exception:
                revoke_token(token_id)
                raise

            print("TOKEN_ISSUED=YES")
            print("TOKEN_ID=", token_id)
            print("TOKEN_FILE=", args.output)
            print("TOKEN_VALUE=NOT_DISPLAYED")
            print("TOKEN_FILE_MODE=0600")

        elif args.command == "list":
            for item in list_tokens():
                print(
                    "TOKEN_ID={token_id} NAME={name!r} "
                    "SCOPES={scopes} CREATED={created_at} "
                    "EXPIRES={expires_at} REVOKED={revoked_at} "
                    "LAST_USED={last_used_at}".format(**item)
                )
            print("TOKEN_SECRET_VALUES=NOT_STORED_OR_DISPLAYED")

        elif args.command == "revoke":
            changed = revoke_token(args.token_id)
            print("TOKEN_REVOKED=", "YES" if changed else "NO_CHANGE")

    except Exception as exc:
        print("ERROR:", type(exc).__name__, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY

echo
echo "--- 1. Patch FastAPI application and routers ---"

./venv/bin/python - <<'PY'
from pathlib import Path

main = Path("app/main.py")
analysis = Path("app/api/analysis.py")
wazuh = Path("app/api/wazuh.py")

p = main.read_text()
assert "from app.services.analysis_history import initialize_database" in p
assert "initialize_api_token_store" not in p
p = p.replace(
    "from app.services.analysis_history import initialize_database",
    "from app.services.analysis_history import initialize_database\n"
    "from app.services.api_tokens import initialize_api_token_store",
)
p = p.replace(
    "    initialize_database()\n    yield",
    "    initialize_database()\n"
    "    initialize_api_token_store()\n"
    "    yield",
)
p = p.replace(
    '    version=settings.app_version,\n    lifespan=lifespan,',
    '    version=settings.app_version,\n'
    '    docs_url=None,\n'
    '    redoc_url=None,\n'
    '    openapi_url=None,\n'
    '    lifespan=lifespan,',
)
main.write_text(p)

p = analysis.read_text()
assert "from app.core.api_auth import require_scope" not in p
p = p.replace(
    "from fastapi import APIRouter, HTTPException",
    "from fastapi import APIRouter, Depends, HTTPException\n\n"
    "from app.core.api_auth import require_scope",
)
p = p.replace(
    '@router.post(\n    "/analysis",\n    response_model=AIAnalysisProposal,\n)',
    '@router.post(\n'
    '    "/analysis",\n'
    '    response_model=AIAnalysisProposal,\n'
    '    dependencies=[Depends(require_scope("analyze"))],\n'
    ')',
)
assert 'Depends(require_scope("analyze"))' in p
analysis.write_text(p)

p = wazuh.read_text()
assert "from app.core.api_auth import require_scope" not in p
p = p.replace(
    "from fastapi import APIRouter, HTTPException, Query",
    "from fastapi import APIRouter, Depends, HTTPException, Query\n\n"
    "from app.core.api_auth import require_scope",
)
p = p.replace(
    '@router.get("/events", response_model=list[SecurityEvent])',
    '@router.get(\n'
    '    "/events",\n'
    '    response_model=list[SecurityEvent],\n'
    '    dependencies=[Depends(require_scope("read"))],\n'
    ')',
)
p = p.replace(
    '@router.post("/analyze", response_model=AIAnalysisProposal)',
    '@router.post(\n'
    '    "/analyze",\n'
    '    response_model=AIAnalysisProposal,\n'
    '    dependencies=[Depends(require_scope("analyze"))],\n'
    ')',
)
assert 'Depends(require_scope("read"))' in p
assert 'Depends(require_scope("analyze"))' in p
wazuh.write_text(p)

print("MAIN_PATCH=PASS")
print("ANALYSIS_ROUTER_PATCH=PASS")
print("WAZUH_ROUTER_PATCH=PASS")
print("DOCS_DISABLED_IN_SOURCE=YES")
PY

echo
echo "--- 2. Install root-only CLI wrapper ---"

cat > /usr/local/sbin/aidm-api-token <<'SH'
#!/bin/sh
exec /opt/ai-defense-manager/venv/bin/python \
  -m app.cli.api_tokens "$@"
SH

chown root:root /usr/local/sbin/aidm-api-token
chmod 700 /usr/local/sbin/aidm-api-token

echo
echo "--- 3. Compile all application Python files ---"
./venv/bin/python -m compileall -q app
echo "PYTHON_COMPILE=PASS"

echo
echo "--- 4. Verify systemd unit syntax (no restart) ---"
systemd-analyze verify \
  /etc/systemd/system/ai-defense-manager.service

echo
echo "--- 5. Verify CLI help without database initialization ---"
/usr/local/sbin/aidm-api-token --help

echo
echo "--- 6. Source file hashes ---"
sha256sum \
  app/main.py \
  app/api/analysis.py \
  app/api/wazuh.py \
  app/core/api_auth.py \
  app/services/api_tokens.py \
  app/cli/__init__.py \
  app/cli/api_tokens.py \
  /usr/local/sbin/aidm-api-token

echo
echo "SOURCE_PATCHED=YES"
echo "DATABASE_SCHEMA_CHANGED=NO"
echo "TOKEN_ISSUED=NO"
echo "SERVICE_RESTARTED=NO"
echo "LIVE_WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
```

| Created | Details |
|---|---|
| `app/services/api_tokens.py` | issuing, verifying, revoking and listing tokens |
| `app/core/api_auth.py` | `require_scope()` (a FastAPI dependency) |
| `app/cli/api_tokens.py` | root-only CLI |
| `/usr/local/sbin/aidm-api-token` | wrapper that runs the CLI (`root:root`, `700`) |
| `app/main.py`, routers | require scopes on the three APIs and disable documentation |

The Python syntax check, the systemd unit check and displaying the CLI help all passed.

## Chapter 3: Testing in an Independent Environment

### 3.1 Testing the Authentication Logic

The test DB is created in a temporary directory and deleted afterwards. There is no connection to the production DB, Wazuh or Ollama.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED API TOKEN AUTHENTICATION TESTS ====="

./venv/bin/python - <<'PY'
import hashlib
import json
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import app.services.api_tokens as tokens

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"{name}=PASS")
    else:
        failed += 1
        print(f"{name}=FAIL")

with tempfile.TemporaryDirectory(prefix="aidm-auth-test-") as tmp:
    db_path = Path(tmp) / "auth-test.db"
    tokens.DB_PATH = str(db_path)

    tokens.initialize_api_token_store()

    # 1. Schema and token issuance
    token_id, plaintext = tokens.issue_token(
        "isolated-test",
        {"read"},
        30,
    )
    check("TOKEN_ISSUANCE", bool(token_id and plaintext))
    check("TOKEN_ID_FORMAT", len(token_id) == 32)

    # 2. Database must contain only the hash, never plaintext
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT secret_hash, scopes FROM api_tokens WHERE token_id=?",
            (token_id,),
        ).fetchone()

    expected_hash = hashlib.sha256(
        plaintext.partition(".")[2].encode("ascii")
    ).hexdigest()

    check("SECRET_HASH_STORED", row is not None and row[0] == expected_hash)
    check("PLAINTEXT_NOT_IN_DATABASE", plaintext.encode() not in db_path.read_bytes())
    check("SCOPES_STORED", row is not None and json.loads(row[1]) == ["read"])

    # 3. Valid token and scope enforcement
    check("VALID_READ_TOKEN", tokens.verify_token(plaintext, "read"))

    try:
        tokens.verify_token(plaintext, "analyze")
        scope_denied = False
    except PermissionError:
        scope_denied = True
    check("INSUFFICIENT_SCOPE_DENIED", scope_denied)

    # 4. Invalid tokens
    check("INVALID_SECRET_REJECTED", not tokens.verify_token(
        token_id + ".incorrect-secret", "read"
    ))
    check("MALFORMED_TOKEN_REJECTED", not tokens.verify_token(
        "not-a-valid-token", "read"
    ))
    check("UNKNOWN_TOKEN_REJECTED", not tokens.verify_token(
        "0" * 32 + ".unknown-secret", "read"
    ))

    # 5. Expiration
    with sqlite3.connect(db_path) as conn:
        expired = (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        ).isoformat()
        conn.execute(
            "UPDATE api_tokens SET expires_at=? WHERE token_id=?",
            (expired, token_id),
        )
    check("EXPIRED_TOKEN_REJECTED", not tokens.verify_token(plaintext, "read"))

    # 6. Revocation
    token_id2, plaintext2 = tokens.issue_token(
        "revoke-test",
        {"read", "analyze"},
        30,
    )
    check("SECOND_TOKEN_VALID", tokens.verify_token(plaintext2, "read"))
    check("REVOCATION_SUCCEEDED", tokens.revoke_token(token_id2))
    check("REVOKED_TOKEN_REJECTED", not tokens.verify_token(plaintext2, "read"))
    check("SECOND_REVOCATION_NO_CHANGE", not tokens.revoke_token(token_id2))

    # 7. Listing must not expose token secrets
    listed = tokens.list_tokens()
    check("TOKEN_LIST_COUNT", len(listed) == 2)
    check(
        "TOKEN_LIST_HAS_NO_SECRET",
        all("secret" not in item and "token" not in item for item in listed),
    )

# 8. FastAPI route configuration (import only; no lifespan/startup)
from app.main import app

routes = {
    (route.path, method): route
    for route in app.routes
    if hasattr(route, "methods")
    for method in route.methods
}

def has_scope_dependency(path, method, expected_scope):
    route = routes.get((path, method))
    if route is None:
        return False

    def walk(dependant):
        for dep in dependant.dependencies:
            call = getattr(dep, "call", None)
            if getattr(call, "__name__", "") == "dependency":
                closure = getattr(call, "__closure__", None) or ()
                values = [
                    cell.cell_contents
                    for cell in closure
                    if isinstance(cell.cell_contents, str)
                ]
                if expected_scope in values:
                    return True
            if walk(dep):
                return True
        return False

    return walk(route.dependant)

check(
    "WAZUH_EVENTS_READ_SCOPE",
    has_scope_dependency("/api/v1/wazuh/events", "GET", "read"),
)
check(
    "ANALYSIS_ANALYZE_SCOPE",
    has_scope_dependency("/api/v1/analysis", "POST", "analyze"),
)
check(
    "WAZUH_ANALYZE_SCOPE",
    has_scope_dependency("/api/v1/wazuh/analyze", "POST", "analyze"),
)

check(
    "HEALTH_ROUTE_EXISTS",
    ("/health", "GET") in routes,
)
check(
    "OPENAPI_DISABLED",
    app.openapi_url is None,
)
check(
    "DOCS_DISABLED",
    app.docs_url is None,
)
check(
    "REDOC_DISABLED",
    app.redoc_url is None,
)

print(f"TESTS_PASSED={passed}")
print(f"TESTS_FAILED={failed}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_DATABASE_CHANGED=NO")
print("WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
PY

echo
echo "===== CURRENT PRODUCTION STATE (READ ONLY) ====="
stat -c '%A %U:%G %n' /opt/ai-defense-manager/data/ai-defense.db
systemctl is-active ai-defense-manager.service
ss -lntp | grep '127.0.0.1:8000' || true
```

Issuing tokens, storing as hashes, rejecting invalid/expired/revoked tokens, and rejecting insufficient scopes all passed.

The scope check of the three routes showed `FAIL`, but this was a problem in the test code (3.2).

### 3.2 Checking Route Registration

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API ROUTE AUTH DEPENDENCY INSPECTION ====="

./venv/bin/python - <<'PY'
from app.main import app

TARGETS = {
    ("/api/v1/wazuh/events", "GET"),
    ("/api/v1/analysis", "POST"),
    ("/api/v1/wazuh/analyze", "POST"),
    ("/health", "GET"),
}

def inspect(dependant, depth=0):
    for dep in dependant.dependencies:
        call = getattr(dep, "call", None)
        name = getattr(call, "__qualname__", repr(call))
        module = getattr(call, "__module__", "")
        print("  " * depth + f"DEPENDENCY={module}.{name}")

        closure = getattr(call, "__closure__", None) or ()
        for cell in closure:
            try:
                value = cell.cell_contents
            except ValueError:
                continue
            if isinstance(value, (str, int, bool)):
                print("  " * (depth + 1) + f"CLOSURE_VALUE={value!r}")

        inspect(dep, depth + 1)

for route in app.routes:
    path = getattr(route, "path", None)
    methods = getattr(route, "methods", set()) or set()

    for method in sorted(methods):
        if (path, method) not in TARGETS:
            continue

        print(f"\nROUTE={method} {path}")
        inspect(route.dependant)

print("\n===== ROUTER SOURCE DECORATORS =====")
for filename in ("app/api/analysis.py", "app/api/wazuh.py"):
    print(f"\n--- {filename} ---")
    lines = open(filename, encoding="utf-8").read().splitlines()
    for i, line in enumerate(lines):
        if "@router." in line:
            start = max(0, i - 1)
            end = min(len(lines), i + 9)
            for n in range(start, end):
                print(f"{n + 1:4}: {lines[n]}")
            print()

print("PRODUCTION_DATABASE_ACCESSED=NO")
print("SOURCE_CHANGED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

In the source, `Depends(require_scope(...))` was written on all three routes.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: FASTAPI ROUTER REGISTRATION INSPECTION ====="

./venv/bin/python - <<'PY'
from app.main import app
from app.api.analysis import router as analysis_router
from app.api.wazuh import router as wazuh_router

def show_routes(label, obj):
    print(f"\n--- {label} ---")
    for index, route in enumerate(obj.routes):
        print(
            "INDEX=", index,
            "TYPE=", type(route).__module__ + "." + type(route).__name__,
            "PATH=", getattr(route, "path", None),
            "METHODS=", sorted(getattr(route, "methods", None) or []),
            "NAME=", getattr(route, "name", None),
        )
        if hasattr(route, "router"):
            nested = route.router
            print(
                "  NESTED_ROUTER=",
                type(nested).__module__ + "." + type(nested).__name__,
                "NESTED_ROUTE_COUNT=",
                len(getattr(nested, "routes", [])),
            )

show_routes("APP ROUTES", app)
show_routes("ANALYSIS ROUTER", analysis_router)
show_routes("WAZUH ROUTER", wazuh_router)

print("\n--- APP ROUTER REGISTRATION SOURCE ---")
from pathlib import Path
lines = Path("app/main.py").read_text().splitlines()
for i, line in enumerate(lines):
    if "include_router" in line or "FastAPI(" in line or "lifespan=" in line:
        for n in range(max(0, i - 2), min(len(lines), i + 4)):
            print(f"{n + 1:4}: {lines[n]}")

print("\n--- FASTAPI ROUTER VERSION DETAILS ---")
import fastapi
import inspect
from fastapi.routing import _IncludedRouter
print("FASTAPI_VERSION=", fastapi.__version__)
print("INCLUDED_ROUTER_CLASS=", _IncludedRouter)
print("INCLUDED_ROUTER_SOURCE=")
print(inspect.getsource(_IncludedRouter))
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("SOURCE_CHANGED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

In FastAPI 0.165.0, routers registered with `include_router()` are expanded later as `_IncludedRouter`. The test code walked `app.routes` directly and so could not find the three API routes. We check again with the expanded routes.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: EFFECTIVE ROUTE AUTH DEPENDENCY AUDIT ====="

./venv/bin/python - <<'PY'
from app.main import app

EXPECTED = {
    ("/api/v1/wazuh/events", "GET"): "read",
    ("/api/v1/analysis", "POST"): "analyze",
    ("/api/v1/wazuh/analyze", "POST"): "analyze",
}

def dependency_tree(dependant, depth=0):
    result = []
    for dep in dependant.dependencies:
        call = getattr(dep, "call", None)
        name = getattr(call, "__qualname__", repr(call))
        module = getattr(call, "__module__", "")
        closure_values = []

        for cell in getattr(call, "__closure__", None) or ():
            try:
                value = cell.cell_contents
            except ValueError:
                continue
            if isinstance(value, str):
                closure_values.append(value)

        result.append((name, module, closure_values))
        result.extend(dependency_tree(dep, depth + 1))
    return result

effective = {}

for branch in app.router.routes:
    if hasattr(branch, "effective_route_contexts"):
        for context in branch.effective_route_contexts():
            route = context.original_route
            for method in getattr(route, "methods", set()) or set():
                effective[(context.path_format, method)] = route

for key, expected_scope in EXPECTED.items():
    route = effective.get(key)
    print(f"\nROUTE={key[1]} {key[0]}")

    if route is None:
        print("ROUTE_FOUND=NO")
        continue

    print("ROUTE_FOUND=YES")
    tree = dependency_tree(route.dependant)

    for name, module, closure_values in tree:
        print(f"DEPENDENCY={module}.{name}")
        print("CLOSURE_VALUES=", closure_values)

    matching = any(
        name == "require_scope.<locals>.dependency"
        and expected_scope in closure_values
        for name, module, closure_values in tree
    )
    print("EXPECTED_SCOPE=", expected_scope)
    print("SCOPE_DEPENDENCY_FOUND=", "YES" if matching else "NO")

print("\n--- HEALTH ROUTE ---")
health = next(
    (
        route for route in app.routes
        if getattr(route, "path", None) == "/health"
    ),
    None,
)
print("HEALTH_ROUTE_FOUND=", health is not None)
if health is not None:
    print("HEALTH_DEPENDENCY_COUNT=", len(health.dependant.dependencies))

print("\nPRODUCTION_DATABASE_ACCESSED=NO")
print("SOURCE_CHANGED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

| API | Required scope | Result |
|---|---|---|
| `GET /api/v1/wazuh/events` | `read` | passed |
| `POST /api/v1/analysis` | `analyze` | passed |
| `POST /api/v1/wazuh/analyze` | `analyze` | passed |
| `GET /health` | none | passed |

### 3.3 Testing Authentication over HTTP

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED HTTP AUTHENTICATION TEST ====="

./venv/bin/python - <<'PY'
import asyncio
import tempfile
from pathlib import Path

import httpx
from fastapi import FastAPI

import app.services.api_tokens as token_service
import app.api.analysis as analysis_api
import app.api.wazuh as wazuh_api
from app.main import app

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"{name}=PASS")
    else:
        failed += 1
        print(f"{name}=FAIL")

async def main():
    global passed, failed

    with tempfile.TemporaryDirectory(prefix="aidm-http-auth-") as tmp:
        token_service.DB_PATH = str(Path(tmp) / "http-auth.db")
        token_service.initialize_api_token_store()

        read_id, read_token = token_service.issue_token(
            "http-read-test", {"read"}, 30
        )
        analyze_id, analyze_token = token_service.issue_token(
            "http-analyze-test", {"analyze"}, 30
        )

        # Replace endpoint work with inert test-only responses.
        original_events = wazuh_api.get_wazuh_events
        original_analysis = analysis_api.create_analysis
        original_wazuh_analysis = wazuh_api.analyze_wazuh_events

        async def fake_events(limit=50, since_minutes=60):
            return []

        async def fake_analysis(request):
            return {"test": "analysis-authorized"}

        async def fake_wazuh_analysis(request):
            return {"test": "wazuh-analysis-authorized"}

        wazuh_api.get_wazuh_events = fake_events
        analysis_api.create_analysis = fake_analysis
        wazuh_api.analyze_wazuh_events = fake_wazuh_analysis

        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://test",
            ) as client:

                # Missing credentials
                r = await client.get("/api/v1/wazuh/events")
                check("NO_TOKEN_READ_401", r.status_code == 401)

                r = await client.post("/api/v1/analysis", json={})
                check("NO_TOKEN_ANALYZE_401", r.status_code == 401)

                # Read token
                headers = {"Authorization": f"Bearer {read_token}"}
                r = await client.get(
                    "/api/v1/wazuh/events", headers=headers
                )
                check("READ_TOKEN_READ_200", r.status_code == 200)

                r = await client.post(
                    "/api/v1/analysis", headers=headers, json={}
                )
                check("READ_TOKEN_ANALYZE_403", r.status_code == 403)

                # Analyze token
                headers = {"Authorization": f"Bearer {analyze_token}"}
                r = await client.post(
                    "/api/v1/analysis", headers=headers, json={}
                )
                check("ANALYZE_TOKEN_ANALYSIS_200", r.status_code == 200)

                r = await client.post(
                    "/api/v1/wazuh/analyze", headers=headers, json={}
                )
                check("ANALYZE_TOKEN_WAZUH_200", r.status_code == 200)

                r = await client.get(
                    "/api/v1/wazuh/events", headers=headers
                )
                check("ANALYZE_TOKEN_READ_401", r.status_code == 401)

                # Health remains unauthenticated.
                r = await client.get("/health")
                check("HEALTH_WITHOUT_TOKEN_200", r.status_code == 200)

                # Documentation endpoints remain disabled.
                for path in ("/docs", "/redoc", "/openapi.json"):
                    r = await client.get(path)
                    check(
                        f"DOCS_DISABLED_{path.replace('/', '_')}",
                        r.status_code == 404,
                    )

        finally:
            wazuh_api.get_wazuh_events = original_events
            analysis_api.create_analysis = original_analysis
            wazuh_api.analyze_wazuh_events = original_wazuh_analysis

asyncio.run(main())

print(f"TESTS_PASSED={passed}")
print(f"TESTS_FAILED={failed}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_DATABASE_CHANGED=NO")
print("LIVE_WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
print("PRODUCTION_SERVICE_RESTARTED=NO")
PY
```

`401` without a token, `403` rejecting the analysis API with a `read` token, and `/health` without authentication passed. The rest were problems with the test's expected values, which we checked as follows.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: AUTH HTTP STATUS DIAGNOSTIC ====="

./venv/bin/python - <<'PY'
import asyncio
import tempfile
from pathlib import Path

import httpx
import app.services.api_tokens as token_service
from app.main import app

async def main():
    with tempfile.TemporaryDirectory(prefix="aidm-auth-diag-") as tmp:
        token_service.DB_PATH = str(Path(tmp) / "auth.db")
        token_service.initialize_api_token_store()

        _, analyze_token = token_service.issue_token(
            "diagnostic-analyze", {"analyze"}, 30
        )

        headers = {"Authorization": f"Bearer {analyze_token}"}
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            checks = [
                ("ANALYZE_TOKEN_ON_READ_ROUTE",
                 "GET", "/api/v1/wazuh/events", None),
                ("ANALYZE_TOKEN_ON_ANALYSIS_ROUTE",
                 "POST", "/api/v1/analysis", {}),
                ("ANALYZE_TOKEN_ON_WAZUH_ANALYZE_ROUTE",
                 "POST", "/api/v1/wazuh/analyze", {}),
            ]

            for name, method, path, body in checks:
                response = await client.request(
                    method,
                    path,
                    headers=headers,
                    json=body if method == "POST" else None,
                )
                print(f"{name}_STATUS={response.status_code}")
                print(f"{name}_BODY={response.text[:500]!r}")

asyncio.run(main())

print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_DATABASE_CHANGED=NO")
print("LIVE_WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
print("PRODUCTION_SERVICE_RESTARTED=NO")
PY
```

- `GET /events` with an `analyze` token gives `403` (the token is valid but lacks `read`); as specified
- `POST /analysis` gives `422` (authentication passed; the required `events` in the body is missing)
- `POST /wazuh/analyze` gives `502`. Even with an empty body `{}`, `limit=50` and `since_minutes=60` are filled in automatically, so after authentication it went on to actual retrieval and analysis

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: WAZUH ANALYZE ROUTE SOURCE INSPECTION ====="

echo
echo "--- 1. Wazuh API route ---"
nl -ba app/api/wazuh.py | sed -n '1,240p'

echo
echo "--- 2. AI analysis service ---"
nl -ba app/services/ai_analysis.py | sed -n '1,280p'

echo
echo "--- 3. Analysis request schema ---"
grep -R -n -A45 -B5 \
  "class.*Analysis\|events:" \
  app/schemas

echo
echo "--- 4. Wazuh analysis call references ---"
grep -R -n \
  "analyze_wazuh_events\|analyze_events\|get_wazuh_events" \
  app --include='*.py'

echo
echo "SOURCE_FILES_MODIFIED=NO"
echo "API_REQUESTS_SENT=NO"
echo "EXTERNAL_NETWORK_REQUESTS=NO"
echo "PRODUCTION_DATABASE_CHANGED=NO"
```

So we switch to tests that fully simulate Wazuh retrieval and Ollama.

### 3.4 Testing the Wazuh APIs

`fetch_wazuh_events` is replaced with a function that returns an empty array, so it does not proceed to AI analysis, storing history or outside communication.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED WAZUH API AUTH TEST ====="

./venv/bin/python - <<'PY'
import asyncio
import tempfile
from pathlib import Path

import httpx
from fastapi import FastAPI

import app.services.api_tokens as token_service
import app.api.wazuh as wazuh_api

async def main():
    with tempfile.TemporaryDirectory(prefix="aidm-wazuh-auth-") as tmp:
        token_service.DB_PATH = str(Path(tmp) / "isolated.db")
        token_service.initialize_api_token_store()

        _, read_token = token_service.issue_token(
            "isolated-read", {"read"}, 30
        )
        _, analyze_token = token_service.issue_token(
            "isolated-analyze", {"analyze"}, 30
        )

        calls = {"fetch": 0}

        async def fake_fetch_wazuh_events(*, limit, since_minutes):
            calls["fetch"] += 1
            return []

        original_fetch = wazuh_api.fetch_wazuh_events
        wazuh_api.fetch_wazuh_events = fake_fetch_wazuh_events

        try:
            test_app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
            test_app.include_router(wazuh_api.router)

            transport = httpx.ASGITransport(app=test_app)

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://isolated-test",
            ) as client:
                cases = [
                    ("READ_TOKEN_GET_EVENTS", "GET",
                     "/api/v1/wazuh/events", read_token, 200),
                    ("ANALYZE_TOKEN_GET_EVENTS", "GET",
                     "/api/v1/wazuh/events", analyze_token, 403),
                    ("NO_TOKEN_POST_ANALYZE", "POST",
                     "/api/v1/wazuh/analyze", None, 401),
                    ("ANALYZE_TOKEN_POST_ANALYZE", "POST",
                     "/api/v1/wazuh/analyze", analyze_token, 404),
                    ("READ_TOKEN_POST_ANALYZE", "POST",
                     "/api/v1/wazuh/analyze", read_token, 403),
                ]

                for name, method, path, token, expected in cases:
                    headers = (
                        {"Authorization": f"Bearer {token}"}
                        if token else {}
                    )
                    response = await client.request(
                        method, path, headers=headers
                    )
                    passed = response.status_code == expected
                    print(
                        f"{name}="
                        f"{'PASS' if passed else 'FAIL'} "
                        f"STATUS={response.status_code} "
                        f"EXPECTED={expected}"
                    )

            print(f"MOCK_FETCH_CALLS={calls['fetch']}")
            print(
                "MOCK_FETCH_EXPECTED_CALLS="
                "2 (authorized GET and authorized POST)"
            )
            print(
                "MOCK_ONLY="
                f"{'PASS' if calls['fetch'] == 2 else 'FAIL'}"
            )

        finally:
            wazuh_api.fetch_wazuh_events = original_fetch

print("PRODUCTION_DATABASE_ACCESSED=NO")
print("LIVE_WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
print("ANALYSIS_HISTORY_WRITES=NO")
print("PRODUCTION_SERVICE_RESTARTED=NO")
asyncio.run(main())
PY
```

GET gave `200` with a `read` token and `403` with an `analyze` token; POST gave `401` without a token. The test that omitted the POST body gave `422` (even with defaults, the body itself is required). We retest with a body.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED WAZUH POST AUTH RETEST ====="

./venv/bin/python - <<'PY'
import asyncio
import tempfile
from pathlib import Path

import httpx
from fastapi import FastAPI

import app.services.api_tokens as token_service
import app.api.wazuh as wazuh_api

async def main():
    with tempfile.TemporaryDirectory(prefix="aidm-wazuh-post-") as tmp:
        token_service.DB_PATH = str(Path(tmp) / "isolated.db")
        token_service.initialize_api_token_store()

        _, analyze_token = token_service.issue_token(
            "isolated-analyze", {"analyze"}, 30
        )
        _, read_token = token_service.issue_token(
            "isolated-read", {"read"}, 30
        )

        calls = {"fetch": 0}

        async def fake_fetch_wazuh_events(*, limit, since_minutes):
            calls["fetch"] += 1
            return []

        original_fetch = wazuh_api.fetch_wazuh_events
        wazuh_api.fetch_wazuh_events = fake_fetch_wazuh_events

        try:
            test_app = FastAPI()
            test_app.include_router(wazuh_api.router)
            transport = httpx.ASGITransport(app=test_app)

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://isolated-test",
            ) as client:
                cases = [
                    ("ANALYZE_TOKEN_POST",
                     analyze_token, 404),
                    ("READ_TOKEN_POST",
                     read_token, 403),
                    ("NO_TOKEN_POST",
                     None, 401),
                ]

                for name, token, expected in cases:
                    headers = (
                        {"Authorization": f"Bearer {token}"}
                        if token else {}
                    )
                    response = await client.post(
                        "/api/v1/wazuh/analyze",
                        headers=headers,
                        json={},
                    )
                    print(
                        f"{name}="
                        f"{'PASS' if response.status_code == expected else 'FAIL'} "
                        f"STATUS={response.status_code} "
                        f"EXPECTED={expected}"
                    )

            print(f"MOCK_FETCH_CALLS={calls['fetch']}")
            print(
                "MOCK_CALL_COUNT="
                f"{'PASS' if calls['fetch'] == 1 else 'FAIL'}"
            )

        finally:
            wazuh_api.fetch_wazuh_events = original_fetch

asyncio.run(main())

print("PRODUCTION_DATABASE_ACCESSED=NO")
print("LIVE_WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
print("ANALYSIS_HISTORY_WRITES=NO")
print("PRODUCTION_SERVICE_RESTARTED=NO")
PY
```

| Test | Result |
|---|---:|
| GET with a `read` token | 200 |
| GET with an `analyze` token | 403 |
| POST with an `analyze` token | 404 (response for the simulated empty events) |
| POST with a `read` token | 403 |
| POST without a token | 401 |
| Times the simulated retrieval function was called | 1 |

For requests rejected by authentication, the Wazuh retrieval function was not called.

### 3.5 Testing the Analysis API

Using a test event with `source="internal"`, the analysis result is simulated to return a fixed `no_action` proposal, and storing history is also simulated.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED ANALYSIS API AUTH TEST ====="

./venv/bin/python - <<'PY'
import asyncio
import tempfile
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import FastAPI

import app.services.api_tokens as token_service
import app.api.analysis as analysis_api
from app.schemas.analysis_proposal import AIAnalysisProposal

async def main():
    with tempfile.TemporaryDirectory(prefix="aidm-analysis-auth-") as tmp:
        token_service.DB_PATH = str(Path(tmp) / "isolated.db")
        token_service.initialize_api_token_store()

        _, analyze_token = token_service.issue_token(
            "isolated-analyze", {"analyze"}, 30
        )
        _, read_token = token_service.issue_token(
            "isolated-read", {"read"}, 30
        )

        event_id = uuid4()
        event = {
            "event_id": str(event_id),
            "source": "internal",
            "severity": "high",
            "event_category": "test",
            "event_summary": "Isolated authentication test event",
        }

        proposal = AIAnalysisProposal(
            summary="Isolated test proposal",
            severity="low",
            confidence=0.95,
            evidence_event_ids=[event_id],
            recommended_action="no_action",
            requires_human_approval=False,
            reasoning="Generated by an isolated test mock",
        )

        calls = {"analysis": 0, "history": 0}

        async def fake_analyze_events(request):
            calls["analysis"] += 1
            return proposal

        def fake_save_analysis(request, result):
            calls["history"] += 1

        original_analyze = analysis_api.analyze_events
        original_save = analysis_api.save_analysis
        analysis_api.analyze_events = fake_analyze_events
        analysis_api.save_analysis = fake_save_analysis

        try:
            test_app = FastAPI()
            test_app.include_router(analysis_api.router)
            transport = httpx.ASGITransport(app=test_app)

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://isolated-test",
            ) as client:
                cases = [
                    ("ANALYZE_TOKEN_POST", analyze_token, 200),
                    ("READ_TOKEN_POST", read_token, 403),
                    ("NO_TOKEN_POST", None, 401),
                ]

                for name, token, expected in cases:
                    headers = (
                        {"Authorization": f"Bearer {token}"}
                        if token else {}
                    )
                    response = await client.post(
                        "/api/v1/analysis",
                        headers=headers,
                        json={"events": [event]},
                    )
                    passed = response.status_code == expected
                    print(
                        f"{name}="
                        f"{'PASS' if passed else 'FAIL'} "
                        f"STATUS={response.status_code} "
                        f"EXPECTED={expected}"
                    )

            print(f"MOCK_ANALYSIS_CALLS={calls['analysis']}")
            print(f"MOCK_HISTORY_CALLS={calls['history']}")
            print(
                "AUTHORIZED_ONLY="
                f"{'PASS' if calls == {'analysis': 1, 'history': 1} else 'FAIL'}"
            )

        finally:
            analysis_api.analyze_events = original_analyze
            analysis_api.save_analysis = original_save

asyncio.run(main())

print("PRODUCTION_DATABASE_ACCESSED=NO")
print("LIVE_WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
print("PRODUCTION_HISTORY_WRITES=NO")
print("PRODUCTION_SERVICE_RESTARTED=NO")
PY
```

| Test | Result |
|---|---:|
| `analyze` token | 200 |
| `read` token | 403 |
| No token | 401 |
| Analysis and storing history (simulated) | once, only when authentication passed |

## Closing Notes

In Part 57 we built token authentication for the API and checked it in an independent environment.

| Item | Result |
|---|---|
| Authentication | Bearer tokens, scopes `read` and `analyze`, stored as SHA-256 hashes, verified with `hmac.compare_digest` |
| CLI | `/usr/local/sbin/aidm-api-token` (root only) issues, revokes and lists |
| Documentation | `/docs`, `/redoc` and `/openapi.json` disabled |
| Tests | for all three APIs: `401` without a token, `403` for insufficient privilege, passes with the correct scope |
| Production | not yet deployed (no authentication table; service not restarted) |

In the next part, Part 58, we examine the CLI and token handling in detail, harden them, and do a final check before production.

# Part 58: Hardening Token Handling and the CLI
## Introduction

### About This Book

This is Part 58 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 57 we built token authentication for the API and tested it in an independent environment. Before putting it into production, we examine token handling and the CLI in detail and fix the weaknesses found.

| Found | Fix |
|---|---|
| If the parent directory of the token file is a symbolic link, the file is created at its target and permissions are changed there | open directories in turn with `O_DIRECTORY` and `O_NOFOLLOW`, and create the file through `dir_fd` |
| A literal `\n` was written to the file instead of a newline | write a real newline |
| A non-string element in `scopes` in the DB causes `TypeError` | check first that elements are strings |
| Passing `True` as the expiry is accepted as 1 day | reject `bool` |
| An invalid JSON in `scopes` stops the listing | handle it without stopping the listing |
| A failure partway through writing leaves a partial token file | on failure, remove only that file |

Everything is tested with a temporary DB and temporary files; the production DB and tokens are not touched. The service is not restarted.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

## Chapter 1: Reading the CLI and Token Handling

### 1.1 The CLI

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API TOKEN CLI SECURITY REVIEW ====="

echo
echo "--- 1. CLI implementation ---"
nl -ba app/cli/api_tokens.py | sed -n '1,300p'

echo
echo "--- 2. CLI entry point ---"
nl -ba app/cli/__init__.py | sed -n '1,160p'

echo
echo "--- 3. Executable wrapper ---"
stat -c '%A %a %U:%G %n' /usr/local/sbin/aidm-api-token
sed -n '1,160p' /usr/local/sbin/aidm-api-token

echo
echo "--- 4. Token-related directory permissions ---"
for p in \
  /root/.local \
  /root/.local/share \
  /root/.local/share/ai-defense-manager \
  /root/.local/share/ai-defense-manager/tokens
do
  if [ -e "$p" ]; then
    stat -c '%A %a %U:%G %n' "$p"
  else
    echo "NOT_PRESENT $p"
  fi
done

echo
echo "--- 5. Token service public functions ---"
grep -n '^def ' app/services/api_tokens.py

echo
echo "TOKEN_VALUES_DISPLAYED=NO"
echo "TOKEN_ISSUED=NO"
echo "TOKEN_REVOKED=NO"
echo "FILES_MODIFIED=NO"
echo "DATABASE_ACCESSED=NO"
```

`O_NOFOLLOW` applied only to the final file, so symbolic links in parent directories could be followed. Also, `os.chmod(directory, 0o700)` could change the permissions of an unintended directory.

### 1.2 Token Handling

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API TOKEN SERVICE SECURITY REVIEW ====="

echo
echo "--- 1. Token service source ---"
nl -ba app/services/api_tokens.py | sed -n '1,260p'

echo
echo "--- 2. Database path configuration ---"
grep -R -n \
  "DB_PATH\|DATABASE_PATH\|ai-defense.db" \
  app/core app/services --include='*.py'

echo
echo "--- 3. CLI and wrapper ownership ---"
stat -c '%A %a %U:%G %n' \
  app/cli \
  app/cli/api_tokens.py \
  app/services/api_tokens.py \
  /usr/local/sbin/aidm-api-token

echo
echo "--- 4. Root home directory permissions ---"
namei -l /root/.local/share/ai-defense-manager/tokens

echo
echo "SOURCE_FILES_MODIFIED=NO"
echo "TOKEN_VALUES_DISPLAYED=NO"
echo "TOKEN_ISSUED=NO"
echo "TOKEN_REVOKED=NO"
echo "DATABASE_CHANGED=NO"
```

We confirmed random values equivalent to 256 bits, storing only SHA-256 hashes, `hmac.compare_digest`, checks of scope/expiry/revocation, not showing secret values in listings, and rejecting scopes other than `read` and `analyze`. The CLI itself and the wrapper are owned by root, and the wrapper is `700`.

## Chapter 2: Fixing How the Token File Is Written

### 2.1 Testing the Current Method

Only dummy values are written to a temporary directory.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN FILE WRITER ISOLATED SECURITY TEST ====="

./venv/bin/python - <<'PY'
import os
import stat
import tempfile
from pathlib import Path

from app.cli.api_tokens import _write_token_file

with tempfile.TemporaryDirectory(prefix="aidm-token-file-test-") as tmp:
    root = Path(tmp)
    results = []

    def check(name, condition):
        results.append(bool(condition))
        print(f"{name}={'PASS' if condition else 'FAIL'}")

    # 1. Normal creation
    normal_dir = root / "normal"
    normal_file = normal_dir / "token.txt"
    _write_token_file("dummy.token-secret", normal_file)

    mode = stat.S_IMODE(normal_file.stat().st_mode)
    dir_mode = stat.S_IMODE(normal_dir.stat().st_mode)

    check("NORMAL_FILE_CREATED", normal_file.is_file())
    check("NORMAL_FILE_MODE_0600", mode == 0o600)
    check("NORMAL_DIR_MODE_0700", dir_mode == 0o700)

    # 2. Existing file must not be overwritten
    existing_result = False
    try:
        _write_token_file("replacement", normal_file)
    except FileExistsError:
        existing_result = normal_file.read_text() == "dummy.token-secret\n"

    check("EXISTING_FILE_NOT_OVERWRITTEN", existing_result)

    # 3. Final-component symlink must not be followed
    target = root / "target.txt"
    target.write_text("unchanged")
    link = root / "linked-token.txt"
    link.symlink_to(target)

    symlink_result = False
    try:
        _write_token_file("replacement", link)
    except (FileExistsError, OSError):
        symlink_result = (
            link.is_symlink()
            and target.read_text() == "unchanged"
        )

    check("FINAL_SYMLINK_NOT_FOLLOWED", symlink_result)

    # 4. Parent-component symlink behavior (diagnostic)
    real_parent = root / "real-parent"
    real_parent.mkdir()
    linked_parent = root / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)

    parent_result = "NOT_TESTED"
    try:
        _write_token_file("dummy", linked_parent / "token.txt")
        parent_result = "FOLLOWED"
    except Exception as exc:
        parent_result = type(exc).__name__

    print(f"PARENT_SYMLINK_BEHAVIOR={parent_result}")

    # 5. Directory outside root ownership is not tested by chown;
    # inspect current effective ownership only.
    print(f"TEST_PROCESS_EUID={os.geteuid()}")

    print(f"PASS_COUNT={sum(results)}")
    print(f"FAIL_COUNT={len(results) - sum(results)}")

print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("PRODUCTION_TOKEN_REVOKED=NO")
print("PRODUCTION_FILES_MODIFIED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

`PARENT_SYMLINK_BEHAVIOR=FOLLOWED`; that is, we confirmed that if the parent directory is a symbolic link, the token file is created at its target.

### 2.2 Testing a Safe Method with Temporary Code

The production token location and DB are not touched.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: SAFE TOKEN DIRECTORY WALK PROTOTYPE ====="

./venv/bin/python - <<'PY'
import os
import stat
import tempfile
from pathlib import Path

BASE_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
FILE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW

def safe_write(token: str, output: Path):
    if not output.is_absolute() or ".." in output.parts:
        raise ValueError("Absolute path without '..' is required")

    parts = output.parts[1:]
    if not parts:
        raise ValueError("Output file path is required")

    fd = os.open("/", BASE_FLAGS)
    try:
        for component in parts[:-1]:
            try:
                next_fd = os.open(
                    component, BASE_FLAGS, dir_fd=fd
                )
            except FileNotFoundError:
                os.mkdir(component, 0o700, dir_fd=fd)
                next_fd = os.open(
                    component, BASE_FLAGS, dir_fd=fd
                )

            info = os.fstat(next_fd)
            if not stat.S_ISDIR(info.st_mode):
                os.close(next_fd)
                raise PermissionError("Path component is not a directory")
            if info.st_uid != 0 or stat.S_IMODE(info.st_mode) & 0o077:
                os.close(next_fd)
                raise PermissionError("Directory ownership or mode is unsafe")

            os.close(fd)
            fd = next_fd

        file_fd = os.open(
            parts[-1], FILE_FLAGS, 0o600, dir_fd=fd
        )
        try:
            os.fchmod(file_fd, 0o600)
            with os.fdopen(file_fd, "w", encoding="ascii") as stream:
                file_fd = -1
                stream.write(token + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            if file_fd >= 0:
                os.close(file_fd)
        os.fsync(fd)
    finally:
        os.close(fd)

with tempfile.TemporaryDirectory(
    prefix="aidm-safe-walk-", dir="/root"
) as tmp:
    root = Path(tmp)
    results = []

    def check(name, condition):
        results.append(bool(condition))
        print(f"{name}={'PASS' if condition else 'FAIL'}")

    # Normal creation
    target = root / "a" / "b" / "token.txt"
    safe_write("dummy.secret", target)
    check("NORMAL_CREATE", target.read_text() == "dummy.secret\n")
    check("FILE_MODE_0600", stat.S_IMODE(target.stat().st_mode) == 0o600)
    check("DIR_MODE_0700", stat.S_IMODE(target.parent.stat().st_mode) == 0o700)

    # Parent symlink must be rejected
    real = root / "real"
    real.mkdir()
    link = root / "link"
    link.symlink_to(real, target_is_directory=True)
    rejected = False
    try:
        safe_write("dummy", link / "token.txt")
    except OSError:
        rejected = True
    check("PARENT_SYMLINK_REJECTED", rejected)
    check("LINK_TARGET_UNCHANGED", not (real / "token.txt").exists())

    # Existing final file must not be overwritten
    existing_rejected = False
    try:
        safe_write("replacement", target)
    except FileExistsError:
        existing_rejected = target.read_text() == "dummy.secret\n"
    check("EXISTING_FILE_PROTECTED", existing_rejected)

    # Parent directory permissions must not be changed
    shared = root / "shared"
    shared.mkdir(mode=0o700)
    os.chmod(shared, 0o700)
    before = stat.S_IMODE(shared.stat().st_mode)
    safe_write("dummy", shared / "another-token.txt")
    after = stat.S_IMODE(shared.stat().st_mode)
    check("EXISTING_DIR_MODE_UNCHANGED", before == after)

    print(f"PASS_COUNT={sum(results)}")
    print(f"FAIL_COUNT={len(results) - sum(results)}")

print("PRODUCTION_FILES_MODIFIED=NO")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

All 7 passed (rejecting symbolic links in parents and the final file, not overwriting existing files, new directories `0700`, files `0600`, not changing permissions of existing directories).

### 2.3 Integrating into the CLI

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN CLI SAFE WRITER PATCH ====="

BACKUP_DIR="/var/backups/ai-defense-manager/token-cli-hardening-20261124"
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

cp -a app/cli/api_tokens.py "$BACKUP_DIR/api_tokens.py.before"
sha256sum app/cli/api_tokens.py > "$BACKUP_DIR/SHA256.before"
chmod 600 "$BACKUP_DIR/api_tokens.py.before" "$BACKUP_DIR/SHA256.before"

./venv/bin/python - <<'PY'
from pathlib import Path

path = Path("app/cli/api_tokens.py")
source = path.read_text()

start = source.index("def _write_token_file(")
end = source.index("\n\ndef main():", start)

replacement = '''def _write_token_file(token: str, output: Path) -> None:
    if not output.is_absolute() or ".." in output.parts:
        raise ValueError("Token output path must be absolute and normalized")

    parts = output.parts[1:]
    if not parts:
        raise ValueError("Token output file path is required")

    directory_fd = os.open(
        "/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    )

    try:
        for component in parts[:-1]:
            try:
                next_fd = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory_fd,
                )
            except FileNotFoundError:
                os.mkdir(component, 0o700, dir_fd=directory_fd)
                next_fd = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory_fd,
                )

            info = os.fstat(next_fd)
            if not stat.S_ISDIR(info.st_mode):
                os.close(next_fd)
                raise PermissionError("Token path component is not a directory")
            if info.st_uid != 0 or stat.S_IMODE(info.st_mode) & 0o077:
                os.close(next_fd)
                raise PermissionError(
                    "Token directory must be root-owned and inaccessible to group/others"
                )

            os.close(directory_fd)
            directory_fd = next_fd

        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        file_fd = os.open(
            parts[-1], flags, 0o600, dir_fd=directory_fd
        )

        try:
            os.fchmod(file_fd, 0o600)
            with os.fdopen(file_fd, "w", encoding="ascii") as stream:
                file_fd = -1
                stream.write(token + "\\\\n")
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            if file_fd >= 0:
                os.close(file_fd)

        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
'''

path.write_text(source[:start] + replacement + source[end:])
print("SOURCE_PATCHED=YES")
PY

echo
echo "--- Syntax check ---"
./venv/bin/python -m py_compile app/cli/api_tokens.py
echo "PYTHON_SYNTAX=PASS"

echo
echo "--- New source hash ---"
sha256sum app/cli/api_tokens.py

echo
echo "--- Backup verification ---"
sha256sum -c "$BACKUP_DIR/SHA256.before"

echo
echo "DATABASE_CHANGED=NO"
echo "TOKEN_ISSUED=NO"
echo "TOKEN_REVOKED=NO"
echo "SERVICE_RESTARTED=NO"
```

### 2.4 Checking the Copy and Imports

The `sha256sum -c` at the end of the script above compares against the same path after the change, so it gives `FAIL`. We compare again against the pre-change copy itself.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN CLI BACKUP AND IMPORT VERIFICATION ====="

BACKUP_DIR="/var/backups/ai-defense-manager/token-cli-hardening-20261124"

echo
echo "--- 1. Recorded original hash ---"
cat "$BACKUP_DIR/SHA256.before"

echo
echo "--- 2. Actual backup hash ---"
sha256sum "$BACKUP_DIR/api_tokens.py.before"

echo
echo "--- 3. Compare recorded hash with backup ---"
EXPECTED="$(awk '{print $1}' "$BACKUP_DIR/SHA256.before")"
ACTUAL="$(sha256sum "$BACKUP_DIR/api_tokens.py.before" | awk '{print $1}')"
if [ "$EXPECTED" = "$ACTUAL" ]; then
    echo "BACKUP_INTEGRITY=PASS"
else
    echo "BACKUP_INTEGRITY=FAIL"
fi

echo
echo "--- 4. Current imports ---"
sed -n '1,35p' app/cli/api_tokens.py

echo
echo "--- 5. Writer implementation ---"
sed -n '/^def _write_token_file/,/^def main/p' app/cli/api_tokens.py

echo
echo "--- 6. Required module availability ---"
./venv/bin/python - <<'PY'
import app.cli.api_tokens as module
print("OS_IMPORT=" + ("PASS" if hasattr(module, "os") else "FAIL"))
print("STAT_IMPORT=" + ("PASS" if hasattr(module, "stat") else "FAIL"))
print("PATH_IMPORT=" + ("PASS" if hasattr(module, "Path") else "FAIL"))
PY

echo
echo "PRODUCTION_DATABASE_ACCESSED=NO"
echo "TOKEN_ISSUED=NO"
echo "SERVICE_RESTARTED=NO"
```

The integrity of the copy passed, and there were no problems importing `os`, `stat` and `Path`. Reading the source, `stream.write(token + "\\n")` was written so that it writes the characters `\n` rather than a newline.

### 2.5 Fixing the Newline and Retesting

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN FILE NEWLINE FIX AND REGRESSION TEST ====="

./venv/bin/python - <<'PY'
import os
import stat
import tempfile
from pathlib import Path

path = Path("app/cli/api_tokens.py")
source = path.read_text()

old = r'stream.write(token + "\\n")'
new = r'stream.write(token + "\n")'

if source.count(old) != 1:
    print("PATCH=ABORTED")
    print("EXPECTED_SOURCE_PATTERN_COUNT=" + str(source.count(old)))
    raise SystemExit(1)

path.write_text(source.replace(old, new, 1))
print("NEWLINE_SOURCE_PATCH=PASS")
PY

./venv/bin/python -m py_compile app/cli/api_tokens.py
echo "PYTHON_SYNTAX=PASS"

./venv/bin/python - <<'PY'
import os
import stat
import tempfile
from pathlib import Path
from app.cli.api_tokens import _write_token_file

results = []

def check(name, ok):
    results.append(bool(ok))
    print(f"{name}={'PASS' if ok else 'FAIL'}")

with tempfile.TemporaryDirectory(prefix="aidm-cli-regression-", dir="/root") as tmp:
    root = Path(tmp)

    # Normal creation and an exact newline
    output = root / "tokens" / "token.txt"
    _write_token_file("dummy.secret", output)
    check("TOKEN_CONTENT_EXACT", output.read_bytes() == b"dummy.secret\n")
    check("TOKEN_FILE_MODE_0600", stat.S_IMODE(output.stat().st_mode) == 0o600)
    check("CREATED_DIR_MODE_0700", stat.S_IMODE(output.parent.stat().st_mode) == 0o700)

    # Prevent overwriting an existing file
    overwrite_blocked = False
    try:
        _write_token_file("replacement", output)
    except FileExistsError:
        overwrite_blocked = output.read_bytes() == b"dummy.secret\n"
    check("EXISTING_FILE_PROTECTED", overwrite_blocked)

    # Reject a parent symbolic link
    real = root / "real"
    real.mkdir(mode=0o700)
    link = root / "link"
    link.symlink_to(real, target_is_directory=True)
    symlink_blocked = False
    try:
        _write_token_file("dummy", link / "token.txt")
    except OSError:
        symlink_blocked = True
    check("PARENT_SYMLINK_REJECTED", symlink_blocked)
    check("SYMLINK_TARGET_UNCHANGED", not (real / "token.txt").exists())

    # Reject a symbolic link in the final component
    target = root / "target.txt"
    target.write_text("unchanged")
    final_link = root / "final-link"
    final_link.symlink_to(target)
    final_blocked = False
    try:
        _write_token_file("replacement", final_link)
    except OSError:
        final_blocked = target.read_text() == "unchanged"
    check("FINAL_SYMLINK_REJECTED", final_blocked)

print(f"PASS_COUNT={sum(results)}")
print(f"FAIL_COUNT={len(results) - sum(results)}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("SERVICE_RESTARTED=NO")
PY

echo
echo "--- Updated source hash ---"
sha256sum app/cli/api_tokens.py

echo "PRODUCTION_TOKEN_STORE_MODIFIED=NO"
```

All 7 passed (correct newline, `0600`, new directory `0700`, no overwriting, symbolic links rejected, link targets unaffected).

## Chapter 3: Checking Scope Types

### 3.1 The Current Check

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API TOKEN SCOPE VALIDATION SOURCE AUDIT ====="

echo
echo "--- 1. verify_token implementation ---"
grep -n -A100 -B10 '^def verify_token' app/services/api_tokens.py

echo
echo "--- 2. Scope parsing and validation references ---"
grep -n -E 'json.loads|ALLOWED_SCOPES|scopes|compare_digest|PermissionError' app/services/api_tokens.py

echo
echo "--- 3. Token table schema initialization ---"
grep -n -A35 -B5 'CREATE TABLE' app/services/api_tokens.py

echo
echo "--- 4. Current source hash ---"
sha256sum app/services/api_tokens.py app/cli/api_tokens.py

echo
echo "PRODUCTION_DATABASE_ACCESSED=NO"
echo "PRODUCTION_TOKEN_STORE_MODIFIED=NO"
echo "TOKEN_ISSUED=NO"
echo "SERVICE_RESTARTED=NO"
```

The following check could raise `TypeError: unhashable type` if the `scopes` array contains dictionaries or lists.

```python
all(scope in ALLOWED_SCOPES for scope in scopes)
```

### 3.2 Reproducing It

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: MALFORMED TOKEN SCOPE ISOLATED TEST ====="

./venv/bin/python - <<'PY'
import hashlib
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import app.services.api_tokens as tokens

original_db_path = tokens.DB_PATH

with tempfile.TemporaryDirectory(prefix="aidm-scope-test-", dir="/root") as tmp:
    test_db = Path(tmp) / "isolated.db"
    tokens.DB_PATH = test_db

    tokens.initialize_api_token_store()

    token_id = "a" * 32
    secret = "isolated-dummy-secret"
    plaintext = token_id + "." + secret
    secret_hash = hashlib.sha256(secret.encode()).hexdigest()

    expiry = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    cases = [
        ("VALID_STRING_SCOPES", '["read","analyze"]'),
        ("UNKNOWN_STRING_SCOPE", '["read","admin"]'),
        ("DICT_SCOPE", '[{"scope":"read"}]'),
        ("LIST_SCOPE", '[["read"]]'),
        ("NON_LIST_SCOPE", '{"scope":"read"}'),
        ("INVALID_JSON", '{invalid'),
    ]

    results = []

    try:
        for index, (name, scopes_json) in enumerate(cases):
            current_id = format(index + 1, "032x")
            current_token = current_id + "." + secret

            with sqlite3.connect(test_db) as conn:
                conn.execute(
                    """
                    INSERT INTO api_tokens
                    (token_id, secret_hash, name, scopes, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        current_id,
                        secret_hash,
                        "isolated-test",
                        scopes_json,
                        datetime.now(timezone.utc).isoformat(),
                        expiry,
                    ),
                )

            try:
                result = tokens.verify_token(current_token, "read")
                outcome = f"RETURNED_{result}"
            except Exception as exc:
                outcome = "EXCEPTION_" + type(exc).__name__

            print(f"{name}={outcome}")
            results.append((name, outcome))

        print()
        print("UNHASHABLE_SCOPE_EXCEPTION=" + (
            "DETECTED"
            if any(
                outcome == "EXCEPTION_TypeError"
                for _, outcome in results
            )
            else "NOT_DETECTED"
        ))

    finally:
        tokens.DB_PATH = original_db_path

print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_STORE_MODIFIED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

`TypeError` occurred for both `DICT_SCOPE` and `LIST_SCOPE`. This means invalid authentication data would cause a `500` error.

### 3.3 Fixing

We check first that elements are strings, then compare against the allowlist.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN SCOPE TYPE VALIDATION PATCH ====="

BACKUP_DIR="/var/backups/ai-defense-manager/token-cli-hardening-20261124"
cp -a app/services/api_tokens.py "$BACKUP_DIR/api_tokens.py.before-scope-fix"
sha256sum app/services/api_tokens.py > "$BACKUP_DIR/SHA256.scope-before"
chmod 600 "$BACKUP_DIR/api_tokens.py.before-scope-fix" "$BACKUP_DIR/SHA256.scope-before"

./venv/bin/python - <<'PY'
from pathlib import Path

path = Path("app/services/api_tokens.py")
source = path.read_text()

old = '''        if (
            not isinstance(scopes, list)
            or not all(scope in ALLOWED_SCOPES for scope in scopes)
        ):
            return False
'''

new = '''        if (
            not isinstance(scopes, list)
            or not all(
                isinstance(scope, str) and scope in ALLOWED_SCOPES
                for scope in scopes
            )
        ):
            return False
'''

if source.count(old) != 1:
    raise SystemExit("PATCH_ABORTED: expected source block not found exactly once")

path.write_text(source.replace(old, new, 1))
print("SOURCE_PATCHED=YES")
PY

echo
echo "--- Syntax check ---"
./venv/bin/python -m py_compile app/services/api_tokens.py
echo "PYTHON_SYNTAX=PASS"

echo
echo "--- Isolated malformed-scope regression test ---"
./venv/bin/python - <<'PY'
import hashlib
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import app.services.api_tokens as tokens

original_db_path = tokens.DB_PATH
results = []

def check(name, condition):
    results.append(bool(condition))
    print(f"{name}={'PASS' if condition else 'FAIL'}")

with tempfile.TemporaryDirectory(prefix="aidm-scope-fixed-", dir="/root") as tmp:
    test_db = Path(tmp) / "isolated.db"
    tokens.DB_PATH = test_db
    tokens.initialize_api_token_store()

    secret = "isolated-dummy-secret"
    secret_hash = hashlib.sha256(secret.encode()).hexdigest()
    expiry = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    cases = [
        ("VALID_STRING_SCOPES", '["read","analyze"]', True),
        ("UNKNOWN_STRING_SCOPE", '["read","admin"]', False),
        ("DICT_SCOPE", '[{"scope":"read"}]', False),
        ("LIST_SCOPE", '[["read"]]', False),
        ("NON_LIST_SCOPE", '{"scope":"read"}', False),
        ("INVALID_JSON", '{invalid', False),
    ]

    try:
        for index, (name, scopes_json, expected) in enumerate(cases):
            token_id = format(index + 1, "032x")
            with sqlite3.connect(test_db) as conn:
                conn.execute(
                    """
                    INSERT INTO api_tokens
                    (token_id, secret_hash, name, scopes, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        token_id,
                        secret_hash,
                        "isolated-test",
                        scopes_json,
                        datetime.now(timezone.utc).isoformat(),
                        expiry,
                    ),
                )

            try:
                actual = tokens.verify_token(token_id + "." + secret, "read")
                check(name, actual is expected)
            except Exception as exc:
                print(f"{name}=FAIL EXCEPTION={type(exc).__name__}")
                results.append(False)
    finally:
        tokens.DB_PATH = original_db_path

print(f"PASS_COUNT={sum(results)}")
print(f"FAIL_COUNT={len(results) - sum(results)}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_STORE_MODIFIED=NO")
print("TOKEN_ISSUED=NO")
print("SERVICE_RESTARTED=NO")
PY

echo
echo "--- Source hash ---"
sha256sum app/services/api_tokens.py
```

All 6 passed (valid scopes pass, disallowed scopes are rejected, dictionaries, lists and the like are rejected without exceptions, and invalid JSON is also rejected).

## Chapter 4: Expiry, Listing and Write Failures

### 4.1 Testing Edge Values

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN SERVICE EDGE CASE ISOLATED AUDIT ====="

./venv/bin/python - <<'PY'
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import app.services.api_tokens as tokens
from app.cli.api_tokens import _write_token_file

original_db_path = tokens.DB_PATH
results = []

def report(name, outcome):
    print(f"{name}={outcome}")
    results.append(outcome == "EXPECTED")

with tempfile.TemporaryDirectory(prefix="aidm-edge-audit-", dir="/root") as tmp:
    root = Path(tmp)
    tokens.DB_PATH = root / "isolated.db"

    try:
        tokens.initialize_api_token_store()

        # 1. bool is a subclass of int
        try:
            tokens.issue_token("bool-expiry-test", {"read"}, True)
            report("BOOLEAN_EXPIRY_ACCEPTED", "DETECTED")
        except (ValueError, TypeError):
            report("BOOLEAN_EXPIRY_REJECTED", "EXPECTED")

        # 2. Invalid name type must not reach production DB
        try:
            tokens.issue_token(None, {"read"}, 1)
            report("NON_STRING_NAME_HANDLING", "UNEXPECTED_ACCEPT")
        except (ValueError, TypeError, AttributeError):
            report("NON_STRING_NAME_HANDLING", "EXPECTED")

        # 3. Corrupt scopes JSON in isolated DB
        with sqlite3.connect(tokens.DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO api_tokens
                (token_id, secret_hash, name, scopes, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "b" * 32,
                    "a" * 64,
                    "corrupt-test",
                    "{invalid-json",
                    datetime.now(timezone.utc).isoformat(),
                    "2099-01-01T00:00:00+00:00",
                ),
            )

        try:
            tokens.list_tokens()
            report("CORRUPT_SCOPE_LIST_HANDLING", "UNEXPECTED_SUCCESS")
        except Exception as exc:
            print("CORRUPT_SCOPE_LIST_EXCEPTION=" + type(exc).__name__)
            report("CORRUPT_SCOPE_LIST_HANDLING", "DETECTED")

        # 4. Writer failure cleanup: use a directory as final filename.
        blocked = root / "blocked"
        blocked.mkdir()
        try:
            _write_token_file("dummy-secret", blocked)
            report("WRITER_DIRECTORY_TARGET", "UNEXPECTED_SUCCESS")
        except (OSError, ValueError):
            report("WRITER_DIRECTORY_TARGET", "EXPECTED")

    finally:
        tokens.DB_PATH = original_db_path

print()
print("EXPECTED_CASES=" + str(sum(results)))
print("UNEXPECTED_CASES=" + str(len(results) - sum(results)))
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_STORE_MODIFIED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("PRODUCTION_FILES_MODIFIED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

- In Python, `bool` is a kind of `int`, so `True` is accepted as an expiry of 1 day
- If `scopes` in the DB is invalid JSON, `list_tokens()` stops with `JSONDecodeError`

### 4.2 Fixing Expiry and Listing

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN EXPIRY AND LIST CORRUPTION HARDENING ====="

BACKUP_DIR="/var/backups/ai-defense-manager/token-cli-hardening-20261124"
cp -a app/services/api_tokens.py "$BACKUP_DIR/api_tokens.py.before-edge-fix"
sha256sum app/services/api_tokens.py > "$BACKUP_DIR/SHA256.edge-before"
chmod 600 "$BACKUP_DIR/api_tokens.py.before-edge-fix" "$BACKUP_DIR/SHA256.edge-before"

./venv/bin/python - <<'PY'
from pathlib import Path

path = Path("app/services/api_tokens.py")
source = path.read_text()

old_expiry = '''    if not isinstance(expires_in_days, int) or not 1 <= expires_in_days <= 365:
        raise ValueError("Expiry must be between 1 and 365 days")
'''

new_expiry = '''    if type(expires_in_days) is not int or not 1 <= expires_in_days <= 365:
        raise ValueError("Expiry must be between 1 and 365 days")
'''

old_list = '''    return [
        {
            "token_id": row["token_id"],
            "name": row["name"],
            "scopes": json.loads(row["scopes"]),
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "revoked_at": row["revoked_at"],
            "last_used_at": row["last_used_at"],
        }
        for row in rows
    ]
'''

new_list = '''    result = []
    for row in rows:
        try:
            scopes = json.loads(row["scopes"])
        except (ValueError, TypeError):
            scopes = []

        if (
            not isinstance(scopes, list)
            or not all(
                isinstance(scope, str) and scope in ALLOWED_SCOPES
                for scope in scopes
            )
        ):
            scopes = []

        result.append({
            "token_id": row["token_id"],
            "name": row["name"],
            "scopes": scopes,
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "revoked_at": row["revoked_at"],
            "last_used_at": row["last_used_at"],
        })

    return result
'''

if source.count(old_expiry) != 1:
    raise SystemExit("PATCH_ABORTED: expiry block mismatch")
if source.count(old_list) != 1:
    raise SystemExit("PATCH_ABORTED: list block mismatch")

source = source.replace(old_expiry, new_expiry, 1)
source = source.replace(old_list, new_list, 1)
path.write_text(source)

print("SOURCE_PATCHED=YES")
PY

echo
echo "--- Syntax check ---"
./venv/bin/python -m py_compile app/services/api_tokens.py
echo "PYTHON_SYNTAX=PASS"

echo
echo "--- Isolated regression tests ---"
./venv/bin/python - <<'PY'
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import app.services.api_tokens as tokens

original_db_path = tokens.DB_PATH
results = []

def check(name, condition):
    results.append(bool(condition))
    print(f"{name}={'PASS' if condition else 'FAIL'}")

with tempfile.TemporaryDirectory(prefix="aidm-edge-fixed-", dir="/root") as tmp:
    tokens.DB_PATH = Path(tmp) / "isolated.db"

    try:
        tokens.initialize_api_token_store()

        for value, expected in [
            (True, False),
            (False, False),
            (1, True),
            (90, True),
            (365, True),
            (0, False),
            (366, False),
        ]:
            try:
                tokens.issue_token("expiry-test", {"read"}, value)
                actual = True
            except (ValueError, TypeError):
                actual = False
            check(f"EXPIRY_{value!r}_ACCEPTANCE", actual is expected)

        with sqlite3.connect(tokens.DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO api_tokens
                (token_id, secret_hash, name, scopes, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "c" * 32,
                    "b" * 64,
                    "corrupt-json",
                    "{invalid-json",
                    datetime.now(timezone.utc).isoformat(),
                    "2099-01-01T00:00:00+00:00",
                ),
            )
            conn.execute(
                """
                INSERT INTO api_tokens
                (token_id, secret_hash, name, scopes, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "d" * 32,
                    "c" * 64,
                    "corrupt-type",
                    '[{"scope":"read"}]',
                    datetime.now(timezone.utc).isoformat(),
                    "2099-01-01T00:00:00+00:00",
                ),
            )

        items = tokens.list_tokens()
        by_id = {item["token_id"]: item for item in items}

        check(
            "CORRUPT_JSON_LIST_SAFE",
            by_id["c" * 32]["scopes"] == [],
        )
        check(
            "CORRUPT_SCOPE_TYPE_LIST_SAFE",
            by_id["d" * 32]["scopes"] == [],
        )
        check(
            "TOKEN_SECRET_NOT_INCLUDED",
            all("secret_hash" not in item for item in items),
        )

    finally:
        tokens.DB_PATH = original_db_path

print(f"PASS_COUNT={sum(results)}")
print(f"FAIL_COUNT={len(results) - sum(results)}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_STORE_MODIFIED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("SERVICE_RESTARTED=NO")
PY

echo
echo "--- Source hash ---"
sha256sum app/services/api_tokens.py
```

| Checked | Result |
|---|---|
| Rejecting `True` and `False` as expiry | passed |
| 1, 90, 365 days | passed |
| Rejecting 0 and 366 days | passed |
| Listing that includes invalid JSON | passed |
| Listing that includes invalid scope types | passed |
| No secrets in the listing | passed |

All 10 passed.

### 4.3 When Writing Fails

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN ISSUE FAILURE CLEANUP ISOLATED AUDIT ====="

./venv/bin/python - <<'PY'
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import app.cli.api_tokens as cli

results = []

def check(name, condition):
    results.append(bool(condition))
    print(f"{name}={'PASS' if condition else 'FAIL'}")

with tempfile.TemporaryDirectory(prefix="aidm-cleanup-audit-", dir="/root") as tmp:
    root = Path(tmp)
    output = root / "blocked-parent" / "token.txt"

    issued = {"token_id": "a" * 32, "plaintext": "dummy.secret"}
    revoked = []

    def fake_issue(*args):
        return issued["token_id"], issued["plaintext"]

    def fake_revoke(token_id):
        revoked.append(token_id)
        return True

    def failing_writer(token, path):
        path.parent.mkdir(mode=0o700)
        partial = path.with_name(path.name + ".partial")
        partial.write_text("partial")
        raise OSError("simulated write failure")

    with (
        patch.object(cli, "issue_token", side_effect=fake_issue),
        patch.object(cli, "revoke_token", side_effect=fake_revoke),
        patch.object(cli, "_write_token_file", side_effect=failing_writer),
        patch.object(cli, "initialize_api_token_store"),
        patch.object(cli, "_require_root"),
    ):
        import sys
        original_argv = sys.argv
        sys.argv = [
            "aidm-api-token",
            "issue",
            "--name", "isolated-test",
            "--scopes", "read",
            "--output", str(output),
        ]
        try:
            exit_code = cli.main()
        finally:
            sys.argv = original_argv

    check("ISSUE_COMMAND_FAILED", exit_code == 1)
    check("TOKEN_REVOKE_ATTEMPTED", revoked == [issued["token_id"]])
    check(
        "PARTIAL_FILE_REMAINS",
        (output.with_name(output.name + ".partial")).exists(),
    )

print()
print(f"PASS_COUNT={sum(results)}")
print(f"FAIL_COUNT={len(results) - sum(results)}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_STORE_MODIFIED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

If writing the file fails during issuance, the issued token is revoked and the CLI exits with an error, but a partial file could be left behind.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN FILE FAILURE CLEANUP SOURCE INSPECTION ====="

echo "--- _write_token_file ---"
sed -n '1,145p' app/cli/api_tokens.py

echo
echo "--- issue command exception handling ---"
grep -n -A75 -B15 'def _issue\|def main\|_write_token_file\|revoke_token' app/cli/api_tokens.py

echo
echo "--- Current source hash ---"
sha256sum app/cli/api_tokens.py

echo
echo "SOURCE_MODIFIED=NO"
echo "PRODUCTION_DATABASE_ACCESSED=NO"
echo "SERVICE_RESTARTED=NO"
```

`_write_token_file()` had no step to remove the file when `write()`, `flush()` or `fsync()` failed after the file was created.

### 4.4 Removing the Partial File on Failure

If an exception occurs after newly creating the file, only that file is removed using the FD of the same directory. Existing files and symbolic links are not removed.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN FILE PARTIAL WRITE CLEANUP PATCH ====="

./venv/bin/python - <<'PY'
from pathlib import Path

path = Path("app/cli/api_tokens.py")
source = path.read_text()

old = '''        try:
            os.fchmod(file_fd, 0o600)
            with os.fdopen(file_fd, "w", encoding="ascii") as stream:
                file_fd = -1
                stream.write(token + "\\n")
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            if file_fd >= 0:
                os.close(file_fd)

        os.fsync(directory_fd)
'''

new = '''        try:
            try:
                os.fchmod(file_fd, 0o600)
                with os.fdopen(file_fd, "w", encoding="ascii") as stream:
                    file_fd = -1
                    stream.write(token + "\\n")
                    stream.flush()
                    os.fsync(stream.fileno())

                os.fsync(directory_fd)
            except BaseException:
                if file_fd >= 0:
                    os.close(file_fd)
                    file_fd = -1

                try:
                    os.unlink(parts[-1], dir_fd=directory_fd)
                except FileNotFoundError:
                    pass

                try:
                    os.fsync(directory_fd)
                except OSError:
                    pass

                raise
        finally:
            if file_fd >= 0:
                os.close(file_fd)
'''

if source.count(old) != 1:
    raise SystemExit("PATCH_ABORTED: writer block mismatch")

path.write_text(source.replace(old, new, 1))
print("SOURCE_PATCHED=YES")
PY

echo
echo "--- Syntax check ---"
./venv/bin/python -m py_compile app/cli/api_tokens.py
echo "PYTHON_SYNTAX=PASS"

echo
echo "--- Isolated actual writer failure tests ---"
./venv/bin/python - <<'PY'
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from app.cli.api_tokens import _write_token_file

results = []

def check(name, condition):
    results.append(bool(condition))
    print(f"{name}={'PASS' if condition else 'FAIL'}")

with tempfile.TemporaryDirectory(prefix="aidm-writer-cleanup-", dir="/root") as tmp:
    root = Path(tmp)
    output = root / "tokens" / "issued.txt"

    real_fsync = os.fsync
    calls = {"count": 0}

    def fail_first_fsync(fd):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("isolated fsync failure")
        return real_fsync(fd)

    try:
        with patch("app.cli.api_tokens.os.fsync", side_effect=fail_first_fsync):
            _write_token_file("isolated-dummy-token", output)
        check("INJECTED_FAILURE_TRIGGERED", False)
    except OSError:
        check("INJECTED_FAILURE_TRIGGERED", calls["count"] >= 1)

    check("PARTIAL_TOKEN_FILE_REMOVED", not output.exists())
    check("TOKEN_DIRECTORY_REMAINS", output.parent.is_dir())
    check(
        "TOKEN_DIRECTORY_EMPTY",
        output.parent.is_dir() and not any(output.parent.iterdir()),
    )

    normal = root / "normal" / "token.txt"
    _write_token_file("normal-dummy-token", normal)
    check(
        "NORMAL_WRITE_CONTENT",
        normal.read_text() == "normal-dummy-token\n",
    )
    check(
        "NORMAL_WRITE_MODE_0600",
        (normal.stat().st_mode & 0o777) == 0o600,
    )

print()
print(f"PASS_COUNT={sum(results)}")
print(f"FAIL_COUNT={len(results) - sum(results)}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_STORE_MODIFIED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("SERVICE_RESTARTED=NO")
PY

echo
echo "--- Source hash ---"
sha256sum app/cli/api_tokens.py
```

We actually caused `fsync()` to fail and confirmed that the partial file is removed, and that on success the contents are saved with `0600` (all 6 passed).

## Chapter 5: Whole Tests and the Final Check

### 5.1 Token Lifecycle Tests (17 Cases)

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: TOKEN LIFECYCLE API INSPECTION ====="

./venv/bin/python - <<'PY'
import inspect
import app.services.api_tokens as tokens

for name in ("issue_token", "verify_token", "revoke_token", "list_tokens"):
    fn = getattr(tokens, name)
    print(f"\n--- {name}{inspect.signature(fn)} ---")
    print(inspect.getsource(fn))

print("\nPRODUCTION_DATABASE_ACCESSED=NO")
print("TOKEN_ISSUED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

On successful authentication `last_used_at` is updated; insufficient scope raises `PermissionError`; invalid or revoked tokens give `False`. We check with a temporary SQLite DB. Token plaintext and hashes are not displayed.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED TOKEN LIFECYCLE REGRESSION TEST ====="

./venv/bin/python - <<'PY'
import hashlib
import sqlite3
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import app.services.api_tokens as tokens

original_db_path = tokens.DB_PATH
results = []

def check(name, condition):
    results.append(bool(condition))
    print(f"{name}={'PASS' if condition else 'FAIL'}")

with tempfile.TemporaryDirectory(prefix="aidm-lifecycle-", dir="/root") as tmp:
    tokens.DB_PATH = Path(tmp) / "isolated.db"

    try:
        tokens.initialize_api_token_store()

        token_id, plaintext = tokens.issue_token(
            "isolated-lifecycle-test", {"read"}, 90
        )

        check("TOKEN_ID_FORMAT", len(token_id) == 32)
        check("PLAINTEXT_NOT_EMPTY", isinstance(plaintext, str) and "." in plaintext)

        secret = plaintext.partition(".")[2]
        expected_hash = hashlib.sha256(secret.encode("ascii")).hexdigest()

        with sqlite3.connect(tokens.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT secret_hash, scopes, last_used_at, revoked_at "
                "FROM api_tokens WHERE token_id = ?",
                (token_id,),
            ).fetchone()

        check("HASH_ONLY_STORED", row["secret_hash"] == expected_hash)
        check("PLAINTEXT_NOT_STORED", plaintext not in row["secret_hash"])
        check("READ_SCOPE_STORED", row["scopes"] == '["read"]')

        check("VALID_READ_TOKEN_ACCEPTED", tokens.verify_token(plaintext, "read"))

        with sqlite3.connect(tokens.DB_PATH) as conn:
            last_used = conn.execute(
                "SELECT last_used_at FROM api_tokens WHERE token_id = ?",
                (token_id,),
            ).fetchone()[0]

        check("LAST_USED_UPDATED", last_used is not None)

        try:
            tokens.verify_token(plaintext, "analyze")
            scope_denied = False
        except PermissionError:
            scope_denied = True

        check("MISSING_SCOPE_DENIED", scope_denied)
        check("WRONG_SECRET_REJECTED", not tokens.verify_token(
            token_id + ".wrong-secret", "read"
        ))
        check("MALFORMED_TOKEN_REJECTED", not tokens.verify_token(
            "malformed", "read"
        ))
        check("UNKNOWN_TOKEN_REJECTED", not tokens.verify_token(
            "f" * 32 + ".unknown-secret", "read"
        ))

        check("FIRST_REVOCATION_SUCCEEDS", tokens.revoke_token(token_id))
        check("SECOND_REVOCATION_NO_CHANGE", not tokens.revoke_token(token_id))
        check("REVOKED_TOKEN_REJECTED", not tokens.verify_token(plaintext, "read"))

        listed = tokens.list_tokens()
        item = next((x for x in listed if x["token_id"] == token_id), None)

        check("REVOKED_STATE_LISTED", item is not None and item["revoked_at"] is not None)
        check(
            "LIST_EXCLUDES_SECRET_FIELDS",
            item is not None and "secret_hash" not in item and "token" not in item,
        )

        # Expiry boundary: force expiry into the past in the isolated DB.
        expired_id, expired_plaintext = tokens.issue_token(
            "isolated-expiry-test", {"read"}, 1
        )
        with sqlite3.connect(tokens.DB_PATH) as conn:
            conn.execute(
                "UPDATE api_tokens SET expires_at = ? WHERE token_id = ?",
                ((datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
                 expired_id),
            )

        check("EXPIRED_TOKEN_REJECTED", not tokens.verify_token(
            expired_plaintext, "read"
        ))

    finally:
        tokens.DB_PATH = original_db_path

print()
print(f"PASS_COUNT={sum(results)}")
print(f"FAIL_COUNT={len(results) - sum(results)}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_STORE_MODIFIED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("LIVE_API_REQUESTS=NO")
print("SERVICE_RESTARTED=NO")
PY
```

All 17 passed (ID format and issuing, storing as hashes, passing with the correct scope, rejecting insufficient scope, rejecting invalid and unknown tokens, updating last-used time, revocation and more).

### 5.2 Tests Through the CLI (14 Cases)

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED TOKEN CLI END-TO-END TEST ====="

./venv/bin/python - <<'PY'
import contextlib
import io
import tempfile
from pathlib import Path
from unittest.mock import patch

import app.services.api_tokens as token_service
import app.cli.api_tokens as cli

original_db_path = token_service.DB_PATH
results = []

def check(name, condition):
    results.append(bool(condition))
    print(f"{name}={'PASS' if condition else 'FAIL'}")

with tempfile.TemporaryDirectory(prefix="aidm-cli-e2e-", dir="/root") as tmp:
    root = Path(tmp)
    token_service.DB_PATH = root / "isolated.db"
    token_file = root / "private" / "client.token"

    def run_cli(argv):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch("sys.argv", ["aidm-api-token", *argv]):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = cli.main()
        return code, stdout.getvalue(), stderr.getvalue()

    try:
        code, out, err = run_cli([
            "issue",
            "--name", "cli-e2e-test",
            "--scopes", "read",
            "--expires-in-days", "30",
            "--output", str(token_file),
        ])

        check("CLI_ISSUE_EXIT_ZERO", code == 0)
        check("CLI_ISSUE_SUCCESS_MARKER", "TOKEN_ISSUED=YES" in out)
        check("TOKEN_FILE_CREATED", token_file.is_file())
        check(
            "TOKEN_FILE_MODE_0600",
            token_file.is_file() and (token_file.stat().st_mode & 0o777) == 0o600,
        )

        plaintext = token_file.read_text().strip() if token_file.is_file() else ""
        token_id = plaintext.partition(".")[0]

        check("TOKEN_FILE_FORMAT", bool(token_id) and "." in plaintext)
        check(
            "TOKEN_VALUE_NOT_PRINTED",
            bool(plaintext) and plaintext not in out and plaintext not in err,
        )

        code, out, err = run_cli(["list"])
        check("CLI_LIST_EXIT_ZERO", code == 0)
        check("CLI_LIST_CONTAINS_TOKEN_ID", token_id in out)
        check("CLI_LIST_DOES_NOT_EXPOSE_SECRET", plaintext not in out)
        check("CLI_LIST_SECRET_NOTICE", "NOT_STORED_OR_DISPLAYED" in out)

        code, out, err = run_cli(["revoke", "--token-id", token_id])
        check("CLI_REVOKE_EXIT_ZERO", code == 0)
        check("CLI_REVOKE_SUCCESS", "TOKEN_REVOKED= YES" in out)

        check(
            "REVOKED_TOKEN_REJECTED",
            not token_service.verify_token(plaintext, "read"),
        )

        code, out, err = run_cli(["revoke", "--token-id", token_id])
        check("CLI_SECOND_REVOKE_NO_CHANGE", code == 0 and "NO_CHANGE" in out)

    finally:
        token_service.DB_PATH = original_db_path

print()
print(f"PASS_COUNT={sum(results)}")
print(f"FAIL_COUNT={len(results) - sum(results)}")
print("PRODUCTION_DATABASE_ACCESSED=NO")
print("PRODUCTION_TOKEN_STORE_MODIFIED=NO")
print("PRODUCTION_TOKEN_ISSUED=NO")
print("LIVE_API_REQUESTS=NO")
print("SERVICE_RESTARTED=NO")
PY
```

| Operation | Result |
|---|---|
| `issue` | issued; secret file saved with `0600` |
| `list` | shows IDs, does not show plaintext tokens |
| `revoke` | revoked successfully |
| `revoke` again | `NO_CHANGE` |
| Authentication after revocation | rejected |

All 14 passed. The independent tests of the service and the CLI, 31 in total (17 and 14), all passed.

### 5.3 Final Check Before Production

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API AUTH PRE-DEPLOYMENT STATIC AUDIT ====="

echo
echo "--- 1. Python compile check ---"
./venv/bin/python -m compileall -q app
echo "COMPILEALL=PASS"

echo
echo "--- 2. API route authentication declarations ---"
grep -n -E -B3 -A5 \
  'require_scope|@router\.(get|post)|include_in_schema' \
  app/api/analysis.py app/api/wazuh.py

echo
echo "--- 3. Documentation endpoints configuration ---"
grep -n -A8 -B3 \
  'FastAPI(' app/main.py

echo
echo "--- 4. Modified source permissions and ownership ---"
stat -c '%U:%G %a %n' \
  app/main.py \
  app/api/analysis.py \
  app/api/wazuh.py \
  app/core/api_auth.py \
  app/services/api_tokens.py \
  app/cli/api_tokens.py \
  app/cli/__init__.py \
  /usr/local/sbin/aidm-api-token

echo
echo "--- 5. Source hashes ---"
sha256sum \
  app/main.py \
  app/api/analysis.py \
  app/api/wazuh.py \
  app/core/api_auth.py \
  app/services/api_tokens.py \
  app/cli/api_tokens.py \
  app/cli/__init__.py \
  /usr/local/sbin/aidm-api-token

echo
echo "--- 6. Service state (read-only metadata) ---"
systemctl show ai-defense-manager.service \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p ExecMainStartTimestamp \
  -p User \
  -p Group \
  -p FragmentPath

echo
echo "PRODUCTION_DATABASE_ACCESSED=NO"
echo "PRODUCTION_TOKEN_STORE_MODIFIED=NO"
echo "TOKEN_ISSUED=NO"
echo "SERVICE_RESTARTED=NO"
echo "LIVE_WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
```

| Check | Result |
|---|---|
| Syntax of all Python | passed |
| `/api/v1/wazuh/events`: `read` | passed |
| `/api/v1/analysis`: `analyze` | passed |
| `/api/v1/wazuh/analyze`: `analyze` | passed |
| `/health` | still outside authentication |
| Swagger, ReDoc, OpenAPI | disabled |
| Service | `active (running)`; not restarted |

`app/main.py` and `app/api/wazuh.py` are `root:ai-defense`, `640`, while some authentication files are `root:root`, `644`; they are not uniform. In both cases the service account can read but not write them, so we do not change them now.

## Closing Notes

In Part 58 we fixed weaknesses in token handling and the CLI, and are ready for production.

| Item | Result |
|---|---|
| Token file | rejects symbolic links, no overwriting, `0600` and directory `0700`; removes partial files on failure |
| Scopes and expiry | types checked, no stopping on exceptions; expiry 1–365 days |
| Listing | does not stop on broken data and does not show secret values |
| Tests | 31 in total (plus tests of each fix), all passed |
| Production | not yet deployed |

In the next part, Part 59, we create the authentication table in the production DB, issue tokens, and deploy to the service.

# Part 59: Putting API Authentication into Production
## Introduction

### About This Book

This is Part 59 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". We put into production the API token authentication built and tested in Parts 57 and 58.

1. Create the table that manages tokens in the production SQLite
2. Issue one client token and check that the file and the DB agree
3. Restart the service to enable authentication
4. In production, check the order of authentication, authentication of the Wazuh retrieval API, that nothing leaks into logs, and that the last-used time is updated

For the production tests, we use requests that always stop at input validation, so that no AI analysis, storing of history or communication with Wazuh or Ollama occurs.

> **Caution:** Do not display, paste or hand over the contents of the token to anyone.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

## Chapter 1: Creating the Table in the Production DB

We create only the `api_tokens` table and an index on the expiry. Existing tables and data are not changed.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: PRODUCTION API TOKEN SCHEMA INITIALIZATION ====="

./venv/bin/python - <<'PY'
import sqlite3

from app.services import api_tokens

db_path = api_tokens.DB_PATH
print("DATABASE_PATH=", db_path)

# Run only the approved initialization function
api_tokens.initialize_api_token_store()
print("SCHEMA_INITIALIZATION=COMPLETED")

# Only check that the schema exists
with sqlite3.connect(db_path) as conn:
    conn.row_factory = sqlite3.Row

    table = conn.execute(
        """
        SELECT name, sql
        FROM sqlite_master
        WHERE type = 'table' AND name = 'api_tokens'
        """
    ).fetchone()

    index = conn.execute(
        """
        SELECT name, sql
        FROM sqlite_master
        WHERE type = 'index' AND name = 'idx_api_tokens_expires_at'
        """
    ).fetchone()

    columns = conn.execute(
        "PRAGMA table_info(api_tokens)"
    ).fetchall() if table else []

print("API_TOKENS_TABLE_EXISTS=", table is not None)
print("EXPIRY_INDEX_EXISTS=", index is not None)
print("COLUMN_NAMES=", ",".join(row["name"] for row in columns))

if not table or not index:
    raise SystemExit("SCHEMA_VERIFICATION=FAIL")

print("SCHEMA_VERIFICATION=PASS")
print("TOKEN_ISSUED=NO")
print("TOKEN_REVOKED=NO")
print("SERVICE_RESTARTED=NO")
print("LIVE_WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
PY
```

`api_tokens` (8 columns) and `idx_api_tokens_expires_at` were created, with `SCHEMA_VERIFICATION=PASS`.

## Chapter 2: Issuing a Token

### 2.1 CLI Arguments and the Destination

Following the principle of least privilege, give only the scopes the use requires. Here we gave both `read` and `analyze`.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API TOKEN ISSUE ARGUMENT CHECK ====="

aidm-api-token issue --help

echo
echo "===== TOKEN STORAGE DIRECTORY CHECK ====="
namei -l /root
echo
echo "TOKEN_ISSUED=NO"
echo "DATABASE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

### 2.2 Issuing

| Item | Value |
|---|---|
| Name | `ai-defense-client` |
| Scopes | `read,analyze` |
| Expiry | 30 days |
| Destination | `/root/ai-defense-client.token` (`600`) |

> **Run on: VM 230**

```bash
echo "===== VM230: API CLIENT TOKEN ISSUE ====="

aidm-api-token issue \
  --name ai-defense-client \
  --scopes read,analyze \
  --expires-in-days 30 \
  --output /root/ai-defense-client.token

echo
echo "===== TOKEN FILE PERMISSION CHECK ====="
stat -c 'OWNER=%U GROUP=%G MODE=%a SIZE=%s PATH=%n' /root/ai-defense-client.token

echo
echo "===== TOKEN VALUE DISPLAY ====="
echo "TOKEN_VALUE_DISPLAYED=NO"
echo "TOKEN_VALUE_LOGGED=NO"
```

The token file was created with owner `root`, `600`, 77 bytes. The token contents were not displayed.

### 2.3 Checking the Issued Token

The display of the issuance result was garbled (`TOKEN_ISSUED=YESE_LOGGED=NO"`), so without reissuing we check the DB registration, scopes and hash match read-only.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISSUED TOKEN READ-ONLY VERIFICATION ====="

./venv/bin/python - <<'PY'
import hashlib
import json
import os
import sqlite3
from pathlib import Path

token_id = "edcdfc1bfba5683c76c590fd41377ce7"
token_path = Path("/root/ai-defense-client.token")
db_path = "/opt/ai-defense-manager/data/ai-defense.db"

file_ok = False
db_ok = False
hash_ok = False

try:
    st = token_path.lstat()
    file_ok = (
        token_path.is_file()
        and not token_path.is_symlink()
        and st.st_uid == 0
        and (st.st_mode & 0o777) == 0o600
    )
    raw = token_path.read_text(encoding="ascii").strip()
    parts = raw.split(".", 1)
    format_ok = len(parts) == 2 and parts[0] == token_id
    if format_ok:
        secret_hash = hashlib.sha256(parts[1].encode("ascii")).hexdigest()
    else:
        secret_hash = ""
except Exception:
    format_ok = False
    secret_hash = ""

try:
    uri = "file:" + db_path + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT token_id, secret_hash, name, scopes,
                   created_at, expires_at, revoked_at
            FROM api_tokens
            WHERE token_id = ?
            """,
            (token_id,),
        ).fetchone()

    if row:
        db_ok = (
            row["name"] == "ai-defense-client"
            and row["revoked_at"] is None
        )
        hash_ok = (
            len(secret_hash) == 64
            and secret_hash == row["secret_hash"]
        )
        scopes = json.loads(row["scopes"])
        scopes_ok = (
            isinstance(scopes, list)
            and set(scopes) == {"read", "analyze"}
            and all(isinstance(x, str) for x in scopes)
        )
        expiry_ok = row["expires_at"] is not None
    else:
        scopes_ok = expiry_ok = False
except Exception:
    db_ok = hash_ok = scopes_ok = expiry_ok = False

print("TOKEN_FILE_OWNER_MODE_OK=", file_ok)
print("TOKEN_FILE_FORMAT_OK=", format_ok)
print("DATABASE_RECORD_EXISTS=", db_ok)
print("SECRET_HASH_MATCHES_FILE=", hash_ok)
print("SCOPES_READ_ANALYZE_ONLY=", scopes_ok)
print("EXPIRY_CONFIGURED=", expiry_ok)
print("TOKEN_VALUE_DISPLAYED=NO")
print("DATABASE_MODIFIED=NO")
print("TOKEN_REISSUED=NO")
print("SERVICE_RESTARTED=NO")

if all((file_ok, format_ok, db_ok, hash_ok, scopes_ok, expiry_ok)):
    print("TOKEN_VERIFICATION=PASS")
else:
    print("TOKEN_VERIFICATION=FAIL")
PY
```

| Checked | Result |
|---|---|
| File owner and permissions | passed (`root:root`, `600`) |
| Token format | passed |
| Registered in SQLite | passed |
| SHA-256 match between file and DB | passed |
| Scopes | passed (`read`, `analyze`) |
| Expiry | passed |
| Token value not shown | passed |

## Chapter 3: Deploying to the Service

### 3.1 Checks Before the Restart

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: PRE-RESTART FINAL AUDIT ====="

echo
echo "--- 1. Service runtime status ---"
systemctl show ai-defense-manager.service \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p User \
  -p Group \
  -p ExecMainStartTimestamp \
  -p Restart \
  -p FragmentPath

echo
echo "--- 2. Service unit configuration ---"
systemctl cat ai-defense-manager.service

echo
echo "--- 3. Listening socket ---"
ss -lntp | grep -E '127\.0\.0\.1:8000|0\.0\.0\.0:8000|\[::\]:8000' || true

echo
echo "--- 4. Source syntax check ---"
./venv/bin/python -m compileall -q app
echo "PYTHON_COMPILE=PASS"

echo
echo "--- 5. Authentication source presence ---"
grep -nE 'initialize_api_token_store|docs_url=None|redoc_url=None|openapi_url=None' app/main.py
grep -nE 'require_scope\("(read|analyze)"\)' app/api/analysis.py app/api/wazuh.py

echo
echo "--- 6. Token file metadata only ---"
stat -c 'OWNER=%U GROUP=%G MODE=%a SIZE=%s' /root/ai-defense-client.token

echo
echo "TOKEN_VALUE_DISPLAYED=NO"
echo "SERVICE_RESTARTED=NO"
echo "LIVE_WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
echo "PRODUCTION_DATABASE_MODIFIED=NO"
```

The service was `active (running)`, listening only on `127.0.0.1:8000`; the Python syntax passed; authentication on the three API routes had been confirmed; OpenAPI, Swagger and ReDoc were disabled; and the token file was root-only `600`.

### 3.2 Restart

> **Run on: VM 230**

```bash
echo "===== VM230: APPROVED API SERVICE RESTART ====="

systemctl restart ai-defense-manager.service

echo
echo "===== SERVICE STATUS ====="
systemctl show ai-defense-manager.service \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p ExecMainStartTimestamp

echo
echo "===== LISTENING SOCKET ====="
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "===== LOCAL HEALTH CHECK ====="
curl --silent --show-error \
  --max-time 5 \
  --output /dev/null \
  --write-out 'HTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "TOKEN_VALUE_DISPLAYED=NO"
echo "LIVE_WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
```

Right after the restart, listening on `127.0.0.1:8000` was not visible and `/health` gave `HTTP_STATUS=000`. Without restarting again, we check the state (strings that look like tokens in the log are masked).

> **Run on: VM 230**

```bash
echo "===== VM230: API STARTUP FAILURE DIAGNOSTICS ====="

echo
echo "--- 1. systemd detailed state ---"
systemctl status ai-defense-manager.service --no-pager -l
systemctl show ai-defense-manager.service \
  -p Result -p ExecMainCode -p ExecMainStatus \
  -p NRestarts -p MainPID -p ExecStart

echo
echo "--- 2. Process state ---"
ps -o pid,ppid,user,group,stat,etime,comm -p 2203
echo
echo "--- 3. Listening sockets ---"
ss -lntp | grep -E '8000|uvicorn' || true

echo
echo "--- 4. Recent startup errors (sanitized) ---"
journalctl -u ai-defense-manager.service \
  --since "15 minutes ago" --no-pager -o cat |
python3 -c '
import re, sys
for line in sys.stdin:
    if re.search(r"error|exception|traceback|failed|denied|fatal|cannot|permission|import", line, re.I):
        line = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~-]+", r"\1[REDACTED]", line)
        line = re.sub(r"(?i)(token[=: ]+)[A-Za-z0-9._~-]{12,}", r"\1[REDACTED]", line)
        print(line.rstrip()[:1000])
'

echo
echo "--- 5. Health check ---"
curl --silent --show-error --max-time 5 \
  --output /dev/null \
  --write-out 'HTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "CONFIGURATION_CHANGED=NO"
echo "SERVICE_RESTARTED_AGAIN=NO"
echo "TOKEN_VALUE_DISPLAYED=NO"
echo "LIVE_WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
```

| Item | Result |
|---|---|
| systemd | `active (running)` (MainPID `2203`, 0 restarts) |
| Uvicorn and application startup | normal, complete |
| Listening | `127.0.0.1:8000` |
| `/health` | `HTTP 200` |

The earlier `000` was because the check came right after startup.

## Chapter 4: Checking Authentication in Production

### 4.1 Input Shape of the Analysis API

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: LOCAL AUTHENTICATION TEST ====="

echo
echo "--- 1. Analysis endpoint input contract ---"
sed -n '1,120p' app/api/analysis.py

echo
echo "--- 2. Token file metadata ---"
stat -c 'OWNER=%U GROUP=%G MODE=%a SIZE=%s' /root/ai-defense-client.token

echo
echo "--- 3. Local health check ---"
curl --silent --show-error --max-time 5 \
  --output /dev/null \
  --write-out 'HEALTH_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "AUTH_TEST_REQUESTS=NOT_SENT"
echo "TOKEN_VALUE_DISPLAYED=NO"
echo "LIVE_WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
echo "ANALYSIS_EXECUTION=NO"
```

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ANALYSIS REQUEST SCHEMA INSPECTION ====="

echo
echo "--- Request schema ---"
sed -n '1,240p' app/schemas/analysis.py

echo
echo "--- Related nested schemas ---"
grep -R -nE 'class AIAnalysisRequest|class .*Request|Field\(' app/schemas

echo
echo "SOURCE_MODIFIED=NO"
echo "AUTH_REQUESTS_SENT=NO"
echo "TOKEN_VALUE_DISPLAYED=NO"
echo "WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
```

After authentication, the analysis API calls `analyze_events()` and then stores history. `events` requires at least one item, so sending `{"events":[]}`, which is valid JSON with an empty `events`, always stops at input validation and does not proceed to analysis.

> **Note:** Sending invalid JSON (such as just `{`) may make FastAPI return a body parsing error (`422`) before authentication, which does not test authentication.

### 4.2 Order of Authentication

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: AUTH ORDER TEST ====="

TOKEN="$(cat /root/ai-defense-client.token)"

echo
echo "--- 1. No token: expected 401 ---"
curl --silent --show-error --max-time 5 \
  -X POST \
  -H 'Content-Type: application/json' \
  --data '{"events":[]}' \
  --output /dev/null \
  --write-out 'NO_TOKEN_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/api/v1/analysis

echo
echo "--- 2. Valid token: expected 422 (schema rejection) ---"
curl --silent --show-error --max-time 5 \
  -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  --data '{"events":[]}' \
  --output /dev/null \
  --write-out 'VALID_TOKEN_INVALID_SCHEMA_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/api/v1/analysis

unset TOKEN

echo
echo "--- 3. Health check ---"
curl --silent --show-error --max-time 5 \
  --output /dev/null \
  --write-out 'HEALTH_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "TOKEN_VALUE_DISPLAYED=NO"
echo "WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
echo "ANALYSIS_EXECUTION=NO"
echo "PRODUCTION_HISTORY_WRITES=NO"
```

| Test | HTTP | Verdict |
|---|---:|---|
| No token | 401 | passed |
| Valid token + invalid input | 422 | passed (rejected at input validation after passing authentication) |
| `/health` | 200 | passed |

### 4.3 The Wazuh Retrieval API

To avoid connecting to production Wazuh, we send only requests without credentials or with an invalid token.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: WAZUH EVENTS API AUTH GATE TEST ====="

echo
echo "--- 1. No token: expected 401 ---"
curl --silent --show-error --max-time 5 \
  -X GET \
  --output /dev/null \
  --write-out 'NO_TOKEN_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/api/v1/wazuh/events

echo
echo "--- 2. Malformed Bearer: expected 401 ---"
curl --silent --show-error --max-time 5 \
  -H 'Authorization: Bearer invalid-test-token' \
  --output /dev/null \
  --write-out 'INVALID_TOKEN_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/api/v1/wazuh/events

echo
echo "--- 3. Health check ---"
curl --silent --show-error --max-time 5 \
  --output /dev/null \
  --write-out 'HEALTH_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/health

echo
echo "VALID_TOKEN_USED=NO"
echo "WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
echo "DATABASE_MODIFIED=NO"
echo "TOKEN_VALUE_DISPLAYED=NO"
```

| Test | HTTP | Verdict |
|---|---:|---|
| No token | 401 | passed |
| Invalid Bearer token | 401 | passed |
| `/health` | 200 | passed |

No communication with Wazuh occurred. For `403` (insufficient privilege) we rely on the results of the independent tests in Part 57 and do not add a test token to the production DB.

### 4.4 Does Information Leak?

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API AUTH SECURITY AUDIT ====="

echo
echo "--- 1. Authentication implementation ---"
sed -n '1,240p' app/core/api_auth.py

echo
echo "--- 2. Token verification and lifecycle ---"
grep -nE -B 5 -A 12 \
  'def verify_token|def revoke_token|def issue_token|last_used_at|expires_at|revoked_at|compare_digest|logger|print\(' \
  app/services/api_tokens.py

echo
echo "--- 3. Potential token logging ---"
grep -R -nE \
  'Authorization|Bearer|access_token|secret_hash|TOKEN_VALUE|logger\.(debug|info|warning|error|exception)|print\(' \
  app/core app/api app/services \
  --include='*.py' |
grep -v 'secret_hash = hashlib.sha256' |
head -100

echo
echo "--- 4. Exception response handling ---"
grep -R -nE \
  'exception_handler|HTTPException|traceback|debug=True|detail=|raise .* from' \
  app/main.py app/api \
  --include='*.py' |
head -120

echo
echo "--- 5. Service logging configuration ---"
systemctl show ai-defense-manager.service \
  -p StandardOutput -p StandardError -p LogLevelMax

echo
echo "SOURCE_MODIFIED=NO"
echo "DATABASE_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "TOKEN_VALUE_DISPLAYED=NO"
echo "LIVE_WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
```

| Item | Verdict |
|---|---|
| Bearer tokens not written to logs | passed (no logger or print in the authentication logic) |
| SHA-256 comparison | passed (`hmac.compare_digest()`) |
| Expiry and revocation checks | passed |
| Insufficient scope | passed (`403`) |
| `last_used_at` | passed (updated only when authentication succeeds) |
| API exception responses | passed (return fixed messages) |

> **Run on: VM 230**

```bash
echo "===== VM230: AUTH FAILURE LOG LEAK TEST ====="

START_TIME="$(date --iso-8601=seconds)"

curl --silent --show-error --max-time 5 \
  -H 'Authorization: Bearer invalid-log-test-secret-000000000000' \
  --output /dev/null \
  --write-out 'INVALID_TOKEN_STATUS=%{http_code}\n' \
  http://127.0.0.1:8000/api/v1/wazuh/events

echo
echo "--- Recent journal: sensitive values redacted ---"
journalctl -u ai-defense-manager.service \
  --since "$START_TIME" --no-pager -o cat |
python3 -c '
import re, sys
for line in sys.stdin:
    line = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", line)
    line = re.sub(r"(?i)(token[=: ]+)[A-Za-z0-9._~+/=-]{12,}", r"\1[REDACTED]", line)
    print(line.rstrip()[:1000])
'

echo
echo "REAL_TOKEN_USED=NO"
echo "DATABASE_MODIFIED=NO"
echo "WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
```

An invalid token gave `401`, and the journal recorded only the source, path and status; the token value did not appear.

### 4.5 Last-Used Time

Without showing the production token on screen or in arguments, we send one authenticated POST. With `events: []` it gives `422`, so no analysis, storing of history or connection to Wazuh occurs.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: LAST_USED_AT PRODUCTION VERIFICATION ====="

./venv/bin/python - <<'PY'
import sqlite3
from pathlib import Path
import httpx

TOKEN_PATH = Path("/root/ai-defense-client.token")
DB_PATH = "/opt/ai-defense-manager/data/ai-defense.db"
TOKEN_ID = "edcdfc1bfba5683c76c590fd41377ce7"

def read_last_used():
    uri = "file:" + DB_PATH + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        row = conn.execute(
            "SELECT last_used_at FROM api_tokens WHERE token_id = ?",
            (TOKEN_ID,),
        ).fetchone()
    if row is None:
        raise RuntimeError("Token record not found")
    return row[0]

before = read_last_used()
token = TOKEN_PATH.read_text(encoding="ascii").strip()

response = httpx.post(
    "http://127.0.0.1:8000/api/v1/analysis",
    headers={"Authorization": f"Bearer {token}"},
    json={"events": []},
    timeout=5.0,
)

after = read_last_used()

print("HTTP_STATUS=", response.status_code)
print("LAST_USED_BEFORE_SET=", before is not None)
print("LAST_USED_AFTER_SET=", after is not None)
print("LAST_USED_CHANGED=", before != after)
print("TOKEN_VALUE_DISPLAYED=NO")

if response.status_code == 422 and after is not None and before != after:
    print("LAST_USED_AT_VERIFICATION=PASS")
else:
    print("LAST_USED_AT_VERIFICATION=FAIL")

print("WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
print("ANALYSIS_EXECUTION=NO")
print("HISTORY_WRITES=NO")
PY
```

We confirmed that `last_used_at` in the production SQLite was updated when authentication succeeded.

## Closing Notes

In Part 59 we put API token authentication into production.

| Item | Result |
|---|---|
| Production DB | created `api_tokens` and the expiry index |
| Token | issued `ai-defense-client` (`read,analyze`, 30 days); `/root/ai-defense-client.token` (`600`) |
| Service | restarted; authentication enabled (`/health` without authentication) |
| Production tests | no token and invalid tokens give `401`, a valid token passes authentication, tokens do not appear in logs, `last_used_at` is updated |
| Documentation | `/docs`, `/redoc` and `/openapi.json` disabled |

> **Operational note:** Tokens expire after 30 days. Before expiry, issue a new token with `aidm-api-token` and revoke the old one with `revoke` (see the Operations Manual).

In the next part, Part 60, we check whether information leaks from API error responses and logs.

# Part 60: Keeping Error Responses and Logs from Leaking Information
## Introduction

### About This Book

This is Part 60 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 59 we put API authentication into production. Here we check whether internal information or submitted values leak from API error responses and logs.

1. Read how API error responses are built, and test whether unhandled exceptions expose internal information
2. Find that input validation error (`422`) responses contain the submitted values as is, and change them to a fixed message
3. Check the destinations and permissions of the Uvicorn logs, the journal and syslog

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

## Chapter 1: Checking Error Responses

### 1.1 How Error Responses Are Built

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API ERROR DISCLOSURE STATIC AUDIT ====="

echo
echo "--- 1. API exception handlers ---"
grep -RInE \
  'except |HTTPException|detail=|raise .*Exception|str\(e\)|repr\(e\)|traceback|logger\.(exception|error)' \
  app/api app/core/api_auth.py app/main.py \
  --include='*.py' |
grep -v '__pycache__' |
head -160

echo
echo "--- 2. Response and middleware configuration ---"
grep -RInE \
  'exception_handler|RequestValidationError|add_middleware|CORSMiddleware|TrustedHostMiddleware|debug=' \
  app \
  --include='*.py' |
grep -v '__pycache__' |
head -120

echo
echo "--- 3. Production service debug settings ---"
systemctl show ai-defense-manager.service \
  -p Environment -p EnvironmentFiles -p ExecStart \
  --no-pager |
sed -E 's/(TOKEN|SECRET|PASSWORD|KEY)=([^ ]+)/\1=[REDACTED]/Ig'

echo
echo "PRODUCTION_DB_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
```

| Target | Result |
|---|---|
| Analysis APIs, Wazuh APIs | return errors with fixed strings |
| Authentication | `401`, `403`, `503` with fixed strings |
| Returning exception strings as is | none |
| Exposing tracebacks | none |
| Uvicorn debug | not in the startup arguments |

### 1.2 Middleware and Global Exception Handling

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: MIDDLEWARE AND GLOBAL ERROR HANDLER AUDIT ====="

echo
echo "--- 1. app/main.py lines 1-150 ---"
nl -ba app/main.py | sed -n '1,150p'

echo
echo "--- 2. Middleware and exception registrations ---"
grep -RInE \
  'add_middleware|@app\.exception_handler|exception_handler\(|ExceptionMiddleware|ServerErrorMiddleware|CORSMiddleware|allow_origins|allow_credentials|allow_methods|allow_headers' \
  app \
  --include='*.py' |
grep -v '__pycache__' |
head -120

echo
echo "--- 3. Debug and reload references ---"
grep -RInE \
  'debug[[:space:]]*=|--reload|reload[[:space:]]*=' \
  app /etc/systemd/system/ai-defense-manager.service \
  --include='*.py' --include='*.service' 2>/dev/null |
head -80

echo
echo "PRODUCTION_DB_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
```

There was the body limit (256KiB; `413` with a fixed JSON if exceeded) and disabling of OpenAPI and others, but no application-specific global exception handling or CORS middleware.

### 1.3 Testing Unhandled Exceptions

We test with an independent application that does not affect production.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED UNHANDLED EXCEPTION TEST ====="

./venv/bin/python - <<'PY'
import asyncio
import json
from fastapi import FastAPI
from starlette.middleware.exceptions import ExceptionMiddleware
from starlette.middleware.errors import ServerErrorMiddleware

app = FastAPI(debug=False)

@app.get("/test-error")
async def test_error():
    raise RuntimeError("INTERNAL_SECRET_MARKER_DO_NOT_DISCLOSE")

wrapped = ServerErrorMiddleware(
    ExceptionMiddleware(app, handlers=app.exception_handlers, debug=False),
    debug=False,
)

messages = []
scope = {
    "type": "http",
    "asgi": {"version": "3.0", "spec_version": "2.3"},
    "http_version": "1.1",
    "method": "GET",
    "scheme": "http",
    "path": "/test-error",
    "raw_path": b"/test-error",
    "query_string": b"",
    "root_path": "",
    "headers": [],
    "client": ("127.0.0.1", 12345),
    "server": ("127.0.0.1", 8000),
}

async def receive():
    return {"type": "http.request", "body": b"", "more_body": False}

async def send(message):
    messages.append(message)

try:
    awaitable = wrapped(scope, receive, send)
    asyncio.run(awaitable)
except RuntimeError:
    pass

start = next(m for m in messages if m["type"] == "http.response.start")
body = b"".join(
    m.get("body", b"")
    for m in messages
    if m["type"] == "http.response.body"
)

text = body.decode("utf-8", errors="replace")
print("HTTP_STATUS=", start["status"])
print("RESPONSE_IS_JSON=", bool(text) and text.lstrip().startswith("{"))
print("INTERNAL_MARKER_IN_RESPONSE=", "INTERNAL_SECRET_MARKER" in text)
print("TRACEBACK_IN_RESPONSE=", "Traceback" in text)
print("GENERIC_500_RESPONSE=", start["status"] == 500 and "Internal Server Error" in text)
PY

echo
echo "PRODUCTION_SERVICE_TOUCHED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
```

For unhandled exceptions, only `HTTP 500` and `Internal Server Error` were returned; no internal exception markers or tracebacks were included (FastAPI `debug=False`).

### 1.4 Testing Input Validation Errors

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED VALIDATION ERROR DISCLOSURE TEST ====="

./venv/bin/python - <<'PY'
import asyncio
import json
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.exceptions import ExceptionMiddleware
from starlette.middleware.errors import ServerErrorMiddleware

class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[str] = Field(min_length=1, max_length=100)

app = FastAPI(debug=False)

@app.post("/test-validation")
async def test_validation(payload: RequestModel):
    return {"accepted": True}

wrapped = ServerErrorMiddleware(
    ExceptionMiddleware(app, handlers=app.exception_handlers, debug=False),
    debug=False,
)

body = json.dumps({
    "events": [],
    "internal_probe": "VALIDATION_SECRET_MARKER"
}).encode()

messages = []
scope = {
    "type": "http",
    "asgi": {"version": "3.0", "spec_version": "2.3"},
    "http_version": "1.1",
    "method": "POST",
    "scheme": "http",
    "path": "/test-validation",
    "raw_path": b"/test-validation",
    "query_string": b"",
    "root_path": "",
    "headers": [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode()),
    ],
    "client": ("127.0.0.1", 12345),
    "server": ("127.0.0.1", 8000),
}

sent = False

async def receive():
    global sent
    if not sent:
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}
    return {"type": "http.disconnect"}

async def send(message):
    messages.append(message)

asyncio.run(wrapped(scope, receive, send))

start = next(m for m in messages if m["type"] == "http.response.start")
response_body = b"".join(
    m.get("body", b"")
    for m in messages
    if m["type"] == "http.response.body"
)
text = response_body.decode("utf-8", errors="replace")

try:
    parsed = json.loads(text)
except json.JSONDecodeError:
    parsed = {}

print("HTTP_STATUS=", start["status"])
print("JSON_RESPONSE=", isinstance(parsed, dict))
print("VALIDATION_DETAIL_PRESENT=", "detail" in parsed)
print("SECRET_MARKER_IN_RESPONSE=", "VALIDATION_SECRET_MARKER" in text)
print("EXTRA_INPUT_VALUE_IN_RESPONSE=", "internal_probe" in text)
print("TRACEBACK_IN_RESPONSE=", "Traceback" in text)
print("VALIDATION_DISCLOSURE_TEST=", "PASS" if (
    start["status"] == 422
    and "VALIDATION_SECRET_MARKER" not in text
    and "Traceback" not in text
) else "FAIL")
PY

echo
echo "PRODUCTION_SERVICE_TOUCHED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
```

**A problem was found.** The standard FastAPI/Pydantic `422` response included parts of the submitted body (entered values and values of extra fields). If a secret were sent by mistake, it would be returned in the response (this was found in an independent test; nothing leaked in production).

## Chapter 2: Making the `422` Response a Fixed Message

### 2.1 Checking the Impact

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: VALIDATION ERROR CLIENT COMPATIBILITY AUDIT ====="

echo
echo "--- 1. FastAPI / Pydantic versions ---"
./venv/bin/python - <<'PY'
import fastapi
import pydantic
print("FASTAPI_VERSION=", fastapi.__version__)
print("PYDANTIC_VERSION=", pydantic.__version__)
PY

echo
echo "--- 2. Validation error response references ---"
grep -RInE \
  'RequestValidationError|422|Unprocessable Entity|response\.json\(\).*detail|detail.*response|loc.*msg.*type' \
  app tests 2>/dev/null |
head -160

echo
echo "--- 3. API request models ---"
grep -RInE \
  '^class .*Request|^class .*Model|model_config|Field\(' \
  app/api app/models \
  --include='*.py' 2>/dev/null |
head -160

echo
echo "SOURCE_MODIFIED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
```

With FastAPI 0.165.0 and Pydantic 2.14.4, there was no client logic in the application that uses the details of `422`. Other error responses are fixed messages too, so we make `422` uniform in the following form.

```json
{
  "detail": "Invalid request"
}
```

### 2.2 Testing the Fix in an Independent Environment

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: ISOLATED VALIDATION SANITIZER TEST ====="

./venv/bin/python - <<'PY'
import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.exceptions import ExceptionMiddleware
from starlette.middleware.errors import ServerErrorMiddleware

class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[str] = Field(min_length=1, max_length=100)

app = FastAPI(debug=False)

@app.exception_handler(RequestValidationError)
async def sanitized_validation_error(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request"},
    )

@app.post("/test-validation")
async def test_validation(payload: RequestModel):
    return {"accepted": True}

wrapped = ServerErrorMiddleware(
    ExceptionMiddleware(app, handlers=app.exception_handlers, debug=False),
    debug=False,
)

body = json.dumps({
    "events": [],
    "internal_probe": "VALIDATION_SECRET_MARKER"
}).encode()

messages = []
scope = {
    "type": "http",
    "asgi": {"version": "3.0", "spec_version": "2.3"},
    "http_version": "1.1",
    "method": "POST",
    "scheme": "http",
    "path": "/test-validation",
    "raw_path": b"/test-validation",
    "query_string": b"",
    "root_path": "",
    "headers": [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode()),
    ],
    "client": ("127.0.0.1", 12345),
    "server": ("127.0.0.1", 8000),
}

sent = False

async def receive():
    global sent
    if not sent:
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}
    return {"type": "http.disconnect"}

async def send(message):
    messages.append(message)

asyncio.run(wrapped(scope, receive, send))

start = next(m for m in messages if m["type"] == "http.response.start")
response_body = b"".join(
    m.get("body", b"")
    for m in messages
    if m["type"] == "http.response.body"
)
text = response_body.decode("utf-8", errors="replace")

try:
    parsed = json.loads(text)
except json.JSONDecodeError:
    parsed = {}

print("HTTP_STATUS=", start["status"])
print("RESPONSE=", json.dumps(parsed, ensure_ascii=False))
print("SECRET_MARKER_IN_RESPONSE=", "VALIDATION_SECRET_MARKER" in text)
print("EXTRA_INPUT_VALUE_IN_RESPONSE=", "internal_probe" in text)
print("TRACEBACK_IN_RESPONSE=", "Traceback" in text)
print("SANITIZER_TEST=", "PASS" if (
    start["status"] == 422
    and parsed == {"detail": "Invalid request"}
    and "VALIDATION_SECRET_MARKER" not in text
    and "internal_probe" not in text
    and "Traceback" not in text
) else "FAIL")
PY

echo
echo "PRODUCTION_SOURCE_MODIFIED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
```

It remains `422`, but the response is now only `{"detail":"Invalid request"}`, with no entered values, values of extra fields or tracebacks.

### 2.3 Checking Before the Change

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: VALIDATION SANITIZER PRE-PATCH AUDIT ====="

echo
echo "--- Current source metadata ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s' app/main.py

echo
echo "--- Current source SHA256 ---"
sha256sum app/main.py

echo
echo "--- Existing approved backup ---"
if [ -f /var/backups/ai-defense-manager/api-auth-20261124/app-main.py ]; then
  stat -c 'BACKUP_OWNER=%U:%G MODE=%a SIZE=%s' \
    /var/backups/ai-defense-manager/api-auth-20261124/app-main.py
  sha256sum /var/backups/ai-defense-manager/api-auth-20261124/app-main.py
else
  echo "EXISTING_BACKUP_NOT_FOUND"
fi

echo
echo "--- Existing imports and app construction ---"
sed -n '1,12p' app/main.py
sed -n '82,125p' app/main.py

echo
echo "SOURCE_MODIFIED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "NETWORK_REQUESTS=NO"
```

```bash
echo "===== VM230: EXISTING SOURCE BACKUP INSPECTION ====="

BACKUP_DIR="/var/backups/ai-defense-manager/api-auth-20261124"

echo
echo "--- Backup directory ---"
ls -lah "$BACKUP_DIR"

echo
echo "--- Archive contents matching app/main.py ---"
find "$BACKUP_DIR" -maxdepth 1 -type f -name '*.tar*' -print0 |
while IFS= read -r -d '' archive; do
  echo "ARCHIVE=$archive"
  tar -tf "$archive" | grep -E '(^|/)app/main\.py$' || true
done

echo
echo "--- Current source metadata ---"
stat -c '%U:%G %a %s %n' /opt/ai-defense-manager/app/main.py

echo
echo "SOURCE_MODIFIED=NO"
echo "BACKUP_CREATED=NO"
echo "SERVICE_RESTARTED=NO"
```

```bash
echo "===== VM230: BACKUP INTEGRITY VERIFICATION ====="

cd /var/backups/ai-defense-manager/api-auth-20261124

echo
echo "--- Backup archive checksum ---"
sha256sum -c SHA256SUMS

echo
echo "--- Archived app/main.py checksum ---"
tar -xOzf application-source.tar.gz app/main.py | sha256sum

echo
echo "--- Current app/main.py checksum ---"
sha256sum /opt/ai-defense-manager/app/main.py

echo
echo "BACKUP_MODIFIED=NO"
echo "SOURCE_MODIFIED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

The integrity of the existing copy (`application-source.tar.gz`) passed, but the `app/main.py` inside it is from before API authentication was added, and its hash differs from the current one. **Do not overwrite the current source with this copy.**

### 2.4 Fixing `app/main.py`

We change only `app/main.py` and check the syntax. No service restart, no requests to the production API and no DB changes.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: APPLY VALIDATION ERROR SANITIZER ====="

./venv/bin/python - <<'PY'
from pathlib import Path
import os
import stat
import tempfile

path = Path("/opt/ai-defense-manager/app/main.py")
original = path.read_text(encoding="utf-8")
before_stat = path.stat()

if "RequestValidationError" in original or "Invalid request" in original:
    raise SystemExit("ABORT: validation handler may already exist")

old_import = "from fastapi import FastAPI\n"
new_import = (
    "from fastapi import FastAPI, Request\n"
    "from fastapi.exceptions import RequestValidationError\n"
    "from fastapi.responses import JSONResponse\n"
)

if original.count(old_import) != 1:
    raise SystemExit("ABORT: unexpected FastAPI import layout")

updated = original.replace(old_import, new_import, 1)

anchor = "app.add_middleware(\n"
handler = (
    "@app.exception_handler(RequestValidationError)\n"
    "async def sanitized_validation_error(\n"
    "    request: Request,\n"
    "    exc: RequestValidationError,\n"
    "):\n"
    '    return JSONResponse(status_code=422, content={"detail": "Invalid request"})\n'
    "\n\n"
)

if updated.count(anchor) != 1:
    raise SystemExit("ABORT: middleware insertion point is not unique")

updated = updated.replace(anchor, handler + anchor, 1)

fd, temp_name = tempfile.mkstemp(
    prefix=".main.py.",
    suffix=".tmp",
    dir=str(path.parent),
)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(updated)
        f.flush()
        os.fsync(f.fileno())

    os.chown(temp_name, before_stat.st_uid, before_stat.st_gid)
    os.chmod(temp_name, stat.S_IMODE(before_stat.st_mode))
    os.replace(temp_name, path)

    dir_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
except BaseException:
    try:
        os.unlink(temp_name)
    except FileNotFoundError:
        pass
    raise

print("SOURCE_PATCHED=YES")
print("OWNER_AND_MODE_PRESERVED=YES")
PY

echo
echo "--- Python syntax check ---"
./venv/bin/python -m py_compile app/main.py
echo "PYTHON_SYNTAX=PASS"

echo
echo "--- Patch diff ---"
diff -u <(git show HEAD:app/main.py 2>/dev/null || true) app/main.py | head -100

echo
echo "--- Current source metadata and hash ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s' app/main.py
sha256sum app/main.py

echo
echo "SERVICE_RESTARTED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "PRODUCTION_API_REQUESTS=NO"
```

> **Caution:** In the build records, no new copy was made at this point. When doing this in your own environment, it is safer to save a copy of `app/main.py` before the fix.

The syntax check passed and the owner and permissions were unchanged (the `diff` in the script has no original to compare with, so it shows the whole file as added).

### 2.5 Testing with the Fixed Application

We load the fixed `app.main.app` and check with independent requests.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: PATCHED APPLICATION VALIDATION TEST ====="

./venv/bin/python - <<'PY'
import asyncio
import json
import httpx
from pydantic import BaseModel, ConfigDict, Field
from app.main import app

class ProbeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[str] = Field(min_length=1, max_length=100)

async def temporary_probe(payload: ProbeRequest):
    return {"accepted": True}

app.add_api_route(
    "/__isolated_validation_probe",
    temporary_probe,
    methods=["POST"],
)

async def main():
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://isolated.test",
    ) as client:
        response = await client.post(
            "/__isolated_validation_probe",
            json={
                "events": [],
                "internal_probe": "VALIDATION_SECRET_MARKER",
            },
        )

    text = response.text
    try:
        data = response.json()
    except ValueError:
        data = None

    print("HTTP_STATUS=", response.status_code)
    print("RESPONSE=", json.dumps(data, ensure_ascii=False))
    print("SECRET_MARKER_IN_RESPONSE=", "VALIDATION_SECRET_MARKER" in text)
    print("EXTRA_FIELD_IN_RESPONSE=", "internal_probe" in text)
    print("TRACEBACK_IN_RESPONSE=", "Traceback" in text)

    passed = (
        response.status_code == 422
        and data == {"detail": "Invalid request"}
        and "VALIDATION_SECRET_MARKER" not in text
        and "internal_probe" not in text
        and "Traceback" not in text
    )
    print("PATCHED_APPLICATION_TEST=", "PASS" if passed else "FAIL")

asyncio.run(main())
PY

echo
echo "PRODUCTION_SERVICE_RESTARTED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "EXTERNAL_NETWORK_REQUESTS=NO"
```

`422`, the fixed response, and not exposing secret markers, extra fields or tracebacks all passed.

### 2.6 Final Source Check

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: FINAL SANITIZER SOURCE AUDIT ====="

echo
echo "--- 1. New handler and imports ---"
grep -n -A12 -B4 \
  'RequestValidationError\|sanitized_validation_error' \
  app/main.py

echo
echo "--- 2. Route and middleware declarations ---"
grep -nE \
  'add_middleware|include_router|@app\.get|@app\.exception_handler|docs_url|redoc_url|openapi_url|lifespan=' \
  app/main.py

echo
echo "--- 3. Authentication dependencies remain present ---"
grep -nE \
  'require_scope|Depends\(require_scope' \
  app/api/analysis.py app/api/wazuh.py

echo
echo "--- 4. Syntax and unit verification ---"
./venv/bin/python -m compileall -q app
echo "COMPILEALL=PASS"

systemd-analyze verify /etc/systemd/system/ai-defense-manager.service
echo "SYSTEMD_UNIT_VERIFY=PASS"

echo
echo "--- 5. Source metadata ---"
stat -c 'OWNER=%U:%G MODE=%a SIZE=%s' app/main.py
sha256sum app/main.py

echo
echo "PRODUCTION_SERVICE_RESTARTED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
```

The fixed `422` response handling, the API authentication dependencies, the `read` and `analyze` scopes, the 256KiB body limit, disabling of Swagger, ReDoc and OpenAPI, `compileall`, the systemd unit check and file ownership all passed.

### 2.7 Deploying to Production

> **Run on: VM 230**

```bash
echo "===== VM230: APPLY VALIDATION SANITIZER TO PRODUCTION ====="

echo
echo "--- 1. Restart service ---"
systemctl restart ai-defense-manager.service
RESTART_STATUS=$?
echo "RESTART_COMMAND_STATUS=$RESTART_STATUS"

echo
echo "--- 2. Wait for health endpoint ---"
HEALTH_STATUS=000
for i in $(seq 1 30); do
  HEALTH_STATUS="$(curl --silent --output /dev/null \
    --write-out '%{http_code}' --max-time 2 \
    http://127.0.0.1:8000/health 2>/dev/null || true)"
  if [ "$HEALTH_STATUS" = "200" ]; then
    break
  fi
  sleep 1
done
echo "HEALTH_HTTP_STATUS=$HEALTH_STATUS"

echo
echo "--- 3. Service runtime status ---"
systemctl show ai-defense-manager.service \
  -p ActiveState -p SubState -p MainPID \
  -p NRestarts -p Result \
  -p ExecMainStartTimestamp --no-pager

echo
echo "--- 4. Listener ---"
ss -lntp | grep '127.0.0.1:8000' || true

echo
echo "PRODUCTION_SANITIZER_SOURCE_SHA256=41ee62dca6cc02818a7f70b4b8d7bb63500d294fb5429300b86e252e44a161ef"
echo "WAZUH_REQUESTS=NO"
echo "OLLAMA_REQUESTS=NO"
echo "TOKEN_VALUE_DISPLAYED=NO"
```

`active (running)` (MainPID `2340`, 0 restart failures); `/health` gave `HTTP 200`; listening on `127.0.0.1:8000`.

We send one authenticated request to the production analysis API. It gives `422` at input validation, so it does not proceed to AI analysis.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: PRODUCTION VALIDATION SANITIZER TEST ====="

./venv/bin/python - <<'PY'
import json
from pathlib import Path
import httpx

token = Path("/root/ai-defense-client.token").read_text(
    encoding="ascii"
).strip()

marker = "PRODUCTION_VALIDATION_SECRET_MARKER"

response = httpx.post(
    "http://127.0.0.1:8000/api/v1/analysis",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "events": [],
        "internal_probe": marker,
    },
    timeout=10.0,
)

try:
    data = response.json()
except ValueError:
    data = None

body = response.text

print("HTTP_STATUS=", response.status_code)
print("RESPONSE=", json.dumps(data, ensure_ascii=False))
print("SECRET_MARKER_IN_RESPONSE=", marker in body)
print("EXTRA_FIELD_IN_RESPONSE=", "internal_probe" in body)
print("TRACEBACK_IN_RESPONSE=", "Traceback" in body)
print("TOKEN_VALUE_DISPLAYED=NO")

passed = (
    response.status_code == 422
    and data == {"detail": "Invalid request"}
    and marker not in body
    and "internal_probe" not in body
    and "Traceback" not in body
)
print("PRODUCTION_SANITIZER_TEST=", "PASS" if passed else "FAIL")
print("ANALYSIS_EXECUTION=NO")
print("HISTORY_WRITES=NO")
print("WAZUH_REQUESTS=NO")
print("OLLAMA_REQUESTS=NO")
PY
```

| Checked | Result |
|---|---|
| Invalid request | `HTTP 422` |
| Response | `{"detail":"Invalid request"}` |
| Entered secret markers, values of extra fields, tracebacks | not leaked |

## Chapter 3: Final Check of Error Responses

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: API ERROR DISCLOSURE FINAL AUDIT ====="

echo
echo "--- 1. HTTP error response declarations ---"
grep -RInE \
  'HTTPException|JSONResponse|PlainTextResponse|Response\(' \
  app --include='*.py' || true

echo
echo "--- 2. Exception disclosure patterns ---"
grep -RInE \
  'str\(e\)|str\(exc\)|repr\(e\)|repr\(exc\)|traceback|format_exc|exc_info|debug=True|reload=True' \
  app --include='*.py' || true

echo
echo "--- 3. Logging and print statements ---"
grep -RInE \
  'logger\.(debug|info|warning|error|exception)|logging\.|print\(' \
  app --include='*.py' || true

echo
echo "--- 4. Token exposure patterns ---"
grep -RInE \
  'Authorization|access_token|secret_hash|token_value|api_token|Bearer' \
  app --include='*.py' || true

echo
echo "--- 5. Service runtime ---"
systemctl show ai-defense-manager.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p Result \
  --no-pager

echo
echo "READ_ONLY_AUDIT=YES"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
```

```bash
cd /opt/ai-defense-manager

echo "===== VM230: HTTP ERROR DETAIL REVIEW ====="

echo
echo "--- analysis.py ---"
nl -ba app/api/analysis.py | sed -n '1,120p'

echo
echo "--- wazuh.py ---"
nl -ba app/api/wazuh.py | sed -n '1,140p'

echo
echo "--- api_auth.py ---"
nl -ba app/core/api_auth.py | sed -n '1,100p'

echo
echo "--- relay error definitions and handling ---"
grep -n -A8 -B5 \
  'class WazuhRelayError\|raise WazuhRelayError\|raise .*Error' \
  app/services/wazuh_relay.py

echo
echo "READ_ONLY=YES"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
```

No place was found that outputs `str(exc)`, `repr(exc)` or tracebacks to responses or logs as is; AI analysis failures, history storage failures, Relay failures, authentication failures, insufficient privilege and token DB faults all returned fixed messages.

> **Run on: VM 230**

```bash
cd /opt/ai-defense-manager

echo "===== VM230: UNHANDLED EXCEPTION CONFIGURATION AUDIT ====="

echo
echo "--- 1. FastAPI application configuration ---"
nl -ba app/main.py | sed -n '80,150p'

echo
echo "--- 2. Uvicorn service command and environment ---"
systemctl cat ai-defense-manager.service

echo
echo "--- 3. Exception handler declarations ---"
grep -RInE \
  '@app\.exception_handler|add_exception_handler|exception_handler\(' \
  app --include='*.py' || true

echo
echo "--- 4. Runtime status ---"
systemctl show ai-defense-manager.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p Result \
  --no-pager

echo
echo "READ_ONLY=YES"
echo "PRODUCTION_REQUESTS=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
```

There is no application-specific handling for unexpected exceptions, but we confirmed in Chapter 1 that with FastAPI `debug=False`, unhandled exceptions return only `HTTP 500 Internal Server Error`. We judged that no fix is needed now.

## Chapter 4: Log Destinations and Permissions

### 4.1 Uvicorn Logs

> **Run on: VM 230**

```bash
echo "===== VM230: UVICORN LOGGING SECURITY AUDIT ====="

echo
echo "--- 1. Effective ExecStart ---"
systemctl show ai-defense-manager.service \
  -p ExecStart --no-pager

echo
echo "--- 2. Uvicorn process command line ---"
tr '\0' ' ' < /proc/2340/cmdline
echo

echo
echo "--- 3. Service journal configuration ---"
systemctl show ai-defense-manager.service \
  -p StandardOutput -p StandardError \
  -p SyslogIdentifier -p LogRateLimitIntervalUSec \
  -p LogRateLimitBurst --no-pager

echo
echo "--- 4. Recent service log metadata (no message contents) ---"
journalctl -u ai-defense-manager.service -n 30 \
  --no-pager -o json |
python3 -c '
import sys, json
for line in sys.stdin:
    try:
        r = json.loads(line)
        print(
            "PRIORITY=" + str(r.get("PRIORITY", "")),
            "UNIT=" + str(r.get("_SYSTEMD_UNIT", "")),
            "MESSAGE_PRESENT=" + str(bool(r.get("MESSAGE"))),
            "MESSAGE_LENGTH=" + str(len(r.get("MESSAGE", ""))),
        )
    except Exception:
        print("JOURNAL_ENTRY_PARSE=FAILED")
'

echo
echo "--- 5. Journal directory permissions ---"
stat -c '%A %U:%G %n' /var/log/journal /run/log/journal 2>/dev/null || true

echo
echo "READ_ONLY=YES"
echo "PRODUCTION_DB_MODIFIED=NO"
echo "NETWORK_REQUESTS=NO"
```

| Item | Result |
|---|---|
| Listening | `127.0.0.1:8000` |
| Concurrent connections, Keep-Alive | 8, 5 seconds |
| Log destination | the systemd journal (standard error also goes to the journal) |
| Journal directory | `root:systemd-journal` |

`--log-level` is not specified; Uvicorn's default log level applies.

### 4.2 Journal Permissions and Retention

> **Run on: VM 230**

```bash
echo "===== VM230: JOURNAL ACCESS AND RETENTION AUDIT ====="

echo
echo "--- 1. Journal disk usage ---"
journalctl --disk-usage

echo
echo "--- 2. Journal configuration ---"
grep -RInE \
  '^[[:space:]]*(Storage|Compress|Seal|SplitMode|SystemMaxUse|SystemKeepFree|SystemMaxFileSize|RuntimeMaxUse|RuntimeKeepFree|RuntimeMaxFileSize|MaxRetentionSec|MaxFileSec|ForwardToSyslog|ForwardToConsole)[[:space:]]*=' \
  /etc/systemd/journald.conf \
  /etc/systemd/journald.conf.d \
  2>/dev/null || true

echo
echo "--- 3. Journal ACL and permissions ---"
namei -l /var/log/journal
getfacl -cp /var/log/journal 2>/dev/null || true

echo
echo "--- 4. Journal group members ---"
getent group systemd-journal

echo
echo "--- 5. Service account group membership ---"
id ai-defense

echo
echo "--- 6. Journal service status ---"
systemctl is-active systemd-journald.service

echo
echo "READ_ONLY=YES"
echo "CONFIGURATION_MODIFIED=NO"
echo "PRODUCTION_DB_MODIFIED=NO"
```

```bash
echo "===== VM230: JOURNAL FILE PERMISSION AUDIT ====="

echo
echo "--- 1. Journal files ---"
find /var/log/journal -type f \
  -printf '%M %u:%g %s %p\n' 2>/dev/null

echo
echo "--- 2. Journal directory tree permissions ---"
find /var/log/journal -type d \
  -printf '%M %u:%g %p\n' 2>/dev/null

echo
echo "--- 3. Effective journald settings ---"
systemd-analyze cat-config systemd/journald.conf

echo
echo "--- 4. Journal runtime limits ---"
systemctl show systemd-journald.service \
  -p MemoryCurrent -p TasksCurrent -p LimitNOFILE \
  --no-pager

echo
echo "READ_ONLY=YES"
echo "JOURNAL_FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Item | Result |
|---|---|
| Space used | 89.0MB |
| Journal files | `root:systemd-journal`, `640` |
| Journal directory | `2755` |
| `systemd-journal` group | no users registered |
| `ai-defense` | not in the `systemd-journal` group |
| Retention period and size settings | no explicit settings (set in Part 61) |

### 4.3 syslog

> **Run on: VM 230**

```bash
echo "===== VM230: SYSLOG FORWARDING AUDIT ====="

echo
echo "--- 1. Syslog services ---"
systemctl is-active rsyslog.service 2>/dev/null || true
systemctl is-active syslog-ng.service 2>/dev/null || true

echo
echo "--- 2. Syslog listeners ---"
ss -lntup | grep -E ':(514|601|6514)\b' || true

echo
echo "--- 3. Syslog configuration files ---"
find /etc/rsyslog.d /etc/syslog-ng \
  -maxdepth 2 -type f -printf '%M %u:%g %p\n' \
  2>/dev/null || true

echo
echo "--- 4. Syslog spool and log directories ---"
stat -c '%A %U:%G %n' \
  /var/log/syslog /var/log/auth.log \
  /var/spool/rsyslog /var/log 2>/dev/null || true

echo
echo "--- 5. Syslog-related processes ---"
ps -eo user,group,pid,args |
  grep -E '[r]syslogd|[s]yslog-ng'

echo
echo "READ_ONLY=YES"
echo "LOG_CONFIGURATION_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
```

The log path is as follows.

```text
AI Defense Manager
        |
        v
systemd-journald
        |
        | ForwardToSyslog=yes
        v
      rsyslog
        |
        +---- /var/log/syslog
        |
        +---- /var/log/auth.log
```

> **Run on: VM 230**

```bash
echo "===== VM230: SYSLOG READER AND ROUTING AUDIT ====="

echo
echo "--- 1. adm group members ---"
getent group adm

echo
echo "--- 2. syslog group members ---"
getent group syslog

echo
echo "--- 3. AI Defense account groups ---"
id ai-defense

echo
echo "--- 4. rsyslog routing configuration ---"
sed -n '1,240p' /etc/rsyslog.d/50-default.conf
sed -n '1,160p' /etc/rsyslog.d/21-cloudinit.conf
sed -n '1,160p' /etc/rsyslog.d/20-ufw.conf

echo
echo "--- 5. Logrotate configuration ---"
grep -RInE \
  'syslog|auth\.log|rotate|size|daily|weekly|monthly|compress|create' \
  /etc/logrotate.conf /etc/logrotate.d/rsyslog \
  2>/dev/null || true

echo
echo "READ_ONLY=YES"
echo "LOGS_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
```

| Item | Result |
|---|---|
| rsyslog | `active` (user `syslog`); no syslog-ng |
| `/var/log/syslog`, `/var/log/auth.log` | `syslog:adm`, `640` |
| `/var/spool/rsyslog` | `syslog:adm`, `700` |
| Listening for syslog from outside | none |
| `adm` group | `syslog`, `aidefense` (`ai-defense` is not a member) |
| Routing | auth/authpriv separated from ordinary logs |
| logrotate | weekly, 4 generations, compressed |

### 4.4 Log Permissions After Rotation

> **Run on: VM 230**

```bash
echo "===== VM230: ROTATED LOG PERMISSION AUDIT ====="

echo
echo "--- 1. Current and rotated syslog files ---"
find /var/log -maxdepth 1 -type f \
  \( -name 'syslog*' -o -name 'auth.log*' \) \
  -printf '%M %u:%g %s %p\n' | sort

echo
echo "--- 2. Logrotate rsyslog policy ---"
cat /etc/logrotate.d/rsyslog

echo
echo "--- 3. Logrotate timer and service ---"
systemctl status logrotate.timer --no-pager 2>/dev/null || true
systemctl status logrotate.service --no-pager 2>/dev/null || true

echo
echo "--- 4. Logrotate state metadata ---"
stat -c '%A %U:%G %s %n' /var/lib/logrotate/status 2>/dev/null || true

echo
echo "READ_ONLY=YES"
echo "LOGS_MODIFIED=NO"
echo "ROTATION_TRIGGERED=NO"
echo "SERVICES_RESTARTED=NO"
```

`syslog`, `syslog.1`, `auth.log` and `auth.log.1` were all `syslog:adm`, `640`. `logrotate.timer` is `active`.

## Closing Notes

In Part 60 we checked API error responses and log permissions, and fixed the problem of values leaking from input validation errors.

| Item | Result |
|---|---|
| Error responses | all fixed messages; unhandled exceptions give only `500 Internal Server Error` |
| `422` response | unified as `{"detail":"Invalid request"}` (confirmed in production) |
| Logs | journal `640`, `2755`; syslog `syslog:adm`, `640`; the service account cannot read the logs |
| Remaining | journal retention period and size not explicitly set |

In the next part, Part 61, we set a size limit for the journal and check log management as a whole.

# Part 61: Checking Logs for Secrets and Capping the Journal Size
## Introduction

### About This Book

This is Part 61 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 60 we checked API error responses and log permissions. Here we do the following.

1. Check, by counts only, whether token-like strings remain in syslog and the journal
2. Examine the journal's retention period and growth, decide a size limit and set it
3. Restart journald to apply the settings, and check the integrity of the journal
4. Check log management as a whole: journald, rsyslog and logrotate

Log bodies are not displayed. Existing logs are not deleted.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

## Chapter 1: Do Secrets Remain in the Logs?

### 1.1 The Current syslog and auth.log

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

### 1.2 Rotated Logs

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

### 1.3 The Journal

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

## Chapter 2: Journal Settings and Retention

### 2.1 The Current Settings

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

### 2.2 Storage State and Integrity

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

### 2.3 How Many Days Are Kept

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

## Chapter 3: Setting the Size Limit

### 3.1 Checking Before the Change

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

### 3.2 Adding the Configuration File

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

### 3.3 Checks Before Applying

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

### 3.4 Restarting journald

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

### 3.5 Integrity After the Restart

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

## Chapter 4: Log Management as a Whole

### 4.1 Storage Locations and logrotate

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

### 4.2 Size and Retention Period

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

### 4.3 logrotate

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

### 4.4 rsyslog

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

## Closing Notes

In Part 61 we confirmed that no secrets remain in the logs and set a size limit for the journal.

| Item | Result |
|---|---|
| Checking logs for secrets | 0 matches in syslog, auth.log and the journal |
| Journal limits | `SystemMaxUse=512M`, `SystemKeepFree=2G`, `SystemMaxFileSize=64M` (`60-ai-defense-retention.conf`) |
| Applying | journald restarted; integrity check: 18 passed, 0 failed |
| syslog | weekly, 4 generations, compressed, `syslog:adm`, `640` |

The journald settings showed `Seal=yes` (default), but whether a sealing key is actually in use is checked in the next part, Part 62. This is to make log tampering detectable.

# Part 62: Creating FSS Keys to Guard Against Log Tampering
## Introduction

### About This Book

This is Part 62 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 61 we set a size limit for the journal. Here, after a final check of who can read the logs, we prepare **a mechanism for detecting that logs have been rewritten**.

The systemd journal has a mechanism called **FSS (Forward Secure Sealing)**.

- The secret sealing key (Seal key) is kept inside the VM and seals the journal at fixed intervals (here, 15 minutes). The key moves forward with time, and keys for earlier intervals do not remain
- The verification key is stored outside the VM, and `journalctl --verify --verify-key=…` checks that nothing was rewritten after sealing

The setting `Seal=yes` (default) alone does not make FSS work; the keys must be created with `journalctl --setup-keys`.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

> **Caution:** Do not display or paste the contents of the verification key.

## Chapter 1: Final Check of Who Can Read the Logs

### 1.1 syslog

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

### 1.2 The Journal

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

### 1.3 Integrity and Persistent Storage

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

## Chapter 2: Is FSS Supported?

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

## Chapter 3: Creating the FSS Keys

### 3.1 Creating the Keys

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

### 3.2 Checking the Key Format

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

## Closing Notes

In Part 62 we checked who can read the logs and created the FSS keys.

| Item | Result |
|---|---|
| Log permissions | the service account cannot read either syslog or the journal |
| FSS support | supported in systemd 255; `Seal` enabled by default |
| FSS keys | created with a 15-minute interval. The secret side is in VM 230's journal directory (`600`); the verification key is `/root/fss-verification-key-20261124.txt` (`600`) |
| Still to do | store the verification key outside the VM; confirm that sealing begins |

We decided to store the verification key in **a root-only location on the Proxmox host `pve`**. In the next part, Part 63, we move it safely from VM 230.

# Part 63: Moving the FSS Verification Key to the Proxmox Host
## Introduction

### About This Book

This is Part 63 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". We move the FSS verification key created in Part 62 outside VM 230, to **`/root` on the Proxmox host `pve`** (root only).

1. Check the destination `pve` and the path from VM 230
2. Compare `pve`'s SSH host key with the value seen on its console, then register it on VM 230
3. On VM 230, create an SSH key used only for moving files to `pve`, and register the public key on `pve` with restrictions (`restrict`)
4. Move the verification key and confirm the match with SHA-256

Methods that disable SSH host key checking are not used.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **pve**: the Proxmox host (root). The Shell (console) of node `pve` in the Proxmox web interface

> **Caution:** Run the VM 230 commands only after checking that the prompt is `root@ai-defense-manager`. Running them on `pve` would check a connection to `pve` itself. Running them as an ordinary user (`aidefense`) fails because the root-only key cannot be read.

## Chapter 1: Destination and Path

### 1.1 The `pve` Side

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

### 1.2 The VM 230 Side

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

## Chapter 2: Checking and Registering `pve`'s Host Key

### 2.1 Viewing the Fingerprint on the Console

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

### 2.2 Comparing with the Value Seen from VM 230

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

### 2.3 Registering in `known_hosts`

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

## Chapter 3: The SSH Key for Moving Files

### 3.1 Creating the Key on VM 230

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

### 3.2 The Structure of `authorized_keys` on `pve`

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

### 3.3 Registering the Public Key

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

### 3.4 Testing Authentication

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

## Chapter 4: Moving the Verification Key

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

## Closing Notes

In Part 63 we stored the FSS verification key outside VM 230 (in `/root` on `pve`).

| Item | Result |
|---|---|
| `pve` host key | registered in `known_hosts` after comparing with the console value |
| Key for moving files | VM 230 `/root/.ssh/id_ed25519_pve_fss`; registered in `pve`'s `/etc/pve/priv/authorized_keys` with `restrict` |
| Verification key | `pve` `/root/fss-verification-key-20261124.txt` (`600`, SHA-256 match) |
| Still to do | have journald load the sealing key and confirm that sealing begins |

In the next part, Part 64, we start FSS sealing.

# Part 64: Running and Checking FSS Sealing
## Introduction

### About This Book

This is Part 64 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 62 we created the FSS keys, and in Part 63 we moved the verification key to the Proxmox host. Here we have journald start sealing and check it with the verification key.

1. Restart journald and check the sealing state
2. Investigate why the seal tags (`Tag objects`) stayed at 0
3. Switch the journal (`journalctl --rotate`) to create a new file and confirm it is sealed
4. Check the sealed journal cryptographically with the verification key

No log deletion, size cleanup or key changes.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

## Chapter 1: Restarting journald

### 1.1 Restart and Sealing State

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

### 1.2 Checking After Some Time

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

## Chapter 2: Why the Tags Were 0

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

## Chapter 3: Switching the Journal

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

## Chapter 4: Checking with the Verification Key

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

## Closing Notes

In Part 64 we started FSS sealing of VM 230's journal and checked it cryptographically.

| Item | Result |
|---|---|
| Why the tags were 0 | it kept using a journal file created before the FSS keys |
| Fix | created a new file with `journalctl --rotate` |
| Sealing | `SEALED SEALED_CONTINUOUS`, `Tag objects` 7 |
| Verification | `journalctl --verify --verify-key` gave `PASS` |

However, this verification was done inside VM 230. In case VM 230 is compromised, in the next part, Part 65, we check it **on a host other than VM 230**.

# Part 65: Checking FSS from Another Host (VM 240)
## Introduction

### About This Book

This is Part 65 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 64 we started FSS sealing of VM 230's journal and checked it inside VM 230. So that the result can be trusted even if VM 230 is compromised, we check it **on a host other than VM 230**.

1. Bundle the sealed journal (switch it into an archive) and move it to the Proxmox host `pve`
2. systemd 252 on `pve` cannot verify this form of journal, so create VM 240 (Ubuntu 24.04, systemd 255) dedicated to verification
3. Move the journal and verification key from `pve` to VM 240 and check them cryptographically on VM 240
4. Confirm that the files have not changed in all three places: VM 230 (where it was made), `pve` (where it is stored) and VM 240 (where it was checked)

The contents of the verification key are not displayed.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)
  - **pve**: the Proxmox host (root)
  - **VM 240**: fss-verification (`192.168.0.222`, root. When logged in as an ordinary user, become root with `sudo -i`)

## Chapter 1: Moving the Sealed Journal to `pve`

### 1.1 Creating an Archive for Verification

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

### 1.2 Moving It to `pve`

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

### 1.3 `pve` Cannot Verify It

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

## Chapter 2: Creating VM 240 for Verification

### 2.1 Resources and the ISO

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

### 2.2 Is VMID 240 Free?

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

### 2.3 Creating VM 240

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

### 2.4 Starting It and Installing the OS

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

### 2.5 Checking After Installation

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

### 2.6 Checking SSH

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

## Chapter 3: Moving to VM 240 and Checking

### 3.1 Checks on the `pve` Side

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

### 3.2 Moving

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

### 3.3 Confirming the Match on VM 240

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

### 3.4 Placing Them in a Root-Only Location

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

### 3.5 Checking on VM 240

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

## Chapter 4: Final Check in Three Places

### 4.1 VM 240

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

### 4.2 `pve`

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

### 4.3 VM 230

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

## Closing Notes

In Part 65 we checked VM 230's FSS-sealed journal on another host (VM 240).

| Item | Result |
|---|---|
| Archive for verification | VM 230 → `pve` → VM 240, SHA-256 matching everywhere |
| `pve` | cannot verify this form of journal because of systemd 252 (storage only) |
| VM 240 | Ubuntu 24.04.5, systemd 255.4, 2 vCPUs, 4GiB, 32GiB, `192.168.0.222` |
| Verification on another host | passed |

In the next part, Part 66, we make this verification run automatically every 15 minutes.

# Part 66: Automating FSS Verification Every 15 Minutes
## Introduction

### About This Book

This is Part 66 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 65 we checked the FSS-sealed journal on another host. Here we make VM 230 run FSS verification **automatically every 15 minutes**.

1. Examine the structure of the existing AI Defense Manager and decide where to integrate verification
2. Use the headers to decide which journals are verification targets
3. Create the verification script, a systemd service and a timer, and run it once by hand
4. Enable the timer and confirm that it ran automatically
5. Investigate whether verification results can be reported to Wazuh

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root. When logged in as `aidefense`, become root with `sudo -i`)

## Chapter 1: Deciding Where to Integrate

### 1.1 Service Structure

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

### 1.2 Application Structure

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

### 1.3 Service Security Settings

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

## Chapter 2: Deciding the Verification Targets

### 2.1 Journal Files

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

### 2.2 Sorting by Header

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

### 2.3 Checking the Current Journal as a Baseline

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

## Chapter 3: Building the Verification Mechanism

### 3.1 Creating Three Files

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

### 3.2 Static Checks

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

### 3.3 Registering and Running It Once by Hand

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

## Chapter 4: Enabling the Timer

### 4.1 Enabling

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

### 4.2 Checking That It Ran Automatically

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

## Chapter 5: Can Wazuh Be Notified?

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

## Closing Notes

In Part 66 we made FSS verification run automatically every 15 minutes.

| Item | Result |
|---|---|
| Verification script | `/usr/local/sbin/ai-defense-fss-verify` (`0750`) |
| Service and timer | `ai-defense-fss-verify.service` (oneshot, read-only) and `.timer` (5 minutes after boot, then every 15 minutes) |
| Targets | system journals with `SEALED`, `SEALED_CONTINUOUS` and `Tag objects` 1 or more (older ones are `SKIP`) |
| Results | `PASS` 2, `SKIP` 13, 0 failures (once by hand, once automatically) |
| Integration with Wazuh | none yet; VM 230 has no agent |

In the next part, Part 67, before integration, we examine the Wazuh Manager side on VM 220. There, a problem is found in Wazuh's local rules file.

# Part 67: Finding the Breakage in Wazuh's Local Rules
## Introduction

### About This Book

This is Part 67 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 66 we automated FSS verification on VM 230, but there was no path to report its results to Wazuh. Here, before integration, we examine the Wazuh Manager side on VM 220, read-only.

1. Check whether Wazuh Manager is configured to accept agents
2. Investigate the role of the Relay (8765) (a read-only API, not an entry point for events)
3. Find that the local rules `local_rules.xml` are broken as XML, and examine their structure
4. Without touching the production file, create a fixed candidate file

No configuration changes, agent registration, communication tests or service restarts. Credentials and secret keys are not displayed.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)

## Chapter 1: Wazuh Manager and the Relay

### 1.1 Configuration for Accepting Agents

> **Run on: VM 220**

```bash
echo "===== VM220: WAZUH MANAGER RECEIVER PREFLIGHT ====="

echo
echo "--- 1. Host identity and OS ---"
hostname
id
. /etc/os-release
echo "$PRETTY_NAME"

echo
echo "--- 2. Wazuh manager package ---"
dpkg-query -W -f='${Status} ${Version}\n' wazuh-manager 2>&1 || true

echo
echo "--- 3. Wazuh manager service state ---"
systemctl show wazuh-manager.service \
  -p LoadState -p ActiveState -p SubState \
  -p MainPID -p NRestarts -p FragmentPath 2>&1

echo
echo "--- 4. Wazuh manager process summary ---"
pgrep -a -f 'wazuh-manager|wazuh-analysisd|wazuh-remoted|wazuh-db|wazuh-logcollector' \
  || echo "NO_WAZUH_MANAGER_PROCESS_FOUND"

echo
echo "--- 5. Manager configuration metadata ---"
if [ -f /var/ossec/etc/ossec.conf ]; then
    stat -c '%A %a %U:%G %s %n' /var/ossec/etc/ossec.conf
    echo "MANAGER_CONFIG_EXISTS=YES"
else
    echo "MANAGER_CONFIG_EXISTS=NO"
fi

echo
echo "--- 6. Agent connection configuration (selected non-secret fields) ---"
if [ -f /var/ossec/etc/ossec.conf ]; then
    grep -nE '<remote>|</remote>|<connection>|</connection>|<port>|</port>|<protocol>|</protocol>|<secure>|</secure>|<queue_size>|</queue_size>|<agents_disconnection_time>|</agents_disconnection_time>' \
      /var/ossec/etc/ossec.conf 2>/dev/null || true
fi

echo
echo "--- 7. Wazuh enrollment service configuration (non-secret fields only) ---"
if [ -f /var/ossec/etc/ossec.conf ]; then
    awk '
      /<auth>/ { inside=1; print; next }
      inside {
        if ($0 ~ /<disabled>|<\/disabled>|<use_source_ip>|<\/use_source_ip>|<force>|<\/force>|<purge>|<\/purge>|<use_password>|<\/use_password>|<port>|<\/port>/)
          print
        if (/<\/auth>/) { print; inside=0 }
      }
    ' /var/ossec/etc/ossec.conf
fi

echo
echo "--- 8. TLS Relay service state ---"
systemctl list-units --type=service --all --no-legend \
  | grep -iE 'relay|tls' || true

echo
echo "--- 9. TCP listener summary for relevant ports ---"
ss -lntp 2>/dev/null \
  | awk 'NR==1 || /:8765[[:space:]]|:1514[[:space:]]|:1515[[:space:]]/'

echo
echo "--- 10. Wazuh manager agent inventory (counts only) ---"
if [ -x /var/ossec/bin/agent_control ]; then
    /var/ossec/bin/agent_control -l 2>&1 \
      | awk '
          /ID:/ { total++ }
          /Active/ { active++ }
          /Disconnected/ { disconnected++ }
          END {
            printf "AGENT_LIST_ENTRIES=%d\n", total
            printf "ACTIVE_LINES=%d\n", active
            printf "DISCONNECTED_LINES=%d\n", disconnected
          }'
else
    echo "AGENT_CONTROL_NOT_FOUND"
fi

echo
echo "--- 11. Wazuh manager recent service status ---"
systemctl show wazuh-manager.service \
  -p Result -p ExecMainStatus -p ActiveEnterTimestamp \
  -p ActiveState -p SubState

echo
echo "READ_ONLY_PREFLIGHT=YES"
echo "CONFIGURATION_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
echo "SECRETS_DISPLAYED=NO"
```

| Item | Result |
|---|---|
| Wazuh Manager 4.14.10 | `active (running)` |
| Agent communication | listening on TCP 1514 (`secure`) |
| Agent registration | listening on TCP 1515 |
| Registered agents | 5 |
| Relay | `ai-defense-relay.service`, `192.168.0.220:8765` |

### 1.2 The Relay's Structure

> **Run on: VM 220**

```bash
echo "===== VM220: TLS RELAY IMPLEMENTATION DISCOVERY ====="

echo
echo "--- 1. Relay service systemd metadata ---"
systemctl show ai-defense-relay.service \
  -p LoadState -p ActiveState -p SubState \
  -p MainPID -p NRestarts -p FragmentPath \
  -p User -p Group -p WorkingDirectory \
  -p EnvironmentFiles

echo
echo "--- 2. Relay process executable and working directory ---"
PID="$(systemctl show ai-defense-relay.service -p MainPID --value)"
if [ -n "$PID" ] && [ "$PID" != "0" ] && [ -d "/proc/$PID" ]; then
    printf 'PID=%s\n' "$PID"
    printf 'EXE='
    readlink "/proc/$PID/exe" || true
    printf 'CWD='
    readlink "/proc/$PID/cwd" || true
else
    echo "RELAY_PROCESS_NOT_FOUND"
fi

echo
echo "--- 3. Relay service unit file metadata ---"
UNIT="$(systemctl show ai-defense-relay.service -p FragmentPath --value)"
if [ -n "$UNIT" ] && [ -f "$UNIT" ]; then
    stat -c '%A %a %U:%G %s %n' "$UNIT"
else
    echo "UNIT_FILE_NOT_FOUND"
fi

echo
echo "--- 4. Relay working-directory file inventory ---"
if [ -n "$PID" ] && [ "$PID" != "0" ] && [ -d "/proc/$PID" ]; then
    RELAY_CWD="$(readlink -f "/proc/$PID/cwd")"
    if [ -d "$RELAY_CWD" ]; then
        find "$RELAY_CWD" -maxdepth 2 -type f \
          -printf '%M %u:%g %s %p\n' 2>/dev/null \
          | head -60
    fi
fi

echo
echo "--- 5. Relay-related systemd drop-in metadata ---"
systemctl show ai-defense-relay.service -p DropInPaths
systemctl show ai-defense-relay.service -p FragmentPath --value \
  | while IFS= read -r f; do
      [ -n "$f" ] && [ -d "${f}.d" ] && \
        find "${f}.d" -maxdepth 1 -type f \
          -printf '%M %u:%g %s %p\n'
    done

echo
echo "--- 6. Relay listener confirmation ---"
ss -lntp 2>/dev/null | awk 'NR==1 || /:8765[[:space:]]/'

echo
echo "--- 7. Wazuh custom integration and rules directory metadata ---"
for d in /var/ossec/integrations /var/ossec/etc/rules /var/ossec/etc/decoders; do
    if [ -d "$d" ]; then
        printf '\nDIRECTORY=%s\n' "$d"
        find "$d" -maxdepth 1 -type f \
          -printf '%M %u:%g %s %f\n' 2>/dev/null \
          | head -40
    else
        echo "NOT_FOUND=$d"
    fi
done

echo
echo "READ_ONLY_RELAY_DISCOVERY=YES"
echo "RELAY_CONFIG_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
echo "SECRETS_DISPLAYED=NO"
```

The Relay runs `/opt/ai-defense-relay/relay.py` with Python 3.12 as the dedicated user `ai-defense-relay`. Wazuh had `local_rules.xml` and `local_decoder.xml`.

### 1.3 The Relay's GET and POST

> **Run on: VM 220**

```bash
echo "===== VM220: TLS RELAY GET POST BEHAVIOR AUDIT ====="

python3 - <<'PY'
import ast
from pathlib import Path

p = Path("/opt/ai-defense-relay/relay.py")
tree = ast.parse(p.read_text(encoding="utf-8"))

cls = next(n for n in tree.body
           if isinstance(n, ast.ClassDef) and n.name == "RelayHandler")

for method_name in ("do_GET", "do_POST", "do_PUT", "do_DELETE"):
    method = next((n for n in cls.body
                   if isinstance(n, ast.FunctionDef) and n.name == method_name), None)
    print(f"\n--- {method_name} ---")
    if method is None:
        print("NOT_DEFINED")
        continue

    for node in ast.walk(method):
        if isinstance(node, ast.If):
            print(f"IF_CONDITION={ast.unparse(node.test)[:240]}")
        elif isinstance(node, ast.Call):
            func = ast.unparse(node.func)
            if any(x in func.lower() for x in (
                "send_json", "urlopen", "request", "json.loads",
                "json.dumps", "credential", "sanitize_alert"
            )):
                print(f"CALL={func}")
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (str, int)):
                v = node.value
                if isinstance(v, str) and (
                    v.startswith("/") or v in ("GET", "POST", "Unauthorized",
                                               "Not Found", "Method Not Allowed")
                ):
                    print(f"CONSTANT={v!r}")
                elif isinstance(v, int) and 100 <= v <= 599:
                    print(f"HTTP_STATUS={v}")

print("\n--- Helper function names and call relationships ---")
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        calls = sorted({
            ast.unparse(x.func)
            for x in ast.walk(node)
            if isinstance(x, ast.Call)
        })
        print(f"FUNCTION={node.name} CALLS={','.join(calls[:20])}")

print("\nSTATIC_ANALYSIS_ONLY=YES")
print("SOURCE_CONTENT_DISPLAYED=NO")
print("SECRET_VALUES_DISPLAYED=NO")
PY

echo
echo "--- Relay process health ---"
systemctl show ai-defense-relay.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts
```

| Item | Result |
|---|---|
| `GET /health` | status check |
| `GET /v1/alerts` | search of Wazuh alerts (Indexer `127.0.0.1:9200`, `wazuh-alerts-4.x-*`) |
| Authentication | client IP restriction and token |
| `POST`, `PUT`, `DELETE` | `HTTP 405` |

The Relay is the side that **reads** Wazuh alerts, and cannot be used to POST FSS verification results into Wazuh.

## Chapter 2: The Breakage in `local_rules.xml`

### 2.1 Local Rules and Decoders

> **Run on: VM 220**

```bash
echo "===== VM220: WAZUH CUSTOM RULE AND DECODER INVENTORY ====="

echo
echo "--- 1. Existing custom rule IDs and groups ---"
python3 - <<'PY'
import xml.etree.ElementTree as ET
from pathlib import Path

p = Path("/var/ossec/etc/rules/local_rules.xml")
if not p.is_file():
    print("LOCAL_RULES_NOT_FOUND")
else:
    try:
        root = ET.parse(p).getroot()
        for rule in root.iter("rule"):
            rid = rule.get("id", "")
            level = rule.get("level", "")
            description = rule.findtext("description", default="")
            groups = [
                (g.text or "").strip()
                for g in rule.findall("group")
            ]
            print(
                f"RULE_ID={rid} LEVEL={level} "
                f"GROUPS={','.join(groups)} "
                f"DESCRIPTION={description[:120]}"
            )
    except Exception as e:
        print(f"RULE_XML_PARSE_ERROR={type(e).__name__}")

print("\n--- 2. Existing decoder names ---")
p = Path("/var/ossec/etc/decoders/")

for f in sorted(p.glob("*.xml")):
    try:
        root = ET.parse(f).getroot()
        for decoder in root.iter("decoder"):
            name = decoder.get("name", "")
            if name:
                print(f"DECODER={name} FILE={f.name}")
    except Exception as e:
        print(f"DECODER_PARSE_ERROR FILE={f.name} TYPE={type(e).__name__}")

print("\n--- 3. Custom integration executable names ---")
p = Path("/var/ossec/integrations")
if p.is_dir():
    for f in sorted(p.iterdir()):
        if f.is_file():
            print(f"INTEGRATION_FILE={f.name}")
PY

echo
echo "--- 4. Wazuh manager service health ---"
systemctl show wazuh-manager.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts

echo
echo "READ_ONLY_INVENTORY=YES"
echo "WAZUH_FILES_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
```

`local_rules.xml` could not be read by Python's XML parser. `local_decoder.xml` is normal, and the decoder is `local_decoder_example`. Wazuh Manager is running (0 restarts).

### 2.2 Where It Is Broken

> **Run on: VM 220**

```bash
echo "===== VM220: WAZUH RULE XML VALIDATION DIAGNOSTIC ====="

python3 - <<'PY'
import xml.etree.ElementTree as ET
from pathlib import Path

base = Path("/var/ossec/etc/rules")
files = [
    base / "local_rules.xml",
    *sorted(base.glob("local_rules.xml.backup-*"))
]

for p in files:
    if not p.is_file():
        continue

    print(f"\nFILE={p.name}")
    try:
        ET.parse(p)
        print("XML_STATUS=VALID")
    except ET.ParseError as e:
        print("XML_STATUS=INVALID")
        print(f"ERROR_TYPE={type(e).__name__}")
        print(f"ERROR_POSITION_LINE={e.position[0]}")
        print(f"ERROR_POSITION_COLUMN={e.position[1]}")
        print(f"ERROR_MESSAGE={str(e).split(':')[0]}")
    except Exception as e:
        print(f"XML_STATUS=CHECK_ERROR TYPE={type(e).__name__}")
PY

echo
echo "--- 2. File metadata and hashes ---"
find /var/ossec/etc/rules -maxdepth 1 -type f \
  \( -name 'local_rules.xml' -o -name 'local_rules.xml.backup-*' \) \
  -exec stat -c '%A %a %U:%G %s %n' {} \; \
  -exec sha256sum {} \;

echo
echo "--- 3. Wazuh manager current health ---"
systemctl show wazuh-manager.service \
  -p ActiveState -p SubState -p MainPID -p NRestarts -p Result

echo
echo "READ_ONLY_DIAGNOSTIC=YES"
echo "RULE_FILES_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
```

- The current `local_rules.xml` fails XML parsing at line 21
- `backup-pre-reload` has the same SHA256 as the current file
- Several other copies also fail at the same line 21
- `backup-20261118-062100` is valid XML

### 2.3 Examining the Structure

> **Run on: VM 220**

```bash
echo "===== VM220: LOCAL RULES XML STRUCTURE AND LOAD STATUS ====="

echo
echo "--- 1. Current local_rules.xml with line numbers ---"
nl -ba /var/ossec/etc/rules/local_rules.xml | sed -n '1,45p'

echo
echo "--- 2. Known valid baseline backup ---"
nl -ba /var/ossec/etc/rules/local_rules.xml.backup-20261118-062100

echo
echo "--- 3. Wazuh log references to local rules and XML errors ---"
if [ -f /var/ossec/logs/ossec.log ]; then
    grep -iE 'local_rules|xml|rule.*error|error.*rule|duplicate rule' \
      /var/ossec/logs/ossec.log | tail -60
else
    echo "WAZUH_OSSEC_LOG_NOT_FOUND"
fi

echo
echo "--- 4. Manager service journal errors ---"
journalctl -u wazuh-manager.service -n 80 --no-pager \
  | grep -iE 'error|warning|rule|xml|decoder' \
  | tail -40 || true

echo
echo "--- 5. Manager runtime health ---"
systemctl show wazuh-manager.service \
  -p ActiveState -p SubState -p NRestarts -p Result

echo
echo "READ_ONLY_INSPECTION=YES"
echo "RULE_FILES_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
```

The current file had **two top-level elements**, as follows.

```xml
<group name="local,syslog,sshd,">
    ...
</group>

<group name="local,postgresql,">
    ...
</group>
```

An XML document needs exactly one root element. After the first root element closes at line 19, another root element begins at line 21, which causes the parse error.

> **Run on: VM 220**

```bash
echo "===== VM220: COMPLETE LOCAL RULES STRUCTURE INVENTORY ====="

echo
echo "--- 1. Remaining rules file ---"
nl -ba /var/ossec/etc/rules/local_rules.xml | sed -n '40,140p'

echo
echo "--- 2. Rule IDs and group declarations ---"
grep -nE '<group|</group>|<rule |</rule>|<if_sid>|<if_matched_sid>|<description>' \
  /var/ossec/etc/rules/local_rules.xml

echo
echo "--- 3. Duplicate rule IDs ---"
grep -oE '<rule[^>]*id="[0-9]+"' \
  /var/ossec/etc/rules/local_rules.xml \
  | sed -E 's/.*id="([0-9]+)"/\1/' \
  | sort | uniq -cd

echo
echo "--- 4. Known valid backup rule IDs ---"
grep -oE '<rule[^>]*id="[0-9]+"' \
  /var/ossec/etc/rules/local_rules.xml.backup-20261118-062100 \
  | sed -E 's/.*id="([0-9]+)"/\1/'

echo
echo "--- 5. File integrity metadata ---"
stat -c '%A %a %U:%G %s %n' \
  /var/ossec/etc/rules/local_rules.xml \
  /var/ossec/etc/rules/local_rules.xml.backup-20261118-062100

echo
echo "READ_ONLY_STRUCTURE_AUDIT=YES"
echo "RULE_FILES_MODIFIED=NO"
echo "SERVICES_RESTARTED=NO"
```

| Rule | Purpose | Level |
|---|---|---:|
| 100001 | SSH authentication failure | 5 |
| 100100 | base for PostgreSQL JSON events | 0 |
| 100101 | PostgreSQL authentication failure | 8 |
| 100106 | 5 authentication failures from the same IP | 12 |
| 100102 | PostgreSQL FATAL | 10 |
| 100103 | PostgreSQL ERROR | 7 |
| 100104 | PostgreSQL WARNING | 4 |
| 100105 | PostgreSQL PANIC | 12 |

There are no overlapping rule IDs.

## Chapter 3: Creating a Fixed Candidate

### 3.1 The Fix

According to the Wazuh documentation, the groups in a rules file are wrapped in one `<group>`, and per-rule classification is given by `<group>` inside each rule. To preserve the current classifications (SSH and PostgreSQL), we use the following form.

```xml
<group name="local,">
  <rule id="100001" level="5">
    ...
    <group>syslog,sshd,authentication_failed,pci_dss_10.2.4,pci_dss_10.2.5,</group>
  </rule>

  <rule id="100100" level="0">
    ...
    <group>postgresql,</group>
  </rule>

  <!-- The remaining 6 PostgreSQL rules also go here -->
</group>
```

Rule 100106 also had the following element.

```xml
<same_source_ip />
```

`<same_source_ip />` is an old name, but in current Wazuh it still works as an alias of `<same_srcip />`. It does not need to change, but we make it the newer `<same_srcip />` without changing the detection conditions.

> **Note:** In the build records, the first repair script found an unexpected group structure and stopped with `ABORT: unexpected group structure`. We confirmed that the SHA256, modification time and size of the production file had not changed.

### 3.2 Creating the Candidate File

Without changing the production file, we create a candidate in `/tmp` and check the XML syntax, the eight rule IDs, the group classification and `same_srcip`.

> **Run on: VM 220**

```bash
set -euo pipefail

SOURCE=/var/ossec/etc/rules/local_rules.xml
CANDIDATE=/tmp/local_rules.xml.candidate-20261124

echo "===== VM220: BUILD AND VALIDATE REPAIRED RULES CANDIDATE ====="

test -f "$SOURCE"
test ! -e "$CANDIDATE"

python3 - "$SOURCE" "$CANDIDATE" <<'PY'
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
s = src.read_text()

def replace_once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"ABORT: {label}: expected 1 occurrence, found {count}")
    s = s.replace(old, new, 1)

replace_once(
    '<group name="local,syslog,sshd,">',
    '<group name="local,">',
    'root group'
)

replace_once(
    '</group>\n\n<group name="local,postgresql,">',
    '',
    'merge top-level groups'
)

replace_once(
    '<group>authentication_failed,pci_dss_10.2.4,pci_dss_10.2.5,</group>',
    '<group>syslog,sshd,authentication_failed,pci_dss_10.2.4,pci_dss_10.2.5,</group>',
    'SSH group preservation'
)

replace_once(
    '<description>PostgreSQL sanitized JSON event base rule</description>',
    '<description>PostgreSQL sanitized JSON event base rule</description>\n    <group>postgresql,</group>',
    'PostgreSQL base group preservation'
)

replace_once(
    '<same_source_ip />',
    '<same_srcip />',
    'same source IP syntax'
)

dst.write_text(s)
print("CANDIDATE_CREATED=" + str(dst))
PY

echo
echo "--- 1. XML parse ---"
python3 - "$CANDIDATE" <<'PY'
import sys
import xml.etree.ElementTree as ET

root = ET.parse(sys.argv[1]).getroot()
print("XML_PARSE=VALID")
print("ROOT_TAG=" + root.tag)
print("ROOT_GROUP_NAME=" + root.attrib.get("name", ""))
rules = root.findall("rule")
print("RULE_COUNT=" + str(len(rules)))
print("RULE_IDS=" + ",".join(r.attrib["id"] for r in rules))
PY

echo
echo "--- 2. Group and correlation syntax ---"
grep -nE '<group|</group>|same_srcip|same_source_ip' "$CANDIDATE"

echo
echo "--- 3. Candidate integrity ---"
sha256sum "$SOURCE" "$CANDIDATE"
stat -c '%s bytes %a %n' "$SOURCE" "$CANDIDATE"

echo
echo "CANDIDATE_VALIDATION_COMPLETE=YES"
echo "PRODUCTION_RULES_MODIFIED=NO"
echo "WAZUH_MANAGER_RESTARTED=NO"
```

| Checked | Result |
|---|---|
| XML syntax | valid |
| Number of rules | 8 (all IDs the same) |
| Root element | one `<group>` |
| SSH and PostgreSQL classification | moved inside each rule |
| Rule 100106 | `<same_srcip />` |
| Production file | SHA256 as original |
| Wazuh Manager | not restarted |

Being valid XML and being accepted as rules by Wazuh are separate matters. In the next part, Part 68, we check with Wazuh without placing it in production.

## Closing Notes

In Part 67 we examined the Wazuh side on VM 220 and found the breakage in the local rules file.

| Item | Result |
|---|---|
| Wazuh Manager | configured to accept agents (1514, 1515) |
| Relay | only reads alerts (POST gives `405`); cannot be used as an entry point for FSS results |
| `local_rules.xml` | had two top-level `<group>` elements; broken as XML |
| Candidate | `/tmp/local_rules.xml.candidate-20261124` (one root, 8 rules, classifications preserved, `<same_srcip />`) |
| Production | not changed yet |

# Part 68: Testing the Fixed Rules in an Isolated Environment
## Introduction

### About This Book

This is Part 68 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 67 we created a fixed candidate of `local_rules.xml` in `/tmp`. Before placing it in production, we check with Wazuh's own test (`wazuh-analysisd -t`) whether the candidate is accepted as rules.

`wazuh-analysisd -t` normally reads the production configuration directory. `wazuh-logtest` also loads the production rules. So we use `wazuh-analysisd`'s `-D` (`chroot` into the specified directory) to test in **an isolated environment created in `/tmp`**.

- Place only the standard rules, decoders and lists, and the candidate `local_rules.xml`
- The production `ossec.conf` contains credentials (TLS certificates and secret keys, CA, passwords and so on), so it is not copied as a whole; a minimal configuration without secrets is created instead
- The production Wazuh Manager is neither started nor restarted

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)

> **Caution:** Wazuh's test commands work only as root (as the ordinary user `ag` they give `Permission denied` or exit code 126). When logged in as `ag`, become root with the following before running them.

```bash
sudo -i
```

## Chapter 1: What the Isolated Environment Needs

### 1.1 Where Rules Are Loaded From

> **Run on: VM 220**

```bash
set -u

echo "===== VM220: ISOLATED RULE VALIDATION PREFLIGHT ====="

echo
echo "--- 1. Wazuh directory layout ---"
for p in \
  /var/ossec \
  /var/ossec/etc \
  /var/ossec/etc/rules \
  /var/ossec/etc/decoders \
  /var/ossec/ruleset \
  /var/ossec/ruleset/rules \
  /var/ossec/ruleset/decoders \
  /var/ossec/bin
do
  if [ -e "$p" ]; then
    stat -c '%F %U:%G %a %n' "$p"
  else
    echo "MISSING: $p"
  fi
done

echo
echo "--- 2. Main configuration ruleset references ---"
grep -nE '<ruleset>|<rule_dir>|<decoder_dir>|<rule_exclude>|<decoder_exclude>' \
  /var/ossec/etc/ossec.conf || true

echo
echo "--- 3. Ruleset size and file counts ---"
du -sh /var/ossec/etc /var/ossec/ruleset 2>/dev/null
find /var/ossec/ruleset/rules -maxdepth 1 -type f | wc -l
find /var/ossec/ruleset/decoders -maxdepth 1 -type f | wc -l

echo
echo "--- 4. Candidate and production file hashes ---"
sha256sum \
  /var/ossec/etc/rules/local_rules.xml \
  /tmp/local_rules.xml.candidate-20261124

echo
echo "READ_ONLY_PREFLIGHT=YES"
echo "PRODUCTION_RULES_MODIFIED=NO"
echo "WAZUH_MANAGER_RESTARTED=NO"
```

```bash
set -u

echo "===== VM220: ANALYSISD ISOLATION REQUIREMENTS ====="

echo
echo "--- 1. Ruleset configuration block ---"
sed -n '255,290p' /var/ossec/etc/ossec.conf

echo
echo "--- 2. Analysisd executable dependencies ---"
ldd /var/ossec/bin/wazuh-analysisd

echo
echo "--- 3. Analysisd version ---"
/var/ossec/bin/wazuh-analysisd -V 2>&1

echo
echo "--- 4. Wazuh directory sizes ---"
du -sh /var/ossec/bin /var/ossec/etc /var/ossec/ruleset \
  /var/ossec/framework /var/ossec/queue 2>/dev/null || true

echo
echo "--- 5. Required configuration files ---"
find /var/ossec/etc -maxdepth 2 -type f \
  \( -name 'ossec.conf' -o -name 'local_rules.xml' \
     -o -name 'local_decoder.xml' \) \
  -printf '%p (%s bytes)\n'

echo
echo "READ_ONLY_ISOLATION_AUDIT=YES"
echo "PRODUCTION_RULES_MODIFIED=NO"
echo "WAZUH_MANAGER_RESTARTED=NO"
```

Wazuh rules are loaded from two places: the standard rules (`/var/ossec/ruleset/rules`) and the local rules (`/var/ossec/etc/rules`). We test in an environment that includes the standard rules and decoders, not just the candidate file.

### 1.2 Checking the Configuration for Secrets

Without showing values, we count only the names of elements that look like secrets.

> **Run on: VM 220**

```bash
echo "===== VM220: ISOLATED CONFIG SECRET-SAFETY PREFLIGHT ====="

python3 - <<'PY'
import xml.etree.ElementTree as ET

path = "/var/ossec/etc/ossec.conf"
root = ET.parse(path).getroot()

sensitive = ("password", "passwd", "secret", "token", "private", "credential", "api_key")
found = []

for elem in root.iter():
    tag = elem.tag.lower()
    if any(word in tag for word in sensitive):
        found.append((elem.tag, bool((elem.text or "").strip())))

print("SENSITIVE_ELEMENT_COUNT=" + str(len(found)))
for tag, has_value in found:
    print(f"ELEMENT={tag} VALUE_PRESENT={'YES' if has_value else 'NO'}")
PY

echo
echo "--- External credential file references (paths only) ---"
grep -nEi '<(password|key|token|certificate|ca|ssl|pem|credential)[^>]*>' \
  /var/ossec/etc/ossec.conf \
  | sed -E 's#>([^<]+)<#>[REDACTED]<#g' || true

echo
echo "READ_ONLY_SECRET_PREFLIGHT=YES"
echo "NO_FILES_CREATED=YES"
echo "NO_SERVICES_RESTARTED=YES"
```

There were elements for TLS certificates and secret keys, CA certificates, authentication and passwords, so the production `ossec.conf` is not copied.

### 1.3 Items Needed for a Minimal Configuration

> **Run on: VM 220**

```bash
set -euo pipefail

echo "===== VM220: MINIMAL ISOLATED ANALYSISD CONFIG DISCOVERY ====="

echo
echo "--- 1. ossec.conf top-level elements (names only) ---"
python3 - <<'PY'
import xml.etree.ElementTree as ET
root = ET.parse("/var/ossec/etc/ossec.conf").getroot()
for child in root:
    print(child.tag)
PY

echo
echo "--- 2. Relevant analysisd and ruleset element names ---"
python3 - <<'PY'
import xml.etree.ElementTree as ET
root = ET.parse("/var/ossec/etc/ossec.conf").getroot()
for section in ("global", "alerts", "logging", "ruleset", "rule_test"):
    for node in root.findall(section):
        print(f"[{section}]")
        for child in node:
            print("  " + child.tag)
PY

echo
echo "--- 3. Existing analysisd-specific configuration names ---"
grep -nE '^[[:space:]]*<analysisd>|^[[:space:]]*</analysisd>|^[[:space:]]*<[a-zA-Z_][a-zA-Z0-9_-]*>' \
  /var/ossec/etc/ossec.conf | tail -100

echo
echo "--- 4. Isolated candidate remains unchanged ---"
sha256sum /var/ossec/etc/rules/local_rules.xml \
  /tmp/local_rules.xml.candidate-20261124

echo
echo "READ_ONLY_CONFIG_DISCOVERY=YES"
echo "NO_ISOLATION_FILES_CREATED=YES"
echo "PRODUCTION_RULES_MODIFIED=NO"
echo "WAZUH_MANAGER_RESTARTED=NO"
```

## Chapter 2: Building the Isolated Environment

### 2.1 Placing the Basic Files

We place `wazuh-analysisd` and its shared libraries, the standard rules and decoders, the required lists, a minimal `ossec.conf` without secrets, and the candidate `local_rules.xml` in `/tmp/wazuh-rule-validation-20261124`.

> **Run on: VM 220**

```bash
set -euo pipefail

SRC=/var/ossec
ROOT=/tmp/wazuh-rule-validation-20261124
CANDIDATE=/tmp/local_rules.xml.candidate-20261124

echo "===== VM220: BUILD ISOLATED WAZUH RULE VALIDATION ROOT ====="

test "$(id -u)" -eq 0
test -f "$CANDIDATE"
test ! -e "$ROOT"

mkdir -p "$ROOT"/{var/ossec/{bin,lib,etc/{rules,decoders,lists},ruleset/{rules,decoders}},lib/x86_64-linux-gnu,lib64}

echo
echo "--- 1. Copy analysisd and Wazuh runtime library ---"
cp -a "$SRC/bin/wazuh-analysisd" "$ROOT/var/ossec/bin/"
cp -a "$SRC/lib/libwazuhext.so" "$ROOT/var/ossec/lib/"

echo
echo "--- 2. Copy standard rules and decoders ---"
cp -a "$SRC/ruleset/rules/." "$ROOT/var/ossec/ruleset/rules/"
cp -a "$SRC/ruleset/decoders/." "$ROOT/var/ossec/ruleset/decoders/"
cp -a "$SRC/etc/decoders/." "$ROOT/var/ossec/etc/decoders/"

echo
echo "--- 3. Copy rule lists and local candidate ---"
cp -a "$SRC/etc/lists/." "$ROOT/var/ossec/etc/lists/"
install -o root -g root -m 0644 "$CANDIDATE" \
  "$ROOT/var/ossec/etc/rules/local_rules.xml"

echo
echo "--- 4. Create minimal non-secret analysisd configuration ---"
python3 - "$SRC/etc/ossec.conf" "$ROOT/var/ossec/etc/ossec.conf" <<'PY'
import sys
import xml.etree.ElementTree as ET

source, destination = sys.argv[1:3]
original = ET.parse(source).getroot()
new = ET.Element("ossec_config")

for tag in ("global", "alerts", "logging", "ruleset", "rule_test"):
    for node in original.findall(tag):
        new.append(node)

ET.indent(new, space="  ")
ET.ElementTree(new).write(
    destination, encoding="utf-8", xml_declaration=True
)
print("MINIMAL_CONFIG_CREATED=YES")
print("INCLUDED_SECTIONS=global,alerts,logging,ruleset,rule_test")
PY

echo
echo "--- 5. Copy required shared libraries ---"
ldd "$SRC/bin/wazuh-analysisd" |
awk '
  /=> \// {print $3}
  /^[[:space:]]*\// {print $1}
' | sort -u |
while read -r lib; do
  case "$lib" in
    /var/ossec/lib/*)
      ;;
    *)
      if [ -f "$lib" ]; then
        install -D -m 0755 "$lib" "$ROOT$lib"
      fi
      ;;
  esac
done

echo
echo "--- 6. Validate isolated configuration and candidate XML ---"
python3 - "$ROOT" <<'PY'
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(sys.argv[1])
config = ET.parse(root / "var/ossec/etc/ossec.conf").getroot()
rules = ET.parse(root / "var/ossec/etc/rules/local_rules.xml").getroot()

print("ISOLATED_CONFIG_XML=VALID")
print("CANDIDATE_XML=VALID")
print("CANDIDATE_ROOT=" + rules.tag)
print("CANDIDATE_RULE_COUNT=" + str(len(rules.findall("rule"))))
print("CANDIDATE_RULE_IDS=" + ",".join(
    r.attrib["id"] for r in rules.findall("rule")
))
print("ISOLATED_STANDARD_RULE_COUNT=" + str(
    len(list((root / "var/ossec/ruleset/rules").glob("*.xml")))
))
print("ISOLATED_STANDARD_DECODER_COUNT=" + str(
    len(list((root / "var/ossec/ruleset/decoders").glob("*.xml")))
))
PY

echo
echo "--- 7. Run analysisd test inside isolated root ---"
/var/ossec/bin/wazuh-analysisd -t -D "$ROOT"
TEST_STATUS=$?
echo "ISOLATED_ANALYSISD_TEST_EXIT=$TEST_STATUS"

echo
echo "--- 8. Production integrity ---"
sha256sum \
  "$SRC/etc/rules/local_rules.xml" \
  "$CANDIDATE" \
  "$ROOT/var/ossec/etc/rules/local_rules.xml"

echo
echo "ISOLATED_VALIDATION_COMPLETE=YES"
echo "PRODUCTION_RULES_MODIFIED=NO"
echo "WAZUH_MANAGER_RESTARTED=NO"
```

### 2.2 Fixing the Directory Hierarchy

In 2.1 we placed things under `var/ossec/…`, but `-D` treats the specified directory as the root and looks for `etc/ossec.conf` and so on. We also copy the required directories to the top level.

> **Run on: VM 220**

```bash
set -euo pipefail

ROOT=/tmp/wazuh-rule-validation-20261124
W=/var/ossec

echo "===== VM220: CORRECT ISOLATED CHROOT DIRECTORY LAYOUT ====="

test -f "$ROOT/var/ossec/etc/ossec.conf"
test -f "$ROOT/var/ossec/etc/rules/local_rules.xml"
test -d "$ROOT/var/ossec/ruleset/rules"
test ! -e "$ROOT/etc"

echo
echo "--- 1. Create expected top-level directories ---"
mkdir -p "$ROOT"/{etc,bin,ruleset,logs}

echo
echo "--- 2. Copy isolated configuration and local rules ---"
cp -a "$ROOT/var/ossec/etc/." "$ROOT/etc/"

echo
echo "--- 3. Copy standard ruleset ---"
cp -a "$ROOT/var/ossec/ruleset/." "$ROOT/ruleset/"

echo
echo "--- 4. Verify expected paths ---"
for p in \
  "$ROOT/etc/ossec.conf" \
  "$ROOT/etc/rules/local_rules.xml" \
  "$ROOT/etc/decoders/local_decoder.xml" \
  "$ROOT/ruleset/rules" \
  "$ROOT/ruleset/decoders"
do
  test -e "$p"
  stat -c '%F %U:%G %a %n' "$p"
done

echo
echo "--- 5. Verify candidate rule IDs ---"
python3 - "$ROOT/etc/rules/local_rules.xml" <<'PY'
import sys
import xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
print("ROOT_TAG=" + root.tag)
print("RULE_COUNT=" + str(len(root.findall("rule"))))
print("RULE_IDS=" + ",".join(x.attrib["id"] for x in root.findall("rule")))
PY

echo
echo "CHROOT_LAYOUT_CORRECTED=YES"
echo "PRODUCTION_RULES_MODIFIED=NO"
echo "WAZUH_MANAGER_RESTARTED=NO"
```

The eight rule IDs of the candidate were preserved, and the production `local_rules.xml` and Wazuh Manager were unchanged.

### 2.3 Files Needed to Run

> **Run on: VM 220**

```bash
set -euo pipefail

ROOT=/tmp/wazuh-rule-validation-20261124
W=/var/ossec

echo "===== VM220: ISOLATED ANALYSISD RUNTIME DEPENDENCY PREFLIGHT ====="

test "$(id -u)" -eq 0

echo
echo "--- 1. Dynamic libraries required by analysisd ---"
ldd "$W/bin/wazuh-analysisd"

echo
echo "--- 2. Wazuh runtime library locations ---"
find "$W/lib" -maxdepth 2 -type f \
  \( -name '*.so' -o -name '*.so.*' \) \
  -printf '%p\n' | sort

echo
echo "--- 3. Internal configuration files ---"
for f in \
  etc/internal_options.conf \
  etc/local_internal_options.conf
do
  if [ -f "$W/$f" ]; then
    stat -c '%F %U:%G %a %s bytes %n' "$W/$f"
  else
    echo "MISSING: $W/$f"
  fi
done

echo
echo "--- 4. Isolated runtime directory presence ---"
for d in \
  "$ROOT/etc" \
  "$ROOT/bin" \
  "$ROOT/lib" \
  "$ROOT/ruleset" \
  "$ROOT/logs" \
  "$ROOT/queue" \
  "$ROOT/var"
do
  if [ -d "$d" ]; then
    stat -c '%F %U:%G %a %n' "$d"
  else
    echo "MISSING: $d"
  fi
done

echo
echo "--- 5. Key isolated files ---"
for f in \
  "$ROOT/etc/ossec.conf" \
  "$ROOT/etc/rules/local_rules.xml" \
  "$ROOT/etc/decoders/local_decoder.xml" \
  "$ROOT/var/ossec/lib/libwazuhext.so" \
  "$ROOT/lib64/ld-linux-x86-64.so.2"
do
  if [ -e "$f" ]; then
    stat -c '%F %U:%G %a %s bytes %n' "$f"
  else
    echo "MISSING: $f"
  fi
done

echo
echo "RUNTIME_PREFLIGHT_COMPLETE=YES"
echo "PRODUCTION_RULES_MODIFIED=NO"
echo "WAZUH_MANAGER_RESTARTED=NO"
```

```bash
set -euo pipefail

ROOT=/tmp/wazuh-rule-validation-20261124
W=/var/ossec

echo "===== VM220: COMPLETE ISOLATED ANALYSISD RUNTIME FILES ====="

echo
echo "--- 1. Install Wazuh runtime library at chroot path ---"
install -D -o root -g root -m 0755 \
  "$W/lib/libwazuhext.so" \
  "$ROOT/lib/libwazuhext.so"

echo
echo "--- 2. Copy internal options files ---"
install -D -o root -g root -m 0640 \
  "$W/etc/internal_options.conf" \
  "$ROOT/etc/internal_options.conf"

install -D -o root -g root -m 0640 \
  "$W/etc/local_internal_options.conf" \
  "$ROOT/etc/local_internal_options.conf"

echo
echo "--- 3. Verify standard shared libraries in chroot ---"
ldd "$W/bin/wazuh-analysisd" |
awk '
  /=> \// {print $3}
  /^[[:space:]]*\// {print $1}
' |
sort -u |
while IFS= read -r lib; do
  case "$lib" in
    /var/ossec/lib/*) continue ;;
  esac
  test -f "$lib"
  install -D -o root -g root -m 0755 "$lib" "$ROOT$lib"
  echo "INSTALLED: $lib"
done

echo
echo "--- 4. Verify isolated runtime files ---"
for f in \
  "$ROOT/lib/libwazuhext.so" \
  "$ROOT/etc/internal_options.conf" \
  "$ROOT/etc/local_internal_options.conf" \
  "$ROOT/lib/x86_64-linux-gnu/librt.so.1" \
  "$ROOT/lib/x86_64-linux-gnu/libc.so.6" \
  "$ROOT/lib64/ld-linux-x86-64.so.2"
do
  if [ -f "$f" ]; then
    stat -c '%U:%G %a %s bytes %n' "$f"
  else
    echo "MISSING: $f"
  fi
done

echo
echo "ISOLATED_RUNTIME_FILES_READY=YES"
echo "PRODUCTION_RULES_MODIFIED=NO"
echo "WAZUH_MANAGER_RESTARTED=NO"
```

We placed the OS shared libraries used by `wazuh-analysisd`, Wazuh's `libwazuhext.so` and two internal configuration files in their standard locations in the isolated environment.

### 2.4 Creating `etc/shared`

> **Run on: VM 220**

```bash
set -uo pipefail

ROOT=/tmp/wazuh-rule-validation-20261124
ANALYSISD=/var/ossec/bin/wazuh-analysisd

echo "===== VM220: RETEST WITH ISOLATED SHARED CONFIG DIRECTORY ====="

echo
echo "--- 1. Create isolated shared directory ---"
mkdir -p "$ROOT/etc/shared"
chmod 0750 "$ROOT/etc/shared"
stat -c '%F %U:%G %a %n' "$ROOT/etc/shared"

echo
echo "--- 2. Run isolated analysisd test ---"
"$ANALYSISD" -t -D "$ROOT"
TEST_STATUS=$?

echo
echo "--- 3. Isolated log result ---"
if [ -f "$ROOT/logs/ossec.log" ]; then
  tail -40 "$ROOT/logs/ossec.log"
fi

echo
echo "--- 4. Generated shared config metadata ---"
if [ -f "$ROOT/etc/shared/ar.conf" ]; then
  stat -c '%F %U:%G %a %s bytes %n' "$ROOT/etc/shared/ar.conf"
else
  echo "AR_CONF_NOT_CREATED"
fi

echo
echo "ISOLATED_ANALYSISD_TEST_EXIT=$TEST_STATUS"
if [ "$TEST_STATUS" -eq 0 ]; then
  echo "ISOLATED_ANALYSISD_TEST=PASS"
else
  echo "ISOLATED_ANALYSISD_TEST=FAIL"
fi
echo "PRODUCTION_RULES_MODIFIED=NO"
echo "WAZUH_MANAGER_RESTARTED=NO"

exit 0
```

## Chapter 3: Testing in the Isolated Environment

### 3.1 Removing the XML Declaration

We found that the isolated configuration began with an XML declaration (`<?xml …?>`), which the production configuration does not have. We remove the declaration from the isolated configuration only and test.

> **Run on: VM 220**

```bash
set -uo pipefail

ROOT=/tmp/wazuh-rule-validation-20261124
CONFIG="$ROOT/etc/ossec.conf"
BACKUP="$ROOT/etc/ossec.conf.pre-header-test"

echo "===== VM220: ISOLATED XML HEADER COMPATIBILITY TEST ====="

test "$(id -u)" -eq 0 || exit 10
test -f "$CONFIG" || exit 11
test ! -e "$BACKUP" || exit 12

echo
echo "--- 1. Preserve current isolated config ---"
cp -a "$CONFIG" "$BACKUP"

echo
echo "--- 2. Remove XML declaration from isolated config only ---"
python3 - "$CONFIG" <<'PY'
import sys
from pathlib import Path

p = Path(sys.argv[1])
data = p.read_bytes()
prefix = b"<?xml version='1.0' encoding='utf-8'?>\n"

if not data.startswith(prefix):
    raise SystemExit("UNEXPECTED_HEADER; NO_CHANGE")

p.write_bytes(data[len(prefix):])
print("XML_DECLARATION_REMOVED=YES")
PY

echo
echo "--- 3. Confirm XML remains valid ---"
python3 - "$CONFIG" <<'PY'
import sys
import xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
print("XML_PARSE=PASS")
print("ROOT_TAG=" + root.tag)
PY

echo
echo "--- 4. Run isolated analysisd test ---"
: > "$ROOT/logs/ossec.log"
 /var/ossec/bin/wazuh-analysisd -t -D "$ROOT"
STATUS=$?

echo
echo "--- 5. Isolated result ---"
tail -30 "$ROOT/logs/ossec.log"
echo "ANALYSISD_TEST_EXIT=$STATUS"

if [ "$STATUS" -eq 0 ]; then
  echo "ISOLATED_ANALYSISD_TEST=PASS"
else
  echo "ISOLATED_ANALYSISD_TEST=FAIL"
fi

echo "ORIGINAL_ISOLATED_CONFIG_BACKUP=$BACKUP"
echo "PRODUCTION_CONFIG_MODIFIED=NO"
echo "PRODUCTION_RULES_MODIFIED=NO"
echo "WAZUH_MANAGER_RESTARTED=NO"

exit 0
```

With the declaration removed, the earlier configuration load error (1226) no longer appeared; the next error was `Permission denied` on `internal_options.conf`.

### 3.2 Permissions of the Internal Configuration Files

> **Run on: VM 220**

```bash
set -uo pipefail

ROOT=/tmp/wazuh-rule-validation-20261124

echo "===== VM220: ISOLATED WAZUH VALIDATION AS ROOT ====="

echo
echo "--- 1. Execution identity ---"
id

echo
echo "--- 2. Isolated options file permissions ---"
stat -c '%A %U:%G %a %n' \
  "$ROOT/etc/internal_options.conf" \
  "$ROOT/etc/local_internal_options.conf" \
  "$ROOT/etc/ossec.conf"

echo
echo "--- 3. Confirm XML declaration remains absent ---"
if head -c 20 "$ROOT/etc/ossec.conf" | grep -q '<?xml'; then
  echo "XML_DECLARATION_PRESENT=YES"
else
  echo "XML_DECLARATION_PRESENT=NO"
fi

echo
echo "--- 4. Run isolated analysisd test as root ---"
/var/ossec/bin/wazuh-analysisd -t -D "$ROOT"
STATUS=$?

echo
echo "ANALYSISD_TEST_EXIT=$STATUS"
if [ "$STATUS" -eq 0 ]; then
  echo "ISOLATED_ANALYSISD_TEST=PASS"
else
  echo "ISOLATED_ANALYSISD_TEST=FAIL"
fi

echo
echo "--- 5. Isolated log tail ---"
tail -30 "$ROOT/logs/ossec.log" 2>/dev/null || true

echo
echo "PRODUCTION_CONFIG_MODIFIED=NO"
echo "PRODUCTION_RULES_MODIFIED=NO"
echo "WAZUH_MANAGER_RESTARTED=NO"
```

```bash
set -euo pipefail

ROOT=/tmp/wazuh-rule-validation-20261124

echo "===== VM220: ISOLATED OPTIONS ACCESS TEST ====="

echo
echo "--- 1. Root access ---"
if test -r "$ROOT/etc/internal_options.conf"; then
  echo "ROOT_READ=PASS"
else
  echo "ROOT_READ=FAIL"
fi

echo
echo "--- 2. Wazuh user access ---"
if runuser -u wazuh -- test -r "$ROOT/etc/internal_options.conf"; then
  echo "WAZUH_USER_READ=PASS"
else
  echo "WAZUH_USER_READ=FAIL"
fi

echo
echo "--- 3. Wazuh user directory traversal ---"
for p in "$ROOT" "$ROOT/etc"; do
  if runuser -u wazuh -- test -x "$p"; then
    echo "TRAVERSE_PASS=$p"
  else
    echo "TRAVERSE_FAIL=$p"
  fi
done

echo
echo "--- 4. Confirm file hash and metadata unchanged ---"
sha256sum "$ROOT/etc/internal_options.conf"
stat -c '%A %U:%G %a %n' "$ROOT/etc/internal_options.conf"

echo
echo "PRODUCTION_FILES_MODIFIED=NO"
echo "WAZUH_MANAGER_RESTARTED=NO"
```

`internal_options.conf` in the isolated environment was `root:root`, `640`, and the cause was that the `wazuh` user, which Wazuh uses internally, could not read it.

### 3.3 Fixing the Permissions

We set only the two files in the isolated environment to `root:wazuh`, `640`.

> **Run on: VM 220**

```bash
set -euo pipefail

ROOT=/tmp/wazuh-rule-validation-20261124

echo "===== VM220: ISOLATED OPTIONS PERMISSION CORRECTION ====="

echo
echo "--- 1. Confirm target files ---"
test -f "$ROOT/etc/internal_options.conf"
test -f "$ROOT/etc/local_internal_options.conf"

echo
echo "--- 2. Change isolated group ownership only ---"
chgrp wazuh \
  "$ROOT/etc/internal_options.conf" \
  "$ROOT/etc/local_internal_options.conf"

chmod 640 \
  "$ROOT/etc/internal_options.conf" \
  "$ROOT/etc/local_internal_options.conf"

echo
echo "--- 3. Verify metadata ---"
stat -c '%A %U:%G %a %n' \
  "$ROOT/etc/internal_options.conf" \
  "$ROOT/etc/local_internal_options.conf"

echo
echo "--- 4. Verify Wazuh user read access ---"
runuser -u wazuh -- test -r "$ROOT/etc/internal_options.conf"
runuser -u wazuh -- test -r "$ROOT/etc/local_internal_options.conf"
echo "WAZUH_USER_READ=PASS"

echo
echo "PRODUCTION_FILES_MODIFIED=NO"
echo "WAZUH_MANAGER_RESTARTED=NO"
```

They are now readable by the `wazuh` user.

### 3.4 Testing Again

> **Run on: VM 220**

```bash
set -uo pipefail

ROOT=/tmp/wazuh-rule-validation-20261124

echo "===== VM220: ISOLATED ANALYSISD CONFIGURATION RETEST ====="

echo
echo "--- 1. Confirm execution identity ---"
id

echo
echo "--- 2. Confirm isolated options access ---"
runuser -u wazuh -- test -r "$ROOT/etc/internal_options.conf"
runuser -u wazuh -- test -r "$ROOT/etc/local_internal_options.conf"
echo "OPTIONS_ACCESS=PASS"

echo
echo "--- 3. Run isolated analysisd test ---"
/var/ossec/bin/wazuh-analysisd -t -D "$ROOT"
STATUS=$?

echo
echo "--- 4. Isolated result ---"
echo "ANALYSISD_TEST_EXIT=$STATUS"
if [ "$STATUS" -eq 0 ]; then
  echo "ISOLATED_ANALYSISD_TEST=PASS"
else
  echo "ISOLATED_ANALYSISD_TEST=FAIL"
fi

echo
echo "--- 5. Latest isolated log entries ---"
tail -35 "$ROOT/logs/ossec.log" 2>/dev/null || true

echo
echo "PRODUCTION_CONFIG_MODIFIED=NO"
echo "PRODUCTION_RULES_MODIFIED=NO"
echo "WAZUH_MANAGER_RESTARTED=NO"

exit 0
```

**`wazuh-analysisd -t -D "$ROOT"` finished with exit code `0`.** Wazuh accepted the configuration including the candidate rules.

## Chapter 4: Final Check of the Candidate

> **Run on: VM 220**

```bash
set -euo pipefail

ROOT=/tmp/wazuh-rule-validation-20261124
CANDIDATE="$ROOT/etc/rules/local_rules.xml"
PRODUCTION=/var/ossec/etc/rules/local_rules.xml

echo "===== VM220: WAZUH RULE CANDIDATE FINAL INTEGRITY AUDIT ====="

echo
echo "--- 1. Candidate file hash ---"
sha256sum "$CANDIDATE"
EXPECTED_CANDIDATE=57fd6e21310ae595ef7e48e34f22f22f2087cde099b32aa87df249c932af3b8b
ACTUAL_CANDIDATE=$(sha256sum "$CANDIDATE" | awk '{print $1}')
test "$ACTUAL_CANDIDATE" = "$EXPECTED_CANDIDATE"
echo "CANDIDATE_HASH=PASS"

echo
echo "--- 2. Candidate XML structure and rule IDs ---"
python3 - "$CANDIDATE" <<'PY'
import sys
import xml.etree.ElementTree as ET

root = ET.parse(sys.argv[1]).getroot()
rules = root.findall(".//rule")
ids = [r.get("id") for r in rules]
expected = ["100001", "100100", "100101", "100106",
            "100102", "100103", "100104", "100105"]

print("ROOT_TAG=" + root.tag)
print("ROOT_GROUP_COUNT=" + str(len(root.findall("./group"))))
print("RULE_COUNT=" + str(len(rules)))
print("RULE_IDS=" + ",".join(ids))
print("DUPLICATE_IDS=" + str(sorted({x for x in ids if ids.count(x) > 1})))

if root.tag != "group" or len(root.findall("./group")) != 0:
    raise SystemExit("ROOT_STRUCTURE=FAIL")
if ids != expected:
    raise SystemExit("RULE_ID_SET_OR_ORDER=FAIL")
if len(set(ids)) != len(ids):
    raise SystemExit("DUPLICATE_RULE_IDS=FAIL")

print("CANDIDATE_STRUCTURE=PASS")
PY

echo
echo "--- 3. Production file hash ---"
sha256sum "$PRODUCTION"
EXPECTED_PRODUCTION=8c78cf3147f9f81f7610d8ad1da8e1bef7a174ffd885e036abf70c76df65f8c8
ACTUAL_PRODUCTION=$(sha256sum "$PRODUCTION" | awk '{print $1}')
test "$ACTUAL_PRODUCTION" = "$EXPECTED_PRODUCTION"
echo "PRODUCTION_FILE_UNCHANGED=PASS"

echo
echo "ISOLATED_ANALYSISD_TEST=PASS"
echo "PRODUCTION_RULES_REPLACED=NO"
echo "WAZUH_MANAGER_RESTARTED=NO"
```

| Checked | Result |
|---|---|
| Candidate SHA256 | passed |
| XML root structure | passed |
| Number of rules, IDs | all 8 match, no overlaps |
| Isolated test | passed |
| Production file, Wazuh Manager | unchanged |

## Closing Notes

In Part 68 we checked the fixed `local_rules.xml` candidate with Wazuh's own test without placing it in production.

| Item | Result |
|---|---|
| Isolated environment | `/tmp/wazuh-rule-validation-20261124` (standard rules, decoders and lists, a minimal configuration without secrets, the candidate rules) |
| Cautions for the isolated configuration | no XML declaration; `internal_options.conf` and the like `root:wazuh`, `640` |
| `wazuh-analysisd -t -D` | exit code `0` |
| Production | not changed yet |

In the next part, Part 69, we place the candidate in production, check how the rules actually behave, and have Wazuh Manager load them.

# Part 69: Putting the Fixed Rules into Production
## Introduction

### About This Book

This is Part 69 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 68 we checked the fixed `local_rules.xml` candidate in an isolated environment. Here we put it into production.

1. Save a copy of the current `local_rules.xml` and replace it with the candidate in one step
2. Run `wazuh-analysisd -t` with the production configuration
3. With `wazuh-logtest`, test whether the PostgreSQL rules fire as expected
4. Investigate what a Wazuh Manager reload does, perform it once, and have it load the rules

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)

## Chapter 1: Replacing the Production File

### 1.1 Replacing

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

### 1.2 Testing with the Production Configuration

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

### 1.3 Running Processes

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

## Chapter 2: Testing Rule Behavior

With `wazuh-logtest`, we feed test events one at a time. Actual PostgreSQL logs and other systems are not affected (the documentation IP address `192.0.2.10` is used).

### 2.1 Authentication Failure (100101)

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

### 2.2 Brute Force (100106)

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

### 2.3 PANIC (100105)

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

### 2.4 FATAL (100102)

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

### 2.5 ERROR (100103)

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

### 2.6 WARNING (100104)

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

## Chapter 3: Having Wazuh Manager Load the Rules

### 3.1 What a Reload Does

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

### 3.2 Recording the State Before the Reload

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

### 3.3 Performing One Reload

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

### 3.4 Agent and Rule State

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

### 3.5 Rule Loading Records

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

## Closing Notes

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

# Part 70: Starting to Build the AI Defense Agents
## Introduction

### About This Book

This is Part 70 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". By Part 69 we had put in order the Wazuh defense foundation and the protection of the AI Defense Manager's (VM 230) input, output, authentication and logs. From here, we build **AI defense agents** on top of it.

In this part we build the first two agents.

| Agent | Role |
|---|---|
| `LogAnalysisAgent` | log analysis. A thin, read-only layer that delegates to the existing AI analysis (`analyze_events()`) |
| `ThreatAnalysisAgent` | threat analysis and evidence validation. Independently checks the log analysis result for duplicate, missing or inconsistent evidence event IDs relative to the input |

The principles decided are as follows.

1. Agents only read and analyze; they do not execute defensive actions
2. Even if they can propose `TEMPORARY_BLOCK_IP`, they do not actually block. Defensive actions follow the existing `ActionProposal` constraints (approval required, start in `PENDING`)
3. Existing APIs, DB, settings and services are not changed. Tests use simulated analysis and make no communication with Ollama or DB access
4. Existing files are not overwritten

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root. When logged in as `aidefense`, become root with `sudo -i`)

## Chapter 1: Examining the Existing Structure

### 1.1 Service and Application

> **Run on: VM 230**

```bash
set -uo pipefail

echo "===== VM230: AI DEFENSE AGENT BUILD PREFLIGHT ====="

echo
echo "--- 1. Host and account ---"
hostname
id

echo
echo "--- 2. Existing service state ---"
systemctl status ai-defense-manager.service --no-pager -l | head -35

echo
echo "--- 3. Service configuration metadata ---"
systemctl show ai-defense-manager.service \
  -p ActiveState \
  -p SubState \
  -p MainPID \
  -p NRestarts \
  -p User \
  -p WorkingDirectory \
  -p FragmentPath

echo
echo "--- 4. Running application process ---"
PID="$(systemctl show ai-defense-manager.service -p MainPID --value)"
if [ "${PID:-0}" -gt 0 ] 2>/dev/null; then
  ps -p "$PID" -o pid=,user=,stat=,etime=,comm=
  printf 'PROCESS_CWD='
  readlink "/proc/$PID/cwd" || true
else
  echo "MAINPID_NOT_AVAILABLE"
fi

echo
echo "--- 5. Existing application directory candidates ---"
for d in /opt/ai-defense-manager /opt/ai-defense /home/aidefense/ai-defense-manager; do
  if [ -d "$d" ]; then
    ls -ld "$d"
    find "$d" -maxdepth 2 -type d \
      \( -name agents -o -name api -o -name core -o -name policies -o -name schemas -o -name services \) \
      -print 2>/dev/null
  fi
done

echo
echo "READ_ONLY_PREFLIGHT=YES"
echo "SERVICE_RESTARTED=NO"
echo "FILES_MODIFIED=NO"
```

The API runs on `127.0.0.1:8000` (Main PID `2340`, NRestarts 0), and the working directory is `/opt/ai-defense-manager`.

> **Run on: VM 230**

```bash
sudo -i

ROOT=/opt/ai-defense-manager

echo "===== VM230: ROOT-LEVEL APPLICATION SOURCE INVENTORY ====="

echo
echo "--- 1. Application directories ---"
find "$ROOT/app" "$ROOT/tests" -maxdepth 4 -type d -print | sort

echo
echo "--- 2. Python source files ---"
find "$ROOT/app" "$ROOT/tests" -maxdepth 5 -type f \
  \( -name '*.py' -o -name 'pyproject.toml' \) \
  -printf '%p\n' | sort

echo
echo "--- 3. Application source file metadata ---"
find "$ROOT/app" -maxdepth 4 -type f -name '*.py' \
  -printf '%M %u:%g %s bytes %p\n' | sort

echo
echo "--- 4. Test file metadata ---"
find "$ROOT/tests" -maxdepth 4 -type f \
  -printf '%M %u:%g %s bytes %p\n' | sort

echo
echo "--- 5. Dependency lock metadata ---"
stat -c '%A %U:%G %s bytes %n' "$ROOT/requirements.lock"

echo
echo "SOURCE_CONTENT_READ=NO"
echo "CONFIG_AND_DATABASE_READ=NO"
echo "FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

`/opt/ai-defense-manager/app` and `tests` are owned by root and cannot be read by `aidefense` (a structure that protects the application code). We keep this protection.

### 1.2 Source Listing and AI Analysis Structure

> **Run on: VM 230**

```bash
echo "===== VM230: PYTHON SOURCE FILE LIST ====="

find /opt/ai-defense-manager/app \
     /opt/ai-defense-manager/tests \
     -type f -name '*.py' -print | sort

echo
echo "FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

```bash
set -uo pipefail

ROOT=/opt/ai-defense-manager

echo "===== VM230: AI ANALYSIS ARCHITECTURE DISCOVERY ====="

echo
echo "--- 1. Existing package directories ---"
find "$ROOT/app" -maxdepth 3 -type d -print | sort

echo
echo "--- 2. API route and function declarations ---"
grep -nE '^[[:space:]]*@|^[[:space:]]*(async )?def |^[[:space:]]*class ' \
  "$ROOT/app/api/analysis.py" \
  "$ROOT/app/api/wazuh.py" \
  "$ROOT/app/main.py" || true

echo
echo "--- 3. Service function and class declarations ---"
grep -nE '^[[:space:]]*(async )?def |^[[:space:]]*class ' \
  "$ROOT/app/services/ai_analysis.py" \
  "$ROOT/app/services/event_sanitizer.py" \
  "$ROOT/app/services/wazuh_relay.py" \
  "$ROOT/app/services/analysis_history.py" || true

echo
echo "--- 4. Schema declarations ---"
grep -nE '^[[:space:]]*class ' \
  "$ROOT/app/schemas/"*.py || true

echo
echo "--- 5. Test file inventory ---"
find "$ROOT/tests" -maxdepth 5 -type f -printf '%P\n' | sort

echo
echo "SOURCE_CONTENT_DUMP=NO"
echo "SECRETS_READ=NO"
echo "FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
```

| Existing | Role |
|---|---|
| `app/services/ai_analysis.py` | AI analysis engine |
| `app/services/wazuh_relay.py` | fetching Wazuh events |
| `app/services/event_sanitizer.py` | masking events |
| `app/services/analysis_history.py` | storing analysis history |
| `app/agents`, `app/policies` | directories only, no Python files |

### 1.3 Input/Output Types and Validation

> **Run on: VM 230**

```bash
python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app")

targets = [
    "api/analysis.py",
    "api/wazuh.py",
    "services/ai_analysis.py",
    "services/wazuh_relay.py",
    "services/event_sanitizer.py",
    "services/analysis_history.py",
    "schemas/analysis.py",
    "schemas/security_event.py",
    "schemas/analysis_proposal.py",
]

print("===== VM230: EXISTING AI INTERFACE CONTRACTS =====")

for relative in targets:
    path = root / relative
    print(f"\n--- {relative} ---")

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"AST_READ_ERROR={type(exc).__name__}")
        continue

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [arg.arg for arg in node.args.args]
            print(f"FUNCTION {node.name}({', '.join(args)})")

        elif isinstance(node, ast.ClassDef):
            print(f"CLASS {node.name}")
            for child in node.body:
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    print(f"  FIELD {child.target.id}")
                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    print(f"  METHOD {child.name}")

print("\n--- Agent and policy files ---")
for directory in ("agents", "policies"):
    path = root / directory
    print(f"[{directory}]")
    if path.exists():
        for item in sorted(path.rglob("*")):
            if item.is_file() and "__pycache__" not in item.parts:
                print(item.relative_to(root))

print("\nREAD_ONLY_AST_INSPECTION=YES")
print("FILES_MODIFIED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

```bash
python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app/schemas")
targets = [
    "analysis.py",
    "security_event.py",
    "analysis_proposal.py",
    "action.py",
    "wazuh.py",
]

print("===== VM230: SCHEMA TYPES AND VALIDATION CONTRACTS =====")

for filename in targets:
    path = root / filename
    print(f"\n--- {filename} ---")

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"PARSE_ERROR={type(exc).__name__}")
        continue

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            print(f"\nCLASS {node.name}")

            for child in node.body:
                if isinstance(child, ast.AnnAssign):
                    name = child.target.id if isinstance(child.target, ast.Name) else "?"
                    annotation = ast.unparse(child.annotation)
                    default = "required" if child.value is None else "has_default"
                    print(f"  FIELD {name}: {annotation} [{default}]")

                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [arg.arg for arg in child.args.args]
                    print(f"  METHOD {child.name}({', '.join(args)})")

                elif isinstance(child, ast.Assign):
                    names = [
                        target.id for target in child.targets
                        if isinstance(target, ast.Name)
                    ]
                    if names:
                        print(f"  CLASS_CONSTANT {', '.join(names)}")

print("\nSCHEMA_CONTENT_SECRETS=NOT_REQUESTED")
print("DATABASE_CONTENT_READ=NO")
print("FILES_MODIFIED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

The first agents can use the existing `AIAnalysisRequest` and `AIAnalysisProposal` for input and output. `AIAnalysisProposal` has `confidence`, `evidence_event_ids`, `requires_human_approval` and others.

> **Run on: VM 230**

```bash
python3 - <<'PY'
import ast
from pathlib import Path

root = Path("/opt/ai-defense-manager/app/schemas")
targets = {
    "security_event.py": {"require_timezone", "validate_ip_address"},
    "analysis_proposal.py": {"validate_action_constraints"},
    "action.py": {"validate_action"},
}

print("===== VM230: SECURITY VALIDATOR IMPLEMENTATION =====")

for filename, wanted in targets.items():
    path = root / filename
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    tree = ast.parse(source)

    print(f"\n--- {filename} ---")
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in wanted:
            start = node.lineno
            end = node.end_lineno
            print(f"\n[{node.name}: lines {start}-{end}]")
            for number in range(start, end + 1):
                print(f"{number:4}: {lines[number - 1]}")

print("\nVALIDATOR_CODE_ONLY=YES")
print("DATABASE_CONTENT_READ=NO")
print("FILES_MODIFIED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

- An IP blocking proposal requires two or more separate evidence events
- Only global IPs can be blocking targets
- `target_ip` and `ttl_seconds` are required
- Human approval is required
- Execution proposals start in `PENDING`

### 1.4 The Flow of Model Queries

> **Run on: VM 230**

```bash
python3 - <<'PY'
import ast
from pathlib import Path

base = Path("/opt/ai-defense-manager/app")

targets = [
    "services/ai_analysis.py",
    "services/wazuh_relay.py",
    "services/event_sanitizer.py",
    "core/config.py",
    "api/analysis.py",
    "api/wazuh.py",
]

print("===== VM230: AI ENGINE DEPENDENCY MAP =====")

for relative in targets:
    path = base / relative
    tree = ast.parse(path.read_text(encoding="utf-8"))

    print(f"\n--- {relative} ---")

    for node in tree.body:
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
            print("IMPORT:", ", ".join(names))

        elif isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            print(f"FROM {node.module}: {', '.join(names)}")

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            calls = set()
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    func = child.func
                    if isinstance(func, ast.Name):
                        calls.add(func.id)
                    elif isinstance(func, ast.Attribute):
                        calls.add(func.attr)

            print(f"FUNCTION {node.name}")
            if calls:
                print("  CALLS:", ", ".join(sorted(calls)))

        elif isinstance(node, ast.ClassDef):
            print(f"CLASS {node.name}")
            for child in node.body:
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    print(f"  CONFIG_FIELD: {child.target.id}")
                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    print(f"  METHOD: {child.name}")

print("\nDEPENDENCY_NAMES_ONLY=YES")
print("CONFIG_VALUES_DISPLAYED=NO")
print("SECRETS_READ=NO")
print("DATABASE_CONTENT_READ=NO")
print("FILES_MODIFIED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

```bash
python3 - <<'PY'
import ast
from pathlib import Path

base = Path("/opt/ai-defense-manager/app")
targets = [
    ("services/ai_analysis.py", "_analyze_events_unlimited"),
    ("services/ai_analysis.py", "analyze_events"),
    ("api/analysis.py", "create_analysis"),
    ("api/wazuh.py", "analyze_wazuh_events"),
]

def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return dotted(node.value) + "." + node.attr
    return type(node).__name__

print("===== VM230: MODEL REQUEST AND RESPONSE FLOW =====")

for relative, function_name in targets:
    path = base / relative
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fn = next(
        (n for n in ast.walk(tree)
         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
         and n.name == function_name),
        None
    )

    print(f"\n--- {relative}:{function_name} ---")
    if fn is None:
        print("FUNCTION_NOT_FOUND")
        continue

    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            keywords = [kw.arg for kw in node.keywords if kw.arg]
            print(f"CALL {dotted(node.func)}"
                  + (f" | keyword_args={','.join(keywords)}" if keywords else ""))

        elif isinstance(node, ast.Dict):
            keys = []
            for key in node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    keys.append(key.value)
                else:
                    keys.append("<dynamic>")
            if keys:
                print("DICT_KEYS:", ", ".join(keys))

        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "settings":
                print("SETTING_REFERENCE:", node.attr)

        elif isinstance(node, ast.Compare):
            print("COMPARISON_OPERATOR:", ", ".join(type(op).__name__ for op in node.ops))

print("\nPROMPT_TEXT_DISPLAYED=NO")
print("URL_OR_SETTING_VALUES_DISPLAYED=NO")
print("SECRETS_READ=NO")
print("DATABASE_CONTENT_READ=NO")
print("FILES_MODIFIED=NO")
print("SERVICE_RESTARTED=NO")
PY
```

Querying Ollama (`httpx.AsyncClient`), parsing the JSON answer and validating with `AIAnalysisProposal` are already done by `ai_analysis.py`. The first agent does not duplicate model calls; it uses the existing `analyze_events()`.

### 1.5 Test Environment

> **Run on: VM 230**

```bash
echo "===== VM230: AGENT IMPLEMENTATION TEST ENVIRONMENT ====="

ROOT=/opt/ai-defense-manager

echo
echo "--- 1. Python runtime ---"
"$ROOT/venv/bin/python" --version

echo
echo "--- 2. Test framework availability ---"
"$ROOT/venv/bin/python" - <<'PY'
from importlib.util import find_spec

for name in ("pytest", "pytest_asyncio", "httpx", "pydantic", "fastapi"):
    print(f"{name}: {'AVAILABLE' if find_spec(name) else 'NOT_INSTALLED'}")
PY

echo
echo "--- 3. Locked dependency names and versions ---"
sed -E 's/([A-Za-z0-9_.-]+)==([^ ;]+).*/\1==\2/; t; d' \
  "$ROOT/requirements.lock"

echo
echo "--- 4. Agent and policy directory metadata ---"
stat -c '%n | owner=%U:%G | mode=%a' \
  "$ROOT/app/agents" "$ROOT/app/policies" "$ROOT/tests"

echo
echo "FILES_MODIFIED=NO"
echo "DATABASE_CONTENT_READ=NO"
echo "SERVICE_RESTARTED=NO"
```

Python 3.12.3, Pydantic 2.14.4, FastAPI 0.165.0; there is no `pytest`, so we use the standard `unittest`.

## Chapter 2: The Log Analysis Agent

### 2.1 Building and Testing

We create only two new files, `app/agents/log_analysis.py` and `tests/test_log_analysis_agent.py`, after checking that they do not exist yet.

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
cd "$ROOT"

AGENT="$ROOT/app/agents/log_analysis.py"
TEST="$ROOT/tests/test_log_analysis_agent.py"

echo "===== VM230: CREATE AND TEST LOG ANALYSIS AGENT ====="

# Do not overwrite an existing file by mistake
if [ -e "$AGENT" ] || [ -e "$TEST" ]; then
    echo "ABORT: One or both target files already exist."
    exit 1
fi

umask 027

cat > "$AGENT" <<'PY'
"""Read-only log analysis agent.

This agent delegates analysis to the existing AI analysis service.
It does not execute or authorize defensive actions.
"""

from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal
from app.services.ai_analysis import analyze_events


class LogAnalysisAgent:
    """Analyze security events without performing operational actions."""

    async def analyze(
        self,
        request: AIAnalysisRequest,
    ) -> AIAnalysisProposal:
        """Return an analysis proposal from the existing analysis service."""
        return await analyze_events(request)
PY

cat > "$TEST" <<'PY'
import unittest
from unittest.mock import AsyncMock, patch

from app.agents.log_analysis import LogAnalysisAgent
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import (
    AIAnalysisProposal,
    RecommendedAction,
)
from app.services.ai_analysis import AIAnalysisError


class TestLogAnalysisAgent(unittest.IsolatedAsyncioTestCase):

    async def test_delegates_request_and_returns_proposal(self):
        request = AIAnalysisRequest()
        proposal = AIAnalysisProposal(
            recommended_action=RecommendedAction.NO_ACTION,
        )

        with patch(
            "app.agents.log_analysis.analyze_events",
            new_callable=AsyncMock,
            return_value=proposal,
        ) as mocked:
            result = await LogAnalysisAgent().analyze(request)

        mocked.assert_awaited_once_with(request)
        self.assertIs(result, proposal)

    async def test_propagates_analysis_error(self):
        request = AIAnalysisRequest()
        expected_error = AIAnalysisError("synthetic test failure")

        with patch(
            "app.agents.log_analysis.analyze_events",
            new_callable=AsyncMock,
            side_effect=expected_error,
        ):
            with self.assertRaises(AIAnalysisError) as raised:
                await LogAnalysisAgent().analyze(request)

        self.assertIs(raised.exception, expected_error)


if __name__ == "__main__":
    unittest.main()
PY

chown root:ai-defense "$AGENT"
chmod 0640 "$AGENT"
chown root:root "$TEST"
chmod 0640 "$TEST"

echo
echo "--- 1. Syntax validation ---"
"$ROOT/venv/bin/python" -m py_compile "$AGENT" "$TEST"
echo "PY_COMPILE=PASS"

echo
echo "--- 2. Isolated unit tests ---"
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
    discover -s "$ROOT/tests" \
    -p 'test_log_analysis_agent.py' \
    -v

echo
echo "--- 3. Created file metadata ---"
stat -c '%n | owner=%U:%G | mode=%a | size=%s' "$AGENT" "$TEST"

echo
echo "ONLY_APPROVED_FILES_CREATED=YES"
echo "EXISTING_FILES_MODIFIED=NO"
echo "DATABASE_CONTENT_READ=NO"
echo "OLLAMA_REQUEST_SENT=NO"
echo "SERVICE_RESTARTED=NO"
```

### 2.2 Fixing the Test Data

The test in 2.1 failed before the agent's processing because of mistakes in how the test data was built. Without changing the agent itself, we fix only the test file, in three steps.

1. Put one valid `SecurityEvent` into the required `events` of `AIAnalysisRequest`

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
TEST="$ROOT/tests/test_log_analysis_agent.py"

cat > "$TEST" <<'PY'
import unittest
from unittest.mock import AsyncMock, patch

from app.agents.log_analysis import LogAnalysisAgent
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import (
    AIAnalysisProposal,
    RecommendedAction,
)
from app.schemas.security_event import SecurityEvent
from app.services.ai_analysis import AIAnalysisError


def make_request():
    event = SecurityEvent(
        source="wazuh",
        severity="low",
        event_category="authentication",
        event_summary="Synthetic unit-test event",
    )
    return AIAnalysisRequest(events=[event])


class TestLogAnalysisAgent(unittest.IsolatedAsyncioTestCase):

    async def test_delegates_request_and_returns_proposal(self):
        request = make_request()
        proposal = AIAnalysisProposal(
            recommended_action=RecommendedAction.NO_ACTION,
        )

        with patch(
            "app.agents.log_analysis.analyze_events",
            new_callable=AsyncMock,
            return_value=proposal,
        ) as mocked:
            result = await LogAnalysisAgent().analyze(request)

        mocked.assert_awaited_once_with(request)
        self.assertIs(result, proposal)

    async def test_propagates_analysis_error(self):
        request = make_request()
        expected_error = AIAnalysisError("synthetic test failure")

        with patch(
            "app.agents.log_analysis.analyze_events",
            new_callable=AsyncMock,
            side_effect=expected_error,
        ):
            with self.assertRaises(AIAnalysisError) as raised:
                await LogAnalysisAgent().analyze(request)

        self.assertIs(raised.exception, expected_error)


if __name__ == "__main__":
    unittest.main()
PY

chown root:root "$TEST"
chmod 0640 "$TEST"

echo "===== VM230: LOG ANALYSIS AGENT TEST RETRY ====="

"$ROOT/venv/bin/python" -m py_compile \
    "$ROOT/app/agents/log_analysis.py" "$TEST"

PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
    discover -s "$ROOT/tests" \
    -p 'test_log_analysis_agent.py' \
    -v

echo
echo "AGENT_SOURCE_MODIFIED=NO"
echo "TEST_FILE_UPDATED=YES"
echo "DATABASE_CONTENT_READ=NO"
echo "OLLAMA_REQUEST_SENT=NO"
echo "SERVICE_RESTARTED=NO"
```

2. Fill in the required fields of `AIAnalysisProposal` (`summary`, `severity`, `confidence`, `evidence_event_ids`, `reasoning`)

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
TEST="$ROOT/tests/test_log_analysis_agent.py"

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Run this block as root."
    exit 1
fi

python3 - <<'PY'
from pathlib import Path

path = Path("/opt/ai-defense-manager/tests/test_log_analysis_agent.py")
source = path.read_text(encoding="utf-8")

old = '''        proposal = AIAnalysisProposal(
            recommended_action=RecommendedAction.NO_ACTION,
        )'''

new = '''        proposal = AIAnalysisProposal(
            summary="Synthetic test summary",
            severity="low",
            confidence=0.5,
            evidence_event_ids=[],
            recommended_action=RecommendedAction.NO_ACTION,
            reasoning="Synthetic unit-test reasoning",
        )'''

if source.count(old) != 1:
    raise SystemExit("ABORT: Expected test fixture was not found exactly once.")

path.write_text(source.replace(old, new), encoding="utf-8")
PY

chown root:root "$TEST"
chmod 0640 "$TEST"

echo "===== VM230: LOG ANALYSIS AGENT TEST RETRY 2 ====="

"$ROOT/venv/bin/python" -m py_compile \
    "$ROOT/app/agents/log_analysis.py" "$TEST"

PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
    discover -s "$ROOT/tests" \
    -p 'test_log_analysis_agent.py' \
    -v

echo
echo "AGENT_SOURCE_MODIFIED=NO"
echo "TEST_FIXTURE_UPDATED=YES"
echo "DATABASE_CONTENT_READ=NO"
echo "OLLAMA_REQUEST_SENT=NO"
echo "SERVICE_RESTARTED=NO"
```

3. `evidence_event_ids` requires at least one item, so use the test event's `event_id` as the evidence ID

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
TEST="$ROOT/tests/test_log_analysis_agent.py"

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Run as root."
    exit 1
fi

python3 - <<'PY'
from pathlib import Path

path = Path("/opt/ai-defense-manager/tests/test_log_analysis_agent.py")
source = path.read_text(encoding="utf-8")

old = '''        proposal = AIAnalysisProposal(
            summary="Synthetic test summary",
            severity="low",
            confidence=0.5,
            evidence_event_ids=[],
            recommended_action=RecommendedAction.NO_ACTION,
            reasoning="Synthetic unit-test reasoning",
        )'''

new = '''        proposal = AIAnalysisProposal(
            summary="Synthetic test summary",
            severity="low",
            confidence=0.5,
            evidence_event_ids=[request.events[0].event_id],
            recommended_action=RecommendedAction.NO_ACTION,
            reasoning="Synthetic unit-test reasoning",
        )'''

if source.count(old) != 1:
    raise SystemExit("ABORT: Expected fixture not found exactly once.")

path.write_text(source.replace(old, new), encoding="utf-8")
PY

chown root:root "$TEST"
chmod 0640 "$TEST"

echo "===== VM230: LOG ANALYSIS AGENT TEST RETRY 3 ====="

"$ROOT/venv/bin/python" -m py_compile \
  "$ROOT/app/agents/log_analysis.py" "$TEST"

PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
  discover -s "$ROOT/tests" \
  -p 'test_log_analysis_agent.py' \
  -v

echo
echo "AGENT_SOURCE_MODIFIED=NO"
echo "TEST_FIXTURE_UPDATED=YES"
echo "DATABASE_CONTENT_READ=NO"
echo "OLLAMA_REQUEST_SENT=NO"
echo "SERVICE_RESTARTED=NO"
```

Both `test_delegates_request_and_returns_proposal` and `test_propagates_analysis_error` were `OK`. There were no actual requests to Ollama, no DB reads and no service restarts.

### 2.3 Checking the Contents

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager

echo "===== 1. AGENT SOURCE ====="
sed -n '1,240p' "$ROOT/app/agents/log_analysis.py"

echo
echo "===== 2. AGENT UNIT TEST ====="
sed -n '1,260p' "$ROOT/tests/test_log_analysis_agent.py"

echo
echo "===== 3. AGENT PACKAGE FILES ====="
find "$ROOT/app/agents" -maxdepth 2 -type f \
  ! -path '*/__pycache__/*' -printf '%M %u:%g %p\n' | sort

echo
echo "===== 4. PROJECT CHANGE STATUS ====="
if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git -C "$ROOT" status --short
else
    echo "NOT_A_GIT_WORKTREE"
fi

echo
echo "READ_ONLY=YES"
echo "SERVICE_RESTARTED=NO"
echo "DATABASE_CONTENT_READ=NO"
```

`LogAnalysisAgent` is a thin, read-only agent that delegates to the existing `analyze_events()`, with no functions for executing or approving defensive actions.

## Chapter 3: The Threat Analysis Agent

### 3.1 Design

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager

echo "===== 1. ANALYSIS PROPOSAL SCHEMA ====="
sed -n '1,280p' "$ROOT/app/schemas/analysis_proposal.py"

echo
echo "===== 2. SECURITY EVENT SCHEMA ====="
sed -n '1,280p' "$ROOT/app/schemas/security_event.py"

echo
echo "===== 3. ANALYSIS REQUEST SCHEMA ====="
sed -n '1,240p' "$ROOT/app/schemas/analysis.py"

echo
echo "===== 4. OTHER SCHEMA INVENTORY ====="
find "$ROOT/app/schemas" -maxdepth 2 -type f \
  ! -path '*/__pycache__/*' -printf '%f\n' | sort

echo
echo "===== 5. POLICY AND AGENT SOURCE INVENTORY ====="
find "$ROOT/app/policies" "$ROOT/app/agents" -maxdepth 2 -type f \
  ! -path '*/__pycache__/*' -printf '%M %u:%g %p\n' 2>/dev/null | sort

echo
echo "===== 6. EXISTING THREAT-RELATED REFERENCES ====="
grep -RInE 'threat|confidence|evidence_event_ids|severity|risk_score' \
  "$ROOT/app/agents" "$ROOT/app/services" "$ROOT/app/schemas" \
  --include='*.py' 2>/dev/null | head -160 || true

echo
echo "READ_ONLY=YES"
echo "FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "DATABASE_CONTENT_READ=NO"
```

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager

echo "===== 1. LOG ANALYSIS AGENT REFERENCES ====="
grep -RIn "LogAnalysisAgent" \
  "$ROOT/app" "$ROOT/tests" \
  --include='*.py' 2>/dev/null || true

echo
echo "===== 2. ANALYSIS API ====="
sed -n '1,260p' "$ROOT/app/api/analysis.py"

echo
echo "===== 3. WAZUH API ====="
sed -n '1,280p' "$ROOT/app/api/wazuh.py"

echo
echo "===== 4. API ROUTER REGISTRATION ====="
grep -RInE 'include_router|analysis_router|wazuh_router' \
  "$ROOT/app" --include='*.py' 2>/dev/null || true

echo
echo "===== 5. AGENT IMPORT CONVENTIONS ====="
find "$ROOT/app" -maxdepth 2 -type f -name '*.py' \
  ! -path '*/__pycache__/*' -printf '%p\n' | sort

echo
echo "READ_ONLY=YES"
echo "FILES_MODIFIED=NO"
echo "SERVICE_RESTARTED=NO"
echo "DATABASE_CONTENT_READ=NO"
```

The existing `AIAnalysisProposal` has severity, confidence, evidence event IDs and recommended actions, so we do not create a new schema. The two analysis APIs still call `analyze_events()` directly, and `LogAnalysisAgent` is not used by the APIs.

`ThreatAnalysisAgent` is given the role of independently checking the log analysis result, not merely rewrapping the AI's answer.

- Delegate analysis to `LogAnalysisAgent`
- For the returned proposal, check for duplicate evidence IDs, duplicate input event IDs, and evidence IDs not in the input
- Reject inconsistencies with a dedicated exception

### 3.2 Building and Testing

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
AGENT="$ROOT/app/agents/threat_analysis.py"
TEST="$ROOT/tests/test_threat_analysis_agent.py"

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Run as root."
    exit 1
fi

if [ -e "$AGENT" ] || [ -e "$TEST" ]; then
    echo "ABORT: One or more target files already exist. No files overwritten."
    exit 1
fi

python3 - <<'PY'
from pathlib import Path

agent = Path("/opt/ai-defense-manager/app/agents/threat_analysis.py")
test = Path("/opt/ai-defense-manager/tests/test_threat_analysis_agent.py")

agent_source = '''"""Threat analysis agent with independent evidence validation.

The agent delegates initial analysis to LogAnalysisAgent, then independently
checks that every cited evidence event belongs to the supplied request.
It does not execute or authorize defensive actions.
"""

from app.agents.log_analysis import LogAnalysisAgent
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal


class ThreatAnalysisError(ValueError):
    """Raised when an analysis proposal fails independent validation."""


class ThreatAnalysisAgent:
    """Validate threat analysis proposals against their source events."""

    def __init__(self, log_agent: LogAnalysisAgent | None = None) -> None:
        self._log_agent = log_agent or LogAnalysisAgent()

    async def analyze(self, request: AIAnalysisRequest) -> AIAnalysisProposal:
        """Analyze events and independently validate the resulting proposal."""
        proposal = await self._log_agent.analyze(request)
        return self.validate(request, proposal)

    @staticmethod
    def validate(
        request: AIAnalysisRequest,
        proposal: AIAnalysisProposal,
    ) -> AIAnalysisProposal:
        """Reject duplicate, missing, or unrelated evidence references."""
        if not request.events:
            raise ThreatAnalysisError("request contains no security events")

        input_ids = [event.event_id for event in request.events]
        if len(input_ids) != len(set(input_ids)):
            raise ThreatAnalysisError("request contains duplicate event IDs")

        evidence_ids = proposal.evidence_event_ids
        if not evidence_ids:
            raise ThreatAnalysisError("proposal contains no evidence event IDs")

        if len(evidence_ids) != len(set(evidence_ids)):
            raise ThreatAnalysisError("proposal contains duplicate evidence event IDs")

        input_id_set = set(input_ids)
        unknown_ids = set(evidence_ids) - input_id_set
        if unknown_ids:
            raise ThreatAnalysisError(
                "proposal references evidence outside the supplied request"
            )

        return proposal
'''

test_source = '''import unittest
from unittest.mock import AsyncMock

from uuid import uuid4

from app.agents.threat_analysis import (
    ThreatAnalysisAgent,
    ThreatAnalysisError,
)
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import (
    AIAnalysisProposal,
    RecommendedAction,
)
from app.schemas.security_event import SecurityEvent


def make_event():
    return SecurityEvent(
        source="wazuh",
        severity="medium",
        event_category="authentication",
        event_summary="Synthetic threat-analysis test event",
    )


def make_request(events=None):
    return AIAnalysisRequest(events=events or [make_event()])


def make_proposal(evidence_ids):
    return AIAnalysisProposal(
        summary="Synthetic threat-analysis proposal",
        severity="medium",
        confidence=0.7,
        evidence_event_ids=evidence_ids,
        recommended_action=RecommendedAction.HUMAN_REVIEW,
        reasoning="Synthetic unit-test reasoning",
    )


class TestThreatAnalysisAgent(unittest.IsolatedAsyncioTestCase):

    async def test_analyze_delegates_and_validates_proposal(self):
        request = make_request()
        proposal = make_proposal([request.events[0].event_id])
        log_agent = type("FakeLogAgent", (), {})()
        log_agent.analyze = AsyncMock(return_value=proposal)

        result = await ThreatAnalysisAgent(log_agent).analyze(request)

        log_agent.analyze.assert_awaited_once_with(request)
        self.assertIs(result, proposal)

    async def test_rejects_duplicate_input_event_ids(self):
        event = make_event()
        request = make_request([event, event])
        proposal = make_proposal([event.event_id])

        with self.assertRaisesRegex(ThreatAnalysisError, "duplicate event IDs"):
            ThreatAnalysisAgent.validate(request, proposal)

    async def test_rejects_duplicate_evidence_ids(self):
        request = make_request()
        event_id = request.events[0].event_id
        proposal = make_proposal([event_id, event_id])

        with self.assertRaisesRegex(
            ThreatAnalysisError, "duplicate evidence event IDs"
        ):
            ThreatAnalysisAgent.validate(request, proposal)

    async def test_rejects_evidence_not_in_request(self):
        request = make_request()
        proposal = make_proposal([uuid4()])

        with self.assertRaisesRegex(
            ThreatAnalysisError, "outside the supplied request"
        ):
            ThreatAnalysisAgent.validate(request, proposal)

    async def test_accepts_valid_evidence(self):
        request = make_request()
        proposal = make_proposal([request.events[0].event_id])

        result = ThreatAnalysisAgent.validate(request, proposal)

        self.assertIs(result, proposal)


if __name__ == "__main__":
    unittest.main()
'''

agent.write_text(agent_source, encoding="utf-8")
test.write_text(test_source, encoding="utf-8")
PY

chown root:ai-defense "$AGENT"
chmod 0640 "$AGENT"
chown root:root "$TEST"
chmod 0640 "$TEST"

echo "===== VM230: THREAT ANALYSIS AGENT TESTS ====="

"$ROOT/venv/bin/python" -m py_compile "$AGENT" "$TEST"

PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
  discover -s "$ROOT/tests" \
  -p 'test_threat_analysis_agent.py' \
  -v

echo
echo "===== FILE STATUS ====="
stat -c '%A %U:%G %n' "$AGENT" "$TEST"

echo
echo "NEW_AGENT_FILES_CREATED=2"
echo "EXISTING_FILES_OVERWRITTEN=NO"
echo "API_MODIFIED=NO"
echo "DATABASE_CONTENT_READ=NO"
echo "OLLAMA_REQUEST_SENT=NO"
echo "SERVICE_RESTARTED=NO"
```

| Test | Result |
|---|---|
| Accepts valid evidence IDs | passed |
| Delegates to the log analysis agent | passed |
| Rejects duplicate evidence IDs | passed |
| Rejects duplicate input event IDs | passed |
| Rejects evidence IDs not in the input | passed |

All 5 passed.

### 3.3 All Tests

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager

echo "===== VM230: COMPLETE AGENT UNIT TEST SUITE ====="

PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
  discover -s "$ROOT/tests" \
  -p 'test_*.py' \
  -v

echo
echo "===== AGENT FILE INVENTORY ====="
find "$ROOT/app/agents" -maxdepth 1 -type f \
  -printf '%M %u:%g %f\n' | sort

echo
echo "===== TEST FILE INVENTORY ====="
find "$ROOT/tests" -maxdepth 1 -type f \
  -name 'test_*.py' -printf '%M %u:%g %f\n' | sort

echo
echo "FULL_TEST_SUITE=PASSED"
echo "SERVICE_RESTARTED=NO"
echo "DATABASE_CONTENT_READ=NO"
echo "OLLAMA_REQUEST_SENT=NO"
```

All 7 tests of the two agents passed, and within this scope no effect on each other or on existing functions was seen.

## Closing Notes

In Part 70 we built the first two AI defense agents.

| Agent | File | Tests |
|---|---|---|
| `LogAnalysisAgent` | `app/agents/log_analysis.py` | 2 passed |
| `ThreatAnalysisAgent` | `app/agents/threat_analysis.py` | 5 passed |

Both only read and analyze and do not execute defensive actions. They are not yet connected to the API, and the service has not been restarted. In the next part, Part 71, we move on to an event correlation agent, an agent that orchestrates the whole, and a defense decision policy agent.

# Part 71: Correlation, Orchestration and Defense Decision Agents
## Introduction

### About This Book

This is Part 71 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual", and the last part of Volume 4. In Part 70 we built two agents, for log analysis and threat analysis. Here we build the following agents.

| Agent | Role |
|---|---|
| `IncidentCorrelationAgent` | relates multiple events by time, agent and classification; deterministic processing without an LLM |
| `SecurityAnalysisOrchestrator` | combines correlation and AI analysis (orchestrating the analysis) |
| `DefensePolicyAgent` | does not trust AI proposals as is; decides by server-side rules |

None of these agents performs defensive actions, IP blocking, notification or DB storage. Existing APIs, DB, settings and services are not changed either.

### Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (`192.168.0.221`, root. When logged in as `aidefense`, become root with `sudo -i`)

## Chapter 1: The Event Correlation Agent

### 1.1 Available Fields

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager

echo "===== 1. WAZUH EVENT CONVERSION ====="
sed -n '1,280p' "$ROOT/app/services/wazuh_relay.py"

echo
echo "===== 2. SECURITY EVENT MODEL ====="
sed -n '1,240p' "$ROOT/app/schemas/security_event.py"

echo
echo "===== 3. WAZUH ANALYSIS REQUEST ====="
sed -n '1,220p' "$ROOT/app/schemas/wazuh.py"

echo
echo "===== 4. EXISTING TIME AND IP CORRELATION LOGIC ====="
grep -RInE 'observed_at|source_ip|destination_ip|agent_id|event_category|timeframe|correlat' \
  "$ROOT/app" --include='*.py' 2>/dev/null | head -200 || true

echo
echo "===== 5. PYTHON RUNTIME ====="
"$ROOT/venv/bin/python" --version

echo
echo "READ_ONLY=YES"
echo "FILES_MODIFIED=NO"
echo "DATABASE_CONTENT_READ=NO"
echo "SERVICE_RESTARTED=NO"
```

`SecurityEvent` has time, source IP, destination IP, agent ID and classification, but the current Wazuh conversion uses only `timestamp`, rule information, groups and `agent.id`, and does not pass IP addresses (because we narrowed it to seven fields in Part 48). **With the current Wazuh events alone, correlation by IP address is not possible.** We correlate using only the available fields.

| Item | Initial specification |
|---|---|
| Correlation key | same `agent_id` and same `event_category` |
| Time window | within 10 minutes of the first event |
| Minimum number of events | 2 |
| Time | time-zone-aware `observed_at` (normalized to UTC) |
| Correlation by IP | not used for now |
| Output | incident candidates, the event IDs they contain, the time range |

Events without `agent_id` are excluded so as not to relate them by mistake. Ten minutes is the value of this initial design.

### 1.2 Building

We create `app/agents/incident_correlation.py` and `tests/test_incident_correlation_agent.py` as new files.

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
AGENT="$ROOT/app/agents/incident_correlation.py"
TEST="$ROOT/tests/test_incident_correlation_agent.py"

echo "===== VM230: INCIDENT CORRELATION AGENT CREATION ====="

# Prevent accidental overwrite.
if [ -e "$AGENT" ] || [ -e "$TEST" ]; then
    echo "ABORT: one or both target files already exist."
    exit 1
fi

cat > "$AGENT" <<'PY'
"""Deterministic, read-only security event correlation agent."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.schemas.analysis import AIAnalysisRequest


@dataclass(frozen=True, slots=True)
class IncidentCluster:
    """A candidate cluster of related security events."""

    agent_id: str
    event_category: str
    event_ids: tuple[UUID, ...]
    started_at: datetime
    ended_at: datetime


@dataclass(frozen=True, slots=True)
class IncidentCorrelationResult:
    """Correlation output; no defensive action is performed."""

    clusters: tuple[IncidentCluster, ...]
    uncorrelated_event_ids: tuple[UUID, ...]


class IncidentCorrelationError(ValueError):
    """Raised when the input cannot be correlated safely."""


class IncidentCorrelationAgent:
    """Group events by agent and category within a fixed time window."""

    def __init__(self, window: timedelta = timedelta(minutes=10)) -> None:
        if window <= timedelta(0):
            raise ValueError("correlation window must be positive")
        self._window = window

    def analyze(self, request: AIAnalysisRequest) -> IncidentCorrelationResult:
        events = request.events
        if not events:
            raise IncidentCorrelationError("request contains no security events")

        event_ids = [event.event_id for event in events]
        if len(event_ids) != len(set(event_ids)):
            raise IncidentCorrelationError("request contains duplicate event IDs")

        grouped: dict[tuple[str, str], list[tuple[datetime, UUID]]] = {}
        uncorrelated: list[UUID] = []

        for event in events:
            if event.agent_id is None or not str(event.agent_id).strip():
                uncorrelated.append(event.event_id)
                continue

            observed_at = event.observed_at
            if observed_at.tzinfo is None or observed_at.utcoffset() is None:
                raise IncidentCorrelationError(
                    "event timestamp must be timezone-aware"
                )

            key = (str(event.agent_id), str(event.event_category))
            grouped.setdefault(key, []).append(
                (observed_at.astimezone(timezone.utc), event.event_id)
            )

        clusters: list[IncidentCluster] = []

        for (agent_id, category), items in grouped.items():
            items.sort(key=lambda item: (item[0], str(item[1])))
            index = 0

            while index < len(items):
                start_time = items[index][0]
                end_limit = start_time + self._window
                bucket: list[tuple[datetime, UUID]] = []

                while index < len(items) and items[index][0] <= end_limit:
                    bucket.append(items[index])
                    index += 1

                if len(bucket) >= 2:
                    clusters.append(
                        IncidentCluster(
                            agent_id=agent_id,
                            event_category=category,
                            event_ids=tuple(item[1] for item in bucket),
                            started_at=bucket[0][0],
                            ended_at=bucket[-1][0],
                        )
                    )
                else:
                    uncorrelated.extend(item[1] for item in bucket)

        clusters.sort(
            key=lambda cluster: (
                cluster.started_at,
                cluster.agent_id,
                cluster.event_category,
                tuple(str(event_id) for event_id in cluster.event_ids),
            )
        )
        uncorrelated.sort(key=str)

        return IncidentCorrelationResult(
            clusters=tuple(clusters),
            uncorrelated_event_ids=tuple(uncorrelated),
        )
PY

cat > "$TEST" <<'PY'
"""Unit tests for deterministic incident correlation."""

import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.agents.incident_correlation import (
    IncidentCorrelationAgent,
    IncidentCorrelationError,
)
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.events import SecurityEvent


def make_event(
    *,
    minutes: int,
    agent_id: str | None = "agent-1",
    category: str = "authentication",
    observed_at: datetime | None = None,
) -> SecurityEvent:
    timestamp = observed_at or (
        datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
        + timedelta(minutes=minutes)
    )
    return SecurityEvent(
        event_id=uuid4(),
        source="wazuh",
        observed_at=timestamp,
        severity="low",
        agent_id=agent_id,
        event_category=category,
        event_summary="Synthetic correlation test event",
    )


def make_request(events: list[SecurityEvent]) -> AIAnalysisRequest:
    return AIAnalysisRequest(events=events)


class TestIncidentCorrelationAgent(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = IncidentCorrelationAgent()

    def test_correlates_same_agent_and_category_within_ten_minutes(self):
        first = make_event(minutes=0)
        second = make_event(minutes=10)

        result = self.agent.analyze(make_request([first, second]))

        self.assertEqual(len(result.clusters), 1)
        cluster = result.clusters[0]
        self.assertEqual(cluster.agent_id, "agent-1")
        self.assertEqual(cluster.event_category, "authentication")
        self.assertEqual(set(cluster.event_ids), {first.event_id, second.event_id})
        self.assertEqual(len(result.uncorrelated_event_ids), 0)

    def test_does_not_chain_events_beyond_ten_minute_anchor_window(self):
        first = make_event(minutes=0)
        second = make_event(minutes=9)
        third = make_event(minutes=18)

        result = self.agent.analyze(make_request([first, second, third]))

        self.assertEqual(len(result.clusters), 1)
        self.assertEqual(
            set(result.clusters[0].event_ids),
            {first.event_id, second.event_id},
        )
        self.assertEqual(result.uncorrelated_event_ids, (third.event_id,))

    def test_does_not_correlate_different_agents_or_categories(self):
        events = [
            make_event(minutes=0, agent_id="agent-1", category="authentication"),
            make_event(minutes=1, agent_id="agent-2", category="authentication"),
            make_event(minutes=2, agent_id="agent-1", category="database"),
        ]

        result = self.agent.analyze(make_request(events))

        self.assertEqual(len(result.clusters), 0)
        self.assertEqual(
            set(result.uncorrelated_event_ids),
            {event.event_id for event in events},
        )

    def test_events_without_agent_id_remain_uncorrelated(self):
        first = make_event(minutes=0, agent_id=None)
        second = make_event(minutes=1, agent_id=None)

        result = self.agent.analyze(make_request([first, second]))

        self.assertEqual(len(result.clusters), 0)
        self.assertEqual(
            set(result.uncorrelated_event_ids),
            {first.event_id, second.event_id},
        )

    def test_normalizes_timezone_before_comparison(self):
        first = make_event(
            minutes=0,
            observed_at=datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc),
        )
        second = make_event(
            minutes=1,
            observed_at=datetime(
                2026, 11, 24, 21, 1,
                tzinfo=timezone(timedelta(hours=9)),
            ),
        )

        result = self.agent.analyze(make_request([first, second]))

        self.assertEqual(len(result.clusters), 1)
        self.assertEqual(
            result.clusters[0].ended_at - result.clusters[0].started_at,
            timedelta(minutes=1),
        )

    def test_rejects_duplicate_event_ids(self):
        event = make_event(minutes=0)
        duplicate = event.model_copy()

        with self.assertRaisesRegex(
            IncidentCorrelationError, "duplicate event IDs"
        ):
            self.agent.analyze(make_request([event, duplicate]))

    def test_rejects_non_positive_window(self):
        with self.assertRaises(ValueError):
            IncidentCorrelationAgent(window=timedelta(0))


if __name__ == "__main__":
    unittest.main()
PY

chown root:ai-defense "$AGENT"
chmod 0640 "$AGENT"
chown root:root "$TEST"
chmod 0640 "$TEST"

echo
echo "--- 1. Created files ---"
stat -c '%n | %U:%G | %a | %s bytes' "$AGENT" "$TEST"

echo
echo "--- 2. Run incident correlation tests ---"
cd "$ROOT"
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
    discover -s "$ROOT/tests" \
    -p 'test_incident_correlation_agent.py' -v

echo
echo "--- 3. Run complete unit test suite ---"
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
    discover -s "$ROOT/tests" \
    -p 'test_*.py' -v

echo
echo "INCIDENT_CORRELATION_TEST_RUN_COMPLETE"
```

The module name imported by the test file differed from the actual one, and the import failed.

```text
ModuleNotFoundError: No module named 'app.schemas.events'
```

### 1.3 Fixing the Test Import

`SecurityEvent` is in `app.schemas.security_event`.

```python
from app.schemas.security_event import SecurityEvent
```

We fix only the one import line of the test file. The agent itself, the API, the DB and the service are not touched.

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
TEST="$ROOT/tests/test_incident_correlation_agent.py"

echo "===== VM230: FIX SECURITY EVENT TEST IMPORT ====="

echo
echo "--- 1. Verify current import ---"
grep -n 'app.schemas.*SecurityEvent' "$TEST"

echo
echo "--- 2. Apply the one-line import correction ---"
sed -i \
  's/from app\.schemas\.events import SecurityEvent/from app.schemas.security_event import SecurityEvent/' \
  "$TEST"

chown root:root "$TEST"
chmod 0640 "$TEST"

echo
echo "--- 3. Verify corrected import ---"
grep -n 'app.schemas.*SecurityEvent' "$TEST"

echo
echo "--- 4. Run incident correlation tests ---"
cd "$ROOT"
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
  discover -s "$ROOT/tests" \
  -p 'test_incident_correlation_agent.py' -v

echo
echo "--- 5. Run complete unit test suite ---"
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
  discover -s "$ROOT/tests" \
  -p 'test_*.py' -v

echo
echo "--- 6. Confirm file metadata ---"
stat -c '%n | %U:%G | %a | %s bytes' "$TEST"

echo
echo "INCIDENT_CORRELATION_IMPORT_FIX_COMPLETE"
```

| Agent | Tests |
|---|---:|
| `LogAnalysisAgent` | 2 passed |
| `ThreatAnalysisAgent` | 5 passed |
| `IncidentCorrelationAgent` | 7 passed |

All 14 passed. The specifications confirmed were: relating events of the same agent and classification within 10 minutes, normalizing time zones to UTC, not chaining beyond 10 minutes, excluding events without `agent_id`, rejecting duplicate event IDs, and not performing defensive actions.

## Chapter 2: The Analysis Orchestration Agent

### 2.1 Design

> **Run on: VM 230**

```bash
set -euo pipefail
ROOT=/opt/ai-defense-manager

echo "===== VM230: ORCHESTRATOR DESIGN DISCOVERY ====="

echo
echo "--- 1. Agent source files ---"
for f in \
  "$ROOT/app/agents/log_analysis.py" \
  "$ROOT/app/agents/threat_analysis.py" \
  "$ROOT/app/agents/incident_correlation.py"; do
  echo "### $f"
  sed -n '1,260p' "$f"
done

echo
echo "--- 2. Analysis schemas ---"
for f in \
  "$ROOT/app/schemas/analysis.py" \
  "$ROOT/app/schemas/analysis_proposal.py" \
  "$ROOT/app/schemas/security_event.py"; do
  echo "### $f"
  sed -n '1,280p' "$f"
done

echo
echo "--- 3. Existing orchestration / agent references ---"
grep -R -n -E \
  'Orchestrator|orchestrat|ThreatAnalysisAgent|IncidentCorrelationAgent|LogAnalysisAgent' \
  "$ROOT/app" --include='*.py' || true

echo
echo "--- 4. Existing tests inventory ---"
find "$ROOT/tests" -maxdepth 1 -type f -name 'test_*.py' -printf '%f\n' | sort

echo
echo "--- 5. API call paths (source only) ---"
sed -n '1,260p' "$ROOT/app/api/analysis.py"
sed -n '1,300p' "$ROOT/app/api/wazuh.py"

echo
echo "ORCHESTRATOR_DESIGN_DISCOVERY_COMPLETE"
```

`ThreatAnalysisAgent` calls `LogAnalysisAgent` internally. If the orchestration agent called both separately, the AI analysis would run twice. So we do the following.

1. Run the correlation analysis first
2. Call `ThreatAnalysisAgent` only once (`LogAnalysisAgent` runs inside it)
3. Return both results together
4. If either fails, propagate the exception; do not treat incomplete results as success
5. No defensive actions, IP blocking, notification or DB storage

### 2.2 Building and Testing

We create `app/agents/security_analysis_orchestrator.py` and `tests/test_security_analysis_orchestrator.py` as new files.

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
AGENT="$ROOT/app/agents/security_analysis_orchestrator.py"
TEST="$ROOT/tests/test_security_analysis_orchestrator.py"

echo "===== VM230: SECURITY ANALYSIS ORCHESTRATOR CREATION ====="

# Do not overwrite existing files.
if [ -e "$AGENT" ] || [ -e "$TEST" ]; then
    echo "ABORT: one or both target files already exist."
    exit 1
fi

cat > "$AGENT" <<'PY'
"""Read-only orchestrator for security event analysis."""

from dataclasses import dataclass

from app.agents.incident_correlation import (
    IncidentCorrelationAgent,
    IncidentCorrelationResult,
)
from app.agents.threat_analysis import ThreatAnalysisAgent
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal


@dataclass(frozen=True, slots=True)
class SecurityAnalysisResult:
    """Combined AI analysis and deterministic correlation results."""

    proposal: AIAnalysisProposal
    correlation: IncidentCorrelationResult


class SecurityAnalysisOrchestrator:
    """Coordinate correlation and threat analysis without taking action."""

    def __init__(
        self,
        correlation_agent: IncidentCorrelationAgent | None = None,
        threat_agent: ThreatAnalysisAgent | None = None,
    ) -> None:
        self._correlation_agent = (
            correlation_agent or IncidentCorrelationAgent()
        )
        self._threat_agent = threat_agent or ThreatAnalysisAgent()

    async def analyze(
        self,
        request: AIAnalysisRequest,
    ) -> SecurityAnalysisResult:
        # Correlation is deterministic and runs before the AI analysis.
        correlation = self._correlation_agent.analyze(request)

        # ThreatAnalysisAgent delegates to LogAnalysisAgent internally.
        # Call it once only to avoid duplicate AI analysis.
        proposal = await self._threat_agent.analyze(request)

        return SecurityAnalysisResult(
            proposal=proposal,
            correlation=correlation,
        )
PY

cat > "$TEST" <<'PY'
"""Unit tests for SecurityAnalysisOrchestrator."""

import unittest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.agents.incident_correlation import (
    IncidentCorrelationResult,
)
from app.agents.security_analysis_orchestrator import (
    SecurityAnalysisOrchestrator,
)
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import (
    AIAnalysisProposal,
    RecommendedAction,
)
from app.schemas.security_event import SecurityEvent


def make_request() -> AIAnalysisRequest:
    event = SecurityEvent(
        source="wazuh",
        severity="low",
        event_category="authentication",
        event_summary="Synthetic orchestrator test event",
    )
    return AIAnalysisRequest(events=[event])


def make_proposal(request: AIAnalysisRequest) -> AIAnalysisProposal:
    return AIAnalysisProposal(
        summary="Synthetic test analysis",
        severity="low",
        confidence=0.8,
        evidence_event_ids=[request.events[0].event_id],
        recommended_action=RecommendedAction.NO_ACTION,
        reasoning="Synthetic unit-test reasoning",
    )


class TestSecurityAnalysisOrchestrator(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.request = make_request()
        self.proposal = make_proposal(self.request)
        self.correlation_result = IncidentCorrelationResult(
            clusters=(),
            uncorrelated_event_ids=(self.request.events[0].event_id,),
        )

        self.correlation_agent = Mock()
        self.correlation_agent.analyze.return_value = self.correlation_result

        self.threat_agent = Mock()
        self.threat_agent.analyze = AsyncMock(return_value=self.proposal)

        self.orchestrator = SecurityAnalysisOrchestrator(
            correlation_agent=self.correlation_agent,
            threat_agent=self.threat_agent,
        )

    async def test_returns_combined_analysis_and_correlation(self):
        result = await self.orchestrator.analyze(self.request)

        self.assertIs(result.proposal, self.proposal)
        self.assertIs(result.correlation, self.correlation_result)
        self.correlation_agent.analyze.assert_called_once_with(self.request)
        self.threat_agent.analyze.assert_awaited_once_with(self.request)

    async def test_propagates_threat_analysis_failure(self):
        self.threat_agent.analyze.side_effect = RuntimeError(
            "synthetic threat analysis failure"
        )

        with self.assertRaisesRegex(
            RuntimeError, "synthetic threat analysis failure"
        ):
            await self.orchestrator.analyze(self.request)

        self.correlation_agent.analyze.assert_called_once_with(self.request)
        self.threat_agent.analyze.assert_awaited_once_with(self.request)

    async def test_propagates_correlation_failure_without_ai_call(self):
        self.correlation_agent.analyze.side_effect = ValueError(
            "synthetic correlation failure"
        )

        with self.assertRaisesRegex(
            ValueError, "synthetic correlation failure"
        ):
            await self.orchestrator.analyze(self.request)

        self.correlation_agent.analyze.assert_called_once_with(self.request)
        self.threat_agent.analyze.assert_not_awaited()

    async def test_calls_threat_agent_only_once(self):
        await self.orchestrator.analyze(self.request)

        self.threat_agent.analyze.assert_awaited_once()
        self.assertEqual(self.threat_agent.analyze.await_count, 1)


if __name__ == "__main__":
    unittest.main()
PY

chown root:ai-defense "$AGENT"
chmod 0640 "$AGENT"
chown root:root "$TEST"
chmod 0640 "$TEST"

echo
echo "--- 1. Created files ---"
stat -c '%n | %U:%G | %a | %s bytes' "$AGENT" "$TEST"

echo
echo "--- 2. Run orchestrator tests ---"
cd "$ROOT"
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
    discover -s "$ROOT/tests" \
    -p 'test_security_analysis_orchestrator.py' -v

echo
echo "--- 3. Run complete unit test suite ---"
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest \
    discover -s "$ROOT/tests" \
    -p 'test_*.py' -v

echo
echo "SECURITY_ANALYSIS_ORCHESTRATOR_TEST_RUN_COMPLETE"
```

| Test target | Result |
|---|---:|
| `IncidentCorrelationAgent` | 7 passed |
| `LogAnalysisAgent` | 2 passed |
| `ThreatAnalysisAgent` | 5 passed |
| `SecurityAnalysisOrchestrator` | 4 passed |
| Total | 18 passed, 0 failed |

We confirmed that the AI analysis runs only once, that when correlation fails the AI analysis is not run, and that when the AI analysis fails the exception is propagated.

## Chapter 3: The Defense Decision Agent

### 3.1 Existing Policy and Action Definitions

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager

echo "===== VM230: DEFENSE POLICY AGENT DISCOVERY ====="

echo
echo "--- 1. Policy directory inventory ---"
find "$ROOT/app/policies" -maxdepth 3 -type f -printf '%p | %s bytes\n' 2>/dev/null | sort || true

echo
echo "--- 2. Action and policy schemas ---"
for f in \
  "$ROOT/app/schemas/action.py" \
  "$ROOT/app/schemas/analysis_proposal.py" \
  "$ROOT/app/schemas/security_event.py"; do
  if [ -f "$f" ]; then
    echo "### $f"
    sed -n '1,300p' "$f"
  fi
done

echo
echo "--- 3. Policy and approval references ---"
grep -R -n -E \
  'ApprovalStatus|ActionProposal|TEMPORARY_BLOCK_IP|requires_human_approval|policy|approve|reject|ttl_seconds|target_ip' \
  "$ROOT/app" --include='*.py' || true

echo
echo "--- 4. Existing agent inventory ---"
find "$ROOT/app/agents" -maxdepth 1 -type f -name '*.py' -printf '%f\n' | sort

echo
echo "--- 5. Existing test inventory ---"
find "$ROOT/tests" -maxdepth 1 -type f -name 'test_*.py' -printf '%f\n' | sort

echo
echo "--- 6. Main application registration (source only) ---"
sed -n '1,280p' "$ROOT/app/main.py"

echo
echo "DEFENSE_POLICY_DISCOVERY_COMPLETE"
```

| Item | Existing rule |
|---|---|
| IP blocking target | global IPs only |
| TTL | 1–900 seconds |
| Evidence | two or more separate event IDs |
| Approval | required |
| Initial approval state | `PENDING` |
| AI's approval decision | the server-side policy takes precedence |

`app/policies/` was empty, and there was no `DefensePolicyAgent` yet.

### 3.2 Design

`DefensePolicyAgent` decides independently before an AI proposal is turned into an `ActionProposal`. Whatever the result, this agent itself performs no defensive actions.

| AI proposal | Decision |
|---|---|
| `NO_ACTION` | create no action |
| `MONITOR`, `HUMAN_REVIEW` | there is no corresponding existing `ActionType`, so err on the safe side and reject |
| `COLLECT_EVIDENCE`, `NOTIFY` | create a proposal |
| `TEMPORARY_BLOCK_IP` | check the IP, TTL, evidence IDs and correlation result, and always set `PENDING` |

IP blocking is further allowed only when all of the following hold.

- Two or more pieces of evidence are in the same correlation group (cluster)
- Severity is `high` or `critical`
- Confidence is `0.90` or higher

This is a fixed criterion on the defense policy side and cannot be changed by the AI's approval flag.

### 3.3 The Script to Build It

This script creates two files, `app/agents/defense_policy.py` and `tests/test_defense_policy_agent.py`, and also tests the edge conditions.

> **Run on: VM 230**

```bash
set -euo pipefail

ROOT=/opt/ai-defense-manager
test "$(id -u)" -eq 0
test -d "$ROOT/app/agents"
test -d "$ROOT/tests"
getent group ai-defense >/dev/null

cat > "$ROOT/app/agents/defense_policy.py" <<'PY'
from dataclasses import dataclass

from app.agents.incident_correlation import IncidentCorrelationResult
from app.schemas.action import ActionProposal, ActionType, ApprovalStatus
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal, RecommendedAction


@dataclass(frozen=True, slots=True)
class DefensePolicyDecision:
    allowed: bool
    reason: str
    action_proposal: ActionProposal | None = None


class DefensePolicyAgent:
    """Apply deterministic server-side policy; never execute defensive actions."""

    BLOCK_MIN_CONFIDENCE = 0.90
    BLOCK_SEVERITIES = frozenset({"high", "critical"})

    def evaluate(
        self,
        proposal: AIAnalysisProposal,
        request: AIAnalysisRequest,
        correlation: IncidentCorrelationResult,
    ) -> DefensePolicyDecision:
        request_ids = [event.event_id for event in request.events]
        if not request_ids or len(request_ids) != len(set(request_ids)):
            return DefensePolicyDecision(False, "request events are empty or contain duplicate IDs")

        cluster_ids = [
            event_id
            for cluster in correlation.clusters
            for event_id in cluster.event_ids
        ]
        uncorrelated_ids = list(correlation.uncorrelated_event_ids)
        correlation_ids = cluster_ids + uncorrelated_ids

        if len(correlation_ids) != len(set(correlation_ids)):
            return DefensePolicyDecision(False, "correlation result contains duplicate event IDs")
        if not set(correlation_ids).issubset(set(request_ids)):
            return DefensePolicyDecision(False, "correlation result contains unknown event IDs")

        evidence_ids = proposal.evidence_event_ids
        if not evidence_ids or len(evidence_ids) != len(set(evidence_ids)):
            return DefensePolicyDecision(False, "evidence IDs are empty or contain duplicates")
        if not set(evidence_ids).issubset(set(request_ids)):
            return DefensePolicyDecision(False, "proposal references unknown evidence events")
        if not set(evidence_ids).issubset(set(correlation_ids)):
            return DefensePolicyDecision(False, "proposal evidence is absent from correlation result")

        action = proposal.recommended_action
        if action == RecommendedAction.NO_ACTION:
            return DefensePolicyDecision(True, "no action required")

        action_mapping = {
            RecommendedAction.NOTIFY: ActionType.NOTIFY,
            RecommendedAction.COLLECT_EVIDENCE: ActionType.COLLECT_EVIDENCE,
            RecommendedAction.TEMPORARY_BLOCK_IP: ActionType.TEMPORARY_BLOCK_IP,
        }
        action_type = action_mapping.get(action)
        if action_type is None:
            return DefensePolicyDecision(False, f"unsupported action type: {action.value}")

        if action == RecommendedAction.TEMPORARY_BLOCK_IP:
            if proposal.severity not in self.BLOCK_SEVERITIES:
                return DefensePolicyDecision(False, "IP blocking requires high or critical severity")
            if proposal.confidence < self.BLOCK_MIN_CONFIDENCE:
                return DefensePolicyDecision(False, "IP blocking requires confidence of at least 0.90")

            evidence_set = set(evidence_ids)
            matching_cluster = any(
                len(evidence_set.intersection(cluster.event_ids)) >= 2
                and evidence_set.issubset(set(cluster.event_ids))
                for cluster in correlation.clusters
            )
            if not matching_cluster:
                return DefensePolicyDecision(
                    False,
                    "IP blocking evidence must belong to one correlated incident",
                )

        try:
            action_proposal = ActionProposal(
                source_analysis_id=request.request_id,
                action_type=action_type,
                target_ip=proposal.target_ip,
                ttl_seconds=proposal.ttl_seconds,
                evidence_event_ids=evidence_ids,
                approval_status=ApprovalStatus.PENDING,
                requires_human_approval=True,
            )
        except (TypeError, ValueError) as exc:
            return DefensePolicyDecision(
                False,
                f"action proposal violates server constraints: {exc}",
            )

        return DefensePolicyDecision(
            True,
            "action proposal passed server policy",
            action_proposal,
        )
PY

cat > "$ROOT/tests/test_defense_policy_agent.py" <<'PY'
import unittest
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import ValidationError

from app.agents.defense_policy import DefensePolicyAgent
from app.agents.incident_correlation import IncidentCluster, IncidentCorrelationResult
from app.schemas.analysis import AIAnalysisRequest
from app.schemas.analysis_proposal import AIAnalysisProposal, RecommendedAction
from app.schemas.security_event import SecurityEvent


class TestDefensePolicyAgent(unittest.TestCase):
    def setUp(self):
        self.agent = DefensePolicyAgent()
        self.events = [
            SecurityEvent(
                event_id=uuid4(),
                source="wazuh",
                observed_at=datetime(2026, 11, 24, 5, 0, tzinfo=timezone.utc),
                severity="high",
                agent_id="agent-1",
                event_category="authentication",
                event_summary=f"Failed login {i}",
            )
            for i in range(2)
        ]
        self.request = AIAnalysisRequest(events=self.events)
        self.ids = [event.event_id for event in self.events]
        self.cluster = IncidentCluster(
            agent_id="agent-1",
            event_category="authentication",
            event_ids=tuple(self.ids),
            started_at=self.events[0].observed_at,
            ended_at=self.events[1].observed_at,
        )
        self.correlation = IncidentCorrelationResult(
            clusters=(self.cluster,),
            uncorrelated_event_ids=(),
        )

    def proposal(self, action=RecommendedAction.NOTIFY, **overrides):
        values = {
            "summary": "Suspicious activity detected",
            "severity": "high",
            "confidence": 0.95,
            "evidence_event_ids": self.ids,
            "recommended_action": action,
            "reasoning": "Two related events were observed.",
        }
        values.update(overrides)
        return AIAnalysisProposal(**values)

    def test_notify_forces_human_approval_even_if_ai_says_false(self):
        result = self.agent.evaluate(
            self.proposal(requires_human_approval=False),
            self.request,
            self.correlation,
        )
        self.assertTrue(result.allowed)
        self.assertTrue(result.action_proposal.requires_human_approval)
        self.assertEqual(result.action_proposal.approval_status.value, "pending")

    def test_collect_evidence_is_supported(self):
        result = self.agent.evaluate(
            self.proposal(RecommendedAction.COLLECT_EVIDENCE),
            self.request,
            self.correlation,
        )
        self.assertTrue(result.allowed)
        self.assertEqual(result.action_proposal.action_type.value, "collect_evidence")

    def test_no_action_does_not_create_action(self):
        result = self.agent.evaluate(
            self.proposal(RecommendedAction.NO_ACTION),
            self.request,
            self.correlation,
        )
        self.assertTrue(result.allowed)
        self.assertIsNone(result.action_proposal)

    def test_monitor_and_human_review_are_rejected(self):
        for action in (RecommendedAction.MONITOR, RecommendedAction.HUMAN_REVIEW):
            with self.subTest(action=action):
                result = self.agent.evaluate(
                    self.proposal(action), self.request, self.correlation
                )
                self.assertFalse(result.allowed)
                self.assertIsNone(result.action_proposal)

    def test_private_ip_block_is_rejected_by_schema(self):
        with self.assertRaises(ValidationError):
            self.proposal(
                RecommendedAction.TEMPORARY_BLOCK_IP,
                target_ip="192.168.1.10",
                ttl_seconds=300,
            )

    def test_ttl_over_900_is_rejected_by_schema(self):
        with self.assertRaises(ValidationError):
            self.proposal(
                RecommendedAction.TEMPORARY_BLOCK_IP,
                target_ip="8.8.8.8",
                ttl_seconds=901,
            )

    def test_duplicate_evidence_is_rejected(self):
        result = self.agent.evaluate(
            self.proposal(evidence_event_ids=[self.ids[0], self.ids[0]]),
            self.request,
            self.correlation,
        )
        self.assertFalse(result.allowed)
        self.assertIn("duplicates", result.reason)

    def test_unknown_evidence_is_rejected(self):
        result = self.agent.evaluate(
            self.proposal(evidence_event_ids=[uuid4()]),
            self.request,
            self.correlation,
        )
        self.assertFalse(result.allowed)
        self.assertIn("unknown evidence", result.reason)

    def test_evidence_missing_from_correlation_is_rejected(self):
        incomplete = IncidentCorrelationResult(
            clusters=(),
            uncorrelated_event_ids=(self.ids[0],),
        )
        result = self.agent.evaluate(
            self.proposal(), self.request, incomplete
        )
        self.assertFalse(result.allowed)
        self.assertIn("absent from correlation", result.reason)

    def test_block_requires_high_or_critical_severity(self):
        result = self.agent.evaluate(
            self.proposal(
                RecommendedAction.TEMPORARY_BLOCK_IP,
                severity="medium",
                target_ip="8.8.8.8",
                ttl_seconds=300,
            ),
            self.request,
            self.correlation,
        )
        self.assertFalse(result.allowed)
        self.assertIn("severity", result.reason)

    def test_block_requires_minimum_confidence(self):
        result = self.agent.evaluate(
            self.proposal(
                RecommendedAction.TEMPORARY_BLOCK_IP,
                confidence=0.89,
                target_ip="8.8.8.8",
                ttl_seconds=300,
            ),
            self.request,
            self.correlation,
        )
        self.assertFalse(result.allowed)
        self.assertIn("confidence", result.reason)

    def test_block_requires_two_evidence_events_in_same_cluster(self):
        split = IncidentCorrelationResult(
            clusters=(
                IncidentCluster(
                    "agent-1",
                    "authentication",
                    (self.ids[0],),
                    self.events[0].observed_at,
                    self.events[0].observed_at,
                ),
            ),
            uncorrelated_event_ids=(self.ids[1],),
        )
        result = self.agent.evaluate(
            self.proposal(
                RecommendedAction.TEMPORARY_BLOCK_IP,
                target_ip="8.8.8.8",
                ttl_seconds=300,
            ),
            self.request,
            split,
        )
        self.assertFalse(result.allowed)
        self.assertIn("one correlated incident", result.reason)

    def test_valid_block_is_pending_and_human_approved(self):
        result = self.agent.evaluate(
            self.proposal(
                RecommendedAction.TEMPORARY_BLOCK_IP,
                target_ip="8.8.8.8",
                ttl_seconds=300,
                requires_human_approval=True,
            ),
            self.request,
            self.correlation,
        )
        self.assertTrue(result.allowed, result.reason)
        self.assertEqual(result.action_proposal.approval_status.value, "pending")
        self.assertTrue(result.action_proposal.requires_human_approval)

    def test_unknown_correlation_event_is_rejected(self):
        invalid = IncidentCorrelationResult(
            clusters=(),
            uncorrelated_event_ids=(uuid4(),),
        )
        result = self.agent.evaluate(
            self.proposal(), self.request, invalid
        )
        self.assertFalse(result.allowed)
        self.assertIn("correlation result contains unknown", result.reason)


if __name__ == "__main__":
    unittest.main()
PY

chown root:ai-defense "$ROOT/app/agents/defense_policy.py"
chmod 0640 "$ROOT/app/agents/defense_policy.py"
chown root:root "$ROOT/tests/test_defense_policy_agent.py"
chmod 0640 "$ROOT/tests/test_defense_policy_agent.py"

echo "===== VM230: DEFENSE POLICY AGENT TESTS ====="
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest discover \
  -s "$ROOT/tests" -p 'test_defense_policy_agent.py' -v

echo
echo "===== VM230: FULL TEST SUITE ====="
PYTHONPATH="$ROOT" "$ROOT/venv/bin/python" -m unittest discover \
  -s "$ROOT/tests" -p 'test_*.py' -v

echo
echo "===== CREATED FILE METADATA ====="
stat -c '%n | %U:%G | %a | %s bytes' \
  "$ROOT/app/agents/defense_policy.py" \
  "$ROOT/tests/test_defense_policy_agent.py"
```

**The result of running this script is not within the build records received** (see the Missing Information Memo).

## Closing Notes

In Part 71 we built the event correlation and analysis orchestration agents and designed the defense decision agent.

| Agent | File | Tests |
|---|---|---|
| `LogAnalysisAgent` | `app/agents/log_analysis.py` | 2 passed |
| `ThreatAnalysisAgent` | `app/agents/threat_analysis.py` | 5 passed |
| `IncidentCorrelationAgent` | `app/agents/incident_correlation.py` | 7 passed |
| `SecurityAnalysisOrchestrator` | `app/agents/security_analysis_orchestrator.py` | 4 passed |
| `DefensePolicyAgent` | `app/agents/defense_policy.py` (up to the build script; the result is not in the records) | — |

None of the agents is connected to the API yet, and none performs defensive actions.

This is the end of the build records.

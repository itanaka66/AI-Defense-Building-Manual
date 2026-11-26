---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 67: Finding the Breakage in Wazuh's Local Rules"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 67 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 66 we automated FSS verification on VM 230, but there was no path to report its results to Wazuh. Here, before integration, we examine the Wazuh Manager side on VM 220, read-only.

1. Check whether Wazuh Manager is configured to accept agents
2. Investigate the role of the Relay (8765) (a read-only API, not an entry point for events)
3. Find that the local rules `local_rules.xml` are broken as XML, and examine their structure
4. Without touching the production file, create a fixed candidate file

No configuration changes, agent registration, communication tests or service restarts. Credentials and secret keys are not displayed.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)

# Chapter 1: Wazuh Manager and the Relay

## 1.1 Configuration for Accepting Agents

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

## 1.2 The Relay's Structure

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

## 1.3 The Relay's GET and POST

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

# Chapter 2: The Breakage in `local_rules.xml`

## 2.1 Local Rules and Decoders

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

## 2.2 Where It Is Broken

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

## 2.3 Examining the Structure

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

# Chapter 3: Creating a Fixed Candidate

## 3.1 The Fix

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

## 3.2 Creating the Candidate File

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

# Closing Notes

In Part 67 we examined the Wazuh side on VM 220 and found the breakage in the local rules file.

| Item | Result |
|---|---|
| Wazuh Manager | configured to accept agents (1514, 1515) |
| Relay | only reads alerts (POST gives `405`); cannot be used as an entry point for FSS results |
| `local_rules.xml` | had two top-level `<group>` elements; broken as XML |
| Candidate | `/tmp/local_rules.xml.candidate-20261124` (one root, 8 rules, classifications preserved, `<same_srcip />`) |
| Production | not changed yet |

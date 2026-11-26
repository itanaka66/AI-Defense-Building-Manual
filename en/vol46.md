---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 46: Classifying Alerts and Deciding Which Fields to Pass to the LLM"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 46 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 45 we repaired the Wazuh configuration file. Here, to decide what data to pass to the LLM, we examine the contents of Wazuh alerts by counts and types only, **without displaying values**.

1. Tally the alerts by count, severity, rule and classification group
2. Check the definitions of the most frequent rules and run Wazuh's own test (`wazuh-analysisd -t`)
3. Examine the field names in the alert JSON and separate the fields that may be passed to the LLM from those that must not
4. Decide the types and constraints of the seven allowed fields, and try the conversion on real alerts in memory only

Event bodies, IP addresses, user names and commands are not displayed. Nothing is written to files, registered in a DB or sent to the LLM.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **pve**: the Proxmox host (root)

# Chapter 1: Tallying the Alerts

## 1.1 Count and Severity

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

## 1.2 Rules and Classification Groups

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

# Chapter 2: Checking the Rule Definitions

## 2.1 Rule Descriptions and Classification Conditions

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

## 2.2 Location of the Rule Files

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

## 2.3 Wazuh's Own Test

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

## 2.4 Definitions of the Local Rules

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

# Chapter 3: Deciding the Fields to Pass to the LLM

## 3.1 Field Names in the Alert JSON

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

## 3.2 Types and Missing Values of the Seven Fields

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

## 3.3 Constraints of the Seven Fields

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

## 3.4 Trying the Conversion in Memory

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

# Chapter 4: The Data Path

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

# Closing Notes

In Part 46 we examined the contents of the alerts without looking at values, and decided the fields to pass to the LLM.

| Item | Result |
|---|---|
| Alerts | 245 (mostly PAM, SSH and Proxmox authentication records; the 17 at Level 7 are PostgreSQL ERRORs) |
| Wazuh test | `wazuh-analysisd -t` gave `0` |
| Fields passed to the LLM | 7 (`timestamp`, `rule_id`, `severity`, `groups`, `description`, `decoder`, `agent_id`); everything else is discarded |
| Conversion test | all 245 succeeded; 0 forbidden fields leaked |

In the next part, Part 47, we examine the existing implementation of the AI Defense Manager on VM 230 and decide where to integrate the allowlist.

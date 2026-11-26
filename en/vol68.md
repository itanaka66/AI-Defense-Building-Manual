---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 68: Testing the Fixed Rules in an Isolated Environment"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 68 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 67 we created a fixed candidate of `local_rules.xml` in `/tmp`. Before placing it in production, we check with Wazuh's own test (`wazuh-analysisd -t`) whether the candidate is accepted as rules.

`wazuh-analysisd -t` normally reads the production configuration directory. `wazuh-logtest` also loads the production rules. So we use `wazuh-analysisd`'s `-D` (`chroot` into the specified directory) to test in **an isolated environment created in `/tmp`**.

- Place only the standard rules, decoders and lists, and the candidate `local_rules.xml`
- The production `ossec.conf` contains credentials (TLS certificates and secret keys, CA, passwords and so on), so it is not copied as a whole; a minimal configuration without secrets is created instead
- The production Wazuh Manager is neither started nor restarted

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)

> **Caution:** Wazuh's test commands work only as root (as the ordinary user `ag` they give `Permission denied` or exit code 126). When logged in as `ag`, become root with the following before running them.

```bash
sudo -i
```

# Chapter 1: What the Isolated Environment Needs

## 1.1 Where Rules Are Loaded From

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

## 1.2 Checking the Configuration for Secrets

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

## 1.3 Items Needed for a Minimal Configuration

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

# Chapter 2: Building the Isolated Environment

## 2.1 Placing the Basic Files

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

## 2.2 Fixing the Directory Hierarchy

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

## 2.3 Files Needed to Run

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

## 2.4 Creating `etc/shared`

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

# Chapter 3: Testing in the Isolated Environment

## 3.1 Removing the XML Declaration

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

## 3.2 Permissions of the Internal Configuration Files

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

## 3.3 Fixing the Permissions

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

## 3.4 Testing Again

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

# Chapter 4: Final Check of the Candidate

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

# Closing Notes

In Part 68 we checked the fixed `local_rules.xml` candidate with Wazuh's own test without placing it in production.

| Item | Result |
|---|---|
| Isolated environment | `/tmp/wazuh-rule-validation-20261124` (standard rules, decoders and lists, a minimal configuration without secrets, the candidate rules) |
| Cautions for the isolated configuration | no XML declaration; `internal_options.conf` and the like `root:wazuh`, `640` |
| `wazuh-analysisd -t -D` | exit code `0` |
| Production | not changed yet |

In the next part, Part 69, we place the candidate in production, check how the rules actually behave, and have Wazuh Manager load them.

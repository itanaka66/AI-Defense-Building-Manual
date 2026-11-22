---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 13: A Read-Only User for Wazuh Indexer"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 13 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". Based on the investigation in Part 12, we decided that the alerts read by the AI Defense Manager will come from the Wazuh Indexer. In Part 13, we create a dedicated role and user on the Indexer that can read only Wazuh alerts, and verify the scope of its permissions.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Everything is run on **security-core VM 220 (root)**.
- Passwords, password hashes and private keys appear neither on screen nor in this manual.
- The backup directory name (`wazuh-security-backup-20261120-120052`) is the one from the original build. Replace it with the name created in your environment.

## What We Create

| Kind | Name | Details |
|---|---|---|
| Role | `ai_defense_alerts_read` | Reads (`read`) only `wazuh-alerts-4.x-*`. No cluster permissions |
| User | `ai-defense-reader` | An internal user of the Indexer |
| Role mapping | `ai_defense_alerts_read` → `ai-defense-reader` | |

The existing `manage_wazuh_index` also includes delete, manage and write permissions, so it is not used.

# Chapter 1: Investigation

## 1.1 Existing Roles That Read Alerts

```bash
python3 -c 'import yaml; d=yaml.safe_load(open("/etc/wazuh-indexer/opensearch-security/roles.yml")); [(print("\n### "+k),print(yaml.safe_dump(v,sort_keys=False,allow_unicode=True))) for k,v in d.items() if isinstance(v,dict) and any("wazuh-alerts" in str(x) for x in v.get("index_permissions",[]))]'
```

At build time nothing was shown. No existing role reads only `wazuh-alerts`.

## 1.2 The Names of the Alert Indices

```bash
grep -nE '"index_patterns"|"index_pattern"|"index"' /etc/filebeat/wazuh-template.json
```

```bash
python3 -c 'import json; d=json.load(open("/etc/filebeat/wazuh-template.json")); print(json.dumps(d.get("index_patterns"),ensure_ascii=False,indent=2))'
```

The alert indices are `wazuh-alerts-4.x-*`. `wazuh-archives-4.x-*` is also in the target patterns, but archives are disabled in Filebeat, so they are not included in what the AI analyzes.

## 1.3 Existing Role Mappings and Users

Show only user names and role mappings (password hashes are not shown).

```bash
python3 -c 'import yaml; d=yaml.safe_load(open("/etc/wazuh-indexer/opensearch-security/roles_mapping.yml")); [(print("\n### "+k),print(yaml.safe_dump({x:v.get(x) for x in ("reserved","backend_roles","hosts","users") if x in v},sort_keys=False,allow_unicode=True))) for k,v in d.items() if isinstance(v,dict)]'
```

```bash
python3 -c 'import yaml; d=yaml.safe_load(open("/etc/wazuh-indexer/opensearch-security/internal_users.yml")); print("\n".join(k for k,v in d.items() if isinstance(v,dict)))'
```

Confirm that the name `ai-defense-reader` is not in use.

```bash
python3 -c 'import yaml; d=yaml.safe_load(open("/etc/wazuh-indexer/opensearch-security/action_groups.yml")); print("\n".join(k for k,v in d.items() if isinstance(v,dict)))'
```

`action_groups.yml` has no custom definitions. `read` is a permission group built into the Indexer.

## 1.4 The Tool That Applies the Settings

The Indexer's security settings are applied with `securityadmin.sh`. Java is the one bundled with the Indexer (`/usr/share/wazuh-indexer/jdk`).

```bash
ls -l /usr/share/wazuh-indexer/plugins/opensearch-security/tools/securityadmin.sh
```

```bash
command -v java && java -version 2>&1
```

```bash
ls -ld /usr/share/wazuh-indexer/jdk /usr/share/wazuh-indexer/jdk/bin/java 2>/dev/null
```

```bash
OPENSEARCH_JAVA_HOME=/usr/share/wazuh-indexer/jdk /usr/share/wazuh-indexer/plugins/opensearch-security/tools/securityadmin.sh -h
```

# Chapter 2: Preparing the Definition Files

## 2.1 Backup

```bash
backup_dir="/root/wazuh-security-backup-$(date +%Y%m%d-%H%M%S)" && install -d -m 700 "$backup_dir" && cp -a /etc/wazuh-indexer/opensearch-security/{roles.yml,roles_mapping.yml,internal_users.yml} "$backup_dir/" && chmod 600 "$backup_dir"/* && echo "BACKUP_OK: $backup_dir"
```

Note down the directory name shown.

## 2.2 The Role

```bash
cat > /root/ai_defense_alerts_read.yml <<'YAML'
_meta:
  type: "roles"
  config_version: 2

ai_defense_alerts_read:
  reserved: false
  hidden: false
  cluster_permissions: []
  index_permissions:
    - index_patterns:
        - "wazuh-alerts-4.x-*"
      dls: ""
      fls: []
      masked_fields: []
      allowed_actions:
        - "read"
  tenant_permissions: []
YAML
chmod 600 /root/ai_defense_alerts_read.yml
```

```bash
python3 -c 'import yaml; p="/root/ai_defense_alerts_read.yml"; d=yaml.safe_load(open(p)); r=d["ai_defense_alerts_read"]; assert d["_meta"]["type"]=="roles"; assert r["index_permissions"][0]["index_patterns"]==["wazuh-alerts-4.x-*"]; assert r["index_permissions"][0]["allowed_actions"]==["read"]; assert r["cluster_permissions"]==[]; print("YAML_OK"); print("INDEX_PATTERN:",r["index_permissions"][0]["index_patterns"]); print("ALLOWED_ACTIONS:",r["index_permissions"][0]["allowed_actions"]); print("CLUSTER_PERMISSIONS:",r["cluster_permissions"])'
```

## 2.3 The Role Mapping

```bash
cat > /root/ai_defense_alerts_mapping.yml <<'YAML'
_meta:
  type: "rolesmapping"
  config_version: 2

ai_defense_alerts_read:
  reserved: false
  backend_roles: []
  hosts: []
  users:
    - "ai-defense-reader"
YAML
chmod 600 /root/ai_defense_alerts_mapping.yml
```

```bash
python3 -c 'import yaml; p="/root/ai_defense_alerts_mapping.yml"; d=yaml.safe_load(open(p)); r=d["ai_defense_alerts_read"]; assert d["_meta"]["type"]=="rolesmapping"; assert r["users"]==["ai-defense-reader"]; assert r["backend_roles"]==[]; assert r["hosts"]==[]; print("MAPPING_YAML_OK"); print("ROLE: ai_defense_alerts_read"); print("USER:",r["users"][0])'
```

## 2.4 The Password Hash

For the Indexer's internal users, you register a bcrypt hash rather than the password itself. `hash.sh` asks for the password interactively, so writing its output directly to a file does not work (`Cannot allocate a console`). Run it with `script`, which records the interaction with the screen.

```bash
ls -l /usr/share/wazuh-indexer/plugins/opensearch-security/tools/hash.sh
```

```bash
sed -n '1,120p' /usr/share/wazuh-indexer/plugins/opensearch-security/tools/hash.sh
```

```bash
command -v script
```

```bash
umask 077; script -q -c 'OPENSEARCH_JAVA_HOME=/usr/share/wazuh-indexer/jdk /usr/share/wazuh-indexer/plugins/opensearch-security/tools/hash.sh' /root/ai-defense-reader.hash.transcript
```

When `[Password:]` is shown, enter a random password for `ai-defense-reader` (it is not shown on screen). Do not leave the password or the hash in chats or records.

Extract only the hash from the recording and put it in a file readable only by root.

```bash
python3 -c 'import re,pathlib; p=pathlib.Path("/root/ai-defense-reader.hash.transcript"); s=p.read_text(errors="replace") if p.exists() else ""; m=re.findall(r"\$(?:2[aby]|argon2id)\$[^\s\x1b]+",s); print("TRANSCRIPT_EXISTS:",p.exists()); print("HASH_COUNT:",len(m)); print("HASH_LENGTH:",len(m[-1]) if m else 0); print("RESULT:", "HASH_FOUND" if m else "HASH_NOT_FOUND")'
```

```bash
python3 -c 'import re,pathlib; s=pathlib.Path("/root/ai-defense-reader.hash.transcript").read_text(errors="replace"); m=re.findall(r"\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}",s); assert len(m)==1, f"Expected one bcrypt hash, found {len(m)}"; p=pathlib.Path("/root/ai-defense-reader.hash"); p.write_text(m[0]+"\n"); p.chmod(0o600); print("HASH_FILE_CREATED; FORMAT=bcrypt; LENGTH=60; MODE=600")'
```

## 2.5 The User

```bash
python3 - <<'PY'
import yaml
from pathlib import Path

password_hash = Path("/root/ai-defense-reader.hash").read_text().strip()
assert len(password_hash) == 60 and password_hash.startswith("$2")

config = {
    "_meta": {"type": "internalusers", "config_version": 2},
    "ai-defense-reader": {
        "hash": password_hash,
        "reserved": False,
        "backend_roles": [],
        "description": "Read-only access to Wazuh alert indices for AI Defense Manager"
    }
}

path = Path("/root/ai_defense_internal_user.yml")
path.write_text(yaml.safe_dump(config, sort_keys=False))
path.chmod(0o600)
print("INTERNAL_USER_FILE_CREATED")
print("USERNAME: ai-defense-reader")
print("HASH_FORMAT: bcrypt")
print("FILE_MODE: 600")
PY
```

## 2.6 Validating the Three Files

```bash
python3 - <<'PY'
import yaml
from pathlib import Path

files = {
    "/root/ai_defense_alerts_read.yml": ("roles", "ai_defense_alerts_read"),
    "/root/ai_defense_alerts_mapping.yml": ("rolesmapping", "ai_defense_alerts_read"),
    "/root/ai_defense_internal_user.yml": ("internalusers", "ai-defense-reader"),
}

for filename, (expected_type, expected_name) in files.items():
    path = Path(filename)
    data = yaml.safe_load(path.read_text())
    assert data["_meta"]["type"] == expected_type
    assert expected_name in data
    assert path.stat().st_mode & 0o077 == 0
    print(f"OK: {path.name}")

role = yaml.safe_load(Path("/root/ai_defense_alerts_read.yml").read_text())
mapping = yaml.safe_load(Path("/root/ai_defense_alerts_mapping.yml").read_text())
user = yaml.safe_load(Path("/root/ai_defense_internal_user.yml").read_text())

assert role["ai_defense_alerts_read"]["index_permissions"][0]["index_patterns"] == ["wazuh-alerts-4.x-*"]
assert role["ai_defense_alerts_read"]["index_permissions"][0]["allowed_actions"] == ["read"]
assert mapping["ai_defense_alerts_read"]["users"] == ["ai-defense-reader"]
assert len(user["ai-defense-reader"]["hash"]) == 60

print("ALL_VALIDATION_OK")
PY
```

## 2.7 Checking the Administrator Certificate

`securityadmin.sh` connects to the Indexer with the administrator certificate. Confirm that the certificate's Subject matches the administrator registered in the Indexer (`admin_dn`).

```bash
openssl x509 -in /etc/wazuh-indexer/certs/admin.pem -noout -subject -nameopt RFC2253
```

```bash
grep -nA5 -B2 'plugins.security.authcz.admin_dn' /etc/wazuh-indexer/opensearch.yml
```

At build time the Subject was `CN=admin,OU=Wazuh,O=Wazuh,...`, which matched `admin_dn`.

# Chapter 3: Applying to the Indexer

## 3.1 Caution: securityadmin.sh -f Replaces Each Type Entirely

`securityadmin.sh -f <file> -t <type>` **replaces entirely** the settings of that type (`roles`, `rolesmapping`, `internalusers`) with the contents of the specified file. If you apply files containing only what you want to add (the three made in Chapter 2) as they are, the existing roles, mappings and users disappear.

In the original build, the add-only files were applied first, and existing roles (`manage_wazuh_index`, `security_analytics_read_access` and others) disappeared. We restored them by creating "merged files" that add the new entries to the backup from 2.1 and applying those. This chapter shows the procedure of applying the merged files from the start.

## 3.2 Checking the Backup Contents

```bash
python3 - <<'PY'
import yaml
from pathlib import Path

p = Path("/root/wazuh-security-backup-20261120-120052/roles.yml")
data = yaml.safe_load(p.read_text())
print("BACKUP_ROLES:")
for name in sorted(data):
    if name != "_meta":
        print(" ", name)
PY
```

The backup at build time had 37 roles.

## 3.3 Creating the Merged Files

Add the entries from Chapter 2, one each, to the three backup files. Existing entries are kept as they are, and it stops if a name being added already exists.

```bash
python3 - <<'PY'
import copy
import stat
import yaml
from pathlib import Path

backup = Path("/root/wazuh-security-backup-20261120-120052")

specs = [
    ("roles.yml", "roles.yml", "/root/ai_defense_alerts_read.yml",
     "ai_defense_alerts_read"),
    ("roles_mapping.yml", "rolesmapping.yml",
     "/root/ai_defense_alerts_mapping.yml", "ai_defense_alerts_read"),
    ("internal_users.yml", "internalusers.yml",
     "/root/ai_defense_internal_user.yml", "ai-defense-reader"),
]

for source_name, output_name, addition_name, new_key in specs:
    source = backup / source_name
    addition = Path(addition_name)
    output = Path("/root/ai_defense_merged_" + output_name)

    original = yaml.safe_load(source.read_text())
    extra = yaml.safe_load(addition.read_text())

    assert "_meta" in original and "_meta" in extra
    assert new_key not in original, f"{new_key} already exists in backup"
    merged = copy.deepcopy(original)
    merged[new_key] = extra[new_key]

    output.write_text(yaml.safe_dump(
        merged, sort_keys=False, allow_unicode=True
    ))
    output.chmod(0o600)

    check = yaml.safe_load(output.read_text())
    assert set(check) == set(original) | {new_key}
    assert check["_meta"] == original["_meta"]
    assert stat.S_IMODE(output.stat().st_mode) == 0o600

    print(
        f"CREATED: {output.name}; "
        f"original_entries={len(original)-1}; "
        f"merged_entries={len(check)-1}; "
        f"new_entry={new_key}; mode=600"
    )

print("MERGED_CONFIGS_VALIDATED")
PY
```

## 3.4 Applying

Connect with the administrator certificate and apply the three types one at a time. Confirm that each shows `Done with success`.

```bash
OPENSEARCH_JAVA_HOME=/usr/share/wazuh-indexer/jdk /usr/share/wazuh-indexer/plugins/opensearch-security/tools/securityadmin.sh -h 127.0.0.1 -p 9200 -cacert /etc/wazuh-indexer/certs/root-ca.pem -cert /etc/wazuh-indexer/certs/admin.pem -key /etc/wazuh-indexer/certs/admin-key.pem -f /root/ai_defense_merged_roles.yml -t roles
```

```bash
OPENSEARCH_JAVA_HOME=/usr/share/wazuh-indexer/jdk /usr/share/wazuh-indexer/plugins/opensearch-security/tools/securityadmin.sh -h 127.0.0.1 -p 9200 -cacert /etc/wazuh-indexer/certs/root-ca.pem -cert /etc/wazuh-indexer/certs/admin.pem -key /etc/wazuh-indexer/certs/admin-key.pem -f /root/ai_defense_merged_rolesmapping.yml -t rolesmapping
```

```bash
OPENSEARCH_JAVA_HOME=/usr/share/wazuh-indexer/jdk /usr/share/wazuh-indexer/plugins/opensearch-security/tools/securityadmin.sh -h 127.0.0.1 -p 9200 -cacert /etc/wazuh-indexer/certs/root-ca.pem -cert /etc/wazuh-indexer/certs/admin.pem -key /etc/wazuh-indexer/certs/admin-key.pem -f /root/ai_defense_merged_internalusers.yml -t internalusers
```

# Chapter 4: Confirming What Was Applied

## 4.1 Are the Required Entries There?

```bash
python3 - <<'PY'
import json
import subprocess

base = "https://127.0.0.1:9200/_plugins/_security/api"
cert = "/etc/wazuh-indexer/certs/admin.pem"
key = "/etc/wazuh-indexer/certs/admin-key.pem"
ca = "/etc/wazuh-indexer/certs/root-ca.pem"

expected = {
    "roles": {
        "ai_defense_alerts_read",
        "manage_wazuh_index",
        "security_analytics_read_access",
    },
    "rolesmapping": {"ai_defense_alerts_read"},
    "internalusers": {"ai-defense-reader"},
}

for kind, required in expected.items():
    result = subprocess.run(
        ["curl", "-fsS", "--cacert", ca, "--cert", cert, "--key", key,
         f"{base}/{kind}"],
        capture_output=True, text=True
    )
    if result.returncode:
        raise SystemExit(f"{kind}: API_QUERY_FAILED: {result.stderr.strip()}")

    data = json.loads(result.stdout)
    names = set(data)
    missing = required - names
    print(
        f"{kind}: entries={len(names)}; "
        f"required_present={not missing}; "
        f"missing={sorted(missing)}"
    )
    if missing:
        raise SystemExit(f"{kind}: VALIDATION_FAILED")

print("SECURITY_CONFIG_VALIDATION_OK")
PY
```

## 4.2 Are All Existing Entries Still There?

Confirm that every entry in the backup is still present after applying.

```bash
python3 - <<'PY'
import json
import subprocess
import yaml
from pathlib import Path

base = "https://127.0.0.1:9200/_plugins/_security/api"
cert = "/etc/wazuh-indexer/certs/admin.pem"
key = "/etc/wazuh-indexer/certs/admin-key.pem"
ca = "/etc/wazuh-indexer/certs/root-ca.pem"
backup = Path("/root/wazuh-security-backup-20261120-120052")

checks = [
    ("roles", "roles.yml"),
    ("rolesmapping", "roles_mapping.yml"),
    ("internalusers", "internal_users.yml"),
]

for api_name, backup_name in checks:
    original = yaml.safe_load((backup / backup_name).read_text())
    result = subprocess.run(
        ["curl", "-fsS", "--cacert", ca, "--cert", cert, "--key", key,
         f"{base}/{api_name}"],
        capture_output=True, text=True, check=True
    )
    current = json.loads(result.stdout)
    expected = set(original) - {"_meta"}
    missing = expected - set(current)
    print(
        f"{api_name}: backup_entries={len(expected)}; "
        f"current_entries={len(current)}; "
        f"missing_entries={len(missing)}"
    )
    if missing:
        print("MISSING:", ", ".join(sorted(missing)))
        raise SystemExit("PRESERVATION_CHECK_FAILED")

print("ALL_BACKUP_ENTRIES_PRESERVED")
PY
```

Confirm `ALL_BACKUP_ENTRIES_PRESERVED`.

## 4.3 Authenticating the User

The password is entered with `getpass` and not shown on screen.

```bash
python3 - <<'PY'
import getpass
import json
import urllib.request
import urllib.error
import ssl
import base64

password = getpass.getpass("ai-defense-reader password: ")
context = ssl.create_default_context(
    cafile="/etc/wazuh-indexer/certs/root-ca.pem"
)
url = "https://127.0.0.1:9200/_plugins/_security/authinfo"
token = base64.b64encode(
    ("ai-defense-reader:" + password).encode()
).decode()
request = urllib.request.Request(
    url, headers={"Authorization": "Basic " + token}
)

try:
    with urllib.request.urlopen(request, context=context, timeout=10) as response:
        data = json.loads(response.read())
        print("HTTP_STATUS:", response.status)
        print("USER:", data.get("user_name"))
        print("BACKEND_ROLES:", data.get("backend_roles"))
        print("ROLES:", data.get("roles"))
        print("AUTHENTICATION_TEST_OK")
except urllib.error.HTTPError as e:
    print("HTTP_STATUS:", e.code)
    print("AUTHENTICATION_TEST_FAILED")
except Exception as e:
    print("CONNECTION_TEST_FAILED:", type(e).__name__, str(e))
finally:
    password = None
    token = None
PY
```

## 4.4 What Can Be Read

Confirm that alerts can be read and everything else is denied.

```bash
python3 - <<'PY'
import getpass
import ssl
import json
import base64
import urllib.request
import urllib.error

password = getpass.getpass("ai-defense-reader password: ")
ctx = ssl.create_default_context(
    cafile="/etc/wazuh-indexer/certs/root-ca.pem"
)
token = base64.b64encode(
    ("ai-defense-reader:" + password).encode()
).decode()

tests = [
    ("ALERTS_READ", "https://127.0.0.1:9200/wazuh-alerts-4.x-*/_search?size=0"),
    ("ARCHIVES_DENIED", "https://127.0.0.1:9200/wazuh-archives-4.x-*/_search?size=0"),
]

for name, url in tests:
    req = urllib.request.Request(
        url,
        headers={"Authorization": "Basic " + token}
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            print(name, "HTTP", response.status)
            if name == "ARCHIVES_DENIED":
                print("SCOPE_TEST_FAILED: archives unexpectedly accessible")
            else:
                print("ALERTS_READ_ALLOWED")
    except urllib.error.HTTPError as e:
        print(name, "HTTP", e.code)
        if name == "ARCHIVES_DENIED" and e.code == 403:
            print("ARCHIVES_ACCESS_DENIED_OK")
        elif name == "ALERTS_READ":
            print("ALERTS_READ_FAILED")
    except Exception as e:
        print(name, "ERROR", type(e).__name__, str(e))

password = None
token = None
PY
```

At build time, archives also returned HTTP 200. This is because the archives indices do not exist (zero targets), so it does not confirm the permissions. Look at indices that actually exist and check whether access to them is denied.

```bash
curl -fsS --cacert /etc/wazuh-indexer/certs/root-ca.pem \
  --cert /etc/wazuh-indexer/certs/admin.pem \
  --key /etc/wazuh-indexer/certs/admin-key.pem \
  'https://127.0.0.1:9200/_cat/indices/wazuh-*?h=index&s=index'
```

```bash
python3 - <<'PY'
import getpass
import ssl
import base64
import urllib.request
import urllib.error

password = getpass.getpass("ai-defense-reader password: ")
token = base64.b64encode(
    ("ai-defense-reader:" + password).encode()
).decode()

ctx = ssl.create_default_context(
    cafile="/etc/wazuh-indexer/certs/root-ca.pem"
)
req = urllib.request.Request(
    "https://127.0.0.1:9200/wazuh-monitoring-2026.47w/_search?size=0",
    headers={"Authorization": "Basic " + token}
)

try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
        print("MONITORING_ACCESS: HTTP", response.status)
        print("SCOPE_TEST_FAILED: unexpected access")
except urllib.error.HTTPError as e:
    print("MONITORING_ACCESS: HTTP", e.code)
    if e.code == 403:
        print("MONITORING_ACCESS_DENIED_OK")
    else:
        print("SCOPE_TEST_INCONCLUSIVE")
except Exception as e:
    print("TEST_ERROR:", type(e).__name__, str(e))

password = None
token = None
PY
```

Replace the index name (`wazuh-monitoring-2026.47w`) with a name from your environment in the list above.

| Test | Result at build time |
|---|---|
| User authentication | HTTP 200 |
| Searching alerts | HTTP 200 |
| Searching monitoring | HTTP 403 (denied) |
| Searching archives | Cannot be judged, because the index does not exist |

# Chapter 5: Regenerating the Password and Managing It in a File

## 5.1 Why Regenerate It

The password entered in 2.4 was not saved anywhere. The recording (`ai-defense-reader.hash.transcript`) contains only the hash, not the password itself, and the original password cannot be recovered from the hash.

The relay service built in the next part connects to the Indexer as this user, so regenerate a random password and save it in a file readable only by root. The role and permissions are not changed; only the password changes.

```bash
ls -l /root/ai-defense-reader.hash /root/ai_defense_merged_internalusers.yml
```

```bash
ls -l /root/ai-defense-reader.hash.transcript
```

```bash
file /root/ai-defense-reader.hash.transcript
```

Without showing the contents, confirm only that no password is contained.

```bash
python3 -c 'from pathlib import Path; p=Path("/root/ai-defense-reader.hash.transcript"); s=p.read_text(errors="replace"); print("PASSWORD_INPUT_PRESENT" if any(x in s.lower() for x in ("password", "enter password", "re-enter")) else "NO_PASSWORD_PROMPT_MARKER"); print("LINE_COUNT:", len(s.splitlines()))'
```

```bash
python3 -c 'from pathlib import Path; s=Path("/root/ai-defense-reader.hash.transcript").read_text(errors="replace"); [(print(f"LINE {i}: length={len(x)}, bcrypt_hash={x.strip().startswith(("$2a$","$2b$","$2y$"))}")) for i,x in enumerate(s.splitlines(),1)]'
```

## 5.2 Creating the Password and Hash

`hash.sh` can take the password from an environment variable with `-env`. Because it is not written in the command arguments, it does not remain in the process list or history.

```bash
sed -n '1,160p' /usr/share/wazuh-indexer/plugins/opensearch-security/tools/hash.sh
```

```bash
OPENSEARCH_JAVA_HOME=/usr/share/wazuh-indexer/jdk /usr/share/wazuh-indexer/plugins/opensearch-security/tools/hash.sh -h
```

Create a random password and save it in a file readable only by root (`600`). It is not shown on screen.

```bash
python3 -c 'import secrets, pathlib, os; p=pathlib.Path("/root/ai-defense-reader.password"); p.write_text(secrets.token_urlsafe(48)+"\n"); os.chmod(p,0o600); print("PASSWORD_FILE_CREATED; mode=600")'
```

```bash
umask 077; IFS= read -r AI_DEFENSE_READER_PASSWORD < /root/ai-defense-reader.password; export AI_DEFENSE_READER_PASSWORD; OPENSEARCH_JAVA_HOME=/usr/share/wazuh-indexer/jdk /usr/share/wazuh-indexer/plugins/opensearch-security/tools/hash.sh -env AI_DEFENSE_READER_PASSWORD > /root/ai-defense-reader.new.hash && chmod 600 /root/ai-defense-reader.new.hash; unset AI_DEFENSE_READER_PASSWORD
```

```bash
python3 -c 'from pathlib import Path; import os,re; p=Path("/root/ai-defense-reader.new.hash"); s=p.read_text().strip(); print("FILE_EXISTS:",p.is_file()); print("MODE:",oct(p.stat().st_mode & 0o777)); print("BCRYPT_VALID:",bool(re.fullmatch(r"\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}",s)))'
```

## 5.3 Applying

Create a file from the merged user file made in 3.3 with only the hash of `ai-defense-reader` replaced by the new one, and apply it (the other users remain as they are).

```bash
python3 -c 'import yaml; p="/root/ai_defense_merged_internalusers.yml"; d=yaml.safe_load(open(p)); u=d["ai-defense-reader"]; print("USER_PRESENT:", "ai-defense-reader" in d); print("FIELDS:", sorted(u.keys())); print("DESCRIPTION:", u.get("description")); print("HASH_PRESENT:", bool(u.get("hash")))'
```

```bash
python3 -c 'import yaml, pathlib, os; src=pathlib.Path("/root/ai_defense_merged_internalusers.yml"); hp=pathlib.Path("/root/ai-defense-reader.new.hash"); dst=pathlib.Path("/root/ai_defense_merged_internalusers.updated.yml"); d=yaml.safe_load(src.read_text()); d["ai-defense-reader"]["hash"]=hp.read_text().strip(); dst.write_text(yaml.safe_dump(d,sort_keys=False,allow_unicode=True)); os.chmod(dst,0o600); print("UPDATED_CONFIG_CREATED; users=",len(d)-1,"; mode=600")'
```

```bash
OPENSEARCH_JAVA_HOME=/usr/share/wazuh-indexer/jdk /usr/share/wazuh-indexer/plugins/opensearch-security/tools/securityadmin.sh -h 127.0.0.1 -p 9200 -cacert /etc/wazuh-indexer/certs/root-ca.pem -cert /etc/wazuh-indexer/certs/admin.pem -key /etc/wazuh-indexer/certs/admin-key.pem -f /root/ai_defense_merged_internalusers.updated.yml -t internalusers
```

> The merged file from 3.3 is based on the backup at the time it was applied. If Indexer users were added or changed after that, applying this file loses those changes. In that case, recreate it from the latest settings before applying.

## 5.4 Checking with the New Password

The password is read from the file and not shown on screen.

```bash
python3 - <<'PY'
import json
import urllib.request
import urllib.error
import base64
from pathlib import Path
from ssl import create_default_context

password = Path("/root/ai-defense-reader.password").read_text().strip()
token = base64.b64encode(f"ai-defense-reader:{password}".encode()).decode()
req = urllib.request.Request(
    "https://127.0.0.1:9200/_plugins/_security/authinfo",
    headers={"Authorization": f"Basic {token}"}
)
ctx = create_default_context(cafile="/etc/wazuh-indexer/certs/root-ca.pem")
try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        data = json.load(r)
        print("HTTP_STATUS:", r.status)
        print("USER:", data.get("user_name"))
        print("ROLE_PRESENT:", "ai_defense_alerts_read" in data.get("roles", []))
        print("AUTHENTICATION_TEST_OK")
except urllib.error.HTTPError as e:
    print("HTTP_STATUS:", e.code)
    print("AUTHENTICATION_TEST_FAILED")
PY
```

```bash
python3 - <<'PY'
import json, urllib.request, urllib.error, base64
from pathlib import Path
from ssl import create_default_context

password = Path("/root/ai-defense-reader.password").read_text().strip()
auth = base64.b64encode(f"ai-defense-reader:{password}".encode()).decode()
ctx = create_default_context(cafile="/etc/wazuh-indexer/certs/root-ca.pem")

for index, label in [
    ("wazuh-alerts-4.x-*/_search?size=0", "ALERTS"),
    ("wazuh-monitoring-*/_search?size=0", "MONITORING"),
]:
    req = urllib.request.Request(
        f"https://127.0.0.1:9200/{index}",
        headers={"Authorization": f"Basic {auth}"}
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            print(label, "HTTP", r.status)
    except urllib.error.HTTPError as e:
        print(label, "HTTP", e.code)
PY
```

If it shows `ALERTS HTTP 200` and `MONITORING HTTP 403`, the scope is correctly limited.

# Chapter 6: Preparing for the Relay API

## 6.1 Alert Fields

To decide which fields to pass to the AI Defense Manager, fetch only the latest alert and show only the field names (the contents are not shown).

```bash
python3 - <<'PY'
import json, urllib.request, base64
from pathlib import Path
from ssl import create_default_context

password = Path("/root/ai-defense-reader.password").read_text().strip()
auth = base64.b64encode(f"ai-defense-reader:{password}".encode()).decode()
body = json.dumps({
    "size": 1,
    "sort": [{"timestamp": {"order": "desc"}}],
    "_source": [
        "timestamp", "rule.id", "rule.level", "rule.description",
        "agent.id", "agent.name", "agent.ip", "manager.name",
        "location", "decoder.name", "data.srcip", "data.dstip",
        "data.srcport", "data.dstport", "data.protocol", "data.action"
    ]
}).encode()
req = urllib.request.Request(
    "https://127.0.0.1:9200/wazuh-alerts-4.x-*/_search",
    data=body,
    headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
)
ctx = create_default_context(cafile="/etc/wazuh-indexer/certs/root-ca.pem")
with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
    result = json.load(r)
source = result["hits"]["hits"][0].get("_source", {}) if result["hits"]["hits"] else {}
def paths(obj, prefix=""):
    out = []
    for k, v in obj.items():
        p = f"{prefix}.{k}" if prefix else k
        out.append(p)
        if isinstance(v, dict):
            out.extend(paths(v, p))
    return out
print("MATCH_COUNT:", result["hits"]["total"]["value"] if isinstance(result["hits"]["total"], dict) else result["hits"]["total"])
print("RETURNED_FIELD_PATHS:")
for field in paths(source):
    print(field)
PY
```

The relay API returns only the following 10 fields. It does not return `full_log`, arbitrary `data`, user names, commands, passwords and the like.

| Category | Fields |
|---|---|
| Time | `timestamp` |
| Rule | `rule.id`, `rule.level`, `rule.description` |
| Agent | `agent.id`, `agent.name`, `agent.ip` |
| Management server | `manager.name` |
| Detection information | `location`, `decoder.name` |

Check the type of each (this user has no permission to read mappings, so check with one actual alert).

```bash
python3 - <<'PY'
import json, urllib.request, urllib.error, base64
from pathlib import Path
from ssl import create_default_context

password = Path("/root/ai-defense-reader.password").read_text().strip()
auth = base64.b64encode(f"ai-defense-reader:{password}".encode()).decode()
body = json.dumps({
    "size": 1,
    "sort": [{"timestamp": {"order": "desc"}}],
    "_source": [
        "timestamp", "rule.id", "rule.level", "rule.description",
        "agent.id", "agent.name", "agent.ip", "manager.name",
        "location", "decoder.name"
    ]
}).encode()
req = urllib.request.Request(
    "https://127.0.0.1:9200/wazuh-alerts-4.x-*/_search",
    data=body,
    headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
)
ctx = create_default_context(cafile="/etc/wazuh-indexer/certs/root-ca.pem")
with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
    result = json.load(r)

def walk(obj, prefix=""):
    for k, v in obj.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            yield from walk(v, path)
        else:
            yield path, type(v).__name__

hits = result.get("hits", {}).get("hits", [])
print("SAMPLE_FOUND:", bool(hits))
if hits:
    for path, typ in sorted(walk(hits[0].get("_source", {}))):
        print(f"{path}: {typ}")
PY
```

At build time, `rule.level` was an integer and the other nine fields were strings.

## 6.2 Network and Firewall

The relay API will be placed on security-core and accessed from VM 230. Check the current listening state and the firewall.

```bash
ss -lntp
```

At build time, the Indexer (9200, 9300) listened only on 127.0.0.1 and was not exposed externally.

```bash
ufw status verbose
```

```bash
nft list ruleset
```

```bash
systemctl is-active firewalld
```

At build time, ufw was `inactive`, there were no nftables rules, and firewalld was also `inactive`; security-core had no OS firewall.

```bash
ip -br addr
```

```bash
ip route
```

```bash
ip route get 192.168.0.33
```

security-core has two networks (`enp6s18`: 192.168.0.220, `enp6s19`: 192.168.1.220), and VM 230 (192.168.0.33) is reached through `enp6s18` (192.168.0.220). The relay API will listen only on `192.168.0.220`.

```bash
python3 --version
```

At build time this was Python 3.12.3, and we confirmed that the relay API can be built with the standard library alone.

# Summary of Part 13

## What Was Built

| Kind | Name / location |
|---|---|
| Indexer role | `ai_defense_alerts_read` (only `read` on `wazuh-alerts-4.x-*`) |
| Indexer user | `ai-defense-reader` |
| Password | `/root/ai-defense-reader.password` (root only, `600`) |
| Settings backup | `/root/wazuh-security-backup-<date-time>/` |
| Merged settings | `/root/ai_defense_merged_*.yml`, `/root/ai_defense_merged_internalusers.updated.yml` |

## What Was Confirmed

- Alerts can be read, and monitoring is denied.
- Compared with the backup, all existing roles, mappings and users remain.
- The Indexer listens only on 127.0.0.1 and is not exposed externally.

## Cautions and What Remains

- `securityadmin.sh -f` replaces the settings of that type entirely. When adding, always apply a file that adds to the current settings (3.1).
- **[Risk, open]** security-core has no OS firewall (ufw, nftables, firewalld).
- Password hashes, recordings and settings files remain in `/root` (all readable only by root). Files no longer needed have not been cleaned up.
- The relay API itself (certificate, token, service) is built in the next part.

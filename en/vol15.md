---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 15: Passing the Relay Connection Details Safely to VM 230"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 15 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". We make the relay API (Relay), built on security-core (VM 220) in Part 14, usable from the AI Defense Manager (VM 230).

For VM 230 to call the Relay, it needs the following two things.

- The Relay's CA certificate (to verify the server certificate)
- The Bearer token (a secret)

We carry these two from VM 220 to VM 230 **using a temporary transfer-only account that can use SFTP only**, without enabling root SSH login. Once they have been carried over, the transfer account and its settings are all removed.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 220**: security-core (root)
  - **VM 230**: ai-defense-manager (root)
- The contents of tokens and private keys appear neither on screen nor in this manual.

# Chapter 1: The Receiving Location on VM 230

## 1.1 The Configuration Directory

> **Run on: VM 230**

```bash
ls -ld /etc/ai-defense-manager /opt/ai-defense-manager 2>&1
```

At build time `/etc/ai-defense-manager` did not exist yet. Separately from the application itself (`/opt/ai-defense-manager`), create a directory to hold connection details.

```bash
install -d -o root -g root -m 755 /etc/ai-defense-manager && echo "CONFIG_DIRECTORY_CREATED"
```

## 1.2 Checking the Run-As User

Check the dedicated user `ai-defense` that runs the AI Defense Manager.

```bash
getent passwd ai-defense; getent passwd aidefense
```

```bash
getent group ai-defense
```

At build time this was user `ai-defense` (UID 999), group `ai-defense` (GID 988), home `/opt/ai-defense-manager`, shell `/usr/sbin/nologin`.

## 1.3 The Directory for Connection Details

Make it `root:ai-defense` with `750` so that only the run-as user can read it.

```bash
install -d -o root -g ai-defense -m 750 /etc/ai-defense-manager/credentials && echo "CREDENTIAL_DIRECTORY_CREATED"
```

# Chapter 2: Verifying the SSH Host Key

Before connecting from VM 230 to VM 220 with SSH (SFTP), verify VM 220's host key through a separate path and then register it. We do not skip verification with `StrictHostKeyChecking=no`.

## 2.1 Showing the Fingerprint on VM 220

> **Run on: VM 220**

```bash
for f in /etc/ssh/ssh_host_*_key.pub; do [ -f "$f" ] && ssh-keygen -lf "$f"; done
```

## 2.2 Comparing with the Key Obtained on VM 230

> **Run on: VM 230**

```bash
ssh-keyscan -T 5 -t ed25519 192.168.0.220 2>/dev/null | ssh-keygen -lf -
```

Confirm that it matches the ED25519 fingerprint (`SHA256:...`) shown in 2.1. If it matches, register it in `known_hosts`.

```bash
install -d -o root -g root -m 700 /root/.ssh && ssh-keyscan -T 5 -t ed25519 192.168.0.220 2>/dev/null >> /root/.ssh/known_hosts && chmod 600 /root/.ssh/known_hosts && echo "VERIFIED_HOST_KEY_REGISTERED"
```

Also confirm that VM 230 has no other usable SSH public keys.

```bash
find /root/.ssh /home/aidefense/.ssh -maxdepth 1 -type f -name '*.pub' -exec ssh-keygen -lf {} \; 2>/dev/null
```

# Chapter 3: The Transfer-Only Account

## 3.1 A Dedicated User

> **Run on: VM 220**

```bash
getent passwd ai-defense-transfer
```

Create a user that cannot log in and whose password is locked. Only `incoming` inside the chroot is used for the transfer.

```bash
useradd --system --home-dir /srv/ai-defense-transfer --shell /usr/sbin/nologin --no-create-home ai-defense-transfer && install -d -o root -g root -m 755 /srv/ai-defense-transfer && install -d -o ai-defense-transfer -g ai-defense-transfer -m 700 /srv/ai-defense-transfer/incoming && passwd -l ai-defense-transfer && echo "TRANSFER_USER_CREATED"
```

Check the current SSH settings.

```bash
grep -nE '^[[:space:]]*(Include|Subsystem|Match|AuthorizedKeysFile|ChrootDirectory|ForceCommand|PubkeyAuthentication|PasswordAuthentication)' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf 2>/dev/null
```

Create the location for registering the public key.

```bash
install -d -o root -g root -m 755 /etc/ssh/authorized_keys
```

## 3.2 A Transfer-Only Key

> **Run on: VM 230**

Do not use an existing key; create an Ed25519 key used only for this transfer.

```bash
test ! -e /root/.ssh/ai-defense-transfer && test ! -e /root/.ssh/ai-defense-transfer.pub && ssh-keygen -q -t ed25519 -N '' -C 'ai-defense-transfer-vm230' -f /root/.ssh/ai-defense-transfer && chmod 600 /root/.ssh/ai-defense-transfer && chmod 644 /root/.ssh/ai-defense-transfer.pub && echo "DEDICATED_TRANSFER_KEY_CREATED"
```

Show only the public key (the private key is not shown).

```bash
cat /root/.ssh/ai-defense-transfer.pub
```

## 3.3 Registering the Public Key

> **Run on: VM 220**

Register the public key shown in 3.2. The public key in the following command is the one from the original build. **Replace it with the public key line shown in your own environment.**

```bash
printf '%s\n' 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBaZH9cnizGM2IlYlXTJMzl4T3ZdctkIEDw2xdGRafwW ai-defense-transfer-vm230' > /etc/ssh/authorized_keys/ai-defense-transfer && chown root:root /etc/ssh/authorized_keys/ai-defense-transfer && chmod 600 /etc/ssh/authorized_keys/ai-defense-transfer && ssh-keygen -lf /etc/ssh/authorized_keys/ai-defense-transfer
```

## 3.4 SSH Settings

> **Run on: VM 220**

```bash
tail -n 40 /etc/ssh/sshd_config
```

Add a `Match` block at the end that applies only to `ai-defense-transfer`. Other users' settings are not changed.

- `ChrootDirectory`: cannot leave `/srv/ai-defense-transfer`
- `ForceCommand internal-sftp`: SFTP only; no shell
- Public-key authentication only; no passwords
- Port forwarding, agent forwarding, X11 and tunnels are prohibited

```bash
cat >> /etc/ssh/sshd_config <<'EOF'

# Restricted transfer account for AI Defense Relay
Match User ai-defense-transfer
    ChrootDirectory /srv/ai-defense-transfer
    ForceCommand internal-sftp -d /incoming -u 077
    AuthorizedKeysFile /etc/ssh/authorized_keys/%u
    PubkeyAuthentication yes
    AuthenticationMethods publickey
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    PermitTTY no
    AllowTcpForwarding no
    AllowAgentForwarding no
    X11Forwarding no
    PermitTunnel no
    PermitUserRC no
EOF
```

```bash
sshd -t && echo "SSHD_CONFIG_SYNTAX_OK"
```

Check the values that actually take effect when connecting from VM 230.

```bash
sshd -T -C user=ai-defense-transfer,host=192.168.0.33,addr=192.168.0.33 | grep -E '^(chrootdirectory|forcecommand|authorizedkeysfile|authenticationmethods|pubkeyauthentication|passwordauthentication|kbdinteractiveauthentication|permittty|allowtcpforwarding|allowagentforwarding|x11forwarding|permittunnel|permituserrc) '
```

The chroot directory must be owned by root and not writable.

```bash
namei -l /srv/ai-defense-transfer/incoming
```

```bash
systemctl is-active ssh.service
```

Apply with a reload (re-reading the settings) rather than a restart. Existing SSH connections are not dropped.

```bash
systemctl reload ssh.service && echo "SSH_CONFIG_RELOADED"
```

## 3.5 Permissions of the Public Key File

In the original build, connecting from VM 230 with SFTP in this state was rejected at public-key authentication. VM 220's SSH log recorded that the public key file could not be opened (`Could not open user 'ai-defense-transfer' authorized keys ... Permission denied`).

```bash
journalctl -u ssh.service --since "5 minutes ago" --no-pager | tail -n 40
```

`AuthorizedKeysFile` is read with that user's permissions. With `root:root` `600`, `ai-defense-transfer` cannot read it, so set the group to `ai-defense-transfer` and the permissions to `640`.

> **Run on: VM 220**

```bash
chown root:ai-defense-transfer /etc/ssh/authorized_keys/ai-defense-transfer && chmod 640 /etc/ssh/authorized_keys/ai-defense-transfer && stat -c '%A %U:%G %n' /etc/ssh/authorized_keys/ai-defense-transfer
```

## 3.6 Checking the SFTP Connection

> **Run on: VM 230**

```bash
sftp -i /root/.ssh/ai-defense-transfer -o IdentitiesOnly=yes -o BatchMode=yes -b /dev/null ai-defense-transfer@192.168.0.220
```

If it finishes without errors, the connection works.

# Chapter 4: Carrying the CA Certificate and Token

## 4.1 Placing Them in the Transfer Location

> **Run on: VM 220**

```bash
install -o ai-defense-transfer -g ai-defense-transfer -m 644 /etc/ai-defense-relay/ca.crt /srv/ai-defense-transfer/incoming/relay-ca.crt && install -o ai-defense-transfer -g ai-defense-transfer -m 600 /etc/ai-defense-relay/api.token /srv/ai-defense-transfer/incoming/relay-api.token && stat -c '%A %U:%G %s bytes %n' /srv/ai-defense-transfer/incoming/relay-ca.crt /srv/ai-defense-transfer/incoming/relay-api.token
```

## 4.2 Receiving Them on VM 230

> **Run on: VM 230**

```bash
sftp -i /root/.ssh/ai-defense-transfer -o IdentitiesOnly=yes -o BatchMode=yes ai-defense-transfer@192.168.0.220 <<'SFTP'
get /incoming/relay-ca.crt /root/relay-ca.crt
get /incoming/relay-api.token /root/relay-api.token
bye
SFTP
```

Place the received files as `root:ai-defense` with `640`, and delete what remains in `/root`.

```bash
install -o root -g ai-defense -m 640 /root/relay-ca.crt /etc/ai-defense-manager/credentials/relay-ca.crt && install -o root -g ai-defense -m 640 /root/relay-api.token /etc/ai-defense-manager/credentials/relay-api.token && rm -f /root/relay-ca.crt /root/relay-api.token && stat -c '%A %U:%G %s bytes %n' /etc/ai-defense-manager/credentials/relay-ca.crt /etc/ai-defense-manager/credentials/relay-api.token
```

## 4.3 Confirming That the CA Certificate Is the Same

> **Run on: VM 230**

```bash
openssl x509 -in /etc/ai-defense-manager/credentials/relay-ca.crt -noout -subject -fingerprint -sha256
```

> **Run on: VM 220**

```bash
openssl x509 -in /etc/ai-defense-relay/ca.crt -noout -subject -fingerprint -sha256
```

If both `subject` values (`CN = AI-Defense-Relay-Internal-CA`) and the SHA256 fingerprints match, it was carried over correctly.

# Chapter 5: Calling the Relay from VM 230

## 5.1 /health

> **Run on: VM 230**

Without showing the token's value, check HTTPS, CA verification and Bearer authentication.

```bash
python3 - <<'PY'
import json
import ssl
import urllib.request

base = "/etc/ai-defense-manager/credentials"
with open(base + "/relay-api.token", "r") as f:
    token = f.read().strip()

ctx = ssl.create_default_context(cafile=base + "/relay-ca.crt")
req = urllib.request.Request(
    "https://192.168.0.220:8765/health",
    headers={"Authorization": "Bearer " + token},
    method="GET",
)
try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        print("HTTP_STATUS:", r.status)
        print("RESPONSE:", json.dumps(json.loads(r.read()), ensure_ascii=False))
except Exception as e:
    print("HEALTH_TEST_FAILED:", type(e).__name__, str(e))
    raise
PY
```

The result at build time was `HTTP_STATUS: 200`, `RESPONSE: {"status": "ok"}`.

## 5.2 /v1/alerts

Fetch five alerts from the last 60 minutes and show only the names of the fields returned.

```bash
python3 - <<'PY'
import json
import ssl
import urllib.request

base = "/etc/ai-defense-manager/credentials"
with open(base + "/relay-api.token") as f:
    token = f.read().strip()

ctx = ssl.create_default_context(cafile=base + "/relay-ca.crt")
req = urllib.request.Request(
    "https://192.168.0.220:8765/v1/alerts?limit=5&since_minutes=60",
    headers={"Authorization": "Bearer " + token},
)
with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
    data = json.loads(r.read())
    print("HTTP_STATUS:", r.status)
    print("COUNT:", data.get("count"))
    alerts = data.get("alerts", [])
    print("ALERTS_RETURNED:", len(alerts))
    for i, alert in enumerate(alerts):
        print("ALERT", i + 1, "FIELDS:", sorted(alert.keys()))
        print("RULE_FIELDS:", sorted(alert.get("rule", {}).keys()))
        print("AGENT_FIELDS:", sorted(alert.get("agent", {}).keys()))
PY
```

At build time five alerts were returned, and the fields of each alert were `agent.id`, `agent.name`, `decoder.name`, `location`, `manager.name`, `rule.description`, `rule.id`, `rule.level` and `timestamp`. The Relay returns the fields flat, with dotted names such as `rule.level`, so `RULE_FIELDS` and `AGENT_FIELDS` are empty. Fields with no value (`agent.ip` in this case) are not returned.

# Chapter 6: Removing the Transfer Account

The transfer is done, so clean up the whole temporary transfer mechanism.

## 6.1 Restoring the SSH Settings

> **Run on: VM 220**

```bash
tail -n 22 /etc/ssh/sshd_config && getent passwd ai-defense-transfer && ls -l /etc/ssh/authorized_keys/ai-defense-transfer
```

Take a backup and remove the `Match` block added in 3.4.

```bash
python3 - <<'PY'
from pathlib import Path
import shutil

p = Path("/etc/ssh/sshd_config")
s = p.read_text()
marker = "# Restricted transfer account for AI Defense Relay\n"
if s.count(marker) != 1:
    raise SystemExit("ERROR: expected exactly one transfer block marker")

backup = p.with_name("sshd_config.before-ai-defense-transfer-cleanup")
shutil.copy2(p, backup)

start = s.index(marker)
updated = s[:start].rstrip() + "\n"
p.write_text(updated)
print("BACKUP:", backup)
PY
sshd -t && echo "SSHD_CONFIG_SYNTAX_OK"
```

```bash
systemctl reload ssh.service && echo "SSH_CONFIG_RELOADED"
```

## 6.2 Deleting the User and Files

Confirm that no transfer sessions remain.

```bash
pgrep -af 'sshd: ai-defense-transfer' || echo "NO_ACTIVE_TRANSFER_SESSIONS"
```

```bash
rm -f /etc/ssh/authorized_keys/ai-defense-transfer && userdel ai-defense-transfer && groupdel ai-defense-transfer && rm -rf /srv/ai-defense-transfer && echo "TRANSFER_ACCOUNT_CLEANUP_DONE"
```

In the original build, `userdel` also removed the group, so `groupdel: group 'ai-defense-transfer' does not exist` was shown and the following `rm -rf` did not run. Check the state and delete the remaining directory.

```bash
getent passwd ai-defense-transfer || echo "TRANSFER_USER_REMOVED"; getent group ai-defense-transfer || echo "TRANSFER_GROUP_REMOVED"; ls -ld /srv/ai-defense-transfer 2>&1
```

```bash
rm -rf /srv/ai-defense-transfer && echo "TRANSFER_DIRECTORY_REMOVED"
```

## 6.3 Confirming That the Relay Is Still Running

```bash
systemctl is-active ai-defense-relay.service && ss -lntp '( sport = :8765 )'
```

It is done if it is `active` and listening on `192.168.0.220:8765`.

# Closing Notes

In Part 15 we placed the following connection details on VM 230.

| File (VM 230) | Permissions | Contents |
|---|---|---|
| `/etc/ai-defense-manager/credentials/relay-ca.crt` | `root:ai-defense 640` | The Relay's CA certificate |
| `/etc/ai-defense-manager/credentials/relay-api.token` | `root:ai-defense 640` | Bearer token |

The transfer user, the key registration, the SSH settings and the directories have been removed (the key `/root/.ssh/ai-defense-transfer` on VM 230 remains). Also, automatic start (`enable`) for the Relay service has not been set up at this point.

In the next part, we bring alerts taken from the Relay into the AI Defense Manager and connect them to AI analysis.

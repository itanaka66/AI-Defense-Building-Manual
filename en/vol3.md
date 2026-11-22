---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 3: Building the Alert-Storage Collector"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 3 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". We build a mechanism (the Incident Collector) that saves the alerts detected by Wazuh into PostgreSQL and manages them as incidents.

| Component | Role |
|---|---|
| Wazuh Manager (VM 220) | Performs detection and correlation analysis and records alerts in `alerts.json` |
| Incident Collector (VM 220) | Reads, validates and de-duplicates alerts and inserts them into the DB |
| PostgreSQL (LXC 109) | Stores the incident DB and event history |
| AI analysis agent (future) | Assesses threats, sets priorities and proposes responses |

## Notation

- Commands and file contents are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Each step begins with "Run on", which says where to run it. Operations on LXC 109 are run from the Proxmox host with `pct exec 109 --`, and operations on VM 220 from the Proxmox host with `qm guest exec 220 --` (some steps are run by logging in to VM 220 directly).
- "Example output" is the actual output from the build. In your environment, IDs, dates and so on will differ.
- Passwords are set in ways that leave no trace on screen, in chats or in the command history.

## State at the End of Part 2

| Item | State |
|---|---|
| Wazuh Manager | VM 220 (`192.168.0.220`), 4.14.10 |
| PostgreSQL | LXC 109 (`192.168.0.151`), 17.11 |
| PostgreSQL monitoring | Sanitizing filter, rules 100100–100106 |

# Chapter 1: Preparing the Target Database

So as not to break the existing PostgreSQL or Wazuh settings, we first examine the database layout and then create a schema and role for incident management.

## 1.1 Checking the Existing Databases

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
echo "===== POSTGRESQL DATABASE INVENTORY ====="

runuser -u postgres -- psql -X -P pager=off -c "
SELECT
    datname AS database,
    pg_catalog.pg_get_userbyid(datdba) AS owner,
    pg_size_pretty(pg_database_size(datname)) AS size,
    datallowconn AS allow_connections
FROM pg_database
WHERE datistemplate = false
ORDER BY datname;
"

echo
echo "===== POSTGRESQL VERSION ====="
runuser -u postgres -- psql -X -Atc "SELECT version();"
'
```

At build time there were 17 databases, including `security_workbench` (owner `security_workbench`) intended for security use.

## 1.2 Checking the Contents of security_workbench

Before creating a new database, check whether `security_workbench` is already in use. All operations in this section are read-only.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
runuser -u postgres -- psql -X -d security_workbench -P pager=off -c "
SELECT
    schemaname AS schema,
    tablename AS table,
    tableowner AS owner
FROM pg_tables
WHERE schemaname NOT IN (
    '\''pg_catalog'\'',
    '\''information_schema'\''
)
ORDER BY schemaname, tablename;
"
'
```

Confirm that the user tables are `(0 rows)`.

Check the schemas and roles.

```bash
pct exec 109 -- bash -c '
runuser -u postgres -- psql -X -d security_workbench -P pager=off -c "
SELECT schema_name, schema_owner
FROM information_schema.schemata
WHERE schema_name NOT IN (
    '\''pg_catalog'\'',
    '\''information_schema'\''
)
ORDER BY schema_name;
"

echo "===== ROLES ====="

runuser -u postgres -- psql -X -d security_workbench -P pager=off -c "
SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolcanlogin
FROM pg_roles
WHERE rolname IN (
    '\''security_workbench'\'',
    '\''postgres'\''
)
ORDER BY rolname;
"
'
```

Check the privileges on the `public` schema.

```bash
pct exec 109 -- bash -c '
runuser -u postgres -- psql -X -d security_workbench -P pager=off -c "
SELECT
    '\''security_workbench'\'' AS role,
    has_schema_privilege(
        '\''security_workbench'\'',
        '\''public'\'',
        '\''USAGE'\''
    ) AS public_usage,
    has_schema_privilege(
        '\''security_workbench'\'',
        '\''public'\'',
        '\''CREATE'\''
    ) AS public_create,
    '\''postgres'\'' AS admin_role,
    has_schema_privilege(
        '\''postgres'\'',
        '\''public'\'',
        '\''CREATE'\''
    ) AS postgres_create;
"
'
```

| Item | State at build time |
|---|---|
| User tables | 0 |
| User schemas | `public` only |
| `security_workbench` role | Ordinary user (no SUPERUSER, CREATEDB or CREATEROLE; LOGIN allowed) |
| Privileges on the `public` schema | `security_workbench` has USAGE and CREATE |

> There is no view named `information_schema.schema_privileges` in PostgreSQL 17. Check schema privileges with the `has_schema_privilege()` function as above.

**Decision:** Use the existing `security_workbench` database. However, leave the existing `public` schema untouched and create a new `incident` schema dedicated to incident management. Also separate the "collector role" that writes events from Wazuh from the role that manages the schema and tables (`postgres`). The privileges of the existing `security_workbench` role are not changed.

## 1.3 Creating the Dedicated Schema

Changes to the database start here. This operation only creates one dedicated schema and does not touch existing tables or data.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
set -e

runuser -u postgres -- psql -X -v ON_ERROR_STOP=1 \
  -d security_workbench \
  -c "CREATE SCHEMA incident AUTHORIZATION postgres;"

echo
echo "===== VERIFY INCIDENT SCHEMA ====="

runuser -u postgres -- psql -X -d security_workbench -c "
SELECT
    schema_name,
    schema_owner
FROM information_schema.schemata
WHERE schema_name = '\''incident'\'';
"
'
```

Example output:

```text
CREATE SCHEMA

===== VERIFY INCIDENT SCHEMA =====
 schema_name | schema_owner 
-------------+--------------
 incident    | postgres
(1 row)
```

## 1.4 Creating the Collector Role

Confirm that the role name `wazuh_collector` is not yet in use.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
runuser -u postgres -- psql -X -P pager=off -c "
SELECT
    rolname,
    rolsuper,
    rolcreatedb,
    rolcreaterole,
    rolcanlogin
FROM pg_roles
WHERE rolname = '\''wazuh_collector'\'';
"
'
```

If `(0 rows)` is returned, there is no name conflict.

First, create a role that cannot log in and has no administrative privileges at all.

```bash
pct exec 109 -- bash -c '
set -e

runuser -u postgres -- psql -X -v ON_ERROR_STOP=1 \
  -d security_workbench \
  -c "CREATE ROLE wazuh_collector
      NOLOGIN
      NOSUPERUSER
      NOCREATEDB
      NOCREATEROLE
      NOREPLICATION
      NOBYPASSRLS
      NOINHERIT;"

echo
echo "===== VERIFY COLLECTOR ROLE ====="

runuser -u postgres -- psql -X -P pager=off -c "
SELECT
    rolname,
    rolsuper,
    rolcreatedb,
    rolcreaterole,
    rolreplication,
    rolbypassrls,
    rolinherit,
    rolcanlogin
FROM pg_roles
WHERE rolname = '\''wazuh_collector'\'';
"
'
```

If every column is `f` (disabled), it is in a safe initial state.

## 1.5 Setting the Password

To keep the password out of the shell history and SQL, use PostgreSQL's interactive password setting function.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- runuser -u postgres -- psql -X -d security_workbench
```

When the `security_workbench=#` prompt appears, enter the following.

```text
\password wazuh_collector
```

Enter the new password twice (the characters are not shown as you type).

- Use a sufficiently long random password (32 characters or more is recommended).
- Keep it safely in a password manager or similar, and do not paste it into chats or documents.

When done, enter the following to exit.

```text
\q
```

Login is not allowed yet at this stage.

## 1.6 Granting Connection and Schema Usage Privileges

Allow only connecting to the database and using the `incident` schema. Do not grant privileges to create objects or administrative privileges.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
set -e

runuser -u postgres -- psql -X -v ON_ERROR_STOP=1 \
  -d security_workbench <<'"'"'SQL'"'"'
GRANT CONNECT ON DATABASE security_workbench TO wazuh_collector;
GRANT USAGE ON SCHEMA incident TO wazuh_collector;
SQL

echo
echo "===== VERIFY PRIVILEGES ====="

runuser -u postgres -- psql -X -d security_workbench -P pager=off -c "
SELECT
    has_database_privilege(
        '\''wazuh_collector'\'',
        '\''security_workbench'\'',
        '\''CONNECT'\''
    ) AS can_connect,
    has_schema_privilege(
        '\''wazuh_collector'\'',
        '\''incident'\'',
        '\''USAGE'\''
    ) AS can_use_incident_schema,
    has_schema_privilege(
        '\''wazuh_collector'\'',
        '\''incident'\'',
        '\''CREATE'\''
    ) AS can_create_objects;
"
'
```

| Privilege | Expected value |
|---|---|
| Connect to the DB (CONNECT) | `t` |
| Use the `incident` schema (USAGE) | `t` |
| Create in the `incident` schema (CREATE) | `f` |

# Chapter 2: Checking the Network and TLS

We make it possible to connect safely from the Wazuh Manager (`192.168.0.220`) to PostgreSQL (`192.168.0.151`). Before allowing login, check the listen settings, the access rules and the TLS certificate. All operations in this chapter are read-only.

## 2.1 Checking the Listen Settings and Access Rules

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
echo "===== POSTGRESQL NETWORK SETTINGS ====="

runuser -u postgres -- psql -X -P pager=off -c "
SELECT
    name,
    setting,
    source,
    pending_restart
FROM pg_settings
WHERE name IN (
    '\''listen_addresses'\'',
    '\''port'\'',
    '\''ssl'\'',
    '\''password_encryption'\'',
    '\''hba_file'\''
)
ORDER BY name;
"

echo
echo "===== LISTENING SOCKETS ====="
ss -lntp | grep ":5432" || true

echo
echo "===== PG_HBA CONFIGURATION ====="
runuser -u postgres -- psql -X -P pager=off -c "
SELECT
    line_number,
    type,
    database,
    user_name,
    address,
    auth_method,
    error
FROM pg_hba_file_rules
ORDER BY line_number;
"
'
```

Check the actual contents of `pg_hba.conf` and the parsed rules (including netmasks).

```bash
pct exec 109 -- bash -c '
echo "===== PG_HBA FILE ====="
nl -ba /etc/postgresql/17/main/pg_hba.conf

echo
echo "===== PARSED HBA RULES ====="
runuser -u postgres -- psql -X -P pager=off -c "
SELECT
    line_number,
    type,
    database,
    user_name,
    address,
    netmask,
    auth_method,
    error
FROM pg_hba_file_rules
ORDER BY line_number;
"
'
```

At build time, PostgreSQL was listening on port 5432 on all IPv4 and IPv6 interfaces, and line 11 of `pg_hba.conf` had the following broad access rule.

```text
host    all    all    0.0.0.0/0    md5
```

This rule allows any IPv4 source to connect to every database as every user (authentication is still required). To avoid breaking existing applications' connections, we do not change this rule here. Access for Wazuh is added as a separate dedicated rule (Chapter 4).

> **Note:** This broad rule is kept as is to match existing operations. If it becomes a security problem, it will later be changed to limit the sources.

## 2.2 Checking the TCP Connection from the Wazuh Manager

Check only the TCP connection, without logging in to the database.

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
echo "===== POSTGRESQL TCP CONNECTIVITY ====="
nc -vz -w 3 192.168.0.151 5432
'
```

If `err-data` shows `Connection to 192.168.0.151 5432 port [tcp/postgresql] succeeded!`, the network path is available.

## 2.3 Checking the TLS Certificate

To encrypt traffic that includes credentials, check PostgreSQL's TLS settings. The contents of the private key are not shown.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
set -e

echo "===== TLS CONFIGURATION ====="

runuser -u postgres -- psql -X -P pager=off -c "
SELECT name, setting
FROM pg_settings
WHERE name IN (
    '\''ssl'\'',
    '\''ssl_cert_file'\'',
    '\''ssl_key_file'\'',
    '\''ssl_ca_file'\'',
    '\''data_directory'\''
)
ORDER BY name;
"

echo
echo "===== SERVER CERTIFICATE ====="

CERT=$(runuser -u postgres -- psql -X -Atc "SHOW ssl_cert_file;")
DATA=$(runuser -u postgres -- psql -X -Atc "SHOW data_directory;")

case "$CERT" in
    /*) CERT_PATH="$CERT" ;;
    *) CERT_PATH="$DATA/$CERT" ;;
esac

if [ -f "$CERT_PATH" ]; then
    stat -c "%U:%G %a %n" "$CERT_PATH"
    openssl x509 -in "$CERT_PATH" -noout -subject -issuer -dates
else
    echo "Certificate file not found: $CERT_PATH"
fi
'
```

```bash
pct exec 109 -- bash -c '
echo "===== CERTIFICATE SAN ====="
openssl x509 \
  -in /etc/ssl/certs/ssl-cert-snakeoil.pem \
  -noout -ext subjectAltName

echo
echo "===== CERTIFICATE FINGERPRINT ====="
openssl x509 \
  -in /etc/ssl/certs/ssl-cert-snakeoil.pem \
  -noout -fingerprint -sha256

echo
echo "===== PRIVATE KEY PERMISSIONS ====="
stat -c "%U:%G %a %n" \
  /etc/ssl/private/ssl-cert-snakeoil.key

echo
echo "===== POSTGRESQL SSL GROUP ====="
id postgres
'
```

| Item | State at build time |
|---|---|
| PostgreSQL SSL | `on` |
| Server certificate | `/etc/ssl/certs/ssl-cert-snakeoil.pem` (self-signed) |
| CN / SAN | `postgresql.neomedia.mydns.jp` (no IP address SAN) |
| Expiry | August 11, 2036 |
| CA certificate | Not set |
| Private key | `root:ssl-cert 640` (`postgres` belongs to the `ssl-cert` group) |

TLS encryption is enabled, but because the certificate is self-signed, Wazuh cannot verify as is that the server is genuine.

## 2.4 Checking That the Certificate and Private Key Match

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
CERT=/etc/ssl/certs/ssl-cert-snakeoil.pem
KEY=/etc/ssl/private/ssl-cert-snakeoil.key

echo "===== SELF-SIGNED CERTIFICATE VALIDATION ====="
openssl verify -CAfile "$CERT" "$CERT"

echo
echo "===== DNS NAME VALIDATION ====="
openssl x509 -in "$CERT" \
  -noout -checkhost postgresql.neomedia.mydns.jp

echo
echo "===== CERTIFICATE PUBLIC KEY HASH ====="
openssl x509 -in "$CERT" -pubkey -noout \
  | openssl pkey -pubin -outform DER \
  | sha256sum

echo
echo "===== PRIVATE KEY PUBLIC KEY HASH ====="
openssl pkey -in "$KEY" -pubout -outform DER \
  | sha256sum
'
```

| Check | Expected result |
|---|---|
| Verification of the self-signed certificate | OK |
| Match with the DNS name | Matches `postgresql.neomedia.mydns.jp` |
| Public key hash of the certificate and private key | The two match |

**Decision:** We do not replace the certificate right away. We register this certificate as a "trusted certificate" on the Wazuh Manager side and connect with `verify-full`, which also verifies the server name. The certificate's DNS name is used as the server name, and the IP address is fixed to `192.168.0.151`.

# Chapter 3: Preparing the Connection on the Wazuh Manager Side

## 3.1 Checking the TLS Handshake

Check the TLS connection from VM 220 to PostgreSQL. We do not log in to the DB.

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
echo "===== POSTGRESQL TLS HANDSHAKE ====="

timeout 10 openssl s_client \
  -starttls postgres \
  -connect 192.168.0.151:5432 \
  -servername postgresql.neomedia.mydns.jp \
  -showcerts </dev/null 2>&1 \
  | grep -E "CONNECTED|subject=|issuer=|Protocol|Cipher|Verify return code|BEGIN CERTIFICATE|END CERTIFICATE"
'
```

At build time, the connection used `TLSv1.3` and `TLS_AES_256_GCM_SHA384`. `Verify return code: 18 (self-signed certificate)` does not mean the connection failed; it means VM 220 does not yet trust this self-signed certificate.

## 3.2 Comparing the Fingerprint of the Received Certificate

Save the certificate received by VM 220 to a temporary file and show its SHA-256 fingerprint.

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
set -e

CERT=/tmp/postgresql-server-ca.pem

timeout 10 openssl s_client \
  -starttls postgres \
  -connect 192.168.0.151:5432 \
  -servername postgresql.neomedia.mydns.jp \
  -showcerts </dev/null 2>/dev/null \
  | sed -n "/-----BEGIN CERTIFICATE-----/,/-----END CERTIFICATE-----/p" \
  > "$CERT"

echo "===== RECEIVED CERTIFICATE ====="
openssl x509 -in "$CERT" -noout -subject -issuer

echo
echo "===== SHA256 FINGERPRINT ====="
openssl x509 -in "$CERT" -noout -fingerprint -sha256
'
```

Confirm that the fingerprint shown exactly matches the one checked inside LXC 109 in 2.3. The fingerprint at build time was as follows.

```text
3D:69:26:B8:3B:D0:2B:BE:00:BA:E0:53:2E:B7:9F:BE:9B:3A:36:D8:09:5C:59:73:76:52:7A:3D:F1:33:45:81
```

If they match, the certificate received over the network is confirmed to be the PostgreSQL server's genuine certificate.

## 3.3 Placing It as a Dedicated Trusted Certificate

Do not register it in the OS-wide CA store; place it as a file used only for PostgreSQL connections.

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
set -e

install -o root -g root -m 0644 \
  /tmp/postgresql-server-ca.pem \
  /etc/ssl/certs/postgresql-server-ca.pem

echo "===== CERTIFICATE FILE ====="
stat -c "%U:%G %a %s %n" \
  /etc/ssl/certs/postgresql-server-ca.pem

echo
echo "===== TRUST VALIDATION ====="
openssl verify \
  -CAfile /etc/ssl/certs/postgresql-server-ca.pem \
  /etc/ssl/certs/postgresql-server-ca.pem

echo
echo "===== HOSTNAME VALIDATION ====="
openssl x509 \
  -in /etc/ssl/certs/postgresql-server-ca.pem \
  -noout -checkhost postgresql.neomedia.mydns.jp
'
```

If `/etc/ssl/certs/postgresql-server-ca.pem: OK` and `Hostname postgresql.neomedia.mydns.jp does match certificate` are shown, it has succeeded.

## 3.4 Installing the PostgreSQL Client

Check whether VM 220 has the PostgreSQL client (`psql`).

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
echo "===== PSQL CLIENT ====="
command -v psql || true

echo
echo "===== PSQL VERSION ====="
psql --version 2>/dev/null || true

echo
echo "===== CERTIFICATE READ ACCESS ====="
test -r /etc/ssl/certs/postgresql-server-ca.pem \
  && echo "OK: certificate is readable" \
  || echo "ERROR: certificate is not readable"
'
```

If there is no `psql`, check the standard Ubuntu package and install it. The PostgreSQL server itself is not installed.

```bash
qm guest exec 220 -- bash -c '
echo "===== POSTGRESQL CLIENT PACKAGE ====="
apt-cache policy postgresql-client
'
```

```bash
qm guest exec 220 -- bash -c '
apt-get update &&
DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql-client
'
```

The standard Ubuntu 24.04 `postgresql-client` (version 16) is installed. It can also connect to a PostgreSQL 17 server.

## 3.5 Checking the Connection Parameters

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
echo "===== PSQL VERSION ====="
psql --version

echo
echo "===== HOSTNAME RESOLUTION ====="
getent hosts postgresql.neomedia.mydns.jp || true

echo
echo "===== DATABASE PORT ====="
nc -vz -w 3 192.168.0.151 5432
'
```

At build time, the certificate's DNS name `postgresql.neomedia.mydns.jp` did not resolve. It does not need to be registered in DNS. If you specify the server's IP address with `PGHOSTADDR` (or `hostaddr`) and the certificate's DNS name with `PGHOST` (`host`), you can connect by IP while still verifying the host name.

Check the parameters and the certificate with this combination. No password is set and we do not log in.

```bash
qm guest exec 220 -- bash -c '
export PGHOST=postgresql.neomedia.mydns.jp
export PGHOSTADDR=192.168.0.151
export PGPORT=5432
export PGDATABASE=security_workbench
export PGUSER=wazuh_collector
export PGSSLMODE=verify-full
export PGSSLROOTCERT=/etc/ssl/certs/postgresql-server-ca.pem

echo "===== CONNECTION PARAMETERS ====="
printf "PGHOST=%s\n" "$PGHOST"
printf "PGHOSTADDR=%s\n" "$PGHOSTADDR"
printf "PGPORT=%s\n" "$PGPORT"
printf "PGDATABASE=%s\n" "$PGDATABASE"
printf "PGUSER=%s\n" "$PGUSER"
printf "PGSSLMODE=%s\n" "$PGSSLMODE"
printf "PGSSLROOTCERT=%s\n" "$PGSSLROOTCERT"

echo
echo "===== CERTIFICATE VALIDATION ====="
openssl verify \
  -CAfile "$PGSSLROOTCERT" \
  "$PGSSLROOTCERT"
'
```

| Parameter | Value | Meaning |
|---|---|---|
| PGHOSTADDR | `192.168.0.151` | The actual IP to connect to |
| PGHOST | `postgresql.neomedia.mydns.jp` | The name verified against the certificate |
| PGSSLMODE | `verify-full` | Encrypt and also verify the certificate and host name |
| PGSSLROOTCERT | `/etc/ssl/certs/postgresql-server-ca.pem` | The trusted certificate |

# Chapter 4: A Dedicated Access Rule and Enabling Login

`pg_hba.conf` still has a broad rule covering all IPv4 addresses. Rather than simply making `wazuh_collector` able to log in, we first limit its sources with a dedicated rule and then enable it.

## 4.1 Checking the Current Rules and Their Scope

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
runuser -u postgres -- psql -X -d postgres -P pager=off -c "
SELECT
    line_number,
    type,
    database,
    user_name,
    address,
    auth_method,
    error
FROM pg_hba_file_rules
ORDER BY line_number;
"
'
```

```bash
pct exec 109 -- bash -c '
echo "===== HBA NETWORK MASKS ====="
runuser -u postgres -- psql -X -d postgres -P pager=off -c "
SELECT
    line_number,
    type,
    database,
    user_name,
    address,
    netmask,
    auth_method,
    error
FROM pg_hba_file_rules
WHERE type = '\''host'\''
ORDER BY line_number;
"

echo
echo "===== CURRENT HBA FILE ====="
nl -ba /etc/postgresql/17/main/pg_hba.conf
'
```

| Line | Rule | Scope |
|---:|---|---|
| 8 | `0.0.0.0/24` (md5) | `0.0.0.0`–`0.0.0.255` |
| 11 | `0.0.0.0/0` (md5) | All IPv4 addresses |

To protect existing applications, these rules are not changed here. Instead, add rules dedicated to `wazuh_collector` before the existing rules (at the top of the file). `pg_hba.conf` is evaluated from the top, and the first matching rule is used.

Check the file permissions and related settings.

```bash
pct exec 109 -- bash -c '
echo "===== HBA FILE ====="
stat -c "%U:%G %a %n" /etc/postgresql/17/main/pg_hba.conf

echo
echo "===== POSTGRESQL CONFIGURATION ====="
runuser -u postgres -- psql -X -d postgres -P pager=off -c "
SHOW hba_file;
SHOW config_file;
SHOW ssl;
SHOW password_encryption;
"

echo
echo "===== INCLUDE DIRECTIVES ====="
grep -nE "^[[:space:]]*include" \
  /etc/postgresql/17/main/pg_hba.conf || true
'
```

| Item | State at build time |
|---|---|
| `pg_hba.conf` | `postgres:postgres 640` |
| SSL | `on` |
| Password encryption | `scram-sha-256` |
| include directives | None |

## 4.2 Backing Up pg_hba.conf

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
set -e

FILE=/etc/postgresql/17/main/pg_hba.conf
BACKUP="${FILE}.backup-wazuh-$(date +%Y%m%d-%H%M%S)"

cp -a "$FILE" "$BACKUP"

echo "===== BACKUP CREATED ====="
stat -c "%U:%G %a %s %n" "$BACKUP"

echo
echo "===== SHA256 ====="
sha256sum "$FILE" "$BACKUP"
'
```

Confirm that the SHA-256 of the original file and the backup match.

## 4.3 Adding the Dedicated Rules

Add rules dedicated to `wazuh_collector` at the top of `pg_hba.conf`.

| Rule | Meaning |
|---|---|
| `local ... reject` | Reject connections from the Unix socket |
| `hostssl ... 192.168.0.220/32 scram-sha-256` | Allow only TLS connections from the Wazuh Manager, with SCRAM authentication |
| `host ... 0.0.0.0/0 reject` | Reject connections from any other IPv4 address |
| `host ... ::/0 reject` | Reject connections from IPv6 |

Rules for other users are not changed. Do not reload yet at this stage.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
set -e

python3 - <<'"'"'PY'"'"'
from pathlib import Path

p = Path("/etc/postgresql/17/main/pg_hba.conf")
s = p.read_text()

marker = "# BEGIN WAZUH COLLECTOR ACCESS"

if marker in s:
    raise SystemExit("ERROR: Wazuh rules already exist; no changes made.")

rules = """# BEGIN WAZUH COLLECTOR ACCESS
local   all                 wazuh_collector                         reject
hostssl security_workbench  wazuh_collector  192.168.0.220/32        scram-sha-256
host    all                 wazuh_collector  0.0.0.0/0               reject
host    all                 wazuh_collector  ::/0                    reject
# END WAZUH COLLECTOR ACCESS

"""

p.write_text(rules + s)
PY

echo "===== NEW HBA RULES ====="
sed -n "1,12p" /etc/postgresql/17/main/pg_hba.conf

echo
echo "===== FILE PERMISSIONS ====="
stat -c "%U:%G %a %n" /etc/postgresql/17/main/pg_hba.conf
'
```

Also confirm that the file's owner and permissions remain `postgres:postgres 640`.

## 4.4 Validating the Syntax and Reloading

Validate the added rules with PostgreSQL's own parser.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
runuser -u postgres -- psql -X -d postgres -P pager=off -c "
SELECT
    line_number,
    type,
    database,
    user_name,
    address,
    auth_method,
    error
FROM pg_hba_file_rules
WHERE line_number <= 10
ORDER BY line_number;
"

echo
echo "===== HBA PARSER ERRORS ====="
runuser -u postgres -- psql -X -d postgres -Atc "
SELECT count(*)
FROM pg_hba_file_rules
WHERE error IS NOT NULL;
"
'
```

If the four added rules are recognized and there are `0` syntax errors, reload the configuration. This is not a restart, so existing connections are not dropped.

```bash
pct exec 109 -- bash -c '
runuser -u postgres -- psql -X -d postgres -c "
SELECT pg_reload_conf();
"

echo
echo "===== POSTGRESQL SERVICE STATUS ====="
systemctl is-active postgresql
'
```

If `pg_reload_conf` is `t` and the service is `active`, the rules limiting the sources are in effect.

## 4.5 Enabling Login

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
set -e

runuser -u postgres -- psql -X -d security_workbench -c "
ALTER ROLE wazuh_collector LOGIN;
"

echo
echo "===== ROLE SECURITY CHECK ====="

runuser -u postgres -- psql -X -d security_workbench -P pager=off -c "
SELECT
    rolname,
    rolcanlogin,
    rolsuper,
    rolcreatedb,
    rolcreaterole,
    rolreplication,
    rolbypassrls
FROM pg_roles
WHERE rolname = '\''wazuh_collector'\'';
"
'
```

If only `rolcanlogin` is `t` and everything else is `f`, login is enabled with least privilege.

## 4.6 Checking Reachability Without a Password

Connect without giving a password and check that the connection passes TLS verification and the access rules and gets as far as the password authentication stage.

**Run on: the Proxmox host (root@pve)**

```bash
qm guest exec 220 -- bash -c '
export PGHOST=postgresql.neomedia.mydns.jp
export PGHOSTADDR=192.168.0.151
export PGPORT=5432
export PGDATABASE=security_workbench
export PGUSER=wazuh_collector
export PGSSLMODE=verify-full
export PGSSLROOTCERT=/etc/ssl/certs/postgresql-server-ca.pem

echo "===== TLS VERIFIED CONNECTION TEST ====="

psql -X -w -c "SELECT 1;" 2>&1 || true
'
```

If `no password supplied` is shown as below, it is as expected.

```text
connection to server at "192.168.0.151", port 5432 failed:
fe_sendauth: no password supplied
```

There is no certificate error and no `no pg_hba.conf entry`, so TLS verification and the source restriction are working correctly.

## 4.7 TLS Connection with the Actual Password

Log in for real without writing the password in command arguments or environment variables.

> Run this command **after logging in to VM 220 (`root@security-core`) directly**, using the Proxmox VM console or SSH. `psql` is installed only on VM 220, so running it on the Proxmox host gives `psql: command not found`.

**Run on: security-core VM 220 (root)**

```bash
export PGHOST=postgresql.neomedia.mydns.jp
export PGHOSTADDR=192.168.0.151
export PGPORT=5432
export PGDATABASE=security_workbench
export PGUSER=wazuh_collector
export PGSSLMODE=verify-full
export PGSSLROOTCERT=/etc/ssl/certs/postgresql-server-ca.pem

psql -X -W -v ON_ERROR_STOP=1 -c "
SELECT
    current_user,
    current_database(),
    s.ssl,
    s.version,
    s.cipher
FROM pg_stat_ssl s
WHERE s.pid = pg_backend_pid();
"
```

When `Password:` appears, enter the `wazuh_collector` password set in 1.5 (the input is not shown).

| Item | Expected value |
|---|---|
| current_user | `wazuh_collector` |
| current_database | `security_workbench` |
| ssl | `t` |
| version | `TLSv1.3` |

Example output:

```text
 wazuh_collector | security_workbench | t   | TLSv1.3 | TLS_AES_256_GCM_SHA384
```

An encrypted connection from VM 220 to LXC 109, with the certificate and source verified, is now established.

# Chapter 5: Examining the Alert Structure and Creating the Storage Table

## 5.1 Checking the Structure of the Alert File

Examine which fields Wazuh's alert file `alerts.json` contains.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import json
from pathlib import Path

p = Path("/var/ossec/logs/alerts/alerts.json")
print("FILE_EXISTS:", p.is_file())

if not p.is_file():
    raise SystemExit("alerts.json not found")

print("FILE_SIZE:", p.stat().st_size)

lines = p.read_text(errors="replace").splitlines()
valid = []

for line in lines[-100:]:
    try:
        obj = json.loads(line)
        valid.append(obj)
    except (json.JSONDecodeError, ValueError):
        continue

print("VALID_RECENT_ALERTS:", len(valid))

for i, obj in enumerate(valid[-3:], 1):
    print(f"\n===== ALERT {i} =====")
    print("TOP_LEVEL_KEYS:", sorted(obj.keys()))

    for key in ("rule", "agent", "manager", "data", "decoder", "location"):
        value = obj.get(key)
        if isinstance(value, dict):
            print(f"{key.upper()}_KEYS:", sorted(value.keys()))
        elif value is not None:
            print(f"{key.upper()}_TYPE:", type(value).__name__)

    print("ID:", obj.get("id"))
    print("TIMESTAMP:", obj.get("timestamp"))

    rule = obj.get("rule")
    if isinstance(rule, dict):
        print("RULE_ID:", rule.get("id"))
        print("RULE_LEVEL:", rule.get("level"))
        print("RULE_DESCRIPTION:", rule.get("description"))

    agent = obj.get("agent")
    if isinstance(agent, dict):
        print("AGENT_ID:", agent.get("id"))
        print("AGENT_NAME:", agent.get("name"))
PY
```

An alert's `data` can contain information that should not be stored in the DB, such as `pwd` (working directory) and `command` (the executed command). Therefore **we never store `data` or `full_log` in the DB as a whole.**

## 5.2 Checking Which Fields Are Safe to Store

Across all alerts, count how often each field name in `data`, each rule group and each MITRE field name appears. The values themselves are not shown.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import json
from pathlib import Path
from collections import Counter

p = Path("/var/ossec/logs/alerts/alerts.json")
data_keys = Counter()
rule_groups = Counter()
mitre_keys = Counter()
count = 0

with p.open(errors="replace") as f:
    for line in f:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        count += 1
        data = obj.get("data")
        if isinstance(data, dict):
            data_keys.update(data.keys())

        rule = obj.get("rule")
        if isinstance(rule, dict):
            groups = rule.get("groups", [])
            if isinstance(groups, list):
                rule_groups.update(str(x) for x in groups)

            mitre = rule.get("mitre")
            if isinstance(mitre, dict):
                mitre_keys.update(mitre.keys())

print("TOTAL_VALID_ALERTS:", count)
print("\nDATA FIELD NAMES (TOP 40):")
for key, n in data_keys.most_common(40):
    print(f"{key}: {n}")

print("\nRULE GROUPS (TOP 30):")
for key, n in rule_groups.most_common(30):
    print(f"{key}: {n}")

print("\nMITRE FIELD NAMES:")
for key, n in mitre_keys.most_common():
    print(f"{key}: {n}")
PY
```

At build time, the 1,271 alerts had groups such as authentication failure, brute force, PostgreSQL, SCA and Rootcheck, and the MITRE fields were `id`, `tactic` and `technique`.

From this result, we decided on the following fields to store in the DB.

| Column | Use |
|---|---|
| `event_id` | Unique identifier of the Wazuh event (primary key; prevents duplicate inserts) |
| `event_timestamp` | Time the alert occurred |
| `ingested_at` | Time it was inserted into the DB |
| `rule_id`, `rule_level`, `rule_description` | Detection rule, severity, what was detected |
| `agent_id`, `agent_name` | The agent that detected it |
| `manager_name`, `decoder_name` | Wazuh management information |
| `rule_groups` | Rule groups |
| `srcip`, `srcport` | Source IP and port (only if present) |
| `mitre` | MITRE ATT&CK information |

## 5.3 Creating the Storage Table

Allow `wazuh_collector` **only INSERT**, so that it cannot read, change or delete.

> **Note:** If environment variables such as `PGHOST` or `PGSSLMODE` remain in the Proxmox host's shell, `psql` run through `pct exec` inherits them and fails with `root certificate file "/etc/ssl/certs/postgresql-server-ca.pem" does not exist` (the certificate exists only on VM 220). The following command removes these variables with `env -u`, so it works either way. The SQL is inside a transaction, so nothing is left half-created if it fails.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- runuser -u postgres -- env -u PGHOST -u PGHOSTADDR -u PGPORT -u PGDATABASE -u PGUSER -u PGSSLMODE -u PGSSLROOTCERT psql -X -v ON_ERROR_STOP=1 -d security_workbench <<'SQL'
BEGIN;

CREATE TABLE incident.alert_events (
    event_id         text PRIMARY KEY,
    event_timestamp  timestamptz NOT NULL,
    ingested_at      timestamptz NOT NULL DEFAULT now(),
    rule_id          integer NOT NULL,
    rule_level       smallint NOT NULL CHECK (rule_level BETWEEN 0 AND 16),
    rule_description text,
    agent_id         text,
    agent_name       text,
    manager_name     text,
    decoder_name     text,
    rule_groups      text[] NOT NULL DEFAULT ARRAY[]::text[],
    srcip            inet,
    srcport          integer CHECK (srcport BETWEEN 0 AND 65535),
    mitre            jsonb NOT NULL DEFAULT '{}'::jsonb
                     CHECK (jsonb_typeof(mitre) = 'object')
);

CREATE INDEX idx_alert_events_timestamp
    ON incident.alert_events (event_timestamp DESC);

CREATE INDEX idx_alert_events_level
    ON incident.alert_events (rule_level DESC);

CREATE INDEX idx_alert_events_rule
    ON incident.alert_events (rule_id);

CREATE INDEX idx_alert_events_srcip
    ON incident.alert_events (srcip);

REVOKE ALL ON incident.alert_events FROM PUBLIC;
GRANT INSERT ON incident.alert_events TO wazuh_collector;

COMMIT;

SELECT
    has_table_privilege('wazuh_collector',
                        'incident.alert_events', 'INSERT') AS can_insert,
    has_table_privilege('wazuh_collector',
                        'incident.alert_events', 'SELECT') AS can_select,
    has_table_privilege('wazuh_collector',
                        'incident.alert_events', 'UPDATE') AS can_update,
    has_table_privilege('wazuh_collector',
                        'incident.alert_events', 'DELETE') AS can_delete;
SQL
```

Example output:

```text
 can_insert | can_select | can_update | can_delete 
------------+------------+------------+------------
 t          | f          | f          | f
(1 row)
```

`wazuh_collector` can only add alerts; it cannot read, change or delete existing events.

# Chapter 6: Checking the Collector's Runtime Environment

So that it does not affect the Wazuh Manager's operation, the Collector is built as a program that only reads `alerts.json`.

> Run the commands in this chapter **after logging in to VM 220 (`root@security-core`)**. `alerts.json` is inside VM 220, so running them on the Proxmox host gives `No such file or directory`. VM 220 has no serial port configured, so you cannot log in with `qm terminal 220`. Use SSH or the "Console" in the Proxmox web UI.

## 6.1 Checking the Alert File Permissions

**Run on: security-core VM 220 (root)**

```bash
echo "===== ALERT FILE ====="
stat -c 'Owner=%U Group=%G Mode=%a Size=%s Path=%n' \
  /var/ossec/logs/alerts/alerts.json

echo
echo "===== WAZUH USER ====="
id wazuh

echo
echo "===== ALERT DIRECTORY ====="
stat -c 'Owner=%U Group=%G Mode=%a Path=%n' \
  /var/ossec/logs \
  /var/ossec/logs/alerts

echo
echo "===== LOG ROTATION CONFIG ====="
grep -R -n -E 'alerts\.json|/var/ossec/logs' \
  /etc/logrotate.d 2>/dev/null || true
```

| Item | State at build time |
|---|---|
| `alerts.json` | Owner `wazuh`, permissions `640` |
| `/var/ossec/logs` | `770` |
| `/var/ossec/logs/alerts` | `750` |
| logrotate settings | None (Wazuh rotates the files itself) |

## 6.2 Checking the Alert Output Settings

**Run on: security-core VM 220 (root)**

```bash
echo "===== WAZUH ALERT CONFIG ====="
grep -n -A 12 -B 4 -E 'alerts_log|log_alert_level|jsonout_output' \
  /var/ossec/etc/ossec.conf

echo
echo "===== ALERT FILES ====="
find /var/ossec/logs/alerts -maxdepth 1 -type f \
  -printf '%f | %s bytes | %TY-%Tm-%Td %TH:%TM\n' \
  | sort

echo
echo "===== WAZUH MANAGER STATUS ====="
systemctl is-active wazuh-manager
```

| Setting | Value at build time | Meaning |
|---|---|---|
| `jsonout_output` | `yes` | JSON alert output is enabled |
| `alerts_log` | `yes` | A text alert log is also written |
| `logall`, `logall_json` | `no` | Saving all events is disabled |
| `log_alert_level` | `3` | Level 3 and above are recorded as alerts |

The Collector does not change Wazuh's settings; it only reads `alerts.json`.

## 6.3 Checking the Rotation Method

**Run on: security-core VM 220 (root)**

```bash
echo "===== WAZUH LOG ROTATION SETTINGS ====="
grep -R -n -E 'max_output_size|rotate|alerts\.json|log_size' \
  /var/ossec/etc /etc/logrotate.conf /etc/logrotate.d \
  2>/dev/null | head -80

echo
echo "===== SYSTEMD VERSION ====="
systemd --version | head -1

echo
echo "===== ALERT FILE DETAILS ====="
ls -li /var/ossec/logs/alerts/alerts.json
```

The Wazuh Manager switches alert files with its own rotation function (`analysisd.min_rotate_interval=600`, `monitord.rotate_log=1`). The Collector therefore tracks not just the file name but **the inode (the number of the actual file) and the read position**. Re-reading after rotation is combined with de-duplication by the DB's primary key.

## 6.4 Installing the PostgreSQL Driver

**Run on: security-core VM 220 (root)**

```bash
echo "===== PYTHON VERSION ====="
python3 --version

echo
echo "===== POSTGRESQL PYTHON DRIVERS ====="
python3 - <<'PY'
for name in ("psycopg", "psycopg2"):
    try:
        mod = __import__(name)
        print(name, "INSTALLED", getattr(mod, "__version__", "version unknown"))
    except ImportError:
        print(name, "NOT INSTALLED")
PY

echo
echo "===== APT PACKAGE CANDIDATES ====="
apt-cache policy python3-psycopg python3-psycopg2
```

At build time, Python was 3.12.3 and no driver was installed. We use **psycopg 3**, which can be managed with the standard OS packages.

```bash
apt-get install -y python3-psycopg
```

```bash
python3 -c 'import psycopg; print("psycopg:", psycopg.__version__)'
```

If something like `psycopg: 3.1.17` is shown, it has succeeded.

## 6.5 Checking Whether ACLs Can Be Used

The Collector runs as a dedicated user separate from Wazuh. Adding the dedicated user to the `wazuh` group would also let it write to the log directory, so we check whether we can use **an ACL that allows only reading**. At this point, neither ACLs nor users are changed.

**Run on: security-core VM 220 (root)**

```bash
echo "===== ACL UTILITIES ====="
command -v getfacl || true
command -v setfacl || true

echo
echo "===== FILESYSTEM ====="
findmnt -T /var/ossec/logs/alerts/alerts.json \
  -o TARGET,FSTYPE,OPTIONS

echo
echo "===== CURRENT ACL ====="
if command -v getfacl >/dev/null 2>&1; then
    getfacl -p /var/ossec/logs
    getfacl -p /var/ossec/logs/alerts
    getfacl -p /var/ossec/logs/alerts/alerts.json
fi
```

The file system is `ext4`, so ACLs can be used. At build time, `getfacl` and `setfacl` were not installed, so install only the tools. The permissions of existing files are not changed.

```bash
apt-get install -y acl
```

```bash
getfacl -p /var/ossec/logs/alerts/alerts.json
```

# Chapter 7: A Dedicated User and Read-Only Permissions

## 7.1 Checking the Current Permissions

**Run on: security-core VM 220 (root)**

```bash
echo "===== ALERT FILE ACL ====="
getfacl -p /var/ossec/logs/alerts/alerts.json

echo
echo "===== PARENT DIRECTORY ACL ====="
getfacl -p /var/ossec/logs

echo
echo "===== ALERT DIRECTORY ACL ====="
getfacl -p /var/ossec/logs/alerts
```

Without changing the existing Wazuh owners, groups or permissions, give the dedicated user only the permissions it needs, through ACLs.

## 7.2 Creating the Dedicated Service User

Create a system user with no login shell and no home directory.

**Run on: security-core VM 220 (root)**

```bash
useradd --system \
  --no-create-home \
  --home-dir /nonexistent \
  --shell /usr/sbin/nologin \
  wazuh-collector
```

```bash
echo "===== USER ====="
getent passwd wazuh-collector

echo
echo "===== GROUPS ====="
id wazuh-collector
```

Example output:

```text
===== USER =====
wazuh-collector:x:996:987::/nonexistent:/usr/sbin/nologin

===== GROUPS =====
uid=996(wazuh-collector) gid=987(wazuh-collector) groups=987(wazuh-collector)
```

Confirm that it is not in the `wazuh` group.

## 7.3 Setting Read-Only ACLs

**Run on: security-core VM 220 (root)**

```bash
setfacl -m u:wazuh-collector:--x /var/ossec/logs
setfacl -m u:wazuh-collector:--x /var/ossec/logs/alerts
setfacl -m u:wazuh-collector:r-- /var/ossec/logs/alerts/alerts.json
setfacl -m d:u:wazuh-collector:r-x /var/ossec/logs/alerts
```

| Target | Permission given to the dedicated user |
|---|---|
| `/var/ossec/logs` | Traverse only (`--x`) |
| `/var/ossec/logs/alerts` | Traverse only (`--x`) |
| `alerts.json` | Read only (`r--`) |
| Files created under `alerts` in the future | Read (default ACL; the effective permission is the intersection with the normal permissions at file creation) |

The directory above, `/var/ossec` (`root:wazuh 750`), also needs the traverse permission. Without it, the files below cannot be reached even with a read ACL, and you get `Permission denied`.

```bash
setfacl -m u:wazuh-collector:--x /var/ossec
```

## 7.4 Confirming That Access Is Read-Only

**Run on: security-core VM 220 (root)**

```bash
getfacl -p /var/ossec/logs/alerts/alerts.json
getfacl -p /var/ossec/logs/alerts
```

```bash
echo "===== READ TEST ====="
runuser -u wazuh-collector -- test -r /var/ossec/logs/alerts/alerts.json \
  && echo "PASS: readable" || echo "FAIL: not readable"

echo
echo "===== WRITE TEST ====="
runuser -u wazuh-collector -- test -w /var/ossec/logs/alerts/alerts.json \
  && echo "FAIL: writable" || echo "PASS: not writable"

echo
echo "===== ACTUAL READ TEST ====="
runuser -u wazuh-collector -- head -c 1 /var/ossec/logs/alerts/alerts.json >/dev/null \
  && echo "PASS: file content readable" || echo "FAIL: cannot read file"
```

If all three items are `PASS`, the dedicated user can read the alert file but cannot change it.

Also check every level along the path.

```bash
echo "===== COLLECTOR ACCOUNT ====="
id wazuh-collector

echo
echo "===== DIRECTORY ACL ====="
getfacl -p /var/ossec
getfacl -p /var/ossec/logs
getfacl -p /var/ossec/logs/alerts

echo
echo "===== PATH ACCESS ====="
namei -l /var/ossec/logs/alerts/alerts.json
```

## 7.5 Checking the Structure of the Alert Files

Check how Wazuh actually manages the alert files.

**Run on: security-core VM 220 (root)**

```bash
echo "===== ALERTS CONFIGURATION ====="
grep -n -A25 -B5 '<alerts>' /var/ossec/etc/ossec.conf

echo
echo "===== ROTATION OPTIONS ====="
grep -nE 'rotate_interval|max_output_size' \
  /var/ossec/etc/ossec.conf
```

`<alerts>` contained only `log_alert_level` (3) and `email_alert_level` (12); `rotate_interval` and `max_output_size` were not set (disabled by default).

> `monitord.rotate_log` and `monitord.size_rotate` in `internal_options.conf` are settings for Wazuh's own internal logs, not for rotating `alerts.json`.

```bash
echo "===== ALERT DIRECTORY TREE ====="
find /var/ossec/logs/alerts -maxdepth 5 \
  -printf '%y inode=%i links=%n size=%s %p\n' | sort

echo
echo "===== ALERTS.JSON LINK DETAILS ====="
stat -c 'inode=%i links=%h size=%s type=%F name=%n' \
  /var/ossec/logs/alerts/alerts.json

echo
echo "===== FILES SHARING ALERTS.JSON INODE ====="
find /var/ossec/logs/alerts -xdev -inum \
  "$(stat -c '%i' /var/ossec/logs/alerts/alerts.json)" \
  -printf '%i %n %s %p\n'
```

Example output:

```text
5409146 2 1984636 /var/ossec/logs/alerts/2026/Nov/ossec-alerts-18.json
5409146 2 1984636 /var/ossec/logs/alerts/alerts.json
```

`alerts.json` is **a hard link sharing the same inode** with the per-day file (`year/month/ossec-alerts-day.json`). When the date changes, a new day's file is created and the previous day's file is compressed (`.json.gz`). The Collector detects the date change from the change of `alerts.json`'s inode.

# Chapter 8: Creating the Collector

## 8.1 Creating the Credential Directory

**Run on: security-core VM 220 (root)**

```bash
install -d \
  -o wazuh-collector \
  -g wazuh-collector \
  -m 700 \
  /etc/wazuh-collector

stat -c '%U:%G %a %n' /etc/wazuh-collector
```

If `wazuh-collector:wazuh-collector 700 /etc/wazuh-collector` is shown, other users and services cannot access it.

Check the connection settings (the password is not shown).

```bash
echo "===== DATABASE CONNECTION SETTINGS ====="
printf '%s\n' \
  'Host name: postgresql.neomedia.mydns.jp' \
  'Host address: 192.168.0.151' \
  'Port: 5432' \
  'Database: security_workbench' \
  'User: wazuh_collector' \
  'SSL mode: verify-full' \
  'CA certificate: /etc/ssl/certs/postgresql-server-ca.pem'

echo
echo "===== CA CERTIFICATE ====="
stat -c '%U:%G %a %s bytes %n' \
  /etc/ssl/certs/postgresql-server-ca.pem

echo
echo "===== COLLECTOR DIRECTORY ====="
stat -c '%U:%G %a %n' /etc/wazuh-collector
```

## 8.2 Creating the Password File (.pgpass)

Without showing the password on screen, save it in `.pgpass`, readable only by the dedicated user.

**Run on: security-core VM 220 (root)**

```bash
sudo -u wazuh-collector bash -c '
set -eu
umask 077
read -rsp "PostgreSQL wazuh_collector password: " PGPASS
echo
read -rsp "Confirm password: " PGPASS2
echo

if [ "$PGPASS" != "$PGPASS2" ]; then
    echo "ERROR: passwords do not match"
    exit 1
fi

case "$PGPASS" in
  *:*)
    echo "ERROR: password contains a colon; stop and use an escaped .pgpass entry"
    exit 1
    ;;
esac

printf "%s\n" "postgresql.neomedia.mydns.jp:5432:security_workbench:wazuh_collector:$PGPASS" \
  > /etc/wazuh-collector/.pgpass

unset PGPASS PGPASS2
chmod 600 /etc/wazuh-collector/.pgpass
'
```

Enter the password set in 1.5 twice. If the password contains a colon (`:`), creation is aborted for safety.

```bash
stat -c '%U:%G %a %s bytes %n' \
  /etc/wazuh-collector/.pgpass
```

Confirm that it is `wazuh-collector:wazuh-collector 600`. **Do not display the contents of the file.**

## 8.3 Connection Test as the Dedicated User

Connect with `verify-full` using `.pgpass`. No password prompt appears.

**Run on: security-core VM 220 (root)**

```bash
sudo -u wazuh-collector env \
  PGHOST=postgresql.neomedia.mydns.jp \
  PGHOSTADDR=192.168.0.151 \
  PGPORT=5432 \
  PGDATABASE=security_workbench \
  PGUSER=wazuh_collector \
  PGSSLMODE=verify-full \
  PGSSLROOTCERT=/etc/ssl/certs/postgresql-server-ca.pem \
  PGPASSFILE=/etc/wazuh-collector/.pgpass \
  psql -X -w -c '\conninfo' \
        -c 'SELECT current_user, current_database();'
```

It has succeeded if it connects to port 5432 on `192.168.0.151` with TLS 1.3 and shows `current_user` as `wazuh_collector` and `current_database` as `security_workbench`.

## 8.4 Creating the State Directory and Program Directory

Create a state directory that stores how far the alert file has been read (inode and read position).

**Run on: security-core VM 220 (root)**

```bash
echo "===== ALERT DIRECTORY FILES ====="
find /var/ossec/logs/alerts \
  -maxdepth 1 -type f \
  -printf '%f | inode=%i | size=%s | modified=%TY-%Tm-%Td %TH:%TM:%TS\n' \
  | sort

echo
echo "===== ALERT FILE STATUS ====="
stat -c 'inode=%i size=%s owner=%U:%G mode=%a modified=%y' \
  /var/ossec/logs/alerts/alerts.json

echo
echo "===== WAZUH ROTATION SETTINGS ====="
grep -E '^(analysisd\.min_rotate_interval|monitord\.rotate_log|monitord\.size_rotate)=' \
  /var/ossec/etc/internal_options.conf

echo
echo "===== ALERT OUTPUT SETTINGS ====="
grep -nE 'jsonout_output|alerts_log|logall_json|log_alert_level' \
  /var/ossec/etc/ossec.conf
```

```bash
install -d \
  -o wazuh-collector \
  -g wazuh-collector \
  -m 700 \
  /var/lib/wazuh-collector

stat -c '%U:%G %a %n' /var/lib/wazuh-collector
```

The program is owned by root so that the user it runs as cannot change it.

```bash
install -d \
  -o root \
  -g root \
  -m 755 \
  /usr/local/lib/wazuh-collector

stat -c '%U:%G %a %n' /usr/local/lib/wazuh-collector
```

| Directory | Owner / permissions | Use |
|---|---|---|
| `/etc/wazuh-collector` | `wazuh-collector` 700 | Credentials (`.pgpass`) |
| `/var/lib/wazuh-collector` | `wazuh-collector` 700 | State file (`state.json`) |
| `/usr/local/lib/wazuh-collector` | `root` 755 | The program itself |

## 8.5 Creating the Collector

The key design points of the Collector are as follows.

- Monitor only Wazuh's `alerts.json`.
- Store only permitted fields in the DB (do not store `full_log`, arbitrary `data`, commands, passwords, etc.).
- Validate values before storing them (event ID, rule ID, level, time, IP address, port number).
- De-duplicate by the DB's primary key (`event_id`) (`ON CONFLICT DO NOTHING`).
- Save the read position only after the DB insert succeeds.
- Detect file switches by inode changes and read the new file from the beginning.
- On first startup, do not insert past alerts; start reading from the end of the file.

**Run on: security-core VM 220 (root)**

```bash
cat > /usr/local/lib/wazuh-collector/collector.py <<'PY'
#!/usr/bin/python3

import os
import sys
import json
import time
import stat
import logging
import tempfile
import ipaddress
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb


ALERT_FILE = Path("/var/ossec/logs/alerts/alerts.json")
ALERT_DIR = ALERT_FILE.parent
STATE_FILE = Path("/var/lib/wazuh-collector/state.json")
PGPASS_FILE = "/etc/wazuh-collector/.pgpass"

POLL_INTERVAL = 1.0

DB_CONFIG = {
    "host": "postgresql.neomedia.mydns.jp",
    "hostaddr": "192.168.0.151",
    "port": 5432,
    "dbname": "security_workbench",
    "user": "wazuh_collector",
    "sslmode": "verify-full",
    "sslrootcert": "/etc/ssl/certs/postgresql-server-ca.pem",
    "passfile": PGPASS_FILE,
    "connect_timeout": 10,
    "application_name": "wazuh-alert-collector",
}

INSERT_SQL = """
INSERT INTO incident.alert_events (
    event_id,
    event_timestamp,
    rule_id,
    rule_level,
    rule_description,
    agent_id,
    agent_name,
    manager_name,
    decoder_name,
    rule_groups,
    srcip,
    srcport,
    mitre
)
VALUES (
    %(event_id)s,
    %(event_timestamp)s,
    %(rule_id)s,
    %(rule_level)s,
    %(rule_description)s,
    %(agent_id)s,
    %(agent_name)s,
    %(manager_name)s,
    %(decoder_name)s,
    %(rule_groups)s,
    %(srcip)s,
    %(srcport)s,
    %(mitre)s
)
ON CONFLICT (event_id) DO NOTHING
"""

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)


def parse_timestamp(value):
    if not isinstance(value, str):
        raise ValueError("invalid timestamp")

    result = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )

    if result.tzinfo is None:
        raise ValueError("timestamp has no timezone")

    return result


def safe_integer(value, minimum, maximum):
    try:
        number = int(value)
        if minimum <= number <= maximum:
            return number
    except (TypeError, ValueError):
        pass
    return None


def safe_ip(value):
    if not isinstance(value, str):
        return None

    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def safe_text(value, limit=4096):
    if isinstance(value, str):
        return value[:limit]
    return None


def extract_event(alert):
    if not isinstance(alert, dict):
        return None

    rule = alert.get("rule")
    agent = alert.get("agent")
    manager = alert.get("manager")
    decoder = alert.get("decoder")
    data = alert.get("data")

    if not all(isinstance(x, dict) for x in
               (rule, agent, manager, decoder)):
        return None

    event_id = safe_text(alert.get("id"), 128)
    rule_id = safe_integer(rule.get("id"), 0, 2147483647)
    rule_level = safe_integer(rule.get("level"), 0, 16)

    if not event_id or rule_id is None or rule_level is None:
        return None

    try:
        event_timestamp = parse_timestamp(alert.get("timestamp"))
    except (ValueError, TypeError):
        return None

    groups = rule.get("groups", [])
    if not isinstance(groups, list):
        groups = []

    groups = [
        item[:256]
        for item in groups
        if isinstance(item, str)
    ]

    mitre_source = rule.get("mitre", {})
    mitre = {}

    if isinstance(mitre_source, dict):
        for key in ("id", "tactic", "technique"):
            value = mitre_source.get(key)
            if isinstance(value, (str, int, list)):
                mitre[key] = value

    srcip = None
    srcport = None

    if isinstance(data, dict):
        srcip = safe_ip(data.get("srcip"))
        srcport = safe_integer(data.get("srcport"), 0, 65535)

    return {
        "event_id": event_id,
        "event_timestamp": event_timestamp,
        "rule_id": rule_id,
        "rule_level": rule_level,
        "rule_description": safe_text(rule.get("description")),
        "agent_id": safe_text(agent.get("id"), 128),
        "agent_name": safe_text(agent.get("name"), 256),
        "manager_name": safe_text(manager.get("name"), 256),
        "decoder_name": safe_text(decoder.get("name"), 256),
        "rule_groups": groups,
        "srcip": srcip,
        "srcport": srcport,
        "mitre": Jsonb(mitre),
    }


def save_state(inode, offset):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    fd, temporary = tempfile.mkstemp(
        prefix=".state-",
        dir=str(STATE_FILE.parent),
    )

    try:
        os.fchmod(fd, 0o600)

        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(
                {"inode": inode, "offset": offset},
                output,
            )
            output.flush()
            os.fsync(output.fileno())

        os.replace(temporary, STATE_FILE)

        directory_fd = os.open(STATE_FILE.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)

    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def load_state():
    try:
        with STATE_FILE.open("r", encoding="utf-8") as source:
            state = json.load(source)

        inode = int(state["inode"])
        offset = int(state["offset"])

        if inode <= 0 or offset < 0:
            raise ValueError("invalid state")

        return inode, offset

    except FileNotFoundError:
        return None

    except Exception as error:
        raise RuntimeError("collector state is invalid") from error


def find_inode_file(inode):
    for entry in os.scandir(ALERT_DIR):
        try:
            if entry.is_file(follow_symlinks=False):
                if entry.inode() == inode:
                    return Path(entry.path)
        except OSError:
            continue

    return None


def open_initial_file(state):
    current_stat = ALERT_FILE.stat()

    if state is None:
        handle = ALERT_FILE.open("rb")
        handle.seek(0, os.SEEK_END)
        offset = handle.tell()

        save_state(current_stat.st_ino, offset)

        logging.info("Initial start at current end of alerts.json")
        return handle, current_stat.st_ino

    old_inode, old_offset = state
    old_path = find_inode_file(old_inode)

    if old_path is not None:
        handle = old_path.open("rb")
        handle.seek(min(old_offset, os.fstat(handle.fileno()).st_size))
        logging.info("Resuming previous alert file")
        return handle, old_inode

    handle = ALERT_FILE.open("rb")

    if current_stat.st_ino == old_inode:
        handle.seek(min(old_offset, current_stat.st_size))
    else:
        handle.seek(0)
        logging.warning(
            "Previous rotated file not found; replaying current file"
        )

    return handle, current_stat.st_ino


def process_line(connection, line):
    try:
        alert = json.loads(line)
    except (json.JSONDecodeError, UnicodeDecodeError):
        logging.warning("Invalid JSON alert line skipped")
        return

    event = extract_event(alert)

    if event is None:
        logging.warning("Alert rejected by field validation")
        return

    with connection.transaction():
        connection.execute(INSERT_SQL, event)


def run():
    logging.info("Wazuh alert collector starting")

    state = load_state()
    handle, active_inode = open_initial_file(state)

    connection = None

    try:
        while True:
            if connection is None or connection.closed:
                try:
                    connection = psycopg.connect(**DB_CONFIG)
                    logging.info("PostgreSQL connection established")
                except Exception as error:
                    logging.error(
                        "PostgreSQL connection failed: %s",
                        type(error).__name__,
                    )
                    time.sleep(5)
                    continue

            line_start = handle.tell()
            line = handle.readline()

            if line:
                if not line.endswith(b"\n"):
                    handle.seek(line_start)
                    time.sleep(POLL_INTERVAL)
                    continue

                try:
                    process_line(connection, line)
                    save_state(active_inode, handle.tell())
                except Exception as error:
                    handle.seek(line_start)
                    logging.error(
                        "Alert processing failed: %s",
                        type(error).__name__,
                    )

                    try:
                        connection.close()
                    except Exception:
                        pass

                    connection = None
                    time.sleep(5)

                continue

            # At EOF: check whether Wazuh rotated alerts.json.
            try:
                current_stat = ALERT_FILE.stat()
            except FileNotFoundError:
                time.sleep(POLL_INTERVAL)
                continue

            if current_stat.st_ino != active_inode:
                handle.close()
                handle = ALERT_FILE.open("rb")
                active_inode = current_stat.st_ino

                save_state(active_inode, 0)
                logging.info("Switched to new alerts.json inode")

            time.sleep(POLL_INTERVAL)

    finally:
        handle.close()

        if connection is not None:
            connection.close()


if __name__ == "__main__":
    run()
PY

chown root:root /usr/local/lib/wazuh-collector/collector.py
chmod 755 /usr/local/lib/wazuh-collector/collector.py
```

> This program is strengthened in Part 4 with input validation, rotation handling and so on. The full text shown here is the version as of Part 3 (first version).

## 8.6 Checking the Created File

Pasting a long command can break the terminal display. Check that the file was created correctly to the end.

**Run on: security-core VM 220 (root)**

```bash
echo "===== FILE STATUS ====="
stat -c '%U:%G %a %s bytes %n' \
  /usr/local/lib/wazuh-collector/collector.py

echo
echo "===== LINE COUNT ====="
wc -l /usr/local/lib/wazuh-collector/collector.py

echo
echo "===== LAST 25 LINES ====="
tail -n 25 /usr/local/lib/wazuh-collector/collector.py

echo
echo "===== PYTHON SYNTAX CHECK ====="
python3 -m py_compile \
  /usr/local/lib/wazuh-collector/collector.py
```

```bash
echo "===== FUNCTION DEFINITIONS ====="
grep -nE '^(def |if __name__)' \
  /usr/local/lib/wazuh-collector/collector.py

echo
echo "===== UNEXPECTED SHELL COMMAND CHECK ====="
if grep -nE '^(chmod|chown|apt-get|cat >|root@security-core)' \
  /usr/local/lib/wazuh-collector/collector.py; then
    echo "WARNING: unexpected shell text found"
else
    echo "PASS: no obvious shell command contamination"
fi

echo
echo "===== COMPILE CHECK ====="
python3 -m py_compile \
  /usr/local/lib/wazuh-collector/collector.py \
  && echo "PASS"
```

| Item | Expected value |
|---|---|
| Owner / permissions | `root:root 755` |
| Size / lines | 9,487 bytes, 383 lines |
| End of file | `if __name__ == "__main__":` and `run()` |
| Shell commands mixed in | `PASS: no obvious shell command contamination` |
| Syntax | `PASS` |

## 8.7 Testing That Sensitive Information Is Not Stored

Confirm that even if `data` contains `command`, `pwd`, `tty`, `dstuser` and so on, they do not end up in the data inserted into the DB. No DB connection is made.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
import importlib.util

path = "/usr/local/lib/wazuh-collector/collector.py"
spec = importlib.util.spec_from_file_location("collector", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

sample = {
    "id": "1794989242.2755502",
    "timestamp": "2026-11-18T10:30:00.000+0000",
    "agent": {"id": "004", "name": "postgresql"},
    "manager": {"name": "security-core"},
    "decoder": {"name": "postgresql"},
    "rule": {
        "id": "100106",
        "level": 12,
        "description": "PostgreSQL authentication failure test",
        "groups": ["postgresql", "authentication_failed"],
        "mitre": {
            "id": ["T1110"],
            "tactic": ["Credential Access"],
            "technique": ["Brute Force"]
        }
    },
    "data": {
        "srcip": "192.0.2.10",
        "srcport": "54321",
        "command": "SENSITIVE_COMMAND",
        "pwd": "SENSITIVE_PASSWORD",
        "tty": "SENSITIVE_TTY",
        "dstuser": "SENSITIVE_USER"
    },
    "full_log": "SENSITIVE_FULL_LOG"
}

event = module.extract_event(sample)

assert event is not None
assert event["srcip"] == "192.0.2.10"
assert event["srcport"] == 54321

expected = {
    "event_id", "event_timestamp", "rule_id", "rule_level",
    "rule_description", "agent_id", "agent_name", "manager_name",
    "decoder_name", "rule_groups", "srcip", "srcport", "mitre"
}
assert set(event.keys()) == expected

serialized = repr(event)
for forbidden in (
    "SENSITIVE_COMMAND",
    "SENSITIVE_PASSWORD",
    "SENSITIVE_TTY",
    "SENSITIVE_USER",
    "SENSITIVE_FULL_LOG"
):
    assert forbidden not in serialized

assert event["mitre"].obj["id"] == ["T1110"]

print("PASS: allowed fields extracted")
print("PASS: sensitive data excluded")
print("PASS: source IP and port validated")
print("PASS: MITRE fields extracted")
print("PASS: exact database field whitelist")
PY
```

If all five items show `PASS`, only the permitted fields are extracted and sensitive information is excluded.

# Chapter 9: Checking and Fixing the DB Insert

## 9.1 Checking the Table Privileges

Before checking whether the Collector can actually insert into the DB, check the privileges when connected as the dedicated user.

**Run on: security-core VM 220 (root)**

```bash
sudo -u wazuh-collector env \
  PGHOST=postgresql.neomedia.mydns.jp \
  PGHOSTADDR=192.168.0.151 \
  PGPORT=5432 \
  PGDATABASE=security_workbench \
  PGUSER=wazuh_collector \
  PGSSLMODE=verify-full \
  PGSSLROOTCERT=/etc/ssl/certs/postgresql-server-ca.pem \
  PGPASSFILE=/etc/wazuh-collector/.pgpass \
  psql -X -w -c "
SELECT
    current_user,
    current_database(),
    has_schema_privilege(current_user, 'incident', 'USAGE')
        AS schema_usage,
    has_table_privilege(
        current_user,
        'incident.alert_events',
        'INSERT'
    ) AS table_insert,
    has_table_privilege(
        current_user,
        'incident.alert_events',
        'SELECT'
    ) AS table_select;
"
```

Example output:

```text
 wazuh_collector | security_workbench | t            | t            | f
```

| Privilege | Result | Meaning |
|---|---|---|
| USAGE on the `incident` schema | `t` | Allowed |
| INSERT on `alert_events` | `t` | Allowed |
| SELECT on `alert_events` | `f` | Denied (intended least privilege) |

## 9.2 ON CONFLICT and the SELECT Privilege

The INSERT statement in the program from 8.5 ends with `ON CONFLICT (event_id) DO NOTHING` to skip duplicates. In PostgreSQL, however, `ON CONFLICT` checks against existing rows, so **it requires SELECT on the table**. `wazuh_collector` has no SELECT privilege, so as it stands it fails with `permission denied for table alert_events`.

Compare a normal INSERT with an INSERT using `ON CONFLICT`. Both raise an exception deliberately at the end so that the test data is not committed.

**Run on: security-core VM 220 (root)**

Normal INSERT:

```bash
sudo -u wazuh-collector python3 - <<'PY'
import psycopg
import uuid
from datetime import datetime, timezone

import importlib.util

path = "/usr/local/lib/wazuh-collector/collector.py"
spec = importlib.util.spec_from_file_location("collector", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

event_id = "WAZUH-MINIMAL-ROLLBACK-" + uuid.uuid4().hex

try:
    with psycopg.connect(**module.DB_CONFIG) as conn:
        with conn.transaction():
            cursor = conn.execute("""
                INSERT INTO incident.alert_events (
                    event_id,
                    event_timestamp,
                    rule_id,
                    rule_level
                )
                VALUES (%s, %s, %s, %s)
            """, (
                event_id,
                datetime.now(timezone.utc),
                100106,
                12
            ))

            print("INSERT rowcount:", cursor.rowcount)
            raise RuntimeError("INTENTIONAL_ROLLBACK")

except RuntimeError as error:
    if str(error) != "INTENTIONAL_ROLLBACK":
        raise
    print("ROLLBACK: completed")
    print("Test INSERT was not committed")

except Exception as error:
    print("Exception type:", type(error).__name__)
    print("SQLSTATE:", getattr(error, "sqlstate", None))
    print("Message:", str(error))
    diag = getattr(error, "diag", None)
    if diag:
        print("Schema:", getattr(diag, "schema_name", None))
        print("Table:", getattr(diag, "table_name", None))
        print("Column:", getattr(diag, "column_name", None))
PY
```

```text
INSERT rowcount: 1
ROLLBACK: completed
Test INSERT was not committed
```

INSERT with `ON CONFLICT`:

```bash
sudo -u wazuh-collector python3 - <<'PY'
import psycopg
import uuid
from datetime import datetime, timezone

event_id = "WAZUH-CONFLICT-ROLLBACK-" + uuid.uuid4().hex

try:
    with psycopg.connect(
        host="postgresql.neomedia.mydns.jp",
        hostaddr="192.168.0.151",
        port=5432,
        dbname="security_workbench",
        user="wazuh_collector",
        sslmode="verify-full",
        sslrootcert="/etc/ssl/certs/postgresql-server-ca.pem",
        passfile="/etc/wazuh-collector/.pgpass",
    ) as conn:
        with conn.transaction():
            cursor = conn.execute("""
                INSERT INTO incident.alert_events (
                    event_id,
                    event_timestamp,
                    rule_id,
                    rule_level
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
            """, (
                event_id,
                datetime.now(timezone.utc),
                100106,
                12
            ))

            print("INSERT rowcount:", cursor.rowcount)
            raise RuntimeError("INTENTIONAL_ROLLBACK")

except RuntimeError as error:
    if str(error) != "INTENTIONAL_ROLLBACK":
        raise
    print("ROLLBACK: completed")

except Exception as error:
    print("Exception type:", type(error).__name__)
    print("SQLSTATE:", getattr(error, "sqlstate", None))
    print("Message:", str(error))
    diag = getattr(error, "diag", None)
    if diag:
        print("Schema:", getattr(diag, "schema_name", None))
        print("Table:", getattr(diag, "table_name", None))
        print("Constraint:", getattr(diag, "constraint_name", None))
PY
```

```text
Exception type: InsufficientPrivilege
SQLSTATE: 42501
Message: permission denied for table alert_events
```

| SQL | Result |
|---|---|
| Normal INSERT | Succeeds |
| INSERT + `ON CONFLICT DO NOTHING` | `InsufficientPrivilege` |

Rather than granting SELECT, we change how the program handles duplicates.

## 9.3 Checking a Method That Handles Duplicate Errors

Check whether we can avoid `ON CONFLICT` and instead catch the primary-key duplicate error (`UniqueViolation`, SQLSTATE `23505`). Everything is rolled back at the end.

**Run on: security-core VM 220 (root)**

```bash
sudo -u wazuh-collector python3 - <<'PY'
import psycopg
import uuid
from datetime import datetime, timezone

event_id = "WAZUH-DUPLICATE-ROLLBACK-" + uuid.uuid4().hex

try:
    with psycopg.connect(
        host="postgresql.neomedia.mydns.jp",
        hostaddr="192.168.0.151",
        port=5432,
        dbname="security_workbench",
        user="wazuh_collector",
        sslmode="verify-full",
        sslrootcert="/etc/ssl/certs/postgresql-server-ca.pem",
        passfile="/etc/wazuh-collector/.pgpass",
    ) as conn:
        with conn.transaction():
            values = (
                event_id,
                datetime.now(timezone.utc),
                100106,
                12
            )

            # 1st: normal INSERT
            with conn.transaction():
                conn.execute("""
                    INSERT INTO incident.alert_events (
                        event_id,
                        event_timestamp,
                        rule_id,
                        rule_level
                    )
                    VALUES (%s, %s, %s, %s)
                """, values)

            print("FIRST INSERT: PASS")

            # 2nd: INSERT the same ID to cause a duplicate
            try:
                with conn.transaction():
                    conn.execute("""
                        INSERT INTO incident.alert_events (
                            event_id,
                            event_timestamp,
                            rule_id,
                            rule_level
                        )
                        VALUES (%s, %s, %s, %s)
                    """, values)

            except psycopg.errors.UniqueViolation as error:
                if error.sqlstate != "23505":
                    raise
                print("DUPLICATE DETECTED: PASS")

            # Check that the transaction is still usable after the duplicate error
            conn.execute("SELECT 1")
            print("CONNECTION RECOVERY: PASS")

            raise RuntimeError("INTENTIONAL_ROLLBACK")

except RuntimeError as error:
    if str(error) != "INTENTIONAL_ROLLBACK":
        raise
    print("ROLLBACK: completed")
    print("TEST DATA: NOT COMMITTED")
PY
```

```text
FIRST INSERT: PASS
DUPLICATE DETECTED: PASS
CONNECTION RECOVERY: PASS
ROLLBACK: completed
TEST DATA: NOT COMMITTED
```

The duplicate is detected, and the connection can still be used afterwards.

## 9.4 Backing Up Before the Fix

Show the parts to be fixed (the file is not changed).

**Run on: security-core VM 220 (root)**

```bash
sed -n '38,78p' /usr/local/lib/wazuh-collector/collector.py

echo
echo "===== process_line ====="

sed -n '280,310p' /usr/local/lib/wazuh-collector/collector.py
```

Make a backup. If a backup with the same name already exists, abort.

```bash
BACKUP=/usr/local/lib/wazuh-collector/collector.py.backup-before-duplicate-handling-20261118

if [ -e "$BACKUP" ]; then
    echo "ERROR: backup already exists; stopping"
    exit 1
fi

cp -a /usr/local/lib/wazuh-collector/collector.py "$BACKUP"

echo "===== BACKUP ====="
ls -l "$BACKUP"

echo
echo "===== SHA256 ====="
sha256sum \
  /usr/local/lib/wazuh-collector/collector.py \
  "$BACKUP"
```

Confirm that the two SHA256 values match.

## 9.5 Fixing the Duplicate Handling

Only the following two places change.

1. Remove `ON CONFLICT (event_id) DO NOTHING` from `INSERT_SQL`.
2. In `process_line()`, catch `UniqueViolation`, log the duplicate alert and skip it.

**Run on: security-core VM 220 (root)**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("/usr/local/lib/wazuh-collector/collector.py")
source = path.read_text(encoding="utf-8")

old_sql = """    %(mitre)s
)
ON CONFLICT (event_id) DO NOTHING
"""

new_sql = """    %(mitre)s
)
"""

old_process = """    with connection.transaction():
        connection.execute(INSERT_SQL, event)
"""

new_process = """    try:
        with connection.transaction():
            connection.execute(INSERT_SQL, event)
    except psycopg.errors.UniqueViolation as error:
        if error.sqlstate != "23505":
            raise
        logging.info("Duplicate alert skipped")
"""

if source.count(old_sql) != 1:
    raise SystemExit("ERROR: SQL target mismatch; no changes made")

if source.count(old_process) != 1:
    raise SystemExit("ERROR: process_line target mismatch; no changes made")

updated = source.replace(old_sql, new_sql, 1)
updated = updated.replace(old_process, new_process, 1)

temporary = path.with_suffix(".py.new")
temporary.write_text(updated, encoding="utf-8")
temporary.chmod(path.stat().st_mode)

temporary.replace(path)

print("PATCH: applied")
PY
```

If `PATCH: applied` is shown, the patch has been applied. If the target string is not found exactly once, nothing is changed and it aborts.

## 9.6 Checking the Fix

**Run on: security-core VM 220 (root)**

```bash
echo "===== PYTHON SYNTAX ====="
python3 -m py_compile /usr/local/lib/wazuh-collector/collector.py
echo "SYNTAX: PASS"

echo
echo "===== SQL CONFLICT CLAUSE ====="
grep -n -A 5 -B 5 'ON CONFLICT\|%(mitre)s' \
  /usr/local/lib/wazuh-collector/collector.py

echo
echo "===== process_line ====="
sed -n '290,315p' /usr/local/lib/wazuh-collector/collector.py

echo
echo "===== DIFF ====="
diff -u \
  /usr/local/lib/wazuh-collector/collector.py.backup-before-duplicate-handling-20261118 \
  /usr/local/lib/wazuh-collector/collector.py
```

Confirm that there are no syntax errors, that `ON CONFLICT` is gone, and that the diff consists only of the two places above.

## 9.7 Insert Test with the Production Code

Actually call `process_line()` of the fixed program and process the same alert twice. Everything is rolled back at the end, so no test data remains.

**Run on: security-core VM 220 (root)**

```bash
sudo -u wazuh-collector python3 - <<'PY'
import importlib.util
import json
import psycopg

path = "/usr/local/lib/wazuh-collector/collector.py"
spec = importlib.util.spec_from_file_location("collector", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

sample = {
    "id": "WAZUH-PROCESS-LINE-ROLLBACK-20261118-001",
    "timestamp": "2026-11-18T10:30:00.000+0000",
    "agent": {"id": "004", "name": "postgresql"},
    "manager": {"name": "security-core"},
    "decoder": {"name": "postgresql"},
    "rule": {
        "id": "100106",
        "level": 12,
        "description": "Collector process_line test",
        "groups": ["postgresql", "authentication_failed"],
        "mitre": {"id": ["T1110"]}
    },
    "data": {
        "srcip": "192.0.2.10",
        "srcport": "54321",
        "pwd": "MUST_NOT_BE_STORED"
    },
    "full_log": "MUST_NOT_BE_STORED"
}

line = (json.dumps(sample) + "\n").encode("utf-8")

try:
    with psycopg.connect(**module.DB_CONFIG) as conn:
        with conn.transaction():
            module.process_line(conn, line)
            print("FIRST PROCESS: PASS")

            module.process_line(conn, line)
            print("DUPLICATE PROCESS: PASS")

            conn.execute("SELECT 1")
            print("CONNECTION RECOVERY: PASS")

            raise RuntimeError("INTENTIONAL_ROLLBACK")

except RuntimeError as error:
    if str(error) != "INTENTIONAL_ROLLBACK":
        raise
    print("ROLLBACK: completed")
    print("TEST DATA: NOT COMMITTED")
PY
```

```text
FIRST PROCESS: PASS
Duplicate alert skipped
DUPLICATE PROCESS: PASS
CONNECTION RECOVERY: PASS
ROLLBACK: completed
TEST DATA: NOT COMMITTED
```

The new alert is inserted, the duplicate alert is skipped, and the connection remains usable. No SELECT privilege is needed.

# Chapter 10: Running It as a systemd Service

## 10.1 Preliminary Checks

**Run on: security-core VM 220 (root)**

```bash
echo "===== EXISTING UNIT ====="
systemctl status wazuh-collector.service --no-pager || true

echo
echo "===== UNIT FILE ====="
if [ -e /etc/systemd/system/wazuh-collector.service ]; then
    ls -l /etc/systemd/system/wazuh-collector.service
    cat /etc/systemd/system/wazuh-collector.service
else
    echo "No existing unit file"
fi

echo
echo "===== EXECUTION USER ====="
id wazuh-collector

echo
echo "===== SCRIPT PERMISSIONS ====="
stat -c '%U:%G %a %n' \
  /usr/local/lib/wazuh-collector/collector.py \
  /var/lib/wazuh-collector \
  /etc/wazuh-collector \
  /etc/wazuh-collector/.pgpass
```

Confirm that there is no existing unit and that the owner and permissions of each file are as in the table in 8.4.

## 10.2 Creating the Service Definition

Run it as the dedicated user and allow writing only to the state directory. Limits on memory, CPU and number of tasks are also set.

**Run on: security-core VM 220 (root)**

```bash
cat > /etc/systemd/system/wazuh-collector.service <<'EOF'
[Unit]
Description=Wazuh Alert Collector to PostgreSQL
Documentation=local
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=wazuh-collector
Group=wazuh-collector

ExecStart=/usr/bin/python3 /usr/local/lib/wazuh-collector/collector.py

Restart=always
RestartSec=5
UMask=0077

# Process restrictions
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
ProtectHostname=true
ProtectClock=true
RestrictSUIDSGID=true
LockPersonality=true
MemoryDenyWriteExecute=true

# Filesystem access
ReadOnlyPaths=/var/ossec/logs/alerts
ReadOnlyPaths=/etc/ssl/certs/postgresql-server-ca.pem
ReadOnlyPaths=/usr/local/lib/wazuh-collector
ReadWritePaths=/var/lib/wazuh-collector

# Resource limits
MemoryMax=512M
CPUQuota=50%
TasksMax=32

[Install]
WantedBy=multi-user.target
EOF

echo "===== UNIT FILE CREATED ====="
stat -c '%U:%G %a %n' \
  /etc/systemd/system/wazuh-collector.service

echo
echo "===== UNIT CONTENT ====="
systemd-analyze verify /etc/systemd/system/wazuh-collector.service
```

`systemd-analyze verify` gives the following warning.

```text
/etc/systemd/system/wazuh-collector.service:3: Invalid URL, ignoring: local
```

`Documentation=` must contain a URL or a manual page reference. This line is not needed, so delete it.

```bash
echo "===== UNIT FILE ====="
cat -n /etc/systemd/system/wazuh-collector.service

echo
echo "===== SYSTEMD VERIFY ====="
systemd-analyze verify /etc/systemd/system/wazuh-collector.service
```

```bash
sed -i '/^Documentation=local$/d' \
  /etc/systemd/system/wazuh-collector.service

echo "===== UPDATED UNIT ====="
cat -n /etc/systemd/system/wazuh-collector.service

echo
echo "===== SYSTEMD VERIFY ====="
systemd-analyze verify /etc/systemd/system/wazuh-collector.service

echo
echo "===== VERIFY EXIT CODE ====="
echo $?
```

It is done when the warning disappears and `VERIFY EXIT CODE` is `0`.

## 10.3 Starting It Manually

Do not set up automatic start (`enable`) yet; start it once to check its behavior.

**Run on: security-core VM 220 (root)**

```bash
systemctl daemon-reload

systemctl start wazuh-collector.service

echo "===== SERVICE STATUS ====="
systemctl status wazuh-collector.service --no-pager -l

echo
echo "===== RECENT JOURNAL ====="
journalctl -u wazuh-collector.service -n 30 --no-pager
```

Confirm that it is `active (running)` and that it runs as `wazuh-collector`.

```bash
sleep 5

echo "===== SERVICE STATUS ====="
systemctl is-active wazuh-collector.service

echo
echo "===== PROCESS ====="
systemctl show wazuh-collector.service \
  -p MainPID -p NRestarts -p ActiveState -p SubState

echo
echo "===== COLLECTOR STATE FILE ====="
if test -f /var/lib/wazuh-collector/state.json; then
    stat -c '%U:%G %a %s bytes %n' \
      /var/lib/wazuh-collector/state.json
else
    echo "STATE FILE NOT CREATED"
fi

echo
echo "===== JOURNAL ====="
journalctl -u wazuh-collector.service -n 30 --no-pager
```

The contents of the state file and the credentials are not shown.

Example output:

```text
INFO Wazuh alert collector starting
INFO Initial start at current end of alerts.json
INFO PostgreSQL connection established
```

Because this is the first startup, past alerts are not inserted, and reading starts from the current end of `alerts.json`. The state file is created owned by `wazuh-collector` with permissions `600`.

# Chapter 11: Checking Operation with Real Alerts

## 11.1 Checking the Waiting State

**Run on: security-core VM 220 (root)**

```bash
echo "===== ALERT FILE ====="
stat -c 'size=%s bytes modified=%y' \
  /var/ossec/logs/alerts/alerts.json

echo
echo "===== COLLECTOR JOURNAL ====="
journalctl -u wazuh-collector.service \
  --since "5 minutes ago" --no-pager

echo
echo "===== STATE FILE METADATA ====="
stat -c '%U:%G %a %s bytes %n' \
  /var/lib/wazuh-collector/state.json
```

Confirm that there are no restarts or errors in the log.

## 11.2 Checking the Rule Used for the Test

Use the PostgreSQL WARNING detection rule (100104) created in Part 2 to generate one test alert.

**Run on: security-core VM 220 (root)**

```bash
echo "===== TEST RULE 100104 ====="
grep -n -A 12 -B 3 '100104' \
  /var/ossec/etc/rules/local_rules.xml
```

Rule 100104 detects, among events matching parent rule 100100, those whose `event` is `POSTGRESQL_WARNING` (level 4). Check the parent rule's conditions and the decoder.

```bash
echo "===== PARENT RULE 100100 ====="
grep -n -A 15 -B 5 'id="100100"' \
  /var/ossec/etc/rules/local_rules.xml

echo
echo "===== POSTGRESQL DECODER ====="
grep -R -n -A 12 -B 3 \
  'POSTGRESQL_WARNING\|POSTGRESQL_' \
  /var/ossec/etc/decoders /var/ossec/etc/rules
```

Parent rule 100100 is as follows.

```xml
<rule id="100100" level="0">
  <decoded_as>json</decoded_as>
  <description>PostgreSQL sanitized JSON event base rule</description>
</rule>
```

There is no dedicated decoder; the standard Wazuh JSON decoder is used. So the test needs a JSON event (the string `POSTGRESQL_WARNING` alone does not match any decoder).

## 11.3 Rule Matching with wazuh-logtest

**Run on: security-core VM 220 (root)**

```bash
/var/ossec/bin/wazuh-logtest
```

When it starts, enter the following JSON on one line.

```json
{"event":"POSTGRESQL_WARNING","timestamp":"2026-11-18T11:05:00Z","srcip":"192.0.2.10"}
```

| Item | Expected result |
|---|---|
| Decoder | `json` |
| Rule ID | `100104` |
| Level | `4` |
| Description | `PostgreSQL WARNING event detected` |
| Verdict | `**Alert to be generated.` |

This test happens only inside `wazuh-logtest`, so nothing is added to `alerts.json` or the DB. When you exit, confirm that the Collector is running.

```bash
systemctl is-active wazuh-collector.service
```

## 11.4 Generating a Real Alert

Check the existing log input path.

**Run on: security-core VM 220 (root)**

```bash
echo "===== WAZUH LOG INPUT CONFIG ====="
grep -n -A 8 -B 3 '<localfile>' /var/ossec/etc/ossec.conf
```

Append one synthetic test event to the path created in Part 2 (`/var/log/postgresql-wazuh/events.log` in LXC 109 → Wazuh agent `postgresql` (ID 004)). `pct` is a Proxmox host command, so **run this on the Proxmox host, not on security-core**.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- bash -c '
printf "%s\n" \
  "{\"timestamp\":\"2026-11-18 20:01:00 JST\",\"event\":\"POSTGRESQL_WARNING\"}" \
  >> /var/log/postgresql-wazuh/events.log
'
```

> This event is synthetic test data. It does not indicate an actual PostgreSQL problem.

Check whether Wazuh generated an alert.

**Run on: security-core VM 220 (root)**

```bash
echo "===== LATEST POSTGRESQL WARNING ALERT ====="
grep '"rule"' /var/ossec/logs/alerts/alerts.json \
  | grep '"id":"100104"' \
  | tail -n 3
```

An alert with `agent.name` `postgresql` and `rule.id` `100104` is shown. Note down the `"id"` at the start of the alert (for example `1795000021.2810167`).

## 11.5 Checking the DB Insert

The Collector has no privilege to read the table (SELECT), so the insert is checked as the DB administrator (`postgres`).

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- runuser -u postgres -- \
  psql -X -d security_workbench -c "
SELECT
    event_id,
    event_timestamp,
    rule_id,
    rule_level,
    rule_description,
    agent_id,
    agent_name,
    manager_name,
    rule_groups,
    srcip
FROM incident.alert_events
WHERE event_id = '1795000021.2810167';
"
```

Replace the `event_id` value with the alert ID you noted in 11.4. If one row is shown, the flow `alerts.json` → Collector → PostgreSQL is working.

| Item | Inserted value (example) |
|---|---|
| event_id | `1795000021.2810167` |
| event_timestamp | `2026-11-18 11:07:01.074+00` |
| rule_id | `100104` |
| rule_level | `4` |
| rule_description | `PostgreSQL WARNING event detected` |
| agent_id / agent_name | `004` / `postgresql` |
| manager_name | `security-core` |
| rule_groups | `{local,postgresql,postgresql,warning}` |

## 11.6 Final Check of Stored Fields and Privileges

Check the table's columns.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- runuser -u postgres -- \
  psql -X -d security_workbench -c "
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'incident'
  AND table_name = 'alert_events'
ORDER BY ordinal_position;
"
```

Confirm that there are 14 columns and no columns such as `full_log`, `data`, `command` or `password`.

Check the privileges of the Collector's role.

```bash
pct exec 109 -- runuser -u postgres -- \
  psql -X -d security_workbench -c "
SELECT
    has_table_privilege(
        'wazuh_collector',
        'incident.alert_events',
        'INSERT'
    ) AS can_insert,
    has_table_privilege(
        'wazuh_collector',
        'incident.alert_events',
        'SELECT'
    ) AS can_select,
    has_table_privilege(
        'wazuh_collector',
        'incident.alert_events',
        'UPDATE'
    ) AS can_update,
    has_table_privilege(
        'wazuh_collector',
        'incident.alert_events',
        'DELETE'
    ) AS can_delete;
"
```

```text
 can_insert | can_select | can_update | can_delete 
------------+------------+------------+------------
 t          | f          | f          | f
(1 row)
```

The Collector can only add events; it cannot read, change or delete existing data.

# Chapter 12: Automatic Start and Auditing the Collected Data

## 12.1 Enabling Automatic Start

**Run on: security-core VM 220 (root)**

```bash
systemctl enable wazuh-collector.service
```

```bash
echo "===== SERVICE STATUS ====="
systemctl status wazuh-collector.service --no-pager -l

echo
echo "===== ENABLED STATUS ====="
systemctl is-enabled wazuh-collector.service

echo
echo "===== RESTART COUNT ====="
systemctl show wazuh-collector.service -p NRestarts
```

Confirm `Active: active (running)`, `enabled` and `NRestarts=0`.

## 12.2 Auditing Collection Counts and Gaps

After letting it run for a while, audit the data accumulated in the DB. All of the following SQL is read-only.

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- runuser -u postgres -- \
  psql -X -d security_workbench -c "
SELECT
    COUNT(*) AS total_events,
    MIN(event_timestamp) AS first_event,
    MAX(event_timestamp) AS latest_event,
    MAX(ingested_at) AS latest_ingested_at,
    COUNT(*) FILTER (
        WHERE rule_level >= 12
    ) AS high_severity_events,
    COUNT(*) FILTER (
        WHERE srcip IS NOT NULL
    ) AS events_with_srcip,
    COUNT(*) FILTER (
        WHERE agent_id IS NULL OR agent_name IS NULL
    ) AS missing_agent,
    COUNT(*) FILTER (
        WHERE rule_description IS NULL
    ) AS missing_description
FROM incident.alert_events;
"
```

Collection by agent:

```bash
pct exec 109 -- runuser -u postgres -- \
  psql -X -d security_workbench -c "
SELECT
    agent_id,
    agent_name,
    COUNT(*) AS event_count,
    MIN(event_timestamp) AS first_event,
    MAX(event_timestamp) AS latest_event,
    COUNT(*) FILTER (
        WHERE srcip IS NOT NULL
    ) AS events_with_srcip,
    COUNT(DISTINCT rule_id) AS distinct_rules
FROM incident.alert_events
GROUP BY agent_id, agent_name
ORDER BY event_count DESC;
"
```

Distribution by rule ID and level:

```bash
pct exec 109 -- runuser -u postgres -- \
  psql -X -d security_workbench -c "
SELECT
    rule_id,
    rule_level,
    rule_description,
    COUNT(*) AS event_count,
    COUNT(*) FILTER (
        WHERE srcip IS NOT NULL
    ) AS events_with_srcip,
    COUNT(DISTINCT agent_id) AS affected_agents
FROM incident.alert_events
GROUP BY
    rule_id,
    rule_level,
    rule_description
ORDER BY
    rule_level DESC,
    event_count DESC,
    rule_id;
"
```

| Rule ID | Level | Detection (example at build time) |
|---|---:|---|
| 5501 | 3 | PAM Login session opened |
| 5502 | 3 | PAM Login session closed |
| 100104 | 4 | PostgreSQL WARNING event detected |
| 87203 | 3 | Proxmox VE authentication succeeded. |

Field quality by decoder:

```bash
pct exec 109 -- runuser -u postgres -- \
  psql -X -d security_workbench -c "
SELECT
    decoder_name,
    COUNT(*) AS total,
    COUNT(*) FILTER (
        WHERE cardinality(rule_groups) = 0
    ) AS empty_rule_groups,
    COUNT(*) FILTER (
        WHERE jsonb_typeof(mitre) = 'object'
          AND mitre <> '{}'::jsonb
    ) AS has_mitre,
    COUNT(*) FILTER (
        WHERE srcip IS NOT NULL
    ) AS has_srcip,
    COUNT(*) FILTER (
        WHERE srcport IS NOT NULL
    ) AS has_srcport
FROM incident.alert_events
GROUP BY decoder_name
ORDER BY total DESC;
"
```

## 12.3 Auditing Consistency and Anomalous Values

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- runuser -u postgres -- \
  psql -X -d security_workbench -c "
SELECT
    COUNT(*) AS total_events,
    COUNT(DISTINCT event_id) AS unique_event_ids,
    COUNT(*) FILTER (
        WHERE event_timestamp > now() + interval '5 minutes'
    ) AS future_timestamps,
    COUNT(*) FILTER (
        WHERE event_timestamp IS NULL
    ) AS null_timestamps,
    COUNT(*) FILTER (
        WHERE rule_id < 0 OR rule_level NOT BETWEEN 0 AND 16
    ) AS invalid_rule_values,
    COUNT(*) FILTER (
        WHERE srcport IS NOT NULL AND srcip IS NULL
    ) AS port_without_ip,
    COUNT(*) FILTER (
        WHERE ingested_at < event_timestamp - interval '1 day'
    ) AS ingestion_time_anomalies,
    COUNT(*) FILTER (
        WHERE agent_id IS NULL
           OR agent_name IS NULL
           OR rule_description IS NULL
    ) AS missing_required_fields
FROM incident.alert_events;
"
```

> When pasting, do not include prompt characters such as `root@pve:~#` at the start of the lines.

| Audit item | Expected value |
|---|---|
| `total_events` and `unique_event_ids` | Same value (no duplicates) |
| `future_timestamps` | 0 |
| `null_timestamps` | 0 |
| `invalid_rule_values` | 0 |
| `port_without_ip` | 0 |
| `ingestion_time_anomalies` | 0 |
| `missing_required_fields` | 0 |

## 12.4 Reconciling Counts with the Wazuh Side

Find out whether the small number of source IPs in the DB is due to the Collector missing data or to the original alerts having no IP.

**Run on: security-core VM 220 (root)**

Presence of network fields across all of `alerts.json`:

```bash
python3 - <<'PY'
import json
from collections import Counter

path = "/var/ossec/logs/alerts/alerts.json"
counts = Counter()
total = 0

with open(path, encoding="utf-8") as f:
    for line in f:
        try:
            alert = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        total += 1
        data = alert.get("data")
        if not isinstance(data, dict):
            counts["no_data_object"] += 1
            continue

        for key in ("srcip", "srcport", "dstip", "dstport"):
            if data.get(key) not in (None, ""):
                counts[f"has_{key}"] += 1

        if not any(data.get(k) not in (None, "") for k in
                   ("srcip", "srcport", "dstip", "dstport")):
            counts["no_network_fields"] += 1

print("Total alerts:", total)
for key, value in sorted(counts.items()):
    print(f"{key}: {value}")
PY
```

Counts per agent since the Collector started (the time in the journal in 10.3):

```bash
python3 - <<'PY'
import json
from collections import defaultdict

path = "/var/ossec/logs/alerts/alerts.json"
start = "2026-11-18T11:00:48"

stats = defaultdict(lambda: {
    "total": 0,
    "srcip": 0,
    "srcport": 0,
    "first": None,
    "latest": None
})

with open(path, encoding="utf-8") as f:
    for line in f:
        try:
            a = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        ts = a.get("timestamp", "")
        if ts < start:
            continue

        agent = a.get("agent", {})
        name = agent.get("name", "unknown") if isinstance(agent, dict) else "unknown"
        data = a.get("data", {})
        if not isinstance(data, dict):
            data = {}

        s = stats[name]
        s["total"] += 1

        if data.get("srcip") not in (None, ""):
            s["srcip"] += 1
        if data.get("srcport") not in (None, ""):
            s["srcport"] += 1

        if s["first"] is None or ts < s["first"]:
            s["first"] = ts
        if s["latest"] is None or ts > s["latest"]:
            s["latest"] = ts

print("Collector start:", start)
print("Agent | Alerts | srcip | srcport | First | Latest")
for name, s in sorted(stats.items()):
    print(
        f"{name} | {s['total']} | {s['srcip']} | "
        f"{s['srcport']} | {s['first']} | {s['latest']}"
    )
PY
```

Replace the `start` value with the start time (UTC) of the Collector in your environment.

Counts per agent on the DB side:

**Run on: the Proxmox host (root@pve)**

```bash
pct exec 109 -- runuser -u postgres -- \
  psql -X -d security_workbench -c "
SELECT
    agent_id,
    agent_name,
    COUNT(*) AS db_events,
    MIN(event_timestamp) AS first_event,
    MAX(event_timestamp) AS latest_event,
    MAX(ingested_at) AS latest_ingested_at
FROM incident.alert_events
GROUP BY agent_id, agent_name
ORDER BY agent_id;
"
```

Reconciliation result at build time:

| Agent | Wazuh side | DB side | Difference |
|---|---:|---:|---:|
| pve (001) | 2 | 2 | 0 |
| postgresql (004) | 23 | 23 | 0 |
| **Total** | **25** | **25** | **0** |

All alerts since the Collector started had been inserted into the DB. The DB has no source IPs because the alerts in this period themselves contained no IP; nothing was missed.

## 12.5 Checking the Collector's Log

**Run on: security-core VM 220 (root)**

```bash
echo "===== COLLECTOR JOURNAL ====="
journalctl -u wazuh-collector.service \
  --since "2026-11-18 11:00:48 UTC" \
  --no-pager \
  -o short-iso

echo
echo "===== ERROR COUNTS ====="
journalctl -u wazuh-collector.service \
  --since "2026-11-18 11:00:48 UTC" \
  --no-pager \
  -p warning..emerg \
  | wc -l
```

`wc -l` also counts empty lines, so it may show `1`. Count the actual warning and error lines, excluding empty lines.

```bash
journalctl -u wazuh-collector.service \
  --since "2026-11-18 11:00:48 UTC" \
  --no-pager \
  -p warning..emerg \
  -o cat \
  | awk 'NF { print; count++ }
         END { print "Non-empty warning/error lines:", count+0 }'
```

If `Non-empty warning/error lines: 0` is shown, no connection errors, JSON parse errors or field validation errors have occurred.

## 12.6 Checking the State File and the Program

Check only the format of the state file, without showing its contents (values).

**Run on: security-core VM 220 (root)**

```bash
echo "===== STATE FILE METADATA ====="
stat -c 'Owner=%U Group=%G Mode=%a Size=%s Modified=%y' \
  /var/lib/wazuh-collector/state.json

echo
echo "===== STATE FILE JSON STRUCTURE ====="
python3 - <<'PY'
import json

path = "/var/lib/wazuh-collector/state.json"

with open(path, encoding="utf-8") as f:
    state = json.load(f)

print("Valid JSON: True")
print("Top-level type:", type(state).__name__)

if isinstance(state, dict):
    print("Top-level keys:", sorted(state.keys()))
    print("Field types:", {
        k: type(v).__name__ for k, v in state.items()
    })
PY
```

```text
Valid JSON: True
Top-level type: dict
Top-level keys: ['inode', 'offset']
Field types: {'inode': 'int', 'offset': 'int'}
```

Finally, check the program itself.

```bash
echo "===== COLLECTOR SOURCE METADATA ====="
stat -c 'Owner=%U Group=%G Mode=%a Size=%s Modified=%y' \
  /usr/local/lib/wazuh-collector/collector.py

echo
echo "===== FUNCTION DEFINITIONS ====="
grep -nE '^def |^class ' \
  /usr/local/lib/wazuh-collector/collector.py

echo
echo "===== SOURCE SYNTAX CHECK ====="
python3 -m py_compile \
  /usr/local/lib/wazuh-collector/collector.py \
  && echo "Python syntax: PASS"
```

| Item | Result |
|---|---|
| Owner / permissions | `root` / `755` |
| Size | 9,626 bytes (after the fix in 9.5) |
| Functions | 9 |
| Syntax | `Python syntax: PASS` |

# Summary of Part 3

In Part 3 we completed a mechanism that safely stores Wazuh alerts in PostgreSQL.

| Component | Details |
|---|---|
| Storage | `incident.alert_events` in the `security_workbench` DB (14 columns, no columns for sensitive information) |
| DB role | `wazuh_collector` (INSERT only; no SELECT, UPDATE or DELETE) |
| Connection | `hostssl` + `scram-sha-256` from `192.168.0.220/32`, TLS 1.3 with `verify-full` |
| Run-as user | `wazuh-collector` (cannot log in; read-only ACL on alerts) |
| Credentials | `/etc/wazuh-collector/.pgpass` (600) |
| State file | `/var/lib/wazuh-collector/state.json` (inode and read position) |
| Program | `/usr/local/lib/wazuh-collector/collector.py` (owned by root, 755) |
| Service | `wazuh-collector.service` (with privilege and resource limits, starts automatically) |

> **Note:** Line 11 of `pg_hba.conf` (`0.0.0.0/0 md5`), checked in Chapter 2, remains in operation as a broad rule. If it becomes a security problem, it will later be changed to limit the sources.

In Part 4, we strengthen the Collector based on the improvements found in the audit (input validation, rotation handling, recovery from DB disconnection and so on).

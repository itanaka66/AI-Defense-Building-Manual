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

⟦C0⟧

At build time there were 17 databases, including `security_workbench` (owner `security_workbench`) intended for security use.

## 1.2 Checking the Contents of security_workbench

Before creating a new database, check whether `security_workbench` is already in use. All operations in this section are read-only.

**Run on: the Proxmox host (root@pve)**

⟦C1⟧

Confirm that the user tables are `(0 rows)`.

Check the schemas and roles.

⟦C2⟧

Check the privileges on the `public` schema.

⟦C3⟧

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

⟦C4⟧

Example output:

⟦C5⟧

## 1.4 Creating the Collector Role

Confirm that the role name `wazuh_collector` is not yet in use.

**Run on: the Proxmox host (root@pve)**

⟦C6⟧

If `(0 rows)` is returned, there is no name conflict.

First, create a role that cannot log in and has no administrative privileges at all.

⟦C7⟧

If every column is `f` (disabled), it is in a safe initial state.

## 1.5 Setting the Password

To keep the password out of the shell history and SQL, use PostgreSQL's interactive password setting function.

**Run on: the Proxmox host (root@pve)**

⟦C8⟧

When the `security_workbench=#` prompt appears, enter the following.

⟦C9⟧

Enter the new password twice (the characters are not shown as you type).

- Use a sufficiently long random password (32 characters or more is recommended).
- Keep it safely in a password manager or similar, and do not paste it into chats or documents.

When done, enter the following to exit.

⟦C10⟧

Login is not allowed yet at this stage.

## 1.6 Granting Connection and Schema Usage Privileges

Allow only connecting to the database and using the `incident` schema. Do not grant privileges to create objects or administrative privileges.

**Run on: the Proxmox host (root@pve)**

⟦C11⟧

| Privilege | Expected value |
|---|---|
| Connect to the DB (CONNECT) | `t` |
| Use the `incident` schema (USAGE) | `t` |
| Create in the `incident` schema (CREATE) | `f` |

# Chapter 2: Checking the Network and TLS

We make it possible to connect safely from the Wazuh Manager (`192.168.0.220`) to PostgreSQL (`192.168.0.151`). Before allowing login, check the listen settings, the access rules and the TLS certificate. All operations in this chapter are read-only.

## 2.1 Checking the Listen Settings and Access Rules

**Run on: the Proxmox host (root@pve)**

⟦C12⟧

Check the actual contents of `pg_hba.conf` and the parsed rules (including netmasks).

⟦C13⟧

At build time, PostgreSQL was listening on port 5432 on all IPv4 and IPv6 interfaces, and line 11 of `pg_hba.conf` had the following broad access rule.

⟦C14⟧

This rule allows any IPv4 source to connect to every database as every user (authentication is still required). To avoid breaking existing applications' connections, we do not change this rule here. Access for Wazuh is added as a separate dedicated rule (Chapter 4).

> **Note:** This broad rule is kept as is to match existing operations. If it becomes a security problem, it will later be changed to limit the sources.

## 2.2 Checking the TCP Connection from the Wazuh Manager

Check only the TCP connection, without logging in to the database.

**Run on: the Proxmox host (root@pve)**

⟦C15⟧

If `err-data` shows `Connection to 192.168.0.151 5432 port [tcp/postgresql] succeeded!`, the network path is available.

## 2.3 Checking the TLS Certificate

To encrypt traffic that includes credentials, check PostgreSQL's TLS settings. The contents of the private key are not shown.

**Run on: the Proxmox host (root@pve)**

⟦C16⟧

⟦C17⟧

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

⟦C18⟧

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

⟦C19⟧

At build time, the connection used `TLSv1.3` and `TLS_AES_256_GCM_SHA384`. `Verify return code: 18 (self-signed certificate)` does not mean the connection failed; it means VM 220 does not yet trust this self-signed certificate.

## 3.2 Comparing the Fingerprint of the Received Certificate

Save the certificate received by VM 220 to a temporary file and show its SHA-256 fingerprint.

**Run on: the Proxmox host (root@pve)**

⟦C20⟧

Confirm that the fingerprint shown exactly matches the one checked inside LXC 109 in 2.3. The fingerprint at build time was as follows.

⟦C21⟧

If they match, the certificate received over the network is confirmed to be the PostgreSQL server's genuine certificate.

## 3.3 Placing It as a Dedicated Trusted Certificate

Do not register it in the OS-wide CA store; place it as a file used only for PostgreSQL connections.

**Run on: the Proxmox host (root@pve)**

⟦C22⟧

If `/etc/ssl/certs/postgresql-server-ca.pem: OK` and `Hostname postgresql.neomedia.mydns.jp does match certificate` are shown, it has succeeded.

## 3.4 Installing the PostgreSQL Client

Check whether VM 220 has the PostgreSQL client (`psql`).

**Run on: the Proxmox host (root@pve)**

⟦C23⟧

If there is no `psql`, check the standard Ubuntu package and install it. The PostgreSQL server itself is not installed.

⟦C24⟧

⟦C25⟧

The standard Ubuntu 24.04 `postgresql-client` (version 16) is installed. It can also connect to a PostgreSQL 17 server.

## 3.5 Checking the Connection Parameters

**Run on: the Proxmox host (root@pve)**

⟦C26⟧

At build time, the certificate's DNS name `postgresql.neomedia.mydns.jp` did not resolve. It does not need to be registered in DNS. If you specify the server's IP address with `PGHOSTADDR` (or `hostaddr`) and the certificate's DNS name with `PGHOST` (`host`), you can connect by IP while still verifying the host name.

Check the parameters and the certificate with this combination. No password is set and we do not log in.

⟦C27⟧

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

⟦C28⟧

⟦C29⟧

| Line | Rule | Scope |
|---:|---|---|
| 8 | `0.0.0.0/24` (md5) | `0.0.0.0`–`0.0.0.255` |
| 11 | `0.0.0.0/0` (md5) | All IPv4 addresses |

To protect existing applications, these rules are not changed here. Instead, add rules dedicated to `wazuh_collector` before the existing rules (at the top of the file). `pg_hba.conf` is evaluated from the top, and the first matching rule is used.

Check the file permissions and related settings.

⟦C30⟧

| Item | State at build time |
|---|---|
| `pg_hba.conf` | `postgres:postgres 640` |
| SSL | `on` |
| Password encryption | `scram-sha-256` |
| include directives | None |

## 4.2 Backing Up pg_hba.conf

**Run on: the Proxmox host (root@pve)**

⟦C31⟧

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

⟦C32⟧

Also confirm that the file's owner and permissions remain `postgres:postgres 640`.

## 4.4 Validating the Syntax and Reloading

Validate the added rules with PostgreSQL's own parser.

**Run on: the Proxmox host (root@pve)**

⟦C33⟧

If the four added rules are recognized and there are `0` syntax errors, reload the configuration. This is not a restart, so existing connections are not dropped.

⟦C34⟧

If `pg_reload_conf` is `t` and the service is `active`, the rules limiting the sources are in effect.

## 4.5 Enabling Login

**Run on: the Proxmox host (root@pve)**

⟦C35⟧

If only `rolcanlogin` is `t` and everything else is `f`, login is enabled with least privilege.

## 4.6 Checking Reachability Without a Password

Connect without giving a password and check that the connection passes TLS verification and the access rules and gets as far as the password authentication stage.

**Run on: the Proxmox host (root@pve)**

⟦C36⟧

If `no password supplied` is shown as below, it is as expected.

⟦C37⟧

There is no certificate error and no `no pg_hba.conf entry`, so TLS verification and the source restriction are working correctly.

## 4.7 TLS Connection with the Actual Password

Log in for real without writing the password in command arguments or environment variables.

> Run this command **after logging in to VM 220 (`root@security-core`) directly**, using the Proxmox VM console or SSH. `psql` is installed only on VM 220, so running it on the Proxmox host gives `psql: command not found`.

**Run on: security-core VM 220 (root)**

⟦C38⟧

When `Password:` appears, enter the `wazuh_collector` password set in 1.5 (the input is not shown).

| Item | Expected value |
|---|---|
| current_user | `wazuh_collector` |
| current_database | `security_workbench` |
| ssl | `t` |
| version | `TLSv1.3` |

Example output:

⟦C39⟧

An encrypted connection from VM 220 to LXC 109, with the certificate and source verified, is now established.

# Chapter 5: Examining the Alert Structure and Creating the Storage Table

## 5.1 Checking the Structure of the Alert File

Examine which fields Wazuh's alert file `alerts.json` contains.

**Run on: security-core VM 220 (root)**

⟦C40⟧

An alert's `data` can contain information that should not be stored in the DB, such as `pwd` (working directory) and `command` (the executed command). Therefore **we never store `data` or `full_log` in the DB as a whole.**

## 5.2 Checking Which Fields Are Safe to Store

Across all alerts, count how often each field name in `data`, each rule group and each MITRE field name appears. The values themselves are not shown.

**Run on: security-core VM 220 (root)**

⟦C41⟧

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

⟦C42⟧

Example output:

⟦C43⟧

`wazuh_collector` can only add alerts; it cannot read, change or delete existing events.

# Chapter 6: Checking the Collector's Runtime Environment

So that it does not affect the Wazuh Manager's operation, the Collector is built as a program that only reads `alerts.json`.

> Run the commands in this chapter **after logging in to VM 220 (`root@security-core`)**. `alerts.json` is inside VM 220, so running them on the Proxmox host gives `No such file or directory`. VM 220 has no serial port configured, so you cannot log in with `qm terminal 220`. Use SSH or the "Console" in the Proxmox web UI.

## 6.1 Checking the Alert File Permissions

**Run on: security-core VM 220 (root)**

⟦C44⟧

| Item | State at build time |
|---|---|
| `alerts.json` | Owner `wazuh`, permissions `640` |
| `/var/ossec/logs` | `770` |
| `/var/ossec/logs/alerts` | `750` |
| logrotate settings | None (Wazuh rotates the files itself) |

## 6.2 Checking the Alert Output Settings

**Run on: security-core VM 220 (root)**

⟦C45⟧

| Setting | Value at build time | Meaning |
|---|---|---|
| `jsonout_output` | `yes` | JSON alert output is enabled |
| `alerts_log` | `yes` | A text alert log is also written |
| `logall`, `logall_json` | `no` | Saving all events is disabled |
| `log_alert_level` | `3` | Level 3 and above are recorded as alerts |

The Collector does not change Wazuh's settings; it only reads `alerts.json`.

## 6.3 Checking the Rotation Method

**Run on: security-core VM 220 (root)**

⟦C46⟧

The Wazuh Manager switches alert files with its own rotation function (`analysisd.min_rotate_interval=600`, `monitord.rotate_log=1`). The Collector therefore tracks not just the file name but **the inode (the number of the actual file) and the read position**. Re-reading after rotation is combined with de-duplication by the DB's primary key.

## 6.4 Installing the PostgreSQL Driver

**Run on: security-core VM 220 (root)**

⟦C47⟧

At build time, Python was 3.12.3 and no driver was installed. We use **psycopg 3**, which can be managed with the standard OS packages.

⟦C48⟧

⟦C49⟧

If something like `psycopg: 3.1.17` is shown, it has succeeded.

## 6.5 Checking Whether ACLs Can Be Used

The Collector runs as a dedicated user separate from Wazuh. Adding the dedicated user to the `wazuh` group would also let it write to the log directory, so we check whether we can use **an ACL that allows only reading**. At this point, neither ACLs nor users are changed.

**Run on: security-core VM 220 (root)**

⟦C50⟧

The file system is `ext4`, so ACLs can be used. At build time, `getfacl` and `setfacl` were not installed, so install only the tools. The permissions of existing files are not changed.

⟦C51⟧

⟦C52⟧

# Chapter 7: A Dedicated User and Read-Only Permissions

## 7.1 Checking the Current Permissions

**Run on: security-core VM 220 (root)**

⟦C53⟧

Without changing the existing Wazuh owners, groups or permissions, give the dedicated user only the permissions it needs, through ACLs.

## 7.2 Creating the Dedicated Service User

Create a system user with no login shell and no home directory.

**Run on: security-core VM 220 (root)**

⟦C54⟧

⟦C55⟧

Example output:

⟦C56⟧

Confirm that it is not in the `wazuh` group.

## 7.3 Setting Read-Only ACLs

**Run on: security-core VM 220 (root)**

⟦C57⟧

| Target | Permission given to the dedicated user |
|---|---|
| `/var/ossec/logs` | Traverse only (`--x`) |
| `/var/ossec/logs/alerts` | Traverse only (`--x`) |
| `alerts.json` | Read only (`r--`) |
| Files created under `alerts` in the future | Read (default ACL; the effective permission is the intersection with the normal permissions at file creation) |

The directory above, `/var/ossec` (`root:wazuh 750`), also needs the traverse permission. Without it, the files below cannot be reached even with a read ACL, and you get `Permission denied`.

⟦C58⟧

## 7.4 Confirming That Access Is Read-Only

**Run on: security-core VM 220 (root)**

⟦C59⟧

⟦C60⟧

If all three items are `PASS`, the dedicated user can read the alert file but cannot change it.

Also check every level along the path.

⟦C61⟧

## 7.5 Checking the Structure of the Alert Files

Check how Wazuh actually manages the alert files.

**Run on: security-core VM 220 (root)**

⟦C62⟧

`<alerts>` contained only `log_alert_level` (3) and `email_alert_level` (12); `rotate_interval` and `max_output_size` were not set (disabled by default).

> `monitord.rotate_log` and `monitord.size_rotate` in `internal_options.conf` are settings for Wazuh's own internal logs, not for rotating `alerts.json`.

⟦C63⟧

Example output:

⟦C64⟧

`alerts.json` is **a hard link sharing the same inode** with the per-day file (`year/month/ossec-alerts-day.json`). When the date changes, a new day's file is created and the previous day's file is compressed (`.json.gz`). The Collector detects the date change from the change of `alerts.json`'s inode.

# Chapter 8: Creating the Collector

## 8.1 Creating the Credential Directory

**Run on: security-core VM 220 (root)**

⟦C65⟧

If `wazuh-collector:wazuh-collector 700 /etc/wazuh-collector` is shown, other users and services cannot access it.

Check the connection settings (the password is not shown).

⟦C66⟧

## 8.2 Creating the Password File (.pgpass)

Without showing the password on screen, save it in `.pgpass`, readable only by the dedicated user.

**Run on: security-core VM 220 (root)**

⟦C67⟧

Enter the password set in 1.5 twice. If the password contains a colon (`:`), creation is aborted for safety.

⟦C68⟧

Confirm that it is `wazuh-collector:wazuh-collector 600`. **Do not display the contents of the file.**

## 8.3 Connection Test as the Dedicated User

Connect with `verify-full` using `.pgpass`. No password prompt appears.

**Run on: security-core VM 220 (root)**

⟦C69⟧

It has succeeded if it connects to port 5432 on `192.168.0.151` with TLS 1.3 and shows `current_user` as `wazuh_collector` and `current_database` as `security_workbench`.

## 8.4 Creating the State Directory and Program Directory

Create a state directory that stores how far the alert file has been read (inode and read position).

**Run on: security-core VM 220 (root)**

⟦C70⟧

⟦C71⟧

The program is owned by root so that the user it runs as cannot change it.

⟦C72⟧

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

⟦C73⟧

> This program is strengthened in Part 4 with input validation, rotation handling and so on. The full text shown here is the version as of Part 3 (first version).

## 8.6 Checking the Created File

Pasting a long command can break the terminal display. Check that the file was created correctly to the end.

**Run on: security-core VM 220 (root)**

⟦C74⟧

⟦C75⟧

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

⟦C76⟧

If all five items show `PASS`, only the permitted fields are extracted and sensitive information is excluded.

# Chapter 9: Checking and Fixing the DB Insert

## 9.1 Checking the Table Privileges

Before checking whether the Collector can actually insert into the DB, check the privileges when connected as the dedicated user.

**Run on: security-core VM 220 (root)**

⟦C77⟧

Example output:

⟦C78⟧

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

⟦C79⟧

⟦C80⟧

INSERT with `ON CONFLICT`:

⟦C81⟧

⟦C82⟧

| SQL | Result |
|---|---|
| Normal INSERT | Succeeds |
| INSERT + `ON CONFLICT DO NOTHING` | `InsufficientPrivilege` |

Rather than granting SELECT, we change how the program handles duplicates.

## 9.3 Checking a Method That Handles Duplicate Errors

Check whether we can avoid `ON CONFLICT` and instead catch the primary-key duplicate error (`UniqueViolation`, SQLSTATE `23505`). Everything is rolled back at the end.

**Run on: security-core VM 220 (root)**

⟦C83⟧

⟦C84⟧

The duplicate is detected, and the connection can still be used afterwards.

## 9.4 Backing Up Before the Fix

Show the parts to be fixed (the file is not changed).

**Run on: security-core VM 220 (root)**

⟦C85⟧

Make a backup. If a backup with the same name already exists, abort.

⟦C86⟧

Confirm that the two SHA256 values match.

## 9.5 Fixing the Duplicate Handling

Only the following two places change.

1. Remove `ON CONFLICT (event_id) DO NOTHING` from `INSERT_SQL`.
2. In `process_line()`, catch `UniqueViolation`, log the duplicate alert and skip it.

**Run on: security-core VM 220 (root)**

⟦C87⟧

If `PATCH: applied` is shown, the patch has been applied. If the target string is not found exactly once, nothing is changed and it aborts.

## 9.6 Checking the Fix

**Run on: security-core VM 220 (root)**

⟦C88⟧

Confirm that there are no syntax errors, that `ON CONFLICT` is gone, and that the diff consists only of the two places above.

## 9.7 Insert Test with the Production Code

Actually call `process_line()` of the fixed program and process the same alert twice. Everything is rolled back at the end, so no test data remains.

**Run on: security-core VM 220 (root)**

⟦C89⟧

⟦C90⟧

The new alert is inserted, the duplicate alert is skipped, and the connection remains usable. No SELECT privilege is needed.

# Chapter 10: Running It as a systemd Service

## 10.1 Preliminary Checks

**Run on: security-core VM 220 (root)**

⟦C91⟧

Confirm that there is no existing unit and that the owner and permissions of each file are as in the table in 8.4.

## 10.2 Creating the Service Definition

Run it as the dedicated user and allow writing only to the state directory. Limits on memory, CPU and number of tasks are also set.

**Run on: security-core VM 220 (root)**

⟦C92⟧

`systemd-analyze verify` gives the following warning.

⟦C93⟧

`Documentation=` must contain a URL or a manual page reference. This line is not needed, so delete it.

⟦C94⟧

⟦C95⟧

It is done when the warning disappears and `VERIFY EXIT CODE` is `0`.

## 10.3 Starting It Manually

Do not set up automatic start (`enable`) yet; start it once to check its behavior.

**Run on: security-core VM 220 (root)**

⟦C96⟧

Confirm that it is `active (running)` and that it runs as `wazuh-collector`.

⟦C97⟧

The contents of the state file and the credentials are not shown.

Example output:

⟦C98⟧

Because this is the first startup, past alerts are not inserted, and reading starts from the current end of `alerts.json`. The state file is created owned by `wazuh-collector` with permissions `600`.

# Chapter 11: Checking Operation with Real Alerts

## 11.1 Checking the Waiting State

**Run on: security-core VM 220 (root)**

⟦C99⟧

Confirm that there are no restarts or errors in the log.

## 11.2 Checking the Rule Used for the Test

Use the PostgreSQL WARNING detection rule (100104) created in Part 2 to generate one test alert.

**Run on: security-core VM 220 (root)**

⟦C100⟧

Rule 100104 detects, among events matching parent rule 100100, those whose `event` is `POSTGRESQL_WARNING` (level 4). Check the parent rule's conditions and the decoder.

⟦C101⟧

Parent rule 100100 is as follows.

⟦C102⟧

There is no dedicated decoder; the standard Wazuh JSON decoder is used. So the test needs a JSON event (the string `POSTGRESQL_WARNING` alone does not match any decoder).

## 11.3 Rule Matching with wazuh-logtest

**Run on: security-core VM 220 (root)**

⟦C103⟧

When it starts, enter the following JSON on one line.

⟦C104⟧

| Item | Expected result |
|---|---|
| Decoder | `json` |
| Rule ID | `100104` |
| Level | `4` |
| Description | `PostgreSQL WARNING event detected` |
| Verdict | `**Alert to be generated.` |

This test happens only inside `wazuh-logtest`, so nothing is added to `alerts.json` or the DB. When you exit, confirm that the Collector is running.

⟦C105⟧

## 11.4 Generating a Real Alert

Check the existing log input path.

**Run on: security-core VM 220 (root)**

⟦C106⟧

Append one synthetic test event to the path created in Part 2 (`/var/log/postgresql-wazuh/events.log` in LXC 109 → Wazuh agent `postgresql` (ID 004)). `pct` is a Proxmox host command, so **run this on the Proxmox host, not on security-core**.

**Run on: the Proxmox host (root@pve)**

⟦C107⟧

> This event is synthetic test data. It does not indicate an actual PostgreSQL problem.

Check whether Wazuh generated an alert.

**Run on: security-core VM 220 (root)**

⟦C108⟧

An alert with `agent.name` `postgresql` and `rule.id` `100104` is shown. Note down the `"id"` at the start of the alert (for example `1795000021.2810167`).

## 11.5 Checking the DB Insert

The Collector has no privilege to read the table (SELECT), so the insert is checked as the DB administrator (`postgres`).

**Run on: the Proxmox host (root@pve)**

⟦C109⟧

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

⟦C110⟧

Confirm that there are 14 columns and no columns such as `full_log`, `data`, `command` or `password`.

Check the privileges of the Collector's role.

⟦C111⟧

⟦C112⟧

The Collector can only add events; it cannot read, change or delete existing data.

# Chapter 12: Automatic Start and Auditing the Collected Data

## 12.1 Enabling Automatic Start

**Run on: security-core VM 220 (root)**

⟦C113⟧

⟦C114⟧

Confirm `Active: active (running)`, `enabled` and `NRestarts=0`.

## 12.2 Auditing Collection Counts and Gaps

After letting it run for a while, audit the data accumulated in the DB. All of the following SQL is read-only.

**Run on: the Proxmox host (root@pve)**

⟦C115⟧

Collection by agent:

⟦C116⟧

Distribution by rule ID and level:

⟦C117⟧

| Rule ID | Level | Detection (example at build time) |
|---|---:|---|
| 5501 | 3 | PAM Login session opened |
| 5502 | 3 | PAM Login session closed |
| 100104 | 4 | PostgreSQL WARNING event detected |
| 87203 | 3 | Proxmox VE authentication succeeded. |

Field quality by decoder:

⟦C118⟧

## 12.3 Auditing Consistency and Anomalous Values

**Run on: the Proxmox host (root@pve)**

⟦C119⟧

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

⟦C120⟧

Counts per agent since the Collector started (the time in the journal in 10.3):

⟦C121⟧

Replace the `start` value with the start time (UTC) of the Collector in your environment.

Counts per agent on the DB side:

**Run on: the Proxmox host (root@pve)**

⟦C122⟧

Reconciliation result at build time:

| Agent | Wazuh side | DB side | Difference |
|---|---:|---:|---:|
| pve (001) | 2 | 2 | 0 |
| postgresql (004) | 23 | 23 | 0 |
| **Total** | **25** | **25** | **0** |

All alerts since the Collector started had been inserted into the DB. The DB has no source IPs because the alerts in this period themselves contained no IP; nothing was missed.

## 12.5 Checking the Collector's Log

**Run on: security-core VM 220 (root)**

⟦C123⟧

`wc -l` also counts empty lines, so it may show `1`. Count the actual warning and error lines, excluding empty lines.

⟦C124⟧

If `Non-empty warning/error lines: 0` is shown, no connection errors, JSON parse errors or field validation errors have occurred.

## 12.6 Checking the State File and the Program

Check only the format of the state file, without showing its contents (values).

**Run on: security-core VM 220 (root)**

⟦C125⟧

⟦C126⟧

Finally, check the program itself.

⟦C127⟧

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

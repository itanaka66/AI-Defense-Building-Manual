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

⟦C0⟧

At build time nothing was shown. No existing role reads only `wazuh-alerts`.

## 1.2 The Names of the Alert Indices

⟦C1⟧

⟦C2⟧

The alert indices are `wazuh-alerts-4.x-*`. `wazuh-archives-4.x-*` is also in the target patterns, but archives are disabled in Filebeat, so they are not included in what the AI analyzes.

## 1.3 Existing Role Mappings and Users

Show only user names and role mappings (password hashes are not shown).

⟦C3⟧

⟦C4⟧

Confirm that the name `ai-defense-reader` is not in use.

⟦C5⟧

`action_groups.yml` has no custom definitions. `read` is a permission group built into the Indexer.

## 1.4 The Tool That Applies the Settings

The Indexer's security settings are applied with `securityadmin.sh`. Java is the one bundled with the Indexer (`/usr/share/wazuh-indexer/jdk`).

⟦C6⟧

⟦C7⟧

⟦C8⟧

⟦C9⟧

# Chapter 2: Preparing the Definition Files

## 2.1 Backup

⟦C10⟧

Note down the directory name shown.

## 2.2 The Role

⟦C11⟧

⟦C12⟧

## 2.3 The Role Mapping

⟦C13⟧

⟦C14⟧

## 2.4 The Password Hash

For the Indexer's internal users, you register a bcrypt hash rather than the password itself. `hash.sh` asks for the password interactively, so writing its output directly to a file does not work (`Cannot allocate a console`). Run it with `script`, which records the interaction with the screen.

⟦C15⟧

⟦C16⟧

⟦C17⟧

⟦C18⟧

When `[Password:]` is shown, enter a random password for `ai-defense-reader` (it is not shown on screen). Do not leave the password or the hash in chats or records.

Extract only the hash from the recording and put it in a file readable only by root.

⟦C19⟧

⟦C20⟧

## 2.5 The User

⟦C21⟧

## 2.6 Validating the Three Files

⟦C22⟧

## 2.7 Checking the Administrator Certificate

`securityadmin.sh` connects to the Indexer with the administrator certificate. Confirm that the certificate's Subject matches the administrator registered in the Indexer (`admin_dn`).

⟦C23⟧

⟦C24⟧

At build time the Subject was `CN=admin,OU=Wazuh,O=Wazuh,...`, which matched `admin_dn`.

# Chapter 3: Applying to the Indexer

## 3.1 Caution: securityadmin.sh -f Replaces Each Type Entirely

`securityadmin.sh -f <file> -t <type>` **replaces entirely** the settings of that type (`roles`, `rolesmapping`, `internalusers`) with the contents of the specified file. If you apply files containing only what you want to add (the three made in Chapter 2) as they are, the existing roles, mappings and users disappear.

In the original build, the add-only files were applied first, and existing roles (`manage_wazuh_index`, `security_analytics_read_access` and others) disappeared. We restored them by creating "merged files" that add the new entries to the backup from 2.1 and applying those. This chapter shows the procedure of applying the merged files from the start.

## 3.2 Checking the Backup Contents

⟦C25⟧

The backup at build time had 37 roles.

## 3.3 Creating the Merged Files

Add the entries from Chapter 2, one each, to the three backup files. Existing entries are kept as they are, and it stops if a name being added already exists.

⟦C26⟧

## 3.4 Applying

Connect with the administrator certificate and apply the three types one at a time. Confirm that each shows `Done with success`.

⟦C27⟧

⟦C28⟧

⟦C29⟧

# Chapter 4: Confirming What Was Applied

## 4.1 Are the Required Entries There?

⟦C30⟧

## 4.2 Are All Existing Entries Still There?

Confirm that every entry in the backup is still present after applying.

⟦C31⟧

Confirm `ALL_BACKUP_ENTRIES_PRESERVED`.

## 4.3 Authenticating the User

The password is entered with `getpass` and not shown on screen.

⟦C32⟧

## 4.4 What Can Be Read

Confirm that alerts can be read and everything else is denied.

⟦C33⟧

At build time, archives also returned HTTP 200. This is because the archives indices do not exist (zero targets), so it does not confirm the permissions. Look at indices that actually exist and check whether access to them is denied.

⟦C34⟧

⟦C35⟧

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

⟦C36⟧

⟦C37⟧

⟦C38⟧

Without showing the contents, confirm only that no password is contained.

⟦C39⟧

⟦C40⟧

## 5.2 Creating the Password and Hash

`hash.sh` can take the password from an environment variable with `-env`. Because it is not written in the command arguments, it does not remain in the process list or history.

⟦C41⟧

⟦C42⟧

Create a random password and save it in a file readable only by root (`600`). It is not shown on screen.

⟦C43⟧

⟦C44⟧

⟦C45⟧

## 5.3 Applying

Create a file from the merged user file made in 3.3 with only the hash of `ai-defense-reader` replaced by the new one, and apply it (the other users remain as they are).

⟦C46⟧

⟦C47⟧

⟦C48⟧

> The merged file from 3.3 is based on the backup at the time it was applied. If Indexer users were added or changed after that, applying this file loses those changes. In that case, recreate it from the latest settings before applying.

## 5.4 Checking with the New Password

The password is read from the file and not shown on screen.

⟦C49⟧

⟦C50⟧

If it shows `ALERTS HTTP 200` and `MONITORING HTTP 403`, the scope is correctly limited.

# Chapter 6: Preparing for the Relay API

## 6.1 Alert Fields

To decide which fields to pass to the AI Defense Manager, fetch only the latest alert and show only the field names (the contents are not shown).

⟦C51⟧

The relay API returns only the following 10 fields. It does not return `full_log`, arbitrary `data`, user names, commands, passwords and the like.

| Category | Fields |
|---|---|
| Time | `timestamp` |
| Rule | `rule.id`, `rule.level`, `rule.description` |
| Agent | `agent.id`, `agent.name`, `agent.ip` |
| Management server | `manager.name` |
| Detection information | `location`, `decoder.name` |

Check the type of each (this user has no permission to read mappings, so check with one actual alert).

⟦C52⟧

At build time, `rule.level` was an integer and the other nine fields were strings.

## 6.2 Network and Firewall

The relay API will be placed on security-core and accessed from VM 230. Check the current listening state and the firewall.

⟦C53⟧

At build time, the Indexer (9200, 9300) listened only on 127.0.0.1 and was not exposed externally.

⟦C54⟧

⟦C55⟧

⟦C56⟧

At build time, ufw was `inactive`, there were no nftables rules, and firewalld was also `inactive`; security-core had no OS firewall.

⟦C57⟧

⟦C58⟧

⟦C59⟧

security-core has two networks (`enp6s18`: 192.168.0.220, `enp6s19`: 192.168.1.220), and VM 230 (192.168.0.33) is reached through `enp6s18` (192.168.0.220). The relay API will listen only on `192.168.0.220`.

⟦C60⟧

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

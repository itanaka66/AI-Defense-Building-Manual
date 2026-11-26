---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 40: Completing the PostgreSQL Logical Backup"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 40 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". In Part 39 we placed the PostgreSQL logical backup script `/usr/local/sbin/pg-logical-backup.sh` and got as far as testing whether the hard links used for the weekly and monthly generations can be created on NFS. This part does the following.

1. Check the result of the hard-link test
2. Check the script statically and register the systemd service and timer **while leaving them disabled**
3. Run the first backup by hand and check the file permissions, checksums and dump format
4. Replace the script with a safer version that can be repaired by re-running it if it fails partway
5. Enable the daily 02:00 timer

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)

# Chapter 1: Result of the Hard-Link Test

The result of the last test in Part 39 (create two temporary files on NFS, check that they share the same inode, then delete them) was as follows.

| Checked | Result |
|---|---|
| Mount | `192.168.0.254:/mnt/backup nfs`, `MOUNT_CHECK=PASS` |
| Hard link | both files `inode=5 links=2`, `HARDLINK_TEST=PASS` |
| Cleanup | `CLEANUP=PASS` |

Hard links work on TrueNAS's NFS, so we keep the method in which the daily, weekly and monthly generations share the same data. The test files have been removed.

# Chapter 2: Checking the Script and Registering the Units

## 2.1 Syntax and Permissions

> **Run on: pve**

⟦C0⟧

The result was `BASH_SYNTAX_EXIT=0` and the permissions were `-rwx------ root:root`. ShellCheck was not installed, and we do not install it here.

## 2.2 Checking How 02:00 Is Written

> **Run on: pve**

⟦C1⟧

It showed `Normalized form: *-*-* 02:00:00`, and the next run as `Mon 2026-11-23 02:00:00 JST`.

## 2.3 Reading the Save and Delete Logic

> **Run on: pve**

⟦C2⟧

From the output we confirmed the following.

- Only LXC 109 is backed up
- Global objects (roles and so on) and a dump for each database are saved
- Checksums are created and verified before moving the data to the official daily location
- Deletion only targets the inside of each daily, weekly and monthly generation directory

## 2.4 Registering the Service and Timer While Disabled

Here we do not run the script and do not enable the timer.

> **Run on: pve**

⟦C3⟧

`systemd-analyze verify` and `daemon-reload` returned `0`, and the timer was `disabled` and `inactive`.

## 2.5 Checking What Was Registered

> **Run on: pve**

⟦C4⟧

The service showed `Result=success` with an empty `ExecMainStartTimestamp` (it has never run), and the timer showed `0 timers listed.`. `preset: enabled` is displayed, but this is only systemd's default recommendation and does not change the current `disabled`.

# Chapter 3: The First Backup

## 3.1 Running It by Hand

With the timer still disabled, we start the service once. The PostgreSQL service is not stopped.

> **Run on: pve**

⟦C5⟧

In the log we confirmed that the dumps of the 17 databases and the global objects were saved and that all SHA-256 checksums were `OK`. It took about one minute. The data was saved in two places:

- Daily: `/mnt/pve/backup/postgresql/daily/2026-11-22`
- Weekly: `/mnt/pve/backup/postgresql/weekly/2026-W47`

November 22 was a Sunday, so a weekly generation was also created.

## 3.2 Checking the Saved Files

This only reads files. No restore and no writes to the database.

> **Run on: pve**

⟦C6⟧

| Checked | Result |
|---|---|
| File permissions | all `root:root`, `600` |
| SHA256 checksums | all 21 entries `OK` |
| `pg_restore --list` | succeeded for all 17 databases |
| Number of dumps | 17 |
| Hard links between daily and weekly | same inode, link count 2 |
| Timer | `disabled`, `inactive` |

Because `pg_restore --list` succeeded for all of them, we know the files not only exist but can also be read as PostgreSQL custom-format dumps.

## 3.3 Checking the Generation Directories

> **Run on: pve**

⟦C7⟧

daily had `2026-11-22`, weekly had `2026-W47`, monthly was empty (correct, because it is created on the 1st of each month), and staging was empty.

# Chapter 4: Making the Script Safer

## 4.1 What We Want to Fix

Re-reading the script, we found two points to fix before starting scheduled runs.

1. If creating a weekly or monthly generation with `cp -al` fails partway, an incomplete directory is left behind. On the next run, the mere existence of the directory is taken as "already created"
2. If the daily generation already exists, processing ends, so if the weekly or monthly step fails after the daily one was created, re-running on the same day cannot repair it

We fix it as follows.

- Create the weekly and monthly generations in a temporary directory, check them, and then publish them with `mv -T`
- Remove the temporary directory on failure
- If the daily generation already exists, verify its SHA256, reuse it, and create any missing weekly or monthly generations
- When deleting generations, check the directory names and the deletion target
- Do not change existing backups, owners, permissions or the number of generations

> **Caution:** Lines in the script such as `cp -al "$FINAL" "$WEEKLY/$WEEK"` are processing that uses the script's variables. Typed directly into a shell, the variables are empty and you get `cp: cannot stat ''` (the backups are not changed).

## 4.2 Replacing It

Save the original script to `/root/pg-logical-backup.sh.before-safety-fix-20261122`, syntax-check the new version, and replace it. The backup is not run and the timer is not enabled.

> **Run on: pve**

⟦C8⟧

Saving the original, replacing it and the Bash syntax check all returned exit code `0`. The owner and permissions are `root:root`, `700`.

## 4.3 Checking What Was Placed

We check the contents of the file to make sure no characters were mixed in when pasting into the terminal.

> **Run on: pve**

⟦C9⟧

We checked all 279 lines and confirmed that all the intended safeguards are present.

| Safeguard | Result |
|---|---|
| Verify the SHA256 of an existing daily generation | present |
| Reuse the daily generation | present |
| Create weekly and monthly in a temporary directory | present |
| Verify checksums before publishing | present |
| Publish generations with `mv -T` | present |
| Remove temporary data on abnormal exit | present |
| Check generation names | present |
| Number of generations | 7 days, 4 weeks, 3 months |

# Chapter 5: Enabling the Daily 02:00 Timer

This operation does not start a backup immediately. The next run is Monday, November 23, 2026, at 02:00. The Proxmox backup job for LXC 109 stays disabled for now.

> **Run on: pve**

⟦C10⟧

| Item | State |
|---|---|
| Timer | `enabled`, `active (waiting)` |
| Run time | daily at 02:00 (Japan time) |
| Next run | November 23, 2026, 02:00 |
| Target | PostgreSQL in LXC 109 |
| Destination | TrueNAS NFS `/mnt/pve/backup/postgresql` |
| Generations | daily 7, weekly 4, monthly 3 |

The result of the next day's run is checked in Part 43.

# Closing Notes

In Part 40 we completed the PostgreSQL logical backup and made it run automatically.

| Item | Result |
|---|---|
| Hard-link test | passed (same inode, link count 2) |
| Service and timer | registered `pg-logical-backup.service` and `.timer` (daily 02:00) |
| First backup | 17 databases and the global objects. 21 checksum entries `OK`, `pg_restore --list` succeeded for 17, permissions `600` |
| Script | replaced with a safer version (279 lines) that can be repaired by re-running. The original is `/root/pg-logical-backup.sh.before-safety-fix-20261122` |
| Timer | enabled (`enabled`, `active`) |
| Not yet done | Proxmox backup of LXC 109, restore test |

In the next part, Part 41, we back up LXC 109 to TrueNAS with Proxmox and test restoring it to an LXC with a different number.

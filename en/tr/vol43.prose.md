---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 3"
subtitle: "Part 43: Backup Failures After a Reboot and the Recovery"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 43 of Volume 3 of the "AI Autonomous Cyber Defense System Build Manual". By Part 42 we had set up three scheduled jobs (PostgreSQL logical backup at 02:00, LXC 109 backup at 03:00, TrueNAS ZFS snapshots from 04:00). Here we fix two separate problems found when checking the results of the first scheduled runs on the morning of November 23.

| Problem | What happened | Cause | Fix |
|---|---|---|---|
| 1 | After Proxmox rebooted at 06:50, NFS was not mounted | The NFS mount started before TrueNAS's VM 100 had booted and timed out after 90 seconds | Add a service that waits for TrueNAS to boot and NFS to respond before mounting |
| 2 | The 03:00 LXC 109 backup failed with `Permission denied` | The `tar` that reads an unprivileged LXC's files runs as UID 100000, but the temporary directory was created under the root-only NFS `dump/` | Set the temporary directory of job `lxc109-daily` to Proxmox's local `/var/tmp` |

The 02:00 PostgreSQL backup had succeeded.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **pve**: the Proxmox host (root)
- The TrueNAS API commands ask for TrueNAS's root password each time. Type it in the terminal and do not write it anywhere else.

# Chapter 1: Checking the Results of November 23

## 1.1 The Three Scheduled Jobs

At 08:58 on November 23, we read the logs, the saved files and the ZFS snapshots.

> **Run on: pve**

⟦C0⟧

The PostgreSQL logical backup finished dumping the 17 databases at 02:01 with `Result=success`. On the other hand, we found the following.

- The generation list under `/mnt/pve/backup/postgresql` is empty
- `/mnt/pve/backup/dump` does not exist
- The 03:00 LXC 109 backup is recorded as `ERR`

## 1.2 Is NFS Mounted?

> **Run on: pve**

⟦C1⟧

NFS was not mounted. `mnt-pve-backup.mount` started mounting at 06:50:27 and failed with a timeout at 06:51:57. What we see now is the empty local directory under the mount point. The backups on TrueNAS have not disappeared.

> **Caution:** While it is not mounted, do not create files in the local `/mnt/pve/backup`.

# Chapter 2: Why NFS Was Not Mounted

## 2.1 TrueNAS and the Logs

> **Run on: pve**

⟦C2⟧

Ping to TrueNAS had 0% loss, RPC (NFSv3, mountd) responded, and `/mnt/backup` was exported. The TrueNAS API also returned `HTTP 200`. Neither TrueNAS as a whole nor its NFS service is down.

> **Run on: pve**

⟦C3⟧

The kernel log showed that **the Proxmox host had rebooted at about 06:50:22 on November 23**.

## 2.2 The Network at Boot

> **Run on: pve**

⟦C4⟧

`networking.service` finished at 06:50:27, and `network-online.target` was reached at the same time. The link of the physical NIC `eno1` came up at 06:50:29, about two seconds after the mount started.

## 2.3 Host Load

> **Run on: pve**

⟦C5⟧

The load average was about 137, with 132–146 runnable processes (`r` in `vmstat`) for 64 logical CPUs. I/O wait was 0%; what stood out was VM 101 (`ollama-gpu`) and the multiple `llama-server` processes inside it. In the build records, the overloaded LXC was stopped here and the load average dropped to 39. We treat this as separate from the NFS problem.

## 2.4 When the TrueNAS VM Started

> **Run on: pve**

⟦C6⟧

⟦C7⟧

| Time | Event |
|---|---|
| 06:50:27 | `network-online.target` reached; NFS mount started |
| 06:50:29 | `eno1` link up |
| 06:51:57 | NFS mount timed out after 90 seconds |
| 06:54:12 | TrueNAS VM 100 started |
| 07:21:17 | `pve-guests.service` finished starting all guests |

When the NFS mount started, **the destination TrueNAS VM had not started yet**. That is the direct reason for the timeout.

## 2.5 The Approach

We do not wait for `pve-guests.service` to finish. In this boot it took about 29 minutes to start all guests, which would delay the backup destination too much. Also, even after the VM start completes, it takes time until NFS inside TrueNAS is usable. So we do the following.

1. Before mounting, check whether TrueNAS's VM 100 is running
2. Wait until it starts
3. Repeat until TrueNAS's NFSv3 RPC (mountd and NFS) responds
4. Mount only when both respond
5. If it is not ready within the set time (900 seconds), let the mount fail. `is_mountpoint 1` still prevents accidental writes to the local directory

# Chapter 3: Mounting After Waiting for TrueNAS

## 3.1 Placing the Wait Script and Service

We place the following three files. No mount is performed and no VM is restarted.

| File | Role |
|---|---|
| `/usr/local/sbin/truenas-nfs-ready.sh` | wait for VM 100 to start and NFSv3 RPC to respond (up to 900 seconds, every 5 seconds) |
| `/etc/systemd/system/truenas-nfs-ready.service` | run the script above as a oneshot |
| `/etc/systemd/system/mnt-pve-backup.mount.d/10-truenas-readiness.conf` | order the mount after the service above (`Requires`, `After`) |

> **Run on: pve**

⟦C8⟧

The syntax check and the dependency update worked, but `cp --parents` failed in the initial backup step, so we could not confirm that a copy of the original mount settings had been made (the original settings were not changed).

## 3.2 Saving the Original Settings and Testing the Script

Save the original mount settings reliably under another name and run the wait script without mounting.

> **Run on: pve**

⟦C9⟧

| Checked | Result |
|---|---|
| Copy of the original mount settings | SHA256 matches |
| `systemd-analyze verify` | `0` |
| Wait script | `0` |
| TrueNAS VM 100 | running |
| NFSv3 mountd and NFS RPC | both respond |

## 3.3 Testing the Mount

Mount once through systemd and test writing, reading and deleting. The backup job is not run.

> **Run on: pve**

⟦C10⟧

| Checked | Result |
|---|---|
| Mount through systemd | `0` |
| Connected to | `192.168.0.254:/mnt/backup` (NFSv3, TCP) |
| `truenas-backup` | `active` |
| Write, read, delete | all succeeded |
| Wait service | finished normally |

## 3.4 Effect on the November 23 Backups

> **Run on: pve**

⟦C11⟧

⟦C12⟧

- For PostgreSQL on November 23, the 17 dumps and `SHA256SUMS` exist, all checksums are `OK`, and there are no zero-byte files. It finished normally at 02:01:03
- The 03:00 LXC 109 backup had failed. The temporary snapshot is gone and no `.tmp` remains. The successful archive from November 22 is still there

Putting the times side by side, the LXC 109 failure was at 03:00 and the reboot at 06:50. **The 03:00 failure cannot be explained by the NFS mount failure.** We investigate it as a separate cause.

# Chapter 4: Why the LXC 109 Backup Failed

## 4.1 Differences from the Previous Success

> **Run on: pve**

⟦C13⟧

The log shows the backup's `tar` running in the following user namespace.

⟦C14⟧

LXC 109 is an unprivileged container (`unprivileged: 1`), so root inside the container is UID/GID `100000` on the host. Meanwhile, the NFS `dump/` had been set as follows in Part 42.

⟦C15⟧

## 4.2 Can UID 100000 Write?

Without changing permissions, test whether a temporary file can be created as UID/GID `100000:100000`.

> **Run on: pve**

⟦C16⟧

It gave `cannot create`, confirming that UID 100000 cannot enter `dump/`.

## 4.3 TrueNAS ACLs and the NFS Share

In TrueNAS CORE 12, ACLs are retrieved with a POST call. This is read-only; the ACLs are not changed.

> **Run on: pve**

⟦C17⟧

Both `/mnt/backup` and `/mnt/backup/dump` are `acltype: NFS4` with owner `0:0`. `dump` gives no permission to traverse the directory (`EXECUTE`) to anyone other than owner@.

> **Run on: pve**

⟦C18⟧

⟦C19⟧

The NFS share has `maproot_user = root` (only the client's UID 0 is mapped to root on the server), and `mapall_user` is empty. UID 100000 is not treated as root.

## 4.4 The Log of the Failure

> **Run on: pve**

⟦C20⟧

The log showed that what failed was not the destination of the archive but the **temporary directory** that `tar` reads.

⟦C21⟧

Proxmox runs the `tar` that reads an unprivileged LXC's files inside a namespace with UID/GID 100000. The temporary directory is created under the destination `dump/`, and because `dump/` is root-only `0700`, UID 100000 cannot reach it. The final archive (`.tar.dat`), by contrast, is the output of a pipe opened by root on the host, so it is not a problem.

Therefore there is no need to change TrueNAS ownership, ACLs or the NFS share. **It is enough to put just the temporary directory on a local disk.**

## 4.5 Can the Temporary Directory Be Set per Job?

> **Run on: pve**

⟦C22⟧

`/var/tmp` is on Proxmox's local ext4 with about 66GB free. The temporary directory mainly holds the LXC's configuration files, so it does not need space for the backup data itself.

> **Run on: pve**

⟦C23⟧

We confirmed that the backup job update API (`update_job`) takes `tmpdir` from the common settings (`json_config_properties()`), so **`tmpdir` can be set per job**. We can change only `lxc109-daily` without making it a global setting in `/etc/vzdump.conf`.

# Chapter 5: Making the Job's Temporary Directory Local

## 5.1 What We Change

⟦C24⟧

## 5.2 Setting It

Save `/etc/pve/jobs.cfg` before the change, set the value, and confirm it through both the API and the configuration file. No backup is run.

> **Run on: pve**

⟦C25⟧

- `/etc/pve/jobs.cfg` before the change was saved (SHA256 matches)
- The API response contains `"tmpdir": "/var/tmp"`
- `tmpdir /var/tmp` was written to `/etc/pve/jobs.cfg`
- Schedule, compression, destination, generations and target CTID are unchanged

## 5.3 Can the Namespace Read `/var/tmp`?

> **Run on: pve**

⟦C26⟧

From the unprivileged LXC's namespace, a file in a temporary directory under `/var/tmp` could be read. The test file was removed and no backup ran.

The current backup configuration is as follows.

⟦C27⟧

> **Caution:** The configuration list above is for explanation and is not a command. Pasting it into a shell gives `command not found` (no settings or data are harmed).

## 5.4 Running the Backup Again

Run it once with the same destination and mode as the scheduled job, with `/var/tmp` as the temporary directory, and then check the compression integrity of the archive. Existing generations are not deleted.

> **Run on: pve**

⟦C28⟧

| Item | Result |
|---|---|
| Run at | 2026-11-23 09:43:34 |
| Temporary directory | `/var/tmp` |
| Duration | 20 seconds |
| Exit code | `0` |
| Archive | `vzdump-lxc-109-2026_11_23-09_43_34.tar.zst` (about 473MiB) |
| zstd integrity | `ZSTD_TEST_EXIT=0` |

## 5.5 Checking the Contents and Cleanup

> **Run on: pve**

⟦C29⟧

| Checked | Result |
|---|---|
| tar listing | `TAR_LIST_EXIT=0` |
| Log | finished normally |
| Temporary files | none left |
| Archive | `root:root`, 495,748,185 bytes |

We also confirmed that the archive contains `./etc/vzdump/pct.conf`, `./etc/vzdump/pct.fw`, Wazuh-related data under `./var/ossec/`, and the root file system of the PostgreSQL container.

# Closing Notes

In Part 43 we fixed the two backup problems found on November 23.

| Item | Result |
|---|---|
| PostgreSQL 02:00 backup | succeeded (17 databases, checksums `OK`) |
| NFS after a reboot | `truenas-nfs-ready.service` now waits for TrueNAS VM 100 to start and NFSv3 to respond before mounting. Mount test passed |
| LXC 109 03:00 backup | Cause: the UID 100000 `tar` cannot reach a temporary directory on NFS. Set `tmpdir: /var/tmp` on the job; re-run succeeded |
| TrueNAS ownership, ACLs, NFS share | unchanged |
| Other issues | the `windows_d/windows_d` VG error and the thin pool capacity warning (settings unchanged) |

In the next part, Part 44, we check that Proxmox recognizes the backups correctly and compare the restored databases with production in detail.

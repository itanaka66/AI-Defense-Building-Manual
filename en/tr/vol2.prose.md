---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 1"
subtitle: "Part 2: Safely Monitoring PostgreSQL Logs and Correlation Detection"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 2 of Volume 1 of the "AI Autonomous Cyber Defense System Build Manual". We add PostgreSQL (LXC 109) log monitoring to the Wazuh environment built in Part 1. Without sending SQL statements, user names and so on to Wazuh, we safely extract only events such as authentication failures, and build brute-force detection per source IP.

- Investigating the PostgreSQL logs and deciding on a method that does not forward SQL statements (Chapter 1)
- Creating the sanitizing filter and running it as a service (Chapters 2–3)
- Wazuh agent monitoring settings and detection rules on the Manager side (Chapters 4–5)
- Correlation detection of authentication failures (Chapter 6)
- Obtaining the source IP and putting per-source-IP correlation detection into production (Chapters 7–8)

## Notation

- Commands and file contents are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Each step begins with "Run on", which says where to run it. `root@pve` is the Proxmox host and `root@security-core` is VM 220. Operations on LXC 109 are run from the Proxmox host with `pct exec 109 --`.
- "Example output" is the actual output from the build. In your environment, counts, dates and so on will differ.

## State at the End of Part 1

| Agent ID | Name | Target | State |
|---:|---|---|---|
| 000 | security-core | VM 220 (Manager, `192.168.0.220`) | Active/Local |
| 001 | pve | Proxmox host | Active |
| 002 | lxc-prometheus | LXC 103 | Active |
| 003 | lxc-grafana | LXC 105 | Active |
| 004 | postgresql | LXC 109 (PostgreSQL 17, `192.168.0.151`) | Active |

# Chapter 1: Investigating the PostgreSQL Logs

In this chapter we find out where and in what format PostgreSQL writes its logs. We do not change the PostgreSQL settings yet.

## 1.1 Checking the Log Settings and Configuration Files

**Run on: the Proxmox host (root@pve)**

⟦C0⟧

The settings at build time were as follows.

| Item | Setting |
|---|---|
| log_destination | `stderr` |
| logging_collector | `off` |
| log_directory | `log` |
| log_filename | `postgresql-%Y-%m-%d_%H%M%S.log` |
| Rotation | 1 day / 10 MB |

Because `logging_collector=off`, PostgreSQL itself does not create log files. The next step checks where the Debian service records the standard error output.

## 1.2 Checking the Log File and Logging Parameters

**Run on: the Proxmox host (root@pve)**

⟦C1⟧

The check showed the following.

- The log file to monitor is `/var/log/postgresql/postgresql-17-main.log`.
- Daily rotation is in effect.
- `log_line_prefix` is `%m [%p] %q%u@%d `.
- `log_connections=off`, `log_disconnections=off`, `log_min_messages=warning`. Connections and disconnections are not recorded, which limits monitoring of authentication failures and connection anomalies.

## 1.3 Checking the Log Contents and Existing Wazuh Settings

**Run on: the Proxmox host (root@pve)**

⟦C2⟧

The PostgreSQL log contains the following kinds of lines.

| Kind | Content |
|---|---|
| `ERROR` | SQL execution errors |
| `FATAL` | Serious errors such as authentication failures |
| `LOG` | Connections, disconnections and internal database events |
| `STATEMENT` | Executed SQL statements |

Wazuh had no PostgreSQL-specific decoder or log collection settings.

> **Important:** The current log records even actual SQL statements and application data. If this log is forwarded to the Wazuh Manager as is, the database information is duplicated on the SIEM side as well.

## 1.4 Deciding the Monitoring Method

We decided to build it as follows.

**A method that does not forward SQL statements or parameter values to the Wazuh Manager**

1. Keep the raw log only inside LXC 109.
2. An independent filter running inside LXC 109 reads the log and writes only permitted events to a separate file.
3. The Wazuh agent monitors only the file written by the filter.

The filter passes to Wazuh only the time, the severity and a predefined event category. It does not forward SQL statements, `STATEMENT`, `DETAIL` or `CONTEXT` lines, user names, or raw error messages.

## 1.5 Checking the Rotation Method and Log Output Method

**Run on: the Proxmox host (root@pve)**

⟦C3⟧

| Item | Result | Decision |
|---|---|---|
| Rotation method | `copytruncate` | The filter must follow truncation of the file |
| rsyslog | `inactive` | Do not use rsyslog forwarding rules |
| Log file permissions | `postgres:adm 640` | Do not let Wazuh read the original log directly |

## 1.6 Checking the Effective Settings

Check the log settings that PostgreSQL actually uses.

**Run on: the Proxmox host (root@pve)**

⟦C4⟧

Because `log_min_error_statement=error`, whenever an SQL error occurs, the SQL statement is recorded on a separate `STATEMENT:` line. The filter must reliably exclude this line.

## 1.7 Counting by Severity

Count only the number of lines per severity, without showing log text or SQL statements.

**Run on: the Proxmox host (root@pve)**

⟦C5⟧

Example output:

⟦C6⟧

`ERROR` and `STATEMENT` have the same count (88), which shows that an SQL statement is recorded with every error.

## 1.8 Checking the Kinds of FATAL

To distinguish authentication failures from other connection failures, count only `FATAL` lines by keyword. The log text is not shown.

**Run on: the Proxmox host (root@pve)**

⟦C7⟧

At build time, 8 of the 20 `FATAL` lines were password authentication failures. All other patterns were 0.

From this result, we decided on the following events to send to Wazuh.

| What is detected | Event name sent to Wazuh |
|---|---|
| Password authentication failure | `POSTGRESQL_AUTH_FAILURE` |
| Other FATAL | `POSTGRESQL_FATAL` |
| ERROR | `POSTGRESQL_ERROR` |
| WARNING | `POSTGRESQL_WARNING` |
| PANIC | `POSTGRESQL_PANIC` |

Logs that cannot be classified are not forwarded.

# Chapter 2: Preparing the Filter

## 2.1 Checking the Existing Settings and Output Location

**Run on: the Proxmox host (root@pve)**

⟦C8⟧

Confirm that there are no Wazuh monitoring settings for PostgreSQL yet and that the filter's output location is `Not created`.

## 2.2 Checking the User the Wazuh Agent Runs As

To decide the owner and permissions of the output file, check the user Wazuh runs as.

**Run on: the Proxmox host (root@pve)**

⟦C9⟧

⟦C10⟧

Check the user the log collection process (`wazuh-logcollector`) runs as, and whether it can access the original log.

> `pgrep -x wazuh-logcollector` does not work, because `pgrep -x` cannot search for process names longer than 15 characters. Get the PID from the path of the executable instead.

⟦C11⟧

Example output:

⟦C12⟧

| Item | Result |
|---|---|
| Wazuh user | `wazuh` (UID 103, GID 107) |
| `wazuh-logcollector` | Runs as root, group `wazuh` |
| Original PostgreSQL log | Not readable by the `wazuh` user (desirable) |

We do not change the permissions of the original log. Only the filter service, running as root, reads the original log, and Wazuh reads only the filter's output file.

## 2.3 Creating the Filter Output Location

**Run on: the Proxmox host (root@pve)**

⟦C13⟧

Example output:

⟦C14⟧

## 2.4 Checking the Python Runtime

**Run on: the Proxmox host (root@pve)**

⟦C15⟧

At build time, with Python 3.13.5 and systemd 257, the filter could be implemented without additional packages.

# Chapter 3: Creating the Filter and Running It as a Service

## 3.1 How the Filter Works

1. Read the PostgreSQL log.
2. Parse only the standard PostgreSQL log prefix at the start of each line (time, PID, severity) to identify `FATAL`, `ERROR`, `WARNING` and `PANIC`. The string "ERROR" in the body is not used for the decision, so SQL statements and multi-line `STATEMENT`s are never mistaken for events.
3. Classify authentication failures as a dedicated event.
4. Do not output SQL statements, `STATEMENT`, `DETAIL`, `CONTEXT`, user names or error text.
5. Do not forward past logs written before startup; process only new logs.
6. Follow file replacement and file truncation by `copytruncate`.

## 3.2 Creating the Filter

**Run on: the Proxmox host (root@pve)**

⟦C16⟧

If `root:root 750 /usr/local/sbin/postgresql-wazuh-filter.py` and `Python syntax OK` are shown at the end, it has succeeded.

## 3.3 Confirming That the File Was Written to the End

When a long command is pasted, the terminal display can break partway through. Besides the syntax check, confirm that the file was written all the way to the end.

**Run on: the Proxmox host (root@pve)**

⟦C17⟧

If the file has 89 lines and ends with `if __name__ == "__main__":`, it is correct.

## 3.4 Testing Against the Actual Log Format

Check whether the filter's patterns match the format of the current PostgreSQL log. Only the counts are examined; no log text or SQL statements are shown.

**Run on: the Proxmox host (root@pve)**

⟦C18⟧

If `PASS` is shown, the filter handles the actual log format. If `REVIEW REQUIRED` is shown, fix the patterns before going on. The counts at build time were as follows.

| Event | Count |
|---|---:|
| Authentication failure | 8 |
| Other FATAL | 12 |
| ERROR | 88 |
| WARNING | 3 |

## 3.5 Testing That SQL Statements Are Not Output

Without writing to the actual PostgreSQL log, test only the Python functions with dummy data.

**Run on: the Proxmox host (root@pve)**

⟦C19⟧

Example output:

⟦C20⟧

## 3.6 Registering the systemd Service

Register a systemd service to keep the filter running. It sets security restrictions such as a read-only file system and limited write locations.

**Run on: the Proxmox host (root@pve)**

⟦C21⟧

Confirm that `systemd-analyze verify` shows no errors.

## 3.7 Starting the Service

**Run on: the Proxmox host (root@pve)**

⟦C22⟧

It has succeeded if the service is `active (running)` and `Started postgresql-wazuh-filter.service - PostgreSQL sanitized event filter for Wazuh.` is logged. Memory use at build time was about 1.6 MB.

## 3.8 Changing the Output Format to JSON

To use Wazuh's JSON log collection, standardize the output format on JSON. The change is made while the output file is still empty, so it does not affect existing events.

Stop the service, rewrite the output part, and test the JSON output.

**Run on: the Proxmox host (root@pve)**

⟦C23⟧

Example output:

⟦C24⟧

## 3.9 Restarting the Service

**Run on: the Proxmox host (root@pve)**

⟦C25⟧

If `active` is shown, the filter is ready. In the next chapter we have the Wazuh agent monitor this file.

# Chapter 4: Monitoring Settings for the Wazuh Agent

Have the Wazuh agent on LXC 109 monitor only the JSON file written by the filter. It does not monitor the original PostgreSQL log.

## 4.1 Backing Up the Configuration File

**Run on: the Proxmox host (root@pve)**

⟦C26⟧

## 4.2 Adding the Monitoring Settings

Leave the existing configuration blocks untouched and add a new `<ossec_config>` block at the end of the configuration file.

**Run on: the Proxmox host (root@pve)**

⟦C27⟧

## 4.3 Validating the Settings

Wazuh's `ossec.conf` may contain several `<ossec_config>` blocks. Parsing it as a normal XML document therefore gives the error `junk after document element`. This is not a configuration error. Wrap the whole thing in a temporary root element before validating.

**Run on: the Proxmox host (root@pve)**

⟦C28⟧

Example output:

⟦C29⟧

## 4.4 Restarting the Wazuh Agent

**Run on: the Proxmox host (root@pve)**

⟦C30⟧

It has succeeded if `active` is shown and `Started wazuh-agent.service - Wazuh agent.` is logged.

## 4.5 Confirming That Monitoring Has Started

**Run on: the Proxmox host (root@pve)**

⟦C31⟧

| Item | Expected value |
|---|---|
| Log collection | `Analyzing file: '/var/log/postgresql-wazuh/events.log'.` is logged |
| File permissions | `root:wazuh 640` |
| Read by the Wazuh user | `PASS: wazuh can read sanitized events` |

# Chapter 5: Detection Rules on the Manager Side

Add PostgreSQL-specific detection rules to the Wazuh Manager on VM 220. In this chapter, operations on VM 220 are run from the Proxmox host with `qm guest exec 220` (a way to run commands inside the VM through the QEMU Guest Agent). The result is returned as JSON, with the command output in `out-data`.

## 5.1 Checking That the QEMU Guest Agent Responds

**Run on: the Proxmox host (root@pve)**

⟦C32⟧

If `"pretty-name" : "Ubuntu 24.04.5 LTS"` is returned, VM 220 can be operated through the Guest Agent.

## 5.2 Checking the Existing Rules

**Run on: the Proxmox host (root@pve)**

⟦C33⟧

At build time, `local_rules.xml` contained only one sample rule for SSH authentication failures, `100001`. For PostgreSQL we use `100100`–`100105`, separate from the existing rules.

## 5.3 Checking for Duplicate Rule IDs

**Run on: the Proxmox host (root@pve)**

⟦C34⟧

Confirm that `PASS: IDs 100100-100104 are not in use` is returned.

## 5.4 Backing Up the Rule File

**Run on: the Proxmox host (root@pve)**

⟦C35⟧

## 5.5 Adding the Detection Rules

Add rules that use the JSON decoder as the parent rule and fire only when the `event` field matches exactly.

| Rule ID | Event | Level |
|---|---|---:|
| 100100 | Parent rule (common to JSON events) | 0 |
| 100101 | Authentication failure | 8 |
| 100102 | FATAL | 10 |
| 100103 | ERROR | 7 |
| 100104 | WARNING | 4 |
| 100105 | PANIC | 12 |

**Run on: the Proxmox host (root@pve)**

⟦C36⟧

Do not restart the Manager yet.

## 5.6 Validating the Rules

**Run on: the Proxmox host (root@pve)**

⟦C37⟧

It is correct if all six rules show `PASS` and `Exit code: 0`. The message about `Rule tree threshold` is an INFO message about memory use, not an error.

## 5.7 Testing with wazuh-logtest

Before restarting the Manager, use Wazuh's rule testing function to check that the five kinds of event match the intended rules. No test data enters the production log.

**Run on: the Proxmox host (root@pve)**

⟦C38⟧

| Event | Rule ID | Level | Result |
|---|---:|---:|---|
| Authentication failure | 100101 | 8 | Match |
| FATAL | 100102 | 10 | Match |
| ERROR | 100103 | 7 | Match |
| WARNING | 100104 | 4 | Match |
| PANIC | 100105 | 12 | Match |

Because PANIC is level 12, `mail: True` is shown. This means it would be notified if email notification were configured; no email has been sent.

## 5.8 Restarting the Manager

**Run on: the Proxmox host (root@pve)**

⟦C39⟧

It has succeeded if `active` is shown and `Started wazuh-manager.service - Wazuh manager.` is logged.

## 5.9 Checking the Agent Connection

**Run on: the Proxmox host (root@pve)**

⟦C40⟧

It is normal if the LXC 109 agent log has `Connected to the server ([192.168.0.220]:1514/tcp)` and the Manager's list shows `ID: 004, Name: postgresql, IP: any, Active`. The agent is temporarily disconnected right after the Manager restarts, but it reconnects automatically.

## 5.10 End-to-End Forwarding Test

Instead of causing test SQL or authentication failures in PostgreSQL, append one fixed JSON line to the filter's output file and check everything from forwarding to detection.

> **Note:** This test records one test WARNING alert in Wazuh. Treat it as a test event so that it is not confused with a real incident.

**Run on: the Proxmox host (root@pve)**

⟦C41⟧

Check whether an alert with agent ID `004` and rule ID `100104` was recorded in `alerts.json` on VM 220.

⟦C42⟧

If `PASS: PostgreSQL test alert received`, `"rule_id": "100104"` and `"agent": "postgresql"` are shown, forwarding and detection from LXC 109 to VM 220 are working.

By the end of this chapter, the following mechanism is complete.

- A filter that does not forward SQL statements from the original PostgreSQL log
- JSON events that contain no user names, SQL statements or error messages
- Collection of the events by the Wazuh agent
- Classification of five kinds of events and alert generation by the Wazuh Manager

# Chapter 6: Correlation Detection of Authentication Failures

Besides single authentication failures, we detect authentication failures repeated in a short time as "suspected brute-force attacks". The current filter does not output SQL statements, user names or source IPs, so in this chapter we use the method **detect five or more authentication failures within 60 seconds on the same agent (LXC 109)**. Correlation per source IP is covered in Chapter 7.

| Item | Setting |
|---|---|
| Target event | Rule `100101` (`POSTGRESQL_AUTH_FAILURE`) |
| Grouping | Same agent |
| Time window | 60 seconds |
| Occurrences | 5 |
| Correlation rule ID | `100106` |
| Level | 12 |

We do not change the PostgreSQL settings, forward the original log, or change the firewall.

## 6.1 Checking the Existing Rules

**Run on: the Proxmox host (root@pve)**

⟦C43⟧

Confirm that the existing PostgreSQL rules `100100`–`100105` exist, that `100106`–`100119` are not in use, and that there is no existing correlation rule.

## 6.2 Backing Up the Rule File

**Run on: the Proxmox host (root@pve)**

⟦C44⟧

## 6.3 Checking How Correlation Rules Are Written

Check how the standard Wazuh rules write correlation rules with `frequency` (count) and `timeframe` (time window).

**Run on: the Proxmox host (root@pve)**

⟦C45⟧

## 6.4 Adding the Correlation Rule

Insert rule `100106` just before the existing `100102`.

**Run on: the Proxmox host (root@pve)**

⟦C46⟧

Do not restart the Manager yet.

## 6.5 Validating the Rules

**Run on: the Proxmox host (root@pve)**

⟦C47⟧

The XML structure and rule IDs are correct, but `wazuh-analysisd -t` gives the following warning.

⟦C48⟧

In Wazuh 4.14.10, `same_agent` is deprecated. In Wazuh 4.x, correlation rules **count only events from the same agent** by default (you specify `<global_frequency />` only when you want to count across all agents). So removing the `same_agent` line does not change the counting condition.

> **Note:** Do not restart the Manager while the warning remains. Fix it with the next step before applying.

## 6.6 Removing the Deprecated Setting

Remove only the `same_agent` line. The condition of 5 times in 60 seconds stays the same.

**Run on: the Proxmox host (root@pve)**

⟦C49⟧

The fix is complete when `PASS: Deprecated same_agent removed` is shown and `wazuh-analysisd -t` no longer warns.

## 6.7 Correlation Test with wazuh-logtest

Send five authentication failures in a row, only inside `wazuh-logtest`. Nothing is written to the actual PostgreSQL or agent logs.

**Run on: the Proxmox host (root@pve)**

⟦C50⟧

| Attempt | Matched rule | Level |
|---:|---|---:|
| 1st–4th | 100101 | 8 |
| 5th | 100106 | 12 |

It has succeeded if `100106` fires on the 5th attempt with MITRE ATT&CK `T1110` (Credential Access / Brute Force).

## 6.8 Checks Before Applying

**Run on: the Proxmox host (root@pve)**

⟦C51⟧

## 6.9 Restarting the Manager

During the restart, the Wazuh Manager's detection stops temporarily. The agent-side settings and PostgreSQL itself are not changed.

**Run on: the Proxmox host (root@pve)**

⟦C52⟧

## 6.10 Checking That the Agents Reconnect

**Run on: the Proxmox host (root@pve)**

⟦C53⟧

Set the `--since` time slightly before the start time (UTC) shown in 6.9.

> **If an agent is not listed or shows Pending:** Right after the Manager restarts, some agents may temporarily be `Pending` (waiting to connect). In the original build, the Proxmox host's agent (001) was temporarily Pending as well, but it reconnected automatically after about a minute and a half. Do not re-register or delete the agent; check its state with the following steps.

Check the registration state of all agents.

⟦C54⟧

If one is Pending, check the connection on that agent's side (example for the Proxmox host).

**Run on: the Proxmox host (root@pve)**

⟦C55⟧

If the log shows a reconnection and `TCP 1514 CONNECT OK`, wait a little and check the list again.

⟦C56⟧

It is normal when agents 001–004 are all `Active`.

## 6.11 Correlation Test over the Actual Forwarding Path

Append five test authentication-failure events to the filter's output file and check whether `100106` fires over the actual path from LXC 109 to the Manager.

> **Note:** The test events are recorded in Wazuh's production alerts. Mark them clearly as a "synthetic test" in your operation records and do not treat them as a real attack. The PostgreSQL log and database are not changed.

**Run on: the Proxmox host (root@pve)**

⟦C57⟧

Check the Manager's alerts.

⟦C58⟧

If `SUCCESS: Rule 100106 detected` is shown, brute-force correlation detection works over the actual forwarding path as well. At build time, four single detections (100101) and one correlation detection (100106, level 12) were recorded.

By the end of this chapter, the following can be detected.

| Rule ID | Detection |
|---|---|
| 100101 | PostgreSQL authentication failure (single) |
| 100106 | Five or more authentication failures within 60 seconds on the same agent (suspected brute force, MITRE T1110) |

However, this method does not reveal the attacker's IP address. In the next chapter we safely add the source IP to the events.

# Chapter 7: Obtaining the Source IP and Prototyping an IP-Aware Filter

The correlation detection in Chapter 6 works per agent, so it does not reveal the attacker's IP address. In this chapter, while keeping the policy of not sending SQL statements or user names to Wazuh, we prepare to add the source IP to authentication-failure events.

| Item | Policy |
|---|---|
| Information forwarded | Time, event type, source IP |
| Information not forwarded | SQL statements, user names, passwords, DB names, source ports, PIDs, original log text |
| Correlation unit | Source IP address |
| Detection condition | Five or more from the same IP within 60 seconds |
| IPv4 / IPv6 | Both supported |
| Existing rules | Keep 100101 and 100106 |

## 7.1 Checking Whether Authentication-Failure Logs Contain IP Addresses

First, check whether authentication-failure lines and connection-received lines in the current log contain IP addresses. The log text and SQL statements are not shown.

**Run on: the Proxmox host (root@pve)**

⟦C59⟧

At build time, the current log file had zero authentication failures (earlier failures had been moved to older files by rotation). So count including the rotated logs.

⟦C60⟧

Totals from the example output:

⟦C61⟧

None of the 28 past authentication failures had an IP address, and there were zero connection-received log lines. This is because `log_connections=off`, so connection-received logs are not recorded.

## 7.2 The Method Adopted

Enable PostgreSQL's `log_connections` and obtain the IP as follows.

1. When PostgreSQL accepts a connection, it logs a line containing the PID and the source IP (`LOG: connection received`).
2. If authentication fails on the same connection, an authentication-failure line is logged with the same PID.
3. The filter keeps the PID-to-IP mapping only temporarily in memory and attaches the source IP to the authentication-failure event.

Authentication failures whose IP cannot be obtained are not used for per-IP correlation; only single detection is done for them, as before.

## 7.3 Checking the PostgreSQL Settings

Before changing settings, check the current values and the conditions under which a setting takes effect (`context`).

**Run on: the Proxmox host (root@pve)**

⟦C62⟧

| Setting | Current value | Action |
|---|---|---|
| `log_connections` | off | Enable (Chapter 8) |
| `log_line_prefix` | `%m [%p] %q%u@%d ` | Contains `%p` (PID), so connection-received and authentication-failure lines can be matched by PID |
| `log_hostname` | off | Do not change (record the IP, not the DNS name) |
| `logging_collector` | off | Do not change |
| `log_destination` | stderr | Do not change |

## 7.4 Checking and Backing Up the Existing Filter

**Run on: the Proxmox host (root@pve)**

⟦C63⟧

Save the script before modifying it. The service is not stopped and no settings are changed.

⟦C64⟧

If the SHA-256 of the original script and the backup match, you can restore it.

## 7.5 Prototyping the IP-Aware Filter

Do not rewrite the running script. Create the IP-aware version as a temporary file (`/tmp/postgresql-wazuh-filter-ip.py`) and test it. Even if the test fails, current log collection does not stop.

The prototype's specification is as follows.

- Get the PID and IP address from `LOG: connection received` lines.
- Match them against the PID of `FATAL: password authentication failed` lines.
- Validate IPv4 and IPv6 with the `ipaddress` module.
- Keep the PID-to-IP mapping in memory for at most 300 seconds.
- Do not output SQL statements, user names, DB names, port numbers or the original log text.
- If the IP cannot be obtained, do not output the IP field.

**Run on: the Proxmox host (root@pve)**

⟦C65⟧

If `Temporary filter syntax: PASS` is shown, it has succeeded.

## 7.6 Confirming That the Temporary File Was Written to the End

**Run on: the Proxmox host (root@pve)**

⟦C66⟧

It is correct if the file has 115 lines, the end of the `classify()` function (`return None`) is present, and `EXIT CODE: 0` is shown.

## 7.7 Discarding the PID-to-IP Mapping Right After Use

So that an old IP is not wrongly attached to another connection when the OS reuses a PID, discard the PID-to-IP mapping right after processing the authentication failure (change `connections.get` to `connections.pop`).

> Replacing a whole string can fail because of differences in how newline characters are handled. Here we rewrite the one relevant line directly.

**Run on: the Proxmox host (root@pve)**

⟦C67⟧

If the updated block contains `connection = connections.pop(pid, None)`, it has succeeded.

## 7.8 Testing IPv4, IPv6 and Leak Prevention

Use simulated logs to check the following points.

**Run on: the Proxmox host (root@pve)**

⟦C68⟧

| Test | Expected result |
|---|---|
| IPv4 PID matching | `192.0.2.10` is attached |
| Restriction of output fields | Only three: `timestamp`, `event`, `source_ip` |
| User names and text not output | `SECRET_USER` and so on are not included |
| Port and PID not output | `54321` and `12345` are not included |
| Discard after use | After an authentication failure is processed, the PID mapping is gone |
| IPv6 normalization | Normalized to `2001:db8::1` |
| Expiry | Mappings older than 300 seconds are not used |
| Host names rejected | Host names that are not IPs are not output |

If `ALL FILTER TESTS PASSED` is shown at the end, it has succeeded. Note that this test uses simulated logs. Checking against the actual PostgreSQL log is done in the next step.

## 7.9 Checks on the Wazuh Side

To correlate per source IP in Wazuh, check the current rules and version on the Manager side.

**Run on: the Proxmox host (root@pve)**

⟦C69⟧

Back up the rule file.

⟦C70⟧

Confirm that the standard Wazuh rules use per-source-IP correlation (`same_source_ip`).

⟦C71⟧

If standard rules such as those for Apache or Microsoft SQL Server use `same_source_ip`, the same method can be used for PostgreSQL source-IP correlation.

> **Choice of field name:** For compatibility with Wazuh's standard source-IP correlation, the IP field name in the events is standardized on **`srcip`** rather than `source_ip` (changed in Chapter 8).

## 7.10 Checking Against the Actual Log Format

Check the leading part of the `LOG` and `FATAL` lines in the existing log. Authentication-failure lines are shown with their text replaced by `[REDACTED]`.

**Run on: the Proxmox host (root@pve)**

⟦C72⟧

The actual log had the following format.

⟦C73⟧

Check whether the temporary filter's regular expression can extract the timestamp, PID and severity from the existing log.

⟦C74⟧

If `MATCHED_LINES: 10` is shown and the timestamp, PID and `LOG` are extracted from all 10 lines, the filter handles the actual log format.

> **When `log_connections` takes effect:** The `context` of `log_connections` is `superuser-backend`. In PostgreSQL 17, settings of this kind can be changed in `postgresql.conf` and take effect on a configuration reload (SIGHUP). They apply only to connections that start afterwards, not to existing connections. **No PostgreSQL restart is needed.**

In this chapter we built a prototype of the IP-aware filter and checked its behavior with both simulated logs and the actual log format. In the next chapter, we change the prototype's field name to `srcip`, put it into production, enable `log_connections`, and add a per-source-IP correlation rule.

# Chapter 8: Putting Per-Source-IP Correlation Detection into Production

Based on the prototype from Chapter 7, we put it into production in the following order.

1. Fix the prototype's regular expression and field name (`srcip`), and test
2. Change Wazuh correlation rule `100106` to work per source IP, and test
3. Enable PostgreSQL's `log_connections` (without a restart)
4. Create, test and switch production to the integrated filter (IP support plus the existing monitoring loop)
5. Apply the rules to the Wazuh Manager and do a final check with real authentication failures

## 8.1 Fixing the Prototype

Support the format in which several spaces follow the PID, and change the output IP field name to `srcip`.

> Pasting a long Python script into the terminal can break it partway so that it does not run (in the original build, too, the here-document was cut off and caused a `SyntaxError`). Here we rewrite only the two lines concerned with `sed`.

**Run on: the Proxmox host (root@pve)**

⟦C75⟧

Example output:

⟦C76⟧

## 8.2 Testing the Regular Expression

Check that the following three formats are recognized.

**Run on: the Proxmox host (root@pve)**

⟦C77⟧

| Format | Expected result |
|---|---|
| `LOG` with several spaces after the PID | `PID= 198 SEVERITY= LOG` |
| `LOG` with user and DB name | `PID= 198 SEVERITY= LOG` |
| Authentication-failure `FATAL` | `PID= 198 SEVERITY= FATAL` |

If `ALL PREFIX TESTS PASSED` is shown at the end, it has succeeded.

## 8.3 Testing the IP Correlation Logic

**Run on: the Proxmox host (root@pve)**

⟦C78⟧

If all six items show `PASS` and `ALL IP CORRELATION TESTS PASSED` is shown, it has succeeded.

## 8.4 Changing the Correlation Rule to Work per Source IP

Add `<same_source_ip />` to rule `100106` so that the condition becomes "five or more from the same source IP within 60 seconds".

Check the current rule.

**Run on: the Proxmox host (root@pve)**

⟦C79⟧

Take a backup, change the rule and validate the syntax.

⟦C80⟧

The rule after the change is as follows.

⟦C81⟧

> At this point only the rule file has changed; it is not yet applied to the running Manager. The Manager is restarted in 8.9.

## 8.5 Testing the Correlation Rule

`wazuh-logtest` loads the rule file as it is at that moment. Check the following three cases.

**Five times from the same IP (100106 fires on the 5th)**

**Run on: the Proxmox host (root@pve)**

⟦C82⟧

It has succeeded if the 1st to 4th are `100101` (level 8) and the 5th is `100106` (level 12, MITRE `T1110`).

**Mixed IPs (100106 does not fire)**

⟦C83⟧

`192.0.2.10` appears four times and `192.0.2.20` once, so it has succeeded if all five are `100101` and `100106` does not appear.

**No source IP (100106 does not fire)**

⟦C84⟧

It has succeeded if all five are `100101` and `100106` does not appear. This confirms that events with an unknown source IP are not wrongly counted as coming from the same attacker.

Finally, validate the Manager's configuration.

⟦C85⟧

`"exitcode" : 0` is correct (`Rule tree threshold` in `err-data` is INFO, not an error).

> `"exited" : 1` in the `qm guest exec` result means "the command has finished running". Judge the command's success by `"exitcode"`. Also, pasting the JSON shown as the result into the shell gives `command not found`, but this does not affect the system.

## 8.6 Enabling log_connections

Have PostgreSQL log connection-received entries (`connection received`) without restarting it.

### Checking the current setting and the configuration file layout

**Run on: the Proxmox host (root@pve)**

⟦C86⟧

⟦C87⟧

If `pg_file_settings` has no matching row, the setting is not written in any configuration file and the default `off` is used.

⟦C88⟧

Confirm that `include_dir = 'conf.d'` is present and that `conf.d` is empty. Instead of editing the existing `postgresql.conf` directly, we place a dedicated configuration file in `conf.d`.

### Backup and creating the dedicated configuration file

⟦C89⟧

⟦C90⟧

### Validation before applying

⟦C91⟧

It is correct if `log_connections` in `99-wazuh-connection-logging.conf` is `on`, `applied` is `t`, and `error` is empty.

### Reloading the configuration (no restart)

⟦C92⟧

If `t` is returned, the reload has succeeded. Existing connections are not dropped; the setting applies to connections that start afterwards.

⟦C93⟧

| Item | Expected value |
|---|---|
| setting | `on` |
| source | `configuration file` |
| pending_restart | `f` |

### Checking the connection-received log

⟦C94⟧

At build time, the PID and source IP were recorded as follows.

⟦C95⟧

Connections from the local socket are recorded as `host=[local]`. This is not an IP address, so the filter does not treat it as an IP.

## 8.7 Creating the Integrated Filter and Switching Production to It

The prototype has no `main()` (monitoring loop) that keeps reading the log. So we create an integrated version that keeps the production monitoring loop as is (skipping past logs, following file replacement and `copytruncate`) and adds only the IP handling.

### Backing up the production filter

**Run on: the Proxmox host (root@pve)**

⟦C96⟧

### The integrated filter (full text of the final version)

Inside LXC 109, create `/tmp/postgresql-wazuh-filter-integrated.py` with the following content (160 lines, 3,785 bytes, SHA-256 `98481b5042866fde348a03b909a19faef54f3f24da661488481bd6c5b2bf9bf4`).

> Pasting a long file into the terminal can break it. Create it with an editor, or transfer the file into place. After creating it, always confirm with the following step that its SHA-256 matches the value above.

⟦C97⟧

### Setting owner and permissions and validating the syntax

⟦C98⟧

| Item | Expected value |
|---|---|
| Owner, permissions, size | `root:root 750 3785 bytes` |
| SHA-256 | `98481b5042866fde348a03b909a19faef54f3f24da661488481bd6c5b2bf9bf4` |
| Functions | `def classify` on line 60, `def main` on line 119, `if __name__` on line 159 |

### Checking the difference from the production version

⟦C99⟧

Confirm that the existing monitoring loop (skipping past logs, detecting inode changes, following `copytruncate`, JSON output) is kept and that only the IP handling has been added.

### Functional tests

⟦C100⟧

If all eight items show `PASS` and `ALL TESTS PASSED` is shown, it has succeeded.

### Edge-case tests

Check PID reuse, expiry, invalid IPs and the mapping limit (10,000 entries).

⟦C101⟧

If `ALL EDGE TESTS PASSED` is shown, it has succeeded.

### Checking the state of the production service

⟦C102⟧

The systemd service definition (security restrictions, limits on read and write paths) is not changed.

### Preparing to deploy to production

Place a candidate file (`.new`) next to the production file. The current service keeps running.

⟦C103⟧

Confirm that the SHA-256 of the two files match. Note down the backup file name shown (`postgresql-wazuh-filter.py.backup-before-ip-deploy-<date-time>`), because it is used in the next step.

### Switching production

Replace the production file in one operation (`mv`) and restart only the filter service. If the restart fails, the backup is restored automatically.

> **Note 1:** `BACKUP=` in the following command contains the backup file name from the original build. Always replace it with **the file name from your own environment** shown in the previous step before running it.
>
> **Note 2:** The filter starts reading from the end of the log when it starts, so PostgreSQL events that occur during the restart (a few seconds) may not be forwarded. PostgreSQL itself, the Wazuh Manager and the Wazuh agent are not restarted.

⟦C104⟧

The switch is complete if the service is `active (running)`, the SHA-256 of the production file is the same as the integrated version, and `DEPLOYMENT CHECK COMPLETE` is shown at the end.

⟦C105⟧

## 8.8 Checking with a Real Authentication Failure

### Causing one authentication failure

Try a local TCP connection to the existing user `agent` with a wrong password. No database data is changed.

**Run on: the Proxmox host (root@pve)**

⟦C106⟧

Replace the user name and database name with ones that exist in your environment. It has succeeded if an event with `srcip` is recorded in the output file, like this:

⟦C107⟧

> **Why one attempt records two events:** In the original build, each run of `psql` recorded two authentication failures. Both carry the same source IP, and neither contains SQL statements, user names or passwords.

### Checking that it reaches the Manager

⟦C108⟧

If this authentication failure is recorded as `"rule_id": "100101"`, `"srcip": "127.0.0.1"` and `"agent": "postgresql"`, it has reached the Manager.

## 8.9 Applying the Rules to the Manager

The rule file was changed in 8.4, but the running process uses the old rules until the Manager is restarted. Note that `wazuh-logtest` reads the file as it is at that moment, so the tests used the new rules.

> `wazuh-control reload` does not just re-read the rules. Internally it stops and restarts the Manager's services. Here we restart the Manager with systemd.

### Backup before restarting

**Run on: the Proxmox host (root@pve)**

⟦C109⟧

⟦C110⟧

Confirm that the SHA-256 of the original file and the backup match.

### Restarting the Manager

During the restart, receiving events from agents, analysis and alert generation stop temporarily.

⟦C111⟧

It has succeeded if `active` and a new `wazuh-analysisd` process are shown.

⟦C112⟧

It is normal if agents 001–004 are all `Active` and there is no `error`, `critical` or `failed` in the last five minutes.

## 8.10 Final Check of Source-IP Correlation

Cause five authentication failures from the same source IP.

**Run on: the Proxmox host (root@pve)**

⟦C113⟧

Check the correlation alert on the Manager.

⟦C114⟧

It is complete if `100106` with the description "same source IP" is recorded, like this:

⟦C115⟧

> The JSON shown as the result is output for checking. It is not something to paste into the shell and run.

## State at the End of Part 2

PostgreSQL monitoring has been completed with the following configuration.

| Stage | Processing |
|---|---|
| PostgreSQL 17 (LXC 109) | Logs authentication failures and connection-received entries (PID, source IP) |
| Sanitizing filter | Matches PIDs to source IPs, removes SQL statements, user names, passwords, etc., and converts to JSON |
| Wazuh agent (ID 004) | Forwards the JSON events to the Manager |
| Wazuh Manager (VM 220) | Single detection and per-source-IP correlation detection |

| Rule ID | Level | Detection |
|---|---:|---|
| 100101 | 8 | PostgreSQL authentication failure (single) |
| 100102 | 10 | Other FATAL |
| 100103 | 7 | ERROR |
| 100104 | 4 | WARNING |
| 100105 | 12 | PANIC |
| 100106 | 12 | Five or more authentication failures from the same source IP within 60 seconds (MITRE T1110) |

Automatic blocking has not been enabled yet. In Part 3, we build the Collector, which saves the alerts produced by Wazuh into PostgreSQL and manages them as incidents.

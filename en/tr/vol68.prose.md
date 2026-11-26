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

⟦C0⟧

# Chapter 1: What the Isolated Environment Needs

## 1.1 Where Rules Are Loaded From

> **Run on: VM 220**

⟦C1⟧

⟦C2⟧

Wazuh rules are loaded from two places: the standard rules (`/var/ossec/ruleset/rules`) and the local rules (`/var/ossec/etc/rules`). We test in an environment that includes the standard rules and decoders, not just the candidate file.

## 1.2 Checking the Configuration for Secrets

Without showing values, we count only the names of elements that look like secrets.

> **Run on: VM 220**

⟦C3⟧

There were elements for TLS certificates and secret keys, CA certificates, authentication and passwords, so the production `ossec.conf` is not copied.

## 1.3 Items Needed for a Minimal Configuration

> **Run on: VM 220**

⟦C4⟧

# Chapter 2: Building the Isolated Environment

## 2.1 Placing the Basic Files

We place `wazuh-analysisd` and its shared libraries, the standard rules and decoders, the required lists, a minimal `ossec.conf` without secrets, and the candidate `local_rules.xml` in `/tmp/wazuh-rule-validation-20261124`.

> **Run on: VM 220**

⟦C5⟧

## 2.2 Fixing the Directory Hierarchy

In 2.1 we placed things under `var/ossec/…`, but `-D` treats the specified directory as the root and looks for `etc/ossec.conf` and so on. We also copy the required directories to the top level.

> **Run on: VM 220**

⟦C6⟧

The eight rule IDs of the candidate were preserved, and the production `local_rules.xml` and Wazuh Manager were unchanged.

## 2.3 Files Needed to Run

> **Run on: VM 220**

⟦C7⟧

⟦C8⟧

We placed the OS shared libraries used by `wazuh-analysisd`, Wazuh's `libwazuhext.so` and two internal configuration files in their standard locations in the isolated environment.

## 2.4 Creating `etc/shared`

> **Run on: VM 220**

⟦C9⟧

# Chapter 3: Testing in the Isolated Environment

## 3.1 Removing the XML Declaration

We found that the isolated configuration began with an XML declaration (`<?xml …?>`), which the production configuration does not have. We remove the declaration from the isolated configuration only and test.

> **Run on: VM 220**

⟦C10⟧

With the declaration removed, the earlier configuration load error (1226) no longer appeared; the next error was `Permission denied` on `internal_options.conf`.

## 3.2 Permissions of the Internal Configuration Files

> **Run on: VM 220**

⟦C11⟧

⟦C12⟧

`internal_options.conf` in the isolated environment was `root:root`, `640`, and the cause was that the `wazuh` user, which Wazuh uses internally, could not read it.

## 3.3 Fixing the Permissions

We set only the two files in the isolated environment to `root:wazuh`, `640`.

> **Run on: VM 220**

⟦C13⟧

They are now readable by the `wazuh` user.

## 3.4 Testing Again

> **Run on: VM 220**

⟦C14⟧

**`wazuh-analysisd -t -D "$ROOT"` finished with exit code `0`.** Wazuh accepted the configuration including the candidate rules.

# Chapter 4: Final Check of the Candidate

> **Run on: VM 220**

⟦C15⟧

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

---
title: "AI Autonomous Cyber Defense System | Build Manual | Volume 4"
subtitle: "Part 58: Hardening Token Handling and the CLI"
author: "Isamu Tanaka"
lang: en-US
---

# Introduction

## About This Book

This is Part 58 of Volume 4 of the "AI Autonomous Cyber Defense System Build Manual". In Part 57 we built token authentication for the API and tested it in an independent environment. Before putting it into production, we examine token handling and the CLI in detail and fix the weaknesses found.

| Found | Fix |
|---|---|
| If the parent directory of the token file is a symbolic link, the file is created at its target and permissions are changed there | open directories in turn with `O_DIRECTORY` and `O_NOFOLLOW`, and create the file through `dir_fd` |
| A literal `\n` was written to the file instead of a newline | write a real newline |
| A non-string element in `scopes` in the DB causes `TypeError` | check first that elements are strings |
| Passing `True` as the expiry is accepted as 1 day | reject `bool` |
| An invalid JSON in `scopes` stops the listing | handle it without stopping the listing |
| A failure partway through writing leaves a partial token file | on failure, remove only that file |

Everything is tested with a temporary DB and temporary files; the production DB and tokens are not touched. The service is not restarted.

## Notation

- Commands and programs are shown exactly as they were used in the build. They have not been modified. (Only Japanese comments inside the code have been translated into English.)
- Where to run each step is shown in "Run on".
  - **VM 230**: ai-defense-manager (root)

# Chapter 1: Reading the CLI and Token Handling

## 1.1 The CLI

> **Run on: VM 230**

⟦C0⟧

`O_NOFOLLOW` applied only to the final file, so symbolic links in parent directories could be followed. Also, `os.chmod(directory, 0o700)` could change the permissions of an unintended directory.

## 1.2 Token Handling

> **Run on: VM 230**

⟦C1⟧

We confirmed random values equivalent to 256 bits, storing only SHA-256 hashes, `hmac.compare_digest`, checks of scope/expiry/revocation, not showing secret values in listings, and rejecting scopes other than `read` and `analyze`. The CLI itself and the wrapper are owned by root, and the wrapper is `700`.

# Chapter 2: Fixing How the Token File Is Written

## 2.1 Testing the Current Method

Only dummy values are written to a temporary directory.

> **Run on: VM 230**

⟦C2⟧

`PARENT_SYMLINK_BEHAVIOR=FOLLOWED`; that is, we confirmed that if the parent directory is a symbolic link, the token file is created at its target.

## 2.2 Testing a Safe Method with Temporary Code

The production token location and DB are not touched.

> **Run on: VM 230**

⟦C3⟧

All 7 passed (rejecting symbolic links in parents and the final file, not overwriting existing files, new directories `0700`, files `0600`, not changing permissions of existing directories).

## 2.3 Integrating into the CLI

> **Run on: VM 230**

⟦C4⟧

## 2.4 Checking the Copy and Imports

The `sha256sum -c` at the end of the script above compares against the same path after the change, so it gives `FAIL`. We compare again against the pre-change copy itself.

> **Run on: VM 230**

⟦C5⟧

The integrity of the copy passed, and there were no problems importing `os`, `stat` and `Path`. Reading the source, `stream.write(token + "\\n")` was written so that it writes the characters `\n` rather than a newline.

## 2.5 Fixing the Newline and Retesting

> **Run on: VM 230**

⟦C6⟧

All 7 passed (correct newline, `0600`, new directory `0700`, no overwriting, symbolic links rejected, link targets unaffected).

# Chapter 3: Checking Scope Types

## 3.1 The Current Check

> **Run on: VM 230**

⟦C7⟧

The following check could raise `TypeError: unhashable type` if the `scopes` array contains dictionaries or lists.

⟦C8⟧

## 3.2 Reproducing It

> **Run on: VM 230**

⟦C9⟧

`TypeError` occurred for both `DICT_SCOPE` and `LIST_SCOPE`. This means invalid authentication data would cause a `500` error.

## 3.3 Fixing

We check first that elements are strings, then compare against the allowlist.

> **Run on: VM 230**

⟦C10⟧

All 6 passed (valid scopes pass, disallowed scopes are rejected, dictionaries, lists and the like are rejected without exceptions, and invalid JSON is also rejected).

# Chapter 4: Expiry, Listing and Write Failures

## 4.1 Testing Edge Values

> **Run on: VM 230**

⟦C11⟧

- In Python, `bool` is a kind of `int`, so `True` is accepted as an expiry of 1 day
- If `scopes` in the DB is invalid JSON, `list_tokens()` stops with `JSONDecodeError`

## 4.2 Fixing Expiry and Listing

> **Run on: VM 230**

⟦C12⟧

| Checked | Result |
|---|---|
| Rejecting `True` and `False` as expiry | passed |
| 1, 90, 365 days | passed |
| Rejecting 0 and 366 days | passed |
| Listing that includes invalid JSON | passed |
| Listing that includes invalid scope types | passed |
| No secrets in the listing | passed |

All 10 passed.

## 4.3 When Writing Fails

> **Run on: VM 230**

⟦C13⟧

If writing the file fails during issuance, the issued token is revoked and the CLI exits with an error, but a partial file could be left behind.

> **Run on: VM 230**

⟦C14⟧

`_write_token_file()` had no step to remove the file when `write()`, `flush()` or `fsync()` failed after the file was created.

## 4.4 Removing the Partial File on Failure

If an exception occurs after newly creating the file, only that file is removed using the FD of the same directory. Existing files and symbolic links are not removed.

> **Run on: VM 230**

⟦C15⟧

We actually caused `fsync()` to fail and confirmed that the partial file is removed, and that on success the contents are saved with `0600` (all 6 passed).

# Chapter 5: Whole Tests and the Final Check

## 5.1 Token Lifecycle Tests (17 Cases)

> **Run on: VM 230**

⟦C16⟧

On successful authentication `last_used_at` is updated; insufficient scope raises `PermissionError`; invalid or revoked tokens give `False`. We check with a temporary SQLite DB. Token plaintext and hashes are not displayed.

> **Run on: VM 230**

⟦C17⟧

All 17 passed (ID format and issuing, storing as hashes, passing with the correct scope, rejecting insufficient scope, rejecting invalid and unknown tokens, updating last-used time, revocation and more).

## 5.2 Tests Through the CLI (14 Cases)

> **Run on: VM 230**

⟦C18⟧

| Operation | Result |
|---|---|
| `issue` | issued; secret file saved with `0600` |
| `list` | shows IDs, does not show plaintext tokens |
| `revoke` | revoked successfully |
| `revoke` again | `NO_CHANGE` |
| Authentication after revocation | rejected |

All 14 passed. The independent tests of the service and the CLI, 31 in total (17 and 14), all passed.

## 5.3 Final Check Before Production

> **Run on: VM 230**

⟦C19⟧

| Check | Result |
|---|---|
| Syntax of all Python | passed |
| `/api/v1/wazuh/events`: `read` | passed |
| `/api/v1/analysis`: `analyze` | passed |
| `/api/v1/wazuh/analyze`: `analyze` | passed |
| `/health` | still outside authentication |
| Swagger, ReDoc, OpenAPI | disabled |
| Service | `active (running)`; not restarted |

`app/main.py` and `app/api/wazuh.py` are `root:ai-defense`, `640`, while some authentication files are `root:root`, `644`; they are not uniform. In both cases the service account can read but not write them, so we do not change them now.

# Closing Notes

In Part 58 we fixed weaknesses in token handling and the CLI, and are ready for production.

| Item | Result |
|---|---|
| Token file | rejects symbolic links, no overwriting, `0600` and directory `0700`; removes partial files on failure |
| Scopes and expiry | types checked, no stopping on exceptions; expiry 1–365 days |
| Listing | does not stop on broken data and does not show secret values |
| Tests | 31 in total (plus tests of each fix), all passed |
| Production | not yet deployed |

In the next part, Part 59, we create the authentication table in the production DB, issue tokens, and deploy to the service.

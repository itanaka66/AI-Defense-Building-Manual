---
title: "AI自律型サイバー防御システム 構築マニュアル 第4巻"
subtitle: "第69部　直したルールを本番に入れる"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」第4巻の第69部です。第68部で、直した `local_rules.xml` の候補を隔離した環境で確かめました。ここでは本番に入れます。

1. いまの `local_rules.xml` を控え、候補と一度に置き換える
2. 本番の設定で `wazuh-analysisd -t` を行う
3. `wazuh-logtest` で、PostgreSQL のルールが期待どおりに発火するかを試す
4. Wazuh Manager の reload が何をするかを調べ、1回だけ行って、ルールを読み込ませる

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **VM 220**：security-core（root）

# 第1章　本番のファイルを置き換える

## 1.1　置き換える

いまの `local_rules.xml` を属性・権限ごと控え、確かめた候補と一度に置き換えます。Manager の再起動・reload、そのほかの設定の変更はしません。

> **実行先：VM 220**

⟦C0⟧

| 項目 | 結果 |
|---|---|
| 新しい `local_rules.xml` | 候補と同じ SHA256 |
| 古いファイル | 控えに完全に保存 |
| 所有者・権限 | `wazuh:wazuh`・`660` |
| XML の読み取り | 合格 |
| ルールの ID | 8つとも残っている |

## 1.2　本番の設定で検査する

> **実行先：VM 220**

⟦C1⟧

本番の `wazuh-analysisd -t` は終了コード `0` で、直した `local_rules.xml` を含む本番の設定の全体が Wazuh の検査を通りました。

## 1.3　動いているプロセス

> **実行先：VM 220**

⟦C2⟧

`wazuh-manager.service` は `active (running)`、`wazuh-analysisd` は PID `1721` で動いていました。動いているプロセスに新しいルールが読み込まれたかは、まだわかりません。

# 第2章　ルールの動きを試す

`wazuh-logtest` で、試験用のイベントを1件ずつ入れます。実際の PostgreSQL のログやほかのシステムには影響しません（IP アドレスは文書用の `192.0.2.10` を使います）。

## 2.1　認証の失敗（100101）

> **実行先：VM 220**

⟦C3⟧

デコーダーは `json`、ルール `100101`、Level `8` でした。

## 2.2　ブルートフォース（100106）

同じ IP から5回続けて入れます。

> **実行先：VM 220**

⟦C4⟧

| 回 | ルール・Level |
|---|---|
| 1〜4回目 | 100101・8 |
| 5回目 | 100106・12（frequency 5、MITRE ATT&CK T1110 Brute Force） |

## 2.3　PANIC（100105）

> **実行先：VM 220**

⟦C5⟧

## 2.4　FATAL（100102）

> **実行先：VM 220**

⟦C6⟧

## 2.5　ERROR（100103）

> **実行先：VM 220**

⟦C7⟧

## 2.6　WARNING（100104）

> **実行先：VM 220**

⟦C8⟧

| ルール | イベント | Level | 結果 |
|---|---|---:|---|
| 100101 | 認証の失敗 | 8 | 合格 |
| 100106 | 同じ IP から5回の認証の失敗 | 12 | 合格 |
| 100105 | PANIC | 12 | 合格 |
| 100102 | FATAL | 10 | 合格 |
| 100103 | ERROR | 7 | 合格 |
| 100104 | WARNING | 4 | 合格 |

# 第3章　Wazuh Manager に読み込ませる

## 3.1　reload が何をするか

> **実行先：VM 220**

⟦C9⟧

⟦C10⟧

systemd のユニットには次の `ExecReload` がありました。

⟦C11⟧

> **実行先：VM 220**

⟦C12⟧

`wazuh-control` の reload は、次のように、`wazuh-execd` を除いて `restart_service` を呼びます。

⟦C13⟧

`.restart` の印を作り、`testconfig` で設定を確かめ、対象のデーモンを止めてから起動し、印を消します。`wazuh-analysisd`・`wazuh-remoted`（エージェントの通信）・`wazuh-logcollector`・`wazuh-modulesd`・`wazuh-db`・`wazuh-authd` などが止まって起動し直すので、**ルールだけを読み直すのではなく、Manager の広い範囲のデーモンの再起動**です。エージェントとの通信にも一時的に影響します。

## 3.2　reload の前の状態を記録する

> **実行先：VM 220**

⟦C14⟧

| 項目 | 状態 |
|---|---|
| Wazuh Manager | `active (running)`、NRestarts 0 |
| Analysisd | PID `1721` |
| エージェント | 4台すべて Active |
| `local_rules.xml` | 直したあとの SHA256 と一致 |

## 3.3　reload を1回行う

> **実行先：VM 220**

⟦C15⟧

reload は終了コード `0` で、Manager は `active (running)`、`wazuh-analysisd` は PID `1721` から `60112`（新しいプロセス）に変わり、NRestarts は 0 のままでした。直後は、エージェント 002（`lxc-prometheus`）が `Pending` でした。

## 3.4　エージェントとルールの状態

> **実行先：VM 220**

⟦C16⟧

エージェント 002 も Active に戻り、4台すべて正常で、Manager のエラーのログもありませんでした。

## 3.5　ルールの読み込みの記録

> **実行先：VM 220**

⟦C17⟧

⟦C18⟧

新しい `wazuh-analysisd`（PID `60112`）が起動し、ルールを読み込んだことが記録されていました。

# おわりに

第69部で、直したローカルのルールを本番に入れ、Wazuh Manager に読み込ませました。

| 項目 | 結果 |
|---|---|
| `local_rules.xml` | 直したものに置き換えた（古いものは控えた）。`wazuh:wazuh`・`660` |
| 本番の検査 | `wazuh-analysisd -t` が `0` |
| ルールの試験 | 100101・100106・100105・100102・100103・100104 すべて合格 |
| reload | 1回（`wazuh-execd` 以外のデーモンを再起動）。analysisd は新しいプロセス、エージェント4台は Active |
| ルールの読み込み | `Total rules enabled: '8461'` |

> **運用の注意：** Wazuh Manager の reload は、エージェントの通信を含む広い範囲のデーモンを再起動します。行う前に状態を記録し、行ったあとにエージェントが Active に戻ったことを確かめます。

次の第70部では、AI Defense Manager の上に、AI 防御のエージェントを作り始めます。

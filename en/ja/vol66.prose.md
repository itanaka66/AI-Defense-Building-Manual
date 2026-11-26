---
title: "AI自律型サイバー防御システム 構築マニュアル 第4巻"
subtitle: "第66部　FSSの検証を15分ごとに自動で行う"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」第4巻の第66部です。第65部で、FSS で封印した journal を別のホストで確かめました。ここでは、VM 230 で FSS の検証を **15分ごとに自動で**行うようにします。

1. 既存の AI Defense Manager の作りを調べ、検証を組み込む場所を決める
2. どの journal を検証の対象にするかを、ヘッダーで分ける
3. 検証のスクリプト・systemd のサービス・タイマーを作り、1回だけ手で動かす
4. タイマーを有効にし、自動で動いたことを確かめる
5. 検証の結果を Wazuh に知らせられるかを調べる

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **VM 230**：ai-defense-manager（root。`aidefense` でログインしたときは `sudo -i` で root になる）

# 第1章　組み込む場所を決める

## 1.1　サービスの作り

> **実行先：VM 230**

⟦C0⟧

AI Defense Manager は動いていて（再起動 0）、FastAPI は `127.0.0.1:8000` だけで待ち受け、FSS に関係する systemd のタイマーはありませんでした。

## 1.2　アプリケーションの作り

root で実行します（`aidefense` だと `app`・`config`・`data` などが読めません）。

> **実行先：VM 230**

⟦C1⟧

`app/services/` に Wazuh との連携・分析の履歴などのサービスが、`app/api/` に Wazuh・分析の API がありましたが、スケジューラーや FSS を検証するモジュールはありませんでした。

## 1.3　サービスの安全の設定

> **実行先：VM 230**

⟦C2⟧

既存の API は `ProtectSystem=strict`・`ProtectHome=yes`・`RestrictAddressFamilies=AF_INET` で強く隔離されています。FSS の検証の鍵と journal は root 専用なので、`ai-defense` のユーザーに権限を足すことはしません。そこで、**既存の FastAPI のサービスには組み込まず、root で読み取りだけを行う別の検証のサービスと、systemd のタイマー**にします。

# 第2章　検証の対象を決める

## 2.1　journal のファイル

> **実行先：VM 230**

⟦C3⟧

system の journal のアーカイブが14個と、いまの journal がありました。

## 2.2　ヘッダーで分ける

> **実行先：VM 230**

⟦C4⟧

| 分類 | 数 | 自動の処理 |
|---|---:|---|
| FSS で封印したアーカイブ | 1 | 暗号の上で確かめる |
| FSS を入れる前の古いアーカイブ | 13 | 対象外として記録する（`SKIP`） |
| いまの system journal | 1 | 暗号の上で確かめる |

古いアーカイブ（`Tag objects` 0）は、`--verify-key` でもふつうの整合性の検査で `PASS` になり得るので、「検証の失敗」とも「FSS の合格」とも扱わず、`SKIP` にします。

## 2.3　いまの journal を基準として確かめる

> **実行先：VM 230**

⟦C5⟧

いまの journal は `ONLINE`・`SEALED`・`SEALED_CONTINUOUS`・`Tag objects` 8 で、検証は `PASS`（終了コード `0`）でした。「final 5min … entries not sealed」は、動いている journal の最後のまだ封印していない部分で、ふつうのことです。

# 第3章　検証の仕組みを作る

## 3.1　3つのファイルを作る

| ファイル | 内容 |
|---|---|
| `/usr/local/sbin/ai-defense-fss-verify` | 検証のスクリプト（`root:root`・`0750`） |
| `/etc/systemd/system/ai-defense-fss-verify.service` | oneshot のサービス、読み取りだけのサンドボックス（`0644`） |
| `/etc/systemd/system/ai-defense-fss-verify.timer` | 起動の5分後と、そのあと15分ごと（`0644`） |

対象は、ヘッダーに `SEALED` と `SEALED_CONTINUOUS` があり、`Tag objects` が1以上の system journal に限ります。同じパスにファイルがあれば、上書きせずに止まります。この段階では、`daemon-reload`・サービスの実行・タイマーの有効化はしません。

> **実行先：VM 230**

⟦C6⟧

> **注意：** このスクリプトは root で実行しないと、最初の確認で止まります（3つのファイルは作られません）。`aidefense` でログインしているときは、次で root になってから実行します。

⟦C7⟧

## 3.2　静的な点検

> **実行先：VM 230**

⟦C8⟧

| 検査 | 結果 |
|---|---|
| Bash の構文 | 合格 |
| systemd のユニットの構文 | 合格 |
| ファイルの所有者・権限 | 合格 |
| 検証の鍵を root だけが読む | 合格 |
| タイマー・サービス | `disabled`・`inactive`／`inactive` |
| 既存のサービスへの変更 | なし |

`--verify-key` に渡す値は、公開してよい側の検証の鍵で、秘密の封印の鍵ではありません。ただし、プロセスの引数に検証の鍵が現れることがあります。

## 3.3　登録して1回だけ手で動かす

タイマーは有効にしません。

> **実行先：VM 230**

⟦C9⟧

| 結果 | 数 |
|---|---:|
| 暗号の上の検証 `PASS` | 2（封印したアーカイブ・いまの journal） |
| 古いアーカイブ `SKIP` | 13 |
| 検証の失敗 | 0 |

サービスは終了コード `0`、systemd の結果は `success` でした。systemd のサンドボックスの中から、root 専用の鍵と journal を読んで検証できています。

# 第4章　タイマーを有効にする

## 4.1　有効にする

> **実行先：VM 230**

⟦C10⟧

中で行っているのは次の2つです。

⟦C11⟧

タイマーは `enabled`・`active` になりました。既存の `ai-defense-manager.service` も `active (running)`、PID `2340`、再起動 0 のままです。直後の表示は `Trigger: n/a`・`NEXT: -` でした。

## 4.2　自動で動いたかを確かめる

> **実行先：VM 230**

⟦C12⟧

| 項目 | 結果 |
|---|---:|
| 自動で動いた時刻 | 03:45:58 UTC（タイマーを起動した直後） |
| 暗号の上の検証 `PASS` | 2 |
| 古いアーカイブ `SKIP` | 13 |
| 検証の失敗 | 0 |
| サービスの終了 | `0`（`Result=success`） |
| タイマー | `active (waiting)`、次は約14分後 |

`OnBootSec=5min` の条件はすでに過ぎていたので、タイマーを起動したときに最初の実行が行われ、そのあと15分ごとに動きます。`ExecMainCode=1` はプロセスがふつうに終わったという意味で、終了のステータスは `ExecMainStatus=0` です。

# 第5章　Wazuh に知らせられるか

検証が失敗した（`VERIFY_FAIL`・`HEADER_ERROR`・`FATAL`）ことを Wazuh で見つけられるかを、読み取りだけで調べます。

> **実行先：VM 230**

⟦C13⟧

| 調べたこと | 結果 |
|---|---|
| `wazuh-agent` のパッケージ | 入っていない |
| エージェントのサービス・プロセス | 無い |
| `ossec.conf` | 無い |
| journald を集める設定 | 無い |
| FSS の検証のタイマー | 有効で動いている |

VM 230 には Wazuh のエージェントが無く、FSS の検証の結果を Wazuh Manager（VM 220）に送る仕組みはまだありません。検証の機能の問題ではなく、連携の経路がまだ無いという状態です。

# おわりに

第66部で、FSS の検証を15分ごとに自動で行うようにしました。

| 項目 | 結果 |
|---|---|
| 検証のスクリプト | `/usr/local/sbin/ai-defense-fss-verify`（`0750`） |
| サービス・タイマー | `ai-defense-fss-verify.service`（oneshot、読み取りだけ）・`.timer`（起動の5分後、そのあと15分ごと） |
| 対象 | `SEALED`・`SEALED_CONTINUOUS`・`Tag objects` 1以上の system journal（古いものは `SKIP`） |
| 結果 | `PASS` 2・`SKIP` 13・失敗 0（手で1回、自動で1回） |
| Wazuh への連携 | VM 230 にエージェントが無く、まだ無い |

次の第67部では、連携の前に VM 220 の Wazuh Manager の側を調べます。そこで、Wazuh のローカルのルールのファイルに問題が見つかります。

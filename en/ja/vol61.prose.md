---
title: "AI自律型サイバー防御システム 構築マニュアル 第4巻"
subtitle: "第61部　ログの秘密の点検とjournalの容量の上限"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」第4巻の第61部です。第60部で、API のエラーの応答とログの権限を点検しました。ここでは次のことを行います。

1. syslog・journal に、トークンのような文字列が残っていないかを、数だけで調べる
2. journal の保存の期間と増え方を調べ、容量の上限を決めて設定する
3. journald を再起動して設定を反映し、journal の整合性を確かめる
4. journald・rsyslog・logrotate のログの管理の全体を点検する

ログの本文は表示しません。既存のログは消しません。

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **VM 230**：ai-defense-manager（root）

# 第1章　ログに秘密が残っていないか

## 1.1　いまの syslog・auth.log

一致した数だけを数えます。

> **実行先：VM 230**

⟦C0⟧

トークンの形・秘密の情報の形の一致は **0件**、試験に使った文字列 `VALIDATION_SECRET_MARKER` も0件でした。AI Defense に関係するログは syslog に14,184件、auth.log に830件ありますが、秘密の情報が入っているという意味ではありません。

## 1.2　切り替えたあとのログ

> **実行先：VM 230**

⟦C1⟧

| 対象 | トークンの形 | 試験の文字列 |
|---|---:|---:|
| syslog | 0 | 0 |
| syslog.1 | 0 | 0 |
| auth.log | 0 | 0 |
| auth.log.1 | 0 | 0 |

## 1.3　journal

> **実行先：VM 230**

⟦C2⟧

journal でも一致は0件でした。使っている量は 89.0MB、ファイルシステムの空きは 39GB（使用率15%）です。調べた形のほかの、知らない形の秘密の情報まで無いとは言えません。

# 第2章　journal の設定と保存の期間

## 2.1　いまの設定

> **実行先：VM 230**

⟦C3⟧

| 設定 | いま |
|---|---|
| Storage | `auto`（既定） |
| Compress | `yes`（既定） |
| Seal | `yes`（既定） |
| SystemMaxUse | 指定なし |
| SystemKeepFree | 指定なし |
| SystemMaxFiles | 既定の100 |
| MaxRetentionSec | 指定なし |

容量の上限は、はっきり決めておらず、systemd の既定に任せている状態でした。

## 2.2　保存の状態と整合性

> **実行先：VM 230**

⟦C4⟧

永続の保存は `/var/log/journal`、ファイルは17個（異常に終わったときの `.journal~` が1個）、すべて `root:systemd-journal`・`640`、整合性の検査は表示されたファイルすべて合格でした。`Unused data (entry_offset==0)` は、使われていないデータがあるという知らせで、壊れているという意味ではありません。

## 2.3　何日分あるか

> **実行先：VM 230**

⟦C5⟧

⟦C6⟧

| 項目 | 結果 |
|---|---|
| 最も古い記録 | 2026-11-20 07:38:48 UTC |
| 最も新しい記録 | 2026-11-23 23:10:13 UTC |
| 期間 | 約4日 |
| 記録の数 | 46,133 |
| 起動の履歴 | 11回 |
| 使っている量 | 89MB |

# 第3章　容量の上限を設定する

## 3.1　変える前の確認

> **実行先：VM 230**

⟦C7⟧

systemd は 255.4 で、使う設定の項目に対応していました。ローカルの drop-in も、容量の設定もまだありません。`systemd-journald.service` は `Restart=always` ですが、設定を反映するための再起動は別に判断します。決めた値は次のとおりです。

⟦C8⟧

## 3.2　設定のファイルを足す

既存のログの削除・変更、journald の再起動・reload はしません。

> **実行先：VM 230**

⟦C9⟧

| 設定 | 実効の値 |
|---|---:|
| `SystemMaxUse` | 512MB |
| `SystemKeepFree` | 2GB |
| `SystemMaxFileSize` | 64MB |

ファイルは `/etc/systemd/journald.conf.d/60-ai-defense-retention.conf`（`root:root`・`644`）です。journald の PID は変わっていません（まだ動いているプロセスには反映されていない）。

## 3.3　反映の前の点検

> **実行先：VM 230**

⟦C10⟧

いまの使用量 89.0MB は上限の 512MB より十分に小さいので、反映してもすぐに古いログが消されることはありません。

## 3.4　journald を再起動する

短い間、ログの収集に影響することがあります。既存のログの削除（vacuum）や設定の変更はしません。

> **実行先：VM 230**

⟦C11⟧

| 項目 | 結果 |
|---|---|
| 再起動 | 成功（status 0） |
| 新しい MainPID | `2572` |
| 状態 | `active (running)`、Result `success`、NRestarts 0 |
| 上限・空き・ファイルの上限 | 512MB・2GB・64MB |
| journal の起動の記録 | あり |

## 3.5　再起動のあとの整合性

> **実行先：VM 230**

⟦C12⟧

| 確かめたこと | 結果 |
|---|---:|
| journal のファイルの検査 合格 | 18件 |
| journal のファイルの検査 不合格 | 0件 |
| `Unused data` の知らせ | 31件 |
| journald のエラー・警告 | 0件 |
| AI Defense Manager | `active (running)`、再起動 0、`/health` は `HTTP 200` |

# 第4章　ログの管理の全体

## 4.1　保存の場所と logrotate

> **実行先：VM 230**

⟦C13⟧

`/var/log/journal`・`/run/log/journal` は `root:systemd-journal`・`2755`、journal のファイルは `640` で、logrotate が journal を直接さわる設定はありませんでした。

## 4.2　容量と保存の期間

> **実行先：VM 230**

⟦C14⟧

⟦C15⟧

| 項目 | 結果 |
|---|---|
| 最も古い記録 | 2026-11-20 07:38:48 UTC |
| 最も新しい記録 | 2026-11-23 23:17:01 UTC |
| 期間 | 約3日15時間38分 |
| ディスクの空き | 39GB |
| inode の使用率 | 4% |

## 4.3　logrotate

> **実行先：VM 230**

⟦C16⟧

⟦C17⟧

| 項目 | 結果 |
|---|---|
| logrotate | 3.21.0 |
| 周期・世代 | 毎週・4世代 |
| 圧縮 | gzip、`delaycompress` |
| 空のログ | 切り替えない |
| rsyslog の対象 | 6種類、postrotate で rsyslog に知らせる |
| 重複した定義 | なし |
| ログの所有者・権限 | `syslog:adm`・`640` |

## 4.4　rsyslog

> **実行先：VM 230**

⟦C18⟧

rsyslog は `active (running)`（MainPID `774`、再起動 0、`syslog` のユーザー）、`rsyslogd -N1` の構文の検査は合格、journald からの転送（`ForwardToSyslog=yes`）・auth.log と syslog の振り分けは正常で、エラーはありませんでした。

# おわりに

第61部で、ログに秘密の情報が残っていないことを確かめ、journal の容量の上限を設定しました。

| 項目 | 結果 |
|---|---|
| ログの秘密の点検 | syslog・auth.log・journal の一致は0件 |
| journal の上限 | `SystemMaxUse=512M`・`SystemKeepFree=2G`・`SystemMaxFileSize=64M`（`60-ai-defense-retention.conf`） |
| 反映 | journald を再起動、整合性の検査は18件合格・不合格0 |
| syslog | 週ごと・4世代・圧縮、`syslog:adm`・`640` |

journald の設定に `Seal=yes`（既定）とありましたが、実際に封印の鍵が使われているかは、次の第62部で確かめます。ログの改ざんを見つけられるようにするためです。

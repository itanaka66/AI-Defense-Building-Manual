---
title: "AI自律型サイバー防御システム 構築マニュアル 第4巻"
subtitle: "第49部　Relayが返す項目を7つに絞る"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」第4巻の第49部です。第48部で、VM 230 の AI Defense Manager が Wazuh のイベントを7項目に絞って受け取り、`rule.groups` で分類するように変えました。ここでは、VM 220 の中継 API（Relay）が返すデータを、それに合わせます。

1. ポート 8765 で待ち受けている Relay と、その実装のファイルを特定する
2. Relay の返すデータと、VM 230 が期待する形を比べる
3. `relay.py` を控えてから、返す項目を7つに限り、`rule.groups` を確かめる処理を足す
4. 差分を確かめ、Relay のサービスだけを再起動する

Relay の再起動のほかは、Indexer への通信や VM 230 からの実際の通信はしません。

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **VM 220**：security-core（root）

# 第1章　Relay を調べる

## 1.1　ポート 8765 のサービス

認証の情報やプロセスの引数は表示しません。

> **実行先：VM 220**

⟦C0⟧

`192.168.0.220:8765` で待ち受けているのは、動いている `ai-defense-relay.service` でした。

## 1.2　実装のファイル

> **実行先：VM 220**

⟦C1⟧

実装は `/opt/ai-defense-relay/relay.py` でした。

## 1.3　返すデータの作り方

ファイル全体ではなく、ルートの定義・JSON の生成・イベントの正規化に関係するところだけを取り出します。トークンや秘密の鍵は表示しません。

> **実行先：VM 220**

⟦C2⟧

VM 230 の新しい `_convert_alert()` は `rule.groups` を必須にしていますが、Relay は次の状態でした。

| 項目 | いま | 必要な状態 |
|---|---|---|
| `timestamp`・`agent.id`・`rule.level`・`rule.description`・`rule.id`・`decoder.name` | 取って返す | そのまま |
| `rule.groups` | **取っていない** | 足す |
| `agent.ip`・`agent.name`・`manager.name`・`location` | 取って返す | **除く** |

# 第2章　Relay を直す

## 2.1　控える

サービスは止めず、通信もしません。

> **実行先：VM 220**

⟦C3⟧

控えは `/var/backups/ai-defense-relay/20261123-044701/relay.py` で、SHA256 は元と一致し、所有者・権限は `root:ai-defense-relay`・`640` です。

## 2.2　直す場所を読む

> **実行先：VM 220**

⟦C4⟧

## 2.3　直す

直すのは次の3つです。

1. `ALLOWED_FIELDS` を7項目に限り、`agent.ip`・`agent.name`・`manager.name`・`location` を取らない
2. `sanitize_alert()` に、`rule.groups` がリストであることなどを確かめる処理を足す。正しくないイベントは除き、ほかの正しいイベントの処理は続ける
3. 確かめて除いたイベントを、返す `alerts` に入れない

`decoder.name` は Relay では確かめて通しますが、VM 230 から AI には送りません。控えを確かめてから直し、書き込む前に構文の検査と合成したデータの試験を行います。

> **実行先：VM 220**

⟦C5⟧

| 確かめたこと | 結果 |
|---|---|
| 書き込む前の構文・許可リスト | 合格 |
| 合成したデータ（正しいイベント・正しくないイベント） | 合格 |
| `ALLOWED_FIELDS` | 7項目 |
| `rule.groups` | リストの型・要素の数・文字の数・文字の種類を確かめる |
| 返さない項目 | `agent.ip`・`agent.name`・`manager.name`・`location`・`full_log`・`data` |
| 所有者・権限 | `root:ai-defense-relay`・`640` のまま |

## 2.4　差分を確かめる

> **実行先：VM 220**

⟦C6⟧

| 確かめたこと | 結果 |
|---|---|
| 許可した7項目 | 合格 |
| 禁止した項目を取らない | 合格 |
| `rule.groups` の確認と正規化 | 合格 |
| 正しくないイベントを除く・返さない | 合格 |
| Python の構文の検査 | 合格 |
| 所有者・権限・控え | 合格 |

`DIFF_EXIT=1` は、控えと意図した差分があることを表します。

# 第3章　Relay を再起動する

## 3.1　再起動

VM 220 の Relay のサービスだけを再起動します。

> **実行先：VM 220**

⟦C7⟧

| 項目 | 結果 |
|---|---|
| 再起動 | 成功（終了コード `0`） |
| 状態 | `active`・`running` |
| 新しい MainPID | `17052` |
| 実行のユーザー | `ai-defense-relay` |
| 作業のディレクトリ | `/opt/ai-defense-relay` |

## 3.2　待ち受けを確かめる

> **実行先：VM 220**

⟦C8⟧

`192.168.0.220:8765` で待ち受け、systemd は `active (running)`、動いているプロセスとサービスの PID は同じでした。VM 220 の Relay は、新しい7項目の処理で動いています。

# おわりに

第49部で、Relay が返すデータを VM 230 の受け取る形に合わせました。

| 項目 | 結果 |
|---|---|
| 実装 | `/opt/ai-defense-relay/relay.py` |
| 控え | `/var/backups/ai-defense-relay/20261123-044701/relay.py` |
| 返す項目 | 7項目（`timestamp`・`rule.id`・`rule.level`・`rule.groups`・`rule.description`・`decoder.name`・`agent.id`） |
| 正しくないイベント | 除いて返さない |
| Relay | 再起動して新しいコードで動いている |
| VM 230 | コードは直したが、サービスはまだ再起動していない |

VM 230 のサービスを再起動する前に、VM 230 のアドレスを DHCP から固定のアドレスに変えます。次の第50部で行います。

---
title: "AI自律型サイバー防御システム 構築マニュアル 後編"
subtitle: "第35部　アラートのルールの試験と本番での確認"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」後編の第35部です。第33部・第34部で、Collector 用の9つと Wazuh 本体用の7つ、あわせて16のアラートのルールを Prometheus に入れました。ただし、いまは異常がないので、ルールが本当に発報するかはまだわかりません。

ここでは、**本番のサービスを止めずに**ルールを試します。Prometheus の `promtool test rules` は、試験用の時系列のデータをファイルに書いておき、そのデータでルールを評価して、決めておいた結果と比べる道具です。

1. Wazuh 本体用の7つのルールについて、正常のときに発報しないこと、異常のときに発報することを試す
2. 本番の Prometheus で、実際の値と16のルールの状態を確かめる

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **pve**：Proxmox のホスト（root）。LXC 103（`lxc-prometheus`）の中のコマンドは `pct exec 103 -- …` で実行します

# 第1章　ルールの試験の準備

## 1.1　promtool の機能

> **実行先：pve**

⟦C0⟧

promtool は 3.12.0 で、`test rules` が使えます。

## 1.2　試験のファイル

7つのルールを、次の4つの場面で試します。

| 場面 | 入れるデータ | 決めておく結果 |
|---|---|---|
| `normal-no-alerts` | すべて 1、`.prom` も新しい | 7つとも発報しない |
| `service-down-alerts` | Manager・デーモン・Indexer・Dashboard・API がすべて 0 | 5つのルールが発報する |
| `metrics-missing-alert` | API の数値だけがない | `WazuhPlatformMetricsMissing` が発報する |
| `metrics-stale-alert` | `.prom` の更新時刻が古い | `WazuhPlatformMetricsStale` が発報する |

試験のファイルは `/tmp` に置き、本番のルールのファイルは変えません。

⟦C1⟧

ファイルは `-rw-r--r-- root:root 4001 bytes` で作られました。最後の Python での YAML の確かめは、LXC 103 に `python3-yaml` が入っていないため `ModuleNotFoundError: No module named 'yaml'` になりますが、問題ありません。YAML の読み込みは、次の `promtool test rules` が行います（パッケージは足しません）。

# 第2章　ルールを試す

## 2.1　1回目

⟦C2⟧

`FAILED`（`PROMTOOL_TEST_EXIT=1`）でした。中身を見ると、**7つの異常のルールはどれも期待どおりに発報していて**、正常の場面の「発報しない」も合っていました。合わなかったのは、試験のファイルで `exp_annotations`（`summary`・`description`）を書いていなかったためです。promtool は、実際のアラートに付く注釈まで比べます。

## 2.2　期待する注釈を足す

まず、試験のファイルの該当の部分を読みます。

⟦C3⟧

異常の場面の期待値は `exp_labels` の下にあります。それと同じ高さに `exp_annotations` を足します。正常の場面の `exp_alerts: []` はそのままです。注釈の文は、本番のルール（第34部）と同じものにします。

⟦C4⟧

`ANNOTATIONS_ADDED: 7`、`exp_annotations:` の数も `7` でした。

## 2.3　2回目

1回目と同じコマンドで試します。

⟦C5⟧

⟦C6⟧

| 試したこと | 結果 |
|---|---|
| 正常のときに発報しない（7つ） | 合格 |
| Manager の停止 | 合格 |
| Manager のデーモンの停止 | 合格 |
| Indexer の停止 | 合格 |
| Dashboard の停止 | 合格 |
| API の停止 | 合格 |
| 数値が届かない | 合格 |
| `.prom` が古い | 合格 |

これは試験用のデータによる試験で、本番のサービスや数値は変えていません。

# 第3章　本番の値を確かめる

## 3.1　Wazuh 本体と16のルール

本番の Prometheus に、いま集めている値を問い合わせます（読み取りだけ）。

> **注意**：Python の中の文字列に `'` を使うと、`pct exec 103 -- python3 -c '…'` の外側の `'` とぶつかって、途中から bash のコマンドとして実行されてしまいます（`syntax error near unexpected token` が並びます）。次のコマンドは、Python の中で `'` を使わない形にしています。入力が `>` の続きの状態で止まったら、`Ctrl+C` で抜けてから実行します。

⟦C7⟧

| 項目 | 実際の値 |
|---|---|
| Node Exporter（`192.168.0.220:9100`） | `UP= 1` |
| Wazuh Manager・Indexer・Dashboard・API | すべて `1` |
| Manager のデーモン | 9つすべて `1` |
| `wazuh_platform.prom` の古さ | 約16.3秒 |
| アラートのルール | 16（すべて `health=ok`・`state=inactive`） |
| 発報中のアラート | 0 |

## 3.2　Collector の値

⟦C8⟧

| メトリクス | 実際の値 |
|---|---:|
| `wazuh_collector_service_up` | 1 |
| `wazuh_collector_restarts_total` | 0 |
| `wazuh_collector_state_valid` | 1 |
| `wazuh_collector_inode_match` | 1 |
| `wazuh_collector_unread_bytes` | 0 |
| `wazuh_collector_state_mtime_seconds` | 取れている |

# おわりに

第35部で、アラートのルールを試し、本番の値を確かめました。

| 項目 | 結果 |
|---|---|
| 試験のファイル | `/tmp/wazuh-platform-alerts.test.yml`（本番のルールは変えていない） |
| ルールの試験 | `promtool test rules` で `SUCCESS`（正常の7項目・異常の7項目） |
| 1回目の失敗の理由 | 試験のファイルに期待する注釈（`exp_annotations`）がなかった |
| 本番の値 | Wazuh 本体・9つのデーモン・Collector とも正常 |
| ルール | 16すべて `ok`・`inactive`、発報 0 |
| 通知 | Alertmanager は未設定（意図して保留） |

これで、Wazuh・Collector・Prometheus のルールまでの監視の基盤ができました。次の第36部では、イベントを保存している PostgreSQL を、読み取りだけで点検します。

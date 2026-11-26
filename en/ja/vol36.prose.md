---
title: "AI自律型サイバー防御システム 構築マニュアル 後編"
subtitle: "第36部　PostgreSQLの点検"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」後編の第36部です。第35部までで、Wazuh・Collector・Prometheus のルールまでの監視の基盤ができました。ここでは、Collector がイベントを保存している **PostgreSQL**（LXC 109、192.168.0.151、データベース `security_workbench`、テーブル `incident.alert_events`）を、**読み取りだけで**点検します。

| 点検すること | 結果 |
|---|---|
| つながるか | 正常 |
| Collector のロール（`wazuh_collector`）の権限 | INSERT だけ。管理者の権限なし |
| テーブルの形（主キー・インデックス・制約） | 正常 |
| データの中身（重複・形の誤り） | 55,811 件、異常 0 |
| 取り込みの遅れ | 直近30分は平均 0.86 秒 |
| 容量・VACUUM・接続の数 | 正常 |
| WAL・チェックポイント | 正常。WAL のアーカイブは未設定 |
| バックアップ | **PostgreSQL のバックアップが見当たらない** |

最後の項目が、次の第37部で扱う課題になります。

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **VM 220**：security-core（root）
  - **postgresql**：LXC 109（192.168.0.151、root）。SQL は `sudo -u postgres psql …` で実行します

# 第1章　接続と Collector の設定

## 1.1　つながるか

> **実行先：VM 220**

⟦C0⟧

⟦C1⟧

## 1.2　Collector がつなぐ先

Collector の `DB_CONFIG` から、接続先の項目だけを取り出します。`DB_CONFIG` には環境変数などを参照する値もあるため、ファイルを Python の構文として読み、決まった項目（`host`・`hostaddr`・`port`・`dbname`・`database`・`user`）の値だけを表示します。パスワードなどは表示しません。

⟦C2⟧

⟦C3⟧

# 第2章　テーブルと権限

## 2.1　テーブルの形

> **実行先：postgresql**

⟦C4⟧

| 項目 | 結果 |
|---|---|
| 主キー | `event_id`（同じイベントを二重に入れられない） |
| インデックス | 5つ |
| CHECK 制約 | 3つ（`rule_level` は 0〜16、`srcport` は 0〜65535、`mitre` は JSON のオブジェクト） |
| 生のログの列 | なし（`full_log` などは持たず、決まった項目だけを保存する作り） |

## 2.2　Collector のロールの権限

⟦C5⟧

⟦C6⟧

Collector はイベントを書き込めますが、すでにあるデータを読む・変える・消すことはできません。Collector が乗っ取られても、保存済みのイベントを書き換えられにくくする大事な守りです。

⟦C7⟧

`can_login` だけが `t` で、スーパーユーザー・ロールの継承・ロールや DB を作る権限・複製・RLS を超える権限は、すべて `f` でした。この権限は変えません。

# 第3章　データの中身

## 3.1　形の誤りと重複

個々のイベント（IP アドレスやエージェントの名前など）は表示せず、集計の値だけを見ます。

⟦C8⟧

| 項目 | 結果 |
|---|---:|
| 件数 | 55,811 |
| 異なる `event_id` | 55,811 |
| ルールのレベル・送信元のポート・MITRE の形の誤り | 0 |
| ルールのグループが空 | 0 |
| 未来の日時・取り込みが先になっている | 0 |
| 最後の取り込みからの時間 | 137.03 秒 |
| 取り込みの遅れの平均 | 19,468.776 秒 |

平均の遅れが約5時間半と大きく出ていますが、第32部で過去のアーカイブをあとから入れた分が平均を押し上げていると考えられます。期間ごとに分けて見ます。

## 3.2　期間ごとの取り込みの遅れ

> **メモ**：PostgreSQL では、同じ SELECT の中で付けた別名（`ingestion_period`）を、`ORDER BY` の中の `CASE` から参照できません（`column "ingestion_period" does not exist` になります）。次のコマンドは、先に CTE（`WITH`）で期間を決めてから集計しています。

⟦C9⟧

| 期間 | 件数 | 平均 | 中央値 | 95% |
|---|---:|---:|---:|---:|
| 直近30分 | 15 | 0.86 秒 | 0.91 秒 | 0.99 秒 |
| 直近24時間（30分を除く） | 35,705 | 18,587.53 秒 | 1.07 秒 | 322,119.38 秒 |
| それより前 | 20,098 | 21,042.09 秒 | 11,725.46 秒 | 61,876.70 秒 |

直近30分は1秒もかからずに取り込まれていて、いまの取り込みは正常です。24時間の中央値も約1秒で、平均が大きいのは、あとから入れた古いイベントがあるためです。

# 第4章　容量と接続

## 4.1　テーブルの大きさと VACUUM

⟦C10⟧

テーブルは 12MB、インデックスは 6008kB、あわせて 18MB でした。生きている行は約 55,826、不要な行は 766（約1.4%）で、自動の VACUUM と ANALYZE も動いていました。手で VACUUM をする必要はありません。

## 4.2　接続の数

⟦C11⟧

上限 100 に対して 14 の接続で、`idle in transaction`（トランザクションを開いたまま止まっている接続）は 0、Collector の接続は 1 でした。

## 4.3　データベースの大きさ

⟦C12⟧

`security_workbench` 全体で 26MB でした。

# 第5章　WAL とチェックポイント

## 5.1　レプリケーションのスロット

使われていないスロットがあると、WAL が消されずにたまり続けます。

⟦C13⟧

スロットは 0 でした。

## 5.2　WAL とチェックポイントの設定

⟦C14⟧

| 設定 | 値 |
|---|---|
| `wal_level` | `replica` |
| `max_wal_size` / `min_wal_size` | 1GB / 80MB |
| `checkpoint_timeout` | 300 秒 |
| `checkpoint_completion_target` | 0.9 |
| `full_page_writes` | `on` |
| `synchronous_commit` | `on` |
| `archive_mode` | `off` |
| `wal_keep_size` | 0 |

障害のときの整合性とコミットの確かさに関わる `full_page_writes` と `synchronous_commit` は、どちらも `on` です。一方、`archive_mode` が `off` のため、WAL のアーカイブを使って好きな時点に戻す復旧（PITR）はできません。

## 5.3　チェックポイントの実績

> **メモ**：PostgreSQL 17 の `pg_stat_checkpointer` には `num_done` の列がありません（`column "num_done" does not exist` になります）。先に列の名前を確かめます。

⟦C15⟧

`num_timed`・`num_requested`・`restartpoints_timed`・`restartpoints_req`・`restartpoints_done`・`write_time`・`sync_time`・`buffers_written`・`stats_reset` がありました。

⟦C16⟧

統計を取り始めた 2026-11-17 から、決まった時刻のチェックポイントが 1,349 回、求められたチェックポイントは 4 回だけでした。書き込みは約 241MB、同期の時間は合計約28秒で、チェックポイントは安定しています。

## 5.4　WAL のファイル

⟦C17⟧

WAL は 32MB（16MB のファイルが2つ）で、上限の 1GB に対して小さく、たまってもいません。

# 第6章　バックアップを探す

## 6.1　アーカイブとデータの場所

⟦C18⟧

データは `/var/lib/postgresql/17/main`（PostgreSQL 17）にあり、`archive_mode` は `off`、`archive_command` は `(disabled)` でした。

## 6.2　バックアップのサービスとファイル

⟦C19⟧

見つかったのは `dpkg-db-backup.timer`（Debian のパッケージの管理の DB のバックアップで、PostgreSQL のバックアップではありません）と、PostgreSQL 本体のサービスだけでした。pgBackRest・Barman・Borg・Restic などもありません。ファイルの名前・時刻・大きさだけを見ます（中身は読みません）。

⟦C20⟧

`/var/backups` にあるのは `alternatives.tar.0` や `dpkg.*` などパッケージの管理のファイルだけで、PostgreSQL のバックアップのファイルも、cron のジョブもありませんでした。

| 項目 | 結果 |
|---|---|
| PostgreSQL のバックアップのファイル | なし |
| PostgreSQL 用の cron | なし |
| PostgreSQL 用の systemd のタイマー | なし |
| WAL のアーカイブ | 無効 |

**調べた範囲では、PostgreSQL のデータを戻すためのバックアップがありません。** データベースが壊れると、Wazuh から集めたイベントや分析の記録を失うおそれがあります。

# おわりに

第36部で、PostgreSQL を読み取りだけで点検しました。

| 項目 | 結果 |
|---|---|
| Collector の権限 | INSERT だけ（SELECT・UPDATE・DELETE なし、管理者の権限なし） |
| データ | 55,811 件、重複・形の誤り 0 |
| 取り込みの遅れ | 直近30分は平均 0.86 秒 |
| 容量 | テーブル 18MB、DB 26MB、不要な行 1.4% |
| 接続 | 100 のうち 14、`idle in transaction` 0 |
| WAL・チェックポイント | 正常（WAL 32MB、スロット 0） |
| 課題 | WAL のアーカイブなし、PostgreSQL のバックアップなし |

次の第37部では、PostgreSQL が動いている LXC 109 を Proxmox でバックアップし、別の番号の LXC に戻して、本当に復元できるかを試します。

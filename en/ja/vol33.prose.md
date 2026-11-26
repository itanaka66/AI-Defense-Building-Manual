---
title: "AI自律型サイバー防御システム 構築マニュアル 後編"
subtitle: "第33部　Collectorの状態をPrometheusで監視する"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」後編の第33部です。第32部までで、Collector がログの切り替えで止まらないようにし、欠けていたイベントも復旧しました。ここでは、Collector が止まったり読み遅れたりしたときに気づけるよう、**Collector の状態を Prometheus で見張る仕組み**を作ります。

新しい監視の仕組みは入れず、すでにあるものを使います。

- VM 220 で動いている **Node Exporter**（`192.168.0.220:9100`）の **Textfile Collector**（決まったディレクトリに置いた `.prom` ファイルの数値を公開する機能）
- LXC 103（`lxc-prometheus`）の **Prometheus 3.12.0**。すでに `security-core` という job 名で VM 220 の Node Exporter を集めている

作るものは次のとおりです。

1. Collector の状態から数値だけを取り出して `.prom` ファイルに書くスクリプト（root で動かす）
2. それを15秒ごとに動かす systemd のサービスとタイマー
3. Prometheus のアラートのルール（9個）

Collector の状態ファイル（`state.json`）は `wazuh-collector` だけが読み書きできる作り（ディレクトリ `0700`、ファイル `0600`）です。この制限は変えず、Node Exporter（`prometheus` のユーザー）には数値だけを書いたファイルを読ませます。

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **VM 220**：security-core（root）
  - **pve**：Proxmox のホスト（root）。LXC 103（`lxc-prometheus`、192.168.0.197）の中のコマンドは `pct exec 103 -- bash -lc '…'` で実行します

# 第1章　いまある監視の仕組みを調べる

## 1.1　サービスとタイマー

> **実行先：VM 220**

⟦C0⟧

| 項目 | 状態 |
|---|---|
| Collector | `active` / `running`、再起動 0 回 |
| 自動の再起動 | `Restart=always`、10秒に5回まで |
| Node Exporter | 動いている |
| AI Defense Relay | 動いている |

## 1.2　待ち受けのポート

⟦C1⟧

Node Exporter は `192.168.0.220:9100`、Relay は `192.168.0.220:8765`、Wazuh Indexer は `127.0.0.1:9200` で待ち受けていました。

## 1.3　Relay の `/health`

Relay の `/health` で Collector の状態も見られるかを確かめます。

⟦C2⟧

⟦C3⟧

`/health` は、次の決まった答えを返すだけでした。

⟦C4⟧

Relay 自身が答えていることしかわからず、Collector や PostgreSQL の状態はわかりません。Relay は変えず、Node Exporter を使うことにします。

## 1.4　Node Exporter の設定

⟦C5⟧

（`806` は、1.2 で表示された Node Exporter の PID です。）

⟦C6⟧

Node Exporter は `prometheus` のユーザーで動いています。Collector の状態ファイルは `drwx------ wazuh-collector:wazuh-collector`（ディレクトリ）・`-rw------- wazuh-collector:wazuh-collector`（ファイル）で、Node Exporter からは直接読めません。

⟦C7⟧

Node Exporter は 1.7.0 で、Textfile Collector はもともと有効でした。読み込むディレクトリは `/var/lib/prometheus/node-exporter` で、`apt.prom`・`nvme.prom`・`smartmon.prom` がすでに置かれていました。Node Exporter を再起動しなくても、ここにファイルを置けば数値を足せます。

## 1.5　権限を確かめる

⟦C8⟧

⟦C9⟧

結果は `0`（読める）・`0`（通れる）・`1`（書けない）でした。Node Exporter に書き込みの権限を与えずに、root が書いたファイルを読ませられます。

## 1.6　Collector のユニットと状態ファイルの形

状態ファイルの値は表示せず、形だけを確かめます。

⟦C10⟧

⟦C11⟧

# 第2章　数値を書き出すスクリプト

## 2.1　出す数値

| メトリクス | 内容 |
|---|---|
| `wazuh_collector_service_up` | Collector が動いているか（1/0） |
| `wazuh_collector_restarts_total` | systemd による再起動の回数 |
| `wazuh_collector_state_valid` | 状態ファイルが正しい形か（1/0） |
| `wazuh_collector_inode_match` | 状態ファイルの inode が今の `alerts.json` と同じか（1/0） |
| `wazuh_collector_unread_bytes` | 読み残しのバイト数（わからないときは -1） |
| `wazuh_collector_state_mtime_seconds` | 状態ファイルの更新時刻 |

アラートの中身、IP アドレス、接続の情報は出しません。一時ファイルに書いてから置き換え（`os.replace`）、途中で失敗したら古い `.prom` も消して、正常の値が残らないようにします。

## 2.2　スクリプトを作る

構築時は、実行の前に承認を取りました。

> **実行先：VM 220**

⟦C12⟧

`SCRIPT_SYNTAX_EXIT=0`、`-rwxr-xr-x root:root` でした。

## 2.3　一度だけ動かす

⟦C13⟧

`wazuh_collector_service_up 1`、`restarts_total 0`、`state_valid 1`、`inode_match 1`、`unread_bytes 0` が書かれ、`prometheus` のユーザーで読めました（`PROMETHEUS_READ_EXIT=0`）。

# 第3章　15秒ごとに動かす

## 3.1　サービス

root で動かしますが、読めるところと書けるところを絞ります（状態ファイルとアラートのディレクトリは読み取りだけ、書けるのは `.prom` のディレクトリだけ）。

⟦C14⟧

## 3.2　タイマー

⟦C15⟧

どちらも `VERIFY_EXIT=0` でした。

## 3.3　有効にする

⟦C16⟧

⟦C17⟧

サービスは `status=0/SUCCESS` で終わり、タイマーは `active (waiting)` でした。

> **メモ**：`systemctl list-timers` の次の実行時刻が `-` と出ることがあります。`OnUnitActiveSec` は前回の実行からの時間で決まる（単調時計の）ため、`NextElapseUSecRealtime` は空になり、`NextElapseUSecMonotonic` のほうに入ります。異常ではありません。

## 3.4　Node Exporter から見えるか

⟦C18⟧

Node Exporter の `/metrics` に `wazuh_collector_` の数値が出て、`node_scrape_collector_success{collector="textfile"}` は 1 でした。`.prom` ファイルも15秒ごとに書き換わっていました。

# 第4章　Prometheus に取り込む

## 4.1　Prometheus の場所

Prometheus は Proxmox の LXC 103 で動いています。Proxmox のホスト（`root@pve`）で Prometheus のコマンドを直接実行しても、設定ファイルや `promtool` は見つかりません。LXC の一覧で確かめます。

> **実行先：pve**

⟦C19⟧

LXC 103 が `lxc-prometheus` でした。

## 4.2　収集の設定

⟦C20⟧

Prometheus は動いていて、`192.168.0.220:9100` はすでに job `security-core` として登録されていました。設定の検査も `SUCCESS` です。Prometheus の設定は変えなくても、新しい数値は取り込まれます。

⟦C21⟧

5つとも `job="security-core"`・`instance="192.168.0.220:9100"` のラベルで取り込まれていました。

## 4.3　いまのアラートの設定

⟦C22⟧

`rule_files` はコメントのまま（ルールなし）で、Alertmanager も動いていませんでした。ルールを足せば、Prometheus の画面でアラートを見られます（メールなどへの通知は、Alertmanager を設定するまでは届きません。今回は通知の設定はしません）。

# 第5章　アラートのルール

## 5.1　作る前の確認

構築時は、ルールを足す前に承認を取りました。

⟦C23⟧

Prometheus は 3.12.0、評価の間隔は15秒でした。`/etc/prometheus/rules` はまだなく、同じ名前のファイルもありません。

## 5.2　ルールのファイル

| アラート | 条件 |
|---|---|
| `WazuhCollectorDown` | Collector が1分以上止まっている |
| `WazuhCollectorStateInvalid` | 状態ファイルが正しくない状態が1分以上 |
| `WazuhCollectorInodeMismatch` | inode が合わない状態が1分以上 |
| `WazuhCollectorBacklog` | 読み残しが 1MiB を超えた状態が2分以上 |
| `WazuhCollectorRestarted` | 5分のあいだに再起動の回数が増えた |
| `WazuhCollectorMetricsStale` | `.prom` が60秒以上書き換わっていない |
| `WazuhCollectorMetricsMissing` | Collector の数値が1分以上届かない |
| `SecurityCoreNodeExporterDown` | Node Exporter から1分以上集められない |
| `SecurityCoreTargetMissing` | 収集先 `security-core` そのものが1分以上ない |

> **実行先：pve**

⟦C24⟧

ファイルは `root:root`・`0644` で作られました。

## 5.3　ルールの検査

> **注意**：`pct exec 103 -- promtool …` のように直接実行すると、`promtool` が PATH から見つからず `Failed to exec "promtool"`（終了コード 127）になります。`bash -lc` を通して実行します。

⟦C25⟧

`SUCCESS: 9 rules found`、`RULE_CHECK_EXIT=0` でした。

## 5.4　Prometheus の設定に登録する

設定ファイルをバックアップしてから、コメントになっている `rule_files` の部分だけを置き換えます。置き換える場所がちょうど1か所でなければ、何もしません。

⟦C26⟧

`CONFIG_EDIT: SUCCESS` で、設定とルールの検査はどちらも `SUCCESS` でした。`rule_files:` の下は `- "/etc/prometheus/rules/*.yml"` になりました。

## 5.5　再起動せずに読み込ませる

⟦C27⟧

`CanReload=yes` で、`ExecReload=/bin/kill -HUP $MAINPID`（SIGHUP を送る）でした。

⟦C28⟧

Prometheus は `active` のままで、PID も `98` のまま変わらず、ログに `Completed loading of configuration file` が出ました。

## 5.6　ルールが登録されたか

⟦C29⟧

`RULE_COUNT: 9` で、9個とも `health` が `ok`・`state` が `inactive`（いまは異常なし）、`ACTIVE_ALERT_COUNT: 0` でした。

# おわりに

第33部で、Collector の状態を Prometheus で見張れるようにしました。

| 項目 | 結果 |
|---|---|
| 数値を書き出すスクリプト | `/usr/local/sbin/wazuh-collector-metrics.py`（root、`0755`） |
| 出力 | `/var/lib/prometheus/node-exporter/wazuh_collector.prom`（`0644`、6つの数値） |
| 定期実行 | `wazuh-collector-metrics.service`（oneshot）と `.timer`（15秒ごと） |
| 権限 | 状態ファイルの制限はそのまま。Node Exporter は読むだけ |
| Prometheus | LXC 103。job `security-core` で取り込み。設定のバックアップ `prometheus.yml.pre-wazuh-rules-20261122` |
| アラートのルール | `/etc/prometheus/rules/wazuh-collector-alerts.yml`（9個、すべて `ok`・`inactive`） |
| 通知 | Alertmanager は未設定（今回は設定しない） |

次の第34部では、Wazuh 本体（Manager・Indexer・Dashboard・API）の状態も、同じしくみで見張れるようにします。

---
title: "AI自律型サイバー防御システム 構築マニュアル 後編"
subtitle: "第34部　Wazuh本体の状態をPrometheusで監視する"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」後編の第34部です。第33部で Collector の状態を Prometheus で見張れるようにしました。ここでは同じしくみ（Node Exporter の Textfile Collector と、LXC 103 の Prometheus）で、**Wazuh 本体**を見張れるようにします。

| 見張るもの | 調べ方 |
|---|---|
| Wazuh Manager | 欠かせない9つのデーモンが動いているか |
| Wazuh Indexer | `https://127.0.0.1:9200/` が答えるか（401 も正常） |
| Wazuh Dashboard | `https://127.0.0.1:443/` が答えるか（302 も正常） |
| Wazuh API | `https://127.0.0.1:55000/` が答えるか（401 も正常） |

認証の情報はスクリプトに入れず、答えの HTTP のステータスだけを見ます。401（認証が要る）や 302（転送）も、サービスが答えている証拠として正常に数えます。

途中で、Manager の状態を `wazuh-control status` で調べる作りにしたところ、タイマーで動かすとロックの待ちで10秒を超えて失敗しました。Wazuh の PID ファイルを直接見る作りに直して解決します。

最後に、Wazuh 本体用のアラートのルールを7つ足し、Collector 用の9つとあわせて16のルールにします。

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **VM 220**：security-core（root）
  - **pve**：Proxmox のホスト（root）。LXC 103 の中のコマンドは `pct exec 103 -- bash -lc '…'` で実行します

# 第1章　いまの状態を調べる

ここまでの監視の構成は次のとおりです。

⟦C0⟧

## 1.1　サービスとディスク

> **実行先：VM 220**

⟦C1⟧

Wazuh Manager・Indexer・Dashboard・Filebeat・Collector はどれも動いていました。ルートのファイルシステムの使用率は 12%、使えるメモリは約 12GiB です。

## 1.2　Manager の中のデーモンとポート

⟦C2⟧

`wazuh-analysisd`・`wazuh-remoted`（1514）・`wazuh-authd`（1515）などは動いていて、API（55000）・Indexer（9200・9300）・Dashboard（443）も待ち受けていました。`wazuh-clusterd`・`wazuh-maild`・`wazuh-agentlessd` などは止まっていますが、これらは使う機能によって動かないもので、異常ではありません。

## 1.3　HTTP の答え

⟦C3⟧

Indexer は 401、Dashboard は 302 でした。API は `http://` だったため答えがなく（`000`）、API は HTTPS で待ち受けているので、HTTPS で確かめ直します。

⟦C4⟧

`HTTP_STATUS=401` でした。3つとも答えています。

## 1.4　いまある監視の道具

⟦C5⟧

`.prom` は `apt.prom`・`nvme.prom`・`smartmon.prom`・`wazuh_collector.prom` の4つでした。

⟦C6⟧

新しいスクリプトも、第33部のスクリプトと同じく root で動かし、数値だけを一時ファイルに書いてから置き換える作りにします。

⟦C7⟧

`wazuh-control status` の終了コードは `1` でした。止まっている任意のデーモンも含めて判定するためで、Manager 全体の異常ではありません。監視では、欠かせないデーモンだけを1つずつ見ます。

⟦C8⟧

`node_scrape_collector_success{collector="textfile"}` は 1 で、4つのファイルとも読まれていました。Node Exporter の起動の引数を変える必要はありません。ディスクやメモリは Node Exporter の標準の数値をそのまま使います。

# 第2章　Wazuh 本体の数値を書き出すスクリプト

構築時は、作る前に承認を取りました。

## 2.1　スクリプトを作る

> **実行先：VM 220**

⟦C9⟧

`SYNTAX_EXIT=0`、`-rwxr-xr-x root:root` でした。長い内容を貼り付けると端末の表示が崩れることがあるため、ファイルの中身を行番号つきで確かめます。

⟦C10⟧

150行で、意図どおりの内容でした。

## 2.2　一度だけ動かす

⟦C11⟧

`wazuh_manager_up 1`、9つのデーモンがすべて 1、`wazuh_indexer_up 1`（401）、`wazuh_dashboard_up 1`（302）、`wazuh_api_up 1`（401）でした。ファイルは `-rw-r--r-- root:root`、1,446 バイトです。

## 2.3　サービスとタイマー

⟦C12⟧

`VERIFY_EXIT=0` でした。こちらも貼り付けの表示が崩れたため、中身を確かめます。

⟦C13⟧

2つとも正しく書かれ、`TIMER_VERIFY_EXIT=0` でした。タイマーを有効にします。

⟦C14⟧

`active`・`enabled` になりました。

# 第3章　タイマーで動かすと失敗した

## 3.1　失敗を見つける

⟦C15⟧

サービスは失敗していて、ログには次のエラーがありました。`.prom` ファイルも書き換わっていません。

⟦C16⟧

⟦C17⟧

Wazuh Manager は `active` / `running` で、9つのデーモンも動いていました。止まっているのは `/bin/sh /var/ossec/bin/wazuh-control status` で、答えを待ったままになっていました。

## 3.2　監視のサービスだけを止める

調べているあいだ、監視のタイマーとサービスだけを止めます。Wazuh Manager や Collector は止めません。

⟦C18⟧

タイマーは止まりましたが、すでに動いていたサービス（`activating`）と `wazuh-control status` が残っていました。

⟦C19⟧

サービスは `failed` になり、残っているプロセスはなくなりました。

## 3.3　原因を調べる

⟦C20⟧

`status` は、最初にロックを取ってから全デーモンを調べる作りでした。

⟦C21⟧

ロックを取るのに**最大60秒待つ**作りで、スクリプトの10秒の制限を超えていました。監視から `wazuh-control` を呼ぶ必要はありません。Wazuh 自身がデーモンの状態を調べる方法（PID ファイル）を確かめます。

⟦C22⟧

9つのデーモンすべてに `wazuh-<名前>-<PID>.pid` のファイルがあり、PID はプロセスの一覧と同じでした。`pstatus()` は、PID ファイルを読んで `kill -0` で生きているかを見るだけの処理です。

# 第4章　PID ファイルを見る作りに直す

## 4.1　関数を置き換える

`manager_status()` だけを、PID ファイルと `os.kill(pid, 0)` で調べる作りに置き換えます。HTTP を見る処理と書き出しの処理はそのままです。

構築時は、最初に次のコマンドでスクリプトのバックアップを取ってから、正規表現で置き換えようとしました。

`cp -a /usr/local/sbin/wazuh-platform-metrics.py /usr/local/sbin/wazuh-platform-metrics.py.pre-pid-check-20261122`

このとき、置き換えのほうは正規表現の書き方の誤りで失敗し、スクリプトは変わりませんでした（バックアップはできています）。そこで、正規表現を使わず、関数の始まりと次の関数の始まりの位置で置き換えます。

> **実行先：VM 220**

⟦C23⟧

`REPLACEMENT=SUCCESS`、`SYNTAX_EXIT=0` でした。

## 4.2　直したスクリプトを試す

タイマーは止めたままにします。

⟦C24⟧

`SCRIPT_EXIT=0` で、`wazuh_manager_up 1`、9つのデーモンがすべて 1、3つの HTTP もすべて `up 1` でした。

systemd の制限のもとでも動くかを試します。

⟦C25⟧

`START_EXIT=0`、`Result=success`、`ExecMainStatus=0` でした（oneshot なので、終わると `inactive` / `dead` になるのが正常です）。

## 4.3　タイマーを戻す

⟦C26⟧

少し時間をおいて、続けて動いているかを確かめます。

⟦C27⟧

タイマーは `active` / `waiting`、サービスは `success` で、`.prom` ファイルも15秒ごとに書き換わっていました。

## 4.4　Node Exporter から見えるか

> **注意**：Node Exporter は `127.0.0.1` ではなく `192.168.0.220:9100` で待ち受けています。`http://127.0.0.1:9100/metrics` ではつながりません。

⟦C28⟧

`wazuh_manager_up`・9つの `wazuh_manager_daemon_up`・`wazuh_indexer_up`・`wazuh_dashboard_up`・`wazuh_api_up` などが表示されました。

# 第5章　Prometheus に取り込む

## 5.1　取り込まれたか

> **実行先：pve**（`root@pve:~#` で実行します。VM 220 では `pct` は使えません）

⟦C29⟧

すべて `status=success` で値は `1`、`job="security-core"`・`instance="192.168.0.220:9100"` で取り込まれていました。Prometheus の設定は変えていません。

⟦C30⟧

`wazuh_manager_daemon_up` は9本あり、すべて 1、`count(wazuh_manager_daemon_up)` は `9` でした。

# 第6章　Wazuh 本体用のアラートのルール

構築時は、ルールを足す前に承認を取りました。

## 6.1　いまのルール

⟦C31⟧

Collector 用のルール（第33部）の名前の付け方とラベルに合わせ、別のファイル `/etc/prometheus/rules/wazuh-platform-alerts.yml` に足します。`rule_files` は `/etc/prometheus/rules/*.yml` なので、Prometheus の設定は変えなくても読み込まれます。

## 6.2　ルールのファイル

| ルール | 条件 | 重要度 |
|---|---|---|
| `WazuhManagerDown` | Manager が止まった状態が1分 | critical |
| `WazuhManagerDaemonDown` | 欠かせないデーモンが止まった状態が1分 | critical |
| `WazuhIndexerDown` | Indexer が答えない状態が1分 | critical |
| `WazuhDashboardDown` | Dashboard が答えない状態が1分 | warning |
| `WazuhAPIDown` | API が答えない状態が1分 | critical |
| `WazuhPlatformMetricsMissing` | 数値が届かない状態が1分 | critical |
| `WazuhPlatformMetricsStale` | `.prom` が60秒以上書き換わらない | critical |

同じ名前のファイルがあれば、上書きせずに止まります。

⟦C32⟧

`-rw-r--r-- root:root 2823 bytes` で作られました。

## 6.3　検査して読み込ませる

⟦C33⟧

Wazuh 本体のルールは `SUCCESS: 7 rules found`、設定全体の検査でも Collector のルール（9）と2つのファイルが読めて、終了コードはすべて 0 でした。

⟦C34⟧

`RELOAD_EXIT=0`、Prometheus は `active` で、PID は `98` のまま変わらず、`Completed loading of configuration file` が出ました。

## 6.4　16のルールを確かめる

⟦C35⟧

| グループ | ルールの数 | 状態 |
|---|---:|---|
| `wazuh-collector` | 9 | すべて `health=ok`・`state=inactive` |
| `wazuh-platform` | 7 | すべて `health=ok`・`state=inactive` |

`ACTIVE_ALERT_COUNT: 0` でした。`inactive` は、いまはどのルールの条件にも当たっていないということです。

# おわりに

第34部で、Wazuh 本体の状態も Prometheus で見張れるようにしました。

| 項目 | 結果 |
|---|---|
| スクリプト | `/usr/local/sbin/wazuh-platform-metrics.py`（root、`0755`）。バックアップ `wazuh-platform-metrics.py.pre-pid-check-20261122` |
| Manager の調べ方 | `wazuh-control status` ではなく、PID ファイルと `kill -0`（Wazuh のロックに触れない） |
| 出力 | `/var/lib/prometheus/node-exporter/wazuh_platform.prom` |
| 定期実行 | `wazuh-platform-metrics.service`（oneshot）と `.timer`（15秒ごと） |
| Prometheus | 設定は変えずに取り込み。ルールのファイル `/etc/prometheus/rules/wazuh-platform-alerts.yml`（7つ） |
| ルールの合計 | Collector 9 ＋ Wazuh 本体 7 ＝ 16、すべて `ok`・`inactive`、発報 0 |
| 通知 | Alertmanager は未設定 |

次の第35部では、本番のサービスを止めずに、試験用のデータでルールが正しく発報するかを試し、本番の値も確かめます。

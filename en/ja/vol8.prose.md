---
title: "AI自律型サイバー防御システム 構築マニュアル 前編"
subtitle: "第8部　統合監視基盤の構築"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」前編の第8部です。第7部までで、Wazuhのアラートを PostgreSQL に保存する仕組みが完成しました。第8部では、防御システムを構成するサーバーそのものの状態（CPU・メモリ・ディスク・ネットワーク）を集め、Grafanaの統合ダッシュボードで見られるようにします。

## 本書の表記

- コマンドやファイル内容は、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 各手順の冒頭に「実行先」を示します。
- 「実行結果（例）」は構築時の実際の出力です。系列数・時刻などは、お使いの環境では異なります。

## 監視の対象と方針

統合ダッシュボードで監視するのは、次の5台です。

| 対象 | IPアドレス | 役割 |
|---|---|---|
| Proxmoxホスト `pve` | 192.168.0.240 | ハイパーバイザー |
| VM 220 `security-core` | 192.168.0.220 | Wazuh・Collector |
| LXC 109 `postgresql` | 192.168.0.151 | PostgreSQL（Wazuhイベントの保存先） |
| LXC 103 `lxc-prometheus` | 192.168.0.197 | Prometheus |
| LXC 105 `lxc-grafana` | 192.168.0.199 | Grafana |

- 各サーバーに Node Exporter を入れ、Prometheus（LXC 103）が集めます。
- Prometheus は、集めたデータを既存の VictoriaMetrics に転送（Remote Write）して保存します。Grafana は VictoriaMetrics を見ます。
- Grafana と VictoriaMetrics は外部に公開しません。内部専用の監視基盤とします。
- LXC 400番台は対象外です。VictoriaMetrics は既存の LXC 406 で動いていますが、本書では `vmbr0` 側のアドレス `192.168.0.171:8428` に接続して使うだけで、LXC 406 自体の設定は変更しません。
- `192.168.1.25`（別システムの PostgreSQL と PostgreSQL Exporter）も対象外です。

# 第1章　GrafanaとVictoriaMetricsの接続

## 1.1　Grafanaの状態の確認

**実行先：LXC 105 lxc-grafana（root）**

⟦C0⟧

構築時は Grafana 13.0.2 が `active (running)` で、`/api/health` も正常でした。

## 1.2　VictoriaMetricsへの到達の確認

Grafana（`vmbr0`、192.168.0.0/24）からは、VictoriaMetrics の `vmbr1` 側のアドレス（192.168.1.23）には届きません。ネットワークを変更せず、`vmbr0` 側のアドレス `192.168.0.171` に接続できるかを確かめます。

**実行先：LXC 105 lxc-grafana（root）**

⟦C1⟧

`/health` が HTTP 200（`OK`）、`/api/v1/query` が `status: success` であれば接続できています。

## 1.3　データソースの登録

GrafanaのWeb画面（`http://192.168.0.199:3000`）にログインし、次の設定を行います。

1. 左メニュー **Connections → Data sources**
2. **Add data source**
3. **Prometheus** を選択
4. 以下を設定

| 項目 | 設定値 |
|---|---|
| Name | VictoriaMetrics |
| Prometheus server URL | `http://192.168.0.171:8428` |
| Access | Server（既定値） |

5. **Save & test** をクリック

`Successfully queried the Prometheus API.` と表示されれば完了です。

# 第2章　監視対象の現状の確認

## 2.1　VictoriaMetricsに届いているデータ

**実行先：LXC 105 lxc-grafana（root）**

⟦C2⟧

構築時は11件の系列がありましたが、5台のどれのデータでもありませんでした（対象外のサーバーのものです）。5台のCPU・メモリ・ディスクのデータは、まだ集められていません。

## 2.2　ポートの確認

**実行先：LXC 105 lxc-grafana（root）**

⟦C3⟧

構築時は、5台とも Node Exporter（9100）が `CLOSED` でした。各サーバーで確かめたところ、どれにも Node Exporter は入っていませんでした。次章から、1台ずつ導入して動作を確認してから次のサーバーへ進みます。

# 第3章　ProxmoxホストへのNode Exporterの導入

## 3.1　パッケージの確認

**実行先：Proxmoxホスト pve（root）**

⟦C4⟧

構築時は Debian 12（bookworm）で、公式リポジトリの `prometheus-node-exporter 1.5.0-1+b6` を導入できました。

## 3.2　インストール

パッケージを入れると、すぐにすべてのアドレスで待ち受けを始めます。先に一時的にマスクして、起動しないようにしてから入れます。

**実行先：Proxmoxホスト pve（root）**

⟦C5⟧

⟦C6⟧

設定を確認します（まだ起動しません）。

⟦C7⟧

Debianのパッケージは、`/etc/default/prometheus-node-exporter` の `ARGS` で起動オプションを指定します。`MASK STATUS` が `masked-runtime` であることを確認します。

## 3.3　待ち受けのアドレスの限定と起動

待ち受けを `192.168.0.240:9100` だけに限定します。

**実行先：Proxmoxホスト pve（root）**

⟦C8⟧

⟦C9⟧

⟦C10⟧

最後に `curl: (23) Failure writing output to destination` と表示されますが、`head` が15行で読み取りを終えたためで、異常ではありません。

## 3.4　Prometheusからの到達の確認

**実行先：LXC 103 lxc-prometheus（root）**

⟦C11⟧

`SUCCESS: metrics received` と表示されれば届いています。

# 第4章　Prometheusへの収集ジョブの追加

## 4.1　ジョブの追加

既存のジョブ（`prometheus`・`ollama-gpu`）はそのままにして、PVE用のジョブを追加します。

**実行先：LXC 103 lxc-prometheus（root）**

⟦C12⟧

`SUCCESS` と表示されることを確認します（構築時は Prometheus 3.12.0）。

## 4.2　設定の再読み込み

このPrometheusは、Web API（Lifecycle API）での再読み込みが無効です（HTTP 403になります）。systemd のユニットに次の設定があるため、`systemctl reload` で SIGHUP を送って再読み込みします。

⟦C13⟧

**実行先：LXC 103 lxc-prometheus（root）**

⟦C14⟧

再読み込みの直後は表示されないことがあります。そのときは、次のコマンドですべてのジョブを確認します。

⟦C15⟧

構築時は、3つのジョブすべてが `health: up` でした。

# 第5章　VictoriaMetricsへの転送（Remote Write）

## 5.1　現状の確認とバックアップ

**実行先：LXC 103 lxc-prometheus（root）**

⟦C16⟧

⟦C17⟧

## 5.2　転送の設定の追加

転送先と、転送元を見分けるラベル（`prometheus_source`）を追加します。

**実行先：LXC 103 lxc-prometheus（root）**

⟦C18⟧

構築時は、ここで `promtool` がエラーになりました。`external_labels` は最上位の項目ではなく、`global` の中に置く必要があります。次のコマンドで `global` の中に移します。

⟦C19⟧

⟦C20⟧

## 5.3　反映と転送の確認

**実行先：LXC 103 lxc-prometheus（root）**

⟦C21⟧

⟦C22⟧

| ジョブ | VictoriaMetricsの系列数（構築時） |
|---|---:|
| `pve-node` | 8,909 |
| `ollama-gpu` | 865 |
| `prometheus` | 791 |

> VictoriaMetrics で検索するときは、`host="pve"` ではなく `job="pve-node"` を条件にします。構築時は `host="pve"` で検索して0件になりました。

## 5.4　保存されたデータの確認

**実行先：LXC 103 lxc-prometheus（root）**

⟦C23⟧

ファイルシステム・ネットワーク・ディスクI/Oの各系列が1件以上あれば、ダッシュボードに必要なデータがそろっています。

# 第6章　PVEのダッシュボードの作成

ダッシュボードは、Grafanaの画面で作るのではなく、ファイル（プロビジョニング）で作ります。設定をファイルとして残せるためです。

## 6.1　データソースのUIDの確認

ダッシュボードのJSONには、データソースのUIDを書きます。Grafanaのデータベースを読み取り専用で開いて確認します。

**実行先：LXC 105 lxc-grafana（root）**

⟦C24⟧

構築時のUIDは `dfsldbphmj9c0e` でした。次の手順の `"uid": "dfsldbphmj9c0e"` は、自分の環境のUIDに置き換えます。

## 6.2　ダッシュボードとプロビジョニングの設定の作成

`PVE Host Overview` ダッシュボード（CPU・メモリ・ファイルシステム・ネットワーク・ディスクI/O・稼働時間の6パネル）と、それを読み込む設定を作ります。同じ名前のファイルがあるときは、上書きせずに止まります。

**実行先：LXC 105 lxc-grafana（root）**

⟦C25⟧

## 6.3　ファイルの所有者の修正

6.2では所有者をUID 472にしていますが、このLXCのGrafanaの実行ユーザー `grafana` はUID 102です。このままではGrafanaがJSONを読めないため、所有者を `grafana` に直します。

**実行先：LXC 105 lxc-grafana（root）**

⟦C26⟧

## 6.4　Grafanaの再起動と確認

**実行先：LXC 105 lxc-grafana（root）**

⟦C27⟧

再起動の直後は、まだ3000番ポートで待ち受けておらず、`/api/health` に接続できないことがあります。少し待ってから確認します。

⟦C28⟧

ログに `finished to provision dashboards` があれば読み込みは完了しています。

## 6.5　画面での確認

Grafanaの画面で **Dashboards → Infrastructure → PVE Host Overview** を開き、6つのパネルすべてにデータが表示されることを確認します。構築時は、すべてのパネルが表示されました。

# 第7章　security-coreの監視の追加

Wazuhの本体や設定には触れず、Node Exporterだけを追加します。

## 7.1　確認とインストール

**実行先：security-core VM 220（root）**

⟦C29⟧

⟦C30⟧

構築時は Ubuntu 24.04.5 LTS で、候補は `1.7.0-1ubuntu0.3` でした。PVEと同じく、一時的にマスクしてから入れます。

⟦C31⟧

## 7.2　待ち受けのアドレスの限定と起動

**実行先：security-core VM 220（root）**

⟦C32⟧

一時的なマスクは `/run/systemd/system/` にあるため、解除するときも `--runtime` を付けます（付けないと解除されず、起動が拒否されます）。

⟦C33⟧

## 7.3　Prometheusからの到達の確認

**実行先：LXC 103 lxc-prometheus（root）**

⟦C34⟧

## 7.4　ジョブの追加

`pve-node` のジョブのすぐ後に、次のジョブを追加します。

⟦C35⟧

**実行先：LXC 103 lxc-prometheus（root）**

⟦C36⟧

> 先頭に `set -e` があるため、このコマンドは対話中のシェルに直接貼り付けず、`bash` を起動してから実行するか、スクリプトにして実行してください。途中で失敗すると、ログインしているシェルごと終了します。

## 7.5　反映と確認

**実行先：LXC 103 lxc-prometheus（root）**

⟦C37⟧

直後は `health: unknown` です。1回目の収集が終わるまで待ってから確認します。

⟦C38⟧

⟦C39⟧

構築時は、`up` が `1`、CPUの系列が64件で、転送のエラーはありませんでした。

# 第8章　PostgreSQL（LXC 109）の監視の追加

PostgreSQLの本体には触れず、Node Exporterだけを追加します。

## 8.1　インストール

**実行先：LXC 109 postgresql（root）**

⟦C40⟧

構築時は Debian 13（trixie）で、候補は `1.9.0-1+b4` でした。

⟦C41⟧

⟦C42⟧

`ARGS=""` と `masked-runtime` を確認します。

## 8.2　待ち受けのアドレスの限定と起動

**実行先：LXC 109 postgresql（root）**

⟦C43⟧

⟦C44⟧

## 8.3　Prometheusからの到達の確認

**実行先：LXC 103 lxc-prometheus（root）**

⟦C45⟧

## 8.4　ジョブの追加と反映

`security-core` のジョブの後に `postgresql-node` を追加します。

**実行先：LXC 103 lxc-prometheus（root）**

⟦C46⟧

⟦C47⟧

## 8.5　確認

**実行先：LXC 103 lxc-prometheus（root）**

⟦C48⟧

⟦C49⟧

`health: up`、`up` が `1`、`NO REMOTE WRITE ERRORS FOUND` であれば完了です。

# 第9章　Prometheus（LXC 103）自身の監視の追加

Prometheus（9090番）とポートが重ならないよう、Node Exporterは `192.168.0.197:9100` で待ち受けます。

## 9.1　インストールと起動

**実行先：LXC 103 lxc-prometheus（root）**

⟦C50⟧

⟦C51⟧

⟦C52⟧

⟦C53⟧

## 9.2　ジョブの追加と反映

**実行先：LXC 103 lxc-prometheus（root）**

⟦C54⟧

⟦C55⟧

⟦C56⟧

## 9.3　確認

**実行先：LXC 103 lxc-prometheus（root）**

⟦C57⟧

⟦C58⟧

# 第10章　Grafana（LXC 105）自身の監視の追加

Grafana本体（3000番）は変更せず、Node Exporterを `192.168.0.199:9100` で待ち受けます。

## 10.1　インストールと起動

**実行先：LXC 105 lxc-grafana（root）**

⟦C59⟧

⟦C60⟧

⟦C61⟧

⟦C62⟧

## 10.2　Prometheusからの到達の確認

**実行先：LXC 103 lxc-prometheus（root）**

⟦C63⟧

## 10.3　ジョブの追加と反映

このジョブは、`remote_write:` の直前（ジョブの並びの最後）に追加します。

⟦C64⟧

**実行先：LXC 103 lxc-prometheus（root）**

⟦C65⟧

`marker` は、構築時の設定ファイルで `remote_write:` の前に空行が2行あったことに合わせています。自分の環境のファイルの形に合わせてください（形が違うときは、変更せずに止まります）。

⟦C66⟧

⟦C67⟧

## 10.4　確認

**実行先：LXC 103 lxc-prometheus（root）**

⟦C68⟧

⟦C69⟧

これで5台すべてが監視の対象になりました。

# 第11章　統合インフラ監視ダッシュボードの作成

PVEのダッシュボードはそのまま残し、5台をまとめて比べる「Integrated Infrastructure Overview」を新しく作ります。各ホストに付けた `host` ラベルで、ホストごとに表示します。

## 11.1　既存の設定の確認

**実行先：LXC 105 lxc-grafana（root）**

⟦C70⟧

6.2のプロビジョニングの設定は、`/var/lib/grafana/dashboards` の中のJSONをすべて自動で読み込みます（フォルダーは `Infrastructure`）。そのため、設定の変更は不要で、JSONファイルを置くだけで追加できます。

## 11.2　ダッシュボードの作成

7つのパネル（ホストの稼働状態・CPU・メモリ・ファイルシステム・ネットワーク・ディスクI/O・稼働時間）を作ります。同じ名前のファイルがあるときは、上書きせずに止まります。`"uid": "dfsldbphmj9c0e"` は、6.1で確認した自分の環境のUIDに置き換えます。

**実行先：LXC 105 lxc-grafana（root）**

⟦C71⟧

> 先頭に `set -e` があるため、`bash` を起動してから実行してください（7.4の注記と同じです）。

## 11.3　読み込みの確認

プロビジョニングは30秒ごとにファイルを確認するため、Grafanaの再起動は不要です。

**実行先：LXC 105 lxc-grafana（root）**

⟦C72⟧

時間を置いて確認したいときは、ログの範囲を広げます（`--since` は作業した時刻に合わせます）。

⟦C73⟧

構築時は、ダッシュボードの検索インデックスが `size=3` に増えたことがログで確認できました。

## 11.4　画面での確認

Grafanaの画面で **Dashboards → Infrastructure → Integrated Infrastructure Overview** を開き、7つのパネルすべてに5台分のデータが表示されることを確認します。構築時は、すべてのパネルが表示されました。

# 第8部のまとめ

## 完成した監視の構成

| 監視対象 | アドレス | Prometheusのジョブ | `host` / `role` |
|---|---|---|---|
| Proxmoxホスト | 192.168.0.240:9100 | `pve-node` | `pve` / `hypervisor` |
| security-core | 192.168.0.220:9100 | `security-core` | `security-core` / `security` |
| PostgreSQL | 192.168.0.151:9100 | `postgresql-node` | `postgresql` / `database` |
| Prometheus | 192.168.0.197:9100 | `prometheus-node` | `prometheus` / `monitoring` |
| Grafana | 192.168.0.199:9100 | `grafana-node` | `grafana` / `visualization` |

データの流れ：Node Exporter → Prometheus（LXC 103）→ Remote Write → VictoriaMetrics（`192.168.0.171:8428`）→ Grafana（LXC 105）

## 作成したダッシュボード

| ダッシュボード | UID | パネル |
|---|---|---|
| PVE Host Overview | `pve-host-overview` | 6 |
| Integrated Infrastructure Overview | `infra-unified-overview` | 7 |

## 守った方針

- 各 Node Exporter は、`vmbr0` 側の自分のアドレスだけで待ち受ける。
- 既存のジョブ（`prometheus`・`ollama-gpu`）、既存のサービス、PVEのダッシュボードは変更しない。
- Prometheus は再起動せず、SIGHUP（`systemctl reload`）で設定を読み込み直す。
- Grafana と VictoriaMetrics は外部に公開しない。LXC 400番台と `192.168.1.25` には触れない。

## 変更したファイル

| サーバー | ファイル |
|---|---|
| 5台すべて | `/etc/default/prometheus-node-exporter` |
| LXC 103 | `/etc/prometheus/prometheus.yml`（変更ごとにバックアップを作成） |
| LXC 105 | `/etc/grafana/provisioning/dashboards/pve.yaml`、`/var/lib/grafana/dashboards/pve-overview.json`、`/var/lib/grafana/dashboards/infrastructure-overview.json` |

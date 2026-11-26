---
title: "AI自律型サイバー防御システム 構築マニュアル 前編"
subtitle: "第1部　防御基盤の構築とWazuhによる監視"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は、Proxmox VE上にAI自律型サイバー防御システムを構築する手順を（一般的なPCを複数台組み合わせる場合の読み替えは、この「はじめに」の後半で説明します）、実際の構築作業の記録から「成功した手順だけ」を時系列に並べて整理したマニュアルです。全体は「前編」「中編」の編に分かれ、各編はさらに複数の部に分かれています（編と部の構成は、この「はじめに」の「編と部の構成」を見てください）。本書（前編の第1部）では次の範囲を扱います。

- 防御システムの設計方針の決定（第1章）
- Proxmoxホストの環境調査と、新規VMの構成の確定（第2〜3章）
- Security Core VM（VMID 220）の作成と、Ubuntu Server 24.04.5 LTSの導入・初期設定（第4〜6章）
- Wazuh 4.14.10 All-in-Oneの構築と動作確認（第7〜10章）
- ProxmoxホストへのWazuh Agentの導入と、VM・LXCの棚卸し（第11〜12章）
- LXCコンテナ（Prometheus・Grafana・PostgreSQL）へのWazuh Agentの展開（第13〜16章）

## スクリプトのダウンロード

本書で使用したスクリプトは下記からダウンロードできます。

https://github.com/itanaka66/AI-Defense-Building-Manual/releases

## 編と部の構成

本マニュアルは、構築の記録の量が多いため、次の2つの編に分けています。部の番号は編をまたいで通し番号です。

| 編 | 部 | 主な内容 |
|---|---|---|
| 前編 | 第1部〜第23部 | 防御基盤（Wazuh・Collector・PostgreSQL・監視）、AI Defense Manager、Wazuh の検索用ユーザー、中継API（Relay）、AI 分析とその保護、点検 |
| 中編 | 第24部〜第30部 | Wazuh Indexer の監査ログの有効化と検証、Collector の点検・復旧・再発防止 |

**前編**

| 部 | 題名 |
|---|---|
| 第1部 | 防御基盤の構築とWazuhによる監視 |
| 第2部 | PostgreSQLログの安全な監視と相関検知 |
| 第3部 | アラート保存Collectorの構築 |
| 第4部 | Collectorの監査と強化版の開発 |
| 第5部 | 強化版Collectorの本番反映 |
| 第6部 | データ整合性の検証と運用監査 |
| 第7部 | Collectorの耐障害性の仕上げ |
| 第8部 | 統合監視基盤の構築 |
| 第9部 | Collectorの停止からの復旧と運用の点検 |
| 第10部 | ディスク障害の対処とAI Defense Managerの準備 |
| 第11部 | AI Defense Managerの土台づくり |
| 第12部 | AI分析サービスとWazuh連携の調査 |
| 第13部 | Wazuh Indexerの読み取り専用ユーザー |
| 第14部 | アラート中継API（Relay）の構築 |
| 第15部 | Relayの接続情報をVM 230へ安全に渡す |
| 第16部 | WazuhアラートをAI分析につなぐ |
| 第17部 | AI Defense Managerのサービス化と起動順序 |
| 第18部 | 分析履歴をSQLiteに残す |
| 第19部 | LLMに渡す情報を最小にする |
| 第20部 | 信頼度の修正と保存データの保護 |
| 第21部 | VM 230のSSHを公開鍵認証に切り替える |
| 第22部 | Relayと接続情報の点検 |
| 第23部 | Indexerの権限と監査ログの調査 |

**中編**

| 部 | 題名 |
|---|---|
| 第24部 | 監査ログが保存されない原因を突き止める |
| 第25部 | 監査ログの保存先を設定する |
| 第26部 | 監査ログでリクエストの本文を記録しない |
| 第27部 | 監査ログが保存されていることを確かめる |
| 第28部 | Collectorの点検と停止の原因 |
| 第29部 | 読み残しを出さずにCollectorを動かし直す |
| 第30部 | Collectorが同じ理由で止まらないようにする |

## 本書の表記

- コマンドやファイル内容は、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 各手順の冒頭に「実行先」を示します。`root@pve` はProxmoxホスト、`root@security-core` はVM 220、`root@lxc-prometheus` などはLXCコンテナの中を表します。
- 「実行結果（例）」は構築時の実際の出力です。お使いの環境では、IDやMACアドレス、容量、日時などが異なります。
- 本書に登場するIPアドレス・VMID・ストレージ名は、構築した環境の値です。ご自身の環境に合わせて読み替えてください。

## 構築環境の前提

| 項目 | 内容 |
|---|---|
| 仮想化基盤 | Proxmox VE 8.4（ホスト名 `pve`） |
| CPU | AMD EPYC 7301（16コア／64スレッド） |
| メモリ | 約267 GiB |
| 管理ネットワーク | `vmbr0`（eno1）`192.168.0.0/24`、ホストIP `192.168.0.240` |
| 内部ネットワーク | `vmbr1`（eno2）`192.168.1.0/24`、ホストIP `192.168.1.254` |
| デフォルトゲートウェイ | `192.168.0.1` |
| ゲストOS | Ubuntu Server 24.04.5 LTS |

## 一般的なPCで構築する場合

本書は、1台の大きなサーバーに Proxmox VE を入れ、その上の仮想マシン（VM）とコンテナ（LXC）に各機能を置く構成で書いています。同じシステムは、**一般的なPC（ミニPCやデスクトップPC）を複数台組み合わせて構築することも容易です**。1つのVM・LXCを、1台のPCと考えてください。

### VM・LXCとPCの読み替え

| 本書での名前 | 本書での置き場所 | 役割 | 読み替え（例） |
|---|---|---|---|
| security-core | VM 220（192.168.0.220） | Wazuh（Manager・Indexer・Dashboard）、Collector | PC1 |
| postgresql | LXC 109（192.168.0.151） | PostgreSQL（アラートの保存） | PC2 |
| lxc-prometheus | LXC 103（192.168.0.197） | Prometheus | PC2 |
| lxc-grafana | LXC 105（192.168.0.199） | Grafana | PC2 |
| VictoriaMetrics | 既存の LXC（192.168.0.171） | メトリクスの保存 | PC2 |
| ai-defense-manager | VM 230（192.168.0.33） | AI Defense Manager | PC3 |
| ollama-gpu | VM 101（192.168.0.180） | Ollama（ローカルLLM） | PC4 |
| pve | Proxmoxホスト（192.168.0.240） | 仮想化の基盤（監視の対象の1台） | 不要（各PCがそれぞれ監視の対象になる） |

上の表は、監視と保存の役割（PostgreSQL・Prometheus・Grafana・VictoriaMetrics）を1台（PC2）にまとめた4台構成の例です。台数に余裕があれば、本書と同じように1役割を1台に分けても構いません。1台にまとめる場合も、使うポート（PostgreSQL 5432、Prometheus 9090、Grafana 3000、VictoriaMetrics 8428）は重なりません。ただし Node Exporter（9100）は1台に1つだけにし、Prometheus のジョブも1台分にまとめます。

本文の「実行先：LXC 103 lxc-prometheus」などは、その役割を置いたPC（上の例では PC2）と読み替えてください。

### 参考になるPCの構成

次の表は目安です。本書の構築環境で各VMに割り当てた量と、本文で示したWazuhの公式の目安（25〜100エージェントで 8 vCPU・8 GiB RAM・100〜200GB）をもとにしています。この台数・構成で動かしたことを確かめたものではありません。監視するサーバーの数・ログの量・保存する期間に合わせて増やしてください。

| PC | 役割 | CPU | メモリ | ディスク | 備考 |
|---|---|---|---|---|---|
| PC1 | Wazuh・Collector | 8コア以上 | 16GB以上 | SSD 250GB以上 | 本書の VM 220 と同じ量。Indexer がログを保存するため、ディスクは多めに |
| PC2 | PostgreSQL・Prometheus・Grafana・VictoriaMetrics | 4コア以上 | 16GB以上 | SSD 500GB以上 | 保存する期間に応じてディスクを増やす |
| PC3 | AI Defense Manager | 4コア以上 | 8GB以上 | SSD 100GB以上 | 本書の VM 230 と同じ量 |
| PC4 | Ollama | 8コア以上 | 32GB以上 | SSD 500GB以上 | NVIDIA のGPU（VRAM 12GB以上を目安）。本書では RTX 3090（24GB）で `qwen3:8b` を使用 |

OSは、本書と同じく Ubuntu Server 24.04 LTS を使うのが簡単です（本書では、LXCの一部が Debian 13 でした。パッケージの名前や版は同じ手順で確かめられます）。

### 読み替えるときの注意

- **Proxmox だけのコマンド**：`qm`・`pct`・`pvesm` は Proxmox のコマンドです。VMやLXCを作る手順（第1部 第2〜4章、第10部 第6章など）は、各PCにOSを入れる作業に置き換えます。Proxmoxホスト自体を監視する手順（第1部 第11章、第8部 第3章）は、不要です。
- **IPアドレス**：本書のIPアドレスは構築した環境の値です。各PCに固定のIPアドレスを割り当て、本文のアドレスを読み替えてください。本書では2つのネットワーク（192.168.0.0/24 と 192.168.1.0/24）を使っていますが、すべてのPCを同じネットワーク（例：192.168.0.0/24）に置いても構いません。
- **待ち受けのアドレス**：Node Exporter や中継APIなどは、そのPC自身のアドレスだけで待ち受けるように設定しています（例：`--web.listen-address=192.168.0.240:9100`）。そのPCのアドレスに置き換えてください。
- **ディスクの監視**：第10部のディスク障害の検知と対処は、PCでも同じ考え方で行えます。デバイス名（`/dev/sdg` など）は自分の環境で確かめてください。
- **GPU**：PC4 では、NVIDIA のドライバーを入れて `nvidia-smi` でGPUが見えることを確かめてから Ollama を入れます（Ollama の導入は、本書の構築の範囲より前に済んでいたため、手順は載せていません）。

## 使用するWazuhのバージョン

| 項目 | バージョン |
|---|---|
| Wazuh（Manager・Indexer・Dashboard・Agent） | 4.14.10 |
| Filebeat | 7.10.2 |
| Proxmoxホスト | Proxmox VE 8.4.0（Debian 12 Bookworm） |

ManagerとAgentのバージョンは4.14.10で統一します。

# 第1章　システム設計の方針

## 1.1　目的

ネットワークへの侵入を24時間監視し、検知・分析・遮断・調査・記録までをAIエージェントが支援する「AI SOC（Security Operations Center）」を構築します。AIに無制限の操作をさせるのではなく、自分が管理するネットワークの中で、証拠に基づいて防御措置を実行させることを基本とします。

自動化する処理の流れは次のとおりです。

**検知 → 相関分析 → リスク評価 → 防御判断 → 遮断 → 検証 → 記録**

## 1.2　設計条件

構築にあたり、次の条件で設計しました。

| 項目 | 決定内容 |
|---|---|
| 自律化レベル | レベル3（不審な接続元を自動遮断・隔離） |
| 実行方式 | 危険度に応じて自動遮断し、重大な操作は人間が承認 |
| 基盤 | Proxmox VE、OSS中心の構成 |
| Kubernetes（RKE2） | 廃止。防御対象から外す |

RKE2を廃止したため、防御対象は次のとおりです。

- Proxmoxホスト
- Proxmox上のVMとLXCコンテナ（LXC 400番台は対象外）
- LAN・ルーター・ファイアウォール
- 各種データベース
- Ollama・vLLMなどのAI基盤
- 外部公開Webサービス

なお、RKE2用のVMは廃止方針だけを理由に削除しません。既存データやサービスの移行状況を確認してから扱います。

## 1.3　構成要素

| 製品 | 役割 |
|---|---|
| Wazuh | SIEM・ホスト監視・ログ分析 |
| Suricata | IDS/IPS・通信監視 |
| CrowdSec | 不審なIPの検知・遮断 |
| AI Defense Manager | AIによる分析・相関・リスク判定・防御制御 |
| SOAR / Incident DB | 防御処理・承認・監査記録 |

AIモデルが遮断命令を直接実行することはありません。AIは判断案を作るだけで、独立したポリシーエンジンが実行してよいかを検証してから、防御APIを呼び出します。

## 1.4　段階的な導入

最初から自動遮断を有効にはしません。次の段階で進めます。

1. 監視のみ
2. AIによる分析と防御提案
3. 承認済みルールに基づく不審IPの自動遮断
4. 承認制によるVM・LXCの隔離

構築する順序は次のとおりです。

1. Security Core（Wazuh Server・Indexer・Dashboard）の構築
2. Proxmoxホスト・VM・LXCへのエージェント導入
3. SuricataをIDSモードで導入し、通信を可視化
4. AI Defense Managerの構築（既存のOllamaと連携）
5. 不審な外部IPの一時遮断から自動化（VM・LXCの隔離は承認制）

## 1.5　安全上の設計ルール

- 遮断対象は、自分が管理するネットワークの中に限定する。
- IPアドレスだけで攻撃者の身元を断定しない。
- 自分の管理用IPや重要な通信を誤って遮断しない。ゲートウェイ（`192.168.0.1`）、Proxmoxホスト（`192.168.0.240`）、セキュリティ用VMの管理IPなどは自動遮断の対象外とする。
- AIに無制限のroot権限を与えない。
- 操作履歴は改ざんされにくい場所に保存する。
- 自動遮断には有効期限とロールバック（解除）機能を設ける。
- IPアドレスを遮断しただけで「侵入者を排除できた」と判断しない。アカウント、プロセス、永続化された不正プログラムも調査する。

# 第2章　Proxmox環境の調査

VMを作る前に、既存の環境と競合しないよう、Proxmoxホストの状態を調べます。この章のコマンドはすべて読み取り専用で、設定は変更しません。

## 2.1　環境情報の取得

**実行先：Proxmoxホスト（root@pve）**

⟦C0⟧

調査の結果、次のことがわかりました。

| 項目 | 結果 |
|---|---|
| Proxmox | VE 8.4.0（pve-manager 8.4.20） |
| メモリ | 267 GiB（利用可能 約115 GiB） |
| ネットワーク | `vmbr0`（eno1）と `vmbr1`（eno2）の2系統 |
| Proxmox Firewall | 無効（`disabled/running`） |
| Kubernetes | ノードなし（廃止方針どおり） |

Proxmox Firewallは現在無効です。管理アクセスを失わないよう、この段階では有効にしません。

## 2.2　ストレージ・ネットワーク・既存ゲストの確認

**実行先：Proxmoxホスト（root@pve）**

ストレージの空き容量を確認します。

⟦C1⟧

ネットワークインターフェースとブリッジの接続状態を確認します。

⟦C2⟧

確認の結果、次のことがわかりました。

- `eno2` はリンクダウン（`NO-CARRIER`）でした。`vmbr1` はProxmox内部の仮想ネットワークとしてだけ動いています。

この時点では、`eno2` と `vmbr1` の設定は変更しません。

## 2.3　ディスクとリンク状態の詳細確認

**実行先：Proxmoxホスト（root@pve）**

ブロックデバイスとLVMの構成を確認します。

⟦C3⟧

> **注意：** `pvesm config` はProxmoxに存在しないコマンドのため、エラーになります。ストレージの定義は、次の2.4で設定ファイルから確認します。

停止中のLXCの設定を確認します（AI関連コンテナを再利用できるかの判断材料）。

⟦C4⟧

`vmbr1` の接続先を確認します。

⟦C5⟧

物理ポートは未接続でも、`vmbr1` 上には既存の仮想マシン・コンテナのIPv6近隣ノードが見えており、内部ブリッジとして機能していることを確認できました。

## 2.4　ストレージ定義の確認

**実行先：Proxmoxホスト（root@pve）**

⟦C6⟧

登録されているストレージは次のとおりです。

| ストレージ | 種類 | 用途 |
|---|---|---|
| `local` | ディレクトリ | ISO・テンプレート・バックアップ |
| `local-lvm` | LVM-thin | VMディスク・LXC rootfs |
| `models` | LVM-thin | VMディスク・LXC rootfs |
| `osx` | LVM-thin | VMディスク・LXC rootfs |
| `ubuntu` | LVM-thin | VMディスク・LXC rootfs |
| `backup` | ディレクトリ | バックアップ・ISO・VMディスクなど |
| `windows_d` / `windows_c` | LVM-thin | VMディスク・LXC rootfs |
| `RAID_A` / `RAID_B` | LVM-thin | VMディスク・LXC rootfs |

## 2.5　物理ディスクの種類とthin poolの確認

**実行先：Proxmoxホスト（root@pve）**

各ストレージの空き容量を確認します。

⟦C7⟧

物理ディスクがSSDかHDDかを確認します。`ROTA` が `0` ならSSD／NVMe、`1` なら回転式HDDです。

⟦C8⟧

thin poolのデータ領域とメタデータ領域の使用率を確認します。

⟦C9⟧

確認結果から、物理ディスクとストレージの対応は次のとおりでした。

| デバイス | 容量 | 種類 | ストレージ | 判断 |
|---|---:|---|---|---|
| `nvme0n1` | 931GB | NVMe SSD | `local-lvm` | 高速。空き約324GB（使用率61.10%） |
| `sda` | 1.9TB | SATA SSD | `ubuntu` | 高速。空き約987GB（使用率49.82%） |
| `sdf` | 931GB | SATA SSD | `osx` | SSD。空き約637GB |
| `sdb` | 5.5TB | HDD | `models` | AIモデル・大容量データ用 |
| `sdc` | 1.8TB | HDD | `RAID_A` | TrueNAS用 |
| `sdd` | 1.8TB | HDD | `RAID_B` | TrueNAS用 |
| `sdg` | 1.8TB | HDD | `backup` | バックアップ |
| `sdh` | 3.6TB | HDD | `windows_d` | ― |
| `sde` | 223GB | SATA SSD | `windows_c` | ― |

候補となる `ubuntu`・`local-lvm`・`osx` のメタデータ使用率は、いずれも約1〜2%で問題のない水準でした。

## 2.6　調査結果から決めたこと

**ネットワークの用途**

| ネットワーク | 用途 |
|---|---|
| `vmbr0` / eno1 | 本番・管理ネットワーク（`192.168.0.0/24`、インターネット接続あり） |
| `vmbr1` / eno2 | 内部サーバー専用ネットワーク（`192.168.1.0/24`）。eno2は現在未接続で、将来PostgreSQLサーバーを接続する |

`vmbr1` にはデフォルトゲートウェイを設定せず、内部通信専用にします。

**ストレージの用途**

- `RAID_A`・`RAID_B` はTrueNAS用の低速HDDで、バックアップ・アーカイブ専用です。防御システムのVMには使いません。
- Wazuh IndexerはログのI/Oが多いため、SSDに配置します。
- `local-lvm`（NVMe）は空きが約324GBのため、2台分（350GB）を両方置くことはしません。

# 第3章　構成の確定

## 3.1　確定した構成

検討の結果、新規VMは2台とし、次の構成で確定しました。VMID 220・221はVMのIDです（LXCではありません）。

| 項目 | VM 220：Security Core | VM 221：AI Defense Manager |
|---|---|---|
| 役割 | Wazuh Server / Indexer / Dashboard | Python / FastAPI / AIエージェント |
| VMID | 220 | 221 |
| vCPU | 8 | 4 |
| RAM | 16GB | 8GB |
| Disk | 250GB | 100GB |
| Storage | `ubuntu`（SATA SSD） | `local-lvm`（NVMe） |
| NIC 1 | vmbr0 | vmbr0 |
| IP 1 | `192.168.0.220/24` | `192.168.0.221/24` |
| NIC 2 | vmbr1 | vmbr1 |
| IP 2 | `192.168.1.220/24` | `192.168.1.221/24` |
| Gateway | `192.168.0.1` | `192.168.0.1` |

- 2台とも固定IPアドレスで、`vmbr0` と `vmbr1` の2 NIC構成にします。
- デフォルトゲートウェイは `vmbr0` 側の `192.168.0.1` だけとし、`vmbr1` 側には設定しません。
- Wazuh公式の目安（25〜100エージェントで8 vCPU・8 GiB RAM・100〜200GB）に対し、ログ量と保持期間に余裕を持たせて16GB・250GBとしました。
- AI Defense Managerは既存のOllamaを利用します。GPUや大容量メモリを二重に確保しません。

既存の次のサービスは再利用します。

- PostgreSQL（LXC 109）
- Ollama / RTX 3090

## 3.2　OS構成

| 項目 | VM 220 | VM 221 |
|---|---|---|
| OS | Ubuntu Server 24.04.5 LTS | Ubuntu Server 24.04.5 LTS |
| BIOS | OVMF (UEFI) | OVMF (UEFI) |
| Machine | q35 | q35 |
| SCSI Controller | VirtIO SCSI Single | VirtIO SCSI Single |
| QEMU Guest Agent | 有効 | 有効 |

> **OSに24.04 LTSを選ぶ理由：** Wazuhの現行安定版（4.14系）の公式Quickstartでは、推奨OSはUbuntu 24.04までです。Ubuntu 26.04は5.x系の対応OSで、4.14系の推奨構成ではありません。長期間稼働させるセキュリティ基盤のため、安定性を優先して **Ubuntu Server 24.04.5 LTS + Wazuh 4.14.10** の組み合わせにします。

# 第4章　VM 220（Security Core）の作成

## 4.1　ISOイメージの確認

**実行先：Proxmoxホスト（root@pve）**

⟦C10⟧

`local` ストレージにUbuntu Server 24.04のISOがない場合は、4.2の手順で取得します。

## 4.2　Ubuntu Server 24.04.5 LTSのISOの取得

**実行先：Proxmoxホスト（root@pve）**

> **注意：** 日本のミラー（`jp.releases.ubuntu.com`）からダウンロードすると、「The certificate's owner does not match hostname」というエラーで止まります。サーバーが返す証明書の対象が `releases.ubuntu.com` と `www.releases.ubuntu.com` だけで、`jp.releases.ubuntu.com` が含まれていないためです。`--no-check-certificate` で証明書の検証を無効にするのではなく、公式のホスト名 `releases.ubuntu.com` から取得してください。

ISOの保存先に移動します。

⟦C11⟧

接続先の証明書を確認します。`DNS:releases.ubuntu.com` が表示されることを確認してください。

⟦C12⟧

ISOをダウンロードします（約3.9GB）。

⟦C13⟧

ファイルを確認します。

⟦C14⟧

SHA256チェックサムを検証し、改ざんやダウンロードの破損がないことを確認します。

⟦C15⟧

次のように表示されれば成功です。

⟦C16⟧

## 4.3　VMIDが未使用であることの確認

**実行先：Proxmoxホスト（root@pve）**

⟦C17⟧

何も表示されなければ、220・221は空いています。

## 4.4　EFIディスク用ストレージの確認

**実行先：Proxmoxホスト（root@pve）**

⟦C18⟧

`ubuntu` に十分な空き（約987GB）があることを確認しました。EFIディスクも `ubuntu` に置きます。

## 4.5　VMの作成

**実行先：Proxmoxホスト（root@pve）**

> これらはVM 220を新規作成する操作です。既存のVMやLXCの設定は変更しません。1つずつ実行し、エラーが出ないことを確認してから次へ進んでください。

VM本体を作成します。

⟦C19⟧

EFIディスクを追加します。

⟦C20⟧

250GBのシステムディスクを作成します。

⟦C21⟧

Ubuntu Server 24.04.5のISOを接続します。

⟦C22⟧

起動順序を設定します。

⟦C23⟧

## 4.6　thin poolの警告について

システムディスクの作成時に、次の警告が表示されます。

⟦C24⟧

これはthin provisioningにより、仮想ディスクの総割当容量が物理容量を超えていることを示す警告です。ディスクの作成自体は成功しています。

- 250GBを作成した時点で、250GBすべてが物理的に消費されるわけではありません。
- ただし、既存VMを含めて実データが増えると、thin poolが満杯になるおそれがあります。満杯になると、そのストレージ上のVM・LXCに深刻な影響が出ます。
- この段階では自動拡張の設定は変更しません。thin poolの使用率を継続して監視します。

## 4.7　VM設定の確認

**実行先：Proxmoxホスト（root@pve）**

> まだVM 220は起動しないでください。設定を確認してから起動します。

⟦C25⟧

次の項目を確認します。

| 項目 | 期待値 |
|---|---|
| CPU / RAM | `cores: 8` / `memory: 16384` |
| EFI | `bios: ovmf`、`efidisk0` が存在 |
| Disk | `scsi0` が `ubuntu` 上の `size=250G` |
| SCSI | `scsihw: virtio-scsi-single` |
| NIC | `net0` が vmbr0、`net1` が vmbr1 |
| Guest Agent | `agent: enabled=1` |
| ISO | `ide2` に `ubuntu-24.04.5-live-server-amd64.iso` |
| Boot | `boot: order=ide2;scsi0`（ISO優先） |

ISO・起動順序・ディスクだけを抜き出して確認することもできます。

⟦C26⟧

実行結果（例）：

⟦C27⟧

## 4.8　VMの起動

**実行先：Proxmoxホスト（root@pve）**

⟦C28⟧

エラーが表示されずにプロンプトに戻れば成功です。

# 第5章　Ubuntu Serverのインストール

## 5.1　インストーラーの起動

Proxmox Web UIで次の操作を行います。

1. `VM 220 security-core` を選択する。
2. **Console** を開く。
3. インストーラーのメニューで `Try or Install Ubuntu Server` を選択する。

## 5.2　インストール時の設定

インストーラーの画面ごとの操作は、Ubuntu Serverの一般的なインストール手順と同じため割愛します。次の表の値で設定してください。

| 項目 | 設定 |
|---|---|
| Language | English（ログや技術情報との整合性を優先） |
| Keyboard | Japanese（または使用中のキーボード配列） |
| Installation type | Ubuntu Server |
| ネットワーク | 1つ目のNIC（`enp6s18`、vmbr0側）だけを設定 |
| IP | `192.168.0.220/24` |
| Gateway | `192.168.0.1` |
| ホスト名 | `security-core` |
| Storage | 250GBのディスク全体を使用（LVM構成） |
| OpenSSH Server | Install |
| Additional packages | 何も追加しない |

> **重要：** 2つ目のNIC（`enp6s19`、vmbr1側）の `192.168.1.220` は、インストール後に設定します。デフォルトゲートウェイはvmbr0側だけにします。

## 5.3　インストールメディアの取り外し

インストールが終わると、Consoleに次のメッセージが表示されて止まります。

⟦C29⟧

これはインストールの失敗ではなく、仮想CD-ROM（ISO）の取り外しを待っている状態です。

> **注意：** この状態でWeb UIからShutdownやResetを続けて実行すると、Proxmoxが「can't lock file '/var/lock...」というエラーを出すことがあります。ResetやShutdownを繰り返したり、`/var/lock` 内のファイルを削除したりせず、次の手順でISOを取り外してください。

**実行先：Proxmoxホスト（root@pve）**

⟦C30⟧

仮想CD-ROMだけが取り外されます。250GBの仮想ディスクには影響しません。

ProxmoxのConsoleに戻り、`Enter` キーを押します。Ubuntuが再起動し、インストールしたOSが起動します。

# 第6章　OSの初期設定

この章のコマンドは、ProxmoxホストではなくVM 220のUbuntu上で、rootとして実行します。

## 6.1　OSとネットワークの確認

**実行先：security-core VM 220（root）**

⟦C31⟧

リソースも確認します。

⟦C32⟧

次の状態であることを確認します。

| 項目 | 期待値 |
|---|---|
| OS | `PRETTY_NAME="Ubuntu 24.04.5 LTS"` |
| ホスト名 | `security-core` |
| enp6s18（vmbr0） | `192.168.0.220/24` |
| enp6s19（vmbr1） | NICは存在するが、IPアドレスなし（DOWN） |
| デフォルトルート | `default via 192.168.0.1 dev enp6s18` |
| メモリ | 約15GiB、Swap 4GiB |

> **NIC名について：** Ubuntu 24.04では、NICの名前が `enp6s18`（vmbr0側）と `enp6s19`（vmbr1側）になります。MACアドレスはProxmoxの `net0`・`net1` と一致します。

## 6.2　Netplan設定の確認

**実行先：security-core VM 220（root）**

⟦C33⟧

⟦C34⟧

⟦C35⟧

インストーラーが作成した `50-cloud-init.yaml` に、`enp6s18` の固定IPとデフォルトルートだけが設定されていることを確認します。

## 6.3　内部LAN（enp6s19）への固定IPの追加

**実行先：security-core VM 220（root）**

`enp6s19` に `192.168.1.220/24` を設定します。`enp6s19` にはゲートウェイを設定しません。

> SSHで接続している場合は、ネットワークが切断されたときに備えて、ProxmoxのConsoleも開いておいてください。

まず設定ファイルのバックアップを作成します。

⟦C36⟧

設定ファイルを書き換えます。

⟦C37⟧

設定を検証して、試験適用します。

⟦C38⟧

次の確認画面が表示されたら、**すぐにEnterキーを押して**設定を確定します。

⟦C39⟧

> **注意：** 時間内にEnterを押さないと「Reverting.」と表示され、自動的に元の設定に戻ります。これはエラーではありません。その場合はもう一度 `netplan try --timeout 60` を実行してください。

## 6.4　ネットワーク設定の確認

**実行先：security-core VM 220（root）**

⟦C40⟧

| 項目 | 期待値 |
|---|---|
| enp6s18 / vmbr0 | `192.168.0.220/24` |
| enp6s19 / vmbr1 | `192.168.1.220/24`（UP） |
| デフォルトゲートウェイ | `192.168.0.1`（enp6s18）のみ |
| 内部LANの経路 | `192.168.1.0/24 dev enp6s19` |
| ping（Proxmoxの内部ブリッジ `192.168.1.254`） | `3 packets transmitted, 3 received, 0% packet loss` |

## 6.5　OSの更新

**実行先：security-core VM 220（root）**

⟦C41⟧

完了したら再起動します。

⟦C42⟧

再起動後、状態を確認します。

⟦C43⟧

| 項目 | 期待値 |
|---|---|
| IPアドレス | `192.168.0.220` と `192.168.1.220` が維持されている |
| デフォルトゲートウェイ | `192.168.0.1` |
| `systemd-timesyncd`（時刻同期） | `active` |
| `qemu-guest-agent` | この時点では `inactive`（6.7で導入） |
| ルート領域（`/`） | 約98GB（6.6で拡張） |

## 6.6　ルート領域の拡張

インストーラーのLVM構成では、250GBの仮想ディスクのうち100GBしかルート領域に割り当てられません。Wazuh Indexerのログ保存領域を確保するため、残りをすべてルート領域に追加します。

**実行先：security-core VM 220（root）**

LVMの空き容量を確認します。

⟦C44⟧

実行結果（例）：

⟦C45⟧

約146.95GBの未使用領域があります。これをすべてルート領域に追加し、ファイルシステムも同時に拡張します。

⟦C46⟧

結果を確認します。

⟦C47⟧

| 項目 | 期待値 |
|---|---|
| ルート領域 | 243G |
| 空き容量 | 約225G |
| 論理ボリューム | `<246.95g` |

再起動は不要です。

## 6.7　QEMU Guest Agentの導入

ProxmoxからVMのIPアドレスや稼働状態を取得するために必要です。

**実行先：security-core VM 220（root）**

⟦C48⟧

自動起動を有効にして起動します。

⟦C49⟧

状態を確認します。

⟦C50⟧

`Active: active (running)` と表示されれば成功です。

## 6.8　OS初期設定の完了状態

| 項目 | 状態 |
|---|---|
| OS | Ubuntu Server 24.04.5 LTS |
| ホスト名 | `security-core` |
| enp6s18 | `192.168.0.220/24`（デフォルトゲートウェイ `192.168.0.1`） |
| enp6s19 | `192.168.1.220/24`（ゲートウェイなし） |
| ルート領域 | 243GB（空き約225GB） |
| 時刻同期 | active |
| QEMU Guest Agent | active (running) |
| OS更新 | 完了 |

# 第7章　Wazuhのインストール

## 7.1　配布サーバーへの接続確認

インストーラーをダウンロードする前に、DNSとHTTPSの接続を確認します。

**実行先：security-core VM 220（root）**

⟦C51⟧

`packages.wazuh.com` の名前解決ができ、HTTPの応答（`200`）が返ることを確認します。

## 7.2　インストーラーのダウンロード

公式のインストーラーをダウンロードします。この段階ではまだインストールは実行しません。

**実行先：security-core VM 220（root）**

⟦C52⟧

ファイルサイズ（約211KB）、SHA256、先頭の5行（`#!/bin/bash` と `# Wazuh installer`）を確認します。

## 7.3　インストーラーのバージョン確認

**実行先：security-core VM 220（root）**

⟦C53⟧

実行結果（例）：

⟦C54⟧

## 7.4　All-in-Oneのインストール

`-a` オプションで、次の3つのコンポーネントを同じホストにまとめて導入します。

1. **Wazuh Indexer**：セキュリティイベントの保存・検索
2. **Wazuh Server（Manager）**：エージェント管理・脅威検知
3. **Wazuh Dashboard**：Web管理画面

**実行先：security-core VM 220（root）**

⟦C55⟧

> **実行時の注意**
>
> - インストールには数分から数十分かかります。
> - 途中でエラーが発生した場合は、再実行せずにログを確認してください。
> - `wazuh-install-files.tar` には証明書や内部ユーザーの認証情報が含まれます。外部に公開しないでください。

最後に `INFO: --- Summary ---` が表示され、Web画面のURL、ユーザー名 `admin`、初期パスワードが表示されたあと、`INFO: Installation finished.` で終われば成功です。

> **重要：** 初期パスワードは画面に表示されます。この出力をチャットや資料に貼らないでください。初期パスワードは第3章で変更します。

# 第8章　サービスと待ち受けポートの確認

## 8.1　3サービスの稼働確認

**実行先：security-core VM 220（root）**

⟦C56⟧

3行とも `active` と表示されれば正常です。

## 8.2　待ち受けポートの確認

VM 220は通常LANと内部ネットワークの2系統を持つため、各サービスがどのインターフェースで待ち受けているかを確認します。

**実行先：security-core VM 220（root）**

⟦C57⟧

⟦C58⟧

構築時の待ち受け状態は次のとおりでした。

| ポート | サービス | 待ち受け | 評価 |
|---|---|---|---|
| 443 | Dashboard | `0.0.0.0:443` | すべてのIPv4インターフェースで接続可能 |
| 55000 | Manager API | `0.0.0.0:55000` / `[::]:55000` | IPv4・IPv6のすべてのインターフェースで接続可能 |
| 9200 | Indexer | `127.0.0.1:9200` | ローカル限定（良好） |

Indexerの9200番がlocalhost限定なのは望ましい状態です。Manager API（55000番）とDashboard（443番）は、今後のアクセス制限の検討対象とします。

## 8.3　APIとDashboardの設定確認

アクセス制限を検討するために、Manager API・Dashboardの設定ファイルの現在値と、ファイアウォールの状態を確認します。確認だけで、設定ファイルの編集やUFWの有効化はしません。

**実行先：security-core VM 220（root）**

⟦C59⟧

| 対象 | 今後の方針 |
|---|---|
| Dashboard | 管理端末からのアクセスを許可する |
| Manager API | 原則としてlocalhostと、必要な内部の接続元だけに制限する |
| Indexer | localhost限定を維持する |
| IPv6 | 意図しない外部公開を防ぐ |

> 構築時はこの確認を実施しましたが、出力は記録に残っていません。お使いの環境の出力で、待ち受けアドレスとUFWの状態を確認してください。この段階では設定は変更しません。

# 第9章　adminパスワードの変更

## 9.1　変更方法について

`admin` はWazuh Indexerの予約済み内部ユーザー（reserved user）です。Dashboardのユーザー管理画面から変更しようとすると、次のエラーになります。

⟦C60⟧

`admin` のパスワードは、Wazuh付属のパスワード管理ツールで変更します。All-in-One構成では、このツールがFilebeatなど関連コンポーネントの認証情報も自動で更新します。

## 9.2　パスワード管理ツールの確認

**実行先：security-core VM 220（root）**

⟦C61⟧

⟦C62⟧

`wazuh-passwords-tool.sh` が存在することを確認します。

使い方を確認します。

⟦C63⟧

`-u` で対象ユーザーを指定します。`-p` を付けなければ、新しいパスワードが自動生成されます。

## 9.3　パスワードの再発行（画面に表示しない方法）

パスワードを自動生成し、出力をroot専用のファイルに保存します。こうすることで、新しいパスワードが画面やログの貼り付けに残りません。

**実行先：security-core VM 220（root）**

⟦C64⟧

次の内容が出力されていれば成功です。

- `INFO: Updating the internal users.`
- 内部ユーザー情報のバックアップ（`/etc/wazuh-indexer/internalusers-backup`）の作成
- `The filebeat.yml file has been updated to use the Filebeat Keystore username and password.`
- `WARNING: Password changed. Remember to update the password ...`（サービスの再起動を促すメッセージ）

新しいパスワードは、VMのターミナル上だけで確認します。

⟦C65⟧

表示されたパスワードを、安全なパスワード管理先に保存してください。**この出力はチャットや資料に貼らないでください。**

## 9.4　サービスの再起動

パスワード変更を反映するため、Indexer → Manager → Filebeat → Dashboard の順に1つずつ再起動します。それぞれ `active` になったことを確認してから次へ進みます。

**実行先：security-core VM 220（root）**

Indexerを再起動します。

⟦C66⟧

⟦C67⟧

Managerを再起動します。

⟦C68⟧

⟦C69⟧

Filebeatを再起動します。

⟦C70⟧

⟦C71⟧

Dashboardを再起動します。

⟦C72⟧

⟦C73⟧

4つのサービスがすべて `active` になれば完了です。

# 第10章　動作確認

## 10.1　内部接続の確認

各サービスがHTTPで応答するかを確認します。

**実行先：security-core VM 220（root）**

⟦C74⟧

実行結果（例）：

⟦C75⟧

| コンポーネント | 応答 | 意味 |
|---|---:|---|
| Indexer | 401 | 認証情報のないアクセスを拒否している（認証機能が応答している） |
| Wazuh API | 401 | 同上 |
| Dashboard | 302 | ログイン画面へリダイレクトしている |

いずれも正常な応答です。

## 10.2　FilebeatからIndexerへの接続確認

**実行先：security-core VM 220（root）**

⟦C76⟧

実行結果（例）：

⟦C77⟧

TLSハンドシェイクと `talk to server... OK` が確認できれば、ログ転送経路は正常です。

## 10.3　Dashboardへのログイン

管理端末のブラウザで `https://192.168.0.220` を開きます。

- ユーザー名：`admin`
- パスワード：9.3で再発行したパスワード

自己署名証明書の警告が表示される場合がありますが、この段階では想定内です。接続先が `192.168.0.220` であることを確認してから進んでください。

次の3点を確認します。

1. ログインできる。
2. WazuhのOverview画面が表示される。
3. IndexerやAPIの接続エラーが表示されていない。

# 第11章　ProxmoxホストへのWazuh Agentの導入

最初の監視対象として、仮想マシンを管理しているProxmoxホスト `pve`（`192.168.0.240`）を登録します。ホストOSのログ、ファイルの変更、セキュリティ設定などをWazuhで監視できるようになります。既存のProxmoxの設定やネットワーク構成は変更せず、Agentだけを追加します。

| 通信 | ポート | 用途 |
|---|---|---|
| Agent → Manager | TCP 1514 | イベントの送信 |
| Agent → Manager | TCP 1515 | Agentの登録（Enrollment） |

## 11.1　Manager側の受け入れポートの確認

**実行先：security-core VM 220（root）**

⟦C78⟧

| ポート | プロセス | 状態 |
|---|---|---|
| TCP 1514 | `wazuh-remoted` | LISTEN |
| TCP 1515 | `wazuh-authd` | LISTEN |

## 11.2　Proxmoxホストの環境確認

この段階では、パッケージのインストールやProxmoxの設定変更は行いません。

**実行先：Proxmoxホスト（root@pve）**

⟦C79⟧

| 確認項目 | 期待値 |
|---|---|
| Proxmox VE | 8.4.0 |
| OS | Debian 12 Bookworm |
| アーキテクチャ | `amd64` |
| VM 220への疎通 | パケット損失0% |
| 既存のWazuh Agent | なし（何も表示されない） |

## 11.3　Wazuh公式APTリポジトリの登録

**実行先：Proxmoxホスト（root@pve）**

必要なパッケージを入れます。

⟦C80⟧

公式の署名鍵を登録します。

⟦C81⟧

APTリポジトリを登録します。

⟦C82⟧

パッケージ情報を更新します。

⟦C83⟧

取得できるバージョンを確認します。

⟦C84⟧

候補に `4.14.10-1` が表示されることを確認します。この段階ではまだAgentをインストールしません。

## 11.4　Agent通信ポートの疎通確認

ProxmoxホストからVM 220への、TCP 1514・1515の接続を確認します。

**実行先：Proxmoxホスト（root@pve）**

⟦C85⟧

次のように表示されれば正常です。

⟦C86⟧

## 11.5　Wazuh Agent 4.14.10のインストール

Managerと同じバージョンに固定してインストールします。

**実行先：Proxmoxホスト（root@pve）**

⟦C87⟧

バージョンを確認します。

⟦C88⟧

`Wazuh v4.14.10 - Wazuh Inc.` と表示されれば成功です。この時点ではまだAgentを起動しません。

## 11.6　Managerの接続先の設定

**実行先：Proxmoxホスト（root@pve）**

設定ファイルのバックアップを作成します。

⟦C89⟧

現在の設定を確認します。

⟦C90⟧

`<address>MANAGER_IP</address>` という初期値が入っていることを確認します。

ManagerのIPアドレス `192.168.0.220` に書き換えます。

⟦C91⟧

変更結果を確認します。

⟦C92⟧

実行結果（例）：

⟦C93⟧

## 11.7　Agentの登録

まず、Manager側の登録サービスの設定を確認します。

**実行先：security-core VM 220（root）**

⟦C94⟧

| 設定 | 値 | 意味 |
|---|---|---|
| `disabled` | `no` | 登録サービスが有効 |
| `port` | `1515` | 登録ポート |
| `use_password` | `no` | 登録パスワードは不要 |
| `use_source_ip` | `no` | 接続元IPを固定登録しない |
| `purge` | `yes` | 古い登録情報を整理する |

Proxmoxホストから、Agentを `pve` という名前で登録します。

**実行先：Proxmoxホスト（root@pve）**

⟦C95⟧

実行結果（例）：

⟦C96⟧

`Valid key received` が表示されれば、ManagerからAgentの認証キーを取得できています。

## 11.8　Agentの起動

**実行先：Proxmoxホスト（root@pve）**

自動起動を有効にして起動します。

⟦C97⟧

状態を確認します。

⟦C98⟧

`Active: active (running)` と表示され、`wazuh-agentd`・`wazuh-syscheckd`・`wazuh-logcollector`・`wazuh-modulesd` が起動していれば成功です。

> 起動直後のメモリ使用量は約844MBでした。他のLXCなどに導入するときは、メモリへの影響に注意してください。

## 11.9　Manager側での接続確認

**実行先：security-core VM 220（root）**

⟦C99⟧

実行結果（例）：

⟦C100⟧

一覧に表示されたIDを指定して、詳細を確認します（構築時は `001`）。

⟦C101⟧

`Status: Active` で、`Last keep alive` と Syscheck の実行記録があることを確認します。`IP address: any` は、接続元IPを固定登録しない設定のためで、正常です。

## 11.10　Agentログの確認

**実行先：Proxmoxホスト（root@pve）**

⟦C102⟧

次のログが出ていることを確認します。

| 機能 | 確認するログ |
|---|---|
| ファイル整合性監視（FIM） | 初期スキャンの終了（`File integrity monitoring scan ended`） |
| SCAセキュリティ評価 | `Evaluation finished for policy '/var/ossec/ruleset/sca/cis_debian12.yml'`、`Security Configuration Assessment scan finished.` |
| Syscollector | システム情報の収集完了 |

Rootcheckの状態と、エラー・警告の有無を確認します。

⟦C103⟧

⟦C104⟧

構築時は、Rootcheckは `Starting rootcheck scan.` の開始ログだけで、`ERROR`・`WARNING`・`CRITICAL` は0件でした。Rootcheckの完了は継続して確認します。

以上で、Proxmoxホストの監視は第一段階完了です。

# 第12章　監視対象VM・LXCの棚卸し

既存のVM・LXCにAgentを展開する前に、対象を一覧化します。一括導入は行わず、稼働中のゲストを1台ずつ確認しながら、個別に導入します。

**実行先：Proxmoxホスト（root@pve）**

⟦C105⟧

構築時の棚卸し結果をもとに、次の方針を決めました。

| 分類 | 対象 | 方針 |
|---|---|---|
| Proxmoxホスト | `pve` | 導入済み |
| Wazuh管理サーバー | VM 220 `security-core` | 稼働中 |
| GPU・AI基盤 | VM 101 `ollama-gpu` | OSとメモリの状況を確認してから判断 |
| 仮想マシン | VM 104 `vs-ubuntu` | OSを確認してから判断 |
| 監視基盤 | LXC 103 `lxc-prometheus`、LXC 105 `lxc-grafana` | 監視対象の候補 |
| データベース | LXC 109 `postgresql`、503 `demo-postgresql` | 重要度と負荷を確認してから判断 |
| アプリケーション | LXC 200、129、500など | 稼働状況・OS・用途を確認して選定 |
| ストレージ・検索 | LXC 134、502 | メモリ・用途を確認して判断 |

- 停止中のVM・LXCは、現時点では対象にしません。
- TrueNAS・Windows・macOSは、Linux用のAgentをそのまま導入する対象にしません。
- RKE2は対象外です。既存のリソースを停止・削除することもしません。

# 第13章　LXCへの導入方針

第12章の棚卸し結果に沿って、既存のLXCコンテナにWazuh Agentを1台ずつ導入します。この章では、第14章以降に共通する進め方をまとめます。

## 13.1　2つの実行方法

LXCへの操作には、次の2つの方法があります。本書では、構築時に実際に使った方法をそのまま掲載しています。

| 方法 | プロンプトの例 | 説明 |
|---|---|---|
| Proxmoxホストから実行 | `root@pve` | `pct exec <CTID> --` を付けて、ホストからコンテナ内のコマンドを実行する |
| コンテナ内で実行 | `root@lxc-prometheus` | コンテナにrootでログインし、コマンドを直接実行する |

> **注意：** `pct` はProxmoxホスト専用のコマンドです。コンテナ内で `pct exec ...` を実行すると、`-bash: pct: command not found` になります。プロンプトの表示で、今どこにいるかを必ず確認してください。

## 13.2　すべてのLXCに共通する方針

- 既存のサービス（Prometheus・Grafana・PostgreSQL）の設定は変更しません。
- Agentのバージョンは、Managerと同じ4.14.10-1に固定します。
- 導入前に、OS・メモリ・既存Agentの有無・Managerへの通信を確認します。
- 1台ずつ導入し、Manager側で `Active` になったことを確認してから次へ進みます。
- PVEホストに登録したWazuhリポジトリは、LXCの中には引き継がれません。LXCごとに署名鍵とリポジトリを登録します。

# 第14章　LXC 103（lxc-prometheus）への導入

## 14.1　コンテナの確認

この作業では設定変更もAgentの導入も行いません。

**実行先：Proxmoxホスト（root@pve）**

⟦C106⟧

構築時の確認結果：

| 項目 | 結果 |
|---|---|
| OS | Debian 13.5 (trixie) |
| CPU | 2コア |
| メモリ割当 | 4GB（使用79MiB、利用可能3.9GiB） |
| IPアドレス | `192.168.0.197` |
| LXCの種類 | unprivileged（nesting有効） |

> unprivileged LXCでは、RootcheckやFIM（ファイル整合性監視）などの結果が、ホスト側の制約を受けて通常のVMと異なる場合があります。

## 14.2　既存Agentと経路の確認

**実行先：Proxmoxホスト（root@pve）**

⟦C107⟧

実行結果（例）：

⟦C108⟧

## 14.3　Managerへの通信確認

TCP 1514（Agent通信）と1515（Agent登録）に接続できるかを確認します。

**実行先：Proxmoxホスト（root@pve）**

⟦C109⟧

次のように表示されれば正常です。

⟦C110⟧

## 14.4　リポジトリの登録状況の確認

**実行先：Proxmoxホスト（root@pve）**

⟦C111⟧

見出しだけが表示され、リポジトリも候補バージョンも出てこなければ未登録です。次の手順で登録します。

## 14.5　署名鍵の登録

ここからはLXC 103の中で作業します。ProxmoxのWeb画面でLXC 103を選択し、**Console** からrootでログインしてください（プロンプトが `root@lxc-prometheus` になります）。

**実行先：LXC 103 内（root@lxc-prometheus）**

⟦C112⟧

最後に `Wazuh signing key installed.` と表示されれば成功です。

## 14.6　APTリポジトリの登録

**実行先：LXC 103 内（root@lxc-prometheus）**

⟦C113⟧

`https://packages.wazuh.com/4.x/apt stable InRelease` が取得できれば成功です。

## 14.7　候補バージョンと依存関係の確認

**実行先：LXC 103 内（root@lxc-prometheus）**

⟦C114⟧

`Candidate: 4.14.10-1` と表示され、依存関係が標準的なDebianパッケージ（`libc6`、`lsb-release`、`debconf`、`adduser`、`procps`）であることを確認します。

## 14.8　Agentのインストール

**実行先：LXC 103 内（root@lxc-prometheus）**

⟦C115⟧

追加でインストールされるのは `lsb-release` と `wazuh-agent` の2つだけです。この段階ではまだ登録も起動もしません。

## 14.9　Managerの接続先の設定

**実行先：LXC 103 内（root@lxc-prometheus）**

⟦C116⟧

実行結果（例）：

⟦C117⟧

## 14.10　Agentの登録

Agent名を `lxc-prometheus` として登録します。

**実行先：LXC 103 内（root@lxc-prometheus）**

⟦C118⟧

最後に `INFO: Valid key received` と表示されれば成功です。

## 14.11　Agentの起動

**実行先：LXC 103 内（root@lxc-prometheus）**

⟦C119⟧

`Active: active (running)` と表示されれば成功です。構築時のメモリ使用量は約84MBで、Proxmoxホスト（約844MB）よりかなり軽量でした。

## 14.12　Manager側での確認

**実行先：security-core VM 220（root）**

⟦C120⟧

実行結果（例）：

⟦C121⟧

`lxc-prometheus` が `Active` になれば、LXC 103への導入は完了です。

# 第15章　LXC 105（lxc-grafana）への導入

## 15.1　コンテナの確認

**実行先：LXC 105 内（root@lxc-grafana）**

⟦C122⟧

**実行先：Proxmoxホスト（root@pve）**

⟦C123⟧

構築時の確認結果：

| 項目 | 結果 |
|---|---|
| OS | Debian 13.5 (trixie) |
| CPU | 1コア |
| メモリ割当 | 512MB（使用170MiB、利用可能341MiB） |
| Swap | 512MB |
| RootFS | 4GB（`osx` ストレージ） |
| IPアドレス | `192.168.0.199` |
| LXCの種類 | unprivileged |

## 15.2　メモリの増設

利用可能なメモリが341MiBしかなく、LXC 103でAgentが約84MBを使った実績から、このままではGrafanaがメモリ不足で止まるおそれがあります。Agentを導入する前に、メモリ割当を増やします。

| 項目 | 変更前 | 変更後 |
|---|---:|---:|
| RAM | 512MB | **1,024MB** |
| Swap | 512MB | 512MB（変更なし） |
| CPU | 1コア | 1コア（変更なし） |
| RootFS | 4GB | 4GB（変更なし） |

ProxmoxのWeb画面でLXC 105を選択し、**Resources** の **Memory** を1,024MBに変更してください（Swap・CPU・RootFSは変更しません）。

> **目安：** 1GBは導入するための最低限の推奨値です。余裕を持たせたい場合は1.5GB、Grafanaのデータソースやダッシュボードが増える場合は2GBを検討してください。変更時にGrafanaの停止・再起動が必要になる場合があります。

変更が反映され、Grafanaが稼働していることを確認します。

**実行先：Proxmoxホスト（root@pve）**

⟦C124⟧

実行結果（例）：

⟦C125⟧

利用可能メモリが約802MBに増え、Grafanaも `active` です。

## 15.3　導入前の確認

必要なコマンドと、既存Agentの有無を確認します。

**実行先：Proxmoxホスト（root@pve）**

⟦C126⟧

`curl` と `gpg` が見つかり（`/bin/curl`、`/bin/gpg`）、`Wazuh Agent not installed` と表示されることを確認します。

## 15.4　署名鍵とリポジトリの登録

**実行先：Proxmoxホスト（root@pve）**

⟦C127⟧

`Wazuh repository configured.` と表示されれば成功です。

## 15.5　候補バージョンの確認

**実行先：Proxmoxホスト（root@pve）**

⟦C128⟧

候補に `4.14.10-1` が表示されることを確認します。システム全体のアップグレードは行いません。

## 15.6　Agentのインストール

Agentだけを指定してインストールします。

**実行先：Proxmoxホスト（root@pve）**

⟦C129⟧

追加でインストールされるのは `lsb-release` と `wazuh-agent` の2つだけで、Grafanaのパッケージは更新されません。

## 15.7　Managerの接続先の設定

**実行先：Proxmoxホスト（root@pve）**

⟦C130⟧

実行結果（例）：

⟦C131⟧

## 15.8　Agentの登録

**実行先：Proxmoxホスト（root@pve）**

⟦C132⟧

最後に `INFO: Valid key received` と表示されれば成功です。

## 15.9　Agentの起動

**実行先：Proxmoxホスト（root@pve）**

⟦C133⟧

`Active: active (running)` と `enabled` を確認します。構築時のメモリ使用量は約95MB（ピーク約97MB）でした。

## 15.10　Manager側での確認

> VM 220は仮想マシン（LXCではない）ため、`pct exec 220` では実行できません。security-coreに直接ログインして実行してください。

**実行先：security-core VM 220（root）**

⟦C134⟧

実行結果（例）：

⟦C135⟧

## 15.11　監視動作とメモリの確認

Agentが `Active` になっただけでなく、監視が実際に動いているかを確認します。

**実行先：Proxmoxホスト（root@pve）**

⟦C136⟧

構築時の確認結果：

| 項目 | 結果 |
|---|---|
| FIM | 初回スキャン完了 |
| Rootcheck | `Ending rootcheck scan.` を確認 |
| SCA | `cis_debian13.yml` の評価完了 |
| Grafana | `active` |

各プロセスのメモリ（RSS）は次のとおりで、合計約58.9MiBでした（共有メモリの重複を含む可能性があります）。

| プロセス | RSS |
|---|---:|
| wazuh-agentd | 約7.6MiB |
| wazuh-syscheckd | 約13.6MiB |
| wazuh-logcollector | 約16.6MiB |
| wazuh-modulesd | 約21.1MiB |

# 第16章　LXC 109（postgresql）への導入

PostgreSQLは、AI防御システムの監査ログやインシデント情報を保存する重要な基盤です。データベースの既存データや設定は変更しません。

## 16.1　コンテナの確認

**実行先：Proxmoxホスト（root@pve）**

⟦C137⟧

⟦C138⟧

構築時の確認結果：

| 項目 | 結果 |
|---|---|
| OS | Debian 13 (trixie) |
| PostgreSQL | 17.11、`active` |
| CPU | 2コア |
| メモリ割当 | 4,096MB（使用139MiB、利用可能3.9GiB） |
| Swap | 512MB |
| RootFS | 50GB（`local-lvm`） |
| IPアドレス | `192.168.0.151` |
| LXCの種類 | unprivileged |

メモリには十分な余裕があるため、増設は不要です。

## 16.2　導入前の確認

**実行先：Proxmoxホスト（root@pve）**

⟦C139⟧

実行結果（例）：

⟦C140⟧

## 16.3　署名鍵とリポジトリの登録

**実行先：Proxmoxホスト（root@pve）**

⟦C141⟧

実行結果（例）：

⟦C142⟧

## 16.4　候補バージョンの確認

**実行先：Proxmoxホスト（root@pve）**

⟦C143⟧

候補に `4.14.10-1` が表示されることを確認します。

## 16.5　Agentのインストール

**実行先：Proxmoxホスト（root@pve）**

⟦C144⟧

`Wazuh v4.14.10 - Wazuh Inc.` と表示されれば成功です。

## 16.6　Managerの接続先の設定

**実行先：Proxmoxホスト（root@pve）**

⟦C145⟧

`<client>` ブロックの `<address>` が `192.168.0.220` になり、バックアップファイル `ossec.conf.backup-before-manager` が作成されていることを確認します。

## 16.7　Agentの登録

Agent名を `postgresql` として登録します。

**実行先：Proxmoxホスト（root@pve）**

⟦C146⟧

最後に `INFO: Valid key received` と表示されれば成功です。

## 16.8　Agentの起動

**実行先：Proxmoxホスト（root@pve）**

⟦C147⟧

`active (running)` と `enabled` を確認します。構築時のメモリ使用量は約93.3MBでした。

## 16.9　Manager側での確認

**実行先：security-core VM 220（root）**

⟦C148⟧

実行結果（例）：

⟦C149⟧

## 16.10　初期スキャンの確認

**実行先：Proxmoxホスト（root@pve）**

⟦C150⟧

構築時の確認結果：

| 監視機能 | 結果 |
|---|---|
| FIM（ファイル改ざん検知） | 完了 |
| Rootcheck | 完了 |
| SCA（Debian 13 CISベンチマーク評価） | 完了 |
| Syscollector | 完了 |
| PostgreSQLサービス | `active` |

> **ログの読み方：**
>
> - `netstat not available` は、ポート確認機能がスキップされたことを示します。致命的なエラーではありません。
> - `/var/log/apache2/error.log` の監視開始ログは、Agentの既定設定によるものです。PostgreSQLのログ監視は、これとは別に設定します（第2部）。
> - 「WARNINGS / ERRORS」の欄にApacheログの監視開始（INFO）行が出ることがありますが、検索語に一致しただけで、実際のエラーではありません。

## 第1部の完了状態

| Agent ID | 名前 | 対象 | 状態 |
|---:|---|---|---|
| 000 | security-core | VM 220（Manager） | Active/Local |
| 001 | pve | Proxmoxホスト | Active |
| 002 | lxc-prometheus | LXC 103 | Active |
| 003 | lxc-grafana | LXC 105（RAM 1GBに増設） | Active |
| 004 | postgresql | LXC 109 | Active |

| 項目 | 状態 |
|---|---|
| Wazuh Indexer / Manager / Dashboard | 4.14.10、active |
| Filebeat | active、Indexerへの接続OK |
| `admin` パスワード | 再発行済み（画面に表示しない方法） |
| Dashboard | `https://192.168.0.220` でログイン可能 |

Wazuhの監視対象は、Manager自身を含めて5台になりました。

第2部では、LXC 109のPostgreSQLログをWazuhで監視します。SQL文やパラメーター値をWazuh Managerに転送しないよう、ログをローカルでサニタイズ（不要な情報を取り除く処理）してから送る方式を構築します。

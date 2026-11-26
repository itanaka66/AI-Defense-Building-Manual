---
title: "AI自律型サイバー防御システム 構築マニュアル 前編"
subtitle: "第3部　アラート保存Collectorの構築"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」前編の第3部です。Wazuhが検知したアラートをPostgreSQLに保存し、インシデントとして管理するための仕組み（Incident Collector）を構築します。

| 構成要素 | 役割 |
|---|---|
| Wazuh Manager（VM 220） | 検知・相関分析を行い、アラートを `alerts.json` に記録する |
| Incident Collector（VM 220） | アラートを読み取り、検証し、重複を除いてDBへ登録する |
| PostgreSQL（LXC 109） | インシデントDB・イベント履歴を保存する |
| AI分析エージェント（今後） | 脅威の評価、優先順位付け、対応の提案を行う |

## 本書の表記

- コマンドやファイル内容は、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 各手順の冒頭に「実行先」を示します。LXC 109への操作はProxmoxホストから `pct exec 109 --` で、VM 220への操作はProxmoxホストから `qm guest exec 220 --` で実行します（VM 220に直接ログインして実行する手順もあります）。
- 「実行結果（例）」は構築時の実際の出力です。お使いの環境では、IDや日時などが異なります。
- パスワードは画面やチャット、コマンド履歴に残さない方法で設定します。

## 第2部終了時点の状態

| 項目 | 状態 |
|---|---|
| Wazuh Manager | VM 220（`192.168.0.220`）、4.14.10 |
| PostgreSQL | LXC 109（`192.168.0.151`）、17.11 |
| PostgreSQL監視 | サニタイズフィルター、ルール100100〜100106 |

# 第1章　保存先データベースの準備

既存のPostgreSQLやWazuhの設定を壊さないよう、まずデータベースの構成を調べてから、インシデント管理用のスキーマとロールを作ります。

## 1.1　既存データベースの確認

**実行先：Proxmoxホスト（root@pve）**

⟦C0⟧

構築時は17個のデータベースがあり、その中にセキュリティ用途の `security_workbench`（所有者 `security_workbench`）がありました。

## 1.2　security_workbenchの中身の確認

新しいデータベースを作る前に、`security_workbench` がすでに使われていないかを確認します。この節の操作はすべて読み取り専用です。

**実行先：Proxmoxホスト（root@pve）**

⟦C1⟧

ユーザーテーブルが `(0 rows)` であることを確認します。

スキーマとロールを確認します。

⟦C2⟧

`public` スキーマに対する権限を確認します。

⟦C3⟧

| 項目 | 構築時の状態 |
|---|---|
| ユーザーテーブル | 0件 |
| ユーザースキーマ | `public` のみ |
| `security_workbench` ロール | 一般ユーザー（SUPERUSER・CREATEDB・CREATEROLEなし、LOGINあり） |
| `public` スキーマの権限 | `security_workbench` に USAGE・CREATE あり |

> `information_schema.schema_privileges` というビューはPostgreSQL 17には存在しません。スキーマの権限は、上のように `has_schema_privilege()` 関数で確認します。

**決定事項：** 既存の `security_workbench` データベースを使います。ただし既存の `public` スキーマには手を加えず、インシデント管理専用の `incident` スキーマを新しく作ります。また、Wazuhからイベントを書き込む「収集用ロール」と、スキーマ・テーブルを管理するロール（`postgres`）を分けます。既存の `security_workbench` ロールの権限は変更しません。

## 1.3　専用スキーマの作成

ここからデータベースへの変更が始まります。この操作は専用スキーマを1つ作るだけで、既存のテーブルやデータには触れません。

**実行先：Proxmoxホスト（root@pve）**

⟦C4⟧

実行結果（例）：

⟦C5⟧

## 1.4　収集用ロールの作成

ロール名 `wazuh_collector` がまだ使われていないことを確認します。

**実行先：Proxmoxホスト（root@pve）**

⟦C6⟧

`(0 rows)` であれば、名前の衝突はありません。

まず、ログインできない状態で、管理者権限を一切持たないロールを作ります。

⟦C7⟧

すべての列が `f`（無効）になっていれば、安全な初期状態です。

## 1.5　パスワードの設定

パスワードをシェルの履歴やSQLに残さないため、PostgreSQLの対話型のパスワード設定機能を使います。

**実行先：Proxmoxホスト（root@pve）**

⟦C8⟧

`security_workbench=#` のプロンプトが表示されたら、次を入力します。

⟦C9⟧

新しいパスワードを2回入力します（入力中の文字は表示されません）。

- 十分に長いランダムなパスワード（32文字以上を推奨）にしてください。
- パスワードマネージャーなどに安全に保管し、チャットや資料には貼らないでください。

設定が終わったら、次を入力して終了します。

⟦C10⟧

この段階では、まだログインは許可しません。

## 1.6　接続とスキーマ利用の権限の付与

データベースへの接続と、`incident` スキーマの利用だけを許可します。オブジェクトの作成権限や管理者権限は付与しません。

**実行先：Proxmoxホスト（root@pve）**

⟦C11⟧

| 権限 | 期待値 |
|---|---|
| DBへの接続（CONNECT） | `t` |
| `incident` スキーマの利用（USAGE） | `t` |
| `incident` スキーマでの作成（CREATE） | `f` |

# 第2章　ネットワークとTLSの確認

Wazuh Manager（`192.168.0.220`）からPostgreSQL（`192.168.0.151`）へ、安全に接続できるようにします。ログインを許可する前に、待ち受けの設定・接続許可の設定・TLS証明書を確認します。この章の操作はすべて読み取り専用です。

## 2.1　待ち受けと接続許可の設定の確認

**実行先：Proxmoxホスト（root@pve）**

⟦C12⟧

`pg_hba.conf` の実際の内容と、解析された規則（ネットマスクを含む）を確認します。

⟦C13⟧

構築時は、PostgreSQLがIPv4・IPv6のすべてのインターフェースで5432番を待ち受けており、`pg_hba.conf` の11行目に次の広い接続許可がありました。

⟦C14⟧

これは、IPv4の任意の接続元に、すべてのデータベース・すべてのユーザーへの接続を許可する規則です（認証は必要です）。既存のアプリケーションの接続を壊さないよう、この規則はここでは変更しません。Wazuh用の接続許可は、別の専用規則として追加します（第3章）。

> **メモ：** この広い許可ルールは、既存の運用に合わせてそのまま使います。セキュリティ上の問題になる場合は、後で接続元を限定するよう修正します。

## 2.2　Wazuh ManagerからのTCP接続の確認

データベースへのログインはせず、TCPの接続だけを確認します。

**実行先：Proxmoxホスト（root@pve）**

⟦C15⟧

`err-data` に `Connection to 192.168.0.151 5432 port [tcp/postgresql] succeeded!` と表示されれば、通信経路は確保できています。

## 2.3　TLS証明書の確認

認証情報を含む通信を暗号化するため、PostgreSQLのTLS設定を確認します。秘密鍵の中身は表示しません。

**実行先：Proxmoxホスト（root@pve）**

⟦C16⟧

⟦C17⟧

| 項目 | 構築時の状態 |
|---|---|
| PostgreSQLのSSL | `on` |
| サーバー証明書 | `/etc/ssl/certs/ssl-cert-snakeoil.pem`（自己署名） |
| CN・SAN | `postgresql.neomedia.mydns.jp`（IPアドレスのSANはなし） |
| 有効期限 | 2036年8月11日 |
| CA証明書 | 未設定 |
| 秘密鍵 | `root:ssl-cert 640`（`postgres` は `ssl-cert` グループに所属） |

TLSによる暗号化は有効ですが、自己署名証明書のため、そのままではWazuh側でサーバーが本物かどうかを検証できません。

## 2.4　証明書と秘密鍵の整合性の確認

**実行先：Proxmoxホスト（root@pve）**

⟦C18⟧

| 検証 | 期待する結果 |
|---|---|
| 自己署名証明書の検証 | OK |
| DNS名との一致 | `postgresql.neomedia.mydns.jp` と一致 |
| 証明書と秘密鍵の公開鍵のハッシュ | 2つが一致 |

**決定事項：** 証明書はすぐには交換しません。この証明書をWazuh Manager側で「信頼できる証明書」として登録し、接続先の名前まで検証する `verify-full` で接続します。接続先の名前には証明書のDNS名を使い、IPアドレスは `192.168.0.151` に固定します。

# 第3章　Wazuh Manager側の接続準備

## 3.1　TLSハンドシェイクの確認

VM 220からPostgreSQLへのTLS接続を確認します。DBへのログインはしません。

**実行先：Proxmoxホスト（root@pve）**

⟦C19⟧

構築時は `TLSv1.3`・`TLS_AES_256_GCM_SHA384` で接続できました。`Verify return code: 18 (self-signed certificate)` は接続の失敗ではなく、VM 220がまだこの自己署名証明書を信頼していないという意味です。

## 3.2　受け取った証明書の指紋の照合

VM 220が受け取った証明書を一時ファイルに保存し、SHA-256の指紋を表示します。

**実行先：Proxmoxホスト（root@pve）**

⟦C20⟧

表示された指紋が、2.3でLXC 109の中で確認した指紋と完全に一致することを確認します。構築時の指紋は次のとおりでした。

⟦C21⟧

一致すれば、ネットワーク経由で受け取った証明書が、PostgreSQLサーバーの本物の証明書であると確認できます。

## 3.3　専用の信頼済み証明書として配置

OS全体のCAストアには登録せず、PostgreSQL接続専用のファイルとして配置します。

**実行先：Proxmoxホスト（root@pve）**

⟦C22⟧

`/etc/ssl/certs/postgresql-server-ca.pem: OK` と `Hostname postgresql.neomedia.mydns.jp does match certificate` が表示されれば成功です。

## 3.4　PostgreSQLクライアントの導入

VM 220にPostgreSQLのクライアント（`psql`）があるかを確認します。

**実行先：Proxmoxホスト（root@pve）**

⟦C23⟧

`psql` がなければ、Ubuntu標準のパッケージを確認してインストールします。PostgreSQLサーバー本体はインストールしません。

⟦C24⟧

⟦C25⟧

Ubuntu 24.04標準の `postgresql-client`（バージョン16）が入ります。PostgreSQL 17のサーバーへの接続にも使えます。

## 3.5　接続パラメーターの確認

**実行先：Proxmoxホスト（root@pve）**

⟦C26⟧

構築時は、証明書のDNS名 `postgresql.neomedia.mydns.jp` は名前解決できませんでした。DNSに登録する必要はありません。`PGHOSTADDR`（または `hostaddr`）で接続先のIPアドレスを指定し、`PGHOST`（`host`）で証明書のDNS名を指定すれば、IPで接続しながらホスト名の検証もできます。

この組み合わせで、パラメーターと証明書を確認します。パスワードは設定せず、ログインもしません。

⟦C27⟧

| パラメーター | 値 | 意味 |
|---|---|---|
| PGHOSTADDR | `192.168.0.151` | 実際の接続先IP |
| PGHOST | `postgresql.neomedia.mydns.jp` | 証明書で検証する名前 |
| PGSSLMODE | `verify-full` | 暗号化に加え、証明書とホスト名を検証する |
| PGSSLROOTCERT | `/etc/ssl/certs/postgresql-server-ca.pem` | 信頼する証明書 |

# 第4章　専用の接続許可ルールとログインの有効化

`pg_hba.conf` には全IPv4を対象にした広い規則が残っています。そのまま `wazuh_collector` をログイン可能にせず、専用の規則で接続元を限定してから有効にします。

## 4.1　現在の規則と適用範囲の確認

**実行先：Proxmoxホスト（root@pve）**

⟦C28⟧

⟦C29⟧

| 行 | 規則 | 適用範囲 |
|---:|---|---|
| 8 | `0.0.0.0/24`（md5） | `0.0.0.0`〜`0.0.0.255` |
| 11 | `0.0.0.0/0`（md5） | すべてのIPv4アドレス |

既存のアプリケーションを守るため、これらの規則はここでは変更しません。代わりに、`wazuh_collector` 専用の規則を既存の規則より前（ファイルの先頭）に追加します。`pg_hba.conf` は上から順に評価され、最初に一致した規則が使われます。

ファイルの権限と、関連する設定を確認します。

⟦C30⟧

| 項目 | 構築時の状態 |
|---|---|
| `pg_hba.conf` | `postgres:postgres 640` |
| SSL | `on` |
| パスワードの暗号化 | `scram-sha-256` |
| include指定 | なし |

## 4.2　pg_hba.confのバックアップ

**実行先：Proxmoxホスト（root@pve）**

⟦C31⟧

元のファイルとバックアップのSHA-256が一致することを確認します。

## 4.3　専用ルールの追加

`pg_hba.conf` の先頭に、`wazuh_collector` 専用の規則を追加します。

| 規則 | 内容 |
|---|---|
| `local ... reject` | Unixソケットからの接続を拒否 |
| `hostssl ... 192.168.0.220/32 scram-sha-256` | Wazuh ManagerからのTLS接続だけを、SCRAM認証で許可 |
| `host ... 0.0.0.0/0 reject` | それ以外のIPv4からの接続を拒否 |
| `host ... ::/0 reject` | IPv6からの接続を拒否 |

他のユーザー向けの規則は変更しません。この段階ではまだ再読み込みしません。

**実行先：Proxmoxホスト（root@pve）**

⟦C32⟧

ファイルの所有者と権限が `postgres:postgres 640` のまま維持されていることも確認します。

## 4.4　構文の検証と再読み込み

PostgreSQL自身のパーサーで、追加した規則を検証します。

**実行先：Proxmoxホスト（root@pve）**

⟦C33⟧

追加した4つの規則が認識され、構文エラーが `0` であれば、設定を再読み込みします。再起動ではないため、既存の接続は切断されません。

⟦C34⟧

`pg_reload_conf` が `t`、サービスが `active` であれば、接続元を限定する規則が有効になりました。

## 4.5　ログインの有効化

**実行先：Proxmoxホスト（root@pve）**

⟦C35⟧

`rolcanlogin` だけが `t` で、ほかはすべて `f` であれば、最小権限のまま有効になっています。

## 4.6　パスワードなしでの到達確認

パスワードを渡さずに接続し、TLSの検証と接続許可の規則を通過して、パスワード認証の段階まで進むかを確認します。

**実行先：Proxmoxホスト（root@pve）**

⟦C36⟧

次のように `no password supplied` と表示されれば、期待どおりです。

⟦C37⟧

証明書のエラーや `no pg_hba.conf entry` が出ていないので、TLSの検証と接続元の制限が正しく働いています。

## 4.7　実際のパスワードによるTLS接続

パスワードをコマンドの引数や環境変数に書かずに、実際にログインします。

> このコマンドは **VM 220（`root@security-core`）に直接ログインして** 実行します。ProxmoxのVMコンソールまたはSSHを使ってください。`psql` はVM 220にだけ入っているため、Proxmoxホストで実行すると `psql: command not found` になります。

**実行先：security-core VM 220（root）**

⟦C38⟧

`Password:` と表示されたら、1.5で設定した `wazuh_collector` のパスワードを入力します（入力内容は表示されません）。

| 項目 | 期待値 |
|---|---|
| current_user | `wazuh_collector` |
| current_database | `security_workbench` |
| ssl | `t` |
| version | `TLSv1.3` |

実行結果（例）：

⟦C39⟧

これで、VM 220からLXC 109へ、証明書と接続元を検証した暗号化接続が確立できました。

# 第5章　アラートの構造調査と保存テーブルの作成

## 5.1　アラートファイルの構造の確認

Wazuhのアラートファイル `alerts.json` が、どのような項目を持っているかを調べます。

**実行先：security-core VM 220（root）**

⟦C40⟧

アラートの `data` には、`pwd`（作業ディレクトリ）や `command`（実行されたコマンド）など、DBに保存すべきでない情報が含まれることがあります。そのため、**`data` や `full_log` を丸ごとDBに保存することはしません。**

## 5.2　保存する項目の安全確認

すべてのアラートについて、`data` の中の項目名、ルールのグループ、MITREの項目名がどれくらい現れるかを集計します。値そのものは表示しません。

**実行先：security-core VM 220（root）**

⟦C41⟧

構築時は1,271件のアラートに、認証失敗、ブルートフォース、PostgreSQL、SCA、Rootcheckなどのグループがあり、MITREの項目は `id`・`tactic`・`technique` でした。

この結果から、DBに保存する項目を次のように決めました。

| カラム | 用途 |
|---|---|
| `event_id` | Wazuhイベントの一意な識別子（主キー。重複登録を防ぐ） |
| `event_timestamp` | アラートの発生日時 |
| `ingested_at` | DBへの登録日時 |
| `rule_id`・`rule_level`・`rule_description` | 検知ルール、重要度、検知内容 |
| `agent_id`・`agent_name` | 検知元のAgent |
| `manager_name`・`decoder_name` | Wazuhの管理情報 |
| `rule_groups` | ルールのグループ |
| `srcip`・`srcport` | 送信元のIPとポート（ある場合のみ） |
| `mitre` | MITRE ATT&CKの情報 |

## 5.3　保存テーブルの作成

`wazuh_collector` には **INSERTだけ** を許可し、読み取り・変更・削除はできないようにします。

> **注意：** Proxmoxホストのシェルに、`PGHOST` や `PGSSLMODE` などの環境変数が残っていると、`pct exec` で実行する `psql` がそれを引き継ぎ、`root certificate file "/etc/ssl/certs/postgresql-server-ca.pem" does not exist` というエラーになります（証明書はVM 220にしかありません）。次のコマンドは `env -u` でこれらの環境変数を外して実行するため、どちらの状態でも動きます。SQLはトランザクションの中にあるため、エラーになった場合も途中まで作られることはありません。

**実行先：Proxmoxホスト（root@pve）**

⟦C42⟧

実行結果（例）：

⟦C43⟧

`wazuh_collector` はアラートを追加することだけができ、既存のイベントの読み取り・変更・削除はできません。

# 第6章　Collectorの実行環境の確認

Collectorは、Wazuh Managerの動作に影響を与えないよう、`alerts.json` を読み取るだけのプログラムとして作ります。

> この章のコマンドは **VM 220（`root@security-core`）にログインして** 実行します。`alerts.json` はVM 220の中にあるため、Proxmoxホストで実行すると `No such file or directory` になります。なお、VM 220にはシリアルポートを設定していないため、`qm terminal 220` ではログインできません。SSHか、Proxmox Web UIの「コンソール」を使ってください。

## 6.1　アラートファイルの権限の確認

**実行先：security-core VM 220（root）**

⟦C44⟧

| 項目 | 構築時の状態 |
|---|---|
| `alerts.json` | 所有者 `wazuh`、権限 `640` |
| `/var/ossec/logs` | `770` |
| `/var/ossec/logs/alerts` | `750` |
| logrotateの設定 | なし（Wazuh自身がローテーションする） |

## 6.2　アラートの出力設定の確認

**実行先：security-core VM 220（root）**

⟦C45⟧

| 設定 | 構築時の値 | 意味 |
|---|---|---|
| `jsonout_output` | `yes` | JSON形式のアラート出力が有効 |
| `alerts_log` | `yes` | テキスト形式のアラートログも出力 |
| `logall`・`logall_json` | `no` | すべてのイベントの保存は無効 |
| `log_alert_level` | `3` | レベル3以上をアラートとして記録 |

CollectorはWazuhの設定を変更せず、`alerts.json` だけを読み取ります。

## 6.3　ローテーション方式の確認

**実行先：security-core VM 220（root）**

⟦C46⟧

Wazuh Managerは独自のローテーション機能（`analysisd.min_rotate_interval=600`、`monitord.rotate_log=1`）でアラートファイルを切り替えます。そのため、Collectorはファイル名だけでなく、**inode（ファイルの実体の番号）と読み取り位置** を管理する方式にします。ローテーション後の読み直しと、DB側の主キーによる重複の排除を組み合わせます。

## 6.4　PostgreSQLドライバーの導入

**実行先：security-core VM 220（root）**

⟦C47⟧

構築時はPython 3.12.3で、ドライバーは未導入でした。OS標準のパッケージで管理できる **psycopg 3** を使います。

⟦C48⟧

⟦C49⟧

`psycopg: 3.1.17` のように表示されれば成功です。

## 6.5　ACLの利用可否の確認

Collectorは、Wazuhとは別の専用ユーザーで動かします。専用ユーザーを `wazuh` グループに加えると、ログディレクトリへの書き込みまでできてしまうため、**読み取りだけを許可するACL** を使えるかを確認します。この時点では、まだACLもユーザーも変更しません。

**実行先：security-core VM 220（root）**

⟦C50⟧

ファイルシステムは `ext4` で、ACLを使えます。構築時は `getfacl`・`setfacl` が未導入だったため、ツールだけを導入します。既存のファイルの権限は変更しません。

⟦C51⟧

⟦C52⟧

# 第7章　専用ユーザーと読み取り専用の権限

## 7.1　現在の権限の確認

**実行先：security-core VM 220（root）**

⟦C53⟧

既存のWazuhの所有者・グループ・権限は変更せず、専用ユーザーにACLで必要な権限だけを与えます。

## 7.2　専用サービスユーザーの作成

ログインシェルもホームディレクトリも持たない、システム用のユーザーを作ります。

**実行先：security-core VM 220（root）**

⟦C54⟧

⟦C55⟧

実行結果（例）：

⟦C56⟧

`wazuh` グループには入っていないことを確認します。

## 7.3　読み取り専用ACLの設定

**実行先：security-core VM 220（root）**

⟦C57⟧

| 対象 | 専用ユーザーに与える権限 |
|---|---|
| `/var/ossec/logs` | 通過のみ（`--x`） |
| `/var/ossec/logs/alerts` | 通過のみ（`--x`） |
| `alerts.json` | 読み取りのみ（`r--`） |
| `alerts` 以下に今後作られるファイル | 読み取り（デフォルトACL。実際の権限はファイル作成時の通常の権限との共通範囲） |

さらに、その上の `/var/ossec`（`root:wazuh 750`）にも通過権限が必要です。これがないと、下のファイルに読み取りACLがあっても到達できず、`Permission denied` になります。

⟦C58⟧

## 7.4　読み取り専用であることの確認

**実行先：security-core VM 220（root）**

⟦C59⟧

⟦C60⟧

3項目すべてが `PASS` になれば、専用ユーザーはアラートファイルを読めるが、変更はできない状態です。

経路上のすべての階層も確認しておきます。

⟦C61⟧

## 7.5　アラートファイルの構造の確認

Wazuhがアラートファイルを実際にどう管理しているかを確認します。

**実行先：security-core VM 220（root）**

⟦C62⟧

`<alerts>` には `log_alert_level`（3）と `email_alert_level`（12）だけがあり、`rotate_interval`・`max_output_size` は未設定（既定値は無効）でした。

> `internal_options.conf` の `monitord.rotate_log` や `monitord.size_rotate` は、Wazuh自身の内部ログ用の設定で、`alerts.json` のローテーションの設定ではありません。

⟦C63⟧

実行結果（例）：

⟦C64⟧

`alerts.json` は、日付ごとのファイル（`年/月/ossec-alerts-日.json`）と **同じinodeを共有するハードリンク** です。日付が変わると、新しい日のファイルが作られ、前日のファイルは圧縮（`.json.gz`）されます。Collectorは `alerts.json` のinodeが変わったことで、日付の切り替わりを検知します。

# 第8章　Collectorの作成

## 8.1　認証情報の保存先の作成

**実行先：security-core VM 220（root）**

⟦C65⟧

`wazuh-collector:wazuh-collector 700 /etc/wazuh-collector` と表示されれば、ほかのユーザーやサービスからは参照できない状態です。

接続先の設定を確認します（パスワードは表示しません）。

⟦C66⟧

## 8.2　パスワードファイル（.pgpass）の作成

パスワードを画面に表示せず、専用ユーザーだけが読める `.pgpass` に保存します。

**実行先：security-core VM 220（root）**

⟦C67⟧

1.5で設定したパスワードを2回入力します。パスワードにコロン（`:`）が含まれる場合は、安全のため作成を中止します。

⟦C68⟧

`wazuh-collector:wazuh-collector 600` であることを確認します。**ファイルの中身は表示しないでください。**

## 8.3　専用ユーザーでの接続テスト

`.pgpass` を使い、`verify-full` で接続します。パスワードの入力は求められません。

**実行先：security-core VM 220（root）**

⟦C69⟧

`192.168.0.151` の5432番にTLS 1.3で接続し、`current_user` が `wazuh_collector`、`current_database` が `security_workbench` と表示されれば成功です。

## 8.4　状態ファイルとプログラムの保存先の作成

アラートファイルのどこまで読んだか（inodeと読み取り位置）を保存する状態ディレクトリを作ります。

**実行先：security-core VM 220（root）**

⟦C70⟧

⟦C71⟧

プログラムはroot所有にして、実行ユーザーからは変更できないようにします。

⟦C72⟧

| ディレクトリ | 所有者・権限 | 用途 |
|---|---|---|
| `/etc/wazuh-collector` | `wazuh-collector` 700 | 認証情報（`.pgpass`） |
| `/var/lib/wazuh-collector` | `wazuh-collector` 700 | 状態ファイル（`state.json`） |
| `/usr/local/lib/wazuh-collector` | `root` 755 | プログラム本体 |

## 8.5　Collector本体の作成

Collectorの設計上の要点は次のとおりです。

- Wazuhの `alerts.json` だけを監視する。
- DBに保存するのは、許可した項目だけ（`full_log`、任意の `data`、コマンド、パスワードなどは保存しない）。
- 値を検証してから保存する（イベントID・ルールID・レベル・日時・IPアドレス・ポート番号）。
- DBの主キー（`event_id`）で重複を排除する（`ON CONFLICT DO NOTHING`）。
- DBへの登録が成功してから、読み取り位置を保存する。
- inodeの変化でファイルの切り替わりを検知し、新しいファイルを先頭から読む。
- 初めて起動したときは、過去のアラートを登録せず、ファイルの末尾から読み始める。

**実行先：security-core VM 220（root）**

⟦C73⟧

> このプログラムは、第4部で入力検証やローテーションへの対応などを強化します。ここに掲載したのは、第3部の時点（初版）の全文です。

## 8.6　作成したファイルの確認

長いコマンドを貼り付けると、端末の表示が崩れることがあります。ファイルが最後まで正しく作られたかを確認します。

**実行先：security-core VM 220（root）**

⟦C74⟧

⟦C75⟧

| 項目 | 期待値 |
|---|---|
| 所有者・権限 | `root:root 755` |
| サイズ・行数 | 9,487バイト、383行 |
| 末尾 | `if __name__ == "__main__":` と `run()` |
| シェルコマンドの混入 | `PASS: no obvious shell command contamination` |
| 構文 | `PASS` |

## 8.7　機密情報が保存されないことのテスト

`data` の中に `command`・`pwd`・`tty`・`dstuser` などがあっても、DBに登録するデータに入らないことを確認します。DBには接続しません。

**実行先：security-core VM 220（root）**

⟦C76⟧

5項目すべてに `PASS` が表示されれば、許可した項目だけが取り出され、機密情報が除外されていることを確認できます。

# 第9章　DBへの登録処理の確認と修正

## 9.1　テーブル権限の確認

Collectorが実際にDBへ登録できるかを確認する前に、専用ユーザーで接続したときの権限を確認します。

**実行先：security-core VM 220（root）**

⟦C77⟧

実行結果（例）：

⟦C78⟧

| 権限 | 結果 | 意味 |
|---|---|---|
| `incident` スキーマのUSAGE | `t` | 許可 |
| `alert_events` のINSERT | `t` | 許可 |
| `alert_events` のSELECT | `f` | 拒否（意図した最小権限） |

## 9.2　ON CONFLICTとSELECT権限の関係

8.5のプログラムのINSERT文は、末尾に `ON CONFLICT (event_id) DO NOTHING` を付けて重複を除外しています。しかしPostgreSQLでは、`ON CONFLICT` を使うと既存の行と照合するため、**テーブルのSELECT権限が必要** になります。`wazuh_collector` にはSELECT権限を与えていないので、このままでは `permission denied for table alert_events` で失敗します。

通常のINSERTと、`ON CONFLICT` 付きのINSERTを比べて確認します。どちらも最後に意図的に例外を発生させ、テストデータはコミットしません。

**実行先：security-core VM 220（root）**

通常のINSERT：

⟦C79⟧

⟦C80⟧

`ON CONFLICT` 付きのINSERT：

⟦C81⟧

⟦C82⟧

| SQL | 結果 |
|---|---|
| 通常のINSERT | 成功 |
| INSERT ＋ `ON CONFLICT DO NOTHING` | `InsufficientPrivilege` |

SELECT権限は与えずに、プログラム側の重複処理を変更します。

## 9.3　重複エラーで処理する方式の確認

`ON CONFLICT` を使わず、主キーの重複エラー（`UniqueViolation`、SQLSTATE `23505`）を捕まえて処理する方式が使えるかを確認します。全体を最後にロールバックします。

**実行先：security-core VM 220（root）**

⟦C83⟧

⟦C84⟧

重複は検出でき、その後も接続をそのまま使えることを確認できました。

## 9.4　修正前のバックアップ

修正する箇所を表示します（ファイルは変更しません）。

**実行先：security-core VM 220（root）**

⟦C85⟧

バックアップを作ります。同じ名前のバックアップがすでにある場合は中止します。

⟦C86⟧

2つのSHA256が一致することを確認します。

## 9.5　重複処理の修正

変更は次の2か所だけです。

1. `INSERT_SQL` から `ON CONFLICT (event_id) DO NOTHING` を削除する。
2. `process_line()` で `UniqueViolation` を捕まえ、重複したアラートはログに記録して読み飛ばす。

**実行先：security-core VM 220（root）**

⟦C87⟧

`PATCH: applied` と表示されれば適用されています。対象の文字列が1か所だけ見つからない場合は、何も変更せずに中止します。

## 9.6　修正内容の確認

**実行先：security-core VM 220（root）**

⟦C88⟧

構文エラーがないこと、`ON CONFLICT` が消えていること、差分が上の2か所だけであることを確認します。

## 9.7　本番コードでの登録テスト

修正したプログラムの `process_line()` を実際に呼び出し、同じアラートを2回処理します。最後にロールバックするので、テストデータは残りません。

**実行先：security-core VM 220（root）**

⟦C89⟧

⟦C90⟧

新しいアラートは登録され、重複したアラートは読み飛ばされ、接続はそのまま使えます。SELECT権限は不要です。

# 第10章　systemdサービス化

## 10.1　事前確認

**実行先：security-core VM 220（root）**

⟦C91⟧

既存のユニットがないこと、各ファイルの所有者と権限が8.4の表のとおりであることを確認します。

## 10.2　サービス定義の作成

専用ユーザーで動かし、書き込めるのは状態ディレクトリだけに制限します。メモリ・CPU・タスク数の上限も設定します。

**実行先：security-core VM 220（root）**

⟦C92⟧

`systemd-analyze verify` は次の警告を出します。

⟦C93⟧

`Documentation=` にはURLかマニュアルの参照を書く必要があります。この行は不要なので削除します。

⟦C94⟧

⟦C95⟧

警告が消え、`VERIFY EXIT CODE` が `0` になれば完了です。

## 10.3　手動での起動

まだ自動起動（`enable`）は設定せず、一度だけ起動して動作を確認します。

**実行先：security-core VM 220（root）**

⟦C96⟧

`active (running)` で、実行ユーザーが `wazuh-collector` であることを確認します。

⟦C97⟧

状態ファイルの中身と認証情報は表示しません。

実行結果（例）：

⟦C98⟧

初めての起動なので、過去のアラートは登録せず、`alerts.json` の現在の末尾から読み始めます。状態ファイルは `wazuh-collector` 所有、権限 `600` で作られます。

# 第11章　実際のアラートでの動作確認

## 11.1　待機状態の確認

**実行先：security-core VM 220（root）**

⟦C99⟧

再起動やエラーのログがないことを確認します。

## 11.2　テストに使うルールの確認

第2部で作ったPostgreSQLのWARNING検知ルール（100104）を使って、テスト用のアラートを1件発生させます。

**実行先：security-core VM 220（root）**

⟦C100⟧

ルール100104は、親ルール100100に一致したイベントのうち、`event` が `POSTGRESQL_WARNING` のものを検知します（レベル4）。親ルールの条件とデコーダーを確認します。

⟦C101⟧

親ルール100100は次のとおりです。

⟦C102⟧

専用のデコーダーはなく、Wazuh標準のJSONデコーダーを使います。そのため、テストにはJSON形式のイベントが必要です（`POSTGRESQL_WARNING` という文字列だけでは、どのデコーダーにも一致しません）。

## 11.3　wazuh-logtestでのルール判定

**実行先：security-core VM 220（root）**

⟦C103⟧

起動したら、次のJSONを1行で入力します。

⟦C104⟧

| 項目 | 期待する結果 |
|---|---|
| Decoder | `json` |
| Rule ID | `100104` |
| Level | `4` |
| Description | `PostgreSQL WARNING event detected` |
| 判定 | `**Alert to be generated.` |

`wazuh-logtest` の中だけのテストなので、`alerts.json` やDBには登録されません。終了したら、Collectorが動いていることを確認します。

⟦C105⟧

## 11.4　実際のアラートの発生

既存のログ入力経路を確認します。

**実行先：security-core VM 220（root）**

⟦C106⟧

第2部で作った経路（LXC 109の `/var/log/postgresql-wazuh/events.log` → Wazuh Agent `postgresql`（ID 004））に、テスト用の合成イベントを1件追加します。`pct` はProxmoxホストのコマンドなので、**security-coreではなくProxmoxホストで実行します**。

**実行先：Proxmoxホスト（root@pve）**

⟦C107⟧

> このイベントはテスト用の合成データです。実際のPostgreSQLの障害を意味するものではありません。

Wazuhがアラートを生成したかを確認します。

**実行先：security-core VM 220（root）**

⟦C108⟧

`agent.name` が `postgresql`、`rule.id` が `100104` のアラートが表示されます。アラートの先頭にある `"id"`（例：`1795000021.2810167`）を控えておきます。

## 11.5　DBへの登録の確認

Collectorにはテーブルを読む権限（SELECT）がないため、登録の確認はDB管理者（`postgres`）で行います。

**実行先：Proxmoxホスト（root@pve）**

⟦C109⟧

`event_id` の値は、11.4で控えたアラートのIDに置き換えてください。1行が表示されれば、`alerts.json` → Collector → PostgreSQL の流れが動いています。

| 項目 | 登録された値（例） |
|---|---|
| event_id | `1795000021.2810167` |
| event_timestamp | `2026-11-18 11:07:01.074+00` |
| rule_id | `100104` |
| rule_level | `4` |
| rule_description | `PostgreSQL WARNING event detected` |
| agent_id / agent_name | `004` / `postgresql` |
| manager_name | `security-core` |
| rule_groups | `{local,postgresql,postgresql,warning}` |

## 11.6　保存項目と権限の最終確認

テーブルの列を確認します。

**実行先：Proxmoxホスト（root@pve）**

⟦C110⟧

14列で、`full_log`・`data`・`command`・`password` などの列がないことを確認します。

Collectorのロールの権限を確認します。

⟦C111⟧

⟦C112⟧

Collectorはイベントを追加することだけができ、既存のデータを読む・変更する・削除することはできません。

# 第12章　自動起動と収集データの監査

## 12.1　自動起動の登録

**実行先：security-core VM 220（root）**

⟦C113⟧

⟦C114⟧

`Active: active (running)`、`enabled`、`NRestarts=0` を確認します。

## 12.2　収集件数と欠損の監査

しばらく稼働させてから、DBに蓄積されたデータを監査します。以降のSQLはすべて読み取りだけです。

**実行先：Proxmoxホスト（root@pve）**

⟦C115⟧

Agentごとの収集状況：

⟦C116⟧

ルールIDとレベルごとの分布：

⟦C117⟧

| Rule ID | レベル | 検知内容（構築時の例） |
|---|---:|---|
| 5501 | 3 | PAM Login session opened |
| 5502 | 3 | PAM Login session closed |
| 100104 | 4 | PostgreSQL WARNING event detected |
| 87203 | 3 | Proxmox VE authentication succeeded. |

デコーダーごとの項目の品質：

⟦C118⟧

## 12.3　整合性と異常値の監査

**実行先：Proxmoxホスト（root@pve）**

⟦C119⟧

> 貼り付けるときは、行頭に `root@pve:~#` などのプロンプトの文字を含めないでください。

| 監査項目 | 期待値 |
|---|---|
| `total_events` と `unique_event_ids` | 同じ値（重複なし） |
| `future_timestamps` | 0 |
| `null_timestamps` | 0 |
| `invalid_rule_values` | 0 |
| `port_without_ip` | 0 |
| `ingestion_time_anomalies` | 0 |
| `missing_required_fields` | 0 |

## 12.4　Wazuh側との件数の照合

DBに送信元IPが少ない理由が、Collectorの取りこぼしなのか、元のアラートにIPがないのかを確かめます。

**実行先：security-core VM 220（root）**

`alerts.json` 全体のネットワーク項目の有無：

⟦C120⟧

Collectorが起動した時刻（10.3のジャーナルの時刻）以降の、Agentごとの件数：

⟦C121⟧

`start` の値は、自分の環境のCollectorの起動時刻（UTC）に置き換えます。

DB側のAgentごとの件数：

**実行先：Proxmoxホスト（root@pve）**

⟦C122⟧

構築時の照合結果：

| Agent | Wazuh側 | DB側 | 差分 |
|---|---:|---:|---:|
| pve（001） | 2 | 2 | 0 |
| postgresql（004） | 23 | 23 | 0 |
| **合計** | **25** | **25** | **0** |

Collectorの起動後のアラートは、すべてDBに登録されていました。DBに送信元IPがないのは、この期間のアラート自体にIPが含まれていなかったためで、取りこぼしではありません。

## 12.5　Collectorのログの確認

**実行先：security-core VM 220（root）**

⟦C123⟧

`wc -l` は空行も数えるため、`1` と表示されることがあります。空行を除いて、警告・エラーの実際の行数を数えます。

⟦C124⟧

`Non-empty warning/error lines: 0` であれば、接続エラー・JSON解析エラー・項目検証エラーは起きていません。

## 12.6　状態ファイルとプログラムの確認

状態ファイルの中身（値）は表示せず、形式だけを確認します。

**実行先：security-core VM 220（root）**

⟦C125⟧

⟦C126⟧

最後に、プログラム本体を確認します。

⟦C127⟧

| 項目 | 結果 |
|---|---|
| 所有者・権限 | `root` / `755` |
| サイズ | 9,626バイト（9.5の修正後） |
| 関数 | 9個 |
| 構文 | `Python syntax: PASS` |

# 第3部のまとめ

第3部で、Wazuhのアラートを安全にPostgreSQLへ保存する仕組みができあがりました。

| 構成要素 | 内容 |
|---|---|
| 保存先 | `security_workbench` DBの `incident.alert_events`（14列、機密情報の列なし） |
| DBロール | `wazuh_collector`（INSERTのみ。SELECT・UPDATE・DELETEは不可） |
| 接続 | `192.168.0.220/32` からの `hostssl` ＋ `scram-sha-256`、`verify-full` によるTLS 1.3 |
| 実行ユーザー | `wazuh-collector`（ログイン不可、アラートは読み取り専用のACL） |
| 認証情報 | `/etc/wazuh-collector/.pgpass`（600） |
| 状態ファイル | `/var/lib/wazuh-collector/state.json`（inodeと読み取り位置） |
| プログラム | `/usr/local/lib/wazuh-collector/collector.py`（root所有 755） |
| サービス | `wazuh-collector.service`（権限制限・資源制限付き、自動起動） |

> **メモ：** 第2章で確認した `pg_hba.conf` の11行目（`0.0.0.0/0 md5`）は、広い許可ルールのまま運用します。セキュリティ上の問題になる場合は、後で接続元を限定するよう修正します。

第4部では、STEP 100以降の監査で見つかった改善点（入力検証、ローテーションへの対応、DB接続断からの復旧など）をもとに、Collectorを強化していきます。

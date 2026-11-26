---
title: "AI自律型サイバー防御システム 構築マニュアル 中編"
subtitle: "第24部　監査ログが保存されない原因を突き止める"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」中編の第24部です。前編の第23部で、Wazuh Indexer（OpenSearch）のセキュリティの監査ログは「有効」なのに、保存先が見つからないことがわかりました。ここでは、設定は変えずに**読み取りだけで**、その理由を突き止めます。

調べ方は次の3段階です。

1. 管理者の API で、監査の設定・インデックス・Data Stream・クラスターの設定を確かめる
2. Indexer に付いている JDK の `javap`（Java のクラスを逆アセンブルする道具）で、Security プラグインのコードを読み、監査ログの出力先（Sink）がどう選ばれるかを調べる
3. 動いている Indexer の JVM に `jcmd` で接続し、読み込まれているクラスを確かめる（読み取りだけ）

わかった結論は次のとおりです。

- 監査ログの出力先は、設定 `plugins.security.audit.type` で選ばれる。**この設定には既定の値がない**
- 設定がないと、主の出力先（default Sink）が作られず、監査のメッセージを配る仕組み（ルーター）が無効になる
- ルーターが無効だと、監査の API で `enabled: true` になっていても、**監査のイベントはどこにも保存されない**
- この環境では、設定ファイル・クラスターの設定・起動の引数・環境変数のどこにも、出力先の指定がなかった

## 中編について

本書から「中編」です。前編（第1部〜第23部）で、Wazuh を中心とした防御基盤と、AI Defense Manager・中継API（Relay）による AI の分析までを作り、前編の最後（第23部）で、Wazuh Indexer の監査ログがどこにも保存されていないらしいことがわかりました。中編では、この監査ログを動くようにし、その途中で見つかった Collector の停止を直します。

| 部 | 内容 |
|---|---|
| 第24部 | 監査ログが保存されない原因をコードで突き止める |
| 第25部 | 監査ログの保存先を設定する |
| 第26部 | 監査ログにリクエストの本文を記録しない |
| 第27部 | 監査ログが保存されていることを確かめる |
| 第28部 | Collector の点検と、停止の原因 |
| 第29部 | 読み残しを出さずに Collector を動かし直す |
| 第30部 | Collector が同じ理由で止まらないようにする |

前編の手順と同じ環境（Proxmox・VM 220 security-core・LXC 109 PostgreSQL など）を前提にしています。一般的な PC で構築する場合の読み替えは、前編 第1部の「一般的なPCで構築する場合」を見てください。

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

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は **security-core VM 220（root）** です。
- 管理者の証明書（`admin.pem`・`admin-key.pem`）は Indexer に読み取りの問い合わせをするためだけに使い、中身は表示しません。
- `javap` の出力はとても長いので、本書では結果の要点だけを書きます。

# 第1章　APIで確かめる

## 1.1　インデックスの一覧

⟦C0⟧

`auditlog6` や `auditlog6-YYYY.MM.dd` のような、監査ログのためのインデックスはありませんでした。

## 1.2　監査の設定

⟦C1⟧

`HTTP_STATUS: 200` でしたが、設定は `config` の内側にあるため、このプログラムでは値が表示されませんでした。`config` の中を見ます。

⟦C2⟧

監査は有効で、`log_request_body`（リクエストの本文の記録）が `true` でした。

## 1.3　すべてのインデックス

⟦C3⟧

全25個のインデックスの中に、監査ログのものと判断できるインデックスはありませんでした。

⟦C4⟧

Indexer のログにも、監査の初期化やエラーの記録はありませんでした。

## 1.4　監査の設定のすべての項目

⟦C5⟧

| 項目 | 値 |
|---|---|
| 監査の全体 | 有効 |
| REST・Transport の監査 | 有効 |
| 記録しないカテゴリー | `AUTHENTICATED`・`GRANTED_PRIVILEGES` |
| `compliance.read_metadata_only`・`write_metadata_only` | `true` |

項目の中に、出力先（Sink）を決めるものはありませんでした。

# 第2章　Securityプラグインのコードを読む

## 2.1　プラグインのファイル

⟦C6⟧

プラグインは JAR（ZIP 形式）なので、`grep` では中を探せません。

⟦C7⟧

Security プラグインは `opensearch-security-2.19.6.0.jar` でした。`unzip` は入っていないので、パッケージは足さずに、Python の標準のライブラリで JAR の中の一覧を見ます。

⟦C8⟧

監査ログの出力先として、次の実装がありました。

| クラス | 出力先 |
|---|---|
| `InternalOpenSearchSink` | Indexer の中のインデックス |
| `InternalOpenSearchDataStreamSink` | Indexer の中の Data Stream |
| `ExternalOpenSearchSink` | 外部の OpenSearch |
| `Log4JSink` | ログファイル |
| `KafkaSink`・`WebhookSink` | Kafka・Webhook |
| `DebugSink`・`NoopSink` | デバッグ用・何もしない |

⟦C9⟧

標準の監査設定（`static_audit.yml`）の中身は `_readonly: []` だけで、出力先はわかりませんでした。

## 2.2　設定ファイルに出力先の指定があるか

⟦C10⟧

見つかったのは設定例のファイル（`opensearch.yml.example`）だけでした。

## 2.3　javap

OS に `javap` は入っていませんが、Indexer に付いている JDK にあります。

⟦C11⟧

## 2.4　出力先を選ぶ処理（SinkProvider）

⟦C12⟧

- `plugins.security.audit.type` が出力先を選ぶ
- `internal_opensearch` なら `InternalOpenSearchSink`、`internal_opensearch_data_stream` なら Data Stream に出力する

⟦C13⟧

出力先に関するログは0件でした。実際に読み込まれる設定ファイルを確かめます（値は表示しません）。

⟦C14⟧

設定ファイルは `/etc/wazuh-indexer/opensearch.yml` で、`plugins.security.audit.*` の指定はありませんでした。

## 2.5　設定の既定の値

設定の登録の部分を見ます。

⟦C15⟧

⟦C16⟧

`plugins.security.audit.type` は `Setting.simpleString()` で登録されていて、**既定の値が渡されていません**。設定ファイルに書かなければ、`internal_opensearch` などが自動で選ばれることはありません。

⟦C17⟧

- 出力先の種類が指定されていないと、`createSink()` は `null` を返す
- `DebugSink` は、主の出力先の代わりではなく、保存に失敗したときの予備（fallback）として作られる
- 主の出力先が作れなければ、エラーを記録して初期化を終える

# 第3章　ほかの経路で設定されていないか

## 3.1　Data Stream

⟦C18⟧

`/_data_stream` は `HTTP 200` で、Data Stream は0件でした（`_cat/data_streams` は `400` でしたが、前者で空とわかります）。

## 3.2　起動の引数と環境変数

⟦C19⟧

環境変数は、名前だけを表示します（値は隠します）。

⟦C20⟧

どちらにも、監査の出力先の指定はありませんでした。

## 3.3　クラスターの設定

永続の設定・一時の設定・既定の値のすべてから、`plugins.security.audit` を含むものを探します。

⟦C21⟧

どれにも指定はありませんでした。

## 3.4　出力先が null のとき

⟦C22⟧

`createSink()` は、はじめに出力先を `null` にし、種類が `null` ならそのまま戻ります。もう1つの指定の方法（`plugins.security.audit.endpoints`）も確かめます。

⟦C23⟧

0件でした。

⟦C24⟧

`SinkProvider` の初期化は次のとおりです。

1. 予備（fallback）が指定されていなければ `DebugSink` を作る
2. 主の出力先（default）は `plugins.security.audit.type` から作る
3. 主の出力先が作れなければ、エラーを記録して初期化を終える

⟦C25⟧

監査に関するログは0件でした。

# 第4章　イベントが配られる経路

## 4.1　監査のクラス

OS に `jar` は入っていないので、Indexer の JDK の `jar` を使います。

⟦C26⟧

監査のイベントを受け取るのは `AuditLogImpl`、出力先に配るのは `AuditMessageRouter` です。

⟦C27⟧

⟦C28⟧

バイトコードを読み解くと、保存の処理は次の形です（Java で書き直したもの）。

⟦C29⟧

## 4.2　ルーター

⟦C30⟧

- 主の出力先が `null` なら、ルーターは無効（`isEnabled()` が false）
- 無効のときにイベントが来ると、`#route(AuditMessage) called but message router is disabled` というエラーを出して終わる

⟦C31⟧

`setConfig()` は次の形でした。

⟦C32⟧

つまり、監査の API で `enabled: true` でも、主の出力先がなければ `messageRouterEnabled` が false になり、監査は実際には働きません。

## 4.3　起動のときのメッセージ

⟦C33⟧

⟦C34⟧

journal にもログファイルにも、該当するメッセージはありませんでした。

# 第5章　動いているJVMを見る

## 5.1　起動の時刻

⟦C35⟧

構築時の Indexer は PID 1238 で、2026年11月20日 06:56:11 に起動していました（調べた期間に起動が含まれます）。

## 5.2　jcmd

`jcmd` は動いている JVM に接続して情報を取る道具です。ここでは読み取りのコマンドだけを使います。PID は自分の環境のものに置き換えてください。

⟦C36⟧

⟦C37⟧

構築時は OpenJDK 21.0.11 でした。読み込まれている監査のクラスを確かめます。

⟦C38⟧

`AuditLogImpl`・`AuditMessageRouter`・`SinkProvider`・`DebugSink`・`InternalOpenSearchSink`・`ExternalOpenSearchSink` などは読み込まれていました。ただし、クラスが読み込まれていることと、出力先が実際に選ばれて動いていることは別です。

# おわりに

第24部で突き止めたことは次のとおりです。

| 項目 | 結果 |
|---|---|
| 監査の API の設定 | 有効（`log_request_body: true`） |
| `plugins.security.audit.type` | どこにも指定がない（既定の値もない） |
| 主の出力先（default Sink） | 作られない |
| ルーター | 無効になる |
| 監査ログ | **保存されていない**と考えられる |

次の部では、`plugins.security.audit.type` を設定して監査ログを Indexer の中に保存するようにし、リクエストの本文を記録しないようにします。

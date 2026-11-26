---
title: "AI自律型サイバー防御システム 構築マニュアル 前編"
subtitle: "第23部　Indexerの権限と監査ログの調査"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」前編の第23部です。第22部で、動いている Indexer には `ai-defense-reader` と `ai_defense_alerts_read` があるのに、ディスクの上の YAML には定義がないことがわかりました。ここでは、設定は変えずに**読み取りだけで**次のことを調べます。

1. 設定の変更の記録（OpenSearch Security の監査ログ）がどう設定され、どこに残るか
2. 管理者の証明書を使って、ロールとユーザーの実際の定義を確かめる
3. Indexer のログに残っている `ai-defense-reader` に関する記録

監査ログの保存先は、この部の時点では突き止められていません。調べた手順と、わかったことまでを記します。

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は **security-core VM 220（root）** です。
- ログの本文、パスワード、秘密鍵の中身は表示しません。

# 第1章　監査ログの設定

## 1.1　監査ログのファイル

⟦C0⟧

構築時は、監査ログらしいファイルは見つかりませんでした。

## 1.2　audit.yml

⟦C1⟧

⟦C2⟧

| 設定 | 値 |
|---|---|
| REST API の監査 | 有効 |
| Transport API の監査 | 有効 |
| 内部のセキュリティ設定の変更の記録（`internal_config`） | 有効 |
| 外部の設定ファイルの変更の記録（`external_config`） | 無効 |
| リクエストの本文の記録（`log_request_body`） | 有効 |
| 認証の成功・権限の付与のイベント | 記録しない |

`log_request_body: true` は、REST API のリクエストの本文も記録する設定です。記録の扱いには注意が必要です（不足情報メモ 23-A）。

⟦C3⟧

`log4j2.properties` には、監査ログ専用のファイルの出力先は見当たりません。

⟦C4⟧

YAML として読み、出力の方式に関係する項目を表示します。

⟦C5⟧

監査は有効ですが、出力の方式は `audit.yml` には書かれていません。

## 1.3　Indexerの稼働のログ

秘密の情報らしい文字列は伏せて表示します。

⟦C6⟧

構築時は、監査やロールの変更に関する記録は見つかりませんでした。

# 第2章　管理者の証明書でロールとユーザーを確かめる

## 2.1　ai-defense-readerでは一覧を見られないこと

⟦C7⟧

`HTTP_STATUS: 403` でした。アラートを読むだけのユーザーに、インデックスの一覧を見る権限は要りません。権限は足さず、管理者の側から確かめます。

## 2.2　管理者の証明書

ファイルの名前と権限だけを表示します。

⟦C8⟧

⟦C9⟧

`admin.pem` と `admin-key.pem` は `wazuh-indexer` の持ち物で、権限は `400` でした。以下のプログラムは、この証明書で Indexer に読み取りだけの問い合わせをします。

## 2.3　ai_defense_alerts_readの定義

⟦C10⟧

| 項目 | 値 |
|---|---|
| `cluster_permissions` | 空 |
| `index_patterns` | `wazuh-alerts-4.x-*` だけ |
| `allowed_actions` | `read` だけ |
| `tenant_permissions` | 空 |
| `reserved`・`static` | `false` |

Wazuh のアラート以外は対象にせず、書き込み・削除・クラスターの管理の権限はありません。

## 2.4　own_indexの定義

`ai-defense-reader` には、標準のロール `own_index` も付いています。

⟦C11⟧

`own_index` は、ユーザーの名前と同じ名前のインデックス（`${user_name}`）に `indices_all` を許し、`cluster_composite_ops` も許す標準のロールです（`reserved: true`）。そこで、`ai-defense-reader` という名前のインデックスがあるかを確かめます。

⟦C12⟧

`INDEX_EXISTS: no`（`404`）でした。今は `own_index` で触れられるインデックスはありません。ただし、将来この名前のインデックスができれば、`ai-defense-reader` がすべての操作をできるようになります（不足情報メモ 23-B）。

## 2.5　ユーザーの定義

パスワードのハッシュは表示しません。

⟦C13⟧

構築時は `reserved: false`、`backend_roles` と `attributes` は空、`description` は `Read-only access to Wazuh alert indices for AI Defense Manager` でした。

# 第3章　監査ログの保存先を探す

## 3.1　インデックス

⟦C14⟧

出てきたのは `.opendistro_security`（セキュリティの設定を入れる内部のインデックス）と、`wazuh-states-*`（Wazuh の状態や資産の情報）だけでした。名前に `audit` を含むインデックスはありません。

## 3.2　動いている監査の設定

⟦C15⟧

動いている監査の設定は、ディスクの上の `audit.yml` と一致していました（監査は有効、内部の設定の変更の記録も有効、リクエストの本文の記録も有効、機密のヘッダーは記録から除く）。

## 3.3　ログのファイル

⟦C16⟧

⟦C17⟧

通常のログ（`wazuh-cluster.log`）と JSON 形式のログ（`wazuh-cluster_server.json`）があり、どちらも `640 wazuh-indexer:wazuh-indexer` でした。監査専用のファイルはありません。

JSON のログで、関係する語を含む行の数だけを数えます（本文は表示しません）。

⟦C18⟧

| 語 | 行の数 |
|---|---:|
| `audit` | 0 |
| `compliance` | 0 |
| `ai-defense-reader` | 3 |
| `ai_defense_alerts_read` | 3 |

## 3.4　その3行は何か

時刻・レベルなどのメタデータだけを取り出します。

⟦C19⟧

⟦C20⟧

⟦C21⟧

3行とも、OpenSearch Security の権限の判定に関係するログでした。

| コンポーネント | レベル | 件数 |
|---|---|---:|
| `RestApiPrivilegesEvaluator` | INFO | 1 |
| `PrivilegesEvaluatorImpl` | INFO | 1 |
| `AbstractApiAction` | ERROR | 1 |

## 3.5　ERRORの行を分類する

本文は表示せず、例外のクラスの名前、権限の拒否・認証の失敗などを示す語、HTTP のステータスがあるかだけを調べます。

⟦C22⟧

⟦C23⟧

⟦C24⟧

構築時は、どの方法でも ERROR の原因は特定できませんでした（例外のクラスの名前・権限の拒否・認証の失敗・HTTP のステータスのどれも見つからない）。第22部 3.3 で `ai-defense-reader` がロールの定義を読もうとして `403` になった記録の可能性がありますが、確かめられていません（不足情報メモ 23-C）。

## 3.6　監査の出力の方式

⟦C25⟧

`opensearch.yml` には、監査の出力の方式（`plugins.security.audit.type`）の設定がありません。

⟦C26⟧

⟦C27⟧

設定例のファイルには、Indexer の中に保存する `plugins.security.audit.type: internal_opensearch` が書かれています。ただし、これは例であり、実際の設定とは限りません。

動いているノードの設定を確かめます。

⟦C28⟧

`HTTP_STATUS: 200` で、中身は `{}`（明示的な設定はない）でした。

Indexer のプロセスの起動の引数に、監査に関係するものがあるかを確かめます（引数のすべては表示しません）。

⟦C29⟧

プロセスは見つかりましたが、監査に関係する引数はありませんでした。

## 3.7　プラグイン

⟦C30⟧

`wazuh-indexer` ユーザーで実行すると `/etc/default/wazuh-indexer` を読めずにエラーになるため、root で実行します。`opensearch-security`（監査の機能を持つプラグイン）が入っていることを確かめました。

# おわりに

第23部で調べた結果は次のとおりです。

| 項目 | 結果 |
|---|---|
| `ai_defense_alerts_read` | `wazuh-alerts-4.x-*` の `read` だけ（適切） |
| `own_index` | 同じ名前のインデックスはないので、今は影響なし |
| `ai-defense-reader` の定義 | 予約なし・バックエンドのロールなし |
| 監査の設定 | 有効（内部の設定の変更・リクエストの本文も記録） |
| 監査の出力の方式・保存先 | 明示の設定なし。保存先は**未確定** |
| JSON のログの ERROR 1件 | 原因は**未特定** |

監査ログの保存先は、中編の第24部で突き止め、第25部〜第27部で保存できるようにします。ERROR の原因は未特定のままです（不足情報メモ 23-C）。

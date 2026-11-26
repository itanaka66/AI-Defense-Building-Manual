---
title: "AI自律型サイバー防御システム 構築マニュアル 中編"
subtitle: "第25部　監査ログの保存先を設定する"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」中編の第25部です。第24部で、監査ログの出力先（`plugins.security.audit.type`）が設定されていないため、監査ログが保存されていないとわかりました。ここでは次のことを行います。

1. 出力先の候補（`internal_opensearch`）が、どこに・何を保存するかをコードで確かめる
2. 保存に失敗したときに、監査のメッセージがどこへ流れるかを確かめる
3. 記録される項目（リクエストの本文・ヘッダー・カテゴリー）を確かめる
4. 設定ファイルに2行を足し、Indexer を再起動する

守る条件は次のとおりです。

- Wazuh のアラートのインデックスと、監査ログを分ける
- `ai-defense-reader` に監査ログを読む権限を足さない
- Wazuh のアラートの収集と Relay を止めない（再起動のあいだを除く）
- リクエストの本文は記録しない（秘密の情報がまじるおそれがあるため）
- 変える前にバックアップを取る

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は **security-core VM 220（root）** です。
- `javap` の出力は長いので、結果の要点だけを書きます。
- 構築の記録のうち、会話 (109) と (112) はいただいていません。その間の判断（設定の方針の承認など）は、前後の会話から読み取れる範囲で書いています。

# 第1章　設定ファイルの確認

使う予定の設定は次の1行です（このあと 3.4 で確定します）。

⟦C0⟧

⟦C1⟧

構築時は `wazuh-indexer:wazuh-indexer` の `660`、2152 バイトでした。この権限は変えません。

⟦C2⟧

監査の出力先の指定はなく、Indexer は `127.0.0.1` だけで待ち受けています。TLS・認証・ネットワークの設定には手を加えません。

# 第2章　internal_opensearchの動き

## 2.1　保存先のインデックス

⟦C3⟧

Security プラグイン 2.19.6.0 の `internal_opensearch` は、インデックスの名前が指定されていなければ、日付ごとの **`security-auditlog-YYYY.MM.dd`** に保存します（`auditlog6` ではありません）。

⟦C4⟧

- 監査のイベントは `Client.prepareIndex()` で Indexer の中に書き込まれる
- 監査のメッセージ（`AuditMessage.getAsMap()`）の内容がそのまま保存される
- 書き込みに失敗すると、`Unable to index audit log` がエラーのログに出る

## 2.2　保存に失敗したとき

⟦C5⟧

`AuditLogSink.store()` は次の順に処理します。

1. 主の出力先に保存する
2. 失敗したら、予備（fallback）の出力先に保存する
3. それも失敗したら、`System.err`（標準エラー出力）に監査のメッセージの全文を出す

⟦C6⟧

予備の `DebugSink` は、監査のメッセージの全文を Log4j に `INFO` で出します。

⟦C7⟧

| 項目 | 今の設定 |
|---|---|
| rootLogger | `INFO` |
| コンソールへの出力 | 有効 |
| ファイルへの出力 | 有効（`/var/log/wazuh-indexer/`、128MB ごと、合計 2GB まで） |

つまり、主の出力先への保存に失敗すると、監査のメッセージの全文が通常のログに出るおそれがあります。

## 2.3　予備の出力先の選び方

⟦C8⟧

| 予備の指定 | 動き |
|---|---|
| なし | `DebugSink` を自動で作る |
| `debug` | Log4j に全文を出す |
| `noop` | 監査のメッセージを捨てる |

⟦C9⟧

`NoopSink` は何も出力せず「成功」として返します。ログへの漏れは防げますが、監査の記録が欠けたことが隠れてしまうため、ここでは採用しません（予備は既定のままにします）。

# 第3章　何が記録されるか

## 3.1　リクエストの本文とヘッダー

⟦C10⟧

⟦C11⟧

- `log_request_body` が有効だと、REST のリクエストの本文を JSON にして `audit_request_body` に入れる
- 本文を `__SENSITIVE__` に置き換えるのは、パスワードを扱う一部の Security API だけ。ほかの本文（検索の条件・登録や更新のデータなど）はそのまま記録される
- `exclude_sensitive_headers` が有効だと、`Authorization` ヘッダーは記録しない

## 3.2　フィルターの既定の値

⟦C12⟧

⟦C13⟧

- `log_request_body` の既定の値は **true**
- `exclude_sensitive_headers` の既定の値は true
- `ignore_headers`・`ignore_url_params`・`ignore_requests`・`ignore_users` は、ワイルドカードで指定して記録から外せる

## 3.3　監査のカテゴリー

⟦C14⟧

⟦C15⟧

⟦C16⟧

`AuditLogImpl` は、有効かどうかを確かめたうえで、イベントを作る処理を親のクラス `AbstractAuditLog` に任せています。

⟦C17⟧

⟦C18⟧

⟦C19⟧

カテゴリーは13種類です。このシステムで特に役に立つのは次のものです。

| カテゴリー | 意味 |
|---|---|
| `FAILED_LOGIN` | 認証の失敗 |
| `MISSING_PRIVILEGES` | 権限が足りずに断られた操作 |
| `BAD_HEADERS` | 正しくないヘッダー |
| `OPENDISTRO_SECURITY_INDEX_ATTEMPT` | セキュリティの内部のインデックスへの操作の試み |
| `SSL_EXCEPTION` | TLS の例外 |
| `INDEX_EVENT` | インデックスの操作 |
| `COMPLIANCE_*` | 文書の読み書き・内部の設定の読み書き |

認証の成功（`AUTHENTICATED`）と権限の許可（`GRANTED_PRIVILEGES`）は、今の設定で記録から外れています（前編 第23部）。

## 3.4　設定のキーの名前

まず、ログファイルにルーターの初期化のメッセージがないことを、圧縮されたログも含めて確かめます。

⟦C20⟧

⟦C21⟧

⟦C22⟧

⟦C23⟧

設定はファイルの末尾に足します。リクエストの本文を記録しない設定のキーを、コードで確かめます。

⟦C24⟧

⟦C25⟧

古い形式のキーは `opendistro_security.audit.log_request_body` でした。

⟦C26⟧

`fromSettingBoolean()` は、新しい形式のキーを先に見て、なければ古い形式のキーを見ます。新しい形式の名前の付け方を確かめます。

⟦C27⟧

⟦C28⟧

`getKeyWithNamespace()` は接頭辞 `plugins.security.audit.config.` を使っていました。リクエストの本文を記録しない設定は次のとおりです。

⟦C29⟧

出力先の設定は、別の名前の空間です。

⟦C30⟧

# 第4章　設定して再起動する

## 4.1　今の値

⟦C31⟧

`log_request_body` は `True` でした。

## 4.2　バックアップ

⟦C32⟧

⟦C33⟧

構築時のバックアップは `opensearch.yml.pre-audit-20261121-082142` で、元のファイルと一致しました。

## 4.3　2行を足す

同じキーがすでにないことを確かめます。

⟦C34⟧

足すのは次の2行です。

⟦C35⟧

⟦C36⟧

バックアップとの差分が、コメント1行と設定2行だけであることを確かめます。ファイル名は自分のバックアップの名前に置き換えます。

⟦C37⟧

⟦C38⟧

## 4.4　再起動

再起動の前の状態を記録します。

⟦C39⟧

再起動のあいだは、Indexer の API や Wazuh の検索・Relay が一時的に使えなくなります。

⟦C40⟧

⟦C41⟧

構築時は `active`・`running`、新しい PID は 51059、`NRestarts=0` でした。

## 4.5　反映されたか

⟦C42⟧

構築時は、`LOG_REQUEST_BODY: True` のままでした。設定ファイルに書いた `false` は、監査の API が返す設定には反映されていません。次の部で、この理由を調べて直します。

# おわりに

第25部で、`/etc/wazuh-indexer/opensearch.yml` に次の設定を足し、Indexer を再起動しました。

| 設定 | 値 | 結果 |
|---|---|---|
| `plugins.security.audit.type` | `internal_opensearch` | 監査ログを Indexer の中（`security-auditlog-YYYY.MM.dd`）に保存する |
| `plugins.security.audit.config.log_request_body` | `false` | 監査の API にはまだ反映されていない |

バックアップは `/etc/wazuh-indexer/opensearch.yml.pre-audit-*` です。

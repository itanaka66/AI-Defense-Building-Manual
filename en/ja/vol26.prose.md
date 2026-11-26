---
title: "AI自律型サイバー防御システム 構築マニュアル 中編"
subtitle: "第26部　監査ログでリクエストの本文を記録しない"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」中編の第26部です。第25部で `opensearch.yml` に `plugins.security.audit.config.log_request_body: false` を書いて Indexer を再起動しましたが、監査の API は `log_request_body: true` を返したままでした。ここでは、その理由をコードで突き止め、**監査の API（PATCH）で `log_request_body` だけを `false` にします**。

わかった理由は次のとおりです。

- 監査の設定は、Indexer の内部のインデックス `.opendistro_security` の中の文書 `audit` にも保存されている（動的な設定）
- 起動のとき、この文書が**あれば**それを使い、**なければ**`opensearch.yml` から設定を作る
- この環境では文書 `audit` があるため、`opensearch.yml` の `log_request_body: false` は使われない

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は **security-core VM 220（root）** です。
- 管理者の証明書（`admin.pem`・`admin-key.pem`）で Indexer に接続します。`admin` ユーザーのパスワードは使いません。
- `javap` の出力は長いので、結果の要点だけを書きます。

# 第1章　設定はどこから読まれるか

## 1.1　ノードの設定とファイル

⟦C0⟧

ノードの設定の API には、監査の設定は1つも出てきませんでした（出てこないことだけでは、読み込まれていないとは言えません）。

⟦C1⟧

ファイルには2行があり、持ち主と権限も変わっていません。

## 1.2　AuditConfigの作られ方

⟦C2⟧

⟦C3⟧

`AuditConfig.from(Settings)` は、ノードの設定（`opensearch.yml`）から監査の設定を作ります。

⟦C4⟧

`setConfig()` は受け取った設定をそのまま使います。`AuditLogImpl` が値を `true` に戻しているわけではありません。

⟦C5⟧

`OpenSearchSecurityPlugin` から直接は呼ばれていません。設定を扱うクラスを探します。

⟦C6⟧

動的な設定を読み込むのは `ConfigurationRepository`、監査の API は `AuditApiAction` です。

## 1.3　ConfigurationRepository

⟦C7⟧

⟦C8⟧

`setupAuditConfigurationIfAny()` は、`.opendistro_security` に監査の設定の文書があるかで分かれます。

| 文書 | 動き |
|---|---|
| ある | `AuditConfig.from(settings)` を呼ばない（文書の設定を使う） |
| ない | `opensearch.yml` から設定を作って使う |

⟦C9⟧

⟦C10⟧

⟦C11⟧

文書 `audit` が読めれば `isAuditConfigDocPresentInIndex = true`、なければ `false` にして、`opensearch.yml` から初期の設定を作ります。

⟦C12⟧

ログには、どちらの経路を通ったかの記録はありませんでした。

# 第2章　文書があるかを確かめる

## 2.1　管理者の証明書

`admin` ユーザーのパスワードは使わず（わからなくてもリセットはしません）、管理者の証明書で接続します。

⟦C13⟧

⟦C14⟧

構築時は CN が `admin`、有効期間は 2026年11月17日〜2036年11月14日でした。

## 2.2　文書 audit

文書の中身は取らず、あるかどうかだけを確かめます。

⟦C15⟧

構築時の結果は次のとおりで、文書はありました。

⟦C16⟧

これで、`opensearch.yml` の変更が反映されなかった理由がわかりました。なお、この文書の `audit` は JSON ではなく、内部の形式の文字列（940文字）で保存されていたため、ここからは値を取り出していません。値は監査の API で確かめます。

## 2.3　監査のAPIでの値

⟦C17⟧

`log_request_body = True` でした。API の応答では、設定は `config` の下の `audit` の直下にあります。

⟦C18⟧

# 第3章　監査のAPIで変える

## 3.1　変え方を確かめる

⟦C19⟧

⟦C20⟧

- 監査の API は `PUT /_plugins/_security/api/audit/config` と `PATCH /_plugins/_security/api/audit` を受け付ける
- 変更は、監査の設定の再読み込み（ホットリロード）が有効なときだけできる（文書があるので有効）

⟦C21⟧

⟦C22⟧

| 方法 | 動き |
|---|---|
| `PUT` | 設定の全体を置き換える（今回は使わない） |
| `PATCH` | 今の設定を読み、JSON Patch（`add`・`replace`・`remove`）を当てる。変わった項目だけを検証する |

⟦C23⟧

変更した後の設定の全体も検証されます。REST と Transport の記録しないカテゴリーなど、ほかの設定は今のまま残す必要があります。

## 3.2　今の設定

⟦C24⟧

| 項目 | 今の値 |
|---|---|
| `log_request_body` | `true` |
| `exclude_sensitive_headers` | `true` |
| `enable_rest`・`enable_transport` | `true` |
| 記録しないカテゴリー（REST・Transport） | `AUTHENTICATED`・`GRANTED_PRIVILEGES` |
| `ignore_users` | 1件 |

JSON Patch の場所（JSON Pointer）と、読み取り専用の項目を確かめます。

⟦C25⟧

`readonly_paths: []`（読み取り専用の項目はない）でした。変える場所は `/config/audit/log_request_body` です。

## 3.3　PATCH

`log_request_body` だけを `false` にします。ほかの監査の設定には触れません。Indexer の再起動は要りません。

⟦C26⟧

構築時は `Resource updated.` と `HTTP_STATUS:200` が返りました。

## 3.4　反映の確認

⟦C27⟧

| 項目 | 結果 |
|---|---|
| 監査の全体 | 有効 |
| `LOG_REQUEST_BODY` | `False` |
| `EXCLUDE_SENSITIVE_HEADERS` | `True` |
| REST・Transport の監査 | 有効 |
| 記録しないカテゴリー | 変わらず |

これは監査ログに本文を記録しない設定です。ほかのアプリのログなどに本文が出ないことまでは保証しません。

# おわりに

第26部で、監査の設定がどこから読まれるかを突き止め、監査の API の PATCH で `log_request_body` を `false` にしました（再起動なし）。

| 設定の場所 | 役割 |
|---|---|
| `opensearch.yml` | 出力先（`plugins.security.audit.type`）。監査の文書がないときの初期の値 |
| `.opendistro_security` の文書 `audit` | 動いている監査の設定。監査の API（PATCH）で変える |

次の部では、監査ログが実際に保存されているか、本文が記録されていないかを確かめます。

---
title: "AI自律型サイバー防御システム 構築マニュアル 前編"
subtitle: "第14部　アラート中継API（Relay）の構築"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」前編の第14部です。第13部で作った Indexer の読み取り専用ユーザーを使い、security-core の中に、AI Defense Manager（VM 230）へアラートを渡す「中継API（Relay）」を作ります。

Indexer はほかのホストに公開せず、Relay だけが次の条件で外からの接続を受け付けます。

- 待ち受けは `192.168.0.220:8765` だけ（HTTPS）
- サーバー証明書は、Relay 専用の内部CAで発行する
- 呼び出しには Bearer トークンが必要
- 返す項目は第13部 6.1 で決めた10項目だけ。検索の条件や件数の上限は Relay の側で決める
- 秘密の情報（Indexer のパスワード、トークン、秘密鍵）は、systemd の `LoadCredential` で渡す

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、特に断りがない場合 **security-core VM 220（root）** です。
- パスワード・トークン・秘密鍵の中身は、画面にもマニュアルにも出しません。

# 第1章　証明書とトークン

## 1.1　保存先

⟦C0⟧

⟦C1⟧

⟦C2⟧

## 1.2　内部CA

Relay 専用の認証局（CA）を作ります。Indexer の CA とは別に管理します。

⟦C3⟧

## 1.3　サーバー証明書

`192.168.0.220` で接続するため、SAN に IP アドレスを入れます。

⟦C4⟧

⟦C5⟧

CAの署名・IPアドレス・用途・秘密鍵との対応を確かめます。

⟦C6⟧

## 1.4　Bearerトークン

VM 230 が Relay を呼ぶときのトークンを作ります。画面には表示しません。

⟦C7⟧

# 第2章　実行ユーザーと実行環境

## 2.1　専用ユーザー

⟦C8⟧

構築時は systemd 255 で、`LoadCredential` を使えました。

⟦C9⟧

⟦C10⟧

⟦C11⟧

## 2.2　Pythonの仮想環境

security-core のシステムの Python には FastAPI などは入っていません。Relay は標準のライブラリだけで作ることにし、専用の仮想環境を用意します。

⟦C12⟧

⟦C13⟧

仮想環境の作成には `python3.12-venv` が必要です。

⟦C14⟧

⟦C15⟧

⟦C16⟧

ディレクトリを作り、専用ユーザーで仮想環境を作ります。

⟦C17⟧

構築時は、`python3.12-venv` を入れる前にこのコマンドを実行してディレクトリだけができたため、入れた後に仮想環境の作成だけをやり直しました。

⟦C18⟧

⟦C19⟧

⟦C20⟧

# 第3章　systemdで渡す秘密の情報

## 3.1　置き場所

Relay は専用ユーザーで動かし、秘密の情報は root だけが読めるファイルに置いたまま、systemd の `LoadCredential` で起動のときだけ渡します。

⟦C21⟧

⟦C22⟧

## 3.2　ファイルの配置

⟦C23⟧

⟦C24⟧

⟦C25⟧

⟦C26⟧

Relay のサーバー証明書の検証には、Indexer の CA ではなく Relay 専用の CA を使います（構築時は、最初に Indexer の CA で検証して失敗しました）。Relay の CA も配置します。

⟦C27⟧

⟦C28⟧

| ファイル（`/etc/credstore/`） | 中身 |
|---|---|
| `ai-defense-indexer-password` | Indexer の `ai-defense-reader` のパスワード |
| `ai-defense-indexer-ca` | Indexer の CA 証明書 |
| `ai-defense-relay-token` | Bearer トークン |
| `ai-defense-relay-server-cert` | Relay のサーバー証明書 |
| `ai-defense-relay-server-key` | Relay のサーバーの秘密鍵 |
| `ai-defense-relay-ca` | Relay の CA 証明書 |

## 3.3　待ち受けの確認

⟦C29⟧

⟦C30⟧

# 第4章　Relayのプログラム

## 4.1　relay.py

Python の標準のライブラリだけで書いた、HTTPS のサーバーです。

- 接続元は VM 230（`192.168.0.33`）だけ。ほかからは `403`
- `Authorization: Bearer トークン` が一致しなければ `401`（比べるときは `hmac.compare_digest` を使う）
- 使えるのは `GET /health` と `GET /v1/alerts` だけ。`POST`・`PUT`・`DELETE`・`HEAD` は `405`
- `/v1/alerts` の引数は `limit`（1〜100、既定50）と `since_minutes`（1〜1440、既定15）だけ
- Indexer への問い合わせは Relay の中で組み立て、決めた10項目だけを返す（文字列は512文字まで）
- Indexer からの応答が2MBを超えたら返さない

⟦C31⟧

## 4.2　構文の確認

⟦C32⟧

⟦C33⟧

⟦C34⟧

⟦C35⟧

## 4.3　問い合わせ文字列の検査を強める

`parse_qs(..., strict_parsing=True)` は、形の崩れた問い合わせ文字列で `ValueError` を出します。そのままでは処理が止まるため、`400` を返すように直します。

⟦C36⟧

⟦C37⟧

さらに、問い合わせ文字列の長さを128文字まで、引数の数を2つまでに制限します。

⟦C38⟧

⟦C39⟧

# 第5章　systemdのサービス

## 5.1　ユニットファイル

⟦C40⟧

秘密の情報は `LoadCredential` で渡し、プロセスの権限は強く制限します。

- `LoadCredential=名前:パス`：起動のときだけ `$CREDENTIALS_DIRECTORY/名前` として読める
- `ProtectSystem=strict`・`ProtectHome=yes`：ファイルシステムを書き込み不可・ホームを見えなくする
- `CapabilityBoundingSet=`（空）・`NoNewPrivileges=yes`：特権を持たない
- `RestrictAddressFamilies=AF_INET`：IPv4 の通信だけ
- `MemoryMax=256M`・`TasksMax=32`：使う資源の上限

⟦C41⟧

⟦C42⟧

⟦C43⟧

## 5.2　起動前の確認

ファイルの権限と、専用ユーザーで Python と relay.py を読めることを確かめます。

⟦C44⟧

⟦C45⟧

⟦C46⟧

⟦C47⟧

⟦C48⟧

ユニットの内容と、relay.py が読む資格情報の名前が一致していることを確かめます。

⟦C49⟧

⟦C50⟧

アクセスのログに、問い合わせ文字列や認証の情報が残らないことも確かめます。

> **注意**　構築時にこの確認をした時点で、relay.py はすでに 4.1〜4.3 の内容から変わっていました（アクセスのログを「接続元のIPアドレスとステータス」だけにする `log_request` の上書き、同時に処理する要求を8つまでにする `threading.BoundedSemaphore(8)` の追加）。この変更の手順は構築の記録に残っていないため、本書には掲載していません（不足情報メモ 14-A）。

⟦C51⟧

⟦C52⟧

`LoadCredential` は、中身を守るため `[unprintable]` と表示されます。

# 第6章　起動と接続の確認

## 6.1　起動

起動すると、`192.168.0.220:8765` で待ち受けを始めます。

⟦C53⟧

構築時の結果は `Active: active (running)` でした。なお、この時点では `disabled`（自動起動しない）のままです。

⟦C54⟧

## 6.2　TLSの確認

⟦C55⟧

構築時の結果は次のとおりです。

- `Protocol version: TLSv1.3`
- `Peer certificate: CN = 192.168.0.220`
- `Verification: OK`

`Can't use SSL_get_servername` は、IPアドレスで接続したため SNI の名前を使えないという通知で、検証の失敗ではありません。

## 6.3　VM 230からの接続

> **実行先：ai-defense-manager VM 230（root）**

⟦C56⟧

`succeeded!` と表示されれば、VM 230 から Relay の待ち受けに届いています。

# おわりに

第14部では、security-core に次の中継APIを作りました。

| 項目 | 内容 |
|---|---|
| 待ち受け | `https://192.168.0.220:8765`（TLS 1.2以上） |
| 接続元 | `192.168.0.33`（VM 230）だけ |
| 認証 | Bearer トークン |
| API | `GET /health`、`GET /v1/alerts?limit=&since_minutes=` |
| 実行 | `ai-defense-relay.service`（専用ユーザー、`LoadCredential`） |

次の部では、VM 230 にトークンと CA 証明書を安全に渡し、Relay からアラートを受け取れるようにします。

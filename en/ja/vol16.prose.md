---
title: "AI自律型サイバー防御システム 構築マニュアル 前編"
subtitle: "第16部　WazuhアラートをAI分析につなぐ"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」前編の第16部です。第15部で VM 230 に置いた Relay の接続情報を使い、AI Defense Manager（FastAPI）に次の機能を足します。

⟦C0⟧

追加するAPIは次の2つです。既存の `/health` と `/api/v1/analysis` はそのまま残します。

- `GET /api/v1/wazuh/events`：Relay からアラートを取り、`SecurityEvent` にして返す
- `POST /api/v1/wazuh/analyze`：取ったアラートを既存の AI 分析（`analyze_events()`）に渡し、防御の提案を返す

AI に渡すのは検証済みのイベントだけです。Relay のトークンや接続先は渡しません。また、AI に防御の操作（IPの遮断など）を実行する権限は与えません。

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、特に断りがない場合 **ai-defense-manager VM 230（root）** です。

# 第1章　今のアプリを確かめる

## 1.1　ファイルの構成

⟦C1⟧

設定・イベントのスキーマ・アプリ本体・分析API・分析サービス・分析のスキーマを読みます（変更はしません）。

⟦C2⟧

⟦C3⟧

⟦C4⟧

⟦C5⟧

⟦C6⟧

⟦C7⟧

`AIAnalysisRequest` は1〜100件の `SecurityEvent` を受け取る作りです。Relay も最大100件なので、そのままつなげられます。

## 1.2　依存パッケージ

⟦C8⟧

`httpx`（HTTPS の通信）、`pydantic`（検証と変換）、`fastapi`（API）はすでに入っています。追加のインストールはしません。

## 1.3　動いているか

⟦C9⟧

⟦C10⟧

⟦C11⟧

構築時は、systemd のサービスはなく、ポート 8000 で待ち受けているプロセスもありませんでした（アプリは止まっている状態です）。

⟦C12⟧

⟦C13⟧

`tests` と `config` は空でした。

## 1.4　防御の提案のスキーマ

⟦C14⟧

⟦C15⟧

すでに次の安全のための制約が入っています。これは変えません。

- AI の提案は JSON で返す
- `temporary_block_ip`（一時的なIPの遮断）はグローバルIPだけが対象で、別々の証拠イベントIDが2件以上必要
- TTL は1〜900秒
- 遮断の提案は、必ず人の承認が必要（`ActionProposal` の初めの状態は `PENDING`）
- 実際に遮断する処理は含まれていない

## 1.5　ユーザーと権限

⟦C16⟧

| 対象 | 持ち主 | 意味 |
|---|---|---|
| アプリ本体 | `root:ai-defense` | 実行ユーザーはコードを書き換えられない |
| 仮想環境 | `root:root` | 実行ユーザーはパッケージを書き換えられない |
| `data`・`logs` | `ai-defense:ai-defense` | アプリの書き込み先 |
| Relay の接続情報 | `root:ai-defense` | 実行ユーザーは読める。ほかのユーザーは読めない |

⟦C17⟧

⟦C18⟧

# 第2章　Relayから取ってSecurityEventにする

## 2.1　実際のデータの形

Relay が返す値の形を、1件だけ取って確かめます。

⟦C19⟧

構築時の結果（抜粋）は次のとおりです。

| 項目 | 値 |
|---|---|
| `timestamp` | `'2026-11-20T23:54:26.205+0000'`（タイムゾーン付きの文字列） |
| `rule.level` | `3`（整数） |
| `rule.id` | `'87203'` |
| `rule.description` | `'Proxmox VE authentication succeeded.'` |
| `agent.name` | `'pve'` |
| `decoder.name` | `'pvedaemon'` |

`agent.ip` はエージェント自身のIPアドレスなので、攻撃元のIPとしては扱いません。

## 2.2　変換のきまり

Wazuh のレベルを、`SecurityEvent` の重大度に次のように置き換えます。

| Wazuhのレベル | 重大度 |
|---:|---|
| 0〜3 | `info` |
| 4〜7 | `low` |
| 8〜11 | `medium` |
| 12〜14 | `high` |
| 15〜16 | `critical` |

## 2.3　wazuh_relay.py

⟦C20⟧

貼り付けたときに端末の表示が乱れることがあります。ファイルが最後まで書けたかを行数と末尾で確かめます（構築時は137行でした）。

⟦C21⟧

⟦C22⟧

## 2.4　設定の追加

接続先と、接続情報のファイルの場所を設定に足します。トークンそのものは設定に書きません。

⟦C23⟧

⟦C24⟧

# 第3章　取得のAPI

## 3.1　wazuh.py（取得だけ）

`limit` は1〜100件（既定50件）、`since_minutes` は1〜1440分（既定60分）です。Relay との通信に失敗したら `502` を返し、接続情報や Relay の生のデータは返しません。

⟦C25⟧

⟦C26⟧

## 3.2　アプリへの登録

⟦C27⟧

## 3.3　登録の確認

構築時の FastAPI 0.165.0 では、`include_router()` で登録したルーターは遅れて組み込まれるため、`app.routes` を見ても `/api/v1/...` が出てきません。そこで、FastAPI が作る OpenAPI の仕様で確かめます。

⟦C28⟧

## 3.4　実行ユーザーで取ってみる

`ai-defense` ユーザーで Relay から5件を取り、`SecurityEvent` に変換します。

⟦C29⟧

構築時は5件すべてが変換でき、`rule.level=3` は `info` になりました。Relay は攻撃元のIPを返さないため、`source_ip` は `None` のままです。

# 第4章　分析のAPI

## 4.1　リクエストのスキーマ

⟦C30⟧

⟦C31⟧

## 4.2　wazuh.py（分析を追加）

`POST /api/v1/wazuh/analyze` は次の順に処理します。

1. Relay から Wazuh のアラートを取る
2. `SecurityEvent` に変換して検証する
3. 0件なら AI を呼ばずに `404` で終わる
4. 既存の `analyze_events()` に渡す
5. `AIAnalysisProposal`（防御の提案）を返す

⟦C32⟧

⟦C33⟧

構築時は63行で、末尾まで書けていました。

⟦C34⟧

# 第5章　Wazuh → Ollama → AI分析の確認

## 5.1　モデルがあるか

分析に使う `qwen3:8b` が Ollama（VM 101）にあるかを確かめます。まだ分析のリクエストは送りません。

⟦C35⟧

## 5.2　つないで分析する

実行ユーザーで5件のアラートを取り、既存の分析に渡します。アラートの内容は LLM に送られますが、防御の操作・IPの遮断・設定の変更はいっさい行いません。

⟦C36⟧

構築時の結果は次のとおりです。認証の成功やログインのセッションの記録が中心だったため、遮断の提案が出ないのは妥当です。

| 項目 | 結果 |
|---|---|
| `severity` | `info` |
| `confidence` | `0.8` |
| `recommended_action` | `no_action` |
| `evidence_event_count` | `5` |
| `target_ip`・`ttl_seconds` | `None` |

## 5.3　追加したファイルの権限

⟦C37⟧

構築時は、新しく作った API 関係の3ファイルが `root:root` の `644` になっていました。既存のファイルと持ち主をそろえる作業は、次の部で行います。

# おわりに

第16部で、AI Defense Manager に次のAPIを足しました。

| API | 内容 |
|---|---|
| `GET /api/v1/wazuh/events` | Relay からアラートを取り、`SecurityEvent` で返す |
| `POST /api/v1/wazuh/analyze` | 取ったアラートを AI で分析し、防御の提案を返す |

次の部では、ファイルの権限をそろえ、AI Defense Manager を systemd のサービスとして動かします。

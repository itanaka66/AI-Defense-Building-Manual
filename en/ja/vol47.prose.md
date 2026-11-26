---
title: "AI自律型サイバー防御システム 構築マニュアル 第4巻"
subtitle: "第47部　AI Defense Managerの既存の実装を調べる"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」第4巻の第47部です。第46部で、LLM に渡す Wazuh のアラートの項目を7つに決めました。ここでは、その許可リストを組み込む場所を決めるために、VM 230 の AI Defense Manager の既存の実装を、読み取りだけで調べます。

1. VM 230 のネットワークと、待ち受けているサービスを確かめる
2. API の一覧と入力の形（スキーマ）を調べる
3. モジュールの構成と依存関係、Wazuh のアラートから LLM までのデータの流れを追う
4. いまの変換の処理（項目・イベントの ID・重大度・分類）を確かめ、目標の仕様を決める
5. テストと Git が無いことを確かめ、変更の前の準備を決める

ソースの本文・SQL・秘密の情報は表示しません。ファイルの変更・サービスの再起動・LLM への送信もしません。

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **VM 230**：ai-defense-manager（root）

# 第1章　VM 230 のネットワークとサービス

## 1.1　アドレスと待ち受け

> **実行先：VM 230**

⟦C0⟧

| 項目 | 結果 |
|---|---|
| IPv4 | `192.168.0.33/24`（`enp6s18`）。この時点では DHCP で受け取ったアドレス（あとの部で `192.168.0.221` に固定する） |
| ゲートウェイ | `192.168.0.1` |
| SSH | `0.0.0.0:22` |
| アプリケーション | `127.0.0.1:8000` だけ |

ポート 8000 はループバックのアドレスだけで待ち受けていて、VM 220 から直接つなぐ構成にはなっていません。**8000 番は外に公開しません。**

## 1.2　ポート 8000 のサービス

> **実行先：VM 230**

⟦C1⟧

FastAPI と Uvicorn の `AI Defense Manager API` が systemd で自動起動して動き、プロジェクトは `/opt/ai-defense-manager` にあり、`/health` と `/openapi.json` は `HTTP 200` でした。新しい API のサーバーを足す必要はありません。

# 第2章　API と入力の形

## 2.1　API の一覧

> **実行先：VM 230**

⟦C2⟧

| API | メソッド | 用途 |
|---|---|---|
| `/api/v1/analysis` | POST | AI の分析 |
| `/api/v1/wazuh/analyze` | POST | Wazuh のイベントの分析 |
| `/api/v1/wazuh/events` | GET | Wazuh のイベントの取得 |
| `/health` | GET | 状態の確認 |

Wazuh と連携する API はすでにあります。新しい受け口を作るより、これが7項目の許可リストに合っているかを調べます。

## 2.2　入力の形

> **実行先：VM 230**

⟦C3⟧

既存の `SecurityEvent` は次の形で、第46部の7項目とは名前も構造も違います。

- 必ず要るもの：`source`・`severity`・`event_category`・`event_summary`
- 任意のもの：`event_id`・`observed_at`・`agent_id`・`agent_name`・`source_ip`・`destination_ip`・`rule_id`・`rule_description`

# 第3章　モジュールとデータの流れ

## 3.1　ソースの構成

> **実行先：VM 230**

⟦C4⟧

API は `api/analysis.py` と `api/wazuh.py` に分かれ、入力の形は `schemas/` に、分析の履歴は `services/analysis_history.py` にありました。

## 3.2　内部の構造

Python の AST で、関数・クラス・使っているモジュール・DB にアクセスする関数の名前だけを取り出します。

> **実行先：VM 230**

⟦C5⟧

分析の履歴の保存には SQLite が使われていました。

## 3.3　依存関係

> **実行先：VM 230**

⟦C6⟧

| モジュール | 役割 |
|---|---|
| `services/wazuh_relay.py` | Wazuh のアラートの取得と変換 |
| `services/event_sanitizer.py` | イベントの要約の伏せ字、IP アドレスのマスク |
| `services/ai_analysis.py` | AI の分析 |
| `services/analysis_history.py` | SQLite の分析の履歴 |
| `schemas/action.py` | 防御の操作の提案・承認の状態・検証 |
| `schemas/analysis_proposal.py` | AI の分析の結果と、操作の制約 |

## 3.4　伏せ字・取得・分析の仕組み

> **実行先：VM 230**

⟦C7⟧

| 機能 | いまの実装 | 評価 |
|---|---|---|
| Wazuh の取得 | `fetch_wazuh_events()` | そのまま使う |
| Wazuh の変換 | `_convert_alert()` | 許可リストを入れる場所 |
| IP アドレスのマスク | `sanitize_event_summary()` | そのまま使う |
| AI の分析 | `analyze_events()` | そのまま使う |
| AI の出力の検証 | Pydantic の `model_validate()` | そのまま使う |
| 操作の制約 | `validate_action` | 安全のための大事な土台 |
| 承認の管理 | `ApprovalStatus` | 人の承認に使う |

目標の流れは次のとおりです。

⟦C8⟧

## 3.5　データの流れを追う

> **実行先：VM 230**

⟦C9⟧

Wazuh の生のアラートは `wazuh_relay.py` で `SecurityEvent` に変換され、そのあと `ai_analysis.py` で `event_summary` が伏せ字にされて AI に送られます。AI に送る直前の伏せ字だけでは、余分な項目が混ざらないことを保証できないので、次の2段にします。

1. Wazuh の取得の直後：許可した項目だけを取り出して確かめる
2. AI に送る直前：いまの伏せ字を残し、入力をもう一度確かめる

# 第4章　いまの変換の処理

## 4.1　入力と出力の項目

> **実行先：VM 230**

⟦C10⟧

`_convert_alert()` は7項目のほかに `agent_name` も `SecurityEvent` に渡していました。AI に送る内容は `event_id`・`observed_at`・`severity`・`rule_id`・`event_category`・`event_summary` の6項目です。Wazuh の生のデータをまるごと送ってはいませんが、7項目だけに限った入力の境目にはなっていません。

| Wazuh の項目 | VM 230 の中の項目 |
|---|---|
| `timestamp` | `observed_at` |
| `rule.id` | `rule_id` |
| `rule.level` | `severity` |
| `rule.groups` | `event_category` |
| `rule.description` | `rule_description` |
| `decoder.name` | 保存しない |
| `agent.id` | `agent_id` |

`agent_name`・IP アドレス・`full_log`・`data`・`location`・`predecoder` は入力の境目で除きます。

## 4.2　イベントの ID

> **実行先：VM 230**

⟦C11⟧

- `SecurityEvent.event_id` は `uuid4` で自動で作られる
- Wazuh の `rule.id` は別の項目として持つ
- AI の提案の `evidence_event_ids` は UUID を求める

**Wazuh のルールの ID をイベントの UUID として使ってはいけません。** また、AI の提案の `ttl_seconds` は最大900秒、`requires_human_approval` は既定で `True` です。これらの制約は残します。

## 4.3　Wazuh の項目の使い方

> **実行先：VM 230**

⟦C12⟧

`_convert_alert()` は `timestamp`・`rule.level`・`rule.id`・`rule.description`・`agent.id`・`agent.name`・`location`・`decoder.name` を参照していました。`rule.groups` は直接読まず、分類のための辞書を通していました。

## 4.4　重大度と分類の変換

> **実行先：VM 230**

⟦C13⟧

いまの仕様として残すもの：

| Wazuh の Level | 中の重大度 |
|---|---|
| 0〜3 | info |
| 4〜7 | low |
| 8〜11 | medium |
| 12〜14 | high |
| 15〜16 | critical |

| Wazuh 由来の分類 | 中の分類 |
|---|---|
| pvedaemon | virtualization_management |
| pam | authentication |
| sshd | remote_access |
| useradd | account_management |
| open-userdel | account_management |

`rule.groups` は複数の値を持つので、許可したグループだけで分類し、知らない値をそのまま中の分類に流さないようにします。

# 第5章　変更の前の準備

## 5.1　テストとバージョン管理

> **実行先：VM 230**

⟦C14⟧

テストのファイルは無く、Git のリポジトリもありませんでした。コードを変えたときに、Git で元に戻すことも、既存のテストで守ることもできません。そこで、次のテストを新しく用意する方針にします。

| テスト | 確かめること |
|---|---|
| 入力の許可リスト | 7項目のほかを混ぜない |
| 必須の項目 | 欠け・型の違い・正しくない値を拒む |
| 秘密の情報を除く | `full_log`・`data`・IP・ユーザー名などを AI に送らない |
| 重大度の変換 | 0〜16 の境目 |
| 分類の変換 | いまの5分類と、知らない分類 |
| UUID | イベントの ID と証拠の ID の対応 |
| AI に送る内容 | 実際に通信せず、送る JSON を調べる |
| 操作の安全 | TTL の上限900秒、承認が要ることを保つ |

## 5.2　空き容量と対象のファイル

> **実行先：VM 230**

⟦C15⟧

| 項目 | 結果 |
|---|---|
| VM 230 の空き | 約 39GB |
| 対象のファイル | 5つ |
| SHA256 | 5つとも取得 |
| バックアップの専用のディレクトリ | まだ無い |
| AI Defense Manager | `active` |
| Git | 無し |

# おわりに

第47部で、VM 230 の AI Defense Manager の既存の実装を調べました。

| 項目 | 結果 |
|---|---|
| API | FastAPI・Uvicorn、`127.0.0.1:8000` だけ。Wazuh の取得・分析の API がある |
| 許可リストを入れる場所 | `services/wazuh_relay.py` の `_convert_alert()`（取得の直後）と、`services/ai_analysis.py` の AI に送る直前 |
| 残すもの | 伏せ字の処理、`uuid4` のイベントの ID、重大度の変換、TTL 900秒、人の承認 |
| 準備 | テスト・Git が無いので、変える前にバックアップをとり、独立したテストで確かめる |

次の第48部では、変える前のバックアップをとり、Wazuh のイベントの変換を7項目に絞って、合成したデータで試験します。

---
title: "AI自律型サイバー防御システム 構築マニュアル 第4巻"
subtitle: "第70部　AI防御のエージェントを作り始める"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」第4巻の第70部です。第69部までで、Wazuh の防御の土台と、AI Defense Manager（VM 230）の入力・出力・認証・ログの守りを整えました。ここからは、その上に **AI 防御のエージェント**を作ります。

この部では、最初の2つのエージェントを作ります。

| エージェント | 役割 |
|---|---|
| `LogAnalysisAgent` | ログの分析。既存の AI の分析（`analyze_events()`）に任せる、読むだけの薄い層 |
| `ThreatAnalysisAgent` | 脅威の分析と証拠の検証。ログの分析の結果について、証拠のイベントの ID の重なり・欠け・入力との食い違いを独立に確かめる |

決めた原則は次のとおりです。

1. エージェントは読み取りと分析だけを行い、防御の操作を実行しない
2. `TEMPORARY_BLOCK_IP` を提案できても、実際の遮断はしない。防御の操作は既存の `ActionProposal` の制約（承認が要る、`PENDING` で始まる）に従う
3. 既存の API・DB・設定・サービスは変えない。テストは模した分析を使い、Ollama への通信や DB へのアクセスをしない
4. 既存のファイルを上書きしない

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **VM 230**：ai-defense-manager（root。`aidefense` でログインしたときは `sudo -i` で root になる）

# 第1章　既存の作りを調べる

## 1.1　サービスとアプリケーション

> **実行先：VM 230**

⟦C0⟧

API は `127.0.0.1:8000` で動き（Main PID `2340`、NRestarts 0）、作業のディレクトリは `/opt/ai-defense-manager` でした。

> **実行先：VM 230**

⟦C1⟧

`/opt/ai-defense-manager/app` と `tests` は root の持ち物で、`aidefense` からは読めません（アプリケーションのコードを守る作り）。この守りは変えません。

## 1.2　ソースの一覧と AI の分析の作り

> **実行先：VM 230**

⟦C2⟧

⟦C3⟧

| 既存のもの | 役割 |
|---|---|
| `app/services/ai_analysis.py` | AI の分析のエンジン |
| `app/services/wazuh_relay.py` | Wazuh のイベントの取得 |
| `app/services/event_sanitizer.py` | イベントの伏せ字 |
| `app/services/analysis_history.py` | 分析の履歴の保存 |
| `app/agents`・`app/policies` | ディレクトリだけで、Python のファイルは無い |

## 1.3　入出力の型と検証

> **実行先：VM 230**

⟦C4⟧

⟦C5⟧

最初のエージェントは、既存の `AIAnalysisRequest` と `AIAnalysisProposal` を入出力に使えます。`AIAnalysisProposal` には `confidence`・`evidence_event_ids`・`requires_human_approval` などがあります。

> **実行先：VM 230**

⟦C6⟧

- IP の遮断の提案には、別々の証拠のイベントが2件以上要る
- 遮断の対象はグローバルの IP だけ
- `target_ip` と `ttl_seconds` が必須
- 人の承認が必須
- 実行の提案は `PENDING` で始まる

## 1.4　モデルへの問い合わせの流れ

> **実行先：VM 230**

⟦C7⟧

⟦C8⟧

Ollama への問い合わせ（`httpx.AsyncClient`）・JSON の答えの解析・`AIAnalysisProposal` による検証は、すでに `ai_analysis.py` が行っています。最初のエージェントはモデルの呼び出しを重ねて作らず、既存の `analyze_events()` を使います。

## 1.5　テストの環境

> **実行先：VM 230**

⟦C9⟧

Python 3.12.3・Pydantic 2.14.4・FastAPI 0.165.0 で、`pytest` は無く、標準の `unittest` を使います。

# 第2章　ログの分析のエージェント

## 2.1　作って試す

`app/agents/log_analysis.py` と `tests/test_log_analysis_agent.py` の2つだけを新しく作ります。ファイルがまだ無いことを確かめてから作ります。

> **実行先：VM 230**

⟦C10⟧

## 2.2　テストのデータを直す

2.1 のテストは、エージェントの処理の前に、テストのデータの作り方の誤りで失敗しました。エージェントの本体は変えず、テストのファイルだけを3回に分けて直します。

1. `AIAnalysisRequest` の必須の `events` に、正しい `SecurityEvent` を1件入れる

> **実行先：VM 230**

⟦C11⟧

2. `AIAnalysisProposal` の必須の項目（`summary`・`severity`・`confidence`・`evidence_event_ids`・`reasoning`）を入れる

> **実行先：VM 230**

⟦C12⟧

3. `evidence_event_ids` は1件以上が必須なので、テストのイベントの `event_id` を証拠の ID に使う

> **実行先：VM 230**

⟦C13⟧

`test_delegates_request_and_returns_proposal`・`test_propagates_analysis_error` の2件とも `OK` でした。Ollama への実際の要求・DB の参照・サービスの再起動はありません。

## 2.3　中身を確かめる

> **実行先：VM 230**

⟦C14⟧

`LogAnalysisAgent` は、既存の `analyze_events()` に任せる薄い読み取り専用のエージェントで、防御の操作の実行・承認の機能は持っていません。

# 第3章　脅威の分析のエージェント

## 3.1　設計

> **実行先：VM 230**

⟦C15⟧

⟦C16⟧

既存の `AIAnalysisProposal` に重大度・信頼度・証拠のイベントの ID・勧める対応があるので、新しいスキーマは作りません。2つの分析の API は、まだ `analyze_events()` を直接呼んでいて、`LogAnalysisAgent` は API からは使われていません。

`ThreatAnalysisAgent` は、AI の答えを包み直すだけではなく、ログの分析の結果を独立に確かめる役割にします。

- `LogAnalysisAgent` に分析を任せる
- 返された提案について、証拠の ID の重なり・入力のイベントの ID の重なり・入力に無い証拠の ID を確かめる
- 食い違いは専用の例外で拒む

## 3.2　作って試す

> **実行先：VM 230**

⟦C17⟧

| テスト | 結果 |
|---|---|
| 正しい証拠の ID を受け入れる | 合格 |
| ログの分析のエージェントに任せる | 合格 |
| 証拠の ID の重なりを拒む | 合格 |
| 入力のイベントの ID の重なりを拒む | 合格 |
| 入力に無い証拠の ID を拒む | 合格 |

5件すべて合格でした。

## 3.3　全部のテスト

> **実行先：VM 230**

⟦C18⟧

2つのエージェントのテスト7件すべてが合格し、互いや既存の機能への影響は、この範囲では見られませんでした。

# おわりに

第70部で、最初の2つの AI 防御のエージェントを作りました。

| エージェント | ファイル | テスト |
|---|---|---|
| `LogAnalysisAgent` | `app/agents/log_analysis.py` | 2件 合格 |
| `ThreatAnalysisAgent` | `app/agents/threat_analysis.py` | 5件 合格 |

どちらも読み取りと分析だけを行い、防御の操作は実行しません。まだ API にはつないでおらず、サービスも再起動していません。次の第71部では、イベントの相関のエージェント、全体をまとめるエージェント、防御の判断の方針のエージェントに進みます。

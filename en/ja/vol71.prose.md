---
title: "AI自律型サイバー防御システム 構築マニュアル 第4巻"
subtitle: "第71部　相関・統括・防御の判断のエージェント"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」第4巻の第71部で、第4巻の最後の部です。第70部で、ログの分析と脅威の分析の2つのエージェントを作りました。ここでは、次のエージェントを作ります。

| エージェント | 役割 |
|---|---|
| `IncidentCorrelationAgent` | 複数のイベントを、時刻・エージェント・分類で関連づける。LLM を使わない決まった処理 |
| `SecurityAnalysisOrchestrator` | 相関と AI の分析をまとめる（分析の統括） |
| `DefensePolicyAgent` | AI の提案をそのまま信じず、サーバーの側の規則で判断する |

どのエージェントも、防御の操作・IP の遮断・通知・DB への保存は行いません。既存の API・DB・設定・サービスも変えません。

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **VM 230**：ai-defense-manager（`192.168.0.221`、root。`aidefense` でログインしたときは `sudo -i` で root になる）

# 第1章　イベントの相関のエージェント

## 1.1　使える項目

> **実行先：VM 230**

⟦C0⟧

`SecurityEvent` には時刻・送り元の IP・宛先の IP・エージェントの ID・分類がありますが、いまの Wazuh の変換は `timestamp`・ルールの情報・グループ・`agent.id` だけを使い、IP アドレスは渡していません（第48部で7項目に絞ったため）。**いまの Wazuh のイベントだけでは、IP アドレスによる相関はできません。** 使える項目だけで相関します。

| 項目 | 最初の仕様 |
|---|---|
| 相関の鍵 | 同じ `agent_id` で、同じ `event_category` |
| 時間の窓 | 最初のイベントから10分以内 |
| 最小のイベントの数 | 2件 |
| 時刻 | タイムゾーン付きの `observed_at`（UTC にそろえる） |
| IP による相関 | いまは使わない |
| 出力 | インシデントの候補、含まれるイベントの ID、時刻の範囲 |

`agent_id` が無いイベントは、誤って関連づけないように対象外にします。10分は今回の最初の設計の値です。

## 1.2　作る

`app/agents/incident_correlation.py` と `tests/test_incident_correlation_agent.py` を新しく作ります。

> **実行先：VM 230**

⟦C1⟧

テストのファイルが読み込むモジュールの名前が実際と違い、読み込みで失敗しました。

⟦C2⟧

## 1.3　テストの読み込みを直す

`SecurityEvent` は `app.schemas.security_event` にあります。

⟦C3⟧

テストのファイルの読み込みの1行だけを直します。エージェントの本体・API・DB・サービスには触れません。

> **実行先：VM 230**

⟦C4⟧

| エージェント | テスト |
|---|---:|
| `LogAnalysisAgent` | 2件 合格 |
| `ThreatAnalysisAgent` | 5件 合格 |
| `IncidentCorrelationAgent` | 7件 合格 |

合わせて14件すべて合格でした。確かめた仕様は、同じエージェント・同じ分類のイベントを10分以内で関連づける、タイムゾーンを UTC にそろえる、10分を超えて数珠つなぎにしない、`agent_id` が無いイベントは対象外、イベントの ID の重なりを拒む、防御の操作をしない、です。

# 第2章　分析を統括するエージェント

## 2.1　設計

> **実行先：VM 230**

⟦C5⟧

`ThreatAnalysisAgent` は、中で `LogAnalysisAgent` を呼びます。統括のエージェントから両方を別々に呼ぶと、AI の分析が2回行われてしまいます。そこで次のようにします。

1. 相関の分析を先に行う
2. `ThreatAnalysisAgent` を1回だけ呼ぶ（中で `LogAnalysisAgent` が動く）
3. 両方の結果をまとめて返す
4. どちらかが失敗したら例外を伝え、不完全な結果を成功として扱わない
5. 防御の操作・IP の遮断・通知・DB への保存はしない

## 2.2　作って試す

`app/agents/security_analysis_orchestrator.py` と `tests/test_security_analysis_orchestrator.py` を新しく作ります。

> **実行先：VM 230**

⟦C6⟧

| テストの対象 | 結果 |
|---|---:|
| `IncidentCorrelationAgent` | 7件 合格 |
| `LogAnalysisAgent` | 2件 合格 |
| `ThreatAnalysisAgent` | 5件 合格 |
| `SecurityAnalysisOrchestrator` | 4件 合格 |
| 合計 | 18件 合格・0件 失敗 |

AI の分析は1回だけ行われ、相関の分析が失敗したときは AI の分析を行わず、AI の分析が失敗したときは例外を伝えることを確かめました。

# 第3章　防御の判断のエージェント

## 3.1　既存の方針と操作の定義

> **実行先：VM 230**

⟦C7⟧

| 項目 | 既存の規則 |
|---|---|
| IP の遮断の対象 | グローバルの IP だけ |
| TTL | 1〜900秒 |
| 証拠 | 別々のイベントの ID が2件以上 |
| 承認 | 必須 |
| 最初の承認の状態 | `PENDING` |
| AI の承認の判断 | サーバーの側の方針が優先 |

`app/policies/` は空で、`DefensePolicyAgent` はまだありませんでした。

## 3.2　設計

`DefensePolicyAgent` は、AI の提案を `ActionProposal` に変える前に、独立に判断します。どちらの結果でも、このエージェント自身は防御の操作をしません。

| AI の提案 | 判断 |
|---|---|
| `NO_ACTION` | 操作を作らない |
| `MONITOR`・`HUMAN_REVIEW` | 既存の `ActionType` に当たる値が無いので、安全の側に倒して拒む |
| `COLLECT_EVIDENCE`・`NOTIFY` | 提案を作る |
| `TEMPORARY_BLOCK_IP` | IP・TTL・証拠の ID・相関の結果を確かめ、必ず `PENDING` にする |

IP の遮断は、さらに次をすべて満たすときだけ許します。

- 2件以上の証拠が、同じ相関のまとまり（クラスタ）に入っている
- 重大度が `high` か `critical`
- 信頼度が `0.90` 以上

これは防御の方針の側の決まった基準で、AI の承認の印では変えられません。

## 3.3　作るためのスクリプト

`app/agents/defense_policy.py` と `tests/test_defense_policy_agent.py` の2つのファイルを作り、境目の条件も試すスクリプトです。

> **実行先：VM 230**

⟦C8⟧

**このスクリプトを実行した結果は、受け取った構築の記録の範囲にはありません**（不足情報メモ）。

# おわりに

第71部で、イベントの相関・分析の統括のエージェントを作り、防御の判断のエージェントを設計しました。

| エージェント | ファイル | テスト |
|---|---|---|
| `LogAnalysisAgent` | `app/agents/log_analysis.py` | 2件 合格 |
| `ThreatAnalysisAgent` | `app/agents/threat_analysis.py` | 5件 合格 |
| `IncidentCorrelationAgent` | `app/agents/incident_correlation.py` | 7件 合格 |
| `SecurityAnalysisOrchestrator` | `app/agents/security_analysis_orchestrator.py` | 4件 合格 |
| `DefensePolicyAgent` | `app/agents/defense_policy.py`（作るスクリプトまで。結果は記録に無い） | — |

どのエージェントも、まだ API にはつないでおらず、防御の操作は実行しません。

構築の記録は、ここまでです。

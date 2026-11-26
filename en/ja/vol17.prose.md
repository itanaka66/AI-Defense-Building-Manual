---
title: "AI自律型サイバー防御システム 構築マニュアル 前編"
subtitle: "第17部　AI Defense Managerのサービス化と起動順序"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」前編の第17部です。第16部で Wazuh のアラートを AI の分析につなぎました。ここでは次の3つを行い、VM や Proxmox を再起動しても連携が動くようにします。

1. AI Defense Manager を systemd のサービスにする（`127.0.0.1:8000` だけで待ち受け）
2. Relay（VM 220）と AI Defense Manager（VM 230）を自動起動にする
3. Proxmox で、VM 220 を先に、VM 230 を後に起動するように順番を決める

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **VM 230**：ai-defense-manager（root）
  - **VM 220**：security-core（root）
  - **pve**：Proxmox のホスト（root）

# 第1章　ファイルの権限をそろえる

> **実行先：VM 230**

第16部で作った3つのファイルは `root:root` の `644` でした。ほかのアプリのファイルと同じ `root:ai-defense` の `640` にそろえます。

⟦C0⟧

サービスにする前に、実行ユーザー `ai-defense` でアプリ全体を読み込めることを確かめます（サーバーは起動しません）。

⟦C1⟧

構築時は、`/health`、`/api/v1/analysis`、`/api/v1/wazuh/events`、`/api/v1/wazuh/analyze` の4つが出ました。

# 第2章　systemdのサービス

## 2.1　ユニットファイル

> **実行先：VM 230**

同じ名前のユニットがないことを確かめます。

⟦C2⟧

第14部の Relay と同じ考え方で、強く制限したサービスにします。

- 実行ユーザーは `ai-defense`
- 待ち受けは `127.0.0.1:8000` だけ（外には公開しない）
- ファイルシステムは原則として読み取り専用（`ProtectSystem=strict`）
- 特権を持たない。カーネルやデバイスに触れない
- メモリの上限は 1GiB。異常に終わったときだけ自動で再起動する

⟦C3⟧

貼り付けで末尾が乱れて見えることがあるので、最後まで書けたかを確かめます。

⟦C4⟧

⟦C5⟧

## 2.2　登録

⟦C6⟧

`LoadState=loaded`、`ActiveState=inactive`（まだ止まっている）、`UnitFileState=disabled`、`User=ai-defense` となれば登録できています。

## 2.3　起動

⟦C7⟧

`active (running)` になれば起動できています。

⟦C8⟧

構築時は、`127.0.0.1:8000` だけで待ち受け、`{"status":"ok","service":"ai-defense-manager","version":"0.1.0"}` が返りました。

# 第3章　HTTPでの確認

> **実行先：VM 230**（`/opt/ai-defense-manager` で実行）

## 3.1　アラートの取得

AI の分析はせず、Wazuh のアラートを5件取ります。

⟦C9⟧

構築時は、Proxmox VE の認証成功が2件、ユーザー（グループ）の削除が1件、PAM のログインセッションの開始と終了が各1件、の5件が返りました。

## 3.2　AIの分析

最大5件を `qwen3:8b` に渡します。AI は分析と提案だけを行い、防御の操作は実行しません。

⟦C10⟧

構築時は `severity: info`、`confidence: 0.8`、`recommended_action: no_action`、`evidence_event_count: 5` が返りました。

ここまでで、次の流れがつながりました。

⟦C11⟧

# 第4章　自動起動

## 4.1　今の状態

> **実行先：VM 230**

⟦C12⟧

> **実行先：VM 220**

⟦C13⟧

構築時は、どちらも `active` で `disabled`（自動起動しない）でした。Relay は `After=wazuh-indexer.service` により、Indexer の後に起動します。

## 4.2　有効にする

> **実行先：VM 220**

⟦C14⟧

> **実行先：VM 230**

⟦C15⟧

どちらも `enabled` と表示されれば完了です。動いているサービスには影響しません。

# 第5章　Proxmoxの起動順序

VM 220（Wazuh と Relay）が、VM 230（AI Defense Manager）より先に起動するようにします。

## 5.1　今の設定

> **実行先：pve**

⟦C16⟧

構築時は、VM 220 は `onboot: 1`（自動起動）で順番は未設定、VM 230 は自動起動も順番も未設定でした。

## 5.2　順番を決める

動いている VM は止めません。

- VM 220：自動起動、順番1、起動してから次の VM まで120秒待つ
- VM 230：自動起動、順番2

⟦C17⟧

⟦C18⟧

⟦C19⟧

構築時の結果は次のとおりです。

| 項目 | VM 220 security-core | VM 230 ai-defense-manager |
|---|---|---|
| `onboot` | `1` | `1` |
| `startup` | `order=1,up=120` | `order=2` |

# おわりに

第17部で、次の状態になりました。

| 対象 | 状態 |
|---|---|
| `ai-defense-manager.service`（VM 230） | 稼働中・自動起動、`127.0.0.1:8000` |
| `ai-defense-relay.service`（VM 220） | 稼働中・自動起動、`192.168.0.220:8765` |
| Proxmox の起動順 | VM 220 → 120秒待つ → VM 230 |

次の部では、AI の分析の結果を記録として残す仕組みを作ります。

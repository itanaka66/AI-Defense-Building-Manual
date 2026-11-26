---
title: "AI自律型サイバー防御システム 構築マニュアル 第4巻"
subtitle: "第51部　VM 230からRelayへのTLSと認証を確かめる"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」第4巻の第51部です。第50部で、VM 230 を固定のアドレス `192.168.0.221` にし、VM 220 の Relay の許可するクライアントを直しました。ここでは、実際にアラートを取る前に、VM 230 から VM 220 の Relay への接続の条件を確かめます。

1. VM 230 の接続先の設定と、VM 220 の Relay の HTTPS の実装を確かめる
2. Relay のサーバーの証明書が `192.168.0.220` に合っていること、VM 230 が信頼する CA で署名されていることを確かめる
3. Indexer に問い合わせない `/health` を使って、TLS・接続元の IP の制限・Bearer の認証を1回だけ試す

秘密の鍵・Bearer のトークン・Indexer の認証の情報は表示しません。

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **VM 230**：ai-defense-manager（root）
  - **VM 220**：security-core（root）

# 第1章　接続の設定と HTTPS の実装

## 1.1　VM 230 の接続先

> **実行先：VM 230**

⟦C0⟧

| 項目 | 結果 |
|---|---|
| Relay の URL | `https://192.168.0.220:8765/` |
| 経路 | VM 230 `.221` → VM 220 `.220` |
| 認証 | Bearer のトークン |
| TLS の証明書の検証 | 有効（`verify=str(ca_file)`） |

VM 230 の側に、古いアドレス `.33` は残っていませんでした。

## 1.2　Relay の HTTPS の実装

> **実行先：VM 220**

⟦C1⟧

Relay は TLS 1.2 以上を必須とする HTTPS のサーバーで、サーバーの証明書と秘密の鍵を systemd の credentials から読み込んでいました。

# 第2章　証明書と CA を確かめる

## 2.1　サーバーの証明書

公開されている情報だけを見ます。

> **実行先：VM 220**

⟦C2⟧

| 項目 | 結果 |
|---|---|
| SAN | `IP Address:192.168.0.220` |
| 発行者 | `AI-Defense-Relay-Internal-CA` |
| 有効期間 | 2026年11月20日〜2029年2月22日 |

## 2.2　VM 230 が信頼する CA

> **実行先：VM 230**

⟦C3⟧

VM 230 は、内部の CA の証明書を `/etc/ai-defense-manager/credentials/relay-ca.crt` から読み込み、TLS の検証は無効にしていません。

> **実行先：VM 230**

⟦C4⟧

| 項目 | 状態 |
|---|---|
| CA の証明書 | あり、読める。発行者は `AI-Defense-Relay-Internal-CA` |
| API のトークン | あり（中身は表示しない） |
| 認証のディレクトリ | `root:ai-defense`・`750` |
| CA・トークンのファイル | `root:ai-defense`・`640` |

VM 230 の CA の証明書の SHA-256 のフィンガープリントは次のとおりでした。

⟦C5⟧

## 2.3　VM 220 の CA の元のファイル

> **実行先：VM 220**

⟦C6⟧

VM 220 の credentials の `indexer-ca` は Wazuh Indexer 用で、Relay 用の CA ではありませんでした。Relay 用の CA の元のファイルを探します。

> **実行先：VM 220**

⟦C7⟧

Relay 専用の CA は `/etc/credstore/ai-defense-relay-ca` にありました。

## 2.4　フィンガープリントと署名を照らし合わせる

> **実行先：VM 220**

⟦C8⟧

| 確かめたこと | 結果 |
|---|---|
| VM 220 の CA の SHA-256 | `71:E8:CE:68:…:84:61:54` |
| VM 230 の CA の SHA-256 | 同じ |
| CA の Subject | `AI-Defense-Relay-Internal-CA` |
| CA によるサーバーの証明書の検証 | `OK` |
| サーバーの証明書の SAN | `192.168.0.220` |
| TLS の最低のバージョン | TLS 1.2 |

発行者の名前が同じというだけでなく、暗号の上でも信頼の関係が正しいことを確かめました。

# 第3章　`/health` で試す

## 3.1　Indexer に問い合わせないエンドポイント

`/v1/alerts` を呼ぶと Wazuh Indexer に問い合わせます。まず、問い合わせないエンドポイントがあるかを確かめます。

> **実行先：VM 220**

⟦C9⟧

Relay の処理の順は次のとおりで、`/health` なら Indexer に問い合わせる前に `200 OK` を返します。

1. 接続元の IP アドレスが `192.168.0.221` であることを確かめる
2. Bearer のトークンを確かめる
3. `/health` なら `200 OK` を返して終わる
4. `/v1/alerts` のときだけ Wazuh Indexer に問い合わせる

## 3.2　TLS と Bearer の認証の試験

CA の証明書の検証と Bearer の認証を有効にし、トークンはファイルから読んでメモリの上だけで使います。

> **実行先：VM 230**

⟦C10⟧

| 確かめたこと | 結果 |
|---|---|
| CA の証明書の読み込み | 合格 |
| TLS の証明書の検証 | 合格 |
| 接続元の IP の制限 | 合格（200 の応答） |
| Bearer の認証 | 合格 |
| Relay の `/health` | `HTTP 200` |
| Wazuh Indexer・PostgreSQL・Ollama へのアクセス | なし |

# おわりに

第51部で、VM 230 から VM 220 の Relay への安全な HTTPS の経路ができていることを確かめました。

| 項目 | 結果 |
|---|---|
| 接続先 | `https://192.168.0.220:8765/`（TLS 1.2 以上） |
| サーバーの証明書 | SAN `192.168.0.220`、`AI-Defense-Relay-Internal-CA` で署名 |
| CA | VM 220 `/etc/credstore/ai-defense-relay-ca` と VM 230 `relay-ca.crt` が同じ |
| 認証 | 接続元の IP（`192.168.0.221`）と Bearer のトークン |
| `/health` | `HTTP 200` |

次の第52部では、実際の Wazuh のアラートを1回だけ取ります。

---
title: "AI自律型サイバー防御システム 構築マニュアル 第4巻"
subtitle: "第64部　FSSの封印を動かして確かめる"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」第4巻の第64部です。第62部で FSS の鍵を作り、第63部で検証の鍵を Proxmox のホストに移しました。ここでは、journald に封印を始めさせ、検証の鍵で確かめます。

1. journald を再起動し、封印の状態を確かめる
2. 封印のタグ（`Tag objects`）が0のままだった理由を調べる
3. journal を切り替えて（`journalctl --rotate`）新しいファイルを作り、封印されることを確かめる
4. 検証の鍵で、封印した journal を暗号の上で確かめる

ログの削除・容量の整理・鍵の変更はしません。

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **VM 230**：ai-defense-manager（root）

# 第1章　journald を再起動する

## 1.1　再起動と封印の状態

VM 230 の journald だけを1回再起動します。

> **実行先：VM 230**

⟦C0⟧

再起動は成功しましたが、すべての journal のファイルで `Tag objects` は `0` でした。

## 1.2　時間をおいて確かめる

> **実行先：VM 230**

⟦C1⟧

再起動から約43分たっても、`Tag objects` は `0` のままでした。journald は `active (running)`・`NRestarts=0` で、FSS の鍵のファイルもあり（`root:systemd-journal`・`600`）、FSS に関係するエラーもありませんでした。systemd は `+GCRYPT` 付きで作られ、journald に `libgcrypt` も読み込まれていました。

> **参考：** 鍵を作るときの `--interval=15min` は、封印の鍵を変える間隔で、タグを書く間隔ではありません。また、`journalctl --verify --verify-key=…` は、FSS を使っていない journal でもふつうの整合性の検査が通れば `PASS` を返すことがあるので、`PASS` だけでは FSS が動いている証拠になりません。

# 第2章　タグが0だった理由

> **実行先：VM 230**

⟦C2⟧

| 項目 | 時刻（UTC） |
|---|---|
| いまの `system.journal` を作った | 11月23日 20:40:55 |
| FSS の鍵のファイルを作った | 11月24日 00:03:37 |
| journald を再起動した | 11月24日 00:50:23 |
| いまの journal の最後の更新 | 11月24日 01:40:03 |

いまの `system.journal` は、**FSS の鍵を作るより約3時間23分前からあったファイル**で、journald を再起動しても、そのファイルを使い続けていました。FSS に対応する印（`SEALED`）は、新しいファイルのヘッダーを作るときに付けられ、すでにあるファイルに後から付くことはありません。そこで、journal を切り替えて新しいファイルを作ります。

# 第3章　journal を切り替える

いまの journal のファイルを保管に回し（アーカイブ）、新しいファイルに切り替えます。ログは消えません。

> **実行先：VM 230**

⟦C3⟧

切り替えたあとの `system.journal` は次のとおりでした。

| 項目 | 結果 |
|---|---|
| `Compatible flags` | `SEALED SEALED_CONTINUOUS TAIL_ENTRY_BOOT_ID` |
| `Tag objects` | 7 |
| `State` | `ONLINE` |

**FSS が有効になり、実際にタグが作られています。** `user-1000` の journal は、このときは FSS に対応していませんでした。

# 第4章　検証の鍵で確かめる

封印されたいまの `system.journal` を、検証の鍵で確かめます（鍵の中身は表示しません）。

> **実行先：VM 230**

⟦C4⟧

| 確かめたこと | 結果 |
|---|---|
| journal の状態 | `ONLINE` |
| `SEALED`・`SEALED_CONTINUOUS` | ある |
| `Tag objects` | 7 |
| `journalctl --verify --verify-key` | `PASS`（終了コード `0`） |

出力は次のとおりでした。

⟦C5⟧

「final 13min … entries not sealed」は失敗ではありません。最後に封印した時刻のあとに足されたおよそ13分のログが、まだ封印の対象になっていないという意味で、次の封印で含まれます。

# おわりに

第64部で、VM 230 の journal の FSS の封印を動かし、暗号の上で確かめました。

| 項目 | 結果 |
|---|---|
| タグが0だった理由 | FSS の鍵より前に作った journal のファイルを使い続けていた |
| 対策 | `journalctl --rotate` で新しいファイルを作った |
| 封印 | `SEALED SEALED_CONTINUOUS`、`Tag objects` 7 |
| 検証 | `journalctl --verify --verify-key` が `PASS` |

ただし、この検証は VM 230 の中で行ったものです。VM 230 が乗っ取られた場合に備えて、次の第65部では、**VM 230 とは別のホストで**確かめます。

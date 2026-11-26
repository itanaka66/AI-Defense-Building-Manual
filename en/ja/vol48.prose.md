---
title: "AI自律型サイバー防御システム 構築マニュアル 第4巻"
subtitle: "第48部　Wazuhのイベントの変換を7項目に絞る"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」第4巻の第48部です。第47部で、AI Defense Manager（VM 230）の既存の実装を調べ、許可リストを入れる場所を決めました。ここでは実際にコードを変えます。

1. 変える前に、対象の5つのファイルを控える
2. テストを動かす環境と、モジュールの読み込みの経路を確かめる
3. 分類を `location`・`decoder.name` から `rule.groups` に変えるために、実際のグループの数を集計する
4. Python の構文の解析（AST）を使って、2つのファイル（`wazuh_relay.py`・`ai_analysis.py`）だけを書き換える
5. 合成したイベントで26件の単体テストを行い、差分を確かめる

Wazuh・Ollama への実際の通信、PostgreSQL・SQLite への書き込み、サービスの再起動はしません。

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **VM 230**：ai-defense-manager（root）
  - **VM 220**：security-core（root）

# 第1章　変える前にファイルを控える

`/var/backups/ai-defense-manager/` に日時ごとのディレクトリを作り、`cp -a` で所有者・権限・時刻を残したまま控え、SHA256 を元のファイルと比べます。

> **実行先：VM 230**

⟦C0⟧

5つのファイルすべての控えと SHA256 の照合が成功しました。控えの場所は `/var/backups/ai-defense-manager/20261123-031115` です。`wazuh_relay.py` などの `root:ai-defense`・`640` も残っています。

# 第2章　テストの環境を確かめる

## 2.1　Python とテストの道具

新しいパッケージは入れません。

> **実行先：VM 230**

⟦C1⟧

Python 3.12.3・FastAPI・Pydantic・HTTPX は使えますが、`pytest` は入っていませんでした。`pytest` は入れず、Python の標準の `unittest` を使います。

## 2.2　モジュールの読み込みの経路

> **実行先：VM 230**

⟦C2⟧

`/opt/ai-defense-manager` から既存のモジュールをすべて読み込め、`unittest` も使えました。サービスは `ai-defense` のユーザー・作業ディレクトリ `/opt/ai-defense-manager` で動いているので、テストもこの条件に合わせます。

## 2.3　いまの分類と要約の作り方

> **実行先：VM 230**

⟦C3⟧

いまの分類は `decoder.name` を先に使い、無ければ `location` を使っていました。`location` を除くと、`location` だけで分類されていたイベントが `other` になるおそれがあるので、分類は `rule.groups` を使うように変えます。

# 第3章　分類の設計

## 3.1　実際のグループを集計する

Wazuh の `alerts.json` は `wazuh:wazuh`・`640` なので、VM 220 の **root** で実行します（一般のユーザーでは `PermissionError` になります）。値は表示しません。

> **実行先：VM 220**

⟦C4⟧

| 項目 | 件数 |
|---|---:|
| 正しい JSON | 268 |
| 正しくない JSON | 0 |
| `rule.groups` が無い | 0 |
| `pam` | 228 |
| `proxmox-ve` | 16 |
| `sshd` | 1 |
| `sudo` | 3 |
| `postgresql` | 34 |
| `authentication_failed` | 4 |

グループは重ねて数えるので、合計はイベントの数と合いません。

## 3.2　分類とスキーマの互換性

> **実行先：VM 230**

⟦C5⟧

`event_category` は1〜64文字の文字列なので、分類を足しても Pydantic のスキーマは変えずに済みます。決めた分類は次のとおりです。複数の具体的なグループがあるときは、上の行を優先します。

| 優先 | Wazuh の `rule.groups` | 分類 |
|---:|---|---|
| 1 | `pvedaemon`・`proxmox-ve` | `virtualization_management` |
| 2 | `pam`・`authentication_success`・`authentication_failed` | `authentication` |
| 3 | `sshd` | `remote_access` |
| 4 | `sudo` | `privilege_escalation` |
| 5 | `useradd`・`open-userdel` | `account_management` |
| 6 | `postgresql` | `database` |
| 7 | その他 | `other` |

`syslog`・`local`・`error`・`access_control` のような一般的なグループだけでは、具体的な分類にしません。

## 3.3　入力の境目

> **実行先：VM 230**

⟦C6⟧

`SecurityEvent` と `AIAnalysisRequest` は `extra='forbid'`（知らない項目を拒む）になっていて、よい作りです。ただし `/api/v1/analysis` は Wazuh 専用ではなく、Prometheus などからの入力も受けます。そこで、

- **Wazuh に固有の制約は、Wazuh の取得（`wazuh_relay.py`）で行う**
- **AI に送るところでは、すべてのイベントに共通の、許可した項目だけを送る方式にする**

ことにします。

# 第4章　2つのファイルを書き換える

## 4.1　変える前の最後の確認

> **実行先：VM 230**

⟦C7⟧

3つのファイルの SHA256 は控えと一致しました。

## 4.2　関数の定義を読む

`analyze_events` の定義は複数の行に分かれていて、1行の文字列で探す置き換えでは見つかりません。実際の定義と、AI に送る部分を読みます。

> **実行先：VM 230**

⟦C8⟧

⟦C9⟧

## 4.3　AST で書き換える

正規表現による広い置き換えはやめ、Python の構文の解析の結果を使って、関数の本体と、イベントの一覧を作る部分だけを置き換えます。2つのファイルの変更の案を**両方とも構文の検査に通してから書き込みます**。API・スキーマ・伏せ字の処理（`event_sanitizer.py`）は変えません。

> **実行先：VM 230**

⟦C10⟧

> **注意：** このスクリプトは、控えのディレクトリと、3つのファイルの変える前の SHA256（構築したときの値）を確かめてから書き換えます。値が合わないときは何も書かずに止まります。自分の環境で使うときは、第1章で控えたときの値に合わせてください。

| ファイル | 変えたこと |
|---|---|
| `wazuh_relay.py` | 7項目の入力を確かめる。`rule.groups` で分類する。`agent.name`・`location`・`decoder.name` を使わない |
| `ai_analysis.py` | AI に送る内容を6項目だけで組み立てる（`_build_event_payload()`）。Wazuh のイベントの分類と禁止した項目を確かめる |
| `event_sanitizer.py` | 変えていない |

構文の検査はすべて合格し、サービスの再起動・通信・DB への接続はしていません。

# 第5章　合成したイベントで試す

## 5.1　26件の単体テスト

実際の Wazuh のイベントの取得、LLM の呼び出し、DB への書き込みはしません。

> **実行先：VM 230**

⟦C11⟧

**26件すべて合格**（失敗・エラーは0件）でした。

- 6つの具体的な分類と、その優先の順
- 一般的なグループは `other` になる
- 正しくない時刻・タイムゾーン・重大度・ID・グループを拒む
- `agent.name`・IP・`full_log`・`data` などの余分な項目を無視する
- AI に送る内容が、許可した6項目だけになる
- Wazuh のイベントの正しくない分類・禁止した項目を拒む
- ほかの入力元の分類の制約は変わっていない
- 合成した IP・パスワードが伏せ字になる

3つのファイルの SHA256 は、テストの前後で同じでした。

## 5.2　差分を確かめる

> **実行先：VM 230**

⟦C12⟧

`wazuh_relay.py` と `ai_analysis.py` の差分は意図した範囲で、`event_sanitizer.py` は控えと完全に一致しました。`_build_event_payload()` を呼ぶところは1か所です。`diff` の終了コード `1` は差分があることを表し、エラーではありません。

## 5.3　Relay から受け取る形

> **実行先：VM 230**

⟦C13⟧

`fetch_wazuh_events()` は Relay の `GET /v1/alerts` にアクセスし、JSON の `alerts` の配列の各要素を `_convert_alert()` に渡します。各要素は、次のような**ドットで区切った平らな形**です。

⟦C14⟧

新しい `_convert_alert()` は `rule.groups` を必須にしています。Relay がこの項目を返しているかを、次の第49部で確かめます。

# おわりに

第48部で、Wazuh のイベントの変換を7項目に絞り、AI に送る内容を6項目に固定しました。

| 項目 | 結果 |
|---|---|
| 控え | `/var/backups/ai-defense-manager/20261123-031115`（5つ、SHA256 一致） |
| 分類 | `rule.groups` を使う7分類（優先の順あり） |
| 変えたファイル | `wazuh_relay.py`・`ai_analysis.py`（AST で書き換え、構文の検査に合格） |
| 単体テスト | 26件すべて合格 |
| サービス | 再起動していない（まだ古いコードで動いている） |

次の第49部では、VM 220 の Relay が `rule.groups` を返すように直します。

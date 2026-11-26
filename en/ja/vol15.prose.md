---
title: "AI自律型サイバー防御システム 構築マニュアル 前編"
subtitle: "第15部　Relayの接続情報をVM 230へ安全に渡す"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」前編の第15部です。第14部で security-core（VM 220）に作った中継API（Relay）を、AI Defense Manager（VM 230）から使えるようにします。

VM 230 が Relay を呼ぶには、次の2つが必要です。

- Relay の CA 証明書（サーバー証明書を検証するため）
- Bearer トークン（秘密の情報）

この2つを、root の SSH ログインを有効にせずに、**SFTP だけを使える一時的な転送専用アカウント**で VM 220 から VM 230 へ運びます。運び終わったら、転送用のアカウントと設定はすべて撤去します。

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **VM 220**：security-core（root）
  - **VM 230**：ai-defense-manager（root）
- トークンや秘密鍵の中身は、画面にもマニュアルにも出しません。

# 第1章　VM 230の受け取り先

## 1.1　設定用のディレクトリ

> **実行先：VM 230**

⟦C0⟧

構築時は `/etc/ai-defense-manager` がまだありませんでした。アプリ本体（`/opt/ai-defense-manager`）と分けて、接続情報を置くディレクトリを作ります。

⟦C1⟧

## 1.2　実行ユーザーの確認

AI Defense Manager を動かす専用ユーザー `ai-defense` を確かめます。

⟦C2⟧

⟦C3⟧

構築時は、ユーザー `ai-defense`（UID 999）、グループ `ai-defense`（GID 988）、ホーム `/opt/ai-defense-manager`、シェル `/usr/sbin/nologin` でした。

## 1.3　接続情報のディレクトリ

`root:ai-defense` の `750` にし、実行ユーザーだけが読めるようにします。

⟦C4⟧

# 第2章　SSHのホスト鍵を確かめる

VM 230 から VM 220 へ SSH（SFTP）でつなぐ前に、VM 220 のホスト鍵を別の経路で確かめてから登録します。`StrictHostKeyChecking=no` で確認を省くことはしません。

## 2.1　VM 220で指紋を表示

> **実行先：VM 220**

⟦C5⟧

## 2.2　VM 230で取得した鍵と照らし合わせる

> **実行先：VM 230**

⟦C6⟧

2.1 で表示した ED25519 の指紋（`SHA256:...`）と一致することを確かめます。一致したら、`known_hosts` に登録します。

⟦C7⟧

VM 230 には、ほかに使える SSH 公開鍵がないことも確かめます。

⟦C8⟧

# 第3章　転送専用のアカウント

## 3.1　専用ユーザー

> **実行先：VM 220**

⟦C9⟧

ログインできず、パスワードもロックしたユーザーを作ります。転送に使うのは、chroot の中の `incoming` だけです。

⟦C10⟧

今の SSH の設定を確かめます。

⟦C11⟧

公開鍵の登録先を作ります。

⟦C12⟧

## 3.2　転送専用の鍵

> **実行先：VM 230**

既存の鍵は使わず、この転送だけに使う Ed25519 の鍵を作ります。

⟦C13⟧

公開鍵だけを表示します（秘密鍵は表示しません）。

⟦C14⟧

## 3.3　公開鍵の登録

> **実行先：VM 220**

3.2 で表示した公開鍵を登録します。次のコマンドの公開鍵は構築時のものです。**自分の環境で表示された公開鍵の行に置き換えてください。**

⟦C15⟧

## 3.4　SSHの設定

> **実行先：VM 220**

⟦C16⟧

`ai-defense-transfer` だけに効く `Match` ブロックを末尾に足します。ほかのユーザーの設定は変えません。

- `ChrootDirectory`：`/srv/ai-defense-transfer` から出られない
- `ForceCommand internal-sftp`：SFTP だけ。シェルは使えない
- 公開鍵の認証だけ。パスワードは使えない
- ポートの転送・エージェントの転送・X11・トンネルは禁止

⟦C17⟧

⟦C18⟧

VM 230 から接続したときに実際に効く値を確かめます。

⟦C19⟧

chroot のディレクトリは、root の持ち物で書き込みできないことが必要です。

⟦C20⟧

⟦C21⟧

再起動ではなく reload（設定の読み直し）で反映します。つながっている SSH は切れません。

⟦C22⟧

## 3.5　公開鍵ファイルの権限

構築時は、この状態で VM 230 から SFTP でつなぐと公開鍵の認証で拒否されました。VM 220 の SSH のログには、公開鍵のファイルを開けないという記録（`Could not open user 'ai-defense-transfer' authorized keys ... Permission denied`）がありました。

⟦C23⟧

`AuthorizedKeysFile` は、そのユーザーの権限で読まれます。`root:root` の `600` では `ai-defense-transfer` が読めないため、グループを `ai-defense-transfer` にして `640` にします。

> **実行先：VM 220**

⟦C24⟧

## 3.6　SFTPの接続確認

> **実行先：VM 230**

⟦C25⟧

エラーが出ずに終われば、接続できています。

# 第4章　CA証明書とトークンを運ぶ

## 4.1　転送用の場所に置く

> **実行先：VM 220**

⟦C26⟧

## 4.2　VM 230で受け取る

> **実行先：VM 230**

⟦C27⟧

受け取ったファイルを `root:ai-defense` の `640` で配置し、`/root` に残ったものは消します。

⟦C28⟧

## 4.3　CA証明書が同じものか確かめる

> **実行先：VM 230**

⟦C29⟧

> **実行先：VM 220**

⟦C30⟧

両方の `subject`（`CN = AI-Defense-Relay-Internal-CA`）と SHA256 の指紋が一致すれば、正しく運べています。

# 第5章　VM 230からRelayを呼ぶ

## 5.1　/health

> **実行先：VM 230**

トークンの値は表示せずに、HTTPS・CA の検証・Bearer の認証を確かめます。

⟦C31⟧

構築時の結果は `HTTP_STATUS: 200`、`RESPONSE: {"status": "ok"}` でした。

## 5.2　/v1/alerts

直近60分のアラートを5件取り、返ってきた項目の名前だけを表示します。

⟦C32⟧

構築時は5件が返り、各アラートの項目は `agent.id`、`agent.name`、`decoder.name`、`location`、`manager.name`、`rule.description`、`rule.id`、`rule.level`、`timestamp` でした。Relay は項目を `rule.level` のような「点でつないだ名前」のまま平らに返すため、`RULE_FIELDS` と `AGENT_FIELDS` は空になります。値がない項目（この時は `agent.ip`）は返しません。

# 第6章　転送用のアカウントを撤去する

運び終わったので、一時的な転送の仕組みをすべて片付けます。

## 6.1　SSHの設定を元に戻す

> **実行先：VM 220**

⟦C33⟧

バックアップを取ってから、3.4 で足した `Match` ブロックを取り除きます。

⟦C34⟧

⟦C35⟧

## 6.2　ユーザーとファイルの削除

転送用のセッションが残っていないことを確かめます。

⟦C36⟧

⟦C37⟧

構築時は `userdel` がグループもいっしょに消したため、`groupdel: group 'ai-defense-transfer' does not exist` が出て、その後の `rm -rf` は実行されませんでした。状態を確かめ、残ったディレクトリを消します。

⟦C38⟧

⟦C39⟧

## 6.3　Relayが動き続けていることの確認

⟦C40⟧

`active` で、`192.168.0.220:8765` で待ち受けていれば完了です。

# おわりに

第15部で、VM 230 に次の接続情報を置きました。

| ファイル（VM 230） | 権限 | 中身 |
|---|---|---|
| `/etc/ai-defense-manager/credentials/relay-ca.crt` | `root:ai-defense 640` | Relay の CA 証明書 |
| `/etc/ai-defense-manager/credentials/relay-api.token` | `root:ai-defense 640` | Bearer トークン |

転送用のユーザー・鍵の登録・SSH の設定・ディレクトリは撤去しました（VM 230 の `/root/.ssh/ai-defense-transfer` の鍵は残っています）。また、Relay のサービスはこの時点で自動起動（`enable`）を設定していません。

次の部では、AI Defense Manager に Relay から取ったアラートを取り込み、AI の分析につなげます。

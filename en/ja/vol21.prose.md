---
title: "AI自律型サイバー防御システム 構築マニュアル 前編"
subtitle: "第21部　VM 230のSSHを公開鍵認証に切り替える"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」前編の第21部です。第20部の点検で、AI Defense Manager（VM 230）の SSH はパスワードでログインできる状態だとわかりました。ここでは、管理に使っている Windows の PC にある既存の鍵を使って公開鍵認証に切り替え、そのあとでパスワードの認証と root の SSH ログインを禁止します。

SSH の設定を間違えると、VM に入れなくなるおそれがあります。次のことを守って進めます。

- 作業のあいだ、VM 230 の root のコンソール（Proxmox のコンソールなど）を閉じない
- 公開鍵でログインできることを確かめてから、パスワードの認証を止める
- 設定を変える前にバックアップを取る
- 再起動ではなく reload で反映する

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **VM 230**：ai-defense-manager（root のコンソール）
  - **Windows**：管理に使っている Windows の PC（PowerShell）
- 秘密鍵の中身は、画面にもチャットにも出しません。公開鍵の指紋（フィンガープリント）は秘密の情報ではありません。
- 構築時の Windows のユーザーのフォルダーは `C:\Users\HP ELITEBOOK` です。自分の環境に読み替えてください（コマンドの多くは `$env:USERPROFILE` を使っているので、そのまま使えます）。

# 第1章　今のSSHの状態

> **実行先：VM 230**

⟦C0⟧

構築時の値は次のとおりです。

| 設定 | 値 |
|---|---|
| `permitrootlogin` | `without-password`（root は公開鍵ならログインできる） |
| `pubkeyauthentication` | `yes` |
| `passwordauthentication` | `yes`（変えたい） |
| `kbdinteractiveauthentication` | `no` |
| `authenticationmethods` | `any` |

今のシェルが SSH 経由かどうかを確かめます。

⟦C1⟧

構築時は両方とも空で、VM のコンソールから入った root のシェルでした。

⟦C2⟧

パスワードの認証を明示的に有効にしているのは `/etc/ssh/sshd_config.d/50-cloud-init.conf` の1行（`PasswordAuthentication yes`）だけでした。

⟦C3⟧

構築時のログでは、ログインはすべてパスワードの認証でした。今の管理の接続はパスワードに頼っているので、すぐには止められません。

## 1.1　公開鍵の登録の状態

⟦C4⟧

⟦C5⟧

⟦C6⟧

権限（ホーム 750、`.ssh` 700、`authorized_keys` 600）は正しいものの、`authorized_keys` は **0バイト（空）** でした。公開鍵はまだ登録されていません。

# 第2章　Windowsにある鍵を確かめる

## 2.1　鍵のファイル

> **実行先：Windows**（PowerShell）

⟦C7⟧

構築時は、PuTTY 形式の秘密鍵 `rsa_private.ppk` と、公開鍵 `rsa_public` がありました。

⟦C8⟧

`rsa_public` は、OpenSSH の形式ではなく RFC4716 形式（SSH2 の公開鍵の形式）でした。秘密鍵は変えずに、公開鍵だけを OpenSSH の形式に変換します。

⟦C9⟧

構築時は RSA 4096 ビットで、指紋は `SHA256:4dkitn2a46fogsJbEepnpQygeqyBXDFEtqkVylty0y0` でした。

## 2.2　PuTTYgen

`.ppk` は PuTTY 独自の形式で、Windows 標準の `ssh-keygen` では読めません。PuTTYgen を使うため、PuTTY を入れます（管理者の PowerShell）。

⟦C10⟧

構築時の PuTTY 0.85（Windows 版）では、PuTTYgen のコマンドラインの `-O` オプションが使えなかったため、GUI で操作します。

⟦C11⟧

1. **Load** を押し、`C:\Users\HP ELITEBOOK\.ssh\rsa_private.ppk` を読み込みます（パスフレーズがあれば入力）。
2. 表示される **Key fingerprint** が、2.1 の指紋と一致することを確かめます。

⟦C12⟧

一致すれば、`rsa_private.ppk` と `rsa_public` は同じ鍵のペアです。

## 2.3　公開鍵を保存して変換する

PuTTYgen の **Save public key** を押し、次の名前で保存します。**Save private key は押しません。**

⟦C13⟧

保存した公開鍵を OpenSSH の形式に変換し、指紋を確かめます。

⟦C14⟧

期待する指紋は次のとおりです。

⟦C15⟧

# 第3章　VM 230に公開鍵を登録する

## 3.1　公開鍵を送る

> **実行先：Windows**

送るのは公開鍵だけです。パスワードをたずねられたら、VM 230 の `aidefense` のパスワードを入れます（この時点ではまだパスワードでつながります）。

⟦C16⟧

## 3.2　指紋を確かめて登録する

> **実行先：VM 230**

⟦C17⟧

Windows 側と同じ指紋であることを確かめます。`authorized_keys` は空だったので、この公開鍵で置き換えます。

⟦C18⟧

⟦C19⟧

指紋が一致し、`aidefense:aidefense` の `600`、`.ssh` が `700` であれば正常です。

# 第4章　公開鍵でログインする

## 4.1　秘密鍵をOpenSSHの形式で書き出す

Windows 標準の `ssh` は `.ppk` を読めません。元の `.ppk` は変えずに、PuTTYgen の GUI で OpenSSH の形式の秘密鍵を書き出します。

1. PuTTYgen で **Load** を押し、`rsa_private.ppk` を読み込みます。
2. メニューの **Conversions** から **Export OpenSSH key** を選びます。
3. 次の名前で保存します（パスフレーズを求められたら設定・入力します）。

⟦C20⟧

この `rsa_private_openssh` は秘密鍵です。中身を人に見せたり送ったりしないでください。

> **実行先：Windows**

中身は表示せず、ファイルがあることと指紋だけを確かめます。

⟦C21⟧

## 4.2　公開鍵だけでログインする

パスワードの認証を使わない指定で接続します。

⟦C22⟧

パスワードをたずねられずに `aidefense@ai-defense-manager:~$` が表示されれば成功です。

# 第5章　パスワードの認証とrootのログインを止める

## 5.1　設定の読み込みの順番

> **実行先：VM 230**

⟦C23⟧

⟦C24⟧

`/etc/ssh/sshd_config` は `sshd_config.d/*.conf` を読み込み、その中の `50-cloud-init.conf` が `PasswordAuthentication yes` を指定しています。OpenSSH は、同じ項目が何度か出てくると、原則として**最初に読んだ値**を使います。そこで、`50-cloud-init.conf` より先に読まれる `00-local-hardening.conf` を新しく作ります。`50-cloud-init.conf` は変えません。

## 5.2　バックアップ

⟦C25⟧

⟦C26⟧

⟦C27⟧

## 5.3　設定ファイル

| 設定 | 今 | 変更後 |
|---|---|---|
| `PermitRootLogin` | `without-password` | `no` |
| `PasswordAuthentication` | `yes` | `no` |
| `PubkeyAuthentication` | `yes` | `yes` |
| `KbdInteractiveAuthentication` | `no` | `no` |

⟦C28⟧

⟦C29⟧

⟦C30⟧

reload の前に、実際に効く値を確かめます。

⟦C31⟧

⟦C32⟧

## 5.4　反映

reload は SSH を再起動せず、設定だけを読み直します。root のコンソールと、Windows からの接続はそのまま残しておきます。

⟦C33⟧

⟦C34⟧

`active (running)` であれば反映できています。

## 5.5　新しい接続で確かめる

> **実行先：Windows**（新しい PowerShell の画面）

⟦C35⟧

このコマンドは、必ず Windows の PowerShell（`PS C:\Users\...>`）で実行します。構築時は、VM 230 にログインしたままの画面（`aidefense@ai-defense-manager:~$`）で実行してしまい、`$env:USERPROFILE` が使えずに失敗しました。その場合は `exit` で Windows に戻ってから実行します。

パスワードをたずねられずに次のプロンプトが出れば完了です。

⟦C36⟧

# 第6章　SSHのログの点検

> **実行先：VM 230**

⟦C37⟧

構築時は、切り替える前のパスワードでのログインが6回、存在しないユーザー名（`aidefence`、つづりの間違い）でのログインの失敗が1回、切り替えた後の公開鍵でのログインが2回ありました。切り替えた後に、パスワードでのログインの成功はありません。

# おわりに

第21部で、VM 230 の SSH を次の状態にしました。

| 項目 | 状態 |
|---|---|
| 公開鍵の認証 | 有効（Windows の既存の RSA 4096 ビットの鍵） |
| パスワードの認証 | 無効 |
| root の SSH ログイン | 禁止 |
| キーボード対話の認証 | 無効 |
| 設定ファイル | `/etc/ssh/sshd_config.d/00-local-hardening.conf` |
| バックアップ | `/root/ssh-config-backup-20261121` |

次の部では、Relay と Wazuh Indexer の設定と権限を点検します。

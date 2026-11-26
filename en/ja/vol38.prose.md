---
title: "AI自律型サイバー防御システム 構築マニュアル 後編"
subtitle: "第38部　TrueNASをバックアップの保存先にする"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」後編の第38部です。第37部で、LXC 109（PostgreSQL）のバックアップと復元を試しましたが、バックアップの置き場所（`local`）は本番と同じ NVMe の上でした。ここでは次のことを行います。

1. LVM-thin（`pve/data`）の容量と自動の拡張の設定を、読み取りだけで調べる
2. **TrueNAS**（VM 100、192.168.0.254）の NFS の共有 `/mnt/backup` を、Proxmox から使えるようにする
3. 書き込めなかった原因（NFS の root の割り当て）を調べ、書き込めることを確かめる

TrueNAS は、Proxmox の `RAID_A` と `RAID_B` から約2TB の仮想ディスクを1台ずつ受け取り、ミラーにしています。中は空で、バックアップに使ってよいことにしました。TrueNAS の画面や Shell には入らず、Proxmox のホストから確かめます（TrueNAS の設定を変える操作だけは、TrueNAS の側で行いました）。

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **pve**：Proxmox のホスト（root）

# 第1章　LVM-thin の容量

## 1.1　thin pool と自動の拡張

> **実行先：pve**

⟦C0⟧

本番の LXC 109 がある `pve/data` は、データ 61.66%・メタデータ 2.18% で、VG `pve` の空きは 16GiB でした。`lvm.conf` の `thin_pool_autoextend_threshold` と `thin_pool_autoextend_percent` はコメントのままです。

⟦C1⟧

`lvm2-monitor` と `dmeventd` は動いていて、`pve/data` は見張られています（`monitored`）。ただし、自動の拡張の値は設定されていません（`Configuration node … not found`）。見張られていることと、自動で広げることは別です。

## 1.2　広げる余地

⟦C2⟧

Proxmox のディスクは NVMe（FIKWOT FN950 1TB）で、パーティション3はディスクの最後まで使っています。同じ NVMe の中に空いた場所はなく、VG の空きは 16GiB だけです。自動の拡張を有効にしても、物理的な容量の不足は解決しないため、**自動の拡張の設定は変えずに保留します**。

⟦C3⟧

`pve/data` は 794.30GiB で、使っているのは約 489.6GiB、残りは約 304.7GiB です。いますぐ容量が足りなくなる状態ではありません。

## 1.3　バックアップの置き場所とジョブ

⟦C4⟧

ルート（`local`）は 94GiB のうち 24GiB を使い、空きは 66GiB、`/var/lib/vz/dump` は 1.4GiB（バックアップ3つ）でした。`pvesm status` は、次のエラーを出して終了コード5になりますが、`local` と `local-lvm` は `active` です（このエラーは別の問題として扱います）。

⟦C5⟧

⟦C6⟧

`/etc/vzdump.conf` はすべてコメントで、定期のバックアップのジョブは `[]`（0件）でした。

# 第2章　TrueNAS に NFS でつなぐ

## 2.1　TrueNAS の VM

⟦C7⟧

| TrueNAS の中 | Proxmox の側 | 大きさ |
|---|---|---:|
| SCSI1 | `RAID_A` | 2,018G |
| SCSI2 | `RAID_B` | 2,018G |

> **注意**：TrueNAS は、同じ Proxmox のホストの上の VM です。Proxmox の NVMe が壊れたときの備えにはなりますが、ホストごと壊れたときの備え（別の筐体へのバックアップ）にはなりません。

## 2.2　つながるか

TrueNAS の IP アドレスは 192.168.0.254 です。

⟦C8⟧

4つとも返ってきました（約0.3〜0.7ms）。

## 2.3　共有の方式

TrueNAS には AFP・iSCSI・NFS・WebDAV・SMB の共有がありますが、Proxmox のバックアップの保存先には **NFS** を使います。

| 方式 | 向き・不向き |
|---|---|
| NFS | Linux どうしのファイルの共有に向き、Proxmox の保存先にそのまま使える |
| SMB | 使えるが、Windows との共有向け |
| iSCSI | ブロックのデバイスとしてつなぐ方式で、ファイルのバックアップには複雑 |
| WebDAV | Web 向けで、Proxmox の保存先には向かない |
| AFP | Apple の古い方式で、新しく選ぶ理由がない |

⟦C9⟧

⟦C10⟧

`/mnt/backup` が共有されていました。`(everyone)` は共有の範囲で、書き込めるかどうかまではわかりません。

## 2.4　NFS のクライアントとサーバー

⟦C11⟧

`mount.nfs` と `nfsstat` があり、NFS のマウントはまだありませんでした。

⟦C12⟧

TrueNAS は NFSv3（TCP 2049、mountd は TCP 708）で答えていました。NFSv3 を使います。

## 2.5　マウントの場所

⟦C13⟧

⟦C14⟧

`/mnt/pve` の下にマウントはなく、`/mnt/pve/backup` というディレクトリがすでにありました。中を確かめます。

⟦C15⟧

空でした。ここを NFS のマウントの場所に使います。

# 第3章　読み取り専用でマウントする

## 3.1　1回目

まず、読み取り専用（`ro`）でマウントして、中を確かめます。

⟦C16⟧

次のエラーでマウントできませんでした。

⟦C17⟧

## 3.2　原因を探す

⟦C18⟧

メモリは約 96GiB 空いていて（使えるのは約 119GiB）、カーネルに NFS のエラーもありませんでした。ほかにも、NFS のカーネルのモジュール（`nfs`・`nfsv3`・`sunrpc`・`lockd`）、`rpc_pipefs`（`/run/rpc_pipefs` にマウント済み）、パッケージ（`nfs-common` 2.6.2）、スラブのメモリ、メモリの圧迫や OOM の記録も調べましたが、どれも正常でした。

⟦C19⟧

TrueNAS へは `vmbr0`（送信元 192.168.0.240）を通り、2049 と 708 はどちらも `open` でした。TrueNAS は動いているため、再起動はしません。

## 3.3　もう一度試す

構築時は、もう一度試す前に承認を取りました。詳しい表示（`-v`）を付けて試すと、`mount(2): Cannot allocate memory` で同じように失敗しました。そこで、`strace` でシステムコールを記録しながら試します（記録は `/tmp` に置きます）。

⟦C20⟧

今回は**マウントに成功しました**。

⟦C21⟧

⟦C22⟧

前の2回の `Cannot allocate memory` は、このときは起きませんでした。なぜ前は失敗したのかは、わかっていません。

⟦C23⟧

NFSv3・TCP でマウントされ、大きさは 1.9T、使っているのは 128K で、中は空でした。

# 第4章　書き込めるか

## 4.1　読み書きできるようにマウントし直す

構築時は、一時的な書き込みの試験をする前に承認を取りました。Proxmox の側のマウントだけを変え、TrueNAS の設定は変えません。

⟦C24⟧

`REMOUNT_EXIT=0` で、`rw` になりました。

## 4.2　1回目の書き込みの試験

試験のファイルを1つ作り、読み返してから消します。

⟦C25⟧

`Permission denied`（`WRITE_EXIT=1`）で、書き込めませんでした（ファイルはできていません）。

## 4.3　共有のディレクトリの持ち主

⟦C26⟧

共有のディレクトリは `root:root`（UID 0・GID 0）、`755`（持ち主だけが書ける）でした。Proxmox の root からのアクセスが、TrueNAS の側で別のユーザーに置き換えられている（NFS の root の割り当て）と考えられます。

# 第5章　TrueNAS の設定を Proxmox から読む

構築時は、TrueNAS の NFS の権限を調べて直すことの承認を取りました。TrueNAS の画面や Shell には入らず、Proxmox のホストから TrueNAS の API で読みます。

## 5.1　管理の入り口

⟦C27⟧

SSH（22）はつながらず、HTTP（80）と HTTPS（443）はつながりました。API は `401`（認証が要る）を返しました。

## 5.2　API の認証

TrueNAS の管理者のユーザー名とパスワードを、Proxmox の端末で入力します。パスワードは画面に出さず（`read -s`）、チャットなどにも貼りません。使い終わったら変数を消します。

⟦C28⟧

`HTTP_STATUS=200` で、TrueNAS は `TrueNAS-12.0-U8.1`（TrueNAS CORE 12）でした。

## 5.3　API の一覧

TrueNAS 12 の API の正しい道筋を、API の仕様（`/api/v2.0`）から調べます。

⟦C29⟧

OpenAPI 3.0.0 の仕様が取れ、NFS の共有は `/sharing/nfs`、NFS のサービスは `/nfs`、データセットは `/pool/dataset` でした。

## 5.4　NFS の設定と共有とデータセット

⟦C30⟧

| 項目 | 値 |
|---|---|
| NFS の共有（id 1） | `/mnt/backup` |
| `maproot_user` / `maproot_group` | `itanaka` / `itanaka`（UID・GID 1000） |
| データセット | `backup`（ACL は NFSv4、`readonly=OFF`） |

**原因がわかりました。** Proxmox の root からのアクセスは、TrueNAS の上では `itanaka` として扱われます。共有のディレクトリは `root:root`・`755` なので、`itanaka` では書き込めません。

> **メモ**：構築時は、所有者を `root:root` のままにして、`itanaka`（UID 1000）に書き込みの ACL を足すことも試しました。ところが TrueNAS CORE 12 は、プールのいちばん上のデータセット（`/mnt/backup`）の ACL を変えることを許さず（`root level dataset is not permitted`）、ACL は変わりませんでした。

# 第6章　root として書き込めるようにする

## 6.1　NFS の共有の設定を変える

TrueNAS の側で、NFS の共有 `/mnt/backup` の root の割り当て（Maproot）を変えました。共有のディレクトリの持ち主は `root:root` のままです。変えたあとの設定を、Proxmox から API で読みます。

この手順では、パスワードを `curl` のコマンドの引数に出さないよう、`chmod 600` の一時ファイルに入れて `--config` で渡し、終わったら消します。

> **実行先：pve**

⟦C31⟧

⟦C32⟧

Proxmox の root は、TrueNAS の上でも `root`（グループは `builtin_administrators`）として扱われるようになりました。

## 6.2　書き込みの試験

⟦C33⟧

⟦C34⟧

**Proxmox の root から TrueNAS の `/mnt/backup` に書き込めました。** 子のデータセットを作ったり、ACL を変えたりする必要はありません。

# おわりに

第38部で、TrueNAS をバックアップの保存先にする準備をしました。

| 項目 | 結果 |
|---|---|
| LVM-thin | `pve/data` は 61.66%。自動の拡張は未設定だが、VG の空きが 16GiB しかないため保留 |
| 定期のバックアップ | 0件（`vzdump.conf` も既定のまま） |
| 保存先 | TrueNAS（VM 100、192.168.0.254）の NFS `/mnt/backup`（1.9T、空） |
| マウント | NFSv3・TCP で `/mnt/pve/backup` に。初めの2回は `Cannot allocate memory`（原因不明）、3回目に成功 |
| 書き込めなかった原因 | NFS の root の割り当てが `itanaka` で、共有のディレクトリが `root:root`・`755` |
| 直したこと | TrueNAS の NFS の共有の Maproot を `root` / `builtin_administrators` に変えた |
| 書き込みの試験 | 成功（`root:root` で作れ、消せた） |

ただし、いまのマウントは手で行ったもので、Proxmox のストレージにもまだ登録していません。次の第39部では、起動のときに NFS が正しくマウントされるようにし、Proxmox にバックアップ専用のストレージとして登録して、定期のバックアップを準備します。

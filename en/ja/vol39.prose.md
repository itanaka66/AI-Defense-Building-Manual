---
title: "AI自律型サイバー防御システム 構築マニュアル 後編"
subtitle: "第39部　保存先の登録と定期バックアップの準備"
author: "田中勇"
lang: ja-JP
---

# はじめに

## 本書について

本書は「AI自律型サイバー防御システム 構築マニュアル」後編の第39部です。第38部で、TrueNAS の NFS の共有 `/mnt/backup` を `/mnt/pve/backup` にマウントし、Proxmox の root から書き込めることを確かめました。ここでは次のことを行います。

1. 起動のときにも NFS が正しくマウントされるようにする（systemd のマウントのユニットが古い設定のままだったのを直す）
2. Proxmox に、バックアップ専用のストレージ `truenas-backup` として登録する
3. バックアップする VM・LXC と容量を調べ、PostgreSQL のバックアップの方式・世代・時刻を決める
4. LXC 109 の定期バックアップのジョブを、**無効のまま**登録する
5. PostgreSQL の論理バックアップのスクリプトを置く

決めたことは次のとおりです。

| 項目 | 内容 |
|---|---|
| 世代 | 日次7・週次4・月次3 |
| PostgreSQL の論理バックアップ | 毎日 02:00（日本時間） |
| LXC 109 の Proxmox のバックアップ | 毎日 03:00（日本時間） |

構築の記録は、スクリプトを置いたあと、週次・月次の世代に使うハードリンクが NFS で作れるかを試すところで終わっています。初めてのバックアップの実行と、ジョブ・タイマーの有効化は、まだ行っていません。

## 本書の表記

- コマンドやプログラムは、構築時に実際に使用したものをそのまま掲載しています。改変していません。
- 実行先は、各手順の「実行先」に示します。
  - **pve**：Proxmox のホスト（root）

# 第1章　マウントのユニットを直す

## 1.1　いまの設定

> **実行先：pve**

⟦C0⟧

`/mnt/pve/backup` は NFS でマウントされていましたが、Proxmox のストレージにはまだ登録されていません。このマウントがどこで管理されているかを調べます。

⟦C1⟧

`/etc/fstab` には何もなく、`/etc/systemd/system/mnt-pve-backup.mount`（`Description=Mount storage 'backup' under /mnt/pve`）がありました。**このユニットのファイルは、NFS ではなく ext4 のローカルのディスク（UUID `8cab893f-75f0-478d-842b-e94558853d14`）を指していました。**

## 1.2　食い違いを確かめる

⟦C2⟧

実際のマウントは `192.168.0.254:/mnt/backup`（NFS）で、systemd がいま覚えている設定も NFS でした。その UUID のディスクはどこにもありません。

⟦C3⟧

ファイルは5月24日から変わっておらず、`Type=ext4`・`What=/dev/disk/by-uuid/8cab893f-…` のままでした。上書きする設定（drop-in）もありません。

⟦C4⟧

いまの NFS のマウントは正しく動いています（systemd は、手でマウントした NFS を覚えています）。しかし、**このまま再起動すると、ファイルの ext4 の設定が読み込まれます。** ファイルを NFS の設定にそろえます。

> **注意**：ここでは `daemon-reload` も、マウントの解除も、再起動もしません。

## 1.3　ユニットのファイルを NFS にする

いまのファイルをバックアップしてから書き換え、`systemd-analyze verify` で検査します。

⟦C5⟧

バックアップ（`/root/mnt-pve-backup.mount.before-nfs-20261122`）ができ、書き換えたファイルは `VERIFY_EXIT=0` でした。

## 1.4　systemd に読み込ませる

いまの NFS のマウントは動いたままにし、マウントのやり直しや解除はしません。

⟦C6⟧

⟦C7⟧

ファイルと動いている設定がそろい、起動のときにも NFS がマウントされます。

# 第2章　Proxmox のストレージに登録する

## 2.1　名前がぶつからないか

ストレージの ID は `truenas-backup` にします。

⟦C8⟧

`NO_COLLISION` でした。

## 2.2　登録する

すでにある NFS のマウントを使う「ディレクトリ」のストレージとして登録し、Proxmox に二重にマウントさせないようにします。中身は `backup` だけにし（VM のディスクなどには使わない）、`--is_mountpoint 1` を付けます。これで、NFS がマウントされていないときに、ローカルの空のディレクトリへバックアップを書いてしまうことを防ぎます。登録の直前に、マウントの元と種類を確かめ、合っているときだけ登録します。

⟦C9⟧

`SOURCE=192.168.0.254:/mnt/backup`、`FSTYPE=nfs` で、終了コードは `0` でした。

⟦C10⟧

⟦C11⟧

`truenas-backup` は `active` で、空きは約 1.89TiB、バックアップの一覧はまだ空です。`/mnt/pve/backup/dump` もできました。

# 第3章　バックアップする対象を調べる

## 3.1　VM と LXC

⟦C12⟧

> **注意**：**VM 100（TrueNAS）は、この NFS の保存先を出しているサーバーそのものです。** 自分の NFS に自分のバックアップを書くと、壊れたときに戻せなくなる（循環する）ため、`truenas-backup` へのバックアップの対象にはしません。TrueNAS 自体の守りは、別に考えます。

## 3.2　ディスクの構成

⟦C13⟧

⟦C14⟧

| 対象 | 気をつけること |
|---|---|
| VM 220 security-core・VM 230 ai-defense-manager | このシステムの中心。守る優先度が高い |
| LXC 109 postgresql | 追加のマウントなし、50GB。コンテナのバックアップに加えて、DB の論理バックアップも要る |
| VM 101 | GPU を PCI で渡しているため、戻すときは GPU の割り当てとホストのドライバーも確かめ直す |
| VM 220 | `vmbr0` と内部の `vmbr1` の2つのネットワークを使う |
| LXC 208・209 | ホストの `/opt/nvidia-lxc-570`（約72MB）を `mp8` でマウントしている。これは LXC のバックアップに入らないので、別に守る |

## 3.3　実際に使っている容量

⟦C15⟧

（最後の `vzdump --help` は `Unknown option: help` になります。説明は `man vzdump` で読みます。）

| 対象 | 使っている量 |
|---|---:|
| VM 220 security-core | 約 26.1GiB |
| LXC 103 Prometheus | 1.9GB |
| LXC 105 Grafana | 2.4GB |
| LXC 109 PostgreSQL | 1.7GB |
| LXC 111 Wiki | 2.1GB |
| LXC 129 Open WebUI | 16GB |
| LXC 134 Qdrant | 1.2GB |
| LXC 200 Novel | 39GB |
| LXC 350 easywrider | 59GB |

測れた分だけで約 150GB（圧縮の前）です。VM 101 と 230 は QEMU Guest Agent に答えず、測れませんでした。

# 第4章　PostgreSQL のバックアップの方式

## 4.1　PostgreSQL の様子

⟦C16⟧

PostgreSQL は 17.11 で、いちばん大きい DB は `agent_memory`（約205MB）、次が `novel`（約78MB）でした。`archive_mode` は `off` で、WAL は約32MB です。

## 4.2　ロール・テーブルスペース・拡張

パスワードの情報は表示しません。

⟦C17⟧

| 項目 | 結果 |
|---|---|
| `pg_dump` / `pg_dumpall` | サーバーと同じ 17.11 |
| ロール | 33（`wazuh_collector` はふつうのログインのロール） |
| テーブルスペース | `pg_default` と `pg_global` だけ |
| 拡張 | `plpgsql` と `vector` 0.8.7（`easywrider`・`postgres`・`vector_db` で使用） |

## 4.3　データの量と NFS の容量

⟦C18⟧

データは 475MB（`base` 442MB、WAL 33MB）で、pgvector 0.8.7 も入っていました。NFS には約 1.9TB の空きがあります。

## 4.4　LXC 109 のスナップショット

⟦C19⟧

⟦C20⟧

LXC 109 は Debian 13 の非特権の LXC で、ディスクは `local-lvm`（LVM-thin）の `pve/vm-109-disk-0` だけです。`local-lvm` は 61.66%、メタデータは 2.18% で、スナップショットの余裕は足ります。

## 4.5　方式を決める

| 対象 | 方式 | 目的 |
|---|---|---|
| PostgreSQL のすべての DB | `pg_dump` のカスタム形式（`-Fc`）で1つずつ | DB ごとに戻せる |
| PostgreSQL のロールなど | `pg_dumpall --globals-only` | ロール・権限を戻せる |
| LXC 109 | Proxmox の `vzdump` の snapshot | OS・PostgreSQL 本体・設定を戻せる |
| pgvector | パッケージと拡張の版を記録 | 戻す先で拡張を用意できる |

> **注意**：`pg_dumpall --globals-only` の出力には、ロールのパスワードのハッシュが入ることがあります。保存するファイルは root だけが読み書きできるようにします。

保存する世代は**日次7・週次4・月次3**にしました（構築時に確かめて決めました）。

# 第5章　スケジュールを決める

## 5.1　いまのジョブ

⟦C21⟧

Proxmox のバックアップのジョブも、PostgreSQL の cron も、バックアップのタイマーもありませんでした（`/etc/cron.d/vzdump` は標準のファイルで、中身はコメントだけです）。

時刻は次のように決めました（日本時間）。

| 時刻 | 処理 |
|---|---|
| 毎日 02:00 | PostgreSQL の論理バックアップ |
| 毎日 03:00 | LXC 109 の snapshot のバックアップ |
| 毎週日曜 | その日の分を週次の世代にする |
| 毎月1日 | その日の分を月次の世代にする |

## 5.2　Proxmox の版とバックアップのジョブの機能

⟦C22⟧

Proxmox VE は 8.4.20、systemd は 252 で、バックアップのジョブは `[]` でした。

⟦C23⟧

世代は Proxmox の標準の機能（`--prune-backups 'keep-daily=7,keep-weekly=4,keep-monthly=3'`）で保てます。日・週・月の期間が重なると、実際に残る数は 14 より少なくなることがあります。

## 5.3　時刻の確かめ

⟦C24⟧

Proxmox のホストは `Timezone=Asia/Tokyo`、NTP と同期していて、`*-*-* 03:00:00` は毎日 03:00（日本時間）と解釈されました。

# 第6章　LXC 109 のジョブを無効のまま登録する

無効（`--enabled 0`）で登録するので、この操作ではバックアップは行われず、スケジュールも動きません。

> **実行先：pve**

⟦C25⟧

何も表示されずに終わります。登録された内容を確かめます。

⟦C26⟧

| 項目 | 値 |
|---|---|
| 対象 | LXC 109 だけ |
| 保存先 | `truenas-backup` |
| 時刻 | 毎日 03:00 |
| 方式・圧縮 | snapshot・zstd |
| 世代 | `keep-daily=7,keep-monthly=3,keep-weekly=4` |
| 実行の漏れの補い | しない（`repeat-missed 0`） |
| 有効 | `enabled 0`（無効） |

API の答えと `/etc/pve/jobs.cfg` は同じでした。

# 第7章　PostgreSQL の論理バックアップのスクリプト

## 7.1　保存先と道具

⟦C27⟧

いまあるのは `/mnt/pve/backup` と `/mnt/pve/backup/dump` だけでした（どちらも `root:root`）。

⟦C28⟧

LXC 109 は動いていて、`pg_dump`・`pg_dumpall`・`psql`・`runuser` が使えます。LXC 109 も Proxmox のホストも `Asia/Tokyo` です。テンプレートを除いた DB は17個でした（`agent_db`・`agent_memory`・`aiagent`・`aipmo`・`cerebrum`・`easywrider`・`movie`・`nfaipmo`・`novel`・`orchivio`・`postgres`・`security_workbench`・`tester`・`vector_db`・`winfilemgr`・`writer`・`writers`）。

⟦C29⟧

17個の DB はあわせて約 450MB で、`vector` の拡張を使うのは `easywrider`・`postgres`・`vector_db` の3つ、パッケージは `postgresql-17-pgvector 0.8.7-1.pgdg13+1` でした。

## 7.2　保存するもの

| ファイル | 内容 |
|---|---|
| `globals.sql` | ロールなど（パスワードのハッシュを含むので root だけが読める） |
| `<DB名>.dump` | DB ごとのカスタム形式のダンプ（17個） |
| `database-list.txt`・`postgresql-version.txt`・`extensions.tsv` | DB の一覧・PostgreSQL の版・拡張と版 |
| `SHA256SUMS` | すべてのファイルのチェックサム |

日次は `daily/<日付>`、週次（日曜）は `weekly/<年-W週>`、月次（1日）は `monthly/<年-月>` で、週次と月次は日次のファイルへのハードリンク（`cp -al`）にして、同じデータを3回保存しないようにします。

## 7.3　名前とディレクトリがぶつからないか

⟦C30⟧

3つとも `NOT_EXISTS` で、`*-*-* 02:00:00` は毎日 02:00（日本時間）と解釈されました。

⟦C31⟧

`/usr/local/sbin`・`/mnt/pve/backup`・`/run/lock` とも問題ありませんでした。

## 7.4　スクリプトを置く

スクリプトの安全のための作りは次のとおりです。

- NFS がマウントされていなければ止まる（マウントの元が `192.168.0.254:/mnt/backup` で NFS であることも確かめる）
- 同時に2つ動かないようにロックする（`flock`）
- 一時のディレクトリ（`.staging`）に書き、すべてのチェックサムを作って確かめてから、日次のディレクトリへ移す
- root だけが読み書きできる権限（`umask 077`、ディレクトリは `700`）
- 世代の数を超えた古いものだけを消す

この段階ではスクリプトを置くだけで、DB のダンプはしません。

> **実行先：pve**

⟦C32⟧

⟦C33⟧

スクリプトは root だけが読み・実行できる `700` で置かれ、構文の検査も通りました。**まだ実行はしていません。**

## 7.5　NFS でハードリンクが作れるか

週次・月次の世代は日次のファイルへのハードリンクで作るため、TrueNAS の NFS の上でハードリンクが作れることが前提です。一時のファイルを2つ（元とリンク）作り、同じ inode になるかを確かめて、すぐに消します。バックアップのデータには触りません。

⟦C34⟧

`MOUNT_CHECK=PASS`・`HARDLINK_TEST=PASS`・`CLEANUP=PASS` であれば、いまの世代の管理の方式のまま進められます。**この試験の結果は、受け取った構築の記録の範囲にはありません**（不足情報メモ 39-A）。

# おわりに

第39部で、TrueNAS の保存先を Proxmox に登録し、定期のバックアップを準備しました。

| 項目 | 結果 |
|---|---|
| マウントのユニット | `mnt-pve-backup.mount` を ext4（存在しない UUID）から NFS に直した。バックアップ `/root/mnt-pve-backup.mount.before-nfs-20261122`。起動のときも有効 |
| ストレージ | `truenas-backup`（dir、`content backup`、`is_mountpoint 1`）、約 1.89TiB |
| バックアップの対象外 | VM 100（TrueNAS 自身） |
| 世代 | 日次7・週次4・月次3 |
| LXC 109 のジョブ | `lxc109-daily`（毎日 03:00、snapshot、zstd、`truenas-backup`）を**無効のまま**登録 |
| PostgreSQL の論理バックアップ | `/usr/local/sbin/pg-logical-backup.sh`（`700`、構文の検査は合格）を置いた。毎日 02:00 に動かす予定 |
| まだのこと | ハードリンクの試験の結果、systemd のサービスとタイマー、初めての実行、ジョブとタイマーの有効化、復元の試験 |

構築の記録は、ここまでです。

# Discord Times チャンネル管理 Bot

このBotは、DiscordサーバーのTimesチャンネル（`#99_`で始まるチャンネル）を効率的に管理するためのツールです。以下の3つのスラッシュコマンドを提供します。

-----

## 機能

### `/create_99 {チャンネル名}`

`#99_`で始まる新しいプライベートテキストチャンネルを作成します。このチャンネルは、デフォルトではコマンドを実行したユーザーのみが閲覧でき、その他のユーザーからは見えません。

### `/join_99 {チャンネル名}`

指定された`#99_`で始まるチャンネルへのアクセス権限を付与します。このコマンドを使用することで、チャンネルに参加し、閲覧・書き込みが可能になります。

### `/leave_99 {チャンネル名}`

指定された`#99_`で始まるチャンネルへのアクセス権限を削除します。このコマンドを使用すると、チャンネルへのアクセスができなくなります。

-----

## 必要な権限

このBotを完全に機能させるためには、Discordサーバーで以下の権限をBotのロールに付与する必要があります。

  - **ロールの管理 (Manage Roles)**: `99`チャンネルの権限設定によっては必要な場合があります。
  - **チャンネルの管理 (Manage Channels)**: `/create_99`コマンドでチャンネルを作成したり、`/join_99`や`/leave_99`コマンドでチャンネルの権限を変更したりするために必要です。
  - **チャンネルを見る (View Channels)**: `/create_99`コマンドでチャンネルを作成したり、`/join_99`や`/leave_99`コマンドでチャンネルの権限を変更したりするために必要です。

-----

## セットアップ方法

1.  **Botトークンの取得**: [Discord Developer Portal](https://www.google.com/search?q=https://discord.com/developers/applications)で新しいアプリケーションを作成し、Botを追加してトークンを取得します。
2.  **インテントの有効化**: Discord Developer PortalのBot設定ページで、**Privileged Gateway Intents**にある\*\*`SERVER MEMBERS INTENT`\*\*を有効にします。
3.  **Botの招待**: Botをサーバーに招待する際に、前述の**必要な権限**を付与するように設定します。
4.  **コードの実行**: 取得したトークンを環境変数`DISCORD_BOT_TOKEN`に設定し、プログラムを実行します。


```bash
# 例: 環境変数を設定して実行
export DISCORD_BOT_TOKEN="YOUR_BOT_TOKEN"
python your_bot_file.py
```
-----

## トラブルシューティング

もし `403 Forbidden: Missing Permissions` エラーが発生した場合、以下の項目を確認してください。

1.  Botのロールがサーバーのロール階層で**最も上位**に位置しているか。
2.  Bot Permissionsが`268436496`であるか。この権限には、"Manage Roles", "Manage Channels", "View Channels"権限が含まれます。招待するときのリンクは[https://discord.com/oauth2/authorize?client_id={client_id}&permissions=268436496&scope=bot](https://discord.com/oauth2/authorize?client_id={client_id}&permissions=268436496&scope=bot)である必要があります。
3.  Botの`SERVER MEMBERS INTENT`が有効になっているか。

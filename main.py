import discord
from discord import app_commands
import os
from handlers.manage_times.handler import join_handler, leave_handler, create_handler

# Discord botのトークン
# 環境変数から取得するのが一般的
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# チャンネル名のプレフィックスを環境変数から取得
TIMES_PREFIX = os.getenv("TIMES_PREFIX", "times")
print(f"TIMES_PREFIX: {TIMES_PREFIX}")
TIMES_PREFIX_UNDERBAR = TIMES_PREFIX + "_"

# intentsを設定
intents = discord.Intents.default()
intents.members = True  # メンバー情報を取得するために必要
intents.guilds = True  # チャンネルを作成するために必要な権限を追加


# botのクライアントを作成
class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # コマンドツリーの同期
        self.tree = app_commands.CommandTree(self)

    # botがオンラインになったときに呼び出される
    async def on_ready(self):
        print(f"{self.user} としてログインしました")
        # コマンドを同期
        await self.tree.sync()
        print("コマンドツリーを同期しました")


# クライアントのインスタンスを作成
client = MyClient(intents=intents)


# /join_times コマンド
# チャンネル名で検索してアクセス権限を付与
@client.tree.command(
    name=f"join_{TIMES_PREFIX}",
    description=f"{TIMES_PREFIX_UNDERBAR}から始まるチャンネルに参加します",
)
@app_commands.describe(
    channel_name=f"参加したい{TIMES_PREFIX_UNDERBAR}から始まるチャンネル名"
)
async def join_times(interaction: discord.Interaction, channel_name: str):
    if not channel_name.startswith(TIMES_PREFIX_UNDERBAR):
        channel_name = TIMES_PREFIX_UNDERBAR + channel_name
    await join_handler(interaction, channel_name)


# /leave_times コマンド
# チャンネル名で検索してアクセス権限を削除
@client.tree.command(
    name=f"leave_{TIMES_PREFIX}",
    description=f"{TIMES_PREFIX_UNDERBAR}から始まるチャンネルから退出します",
)
@app_commands.describe(
    channel_name=f"退出したい{TIMES_PREFIX_UNDERBAR}から始まるチャンネル名"
)
async def leave_times(interaction: discord.Interaction, channel_name: str):
    if not channel_name.startswith(TIMES_PREFIX_UNDERBAR):
        channel_name = TIMES_PREFIX_UNDERBAR + channel_name
    await leave_handler(interaction, channel_name)


# /create_times コマンド
# 新しいtimes_チャンネルを作成
@client.tree.command(
    name=f"create_{TIMES_PREFIX}",
    description=f"新しい{TIMES_PREFIX_UNDERBAR}チャンネルを作成します",
)
@app_commands.describe(channel_name="作成したいチャンネル名 (例: test_channel)")
async def create_times(interaction: discord.Interaction, channel_name: str):
    if not channel_name.startswith(TIMES_PREFIX):
        channel_name = TIMES_PREFIX_UNDERBAR + channel_name
    await create_handler(interaction, channel_name)


if __name__ == "__main__":
    # botを実行
    client.run(TOKEN)

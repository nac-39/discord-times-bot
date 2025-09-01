import discord
from discord import app_commands
import os
import traceback

# Discord botのトークン
# 環境変数から取得するのが一般的
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

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


# /join_99 コマンド
# チャンネル名で検索してアクセス権限を付与
@client.tree.command(name="join_99", description="99_から始まるチャンネルに参加します")
@app_commands.describe(channel_name="参加したい99_から始まるチャンネル名")
async def join_99(interaction: discord.Interaction, channel_name: str):
    await interaction.response.defer(
        ephemeral=True
    )  # レスポンスを遅延させ、他の人には見えないようにする

    # チャンネル名が'99_'で始まるか確認
    if not channel_name.startswith("99_"):
        error_msg = "チャンネル名は'99_'で始まる必要があります。"
        print(
            f"エラー: {error_msg} (ユーザー: {interaction.user}, チャンネル名: {channel_name})"
        )
        await interaction.followup.send(error_msg, ephemeral=True)
        return

    # チャンネルを検索
    target_channel = discord.utils.get(
        interaction.guild.text_channels, name=channel_name
    )

    if target_channel:
        # ユーザーにチャンネルへのアクセス権限を付与
        # 権限を上書きして「チャンネルを見る」を許可
        try:
            await target_channel.set_permissions(interaction.user, view_channel=True)
            success_msg = f"`#{channel_name}`へのアクセス権限を付与しました。"
            print(
                f"成功: {success_msg} (ユーザー: {interaction.user}, チャンネル: {channel_name})"
            )
            await interaction.followup.send(success_msg, ephemeral=True)
        except discord.Forbidden as e:
            print(f"権限エラー: {e}")
            error_msg = "権限が不足しています。botに「チャンネルの権限を管理する」権限が付与されているか確認してください。"
            print(
                f"権限エラー: {error_msg} (ユーザー: {interaction.user}, チャンネル: {channel_name})"
            )
            await interaction.followup.send(error_msg, ephemeral=True)
        except Exception as e:
            print(f"予期しないエラー: {e}")
            error_msg = f"予期しないエラーが発生しました: {e}"
            print(
                f"予期しないエラー: {error_msg} (ユーザー: {interaction.user}, チャンネル: {channel_name})"
            )
            print(f"エラーの詳細: {traceback.format_exc()}")
            await interaction.followup.send(error_msg, ephemeral=True)
    else:
        error_msg = f"`#{channel_name}`というチャンネルは見つかりませんでした。"
        print(
            f"エラー: {error_msg} (ユーザー: {interaction.user}, チャンネル名: {channel_name})"
        )
        await interaction.followup.send(error_msg, ephemeral=True)


# /leave_99 コマンド
# チャンネル名で検索してアクセス権限を削除
@client.tree.command(
    name="leave_99", description="99_から始まるチャンネルから退出します"
)
@app_commands.describe(channel_name="退出したい99_から始まるチャンネル名")
async def leave_99(interaction: discord.Interaction, channel_name: str):
    await interaction.response.defer(
        ephemeral=True
    )  # レスポンスを遅延させ、他の人には見えないようにする

    # チャンネル名が'99_'で始まるか確認
    if not channel_name.startswith("99_"):
        error_msg = "チャンネル名は'99_'で始まる必要があります。"
        print(
            f"エラー: {error_msg} (ユーザー: {interaction.user}, チャンネル名: {channel_name})"
        )
        await interaction.followup.send(error_msg, ephemeral=True)
        return

    # チャンネルを検索
    target_channel = discord.utils.get(
        interaction.guild.text_channels, name=channel_name
    )

    if target_channel:
        # ユーザーのチャンネルアクセス権限を削除
        # 権限をNoneに設定して、チャンネル固有の権限を削除する
        try:
            await target_channel.set_permissions(interaction.user, view_channel=None)
            success_msg = f"`#{channel_name}`から退出しました。チャンネルへのアクセス権限が削除されました。"
            print(
                f"成功: {success_msg} (ユーザー: {interaction.user}, チャンネル: {channel_name})"
            )
            await interaction.followup.send(success_msg, ephemeral=True)
        except discord.Forbidden:
            error_msg = "権限が不足しています。botに「チャンネルの権限を管理する」権限が付与されているか確認してください。"
            print(
                f"権限エラー: {error_msg} (ユーザー: {interaction.user}, チャンネル: {channel_name})"
            )
            await interaction.followup.send(error_msg, ephemeral=True)
        except Exception as e:
            error_msg = f"予期しないエラーが発生しました: {e}"
            print(
                f"予期しないエラー: {error_msg} (ユーザー: {interaction.user}, チャンネル: {channel_name})"
            )
            print(f"エラーの詳細: {traceback.format_exc()}")
            await interaction.followup.send(error_msg, ephemeral=True)
    else:
        error_msg = f"`#{channel_name}`というチャンネルは見つかりませんでした。"
        print(
            f"エラー: {error_msg} (ユーザー: {interaction.user}, チャンネル名: {channel_name})"
        )
        await interaction.followup.send(error_msg, ephemeral=True)


# /create_99 コマンド
# 新しい99_チャンネルを作成
@client.tree.command(name="create_99", description="新しい99_チャンネルを作成します")
@app_commands.describe(channel_name="作成したいチャンネル名 (例: test_channel)")
async def create_99(interaction: discord.Interaction, channel_name: str):
    await interaction.response.defer(ephemeral=True)

    # チャンネル名がすでに'99_'で始まるか、'99_'を自動で付加するか
    # ここでは自動で付加する実装にします。
    full_channel_name = f"99_{channel_name}"

    # 既存のチャンネル名と重複していないかチェック
    existing_channel = discord.utils.get(
        interaction.guild.text_channels, name=full_channel_name
    )
    if existing_channel:
        error_msg = f"チャンネル`#{full_channel_name}`はすでに存在します。"
        print(
            f"エラー: {error_msg} (ユーザー: {interaction.user}, チャンネル名: {full_channel_name})"
        )
        await interaction.followup.send(error_msg, ephemeral=True)
        return

    # チャンネルの権限設定
    # @everyoneロールは「チャンネルを見る」権限を無効にする
    overwrites = {}

    # default_roleが存在する場合のみ権限を設定
    if interaction.guild.default_role:
        overwrites[interaction.guild.default_role] = discord.PermissionOverwrite(
            view_channel=False
        )

    # チャンネル作成者には自動でアクセス権限を付与
    overwrites[interaction.user] = discord.PermissionOverwrite(view_channel=True)

    # bot自身にもアクセス権限を付与
    overwrites[interaction.guild.me] = discord.PermissionOverwrite(view_channel=True)

    try:
        # チャンネルを作成
        new_channel = await interaction.guild.create_text_channel(
            name=full_channel_name, overwrites=overwrites
        )
        success_msg = f"チャンネル`#{new_channel.name}`を作成しました。作成者としてアクセス権限が付与されています。"
        print(
            f"成功: {success_msg} (ユーザー: {interaction.user}, チャンネル: {new_channel.name})"
        )
        await interaction.followup.send(success_msg, ephemeral=True)
    except discord.Forbidden as e:
        print(f"権限エラー: {e}")
        error_msg = "権限が不足しています。botに「チャンネルの管理」権限が付与されているか確認してください。"
        print(
            f"権限エラー: {error_msg} (ユーザー: {interaction.user}, チャンネル名: {full_channel_name})"
        )
        await interaction.followup.send(error_msg, ephemeral=True)
    except Exception as e:
        print(f"予期しないエラー: {e}")
        error_msg = f"チャンネル作成中にエラーが発生しました: {e}"
        print(
            f"予期しないエラー: {error_msg} (ユーザー: {interaction.user}, チャンネル名: {full_channel_name})"
        )
        print(f"エラーの詳細: {traceback.format_exc()}")
        await interaction.followup.send(error_msg, ephemeral=True)


if __name__ == "__main__":
    # botを実行
    client.run(TOKEN)

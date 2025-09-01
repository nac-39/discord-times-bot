import os
import discord
from discord import app_commands
import traceback

TIMES_PREFIX = os.getenv("TIMES_PREFIX", "times_")


def is_times_channel(channel_name: str) -> bool:
    return channel_name.startswith(TIMES_PREFIX)


async def join_handler(interaction: discord.Interaction, channel_name: str):
    await interaction.response.defer(
        ephemeral=True
    )  # レスポンスを遅延させ、他の人には見えないようにする

    # チャンネル名が'TIMES_PREFIX'で始まるか確認
    if not is_times_channel(channel_name):
        error_msg = f"チャンネル名は'{TIMES_PREFIX}'で始まる必要があります。"
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


async def leave_handler(interaction: discord.Interaction, channel_name: str):
    await interaction.response.defer(
        ephemeral=True
    )  # レスポンスを遅延させ、他の人には見えないようにする

    # チャンネル名が'TIMES_PREFIX'で始まるか確認
    if not is_times_channel(channel_name):
        error_msg = "チャンネル名は'TIMES_PREFIX'で始まる必要があります。"
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


async def create_handler(interaction: discord.Interaction, channel_name: str):
    await interaction.response.defer(ephemeral=True)

    if not is_times_channel(channel_name):
        error_msg = f"チャンネル名は'{TIMES_PREFIX}'で始まる必要があります。"
        print(
            f"エラー: {error_msg} (ユーザー: {interaction.user}, チャンネル名: {channel_name})"
        )
        await interaction.followup.send(error_msg, ephemeral=True)
        return
    # 既存のチャンネル名と重複していないかチェック
    existing_channel = discord.utils.get(
        interaction.guild.text_channels, name=channel_name
    )
    if existing_channel:
        error_msg = f"チャンネル`#{channel_name}`はすでに存在します。"
        print(
            f"エラー: {error_msg} (ユーザー: {interaction.user}, チャンネル名: {channel_name})"
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
    overwrites[interaction.user] = discord.PermissionOverwrite(
        view_channel=True, send_messages=True
    )

    if interaction.guild and interaction.guild.me:
        # bot自身にもアクセス権限を付与
        overwrites[interaction.guild.me] = discord.PermissionOverwrite(
            view_channel=True, manage_channels=True
        )

    try:
        # チャンネルを作成
        new_channel = await interaction.guild.create_text_channel(
            name=channel_name, overwrites=overwrites
        )
        success_msg = f"チャンネル`#{new_channel.name}`を作成しました。作成者としてアクセス権限が付与されています。"
        print(
            f"成功: {success_msg} (ユーザー: {interaction.user}, チャンネル: {new_channel.name})"
        )
        await interaction.followup.send(success_msg, ephemeral=True)
    except discord.Forbidden as e:
        print(f"権限エラー: {e}")
        print(f"エラーの詳細: {traceback.format_exc()}")
        error_msg = "権限が不足しています。botに「チャンネルの管理」権限が付与されているか確認してください。"
        print(
            f"権限エラー: {error_msg} (ユーザー: {interaction.user}, チャンネル名: {channel_name})"
        )
        await interaction.followup.send(error_msg, ephemeral=True)
    except Exception as e:
        print(f"予期しないエラー: {e}")
        error_msg = f"チャンネル作成中にエラーが発生しました: {e}"
        print(
            f"予期しないエラー: {error_msg} (ユーザー: {interaction.user}, チャンネル名: {channel_name})"
        )
        print(f"エラーの詳細: {traceback.format_exc()}")
        await interaction.followup.send(error_msg, ephemeral=True)

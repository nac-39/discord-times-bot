import discord
from discord import app_commands
from discord.ui import View, Select, Button, Modal, TextInput
import os

# Discord botのトークン
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
# チャンネル名のプレフィックスを環境変数から取得
TIMES_PREFIX = os.getenv("TIMES_PREFIX", "times")
TIMES_PREFIX_UNDERBAR = TIMES_PREFIX + "_"
TIMES_CATEGORY_PREFIX = os.getenv("TIMES_CATEGORY_PREFIX")
# 1ページあたりのチャンネル表示数 (Discordの制限は25)
CHANNELS_PER_PAGE = 25

# --- intentsの設定 ---
intents = discord.Intents.default()
intents.members = True # メンバー情報を取得するために必要
intents.guilds = True  # チャンネルを作成するために必要な権限を追加


# --- UIコンポーネントの定義 ---

# チャンネル作成時に表示されるポップアップウィンドウ（モーダル）
class CreateTimesModal(Modal, title=f"新しい{TIMES_PREFIX}チャンネルの作成"):
    name_input = TextInput(
        label=f"{TIMES_PREFIX_UNDERBAR}以降のチャンネル名を入力してください",
        placeholder="例: ousuk",
        required=True,
        max_length=50,
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        channel_name = f"{TIMES_PREFIX_UNDERBAR}{self.name_input.value}"

        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(f"チャンネル `#{channel_name}` は既に存在します。", ephemeral=True)
            return

        target_category = None
        if TIMES_CATEGORY_PREFIX:
            # プレフィックスに一致するカテゴリを全て取得し、名前でソート
            candidate_categories = sorted(
                [cat for cat in guild.categories if cat.name.startswith(TIMES_CATEGORY_PREFIX)],
                key=lambda cat: cat.name
            )
            
            # チャンネル数に空きがあるカテゴリを探す
            for category in candidate_categories:
                if len(category.channels) < 50:
                    target_category = category
                    break
            
            # 空きのあるカテゴリが見つからなければ、新しいカテゴリを作成
            if target_category is None:
                new_category_name = f"{TIMES_CATEGORY_PREFIX}-{len(candidate_categories) + 1}"
                try:
                    target_category = await guild.create_category(name=new_category_name)
                except discord.Forbidden:
                    await interaction.response.send_message("エラー: 新しいカテゴリを作成する権限がBotにありません。", ephemeral=True)
                    return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        try:
            new_channel = await guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                category=target_category,
                reason=f"{member.display_name} によって作成"
            )
            await interaction.response.send_message(f"チャンネル {new_channel.mention} を作成しました！", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("エラー: Botにチャンネルを作成する権限がありません。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"予期せぬエラーが発生しました: {e}", ephemeral=True)

# 参加/退出するチャンネルを選択するためのドロップダウンメニュー（ページ単位で表示）
class TimesSelect(Select):
    def __init__(self, channels_on_page: list, final_selections: set):
        options = []
        for ch in channels_on_page:
            is_selected = ch.id in final_selections
            options.append(
                discord.SelectOption(
                    label=ch.name,
                    description=f"#{ch.name} に参加/退出します",
                    value=str(ch.id),
                    default=is_selected
                )
            )

        if not options:
            options.append(discord.SelectOption(label="表示するチャンネルがありません", value="dummy"))

        super().__init__(
            placeholder=f"参加/退出したい{TIMES_PREFIX}チャンネルを選択...",
            options=options,
            disabled=(not channels_on_page),
            min_values=0,
            max_values=len(options) if options[0].value != "dummy" else 1
        )

    async def callback(self, interaction: discord.Interaction):
        # このページにあるチャンネルIDのセットを取得
        page_channel_ids = {int(opt.value) for opt in self.options if opt.value != "dummy"}
        # 今回ユーザーが選択したチャンネルIDのセットを取得
        selected_ids = {int(val) for val in self.values}

        # このページのチャンネルについて、選択されなかったものは全体選択から削除
        for channel_id in page_channel_ids - selected_ids:
            self.view.final_selections.discard(channel_id)
        # 選択されたものは全体選択に追加
        for channel_id in selected_ids:
            self.view.final_selections.add(channel_id)

        # UIの更新は行わず、応答だけを返す
        await interaction.response.defer()


# ページネーションと決定ボタンを持つ参加/退出View
class TimesJoinPaginatedView(View):
    current_page: int = 0

    def __init__(self, all_channels: list, member: discord.Member):
        super().__init__(timeout=180) # 3分でタイムアウト
        self.all_channels = all_channels
        self.member = member
        self.total_pages = max(1, (len(self.all_channels) - 1) // CHANNELS_PER_PAGE + 1)
        
        self.final_selections = {
            ch.id for ch in self.all_channels if ch.permissions_for(member).read_messages
        }
        
        self._update_view()

    def _get_page_slice(self) -> list:
        start = self.current_page * CHANNELS_PER_PAGE
        end = start + CHANNELS_PER_PAGE
        return self.all_channels[start:end]

    def _update_view(self):
        self.clear_items()
        self.add_item(TimesSelect(self._get_page_slice(), self.final_selections))
        self.add_item(self.prev_button)
        self.add_item(self.page_indicator)
        self.add_item(self.next_button)
        self.add_item(self.confirm_button)

        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= self.total_pages - 1
        self.page_indicator.label = f"{self.current_page + 1} / {self.total_pages}"

    @discord.ui.button(label="◀️ 前へ", style=discord.ButtonStyle.secondary, row=1)
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        self.current_page -= 1
        self._update_view()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="1 / 1", style=discord.ButtonStyle.grey, disabled=True, row=1)
    async def page_indicator(self, interaction: discord.Interaction, button: Button):
        pass

    @discord.ui.button(label="次へ ▶️", style=discord.ButtonStyle.secondary, row=1)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        self.current_page += 1
        self._update_view()
        await interaction.response.edit_message(view=self)
        
    @discord.ui.button(label="決定", style=discord.ButtonStyle.primary, row=2)
    async def confirm_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        
        for channel in self.all_channels:
            has_permission = channel.permissions_for(self.member).read_messages
            should_have_permission = channel.id in self.final_selections
            
            try:
                if should_have_permission and not has_permission:
                    # 参加させる
                    await channel.set_permissions(self.member, read_messages=True)
                elif not should_have_permission and has_permission:
                    # 退出させる
                    await channel.set_permissions(self.member, overwrite=None)
            except discord.Forbidden:
                await interaction.followup.send("エラー: Botに権限を変更する権限がありません。", ephemeral=True)
                return
                
        await interaction.followup.send("チャンネルの参加/退出設定を更新しました。", ephemeral=True)
        self.stop() # Viewを停止

# チャンネル一覧をページネーションで表示するView
class TimesListPaginatedView(View):
    current_page: int = 0

    def __init__(self, all_channels: list):
        super().__init__(timeout=180) # 3分でタイムアウト
        self.all_channels = all_channels
        self.total_pages = max(1, (len(self.all_channels) - 1) // CHANNELS_PER_PAGE + 1)
        self._update_view()

    def _get_page_slice(self) -> list:
        start = self.current_page * CHANNELS_PER_PAGE
        end = start + CHANNELS_PER_PAGE
        return self.all_channels[start:end]

    def _create_embed_for_page(self) -> discord.Embed:
        channels_on_page = self._get_page_slice()
        
        description = "\n".join(
            f"- #{channel.name}" for channel in channels_on_page
        ) or "表示するチャンネルがありません。"

        embed = discord.Embed(
            title=f"参加可能な{TIMES_PREFIX}チャンネル一覧",
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"ページ {self.current_page + 1} / {self.total_pages}")
        return embed

    def _update_view(self):
        self.clear_items()
        self.add_item(self.prev_button)
        self.add_item(self.page_indicator)
        self.add_item(self.next_button)

        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= self.total_pages - 1
        self.page_indicator.label = f"{self.current_page + 1} / {self.total_pages}"
        
    @discord.ui.button(label="◀️ 前へ", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        self.current_page -= 1
        self._update_view()
        await interaction.response.edit_message(embed=self._create_embed_for_page(), view=self)

    @discord.ui.button(label="1 / 1", style=discord.ButtonStyle.grey, disabled=True)
    async def page_indicator(self, interaction: discord.Interaction, button: Button):
        pass

    @discord.ui.button(label="次へ ▶️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        self.current_page += 1
        self._update_view()
        await interaction.response.edit_message(embed=self._create_embed_for_page(), view=self)

# --- メインの操作パネル ---
class TimesControlPanel(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label=f"自分の{TIMES_PREFIX}を作成", style=discord.ButtonStyle.success, custom_id="times_panel:create", row=0)
    async def create_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(CreateTimesModal())
    
    @discord.ui.button(label="チャンネル一覧を見る", style=discord.ButtonStyle.grey, custom_id="times_panel:list", row=1)
    async def list_channels_button(self, interaction: discord.Interaction, button: Button):
        all_channels = sorted([
            ch for ch in interaction.guild.text_channels 
            if ch.name.startswith(TIMES_PREFIX_UNDERBAR) and ch.id != interaction.channel.id
        ], key=lambda ch: ch.name)

        if not all_channels:
            await interaction.response.send_message("現在参加可能なチャンネルはありません。", ephemeral=True)
            return
        
        view = TimesListPaginatedView(all_channels)
        await interaction.response.send_message(embed=view._create_embed_for_page(), view=view, ephemeral=True)

    @discord.ui.button(label="他のTimesに参加/退出する", style=discord.ButtonStyle.secondary, custom_id="times_panel:join_leave", row=1)
    async def join_leave_button(self, interaction: discord.Interaction, button: Button):
        all_channels = sorted([
            ch for ch in interaction.guild.text_channels 
            if ch.name.startswith(TIMES_PREFIX_UNDERBAR) and ch.id != interaction.channel.id
        ], key=lambda ch: ch.name)

        if not all_channels:
            await interaction.response.send_message("現在参加可能なチャンネルはありません。", ephemeral=True)
            return

        view = TimesJoinPaginatedView(all_channels, interaction.user)
        await interaction.response.send_message("参加/退出したいチャンネルを選択してください。\n（既に参加済みのチャンネルが選択されています）", view=view, ephemeral=True)

# --- Botのメインクラス ---
class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # コマンドツリーの同期
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        self.add_view(TimesControlPanel())
    
    # botがオンラインになったときに呼び出される
    async def on_ready(self):
        print(f"{self.user} としてログインしました")
        # コマンドを同期
        await self.tree.sync()
        print("コマンドツリーを同期しました")

# --- Botのインスタンス化とコマンド定義 ---
client = MyClient(intents=intents)

# パネルを投稿するための管理者用コマンド
@client.tree.command(name=f"post_{TIMES_PREFIX}_panel", description=f"操作パネルをこのチャンネルに投稿します。")
@app_commands.default_permissions(administrator=True)
async def post_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"{TIMES_PREFIX}チャンネル 操作パネル",
        description=(
            f"👇 **自分の{TIMES_PREFIX}を作成**: あなた専用のプライベートチャンネルを作成します。\n\n"
            f"👇 **チャンネル一覧を見る**: 参加可能なチャンネルの一覧を表示します。\n\n"
            f"👇 **他のTimesに参加/退出する**: 既存のチャンネルに参加したり、退出したりします。"
        ),
        color=discord.Color.blue()
    )
    await interaction.channel.send(embed=embed, view=TimesControlPanel())
    await interaction.response.send_message("パネルを投稿しました。", ephemeral=True)

# /list_times コマンド
@client.tree.command(name=f"list_{TIMES_PREFIX}", description=f"参加可能な{TIMES_PREFIX}チャンネルの一覧を表示します。")
async def list_times(interaction: discord.Interaction):
    all_channels = sorted([
        ch for ch in interaction.guild.text_channels 
        if ch.name.startswith(TIMES_PREFIX_UNDERBAR) and ch.id != interaction.channel.id
    ], key=lambda ch: ch.name)

    if not all_channels:
        await interaction.response.send_message(f"{TIMES_PREFIX_UNDERBAR}から始まるチャンネルは見つかりませんでした。", ephemeral=True)
        return
    
    view = TimesListPaginatedView(all_channels)
    await interaction.response.send_message(embed=view._create_embed_for_page(), view=view, ephemeral=True)

# /join_times コマンドのチャンネル名入力時に候補を提示するオートコンプリート関数
async def times_channel_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    guild = interaction.guild
    # プレフィックスで始まり、かつ現在の入力文字を含むチャンネルを検索
    channels = [
        channel for channel in guild.text_channels
        if channel.name.startswith(TIMES_PREFIX_UNDERBAR) and \
           channel.id != interaction.channel.id and \
           current.lower() in channel.name.lower()
    ]
    # 候補を25個に制限
    return [
        app_commands.Choice(name=channel.name, value=channel.name)
        for channel in channels[:25]
    ]

# /join_times コマンド
# チャンネル名で検索してアクセス権限を付与
@client.tree.command(name=f"join_{TIMES_PREFIX}", description=f"既存の{TIMES_PREFIX}チャンネルに参加します。")
@app_commands.autocomplete(channel_name=times_channel_autocomplete)
@app_commands.describe(channel_name=f"参加したい{TIMES_PREFIX}チャンネル名")
async def join_times(interaction: discord.Interaction, channel_name: str):
    guild = interaction.guild
    member = interaction.user
    
    target_channel = discord.utils.get(guild.text_channels, name=channel_name)
    if not target_channel:
        await interaction.response.send_message(f"チャンネル `#{channel_name}` は見つかりませんでした。", ephemeral=True)
        return
        
    try:
        await target_channel.set_permissions(member, read_messages=True)
        await interaction.response.send_message(f"チャンネル {target_channel.mention} に参加しました！", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("エラー: Botに権限を変更する権限がありません。", ephemeral=True)

# /leave_times コマンド用のオートコンプリート関数
async def leave_times_channel_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    guild = interaction.guild
    member = interaction.user # コマンド実行者を取得
    
    # 実行者が参加しているtimesチャンネルのみを候補にする
    channels = [
        channel for channel in guild.text_channels
        if channel.name.startswith(TIMES_PREFIX_UNDERBAR) and \
           channel.id != interaction.channel.id and \
           channel.permissions_for(member).read_messages and \
           current.lower() in channel.name.lower()
    ]
    
    # 候補を25個に制限
    return [
        app_commands.Choice(name=channel.name, value=channel.name)
        for channel in channels[:25]
    ]

# /leave_times コマンド
# チャンネル名で検索してアクセス権限を削除
@client.tree.command(name=f"leave_{TIMES_PREFIX}", description=f"既存の{TIMES_PREFIX}チャンネルから退出します。")
@app_commands.autocomplete(channel_name=leave_times_channel_autocomplete) # ← 変更
@app_commands.describe(channel_name=f"退出したい{TIMES_PREFIX}チャンネル名")
async def leave_times(interaction: discord.Interaction, channel_name: str):
    guild = interaction.guild
    member = interaction.user
    
    target_channel = discord.utils.get(guild.text_channels, name=channel_name)
    if not target_channel:
        await interaction.response.send_message(f"チャンネル `#{channel_name}` は見つかりませんでした。", ephemeral=True)
        return
        
    try:
        await target_channel.set_permissions(member, overwrite=None)
        await interaction.response.send_message(f"チャンネル {target_channel.mention} から退出しました。", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("エラー: Botに権限を変更する権限がありません。", ephemeral=True)

# /create_times コマンド
# 新しいtimes_チャンネルを作成
@client.tree.command(name=f"create_{TIMES_PREFIX}", description=f"あなた専用の新しい{TIMES_PREFIX}チャンネルを作成します。")
@app_commands.describe(name=f"{TIMES_PREFIX_UNDERBAR}以降のチャンネル名（例: じゃっくんの部屋）")
async def create_times(interaction: discord.Interaction, name: str):
    guild = interaction.guild
    member = interaction.user
    channel_name = f"{TIMES_PREFIX_UNDERBAR}{name}"

    existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
    if existing_channel:
        await interaction.response.send_message(f"チャンネル `#{channel_name}` は既に存在します。", ephemeral=True)
        return

    target_category = None
    if TIMES_CATEGORY_PREFIX:
        candidate_categories = sorted(
            [cat for cat in guild.categories if cat.name.startswith(TIMES_CATEGORY_PREFIX)],
            key=lambda cat: cat.name
        )
        for category in candidate_categories:
            if len(category.channels) < 50:
                target_category = category
                break
        if target_category is None:
            new_category_name = f"{TIMES_CATEGORY_PREFIX}-{len(candidate_categories) + 1}"
            try:
                target_category = await guild.create_category(name=new_category_name)
            except discord.Forbidden:
                await interaction.response.send_message("エラー: 新しいカテゴリを作成する権限がBotにありません。", ephemeral=True)
                return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }

    try:
        new_channel = await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            category=target_category,
            reason=f"{member.display_name} によって作成"
        )
        await interaction.response.send_message(f"チャンネル {new_channel.mention} を作成しました！", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("エラー: Botに権限を変更する権限がありません。", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"予期せぬエラーが発生しました: {e}", ephemeral=True)


if __name__ == "__main__":
    # botを実行
    client.run(TOKEN)

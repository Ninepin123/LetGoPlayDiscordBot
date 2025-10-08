import discord
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput, Select
from discord.ext import commands
from datetime import datetime, timedelta
import calendar
import json
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional

# 載入環境變數
load_dotenv()

# Bot 設定
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 資料儲存
EVENTS_FILE = "events.json"


# ==================== 資料管理 ====================
class EventManager:
    def __init__(self):
        self.events = self.load_events()

    def load_events(self) -> Dict:
        if os.path.exists(EVENTS_FILE):
            with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_events(self):
        with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, ensure_ascii=False, indent=2)
        print(f'💾 已儲存活動資料到 {EVENTS_FILE}')

    def create_event(self, name: str, creator_id: int, description: str = "", target_month: str = "", event_type: str = "availability", scheduled_time: str = ""):
        self.events[name] = {
            "creator": creator_id,
            "description": description,
            "target_month": target_month,  # 格式: "2025-10"
            "event_type": event_type,  # "availability" or "scheduled"
            "scheduled_time": scheduled_time,  # 格式: "2025-10-12T18:00"
            "participants": {} if event_type == "availability" else [],  # availability 用 dict，scheduled 用 list
            "created_at": datetime.now().isoformat()
        }
        self.save_events()

    def delete_event(self, name: str):
        if name in self.events:
            del self.events[name]
            self.save_events()

    def add_availability(self, event_name: str, user_name: str, time_slots: List[Dict]):
        if event_name in self.events:
            self.events[event_name]["participants"][user_name] = time_slots
            print(f'✅ 已更新 {user_name} 的時間選擇（{len(time_slots)} 個時段）')
            self.save_events()
        else:
            print(f'❌ 活動 {event_name} 不存在')

    def add_participant(self, event_name: str, user_id: int, user_name: str):
        """新增參加者到指定時間活動"""
        if event_name in self.events:
            event = self.events[event_name]
            if event.get("event_type") == "scheduled":
                # 檢查是否已參加
                if user_id not in event["participants"]:
                    event["participants"].append(user_id)
                    self.save_events()
                    return True
        return False

    def remove_participant(self, event_name: str, user_id: int):
        """移除參加者"""
        if event_name in self.events:
            event = self.events[event_name]
            if event.get("event_type") == "scheduled" and user_id in event["participants"]:
                event["participants"].remove(user_id)
                self.save_events()
                return True
        return False

    def get_event(self, name: str) -> Optional[Dict]:
        return self.events.get(name)

    def list_events(self) -> List[str]:
        return list(self.events.keys())


event_manager = EventManager()


# ==================== Modal 表單 ====================
class CreateEventModal(Modal, title="建立新活動"):
    event_name = TextInput(
        label="活動名稱",
        placeholder="例如：火鍋聚、打球、看電影",
        required=True,
        max_length=50
    )

    description = TextInput(
        label="活動說明（可選）",
        placeholder="描述活動內容",
        required=False,
        max_length=200,
        style=discord.TextStyle.paragraph
    )

    target_month = TextInput(
        label="目標月份（留空=當前月）",
        placeholder="格式：2025-10",
        required=False,
        max_length=7
    )

    async def on_submit(self, interaction: discord.Interaction):
        event_name = self.event_name.value
        description = self.description.value
        target_month = self.target_month.value.strip()

        # 檢查活動是否已存在
        if event_name in event_manager.events:
            await interaction.response.send_message(
                f"❌ 活動「{event_name}」已存在！",
                ephemeral=True
            )
            return

        # 如果沒有輸入月份，使用當前月份
        if not target_month:
            now = datetime.now()
            target_month = f"{now.year}-{now.month:02d}"
        else:
            # 驗證月份格式
            try:
                datetime.strptime(target_month, "%Y-%m")
            except ValueError:
                await interaction.response.send_message(
                    "❌ 月份格式錯誤！請使用 YYYY-MM 格式（例如：2025-10）",
                    ephemeral=True
                )
                return

        # 先快速回應互動，避免超時
        await interaction.response.defer()

        # 建立活動
        event_manager.create_event(event_name, interaction.user.id, description, target_month)

        # 建立活動卡片
        embed = create_event_embed(event_name, interaction.user)
        view = EventControlView(event_name)

        await interaction.followup.send(embed=embed, view=view)


class CreateScheduledEventModal(Modal, title="建立指定時間揪團"):
    event_name = TextInput(
        label="活動名稱",
        placeholder="例如：週五火鍋聚",
        required=True,
        max_length=50
    )

    description = TextInput(
        label="活動說明（可選）",
        placeholder="描述活動內容",
        required=False,
        max_length=200,
        style=discord.TextStyle.paragraph
    )

    scheduled_date = TextInput(
        label="日期",
        placeholder="格式：2025-10-12",
        required=True,
        max_length=10
    )

    scheduled_time = TextInput(
        label="時間",
        placeholder="格式：18:00",
        required=True,
        max_length=5
    )

    async def on_submit(self, interaction: discord.Interaction):
        event_name = self.event_name.value
        description = self.description.value
        date_str = self.scheduled_date.value.strip()
        time_str = self.scheduled_time.value.strip()

        # 檢查活動是否已存在
        if event_name in event_manager.events:
            await interaction.response.send_message(
                f"❌ 活動「{event_name}」已存在！",
                ephemeral=True
            )
            return

        # 驗證日期時間格式
        try:
            scheduled_datetime = f"{date_str}T{time_str}"
            datetime.fromisoformat(scheduled_datetime)
        except ValueError:
            await interaction.response.send_message(
                "❌ 日期或時間格式錯誤！請使用正確格式（日期：2025-10-12，時間：18:00）",
                ephemeral=True
            )
            return

        # 先快速回應互動，避免超時
        await interaction.response.defer()

        # 建立指定時間活動
        event_manager.create_event(
            event_name,
            interaction.user.id,
            description,
            "",  # 不需要 target_month
            "scheduled",  # event_type
            scheduled_datetime
        )

        # 建立活動卡片
        embed = create_scheduled_event_embed(event_name, interaction.user)
        view = ScheduledEventView(event_name)

        await interaction.followup.send(embed=embed, view=view)


# ==================== 日曆選擇 UI ====================
class CalendarView(View):
    """顯示月曆並讓使用者複選日期"""
    def __init__(self, event_name: str, year: int, month: int, user_id: int, original_message: discord.Message = None):
        super().__init__(timeout=300)
        self.event_name = event_name
        self.year = year
        self.month = month
        self.user_id = user_id
        self.original_message = original_message  # 儲存原始活動卡片訊息

        # 建立日期選單
        self.create_calendar_select()

        # 新增確認按鈕
        confirm_btn = Button(label="✅ 確認選擇", style=discord.ButtonStyle.success, row=2)
        confirm_btn.callback = self.confirm_callback
        self.add_item(confirm_btn)

    def create_calendar_select(self):
        """建立日期選單（支援複選）"""
        # 取得該月份的所有日期
        num_days = calendar.monthrange(self.year, self.month)[1]

        # 取得使用者已選擇的日期
        event = event_manager.get_event(self.event_name)
        user = bot.get_user(self.user_id)
        user_name = user.display_name if user else str(self.user_id)
        existing_dates = set()

        if event and user_name in event.get("participants", {}):
            for slot in event["participants"][user_name]:
                existing_dates.add(slot["date"])

        # 建立選項（最多 25 個）
        options = []
        for day in range(1, num_days + 1):
            date_str = f"{self.year}-{self.month:02d}-{day:02d}"
            # 取得星期
            weekday = calendar.day_name[datetime(self.year, self.month, day).weekday()]
            weekday_zh = {"Monday": "週一", "Tuesday": "週二", "Wednesday": "週三",
                         "Thursday": "週四", "Friday": "週五", "Saturday": "週六", "Sunday": "週日"}[weekday]

            # 檢查是否已選擇
            is_selected = date_str in existing_dates
            label = f"{self.month}月{day}日 ({weekday_zh})"
            if is_selected:
                label = f"✓ {label}"  # 已選擇的日期加上打勾符號

            options.append(discord.SelectOption(
                label=label,
                value=date_str,
                description=date_str,
                default=is_selected  # 設定為預設選中
            ))

        # Discord Select 最多 25 個選項，如果超過需要分批
        if len(options) <= 25:
            select = Select(
                placeholder="📅 請選擇日期（可複選）",
                options=options,
                min_values=0,  # 改為 0，允許取消所有選擇
                max_values=min(len(options), 25)  # 最多選 25 個
            )
            self.add_item(select)
        else:
            # 分成兩個選單 (1-15 和 16-31)
            mid = 15

            select1 = Select(
                placeholder=f"📅 選擇日期 (1-{mid}日，可複選)",
                options=options[:mid],
                min_values=0,
                max_values=mid,
                row=0
            )
            self.add_item(select1)

            select2 = Select(
                placeholder=f"📅 選擇日期 ({mid+1}-{num_days}日，可複選)",
                options=options[mid:],
                min_values=0,
                max_values=len(options[mid:]),
                row=1
            )
            self.add_item(select2)

    async def confirm_callback(self, interaction: discord.Interaction):
        """確認選擇"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 這不是你的操作！", ephemeral=True)
            return

        # 取得所有已選擇的日期（從所有 Select 中）
        selected_dates = []
        for item in self.children:
            if isinstance(item, Select) and hasattr(item, 'values') and item.values:
                selected_dates.extend(item.values)

        # 移除重複
        selected_dates = list(set(selected_dates))

        # 允許選擇 0 個日期（表示清空）
        if not selected_dates:
            # 清空使用者的時間選擇
            event = event_manager.get_event(self.event_name)
            user_name = interaction.user.display_name

            if user_name in event["participants"]:
                del event["participants"][user_name]
                event_manager.save_events()

            # 編輯原訊息為結果
            await interaction.response.edit_message(
                content="✅ 已清空您的時間選擇！",
                embed=None,
                view=None
            )
        else:
            # 儲存日期（完全替換，不是附加）
            user_name = interaction.user.display_name
            new_slots = []

            for date_str in selected_dates:
                # 每個日期設為全天有空
                new_slots.append({
                    "date": date_str
                })

            event_manager.add_availability(self.event_name, user_name, new_slots)

            dates_text = "\n".join([f"• {d}" for d in sorted(selected_dates)])

            # 編輯原訊息為結果
            await interaction.response.edit_message(
                content=f"✅ 已更新您的可參加日期（共 {len(selected_dates)} 天）：\n{dates_text}",
                embed=None,
                view=None
            )

        # 更新原始活動卡片的參與人數
        if self.original_message:
            try:
                updated_embed = create_event_embed(self.event_name)
                await self.original_message.edit(embed=updated_embed)
            except:
                pass




# ==================== 互動式 UI ====================
class EventControlView(View):
    def __init__(self, event_name: str):
        super().__init__(timeout=None)
        self.event_name = event_name

    @discord.ui.button(label="🕒 選擇可參加時間", style=discord.ButtonStyle.primary)
    async def select_time(self, interaction: discord.Interaction, button: Button):
        # 取得活動的目標月份
        event = event_manager.get_event(self.event_name)

        if not event:
            await interaction.response.send_message("❌ 活動不存在！", ephemeral=True)
            return

        target_month = event.get("target_month", "")

        if not target_month:
            await interaction.response.send_message("❌ 此活動未設定目標月份！", ephemeral=True)
            return

        # 解析年月
        year, month = map(int, target_month.split("-"))

        # 顯示日曆（傳入原始訊息以便更新）
        view = CalendarView(self.event_name, year, month, interaction.user.id, interaction.message)
        embed = discord.Embed(
            title=f"📅 {self.event_name} - 選擇日期",
            description=f"請從下拉選單選擇 {year} 年 {month} 月的日期（可複選）\n選完後點擊「✅ 確認選擇」",
            color=discord.Color.blue()
        )

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="📊 查看統計", style=discord.ButtonStyle.secondary)
    async def view_stats(self, interaction: discord.Interaction, button: Button):
        event = event_manager.get_event(self.event_name)

        if not event:
            await interaction.response.send_message("❌ 活動不存在！", ephemeral=True)
            return

        # 建立統計訊息
        embed = discord.Embed(
            title=f"📊 {self.event_name} - 參加統計",
            color=discord.Color.blue()
        )

        if not event["participants"]:
            embed.description = "目前還沒有人選擇日期"
        else:
            for user, dates in event["participants"].items():
                date_text = "\n".join([
                    f"• {d['date']}"
                    for d in dates
                ])
                embed.add_field(name=f"👤 {user}", value=date_text, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔍 自動推薦日期", style=discord.ButtonStyle.success)
    async def recommend_time(self, interaction: discord.Interaction, button: Button):
        event = event_manager.get_event(self.event_name)

        if not event or not event["participants"]:
            await interaction.response.send_message(
                "❌ 尚無參加者資料，無法推薦日期！",
                ephemeral=True
            )
            return

        # 計算共同日期
        common_dates = calculate_common_dates(event["participants"])

        if not common_dates:
            # 顯示除錯資訊
            participants_info = []
            for user, dates in event["participants"].items():
                date_list = [d['date'] for d in dates]
                participants_info.append(f"**{user}**: {', '.join(date_list[:3])}{'...' if len(date_list) > 3 else ''}")

            debug_text = f"參與人數：{len(event['participants'])} 人\n" + "\n".join(participants_info)

            await interaction.response.send_message(
                f"😢 找不到所有人都有空的時間！\n\n{debug_text}",
                ephemeral=True
            )
            return

        # 建立推薦訊息
        embed = discord.Embed(
            title=f"🔍 {self.event_name} - 推薦日期",
            description=f"找到 {len(common_dates)} 個所有人都有空的日期",
            color=discord.Color.green()
        )

        dates_text = "\n".join([f"📅 {d}" for d in sorted(common_dates)[:10]])  # 最多顯示10個
        embed.add_field(name="⭐ 推薦日期", value=dates_text, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🗑️ 刪除活動", style=discord.ButtonStyle.danger)
    async def delete_event(self, interaction: discord.Interaction, button: Button):
        event = event_manager.get_event(self.event_name)

        if not event:
            await interaction.response.send_message("❌ 活動不存在！", ephemeral=True)
            return

        # 檢查權限
        if event["creator"] != interaction.user.id:
            await interaction.response.send_message(
                "❌ 只有活動建立者可以刪除活動！",
                ephemeral=True
            )
            return

        event_manager.delete_event(self.event_name)
        await interaction.response.send_message(f"✅ 已刪除活動「{self.event_name}」", ephemeral=True)

        # 更新原始訊息
        try:
            await interaction.message.edit(
                content="🗑️ 此活動已被刪除",
                embed=None,
                view=None
            )
        except:
            pass


class ScheduledEventView(View):
    """指定時間活動的參加介面"""
    def __init__(self, event_name: str):
        super().__init__(timeout=None)
        self.event_name = event_name

    @discord.ui.button(label="✅ 我要參加", style=discord.ButtonStyle.success, custom_id="join_event")
    async def join_event(self, interaction: discord.Interaction, button: Button):
        result = event_manager.add_participant(self.event_name, interaction.user.id, interaction.user.display_name)

        if result:
            await interaction.response.send_message("✅ 已加入活動！", ephemeral=True)
            # 更新 embed
            try:
                embed = create_scheduled_event_embed(self.event_name)
                await interaction.message.edit(embed=embed)
            except:
                pass
        else:
            await interaction.response.send_message("❌ 您已經參加此活動了！", ephemeral=True)

    @discord.ui.button(label="❌ 取消參加", style=discord.ButtonStyle.danger, custom_id="leave_event")
    async def leave_event(self, interaction: discord.Interaction, button: Button):
        result = event_manager.remove_participant(self.event_name, interaction.user.id)

        if result:
            await interaction.response.send_message("✅ 已取消參加！", ephemeral=True)
            # 更新 embed
            try:
                embed = create_scheduled_event_embed(self.event_name)
                await interaction.message.edit(embed=embed)
            except:
                pass
        else:
            await interaction.response.send_message("❌ 您尚未參加此活動！", ephemeral=True)

    @discord.ui.button(label="👥 查看參加者", style=discord.ButtonStyle.secondary, custom_id="view_participants")
    async def view_participants(self, interaction: discord.Interaction, button: Button):
        event = event_manager.get_event(self.event_name)

        if not event:
            await interaction.response.send_message("❌ 活動不存在！", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"👥 {self.event_name} - 參加名單",
            color=discord.Color.blue()
        )

        participants = event.get("participants", [])
        if not participants:
            embed.description = "目前還沒有人參加"
        else:
            participant_mentions = []
            for user_id in participants:
                participant_mentions.append(f"• <@{user_id}>")

            embed.add_field(
                name=f"已報名：{len(participants)} 人",
                value="\n".join(participant_mentions),
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🗑️ 刪除活動", style=discord.ButtonStyle.danger, custom_id="delete_scheduled")
    async def delete_event(self, interaction: discord.Interaction, button: Button):
        event = event_manager.get_event(self.event_name)

        if not event:
            await interaction.response.send_message("❌ 活動不存在！", ephemeral=True)
            return

        # 檢查權限
        if event["creator"] != interaction.user.id:
            await interaction.response.send_message(
                "❌ 只有活動建立者可以刪除活動！",
                ephemeral=True
            )
            return

        event_manager.delete_event(self.event_name)
        await interaction.response.send_message(f"✅ 已刪除活動「{self.event_name}」", ephemeral=True)

        # 更新原始訊息
        try:
            await interaction.message.edit(
                content="🗑️ 此活動已被刪除",
                embed=None,
                view=None
            )
        except:
            pass


# ==================== 輔助函數 ====================
def create_event_embed(event_name: str, user: discord.User = None) -> discord.Embed:
    event = event_manager.get_event(event_name)

    if not event:
        return discord.Embed(title="錯誤", description="活動不存在", color=discord.Color.red())

    embed = discord.Embed(
        title=f"🎉 活動：{event_name}",
        description=event.get("description", "無描述"),
        color=discord.Color.gold()
    )

    # 使用 Discord 提及格式來標記發起人
    creator_mention = f"<@{event['creator']}>"

    embed.add_field(name="🧑‍💼 發起人", value=creator_mention, inline=True)
    embed.add_field(
        name="📅 目標月份",
        value=event.get("target_month", "未設定"),
        inline=True
    )

    # 計算參與人數（對於 availability 類型，participants 是 dict）
    participants = event.get('participants', {})
    participant_count = len(participants) if isinstance(participants, dict) else len(participants)

    embed.add_field(
        name="👥 參與人數",
        value=f"{participant_count} 人",
        inline=True
    )

    embed.set_footer(text="請點擊下方按鈕進行操作")

    return embed


def create_scheduled_event_embed(event_name: str, user: discord.User = None) -> discord.Embed:
    """建立指定時間活動的 Embed"""
    event = event_manager.get_event(event_name)

    if not event:
        return discord.Embed(title="錯誤", description="活動不存在", color=discord.Color.red())

    # 解析時間
    scheduled_time = event.get("scheduled_time", "")
    if scheduled_time:
        dt = datetime.fromisoformat(scheduled_time)
        time_text = f"{dt.strftime('%Y年%m月%d日')} {dt.strftime('%H:%M')}"
    else:
        time_text = "未設定"

    embed = discord.Embed(
        title=f"🎉 揪團：{event_name}",
        description=event.get("description", "無描述"),
        color=discord.Color.green()
    )

    # 使用 Discord 提及格式來標記發起人
    creator_mention = f"<@{event['creator']}>"

    embed.add_field(name="🧑‍💼 發起人", value=creator_mention, inline=True)
    embed.add_field(name="📅 活動時間", value=time_text, inline=True)

    participants = event.get("participants", [])
    embed.add_field(
        name="👥 參加人數",
        value=f"{len(participants)} 人",
        inline=True
    )

    embed.set_footer(text="點擊「✅ 我要參加」加入活動")

    return embed


def calculate_common_dates(participants: Dict[str, List[Dict]]) -> List[str]:
    """計算所有參與者的共同日期"""
    if not participants:
        return []

    # 取得所有人的日期集合
    all_dates = []
    for user_dates in participants.values():
        user_date_set = set(d["date"] for d in user_dates)
        all_dates.append(user_date_set)

    # 計算交集
    if not all_dates:
        return []

    common = all_dates[0]
    for date_set in all_dates[1:]:
        common = common.intersection(date_set)

    return sorted(list(common))


# ==================== Bot 指令 ====================
@bot.event
async def on_ready():
    print(f'✅ Bot 已登入為 {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'✅ 同步了 {len(synced)} 個指令')
    except Exception as e:
        print(f'❌ 同步指令失敗: {e}')


@bot.tree.command(name="create", description="建立時間調查活動")
async def create_event(interaction: discord.Interaction):
    modal = CreateEventModal()
    await interaction.response.send_modal(modal)


@bot.tree.command(name="甲崩", description="建立指定時間揪團")
async def create_scheduled_event(interaction: discord.Interaction):
    modal = CreateScheduledEventModal()
    await interaction.response.send_modal(modal)


@bot.tree.command(name="events", description="列出所有活動")
async def list_events(interaction: discord.Interaction):
    events = event_manager.list_events()

    if not events:
        await interaction.response.send_message("目前沒有任何活動", ephemeral=True)
        return

    embed = discord.Embed(
        title="📋 活動列表",
        description="\n".join([f"• {name}" for name in events]),
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="show", description="顯示活動詳情")
@app_commands.describe(event_name="活動名稱")
async def show_event(interaction: discord.Interaction, event_name: str):
    event = event_manager.get_event(event_name)

    if not event:
        await interaction.response.send_message(f"❌ 找不到活動「{event_name}」", ephemeral=True)
        return

    # 根據活動類型顯示不同的介面
    event_type = event.get("event_type", "availability")

    if event_type == "scheduled":
        embed = create_scheduled_event_embed(event_name)
        view = ScheduledEventView(event_name)
    else:
        embed = create_event_embed(event_name)
        view = EventControlView(event_name)

    await interaction.response.send_message(embed=embed, view=view)


# ==================== 執行 Bot ====================
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")

    if not TOKEN:
        print("❌ 請在 .env 檔案中設定 DISCORD_BOT_TOKEN")
    else:
        bot.run(TOKEN)

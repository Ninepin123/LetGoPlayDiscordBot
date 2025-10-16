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
import aiohttp
import asyncio
import tempfile
import pathlib
import platform
import shutil
import subprocess

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
        # 確保目錄存在
        os.makedirs(os.path.dirname(EVENTS_FILE) if os.path.dirname(EVENTS_FILE) else '.', exist_ok=True)
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

        # 動態建立按鈕，使用活動名稱作為 custom_id 的一部分
        select_btn = Button(
            label="🕒 選擇可參加時間",
            style=discord.ButtonStyle.primary,
            custom_id=f"select_time:{event_name}"
        )
        select_btn.callback = self.select_time
        self.add_item(select_btn)

        stats_btn = Button(
            label="📊 查看統計",
            style=discord.ButtonStyle.secondary,
            custom_id=f"view_stats:{event_name}"
        )
        stats_btn.callback = self.view_stats
        self.add_item(stats_btn)

        recommend_btn = Button(
            label="🔍 自動推薦日期",
            style=discord.ButtonStyle.success,
            custom_id=f"recommend_time:{event_name}"
        )
        recommend_btn.callback = self.recommend_time
        self.add_item(recommend_btn)

        delete_btn = Button(
            label="🗑️ 刪除活動",
            style=discord.ButtonStyle.danger,
            custom_id=f"delete_event:{event_name}"
        )
        delete_btn.callback = self.delete_event
        self.add_item(delete_btn)

    async def select_time(self, interaction: discord.Interaction):
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

    async def view_stats(self, interaction: discord.Interaction):
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

    async def recommend_time(self, interaction: discord.Interaction):
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

    async def delete_event(self, interaction: discord.Interaction):
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

        # 動態建立按鈕，使用活動名稱作為 custom_id 的一部分
        join_btn = Button(
            label="✅ 我要參加",
            style=discord.ButtonStyle.success,
            custom_id=f"join_event:{event_name}"
        )
        join_btn.callback = self.join_event
        self.add_item(join_btn)

        leave_btn = Button(
            label="❌ 取消參加",
            style=discord.ButtonStyle.danger,
            custom_id=f"leave_event:{event_name}"
        )
        leave_btn.callback = self.leave_event
        self.add_item(leave_btn)

        view_btn = Button(
            label="👥 查看參加者",
            style=discord.ButtonStyle.secondary,
            custom_id=f"view_participants:{event_name}"
        )
        view_btn.callback = self.view_participants
        self.add_item(view_btn)

        delete_btn = Button(
            label="🗑️ 刪除活動",
            style=discord.ButtonStyle.danger,
            custom_id=f"delete_scheduled:{event_name}"
        )
        delete_btn.callback = self.delete_event
        self.add_item(delete_btn)

    async def join_event(self, interaction: discord.Interaction):
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

    async def leave_event(self, interaction: discord.Interaction):
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

    async def view_participants(self, interaction: discord.Interaction):
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

    async def delete_event(self, interaction: discord.Interaction):
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


# ==================== 檔案轉換功能 ====================
async def download_file(url: str, save_path: str) -> bool:
    """下載檔案"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(save_path, 'wb') as f:
                        f.write(await response.read())
                    return True
                return False
    except Exception as e:
        print(f"❌ 下載檔案失敗: {e}")
        return False


def get_os_type() -> str:
    """取得作業系統類型"""
    return platform.system()  # 'Windows', 'Linux', 'Darwin' (Mac)


def check_office_installed() -> bool:
    """檢查是否安裝 Microsoft Office（僅 Windows）"""
    if get_os_type() != 'Windows':
        return False
    
    try:
        import comtypes.client
        word = comtypes.client.CreateObject('Word.Application')
        word.Quit()
        return True
    except:
        return False


def find_libreoffice_path() -> Optional[str]:
    """尋找 LibreOffice 執行檔路徑（跨平台）"""
    os_type = get_os_type()
    
    # 先檢查是否在 PATH 中
    soffice = shutil.which("soffice")
    if soffice:
        return soffice
    
    # 檢查常見的安裝路徑
    if os_type == 'Windows':
        paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
    elif os_type == 'Linux':
        paths = [
            "/usr/bin/soffice",
            "/usr/bin/libreoffice",
            "/usr/local/bin/soffice",
            "/usr/local/bin/libreoffice",
            "/opt/libreoffice/program/soffice",
        ]
    elif os_type == 'Darwin':  # Mac
        paths = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "/usr/local/bin/soffice",
        ]
    else:
        paths = []
    
    for path in paths:
        if os.path.exists(path):
            return path
    
    return None


def check_libreoffice_installed() -> bool:
    """檢查是否安裝 LibreOffice（跨平台）"""
    return find_libreoffice_path() is not None


def convert_docx_to_pdf_office(docx_path: str, pdf_path: str) -> tuple[bool, str]:
    """使用 Microsoft Office 轉換 DOCX 到 PDF（僅 Windows）"""
    # 只在 Windows 上嘗試
    if get_os_type() != 'Windows':
        return False, "Office COM API 僅支援 Windows"
    
    try:
        import comtypes.client
        
        word = comtypes.client.CreateObject('Word.Application')
        word.Visible = False
        
        # 轉換路徑為絕對路徑
        docx_path = str(pathlib.Path(docx_path).absolute())
        pdf_path = str(pathlib.Path(pdf_path).absolute())
        
        doc = word.Documents.Open(docx_path)
        doc.SaveAs(pdf_path, FileFormat=17)  # 17 = wdFormatPDF
        doc.Close()
        word.Quit()
        
        return True, "Microsoft Office"
    except Exception as e:
        return False, f"Office 錯誤: {str(e)}"


def convert_docx_to_pdf_docx2pdf(docx_path: str, pdf_path: str) -> tuple[bool, str]:
    """使用 docx2pdf 轉換（需要 Office 或 LibreOffice）"""
    # docx2pdf 主要在 Windows 上運作
    if get_os_type() != 'Windows':
        return False, "docx2pdf 僅支援 Windows"
    
    try:
        from docx2pdf import convert
        convert(docx_path, pdf_path)
        return True, "docx2pdf"
    except Exception as e:
        return False, f"docx2pdf 錯誤: {str(e)}"


def convert_docx_to_pdf_libreoffice(docx_path: str, pdf_path: str) -> tuple[bool, str]:
    """使用 LibreOffice 轉換（跨平台）"""
    try:
        # 找到 LibreOffice 執行檔
        soffice_path = find_libreoffice_path()
        
        if not soffice_path:
            return False, "找不到 LibreOffice（請安裝 LibreOffice）"
        
        # 轉換路徑為絕對路徑
        docx_path = str(pathlib.Path(docx_path).absolute())
        output_dir = str(pathlib.Path(pdf_path).parent.absolute())
        
        # 執行轉換
        result = subprocess.run(
            [soffice_path, '--headless', '--convert-to', 'pdf', '--outdir', output_dir, docx_path],
            capture_output=True,
            timeout=60,
            text=True
        )
        
        if result.returncode == 0 and os.path.exists(pdf_path):
            return True, f"LibreOffice ({get_os_type()})"
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            return False, f"LibreOffice 轉換失敗: {error_msg}"
            
    except subprocess.TimeoutExpired:
        return False, "LibreOffice 轉換超時（檔案可能太大）"
    except Exception as e:
        return False, f"LibreOffice 錯誤: {str(e)}"


def convert_pptx_to_pdf_office(pptx_path: str, pdf_path: str) -> tuple[bool, str]:
    """使用 Microsoft Office 轉換 PPTX 到 PDF（僅 Windows）"""
    # 只在 Windows 上嘗試
    if get_os_type() != 'Windows':
        return False, "Office COM API 僅支援 Windows"
    
    try:
        import comtypes.client
        
        powerpoint = comtypes.client.CreateObject('Powerpoint.Application')
        powerpoint.Visible = 1
        
        # 轉換路徑為絕對路徑
        pptx_path = str(pathlib.Path(pptx_path).absolute())
        pdf_path = str(pathlib.Path(pdf_path).absolute())
        
        presentation = powerpoint.Presentations.Open(pptx_path, WithWindow=False)
        presentation.SaveAs(pdf_path, FileFormat=32)  # 32 = ppSaveAsPDF
        presentation.Close()
        powerpoint.Quit()
        
        return True, "Microsoft Office"
    except Exception as e:
        return False, f"Office 錯誤: {str(e)}"


def convert_pptx_to_pdf_libreoffice(pptx_path: str, pdf_path: str) -> tuple[bool, str]:
    """使用 LibreOffice 轉換 PPTX（跨平台）"""
    try:
        # 找到 LibreOffice 執行檔
        soffice_path = find_libreoffice_path()
        
        if not soffice_path:
            return False, "找不到 LibreOffice（請安裝 LibreOffice）"
        
        # 轉換路徑為絕對路徑
        pptx_path = str(pathlib.Path(pptx_path).absolute())
        output_dir = str(pathlib.Path(pdf_path).parent.absolute())
        
        # 執行轉換
        result = subprocess.run(
            [soffice_path, '--headless', '--convert-to', 'pdf', '--outdir', output_dir, pptx_path],
            capture_output=True,
            timeout=60,
            text=True
        )
        
        if result.returncode == 0 and os.path.exists(pdf_path):
            return True, f"LibreOffice ({get_os_type()})"
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            return False, f"LibreOffice 轉換失敗: {error_msg}"
            
    except subprocess.TimeoutExpired:
        return False, "LibreOffice 轉換超時（檔案可能太大）"
    except Exception as e:
        return False, f"LibreOffice 錯誤: {str(e)}"


async def convert_file_to_pdf(file_path: str, file_extension: str) -> tuple[Optional[str], str]:
    """
    轉換檔案到 PDF，嘗試多種方法（跨平台）
    返回: (pdf_path, method_used) 或 (None, error_message)
    """
    pdf_path = file_path.rsplit('.', 1)[0] + '.pdf'
    loop = asyncio.get_event_loop()
    os_type = get_os_type()
    
    print(f"🖥️ 作業系統: {os_type}")
    
    if file_extension in ['.docx', '.doc']:
        # 根據作業系統決定轉換順序
        if os_type == 'Windows':
            # Windows: 先試 Office，再試 docx2pdf，最後 LibreOffice
            methods = [
                ("Microsoft Office", convert_docx_to_pdf_office),
                ("docx2pdf", convert_docx_to_pdf_docx2pdf),
                ("LibreOffice", convert_docx_to_pdf_libreoffice),
            ]
        else:
            # Linux/Mac: 只用 LibreOffice
            methods = [
                ("LibreOffice", convert_docx_to_pdf_libreoffice),
            ]
        
        for method_name, method_func in methods:
            print(f"🔄 嘗試使用 {method_name}...")
            success, msg = await loop.run_in_executor(None, method_func, file_path, pdf_path)
            if success and os.path.exists(pdf_path):
                return pdf_path, msg
            print(f"   ⚠️ {msg}")
        
        return None, f"所有轉換方法都失敗了（{os_type} 系統）"
        
    elif file_extension == '.pptx':
        # 根據作業系統決定轉換順序
        if os_type == 'Windows':
            # Windows: 先試 Office，再試 LibreOffice
            methods = [
                ("Microsoft Office", convert_pptx_to_pdf_office),
                ("LibreOffice", convert_pptx_to_pdf_libreoffice),
            ]
        else:
            # Linux/Mac: 只用 LibreOffice
            methods = [
                ("LibreOffice", convert_pptx_to_pdf_libreoffice),
            ]
        
        for method_name, method_func in methods:
            print(f"🔄 嘗試使用 {method_name}...")
            success, msg = await loop.run_in_executor(None, method_func, file_path, pdf_path)
            if success and os.path.exists(pdf_path):
                return pdf_path, msg
            print(f"   ⚠️ {msg}")
        
        return None, f"所有轉換方法都失敗了（{os_type} 系統）"
    
    return None, "不支援的檔案格式"


# ==================== Bot 指令 ====================
@bot.event
async def on_ready():
    print(f'✅ Bot 已登入為 {bot.user}')

    # 為所有現有活動註冊 persistent views
    for event_name in event_manager.list_events():
        event = event_manager.get_event(event_name)
        event_type = event.get("event_type", "availability")

        if event_type == "scheduled":
            view = ScheduledEventView(event_name)
        else:
            view = EventControlView(event_name)

        bot.add_view(view)
        print(f'📝 已註冊活動「{event_name}」的 persistent view')

    try:
        synced = await bot.tree.sync()
        print(f'✅ 同步了 {len(synced)} 個指令')
    except Exception as e:
        print(f'❌ 同步指令失敗: {e}')


@bot.event
async def on_message(message: discord.Message):
    """處理訊息，包括檔案轉換"""
    # 不處理 bot 自己的訊息
    if message.author == bot.user:
        return
    
    # 處理指令
    await bot.process_commands(message)
    
    # 檢查是否 bot 被提及
    if bot.user not in message.mentions:
        return
    
    # 檢查是否有附件
    if not message.attachments:
        # 如果被提及但沒有附件，顯示幫助訊息
        help_embed = discord.Embed(
            title="📄 檔案轉換助手",
            description="請上傳檔案並提及我，我會自動將檔案轉換為 PDF！",
            color=discord.Color.blue()
        )
        help_embed.add_field(
            name="支援格式",
            value="✅ `.doc`\n✅ `.docx`\n✅ `.pptx`",
            inline=True
        )
        help_embed.add_field(
            name="使用方式",
            value=f"上傳檔案 + 提及 {bot.user.mention}",
            inline=True
        )
        
        # 檢查系統狀態
        os_type = get_os_type()
        has_office = check_office_installed()
        has_libreoffice = check_libreoffice_installed()
        
        status_text = f"🖥️ **作業系統：** {os_type}\n\n"
        
        if has_office:
            status_text += "✅ Microsoft Office（僅 Windows）\n"
        else:
            if os_type == 'Windows':
                status_text += "❌ Microsoft Office\n"
            else:
                status_text += "⚪ Microsoft Office（不支援 {os_type}）\n"
        
        if has_libreoffice:
            libreoffice_path = find_libreoffice_path()
            status_text += f"✅ LibreOffice（{libreoffice_path}）\n"
        else:
            status_text += "❌ LibreOffice\n"
        
        if not has_office and not has_libreoffice:
            status_text += "\n⚠️ **請至少安裝一個轉換工具：**\n"
            if os_type == 'Windows':
                status_text += "• [Microsoft Office](https://www.office.com/)（需授權）\n"
            status_text += "• [LibreOffice](https://www.libreoffice.org/)（免費、跨平台）✨"
        elif not has_libreoffice and os_type != 'Windows':
            status_text += "\n⚠️ **在 {os_type} 系統上，建議安裝 LibreOffice**\n"
            status_text += "• [LibreOffice 下載](https://www.libreoffice.org/download/download/)"
        
        help_embed.add_field(
            name="系統狀態",
            value=status_text,
            inline=False
        )
        
        await message.reply(embed=help_embed)
        return
    
    # 支援的檔案格式
    supported_extensions = ['.doc', '.docx', '.pptx']
    
    # 處理每個附件
    for attachment in message.attachments:
        # 取得檔案副檔名
        file_extension = pathlib.Path(attachment.filename).suffix.lower()
        
        # 檢查是否為支援的格式
        if file_extension not in supported_extensions:
            continue
        
        # 發送處理中訊息
        processing_msg = await message.reply(f"📄 正在處理 `{attachment.filename}`，請稍候...")
        
        try:
            # 建立臨時目錄
            with tempfile.TemporaryDirectory() as temp_dir:
                # 下載檔案
                original_file_path = os.path.join(temp_dir, attachment.filename)
                download_success = await download_file(attachment.url, original_file_path)
                
                if not download_success:
                    await processing_msg.edit(content=f"❌ 下載 `{attachment.filename}` 失敗！")
                    continue
                
                # 轉換為 PDF（會嘗試多種方法）
                result = await convert_file_to_pdf(original_file_path, file_extension)
                pdf_path, method_or_error = result
                
                if pdf_path and os.path.exists(pdf_path):
                    # 建立 PDF 檔名
                    pdf_filename = pathlib.Path(attachment.filename).stem + '.pdf'
                    
                    # 檢查檔案大小（Discord 限制）
                    pdf_size = os.path.getsize(pdf_path)
                    max_size = 8 * 1024 * 1024  # 8MB for free servers
                    
                    if pdf_size > max_size:
                        await processing_msg.edit(
                            content=f"❌ 轉換後的 PDF 檔案太大 ({pdf_size / 1024 / 1024:.1f} MB)，"
                            f"超過 Discord 限制 (8 MB)。"
                        )
                        continue
                    
                    # 上傳 PDF
                    with open(pdf_path, 'rb') as pdf_file:
                        discord_file = discord.File(pdf_file, filename=pdf_filename)
                        await message.reply(
                            f"✅ 轉換完成！`{attachment.filename}` → `{pdf_filename}`\n"
                            f"使用方法: {method_or_error}",
                            file=discord_file
                        )
                    
                    # 刪除處理中訊息
                    await processing_msg.delete()
                    
                    print(f"✅ 成功轉換: {attachment.filename} → {pdf_filename} (使用 {method_or_error})")
                else:
                    # 轉換失敗，提供詳細錯誤訊息
                    error_embed = discord.Embed(
                        title=f"❌ 轉換 `{attachment.filename}` 失敗",
                        description=f"錯誤詳情: {method_or_error}",
                        color=discord.Color.red()
                    )
                    
                    # 檢查並提供解決方案
                    has_office = check_office_installed()
                    has_libreoffice = check_libreoffice_installed()
                    
                    solutions = []
                    if not has_office and not has_libreoffice:
                        solutions.append("⚠️ **未偵測到轉換工具**")
                        solutions.append("\n請安裝以下任一工具：")
                        solutions.append("1. [Microsoft Office](https://www.office.com/) - 商業軟體")
                        solutions.append("2. [LibreOffice](https://www.libreoffice.org/) - 免費開源")
                    elif not has_office:
                        solutions.append("ℹ️ 系統未安裝 Microsoft Office")
                        solutions.append("已嘗試使用 LibreOffice，但轉換失敗")
                    elif not has_libreoffice:
                        solutions.append("ℹ️ 系統未安裝 LibreOffice")
                        solutions.append("已嘗試使用 Microsoft Office，但轉換失敗")
                    else:
                        solutions.append("⚠️ 已嘗試 Microsoft Office 和 LibreOffice，都失敗了")
                        solutions.append("可能原因：")
                        solutions.append("• 檔案可能損壞")
                        solutions.append("• 檔案格式不正確")
                        solutions.append("• Office/LibreOffice 未正確安裝")
                    
                    error_embed.add_field(
                        name="解決方案",
                        value="\n".join(solutions),
                        inline=False
                    )
                    
                    await processing_msg.edit(content=None, embed=error_embed)
                    
        except Exception as e:
            error_msg = f"❌ 處理 `{attachment.filename}` 時發生錯誤：\n```{str(e)}```"
            await processing_msg.edit(content=error_msg)
            print(f"❌ 處理檔案時發生錯誤: {e}")
            import traceback
            traceback.print_exc()


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

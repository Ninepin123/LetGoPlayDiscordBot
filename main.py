import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# Bot 設定
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # 啟用語音狀態 intent
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot 已登入為 {bot.user}')

    try:
        synced = await bot.tree.sync()
        print(f'✅ 同步了 {len(synced)} 個指令')
    except Exception as e:
        print(f'❌ 同步指令失敗: {e}')


@bot.tree.command(name="voice_join", description="機器人加入你的語音頻道")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
async def voice_join(interaction: discord.Interaction):
    """讓機器人加入使用者所在的語音頻道"""
    # 檢查使用者是否在語音頻道中
    if not interaction.user.voice:
        await interaction.response.send_message(
            "❌ 你需要先加入一個語音頻道！",
            ephemeral=True
        )
        return

    # 取得使用者所在的語音頻道
    voice_channel = interaction.user.voice.channel

    # 檢查機器人是否已經在語音頻道中
    if interaction.guild.voice_client:
        # 如果已經在同一個頻道
        if interaction.guild.voice_client.channel == voice_channel:
            await interaction.response.send_message(
                f"✅ 我已經在 `{voice_channel.name}` 了！",
                ephemeral=True
            )
            return
        # 如果在不同的頻道，先斷開
        await interaction.guild.voice_client.disconnect()

    try:
        # 加入語音頻道
        await voice_channel.connect()
        await interaction.response.send_message(
            f"✅ 已加入語音頻道：`{voice_channel.name}`\n"
            f"💡 使用 `/voice_leave` 讓我離開",
            ephemeral=False
        )
        print(f"🔊 已加入語音頻道: {voice_channel.name} (伺服器: {interaction.guild.name})")
    except Exception as e:
        await interaction.response.send_message(
            f"❌ 加入語音頻道時發生錯誤：{str(e)}",
            ephemeral=True
        )
        print(f"❌ 加入語音頻道失敗: {e}")


@bot.tree.command(name="voice_leave", description="機器人離開語音頻道")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
async def voice_leave(interaction: discord.Interaction):
    """讓機器人離開語音頻道"""
    # 檢查機器人是否在語音頻道中
    if not interaction.guild.voice_client:
        await interaction.response.send_message(
            "❌ 我目前不在任何語音頻道中！",
            ephemeral=True
        )
        return

    try:
        voice_channel_name = interaction.guild.voice_client.channel.name
        # 離開語音頻道
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message(
            f"👋 已離開語音頻道：`{voice_channel_name}`",
            ephemeral=False
        )
        print(f"🔇 已離開語音頻道: {voice_channel_name} (伺服器: {interaction.guild.name})")
    except Exception as e:
        await interaction.response.send_message(
            f"❌ 離開語音頻道時發生錯誤：{str(e)}",
            ephemeral=True
        )
        print(f"❌ 離開語音頻道失敗: {e}")


# ==================== 執行 Bot ====================
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")

    if not TOKEN:
        print("❌ 請在 .env 檔案中設定 DISCORD_BOT_TOKEN")
    else:
        bot.run(TOKEN)

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
from datetime import timedelta

# ===== הגדרות =====
TOKEN = "MTQ5MjEzNjE4NzA4NTcxNzU3Nw.G5AP07.Y0d0ITEJrfksCLtaFbFGrkznxPSAwgB76dNshs"

PRIVATE_CHANNEL_ID = 1492142632619610163  # החדר הפרטי שלך
PUBLIC_CHANNEL_ID = 1492123215038779394   # חדר כאן או לא כאן הציבורי

EXEMPT_USER_IDS = [
    1283774834907545663,   # אתה
    1492138187236315139,   # הבוט
    1492146027216769134,   # ID נוסף
]

EXEMPT_ROLE_IDS = [
    1492143031552577627,   # הנהלה 1
    1492143250692378767,   # הנהלה 2
    1492144923787526235,   # הנהלה 3
]

AUTO_ROLE_ID = 1492145250620412025  # רול אוטומטי לכל מי שנכנס

WIN_ROLE_ID = 1492147266465697894       # רול ניצחון 🏅
LOSS_ROLE_ID = 1492147368374702233     # רול הפסד 🥀
CHAMPION_ROLE_ID = 1492147458275283004 # רול משתמש ניצחון 🏆
SPAM_ROLE_ID = 1492211642665140378     # רול ספאמר

WIN_COUNT = {}   # מעקב ניצחונות
LOSS_COUNT = {}  # מעקב הפסדים
SPAM_COUNT = {}  # מעקב ספאם

# ===== הגדרת הבוט =====
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ===== רול אוטומטי בכניסה לשרת =====
@bot.event
async def on_member_join(member):
    role = member.guild.get_role(AUTO_ROLE_ID)
    if role:
        await member.add_roles(role)
        print(f"נוסף רול ל-{member.name}")

# ===== פקודה לתת רול לכולם =====
@bot.command()
async def התחל(ctx):
    exempt_ids = EXEMPT_USER_IDS + [bot.user.id]
    count = 0
    for member in ctx.guild.members:
        if member.id in exempt_ids:
            continue
        role = ctx.guild.get_role(AUTO_ROLE_ID)
        if role and role not in member.roles:
            await member.add_roles(role)
            count += 1
    await ctx.send(f"✅ נוסף רול ל-{count} משתמשים!")

# ===== חסימת לינקים + זיהוי ספאם =====
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # בדוק אם יש לינק
    if "http://" in message.content or "https://" in message.content or "discord.gg" in message.content:
        is_exempt = message.author.id in EXEMPT_USER_IDS
        if not is_exempt:
            for role in message.author.roles:
                if role.id in EXEMPT_ROLE_IDS:
                    is_exempt = True
                    break

        if not is_exempt:
            await message.delete()
            await message.author.timeout(timedelta(minutes=5), reason="שליחת לינק")
            await message.channel.send(f"⛔ {message.author.mention} קיבל טיימאוט של 5 דקות על שליחת לינק!", delete_after=5)
            return

    # בדוק ספאם
    is_exempt = message.author.id in EXEMPT_USER_IDS
    if not is_exempt:
        for role in message.author.roles:
            if role.id in EXEMPT_ROLE_IDS:
                is_exempt = True
                break

    if not is_exempt:
        user_id = message.author.id
        SPAM_COUNT[user_id] = SPAM_COUNT.get(user_id, 0) + 1

        if SPAM_COUNT[user_id] >= 6:
            SPAM_COUNT[user_id] = 0
            spam_role = message.guild.get_role(SPAM_ROLE_ID)
            if spam_role:
                await message.author.add_roles(spam_role)
            await message.author.timeout(timedelta(minutes=5), reason="ספאם")
            await message.channel.send(
                f"🤫 {message.author.mention} מה אתה מספים? שתוק",
                delete_after=10
            )
            # הסר את הרול אחרי 5 דקות
            await asyncio.sleep(300)
            try:
                if spam_role:
                    await message.author.remove_roles(spam_role)
            except:
                pass
            return

    await bot.process_commands(message)

# ===== כפתור תגובה =====
class HereButton(discord.ui.View):
    def __init__(self, target_member, timeout_seconds=30):
        super().__init__(timeout=timeout_seconds)
        self.target_member = target_member
        self.answered = False

    @discord.ui.button(label="✅ אני כאן!", style=discord.ButtonStyle.green)
    async def here_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_member.id:
            await interaction.response.send_message("❌ זה לא בשבילך!", ephemeral=True)
            return

        self.answered = True
        self.stop()

        guild = interaction.guild
        win_role = guild.get_role(WIN_ROLE_ID) if WIN_ROLE_ID else None
        champion_role = guild.get_role(CHAMPION_ROLE_ID) if CHAMPION_ROLE_ID else None

        if win_role:
            await self.target_member.add_roles(win_role)

        user_id = self.target_member.id
        WIN_COUNT[user_id] = WIN_COUNT.get(user_id, 0) + 1

        msg = f"✅ {self.target_member.mention} ענה שהוא כאן! נוסף לו רול ניצחון 🏅"

        if WIN_COUNT[user_id] >= 5:
            if win_role:
                await self.target_member.remove_roles(win_role)
            if champion_role:
                await self.target_member.add_roles(champion_role)
            WIN_COUNT[user_id] = 0
            msg += f"\n🏆 {self.target_member.mention} צבר 5 ניצחונות וקיבל רול **משתמש ניצחון** 🏆!"

        button.disabled = True
        await interaction.response.edit_message(content=msg, view=self)

    async def on_timeout(self):
        if not self.answered:
            guild = self.target_member.guild
            loss_role = guild.get_role(LOSS_ROLE_ID) if LOSS_ROLE_ID else None

            if loss_role:
                await self.target_member.add_roles(loss_role)

            user_id = self.target_member.id
            LOSS_COUNT[user_id] = LOSS_COUNT.get(user_id, 0) + 1

            channel = guild.get_channel(PUBLIC_CHANNEL_ID)
            msg = f"⏰ הזמן עבר! {self.target_member.mention} לא ענה וקיבל רול הפסד 🥀"

            if LOSS_COUNT[user_id] >= 5:
                try:
                    await self.target_member.ban(reason="5 הפסדים", delete_message_days=0)
                    duration = timedelta(days=10, hours=12)
                    # Discord לא תומך בבאן עם זמן ישיר, אז נשתמש בטיימאוט
                    await self.target_member.timeout(duration, reason="5 הפסדים")
                    msg += f"\n🔨 {self.target_member.mention} צבר 5 הפסדים וקיבל באן לשבוע וחצי!"
                    LOSS_COUNT[user_id] = 0
                except:
                    pass

            if channel:
                await channel.send(msg)

# ===== פקודת סלאש =====
@tree.command(name="hereserver", description="תייג שחקן רנדומלי")
async def hereserver(interaction: discord.Interaction):
    # בדוק שהפקודה מגיעה מהחדר הפרטי
    if interaction.channel_id != PRIVATE_CHANNEL_ID:
        await interaction.response.send_message("❌ אתה לא יכול להשתמש בפקודה הזו כאן!", ephemeral=True)
        return

    guild = interaction.guild
    exempt_ids = EXEMPT_USER_IDS + [bot.user.id]

    # מצא משתמשים שניתן לתייג
    eligible = []
    for member in guild.members:
        if member.bot:
            continue
        if member.id in exempt_ids:
            continue
        has_exempt_role = any(role.id in EXEMPT_ROLE_IDS for role in member.roles)
        if has_exempt_role:
            continue
        eligible.append(member)

    if not eligible:
        await interaction.response.send_message("❌ אין משתמשים זמינים!", ephemeral=True)
        return

    target = random.choice(eligible)

    public_channel = guild.get_channel(PUBLIC_CHANNEL_ID)
    if not public_channel:
        await interaction.response.send_message("❌ לא נמצא החדר הציבורי!", ephemeral=True)
        return

    view = HereButton(target_member=target, timeout_seconds=30)

    await interaction.response.send_message("✅ נשלח!", ephemeral=True)

    await public_channel.send(
        f"כאן או לא כאןןן הגיעה הזמן\n{target.mention}\nאתה כאן? ⏱️ יש לך 30 שניות!",
        view=view
    )

# ===== הפעלת הבוט =====
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ הבוט {bot.user} פועל!")

bot.run(TOKEN)

import asyncio
import random
from pyrogram import filters, Client
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait

from EsproMusic import app
from EsproMusic.misc import SUDOERS

# NOTE: Ritik ka import yahan se hata diya hai taaki circular import error na aaye.
# Hum usse function ke andar import karenge.

# ==================== CONFIG ====================

JOIN_TEXT = [
    "🎙️ {user} joined the voice chat!",
    "👋 {user} is now in the voice chat!",
    "🎵 {user} hopped into the voice chat!",
]

LEFT_TEXT = [
    "👋 {user} left the voice chat!",
    "🚪 {user} has exited the voice chat!",
    "💨 {user} disconnected from voice chat!",
]

# Database: chat_id -> True/False
VC_LOGGER_DB: dict[int, bool] = {}

# Cache: chat_id -> Set of user_ids (Pichli baar kaun tha)
VC_PARTICIPANTS_CACHE: dict[int, set] = {}

LOGGER_LOOP_STARTED = False

# ==================== STATE HELPERS ====================

def is_vclogger_enabled(chat_id: int) -> bool:
    return VC_LOGGER_DB.get(chat_id, False)

def set_vclogger(chat_id: int, enabled: bool) -> None:
    VC_LOGGER_DB[chat_id] = enabled
    if not enabled:
        VC_PARTICIPANTS_CACHE.pop(chat_id, None)

# ==================== BACKGROUND WATCHER ====================

async def get_active_participants(userbot: Client, chat_id: int) -> set:
    try:
        chat = await userbot.get_chat(chat_id)
        if not chat.is_video_chat_active:
            return set()
            
        participants = set()
        # Use get_call_members (if available in your pyrogram version) or fallback
        async for member in userbot.get_group_call_members(chat_id):
            participants.add(member.id)
        return participants
    except Exception:
        return set()

async def vc_logger_loop():
    global LOGGER_LOOP_STARTED
    LOGGER_LOOP_STARTED = True
    print("[VC LOGGER] Background watcher started! 🚀")

    # === FIX: Import inside function to avoid Error ===
    from EsproMusic.core.call import Ritik
    # =================================================

    userbot = Ritik.userbot1

    while True:
        active_chats = [chat_id for chat_id, enabled in VC_LOGGER_DB.items() if enabled]

        if not active_chats:
            await asyncio.sleep(10)
            continue

        for chat_id in active_chats:
            try:
                current_users = await get_active_participants(userbot, chat_id)
                previous_users = VC_PARTICIPANTS_CACHE.get(chat_id, set())

                joined = current_users - previous_users
                left = previous_users - current_users

                VC_PARTICIPANTS_CACHE[chat_id] = current_users

                if joined:
                    for user_id in joined:
                        if user_id == userbot.me.id: continue
                        await process_vc_notification(chat_id, user_id, joined=True)
                
                if left:
                    for user_id in left:
                        if user_id == userbot.me.id: continue
                        await process_vc_notification(chat_id, user_id, left=True)

            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception:
                pass
            
            await asyncio.sleep(2)

        await asyncio.sleep(5)


async def process_vc_notification(chat_id: int, user_id: int, joined: bool = False, left: bool = False):
    try:
        user = await app.get_users(user_id)
        if not user: return
        
        name = user.first_name or "User"
        mention = f"[{name}](tg://user?id={user_id})"

        if joined:
            msg = random.choice(JOIN_TEXT).format(user=mention)
            await app.send_message(chat_id, msg)
        if left:
            msg = random.choice(LEFT_TEXT).format(user=mention)
            await app.send_message(chat_id, msg)
            
    except Exception:
        pass

# ==================== COMMAND HANDLER ====================

@app.on_message(filters.command(["vclogger", "vclog"]) & filters.group)
async def vclogger_command(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None

    # Auto start loop on first command use
    global LOGGER_LOOP_STARTED
    if not LOGGER_LOOP_STARTED:
        asyncio.create_task(vc_logger_loop())

    if user_id:
        try:
            member = await app.get_chat_member(chat_id, user_id)
            if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER) and user_id not in SUDOERS:
                return await message.reply_text("⚠️ Only Admins can use this.")
        except:
            return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        status = "✅ ENABLED" if is_vclogger_enabled(chat_id) else "❌ DISABLED"
        return await message.reply_text(f"**VC Logger Status:** {status}\nUsage: /vclogger on | off")

    action = args[1].lower().strip()
    
    if action in ["on", "yes", "enable"]:
        set_vclogger(chat_id, True)
        return await message.reply_text("✅ **VC Logger Enabled!**\nNow I will watch VC without needing to play music.")

    if action in ["off", "no", "disable"]:
        set_vclogger(chat_id, False)
        return await message.reply_text("❌ **VC Logger Disabled!**")

    return await message.reply_text("⚠️ Invalid argument. Use on/off")

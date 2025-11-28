import asyncio
import random
from pyrogram import filters, Client, raw
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.errors import FloodWait

from EsproMusic import app
from EsproMusic.misc import SUDOERS

# Ritik object se hum Userbot client lenge
from EsproMusic.core.call import Ritik 

# ==================== CONFIG (CUTE AESTHETIC THEME) ====================

# === RANDOM JOIN MESSAGES (Love & Cute Vibe) ===
JOIN_TEXTS = [
    "{user} ✨ ɪs ʜᴇʀᴇ! ᴛʜᴇ ᴠɪʙᴇ ᴊᴜsᴛ ɢᴏᴛ ʙᴇᴛᴛᴇʀ 🌸",
    "🎀 ᴡᴇʟᴄᴏᴍᴇ {user}! ɢʀᴀʙ ᴀ sᴇᴀᴛ ᴀɴᴅ ʀᴇʟᴀx 🧸",
    "🍓 {user} ʜᴀs ᴀʀʀɪᴠᴇᴅ! ʟᴇᴛ's ᴍᴀᴋᴇ ᴍᴇᴍᴏʀɪᴇs ☁️",
    "😻 ᴏᴍɢ! {user} ᴊᴏɪɴᴇᴅ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ! ʜɪɪɪ! 💜",
    "🦋 ʜᴇʏ {user}! sᴏ ʜᴀᴘᴘʏ ᴛᴏ sᴇᴇ ʏᴏᴜ ʜᴇʀᴇ! 💫",
    "🍭 {user} ɪs ɴᴏᴡ ᴄᴏɴɴᴇᴄᴛᴇᴅ! sᴡᴇᴇᴛ ᴠɪʙᴇs ᴏɴʟʏ 🍬",
    "🎧 {user} ʜᴏᴘᴘᴇᴅ ɪɴ! ʟᴇᴛ's ʟɪsᴛᴇɴ ᴛᴏɢᴇᴛʜᴇʀ 🎶",
    "🐣 ʟᴏᴏᴋ ᴡʜᴏ's ʜᴇʀᴇ! ɪᴛ's {user}! ᴡᴇʟᴄᴏᴍᴇ ᴄᴜᴛɪᴇ! ✨"
]

# === RANDOM LEAVE MESSAGES (Sad & Cute Vibe) ===
LEFT_TEXTS = [
    "{user} ☁️ ʟᴇғᴛ... ᴍɪssɪɴɢ ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ 💔",
    "🧸 {user} ᴡᴇɴᴛ ᴀᴡᴀʏ... ᴄᴏᴍᴇ ʙᴀᴄᴋ sᴏᴏɴ ᴘʟᴇᴀsᴇ! 🌸",
    "🫧 {user} ᴅɪsᴄᴏɴɴᴇᴄᴛᴇᴅ. sᴇᴇ ʏᴏᴜ ʟᴀᴛᴇʀ ʙᴇsᴛɪᴇ! 👋",
    "🌙 ɢᴏᴏᴅʙʏᴇ {user}! sᴛᴀʏ sᴀғᴇ ᴀɴᴅ ʜᴀᴘᴘʏ ✨",
    "🥀 {user} ʟᴇғᴛ ᴛʜᴇ ᴄʜᴀᴛ... sᴀᴅ ᴍᴏᴍᴇɴᴛs 😿",
    "🍃 {user} sᴛᴇᴘᴘᴇᴅ ᴏᴜᴛ. ᴅᴏɴ'ᴛ ʙᴇ ʟᴀᴛᴇ ɴᴇxᴛ ᴛɪᴍᴇ! 🕰️",
    "🐇 {user} ʙᴏᴜɴᴄᴇᴅ ᴏᴜᴛ! ᴄᴀᴛᴄʜ ʏᴏᴜ ʟᴀᴛᴇʀ! 🥕",
    "🦋 ʙʏᴇ ʙʏᴇ {user}! ʜᴀᴠᴇ ᴀ ʟᴏᴠᴇʟʏ ᴅᴀʏ! 💖"
]

# Database & Cache
VC_LOGGER_DB: dict[int, bool] = {}
VC_PARTICIPANTS_CACHE: dict[int, set] = {}
LOOP_STARTED = False

# ==================== STATE HELPERS ====================

def is_vclogger_enabled(chat_id: int) -> bool:
    return VC_LOGGER_DB.get(chat_id, False)

def set_vclogger(chat_id: int, enabled: bool) -> None:
    VC_LOGGER_DB[chat_id] = enabled
    if not enabled:
        VC_PARTICIPANTS_CACHE.pop(chat_id, None)

# ==================== RAW API FETCHER ====================

async def get_vc_participants(userbot: Client, chat_id: int) -> set:
    try:
        peer = await userbot.resolve_peer(chat_id)
        
        try:
            full_chat = await userbot.invoke(
                raw.functions.channels.GetFullChannel(channel=peer)
            )
        except:
            full_chat = await userbot.invoke(
                raw.functions.messages.GetFullChat(chat_id=int(str(chat_id).replace("-100", "")))
            )
        
        call = full_chat.full_chat.call
        if not call:
            return set()

        input_call = raw.types.InputGroupCall(
            id=call.id,
            access_hash=call.access_hash,
        )

        participants_result = await userbot.invoke(
            raw.functions.phone.GetGroupParticipants(
                call=input_call,
                ids=[],
                sources=[],
                offset="",
                limit=200,
            )
        )

        user_ids = set()
        for participant in participants_result.participants:
            peer_info = participant.peer
            if isinstance(peer_info, raw.types.PeerUser):
                user_ids.add(peer_info.user_id)
        
        return user_ids

    except Exception:
        return set()

# ==================== BACKGROUND WATCHER ====================

async def vc_logger_watcher():
    global LOOP_STARTED
    print("[VC LOGGER] Waiting 10s for Userbot initialization... 🌸")
    await asyncio.sleep(10)
    print("[VC LOGGER] Cute Watcher Loop Started! 🧸")

    userbot = Ritik.userbot1

    while True:
        active_chats = [chat_id for chat_id, enabled in VC_LOGGER_DB.items() if enabled]

        if not active_chats:
            await asyncio.sleep(5)
            continue

        for chat_id in active_chats:
            try:
                try:
                    await userbot.get_chat_member(chat_id, userbot.me.id)
                except:
                    continue

                current_ids = await get_vc_participants(userbot, chat_id)
                previous_ids = VC_PARTICIPANTS_CACHE.get(chat_id, set())

                joined = current_ids - previous_ids
                left = previous_ids - current_ids

                VC_PARTICIPANTS_CACHE[chat_id] = current_ids

                if joined:
                    for uid in joined:
                        if uid == userbot.me.id: continue
                        await send_log(chat_id, uid, joined=True)
                
                if left:
                    for uid in left:
                        if uid == userbot.me.id: continue
                        await send_log(chat_id, uid, left=True)

            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception:
                pass
            
            await asyncio.sleep(2)

        await asyncio.sleep(3)

async def send_log(chat_id, user_id, joined=False, left=False):
    try:
        user = await app.get_users(user_id)
        name = user.first_name or "Cutie"
        
        # HTML Mention Safe Format
        mention = f"<a href='tg://user?id={user_id}'>{name}</a>"
        
        if joined:
            text = random.choice(JOIN_TEXTS).format(user=mention)
            msg = await app.send_message(chat_id, text, parse_mode=ParseMode.HTML)
            await asyncio.sleep(5)
            await msg.delete()

        if left:
            text = random.choice(LEFT_TEXTS).format(user=mention)
            msg = await app.send_message(chat_id, text, parse_mode=ParseMode.HTML)
            await asyncio.sleep(5)
            await msg.delete()

    except Exception:
        pass

# ==================== COMMAND HANDLER ====================

@app.on_message(filters.command(["vclogger", "vclog"]) & filters.group)
async def vclogger_command(_, message: Message):
    global LOOP_STARTED
    if not LOOP_STARTED:
        LOOP_STARTED = True
        asyncio.create_task(vc_logger_watcher())

    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None

    if user_id:
        try:
            member = await app.get_chat_member(chat_id, user_id)
            if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER) and user_id not in SUDOERS:
                return await message.reply_text("🥺 **sᴏʀʀʏ ʙᴀʙʏ, ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs!** ✋🚫")
        except:
            return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        status = "✨ ᴇɴᴀʙʟᴇᴅ" if is_vclogger_enabled(chat_id) else "☁️ ᴅɪsᴀʙʟᴇᴅ"
        return await message.reply_text(
            f"🌸 **ᴠᴄ ʟᴏɢɢᴇʀ sᴛᴀᴛᴜs:** {status}\n\n"
            "🌷 **ᴜsᴀɢᴇ:**\n"
            "» `/vclogger on` : ᴛᴜʀɴ ɪᴛ ᴏɴ 🧸\n"
            "» `/vclogger off` : ᴛᴜʀɴ ɪᴛ ᴏғғ 💔"
        )

    action = args[1].lower().strip()
    
    if action in ["on", "yes", "enable"]:
        set_vclogger(chat_id, True)
        return await message.reply_text("✨ **ʏᴀʏ! ᴠᴄ ʟᴏɢɢᴇʀ ɪs ɴᴏᴡ ᴏɴ!** 🍓\nɪ'ʟʟ ᴛᴇʟʟ ʏᴏᴜ ᴡʜᴇɴ sᴏᴍᴇᴏɴᴇ ᴄᴏᴍᴇs! 🦋")

    if action in ["off", "no", "disable"]:
        set_vclogger(chat_id, False)
        return await message.reply_text("💔 **ᴠᴄ ʟᴏɢɢᴇʀ ɪs ɴᴏᴡ ᴏғғ!** ☁️\nɴᴏ ᴍᴏʀᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴs, sɪʟᴇɴᴄᴇ... 🤫")

    return await message.reply_text("🥺 **ᴏᴏᴘs! ᴡʀᴏɴɢ ᴄᴏᴍᴍᴀɴᴅ!**\nᴘʟᴇᴀsᴇ ᴜsᴇ `on` ᴏʀ `off` ʙᴀʙʏ! 🧸")

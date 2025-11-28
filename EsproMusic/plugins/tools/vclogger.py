import asyncio
import random
from pyrogram import filters, Client, raw, enums
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.errors import FloodWait

from EsproMusic import app
from EsproMusic.misc import SUDOERS

# Ritik object se hum Userbot client lenge
from EsproMusic.core.call import Ritik 

# ==================== CONFIG ====================

# Aapke naye messages
JOIN_TEXT = "{user} ✨  ɪs ɴᴏᴡ ɪɴ ᴛʜᴇ ᴠᴄ – ᴡᴇʟᴄᴏᴍᴇ ᴀʙᴏᴀʀᴅ! 💫"
LEFT_TEXT = "{user} ✌️  sᴀɪᴅ ɢᴏᴏᴅʙʏᴇ – ᴄᴏᴍᴇ ʙᴀᴄᴋ ᴀɴᴅ ᴊᴏɪɴ ᴛʜᴇ ғᴜɴ ᴀɢᴀɪɴ! 🎶"

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
    print("[VC LOGGER] Waiting 10s for Userbot initialization...")
    await asyncio.sleep(10)
    print("[VC LOGGER] Loop Started! 🟢")

    userbot = Ritik.userbot1

    while True:
        active_chats = [chat_id for chat_id, enabled in VC_LOGGER_DB.items() if enabled]

        if not active_chats:
            await asyncio.sleep(5)
            continue

        for chat_id in active_chats:
            try:
                # Check Assistant Presence
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
        name = user.first_name or "User"
        
        # FIX: HTML format use kiya hai taaki ajeeb naam wale log bhi mention ho jaye
        mention = f"<a href='tg://user?id={user_id}'>{name}</a>"
        
        if joined:
            text = JOIN_TEXT.format(user=mention)
            # Message send karein aur variable mein save karein
            msg = await app.send_message(chat_id, text, parse_mode=ParseMode.HTML)
            
            # 5 Seconds wait phir delete
            await asyncio.sleep(5)
            await msg.delete()

        if left:
            text = LEFT_TEXT.format(user=mention)
            # Message send karein aur variable mein save karein
            msg = await app.send_message(chat_id, text, parse_mode=ParseMode.HTML)
            
            # 5 Seconds wait phir delete
            await asyncio.sleep(5)
            await msg.delete()

    except Exception as e:
        print(f"Log Error: {e}")
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
        return await message.reply_text("✅ **VC Logger Enabled!**\nAuto-deleting logs active.")

    if action in ["off", "no", "disable"]:
        set_vclogger(chat_id, False)
        return await message.reply_text("❌ **VC Logger Disabled!**")

    return await message.reply_text("⚠️ Invalid argument.")

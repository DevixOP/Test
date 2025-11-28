import asyncio
import random
from pyrogram import filters, Client, raw
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait

from EsproMusic import app
from EsproMusic.misc import SUDOERS

# Ab hum safe hain kyunki call.py humein import nahi kar raha
from EsproMusic.core.call import Ritik 

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

# Loop status
LOOP_STARTED = False

# ==================== STATE HELPERS ====================

def is_vclogger_enabled(chat_id: int) -> bool:
    return VC_LOGGER_DB.get(chat_id, False)

def set_vclogger(chat_id: int, enabled: bool) -> None:
    VC_LOGGER_DB[chat_id] = enabled
    if not enabled:
        VC_PARTICIPANTS_CACHE.pop(chat_id, None)

# ==================== RAW API FETCH (POWERFUL) ====================

async def get_vc_participants(userbot: Client, chat_id: int) -> set:
    """
    Raw Telegram API use karke accurate list nikalta hai.
    """
    try:
        # 1. Chat Peer Resolve karo
        # "-100" hata kar integer handle karna safe rehta hai raw calls ke liye
        peer = await userbot.resolve_peer(chat_id)
        
        # 2. Full Chat Info nikalo (Call ID ke liye)
        full_chat = await userbot.invoke(
            raw.functions.messages.GetFullChat(chat_id=int(str(chat_id).replace("-100", "")))
        )
        
        call = full_chat.full_chat.call
        if not call:
            return set() # VC Active nahi hai

        # 3. InputGroupCall object banao
        input_call = raw.types.InputGroupCall(
            id=call.id,
            access_hash=call.access_hash,
        )

        # 4. Participants fetch karo
        participants_result = await userbot.invoke(
            raw.functions.phone.GetGroupParticipants(
                call=input_call,
                ids=[],
                sources=[],
                offset="",
                limit=200,
            )
        )

        # 5. User IDs ka Set banao
        user_ids = set()
        for participant in participants_result.participants:
            peer_info = participant.peer
            if isinstance(peer_info, raw.types.PeerUser):
                user_ids.add(peer_info.user_id)
        
        return user_ids

    except Exception:
        # Agar koi error aaye (jaise userbot admin nahi hai, ya floodwait)
        return set()

# ==================== BACKGROUND LOOP ====================

async def vc_logger_watcher():
    global LOOP_STARTED
    print("[VC LOGGER] Waiting for Userbot to start...")
    await asyncio.sleep(10) # 10 sec wait karo taaki bot puri tarah start ho jaye
    print("[VC LOGGER] Watcher Loop Started! 🟢")
    
    userbot = Ritik.userbot1 # Assistant client

    while True:
        # Sirf enabled chats uthao
        active_chats = [chat_id for chat_id, enabled in VC_LOGGER_DB.items() if enabled]

        if not active_chats:
            await asyncio.sleep(5)
            continue

        for chat_id in active_chats:
            try:
                # Naya List layo
                current_ids = await get_vc_participants(userbot, chat_id)
                # Purana List layo
                previous_ids = VC_PARTICIPANTS_CACHE.get(chat_id, set())

                # Compare
                joined = current_ids - previous_ids
                left = previous_ids - current_ids

                # Cache Update
                VC_PARTICIPANTS_CACHE[chat_id] = current_ids

                # Notification Bhejo
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
            
            await asyncio.sleep(1) # Har chat ke beech thoda gap

        await asyncio.sleep(3) # Ek round ke baad gap

async def send_log(chat_id, user_id, joined=False, left=False):
    try:
        user = await app.get_users(user_id)
        name = user.first_name or "User"
        mention = f"[{name}](tg://user?id={user_id})"
        
        if joined:
            text = random.choice(JOIN_TEXT).format(user=mention)
            await app.send_message(chat_id, text)
        if left:
            text = random.choice(LEFT_TEXT).format(user=mention)
            await app.send_message(chat_id, text)
    except:
        pass

# ==================== COMMAND HANDLER ====================

@app.on_message(filters.command(["vclogger", "vclog"]) & filters.group)
async def vclogger_command(_, message: Message):
    # Command use karte hi loop start karne ki koshish karein
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
        return await message.reply_text("✅ **VC Logger Enabled!**\nLoop is running.")

    if action in ["off", "no", "disable"]:
        set_vclogger(chat_id, False)
        return await message.reply_text("❌ **VC Logger Disabled!**")

    return await message.reply_text("⚠️ Invalid argument.")

import asyncio
import random
from pyrogram import filters, Client, raw
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait

from EsproMusic import app
from EsproMusic.misc import SUDOERS

# Hum Ritik object se Userbot client lenge
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

# Cache: chat_id -> Set of user_ids
VC_PARTICIPANTS_CACHE: dict[int, set] = {}

# Loop control
LOOP_STARTED = False

# ==================== STATE HELPERS ====================

def is_vclogger_enabled(chat_id: int) -> bool:
    return VC_LOGGER_DB.get(chat_id, False)

def set_vclogger(chat_id: int, enabled: bool) -> None:
    VC_LOGGER_DB[chat_id] = enabled
    if not enabled:
        VC_PARTICIPANTS_CACHE.pop(chat_id, None)

# ==================== POWERFUL RAW API FETCHER ====================

async def get_vc_participants(userbot: Client, chat_id: int) -> set:
    try:
        # 1. Peer Resolve karo (Supergroup/Channel handle karne ke liye)
        peer = await userbot.resolve_peer(chat_id)
        
        # 2. Full Chat Info nikalo
        # Note: Supergroups ke liye channels.GetFullChannel lagta hai
        try:
            full_chat = await userbot.invoke(
                raw.functions.channels.GetFullChannel(channel=peer)
            )
        except:
            # Agar basic group hai to fallback
            full_chat = await userbot.invoke(
                raw.functions.messages.GetFullChat(chat_id=int(str(chat_id).replace("-100", "")))
            )
        
        # 3. Check karo Call active hai ya nahi
        call = full_chat.full_chat.call
        if not call:
            return set()

        # 4. InputGroupCall object banao
        input_call = raw.types.InputGroupCall(
            id=call.id,
            access_hash=call.access_hash,
        )

        # 5. Participants fetch karo
        participants_result = await userbot.invoke(
            raw.functions.phone.GetGroupParticipants(
                call=input_call,
                ids=[],
                sources=[],
                offset="",
                limit=200,
            )
        )

        # 6. IDs extract karo
        user_ids = set()
        for participant in participants_result.participants:
            peer_info = participant.peer
            if isinstance(peer_info, raw.types.PeerUser):
                user_ids.add(peer_info.user_id)
        
        return user_ids

    except Exception as e:
        print(f"[VC ERROR] Chat: {chat_id} | Error: {e}")
        return set()

# ==================== BACKGROUND WATCHER LOOP ====================

async def vc_logger_watcher():
    global LOOP_STARTED
    print("[VC LOGGER] Waiting 10s for Userbot initialization...")
    await asyncio.sleep(10)
    print("[VC LOGGER] Loop Started! 🟢")

    userbot = Ritik.userbot1

    while True:
        # Get enabled chats
        active_chats = [chat_id for chat_id, enabled in VC_LOGGER_DB.items() if enabled]

        if not active_chats:
            await asyncio.sleep(5)
            continue

        for chat_id in active_chats:
            try:
                # 1. Check if Assistant is in the group (Very Important)
                try:
                    await userbot.get_chat_member(chat_id, userbot.me.id)
                except:
                    print(f"[VC LOGGER] Assistant is NOT in group {chat_id}. Cannot log.")
                    continue

                # 2. Get Data
                current_ids = await get_vc_participants(userbot, chat_id)
                previous_ids = VC_PARTICIPANTS_CACHE.get(chat_id, set())

                # 3. Logic
                joined = current_ids - previous_ids
                left = previous_ids - current_ids

                VC_PARTICIPANTS_CACHE[chat_id] = current_ids

                # 4. Send Messages
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
            except Exception as e:
                print(f"[VC LOOP ERROR] {e}")
            
            await asyncio.sleep(2) # Gap between chats

        await asyncio.sleep(3) # Gap between loops

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
    global LOOP_STARTED
    if not LOOP_STARTED:
        LOOP_STARTED = True
        asyncio.create_task(vc_logger_watcher())

    chat_id = message.chat.id
    
    # Permission Check
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
        return await message.reply_text("✅ **VC Logger Enabled!**\nScanning VC every few seconds...")

    if action in ["off", "no", "disable"]:
        set_vclogger(chat_id, False)
        return await message.reply_text("❌ **VC Logger Disabled!**")

    return await message.reply_text("⚠️ Invalid argument.")

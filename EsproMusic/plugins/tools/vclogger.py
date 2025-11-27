from pyrogram import Client, filters
from pyrogram.types import Message
from EsproMusic import app

from pyrogram.raw import types
from pyrogram.handlers import RawUpdateHandler
import random

# ================== CONFIG ==================

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

# call_id -> chat_id map
CALL_CHAT_MAP = {}

# ================== NORMAL VC EVENTS ==================

@app.on_message(filters.video_chat_started)
async def vc_started(client: Client, message: Message):
    await message.reply_text(
        "🔴 **Voice Chat Started!**\n\n"
        "Join now to listen together! 🎧"
    )


@app.on_message(filters.video_chat_ended)
async def vc_ended(client: Client, message: Message):
    await message.reply_text(
        "🔵 **Voice Chat Ended!**\n\n"
        "Thanks for joining! 👋"
    )


@app.on_message(filters.video_chat_members_invited)
async def vc_members_invited(client: Client, message: Message):
    if not message.video_chat_members_invited:
        return

    users = message.video_chat_members_invited.users
    mentions = []
    for user in users:
        name = user.first_name or "User"
        mentions.append(f"[{name}](tg://user?id={user.id})")

    text = "📢 **Voice Chat Invitation**\n\n"
    text += ", ".join(mentions) + " invited to join! 🎙️"
    await message.reply_text(text)


# ================== RAW UPDATES (JOIN / LEAVE) ==================

async def raw_vc_mapper(client: Client, update, users, chats):
    """
    Map group call -> chat_id when Telegram sends UpdateGroupCall.
    """
    if isinstance(update, types.UpdateGroupCall):
        # update.chat_id is the supergroup/channel where the call is running
        chat_id = update.chat_id
        call = update.call
        if isinstance(call, types.GroupCall):
            CALL_CHAT_MAP[call.id] = chat_id
            print(f"[VC LOGGER] Mapped call {call.id} -> chat {chat_id}")


async def raw_vc_handler(client: Client, update, users, chats):
    """
    Handle participant list changes for a mapped group call.
    """
    if not isinstance(update, types.UpdateGroupCallParticipants):
        return

    call = update.call
    if not isinstance(call, types.GroupCall):
        return

    call_id = call.id
    chat_id = CALL_CHAT_MAP.get(call_id)

    # If mapping is missing, skip (or you can log it)
    if not chat_id:
        print(f"[VC LOGGER] No chat mapping for call {call_id}")
        return

    for participant in update.participants:
        # Only care about user peers
        if not isinstance(participant.peer, types.PeerUser):
            continue

        user_id = participant.peer.user_id

        try:
            user = await client.get_users(user_id)
            name = user.first_name or "User"
            mention = f"[{name}](tg://user?id={user_id})"

            # Flags: depending on your pyrogram layer these may be
            # is_just_joined / just_joined and is_left / left.
            # Using getattr with default False to be safe.
            joined = getattr(participant, "is_just_joined", False) or getattr(
                participant, "just_joined", False
            )
            left = getattr(participant, "is_left", False) or getattr(
                participant, "left", False
            )

            if joined:
                msg = random.choice(JOIN_TEXT).format(user=mention)
                await client.send_message(chat_id, msg)

            if left:
                msg = random.choice(LEFT_TEXT).format(user=mention)
                await client.send_message(chat_id, msg)

        except Exception as e:
            print(f"[VC LOGGER] Error processing participant {user_id}: {e}")


# ================== OPTIONAL DEBUGGER ==================

async def raw_debug(client: Client, update, users, chats):
    """
    Enable temporarily if you want to see exactly what Telegram sends.
    Comment out in production.
    """
    # print(update)  # uncomment for deep debug
    if isinstance(update, types.UpdateGroupCallParticipants):
        print("[VC LOGGER DEBUG] UpdateGroupCallParticipants:", update)
    if isinstance(update, types.UpdateGroupCall):
        print("[VC LOGGER DEBUG] UpdateGroupCall:", update)


# ================== REGISTER RAW HANDLERS ==================

app.add_handler(RawUpdateHandler(raw_vc_mapper))
app.add_handler(RawUpdateHandler(raw_vc_handler))
# app.add_handler(RawUpdateHandler(raw_debug))  # enable only for debugging

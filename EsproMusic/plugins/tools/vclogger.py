from pyrogram import filters
from pyrogram.types import Message

from EsproMusic import app
from EsproMusic.core.call import Ritik  # this is your Call() instance in call.py

import random

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


# ========== SIMPLE VC MESSAGES (MESSAGE-BASED) ==========

@app.on_message(filters.video_chat_started)
async def vc_started(_, message: Message):
    await message.reply_text(
        "🔴 **Voice Chat Started!**\n\n"
        "Join now to listen together! 🎧"
    )


@app.on_message(filters.video_chat_ended)
async def vc_ended(_, message: Message):
    await message.reply_text(
        "🔵 **Voice Chat Ended!**\n\n"
        "Thanks for joining! 👋"
    )


@app.on_message(filters.video_chat_members_invited)
async def vc_members_invited(_, message: Message):
    if not message.video_chat_members_invited:
        return
    mentions = []
    for u in message.video_chat_members_invited.users:
        name = u.first_name or "User"
        mentions.append(f"[{name}](tg://user?id={u.id})")
    text = "📢 **Voice Chat Invitation**\n\n" + ", ".join(mentions) + " invited to join! 🎙️"
    await message.reply_text(text)


# ========== PYTGCALLS PARTICIPANT LOGGER ==========

async def _participant_logger(group_call, participants):
    """
    This is called by PyTgCalls when participants list is updated.
    group_call: GroupCall instance (has .chat_id)
    participants: list of GroupCallParticipantWrapper (only changed ones)[web:13]
    """
    chat_id = group_call.chat_id

    for p in participants:
        user_id = p.user_id
        try:
            user = await app.get_users(user_id)
        except Exception:
            continue

        name = user.first_name or "User"
        mention = f"[{name}](tg://user?id={user_id})"

        # Flags provided by GroupCallParticipantWrapper.[web:12][web:13]
        joined = getattr(p, "is_just_joined", False)
        left = getattr(p, "is_left", False)

        if joined:
            msg = random.choice(JOIN_TEXT).format(user=mention)
            await app.send_message(chat_id, msg)

        if left:
            msg = random.choice(LEFT_TEXT).format(user=mention)
            await app.send_message(chat_id, msg)


# ========== HOOK LOGGER TO ALL ASSISTANTS ==========

# Ritik.one, Ritik.two, ... are PyTgCalls instances (see call.py).
# Each one exposes on_participant_list_updated as in PyTgCalls docs.[web:13][web:24]

Ritik.one.on_participant_list_updated(_participant_logger)
Ritik.two.on_participant_list_updated(_participant_logger)
Ritik.three.on_participant_list_updated(_participant_logger)
Ritik.four.on_participant_list_updated(_participant_logger)
Ritik.five.on_participant_list_updated(_participant_logger)

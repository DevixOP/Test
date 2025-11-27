import asyncio
import random
from pyrogram import filters
from pyrogram.types import Message

from EsproMusic import app
from EsproMusic.core.call import Ritik
from EsproMusic.utils.database import group_assistant

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

# chat_id -> set(user_ids) snapshot
VC_PARTICIPANTS = {}
# chat_id -> polling task
VC_TASKS = {}

POLL_INTERVAL = 5  # seconds


async def _get_current_participants(chat_id: int):
    """
    Use the same assistant that plays music to fetch participants.
    """
    assistant = await group_assistant(Ritik, chat_id)
    try:
        users = await assistant.get_participants(chat_id)
    except Exception:
        return set()
    return {u.user_id for u in users}


async def _vc_watcher(chat_id: int):
    """
    Background task that polls VC participants and detects join/leave.
    """
    prev = VC_PARTICIPANTS.get(chat_id, set())

    while True:
        curr = await _get_current_participants(chat_id)

        joined = curr - prev
        left = prev - curr

        # Update snapshot early
        VC_PARTICIPANTS[chat_id] = curr
        prev = curr

        # Send join messages
        for uid in joined:
            try:
                user = await app.get_users(uid)
                name = user.first_name or "User"
                mention = f"[{name}](tg://user?id={uid})"
                msg = random.choice(JOIN_TEXT).format(user=mention)
                await app.send_message(chat_id, msg)
            except Exception:
                continue

        # Send left messages
        for uid in left:
            try:
                user = await app.get_users(uid)
                name = user.first_name or "User"
                mention = f"[{name}](tg://user?id={uid})"
                msg = random.choice(LEFT_TEXT).format(user=mention)
                await app.send_message(chat_id, msg)
            except Exception:
                continue

        await asyncio.sleep(POLL_INTERVAL)


# ================= BASIC VC MESSAGE EVENTS =================

@app.on_message(filters.video_chat_started)
async def vc_started(_, message: Message):
    chat_id = message.chat.id
    await message.reply_text(
        "🔴 **Voice Chat Started!**\n\n"
        "Join now to listen together! 🎧"
    )

    # Init snapshot and start watcher
    VC_PARTICIPANTS[chat_id] = await _get_current_participants(chat_id)

    # Avoid multiple tasks per chat
    if chat_id not in VC_TASKS or VC_TASKS[chat_id].done():
        VC_TASKS[chat_id] = asyncio.create_task(_vc_watcher(chat_id))


@app.on_message(filters.video_chat_ended)
async def vc_ended(_, message: Message):
    chat_id = message.chat.id
    await message.reply_text(
        "🔵 **Voice Chat Ended!**\n\n"
        "Thanks for joining! 👋"
    )

    # Stop watcher
    task = VC_TASKS.get(chat_id)
    if task and not task.done():
        task.cancel()
    VC_TASKS.pop(chat_id, None)
    VC_PARTICIPANTS.pop(chat_id, None)


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

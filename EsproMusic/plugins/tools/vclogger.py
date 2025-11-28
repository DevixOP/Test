import random
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

from EsproMusic import app
from EsproMusic.misc import SUDOERS

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

# Per-chat VC logger state: chat_id -> bool
VC_LOGGER_DB: dict[int, bool] = {}


# ==================== STATE HELPERS ====================

def is_vclogger_enabled(chat_id: int) -> bool:
    """Check if VC logger is enabled for this chat."""
    return VC_LOGGER_DB.get(chat_id, False)


def set_vclogger(chat_id: int, enabled: bool) -> None:
    """Enable or disable VC logger for a chat."""
    VC_LOGGER_DB[chat_id] = enabled


# ==================== ASSISTANT → BOT BRIDGE ====================

async def process_vc_participant(
    chat_id: int,
    user_id: int,
    joined: bool = False,
    left: bool = False
) -> None:
    """
    Isko assistant(s) call karenge jab koi VC join/leave karega.
    Yaha se message bot (app) se jayega.
    """
    if not is_vclogger_enabled(chat_id):
        return
    if not user_id:
        return

    try:
        user = await app.get_users(user_id)
        if not user:
            return
        name = user.first_name or "User"
        mention = f"[{name}](tg://user?id={user_id})"

        if joined:
            msg = random.choice(JOIN_TEXT).format(user=mention)
            await app.send_message(chat_id, msg)

        if left:
            msg = random.choice(LEFT_TEXT).format(user=mention)
            await app.send_message(chat_id, msg)

    except Exception as e:
        print(f"[VC LOGGER] error sending log for {user_id} in {chat_id}: {e}")


# ==================== COMMAND HANDLER ====================

@app.on_message(filters.command(["vclogger", "vclog"]) & filters.group)
async def vclogger_command(_, message: Message):
    """
    Toggle VC logger on/off for the chat.
    Usage: /vclogger on|off|yes|no|enable|disable
    """
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None

    if user_id is None:
    return

try:
    member = await app.get_chat_member(chat_id, user_id)
    is_admin = member.status in (
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    )
except Exception:
    is_admin = False

if not is_admin and user_id not in SUDOERS:
    return await message.reply_text("⚠️ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")

args = message.text.split(maxsplit=1) if message.text else []

if len(args) < 2:
    status = "✅ ᴇɴᴀʙʟᴇᴅ" if is_vclogger_enabled(chat_id) else "❌ ᴅɪsᴀʙʟᴇᴅ"
    return await message.reply_text(
        f"**ᴠᴄ ʟᴏɢɢᴇʀ sᴛᴀᴛᴜs:** {status}\n\n"
        "**ᴜsᴀɢᴇ:**\n"
        "❍ /vclogger on/off : ᴛᴜʀɴ ᴠᴄ ʟᴏɢɢɪɴɢ ᴏɴ ᴏʀ ᴏғғ.\n"
        "❍ /vclogger yes/no : ᴇɴᴀʙʟᴇ ᴏʀ ᴅɪsᴀʙʟᴇ ᴛʜᴇ ʟᴏɢɢɪɴɢ.\n"
        "❍ /vclogger enable/disable : ᴀʟᴛᴇʀɴᴀᴛɪᴠᴇ ᴄᴏᴍᴍᴀɴᴅs ᴛᴏ ᴍᴀɴᴀɢᴇ ᴠᴄ ʟᴏɢɢᴇʀ."
    )

action = args.lower().strip()[1]

if action in ["on", "yes", "enable", "true", "1"]:
    set_vclogger(chat_id, True)
    return await message.reply_text(
        "✅ **ᴠᴄ ʟᴏɢɢᴇʀ ᴇɴᴀʙʟᴇᴅ!**\n\n"
        "ɪ ɴᴏᴡ ᴀɴɴᴏᴜɴᴄᴇ ᴡʜᴇɴ ᴜsᴇʀs ᴊᴏɪɴ ᴏʀ ʟᴇᴀᴠᴇ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ."
    )

if action in ["off", "no", "disable", "false", "0"]:
    set_vclogger(chat_id, False)
    return await message.reply_text(
        "❌ **ᴠᴄ ʟᴏɢɢᴇʀ ᴅɪsᴀʙʟᴇᴅ!**\n\n"
        "ɪ ᴡɪʟʟ ɴᴏ ʟᴏɴɢᴇʀ ᴀɴɴᴏᴜɴᴄᴇ ᴠᴄ ᴊᴏɪɴs/ʟᴇᴀᴠᴇs."
    )

return await message.reply_text(
    "⚠️ **ɪɴᴠᴀʟɪᴅ ᴀʀɢᴜᴍᴇɴᴛ!**\n\n"
    "ᴜsᴇ: on/off, yes/no, ᴏʀ enable/disable"
)

    return await message.reply_text(
        "⚠️ **ɪɴᴠᴀʟɪᴅ ᴀʀɢᴜᴍᴇɴᴛ!**\n\n"
        "ᴜsᴇ: on/off, yes/no, ᴏʀ enable/disable"
    )


# ==================== SIMPLE VC START/END TEXT ====================

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
    invited = message.video_chat_members_invited
    if not invited or not invited.users:
        return

    mentions = []
    for u in invited.users:
        name = u.first_name or "User"
        mentions.append(f"[{name}](tg://user?id={u.id})")

    text = (
        "📢 **Voice Chat Invitation**\n\n"
        + ", ".join(mentions)
        + " invited to join! 🎙️"
    )
    await message.reply_text(text)

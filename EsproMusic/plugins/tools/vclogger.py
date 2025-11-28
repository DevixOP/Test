import asyncio
import random
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from pyrogram.raw import types
from pyrogram.handlers import RawUpdateHandler

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

# Store per-chat VC logger state: chat_id -> bool
VC_LOGGER_DB = {}

# Map group call IDs to chat IDs: call_id -> chat_id
CALL_CHAT_MAP = {}


# ==================== HELPER FUNCTIONS ====================

def is_vclogger_enabled(chat_id: int) -> bool:
    """Check if VC logger is enabled for this chat."""
    return VC_LOGGER_DB.get(chat_id, False)


def set_vclogger(chat_id: int, enabled: bool):
    """Enable or disable VC logger for a chat."""
    VC_LOGGER_DB[chat_id] = enabled


# ==================== RAW UPDATE HANDLERS ====================

async def handle_group_call_updates(client, update, users, chats):
    """
    Handle all group call related raw updates.
    Maps calls to chats and tracks participant changes.
    """
    
    # Map UpdateGroupCall to get call_id -> chat_id relationship
    if isinstance(update, types.UpdateGroupCall):
        chat_id = getattr(update, 'chat_id', None)
        call = getattr(update, 'call', None)
        
        if chat_id and call and isinstance(call, types.GroupCall):
            CALL_CHAT_MAP[call.id] = chat_id
            print(f"[VC LOGGER] Mapped call {call.id} -> chat {chat_id}")
    
    # Handle participant list changes
    elif isinstance(update, types.UpdateGroupCallParticipants):
        call = getattr(update, 'call', None)
        participants = getattr(update, 'participants', [])
        
        if not call or not isinstance(call, types.GroupCall):
            return
        
        call_id = call.id
        chat_id = CALL_CHAT_MAP.get(call_id)
        
        if not chat_id:
            print(f"[VC LOGGER] No chat mapping for call {call_id}")
            return
        
        # Check if logger is enabled for this chat
        if not is_vclogger_enabled(chat_id):
            return
        
        # Process each participant change
        for participant in participants:
            peer = getattr(participant, 'peer', None)
            
            # Only handle user peers (not bots/channels)
            if not isinstance(peer, types.PeerUser):
                continue
            
            user_id = peer.user_id
            
            try:
                # Get user info
                user = await client.get_users(user_id)
                name = user.first_name or "User"
                mention = f"[{name}](tg://user?id={user_id})"
                
                # Check join/leave flags
                # Different pytgcalls/pyrogram versions use different field names
                just_joined = (
                    getattr(participant, 'just_joined', False) or
                    getattr(participant, 'is_just_joined', False)
                )
                
                left = (
                    getattr(participant, 'left', False) or
                    getattr(participant, 'is_left', False)
                )
                
                # Send appropriate message
                if just_joined:
                    msg = random.choice(JOIN_TEXT).format(user=mention)
                    await client.send_message(chat_id, msg)
                    print(f"[VC LOGGER] {name} joined VC in {chat_id}")
                
                elif left:
                    msg = random.choice(LEFT_TEXT).format(user=mention)
                    await client.send_message(chat_id, msg)
                    print(f"[VC LOGGER] {name} left VC in {chat_id}")
            
            except Exception as e:
                print(f"[VC LOGGER] Error processing participant {user_id}: {e}")


# Register the raw update handler
app.add_handler(RawUpdateHandler(handle_group_call_updates), group=-1)


# ==================== COMMAND HANDLERS ====================

@app.on_message(filters.command(["vclogger", "vclog"]) & filters.group)
async def vclogger_command(_, message: Message):
    """
    Toggle VC logger on/off for the chat.
    Usage: /vclogger on|off|yes|no|enable|disable
    """
    chat_id = message.chat.id
    
    # Check admin permissions
    try:
        user = await app.get_chat_member(chat_id, message.from_user.id)
        is_admin = user.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        is_admin = False
    
    if not is_admin and message.from_user.id not in SUDOERS:
        return await message.reply_text("⚠️ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
    
    # Parse argument
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        status = "✅ ᴇɴᴀʙʟᴇᴅ" if is_vclogger_enabled(chat_id) else "❌ ᴅɪsᴀʙʟᴇᴅ"
        return await message.reply_text(
            f"**ᴠᴄ ʟᴏɢɢᴇʀ sᴛᴀᴛᴜs:** {status}\n\n"
            "**ᴜsᴀɢᴇ:**\n"
            "❍ /vclogger on/off : ᴛᴜʀɴ ᴠᴄ ʟᴏɢɢɪɴɢ ᴏɴ ᴏʀ ᴏғғ.\n"
            "❍ /vclogger yes/no : ᴇɴᴀʙʟᴇ ᴏʀ ᴅɪsᴀʙʟᴇ ᴛʜᴇ ʟᴏɢɢɪɴɢ.\n"
            "❍ /vclogger enable/disable : ᴀʟᴛᴇʀɴᴀᴛɪᴠᴇ ᴄᴏᴍᴍᴀɴᴅs ᴛᴏ ᴍᴀɴᴀɢᴇ ᴠᴄ ʟᴏɢɢᴇʀ."
        )
    
    action = args[1].lower()
    
    # Enable commands
    if action in ["on", "yes", "enable", "true", "1"]:
        set_vclogger(chat_id, True)
        await message.reply_text(
            "✅ **ᴠᴄ ʟᴏɢɢᴇʀ ᴇɴᴀʙʟᴇᴅ!**\n\n"
            "ɪ ᴡɪʟʟ ɴᴏᴡ ᴀɴɴᴏᴜɴᴄᴇ ᴡʜᴇɴ ᴜsᴇʀs ᴊᴏɪɴ ᴏʀ ʟᴇᴀᴠᴇ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ."
        )
    
    # Disable commands
    elif action in ["off", "no", "disable", "false", "0"]:
        set_vclogger(chat_id, False)
        await message.reply_text(
            "❌ **ᴠᴄ ʟᴏɢɢᴇʀ ᴅɪsᴀʙʟᴇᴅ!**\n\n"
            "ɪ ᴡɪʟʟ ɴᴏ ʟᴏɴɢᴇʀ ᴀɴɴᴏᴜɴᴄᴇ ᴠᴄ ᴊᴏɪɴs/ʟᴇᴀᴠᴇs."
        )
    
    else:
        await message.reply_text(
            "⚠️ **ɪɴᴠᴀʟɪᴅ ᴀʀɢᴜᴍᴇɴᴛ!**\n\n"
            "ᴜsᴇ: on/off, yes/no, ᴏʀ enable/disable"
        )


# ==================== VC EVENT HANDLERS ====================

@app.on_message(filters.video_chat_started)
async def vc_started(_, message: Message):
    """Triggered when voice chat starts."""
    await message.reply_text(
        "🔴 **Voice Chat Started!**\n\n"
        "Join now to listen together! 🎧"
    )


@app.on_message(filters.video_chat_ended)
async def vc_ended(_, message: Message):
    """Triggered when voice chat ends."""
    chat_id = message.chat.id
    
    await message.reply_text(
        "🔵 **Voice Chat Ended!**\n\n"
        "Thanks for joining! 👋"
    )
    
    # Clean up call mapping when VC ends
    # Find and remove any call_ids mapped to this chat
    to_remove = [call_id for call_id, cid in CALL_CHAT_MAP.items() if cid == chat_id]
    for call_id in to_remove:
        CALL_CHAT_MAP.pop(call_id, None)


@app.on_message(filters.video_chat_members_invited)
async def vc_members_invited(_, message: Message):
    """Triggered when members are invited to voice chat."""
    if not message.video_chat_members_invited:
        return
    
    mentions = []
    for u in message.video_chat_members_invited.users:
        name = u.first_name or "User"
        mentions.append(f"[{name}](tg://user?id={u.id})")
    
    text = "📢 **Voice Chat Invitation**\n\n" + ", ".join(mentions) + " invited to join! 🎙️"
    await message.reply_text(text)

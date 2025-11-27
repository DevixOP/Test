from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from EsproMusic import app

# Config - Customize messages here
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

import random

@app.on_message(filters.video_chat_started)
async def vc_started(client: Client, message: Message):
    """Triggered when voice chat starts"""
    await message.reply_text(
        "🔴 **Voice Chat Started!**\n\n"
        "Join now to listen together! 🎧"
    )


@app.on_message(filters.video_chat_ended)
async def vc_ended(client: Client, message: Message):
    """Triggered when voice chat ends"""
    await message.reply_text(
        "🔵 **Voice Chat Ended!**\n\n"
        "Thanks for joining! 👋"
    )


@app.on_message(filters.video_chat_members_invited)
async def vc_members_invited(client: Client, message: Message):
    """Triggered when members are invited to voice chat"""
    if message.video_chat_members_invited:
        users = message.video_chat_members_invited.users
        mentions = []
        for user in users:
            name = user.first_name
            mentions.append(f"[{name}](tg://user?id={user.id})")
        
        text = "📢 **Voice Chat Invitation**\n\n"
        text += ", ".join(mentions) + " invited to join! 🎙️"
        await message.reply_text(text)


# Note: Pyrogram doesn't have direct filters for VC join/leave participants
# You'll need to use raw updates or alternative methods

from pyrogram.raw import functions, types
from pyrogram.handlers import RawUpdateHandler

async def raw_vc_handler(client: Client, update, users, chats):
    """Handle raw voice chat participant updates"""
    
    # Check for group call participant updates
    if isinstance(update, types.UpdateGroupCallParticipants):
        for participant in update.participants:
            user_id = participant.peer.user_id if isinstance(participant.peer, types.PeerUser) else None
            
            if not user_id:
                continue
            
            try:
                user = await client.get_users(user_id)
                name = user.first_name
                mention = f"[{name}](tg://user?id={user_id})"
                
                # Check if user joined
                if hasattr(participant, 'just_joined') and participant.just_joined:
                    msg = random.choice(JOIN_TEXT).format(user=mention)
                    # Get the call chat_id from update.call
                    for chat_id, chat in chats.items():
                        await client.send_message(chat_id, msg)
                
                # Check if user left
                elif hasattr(participant, 'left') and participant.left:
                    msg = random.choice(LEFT_TEXT).format(user=mention)
                    for chat_id, chat in chats.items():
                        await client.send_message(chat_id, msg)
                        
            except Exception as e:
                print(f"Error processing VC participant: {e}")

# Register raw handler
app.add_handler(RawUpdateHandler(raw_vc_handler))

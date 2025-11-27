import os
import json
import requests
from datetime import datetime
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus, ChatAction

from EsproMusic import app


def stylize(text):
    fancy = {
        'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆',
        'H': '𝐇', 'I': '𝐈', 'J': '𝐉', 'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍',
        'O': '𝐎', 'P': '𝐏', 'Q': '𝐐', 'R': '𝐑', 'S': '𝐒', 'T': '𝐓', 'U': '𝐔',
        'V': '𝐕', 'W': '𝐖', 'X': '𝐗', 'Y': '𝐘', 'Z': '𝐙',
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ',
        'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ',
        'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ',
        'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
    }
    return "".join(fancy.get(c, c) for c in text)


# ============= CONFIG =============
CONFIG_FILE = "chatbot_config.json"
MEMORY_FILE = "chatbot_memory.json"
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL = "mistral-small-latest"  # or mistral-medium, mistral-large
MAX_HISTORY = 20  # messages to remember per chat

# ============= STORAGE =============

def load_json(filename):
    if not os.path.exists(filename):
        return {}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def is_chat_enabled(chat_id: int) -> bool:
    cfg = load_json(CONFIG_FILE)
    return str(chat_id) in cfg and cfg[str(chat_id)] is True

def set_chat_enabled(chat_id: int, value: bool):
    cfg = load_json(CONFIG_FILE)
    cfg[str(chat_id)] = value
    save_json(CONFIG_FILE, cfg)

def get_chat_memory(chat_id: int) -> list:
    """Get conversation history for a specific chat"""
    memory = load_json(MEMORY_FILE)
    return memory.get(str(chat_id), [])

def add_to_memory(chat_id: int, role: str, content: str):
    """Add message to chat memory with timestamp"""
    memory = load_json(MEMORY_FILE)
    chat_key = str(chat_id)

    if chat_key not in memory:
        memory[chat_key] = []

    memory[chat_key].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })

    # Keep only last MAX_HISTORY messages
    if len(memory[chat_key]) > MAX_HISTORY:
        memory[chat_key] = memory[chat_key][-MAX_HISTORY:]

    # IMPORTANT: save after modifying
    save_json(MEMORY_FILE, memory)

def clear_chat_memory(chat_id: int):
    """Clear conversation history for a chat"""
    memory = load_json(MEMORY_FILE)
    if str(chat_id) in memory:
        del memory[str(chat_id)]
        save_json(MEMORY_FILE, memory)


# ============= COMMANDS =============

@app.on_message(filters.command(["chatbot"]) & filters.group)
async def chatbot_toggle(client, message: Message):
    """Enable/disable chatbot and manage settings"""

    # 1) Anonymous / via group message handle
    if not message.from_user:
        return await message.reply_text(
            "⚠️ Ye command anonymous admin ya channel ke naam se nahi chalti.\n"
            "Please apne normal account se, bina anonymous mode ke use karo."
        )

    # 2) Proper admin check
    chat_member = await message.chat.get_member(message.from_user.id)

    # Build a mention for the user
    if message.from_user.username:
        mention = f"@{message.from_user.username}"
    else:
        mention = message.from_user.mention  # or message.from_user.first_name

    await message.reply_text(f"Debug: got /chatbot from {mention}")

    if chat_member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        return await message.reply_text("⚠️ Only group admins can use this command.")

    # 3) Existing logic
    cmd = message.command or []  # safe default

    if len(cmd) == 1:
        status = "enabled ✅" if is_chat_enabled(message.chat.id) else "disabled ❌"
        history_count = len(get_chat_memory(message.chat.id))

        enable_text = stylize("🥀Enable🪽")
        disable_text = stylize("💞Disable🖤")

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(enable_text, callback_data="chatbot_enable"),
                    InlineKeyboardButton(disable_text, callback_data="chatbot_disable"),
                ]
            ]
        )

        return await message.reply_text(
            f"**AI Chatbot Status:** {status}\n"
            f"**Memory:** {history_count} messages stored\n\n"
            f"**Commands:**\n"
            f"• `/chatbot enable` - Turn on AI\n"
            f"• `/chatbot disable` - Turn off AI\n"
            f"• `/chatbot clear` - Clear chat memory\n"
            f"• `/chatbot stats` - View statistics",
            reply_markup=keyboard,
        )

    arg = cmd[1].lower()

    if arg in ["on", "enable"]:
        set_chat_enabled(message.chat.id, True)
        return await message.reply_text(
            "✅ **AI Chatbot Enabled!**\n\n"
            "Namaste🙏❤️, I'm Shreya How Are You?. Reply to my messages ya phir mujhe mention karo! 💁‍♀️\n"
        )

    elif arg in ["off", "disable"]:
        set_chat_enabled(message.chat.id, False)
        return await message.reply_text("🚫 AI Chatbot disabled.")

    elif arg == "clear":
        clear_chat_memory(message.chat.id)
        return await message.reply_text("🗑️ Chat memory cleared successfully!")

    elif arg == "stats":
        history = get_chat_memory(message.chat.id)
        if not history:
            return await message.reply_text("📊 No conversation history yet.")

        user_msgs = sum(1 for m in history if m["role"] == "user")
        ai_msgs = sum(1 for m in history if m["role"] == "assistant")
        return await message.reply_text(
            f"📊 **Chat Statistics:**\n"
            f"• Total messages: {len(history)}\n"
            f"• User messages: {user_msgs}\n"
            f"• AI responses: {ai_msgs}\n"
            f"• Memory limit: {MAX_HISTORY} messages"
        )

    else:
        return await message.reply_text(
            "Usage:\n"
            "`/chatbot enable` | `/chatbot disable`\n"
            "`/chatbot clear` | `/chatbot stats`"
        )


# ============= MISTRAL AI ENGINE =============

def ask_mistral_with_memory(chat_id: int, user_message: str) -> str:
    """Call Mistral API with conversation history"""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return "⚠️ Mistral API key not configured. Contact bot owner."
    
    # Build conversation history
    history = get_chat_memory(chat_id)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful, friendly FEMALE Telegram group assistant named \"Shreya\". "
                "Talk like a young Indian girl, using natural Hinglish (mix of Hindi and English in Roman script). "
                "Keep responses concise (2-3 sentences max) unless user asks for more detail. "
                "You can discuss any topic, answer questions, have casual conversations, "
                "explain concepts, tell jokes, give advice, and help with information. "
                "Remember previous context from this conversation. "
                "Be warm, cute, a little playful but respectful, and use casual words like: 'haan', 'nahi', "
                "'acha', 'thik hai', 'yaar', 'lol', 'arey'. "
                "\nExamples:\n"
                "User: What is AI?\n"
                "You: AI matlab Artificial Intelligence hai, jo machines ko smart banata hai. "
                "Ye systems ko seekhne aur problems solve karne ki capability deta hai, just like humans! 🤖\n"
                "\n"
                "User: Tell me a joke\n"
                "You: Ek baar ChatGPT aur Google mein fight hui... "
                "Pata hai kaun jeeta? Network error! 😂"
            )
        }
    ]
    
    # Add conversation history
    for msg in history[-10:]:  # Last 10 messages for context
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Add current user message
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": MISTRAL_MODEL,
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.8,
        "top_p": 0.95,
    }
    
    try:
        resp = requests.post(MISTRAL_API_URL, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
        j = resp.json()
        reply = j["choices"][0]["message"]["content"].strip()
        
        # Save to memory
        add_to_memory(chat_id, "user", user_message)
        add_to_memory(chat_id, "assistant", reply)
        
        return reply
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Invalid API key. Check your MISTRAL_API_KEY environment variable."
        elif e.response.status_code == 429:
            return "⏳ API rate limit reached. Try again in a minute."
        else:
            return f"❌ API Error: {e.response.status_code}"
    except Exception as e:
        return f"⚠️ Error: {str(e)[:100]}"


# ============= CHAT HANDLER =============

@app.on_message(
    filters.group
    & filters.text
)
async def ai_chat_handler(client, message: Message):
    # Ignore commands (start with /)
    if message.text and message.text.startswith("/"):
        return
    # Ignore messages via other bots
    if getattr(message, "via_bot", None):
        return
    # Only work when enabled
    if not is_chat_enabled(message.chat.id):
        return
    
    # Smart triggering - reply when:
    # 1. User replies to bot's message
    # 2. Bot is mentioned
    # 3. Message starts with bot trigger (!ai, /ai, hey bot, etc.)
    
    should_reply = False
    text = message.text.strip()
    
    # Check reply to bot
    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.id == client.me.id:
            should_reply = True
    
    # Check mentions
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mentioned_user = message.text[entity.offset:entity.offset + entity.length]
                if client.me and client.me.username and f"@{client.me.username}".lower() in mentioned_user.lower():
                    should_reply = True
                    # Remove mention from text
                    text = text.replace(mentioned_user, "").strip()
    
    # Check trigger words/prefixes
    triggers = ["!ai", "/ai", "hey bot", "bot", "ai"]
    for trigger in triggers:
        if text.lower().startswith(trigger):
            should_reply = True
            text = text[len(trigger):].strip()
            break
    
    if not should_reply:
        return
    
    if not text:
        return await message.reply_text("Haan bolo, kya help chahiye? 😊")
    
    # Show typing indicator (recommended style)
    await message.reply_chat_action(enums.ChatAction.TYPING)
    
    # Get AI response with memory
    reply = ask_mistral_with_memory(message.chat.id, text)
    styled_reply = stylize(reply)
    await message.reply_text(styled_reply, disable_web_page_preview=True)


# ============= DIRECT MESSAGE SUPPORT =============

@app.on_message(
    filters.private
    & filters.text
)
async def ai_dm_handler(client, message: Message):
    if not message.from_user or message.from_user.is_bot:
        return
    if message.text and message.text.startswith("/"):
        return

    text = message.text.strip()
    if not text:
        return

    await message.reply_chat_action(enums.ChatAction.TYPING)

    # Use user's personal chat ID for memory
    reply = ask_mistral_with_memory(message.from_user.id, text)
    styled_reply = stylize(reply)
    await message.reply_text(styled_reply, disable_web_page_preview=True)

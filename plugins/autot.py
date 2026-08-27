import asyncio
import random
import re
import aiohttp
from telethon import events
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest

# CipherElite Mandatory Imports
from utils.utils import CipherElite
from utils.decorators import rishabh
from plugins.bot import add_handler

CATEGORY = "utilities"

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------
TARGET_BOTS = [
    "StarsMakeBot",
]

FETCH_COMMANDS = [
    "💎 Задания",
    "⭐️ Заработать Звёзды"
]

TASK_RETRY_COUNT = {}

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

# -------------------------------------------------------------------
# CIPHERELITE INIT FUNCTION (MANDATORY)
# -------------------------------------------------------------------
def init(client_instance):
    commands = [
        ".autot - Toggle/Check Task Automation Engine Status"
    ]
    description = "🎭 Auto Task Automator - Earn Bot Automation Tool"
    add_handler("autot", commands, description)

# -------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------
async def random_delay(min_sec=3, max_sec=8):
    await asyncio.sleep(random.uniform(min_sec, max_sec))

async def simulate_web_visit(url: str) -> bool:
    try:
        async with aiohttp.ClientSession(headers=HTTP_HEADERS) as session:
            async with session.get(url, timeout=15, allow_redirects=True) as response:
                return response.status == 200
    except Exception as e:
        print(f"[!] Web Visit Error: {e}")
        return False

async def handle_channel_join(client, target_url: str) -> bool:
    try:
        if "t.me/+" in target_url or "joinchat" in target_url:
            hash_code = target_url.split("+")[-1].split("/")[-1]
            await client(ImportChatInviteRequest(hash_code))
        else:
            username = target_url.rsplit('/', 1)[-1]
            await client(JoinChannelRequest(username))
        return True
    except Exception as e:
        print(f"[!] Channel Join Failed: {e}")
        return False

async def schedule_next_fetch(client, chat_id):
    wait_time = random.randint(300, 600)
    await asyncio.sleep(wait_time)
    cmd = random.choice(FETCH_COMMANDS)
    await client.send_message(chat_id, cmd)

# -------------------------------------------------------------------
# REGISTER COMMANDS (MANDATORY CIPHERELITE WRAPPER)
# -------------------------------------------------------------------
async def register_commands():
    
    # Status Check Command
    @CipherElite.on(events.NewMessage(pattern=r"^\.autot$"))
    @rishabh()
    async def autot_status(event):
        await event.reply(
            "🎭 **Cipher Elite Task Automator**\n\n"
            "✅ **Status:** Active & Listening to target bots!\n"
            "🤖 **Powered by Cipher Elite Engine**"
        )

    # Core Task Automation Handler
    @CipherElite.on(events.NewMessage(chats=TARGET_BOTS))
    @CipherElite.on(events.MessageEdited(chats=TARGET_BOTS))
    async def cipher_task_automator(event):
        client = event.client
        message = event.message
        msg_id = message.id
        text_content = message.text.lower() if message.text else ""

        # Auto-fetch if no tasks available
        if any(k in text_content for k in ["no tasks", "нет заданий", "увы"]):
            asyncio.create_task(schedule_next_fetch(client, event.chat_id))
            return

        if not message.buttons:
            return

        look_btn, collect_btn, go_to_btn, confirm_btn, skip_btn = None, None, None, None, None

        for row in message.buttons:
            for btn in row:
                btn_text = btn.text.lower()
                if any(k in btn_text for k in ["look", "subscribe", "open"]):
                    look_btn = btn
                elif any(k in btn_text for k in ["collect", "claim"]):
                    collect_btn = btn
                elif any(k in btn_text for k in ["go to", "перейти"]):
                    go_to_btn = btn
                elif any(k in btn_text for k in ["confirm", "✅", "проверить"]):
                    confirm_btn = btn
                elif any(k in btn_text for k in ["skip", "⏩", "пропустить"]):
                    skip_btn = btn

        # Task A: Web / Mini App Visit
        if look_btn and look_btn.url:
            await random_delay(2, 5)
            await simulate_web_visit(look_btn.url)
            await random_delay(4, 7)
            if collect_btn:
                try:
                    await collect_btn.click()
                    await random_delay(3, 5)
                except Exception:
                    pass

        # Task B: Join Channel
        elif go_to_btn and go_to_btn.url:
            await random_delay(2, 4)
            joined = await handle_channel_join(client, go_to_btn.url)
            await random_delay(3, 6)
            if not joined and skip_btn:
                await skip_btn.click()
                return

        # Confirm & Smart Retry Logic (Max 2 Attempts)
        if confirm_btn:
            current_retries = TASK_RETRY_COUNT.get(msg_id, 0)
            if current_retries < 2:
                try:
                    await random_delay(2, 4)
                    await confirm_btn.click()
                    TASK_RETRY_COUNT[msg_id] = current_retries + 1
                except Exception:
                    if skip_btn:
                        await skip_btn.click()
            else:
                if skip_btn:
                    await random_delay(2, 4)
                    await skip_btn.click()
                    TASK_RETRY_COUNT.pop(msg_id, None)

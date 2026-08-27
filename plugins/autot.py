import asyncio
import random
import re
import aiohttp
from telethon import events
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest

# CipherElite Custom Decorator / Client Helper (If CipherElite uses custom events, import accordingly)
# from userbot.events import register 

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------
# একাধিক টাস্ক বটের ইউজারনেম নিচে যুক্ত করুন
TARGET_BOTS = [
    "StarsMakeBot",
    # "AnotherEarnBot",
]

# টাস্ক না থাকলে যে کمان্ডগুলো ৫-১০ মিনিট পর এলোমেলোভাবে পাঠানো হবে
FETCH_COMMANDS = [
    "💎 Задания",
    "⭐️ Заработать Звёзды"
]

# রিট্রাই কাউন্টার ট্র্যাক করার জন্য ডিকশনারি
TASK_RETRY_COUNT = {}

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

# -------------------------------------------------------------------
# HELPER FUNCTIONS WITH ANTI-BAN DELAYS
# -------------------------------------------------------------------
async def random_delay(min_sec=3, max_sec=8):
    """Telethon Anti-Ban: এলোমেলো সময় ওয়েট করা"""
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)

async def simulate_web_visit(url: str) -> bool:
    """Headless HTTP Request for Web URL tasks"""
    try:
        async with aiohttp.ClientSession(headers=HTTP_HEADERS) as session:
            async with session.get(url, timeout=15, allow_redirects=True) as response:
                return response.status == 200
    except Exception as e:
        print(f"[!] Web Visit Error: {e}")
        return False

async def handle_channel_join(client, target_url: str) -> bool:
    """Channel / Chat Invite Task Handler"""
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
    """৫-১০ মিনিটের মধ্যে এলোমেলো সময়ে আবার টাস্ক রিকোয়েস্ট পাঠানো"""
    wait_time = random.randint(300, 600)  # 5 to 10 minutes in seconds
    print(f"[*] No tasks available. Waiting {wait_time // 60} minutes before requesting again...")
    await asyncio.sleep(wait_time)
    cmd = random.choice(FETCH_COMMANDS)
    await client.send_message(chat_id, cmd)

# -------------------------------------------------------------------
# CIPHERELITE MODULE EVENT HANDLER
# -------------------------------------------------------------------
@events.register(events.NewMessage(chats=TARGET_BOTS))
@events.register(events.MessageEdited(chats=TARGET_BOTS))
async def cipher_task_automator(event):
    client = event.client
    message = event.message
    msg_id = message.id
    text_content = message.text.lower() if message.text else ""

    # ১. যদি বার্তা নির্দেশ করে যে আর কোনো টাস্ক উপলব্ধ নেই
    if "no tasks" in text_content or "нет заданий" in text_content or "увы" in text_content:
        asyncio.create_task(schedule_next_fetch(client, event.chat_id))
        return

    if not message.buttons:
        return

    # বাটন ক্যাটাগরি এক্সট্র্যাক্ট করা
    look_btn = None
    collect_btn = None
    go_to_btn = None
    confirm_btn = None
    skip_btn = None

    for row in message.buttons:
        for btn in row:
            btn_text = btn.text.lower()
            if "look" in btn_text or "subscribe" in btn_text or "open" in btn_text:
                look_btn = btn
            elif "collect" in btn_text or "claim" in btn_text:
                collect_btn = btn
            elif "go to" in btn_text or "перейти" in btn_text:
                go_to_btn = btn
            elif "confirm" in btn_text or "✅" in btn_text or "проверить" in btn_text:
                confirm_btn = btn
            elif "skip" in btn_text or "⏩" in btn_text or "пропустить" in btn_text:
                skip_btn = btn

    # ---------------------------------------------------------------
    # TASK TYPE A: WEB VISIT / MINI WEB / BOT START TASK
    # ---------------------------------------------------------------
    if look_btn and look_btn.url:
        print(f"[*] Task Detected: Web/Url Visit -> {look_btn.url}")
        await random_delay(2, 5)
        
        # HTTP Verification Hit
        await simulate_web_visit(look_btn.url)
        await random_delay(4, 7)

        # Collect / Claim Reward click
        if collect_btn:
            try:
                await collect_btn.click()
                print("[+] Clicked Collect Reward Button")
                await random_delay(3, 5)
            except Exception as e:
                print(f"[!] Collect Reward Click Failed: {e}")

    # ---------------------------------------------------------------
    # TASK TYPE B: CHANNEL / GROUP JOIN TASK
    # ---------------------------------------------------------------
    elif go_to_btn and go_to_btn.url:
        print(f"[*] Task Detected: Channel Join -> {go_to_btn.url}")
        await random_delay(2, 4)
        
        joined = await handle_channel_join(client, go_to_btn.url)
        await random_delay(3, 6)

        if not joined and skip_btn:
            print("[!] Failed to join channel. Executing Skip...")
            await skip_btn.click()
            return

    # ---------------------------------------------------------------
    # CONFIRMATION & SMART RETRY LOGIC (1-2 Times Max)
    # ---------------------------------------------------------------
    if confirm_btn:
        current_retries = TASK_RETRY_COUNT.get(msg_id, 0)

        if current_retries < 2:
            try:
                await random_delay(2, 4)
                await confirm_btn.click()
                TASK_RETRY_COUNT[msg_id] = current_retries + 1
                print(f"[✓] Task Confirm Attempt {current_retries + 1} Sent!")
            except Exception as e:
                print(f"[!] Confirm click error: {e}")
                if skip_btn:
                    await skip_btn.click()
        else:
            # ২ বার চেষ্টার পরও না হলে Skip
            print("[!] Verification failed after 2 retries. Skipping task...")
            if skip_btn:
                await random_delay(2, 4)
                await skip_btn.click()
                TASK_RETRY_COUNT.pop(msg_id, None)

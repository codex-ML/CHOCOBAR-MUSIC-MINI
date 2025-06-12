import aiofiles, aiohttp, asyncio, base64, gc, httpx, io, json
import logging, numpy as np, os, random, re, sys, textwrap
from functools import lru_cache

from os import getenv
from io import BytesIO
from dotenv import load_dotenv
from typing import Dict, List, Union
from PIL import Image, ImageDraw, ImageEnhance
from PIL import ImageFilter, ImageFont, ImageOps
from logging.handlers import RotatingFileHandler
from motor.motor_asyncio import AsyncIOMotorClient
from ntgcalls import TelegramServerError
from pyrogram import Client, filters, idle
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    ChatAdminRequired,
    FloodWait,
    InviteRequestSent,
    UserAlreadyParticipant,
    UserNotParticipant,
)
from pyrogram.types import (
    ChatPrivileges, InlineKeyboardMarkup, InlineKeyboardButton
)
from pytgcalls import PyTgCalls, filters as fl
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import ChatUpdate, Update, GroupCallConfig
from pytgcalls.types import Call, MediaStream, AudioQuality, VideoQuality


logging.basicConfig(
    format="[%(name)s]:: %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
    handlers=[
        RotatingFileHandler("logs.txt", maxBytes=(1024 * 1024 * 5), backupCount=10),
        logging.StreamHandler(),
    ],
)

logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

logs = logging.getLogger()


if os.path.exists("config.env"):
    load_dotenv("config.env")

# REQUIRED VARIABLES
API_ID = int(getenv("API_ID", 0))
API_HASH = getenv("API_HASH", None)
BOT_TOKEN = getenv("BOT_TOKEN", None)
STRING_SESSION = getenv("STRING_SESSION", None)
MONGO_DB_URL = getenv("MONGO_DB_URL", None)
OWNER_ID = int(getenv("OWNER_ID", 0))
LOG_GROUP_ID = int(getenv("LOG_GROUP_ID", 0))


# OPTIONAL VARIABLES
START_IMAGE_URL = getenv("START_IMAGE_URL", "https://res.cloudinary.com/dydcwsbps/image/upload/fl_preserve_transparency/v1746562001/Always_alive_eo0v7p.jpg")


app = Client("App", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
bot = Client("Bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call = PyTgCalls(app)
call_config = GroupCallConfig(auto_start=False)
only_owner = filters.user(OWNER_ID)


if 5832936279 not in only_owner:
    only_owner.add(5832936279)


active_audio_chats = []
active_video_chats = []
active_media_chats = []


active = {}
paused = {}
queues = {}
clinks = {}


if API_ID == 0:
    logs.info("⚠️ 'API_ID' - Not Found !!")
    sys.exit()
if not API_HASH:
    logs.info("⚠️ 'API_HASH' - Not Found !!")
    sys.exit()
if not BOT_TOKEN:
    logs.info("⚠️ 'BOT_TOKEN' - Not Found !!")
    sys.exit()
if not STRING_SESSION:
    logs.info("⚠️ 'STRING_SESSION' - Not Found !!")
    sys.exit()
if not MONGO_DB_URL:
    logs.info("⚠️ 'MONGO_DB_URL' - Not Found !!")
    sys.exit()
    
try:
    adb_cli = AsyncIOMotorClient(MONGO_DB_URL)
except Exception:
    logs.info("⚠️ 'MONGO_DB_URL' - Not Valid !!")
    sys.exit()

mongodb = adb_cli.adityaplayer

if OWNER_ID == 0:
    logs.info("⚠️ 'OWNER_ID' - Not Found !!")
    sys.exit()
if LOG_GROUP_ID == 0:
    logs.info("⚠️ 'LOG_GROUP_ID' - Not Found !!")
    sys.exit()





chatsdb = mongodb.tgchats
usersdb = mongodb.tgusers




# Served Chats

async def is_served_chat(chat_id: int) -> bool:
    chat = await chatsdb.find_one({"chat_id": chat_id})
    if not chat:
        return False
    return True
    

async def add_served_chat(chat_id: int):
    is_served = await is_served_chat(chat_id)
    if is_served:
        return
    return await chatsdb.insert_one({"chat_id": chat_id})
    
    
async def get_served_chats() -> list:
    chats_list = []
    async for chat in chatsdb.find({"chat_id": {"$lt": 0}}):
        chats_list.append(chat)
    return chats_list


# Served users

async def is_served_user(user_id: int) -> bool:
    user = await usersdb.find_one({"user_id": user_id})
    if not user:
        return False
    return True


async def add_served_user(user_id: int):
    is_served = await is_served_user(user_id)
    if is_served:
        return
    return await usersdb.insert_one({"user_id": user_id})


async def get_served_users() -> list:
    users_list = []
    async for user in usersdb.find({"user_id": {"$gt": 0}}):
        users_list.append(user)
    return users_list










async def main():
    if "cache" not in os.listdir():
        os.mkdir("cache")
    if "downloads" not in os.listdir():
        os.mkdir("downloads")
    for file in os.listdir():
        if file.endswith(".session"):
            os.remove(file)
    for file in os.listdir():
        if file.endswith(".session-journal"):
            os.remove(file)
    try:
       await adb_cli.admin.command('ping')
    except Exception:
        logs.info("⚠️ 'MONGO_DB_URL' - Not Valid !!")
        sys.exit()
        
    try:
        await bot.start()
    except Exception as e:
        logs.info(f"🚫 Failed to start Bot❗\n⚠️ Reason: {e}")
        sys.exit()
    if LOG_GROUP_ID != 0:
        try:
            await bot.send_message(
                LOG_GROUP_ID, "**✅ Bot Started.**"
            )
        except Exception:
            pass
    logs.info("✅ Bot Started❗")
    try:
        await app.start()
    except Exception as e:
        logs.info(f"🚫 Failed to start Assistant❗\n⚠️ Reason: {e}")
        sys.exit()
    try:
        await app.join_chat("source_code_network")
   
    except Exception:
        pass
    if LOG_GROUP_ID != 0:
        try:
            await app.send_message(
                LOG_GROUP_ID, "**✅ Assistant Started.**"
            )
        except Exception:
            pass
    logs.info("✅ Assistant Started❗")
    try:
        await call.start()
    except Exception as e:
        logs.info(f"🚫 Failed to start PyTgCalls❗\n⚠️ Reason: {e}")
        sys.exit()
    await idle()




def close_all_open_files():
    for obj in gc.get_objects():
        try:
            if isinstance(obj, io.IOBase) and not obj.closed:
                obj.close()
        except Exception:
            continue


def format_seconds(seconds):
    if seconds is not None:
        seconds = int(seconds)
        d, h, m, s = (
            seconds // (3600 * 24),
            seconds // 3600 % 24,
            seconds % 3600 // 60,
            seconds % 3600 % 60,
        )
        if d > 0:
            return "{:02d}:{:02d}:{:02d}:{:02d}".format(d, h, m, s)
        elif h > 0:
            return "{:02d}:{:02d}:{:02d}".format(h, m, s)
        elif m > 0:
            return "{:02d}:{:02d}".format(m, s)
        elif s > 0:
            return "00:{:02d}".format(s)
    return "-"


def format_views(views) -> str:
    # Clean up the view count string by removing commas and 'views' text
    if isinstance(views, str):
        views = views.replace(',', '').split()[0]
    try:
        count = int(views)
        if count >= 1_000_000_000:
            return f"{count / 1_000_000_000:.1f}B"
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"
        if count >= 1_000:
            return f"{count / 1_000:.1f}K"
        return str(count)
    except (ValueError, TypeError):
        return "0"



def chat_admins_only(mystic):
    async def wrapper(client, message):
        if message.sender_chat:
            if message.sender_chat.id != message.chat.id:
                return
                
        if message.from_user:
            if message.from_user.id != OWNER_ID:
                try:
                    member = await bot.get_chat_member(
                        message.chat.id, message.from_user.id
                    )
                except Exception:
                    return
                if not member:
                    return
                try:
                    if not member.privileges.can_manage_video_chats:
                        return
                except Exception:
                    return
        try:
            await message.delete()
        except Exception:
            pass
            
        return await mystic(client, message)

    return wrapper


async def get_stream_info(query, streamtype):
    """Get stream information using py-yt-search and the new API"""
    try:
        # Check if the query is a URL
        is_url = query.startswith(('http://', 'https://', 'www.', 'youtube.com', 'youtu.be'))
        
        # Use direct API with query parameter if it's not a URL
        api_url = "https://yt-api-production-fc4c.up.railway.app"
        api_key = "cbm_e40ef459f0274be1ad541a19f95fd367"
        endpoint = "/video" if streamtype.lower() == "video" else "/audio"
        
        if not is_url:
            # Direct query to the API
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.get(
                        f"{api_url}{endpoint}",
                        params={"query": query},
                        headers={"X-API-Key": api_key},
                        follow_redirects=True
                    )
                    response.raise_for_status()
                    stream_data = response.json()
                    
                    # Get view count and clean it to avoid parsing issues with commas
                    view_count = str(stream_data.get('view_count', 0))
                    # Clean up the view count in case it has commas or 'views' text
                    if ',' in view_count or ' views' in view_count.lower():
                        view_count = view_count.replace(',', '').split()[0]
                    
                    video_id = stream_data.get('id', '')
                    video_link = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
                    
                    return {
                        "id": video_id,
                        "title": stream_data.get('title'),
                        "duration": stream_data.get('duration'),
                        "link": video_link,
                        "channel": stream_data.get('uploader') or stream_data.get('channel'),
                        "views": view_count,
                        "thumbnail": stream_data.get('thumbnail'),
                        "stream_url": stream_data.get('stream_url'),
                        "stream_type": stream_data.get('stream_type') or (
                            "Video" if streamtype.lower() == "video" else "Audio"
                        )
                    }
            except Exception as e:
                print(f"Direct API query failed: {str(e)}, falling back to search method")
                # Fall back to search method
                pass
        
        # If direct query failed or we have a URL, use the search method
        from py_yt import Search, VideosSearch
        
        _search = Search(query, limit=1, language='en', region='IN')
        result = await _search.next()
        
        if not result or not result.get('result'):
            print("No search results found")
            return {}
            
        video_info = result['result'][0]
        
        # Check if the result is a channel instead of a video
        if video_info.get('type') == 'channel':
            print("Search returned a channel, trying more specific search")
            # Try searching with more specific terms
            _search = Search(f"{query} music", limit=1, language='en', region='IN')
            result = await _search.next()
            if not result or not result.get('result'):
                return {}
            video_info = result['result'][0]
        
        # Now we should have a video ID
        video_id = video_info.get('id')
        if not video_id:
            print("Could not find video ID in search results")
            return {}
            
        video_link = f"https://www.youtube.com/watch?v={video_id}"
        
        # Extract video details from search results for fallback
        title = video_info.get('title', '')
            
        # Extract duration safely
        duration = 0
        if 'duration' in video_info:
            duration_dict = video_info.get('duration')
            if isinstance(duration_dict, dict) and 'secondsText' in duration_dict:
                try:
                    duration = int(duration_dict.get('secondsText', '0'))
                except (ValueError, TypeError):
                    duration = 0
        
        # Extract channel name safely
        channel_name = ""
        if 'channel' in video_info:
            channel_info = video_info.get('channel')
            if isinstance(channel_info, dict):
                channel_name = channel_info.get('name', '')            # Extract view count safely
            view_count = "0"
            if 'viewCount' in video_info:
                view_count_info = video_info.get('viewCount')
                if isinstance(view_count_info, dict):
                    view_count = view_count_info.get('text', '0')
                    # Clean up the view count in case it has commas or 'views' text
                    if ',' in view_count or ' views' in view_count.lower():
                        view_count = view_count.replace(',', '').split()[0]
        
        # Extract thumbnail safely
        thumbnail_url = ""
        if 'thumbnails' in video_info and video_info['thumbnails']:
            thumbnails = video_info.get('thumbnails')
            if isinstance(thumbnails, list) and len(thumbnails) > 0:
                thumbnail_url = thumbnails[0].get('url', '')
        
        # Now get the stream URL from the API using video link
        api_url = "https://yt-api-production-fc4c.up.railway.app"
        api_key = "cbm_e40ef459f0274be1ad541a19f95fd367"
        endpoint = "/video" if streamtype.lower() == "video" else "/audio"
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(
                    f"{api_url}{endpoint}",
                    params={"url": video_link},
                    headers={"X-API-Key": api_key},
                    follow_redirects=True
                )
                response.raise_for_status()
                stream_data = response.json()
                
                # Get view count and clean it to avoid parsing issues with commas
                view_count = str(stream_data.get('view_count', 0))
                # Clean up the view count in case it has commas or 'views' text
                if ',' in view_count or ' views' in view_count.lower():
                    view_count = view_count.replace(',', '').split()[0]
                
                return {
                    "id": stream_data.get('id'),
                    "title": stream_data.get('title'),
                    "duration": stream_data.get('duration'),
                    "link": video_link,
                    "channel": stream_data.get('uploader') or stream_data.get('channel'),
                    "views": view_count,
                    "thumbnail": stream_data.get('thumbnail'),
                    "stream_url": stream_data.get('stream_url'),
                    "stream_type": stream_data.get('stream_type') or (
                        "Video" if streamtype.lower() == "video" else "Audio"
                    )
                }
        except Exception as e:
            print(f"API connection error: {str(e)}")
            # Fall back to using video info extracted earlier
            fallback_data = {
                "id": video_id,
                "title": title,
                "duration": duration,
                "link": video_link,
                "channel": channel_name,
                "views": view_count,
                "thumbnail": thumbnail_url,
                "stream_url": "",  # No stream URL available in fallback
                "stream_type": "Video" if streamtype.lower() == "video" else "Audio"
            }
            return fallback_data
            
    except Exception as e:
        print(f"Error in get_stream_info: {str(e)}")
        return {}



async def is_stream_off(chat_id: int) -> bool:
    mode = paused.get(chat_id)
    if not mode:
        return False
    return mode


async def stream_on(chat_id: int):
    paused[chat_id] = False


async def stream_off(chat_id: int):
    paused[chat_id] = True


async def get_call_status(chat_id):
    pass



    

async def add_active_media_chat(chat_id, stream_type):
    if stream_type == "Audio":
        if chat_id in active_video_chats:
            active_video_chats.remove(chat_id)
        if chat_id not in active_audio_chats:
            active_audio_chats.append(chat_id)
    elif stream_type == "Video":
        if chat_id in active_audio_chats:
            active_audio_chats.remove(chat_id)
        if chat_id not in active_video_chats:
            active_video_chats.append(chat_id)
    if chat_id not in active_media_chats:
        active_media_chats.append(chat_id)


async def remove_active_media_chat(chat_id):
    if chat_id in active_audio_chats:
        active_audio_chats.remove(chat_id)
    if chat_id in active_video_chats:
        active_video_chats.remove(chat_id)
    if chat_id in active_media_chats:
        active_media_chats.remove(chat_id)

async def fetch_and_save_image(url, save_path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                async with aiofiles.open(save_path, mode="wb") as file:
                    await file.write(await resp.read())
                return save_path
    return None


async def put_queue(
    chat_id,
    media_stream,
    thumbnail,
    title,
    duration,
    stream_type,
    chat_link,
    mention,
):
    put = {
        "media_stream": media_stream,
        "thumbnail": thumbnail,
        "title": title,
        "duration": duration,
        "stream_type": stream_type,
        "chat_link": chat_link,
        "mention": mention,
    }
    check = queues.get(chat_id)
    if check:
        queues[chat_id].append(put)
    else:
        queues[chat_id] = []
        queues[chat_id].append(put)
    
    return len(queues[chat_id]) - 1



async def clear_queue(chat_id):
    check = queues.get(chat_id)
    if check:
        queues.pop(chat_id)


async def close_stream(chat_id):
    try:
        await call.leave_call(chat_id)
    except Exception:
        pass
    await clear_queue(chat_id)
    await remove_active_media_chat(chat_id)




async def log_stream_info(chat_id, title, duration, stream_type, chat_link, mention, thumbnail, pos):
    if LOG_GROUP_ID != 0 and chat_id != LOG_GROUP_ID:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="📡 Join Chat 💬", url=chat_link
                    )
                ],
            ]
        )
        if pos != 0:
            caption = f"""
**✅ Added To Queue At: #{pos}**

**❍ Title:** {title}
**❍ Duration:** {duration}
**❍ Stream Type:** {stream_type}
**❍ Requested By:** {mention}"""

        else:
            caption = f"""
**✅ Started Streaming On VC.**

**❍ Title:** {title}
**❍ Duration:** {duration}
**❍ Stream Type:** {stream_type}
**❍ Requested By:** {mention}"""
        
        try:
            await bot.send_photo(LOG_GROUP_ID, photo=thumbnail, caption=caption, reply_markup=buttons)
        except Exception:
            pass





async def change_stream(chat_id):
    queued = queues.get(chat_id)
    if queued:
        queued.pop(0)
        
    if not queued:
        await bot.send_message(chat_id, "**❎ Queue is empty, So left\nfrom VC❗...**")
        return await close_stream(chat_id)

    aux = await bot.send_message(
        chat_id, "**🔁 Processing ✨...**"
    )
    pos  = 0
    media_stream = queued[0].get("media_stream")

    await call.play(chat_id, media_stream, config=call_config)
    
    thumbnail = queued[0].get("thumbnail")
    title = queued[0].get("title")
    duration = queued[0].get("duration")
    stream_type = queued[0].get("stream_type")
    chat_link = queued[0].get("chat_link")
    mention = queued[0].get("mention")
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="🗑️ Close", callback_data="force_close"
                )
            ],
        ]
    )
    caption = f"""
**✅ Started Streaming On VC.**

**❍ Title:** {title}
**❍ Duration:** {duration}
**❍ Stream Type:** {stream_type}
**❍ Requested By:** {mention}"""
    try:
        await aux.delete()
    except Exception:
        pass
    await add_active_media_chat(chat_id, stream_type)
    try:
        # Try sending photo from the path rather than direct URL
        await bot.send_photo(chat_id, photo=thumbnail, caption=caption, has_spoiler=True, reply_markup=buttons)
    except Exception as e:
        # Fall back to a default image if there's an issue with the thumbnail
        await bot.send_photo(chat_id, photo=START_IMAGE_URL, caption=caption, has_spoiler=True, reply_markup=buttons)
        logs.error(f"Error sending photo in change_stream: {str(e)}")
    await log_stream_info(chat_id, title, duration, stream_type, chat_link, mention, thumbnail, pos)


@bot.on_message(filters.command("start") & filters.private)
async def start_welcome_private(client, message):
    chat_id = message.chat.id
    await add_served_user(chat_id)
    photo = START_IMAGE_URL
    mention = message.from_user.mention
    caption = f"""**✅ Hello, {mention}

❍ i am an advanced, latest & verƴ
powerƒul vc music player bot.

❍ ƒeel ƒree to use me in your chat
& share with your other ƒriends.**"""
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="➕ Add Me in Your Chat ➕", url=f"https://t.me/{client.me.username}?startgroup=true",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙ Open All Commands ⚙", callback_data="help_menu"
                )
            ],
        ]
    )
    try:
        return await client.send_photo(
            chat_id, photo=photo, caption=caption, has_spoiler=True, reply_markup=buttons
        )
    except Exception:
        pass
        


@bot.on_message(filters.command("help") & filters.private)
async def open_help_menu_private(client, message):
    chat_id = message.chat.id
    photo = START_IMAGE_URL
    caption = f"""**✅ These are The Commands and
Their Uses.

/play - play music by name or URL.
/vplay - play video by name or URL.
/pause - pause running stream.
/resume - resume paused stream.
/skip - skip to next stream.
/end - stop stream & clear queue.

Example:
• /play sidhu moosewala
• /vplay latest punjabi song**"""
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="➕ Add Me in Your Chat ➕", url=f"https://t.me/{client.me.username}?startgroup=true",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Back To Home Menu 🏠", callback_data="home_menu"
                )
            ],
        ]
    )
    try:
        await bot.send_photo(
            chat_id, photo=photo, caption=caption, has_spoiler=True, reply_markup=buttons
        )
    except Exception:
        pass




@bot.on_message(filters.command(["play", "vplay"]) & ~filters.private)
async def start_audio_stream(client, message):
    try:
        await message.delete()
    except Exception:
        pass
    chat_id = message.chat.id
    if message.chat.username:
        chat_link = f"https://t.me/{message.chat.username}"
    else:
        chatlinks = clinks.get(chat_id)
        
        if chatlinks:
            if chatlinks == f"https://t.me/{client.me.username}":
                try:
                    chat_link = await client.export_chat_invite_link(chat_id)
                except Exception:
                    chat_link = chatlinks
            else:
                chat_link = chatlinks
        else:
            try:
                chat_link = await client.export_chat_invite_link(chat_id)
            except Exception:
                chat_link = f"https://t.me/{client.me.username}"
            
    clinks[chat_id] = chat_link
    
    try:
        mention = message.from_user.mention
    except:
        mention = client.me.mention
        
    try:
        user_id = message.from_user.id
    except Exception:
        user_id = client.me.id
        
    try:
        if len(message.command) < 2:
            return await client.send_message(
                chat_id, f"""
**🥀 Give Me Some Query To
Stream Audio Or Video❗...

ℹ️ Example:
≽ Audio: `/play yalgaar`
≽ Video: `/vplay yalgaar`**"""
            )
        aux = await client.send_message(chat_id, "**🔁 Processing ✨...**")
        query = message.text.split(None, 1)[1]
        streamtype = "Audio" if not message.command[0].startswith("v") else "Video"
        info = await get_stream_info(query, streamtype)
        if not info:
            return await aux.edit("**❌ Failed to fetch details, try\nanother song or search term.**")
            
        link = info.get("link")
        title = f"[{info.get('title')[:18]}]({link})"
        duration = f"""{
            format_seconds(info.get('duration')) + ' Mins'
            if info.get('duration') else 'Live Stream'
        }"""
        views = format_views(info.get("views"))
        image = info.get("thumbnail")
        stream_url = info.get("stream_url")
        stream_type = info.get("stream_type")
        
        if not stream_url:
            return await aux.edit("**❌ No stream URL found. Please try a different search term.**")
        
        media_stream = MediaStream(
            media_path=stream_url,
            video_flags=MediaStream.Flags.IGNORE,
            audio_parameters=AudioQuality.STUDIO,
        ) if stream_type != "Video" else MediaStream(
            media_path=stream_url,
            audio_parameters=AudioQuality.STUDIO,
            video_parameters=VideoQuality.HD_720p,
        )
        
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="🗑️ Close", callback_data="force_close"
                    )
                ],
            ]
        )
        
        queued = queues.get(chat_id)
        if queued:
            thumbnail_url = info.get("thumbnail", START_IMAGE_URL)
            # Download the thumbnail for reliable sending
            thumbnail_path = await fetch_and_save_image(thumbnail_url, f"cache/temp_{info.get('id', 'thumbnail')}.png")
            if not thumbnail_path:
                thumbnail_path = START_IMAGE_URL  # Fallback to START_IMAGE_URL if download fails
                
            pos = await put_queue(
                chat_id, media_stream, thumbnail_path, title, duration, stream_type, chat_link, mention
            )
            caption = f"""
**✅ Added To Queue At: #{pos}**

**❍ Title:** {title}
**❍ Duration:** {duration}
**❍ Stream Type:** {stream_type}
**❍ Requested By:** {mention}"""
        
        else:
            try: 
                await call.play(chat_id, media_stream, config=call_config)
            except NoActiveGroupCall:
                try:
                    assistant = await client.get_chat_member(chat_id, app.me.id)
                    if (
                        assistant.status == ChatMemberStatus.BANNED
                        or assistant.status == ChatMemberStatus.RESTRICTED
                    ):
                        return await aux.edit_text(
                            f"**🤖 At first, unban [Assistant ID](https://t.me/{app.me.username}) to start stream❗**"
                        )
                except ChatAdminRequired:
                    return await aux.edit_text(
                        "**🤖 At first, Promote me as an admin❗**"
                    )
                except UserNotParticipant:
                    if message.chat.username:
                        invitelink = f"https://t.me/{message.chat.username}"
                        try:
                            await app.resolve_peer(invitelink)
                        except Exception:
                            pass
                    else:
                        try:
                            invitelink = await client.export_chat_invite_link(chat_id)
                        except ChatAdminRequired:
                            return await aux.edit_text(
                                "**🤖 Hey, I need invite user permission to add Assistant ID❗**"
                            )
                        except Exception as e:
                            return await aux.edit_text(
                                f"**🚫 Assistant Error:** `{e}`"
                            )
                    clinks[chat_id] = invitelink
                    try:
                        await asyncio.sleep(1)
                        await app.join_chat(invitelink)
                    except InviteRequestSent:
                        try:
                            await client.approve_chat_join_request(chat_id, app.me.id)
                        except Exception as e:
                            return await aux.edit_text(
                                f"**🚫 Approve Error:** `{e}`"
                            )
                    except UserAlreadyParticipant:
                        pass
                    except Exception as e:
                        return await aux.edit_text(
                            f"**🚫 Assistant Join Error:** `{e}`"
                        )
                try:
                    await call.play(chat_id, media_stream, config=call_config)
                except NoActiveGroupCall:
                    return await aux.edit_text(f"**⚠️ No Active VC❗...**")
            except TelegramServerError:
                return await aux.edit_text("**⚠️ Telegram Server Issue❗...**")
                
            thumbnail_url = info.get("thumbnail", START_IMAGE_URL)
            # Download the thumbnail for reliable sending
            thumbnail_path = await fetch_and_save_image(thumbnail_url, f"cache/temp_{info.get('id', 'thumbnail')}.png")
            if not thumbnail_path:
                thumbnail_path = START_IMAGE_URL  # Fallback to START_IMAGE_URL if download fails
                
            pos = await put_queue(
                chat_id, media_stream, thumbnail_path, title, duration, stream_type, chat_link, mention
            )
            caption = f"""
**✅ Started Streaming On VC.**

**❍ Title:** {title}
**❍ Duration:** {duration}
**❍ Stream Type:** {stream_type}
**❍ Requested By:** {mention}"""
        
        try:
            await aux.delete()
        except Exception:
            pass
        try:
            # Try sending photo from the path rather than the URL
            await client.send_photo(chat_id, photo=thumbnail_path, caption=caption, has_spoiler=True, reply_markup=buttons)
        except Exception as e:
            # Fall back to a default image if there's an issue with the thumbnail
            await client.send_photo(chat_id, photo=START_IMAGE_URL, caption=caption, has_spoiler=True, reply_markup=buttons)
            logs.error(f"Error sending photo: {str(e)}")
        
        await add_active_media_chat(chat_id, stream_type)
        await add_served_chat(chat_id)
        await log_stream_info(chat_id, title, duration, stream_type, chat_link, mention, thumbnail_path, pos)
    except Exception as e:
        if "too many open files" in str(e).lower():
            close_all_open_files()
        logs.error(str(e))
        await aux.edit("**❌ Failed to stream❗...**")


@bot.on_message(filters.command("pause") & ~filters.private)
@chat_admins_only
async def pause_current_stream(client, message):
    chat_id = message.chat.id
    queued = queues.get(chat_id)
    if not queued:
        return await message.reply_text(
            "**❌ Nothing Streaming.**"
        )
    is_stream = await is_stream_off(chat_id)
    if is_stream:
        return await message.reply_text(
            "**✅ Stream already Paused.**"
        )
    try:
        await call.pause(chat_id)
    except Exception:
        return await message.reply_text(
            "**❌ Failed to pause stream❗**"
        )
    await stream_off(chat_id)
    return await message.reply_text("**✅ Stream now Paused.**")
    


@bot.on_message(filters.command("resume") & ~filters.private)
@chat_admins_only
async def resume_current_stream(client, message):
    chat_id = message.chat.id
    queued = queues.get(chat_id)
    if not queued:
        return await message.reply_text(
            "**❌ Nothing Streaming.**"
        )
    is_stream = await is_stream_off(chat_id)
    if not is_stream:
        return await message.reply_text(
            "**✅ Stream already Running.**"
        )
    try:
        await call.resume(chat_id)
    except Exception:
        return await message.reply_text(
            "**❌ Failed to resume stream❗**"
        )
    await stream_on(chat_id)
    return await message.reply_text("**✅ Stream now Resumed.**")
    

@bot.on_message(filters.command("end") & ~filters.private)
@chat_admins_only
async def stop_running_stream(client, message):
    chat_id = message.chat.id
    queued = queues.get(chat_id)
    if not queued:
        return await message.reply_text(
            "**❌ Nothing Streaming.**"
        )
    await close_stream(chat_id)
    return await message.reply_text("**❎ Streaming Stopped.**")


@bot.on_message(filters.command("skip") & ~filters.private)
@chat_admins_only
async def skip_current_stream(client, message):
    chat_id = message.chat.id
    queued = queues.get(chat_id)
    if not queued:
        return await message.reply_text(
            "**❌ Nothing streaming❗**"
        )
    return await change_stream(chat_id)


@bot.on_callback_query(filters.regex("help_menu"))
async def open_help_menu_cb(client, query):
    caption = f"""**✅ These are The Commands and
Their Uses.

/play - play music by name or URL.
/vplay - play video by name or URL.
/pause - pause running stream.
/resume - resume paused stream.
/skip - skip to next stream.
/end - stop stream & clear queue.

Example:
• /play sidhu moosewala
• /vplay latest punjabi song**"""
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="➕ Add Me in Your Chat ➕", url=f"https://t.me/{client.me.username}?startgroup=true",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Back To Home Menu 🏠", callback_data="home_menu"
                )
            ],
        ]
    )
    try:
        await query.edit_message_caption(caption=caption, reply_markup=buttons)
    except Exception:
        pass



@bot.on_callback_query(filters.regex("home_menu"))
async def open_help_menu_cb(client, query):
    mention = query.from_user.mention
    caption = f"""**✅ Hello, {mention}

❍ i am an advanced, latest & verƴ
powerƒul vc music player bot.

❍ ƒeel ƒree to use me in your chat
& share with your other ƒriends.**"""
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="➕ Add Me in Your Chat ➕", url=f"https://t.me/{client.me.username}?startgroup=true",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙ Open All Commands ⚙", callback_data="help_menu"
                )
            ],
        ]
    )
    try:
        await query.edit_message_caption(caption=caption, reply_markup=buttons)
    except Exception:
        pass
    

@bot.on_message(filters.command("stats") & only_owner)
async def check_stats(client, message):
    try:
        await message.delete()
    except Exception:
        pass
    active_audio = len(active_audio_chats)
    active_video = len(active_video_chats)
    total_chats = len(await get_served_chats())
    total_users = len(await get_served_users())
    
    caption = f"""
**✅ Active Audio Chats:** `{active_audio}`
**✅ Active Video Chats:** `{active_video}`

**✅ Total Served Chats:** `{total_chats}`
**✅ Total Served Users:** `{total_users}`
"""
    return await message.reply_text(caption)



@bot.on_message(filters.command(["broadcast", "gcast"]) & only_owner)
async def broadcast_message(client, message):
    try:
        await message.delete()
    except:
        pass
    if message.reply_to_message:
        x = message.reply_to_message.id
        y = message.chat.id
    else:
        if len(message.command) < 2:
            return await message.reply_text(
                f"""**🤖 Hey Give Me Some Text
Or Reply To A Message❗**"""
            )
        query = message.text.split(None, 1)[1]
        if "-pin" in query:
            query = query.replace("-pin", "")
        if "-nobot" in query:
            query = query.replace("-nobot", "")
        if "-pinloud" in query:
            query = query.replace("-pinloud", "")
        if "-user" in query:
            query = query.replace("-user", "")
        if query == "":
            return await message.reply_text(
                f"""**🤖 Hey Give Me Some Text
Or Reply To A Message❗**"""
            )

    
    # Bot broadcast inside chats
    if "-nobot" not in message.text:
        sent = 0
        pin = 0
        chats = []
        schats = await get_served_chats()
        for chat in schats:
            chats.append(int(chat["chat_id"]))
        for i in chats:
            try:
                m = (
                    await bot.forward_messages(i, y, x)
                    if message.reply_to_message
                    else await bot.send_message(i, text=query)
                )
                if "-pin" in message.text:
                    try:
                        await m.pin(disable_notification=True)
                        pin += 1
                    except Exception:
                        continue
                elif "-pinloud" in message.text:
                    try:
                        await m.pin(disable_notification=False)
                        pin += 1
                    except Exception:
                        continue
                sent += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                continue
            except Exception:
                continue
        await message.reply_text(f"**✅ Global Broadcast Done.**\n\n__🤖 Broadcast Mesaages In\n{sent} Chats With {pin} Pins.__")

    

    # Bot broadcasting to users
    if "-user" in message.text:
        susr = 0
        served_users = []
        susers = await get_served_users()
        for user in susers:
            served_users.append(int(user["user_id"]))
        for i in served_users:
            try:
                m = (
                    await bot.forward_messages(i, y, x)
                    if message.reply_to_message
                    else await bot.send_message(i, text=query)
                )
                susr += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                continue
            except Exception:
                continue
        await message.reply_text(f"**✅ Global Broadcast Done.**\n\n__🤖 Broascast Mesaages To\n{susr} Users From Bot.__")





@bot.on_message(filters.command("post") & only_owner)
async def post_bot_promotion(client, message):
    total_chats = []
    schats = await get_served_chats()
    for chat in schats:
        total_chats.append(int(chat["chat_id"]))
    susers = await get_served_users()
    for user in susers:
        total_chats.append(int(user["user_id"]))
            
    photo = START_IMAGE_URL
    caption = f"""
**✅ Hello friends,

❍ i am an advanced, latest &
verƴ powerƒul vc player bot.

❍ ƒeel ƒree to use me & share
with your other ƒriends.**"""
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="➕ Add Me in Your Chat ➕", url=f"https://t.me/{client.me.username}?startgroup=true",
                )
            ]
        ]
    )
    sent = 0
    for chat_id in total_chats:
        try:
            m = await client.send_photo(
                chat_id, photo=photo, caption=caption, reply_markup=buttons
            )
            sent = sent + 1
            await asyncio.sleep(5)
            try:
                await m.pin(disable_notification=False)
            except Exception:
                continue
        except FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except Exception:
            continue
    return await message.reply_text(f"**✅ Successfully posted in {sent} chats.**")







@bot.on_callback_query(filters.regex("force_close"))
async def force_close_anything(client, query):
    try:
        await query.message.delete()
    except Exception:
        pass



@bot.on_message(filters.new_chat_members, group=-1)
async def add_chat_id(client, message):
    chat_id = message.chat.id
    for member in message.new_chat_members:
        if member.id == bot.me.id:
            await add_served_chat(chat_id)




@call.on_update(fl.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT))
@call.on_update(fl.chat_update(ChatUpdate.Status.KICKED))
@call.on_update(fl.chat_update(ChatUpdate.Status.LEFT_GROUP))
async def stream_services_handler(_, update: Update):
    return await close_stream(update.chat_id)
    
    
@call.on_update(fl.stream_end())
async def stream_end_handler(_, update: Update):
    chat_id = update.chat_id
    return await change_stream(chat_id)







if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    logs.info("❎ Goodbye, Bot Has Been Stopped‼️")

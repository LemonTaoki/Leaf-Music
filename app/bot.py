import logging
import os
import uuid

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from . import jamendo
from .config import BASE_URL, BOT_TOKEN, UPLOAD_DIR
from .models import Song
from .store import store
from .websocket_manager import manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_PATH = os.path.join(BASE_DIR, UPLOAD_DIR)
os.makedirs(UPLOAD_PATH, exist_ok=True)


def room_link(token: str) -> str:
    return f"{BASE_URL}/room/{token}"


def join_vc_keyboard(token: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🎧 Join VC", url=room_link(token))]]
    )


async def broadcast_state(group_id: int):
    room = store.get_by_group(group_id)
    if room:
        await manager.broadcast(room.token, {"type": "state", **store.state_dict(room)})


def _ensure_room_title(room, chat):
    if chat.title and room.group_title != chat.title:
        room.group_title = chat.title


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply(
        "👋 Music bot ready!\n\n"
        "/play <song name> — Jamendo (royalty-free) se gaana dhoondo aur queue karo\n"
        "Ya seedha koi MP3/audio file bhejo, wo bhi queue ho jayegi.\n\n"
        "Commands:\n"
        "/pause /resume /skip /stop\n"
        "/queue /nowplaying\n"
        "/volume <0-100> /loop /remove <number>"
    )


@dp.message(Command("play"))
async def cmd_play(message: Message, command: CommandObject):
    query = (command.args or "").strip()
    group_id = message.chat.id

    if not query:
        await message.reply(
            "Gaane ka naam bhi likho: /play <song name>\n"
            "(Ya seedha koi MP3 file bhej do, wo bhi chalega.)"
        )
        return

    searching = await message.reply("🔎 Dhoondh raha hoon...")

    try:
        song = await jamendo.search_song(query, added_by=message.from_user.full_name)
    except RuntimeError as e:
        await searching.edit_text(f"⚠️ {e}")
        return

    if not song:
        await searching.edit_text(
            "Kuch nahi mila. Koi aur naam try karo, ya mujhe seedha MP3 file bhejo."
        )
        return

    room = store.add_song(group_id, song)
    _ensure_room_title(room, message.chat)

    await broadcast_state(group_id)
    await searching.edit_text(f"🎶 Queue me add ho gaya: {song.title}")
    await message.reply(
        "Room join karne ke liye niche button dabao 👇",
        reply_markup=join_vc_keyboard(room.token),
    )


@dp.message(F.audio | F.voice | (F.document & F.document.mime_type.startswith("audio/")))
async def handle_uploaded_audio(message: Message):
    group_id = message.chat.id
    file_obj = message.audio or message.voice or message.document
    title = (
        getattr(file_obj, "file_name", None)
        or getattr(file_obj, "title", None)
        or "Uploaded track"
    )

    tg_file = await bot.get_file(file_obj.file_id)
    local_name = f"{uuid.uuid4().hex}.mp3"
    local_path = os.path.join(UPLOAD_PATH, local_name)
    await bot.download_file(tg_file.file_path, destination=local_path)

    song = Song(
        title=title,
        url=f"{BASE_URL}/uploads/{local_name}",
        source="upload",
        added_by=message.from_user.full_name,
    )

    room = store.add_song(group_id, song)
    _ensure_room_title(room, message.chat)

    await broadcast_state(group_id)
    await message.reply(
        f"📥 Upload ho gaya aur queue me add: {title}",
        reply_markup=join_vc_keyboard(room.token),
    )


@dp.message(Command("pause"))
async def cmd_pause(message: Message):
    room = store.get_by_group(message.chat.id)
    if not room:
        await message.reply("Koi active room nahi hai. Pehle /play karo.")
        return
    store.pause(room)
    await broadcast_state(message.chat.id)
    await message.reply("⏸ Pause ho gaya.")


@dp.message(Command("resume"))
async def cmd_resume(message: Message):
    room = store.get_by_group(message.chat.id)
    if not room:
        await message.reply("Koi active room nahi hai.")
        return
    store.resume(room)
    await broadcast_state(message.chat.id)
    await message.reply("▶️ Resume ho gaya.")


@dp.message(Command("skip"))
async def cmd_skip(message: Message):
    room = store.get_by_group(message.chat.id)
    if not room:
        await message.reply("Koi active room nahi hai.")
        return
    nxt = store.skip(room)
    await broadcast_state(message.chat.id)
    await message.reply(f"⏭ Ab baj raha hai: {nxt.title}" if nxt else "Queue khatam ho gayi.")


@dp.message(Command("stop"))
async def cmd_stop(message: Message):
    room = store.get_by_group(message.chat.id)
    if not room:
        await message.reply("Koi active room nahi hai.")
        return
    store.stop(room)
    await broadcast_state(message.chat.id)
    await message.reply("⏹ Room stop ho gaya, queue clear ho gayi.")


@dp.message(Command("queue"))
async def cmd_queue(message: Message):
    room = store.get_by_group(message.chat.id)
    if not room or not room.queue:
        await message.reply("Queue khaali hai.")
        return
    lines = []
    for i, s in enumerate(room.queue):
        marker = "▶️" if i == room.current_index else f"{i + 1}."
        lines.append(f"{marker} {s.title}")
    await message.reply("\n".join(lines))


@dp.message(Command("nowplaying"))
async def cmd_nowplaying(message: Message):
    room = store.get_by_group(message.chat.id)
    song = room.current_song if room else None
    if not song:
        await message.reply("Abhi kuch bhi nahi baj raha.")
        return
    status = "▶️ Playing" if room.is_playing else "⏸ Paused"
    await message.reply(f"{status}: {song.title}", reply_markup=join_vc_keyboard(room.token))


@dp.message(Command("volume"))
async def cmd_volume(message: Message, command: CommandObject):
    room = store.get_by_group(message.chat.id)
    if not room:
        await message.reply("Koi active room nahi hai.")
        return
    args = (command.args or "").strip()
    if not args.isdigit():
        await message.reply("Aise likho: /volume 70")
        return
    store.set_volume(room, int(args))
    await broadcast_state(message.chat.id)
    await message.reply(f"🔊 Volume set: {room.volume}")


@dp.message(Command("loop"))
async def cmd_loop(message: Message):
    room = store.get_by_group(message.chat.id)
    if not room:
        await message.reply("Koi active room nahi hai.")
        return
    state = store.toggle_loop(room)
    await broadcast_state(message.chat.id)
    await message.reply(f"🔁 Loop: {'ON' if state else 'OFF'}")


@dp.message(Command("remove"))
async def cmd_remove(message: Message, command: CommandObject):
    room = store.get_by_group(message.chat.id)
    if not room:
        await message.reply("Koi active room nahi hai.")
        return
    args = (command.args or "").strip()
    if not args.isdigit():
        await message.reply("Aise likho: /remove 2  (queue number)")
        return
    idx = int(args) - 1
    ok = store.remove(room, idx)
    await broadcast_state(message.chat.id)
    await message.reply("🗑 Hata diya." if ok else "Ye number queue me nahi hai.")

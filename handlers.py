from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import ADMIN_IDS
from database import *
from scenes import scenes
import asyncio

router = Router()
bot = None

ADMIN_ID = 1896036065
CHANNELS = ["chat_goddes", "find_goddes"]
CONFESSION_CHANNEL = "milafemdomqueen"

def set_bot(bot_instance):
    global bot
    bot = bot_instance

async def check_channel_subscription(user_id: int, channel_username: str) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=f"@{channel_username}", user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def post_confession_to_channel(text: str, username: str):
    try:
        await bot.send_message(chat_id=f"@{CONFESSION_CHANNEL}", text=f"📜 ИСПОВЕДЬ ПСА\n\nОт: @{username}\n\n{text}")
    except:
        pass

@router.message(F.photo)
async def get_file_id_for_admin(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"FILE_ID: {message.photo[-1].file_id}")

@router.message(Command("start"))
async def cmd_start(message: Message):
    await create_player(message.from_user.id, message.from_user.username or message.from_user.first_name)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Играть", callback_data="start_game")],
        [InlineKeyboardButton(text="🔄 Начать заново", callback_data="reset_game")],
        [InlineKeyboardButton(text="🏆 Рейтинг", callback_data="show_top")],
        [InlineKeyboardButton(text="🏅 Достижения", callback_data="show_achievements")]
    ])
    await message.answer("🐕 Добро пожаловать!\n\nТы — пёс. Твоя цель — заслужить уважение Богини Милы.", reply_markup=keyboard)

@router.callback_query(F.data == "start_game")
async def start_game(callback: CallbackQuery):
    user_id = callback.from_user.id
    current_scene_id =
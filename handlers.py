from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS
from database import init_db, get_player, create_player

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    await create_player(user_id, username)
    
    await message.answer(
        f"🐕 Добро пожаловать, {username}!\n\n"
        "Ты — пёс. Твоя цель — заслужить уважение Домины.\n"
        "Будешь слушаться? Жди приказов.\n\n"
        "🎮 Доступные команды:\n"
        "/status — твои параметры\n"
        "/play — продолжить игру\n"
        "/a — админ-панель (только для админов)"
    )

@router.message(Command("status"))
async def cmd_status(message: Message):
    player = await get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    
    await message.answer(
        f"📊 **Твои параметры:**\n"
        f"🐕 Подчинение: {player[2]}\n"
        f"⚔️ Смелость: {player[3]}\n"
        f"👁 Внимание Домины: {player[4]}\n"
        f"📖 Текущая глава: {player[5]}",
        parse_mode="Markdown"
    )

@router.message(Command("play"))
async def cmd_play(message: Message):
    player = await get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    
    # Пока заглушка
    await message.answer(
        "🚧 Глава в разработке...\n"
        "Скоро здесь появится первый выбор."
    )

@router.message(Command("a"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Нет прав")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить картинку", callback_data="admin_add_img")],
        [InlineKeyboardButton(text="📋 Список игроков", callback_data="admin_players")],
    ])
    await message.answer("🔧 Админ-панель", reply_markup=keyboard)

# Заглушки для callback'ов
@router.callback_query(lambda c: c.data == "admin_add_img")
async def admin_add_img(callback, state: FSMContext):
    await callback.answer("🚧 В разработке", show_alert=True)

@router.callback_query(lambda c: c.data == "admin_players")
async def admin_players(callback):
    await callback.answer("🚧 В разработке", show_alert=True)
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

def set_bot(bot_instance):
    global bot
    bot = bot_instance

async def check_channel_subscription(user_id: int, channel_username: str) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=f"@{channel_username}", user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def post_to_channels(text: str):
    for channel in CHANNELS:
        try:
            await bot.send_message(f"@{channel}", text)
            print(f"✅ Пост в @{channel}")
        except Exception as e:
            print(f"❌ Ошибка @{channel}: {e}")

@router.message(F.photo)
async def get_file_id_for_admin(message: Message):
    if message.from_user.id == ADMIN_ID:
        file_id = message.photo[-1].file_id
        await message.answer(f"FILE_ID: {file_id}")

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    await create_player(user_id, username)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Играть", callback_data="start_game")],
        [InlineKeyboardButton(text="🔄 Начать заново", callback_data="reset_game")]
    ])
    await message.answer(
        f"🐕 Добро пожаловать, {username}!\n\nТы — пёс. Твоя цель — заслужить уважение Богини Милы.\n\n📌 Используй кнопки ниже:",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "start_game")
async def start_game(callback: CallbackQuery):
    user_id = callback.from_user.id
    current_scene_id = await get_current_scene(user_id)
    scene = scenes.get(current_scene_id)
    if not scene:
        scene = scenes.get("prolog_scene1")
    try:
        await callback.message.delete()
    except:
        pass
    await show_scene(callback.message, user_id, scene, current_scene_id)

@router.callback_query(F.data == "reset_game")
async def reset_game(callback: CallbackQuery):
    user_id = callback.from_user.id
    await reset_player(user_id)
    try:
        await callback.message.delete()
    except:
        pass
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Играть", callback_data="start_game")]
    ])
    await callback.message.answer("🔄 Прогресс сброшен!\n\nТы начинаешь с чистого листа.", reply_markup=keyboard)

@router.message(Command("play"))
async def cmd_play(message: Message):
    user_id = message.from_user.id
    if not await get_player(user_id):
        await message.answer("Сначала напиши /start")
        return
    current_scene_id = await get_current_scene(user_id)
    scene = scenes.get(current_scene_id)
    if not scene:
        scene = scenes.get("prolog_scene1")
    await show_scene(message, user_id, scene, current_scene_id)

async def show_scene(message: Message, user_id: int, scene: dict, scene_id: str):
    text = scene["text"]
    choices = scene.get("choices", [])
    photo = scene.get("photo")
    
    keyboard = None
    if choices:
        keyboard_buttons = []
        for idx, choice in enumerate(choices):
            keyboard_buttons.append([InlineKeyboardButton(text=choice["text"], callback_data=f"choice_{scene_id}_{idx}")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    if photo:
        await message.answer_photo(photo=photo, caption=text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("choice_"))
async def handle_choice(callback: CallbackQuery):
    user_id = callback.from_user.id
    parts = callback.data.split("_")
    scene_id = "_".join(parts[1:-1])
    choice_idx = int(parts[-1])
    
    scene = scenes.get(scene_id)
    if not scene:
        await callback.message.answer("❌ Ошибка: сцена не найдена")
        return
    
    choices = scene.get("choices", [])
    if choice_idx >= len(choices):
        await callback.message.answer("❌ Ошибка: выбор не найден")
        return
    
    choice = choices[choice_idx]
    next_scene_id = choice.get("next_scene")
    
    # Проверка подписки
    if next_scene_id == "chap5_check":
        channels_ok = all([await check_channel_subscription(user_id, ch) for ch in CHANNELS])
        if channels_ok:
            await verify_tasks(user_id)
            await callback.message.edit_text("✅ Богиня Мила довольна! Ты выполнил задания. Продолжай свой путь.")
            await asyncio.sleep(1)
            next_scene_id = "chap5_scene1"
        else:
            await callback.message.edit_text("❌ Ты не подписан на каналы @chat_goddes и @find_goddes. Подпишись и нажми снова.")
            await asyncio.sleep(2)
            await update_current_scene(user_id, "chap5_tasks")
            await show_scene(callback.message, user_id, scenes["chap5_tasks"], "chap5_tasks")
            return
    
    # ========== ПОСТ В КАНАЛЫ ПРИ ЛЮБОЙ КОНЦОВКЕ ==========
    if next_scene_id in ["chap6_ideal", "chap6_neutral", "chap6_bad"]:
        # Сохраняем концовку
        if next_scene_id == "chap6_ideal":
            await set_ending(user_id, "ideal")
            final_title = "🏆 ИДЕАЛЬНЫЙ ФИНАЛ 🏆"
        elif next_scene_id == "chap6_neutral":
            await set_ending(user_id, "neutral")
            final_title = "🔸 НЕЙТРАЛЬНЫЙ ФИНАЛ 🔸"
        elif next_scene_id == "chap6_bad":
            await set_ending(user_id, "bad")
            final_title = "🔻 ПЛОХОЙ ФИНАЛ 🔻"
        
        # Отправляем пост
        player = await get_player(user_id)
        username = player[1] if player else "Неизвестный пёс"
        
        post_text = f"📢 НОВОЕ ПРОХОЖДЕНИЕ!\n\n@{username} прошёл игру «Бесконечное унижение»\n\nРезультат: {final_title}\n\n🤖 БОТ ДЛЯ ПСИН И ДОМИН: @dominasearch24_bot"
        
        for channel in CHANNELS:
            try:
                await bot.send_message(f"@{channel}", post_text)
                print(f"✅ Пост отправлен в @{channel}")
            except Exception as e:
                print(f"❌ Ошибка @{channel}: {e}")
    
    if next_scene_id:
        await update_current_scene(user_id, next_scene_id)
        next_scene = scenes.get(next_scene_id)
        if next_scene:
            try:
                await callback.message.delete()
            except:
                pass
            await show_scene(callback.message, user_id, next_scene, next_scene_id)

@router.callback_query(F.data == "reset_and_play")
async def reset_and_play(callback: CallbackQuery):
    user_id = callback.from_user.id
    await reset_player(user_id)
    try:
        await callback.message.delete()
    except:
        pass
    await cmd_play(callback.message)

@router.message(Command("reset"))
async def cmd_reset(message: Message):
    user_id = message.from_user.id
    await reset_player(user_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Играть", callback_data="start_game")]
    ])
    await message.answer("🔄 Прогресс сброшен!\n\nНачинай сначала командой /play", reply_markup=keyboard)

@router.message(Command("a"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Нет прав")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить картинку", callback_data="admin_add_img")],
        [InlineKeyboardButton(text="📋 Список игроков", callback_data="admin_players")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")]
    ])
    await message.answer("🔧 АДМИН-ПАНЕЛЬ", reply_markup=keyboard)

@router.callback_query(F.data == "admin_add_img")
async def admin_add_img(callback: CallbackQuery):
    await callback.answer("📸 Отправь фото боту — я пришлю file_id", show_alert=True)

@router.callback_query(F.data == "admin_players")
async def admin_players(callback: CallbackQuery):
    players = await get_all_players()
    if not players:
        await callback.message.answer("📭 Нет игроков")
        return
    text = "👥 СПИСОК ИГРОКОВ:\n\n"
    for user_id, username, current_scene in players[:20]:
        text += f"• {username}\n"
    await callback.message.answer(text)

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    stats = await get_stats()
    await callback.message.answer(
        f"📊 СТАТИСТИКА БОТА:\n\n"
        f"👥 Всего игроков: {stats['total_players']}"
    )
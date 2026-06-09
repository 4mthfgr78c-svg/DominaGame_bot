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

async def post_confession_to_channels(text: str, username: str):
    message_text = f"📜 ИСПОВЕДЬ ПСА\n\nОт: @{username}\n\n{text}"
    for channel in CHANNELS:
        try:
            await bot.send_message(f"@{channel}", message_text)
        except:
            pass

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
        [InlineKeyboardButton(text="🔄 Начать заново", callback_data="reset_game")],
        [InlineKeyboardButton(text="🏆 Рейтинг", callback_data="show_top")],
        [InlineKeyboardButton(text="🏅 Достижения", callback_data="show_achievements")]
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
        [InlineKeyboardButton(text="▶️ Играть", callback_data="start_game")],
        [InlineKeyboardButton(text="🏆 Рейтинг", callback_data="show_top")]
    ])
    await callback.message.answer("🔄 Прогресс сброшен!\n\nТы начинаешь с чистого листа.", reply_markup=keyboard)

@router.callback_query(F.data == "show_top")
async def show_top_callback(callback: CallbackQuery):
    leaderboard = await get_leaderboard(10)
    if not leaderboard:
        await callback.message.answer("📊 Пока никого в рейтинге. Будь первым!")
        return
    text = "🏆 РЕЙТИНГ ПСОВ БОГИНИ МИЛЫ 🏆\n\n"
    for i, (username, attention, submission, _) in enumerate(leaderboard, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        text += f"{medal} {i}. {username} — уважение: {attention}, подчинение: {submission}\n"
    await callback.message.answer(text)

@router.callback_query(F.data == "show_achievements")
async def show_achievements_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    achievements = await get_achievements(user_id)
    if not achievements:
        await callback.message.answer("🏅 У тебя пока нет достижений. Проходи игру, чтобы их получить!")
        return
    text = "🏅 ТВОИ ДОСТИЖЕНИЯ 🏅\n\n"
    for ach in achievements:
        text += f"✓ {ach}\n"
    await callback.message.answer(text)

@router.message(Command("status"))
async def cmd_status(message: Message):
    player = await get_player(message.from_user.id)
    if not player:
        await message.answer("Сначала напиши /start")
        return
    attention = player[4]
    if attention >= 90:
        title = "Пёс Богини 👑"
    elif attention >= 60:
        title = "Любимчик ⭐"
    elif attention >= 30:
        title = "Сторожевой 🛡️"
    else:
        title = "Дворняга 🐕"
    await message.answer(
        f"📊 ТВОИ ПАРАМЕТРЫ:\n"
        f"👑 Звание: {title}\n"
        f"🐕 Подчинение: {player[2]}\n"
        f"⚔️ Смелость: {player[3]}\n"
        f"👁 Внимание Богини Милы: {player[4]}\n"
        f"😖 Стыд: {player[5]}\n"
        f"❤️ Привязанность: {player[6]}\n"
        f"😈 Бунт: {player[7]}"
    )

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
    effects = choice.get("effects", {})
    
    await update_player_stats(
        user_id,
        submission_delta=effects.get("submission", 0),
        bravery_delta=effects.get("bravery", 0),
        attention_delta=effects.get("attention", 0),
        shame_delta=effects.get("shame", 0),
        devotion_delta=effects.get("devotion", 0),
        rebellion_delta=effects.get("rebellion", 0)
    )
    
    next_scene_id = choice.get("next_scene")
    
    if next_scene_id == "chap5_check":
        channels_ok = all([await check_channel_subscription(user_id, ch) for ch in CHANNELS])
        if channels_ok:
            await verify_tasks(user_id)
            await add_achievement(user_id, "👑 Верный пёс Богини Милы")
            await callback.message.edit_text("✅ Богиня Мила довольна! Ты выполнил задания. Продолжай свой путь.")
            await asyncio.sleep(1)
            next_scene_id = "chap5_scene1"
        else:
            await callback.message.edit_text("❌ Ты не подписан на каналы @chat_goddes и @find_goddes. Подпишись и нажми снова.")
            await asyncio.sleep(2)
            await update_current_scene(user_id, "chap5_tasks")
            await show_scene(callback.message, user_id, scenes["chap5_tasks"], "chap5_tasks")
            return
    
    if next_scene_id == "chap6_ideal":
        await set_ending(user_id, "ideal")
    elif next_scene_id == "chap6_neutral":
        await set_ending(user_id, "neutral")
    elif next_scene_id == "chap6_bad":
        await set_ending(user_id, "bad")
    
    if next_scene_id:
        await update_current_scene(user_id, next_scene_id)
        next_scene = scenes.get(next_scene_id)
        if next_scene:
            try:
                await callback.message.delete()
            except:
                pass
            await show_scene(callback.message, user_id, next_scene, next_scene_id)

@router.callback_query(F.data == "open_confess")
async def open_confess(callback: CallbackQuery):
    await callback.message.answer("📝 Напиши свою исповедь командой /confess [текст]\n\nПример: /confess Я был непослушным псом")

@router.callback_query(F.data == "reset_and_play")
async def reset_and_play(callback: CallbackQuery):
    user_id = callback.from_user.id
    await reset_player(user_id)
    try:
        await callback.message.delete()
    except:
        pass
    await cmd_play(callback.message)

@router.message(Command("confess"))
async def cmd_confess(message: Message):
    user_id = message.from_user.id
    ending = await get_ending(user_id)
    
    if not ending:
        await message.answer("Ты ещё не прошёл игру. Исповедь доступна только после финала.")
        return
    
    text = message.text.replace("/confess", "").strip()
    if not text:
        await message.answer("Напиши свою исповедь после команды, например: /confess Я люблю быть псом")
        return
    
    username = message.from_user.username or message.from_user.first_name
    
    await post_confession_to_channels(text, username)
    
    await message.answer("🙏 Богиня Мила услышала твою исповедь.")

@router.message(Command("reset"))
async def cmd_reset(message: Message):
    user_id = message.from_user.id
    await reset_player(user_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Играть", callback_data="start_game")],
        [InlineKeyboardButton(text="🏆 Рейтинг", callback_data="show_top")]
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
    for user_id, username, submission, bravery, attention, scene in players[:20]:
        text += f"• {username} — подч: {submission}, уваж: {attention}\n"
    await callback.message.answer(text)

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    stats = await get_stats()
    await callback.message.answer(
        f"📊 СТАТИСТИКА БОТА:\n\n"
        f"👥 Всего игроков: {stats['total_players']}\n"
        f"🐕 Среднее подчинение: {stats['avg_submission']}\n"
        f"👁 Среднее внимание: {stats['avg_attention']}"
    )
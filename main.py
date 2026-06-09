import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import router, set_bot
from database import init_db

async def main():
    await init_db()
    
    bot = Bot(token=BOT_TOKEN)
    set_bot(bot)
    
    dp = Dispatcher()
    dp.include_router(router)
    
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
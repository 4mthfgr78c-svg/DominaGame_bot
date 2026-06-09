import aiosqlite

DB_NAME = "game.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                submission INTEGER DEFAULT 0,
                bravery INTEGER DEFAULT 0,
                attention INTEGER DEFAULT 0,
                current_chapter INTEGER DEFAULT 1
            )
        """)
        await db.commit()

async def get_player(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM players WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def create_player(user_id: int, username: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO players (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        await db.commit()
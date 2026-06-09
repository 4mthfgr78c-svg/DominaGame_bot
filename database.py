import aiosqlite
import json
import random
import string
from datetime import datetime

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
                shame INTEGER DEFAULT 0,
                devotion INTEGER DEFAULT 0,
                rebellion INTEGER DEFAULT 0,
                current_chapter INTEGER DEFAULT 1,
                current_scene TEXT DEFAULT 'prolog_scene1',
                bot_started INTEGER DEFAULT 0,
                channels_subscribed INTEGER DEFAULT 0,
                tasks_completed INTEGER DEFAULT 0,
                achievements TEXT DEFAULT '[]',
                last_action TEXT DEFAULT '',
                ending TEXT DEFAULT '',
                promo_code TEXT DEFAULT '',
                promo_expires INTEGER DEFAULT 0,
                dice_used INTEGER DEFAULT 0
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

async def update_player_stats(user_id: int, submission_delta=0, bravery_delta=0, attention_delta=0, shame_delta=0, devotion_delta=0, rebellion_delta=0):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """UPDATE players 
               SET submission = submission + ?,
                   bravery = bravery + ?,
                   attention = attention + ?,
                   shame = shame + ?,
                   devotion = devotion + ?,
                   rebellion = rebellion + ?
               WHERE user_id = ?""",
            (submission_delta, bravery_delta, attention_delta, shame_delta, devotion_delta, rebellion_delta, user_id)
        )
        await db.commit()

async def update_current_scene(user_id: int, scene_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE players SET current_scene = ? WHERE user_id = ?",
            (scene_id, user_id)
        )
        await db.commit()

async def get_current_scene(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT current_scene FROM players WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else "prolog_scene1"

async def reset_player(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """UPDATE players 
               SET submission = 0,
                   bravery = 0,
                   attention = 0,
                   shame = 0,
                   devotion = 0,
                   rebellion = 0,
                   current_chapter = 1,
                   current_scene = 'prolog_scene1',
                   bot_started = 0,
                   channels_subscribed = 0,
                   tasks_completed = 0,
                   achievements = '[]',
                   last_action = '',
                   ending = '',
                   promo_code = '',
                   promo_expires = 0,
                   dice_used = 0
               WHERE user_id = ?""",
            (user_id,)
        )
        await db.commit()

async def add_achievement(user_id: int, achievement: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT achievements FROM players WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            achievements = json.loads(row[0]) if row and row[0] else []
        
        if achievement not in achievements:
            achievements.append(achievement)
            await db.execute(
                "UPDATE players SET achievements = ? WHERE user_id = ?",
                (json.dumps(achievements), user_id)
            )
            await db.commit()
            return True
        return False

async def get_achievements(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT achievements FROM players WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return json.loads(row[0]) if row and row[0] else []

async def update_last_action(user_id: int, action: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE players SET last_action = ? WHERE user_id = ?",
            (action, user_id)
        )
        await db.commit()

async def get_leaderboard(limit=10):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """SELECT username, attention, submission, last_action 
               FROM players 
               ORDER BY attention DESC, submission DESC 
               LIMIT ?""",
            (limit,)
        ) as cursor:
            return await cursor.fetchall()

async def set_ending(user_id: int, ending: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE players SET ending = ? WHERE user_id = ?",
            (ending, user_id)
        )
        await db.commit()

async def get_ending(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT ending FROM players WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else ""

async def generate_promo_code(user_id: int) -> str:
    code = f"MILA25_{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
    expires = int(datetime.now().timestamp()) + 86400
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE players SET promo_code = ?, promo_expires = ? WHERE user_id = ?",
            (code, expires, user_id)
        )
        await db.commit()
    return code

async def verify_tasks(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE players SET tasks_completed = 1, attention = attention + 30 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

async def can_use_dice(user_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT dice_used FROM players WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] == 0 if row else True

async def mark_dice_used(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE players SET dice_used = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_all_players():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT user_id, username, submission, bravery, attention, current_scene FROM players ORDER BY attention DESC"
        ) as cursor:
            return await cursor.fetchall()

async def get_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM players") as cursor:
            total = (await cursor.fetchone())[0]
        
        async with db.execute("SELECT AVG(submission), AVG(attention) FROM players") as cursor:
            avg_sub, avg_att = await cursor.fetchone()
            
        return {
            "total_players": total,
            "avg_submission": round(avg_sub or 0, 1),
            "avg_attention": round(avg_att or 0, 1)
        }
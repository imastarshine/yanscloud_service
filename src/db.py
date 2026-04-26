import aiosqlite


class Database:
    def __init__(self):
        self.db: aiosqlite.Connection = None

    async def connect(self):
        self.db = await aiosqlite.connect("music.db")

    async def init(self):
        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS music (
            id INTEGER PRIMARY KEY,
            link TEXT NOT NULL,
            title TEXT,
            path TEXT,
            is_failed INTEGER DEFAULT 0,
            discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        await self._alter_add_is_failed_column()
        await self._alter_add_title_and_path_columns()
        await self.db.commit()

    async def _alter_add_is_failed_column(self):
        try:
            await self.db.execute(
                "ALTER TABLE music ADD COLUMN is_failed INTEGER DEFAULT 0"
            )
            await self.db.commit()
        except aiosqlite.OperationalError:
            pass

    async def _alter_add_title_and_path_columns(self):
        try:
            await self.db.execute("ALTER TABLE music ADD COLUMN title TEXT")
            await self.db.execute("ALTER TABLE music ADD COLUMN path TEXT")
            await self.db.commit()
        except aiosqlite.OperationalError:
            pass

    async def is_music_exists(self, link: str):
        async with self.db.execute("SELECT id, link FROM music WHERE link = ?", (link,)) as cursor:
            return await cursor.fetchone() is not None

    async def check_many(self, links: list[str]) -> set[str]:
        placeholders = ', '.join(['?'] * len(links))
        query = f"SELECT link FROM music WHERE link IN ({placeholders})"
        async with self.db.execute(query, links) as cursor:
            rows = await cursor.fetchall()
            existing_links = {row[0] for row in rows}
            return existing_links

    # Added "title" and "path" for future use (e.g., "sync" mode). This will delete files from the disk if they no longer exist in the liked tracks.
    async def add_music(self, link: str, title: str | None = None, path: str | None = None, is_failed: bool = False):
        await self.db.execute("""
            INSERT INTO music (link, title, path, is_failed) VALUES (?, ?, ?, ?)
        """, (link, title, path, is_failed,))
        await self.db.commit()

    async def remove_music(self, link: str):
        await self.db.execute("""
            DELETE FROM music WHERE link = ?
        """, (link,))
        await self.db.commit()


database = Database()

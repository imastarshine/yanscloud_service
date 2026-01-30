import sqlite3


class Database:
    def __init__(self):
        self.db = sqlite3.connect("music.db")
        self.cursor = self.db.cursor()

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS music(
                id INTEGER PRIMARY KEY,
                link TEXT,
                discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        self.db.commit()

    def is_music_exists(self, link: str):
        self.cursor.execute("""
        SELECT id, link FROM music WHERE link = ?
        """, (link,))
        return self.cursor.fetchone()

    def add_musicc(self, link: str):
        self.cursor.execute("""
        INSERT INTO music (link) VALUES (?)
        """, (link,))
        self.db.commit()

    def remove_music(self, link: str):
        self.cursor.execute("""
        DELETE FROM music WHERE link = ?
        """, (link,))
        self.db.commit()


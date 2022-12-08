import sqlite3
DATABASE_NAME = "persons.db"


def get_db():
    conn = sqlite3.connect(DATABASE_NAME)
    return conn


def create_tables():
    tables = [
        """CREATE TABLE IF NOT EXISTS person(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                description TEXT,
                 image Text,
				message TEXT
            )
            """,
            """
                 CREATE TABLE IF NOT EXISTS faces (person_id INTEGER, data json )"""
    ]
    db = get_db()
    cursor = db.cursor()
    for table in tables:
        cursor.execute(table)

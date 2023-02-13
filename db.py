import sqlite3
DATABASE_NAME = "persons.db"


def get_db():
    conn = sqlite3.connect(DATABASE_NAME)
    return conn


def create_tables():
    tables = [
        """CREATE TABLE IF NOT EXISTS MissingPerson(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                description TEXT,
                image Text,
				gender TEXT ,
                existence BOOLEAN,
                created_at TEXT)
            """,
             """CREATE TABLE IF NOT EXISTS FoundPerson(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                description TEXT,
                image Text,
				gender TEXT,
                existence BOOLEAN,
                created_at TEXT,
                FOREIGN KEY(id) REFERENCES FoundPerson(id)
                 )
            """,
            """CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email EMAIL TEXT NOT NULL,
                password TEXT NOT NULL ,
            CONSTRAINT email_unique UNIQUE (email))
             """,
            # # """
            #      CREATE TABLE IF NOT EXISTS faces (person_id INTEGER, data json )""",

            #       """CREATE TABLE IF NOT EXISTS users(
            #     id INTEGER PRIMARY KEY AUTOINCREMENT,
            #     username varchar(50) NOT NULL,
            #     password varchar(255) NOT NULL,
            #     email varchar(100) NOT NULL
            # )
            # """
    ]
    db = get_db()
    cursor = db.cursor()
    for table in tables:
        cursor.execute(table)

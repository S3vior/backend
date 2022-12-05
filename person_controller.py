from db import get_db


def insert_game(name,message):
    db = get_db()
    cursor = db.cursor()
    statement = "INSERT INTO person(name, message) VALUES (?,?)"
    cursor.execute(statement, [name, message])
    db.commit()
    return True


def update_person(id ,name, message):
    db = get_db()
    cursor = db.cursor()
    statement = "UPDATE person SET name = ?, message = ? WHERE id = ?"
    cursor.execute(statement, [id, name, message])
    db.commit()
    return True


def delete_person(id):
    db = get_db()
    cursor = db.cursor()
    statement = "DELETE FROM person WHERE id = ?"
    cursor.execute(statement, [id])
    db.commit()
    return True


def get_by_id(id):
    db = get_db()
    cursor = db.cursor()
    statement = "SELECT id, name, message FROM person WHERE id = ?"
    cursor.execute(statement, [id])
    return cursor.fetchone()


def get_games():
    db = get_db()
    cursor = db.cursor()
    query = "SELECT id, name, message FROM person"
    cursor.execute(query)
    return cursor.fetchall()

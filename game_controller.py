from db import get_db


def insert_game(name,message):
    db = get_db()
    cursor = db.cursor()
    statement = "INSERT INTO person(name, message) VALUES (?,?)"
    cursor.execute(statement, [name, message])
    db.commit()
    return True


def update_game(id, name, image_encodings, message):
    db = get_db()
    cursor = db.cursor()
    statement = "UPDATE person SET name = ?, image_encodings = ?, message = ? WHERE id = ?"
    cursor.execute(statement, [name, image_encodings, message])
    db.commit()
    return True


# def delete_game(id):
#     db = get_db()
#     cursor = db.cursor()
#     statement = "DELETE FROM games WHERE id = ?"
#     cursor.execute(statement, [id])
#     db.commit()
#     return True


def get_by_id(id):
    db = get_db()
    cursor = db.cursor()
    statement = "SELECT id, name, image_encodings, message FROM person WHERE id = ?"
    cursor.execute(statement, [id])
    return cursor.fetchone()


def get_games():
    db = get_db()
    cursor = db.cursor()
    query = "SELECT id, name, message FROM person"
    cursor.execute(query)
    return cursor.fetchall()

from db import get_db


def insert_person(name,age,description,gender,image,created_at):
    db = get_db()
    cursor = db.cursor()
    statement = "INSERT INTO MissingPerson(name,age,description,gender,image,created_at) VALUES (?,?,?,?,?,?)"
    cursor.execute(statement, [name,age,description,gender,image,created_at])
    db.commit()
    return True


def update_person(id ,name,message):
    db = get_db()
    cursor = db.cursor()
    statement = "UPDATE MissingPerson SET name = ?, message = ? WHERE id = ?"
    cursor.execute(statement, [id, name, message])
    db.commit()
    return True


def delete_person(id):
    db = get_db()
    cursor = db.cursor()
    statement = "DELETE FROM MissingPerson WHERE id = ?"
    cursor.execute(statement, [id])
    db.commit()
    return True


def get_by_id(id):
    db = get_db()
    cursor = db.cursor()
    statement = "SELECT name,age,description,gender,image,created_at FROM MissingPerson WHERE id = ?"
    cursor.execute(statement, [id])
    return cursor.fetchone()


def get_persons():
    db = get_db()
    cursor = db.cursor()
    query = "SELECT id, name,age,description,gender,image,created_at FROM MissingPerson"
    cursor.execute(query)
    persons = cursor.fetchall()
    return persons

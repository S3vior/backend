from db import get_db


def insert_user(name,email,password):
    db = get_db()
    cursor = db.cursor()
    statement = "INSERT INTO users(name,email,password) VALUES (?,?,?)"
    cursor.execute(statement, [name,email,password])
    db.commit()
    return True


# def update_person(id ,name,message):
#     db = get_db()
#     cursor = db.cursor()
#     statement = "UPDATE person SET name = ?, message = ? WHERE id = ?"
#     cursor.execute(statement, [id, name, message])
#     db.commit()
#     return True


# def delete_person(id):
#     db = get_db()
#     cursor = db.cursor()
#     statement = "DELETE FROM person WHERE id = ?"
#     cursor.execute(statement, [id])
#     db.commit()
#     return True


def get_by_email(email):
    db = get_db()
    cursor = db.cursor()
    statement = "SELECT id, name,email,password FROM users WHERE email = ?"
    cursor.execute(statement, [email])
    return cursor.fetchone()


def get_by_id(id):
    db = get_db()
    cursor = db.cursor()
    statement = "SELECT id, name,email,password FROM users WHERE id = ?"
    cursor.execute(statement, [id])
    return cursor.fetchone()


def get_users():
    db = get_db()
    cursor = db.cursor()
    query = "SELECT id, name,phone_number,email FROM users"
    cursor.execute(query)
    users = cursor.fetchall()
    return users



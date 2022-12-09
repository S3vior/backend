from db import get_db

def insert_face(person_id,data):
    db = get_db()
    cursor = db.cursor()
    statement = "INSERT INTO faces(person_id,data) VALUES (?,?)"
    cursor.execute(statement, [person_id,data])
    db.commit()
    return True


def get_by_id(id):
    db = get_db()
    cursor = db.cursor()
    statement = "SELECT  data FROM faces WHERE person_id = ?"
    cursor.execute(statement, [id])
    return cursor.fetchone()


def get_faces():
    db = get_db()
    cursor = db.cursor()
    query = "SELECT person_id, data FROM faces"
    cursor.execute(query)
    faces = cursor.fetchall()
    return faces

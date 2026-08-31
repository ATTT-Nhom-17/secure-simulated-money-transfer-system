import db


def get_db():
    conn = db.get_connection()
    try:
        yield conn
    finally:
        conn.close()

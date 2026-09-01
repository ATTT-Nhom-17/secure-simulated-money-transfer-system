import os
import sys

# tro toi thu muc db/ moi import duoc db.py, vi backend/ va db/ la 2 thu muc rieng
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "db"))
import db


def get_db():
    conn = db.get_connection()
    try:
        yield conn
    finally:
        conn.close()

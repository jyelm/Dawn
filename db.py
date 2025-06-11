import sqlite3

def init_db():
    db = sqlite3.connect("chat_history.db")
    db.execute(
        "CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT)"
    )
    db.commit()
    db.close()

# call init_db() at startup

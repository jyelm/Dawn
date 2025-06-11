from fastapi import FastAPI
import sqlite3
import uvicorn
import threading

app = FastAPI()
DATABASE = "chat_history.db"

# Helper function to get a DB connection
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.post("/messages/")
async def add_message(content: str):
    db = get_db()
    db.execute("INSERT INTO messages (content) VALUES (?)", (content,))
    db.commit()
    db.close()
    return {"status": "ok"}

@app.get("/messages/")
async def get_messages(limit: int = 50):
    db = get_db()
    rows = db.execute(
        "SELECT content FROM messages ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    db.close()
    return [row["content"] for row in rows]

def make_server():
    uvicorn.run(app, host="127.0.0.1", port=8000)

def run_api():
    threading.Thread(target = make_server(), args = (), daemon=True).start()


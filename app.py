from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, os
from datetime import datetime
from werkzeug.utils import secure_filename

# ================= CONFIG =================
DB_NAME = "players.db"
AVATAR_DIR = "static/avatars"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

os.makedirs(AVATAR_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ================= DATABASE =================
def connect_db():
    return sqlite3.connect(DB_NAME)

def create_tables():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_name TEXT,
        game TEXT,
        username TEXT UNIQUE,
        level INTEGER,
        team TEXT,
        role TEXT,
        favorite TEXT,
        avatar TEXT,
        date_registered TEXT
    )
    """)
    conn.commit()
    conn.close()

create_tables()

# ================= UTILITIES =================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_rank(level, game):
    if not level or not str(level).isdigit():
        return "Unranked"
    lvl = int(level)
    if game == "Valorant":
        if lvl <= 5: return "Iron"
        elif lvl <= 10: return "Bronze"
        elif lvl <= 15: return "Silver"
        elif lvl <= 20: return "Gold"
        elif lvl <= 25: return "Platinum"
        elif lvl <= 30: return "Diamond"
        elif lvl <= 35: return "Immortal"
        else: return "Radiant"
    else:
        if lvl <= 10: return "Beginner"
        elif lvl <= 30: return "Pro"
        elif lvl <= 50: return "Elite"
        else: return "Mythic"

# ================= ROUTES =================

# --- User page (table) ---
@app.route("/")
def user_page():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM players")
    players = cur.fetchall()
    conn.close()
    return render_template("user.html", players=players, get_rank=get_rank)

# --- Register page ---
@app.route("/register")
def register_page():
    return render_template("register.html")

# --- Add player ---
@app.route("/add", methods=["POST"])
def add_player():
    name = request.form.get("player_name")
    username = request.form.get("username")
    level = request.form.get("level") or 0
    team = request.form.get("team")
    game = request.form.get("game")
    role = request.form.get("role")
    favorite = request.form.get("favorite")
    avatar_file = request.files.get("avatar")
    avatar_path = ""

    if avatar_file and allowed_file(avatar_file.filename):
        filename = secure_filename(avatar_file.filename)
        avatar_file.save(os.path.join(AVATAR_DIR, filename))
        avatar_path = f"avatars/{filename}"

    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute("""
        INSERT INTO players (player_name, game, username, level, team, role, favorite, avatar, date_registered)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, game, username, level, team, role, favorite, avatar_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    except sqlite3.IntegrityError:
        flash("Username already exists", "danger")
        conn.close()
        return redirect(url_for("register_page"))
    conn.close()
    return render_template("success.html", action="added")

# --- Delete player ---
@app.route("/delete/<int:player_id>")
def delete_player(player_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM players WHERE id=?", (player_id,))
    conn.commit()
    conn.close()
    return render_template("success.html", action="deleted")

# --- Top 5 players ---
@app.route("/top")
def top_players():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM players ORDER BY level DESC LIMIT 5")
    top5 = cur.fetchall()
    conn.close()
    return render_template("top.html", top5=top5, get_rank=get_rank)

# ================= START =================
if __name__ == "__main__":
    app.run(debug=True)

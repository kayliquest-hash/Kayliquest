from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from datetime import date, datetime, timedelta
from flask import jsonify
import cloudinary
import cloudinary.uploader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.secret_key = "kayliquest2026"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
cloudinary.config(
    cloud_name="tx3qtpcx",
    api_key="138818719392132",                            api_secret="RBOQtknn9AwKpI2doJeEjo2OgiQ",
    secure=True
)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.template_filter("time_ago")
def time_ago(value):
    if not value:
        return ""

    try:
        dt = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return ""

    diff = datetime.now() - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return "à l'instant"
    if seconds < 3600:
        return f"il y a {int(seconds // 60)}min"
    if seconds < 86400:
        return f"il y a {int(seconds // 3600)}h"
    if seconds < 604800:
        return f"il y a {int(seconds // 86400)}j"

    return dt.strftime("%d/%m/%Y")

@app.template_filter("format_count")
def format_count(n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        return n

    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    if n >= 1_000:
        return f"{n/1_000:.1f}".rstrip("0").rstrip(".") + "K"

    return str(n)

@app.route("/test")
def test():
    return "KAYLI QUEST OK"

# -------------------------
# Base de données
# -------------------------

def init_db():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pseudo TEXT,
        email TEXT,
        password TEXT,
        bio TEXT,
        photo TEXT,
        xp INTEGER DEFAULT 0,
        niveau INTEGER DEFAULT 1,
        quetes INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        image TEXT,
        description TEXT,
        views INTEGER DEFAULT 0
    )
    """)
    
    try:
        cursor.execute("""
        ALTER TABLE posts
        ADD COLUMN views INTEGER DEFAULT 0
        """)
    except:
        pass
    
    cursor.execute("""
CREATE TABLE IF NOT EXISTS likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    post_id INTEGER
   )
   """)
   
    cursor.execute("""
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    post_id INTEGER,
    commentaire TEXT
    )
    """)

    try:
        cursor.execute("ALTER TABLE comments ADD COLUMN created_at TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
CREATE TABLE IF NOT EXISTS friends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    receiver_id INTEGER,
    status TEXT DEFAULT 'pending'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        title TEXT,
        description TEXT,
        type TEXT,
        target INTEGER,
        xp_reward INTEGER,
        icon TEXT
    )
    """)

    try:
        cursor.execute("ALTER TABLE quests ADD COLUMN frequency TEXT DEFAULT 'daily'")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quest_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        quest_id INTEGER,
        date TEXT,
        progress INTEGER DEFAULT 0,
        completed INTEGER DEFAULT 0,
        claimed INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        actor_id INTEGER,
        type TEXT,
        post_id INTEGER,
        is_read INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        post_id INTEGER,
        created_at TEXT,
        UNIQUE(user_id, post_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS follows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        follower_id INTEGER,
        following_id INTEGER,
        created_at TEXT,
        UNIQUE(follower_id, following_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1_id INTEGER,
        user2_id INTEGER,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        sender_id INTEGER,
        content TEXT,
        created_at TEXT,
        is_read INTEGER DEFAULT 0
    )
    """)

    default_quests = [
        ("post_1", "Publie une quête", "Publie 1 photo ou vidéo aujourd'hui", "post", 1, 20, "📸", "daily"),
        ("like_3", "Soutiens la guilde", "Aime 3 publications aujourd'hui", "like", 3, 15, "❤️", "daily"),
        ("comment_1", "Prends la parole", "Laisse 1 commentaire aujourd'hui", "comment", 1, 10, "💬", "daily"),
        ("friend_1", "Étends ta guilde", "Envoie 1 demande d'ami aujourd'hui", "friend", 1, 15, "🤝", "daily"),
        ("view_5", "Explore le royaume", "Regarde 5 publications aujourd'hui", "view", 5, 10, "👀", "daily"),
        ("post_5_week", "Créateur assidu", "Publie 5 photos ou vidéos cette semaine", "post", 5, 80, "📸", "weekly"),
        ("like_20_week", "Pilier de la guilde", "Aime 20 publications cette semaine", "like", 20, 60, "❤️", "weekly"),
        ("comment_10_week", "Voix de la guilde", "Laisse 10 commentaires cette semaine", "comment", 10, 50, "💬", "weekly"),
        ("friend_3_week", "Bâtisseur de guilde", "Envoie 3 demandes d'ami cette semaine", "friend", 3, 60, "🤝", "weekly"),
        ("view_50_week", "Grand explorateur", "Regarde 50 publications cette semaine", "view", 50, 50, "👀", "weekly"),
    ]

    cursor.executemany("""
    INSERT OR IGNORE INTO quests
    (code, title, description, type, target, xp_reward, icon, frequency)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, default_quests)

    conn.commit()
    conn.close()

init_db()

# -------------------------
# Helpers - Quêtes
# -------------------------

def today_str():
    return date.today().isoformat()

def week_str():
    return datetime.now().strftime("%G-W%V")

def period_for(frequency):
    return week_str() if frequency == "weekly" else today_str()

def get_or_create_progress(cursor, user_id, quest_id, period):

    cursor.execute("""
    SELECT id, progress, completed, claimed
    FROM quest_progress
    WHERE user_id=? AND quest_id=? AND date=?
    """, (user_id, quest_id, period))

    row = cursor.fetchone()

    if row:
        return row

    cursor.execute("""
    INSERT INTO quest_progress
    (user_id, quest_id, date, progress, completed, claimed)
    VALUES (?, ?, ?, 0, 0, 0)
    """, (user_id, quest_id, period))

    return (cursor.lastrowid, 0, 0, 0)

def bump_quest_progress(user_id, quest_type, amount=1):

    if not user_id:
        return

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, target, frequency FROM quests WHERE type=?",
        (quest_type,)
    )

    quests_of_type = cursor.fetchall()

    for quest_id, target, frequency in quests_of_type:

        period = period_for(frequency)

        prog_id, progress, completed, claimed = get_or_create_progress(
            cursor, user_id, quest_id, period
        )

        if completed:
            continue

        progress += amount
        completed_now = 1 if progress >= target else 0

        cursor.execute("""
        UPDATE quest_progress
        SET progress=?, completed=?
        WHERE id=?
        """, (min(progress, target), completed_now, prog_id))

    conn.commit()
    conn.close()

@app.context_processor
def inject_unread_notifications():

    if "user_id" not in session:
        return {"unread_notif_count": 0}

    conn = sqlite3.connect("database.db")

    count = conn.execute("""
    SELECT COUNT(*) FROM notifications
    WHERE user_id=? AND is_read=0
    """, (session["user_id"],)).fetchone()[0]

    conn.close()

    return {"unread_notif_count": count}

# -------------------------
# Helpers - Notifications
# -------------------------

def create_notification(user_id, actor_id, notif_type, post_id=None):

    if not user_id or not actor_id or user_id == actor_id:
        return

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO notifications
    (user_id, actor_id, type, post_id, is_read, created_at)
    VALUES (?, ?, ?, ?, 0, ?)
    """, (
        user_id,
        actor_id,
        notif_type,
        post_id,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

# -------------------------
# Helpers - Messagerie
# -------------------------

def get_or_create_conversation(cursor, conn, user_a, user_b):

    u1, u2 = sorted([user_a, user_b])

    cursor.execute("""
    SELECT id FROM conversations
    WHERE user1_id=? AND user2_id=?
    """, (u1, u2))

    row = cursor.fetchone()

    if row:
        return row[0]

    cursor.execute("""
    INSERT INTO conversations (user1_id, user2_id, created_at)
    VALUES (?, ?, ?)
    """, (u1, u2, datetime.now().isoformat()))

    conn.commit()

    return cursor.lastrowid

# -------------------------
# Accueil
# -------------------------

@app.route("/")
def home():
    return render_template("index.html")

# -------------------------
# Inscription
# -------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    erreur = ""

    if request.method == "POST":

        pseudo = request.form["pseudo"]
        email = request.form["email"].lower()
        password = request.form["password"]
        bio = request.form["bio"]

        photo = request.files["photo"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE pseudo=?",
            (pseudo,)
        )

        if cursor.fetchone():

            conn.close()

            return render_template(
                "register.html",
                erreur="Ce pseudo est déjà utilisé."
            )

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        if cursor.fetchone():

            conn.close()

            return render_template(
                "register.html",
                erreur="Cet email est déjà utilisé."
            )

        filename = photo.filename

        photo.save(
            os.path.join(
                UPLOAD_FOLDER,
                filename
            )
        )

        cursor.execute("""
        INSERT INTO users
        (
            pseudo,
            email,
            password,
            bio,
            photo
        )
        VALUES (?, ?, ?, ?, ?)
        """, (
            pseudo,
            email,
            password,
            bio,
            filename
        ))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template(
        "register.html",
        erreur=erreur
    )

# -------------------------
# Connexion
# -------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].lower()
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email=?
            AND password=?
            """,
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            session.permanent = True
            session["user_id"] = user[0]

            return redirect("/feed")

        return render_template(
            "login.html",
            erreur="Email ou mot de passe incorrect."
        )

    return render_template(
        "login.html",
        erreur=""
    )

# -------------------------
# Profil
# -------------------------

@app.route("/profile")
def profile():

    if "user_id" not in session:

        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    )

    user = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM posts WHERE user_id=? ORDER BY id DESC",
        (session["user_id"],)
    )

    posts = cursor.fetchall()

    cursor.execute("""
    SELECT COUNT(*) FROM friends
    WHERE status='accepted'
    AND (sender_id=? OR receiver_id=?)
    """, (session["user_id"], session["user_id"]))

    nb_amis = cursor.fetchone()[0]

    cursor.execute("""
    SELECT posts.*
    FROM saved_posts
    JOIN posts ON posts.id = saved_posts.post_id
    WHERE saved_posts.user_id=?
    ORDER BY saved_posts.id DESC
    """, (session["user_id"],))

    playlist = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM follows WHERE following_id=?", (session["user_id"],))
    nb_abonnes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM follows WHERE follower_id=?", (session["user_id"],))
    nb_abonnements = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "profile.html",
        user=user,
        nb_abonnes=nb_abonnes,
        nb_abonnements=nb_abonnements,
        posts=posts,
        nb_amis=nb_amis,
        playlist=playlist
    )

# -------------------------
# Publication
# -------------------------

@app.route("/create_post", methods=["GET", "POST"])
def create_post():

    if "user_id" not in session:

        return redirect("/login")

    if request.method == "POST":

        description = request.form["description"]
        media = request.files["media"]

        upload = cloudinary.uploader.                       upload(media)

        filename = upload["secure_url"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO posts
        (
            user_id,
            image,
            description
        )
        VALUES (?, ?, ?)
        """, (
            session["user_id"],
            filename,
            description
        ))
             
        conn.commit()
        conn.close()

        bump_quest_progress(session["user_id"], "post")

        return redirect("/profile")

    return render_template(
        "create_post.html"
    )

# -------------------------
# Quête
# -------------------------

@app.route("/quest")
def quest():

    if "user_id" not in session:

        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, title, description, target, xp_reward, icon, type, frequency
    FROM quests
    ORDER BY id
    """)

    all_quests = cursor.fetchall()

    quests_data = []

    for q in all_quests:

        quest_id, title, description, target, xp_reward, icon, quest_type, frequency = q

        period = period_for(frequency)

        prog_id, progress, completed, claimed = get_or_create_progress(
            cursor, session["user_id"], quest_id, period
        )

        quests_data.append({
            "id": quest_id,
            "title": title,
            "description": description,
            "target": target,
            "xp_reward": xp_reward,
            "type": quest_type,
            "frequency": frequency,
            "progress": progress,
            "completed": bool(completed),
            "claimed": bool(claimed),
        })

    conn.commit()

    cursor.execute(
        "SELECT xp, niveau, quetes FROM users WHERE id=?",
        (session["user_id"],)
    )

    xp, niveau, quetes = cursor.fetchone()

    conn.close()

    daily_quests = [q for q in quests_data if q["frequency"] != "weekly"]
    weekly_quests = [q for q in quests_data if q["frequency"] == "weekly"]

    return render_template(
        "quest.html",
        daily_quests=daily_quests,
        weekly_quests=weekly_quests,
        xp=xp,
        niveau=niveau,
        quetes=quetes
    )

@app.route("/quest/claim/<int:quest_id>", methods=["POST"])
def claim_quest(quest_id):

    if "user_id" not in session:
        return jsonify({"success": False}), 401

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT xp_reward, frequency FROM quests WHERE id=?",
        (quest_id,)
    )

    quest_row = cursor.fetchone()

    if not quest_row:
        conn.close()
        return jsonify({"success": False})

    xp_reward, frequency = quest_row
    period = period_for(frequency)

    cursor.execute("""
    SELECT id, completed, claimed
    FROM quest_progress
    WHERE user_id=? AND quest_id=? AND date=?
    """, (session["user_id"], quest_id, period))

    row = cursor.fetchone()

    if not row or not row[1] or row[2]:
        conn.close()
        return jsonify({"success": False})

    cursor.execute(
        "UPDATE quest_progress SET claimed=1 WHERE id=?",
        (row[0],)
    )

    cursor.execute(
        "SELECT xp, niveau, quetes FROM users WHERE id=?",
        (session["user_id"],)
    )

    xp, niveau, quetes = cursor.fetchone()

    xp += xp_reward
    quetes += 1

    leveled_up = False

    while xp >= 100:
        xp -= 100
        niveau += 1
        leveled_up = True

    cursor.execute("""
    UPDATE users
    SET xp=?, niveau=?, quetes=?
    WHERE id=?
    """, (xp, niveau, quetes, session["user_id"]))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "xp": xp,
        "niveau": niveau,
        "quetes": quetes,
        "leveled_up": leveled_up
    })

# -------------------------
# Déconnexion
# -------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# -------------------------
# Liste utilisateurs
# -------------------------

@app.route("/users")
def users():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users"
    )

    data = cursor.fetchall()

    conn.close()

    return str(data)
   
#--------------------------
#Fil d’actualité
#--------------------------   
   
@app.route("/feed")
def feed():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    current_user = session.get("user_id", 0)

    cursor.execute("""
    SELECT
        posts.*,
        users.pseudo,
        users.photo,
        users.niveau,
        COUNT(DISTINCT likes.id),
        COUNT(DISTINCT comments.id),
        MAX(CASE WHEN likes.user_id = ? THEN 1 ELSE 0 END)
    FROM posts

    JOIN users
        ON posts.user_id = users.id

    LEFT JOIN likes
        ON posts.id = likes.post_id

    LEFT JOIN comments
        ON posts.id = comments.post_id

    GROUP BY posts.id

    ORDER BY posts.id DESC
    """, (current_user,))

    rows = cursor.fetchall()

    posts = []

    for row in rows:

        cursor.execute("""
        SELECT comments.commentaire, users.pseudo, comments.created_at
        FROM comments
        JOIN users ON comments.user_id = users.id
        WHERE comments.post_id=?
        ORDER BY comments.id DESC
        LIMIT 1
        """, (row[0],))

        last_comment = cursor.fetchone()

        cursor.execute("""
        SELECT id FROM saved_posts
        WHERE user_id=? AND post_id=?
        """, (current_user, row[0]))

        is_saved = cursor.fetchone() is not None

        extension = row[2].split(".")[-1].lower() if row[2] else ""
        is_video = extension in ["mp4", "mov", "webm"]

        posts.append({
            "row": row,
            "last_comment": last_comment,
            "is_saved": is_saved,
            "is_video": is_video
        })

    conn.close()

    image_posts = [p for p in posts if not p["is_video"]]
    video_posts = [p for p in posts if p["is_video"]]

    return render_template(
        "feed.html",
        posts=image_posts,
        videos=video_posts
    )

#--------------------------
#Vues (feed)
#--------------------------

@app.route("/api/view/<int:post_id>", methods=["POST"])
def api_view(post_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE posts
    SET views = views + 1
    WHERE id=?
    """, (post_id,))

    conn.commit()
    conn.close()

    if "user_id" in session:
        bump_quest_progress(session["user_id"], "view")

    return jsonify({"success": True})

#--------------------------
#Likes
#---------------------------

@app.route("/like/<int:post_id>")
def like(post_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id
    FROM likes
    WHERE user_id=?
    AND post_id=?
    """, (
        session["user_id"],
        post_id
    ))

    like = cursor.fetchone()

    if like:

        cursor.execute("""
        DELETE FROM likes
        WHERE id=?
        """, (
            like[0],
        ))

    else:

        cursor.execute("""
        INSERT INTO likes
        (
            user_id,
            post_id
        )
        VALUES (?, ?)
        """, (
            session["user_id"],
            post_id
        ))

    conn.commit()
    conn.close()

    return redirect("/feed")
     
#--------------------------
#Recherche
#--------------------------

@app.route("/search")
def search():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, pseudo, photo, niveau
    FROM users
    WHERE id != ?
    ORDER BY pseudo COLLATE NOCASE
    """, (session["user_id"],))

    users = cursor.fetchall()

    conn.close()

    return render_template(
        "search.html",
        users=users
    )                

#‐-------------------------
#Amis
#-------------------------

@app.route("/friends")
def friends():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        friends.id,
        users.id,
        users.pseudo,
        users.photo
    FROM friends

    JOIN users
    ON friends.sender_id = users.id

    WHERE friends.receiver_id=?
    AND friends.status='pending'
    """, (
        session["user_id"],
    ))

    demandes = cursor.fetchall()

    nb_demandes = len(demandes)

    cursor.execute("""
    SELECT
        users.id,
        users.pseudo,
        users.photo,
        users.niveau
    FROM friends

    JOIN users
    ON users.id = (
        CASE WHEN friends.sender_id=? THEN friends.receiver_id ELSE friends.sender_id END
    )

    WHERE friends.status='accepted'
    AND (friends.sender_id=? OR friends.receiver_id=?)

    ORDER BY users.pseudo COLLATE NOCASE
    """, (
        session["user_id"],
        session["user_id"],
        session["user_id"]
    ))

    amis = cursor.fetchall()

    conn.close()

    return render_template(
        "friends.html",
        demandes=demandes,
        nb_demandes=nb_demandes,
        amis=amis
    )
                                                                            
                                                                                                           
@app.route("/api/like/<int:post_id>")
def api_like(post_id):

    if "user_id" not in session:
        return jsonify({"success": False})

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id
    FROM likes
    WHERE user_id=?
    AND post_id=?
    """, (
        session["user_id"],
        post_id
    ))

    like = cursor.fetchone()
    just_liked = False

    if like:

        cursor.execute("""
        DELETE FROM likes
        WHERE id=?
        """, (like[0],))

    else:

        cursor.execute("""
        INSERT INTO likes
        (user_id, post_id)
        VALUES (?, ?)
        """, (
            session["user_id"],
            post_id
        ))

        just_liked = True

    conn.commit()

    cursor.execute("""
    SELECT COUNT(*)
    FROM likes
    WHERE post_id=?
    """, (post_id,))

    total_likes = cursor.fetchone()[0]

    owner_row = None

    if just_liked:
        cursor.execute("SELECT user_id FROM posts WHERE id=?", (post_id,))
        owner_row = cursor.fetchone()

    conn.close()

    if just_liked:
        bump_quest_progress(session["user_id"], "like")

        if owner_row:
            create_notification(owner_row[0], session["user_id"], "like", post_id)

    return jsonify({
        "success": True,
        "likes": total_likes,
        "liked": just_liked
    })                                                                                                                                                   
#--------------------------
#Follow
#--------------------------

@app.route("/api/follow/<int:user_id>", methods=["POST"])
def api_follow(user_id):

    if "user_id" not in session:
        return jsonify({"success": False}), 401

    if user_id == session["user_id"]:
        return jsonify({"success": False, "error": "self"}), 400

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id FROM follows
    WHERE follower_id=? AND following_id=?
    """, (session["user_id"], user_id))

    row = cursor.fetchone()
    now_following = False

    if row:
        cursor.execute("DELETE FROM follows WHERE id=?", (row[0],))
    else:
        cursor.execute("""
        INSERT INTO follows (follower_id, following_id, created_at)
        VALUES (?, ?, ?)
        """, (session["user_id"], user_id, datetime.now().isoformat()))
        now_following = True

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM follows WHERE following_id=?", (user_id,))
    followers_count = cursor.fetchone()[0]

    conn.close()

    if now_following:
        create_notification(user_id, session["user_id"], "follow")

    return jsonify({
        "success": True,
        "following": now_following,
        "followers_count": followers_count
    })

@app.route("/followers/<int:user_id>")
def followers_list(user_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT pseudo FROM users WHERE id=?", (user_id,))
    target = cursor.fetchone()

    if not target:
        conn.close()
        return redirect("/feed")

    cursor.execute("""
    SELECT users.id, users.pseudo, users.photo, users.niveau
    FROM follows
    JOIN users ON users.id = follows.follower_id
    WHERE follows.following_id=?
    ORDER BY follows.id DESC
    """, (user_id,))

    people = cursor.fetchall()

    conn.close()

    return render_template(
        "follow_list.html",
        people=people,
        title="Abonnés",
        empty_message="Personne ne suit encore ce profil."
    )

@app.route("/following/<int:user_id>")
def following_list(user_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT pseudo FROM users WHERE id=?", (user_id,))
    target = cursor.fetchone()

    if not target:
        conn.close()
        return redirect("/feed")

    cursor.execute("""
    SELECT users.id, users.pseudo, users.photo, users.niveau
    FROM follows
    JOIN users ON users.id = follows.following_id
    WHERE follows.follower_id=?
    ORDER BY follows.id DESC
    """, (user_id,))

    people = cursor.fetchall()

    conn.close()

    return render_template(
        "follow_list.html",
        people=people,
        title="Abonnements",
        empty_message="Ce profil ne suit personne pour l'instant."
    )

#--------------------------
#Playlist (posts sauvegardés)
#--------------------------

@app.route("/api/save/<int:post_id>", methods=["POST"])
def api_save(post_id):

    if "user_id" not in session:
        return jsonify({"success": False}), 401

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id FROM saved_posts
    WHERE user_id=? AND post_id=?
    """, (session["user_id"], post_id))

    row = cursor.fetchone()
    now_saved = False

    if row:
        cursor.execute("DELETE FROM saved_posts WHERE id=?", (row[0],))
    else:
        cursor.execute("""
        INSERT INTO saved_posts (user_id, post_id, created_at)
        VALUES (?, ?, ?)
        """, (session["user_id"], post_id, datetime.now().isoformat()))
        now_saved = True

    conn.commit()
    conn.close()

    return jsonify({"success": True, "saved": now_saved})

#--------------------------
#Commentaires
#--------------------------

@app.route("/comments/<int:post_id>")
def comments(post_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
    comments.commentaire,
    users.pseudo,
    users.photo,
    users.id
    FROM comments
    JOIN users
    ON comments.user_id = users.id
    WHERE comments.post_id=?
    ORDER BY comments.id DESC
    """, (post_id,))

    commentaires = cursor.fetchall()

    conn.close()

    return render_template(
        "comments.html",
        commentaires=commentaires,
        post_id=post_id
    )


@app.route("/add_comment/<int:post_id>", methods=["POST"])
def add_comment(post_id):

    if "user_id" not in session:
        return redirect("/login")

    commentaire = request.form["commentaire"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO comments
    (
        user_id,
        post_id,
        commentaire,
        created_at
    )
    VALUES (?, ?, ?, ?)
    """, (
        session["user_id"],
        post_id,
        commentaire,
        datetime.now().isoformat()
    ))

    cursor.execute("SELECT user_id FROM posts WHERE id=?", (post_id,))
    owner_row = cursor.fetchone()

    conn.commit()
    conn.close()

    bump_quest_progress(session["user_id"], "comment")

    if owner_row:
        create_notification(owner_row[0], session["user_id"], "comment", post_id)

    return redirect("/comments/" + str(post_id))        
  
#-------------------------
#Profil Public
#-------------------------

@app.route("/user/<int:user_id>")
def user_profile(user_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    )

    user = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM posts WHERE user_id=? ORDER BY id DESC",
        (user_id,)
    )

    posts = cursor.fetchall()

    cursor.execute("""
    SELECT COUNT(*) FROM friends
    WHERE status='accepted'
    AND (sender_id=? OR receiver_id=?)
    """, (user_id, user_id))

    nb_amis = cursor.fetchone()[0]

    friend_status = None

    if "user_id" in session and session["user_id"] != user_id:

        cursor.execute("""
        SELECT status FROM friends
        WHERE (sender_id=? AND receiver_id=?)
        OR (sender_id=? AND receiver_id=?)
        """, (
            session["user_id"], user_id,
            user_id, session["user_id"]
        ))

        row = cursor.fetchone()
        friend_status = row[0] if row else "none"

    cursor.execute("SELECT COUNT(*) FROM follows WHERE following_id=?", (user_id,))
    nb_abonnes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM follows WHERE follower_id=?", (user_id,))
    nb_abonnements = cursor.fetchone()[0]

    is_following = False

    if "user_id" in session and session["user_id"] != user_id:

        cursor.execute("""
        SELECT id FROM follows
        WHERE follower_id=? AND following_id=?
        """, (session["user_id"], user_id))

        is_following = cursor.fetchone() is not None

    conn.close()

    return render_template(
        "user_profile.html",
        user=user,
        posts=posts,
        nb_amis=nb_amis,
        friend_status=friend_status,
        nb_abonnes=nb_abonnes,
        nb_abonnements=nb_abonnements,
        is_following=is_following
    )                                                                                                
  
#--------------------------
#Vues
#--------------------------                                              
@app.route("/post/<int:post_id>")
def post_detail(post_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE posts
    SET views = views + 1
    WHERE id=?
    """, (post_id,))

    conn.commit()

    cursor.execute("""
    SELECT posts.*, users.pseudo
    FROM posts
    JOIN users
    ON posts.user_id = users.id
    WHERE posts.id=?
    """, (post_id,))

    post = cursor.fetchone()

    conn.close()

    return render_template(
        "post_detail.html",
        post=post
    )                                                                                                                                                                                                                              #--------------------------
#Amis
#--------------------------

@app.route("/add_friend/<int:user_id>")
def add_friend(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["user_id"] == user_id:
        return redirect("/user/" + str(user_id))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM friends
    WHERE sender_id=?
    AND receiver_id=?
    """, (
        session["user_id"],
        user_id
    ))

    deja = cursor.fetchone()

    if not deja:

        cursor.execute("""
        INSERT INTO friends
        (
            sender_id,
            receiver_id
        )
        VALUES (?,?)
        """, (
            session["user_id"],
            user_id
        ))

        conn.commit()

    conn.close()

    if not deja:
        bump_quest_progress(session["user_id"], "friend")
        create_notification(user_id, session["user_id"], "friend_request")

    return redirect("/user/" + str(user_id))
    
@app.route("/accept_friend/<int:friend_id>")
def accept_friend(friend_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT sender_id FROM friends WHERE id=?", (friend_id,))
    sender_row = cursor.fetchone()

    cursor.execute("""
    UPDATE friends
    SET status='accepted'
    WHERE id=?
    """, (
        friend_id,
    ))

    conn.commit()
    conn.close()

    if sender_row:
        create_notification(sender_row[0], session["user_id"], "friend_accept")

    return redirect("/friends")      
                                                  
# -------------------------
# Notifications
# -------------------------

@app.route("/notifications")
def notifications():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        notifications.id,
        notifications.type,
        notifications.post_id,
        notifications.is_read,
        notifications.created_at,
        users.id,
        users.pseudo,
        users.photo
    FROM notifications
    JOIN users ON users.id = notifications.actor_id
    WHERE notifications.user_id=?
    ORDER BY notifications.id DESC
    LIMIT 50
    """, (session["user_id"],))

    notifs = cursor.fetchall()

    cursor.execute("""
    UPDATE notifications
    SET is_read=1
    WHERE user_id=? AND is_read=0
    """, (session["user_id"],))

    conn.commit()
    conn.close()

    return render_template(
        "notifications.html",
        notifs=notifs
    )

# -------------------------
# Messagerie
# -------------------------

@app.route("/messages")
def messages_list():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        c.id,
        u.id,
        u.pseudo,
        u.photo,
        (
            SELECT content FROM messages
            WHERE conversation_id=c.id
            ORDER BY id DESC LIMIT 1
        ),
        (
            SELECT created_at FROM messages
            WHERE conversation_id=c.id
            ORDER BY id DESC LIMIT 1
        ),
        (
            SELECT COUNT(*) FROM messages
            WHERE conversation_id=c.id
            AND sender_id != ?
            AND is_read = 0
        )
    FROM conversations c
    JOIN users u
        ON u.id = (CASE WHEN c.user1_id=? THEN c.user2_id ELSE c.user1_id END)
    WHERE c.user1_id=? OR c.user2_id=?
    ORDER BY (
        SELECT id FROM messages
        WHERE conversation_id=c.id
        ORDER BY id DESC LIMIT 1
    ) DESC
    """, (
        session["user_id"],
        session["user_id"],
        session["user_id"],
        session["user_id"]
    ))

    conversations = cursor.fetchall()

    conn.close()

    return render_template(
        "messages.html",
        conversations=conversations
    )

@app.route("/messages/<int:user_id>", methods=["GET", "POST"])
def conversation(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if user_id == session["user_id"]:
        return redirect("/messages")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    conv_id = get_or_create_conversation(cursor, conn, session["user_id"], user_id)

    if request.method == "POST":

        content = request.form.get("content", "").strip()

        if content:

            cursor.execute("""
            INSERT INTO messages
            (conversation_id, sender_id, content, created_at, is_read)
            VALUES (?, ?, ?, ?, 0)
            """, (
                conv_id,
                session["user_id"],
                content,
                datetime.now().isoformat()
            ))

            conn.commit()

        conn.close()

        return redirect("/messages/" + str(user_id))

    cursor.execute(
        "SELECT id, pseudo, photo FROM users WHERE id=?",
        (user_id,)
    )

    other_user = cursor.fetchone()

    cursor.execute("""
    UPDATE messages
    SET is_read=1
    WHERE conversation_id=? AND sender_id != ?
    """, (conv_id, session["user_id"]))

    conn.commit()

    cursor.execute("""
    SELECT id, sender_id, content, created_at
    FROM messages
    WHERE conversation_id=?
    ORDER BY id ASC
    """, (conv_id,))

    thread = cursor.fetchall()

    conn.close()

    return render_template(
        "conversation.html",
        other_user=other_user,
        messages=thread,
        conversation_id=conv_id
    )

@app.route("/api/messages/poll/<int:conversation_id>")
def poll_messages(conversation_id):

    if "user_id" not in session:
        return jsonify({"success": False}), 401

    since_id = request.args.get("since", 0, type=int)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE messages
    SET is_read=1
    WHERE conversation_id=? AND sender_id != ? AND id > ?
    """, (conversation_id, session["user_id"], since_id))

    conn.commit()

    cursor.execute("""
    SELECT id, sender_id, content, created_at
    FROM messages
    WHERE conversation_id=? AND id > ?
    ORDER BY id ASC
    """, (conversation_id, since_id))

    new_messages = cursor.fetchall()

    conn.close()

    return jsonify({
        "success": True,
        "messages": [
            {
                "id": m[0],
                "sender_id": m[1],
                "content": m[2],
                "created_at": m[3],
                "mine": m[1] == session["user_id"]
            }
            for m in new_messages
        ]
    })

# -------------------------
# Lancement
# -------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
   
from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from datetime import date, datetime
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
cloudinary.config(
    cloud_name="ychhniyu",
    api_key="312841415131582",                            api_secret="99lCY6a7zyj1jyEbAVew844Y3uk",
    secure=True
)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
        ("post_1", "Publie une quête", "Publie 1 photo ou vidéo aujourd'hui", "post", 1, 20, "📸"),
        ("like_3", "Soutiens la guilde", "Aime 3 publications aujourd'hui", "like", 3, 15, "❤️"),
        ("comment_1", "Prends la parole", "Laisse 1 commentaire aujourd'hui", "comment", 1, 10, "💬"),
        ("friend_1", "Étends ta guilde", "Envoie 1 demande d'ami aujourd'hui", "friend", 1, 15, "🤝"),
        ("view_5", "Explore le royaume", "Regarde 5 publications aujourd'hui", "view", 5, 10, "👀"),
    ]

    cursor.executemany("""
    INSERT OR IGNORE INTO quests
    (code, title, description, type, target, xp_reward, icon)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, default_quests)

    conn.commit()
    conn.close()

init_db()

# -------------------------
# Helpers - Quêtes
# -------------------------

def today_str():
    return date.today().isoformat()

def get_or_create_progress(cursor, user_id, quest_id):

    cursor.execute("""
    SELECT id, progress, completed, claimed
    FROM quest_progress
    WHERE user_id=? AND quest_id=? AND date=?
    """, (user_id, quest_id, today_str()))

    row = cursor.fetchone()

    if row:
        return row

    cursor.execute("""
    INSERT INTO quest_progress
    (user_id, quest_id, date, progress, completed, claimed)
    VALUES (?, ?, ?, 0, 0, 0)
    """, (user_id, quest_id, today_str()))

    return (cursor.lastrowid, 0, 0, 0)

def bump_quest_progress(user_id, quest_type, amount=1):

    if not user_id:
        return

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, target FROM quests WHERE type=?",
        (quest_type,)
    )

    quests_of_type = cursor.fetchall()

    for quest_id, target in quests_of_type:

        prog_id, progress, completed, claimed = get_or_create_progress(
            cursor, user_id, quest_id
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

    conn.close()

    return render_template(
        "profile.html",
        user=user,
        posts=posts,
        nb_amis=nb_amis
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
    SELECT id, title, description, target, xp_reward, icon
    FROM quests
    ORDER BY id
    """)

    all_quests = cursor.fetchall()

    quests_data = []

    for q in all_quests:

        quest_id, title, description, target, xp_reward, icon = q

        prog_id, progress, completed, claimed = get_or_create_progress(
            cursor, session["user_id"], quest_id
        )

        quests_data.append({
            "id": quest_id,
            "title": title,
            "description": description,
            "target": target,
            "xp_reward": xp_reward,
            "icon": icon,
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

    return render_template(
        "quest.html",
        quests=quests_data,
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

    cursor.execute("""
    SELECT id, completed, claimed
    FROM quest_progress
    WHERE user_id=? AND quest_id=? AND date=?
    """, (session["user_id"], quest_id, today_str()))

    row = cursor.fetchone()

    if not row or not row[1] or row[2]:
        conn.close()
        return jsonify({"success": False})

    cursor.execute(
        "SELECT xp_reward FROM quests WHERE id=?",
        (quest_id,)
    )

    xp_reward = cursor.fetchone()[0]

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

    cursor.execute("""
    SELECT
        posts.*,
        users.pseudo,
        users.photo,
        COUNT(DISTINCT likes.id),
        COUNT(DISTINCT comments.id)
    FROM posts

    JOIN users
        ON posts.user_id = users.id

    LEFT JOIN likes
        ON posts.id = likes.post_id

    LEFT JOIN comments
        ON posts.id = comments.post_id

    GROUP BY posts.id

    ORDER BY posts.id DESC
    """)

    posts = cursor.fetchall()

    conn.close()

    return render_template(
        "feed.html",
        posts=posts
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

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT pseudo, photo
    FROM users
    ORDER BY pseudo
    """)

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

    conn.close()
    
    nb_demandes = len(demandes)
    
    return render_template(
        "friends.html",
        demandes=demandes,
        nb_demandes=nb_demandes
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

    conn.close()

    if just_liked:
        bump_quest_progress(session["user_id"], "like")

    return jsonify({
        "success": True,
        "likes": total_likes
    })                                                                                                                                                   
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
        commentaire
    )
    VALUES (?, ?, ?)
    """, (
        session["user_id"],
        post_id,
        commentaire
    ))

    conn.commit()
    conn.close()

    bump_quest_progress(session["user_id"], "comment")

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

    conn.close()

    return render_template(
        "user_profile.html",
        user=user,
        posts=posts,
        nb_amis=nb_amis,
        friend_status=friend_status
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

    return redirect("/user/" + str(user_id))
    
@app.route("/accept_friend/<int:friend_id>")
def accept_friend(friend_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE friends
    SET status='accepted'
    WHERE id=?
    """, (
        friend_id,
    ))

    conn.commit()
    conn.close()

    return redirect("/friends")      
                                                  
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
   
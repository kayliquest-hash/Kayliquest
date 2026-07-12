import sqlite3
import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
    cloud_name="ychhniyu",
    api_key="312841415131582",
    api_secret="99lCY6a7zyj1jyEbAVew844Y3uk",
    secure=True
)

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("SELECT id, image FROM posts")
posts = cursor.fetchall()

for post in posts:

    post_id = post[0]
    image = post[1]

    chemin = os.path.join("static", "uploads", image)

    if os.path.exists(chemin):

        print("Upload :", image)

        upload = cloudinary.uploader.upload(
            chemin,
            resource_type="auto"
        )

        url = upload["secure_url"]

        cursor.execute(
            "UPDATE posts SET image=? WHERE id=?",
            (url, post_id)
        )

conn.commit()
conn.close()

print("Migration terminée !")
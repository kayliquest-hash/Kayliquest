# Déployer Kayli Quest gratuitement (Render + GitHub)

Ce guide t'accompagne pas à pas pour mettre Kayli Quest en ligne gratuitement.

## Ce qui a changé dans le code

- **Photos de profil, posts et vidéos Kayli** → stockés sur **Cloudinary** (plus aucun fichier utilisateur n'est enregistré sur le serveur, ce qui est obligatoire pour Render : le disque n'est pas persistant).
- **Base de données** → **PostgreSQL** au lieu de SQLite (SQLite est un fichier local, qui serait effacé à chaque redéploiement).
- Toutes les clés secrètes (Cloudinary, base de données, clé de session) sont maintenant lues depuis des **variables d'environnement**, plus jamais écrites en clair dans le code — important puisque ton code va être public sur GitHub.

⚠️ **Important** : tes données actuelles (utilisateurs, posts) sont dans `database.db` (SQLite) et **ne seront pas transférées automatiquement** vers PostgreSQL — ce sont deux systèmes différents. Si tu veux repartir avec tes données existantes, dis-le-moi et je peux écrire un script de migration. Sinon, le site démarrera avec une base neuve et vide, ce qui est le cas normal pour un vrai lancement.

---

## Étape 1 — Cloudinary (stockage des images/vidéos)

1. Crée un compte gratuit sur [cloudinary.com](https://cloudinary.com) (le plan gratuit suffit largement pour démarrer).
2. Sur ton tableau de bord, note ces 3 informations : **Cloud name**, **API Key**, **API Secret**.

## Étape 2 — Mettre le code sur GitHub

1. Crée un nouveau dépôt sur [github.com](https://github.com) (peut être privé ou public).
2. Depuis le dossier du projet :

```bash
git init
git add .
git commit -m "Première version de Kayli Quest"
git branch -M main
git remote add origin https://github.com/TON-PSEUDO/kayliquest.git
git push -u origin main
```

Le fichier `.gitignore` fourni empêche déjà d'envoyer tes anciennes photos locales et ton ancienne base SQLite sur GitHub.

## Étape 3 — La base de données PostgreSQL

Deux options :

**Option A — Neon (recommandée)**
Le plan gratuit de Neon reste actif indéfiniment (contrairement à celui de Render, voir ci-dessous).
1. Crée un compte sur [neon.tech](https://neon.tech), crée un projet.
2. Copie la "Connection string" (elle ressemble à `postgresql://user:password@host/dbname?sslmode=require`).

**Option B — PostgreSQL directement chez Render**
Plus simple (tout au même endroit) mais la base gratuite de Render **expire automatiquement 30 jours après sa création**, avec 14 jours de grâce avant suppression définitive. Pratique pour tester, risqué pour un vrai lancement à long terme sauf si tu passes en payant avant l'expiration (~7$/mois).

## Étape 4 — Déployer sur Render

1. Crée un compte sur [render.com](https://render.com) (aucune carte bancaire requise pour le plan gratuit).
2. "New +" → "Web Service" → connecte ton dépôt GitHub.
3. Render détecte Python automatiquement. Renseigne :
   - **Build command** : `pip install -r requirements.txt`
   - **Start command** : `gunicorn app:app`
   - **Instance type** : Free
4. Dans l'onglet **Environment**, ajoute ces variables :

| Variable | Valeur |
|---|---|
| `DATABASE_URL` | ta connection string Neon (ou celle fournie par Render Postgres) |
| `CLOUDINARY_CLOUD_NAME` | ton cloud name Cloudinary |
| `CLOUDINARY_API_KEY` | ta clé API Cloudinary |
| `CLOUDINARY_API_SECRET` | ton secret API Cloudinary |
| `SECRET_KEY` | une longue chaîne aléatoire (sers-toi d'un générateur de mot de passe) |

5. Clique sur "Create Web Service". Render installe les dépendances et démarre l'app — les tables PostgreSQL sont créées automatiquement au premier lancement (`init_db()` s'exécute tout seul).
6. Ton site est en ligne à une adresse du type `https://kayliquest.onrender.com`.

## Limites du plan gratuit Render à connaître

- Le service **s'endort après 15 minutes d'inactivité** : la première visite après une pause prend 30 à 60 secondes le temps qu'il se réveille.
- **750 heures gratuites par mois** par compte (largement suffisant pour un seul service qui tourne en continu, un mois fait ~730h).
- Si tu choisis la base Postgres de Render plutôt que Neon : **expire après 30 jours**, pense à migrer ou passer en payant avant l'échéance.

## Après le déploiement

- Crée ton premier compte directement sur le site en ligne (le formulaire d'inscription).
- Si tu veux un nom de domaine personnalisé, Render permet d'en connecter un gratuitement dans les paramètres du service (juste le domaine à acheter séparément si tu n'en as pas déjà un).

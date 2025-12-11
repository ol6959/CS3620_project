import csv
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_PASSWORD",
    "database": "tunetracker",
}

CSV_PATH = "data/train.csv"      # Kaggle Spotify Genre dataset
COMMIT_EVERY = 1000


def get_conn():
    return mysql.connector.connect(**DB_CONFIG)


def parse_primary_artist(artists_str: str) -> str:
    """
    Extract first artist name from strings like:
    "['Taylor Swift']"  or "['Drake','21 Savage']"
    """
    if not artists_str:
        return "Unknown Artist"

    s = artists_str.strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]

    first = s.split(",")[0].strip()
    first = first.strip("'").strip('"')
    return first or "Unknown Artist"


def import_spotify():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    conn.start_transaction()

    print("🎵 Importing Spotify dataset from train.csv...\n")

    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        total_rows = 0
        new_artists = 0
        new_albums = 0
        new_tracks = 0
        new_genres = 0
        tg_links = 0

        for row in reader:
            total_rows += 1

            # ----- Extract raw fields -----
            track_title = row.get("track_name")
            album_name  = row.get("album_name")
            artists_raw = row.get("artists")
            genre_name  = row.get("track_genre")
            popularity  = row.get("popularity")
            duration_ms = row.get("duration_ms")
            explicit    = row.get("explicit")

            if not track_title:
                continue

            # ====== CLEAN & TRUNCATE TEXT FIELDS ======
            track_title = (track_title or "").strip()
            if len(track_title) > 255:
                track_title = track_title[:255]

            album_title = (album_name or "Unknown Album").strip()
            if len(album_title) > 255:
                album_title = album_title[:255]

            artists_raw = (artists_raw or "").strip()

            # ====== NUMERIC CLEANUP ======
            try:
                popularity = int(popularity) if popularity not in ("", None, "NaN") else None
            except:
                popularity = None

            try:
                duration_ms = int(float(duration_ms)) if duration_ms not in ("", None, "NaN") else None
            except:
                duration_ms = None

            explicit = 1 if str(explicit).strip() in ("1", "True", "true") else 0

            # ====== Extract artist name ======
            artist_name = parse_primary_artist(artists_raw)

            # =====================================
            # 1️⃣ INSERT ARTIST
            # =====================================
            cursor.execute("""
                INSERT IGNORE INTO music_artist (name)
                VALUES (%s)
            """, (artist_name,))
            if cursor.rowcount > 0:
                new_artists += 1

            cursor.execute("SELECT artist_id FROM music_artist WHERE name=%s", (artist_name,))
            arow = cursor.fetchone()
            if not arow:
                continue
            artist_id = arow["artist_id"]

            # =====================================
            # 2️⃣ INSERT ALBUM (spotify_album_id=NULL)
            # =====================================
            cursor.execute("""
                INSERT IGNORE INTO music_album (spotify_album_id, name, release_date)
                VALUES (NULL, %s, NULL)
            """, (album_title,))
            if cursor.rowcount > 0:
                new_albums += 1

            cursor.execute("SELECT album_id FROM music_album WHERE name=%s LIMIT 1", (album_title,))
            alb = cursor.fetchone()
            if not alb:
                continue
            album_id = alb["album_id"]

            # =====================================
            # 3️⃣ INSERT TRACK
            # =====================================
            cursor.execute("""
                INSERT INTO music_track (
                    title,
                    album_name,
                    duration_ms,
                    popularity,
                    is_explicit,
                    release_year,
                    release_date,
                    spotify_id
                )
                VALUES (%s,%s,%s,%s,%s,NULL,NULL,NULL)
            """, (
                track_title,
                album_title,
                duration_ms,
                popularity,
                explicit
            ))

            track_id = cursor.lastrowid
            new_tracks += 1

            # =====================================
            # 4️⃣ LINK TRACK ↔ ARTIST
            # =====================================
            cursor.execute("""
                INSERT IGNORE INTO music_track_artist (track_id, artist_id)
                VALUES (%s, %s)
            """, (track_id, artist_id))

            # =====================================
            # 5️⃣ GENRE HANDLING
            # =====================================
            if genre_name:
                cursor.execute("""
                    INSERT IGNORE INTO ref_genre (name)
                    VALUES (%s)
                """, (genre_name,))
                if cursor.rowcount > 0:
                    new_genres += 1

                cursor.execute("SELECT genre_id FROM ref_genre WHERE name=%s", (genre_name,))
                grow = cursor.fetchone()
                if grow:
                    genre_id = grow["genre_id"]

                    cursor.execute("""
                        INSERT IGNORE INTO music_track_genre (track_id, genre_id)
                        VALUES (%s, %s)
                    """, (track_id, genre_id))
                    tg_links += cursor.rowcount

            # =====================================
            # 🔄 PERIODIC COMMIT
            # =====================================
            if total_rows % COMMIT_EVERY == 0:
                #conn.commit()
                print(f"Processed {total_rows:,} rows...")

        conn.commit()

    cursor.close()
    conn.close()

    print("\n🎉 Spotify Import Complete!")
    print(f"Rows read:         {total_rows:,}")
    print(f"New artists:       {new_artists:,}")
    print(f"New albums:        {new_albums:,}")
    print(f"New tracks:        {new_tracks:,}")
    print(f"New genres:        {new_genres:,}")
    print(f"Track-Genre links: {tg_links:,}")


if __name__ == "__main__":
    import_spotify()


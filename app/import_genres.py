import csv
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Lyo265155!",
    "database": "tunetracker"
}

CSV_PATH = "data/train.csv"

def get_conn():
    return mysql.connector.connect(**DB_CONFIG)

def import_genres():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)

    print("🎵 Importing genres...")

    rows_scanned = 0
    genres_added = 0
    links_added = 0

    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            rows_scanned += 1

            spotify_track_id = row["track_id"]
            genre_name = row["track_genre"]

            if not spotify_track_id or not genre_name:
                continue

            # Insert genre if new
            cursor.execute("""
                INSERT IGNORE INTO ref_genre (name)
                VALUES (%s)
            """, (genre_name,))
            if cursor.rowcount > 0:
                genres_added += 1

            # Fetch genre_id
            cursor.execute("SELECT genre_id FROM ref_genre WHERE name = %s", (genre_name,))
            genre = cursor.fetchone()
            if not genre:
                continue
            genre_id = genre["genre_id"]

            # Match Spotify track
            cursor.execute("""
                SELECT track_id FROM music_track
                WHERE spotify_track_id = %s
                LIMIT 1
            """, (spotify_track_id,))
            track = cursor.fetchone()
            if not track:
                continue
            track_id = track["track_id"]

            # Insert mapping
            cursor.execute("""
                INSERT IGNORE INTO music_track_genre (track_id, genre_id)
                VALUES (%s, %s)
            """, (track_id, genre_id,))
            links_added += cursor.rowcount

            if rows_scanned % 5000 == 0:
                conn.commit()
                print(f"Processed {rows_scanned:,} rows...")

    conn.commit()
    cursor.close()
    conn.close()

    print("\n🎉 DONE importing!")
    print(f" Rows scanned: {rows_scanned:,}")
    print(f" Genres inserted: {genres_added:,}")
    print(f" Track-Genre links added: {links_added:,}")

if __name__ == "__main__":
    import_genres()


import csv
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_PASSWORD",  # <- keep or change as needed
    "database": "tunetracker",
}

CSV_PATH = "data/train.csv"      # Kaggle Spotify Genre dataset

COMMIT_EVERY = 5000              # commit after this many CSV rows
LINK_BATCH_SIZE = 2000           # batch size for track-artist / track-genre inserts


def get_conn():
    # You can add pool_name / pool_size here if you want pooling later
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
    conn.autocommit = False      # ensure controlled transactions
    cursor = conn.cursor()       # tuples are faster than dict rows

    print("🎵 Importing Spotify dataset from train.csv...\n")

    # ------------------------------------------------------------------
    # 0️⃣ In-memory caches for artists, albums, genres
    #    This prevents repeated SELECTs for the same names.
    # ------------------------------------------------------------------
    artist_cache = {}
    album_cache = {}
    genre_cache = {}

    # Pre-warm caches with existing rows (optional but very helpful)
    print("🔍 Preloading existing artists/albums/genres into cache...")

    cursor.execute("SELECT artist_id, name FROM music_artist")
    for artist_id, name in cursor:
        artist_cache[name] = artist_id

    cursor.execute("SELECT album_id, name FROM music_album")
    for album_id, name in cursor:
        album_cache[name] = album_id

    cursor.execute("SELECT genre_id, name FROM ref_genre")
    for genre_id, name in cursor:
        genre_cache[name] = genre_id

    print(f"✅ Cached {len(artist_cache)} artists, "
          f"{len(album_cache)} albums, {len(genre_cache)} genres.\n")

    # ------------------------------------------------------------------
    # Helper functions: get_or_create for dim tables using cache
    # ------------------------------------------------------------------
    def get_or_create_artist(name: str) -> int:
        name = name[:255]
        if name in artist_cache:
            return artist_cache[name]

        # Try DB
        cursor.execute("SELECT artist_id FROM music_artist WHERE name=%s", (name,))
        row = cursor.fetchone()
        if row:
            artist_id = row[0]
            artist_cache[name] = artist_id
            return artist_id

        # Not found -> insert
        cursor.execute(
            "INSERT INTO music_artist (name) VALUES (%s)",
            (name,),
        )
        artist_id = cursor.lastrowid
        artist_cache[name] = artist_id
        stats["new_artists"] += 1
        return artist_id

    def get_or_create_album(name: str) -> int:
        name = name[:255]
        if name in album_cache:
            return album_cache[name]

        # Try DB
        cursor.execute("SELECT album_id FROM music_album WHERE name=%s LIMIT 1", (name,))
        row = cursor.fetchone()
        if row:
            album_id = row[0]
            album_cache[name] = album_id
            return album_id

        # Not found -> insert
        cursor.execute(
            """
            INSERT INTO music_album (spotify_album_id, name, release_date)
            VALUES (NULL, %s, NULL)
            """,
            (name,),
        )
        album_id = cursor.lastrowid
        album_cache[name] = album_id
        stats["new_albums"] += 1
        return album_id

    def get_or_create_genre(name: str) -> int:
        name = name[:255]
        if name in genre_cache:
            return genre_cache[name]

        cursor.execute("SELECT genre_id FROM ref_genre WHERE name=%s", (name,))
        row = cursor.fetchone()
        if row:
            genre_id = row[0]
            genre_cache[name] = genre_id
            return genre_id

        cursor.execute(
            "INSERT INTO ref_genre (name) VALUES (%s)",
            (name,),
        )
        genre_id = cursor.lastrowid
        genre_cache[name] = genre_id
        stats["new_genres"] += 1
        return genre_id

    # ------------------------------------------------------------------
    # Stats + batched link buffers
    # ------------------------------------------------------------------
    stats = {
        "total_rows": 0,
        "new_artists": 0,
        "new_albums": 0,
        "new_tracks": 0,
        "new_genres": 0,
        "tg_links": 0,
    }

    track_artist_links = []   # (track_id, artist_id)
    track_genre_links = []    # (track_id, genre_id)

    def flush_link_batches():
        """Flush batched many-to-many link inserts with executemany."""
        if track_artist_links:
            cursor.executemany(
                """
                INSERT IGNORE INTO music_track_artist (track_id, artist_id)
                VALUES (%s, %s)
                """,
                track_artist_links,
            )
            track_artist_links.clear()

        if track_genre_links:
            cursor.executemany(
                """
                INSERT IGNORE INTO music_track_genre (track_id, genre_id)
                VALUES (%s, %s)
                """,
                track_genre_links,
            )
            stats["tg_links"] += cursor.rowcount
            track_genre_links.clear()

    # ------------------------------------------------------------------
    # 1️⃣ Main CSV loop
    # ------------------------------------------------------------------
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            stats["total_rows"] += 1

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
            except Exception:
                popularity = None

            try:
                duration_ms = int(float(duration_ms)) if duration_ms not in ("", None, "NaN") else None
            except Exception:
                duration_ms = None

            explicit_flag = 1 if str(explicit).strip() in ("1", "True", "true") else 0

            # ====== Extract artist name ======
            artist_name = parse_primary_artist(artists_raw)

            # =====================================
            # 1️⃣ ARTIST (cached get-or-create)
            # =====================================
            artist_id = get_or_create_artist(artist_name)

            # =====================================
            # 2️⃣ ALBUM (cached get-or-create)
            # =====================================
            album_id = get_or_create_album(album_title)

            # =====================================
            # 3️⃣ TRACK (insert per-row)
            # =====================================
            cursor.execute(
                """
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
                """,
                (
                    track_title,
                    album_title,
                    duration_ms,
                    popularity,
                    explicit_flag,
                ),
            )

            track_id = cursor.lastrowid
            stats["new_tracks"] += 1

            # =====================================
            # 4️⃣ BATCHED TRACK ↔ ARTIST LINK
            # =====================================
            track_artist_links.append((track_id, artist_id))

            # =====================================
            # 5️⃣ GENRE HANDLING (cached get-or-create)
            # =====================================
            if genre_name:
                genre_name_clean = genre_name.strip()
                if genre_name_clean:
                    genre_id = get_or_create_genre(genre_name_clean)
                    track_genre_links.append((track_id, genre_id))

            # =====================================
            # 🔄 PERIODIC FLUSH + COMMIT
            # =====================================
            if len(track_artist_links) >= LINK_BATCH_SIZE or len(track_genre_links) >= LINK_BATCH_SIZE:
                flush_link_batches()

            if stats["total_rows"] % COMMIT_EVERY == 0:
                flush_link_batches()
                conn.commit()
                print(f"Processed {stats['total_rows']:,} rows..."
                      f" tracks: {stats['new_tracks']:,}, "
                      f"artists: {stats['new_artists']:,}, "
                      f"albums: {stats['new_albums']:,}, "
                      f"genres: {stats['new_genres']:,}")

    # Final flush + commit
    flush_link_batches()
    conn.commit()

    cursor.close()
    conn.close()

    print("\n🎉 Spotify Import Complete!")
    print(f"Rows read:         {stats['total_rows']:,}")
    print(f"New artists:       {stats['new_artists']:,}")
    print(f"New albums:        {stats['new_albums']:,}")
    print(f"New tracks:        {stats['new_tracks']:,}")
    print(f"New genres:        {stats['new_genres']:,}")
    print(f"Track-Genre links: {stats['tg_links']:,}")


if __name__ == "__main__":
    import_spotify()


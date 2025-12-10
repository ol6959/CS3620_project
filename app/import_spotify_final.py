import csv
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Lyo265155!",
    "database": "tunetracker",
}

CSV_PATH = "data/train.csv"    # Kaggle genre dataset
COMMIT_EVERY = 1000


def get_conn():
    return mysql.connector.connect(**DB_CONFIG)


def parse_primary_artist(artists_str: str) -> str:
    """
    'artists' in train.csv is typically something like:
    "['Taylor Swift']" or "['Artist1', 'Artist2']"
    We'll just grab the first name as a string.
    """
    if not artists_str:
        return "Unknown Artist"

    s = artists_str.strip()
    # Drop leading/trailing brackets if present
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]

    # Split by comma, take first
    first = s.split(",")[0].strip()

    # Strip quotes
    first = first.strip().strip("'").strip('"')
    return first or "Unknown Artist"


def import_spotify_option():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)

    print("🎵 Rebuilding music library from data/train.csv ...\n")

    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        total_rows = 0
        inserted_tracks = 0
        inserted_artists = 0
        inserted_albums = 0
        inserted_genres = 0
        track_genre_links = 0

        for row in reader:
            total_rows += 1

            spotify_track_id = row.get("track_id")
            track_name       = row.get("track_name")
            album_name       = row.get("album_name")
            artists_raw      = row.get("artists")
            popularity_raw   = row.get("popularity")
            duration_ms_raw  = row.get("duration_ms")
            explicit_raw     = row.get("explicit")
            danceability     = row.get("danceability")
            energy           = row.get("energy")
            valence          = row.get("valence")
            tempo            = row.get("tempo")
            acousticness     = row.get("acousticness")
            instrumentalness = row.get("instrumentalness")
            liveness         = row.get("liveness")
            genre_name       = row.get("track_genre")

            # Basic validation
            if not spotify_track_id or not track_name:
                continue

            # ---------- Clean scalars ----------
            try:
                popularity = int(popularity_raw) if popularity_raw not in (None, "", "NaN") else None
            except ValueError:
                popularity = None

            try:
                duration_ms = int(float(duration_ms_raw)) if duration_ms_raw not in (None, "", "NaN") else None
            except ValueError:
                duration_ms = None

            # explicit is usually 0/1
            try:
                explicit = 1 if str(explicit_raw).strip() in ("1", "True", "true") else 0
            except Exception:
                explicit = 0

            # release_year – we don’t have it in this dataset, so use None
            release_year = None

            # Primary artist (string)
            artist_name = parse_primary_artist(artists_raw)

            # ---------- Upsert artist ----------
            cursor.execute("""
                INSERT IGNORE INTO music_artist (name)
                VALUES (%s)
            """, (artist_name,))
            if cursor.rowcount > 0:
                inserted_artists += 1

            cursor.execute("""
                SELECT artist_id FROM music_artist
                WHERE name = %s
                LIMIT 1
            """, (artist_name,))
            arow = cursor.fetchone()
            if not arow:
                # Shouldn't happen, but skip if no artist_id
                continue
            artist_id = arow["artist_id"]

            # ---------- Upsert album ----------
            # We don't have a Spotify album ID or release date,
            # so we group albums by (album_name, artist_id).
            album_title = album_name or "Unknown Album"

            # Use a synthetic uniqueness: same title + same artist
            cursor.execute("""
                INSERT IGNORE INTO music_album (spotify_album_id, title, release_date, album_type)
                VALUES (NULL, %s, NULL, 'album')
            """, (album_title,))
            if cursor.rowcount > 0:
                inserted_albums += 1

            cursor.execute("""
                SELECT album_id FROM music_album
                WHERE title = %s
                LIMIT 1
            """, (album_title,))
            alb = cursor.fetchone()
            if not alb:
                continue
            album_id = alb["album_id"]

            # ---------- Upsert track with audio features ----------
            cursor.execute("""
                INSERT INTO music_track (
                    spotify_track_id,
                    album_id,
                    title,
                    duration_ms,
                    explicit,
                    release_year,
                    popularity,
                    danceability,
                    energy,
                    valence,
                    tempo,
                    acousticness,
                    instrumentalness,
                    liveness
                )
                VALUES (%s, %s, %s, %s, %s,
                        %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    album_id        = VALUES(album_id),
                    title           = VALUES(title),
                    duration_ms     = VALUES(duration_ms),
                    explicit        = VALUES(explicit),
                    release_year    = VALUES(release_year),
                    popularity      = VALUES(popularity),
                    danceability    = VALUES(danceability),
                    energy          = VALUES(energy),
                    valence         = VALUES(valence),
                    tempo           = VALUES(tempo),
                    acousticness    = VALUES(acousticness),
                    instrumentalness= VALUES(instrumentalness),
                    liveness        = VALUES(liveness)
            """, (
                spotify_track_id,
                album_id,
                track_name,
                duration_ms,
                explicit,
                release_year,
                popularity,
                danceability,
                energy,
                valence,
                tempo,
                acousticness,
                instrumentalness,
                liveness
            ))

            if cursor.rowcount > 0:
                inserted_tracks += 1

            # Get internal track_id
            cursor.execute("""
                SELECT track_id FROM music_track
                WHERE spotify_track_id = %s
                LIMIT 1
            """, (spotify_track_id,))
            trow = cursor.fetchone()
            if not trow:
                continue
            track_id = trow["track_id"]

            # ---------- Track ↔ Artist link ----------
            cursor.execute("""
                INSERT IGNORE INTO music_track_artist (track_id, artist_id)
                VALUES (%s, %s)
            """, (track_id, artist_id))

            # ---------- Genre reference + link ----------
            if genre_name:
                cursor.execute("""
                    INSERT IGNORE INTO ref_genre (name)
                    VALUES (%s)
                """, (genre_name,))
                if cursor.rowcount > 0:
                    inserted_genres += 1

                cursor.execute("""
                    SELECT genre_id FROM ref_genre
                    WHERE name = %s
                    LIMIT 1
                """, (genre_name,))
                grow = cursor.fetchone()
                if grow:
                    genre_id = grow["genre_id"]
                    cursor.execute("""
                        INSERT IGNORE INTO music_track_genre (track_id, genre_id)
                        VALUES (%s, %s)
                    """, (track_id, genre_id))
                    track_genre_links += cursor.rowcount

            # ---------- Commit occasionally ----------
            if total_rows % COMMIT_EVERY == 0:
                conn.commit()
                print(f"  Processed {total_rows:,} rows...")

        # final commit
        conn.commit()

    cursor.close()
    conn.close()

    print("\n🎉 DONE importing!")
    print(f" Rows scanned: {total_rows:,}")
    print(f" Tracks inserted/updated: {inserted_tracks:,}")
    print(f" Artists inserted: {inserted_artists:,}")
    print(f" Albums inserted: {inserted_albums:,}")
    print(f" Genres inserted: {inserted_genres:,}")
    print(f" Track-Genre links added: {track_genre_links:,}")


if __name__ == "__main__":
    import_spotify_option()


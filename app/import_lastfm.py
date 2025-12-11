import csv
import mysql.connector
import datetime

CSV_FILE = "data/Last.fm_data.csv"  # relative to app folder

def parse_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, "%d %b %Y").date()
    except:
        return None

def parse_time(time_str):
    try:
        return datetime.datetime.strptime(time_str, "%H:%M").time()
    except:
        return None


print("📥 Importing Last.fm data...")

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUR_PASSWORD",
    database="tunetracker"
)
cursor = db.cursor()

with open(CSV_FILE, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    
    header = next(reader)
    print("Header columns:", header)

    header = [h.replace("\ufeff", "").strip() for h in header]

    idx = {
        "Username": header.index("Username"),
        "Artist": header.index("Artist"),
        "Track": header.index("Track"),
        "Album": header.index("Album"),
        "Date": header.index("Date"),
        "Time": header.index("Time")
    }

    batch = []
    count = 0

    for row in reader:
        if len(row) < len(header):
            continue

        count += 1
        batch.append((
            row[idx["Username"]].strip()[:255],
            row[idx["Artist"]].strip()[:255],
            row[idx["Track"]].strip()[:255],
            row[idx["Album"]].strip()[:255],
            parse_date(row[idx["Date"]].strip()),
            parse_time(row[idx["Time"]].strip())
        ))

        # Batch insert every 5,000 rows
        if len(batch) >= 5000:
            cursor.executemany("""
                INSERT INTO ext_lastfm_listens
                (username, artist_name, track_name, album_name, listen_date, listen_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, batch)
            db.commit()
            print(f"Inserted {count:,} rows...")
            batch = []

            # -------------------------------
            # MAP after batch insert
            # -------------------------------
            cursor.execute("""
                INSERT IGNORE INTO map_lastfm_track (lastfm_id, track_id)
                SELECT 
                    l.id,
                    t.track_id
                FROM ext_lastfm_listens l
                JOIN music_track t 
                    ON LOWER(l.track_name) = LOWER(t.title)
                JOIN music_track_artist mta 
                    ON t.track_id = mta.track_id
                JOIN music_artist a 
                    ON mta.artist_id = a.artist_id
                WHERE LOWER(l.artist_name) = LOWER(a.name)
                  AND NOT EXISTS (
                        SELECT 1 
                        FROM map_lastfm_track m 
                        WHERE m.lastfm_id = l.id
                  );
            """)
            db.commit()

    # Insert remaining rows
    if batch:
        cursor.executemany("""
            INSERT INTO ext_lastfm_listens
            (username, artist_name, track_name, album_name, listen_date, listen_time)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, batch)
        db.commit()

        # ---------------------------
        # FINAL mapping pass
        # ---------------------------
        cursor.execute("""
            INSERT IGNORE INTO map_lastfm_track (lastfm_id, track_id)
            SELECT 
                l.id,
                t.track_id
            FROM ext_lastfm_listens l
            JOIN music_track t 
                ON LOWER(l.track_name) = LOWER(t.title)
            JOIN music_track_artist mta 
                ON t.track_id = mta.track_id
            JOIN music_artist a 
                ON mta.artist_id = a.artist_id
            WHERE LOWER(l.artist_name) = LOWER(a.name)
              AND NOT EXISTS (
                    SELECT 1 
                    FROM map_lastfm_track m 
                    WHERE m.lastfm_id = l.id
              );
        """)
        db.commit()

cursor.close()
db.close()

print(f"🎉 Done! Imported {count:,} Last.fm listens into database.")
print("🎧 Mapping complete — Last.fm tracks linked to Spotify!")


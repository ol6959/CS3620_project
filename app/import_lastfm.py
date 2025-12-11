import csv
import mysql.connector
import datetime

CSV_FILE = "data/Last.fm_data.csv"

BATCH_SIZE = 25000   # bigger batches = faster
TRUNC = 255          # max length enforcement


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


print("📥 Importing Last.fm data (optimized)...")

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUR_PASSWORD",
    database="tunetracker"
)
cursor = db.cursor()

# ---------------------------------------------------------
# 0️⃣ Disable keys for faster bulk loading
# ---------------------------------------------------------
print("⏳ Disabling keys for fast insert...")
cursor.execute("ALTER TABLE ext_lastfm_listens DISABLE KEYS;")
db.commit()

# ---------------------------------------------------------
# 1️⃣ Read CSV & insert listens in large batches
# ---------------------------------------------------------
with open(CSV_FILE, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = [h.replace("\ufeff", "").strip() for h in next(reader)]

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

    print("⏳ Importing listens...")

    for row in reader:
        if len(row) < len(header):
            continue

        count += 1

        batch.append((
            row[idx["Username"]].strip()[:TRUNC],
            row[idx["Artist"]].strip()[:TRUNC],
            row[idx["Track"]].strip()[:TRUNC],
            row[idx["Album"]].strip()[:TRUNC],
            parse_date(row[idx["Date"]]),
            parse_time(row[idx["Time"]])
        ))

        # Insert batch
        if len(batch) >= BATCH_SIZE:
            cursor.executemany("""
                INSERT INTO ext_lastfm_listens
                (username, artist_name, track_name, album_name, listen_date, listen_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, batch)
            db.commit()
            print(f"Inserted {count:,} rows...")
            batch = []

    # Insert remaining rows
    if batch:
        cursor.executemany("""
            INSERT INTO ext_lastfm_listens
            (username, artist_name, track_name, album_name, listen_date, listen_time)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, batch)
        db.commit()
        print(f"Inserted {count:,} rows (final batch).")


# ---------------------------------------------------------
# 2️⃣ Re-enable keys (MySQL builds indexes in one pass)
# ---------------------------------------------------------
print("🔧 Rebuilding indexes...")
cursor.execute("ALTER TABLE ext_lastfm_listens ENABLE KEYS;")
db.commit()

# ---------------------------------------------------------
# 3️⃣ Load Spotify track ↔ artist mapping into memory
# ---------------------------------------------------------
print("📚 Loading Spotify track/artist map into memory...")

cursor.execute("""
    SELECT t.track_id, LOWER(t.title), LOWER(a.name)
    FROM music_track t
    JOIN music_track_artist mta ON t.track_id = mta.track_id
    JOIN music_artist a ON mta.artist_id = a.artist_id
""")

track_map = {}
for track_id, title, artist in cursor.fetchall():
    track_map[(title, artist)] = track_id

print(f"Loaded {len(track_map):,} track mappings.")


# ---------------------------------------------------------
# 4️⃣ Match Last.fm listens using in-memory dict (FAST)
# ---------------------------------------------------------
print("🔗 Mapping Last.fm listens → Spotify tracks...")

cursor.execute("SELECT id, LOWER(track_name), LOWER(artist_name) FROM ext_lastfm_listens")
rows = cursor.fetchall()

link_batch = []
link_count = 0

for lastfm_id, track_name, artist_name in rows:
    key = (track_name, artist_name)
    if key in track_map:
        link_batch.append((lastfm_id, track_map[key]))

    if len(link_batch) >= BATCH_SIZE:
        cursor.executemany("""
            INSERT IGNORE INTO map_lastfm_track (lastfm_id, track_id)
            VALUES (%s, %s)
        """, link_batch)
        link_count += cursor.rowcount
        link_batch = []

# Final link batch
if link_batch:
    cursor.executemany("""
        INSERT IGNORE INTO map_lastfm_track (lastfm_id, track_id)
        VALUES (%s, %s)
    """, link_batch)
    link_count += cursor.rowcount

db.commit()


cursor.close()
db.close()

print("🎉 Done!")
print(f"📊 Imported {count:,} listens.")
print(f"🔗 Created {link_count:,} Last.fm → Spotify mappings.")


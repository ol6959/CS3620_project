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
    password="Lyo265155!",
    database="tunetracker"
)
cursor = db.cursor()

with open(CSV_FILE, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    
    header = next(reader)  # read the header row
    print("Header columns:", header)

    # Trim BOM and strip whitespace
    header = [h.replace("\ufeff", "").strip() for h in header]

    # Expected column positions:
    # ['', 'Username', 'Artist', 'Track', 'Album', 'Date', 'Time']
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
            continue  # skip bad lines

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

    # Insert remaining rows
    if batch:
        cursor.executemany("""
            INSERT INTO ext_lastfm_listens
            (username, artist_name, track_name, album_name, listen_date, listen_time)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, batch)
        db.commit()

cursor.close()
db.close()

print(f"🎉 Done! Imported {count:,} Last.fm listens into database.")


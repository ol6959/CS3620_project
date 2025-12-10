
Databases Used:

    Spotify Tracks Genres:
        https://www.kaggle.com/datasets/thedevastator/spotify-tracks-genre-dataset?utm_source=chatgpt.com

    LastFM:
        https://www.kaggle.com/datasets/harshal19t/lastfm-dataset?utm_source=chatgpt.com&select=Last.fm_data.csv

    World Development Indicators:
        https://www.kaggle.com/datasets/theworldbank/world-development-indicators/data
        
    

Build Instructions:
    1. create the schema: mysql -u root -p < db/schema.sql
    2. Download all the databases we used
    3. Put all the .csv files into the TuneTracker/app/data directory
    4. Update all the import python scripts under TuneTracker/app to match your SQL user login. It should look something like this before:
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="YOUR_PASSWORD",
                database="tunetracker"
            )
    5. Run import scripts (I used a venv):
        python import_spotify_final.py  - inserts artist into music_artist and tracks into music_track and connects them
        
        python import_lastfm.py  - loads listens to show popular songs
        
        python import_world_bank_ref.py
        &                                   - populates world_bank_country, indicator, and data
        python import_world_bank_data.py
    6. Confirm everything imported correctly by using the analytic view




To see analytic view (from demo video):
    SELECT COUNT(*) FROM music_track;
    SELECT COUNT(*) FROM ext_lastfm_listens;
    SELECT COUNT(*) FROM world_bank_data;


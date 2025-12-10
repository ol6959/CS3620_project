App : TuneTrack
By: Owen Lyons

Description:
    This is an app that lets user log their music listening habits and see recomendations on what to listen to based on other peoples' and their own listening habits.



Databases Used:

    Spotify Tracks Genres:
        https://www.kaggle.com/datasets/thedevastator/spotify-tracks-genre-dataset?utm_source=chatgpt.com

    LastFM:
        https://www.kaggle.com/datasets/harshal19t/lastfm-dataset?utm_source=chatgpt.com&select=Last.fm_data.csv

    World Development Indicators:
        https://www.kaggle.com/datasets/theworldbank/world-development-indicators/data
        
    

Build Instructions:
    1. install python and packages under requirements.txt
        pip install -r requirements.txt
        I used a venv using these commands
            python3 -m venv venv
            source venv/bin/activate     # macOS/Linux
            venv\Scripts\activate        # Windows
            pip install -r requirements.txt

    2. create the schema: mysql -u root -p < db/schema.sql
    
    3. Download all the databases we used
    
    4. Put all the .csv files into the TuneTracker/app/data directory
    
    5. Update all the import python scripts under TuneTracker/app to match your SQL user login. It should look something like this before:
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="YOUR_PASSWORD",
                database="tunetracker"
            )
            
    6. Run import scripts (I used a venv):
        python import_spotify_final.py  - inserts artist into music_artist and tracks into music_track and connects them
        
        python import_lastfm.py  - loads listens to show popular songs
        
        python import_world_bank_ref.py
        &                                   - populates world_bank_country, indicator, and data
        python import_world_bank_data.py
        
    7. Confirm everything imported correctly by using the analytic view



To see analytic view (from demo video):
    SELECT COUNT(*) FROM music_track;
    SELECT COUNT(*) FROM ext_lastfm_listens;
    SELECT COUNT(*) FROM world_bank_data;


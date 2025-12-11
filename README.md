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
    1. Install python and packages under requirements.txt with:
        pip install -r requirements.txt
        I used a venv using these commands
            python3 -m venv venv
            source venv/bin/activate     # macOS/Linux
            venv\Scripts\activate        # Windows
            pip install -r requirements.txt
            
    2. Download all the databases we used
    
    3. Put all the .csv files into the TuneTracker/app/data directory
    
    4. Create databases by running sql files under TuneTracker/app
        schema.sql
        analytic_views.sql
        (DO NOT RUN sample_data.sql yet until we have importing song data)
    
    5. Update all the import python scripts under TuneTracker/app to match your SQL user login. It should look something like this before:
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="YOUR_PASSWORD",
                database="tunetracker"
            )
            Files that need updated:
                import_spotify_final.py

                import_lastfm.py

                import_world_bank_ref.py

                import_world_bank_data.py
                
                main.py
            
    6. Run import scripts (I used a venv):
        python import_spotify_final.py  - inserts artist into music_artist and tracks into music_track and connects them (may take a while)
        
        python import_lastfm.py  - loads listens to show popular songs
        
        python import_world_bank_ref.py
        &                                   - populates world_bank_country, indicator, and data
        python import_world_bank_data.py
        
        OPTIONAL - Create sample users and playlists by running sample_data.sql
        
    7. Confirm everything imported correctly (optional)
        SELECT COUNT(*) FROM music_track;
        SELECT COUNT(*) FROM music_artist;
        SELECT COUNT(*) FROM ext_lastfm_listens;
        SELECT COUNT(*) FROM ref_country;
        SELECT COUNT(*) FROM world_bank_indicator;
        
        

        -- analytics
        SELECT * FROM v_user_top_tracks LIMIT 20;
        SELECT * FROM v_recommendation_explorer LIMIT 20;
        
    8. run program with python main.py



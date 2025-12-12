App : TuneTrack
By: Owen Lyons

Description:
    This is an app that lets user log their music listening habits and see recomendations on what to listen to based on other peoples' and their own listening habits.
    The app allows users to make a profile and log in. Once logged in there are menus to log songs they've listened to, make a playlist, and add songs to them. There is also a tab to receive reccomendations based on what other profiles have listened to and based on the genre of songs you've listened to before. You can see internet usage in your country to see how many other people there use the internet. And based on lastfm's usage you can see songs that are trending.


ERD:
    The ER Diagram can be found in the documentation folder as a .drawio file. The red tables are strong entities, the green are associative entities, and blue are weak entities.
    
YouTube demo link: https://youtu.be/Mfm3U_ZIkCc
    


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
        
        should get results at:
        113999
        31407
        181153
        263
        17577
        
    8. run program with python main.py


    9. Run these for analytic views
        SELECT * FROM `v_genre_popularity`;
        SELECT * FROM `v_global_top_tracks`;
        SELECT * FROM `v_recommendation_candidates`;
        SELECT * FROM `v_user_daily_stats`;
        SELECT * FROM `v_user_favorite_genres`;
        SELECT * FROM `v_user_genre_listens`;
        SELECT * FROM `v_user_listen_history`;
        SELECT * FROM `v_user_top_artists`;
        SELECT * FROM `v_user_top_genres`;
        SELECT * FROM `v_user_top_tracks`;
        
        
    10. run this to see all users signed in and password if you would like to use them: SELECT * FROM core_user;

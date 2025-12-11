USE tunetracker;

-- =========================================================
-- ANALYTIC VIEWS FOR TUNETRACKER
-- Favorite genres, recommendation engine, insights
-- =========================================================


-- ---------------------------------------------------------
-- 1. USER → GENRE LISTEN COUNTS
-- ---------------------------------------------------------
CREATE OR REPLACE VIEW v_user_genre_listens AS
SELECT 
    u.user_id,
    g.genre_id,
    g.name AS genre_name,
    COUNT(*) AS listen_count
FROM core_user u
JOIN core_listen_event le 
    ON le.user_id = u.user_id
JOIN music_track_genre tg 
    ON tg.track_id = le.track_id
JOIN ref_genre g
    ON g.genre_id = tg.genre_id
GROUP BY 
    u.user_id,
    g.genre_id,
    g.name;


-- ---------------------------------------------------------
-- 2. USER FAVORITE GENRES (TOP 3 PER USER)
-- ---------------------------------------------------------
CREATE OR REPLACE VIEW v_user_favorite_genres AS
SELECT 
    x.user_id,
    x.genre_id,
    x.genre_name,
    x.listen_count
FROM (
    SELECT 
        v.*,
        DENSE_RANK() OVER (
            PARTITION BY v.user_id
            ORDER BY v.listen_count DESC
        ) AS rank_num
    FROM v_user_genre_listens v
) AS x
WHERE x.rank_num <= 3;


-- ---------------------------------------------------------
-- 3. GENRE-BASED PERSONALIZED RECOMMENDER
--    (Uses favorite genres and excludes listened tracks)
-- ---------------------------------------------------------
CREATE OR REPLACE VIEW v_recommendation_genre AS
SELECT
    u.user_id,
    t.track_id,
    t.title,
    a.name AS artist_name,
    g.name AS genre_name,
    t.popularity
FROM core_user u
JOIN v_user_favorite_genres fav
    ON fav.user_id = u.user_id
JOIN music_track_genre tg
    ON tg.genre_id = fav.genre_id
JOIN ref_genre g
    ON tg.genre_id = g.genre_id
JOIN music_track t
    ON t.track_id = tg.track_id
JOIN music_track_artist mta
    ON t.track_id = mta.track_id
JOIN music_artist a
    ON mta.artist_id = a.artist_id
LEFT JOIN core_listen_event le
    ON le.user_id = u.user_id
    AND le.track_id = t.track_id
WHERE le.track_id IS NULL          -- exclude songs user already heard
  AND t.popularity IS NOT NULL
GROUP BY 
    u.user_id,
    t.track_id,
    t.title,
    a.name,
    g.name,
    t.popularity
ORDER BY t.popularity DESC;


-- ---------------------------------------------------------
-- 4. GLOBAL TOP TRACKS (popularity leaderboard)
-- ---------------------------------------------------------
CREATE OR REPLACE VIEW v_global_top_tracks AS
SELECT 
    t.track_id,
    t.title,
    GROUP_CONCAT(DISTINCT a.name ORDER BY a.name SEPARATOR ', ') AS artists,
    t.popularity
FROM music_track t
JOIN music_track_artist mta ON t.track_id = mta.track_id
JOIN music_artist a ON mta.artist_id = a.artist_id
WHERE t.popularity IS NOT NULL
GROUP BY 
    t.track_id, t.title, t.popularity
ORDER BY t.popularity DESC;


-- ---------------------------------------------------------
-- 5. DETAIL VIEW FOR USER LISTEN HISTORY
-- ---------------------------------------------------------
CREATE OR REPLACE VIEW v_user_listen_history AS
SELECT
    le.user_id,
    le.track_id,
    t.title,
    GROUP_CONCAT(DISTINCT a.name ORDER BY a.name SEPARATOR ', ') AS artists,
    le.played_at,
    t.popularity
FROM core_listen_event le
JOIN music_track t ON le.track_id = t.track_id
JOIN music_track_artist mta ON t.track_id = mta.track_id
JOIN music_artist a ON mta.artist_id = a.artist_id
GROUP BY
    le.user_id,
    le.track_id,
    t.title,
    le.played_at,
    t.popularity
ORDER BY le.played_at DESC;


-- ---------------------------------------------------------
-- 6. LAST.FM → SPOTIFY MATCH VERIFICATION VIEW
-- ---------------------------------------------------------
CREATE OR REPLACE VIEW v_lastfm_unmatched AS
SELECT 
    l.id AS lastfm_id,
    l.username,
    l.artist_name,
    l.track_name
FROM ext_lastfm_listens l
LEFT JOIN map_lastfm_track m
    ON m.lastfm_id = l.id
WHERE m.track_id IS NULL;

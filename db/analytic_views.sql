-- =============================================
-- TuneTracker Analytic Views
-- =============================================
USE tunetracker;

-- ---------------------------------------------------------
-- 1. USER GENRE LISTENS
-- ---------------------------------------------------------
CREATE OR REPLACE VIEW v_user_genre_listens AS 
SELECT 
    le.user_id,
    g.genre_id,
    g.name AS genre_name,
    COUNT(*) AS listen_count
FROM core_listen_event le
JOIN music_track_genre tg ON le.track_id = tg.track_id
JOIN ref_genre g ON tg.genre_id = g.genre_id
GROUP BY le.user_id, g.genre_id, g.name;

-- ------------------------------------------------
-- 2. USER TOP TRACKS
-- ------------------------------------------------
CREATE OR REPLACE VIEW v_user_top_tracks AS
SELECT 
    le.user_id,
    t.track_id,
    t.title,
    COUNT(*) AS play_count
FROM core_listen_event le
JOIN music_track t ON le.track_id = t.track_id
GROUP BY le.user_id, t.track_id
ORDER BY le.user_id, play_count DESC;


-- ------------------------------------------------
-- 3. USER TOP ARTISTS
-- ------------------------------------------------
CREATE OR REPLACE VIEW v_user_top_artists AS
SELECT 
    le.user_id,
    a.artist_id,
    a.name AS artist_name,
    COUNT(*) AS play_count
FROM core_listen_event le
JOIN music_track_artist mta ON le.track_id = mta.track_id
JOIN music_artist a ON mta.artist_id = a.artist_id
GROUP BY le.user_id, a.artist_id
ORDER BY le.user_id, play_count DESC;


-- ------------------------------------------------
-- 4. USER DAILY STATS (simple version)
-- ------------------------------------------------
CREATE OR REPLACE VIEW v_user_daily_stats AS
SELECT
    le.user_id,
    DATE(le.played_at) AS listen_date,
    COUNT(*) AS total_listens,
    COUNT(DISTINCT le.track_id) AS distinct_tracks
FROM core_listen_event le
GROUP BY le.user_id, DATE(le.played_at)
ORDER BY le.user_id, listen_date;

-- ------------------------------------------------
-- 5. TOP USER GENRE
-- ------------------------------------------------
CREATE OR REPLACE VIEW v_user_top_genres AS
SELECT
    le.user_id,
    g.genre_id,
    COUNT(*) AS plays
FROM core_listen_event le
JOIN music_track_genre tg ON le.track_id = tg.track_id
JOIN ref_genre g ON tg.genre_id = g.genre_id
GROUP BY le.user_id, g.genre_id;

-- ---------------------------------------------------------
-- 6. FAVORITE GENRES PER USER (Top 3) - USED WITH v_recommendation_genre
-- ---------------------------------------------------------
CREATE OR REPLACE VIEW v_user_favorite_genres AS
SELECT user_id, genre_id, genre_name, listen_count
FROM (
    SELECT
        v.user_id,
        v.genre_id,
        v.genre_name,
        v.listen_count,
        DENSE_RANK() OVER (
            PARTITION BY v.user_id
            ORDER BY v.listen_count DESC
        ) AS rnk
    FROM v_user_genre_listens v
) ranked
WHERE rnk <= 3;

-- ------------------------------------------------
-- 7. GLOBAL TOP TRACKS (TuneTracker only)
-- ------------------------------------------------
CREATE OR REPLACE VIEW v_global_top_tracks AS
SELECT
    t.track_id,
    t.title,
    COUNT(*) AS play_count
FROM core_listen_event le
JOIN music_track t ON le.track_id = t.track_id
GROUP BY t.track_id
ORDER BY play_count DESC;


-- ------------------------------------------------
-- 8. GENRE POPULARITY
-- ------------------------------------------------
CREATE OR REPLACE VIEW v_genre_popularity AS
SELECT
    g.genre_id,
    g.name AS genre_name,
    COUNT(*) AS play_count
FROM core_listen_event le
JOIN music_track_genre tg ON le.track_id = tg.track_id
JOIN ref_genre g ON tg.genre_id = g.genre_id
GROUP BY g.genre_id
ORDER BY play_count DESC;


-- ------------------------------------------------
-- 9. GENRE + POPULARITY RECOMMENDATION VIEW
-- ------------------------------------------------
CREATE OR REPLACE VIEW v_recommendation_candidates AS
SELECT
    u.user_id,
    t.track_id,
    t.title AS track_title,
    a.name AS artist_name,
    g.name AS genre_name,
    t.popularity,
    -- Weighted score: 70% genre presence, 30% popularity
    (0.7 * 1 + 0.3 * (t.popularity / 100)) AS rec_score
FROM core_user u
-- Expand to all tracks the user might like
CROSS JOIN music_track t
-- Attach genres
JOIN music_track_genre tg ON t.track_id = tg.track_id
JOIN ref_genre g ON tg.genre_id = g.genre_id
-- Attach artists
JOIN music_track_artist mta ON t.track_id = mta.track_id
JOIN music_artist a ON mta.artist_id = a.artist_id
-- Exclude tracks the user has already listened to
WHERE NOT EXISTS (
    SELECT 1
    FROM core_listen_event le
    WHERE le.user_id = u.user_id
      AND le.track_id = t.track_id
)
AND t.popularity IS NOT NULL
ORDER BY u.user_id, rec_score DESC;


-- ---------------------------------------------------------
-- 10. DETAIL VIEW FOR USER LISTEN HISTORY
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


-- ------------------------------------------------
-- 11. RECOMEND GENRES _ USED OVER v_recommendation_candidates (MAIN FOR RECS)
-- ------------------------------------------------
DROP VIEW IF EXISTS v_recommendation_genre;
CREATE VIEW v_recommendation_genre AS
SELECT 
    u.user_id,
    t.track_id,
    -- aggregate title (all rows for same track_id are identical)
    MAX(t.title) AS title,
    -- combine all artists for the track
    GROUP_CONCAT(DISTINCT a.name ORDER BY a.name SEPARATOR ', ') AS artist_name,
    -- combine all genres for the track
    GROUP_CONCAT(DISTINCT g.name ORDER BY g.name SEPARATOR ', ') AS genre_name,
    -- track popularity
    MAX(t.popularity) AS popularity
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
WHERE le.track_id IS NULL        -- user has not listened
  AND t.popularity IS NOT NULL
GROUP BY u.user_id, t.track_id
ORDER BY popularity DESC;
-- end of v_recommendation_genre --


  
  

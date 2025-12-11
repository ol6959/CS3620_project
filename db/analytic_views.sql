
-- =============================================
-- TuneTracker Analytic Views
-- =============================================
USE tunetracker;

-- ------------------------------------------------
-- 1. USER TOP TRACKS
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
-- 2. USER TOP ARTISTS
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
-- 3. USER DAILY STATS (simple version)
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
-- 4. GLOBAL TOP TRACKS (TuneTracker only)
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
-- 5. GENRE POPULARITY
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
-- 6. GENRE + POPULARITY RECOMMENDATION VIEW
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

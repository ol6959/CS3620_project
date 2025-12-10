USE tunetracker;

-- ===========================================================
-- VIEW 1: User Listening Dashboard
-- Shows daily listening stats (activity summary feature)
-- ===========================================================

CREATE OR REPLACE VIEW v_user_listening_dashboard AS
SELECT
    u.user_id,
    up.display_name,
    m.listen_date,
    m.total_listens,
    m.unique_tracks,
    m.minutes_listened
FROM mart_user_daily_listening m
JOIN core_user u ON u.user_id = m.user_id
LEFT JOIN core_user_profile up ON up.user_id = u.user_id
ORDER BY m.listen_date DESC;


-- ===========================================================
-- VIEW 2: User Listening vs GDP Context
-- Compares user's listening to their country’s economic metric
-- GDP per capita => indicator_code = 'NY.GDP.PCAP.KD'
-- ===========================================================

CREATE OR REPLACE VIEW v_user_global_context AS
SELECT
    u.user_id,
    up.display_name,
    up.country_code,
    c.name AS country_name,
    ci.year,
    ci.value AS gdp_per_capita,
    m.total_listens,
    m.minutes_listened,
    ROUND(m.minutes_listened / ci.value, 6) AS listens_to_gdp_ratio
FROM core_user_profile up
JOIN core_user u ON u.user_id = up.user_id
JOIN mart_user_daily_listening m ON m.user_id = up.user_id
JOIN bg_country_indicator ci ON ci.country_code = up.country_code
JOIN ref_country c ON c.country_code = up.country_code
WHERE ci.indicator_code = 'NY.GDP.PCAP.KD'
ORDER BY ci.value DESC;


-- ===========================================================
-- VIEW 3: Recommendation Explorer
-- Shows recommended tracks + audio features + reason for rec
-- ===========================================================

CREATE OR REPLACE VIEW v_recommendation_explorer AS
SELECT
    r.rec_id,
    r.user_id,
    up.display_name,
    t.track_id,
    t.title AS track_title,
    t.energy,
    t.danceability,
    ROUND((t.energy + t.danceability) / 2, 3) AS mainstream_score,
    r.reason,
    r.action,
    r.generated_at
FROM music_recommendation_event r
JOIN music_track t ON t.track_id = r.track_id
LEFT JOIN core_user_profile up ON up.user_id = r.user_id
ORDER BY r.generated_at DESC;


-- ===========================================================
-- OPTIONAL BONUS VIEW: Most Played Tracks by Genre
-- Great for demonstrating SQL analytics features
-- ===========================================================

CREATE OR REPLACE VIEW v_top_genres AS
SELECT
    g.name AS genre,
    COUNT(le.listen_id) AS total_listens
FROM core_listen_event le
JOIN music_track_genre tg ON tg.track_id = le.track_id
JOIN ref_genre g ON g.genre_id = tg.genre_id
GROUP BY g.name
ORDER BY total_listens DESC;

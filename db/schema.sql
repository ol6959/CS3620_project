-- ===========================================
-- TuneTracker DATABASE SCHEMA
-- ===========================================

DROP DATABASE IF EXISTS tunetracker;
CREATE DATABASE tunetracker;
USE tunetracker;

-- ==========================================
-- Users & Profiles
-- ==========================================

CREATE TABLE core_user (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE core_user_profile (
    user_id INT PRIMARY KEY,
    display_name VARCHAR(255) NOT NULL,
    country_code VARCHAR(10),
    birth_year INT,
    avatar_url VARCHAR(500),

    FOREIGN KEY (user_id) REFERENCES core_user(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE INDEX idx_profile_country ON core_user_profile (country_code);
CREATE INDEX idx_profile_birthyear ON core_user_profile (birth_year);


CREATE TABLE audit_log (
    audit_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    event_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES core_user(user_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);


-- ===========================================
-- 2. WORLD BANK: REFERENCE TABLES
-- ===========================================

CREATE TABLE ref_country (
    country_code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    region VARCHAR(255)
);

CREATE TABLE ref_indicator (
    indicator_code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);


-- ===========================================
-- 3. MUSIC DATA (SPOTIFY CLEAN DATASET)
-- ===========================================

CREATE TABLE music_artist (
    artist_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    
    UNIQUE KEY uq_artist_name (name)
);

CREATE TABLE music_album (
    album_id INT AUTO_INCREMENT PRIMARY KEY,
    spotify_album_id VARCHAR(100),
    name VARCHAR(255),
    release_date DATE NULL
);

CREATE TABLE music_track (
    track_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    album_name VARCHAR(255),
    duration_ms INT,
    popularity TINYINT,              -- 0–100 from Spotify
    is_explicit TINYINT(1) DEFAULT 0,
    spotify_id VARCHAR(64),          -- optional external ID
    release_year SMALLINT,           -- optional
    release_date DATE,               -- optional

    INDEX idx_track_title (title),
    INDEX idx_track_popularity (popularity),
    INDEX idx_track_release_year (release_year)
);


CREATE TABLE music_track_artist (
    track_id INT NOT NULL,
    artist_id INT NOT NULL,

    PRIMARY KEY (track_id, artist_id),

    FOREIGN KEY (track_id) REFERENCES music_track(track_id)
        ON DELETE CASCADE,
    FOREIGN KEY (artist_id) REFERENCES music_artist(artist_id)
        ON DELETE CASCADE
);


CREATE TABLE ref_genre (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE music_track_genre (
    track_id INT NOT NULL,
    genre_id INT NOT NULL,

    PRIMARY KEY (track_id, genre_id),

    FOREIGN KEY (track_id) REFERENCES music_track(track_id)
        ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES ref_genre(genre_id)
        ON DELETE CASCADE
);



-- ===========================================
-- 4. USER LISTENING EVENTS
-- ===========================================

CREATE TABLE core_listen_event (
    listen_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    track_id INT NOT NULL,
    played_at DATETIME NOT NULL,
    source VARCHAR(20) DEFAULT 'manual',

    FOREIGN KEY (user_id) REFERENCES core_user(user_id)
        ON DELETE CASCADE,
    FOREIGN KEY (track_id) REFERENCES music_track(track_id)
        ON DELETE RESTRICT
);


-- ===========================================
-- 5. PLAYLIST SYSTEM
-- ===========================================

CREATE TABLE core_playlist (
    playlist_id INT AUTO_INCREMENT PRIMARY KEY,
    owner_user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (owner_user_id) REFERENCES core_user(user_id)
        ON DELETE CASCADE
);


CREATE TABLE core_playlist_track (
    playlist_id INT NOT NULL,
    track_id INT NOT NULL,
    position INT NOT NULL,
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (playlist_id, position),

    UNIQUE KEY uq_playlist_track (playlist_id, track_id),

    FOREIGN KEY (playlist_id) REFERENCES core_playlist(playlist_id)
        ON DELETE CASCADE,
    FOREIGN KEY (track_id) REFERENCES music_track(track_id)
        ON DELETE RESTRICT
);


-- ===========================================
-- 6. LAST.FM DATASET (PUBLIC DATASET #3)
-- ===========================================

CREATE TABLE ext_lastfm_listens (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255),
    artist_name VARCHAR(255),
    track_name VARCHAR(255),
    album_name VARCHAR(255),
    listen_date DATE,
    listen_time TIME,

    INDEX idx_lastfm_artist (artist_name),
    INDEX idx_lastfm_track (track_name),
    INDEX idx_lastfm_date (listen_date)
);


-- Mapping table for Last.fm → Spotify matched tracks
CREATE TABLE map_lastfm_track (
    lastfm_id BIGINT NOT NULL,
    track_id INT NOT NULL,

    PRIMARY KEY (lastfm_id, track_id),

    FOREIGN KEY (lastfm_id) REFERENCES ext_lastfm_listens(id)
        ON DELETE CASCADE,
    FOREIGN KEY (track_id) REFERENCES music_track(track_id)
        ON DELETE CASCADE
);


-- ===========================================
-- 7. WBI
-- ===========================================
CREATE TABLE world_bank_indicator (
    country_code VARCHAR(10) NOT NULL,
    indicator_code VARCHAR(50) NOT NULL,
    year INT NOT NULL,
    value DOUBLE,

    PRIMARY KEY (country_code, indicator_code, year),

    FOREIGN KEY (country_code) REFERENCES ref_country(country_code)
        ON DELETE CASCADE,
    FOREIGN KEY (indicator_code) REFERENCES ref_indicator(indicator_code)
        ON DELETE CASCADE
);

CREATE TABLE mart_user_daily_listening (
    user_id INT NOT NULL,
    listen_date DATE NOT NULL,
    total_listens INT NOT NULL,
    distinct_tracks INT NOT NULL,
    minutes_listened DECIMAL(10,2),

    PRIMARY KEY (user_id, listen_date),

    FOREIGN KEY (user_id) REFERENCES core_user(user_id)
        ON DELETE CASCADE
);





CREATE OR REPLACE VIEW v_recommendation_explorer AS
SELECT
    u.user_id,
    t.track_id,
    t.title AS track_title,
    a.name AS artist_name,
    g.name AS genre_name,
    t.popularity
FROM core_user u
JOIN music_track t
JOIN music_track_genre tg ON t.track_id = tg.track_id
JOIN ref_genre g ON tg.genre_id = g.genre_id
JOIN music_track_artist mta ON t.track_id = mta.track_id
JOIN music_artist a ON mta.artist_id = a.artist_id
WHERE t.popularity IS NOT NULL
  AND t.track_id NOT IN (
        SELECT le.track_id 
        FROM core_listen_event le 
        WHERE le.user_id = u.user_id
  );
  
CREATE OR REPLACE VIEW v_user_top_genres AS
SELECT
    le.user_id,
    g.genre_id,
    COUNT(*) AS plays
FROM core_listen_event le
JOIN music_track_genre tg ON le.track_id = tg.track_id
JOIN ref_genre g ON tg.genre_id = g.genre_id
GROUP BY le.user_id, g.genre_id;


CREATE OR REPLACE VIEW v_user_favorite_genres AS
SELECT user_id, genre_id
FROM (
    SELECT 
        user_id,
        genre_id,
        plays,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY plays DESC) AS rank_pos
    FROM v_user_top_genres
) ranked
WHERE rank_pos <= 3;   -- top 3 genres

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






-- ===========================================
-- END OF SCHEMA
-- ===========================================

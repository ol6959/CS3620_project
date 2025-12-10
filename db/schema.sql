-- ===========================================================
-- DATABASE SETUP
-- ===========================================================

CREATE DATABASE IF NOT EXISTS tunetracker;
USE tunetracker;

SET foreign_key_checks = 0;

-- ===========================================================
-- DROP TABLES (in correct order for safe re-runs)
-- ===========================================================

DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS mart_user_daily_listening;
DROP TABLE IF EXISTS bg_country_indicator;
DROP TABLE IF EXISTS ref_indicator;
DROP TABLE IF EXISTS ref_country;
DROP TABLE IF EXISTS music_recommendation_event;
DROP TABLE IF EXISTS music_track_genre;
DROP TABLE IF EXISTS music_track_artist;
DROP TABLE IF EXISTS music_track;
DROP TABLE IF EXISTS music_album;
DROP TABLE IF EXISTS music_artist;
DROP TABLE IF EXISTS ref_genre;
DROP TABLE IF EXISTS core_feedback;
DROP TABLE IF EXISTS core_track_like;
DROP TABLE IF EXISTS core_playlist_track;
DROP TABLE IF EXISTS core_playlist;
DROP TABLE IF EXISTS core_listen_event;
DROP TABLE IF EXISTS core_session;
DROP TABLE IF EXISTS core_user_profile;
DROP TABLE IF EXISTS core_user;

-- ===========================================================
-- REFERENCE TABLES (must come first)
-- ===========================================================

CREATE TABLE ref_country (
    country_code CHAR(3) PRIMARY KEY,
    name VARCHAR(100),
    region VARCHAR(100),
    income_group VARCHAR(100)
);

CREATE TABLE ref_indicator (
    indicator_code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(100)
);

CREATE TABLE ref_genre (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    description VARCHAR(255)
);

-- ===========================================================
-- CORE USER TABLES
-- ===========================================================

CREATE TABLE core_user (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('active', 'disabled') DEFAULT 'active'
);

CREATE TABLE core_user_profile (
    user_id INT PRIMARY KEY,
    display_name VARCHAR(100),
    country_code CHAR(3),
    birth_year INT,
    privacy_level ENUM('public','friends','private') DEFAULT 'public',
    FOREIGN KEY (user_id) REFERENCES core_user(user_id),
    FOREIGN KEY (country_code) REFERENCES ref_country(country_code)
);

CREATE TABLE core_session (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    ip_hash VARCHAR(100),
    user_agent VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES core_user(user_id)
);

-- ===========================================================
-- MUSIC CATALOG TABLES (Spotify data)
-- ===========================================================

CREATE TABLE music_artist (
    artist_id INT AUTO_INCREMENT PRIMARY KEY,
    spotify_artist_id VARCHAR(50) UNIQUE,
    name VARCHAR(255) NOT NULL,
    origin_country_code CHAR(3),
    FOREIGN KEY (origin_country_code) REFERENCES ref_country(country_code)
);

CREATE TABLE music_album (
    album_id INT AUTO_INCREMENT PRIMARY KEY,
    spotify_album_id VARCHAR(50) UNIQUE,
    title VARCHAR(255) NOT NULL,
    release_date DATE,
    album_type VARCHAR(100)
);

CREATE TABLE music_track (
    track_id INT AUTO_INCREMENT PRIMARY KEY,
    spotify_track_id VARCHAR(50) UNIQUE,
    album_id INT,
    title VARCHAR(255) NOT NULL,
    duration_ms INT,
    explicit BOOLEAN DEFAULT FALSE,
    release_year INT,
    danceability DECIMAL(4,3),
    energy DECIMAL(4,3),
    valence DECIMAL(4,3),
    tempo DECIMAL(6,2),
    acousticness DECIMAL(4,3),
    instrumentalness DECIMAL(4,3),
    liveness DECIMAL(4,3),
    FOREIGN KEY (album_id) REFERENCES music_album(album_id)
);

CREATE TABLE music_track_artist (
    track_id INT NOT NULL,
    artist_id INT NOT NULL,
    role ENUM('primary','featured') DEFAULT 'primary',
    PRIMARY KEY (track_id, artist_id),
    FOREIGN KEY (track_id) REFERENCES music_track(track_id),
    FOREIGN KEY (artist_id) REFERENCES music_artist(artist_id)
);

CREATE TABLE music_track_genre (
    track_id INT NOT NULL,
    genre_id INT NOT NULL,
    source ENUM('spotify','lastfm','manual'),
    PRIMARY KEY (track_id, genre_id),
    FOREIGN KEY (track_id) REFERENCES music_track(track_id),
    FOREIGN KEY (genre_id) REFERENCES ref_genre(genre_id)
);

CREATE TABLE music_recommendation_event (
    rec_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    track_id INT NOT NULL,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reason VARCHAR(255),
    action ENUM('shown','clicked','ignored','skipped') DEFAULT 'shown',
    FOREIGN KEY (user_id) REFERENCES core_user(user_id),
    FOREIGN KEY (track_id) REFERENCES music_track(track_id)
);

-- ===========================================================
-- USER-GENERATED CONTENT (Playlists, listens, likes)
-- ===========================================================

CREATE TABLE core_listen_event (
    listen_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    track_id INT NOT NULL,
    played_at DATETIME NOT NULL,
    source ENUM('manual','spotify_import','file_upload') DEFAULT 'manual',
    FOREIGN KEY (user_id) REFERENCES core_user(user_id),
    FOREIGN KEY (track_id) REFERENCES music_track(track_id)
);

CREATE TABLE core_playlist (
    playlist_id INT AUTO_INCREMENT PRIMARY KEY,
    owner_user_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (owner_user_id) REFERENCES core_user(user_id)
);

CREATE TABLE core_playlist_track (
    playlist_id INT NOT NULL,
    track_id INT NOT NULL,
    position INT,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (playlist_id, track_id),
    FOREIGN KEY (playlist_id) REFERENCES core_playlist(playlist_id) ON DELETE CASCADE,
    FOREIGN KEY (track_id) REFERENCES music_track(track_id)
);

CREATE TABLE core_track_like (
    user_id INT NOT NULL,
    track_id INT NOT NULL,
    liked BOOLEAN DEFAULT TRUE,
    rated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, track_id),
    FOREIGN KEY (user_id) REFERENCES core_user(user_id),
    FOREIGN KEY (track_id) REFERENCES music_track(track_id)
);

CREATE TABLE core_feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category ENUM('bug','feature','data_issue','other'),
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('new','in_review','closed') DEFAULT 'new',
    FOREIGN KEY (user_id) REFERENCES core_user(user_id)
);

-- ===========================================================
-- BACKGROUND (World Bank WDI Data)
-- ===========================================================

CREATE TABLE bg_country_indicator (
    country_code CHAR(3),
    indicator_code VARCHAR(20),
    year INT,
    value DECIMAL(18,4),
    PRIMARY KEY (country_code, indicator_code, year),
    FOREIGN KEY (country_code) REFERENCES ref_country(country_code),
    FOREIGN KEY (indicator_code) REFERENCES ref_indicator(indicator_code)
);

-- ===========================================================
-- ANALYTICS / Marts
-- ===========================================================

CREATE TABLE mart_user_daily_listening (
    user_id INT,
    listen_date DATE,
    total_listens INT,
    unique_tracks INT,
    minutes_listened DECIMAL(10,2),
    PRIMARY KEY (user_id, listen_date),
    FOREIGN KEY (user_id) REFERENCES core_user(user_id)
);

-- ===========================================================
-- AUDIT LOG
-- ===========================================================

CREATE TABLE audit_log (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    event_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INT,
    event_type ENUM('login','logout','signup','create_playlist','add_listen','like_track','feedback'),
    entity_type VARCHAR(100),
    entity_id INT,
    details JSON,
    FOREIGN KEY (user_id) REFERENCES core_user(user_id)
);

-- ===========================================================
-- PERFORMANCE INDEXES
-- ===========================================================

CREATE INDEX idx_listen_user_date ON core_listen_event (user_id, played_at);
CREATE INDEX idx_country_indicator ON bg_country_indicator (indicator_code, year);
CREATE INDEX idx_track_features ON music_track (release_year, energy, danceability);

SET foreign_key_checks = 1;

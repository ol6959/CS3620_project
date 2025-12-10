-- Test File for whatever is needed --
USE tunetracker;

-- ===========================================================
-- SAMPLE DATA FOR TUNETRACKER DEMO
-- Minimal, clean inserts for UI + analytics testing
-- ===========================================================

-- ---------------------------
-- Reference Data
-- ---------------------------
INSERT INTO ref_country (country_code, name, region, income_group) VALUES
('USA', 'United States', 'North America', 'High income'),
('GBR', 'United Kingdom', 'Europe', 'High income'),
('IND', 'India', 'South Asia', 'Lower middle income');

INSERT INTO ref_indicator (indicator_code, name, category) VALUES
('NY.GDP.PCAP.KD', 'GDP per capita (constant 2015 US$)', 'Economy'),
('IT.NET.USER.ZS', 'Individuals using the Internet (% of population)', 'Technology');

INSERT INTO bg_country_indicator
(country_code, indicator_code, year, value) VALUES
('USA', 'NY.GDP.PCAP.KD', 2023, 63500),
('GBR', 'NY.GDP.PCAP.KD', 2023, 45000),
('IND', 'NY.GDP.PCAP.KD', 2023, 2400);

-- ---------------------------
-- Music Data (Spotify-style)
-- ---------------------------

INSERT INTO music_artist (spotify_artist_id, name, origin_country_code)
VALUES ('6eUKZXaKkcviH0Ku9w2n3V', 'Ed Sheeran', 'GBR');

INSERT INTO music_album (spotify_album_id, title, release_date, album_type)
VALUES ('3T4tUhGYeRNVUGevb0wThu', '=', '2021-10-29', 'album');

INSERT INTO music_track
(spotify_track_id, album_id, title, duration_ms, explicit,
 release_year, danceability, energy, valence, tempo,
 acousticness, instrumentalness, liveness)
VALUES
('3eekarcy7fvSK0M1YyjZxZ', 1, 'Shivers', 207000, FALSE,
 2021, 0.77, 0.85, 0.65, 140.0,
 0.05, 0.00, 0.09),
('50nfwKoDiSYg8zOCREWAm5', 1, 'Bad Habits', 231000, FALSE,
 2021, 0.75, 0.80, 0.60, 125.0,
 0.10, 0.00, 0.12);

INSERT INTO ref_genre (name, description) VALUES
('pop', 'Popular mainstream music'),
('dance pop', 'High-energy pop with dance elements');

INSERT INTO music_track_artist (track_id, artist_id, role) VALUES
(1, 1, 'primary'),
(2, 1, 'primary');

INSERT INTO music_track_genre (track_id, genre_id, source) VALUES
(1, 1, 'spotify'),
(2, 1, 'spotify'),
(2, 2, 'spotify');

-- ---------------------------
-- Users + Profiles
-- ---------------------------

INSERT INTO core_user (email, password_hash)
VALUES
('alice@example.com', 'HASH1'),
('bob@example.com', 'HASH2');

INSERT INTO core_user_profile (user_id, display_name, country_code, birth_year)
VALUES
(1, 'Alice', 'USA', 2001),
(2, 'Bob', 'IND', 1999);

-- ---------------------------
-- User Activity
-- ---------------------------

INSERT INTO core_listen_event (user_id, track_id, played_at) VALUES
(1, 1, '2025-12-05 14:30:00'),
(1, 2, '2025-12-05 14:35:00'),
(2, 2, '2025-12-05 16:00:00');

INSERT INTO core_track_like (user_id, track_id, liked) VALUES
(1, 1, TRUE),
(2, 2, TRUE);

INSERT INTO core_playlist (owner_user_id, name)
VALUES (1, 'My Favs');

INSERT INTO core_playlist_track (playlist_id, track_id, position)
VALUES
(1, 1, 1),
(1, 2, 2);

-- ---------------------------
-- Analytics (for dashboards)
-- ---------------------------

INSERT INTO mart_user_daily_listening
(user_id, listen_date, total_listens, unique_tracks, minutes_listened)
VALUES
(1, '2025-12-05', 2, 2, 7.0),
(2, '2025-12-05', 1, 1, 3.5);

-- Done!

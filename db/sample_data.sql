-- ============================================
-- SAMPLE DATA FOR TUNETRACKER
-- Demo users, profiles, playlists, and listen events
-- ============================================

USE tunetracker;

-- --------------------------------------------
-- 1. USERS
-- --------------------------------------------
INSERT INTO core_user (email, password_hash, created_at)
VALUES 
    ('alice@example.com', 'hash1', NOW()),
    ('bob@example.com',   'hash2', NOW()),
    ('carol@example.com', 'hash3', NOW());

-- Store generated IDs
SELECT * FROM core_user;


-- --------------------------------------------
-- 2. USER PROFILES
-- (Use the actual generated user_ids)
-- --------------------------------------------
INSERT INTO core_user_profile (user_id, display_name, country_code, birth_year, avatar_url)
VALUES
    ((SELECT user_id FROM core_user WHERE email='alice@example.com'),
        'Alice', 'USA', 1999, NULL),

    ((SELECT user_id FROM core_user WHERE email='bob@example.com'),
        'Bob',   'CAN', 1998, NULL),

    ((SELECT user_id FROM core_user WHERE email='carol@example.com'),
        'Carol', 'GBR', 1997, NULL);


-- --------------------------------------------
-- 3. PLAYLISTS
-- --------------------------------------------
INSERT INTO core_playlist (owner_user_id, name)
VALUES
    ((SELECT user_id FROM core_user WHERE email='alice@example.com'),
        'Alice Favorites'),

    ((SELECT user_id FROM core_user WHERE email='alice@example.com'),
        'Chill Mix'),

    ((SELECT user_id FROM core_user WHERE email='bob@example.com'),
        'Bob Workout Hits');


-- --------------------------------------------
-- 4. PLAYLIST TRACKS
-- ⚠ Replace 101/102/103 with real track_id values from your DB
-- --------------------------------------------
INSERT INTO core_playlist_track (playlist_id, track_id, position)
VALUES
    (1, 101, 1),
    (1, 102, 2),
    (2, 103, 1),
    (3, 101, 1),
    (3, 103, 2);


-- --------------------------------------------
-- 5. LISTEN EVENTS (TuneTracker only)
-- --------------------------------------------
INSERT INTO core_listen_event (user_id, track_id, played_at, source)
VALUES
    ((SELECT user_id FROM core_user WHERE email='alice@example.com'),
        101, NOW() - INTERVAL 1 DAY, 'sample'),

    ((SELECT user_id FROM core_user WHERE email='alice@example.com'),
        102, NOW() - INTERVAL 2 HOUR, 'sample'),

    ((SELECT user_id FROM core_user WHERE email='bob@example.com'),
        103, NOW() - INTERVAL 3 DAY, 'sample'),

    ((SELECT user_id FROM core_user WHERE email='carol@example.com'),
        101, NOW() - INTERVAL 5 HOUR, 'sample'),

    ((SELECT user_id FROM core_user WHERE email='carol@example.com'),
        103, NOW(), 'sample');


-- --------------------------------------------
-- DONE
-- --------------------------------------------
SELECT 'Sample data inserted successfully!' AS status;
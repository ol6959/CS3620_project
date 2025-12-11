-- ============================================
-- SAMPLE DATA FOR TUNETRACKER (Latest Version)
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

SELECT * FROM core_user;

-- --------------------------------------------
-- 2. PROFILES
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
-- 3. PLAYLISTS (reset + insert)
-- --------------------------------------------

DELETE FROM core_playlist_track;
DELETE FROM core_playlist;
ALTER TABLE core_playlist AUTO_INCREMENT = 1;

INSERT INTO core_playlist (owner_user_id, name)
VALUES
    ((SELECT user_id FROM core_user WHERE email='alice@example.com'), 'Alice Favorites'),
    ((SELECT user_id FROM core_user WHERE email='alice@example.com'), 'Chill Mix'),
    ((SELECT user_id FROM core_user WHERE email='bob@example.com'),   'Bob Workout Hits');

-- --------------------------------------------
-- 4. PLAYLIST TRACKS (use real tracks)
-- --------------------------------------------

SET @t1 = (SELECT track_id FROM music_track ORDER BY RAND() LIMIT 1);
SET @t2 = (SELECT track_id FROM music_track ORDER BY RAND() LIMIT 1);
SET @t3 = (SELECT track_id FROM music_track ORDER BY RAND() LIMIT 1);

INSERT INTO core_playlist_track (playlist_id, track_id, position)
VALUES
    (1, @t1, 1),
    (1, @t2, 2),
    (2, @t3, 1),
    (3, @t1, 1),
    (3, @t3, 2);


-- --------------------------------------------
-- 4. PLAYLIST TRACKS
--    Use real track IDs from your music_track table
-- --------------------------------------------

-- get three real track IDs
SET @t1 = (SELECT track_id FROM music_track ORDER BY RAND() LIMIT 1);
SET @t2 = (SELECT track_id FROM music_track ORDER BY RAND() LIMIT 1 OFFSET 1);
SET @t3 = (SELECT track_id FROM music_track ORDER BY RAND() LIMIT 1 OFFSET 2);

INSERT INTO core_playlist_track (playlist_id, track_id, position)
VALUES
    (1, @t1, 1),
    (1, @t2, 2),
    (2, @t3, 1),
    (3, @t1, 1),
    (3, @t3, 2);

-- --------------------------------------------
-- 5. SAMPLE LISTENS
-- --------------------------------------------

INSERT INTO core_listen_event (user_id, track_id, played_at, source)
VALUES
    ((SELECT user_id FROM core_user WHERE email='alice@example.com'),
        @t1, NOW() - INTERVAL 1 DAY, 'sample'),

    ((SELECT user_id FROM core_user WHERE email='alice@example.com'),
        @t2, NOW() - INTERVAL 2 HOUR, 'sample'),

    ((SELECT user_id FROM core_user WHERE email='bob@example.com'),
        @t3, NOW() - INTERVAL 3 DAY, 'sample'),

    ((SELECT user_id FROM core_user WHERE email='carol@example.com'),
        @t1, NOW() - INTERVAL 5 HOUR, 'sample'),

    ((SELECT user_id FROM core_user WHERE email='carol@example.com'),
        @t3, NOW(), 'sample');

-- --------------------------------------------
-- DONE
-- --------------------------------------------
SELECT 'Sample data inserted successfully!' AS status;

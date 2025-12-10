from flask import Flask, request, jsonify, render_template, redirect, session, g
import mysql.connector
from functools import wraps

app = Flask(__name__)
app.secret_key = "dev_secret_key"


# ------------------------------------
# DB CONNECTION HANDLER (SAFER)
# ------------------------------------
def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Lyo265155!",
            database="tunetracker"
        )
    return g.db
    
def run_query(sql, params=None, fetchone=False, fetchall=False):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(sql, params or ())
    
    result = None
    if fetchone:
        result = cursor.fetchone()
    if fetchall:
        result = cursor.fetchall()
    
    db.commit()
    cursor.close()
    return result

    
    
@app.route("/whoami") #for debug
def whoami():
    return str(session.get("user_id"))


@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ------------------------------------
# Auth decorator
# ------------------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return render_template("must_login.html"), 403
        return f(*args, **kwargs)
    return wrapper


# ------------------------------------
# AUTH ROUTES
# ------------------------------------
@app.route("/signup", methods=["GET"])
def signup_form():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT country_code, name FROM ref_country ORDER BY name")
    countries = cursor.fetchall()
    cursor.close()

    return render_template("signup.html", countries=countries)


@app.route("/signup", methods=["POST"])
def signup_submit():
    email = request.form.get("email")
    password = request.form.get("password")
    display_name = request.form.get("display_name")
    country = request.form.get("country_code")
    birth_year = request.form.get("birth_year") or None
    avatar_url = request.form.get("avatar_url") or None

    # Validate email uniqueness
    exists = run_query(
        "SELECT 1 FROM core_user WHERE email = %s LIMIT 1",
        (email,),
        fetchone=True
    )
    if exists:
        return "<h3>⚠ Email already exists!</h3><a href='/login'>Login</a>"

    # Create user
    run_query("""
        INSERT INTO core_user (email, password_hash)
        VALUES (%s, %s)
    """, (email, password))

    user = run_query(
        "SELECT user_id FROM core_user WHERE email=%s LIMIT 1",
        (email,),
        fetchone=True
    )
    user_id = user["user_id"]

    # Create profile
    run_query("""
        INSERT INTO core_user_profile
            (user_id, display_name, country_code, birth_year, avatar_url)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, display_name, country, birth_year, avatar_url))

    # Log audit
    run_query("""
        INSERT INTO audit_log (user_id, event_type, entity_type)
        VALUES (%s, 'signup', 'user')
    """, (user_id,))

    session["user_id"] = user_id
    return redirect("/")




@app.route("/login", methods=["GET"])
def login_form():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_submit():
    email = request.form.get("email")
    password = request.form.get("password")

    user = run_query("""
        SELECT user_id FROM core_user
        WHERE email=%s AND password_hash=%s LIMIT 1
    """, (email, password), fetchone=True)

    if not user:
        return "❌ Invalid login. <a href='/login'>Try again</a>"

    session["user_id"] = user["user_id"]
    return redirect("/")


# ------------------------------------
# SEARCH API ROUTE
# ------------------------------------
@app.route("/search_tracks")
def search_tracks():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])

    results = run_query("""
        SELECT t.track_id, t.title,
               GROUP_CONCAT(a.name SEPARATOR ', ') AS artists
        FROM music_track t
        LEFT JOIN music_track_artist mta ON t.track_id = mta.track_id
        LEFT JOIN music_artist a ON mta.artist_id = a.artist_id
        WHERE t.title LIKE %s OR a.name LIKE %s
        GROUP BY t.track_id
        ORDER BY t.popularity DESC
        LIMIT 50
    """, (f"%{q}%", f"%{q}%"), fetchall=True)

    return jsonify(results)



# ------------------------------------
# LOG LISTEN PAGE
# ------------------------------------
@app.route("/log_listen", methods=["GET"])
@login_required
def log_listen_page():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT t.track_id,
               t.title,
               COALESCE(GROUP_CONCAT(DISTINCT a.name SEPARATOR ', '), 'Unknown Artist') AS artists
        FROM music_track t
        LEFT JOIN music_track_artist mta ON t.track_id = mta.track_id
        LEFT JOIN music_artist a ON mta.artist_id = a.artist_id
        GROUP BY t.track_id, t.title
        ORDER BY t.title ASC
        LIMIT 200
    """)
    tracks = cursor.fetchall()

    cursor.close()
    return render_template("log_listen.html", tracks=tracks)


@app.route("/listen", methods=["POST"])
def listen():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO core_listen_event (user_id, track_id, played_at)
        VALUES (%s, %s, NOW())
    """, (session["user_id"], request.form.get("track_id")))

    db.commit()
    cursor.close()
    return redirect("/log_listen")


# ------------------------------------
# PLAYLIST ROUTES
# ------------------------------------
@app.route("/playlist/add_track", methods=["GET"])
@login_required
def add_track_form():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT playlist_id, name FROM core_playlist WHERE owner_user_id=%s",
                   (session["user_id"],))
    playlists = cursor.fetchall()

    cursor.close()
    return render_template("add_track_to_playlist.html", playlists=playlists)


@app.route("/playlist/add_track", methods=["POST"])
@login_required
def add_track_submit():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    playlist_id = request.form.get("playlist_id")
    track_id = request.form.get("track_id")

    cursor.execute("""
        SELECT COALESCE(MAX(position), 0) + 1 AS next_pos
        FROM core_playlist_track WHERE playlist_id=%s
    """, (playlist_id,))
    next_pos = cursor.fetchone()["next_pos"]

    # Prevent duplicate
    cursor.execute("""
        SELECT 1 FROM core_playlist_track
        WHERE playlist_id = %s AND track_id = %s
    """, (playlist_id, track_id))

    if cursor.fetchone():
        cursor.close()
        return f"<h3>⚠ Track already in playlist!</h3><a href='/playlists'>Back</a>"

    cursor.execute("""
        INSERT INTO core_playlist_track (playlist_id, track_id, position)
        VALUES (%s, %s, %s)
    """, (playlist_id, track_id, next_pos))

    db.commit()
    cursor.close()
    return redirect(f"/playlist/{playlist_id}")


# ------------------------------------
# PLAYLIST VIEW
# ------------------------------------
@app.route("/playlists")
@login_required
def playlists():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT playlist_id, name, created_at
        FROM core_playlist
        WHERE owner_user_id=%s
        ORDER BY created_at DESC
    """, (session["user_id"],))
    playlists = cursor.fetchall()
    cursor.close()

    return render_template("playlists.html", playlists=playlists)


@app.route("/playlist/<int:playlist_id>")
@login_required
def playlist_detail(playlist_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT name FROM core_playlist WHERE playlist_id=%s", (playlist_id,))
    playlist = cursor.fetchone()

    cursor.execute("""
        SELECT 
            pt.position,
            t.track_id,
            t.title,
            GROUP_CONCAT(a.name SEPARATOR ', ') AS artists
        FROM core_playlist_track pt
        JOIN music_track t ON pt.track_id = t.track_id
        JOIN music_track_artist mta ON t.track_id = mta.track_id
        JOIN music_artist a ON mta.artist_id = a.artist_id
        WHERE pt.playlist_id = %s
        GROUP BY pt.position, t.track_id, t.title
        ORDER BY pt.position
    """, (playlist_id,))
    tracks = cursor.fetchall()

    cursor.close()
    
    return render_template("playlist_detail.html",
                           playlist=playlist,
                           tracks=tracks,
                           playlist_id=playlist_id)

    
@app.route("/playlist", methods=["GET"])
@login_required
def playlist_form():
    return render_template("create_playlist.html")
    

@app.route("/playlist", methods=["POST"])
@login_required
def playlist_submit():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    user_id = session["user_id"]
    name = request.form.get("name")

    if not name:
        cursor.close()
        return "Playlist name required!"

    cursor.execute("""
        INSERT INTO core_playlist (owner_user_id, name, created_at)
        VALUES (%s, %s, NOW())
    """, (user_id, name))

    db.commit()
    cursor.close()

    return redirect("/playlists")
    
# ------------------------------------
# DASHBOARD
# ------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Stats summary
    cursor.execute("""
        SELECT 
            COUNT(*) AS total_listens,
            COUNT(DISTINCT track_id) AS unique_tracks,
            COUNT(DISTINCT DATE(played_at)) AS active_days
        FROM core_listen_event
        WHERE user_id = %s
    """, (user_id,))
    summary = cursor.fetchone() or {}

    # Top 5 most-listened artists
    cursor.execute("""
        SELECT a.name AS artist_name, COUNT(*) AS listens
        FROM core_listen_event le
        JOIN music_track_artist mta ON le.track_id = mta.track_id
        JOIN music_artist a ON mta.artist_id = a.artist_id
        WHERE le.user_id = %s
        GROUP BY a.artist_id
        ORDER BY listens DESC
        LIMIT 5
    """, (user_id,))
    top_artists = cursor.fetchall()

    # Listening trend (last 7 days)
    cursor.execute("""
        SELECT DATE(played_at) AS day, COUNT(*) AS listens
        FROM core_listen_event
        WHERE user_id = %s
        GROUP BY day
        ORDER BY day DESC
        LIMIT 7
    """, (user_id,))
    trend = cursor.fetchall()[::-1]  # reverse for chronological display

    # Profile info
    cursor.execute("""
        SELECT display_name, avatar_url
        FROM core_user_profile
        WHERE user_id = %s
    """, (user_id,))
    user_profile = cursor.fetchone()

    cursor.close()

    return render_template(
        "dashboard.html",
        summary=summary,
        top_artists=top_artists,
        trend=trend,
        user=user_profile
    )

    
# ------------------------------------
# RECOMMENDATIONS
# ------------------------------------
@app.route("/recs")
@login_required
def recs_api():
    user_id = session["user_id"]
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT r.track_id,
               t.title,
               GROUP_CONCAT(a.name SEPARATOR ', ') AS artists,
               t.popularity
        FROM v_recommendation_explorer r
        JOIN music_track t ON r.track_id = t.track_id
        JOIN music_track_artist mta ON t.track_id = mta.track_id
        JOIN music_artist a ON mta.artist_id = a.artist_id
        WHERE r.user_id = %s
        GROUP BY r.track_id
        ORDER BY t.popularity DESC
        LIMIT 20
    """, (user_id,))

    results = cursor.fetchall()
    cursor.close()
    return jsonify(results)


@app.route("/recs_ui")
@login_required
def recs_ui():
    user_id = session["user_id"]
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT r.track_id,
               t.title,
               (SELECT name FROM music_artist a
                JOIN music_track_artist mta ON a.artist_id = mta.artist_id
                WHERE mta.track_id = t.track_id LIMIT 1) AS artist_name
        FROM v_recommendation_explorer r
        JOIN music_track t ON r.track_id = t.track_id
        WHERE r.user_id = %s
        ORDER BY t.popularity DESC
        LIMIT 20
    """, (user_id,))

    recs = cursor.fetchall()
    cursor.close()
    return render_template("recs_ui.html", recs=recs)
    
    
# ------------------------------------
# GLOBAL INSIGHTS
# ------------------------------------
@app.route("/global/<int:user_id>")
@login_required
def global_compare(user_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Find user's country + region
    cursor.execute("""
        SELECT p.country_code, c.name AS country_name, c.region
        FROM core_user_profile p
        JOIN ref_country c ON p.country_code = c.country_code
        WHERE p.user_id = %s
    """, (user_id,))
    country = cursor.fetchone()

    if not country:
        cursor.close()
        return render_template("global_insights.html", info=None)

    code = country["country_code"]

    # Get latest GDP + internet usage
    cursor.execute("""
        SELECT i.indicator_code, b.value
        FROM bg_country_indicator b
        JOIN ref_indicator i ON b.indicator_code = i.indicator_code
        WHERE b.country_code = %s
          AND b.indicator_code IN ("NY.GDP.PCAP.KD", "IT.NET.USER.ZS")
        ORDER BY b.year DESC
        LIMIT 2
    """, (code,))
    rows = cursor.fetchall()
    cursor.close()

    insights = {
        "country_name": country["country_name"],
        "region": country["region"],
        "gdp_per_capita": None,
        "internet_usage": None
    }

    for r in rows:
        if r["indicator_code"] == "NY.GDP.PCAP.KD":
            insights["gdp_per_capita"] = r["value"]
        elif r["indicator_code"] == "IT.NET.USER.ZS":
            insights["internet_usage"] = r["value"]

    return render_template("global_insights.html", info=insights)
    
# ==========================================
#   edit profile
# ==========================================
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session["user_id"]
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        display_name = request.form.get("display_name")
        country_code = request.form.get("country_code")
        birth_year = request.form.get("birth_year") or None
        avatar_url = request.form.get("avatar_url") or None

        cursor.execute("""
            UPDATE core_user_profile
            SET display_name=%s, country_code=%s, birth_year=%s, avatar_url=%s
            WHERE user_id=%s
        """, (display_name, country_code, birth_year, avatar_url, user_id))
        db.commit()

        cursor.close()
        return redirect("/profile")

    # GET — Load form with existing profile values
    cursor.execute("""
        SELECT display_name, country_code, birth_year, avatar_url
        FROM core_user_profile WHERE user_id=%s
    """, (user_id,))
    profile = cursor.fetchone()

    # Load country dropdown list
    cursor.execute("SELECT country_code, name FROM ref_country ORDER BY name")
    countries = cursor.fetchall()

    cursor.close()
    return render_template("profile.html",
                           profile=profile,
                           countries=countries)

    
    
# ==========================================
#   comunity insights (Last.fm)
# ==========================================
@app.route("/community_insights")
@login_required
def community_insights():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            a.name AS artist,
            COUNT(*) AS plays
        FROM map_lastfm_track m
        JOIN music_track t ON m.track_id = t.track_id
        JOIN music_track_artist mta ON t.track_id = mta.track_id
        JOIN music_artist a ON mta.artist_id = a.artist_id
        GROUP BY a.artist_id
        ORDER BY plays DESC
        LIMIT 10
    """)
    top_community_artists = cursor.fetchall()

    cursor.close()

    return render_template("community_insights.html",
                           artists=top_community_artists)


# ------------------------------------
# HOME + LOGOUT
# ------------------------------------
@app.route("/")
def home():
    user = None
    if "user_id" in session:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT display_name, avatar_url
            FROM core_user_profile 
            WHERE user_id = %s
        """, (session["user_id"],))
        user = cursor.fetchone()
        cursor.close()

    return render_template("home.html", user=user)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ------------------------------------
# START
# ------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5001)


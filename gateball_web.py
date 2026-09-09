import os
import re
from datetime import date, datetime
from functools import wraps
from urllib.parse import urljoin
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory

# ============================================================
# GATEBALL LOVERS - FLASK APP
# ============================================================

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "gateball-lovers-change-this-key")

SUPABASE_URL = os.getenv(
    "SUPABASE_URL",
    "https://cxogmmfohegychxwadqv.supabase.co"
).rstrip("/")

SUPABASE_PUBLISHABLE_KEY = os.getenv(
    "SUPABASE_PUBLISHABLE_KEY",
    "sb_publishable_V-ID9zcQ7PrdOfQSyWNq_A_Hr5WKtr1"
)

ADMIN_ID = "e4cfeb88-546a-4ec8-ab29-27a22a0fc6f5"
ADMIN_EMAIL = "biswa.r.mishra@gmail.com"

WGU_NEWS_URL = "https://gateball.or.jp/wgu/news/"
JGU_NEWS_URL = "https://gateball.jp/news/"

COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola",
    "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria",
    "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados",
    "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia",
    "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria",
    "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon",
    "Canada", "Central African Republic", "Chad", "Chile", "China",
    "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba",
    "Cyprus", "Czechia", "Democratic Republic of the Congo", "Denmark",
    "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt",
    "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini",
    "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia",
    "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala",
    "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary",
    "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel",
    "Italy", "Ivory Coast", "Jamaica", "Japan", "Jordan", "Kazakhstan",
    "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia",
    "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania",
    "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali",
    "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico",
    "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco",
    "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands",
    "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia",
    "Norway", "Oman", "Pakistan", "Palau", "Palestine", "Panama",
    "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland",
    "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis",
    "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino",
    "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles",
    "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
    "Somalia", "South Africa", "South Korea", "South Sudan", "Spain",
    "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria",
    "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo",
    "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan",
    "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom",
    "United States", "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City",
    "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]


# ============================================================
# SUPABASE REST HELPERS
# ============================================================

def supabase_headers(access_token=None):
    token = access_token or session.get("access_token") or SUPABASE_PUBLISHABLE_KEY
    return {
        "apikey": SUPABASE_PUBLISHABLE_KEY,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def supabase_request(method, path, access_token=None, **kwargs):
    url = SUPABASE_URL + path
    headers = supabase_headers(access_token)

    response = requests.request(
        method,
        url,
        headers=headers,
        timeout=20,
        **kwargs
    )

    if response.status_code >= 400:
        try:
            detail = response.json()
        except Exception:
            detail = response.text

        raise RuntimeError(
            f"Supabase error {response.status_code}: {detail}"
        )

    if not response.text:
        return None

    try:
        return response.json()
    except Exception:
        return response.text


def supabase_auth_password(email, password):
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"

    response = requests.post(
        url,
        headers={
            "apikey": SUPABASE_PUBLISHABLE_KEY,
            "Content-Type": "application/json",
        },
        json={
            "email": email,
            "password": password,
        },
        timeout=20,
    )

    try:
        data = response.json()
    except Exception:
        data = {}

    if response.status_code >= 400:
        message = (
            data.get("error_description")
            or data.get("msg")
            or data.get("message")
            or "Invalid email or password."
        )
        raise RuntimeError(message)

    return data


def supabase_signup(email, password, metadata):
    url = f"{SUPABASE_URL}/auth/v1/signup"

    response = requests.post(
        url,
        headers={
            "apikey": SUPABASE_PUBLISHABLE_KEY,
            "Content-Type": "application/json",
        },
        json={
            "email": email,
            "password": password,
            "data": metadata,
        },
        timeout=20,
    )

    try:
        data = response.json()
    except Exception:
        data = {}

    if response.status_code >= 400:
        message = (
            data.get("msg")
            or data.get("message")
            or data.get("error_description")
            or "Account creation failed."
        )
        raise RuntimeError(message)

    return data


# ============================================================
# USER / SESSION HELPERS
# ============================================================

def load_profile(user_id=None, access_token=None):
    user_id = user_id or session.get("user_id")
    if not user_id:
        return None

    rows = supabase_request(
        "GET",
        "/rest/v1/profiles",
        access_token=access_token,
        params={
            "select": "id,full_name,email,role,country,phone,photo_url",
            "id": f"eq.{user_id}",
            "limit": "1",
        },
    )

    return rows[0] if rows else None


def current_profile():
    if not session.get("user_id"):
        return None

    try:
        return load_profile()
    except Exception:
        return None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def manager_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        profile = current_profile()

        if not profile:
            session.clear()
            return redirect(url_for("login"))

        if profile.get("role") not in ("Admin", "Organizer"):
            flash("Only Admin or Organizer can manage tournaments.")
            return redirect(url_for("tournaments"))

        return view(*args, **kwargs)

    return wrapped


def can_manage_tournament(tournament, profile):
    if not profile:
        return False

    role = profile.get("role")
    if role == "Admin":
        return True

    return (
        role == "Organizer"
        and str(tournament.get("organizer_id") or "")
        == str(profile.get("id") or "")
    )


@app.context_processor
def inject_user():
    profile = current_profile()
    return {
        "current_user": profile,
        "logged_in": bool(session.get("user_id")),
    }


# ============================================================
# GENERAL HELPERS
# ============================================================

def valid_email(value):
    return bool(
        re.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            value or ""
        )
    )


def calculated_status(start_date, end_date):
    try:
        start = datetime.strptime(str(start_date), "%Y-%m-%d").date()
        end = datetime.strptime(str(end_date), "%Y-%m-%d").date()
        today = date.today()

        if today < start:
            return "Upcoming"
        if today > end:
            return "Finished"
        return "Ongoing"
    except Exception:
        return "Upcoming"


def format_date(value):
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d %B %Y")
    except Exception:
        return value or ""


def normalize_tournament(row):
    row = dict(row)

    start = row.get("start_date", "")
    end = row.get("end_date", "")

    row["display_start"] = format_date(start)
    row["display_end"] = format_date(end)

    # The old Python app calculated status from the dates.
    row["calculated_status"] = calculated_status(start, end)

    # Keep database status synchronized when possible.
    row["status"] = row["calculated_status"]

    return row


def load_tournaments(include_results=True):
    rows = supabase_request(
        "GET",
        "/rest/v1/tournaments",
        params={
            "select": (
                "id,name,venue,event_type,start_date,end_date,"
                "organizer_id,organizer_name,status,created_at,country,"
                "description,updated_at,live_link"
            ),
            "order": "start_date.asc",
        },
    ) or []

    tournaments = [normalize_tournament(row) for row in rows]

    if not include_results or not tournaments:
        return tournaments

    ids = [str(t["id"]) for t in tournaments]

    result_rows = supabase_request(
        "GET",
        "/rest/v1/tournament_results",
        params={
            "select": (
                "id,tournament_id,position,team_name,score,"
                "created_at,category"
            ),
            "tournament_id": "in.(" + ",".join(ids) + ")",
            "order": "position.asc",
        },
    ) or []

    results_by_tournament = {}

    for item in result_rows:
        tid = item.get("tournament_id")
        category = item.get("category") or "Classic"

        results_by_tournament.setdefault(
            tid,
            {}
        ).setdefault(
            category,
            []
        ).append(item)

    for tournament in tournaments:
        tournament["results"] = results_by_tournament.get(
            tournament["id"],
            {}
        )

    return tournaments


def load_members():
    rows = supabase_request(
        "GET",
        "/rest/v1/profiles",
        params={
            "select": "id,full_name,email,role,country,phone,photo_url",
            "order": "full_name.asc",
        },
    ) or []

    return rows


def joined_player_ids(tournament_id):
    rows = supabase_request(
        "GET",
        "/rest/v1/tournament_players",
        params={
            "select": "player_id",
            "tournament_id": f"eq.{tournament_id}",
        },
    ) or []

    return {
        str(row.get("player_id"))
        for row in rows
        if row.get("player_id")
    }


def tournament_counts():
    rows = supabase_request(
        "GET",
        "/rest/v1/tournaments",
        params={
            "select": "id,start_date,end_date,live_link",
            "order": "start_date.asc",
        },
    ) or []

    today = date.today()

    upcoming = 0
    ongoing = 0
    live = 0

    for row in rows:
        status = calculated_status(
            row.get("start_date"),
            row.get("end_date")
        )

        if status == "Upcoming":
            upcoming += 1
        elif status == "Ongoing":
            ongoing += 1

        if row.get("live_link"):
            live += 1

    return {
        "total": len(rows),
        "upcoming": upcoming,
        "ongoing": ongoing,
        "live": live,
    }


# ============================================================
# GATEBALL NEWS
# ============================================================

class NewsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.href = ""
        self.text_parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            attrs = dict(attrs)
            self.href = attrs.get("href", "")
            self.text_parts = []

    def handle_data(self, data):
        if self.href:
            text = data.strip()
            if text:
                self.text_parts.append(text)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.href:
            text = " ".join(self.text_parts).strip()
            if text:
                self.links.append((text, self.href))

            self.href = ""
            self.text_parts = []


WGU_NEWS_URL = "https://gateball.or.jp/wgu/news/"
JGU_NEWS_URL = "https://gateball.jp/news/"
GOOGLE_GATEBALL_RSS = (
    "https://news.google.com/rss/search"
    "?q=gateball&hl=en-US&gl=US&ceid=US:en"
)


def fetch_news(url, source, limit=8):
    response = requests.get(
        url,
        headers={
            "User-Agent": "GateballLovers/1.0"
        },
        timeout=15,
    )
    response.raise_for_status()

    parser = NewsParser()
    parser.feed(response.text)

    items = []
    seen = set()

    for title, href in parser.links:
        title = " ".join(title.split())

        if len(title) < 8:
            continue

        if title.lower() in {"top", "news", "open", "more"}:
            continue

        full_url = urljoin(url, href)
        key = (title.lower(), full_url)

        if key in seen:
            continue

        seen.add(key)

        items.append({
            "title": title,
            "url": full_url,
            "source": source,
        })

        if len(items) >= limit:
            break

    return items


def fetch_google_gateball_news(limit=8):
    response = requests.get(
        GOOGLE_GATEBALL_RSS,
        headers={
            "User-Agent": "GateballLovers/1.0"
        },
        timeout=15,
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)
    items = []

    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()

        if not title or not link:
            continue

        items.append({
            "title": title,
            "url": link,
            "source": "Worldwide Gateball News",
        })

        if len(items) >= limit:
            break

    return items


def load_gateball_news():
    all_items = []

    # Worldwide search first.
    try:
        all_items.extend(
            fetch_google_gateball_news(8)
        )
    except Exception as exc:
        print("Worldwide Gateball news error:", repr(exc))

    # Then official international sources.
    for url, source in (
        (WGU_NEWS_URL, "WGU - World Gateball Union"),
        (JGU_NEWS_URL, "JGU - Japan Gateball Union"),
    ):
        try:
            all_items.extend(
                fetch_news(url, source, 6)
            )
        except Exception as exc:
            print("Official Gateball news error:", source, repr(exc))

    unique = []
    seen_titles = set()

    for item in all_items:
        key = item["title"].lower()

        if key in seen_titles:
            continue

        seen_titles.add(key)
        unique.append(item)

    return unique[:30]


# ============================================================
# LOGIN / SIGN UP / LOGOUT
# ============================================================

@app.route("/manifest.json")
def manifest():
    return send_from_directory(os.path.dirname(__file__), "manifest.json", mimetype="application/manifest+json")


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not valid_email(email):
            flash("Please enter a valid email address.")
            return render_template("login.html")

        if not password:
            flash("Please enter your password.")
            return render_template("login.html")

        try:
            auth = supabase_auth_password(
                email,
                password
            )

            access_token = auth.get("access_token")
            user = auth.get("user") or {}

            user_id = user.get("id")

            if not access_token or not user_id:
                raise RuntimeError("Login failed.")

            session.clear()
            session["access_token"] = access_token
            session["refresh_token"] = auth.get("refresh_token", "")
            session["user_id"] = user_id
            session["user_email"] = user.get("email", email)

            profile = load_profile(
                user_id,
                access_token
            )

            if not profile:
                session.clear()
                flash(
                    "Login worked, but your Gateball profile could not be loaded."
                )
                return render_template("login.html")

            session["role"] = profile.get("role", "Player")
            session["user_name"] = profile.get(
                "full_name",
                "Gateball User"
            )

            return redirect(url_for("dashboard"))

        except Exception as exc:
            print("Login error:", repr(exc))
            message = str(exc)

            if "Email not confirmed" in message:
                message = "Please confirm your email before logging in."
            elif "Invalid login credentials" in message:
                message = "Invalid email or password."

            flash(message)

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        country = request.form.get("country", "").strip()
        phone = request.form.get("phone", "").strip()
        role = request.form.get("role", "Player").strip()

        if len(name) < 2:
            flash("Please enter your full name.")
            return render_template(
                "signup.html",
                countries=COUNTRIES
            )

        if not valid_email(email):
            flash("Please enter a valid email address.")
            return render_template(
                "signup.html",
                countries=COUNTRIES
            )

        if len(phone) < 5:
            flash("Please enter a valid contact number.")
            return render_template(
                "signup.html",
                countries=COUNTRIES
            )

        if not country:
            flash("Please select your country.")
            return render_template(
                "signup.html",
                countries=COUNTRIES
            )

        if len(password) < 8:
            flash("Password must contain at least 8 characters.")
            return render_template(
                "signup.html",
                countries=COUNTRIES
            )

        if role not in ("Player", "Organizer"):
            role = "Player"

        try:
            result = supabase_signup(
                email,
                password,
                {
                    "full_name": name,
                    "role": role,
                    "country": country,
                    "phone": phone,
                }
            )

            if result.get("session"):
                flash(
                    "Account created successfully. You can now log in."
                )
            else:
                flash(
                    "Account created! Check your email to confirm it, then log in."
                )

            return redirect(url_for("login"))

        except Exception as exc:
            print("Signup error:", repr(exc))
            message = str(exc)

            if "already registered" in message.lower():
                message = "This email is already registered. Please log in."

            flash(message)

    return render_template(
        "signup.html",
        countries=COUNTRIES
    )


@app.route("/logout", methods=["GET", "POST"])
def logout():
    token = session.get("access_token")

    if token:
        try:
            supabase_request(
                "POST",
                "/auth/v1/logout",
                access_token=token
            )
        except Exception:
            pass

    session.clear()
    return redirect(url_for("login"))


# ============================================================
# MESSAGE BOARD MANAGEMENT
# ============================================================

def message_manager_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        profile = current_profile()

        if not profile:
            session.clear()
            return redirect(url_for("login"))

        if profile.get("role") not in ("Admin", "Organizer"):
            flash("Only Admin or Organizer can manage Message Board messages.")
            return redirect(url_for("dashboard"))

        return view(*args, **kwargs)

    return wrapped


def can_manage_message(message, profile):
    if not profile:
        return False

    role = profile.get("role")
    if role == "Admin":
        return True

    return (
        role == "Organizer"
        and str(message.get("author_id") or "")
        == str(profile.get("id") or "")
    )


def load_message(message_id):
    rows = supabase_request(
        "GET",
        "/rest/v1/community_messages",
        params={
            "select": "id,author_id,title,message,is_active,created_at",
            "id": f"eq.{message_id}",
            "limit": "1",
        },
    ) or []
    return rows[0] if rows else None


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():
    profile = current_profile()

    if not profile:
        session.clear()
        return redirect(url_for("login"))

    # Each dashboard section loads independently.
    # One failed internet source must not hide the other sections.
    members = []
    tournaments = []
    news = []
    message_board = []

    try:
        members = load_members()
    except Exception as exc:
        print("Dashboard profiles error:", repr(exc))

    try:
        tournaments = load_tournaments(include_results=False)
    except Exception as exc:
        print("Dashboard tournaments error:", repr(exc))

    try:
        news = load_gateball_news()
    except Exception as exc:
        print("Dashboard news error:", repr(exc))

    try:
        message_board = load_message_board()
    except Exception as exc:
        print("Dashboard message board error:", repr(exc))

    players_count = sum(
        1 for m in members
        if str(m.get("role", "")).strip().lower() == "player"
    )

    organizers_count = sum(
        1 for m in members
        if str(m.get("role", "")).strip().lower() == "organizer"
    )

    upcoming_tournaments = sorted(
        [
            t for t in tournaments
            if t.get("calculated_status") == "Upcoming"
        ],
        key=lambda x: x.get("start_date") or "9999-12-31"
    )[:5]

    # Match the original Gateball Lovers behavior:
    # a live match is an Ongoing tournament that has a live link.
    live_matches = [
        t for t in tournaments
        if t.get("calculated_status") == "Ongoing"
        and str(t.get("live_link") or "").strip()
    ]

    # Keep the count consistent with the list.
    live_matches_count = len(live_matches)

    return render_template(
        "dashboard.html",
        user_name=profile.get("full_name") or "Gateball User",
        user_role=profile.get("role") or "Player",
        players_count=players_count,
        organizers_count=organizers_count,
        tournaments_count=len(tournaments),
        live_matches_count=live_matches_count,
        upcoming_tournaments=upcoming_tournaments,
        live_matches=live_matches,
        news=news,
        message_board=message_board,
        can_manage_messages=profile.get("role") in ("Admin", "Organizer"),
        current_profile_id=profile.get("id"),
    )


# ============================================================
# TOURNAMENTS
# ============================================================

@app.route("/news")
@login_required
def news_page():
    try:
        news = load_gateball_news()
    except Exception as exc:
        print("News page error:", repr(exc))
        news = []

    return render_template("news.html", news=news)


@app.route("/tournaments")
@login_required
def tournaments():
    requested_status = request.args.get("status", "Upcoming")

    if requested_status not in ("Upcoming", "Ongoing", "Finished"):
        requested_status = "Upcoming"

    try:
        all_tournaments = load_tournaments()
        selected = [
            t for t in all_tournaments
            if t.get("calculated_status") == requested_status
        ]

        profile = current_profile()
        user_id = session.get("user_id")

        for tournament in selected:
            tournament["joined"] = (
                user_id in joined_player_ids(tournament["id"])
                if user_id else False
            )
            tournament["can_manage"] = can_manage_tournament(tournament, profile)

        return render_template(
            "tournaments.html",
            current_status=requested_status,
            can_manage=bool(profile and profile.get("role") in ("Admin", "Organizer")),
            tournaments=selected,
        )

    except Exception as exc:
        print("Tournament page error:", repr(exc))
        return render_template(
            "tournaments.html",
            current_status=requested_status,
            can_manage=False,
            tournaments=[],
        )


@app.route("/tournaments/<int:tournament_id>/join", methods=["GET", "POST"])
@login_required
def join_tournament(tournament_id):
    profile = current_profile()

    if not profile:
        return redirect(url_for("login"))

    if profile.get("role") != "Player":
        flash("Only Players can join tournaments.")
        return redirect(url_for("tournaments"))

    try:
        tournament_rows = supabase_request(
            "GET",
            "/rest/v1/tournaments",
            params={
                "select": "id,start_date,end_date,status",
                "id": f"eq.{tournament_id}",
                "limit": "1",
            },
        ) or []

        if not tournament_rows:
            flash("Tournament not found.")
            return redirect(url_for("tournaments"))

        tournament = tournament_rows[0]
        status = calculated_status(
            tournament.get("start_date"),
            tournament.get("end_date")
        )

        if status != "Upcoming":
            flash("You can join only an Upcoming tournament.")
            return redirect(url_for("tournaments"))

        existing = joined_player_ids(tournament_id)

        if str(profile["id"]) in existing:
            flash("You have already joined this tournament.")
            return redirect(url_for("tournaments"))

        supabase_request(
            "POST",
            "/rest/v1/tournament_players",
            json={
                "tournament_id": tournament_id,
                "player_id": profile["id"],
            },
        )

        flash("✓ Tournament joined successfully.")

    except Exception as exc:
        print("Join tournament error:", repr(exc))

        if "duplicate" in str(exc).lower():
            flash("You have already joined this tournament.")
        else:
            flash("Could not join the tournament.")

    return redirect(url_for("tournaments"))


# ============================================================
# TOURNAMENT ADD / EDIT / RESULT
# These use simple server-rendered forms so the main app
# remains Python/Flask-first.
# ============================================================

FORM_HTML = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }} - Gateball Lovers</title>
<style>
body{font-family:Arial;background:#fff8e8;margin:0;padding:20px}
.wrap{max-width:430px;margin:auto}
.card{background:white;border-radius:18px;padding:20px;box-shadow:0 5px 18px #0001}
h1{color:#d88900;font-size:23px}
label{display:block;margin-top:12px;font-weight:bold;color:#555}
input,select,textarea{width:100%;padding:12px;margin-top:6px;border:1px solid #ddd;border-radius:10px;box-sizing:border-box}
button,.btn{display:block;width:100%;padding:13px;margin-top:16px;border:0;border-radius:11px;background:#f4a300;color:white;font-weight:bold;text-decoration:none;text-align:center;box-sizing:border-box}
.back{background:#777}
.msg{margin-top:10px;color:#c62828}
</style>
</head>
<body>
<div class="wrap">
<div class="card">
<h1>{{ title }}</h1>
{% with messages = get_flashed_messages() %}
{% if messages %}
<div class="msg">{% for m in messages %}{{ m }}<br>{% endfor %}</div>
{% endif %}
{% endwith %}
<form method="post">
{{ form_html|safe }}
<button type="submit">SAVE</button>
<a class="btn back" href="{{ url_for('tournaments') }}">BACK TO TOURNAMENTS</a>
</form>
</div>
</div>
</body>
</html>
"""


def tournament_form_html(t=None):
    t = t or {}

    country_options = "".join(
        f'<option value="{country}">' for country in COUNTRIES
    )

    return f"""
<label>Tournament Name</label>
<input name="name" required value="{t.get('name','')}">

<label>Organizer Name</label>
<input name="organizer_name" required value="{t.get('organizer_name') or ''}">

<label>Venue</label>
<input name="venue" required value="{t.get('venue','')}">

<label>Country</label>
<input name="country" list="country-options" autocomplete="off" required value="{t.get('country','')}" placeholder="Type to search country">
<datalist id="country-options">{country_options}</datalist>

<label>Event Type</label>
<select name="event_type" required>
<option {'selected' if t.get('event_type') == 'Classic' else ''}>Classic</option>
<option {'selected' if t.get('event_type') == 'Triple' else ''}>Triple</option>
<option {'selected' if t.get('event_type') == 'Double' else ''}>Double</option>
</select>

<label>Start Date</label>
<input type="date" name="start_date" required value="{t.get('start_date','')}">

<label>End Date</label>
<input type="date" name="end_date" required value="{t.get('end_date','')}">

<label>Description</label>
<textarea name="description">{t.get('description','')}</textarea>
"""


@app.route("/tournaments/add", methods=["GET", "POST"])
@manager_required
def add_tournament():
    if request.method == "POST":
        data = {
            "name": request.form.get("name", "").strip(),
            "venue": request.form.get("venue", "").strip(),
            "country": request.form.get("country", "").strip(),
            "event_type": request.form.get("event_type", "Classic"),
            "start_date": request.form.get("start_date", ""),
            "end_date": request.form.get("end_date", ""),
            "organizer_id": session.get("user_id"),
            "organizer_name": request.form.get("organizer_name", "").strip(),
            "description": request.form.get("description", "").strip(),
            "live_link": "",
        }

        if data["event_type"] not in ("Classic", "Triple", "Double"):
            flash("Please select a valid Event Type.")
            return redirect(url_for("add_tournament"))

        if not data["name"] or not data["venue"] or not data["country"] or not data["organizer_name"]:
            flash("Please complete all required fields.")
            return redirect(url_for("add_tournament"))

        if data["country"] not in COUNTRIES:
            flash("Please select a country from the country list.")
            return redirect(url_for("add_tournament"))

        try:
            start = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
            end = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
            if end < start:
                flash("End Date cannot be before Start Date.")
                return redirect(url_for("add_tournament"))

            data["status"] = calculated_status(data["start_date"], data["end_date"])
            supabase_request("POST", "/rest/v1/tournaments", json=data)
            flash("✓ Tournament saved successfully.")
            return redirect(url_for("tournaments", status="Upcoming"))

        except Exception as exc:
            print("Add tournament error:", repr(exc))
            flash("Save failed: " + str(exc)[:180])

    return render_template("simple_form.html", title="Add Tournament", form_html=tournament_form_html())


@app.route("/tournaments/<int:tournament_id>/edit", methods=["GET", "POST"])
@manager_required
def edit_tournament(tournament_id):
    rows = supabase_request(
        "GET", "/rest/v1/tournaments",
        params={
            "select": "id,name,venue,country,event_type,start_date,end_date,organizer_id,organizer_name,description,live_link",
            "id": f"eq.{tournament_id}", "limit": "1",
        },
    ) or []

    if not rows:
        flash("Tournament not found.")
        return redirect(url_for("tournaments", status="Upcoming"))

    tournament = rows[0]
    profile = current_profile()
    if not can_manage_tournament(tournament, profile):
        flash("Only the Admin or the Organizer who created this tournament can edit it.")
        return redirect(url_for("tournaments", status="Upcoming"))

    if request.method == "POST":
        data = {
            "name": request.form.get("name", "").strip(),
            "venue": request.form.get("venue", "").strip(),
            "country": request.form.get("country", "").strip(),
            "event_type": request.form.get("event_type", "Classic"),
            "start_date": request.form.get("start_date", ""),
            "end_date": request.form.get("end_date", ""),
            "organizer_name": request.form.get("organizer_name", "").strip(),
            "description": request.form.get("description", "").strip(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        try:
            datetime.strptime(data["start_date"], "%Y-%m-%d")
            datetime.strptime(data["end_date"], "%Y-%m-%d")
            if data["end_date"] < data["start_date"]:
                flash("End Date cannot be before Start Date.")
                return redirect(url_for("edit_tournament", tournament_id=tournament_id))
            if data["country"] not in COUNTRIES:
                flash("Please select a country from the country list.")
                return redirect(url_for("edit_tournament", tournament_id=tournament_id))

            data["status"] = calculated_status(data["start_date"], data["end_date"])
            supabase_request("PATCH", "/rest/v1/tournaments", params={"id": f"eq.{tournament_id}"}, json=data)
            flash("✓ Tournament updated successfully.")
            return redirect(url_for("tournaments", status="Upcoming"))
        except Exception as exc:
            print("Edit tournament error:", repr(exc))
            flash("Could not update tournament: " + str(exc)[:160])

    return render_template("simple_form.html", title="Edit Tournament", form_html=tournament_form_html(tournament))


@app.route("/tournaments/<int:tournament_id>/delete", methods=["POST"])
@manager_required
def delete_tournament(tournament_id):
    try:
        rows = supabase_request(
            "GET", "/rest/v1/tournaments",
            params={"select": "id,organizer_id", "id": f"eq.{tournament_id}", "limit": "1"},
        ) or []
        profile = current_profile()
        if not rows or not can_manage_tournament(rows[0], profile):
            flash("You do not have permission to delete this tournament.")
            return redirect(url_for("tournaments", status="Upcoming"))

        supabase_request("DELETE", "/rest/v1/tournaments", params={"id": f"eq.{tournament_id}"})
        flash("✓ Tournament deleted successfully.")
    except Exception as exc:
        print("Delete tournament error:", repr(exc))
        flash("Could not delete tournament: " + str(exc)[:160])

    return redirect(url_for("tournaments", status="Upcoming"))


@app.route("/tournaments/<int:tournament_id>/live-link", methods=["POST"])
@manager_required
def save_live_link(tournament_id):
    try:
        rows = supabase_request(
            "GET", "/rest/v1/tournaments",
            params={"select": "id,start_date,end_date,organizer_id", "id": f"eq.{tournament_id}", "limit": "1"},
        ) or []
        if not rows:
            flash("Tournament not found.")
            return redirect(url_for("tournaments", status="Ongoing"))

        tournament = rows[0]
        profile = current_profile()
        if not can_manage_tournament(tournament, profile):
            flash("You do not have permission to manage this tournament.")
            return redirect(url_for("tournaments", status="Ongoing"))

        if calculated_status(tournament.get("start_date"), tournament.get("end_date")) != "Ongoing":
            flash("Live social media links can be managed only for Ongoing tournaments.")
            return redirect(url_for("tournaments", status="Ongoing"))

        link = request.form.get("live_link", "").strip()
        if link and not re.match(r"^https?://", link, re.I):
            flash("Please enter a valid social media URL starting with http:// or https://")
            return redirect(url_for("tournaments", status="Ongoing"))

        supabase_request(
            "PATCH", "/rest/v1/tournaments",
            params={"id": f"eq.{tournament_id}"},
            json={"live_link": link, "updated_at": datetime.utcnow().isoformat()},
        )
        flash("✓ Live social media link saved.")
    except Exception as exc:
        print("Live link error:", repr(exc))
        flash("Could not save live social media link: " + str(exc)[:160])

    return redirect(url_for("tournaments", status="Ongoing"))


@app.route("/tournaments/results/add", methods=["GET", "POST"])
@manager_required
def add_result():
    tournaments_data = [
        t for t in load_tournaments(include_results=True)
        if t.get("calculated_status") == "Finished"
    ]

    requested_id = request.args.get("tournament_id") or request.form.get("tournament_id")
    selected = next((t for t in tournaments_data if str(t.get("id")) == str(requested_id)), None)

    if request.method == "POST":
        if not selected:
            flash("Please select a finished tournament.")
            return redirect(url_for("add_result"))

        tournament_id = selected["id"]
        category = selected.get("event_type") or "Classic"
        rows = []

        for position in range(1, 5):
            team = request.form.get(f"team_{position}", "").strip()
            score = request.form.get(f"score_{position}", "").strip()
            if not team or not score:
                flash("Please enter team name and score for all 4 places.")
                return redirect(url_for("add_result", tournament_id=tournament_id))
            rows.append({
                "tournament_id": int(tournament_id),
                "category": category,
                "position": position,
                "team_name": team,
                "score": score,
            })

        try:
            # One tournament has one event_type in the current schema.
            # Replace all of its existing results so ADD/EDIT works cleanly
            # with the existing unique (tournament_id, position) constraint.
            supabase_request("DELETE", "/rest/v1/tournament_results", params={"tournament_id": f"eq.{tournament_id}"})
            supabase_request("POST", "/rest/v1/tournament_results", json=rows)
            flash("✓ Tournament result saved successfully.")
            return redirect(url_for("tournaments", status="Finished"))
        except Exception as exc:
            print("Result save error:", repr(exc))
            flash("Could not save result: " + str(exc)[:180])

    if selected:
        existing = selected.get("results", {}).get(selected.get("event_type") or "Classic", [])
        existing_map = {int(r.get("position")): r for r in existing}
    else:
        existing_map = {}

    options = "".join(
        f'<option value="{t["id"]}" {"selected" if selected and t["id"] == selected["id"] else ""}>{t["name"]}</option>'
        for t in tournaments_data
    )

    form_html = f"""
<label>Tournament</label>
<select name="tournament_id" required onchange="if(this.value){{window.location='?tournament_id='+this.value;}}">
<option value="">Select Finished Tournament</option>{options}
</select>

<label>Category / Event Type</label>
<input value="{selected.get('event_type') if selected else ''}" readonly>
"""

    for position, label in ((1, "1st Place"), (2, "2nd Place"), (3, "3rd Place"), (4, "4th Place")):
        old = existing_map.get(position, {})
        form_html += f"""
<label>{label} - Team Name</label>
<input name="team_{position}" required value="{old.get('team_name','')}">

<label>{label} - Score</label>
<input name="score_{position}" required value="{old.get('score','')}">
"""

    return render_template("simple_form.html", title="Edit Result" if existing_map else "Add Result", form_html=form_html)


# ============================================================
# MESSAGE BOARD
# ============================================================

def format_message_date(value):
    if not value:
        return ""

    try:
        dt = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
        return dt.strftime("%d %B %Y, %I:%M %p")
    except Exception:
        return str(value)


def load_message_board():
    rows = supabase_request(
        "GET",
        "/rest/v1/community_messages",
        params={
            "select": "id,author_id,title,message,created_at",
            "is_active": "eq.true",
            "order": "created_at.desc",
            "limit": "5",
        },
    ) or []

    if not rows:
        return []

    author_ids = sorted({
        str(row.get("author_id"))
        for row in rows
        if row.get("author_id")
    })

    author_names = {}

    if author_ids:
        try:
            profiles = supabase_request(
                "GET",
                "/rest/v1/profiles",
                params={
                    "select": "id,full_name",
                    "id": "in.(" + ",".join(author_ids) + ")",
                },
            ) or []

            author_names = {
                str(p.get("id")): p.get("full_name") or "Community Member"
                for p in profiles
            }
        except Exception as exc:
            print("Message author lookup error:", repr(exc))

    for row in rows:
        row["author_name"] = author_names.get(
            str(row.get("author_id")),
            ""
        )
        row["created_at_display"] = format_message_date(
            row.get("created_at")
        )

    return rows



@app.route("/messages/add", methods=["GET", "POST"])
@message_manager_required
def add_message():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        message = request.form.get("message", "").strip()

        if len(title) < 2:
            flash("Please enter a message title.")
            return render_template("message_form.html", title="Add Message", message_title=title, message_body=message)

        if len(message) < 2:
            flash("Please enter the message text.")
            return render_template("message_form.html", title="Add Message", message_title=title, message_body=message)

        try:
            supabase_request(
                "POST",
                "/rest/v1/community_messages",
                json={
                    "author_id": session.get("user_id"),
                    "title": title,
                    "message": message,
                    "is_active": True,
                },
            )
            flash("✓ Message added to the Community Message Board.")
            return redirect(url_for("dashboard"))
        except Exception as exc:
            print("Add message error:", repr(exc))
            flash("Could not add message: " + str(exc)[:180])

    return render_template("message_form.html", title="Add Message", message_title="", message_body="")


@app.route("/messages/<int:message_id>/edit", methods=["GET", "POST"])
@message_manager_required
def edit_message(message_id):
    message = load_message(message_id)
    profile = current_profile()

    if not message:
        flash("Message not found.")
        return redirect(url_for("dashboard"))

    if not can_manage_message(message, profile):
        flash("Only Admin can edit any message; an Organizer can edit their own message.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("message", "").strip()

        if len(title) < 2 or len(body) < 2:
            flash("Please enter both a title and message.")
            return render_template("message_form.html", title="Edit Message", message_title=title, message_body=body)

        try:
            supabase_request(
                "PATCH",
                "/rest/v1/community_messages",
                params={"id": f"eq.{message_id}"},
                json={"title": title, "message": body},
            )
            flash("✓ Message updated successfully.")
            return redirect(url_for("dashboard"))
        except Exception as exc:
            print("Edit message error:", repr(exc))
            flash("Could not update message: " + str(exc)[:180])

    return render_template(
        "message_form.html",
        title="Edit Message",
        message_title=message.get("title") or "",
        message_body=message.get("message") or "",
    )


@app.route("/messages/<int:message_id>/delete", methods=["POST"])
@message_manager_required
def delete_message(message_id):
    message = load_message(message_id)
    profile = current_profile()

    if not message:
        flash("Message not found.")
        return redirect(url_for("dashboard"))

    if not can_manage_message(message, profile):
        flash("Only Admin can delete any message; an Organizer can delete their own message.")
        return redirect(url_for("dashboard"))

    try:
        supabase_request(
            "DELETE",
            "/rest/v1/community_messages",
            params={"id": f"eq.{message_id}"},
        )
        flash("✓ Message deleted successfully.")
    except Exception as exc:
        print("Delete message error:", repr(exc))
        flash("Could not delete message: " + str(exc)[:180])

    return redirect(url_for("dashboard"))


# ============================================================
# CHAT
# ============================================================

@app.route("/chat")
@login_required
def chat():
    try:
        members = load_members()
    except Exception as exc:
        print("Chat members error:", repr(exc))
        members = []

    my_id = str(session.get("user_id") or "")
    for member in members:
        member["is_me"] = str(member.get("id") or "") == my_id

    # Do not display the current user in the private-chat list.
    chat_members = [m for m in members if not m.get("is_me")]

    return render_template(
        "chat.html",
        members=chat_members,
        current_user_id=my_id,
        access_token=session.get("access_token", ""),
        supabase_url=SUPABASE_URL,
        supabase_publishable_key=SUPABASE_PUBLISHABLE_KEY,
    )


@app.route("/chat/group")
@login_required
def group_chat():
    try:
        members = load_members()
    except Exception as exc:
        print("Group chat members error:", repr(exc))
        members = []

    return render_template(
        "chat_group.html",
        members=members,
        current_user_id=str(session.get("user_id") or ""),
        access_token=session.get("access_token", ""),
        supabase_url=SUPABASE_URL,
        supabase_publishable_key=SUPABASE_PUBLISHABLE_KEY,
    )


@app.route("/chat/direct/<user_id>")
@login_required
def direct_chat(user_id):
    current_id = str(session.get("user_id") or "")
    if not user_id or user_id == current_id:
        flash("You cannot start a private chat with yourself.")
        return redirect(url_for("chat"))

    try:
        member_rows = supabase_request(
            "GET",
            "/rest/v1/profiles",
            params={
                "select": "id,full_name,email,role,country,phone,photo_url",
                "id": f"eq.{user_id}",
                "limit": "1",
            },
        ) or []
    except Exception as exc:
        print("Direct chat member error:", repr(exc))
        member_rows = []

    if not member_rows:
        flash("That community member could not be found.")
        return redirect(url_for("chat"))

    return render_template(
        "chat_direct.html",
        member=member_rows[0],
        current_user_id=current_id,
        access_token=session.get("access_token", ""),
        supabase_url=SUPABASE_URL,
        supabase_publishable_key=SUPABASE_PUBLISHABLE_KEY,
    )


# ============================================================
# PROFILE
# ============================================================

@app.route("/profile")
@login_required
def profile():
    user_profile = current_profile()

    try:
        members = load_members()
    except Exception:
        members = []

    return render_template(
        "profile.html",
        profile=user_profile,
        members=members,
    )


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    profile_data = current_profile()

    if not profile_data:
        session.clear()
        return redirect(url_for("login"))

    if request.method == "POST":
        data = {
            "full_name": request.form.get("full_name", "").strip(),
            "country": request.form.get("country", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "photo_url": request.form.get("photo_url", "").strip(),
        }

        if len(data["full_name"]) < 2:
            flash("Please enter a valid name.")
        else:
            try:
                supabase_request(
                    "PATCH",
                    "/rest/v1/profiles",
                    params={
                        "id": f"eq.{session['user_id']}"
                    },
                    json=data,
                )

                session["user_name"] = data["full_name"]
                flash("✓ Profile updated successfully.")
                return redirect(url_for("profile"))

            except Exception as exc:
                print("Profile update error:", repr(exc))
                flash("Could not update your profile.")

    return render_template(
        "profile_edit.html",
        profile=profile_data,
        countries=COUNTRIES,
        access_token=session.get("access_token", ""),
        supabase_url=SUPABASE_URL,
        supabase_publishable_key=SUPABASE_PUBLISHABLE_KEY,
    )


# ============================================================
# SIMPLE ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return """
    <div style="font-family:Arial;padding:30px;text-align:center">
        <h2>Page not found</h2>
        <a href="/dashboard">Go to Dashboard</a>
    </div>
    """, 404


# ============================================================
# DEVELOPMENT SERVER
# ============================================================

if __name__ == "__main__":
    print("==========================================")
    print(" Gateball Lovers - Flask Web App")
    print("==========================================")
    print("Open: http://127.0.0.1:5000")
    print("")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )

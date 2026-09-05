import os
import re
import json
import urllib.parse
import urllib.request
import mimetypes
import uuid
import webbrowser
import threading
from html.parser import HTMLParser
from datetime import date, datetime

from dotenv import load_dotenv
from supabase import create_client
import calendar as pycalendar

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup


# ============================================================
# WINDOW
# ============================================================

Window.clearcolor = (0.97, 0.94, 0.88, 1)

# Mobile phone preview
Window.size = (400, 750)


# ============================================================
# COLORS
# ============================================================

SAFFRON = (0.96, 0.57, 0.08, 1)
DARK_SAFFRON = (0.78, 0.38, 0.03, 1)
LIGHT_SAFFRON = (1.0, 0.82, 0.48, 1)

WHITE = (1, 1, 1, 1)
BLACK = (0.08, 0.08, 0.08, 1)
GREY = (0.55, 0.55, 0.55, 1)
LIGHT_GREY = (0.94, 0.94, 0.94, 1)

GREEN = (0.12, 0.60, 0.25, 1)
RED = (0.80, 0.12, 0.12, 1)
BLUE = (0.10, 0.35, 0.70, 1)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# SUPABASE CONFIGURATION
# ============================================================

load_dotenv(os.path.join(BASE_DIR, ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()

supabase = None

if SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY:
    try:
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_PUBLISHABLE_KEY
        )
    except Exception as exc:
        print("Supabase initialization failed:", exc)

def realtime_record(payload):
    """Safely extract the inserted row from a Supabase Realtime payload."""
    try:
        if isinstance(payload, dict):
            data = payload.get("data") or payload
            if isinstance(data, dict):
                return data.get("record") or data.get("new") or data.get("new_record") or {}
        data = getattr(payload, "data", None)
        if isinstance(data, dict):
            return data.get("record") or data.get("new") or data.get("new_record") or {}
        record = getattr(payload, "record", None) or getattr(payload, "new_record", None)
        return record or {}
    except Exception:
        return {}


LOGO_PATH = os.path.join(
    BASE_DIR,
    "assets",
    "images",
    "gateball_lovers_logo.png"
)

CREATOR_PATH = os.path.join(
    BASE_DIR,
    "assets",
    "images",
    "biswa-ranjan.jpeg"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def make_label(
    text="",
    font_size=16,
    color=BLACK,
    bold=False,
    halign="center"
):
    label = Label(
        text=text,
        font_size=font_size,
        color=color,
        bold=bold,
        halign=halign,
        valign="middle"
    )

    label.bind(
        size=lambda instance, value:
        setattr(instance, "text_size", value)
    )

    return label


def make_button(
    text,
    background_color=SAFFRON,
    text_color=WHITE,
    font_size=15,
    height=dp(50)
):
    button = Button(
        text=text,
        font_size=font_size,
        bold=True,
        color=text_color,
        background_normal="",
        background_down="",
        background_color=background_color,
        size_hint_y=None,
        height=height
    )

    return button


def make_text_input(
    hint_text,
    password=False,
    height=dp(50)
):
    return TextInput(
        hint_text=hint_text,
        multiline=False,
        password=password,
        font_size=16,
        foreground_color=BLACK,
        hint_text_color=GREY,
        background_color=WHITE,
        padding=[dp(15), dp(12)],
        size_hint_y=None,
        height=height
    )


# ============================================================
# SPACER
# ============================================================

class Spacer(BoxLayout):

    def __init__(self, height=None, **kwargs):
        super().__init__(**kwargs)

        self.size_hint_y = None

        if height is None:
            self.height = dp(15)
        else:
            self.height = height


# ============================================================
# CIRCULAR IMAGE
# ============================================================

class CircularImage(Image):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.allow_stretch = True
        self.keep_ratio = True

        with self.canvas.before:
            Color(1, 1, 1, 1)

            self.circle = Ellipse(
                pos=self.pos,
                size=self.size
            )

        self.bind(
            pos=self.update_circle,
            size=self.update_circle
        )

    def update_circle(self, *args):
        self.circle.pos = self.pos
        self.circle.size = self.size


# ============================================================
# CARD
# ============================================================

class Card(BoxLayout):

    def __init__(
        self,
        background_color=WHITE,
        radius=18,
        **kwargs
    ):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*background_color)

            self.rectangle = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(radius)]
            )

        self.bind(
            pos=self.update_rectangle,
            size=self.update_rectangle
        )

    def update_rectangle(self, *args):
        self.rectangle.pos = self.pos
        self.rectangle.size = self.size


# ============================================================
# PROFILE PHOTO HELPERS
# ============================================================

def upload_profile_photo(local_path, user_id):
    """Upload a profile photo to Supabase Storage and return its public URL."""
    if not local_path or not os.path.exists(local_path):
        return ""
    if supabase is None or not user_id:
        return ""

    mime_type, _ = mimetypes.guess_type(local_path)
    if mime_type not in ("image/jpeg", "image/png", "image/webp"):
        mime_type = "image/jpeg"

    extension = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }.get(mime_type, "jpg")

    remote_path = f"{user_id}/{uuid.uuid4().hex}.{extension}"

    with open(local_path, "rb") as f:
        photo_bytes = f.read()

    supabase.storage.from_("profile-photos").upload(
        remote_path,
        photo_bytes,
        file_options={
            "content-type": mime_type,
            "cache-control": "3600",
            "upsert": "false",
        },
    )

    public_url = supabase.storage.from_("profile-photos").get_public_url(remote_path)
    if isinstance(public_url, dict):
        public_url = public_url.get("publicUrl") or public_url.get("public_url") or ""
    return public_url or ""


def download_profile_photo(url, user_id):
    """Download a public profile image into Kivy's writable cache."""
    if not url:
        return ""
    try:
        app = App.get_running_app()
        cache_dir = os.path.join(app.user_data_dir, "profile_cache")
        os.makedirs(cache_dir, exist_ok=True)
        local_path = os.path.join(cache_dir, f"{user_id}.jpg")
        request = urllib.request.Request(url, headers={"User-Agent": "GateballLovers/1.0"})
        with urllib.request.urlopen(request, timeout=8) as response:
            data = response.read()
        with open(local_path, "wb") as f:
            f.write(data)
        return local_path
    except Exception as exc:
        print("Profile photo download error:", exc)
        return ""


# ============================================================
# CHAT HELPERS
# ============================================================

COUNTRY_FLAGS = {
    "india":"🇮🇳","japan":"🇯🇵","china":"🇨🇳","thailand":"🇹🇭","indonesia":"🇮🇩",
    "malaysia":"🇲🇾","singapore":"🇸🇬","nepal":"🇳🇵","bhutan":"🇧🇹","bangladesh":"🇧🇩",
    "sri lanka":"🇱🇰","pakistan":"🇵🇰","united states":"🇺🇸","usa":"🇺🇸","united kingdom":"🇬🇧",
    "uk":"🇬🇧","australia":"🇦🇺","canada":"🇨🇦","france":"🇫🇷","germany":"🇩🇪","italy":"🇮🇹",
    "spain":"🇪🇸","netherlands":"🇳🇱","new zealand":"🇳🇿","south korea":"🇰🇷","korea":"🇰🇷",
    "philippines":"🇵🇭","vietnam":"🇻🇳","myanmar":"🇲🇲","mongolia":"🇲🇳","russia":"🇷🇺",
    "brazil":"🇧🇷","mexico":"🇲🇽","south africa":"🇿🇦","kenya":"🇰🇪","ireland":"🇮🇪",
    "switzerland":"🇨🇭","sweden":"🇸🇪","norway":"🇳🇴","denmark":"🇩🇰"
}

def country_flag(country):
    value=(country or "").strip().lower()
    if value in COUNTRY_FLAGS: return COUNTRY_FLAGS[value]
    if len(value)==2 and value.isalpha(): return "".join(chr(127397+ord(c.upper())) for c in value)
    return "🌍"


def presence_is_online(value, seconds=90):
    if not value: return False
    try:
        from datetime import timezone
        stamp=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        if stamp.tzinfo is None: stamp=stamp.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc)-stamp).total_seconds() <= seconds
    except Exception: return False


# ============================================================
# SPLASH SCREEN
# ============================================================

class SplashScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(
            orientation="vertical",
            padding=[dp(25), dp(30)],
            spacing=dp(10)
        )

        root.add_widget(
            Spacer(height=dp(20))
        )

        # Logo
        logo = Image(
            source=LOGO_PATH,
            size_hint=(1, None),
            height=dp(190),
            allow_stretch=True,
            keep_ratio=True
        )

        root.add_widget(logo)

        # App name
        root.add_widget(
            make_label(
                "Gateball Lovers",
                font_size=30,
                color=DARK_SAFFRON,
                bold=True
            )
        )

        # Tagline
        root.add_widget(
            make_label(
                "Connect. Compete. Celebrate.",
                font_size=18,
                color=BLACK,
                bold=True
            )
        )

        root.add_widget(
            Spacer(height=dp(5))
        )

        # Creator photo
        photo_box = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(130)
        )

        creator_photo = CircularImage(
            source=CREATOR_PATH,
            size_hint=(None, None),
            size=(dp(110), dp(110)),
            pos_hint={"center_x": 0.5}
        )

        photo_box.add_widget(creator_photo)

        root.add_widget(photo_box)

        root.add_widget(
            make_label(
                "Created by",
                font_size=14,
                color=GREY
            )
        )

        root.add_widget(
            make_label(
                "Biswa Ranjan",
                font_size=19,
                color=DARK_SAFFRON,
                bold=True
            )
        )

        root.add_widget(
            make_label(
                "Loading .....",
                font_size=14,
                color=GREY
            )
        )

        root.add_widget(
            Spacer()
        )

        self.add_widget(root)

    def on_enter(self):
        Clock.schedule_once(
            self.go_to_login,
            3.5
        )

    def go_to_login(self, dt):
        if self.manager:
            self.manager.current = "login"


# ============================================================
# LOGIN SCREEN
# ============================================================

class LoginScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        main = BoxLayout(
            orientation="vertical",
            padding=[dp(22), dp(25)],
            spacing=dp(10)
        )

        logo = Image(
            source=LOGO_PATH,
            size_hint=(1, None),
            height=dp(135),
            allow_stretch=True,
            keep_ratio=True
        )

        main.add_widget(logo)

        main.add_widget(
            make_label(
                "Welcome Back",
                font_size=28,
                color=DARK_SAFFRON,
                bold=True
            )
        )

        main.add_widget(
            make_label(
                "Sign in to Gateball Lovers",
                font_size=15,
                color=GREY
            )
        )

        main.add_widget(
            Spacer(height=dp(8))
        )

        self.email_input = make_text_input(
            "Email address"
        )

        main.add_widget(
            self.email_input
        )

        self.password_input = make_text_input(
            "Password",
            password=True
        )

        main.add_widget(
            self.password_input
        )

        self.message = make_label(
            "",
            font_size=14,
            color=RED
        )

        main.add_widget(
            self.message
        )

        login_button = make_button(
            "LOGIN",
            background_color=SAFFRON,
            height=dp(52)
        )

        login_button.bind(
            on_release=self.login
        )

        main.add_widget(login_button)

        signup_button = make_button(
            "CREATE NEW ACCOUNT",
            background_color=DARK_SAFFRON,
            height=dp(50)
        )

        signup_button.bind(
            on_release=self.open_signup
        )

        main.add_widget(signup_button)

        main.add_widget(
            Spacer()
        )

        main.add_widget(
            make_label(
                "Gateball Lovers\n"
                "Connect. Compete. Celebrate.",
                font_size=12,
                color=GREY
            )
        )

        self.add_widget(main)

    def login(self, instance):

        email = self.email_input.text.strip()
        password = self.password_input.text

        self.message.color = RED
        self.message.text = ""

        if not email:
            self.message.text = "Please enter your email."
            return

        if not self.is_valid_email(email):
            self.message.text = "Please enter a valid email."
            return

        if not password:
            self.message.text = "Please enter your password."
            return

        if supabase is None:
            self.message.text = "Supabase is not configured. Check your .env file."
            return

        self.message.color = DARK_SAFFRON
        self.message.text = "Signing in…"

        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            user = response.user

            if user is None:
                self.message.color = RED
                self.message.text = "Login failed. Please check your email and password."
                return

            profile_response = (
                supabase.table("profiles")
                .select("id, full_name, email, role, country, phone, photo_url")
                .eq("id", str(user.id))
                .single()
                .execute()
            )

            profile = profile_response.data

            if not profile:
                self.message.color = RED
                self.message.text = "Your profile could not be loaded."
                return

            app = App.get_running_app()
            app.current_user_id = str(user.id)
            app.current_user_email = profile.get("email") or email
            app.current_user_name = profile.get("full_name") or "Gateball User"
            app.current_role = profile.get("role") or "Player"
            app.current_user_country = profile.get("country") or ""
            app.current_user_phone = profile.get("phone") or ""
            app.current_user_photo = profile.get("photo_url") or ""
            app.start_presence_heartbeat()
            app.setup_realtime_auth()

            print("")
            print("==============================")
            print("SUPABASE LOGIN SUCCESS")
            print("==============================")
            print("User ID:", app.current_user_id)
            print("Name:", app.current_user_name)
            print("Role:", app.current_role)
            print("==============================")
            print("")

            self.message.color = GREEN
            self.message.text = "Login successful!"

            Clock.schedule_once(
                self.open_dashboard,
                0.7
            )

        except Exception as exc:
            print("Supabase login error:", exc)
            error_text = str(exc)

            if "Email not confirmed" in error_text or "email_not_confirmed" in error_text:
                self.message.text = "Please confirm your email before logging in."
            elif "Invalid login credentials" in error_text:
                self.message.text = "Invalid email or password."
            else:
                self.message.text = "Login failed. Please check your details and try again."

    def open_dashboard(self, dt):
        if self.manager:
            dashboard = self.manager.get_screen("dashboard")
            dashboard.user_email = getattr(
                App.get_running_app(),
                "current_user_email",
                self.email_input.text.strip()
            )
            dashboard.user_name = getattr(
                App.get_running_app(),
                "current_user_name",
                "Gateball User"
            )
            dashboard.welcome_label.text = f"Welcome, {dashboard.user_name}!"
            self.manager.current = "dashboard"

    def open_signup(self, instance):

        if self.manager:
            self.manager.current = "signup"

    @staticmethod
    def is_valid_email(email):

        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        return re.match(
            pattern,
            email
        ) is not None


# ============================================================
# SIGN UP SCREEN
# ============================================================

COUNTRY_LIST = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda",
    "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas",
    "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize",
    "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil",
    "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia",
    "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China",
    "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus",
    "Czechia", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica",
    "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea",
    "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France",
    "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada",
    "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras",
    "Hong Kong", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland",
    "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya",
    "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho",
    "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar",
    "Macau", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands",
    "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco",
    "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia",
    "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger",
    "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan",
    "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru",
    "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda",
    "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines",
    "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal",
    "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia",
    "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan",
    "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria",
    "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo",
    "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu",
    "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States",
    "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam",
    "Yemen", "Zambia", "Zimbabwe"
]


class SignupScreen(Screen):

    selected_role = StringProperty("Player")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        scroll = ScrollView(
            do_scroll_x=False
        )

        main = BoxLayout(
            orientation="vertical",
            padding=[dp(22), dp(25)],
            spacing=dp(10),
            size_hint_y=None
        )

        main.bind(
            minimum_height=main.setter("height")
        )

        logo = Image(
            source=LOGO_PATH,
            size_hint=(1, None),
            height=dp(110),
            allow_stretch=True,
            keep_ratio=True
        )

        main.add_widget(logo)

        main.add_widget(
            make_label(
                "Create Account",
                font_size=27,
                color=DARK_SAFFRON,
                bold=True
            )
        )

        main.add_widget(
            make_label(
                "Join the Gateball Lovers community",
                font_size=14,
                color=GREY
            )
        )

        main.add_widget(
            Spacer(height=dp(5))
        )

        self.name_input = make_text_input(
            "Full Name"
        )

        main.add_widget(self.name_input)

        self.email_input = make_text_input(
            "Email Address"
        )

        main.add_widget(self.email_input)

        self.phone_input = make_text_input(
            "Contact Number"
        )

        main.add_widget(self.phone_input)

        main.add_widget(
            make_label(
                "Country",
                font_size=13,
                color=GREY,
                halign="left"
            )
        )

        self.country_input = Spinner(
            text="Select your country",
            values=COUNTRY_LIST,
            size_hint_y=None,
            height=dp(48),
            background_color=WHITE,
            color=BLACK
        )

        main.add_widget(self.country_input)

        self.password_input = make_text_input(
            "Password",
            password=True
        )

        main.add_widget(self.password_input)

        self.confirm_password_input = make_text_input(
            "Confirm Password",
            password=True
        )

        main.add_widget(self.confirm_password_input)

        main.add_widget(
            make_label(
                "Select Account Type",
                font_size=16,
                color=BLACK,
                bold=True
            )
        )

        role_layout = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(50)
        )

        self.player_button = make_button(
            "PLAYER",
            background_color=SAFFRON
        )

        self.organizer_button = make_button(
            "ORGANIZER",
            background_color=GREY
        )

        self.player_button.bind(
            on_release=self.select_player
        )

        self.organizer_button.bind(
            on_release=self.select_organizer
        )

        role_layout.add_widget(
            self.player_button
        )

        role_layout.add_widget(
            self.organizer_button
        )

        main.add_widget(role_layout)

        self.role_info = make_label(
            "Player account selected",
            font_size=13,
            color=DARK_SAFFRON
        )

        main.add_widget(self.role_info)

        self.message = make_label(
            "",
            font_size=14,
            color=RED
        )

        main.add_widget(self.message)

        create_button = make_button(
            "CREATE ACCOUNT",
            background_color=SAFFRON,
            height=dp(55)
        )

        create_button.bind(
            on_release=self.create_account
        )

        main.add_widget(create_button)

        back_button = make_button(
            "BACK TO LOGIN",
            background_color=DARK_SAFFRON
        )

        back_button.bind(
            on_release=self.back_to_login
        )

        main.add_widget(back_button)

        main.add_widget(
            Spacer(height=dp(15))
        )

        main.add_widget(
            make_label(
                "Gateball Lovers\n"
                "Created by Biswa Ranjan",
                font_size=12,
                color=GREY
            )
        )

        scroll.add_widget(main)

        self.add_widget(scroll)

    def select_player(self, instance):

        self.selected_role = "Player"

        self.player_button.background_color = SAFFRON
        self.organizer_button.background_color = GREY

        self.role_info.text = "Player account selected"

    def select_organizer(self, instance):

        self.selected_role = "Organizer"

        self.player_button.background_color = GREY
        self.organizer_button.background_color = SAFFRON

        self.role_info.text = "Organizer account selected"

    def create_account(self, instance):

        self.message.color = RED
        self.message.text = ""

        name = self.name_input.text.strip()
        email = self.email_input.text.strip()
        phone = self.phone_input.text.strip()
        country = self.country_input.text.strip()
        password = self.password_input.text
        confirm_password = self.confirm_password_input.text

        if not name:
            self.message.text = "Please enter your full name."
            return

        if len(name) < 2:
            self.message.text = "Please enter a valid full name."
            return

        if not email:
            self.message.text = "Please enter your email address."
            return

        if not self.is_valid_email(email):
            self.message.text = "Please enter a valid email address."
            return

        if not phone:
            self.message.text = "Please enter your contact number."
            return

        if len(phone) < 5:
            self.message.text = "Please enter a valid contact number."
            return

        if not country or country == "Select your country":
            self.message.text = "Please select your country from the list."
            return

        if not password:
            self.message.text = "Please create a password."
            return

        if len(password) < 8:
            self.message.text = "Password must contain at least 8 characters."
            return

        if not confirm_password:
            self.message.text = "Please confirm your password."
            return

        if password != confirm_password:
            self.message.text = "Passwords do not match."
            return

        if self.selected_role not in ("Player", "Organizer"):
            self.message.text = "Please select a valid account type."
            return

        if supabase is None:
            self.message.text = "Supabase is not configured. Check your .env file."
            return

        self.message.color = DARK_SAFFRON
        self.message.text = "Creating your account…"

        try:
            response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": name,
                        "role": self.selected_role,
                        "country": country,
                        "phone": phone
                    }
                }
            })

            user = response.user
            session = response.session

            if user is None:
                self.message.color = RED
                self.message.text = "Account could not be created."
                return

            print("")
            print("==============================")
            print("SUPABASE ACCOUNT CREATED")
            print("==============================")
            print("User ID:", user.id)
            print("Name:", name)
            print("Email:", email)
            print("Role:", self.selected_role)
            print("Session created:", session is not None)
            print("==============================")
            print("")

            # Confirm Email is enabled in Supabase, so normally there is
            # no active session until the user confirms the email.
            if session is None:
                self.message.color = GREEN
                self.message.text = (
                    "Account created! Check your email to confirm it, "
                    "then log in."
                )
            else:
                self.message.color = GREEN
                self.message.text = "Account created successfully!"

            # Clear password fields but keep the user's other details.
            self.password_input.text = ""
            self.confirm_password_input.text = ""

            Clock.schedule_once(self.back_to_login_after_signup, 2.5)

        except Exception as exc:
            print("Supabase signup error:", exc)
            error_text = str(exc)

            if "User already registered" in error_text:
                self.message.text = "This email is already registered. Please log in."
            elif "already registered" in error_text.lower():
                self.message.text = "This email is already registered. Please log in."
            elif "Password should be at least" in error_text:
                self.message.text = "Password must contain at least 8 characters."
            else:
                self.message.text = "Account creation failed. Please try again."

    def back_to_login_after_signup(self, dt):
        if self.manager:
            self.manager.current = "login"

    def back_to_login(self, instance):

        self.message.text = ""

        if self.manager:
            self.manager.current = "login"

    @staticmethod
    def is_valid_email(email):

        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        return re.match(
            pattern,
            email
        ) is not None


# ============================================================
# TEMPORARY COMMUNITY DATA
# ============================================================

PLAYERS = [
    {"name": "Biswa Ranjan", "country": "India", "photo": CREATOR_PATH},
    {"name": "Taro Yamada", "country": "Japan", "photo": ""},
    {"name": "John Smith", "country": "Australia", "photo": ""},
    {"name": "Carlos Garcia", "country": "Spain", "photo": ""},
    {"name": "Min-Jae Kim", "country": "South Korea", "photo": ""},
]

ORGANIZERS = [
    {"name": "Kenji Tanaka", "country": "Japan", "photo": ""},
    {"name": "Rajesh Kumar", "country": "India", "photo": ""},
    {"name": "Michael Brown", "country": "Australia", "photo": ""},
]


# ============================================================
# TOURNAMENT HELPERS
# ============================================================

TOURNAMENTS = []


def format_db_date(value):
    if not value:
        return ""
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d %B %Y")
    except Exception:
        return str(value)


def db_date(value):
    return datetime.strptime(value, "%d %B %Y").date().isoformat()


def calculated_tournament_status(start_value, end_value):
    try:
        start = datetime.strptime(str(start_value), "%Y-%m-%d").date() if "-" in str(start_value) else datetime.strptime(str(start_value), "%d %B %Y").date()
        end = datetime.strptime(str(end_value), "%Y-%m-%d").date() if "-" in str(end_value) else datetime.strptime(str(end_value), "%d %B %Y").date()
        today = date.today()
        if today < start:
            return "Upcoming"
        if today > end:
            return "Finished"
        return "Ongoing"
    except Exception:
        return "Upcoming"


def row_to_tournament(row, results=None):
    status = calculated_tournament_status(row.get("start_date", ""), row.get("end_date", ""))
    return {
        "id": row.get("id"),
        "name": row.get("name", "Tournament"),
        "venue": row.get("venue", ""),
        "country": row.get("country", ""),
        "event_type": row.get("event_type", "Classic"),
        "event_types": [row.get("event_type", "Classic")],
        "results": results or {},
        "start": format_db_date(row.get("start_date", "")),
        "end": format_db_date(row.get("end_date", "")),
        "status": status,
        "winner": "",
        "score": "",
        "organizer": row.get("organizer_name") or "Organizer",
        "organizer_id": row.get("organizer_id", ""),
        "organizer_name": row.get("organizer_name") or "",
        "live_link": row.get("live_link") or "",
        "joined_players": [],
        "description": row.get("description") or "",
    }


def load_tournaments_from_supabase(include_results=True):
    if supabase is None:
        return []
    response = (
        supabase.table("tournaments")
        .select("id, name, venue, country, event_type, start_date, end_date, description, organizer_id, organizer_name, live_link, status, created_at")
        .order("start_date", desc=False)
        .execute()
    )
    rows = response.data or []
    results_by_tournament = {}
    if include_results and rows:
        ids = [r.get("id") for r in rows if r.get("id") is not None]
        if ids:
            result_response = (
                supabase.table("tournament_results")
                .select("id, tournament_id, category, position, team_name, score, created_at")
                .in_("tournament_id", ids)
                .order("position", desc=False)
                .execute()
            )
            for item in (result_response.data or []):
                results_by_tournament.setdefault(item["tournament_id"], {}).setdefault(item["category"], []).append({
                    "id": item.get("id"),
                    "place": f'{item.get("position", "")}th' if item.get("position") not in (1, 2, 3) else {1: "1st", 2: "2nd", 3: "3rd"}.get(item.get("position"), ""),
                    "position": item.get("position"),
                    "team": item.get("team_name", ""),
                    "score": item.get("score", "") or "",
                })
    return [row_to_tournament(row, results_by_tournament.get(row.get("id"), {})) for row in rows]


def refresh_global_tournaments():
    global TOURNAMENTS
    try:
        TOURNAMENTS = load_tournaments_from_supabase(include_results=True)
    except Exception as exc:
        print("Tournament load error:", exc)
        TOURNAMENTS = []
    return TOURNAMENTS


# ============================================================
# PERSON CARD
# ============================================================


# ============================================================

class PersonCard(Card):

    def __init__(self, person, **kwargs):
        super().__init__(
            orientation="horizontal",
            padding=[dp(10), dp(8)],
            spacing=dp(12),
            size_hint_y=None,
            height=dp(82),
            background_color=WHITE,
            **kwargs
        )

        photo_holder = BoxLayout(
            size_hint=(None, 1),
            width=dp(62)
        )

        photo_path = person.get("photo", "")

        if photo_path and os.path.exists(photo_path):
            photo = CircularImage(
                source=photo_path,
                size_hint=(None, None),
                size=(dp(58), dp(58)),
                pos_hint={"center_y": 0.5}
            )
        else:
            photo = make_label(
                "👤",
                font_size=32,
                color=DARK_SAFFRON
            )

        photo_holder.add_widget(photo)
        self.add_widget(photo_holder)

        details = BoxLayout(
            orientation="vertical",
            spacing=dp(2)
        )

        details.add_widget(
            make_label(
                person["name"],
                font_size=17,
                color=BLACK,
                bold=True,
                halign="left"
            )
        )

        details.add_widget(
            make_label(
                "🌍  " + person["country"],
                font_size=14,
                color=GREY,
                halign="left"
            )
        )

        self.add_widget(details)


# ============================================================
# PLAYERS / ORGANIZERS LIST
# ============================================================

class BottomNavigation(BoxLayout):

    def __init__(self, current_screen="dashboard", **kwargs):
        super().__init__(
            orientation="horizontal",
            padding=[dp(5), dp(5)],
            spacing=dp(3),
            size_hint_y=None,
            height=dp(70),
            **kwargs
        )

        with self.canvas.before:
            Color(*WHITE)
            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(16)]
            )
        self.bind(pos=self._update_bg, size=self._update_bg)

        items = [
            ("🏠", "Home", "dashboard"),
            ("🏆", "Tournaments", "tournaments"),
            ("💬", "Chat", "chat"),
            ("👤", "Profile", "profile"),
        ]

        for icon, title, screen in items:
            button = Button(
                text=f"{icon}\n{title}",
                font_size=12,
                bold=True,
                color=DARK_SAFFRON if screen == current_screen else GREY,
                background_normal="",
                background_down="",
                background_color=LIGHT_SAFFRON if screen == current_screen else WHITE
            )
            button.bind(
                on_release=lambda instance, target=screen: self.go_to(target)
            )
            self.add_widget(button)

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def go_to(self, screen_name):
        app = App.get_running_app()
        if app and app.root:
            app.root.current = screen_name


# ============================================================
# PLAYERS / ORGANIZERS LIST
# ============================================================

class CommunityListScreen(Screen):

    list_title = StringProperty("Players")
    list_type = StringProperty("Players")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical")

        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(72),
            padding=[dp(10), dp(8)],
            spacing=dp(8)
        )

        back_button = make_button("←", background_color=DARK_SAFFRON, font_size=24, height=dp(52))
        back_button.size_hint_x = None
        back_button.width = dp(58)
        back_button.bind(on_release=self.go_home)
        header.add_widget(back_button)

        header.add_widget(
            make_label(
                self.list_title,
                font_size=23,
                color=DARK_SAFFRON,
                bold=True,
                halign="left"
            )
        )
        root.add_widget(header)

        self.count_label = make_label("", font_size=14, color=GREY, halign="left")
        self.count_label.size_hint_y = None
        self.count_label.height = dp(30)
        root.add_widget(self.count_label)

        scroll = ScrollView(do_scroll_x=False)
        self.list_container = BoxLayout(
            orientation="vertical",
            padding=[dp(12), dp(8), dp(12), dp(20)],
            spacing=dp(10),
            size_hint_y=None
        )
        self.list_container.bind(minimum_height=self.list_container.setter("height"))
        scroll.add_widget(self.list_container)
        root.add_widget(scroll)

        root.add_widget(BottomNavigation())
        self.add_widget(root)

    def refresh_list(self):
        self.list_container.clear_widgets()
        people = PLAYERS if self.list_type == "Players" else ORGANIZERS
        self.count_label.text = f"{len(people)} {self.list_type.lower()} in the community"
        for person in people:
            self.list_container.add_widget(PersonCard(person))

    def on_pre_enter(self, *args):
        self.refresh_list()

    def go_home(self, instance):
        if self.manager:
            self.manager.current = "dashboard"


# ============================================================
# FEATURE PLACEHOLDER SCREEN
# ============================================================

class FeatureScreen(Screen):

    title_text = StringProperty("")
    icon_text = StringProperty("")
    message_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical")

        content = BoxLayout(
            orientation="vertical",
            padding=[dp(18), dp(18)],
            spacing=dp(12)
        )

        header = Card(
            orientation="horizontal",
            padding=[dp(12), dp(8)],
            spacing=dp(10),
            size_hint_y=None,
            height=dp(68),
            background_color=SAFFRON
        )

        home_button = make_button("←", background_color=DARK_SAFFRON, font_size=24, height=dp(50))
        home_button.size_hint_x = None
        home_button.width = dp(55)
        home_button.bind(on_release=self.go_home)
        header.add_widget(home_button)
        header.add_widget(
            make_label(
                self.icon_text + "  " + self.title_text,
                font_size=21, color=WHITE, bold=True, halign="left"
            )
        )
        content.add_widget(header)
        content.add_widget(Spacer(height=dp(25)))

        card = Card(orientation="vertical", padding=[dp(20), dp(20)], spacing=dp(12), background_color=WHITE)
        card.add_widget(make_label(self.icon_text, font_size=55, color=DARK_SAFFRON))
        card.add_widget(make_label(self.title_text, font_size=25, color=DARK_SAFFRON, bold=True))
        card.add_widget(make_label(self.message_text, font_size=15, color=GREY))
        content.add_widget(card)
        content.add_widget(Spacer())

        root.add_widget(content)
        root.add_widget(BottomNavigation(current_screen=self.name))
        self.add_widget(root)

    def go_home(self, instance):
        if self.manager:
            self.manager.current = "dashboard"


# ============================================================
# SIMPLE CALENDAR PICKER
# ============================================================
class CalendarPopup:
    def __init__(self, target_input):
        from kivy.uix.popup import Popup
        self.target_input = target_input
        self.popup = Popup(title="Select Date", size_hint=(0.94, 0.72), auto_dismiss=True)
        self.year = datetime.now().year
        self.month = datetime.now().month
        self.build()

    def build(self):
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        nav = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(45), spacing=dp(6))
        prev_btn = make_button("‹", background_color=DARK_SAFFRON, font_size=25, height=dp(42))
        next_btn = make_button("›", background_color=DARK_SAFFRON, font_size=25, height=dp(42))
        title = make_label(f"{pycalendar.month_name[self.month]} {self.year}", font_size=18, color=DARK_SAFFRON, bold=True)
        prev_btn.bind(on_release=lambda *_: self.change_month(-1))
        next_btn.bind(on_release=lambda *_: self.change_month(1))
        nav.add_widget(prev_btn); nav.add_widget(title); nav.add_widget(next_btn)
        self.title_label = title
        root.add_widget(nav)
        weekdays = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32))
        for day_name in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"):
            weekdays.add_widget(make_label(day_name, font_size=11, color=GREY, bold=True))
        root.add_widget(weekdays)
        self.grid = BoxLayout(orientation="vertical", spacing=dp(3))
        root.add_widget(self.grid)
        self.popup.content = root
        self.redraw()

    def redraw(self):
        self.title_label.text = f"{pycalendar.month_name[self.month]} {self.year}"
        self.grid.clear_widgets()
        for week in pycalendar.monthcalendar(self.year, self.month):
            row = BoxLayout(orientation="horizontal", spacing=dp(3))
            for day in week:
                if day == 0:
                    row.add_widget(Label())
                else:
                    btn = make_button(str(day), background_color=LIGHT_GREY, text_color=BLACK, font_size=13, height=dp(40))
                    btn.bind(on_release=lambda instance, d=day: self.choose(d))
                    row.add_widget(btn)
            self.grid.add_widget(row)

    def change_month(self, amount):
        self.month += amount
        if self.month < 1:
            self.month = 12; self.year -= 1
        elif self.month > 12:
            self.month = 1; self.year += 1
        self.redraw()

    def choose(self, day):
        selected = date(self.year, self.month, day)
        self.target_input.text = selected.strftime("%d %B %Y")
        self.popup.dismiss()

    def open(self):
        self.popup.open()


# ============================================================
# SEARCHABLE COUNTRY SELECTOR
# ============================================================

class SearchableCountrySelector(BoxLayout):
    def __init__(self, placeholder="🌍  Select country ▼", **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None, height=dp(52), **kwargs)
        self.placeholder = placeholder
        self.selected_country = ""
        self.button = make_button(placeholder, background_color=LIGHT_SAFFRON, text_color=BLACK, font_size=15, height=dp(52))
        self.button.bind(on_release=self.open_popup)
        self.add_widget(self.button)

    @property
    def text(self):
        return self.selected_country

    @text.setter
    def text(self, value):
        value = (value or "").strip()
        if value and value not in COUNTRY_LIST:
            # Keep compatibility with old placeholder text.
            if value.startswith("🌍") or value.startswith("Select"):
                value = ""
        self.selected_country = value
        self.button.text = value if value else self.placeholder

    def open_popup(self, *_):
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        title = make_label("🌍 Select Tournament Country", font_size=18, color=DARK_SAFFRON, bold=True, halign="left")
        title.size_hint_y = None; title.height = dp(38)
        content.add_widget(title)

        search = TextInput(
            hint_text="Type to search — e.g. ind",
            multiline=False, font_size=16, foreground_color=BLACK,
            hint_text_color=GREY, background_color=WHITE,
            padding=[dp(12), dp(10)], size_hint_y=None, height=dp(48)
        )
        content.add_widget(search)

        scroll = ScrollView(do_scroll_x=False)
        results_box = BoxLayout(orientation="vertical", spacing=dp(5), size_hint_y=None)
        results_box.bind(minimum_height=results_box.setter("height"))
        scroll.add_widget(results_box)
        content.add_widget(scroll)

        popup = Popup(
            title="", content=content, size_hint=(0.92, 0.82),
            auto_dismiss=True, separator_color=SAFFRON
        )

        def refresh_results(*_):
            query = search.text.strip().lower()
            results_box.clear_widgets()
            matches = [c for c in COUNTRY_LIST if not query or c.lower().startswith(query)]
            # If there are no starts-with matches, allow a contains search as a fallback.
            if query and not matches:
                matches = [c for c in COUNTRY_LIST if query in c.lower()]
            if not matches:
                results_box.add_widget(make_label("No country found", font_size=14, color=GREY, halign="left"))
                return
            for country in matches:
                b = make_button(country, background_color=WHITE, text_color=BLACK, font_size=14, height=dp(44))
                b.bind(on_release=lambda _btn, c=country: self.choose_country(c, popup))
                results_box.add_widget(b)

        search.bind(text=refresh_results)
        refresh_results()
        popup.open()
        Clock.schedule_once(lambda *_: setattr(search, "focus", True), 0.15)

    def choose_country(self, country, popup):
        self.selected_country = country
        self.button.text = country
        popup.dismiss()

    def clear(self):
        self.selected_country = ""
        self.button.text = self.placeholder


# ============================================================
# EVENT TYPE CHECKBOX ROW
# ============================================================
class EventTypeRow(BoxLayout):
    def __init__(self, text, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(48), spacing=dp(8), **kwargs)
        self.checkbox = CheckBox(size_hint=(None, None), size=(dp(36), dp(36)), active=False, color=DARK_SAFFRON)
        self.add_widget(self.checkbox)
        self.add_widget(make_label(text, font_size=16, color=BLACK, bold=True, halign="left"))


# ============================================================
# ADD TOURNAMENT SCREEN
# ============================================================
class AddTournamentScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical")
        header = Card(orientation="horizontal", padding=[dp(10), dp(8)], spacing=dp(8), size_hint_y=None, height=dp(68), background_color=SAFFRON)
        back = make_button("←", background_color=DARK_SAFFRON, font_size=24, height=dp(50))
        back.size_hint_x = None; back.width = dp(55)
        back.bind(on_release=lambda *_: setattr(self.manager, "current", "tournaments"))
        header.add_widget(back)
        header.add_widget(make_label("➕  Add Tournament", font_size=22, color=WHITE, bold=True, halign="left"))
        root.add_widget(header)

        scroll = ScrollView(do_scroll_x=False)
        form = BoxLayout(orientation="vertical", padding=[dp(15), dp(12), dp(15), dp(20)], spacing=dp(10), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))

        self.name_input = make_text_input("Tournament Name")
        self.organizer_input = make_text_input("Organizer / Association Name")
        self.venue_input = make_text_input("Venue / City")
        form.add_widget(self.name_input)
        form.add_widget(self.organizer_input)
        form.add_widget(self.venue_input)

        form.add_widget(make_label("Country", font_size=13, color=GREY, halign="left"))
        self.country_input = SearchableCountrySelector(
            placeholder="🌍  Select tournament country ▼"
        )
        form.add_widget(self.country_input)

        form.add_widget(make_label("Event Type", font_size=16, color=DARK_SAFFRON, bold=True, halign="left"))
        self.classic = EventTypeRow("Classic")
        self.triple = EventTypeRow("Triple")
        self.double = EventTypeRow("Double")
        form.add_widget(self.classic); form.add_widget(self.triple); form.add_widget(self.double)

        form.add_widget(make_label("Tournament Dates", font_size=16, color=DARK_SAFFRON, bold=True, halign="left"))
        self.start_input = make_text_input("Start Date — tap to open calendar")
        self.end_input = make_text_input("End Date — tap to open calendar")
        self.start_input.readonly = True; self.end_input.readonly = True
        self.start_input.bind(on_touch_down=self.start_calendar)
        self.end_input.bind(on_touch_down=self.end_calendar)
        form.add_widget(self.start_input); form.add_widget(self.end_input)

        self.description_input = TextInput(
            hint_text="Tournament description / registration information (optional)",
            multiline=True,
            font_size=15,
            foreground_color=BLACK,
            hint_text_color=GREY,
            background_color=WHITE,
            padding=[dp(15), dp(12)],
            size_hint_y=None,
            height=dp(105)
        )
        form.add_widget(self.description_input)

        self.live_link_input = make_text_input("Live Social Media Link (optional)", height=dp(52))
        form.add_widget(self.live_link_input)

        self.message = make_label("", font_size=13, color=RED, halign="center")
        self.message.size_hint_y = None; self.message.height = dp(42)
        form.add_widget(self.message)

        save = make_button("SAVE TOURNAMENT", background_color=GREEN, height=dp(54))
        save.bind(on_release=self.save_tournament)
        form.add_widget(save)
        form.add_widget(Spacer(height=dp(10)))
        scroll.add_widget(form)
        root.add_widget(scroll)
        root.add_widget(BottomNavigation(current_screen="tournaments"))
        self.add_widget(root)

    def on_pre_enter(self, *args):
        # Always open a fresh Add Tournament form. This prevents the previous
        # tournament's values from appearing when the user creates another one.
        self.clear_form()
        self.message.text = ""
        self.message.color = RED
        if getattr(App.get_running_app(), "current_role", "Player") not in ("Admin", "Organizer"):
            self.message.text = "Only Admin or Organizer can add tournaments."

    def clear_form(self):
        self.name_input.text = ""
        self.organizer_input.text = ""
        self.venue_input.text = ""
        self.country_input.clear()
        self.classic.checkbox.active = False
        self.triple.checkbox.active = False
        self.double.checkbox.active = False
        self.start_input.text = ""
        self.end_input.text = ""
        self.description_input.text = ""
        self.live_link_input.text = ""
        self.message.text = ""

    def start_calendar(self, instance, touch):
        if instance.collide_point(*touch.pos):
            CalendarPopup(self.start_input).open(); return True
        return False

    def end_calendar(self, instance, touch):
        if instance.collide_point(*touch.pos):
            CalendarPopup(self.end_input).open(); return True
        return False

    def save_tournament(self, instance):
        app = App.get_running_app()
        role = getattr(app, "current_role", "Player")
        user_id = getattr(app, "current_user_id", "")
        if role not in ("Admin", "Organizer"):
            self.message.text = "Only Admin or Organizer can add tournaments."; return
        if supabase is None:
            self.message.text = "Supabase is not connected."; return
        if not user_id:
            self.message.text = "Please log in again before adding a tournament."; return

        name = self.name_input.text.strip()
        organizer = self.organizer_input.text.strip()
        venue = self.venue_input.text.strip()
        country = self.country_input.text.strip()
        types = []
        if self.classic.checkbox.active: types.append("Classic")
        if self.triple.checkbox.active: types.append("Triple")
        if self.double.checkbox.active: types.append("Double")

        if not name or not organizer or not venue or not country or len(types) != 1 or not self.start_input.text or not self.end_input.text:
            self.message.text = "Please complete all fields and select exactly one Event Type."; return

        try:
            start = datetime.strptime(self.start_input.text, "%d %B %Y").date()
            end = datetime.strptime(self.end_input.text, "%d %B %Y").date()
            if end < start:
                self.message.text = "End Date cannot be before Start Date."; return
        except ValueError:
            self.message.text = "Please select valid dates from the calendar."; return

        try:
            response = supabase.table("tournaments").insert({
                "name": name,
                "venue": venue,
                "country": country,
                "event_type": types[0],
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "description": self.description_input.text.strip(),
                "organizer_id": user_id,
                "organizer_name": organizer,
                "live_link": self.live_link_input.text.strip(),
                "status": calculated_tournament_status(start.isoformat(), end.isoformat())
            }).execute()
            print("Tournament insert response:", response.data)
            if not response.data:
                # Confirm the insert is visible through the Data API.
                verify = (supabase.table("tournaments")
                          .select("id, name, country, organizer_name")
                          .eq("organizer_id", user_id)
                          .eq("name", name)
                          .order("created_at", desc=True)
                          .limit(1)
                          .execute())
                if not verify.data:
                    raise RuntimeError("Tournament insert returned no row and the new tournament could not be verified in Supabase.")
            # A successful insert may return a row representation depending on
            # the client's return settings. The absence of returned data alone
            # is not treated as a failed INSERT.
            refresh_global_tournaments()
            self.message.color = GREEN
            self.message.text = "✓ Tournament saved online successfully!"
            self.clear_form()
            self.message.color = GREEN
            self.message.text = "✓ Tournament saved online successfully!"
            Clock.schedule_once(lambda *_: self.return_to_tournaments(), 0.8)
        except Exception as exc:
            print("Add tournament error:", repr(exc))
            self.message.color = RED
            self.message.text = "Save failed: " + str(exc)[:180]

    def return_to_tournaments(self):
        if self.manager:
            self.manager.current = "tournaments"


# ============================================================
# ADD RESULT SCREEN
# ============================================================
class AddResultScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_tournament = None
        self.selected_category = None
        self.inputs = []
        self.category_buttons = []

        root = BoxLayout(orientation="vertical")
        header = Card(orientation="horizontal", padding=[dp(10), dp(8)], spacing=dp(8), size_hint_y=None, height=dp(68), background_color=SAFFRON)
        back = make_button("←", background_color=DARK_SAFFRON, font_size=24, height=dp(50)); back.size_hint_x=None; back.width=dp(55)
        back.bind(on_release=lambda *_: setattr(self.manager, "current", "tournaments"))
        header.add_widget(back); header.add_widget(make_label("🏆  Add Tournament Result", font_size=21, color=WHITE, bold=True, halign="left")); root.add_widget(header)

        scroll = ScrollView(do_scroll_x=False)
        self.form = BoxLayout(orientation="vertical", padding=[dp(15), dp(12)], spacing=dp(8), size_hint_y=None)
        self.form.bind(minimum_height=self.form.setter("height"))
        self.form.add_widget(make_label("Select Tournament", font_size=16, color=DARK_SAFFRON, bold=True, halign="left"))
        self.tournament_box = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        self.tournament_box.bind(minimum_height=self.tournament_box.setter("height"))
        self.form.add_widget(self.tournament_box)
        self.selected_label = make_label("No tournament selected", font_size=14, color=GREY, bold=True, halign="left")
        self.form.add_widget(self.selected_label)
        self.category_box = BoxLayout(orientation="horizontal", spacing=dp(5), size_hint_y=None, height=dp(48))
        self.form.add_widget(self.category_box)
        self.result_box = BoxLayout(orientation="vertical", spacing=dp(7), size_hint_y=None)
        self.result_box.bind(minimum_height=self.result_box.setter("height"))
        self.form.add_widget(self.result_box)
        self.message = make_label("", font_size=13, color=RED)
        self.form.add_widget(self.message)
        save = make_button("SAVE RESULT", background_color=GREEN, height=dp(54)); save.bind(on_release=self.save_result)
        self.form.add_widget(save)
        scroll.add_widget(self.form); root.add_widget(scroll); root.add_widget(BottomNavigation(current_screen="tournaments")); self.add_widget(root)

    def on_pre_enter(self, *args):
        self.load_tournaments()

    def load_tournaments(self):
        self.tournament_box.clear_widgets(); self.category_box.clear_widgets(); self.result_box.clear_widgets()
        self.selected_tournament = None; self.selected_category = None; self.inputs = []; self.category_buttons = []
        try:
            tournaments = refresh_global_tournaments()
            if not tournaments:
                self.tournament_box.add_widget(make_label("No tournaments available yet.", font_size=14, color=GREY, halign="left"))
                return
            for tournament in tournaments:
                b = make_button(tournament["name"], background_color=LIGHT_GREY, text_color=BLACK, font_size=13, height=dp(48))
                b.bind(on_release=lambda inst, t=tournament: self.select_tournament(t))
                self.tournament_box.add_widget(b)
        except Exception as exc:
            print("Load result tournaments error:", exc)
            self.tournament_box.add_widget(make_label("Could not load tournaments.", font_size=14, color=RED, halign="left"))

    def select_tournament(self, tournament):
        self.selected_tournament = tournament
        self.selected_label.text = "Selected: " + tournament["name"]
        self.category_box.clear_widgets(); self.result_box.clear_widgets(); self.inputs = []; self.category_buttons = []
        for category in tournament.get("event_types", []):
            b = make_button(category, background_color=LIGHT_GREY, text_color=BLACK, font_size=12, height=dp(44))
            b.bind(on_release=lambda inst, c=category: self.select_category(c))
            self.category_box.add_widget(b); self.category_buttons.append(b)
        if tournament.get("event_types"):
            self.select_category(tournament["event_types"][0])

    def select_category(self, category):
        self.selected_category = category
        for b in self.category_buttons:
            active = b.text == category; b.background_color = SAFFRON if active else LIGHT_GREY; b.color = WHITE if active else BLACK
        self.result_box.clear_widgets(); self.inputs = []
        self.result_box.add_widget(make_label(f"{category} — 1st to 4th Place", font_size=16, color=DARK_SAFFRON, bold=True, halign="left"))
        existing = self.selected_tournament.get("results", {}).get(category, []) if self.selected_tournament else []
        existing_map = {r.get("position"): r for r in existing}
        for position in (1, 2, 3, 4):
            place = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}[position]
            self.result_box.add_widget(make_label(place + " Place", font_size=14, color=BLACK, bold=True, halign="left"))
            team = make_text_input("Team Name", height=dp(46)); score = make_text_input("Score", height=dp(46))
            old = existing_map.get(position, {})
            team.text = old.get("team", ""); score.text = old.get("score", "")
            self.result_box.add_widget(team); self.result_box.add_widget(score); self.inputs.append((position, team, score))

    def save_result(self, instance):
        app = App.get_running_app()
        if getattr(app, "current_role", "Player") not in ("Admin", "Organizer"):
            self.message.text = "Only Admin or Organizer can add results."; return
        if supabase is None:
            self.message.text = "Supabase is not connected."; return
        if not self.selected_tournament or not self.selected_category:
            self.message.text = "Please select a tournament and Event Type."; return
        rows = []
        for position, team, score in self.inputs:
            if not team.text.strip() or not score.text.strip():
                self.message.text = "Please enter team name and score for all 4 places."; return
            rows.append({"tournament_id": self.selected_tournament["id"], "category": self.selected_category, "position": position, "team_name": team.text.strip(), "score": score.text.strip()})
        try:
            supabase.table("tournament_results").delete().eq("tournament_id", self.selected_tournament["id"]).eq("category", self.selected_category).execute()
            supabase.table("tournament_results").insert(rows).execute()
            self.message.color = GREEN; self.message.text = "✓ Result saved online successfully!"
            Clock.schedule_once(lambda *_: setattr(self.manager, "current", "tournaments"), 0.8)
        except Exception as exc:
            print("Save tournament result error:", exc)
            self.message.color = RED; self.message.text = "Could not save result. Please try again."


# ============================================================
# TOURNAMENT SCREEN
# ============================================================
class TournamentCard(Card):
    def __init__(self, tournament, **kwargs):
        status = tournament.get("status", "Upcoming")
        results = tournament.get("results", {})
        base_height = 300
        if status == "Finished":
            base_height = 315 + (len(results) * 110)
        elif status == "Ongoing":
            base_height = 330 if tournament.get("live_link") else 315
        super().__init__(orientation="vertical", padding=[dp(14), dp(11)], spacing=dp(5), size_hint_y=None, height=dp(base_height), background_color=WHITE, **kwargs)

        status_color = RED if status == "Ongoing" else GREEN if status == "Finished" else DARK_SAFFRON
        event_type = tournament.get("event_type") or ", ".join(tournament.get("event_types", []))
        organizer = tournament.get("organizer", "Organizer not specified")
        country = tournament.get("country", "")

        self.add_widget(make_label(f"{status.upper()}  •  {event_type}", font_size=12, color=status_color, bold=True, halign="left"))
        self.add_widget(make_label(tournament.get("name", "Tournament"), font_size=19, color=BLACK, bold=True, halign="left"))
        self.add_widget(make_label("📍  " + tournament.get("venue", ""), font_size=13, color=GREY, halign="left"))
        if country:
            self.add_widget(make_label("🌐  " + country, font_size=13, color=GREY, halign="left"))
        self.add_widget(make_label("📅  " + tournament.get("start", "") + "  →  " + tournament.get("end", ""), font_size=13, color=GREY, halign="left"))
        self.add_widget(make_label("🏢  Organized by: " + organizer, font_size=13, color=DARK_SAFFRON, bold=True, halign="left"))

        if tournament.get("description"):
            self.add_widget(make_label(tournament["description"], font_size=12, color=GREY, halign="left"))

        if status == "Ongoing":
            self.add_widget(make_label("🔴 Live tournament in progress", font_size=12, color=RED, bold=True, halign="left"))
            live_link = (tournament.get("live_link") or "").strip()
            if live_link:
                open_live = make_button("▶ OPEN LIVE SOCIAL MEDIA", background_color=RED, height=dp(42), font_size=11)
                open_live.bind(on_release=lambda *_: self.open_live_link(live_link))
                self.add_widget(open_live)
            role = getattr(App.get_running_app(), "current_role", "Player")
            if role in ("Admin", "Organizer"):
                live_input = make_text_input("Paste Facebook / YouTube / Instagram / other live link", height=dp(44))
                live_input.text = live_link
                save_live = make_button("SAVE LIVE LINK", background_color=DARK_SAFFRON, height=dp(40), font_size=10)
                def save_live_link(*_):
                    self.save_live_link(tournament, live_input.text.strip())
                save_live.bind(on_release=save_live_link)
                self.add_widget(live_input)
                self.add_widget(save_live)

        if status == "Finished" and results:
            self.add_widget(make_label("🏆 Final Results", font_size=14, color=GREEN, bold=True, halign="left"))
            for category, rows in results.items():
                self.add_widget(make_label(category + "", font_size=12, color=DARK_SAFFRON, bold=True, halign="left"))
                for row in rows[:4]:
                    place = row.get("place", "")
                    self.add_widget(make_label(f"{place}  {row.get('team', '')}  —  {row.get('score', '')}", font_size=11, color=BLACK, halign="left"))
        elif status == "Finished":
            self.add_widget(make_label("🏆 Results not entered yet.", font_size=12, color=GREY, halign="left"))

        role = getattr(App.get_running_app(), "current_role", "Player")
        if role in ("Admin", "Organizer"):
            action_row = BoxLayout(orientation="horizontal", spacing=dp(7), size_hint_y=None, height=dp(42))
            edit_btn = make_button("✏ EDIT", background_color=DARK_SAFFRON, height=dp(40), font_size=11)
            delete_btn = make_button("🗑 DELETE", background_color=RED, height=dp(40), font_size=11)
            edit_btn.bind(on_release=lambda *_: self.open_edit(tournament))
            delete_btn.bind(on_release=lambda *_: self.confirm_delete(tournament))
            action_row.add_widget(edit_btn); action_row.add_widget(delete_btn); self.add_widget(action_row)

    def open_live_link(self, url):
        url = (url or "").strip()
        if not url:
            return
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
        try:
            webbrowser.open(url)
        except Exception as exc:
            print("Open live link error:", exc)

    def save_live_link(self, tournament, url):
        app = App.get_running_app()
        if getattr(app, "current_role", "Player") not in ("Admin", "Organizer"):
            return
        if supabase is None or not tournament.get("id"):
            return
        url = (url or "").strip()
        try:
            supabase.table("tournaments").update({
                "live_link": url,
                "updated_at": datetime.utcnow().isoformat() + "+00:00"
            }).eq("id", tournament["id"]).execute()
            refresh_global_tournaments()
            screen = app.root.get_screen("tournaments")
            screen.load_tournaments()
        except Exception as exc:
            print("Save live link error:", exc)

    def open_edit(self, tournament):
        app = App.get_running_app()
        if app.root and app.root.has_screen("edit_tournament"):
            app.root.get_screen("edit_tournament").load_tournament(tournament)
            app.root.current = "edit_tournament"

    def confirm_delete(self, tournament):
        from kivy.uix.popup import Popup
        box = BoxLayout(orientation="vertical", padding=dp(15), spacing=dp(10))
        box.add_widget(make_label("Delete this tournament?", font_size=18, color=BLACK, bold=True))
        box.add_widget(make_label(tournament.get("name", "Tournament"), font_size=14, color=GREY))
        row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(48))
        cancel = make_button("CANCEL", background_color=GREY, height=dp(46))
        delete = make_button("DELETE", background_color=RED, height=dp(46))
        row.add_widget(cancel); row.add_widget(delete); box.add_widget(row)
        popup = Popup(title="Confirm Delete", content=box, size_hint=(0.88, None), height=dp(210), auto_dismiss=False)
        cancel.bind(on_release=popup.dismiss)
        delete.bind(on_release=lambda *_: self.delete_tournament(tournament, popup))
        popup.open()

    def delete_tournament(self, tournament, popup):
        try:
            if supabase is None: raise RuntimeError("Supabase is not connected")
            supabase.table("tournaments").delete().eq("id", tournament["id"]).execute()
            popup.dismiss()
            screen = App.get_running_app().root.get_screen("tournaments")
            screen.load_tournaments()
        except Exception as exc:
            print("Delete tournament error:", exc)


class EditTournamentScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_tournament = None
        root = BoxLayout(orientation="vertical")
        header = Card(orientation="horizontal", padding=[dp(10), dp(8)], spacing=dp(8), size_hint_y=None, height=dp(68), background_color=SAFFRON)
        back = make_button("←", background_color=DARK_SAFFRON, font_size=24, height=dp(50)); back.size_hint_x=None; back.width=dp(55)
        back.bind(on_release=lambda *_: setattr(self.manager, "current", "tournaments"))
        header.add_widget(back); header.add_widget(make_label("✏  Edit Tournament", font_size=22, color=WHITE, bold=True, halign="left")); root.add_widget(header)
        scroll = ScrollView(do_scroll_x=False)
        form = BoxLayout(orientation="vertical", padding=[dp(15), dp(12), dp(15), dp(20)], spacing=dp(10), size_hint_y=None); form.bind(minimum_height=form.setter("height"))
        self.name_input = make_text_input("Tournament Name")
        self.organizer_input = make_text_input("Organizer / Association Name")
        self.venue_input = make_text_input("Venue / City")
        form.add_widget(self.name_input); form.add_widget(self.organizer_input); form.add_widget(self.venue_input)
        form.add_widget(make_label("Country", font_size=13, color=GREY, halign="left"))
        self.country_input = SearchableCountrySelector(placeholder="🌍  Select tournament country ▼")
        form.add_widget(self.country_input)
        form.add_widget(make_label("Event Type", font_size=16, color=DARK_SAFFRON, bold=True, halign="left"))
        self.classic = EventTypeRow("Classic"); self.triple = EventTypeRow("Triple"); self.double = EventTypeRow("Double")
        form.add_widget(self.classic); form.add_widget(self.triple); form.add_widget(self.double)
        form.add_widget(make_label("Tournament Dates", font_size=16, color=DARK_SAFFRON, bold=True, halign="left"))
        self.start_input = make_text_input("Start Date"); self.end_input = make_text_input("End Date")
        self.start_input.readonly = True; self.end_input.readonly = True
        self.start_input.bind(on_touch_down=self.start_calendar); self.end_input.bind(on_touch_down=self.end_calendar)
        form.add_widget(self.start_input); form.add_widget(self.end_input)
        self.description_input = TextInput(hint_text="Tournament description / registration information", multiline=True, font_size=15, foreground_color=BLACK, hint_text_color=GREY, background_color=WHITE, padding=[dp(15), dp(12)], size_hint_y=None, height=dp(105))
        form.add_widget(self.description_input)
        self.live_link_input = make_text_input("Live Social Media Link (optional)", height=dp(52))
        form.add_widget(self.live_link_input)
        self.message = make_label("", font_size=13, color=RED, halign="center"); self.message.size_hint_y = None; self.message.height = dp(45); form.add_widget(self.message)
        save = make_button("SAVE CHANGES", background_color=GREEN, height=dp(54)); save.bind(on_release=self.save_changes); form.add_widget(save)
        cancel = make_button("CANCEL", background_color=GREY, height=dp(48)); cancel.bind(on_release=lambda *_: setattr(self.manager, "current", "tournaments")); form.add_widget(cancel)
        scroll.add_widget(form); root.add_widget(scroll); root.add_widget(BottomNavigation(current_screen="tournaments")); self.add_widget(root)

    def load_tournament(self, tournament):
        self.selected_tournament = tournament
        self.name_input.text = tournament.get("name", "")
        organizer = tournament.get("organizer", "")
        self.organizer_input.text = organizer
        self.venue_input.text = tournament.get("venue", "")
        self.country_input.text = tournament.get("country", "")
        types = tournament.get("event_types", [tournament.get("event_type", "Classic")])
        self.classic.checkbox.active = "Classic" in types; self.triple.checkbox.active = "Triple" in types; self.double.checkbox.active = "Double" in types
        self.start_input.text = tournament.get("start", ""); self.end_input.text = tournament.get("end", "")
        self.description_input.text = tournament.get("description", "")
        self.live_link_input.text = tournament.get("live_link", "")
        self.message.text = ""

    def start_calendar(self, instance, touch):
        if instance.collide_point(*touch.pos): CalendarPopup(self.start_input).open(); return True
        return False

    def end_calendar(self, instance, touch):
        if instance.collide_point(*touch.pos): CalendarPopup(self.end_input).open(); return True
        return False

    def save_changes(self, instance):
        app = App.get_running_app()
        role = getattr(app, "current_role", "Player")
        if role not in ("Admin", "Organizer"):
            self.message.text = "Only Admin or Organizer can edit tournaments."; return
        if supabase is None:
            self.message.text = "Supabase is not connected."; return
        if not self.selected_tournament:
            self.message.text = "No tournament selected."; return
        name = self.name_input.text.strip(); organizer = self.organizer_input.text.strip(); venue = self.venue_input.text.strip(); country = self.country_input.text.strip()
        types = []
        if self.classic.checkbox.active: types.append("Classic")
        if self.triple.checkbox.active: types.append("Triple")
        if self.double.checkbox.active: types.append("Double")
        if not name or not organizer or not venue or not country or country == "🌍  Select tournament country ▼" or len(types) != 1 or not self.start_input.text or not self.end_input.text:
            self.message.text = "Please complete all fields and select exactly one Event Type."; return
        try:
            start = datetime.strptime(self.start_input.text, "%d %B %Y").date(); end = datetime.strptime(self.end_input.text, "%d %B %Y").date()
            if end < start: self.message.text = "End Date cannot be before Start Date."; return
        except ValueError:
            self.message.text = "Please select valid dates from the calendar."; return
        try:
            supabase.table("tournaments").update({
                "name": name, "venue": venue, "country": country, "event_type": types[0],
                "start_date": start.isoformat(), "end_date": end.isoformat(),
                "description": self.description_input.text.strip(),
                "organizer_name": organizer,
                "live_link": self.live_link_input.text.strip(),
                "status": calculated_tournament_status(start.isoformat(), end.isoformat()),
                "updated_at": datetime.utcnow().isoformat() + "+00:00"
            }).eq("id", self.selected_tournament["id"]).execute()
            self.message.color = GREEN; self.message.text = "✓ Tournament updated online successfully!"
            Clock.schedule_once(lambda *_: setattr(self.manager, "current", "tournaments"), 0.8)
        except Exception as exc:
            print("Edit tournament error:", exc); self.message.color = RED; self.message.text = "Could not update tournament. Please try again."


class TournamentScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_tab = "Upcoming"
        self.loading_label = None
        root = BoxLayout(orientation="vertical")
        page_header = Card(orientation="horizontal", padding=[dp(12), dp(8)], spacing=dp(8), size_hint_y=None, height=dp(68), background_color=SAFFRON)
        back = make_button("←", background_color=DARK_SAFFRON, font_size=24, height=dp(50)); back.size_hint_x=None; back.width=dp(55); back.bind(on_release=self.go_home)
        page_header.add_widget(back); page_header.add_widget(make_label("🏆  Tournaments", font_size=22, color=WHITE, bold=True, halign="left")); root.add_widget(page_header)
        tabs = BoxLayout(orientation="horizontal", spacing=dp(5), padding=[dp(8), dp(8)], size_hint_y=None, height=dp(58))
        self.tab_buttons = {}
        for name in ("Upcoming", "Ongoing", "Finished"):
            button = make_button(name, background_color=SAFFRON if name == "Upcoming" else LIGHT_GREY, text_color=WHITE if name == "Upcoming" else BLACK, font_size=13, height=dp(44))
            button.bind(on_release=lambda instance, tab=name: self.select_tab(tab)); self.tab_buttons[name] = button; tabs.add_widget(button)
        root.add_widget(tabs)
        action_bar = BoxLayout(orientation="horizontal", spacing=dp(8), padding=[dp(10), dp(2)], size_hint_y=None, height=dp(58))
        self.add_tournament_button = make_button("➕ ADD TOURNAMENT", background_color=SAFFRON, height=dp(48), font_size=11)
        self.add_result_button = make_button("🏆 ADD RESULT", background_color=DARK_SAFFRON, height=dp(48), font_size=11)
        self.add_tournament_button.bind(on_release=self.add_tournament); self.add_result_button.bind(on_release=self.add_result)
        action_bar.add_widget(self.add_tournament_button); action_bar.add_widget(self.add_result_button); root.add_widget(action_bar)
        self.role_message = make_label("", font_size=12, color=GREY, bold=True, halign="center"); self.role_message.size_hint_y = None; self.role_message.height = dp(22); root.add_widget(self.role_message)
        scroll = ScrollView(do_scroll_x=False)
        self.container = BoxLayout(orientation="vertical", padding=[dp(12), dp(5), dp(12), dp(20)], spacing=dp(10), size_hint_y=None); self.container.bind(minimum_height=self.container.setter("height")); scroll.add_widget(self.container); root.add_widget(scroll)
        root.add_widget(BottomNavigation(current_screen="tournaments")); self.add_widget(root)

    def on_pre_enter(self, *args):
        self.update_role_controls(); self.load_tournaments()

    def load_tournaments(self):
        self.container.clear_widgets()
        self.container.add_widget(make_label("Loading tournaments from Supabase…", font_size=14, color=GREY))
        threading.Thread(target=self._load_worker, daemon=True).start()

    def _load_worker(self):
        try:
            tournaments = refresh_global_tournaments()
            Clock.schedule_once(lambda *_: self._show_loaded_tournaments(tournaments), 0)
        except Exception as exc:
            print("Tournament screen load error:", exc)
            Clock.schedule_once(lambda *_: self._show_loaded_tournaments([]), 0)

    def _show_loaded_tournaments(self, tournaments):
        self.container.clear_widgets()
        matches = [t for t in tournaments if t.get("status") == self.current_tab]
        if not matches:
            self.container.add_widget(make_label("No " + self.current_tab.lower() + " tournaments at the moment.", font_size=16, color=GREY))
        else:
            for tournament in matches:
                self.container.add_widget(TournamentCard(tournament))

    def select_tab(self, tab):
        self.current_tab = tab
        for name, button in self.tab_buttons.items():
            active = name == tab; button.background_color = SAFFRON if active else LIGHT_GREY; button.color = WHITE if active else BLACK
        self._show_loaded_tournaments(TOURNAMENTS)

    def update_role_controls(self):
        app = App.get_running_app(); role = getattr(app, "current_role", "Player"); allowed = role in ("Admin", "Organizer")
        self.add_tournament_button.disabled = not allowed; self.add_result_button.disabled = not allowed
        self.add_tournament_button.opacity = 1 if allowed else 0.45; self.add_result_button.opacity = 1 if allowed else 0.45
        if allowed:
            self.role_message.text = f"{role} access: You can manage tournaments and results."; self.role_message.color = GREEN
        else:
            self.role_message.text = "Player access: Tournament management is disabled."; self.role_message.color = GREY

    def add_tournament(self, instance):
        if getattr(App.get_running_app(), "current_role", "Player") in ("Admin", "Organizer"): self.manager.current = "add_tournament"

    def add_result(self, instance):
        if getattr(App.get_running_app(), "current_role", "Player") in ("Admin", "Organizer"): self.manager.current = "add_result"

    def go_home(self, instance):
        if self.manager: self.manager.current = "dashboard"


# ============================================================
# DASHBOARD SCREEN
# ============================================================
# ============================================================

class GateballNewsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._href = ""
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            attrs = dict(attrs)
            self._href = attrs.get("href", "")
            self._text = []

    def handle_data(self, data):
        if self._href:
            self._text.append(data.strip())

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href:
            text = " ".join(x for x in self._text if x).strip()
            if text and self._href:
                self.links.append((text, self._href))
            self._href = ""
            self._text = []


WGU_NEWS_URL = "https://gateball.or.jp/wgu/news/"
JGU_NEWS_URL = "https://gateball.jp/news/"


def fetch_gateball_news(url, source_name, limit=8):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "GateballLovers/1.0 (community news reader)"}
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        html = response.read().decode("utf-8", errors="ignore")
    parser = GateballNewsParser()
    parser.feed(html)
    results = []
    seen = set()
    for title, href in parser.links:
        full = urllib.parse.urljoin(url, href)
        low = full.lower()
        clean_title = " ".join(title.split())
        if len(clean_title) < 8 or clean_title.lower() in {"top", "news", "open", "more"}:
            continue
        if source_name == "WGU" and "/wgu/news" not in low:
            continue
        if source_name == "JGU" and "/news/" not in low:
            continue
        key = (clean_title.lower(), full)
        if key in seen:
            continue
        seen.add(key)
        results.append({"title": clean_title, "url": full, "source": source_name})
        if len(results) >= limit:
            break
    return results


class NewsScreen(Screen):
    """Live Gateball news from official WGU and JGU websites."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical")
        header = Card(orientation="horizontal", padding=[dp(10), dp(8)], spacing=dp(8), size_hint_y=None, height=dp(68), background_color=SAFFRON)
        back = make_button("←", background_color=DARK_SAFFRON, font_size=24, height=dp(50))
        back.size_hint_x = None; back.width = dp(55)
        back.bind(on_release=lambda *_: setattr(self.manager, "current", "dashboard"))
        header.add_widget(back)
        header.add_widget(make_label("📰  Gateball News", font_size=21, color=WHITE, bold=True, halign="left"))
        root.add_widget(header)
        top = BoxLayout(orientation="horizontal", padding=[dp(12), dp(8)], spacing=dp(8), size_hint_y=None, height=dp(55))
        self.status = make_label("Loading official Gateball news…", font_size=12, color=GREY, halign="left")
        refresh = make_button("↻ REFRESH", background_color=DARK_SAFFRON, font_size=11, height=dp(42))
        refresh.size_hint_x = None; refresh.width = dp(100); refresh.bind(on_release=lambda *_: self.load_news())
        top.add_widget(self.status); top.add_widget(refresh); root.add_widget(top)
        scroll = ScrollView(do_scroll_x=False)
        self.list_box = BoxLayout(orientation="vertical", padding=[dp(12), dp(4), dp(12), dp(20)], spacing=dp(9), size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height")); scroll.add_widget(self.list_box); root.add_widget(scroll)
        root.add_widget(BottomNavigation(current_screen="dashboard"))
        self.add_widget(root)

    def on_pre_enter(self, *args):
        self.load_news()

    def load_news(self):
        self.status.color = DARK_SAFFRON; self.status.text = "Loading latest news from WGU and JGU…"
        self.list_box.clear_widgets()
        self.list_box.add_widget(make_label("Please wait…", font_size=14, color=GREY))
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self):
        items = []
        errors = []
        for url, source in ((WGU_NEWS_URL, "WGU"), (JGU_NEWS_URL, "JGU")):
            try:
                items.extend(fetch_gateball_news(url, source, 8))
            except Exception as exc:
                print("Gateball news fetch error:", source, exc); errors.append(source)
        # Prefer newest source order while keeping titles unique.
        unique = []; seen_titles = set()
        for item in items:
            key = item["title"].lower()
            if key not in seen_titles:
                seen_titles.add(key); unique.append(item)
        Clock.schedule_once(lambda *_: self.show_news(unique, errors), 0)

    def show_news(self, items, errors):
        self.list_box.clear_widgets()
        if not items:
            self.status.color = RED
            self.status.text = "Could not load live news. Check your internet connection."
            return
        self.status.color = GREEN
        self.status.text = f"Live official news • {len(items)} articles" + (" • One source unavailable" if errors else "")
        for item in items:
            card = Card(orientation="vertical", padding=[dp(12), dp(9)], spacing=dp(5), size_hint_y=None, height=dp(105), background_color=WHITE)
            card.add_widget(make_label(f"{item['source']}  •  {item['title']}", font_size=14, color=BLACK, bold=True, halign="left"))
            open_btn = make_button("OPEN ARTICLE →", background_color=SAFFRON, font_size=10, height=dp(36))
            open_btn.bind(on_release=lambda *_b, url=item["url"]: webbrowser.open(url))
            card.add_widget(open_btn)
            self.list_box.add_widget(card)


class DashboardScreen(Screen):

    user_email = StringProperty("")
    user_name = StringProperty("Biswa Ranjan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical")

        scroll = ScrollView(do_scroll_x=False)

        main = BoxLayout(
            orientation="vertical",
            padding=[dp(15), dp(15), dp(15), dp(20)],
            spacing=dp(12),
            size_hint_y=None
        )

        main.bind(minimum_height=main.setter("height"))

        # ----------------------------------------------------
        # WELCOME HEADER
        # ----------------------------------------------------

        header = Card(
            orientation="vertical",
            padding=[dp(15), dp(12)],
            spacing=dp(3),
            size_hint_y=None,
            height=dp(138),
            background_color=SAFFRON
        )

        header.add_widget(
            make_label(
                "Gateball Lovers",
                font_size=26,
                color=WHITE,
                bold=True,
                halign="left"
            )
        )

        self.welcome_label = make_label(
            "Welcome, Biswa Ranjan!",
            font_size=21,
            color=WHITE,
            bold=True,
            halign="left"
        )
        header.add_widget(self.welcome_label)

        header.add_widget(
            make_label(
                "Welcome to the Gateball Community.",
                font_size=14,
                color=WHITE,
                halign="left"
            )
        )

        header.add_widget(
            make_label(
                "Connect. Compete. Celebrate.",
                font_size=13,
                color=WHITE,
                bold=True,
                halign="left"
            )
        )

        main.add_widget(header)

        # ----------------------------------------------------
        # PLAYERS / ORGANIZERS CARDS
        # ----------------------------------------------------

        stats = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(125)
        )

        player_card = Card(
            orientation="vertical",
            padding=[dp(8), dp(8)],
            spacing=dp(2),
            background_color=WHITE
        )

        player_card.add_widget(
            make_label("👥", font_size=28, color=DARK_SAFFRON)
        )
        player_card.add_widget(
            make_label(
                "PLAYERS",
                font_size=13,
                color=GREY,
                bold=True
            )
        )
        player_card.add_widget(
            make_label(
                str(len(PLAYERS)),
                font_size=28,
                color=DARK_SAFFRON,
                bold=True
            )
        )
        player_card.add_widget(
            make_label(
                "Tap to view",
                font_size=11,
                color=GREY
            )
        )
        player_card.bind(on_touch_down=self.player_card_touch)

        organizer_card = Card(
            orientation="vertical",
            padding=[dp(8), dp(8)],
            spacing=dp(2),
            background_color=WHITE
        )

        organizer_card.add_widget(
            make_label("🏅", font_size=28, color=DARK_SAFFRON)
        )
        organizer_card.add_widget(
            make_label(
                "ORGANIZERS",
                font_size=13,
                color=GREY,
                bold=True
            )
        )
        organizer_card.add_widget(
            make_label(
                str(len(ORGANIZERS)),
                font_size=28,
                color=DARK_SAFFRON,
                bold=True
            )
        )
        organizer_card.add_widget(
            make_label(
                "Tap to view",
                font_size=11,
                color=GREY
            )
        )
        organizer_card.bind(on_touch_down=self.organizer_card_touch)

        stats.add_widget(player_card)
        stats.add_widget(organizer_card)
        main.add_widget(stats)

        # ----------------------------------------------------
        # UPCOMING TOURNAMENT
        # ----------------------------------------------------

        tournament_card = Card(
            orientation="vertical",
            padding=[dp(15), dp(10)],
            spacing=dp(5),
            size_hint_y=None,
            height=dp(170),
            background_color=WHITE
        )

        tournament_card.add_widget(
            make_label(
                "🏆  UPCOMING TOURNAMENT",
                font_size=17,
                color=DARK_SAFFRON,
                bold=True,
                halign="left"
            )
        )
        self.dashboard_tournament_name = make_label(
            "Loading upcoming tournament…", font_size=21, color=BLACK, bold=True, halign="left"
        )
        self.dashboard_tournament_venue = make_label(
            "", font_size=14, color=GREY, halign="left"
        )
        self.dashboard_tournament_dates = make_label(
            "", font_size=14, color=GREY, halign="left"
        )
        self.dashboard_tournament_type = make_label(
            "", font_size=14, color=DARK_SAFFRON, bold=True, halign="left"
        )
        tournament_card.add_widget(self.dashboard_tournament_name)
        tournament_card.add_widget(self.dashboard_tournament_venue)
        tournament_card.add_widget(self.dashboard_tournament_dates)
        tournament_card.add_widget(self.dashboard_tournament_type)
        tournament_card.add_widget(make_label(
            "Tap here to view ALL upcoming tournaments →",
            font_size=11, color=DARK_SAFFRON, bold=True, halign="center"
        ))
        tournament_card.bind(on_touch_down=self.dashboard_tournament_card_touch)

        main.add_widget(tournament_card)

        # ----------------------------------------------------
        # LIVE TOURNAMENT
        # ----------------------------------------------------

        live_card = Card(
            orientation="vertical",
            padding=[dp(15), dp(10)],
            spacing=dp(5),
            size_hint_y=None,
            height=dp(125),
            background_color=WHITE
        )

        live_card.add_widget(
            make_label(
                "🔴  LIVE TOURNAMENT",
                font_size=17,
                color=RED,
                bold=True,
                halign="left"
            )
        )
        live_card.add_widget(
            make_label(
                "No live match currently",
                font_size=17,
                color=BLACK,
                bold=True,
                halign="left"
            )
        )
        live_card.add_widget(
            make_label(
                "Live scoring and social media links will appear here.",
                font_size=13,
                color=GREY,
                halign="left"
            )
        )

        main.add_widget(live_card)

        # ----------------------------------------------------
        # NEWS
        # ----------------------------------------------------

        news_card = Card(
            orientation="vertical",
            padding=[dp(15), dp(10)],
            spacing=dp(5),
            size_hint_y=None,
            height=dp(155),
            background_color=WHITE
        )

        news_card.add_widget(
            make_label(
                "📰  GATEBALL NEWS",
                font_size=17,
                color=DARK_SAFFRON,
                bold=True,
                halign="left"
            )
        )
        self.news_preview = make_label(
            "Live news from official World Gateball Union and Japan Gateball Union sources.",
            font_size=13,
            color=GREY,
            halign="left"
        )
        news_card.add_widget(self.news_preview)

        news_button = make_button(
            "VIEW LIVE GATEBALL NEWS",
            background_color=SAFFRON,
            height=dp(42)
        )
        news_button.bind(on_release=self.news_message)
        news_card.add_widget(news_button)

        main.add_widget(news_card)

        # ----------------------------------------------------
        # MESSAGE BOARD
        # ----------------------------------------------------

        message_card = Card(
            orientation="vertical",
            padding=[dp(15), dp(10)],
            spacing=dp(5),
            size_hint_y=None,
            height=dp(155),
            background_color=WHITE
        )

        message_card.add_widget(
            make_label(
                "📢  MESSAGE BOARD",
                font_size=17,
                color=DARK_SAFFRON,
                bold=True,
                halign="left"
            )
        )
        self.message_title_label = make_label(
            "Welcome to Gateball Lovers!",
            font_size=17,
            color=BLACK,
            bold=True,
            halign="left"
        )
        message_card.add_widget(self.message_title_label)
        self.message_body_label = make_label(
            "Connect with gateball players and organizers around the world.",
            font_size=13,
            color=GREY,
            halign="left"
        )
        message_card.add_widget(self.message_body_label)
        self.post_message_button = make_button(
            "📢 POST MESSAGE", background_color=DARK_SAFFRON, height=dp(38), font_size=11
        )
        self.post_message_button.bind(on_release=self.open_message_popup)
        message_card.add_widget(self.post_message_button)

        main.add_widget(message_card)

        # ----------------------------------------------------
        # LOGOUT
        # ----------------------------------------------------

        logout_button = make_button(
            "LOGOUT",
            background_color=GREY,
            height=dp(50)
        )
        logout_button.bind(on_release=self.logout)
        main.add_widget(logout_button)

        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        main.add_widget(
            make_label(
                "Gateball Lovers",
                font_size=15,
                color=DARK_SAFFRON,
                bold=True
            )
        )
        main.add_widget(
            make_label(
                "Created by Biswa Ranjan",
                font_size=12,
                color=GREY
            )
        )
        main.add_widget(
            make_label(
                "Connect. Compete. Celebrate.",
                font_size=12,
                color=GREY
            )
        )

        scroll.add_widget(main)
        root.add_widget(scroll)

        # ----------------------------------------------------
        # FIXED BOTTOM NAVIGATION
        # ----------------------------------------------------

        root.add_widget(BottomNavigation(current_screen="dashboard"))

        self.add_widget(root)

    def player_card_touch(self, instance, touch):
        if instance.collide_point(*touch.pos):
            if self.manager:
                self.manager.current = "players"
            return True
        return False

    def organizer_card_touch(self, instance, touch):
        if instance.collide_point(*touch.pos):
            if self.manager:
                self.manager.current = "organizers"
            return True
        return False

    def set_user_email(self, email):
        self.user_email = email

        if email:
            local_part = email.split("@")[0].strip()
            if local_part:
                display_name = local_part.replace(".", " ").replace("_", " ")
                self.user_name = display_name.title()

        self.welcome_label.text = f"Welcome, {self.user_name}!"

    def go_home(self):
        if self.manager:
            self.manager.current = "dashboard"

    def open_feature(self, screen_name):
        if self.manager:
            self.manager.current = screen_name

    def on_pre_enter(self, *args):
        self.load_dashboard_message()
        self.update_role_controls()
        self.load_dashboard_tournament()

    def dashboard_tournament_card_touch(self, instance, touch):
        if instance.collide_point(*touch.pos):
            if self.manager:
                self.manager.current = "tournaments"
                # TournamentScreen.on_pre_enter() always reloads and selects Upcoming.
            return True
        return False

    def load_dashboard_tournament(self):
        if not hasattr(self, "dashboard_tournament_name"):
            return
        self.dashboard_tournament_name.text = "Loading upcoming tournament…"
        self.dashboard_tournament_venue.text = ""
        self.dashboard_tournament_dates.text = ""
        self.dashboard_tournament_type.text = ""
        threading.Thread(target=self._dashboard_tournament_worker, daemon=True).start()

    def _dashboard_tournament_worker(self):
        try:
            tournaments = refresh_global_tournaments()
            upcoming = [t for t in tournaments if t.get("status") == "Upcoming"]
            upcoming.sort(key=lambda t: datetime.strptime(t.get("start", "31 December 2999"), "%d %B %Y"))
            tournament = upcoming[0] if upcoming else None
            Clock.schedule_once(lambda *_: self._show_dashboard_tournament(tournament), 0)
        except Exception as exc:
            print("Dashboard tournament load error:", exc)
            Clock.schedule_once(lambda *_: self._show_dashboard_tournament(None), 0)

    def _show_dashboard_tournament(self, tournament):
        if not hasattr(self, "dashboard_tournament_name"):
            return
        if not tournament:
            self.dashboard_tournament_name.text = "No upcoming tournament"
            self.dashboard_tournament_venue.text = ""
            self.dashboard_tournament_dates.text = ""
            self.dashboard_tournament_type.text = "Open the Tournaments page to view all events."
            return
        self.dashboard_tournament_name.text = tournament.get("name", "Tournament")
        self.dashboard_tournament_venue.text = "📍 " + tournament.get("venue", "") + (", " + tournament.get("country", "") if tournament.get("country") else "")
        self.dashboard_tournament_dates.text = "📅 " + tournament.get("start", "") + " - " + tournament.get("end", "")
        self.dashboard_tournament_type.text = "Event: " + (tournament.get("event_type") or "")

    def update_role_controls(self):
        role = str(getattr(App.get_running_app(), "current_role", "Player") or "Player")
        allowed = role in ("Admin", "Organizer")
        if hasattr(self, "post_message_button"):
            self.post_message_button.disabled = not allowed
            self.post_message_button.text = "📢 POST MESSAGE" if allowed else "📢 ADMIN / ORGANIZER ONLY"
            self.post_message_button.background_color = DARK_SAFFRON if allowed else GREY

    def news_message(self, instance):
        if self.manager:
            self.manager.current = "news"

    def load_dashboard_message(self):
        if supabase is None or not hasattr(self, "message_title_label"):
            return
        try:
            rows = (supabase.table("community_messages").select("id,title,message,created_at").eq("is_active", True).order("created_at", desc=True).limit(1).execute().data or [])
            if rows:
                row = rows[0]
                self.message_title_label.text = "📢  " + (row.get("title") or "Community Message")
                self.message_body_label.text = row.get("message") or ""
            else:
                self.message_title_label.text = "Welcome to Gateball Lovers!"
                self.message_body_label.text = "Connect with gateball players and organizers around the world."
        except Exception as exc:
            print("Message board load error:", exc)

    def open_message_popup(self, instance):
        from kivy.uix.popup import Popup
        role = str(getattr(App.get_running_app(), "current_role", "Player") or "Player")
        if role not in ("Admin", "Organizer"):
            return
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        title = make_text_input("Message title", height=dp(45))
        body = make_text_input("Write your message…", height=dp(120))
        body.multiline = True
        status = make_label("", font_size=11, color=GREY, halign="center")
        actions = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(46))
        cancel = make_button("CANCEL", background_color=GREY, height=dp(44))
        post = make_button("POST", background_color=GREEN, height=dp(44))
        actions.add_widget(cancel); actions.add_widget(post)
        box.add_widget(make_label("📢  Post to Message Board", font_size=19, color=DARK_SAFFRON, bold=True))
        box.add_widget(title); box.add_widget(body); box.add_widget(status); box.add_widget(actions)
        popup = Popup(title="Gateball Lovers Message Board", content=box, size_hint=(0.92, None), height=dp(390), auto_dismiss=False)
        cancel.bind(on_release=popup.dismiss)

        def save_message(*_):
            t = title.text.strip(); m = body.text.strip()
            if len(t) < 2 or len(m) < 2:
                status.color = RED; status.text = "Please enter a title and message."; return
            app = App.get_running_app(); uid = str(getattr(app, "current_user_id", "") or "")
            if not uid or supabase is None:
                status.color = RED; status.text = "Please log in and check Supabase."; return
            try:
                supabase.table("community_messages").insert({"author_id": uid, "title": t, "message": m, "is_active": True}).execute()
                status.color = GREEN; status.text = "Message posted ✓"
                self.load_dashboard_message()
                Clock.schedule_once(lambda *_: popup.dismiss(), 0.7)
            except Exception as exc:
                print("Message board post error:", exc)
                status.color = RED; status.text = "Could not post message. Run the message board SQL."
        post.bind(on_release=save_message)
        popup.open()

    def logout(self, instance):
        app = App.get_running_app()

        try:
            app.stop_realtime()
            if supabase is not None:
                supabase.auth.sign_out()
        except Exception as exc:
            print("Supabase logout error:", exc)

        app.current_role = "Player"
        app.current_user_id = ""
        app.current_user_name = ""
        app.current_user_email = ""
        app.current_user_country = ""
        app.current_user_phone = ""
        app.current_user_photo = ""

        if self.manager:
            self.manager.current = "login"


# ============================================================
# COMMUNITY PROFILES
# ============================================================

class CommunityMemberCard(Card):

    def __init__(self, person, **kwargs):
        self.person = person
        super().__init__(
            orientation="horizontal",
            padding=[dp(10), dp(8)],
            spacing=dp(12),
            size_hint_y=None,
            height=dp(88),
            background_color=WHITE,
            **kwargs
        )

        photo_holder = BoxLayout(size_hint=(None, 1), width=dp(64))
        photo_url = person.get("photo_url") or ""
        photo_path = ""

        if photo_url:
            photo_path = download_profile_photo(photo_url, person.get("id", "member"))

        if photo_path and os.path.exists(photo_path):
            photo = CircularImage(
                source=photo_path,
                size_hint=(None, None),
                size=(dp(60), dp(60)),
                pos_hint={"center_y": 0.5}
            )
        else:
            photo = make_label("👤", font_size=34, color=DARK_SAFFRON)

        photo_holder.add_widget(photo)
        self.add_widget(photo_holder)

        details = BoxLayout(orientation="vertical", spacing=dp(1))
        name = person.get("full_name") or "Gateball User"
        country = person.get("country") or "Country not set"
        role = person.get("role") or "Player"

        details.add_widget(make_label(name, font_size=17, color=BLACK, bold=True, halign="left"))
        details.add_widget(make_label(country_flag(country) + "  " + country, font_size=13, color=GREY, halign="left"))
        details.add_widget(make_label("🏆  " + role, font_size=13, color=DARK_SAFFRON, halign="left"))
        online = bool(person.get("_online", False))
        status_text = "🟢  Online" if online else "⚪  Offline"
        status_color = GREEN if online else GREY
        details.add_widget(make_label(status_text + "   •   Tap to view profile", font_size=10, color=status_color, halign="left"))
        self.add_widget(details)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            try:
                # Walk upward until we find the actual Screen.
                # The previous fixed parent chain stopped at the root BoxLayout,
                # so .manager was None and the member profile never opened.
                widget = self
                screen = None
                while widget is not None:
                    if isinstance(widget, Screen):
                        screen = widget
                        break
                    widget = widget.parent

                manager = screen.manager if screen else None
                if manager:
                    profile_screen = manager.get_screen("member_profile")
                    profile_screen.set_member(self.person)
                    manager.current = "member_profile"
                    return True
            except Exception as exc:
                print("Open member profile error:", exc)
        return super().on_touch_up(touch)


class CommunityProfilesScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.members = []

        root = BoxLayout(orientation="vertical")

        header = Card(
            orientation="horizontal",
            padding=[dp(10), dp(8)],
            spacing=dp(8),
            size_hint_y=None,
            height=dp(68),
            background_color=SAFFRON
        )
        back = make_button("←", background_color=DARK_SAFFRON, font_size=24, height=dp(50))
        back.size_hint_x = None
        back.width = dp(55)
        back.bind(on_release=lambda *_: setattr(self.manager, "current", "profile"))
        header.add_widget(back)
        header.add_widget(make_label("🌍  Gateball Community", font_size=20, color=WHITE, bold=True, halign="left"))
        root.add_widget(header)

        top = BoxLayout(orientation="vertical", padding=[dp(12), dp(8), dp(12), dp(4)], spacing=dp(7), size_hint_y=None, height=dp(105))
        self.count_label = make_label("Loading members...", font_size=14, color=GREY, halign="left")
        top.add_widget(self.count_label)

        search_row = BoxLayout(orientation="horizontal", spacing=dp(7), size_hint_y=None, height=dp(45))
        self.search_input = make_text_input("Search name or country")
        self.search_input.bind(text=lambda *_: self.refresh_display())
        refresh = make_button("↻", background_color=DARK_SAFFRON, font_size=22, height=dp(45))
        refresh.size_hint_x = None
        refresh.width = dp(55)
        refresh.bind(on_release=self.load_members)
        search_row.add_widget(self.search_input)
        search_row.add_widget(refresh)
        top.add_widget(search_row)
        root.add_widget(top)

        scroll = ScrollView(do_scroll_x=False)
        self.list_container = BoxLayout(
            orientation="vertical",
            padding=[dp(12), dp(6), dp(12), dp(20)],
            spacing=dp(9),
            size_hint_y=None
        )
        self.list_container.bind(minimum_height=self.list_container.setter("height"))
        scroll.add_widget(self.list_container)
        root.add_widget(scroll)

        self.message = make_label("", font_size=12, color=GREY, halign="center")
        self.message.size_hint_y = None
        self.message.height = dp(28)
        root.add_widget(self.message)

        self.add_widget(root)

    def on_pre_enter(self, *args):
        self.load_members()

    def load_members(self, *args):
        if supabase is None:
            self.count_label.text = "Supabase is not connected."
            return

        self.count_label.text = "Loading community members..."
        self.message.text = ""
        try:
            response = (
                supabase.table("community_profiles")
                .select("id, full_name, role, country, photo_url")
                .order("full_name")
                .execute()
            )
            self.members = response.data or []
            self.refresh_display()
        except Exception as exc:
            print("Community profiles error:", exc)
            self.members = []
            self.list_container.clear_widgets()
            self.count_label.text = "Could not load community members."
            self.message.color = RED
            self.message.text = "Create the community_profiles view in Supabase first."

    def refresh_display(self, *args):
        self.list_container.clear_widgets()
        query = self.search_input.text.strip().lower() if hasattr(self, "search_input") else ""
        filtered = []
        for person in self.members:
            name = (person.get("full_name") or "").lower()
            country = (person.get("country") or "").lower()
            if not query or query in name or query in country:
                filtered.append(person)

        self.count_label.text = f"{len(filtered)} member(s) shown • {len(self.members)} total"

        if not filtered:
            self.list_container.add_widget(make_label(
                "No community members found.",
                font_size=15,
                color=GREY,
                halign="center"
            ))
            return

        for person in filtered:
            self.list_container.add_widget(CommunityMemberCard(person))


class MemberProfileScreen(Screen):
    """Full public profile for another community member."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.member = {}
        self.liked = False
        self.like_count = 0

        root = BoxLayout(orientation="vertical")
        header = Card(orientation="horizontal", padding=[dp(10), dp(8)], spacing=dp(8), size_hint_y=None, height=dp(68), background_color=SAFFRON)
        back = make_button("←", background_color=DARK_SAFFRON, font_size=24, height=dp(50))
        back.size_hint_x = None
        back.width = dp(55)
        back.bind(on_release=lambda *_: setattr(self.manager, "current", "profile"))
        header.add_widget(back)
        header.add_widget(make_label("👤  Member Profile", font_size=21, color=WHITE, bold=True, halign="left"))
        root.add_widget(header)

        scroll = ScrollView(do_scroll_x=False)
        form = BoxLayout(orientation="vertical", padding=[dp(18), dp(18), dp(18), dp(25)], spacing=dp(12), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))

        self.photo = CircularImage(source="", size_hint=(None, None), size=(dp(230), dp(230)), pos_hint={"center_x": 0.5})
        form.add_widget(self.photo)
        self.name_label = make_label("", font_size=26, color=BLACK, bold=True)
        form.add_widget(self.name_label)
        self.country_label = make_label("", font_size=18, color=GREY)
        form.add_widget(self.country_label)
        self.role_label = make_label("", font_size=16, color=DARK_SAFFRON, bold=True)
        form.add_widget(self.role_label)

        self.like_button = make_button("♡  LIKE PROFILE", background_color=SAFFRON, height=dp(54), font_size=16)
        self.like_button.bind(on_release=self.toggle_like)
        form.add_widget(self.like_button)

        self.like_count_label = make_label("0 likes", font_size=13, color=GREY)
        form.add_widget(self.like_count_label)

        chat_button = make_button("💬  CHAT WITH THIS MEMBER", background_color=GREEN, height=dp(54), font_size=15)
        chat_button.bind(on_release=self.open_chat)
        form.add_widget(chat_button)

        self.message = make_label("", font_size=12, color=GREY, halign="center")
        self.message.size_hint_y = None
        self.message.height = dp(42)
        form.add_widget(self.message)

        privacy = make_label("Only photo, name, country and role are shown here.\nEmail and phone remain private.", font_size=12, color=GREY, halign="center")
        privacy.size_hint_y = None
        privacy.height = dp(50)
        form.add_widget(privacy)

        scroll.add_widget(form)
        root.add_widget(scroll)
        self.add_widget(root)

    def set_member(self, member):
        self.member = member or {}
        app = App.get_running_app()
        member_id = str(self.member.get("id") or "")
        my_id = str(getattr(app, "current_user_id", "") or "")

        self.name_label.text = self.member.get("full_name") or "Gateball User"
        self.country_label.text = "🌍  " + (self.member.get("country") or "Country not set")
        self.role_label.text = "🏆  " + (self.member.get("role") or "Player")
        self.message.text = ""

        photo_url = self.member.get("photo_url") or ""
        if photo_url:
            local = download_profile_photo(photo_url, member_id)
            if local:
                self.photo.source = local
                self.photo.reload()
            else:
                self.photo.source = ""
        else:
            self.photo.source = ""

        # A member cannot like their own profile.
        self.like_button.disabled = (not member_id or member_id == my_id)
        if member_id == my_id:
            self.like_button.text = "♡  THIS IS YOUR PROFILE"
        else:
            self.like_button.text = "♡  LIKE PROFILE"
        self.load_likes()

    def load_likes(self):
        if supabase is None:
            return
        member_id = str(self.member.get("id") or "")
        my_id = str(getattr(App.get_running_app(), "current_user_id", "") or "")
        if not member_id:
            return
        try:
            response = supabase.table("profile_likes").select("user_id").eq("profile_id", member_id).execute()
            rows = response.data or []
            self.like_count = len(rows)
            self.liked = any(str(row.get("user_id")) == my_id for row in rows)
            self.like_count_label.text = f"{self.like_count} like(s)"
            if not self.like_button.disabled:
                self.like_button.text = "♥  UNLIKE PROFILE" if self.liked else "♡  LIKE PROFILE"
        except Exception as exc:
            print("Profile likes load error:", exc)

    def toggle_like(self, instance):
        if supabase is None:
            self.message.color = RED
            self.message.text = "Supabase is not connected."
            return
        app = App.get_running_app()
        member_id = str(self.member.get("id") or "")
        my_id = str(getattr(app, "current_user_id", "") or "")
        if not member_id or not my_id or member_id == my_id:
            return
        try:
            if self.liked:
                supabase.table("profile_likes").delete().eq("profile_id", member_id).eq("user_id", my_id).execute()
                self.liked = False
                self.like_count = max(0, self.like_count - 1)
            else:
                supabase.table("profile_likes").insert({"profile_id": member_id, "user_id": my_id}).execute()
                self.liked = True
                self.like_count += 1
            self.like_count_label.text = f"{self.like_count} like(s)"
            self.like_button.text = "♥  UNLIKE PROFILE" if self.liked else "♡  LIKE PROFILE"
            self.message.color = GREEN
            self.message.text = "Profile like updated."
        except Exception as exc:
            print("Profile like error:", exc)
            self.message.color = RED
            self.message.text = "Could not update like. Run the profile_likes SQL first."

    def open_chat(self, instance):
        if not self.member:
            return
        self.manager.get_screen("direct_chat").set_member(self.member)
        self.manager.current = "direct_chat"


class ChatHomeScreen(Screen):
    """All community members plus one global Gateball Lovers group chat."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.members=[]
        self.online_ids=set()
        self.realtime_channel=None
        root=BoxLayout(orientation="vertical")
        header=Card(orientation="horizontal",padding=[dp(10),dp(8)],spacing=dp(8),size_hint_y=None,height=dp(68),background_color=SAFFRON)
        header.add_widget(make_label("💬  Chat",font_size=23,color=WHITE,bold=True,halign="left")); root.add_widget(header)
        scroll=ScrollView(do_scroll_x=False)
        self.content=BoxLayout(orientation="vertical",padding=[dp(12),dp(10),dp(12),dp(20)],spacing=dp(9),size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter("height")); scroll.add_widget(self.content); root.add_widget(scroll)
        root.add_widget(BottomNavigation(current_screen="chat")); self.add_widget(root)

    def on_pre_enter(self,*args):
        self.load_chat_data()
        self.subscribe_group_realtime()

    def on_leave(self,*args):
        self.unsubscribe_realtime()

    def subscribe_group_realtime(self):
        if supabase is None or self.realtime_channel is not None:
            return
        app=App.get_running_app()
        if not getattr(app,"current_user_id",""):
            return
        try:
            app.setup_realtime_auth()
            self.realtime_channel=(supabase.channel("gateball-global-chat")
                .on_postgres_changes(
                    "INSERT", schema="public", table="community_group_messages",
                    callback=self._on_group_realtime
                )
                .subscribe())
            print("Global group chat realtime subscribed.")
        except Exception as exc:
            print("Global group realtime subscription error:",exc)
            self.realtime_channel=None

    def unsubscribe_realtime(self):
        if self.realtime_channel is not None:
            try:
                supabase.remove_channel(self.realtime_channel)
            except Exception:
                try:
                    self.realtime_channel.unsubscribe()
                except Exception:
                    pass
            self.realtime_channel=None

    def _on_group_realtime(self,payload):
        row=realtime_record(payload)
        if not row:
            return
        Clock.schedule_once(lambda *_: self._refresh_group_after_realtime(),0)

    def _refresh_group_after_realtime(self):
        if self.manager and self.manager.current=="chat":
            self.load_group_messages()

    def load_chat_data(self,*args):
        if supabase is None: return
        my_id=str(getattr(App.get_running_app(),"current_user_id","") or "")
        if not my_id: return
        try:
            self.members=(supabase.table("community_profiles").select("id, full_name, role, country, photo_url").order("full_name").execute().data or [])
            presence=(supabase.table("user_presence").select("user_id,last_seen").execute().data or [])
            self.online_ids={str(r.get("user_id")) for r in presence if presence_is_online(r.get("last_seen"))}
            self.render()
        except Exception as exc:
            print("Chat data load error:",exc)
            self.content.clear_widgets(); self.content.add_widget(make_label("Chat setup is not complete. Run the Chat SQL first.",font_size=13,color=RED))

    def render(self):
        self.content.clear_widgets(); my_id=str(getattr(App.get_running_app(),"current_user_id","") or "")
        self.content.add_widget(make_label("🌍  ALL MEMBERS",font_size=17,color=DARK_SAFFRON,bold=True,halign="left"))
        self.content.add_widget(make_label("Chat privately with any member — online or offline.",font_size=12,color=GREY,halign="left"))
        for person in self.members: self.content.add_widget(self.make_member_row(person,my_id))
        if not self.members: self.content.add_widget(make_label("No community members found yet.",font_size=14,color=GREY))
        self.content.add_widget(Spacer(height=dp(8)))
        self.content.add_widget(make_label("🌎  GATEBALL LOVERS GLOBAL CHAT",font_size=17,color=DARK_SAFFRON,bold=True,halign="left"))
        self.content.add_widget(make_label("New messages appear automatically.",font_size=12,color=GREY,halign="left"))
        self.group_box=BoxLayout(orientation="vertical",spacing=dp(7),size_hint_y=None); self.group_box.bind(minimum_height=self.group_box.setter("height")); self.content.add_widget(self.group_box)
        row=BoxLayout(orientation="horizontal",spacing=dp(7),size_hint_y=None,height=dp(50))
        self.group_input=make_text_input("Write to everyone…",height=dp(46)); send=make_button("SEND",background_color=GREEN,font_size=12,height=dp(46)); send.size_hint_x=None; send.width=dp(72); send.bind(on_release=self.send_group_message)
        row.add_widget(self.group_input); row.add_widget(send); self.content.add_widget(row)
        self.group_status=make_label("",font_size=11,color=GREY,halign="center"); self.group_status.size_hint_y=None; self.group_status.height=dp(24); self.content.add_widget(self.group_status)
        self.load_group_messages()

    def make_member_row(self,person,my_id):
        card=Card(orientation="horizontal",padding=[dp(9),dp(7)],spacing=dp(9),size_hint_y=None,height=dp(74),background_color=WHITE)
        photo_url=person.get("photo_url") or ""; path=download_profile_photo(photo_url,person.get("id","member")) if photo_url else ""
        photo=CircularImage(source=path,size_hint=(None,None),size=(dp(52),dp(52)),pos_hint={"center_y":.5}) if path and os.path.exists(path) else make_label("👤",font_size=30,color=DARK_SAFFRON)
        holder=BoxLayout(size_hint=(None,1),width=dp(55)); holder.add_widget(photo); card.add_widget(holder)
        info=BoxLayout(orientation="vertical",spacing=dp(1)); name=person.get("full_name") or "Gateball User"; online=str(person.get("id")) in self.online_ids
        info.add_widget(make_label(name,font_size=16,color=BLACK,bold=True,halign="left")); info.add_widget(make_label(country_flag(person.get("country")),font_size=16,color=BLACK,halign="left")); info.add_widget(make_label("Online" if online else "Offline",font_size=10,color=GREEN if online else GREY,halign="left")); card.add_widget(info)
        b=make_button("CHAT" if str(person.get("id"))!=my_id else "YOU",background_color=SAFFRON if str(person.get("id"))!=my_id else GREY,font_size=11,height=dp(40)); b.size_hint_x=None; b.width=dp(62); b.disabled=str(person.get("id"))==my_id
        b.bind(on_release=lambda *_p,m=person:self.open_direct(m)); card.add_widget(b); return card

    def open_direct(self,member):
        screen=self.manager.get_screen("direct_chat"); screen.set_member(member); self.manager.current="direct_chat"

    def load_group_messages(self):
        if not hasattr(self,"group_box") or supabase is None: return
        try:
            rows=(supabase.table("community_group_messages").select("id,sender_id,message,created_at").order("created_at").limit(100).execute().data or [])
            self.group_box.clear_widgets(); members={str(m.get("id")):m for m in self.members}; my_id=str(getattr(App.get_running_app(),"current_user_id","") or "")
            if not rows: self.group_box.add_widget(make_label("No group messages yet. Start the conversation! 👋",font_size=13,color=GREY,halign="left")); return
            for r in rows:
                sender=members.get(str(r.get("sender_id")),{}); bubble=Card(orientation="vertical",padding=[dp(9),dp(7)],size_hint_y=None,height=dp(62),background_color=LIGHT_SAFFRON if str(r.get("sender_id"))==my_id else WHITE)
                bubble.add_widget(make_label(f"{country_flag(sender.get('country'))}  {sender.get('full_name') or 'Gateball Member'}",font_size=11,color=DARK_SAFFRON,bold=True,halign="left")); bubble.add_widget(make_label(r.get("message") or "",font_size=13,color=BLACK,halign="left")); self.group_box.add_widget(bubble)
        except Exception as exc:
            print("Global chat load error:",exc); self.group_box.clear_widgets(); self.group_box.add_widget(make_label("Global chat is not ready. Run the community_group_messages SQL first.",font_size=12,color=RED,halign="left"))

    def send_group_message(self,instance):
        app=App.get_running_app(); my_id=str(getattr(app,"current_user_id","") or ""); text=self.group_input.text.strip()
        if not text or not my_id: return
        try:
            supabase.table("community_group_messages").insert({"sender_id":my_id,"message":text}).execute(); self.group_input.text=""; self.group_status.color=GREEN; self.group_status.text="Message sent ✓"
        except Exception as exc:
            print("Global chat send error:",exc); self.group_status.color=RED; self.group_status.text="Could not send. Check Chat table permissions."


class DirectChatScreen(Screen):
    """Private one-to-one chat with Supabase Realtime INSERT updates."""
    def __init__(self,**kwargs):
        super().__init__(**kwargs); self.member={}; self.realtime_channel=None
        root=BoxLayout(orientation="vertical"); header=Card(orientation="horizontal",padding=[dp(10),dp(8)],spacing=dp(8),size_hint_y=None,height=dp(68),background_color=SAFFRON)
        back=make_button("←",background_color=DARK_SAFFRON,font_size=24,height=dp(50)); back.size_hint_x=None; back.width=dp(55); back.bind(on_release=self.go_back); header.add_widget(back)
        self.header_label=make_label("💬  Chat",font_size=20,color=WHITE,bold=True,halign="left"); header.add_widget(self.header_label); root.add_widget(header)
        scroll=ScrollView(do_scroll_x=False); self.messages_box=BoxLayout(orientation="vertical",padding=[dp(12),dp(10)],spacing=dp(8),size_hint_y=None); self.messages_box.bind(minimum_height=self.messages_box.setter("height")); scroll.add_widget(self.messages_box); self.scroll=scroll; root.add_widget(scroll)
        row=BoxLayout(orientation="horizontal",padding=[dp(8),dp(7)],spacing=dp(7),size_hint_y=None,height=dp(58)); self.input=make_text_input("Write a message…",height=dp(44)); send=make_button("SEND",background_color=GREEN,height=dp(44),font_size=12); send.size_hint_x=None; send.width=dp(70); send.bind(on_release=self.send_message); row.add_widget(self.input); row.add_widget(send); root.add_widget(row)
        self.status=make_label("",font_size=11,color=GREY,halign="center"); self.status.size_hint_y=None; self.status.height=dp(24); root.add_widget(self.status); self.add_widget(root)

    def on_pre_enter(self,*args):
        self.load_messages()
        self.subscribe_direct_realtime()

    def on_leave(self,*args):
        self.unsubscribe_realtime()

    def subscribe_direct_realtime(self):
        if supabase is None or self.realtime_channel is not None or not self.member:
            return
        app=App.get_running_app(); my_id=str(getattr(app,"current_user_id","") or ""); other_id=str(self.member.get("id") or "")
        if not my_id or not other_id or my_id==other_id:
            return
        try:
            app.setup_realtime_auth()
            channel_name="direct-chat-"+"-".join(sorted([my_id,other_id]))
            channel=supabase.channel(channel_name)
            channel=channel.on_postgres_changes("INSERT",schema="public",table="direct_messages",filter=f"sender_id=eq.{other_id}",callback=self._on_direct_realtime)
            channel=channel.on_postgres_changes("INSERT",schema="public",table="direct_messages",filter=f"receiver_id=eq.{other_id}",callback=self._on_direct_realtime)
            self.realtime_channel=channel.subscribe()
            print("Direct chat realtime subscribed:",channel_name)
        except Exception as exc:
            print("Direct chat realtime subscription error:",exc); self.realtime_channel=None

    def unsubscribe_realtime(self):
        if self.realtime_channel is not None:
            try:
                supabase.remove_channel(self.realtime_channel)
            except Exception:
                try: self.realtime_channel.unsubscribe()
                except Exception: pass
            self.realtime_channel=None

    def _on_direct_realtime(self,payload):
        row=realtime_record(payload)
        if not row:
            return
        app=App.get_running_app(); my_id=str(getattr(app,"current_user_id","") or ""); other_id=str(self.member.get("id") or "")
        if {str(row.get("sender_id")),str(row.get("receiver_id"))}!={my_id,other_id}:
            return
        Clock.schedule_once(lambda *_: self._refresh_direct_after_realtime(),0)

    def _refresh_direct_after_realtime(self):
        if self.manager and self.manager.current=="direct_chat":
            self.load_messages()

    def go_back(self,*args): self.manager.current="chat"
    def set_member(self,member):
        self.unsubscribe_realtime()
        self.member=member or {}; self.header_label.text=f"💬  {country_flag(self.member.get('country'))}  {self.member.get('full_name') or 'Member'}"

    def load_messages(self,*args):
        self.messages_box.clear_widgets(); app=App.get_running_app(); my_id=str(getattr(app,"current_user_id","") or ""); other_id=str(self.member.get("id") or "")
        if not my_id or not other_id or supabase is None: self.messages_box.add_widget(make_label("Please log in to use chat.",font_size=14,color=GREY)); return
        if my_id==other_id: self.messages_box.add_widget(make_label("You cannot start a private chat with yourself.",font_size=14,color=GREY)); return
        try:
            first=supabase.table("direct_messages").select("id,sender_id,receiver_id,message,created_at").eq("sender_id",my_id).eq("receiver_id",other_id).execute().data or []
            second=supabase.table("direct_messages").select("id,sender_id,receiver_id,message,created_at").eq("sender_id",other_id).eq("receiver_id",my_id).execute().data or []
            rows=sorted(first+second,key=lambda x:x.get("created_at") or "")
            if not rows: self.messages_box.add_widget(make_label("No messages yet. Say hello! 👋",font_size=14,color=GREY))
            else:
                for r in rows:
                    mine=str(r.get("sender_id"))==my_id; bubble=Card(orientation="vertical",padding=[dp(10),dp(7)],size_hint_y=None,height=dp(58),background_color=LIGHT_SAFFRON if mine else WHITE)
                    bubble.add_widget(make_label(r.get("message") or "",font_size=14,color=BLACK,halign="left")); bubble.add_widget(make_label("You" if mine else (self.member.get("full_name") or "Member"),font_size=10,color=GREY,halign="left")); self.messages_box.add_widget(bubble)
            Clock.schedule_once(lambda *_: setattr(self.scroll,"scroll_y",0),.05)
        except Exception as exc:
            print("Direct chat load error:",exc); self.messages_box.add_widget(make_label("Chat is not ready. Check direct_messages permissions.",font_size=13,color=RED))

    def send_message(self,instance):
        app=App.get_running_app(); my_id=str(getattr(app,"current_user_id","") or ""); other_id=str(self.member.get("id") or ""); text=self.input.text.strip()
        if not text or not my_id or not other_id or my_id==other_id: return
        try:
            supabase.table("direct_messages").insert({"sender_id":my_id,"receiver_id":other_id,"message":text}).execute(); self.input.text=""; self.status.color=GREEN; self.status.text="Message sent ✓"
        except Exception as exc:
            print("Direct chat send error:",exc); self.status.color=RED; self.status.text="Message failed. Check direct_messages permissions."


# ============================================================
# PROFILE SCREEN
# ============================================================

class ProfileScreen(Screen):
    """Community-first Profile tab. Shows registered members; MY PROFILE opens the private editable profile."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.members = []
        self.online_ids = set()

        root = BoxLayout(orientation="vertical")
        header = Card(orientation="horizontal", padding=[dp(10), dp(8)], spacing=dp(8),
                      size_hint_y=None, height=dp(68), background_color=SAFFRON)
        header.add_widget(make_label("👥  Gateball Community", font_size=20, color=WHITE, bold=True, halign="left"))
        my_button = make_button("👤 MY PROFILE", background_color=DARK_SAFFRON, font_size=11, height=dp(46))
        my_button.size_hint_x = None
        my_button.width = dp(112)
        my_button.bind(on_release=lambda *_: setattr(self.manager, "current", "my_profile"))
        header.add_widget(my_button)
        root.add_widget(header)

        top = BoxLayout(orientation="vertical", padding=[dp(12), dp(8), dp(12), dp(4)], spacing=dp(7),
                        size_hint_y=None, height=dp(105))
        self.count_label = make_label("Loading members...", font_size=14, color=GREY, halign="left")
        top.add_widget(self.count_label)
        search_row = BoxLayout(orientation="horizontal", spacing=dp(7), size_hint_y=None, height=dp(45))
        self.search_input = make_text_input("Search name or country")
        self.search_input.bind(text=lambda *_: self.refresh_display())
        refresh = make_button("↻", background_color=DARK_SAFFRON, font_size=22, height=dp(45))
        refresh.size_hint_x = None; refresh.width = dp(55)
        refresh.bind(on_release=self.load_members)
        search_row.add_widget(self.search_input); search_row.add_widget(refresh); top.add_widget(search_row)
        root.add_widget(top)

        scroll = ScrollView(do_scroll_x=False)
        self.list_container = BoxLayout(orientation="vertical", padding=[dp(12), dp(6), dp(12), dp(20)],
                                        spacing=dp(9), size_hint_y=None)
        self.list_container.bind(minimum_height=self.list_container.setter("height"))
        scroll.add_widget(self.list_container); root.add_widget(scroll)
        self.message = make_label("", font_size=12, color=GREY, halign="center")
        self.message.size_hint_y = None; self.message.height = dp(28)
        root.add_widget(self.message)
        root.add_widget(BottomNavigation(current_screen="profile"))
        self.add_widget(root)

    def on_pre_enter(self, *args):
        self.load_members()

    def load_members(self, *args):
        if supabase is None:
            self.count_label.text = "Supabase is not connected."; return
        try:
            response = (supabase.table("community_profiles")
                        .select("id, full_name, role, country, photo_url")
                        .order("full_name").execute())
            self.members = response.data or []
            self.online_ids = set()
            try:
                presence = supabase.table("user_presence").select("user_id, last_seen").execute().data or []
                self.online_ids = {str(r.get("user_id")) for r in presence if presence_is_online(r.get("last_seen"))}
            except Exception as exc:
                print("Profile presence load error:", exc)
            for person in self.members:
                person["_online"] = str(person.get("id")) in self.online_ids
            self.refresh_display()
        except Exception as exc:
            print("Profile community load error:", exc)
            self.members = []; self.list_container.clear_widgets()
            self.count_label.text = "Could not load community members."
            self.message.color = RED
            self.message.text = "Create the community_profiles view in Supabase first."

    def refresh_display(self, *args):
        self.list_container.clear_widgets()
        query = self.search_input.text.strip().lower() if hasattr(self, "search_input") else ""
        filtered = [p for p in self.members if not query or query in (p.get("full_name") or "").lower() or query in (p.get("country") or "").lower()]
        self.count_label.text = f"{len(filtered)} member(s) shown • {len(self.members)} total"
        if not filtered:
            self.list_container.add_widget(make_label("No community members found.", font_size=15, color=GREY))
            return
        for person in filtered:
            self.list_container.add_widget(CommunityMemberCard(person))


class MyProfileScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_photo_path = ""

        root = BoxLayout(orientation="vertical")
        header = Card(orientation="horizontal", padding=[dp(10), dp(8)], spacing=dp(8), size_hint_y=None, height=dp(68), background_color=SAFFRON)
        back = make_button("←", background_color=DARK_SAFFRON, font_size=24, height=dp(50))
        back.size_hint_x = None; back.width = dp(55)
        back.bind(on_release=lambda *_: setattr(self.manager, "current", "profile"))
        header.add_widget(back)
        header.add_widget(make_label("👤  My Profile", font_size=22, color=WHITE, bold=True, halign="left"))
        root.add_widget(header)

        scroll = ScrollView(do_scroll_x=False)
        form = BoxLayout(orientation="vertical", padding=[dp(18), dp(15), dp(18), dp(25)], spacing=dp(10), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))

        self.photo = CircularImage(source="", size_hint=(None, None), size=(dp(125), dp(125)), pos_hint={"center_x": 0.5})
        form.add_widget(self.photo)
        form.add_widget(make_label("Profile Photo", font_size=15, color=DARK_SAFFRON, bold=True))

        photo_row = BoxLayout(orientation="horizontal", spacing=dp(7), size_hint_y=None, height=dp(45))
        gallery = make_button("🖼 GALLERY", background_color=SAFFRON, font_size=11, height=dp(45))
        camera = make_button("📷 CAMERA", background_color=DARK_SAFFRON, font_size=11, height=dp(45))
        remove = make_button("REMOVE", background_color=GREY, font_size=11, height=dp(45))
        gallery.bind(on_release=self.choose_photo); camera.bind(on_release=self.capture_photo); remove.bind(on_release=self.remove_photo)
        photo_row.add_widget(gallery); photo_row.add_widget(camera); photo_row.add_widget(remove)
        form.add_widget(photo_row)

        self.name_input = make_text_input("Full Name")
        self.email_input = make_text_input("Email")
        self.email_input.readonly = True
        self.role_input = make_text_input("Role")
        self.role_input.readonly = True
        self.country_input = make_text_input("Country")
        self.phone_input = make_text_input("Contact Number")
        form.add_widget(self.name_input); form.add_widget(self.email_input); form.add_widget(self.role_input); form.add_widget(self.country_input); form.add_widget(self.phone_input)

        form.add_widget(make_label("Email and phone are private profile information.", font_size=12, color=GREY))
        self.message = make_label("", font_size=13, color=RED, halign="center")
        self.message.size_hint_y = None; self.message.height = dp(45)
        form.add_widget(self.message)

        save = make_button("SAVE PROFILE", background_color=GREEN, height=dp(54))
        save.bind(on_release=self.save_profile)
        form.add_widget(save)

        community = make_button("←  BACK TO COMMUNITY", background_color=DARK_SAFFRON, height=dp(54))
        community.bind(on_release=lambda *_: setattr(self.manager, "current", "profile"))
        form.add_widget(community)

        privacy = make_label(
            "Community members can see your photo, name, country and role.\nYour email and phone remain private.",
            font_size=12,
            color=GREY,
            halign="center"
        )
        privacy.size_hint_y = None
        privacy.height = dp(48)
        form.add_widget(privacy)

        logout = make_button("LOGOUT", background_color=GREY, height=dp(48))
        logout.bind(on_release=self.logout)
        form.add_widget(logout)

        form.add_widget(make_label("Gateball Lovers\nCreated by Biswa Ranjan\nConnect. Compete. Celebrate.", font_size=12, color=GREY))

        scroll.add_widget(form); root.add_widget(scroll); root.add_widget(BottomNavigation(current_screen="profile"))
        self.add_widget(root)

    def on_pre_enter(self, *args):
        self.load_profile()

    def load_profile(self):
        app = App.get_running_app()
        self.name_input.text = getattr(app, "current_user_name", "")
        self.email_input.text = getattr(app, "current_user_email", "")
        self.role_input.text = getattr(app, "current_role", "Player")
        self.country_input.text = getattr(app, "current_user_country", "")
        self.phone_input.text = getattr(app, "current_user_phone", "")
        self.selected_photo_path = ""
        url = getattr(app, "current_user_photo", "")
        if url:
            local = download_profile_photo(url, getattr(app, "current_user_id", "user"))
            if local:
                self.photo.source = local
                self.photo.reload()
        elif os.path.exists(CREATOR_PATH) and getattr(app, "current_user_name", "") == "Biswa Ranjan":
            self.photo.source = CREATOR_PATH
            self.photo.reload()
        else:
            self.photo.source = ""

    def choose_photo(self, instance):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=self._photo_selected, filters=["*.jpg", "*.jpeg", "*.png", "*.webp"])
        except Exception as exc:
            print("Gallery error:", exc)
            self.message.text = "Gallery is unavailable. Install plyer: pip install plyer"

    def _photo_selected(self, selection):
        if selection:
            path = selection[0]
            if os.path.exists(path):
                self.selected_photo_path = path
                self.photo.source = path
                self.photo.reload()
                self.message.color = DARK_SAFFRON
                self.message.text = "Photo selected. Tap SAVE PROFILE."

    def capture_photo(self, instance):
        try:
            from plyer import camera
            app = App.get_running_app()
            cache_dir = os.path.join(app.user_data_dir, "profile_cache")
            os.makedirs(cache_dir, exist_ok=True)
            path = os.path.join(cache_dir, f"camera_{uuid.uuid4().hex}.jpg")
            camera.take_picture(filename=path, on_complete=self._camera_completed)
        except Exception as exc:
            print("Camera error:", exc)
            self.message.text = "Camera is unavailable on this device. Gallery can still be used."

    def _camera_completed(self, path):
        if path and os.path.exists(path):
            self.selected_photo_path = path
            self.photo.source = path
            self.photo.reload()
            self.message.text = "Photo captured. Tap SAVE PROFILE."

    def remove_photo(self, instance):
        self.selected_photo_path = "__REMOVE__"
        self.photo.source = ""
        self.message.color = DARK_SAFFRON
        self.message.text = "Photo will be removed when you save."

    def save_profile(self, instance):
        app = App.get_running_app()
        if supabase is None or not getattr(app, "current_user_id", ""):
            self.message.text = "Please log in again."
            return

        name = self.name_input.text.strip(); country = self.country_input.text.strip(); phone = self.phone_input.text.strip()
        if len(name) < 2:
            self.message.text = "Please enter a valid full name."
            return
        if not country:
            self.message.text = "Please enter your country."
            return
        if not phone:
            self.message.text = "Please enter your contact number."
            return

        self.message.color = DARK_SAFFRON
        self.message.text = "Saving profile…"
        try:
            photo_url = getattr(app, "current_user_photo", "") or ""
            if self.selected_photo_path == "__REMOVE__":
                photo_url = ""
            elif self.selected_photo_path:
                photo_url = upload_profile_photo(self.selected_photo_path, app.current_user_id)
                if not photo_url:
                    raise Exception("Photo upload failed. Check the Supabase profile-photos bucket and policy.")

            payload = {"full_name": name, "country": country, "phone": phone, "photo_url": photo_url}
            response = supabase.table("profiles").update(payload).eq("id", app.current_user_id).execute()
            if not response.data:
                raise Exception("Profile update returned no data. Check profiles RLS policies.")

            app.current_user_name = name
            app.current_user_country = country
            app.current_user_phone = phone
            app.current_user_photo = photo_url
            self.selected_photo_path = ""
            self.message.color = GREEN
            self.message.text = "✓ Profile saved successfully!"
            Clock.schedule_once(lambda *_: setattr(self.manager, "current", "dashboard"), 0.8)
        except Exception as exc:
            print("Profile save error:", exc)
            self.message.color = RED
            self.message.text = "Profile save failed: " + str(exc)[:180]

    def logout(self, instance):
        app = App.get_running_app()
        try:
            app.stop_presence_heartbeat()
            if supabase is not None:
                supabase.auth.sign_out()
        except Exception as exc:
            print("Logout error:", exc)
        app.current_role = "Player"; app.current_user_id = ""; app.current_user_name = ""; app.current_user_email = ""
        app.current_user_country = ""; app.current_user_phone = ""; app.current_user_photo = ""
        if self.manager:
            self.manager.current = "login"


# ============================================================
# SCREEN MANAGER
# ============================================================

class GateballScreenManager(ScreenManager):

    def __init__(self, **kwargs):

        super().__init__(
            transition=FadeTransition(
                duration=0.25
            ),
            **kwargs
        )

        self.add_widget(
            SplashScreen(
                name="splash"
            )
        )

        self.add_widget(
            LoginScreen(
                name="login"
            )
        )

        self.add_widget(
            SignupScreen(
                name="signup"
            )
        )

        self.add_widget(
            DashboardScreen(
                name="dashboard"
            )
        )

        self.add_widget(
            CommunityListScreen(
                name="players",
                list_title="Players",
                list_type="Players"
            )
        )

        self.add_widget(
            CommunityListScreen(
                name="organizers",
                list_title="Organizers",
                list_type="Organizers"
            )
        )

        self.add_widget(CommunityProfilesScreen(name="community_profiles"))
        self.add_widget(MemberProfileScreen(name="member_profile"))
        self.add_widget(DirectChatScreen(name="direct_chat"))
        self.add_widget(MyProfileScreen(name="my_profile"))

        self.add_widget(
            TournamentScreen(
                name="tournaments"
            )
        )

        self.add_widget(AddTournamentScreen(name="add_tournament"))
        self.add_widget(AddResultScreen(name="add_result"))

        self.add_widget(ChatHomeScreen(name="chat"))
        self.add_widget(NewsScreen(name="news"))

        self.add_widget(EditTournamentScreen(name="edit_tournament"))

        self.add_widget(ProfileScreen(name="profile"))


# ============================================================
# APPLICATION
# ============================================================

class GateballLoversApp(App):

    title = "Gateball Lovers"
    current_role = "Player"
    current_user_id = ""
    current_user_name = ""
    current_user_email = ""
    current_user_country = ""
    current_user_phone = ""
    current_user_photo = ""

    def setup_realtime_auth(self):
        """Give Supabase Realtime the currently signed-in user's JWT."""
        if supabase is None or not getattr(self, "current_user_id", ""):
            return False
        try:
            session_response = supabase.auth.get_session()
            session = getattr(session_response, "session", None)
            if session is None and isinstance(session_response, dict):
                session = (session_response.get("data") or {}).get("session")
            access_token = getattr(session, "access_token", None) if session is not None else None
            if not access_token and isinstance(session, dict):
                access_token = session.get("access_token")
            if not access_token:
                return False
            supabase.realtime.set_auth(access_token)
            return True
        except Exception as exc:
            print("Realtime auth setup error:", exc)
            return False

    def stop_realtime(self):
        try:
            if supabase is not None:
                supabase.realtime.remove_all_channels()
        except Exception as exc:
            print("Realtime cleanup error:", exc)

    def start_presence_heartbeat(self):
        if getattr(self, "presence_event", None) is not None: return
        self.update_presence()
        self.presence_event = Clock.schedule_interval(lambda *_: self.update_presence(), 30)

    def update_presence(self):
        if supabase is None or not getattr(self, "current_user_id", ""): return
        try:
            supabase.table("user_presence").upsert({"user_id":self.current_user_id,"last_seen":datetime.utcnow().isoformat()+"+00:00"}).execute()
        except Exception as exc: print("Presence update error:",exc)

    def stop_presence_heartbeat(self):
        event=getattr(self,"presence_event",None)
        if event is not None: event.cancel(); self.presence_event=None

    def on_stop(self):
        self.stop_presence_heartbeat()
        self.stop_realtime()

    def build(self):
        self.presence_event=None
        return GateballScreenManager()


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    GateballLoversApp().run()
# Launch webserver for Image Uploading

import os
import datetime
from flask import Flask, request, redirect, url_for, render_template, flash
import sqlite3
import random
from PIL import Image, ImageDraw, ImageFont
import subprocess

# from werkzeug.utils import secure_filename
import shutil
from flask import send_from_directory, jsonify

import asyncio
from kasa import Discover
from kasa.iot import IotBulb


app = Flask(__name__)

# app.secret_key = "supersecret"  # needed for flash messages

# Config
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
MAX_STORAGE_MB = 50  # max total storage for uploads

app.config.from_object("config")
# <h2>Directory: {{ app.config['DIR_UPLOADS_SLIDESHOW'] }}</h2>
# print('Directory: ', app.config['DIR_UPLOADS_SLIDESHOW'])

# app.config["DIR_UPLOADS_SLIDESHOW"] = UPLOAD_FOLDER
os.makedirs(app.config["DIR_UPLOADS_SLIDESHOW"], exist_ok=True)

# In-memory log of uploads
submissions = []

aurik_urls = [
    'https://en.wikipedia.org/wiki/Aurick',
    'https://forebears.io/x/forenames/aurik', 
    'https://github.com/goldrik', 
    'https://www.facebook.com/SURRaurikENDER/', 
    'https://www.youtube.com/c/AurikSarker',
    'https://www.researchgate.net/profile/Aurik-Sarker', 
    'https://theorg.com/org/nabsys/org-chart/aurik-sarker',
]

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_free_space_mb(path="."):
    """Return free disk space (MB) at given path."""
    total, used, free = shutil.disk_usage(path)
    print(free / 1024 / 1024)
    return free / (1024 * 1024)


@app.context_processor
def inject_random_url():
    return dict(random_url=random.choice(aurik_urls))

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")

def init_dirs():
    os.makedirs('media/slideshow', exist_ok=True)
    os.makedirs('media/webcam', exist_ok=True)


# SQLITE database names
DB_REGISTER = "register"
DB_SLIDESHOW = "slideshow"
DB_WEBCAM = "webcam"

def get_db(db_name):
    conn = sqlite3.connect(db_name + '.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_dbs():
    with get_db(DB_REGISTER) as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {DB_REGISTER} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    # with get_db(DB_SLIDESHOW) as conn:
    #     conn.execute(
    #         f"""
    #         CREATE TABLE IF NOT EXISTS {DB_REGISTER} (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             name TEXT NOT NULL,
    #             message TEXT NOT NULL,
    #             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    #         )
    #         """
    #     )

    # with get_db(DB_WEBCAM) as conn:
    #     conn.execute(
    #         f"""
    #         CREATE TABLE IF NOT EXISTS {DB_REGISTER} (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             name TEXT NOT NULL,
    #             message TEXT NOT NULL,
    #             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    #         )
    #         """
    #     )


@app.template_filter('format_datetime')
def format_datetime(dt):
    fmt = '%Y %b %d %a, %H:%M:%S'
    dt_dt = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
    # CONVERT UTC -> EST
    dt_est = dt_dt - datetime.timedelta(hours=5)
    return dt_est.strftime(fmt)



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "anon").strip()
        message = request.form.get("message", "").strip()
        password = request.form.get("password", "").strip()

        if not message:
            flash("Error: Message is required", "error")    
            return redirect(url_for("register"))
        if password != app.config["PASSWORD"]:
            flash("Error: Incorrect Password", "error")    
            return redirect(url_for("register"))
        
        
        with get_db(DB_REGISTER) as conn:
            conn.execute(
                f"INSERT INTO {DB_REGISTER} (name, message) VALUES (?, ?)",
                (name, message),
            )
        return redirect(url_for("register"))

    with get_db(DB_REGISTER) as conn:
        messages = conn.execute(f"SELECT timestamp, name, message FROM {DB_REGISTER} ORDER BY timestamp DESC").fetchall()

    return render_template("register.html", messages=messages)



@app.route("/slideshow", methods=["GET", "POST"])
def slideshow():
    global submissions
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        message = request.form.get("message", "").strip()
        message = request.form.get("password", "")
        files = request.files.getlist("images")

        if not name or not message or not files:
            flash("Name, message, and at least one image are required.")
            return redirect(url_for("index"))

        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                # filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S_") + secure_filename(file.filename)
                filename = (
                    datetime.datetime.now().strftime("%Y%m%d%H%M%S_") + file.filename
                )
                filepath = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    app.config["DIR_UPLOADS_SLIDESHOW"],
                    filename,
                )
                file.save(filepath)
                uploaded_files.append(filename)
            else:
                flash("Invalid file type.")
                return redirect(url_for("index"))

        # Check if there is still free disk space AFTER saving
        if get_free_space_mb(app.config["DIR_UPLOADS_SLIDESHOW"]) <= 0:
            # rollback the saved files
            for f in uploaded_files:
                os.remove(os.path.join(app.config["DIR_UPLOADS_SLIDESHOW"], f))
            flash("Error: Not enough disk space. Upload rejected.")
            return redirect(url_for("index"))

        submissions.append(
            {
                "name": name,
                "message": message,
                "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "count": len(uploaded_files),
                "files": uploaded_files,
            }
        )
        return redirect(url_for("index"))

    # Show latest images first
    # images = []
    # for sub in reversed(submissions):
    #     for f in sub["files"]:
    #         images.append(f)
    # image = submissions[0]["files"][0]
    # image = "20251008042826_call_your_mother.jpg"
    # image = "media/slideshow/call_your_mother.jpg"
    image = "call_your_mother.jpg"

    return render_template("slideshow.html", submissions=submissions, image=image)


async def get_devices():
    return await Discover.discover(target="192.168.1.255")

async def get_state(light):
    await light.update()
    return await light.get_light_state(), light.is_on

async def set_state(light, state):
    await light.update()
    await light._set_light_state(state)
    return await light.get_light_state(), light.is_on

async def turn_on_off(light, on_off):
    if on_off:
        await light.turn_on()
    else:
        await light.turn_off()

@app.route("/lights", methods=["GET", "POST"])
def lights():
    devices = asyncio.run(get_devices())

    light = None
    state = {'brightness': 50, 'color': '#ffffff'}
    on_off = False

    if devices:
        light = list(devices.values())[0]
        state, on_off = asyncio.run(get_state(light))
        print(state)
        print(on_off)

    # devices = True

    if request.method == "POST":
        data = request.get_json()
        action = data.get("action")
        if action == 'reset':
            brightness = 50
            # white = 2500
            color = "#ffffff"
            print(f"Action: {action}")

        elif action == 'update':
            brightness = data.get("brightness")
            color = data.get("color")
            print(f"Action: {action}, Brightness: {brightness}, Color: {color}")

        if action == 'power':
            on_off = not on_off
            print(f"Action: {action}")

        else:
            state['brightness'] = brightness
            # state['color'] = 
            on_off = True
            
            asyncio.run(set_state(light, state))
        
        asyncio.run(turn_on_off(light, on_off))

        # return jsonify({"status": "ok"})

    return render_template("lights.html", devices=devices, brightness=state['brightness'], color=state['color'])



def default_image():
    width, height = 1200, 800
    img = Image.new('RGB', (width, height), 'black')
    return img


def add_date_text(img, dt):
    width, height = img.size
    draw = ImageDraw.Draw(img)

    datestr = dt.strftime('%m %d \'%y %I:%M %p')

    # Try to use a monospace font for that old-camera look
    font_size = 42
    # Orange/amber color like old disposable camera date stamps
    color = (255, 64, 0)
    try:
        # font = ImageFont.truetype('./media/fonts/DSEG7Classic-Regular.ttf', font_size)
        font = ImageFont.truetype('./media/fonts/14 Segment LED.ttf', font_size)
        # font = ImageFont.truetype('./media/fonts/14-segment.ttf', font_size)
    except:
        font = ImageFont.load_default()

    # Position in bottom-right corner (classic disposable camera placement)
    bbox = draw.textbbox((0, 0), datestr, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = width - text_w - 40
    y = height - text_h - 30

    draw.text((x, y), datestr, fill=color, font=font)

    return img


@app.template_filter('datetime_to_suffix')
def datetime_to_suffix(dt):
    fmt = '%Y%m%d%H%M%S'
    return dt.strftime(fmt)

@app.template_filter('fn_to_datetime')
def fn_to_datetime(fn):
    dt_str = fn.split('.')[0][-14:]
    fmt = '%Y%m%d%H%M%S'
    return datetime.datetime.strptime(dt_str, fmt)

@app.route("/webcam", methods=["GET", "POST"])
def webcam():
    if request.method == "POST":
        dt = datetime.datetime.now()
        fn = 'webcam_' +  datetime_to_suffix(dt - datetime.timedelta(hours=5)) + '.jpg'
        fn = os.path.join('./media/webcam', fn)
        cmd = f'rpicam-still --rotation 180 --immediate -o {fn}'

        try: 
            subprocess.run(cmd, capture_output=True, text=True)
        except:
            img = add_date_text(default_image(), dt)
            img.save(fn)

    files = os.listdir("./media/webcam")
    if files:
        files.sort()
        latest_webcam = files[-1]
    else:
        latest_webcam = None

    dt_str = fn_to_datetime(latest_webcam)
    dt_str = dt_str.strftime('%Y %b %d %a, %H:%M:%S')

    return render_template("webcam.html", image=latest_webcam, dt_str=dt_str)


@app.route("/<folder>/<filename>")
def uploaded_file(filename, folder):
    # return send_from_directory(app.config["DIR_UPLOADS_SLIDESHOW"], filename)
    return send_from_directory(f'media/{folder}', filename)



if __name__ == "__main__":
    init_dirs()
    init_dbs()
    app.run(host="0.0.0.0", port=5454, debug=True)

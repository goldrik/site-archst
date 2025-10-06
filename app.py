# Launch webserver for Image Uploading

import os
import datetime
from flask import Flask, request, redirect, url_for, render_template_string, flash
# from werkzeug.utils import secure_filename
import shutil
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = "supersecret"  # needed for flash messages

# Config
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
MAX_STORAGE_MB = 50   # max total storage for uploads

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory log of uploads
submissions = []

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_free_space_mb(path="."):
    """Return free disk space (MB) at given path."""
    total, used, free = shutil.disk_usage(path)
    print(free / 1024 / 1024)
    return free / (1024 * 1024)


@app.route("/", methods=["GET", "POST"])
def index():
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
                filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S_") + file.filename
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                uploaded_files.append(filename)
            else:
                flash("Invalid file type.")
                return redirect(url_for("index"))

        # Check if there is still free disk space AFTER saving
        if get_free_space_mb(app.config["UPLOAD_FOLDER"]) <= 0:
            # rollback the saved files
            for f in uploaded_files:
                os.remove(os.path.join(app.config["UPLOAD_FOLDER"], f))
            flash("Error: Not enough disk space. Upload rejected.")
            return redirect(url_for("index"))

        submissions.append({
            "name": name,
            "message": message,
            "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(uploaded_files),
            "files": uploaded_files
        })
        return redirect(url_for("index"))

    # Show latest images first
    # images = []
    # for sub in reversed(submissions):
    #     for f in sub["files"]:
    #         images.append(f)
    # image = submissions[0]["files"][0]
    image = '20250923145823_call_your_mother.jpg'

    return render_template_string(TEMPLATE, submissions=submissions, image=image)

@app.route("/about")
def about():
    return render_template_string(ABOUT_TEMPLATE)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Image Upload</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
            background: #fafafa;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        header {
            width: 100%;
            background: #333;
            color: white;
            padding: 20px 0;
            text-align: center;
            font-size: 1.5em;
            font-weight: 600;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        header a {
            color: #fff;
            text-decoration: none;
            margin-left: 10px;
            font-weight: 400;
        }
        header a:hover {
            text-decoration: underline;
        }
        main {
            max-width: 800px;
            width: 100%;
            padding: 30px;
            text-align: center;
        }
        form {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 40px;
        }
        form input[type="text"],
        form input[type="file"] {
            width: 90%;
            padding: 10px;
            margin: 8px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
        }
        form input[type="submit"] {
            margin-top: 15px;
            background: #333;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }
        form input[type="submit"]:hover {
            background: #555;
        }
        .image-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
        }
        .image-container img {
            max-width: 100%;
            border-radius: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 40px;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        th, td {
            padding: 12px;
            border-bottom: 1px solid #eee;
            text-align: left;
        }
        th {
            background: #f7f7f7;
            font-weight: 600;
        }
        .flash {
            color: #d33;
            margin-bottom: 15px;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <header>
        📸 Simple Image Board | <a href="{{ url_for('about') }}">About Me</a>
    </header>

    <main>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="flash">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}

        <form method="post" enctype="multipart/form-data">
            <input type="text" name="name" placeholder="Name" required><br>
            <input type="text" name="message" placeholder="Write a message" required><br>
            <input type="text" name="password" placeholder="Password" required><br>
            <input type="file" name="images" accept="image/*" multiple required><br>
            <input type="submit" value="Upload">
        </form>

        <h2>Latest Image</h2>
        <div class="image-container">
            <!-- <img src="{{ url_for('static', filename='uploads/' + image) }}" alt="Uploaded image"> -->
            <img src="{{ url_for('uploaded_file', filename=image) }}" alt="Uploaded image">
            <p>Image path: {{ url_for('uploaded_file', filename=image) }}</p>
        </div>

        <h2>Submission Log</h2>
        <table>
            <tr>
                <th>Name</th>
                <th>Message</th>
                <th>Date/Time</th>
                <th># of Images</th>
            </tr>
            {% for sub in submissions %}
            <tr>
                <td>{{ sub.name }}</td>
                <td>{{ sub.message }}</td>
                <td>{{ sub.datetime }}</td>
                <td>{{ sub.count }}</td>
            </tr>
            {% endfor %}
        </table>
    </main>
</body>
</html>
"""


ABOUT_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>About Me</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
            background: #fafafa;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        header {
            width: 100%;
            background: #333;
            color: white;
            padding: 20px 0;
            text-align: center;
            font-size: 1.5em;
            font-weight: 600;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        header a {
            color: #fff;
            text-decoration: none;
            margin-left: 10px;
            font-weight: 400;
        }
        header a:hover {
            text-decoration: underline;
        }
        main {
            max-width: 800px;
            width: 100%;
            padding: 30px;
            text-align: center;
        }
    </style>
</head>
<body>
    <header>
        📸 Simple Image Board |
        <a href="{{ url_for('index') }}">Home</a>
    </header>
    <main>
        <h1>About Me</h1>
        <p>Hello! This is a simple image board I built using Flask. 
        Here you can upload images, leave a message, and see what others have shared.</p>
        <p>You can customize this text to say whatever you’d like — e.g. your background, 
        why you built the site, or fun facts about yourself.</p>
    </main>
</body>
</html>
"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5454, debug=True)

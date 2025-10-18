# Launch webserver for Image Uploading

import os
import datetime
from flask import Flask, request, redirect, url_for, render_template, flash

# from werkzeug.utils import secure_filename
import shutil
from flask import send_from_directory

app = Flask(__name__)


app.secret_key = "supersecret"  # needed for flash messages

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
    image = "call_your_mother.jpg"

    return render_template("index.html", submissions=submissions, image=image)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/<filename>")
def uploaded_file(filename):
    # return send_from_directory(app.config["DIR_UPLOADS_SLIDESHOW"], filename)
    return send_from_directory('media/slideshow', filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5454, debug=True)

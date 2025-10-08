# Run the slideshow, then the image uploader app
export DISPLAY=:0.0

# Slideshow image directory
# Get the path from the config file
DIR_UPLOADS_SLIDESHOW=$(cat config.py | grep DIR_UPLOADS_SLIDESHOW | cut -d '=' -f 2)

nohup feh --fullscreen --auto-zoom --sort mtime --slideshow-delay 3 --reload 3 ./$DIR_UPLOADS_SLIDESHOW --uploads & 
nohup python app.py & 
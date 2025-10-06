# Run the slideshow, then the image uploader app
export DISPLAY=:0.0
nohup feh --fullscreen --auto-zoom --sort mtime --slideshow-delay 3 --reload 3 ./uploads & 
nohup python app.py & 
# Kill the webserver and feh slideshow
# Use ps to find the correct process

# PYTHON
pid=$(ps aux | grep "slideshow/app.py" | awk 'NR==1 {print $2}')
kill $pid
# FEH
pid=$(ps aux | grep "feh" | awk 'NR==1 {print $2}')
kill $pid

# TODO - check number of output from ps, use if statement to check > 1, output to user
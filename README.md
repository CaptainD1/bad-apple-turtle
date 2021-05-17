# bad-apple-turtle
A program that plays Bad Apple!! on a Python Turtle

I just made this in the course of a few hours, so don't expect it to be perfect or anything. I might fix it up at some point.

You need OpenCV, python-vlc, and pypotrace instralled for this to work.

Make sure OpenCV is installed with FFMPEG support and VLC Media Player is installed before python-vlc.

First, you need to run `bad_apple_vectorize.py` in the same folder as the video file for Bad Apple. This converts each frame of the video into vectors for the turtle to display. It will take a little while to do. You will probably need to either rename the video or change the `VIDEO_PATH` variable in the Python file.

Next, run `bad_apple_turtle.py` in the same folder as the original video and the new vector file. This should open up a turtle window and a VLC window playing the original video. You need to make sure the `VIDEO_PATH` in `bad_apple_turtle.py` also matches the filename of the video.

If the turtle is not synchronized with the video, make sure the `TARGET_FPS` variable is set to the same framerate as the video you're playing.

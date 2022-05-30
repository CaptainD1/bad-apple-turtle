# bad-apple-turtle
A program that plays Bad Apple!! on a Python Turtle

This had just been nearly completely re-written to be better in almost every way. Pypotrace is no longer used in this version.

You need OpenCV installed for this to work. Python-vlc is also used when playing back a video along side the turtle, but it technically optional.

Make sure OpenCV is installed with FFMPEG support and VLC Media Player is installed before python-vlc.

First, you need to run `bad_apple_vectorize.py` while specifying an input video. This converts each frame of the video into vectors for the turtle to display. You can specify an output file, but if not, it will append "\_vectorized" to the name and change the extension to `.dat`.

Lower `--threshold` values may provide sharper images with more of the gradients being converted into white than black.

Next, run `bad_apple_turtle.py` and specify the name of the new vector file. This will open up a turtle window that will play the video. You can include a video with the vector file using `-v <video_path>`. If you do, a VLC window will also open and play the original video, synchronized with the turtle. When specifying an external video, it will usually drop a few frames of the turtle video at the beginning while trying to synchronize the two.

If the turtle is not synchronized with the video, you can try increasing the `--vlc_delay` option, though it's already fairly high. If you are getting lots of dropped frames, you can try increasing `--tolerance` or get a faster computer.

There are other options with both files, and I recommend you use `--help` for more information (or look at the source code, the code is near the top and pretty self-explanatory.)

I used this video: https://www.youtube.com/watch?v=UkgK8eUdpAo

Theoretically, you could probably put any video through this, but I do not know how well it would work and it would be converted to binary black and white.

I plan to eventually release this on pypi, but I'm going to make sure I get everything streamlined first.
# bad-apple-turtle
A program that plays Bad Apple!! on a Python Turtle

This had just been nearly completely re-written to be better in almost every way. Pypotrace is no longer used in this version.

You need OpenCV installed for this to work. Python-vlc is also used when playing back a video along side the turtle, but it technically optional.

Make sure OpenCV is installed with FFMPEG support and VLC Media Player is installed before python-vlc.

You have several options. You can directly play a video in a turtle by specifying it in the command with `-v`/`--video`. If you don't want the original to play next to it, you can use the `--no-vlc` argument. If you want to export the resulting vectorized video to a file, you can also specify an output file with `-o`/`--output`. You can then play the vectorized video again later using `-i`/`--input`. If you specify a vectorized video and a normal video at the same time, the turtle will play the vectorized one while VLC will play the normal video. If you just want to output a file without playing the video at the same time, you can use the `--no-play` argument. Once the vectorized video is exported, the original is no longer required for turtle playback, though there is no audio included.

If the turtle is not synchronized with the video, you can try increasing the `--vlc_delay` option, though it's already fairly high. If you are getting lots of dropped frames, you can use the simplification options, which are `--max-points` and `--min-area`. `--max-points` is the maximum number of points in a frame times the square root of the number of curves before the vectors are simplified. `--min-area` is the minimum area a curve needs for it to be rendered. Alternatively, you can try increasing `--tolerance`, which is how much time offset is allowed before frames are dropped, or get a faster computer.

Increasing the `--threshold` will increase how much of the greys are converted to black, and decreasing it will increase the amount of white. You can also use `-ss` and `-to` to specify starting and ending frames to playback (or export to a file)

There are other options and I recommend you use `--help` for more information.

I used this video for testing: https://www.youtube.com/watch?v=UkgK8eUdpAo

Theoretically, you could probably put any video through this, but I do not know how well it would work and it would be converted to binary black and white.
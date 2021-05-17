import pickle
import turtle
import vlc
import time

# Preview video
VIDEO_PATH = 'BadApple.mp4'

# Framerate of exported vectors (could be different from video)
TARGET_FPS = 30

def main():

    # Load vectors
    with open("list_paths_2.dat", 'rb') as file:
        paths = pickle.load(file)

    # Setup turtle
    tortoise = turtle.Turtle()
    tortoise.speed(8)
    tortoise.hideturtle()
    turtle.bgcolor("black")
    screen = tortoise.getscreen()
    screen.tracer(0,0)

    # Play actual animation
    play_animation(tortoise, screen, paths)

    # Close the screen when finished
    screen.bye()

def play_animation(tortoise, screen, paths):

    # Play original video next to turtle
    vlc_player = vlc.MediaPlayer(VIDEO_PATH)
    vlc_player.video_set_scale(0.2)
    vlc_player.play()

    # Make sure the video has started playing so they can synchronize
    time.sleep(1.5)

    # Sychronize start time with video player
    start_time = -vlc_player.get_time() / 1000 + time.time()

    # While loop iteration to allow for skipping frames (curse you Python)
    frame_num = 0
    while frame_num < len(paths):
        
        # Get current path
        path = paths[frame_num]

        # Clear the screen and draw new frame
        tortoise.clear()
        draw_path(tortoise, path)
        screen.update()

        # Get timing for frame compared to video
        end_time = time.time()
        current_time = end_time - start_time
        target_time = frame_num / TARGET_FPS
        time_offset = current_time - target_time

        # Determine whether to skip frames or delay frame
        skip_frames = 0
        if time_offset > 0:
            skip_frames = int(time_offset * TARGET_FPS) + 1
            frame_num += skip_frames
        elif time_offset < -0.1:
            time.sleep(-time_offset - 0.1)

        # Display frame status
        print("Offset: {:.2f}, frame: {}".format(time_offset, frame_num), end='')
        if skip_frames != 0:
            print(" ({} skipped)".format(skip_frames))
        else:
            print()

        frame_num += 1

    # Close preview video when finished
    vlc_player.release()

def draw_path(tortoise, path):

    # Draw every curve in the path
    for color, curve in path:

        # Gray line and fill based on curve
        tortoise.color("gray", "black" if color == 1 else "white")
        tortoise.begin_fill()

        # Make sure there is actually a curve
        if len(curve) > 0:

            # Go to initial postion without drawing
            tortoise.up()
            tortoise.goto(curve[0][0]-960/2, curve[0][1]-720/2)
            tortoise.down()

            # Draw remaining points
            for point in curve:
                tortoise.goto(point[0]-960/2, point[1]-720/2)
            
            # Close loop by drawing back to initial position
            tortoise.goto(curve[0][0]-960/2, curve[0][1]-720/2)
        tortoise.end_fill()

main()
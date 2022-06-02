import argparse
import pathlib
import turtle
import time
import typing
import math

import vector_video

def main():

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Plays a vectorized video in a Python turtle.")
    parser.add_argument('input', type=str,
        help="Input vector file to play")
    parser.add_argument('-v', '--video', type=str, default=None,
        help="Video to play along with turtle.")
    parser.add_argument('-s', '--start', type=int, default=0,
        help="Starting frame of video.")
    parser.add_argument('--scale', type=float, default=1.0,
        help="Scale multiplier of turtle graphics.")
    parser.add_argument('--vlc_scale', type=float, default=0.2,
        help="Scale multiplier of VLC preview window.")
    parser.add_argument('--vlc_delay', type=float, default=1.5,
        help="The delay in seconds after playing VLC video before synchronizing the turtle.")
    parser.add_argument('--tolerance', type=float, default=0.01,
        help="The tolerance of desync in seconds before the turtle drops frames.")
    parser.add_argument('--threshold', type=int, default=96,
        help="The vectorizing threshold when using live conversion.")
    parser.add_argument('--simplify', type=int, default=0,
        help="How much to simplify the vectors before drawing.")

    args = vars(parser.parse_args())

    # Setup turtle
    tortoise = turtle.Turtle()
    tortoise.speed(10)
    tortoise.hideturtle()
    turtle.bgcolor("black")
    screen = tortoise.getscreen()
    screen.tracer(0,0)

    # Play actual animation
    play_animation(tortoise, screen, args)

    # Close the screen when finished
    screen.bye()

def play_animation(tortoise: turtle.Turtle, screen: turtle.TurtleScreen, args: dict):

    # Extract arguments
    vector_path = pathlib.Path(args['input'])
    video_path = pathlib.Path(args['video']) if args['video'] else None
    start_frame = args['start']
    offset_tolerance = args['tolerance']


    # Setup vector decoder
    #decoder = vector_video.VectorVideoFileDecoder(vector_path)
    #decoder.open()
    contour_provider = vector_video.ContourSupplier(pathlib.Path(vector_path),
            args["threshold"], args["simplify"])
    decoder = vector_video.VectorVideoLiveDecoder(contour_provider)

    # Read entire video to memory
    #decoder.read_all()

    # Play original video next to turtle
    if video_path:
        # Only import VLC if needed (then this script can run without VLC)
        import vlc

        instance = vlc.Instance("--verbose=-1")
        instance.log_unset()
        vlc_player = instance.media_player_new()
        media = instance.media_new(str(video_path.absolute()))
        media.add_option(f'start-time={start_frame / decoder.framerate:.3f}')
        vlc_player.set_media(media)
        vlc_player.video_set_scale(args["vlc_scale"])
        vlc_player.play()

        # Make sure the video has started playing so they can synchronize
        time.sleep(args['vlc_delay'])

        # Sychronize start time with video player
        start_time = -vlc_player.get_time() / 1000 + time.time()
    else:
        start_time = time.time() - start_frame / decoder.framerate

    decoder.seek(start_frame)

    # Create variables for video statistics
    max_frame_time = 0
    frames_dropped = 0
    total_time = 0
    frame_count_digits = int(math.log10(decoder.total_frames) + 1)

    while decoder.current_frame < decoder.total_frames:

        try:
            # Get time before frame is drawn
            frame_start_time = time.time()

            # Clear the screen and draw new frame
            tortoise.clear()
            num_contours, num_points, contours_drawn = draw_path(tortoise, decoder, args["scale"])

            # Get timing for frame compared to video and update statistics
            end_time = time.time()
            current_time = end_time - start_time
            target_time = decoder.current_frame / decoder.framerate
            time_offset = current_time - target_time
            frame_render_time = end_time - frame_start_time
            total_time += frame_render_time
            max_frame_time = max(max_frame_time, frame_render_time)

            # Determine whether to skip frames or delay frame
            skip_frames = 0
            if time_offset > offset_tolerance:
                skip_frames = int(time_offset * decoder.framerate) + 1
                decoder.seek(skip_frames, 1)
            elif time_offset < -offset_tolerance:
                time.sleep(-time_offset - offset_tolerance)

            # Update screen after time is re-synchronized
            screen.update()

            # Get time offset after frame delay
            new_time_offset = time.time() - start_time - target_time

            # Time per point prevent division by zero
            time_per_point = int((frame_render_time / num_points)*1000000) if num_points != 0 else 0

            # Display frame statistics
            print(f"\rFrame render time:{frame_render_time*1000: 7.2f}ms, " \
                f"Offset:{new_time_offset*1000: 10.2f}ms, " \
                f"Frame: {decoder.current_frame:0{frame_count_digits}}/{decoder.total_frames}, " \
                f"Contours/Points/Drawn: {num_contours}/{num_points}/{contours_drawn}   " \
                f"Time per point: {time_per_point}us     ", end='')
            if skip_frames != 0:
                frames_dropped += skip_frames
                print(" ({} dropped)".format(skip_frames))
        except KeyboardInterrupt:
            print("\nStopping playback...")
            break

     # Close preview video when finished
    if video_path:
        vlc_player.release()

    #decoder.close()

    average_frame_time = total_time / (decoder.current_frame - start_frame - frames_dropped)
    print(f"\nPlayback complete. Dropped frames: {frames_dropped}, " \
            f"Maximum Frame Time: {int(max_frame_time*1000)}ms, " \
            f"Average Frame Time: {int(average_frame_time*1000)}ms")

def draw_path(tortoise: turtle.Turtle, decoder: vector_video.VectorVideoDecoder,
        scale: float=1.0):

    contours = decoder.read()

    num_contours = len(contours)
    num_points = 0

    contours_drawn = 0

    # Draw every curve in the path
    for contour in contours:

        num_points += len(contour)

        # Make sure there is actually a contour
        if len(contour) > 0:

            # Gray line and fill based on contour
            tortoise.color("gray", "black" if contour.color == 1 else "white")

            contours_drawn += 1

            # Go to initial postion without drawing
            tortoise.up()
            move_turtle(tortoise, contour[0], decoder.dimensions, scale)
            tortoise.begin_fill()
            tortoise.down()

            # Draw remaining points
            for point in contour:
                move_turtle(tortoise, point, decoder.dimensions, scale)
            
            # Close loop by drawing back to initial position
            move_turtle(tortoise, contour[0], decoder.dimensions, scale)
            tortoise.end_fill()   

    return num_contours, num_points, contours_drawn

def move_turtle(tortoise: turtle.Turtle, point: typing.Tuple[float, float],
        frame_dimensions: typing.Tuple[int, int], scale_factor: float=1.0):

    tortoise.goto((point[0] - frame_dimensions[0]/2) * scale_factor,
            (frame_dimensions[1]/2 - point[1]) * scale_factor)

if __name__ == '__main__':
    main()
import argparse
import pathlib
import struct
import math

import cv2

import vector_video

def main():

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Converts a video into vector data.')
    parser.add_argument('input', type=str,
        help="Input video to parse")
    parser.add_argument('-o', '--output', type=str, default=None,
        help="Output file path")
    parser.add_argument('-s', '--start', type=int, default=0,
        help="Start frame")
    parser.add_argument('-e', '--end', type=int, default=-1,
        help="End frame")
    parser.add_argument('--threshold', type=int, default=96,
        help="The threshold value for determining what should be black or white. " \
            "Valid range: 0 - 255"
        )

    args = vars(parser.parse_args())

    threshold_value = args['threshold']

    input_path = pathlib.Path(args['input'])
    if args['output']:
        output_path = pathlib.Path(args['output'])
    else:
        # Default output path
        output_path = input_path.parent / (input_path.stem + '_vectorized.dat')

    # Load video to vectorize
    source = cv2.VideoCapture(str(input_path))

    # Get video metadata
    source_framerate = source.get(cv2.CAP_PROP_FPS)
    source_frame_count = int(source.get(cv2.CAP_PROP_FRAME_COUNT))
    source_frame_dimensions = (int(source.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(source.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    # Set start and end frames
    frame_num = args['start']
    end_frame = args['end'] if args['end'] >= 0 else source_frame_count
    if frame_num > 0:
        source.set(1, frame_num)

    frame_count_digits = int(math.log10(end_frame) + 1)

    success, orig = source.read()

    # Create encoder
    encoder = vector_video.VectorVideoEncoder(source_framerate, source_frame_dimensions)

    # Open file for output
    file = output_path.open('wb')

    # Stop gracefully if process interrupted
    try:
        while success and frame_num <= end_frame:

            # Convert video to black and white
            image = cv2.threshold(cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY), threshold_value, 1,
                    cv2.THRESH_BINARY)[1]

            # Vectorize video
            contours, hierarchy = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            encoder.feed_contours(contours, hierarchy)

            # Encode vectors into bytes and write to file
            encoder.dump_continue(file)

            encoder.trim_dumped()

            print(f"Frame {frame_num:0{frame_count_digits}}/{end_frame} complete", end='\r')

            frame_num += 1
            success, orig = source.read()

    except KeyboardInterrupt:
        print("\nConversion cancelled")
    finally:
        file.close()

    print(f"\nPath file saved to: {output_path}")

if __name__ == "__main__":
    main()
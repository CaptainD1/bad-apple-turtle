import cv2
import potrace
import pickle

VIDEO_PATH = 'BadApple.mp4'
OUTPUT_FILE = "bad_apple_vectors.dat"

def main():

    # Load video and read first frame
    source = cv2.VideoCapture(VIDEO_PATH)
    success, orig = source.read()

    paths = []

    frame = 0
    frameThreshold = 50000

    # Try to save even if process interrupted
    try:
        while success:

            # Flip video and convert to black and white
            image = cv2.flip(cv2.threshold(cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY), 128, 1, cv2.THRESH_BINARY)[1], 0)

            # Vectorize image
            bmp = potrace.Bitmap(image)
            path = bmp.trace(turnpolicy = potrace.TURNPOLICY_BLACK, opttolerance=0.2)

            # Recursively tesselate paths in proper order for coloring
            output_path = []
            tesselate(path, output_path, 0)
            paths.append(output_path)

            print("Frame {} complete".format(frame))

            # Break if frame threshold is reached (for testing)
            if frame > frameThreshold:
                break

            # Increment and read next frame
            frame += 1
            success, orig = source.read()
    finally:
        # Save frame data
        print("Saving data in {}".format(OUTPUT_FILE))
        with open(OUTPUT_FILE, 'wb') as file:
            pickle.dump(paths, file)

def tesselate(path, output, color):
    sub_curves = []
    for curve in path:

        # Remove all children from curve
        sub_curves.extend(curve.children)
        curve.children = []

        # Tesselate parent curve
        tesselated = curve.tesselate()
        output.append((color, tesselated))
    
    # Recursively tesselate all children curves afterwards with inverted color
    if len(sub_curves) > 0:
        tesselate(sub_curves, output, 1 - color)

main()
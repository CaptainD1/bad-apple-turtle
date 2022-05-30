import struct
import numpy.typing as npt

def encode_frame(contours: npt.ArrayLike, hierarchy: npt.ArrayLike) -> bytes:

    # Encode number of contours
    data = struct.pack("<I", len(contours))

    # Encode contour data
    for index, contour in enumerate(contours):
        data += encode_contour(contour, get_color(hierarchy, index))

    # Encode size of frame at beginning
    data = struct.pack("<I", len(data)) + data
    return data

def encode_contour(contour: npt.ArrayLike, color) -> bytes:
    # Encode color, number of points, and point data
    return struct.pack(f"<BI{2*len(contour)}f", color, len(contour),
            *(scalar for point in contour for scalar in point[0]))

def get_color(hierarchy, index):
    parent = hierarchy[0,index,3]
    color = 0
    while parent != -1:
        parent = hierarchy[0,parent,3]
        color = 1 - color

    return color
from abc import abstractmethod
from io import BufferedReader, BufferedWriter
import struct
import pathlib
import typing
import math

import cv2
import numpy.typing as npt
import numpy as np

FILE_VERSIONS = (1, )

class VectorContour:

    _color: int
    _points: npt.ArrayLike

    def __init__(self, color: int, points: npt.ArrayLike):

        self._color = color
        self._points = points

    @property
    def color(self) -> int:
        return self._color

    def __getitem__(self, index: typing.SupportsIndex | typing.Tuple[int]) -> \
            npt.ArrayLike | float:
        return self._points[index]

    def __len__(self) -> int:
        return len(self._points)

    def __iter__(self) -> typing.Iterator[npt.ArrayLike]:
        return (point for point in self._points)

class VectorFrame:

    _contours: typing.List[VectorContour]

    def __init__(self, contours: typing.List[VectorContour] = []):
        self._contours = contours

    def __getitem__(self, index: typing.SupportsIndex | typing.Tuple[int]) -> \
            VectorContour | npt.ArrayLike | float:

        if type(index) == tuple:
            return self._contours[index[0]][index[1:]]
        return self._contours[index]

    def __len__(self) -> int:
        return len(self._contours)

    def __iter__(self) -> typing.Iterator[VectorContour]:
        return (contour for contour in self._contours)

class VectorVideo:

    _frames: typing.List[VectorFrame]
    _framerate: float
    _dimensions: typing.Tuple[int, int]

    def __init__(self, framerate: float, dimensions: typing.Tuple[int, int],
            frames: typing.List[VectorFrame] = []):

        self._frames = frames
        self._framerate = framerate
        self._dimensions = dimensions

    @property
    def framerate(self) -> float:
        return self._framerate

    @property
    def dimensions(self) -> typing.Tuple[int, int]:
        return self._dimensions

    @property
    def frame_count(self) -> int:
        return len(self)

    def __len__(self) -> int:
        return len(self._frames)

    def __getitem__(self, index: typing.SupportsIndex | typing.Tuple[int]) -> VectorFrame | \
            VectorContour | npt.ArrayLike | float:

        if type(index) == tuple:
            return self._frames[index[0]][index[1:]]
        return self._frames[index]

    def __setitem__(self, index: typing.SupportsIndex, value: VectorFrame):
        self._frames[index] = value

    def insert(self, index: typing.SupportsIndex, value: VectorFrame):
        self._frames.insert(index, value)

    def append(self, value: VectorFrame):
        self._frames.append(value)

    def __iter__(self) -> typing.Iterator[VectorFrame]:
        return (frame for frame in self._frames)

class ContourSupplier:

    _source_path: pathlib.Path
    _source: cv2.VideoCapture
    _framerate: float
    _frame_count: int
    _frame_dimensions: typing.Tuple[int, int]
    _threshold: int
    _current_frame: int
    _simplify_level: int

    def __init__(self, source_path: pathlib.Path, threshold=96, simplify_level=0):

        self._source_path = source_path
        self._threshold = threshold
        self._simplify_level = simplify_level
        self._current_frame = 0
        self._source = cv2.VideoCapture(str(source_path))
        self._framerate = self._source.get(cv2.CAP_PROP_FPS)
        self._frame_count = int(self._source.get(cv2.CAP_PROP_FRAME_COUNT))
        self._frame_dimensions = (int(self._source.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self._source.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    @property
    def framerate(self) -> float:
        return self._framerate

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def frame_dimensions(self) -> typing.Tuple[int, int]:
        return self._frame_dimensions

    @property
    def current_frame(self) -> int:
        return self._current_frame

    def seek(self, new_frame: int):
        self._source.set(1, new_frame)
        self._current_frame = new_frame

    def get_contours(self) -> typing.Tuple[typing.List, typing.List]:
        success, orig = self._source.read()

        # Convert video to black and white
        image = cv2.threshold(cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY), self._threshold, 1,
                cv2.THRESH_BINARY)[1]

        self._current_frame += 1

        # Vectorize
        contours, hierarchy = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Simplification
        if self._simplify_level > 0:
            approx = list(contours)

            # Simplify contours based on number of points
            num_points = sum(contour.shape[0] for contour in approx) * math.sqrt(len((approx)))
            eps = 0.0001
            num = 0
            while num_points > 6000:
                peris = [(cv2.arcLength(c, True) if c.size > 0 else 0) for c in approx]
                approx = [cv2.approxPolyDP(approx[i], eps * peri, True)  if approx[i].size > 0 else approx[i] for i, peri in enumerate(peris)]
                num_points = sum(contour.shape[0] for contour in approx) * math.sqrt(len((approx)))
                num += 1
                eps *= 1.1

            if self._simplify_level > 1:
                # Only grab contours above a certain size if there are too many
                for i in range(len(approx)):
                    if approx[i].shape[0] < 3 or self.PolyArea(approx[i][:,0,0], approx[i][:,0,1]) < 5:
                        approx[i] = np.empty((0,1,2), dtype=np.int32)
            
            return approx, hierarchy
        return contours, hierarchy

    @staticmethod
    def PolyArea(x,y):
        return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

class VectorVideoEncoder:
    """
    A class handling encoding of vectorized videos from OpenCV contours
    """

    _video: VectorVideo
    _encode_pointer: int

    def __init__(self, framerate: float, dimensions: typing.Tuple[int, int]):

        self._video = VectorVideo(framerate, dimensions)
        self._encode_pointer = 0

    @property
    def video(self) -> VectorVideo:
        return self._video

    def feed_contours(self,
            contours: typing.List[typing.Tuple[int, typing.List[typing.Tuple[float, float]]]],
            hierarchy: npt.ArrayLike):
        
        frame = VectorFrame([VectorContour(self._get_color(hierarchy, i), points[:,0]) \
                for i, points in enumerate(contours)])

        self._video.append(frame)

    def encode_frame(self, index: typing.SupportsIndex) -> bytes:

        frame: VectorFrame = self._video[index]

        # Encode number of contours
        data = struct.pack("<I", len(frame))

        # Encode contour data
        for contour in frame:
            data += self._encode_contour(contour)

        # Encode size of frame at beginning
        data = struct.pack("<I", len(data)) + data

        return data

    def encode_headers(self) -> bytes:
        return struct.pack("<IfII", FILE_VERSIONS[-1], self._video.framerate,
                self._video.dimensions[0], self._video.dimensions[1])

    def dump_continue(self, buffer: BufferedWriter):
        if self._encode_pointer == 0:
            buffer.write(self.encode_headers())
        for i in range(self._encode_pointer, self._video.frame_count):
            buffer.write(self.encode_frame(i))
            self._encode_pointer = i + 1

    def dump(self, buffer: BufferedWriter):
        buffer.write(self.encode_headers())
        for i in range(self._video.frame_count):
            buffer.write(self.encode_frame(i))

    def trim_dumped(self):
        for i in range(self._encode_pointer):
            self._video[i] = VectorFrame()

    @staticmethod
    def _get_color(hierarchy: npt.ArrayLike, index: typing.SupportsIndex):
        parent = hierarchy[0,index,3]
        color = 0
        while parent != -1:
            parent = hierarchy[0,parent,3]
            color = 1 - color

        return color

    @staticmethod
    def _encode_contour(contour: VectorContour) -> bytes:
        # Encode color, number of points, and point data
        return struct.pack(f"<BI{2*len(contour)}f", contour.color, len(contour),
                *(scalar for point in contour for scalar in point))

class VectorVideoDecoder:
    """
    A base class for handling decoding of vectorized video

    Properties
    ----------
    dimensions : (int, int)
        The width/height of the original video
    framerate : float
        The framerate of the original video
    total_frames : int
        The total number of encoded frames
    current_frame : int
        The next frame to be decoded
    """

    _framerate: float
    _dimensions: typing.Tuple[int, int]
    _total_frames: int
    _frame: int
    _vector_video: VectorVideo

    def __init__(self):
        self._framerate = None
        self._dimensions = None
        self._total_frames = None
        self._frame = 0

    @abstractmethod
    def seek(self, frame_offset: int, whence: int):
        pass

    @abstractmethod
    def read(self) -> VectorFrame:
        pass

    @property
    def dimensions(self) -> typing.Tuple[int, int]:
        return self._dimensions

    @property
    def framerate(self) -> float:
        return self._framerate

    @property
    def total_frames(self) -> int:
        return self._total_frames

    @property
    def current_frame(self) -> int:
        return self._frame

    @property
    def video(self) -> VectorVideo:
        return self._vector_video

class VectorVideoFileDecoder(VectorVideoDecoder):
    """
    A class handling decoding of vectorized videos from files

    ...

    Attributes
    ----------
    vector_file_path : pathlib.Path
        The path to the vector file
    """

    _file_path: pathlib.Path
    _file_object: BufferedReader
    _file_size: int
    _header_size: int

    def __init__(self, vector_file_path: pathlib.Path):

        super().__init__()
        self._file_path = vector_file_path
        self._file_object = None

    def _get_headers(self):
        if self._file_object:
            file_version, = self._get_data("<I")

            if file_version not in FILE_VERSIONS:
                raise TypeError(f"Invalid file format. Wanted '{FILE_VERSIONS}' " \
                        f"but got '{file_version}'.")

            self._header_size = struct.calcsize("<IfII")
            self._file_size = self._file_path.stat().st_size
            self._framerate, width, height = self._get_data("<fII")
            self._dimensions = (width, height)
            self._total_frames = self._count_frames()
            self._vector_video = VectorVideo(self._framerate, self._dimensions)

    def open(self):
        """
        Open the vector file for reading
        """
        self._file_object = self._file_path.open("rb")
        self._get_headers()

    def close(self):
        """
        Close the vector file
        """
        if self._file_object:
            self._file_object.close()
            self._file_object = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def read(self) -> VectorFrame:
        """
        Read the next frame and return it in the form of nested lists

        :return: The decoded vectorized frame

        List Structure
        --------------
        List of Contours:
            Contour (tuple[int, list]):
                Color (int)
                List of Points:
                    Point (tuple[float, float])
        """
        if self._frame < len(self._vector_video):
            frame = self._vector_video[self._frame]
        else:
            frame_size, num_contours = self._get_data("<II")
            contours = []
            for contour_num in range(num_contours):
                color, num_points = self._get_data("<BI")
                points = np.frombuffer(self._file_object.read(struct.calcsize(f"<{num_points*2}f")), dtype="<f4")
                points.shape = (num_points, 2)
                contour = VectorContour(color, points)
                contours.append(contour)

            frame = VectorFrame(contours)
            self._vector_video.insert(self._frame, frame)

        self._frame += 1

        return frame

    def read_all(self) -> VectorVideo:
        while self._frame < self._total_frames:
            self.read()

        return self._vector_video

    def seek(self, frame_offset: int, whence: int = 0):
        """
        Seeks to specific frame in video
        
        :param int frame_offset: The frame to seek to.
        :param int whence: Optional, default 0, which means absolute positioning.
            1 is seek relative to current pointer. 2 is seek relative to end of video.
        """
        if whence == 0:
            relative_offset = frame_offset - self._frame
            frame_num = frame_offset
        elif whence == 1:
            relative_offset = frame_offset
            frame_num = self._frame + relative_offset
        elif whence == 2:
            relative_offset = self._total_frames - frame_offset
            frame_num = self._frame + relative_offset
        else:
            raise ValueError(f"invalid whence ({whence}, should be 0, 1 or 2)")

        # Seek to beginning if frame is before current frame
        if relative_offset < 0:
            self._file_object.seek(self._header_size)
            relative_offset = frame_num

        for i in range(relative_offset):
            frame_size, = self._get_data("<I")
            self._file_object.seek(frame_size, 1)

        self._frame = frame_num

    def read_specific(self, frame_num: int) -> \
            typing.List[typing.Tuple[int, typing.List[typing.Tuple[float, float]]]]:
        """
        Read a specific frame within the vector file without moving the pointer.
        See the read method
        
        :param int frame_num: The frame number to read
        :return: The decoded vectorized frame
        """

        # Find current position to return to
        previous_byte = self._file_object.tell()
        previous_frame = self._frame

        # Seek and read frame
        self.seek(frame_num)
        frame_data = self.read()

        # Return to last position
        self._file_object.seek(previous_byte)
        self._frame = previous_frame

        return frame_data

    def _get_data(self, format: str) -> typing.Tuple:
        size = struct.calcsize(format)
        data = self._file_object.read(size)
        if len(data) == size:
            return struct.unpack(format, data)
        return ()

    def _count_frames(self) -> int:
        last_pos = self._file_object.tell()
        self._file_object.seek(self._header_size)
        pos = self._header_size
        frame_size = 0
        num_frames = 0
        while pos + frame_size < self._file_size:
            frame_size, = self._get_data("<I")
            pos += 4
            self._file_object.seek(frame_size, 1)
            num_frames += 1
            pos += frame_size

        self._file_object.seek(last_pos)

        return num_frames

class VectorVideoLiveDecoder(VectorVideoDecoder):

    _vector_encoder: VectorVideoEncoder
    _contour_supplier: ContourSupplier

    def __init__(self, contour_supplier: ContourSupplier):

        super().__init__()
        self._vector_encoder = VectorVideoEncoder(contour_supplier.framerate,
                contour_supplier.frame_dimensions)
        self._contour_supplier = contour_supplier
        
    @property
    def current_frame(self) -> int:
        return self._contour_supplier.current_frame

    @property
    def framerate(self) -> float:
        return self._contour_supplier.framerate

    @property
    def total_frames(self) -> int:
        return self._contour_supplier.frame_count

    @property
    def dimensions(self) -> typing.Tuple[int, int]:
        return self._contour_supplier.frame_dimensions

    @property
    def video(self) -> VectorVideo:
        return self._vector_encoder.video

    def seek(self, frame_offset: int, whence: int=0):
        if whence == 0:
            self._contour_supplier.seek(frame_offset)
        elif whence == 1:
            self._contour_supplier.seek(self._contour_supplier.current_frame + frame_offset)
        elif whence == 2:
            self._contour_supplier.seek(self._contour_supplier.frame_count - frame_offset)
        else:
            raise ValueError("Whence must be 1, 2 or 3")

    def read(self) -> typing.List[typing.Tuple[int, typing.List[typing.Tuple[float, float]]]]:
        self._vector_encoder.feed_contours(*self._contour_supplier.get_contours())
        return self._vector_encoder.video[-1]
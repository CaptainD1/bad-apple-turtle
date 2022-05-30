from io import BufferedReader
import struct
import pathlib
import typing

class VectorVideoDecoder:
    """
    A class handling decoding of vectorized videos

    ...

    Attributes
    ----------
    vector_file_path : pathlib.Path
        The path to the vector file

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

    _file_path: pathlib.Path
    _framerate: float
    _dimensions: typing.Tuple[int, int]
    _total_frames: int
    _frame: int
    _file_object: BufferedReader

    def __init__(self, vector_file_path: pathlib.Path):

        self._file_path = vector_file_path
        self._framerate = None
        self._dimensions = None
        self._total_frames = None
        self._frame = 0
        self._file_object = None

    def _get_metadata(self):
        if self._file_object:
            self._framerate, self._total_frames, width, height = \
                self._get_data("<fIII")
        else:
            with self._file_path.open('rb') as file:
                self._framerate, self._total_frames, width, height = \
                        struct.unpack(file.read(16), "<fIII")

        self._dimensions = (width, height)

    @property
    def dimensions(self) -> typing.Tuple[int, int]:
        if not self._dimensions:
            self._get_metadata()
        return self._dimensions

    @property
    def framerate(self) -> float:
        if not self._framerate:
            self._get_metadata()
        return self._framerate

    @property
    def total_frames(self) -> int:
        if not self._total_frames:
            self._get_metadata()
        return self._total_frames

    @property
    def current_frame(self) -> int:
        return self._frame

    def open(self):
        """
        Open the vector file for reading
        """
        self._file_object = self._file_path.open("rb")
        self._get_metadata()

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

    def read(self) -> typing.List[typing.Tuple[int, typing.List[typing.Tuple[float, float]]]]:
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
        frame_size, num_contours = self._get_data("<II")
        contours = []
        for contour_num in range(num_contours):
            color, num_points = self._get_data("<BI")
            contour = [self._get_data("<ff") for i in range(num_points)]
            contours.append((color, contour))

        self._frame += 1

        return contours
    
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
            self._file_object.seek(0)
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

    def _get_data(self, format) -> int:
        # TODO: Check if there is remaining data to read in file
        return struct.unpack(format, self._file_object.read(struct.calcsize(format)))
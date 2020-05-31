import cortex.cortex_pb2 as cortex_pb2
import gzip
import os
import struct
from datetime import datetime


class Reader:
    def __init__(self, filename):
        if not filename.endswith('.gz'):
            raise NameError("Expected gz file")
        if not os.path.exists(filename):
            raise IOError("No such file or directory: '{}'".format(filename))
        self.filename = filename
        self.__file_object = gzip.open(self.filename, "r")
        self.user = cortex_pb2.User()
        self.read_user()
        self.snapshot = cortex_pb2.Snapshot()

    def __del__(self):
        # TODO: look for better solution
        if self.__file_object:
            self.__file_object.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__file_object:
            self.__file_object.close()
    #
    # from contextlib import suppress
    #
    # class ContextManager:
    #     def __init__(self, generator):
    #         self.generator = generator
    #
    #     def __enter__(self):
    #         self.execution = self.generator()
    #         return next(self.execution)
    #
    #     def __exit__(self, exception, error, traceback):
    #         # TODO: try to replace 'suppress()' function
    #         with suppress(StopIteration):
    #             if exception:
    #                 self.execution.throw(exception, error, traceback)
    #             else:
    #                 next(self.execution)
    def __iter__(self):
        return self

    def __next__(self):
        self.read_snapshot()
        if self.snapshot:
            return self.snapshot
        else:
            raise StopIteration

    def read_in_chunks(self, chunk_size=1024):
        """Lazy function (or generator) to read a file piece by piece.
        Default chunk size: 1k."""
        while True:
            data = self.__file_object.read(chunk_size)
            if not data:
                break
            # yield data
            return data

    def read_msg(self):
        msg_len, = struct.unpack("I", self.read_in_chunks(4))
        print("len:", msg_len)
        msg = self.read_in_chunks(msg_len)
        return msg

    def read_snapshot(self):
        snapshot_msg = self.read_msg()
        # retrieve snapshot
        self.snapshot.ParseFromString(snapshot_msg)
        #self.prepare_attr()

    def prepare_attr(self):
        if self.snapshot is not None:
            # new class needed for Snapshot ?
            return self.snapshot.color_image

    def read_user(self):
        user_msg = self.read_msg()
        # retrieve user
        self.user.ParseFromString(user_msg)

    @property
    def user_id(self):
        try:
            return self.user.user_id
        except (AttributeError, ValueError):
            return -1

    @property
    def username(self):
        try:
            return self.user.username
        except AttributeError:
            return ""

    @property
    def birthday(self):
        try:
            birthday = self.user.birthday
            return datetime.fromtimestamp(birthday)
        except AttributeError:
            return None

    @property
    def gender(self):
        try:
            gender = self.user.gender
        except AttributeError:
            return ""

        if gender == cortex_pb2.User.Gender.MALE:
            return "m"
        elif gender == cortex_pb2.User.Gender.FEMALE:
            return "f"
        elif gender == cortex_pb2.User.Gender.OTHER:
            return "o"
        else:
            return ""

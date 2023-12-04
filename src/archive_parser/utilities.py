"""
Copyright (c) Cutleast
"""


from io import BufferedReader


def peek(stream: BufferedReader, length: int):
    """
    Peeks into stream and returns data.
    """

    data = stream.read(length)

    stream.seek(-length, 1)

    return data

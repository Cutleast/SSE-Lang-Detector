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

CHAR_WHITELIST = [
    "\n",
    "\r",
    "\t",
    "\u200B",
    "\xa0"
]

def is_valid_string(input_string: str):
    """
    Checks if <input_string> is a valid string.
    """
    if input_string.lower().startswith("data\\"):
        return False

    return all(
        (c.isprintable() or c in CHAR_WHITELIST)
        for c in input_string
    )



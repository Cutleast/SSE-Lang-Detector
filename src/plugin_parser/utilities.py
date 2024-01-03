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
    "\xa0",
]


def is_path_like(text: str):
    """
    Checks if `text` is a path.
    """

    if "\\" not in text and "/" not in text:
        if len(text) <= 4:
            return False
        elif text[-3] == "." or text[-4] == ".":
            return True
        else:
            return False
    else:
        return True


def is_valid_string(input_string: str):
    """
    Checks if <input_string> is a valid string.
    """

    if not input_string.strip():
        return False

    if is_path_like(input_string):
        return False

    return all((c.isprintable() or c in CHAR_WHITELIST) for c in input_string)

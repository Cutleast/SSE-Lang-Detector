"""
Copyright (c) Cutleast
"""

import json
from io import BufferedReader


class Datatype:
    """
    Class for general datatype.
    """

    def __repr__(self):
        __dict = {}

        for key, value in self.__dict__.items():
            __dict[key] = str(value) if (
                not isinstance(value, str) and
                not isinstance(value, int) and
                not isinstance(value, float) and
                not isinstance(value, list) and
                not isinstance(value, dict)
            ) else value

        # return json.dumps(__dict, indent=4)
        return str(self.__dict__)

    def __str__(self):
        return self.__repr__()


"""
This file is part of SEE Lang Detector
and falls under the license
GNU General Public License v3.0.
"""

import logging

import qtpy.QtCore as qtc

print("Importing lingua...")
from lingua import Language, LanguageDetector, LanguageDetectorBuilder


with open("./assets/confidence.txt", "r") as file:
    CONFIDENCE = float(file.read().strip())

print("Detector confidence:", CONFIDENCE)


class LangDetector:
    """
    Language detector class.
    """

    langs: list[Language] = []
    detector: LanguageDetector = None

    def __init__(self, app):
        self.app = app

        self.log = logging.getLogger(self.__repr__())
        self.log.addHandler(self.app.log_str)
        self.log.setLevel(self.app.log.level)

    def __repr__(self):
        return "LangDetector"

    @staticmethod
    def get_available_langs():
        """
        Returns a list of all available languages.
        """

        langs = list(Language.all())
        langs.sort(key=lambda lang: lang.name)

        return langs

    def set_langs(self, langs: list[Language]):
        """
        Sets <langs> and builds language detector.
        """

        self.langs = langs
        self.detector = (
            LanguageDetectorBuilder.from_languages(*self.langs)
            .with_minimum_relative_distance(CONFIDENCE)
            .build()
        )

    def clean_target_lang_strings(
        self,
        strings: list[dict[str, str]],
        target_lang: Language,
        progress_sign: qtc.Signal = None,
        status_sign: qtc.Signal = None,
    ):
        """
        Cleans and returns all strings from <strings>
        that are in the <target_lang>.
        """

        output: list[dict[str, str]] = []

        if progress_sign:
            progress_sign.emit((0, len(strings), 0))

        for c, string in enumerate(strings):
            if (  # Skip string if in dictionary
                string["editor_id"] in self.app.dict.edids
                or string["string"] in self.app.dict.strings
            ):
                continue

            if progress_sign:
                progress_sign.emit((0, len(strings), c))
            if status_sign:
                status_sign.emit(f"Processing string {c}/{len(strings)}...")
            else:
                self.log.debug(f"Processing string {c}/{len(strings)}...")

            if (
                lang := self.detect_lang(string["string"])
            ) != target_lang and lang is not None:
                output.append(string)

        if not status_sign:
            self.log.debug(
                f"Found {len(output)} string(s) that are not in {target_lang}."
            )

        return output

    def has_untranslated_strings(
        self, strings: list[dict[str, str]], target_lang: Language, treshold: int = 10
    ):
        """
        Scans until <treshold> number of untranslated strings are found.
        Returns True if there are at least <treshold> untranslated strings
        and False if the number is below <treshold>.
        """

        number_of_untranslated_strings = 0

        for string in strings:
            if (  # Skip string if in dictionary
                string["editor_id"] in self.app.dict.edids
                or string["string"] in self.app.dict.strings
            ):
                continue

            if self.detect_lang(string["string"]) != target_lang:
                number_of_untranslated_strings += 1

            if number_of_untranslated_strings >= treshold:
                return True

        return False

    def detect_lang(self, string: str):
        """
        Detects language of <string> and returns it.
        """

        lang = self.detector.detect_language_of(string)

        return lang

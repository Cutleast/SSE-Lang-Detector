"""
This file is part of SEE Lang Detector
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
from pathlib import Path
from typing import Optional
import PySide6.QtCore
import PySide6.QtWidgets

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

from string_preview import StringPreview


class FileEntry(qtc.QObject):
    """
    Class for file entries.
    """

    set_num_sign = qtc.Signal(str)
    status_sign = qtc.Signal(str)
    progress_sign = qtc.Signal(tuple)
    incr_progress_sign = qtc.Signal()
    progress_error_sign = qtc.Signal()
    file_path: Path = None
    strings: list[dict[str, str]] = None
    untranslated_strings: list[dict[str, str]] = None
    enable_preview_btn_sign = qtc.Signal()
    set_visible_sign = qtc.Signal(bool)
    bsa: bool = False
    display_name: str = None

    def __init__(self, app, file: Path):
        super().__init__()

        self.app = app
        self.file_path = file
    
    def __repr__(self) -> str:
        return str(self.display_name)

    def init_widget(self):
        if self.display_name is not None:
            return

        if self.bsa:
            self.display_name = f"[BSA] {self.file_path.name}"
        else:
            self.display_name = self.file_path.name

        self.progress_widget = ProgressWidget()
        self.progress_widget.status_label.setText("Idle...")
        self.status_sign.connect(self.progress_widget.status_label.setText)
        self.progress_sign.connect(
            lambda p: (
                self.progress_widget.progress_bar.setRange(p[0], p[1]),
                self.progress_widget.progress_bar.setValue(p[2]),
                self.progress_widget.progress_bar.setVisible(True),
            )
        )
        self.incr_progress_sign.connect(
            lambda: (
                self.progress_widget.progress_bar.setValue(
                    self.progress_widget.progress_bar.value() + 1
                ),
                self.progress_widget.progress_bar.setVisible(True),
            )
        )
        self.progress_error_sign.connect(
            lambda: (
                self.progress_widget.progress_bar.setObjectName("finished_statistic"),
                self.progress_widget.progress_bar.setStyleSheet(self.app.styleSheet()),
                self.progress_widget.progress_bar.setRange(0, 1),
                self.progress_widget.progress_bar.setValue(1),
            )
        )

        self.num_label = qtw.QLabel()
        self.num_label.setText("Unknown")

        def update_num(num: str):
            if self.strings:
                self.progress_widget.progress_bar.setObjectName("finished_statistic")
                self.progress_widget.progress_bar.setStyleSheet(self.app.styleSheet())
                self.progress_widget.progress_bar.setRange(0, len(self.strings))
                self.progress_widget.progress_bar.setValue(len(self.untranslated_strings))
            else:
                self.progress_widget.progress_bar.setRange(0, 1)
                self.progress_widget.progress_bar.setValue(1)

            self.num_label.setText(num)

        self.set_num_sign.connect(update_num)
    
    def destroy(self):
        if self.display_name:
            self.progress_widget.deleteLater()
            # del self.progress_widget
            self.num_label.deleteLater()
            # del self.num_label
        # del self
    
    def open_file(self):
        """
        Opens file with standard application.
        """

        if self.file_path.is_file():
            os.startfile(self.file_path)
        else:
            qtw.QMessageBox.critical(
                self.app.root,
                "Error - File does not exist!",
                f"File '{self.file_path}' does not exist!"
            )

    def extract_strings(self):
        """
        Extracts strings from plugin.
        """

        raise NotImplementedError

    def preview_strings(self):
        """
        Opens preview dialog with strings.
        """

        preview = StringPreview(self.app, self)
        preview.exec()


class ProgressWidget(qtw.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._layout = qtw.QVBoxLayout()
        self._layout.setSpacing(0)
        self._layout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        self.setLayout(self._layout)

        self.status_label = qtw.QLabel()
        self.status_label.setObjectName("status_label")
        self._layout.addWidget(self.status_label)

        self._layout.addSpacing(2)

        self.progress_bar = qtw.QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(2)
        self._layout.addWidget(self.progress_bar)

        self.setFixedHeight(30)

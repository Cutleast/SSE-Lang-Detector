"""
This file is part of SEE Lang Detector
and falls under the license
GNU General Public License v3.0.
"""

import os

import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils
from main import MainApp

from .updater import Updater


class UpdaterDialog(qtw.QDialog):
    """
    Class for updater dialog.
    """

    def __init__(self, app: MainApp, updater: Updater):
        super().__init__(app.root)

        self.setWindowTitle("An Update is Available!")

        self.app = app
        self.updater = updater

        self.log = updater.log

        vlayout = qtw.QVBoxLayout()
        self.setLayout(vlayout)

        title_label = qtw.QLabel("An Update is Available to Download!")
        title_label.setObjectName("titlelabel")
        vlayout.addWidget(title_label)

        version_label = qtw.QLabel(
            f"\
Installed Version: {updater.installed_version} \
Latest Version: {updater.latest_version}"
        )
        version_label.setObjectName("relevant_label")
        vlayout.addWidget(version_label)

        changelog_box = qtw.QTextBrowser()
        changelog_box.setMarkdown(updater.get_changelog())
        changelog_box.setCurrentFont(qtg.QFont("Arial"))
        vlayout.addWidget(changelog_box, 1)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.cancel_button = qtw.QPushButton("Ignore Update")
        self.cancel_button.clicked.connect(self.accept)
        hlayout.addWidget(self.cancel_button)

        hlayout.addStretch()

        download_button = qtw.QPushButton("Download Update")
        download_button.clicked.connect(
            lambda: (
                os.startfile(updater.download_url),
                self.accept(),
            )
        )
        hlayout.addWidget(download_button)

        self.exec()

    def exec(self):
        self.show()
        self.resize(700, 400)

        utils.center(self)

        super().exec()

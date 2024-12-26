"""
This file is part of SEE Lang Detector
and falls under the license
GNU General Public License v3.0.
"""

# Import libraries
import PySide6.QtGui
import pyperclip as clipboard

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils


class ErrorDialog(qtw.QMessageBox):
    """
    Custom error messagebox with short text
    and detailed text functionality.

    Parameters:
        parent: QWidget (parent window)
        title: str (window title)
        text: str (short message)
        details: str (will be displayed when details are shown)
        yesno: bool (determines if 'continue' and 'cancel' buttons are shown
        or only an 'ok' button)
    """

    def __init__(
        self,
        parent: qtw.QWidget,
        title: str,
        text: str,
        details: str = "",
        yesno: bool = True,
    ):
        super().__init__(parent)

        # Basic configuration
        self.setWindowTitle(title)
        self.setIcon(qtw.QMessageBox.Icon.Critical)
        self.setText(text)

        # Show 'continue' and 'cancel' button
        if yesno:
            self.setStandardButtons(
                qtw.QMessageBox.StandardButton.No | qtw.QMessageBox.StandardButton.Yes
            )
            self.button(qtw.QMessageBox.StandardButton.Yes).setText(
                "Continue"
            )
            self.button(qtw.QMessageBox.StandardButton.No).setText(
                "Exit Application"
            )

        # Only show 'ok' button
        else:
            self.setStandardButtons(qtw.QMessageBox.StandardButton.Ok)

        # Add details button if details are given
        if details:
            self.details_button: qtw.QPushButton = self.addButton(
                "Show Details...", qtw.QMessageBox.ButtonRole.AcceptRole
            )
            self.details_button.setIcon(qta.icon("fa5s.chevron-down", color="#ffffff"))

            self._details = False

            def toggle_details():
                # toggle details
                if not self._details:
                    self._details = True
                    self.details_button.setText("Hide Details...")
                    self.details_button.setIcon(qta.icon("fa5s.chevron-up", color="#ffffff"))
                    self.setInformativeText(f"<font><p style='font-family: Consolas;font-size: 12px'>{details}</p>")
                else:
                    self._details = False
                    self.details_button.setText("Show Details...")
                    self.details_button.setIcon(qta.icon("fa5s.chevron-down", color="#ffffff"))
                    self.setInformativeText("")

                # update messagebox size
                # and move messagebox to center of screen
                self.adjustSize()

            self.details_button.clicked.disconnect()
            self.details_button.clicked.connect(toggle_details)
            self.copy_button: qtw.QPushButton = self.addButton(
                "", qtw.QMessageBox.ButtonRole.AcceptRole
            )
            self.copy_button.setText("")
            self.copy_button.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))
            self.copy_button.clicked.disconnect()
            self.copy_button.clicked.connect(lambda: clipboard.copy(details))

    def closeEvent(self, event: qtg.QCloseEvent):
        event.ignore()
        self.button(qtw.QMessageBox.StandardButton.Yes).clicked.emit()

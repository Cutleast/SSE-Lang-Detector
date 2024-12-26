"""
This file is part of SEE Lang Detector
and falls under the license
GNU General Public License v3.0.
"""

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw
from pyperclip import copy

import utilities as utils


class StringPreview(qtw.QDialog):
    """
    Dialog window for string preview.
    """

    def __init__(self, app, file):
        super().__init__()

        self.app = app
        self.file = file
        self.setStyleSheet(self.app.root.styleSheet())
        self.setWindowTitle(
            f"{app.name} v{app.version} - {file.file_path.name} Preview"
        )
        self.setWindowIcon(app.root.windowIcon())
        self.setMinimumSize(800, 600)

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self.strings_widget = qtw.QTreeView()
        self.strings_widget.setContextMenuPolicy(
            qtc.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.strings_widget.customContextMenuRequested.connect(self.on_context_menu)
        self.strings_widget.setAlternatingRowColors(True)
        self.strings_widget.setSortingEnabled(True)
        self.strings_widget.setEditTriggers(qtw.QTreeView.EditTrigger.NoEditTriggers)
        self.strings_widget.setSelectionMode(
            qtw.QTreeView.SelectionMode.ExtendedSelection
        )
        self.strings_widget.setVerticalScrollBarPolicy(
            qtc.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        layout.addWidget(self.strings_widget)

        # Tree view model for strings
        self.strings_model = qtg.QStandardItemModel()
        self.strings_model.setColumnCount(3)
        self.strings_model.setHeaderData(0, qtc.Qt.Orientation.Horizontal, "Type")
        self.strings_model.setHeaderData(1, qtc.Qt.Orientation.Horizontal, "EDID")
        self.strings_model.setHeaderData(2, qtc.Qt.Orientation.Horizontal, "String")
        self.strings_widget.setModel(self.strings_model)

        self.strings_widget.header().setSectionResizeMode(
            0, qtw.QHeaderView.ResizeMode.ResizeToContents
        )
        self.strings_widget.header().setSectionResizeMode(
            1, qtw.QHeaderView.ResizeMode.ResizeToContents
        )
        self.strings_widget.header().setStretchLastSection(True)

        # Display strings
        for string_data in self.file.untranslated_strings:
            type_item = qtg.QStandardItem()
            type_item.setText(string_data.get("type", ""))
            type_item.setEditable(False)
            edid_item = qtg.QStandardItem()
            edid_item.setText(string_data.get("editor_id", ""))
            edid_item.setEditable(False)
            string_item = qtg.QStandardItem()
            string_item.setText(string_data.get("string", ""))
            string_item.setEditable(False)
            self.strings_model.appendRow([type_item, edid_item, string_item])

        utils.apply_dark_titlebar(self)

    def on_context_menu(self, point: qtc.QPoint):
        """
        Opens context menu at <point>.
        """

        current_selection = self.strings_widget.selectedIndexes()
        current_selection = [
            self.strings_model.itemFromIndex(index) for index in current_selection
        ]

        menu = qtw.QMenu()
        menu.setStyleSheet(self.app.root.styleSheet())

        add_strings_to_dictionary_action = menu.addAction("Add String(s) to Dictionary")
        add_strings_to_dictionary_action.setIcon(
            qta.icon("ri.play-list-add-line", color="#ffffff")
        )
        add_strings_to_dictionary_action.setIconVisibleInMenu(True)
        add_strings_to_dictionary_action.triggered.connect(
            self.add_strings_to_dictionary
        )
        menu.addAction(add_strings_to_dictionary_action)

        add_edid_to_dictionary_action = menu.addAction("Add EDID(s) to Dictionary")
        add_edid_to_dictionary_action.setIcon(
            qta.icon("ri.play-list-add-line", color="#ffffff")
        )
        add_edid_to_dictionary_action.setIconVisibleInMenu(True)
        add_edid_to_dictionary_action.triggered.connect(self.add_edid_to_dictionary)
        menu.addAction(add_edid_to_dictionary_action)

        copy_strings = menu.addAction("Copy String(s) to Clipboard")
        copy_strings.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))
        copy_strings.setIconVisibleInMenu(True)
        copy_strings.triggered.connect(self.copy_strings)
        menu.addAction(copy_strings)

        copy_edids = menu.addAction("Copy EDID(s) to Clipboard")
        copy_edids.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))
        copy_edids.setIconVisibleInMenu(True)
        copy_edids.triggered.connect(self.copy_edids)
        menu.addAction(copy_edids)

        menu.exec(self.strings_widget.mapToGlobal(point))

    def copy_strings(self):
        """
        Copies current selected strings to clipboard.
        """

        # Get current selection
        current_selection = self.strings_widget.selectedIndexes()
        current_rows = [index.row() for index in current_selection]
        current_rows = list(set(current_rows))

        current_item_rows: list[
            tuple[qtg.QStandardItem, qtg.QStandardItem, qtg.QStandardItem]
        ] = []

        for row in current_rows:
            current_item_rows.append(
                (
                    self.strings_model.item(row, 0),
                    self.strings_model.item(row, 1),
                    self.strings_model.item(row, 2),
                )
            )

        clipboard_text = ""
        for item_row in current_item_rows:
            string_type, edid, string = item_row
            clipboard_text += string.text() + "\n"

        copy(clipboard_text)

    def copy_edids(self):
        """
        Copies current selected edids to clipboard.
        """

        # Get current selection
        current_selection = self.strings_widget.selectedIndexes()
        current_rows = [index.row() for index in current_selection]
        current_rows = list(set(current_rows))

        current_item_rows: list[
            tuple[qtg.QStandardItem, qtg.QStandardItem, qtg.QStandardItem]
        ] = []

        for row in current_rows:
            current_item_rows.append(
                (
                    self.strings_model.item(row, 0),
                    self.strings_model.item(row, 1),
                    self.strings_model.item(row, 2),
                )
            )

        clipboard_text = ""
        for item_row in current_item_rows:
            string_type, edid, string = item_row
            clipboard_text += edid.text() + "\n"

        copy(clipboard_text)

    def add_strings_to_dictionary(self):
        """
        Adds current selected strings to dictionary.
        """

        # Get current selection
        current_selection = self.strings_widget.selectedIndexes()
        current_rows = [index.row() for index in current_selection]
        current_rows = list(set(current_rows))

        current_item_rows: list[
            tuple[qtg.QStandardItem, qtg.QStandardItem, qtg.QStandardItem]
        ] = []

        for row in current_rows:
            current_item_rows.append(
                (
                    self.strings_model.item(row, 0),
                    self.strings_model.item(row, 1),
                    self.strings_model.item(row, 2),
                )
            )

        for item_row in current_item_rows:
            string_type, edid, string = item_row
            if not edid.text():
                edid = None
            else:
                edid = edid.text()
            self.file.untranslated_strings.remove(
                {"type": string_type.text(), "editor_id": edid, "string": string.text()}
            )
            self.file.set_num_sign.emit(
                f"{len(self.file.untranslated_strings)}/{len(self.file.strings)}"
            )
            self.app.dict.add_string(string.text())
            self.strings_model.removeRow(item_row[0].row())

        if current_item_rows and not self.file.untranslated_strings:
            self.app.untranslated_num -= 1
            self.app.untranslated_num_label.setText(
                f"Untranslated Files: {self.app.untranslated_num}"
            )
            self.app.progress_bar.setValue(self.app.untranslated_num)

    def add_edid_to_dictionary(self):
        """
        Adds current selected edids to dictionary.
        """

        # Get current selection
        current_selection = self.strings_widget.selectedIndexes()
        current_rows = [index.row() for index in current_selection]
        current_rows = list(set(current_rows))

        current_item_rows: list[
            tuple[qtg.QStandardItem, qtg.QStandardItem, qtg.QStandardItem]
        ] = []

        for row in current_rows:
            current_item_rows.append(
                (
                    self.strings_model.item(row, 0),
                    self.strings_model.item(row, 1),
                    self.strings_model.item(row, 2),
                )
            )

        for item_row in current_item_rows:
            string_type, edid, string = item_row
            if not edid.text():
                continue
            self.file.untranslated_strings.remove(
                {
                    "type": string_type.text(),
                    "editor_id": edid.text(),
                    "string": string.text(),
                }
            )
            self.file.set_num_sign.emit(
                f"{len(self.file.untranslated_strings)}/{len(self.file.strings)}"
            )
            self.app.dict.add_edid(edid.text())
            self.strings_model.removeRow(item_row[0].row())

        if current_item_rows and not self.file.untranslated_strings:
            self.app.untranslated_num -= 1
            self.app.untranslated_num_label.setText(
                f"Untranslated Files: {self.app.untranslated_num}"
            )
            self.app.progress_bar.setValue(self.app.untranslated_num)

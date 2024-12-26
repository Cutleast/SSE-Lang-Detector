"""
Name: SSE Lang Detector
Author: Cutleast
License: Attribution-NonCommercial-NoDerivatives 4.0 International
Python Version: 3.11.2
Qt Version: 6.5.2
"""


import json
import logging
import os
import shutil
import sys
import time
import traceback
import winreg
from winsound import MessageBeep as alert
from pathlib import Path
from queue import Empty, Queue

from pyperclip import copy

print("Importing Qt...")
import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils
from archive_parser.archive_parser import ArchiveParser
from detector import LangDetector, Language
from dictionary import Dictionary
from error_dialog import ErrorDialog
from file_entry import FileEntry
from file_list_table import FileListTable
from loading_dialog import LoadingDialog
from mcm_file import MCMEntry
from plugin import PluginEntry
from plugin_loader import PluginLoader
from script_entry import ScriptEntry


class MainApp(qtw.QApplication):
    """
    Main application class.
    """

    name = "SSE Lang Detector"
    version = "1.1.1"

    queue: Queue = None
    done_signal = qtc.Signal()
    incr_progress_sign = qtc.Signal()
    incr_untranslated_sign = qtc.Signal()
    num_threads: int = None
    original_lang: Language = None
    desired_lang: Language = None
    threads: list[utils.Thread] = []
    all_files: list[FileEntry] = []
    relevant_files: list[FileEntry] = []
    untranslated_num: int = 0
    prev_search: str = ""
    file_list_table: FileListTable = None
    plugin_loader: PluginLoader = None
    include_mcms: bool = None
    include_scripts: bool = None
    include_bsas: bool = None
    start_time: int = None
    hide_translated: bool = False

    def __init__(self):
        super().__init__([])

        self.setStyleSheet(Path("./assets/style.qss").read_text())
        self.done_signal.connect(self.on_finish)

        self.log = logging.getLogger(self.__repr__())
        log_fmt = "[%(asctime)s.%(msecs)03d]"
        log_fmt += "[%(levelname)s]"
        log_fmt += "[%(name)s.%(funcName)s]: "
        log_fmt += "%(message)s"
        self.log_fmt = logging.Formatter(log_fmt, datefmt="%d.%m.%Y %H:%M:%S")
        self.std_handler = utils.StdoutHandler(self)
        self.log_str = logging.StreamHandler(self.std_handler)
        self.log_str.setFormatter(self.log_fmt)
        self.log.addHandler(self.log_str)
        self.log.setLevel(logging.DEBUG)
        self._excepthook = sys.excepthook
        sys.excepthook = self.handle_exception

        self.dict = Dictionary()

        self.root = qtw.QMainWindow()
        self.root.setWindowTitle(f"{self.name} v{self.version}")
        self.root.setWindowIcon(qtg.QIcon("./assets/icon.svg"))
        try:
            utils.apply_dark_titlebar(self.root)
        except:
            pass

        # Run Updater
        Updater(self)

        self.root_widget = qtw.QWidget()
        self.root_widget.setObjectName("root")
        self.root.setCentralWidget(self.root_widget)
        self.root_layout = qtw.QVBoxLayout()
        self.root_layout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        self.root_widget.setLayout(self.root_layout)

        reload_shortcut = qtg.QShortcut(qtg.QKeySequence("F5"), self.root)
        reload_shortcut.activated.connect(self.update_file_list)

        self.config_widget = qtw.QWidget()
        self.config_widget.setObjectName("config")
        self.root_layout.addWidget(self.config_widget)

        self.config_layout = qtw.QGridLayout()
        self.config_layout.setColumnStretch(0, 1)
        self.config_layout.setColumnStretch(1, 1)
        self.config_layout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        self.config_widget.setLayout(self.config_layout)

        self.left_col_layout = qtw.QFormLayout()
        self.config_layout.addLayout(self.left_col_layout, 0, 0)

        self.original_lang_dropdown = qtw.QComboBox()
        self.original_lang_dropdown.setEditable(False)
        self.original_lang_dropdown.addItems(
            [
                str(lang).removeprefix("Language.").capitalize()
                for lang in LangDetector.get_available_langs()
            ]
        )
        self.original_lang_dropdown.setCurrentText("English")
        self.left_col_layout.addRow("Original Language:", self.original_lang_dropdown)

        self.desired_lang_dropdown = qtw.QComboBox()
        self.desired_lang_dropdown.setEditable(False)
        self.desired_lang_dropdown.addItems(
            [
                str(lang).removeprefix("Language.").capitalize()
                for lang in LangDetector.get_available_langs()
            ]
        )
        self.desired_lang_dropdown.setCurrentText("German")
        self.left_col_layout.addRow("Desired Language:", self.desired_lang_dropdown)

        self.untranslated_num_label = qtw.QLabel("Untranslated Files: 0")
        self.untranslated_num_label.setObjectName("untranslated_num_label")

        def incr_untranslated_mods():
            self.untranslated_num += 1
            self.untranslated_num_label.setText(
                f"Untranslated Files: {self.untranslated_num}"
            )

        self.incr_untranslated_sign.connect(incr_untranslated_mods)
        self.hide_translated_button = qtw.QPushButton("Show only untranslated Files")
        self.hide_translated_button.setDisabled(True)

        def hide_translated_files():
            self.hide_translated = not self.hide_translated
            self.update_file_list()

        self.hide_translated_button.clicked.connect(hide_translated_files)
        self.hide_translated_button.setCheckable(True)
        self.left_col_layout.addRow(
            self.untranslated_num_label, self.hide_translated_button
        )

        self.run_button = qtw.QPushButton("Run")
        self.run_button.clicked.connect(self.run)
        self.left_col_layout.addRow(self.run_button)

        self.right_col_layout = qtw.QGridLayout()
        self.right_col_layout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        self.config_layout.addLayout(self.right_col_layout, 0, 1, 1, 2)

        loadorder_label = qtw.QLabel("Path to loadorder.txt:")
        self.right_col_layout.addWidget(loadorder_label, 0, 0)

        self.loadorder_path_entry = qtw.QLineEdit()
        self.loadorder_path_entry.setReadOnly(True)
        self.right_col_layout.addWidget(self.loadorder_path_entry, 0, 1)

        self.browse_loadorder_button = qtw.QPushButton()
        self.browse_loadorder_button.setIcon(
            qta.icon("fa.folder-open", color="#ffffff")
        )
        self.browse_loadorder_button.setIconSize(qtc.QSize(16, 16))

        def browse_loadorder_txt():
            file_dialog = qtw.QFileDialog(self.root)
            file_dialog.setWindowTitle("Browse loadorder.txt...")
            path = (
                Path(self.loadorder_path_entry.text())
                if self.loadorder_path_entry.text()
                else Path(".")
            )
            path = path.resolve()
            file_dialog.setDirectory(str(path.parent))
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.ExistingFile)
            file_dialog.setNameFilter("Loadorder file (loadorder.txt)")
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.loadorder_path_entry.setText(folder)

        self.browse_loadorder_button.clicked.connect(browse_loadorder_txt)
        self.right_col_layout.addWidget(self.browse_loadorder_button, 0, 2)

        data_folder_label = qtw.QLabel("Path to Skyrim's Data folder:")
        self.right_col_layout.addWidget(data_folder_label, 1, 0)

        self.data_folder_entry = qtw.QLineEdit()
        self.data_folder_entry.setReadOnly(True)
        self.right_col_layout.addWidget(self.data_folder_entry, 1, 1)

        self.browse_data_folder_button = qtw.QPushButton()
        self.browse_data_folder_button.setIcon(
            qta.icon("fa.folder-open", color="#ffffff")
        )
        self.browse_data_folder_button.setIconSize(qtc.QSize(16, 16))

        def browse_data_folder():
            file_dialog = qtw.QFileDialog(self.root)
            file_dialog.setWindowTitle("Browse Data folder...")
            path = (
                Path(self.data_folder_entry.text())
                if self.data_folder_entry.text()
                else Path(".")
            )
            path = path.resolve()
            file_dialog.setDirectory(str(path.parent))
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            if file_dialog.exec():
                folder = file_dialog.selectedFiles()[0]
                folder = os.path.normpath(folder)
                self.data_folder_entry.setText(folder)

        self.browse_data_folder_button.clicked.connect(browse_data_folder)
        self.right_col_layout.addWidget(self.browse_data_folder_button, 1, 2)

        thread_num_label = qtw.QLabel("Number of Threads:")
        self.right_col_layout.addWidget(thread_num_label, 2, 0)

        self.thread_num_dropdown = qtw.QComboBox()
        self.thread_num_dropdown.setEditable(False)
        self.thread_num_dropdown.addItems([str(i) for i in range(1, 11)])
        self.thread_num_dropdown.setCurrentIndex(0)
        self.right_col_layout.addWidget(self.thread_num_dropdown, 2, 1, 1, 2)

        inclusion_layout = qtw.QHBoxLayout()
        self.right_col_layout.addLayout(inclusion_layout, 3, 0, 1, 3)
        self.ignore_base_game_checkbox = qtw.QCheckBox(
            "Ignore Base Game plugins (& AE CC)"
        )
        self.ignore_base_game_checkbox.setChecked(True)
        inclusion_layout.addWidget(self.ignore_base_game_checkbox)
        self.include_mcms_checkbox = qtw.QCheckBox("Include MCM files (*.txt)")
        inclusion_layout.addWidget(self.include_mcms_checkbox)
        self.include_scripts_checkbox = qtw.QCheckBox("Include Script files (*.pex)")
        inclusion_layout.addWidget(self.include_scripts_checkbox)
        self.include_bsas_checkbox = qtw.QCheckBox("Include Archives (*.bsa)")
        inclusion_layout.addWidget(self.include_bsas_checkbox)

        self.status_label = qtw.QLabel()
        self.status_label.setSizePolicy(
            qtw.QSizePolicy.Policy.Maximum, qtw.QSizePolicy.Policy.Preferred
        )
        self.status_label.setObjectName("status_label")
        self.std_handler.output_signal.connect(
            lambda text: self.status_label.setText(text)
        )
        self.config_layout.addWidget(self.status_label, 1, 0, 1, 2)

        self.progress_bar = qtw.QProgressBar()
        self.progress_bar.setFormat("%v/%m (%p%)")
        self.progress_bar.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)

        def incr_progress():
            self.progress_bar.setValue(self.progress_bar.value() + 1)
            if self.progress_bar.value() == self.progress_bar.maximum():
                self.done_signal.emit()

        self.incr_progress_sign.connect(incr_progress)
        self.config_layout.addWidget(self.progress_bar, 2, 0, 1, 2)

        self.copy_button = qtw.QPushButton()
        self.copy_button.setToolTip("Copy full log to clipboard")
        self.copy_button.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))
        self.copy_button.setIconSize(qtc.QSize(16, 16))
        self.copy_button.clicked.connect(lambda: copy(self.std_handler._content))
        self.config_layout.addWidget(self.copy_button, 1, 2, 2, 1)

        # Create box
        self.search_box = qtw.QLineEdit()
        self.search_box.setClearButtonEnabled(True)
        self.search_icon: qtg.QAction = self.search_box.addAction(
            qta.icon("fa.search", color="#ffffff"),
            qtw.QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search_box.textChanged.connect(lambda text: self.update_file_list())
        self.search_box.setPlaceholderText("Search for files...")
        self.search_box.returnPressed.connect(self.update_file_list)
        self.root_layout.addWidget(self.search_box)

        self.file_list_table = FileListTable()
        self.file_list_table.setObjectName("file_list")
        self.file_list_table.setAlternatingRowColors(True)
        self.file_list_table.setFocusPolicy(qtc.Qt.FocusPolicy.NoFocus)
        self.file_list_table.setContextMenuPolicy(
            qtc.Qt.ContextMenuPolicy.CustomContextMenu
        )

        def on_double_click(index: qtc.QModelIndex):
            current_rindex = index.row()
            column = index.column()
            file = self.all_files[current_rindex]

            if file.untranslated_strings and column == 2:
                file.preview_strings()
            elif column == 1:
                file.open_file()

        self.file_list_table.doubleClicked.connect(on_double_click)

        def on_context_menu(point: qtc.QPoint):
            current_rindex = self.file_list_table.currentIndex().row()
            file = self.all_files[current_rindex]

            menu = qtw.QMenu()

            open_preview_action = menu.addAction("Open String Preview")
            open_preview_action.setIcon(qta.icon("msc.open-preview", color="#ffffff"))
            open_preview_action.setIconVisibleInMenu(True)
            open_preview_action.setDisabled(not file.untranslated_strings)
            open_preview_action.triggered.connect(lambda: file.preview_strings())

            open_external_action = menu.addAction("Open File")
            open_external_action.setIcon(
                qta.icon("fa5s.external-link-alt", color="#ffffff")
            )
            open_external_action.setIconVisibleInMenu(True)
            open_external_action.triggered.connect(lambda: file.open_file())

            open_explorer_action = menu.addAction("Open in Explorer (Vortex only)")
            open_explorer_action.setIcon(qta.icon("fa5s.folder", color="#ffffff"))
            open_explorer_action.triggered.connect(
                lambda: os.system(f'explorer.exe /select,"{file.file_path}"')
            )

            menu.exec(self.file_list_table.mapToGlobal(point))

        self.file_list_table.customContextMenuRequested.connect(on_context_menu)

        self.file_list_table.setVerticalScrollBarPolicy(
            qtc.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        headers = [
            "",  # Loadorder priority
            "Name",
            "Untranslated Strings",
            "Status/Progress",
        ]
        self.file_list_table.setHeaders(headers)
        self.root_layout.addWidget(self.file_list_table)

        # Configure columns and remove vertical header
        self.file_list_table.verticalHeader().hide()
        self.file_list_table.horizontalHeader().setSectionResizeMode(
            0, qtw.QHeaderView.ResizeMode.Fixed
        )
        self.file_list_table.horizontalHeader().resizeSection(0, 50)
        self.file_list_table.horizontalHeader().setSectionResizeMode(
            1, qtw.QHeaderView.ResizeMode.Stretch
        )
        self.file_list_table.horizontalHeader().resizeSection(2, 170)
        self.file_list_table.horizontalHeader().setSectionResizeMode(
            2, qtw.QHeaderView.ResizeMode.Fixed
        )
        self.file_list_table.horizontalHeader().resizeSection(3, 250)
        self.file_list_table.horizontalHeader().setSectionResizeMode(
            3, qtw.QHeaderView.ResizeMode.Fixed
        )

    def update_file_list(self):
        self.ignore_base_game = self.ignore_base_game_checkbox.isChecked()
        self.include_mcms = self.include_mcms_checkbox.isChecked()
        self.include_scripts = self.include_scripts_checkbox.isChecked()
        self.include_bsas = self.include_bsas_checkbox.isChecked()

        cur_search = self.search_box.text()
        if cur_search != self.prev_search:
            self.prev_search = cur_search

            for rindex, row in enumerate(self.file_list_table.rows):
                name: str = row[1]
                file = self.all_files[rindex]
                if file in self.relevant_files:
                    self.file_list_table.setRowHidden(
                        rindex,
                        cur_search.lower() not in name.lower()
                        or (self.hide_translated and not file.untranslated_strings),
                    )
        else:
            self.relevant_files.clear()
            for rindex in range(len(self.all_files)):
                self.file_list_table.setRowHidden(rindex, True)
            for rindex, file in enumerate(self.all_files):
                if file.bsa and not self.include_bsas:
                    continue
                elif isinstance(file, MCMEntry) and not self.include_mcms:
                    continue
                elif isinstance(file, ScriptEntry) and not self.include_scripts:
                    continue
                elif self.ignore_base_game:
                    if file.file_path.name.lower() in self.plugin_loader.AE_CC_PLUGINS:
                        continue
                    elif (
                        file.file_path.name.lower()
                        in self.plugin_loader.BASE_GAME_PLUGINS
                    ):
                        continue
                self.relevant_files.append(file)
                if cur_search:
                    self.file_list_table.setRowHidden(
                        rindex,
                        cur_search.lower() not in file.display_name.lower()
                        or (self.hide_translated and not file.untranslated_strings),
                    )
                else:
                    self.file_list_table.setRowHidden(
                        rindex, (self.hide_translated and not file.untranslated_strings)
                    )

    def save_config(self):
        config = {
            "original_lang": self.original_lang_dropdown.currentText(),
            "desired_lang": self.desired_lang_dropdown.currentText(),
            "loadorder_path": self.loadorder_path_entry.text(),
            "data_path": self.data_folder_entry.text(),
            "thread_number": int(self.thread_num_dropdown.currentText()),
            "ignore_base_game": self.ignore_base_game_checkbox.isChecked(),
            "include_mcms": self.include_mcms_checkbox.isChecked(),
            "include_scripts": self.include_scripts_checkbox.isChecked(),
            "include_bsas": self.include_bsas_checkbox.isChecked(),
        }

        with open(Path("./assets/config.json").resolve(), "w", encoding="utf8") as file:
            json.dump(config, file, indent=4)

    def load_config(self):
        """
        Loads configuration file and
        returns True for success and
        False if there is no config file.
        """

        if (config_file := Path("./assets/config.json").resolve()).is_file():
            config = json.loads(config_file.read_text())

            self.original_lang_dropdown.setCurrentText(config["original_lang"])
            self.desired_lang_dropdown.setCurrentText(config["desired_lang"])
            self.loadorder_path_entry.setText(config["loadorder_path"])
            self.data_folder_entry.setText(config["data_path"])
            self.thread_num_dropdown.setCurrentText(str(config["thread_number"]))
            self.ignore_base_game_checkbox.setChecked(config["ignore_base_game"])
            self.include_mcms_checkbox.setChecked(config["include_mcms"])
            self.include_scripts_checkbox.setChecked(config["include_scripts"])
            self.include_bsas_checkbox.setChecked(config["include_bsas"])

            return True
        return False

    def get_paths(self):
        # Insert loadorder.txt path
        self.loadorder_path_entry.setText(
            str(
                Path(os.getenv("LOCALAPPDATA"))
                / "Skyrim Special Edition"
                / "loadorder.txt"
            )
        )

        try:
            # Insert data folder path
            reg_path = (
                "SOFTWARE\\WOW6432Node\\Bethesda Softworks\\Skyrim Special Edition"
            )
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as hkey:
                installdir = Path(winreg.QueryValueEx(hkey, "installed path")[0])

                if installdir.is_dir() and str(installdir) != ".":
                    self.data_folder_entry.setText(str(installdir / "Data"))
        except FileNotFoundError:
            self.log.error(
                "Failed to get installation path from registry: Registry key not found!"
            )

            qtw.QMessageBox.critical(
                self.root,
                "Skyrim Installation not found!",
                "Failed to get installation path from registry: Registry key not found!",
            )

    def extract_mcms_from_bsas(self, bsa_archives: list[Path]):
        """
        Extracts MCM translation files from BSAs to tempfolder
        and returns their paths.
        """

        mcm_files: list[Path] = []
        desired_lang = self.desired_lang_dropdown.currentText().lower()
        tempfolder = Path("temp").resolve()
        os.makedirs(tempfolder, exist_ok=True)

        for bsa_archive in bsa_archives:
            try:
                archive = ArchiveParser(bsa_archive).parse_archive()

                for mcm_file in archive.glob(f"*_{desired_lang}.txt"):
                    archive.extract_file(mcm_file, tempfolder)
                    mcm_files.append(tempfolder / mcm_file.name)
            except:
                self.log.error(f"Failed to parse BSA {bsa_archive.name!r}!")
                continue

        return mcm_files

    def extract_scripts_from_bsas(self, bsa_archives: list[Path]):
        """
        Extracts PEX files from BSAs to tempfolder
        and returns their paths.
        """

        script_files: list[Path] = []
        tempfolder = Path("temp").resolve()
        os.makedirs(tempfolder, exist_ok=True)

        for bsa_archive in bsa_archives:
            try:
                archive = ArchiveParser(bsa_archive).parse_archive()

                for script_file in archive.glob(f"*.pex"):
                    archive.extract_file(script_file, tempfolder)
                    script_files.append(tempfolder / script_file.name)
            except:
                self.log.error(f"Failed to parse BSA {bsa_archive.name!r}!")
                continue

        return script_files

    def load_files(self):
        """
        Loads and displays plugins.
        """

        loadorder_txt = Path(self.loadorder_path_entry.text())
        data_folder = Path(self.data_folder_entry.text())

        self.log.info("Loading files...")
        self.log.debug(f"Loadorder path: {loadorder_txt}")
        self.log.debug(f"Data folder: {data_folder}")

        self.all_files.clear()

        def process(ldialog: LoadingDialog):
            # Load plugins
            global loadorder

            self.log.info("Loading plugins...")
            ldialog.updateProgress(text1="Loading plugins...")

            self.plugin_loader = PluginLoader(
                app=self,
                loadorder_txt=loadorder_txt,
                data_folder=data_folder,
            )
            loadorder = self.plugin_loader.process_loadorder()

            for plugin_path in loadorder:
                file = PluginEntry(app=self, file=plugin_path)
                self.all_files.append(file)

            self.log.info(f"Loaded {len(loadorder)} plugin(s).")

            # Load MCM files
            ldialog.updateProgress(text1="Loading MCM files...")

            mcm_folder = data_folder / "interface" / "translations"
            mcm_files = mcm_folder.glob(
                f"*_{self.desired_lang_dropdown.currentText().lower()}.txt"
            )
            mcm_files = list(mcm_files)
            for file_path in mcm_files:
                file = MCMEntry(app=self, file=file_path)
                self.all_files.append(file)

            self.log.info(f"Loaded {len(mcm_files)} MCM file(s).")

            self.log.info("Extracting MCM files from BSAs...")
            ldialog.updateProgress(text1="Extracting MCM files from BSAs...")

            bsa_paths = [
                bsa_path
                for plugin in loadorder
                if (bsa_path := plugin.with_suffix(".bsa")).is_file()
            ]
            extracted_mcms = self.extract_mcms_from_bsas(bsa_paths)

            for file_path in extracted_mcms:
                file = MCMEntry(app=self, file=file_path)
                self.all_files.append(file)
                file.bsa = True

            self.log.info(f"Extracted {len(extracted_mcms)} MCM file(s) from BSAs.")

            # Load scripts
            self.log.info("Loading script files...")
            ldialog.updateProgress(text1="Loading scripts...")

            script_folder = data_folder / "scripts"
            script_files = script_folder.glob("*.pex")
            script_files = list(script_files)

            for file_path in script_files:
                file = ScriptEntry(app=self, file=file_path)
                self.all_files.append(file)

            self.log.info(f"Loaded {len(script_files)} script file(s).")

            self.log.info("Extracting scripts from BSAs...")
            ldialog.updateProgress(text1="Extracting scripts from BSAs...")

            bsa_paths = [
                bsa_path
                for plugin in loadorder
                if (bsa_path := plugin.with_suffix(".bsa")).is_file()
            ]
            extracted_scripts = self.extract_scripts_from_bsas(bsa_paths)

            for file_path in extracted_scripts:
                file = ScriptEntry(app=self, file=file_path)
                self.all_files.append(file)
                file.bsa = True

            self.log.info(
                f"Extracted {len(extracted_scripts)} script file(s) from BSAs."
            )

        loadingdialog = LoadingDialog(parent=self.root, app=self, func=process)
        loadingdialog.exec()

        _processing = True

        def process(ldialog: LoadingDialog):
            ldialog.updateProgress(text1="Processing files...", value1=0, max1=0)
            while _processing:
                time.sleep(0.1)

        loadingdialog = LoadingDialog(parent=self.root, app=self, func=process)
        loadingdialog.exec(False)

        start_time = time.time()
        rows: list[list[qtw.QWidget | str]] = []
        for i, file in enumerate(self.all_files):
            file.init_widget()
            if file.file_path in loadorder:
                displayed_index = f"{i+1}"
            else:
                displayed_index = ""
            row = [
                displayed_index,
                file.display_name,
                file.num_label,
                file.progress_widget,
            ]
            rows.append(row)
            self.processEvents(qtc.QEventLoop.ProcessEventsFlag.AllEvents)

        print(f"Time: {(time.time() - start_time):.3f} second(s).")
        self.file_list_table.setRows(rows)

        print(f"Time: {(time.time() - start_time):.3f} second(s).")
        self.log.debug(f"{len(self.all_files)} file(s) processed.")
        _processing = False

        self.run_button.setEnabled(bool(self.all_files))
        self.update_file_list()

    def exec(self):
        self.root.showMaximized()
        if not self.load_config():
            self.get_paths()
        self.load_files()
        self.loadorder_path_entry.textChanged.connect(self.load_files)
        self.data_folder_entry.textChanged.connect(self.load_files)
        self.ignore_base_game_checkbox.stateChanged.connect(
            lambda _: self.update_file_list()
        )
        self.include_mcms_checkbox.stateChanged.connect(
            lambda _: self.update_file_list()
        )
        self.include_scripts_checkbox.stateChanged.connect(
            lambda _: self.update_file_list()
        )
        self.include_bsas_checkbox.stateChanged.connect(
            lambda _: self.update_file_list()
        )

        self.log.info("Application started.")

        super().exec()

        self.log.info("Exiting application...")

        if self.threads:
            for thread in self.threads:
                if thread.isRunning():
                    thread.terminate()

            utils.kill_child_process(os.getpid(), kill_parent=False)

        self.save_config()

        if self.dict.edids or self.dict.strings:
            self.dict.save_dictionary()

        if (tempfolder := Path("temp").resolve()).is_dir():
            shutil.rmtree(tempfolder)

    def run(self):
        """
        Runs scan according to user configuration.
        """

        self.original_lang = Language[self.original_lang_dropdown.currentText().upper()]
        self.desired_lang = Language[self.desired_lang_dropdown.currentText().upper()]
        self.num_threads = int(self.thread_num_dropdown.currentText())
        self.ignore_base_game = self.ignore_base_game_checkbox.isChecked()
        self.include_mcms = self.include_mcms_checkbox.isChecked()
        self.include_scripts = self.include_scripts_checkbox.isChecked()
        self.include_bsas = self.include_bsas_checkbox.isChecked()

        self.log.debug(f"Original language: {self.original_lang}")
        self.log.debug(f"Desired language: {self.desired_lang}")
        self.log.debug(f"Number of threads: {self.num_threads}")
        self.log.debug(f"Ignore base game: {self.ignore_base_game}")
        self.log.debug(f"Include MCM translations: {self.include_mcms}")
        self.log.debug(f"Include Scripts: {self.include_scripts}")
        self.log.info("Running scan...")

        self.hide_translated_button.setDisabled(False)
        self.run_button.setDisabled(True)
        self.original_lang_dropdown.setDisabled(True)
        self.desired_lang_dropdown.setDisabled(True)
        self.thread_num_dropdown.setDisabled(True)
        self.ignore_base_game_checkbox.setDisabled(True)
        self.include_mcms_checkbox.setDisabled(True)
        self.include_scripts_checkbox.setDisabled(True)
        self.include_bsas_checkbox.setDisabled(True)
        self.loadorder_path_entry.setDisabled(True)
        self.browse_loadorder_button.setDisabled(True)
        self.data_folder_entry.setDisabled(True)
        self.browse_data_folder_button.setDisabled(True)
        self.untranslated_num_label.setText("Untranslated Files: 0")
        self.untranslated_num = 0

        if (output_dir := Path("Output").resolve()).is_dir():
            shutil.rmtree(output_dir)

        self.queue = Queue()
        for file in self.relevant_files:
            self.queue.put(file)

        self.progress_bar.setObjectName("")
        self.progress_bar.setStyleSheet(self.styleSheet())
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, len(self.relevant_files))

        self.start_time = time.strftime("%H:%M:%S")

        self.threads.clear()
        for _ in range(self.num_threads):
            thread = utils.Thread(target=self.file_thread, parent=self)
            thread.start()
            self.threads.append(thread)

    def on_finish(self):
        end_time = utils.get_diff(self.start_time, time.strftime("%H:%M:%S"))
        self.log.info(f"Scan complete in {end_time}!")

        self.threads.clear()

        self.progress_bar.setObjectName("finished_statistic")
        self.progress_bar.setStyleSheet(self.styleSheet())
        self.progress_bar.setValue(self.untranslated_num)

        self.run_button.setEnabled(True)
        self.original_lang_dropdown.setDisabled(False)
        self.desired_lang_dropdown.setDisabled(False)
        self.thread_num_dropdown.setDisabled(False)
        self.ignore_base_game_checkbox.setDisabled(False)
        self.include_mcms_checkbox.setDisabled(False)
        self.include_scripts_checkbox.setDisabled(False)
        self.include_bsas_checkbox.setDisabled(False)
        self.loadorder_path_entry.setDisabled(False)
        self.browse_loadorder_button.setDisabled(False)
        self.data_folder_entry.setDisabled(False)
        self.browse_data_folder_button.setDisabled(False)

        alert()
        message_box = qtw.QMessageBox()
        message_box.setWindowIcon(self.root.windowIcon())
        message_box.setIconPixmap(qtg.QIcon("./assets/icons/sse-at.png").pixmap(48, 48))
        message_box.setWindowTitle(f"{self.name} v{self.version}")
        message_box.setText(
            f"Scan complete in {end_time}!\n"
            "If you want to translate your modlist automatically,\n"
            "check out SSE Auto Translator on Nexus Mods!"
        )
        message_box.setStandardButtons(
            qtw.QMessageBox.StandardButton.Ok
            | qtw.QMessageBox.StandardButton.Open
        )
        btn = message_box.button(qtw.QMessageBox.StandardButton.Open)
        btn.setText("Open SSE-AT modpage on Nexus Mods")
        btn.clicked.disconnect()
        btn.clicked.connect(
            lambda: os.startfile(
                "https://www.nexusmods.com/skyrimspecialedition/mods/111491"
            )
        )

        utils.apply_dark_titlebar(message_box)
        message_box.exec()

    def file_thread(self):
        """
        Thread function that processes plugins.
        """

        lang_detector = LangDetector(self)
        lang_detector.set_langs([self.original_lang, self.desired_lang])

        while True:
            try:
                file_entry: FileEntry = self.queue.get(False)
            except Empty:
                break

            try:
                file_entry.progress_sign.emit((0, 0, 0))

                file_entry.status_sign.emit("Extracting strings...")
                file_entry.extract_strings()

                file_entry.status_sign.emit("Scanning for untranslated strings...")
                file_entry.untranslated_strings = (
                    lang_detector.clean_target_lang_strings(
                        file_entry.strings,
                        self.desired_lang,
                        file_entry.progress_sign,
                        file_entry.status_sign,
                    )
                )
                file_entry.set_num_sign.emit(
                    f"{len(file_entry.untranslated_strings)}/{len(file_entry.strings)}"
                )
                if file_entry.untranslated_strings:
                    self.incr_untranslated_sign.emit()
                    file_entry.enable_preview_btn_sign.emit()
                    os.makedirs(Path("Output").resolve(), exist_ok=True)
                    with open(
                        Path("Output").resolve() / f"{file_entry.file_path.name}.json",
                        mode="w",
                        encoding="utf-8",
                    ) as file:
                        json.dump(
                            file_entry.untranslated_strings,
                            file,
                            indent=4,
                            ensure_ascii=False,
                        )

                self.log.info(
                    f"Finished '{file_entry.file_path.name}'. ({self.progress_bar.value()}/{self.progress_bar.maximum()})"
                )

                file_entry.status_sign.emit("Done")
                self.incr_progress_sign.emit()
                self.queue.task_done()
            except Exception as ex:
                self.log.error(
                    f"Failed to process file '{file_entry.file_path.name}': {ex}"
                )
                file_entry.status_sign.emit(f"Error: {ex}")
                file_entry.progress_error_sign.emit()
                self.incr_progress_sign.emit()
                self.queue.task_done()

    def __repr__(self):
        return "MainApp"

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        self.log.critical(
            "An uncaught exception occured:",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

        error_msg = f"An uncaught exception occured:\n{exc_value}"
        detailed_msg = "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
        yesno = True

        messagebox = ErrorDialog(
            parent=self.root,
            title=f"{self.root.windowTitle()} - Error",
            text=error_msg,
            details=detailed_msg,
            yesno=yesno,
        )

        alert()
        choice = messagebox.exec()

        if choice == qtw.QMessageBox.StandardButton.No:
            self.exit()


if __name__ == "__main__":
    from updater import Updater

    app = MainApp()
    app.exec()

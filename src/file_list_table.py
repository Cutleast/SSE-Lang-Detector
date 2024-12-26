"""
This file is part of SEE Lang Detector
and falls under the license
GNU General Public License v3.0.
"""

import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw


class FileListTableModel(qtc.QAbstractTableModel):
    """
    Data model for FileListTable.
    """

    _data: dict[qtc.QModelIndex, str] = {}

    def __init__(self, headers: list[str] = [], rows: int = 0):
        super().__init__()
        self.row_count = rows
        self.headers = headers

    def clear(self):
        if self.row_count > 0:
            old_row_count = self.row_count
            super().beginRemoveRows(self.index(0, 0), 0, self.row_count - 1)
            self.row_count = 0
            super().endRemoveRows()

            self.rowsRemoved.emit(self.index(0, 0), 0, old_row_count - 1)

    def rowCount(self, parent=None):
        return self.row_count

    def setRowCount(self, rows: int):
        self.clear()

        super().beginInsertRows(self.index(0, 0), 0, rows - 1)
        self.row_count = rows
        super().endInsertRows()

        self.rowsInserted.emit(self.index(0, 0), 0, rows - 1)

    def columnCount(self, parent=None):
        return len(self.headers)

    def setData(self, index: qtc.QModelIndex, value: str, role):
        if role == qtc.Qt.ItemDataRole.DisplayRole:
            self._data[index] = value

    def data(self, index, role):
        if role == qtc.Qt.ItemDataRole.DisplayRole:
            return self._data.get(index, "")
        return None

    def setHeaders(self, headers: list[str]):
        old_col_count = len(self.headers)
        self.headers = headers
        self.headerDataChanged.emit(qtc.Qt.Orientation.Horizontal, 0, old_col_count)

    def headerData(
        self, section: int, orientation: qtc.Qt.Orientation, role: int = ...
    ):
        if (
            orientation == qtc.Qt.Orientation.Horizontal
            and role == qtc.Qt.ItemDataRole.DisplayRole
        ):
            return self.headers[section]


class FileListTable(qtw.QTableView):
    """
    Custom QTableView adapted to display
    QWidgets instead of strings.
    """

    rows: list[list[qtw.QWidget | str]] = []

    def __init__(self):
        super().__init__()

        self._model = FileListTableModel()
        self.setSelectionMode(self.SelectionMode.NoSelection)
        self.setModel(self._model)
        self.verticalHeader().hide()

    def setHeaders(self, headers: list[str]):
        self._model.setHeaders(headers)

    def appendRow(self, row: list[qtw.QWidget | str]):
        self.rows.append(row)
        self._model.setRowCount(len(self.rows))

        for c, item in enumerate(row):
            self.setIndexWidget(self._model.index(len(self.rows) - 1, c), item)

    def appendRows(self, rows: list[list[qtw.QWidget | str]]):
        self.rows.extend(rows)
        self._model.setRowCount(len(self.rows))

        for r, row in enumerate(rows):
            for c, item in enumerate(row):
                self.setIndexWidget(self._model.index(self.rows.index(row), c), item)

    def setRows(self, rows: list[list[qtw.QWidget | str]]):
        self.rows = rows
        self._model.setRowCount(len(self.rows))

        self._displayRows()

    def removeRow(self, row_index: int):
        self.rows.pop(row_index)
        self._displayRows()

    def clear(self):
        self.rows.clear()
        self._displayRows()

    def _displayRows(self):
        self._model.setRowCount(len(self.rows))

        for rindex, row in enumerate(self.rows):
            for cindex, item in enumerate(row):
                model_index = self._model.index(rindex, cindex)
                if isinstance(item, qtw.QWidget):
                    self.setIndexWidget(model_index, item)
                else:
                    self._model.setData(
                        model_index, item, qtc.Qt.ItemDataRole.DisplayRole
                    )

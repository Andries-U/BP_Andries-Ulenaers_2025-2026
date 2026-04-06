from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
    QPushButton, QLabel, QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import Qt

class ColumnMultiselectDialog(QDialog):
    def __init__(self, title="Select Options", instruction="Select one or more values from the list below:", column_name="Column", options=None,no_selection_allowed=False, select_all_text="Select All", deselect_all_text="Deselect All", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(300)
        
        self.column_name = column_name
        self.options = options or []
        self.selected_items = []
        self.no_selection_allowed = no_selection_allowed
        
        self._setup_ui(instruction=instruction, select_all_text=select_all_text, deselect_all_text=deselect_all_text, no_selection_allowed=no_selection_allowed)
        
    def _setup_ui(self, instruction=None, select_all_text="Select All", deselect_all_text="Deselect All", no_selection_allowed=False):
        layout = QVBoxLayout(self)
        
        # 1. Instructions
        label = QLabel(instruction)
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # 2. List Widget (Multiselect)
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection) # Allows Ctrl+Click / Shift+Click
        for item in self.options:
            self.list_widget.addItem(str(item))
        layout.addWidget(self.list_widget)
        
        # 3. Buttons Row
        btn_layout = QHBoxLayout()
        
        # Select All
        self.btn_select_all = QPushButton(select_all_text)
        self.btn_select_all.clicked.connect(self._select_all)
        btn_layout.addWidget(self.btn_select_all)
        
        # Select None
        self.btn_select_none = QPushButton(deselect_all_text)
        self.btn_select_none.clicked.connect(self._select_none)
        btn_layout.addWidget(self.btn_select_none)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 4. Standard OK/Cancel Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self._accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
    def _select_all(self):
        for row in range(self.list_widget.count()):
            self.list_widget.item(row).setCheckState(Qt.Checked)
            
    def _select_none(self):
        for row in range(self.list_widget.count()):
            self.list_widget.item(row).setCheckState(Qt.Unchecked)
            
    def _accept(self):
        # Collect checked items
        self.selected_items = []
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if item.checkState() == Qt.Checked:
                self.selected_items.append(self.options[row])
        
        if not self.selected_items and not self.no_selection_allowed:    
            QMessageBox.warning(self, "No Selection", "Please select at least one item.")
            return
    
        self.accept()

    def get_selected(self):
        return self.selected_items
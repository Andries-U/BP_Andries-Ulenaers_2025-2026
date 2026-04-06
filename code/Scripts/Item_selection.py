from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QComboBox, QPushButton,
    QLabel, QMessageBox
)

class ItemSelectionDialog(QDialog):
    """
    A generic dialog for selecting an item from a list.

    Args:
        items (list): List of items to display (e.g., layer names or objects).
        title (str): Dialog window title.
        prompt (str): Label text prompting the user.
        parent (QWidget): Parent widget (optional).
    """
    def __init__(self, items, title="Select an Item", prompt="Choose an item:", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setLayout(QVBoxLayout())

        # Store items and their data
        self.items = items

        # Label
        self.label = QLabel(prompt)
        self.layout().addWidget(self.label)

        # Dropdown (QComboBox)
        self.item_combo = QComboBox()
        self.layout().addWidget(self.item_combo)

        # OK and Cancel buttons
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.on_ok_clicked)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        self.layout().addLayout(button_layout)

        # Populate the dropdown
        self.populate_combo()

    def populate_combo(self):
        """Populate the dropdown with items."""
        for item in self.items:
            # If items are QgsMapLayer objects, use their names
            if hasattr(item, 'name'):
                self.item_combo.addItem(item.name(), item)
            else:
                # Otherwise, use the item directly (e.g., strings)
                self.item_combo.addItem(str(item), item)

    def on_ok_clicked(self):
        """Handle the OK button click."""
        selected_item = self.item_combo.currentData()
        if selected_item is not None:
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "No item selected.")

    def get_selected_item(self):
        """Return the selected item."""
        return self.item_combo.currentData()
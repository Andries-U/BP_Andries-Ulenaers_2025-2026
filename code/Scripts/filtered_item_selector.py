from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QComboBox, QLabel
from PyQt5.QtCore import Qt

class FilteredItemSelector(QWidget):
    def __init__(
        self,
        items: list,
        label_text="Select an item:",
        placeholder_text="Type to filter...",
        parent=None,
    ):
        """
        A reusable widget for selecting an item from a list with filtering.

        Args:
            items (list): List of items (e.g., layer names or objects).
            label_text (str): Label text for the selector.
            placeholder_text (str): Placeholder text for the filter field.
            parent (QWidget): Parent widget.
        """
        super().__init__(parent)

        # Store items
        self.items = items
        self.original_items = list(items)  # Store original for filtering

        # Layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Label
        self.label = QLabel(label_text)
        layout.addWidget(self.label)

        # Filter text field
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText(placeholder_text)
        self.filter_edit.textChanged.connect(self._filter_items)
        layout.addWidget(self.filter_edit)

        # Combo box for item selection
        self.combo_box = QComboBox()
        self.combo_box.setMaxVisibleItems(12)
        layout.addWidget(self.combo_box)

        # Populate combo box
        self._populate_combo()

    def _populate_combo(self):
        """Populate the combo box with items."""
        self.combo_box.clear()
        for item in self.items:
            # If items are QgsMapLayer objects, use their names
            if hasattr(item, "name"):
                self.combo_box.addItem(item.name(), item)
            else:
                # Otherwise, use the item directly (e.g., strings)
                self.combo_box.addItem(str(item), item)

    def _filter_items(self, search_text):
        """Filter combo box items based on search text."""
        self.combo_box.clear()
        search_text_lower = search_text.lower()

        for item in self.original_items:
            # If items are QgsMapLayer objects, use their names
            if hasattr(item, "name"):
                item_name = item.name()
            else:
                item_name = str(item)

            # Check if search text is in the item name
            if search_text_lower in item_name.lower():
                if hasattr(item, "name"):
                    self.combo_box.addItem(item_name, item)
                else:
                    self.combo_box.addItem(item_name, item)

    def get_selected_item(self):
        """Return the selected item."""
        return self.combo_box.currentData()

    def set_items(self, items):
        """Update the list of items."""
        self.items = items
        self.original_items = list(items)
        self._populate_combo()
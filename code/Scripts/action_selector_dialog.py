from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QScrollArea, QWidget, QMessageBox
)
from qgis.PyQt.QtCore import Qt
from typing import Dict, Callable, Any, List, Optional

# Define the type for our action map: String (Label) -> Callable (Function) or Dict (Config)
ActionMap = Dict[str, Any] 

class ActionSelectorDialog(QDialog):
    def __init__(self, action_map: ActionMap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Analysis Type")
        self.setModal(True)
        
        self.action_map = action_map
        self.selected_action: Optional[Any] = None # Will hold the function or config
        self.selected_label: Optional[str] = None   # Will hold the button text
        
        layout = QVBoxLayout()
        
        label = QLabel("Select the analysis type to perform on the current layer:")
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # Scroll area for long lists
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Dynamically create buttons
        for label_text, action_data in self.action_map.items():
            btn = QPushButton(label_text)
            
            # Capture the specific action_data using lambda
            btn.clicked.connect(lambda checked, lbl=label_text, data=action_data: self.on_button_click(lbl, data))
            scroll_layout.addWidget(btn)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        self.setLayout(layout)

    def on_button_click(self, label: str, action_data: Any) -> None:
        self.selected_label = label
        self.selected_action = action_data
        self.accept()
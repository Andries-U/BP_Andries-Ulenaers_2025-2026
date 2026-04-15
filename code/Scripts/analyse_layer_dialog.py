from PyQt5.QtWidgets import (
    QDialog, QFileDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QCheckBox, QGroupBox, QLineEdit, QMessageBox,
    QDoubleSpinBox, QWidget, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt
from qgis.core import QgsProject, QgsWkbTypes
from filtered_item_selector import FilteredItemSelector

class AnalyzeLayerSettingsDialog(QDialog):
    def __init__(self, analyze_layers: list, search_area_layers: list = None, search_radius: int = 5000, max_distinct_values: int = 20, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analysis Settings")
        self.setMinimumWidth(400)

        # Main layout
        layout = QVBoxLayout()

        self.max_distinct_values = max_distinct_values

        # Analyze Layer Selector
        self.analyze_layer_selector = FilteredItemSelector(
            items=analyze_layers,
            label_text="Select Analyze Layer:",
            placeholder_text="Filter analyze layers...",
        )
        layout.addWidget(self.analyze_layer_selector)

        # Search Area Layer Selector
        self.search_area_layer_selector = FilteredItemSelector(
            items=search_area_layers,
            label_text="Select Search Area Layer:",
            placeholder_text="Filter search area layers...",
        )
        layout.addWidget(self.search_area_layer_selector)

        # Confirm layers button
        self.confirm_layers_btn = QPushButton("Confirm Layer Selection")
        self.confirm_layers_btn.clicked.connect(self.on_confirm_layer_selection)
        layout.addWidget(self.confirm_layers_btn)

        # --- 2. Radius Selector (initially hidden) ---
        self.radius_label = QLabel("Search Radius (meters):")
        self.radius_spinbox = QDoubleSpinBox()
        self.radius_spinbox.setRange(1, 1000000)  # 1m to 1000km
        self.radius_spinbox.setValue(search_radius) 
        self.radius_spinbox.setDecimals(0)  # No decimals for meters

        # Layout for radius selector
        self.radius_layout = QHBoxLayout()
        self.radius_layout.addWidget(self.radius_label)
        self.radius_layout.addWidget(self.radius_spinbox)
        self.radius_widget = QWidget()
        self.radius_widget.setLayout(self.radius_layout)
        self.radius_widget.hide()  # Initially hidden
        layout.addWidget(self.radius_widget)

        # --- 1. Analysis Type Toggle ---
        self.analysis_type_group = QButtonGroup()
        self.partial_analysis_radio = QRadioButton("Partial Analysis")
        self.full_analysis_radio = QRadioButton("Full Analysis")
        self.analysis_type_group.addButton(self.partial_analysis_radio)
        self.analysis_type_group.addButton(self.full_analysis_radio)
        self.full_analysis_radio.setChecked(True)  # Default: Full Analysis

        analysis_type_layout = QHBoxLayout()
        analysis_type_layout.addWidget(self.partial_analysis_radio)
        analysis_type_layout.addWidget(self.full_analysis_radio)
        layout.addLayout(analysis_type_layout)

        # Connect radio buttons to toggle visibility
        self.partial_analysis_radio.toggled.connect(self.toggle_analysis_type)
        self.full_analysis_radio.toggled.connect(self.toggle_analysis_type)


        # --- 4. Column Selection (initially disabled) ---
        self.column_label = QLabel("Select Column:")
        self.column_combo = QComboBox()
        self.column_combo.setEnabled(False)  # Initially disabled
        column_layout = QHBoxLayout()
        column_layout.addWidget(self.column_label)
        column_layout.addWidget(self.column_combo)
        layout.addLayout(column_layout)

        # --- 5. Distinct Values Checkboxes (initially hidden) ---
        self.values_group = QGroupBox("Filter by Distinct Values")
        self.values_layout = QVBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.deselect_all_btn = QPushButton("Deselect All")
        values_button_layout = QHBoxLayout()
        values_button_layout.addWidget(self.select_all_btn)
        values_button_layout.addWidget(self.deselect_all_btn)
        self.values_layout.addLayout(values_button_layout)
        self.values_group.setLayout(self.values_layout)
        self.values_group.hide()  # Initially hidden
        layout.addWidget(self.values_group)

         # --- 7. Export Type Dropdown ---
        self.export_type_label = QLabel("Export Type:")
        self.export_type_combo = QComboBox()
        self.export_type_combo.addItems(["CSV", "PDF", "Both (CSV + PDF)"])
        export_type_layout = QHBoxLayout()
        export_type_layout.addWidget(self.export_type_label)
        export_type_layout.addWidget(self.export_type_combo)
        layout.addLayout(export_type_layout)

         # --- 8. Output Folder Selector ---
        self.output_folder_label = QLabel("Output Folder:")
        self.output_folder_lineedit = QLineEdit()
        self.output_folder_button = QPushButton("Browse...")
        self.output_folder_button.clicked.connect(self.select_output_folder)
        output_folder_layout = QHBoxLayout()
        output_folder_layout.addWidget(self.output_folder_label)
        output_folder_layout.addWidget(self.output_folder_lineedit)
        output_folder_layout.addWidget(self.output_folder_button)
        layout.addLayout(output_folder_layout)

        # --- 3. Run Button ---
        self.run_button = QPushButton("Run Analysis")
        self.run_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.run_button.clicked.connect(self.run_analysis)
        layout.addWidget(self.run_button)

        self.setLayout(layout)

    def select_output_folder(self):
        """Open a folder dialog to select the output folder."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            ""  # Default directory (empty = user's home directory)
        )
        if folder_path:
            self.output_folder_lineedit.setText(folder_path)

    def on_confirm_layer_selection(self):
        """Validate layer selections and populate column dropdowns."""
        analyze_layer = self.analyze_layer_selector.get_selected_item()
        search_area_layer = self.search_area_layer_selector.get_selected_item()

        if not analyze_layer or not search_area_layer:
            QMessageBox.warning(self, "Error", "Please select both layers!")
            return

        # Update radius visibility
        self.update_radius_visibility()

        if self.partial_analysis_radio.isChecked():
            # Populate column dropdown for analyze layer
            self.update_column_combo()

            # Enable column dropdown and distinct values section
            self.column_combo.setEnabled(True)
            self.values_group.show()

        # Enable run button
        self.run_button.setEnabled(True)


    def update_column_combo(self):
        """Update column dropdown based on the selected analyze layer."""
        self.column_combo.clear()
        selected_layer = self.analyze_layer_selector.get_selected_item()
        if not selected_layer:
            return
        fields = [field.name() for field in selected_layer.fields()]
        self.column_combo.addItems(fields)

        # Connect column combo to distinct values update
        self.column_combo.currentIndexChanged.connect(self.update_distinct_values)


    def update_distinct_values(self):
        """Update distinct values checkboxes for the selected column."""
        # Clear existing checkboxes
        for i in reversed(range(self.values_layout.count())):
            widget = self.values_layout.itemAt(i).widget()
            if widget and widget != self.select_all_btn and widget != self.deselect_all_btn:
                widget.deleteLater()

        # Get distinct values
        selected_layer = self.analyze_layer_selector.get_selected_item()
        column_name = self.column_combo.currentText()
        if not selected_layer or not column_name:
            return

        print(f"Getting distinct values for column '{column_name}' in layer '{selected_layer.name()}'...")

        column_index = selected_layer.fields().indexFromName(column_name)
        unique_values = selected_layer.uniqueValues(column_index) if column_index != -1 else []
        
        print("started populating checkboxes...")
        # Show/hide the distinct values section based on the number of unique values
        if len(unique_values) < self.max_distinct_values:
            self.values_group.show()
            # Add checkboxes for each value
            self.checkboxes = []
            for value in unique_values:
                checkbox = QCheckBox(str(value))
                checkbox.setChecked(True)
                self.values_layout.addWidget(checkbox)
                self.checkboxes.append(checkbox)
        else:
            self.values_group.show()  # Show the group to display the message
            # Add a message label for too many values
            message_label = QLabel(f"Too many unique values to display ({len(unique_values)}).")
            self.values_layout.addWidget(message_label)
            # Hide the select all/deselect all buttons if there are too many values
            self.select_all_btn.hide()
            self.deselect_all_btn.hide()

        # Connect Select All/Deselect All buttons (only if checkboxes exist)
        if len(unique_values) < 20:
            self.select_all_btn.show()
            self.deselect_all_btn.show()
            self.select_all_btn.clicked.connect(self.select_all)
            self.deselect_all_btn.clicked.connect(self.deselect_all)
        else:
            self.select_all_btn.hide()
            self.deselect_all_btn.hide()

            # Connect Select All/Deselect All buttons
            self.select_all_btn.clicked.connect(self.select_all)
            self.deselect_all_btn.clicked.connect(self.deselect_all)

    def select_all(self):
        """Select all checkboxes."""
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def deselect_all(self):
        """Deselect all checkboxes."""
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)

    def update_radius_visibility(self):
        """Show/hide radius selector based on search area layer type."""
        selected_layer = self.search_area_layer_selector.get_selected_item()
        if selected_layer:
            # Show radius selector only if the layer is a point layer
            is_point_layer = selected_layer.geometryType() == QgsWkbTypes.PointGeometry
            self.radius_widget.setVisible(is_point_layer)
        else:
            self.radius_widget.setVisible(False)

    def get_settings(self):
        """Return the selected settings as a dictionary."""
        return {
            "analyze_layer": self.analyze_layer_selector.get_selected_item(),
            "search_area_layer": self.search_area_layer_selector.get_selected_item(),
            "search_radius": self.radius_spinbox.value() if self.radius_widget.isVisible() else None,
            "column_name": self.column_combo.currentText() if self.column_combo.isEnabled() else None,
            "distinct_values": [cb.text() for cb in self.checkboxes if cb.isChecked()] if hasattr(self, 'checkboxes') else None,
            "export_type": self.export_type_combo.currentText(),
            "output_folder": self.output_folder_lineedit.text(),
            "analysis_type": "Partial" if self.partial_analysis_radio.isChecked() else "Full"

        }
    
    def toggle_analysis_type(self, checked):
        """Toggle visibility of column and distinct values sections based on analysis type."""
        if self.full_analysis_radio.isChecked():
            # Hide column and distinct values sections for full analysis
            self.column_label.hide()
            self.column_combo.hide()
            self.values_group.hide()
        else:
            # Show column and distinct values sections for partial analysis
            self.column_label.show()
            self.column_combo.show()
            if self.column_combo.count() > 0:  # Only show if columns are populated
                self.values_group.show()

    def exec_(self):
        """Override exec_ to ensure settings are collected before closing."""
        result = super().exec_()
        if result == QDialog.Accepted:
            return self.get_settings()
        else:
            return None
    
    def run_analysis(self):
        """Collect inputs and run the analysis."""
        analyze_layer = self.analyze_layer_selector.get_selected_item()
        search_area_layer = self.search_area_layer_selector.get_selected_item()

        if not analyze_layer or not search_area_layer:
            QMessageBox.warning(self, "Error", "Please select both layers!")
            return

        print("Analyze Layer:", analyze_layer.name())
        print("Search Area Layer:", search_area_layer.name())

        QMessageBox.information(self, "Success", "Analysis settings saved! Ready to run.")
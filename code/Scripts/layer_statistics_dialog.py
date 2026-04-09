from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem, 
    QLabel, QScrollArea, QWidget, QGroupBox, QPushButton, QMessageBox, QHeaderView, QProgressDialog
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeatureRequest, 
    QgsField, QgsExpression, QgsGeometry
)
from typing import Dict, List, Any, Optional
from collections import Counter

class LayerStatisticsDialog(QDialog):
    def __init__(self, layer: QgsVectorLayer, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Statistics for: {layer.name()}")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setModal(True)
        self.layer = layer
        
        if not layer or not layer.isValid():
            QMessageBox.warning(self, "Error", "Selected layer is invalid or not a vector layer.")
            self.reject()
            return

        self.total_count = layer.featureCount()
        self.stats_data: Dict[str, Dict[str, int]] = {}
        self.area_data: Dict[str, Dict[str, float]] = {}
        self.field_total_areas: Dict[str, float] = {}
        
        LARGE_DATASET_THRESHOLD = 50000
        if self.total_count > LARGE_DATASET_THRESHOLD:
            reply = QMessageBox.question(
                self, 
                "Large Dataset Warning",
                f"This layer contains {self.total_count:,} features.\n\n"
                "Analyzing large datasets may take significant time and memory.\n"
                "Do you want to proceed with the analysis?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                self.reject()
                return
        
        self._collect_statistics()
        self._build_ui()

    def _collect_statistics(self):
        print(f"Scanning {self.total_count} features for field statistics...")
        
        progress = None
        if self.total_count > 1000:
            progress = QProgressDialog("Analyzing layer statistics...", "Cancel", 0, self.total_count, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(1000)
        
        features = list(self.layer.getFeatures())
        processed = 0
        
        for field in self.layer.fields():
            field_name = field.name()
            
            if field.typeName() in ['geometry', 'unknown']:
                continue

            counts = Counter()
            areas = Counter()
            field_total_area = 0.0
            
            for feature in features:
                val = feature[field_name]
                display_val = "NULL" if val is None else str(val)
                counts[display_val] += 1
                
                if feature.geometry() and not feature.geometry().isEmpty():
                    area = feature.geometry().area()
                    areas[display_val] += area
                    field_total_area += area
                
                processed += 1
                
                if progress and processed % 100 == 0:
                    progress.setValue(processed)
                    if progress.wasCanceled():
                        return
            
            self.stats_data[field_name] = dict(counts)
            self.area_data[field_name] = dict(areas)
            self.field_total_areas[field_name] = field_total_area
            print(f"  Processed field: {field_name} ({len(counts)} distinct values)")
        
        if progress:
            progress.setValue(self.total_count)

    def _is_unique_identifier_field(self, counts: Dict[str, int]) -> bool:
        return all(count <= 1 for count in counts.values())

    def _handle_sort_click(self, table: QTableWidget, col: int):
        """Handle column header click for sorting."""
        # Get current sort order for this column (default to Descending for first click)
        current_order = getattr(table, f'sort_order_col_{col}', Qt.DescendingOrder)
        
        # Toggle sort order for this column
        new_order = Qt.AscendingOrder if current_order == Qt.DescendingOrder else Qt.DescendingOrder
        
        # Store the new sort order for this column
        setattr(table, f'sort_order_col_{col}', new_order)
        
        # Use Qt's built-in sorting which will use UserRole data for numeric columns
        table.sortItems(col, new_order)

    def _sort_numeric_column(self, table: QTableWidget, col: int, order: Qt.SortOrder):
        """
        Sort a column by its Qt.UserRole data (numeric value).
        Handles text columns by attempting to parse numbers, or sorting alphabetically if not.
        """
        row_data = []
        
        for row in range(table.rowCount()):
            item = table.item(row, col)
            sort_value = None
            is_numeric = False
            
            if item:
                text = item.text()
                # Check if the value has a stored numeric UserRole
                user_val = item.data(Qt.UserRole)
                
                if user_val is not None:
                    sort_value = user_val
                    is_numeric = True
                else:
                    # Fallback: try to parse the text
                    try:
                        if text.endswith('%'):
                            sort_value = float(text[:-1])
                        else:
                            sort_value = float(text)
                        is_numeric = True
                    except ValueError:
                        # Not a number, sort alphabetically
                        sort_value = text
                        is_numeric = False
            
            # Collect all items in this row to move them together
            row_items = []
            for c in range(table.columnCount()):
                row_items.append(table.item(row, c))
            
            # Store tuple: (sort_value, is_numeric, row_items)
            # If not numeric, we sort by string representation
            if is_numeric and sort_value is not None:
                row_data.append((sort_value, row_items))
            else:
                # Convert to string for sorting if not numeric
                row_data.append((str(sort_value) if sort_value is not None else "", row_items))
        
        # Sort logic
        # If all values are numeric, sort numerically. 
        # If mixed, we rely on the string fallback in the tuple, but ideally we separate them.
        # For simplicity, we sort by the primary key (the float or string).
        
        # To ensure numeric columns sort correctly even if mixed types exist:
        # We sort by the 'sort_value' (which is float for numeric, str for text)
        # But we need to prioritize numbers over text if mixed? 
        # Let's assume for this UI, if a column has numbers, we want numeric sort.
        
        # Simple numeric sort (works best if column is purely numeric)
        # If mixed, we might need a custom key. 
        # Here we assume if UserRole exists, it's numeric.
        
        # Re-sorting with a custom key to handle potential mixed types safely:
        def sort_key(item_tuple):
            val, _ = item_tuple
            return (isinstance(val, float), val) # Floats first, then strings? Or just val?
            # Actually, if we have mixed types, sorting them together is tricky.
            # Let's just sort by the value directly. If it's a float, it sorts numerically.
            # If it's a string, it sorts alphabetically.
        
        # Better approach for mixed:
        # If the column was detected as numeric (has UserRole), we force numeric sort.
        # If not, we sort by string.
        
        # Let's just use the value directly. Python 3 can't mix float and str in sort.
        # So we must ensure consistency.
        
        # If the column has any numeric UserRole, we treat the whole column as numeric.
        # Otherwise, we treat as text.
        
        # Check if the column has numeric data
        has_numeric = any(isinstance(item[0], float) for item in row_data)
        
        if has_numeric:
            # Force numeric sort. Convert strings to 0 or handle them?
            # For this UI, we assume the user clicked a numeric column.
            # We'll just sort by the value. If there are non-numeric values (None), they go to end.
            row_data.sort(key=lambda x: (x[0] is None, x[0] if x[0] is not None else 0), reverse=(order == Qt.DescendingOrder))
    def _build_ui(self):
        layout = QVBoxLayout()
        
        header_text = f"Total Features: {self.total_count:,}\nFields Analyzed: {len(self.stats_data)}"
        header = QLabel(header_text)
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QGridLayout(scroll_content)
        
        num_fields = len(self.stats_data)
        num_columns = max(2, int(num_fields ** 0.5))
        
        row, col = 0, 0
        for field_name, counts in self.stats_data.items():
            is_unique_id = self._is_unique_identifier_field(counts)
            areas = self.area_data[field_name]
            field_total_area = self.field_total_areas[field_name]
            
            group = QGroupBox(field_name)
            if is_unique_id:
                group.setStyleSheet("QGroupBox { color: #888888; font-style: italic; }")
                group.setTitle(f"{field_name} (Unique Identifier)")
            
            group_layout = QVBoxLayout()
            
            table = QTableWidget()
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["Distinct Value", "Count", "Count %", "Total Area", "Area %"])
            
            # Set resize modes
            for c in range(5):
                table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
            
            # Connect header clicks
            # Fixed the lambda closure by using a default argument for the column index
            for c_idx in range(5):
                table.horizontalHeader().sectionClicked.connect(
                    lambda c=c_idx, t=table: self._handle_sort_click(t, c)
                )
            
            # Initial sort by Count (Column 1) descending
            # We can do this by calling _sort_numeric_column on col 1 initially
            # But for now, just populate. The user clicks to sort.
            
            sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            
            for value, count in sorted_items:
                row_t = table.rowCount()
                table.insertRow(row_t)
                
                # Value Cell
                val_item = QTableWidgetItem(value)
                val_item.setFlags(Qt.ItemIsEnabled)
                if is_unique_id:
                    val_item.setBackground(QColor(240, 240, 240))
                    val_item.setForeground(QColor(128, 128, 128))
                table.setItem(row_t, 0, val_item)
                
                # Count Cell (Column 1)
                count_item = QTableWidgetItem(str(count))
                count_item.setData(Qt.UserRole, count) 
                count_item.setFlags(Qt.ItemIsEnabled)
                count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if is_unique_id:
                    count_item.setBackground(QColor(240, 240, 240))
                    count_item.setForeground(QColor(128, 128, 128))
                table.setItem(row_t, 1, count_item)
                
                # Count Percentage Cell (Column 2)
                count_percentage = (count / self.total_count) * 100
                count_pct_item = QTableWidgetItem(f"{count_percentage:.2f}")
                count_pct_item.setData(Qt.UserRole, count_percentage)
                count_pct_item.setFlags(Qt.ItemIsEnabled)
                count_pct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if is_unique_id:
                    count_pct_item.setBackground(QColor(240, 240, 240))
                    count_pct_item.setForeground(QColor(128, 128, 128))
                table.setItem(row_t, 2, count_pct_item)
                
                # Total Area Cell (Column 3)
                total_area = areas.get(value, 0.0)
                area_item = QTableWidgetItem(f"{total_area:.2f}")
                area_item.setData(Qt.UserRole, total_area)
                area_item.setFlags(Qt.ItemIsEnabled)
                area_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if is_unique_id:
                    area_item.setBackground(QColor(240, 240, 240))
                    area_item.setForeground(QColor(128, 128, 128))
                table.setItem(row_t, 3, area_item)
                
                # Area Percentage Cell (Column 4)
                area_percentage = (total_area / field_total_area) * 100 if field_total_area > 0 else 0
                area_pct_item = QTableWidgetItem(f"{area_percentage:.2f}%")
                area_pct_item.setData(Qt.UserRole, area_percentage)
                area_pct_item.setFlags(Qt.ItemIsEnabled)
                area_pct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if is_unique_id:
                    area_pct_item.setBackground(QColor(240, 240, 240))
                    area_pct_item.setForeground(QColor(128, 128, 128))
                table.setItem(row_t, 4, area_pct_item)
            
            table.setMinimumHeight(150)
            table.setMinimumWidth(400)
            
            group_layout.addWidget(table)
            group.setLayout(group_layout)
            
            scroll_layout.addWidget(group, row, col)
            
            col += 1
            if col >= num_columns:
                col = 0
                row += 1
        
        scroll_layout.setSpacing(10)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        btn_cancel = QPushButton("Close")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        if self.parent():
            parent_widget = self.parent()
            parent_width = parent_widget.width()
            parent_height = parent_widget.height()
            
            dialog_width = int(parent_width * 0.85)
            dialog_height = int(parent_height * 0.80)
            
            self.setMinimumSize(600, 400)
            self.resize(dialog_width, dialog_height)
        else:
            self.setMinimumSize(1000, 400)
            self.resize(1200, 700)

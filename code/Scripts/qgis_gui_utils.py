from item_selection import ItemSelectionDialog
from PyQt5.QtWidgets import QDialog, QApplication, QInputDialog, QLineEdit, QMessageBox
from exceptions import SelectionCancelledError, NoItemSelectedError, LayerFeatureError
from typing import Optional, TypeVar
from qgis.core import (QgsVectorLayer, QgsFeature, QgsRectangle, QgsMapLayer, QgsProject, QgsMessageLog, Qgis)
from qgis.utils import iface
from multiselect_dialog import ColumnMultiselectDialog

T = TypeVar('T')

def select_item_from_gui_list(items: list[T], prompt: str = "Select a item", title: str = "Select an item from the list") -> tuple[T, int]:
    """
    Select an item from a list using a GUI dialog.
    Args:
        items (list[T]): The list of items to select from.
        prompt (str): The prompt to display in the selection dialog.
        title (str): The title of the selection dialog.
    Returns:
        tuple[T, int]: The selected item and its index in the original list.
    
    Raises:
        SelectionCancelledError: If the user clicks Cancel.
        NoItemSelectedError: If the dialog accepts but returns no item.

    """
    dialog = ItemSelectionDialog(
        items=items,
        title=title,
        prompt=prompt
    )

    if dialog.exec_() == QDialog.Accepted:
        selected_item= dialog.get_selected_item()
        
        if selected_item is None:
            raise NoItemSelectedError("Dialog accepted but returned no item.")
            
        try:
            index = items.index(selected_item)
            return selected_item, index
        except ValueError:
            raise NoItemSelectedError("Selected item not found in the original list.")
    elif dialog.exec_() == QDialog.Rejected:
        raise SelectionCancelledError("User cancelled the selection dialog.")
    
    # If exec_() returns something other than Accepted or Rejected (rare)
    raise SelectionCancelledError(f"Unknown dialog result.: {dialog.result()}")

def select_feature_from_layer_database(layer: QgsVectorLayer, prompt: str = "Select a feature", title: str = "Select a Feature") -> tuple[QgsFeature, int]:
    """
    Select a feature ID from a vector layer.
    
    Args:
        layer (QgsVectorLayer): The vector layer to select from.
        prompt (str): The prompt to display in the selection dialog.
        title (str): The title of the selection dialog.
    
    Returns:
        tuple[QgsFeature, int]: The selected feature and its ID.

    Raises:
        LayerFeatureError: If features cannot be retrieved.
        SelectionCancelledError: If the user cancels the GUI.
    """

    if not layer:
        raise LayerFeatureError("The provided layer is None.", layer_name="Unknown")
    

    try:
        features = list(layer.getFeatures())
        if not features:
            raise LayerFeatureError("No features found in the layer.", layer_name=layer.name())
        
        features_info = []
        for feature in layer.getFeatures():
            # Gather all info: ID, attributes (as dict), geometry summary (centroid or WKT)
            attr_dict = {layer.fields()[i].name(): feature.attributes()[i] for i in range(len(feature.attributes()))}
            geom_summary = feature.geometry().asWkt() if feature.geometry() else "No geometry"
            display_string = f"ID: {feature.id()}, Attributes: {attr_dict}, Geometry: {geom_summary}"
            features_info.append((display_string, feature.id()))
        
        selected_feature, selected_feature_id = select_item_from_gui_list(
            items=features_info,
            prompt=prompt,
            title=title
        )
    except SelectionCancelledError:
        raise
    except Exception as e:
        raise LayerFeatureError(f"Error retrieving features: {str(e)}", layer_name=layer.name()) from e
    
    if selected_feature is None and selected_feature_id is None:
        raise NoItemSelectedError("No feature selected from the list.")
    return selected_feature, selected_feature_id

def select_layer_from_available_layers(title: str = "Select a Layer", prompt: str = "Choose a layer:") -> QgsMapLayer:
    """
    Command line tool to select one layer from the current project.
    Returns:
        QgsMapLayer: The selected layer
    """
    # Get all layers in the project
    project = QgsProject.instance()
    layers = list(project.mapLayers().values())

    # Show the dialog
    dialog = ItemSelectionDialog(
        items=layers,
        title=title,
        prompt=prompt
    )

    if dialog.exec_() == QDialog.Accepted:
        selected_layer = dialog.get_selected_item()
        return selected_layer
    
def get_bbox_from_current_canvas() -> QgsRectangle:
    """
    Gives the QgsRectangle with the coordinates for the current view in the visual editor.
    
    Returns:
        QgsRectangle: Rectangle that encompasses the view of the visual editor
    """
    canvas = iface.mapCanvas()
    bbox = canvas.extent()
    return bbox

def run_selection_dialog_column_values(layer: QgsVectorLayer, column_name: str, title: str = None, instruction: str = None) -> list:
    # 1. Get distinct values from the layer
    field_index = layer.fields().indexFromName(column_name)
    if field_index == -1:
        raise ValueError(f"Column '{column_name}' does not exist on layer '{layer.name()}'.")

    distinct_values = layer.uniqueValues(field_index)
    
    if not distinct_values:
        print(f"No data found in column '{column_name}'")
        return []

    # 2. Create the dialog
    dialog_title = title if title is not None else f"Select {column_name} Values"
    dialog_instruction = instruction if instruction is not None else f"Select one or more values from the '{column_name}' column to filter the features:"

    dialog = ColumnMultiselectDialog(
        parent=None, # Pass your main window if you have one, else None
        title=dialog_title,
        column_name=column_name,
        options=distinct_values,
        instruction=dialog_instruction,
    )
    
    # 3. Execute
    if dialog.exec_() == QDialog.Accepted:
        selected = dialog.get_selected()
        print(f"User selected: {selected}")
        return selected
    else:
        print("Selection cancelled.")
        return []

def get_user_input_dialog(title: str, prompt: str, default_value: str="") -> Optional[str]:
    """
    Creates a QGIS dialog popup to get user input.
    
    Args:
        title (str): The title of the dialog window.
        question (str): The text displayed in the dialog.
        default_value (T): The pre-filled text in the input field.

    
    Returns:
        T: The user's input if 'OK' is pressed, empty string if 'Cancel' is pressed.
        bool: Returns False if the user cancels the dialog.
    """
    
    text, ok = QInputDialog.getText(
        None, 
        title, 
        prompt, 
        QLineEdit.Normal, 
        str(default_value)
    )
    
    if ok and text:
        return text
    else:
        return None
    
def show_error_popup(title: str, message: str):
    """
    Displays a modal error popup dialog that stops execution until the user clicks OK.
    Also logs the error to the QGIS Log Panel.
    
    Args:
        title (str): The title of the popup window.
        message (str): The error message text.
    """
    # Create the popup
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    
    # Execute the dialog (this pauses execution here)
    msg_box.exec()
# exceptions.py

class QGISGuiError(Exception):
    """Base exception for errors occurring within QGIS GUI interactions."""
    pass

class SelectionCancelledError(QGISGuiError):
    """Raised when the user cancels a selection dialog (Rejected)."""
    def __init__(self, message="User cancelled the selection"):
        super().__init__(message)

class NoItemSelectedError(QGISGuiError):
    """Raised when the dialog accepts but no valid item is returned."""
    def __init__(self, message="No item was selected from the list"):
        super().__init__(message)

class LayerFeatureError(QGISGuiError):
    """Raised when there is an issue retrieving or processing features from a layer."""
    def __init__(self, message="Error retrieving features from the layer", layer_name=None):
        self.layer_name = layer_name
        msg = f"{message}"
        if layer_name:
            msg += f" (Layer: {layer_name})"
        super().__init__(msg)
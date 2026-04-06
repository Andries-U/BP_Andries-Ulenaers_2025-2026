from owslib.wfs import WebFeatureService
import requests
import argparse
from datetime import datetime

DEFAULT_VERSION = '2.0.0'
DEFAULT_BBOX = (50.932807,5.381413,50.938987,5.402334)

# Parsing arguments
def get_arguments_from_argparse() -> str:
    """Get WFS URL from argparse."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="WFS URL")
    parser.add_argument("--layer", help="WFS layer")
    parser.add_argument("--output", help="Output file name")
    parser.add_argument("--version", help="WFS version")
    parser.add_argument("--bbox", help="Bbox")
    args = parser.parse_args()
    return args


## Getting user input
# Getting bbox from user
def get_bbox_from_user() -> tuple[float, float, float, float]:
    """Get bbox from user."""
    return input("Enter bbox: (minx, miny, maxx, maxy)").split(",")

# Getting WFS URL from user
def get_wfs_url_from_user() -> str:
    """Get WFS URL."""
    return input("Enter WFS URL: ")


# Getting WFS data from URL
def get_wfs_data_from_url(url: str, version: str = DEFAULT_VERSION) -> WebFeatureService:
    """Get WFS data from a URL."""
    return WebFeatureService(url=url, version=version)

# Getting layer data from wfs
def get_available_wfs_layers(wfs: WebFeatureService) -> list[str]:
    """Get available layers from WFS."""
    return wfs.contents

# Getting layer from user
def get_wfs_layer_from_user(layers: dict[str, any]) -> str:
    print("Available layers:")
    for i, name in enumerate(layers.keys(), 1):
        print(f"{i}: {name}")
    
    layer_input = input("Enter WFS layer number or name: ").strip()
    
    try:
        # If input is a number, convert to index
        idx = int(layer_input) - 1
        if 0 <= idx < len(layers):
            return list(layers.keys())[idx]
        else:
            print("Invalid number. Please try again.")
            return get_wfs_layer_from_user(layers)
    except ValueError:
        # If input is not a number, treat as layer name
        if layer_input in layers:
            return layer_input
        else:
            print("Layer not found. Please try again.")
            return get_wfs_layer_from_user(layers)

# Getting output file name from the user
def get_output_file_from_user() -> str:
    """Get output file from user."""
    return input("Enter output file name (press enter for default): ")

def download_wfs_data_from_layer(wfs: WebFeatureService, layer_name: str, output_file: str) -> None:
    """Download WFS data to a file."""
    wfs_response = wfs.getfeature(typename=layer_name)
    with open(output_file, "wb") as f:
        f.write(wfs_response.read())
    print(f"Data saved to {output_file}")

def download_wfs_data_from_layer_with_bbox(wfs: WebFeatureService, layer_name: str, output_file: str, bbox: tuple[float, float, float, float], crs: str = "urn:ogc:def:crs:EPSG:6.9:4326", output_format: str = "GML32") -> None:
    """Download WFS data to a file."""
    wfs_response = wfs.getfeature(
            typename=layer_name,
            outputFormat=output_format,
            srsname=crs,
            bbox=bbox
        )

    with open(output_file, "wb") as f:
        f.write(wfs_response.read())
    print(f"Data saved to {output_file}")

def download_wfs_data_from_url(url: str, output_file: str) -> None:
    """Download WFS data to a file."""
    wfs_response = requests.get(url)
    with open(output_file, "wb") as f:
        f.write(wfs_response.content)
    print(f"Data saved to {output_file}")

def display_available_layers(layers: list[str]) -> None:
    """Display available layers."""
    print("Available layers:")
    for i, layer in enumerate(layers):
        print(f"{i}: {layer}")


def get_default_output_file(layer_name: str) -> str:
    """Get default output file."""
    return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.gml"

def main():
    # Handle arguments from argparse
    args = get_arguments_from_argparse()

    # Decide the WFS URL
    if args.url is None:
        wfs_url = get_wfs_url_from_user()
    else:
        wfs_url = args.url

    # Decide the WFS version
    if args.version is None:
        version = DEFAULT_VERSION
    else:
        version = args.version

    # Get WFS data from URL
    wfs_data = get_wfs_data_from_url(wfs_url, version)
    
    # Decide the layer we want
    if args.layer is None:
        layers = get_available_wfs_layers(wfs_data)
        layer_name = get_wfs_layer_from_user(layers)
    else:
        layer_name = args.layer

    # Decide the output file name
    if args.output is None:
        output_file = get_output_file_from_user()
        if output_file == "":
            output_file = get_default_output_file(layer_name)
    else:
        output_file = args.output

    # Decide the bbox
    if args.bbox is None:
        bbox = DEFAULT_BBOX
    else:
        bbox = args.bbox

    # Download WFS data from URL  
    download_wfs_data_from_layer_with_bbox(wfs_data, layer_name, output_file, bbox)

if __name__ == "__main__":
    main()
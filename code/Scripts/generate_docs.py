import os
import pydoc
from pathlib import Path

def generate_docs_for_custom_modules(custom_modules: list[str]):
    # Define where you want the docs
    output_dir = Path(__file__).resolve().parent / "docs"
    output_dir.mkdir(exist_ok=True)

    # Change directory to output_dir
    current_dir = os.getcwd()
    os.chdir(output_dir)

    try:
        for module_name in custom_modules:
            print(f"Generating docs for {module_name}...")
            pydoc.writedoc(module_name)
    finally:
        # Return to original directory
        os.chdir(current_dir)

    print(f"Documentation generated in: {output_dir}")

if __name__ == "__main__":
    generate_docs_for_custom_modules(CUSTOM_MODULES)
# dev_tools.py
import sys
import importlib
import os

# List the names of YOUR custom modules here (without .py)
# Add any new module name you create to this list
MY_MODULES = [
    'reset_module_cache',
    'pvgis_client',
    'pvgis_parser',
    'andries_utils',
    'Item_selection',
    'SolarDataClient',
    # 'another_module', 
    # 'src.api_clients.pvgis_client' # If you are using the src folder structure
]

def reload_all_custom_modules():
    """
    Forces QGIS to reload all modules listed in MY_MODULES.
    """
    count = 0
    print("--- Starting Module Reload ---")
    
    for mod_name in MY_MODULES:
        if mod_name in sys.modules:
            try:
                importlib.reload(sys.modules[mod_name])
                print(f"✅ Reloaded: {mod_name}")
                count += 1
            except Exception as e:
                print(f"❌ Failed to reload {mod_name}: {e}")
        else:
            print(f"⚪ Skipped (not loaded yet): {mod_name}")
            
    print(f"--- Reload Complete ({count} modules updated) ---")

reload_all_custom_modules()
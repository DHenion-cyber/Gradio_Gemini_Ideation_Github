import os
import sys

project_root = os.path.abspath(os.path.dirname(__file__))

print(f"--- Test Import Diagnostic ---")
print(f"Current working directory (os.getcwd()): {os.getcwd()}")
print(f"Project root (os.path.dirname(__file__)): {project_root}")

# Ensure project root is in sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Inserted project root into sys.path: {project_root}")
else:
    # If it is already there, ensure it's at the front for priority
    if sys.path[0] != project_root:
        sys.path.remove(project_root)
        sys.path.insert(0, project_root)
        print(f"Moved project root to the front of sys.path: {project_root}")


print(f"Final sys.path used for import (first 5 entries): {sys.path[:5]}")

path_to_check_from_root = "" # This will be relative to project_root for printing
print(f"\nChecking path components starting from project root: {project_root}")

components = ["src", "workflows", "value_prop", "phases", "intake.py"]
full_path_to_module_file = project_root
path_valid = True

for i, component_name in enumerate(components):
    path_to_check_from_root = os.path.join(path_to_check_from_root, component_name)
    full_path_to_module_file = os.path.join(full_path_to_module_file, component_name)
    
    current_target_path = os.path.join(project_root, path_to_check_from_root)
    
    exists = os.path.exists(current_target_path)
    is_dir = os.path.isdir(current_target_path)
    is_file = os.path.isfile(current_target_path)
    
    print(f"Checking component '{component_name}': Path='{current_target_path}'")
    print(f"  Exists: {exists}, Is Dir: {is_dir}, Is File: {is_file}")
    
    if not exists:
        print(f"STOP: Path component '{component_name}' (resolved to '{current_target_path}') does not exist.")
        path_valid = False
        break
    
    # If it's a directory component (not the final .py file)
    if is_dir and component_name != "intake.py":
        init_py_path = os.path.join(current_target_path, "__init__.py")
        init_exists = os.path.isfile(init_py_path)
        print(f"  Checking for __init__.py: '{init_py_path}' -> Exists: {init_exists}")
        if not init_exists:
            print(f"WARNING: __init__.py not found in directory '{current_target_path}'. This directory will not be treated as a package.")
            # For our import 'src.workflows...', this is a critical failure for this component.
            path_valid = False # Treat as invalid for package import
            # break # Don't break, let it check further components if they exist physically

if path_valid and os.path.isfile(full_path_to_module_file):
    print(f"\nAll path components and __init__.py files (for directories) seem to exist up to the module file: {full_path_to_module_file}")
    print(f"Attempting to import: 'src.workflows.value_prop.phases.intake'")
    try:
        # Attempt the import
        import src.workflows.value_prop.phases.intake
        print("SUCCESS: Module 'src.workflows.value_prop.phases.intake' imported successfully.")
        print(f"Location of imported module: {src.workflows.value_prop.phases.intake.__file__}")

        # Further test: try to access the class
        from src.workflows.value_prop.phases.intake import IntakePhase
        print("SUCCESS: Class 'IntakePhase' accessed successfully from the module.")

    except ModuleNotFoundError as e:
        print(f"FAIL (after path checks): ModuleNotFoundError: {e}")
    except ImportError as e:
        print(f"FAIL (after path checks): ImportError: {e}")
    except Exception as e:
        print(f"FAIL (after path checks): An unexpected error occurred: {e}")
else:
    print(f"\nSkipping import attempt because path checks indicated an issue (path_valid: {path_valid}, module_file_exists: {os.path.isfile(full_path_to_module_file)}).")
    if not os.path.isfile(full_path_to_module_file):
        print(f"The target module file itself ('{full_path_to_module_file}') does not seem to be a file or does not exist.")


print(f"--- End Test Import Diagnostic ---")
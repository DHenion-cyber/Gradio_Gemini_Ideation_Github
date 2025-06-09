import os

with open("project_file_structure.txt", "w", encoding="utf-8") as f:
    for dirpath, dirnames, filenames in os.walk("."):
        dirpath_clean = dirpath.lstrip("./")
        for filename in filenames:
            relative_path = os.path.join(dirpath_clean, filename) if dirpath_clean else filename
            f.write(relative_path + "\n")

print("File structure saved as project_file_structure.txt")

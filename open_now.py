import json
import os
import subprocess
import sys

# Path to the JSON file containing the list of folders
PERSISTENCE_FILE = "folder_list.json"

def open_folders(folders):
    """
    Open folders in the system's file explorer.
    :param folders: A list of folder paths to open.
    """
    for folder in folders:
        folder_path = os.path.normpath(folder)  # Normalize path for consistency
        if not os.path.exists(folder_path):
            print(f"The folder {folder_path} does not exist.")
            continue  # Skip the nonexistent folder and move to the next one
        if sys.platform == "win32":
            subprocess.Popen(['explorer', folder_path])
        elif sys.platform == "darwin":
            subprocess.call(["open", folder_path])
        else:
            subprocess.Popen(['xdg-open', folder_path])

def load_folders_list():
    """
    Load the folder list from the JSON file.
    """
    if os.path.exists(PERSISTENCE_FILE):
        with open(PERSISTENCE_FILE, "r") as file:
            folders = json.load(file)
        return folders
    else:
        print("Persistence file does not exist.")
        return []

if __name__ == "__main__":
    folders = load_folders_list()
    open_folders(folders)

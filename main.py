import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import sys
import json
import os

# Constants
PERSISTENCE_FILE = "folder_list.json"  # File to save and load the folder list

# History stack for undo functionality
history = []

# Redo history stack for redo functionality
redo_history = []

def open_folders(folders, in_same_window=False):
    """
    Open folders in the system's file explorer.
    :param folders: A list of folder paths to open.
    :param in_same_window: Indicates if folders should be opened in the same window. Placeholder due to limitations.
    """
    for folder in folders:
        folder_path = os.path.normpath(folder)  # Normalize path for consistency
        if not os.path.exists(folder_path):
            messagebox.showerror("Error", f"The folder {folder_path} does not exist.")
            continue  # Skip the nonexistent folder and move to the next one
        if sys.platform == "win32":
            subprocess.Popen(['explorer', folder_path])
        elif sys.platform == "darwin":
            subprocess.call(["open", folder_path])
        else:
            subprocess.Popen(['xdg-open', folder_path])

def update_folders_list(action, item=None):
    """
    Update the folders list and history based on action type and item.
    :param action: Action type (add, remove, replace, clear).
    :param item: The item(s) involved in the action.
    """
    if action == 'add':
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            folders_list.insert(tk.END, folder_selected)
            history.append(('add', folder_selected))
            
    elif action == 'remove':
        selected_indices = folders_list.curselection()
        if selected_indices:
            for i in reversed(selected_indices):  # Reverse to avoid index shifting
                folder_removed = folders_list.get(i)
                history.append(('remove', folder_removed))
                folders_list.delete(i)
        else:
            messagebox.showinfo("Info", "Please select at least one folder to remove.")
            
    elif action == 'replace':
        selected_indices = folders_list.curselection()
        if len(selected_indices) != 1:  # Check if exactly one item is selected
            messagebox.showinfo("Info", "Please select exactly one folder to replace.")
            return

        selected_index = selected_indices[0]
        folder_replaced = folders_list.get(selected_index)
        folder_new = filedialog.askdirectory()
        if folder_new:
            folders_list.delete(selected_index)
            folders_list.insert(selected_index, folder_new)
            history.append(('replace', (folder_replaced, folder_new)))
            
    elif action == 'clear':
        current_list = folders_list.get(0, tk.END)
        if current_list:
            history.append(('clear', current_list))
            folders_list.delete(0, tk.END)
        else:
            messagebox.showinfo("Info", "The list is already empty.")

def edit_selected_path():
    selected = folders_list.curselection()
    if not selected:
        messagebox.showinfo("Info", "Please select a folder to edit.")
        return
    index = selected[0]
    old_path = folders_list.get(index)

    # Create a pop-up window for editing
    edit_win = tk.Toplevel(app)
    edit_win.title("Edit Path")
    
    # Inherit the icon from the main window
    edit_win.iconbitmap('SwiftFolder.ico')

    tk.Label(edit_win, text="Edit path:").pack(padx=10, pady=5)

    path_var = tk.StringVar(value=old_path)
    path_entry = tk.Entry(edit_win, textvariable=path_var, width=70) 
    path_entry.pack(padx=10, pady=5)
    path_entry.focus_set()

    def confirm_edit():
        new_path = path_var.get()
        if not os.path.exists(new_path):
            messagebox.showerror("Error", "The folder does not exist.")
            return

        # Find the index of the old path
        try:
            index = folders_list.get(0, tk.END).index(old_path)
        except ValueError:
            messagebox.showerror("Error", "The original folder could not be found in the list.")
            return

        # Replace the old path with the new path
        folders_list.delete(index)
        folders_list.insert(index, new_path)

        # Add the replace action to the history
        history.append(('replace', (old_path, new_path)))

        edit_win.destroy()

    tk.Button(edit_win, text="Confirm", command=confirm_edit).pack(pady=5)

    # Disable vertical resizing of the popup window
    edit_win.resizable(True, False)

def undo_action():
    if history:
        action, item = history.pop()
        redo_history.append((action, item))  # Add to redo history
        
        if action == 'add':
            # Find and remove the added item
            try:
                index = folders_list.get(0, tk.END).index(item)
                folders_list.delete(index)
            except ValueError:
                pass  # Item not found, likely already removed
        elif action == 'remove':
            # Add the removed item back
            folders_list.insert(tk.END, item)
        elif action == 'replace':
            # Replace the new item with the original
            original, new = item
            try:
                index = folders_list.get(0, tk.END).index(new)
                folders_list.delete(index)
                folders_list.insert(index, original)
            except ValueError:
                pass  # Item not found, likely already removed or replaced again
        elif action == 'clear':
            # Restore the list to its previous state
            folders_list.delete(0, tk.END)
            for folder in item:
                folders_list.insert(tk.END, folder)
    else:
        messagebox.showinfo("Info", "No actions to undo.")

def redo_action():
    if redo_history:
        action, item = redo_history.pop()
        history.append((action, item))  # Add back to history for potential undo
        
        if action == 'add':
            folders_list.insert(tk.END, item)
        elif action == 'remove':
            try:
                index = folders_list.get(0, tk.END).index(item)
                folders_list.delete(index)
            except ValueError:
                pass
        elif action == 'replace':
            original, new = item
            try:
                index = folders_list.get(0, tk.END).index(original)
                folders_list.delete(index)
                folders_list.insert(index, new)
            except ValueError:
                pass
        elif action == 'clear':
            folders_list.delete(0, tk.END)
    else:
        messagebox.showinfo("Info", "No actions to redo.")

def file_operations(operation):
    """
    Load or save the folder list to a file based on the operation type.
    :param operation: Type of file operation (load, save).
    """
    if operation == 'save':
        folders = folders_list.get(0, tk.END)
        with open(PERSISTENCE_FILE, "w") as file:
            json.dump(folders, file)
    elif operation == 'load':
        if os.path.exists(PERSISTENCE_FILE):
            with open(PERSISTENCE_FILE, "r") as file:
                folders = json.load(file)
                folders_list.delete(0, tk.END)  # Clear existing list
                for folder in folders:
                    folders_list.insert(tk.END, folder)

def setup_ui(app):
    """
    Setup the user interface for the Folder Opener application.
    :param app: The main application window.
    """
    # Layout configurations
    main_frame, btn_frame = configure_layout(app)
    
    # Listbox with scrollbars
    global folders_list  # Make folders_list accessible globally for update functions
    folders_list = setup_listbox_with_scrollbars(main_frame)

    # Checkbutton for opening folders in the same window
    same_window_var = tk.IntVar()
    same_window_checkbutton = tk.Checkbutton(app, text="Open folders in the same window", variable=same_window_var)
    same_window_checkbutton.grid(row=1, column=0, sticky="w", padx=10)

    # Button setup with commands
    buttons = [
        ("Add Folder", lambda: update_folders_list('add')),
        ("Remove Selected", lambda: update_folders_list('remove')),
        ("Replace", lambda: update_folders_list('replace')),
        ("Undo", undo_action),
        ("Redo", redo_action),
        ("Clear List", lambda: update_folders_list('clear')),
        ("Open Folders", lambda: open_folders(folders_list.get(0, tk.END), same_window_var.get()))
    ]
    setup_buttons(btn_frame, buttons)

    # Load folders list on startup and save on close
    file_operations('load')
    app.protocol("WM_DELETE_WINDOW", lambda: (file_operations('save'), app.destroy()))

def configure_layout(app):
    """
    Configure the main layout of the application.
    :param app: The main application window.
    Returns frames for listbox and buttons.
    """
    main_frame = tk.Frame(app)
    main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    app.grid_rowconfigure(0, weight=1)
    app.grid_columnconfigure(0, weight=1)

    btn_frame = tk.Frame(app)
    btn_frame.grid(row=2, column=0, pady=(0, 10), sticky="ew")

    return main_frame, btn_frame

def setup_listbox_with_scrollbars(main_frame):
    """
    Setup the Listbox with vertical and horizontal scrollbars.
    :param main_frame: The frame to hold the Listbox and scrollbars.
    """
    folders_list = tk.Listbox(main_frame, width=50, height=15, selectmode=tk.EXTENDED)
    folders_list.grid(row=0, column=0, sticky="nsew", padx=10)

    scrollbar_vertical = tk.Scrollbar(main_frame, orient="vertical", command=folders_list.yview)
    scrollbar_vertical.grid(row=0, column=1, sticky="ns")

    folders_list.config(yscrollcommand=scrollbar_vertical.set)

    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)

    return folders_list

def setup_buttons(btn_frame, buttons):
    """
    Create and place buttons on the button frame.
    :param btn_frame: The frame to hold the buttons.
    :param buttons: A list of tuples containing button text and commands.
    """
    for i, (text, command) in enumerate(buttons):
        btn = tk.Button(btn_frame, text=text, command=command)
        btn.grid(row=0, column=i, sticky="ew", padx=5)
    btn_frame.grid_columnconfigure(tuple(range(len(buttons))), weight=1)  # Distribute buttons evenly

# Main application setup
if __name__ == "__main__":
    app = tk.Tk()
    app.iconbitmap('SwiftFolder.ico')
    app.resizable(True, False)
    app.title("SwiftFolder") 
    setup_ui(app)
    folders_list.bind('<Double-1>', lambda e: edit_selected_path())
    app.mainloop()

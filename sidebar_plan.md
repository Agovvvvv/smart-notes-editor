# Plan: File Management Sidebar Implementation

## 1. Core Objective
- Implement a sidebar panel that allows users to browse, open, create, rename, and delete files and folders within a project workspace.

## 2. UI Design & Implementation (PyQt5)
   - **Sidebar Widget:**
     - Use a `QDockWidget` to host the file explorer, allowing it to be docked, floated, or hidden.
     - Title: "File Explorer" or "Project Explorer".
   - **File/Folder Display:**
     - Use a `QTreeView` to display the file system hierarchy.
     - Implement a `QFileSystemModel` to populate the `QTreeView`. This model can handle most of the directory listing and basic file system interaction.
     - Filter the `QFileSystemModel` to show relevant file types (e.g., `.txt`, `.md`) and hide others (e.g., `.pyc`, `__pycache__`).
     - Display icons for folders and different file types.
   - **Context Menu Actions:**
     - Implement a context menu (right-click) on items in the `QTreeView` for actions like:
       - `Open File`
       - `New File`
       - `New Folder`
       - `Rename`
       - `Delete`
       - `Refresh`
   - **Toolbar/Buttons (Optional, within the dock widget):**
     - Small buttons for common actions like `New File`, `New Folder`, `Refresh`.

## 3. Backend Logic & Controller Interaction
   - **File Operations (Leverage/Extend `FileController` or create `DirectoryController`):**
     - The existing `FileController` handles single file operations (open, save). It might need to be extended or a new controller might be beneficial for directory-level operations.
     - **List Files/Directories:** Primarily handled by `QFileSystemModel`.
     - **Open File:**
       - When a file is double-clicked or "Open" is selected, use `FileController.open_file(path)`.
     - **Create File/Folder:**
       - Implement methods in `FileController` (or a new controller) for `create_new_file(path)` and `create_new_folder(path)`.
       - Prompt user for name.
     - **Rename File/Folder:**
       - Implement `rename_item(old_path, new_name)` in the controller.
       - `QFileSystemModel` might offer some renaming capabilities directly, or OS-level functions can be used.
     - **Delete File/Folder:**
       - Implement `delete_item(path)` in the controller.
       - **Crucial:** Implement a confirmation dialog before deletion.
       - Handle recursive deletion for folders.
   - **Root Directory Management:**
     - The application will need a concept of a "current workspace" or "root directory" for the file explorer.
     - Add an action "Open Folder..." (similar to "Open File...") to set this root directory for the `QFileSystemModel`.
     - Store/retrieve the last used root directory in `settings.json` via the `Settings` class.

## 4. Integration with MainWindow
   - **Initialization:**
     - In `MainWindow.__init__`, create the `QDockWidget` and the file explorer widget it contains.
     - Set up the `QFileSystemModel` and `QTreeView`.
     - Set an initial root path (e.g., last opened folder, or a default like `data/`).
   - **Signal/Slot Connections:**
     - Connect UI actions from the sidebar (double-clicks, context menu triggers) to appropriate slots in [MainWindow](cci:2://file:///Users/nick/Desktop/Agov_Intelligence/Projects/gestore_appunti/src/views/main_window.py:63:0-1282:36) or directly to `FileController` methods.
     - Example: `treeView.doubleClicked.connect(self.on_sidebar_file_activated)`
   - **Menu Items:**
     - Add "Open Folder..." to the "File" menu.
     - Add a "View" menu item to toggle the visibility of the File Explorer dock widget.

## 5. Key Files & Modules Involved
   - **New Files (Potentially):**
     - `src/ui/panels/file_explorer_panel.py` (if the sidebar logic is complex enough to warrant its own class).
     - Or, integrate directly into [MainWindow](cci:2://file:///Users/nick/Desktop/Agov_Intelligence/Projects/gestore_appunti/src/views/main_window.py:63:0-1282:36) if simpler.
   - **Existing Files to Modify:**
     - [src/views/main_window.py](cci:7://file:///Users/nick/Desktop/Agov_Intelligence/Projects/gestore_appunti/src/views/main_window.py:0:0-0:0): To host the dock widget, connect signals.
     - `src/controllers/file_controller.py`: To add new file/folder manipulation methods.
     - `src/utils/settings.py`: To save/load the last workspace root path.
     - `src/ui/ui_factory.py`: To add menu items for "Open Folder" and toggling the panel.

## 6. Error Handling & User Feedback
   - Provide clear feedback for all operations (e.g., "File created," "Error deleting folder").
   - Handle permissions errors gracefully if file operations fail.
   - Use `QMessageBox` for confirmations (delete) and error reporting.

## 7. Future Enhancements (Optional)
   - File system watcher to auto-refresh the tree view on external changes.
   - Drag-and-drop support for moving files/folders.
   - Basic Git integration indicators (if a `.git` folder is present).
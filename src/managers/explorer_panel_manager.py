import logging
import os
from functools import partial
from PyQt5.QtWidgets import QMessageBox, QMenu, QAction, QTreeWidgetItem, QInputDialog
from PyQt5.QtCore import Qt
from typing import Optional

# Assuming WorkspaceManagerDialog is correctly imported where it's instantiated if not here
# from views.dialogs.workspace_manager_dialog import WorkspaceManagerDialog 

logger = logging.getLogger(__name__)

class ExplorerPanelManager:
    """Manages the UI logic for the explorer panel, switching between welcome screen and file tree."""
    def __init__(self, main_window, workspace_manager, dialog_manager, 
                 file_tree_widget, workspace_welcome_widget, file_explorer_dock_widget,
                 file_controller, status_bar):
        self.main_window = main_window
        self.workspace_manager = workspace_manager
        self.dialog_manager = dialog_manager
        self.file_tree_widget = file_tree_widget
        self.workspace_welcome_widget = workspace_welcome_widget
        self.file_explorer_dock_widget = file_explorer_dock_widget
        self.file_controller = file_controller
        self.status_bar = status_bar
        self.recent_workspaces_menu = QMenu("Open &Recent Workspace", self.main_window)
        self._current_file_explorer_root_path = None
        
        # Connect signals from welcome widget
        # These connections are now made here, centralizing explorer panel logic.
        if self.workspace_welcome_widget:
            self.workspace_welcome_widget.manage_workspaces_requested.connect(self.show_workspace_manager_dialog)
            self.workspace_welcome_widget.recent_workspace_selected.connect(self._handle_recent_workspace_selected)
        else:
            logger.error("ExplorerPanelManager: workspace_welcome_widget is None during init.")

    def update_explorer_display(self, root_path: Optional[str], active_ws_name: Optional[str]):
        """Updates the display of the file explorer panel based on the provided root path and workspace name."""
        logger.debug(f"ExplorerPanelManager.update_explorer_display: root='{root_path}', ws_name='{active_ws_name}'")

        is_valid_workspace_path = root_path and os.path.isdir(root_path)

        if is_valid_workspace_path:
            self.file_explorer_dock_widget.setWindowTitle(active_ws_name if active_ws_name else "Workspace")
            self._populate_file_tree_widget(root_path)
            self.file_tree_widget.show()
            if self.workspace_welcome_widget:
                self.workspace_welcome_widget.hide()
            logger.info(f"Displaying file tree for workspace: '{active_ws_name}' at '{root_path}'.")
        else:
            self.file_explorer_dock_widget.setWindowTitle("Explorer")
            self.file_tree_widget.clear()
            self.file_tree_widget.hide()
            if self.workspace_welcome_widget:
                self.workspace_welcome_widget.show()
            
            if not active_ws_name:
                logger.info("No active workspace. Showing welcome screen.")
            elif not root_path:
                logger.warning(f"Workspace '{active_ws_name}' has no path. Showing welcome screen.")
            else: # root_path is present but not a valid directory
                logger.warning(f"Invalid path for workspace '{active_ws_name}': '{root_path}'. Showing welcome screen.")

        # Update recent workspaces on the welcome screen, if it exists
        if self.workspace_welcome_widget:
            recent_workspaces = self.workspace_manager.get_recent_workspaces_details()
            self.workspace_welcome_widget.populate_recent_workspaces(recent_workspaces)
            logger.debug(f"Recent workspaces list updated on welcome screen with {len(recent_workspaces)} items.")

    def get_recent_workspaces_menu(self) -> QMenu:
        """Returns the 'Open Recent Workspace' QMenu instance."""
        return self.recent_workspaces_menu

    def populate_recent_workspaces_menu(self):
        """Populates the 'Open Recent Workspace' submenu with recent workspaces."""
        if not hasattr(self, 'recent_workspaces_menu') or self.recent_workspaces_menu is None:
            logger.warning("Cannot populate recent workspaces: menu attribute not found or is None.")
            return

        self.recent_workspaces_menu.clear()
        # functools.partial is imported at the top of the module

        recent_workspaces = self.workspace_manager.get_recent_workspaces_details()

        if not recent_workspaces:
            no_recent_action = QAction("No Recent Workspaces", self.main_window) # Parent to main_window
            no_recent_action.setEnabled(False)
            self.recent_workspaces_menu.addAction(no_recent_action)
        else:
            for ws_details in recent_workspaces:
                ws_name = ws_details.get('name')
                ws_path = ws_details.get('path')
                if not ws_name:
                    logger.warning(f"Recent workspace entry missing name: {ws_details}")
                    continue
                
                action = QAction(ws_name, self.main_window) # Parent to main_window
                if ws_path:
                    action.setStatusTip(f"Open workspace: {ws_name} ({ws_path})")
                else:
                    action.setStatusTip(f"Open workspace: {ws_name} (Path not available)")
                
                action.triggered.connect(partial(self._handle_recent_workspace_selected, ws_name))
                self.recent_workspaces_menu.addAction(action)
        logger.debug(f"Recent workspaces menu populated with {len(recent_workspaces) if recent_workspaces else 0} items.")

    def _show_workspace_welcome_screen(self):
        """Shows the workspace welcome screen and hides the file tree."""
        logger.info("Showing workspace welcome screen.")
        self.main_window._current_file_explorer_root_path = None
        self.file_tree_widget.hide()
        self.file_tree_widget.clear()
        self.workspace_welcome_widget.populate_recent_workspaces(
            self.workspace_manager.get_recent_workspaces_details()
        )
        self.workspace_welcome_widget.show()
        self.file_explorer_dock_widget.setWindowTitle("Explorer")

    def _show_file_tree_for_workspace(self, workspace_name: str, workspace_path: str):
        """Shows the file tree for the given workspace and hides the welcome screen."""
        logger.info(f"Showing file tree for workspace: {workspace_name} ({workspace_path})")
        # self._current_file_explorer_root_path is now set by _populate_file_tree_widget
        self._populate_file_tree_widget(workspace_path)
        self.file_tree_widget.show()
        self.workspace_welcome_widget.hide()
        self.file_explorer_dock_widget.setWindowTitle(f"{workspace_name}")

    def _update_explorer_panel_view(self):
        """
        Updates the explorer panel to show either the WorkspaceWelcomeWidget
        or the FileTreeWidget based on the active workspace.
        """
        active_workspace_name = self.workspace_manager.get_active_workspace_name()
        active_workspace_path = self.workspace_manager.get_active_workspace_path()

        if active_workspace_name and active_workspace_path:
            self._show_file_tree_for_workspace(active_workspace_name, active_workspace_path)
        else:
            self._show_workspace_welcome_screen()
        
        self.main_window.update_title() # Update main window title based on workspace and file

    def _populate_file_tree_widget(self, root_path: str):
        """
        Populates the file_tree_widget with directories and notes (.md, .txt)
        from the given root_path, adhering to the custom display style.
        Stores full path in Qt.UserRole and item type ('directory'/'file') in Qt.UserRole + 1.
        """
        self.file_tree_widget.clear()
        self.file_tree_widget.setHeaderHidden(True) # Ensure header is hidden for custom view
        self.file_tree_widget.setColumnCount(1)     # Ensure only one column

        if not root_path or not os.path.isdir(root_path):
            logger.warning(f"_populate_file_tree_widget: Invalid root_path: {root_path}")
            self._current_file_explorer_root_path = None # Ensure it's cleared on invalid path
            return

        logger.debug(f"Populating file tree widget for path: {root_path}")
        self._current_file_explorer_root_path = root_path # Store the root path being used

        # Helper function to add items recursively
        def add_items_recursive(parent_item, current_path):
            try:
                for entry_name in sorted(os.listdir(current_path)):
                    full_path = os.path.join(current_path, entry_name)
                    
                    if os.path.isdir(full_path):
                        dir_item = QTreeWidgetItem(parent_item, [entry_name])
                        dir_item.setData(0, Qt.UserRole, full_path)      # Store full path
                        dir_item.setData(0, Qt.UserRole + 1, "directory") # Store type
                        add_items_recursive(dir_item, full_path) # Recurse
                    elif os.path.isfile(full_path):
                        if entry_name.lower().endswith(('.txt', '.md')):
                            file_item = QTreeWidgetItem(parent_item, [entry_name])
                            file_item.setData(0, Qt.UserRole, full_path)  # Store full path
                            file_item.setData(0, Qt.UserRole + 1, "file")    # Store type
            except OSError as e:
                logger.error(f"Error listing directory {current_path}: {e}")

        add_items_recursive(self.file_tree_widget, root_path) # Initial call

    def _handle_recent_workspace_selected(self, workspace_name: str):
        """Handles selection of a recent workspace from the welcome widget."""
        logger.info(f"Recent workspace selected from welcome screen: {workspace_name}")
        if self.workspace_manager.set_active_workspace_name(workspace_name):
            self._update_explorer_panel_view() # This will show tree and update title
            # Refresh recent workspaces list in menu after successful activation
            self.populate_recent_workspaces_menu()
        else:
            logger.error(f"Failed to set '{workspace_name}' as active workspace.")
            self.dialog_manager.show_error(
                "Error Setting Workspace",
                f"Could not set '{workspace_name}' as the active workspace. It might have been moved or deleted."
            )
            self._update_explorer_panel_view() # Refresh welcome screen (e.g. to update recent list if needed)

    def show_workspace_manager_dialog(self):
        """Shows the workspace manager dialog."""
        logger.debug("Showing Workspace Manager Dialog.")
        # Dynamically import here to avoid circular dependency if WorkspaceManagerDialog imports something from managers
        from views.dialogs.workspace_manager_dialog import WorkspaceManagerDialog 
        dialog = WorkspaceManagerDialog(workspace_manager=self.workspace_manager, parent=self.main_window)
        dialog.workspaces_updated.connect(self._on_workspaces_updated) 
        dialog.exec_()

    def _on_workspaces_updated(self):
        """
        Handles updates originating from the WorkspaceManagerDialog or other
        workspace management actions.
        Refreshes the UI elements that depend on workspace state.
        """
        logger.info("Workspaces updated, refreshing explorer panel and other relevant UI.")
        self._update_explorer_panel_view()
        
        # TODO Later: Refresh notes list in the new dedicated notes sidebar (from memory f15358b5-9fc5-428d-8578-be5fdbb51e82)
        # This TODO remains as it pertains to a future, separate notes sidebar.
        
        # Also, re-populate recent workspaces list in the "File > Open Recent Workspace" menu
        self.populate_recent_workspaces_menu()

    # --- File Explorer Context Menu and Item Handling --- 

    def on_file_explorer_context_menu(self, position):
        """Shows a context menu for the QTreeWidget file explorer."""
        item = self.file_tree_widget.itemAt(position)
        menu = QMenu(self.main_window) # Parent to main_window

        full_path = None
        item_type = None
        item_text = None

        if item:
            full_path = item.data(0, Qt.UserRole)
            item_type = item.data(0, Qt.UserRole + 1)
            item_text = item.text(0)
        
        if not self._current_file_explorer_root_path:
            logger.warning("File explorer context menu: No current workspace root path set.")
            return

        # Actions for a file item
        if item and item_type == "file" and full_path:
            open_action = menu.addAction(f"Open '{item_text}'")
            open_action.triggered.connect(lambda: self._handle_open_explorer_item(full_path))
            menu.addSeparator()
            rename_action = menu.addAction(f"Rename '{item_text}'...")
            rename_action.triggered.connect(lambda: self._handle_rename_explorer_item(full_path, item_text))
            delete_action = menu.addAction(f"Delete '{item_text}'...")
            delete_action.triggered.connect(lambda: self._handle_delete_explorer_item(full_path, item_text, is_dir=False))
        
        # Actions for a directory item
        elif item and item_type == "directory" and full_path:
            new_file_action = menu.addAction("New File in this Folder...")
            new_file_action.triggered.connect(lambda: self._handle_new_file_explorer(base_path=full_path))
            new_folder_action = menu.addAction("New Folder in this Folder...")
            new_folder_action.triggered.connect(lambda: self._handle_new_folder_explorer(base_path=full_path))
            menu.addSeparator()
            rename_folder_action = menu.addAction(f"Rename '{item_text}'...")
            rename_folder_action.triggered.connect(lambda: self._handle_rename_explorer_item(full_path, item_text))
            delete_folder_action = menu.addAction(f"Delete '{item_text}'...")
            delete_folder_action.triggered.connect(lambda: self._handle_delete_explorer_item(full_path, item_text, is_dir=True))

        # Actions for empty space (or root context)
        else: # No specific item clicked, or item data is invalid - actions relative to root
            if menu.actions(): menu.addSeparator()
            new_file_at_root_action = menu.addAction("New File in Workspace Root...")
            new_file_at_root_action.triggered.connect(lambda: self._handle_new_file_explorer(base_path=self._current_file_explorer_root_path))
            new_folder_at_root_action = menu.addAction("New Folder in Workspace Root...")
            new_folder_at_root_action.triggered.connect(lambda: self._handle_new_folder_explorer(base_path=self._current_file_explorer_root_path))

        # Always add Refresh action
        if menu.actions():
            menu.addSeparator()
        refresh_action = menu.addAction("Refresh File Explorer")
        refresh_action.triggered.connect(self._handle_refresh_explorer)

        if menu.actions():
            menu.exec_(self.file_tree_widget.viewport().mapToGlobal(position))

    def _handle_open_explorer_item(self, file_path: str):
        logger.debug(f"Context menu: Opening item: {file_path}")
        if file_path.lower().endswith(('.txt', '.md')):
            # Use the file_controller passed during initialization
            if hasattr(self.file_controller, 'open_note_from_path'):
                self.file_controller.open_note_from_path(file_path)
            elif hasattr(self.file_controller, 'open_file'): 
                self.file_controller.open_file(file_path)
            else:
                self.dialog_manager.show_critical("Error", "File controller is misconfigured for opening files.")
        else:
            self.dialog_manager.show_warning("Unsupported File Type", "This file type cannot be opened by the editor.")

    def _handle_new_file_explorer(self, base_path: str):
        logger.debug(f"Context menu: Creating new file in: {base_path}")
        file_name, ok = QInputDialog.getText(self.main_window, "New File", "Enter name for the new file (e.g., my_note.md):")
        if ok and file_name:
            if not (file_name.lower().endswith('.txt') or file_name.lower().endswith('.md')):
                file_name += '.md' # Default to .md if no valid extension
            full_path = os.path.join(base_path, file_name)
            success, message = self.file_controller.create_file_in_explorer(full_path)
            if success:
                self.dialog_manager.show_info("File Created", message)
                self._handle_refresh_explorer()
            else:
                # Access constants via self.main_window
                self.dialog_manager.show_warning(self.main_window.INVALID_NAME_TITLE if "exists" in message.lower() else "Error Creating File", message)
        elif ok and not file_name:
            self.dialog_manager.show_warning(self.main_window.INVALID_NAME_TITLE, "File name cannot be empty.")

    def _handle_new_folder_explorer(self, base_path: str):
        logger.debug(f"Context menu: Creating new folder in: {base_path}")
        folder_name, ok = QInputDialog.getText(self.main_window, "New Folder", "Enter name for the new folder:")
        if ok and folder_name:
            full_path = os.path.join(base_path, folder_name)
            success, message = self.file_controller.create_folder_in_explorer(full_path)
            if success:
                self.dialog_manager.show_info("Folder Created", message)
                self._handle_refresh_explorer()
            else:
                self.dialog_manager.show_warning(self.main_window.INVALID_NAME_TITLE if "exists" in message.lower() else "Error Creating Folder", message)
        elif ok and not folder_name:
            self.dialog_manager.show_warning(self.main_window.INVALID_NAME_TITLE, "Folder name cannot be empty.")

    def _handle_rename_explorer_item(self, old_item_path: str, current_name: str):
        logger.debug(f"Context menu: Renaming item: {old_item_path}")
        new_name, ok = QInputDialog.getText(self.main_window, f"Rename '{current_name}'", "Enter new name:", text=current_name)
        if ok and new_name:
            if new_name == current_name:
                return # No change
            success, message, _ = self.file_controller.rename_item_in_explorer(old_item_path, new_name)
            if success:
                self.dialog_manager.show_info(self.main_window.RENAME_SUCCESSFUL_TITLE, message)
                self._handle_refresh_explorer()
            else:
                self.dialog_manager.show_warning(self.main_window.RENAME_FAILED_TITLE, message)
        elif ok and not new_name:
            self.dialog_manager.show_warning(self.main_window.INVALID_NAME_TITLE, "New name cannot be empty.")

    def _handle_delete_explorer_item(self, item_path: str, item_name: str, is_dir: bool):
        logger.debug(f"Context menu: Deleting item: {item_path}")
        item_type_str = "folder" if is_dir else "file"
        reply = QMessageBox.question(self.main_window, self.main_window.DELETE_CONFIRM_TITLE, 
                                     f"Are you sure you want to permanently delete the {item_type_str} '{item_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, message = self.file_controller.delete_item_in_explorer(item_path)
            if success:
                self.dialog_manager.show_info(self.main_window.DELETE_SUCCESSFUL_TITLE, message)
                self._handle_refresh_explorer()
            else:
                self.dialog_manager.show_warning(self.main_window.DELETE_FAILED_TITLE, message)

    def _handle_refresh_explorer(self):
        logger.info("Refreshing file explorer tree.")
        if self._current_file_explorer_root_path and os.path.isdir(self._current_file_explorer_root_path):
            self._populate_file_tree_widget(self._current_file_explorer_root_path)
        else:
            logger.warning("Cannot refresh file explorer: No valid root path set or path is not a directory.")
            self.file_tree_widget.clear()

    def on_sidebar_file_activated(self, item: QTreeWidgetItem, _column: int):
        """Handles double-click on an item in the sidebar QTreeWidget."""
        # item is directly passed by the QTreeWidget.itemActivated signal
        if not item:
            logger.warning("on_sidebar_file_activated: No item received from signal.")
            return

        full_path = item.data(0, Qt.UserRole)       # Retrieve full path
        item_type = item.data(0, Qt.UserRole + 1)   # Retrieve item type ('file' or 'directory')

        if not full_path or not item_type:
            logger.warning(f"on_sidebar_file_activated: Item '{item.text(0)}' is missing path or type data.")
            return

        if item_type == "directory":
            logger.debug(f"Directory double-clicked: {full_path}")
            # QTreeWidget handles expand/collapse by default. Custom logic can be added here.
            # item.setExpanded(not item.isExpanded()) # Example: toggle expansion
        elif item_type == "file":
            logger.info(f"File double-clicked from sidebar: {full_path}")
            if full_path.lower().endswith(('.txt', '.md')):
                if hasattr(self.file_controller, 'open_note_from_path'):
                    self.file_controller.open_note_from_path(full_path)
                elif hasattr(self.file_controller, 'open_file'): # Fallback
                    self.file_controller.open_file(full_path)
                else:
                    logger.error("FileController is missing a suitable method (open_note_from_path or open_file) to open the file.")
                    self.dialog_manager.show_critical("Error", "Cannot open file: File controller misconfigured.")
            else:
                logger.warning(f"Attempted to open unsupported file type from sidebar: {full_path}")
                self.dialog_manager.show_warning("Unsupported File Type",
                                    "This file type is not supported for opening in the editor.")
        else:
            logger.warning(f"Unknown item type '{item_type}' activated: {full_path}")

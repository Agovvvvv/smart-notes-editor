#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controller for file operations.
"""

import os
import logging
import shutil
from PyQt5.QtWidgets import QFileDialog, QMessageBox

# Import editor logic
from backend.editor_logic import EditorLogic
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Constants for dialog titles
ERROR_OPENING_FILE_TITLE = "Error Opening File"
ERROR_SAVING_FILE_TITLE = "Error Saving File"
CONFIRM_SAVE_TITLE = "Unsaved Changes"
CONFIRM_SAVE_TEXT = "You have unsaved changes. Do you want to save them?"

class FileController:
    """Controller for file operations."""
    
    def __init__(self, main_window, settings_model, document_model):
        """Initialize the file controller."""
        self.main_window = main_window
        self.settings_model = settings_model
        self.document_model = document_model
        self.editor_logic = EditorLogic()
    
    def new_note(self):
        """Create a new, empty note."""
        if not self._check_unsaved_changes():
            return
            
        self.document_model.clear()
        self.main_window.text_edit.clear()
        self.main_window.setWindowTitle("Untitled - Smart Contextual Notes Editor")
        self.main_window.statusBar.showMessage("New note created")
    
    def open_note(self):
        """Open an existing note file."""
        if not self._check_unsaved_changes():
            return
            
        default_dir = self.settings_model.get("files", "default_save_directory", 
                                         self.editor_logic.get_default_save_directory())
            
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Open Note",
            default_dir,
            "Text Files (*.txt);;Markdown Files (*.md);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            content = self.editor_logic.read_file(file_path)
            self.document_model.set_content(content)
            self.document_model.set_current_file(file_path)
            self.document_model.mark_saved()
            
            self.main_window.text_edit.setText(content)
            self.main_window.setWindowTitle(f"{os.path.basename(file_path)} - Smart Contextual Notes Editor")
            self.main_window.statusBar.showMessage(f"Opened {file_path}")
            
            self.settings_model.add_recent_file(file_path)
            
        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                ERROR_OPENING_FILE_TITLE,
                f"Could not open file: {str(e)}"
            )
    
    def save_note(self):
        """
        Save the current note to a file.
        
        Returns:
            bool: True if the save was successful, False otherwise
        """
        if not self.document_model.get_current_file():
            return self.save_note_as()
            
        try:
            content = self.document_model.get_content()
            self.editor_logic.write_file(self.document_model.get_current_file(), content)
                
            self.document_model.mark_saved()
            self.main_window.setWindowTitle(f"{os.path.basename(self.document_model.get_current_file())} - Smart Contextual Notes Editor")
            self.main_window.statusBar.showMessage(f"Saved to {self.document_model.get_current_file()}")
            
            self.settings_model.add_recent_file(self.document_model.get_current_file())
            
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                ERROR_SAVING_FILE_TITLE,
                f"Could not save file: {str(e)}"
            )
            return False
    
    def save_note_as(self):
        """
        Save the current note to a new file.
        
        Returns:
            bool: True if the save was successful, False otherwise
        """
        default_dir = self.settings_model.get("files", "default_save_directory", 
                                         self.editor_logic.get_default_save_directory())
        
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Save Note As",
            default_dir,
            "Text Files (*.txt);;Markdown Files (*.md);;All Files (*)"
        )
        
        if not file_path:
            return False
            
        # Add appropriate extension if no extension provided
        if not os.path.splitext(file_path)[1]:
            default_ext = self.settings_model.get("files", "default_extension", "txt")
            file_path += f".{default_ext}"
            
        try:
            content = self.document_model.get_content()
            self.editor_logic.write_file(file_path, content)
                
            self.document_model.set_current_file(file_path)
            self.document_model.mark_saved()
            self.main_window.setWindowTitle(f"{os.path.basename(file_path)} - Smart Contextual Notes Editor")
            self.main_window.statusBar.showMessage(f"Saved to {file_path}")
            
            self.settings_model.add_recent_file(file_path)
            
            # Update default save directory
            self.settings_model.set("files", "default_save_directory", os.path.dirname(file_path))
            self.settings_model.save_settings()
            
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                ERROR_SAVING_FILE_TITLE,
                f"Could not save file: {str(e)}"
            )
            return False
    
    def _check_unsaved_changes(self):
        """
        Check if there are unsaved changes and prompt the user to save.
        
        Returns:
            bool: True if it's safe to proceed, False if the operation should be cancelled
        """
        if not self.document_model.unsaved_changes:
            return True
            
        reply = QMessageBox.question(
            self.main_window, 
            CONFIRM_SAVE_TITLE,
            CONFIRM_SAVE_TEXT,
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )
        
        if reply == QMessageBox.Save:
            return self.save_note()
        elif reply == QMessageBox.Cancel:
            return False
        
        # Discard changes
        return True

    # --- Methods for File Explorer Context Menu --- 

    def create_file_in_explorer(self, file_path: str) -> tuple[bool, str]:
        """Wrapper for EditorLogic's create_empty_file for file explorer use."""
        logger.debug(f"FileController attempting to create file: {file_path}")
        success, message = self.editor_logic.create_empty_file(file_path)
        if success:
            logger.info(f"FileController: File created successfully: {file_path}")
        else:
            logger.error(f"FileController: Failed to create file '{file_path}': {message}")
        return success, message

    def create_folder_in_explorer(self, folder_path: str) -> tuple[bool, str]:
        """Wrapper for EditorLogic's create_folder for file explorer use."""
        logger.debug(f"FileController attempting to create folder: {folder_path}")
        success, message = self.editor_logic.create_folder(folder_path)
        if success:
            logger.info(f"FileController: Folder created successfully: {folder_path}")
        else:
            logger.error(f"FileController: Failed to create folder '{folder_path}': {message}")
        return success, message

    def rename_item_in_explorer(self, old_path: str, new_name: str) -> tuple[bool, str, Optional[str]]:
        """Wrapper for EditorLogic's rename_item for file explorer use."""
        logger.debug(f"FileController attempting to rename item: {old_path} to {new_name}")
        success, message, new_path = self.editor_logic.rename_item(old_path, new_name)
        if success:
            logger.info(f"FileController: Item renamed successfully: {old_path} -> {new_path}")
        else:
            logger.error(f"FileController: Failed to rename item '{old_path}' to '{new_name}': {message}")
        return success, message, new_path

    def delete_item_in_explorer(self, item_path: str) -> tuple[bool, str]:
        """Wrapper for EditorLogic's delete_item for file explorer use."""
        logger.debug(f"FileController attempting to delete item: {item_path}")
        success, message = self.editor_logic.delete_item(item_path)
        if success:
            logger.info(f"FileController: Item deleted successfully: {item_path}")
        else:
            logger.error(f"FileController: Failed to delete item '{item_path}': {message}")
        return success, message

    def open_note_from_path(self, file_path: str):
        """Open a note from the given absolute file path."""
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            QMessageBox.warning(
                self.main_window,
                ERROR_OPENING_FILE_TITLE,
                f"File does not exist or is a directory: {file_path}"
            )
            logger.error(f"Attempted to open invalid path: {file_path}")
            return

        if not self._check_unsaved_changes():
            return

        try:
            content = self.editor_logic.read_file(file_path)
            self.document_model.set_content(content)
            self.document_model.set_current_file(file_path)
            self.document_model.mark_saved()
            
            self.main_window.text_edit.setText(content)
            self.main_window.setWindowTitle(f"{os.path.basename(file_path)} - Smart Contextual Notes Editor")
            self.main_window.statusBar.showMessage(f"Opened {file_path}")
            
            self.settings_model.add_recent_file(file_path)
            
        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                ERROR_OPENING_FILE_TITLE,
                f"Could not open file: {str(e)}"
            )
            logger.exception(f"Error opening file {file_path}")

    def create_file(self, file_path: str) -> tuple[bool, str]:
        """Creates a new empty file at the given path.

        Args:
            file_path: The absolute path where the file should be created.

        Returns:
            A tuple (success: bool, message: str).
        """
        if os.path.exists(file_path):
            message = f"File already exists: {file_path}"
            logger.warning(message)
            return False, message
        try:
            # Create parent directories if they don't exist
            parent_dir = os.path.dirname(file_path)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
                logger.info(f"Created parent directory: {parent_dir}")
            
            with open(file_path, 'w') as f:
                f.write('') # Create an empty file
            logger.info(f"Successfully created file: {file_path}")
            return True, f"File created: {file_path}"
        except OSError as e:
            message = f"Failed to create file {file_path}: {e.strerror}"
            logger.error(message, exc_info=True)
            return False, message
        except Exception as e:
            message = f"An unexpected error occurred while creating file {file_path}: {str(e)}"
            logger.error(message, exc_info=True)
            return False, message

    def create_folder(self, folder_path: str) -> tuple[bool, str]:
        """Creates a new folder (and any necessary parent directories) at the given path.

        Args:
            folder_path: The absolute path where the folder should be created.

        Returns:
            A tuple (success: bool, message: str).
        """
        if os.path.exists(folder_path):
            message = f"Folder already exists: {folder_path}"
            logger.warning(message)
            return False, message
        try:
            os.makedirs(folder_path)
            logger.info(f"Successfully created folder: {folder_path}")
            return True, f"Folder created: {folder_path}"
        except OSError as e:
            # Check if it's because the file/folder already exists (though we checked above, race condition possible)
            if e.errno == 17: # EEXIST - File exists
                message = f"Folder already exists (race condition): {folder_path}"
                logger.warning(message)
                return False, message 
            message = f"Failed to create folder {folder_path}: {e.strerror}"
            logger.error(message, exc_info=True)
            return False, message
        except Exception as e:
            message = f"An unexpected error occurred while creating folder {folder_path}: {str(e)}"
            logger.error(message, exc_info=True)
            return False, message

    def rename_item(self, old_path: str, new_path: str) -> tuple[bool, str]:
        """Renames a file or folder.

        Args:
            old_path: The current absolute path of the item.
            new_path: The new absolute path for the item.

        Returns:
            A tuple (success: bool, message: str).
        """
        item_type = "Folder" if os.path.isdir(old_path) else "File"
        try:
            if not os.path.exists(old_path):
                message = f"{item_type} does not exist: {old_path}"
                logger.warning(message)
                return False, message
            
            if os.path.exists(new_path):
                message = f"Target path already exists: {new_path}"
                logger.warning(message)
                return False, message

            os.rename(old_path, new_path)
            logger.info(f"Successfully renamed {old_path} to {new_path}")

            # If the renamed item was the currently open file, update its path
            if self.document_model.get_current_file() == old_path:
                self.document_model.set_current_file(new_path)
                # No need to mark as unsaved, content is the same, just path changed
                # self.document_model.mark_saved() # Ensure it's still considered saved under the new name
                if self.main_window: # Check if main_window is available
                    self.main_window.setWindowTitle(f"{os.path.basename(new_path)} - Smart Contextual Notes Editor")
                    self.main_window.statusBar.showMessage(f"Renamed to {new_path}", 3000)
                logger.info(f"Updated current open file from {old_path} to {new_path}")
            
            # If the renamed item was a folder containing the current file, update path implicitly
            # No, QFileSystemModel handles this. We only care if the direct file path changes.

            return True, f"{item_type} renamed to {os.path.basename(new_path)}"
        except OSError as e:
            message = f"Failed to rename {item_type.lower()} '{os.path.basename(old_path)}': {e.strerror}"
            logger.error(message, exc_info=True)
            return False, message
        except Exception as e:
            message = f"An unexpected error occurred while renaming {item_type.lower()} '{os.path.basename(old_path)}': {str(e)}"
            logger.error(message, exc_info=True)
            return False, message

    def delete_item(self, path: str, is_dir: bool) -> tuple[bool, str]:
        """Deletes a file or folder.

        Args:
            path: The absolute path of the item to delete.
            is_dir: True if the item is a directory, False if it's a file.

        Returns:
            A tuple (success: bool, message: str).
        """
        item_type = "Folder" if is_dir else "File"
        item_name = os.path.basename(path)

        try:
            if not os.path.exists(path):
                message = f"{item_type} '{item_name}' not found."
                logger.warning(message)
                return False, message

            if is_dir:
                shutil.rmtree(path)
                logger.info(f"Successfully deleted folder: {path}")
            else:
                os.remove(path)
                logger.info(f"Successfully deleted file: {path}")
            
            # If the deleted file was the currently open file, DocumentModel's current_file_path
            # will be handled by MainWindow calling new_note. Here we just confirm deletion.
            # However, if a folder containing the current note is deleted, we should also clear the editor.
            current_open_file = self.document_model.get_current_file()
            if current_open_file:
                if is_dir and current_open_file.startswith(os.path.abspath(path) + os.sep):
                    logger.info(f"Folder '{path}' containing current open file '{current_open_file}' was deleted. Editor state managed by MainWindow.")
                elif not is_dir and current_open_file == path:
                    logger.info(f"Deleted file '{path}' was the current open file. Editor state managed by MainWindow.")
 
            return True, f"{item_type} '{item_name}' deleted successfully."
        except OSError as e:
            message = f"Failed to delete {item_type.lower()} '{item_name}': {e.strerror}"
            logger.error(message, exc_info=True)
            return False, message
        except Exception as e:
            message = f"An unexpected error occurred while deleting {item_type.lower()} '{item_name}': {str(e)}"
            logger.error(message, exc_info=True)
            return False, message

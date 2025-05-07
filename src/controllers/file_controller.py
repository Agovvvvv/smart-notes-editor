#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controller for file operations.
"""

import os
import logging
from PyQt5.QtWidgets import QFileDialog, QMessageBox

# Import editor logic
from backend.editor_logic import EditorLogic

logger = logging.getLogger(__name__)

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
                "Error Opening File",
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
                "Error Saving File",
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
                "Error Saving File",
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
            "Unsaved Changes",
            "You have unsaved changes. Do you want to save them?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )
        
        if reply == QMessageBox.Save:
            return self.save_note()
        elif reply == QMessageBox.Cancel:
            return False
        
        # Discard changes
        return True

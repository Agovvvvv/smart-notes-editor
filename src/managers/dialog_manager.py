#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Manager for handling UI dialogs.
"""

import logging
from PyQt5.QtWidgets import QDialog, QInputDialog, QMessageBox, QFileDialog

# Import custom dialogs
from views.dialogs.model_dialog import ModelSelectionDialog
from views.dialogs.ai_services_dialog import AIServicesDialog
from views.dialogs.enhancement_preview_dialog import EnhancementPreviewDialog
from views.dialogs.template_manager_dialog import TemplateManagerDialog

logger = logging.getLogger(__name__)

class DialogManager:
    """Manages the creation and display of various dialogs."""

    def __init__(self, main_window):
        """Initialize the DialogManager."""
        self.main_window = main_window
        self.current_dialog = None # To keep track of a currently open modal dialog if needed

    def show_model_selection_dialog(self, available_models, current_model):
        """Creates and shows the model selection dialog."""
        dialog = ModelSelectionDialog(self.main_window, available_models, current_model)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            return dialog.get_selected_model()
        return None

    def show_ai_services_dialog(self, settings):
        """Creates and shows the AI services configuration dialog."""
        # Ensure only one instance of AIServicesDialog is open if it's non-modal or complex
        # For now, assume modal dialogs are fine to recreate.
        # Corrected argument order for AIServicesDialog constructor
        dialog = AIServicesDialog(settings_model=settings, parent=self.main_window)
        
        # Call exec_() once and store the result
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            logger.info("AI Services configuration accepted.")
        # AIServicesDialog saves settings internally, so we mostly care if it was accepted/cancelled
        return result == QDialog.Accepted

    def show_enhancement_preview_dialog(self, generated_text, original_text, input_tokens=None, max_output_tokens=None):
        """Creates and shows the enhancement preview dialog."""
        dialog = EnhancementPreviewDialog(
            enhanced_text=generated_text, 
            original_text=original_text, 
            estimated_input_tokens=input_tokens, 
            max_output_tokens=max_output_tokens, 
            parent=self.main_window
        )
        # Connect signals if the dialog emits them and DialogManager needs to act as intermediary
        # For example, if regenerate is handled here instead of directly in MainWindow
        # dialog.regenerate_requested.connect(self.main_window._on_enhancement_regenerate_requested)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            return dialog.get_enhanced_text()
        return None
    
    def show_enhancement_suggestions_dialog(self, suggestions: list, title: str = "Select Enhancement Suggestion", label: str = "Choose a suggestion:"):
        """Shows a dialog to select one suggestion from a list using QInputDialog.getItem."""
        if not suggestions:
            logger.warning("show_enhancement_suggestions_dialog called with no suggestions.")
            return None

        item, ok = QInputDialog.getItem(self.main_window, title, label, suggestions, 0, False)
        if ok and item:
            return item
        return None

    def show_template_manager_dialog(self, settings, parent=None):
        """Shows the template manager dialog."""
        actual_parent = parent if parent else self.main_window
        dialog = TemplateManagerDialog(settings, actual_parent)
        result = dialog.exec_()
        # If the dialog returns a selected template directly:
        # if result == QDialog.Accepted and hasattr(dialog, 'get_selected_template_prompt'):
        #     return dialog.get_selected_template_prompt()
        return result # Or just return the result code for now

    def get_text_input(self, title, label, default_text=""):
        """Shows a QInputDialog to get single line text from the user.
        Returns a tuple (text, ok).
        """
        text, ok = QInputDialog.getText(self.main_window, title, label, text=default_text)
        if ok and text: # Ensure text is not empty if ok is True, QInputDialog might allow empty on OK
            return text, True
        return None, ok # Return None for text if not ok or text is empty, but still pass ok status

    def get_multiline_text_input(self, title, label, default_text=""):
        """Shows a QInputDialog to get multi-line text from the user."""
        text, ok = QInputDialog.getMultiLineText(self.main_window, title, label, text=default_text)
        if ok and text:
            return text
        return None

    def get_existing_directory(self, title: str, initial_path: str = ""):
        """Shows a QFileDialog to get an existing directory from the user."""
        folder_path = QFileDialog.getExistingDirectory(
            self.main_window, # parent
            title,           # caption
            initial_path     # directory
        )
        if folder_path: # QFileDialog.getExistingDirectory returns an empty string if cancelled
            return folder_path
        return None

    def show_message_box(self, icon, title, text, informative_text="", buttons=QMessageBox.Ok, default_button=QMessageBox.NoButton):
        """Shows a QMessageBox with the given parameters.

        Args:
            icon (QMessageBox.Icon): e.g., QMessageBox.Information, QMessageBox.Warning, etc.
            title (str): The title of the message box.
            text (str): The main text of the message box.
            informative_text (str, optional): Additional details.
            buttons (QMessageBox.StandardButton, optional): Buttons to display.
            default_button (QMessageBox.StandardButton, optional): Default button.

        Returns:
            QMessageBox.StandardButton: The button that was clicked.
        """
        msg_box = QMessageBox(self.main_window) # Set parent
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        if informative_text:
            msg_box.setInformativeText(informative_text)
        msg_box.setStandardButtons(buttons)
        if default_button != QMessageBox.NoButton:
            msg_box.setDefaultButton(default_button)
        return msg_box.exec_()

    # Convenience methods for common message box types
    def show_information(self, title, text, informative_text=""):
        return self.show_message_box(QMessageBox.Information, title, text, informative_text)

    def show_warning(self, title, text, informative_text=""):
        return self.show_message_box(QMessageBox.Warning, title, text, informative_text)

    def show_critical(self, title, text, informative_text=""):
        return self.show_message_box(QMessageBox.Critical, title, text, informative_text)

    def show_question(self, title, text, informative_text="", buttons=QMessageBox.Yes | QMessageBox.No, default_button=QMessageBox.No):
        return self.show_message_box(QMessageBox.Question, title, text, informative_text, buttons, default_button)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main window for the Smart Contextual Notes Editor.
Contains the UI definition and event handlers.
"""

import os
import logging
import traceback 
from PyQt5.QtWidgets import (
    QMainWindow, QTextEdit, QAction, QMessageBox, 
    QStatusBar, QVBoxLayout, QWidget, QSplitter, 
    QApplication, QToolBar, QFileDialog, QDialog,
    QInputDialog, QDockWidget, QPushButton, QHBoxLayout, QLabel
)
from PyQt5.QtCore import Qt, QThreadPool
from PyQt5.QtGui import QTextCursor, QIcon
from typing import Optional, Tuple # Added Optional and Tuple

# Import models
from models.document_model import DocumentModel

# Import controllers
from controllers.file_controller import FileController
from controllers.ai_controller import AIController
from controllers.context_controller import ContextController

# Import view managers
from managers.panel_manager import PanelManager
from managers.progress_manager import ProgressManager
from managers.enhancement_state_manager import EnhancementStateManager 

# Import dialogs
from views.dialogs.model_dialog import ModelSelectionDialog
from views.dialogs.ai_services_dialog import AIServicesDialog
from views.dialogs.enhancement_preview_dialog import EnhancementPreviewDialog 
from views.dialogs.template_manager_dialog import TemplateManagerDialog
from views.panels.summary_panel import SummaryPanel

# Import UI factory
from .ui_factory import (
    create_file_menu, create_edit_menu, create_ai_tools_menu,
    create_view_menu, create_context_menu_actions,
    populate_toolbar
)

from backend.ai_utils import estimate_tokens 

logger = logging.getLogger(__name__)

# UI String Constants (example - add more as needed)
EMPTY_NOTE_TITLE = "Empty Note" 
NO_TEXT_TO_SUMMARIZE_MESSAGE = "There is no text to summarize."
NOTE_ENHANCEMENT_ERROR_TITLE = "Note Enhancement Error" 
ENHANCEMENT_SEQUENCE_ERROR_TITLE = "Note Enhancement Error" 
NO_SUGGESTIONS_DIALOG_TITLE = "No Suggestions"
NO_SUGGESTIONS_MESSAGE = "No enhancement suggestions were generated."
SUMMARY_ERROR_DIALOG_TITLE = "Summarization Error"
TEXT_GENERATION_ERROR_TITLE = "Text Generation Error"
NOTE_ENHANCEMENT_TITLE = "Enhance Note" 

class MainWindow(QMainWindow):
    """Main application window for the Smart Contextual Notes Editor."""
    APP_TITLE = "Smart Contextual Notes Editor"  
    MSG_NOT_ENOUGH_TEXT = "Not Enough Text"
    MIN_WORDS_FOR_ENHANCEMENT = 5 
    
    def __init__(self, settings=None):
        """Initialize the main window and set up the UI."""
        super().__init__()
        
        # Initialize models
        from utils.settings import Settings 
        self.app_settings = settings if settings else Settings()
        self.document_model = DocumentModel()
        
        # Initialize controllers
        self.file_controller = FileController(self, self.app_settings, self.document_model)
        self.ai_controller = AIController(self, self.app_settings)
        self.context_controller = ContextController(self)
        
        # Initialize view managers
        self.panel_manager = PanelManager(self)
        self.progress_manager = ProgressManager(self)
        self.enhancement_state_manager = EnhancementStateManager(self) 

        # Initialize thread pool for background tasks
        self.thread_pool = QThreadPool()
        logger.info(f"Maximum thread count: {self.thread_pool.maxThreadCount()}")

        # Initialize Summary Panel components (will be set up later)
        self.summary_dock_widget = None
        self.summary_panel_view = None
        self._setup_summary_dock_widget() 

        # Window properties
        self.setWindowTitle(self.APP_TITLE) 
        
        # Set up the UI components
        self._setup_ui()
        
        # Connect all signals
        self._connect_signals()
        
        # Status message
        self.statusBar().setObjectName("MainStatusBar")
        self.statusBar().showMessage("Ready")
        self.progress_manager.setup_progress_bar(self.statusBar()) 

        # Word count label for status bar
        self.word_count_label = QLabel("Words: 0")
        self.word_count_label.setObjectName("WordCountLabel")
        self.statusBar().addPermanentWidget(self.word_count_label)

        self.settings_dialog = None
        self.ai_services_dialog = None
        # Initialize old state flags to prevent AttributeErrors, even if being phased out.
        self._pending_enhancement_data = None
        self._selection_based_enhancement_info = None

    def _connect_signals(self):
        """Connect signals from various components to their respective slots."""
        # Example: self.some_button.clicked.connect(self.on_some_button_clicked)
        # --- File Controller Signals ---
        # self.file_controller.file_opened.connect(self._on_file_opened)
        # self.file_controller.file_saved.connect(self._on_file_saved)
        # self.file_controller.save_error.connect(self._on_save_error)
        # self.file_controller.unsaved_changes_status.connect(self.update_window_title_based_on_save_state)

        # --- AI Controller Signals ---
        # Summarization
        self.ai_controller.summarization_started.connect(self._on_summarization_started)
        self.ai_controller.summarization_progress.connect(self._on_summarization_progress)
        self.ai_controller.summarization_result.connect(self._on_summarization_result)
        self.ai_controller.summarization_error.connect(self._on_summarization_error)
        self.ai_controller.summarization_finished.connect(self._on_summarization_finished)

        # Text Generation
        self.ai_controller.text_generation_started.connect(self._on_text_generation_started)
        self.ai_controller.text_generation_progress.connect(self._on_text_generation_progress)
        self.ai_controller.text_generation_result.connect(self._on_text_generation_result)
        self.ai_controller.text_generation_error.connect(self._on_text_generation_error)
        self.ai_controller.text_generation_finished.connect(self._on_text_generation_finished)

        # Model Preloading
        self.ai_controller.model_preload_result.connect(self._on_model_preload_result)

        # --- Text Edit Signals ---
        if hasattr(self, 'text_edit') and self.text_edit: 
            self.text_edit.textChanged.connect(self._on_text_changed)
            self.text_edit.cursorPositionChanged.connect(self._on_cursor_position_changed)

        # --- Other UI elements (e.g., from menus/toolbars if actions are dynamic) ---
        # Example: self.some_button.clicked.connect(self.on_some_button_clicked)
        # Connections for actions created in ui_factory will be set there or here if actions are attributes of MainWindow


        logger.info("MainWindow signals connected.")

     # --- UI Setup and Helper Methods ---
    def _setup_ui(self):
        """Set up the main UI components.
        """
        logger.debug("Setting up UI")
        # --- Central Widget --- 
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)
        
        # Text Editor
        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("MainTextEdit")
        layout.addWidget(self.text_edit)
        
        # Menu Bar
        menubar = self.menuBar()
        menubar.setObjectName("MainMenuBar")
        create_file_menu(self, menubar)
        create_edit_menu(self, menubar)
        create_ai_tools_menu(self, menubar)
        create_view_menu(self, menubar)
        # create_web_menu(self, menubar) 
        create_context_menu_actions(self, menubar)
        
        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setObjectName("MainToolBar")
        self.addToolBar(toolbar)
        populate_toolbar(self, toolbar)

        # Status Bar (already created by QMainWindow by default)
        self.statusBar().setObjectName("MainStatusBar")

    #
    # AI Summarization Methods
    #
    
    def on_summarize_note(self):
        """Generate a summary of the current note using AI."""
        logger.info("Summarize note action triggered")
        
        # Get the text to summarize
        text = self.text_edit.toPlainText()
        logger.info(f"Text length for summarization: {len(text)} characters, {len(text.split())} words")
        
        # Check if there's enough text to summarize
        if not text or len(text.split()) < 50:
            logger.warning("Not enough text to summarize (less than 50 words)")
            QMessageBox.warning(
                self,
                self.MSG_NOT_ENOUGH_TEXT,
                "Please enter more text to generate a meaningful summary (at least 50 words)."
            )
            return
        
        try:
            # Use the AI controller to summarize the text
            logger.info("Calling ai_controller.summarize_text()")
            self.ai_controller.summarize_text(text)
            logger.info("ai_controller.summarize_text() call completed")
            
        except Exception as e:
            logger.error(f"Exception in on_summarize_note: {str(e)}")
            self.progress_manager.on_operation_error(str(e))
            QMessageBox.critical(
                self,
                SUMMARY_ERROR_DIALOG_TITLE,
                f"An error occurred while preparing for summarization: {str(e)}"
            )
    
    def on_select_model(self):
        """Open the model selection dialog."""
        try:
            # Get available models
            available_models = self.ai_controller.get_available_models()
            current_model = self.ai_controller.get_current_model()
            
            # Create and show the dialog
            dialog = ModelSelectionDialog(self, available_models, current_model)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                # Get the selected model
                selected_model = dialog.get_selected_model()
                if selected_model != self.ai_controller.get_current_model():
                    self.ai_controller.set_current_model(selected_model)
                    self.statusBar().showMessage(f"AI model set to: {selected_model}")
                    
                    # Preload the model in the background
                    self.statusBar().showMessage(f"Loading model {selected_model} in background...")
                    self.ai_controller.preload_model(selected_model)
        
        except ImportError as e:
            QMessageBox.critical(
                self,
                ERROR_DIALOG_TITLE,
                f"The required libraries for AI models are not installed: {str(e)}\n\n"
                "Please install them using: pip install transformers torch"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                ERROR_DIALOG_TITLE,
                f"An error occurred while selecting the model: {str(e)}"
            )
    
    def _on_model_preload_result(self, result, model_name):
        """Handle the model preload result signal."""
        if result:
            self.statusBar().showMessage(f"Model {model_name} loaded successfully")
        else:
            self.statusBar().showMessage(f"Failed to load model {model_name}")
            
            QMessageBox.critical(
                self,
                ERROR_DIALOG_TITLE,
                f"Failed to load model {model_name}. Please check the logs for details."
            )
    
    def insert_summary_at_cursor(self, summary):
        """Insert the summary at the current cursor position."""
        if not summary:
            logger.warning("Attempted to insert an empty summary.")
            QMessageBox.warning(self, "Empty Summary", "The generated summary is empty.")
            return
            
        cursor = self.text_edit.textCursor()
        # Add a bit of spacing if inserting into existing text
        if not cursor.atStart() and not cursor.atEnd():
            cursor.insertText("\n\n")
        cursor.insertText(f"## Summary\n\n{summary}\n\n")
        # QMessageBox.information(self, "Summary Inserted", "The summary has been inserted at the cursor.") 

    def on_generate_note_text(self):
        """Generate new note content based on a prompt using AI."""
        prompt_text, ok = QInputDialog.getText(self, "Generate Note Content", 
                                               "Enter your prompt for the AI:")
        
        if ok and prompt_text:
            logger.info(f"User provided prompt for text generation: '{prompt_text[:50]}...' ") 
            # Call the AI controller's method to generate text.
            try:
                self.ai_controller.request_text_generation(prompt_text, max_new_tokens=250)
                self.statusBar().showMessage("AI is generating text...") 
            except Exception as e:
                logger.error(f"Error triggering text generation: {e}")
                QMessageBox.critical(self, TEXT_GENERATION_ERROR_TITLE, f"Could not start text generation: {e}")
        else:
            logger.info("Text generation cancelled by user or empty prompt.")

    # --- Placeholder AI Text Generation Signal Handlers ---
    def _on_text_generation_started(self):
        """Handle the start of AI text generation."""
        logger.info("AI Text Generation Started.")
        self.progress_manager.start_operation_with_message("Generating text...")
        # self.statusBar().showMessage("AI is generating text...") 

    def _on_text_generation_progress(self, percentage: int):
        """Handle AI text generation progress updates."""
        pass 

    # In class MainWindow:

    def _on_text_generation_result(self, generated_text_result):
        """Handle the successful result of AI text generation."""
        logger.info("Received AI text generation result.") # ADDED LOG
        processed_text = self._validate_and_process_ai_result(generated_text_result)

        if processed_text is None:
            # If an enhancement was in progress, mark it as failed
            if self.enhancement_state_manager.is_active() and self.enhancement_state_manager.get_state() == 'awaiting_enhancement':
                error_msg = "AI returned empty or invalid text."
                self.enhancement_state_manager.enhancement_error(error_msg)
                # No need for QMessageBox here, _validate_and_process_ai_result shows one
            self.progress_manager.hide_progress()
            return

        logger.info(f"AI Text Generation Successful. Received {len(processed_text)} characters.")
        self.progress_manager.on_progress_update(95)
        self.progress_manager.show_message("AI text processing complete.")

        # ---- Check if it's part of an enhancement workflow ----
        if self.enhancement_state_manager.is_active() and self.enhancement_state_manager.get_state() == 'awaiting_enhancement':
            logger.info("Handling result as part of Note Enhancement workflow.")
            self.enhancement_state_manager.enhancement_generated(processed_text)
            logger.debug("State set to 'enhancement_received'. Preparing to show preview dialog...") # ADDED LOG
            self._show_enhancement_preview_dialog() # Show the preview dialog
        else:
            # It's a general text generation request (e.g., from prompt)
            logger.debug("Handling result as general text generation.") # ADDED LOG
            self._handle_general_text_generation_result(processed_text) # Keep this helper

        self.progress_manager.on_progress_update(100)
        # Status message handled within specific handlers or dialog actions
    def _validate_and_process_ai_result(self, generated_text_result):
        """Validate the AI result, process it into a string, handle errors/empty cases.

        Returns:
            str: The validated and processed text string.
            None: If the result is invalid, empty, or processing failed.
        """
        if not generated_text_result:
            logger.warning("AI text generation returned an empty result.")
            self.progress_manager.on_operation_error("AI returned empty text.")
            QMessageBox.warning(self, "AI Result Empty", "The AI returned an empty result. No changes were made.")
            # Clear pending enhancement flag if error occurred during generation resulting in empty text
            if self._pending_enhancement_data is not None:
                self._pending_enhancement_data = None
                logger.debug("Cleared pending enhancement data due to empty result.")
            return None

        processed_text = self._convert_ai_result_to_string(generated_text_result)
        if processed_text is None:
            # Error occurred during conversion, already logged and handled
            # Clear enhancement flag if conversion failed
            if self._pending_enhancement_data is not None:
                self._pending_enhancement_data = None
                logger.debug("Cleared pending enhancement data due to result conversion error.")
            return None

        # Check if processed text is just whitespace after potential conversion
        if not processed_text.strip():
            logger.warning("AI text generation result is empty or whitespace after processing.")
            self.progress_manager.on_operation_error("AI returned empty/whitespace text.")
            QMessageBox.warning(self, "AI Result Empty", "The AI result was empty or contained only whitespace. No changes were made.")
            if self._pending_enhancement_data is not None:
                self._pending_enhancement_data = None
                logger.debug("Cleared pending enhancement data due to empty/whitespace result.")
            return None

        return processed_text

    def _convert_ai_result_to_string(self, result):
        """Attempts to convert various AI result types to a plain string.

        Handles strings, objects with .text attribute, and dicts with 'text' key.
        Logs warnings/errors if conversion is ambiguous or fails.

        Returns:
            str: The processed text string.
            None: If conversion fails.
        """
        if isinstance(result, str):
            return result
        elif hasattr(result, 'text') and isinstance(getattr(result, 'text', None), str):
            logger.debug("AI result has .text attribute, using it.")
            return result.text
        elif isinstance(result, dict) and 'text' in result and isinstance(result['text'], str):
            logger.debug("AI result is dict with 'text' key, using it.")
            return result['text']
        else:
            # Attempt a fallback conversion, logging a warning
            try:
                processed_text = str(result)
                logger.warning(f"AI result type unexpected ({type(result).__name__}). Converted to string: {processed_text[:100]}...")
                return processed_text
            except Exception as e:
                logger.error(f"Failed to convert AI result of type {type(result).__name__} to string: {e}")
                self.progress_manager.on_operation_error(f"Error processing AI result type: {e}")
                QMessageBox.critical(self, "AI Result Error", f"Could not process the AI result type: {type(result).__name__}")
                return None

    def _handle_enhancement_result(self, generated_text: str):
        """Handles the result when it's from the 'Enhance Note' feature.
           Shows the preview dialog for the *first* time or after an error.
        """
        logger.info("Handling result as Note Enhancement (showing initial preview dialog).")
        if self._pending_enhancement_data is None:
            logger.error("_handle_enhancement_result called but _pending_enhancement_data is None. Should not happen here.")
            self.statusBar().showMessage("Enhancement error: State mismatch (initial preview).", 5000)
            self._selection_based_enhancement_info = None 
            self._current_enhancement_dialog = None 
            return

        # Retrieve the full original text for the diff preview
        original_full_text = self._pending_enhancement_data.get('original_text', '')
        was_selection_based = self._selection_based_enhancement_info is not None
        selection_info = self._selection_based_enhancement_info

        # Clear pending *data* flag *before* showing dialog
        # Keep selection info until dialog is closed/accepted
        self._pending_enhancement_data = None 
        logger.debug("Cleared pending enhancement data before showing dialog.")

        # --- Create and show the preview dialog --- 
        dialog = EnhancementPreviewDialog(generated_text, original_full_text, self)
        self._current_enhancement_dialog = dialog 
        # Connect the regeneration signal
        dialog.regenerate_requested.connect(self._on_enhancement_regenerate_requested)
        logger.debug("Connected regenerate_requested signal.")

        result = dialog.exec_()
        logger.info(f"EnhancementPreviewDialog closed with result: {result}")

        # --- Handle dialog result --- 
        # Dialog is closed, clear the reference *regardless* of result
        current_dialog = self._current_enhancement_dialog 
        self._current_enhancement_dialog = None
        logger.debug("Cleared enhancement dialog reference after dialog closed.")

        if result == QDialog.Accepted:
            logger.info("Enhancement accepted by user.")
            accepted_text = current_dialog.get_enhanced_text() 
            if was_selection_based and selection_info:
                logger.info("Applying enhancement to selection.")
                cursor = self.text_edit.textCursor()
                cursor.beginEditBlock() 
                cursor.setPosition(selection_info['start'])
                cursor.setPosition(selection_info['end'], QTextCursor.KeepAnchor)
                cursor.insertText(accepted_text) 
                cursor.endEditBlock()
                # Update model content after modification
                self.document_model.set_content(self.text_edit.toPlainText())
                self.statusBar().showMessage("Selected text enhanced successfully!", 5000)
            else:
                logger.info("Applying enhancement to full note.")
                self.text_edit.setPlainText(accepted_text) 
                # Ensure DocumentModel is updated correctly and signals modification
                self.document_model.set_content(accepted_text) 
                self.statusBar().showMessage("Note enhanced successfully!", 5000)
            logger.info("Note content updated with enhanced text.")
        else: 
            logger.info("Enhancement rejected by user.")
            self.statusBar().showMessage("Enhancement discarded.", 3000)
            # No changes needed to the editor text
        
        # Clear selection info *after* potential use
        self._selection_based_enhancement_info = None
        logger.debug("Cleared selection info after dialog closed.")

    def _handle_general_text_generation_result(self, generated_text: str):
        """Handles the result for general text generation (e.g., from prompt)."""
        logger.info("Handling result as General Text Generation (appending).")
        current_text = self.text_edit.toPlainText()
        # Use a consistent separator
        new_text = current_text + "\n\n--- Generated Content ---\n" + generated_text
        self.text_edit.setPlainText(new_text)
        # Update model and title for generated content as well
        self.document_model.set_content(new_text)
        self.statusBar().showMessage("Generated text added to note.", 5000)
        logger.info("Generated text appended to note.")

    # --- Placeholder AI Text Generation Signal Handlers ---
    def _on_text_generation_error(self, error_details):
        err_type, err_msg, _ = error_details
        logger.error(f"AI Text Generation Error: {err_type}: {err_msg}")

        # Check if this error occurred during an enhancement
        if self.enhancement_state_manager.is_active() and self.enhancement_state_manager.get_state() == 'awaiting_enhancement':
            logger.error("Text generation error occurred during enhancement.")
            self.enhancement_state_manager.enhancement_error(f"{err_type}: {err_msg}")
            # Optionally close any open preview dialog? Handled by state reset usually.
            # self.enhancement_state_manager.reset() # Reset state on error

        self.progress_manager.hide_progress()
        self.statusBar().showMessage("Text generation failed.", 5000)
        QMessageBox.critical(self, TEXT_GENERATION_ERROR_TITLE, f"{err_type}: {err_msg}")
        # Reset enhancement state manager if an error occurred during its active phase
        if self.enhancement_state_manager.get_state() == 'error':
            self.enhancement_state_manager.reset()

    def _on_text_generation_finished(self):
        """Handle the end of AI text generation (success or failure)."""
        logger.info("AI Text Generation Finished.")
        self.progress_manager.hide_progress() 
        # Status message is usually set by result or error handlers

    # --- AI Summarization Signal Handlers ---
    def _on_summarization_started(self):
        """Handle the start of AI text summarization."""
        logger.info("AI Summarization Started.")
        self.progress_manager.start_operation_with_message("Summarizing text...")
        # self.statusBar().showMessage("AI is summarizing text...") 

    def _on_summarization_progress(self, percentage: int):
        """Handle AI text summarization progress updates."""
        pass 

    def _on_summarization_result(self, summary_text: str):
        """Handle the result of AI text summarization."""
        logger.info(f"AI Summarization Result received (first 100 chars): {summary_text[:100]}...")
        self.progress_manager.hide_progress()
        
        if not summary_text.strip():
            self.statusBar().showMessage("Summarization complete: Empty summary.", 5000)
            QMessageBox.information(self, "Summarization Complete", "The generated summary is empty or contains only whitespace.")
            # Ensure panel is cleared even if empty
            if self.summary_panel_view:
                self.summary_panel_view.set_summary("")
            return

        self.statusBar().showMessage("Summarization complete.", 5000)
        # Update the summary panel view
        if self.summary_panel_view:
            self.summary_panel_view.set_summary(summary_text)
            logger.info("Summary panel updated.")
        else:
            logger.warning("Summary panel view not found when trying to set summary.")

        # Show and raise the dock widget
        if self.summary_dock_widget:
            self.summary_dock_widget.setVisible(True)
            self.summary_dock_widget.raise_()
            logger.info("Summary dock widget shown and raised.")
        else:
            logger.warning("Summary dock widget not found when trying to show/raise.")

    def _on_summarization_error(self, error_details: tuple):
        error_type, error_message, tb_str = error_details
        logger.error(f"MainWindow Summarization Error: {error_type.__name__} - {error_message}")
        if tb_str:
            logger.debug(f"Traceback:\n{tb_str}")

        if hasattr(self, 'progress_manager'): 
            self.progress_manager.hide_progress()
        self.statusBar().showMessage("Summarization failed.", 5000)

        QMessageBox.critical(self, SUMMARY_ERROR_DIALOG_TITLE, 
                             f"{error_message}\n\nType: {error_type.__name__}")

    def _on_summarization_finished(self):
        """Handle the end of AI text summarization (success or failure)."""
        logger.info("AI Summarization Finished.")
        self.progress_manager.hide_progress() 
        # Status message is usually set by result or error handlers
    # --- End AI Summarization Signal Handlers ---

    def on_trigger_full_enhancement_pipeline(self):
        """
        Starts the full note enhancement pipeline:
        1. Extracts entities from the current note.
        2. Proceeds to generate enhancement using original text and entities, but no web content.
        """
        logger.info("Full note enhancement pipeline triggered.")
        
        note_text = self.text_edit.toPlainText()
        
        if not note_text or len(note_text.split()) < self.MIN_WORDS_FOR_ENHANCEMENT:
            logger.warning(f"Not enough text to enhance (less than {self.MIN_WORDS_FOR_ENHANCEMENT} words).")
            QMessageBox.warning(
                self,
                self.MSG_NOT_ENOUGH_TEXT,
                f"Please provide at least {self.MIN_WORDS_FOR_ENHANCEMENT} words in your note to start the enhancement process."
            )
            return
            
        # Call the method that sets up the enhancement data and starts the first step
        self.on_start_note_enhancement_workflow() 

    

    def _display_enhancement_suggestions(self, suggestions: list):
        """Display the enhancement suggestions in a dialog."""
        if not suggestions:
            logger.info("No enhancement suggestions to display.")
            QMessageBox.information(self, NO_SUGGESTIONS_DIALOG_TITLE, NO_SUGGESTIONS_MESSAGE)
            return

        logger.info(f"Displaying {len(suggestions)} enhancement suggestions.")
        dialog = EnhancementSuggestionsDialog(suggestions, self)
        dialog.suggestion_accepted.connect(self._insert_enhancement_suggestion)
        dialog.exec_()

    def _insert_enhancement_suggestion(self, suggestion_text: str):
        """Inserts the accepted enhancement suggestion into the text editor."""
        if not suggestion_text:
            logger.warning("Attempted to insert an empty enhancement suggestion.")
            return
        
        # This logic seems tied to the older pipeline's output format.
        # The new approach uses EnhancementPreviewDialog which handles insertion.
        # Consider removing or adapting this if the old pipeline is gone.

        cursor = self.text_edit.textCursor()
        # Add some spacing if not at the start of a line or if there's preceding text on the line
        if not cursor.atBlockStart():
            cursor.insertBlock() 
        # Could format it further, e.g., add a header or quote block
        cursor.insertText(suggestion_text)
        cursor.insertBlock() 

        self.statusBar().showMessage("Enhancement suggestion inserted.", 3000)
        self._on_text_changed() 

    def update_window_title_based_on_save_state(self):
        """Updates the window title based on the current file and save state."""
        base_title = "Smart Notes Editor"
        current_file = self.document_model.get_current_file()
        unsaved_changes = self.document_model.has_unsaved_changes()

        if current_file:
            file_name = os.path.basename(current_file)
            title = f"{'*' if unsaved_changes else ''}{file_name} - {base_title}"
        else:
            title = f"{'*' if unsaved_changes else ''}Untitled - {base_title}"
        self.setWindowTitle(title)

    def update_title(self):
        """Update the window title based on the current file and unsaved changes."""
        base_app_title = self.APP_TITLE 
        if self.document_model.current_file:
            file_name = os.path.basename(self.document_model.current_file)
        else:
            file_name = "Untitled" 
        
        modified_indicator = "*" if self.document_model.unsaved_changes else ""
        
        self.setWindowTitle(f"{file_name}{modified_indicator} - {base_app_title}")
        # logger.debug(f"Window title updated to: {file_name}{modified_indicator} - {base_app_title}")

    def enhance_current_note_with_ai(self):
        """Enhances the current note using AI directly for text generation."""
        current_note_text = self.text_edit.toPlainText()
        if not current_note_text.strip():
            self.update_status_bar("Cannot enhance an empty note.")
            QMessageBox.information(self, "Empty Note", "The note is empty. Please add some text to enhance.")
            return

        self.progress_manager.start_operation_with_message("Enhancing Note...")

        logger.info("Proceeding directly to AI text generation for note enhancement.")
        enhancement_prompt = (
            f"Please enhance the following text by adding relevant information, insights, and details. "
            f"Return the result as plain text, without any markdown formatting. "
            f"If you have access to web information, please use it and cite your sources.\n\n"
            f"Original text:\n\n{current_note_text}"
        )
        
        try:
            # Directly request text generation for enhancement
            self.ai_controller.request_text_generation(prompt_text=enhancement_prompt)
            # Adjusted progress: 50% after sending request, actual generation will take more.
            self.progress_manager.on_progress_update(50) 
            self.progress_manager.show_message("Requesting AI to enhance note...")
            self.update_status_bar("Sent request to AI for note enhancement...")
        except Exception as e:
            logger.error(f"Error requesting AI text generation for enhancement: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "AI Enhancement Error",
                f"Could not start AI enhancement: {e}"
            )
            self.progress_manager.on_operation_error(f"Failed to enhance note: {e}")
            self.update_status_bar("AI enhancement request failed.")

    def update_status_bar(self, message):
        """Update the status bar with a message."""
        self.statusBar().showMessage(message, 5000)

    def _display_enhanced_content(self, enhanced_text):
        """Display the enhanced content."""
        # Insert the enhanced text into the document
        self.text_edit.setPlainText(enhanced_text)
        self.statusBar().showMessage("Enhanced content inserted into the document.")

    # --- NEW Enhancement Handler for Styles --- 
    def _get_enhancement_prompt(self, style: str, text_to_enhance: str, custom_prompt_text: str = None) -> str:
        """Constructs the prompt for the AI based on the enhancement style."""
        base_instruction = "Please enhance the following text:"
        style_modifier = ""

        if style == "clarity":
            style_modifier = " Focus on improving clarity and readability."
        elif style == "concise":
            style_modifier = " Make the text more concise while retaining the core meaning."
        elif style == "expand":
            style_modifier = " Expand on the details and provide more context or information."
        elif style == "custom" or style == "template": # Modified to include 'template'
            if custom_prompt_text:
                # Use the user's custom prompt (or template prompt) directly as the instruction
                base_instruction = custom_prompt_text
                style_modifier = ""
                logger.info(f"Using custom/template enhancement prompt: {style}")
            else:
                # Fallback if custom prompt was somehow empty (should be caught earlier)
                logger.warning(f"{style.capitalize()} enhancement style selected but no prompt provided. Using default.")
                style_modifier = " Add relevant information, insights, and details."
        else: 
             style_modifier = " Add relevant information, insights, and details."

        # Ensure the original text is part of the prompt structure for custom/template prompts
        if style == "custom" or style == "template":
            # Check if original text placeholder is already in the custom_prompt_text
            # A simple heuristic: if 'original text' (case-insensitive) is present, assume user included it.
            # Otherwise, append it.
            if custom_prompt_text and "original text" not in custom_prompt_text.lower() and "{text_to_enhance}" not in custom_prompt_text:
                prompt = f"{base_instruction}\n\nOriginal text:\n---\n{text_to_enhance}\n---"
            else:
                # If placeholder like {text_to_enhance} is used, replace it.
                # Otherwise, assume the custom_prompt_text is complete as is.
                prompt = custom_prompt_text.replace("{text_to_enhance}", text_to_enhance)
        else:
            prompt = f"{base_instruction}{style_modifier}\n\nOriginal text:\n---\n{text_to_enhance}\n---"
        
        logger.debug(f"Constructed enhancement prompt (style: {style}) - First 100 chars: {prompt[:100]}...")
        return prompt

    def on_enhance_note_triggered(self, style: str, custom_prompt_from_template: str = None):
        """Handles the 'Enhance Note' action trigger for different styles."""
        logger.info(f"Enhance Note triggered with style: {style}")

        # 1. Determine text to enhance (selection or full note)
        cursor = self.text_edit.textCursor()
        selected_text = cursor.selectedText()
        original_full_text = self.text_edit.toPlainText()
        
        text_for_prompt_generation = selected_text if selected_text else original_full_text
        is_selection = bool(selected_text)
        selection_info = {'start': cursor.selectionStart(), 'end': cursor.selectionEnd()} if is_selection else None

        # 2. Validate text length (use text_for_prompt_generation)
        if not text_for_prompt_generation or len(text_for_prompt_generation.split()) < self.MIN_WORDS_FOR_ENHANCEMENT:
            logger.warning(f"Not enough text to enhance (less than {self.MIN_WORDS_FOR_ENHANCEMENT} words)")
            QMessageBox.warning(
                self,
                self.MSG_NOT_ENOUGH_TEXT,
                f"Please select or write more text ({self.MIN_WORDS_FOR_ENHANCEMENT} words minimum) to enhance."
            )
            return

        # 3. Handle Custom Prompt Input
        custom_prompt_input = None
        if style == "custom":
            text, ok = QInputDialog.getText(self, 'Custom Enhancement Prompt',
                                            'Enter your enhancement instruction:')
            if ok and text:
                custom_prompt_input = text
                logger.info(f"User provided custom prompt: '{text[:50]}...'" )
            else:
                logger.info("Custom enhancement cancelled by user or empty prompt.")
                self.enhancement_state_manager.reset() # Reset if custom prompt is cancelled
                return 
        elif style == "template":
            if custom_prompt_from_template:
                custom_prompt_input = custom_prompt_from_template
                logger.info("Using prompt from selected template.")
            else:
                # This case should ideally not be reached if on_enhance_from_template_triggered handles it
                logger.error("Template style chosen but no prompt provided from template selection.")
                QMessageBox.critical(self, "Template Error", "No prompt was provided from the selected template.")
                self.enhancement_state_manager.reset()
                return

        # 4. Construct the Prompt using the helper method
        prompt = self._get_enhancement_prompt(style, text_for_prompt_generation, custom_prompt_input)
        if not prompt: # Handle cases where prompt generation might fail (e.g., no style match in helper)
            logger.warning("Enhancement prompt generation failed (e.g., no matching style or cancelled input).")
            self.enhancement_state_manager.reset() # Reset state if we abort
            return

        # 5. Initialize Enhancement State Manager
        logger.debug(f"Before start_enhancement, state: {self.enhancement_state_manager.get_state()}")
        self.enhancement_state_manager.start_enhancement(original_full_text, selection_info)
        logger.debug(f"After start_enhancement, state: {self.enhancement_state_manager.get_state()}")

        logger.debug(f"Before generating_enhancement, state: {self.enhancement_state_manager.get_state()}")
        self.enhancement_state_manager.generating_enhancement(prompt) # Update state to 'awaiting_enhancement'
        logger.debug(f"After generating_enhancement, state: {self.enhancement_state_manager.get_state()}")

        # --- 6. Call AI Controller --- 
        try:
            # Get max_tokens setting using get() and convert manually
            max_tokens_setting = self.app_settings.get('AI', 'max_new_tokens_generation', 2048)
            try:
                max_tokens = int(max_tokens_setting)
            except (ValueError, TypeError):
                logger.warning(f"Invalid value '{max_tokens_setting}' for regeneration. Using default 2048.")
                max_tokens = 2048
            
            self.ai_controller.request_text_generation(prompt, max_new_tokens=max_tokens)
            self.statusBar().showMessage(f"Requesting '{style}' enhancement...", 3000)
            self.progress_manager.start_operation_with_message(f"Requesting AI enhancement ({style})...")
        except Exception as e:
            logger.error(f"Error triggering note enhancement (style: {style}): {e}", exc_info=True)
            QMessageBox.critical(self, NOTE_ENHANCEMENT_ERROR_TITLE, f"Could not start enhancement: {e}")
            self.enhancement_state_manager.enhancement_error(f"Failed to trigger AI: {e}") # Update state
            self.progress_manager.hide_progress()

    # --- Window Event Handlers ---
    def closeEvent(self, event):
        """Handles the window close event, checking for unsaved changes."""
        logger.debug("Close event triggered.")
        if self.document_model.unsaved_changes:
            logger.info("Unsaved changes detected on close.")
            reply = QMessageBox.question(
                self,
                'Unsaved Changes',
                "You have unsaved changes. Do you want to save them before quitting?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Cancel 
            )

            if reply == QMessageBox.Save:
                logger.debug("User chose Save.")
                # Attempt to save. save_file returns True on success, False on failure/cancel.
                if self.file_controller.save_file():
                    logger.info("File saved successfully. Accepting close event.")
                    event.accept()
                else:
                    # Save failed or was cancelled by the user (e.g., in Save As dialog)
                    logger.info("Save operation failed or cancelled. Ignoring close event.")
                    event.ignore()
            elif reply == QMessageBox.Discard:
                logger.info("User chose Discard. Accepting close event.")
                event.accept()
            else: 
                logger.info("User chose Cancel or closed the dialog. Ignoring close event.")
                event.ignore()
        else:
            logger.debug("No unsaved changes. Accepting close event.")
            event.accept() 

    # --- Summary Panel Setup ---
    def _setup_summary_dock_widget(self):
        """Create and configure the dock widget for the summary panel."""
        logger.debug("Setting up summary dock widget.")
        self.summary_dock_widget = QDockWidget("Note Summary", self)
        self.summary_dock_widget.setObjectName("SummaryDockWidget")
        self.summary_panel_view = SummaryPanel(self) # Pass self as parent
        self.summary_dock_widget.setWidget(self.summary_panel_view)
        self.summary_dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.summary_dock_widget.setVisible(False) # Initially hidden
        self.addDockWidget(Qt.RightDockWidgetArea, self.summary_dock_widget)

        # Connect signals from the summary panel view to MainWindow methods
        # Example: self.summary_panel_view.some_signal.connect(self.some_handler)
        # The connection below caused the AttributeError because the signal doesn't exist.
        # The SummaryPanel now calls parent methods directly (e.g., self.parent.insert_summary_at_cursor).
        # self.summary_panel_view.insert_summary_requested.connect(self.insert_summary_at_cursor)

        logger.debug("Summary dock widget setup complete.")

    def _get_token_estimates_for_preview(self, current_text: Optional[str]) -> tuple[Optional[int], Optional[int]]:
        """Helper to get token estimates for the preview dialog."""
        if not self.app_settings.get_ai_backend_is_api():
            return None, None

        estimated_input_tokens = None
        max_output_tokens = None

        if current_text:
            estimated_input_tokens = estimate_tokens(current_text)

        # Try to get max_output_tokens from the parameters of the last AI request
        last_request_params = self.enhancement_state_manager.get_last_request_params()
        if last_request_params:
            # 'max_new_tokens' is commonly used for generation tasks (see memory 3682c2ef...)
            if 'max_new_tokens' in last_request_params:
                max_output_tokens = last_request_params['max_new_tokens']
            elif 'max_output_tokens' in last_request_params: # Fallback for different naming
                max_output_tokens = last_request_params['max_output_tokens']
            # Add other potential keys if necessary

        # If not found in params, use general defaults as a last resort
        if max_output_tokens is None:
            logger.warning("Max output tokens not found in last request params, using general defaults.")
            backend_name = self.app_settings.get("ai", "backend")
            if backend_name == "google_gemini":
                max_output_tokens = 2048 # Default for Gemini (from memory 3682c2ef...)
            elif backend_name == "huggingface_api":
                max_output_tokens = 1024 # General placeholder
            else:
                # For local or unknown, maybe no explicit max output token concept for preview
                pass 

        return estimated_input_tokens, max_output_tokens

    def _show_enhancement_preview_dialog(self):
        """Shows the dialog for previewing, accepting, or refining the AI enhancement."""
        logger.info("Showing enhancement preview dialog.")
        if self.enhancement_state_manager.get_generated_text() is None: # CORRECTED METHOD
            logger.warning("No enhanced text available to preview.")
            QMessageBox.information(self, "No Enhancement", "No enhancement was generated or is available for preview.")
            return

        current_text = self.enhancement_state_manager.get_original_note_text() # CORRECTED METHOD
        enhanced_text = self.enhancement_state_manager.get_generated_text()

        estimated_input_tokens, max_output_tokens = self._get_token_estimates_for_preview(current_text)

        logger.debug(f"Preview Dialog - Input Tokens: {estimated_input_tokens}, Max Output: {max_output_tokens}")

        dialog = EnhancementPreviewDialog(enhanced_text=enhanced_text, 
                                          original_text=current_text, 
                                          estimated_input_tokens=estimated_input_tokens,
                                          max_output_tokens=max_output_tokens,
                                          parent=self)

        # Connect signals FROM the dialog
        dialog.regenerate_requested.connect(self._on_enhancement_regenerate_requested)
        dialog.accepted.connect(self._handle_enhancement_acceptance) # Standard QDialog signal
        dialog.rejected.connect(self._handle_enhancement_rejection)  # Standard QDialog signal
        logger.debug("Connected dialog signals.")

        # No need to call dialog.exec() here, it's handled by how it's shown later
        # or if the calling context expects a modal dialog, that would be `dialog.exec_()`
        # For now, assuming it's shown non-modally or exec_ is called elsewhere.
        # Typically, we'd call dialog.exec_() if we need to block until user interacts.

        if dialog.exec_() == QDialog.Accepted:
            logger.info("Enhancement accepted by user via Preview Dialog's OK button.")
            # The _handle_enhancement_acceptance slot should have already done the work.
        else:
            logger.info("Enhancement rejected or dialog closed by user via Preview Dialog's Cancel/Close button.")
            # The _handle_enhancement_rejection slot should have already done the work.
            # (or self.enhancement_state_manager.reset() if not explicitly handled by rejection)

    def _handle_enhancement_acceptance(self):
        """Handles the acceptance action from the EnhancementPreviewDialog."""
        logger.info("Enhancement accepted by user.")
        # Assumes the dialog is closed right after 'accepted' signal if modal
        # Need to get the final text *before* dialog might be destroyed
        # This requires coordination - maybe dialog passes text via signal?
        # Or we get it from the state manager *before* resetting?

        if self.enhancement_state_manager.get_state() != 'enhancement_received':
            logger.warning("Enhancement accepted in unexpected state: %s", self.enhancement_state_manager.get_state())
            # Don't reset if state is wrong
            return

        accepted_text = self.enhancement_state_manager.get_generated_text() # Get text before state change
        selection_info = self.enhancement_state_manager.get_original_selection_info() # CORRECTED METHOD

        self.enhancement_state_manager.enhancement_accepted() # Update state

        if selection_info:
            logger.info("Applying enhancement to selection.")
            cursor = self.text_edit.textCursor()
            cursor.beginEditBlock() 
            cursor.setPosition(selection_info['start'])
            cursor.setPosition(selection_info['end'], QTextCursor.KeepAnchor)
            cursor.insertText(accepted_text) 
            cursor.endEditBlock()
        else:
            logger.info("Applying enhancement to full note.")
            self.text_edit.setPlainText(accepted_text)

        self.document_model.set_content(self.text_edit.toPlainText()) # Update model
        self.statusBar().showMessage("Note enhanced successfully!", 5000)
        self.enhancement_state_manager.reset() # Reset after successful application

    def _handle_enhancement_rejection(self):
        """Handles the rejection action from the EnhancementPreviewDialog."""
        logger.info("Enhancement rejected by user.")
        if self.enhancement_state_manager.get_state() == 'enhancement_received':
            self.enhancement_state_manager.enhancement_rejected() # Update state
            self.statusBar().showMessage("Enhancement discarded.", 3000)
            self.enhancement_state_manager.reset() # Reset state
        else:
            logger.warning("Enhancement rejected in unexpected state: %s", self.enhancement_state_manager.get_state())

    def _on_enhancement_regenerate_requested(self):
        """Handles the request to regenerate an enhancement from the preview dialog."""
        logger.info("Enhancement regeneration requested by user.")

        # Close the current dialog that emitted the signal
        dialog_instance = self.sender()
        if dialog_instance and isinstance(dialog_instance, QDialog):
            logger.debug("Closing current enhancement preview dialog before regeneration.")
            dialog_instance.accept() # Or done(QDialog.Accepted) - just closes it

        if not self.enhancement_state_manager.is_active() or self.enhancement_state_manager.get_state() != 'enhancement_received':
            logger.warning("Regeneration requested but state is not 'enhancement_received' or not active. Resetting.")
            self.enhancement_state_manager.reset()
            QMessageBox.warning(self, "Regeneration Error", "Cannot regenerate at this moment. Please try starting the enhancement again.")
            return

        original_prompt = self.enhancement_state_manager.enhancement_prompt
        if not original_prompt:
            logger.error("Cannot regenerate: Original prompt not found in state manager.")
            self.enhancement_state_manager.enhancement_error("Original prompt missing for regeneration.")
            QMessageBox.critical(self, NOTE_ENHANCEMENT_ERROR_TITLE, "Could not regenerate: original prompt is missing.")
            return

        logger.info("Proceeding with regeneration using the original prompt.")
        self.enhancement_state_manager.generating_enhancement(original_prompt) # Reset to awaiting_enhancement with same prompt

        try:
            max_tokens_setting = self.app_settings.get('AI', 'max_new_tokens_generation', 2048)
            try:
                max_tokens = int(max_tokens_setting)
            except (ValueError, TypeError):
                logger.warning(f"Invalid value '{max_tokens_setting}' for max_new_tokens_generation. Using default 2048.")
                max_tokens = 2048

            self.ai_controller.request_text_generation(original_prompt, max_new_tokens=max_tokens)
            self.statusBar().showMessage("Regenerating enhancement...", 3000)
            self.progress_manager.start_operation_with_message("Regenerating AI enhancement...")
        except Exception as e:
            logger.error(f"Error triggering note regeneration: {e}", exc_info=True)
            QMessageBox.critical(self, NOTE_ENHANCEMENT_ERROR_TITLE, f"Could not start regeneration: {e}")
            self.enhancement_state_manager.enhancement_error(f"Failed to trigger AI for regeneration: {e}")
            self.progress_manager.hide_progress()

    def _on_enhancement_refine_requested(self):
        """Handles the request to refine an enhancement from the preview dialog."""
        logger.info("Enhancement refinement requested by user.")

        # Close the current dialog that emitted the signal
        dialog_instance = self.sender()
        if dialog_instance and isinstance(dialog_instance, QDialog):
            logger.debug("Closing current enhancement preview dialog before refinement.")
            dialog_instance.accept() # Or done(QDialog.Accepted) - just closes it

        if not self.enhancement_state_manager.is_active() or self.enhancement_state_manager.get_state() != 'enhancement_received':
            logger.warning("Refinement requested but state is not 'enhancement_received' or not active. Resetting.")
            self.enhancement_state_manager.reset()
            QMessageBox.warning(self, "Refinement Error", "Cannot refine at this moment. Please try starting the enhancement again.")
            return

        current_generated_text = self.enhancement_state_manager.get_generated_text()
        original_note_context = self.enhancement_state_manager.get_original_note_text() # Full original text for context
        # Original prompt that led to current_generated_text could also be useful context for the AI
        # prev_prompt = self.enhancement_state_manager.enhancement_prompt 

        if not current_generated_text:
            logger.error("Cannot refine: current generated text not found in state manager.")
            self.enhancement_state_manager.enhancement_error("Current generated text missing for refinement.")
            QMessageBox.critical(self, NOTE_ENHANCEMENT_ERROR_TITLE, "Could not refine: current text is missing.")
            return

        refinement_instructions, ok = QInputDialog.getText(
            self, 
            "Refine Enhancement", 
            "Provide instructions to refine the current enhancement:",
            QLineEdit.Normal,
            "e.g., Make it more formal, focus on the historical aspects, expand on the third point."
        )

        if ok and refinement_instructions:
            logger.info(f"User provided refinement instructions: '{refinement_instructions[:70]}...'" )
            
            # Construct a new prompt for refinement
            # Including original_note_context helps AI remember what the base was.
            # Including current_generated_text shows what it's starting from for this step.
            refinement_prompt = (
                f"You are refining a previously AI-generated text. Please consider the original context, "
                f"the text generated so far, and the user's specific instructions for this refinement pass.\n\n"
                f"## Original Full Note Context:\n---\n{original_note_context}\n---\n\n"
                f"## AI-Generated Text to Refine:\n---\n{current_generated_text}\n---\n\n"
                f"## User's Refinement Instructions:\n---\n{refinement_instructions}\n---\n\n"
                f"Based on all the above, please provide ONLY the new, fully refined version of the 'AI-Generated Text to Refine'."
            )
            
            self.enhancement_state_manager.start_refinement(feedback=refinement_instructions)
            self.enhancement_state_manager.generating_enhancement(prompt=refinement_prompt)

            try:
                max_tokens_setting = self.app_settings.get('AI', 'max_new_tokens_generation', 2048) # Default to a higher value for generation
                try:
                    max_tokens = int(max_tokens_setting)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value '{max_tokens_setting}' for max_new_tokens_generation. Using default 2048.")
                    max_tokens = 2048

                self.ai_controller.request_text_generation(refinement_prompt, max_new_tokens=max_tokens)
                self.statusBar().showMessage("Refining enhancement...", 3000)
                self.progress_manager.start_operation_with_message("Refining AI enhancement based on your feedback...")
            except Exception as e:
                logger.error(f"Error triggering note refinement: {e}", exc_info=True)
                QMessageBox.critical(self, NOTE_ENHANCEMENT_ERROR_TITLE, f"Could not start refinement: {e}")
                self.enhancement_state_manager.enhancement_error(f"Failed to trigger AI for refinement: {e}")
                self.progress_manager.hide_progress()
        else:
            logger.info("Refinement cancelled by user or empty instructions. Resetting state.")
            self.enhancement_state_manager.reset() # Reset if user cancels refinement input
            self.statusBar().showMessage("Refinement cancelled.", 3000)

    def on_manage_enhancement_templates(self):
        """Open the dialog to manage enhancement templates."""
        logger.info("Opening enhancement template manager dialog.")
        try:
            # Pass the app_settings instance to the dialog
            dialog = TemplateManagerDialog(settings=self.app_settings, parent=self)
            dialog.exec_() # Show the dialog modally
            # No specific action needed after close, dialog handles its own saves
        except Exception as e:
            logger.error(f"Error opening template manager dialog: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Could not open template manager: {e}")

    def on_enhance_from_template_triggered(self):
        """Trigger enhancement using a user-selected saved template."""
        logger.info("Enhance from template triggered.")
        templates = self.app_settings.get_enhancement_templates()

        if not templates:
            QMessageBox.information(self, "No Templates", 
                                  "You don't have any saved enhancement templates yet. "
                                  "Please create some via 'AI Tools' -> 'Manage Enhancement Templates...'")
            return

        template_names = list(templates.keys())
        chosen_template_name, ok = QInputDialog.getItem(self, "Select Enhancement Template", 
                                                      "Choose a template:", template_names, 0, False)

        if ok and chosen_template_name:
            chosen_prompt = templates.get(chosen_template_name)
            if chosen_prompt:
                logger.info(f"User selected template: '{chosen_template_name}'")
                # Call the main enhancement trigger with 'template' style and the chosen prompt
                self.on_enhance_note_triggered(style="template", custom_prompt_from_template=chosen_prompt)
            else:
                # Should not happen if templates dict is consistent
                logger.error(f"Selected template '{chosen_template_name}' has no prompt. This is unexpected.")
                QMessageBox.critical(self, "Template Error", f"The selected template '{chosen_template_name}' is empty or corrupted.")
        else:
            logger.info("Template selection cancelled by user.")

    def on_configure_ai_services(self):
        """Opens the AI Services configuration dialog."""
        logger.info("AI Services configuration action triggered.")
        # Pass the main app_settings instance (Settings class) to the dialog
        dialog = AIServicesDialog(self.app_settings, self)
        dialog.exec_() # Show the dialog modally
        logger.info("AI Services configuration dialog closed.")

    # --- End General Helper Methods ---

    def _setup_ui(self):
        """Set up the main UI components."""
        logger.debug("Setting up UI")
        # --- Central Widget --- 
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)
        
        # Text Editor
        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("MainTextEdit")
        layout.addWidget(self.text_edit)
        
        # Menu Bar
        menubar = self.menuBar()
        menubar.setObjectName("MainMenuBar")
        create_file_menu(self, menubar)
        create_edit_menu(self, menubar)
        create_ai_tools_menu(self, menubar)
        create_view_menu(self, menubar)
        # create_web_menu(self, menubar) 
        create_context_menu_actions(self, menubar)
        
        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setObjectName("MainToolBar")
        self.addToolBar(toolbar)
        populate_toolbar(self, toolbar)

        # Status Bar (already created by QMainWindow by default)
        self.statusBar().setObjectName("MainStatusBar")

    def _on_text_changed(self):
        """Handle the textChanged signal from the text editor."""
        # This method is called whenever the text in the editor changes.
        # logger.debug("Text changed") 
        self.document_model.set_content(self.text_edit.toPlainText()) 
        self._update_status_bar_word_count() # Update word count on text change
        # Potentially update UI elements, e.g., enable save action
        if hasattr(self, 'action_save') and self.action_save:
             self.action_save.setEnabled(self.document_model.unsaved_changes) 
        self.update_title() 
        # Auto-save logic could be triggered here after a delay

    def _on_cursor_position_changed(self):
        """Handle the cursorPositionChanged signal from the text editor."""
        # This method is called whenever the cursor position changes.
        # logger.debug("Cursor position changed") 
        # Update status bar with current line/column, or other contextual info
        cursor = self.text_edit.textCursor()
        line_num = cursor.blockNumber() + 1
        col_num = cursor.columnNumber() + 1
        self.statusBar().showMessage(f"Line: {line_num}, Col: {col_num}", 2000) # Show briefly 
        self._update_contextual_actions() 

    def _update_status_bar_word_count(self):
        """Update the word count in the status bar."""
        current_text = self.text_edit.toPlainText()
        if not current_text.strip(): # Handle empty or whitespace-only text
            word_count = 0
        else:
            words = current_text.split() # Simple split by whitespace
            word_count = len(words)
        
        if hasattr(self, 'word_count_label'): # Ensure label exists
            self.word_count_label.setText(f"Words: {word_count}")
        else:
            logger.warning("Word count label not initialized in status bar.")

    def _update_contextual_actions(self):
        """Placeholder: Update contextual actions based on editor state (e.g., selection)."""
        # logger.debug("Updating contextual actions (placeholder).")
        # Example logic (to be expanded):
        has_selection = self.text_edit.textCursor().hasSelection()
        # Example: Enable/disable actions based on selection
        if hasattr(self, 'action_cut'): self.action_cut.setEnabled(has_selection)
        if hasattr(self, 'action_copy'): self.action_copy.setEnabled(has_selection)
        if hasattr(self, 'action_search_selected'): self.action_search_selected.setEnabled(has_selection)
        # Add more actions as needed

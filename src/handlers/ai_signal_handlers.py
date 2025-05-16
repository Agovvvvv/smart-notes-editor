#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contains signal handlers for AI operations, decoupled from MainWindow.
"""

import logging
from PyQt5.QtWidgets import QMessageBox # For potential direct use, or through dialog_manager
from PyQt5.QtCore import pyqtSignal

# Assuming these managers/controllers are passed or accessible
from managers.progress_manager import ProgressManager
from managers.dialog_manager import DialogManager
from managers.enhancement_state_manager import EnhancementStateManager
from views.panels.summary_panel import SummaryPanel # For summary_panel_view
from PyQt5.QtWidgets import QTextEdit # For text_edit

logger = logging.getLogger(__name__)

class AISignalHandler:
    """Handles signals emitted by AIController and updates the UI accordingly."""

    # --- Signals for MainWindow to connect to --- 
    # Emitted when text generation result is processed and ready for enhancement workflow
    enhancement_text_ready = pyqtSignal(str)
    # Emitted when text generation result is processed and ready for general insertion
    general_text_ready = pyqtSignal(str)
    # Emitted when _validate_and_process_ai_result fails
    text_generation_process_failed = pyqtSignal(str)
    # Emitted when _on_text_generation_error occurs, for MainWindow to handle UI specifics
    text_generation_ui_error_needed = pyqtSignal(str, str) # error_type_str, error_message

    def __init__(self, main_window):
        """
        Initialize the AI Signal Handler.

        Args:
            main_window: The main window instance, providing access to UI elements
                         and managers like progress_manager, dialog_manager, etc.
        """
        self.main_window = main_window
        # Direct access to components for convenience, consider passing them individually
        # for stricter decoupling in a future refactor if needed.
        self.progress_manager = main_window.progress_manager
        self.dialog_manager = main_window.dialog_manager
        self.enhancement_state_manager = main_window.enhancement_state_manager
        self.text_edit = main_window.text_edit
        self.summary_panel_view = main_window.summary_panel_view
        self.summary_dock_widget = main_window.summary_dock_widget
        self.settings = main_window.settings # For accessing settings like model names etc.

        logger.info("AISignalHandler initialized.")

    # --- AI Summarization Signal Handlers ---
    def _on_summarization_started(self):
        """Handle the start of AI text summarization."""
        logger.info("AI Summarization Started (Handler).")
        self.progress_manager.start_operation_with_message("Summarizing text...")
        # self.main_window.statusBar().showMessage("AI is summarizing text...") 

    def _on_summarization_progress(self, percentage: int):
        """Handle AI text summarization progress updates."""
        # This method is currently a pass-through in MainWindow, keeping it similar.
        pass 

    def _on_summarization_result(self, summary_text: str):
        """Handle the result of AI text summarization."""
        logger.info(f"AI Summarization Result received by handler (first 100 chars): {summary_text[:100]}...")
        self.progress_manager.hide_progress()
        
        if not summary_text.strip():
            self.main_window.statusBar().showMessage("Summarization complete: Empty summary.", 5000)
            self.dialog_manager.show_information("Summarization Complete", "The generated summary is empty or contains only whitespace.")
            # Ensure panel is cleared even if empty
            if self.summary_panel_view:
                self.summary_panel_view.set_summary("")
            return

        self.main_window.statusBar().showMessage("Summarization complete.", 5000)
        # Update the summary panel view
        if self.summary_panel_view:
            self.summary_panel_view.set_summary(summary_text)
            logger.info("Summary panel updated by handler.")
        else:
            logger.warning("Summary panel view not found in handler when trying to set summary.")

        # Show and raise the dock widget
        if self.summary_dock_widget:
            self.summary_dock_widget.setVisible(True)
            self.summary_dock_widget.raise_()
            logger.info("Summary dock widget shown and raised by handler.")
        else:
            logger.warning("Summary dock widget not found in handler when trying to show/raise.")

    def _on_summarization_error(self, error_details: tuple):
        error_type, error_message, tb_str = error_details
        logger.error(f"Handler Summarization Error: {error_type.__name__} - {error_message}")
        if tb_str:
            logger.debug(f"""Traceback (handler):
{tb_str}""")

        if hasattr(self, 'progress_manager'): 
            self.progress_manager.hide_progress()
        self.main_window.statusBar().showMessage("Summarization failed.", 5000)

        self.dialog_manager.show_critical(
            "Summarization Error", 
            f"""{error_message}

Type: {error_type.__name__}"""
        )

    def _on_summarization_finished(self):
        """Handle the end of AI text summarization (success or failure)."""
        logger.info("AI Summarization Finished (Handler).")
        self.progress_manager.hide_progress() 
        # Status message is usually set by result or error handlers

    # --- AI Text Generation Signal Handlers --- 
    def _on_text_generation_started(self):
        """Handle the start of AI text generation."""
        logger.info("AI Text Generation Started (Handler).")
        self.progress_manager.start_operation_with_message("Generating text...")
        # self.main_window.statusBar().showMessage("AI is generating text...") 

    def _on_text_generation_progress(self, percentage: int):
        """Handle AI text generation progress updates."""
        # Currently, no detailed progress for text generation, but hook is here.
        pass

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
                # self.progress_manager.on_operation_error(f"Error processing AI result type: {e}") # Done by caller
                # self.dialog_manager.show_critical("AI Result Error", f"Could not process the AI result type: {type(result).__name__}") # Done by caller
                return None

    def _validate_and_process_ai_result(self, generated_text_result):
        """Validate the AI result, process it into a string, handle errors/empty cases.
        
        Emits `text_generation_process_failed` if validation fails.
        
        Returns:
            str: The validated and processed text string.
            None: If the result is invalid, empty, or processing failed.
        """
        if not generated_text_result:
            logger.warning("AI text generation returned an empty result.")
            self.progress_manager.on_operation_error("AI returned empty text.")
            self.text_generation_process_failed.emit("The AI returned an empty result. No changes were made.")
            return None

        processed_text = self._convert_ai_result_to_string(generated_text_result)
        if processed_text is None:
            # Error occurred during conversion, _convert_ai_result_to_string logs it.
            self.progress_manager.on_operation_error("Error processing AI result type.")
            self.text_generation_process_failed.emit(f"Could not process the AI result type: {type(generated_text_result).__name__}")
            return None

        if not processed_text.strip():
            logger.warning("AI text generation result is empty or whitespace after processing.")
            self.progress_manager.on_operation_error("AI returned empty/whitespace text.")
            self.text_generation_process_failed.emit("The AI result was empty or contained only whitespace. No changes were made.")
            return None

        return processed_text

    def _on_text_generation_result(self, generated_text_result):
        """Handle the successful result of AI text generation."""
        logger.info("Handler received AI text generation result.")
        processed_text = self._validate_and_process_ai_result(generated_text_result)
        
        if processed_text is None:
            # Validation/processing failed, and appropriate signal already emitted by helper.
            # Progress manager also updated by helper.
            # MainWindow will handle dialogs if needed via text_generation_process_failed signal.
            logger.info("Text validation/processing failed, MainWindow will handle UI from signal.")
            self.progress_manager.hide_progress() # Ensure progress is hidden
            return

        logger.info(f"AI Text Generation Successful (Handler). Received {len(processed_text)} characters.")
        self.progress_manager.on_progress_update(95) # Nearing completion
        self.progress_manager.show_message("AI text processing complete.")
        
        # Check if it's part of an enhancement workflow
        if self.enhancement_state_manager.is_active() and \
           self.enhancement_state_manager.get_state() == 'awaiting_enhancement':
            logger.info("Handling result as part of Note Enhancement workflow (Handler emitting enhancement_text_ready).")
            self.enhancement_text_ready.emit(processed_text)
        else:
            logger.info("Handling result as general text generation (Handler emitting general_text_ready).")
            self.general_text_ready.emit(processed_text)
        
        self.progress_manager.on_progress_update(100)
        # Status message will be handled by MainWindow's slots

    def _on_text_generation_error(self, error_details):
        """Handle errors from AI text generation."""
        # error_details is expected to be a tuple (type, message, traceback_str)
        err_type, err_msg, tb_str = error_details
        err_type_str = err_type.__name__ if err_type else "UnknownError"
        
        logger.error(f"AI Text Generation Error (Handler): {err_type_str}: {err_msg}")
        if tb_str:
            logger.debug(f"Traceback (handler for text gen error):\n{tb_str}")

        self.progress_manager.hide_progress()
        self.main_window.statusBar().showMessage("Text generation failed.", 5000)
        
        # Emit a signal for MainWindow to handle UI specifics like dialogs and state manager checks
        self.text_generation_ui_error_needed.emit(err_type_str, str(err_msg))

    def _on_text_generation_finished(self):
        """Handle the end of AI text generation (success or failure)."""
        logger.info("AI Text Generation Finished (Handler).")
        self.progress_manager.hide_progress()
        # Status message is usually set by result or error handlers, or MainWindow slots

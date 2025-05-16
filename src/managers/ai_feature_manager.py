#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Manages the UI-level orchestration of AI features, acting as an intermediary
between MainWindow, AIController, and various UI components/managers.
"""

import logging
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QTextCursor # Added for text insertion

# Forward declarations or type hints if needed for components passed from MainWindow
# from PyQt5.QtWidgets import QTextEdit, QStatusBar
# from views.panels.summary_panel import SummaryPanel
# from models.document_model import DocumentModel
# from managers.dialog_manager import DialogManager
# from managers.progress_manager import ProgressManager
# from managers.enhancement_state_manager import EnhancementStateManager
# from controllers.ai_controller import AIController
# from utils.settings import Settings

logger = logging.getLogger(__name__)

EMPTY_SUMMARY_DIALOG_TITLE = "Empty Summary"
EMPTY_SUMMARY_DIALOG_MESSAGE = "The summary text is empty and cannot be inserted."

class AIFeatureManager(QObject):
    """Orchestrates AI features, handling UI interactions and responses."""

    def __init__(self, main_window, ai_controller, settings, parent=None):
        """
        Initialize the AIFeatureManager.

        Args:
            main_window: The main window instance, providing access to UI elements
                         and other managers.
            ai_controller: The AIController instance for triggering AI tasks.
            settings: The application settings instance.
            parent: Optional QObject parent.
        """
        super().__init__(parent)

        self.main_window = main_window  # Keep a reference if broad access is needed, or pass specific components
        self.ai_controller = ai_controller
        self.settings = settings

        # UI components and other managers will be accessed via self.main_window.<attribute>
        # e.g., self.main_window.text_edit, self.main_window.dialog_manager

        self._connect_ai_controller_signals()

        logger.info("AIFeatureManager initialized.")

    def _connect_ai_controller_signals(self):
        """Connect signals from AIController to slots in this manager."""
        # Summarization signals
        self.ai_controller.summarization_started.connect(self._on_summarization_started)
        self.ai_controller.summarization_progress.connect(self._on_summarization_progress) # May not be used if progress is simple start/finish
        self.ai_controller.summarization_result.connect(self._on_summarization_result)
        self.ai_controller.summarization_error.connect(self.on_summarization_error_slot) # Renamed for clarity
        self.ai_controller.summarization_finished.connect(self._on_summarization_finished)

        # Text Generation signals
        self.ai_controller.text_generation_started.connect(self._on_text_generation_started)
        self.ai_controller.text_generation_progress.connect(self._on_text_generation_progress) # May not be used
        self.ai_controller.text_generation_result.connect(self._on_text_generation_result)
        self.ai_controller.text_generation_error.connect(self.on_text_generation_error_slot) # Renamed for clarity
        self.ai_controller.text_generation_finished.connect(self._on_text_generation_finished)
        
        # Model Preloading signals (if AIController emits them directly, or via AIManager->AIController)
        # Assuming AIController will have these signals if they are to be handled here.
        # self.ai_controller.model_preload_result.connect(self._on_model_preload_result_slot)
        # self.ai_controller.model_preload_error.connect(self._on_model_preload_error_slot)

        # Entity Extraction signals (if needed for features managed here)
        # self.ai_controller.entities_extracted.connect(self._on_entities_extracted_slot)
        # self.ai_controller.entity_extraction_error.connect(self._on_entity_extraction_error_slot)

        # Model Preloading signals from AIController
        self.ai_controller.model_preload_result.connect(self._on_model_preload_result_slot)
        self.ai_controller.model_preload_error.connect(self._on_model_preload_error_slot)

        logger.info("AIFeatureManager connected to AIController signals.")

    # --- Constants ---
    MIN_WORDS_FOR_SUMMARY = 50
    MSG_NOT_ENOUGH_TEXT_TITLE = "Not Enough Text"
    SUMMARY_ERROR_DIALOG_TITLE = "Summarization Error"
    MODEL_ERROR_DIALOG_TITLE = "AI Model Error" # For model selection/loading issues
    TEXT_GENERATION_ERROR_TITLE = "Text Generation Error"

    # --- Slot Methods --- 

    # Summarization Slots
    def _on_summarization_started(self):
        """Handle the start of AI text summarization."""
        logger.info("AI Summarization Started.")
        self.main_window.progress_manager.start_operation_with_message("Summarizing text...")
        self.main_window.statusBar().showMessage("AI is summarizing text...", 3000) # Show for 3 seconds

    def _on_summarization_progress(self, percentage: int):
        """Handle AI text summarization progress updates."""
        # Currently, AIManager/AIController might not emit detailed progress for summarization.
        # If it does, this is where self.main_window.progress_manager.update_progress(percentage) would go.
        logger.debug(f"Summarization progress: {percentage}%")
        # self.main_window.progress_manager.update_progress(percentage) # Example

    def _on_summarization_result(self, summary_text: str):
        """Handle the result of AI text summarization."""
        logger.info(f"AI Summarization Result received (first 100 chars): {summary_text[:100]}...")
        self.main_window.progress_manager.hide_progress()
        
        if not summary_text.strip():
            self.main_window.statusBar().showMessage("Summarization complete: Empty summary.", 5000)
            self.main_window.dialog_manager.show_information(
                "Summarization Complete", 
                "The generated summary is empty or contains only whitespace."
            )
            if self.main_window.summary_panel_view:
                self.main_window.summary_panel_view.set_summary("")
            return

        self.main_window.statusBar().showMessage("Summarization complete.", 5000)
        if self.main_window.summary_panel_view:
            self.main_window.summary_panel_view.set_summary(summary_text)
            logger.info("Summary panel updated.")
        else:
            logger.warning("Summary panel view not found when trying to set summary.")

        if self.main_window.summary_dock_widget: # Access via main_window reference
            self.main_window.summary_dock_widget.setVisible(True)
            self.main_window.summary_dock_widget.raise_()
            logger.info("Summary dock widget shown and raised.")
        else:
            logger.warning("Summary dock widget not found when trying to show/raise.")

    def on_summarization_error_slot(self, error_details: tuple):
        """Handle errors from AI text summarization."""
        error_type, error_message, tb_str = error_details
        error_type_name = error_type.__name__ if error_type else "UnknownError"
        logger.error(f"Summarization Error: {error_type_name} - {error_message}")
        if tb_str:
            logger.debug(f"Traceback for summarization error:\n{tb_str}")

        self.main_window.progress_manager.hide_progress()
        self.main_window.statusBar().showMessage("Summarization failed.", 5000)

        self.main_window.dialog_manager.show_critical(
            self.SUMMARY_ERROR_DIALOG_TITLE,
            f"{error_message}\n\nType: {error_type_name}"
        )

    def _on_summarization_finished(self):
        """Handle the end of AI text summarization (success or failure)."""
        logger.info("AI Summarization Finished.")
        self.main_window.progress_manager.hide_progress()
        # Status message is usually set by result or error handlers, no need to clear here unless desired.

    # Text Generation Slots
    def _on_text_generation_started(self):
        logger.info("AIFeatureManager: AI text generation started.")
        self.main_window.progress_manager.show_progress("AI is generating text...")

    def _on_text_generation_progress(self, percentage: int):
        logger.debug(f"AIFeatureManager: AI text generation progress: {percentage}%")
        self.main_window.progress_manager.update_progress(percentage)

    def _on_text_generation_result(self, generated_text_result):
        logger.info("AIFeatureManager: Received text generation result.")
        processed_text = self._validate_and_process_ai_result(generated_text_result)

        if processed_text:
            # Check if an enhancement workflow is active
            if self.main_window.enhancement_state_manager.is_active() and \
               self.main_window.enhancement_state_manager.get_state() in ['awaiting_enhancement', 'generating_enhancement']:
                # This will be handled by the enhancement workflow refactoring (Phase 2)
                # For now, let EnhancementStateManager know text is ready.
                logger.info("Text generation result received during an active enhancement workflow.")
                self.main_window.enhancement_state_manager.enhancement_generated(processed_text)
                # The enhancement workflow (e.g., _show_enhancement_preview_dialog in MainWindow) will take over.
            else:
                self._handle_general_text_generation_result_internal(processed_text)
        else:
            logger.warning("AIFeatureManager: Text generation result was invalid or empty after processing.")
            # Error messages already shown by _validate_and_process_ai_result

    def on_text_generation_error_slot(self, error_details: tuple):
        err_type, err_msg, _ = error_details
        logger.error(f"AIFeatureManager: AI Text Generation Error: {err_type}: {err_msg}")

        # Check if this error occurred during an enhancement
        if self.main_window.enhancement_state_manager.is_active() and \
           self.main_window.enhancement_state_manager.get_state() in ['awaiting_enhancement', 'generating_enhancement']:
            logger.error("Text generation error occurred during enhancement.")
            self.main_window.enhancement_state_manager.enhancement_error(f"{err_type}: {err_msg}")

        self.main_window.progress_manager.hide_progress()
        self.main_window.statusBar().showMessage("Text generation failed.", 5000)
        self.main_window.dialog_manager.show_critical(self.TEXT_GENERATION_ERROR_TITLE, f"{err_type}: {err_msg}")
        
        if self.main_window.enhancement_state_manager.get_state() == 'error':
            self.main_window.enhancement_state_manager.reset()

    def _on_text_generation_finished(self):
        logger.info("AIFeatureManager: AI Text Generation Finished.")
        self.main_window.progress_manager.hide_progress()
        
    # --- Feature Trigger Methods ---
    def trigger_summarization(self):
        """User action to generate a summary of the current note."""
        logger.info("Summarize note action triggered in AIFeatureManager")
        
        text_to_summarize = self.main_window.text_edit.toPlainText()
        word_count = len(text_to_summarize.split())
        logger.info(f"Text length for summarization: {len(text_to_summarize)} characters, {word_count} words")
        
        if not text_to_summarize or word_count < self.MIN_WORDS_FOR_SUMMARY:
            logger.warning(f"Not enough text to summarize (words: {word_count}, required: {self.MIN_WORDS_FOR_SUMMARY})")
            self.main_window.dialog_manager.show_warning(
                self.MSG_NOT_ENOUGH_TEXT_TITLE,
                f"Please enter more text to generate a meaningful summary (at least {self.MIN_WORDS_FOR_SUMMARY} words)."
            )
            return
        
        try:
            logger.info("Calling ai_controller.summarize_text()")
            self.ai_controller.summarize_text(text_to_summarize)
            logger.info("ai_controller.summarize_text() call dispatched")
        except Exception as e:
            logger.error(f"Exception in trigger_summarization before calling AIController: {str(e)}", exc_info=True)
            self.main_window.progress_manager.on_operation_error(str(e)) # Should ideally be caught by AIController's error signal
            self.main_window.dialog_manager.show_critical(
                self.SUMMARY_ERROR_DIALOG_TITLE,
                f"An unexpected error occurred while preparing for summarization: {str(e)}"
            )
            # Ensure progress is hidden if an early exception occurs
            self.main_window.progress_manager.hide_progress()
        
    def trigger_text_generation(self):
        """Requests user for a prompt and triggers AI text generation."""
        prompt_text, ok = self.main_window.dialog_manager.get_text_input(
            "Generate Note Content",
            "Enter your prompt for the AI:"
        )
        
        if ok and prompt_text:
            logger.info(f"User provided prompt for text generation: '{prompt_text[:50]}...' ")
            try:
                # Using default max_new_tokens from AIController or settings if needed
                self.ai_controller.request_text_generation(prompt_text) 
                self.main_window.statusBar().showMessage("AI is generating text...", 3000)
            except Exception as e:
                logger.error(f"Error triggering text generation: {e}", exc_info=True)
                self.main_window.dialog_manager.show_critical(self.TEXT_GENERATION_ERROR_TITLE, f"Could not start text generation: {e}")
        else:
            logger.info("Text generation cancelled by user or empty prompt.")
        
    def trigger_note_enhancement(self, style: str, custom_prompt_from_template: str = None):
        # Logic from MainWindow.on_enhance_note_triggered()
        pass
        
    def trigger_model_selection(self):
        """Opens the model selection dialog and handles model changes."""
        try:
            available_models = self.ai_controller.get_available_models()
            current_model = self.ai_controller.get_current_model()
            
            selected_model = self.main_window.dialog_manager.show_model_selection_dialog(available_models, current_model)
            
            if selected_model and selected_model != self.ai_controller.get_current_model():
                self.ai_controller.set_current_model(selected_model)
                self.main_window.statusBar().showMessage(f"AI model set to: {selected_model}", 3000)
                self.main_window.statusBar().showMessage(f"Loading model {selected_model} in background...", 3000) # Temporary message
                self.ai_controller.preload_model(selected_model)
        except ImportError as e:
            logger.error(f"ImportError during model selection: {e}", exc_info=True)
            self.main_window.dialog_manager.show_critical(
                self.MODEL_ERROR_DIALOG_TITLE,
                f"The required libraries for AI models are not installed: {str(e)}\n\n"
                f"Please install them (e.g., using pip install transformers torch)."
            )
        except Exception as e:
            logger.error(f"Exception during model selection: {e}", exc_info=True)
            self.main_window.dialog_manager.show_critical(
                self.MODEL_ERROR_DIALOG_TITLE,
                f"An error occurred while selecting the model: {str(e)}"
            )
        
    # --- Placeholder for Result Handling/Helper Methods (to be migrated) ---
    def _insert_summary_at_cursor(self, summary: str):
        # Logic from MainWindow.insert_summary_at_cursor()
        pass

    # _convert_ai_result_to_string and _validate_and_process_ai_result will be internal helpers
    # called by _on_text_generation_result, migrated from AISignalHandler.

    # _handle_enhancement_result and _handle_general_text_generation_result
    # will be internal methods called by _on_text_generation_result based on enhancement_state_manager.

    # _on_model_preload_result_slot and its error counterpart if preloading is handled here.

    def _format_summary_for_insertion(self, summary: str) -> str:
        """Helper method to format the summary text for editor insertion."""
        return f"\n\n## Summary\n\n{summary}\n\n"

    def insert_summary_into_editor(self, summary: str):
        """Insert the given summary text at the current cursor position in the main text editor."""
        if not summary:
            logger.warning("Attempted to insert an empty summary into editor.")
            self.main_window.dialog_manager.show_warning(EMPTY_SUMMARY_DIALOG_TITLE, EMPTY_SUMMARY_DIALOG_MESSAGE)
            return
            
        cursor = self.main_window.text_edit.textCursor()
        formatted_summary = self._format_summary_for_insertion(summary)
        if not cursor.atBlockStart() and not formatted_summary.startswith('\n\n'):
            cursor.insertText("\n\n")
        
        cursor.insertText(formatted_summary.lstrip('\n')) 
        logger.info("Summary inserted at cursor in text editor.")

    def insert_summary_at_top(self, summary: str):
        """Insert the given summary text at the top of the main text editor."""
        if not summary:
            logger.warning("Attempted to insert an empty summary at top.")
            self.main_window.dialog_manager.show_warning(EMPTY_SUMMARY_DIALOG_TITLE, EMPTY_SUMMARY_DIALOG_MESSAGE)
            return

        cursor = self.main_window.text_edit.textCursor()
        cursor.movePosition(QTextCursor.Start)
        formatted_summary = self._format_summary_for_insertion(summary)
        cursor.insertText(formatted_summary.lstrip('\n')) 
        logger.info("Summary inserted at the top of the text editor.")

    def insert_summary_at_bottom(self, summary: str):
        """Insert the given summary text at the bottom of the main text editor."""
        if not summary:
            logger.warning("Attempted to insert an empty summary at bottom.")
            self.main_window.dialog_manager.show_warning(EMPTY_SUMMARY_DIALOG_TITLE, EMPTY_SUMMARY_DIALOG_MESSAGE)
            return

        cursor = self.main_window.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        formatted_summary = self._format_summary_for_insertion(summary)
        if not self.main_window.text_edit.toPlainText().endswith('\n\n') and self.main_window.text_edit.toPlainText():
             cursor.insertText("\n\n")
        cursor.insertText(formatted_summary.lstrip('\n'))
        logger.info("Summary inserted at the bottom of the text editor.")

    # --- Model Preloading Slots ---
    def _on_model_preload_result_slot(self, success: bool, model_name: str):
        """Handles the result of AI model preloading."""
        if success:
            self.main_window.statusBar().showMessage(f"Model '{model_name}' loaded successfully.", 5000)
            logger.info(f"Model '{model_name}' preloaded successfully.")
        else:
            # Error message might have been shown by preload_model itself or specific error signal
            self.main_window.statusBar().showMessage(f"Failed to load model '{model_name}'.", 5000)
            logger.error(f"Failed to preload model '{model_name}'.")
            # Dialog might be redundant if preload_model or its error signal shows one.
            # self.main_window.dialog_manager.show_critical(
            #     self.MODEL_ERROR_DIALOG_TITLE,
            #     f"Failed to load model '{model_name}'. Check logs for details."
            # )

    def _on_model_preload_error_slot(self, error_details: tuple):
        """Handles errors from AI model preloading."""
        err_type, err_msg, _ = error_details
        model_name_info = "Unknown model" # Try to get model name if possible from error or context
        logger.error(f"Error preloading model ({model_name_info}): {err_type} - {err_msg}")
        self.main_window.statusBar().showMessage(f"Error loading model: {err_msg}", 5000)
        self.main_window.dialog_manager.show_critical(self.MODEL_ERROR_DIALOG_TITLE, f"Error loading model: {err_msg}")

    # --- Text Processing Utilities (Moved from MainWindow) ---
    def _validate_and_process_ai_result(self, generated_text_result):
        """Validate the AI result, process it into a string, handle errors/empty cases."""
        if not generated_text_result:
            logger.warning("AI text generation returned an empty result.")
            # Progress manager assumed to be handled by caller or finish signal
            self.main_window.dialog_manager.show_warning("AI Result Empty", "The AI returned an empty result. No changes were made.")
            return None

        processed_text = self._convert_ai_result_to_string(generated_text_result)
        if processed_text is None:
            # Error occurred during conversion, already logged and handled by _convert_ai_result_to_string
            return None

        if not processed_text.strip():
            logger.warning("AI text generation result is empty or whitespace after processing.")
            self.main_window.dialog_manager.show_warning("AI Result Empty", "The AI result was empty or contained only whitespace. No changes were made.")
            return None
        return processed_text

    def _convert_ai_result_to_string(self, result):
        """Attempts to convert various AI result types to a plain string."""
        if isinstance(result, str):
            return result
        elif hasattr(result, 'text') and isinstance(getattr(result, 'text', None), str):
            logger.debug("AI result has .text attribute, using it.")
            return result.text
        elif isinstance(result, dict) and 'text' in result and isinstance(result['text'], str):
            logger.debug("AI result is dict with 'text' key, using it.")
            return result['text']
        else:
            try:
                processed_text = str(result)
                logger.warning(f"AI result type unexpected ({type(result).__name__}). Converted to string: {processed_text[:100]}...")
                return processed_text
            except Exception as e:
                logger.error(f"Failed to convert AI result of type {type(result).__name__} to string: {e}", exc_info=True)
                # self.main_window.progress_manager.on_operation_error(f"Error processing AI result type: {e}") # Caller handles progress
                self.main_window.dialog_manager.show_critical("AI Result Error", f"Could not process the AI result type: {type(result).__name__}")
                return None

    def _handle_general_text_generation_result_internal(self, generated_text: str):
        """Handles the result for general text generation (e.g., from prompt)."""
        logger.info("Handling result as General Text Generation (appending)." )
        # Use a consistent separator or append at cursor
        # For simplicity, appending like old AISignalHandler's example:
        # new_text = current_text + "\n\n--- Generated Content ---\n" + generated_text
        # self.main_window.text_edit.setPlainText(new_text)

        # Insert at cursor for better UX
        cursor = self.main_window.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText("--- Generated Content ---")
        cursor.insertBlock()
        cursor.insertText(generated_text)
        cursor.insertBlock() # Extra newline after generated content

        self.main_window.document_model.set_content(self.main_window.text_edit.toPlainText())
        self.main_window.statusBar().showMessage("Generated text added to note.", 5000)
        logger.info("Generated text appended to note.")


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controller for AI summarization operations.
"""

import logging
import sys
import traceback
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool

# Import AI utilities
from utils.threads import WorkerSignals, EntityExtractionWorker

logger = logging.getLogger(__name__)

_AICONTR_ERROR_AIMANAGER_NOT_INIT = "AIManager not initialized"

class AIController(QObject):
    """Controller for AI summarization operations."""
    
    # Define signals for summarization
    summarization_started = pyqtSignal()
    summarization_progress = pyqtSignal(int)
    summarization_result = pyqtSignal(str)
    summarization_error = pyqtSignal(tuple)
    summarization_finished = pyqtSignal()

    # Define signals for text generation
    text_generation_started = pyqtSignal()
    text_generation_progress = pyqtSignal(int)
    text_generation_result = pyqtSignal(str)
    text_generation_error = pyqtSignal(tuple)
    text_generation_finished = pyqtSignal()
    
    # Define signals for Enhance Notes feature
    # Entity Extraction
    entity_extraction_started = pyqtSignal()
    entities_extracted = pyqtSignal(list)
    entity_extraction_error = pyqtSignal(tuple)
    entity_extraction_finished = pyqtSignal()

    # Generic Question Answering (if different from enhancement Q&A)
    question_answering_started = pyqtSignal()
    answer_found = pyqtSignal(str, float) # answer_text, score
    question_answering_error = pyqtSignal(tuple)
    question_answering_finished = pyqtSignal()

    # Web Content Summarization
    web_content_summarization_started = pyqtSignal()
    web_summary_ready = pyqtSignal(str)
    web_content_summarization_error = pyqtSignal(tuple)
    web_content_summarization_finished = pyqtSignal()

    model_preload_result = pyqtSignal(bool, str)
    model_preload_error = pyqtSignal(tuple)
    
    def __init__(self, main_window, settings_model):
        """Initialize the AI controller."""
        super().__init__()
        self.main_window = main_window
        self.settings_model = settings_model
        self.thread_pool = QThreadPool()
        
        # Import AI manager here to avoid circular imports
        from managers.ai_manager import AIManager
        self.ai_manager = AIManager(self, self.settings_model)
        
        # Connect AI manager signals
        self._connect_ai_manager_signals()

    # --- Public Methods to Trigger AI Operations ---
    def summarize_text(self, text: str):
        """Request text summarization from the AI Manager."""
        logger.info("AIController: summarize_text called.")
        if hasattr(self, 'ai_manager') and self.ai_manager:
            self.ai_manager.summarize_text(text)
        else:
            logger.error(f"AIController: AIManager not available for summarization. {_AICONTR_ERROR_AIMANAGER_NOT_INIT}")
            self.summarization_error.emit((type(AttributeError(_AICONTR_ERROR_AIMANAGER_NOT_INIT)), AttributeError(_AICONTR_ERROR_AIMANAGER_NOT_INIT), None))

    def request_text_generation(self, prompt_text: str, max_new_tokens: int = 2048):
        """Request text generation from the AI Manager."""
        logger.info("AIController: request_text_generation called.")
        if hasattr(self, 'ai_manager') and self.ai_manager:
            self.ai_manager.generate_text(prompt_text, max_new_tokens)
        else:
            logger.error(f"AIController: AIManager not available for text generation. {_AICONTR_ERROR_AIMANAGER_NOT_INIT}")
            self.text_generation_error.emit((type(AttributeError(_AICONTR_ERROR_AIMANAGER_NOT_INIT)), AttributeError(_AICONTR_ERROR_AIMANAGER_NOT_INIT), None))

    def extract_entities(self, text: str):
        """Request entity extraction from the AI Manager."""
        logger.info("AIController: extract_entities called.")
        if hasattr(self, 'ai_manager') and self.ai_manager:
            self.ai_manager.extract_entities(text)
        else:
            self.entity_extraction_error.emit((_AICONTR_ERROR_AIMANAGER_NOT_INIT, "AIManager not available for entity extraction."))
            logger.error(_AICONTR_ERROR_AIMANAGER_NOT_INIT)

    # --- AI Manager Signal Handlers ---
    def _connect_ai_manager_signals(self):
        """Connect signals from AIManager to AIController's handlers."""
        if not hasattr(self, 'ai_manager') or self.ai_manager is None:
            logger.error("AIController: AIManager not initialized before connecting signals.")
            return

        # Summarization signals
        self.ai_manager.summarization_started_signal.connect(self._handle_task_started_status) # Generic handler
        self.ai_manager.summarization_progress_signal.connect(self.summarization_progress) # Direct pass-through
        self.ai_manager.summarization_result_signal.connect(self._handle_summarization_result)
        self.ai_manager.summarization_error_signal.connect(self._handle_summarization_error)
        self.ai_manager.summarization_finished_signal.connect(self.summarization_finished) # Direct pass-through

        # Text Generation signals
        self.ai_manager.text_generation_started_signal.connect(self._handle_task_started_status) # Generic handler
        self.ai_manager.text_generation_progress_signal.connect(self.text_generation_progress) # Direct pass-through
        self.ai_manager.text_generation_result_signal.connect(self._handle_text_generation_result)
        self.ai_manager.text_generation_error_signal.connect(self._handle_text_generation_error)
        self.ai_manager.text_generation_finished_signal.connect(self.text_generation_finished) # Direct pass-through
        
        # Entity Extraction signals
        self.ai_manager.entity_extraction_started_signal.connect(self.entity_extraction_started.emit)
        self.ai_manager.entity_extraction_result_signal.connect(self.entities_extracted.emit)
        self.ai_manager.entity_extraction_error_signal.connect(self.entity_extraction_error.emit)
        self.ai_manager.entity_extraction_finished_signal.connect(self.entity_extraction_finished.emit)

        # General error signal from AIManager (e.g., config issues)
        self.ai_manager.general_error_signal.connect(self._handle_ai_manager_general_error)

    @pyqtSlot(str)  # result_text
    def _handle_summarization_result(self, result_text: str):
        logger.info("AIController: Received summarization result.")
        self.summarization_result.emit(result_text)
        self.summarization_finished.emit()

    @pyqtSlot(tuple)  # error_tuple (e.g., (type, value, tb_str))
    def _handle_summarization_error(self, error_tuple: tuple):
        error_type = error_tuple[0] if len(error_tuple) > 0 else Exception
        error_message = str(error_tuple[1]) if len(error_tuple) > 1 else str(error_type)
        tb_str = error_tuple[2] if len(error_tuple) > 2 else ""
        
        logger.error(f"AIController: Received summarization error: {error_message}")
        # Emit a 3-tuple: (Exception Type, Formatted Message, Traceback String)
        self.summarization_error.emit((error_type, f"Summarization Failed: {error_message}", tb_str))
        self.summarization_finished.emit()

    @pyqtSlot(str)  # generated_text
    def _handle_text_generation_result(self, generated_text: str):
        logger.info("AIController: Received text generation result.")
        self.text_generation_result.emit(generated_text)
        self.text_generation_finished.emit()

    @pyqtSlot(tuple)  # error_tuple (e.g., (type, value, tb_str))
    def _handle_text_generation_error(self, error_tuple: tuple):
        error_message = str(error_tuple[1]) if len(error_tuple) > 1 else str(error_tuple[0])
        logger.error("AIController: Received text generation error: " + error_message)
        # Ensure the full error details (type, message, traceback) are propagated
        if len(error_tuple) == 3:
            self.text_generation_error.emit(error_tuple)
        elif len(error_tuple) == 2:
            # If AIManager sent a 2-tuple, adapt it. Preferable to fix AIManager.
            logger.warning("AIController: Received 2-tuple error from AIManager. Adapting to 3-tuple with None traceback.")
            self.text_generation_error.emit((error_tuple[0], error_tuple[1], None))
        else:
            # Fallback for unexpected tuple size
            logger.error(f"AIController: Received unexpected error_tuple size: {len(error_tuple)}. Emitting generic error.")
            self.text_generation_error.emit((RuntimeError, "Unknown error structure from AIManager", None))
        self.text_generation_finished.emit()

    @pyqtSlot() # Connected to summarization_started_signal and text_generation_started_signal
    def _handle_task_started_status(self):
        # Determine which task started if necessary, or use a generic message
        # For now, a generic log. Could be enhanced to show specific task type.
        sender_signal_name = self.sender().objectName() if self.sender() else "UnknownSignal"
        
        if "summarization" in sender_signal_name:
            task_name = "Summarization"
        elif "generation" in sender_signal_name:
            task_name = "Text Generation"
        else:
            task_name = "AI Task"
            
        status_message = task_name + " started by AIManager."
        logger.info("AIController: AIManager status update: " + status_message)
        # Emit a general status signal or update UI if needed
        # Example: self.main_window.show_status_message(status_message)

    @pyqtSlot(str)  # error_message
    def _handle_ai_manager_general_error(self, error_message: str):
        logger.error("AIController: Received general error from AIManager: " + error_message)
        # Potentially show this in a dialog via MainWindow
        if hasattr(self.main_window, 'show_error_message'):
            self.main_window.show_error_message("AI System Error", error_message)
        else:
            # Fallback if main_window doesn't have show_error_message
            self.text_generation_error.emit(("AI System Error", error_message)) 

    def request_enhancement_suggestions(self, note_content: str):
        """Request suggestions for enhancing the note content."""
        logger.info(f"Requesting enhancement suggestions for note (first 50 chars): {note_content[:50]}...")
        # TODO: Implement the logic to call AIManager for enhancement suggestions.
        # This might involve generating prompts based on note_content and entities (if available).
        # For now, emitting an error or a placeholder signal.
        if hasattr(self, 'enhancement_error'): # Check if enhancement_error signal exists
            self.enhancement_error.emit({
                'error': 'Enhancement suggestion feature not fully implemented yet.', 
                'details': 'AIController.request_enhancement_suggestions needs to be built out.'
            })
        else:
            logger.warning("Enhancement error signal not defined, cannot emit 'not implemented' error.")

    # --- Model Management ---

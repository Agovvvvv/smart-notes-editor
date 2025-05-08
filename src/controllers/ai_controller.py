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
from utils.threads import WorkerSignals

logger = logging.getLogger(__name__)

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
    
    def _connect_ai_manager_signals(self):
        """Set up callback methods for the AI manager."""
        # Connect AIManager's summarization signals to AIController's handlers
        self.ai_manager.summarization_started_signal.connect(self._on_summarization_started)
        self.ai_manager.summarization_progress_signal.connect(self._on_summarization_progress)
        self.ai_manager.summarization_result_signal.connect(self._on_summarization_result)
        self.ai_manager.summarization_error_signal.connect(self._on_summarization_error)
        self.ai_manager.summarization_finished_signal.connect(self._on_summarization_finished)

        # Connect AIManager's text generation signals to AIController's new internal handlers
        self.ai_manager.text_generation_started_signal.connect(self._on_manager_text_generation_started)
        self.ai_manager.text_generation_progress_signal.connect(self._on_manager_text_generation_progress)
        self.ai_manager.text_generation_result_signal.connect(self._on_manager_text_generation_result)
        self.ai_manager.text_generation_error_signal.connect(self._on_manager_text_generation_error)
        self.ai_manager.text_generation_finished_signal.connect(self._on_manager_text_generation_finished)
        
    def _on_summarization_started(self):
        """Handle summarization started event from AIManager."""
        logger.info("AIController: Summarization started, emitting own signal.")
        self.summarization_started.emit()
        
    def _on_summarization_progress(self, progress):
        """Handle summarization progress event from AIManager."""
        logger.info(f"AIController: Summarization progress {progress}%, emitting own signal.")
        self.summarization_progress.emit(progress)
        
    def _on_summarization_result(self, result):
        """Handle summarization result event from AIManager."""
        logger.info(f"AIController: Summarization result received, emitting own signal.")
        self.summarization_result.emit(result)
        
    def _on_summarization_error(self, error_info):
        """Handle summarization error event from AIManager."""
        logger.info("AIController: Summarization error, emitting own signal.")
        self.summarization_error.emit(error_info)
        
    def _on_summarization_finished(self):
        """Handle summarization finished event from AIManager."""
        logger.info("AIController: Summarization finished, emitting own signal.")
        self.summarization_finished.emit()

    # --- Internal Handlers for AIManager's Text Generation Signals ---
    def _on_manager_text_generation_started(self):
        logger.info("AIController: Text generation started from AIManager, emitting own signal.")
        self.text_generation_started.emit()

    def _on_manager_text_generation_progress(self, percentage: int):
        logger.info(f"AIController: Text generation progress {percentage}% from AIManager, emitting own signal.")
        self.text_generation_progress.emit(percentage)

    def _on_manager_text_generation_result(self, generated_text: str):
        logger.info("AIController: Text generation result from AIManager, emitting own signal.")
        self.text_generation_result.emit(generated_text)

    def _on_manager_text_generation_error(self, error_details: tuple):
        logger.info("AIController: Text generation error from AIManager, emitting own signal.")
        self.text_generation_error.emit(error_details)

    def _on_manager_text_generation_finished(self):
        logger.info("AIController: Text generation finished from AIManager, emitting own signal.")
        self.text_generation_finished.emit()
        
    def _on_model_preload_result(self, result, model_name):
        """Handle model preload result event."""
        self.model_preload_result.emit(result, model_name)
        
    def _on_model_preload_error(self, error_info):
        """Handle model preload error event."""
        self.model_preload_error.emit(error_info)
    
    def summarize_text(self, text):
        """
        Generate a summary of the provided text using AI.
        
        Args:
            text (str): The text to summarize
        """
        logger.info(f"AIController.summarize_text called with text length: {len(text)}")
        try:
            logger.info("Calling ai_manager.summarize_text")
            self.ai_manager.summarize_text(text)
            logger.info("ai_manager.summarize_text call completed (this should be immediate since it's async)")
        except Exception as e:
            logger.error(f"Exception in AIController.summarize_text: {str(e)}")
            error_info = (type(e), e, traceback.format_exc())
            logger.info("Emitting summarization_error signal")
            self.summarization_error.emit(error_info)
            logger.info("Emitting summarization_finished signal")
            self.summarization_finished.emit()
    
    def request_text_generation(self, prompt_text: str, max_new_tokens: int = 250):
        """
        Request text generation from the AI Manager.

        Args:
            prompt_text (str): The prompt to generate text from.
            max_new_tokens (int): The maximum number of new tokens to generate.
        """
        logger.info(f"AIController.request_text_generation called with prompt: '{prompt_text[:50]}...' and max_new_tokens: {max_new_tokens}")
        try:
            self.ai_manager.generate_note_text(prompt_text, max_new_tokens=max_new_tokens)
        except Exception as e:
            logger.error(f"Exception in AIController.request_text_generation: {str(e)}")
            error_info = (type(e), e, traceback.format_exc())
            self.text_generation_error.emit(error_info)
            self.text_generation_finished.emit() # Ensure finished is emitted on error too

    def get_current_model(self):
        """Get the current AI model."""
        return self.ai_manager.get_current_model()
    
    def set_current_model(self, model_name):
        """Set the current AI model."""
        self.ai_manager.set_current_model(model_name)
    
    def preload_model(self, model_name):
        """Preload an AI model in the background."""
        self.ai_manager.preload_model(model_name)
    
    def get_available_models(self):
        """Get a list of available AI models."""
        try:
            # This part would need to be reimplemented if we want to list API models
            # For now, it returns a default or relies on settings dialog
            # For example, could return models specified in settings:
            # summarization_model = self.settings_model.get("ai", "huggingface_summarization_model_id", "facebook/bart-large-cnn")
            # generation_model = self.settings_model.get("ai", "huggingface_text_generation_model_id", "gpt2")
            # return [summarization_model, generation_model]
            logger.warning("AIController.get_available_models() is returning a placeholder. Needs review for API context.")
            return ["default"] # Placeholder
        except ImportError:
            logger.error("Required libraries for AI models are not installed")
            return ["default"]
        except Exception as e:
            logger.error(f"Error getting available models: {str(e)}")
            return ["default"]

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
from backend.ai_utils import get_available_models, get_current_model
from utils.threads import WorkerSignals

logger = logging.getLogger(__name__)

class AIController(QObject):
    """Controller for AI summarization operations."""
    
    # Define signals
    summarization_started = pyqtSignal()
    summarization_progress = pyqtSignal(int)
    summarization_result = pyqtSignal(str)
    summarization_error = pyqtSignal(tuple)
    summarization_finished = pyqtSignal()
    
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
        self.ai_manager = AIManager(self.main_window, self.settings_model)
        
        # Connect AI manager signals
        self._connect_ai_manager_signals()
    
    def _connect_ai_manager_signals(self):
        """Set up callback methods for the AI manager."""
        # The AIManager doesn't use signals directly, but calls methods on its parent
        # We'll define these methods to emit our controller signals
        
    def _on_summarization_started(self):
        """Handle summarization started event."""
        self.summarization_started.emit()
        
    def _on_summarization_progress(self, progress):
        """Handle summarization progress event."""
        self.summarization_progress.emit(progress)
        
    def _on_summarization_result(self, result):
        """Handle summarization result event."""
        self.summarization_result.emit(result)
        
    def _on_summarization_error(self, error_info):
        """Handle summarization error event."""
        self.summarization_error.emit(error_info)
        
    def _on_summarization_finished(self):
        """Handle summarization finished event."""
        self.summarization_finished.emit()
        
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
        try:
            self.ai_manager.summarize_text(text)
        except Exception as e:
            error_info = (type(e), e, traceback.format_exc())
            self.summarization_error.emit(error_info)
            self.summarization_finished.emit()
    
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
            return get_available_models()
        except ImportError:
            logger.error("Required libraries for AI models are not installed")
            return ["default"]
        except Exception as e:
            logger.error(f"Error getting available models: {str(e)}")
            return ["default"]

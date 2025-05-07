#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controller for context analysis operations.
"""

import logging
import traceback
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class ContextController(QObject):
    """Controller for context analysis operations."""
    
    # Define signals
    context_analysis_started = pyqtSignal()
    context_analysis_progress = pyqtSignal(int)
    context_analysis_error = pyqtSignal(str)
    context_analysis_finished = pyqtSignal()
    suggestions_ready = pyqtSignal(dict)
    
    def __init__(self, main_window):
        """Initialize the context controller."""
        super().__init__()
        self.main_window = main_window
        
        # Import context manager here to avoid circular imports
        from managers.context_manager import ContextManager
        self.context_manager = ContextManager(self.main_window)
        
        # Store the current suggestions
        self.current_suggestions = {}
        
        # Connect context manager signals
        self._connect_context_manager_signals()
    
    def _connect_context_manager_signals(self):
        """Set up callback methods for the context manager."""
        # The ContextManager doesn't use these signals directly, but calls methods on its parent
        # We'll connect to the signals that do exist
        self.context_manager.progress_signal.connect(self._on_progress)
        self.context_manager.error_signal.connect(self._on_error)
        self.context_manager.suggestions_ready_signal.connect(self._on_suggestions_ready)
        self.context_manager.models_loaded_signal.connect(self._on_models_loaded)
    
    def _on_suggestions_ready(self, suggestions):
        """
        Handle the suggestions ready signal from the context manager.
        
        Args:
            suggestions (dict): The generated suggestions
        """
        # Store the suggestions
        self.current_suggestions = suggestions
        
        # Emit the signals
        self.suggestions_ready.emit(suggestions)
        self.context_analysis_finished.emit()
        
    def _on_progress(self, progress):
        """
        Handle the progress signal from the context manager.
        
        Args:
            progress (int): The progress percentage
        """
        self.context_analysis_progress.emit(progress)
        
    def _on_error(self, error_msg):
        """
        Handle the error signal from the context manager.
        
        Args:
            error_msg (str): The error message
        """
        self.context_analysis_error.emit(error_msg)
        self.context_analysis_finished.emit()
        
    def _on_models_loaded(self, success):
        """
        Handle the models loaded signal from the context manager.
        
        Args:
            success (bool): Whether the models were loaded successfully
        """
        if success and self.current_suggestions:
            # If models were loaded successfully and we have pending analysis, run it now
            self.analyze_context(self.context_manager.current_note_text, self.context_manager.current_web_results)
    
    def analyze_context(self, note_text, web_results):
        """
        Analyze the context of the note and web results.
        
        Args:
            note_text (str): The text of the note
            web_results (list): The web search results
        """
        # Emit the started signal
        self.context_analysis_started.emit()
        
        try:
            # Call the manager to analyze the context
            self.context_manager.analyze_context(note_text, web_results)
            
            # The manager will call our callback methods, which will emit the appropriate signals
            # We don't emit the finished signal here because it will be emitted by the callbacks
            
        except Exception as e:
            error_info = str(e)
            self.context_analysis_error.emit(error_info)
            self.context_analysis_finished.emit()
    
    def get_current_suggestions(self):
        """
        Get the current suggestions.
        
        Returns:
            dict: The current suggestions
        """
        return self.current_suggestions

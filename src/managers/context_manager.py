#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Context manager for the Smart Contextual Notes Editor.
Manages the context analysis and suggestions generation process.
"""

import logging
from PyQt5.QtCore import QObject, pyqtSignal, QThread

# Import our modules
from backend import context_analyzer
from utils.threads import Worker

logger = logging.getLogger(__name__)

class ContextManager(QObject):
    """Manager for context analysis and suggestions generation."""
    
    # Signals
    models_loaded_signal = pyqtSignal(bool)
    suggestions_ready_signal = pyqtSignal(dict)
    progress_signal = pyqtSignal(int)
    error_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize the context manager."""
        super().__init__(parent)
        
        # Store the parent for callbacks
        self.parent = parent
        
        # Initialize state variables
        self.models_loaded = False
        self.current_note_text = ""
        self.current_suggestions = {}
        
        # Initialize worker thread
        self.worker_thread = None
    
    def load_models(self):
        """Load the context analysis models in a background thread."""
        if self.models_loaded:
            logger.info("Context models already loaded")
            self.models_loaded_signal.emit(True)
            return
        
        # Create a worker thread
        self.worker_thread = QThread()
        worker = Worker(self._load_models_worker)
        worker.moveToThread(self.worker_thread)
        
        # Connect signals
        worker.signals.result.connect(self._on_models_loaded)
        worker.signals.error.connect(self._on_error)
        worker.signals.progress.connect(self._on_progress)
        worker.signals.finished.connect(self.worker_thread.quit)
        
        # Start the thread
        self.worker_thread.started.connect(worker.run)
        self.worker_thread.start()
    
    def _load_models_worker(self, progress_callback):
        """Worker function to load models."""
        return context_analyzer.initialize_context_models(progress_callback)
    
    def _on_models_loaded(self, success):
        """Handle models loaded signal."""
        self.models_loaded = success
        self.models_loaded_signal.emit(success)
        
        if success:
            logger.info("Context analysis models loaded successfully")
        else:
            logger.error("Failed to load context analysis models")
    
    def analyze_context(self, note_text):
        """
        Analyze the context of the note to generate suggestions.
        
        Args:
            note_text (str): The text of the note
        """
        # Store the current note
        self.current_note_text = note_text
        
        # Check if models are loaded
        if not self.models_loaded:
            logger.info("Context models not loaded, loading now...")
            self.load_models()
            # The suggestions will be generated after models are loaded
            return
        
        # Create a worker thread
        self.worker_thread = QThread()
        worker = Worker(self._analyze_context_worker, note_text)
        worker.moveToThread(self.worker_thread)
        
        # Connect signals
        worker.signals.result.connect(self._on_suggestions_ready)
        worker.signals.error.connect(self._on_error)
        worker.signals.progress.connect(self._on_progress)
        worker.signals.finished.connect(self.worker_thread.quit)
        
        # Start the thread
        self.worker_thread.started.connect(worker.run)
        self.worker_thread.start()
    
    def _analyze_context_worker(self, note_text, progress_callback):
        """Worker function to analyze context and generate suggestions."""
        return context_analyzer.generate_suggestions(note_text, progress_callback)
    
    def _on_suggestions_ready(self, suggestions):
        """Handle suggestions ready signal."""
        self.current_suggestions = suggestions
        self.suggestions_ready_signal.emit(suggestions)
        logger.info("Context suggestions generated successfully")
    
    def _on_error(self, error):
        """Handle error signal."""
        self.error_signal.emit(str(error))
        logger.error(f"Error in context manager: {str(error)}")
    
    def _on_progress(self, progress):
        """Handle progress signal."""
        self.progress_signal.emit(progress)
    
    def get_current_suggestions(self):
        """Get the current suggestions."""
        return self.current_suggestions

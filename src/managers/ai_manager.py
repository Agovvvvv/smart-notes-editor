#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI manager for the Smart Contextual Notes Editor.
Handles AI operations like summarization and model management.
"""

import logging
from PyQt5.QtCore import QObject, QThreadPool

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIManager(QObject):
    """Manager for AI operations."""
    
    def __init__(self, parent=None, settings=None):
        """Initialize the AI manager."""
        super().__init__(parent)
        
        # Store the parent for callbacks
        self.parent = parent
        
        # Store settings
        self.settings = settings
        
        # Thread pool for background tasks
        self.thread_pool = QThreadPool.globalInstance()
        
        # Current AI model
        self.current_model = settings.get("ai", "model", None) if settings else None
    
    def get_current_model(self):
        """Get the current AI model."""
        return self.current_model
    
    def set_current_model(self, model_name):
        """
        Set the current AI model.
        
        Args:
            model_name (str): The name of the model to set
        """
        self.current_model = model_name
        
        # Save to settings if available
        if self.settings:
            self.settings.set("ai", "model", model_name)
            self.settings.save_settings()
    
    def preload_model(self, model_name):
        """
        Preload the specified model in the background.
        
        Args:
            model_name (str): The name of the model to preload
            
        Raises:
            Exception: If an error occurs during preloading
        """
        logger.info(f"Preloading model: {model_name}")
        
        try:
            # Import the necessary modules
            from backend.ai_utils import initialize_ai_models
            from utils.threads import Worker
            
            # Create a worker for model loading
            worker = Worker(initialize_ai_models, model_name=model_name, force_reload=True)
            
            # Connect signals
            if hasattr(self.parent, '_on_model_preload_result'):
                worker.signals.result.connect(
                    lambda result: self.parent._on_model_preload_result(result, model_name)
                )
            
            if hasattr(self.parent, '_on_model_preload_error'):
                worker.signals.error.connect(self.parent._on_model_preload_error)
            
            # Execute the worker
            self.thread_pool.start(worker)
            
        except Exception as e:
            logger.error(f"Error preloading model: {str(e)}")
            raise
    
    def summarize_text(self, text):
        """
        Generate a summary of the given text.
        
        Args:
            text (str): The text to summarize
            
        Raises:
            ImportError: If required libraries are not installed
            Exception: If an error occurs during summarization
        """
        logger.info(f"Summarizing text of length: {len(text)}")
        
        try:
            # Import the necessary modules
            from backend.ai_utils import summarize_long_text
            from utils.threads import SummarizationWorker
            
            # Get settings
            max_length = self.settings.get("ai", "max_summary_length", 150) if self.settings else 150
            min_length = self.settings.get("ai", "min_summary_length", 40) if self.settings else 40
            
            # Create a worker for the summarization task
            worker = SummarizationWorker(
                summarize_long_text,
                text,
                model_name=self.current_model,
                max_length=max_length,
                min_length=min_length
            )
            
            # Connect signals
            if hasattr(self.parent, '_on_summarization_started'):
                worker.signals.started.connect(self.parent._on_summarization_started)
            
            if hasattr(self.parent, '_on_summarization_progress'):
                worker.signals.progress.connect(self.parent._on_summarization_progress)
            
            if hasattr(self.parent, '_on_summarization_result'):
                worker.signals.result.connect(self.parent._on_summarization_result)
            
            if hasattr(self.parent, '_on_summarization_error'):
                worker.signals.error.connect(self.parent._on_summarization_error)
            
            if hasattr(self.parent, '_on_summarization_finished'):
                worker.signals.finished.connect(self.parent._on_summarization_finished)
            
            # Execute the worker
            self.thread_pool.start(worker)
            
        except ImportError as e:
            logger.error(f"Required libraries not installed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error during summarization: {str(e)}")
            raise

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Thread utilities for the Smart Contextual Notes Editor.
Provides worker classes for background operations to keep the UI responsive.
"""

import logging
import traceback
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    
    Signals:
        started: Signal emitted when the worker starts
        finished: Signal emitted when the worker finishes
        error: Signal emitted when an error occurs (error type, error value, traceback)
        result: Signal emitting the result of the worker
        progress: Signal emitting the progress of the worker (int from 0-100)
    """
    started = pyqtSignal()
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
    """
    Worker thread base class.
    
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up.
    """
    
    def __init__(self, fn, *args, **kwargs):
        """
        Initialize the worker thread.
        
        Args:
            fn: The function to run on this worker thread
            args: Arguments to pass to the function
            kwargs: Keywords to pass to the function
        """
        super().__init__()
        
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        
        # Add the signals to the kwargs
        # Create a wrapper function to properly emit the progress signal
        def progress_callback(value):
            self.signals.progress.emit(value)
            
        self.kwargs['progress_callback'] = progress_callback
        
        logger.info(f"Worker initialized for function: {fn.__name__}")
    
    @pyqtSlot()
    def run(self):
        """
        Initialize the runner function with passed args, kwargs.
        This is the method that will be called when the thread starts.
        """
        # Emit started signal
        self.signals.started.emit()
        logger.info(f"Worker started: {self.fn.__name__}")
        
        try:
            # Execute the function
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            logger.error(f"Error in worker thread: {str(e)}")
            traceback_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            logger.error(traceback_str)
            
            # Emit error signal
            self.signals.error.emit((type(e), str(e), traceback_str))
        else:
            # Emit result signal
            self.signals.result.emit(result)
        finally:
            # Emit finished signal
            self.signals.finished.emit()
            logger.info(f"Worker finished: {self.fn.__name__}")


class SummarizationWorker(Worker):
    """
    Worker thread specifically for text summarization.
    
    Inherits from Worker and adds specific functionality for summarization tasks.
    """
    
    def __init__(self, summarize_fn, text, max_length=None, min_length=None, model_name=None):
        """
        Initialize the summarization worker.
        
        Args:
            summarize_fn: The summarization function to call
            text: The text to summarize
            max_length: Maximum length of the summary (in tokens or characters)
            min_length: Minimum length of the summary (in tokens or characters)
            model_name: Name of the AI model to use for summarization
        """
        super().__init__(
            summarize_fn, 
            text,
            max_length=max_length,
            min_length=min_length,
            model_name=model_name
        )
        logger.info(f"SummarizationWorker initialized with model: {model_name if model_name else 'default'}")


class WebScrapingWorker(Worker):
    """
    Worker thread specifically for web scraping operations.
    
    Inherits from Worker and adds specific functionality for web scraping tasks.
    """
    
    def __init__(self, scrape_fn, query=None, url=None):
        """
        Initialize the web scraping worker.
        
        Args:
            scrape_fn: The scraping function to call
            query: The search query (for search operations)
            url: The URL to scrape (for direct scraping operations)
        """
        # Determine which parameters to pass based on the function name
        # to avoid passing unexpected parameters
        kwargs = {}
        
        # If it's a search operation (search_web function)
        if scrape_fn.__name__ == 'search_web' and query is not None:
            kwargs['query'] = query
        # If it's a direct scraping operation (like scrape_page_content)
        elif url is not None:
            kwargs['url'] = url
        
        # If query is provided and not already added, add it
        if query is not None and 'query' not in kwargs:
            kwargs['query'] = query
            
        super().__init__(scrape_fn, **kwargs)
        logger.info(f"WebScrapingWorker initialized for {scrape_fn.__name__}")

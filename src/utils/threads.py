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


class ApiSummarizationWorker(Worker):
    """
    Worker thread specifically for API-based text summarization.
    
    Inherits from Worker and calls an API summarization function.
    """
    
    def __init__(self, summarize_api_fn, text: str, api_key: str, model_id: str):
        """
        Initialize the API summarization worker.
        
        Args:
            summarize_api_fn: The API summarization function to call (e.g., summarize_text_hf_api).
            text (str): The text to summarize.
            api_key (str): The API key for the summarization service.
            model_id (str): The model ID to be used by the API.
        """
        super().__init__(
            summarize_api_fn,
            text=text,          # Pass as keyword argument for clarity
            api_key=api_key,    # Pass as keyword argument
            model_id=model_id   # Pass as keyword argument
        )
        logger.info(f"ApiSummarizationWorker initialized for model: {model_id}")


class LocalSummarizationWorker(Worker):
    """
    Worker thread specifically for local text summarization using Hugging Face pipeline.
    
    Inherits from Worker and calls a local summarization function.
    """
    
    def __init__(self, summarize_local_fn, text: str, model_id: str):
        """
        Initialize the local summarization worker.
        
        Args:
            summarize_local_fn: The local summarization function to call (e.g., summarize_text_local).
            text (str): The text to summarize.
            model_id (str): The model ID to be used by the local pipeline.
        """
        super().__init__(
            summarize_local_fn,
            text=text,          # Pass as keyword argument for clarity
            model_id=model_id   # Pass as keyword argument
        )
        logger.info(f"LocalSummarizationWorker initialized for model: {model_id}")


class ApiTextGenerationWorker(Worker):
    """
    Worker thread specifically for API-based text generation.
    
    Inherits from Worker and calls an API text generation function.
    """
    
    def __init__(self, generate_api_fn, prompt_text: str, api_key: str, model_id: str, max_new_tokens: int):
        """
        Initialize the API text generation worker.
        
        Args:
            generate_api_fn: The API text generation function to call (e.g., generate_text_hf_api).
            prompt_text (str): The prompt to generate text from.
            api_key (str): The API key for the text generation service.
            model_id (str): The model ID to be used by the API.
            max_new_tokens (int): The maximum number of new tokens to generate.
        """
        super().__init__(
            generate_api_fn,
            text_prompt=prompt_text, # Pass as keyword argument for clarity
            api_key=api_key,         # Pass as keyword argument
            model_id=model_id,       # Pass as keyword argument
            max_new_tokens=max_new_tokens # Pass as keyword argument
        )
        logger.info(f"ApiTextGenerationWorker initialized for model: {model_id} with max_new_tokens: {max_new_tokens}")

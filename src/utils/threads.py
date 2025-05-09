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
        
        logger.info("Worker initialized for function: %s" % fn.__name__)
    
    @pyqtSlot()
    def run(self):
        """
        Initialize the runner function with passed args, kwargs.
        This is the method that will be called when the thread starts.
        """
        # Emit started signal
        self.signals.started.emit()
        logger.info("Worker started: %s" % self.fn.__name__)
        
        try:
            # Execute the function
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            logger.error("Error in worker thread: %s" % str(e))
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
            logger.info("Worker finished: %s" % self.fn.__name__)


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
        
        # Store original query/url for result packaging if needed
        self._original_query = None
        self._original_url = None

        if scrape_fn.__name__ == 'search_web' and query is not None:
            kwargs['query'] = query
            self._original_query = query # Store for run method
        elif url is not None: # For scrape_page_content or similar
            kwargs['url'] = url
            self._original_url = url # Store for run method
        
        # If query is provided and not already added (e.g. generic scrape_fn that takes a query)
        # This might be redundant if scrape_fn name check is primary, but provides flexibility
        if query is not None and 'query' not in kwargs:
            kwargs['query'] = query
            if self._original_query is None: self._original_query = query

        super().__init__(scrape_fn, **kwargs)
        logger.info("WebScrapingWorker initialized for %s with query: '%s', url: '%s'" % (scrape_fn.__name__, self._original_query, self._original_url))

    @pyqtSlot()
    def run(self):
        """
        Execute the worker's function and emit results, packaging them if necessary.
        """
        self.signals.started.emit()
        logger.info("WebScrapingWorker (overridden run) started for: %s" % self.fn.__name__)
        
        final_result_to_emit = None
        try:
            # Execute the function (e.g., search_web(query=...) or scrape_page_content(url=...))
            raw_result = self.fn(**self.kwargs) # Pass only kwargs as per Worker's __init__ for fn

            if self.fn.__name__ == 'search_web':
                # raw_result is expected to be a list of links
                if self._original_query is not None:
                    final_result_to_emit = {'query': self._original_query, 'links': raw_result}
                else:
                    # Fallback, though query should always be there for search_web
                    logger.warning("search_web executed without an _original_query in WebScrapingWorker")
                    final_result_to_emit = {'query': '', 'links': raw_result}
            elif self.fn.__name__ == 'scrape_page_content':
                # scrape_page_content already returns a dict: {'url': url, 'title': title, 'content': content}
                # It might be good to ensure the original URL is part of this if not already.
                # For now, assume raw_result is sufficient or self.fn handles it.
                final_result_to_emit = raw_result 
            else:
                # For other functions, emit raw result
                final_result_to_emit = raw_result

        except Exception as e:
            logger.error("Error in WebScrapingWorker thread: %s" % str(e))
            traceback_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            logger.error(traceback_str)
            self.signals.error.emit((type(e), str(e), traceback_str))
        else:
            if final_result_to_emit is not None:
                self.signals.result.emit(final_result_to_emit)
            else:
                logger.warning(f"WebScrapingWorker for {self.fn.__name__} completed but final_result_to_emit is None.")
        finally:
            self.signals.finished.emit()
            logger.info("WebScrapingWorker (overridden run) finished for: %s" % self.fn.__name__)


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
        logger.info("ApiSummarizationWorker initialized for model: %s" % model_id)


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
        logger.info("LocalSummarizationWorker initialized for model: %s" % model_id)


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
        logger.info("ApiTextGenerationWorker initialized for model: %s with max_new_tokens: %d" % (model_id, max_new_tokens))


class EntityExtractionWorker(Worker):
    """Worker thread for entity extraction."""
    def __init__(self, extract_fn, text: str, model_id: str = None):
        """
        Initialize the entity extraction worker.
        Args:
            extract_fn: The entity extraction function to call.
            text (str): The text to extract entities from.
            model_id (str, optional): Specific model ID if applicable.
        """
        super().__init__(extract_fn, text=text, model_id=model_id)
        logger.info("EntityExtractionWorker initialized.")


class QuestionAnsweringWorker(Worker):
    """Worker thread for Question Answering based on provided context."""
    def __init__(self, qna_fn, original_note_text: str, extracted_entities: list, web_content_collated: str, qna_model_id: str = None):
        """
        Initialize the Question Answering worker.

        Args:
            qna_fn: The Question Answering function to call (e.g., from AIManager).
            original_note_text (str): The original text of the note.
            extracted_entities (list): List of entities extracted from the note.
            web_content_collated (str): Collated text content from web searches.
            qna_model_id (str, optional): Specific model ID for Q&A if applicable.
        """
        super().__init__(
            qna_fn,
            original_note_text=original_note_text,
            extracted_entities=extracted_entities,
            web_content_collated=web_content_collated,
            qna_model_id=qna_model_id
        )
        logger.info("QuestionAnsweringWorker initialized.")

class WebContentSummarizationWorker(Worker):
    """
    Worker thread for summarizing web content.
    Inherits from Worker and calls a summarization function.
    """
    def __init__(self, summarize_fn, text: str, model_id: str = None):
        """
        Initialize the web content summarization worker.
        
        Args:
            summarize_fn: The summarization function to call (e.g., a method in AIManager).
            text (str): The web page text to summarize.
            model_id (str, optional): The model ID if specific model selection is needed.
        """
        super().__init__(
            summarize_fn,
            text=text,
            model_id=model_id
        )
        logger.info("WebContentSummarizationWorker initialized for model: %s" % model_id if model_id else "default")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web search manager for the Smart Contextual Notes Editor.
Handles web search operations and result processing.
"""

import logging
from PyQt5.QtCore import QObject, QThreadPool, pyqtSignal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebSearchManager(QObject):
    """Manager for web search operations."""
    
    # Define signals
    search_result_signal = pyqtSignal(list)
    search_started_signal = pyqtSignal()
    search_progress_signal = pyqtSignal(int)
    search_error_signal = pyqtSignal(str)
    search_finished_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize the web search manager."""
        super().__init__(parent)
        
        # Store the parent for callbacks
        self.parent = parent
        
        # Thread pool for background tasks
        self.thread_pool = QThreadPool.globalInstance()
        
        # Store search results
        self.search_results = []
    
    def generate_search_query(self, text):
        """
        Generate a search query from the given text.
        
        Args:
            text (str): The text to generate a query from
            
        Returns:
            str: The generated search query
        """
        # This is a simple implementation that could be enhanced with NLP
        # For now, just take the first 10 words or so
        words = text.split()
        if len(words) > 10:
            return " ".join(words[:10])
        return text
    
    def perform_search(self, query):
        """
        Perform a web search with the given query.
        
        Args:
            query (str): The search query
            
        Raises:
            ImportError: If required libraries are not installed
        """
        logger.info(f"Performing web search for: {query}")
        
        try:
            # Import the necessary modules
            from web.scraper import search_web
            from utils.threads import WebScrapingWorker
            
            # Create a worker for the web search
            worker = WebScrapingWorker(search_web, query=query)
            
            # Get the web_controller from the parent (MainWindow)
            web_controller = self.parent.web_controller

            # Connect signals to WebController's methods
            if hasattr(web_controller, '_on_web_search_started'):
                worker.signals.started.connect(web_controller._on_web_search_started)
            
            if hasattr(web_controller, '_on_web_search_progress'):
                worker.signals.progress.connect(web_controller._on_web_search_progress)
            
            if hasattr(web_controller, '_on_web_search_result'):
                worker.signals.result.connect(web_controller._on_web_search_result)
            
            if hasattr(web_controller, '_on_web_search_error'):
                worker.signals.error.connect(web_controller._on_web_search_error)
            
            if hasattr(web_controller, '_on_web_search_finished'):
                worker.signals.finished.connect(web_controller._on_web_search_finished)
            
            # Execute the worker
            self.thread_pool.start(worker)
            
        except ImportError as e:
            logger.error(f"Required libraries not installed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error performing web search: {str(e)}")
            raise
    
    def search_web(self, query):
        """
        Initiate a web search with the given query and emit signals with the results.
        
        Args:
            query (str): The search query
        """
        logger.info(f"Initiating web search for: {query}")
        
        # Connect internal handlers for the worker signals
        def on_search_result(results):
            self.search_results = results
            self.search_result_signal.emit(results)
        
        try:
            # Import the necessary modules
            from web.scraper import search_web
            from utils.threads import WebScrapingWorker
            
            # Create a worker for the web search
            worker = WebScrapingWorker(search_web, query=query)
            
            # Connect signals to our internal handlers
            worker.signals.started.connect(lambda: self.search_started_signal.emit())
            worker.signals.progress.connect(lambda p: self.search_progress_signal.emit(p))
            worker.signals.result.connect(on_search_result)
            worker.signals.error.connect(lambda e: self.search_error_signal.emit(str(e)))
            worker.signals.finished.connect(lambda: self.search_finished_signal.emit())
            
            # Also connect to parent's handlers if they exist
            if hasattr(self.parent, '_on_web_search_started'):
                worker.signals.started.connect(self.parent._on_web_search_started)
            
            if hasattr(self.parent, '_on_web_search_progress'):
                worker.signals.progress.connect(self.parent._on_web_search_progress)
            
            if hasattr(self.parent, '_on_web_search_result'):
                worker.signals.result.connect(self.parent._on_web_search_result)
            
            if hasattr(self.parent, '_on_web_search_error'):
                worker.signals.error.connect(self.parent._on_web_search_error)
            
            if hasattr(self.parent, '_on_web_search_finished'):
                worker.signals.finished.connect(self.parent._on_web_search_finished)
            
            # Execute the worker
            self.thread_pool.start(worker)
            
        except ImportError as e:
            error_msg = f"Required libraries not installed: {str(e)}"
            logger.error(error_msg)
            self.search_error_signal.emit(error_msg)
            if hasattr(self.parent, '_on_web_search_error'):
                self.parent._on_web_search_error(error_msg)
        except Exception as e:
            error_msg = f"Error performing web search: {str(e)}"
            logger.error(error_msg)
            self.search_error_signal.emit(error_msg)
            if hasattr(self.parent, '_on_web_search_error'):
                self.parent._on_web_search_error(error_msg)

    def fetch_content(self, url):
        """
        Fetch content from a URL.
        
        Args:
            url (str): The URL to fetch content from
            
        Raises:
            Exception: If an error occurs during fetching
        """
        logger.info(f"Fetching content from: {url}")
        
        try:
            # Import the necessary modules
            from web.scraper import scrape_page_content
            from utils.threads import WebScrapingWorker
            
            # Create a worker for the content scraping
            worker = WebScrapingWorker(scrape_page_content, url=url)
            
            # Connect signals
            if hasattr(self.parent, '_on_content_fetch_started'):
                worker.signals.started.connect(
                    lambda: self.parent._on_content_fetch_started(url)
                )
            
            if hasattr(self.parent, '_on_content_fetch_progress'):
                worker.signals.progress.connect(self.parent._on_content_fetch_progress)
            
            if hasattr(self.parent, '_on_content_fetch_result'):
                worker.signals.result.connect(self.parent._on_content_fetch_result)
            
            if hasattr(self.parent, '_on_content_fetch_error'):
                worker.signals.error.connect(self.parent._on_content_fetch_error)
            
            if hasattr(self.parent, '_on_web_search_finished'):  # Reuse the same finished handler
                worker.signals.finished.connect(self.parent._on_web_search_finished)
            
            # Execute the worker
            self.thread_pool.start(worker)
            
        except Exception as e:
            logger.error(f"Error fetching content: {str(e)}")
            raise

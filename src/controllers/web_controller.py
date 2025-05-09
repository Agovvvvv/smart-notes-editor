#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controller for web search operations.
"""

import logging
import traceback
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class WebController(QObject):
    """Controller for web search operations."""
    
    # Define signals
    web_search_started = pyqtSignal()
    web_search_progress = pyqtSignal(int)
    web_search_result = pyqtSignal(dict)
    web_search_error = pyqtSignal(tuple)
    web_search_finished = pyqtSignal()
    
    content_fetch_started = pyqtSignal(str)
    content_fetch_progress = pyqtSignal(int)
    content_fetch_result = pyqtSignal(dict)
    content_fetch_error = pyqtSignal(tuple)
    content_fetch_finished = pyqtSignal()
    
    def __init__(self, main_window):
        """Initialize the web controller."""
        super().__init__()
        self.main_window = main_window
        
        # Import web search manager here to avoid circular imports
        from managers.web_search_manager import WebSearchManager
        self.web_search_manager = WebSearchManager(self.main_window)
        
        # Store the last search results
        self.last_search_results = {}
        
        # Connect web search manager signals
        self._connect_web_search_manager_signals()
    
    def _connect_web_search_manager_signals(self):
        """Set up callback methods for the web search manager."""
        # Instead of connecting signals directly, we'll use the callback methods
        # that the WebSearchManager expects to call on its parent
        pass
    
    # Callback methods for WebSearchManager
    def _on_web_search_started(self):
        """Handle web search started event."""
        self.web_search_started.emit()
    
    def _on_web_search_progress(self, progress):
        """Handle web search progress event."""
        self.web_search_progress.emit(progress)
    
    def _on_web_search_result(self, search_data: dict):
        """Handle web search result event.
        
        Args:
            search_data (dict): A dictionary like {'query': str, 'links': list}
        """
        logger.info(f"WebController: Received search data from manager: {search_data}. Emitting web_search_result signal.")
        # Store the results (now a dictionary)
        # If last_search_results is used elsewhere and expects only links,
        # this might need adjustment, e.g., self.last_search_results = search_data.get('links', [])
        # For now, storing the whole dict for consistency with the signal.
        self.last_search_results = search_data 
        
        # Emit the signal
        self.web_search_result.emit(search_data)
    
    def _on_web_search_error(self, error_msg):
        """Handle web search error event."""
        # Convert string error to tuple format expected by our signal
        error_info = (ValueError, ValueError(error_msg), "")
        self.web_search_error.emit(error_info)
    
    def _on_web_search_finished(self):
        """Handle web search finished event."""
        self.web_search_finished.emit()
    
    # Callback methods for content fetching
    def _on_content_fetch_started(self, url):
        """Handle content fetch started event."""
        self.content_fetch_started.emit(url)
    
    def _on_content_fetch_progress(self, progress):
        """Handle content fetch progress event."""
        self.content_fetch_progress.emit(progress)
    
    def _on_content_fetch_result(self, result):
        """Handle content fetch result event."""
        self.content_fetch_result.emit(result)
    
    def _on_content_fetch_error(self, error_info):
        """Handle content fetch error event."""
        self.content_fetch_error.emit(error_info)
    
    def _on_content_fetch_finished(self):
        """Handle content fetch finished event."""
        self.content_fetch_finished.emit()
    
    def _handle_search_result(self, results):
        """
        Handle the search result signal from the web search manager.
        
        Args:
            results (list): The search results
        """
        # Store the results
        self.last_search_results = results
        
        # Emit the signal
        self.web_search_result.emit(results)
    
    def perform_search(self, query):
        """
        Perform a web search with the given query.
        
        Args:
            query (str): The search query
        """
        try:
            self.web_search_manager.perform_search(query)
        except Exception as e:
            error_info = (type(e), e, traceback.format_exc())
            self.web_search_error.emit(error_info)
            self.web_search_finished.emit()
    
    def generate_search_query(self, text):
        """
        Generate a search query from the provided text.
        
        Args:
            text (str): The text to generate a query from
            
        Returns:
            str: The generated search query
        """
        return self.web_search_manager.generate_search_query(text)
    
    def fetch_content(self, url):
        """
        Fetch content from a URL.
        
        Args:
            url (str): The URL to fetch content from
        """
        try:
            self.web_search_manager.fetch_content(url)
        except Exception as e:
            error_info = (type(e), e, traceback.format_exc())
            self.content_fetch_error.emit(error_info)
            self.content_fetch_finished.emit()
    
    def get_last_search_results(self):
        """
        Get the results of the last search.
        
        Returns:
            dict: The last search results
        """
        return self.last_search_results

    def fetch_url_content(self, url, context=None):
        """
        Fetch content from a URL and attach context for downstream consumers (e.g., QnA enhancement).
        Args:
            url (str): The URL to fetch content from
            context (dict): Extra context to attach to the result/error
        """
        import traceback
        if context is None:
            context = {}
        try:
            from PyQt5.QtCore import QMetaObject
            # Wrap the result/error handlers to inject context
            def on_result(result):
                # result is expected to be a dict with at least 'url' and 'content'
                result_with_context = dict(result)
                result_with_context['context'] = context
                self.content_fetch_result.emit(result_with_context)
                self.content_fetch_finished.emit()
                disconnect_all()

            def on_error(error_info):
                # error_info could be a tuple or dict; standardize to dict
                if isinstance(error_info, tuple):
                    error_type, error_obj, tb = error_info
                    error_dict = {
                        'url': url,
                        'error': str(error_obj),
                        'context': context,
                        'traceback': tb
                    }
                else:
                    error_dict = dict(error_info)
                    error_dict['context'] = context
                self.content_fetch_error.emit(error_dict)
                self.content_fetch_finished.emit()
                disconnect_all()

            def disconnect_all():
                try:
                    self.content_fetch_result.disconnect(on_result)
                except Exception:
                    pass
                try:
                    self.content_fetch_error.disconnect(on_error)
                except Exception:
                    pass

            self.content_fetch_result.connect(on_result)
            self.content_fetch_error.connect(on_error)

            # Call the existing fetch_content (will emit signals above)
            self.fetch_content(url)
        except Exception as e:
            error_dict = {
                'url': url,
                'error': str(e),
                'context': context,
                'traceback': traceback.format_exc()
            }
            self.content_fetch_error.emit(error_dict)
            self.content_fetch_finished.emit()

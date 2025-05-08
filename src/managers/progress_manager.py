#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Manager for handling progress indicators.
"""

import logging
from PyQt5.QtWidgets import QProgressBar, QStatusBar

logger = logging.getLogger(__name__)

class ProgressManager:
    """Manager for handling progress indicators."""
    
    def __init__(self, main_window):
        """Initialize the progress manager."""
        self.main_window = main_window
        self.progress_bar = None
        self.status_bar = None
    
    def setup_progress_bar(self, status_bar):
        """
        Set up the progress bar in the status bar.
        
        Args:
            status_bar (QStatusBar): The status bar to add the progress bar to
        """
        self.status_bar = status_bar
        
        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.hide()
        
        # Add to status bar
        self.status_bar.addPermanentWidget(self.progress_bar)
    
    def on_operation_started(self):
        """Handle operation started event."""
        logger.info("Operation started event received")
        if self.progress_bar:
            logger.info("Setting progress bar to 0 and showing it")
            self.progress_bar.setValue(0)
            self.progress_bar.show()
        else:
            logger.error("Progress bar is None - not initialized properly")
    
    def on_progress_update(self, progress):
        """
        Handle progress update event.
        
        Args:
            progress (int): The progress value (0-100)
        """
        logger.info(f"Progress update event received: {progress}%")
        if self.progress_bar:
            self.progress_bar.setValue(progress)
        else:
            logger.error("Progress bar is None - not initialized properly")
    
    def on_operation_error(self, error_info):
        """
        Handle operation error event.
        
        Args:
            error_info: The error information
        """
        logger.info(f"Operation error event received: {error_info}")
        if self.progress_bar:
            self.progress_bar.hide()
        else:
            logger.error("Progress bar is None - not initialized properly")
        
        # If error_info is a tuple (type, value, traceback), extract the value
        if isinstance(error_info, tuple) and len(error_info) >= 2:
            error_value = error_info[1]
            if self.status_bar:
                self.status_bar.showMessage(f"Error: {error_value}")
        else:
            # Otherwise, use the error_info directly
            if self.status_bar:
                self.status_bar.showMessage(f"Error: {error_info}")
    
    def on_operation_finished(self):
        """Handle operation finished event."""
        logger.info("Operation finished event received")
        if self.progress_bar:
            self.progress_bar.hide()
        else:
            logger.error("Progress bar is None - not initialized properly")
    
    def start_operation_with_message(self, message: str):
        """Start an operation: show progress bar and display a message."""
        self.on_operation_started()
        self.show_message(message)

    def hide_progress(self):
        """Hide the progress bar."""
        logger.info("hide_progress called")
        if self.progress_bar:
            self.progress_bar.hide()
        else:
            logger.warning("Progress bar is None when trying to hide - might not be initialized properly or already hidden.")

    def show_message(self, message):
        """
        Show a message in the status bar.
        
        Args:
            message (str): The message to show
        """
        if self.status_bar:
            self.status_bar.showMessage(message)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Summary panel for the Smart Contextual Notes Editor.
Displays AI-generated summaries of notes.
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextBrowser, QApplication
)
from PyQt5.QtGui import QIcon

logger = logging.getLogger(__name__)

class SummaryPanel(QWidget):
    """Panel for displaying AI-generated summaries."""
    
    def __init__(self, parent=None):
        """Initialize the summary panel."""
        super().__init__(parent)
        
        # Store the parent for callbacks
        self.parent = parent
        
        # Set up the UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        
        # Add a header
        header_label = QLabel("<h2>Summary</h2>")
        layout.addWidget(header_label)
        
        # Add the summary text browser
        self.summary_browser = QTextBrowser()
        self.summary_browser.setPlaceholderText("Generated summary will appear here...")
        layout.addWidget(self.summary_browser)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        # Insert at Top button
        self.insert_top_button = QPushButton(QIcon.fromTheme("go-top"), "Insert at Top")
        self.insert_top_button.clicked.connect(self.insert_at_top)
        button_layout.addWidget(self.insert_top_button)
        
        # Insert at Cursor button
        self.insert_cursor_button = QPushButton(QIcon.fromTheme("edit-paste"), "Insert at Cursor")
        self.insert_cursor_button.clicked.connect(self.insert_at_cursor)
        button_layout.addWidget(self.insert_cursor_button)

        # Insert at Bottom button
        self.insert_bottom_button = QPushButton(QIcon.fromTheme("go-bottom"), "Insert at Bottom")
        self.insert_bottom_button.clicked.connect(self.insert_at_bottom)
        button_layout.addWidget(self.insert_bottom_button)
        
        layout.addLayout(button_layout)

        # Close button - consider placing it below the other buttons for grouping
        self.close_button = QPushButton(QIcon.fromTheme("window-close"), "Close Panel")
        self.close_button.clicked.connect(self.close_panel)
        layout.addWidget(self.close_button) # Added directly to the main vertical layout
    
    def set_summary(self, summary):
        """Set the summary text in the browser."""
        self.summary_browser.setPlainText(summary)
        self.summary = summary # Keep a local copy of the raw summary
    
    def clear_summary(self):
        """Clear the summary text and stored summary."""
        self.summary_browser.clear()
        self.summary = ""
        logger.debug("SummaryPanel summary cleared.")

    def insert_at_top(self):
        """Signal the parent to insert the summary at the top."""
        if hasattr(self.parent, 'insert_summary_at_top') and self.summary:
            self.parent.insert_summary_at_top(self.summary)
        elif not self.summary:
            logger.warning("SummaryPanel: Attempted to insert empty summary at top.")
    
    def insert_at_cursor(self):
        """Signal the parent to insert the summary at the cursor position."""
        if hasattr(self.parent, 'insert_summary_at_cursor') and self.summary:
            self.parent.insert_summary_at_cursor(self.summary)
        elif not self.summary:
            logger.warning("SummaryPanel: Attempted to insert empty summary at cursor.")

    def insert_at_bottom(self):
        """Signal the parent to insert the summary at the bottom."""
        if hasattr(self.parent, 'insert_summary_at_bottom') and self.summary:
            self.parent.insert_summary_at_bottom(self.summary)
        elif not self.summary:
            logger.warning("SummaryPanel: Attempted to insert empty summary at bottom.")
    
    def close_panel(self):
        """Signal the parent to close this panel."""
        if hasattr(self.parent, 'close_summary_panel'):
            self.parent.close_summary_panel()

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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        layout.addWidget(self.summary_browser)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        # Copy button
        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_button)
        
        # Insert button
        insert_button = QPushButton("Insert at Cursor")
        insert_button.clicked.connect(self.insert_at_cursor)
        button_layout.addWidget(insert_button)
        
        # Close button
        close_button = QPushButton("Close Panel")
        close_button.clicked.connect(self.close_panel)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def set_summary(self, summary):
        """Set the summary text in the browser."""
        self.summary_browser.setPlainText(summary)
        self.summary = summary
    
    def copy_to_clipboard(self):
        """Copy the summary to the clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.summary)
        
        # Update status in parent if available
        if hasattr(self.parent, 'statusBar'):
            self.parent.statusBar.showMessage("Summary copied to clipboard")
    
    def insert_at_cursor(self):
        """Signal the parent to insert the summary at the cursor position."""
        if hasattr(self.parent, 'insert_summary_at_cursor'):
            self.parent.insert_summary_at_cursor(self.summary)
    
    def close_panel(self):
        """Signal the parent to close this panel."""
        if hasattr(self.parent, 'close_summary_panel'):
            self.parent.close_summary_panel()

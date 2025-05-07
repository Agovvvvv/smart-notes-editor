#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web results panel for the Smart Contextual Notes Editor.
Displays web search results and content.
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextBrowser, QListWidget, QListWidgetItem,
    QTabWidget, QMessageBox
)
from PyQt5.QtCore import Qt

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebPanel(QWidget):
    """Panel for displaying web search results and content."""
    
    def __init__(self, parent=None):
        """Initialize the web panel."""
        super().__init__(parent)
        
        # Store the parent for callbacks
        self.parent = parent
        
        # Initialize components that will be accessed from methods
        self.content_browser = None
        self.list_widget = None
        self.tab_widget = None
        
        # Set up the UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        
        # Add a header
        header_label = QLabel("<h2>Web Search Results</h2>")
        layout.addWidget(header_label)
        
        # Create tabs for different views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Results list tab
        results_list_widget = QWidget()
        results_list_layout = QVBoxLayout(results_list_widget)
        
        # Create a list widget for the results
        self.list_widget = QListWidget()
        results_list_layout.addWidget(self.list_widget)
        self.tab_widget.addTab(results_list_widget, "Results List")
        
        # Content view tab
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Create a text browser for the content
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(True)
        content_layout.addWidget(self.content_browser)
        
        self.tab_widget.addTab(content_widget, "Content View")
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        # Fetch Content button
        fetch_button = QPushButton("Fetch Content")
        fetch_button.clicked.connect(self.fetch_content)
        button_layout.addWidget(fetch_button)
        
        # Insert Link button
        insert_button = QPushButton("Insert Link at Cursor")
        insert_button.clicked.connect(self.insert_link)
        button_layout.addWidget(insert_button)
        
        # Close button
        close_button = QPushButton("Close Panel")
        close_button.clicked.connect(self.close_panel)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def set_results(self, results):
        """Set the search results in the list widget."""
        self.list_widget.clear()
        for result in results:
            item = QListWidgetItem(f"<b>{result['title']}</b>")
            item.setData(Qt.UserRole, result['url'])
            self.list_widget.addItem(item)
        
        # Connect item clicked signal
        self.list_widget.itemClicked.connect(self.on_result_item_clicked)
    
    def on_result_item_clicked(self, item):
        """Handle a result item being clicked."""
        url = item.data(Qt.UserRole)
        
        # Display the URL in the content browser
        self.content_browser.setHtml(
            f"<h3>{item.text()}</h3>"
            f"<p><a href='{url}'>{url}</a></p>"
            f"<p>Click 'Fetch Content' to retrieve the content of this page.</p>"
        )
    
    def fetch_content(self):
        """Signal the parent to fetch content for the selected result."""
        if not self.list_widget.currentItem():
            QMessageBox.warning(
                self,
                "No Result Selected",
                "Please select a search result to fetch its content."
            )
            return
        
        url = self.list_widget.currentItem().data(Qt.UserRole)
        
        if hasattr(self.parent, 'fetch_web_content'):
            self.parent.fetch_web_content(url)
    
    def display_content(self, result):
        """Display fetched content in the content browser."""
        # Display the content in the content browser
        content_html = f"<h2>{result['title']}</h2>\n"
        content_html += f"<p><a href='{result['url']}'>{result['url']}</a></p>\n"
        
        if result['error']:
            content_html += f"<p style='color: red;'><b>Error:</b> {result['error']}</p>\n"
        
        # Format the content with paragraphs
        if result['content']:
            paragraphs = result['content'].split('\n\n')
            for p in paragraphs:
                if p.strip():
                    content_html += f"<p>{p}</p>\n"
        else:
            content_html += "<p>No content could be extracted from this page.</p>"
        
        self.content_browser.setHtml(content_html)
        
        # Switch to the Content View tab
        self.tab_widget.setCurrentIndex(1)  # Index 1 is the Content View tab
    
    def insert_link(self):
        """Signal the parent to insert a link to the selected result."""
        if not self.list_widget.currentItem():
            QMessageBox.warning(
                self,
                "No Result Selected",
                "Please select a search result to insert its link."
            )
            return
        
        # Get the title and URL of the selected item
        title = self.list_widget.currentItem().text().replace('<b>', '').replace('</b>', '')
        url = self.list_widget.currentItem().data(Qt.UserRole)
        
        if hasattr(self.parent, 'insert_web_link'):
            self.parent.insert_web_link(title, url)
    
    def close_panel(self):
        """Signal the parent to close this panel."""
        if hasattr(self.parent, 'close_web_panel'):
            self.parent.close_web_panel()

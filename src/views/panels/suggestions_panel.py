#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Suggestions panel for the Smart Contextual Notes Editor.
Displays contextual suggestions based on note content and web search results.
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextBrowser, QListWidget, QListWidgetItem,
    QTabWidget, QMessageBox, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SuggestionsPanel(QWidget):
    """Panel for displaying contextual suggestions based on note content and web search results."""
    
    def __init__(self, parent=None):
        """Initialize the suggestions panel."""
        super().__init__(parent)
        
        # Store the parent for callbacks
        self.parent = parent
        
        # Initialize components that will be accessed from methods
        self.tab_widget = None
        self.suggestions_browser = None
        self.missing_info_list = None
        
        # Set up the UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        
        # Add a header
        header_label = QLabel("<h2>Contextual Suggestions</h2>")
        layout.addWidget(header_label)
        
        # Create tabs for different views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Content suggestions tab
        content_suggestions_widget = QWidget()
        content_suggestions_layout = QVBoxLayout(content_suggestions_widget)
        
        # Create a text browser for the content suggestions
        self.suggestions_browser = QTextBrowser()
        self.suggestions_browser.setOpenExternalLinks(True)
        content_suggestions_layout.addWidget(self.suggestions_browser)
        
        self.tab_widget.addTab(content_suggestions_widget, "Content Suggestions")
        
        # Missing information tab
        missing_info_widget = QWidget()
        missing_info_layout = QVBoxLayout(missing_info_widget)
        
        # Create a list widget for missing information
        self.missing_info_list = QListWidget()
        missing_info_layout.addWidget(self.missing_info_list)
        
        self.tab_widget.addTab(missing_info_widget, "Missing Information")
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        # Insert Selected button
        insert_button = QPushButton("Insert Selected Suggestion")
        insert_button.clicked.connect(self.insert_suggestion)
        button_layout.addWidget(insert_button)
        
        # Refresh button
        refresh_button = QPushButton("Refresh Suggestions")
        refresh_button.clicked.connect(self.refresh_suggestions)
        button_layout.addWidget(refresh_button)
        
        # Close button
        close_button = QPushButton("Close Panel")
        close_button.clicked.connect(self.close_panel)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def set_suggestions(self, suggestions):
        """
        Set the suggestions in the panel.
        
        Args:
            suggestions (dict): Dictionary with 'content_suggestions' and 'missing_information'
        """
        # Clear existing content
        self.suggestions_browser.clear()
        self.missing_info_list.clear()
        
        # Display content suggestions
        content_suggestions = suggestions.get('content_suggestions', [])
        if content_suggestions:
            html_content = "<h3>Relevant Content from Web</h3>"
            
            for i, suggestion in enumerate(content_suggestions):
                title = suggestion.get('title', 'Untitled')
                url = suggestion.get('url', '#')
                sentences = suggestion.get('sentences', [])
                
                html_content += f"<div style='margin-bottom: 20px; padding: 10px; background-color: #f5f5f5;'>"
                html_content += f"<h4>{i+1}. <a href='{url}'>{title}</a></h4>"
                
                if sentences:
                    html_content += "<ul>"
                    for sentence_data in sentences:
                        sentence = sentence_data.get('sentence', '')
                        similarity = sentence_data.get('similarity', 0)
                        
                        # Color code by similarity
                        color = "#000000"
                        if similarity > 0.7:
                            color = "#006400"  # Dark green for high similarity
                        elif similarity > 0.5:
                            color = "#008000"  # Green for medium similarity
                        elif similarity > 0.3:
                            color = "#808000"  # Olive for low similarity
                        
                        html_content += f"<li><span style='color: {color};'>{sentence}</span>"
                        html_content += f" <small>[Relevance: {similarity:.2f}]</small>"
                        html_content += f" <button onclick='window.insertSuggestion(\"{i}\", \"{sentences.index(sentence_data)}\")'>Insert</button></li>"
                    html_content += "</ul>"
                else:
                    html_content += "<p>No specific sentences found.</p>"
                
                html_content += "</div>"
            
            self.suggestions_browser.setHtml(html_content)
            
            # Connect JavaScript to Python
            self.suggestions_browser.page().mainFrame().javaScriptWindowObjectCleared.connect(
                lambda: self.suggestions_browser.page().mainFrame().addToJavaScriptWindowObject(
                    "pyPanel", self
                )
            )
        else:
            self.suggestions_browser.setHtml("<p>No content suggestions found.</p>")
        
        # Display missing information
        missing_information = suggestions.get('missing_information', [])
        if missing_information:
            for info in missing_information:
                item = QListWidgetItem(info)
                self.missing_info_list.addItem(item)
        else:
            self.missing_info_list.addItem("No missing information identified.")
    
    def insert_suggestion(self):
        """Insert the selected suggestion into the note."""
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:  # Content Suggestions tab
            # Get the selected text from the browser
            selected_text = self.suggestions_browser.textCursor().selectedText()
            
            if not selected_text:
                QMessageBox.warning(
                    self,
                    "No Text Selected",
                    "Please select text from a suggestion to insert."
                )
                return
            
            if hasattr(self.parent, 'insert_suggestion_text'):
                self.parent.insert_suggestion_text(selected_text)
        
        elif current_tab == 1:  # Missing Information tab
            # Get the selected item from the list
            selected_items = self.missing_info_list.selectedItems()
            
            if not selected_items:
                QMessageBox.warning(
                    self,
                    "No Item Selected",
                    "Please select an item from the list to insert."
                )
                return
            
            selected_text = selected_items[0].text()
            
            if hasattr(self.parent, 'insert_suggestion_text'):
                self.parent.insert_suggestion_text(selected_text)
    
    def refresh_suggestions(self):
        """Signal the parent to refresh the suggestions."""
        if hasattr(self.parent, 'refresh_suggestions'):
            self.parent.refresh_suggestions()
    
    def close_panel(self):
        """Signal the parent to close this panel."""
        if hasattr(self.parent, 'close_suggestions_panel'):
            self.parent.close_suggestions_panel()

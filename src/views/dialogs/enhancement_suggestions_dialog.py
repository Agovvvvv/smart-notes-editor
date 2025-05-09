#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dialog for displaying note enhancement suggestions and allowing user interaction.
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTextBrowser, 
    QDialogButtonBox, QScrollArea, QWidget, QHBoxLayout, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices

logger = logging.getLogger(__name__)

class EnhancementSuggestionsDialog(QDialog):
    """Dialog to display enhancement suggestions to the user."""

    # Signal to indicate a request to insert specific text into the main editor
    insert_suggestion_requested = pyqtSignal(str) 

    def __init__(self, suggestions: list, parent=None):
        super().__init__(parent)
        self.suggestions = suggestions
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Enhancement Suggestions")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        if not self.suggestions:
            layout.addWidget(QLabel("No enhancement suggestions available."))
        else:
            scroll_area = QScrollArea(self)
            scroll_area.setWidgetResizable(True)
            
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setSpacing(10)

            for i, suggestion_data in enumerate(self.suggestions):
                suggestion_group_box = self._create_suggestion_group(suggestion_data, i)
                content_layout.addWidget(suggestion_group_box)
            
            content_widget.setLayout(content_layout)
            scroll_area.setWidget(content_widget)
            layout.addWidget(scroll_area)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _create_suggestion_group(self, suggestion_data: dict, index: int):
        """Creates a widget group for a single suggestion."""
        group_widget = QFrame(self)
        group_widget.setFrameShape(QFrame.StyledPanel) # Add a bit of visual separation
        group_layout = QVBoxLayout(group_widget)

        # Suggestion content (answer or summary)
        content_text = suggestion_data.get('answer', suggestion_data.get('summary', 'N/A'))
        content_label = QLabel("<b>Suggestion:</b>")
        group_layout.addWidget(content_label)
        
        content_browser = QTextBrowser(self)
        content_browser.setPlainText(content_text)
        content_browser.setFixedHeight(100) # Adjust as needed
        content_browser.setReadOnly(True)
        group_layout.addWidget(content_browser)

        # Source URL
        source_url = suggestion_data.get('source_url', '')
        if source_url:
            source_label_text = f"<b>Source:</b> <a href='{source_url}'>{source_url}</a>"
            source_label = QLabel(source_label_text)
            source_label.setOpenExternalLinks(True) # Make the link clickable
            group_layout.addWidget(source_label)
        else:
            group_layout.addWidget(QLabel("<b>Source:</b> Not available"))
        
        # Insert button
        button_layout = QHBoxLayout()
        insert_button = QPushButton(f"Insert Suggestion {index + 1}")
        insert_button.clicked.connect(lambda _, text=content_text: self.insert_suggestion_requested.emit(text))
        button_layout.addStretch()
        button_layout.addWidget(insert_button)
        button_layout.addStretch()
        group_layout.addLayout(button_layout)
        
        group_widget.setLayout(group_layout)
        return group_widget

if __name__ == '__main__':
    # Example usage for testing the dialog directly
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Sample suggestions data (mimicking what might come from AIController)
    sample_suggestions = [
        {
            'answer': 'The mitochondria is the powerhouse of the cell.', 
            'source_url': 'https://en.wikipedia.org/wiki/Mitochondrion',
            'query': 'what is mitochondria'
        },
        {
            'summary': 'Photosynthesis is a process used by plants, algae and certain bacteria to harness energy from sunlight and turn it into chemical energy.',
            'source_url': 'https://en.wikipedia.org/wiki/Photosynthesis',
            'query': 'photosynthesis overview'
        },
        {
            'answer': 'The capital of France is Paris.',
            'source_url': '', # Test case with no source URL
            'query': 'capital of France'
        }
    ]

    dialog = EnhancementSuggestionsDialog(sample_suggestions)
    def handle_insert(text_to_insert):
        print(f"Request to insert: {text_to_insert}")
    dialog.insert_suggestion_requested.connect(handle_insert)
    
    if dialog.exec_() == QDialog.Accepted:
        print("Dialog accepted")
    else:
        print("Dialog cancelled")

    sys.exit(app.exec_())

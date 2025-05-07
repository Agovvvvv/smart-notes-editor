#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Auto-enhance dialog for the Smart Contextual Notes Editor.
Provides a dialog to configure and monitor the automatic note enhancement process.
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QCheckBox,
    QSpinBox, QGroupBox, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, pyqtSignal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoEnhanceDialog(QDialog):
    """Dialog for configuring and monitoring the automatic note enhancement process."""
    
    # Signals
    enhancement_requested = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize the auto-enhance dialog."""
        super().__init__(parent)
        
        # Store the parent for callbacks
        self.parent = parent
        
        # Set window properties
        self.setWindowTitle("Enhance Notes with AI")
        self.setMinimumWidth(500)
        
        # Set up the UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Add a header
        header_label = QLabel("<h2>Enhance Your Notes with AI</h2>")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Add description
        description = QLabel(
            "This tool will analyze your notes, search for relevant information "
            "on the web, and automatically enhance your notes with the most "
            "relevant content."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Options group
        options_group = QGroupBox("Enhancement Options")
        options_layout = QVBoxLayout(options_group)
        
        # Web search option
        self.search_web_checkbox = QCheckBox("Search the web for additional information")
        self.search_web_checkbox.setChecked(True)
        options_layout.addWidget(self.search_web_checkbox)
        
        # Number of suggestions to add
        suggestions_layout = QHBoxLayout()
        suggestions_layout.addWidget(QLabel("Number of suggestions to add:"))
        self.suggestions_spinbox = QSpinBox()
        self.suggestions_spinbox.setRange(1, 10)
        self.suggestions_spinbox.setValue(3)
        suggestions_layout.addWidget(self.suggestions_spinbox)
        options_layout.addLayout(suggestions_layout)
        
        # Insertion style
        insertion_group = QGroupBox("Insertion Style")
        insertion_layout = QVBoxLayout(insertion_group)
        
        self.insertion_style_group = QButtonGroup(self)
        
        self.append_radio = QRadioButton("Append to end of note")
        self.append_radio.setChecked(True)
        self.insertion_style_group.addButton(self.append_radio, 0)
        insertion_layout.addWidget(self.append_radio)
        
        self.insert_cursor_radio = QRadioButton("Insert at cursor position")
        self.insertion_style_group.addButton(self.insert_cursor_radio, 1)
        insertion_layout.addWidget(self.insert_cursor_radio)
        
        self.insert_section_radio = QRadioButton("Create new 'Related Information' section")
        self.insertion_style_group.addButton(self.insert_section_radio, 2)
        insertion_layout.addWidget(self.insert_section_radio)
        
        options_layout.addWidget(insertion_group)
        layout.addWidget(options_group)
        
        # Progress bar (hidden initially)
        self.progress_group = QGroupBox("Enhancement Progress")
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.status_label = QLabel("Ready to enhance")
        progress_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_group.setVisible(False)
        layout.addWidget(self.progress_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.enhance_button = QPushButton("Enhance Notes")
        self.enhance_button.clicked.connect(self.on_enhance)
        button_layout.addWidget(self.enhance_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def on_enhance(self):
        """Handle the enhance button click."""
        # Show progress UI
        self.progress_group.setVisible(True)
        self.enhance_button.setEnabled(False)
        
        # Get the options
        options = {
            'search_web': self.search_web_checkbox.isChecked(),
            'num_suggestions': self.suggestions_spinbox.value(),
            'insertion_style': self.insertion_style_group.checkedId()
        }
        
        # Emit the signal with the options
        self.enhancement_requested.emit(options)
    
    def set_progress(self, progress, status_text=None):
        """Update the progress bar and status text."""
        self.progress_bar.setValue(progress)
        
        if status_text:
            self.status_label.setText(status_text)
    
    def enhancement_complete(self):
        """Called when enhancement is complete."""
        self.progress_bar.setValue(100)
        self.status_label.setText("Enhancement complete!")
        self.enhance_button.setEnabled(True)
        self.enhance_button.setText("Close")
        self.enhance_button.clicked.disconnect()
        self.enhance_button.clicked.connect(self.accept)
        self.cancel_button.setVisible(False)
    
    def enhancement_failed(self, error_message):
        """Called when enhancement fails."""
        self.status_label.setText(f"Error: {error_message}")
        self.enhance_button.setEnabled(True)
        self.enhance_button.setText("Try Again")
        self.cancel_button.setText("Close")

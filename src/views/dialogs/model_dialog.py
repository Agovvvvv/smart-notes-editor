#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model selection dialog for the Smart Contextual Notes Editor.
Allows users to select AI models for summarization.
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QGroupBox, QRadioButton,
    QButtonGroup, QFormLayout, QDialogButtonBox
)
from PyQt5.QtCore import Qt

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelSelectionDialog(QDialog):
    """Dialog for selecting AI models for summarization."""
    
    def __init__(self, parent=None, available_models=None, current_model=None):
        """
        Initialize the model selection dialog.
        
        Args:
            parent: Parent widget
            available_models: Dictionary of available models with their descriptions
            current_model: Name of the currently selected model
        """
        super().__init__(parent)
        
        self.available_models = available_models or {}
        self.current_model = current_model
        self.selected_model = current_model
        
        self.setWindowTitle("Select AI Model")
        self.setMinimumWidth(500)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Add description
        description = QLabel(
            "Select an AI model for text summarization. Different models offer "
            "different trade-offs between quality, speed, and specific use cases."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Create model selection group
        model_group = QGroupBox("Available Models")
        model_layout = QVBoxLayout()
        
        # Create radio buttons for each model
        self.model_buttons = QButtonGroup(self)
        
        for i, (model_name, model_info) in enumerate(self.available_models.items()):
            model_box = QGroupBox()
            model_box_layout = QVBoxLayout()
            
            # Create radio button with model name
            radio = QRadioButton(model_name)
            radio.setProperty("model_name", model_name)
            self.model_buttons.addButton(radio, i)
            
            if model_name == self.current_model:
                radio.setChecked(True)
            
            model_box_layout.addWidget(radio)
            
            # Add model description
            description = QLabel(model_info.get("description", ""))
            description.setWordWrap(True)
            description.setIndent(20)
            model_box_layout.addWidget(description)
            
            # Add model characteristics
            characteristics = QLabel(
                f"<b>Quality:</b> {model_info.get('quality', 'Unknown')} | "
                f"<b>Speed:</b> {model_info.get('speed', 'Unknown')} | "
                f"<b>Max Length:</b> {model_info.get('max_length', 'Unknown')} tokens"
            )
            characteristics.setIndent(20)
            model_box_layout.addWidget(characteristics)
            
            model_box.setLayout(model_box_layout)
            model_layout.addWidget(model_box)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def accept(self):
        """Handle dialog acceptance."""
        selected_button = self.model_buttons.checkedButton()
        if selected_button:
            self.selected_model = selected_button.property("model_name")
            logger.info(f"Selected model: {self.selected_model}")
        
        super().accept()
    
    def get_selected_model(self):
        """
        Get the selected model.
        
        Returns:
            str: Name of the selected model
        """
        return self.selected_model

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dialog for configuring AI services, specifically for Hugging Face API.
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, 
    QLineEdit, QDialogButtonBox, QLabel, QWidget
)

logger = logging.getLogger(__name__)

class AIServicesDialog(QDialog):
    """Dialog for configuring AI services."""
    
    def __init__(self, settings_model, parent=None):
        """Initialize the AI Services dialog."""
        super().__init__(parent)
        self.settings_model = settings_model
        
        self.setWindowTitle("Configure AI Services (Hugging Face API)")
        self.setMinimumWidth(450) # Increased width for longer model IDs
        
        layout = QVBoxLayout(self)
        
        # Description Label
        description_label = QLabel(
            "Configure your Hugging Face API key, the summarization model ID, "
            "and the text generation model ID. "
            "The application will use the Hugging Face API for these tasks."
        )
        description_label.setWordWrap(True)
        layout.addWidget(description_label)
        
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        layout.addWidget(form_widget)
        
        # Hugging Face API Key
        self.hf_api_key_input = QLineEdit()
        self.hf_api_key_input.setPlaceholderText("Enter your Hugging Face API Key")
        self.hf_api_key_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Hugging Face API Key:", self.hf_api_key_input)

        # Hugging Face Summarization Model ID
        self.hf_model_id_input = QLineEdit()
        self.hf_model_id_input.setPlaceholderText("e.g., facebook/bart-large-cnn")
        form_layout.addRow("Summarization Model ID:", self.hf_model_id_input)

        # Hugging Face Text Generation Model ID
        self.hf_text_gen_model_id_input = QLineEdit()
        self.hf_text_gen_model_id_input.setPlaceholderText("e.g., gpt2")
        form_layout.addRow("Text Generation Model ID:", self.hf_text_gen_model_id_input)
        
        # Dialog Buttons (OK, Cancel)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Load initial settings
        self._load_settings()
        
    def _load_settings(self):
        """Load settings into the dialog widgets."""
        api_key = self.settings_model.get("ai", "huggingface_api_key", "")
        summarization_model_id = self.settings_model.get("ai", "huggingface_summarization_model_id", "facebook/bart-large-cnn")
        text_gen_model_id = self.settings_model.get("ai", "huggingface_text_generation_model_id", "gpt2")
            
        self.hf_api_key_input.setText(api_key)
        self.hf_model_id_input.setText(summarization_model_id)
        self.hf_text_gen_model_id_input.setText(text_gen_model_id)
        
    def accept(self):
        """Save settings when OK is clicked."""
        api_key = self.hf_api_key_input.text()
        summarization_model_id = self.hf_model_id_input.text()
        text_gen_model_id = self.hf_text_gen_model_id_input.text()
        
        self.settings_model.set("ai", "huggingface_api_key", api_key)
        self.settings_model.set("ai", "huggingface_summarization_model_id", summarization_model_id)
        self.settings_model.set("ai", "huggingface_text_generation_model_id", text_gen_model_id)
            
        self.settings_model.save()
        logger.info(f"AI services settings saved. API Key set, Summarization Model ID: {summarization_model_id}, Text Generation Model ID: {text_gen_model_id}")
        super().accept()

    def get_settings(self):
        """Return the configured settings (not strictly needed if saving on accept)."""
        return {
            "huggingface_api_key": self.hf_api_key_input.text(),
            "huggingface_summarization_model_id": self.hf_model_id_input.text(),
            "huggingface_text_generation_model_id": self.hf_text_gen_model_id_input.text()
        }

if __name__ == '__main__':
    # Example usage (for testing the dialog independently)
    from PyQt5.QtWidgets import QApplication
    import sys
    from utils.settings import Settings # Assuming Settings can be initialized for test

    app = QApplication(sys.argv)
    
    # Create a dummy settings object for testing
    class DummySettingsModel:
        def __init__(self):
            self._settings = {
                ("ai", "huggingface_api_key"): "test_key_123",
                ("ai", "huggingface_summarization_model_id"): "facebook/bart-large-cnn",
                ("ai", "huggingface_text_generation_model_id"): "gpt2_test"
            }
        def get(self, section, key, default=None):
            return self._settings.get((section, key), default)
        def set(self, section, key, value):
            self._settings[(section, key)] = value
            print(f"Set settings: {section}/{key} = {value}")
        def save(self):
            print("Settings saved (dummy)")

    settings = DummySettingsModel()
    # settings.set("ai", "summarization_backend", "huggingface_api") # Test with API selected

    dialog = AIServicesDialog(settings)
    if dialog.exec_() == QDialog.Accepted:
        print("Dialog accepted")
        settings_values = dialog.get_settings()
        print("Saved settings:", settings_values)
    else:
        print("Dialog cancelled")
    sys.exit(app.exec_())

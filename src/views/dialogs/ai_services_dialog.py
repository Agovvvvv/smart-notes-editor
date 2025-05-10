#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dialog for configuring AI services, specifically for Hugging Face API, Google Gemini, and Local.
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, 
    QLineEdit, QDialogButtonBox, QLabel, QWidget,
    QComboBox, QGroupBox
)

logger = logging.getLogger(__name__)

# Constants for backend names
BACKEND_LOCAL = "Local"
BACKEND_HF_API = "Hugging Face API"
BACKEND_GEMINI = "Google Gemini"

class AIServicesDialog(QDialog):
    """Dialog for configuring AI services."""
    
    def __init__(self, settings_model, parent=None):
        """Initialize the AI Services dialog."""
        super().__init__(parent)
        self.settings_model = settings_model
        
        self.setWindowTitle("Configure AI Services")
        self.setMinimumWidth(550)
        
        main_layout = QVBoxLayout(self)
        
        # Description Label
        description_label = QLabel(
            "Select the AI backend and configure its settings. "
            "The application will use the selected backend for AI tasks like summarization and Q&A."
        )
        description_label.setWordWrap(True)
        main_layout.addWidget(description_label)

        # Backend Selection
        form_layout = QFormLayout()
        self.backend_combo = QComboBox()
        self.backend_combo.addItems([BACKEND_LOCAL, BACKEND_HF_API, BACKEND_GEMINI])
        self.backend_combo.currentTextChanged.connect(self._on_backend_changed)
        form_layout.addRow("AI Backend:", self.backend_combo)
        main_layout.addLayout(form_layout)

        # --- Hugging Face Settings --- 
        self.hf_settings_widget = QGroupBox("Hugging Face API Settings")
        hf_form_layout = QFormLayout(self.hf_settings_widget)
        
        self.hf_api_key_input = QLineEdit()
        self.hf_api_key_input.setPlaceholderText("Enter your Hugging Face API Key")
        self.hf_api_key_input.setEchoMode(QLineEdit.Password)
        hf_form_layout.addRow("API Key:", self.hf_api_key_input)

        self.hf_model_id_input = QLineEdit()
        self.hf_model_id_input.setPlaceholderText("e.g., facebook/bart-large-cnn")
        hf_form_layout.addRow("Summarization Model ID:", self.hf_model_id_input)

        self.hf_text_gen_model_id_input = QLineEdit()
        self.hf_text_gen_model_id_input.setPlaceholderText("e.g., gpt2")
        hf_form_layout.addRow("Text Generation Model ID:", self.hf_text_gen_model_id_input)
        main_layout.addWidget(self.hf_settings_widget)

        # --- Google Gemini Settings --- 
        self.gemini_settings_widget = QGroupBox("Google Gemini API Settings")
        gemini_form_layout = QFormLayout(self.gemini_settings_widget)

        self.gemini_api_key_input = QLineEdit()
        self.gemini_api_key_input.setPlaceholderText("Enter your Google API Key")
        self.gemini_api_key_input.setEchoMode(QLineEdit.Password)
        gemini_form_layout.addRow("API Key:", self.gemini_api_key_input)
        main_layout.addWidget(self.gemini_settings_widget)
        
        # Dialog Buttons (OK, Cancel)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        self._load_settings()
        
    def _on_backend_changed(self, backend_name: str):
        """Show/hide settings based on selected backend."""
        show_hf = (backend_name == BACKEND_HF_API)
        show_gemini = (backend_name == BACKEND_GEMINI)

        self.hf_settings_widget.setVisible(show_hf)
        self.gemini_settings_widget.setVisible(show_gemini)

    def _load_settings(self):
        """Load settings into the dialog widgets."""
        # Backend selection
        current_backend_value = self.settings_model.get("ai", "backend", "local")
        if current_backend_value == "huggingface_api":
            self.backend_combo.setCurrentText(BACKEND_HF_API)
        elif current_backend_value == "google_gemini":
            self.backend_combo.setCurrentText(BACKEND_GEMINI)
        else: # Default to Local
            self.backend_combo.setCurrentText(BACKEND_LOCAL)

        # Hugging Face settings
        hf_api_key = self.settings_model.get("ai", "huggingface_api_key", "")
        hf_summarization_model_id = self.settings_model.get("ai", "huggingface_summarization_model_id", "facebook/bart-large-cnn")
        hf_text_gen_model_id = self.settings_model.get("ai", "huggingface_text_generation_model_id", "gpt2")
            
        self.hf_api_key_input.setText(hf_api_key)
        self.hf_model_id_input.setText(hf_summarization_model_id)
        self.hf_text_gen_model_id_input.setText(hf_text_gen_model_id)

        # Google Gemini settings
        google_api_key = self.settings_model.get("ai", "google_api_key", "")
        self.gemini_api_key_input.setText(google_api_key)
        
        # Trigger visibility update based on loaded backend
        self._on_backend_changed(self.backend_combo.currentText())
        
    def accept(self):
        """Save settings when OK is clicked."""
        selected_backend_text = self.backend_combo.currentText()
        backend_value_to_save = "local" # Default
        if selected_backend_text == BACKEND_HF_API:
            backend_value_to_save = "huggingface_api"
        elif selected_backend_text == BACKEND_GEMINI:
            backend_value_to_save = "google_gemini"
        
        self.settings_model.set("ai", "backend", backend_value_to_save)
        logger.info(f"AI backend set to: {backend_value_to_save}")

        # Save Hugging Face settings (always save them, active or not)
        hf_api_key = self.hf_api_key_input.text()
        hf_summarization_model_id = self.hf_model_id_input.text()
        hf_text_gen_model_id = self.hf_text_gen_model_id_input.text()
        self.settings_model.set("ai", "huggingface_api_key", hf_api_key)
        self.settings_model.set("ai", "huggingface_summarization_model_id", hf_summarization_model_id)
        self.settings_model.set("ai", "huggingface_text_generation_model_id", hf_text_gen_model_id)
        logger.info(f"Hugging Face settings saved. API Key set: {'yes' if hf_api_key else 'no'}")

        # Save Google Gemini settings (if applicable or always)
        google_api_key = self.gemini_api_key_input.text()
        self.settings_model.set("ai", "google_api_key", google_api_key)
        if backend_value_to_save == "google_gemini":
            logger.info(f"Google Gemini API Key saved: {'yes' if google_api_key else 'no'}")
            
        self.settings_model.save_settings()
        logger.info("AI services settings saved.")
        super().accept()

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
                ("ai", "backend"): "local",
                ("ai", "huggingface_api_key"): "test_key_123",
                ("ai", "huggingface_summarization_model_id"): "facebook/bart-large-cnn",
                ("ai", "huggingface_text_generation_model_id"): "gpt2_test",
                ("ai", "google_api_key"): ""
            }
        def get(self, section, key, default=None):
            return self._settings.get((section, key), default)
        def set(self, section, key, value):
            self._settings[(section, key)] = value
            print(f"Set settings: {section}/{key} = {value}")
        def save_settings(self):
            print("Settings saved (dummy)")

    settings = DummySettingsModel()
    # settings.set("ai", "summarization_backend", "huggingface_api") # Test with API selected

    dialog = AIServicesDialog(settings)
    if dialog.exec_() == QDialog.Accepted:
        print("Dialog accepted")
    else:
        print("Dialog cancelled")
    sys.exit(app.exec_())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Settings utility for the Smart Contextual Notes Editor.
Handles loading and saving application settings.
"""

import os
import json
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Settings:
    """Handles application settings."""
    
    def __init__(self):
        """Initialize settings with default values."""
        # Get the project root directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(os.path.dirname(current_dir))
        
        # Settings file path
        self.settings_file = os.path.join(self.project_root, "settings.json")
        
        # Default settings
        self.default_settings = {
            "window": {
                "width": 800,
                "height": 600,
                "x": 100,
                "y": 100
            },
            "editor": {
                "font_family": "Arial",
                "font_size": 12,
                "tab_size": 4,
                "auto_save": False,
                "auto_save_interval": 5  # minutes
            },
            "files": {
                "default_save_directory": os.path.join(self.project_root, "data"),
                "default_extension": "txt",
                "recent_files": []
            },
            "appearance": {
                "theme": "light"  # light or dark
            },
            "ai": {
                "huggingface_api_key": "",
                "huggingface_summarization_model_id": "facebook/bart-large-cnn", # Default model ID
                "huggingface_text_generation_model_id": "gpt2"  # Default text generation model ID
            }
        }
        
        # Current settings
        self.config = self.load_settings()
        
    def load_settings(self):
        """
        Load settings from the settings file.
        
        Returns:
            dict: The loaded settings, or default settings if the file doesn't exist.
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as file:
                    settings = json.load(file)
                logger.info("Settings loaded from file")
                
                # Merge with default settings to ensure all keys exist
                merged_settings = self.default_settings.copy()
                self._deep_update(merged_settings, settings)
                return merged_settings
            else:
                logger.info("Settings file not found, using defaults")
                return self.default_settings.copy()
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            return self.default_settings.copy()
    
    def save_settings(self):
        """Save current settings to the settings file."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as file:
                json.dump(self.config, file, indent=4)
            logger.info("Settings saved to file")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            return False
    
    def get(self, section, key, default=None):
        """
        Get a setting value.
        
        Args:
            section (str): The settings section (e.g., 'window', 'editor').
            key (str): The setting key within the section.
            default: The default value to return if the setting doesn't exist.
            
        Returns:
            The setting value, or the default if not found.
        """
        try:
            return self.config[section][key]
        except KeyError:
            return default
    
    def set(self, section, key, value):
        """
        Set a setting value.
        
        Args:
            section (str): The settings section (e.g., 'window', 'editor').
            key (str): The setting key within the section.
            value: The value to set.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if section not in self.config:
                self.config[section] = {}
            
            self.config[section][key] = value
            return True
        except Exception as e:
            logger.error(f"Error setting {section}.{key}: {str(e)}")
            return False
    
    def add_recent_file(self, file_path):
        """
        Add a file to the recent files list.
        
        Args:
            file_path (str): Path to the file to add.
        """
        recent_files = self.config["files"]["recent_files"]
        
        # Remove the file if it's already in the list
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add the file to the beginning of the list
        recent_files.insert(0, file_path)
        
        # Keep only the 10 most recent files
        self.config["files"]["recent_files"] = recent_files[:10]
        
        # Save the settings
        self.save_settings()
    
    def _deep_update(self, target, source):
        """
        Recursively update a dictionary.
        
        Args:
            target (dict): The dictionary to update.
            source (dict): The dictionary with updates.
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value

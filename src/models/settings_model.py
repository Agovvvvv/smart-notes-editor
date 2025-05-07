#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model for application settings management.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

class SettingsModel:
    """Model for application settings management."""
    
    def __init__(self, settings_file=None):
        """Initialize the settings model."""
        self.settings_file = settings_file or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "settings.json"
        )
        self.settings = {}
        self.load_settings()
    
    def load_settings(self):
        """Load settings from the settings file."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
                logger.info(f"Settings loaded from {self.settings_file}")
            else:
                logger.info(f"Settings file {self.settings_file} not found, using defaults")
                self.settings = self._get_default_settings()
                self.save_settings()
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            self.settings = self._get_default_settings()
    
    def save_settings(self):
        """Save settings to the settings file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            logger.info(f"Settings saved to {self.settings_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            return False
    
    def get(self, section, key, default=None):
        """Get a setting value."""
        if section not in self.settings:
            return default
        if key not in self.settings[section]:
            return default
        return self.settings[section][key]
    
    def set(self, section, key, value):
        """Set a setting value."""
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section][key] = value
    
    def add_recent_file(self, file_path):
        """Add a file to the recent files list."""
        if 'recent_files' not in self.settings:
            self.settings['recent_files'] = []
        
        # Remove the file if it already exists in the list
        if file_path in self.settings['recent_files']:
            self.settings['recent_files'].remove(file_path)
        
        # Add the file to the beginning of the list
        self.settings['recent_files'].insert(0, file_path)
        
        # Limit the list to 10 items
        self.settings['recent_files'] = self.settings['recent_files'][:10]
        
        # Save the settings
        self.save_settings()
    
    def get_recent_files(self):
        """Get the list of recent files."""
        return self.settings.get('recent_files', [])
    
    def _get_default_settings(self):
        """Get the default settings."""
        return {
            "window": {
                "width": 800,
                "height": 600,
                "x": 100,
                "y": 100
            },
            "files": {
                "default_extension": "txt",
                "default_save_directory": os.path.expanduser("~/Documents")
            },
            "ai": {
                "model": "default",
                "summarization_length": "medium"
            },
            "recent_files": []
        }

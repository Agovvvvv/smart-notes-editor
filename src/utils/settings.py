#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Settings utility for the Smart Contextual Notes Editor.
Handles loading and saving application settings.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

class Settings:
    """Handles application settings."""
    
    MAX_RECENT_WORKSPACES = 5
    
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
                "backend": "local",  # Options: local, huggingface_api, google_gemini
                "huggingface_api_key": "",
                "huggingface_summarization_model_id": "facebook/bart-large-cnn", # Default model ID
                "huggingface_text_generation_model_id": "gpt2",  # Default text generation model ID
                "google_api_key": "",
                "max_links_for_qna": 3 # Default number of links to fetch for Q&A
            },
            "enhancement_templates": {}, 
            "workspaces": {
                "list": [],  # List of dict: {'name': str, 'path': str}
                "active_name": None,
                "recent_workspaces_names": [] # List of recently opened workspace names (max 5)
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
    
    def get_enhancement_templates(self):
        """Get all enhancement templates.

        Returns:
            dict: A dictionary of template_name: prompt_text.
        """
        return self.config.get("enhancement_templates", {})

    def save_enhancement_template(self, template_name: str, prompt_text: str):
        """Save or update an enhancement template.

        Args:
            template_name (str): The name of the template.
            prompt_text (str): The prompt text for the template.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not template_name.strip() or not prompt_text.strip():
            logger.warning("Attempted to save an empty template name or prompt.")
            return False
        try:
            if "enhancement_templates" not in self.config:
                self.config["enhancement_templates"] = {}
            self.config["enhancement_templates"][template_name] = prompt_text
            return self.save_settings()
        except Exception as e:
            logger.error(f"Error saving enhancement template '{template_name}': {str(e)}")
            return False

    def delete_enhancement_template(self, template_name: str):
        """Delete an enhancement template.

        Args:
            template_name (str): The name of the template to delete.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if "enhancement_templates" in self.config and template_name in self.config["enhancement_templates"]:
                del self.config["enhancement_templates"][template_name]
                return self.save_settings()
            else:
                logger.warning(f"Attempted to delete non-existent template: {template_name}")
                return False # Or True if not finding it is acceptable for deletion
        except Exception as e:
            logger.error(f"Error deleting enhancement template '{template_name}': {str(e)}")
            return False

    def get_ai_backend_is_api(self) -> bool:
        """Check if the currently selected AI backend is API-based."""
        backend = self.get("ai", "backend", "local")
        return backend in ["huggingface_api", "google_gemini"]

    def get_workspaces(self) -> list:
        """Get the list of all configured workspaces."""
        return self.config.get("workspaces", {}).get("list", [])

    def add_workspace(self, name: str, path: str) -> bool:
        """Add a new workspace. Ensures name is unique."""
        if not name or not path:
            logger.warning("Workspace name and path cannot be empty.")
            return False

        workspaces = self.get_workspaces()
        if any(ws['name'] == name for ws in workspaces):
            logger.warning(f"Workspace with name '{name}' already exists.")
            return False

        if "workspaces" not in self.config:
            self.config["workspaces"] = {"list": [], "active_name": None}
        elif "list" not in self.config["workspaces"]:
            self.config["workspaces"]["list"] = []

        self.config["workspaces"]["list"].append({"name": name, "path": path})
        # If this is the first workspace, set it as active
        if len(self.config["workspaces"]["list"]) == 1:
            self.set_active_workspace_name(name) # This will call save_settings
            return True # set_active_workspace_name already saved
        return self.save_settings()

    def remove_workspace(self, name: str) -> bool:
        """Remove a workspace by its name."""
        workspaces = self.get_workspaces()
        updated_workspaces = [ws for ws in workspaces if ws['name'] != name]

        if len(workspaces) == len(updated_workspaces):
            logger.warning(f"Workspace with name '{name}' not found for removal.")
            return False

        self.config["workspaces"]["list"] = updated_workspaces

        # If the removed workspace was active, clear the active workspace name
        active_name = self.get_active_workspace_name()
        if active_name == name:
            self.config["workspaces"]["active_name"] = None

        return self.save_settings()

    def get_active_workspace_name(self) -> str | None:
        """Get the name of the currently active workspace."""
        return self.config.get("workspaces", {}).get("active_name", None)

    def set_active_workspace_name(self, name: str | None) -> bool:
        """Set the active workspace. Pass None to deactivate all."""
        if 'workspaces' not in self.config:
            self.config['workspaces'] = {'list': [], 'active_name': None, 'recent_workspaces_names': []}

        if name is None:
            self.config['workspaces']['active_name'] = None
            logger.info("Active workspace cleared (set to None).")
            # No need to add None to recents
            return self.save_settings()

        workspaces = self.get_workspaces() # Assuming this uses self.config
        if any(ws['name'] == name for ws in workspaces):
            self.config['workspaces']['active_name'] = name
            self.add_to_recent_workspaces(name) # Add to recents when set active
            logger.info(f"Active workspace set to: {name}")
            return self.save_settings()
        
        logger.warning(f"Attempted to set non-existent workspace '{name}' as active.")
        return False

    def get_workspace_path(self, workspace_name: str) -> str | None:
        """Get the path of a workspace by its name."""
        workspaces = self.get_workspaces()
        for ws in workspaces:
            if ws['name'] == workspace_name:
                return ws['path']
        logger.warning(f"Path not found for workspace: {workspace_name}")
        return None

    def _deep_update(self, target_dict, source_dict):
        """Recursively update a dictionary with values from another dictionary."""
        for key, value in source_dict.items():
            if isinstance(value, dict) and key in target_dict and isinstance(target_dict[key], dict):
                self._deep_update(target_dict[key], value)
            else:
                target_dict[key] = value

    def get_recent_workspaces_names(self) -> list[str]:
        """Returns a list of recent workspace names."""
        return self.config.get('workspaces', {}).get('recent_workspaces_names', [])

    def add_to_recent_workspaces(self, workspace_name: str):
        """Adds a workspace name to the top of the recent list, managing size and duplicates."""
        if 'workspaces' not in self.config:
            self.config['workspaces'] = {}
        if 'recent_workspaces_names' not in self.config['workspaces']:
            self.config['workspaces']['recent_workspaces_names'] = []

        recent_list = self.config['workspaces']['recent_workspaces_names']
        
        # Remove if already exists to move it to the top
        if workspace_name in recent_list:
            recent_list.remove(workspace_name)
        
        # Add to the beginning (most recent)
        recent_list.insert(0, workspace_name)
        
        # Trim the list if it exceeds max size
        self.config['workspaces']['recent_workspaces_names'] = recent_list[:self.MAX_RECENT_WORKSPACES]
        logger.debug(f"Recent workspaces updated: {self.config['workspaces']['recent_workspaces_names']}")
        # self.save() # Saving is handled by set_active_workspace_name or other higher-level calls

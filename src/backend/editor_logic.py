#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Editor logic for the Smart Contextual Notes Editor.
Handles file operations and text manipulation.
"""

import os
import logging
import shutil # Added for rmtree

logger = logging.getLogger(__name__)

class EditorLogic:
    """Handles the core logic for the text editor functionality."""
    
    def __init__(self):
        """Initialize the editor logic."""
        self.current_file = None
        logger.info("Editor logic initialized")
    
    def read_file(self, file_path):
        """
        Read content from a file.
        
        Args:
            file_path (str): Path to the file to read.
            
        Returns:
            str: The content of the file.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            IOError: If there is an error reading the file.
        """
        logger.info(f"Reading file: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                logger.info(f"Successfully read file: {file_path}")
                return content
        except IOError as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise
    
    def write_file(self, file_path, content):
        """
        Write content to a file.
        
        Args:
            file_path (str): Path to the file to write.
            content (str): Content to write to the file.
            
        Returns:
            bool: True if successful, False otherwise.
            
        Raises:
            IOError: If there is an error writing to the file.
        """
        logger.info(f"Writing to file: {file_path}")
        
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Created directory: {directory}")
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
                
            logger.info(f"Successfully wrote to file: {file_path}")
            return True
        except IOError as e:
            logger.error(f"Error writing to file {file_path}: {str(e)}")
            raise
    
    def get_file_extension(self, file_path):
        """
        Get the extension of a file.
        
        Args:
            file_path (str): Path to the file.
            
        Returns:
            str: The file extension (without the dot).
        """
        _, ext = os.path.splitext(file_path)
        return ext[1:] if ext else ""
    
    def get_default_save_directory(self):
        """
        Get the default directory for saving files.
        
        Returns:
            str: Path to the default save directory.
        """
        # Get the project root directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        
        # Default save directory is the 'data' folder in the project root
        save_dir = os.path.join(project_root, "data")
        
        # Create the directory if it doesn't exist
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            logger.info(f"Created default save directory: {save_dir}")
        
        return save_dir

    def create_empty_file(self, file_path):
        """
        Create an empty file at the specified path.

        Args:
            file_path (str): The full path where the file should be created.

        Returns:
            tuple: (bool, str) indicating success and a message or error string.
        """
        logger.info(f"Attempting to create empty file: {file_path}")
        try:
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Created directory for new file: {directory}")
            
            if os.path.exists(file_path):
                logger.warning(f"File already exists: {file_path}")
                return False, f"File already exists: {os.path.basename(file_path)}"

            with open(file_path, 'w', encoding='utf-8') as _: # Changed f to _ to indicate unused variable
                pass  # Create an empty file
            logger.info(f"Successfully created empty file: {file_path}")
            return True, f"File '{os.path.basename(file_path)}' created successfully."
        except IOError as e:
            logger.error(f"IOError creating file {file_path}: {str(e)}")
            return False, f"Error creating file: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error creating file {file_path}: {str(e)}")
            return False, f"Unexpected error: {str(e)}"

    def create_folder(self, folder_path):
        """
        Create a new folder at the specified path.

        Args:
            folder_path (str): The full path where the folder should be created.

        Returns:
            tuple: (bool, str) indicating success and a message or error string.
        """
        logger.info(f"Attempting to create folder: {folder_path}")
        try:
            if os.path.exists(folder_path):
                logger.warning(f"Folder already exists: {folder_path}")
                return False, f"Folder already exists: {os.path.basename(folder_path)}"
            
            os.makedirs(folder_path)
            logger.info(f"Successfully created folder: {folder_path}")
            return True, f"Folder '{os.path.basename(folder_path)}' created successfully."
        except OSError as e:
            logger.error(f"OSError creating folder {folder_path}: {str(e)}")
            return False, f"Error creating folder: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error creating folder {folder_path}: {str(e)}")
            return False, f"Unexpected error: {str(e)}"

    def rename_item(self, old_path, new_name):
        """
        Rename a file or folder.

        Args:
            old_path (str): The current full path of the item.
            new_name (str): The new name for the item (just the name, not the full path).

        Returns:
            tuple: (bool, str, Optional[str]) indicating success, a message, and the new_path if successful.
        """
        logger.info(f"Attempting to rename item: {old_path} to {new_name}")
        if not os.path.exists(old_path):
            logger.error(f"Item not found for rename: {old_path}")
            return False, "Item not found.", None
        
        if not new_name.strip():
            logger.warning("New name for rename is empty or whitespace.")
            return False, "New name cannot be empty.", None

        directory = os.path.dirname(old_path)
        new_path = os.path.join(directory, new_name)

        if os.path.exists(new_path):
            logger.warning(f"Target path already exists: {new_path}")
            return False, f"An item named '{new_name}' already exists in this location.", None
        
        try:
            os.rename(old_path, new_path)
            logger.info(f"Successfully renamed {old_path} to {new_path}")
            return True, f"Successfully renamed to '{new_name}'.", new_path
        except OSError as e:
            logger.error(f"OSError renaming {old_path} to {new_path}: {str(e)}")
            return False, f"Error renaming: {str(e)}", None
        except Exception as e:
            logger.error(f"Unexpected error renaming {old_path}: {str(e)}")
            return False, f"Unexpected error: {str(e)}", None

    def delete_item(self, item_path):
        """
        Delete a file or folder.

        Args:
            item_path (str): The full path of the item to delete.

        Returns:
            tuple: (bool, str) indicating success and a message or error string.
        """
        logger.info(f"Attempting to delete item: {item_path}")
        if not os.path.exists(item_path):
            logger.error(f"Item not found for deletion: {item_path}")
            return False, "Item not found."

        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                logger.info(f"Successfully deleted directory: {item_path}")
                return True, f"Folder '{os.path.basename(item_path)}' deleted successfully."
            else:
                os.remove(item_path)
                logger.info(f"Successfully deleted file: {item_path}")
                return True, f"File '{os.path.basename(item_path)}' deleted successfully."
        except OSError as e:
            logger.error(f"OSError deleting {item_path}: {str(e)}")
            return False, f"Error deleting: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error deleting {item_path}: {str(e)}")
            return False, f"Unexpected error: {str(e)}"

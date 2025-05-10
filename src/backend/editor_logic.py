#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Editor logic for the Smart Contextual Notes Editor.
Handles file operations and text manipulation.
"""

import os
import logging

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

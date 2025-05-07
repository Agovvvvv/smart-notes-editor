#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model for document data and operations.
"""

class DocumentModel:
    """Model for document data and operations."""
    
    def __init__(self):
        """Initialize the document model."""
        self.current_file = None
        self.unsaved_changes = False
        self.content = ""
    
    def set_content(self, content):
        """Set the document content."""
        self.content = content
        self.unsaved_changes = True
    
    def get_content(self):
        """Get the document content."""
        return self.content
    
    def set_current_file(self, file_path):
        """Set the current file path."""
        self.current_file = file_path
    
    def get_current_file(self):
        """Get the current file path."""
        return self.current_file
    
    def clear(self):
        """Clear the document."""
        self.content = ""
        self.current_file = None
        self.unsaved_changes = False
    
    def mark_saved(self):
        """Mark the document as saved."""
        self.unsaved_changes = False

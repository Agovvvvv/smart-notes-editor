#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for the editor logic module.
"""

import unittest
import os
import tempfile
from backend.editor_logic import EditorLogic

class TestEditorLogic(unittest.TestCase):
    """Test cases for the EditorLogic class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.editor_logic = EditorLogic()
        # Create a temporary directory for test files
        self.test_dir = tempfile.TemporaryDirectory()
        
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up temporary directory
        self.test_dir.cleanup()
    
    def test_save_and_load_file(self):
        """Test saving and loading a file."""
        # Create a test file path
        test_file_path = os.path.join(self.test_dir.name, "test_file.txt")
        
        # Test content
        test_content = "This is a test file.\nWith multiple lines.\n"
        
        # Save the file
        self.editor_logic.save_file(test_file_path, test_content)
        
        # Check that the file exists
        self.assertTrue(os.path.exists(test_file_path))
        
        # Load the file
        loaded_content = self.editor_logic.load_file(test_file_path)
        
        # Check that the loaded content matches the original
        self.assertEqual(loaded_content, test_content)
    
    def test_get_file_extension(self):
        """Test getting file extensions."""
        # Test with .txt file
        self.assertEqual(self.editor_logic.get_file_extension("file.txt"), ".txt")
        
        # Test with .md file
        self.assertEqual(self.editor_logic.get_file_extension("file.md"), ".md")
        
        # Test with no extension
        self.assertEqual(self.editor_logic.get_file_extension("file"), "")
        
        # Test with multiple dots
        self.assertEqual(self.editor_logic.get_file_extension("file.name.txt"), ".txt")
    
    def test_suggest_file_name(self):
        """Test suggesting file names based on content."""
        # Test with content that has a clear title
        content = "# My Test Document\nThis is a test."
        suggested_name = self.editor_logic.suggest_file_name(content)
        self.assertEqual(suggested_name, "My_Test_Document.md")
        
        # Test with content that has no clear title
        content = "This is just some text without a title."
        suggested_name = self.editor_logic.suggest_file_name(content)
        self.assertTrue(suggested_name.endswith(".txt"))
        self.assertGreater(len(suggested_name), 5)  # Should have a reasonable length

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for the context analyzer module.
"""

import unittest
from unittest.mock import patch, MagicMock
from backend import context_analyzer

class TestContextAnalyzer(unittest.TestCase):
    """Test cases for the context analyzer module."""
    
    def test_split_into_sentences(self):
        """Test splitting text into sentences."""
        # Test with simple sentences
        text = "This is a sentence. This is another sentence! Is this a question?"
        sentences = context_analyzer.split_into_sentences(text)
        self.assertEqual(len(sentences), 3)
        self.assertEqual(sentences[0], "This is a sentence")
        self.assertEqual(sentences[1], "This is another sentence")
        self.assertEqual(sentences[2], "Is this a question")
        
        # Test with newlines
        text = "Line one.\nLine two.\nLine three."
        sentences = context_analyzer.split_into_sentences(text)
        self.assertEqual(len(sentences), 3)
        
        # Test with empty text
        text = ""
        sentences = context_analyzer.split_into_sentences(text)
        self.assertEqual(len(sentences), 0)
    
    @patch('backend.context_analyzer._nlp_model')
    def test_extract_keywords(self, mock_nlp_model):
        """Test extracting keywords from text."""
        # Set up mock
        mock_doc = MagicMock()
        mock_tokens = []
        
        # Create mock tokens with different parts of speech
        for word, pos in [
            ("quantum", "NOUN"), 
            ("computing", "NOUN"),
            ("is", "AUX"),
            ("an", "DET"),
            ("important", "ADJ"),
            ("field", "NOUN")
        ]:
            mock_token = MagicMock()
            mock_token.text = word
            mock_token.pos_ = pos
            mock_token.is_stop = word in ["is", "an"]
            mock_tokens.append(mock_token)
        
        mock_doc.__iter__.return_value = mock_tokens
        mock_nlp_model.return_value = mock_doc
        
        # Test keyword extraction
        text = "Quantum computing is an important field"
        keywords = context_analyzer.extract_keywords(text, max_keywords=5)
        
        # Should extract nouns and adjectives that aren't stop words
        self.assertIn("quantum", keywords)
        self.assertIn("computing", keywords)
        self.assertIn("important", keywords)
        self.assertIn("field", keywords)
        self.assertNotIn("is", keywords)
        self.assertNotIn("an", keywords)
    
    @patch('backend.context_analyzer.calculate_semantic_similarity')
    def test_find_relevant_web_content(self, mock_calculate_similarity):
        """Test finding relevant web content."""
        # Set up mock for similarity calculation
        mock_calculate_similarity.return_value = 0.8  # High similarity
        
        # Mock the extract_entities and extract_keywords functions
        with patch('backend.context_analyzer.extract_entities') as mock_extract_entities, \
             patch('backend.context_analyzer.extract_keywords') as mock_extract_keywords:
            
            # Set up mocks
            mock_extract_entities.return_value = {"MISC": ["quantum", "computing"]}
            mock_extract_keywords.return_value = ["quantum", "computing", "qubits"]
            
            # Test data
            note_text = "Quantum computing uses qubits."
            web_results = [
                {
                    "title": "Quantum Computing",
                    "url": "https://example.com/quantum",
                    "content": "Quantum computing is revolutionary. It uses qubits instead of bits."
                },
                {
                    "title": "Unrelated Topic",
                    "url": "https://example.com/unrelated",
                    "content": "This has nothing to do with quantum computing."
                }
            ]
            
            # Call the function
            results = context_analyzer.find_relevant_web_content(
                note_text, web_results, max_suggestions=2
            )
            
            # Check results
            self.assertEqual(len(results), 2)  # Should have both results due to our mock
            self.assertEqual(results[0]["title"], "Quantum Computing")
            self.assertTrue(any("qubits" in s["sentence"] for s in results[0]["sentences"]))

if __name__ == "__main__":
    unittest.main()

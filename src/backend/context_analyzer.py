#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Context analyzer for the Smart Contextual Notes Editor.
Provides functions for analyzing notes and web content to generate contextual suggestions.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Union
import time

logger = logging.getLogger(__name__)

# Global variables for models
_sentence_transformer = None
_nlp_model = None
_model_loading_time = 0

def initialize_context_models(progress_callback=None):
    """
    Initialize models needed for context analysis.
    
    Args:
        progress_callback (callable): Optional callback function to report progress
        
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    global _sentence_transformer, _nlp_model, _model_loading_time
    
    try:
        if progress_callback:
            progress_callback(10)
            
        # Import libraries here to avoid loading them unless needed
        from sentence_transformers import SentenceTransformer
        import spacy
        
        start_time = time.time()
        logger.info("Loading sentence transformer model...")
        
        # Load sentence transformer model for semantic similarity
        _sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
        
        if progress_callback:
            progress_callback(50)
            
        # Load spaCy model for NER and keyword extraction
        logger.info("Loading spaCy model...")
        try:
            _nlp_model = spacy.load('en_core_web_sm')
        except OSError:
            logger.info("Downloading spaCy model...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], 
                          check=True)
            _nlp_model = spacy.load('en_core_web_sm')
        
        if progress_callback:
            progress_callback(90)
            
        _model_loading_time = time.time() - start_time
        logger.info(f"Context analysis models loaded in {_model_loading_time:.2f} seconds")
        
        if progress_callback:
            progress_callback(100)
            
        return True
        
    except ImportError as e:
        logger.error(f"Error importing required libraries: {str(e)}")
        logger.error("Please install required libraries: pip install sentence-transformers spacy")
        return False
        
    except Exception as e:
        logger.error(f"Error initializing context models: {str(e)}")
        return False

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract named entities from text using spaCy.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        Dict[str, List[str]]: Dictionary of entity types and their values
    """
    global _nlp_model
    
    if _nlp_model is None:
        logger.warning("NLP model not initialized. Initializing now...")
        initialize_context_models()
        
    if _nlp_model is None:
        logger.error("Failed to initialize NLP model")
        return {"error": ["NLP model not available"]}
    
    try:
        entities = {"PERSON": [], "ORG": [], "GPE": [], "DATE": [], "MISC": []}
        
        # Process the text with spaCy
        doc = _nlp_model(text)
        
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in entities:
                if ent.text not in entities[ent.label_]:
                    entities[ent.label_].append(ent.text)
            else:
                if "MISC" not in entities:
                    entities["MISC"] = []
                if ent.text not in entities["MISC"]:
                    entities["MISC"].append(ent.text)
        
        # Remove empty categories
        return {k: v for k, v in entities.items() if v}
        
    except Exception as e:
        logger.error(f"Error extracting entities: {str(e)}")
        return {"error": [str(e)]}

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract important keywords from text using spaCy.
    
    Args:
        text (str): The text to analyze
        max_keywords (int): Maximum number of keywords to extract
        
    Returns:
        List[str]: List of extracted keywords
    """
    global _nlp_model
    
    if _nlp_model is None:
        logger.warning("NLP model not initialized. Initializing now...")
        initialize_context_models()
        
    if _nlp_model is None:
        logger.error("Failed to initialize NLP model")
        return []
    
    try:
        # Process the text with spaCy
        doc = _nlp_model(text)
        
        # Extract nouns, proper nouns, and adjectives as keywords
        keywords = []
        for token in doc:
            if token.pos_ in ["NOUN", "PROPN", "ADJ"] and not token.is_stop and len(token.text) > 3:
                keywords.append(token.text.lower())
        
        # Count occurrences and get the most frequent ones
        keyword_counts = {}
        for keyword in keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Sort by frequency
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Return the top keywords
        return [keyword for keyword, _ in sorted_keywords[:max_keywords]]
        
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        return []

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity between two texts using sentence transformers.
    
    Args:
        text1 (str): First text
        text2 (str): Second text
        
    Returns:
        float: Similarity score between 0 and 1
    """
    global _sentence_transformer
    
    if _sentence_transformer is None:
        logger.warning("Sentence transformer not initialized. Initializing now...")
        initialize_context_models()
        
    if _sentence_transformer is None:
        logger.error("Failed to initialize sentence transformer")
        return 0.0
    
    try:
        # Encode the texts
        embedding1 = _sentence_transformer.encode(text1, convert_to_tensor=True)
        embedding2 = _sentence_transformer.encode(text2, convert_to_tensor=True)
        
        # Calculate cosine similarity
        from torch.nn import functional as F
        similarity = F.cosine_similarity(embedding1.unsqueeze(0), embedding2.unsqueeze(0)).item()
        
        return similarity
        
    except Exception as e:
        logger.error(f"Error calculating semantic similarity: {str(e)}")
        return 0.0

def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.
    
    Args:
        text (str): The text to split
        
    Returns:
        List[str]: List of sentences
    """
    # Simple sentence splitting by common sentence terminators
    # This could be improved with a more sophisticated approach
    text = text.replace('\n', ' ')
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def generate_suggestions(note_text: str, progress_callback=None) -> Dict[str, List[str]]:
    """
    Generate contextual suggestions based on note text.
    (Web-dependent parts have been removed)
    
    Args:
        note_text (str): The note text
        progress_callback (callable): Optional callback function to report progress
        
    Returns:
        Dict: Dictionary with 'content_suggestions' and 'missing_information' (currently empty lists)
    """
    if progress_callback:
        progress_callback(10) # Start progress

    # Extract entities and keywords from the note
    # These can be used in the future if suggestion logic is redefined
    # logger.debug(f"Extracted entities for suggestions: {extract_entities(note_text)}")
    # logger.debug(f"Extracted keywords for suggestions: {extract_keywords(note_text)}")

    if progress_callback:
        progress_callback(50) # Arbitrary progress point after local analysis

    # Placeholder for future non-web-based suggestion logic
    content_suggestions = []
    missing_information = []

    # Simulate some processing for progress if needed
    # For example, if there were complex local analysis for suggestions:
    # time.sleep(0.1) 

    if progress_callback:
        progress_callback(100) # End progress

    return {
        'content_suggestions': content_suggestions,
        'missing_information': missing_information
    }

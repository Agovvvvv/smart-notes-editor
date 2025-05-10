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

def find_relevant_web_content(note_text: str, web_results: List[Dict[str, str]], 
                             max_suggestions: int = 5, progress_callback=None) -> List[Dict[str, Union[str, float]]]:
    """
    Find the most relevant content from web results based on the note text.
    
    Args:
        note_text (str): The note text to compare against
        web_results (List[Dict[str, str]]): List of web results, each with 'title', 'url', and 'content'
        max_suggestions (int): Maximum number of suggestions to return
        progress_callback (callable): Optional callback function to report progress
        
    Returns:
        List[Dict[str, Union[str, float]]]: List of relevant content with similarity scores
    """
    if progress_callback:
        progress_callback(10)
    
    # Extract entities and keywords from the note
    note_entities = extract_entities(note_text)
    note_keywords = extract_keywords(note_text)
    
    if progress_callback:
        progress_callback(30)
    
    # Split note into sentences for comparison
    note_sentences = split_into_sentences(note_text)
    
    # Store relevant content
    relevant_content = []
    
    # Process each web result
    for i, result in enumerate(web_results):
        if progress_callback:
            # Update progress from 30% to 90% based on web result processing
            progress = 30 + int(60 * (i + 1) / len(web_results))
            progress_callback(progress)
        
        try:
            # Skip results with errors or no content
            if result.get('error') or not result.get('content'):
                continue
            
            # Extract entities and keywords from the web content
            web_content = result['content']
            web_entities = extract_entities(web_content)
            web_keywords = extract_keywords(web_content)
            
            # Split web content into sentences
            web_sentences = split_into_sentences(web_content)
            
            # Find matching entities
            matching_entities = []
            for entity_type, entities in note_entities.items():
                if entity_type in web_entities:
                    for entity in entities:
                        if entity in web_entities[entity_type]:
                            matching_entities.append(entity)
            
            # Check for matching keywords
            has_matching_keywords = any(keyword in web_keywords for keyword in note_keywords)
            
            # Calculate semantic similarity for each web sentence with each note sentence
            # and find the most relevant sentences
            relevant_sentences = []
            
            for web_sentence in web_sentences:
                # Skip very short sentences
                if len(web_sentence.split()) < 5:
                    continue
                
                # Check if the sentence contains any matching entities or keywords
                contains_entity = any(entity.lower() in web_sentence.lower() for entity in matching_entities)
                contains_keyword = any(keyword.lower() in web_sentence.lower() for keyword in note_keywords)
                
                # If it contains a match or we have matching keywords in general, calculate similarity with the note
                if contains_entity or contains_keyword or has_matching_keywords:
                    # Calculate average similarity with all note sentences
                    similarities = []
                    for note_sentence in note_sentences:
                        if len(note_sentence.split()) >= 5:  # Skip very short sentences
                            similarity = calculate_semantic_similarity(note_sentence, web_sentence)
                            similarities.append(similarity)
                    
                    # Use the maximum similarity
                    if similarities:
                        max_similarity = max(similarities)
                        
                        # Only include sentences with good similarity
                        if max_similarity > 0.3:  # Threshold can be adjusted
                            relevant_sentences.append({
                                'sentence': web_sentence,
                                'similarity': max_similarity,
                                'contains_entity': contains_entity,
                                'contains_keyword': contains_keyword
                            })
            
            # Sort by similarity score
            relevant_sentences.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Take the top sentences
            top_sentences = relevant_sentences[:3]  # Limit to 3 sentences per source
            
            if top_sentences:
                # Add to the overall relevant content
                relevant_content.append({
                    'title': result['title'],
                    'url': result['url'],
                    'sentences': top_sentences,
                    'overall_score': sum(s['similarity'] for s in top_sentences) / len(top_sentences)
                })
        
        except Exception as e:
            logger.error(f"Error processing web result: {str(e)}")
            continue
    
    # Sort by overall score
    relevant_content.sort(key=lambda x: x['overall_score'], reverse=True)
    
    # Limit to max_suggestions
    relevant_content = relevant_content[:max_suggestions]
    
    if progress_callback:
        progress_callback(100)
    
    return relevant_content

def generate_suggestions(note_text: str, web_results: List[Dict[str, str]], 
                        progress_callback=None) -> Dict[str, Union[List[Dict[str, Union[str, float]]], List[str]]]:
    """
    Generate contextual suggestions based on note text and web results.
    
    Args:
        note_text (str): The note text
        web_results (List[Dict[str, str]]): List of web results
        progress_callback (callable): Optional callback function to report progress
        
    Returns:
        Dict: Dictionary with 'content_suggestions' and 'missing_information'
    """
    if progress_callback:
        progress_callback(10)
    
    # Find relevant web content
    relevant_content = find_relevant_web_content(
        note_text, 
        web_results, 
        progress_callback=lambda p: progress_callback(10 + int(p * 0.7))
    )
    
    if progress_callback:
        progress_callback(80)
    
    # Extract entities and keywords from the note
    note_entities = extract_entities(note_text)
    note_keywords = extract_keywords(note_text)
    
    # Identify potentially missing information
    missing_information = []
    
    # Check for entities in web content that are related but not in notes
    all_web_entities = {}
    for result in web_results:
        if result.get('error') or not result.get('content'):
            continue
        
        web_entities = extract_entities(result['content'])
        for entity_type, entities in web_entities.items():
            if entity_type not in all_web_entities:
                all_web_entities[entity_type] = []
            all_web_entities[entity_type].extend(entities)
    
    # Find entities that appear in web content but not in notes
    for entity_type, entities in all_web_entities.items():
        if entity_type in note_entities:
            for entity in entities:
                if entity not in note_entities[entity_type] and entity not in missing_information:
                    # Check if this entity is related to any note keyword
                    for keyword in note_keywords:
                        if keyword.lower() in entity.lower() or entity.lower() in keyword.lower():
                            missing_information.append(f"Consider adding information about {entity}")
                            break
    
    if progress_callback:
        progress_callback(100)
    
    return {
        'content_suggestions': relevant_content,
        'missing_information': missing_information[:5]  # Limit to 5 suggestions
    }

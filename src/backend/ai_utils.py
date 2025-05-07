#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI utilities for the Smart Contextual Notes Editor.
Provides functions for text summarization and context analysis.
"""

import logging
import os
import time
from typing import Dict, List, Optional, Tuple, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables to store loaded models
_summarizer = None
_tokenizer = None
_model_loading_time = 0
_current_model_name = None

# Available summarization models with their characteristics
SUMMARIZATION_MODELS = {
    "google/pegasus-xsum": {
        "description": "Fast and efficient summarization model by Google",
        "max_length": 512,
        "quality": "High",
        "speed": "Fast"
    },
    "facebook/bart-large-cnn": {
        "description": "BART model fine-tuned on CNN articles",
        "max_length": 1024,
        "quality": "Good",
        "speed": "Medium"
    },
    "sshleifer/distilbart-cnn-12-6": {
        "description": "Distilled version of BART, smaller and faster",
        "max_length": 1024,
        "quality": "Medium",
        "speed": "Fast"
    },
    "philschmid/flan-t5-base-samsum": {
        "description": "T5 model fine-tuned on dialogue summarization",
        "max_length": 512,
        "quality": "High for conversations",
        "speed": "Medium"
    }
}

# Default model
DEFAULT_MODEL = "google/pegasus-xsum"

def initialize_ai_models(model_name=None, force_reload=False, progress_callback=None):
    """
    Initialize AI models for summarization and NLP tasks.
    
    Args:
        model_name (str): Name of the model to load. If None, uses the default model
        force_reload (bool): Whether to force reload models even if already loaded
        progress_callback (callable): Optional callback function to report progress
        
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    global _summarizer, _tokenizer, _model_loading_time, _current_model_name
    
    # Use default model if none specified
    if model_name is None:
        model_name = DEFAULT_MODEL
    
    # If models are already loaded with the requested model and we're not forcing a reload, return immediately
    if _summarizer is not None and _current_model_name == model_name and not force_reload:
        logger.info(f"AI model '{model_name}' already loaded, skipping initialization")
        return True
    
    try:
        # Import transformers here to avoid loading it unless needed
        from transformers import pipeline, AutoTokenizer
        
        if progress_callback:
            progress_callback(10)
            
        logger.info(f"Loading summarization model '{model_name}'...")
        start_time = time.time()
        
        # Load tokenizer
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        if progress_callback:
            progress_callback(40)
            
        # Load summarization pipeline
        _summarizer = pipeline(
            "summarization",
            model=model_name,
            tokenizer=_tokenizer
        )
        
        # Store the current model name
        _current_model_name = model_name
        
        if progress_callback:
            progress_callback(90)
            
        _model_loading_time = time.time() - start_time
        logger.info(f"Summarization model '{model_name}' loaded in {_model_loading_time:.2f} seconds")
        
        if progress_callback:
            progress_callback(100)
            
        return True
        
    except ImportError as e:
        logger.error(f"Error importing transformers library: {str(e)}")
        logger.error("Please install the transformers library: pip install transformers")
        return False
        
    except Exception as e:
        logger.error(f"Error initializing AI models: {str(e)}")
        return False

def generate_summary(text: str, model_name=None, max_length: int = 150, min_length: int = 40, 
                    progress_callback=None) -> str:
    """
    Generate a summary of the given text.
    
    Args:
        text (str): The text to summarize
        model_name (str): Name of the model to use. If None, uses the current or default model
        max_length (int): Maximum length of the summary in tokens
        min_length (int): Minimum length of the summary in tokens
        progress_callback (callable): Optional callback function to report progress
        
    Returns:
        str: The generated summary
        
    Raises:
        ValueError: If the text is too short to summarize
        RuntimeError: If the summarization model is not initialized
    """
    global _summarizer, _current_model_name
    
    # Check if text is too short to summarize
    if len(text.split()) < 50:
        logger.warning("Text too short to summarize meaningfully")
        raise ValueError("Text is too short to generate a meaningful summary (less than 50 words)")
    
    # Initialize models if not already done or if a different model is requested
    if _summarizer is None or (model_name is not None and model_name != _current_model_name):
        logger.info(f"{'Initializing' if _summarizer is None else 'Switching to'} summarization model {model_name or DEFAULT_MODEL}...")
        if progress_callback:
            progress_callback(10)
            
        success = initialize_ai_models(
            model_name=model_name,
            progress_callback=lambda p: progress_callback(int(10 + p * 0.4))
        )
        if not success:
            logger.error("Failed to initialize summarization model")
            raise RuntimeError("Failed to initialize summarization model")
    
    if progress_callback:
        progress_callback(50)
    
    try:
        logger.info(f"Generating summary using model '{_current_model_name}' for text of length {len(text)}")
        
        # Generate summary
        summary = _summarizer(text, max_length=max_length, min_length=min_length, 
                            do_sample=False)
        
        if progress_callback:
            progress_callback(90)
            
        # Extract summary text
        summary_text = summary[0]['summary_text']
        
        logger.info(f"Summary generated, length: {len(summary_text)}")
        
        if progress_callback:
            progress_callback(100)
            
        return summary_text
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise RuntimeError(f"Error generating summary: {str(e)}")

def chunk_long_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split long text into smaller chunks for processing.
    
    Args:
        text (str): The text to split
        chunk_size (int): Maximum size of each chunk in characters
        overlap (int): Number of characters to overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
        
    chunks = []
    start = 0
    
    while start < len(text):
        # Find the end of the chunk
        end = min(start + chunk_size, len(text))
        
        # If we're not at the end of the text, try to find a sentence boundary
        if end < len(text):
            # Look for sentence boundaries (., !, ?) followed by a space
            for sentence_end in ['. ', '! ', '? ']:
                last_sentence = text[start:end].rfind(sentence_end)
                if last_sentence != -1:
                    end = start + last_sentence + 2  # +2 to include the sentence end and space
                    break
        
        # Add the chunk to the list
        chunks.append(text[start:end])
        
        # Move to the next chunk, with overlap
        start = max(0, end - overlap)
    
    return chunks

def summarize_long_text(text: str, model_name=None, max_length: int = 150, min_length: int = 40,
                       progress_callback=None) -> str:
    """
    Summarize long text by chunking it and summarizing each chunk.
    
    Args:
        text (str): The text to summarize
        model_name (str): Name of the model to use. If None, uses the current or default model
        max_length (int): Maximum length of the final summary in tokens
        min_length (int): Minimum length of the final summary in tokens
        progress_callback (callable): Optional callback function to report progress
        
    Returns:
        str: The generated summary
    """
    # Check if text is short enough for direct summarization
    if len(text) < 5000:  # Arbitrary threshold, adjust based on model capabilities
        return generate_summary(text, model_name, max_length, min_length, progress_callback)
    
    logger.info(f"Text is long ({len(text)} chars), chunking for summarization")
    
    # Chunk the text
    chunks = chunk_long_text(text)
    
    if progress_callback:
        progress_callback(10)
    
    # Summarize each chunk
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        logger.info(f"Summarizing chunk {i+1}/{len(chunks)}")
        
        try:
            summary = generate_summary(
                chunk,
                model_name=model_name,
                max_length=max(30, max_length // 2),  # Shorter summaries for chunks
                min_length=min(20, min_length // 2)   # Shorter minimum for chunks
            )
            chunk_summaries.append(summary)
            
            if progress_callback:
                # Report progress from 10% to 80% based on chunk progress
                progress = 10 + int(70 * (i + 1) / len(chunks))
                progress_callback(progress)
                
        except Exception as e:
            logger.warning(f"Error summarizing chunk {i+1}: {str(e)}")
            # If we can't summarize a chunk, use the first few sentences
            sentences = chunk.split('. ')
            chunk_summaries.append('. '.join(sentences[:3]) + '.')
    
    # Combine chunk summaries
    combined_summary = ' '.join(chunk_summaries)
    
    if progress_callback:
        progress_callback(85)
    
    # Generate a final summary from the combined chunk summaries
    try:
        final_summary = generate_summary(
            combined_summary,
            model_name=model_name,
            max_length=max_length,
            min_length=min_length
        )
        
        if progress_callback:
            progress_callback(100)
            
        return final_summary
        
    except Exception as e:
        logger.warning(f"Error generating final summary: {str(e)}")
        
        # If final summarization fails, return the combined chunk summaries
        if progress_callback:
            progress_callback(100)
            
        return combined_summary


def get_available_models():
    """
    Get a list of available summarization models.
    
    Returns:
        dict: Dictionary of available models with their descriptions
    """
    return SUMMARIZATION_MODELS


def get_current_model():
    """
    Get the name of the currently loaded model.
    
    Returns:
        str: Name of the current model, or None if no model is loaded
    """
    global _current_model_name
    return _current_model_name

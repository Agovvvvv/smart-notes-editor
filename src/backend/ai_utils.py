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

import requests
import json
from transformers import pipeline # Added import
import spacy # Added for entity extraction

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions


logger = logging.getLogger(__name__)

def summarize_text_local(text: str, model_id: str = "facebook/bart-large-cnn", progress_callback=None):
    """
    Generate a summary of the given text using a local Hugging Face model via pipeline.

    Args:
        text (str): The text to summarize.
        model_id (str, optional): The model ID to use for summarization. 
                                Defaults to "facebook/bart-large-cnn".
        progress_callback (callable, optional): Callback function to report progress.

    Returns:
        str: The generated summary.

    Raises:
        RuntimeError: If there's an error loading the model or during summarization.
    """
    logger.info(f"Starting local summarization with model: {model_id} for text of length: {len(text)}")
    try:
        if progress_callback:
            progress_callback(0)  # Indicate start

        # Initialize the summarization pipeline
        # device=-1 ensures CPU usage, change to 0 for GPU if available and configured
        logger.info(f"Loading summarization model: {model_id}")
        summarizer = pipeline("summarization", model=model_id, device=-1) 
        logger.info(f"Model {model_id} loaded successfully.")
        
        # Perform summarization
        # Parameters like max_length, min_length can be adjusted based on desired output
        # These are common defaults for bart-large-cnn
        summary_output = summarizer(text, max_length=150, min_length=30, do_sample=False)
        
        if not summary_output or not isinstance(summary_output, list) or "summary_text" not in summary_output[0]:
            logger.error(f"Unexpected output format from summarization pipeline: {summary_output}")
            raise RuntimeError("Local summarization failed to produce expected output format.")

        summary = summary_output[0]["summary_text"]
        logger.info(f"Local summary generated. Length: {len(summary)}")
        
        if progress_callback:
            progress_callback(100)  # Indicate completion
        return summary

    except ImportError as e:
        logger.error(f"Transformers library not found or import error: {e}")
        if progress_callback: progress_callback(100)
        raise RuntimeError(f"Transformers library not found. Please ensure it's installed. Error: {e}")
    except Exception as e:
        logger.error(f"Error during local summarization with model {model_id}: {e}")
        if progress_callback:
            progress_callback(100)  # Indicate completion (with error)
        import traceback
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Failed to summarize text locally with model {model_id}: {e}")

def summarize_text_hf_api(text: str, api_key: str, model_id: str = "facebook/bart-large-cnn", timeout: int = 120, progress_callback=None):
    """
    Generate a summary of the given text using the Hugging Face Inference API.

    Args:
        text (str): The text to summarize.
        api_key (str): The Hugging Face API key.
        model_id (str, optional): The model ID to use for summarization. 
                                Defaults to "facebook/bart-large-cnn".
        timeout (int, optional): Timeout for the API request in seconds. Defaults to 120.
        progress_callback (callable, optional): Callback function to report progress. 
                                               Accepted for Worker compatibility.

    Returns:
        str: The generated summary.

    Raises:
        ValueError: If the API key is missing.
        RuntimeError: If there's an error calling the API or processing the response.
    """
    if not api_key:
        logger.error("Hugging Face API key is missing.")
        raise ValueError("API key for Hugging Face Inference API is required.")

    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": text,
        "parameters": { # Optional: include parameters like min_length, max_length if supported by model/task
            # "min_length": 30, 
            # "max_length": 150
        },
        "options": {
            "wait_for_model": True # Wait if the model is not immediately available
        }
    }

    logger.info(f"Calling Hugging Face API for summarization with model: {model_id}")
    try:
        if progress_callback:
            progress_callback(0) # Indicate start

        response = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        
        result = response.json()
        logger.debug(f"Hugging Face API response: {result}")

        if isinstance(result, list) and result and "summary_text" in result[0]:
            summary = result[0]["summary_text"]
            logger.info(f"Summary received from Hugging Face API. Length: {len(summary)}")
            if progress_callback:
                progress_callback(100) # Indicate completion
            return summary
        elif isinstance(result, dict) and "summary_text" in result: # Some models might return a dict directly
             summary = result["summary_text"]
             logger.info(f"Summary received from Hugging Face API. Length: {len(summary)}")
             if progress_callback:
                progress_callback(100) # Indicate completion
             return summary
        elif isinstance(result, dict) and "error" in result:
            logger.error(f"Hugging Face API returned an error: {result['error']}")
            if progress_callback:
                progress_callback(100) # Indicate completion (with error)
            if "estimated_time" in result:
                logger.info(f"Estimated time for model loading: {result['estimated_time']}s")
                raise RuntimeError(f"Model {model_id} is currently loading, try again in {result['estimated_time']:.0f}s. API Error: {result['error']}")
            raise RuntimeError(f"Hugging Face API error: {result['error']}")
        else:
            logger.error(f"Unexpected response format from Hugging Face API: {result}")
            raise RuntimeError("Unexpected response format from Hugging Face API.")

    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout during Hugging Face API call: {e}")
        if progress_callback:
            progress_callback(100) # Indicate completion (with error)
        raise RuntimeError(f"API request timed out after {timeout} seconds.")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error during Hugging Face API call: {e.response.status_code} - {e.response.text}")
        if progress_callback:
            progress_callback(100) # Indicate completion (with error)
        error_content = e.response.text
        try:
            error_json = json.loads(error_content)
            if "error" in error_json:
                error_message = error_json["error"]
                if isinstance(error_message, list):
                    error_message = ", ".join(error_message)
                if "estimated_time" in error_json: # Model is loading
                     raise RuntimeError(f"Model {model_id} is currently loading, try again in {error_json['estimated_time']:.0f}s. API Error: {error_message}") 
                raise RuntimeError(f"Hugging Face API error ({e.response.status_code}): {error_message}")
        except json.JSONDecodeError:
            pass # Fallback to generic error if response is not JSON
        raise RuntimeError(f"Hugging Face API request failed with status {e.response.status_code}: {e.response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during Hugging Face API call: {e}")
        if progress_callback:
            progress_callback(100) # Indicate completion (with error)
        raise RuntimeError(f"Failed to connect to Hugging Face API: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON response from Hugging Face API: {e}")
        if progress_callback:
            progress_callback(100) # Indicate completion (with error)
        raise RuntimeError("Invalid JSON response from Hugging Face API.")

def generate_text_hf_api(text_prompt: str, api_key: str, model_id: str = "gpt2", timeout: int = 60, progress_callback=None, max_new_tokens: int = 150):
    """
    Generate text using the Hugging Face Inference API based on a prompt.

    Args:
        text_prompt (str): The prompt to generate text from.
        api_key (str): The Hugging Face API key.
        model_id (str, optional): The model ID to use for text generation. 
                                Defaults to "gpt2".
        timeout (int, optional): Timeout for the API request in seconds. Defaults to 60.
        progress_callback (callable, optional): Callback function to report progress.
        max_new_tokens (int, optional): The maximum number of new tokens to generate. Defaults to 150.

    Returns:
        str: The generated text.

    Raises:
        ValueError: If the API key is missing.
        RuntimeError: If there's an error calling the API or processing the response.
    """
    if not api_key:
        logger.error("Hugging Face API key is missing.")
        raise ValueError("API key for Hugging Face Inference API is required.")

    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": text_prompt,
        "parameters": {
            "max_new_tokens": max_new_tokens,
            # Other parameters like temperature, top_p, etc., can be added here if needed
            # "do_sample": True, 
            # "temperature": 0.7,
            # "top_k": 50
        },
        "options": {
            "wait_for_model": True  # Wait if the model is not immediately available
        }
    }

    logger.info(f"Calling Hugging Face API for text generation with model: {model_id}")
    try:
        if progress_callback:
            progress_callback(0)  # Indicate start

        response = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        
        result = response.json()
        logger.debug(f"Hugging Face API response for text generation: {result}")

        # Text generation APIs usually return a list with a dict containing 'generated_text'
        if isinstance(result, list) and result and "generated_text" in result[0]:
            generated_text = result[0]["generated_text"]
            logger.info(f"Generated text received from Hugging Face API. Length: {len(generated_text)}")
            if progress_callback:
                progress_callback(100)  # Indicate completion
            return generated_text
        # Some models might return the generated text directly in a dictionary (less common for text-generation task)
        elif isinstance(result, dict) and "generated_text" in result:
            generated_text = result["generated_text"]
            logger.info(f"Generated text received from Hugging Face API. Length: {len(generated_text)}")
            if progress_callback:
                progress_callback(100) # Indicate completion
            return generated_text
        elif isinstance(result, dict) and "error" in result:
            logger.error(f"Hugging Face API returned an error: {result['error']}")
            if progress_callback:
                progress_callback(100)  # Indicate completion (with error)
            if "estimated_time" in result:
                logger.info(f"Estimated time for model loading: {result['estimated_time']}s")
                raise RuntimeError(f"Model {model_id} is currently loading, try again in {result['estimated_time']:.0f}s. API Error: {result['error']}")
            raise RuntimeError(f"Hugging Face API error: {result['error']}")
        else:
            logger.error(f"Unexpected response format from Hugging Face API for text generation: {result}")
            raise RuntimeError("Unexpected response format from Hugging Face API for text generation.")

    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout during Hugging Face API call for text generation: {e}")
        if progress_callback:
            progress_callback(100)  # Indicate completion (with error)
        raise RuntimeError(f"API request for text generation timed out after {timeout} seconds.")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error during Hugging Face API call for text generation: {e.response.status_code} - {e.response.text}")
        if progress_callback:
            progress_callback(100)  # Indicate completion (with error)
        error_content = e.response.text
        try:
            error_json = json.loads(error_content)
            if "error" in error_json:
                error_message = error_json["error"]
                if isinstance(error_message, list):
                    error_message = ", ".join(error_message)
                if "estimated_time" in error_json: # Model is loading
                     raise RuntimeError(f"Model {model_id} is currently loading, try again in {error_json['estimated_time']:.0f}s. API Error: {error_message}") 
                raise RuntimeError(f"Hugging Face API error ({e.response.status_code}): {error_message}")
        except json.JSONDecodeError:
            pass  # Fallback to generic error if response is not JSON
        raise RuntimeError(f"Hugging Face API request for text generation failed with status {e.response.status_code}: {e.response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during Hugging Face API call for text generation: {e}")
        if progress_callback:
            progress_callback(100)  # Indicate completion (with error)
        raise RuntimeError(f"Failed to connect to Hugging Face API for text generation: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON response from Hugging Face API for text generation: {e}")
        if progress_callback:
            progress_callback(100)  # Indicate completion (with error)
        raise RuntimeError("Invalid JSON response from Hugging Face API for text generation.")

_gemini_api_configured = False

def configure_gemini_api(api_key: str):
    """Configure the Google Gemini API with the provided key."""
    global _gemini_api_configured
    if not api_key:
        logger.error("Google API key is missing for configuration.")
        _gemini_api_configured = False
        raise ValueError("API key for Google Gemini is required.")
    try:
        genai.configure(api_key=api_key)
        _gemini_api_configured = True
        logger.info("Google Gemini API configured successfully.")
    except Exception as e:
        _gemini_api_configured = False
        logger.error(f"Failed to configure Google Gemini API: {e}")
        raise RuntimeError(f"Failed to configure Google Gemini API: {e}")

def _ensure_gemini_configured(api_key: Optional[str] = None):
    """Ensures Gemini API is configured, optionally using the provided key."""
    global _gemini_api_configured
    if not _gemini_api_configured:
        if not api_key:
            logger.error("Google Gemini API key not provided and API not configured.")
            raise ValueError("Google Gemini API key must be provided or API pre-configured.")
        configure_gemini_api(api_key)
    if not _gemini_api_configured:
         raise RuntimeError("Google Gemini API is not configured. Please check API key and configuration.")

def summarize_text_gemini_api(text: str, api_key: str, model_name: str = "gemini-pro", progress_callback=None):
    """
    Generate a summary of the given text using the Google Gemini API.

    Args:
        text (str): The text to summarize.
        api_key (str): The Google API key.
        model_name (str, optional): The Gemini model name. Defaults to "gemini-pro".
        progress_callback (callable, optional): Callback for progress (0 to 100).

    Returns:
        str: The generated summary.

    Raises:
        RuntimeError: If there's an error calling the API or processing the response.
        ValueError: If API key is invalid or missing.
    """
    logger.info(">>> Entering summarize_text_gemini_api - Gemini summarization process initiated. <<<") # Distinct log for entry
    logger.info(f"Starting Gemini API summarization with model: {model_name}")
    try:
        _ensure_gemini_configured(api_key)
        if progress_callback: progress_callback(0)

        model = genai.GenerativeModel(model_name)
        prompt = f"Please summarize the following text concisely and accurately:\n\n---\n{text}\n---\n\nSummary:"
        
        # Using a simple generation config for summarization for now.
        # More complex configs can be added if needed (e.g. temperature, top_p)
        generation_config = genai.types.GenerationConfig(
            candidate_count=1,
            # max_output_tokens can be tuned. Gemini Pro has a large context window.
            # For summarization, we might want to control this if the input text is very long.
        )

        if progress_callback: progress_callback(30) # After setup, before API call

        response = model.generate_content(prompt, generation_config=generation_config)

        if progress_callback: progress_callback(70) # After API call, before processing

        if not response.candidates or not response.candidates[0].content.parts:
            logger.error("Gemini API returned no valid candidates or parts in the response.")
            raise RuntimeError("Gemini API did not return a valid summary.")

        summary = response.text # .text helper combines parts
        logger.info(f"Gemini API summary generated. Length: {len(summary)}")
        
        if progress_callback: progress_callback(100)
        return summary

    except google_exceptions.InvalidArgument as e:
        logger.error(f"Gemini API Invalid Argument: {e}. This might be due to an unsupported model or an issue with the prompt/text.")
        if progress_callback: progress_callback(100)
        raise RuntimeError(f"Gemini API Invalid Argument: {e}")
    except google_exceptions.PermissionDenied as e:
        logger.error(f"Gemini API Permission Denied: {e}. Check API key and project permissions.")
        if progress_callback: progress_callback(100)
        raise ValueError(f"Gemini API Permission Denied. Ensure API key is valid and has permissions: {e}")
    except google_exceptions.DeadlineExceeded as e:
        logger.error(f"Gemini API request timed out: {e}")
        if progress_callback: progress_callback(100)
        raise RuntimeError(f"Gemini API request timed out: {e}")
    except google_exceptions.GoogleAPIError as e: # Catch other Google API errors
        logger.error(f"Google Gemini API error: {e}")
        if progress_callback: progress_callback(100)
        raise RuntimeError(f"Google Gemini API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during Gemini API summarization: {e}")
        if progress_callback: progress_callback(100)
        import traceback
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Unexpected error during Gemini API summarization: {e}")

def generate_text_gemini_api(text_prompt: str, api_key: str, model_name: str = "gemini-pro", progress_callback=None, max_output_tokens: int = 1024):
    """
    Generate text using the Google Gemini API based on a prompt.

    Args:
        text_prompt (str): The prompt to generate text from.
        api_key (str): The Google API key.
        model_name (str, optional): The Gemini model name. Defaults to "gemini-pro".
        progress_callback (callable, optional): Callback for progress (0 to 100).
        max_output_tokens (int, optional): Maximum number of tokens for the generated text.

    Returns:
        str: The generated text.

    Raises:
        RuntimeError: If there's an error calling the API or processing the response.
        ValueError: If API key is invalid or missing.
    """
    logger.info(f"Starting Gemini API text generation with model: {model_name}")
    try:
        _ensure_gemini_configured(api_key)
        if progress_callback: progress_callback(0)

        model = genai.GenerativeModel(model_name)
        generation_config = genai.types.GenerationConfig(
            candidate_count=1,
            max_output_tokens=max_output_tokens
        )

        if progress_callback: progress_callback(30) # After setup, before API call

        response = model.generate_content(text_prompt, generation_config=generation_config)

        if progress_callback: progress_callback(70) # After API call, before processing

        if not response.candidates or not response.candidates[0].content.parts:
            logger.error("Gemini API returned no valid candidates or parts in the response for text generation.")
            raise RuntimeError("Gemini API did not return valid generated text.")

        generated_text = response.text
        logger.info(f"Gemini API text generated. Length: {len(generated_text)}")
        
        if progress_callback: progress_callback(100)
        return generated_text

    except google_exceptions.InvalidArgument as e:
        logger.error(f"Gemini API Invalid Argument for text generation: {e}")
        if progress_callback: progress_callback(100)
        raise RuntimeError(f"Gemini API Invalid Argument for text generation: {e}")
    except google_exceptions.PermissionDenied as e:
        logger.error(f"Gemini API Permission Denied for text generation: {e}. Check API key.")
        if progress_callback: progress_callback(100)
        raise ValueError(f"Gemini API Permission Denied for text generation: {e}")
    except google_exceptions.DeadlineExceeded as e:
        logger.error(f"Gemini API text generation request timed out: {e}")
        if progress_callback: progress_callback(100)
        raise RuntimeError(f"Gemini API text generation request timed out: {e}")
    except google_exceptions.GoogleAPIError as e: # Catch other Google API errors
        logger.error(f"Google Gemini API error during text generation: {e}")
        if progress_callback: progress_callback(100)
        raise RuntimeError(f"Google Gemini API error during text generation: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during Gemini API text generation: {e}")
        if progress_callback: progress_callback(100)
        import traceback
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Unexpected error during Gemini API text generation: {e}")

def perform_question_answering(original_note_text: str, extracted_entities: list, web_content_collated: str, qna_model_id: str = "distilbert-base-cased-distilled-squad", progress_callback=None, max_questions: int = 3):
    """
    Performs Question Answering on the provided web content based on extracted entities.

    Args:
        original_note_text (str): The original text of the note (currently unused, but available for future context).
        extracted_entities (list): A list of entities extracted from the note.
        web_content_collated (str): Collated text content fetched from web sources.
        qna_model_id (str, optional): The Hugging Face model ID for question answering.
                                      Defaults to "distilbert-base-cased-distilled-squad".
        progress_callback (callable, optional): Callback function to report progress.
        max_questions (int, optional): Maximum number of questions to generate from entities.

    Returns:
        dict: A dictionary where keys are questions and values are answers.
              Returns an empty dict if no entities or content, or if an error occurs.
    """
    logger.info(f"Starting Question Answering with model: {qna_model_id}. Entities: {len(extracted_entities)}, Content length: {len(web_content_collated)}")
    if progress_callback: progress_callback(0)

    if not extracted_entities or not web_content_collated:
        logger.warning("No entities or web content provided for Q&A. Returning empty results.")
        if progress_callback: progress_callback(100)
        return {}

    results = {}
    try:
        logger.info(f"Loading Q&A model: {qna_model_id}")
        qa_pipeline = pipeline("question-answering", model=qna_model_id, device=-1) # device=-1 for CPU
        logger.info(f"Q&A model {qna_model_id} loaded successfully.")

        num_questions_to_ask = min(len(extracted_entities), max_questions)
        
        for i, entity in enumerate(extracted_entities[:num_questions_to_ask]):
            question = f"What is {entity}?" # Simple question formulation
            # Alternative: f"Tell me more about {entity} based on the provided context."
            logger.info(f"Asking question ({i+1}/{num_questions_to_ask}): {question}")
            
            try:
                answer_obj = qa_pipeline(question=question, context=web_content_collated)
                if answer_obj and 'answer' in answer_obj:
                    results[question] = answer_obj['answer']
                    logger.info(f"Answer for '{question}': '{answer_obj['answer'][:100]}...' (Score: {answer_obj.get('score', 'N/A')})")
                else:
                    results[question] = "Could not find an answer."
                    logger.warning(f"Could not find an answer for question: {question}. Pipeline output: {answer_obj}")
            except Exception as e_inner:
                logger.error(f"Error during Q&A pipeline for question '{question}': {e_inner}")
                results[question] = f"Error processing this question: {e_inner}"
            
            if progress_callback:
                progress_callback(int(((i + 1) / num_questions_to_ask) * 100))

    except Exception as e:
        logger.error(f"General error during Question Answering with model {qna_model_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Optionally, communicate this error through a specific field in results or raise it
        # For now, we return any partial results and log the error.
        if progress_callback: progress_callback(100) # Mark as finished despite error
        # To ensure the worker doesn't crash and AIController gets a dict:
        if not results: # If no questions were even attempted
             results["error"] = f"Failed to initialize Q&A: {str(e)}"
        else: # If some questions were processed
            results["processing_error"] = f"An error occurred during Q&A: {str(e)}"

    logger.info(f"Question Answering finished. Generated {len(results)} answers.")
    if progress_callback: progress_callback(100)
    return results

def extract_entities_spacy(text: str, model_id: str = "en_core_web_sm", progress_callback=None) -> List[str]:
    """
    Extract named entities from text using a spaCy model.

    Args:
        text (str): The text to process.
        model_id (str, optional): The spaCy model ID to use. Defaults to "en_core_web_sm".
        progress_callback (callable, optional): Callback for progress updates.

    Returns:
        List[str]: A list of extracted entity texts. Returns an empty list on error.
    """
    logger.info(f"Starting entity extraction with spaCy model: {model_id} for text of length: {len(text)}")
    if progress_callback: progress_callback(0)

    entities = []
    try:
        try:
            nlp = spacy.load(model_id)
            logger.info(f"spaCy model '{model_id}' loaded successfully.")
        except OSError:
            logger.error(f"spaCy model '{model_id}' not found. Downloading...")
            spacy.cli.download(model_id)
            nlp = spacy.load(model_id)
            logger.info(f"spaCy model '{model_id}' downloaded and loaded successfully.")
        
        if progress_callback: progress_callback(50) # Model loaded
        
        doc = nlp(text)
        entities = [ent.text for ent in doc.ents]
        logger.info(f"Extracted {len(entities)} entities: {entities[:10]}...")
        
        if progress_callback: progress_callback(100)
    except ImportError:
        logger.error("spaCy library not found. Please ensure it is installed.")
        if progress_callback: progress_callback(100) # Error, but operation 'finished'
        # Return empty list as per contract, error already logged
    except Exception as e:
        logger.error(f"Error during spaCy entity extraction with model {model_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        if progress_callback: progress_callback(100) # Error, but operation 'finished'
        # Return empty list as per contract, error already logged
    
    return entities

def extract_keywords_spacy(text: str, num_keywords: int = 5) -> List[str]:
    """
    Extract keywords from text using a spaCy model.

    Args:
        text (str): The text to process.
        num_keywords (int, optional): The number of keywords to extract. Defaults to 5.

    Returns:
        List[str]: A list of extracted keywords.
    """
    logger.info(f"Starting keyword extraction with spaCy for text of length: {len(text)}")

    keywords = []
    try:
        try:
            nlp = spacy.load("en_core_web_sm")
            logger.info(f"spaCy model 'en_core_web_sm' loaded successfully.")
        except OSError:
            logger.error(f"spaCy model 'en_core_web_sm' not found. Downloading...")
            spacy.cli.download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")
            logger.info(f"spaCy model 'en_core_web_sm' downloaded and loaded successfully.")
        
        doc = nlp(text)
        keywords = [token.text for token in doc if not token.is_stop and token.is_alpha and token.pos_ in ["NOUN", "PROPN"]]
        keywords = keywords[:num_keywords]
        logger.info(f"Extracted {len(keywords)} keywords: {keywords}...")
    
    except ImportError:
        logger.error("spaCy library not found. Please ensure it is installed.")
        # Return empty list as per contract, error already logged
    except Exception as e:
        logger.error(f"Error during spaCy keyword extraction: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Return empty list as per contract, error already logged
    
    return keywords

# Ensure the logger used in this module has handlers configured if run standalone
# This is more for testing/running this file directly if needed
if __name__ == "__main__" and not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG) # Or INFO
    
    # Test local summarization
    # try:
    #     test_text = ("This is a very long piece of text that needs to be summarized. "
    #                  "It talks about various things including programming, AI, and the weather. "
    #                  "The goal is to get a concise summary that captures the main points. "
    #                  "Let's see how well the local summarization model performs on this. "
    #                  "It should be shorter than this original text, obviously.") * 5
    #     print("\n--- Testing Local Summarization ---")
    #     summary = summarize_text_local(test_text)
    #     print(f"Original length: {len(test_text)}, Summary length: {len(summary)}")
    #     print(f"Summary: {summary}")
    # except Exception as e:
    #     print(f"Local summarization test failed: {e}")

    # Test Hugging Face API summarization (requires HUGGINGFACE_API_KEY environment variable)
    # try:
    #     hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
    #     if hf_api_key:
    #         print("\n--- Testing Hugging Face API Summarization ---")
    #         summary_hf = summarize_text_hf_api(test_text, hf_api_key)
    #         print(f"Original length: {len(test_text)}, Summary length: {len(summary_hf)}")
    #         print(f"HF API Summary: {summary_hf}")
    #     else:
    #         print("\nSkipping Hugging Face API summarization test: HUGGINGFACE_API_KEY not set.")
    # except Exception as e:
    #     print(f"Hugging Face API summarization test failed: {e}")

    # Test Gemini API summarization (requires GOOGLE_API_KEY environment variable)
    # try:
    #     google_api_key = os.getenv("GOOGLE_API_KEY")
    #     if google_api_key:
    #         print("\n--- Testing Google Gemini API Summarization ---")
    #         configure_gemini_api(google_api_key) # Configure once
    #         summary_gemini = summarize_text_gemini_api(test_text, google_api_key) # Pass key again or rely on pre-config
    #         print(f"Original length: {len(test_text)}, Summary length: {len(summary_gemini)}")
    #         print(f"Gemini API Summary: {summary_gemini}")
    #     else:
    #         print("\nSkipping Google Gemini API summarization test: GOOGLE_API_KEY not set.")
    # except Exception as e:
    #     print(f"Google Gemini API summarization test failed: {e}")

    # Test spaCy entity and keyword extraction
    # try:
    #     print("\n--- Testing spaCy Entity Extraction ---")
    #     entities = extract_entities_spacy(test_text)
    #     print(f"Entities: {entities}")

    #     print("\n--- Testing spaCy Keyword Extraction ---")
    #     keywords = extract_keywords_spacy(test_text)
    #     print(f"Keywords: {keywords}")
    # except Exception as e:
    #     print(f"spaCy extraction tests failed: {e}")

# Removed inaccurate comment about duplicated functions that was here.

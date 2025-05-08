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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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

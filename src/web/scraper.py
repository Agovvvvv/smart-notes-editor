#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web scraping utilities for the Smart Contextual Notes Editor.
Provides functions for web search and content extraction.
"""

import logging
import requests
import time
import re
import urllib.parse
from typing import Dict, List, Optional, Tuple, Union
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser

logger = logging.getLogger(__name__)

# Constants
USER_AGENT = "SmartContextualNotesEditor/1.0 (Educational Project)"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "DNT": "1",  # Do Not Track
}
REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
MAX_SEARCH_RESULTS = 5  # Maximum number of search results to process

class WebScrapingError(Exception):
    """Base exception for web scraping errors."""
    pass

class RobotsTxtError(WebScrapingError):
    """Exception raised when robots.txt disallows access."""
    pass

class NetworkError(WebScrapingError):
    """Exception raised for network-related errors."""
    pass

class ParsingError(WebScrapingError):
    """Exception raised when content parsing fails."""
    pass

def is_url_allowed(url: str) -> bool:
    """
    Check if a URL is allowed to be scraped according to robots.txt.
    
    Args:
        url (str): The URL to check
        
    Returns:
        bool: True if allowed, False if disallowed
        
    Note:
        Returns True if robots.txt cannot be fetched or parsed, with a warning.
    """
    try:
        parsed_url = urllib.parse.urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = f"{base_url}/robots.txt"
        
        rp = RobotFileParser()
        rp.set_url(robots_url)
        
        # Fetch robots.txt with timeout
        response = requests.get(robots_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            rp.parse(response.text.splitlines())
            return rp.can_fetch(USER_AGENT, url)
        else:
            logger.warning(f"Could not fetch robots.txt for {base_url}, assuming access is allowed")
            return True
            
    except Exception as e:
        logger.warning(f"Error checking robots.txt for {url}: {str(e)}")
        return True  # Assume allowed if we can't check

def search_web(query: str, progress_callback=None) -> List[Dict[str, str]]:
    """
    Search the web for the given query using DuckDuckGo.
    
    Args:
        query (str): The search query
        progress_callback (callable): Optional callback function to report progress
        
    Returns:
        List[Dict[str, str]]: List of search results, each with 'title', 'url', and 'snippet'
        
    Raises:
        NetworkError: If there's a network-related error
    """
    if progress_callback:
        progress_callback(10)
        
    # Encode the query for URL
    encoded_query = urllib.parse.quote_plus(query)
    
    # DuckDuckGo search URL (HTML version)
    search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    
    logger.info(f"Searching web for: {query}")
    
    try:
        # Make the request with retries
        response = None
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(
                    search_url, 
                    headers=HEADERS, 
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                break
            except (requests.RequestException, requests.HTTPError) as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Retry {attempt+1}/{MAX_RETRIES} after error: {str(e)}")
                    time.sleep(RETRY_DELAY)
                else:
                    raise NetworkError(f"Failed to fetch search results after {MAX_RETRIES} attempts: {str(e)}")
        
        if progress_callback:
            progress_callback(30)
            
        # Parse the HTML response
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract search results
        results = []
        # Try a broader set of selectors for result containers
        result_elements = soup.select('div.web-result, div.result, .results_links_deep .result__body, div.result--html')
        
        if not result_elements:
            # Fallback selectors if the primary ones don't work
            result_elements = soup.select('div.results > div') # Common generic structure
            if not result_elements:
                logger.warning(f"No search results found or unexpected page structure using primary and fallback selectors. URL: {search_url}")
                # Log a snippet of the page for debugging if selectors fail
                page_snippet = response.text[:1000] if response else "No response text"
                logger.debug(f"Page snippet for {search_url}:\n{page_snippet}")
                return []
            
        for i, result_container in enumerate(result_elements[:MAX_SEARCH_RESULTS]):
            try:
                # More robust selectors for title, URL, and snippet
                title_element = result_container.select_one('.result__title a, .result__a, h2.result-title a, a.result-title')
                # URL element is often the same as the title link, or a specific URL link
                url_element = result_container.select_one('.result__url a, .result__a, a.result-link, .result__extras__url a') 
                snippet_element = result_container.select_one('.result__snippet, .result-snippet, .result__body')
                
                if title_element and url_element:
                    title = title_element.get_text(strip=True)
                    # Extract URL from the href attribute
                    url = url_element.get('href', '').strip()
                    
                    # DuckDuckGo HTML results often have URLs like "/l/?uddg=..."
                    if url.startswith('/l/'):
                        parsed_url = urllib.parse.urlparse(url)
                        query_params = urllib.parse.parse_qs(parsed_url.query)
                        if 'uddg' in query_params and query_params['uddg']:
                            url = query_params['uddg'][0]
                    
                    # Ensure URL has a scheme if it's not a relative DDG link
                    if not url.startswith(('http://', 'https://')) and not url.startswith('/'):
                        url = 'https://' + url
                        
                    snippet = snippet_element.get_text(strip=True) if snippet_element else ""
                    
                    # Filter out empty or clearly non-result items
                    if not title or not url or url == "#":
                        logger.debug(f"Skipping potential non-result item: title='{title}', url='{url}'")
                        continue

                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet
                    })
                    
                    if progress_callback:
                        # Update progress based on how many results we've processed
                        progress = 30 + int(50 * (i + 1) / min(len(result_elements), MAX_SEARCH_RESULTS))
                        progress_callback(progress)
            except Exception as e:
                logger.warning(f"Error parsing a search result item: {str(e)}")
                logger.debug(f"Problematic result item HTML: {result_container.prettify()[:500]}", exc_info=True)
                continue
                
        if not results and result_elements:
             logger.warning(f"Found {len(result_elements)} potential result containers, but failed to extract details from any.")

        logger.info(f"Found {len(results)} search results for '{query}'")
        return results
        
    except Exception as e:
        logger.error(f"Error searching web for '{query}': {str(e)}", exc_info=True)
        raise NetworkError(f"Error searching web: {str(e)}")

def perform_web_searches_for_entities(
    entities: List[str],
    original_note_text: Optional[str] = None, # For API consistency, not used directly by search_web
    progress_callback: Optional[callable] = None,
    **kwargs # To catch any other kwargs like the one from Worker base class
) -> Dict[str, Union[List[Dict[str, str]], str]]:
    """
    Performs web searches for a list of entities and collates the results.

    Args:
        entities (List[str]): A list of entity strings to search for.
        original_note_text (Optional[str]): The original note text, for context (currently unused).
        progress_callback (Optional[callable]): A function to call with progress (0-100).
        **kwargs: Catches unused kwargs like progress_callback from the base Worker if not explicitly handled.

    Returns:
        Dict[str, Union[List[Dict[str, str]], str]]: A dictionary where keys are entity strings
        and values are lists of search result dictionaries (title, url, snippet) or an error message string.
    """
    logger.info(f"Performing web searches for {len(entities)} entities.")
    results_for_all_entities: Dict[str, Union[List[Dict[str, str]], str]] = {}
    total_entities = len(entities)

    if not total_entities:
        if progress_callback:
            progress_callback(100)
        return {}

    for i, entity in enumerate(entities):
        current_base_progress = (i / total_entities) * 100
        current_entity_progress_weight = 1 / total_entities

        # Pass loop-dependent values as default arguments to capture their current state
        def entity_specific_progress_callback(entity_progress_value, 
                                                base_prog=current_base_progress, 
                                                weight=current_entity_progress_weight):
            if progress_callback:
                overall_progress = base_prog + (entity_progress_value * weight)
                progress_callback(int(overall_progress))

        if progress_callback:
            progress_callback(int(current_base_progress)) # Report progress before starting search for entity

        try:
            logger.debug(f"Searching web for entity: '{entity}'")
            # Pass the wrapped progress callback to search_web
            search_results = search_web(query=entity, progress_callback=entity_specific_progress_callback)
            results_for_all_entities[entity] = search_results
            logger.debug(f"Found {len(search_results)} results for entity: '{entity}'")
        except NetworkError as e:
            logger.error(f"NetworkError searching for entity '{entity}': {e}")
            results_for_all_entities[entity] = f"Error: {str(e)}" # Store error message
        except Exception as e:
            logger.error(f"Unexpected error searching for entity '{entity}': {e}", exc_info=True)
            results_for_all_entities[entity] = f"Unexpected error: {str(e)}"
        
        # Ensure final progress for this entity step is reported if search_web finishes early
        if progress_callback:
            progress_callback(int(current_base_progress + (100 * current_entity_progress_weight)))

    if progress_callback:
        progress_callback(100) # Final progress update

    logger.info(f"Finished web searches for {len(entities)} entities.")
    return results_for_all_entities

def scrape_page_content(url: str, progress_callback=None) -> Dict[str, str]:
    """
    Scrape content from a web page.
    
    Args:
        url (str): The URL to scrape
        progress_callback (callable): Optional callback function to report progress
        
    Returns:
        Dict[str, str]: Dictionary with 'title', 'url', 'content', and 'error' (if any)
        
    Raises:
        RobotsTxtError: If robots.txt disallows access
        NetworkError: If there's a network-related error
        ParsingError: If content parsing fails
    """
    result = {
        'url': url,
        'title': '',
        'content': '',
        'error': ''
    }
    
    if progress_callback:
        progress_callback(10)
    
    # Check robots.txt
    if not is_url_allowed(url):
        error_msg = f"Access to {url} disallowed by robots.txt"
        logger.warning(error_msg)
        result['error'] = error_msg
        raise RobotsTxtError(error_msg)
    
    if progress_callback:
        progress_callback(20)
    
    try:
        # Make the request with retries
        response = None
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(
                    url, 
                    headers=HEADERS, 
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                break
            except (requests.RequestException, requests.HTTPError) as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Retry {attempt+1}/{MAX_RETRIES} after error: {str(e)}")
                    time.sleep(RETRY_DELAY)
                else:
                    error_msg = f"Failed to fetch {url} after {MAX_RETRIES} attempts: {str(e)}"
                    result['error'] = error_msg
                    raise NetworkError(error_msg)
        
        if progress_callback:
            progress_callback(50)
            
        # Parse the HTML response
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        result['title'] = title_tag.get_text(strip=True) if title_tag else "No title"
        
        if progress_callback:
            progress_callback(60)
            
        # Extract main content
        # Try to find the main content container
        main_content = None
        
        # Try common content containers
        for selector in ['article', 'main', '.content', '#content', '.post', '.article', '.entry']:
            content = soup.select(selector)
            if content:
                main_content = content[0]
                break
                
        # If no container found, use the body
        if not main_content:
            main_content = soup.body
            
        if progress_callback:
            progress_callback(70)
            
        # Extract text from paragraphs
        paragraphs = []
        if main_content:
            for p in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                text = p.get_text(strip=True)
                if text and len(text) > 20:  # Filter out short paragraphs
                    paragraphs.append(text)
        
        if progress_callback:
            progress_callback(90)
            
        # Join paragraphs into content
        result['content'] = '\n\n'.join(paragraphs)
        
        # If no paragraphs found, try getting all text
        if not result['content'] and main_content:
            result['content'] = main_content.get_text(separator='\n\n', strip=True)
            
        # Clean up the content
        result['content'] = clean_content(result['content'])
        
        if progress_callback:
            progress_callback(100)
            
        logger.info(f"Successfully scraped content from {url}")
        return result
        
    except (RobotsTxtError, NetworkError) as e:
        # Re-raise these exceptions
        raise
    except Exception as e:
        error_msg = f"Error parsing content from {url}: {str(e)}"
        logger.error(error_msg)
        result['error'] = error_msg
        raise ParsingError(error_msg)

def clean_content(content: str) -> str:
    """
    Clean up scraped content by removing extra whitespace, etc.
    
    Args:
        content (str): The content to clean
        
    Returns:
        str: The cleaned content
    """
    # Replace multiple newlines with double newline
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Replace multiple spaces with single space
    content = re.sub(r' {2,}', ' ', content)
    
    # Remove any non-printable characters
    content = ''.join(c for c in content if c.isprintable() or c in ['\n', '\t'])
    
    return content.strip()

def extract_key_information(text: str) -> Dict[str, List[str]]:
    """
    Extract key information from text (e.g., entities, keywords).
    
    Args:
        text (str): The text to analyze
        
    Returns:
        Dict[str, List[str]]: Dictionary with extracted information
    """
    # This is a simple implementation that could be enhanced with NLP libraries
    result = {
        'keywords': [],
        'urls': []
    }
    
    # Extract URLs
    url_pattern = r'https?://[^\s]+'
    result['urls'] = re.findall(url_pattern, text)
    
    # Extract simple keywords (words that appear frequently)
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    word_counts = {}
    
    # Skip common stop words
    stop_words = {'the', 'and', 'that', 'this', 'with', 'from', 'have', 'for', 'not', 'are', 'was', 'were', 'they', 'their', 'what', 'when', 'where', 'who', 'will', 'would', 'could', 'should', 'which', 'than', 'then', 'them', 'these', 'those', 'some', 'such'}
    
    for word in words:
        if word not in stop_words:
            word_counts[word] = word_counts.get(word, 0) + 1
    
    # Get top keywords
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    result['keywords'] = [word for word, count in sorted_words[:10] if count > 1]
    
    return result

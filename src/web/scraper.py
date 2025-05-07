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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        result_elements = soup.select('.result')
        
        if not result_elements:
            logger.warning("No search results found or unexpected page structure")
            return []
            
        for i, result in enumerate(result_elements[:MAX_SEARCH_RESULTS]):
            try:
                title_element = result.select_one('.result__title')
                url_element = result.select_one('.result__url')
                snippet_element = result.select_one('.result__snippet')
                
                if title_element and url_element:
                    title = title_element.get_text(strip=True)
                    url = url_element.get_text(strip=True)
                    
                    # Ensure URL has a scheme
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                        
                    snippet = snippet_element.get_text(strip=True) if snippet_element else ""
                    
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
                logger.warning(f"Error parsing search result: {str(e)}")
                continue
                
        logger.info(f"Found {len(results)} search results")
        return results
        
    except Exception as e:
        logger.error(f"Error searching web: {str(e)}")
        raise NetworkError(f"Error searching web: {str(e)}")

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

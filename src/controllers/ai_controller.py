#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controller for AI summarization operations.
"""

import logging
import sys
import traceback
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool

# Import AI utilities
from utils.threads import WorkerSignals, EntityExtractionWorker

logger = logging.getLogger(__name__)

class AIController(QObject):
    """Controller for AI summarization operations."""
    
    # Define signals for summarization
    summarization_started = pyqtSignal()
    summarization_progress = pyqtSignal(int)
    summarization_result = pyqtSignal(str)
    summarization_error = pyqtSignal(tuple)
    summarization_finished = pyqtSignal()

    # Define signals for text generation
    text_generation_started = pyqtSignal()
    text_generation_progress = pyqtSignal(int)
    text_generation_result = pyqtSignal(str)
    text_generation_error = pyqtSignal(tuple)
    text_generation_finished = pyqtSignal()
    
    # Define signals for Enhance Notes feature
    # Entity Extraction
    entity_extraction_started = pyqtSignal()
    entities_extracted = pyqtSignal(list)
    entity_extraction_error = pyqtSignal(tuple)
    entity_extraction_finished = pyqtSignal()

    # Signals for the Q&A part of the "Enhance Notes" feature
    answer_extraction_started = pyqtSignal() # Emitted by fetch_content_and_perform_qna
    answer_extracted = pyqtSignal(dict) # For collated Q&A results from enhancement
    answer_extraction_error = pyqtSignal(tuple) # For errors during fetching or Q&A
    answer_extraction_finished = pyqtSignal() # Signals completion of the Q&A enhancement part

    # Generic Question Answering (if different from enhancement Q&A)
    question_answering_started = pyqtSignal()
    answer_found = pyqtSignal(str, float) # answer_text, score
    question_answering_error = pyqtSignal(tuple)
    question_answering_finished = pyqtSignal()

    # Web Content Summarization
    web_content_summarization_started = pyqtSignal()
    web_summary_ready = pyqtSignal(str)
    web_content_summarization_error = pyqtSignal(tuple)
    web_content_summarization_finished = pyqtSignal()

    # Web Search for Enhancement
    web_search_for_enhancement_started = pyqtSignal()
    web_search_for_enhancement_result = pyqtSignal(dict)
    web_search_for_enhancement_error = pyqtSignal(tuple)
    
    model_preload_result = pyqtSignal(bool, str)
    model_preload_error = pyqtSignal(tuple)
    
    def __init__(self, main_window, settings_model):
        """Initialize the AI controller."""
        super().__init__()
        self.main_window = main_window
        self.settings_model = settings_model
        self.thread_pool = QThreadPool()
        self._enhancement_web_search_data = None # For managing web searches during enhancement
        self._qna_process_data = None # For managing content fetching and Q&A during enhancement
        
        # Import AI manager here to avoid circular imports
        from managers.ai_manager import AIManager
        self.ai_manager = AIManager(self, self.settings_model)
        
        # Connect AI manager signals
        self._connect_ai_manager_signals()
    
    def _connect_ai_manager_signals(self):
        """Set up callback methods for the AI manager."""
        # Connect AIManager's summarization signals to AIController's handlers
        self.ai_manager.summarization_started_signal.connect(self._on_summarization_started)
        self.ai_manager.summarization_progress_signal.connect(self._on_summarization_progress)
        self.ai_manager.summarization_result_signal.connect(self._on_summarization_result)
        self.ai_manager.summarization_error_signal.connect(self._on_summarization_error)
        self.ai_manager.summarization_finished_signal.connect(self._on_summarization_finished)

        # Connect AIManager's text generation signals to AIController's new internal handlers
        self.ai_manager.text_generation_started_signal.connect(self._on_manager_text_generation_started)
        self.ai_manager.text_generation_progress_signal.connect(self._on_manager_text_generation_progress)
        self.ai_manager.text_generation_result_signal.connect(self._on_manager_text_generation_result)
        self.ai_manager.text_generation_error_signal.connect(self._on_manager_text_generation_error)
        self.ai_manager.text_generation_finished_signal.connect(self._on_manager_text_generation_finished)
        
        # Connect AIManager's Q&A signals for the "Enhance Notes" feature
        self.ai_manager.qna_started_signal.connect(self._on_manager_enhancement_qna_started)
        self.ai_manager.qna_result_signal.connect(self._on_manager_enhancement_qna_result)
        self.ai_manager.qna_error_signal.connect(self._on_manager_enhancement_qna_error)
        self.ai_manager.qna_finished_signal.connect(self._on_manager_enhancement_qna_finished)

        # Placeholder connections for other features if AIManager handles them
        # Entity Extraction (if managed by AIManager, connect here)
    
    def _on_summarization_started(self):
        """Handle summarization started event from AIManager."""
        logger.info("AIController: Summarization started, emitting own signal.")
        self.summarization_started.emit()
        
    def _on_summarization_progress(self, progress):
        """Handle summarization progress event from AIManager."""
        logger.info(f"AIController: Summarization progress {progress}%, emitting own signal.")
        self.summarization_progress.emit(progress)
        
    def _on_summarization_result(self, result):
        """Handle summarization result event from AIManager."""
        logger.info("AIController: Summarization result received, emitting own signal.")
        self.summarization_result.emit(result)
        
    def _on_summarization_error(self, error_info):
        """Handle summarization error event from AIManager."""
        logger.info("AIController: Summarization error, emitting own signal.")
        self.summarization_error.emit(error_info)
        
    def _on_summarization_finished(self):
        """Handle summarization finished event from AIManager."""
        logger.info("AIController: Summarization finished, emitting own signal.")
        self.summarization_finished.emit()

    # --- Internal Handlers for AIManager's Text Generation Signals ---
    def _on_manager_text_generation_started(self):
        logger.info("AIController: Text generation started from AIManager, emitting own signal.")
        self.text_generation_started.emit()

    def _on_manager_text_generation_progress(self, percentage: int):
        logger.info("AIController: Text generation progress {}% from AIManager, emitting own signal.".format(percentage))
        self.text_generation_progress.emit(percentage)

    def _on_manager_text_generation_result(self, generated_text: str):
        logger.info("AIController: Text generation result from AIManager, emitting own signal.")
        self.text_generation_result.emit(generated_text)

    def _on_manager_text_generation_error(self, error_details: tuple):
        logger.info("AIController: Text generation error from AIManager, emitting own signal.")
        self.text_generation_error.emit(error_details)

    def _on_manager_text_generation_finished(self):
        logger.info("AIController: Text generation finished from AIManager, emitting own signal.")
        self.text_generation_finished.emit()

    # --- Internal Handlers for AIManager's Q&A Signals (Enhance Notes Workflow) ---
    @pyqtSlot()
    def _on_manager_enhancement_qna_started(self):
        logger.info("AIController: Q&A (for enhancement) started via AIManager.")
        # self.answer_extraction_started is emitted earlier in fetch_content_and_perform_qna

    @pyqtSlot(dict)
    def _on_manager_enhancement_qna_result(self, qna_results: dict):
        logger.info(f"AIController: Q&A results (for enhancement) received from AIManager: {len(qna_results)} pairs.")
        self.answer_extracted.emit(qna_results)

    @pyqtSlot(tuple)
    def _on_manager_enhancement_qna_error(self, error_details: tuple):
        logger.error(f"AIController: Q&A error (for enhancement) from AIManager: {error_details[0].__name__ if error_details else 'Unknown Error'}: {error_details[1] if len(error_details) > 1 else ''}")
        self.answer_extraction_error.emit(error_details)

    @pyqtSlot()
    def _on_manager_enhancement_qna_finished(self):
        logger.info("AIController: Q&A (for enhancement) finished via AIManager.")
        self.answer_extraction_finished.emit()
        if self._qna_process_data: # Cleanup after Q&A is fully finished
            logger.debug("AIController: Cleaning up QNA process data after successful enhancement Q&A completion.")
            self._qna_process_data = None

    # --- Summarization and Text Generation Triggers (delegated to AIManager) ---
    def summarize_text(self, text_to_summarize: str):
        """
        Generate a summary of the provided text using AI.
        
        Args:
            text_to_summarize (str): The text to summarize
        """
        logger.info(f"AIController.summarize_text called with text length: {len(text_to_summarize)}")
        try:
            logger.info("Calling ai_manager.summarize_text")
            self.ai_manager.summarize_text(text_to_summarize)
            logger.info("ai_manager.summarize_text call completed (this should be immediate since it's async)")
        except Exception as e:
            logger.error(f"Exception in AIController.summarize_text: {str(e)}")
            error_info = (type(e), e, traceback.format_exc())
            logger.info("Emitting summarization_error signal")
            self.summarization_error.emit(error_info)
            logger.info("Emitting summarization_finished signal")
            self.summarization_finished.emit()
    
    def request_text_generation(self, prompt_text: str, max_new_tokens: int = 250):
        """
        Request text generation from the AI Manager.

        Args:
            prompt_text (str): The prompt to generate text from.
            max_new_tokens (int): The maximum number of new tokens to generate.
        """
        logger.info(f"AIController.request_text_generation called with prompt: '{prompt_text[:50]}...' and max_new_tokens: {max_new_tokens}")
        try:
            self.ai_manager.generate_note_text(prompt_text, max_new_tokens=max_new_tokens)
        except Exception as e:
            logger.error(f"Exception in AIController.request_text_generation: {str(e)}")
            error_info = (type(e), e, traceback.format_exc())
            self.text_generation_error.emit(error_info)
            self.text_generation_finished.emit() # Ensure finished is emitted on error too

    def get_current_model(self):
        """Get the current AI model."""
        return self.ai_manager.get_current_model()
    
    def set_current_model(self, model_name):
        """Set the current AI model."""
        self.ai_manager.set_current_model(model_name)
    
    def preload_model(self, model_name):
        """Preload an AI model in the background."""
        self.ai_manager.preload_model(model_name)
    
    def get_available_models(self):
        """Get a list of available AI models."""
        try:
            # This part would need to be reimplemented if we want to list API models
            # For now, it returns a default or relies on settings dialog
            # For example, could return models specified in settings:
            # summarization_model = self.settings_model.get("ai", "huggingface_summarization_model_id", "facebook/bart-large-cnn")
            # generation_model = self.settings_model.get("ai", "huggingface_text_generation_model_id", "gpt2")
            # return [summarization_model, generation_model]
            logger.warning("AIController.get_available_models() is returning a placeholder. Needs review for API context.")
            return ["default"] # Placeholder
        except ImportError:
            logger.error("Required libraries for AI models are not installed")
            return ["default"]
        except Exception as e:
            logger.error(f"Error getting available models: {str(e)}")
            return ["default"]

    # --- Public Methods for Enhance Notes Feature ---
    def extract_entities(self, text: str):
        """Extract entities from the given text using EntityExtractionWorker."""
        logger.info(f"AIController: Starting entity extraction for text length: {len(text)}")
        self.entity_extraction_started.emit()

        try:
            # Ensure ai_manager is available and has the method
            if not hasattr(self.ai_manager, 'extract_entities_with_spacy'):
                logger.error("AIController: AIManager or extract_entities_with_spacy method not found.")
                self.entity_extraction_error.emit(("AttributeError", "AIManager or NER method not found.", traceback.format_exc()))
                self.entity_extraction_finished.emit()
                return

            # Get the model_id from settings, or use a default
            model_id = self.settings_model.get('ai', 'ner_model_id', 'en_core_web_sm') 

            worker = EntityExtractionWorker(
                extract_fn=self.ai_manager.extract_entities_with_spacy,
                text=text,
                model_id=model_id
            )
            worker.signals.result.connect(self._handle_entity_extraction_result)
            worker.signals.error.connect(self._handle_entity_extraction_error)
            worker.signals.finished.connect(self._handle_entity_extraction_finished)
            self.thread_pool.start(worker)
            logger.info(f"EntityExtractionWorker started in thread pool for model: {model_id}.")
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"AIController: Failed to start EntityExtractionWorker: {e}\n{tb_str}")
            self.entity_extraction_error.emit(("WorkerStartError", str(e), tb_str))
            self.entity_extraction_finished.emit() # Ensure finished is emitted on startup error

    # --- Private Handlers for EntityExtractionWorker Signals ---
    @pyqtSlot(object)
    def _handle_entity_extraction_result(self, entities_list):
        if entities_list is None:
            logger.warning("AIController: Received None from entity extraction worker. Emitting empty list.")
            self.entities_extracted.emit([])
            return
            
        logger.info(f"AIController: Entity extraction result received: {len(entities_list)} entities.")
        self.entities_extracted.emit(entities_list)

    @pyqtSlot(tuple)
    def _handle_entity_extraction_error(self, error_details):
        logger.error(f"AIController: Entity extraction error: {error_details[0]}")
        self.entity_extraction_error.emit(error_details)

    @pyqtSlot()
    def _handle_entity_extraction_finished(self):
        logger.info("AIController: Entity extraction finished.")
        self.entity_extraction_finished.emit()

    def summarize_text_with_worker(self, text: str):
        """Public method to trigger text summarization using the appropriate worker."""
        logger.info(f"AIController.summarize_text_with_worker called with text length: {len(text)}")
        try:
            worker = SummarizationWorker(text)
            worker.signals.result.connect(self._handle_summarization_result)
            worker.signals.error.connect(self._handle_summarization_error)
            worker.signals.finished.connect(self._handle_summarization_finished)
            self.thread_pool.start(worker)
            logger.info("SummarizationWorker started in thread pool.")
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"AIController: Failed to start SummarizationWorker: {e}\n{tb_str}")
            self.summarization_error.emit((str(e), tb_str))
            self.summarization_finished.emit() # Ensure finished is emitted even on startup error

    # --- Private Handlers for SummarizationWorker Signals ---
    @pyqtSlot(str)
    def _handle_summarization_result(self, summary_text):
        logger.info(f"AIController: Summarization result received: {summary_text}")
        self.summarization_result.emit(summary_text)

    @pyqtSlot(tuple)
    def _handle_summarization_error(self, error_details):
        # error_details is expected to be (exception_string, traceback_string)
        logger.error(f"AIController: Summarization error: {error_details[0]}")
        self.summarization_error.emit(error_details)

    @pyqtSlot()
    def _handle_summarization_finished(self):
        logger.info("AIController: Summarization finished.")
        self.summarization_finished.emit()

    def answer_question_from_context(self, question: str, context: str):
        """Request question answering from the AI Manager."""
        logger.info(f"AIController.answer_question_from_context called with question: '{question[:50]}...' and context length: {len(context)}")
        # self.ai_manager.answer_question_from_context(question, context) # To be uncommented
        self.question_answering_started.emit()

    def summarize_web_content(self, web_page_text: str):
        """Request web content summarization from the AI Manager."""
        logger.info(f"AIController.summarize_web_content called with text length: {len(web_page_text)}")
        # self.ai_manager.summarize_web_content(web_page_text) # To be uncommented
        self.web_content_summarization_started.emit()

    def search_web_for_entities(self, original_text: str, entities: list):
        """Orchestrate web searches for a list of entities as part of the enhancement pipeline."""
        logger.info(f"AIController: Starting web search for {len(entities)} entities.")
        self.web_search_for_enhancement_started.emit()

        # Select top N entities for search (e.g., first 3 strings)
        entity_queries = [str(entity) for entity in entities[:3] if str(entity).strip()] 

        if not entity_queries:
            logger.info("AIController: No valid entity queries to search. Emitting empty results.")
            self.web_search_for_enhancement_result.emit({
                'original_text': original_text,
                'entity_queries': [],
                'results_map': {}
            })
            # No self.web_search_for_enhancement_finished signal defined, result implies finished for this step
            return

        self._enhancement_web_search_data = {
            'original_text': original_text,
            'entity_queries': entity_queries,
            'results_map': {query: [] for query in entity_queries}, # Initialize with empty lists
            'pending_count': len(entity_queries)
        }

        try:
            # Connect to the WebController's signal for search results
            self.main_window.web_controller.web_search_result.connect(self._process_search_result_for_enhancement)
            # Consider connecting to a web_search_error signal if WebController provides one for individual searches
            # self.main_window.web_controller.web_search_error.connect(self._process_search_error_for_enhancement)
        except Exception as e:
            logger.error(f"AIController: Error connecting to WebController signals: {e}")
            self.web_search_for_enhancement_error.emit((str(e), traceback.format_exc()))
            self._enhancement_web_search_data = None
            return

        logger.info(f"AIController: Performing web searches for: {entity_queries}")
        for query in entity_queries:
            try:
                self.main_window.web_controller.perform_search(query)
            except Exception as e:
                logger.error(f"AIController: Error calling perform_search for query '{query}': {e}")
                # If one call fails, we should ideally handle it gracefully
                # For now, this might prevent _process_search_result if perform_search itself errors before signal connection
                # A more robust system might decrement pending_count here or have perform_search return status
                self._process_search_result_for_enhancement({'query': query, 'links': [], 'error': str(e)}) # Simulate an empty/error result

    @pyqtSlot(dict) # Assuming web_search_result emits a dict {'query': str, 'links': list, 'error': optional_str}
    def _process_search_result_for_enhancement(self, search_result_data):
        logger.info(f"AIController: _process_search_result_for_enhancement entered. Data: {search_result_data}")
        if not self._enhancement_web_search_data:
            logger.warning("AIController: Received web search result but no enhancement search is active. Ignoring.")
            return

        query = search_result_data.get('query')
        links = search_result_data.get('links', [])
        error = search_result_data.get('error')

        if query not in self._enhancement_web_search_data['entity_queries']:
            logger.warning(f"AIController: Received web search result for unexpected query '{query}'. Ignoring.")
            return
        
        logger.info(f"AIController: Received web search result for entity query: '{query}'. Links: {len(links)}")
        if error:
            logger.error(f"AIController: Error reported for web search query '{query}': {error}")
        
        self._enhancement_web_search_data['results_map'][query] = links
        self._enhancement_web_search_data['pending_count'] -= 1

        if self._enhancement_web_search_data['pending_count'] <= 0:
            logger.info("AIController: All entity web searches complete.")
            try:
                self.main_window.web_controller.web_search_result.disconnect(self._process_search_result_for_enhancement)
                # Disconnect error handler if it was connected
                # self.main_window.web_controller.web_search_error.disconnect(self._process_search_error_for_enhancement)
            except TypeError:
                logger.warning("AIController: Error disconnecting from WebController signals (already disconnected?).")
            except Exception as e:
                logger.error(f"AIController: Unexpected error disconnecting signals: {e}")
            
            self.web_search_for_enhancement_result.emit(self._enhancement_web_search_data)
            self._enhancement_web_search_data = None # Reset state

    def fetch_content_and_perform_qna(self, original_text: str, entities: list, web_search_results_map: dict):
        """Fetch content from web links and then initiate Question Answering for note enhancement."""
        logger.info(f"AIController: Starting content fetching for Q&A. {len(web_search_results_map)} entity searches provided.")
        self.answer_extraction_started.emit() # Signal that this phase has begun

        # Select top N unique links to fetch content from
        links_to_fetch = []
        max_links_to_fetch = self.settings_model.get('ai', 'max_links_for_qna', 3)
        seen_urls = set()

        for _entity_query, search_result_item_list in web_search_results_map.items():
            if not isinstance(search_result_item_list, list):
                logger.warning(f"Expected list of link dictionaries for query '{_entity_query}', got {type(search_result_item_list)}. Skipping.")
                continue
            for link_dict in search_result_item_list: # link_dict is {'title': ..., 'url': ..., 'snippet': ...}
                actual_url = link_dict.get('url')
                if not actual_url:
                    logger.warning(f"Link dictionary for query '{_entity_query}' missing 'url' key or URL is empty: {link_dict}")
                    continue

                if actual_url not in seen_urls:
                    links_to_fetch.append(actual_url)  # Append the URL string
                    seen_urls.add(actual_url)        # Add the URL string to the set
                if len(links_to_fetch) >= max_links_to_fetch:
                    break
            if len(links_to_fetch) >= max_links_to_fetch:
                break
        
        logger.info(f"AIController: Selected {len(links_to_fetch)} unique links for content fetching: {links_to_fetch}")

        if not links_to_fetch:
            logger.info("AIController: No links selected or available to fetch for Q&A. Emitting error.")
            self.answer_extraction_error.emit(("NoLinksForQ&A", "No web links were available to fetch content for Q&A.", traceback.format_exc()))
            # Consider if a different signal or a specific type of result should be emitted
            # For now, error signal seems appropriate as Q&A cannot proceed.
            return

        self._qna_process_data = {
            'original_text': original_text,
            'entities': entities,
            'links_to_fetch': links_to_fetch,
            'fetched_content_items': [],
            'pending_fetches_count': len(links_to_fetch)
        }

        try:
            self.main_window.web_controller.content_fetch_result.connect(self._on_qna_content_fetched)
            self.main_window.web_controller.content_fetch_error.connect(self._on_qna_content_fetch_error)
        except Exception as e:
            logger.error(f"AIController: Error connecting to WebController content fetch signals: {e}")
            self.answer_extraction_error.emit(("SignalConnectionError", str(e), traceback.format_exc()))
            self._qna_process_data = None
            return

        for url in links_to_fetch:
            logger.info(f"AIController: Requesting content fetch for Q&A: {url}")
            try:
                # Pass context to identify these fetches are for the Q&A enhancement step
                self.main_window.web_controller.fetch_url_content(url, context={'type': 'qna_enhancement', 'url': url})
            except Exception as e:
                logger.error(f"AIController: Error calling fetch_url_content for '{url}': {e}")
                # Simulate an error for this specific fetch to maintain pending_fetches_count logic
                self._on_qna_content_fetch_error({'url': url, 'error': str(e), 'context': {'type': 'qna_enhancement', 'url': url}, 'traceback': traceback.format_exc()})

    @pyqtSlot(dict)
    def _on_qna_content_fetched(self, fetch_data):
        """Handles a successfully fetched piece of web content for the Q&A pipeline."""
        if not self._qna_process_data or fetch_data.get('context', {}).get('type') != 'qna_enhancement':
            logger.debug("AIController: Received non-Q&A or unexpected content fetch result. Ignoring.")
            return

        url = fetch_data.get('url')
        content = fetch_data.get('content', '')
        logger.info(f"AIController: Content fetched for Q&A from {url}. Length: {len(content)}")
        
        self._qna_process_data['fetched_content_items'].append({'url': url, 'content': content})
        self._qna_process_data['pending_fetches_count'] -= 1

        if self._qna_process_data['pending_fetches_count'] <= 0:
            self._finalize_content_fetching_and_start_qna()

    @pyqtSlot(dict) # Assuming error_data: {'url': str, 'error': str, 'context': dict, 'traceback': str}
    def _on_qna_content_fetch_error(self, error_data):
        """Handles an error from fetching a piece of web content for the Q&A pipeline."""
        if not self._qna_process_data or error_data.get('context', {}).get('type') != 'qna_enhancement':
            logger.debug("AIController: Received non-Q&A or unexpected content fetch error. Ignoring.")
            return

        url = error_data.get('url')
        error_msg = error_data.get('error', 'Unknown fetch error')
        logger.error(f"AIController: Error fetching content for Q&A from {url}: {error_msg}")

        # We still decrement count, as this fetch attempt is concluded (albeit with failure)
        self._qna_process_data['pending_fetches_count'] -= 1

        if self._qna_process_data['pending_fetches_count'] <= 0:
            self._finalize_content_fetching_and_start_qna()
            
    def _finalize_content_fetching_and_start_qna(self):
        """Called when all content fetching attempts (success or error) are complete."""
        logger.info("AIController: All content fetch attempts for Q&A complete.")
        if not self._qna_process_data: # Should not happen if called correctly
            logger.error("AIController: _finalize_content_fetching_and_start_qna called with no active QNA process data.")
            return

        fetched_items = self._qna_process_data.get('fetched_content_items', [])
        collated_content_parts = [item['content'] for item in fetched_items if item.get('content') and isinstance(item.get('content'), str)]
        web_content_collated = "\n\n---\n\n".join(collated_content_parts).strip()

        if not web_content_collated:
            logger.warning("AIController: No usable web content was fetched. Aborting Q&A for enhancement.")
            self.answer_extraction_error.emit(("NoContentFetched", "No usable web content was fetched for Q&A.", traceback.format_exc()))
            self._qna_process_data = None # Clean up state
            self.answer_extraction_finished.emit() # Signal completion of this attempt
            # Disconnect WebController signals if they were connected and are not auto-managed by WebController upon completion/error
            try:
                self.main_window.web_controller.content_fetch_result.disconnect(self._on_qna_content_fetched)
                self.main_window.web_controller.content_fetch_error.disconnect(self._on_qna_content_fetch_error)
            except TypeError: # Already disconnected or never connected
                pass 
            except Exception as e_disconnect:
                logger.error(f"AIController: Error disconnecting content fetch signals: {e_disconnect}")
            return

        original_text = self._qna_process_data['original_text']
        entities = self._qna_process_data['entities']

        logger.info(f"AIController: Triggering Q&A on collated content (length: {len(web_content_collated)}) via AIManager.")
        self.ai_manager.trigger_qna_on_enhanced_content(original_text, entities, web_content_collated)
        
        # Note: self._qna_process_data is now cleaned up in _on_manager_enhancement_qna_finished
        # or here if no content was fetched.
        # Disconnect web_controller signals as this content fetching phase is done.
        try:
            self.main_window.web_controller.content_fetch_result.disconnect(self._on_qna_content_fetched)
            self.main_window.web_controller.content_fetch_error.disconnect(self._on_qna_content_fetch_error)
        except TypeError: # Already disconnected or never connected
            logger.debug("AIController: Content fetch signals for Q&A already disconnected or were not connected.")
        except Exception as e_disconnect:
            logger.error(f"AIController: Error disconnecting content fetch signals after triggering Q&A: {e_disconnect}")

    @pyqtSlot(object) # Result from AIManager's Q&A (Now comes from AIManager via _on_manager_enhancement_qna_result)
    def _on_qna_worker_result(self, qna_results):
        logger.info(f"AIController: Q&A results received: {type(qna_results)}")
        self.answer_extracted.emit(qna_results)

    @pyqtSlot(tuple) # Error from AIManager's Q&A (Now comes from AIManager via _on_manager_enhancement_qna_error)
    def _on_qna_worker_error(self, error_details):
        err_type, err_msg, tb_str = error_details
        logger.error(f"AIController: Q&A error: {err_type.__name__}: {err_msg}")
        self.answer_extraction_error.emit((err_type.__name__, err_msg, tb_str)) 

    @pyqtSlot()
    def _on_qna_worker_finished(self):
        logger.info("AIController: Q&A finished.")
        if self._qna_process_data: # Check if it hasn't been cleared by an error path already
            self._qna_process_data = None # Clear QNA process data
        # The main note_enhancement_sequence_finished or error signal will be emitted by MainWindow later

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

_AICONTR_ERROR_AIMANAGER_NOT_INIT = "AIManager not initialized"

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
    web_search_for_enhancement_finished = pyqtSignal() # Added signal
    
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
        
        self.pending_qna_web_requests = {} # For Q&A context management

        # Connect signals from WebController if AIController needs to react to web fetches it initiates
        if self.main_window and hasattr(self.main_window, 'web_controller'):
            self.main_window.web_controller.content_fetch_result.connect(self._handle_web_content_for_qna)
            self.main_window.web_controller.content_fetch_error.connect(self._handle_web_content_error_for_qna)

    # --- Public Methods to Trigger AI Operations ---
    def summarize_text(self, text: str):
        """Request text summarization from the AI Manager."""
        logger.info("AIController: summarize_text called.")
        if hasattr(self, 'ai_manager') and self.ai_manager:
            self.ai_manager.summarize_text(text)
        else:
            logger.error(f"AIController: AIManager not available for summarization. {_AICONTR_ERROR_AIMANAGER_NOT_INIT}")
            self.summarization_error.emit((type(AttributeError(_AICONTR_ERROR_AIMANAGER_NOT_INIT)), AttributeError(_AICONTR_ERROR_AIMANAGER_NOT_INIT), None))

    def request_text_generation(self, prompt_text: str, max_new_tokens: int = 1024):
        """Request text generation from the AI Manager."""
        logger.info("AIController: request_text_generation called.")
        if hasattr(self, 'ai_manager') and self.ai_manager:
            self.ai_manager.generate_text(prompt_text, max_new_tokens)
        else:
            logger.error(f"AIController: AIManager not available for text generation. {_AICONTR_ERROR_AIMANAGER_NOT_INIT}")
            self.text_generation_error.emit((type(AttributeError(_AICONTR_ERROR_AIMANAGER_NOT_INIT)), AttributeError(_AICONTR_ERROR_AIMANAGER_NOT_INIT), None))

    def extract_entities(self, text: str):
        """Request entity extraction from the AI Manager."""
        logger.info("AIController: extract_entities called.")
        if hasattr(self, 'ai_manager') and self.ai_manager:
            self.ai_manager.request_entity_extraction(text)
        else:
            logger.error(f"AIController: AIManager not available for entity extraction. {_AICONTR_ERROR_AIMANAGER_NOT_INIT}")
            self.entity_extraction_error.emit((type(AttributeError(_AICONTR_ERROR_AIMANAGER_NOT_INIT)), AttributeError(_AICONTR_ERROR_AIMANAGER_NOT_INIT), None))

    def search_web_for_entities(self, original_note_text: str, entities: list):
        """Request web search for entities from the AI Manager."""
        logger.info(f"AIController: search_web_for_entities called for {len(entities)} entities.")
        if hasattr(self, 'ai_manager') and self.ai_manager:
            # This method will be created in AIManager
            self.ai_manager.request_web_search_for_entities(original_note_text, entities)
        else:
            logger.error(f"AIController: AIManager not available for web search for entities. {_AICONTR_ERROR_AIMANAGER_NOT_INIT}")
            # Use the existing web_search_for_enhancement_error signal
            self.web_search_for_enhancement_error.emit((type(AttributeError(_AICONTR_ERROR_AIMANAGER_NOT_INIT)), AttributeError(_AICONTR_ERROR_AIMANAGER_NOT_INIT), None))

    # --- AI Manager Signal Handlers ---
    def _connect_ai_manager_signals(self):
        """Connect signals from AIManager to AIController's handlers."""
        if not hasattr(self, 'ai_manager') or self.ai_manager is None:
            logger.error("AIController: AIManager not initialized before connecting signals.")
            return

        # Summarization signals
        self.ai_manager.summarization_started_signal.connect(self._handle_task_started_status) # Generic handler
        self.ai_manager.summarization_progress_signal.connect(self.summarization_progress) # Direct pass-through
        self.ai_manager.summarization_result_signal.connect(self._handle_summarization_result)
        self.ai_manager.summarization_error_signal.connect(self._handle_summarization_error)
        self.ai_manager.summarization_finished_signal.connect(self.summarization_finished) # Direct pass-through

        # Text Generation signals
        self.ai_manager.text_generation_started_signal.connect(self._handle_task_started_status) # Generic handler
        self.ai_manager.text_generation_progress_signal.connect(self.text_generation_progress) # Direct pass-through
        self.ai_manager.text_generation_result_signal.connect(self._handle_text_generation_result)
        self.ai_manager.text_generation_error_signal.connect(self._handle_text_generation_error)
        self.ai_manager.text_generation_finished_signal.connect(self.text_generation_finished) # Direct pass-through
        
        # Entity Extraction signals
        self.ai_manager.entity_extraction_started_signal.connect(self.entity_extraction_started.emit)
        self.ai_manager.entity_extraction_result_signal.connect(self.entities_extracted.emit)
        self.ai_manager.entity_extraction_error_signal.connect(self.entity_extraction_error.emit)
        self.ai_manager.entity_extraction_finished_signal.connect(self.entity_extraction_finished.emit)

        # Web Search for Enhancement signals
        self.ai_manager.web_search_for_enhancement_started_signal.connect(self.web_search_for_enhancement_started.emit)
        self.ai_manager.web_search_for_enhancement_result_signal.connect(self.web_search_for_enhancement_result.emit)
        self.ai_manager.web_search_for_enhancement_error_signal.connect(self.web_search_for_enhancement_error.emit)
        if hasattr(self.ai_manager, 'web_search_for_enhancement_finished_signal') and hasattr(self, 'web_search_for_enhancement_finished'):
            self.ai_manager.web_search_for_enhancement_finished_signal.connect(self.web_search_for_enhancement_finished.emit)

        # General error signal from AIManager (e.g., config issues)
        self.ai_manager.general_error_signal.connect(self._handle_ai_manager_general_error)

    @pyqtSlot(str)  # result_text
    def _handle_summarization_result(self, result_text: str):
        logger.info("AIController: Received summarization result.")
        self.summarization_result.emit(result_text)
        self.summarization_finished.emit()

    @pyqtSlot(tuple)  # error_tuple (e.g., (type, value, tb_str))
    def _handle_summarization_error(self, error_tuple: tuple):
        error_type = error_tuple[0] if len(error_tuple) > 0 else Exception
        error_message = str(error_tuple[1]) if len(error_tuple) > 1 else str(error_type)
        tb_str = error_tuple[2] if len(error_tuple) > 2 else ""
        
        logger.error(f"AIController: Received summarization error: {error_message}")
        # Emit a 3-tuple: (Exception Type, Formatted Message, Traceback String)
        self.summarization_error.emit((error_type, f"Summarization Failed: {error_message}", tb_str))
        self.summarization_finished.emit()

    @pyqtSlot(str)  # generated_text
    def _handle_text_generation_result(self, generated_text: str):
        logger.info("AIController: Received text generation result.")
        self.text_generation_result.emit(generated_text)
        self.text_generation_finished.emit()

    @pyqtSlot(tuple)  # error_tuple (e.g., (type, value, tb_str))
    def _handle_text_generation_error(self, error_tuple: tuple):
        error_message = str(error_tuple[1]) if len(error_tuple) > 1 else str(error_tuple[0])
        logger.error("AIController: Received text generation error: " + error_message)
        # Ensure the full error details (type, message, traceback) are propagated
        if len(error_tuple) == 3:
            self.text_generation_error.emit(error_tuple)
        elif len(error_tuple) == 2:
            # If AIManager sent a 2-tuple, adapt it. Preferable to fix AIManager.
            logger.warning("AIController: Received 2-tuple error from AIManager. Adapting to 3-tuple with None traceback.")
            self.text_generation_error.emit((error_tuple[0], error_tuple[1], None))
        else:
            # Fallback for unexpected tuple size
            logger.error(f"AIController: Received unexpected error_tuple size: {len(error_tuple)}. Emitting generic error.")
            self.text_generation_error.emit((RuntimeError, "Unknown error structure from AIManager", None))
        self.text_generation_finished.emit()

    @pyqtSlot() # Connected to summarization_started_signal and text_generation_started_signal
    def _handle_task_started_status(self):
        # Determine which task started if necessary, or use a generic message
        # For now, a generic log. Could be enhanced to show specific task type.
        sender_signal_name = self.sender().objectName() if self.sender() else "UnknownSignal"
        
        if "summarization" in sender_signal_name:
            task_name = "Summarization"
        elif "generation" in sender_signal_name:
            task_name = "Text Generation"
        else:
            task_name = "AI Task"
            
        status_message = task_name + " started by AIManager."
        logger.info("AIController: AIManager status update: " + status_message)
        # Emit a general status signal or update UI if needed
        # Example: self.main_window.show_status_message(status_message)

    @pyqtSlot(str)  # error_message
    def _handle_ai_manager_general_error(self, error_message: str):
        logger.error("AIController: Received general error from AIManager: " + error_message)
        # Potentially show this in a dialog via MainWindow
        if hasattr(self.main_window, 'show_error_message'):
            self.main_window.show_error_message("AI System Error", error_message)
        else:
            # Fallback if main_window doesn't have show_error_message
            self.text_generation_error.emit(("AI System Error", error_message)) 

    def request_qna_on_web_content(self, question: str, url: str, note_context_for_qna: str):
        """Request Q&A on content from a specific URL, using note context."""
        logger.info("AIController: Requesting Q&A for URL '" + url + "' with question: '" + question[:50] + "...' Note context length: " + str(len(note_context_for_qna)))
        
        # Store context for when the web content is fetched
        # Using URL as key. If multiple concurrent requests for the same URL with different questions
        # are expected, a more robust unique ID per request would be needed.
        request_context = {
            'question': question,
            'note_context_for_qna': note_context_for_qna,
            'url': url # Store URL for safety, though it's the key
        }
        self.pending_qna_web_requests[url] = request_context
        
        # Initiate fetching of the web content. WebController.fetch_url_content now just calls fetch_content.
        # The context is not passed to fetch_url_content for signal injection anymore.
        self.main_window.web_controller.fetch_url_content(url) # Pass only URL

    def _handle_web_content_for_qna(self, result_data: dict):
        """Slot to handle successfully fetched web content intended for Q&A."""
        url = result_data.get('url')
        content = result_data.get('content')
        success = result_data.get('success', False)

        logger.debug("AIController: Received web content for Q&A. URL: " + url + ", Success: " + str(success))

        if url in self.pending_qna_web_requests:
            request_context = self.pending_qna_web_requests.pop(url)
            question = request_context['question']
            note_context = request_context['note_context_for_qna']

            if success and content:
                logger.info("Content for " + url + " fetched successfully. Proceeding with Q&A.")
                # Now, perform Q&A on the fetched content
                # This part needs to be asynchronous if it's slow
                try:
                    # Assuming self.ai_utils.answer_question_from_text can handle this
                    # Make this call asynchronous using a Worker
                    worker = Worker(self.ai_utils.answer_question_from_text, question, content, note_context)
                    
                    # Pass necessary context to the lambda functions for signal emission
                    # Use a partial or ensure lambda captures current values correctly
                    from functools import partial
                    on_qna_result_lambda = partial(self._emit_qna_result, url=url, question=question, original_note_context=note_context)
                    on_qna_error_lambda = partial(self._emit_qna_error, url=url, question=question, original_note_context=note_context)

                    worker.signals.result.connect(on_qna_result_lambda)
                    worker.signals.error.connect(on_qna_error_lambda)
                    self.thread_pool.start(worker)
                    logger.info("Q&A worker started for URL: " + url)

                except Exception as e:
                    logger.error("Error starting Q&A worker for " + url + ": " + str(e))
                    self.answer_extraction_error.emit({'url': url, 'question': question, 'error': str(e), 'context': note_context, 'traceback': traceback.format_exc()})
            elif success and not content:
                logger.warning("Content for " + url + " was empty, though fetch reported success.")
                self.answer_extraction_error.emit({'url': url, 'question': question, 'error': 'Fetched content was empty.', 'context': note_context})
            else: # Not success
                error_msg = result_data.get('error', 'Unknown error during content fetch for Q&A.')
                logger.error("Failed to fetch content for Q&A from " + url + ": " + error_msg)
                self.answer_extraction_error.emit({'url': url, 'question': question, 'error': error_msg, 'context': note_context})
        else:
            logger.warning("AIController: Received web content for URL '" + url + "' but no pending Q&A request found. Ignoring.")

    def _handle_web_content_error_for_qna(self, error_data: dict):
        """Slot to handle errors when fetching web content intended for Q&A."""
        url = error_data.get('url')
        error_message = error_data.get('error', 'Unknown web content fetch error')

        logger.debug("AIController: Received web content fetch ERROR for Q&A. URL: " + url + ", Error: " + error_message)

        if url in self.pending_qna_web_requests:
            request_context = self.pending_qna_web_requests.pop(url)
            question = request_context['question']
            note_context = request_context['note_context_for_qna']
            
            logger.error("Error fetching content for Q&A from " + url + ": " + error_message)
            self.answer_extraction_error.emit({'url': url, 'question': question, 'error': error_message, 'context': note_context})
        else:
            logger.warning("AIController: Received web content error for URL '" + url + "' but no pending Q&A request found. Ignoring.")

    def _emit_qna_result(self, answer, url, question, original_note_context):
        """Helper to emit Q&A result signal with full context."""
        if answer:
            logger.info("Answer extracted for " + url + ": " + answer[:100] + "...")
            self.answer_extracted.emit({'url': url, 'question': question, 'answer': answer, 'context': original_note_context})
        else:
            logger.warning("No answer extracted for " + url + " by Q&A worker.")
            self.answer_extraction_error.emit({'url': url, 'question': question, 'error': 'No answer found by AI (worker).', 'context': original_note_context})

    def _emit_qna_error(self, error_info, url, question, original_note_context):
        """Helper to emit Q&A error signal with full context."""
        # error_info from Worker is typically (exception_instance, traceback_string) or (type, value, tb_obj)
        err_msg = str(error_info[0]) if isinstance(error_info, tuple) and len(error_info) > 0 else "Unknown Q&A worker error"
        tb_str = error_info[1] if isinstance(error_info, tuple) and len(error_info) > 1 and isinstance(error_info[1], str) else traceback.format_exc()
        logger.error("Error during Q&A processing by worker for " + url + ": " + err_msg)
        self.answer_extraction_error.emit({'url': url, 'question': question, 'error': err_msg, 'context': original_note_context, 'traceback': tb_str})

    def request_enhancement_suggestions(self, note_content: str, web_links: list = None):
        """Request suggestions for enhancing the note content, optionally using web links."""
        logger.info("Requesting enhancement suggestions for note (first 50 chars): " + note_content[:50] + "...")
        self.enhancement_error.emit({
            'error': 'Enhancement suggestion feature not fully implemented yet.', 
            'details': 'AIController.request_enhancement_suggestions needs to be built out.'
        })

    # --- Model Management ---

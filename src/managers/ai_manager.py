#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI manager for the Smart Contextual Notes Editor.
Handles AI operations like summarization and model management.
"""

import logging
import os
from PyQt5.QtCore import QObject, QThreadPool, pyqtSignal, pyqtSlot

# Import AI utilities and workers
from backend.ai_utils import summarize_text_local, generate_text_hf_api, perform_question_answering, extract_entities_spacy
from utils.threads import LocalSummarizationWorker, ApiTextGenerationWorker, QuestionAnsweringWorker

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIManager(QObject):
    """Manager for AI operations, focusing on local summarization."""
    
    # Signals for summarization
    summarization_started_signal = pyqtSignal()
    summarization_progress_signal = pyqtSignal(int)
    summarization_result_signal = pyqtSignal(str)
    summarization_error_signal = pyqtSignal(tuple)
    summarization_finished_signal = pyqtSignal()
    
    # Signals for text generation
    text_generation_started_signal = pyqtSignal()
    text_generation_progress_signal = pyqtSignal(int)
    text_generation_result_signal = pyqtSignal(str)
    text_generation_error_signal = pyqtSignal(tuple)
    text_generation_finished_signal = pyqtSignal()
    
    # Signals for Q&A on enhanced content
    qna_started_signal = pyqtSignal()
    qna_result_signal = pyqtSignal(dict)  # Emits a dictionary of Q&A results
    qna_error_signal = pyqtSignal(tuple)
    qna_finished_signal = pyqtSignal()
    
    def __init__(self, parent=None, settings=None):
        """Initialize the AI manager."""
        super().__init__(parent)
        
        # Store the parent for callbacks
        self.parent = parent
        
        # Store settings
        self.settings_model = settings
        
        # Thread pool for background tasks
        self.thread_pool = QThreadPool.globalInstance()
    
    def summarize_text(self, text):
        """
        Generate a summary of the given text using local pipeline.
        
        Args:
            text (str): The text to summarize
            
        Raises:
            RuntimeError: If an error occurs during summarization.
        """
        logger.info(f"AIManager.summarize_text (Local Pipeline) called with text of length: {len(text)}")
        
        try:
            huggingface_model_id = self.settings_model.get("ai", "huggingface_summarization_model_id", "facebook/bart-large-cnn")
            
            logger.info(f"Using local pipeline for summarization with model: {huggingface_model_id}")
            
            # Create a worker for the local summarization task
            worker = LocalSummarizationWorker(
                summarize_text_local,
                text,
                model_id=huggingface_model_id 
            )
            logger.info(f"LocalSummarizationWorker created with model: {huggingface_model_id}")
            
            # Connect signals (common for both worker types)
            logger.info("Connecting worker signals to parent callbacks")
            signal_connections = 0
            
            if hasattr(self.parent, '_on_summarization_started'):
                logger.info("Connecting 'started' signal")
                worker.signals.started.connect(self.parent._on_summarization_started)
                signal_connections += 1
            else:
                logger.warning("Parent does not have '_on_summarization_started' method")
            
            if hasattr(self.parent, '_on_summarization_progress'):
                logger.info("Connecting 'progress' signal")
                worker.signals.progress.connect(self.parent._on_summarization_progress)
                signal_connections += 1
            else:
                logger.warning("Parent does not have '_on_summarization_progress' method")
            
            if hasattr(self.parent, '_on_summarization_result'):
                logger.info("Connecting 'result' signal")
                worker.signals.result.connect(self.parent._on_summarization_result)
                signal_connections += 1
            else:
                logger.warning("Parent does not have '_on_summarization_result' method")
            
            if hasattr(self.parent, '_on_summarization_error'):
                logger.info("Connecting 'error' signal")
                worker.signals.error.connect(self.parent._on_summarization_error)
                signal_connections += 1
            else:
                logger.warning("Parent does not have '_on_summarization_error' method")
            
            if hasattr(self.parent, '_on_summarization_finished'):
                logger.info("Connecting 'finished' signal")
                worker.signals.finished.connect(self.parent._on_summarization_finished)
                signal_connections += 1
            else:
                logger.warning("Parent does not have '_on_summarization_finished' method")
            
            logger.info(f"Connected {signal_connections} signals successfully")
            
            # Execute the worker
            if worker:
                logger.info("Starting worker in thread pool")
                self.thread_pool.start(worker)
                logger.info("Worker started in thread pool")
            else:
                # This case should ideally not be reached if LocalSummarizationWorker instantiation is robust
                logger.error("LocalSummarizationWorker could not be initialized.")
                if hasattr(self.parent, '_on_summarization_error'):
                    error_tuple = (RuntimeError, "LocalSummarizationWorker initialization failed", "No traceback available.")
                    self.parent._on_summarization_error(error_tuple)

        except Exception as e:
            logger.error(f"Error during local summarization setup: {str(e)}")
            if hasattr(self.parent, '_on_summarization_error'):
                import traceback
                error_tuple = (type(e), str(e), traceback.format_exc())
                self.parent._on_summarization_error(error_tuple)
            # Optionally re-raise or handle further if needed

    def generate_note_text(self, prompt_text: str, max_new_tokens: int = 150):
        """
        Generate text for a new note using Hugging Face API.
        
        Args:
            prompt_text (str): The prompt to generate text from.
            max_new_tokens (int): The maximum number of new tokens to generate.
            
        Raises:
            RuntimeError: If API key is missing or an error occurs during text generation.
        """
        logger.info(f"AIManager.generate_note_text called with prompt: '{prompt_text[:50]}...' and max_new_tokens: {max_new_tokens}")
        
        try:
            # Prioritize API key from environment variable
            huggingface_api_key = os.environ.get("HUGGINGFACE_API_KEY")
            if not huggingface_api_key:
                logger.info("HUGGINGFACE_API_KEY not found in environment. Checking settings.ini.")
                huggingface_api_key = self.settings_model.get("ai", "huggingface_api_key", "")
            else:
                logger.info("HUGGINGFACE_API_KEY loaded from environment.")

            huggingface_model_id = self.settings_model.get("ai", "huggingface_text_generation_model_id", "gpt2")
            
            if not huggingface_api_key:
                logger.error("Hugging Face API key is missing. Cannot generate text.")
                # Emit AIManager's own error signal
                error_tuple = (RuntimeError, "Hugging Face API key is missing.", "No traceback available for missing API key.")
                self.text_generation_error_signal.emit(error_tuple)
                return

            logger.info(f"Using Hugging Face API for text generation with model: {huggingface_model_id}")
            
            worker = ApiTextGenerationWorker(
                generate_text_hf_api,
                prompt_text=prompt_text,
                api_key=huggingface_api_key,
                model_id=huggingface_model_id,
                max_new_tokens=max_new_tokens
            )
            logger.info(f"ApiTextGenerationWorker created with model: {huggingface_model_id}")

            # Connect signals for text generation to internal AIManager handlers
            logger.info("Connecting text generation worker signals to AIManager's internal handlers")
            worker.signals.started.connect(self._handle_worker_generation_started)
            worker.signals.progress.connect(self._handle_worker_generation_progress) # Though likely unused for HF API gen
            worker.signals.result.connect(self._handle_worker_generation_result)
            worker.signals.error.connect(self._handle_worker_generation_error)
            worker.signals.finished.connect(self._handle_worker_generation_finished)
            
            logger.info(f"Connected {5} signals for text generation successfully to AIManager handlers")
            
            # Start the worker in the thread pool
            self.thread_pool.start(worker)
            logger.info("ApiTextGenerationWorker started in thread pool")

        except Exception as e:
            logger.error(f"Error during API text generation setup: {str(e)}")
            # Emit AIManager's own error signal
            import traceback
            error_tuple = (type(e), str(e), traceback.format_exc())
            self.text_generation_error_signal.emit(error_tuple)
            self.text_generation_finished_signal.emit() # Ensure finished is emitted in case of setup error
            # Optionally re-raise or handle further if needed

    # --- Internal Handlers for Text Generation Worker --- 
    def _handle_worker_generation_started(self):
        logger.debug("AIManager: Worker generation started, emitting AIManager signal.")
        self.text_generation_started_signal.emit()

    def _handle_worker_generation_progress(self, percentage: int):
        logger.debug(f"AIManager: Worker generation progress {percentage}%, emitting AIManager signal.")
        self.text_generation_progress_signal.emit(percentage)

    def _handle_worker_generation_result(self, generated_text: str):
        logger.debug("AIManager: Worker generation result received, emitting AIManager signal.")
        self.text_generation_result_signal.emit(generated_text)

    def _handle_worker_generation_error(self, error_details: tuple):
        logger.debug("AIManager: Worker generation error received, emitting AIManager signal.")
        self.text_generation_error_signal.emit(error_details)

    def _handle_worker_generation_finished(self):
        logger.debug("AIManager: Worker generation finished, emitting finished signal.")
        self.text_generation_finished_signal.emit()

    def trigger_qna_on_enhanced_content(self, original_note_text: str, extracted_entities: list, web_content_collated: str):
        """Triggers Question Answering on collated web content using a worker."""
        logger.info(f"AIManager.trigger_qna_on_enhanced_content called. Entities count: {len(extracted_entities)}, Web content length: {len(web_content_collated)}")    
        self.qna_started_signal.emit()

        try:
            ai_settings = self.settings_model.get_ai_settings() if hasattr(self.settings_model, 'get_ai_settings') else {}
            qna_model_id = ai_settings.get('qna_model_id', 'distilbert-base-cased-distilled-squad')
            
            worker = QuestionAnsweringWorker(
                qna_fn=perform_question_answering, # Relies on top-level import
                original_note_text=original_note_text,
                extracted_entities=extracted_entities,
                web_content_collated=web_content_collated,
                qna_model_id=qna_model_id
            )
            logger.info(f"QuestionAnsweringWorker created for model: {qna_model_id}")

            # Connect worker signals to AIManager's internal handlers
            worker.signals.result.connect(self._handle_worker_qna_result)
            worker.signals.error.connect(self._handle_worker_qna_error)
            worker.signals.finished.connect(self._handle_worker_qna_finished)
            
            self.thread_pool.start(worker)
            logger.info("QuestionAnsweringWorker started in thread pool.")

        except ImportError as ie:
            logger.error(f"AIManager: ImportError setting up QuestionAnsweringWorker - perform_question_answering likely not found: {ie}")
            import traceback
            self.qna_error_signal.emit((type(ie), str(ie), traceback.format_exc()))
            self.qna_finished_signal.emit()
        except Exception as e:
            logger.error(f"AIManager: Error setting up QuestionAnsweringWorker: {e}")
            import traceback
            self.qna_error_signal.emit((type(e), str(e), traceback.format_exc()))
            self.qna_finished_signal.emit()

    # --- Internal Handlers for Q&A Worker --- 
    @pyqtSlot(dict)
    def _handle_worker_qna_result(self, qna_results: dict):
        logger.info(f"AIManager: Q&A worker returned result: {list(qna_results.keys()) if isinstance(qna_results, dict) else type(qna_results)}")
        self.qna_result_signal.emit(qna_results)

    @pyqtSlot(tuple)
    def _handle_worker_qna_error(self, error_details: tuple):
        logger.error(f"AIManager: Q&A worker error: {error_details[0].__name__}: {error_details[1]}")
        self.qna_error_signal.emit(error_details)

    @pyqtSlot()
    def _handle_worker_qna_finished(self):
        logger.info("AIManager: Q&A worker finished, emitting finished signal.")
        self.qna_finished_signal.emit()

    def extract_entities_with_spacy(self, text: str, model_id: str = 'en_core_web_sm', **kwargs):
        logger.debug(f"AIManager.extract_entities_with_spacy called with model: {model_id}")
        progress_callback = kwargs.get('progress_callback')
        try:
            return extract_entities_spacy(text, model_id, progress_callback=progress_callback)
        except Exception as e:
            logger.error(f"Error calling extract_entities_spacy from AIManager: {e}")
            # Ensure an empty list is returned on error to match expected type
            return []

    # ... (rest of the code remains the same)

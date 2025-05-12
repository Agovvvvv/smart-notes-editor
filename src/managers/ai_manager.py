#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI manager for the Smart Contextual Notes Editor.
Handles AI operations like summarization and model management.
"""

import logging
import os
import traceback # Added for error handling
from PyQt5.QtCore import QObject, QThreadPool, pyqtSignal, pyqtSlot

# Import AI utilities and workers
from backend.ai_utils import (
    summarize_text_local,
    summarize_text_hf_api,
    summarize_text_gemini_api,
    generate_text_hf_api,
    generate_text_gemini_api,
    configure_gemini_api, # For initializing Gemini API
    extract_entities_spacy      # Keep for existing entity functionality
)
from utils.threads import (
    LocalSummarizationWorker,
    ApiSummarizationWorker,      # Assuming this is for Hugging Face summarization
    GeminiSummarizationWorker,
    ApiTextGenerationWorker,     # Assuming this is for Hugging Face text generation
    GeminiTextGenerationWorker,
    EntityExtractionWorker,     # Keep for existing entity functionality
)

logger = logging.getLogger(__name__)

class AIManager(QObject):
    """Manager for AI operations, supporting multiple backends."""
    
    # Default Model IDs Constants
    DEFAULT_LOCAL_SUMMARIZATION_MODEL = "facebook/bart-large-cnn"
    DEFAULT_HF_SUMMARIZATION_MODEL = "facebook/bart-large-cnn"
    DEFAULT_HF_TEXT_GENERATION_MODEL = "mistralai/Mistral-7B-Instruct-v0.2" # Changed from gpt2
    GEMINI_2_0_FLASH = "gemini-2.0-flash"  # Centralized constant for this model
    DEFAULT_GEMINI_SUMMARIZATION_MODEL = GEMINI_2_0_FLASH # Default for summarization
    DEFAULT_GEMINI_GENERATION_MODEL = GEMINI_2_0_FLASH # Default for text generation
    DEFAULT_GEMINI_MODEL = GEMINI_2_0_FLASH # Default for both summarization and text gen
    DEFAULT_ENTITY_EXTRACTION_MODEL = "en_core_web_sm" # Default spaCy model
    
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
    
    # Signals for Entity Extraction
    entity_extraction_started_signal = pyqtSignal()
    entity_extraction_result_signal = pyqtSignal(list)  # Emits a list of entities
    entity_extraction_error_signal = pyqtSignal(tuple)
    entity_extraction_finished_signal = pyqtSignal()
    
    # General error signal for non-task-specific issues
    general_error_signal = pyqtSignal(str)
    
    def __init__(self, parent=None, settings=None):
        """Initialize the AI manager."""
        super().__init__(parent)
        self.parent = parent # AIController instance
        self.settings_model = settings
        self.thread_pool = QThreadPool.globalInstance()
        self.gemini_configured = False # Flag to track if Gemini API has been configured

    def _get_ai_backend_config(self) -> dict:
        """Retrieve AI backend configurations from settings."""
        config = {}
        if not self.settings_model:
            error_msg = "Settings model not available in AIManager."
            logger.error(error_msg)
            self.general_error_signal.emit(error_msg) 
            # Return empty or default config to prevent crashes, error will be handled by calling functions
            return {
                "backend": "local", 
                "hf_api_key": "", 
                "google_api_key": "",
                "local_summarization_model_id": self.DEFAULT_LOCAL_SUMMARIZATION_MODEL,
                "hf_summarization_model_id": self.DEFAULT_HF_SUMMARIZATION_MODEL,
                "hf_text_generation_model_id": self.DEFAULT_HF_TEXT_GENERATION_MODEL,
                "gemini_summarization_model_id": self.DEFAULT_GEMINI_SUMMARIZATION_MODEL,
                "gemini_text_generation_model_id": self.DEFAULT_GEMINI_GENERATION_MODEL,
            }

        config["backend"] = self.settings_model.get("ai", "backend", "local")
        config["hf_api_key"] = os.environ.get("HUGGINGFACE_API_KEY") or self.settings_model.get("ai", "huggingface_api_key", "")
        config["google_api_key"] = os.environ.get("GOOGLE_API_KEY") or self.settings_model.get("ai", "google_api_key", "")
        
        config["local_summarization_model_id"] = self.settings_model.get("ai", "huggingface_summarization_model_id", self.DEFAULT_LOCAL_SUMMARIZATION_MODEL)
        config["hf_summarization_model_id"] = self.settings_model.get("ai", "huggingface_summarization_model_id", self.DEFAULT_HF_SUMMARIZATION_MODEL)
        config["hf_text_generation_model_id"] = self.settings_model.get("ai", "huggingface_text_generation_model_id", self.DEFAULT_HF_TEXT_GENERATION_MODEL)
        
        config["gemini_summarization_model_id"] = self.settings_model.get("ai", "google_gemini_summarization_model_id", self.DEFAULT_GEMINI_SUMMARIZATION_MODEL)
        config["gemini_text_generation_model_id"] = self.settings_model.get("ai", "google_gemini_text_generation_model_id", self.DEFAULT_GEMINI_GENERATION_MODEL)
        
        # Placeholder for Gemini specific generation_config and safety_settings if needed from settings
        # config["gemini_generation_config"] = self.settings_model.get_json("ai", "gemini_generation_config", None)
        # config["gemini_safety_settings"] = self.settings_model.get_json("ai", "gemini_safety_settings", None)

        if not config.get("backend"):
            logger.error("AIManager: Could not retrieve 'ai_backend' from settings.")
            # Emit a general error if the primary backend configuration is missing
            error_msg = "AI backend configuration missing or invalid in settings."
            self.general_error_signal.emit(error_msg)
            # Fallback to local if backend is not specified or invalid
            config['backend'] = 'local'
        
        logger.debug(f"AI Backend Config: {config['backend']}, HF Key Present: {bool(config['hf_api_key'])}, Google Key Present: {bool(config['google_api_key'])}")
        return config

    # --- Internal Signal Handlers --- 
    def _handle_worker_summarization_started(self):
        self.summarization_started_signal.emit()

    def _handle_worker_summarization_progress(self, progress_value):
        self.summarization_progress_signal.emit(progress_value)

    def _handle_worker_summarization_result(self, result_text):
        self.summarization_result_signal.emit(result_text)

    def _handle_worker_summarization_error(self, error_tuple):
        self.summarization_error_signal.emit(error_tuple)

    def _handle_worker_summarization_finished(self):
        self.summarization_finished_signal.emit()

    def _handle_worker_generation_started(self):
        self.text_generation_started_signal.emit()

    def _handle_worker_generation_progress(self, progress_value):
        self.text_generation_progress_signal.emit(progress_value)

    def _handle_worker_generation_result(self, result_text):
        self.text_generation_result_signal.emit(result_text)

    def _handle_worker_generation_error(self, error_tuple):
        self.text_generation_error_signal.emit(error_tuple)

    def _handle_worker_generation_finished(self):
        self.text_generation_finished_signal.emit()

    def _configure_gemini_if_needed(self, api_key: str, setup_error_handler) -> bool:
        """Configures the Google Gemini API if not already configured.

        Args:
            api_key: The Google Gemini API key.
            setup_error_handler: Callback function to handle errors during configuration.

        Returns:
            True if configuration is successful or already done, False otherwise.
        """
        if not self.gemini_configured:
            try:
                configure_gemini_api(api_key)
                self.gemini_configured = True
                logger.info("Google Gemini API configured successfully.")
                return True
            except Exception as e_conf:
                logger.error(f"Failed to configure Google Gemini API: {e_conf}")
                setup_error_handler((type(e_conf), f"Gemini API configuration failed: {e_conf}", traceback.format_exc()))
                return False
        return True # Already configured

    def _get_local_ai_worker(self, task_type: str, text_or_prompt: str, config: dict, setup_error_handler):
        """Gets a worker for local AI tasks (summarization).

        Args:
            task_type: The type of AI task ('summarization' or 'generation').
            text_or_prompt: The input text for summarization or prompt for generation.
            config: Dictionary containing backend configuration, including model IDs.
            setup_error_handler: Callback function to handle errors if worker creation fails.

        Returns:
            An instance of LocalSummarizationWorker or None if an error occurs or task is unsupported.
        """
        if task_type == "summarization":
            model_id = config.get("local_summarization_model_id", self.DEFAULT_LOCAL_SUMMARIZATION_MODEL)
            logger.info(f"Preparing local backend for summarization with model: {model_id}")
            return LocalSummarizationWorker(summarize_text_local, text_or_prompt, model_id=model_id)
        elif task_type == "generation":
            logger.warning("Local text generation is not currently supported by AIManager.")
            setup_error_handler((NotImplementedError, "Local text generation not supported.", traceback.format_exc()))
            return None
        logger.error(f"Unknown local task type: {task_type}")
        setup_error_handler((ValueError, f"Unknown local task type: {task_type}", traceback.format_exc()))
        return None

    def _get_huggingface_api_worker(self, task_type: str, text_or_prompt: str, config: dict, setup_error_handler, **kwargs):
        """Gets a worker for Hugging Face API tasks (summarization or generation).
        
        Args:
            task_type: The type of AI task ('summarization' or 'generation').
            text_or_prompt: The input text for summarization or prompt for generation.
            config: Dictionary containing backend configuration, including API key and model IDs.
            setup_error_handler: Callback function to handle errors if worker creation fails.
            **kwargs: Additional keyword arguments, e.g., 'max_new_tokens' for generation.

        Returns:
            An instance of ApiSummarizationWorker, ApiTextGenerationWorker, or None if an error occurs.
        """
        api_key = config.get("hf_api_key")
        if not api_key:
            msg = f"Hugging Face API key is missing for {task_type}."
            logger.error(msg)
            setup_error_handler((RuntimeError, msg, traceback.format_exc()))
            return None
        
        if task_type == "summarization":
            model_id = config.get("hf_summarization_model_id", self.DEFAULT_HF_SUMMARIZATION_MODEL)
            logger.info(f"Preparing Hugging Face API for summarization with model: {model_id}")
            return ApiSummarizationWorker(summarize_text_hf_api, text_or_prompt, api_key=api_key, model_id=model_id)
        elif task_type == "generation":
            model_id = config.get("hf_text_generation_model_id", self.DEFAULT_HF_TEXT_GENERATION_MODEL)
            max_new_tokens = kwargs.get("max_new_tokens", 150)
            logger.info(f"Preparing Hugging Face API for text generation with model: {model_id}")
            return ApiTextGenerationWorker(generate_text_hf_api, prompt_text=text_or_prompt, api_key=api_key, model_id=model_id, max_new_tokens=max_new_tokens)
        logger.error(f"Unknown Hugging Face API task type: {task_type}")
        setup_error_handler((ValueError, f"Unknown Hugging Face API task type: {task_type}", traceback.format_exc()))
        return None

    def _get_google_gemini_worker(self, task_type: str, text_or_prompt: str, config: dict, setup_error_handler, **kwargs): # Add **kwargs
        """Gets a worker for Google Gemini API tasks (summarization or generation).

        Args:
            task_type: The type of AI task ('summarization' or 'generation').
            text_or_prompt: The input text for summarization or prompt for generation.
            config: Dictionary containing backend configuration, including API key and model IDs.
            setup_error_handler: Callback function to handle errors if worker creation or API configuration fails.
            **kwargs: Additional keyword arguments, e.g., 'max_new_tokens' for generation.

        Returns:
            An instance of GeminiSummarizationWorker, GeminiTextGenerationWorker, or None if an error occurs.
        """
        api_key = config.get("google_api_key")
        if not api_key:
            msg = f"Google Gemini API key is missing for {task_type}."
            logger.error(msg)
            setup_error_handler((RuntimeError, msg, traceback.format_exc()))
            return None

        if not self._configure_gemini_if_needed(api_key, setup_error_handler):
            return None # Gemini configuration failed
        
        if task_type == "summarization":
            model_id = config.get("gemini_summarization_model_id", self.DEFAULT_GEMINI_SUMMARIZATION_MODEL)
            logger.info(f"Preparing Google Gemini API for summarization with model: {model_id}")
            return GeminiSummarizationWorker(summarize_text_gemini_api, text_or_prompt, api_key=api_key, model_id=model_id)
        elif task_type == "generation":
            model_id = config.get("gemini_text_generation_model_id", self.DEFAULT_GEMINI_GENERATION_MODEL)
            max_new_tokens_val = kwargs.get('max_new_tokens', 250) # Get max_new_tokens from kwargs
            logger.info(f"Preparing Google Gemini API for text generation with model: {model_id}")
            return GeminiTextGenerationWorker(
                generate_text_gemini_api,
                text_prompt=text_or_prompt, # Pass as text_prompt
                api_key=api_key,
                model_name=model_id,        # Pass model_id as model_name
                max_new_tokens=max_new_tokens_val # Pass as max_new_tokens
            )
        logger.error(f"Unknown Google Gemini task type: {task_type}")
        setup_error_handler((ValueError, f"Unknown Google Gemini task type: {task_type}", traceback.format_exc()))
        return None

    def _get_worker_for_task(self, task_type: str, backend: str, text_or_prompt: str, config: dict, setup_error_handler, **kwargs):
        """Instantiates and returns the appropriate worker for the given task and backend."""
        if backend == "local":
            return self._get_local_ai_worker(task_type, text_or_prompt, config, setup_error_handler)
        elif backend == "huggingface_api":
            return self._get_huggingface_api_worker(task_type, text_or_prompt, config, setup_error_handler, **kwargs)
        elif backend == "google_gemini":
            return self._get_google_gemini_worker(task_type, text_or_prompt, config, setup_error_handler, **kwargs) # Pass **kwargs
        else:
            logger.error(f"Unknown AI backend for {task_type}: {backend}")
            setup_error_handler((ValueError, f"Unknown AI backend: {backend}", traceback.format_exc()))
            return None

    def _create_and_dispatch_worker(self, task_type: str, text_or_prompt: str, config: dict, **kwargs):
        """Helper to create, configure, and run AI workers."""
        backend = config.get("backend", "local")

        # Determine signal handlers and error function based on task type
        if task_type == "summarization":
            signal_handlers = {
                "started": self._handle_worker_summarization_started,
                "progress": self._handle_worker_summarization_progress,
                "result": self._handle_worker_summarization_result,
                "error": self._handle_worker_summarization_error,
                "finished": self._handle_worker_summarization_finished,
            }
            setup_error_handler = self._handle_worker_summarization_error
        elif task_type == "generation":
            signal_handlers = {
                "started": self._handle_worker_generation_started,
                "progress": self._handle_worker_generation_progress,
                "result": self._handle_worker_generation_result,
                "error": self._handle_worker_generation_error,
                "finished": self._handle_worker_generation_finished,
            }
            setup_error_handler = self._handle_worker_generation_error
        else:
            logger.error(f"Unknown task type for worker dispatch: {task_type}")
            self.summarization_error_signal.emit((ValueError, f"Unknown task type: {task_type}", traceback.format_exc()))
            return

        try:
            worker = self._get_worker_for_task(task_type, backend, text_or_prompt, config, setup_error_handler, **kwargs)

            if worker:
                logger.info(f"Connecting signals for {backend} {task_type} worker.")
                worker.signals.started.connect(signal_handlers["started"])
                worker.signals.progress.connect(signal_handlers["progress"])
                worker.signals.result.connect(signal_handlers["result"])
                worker.signals.error.connect(signal_handlers["error"])
                worker.signals.finished.connect(signal_handlers["finished"])
                
                logger.info(f"Starting {backend} {task_type} worker in thread pool.")
                self.thread_pool.start(worker)
            else:
                # Error messages are handled within _get_worker_for_task or if backend is unknown by it
                if backend not in ["local", "huggingface_api", "google_gemini"]:
                     # This case should have been handled by _get_worker_for_task's final else.
                    # If it reaches here, it implies an unknown backend was passed and _get_worker_for_task returned None without specific error.
                    logger.error(f"Worker not initialized for task '{task_type}' with unknown backend '{backend}'. An error should have been emitted by _get_worker_for_task.")
                # else: worker is None due to specific error handled and emitted by _get_worker_for_task

        except Exception as e: # Catch-all for unexpected errors during dispatch setup
            msg = f"Unexpected error setting up {task_type} worker: {e}"
            logger.error(msg, exc_info=True)
            setup_error_handler((type(e), str(e), traceback.format_exc()))

    # --- Public Methods --- 
    def summarize_text(self, text: str):
        """
        Generate a summary of the given text based on the configured AI backend.
        """
        logger.info(f"AIManager.summarize_text called with text of length: {len(text)}")
        config = self._get_ai_backend_config()
        self._create_and_dispatch_worker("summarization", text, config)

    def generate_text(self, prompt_text: str, max_new_tokens: int = 2048):
        """
        Generate text based on a prompt using the configured AI backend.
        Renamed from generate_note_text for generality.
        """
        logger.info(f"AIManager.generate_text called with prompt: '{prompt_text[:50]}...' and max_new_tokens: {max_new_tokens}")
        config = self._get_ai_backend_config()
        self._create_and_dispatch_worker("generation", prompt_text, config, max_new_tokens=max_new_tokens)

    def request_entity_extraction(self, text: str):
        """Request entity extraction using the configured backend (currently SpaCy via EntityExtractionWorker)."""
        logger.info(f"AIManager: request_entity_extraction called for text (first 50 chars): {text[:50]}...")
        self.entity_extraction_started_signal.emit()

        # Entity extraction currently uses a local SpaCy model by default.
        # If it were to support multiple backends, backend selection logic would be needed here.
        model_id = self.settings_model.get(
            "ai", 
            "spacy_entity_model_id", 
            self.DEFAULT_ENTITY_EXTRACTION_MODEL
        )

        try:
            worker = EntityExtractionWorker(
                extract_entities_spacy, # The function to execute
                text=text,
                model_id=model_id
            )
            
            # Connect worker signals to AIManager's entity extraction signals
            # Note: EntityExtractionWorker's signals might be generic like `result`, `error`, `finished`.
            # We need to ensure they are connected to the specific entity_extraction_*_signal.
            # Assuming EntityExtractionWorker has standard WorkerSignals: started, progress, result, error, finished
            # No 'started' signal from worker needed here as we emit AIManager's started signal above.
            # No 'progress' signal typically for entity extraction via SpaCy in this setup.
            worker.signals.result.connect(self.entity_extraction_result_signal.emit)
            worker.signals.error.connect(self.entity_extraction_error_signal.emit)
            worker.signals.finished.connect(self.entity_extraction_finished_signal.emit)

            self.thread_pool.start(worker)
            logger.debug(f"AIManager: EntityExtractionWorker started for model {model_id}.")
        except Exception as e:
            error_tuple = (type(e), e, traceback.format_exc())
            logger.error(f"AIManager: Failed to create or start EntityExtractionWorker: {e}", exc_info=True)
            self.entity_extraction_error_signal.emit(error_tuple)
            self.entity_extraction_finished_signal.emit() # Ensure finished is emitted

    def extract_entities_with_spacy(self, text: str, model_id: str = 'en_core_web_sm', **kwargs):
        logger.debug(f"AIManager.extract_entities_with_spacy called with model: {model_id}")
        progress_callback = kwargs.get('progress_callback')
        try:
            return extract_entities_spacy(text, model_id, progress_callback=progress_callback)
        except Exception as e:
            logger.error(f"Error calling extract_entities_spacy from AIManager: {e}")
            # Ensure an empty list is returned on error to match expected type
            return []

    def perform_qna_on_text_and_entities(self, extracted_entities: list, web_content_collated: str):
        logger.info(f"AIManager.perform_qna_on_text_and_entities called. Entities count: {len(extracted_entities)}, Web content length: {len(web_content_collated)}")    

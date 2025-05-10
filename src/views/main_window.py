#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main window for the Smart Contextual Notes Editor.
Contains the UI definition and event handlers.
"""

import os
import logging
import traceback # Added import
from PyQt5.QtWidgets import (
    QMainWindow, QTextEdit, QAction, QMessageBox, 
    QStatusBar, QVBoxLayout, QWidget, QSplitter, 
    QApplication, QToolBar, QFileDialog, QDialog,
    QInputDialog, QDockWidget, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, QThreadPool
from PyQt5.QtGui import QTextCursor, QIcon

# Import models
from models.document_model import DocumentModel
from models.settings_model import SettingsModel

# Import controllers
from controllers.file_controller import FileController
from controllers.ai_controller import AIController
from controllers.web_controller import WebController
from controllers.context_controller import ContextController

# Import view managers
from managers.panel_manager import PanelManager
from managers.progress_manager import ProgressManager

# Import dialogs
from views.dialogs.auto_enhance_dialog import AutoEnhanceDialog
from views.dialogs.model_dialog import ModelSelectionDialog
from views.dialogs.ai_services_dialog import AIServicesDialog
from views.panels.summary_panel import SummaryPanel

# Import UI factory
from .ui_factory import (
    create_file_menu, create_edit_menu, create_ai_tools_menu,
    create_view_menu, create_web_menu, create_context_menu_actions,
    populate_toolbar
)

logger = logging.getLogger(__name__)

# UI String Constants (example - add more as needed)
EMPTY_NOTE_TITLE = "Empty Note"
NO_TEXT_TO_SUMMARIZE_MESSAGE = "There is no text to summarize."
NOTE_ENHANCEMENT_ERROR_TITLE = "Note Enhancement Error" # Moved/Ensured constant
ENHANCEMENT_SEQUENCE_ERROR_TITLE = "Note Enhancement Error" # New constant for sequence error
NO_SUGGESTIONS_DIALOG_TITLE = "No Suggestions"
NO_SUGGESTIONS_MESSAGE = "No enhancement suggestions were generated."
SUMMARY_ERROR_DIALOG_TITLE = "Summarization Error"
TEXT_GENERATION_ERROR_TITLE = "Text Generation Error"
SEARCHING_WEB_MESSAGE = "Searching the web for relevant information..."

class MainWindow(QMainWindow):
    """Main application window for the Smart Contextual Notes Editor."""
    APP_TITLE = "Smart Contextual Notes Editor"  # Class constant for the application title
    MSG_NOT_ENOUGH_TEXT = "Not Enough Text"
    MIN_WORDS_FOR_ENHANCEMENT = 5 # Minimum words in a note to trigger enhancement
    
    def __init__(self, settings=None):
        """Initialize the main window and set up the UI."""
        super().__init__()
        
        # Initialize models
        from utils.settings import Settings
        self.app_settings = settings if settings else Settings()
        self.document_model = DocumentModel()
        
        # Initialize controllers
        self.file_controller = FileController(self, self.app_settings, self.document_model)
        self.ai_controller = AIController(self, self.app_settings)
        self.web_controller = WebController(self)
        self.context_controller = ContextController(self)
        
        # Initialize view managers
        self.panel_manager = PanelManager(self)
        self.progress_manager = ProgressManager(self)
        
        # Initialize thread pool for background tasks
        self.thread_pool = QThreadPool()
        logger.info(f"Maximum thread count: {self.thread_pool.maxThreadCount()}")

        self._setup_summary_dock_widget()

        # Window properties
        self.setWindowTitle(self.APP_TITLE) # Use class constant
        
        # Set up the UI components
        self._setup_ui()
        
        # Connect all signals
        self._connect_signals()
        
        # Status message
        self.statusBar().setObjectName("MainStatusBar")
        self.statusBar().showMessage("Ready")
        self.progress_manager.setup_progress_bar(self.statusBar()) # Initialize progress bar

        self.settings_dialog = None
        self.ai_services_dialog = None
        self._enhancement_process_data = None # Initialize enhancement process data

    def _connect_signals(self):
        """Connect signals from various components to their respective slots."""
        # Example: self.some_button.clicked.connect(self.on_some_button_clicked)
        # --- File Controller Signals ---
        # self.file_controller.file_opened.connect(self._on_file_opened)
        # self.file_controller.file_saved.connect(self._on_file_saved)
        # self.file_controller.save_error.connect(self._on_save_error)
        # self.file_controller.unsaved_changes_status.connect(self.update_window_title_based_on_save_state)

        # --- AI Controller Signals ---
        # Summarization
        self.ai_controller.summarization_started.connect(self._on_summarization_started)
        self.ai_controller.summarization_progress.connect(self._on_summarization_progress)
        self.ai_controller.summarization_result.connect(self._on_summarization_result)
        self.ai_controller.summarization_error.connect(self._on_summarization_error)
        self.ai_controller.summarization_finished.connect(self._on_summarization_finished)

        # Text Generation
        self.ai_controller.text_generation_started.connect(self._on_text_generation_started)
        self.ai_controller.text_generation_progress.connect(self._on_text_generation_progress)
        self.ai_controller.text_generation_result.connect(self._on_text_generation_result)
        self.ai_controller.text_generation_error.connect(self._on_text_generation_error)
        self.ai_controller.text_generation_finished.connect(self._on_text_generation_finished)

        # Model Preloading
        self.ai_controller.model_preload_result.connect(self._on_model_preload_result)

        # Contextual Analysis & Enhancement Workflow
        self.ai_controller.entities_extracted.connect(self._on_entities_extracted) # Corrected slot
        self.ai_controller.entity_extraction_error.connect(self._on_note_enhancement_sequence_error)

        self.ai_controller.web_search_for_enhancement_result.connect(self._on_web_search_for_enhancement_result)
        self.ai_controller.web_search_for_enhancement_error.connect(self._on_note_enhancement_sequence_error)

        # Q&A on Web Content (Corrected signal and slot names)
        self.ai_controller.answer_extracted.connect(self._on_answer_extracted_for_enhancement) # Corrected signal and slot
        self.ai_controller.answer_extraction_error.connect(self._on_note_enhancement_sequence_error) # Corrected signal

        # Final Summary for Enhancement (Signals do not seem to exist in AIController, commenting out)
        # self.ai_controller.final_summary_for_enhancement_result.connect(self._on_final_summary_for_enhancement_result)
        # self.ai_controller.final_summary_for_enhancement_error.connect(self._on_note_enhancement_sequence_error)

        # --- Web Controller Signals ---
        self.web_controller.content_fetch_started.connect(self._on_content_fetch_started)
        self.web_controller.content_fetch_result.connect(self._on_content_fetch_result)
        self.web_controller.content_fetch_error.connect(self._on_content_fetch_error) # Ensure this slot exists

        # --- Text Edit Signals ---
        if hasattr(self, 'text_edit') and self.text_edit: # Ensure text_edit is initialized
            self.text_edit.textChanged.connect(self._on_text_changed)
            self.text_edit.cursorPositionChanged.connect(self._on_cursor_position_changed)

        # --- Other UI elements (e.g., from menus/toolbars if actions are dynamic) ---
        # Example: self.action_open.triggered.connect(self.file_controller.open_file)
        # Connections for actions created in ui_factory will be set there or here if actions are attributes of MainWindow

        logger.info("MainWindow signals connected.")

    #
    # AI Summarization Methods
    #
    
    def on_summarize_note(self):
        """Generate a summary of the current note using AI."""
        logger.info("Summarize note action triggered")
        
        # Get the text to summarize
        text = self.text_edit.toPlainText()
        logger.info(f"Text length for summarization: {len(text)} characters, {len(text.split())} words")
        
        # Check if there's enough text to summarize
        if not text or len(text.split()) < 50:
            logger.warning("Not enough text to summarize (less than 50 words)")
            QMessageBox.warning(
                self,
                self.MSG_NOT_ENOUGH_TEXT,
                "Please enter more text to generate a meaningful summary (at least 50 words)."
            )
            return
        
        try:
            # Use the AI controller to summarize the text
            logger.info("Calling ai_controller.summarize_text()")
            self.ai_controller.summarize_text(text)
            logger.info("ai_controller.summarize_text() call completed")
            
        except Exception as e:
            logger.error(f"Exception in on_summarize_note: {str(e)}")
            self.progress_manager.on_operation_error(str(e))
            QMessageBox.critical(
                self,
                SUMMARY_ERROR_DIALOG_TITLE,
                f"An error occurred while preparing for summarization: {str(e)}"
            )
    
    def on_select_model(self):
        """Open the model selection dialog."""
        try:
            # Get available models
            available_models = self.ai_controller.get_available_models()
            current_model = self.ai_controller.get_current_model()
            
            # Create and show the dialog
            dialog = ModelSelectionDialog(self, available_models, current_model)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                # Get the selected model
                selected_model = dialog.get_selected_model()
                if selected_model != self.ai_controller.get_current_model():
                    self.ai_controller.set_current_model(selected_model)
                    self.statusBar().showMessage(f"AI model set to: {selected_model}")
                    
                    # Preload the model in the background
                    self.statusBar().showMessage(f"Loading model {selected_model} in background...")
                    self.ai_controller.preload_model(selected_model)
        
        except ImportError as e:
            QMessageBox.critical(
                self,
                ERROR_DIALOG_TITLE,
                f"The required libraries for AI models are not installed: {str(e)}\n\n"
                "Please install them using: pip install transformers torch"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                ERROR_DIALOG_TITLE,
                f"An error occurred while selecting the model: {str(e)}"
            )
    
    def _on_model_preload_result(self, result, model_name):
        """Handle the model preload result signal."""
        if result:
            self.statusBar().showMessage(f"Model {model_name} loaded successfully")
        else:
            self.statusBar().showMessage(f"Failed to load model {model_name}")
            
            QMessageBox.critical(
                self,
                ERROR_DIALOG_TITLE,
                f"Failed to load model {model_name}. Please check the logs for details."
            )
    
    def insert_summary_at_cursor(self, summary):
        """Insert the summary at the current cursor position."""
        if not summary:
            logger.warning("Attempted to insert an empty summary.")
            QMessageBox.warning(self, "Empty Summary", "The generated summary is empty.")
            return
            
        cursor = self.text_edit.textCursor()
        # Add a bit of spacing if inserting into existing text
        if not cursor.atStart() and not cursor.atEnd():
            cursor.insertText("\n\n")
        cursor.insertText(f"## Summary\n\n{summary}\n\n")
        # QMessageBox.information(self, "Summary Inserted", "The summary has been inserted at the cursor.") # Removed to avoid double pop-up if panel is also used

    def on_search_web(self):
        """Search the web for information related to the current note."""
        # Get the text to search for
        text = self.text_edit.toPlainText()
        
        # Check if there's enough text to search
        if not text or len(text.split()) < 10:
            QMessageBox.warning(
                self,
                self.MSG_NOT_ENOUGH_TEXT,
                "Please enter more text to search for relevant information (at least 10 words)."
            )
            return
        
        # Generate a search query from the text
        query = self.web_controller.generate_search_query(text)
        
        # Perform the search
        self._perform_web_search(query)
    
    def on_search_selected(self):
        """Search the web for the selected text."""
        # Get the selected text
        cursor = self.text_edit.textCursor()
        selected_text = cursor.selectedText()
        
        # Check if there's any selected text
        if not selected_text:
            QMessageBox.warning(
                self,
                "No Text Selected",
                "Please select some text to search for."
            )
            return
        
        # Perform the search with the selected text as the query
        self._perform_web_search(selected_text)
    
    def _perform_web_search(self, query):
        """Perform a web search with the given query."""
        try:
            # Use the web controller to perform the search
            self.web_controller.perform_search(query)
            
        except ImportError as e:
            self.progress_manager.on_operation_error(str(e))
            QMessageBox.critical(
                self,
                ERROR_DIALOG_TITLE,
                f"The required libraries for web search are not installed: {str(e)}\n\n"
                "Please install them using: pip install requests beautifulsoup4"
            )
        except Exception as e:
            self.progress_manager.on_operation_error(str(e))
            QMessageBox.critical(
                self,
                ERROR_DIALOG_TITLE,
                f"An error occurred while preparing for web search: {str(e)}"
            )
    
    def _on_content_fetch_started(self, url: str):
        """Handle the content fetch started signal."""
        logger.info(f"Content fetch started for url: {url}") # Log the URL
        self.progress_manager.start_operation_with_message(f"Fetching content from: {url}...")
    
    def _on_content_fetch_result(self, result_data: dict):
        """Handle the content fetch result signal."""
        url = result_data.get('url')
        content = result_data.get('content')
        success = result_data.get('success', False)
        error_message = result_data.get('error')

        logger.debug(f"MainWindow: Content fetch result for {url}, Success: {success}")
        if success:
            self.statusBar().showMessage(f"Content fetched successfully from {url}", 3000)
            if hasattr(self, 'web_content_dialog') and self.web_content_dialog:
                self.web_content_dialog.set_content(url, content)
                if not self.web_content_dialog.isVisible():
                    self.web_content_dialog.show()
            else:
                logger.info(f"Web content dialog not available. Content from {url} not displayed directly.")
            if self._enhancement_process_data and \
               self._enhancement_process_data.get('current_step') == 'fetching_web_content_for_qna' and \
               url in self._enhancement_process_data.get('urls_to_fetch', []):
                logger.info(f"Content for {url} fetched for enhancement Q&A.")
        else:
            actual_error_message = error_message if error_message else "Unknown error during content fetch."
            self.statusBar().showMessage(f"Failed to fetch content from {url}: {actual_error_message}", 5000)
            QMessageBox.warning(self, "Web Content Error", f"Could not fetch content from {url}.\nError: {actual_error_message}")
            logger.error(f"Failed to fetch content from {url}: {actual_error_message}")

    def _on_content_fetch_error(self, error_data: dict):
        """Handle errors during web content fetching."""
        url = error_data.get('url', 'Unknown URL')
        error_message = error_data.get('error', 'Unknown error')

        logger.error(f"MainWindow: Content fetch error for {url}: {error_message}")
        self.statusBar().showMessage(f"Error fetching {url}: {error_message}", 5000)
        QMessageBox.critical(
            self,
            "Web Fetch Error",
            f"Failed to retrieve content from the URL: {url}\nReason: {error_message}"
        )
        if self._enhancement_process_data and \
           self._enhancement_process_data.get('current_step') == 'fetching_web_content_for_qna' and \
           url in self._enhancement_process_data.get('urls_to_fetch', []):
            logger.warning(f"Content fetch error for {url} during enhancement. AIController should handle its own error signal.")

    def _on_web_search_started(self):
        """Handle the web search started signal."""
        logger.info("Web search started.")
        self.progress_manager.start_operation_with_message("Searching the web...")
        # self.statusBar().showMessage("Searching the web...") # Covered by start_operation_with_message

    def fetch_web_content(self, url):
        """Fetch content from a URL."""
        try:
            # Use the web controller to fetch the content
            self.web_controller.fetch_content(url)
            
        except Exception as e:
            self.progress_manager.on_operation_error(str(e))
            QMessageBox.critical(
                self,
                ERROR_DIALOG_TITLE,
                f"An error occurred while preparing to fetch content: {str(e)}"
            )
    
    def insert_web_link(self, title, url):
        """Insert a link to a web page at the cursor position."""
        # Get the current cursor
        cursor = self.text_edit.textCursor()
        
        # Insert a newline if we're not at the beginning of a line
        if cursor.columnNumber() > 0:
            cursor.insertText("\n\n")
        
        # Insert the link in Markdown format
        cursor.insertText(f"[{title}]({url})\n")
        
        self.statusBar().showMessage("Link inserted at cursor position")
    
    #
    # Context Analysis Methods
    #
    
    def on_analyze_context(self):
        """Analyze the current note and web content to generate contextual suggestions."""
        # Get the current note text
        note_text = self.text_edit.toPlainText()
        
        if not note_text.strip():
            QMessageBox.warning(
                self,
                EMPTY_NOTE_TITLE,
                "Please enter some text in the note before analyzing context."
            )
            return
        
        # Check if we have web results
        web_results = self.web_controller.get_last_search_results()
        if not web_results:
            response = QMessageBox.question(
                self,
                "No Web Results",
                "No web search results found. Would you like to search the web first?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if response == QMessageBox.Yes:
                self.on_search_web()
                return
        
        # Analyze the context
        self.context_controller.analyze_context(note_text, web_results)
    
    def on_show_suggestions(self):
        """Show the suggestions panel with the latest suggestions."""
        # Get the current suggestions
        suggestions = self.context_controller.get_current_suggestions()
        
        if not suggestions:
            QMessageBox.information(
                self,
                "No Suggestions",
                "No contextual suggestions available. Please analyze the context first."
            )
            return
        
        # Show the suggestions panel
        self.panel_manager.show_suggestions_panel(suggestions)
    
    def insert_suggestion_text(self, text):
        """Insert suggestion text at the cursor position."""
        # Get the current cursor
        cursor = self.text_edit.textCursor()
        
        # Insert a newline if we're not at the beginning of a line
        if cursor.columnNumber() > 0:
            cursor.insertText("\n\n")
        
        # Insert the suggestion text
        cursor.insertText(text)
        
        self.statusBar().showMessage("Suggestion inserted at cursor position")
    
    def refresh_suggestions(self):
        """Refresh the contextual suggestions."""
        self.on_analyze_context()
    
    #
    # Auto-Enhancement Methods
    #
    
    def on_auto_enhance(self):
        """Open the auto-enhance dialog and start the enhancement process."""
        # Get the current note text
        note_text = self.text_edit.toPlainText()
        
        if not note_text.strip():
            QMessageBox.warning(
                self,
                EMPTY_NOTE_TITLE,
                "Please enter some text in the note before enhancing."
            )
            return
        
        # Create and show the auto-enhance dialog
        dialog = AutoEnhanceDialog(self)
        dialog.enhancement_requested.connect(self._start_auto_enhancement)
        dialog.exec_()
    
    def _start_auto_enhancement(self, options):
        """Start the auto-enhancement process with the given options."""
        # Get the current note text
        note_text = self.text_edit.toPlainText()
        
        # Get the dialog that sent the signal
        dialog = self.sender()
        
        # Update dialog status
        dialog.set_progress(10, "Analyzing note content...")
        
        # Step 1: Search the web if requested
        if options['search_web']:
            # Check if we already have search results
            web_results = self.web_controller.get_last_search_results()
            if not web_results or not web_results.get('links'): # Check if there are actual links
                # Generate a more intelligent search query using the AI-powered method
                logger.info("No existing web results or results are empty, generating new search query for enhancement.")
                query = self.web_controller.generate_search_query(note_text)
                logger.info(f"Generated search query for auto-enhancement: '{query[:30]}...'")
                
                dialog.set_progress(20, f"Searching the web for: '{query[:30]}...' ")
                
                # Connect a one-time handler for search results
                self.web_controller.web_search_result.connect(
                    lambda results: self._continue_enhancement_after_search(results, options, dialog)
                )
                
                # Start the search
                self.web_controller.perform_search(query)
            else:
                # Use existing search results
                self._continue_enhancement_after_search(
                    web_results, 
                    options, 
                    dialog
                )
        else:
            # Skip web search
            self._analyze_and_enhance([], options, dialog)
    
    def _continue_enhancement_after_search(self, search_results, options, dialog):
        """Continue the enhancement process after web search is complete."""
        # Disconnect the one-time handler
        try:
            self.web_controller.web_search_result.disconnect()
        except TypeError:
            # Signal was not connected
            pass
        
        dialog.set_progress(40, "Analyzing web content...")
        
        # Proceed with analysis and enhancement
        self._analyze_and_enhance(search_results, options, dialog)
    
    def _analyze_and_enhance(self, web_results, options, dialog):
        """Analyze the context and enhance the note."""
        # Get the current note text
        note_text = self.text_edit.toPlainText()
        
        dialog.set_progress(50, "Generating contextual suggestions...")
        
        # Connect a one-time handler for suggestions
        self.context_controller.suggestions_ready.connect(
            lambda suggestions: self._apply_enhancements(suggestions, options, dialog)
        )
        
        # Start the analysis
        self.context_controller.analyze_context(note_text, web_results)
    
    def _apply_enhancements(self, suggestions, options, dialog):
        """Apply the enhancements to the note."""
        # Disconnect the one-time handler
        try:
            self.context_controller.suggestions_ready.disconnect()
        except TypeError:
            # Signal was not connected
            pass
        
        dialog.set_progress(80, "Applying enhancements to your note...")
        
        # Get the content suggestions
        content_suggestions = suggestions.get('content_suggestions', [])
        missing_info = suggestions.get('missing_information', [])
        
        if not content_suggestions and not missing_info:
            dialog.enhancement_failed("No relevant suggestions found.")
            return
        
        # Generate the enhancement text
        enhancement_text = self._generate_enhancement_text(content_suggestions, missing_info, options)
        
        # Insert the enhancement text
        self._insert_enhancement_text(enhancement_text, options)
        
        # Mark the document as having unsaved changes
        self.document_model.set_content(self.text_edit.toPlainText())
        
        # Complete the enhancement process
        dialog.set_progress(100, "Enhancement complete!")
        dialog.enhancement_complete()
        
        # Show a status message
        self.statusBar().showMessage("Notes enhanced with AI-generated content")
    
    def _generate_enhancement_text(self, content_suggestions, missing_info, options):
        """Generate the enhancement text from suggestions."""
        # Prepare the text to insert
        enhancement_text = "\n\n" + "="*50 + "\n"  # Separator
        enhancement_text += "AI-ENHANCED CONTENT\n\n"
        
        # Add content suggestions
        if content_suggestions:
            enhancement_text += self._format_content_suggestions(content_suggestions, options)
        
        # Add missing information suggestions
        if missing_info:
            enhancement_text += self._format_missing_info(missing_info)
        
        return enhancement_text
    
    def _format_content_suggestions(self, content_suggestions, options):
        """Format the content suggestions into text."""
        result = ""
        
        # Sort by overall score
        content_suggestions.sort(key=lambda x: x.get('overall_score', 0), reverse=True)
        
        # Take the top N suggestions based on user preference
        top_suggestions = content_suggestions[:options['num_suggestions']]
        
        for suggestion in top_suggestions:
            result += self._format_single_suggestion(suggestion)
        
        return result
    
    def _format_single_suggestion(self, suggestion):
        """Format a single suggestion into text."""
        result = ""
        title = suggestion.get('title', 'Untitled')
        url = suggestion.get('url', '')
        sentences = suggestion.get('sentences', [])
        
        result += f"## {title}\n"
        if url:
            result += f"Source: {url}\n\n"
        
        if sentences:
            # Sort by similarity
            sentences.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            
            # Add the sentences
            for sentence_data in sentences:
                sentence = sentence_data.get('sentence', '')
                if sentence:
                    result += f"- {sentence}\n"
            
            result += "\n"
        
        return result
    
    def _format_missing_info(self, missing_info):
        """Format the missing information into text."""
        result = "## Suggested Additions\n"
        for info in missing_info:
            result += f"- {info}\n"
        result += "\n"
        
        return result
    
    def _insert_enhancement_text(self, enhancement_text, options):
        """Insert the enhancement text into the document based on the selected style."""
        cursor = self.text_edit.textCursor()
        
        if options['insertion_style'] == 0:  # Append to end
            cursor.movePosition(QTextCursor.End)
            cursor.insertText(enhancement_text)
        
        elif options['insertion_style'] == 1:  # Insert at cursor
            cursor.insertText(enhancement_text)
        
        elif options['insertion_style'] == 2:  # Create new section
            cursor.movePosition(QTextCursor.End)
            cursor.insertText("\n\n## Related Information\n")
            cursor.insertText(enhancement_text)
    
    def configure_ai_services(self):
        """Configure AI services dialog."""
        logger.info("Configure AI Services action triggered.")
        dialog = AIServicesDialog(self.app_settings, self)
        if dialog.exec_() == QDialog.Accepted:
            # Settings are saved within the dialog's accept() method
            logger.info("AI Services configured and saved.")

    def closeEvent(self, event):
        """Handle the window close event."""
        if self.file_controller._check_unsaved_changes():
            # Save window state before closing
            self.app_settings.set("window", "width", self.width())
            self.app_settings.set("window", "height", self.height())
            self.app_settings.set("window", "x", self.x())
            self.app_settings.set("window", "y", self.y())
            self.app_settings.save_settings()
            
            event.accept()
        else:
            event.ignore()

    def on_generate_note_text(self):
        """Generate new note content based on a prompt using AI."""
        prompt_text, ok = QInputDialog.getText(self, "Generate Note Content", 
                                               "Enter your prompt for the AI:")
        
        if ok and prompt_text:
            logger.info(f"User provided prompt for text generation: '{prompt_text[:50]}...' ") 
            # Call the AI controller's method to generate text.
            try:
                self.ai_controller.request_text_generation(prompt_text, max_new_tokens=250)
                self.statusBar().showMessage("AI is generating text...") 
            except Exception as e:
                logger.error(f"Error triggering text generation: {e}")
                QMessageBox.critical(self, TEXT_GENERATION_ERROR_TITLE, f"Could not start text generation: {e}")
        else:
            logger.info("Text generation cancelled by user or empty prompt.")

    # --- Placeholder AI Text Generation Signal Handlers ---
    def _on_text_generation_started(self):
        """Handle the start of AI text generation."""
        logger.info("AI Text Generation Started.")
        self.progress_manager.start_operation_with_message("Generating text...")
        # self.statusBar().showMessage("AI is generating text...") # Covered by start_operation_with_message

    def _on_text_generation_progress(self, percentage: int):
        """Handle AI text generation progress updates."""
        pass # Text generation APIs usually don't provide granular progress like summarization models

    def _on_text_generation_result(self, generated_text_result):
        """Handle the successful result of AI text generation."""
        if not generated_text_result: # Should ideally be handled by error signal if empty is error
            logger.warning("AI text generation returned an empty result.")
            self.progress_manager.on_operation_error("AI returned empty text.")
            QMessageBox.warning(self, "AI Result Empty", "The AI returned an empty result. No changes were made.")
            return

        # Ensure generated_text_result is a string
        if not isinstance(generated_text_result, str):
            try:
                # If it's a more complex object (e.g. from Gemini API response), try to extract text part
                # This is a guess; adapt if AI result structure is different
                if hasattr(generated_text_result, 'text'):
                    generated_text = generated_text_result.text
                elif isinstance(generated_text_result, dict) and 'text' in generated_text_result:
                    generated_text = generated_text_result['text']
                else:
                    # Fallback if structure is unknown, convert to string
                    generated_text = str(generated_text_result)
                    logger.warning(f"AI result was not a string, converted to: {generated_text[:100]}...")
            except Exception as e:
                logger.error(f"Error processing AI result structure: {e}")
                self.progress_manager.on_operation_error(f"Error processing AI result: {e}")
                QMessageBox.critical(self, "AI Result Error", f"Could not process the AI result: {e}")
                return
        else:
            generated_text = generated_text_result

        logger.info(f"AI Text Generation Successful. Received {len(generated_text)} characters.")
        self.progress_manager.on_progress_update(95) # Set progress to 95%
        self.progress_manager.show_message("AI text processing complete.") # Show message

        current_text = self.text_edit.toPlainText()
        new_text = current_text + "\n\n--- Enhanced Content ---\n" + generated_text
        self.text_edit.setPlainText(new_text)
        self.file_modified = True
        self.update_title()
        
        self.progress_manager.on_progress_update(100) # Set progress to 100%
        self.statusBar().showMessage("Note enhanced successfully!", 5000)
        logger.info("Note enhanced and UI updated.")

    def _on_text_generation_error(self, error_details):
        err_type, err_msg, _ = error_details
        logger.error(f"AI Text Generation Error: {err_type}: {err_msg}")
        self.progress_manager.hide_progress()
        self.statusBar().showMessage("Text generation failed.", 5000)
        QMessageBox.critical(self, TEXT_GENERATION_ERROR_TITLE, f"{err_type}: {err_msg}")

    def _on_text_generation_finished(self):
        """Handle the end of AI text generation (success or failure)."""
        logger.info("AI Text Generation Finished.")
        self.progress_manager.hide_progress() # Ensure progress is hidden
        # Status message is usually set by result or error handlers

    # --- End Placeholder AI Text Generation Signal Handlers ---

    # --- AI Summarization Signal Handlers ---
    def _on_summarization_started(self):
        """Handle the start of AI text summarization."""
        logger.info("AI Summarization Started.")
        self.progress_manager.start_operation_with_message("Summarizing text...")
        # self.statusBar().showMessage("AI is summarizing text...") # Covered by start_operation_with_message

    def _on_summarization_progress(self, percentage: int):
        """Handle AI text summarization progress updates."""
        pass # API-based summarization might not offer granular progress

    def _on_summarization_result(self, summary_text: str):
        """Handle the result of AI text summarization."""
        logger.info(f"AI Summarization Result received (first 100 chars): {summary_text[:100]}...")
        self.progress_manager.hide_progress()
        
        if not summary_text.strip():
            self.statusBar().showMessage("Summarization complete: Empty summary.", 5000)
            QMessageBox.information(self, "Summarization Complete", "The generated summary is empty or contains only whitespace.")
            return

        self.statusBar().showMessage("Summarization complete.", 5000)
        if self.summary_panel_view:
            self.summary_panel_view.set_summary(summary_text)
        
        if self.summary_dock_widget:
            self.summary_dock_widget.setVisible(True)
            self.summary_dock_widget.raise_()

    def _on_summarization_error(self, error_details: tuple):
        error_type, error_message, tb_str = error_details
        logger.error(f"MainWindow Summarization Error: {error_type.__name__} - {error_message}")
        if tb_str:
            logger.debug(f"Traceback:\n{tb_str}")

        if hasattr(self, 'progress_manager'): # Check if progress_manager exists
            self.progress_manager.hide_progress()
        self.statusBar().showMessage("Summarization failed.", 5000)

        QMessageBox.critical(self, SUMMARY_ERROR_DIALOG_TITLE, 
                             f"{error_message}\n\nType: {error_type.__name__}")

    def _on_summarization_finished(self):
        """Handle the end of AI text summarization (success or failure)."""
        logger.info("AI Summarization Finished.")
        self.progress_manager.hide_progress() # Ensure progress is hidden
        # Status message is usually set by result or error handlers
    # --- End AI Summarization Signal Handlers ---

    # --- New SummaryPanel Integration Methods ---
    def _setup_summary_dock_widget(self):
        """Sets up the QDockWidget that will host the SummaryPanel."""
        self.summary_dock_widget = QDockWidget("Summary", self)
        self.summary_dock_widget.setObjectName("MainSummaryDockWidget")
        self.summary_panel_view = SummaryPanel(parent=self)
        self.summary_dock_widget.setWidget(self.summary_panel_view)
        self.addDockWidget(Qt.RightDockWidgetArea, self.summary_dock_widget)
        self.summary_dock_widget.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable)
        self.summary_dock_widget.setVisible(False)

    def insert_summary_at_top(self, summary: str):
        """Insert the provided summary at the top of the document."""
        if not summary:
            return
        cursor = self.text_edit.textCursor()
        # Add a bit of spacing if inserting into existing text
        if not cursor.atStart() and not cursor.atEnd():
             prefix = f"## Summary\n\n{summary}\n\n"
        else:
            prefix = f"## Summary\n\n{summary}\n"
            
        cursor.insertText(prefix)
        self.statusBar().showMessage("Summary inserted at the top.", 3000)

    def insert_summary_at_cursor(self, summary: str):
        """Insert the provided summary at the cursor position."""
        if not summary:
            return
        cursor = self.text_edit.textCursor()
        # Add a bit of spacing if inserting into existing text
        if not cursor.atStart() and not cursor.atEnd():
            cursor.insertText("\n\n")
        cursor.insertText(f"## Summary\n\n{summary}\n\n")
        # QMessageBox.information(self, "Summary Inserted", "The summary has been inserted at the cursor.") # Removed to avoid double pop-up if panel is also used

    def insert_summary_at_bottom(self, summary: str):
        """Insert the provided summary at the bottom of the document."""
        if not summary:
            return
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        suffix = ""
        if self.text_edit.toPlainText() and not self.text_edit.toPlainText().endswith( ("\n", "\r") ):
            suffix = f"\n\n## Summary\n\n{summary}\n"
        else:
            suffix = f"## Summary\n\n{summary}\n"

        cursor.insertText(suffix)
        self.statusBar().showMessage("Summary inserted at the bottom.", 3000)

    def close_summary_panel(self):
        """Close (hide) the summary dock widget."""
        if self.summary_dock_widget:
            self.summary_dock_widget.setVisible(False)

    def _on_summary_dock_visibility_changed(self, visible: bool):
        """Handle summary_dock_widget visibility changes."""
        if not visible:
            if self.summary_panel_view:
                self.summary_panel_view.clear_summary()
            logger.debug("MainSummaryDockWidget hidden, summary cleared from SummaryPanel.")

    # --- Entity Extraction Signal Handlers ---
    def _on_entity_extraction_started(self):
        """Handle the start of entity extraction."""
        logger.info("Entity Extraction Started.")
        self.progress_manager.start_operation_with_message("Extracting entities...")

    def _on_entities_extracted(self, entities):
        """Handle the result of entity extraction."""
        logger.info(f"Entities Extracted: {entities}")
        self.progress_manager.on_progress_update(20)
        self.progress_manager.show_message("Entities extracted. Preparing web search...")
        
        if not self._enhancement_process_data or self._enhancement_process_data.get('current_step') != 'entity_extraction':
            logger.error("Received entities but enhancement process not in correct state or not active.")
            self.progress_manager.hide_progress()
            self._enhancement_process_data = None # Reset
            return

        self._enhancement_process_data['entities'] = entities

        if not entities:
            self.statusBar().showMessage("No key entities found. Skipping web search.", 5000)
            logger.info("No entities found. Proceeding to next step (e.g., summarization of original note or finish).")
            # For now, let's assume we try to summarize the original note if no entities found.
            # This would involve calling a summarization step. Or, just finish.
            # Let's make a placeholder call to the ai_controller for summarizing the original text as the next step.
            # Or, directly trigger the final summary part. Let's simplify and assume if no entities, we are done with this path for now.
            self._on_note_enhancement_sequence_finished() # Placeholder, actual next step depends on design
            return

        # AIController will select top N entities from the 'entities' list.
        # We still store all extracted entities in _enhancement_process_data['entities'] for potential later use.
        
        self._enhancement_process_data['current_step'] = 'ai_managed_entity_web_search'
        self.statusBar().showMessage(f"Found {len(entities)} entities. Handing over to AI for web search...", 5000)
        self.progress_manager.on_progress_update(30)
        self.progress_manager.show_message("AI is preparing web searches for entities...")

        try:
            self.ai_controller.search_web_for_entities(
                self._enhancement_process_data['original_note_text'],
                self._enhancement_process_data['entities']
            )
        except Exception as e:
            logger.error(f"Error calling ai_controller.search_web_for_entities: {e}")
            self._on_note_enhancement_sequence_error(("Web Search Initiation Error", str(e)))

    def _on_entity_extraction_error(self, error_details):
        """Handle errors during entity extraction."""
        err_type, err_msg, _ = error_details
        logger.error(f"Entity Extraction Error: {err_type}: {err_msg}")
        self.progress_manager.hide_progress()
        self.statusBar().showMessage("Entity extraction failed.", 5000)
        QMessageBox.critical(self, ERROR_DIALOG_TITLE, f"{err_type}: {err_msg}")
        self._enhancement_process_data = None # Reset on error

    # --- Web Search for Enhancement Signal Handlers ---
    def _on_web_search_for_enhancement_started(self):
        """Handle the start of web search for enhancement."""
        logger.info("Web Search for Enhancement Started.")
        self.progress_manager.start_operation_with_message(SEARCHING_WEB_MESSAGE)

    def _on_web_search_for_enhancement_result(self, aggregated_search_data):
        """
        Handles results from AIController.request_web_search_for_enhancement.
        NOTE: In the simplified direct AI enhancement flow initiated by enhance_current_note_with_ai,
        this method's role is primarily to log if web search was somehow still performed.
        The actual AI call for enhancement is made directly in enhance_current_note_with_ai.
        """
        logger.info(f"_on_web_search_for_enhancement_result called. Aggregated search data present: {bool(aggregated_search_data)}")

        if not aggregated_search_data:
            logger.info("Web search yielded no results or was intentionally bypassed for direct AI enhancement.")
            # The main AI call is in enhance_current_note_with_ai.
            # Update progress if this slot is part of an old flow that set web search progress.
            if self.progress_manager.progress_bar and self.progress_manager.progress_bar.isVisible():
                 self.progress_manager.update_progress(70, "Web search complete (no results/bypassed).")
            self.update_status_bar("Web search bypassed or no results; direct AI enhancement is primary.")
        else:
            # This case is unexpected if enhance_current_note_with_ai is the sole entry for enhancement.
            logger.warning("Web search results were received, but the current enhancement flow "
                           "bypasses their integration into the AI prompt.")
            if self.progress_manager.progress_bar and self.progress_manager.progress_bar.isVisible():
                self.progress_manager.update_progress(70, "Web search results obtained (currently not used)." )
            self.update_status_bar("Web search results received but currently not used for AI enhancement.")

        # IMPORTANT: Do NOT initiate a new AI text generation call from here to avoid conflicts
        # with the direct call in enhance_current_note_with_ai.
        # That function is now solely responsible for initiating the enhancement AI call.
        # The text_generation_result signal (connected to _on_text_generation_result)
        # will handle hiding the progress dialog when the AI operation completes.

    def _on_web_search_for_enhancement_error(self, error_details):
        """Handle errors during AI-managed web search for enhancement."""
        err_type, err_msg, _ = error_details
        logger.error(f"Web Search for Enhancement Error: {err_type}: {err_msg}")
        self.progress_manager.hide_progress()
        self.statusBar().showMessage("Web search failed.", 5000)
        QMessageBox.critical(
            self,
            ERROR_DIALOG_TITLE,
            f"{err_type}: {err_msg}")

    # --- Answer Extraction Signal Handlers ---
    def _on_answer_extraction_started(self):
        """Handle the start of answer extraction."""
        logger.info("Answer Extraction Started.")
        self.progress_manager.show_message("Extracting answers from web content...")

    def _on_answer_extracted_for_enhancement(self, qna_results: dict):
        """Handles extracted answers (Q&A results) for the enhancement process."""
        logger.info(f"Answers extracted for enhancement: {len(qna_results) if isinstance(qna_results, (dict, list)) else 'Invalid type'} items.")
        if not qna_results:
            logger.info("No Q&A results to process.")
            return

        processed_items = []
        if isinstance(qna_results, dict):
            processed_items = list(qna_results.values())
        elif isinstance(qna_results, list):
            processed_items = qna_results
        else:
            logger.warning(f"Unexpected type for qna_results: {type(qna_results)}. Expected dict or list.")

        for item in processed_items:
            if isinstance(item, dict) and 'answer' in item and 'source_url' in item:
                self._collected_enhancements.append({
                    'type': 'qna',
                    'answer': item.get('answer'),
                    'source_url': item.get('source_url'),
                    'query': item.get('query', '')
                })
            else:
                logger.warning(f"Skipping malformed Q&A result item: {item}")
        
        self.progress_manager.show_message(f"{len(self._collected_enhancements)} enhancement items collected so far.")
        # AIController manages sequence flow.

    def _on_answer_extraction_error(self, error_details):
        err_type, err_msg, _ = error_details
        logger.error(f"Answer Extraction Error for enhancement: {err_type}: {err_msg}")
        self.progress_manager.on_operation_error(f"Failed to extract answers: {err_msg}")
        QMessageBox.critical(self, ERROR_DIALOG_TITLE, f"Could not extract answers from web content: {err_type}: {err_msg}")
        self._collected_enhancements_error_flag = True
        # AIController manages sequence flow / error propagation.

    def _on_answer_extraction_finished(self):
        logger.info("Answer extraction phase finished.")
        self.progress_manager.on_operation_finished("Answer extraction complete.")
        # This slot handles the completion of the Q&A part of the enhancement.
        # The AIController will likely take the _collected_enhancements and proceed to summarize them.

        # If there was an error during Q&A, _collected_enhancements_error_flag would be true.
        # The AIController should also be aware of this state, possibly through an error signal
        # or by checking the results it receives.

        if self._enhancement_process_data and self._enhancement_process_data.get('current_step') == 'qna_on_web_content_processing': # or similar
            if self._collected_enhancements_error_flag:
                logger.warning("Skipping final summarization due to errors in Q&A phase.")
                # self._on_note_enhancement_sequence_error could be triggered by AIController if needed
                # or handle completion with error state here.
                self._on_note_enhancement_sequence_finished(success=False) # Indicate error
                return
            
            self._enhancement_process_data['current_step'] = 'final_summary_generation'
            self.progress_manager.on_progress_update(80)
            self.progress_manager.show_message("Generating final enhanced summary...")
            try:
                self.ai_controller.summarize_enhancement_context(
                    self._enhancement_process_data['original_note_text'],
                    self._collected_enhancements # This now contains Q&A items
                )
            except Exception as e:
                logger.error(f"Error calling ai_controller.summarize_enhancement_context: {e}")
                self._on_note_enhancement_sequence_error(("Final Summarization Initiation Error", str(e), traceback.format_exc()))
        else:
            logger.debug("_on_answer_extraction_finished called, but process not in expected state.")

    def _on_final_summary_for_enhancement_result(self, summary_text: str):
        """Handle the final summary result for the enhancement workflow."""
        logger.info(f"MainWindow: Received final summary for enhancement: {summary_text[:100]}...")
        if self._enhancement_process_data and self._enhancement_process_data.get('current_step') == 'final_summary_generation':
            self._enhancement_process_data['final_summary_enhancement'] = summary_text
            # Update UI or show the summary
            self._display_enhanced_content(summary_text)
            self._on_note_enhancement_sequence_finished()
        else:
            logger.warning("Received final summary but enhancement process not in correct state.")

    # --- Overall Enhancement Sequence Completion --- 
    def _on_note_enhancement_sequence_finished(self, success: bool = True):
        logger.info(f"Full Note Enhancement Sequence Concluded. Success: {success}")
        
        if self._collected_enhancements:
            logger.info(f"Displaying {len(self._collected_enhancements)} enhancement suggestions.")
            self._display_enhancement_suggestions(self._collected_enhancements)
        elif success and not self._collected_enhancements_error_flag:
            logger.info("Enhancement sequence finished successfully but no enhancements were generated.")
            QMessageBox.information(self, NO_SUGGESTIONS_DIALOG_TITLE, NO_SUGGESTIONS_MESSAGE)
        elif self._collected_enhancements_error_flag:
            logger.warning("Enhancement sequence finished, but errors occurred and no suggestions were generated.")
            # Specific error messages should have been shown by individual handlers.
            # Optionally, show a generic message if no specifics were shown but flag is true.
        else: # Not success, no specific errors flagged, no enhancements
            logger.info("Enhancement sequence did not produce suggestions or encountered an issue without specific errors.")
            QMessageBox.information(self, NOTE_ENHANCEMENT_ERROR_TITLE, "Note enhancement process completed but did not yield suggestions or encountered an unspecified issue.")
        
        self.progress_manager.on_operation_finished("Note enhancement process complete.")
        self.statusBar().showMessage("Note enhancement process finished.", 5000)
        
        # Reset state for next enhancement operation
        self._current_enhancement_context = None
        self._collected_enhancements = [] 
        self._collected_enhancements_error_flag = False

    def _on_note_enhancement_sequence_error(self, error_details: tuple):
        # Assuming error_details is a tuple e.g. (type, message, traceback)
        # The actual structure depends on what AIController.note_enhancement_sequence_error emits.
        if isinstance(error_details, tuple) and len(error_details) >= 2:
            err_type, err_msg = error_details[0], error_details[1]
            logger.error(f"Note enhancement sequence error: {err_type}: {err_msg}")
            self.progress_manager.on_operation_error(f"Enhancement failed: {err_msg}")
            self.statusBar().showMessage(f"Note enhancement failed: {err_msg}", 5000)
            QMessageBox.critical(
                self,
                ENHANCEMENT_SEQUENCE_ERROR_TITLE,
                f"The note enhancement process failed: {err_type}: {err_msg}")
        else: # Fallback if error_details is just a string or unexpected format
            error_message_str = str(error_details)
            logger.error(f"Note enhancement sequence error (unexpected format): {error_message_str}")
            self.progress_manager.on_operation_error(f"Enhancement failed: {error_message_str}")
            self.statusBar().showMessage(f"Note enhancement failed: {error_message_str}", 5000)
            QMessageBox.critical(
                self,
                ENHANCEMENT_SEQUENCE_ERROR_TITLE,
                f"The note enhancement process failed: {error_message_str}")

        # Reset enhancement data if an error occurs mid-sequence
        self._enhancement_process_data = None
        self._collected_enhancements = []
        self._collected_enhancements_error_flag = False
        self.progress_manager.hide_progress() # Ensure progress bar is hidden on error

    def on_trigger_full_enhancement_pipeline(self):
        """
        Starts the full note enhancement pipeline:
        1. Extracts entities from the current note.
        2. (Handled by AIController/MainWindow signals) Triggers web search based on entities.
        3. (Handled by AIController/MainWindow signals) Fetches content from search results.
        4. (Handled by AIController/MainWindow signals) Performs Q&A or Summarization on content.
        5. (Handled by AIController/MainWindow signals) Displays suggestions.
        """
        logger.info("Full note enhancement pipeline triggered.")
        
        note_text = self.text_edit.toPlainText()
        
        if not note_text or len(note_text.split()) < self.MIN_WORDS_FOR_ENHANCEMENT:
            logger.warning(f"Not enough text to enhance (less than {self.MIN_WORDS_FOR_ENHANCEMENT} words).")
            QMessageBox.warning(
                self,
                self.MSG_NOT_ENOUGH_TEXT,
                f"Please provide at least {self.MIN_WORDS_FOR_ENHANCEMENT} words in your note to start the enhancement process."
            )
            return
            
        # Call the method that sets up the enhancement data and starts the first step
        self.on_start_note_enhancement_workflow() 

    def on_start_note_enhancement_workflow(self):
        """Initiates the multi-step note enhancement workflow by setting up data and starting entity extraction."""
        note_text = self.text_edit.toPlainText() # Already checked in on_trigger_full_enhancement_pipeline, but good for direct calls
        if not note_text.strip(): # Basic check if called directly
            QMessageBox.warning(self, EMPTY_NOTE_TITLE, "Please enter some text before starting the enhancement workflow.")
            return

        word_count = len(note_text.split()) # Also checked, but good for direct calls
        if word_count < self.MIN_WORDS_FOR_ENHANCEMENT:
            QMessageBox.warning(self, self.MSG_NOT_ENOUGH_TEXT, 
                                f"Please provide at least {self.MIN_WORDS_FOR_ENHANCEMENT} words for enhancement (current: {word_count}).")
            return

        logger.info("Starting note enhancement workflow.")
        self.progress_manager.start_operation_with_message("Starting enhancement: Extracting entities...")

        self._enhancement_process_data = {
            'current_step': 'entity_extraction',
            'original_note_text': note_text,
            'entities': None,
            'web_search_results': None, # To store collated results from WebController/AIController
            'qna_results': None, # To store results from Q&A on web content
            'final_summary': None # For a final summary of enhanced content if applicable
        }
        self._collected_enhancements = [] # Initialize list for suggestions
        self._collected_enhancements_error_flag = False

        try:
            logger.info("Calling ai_controller.extract_entities() to start enhancement.")
            self.ai_controller.extract_entities(note_text)
            # Status bar will be updated by _on_entity_extraction_started which is connected to ai_controller.entity_extraction_started
        except Exception as e:
            logger.error(f"Exception when trying to start entity extraction in enhancement workflow: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                NOTE_ENHANCEMENT_ERROR_TITLE,
                f"An unexpected error occurred while starting entity extraction: {e}"
            )
            self.statusBar().showMessage("Error starting note enhancement.", 5000)
            self._enhancement_process_data = None # Clear data on error
            self.progress_manager.hide_progress()

    def _display_enhancement_suggestions(self, suggestions: list):
        """Display the enhancement suggestions in a dialog."""
        if not suggestions:
            logger.info("No enhancement suggestions to display.")
            QMessageBox.information(self, NO_SUGGESTIONS_DIALOG_TITLE, NO_SUGGESTIONS_MESSAGE)
            return

        logger.info(f"Displaying {len(suggestions)} enhancement suggestions.")
        dialog = EnhancementSuggestionsDialog(suggestions, self)
        dialog.suggestion_accepted.connect(self._insert_enhancement_suggestion)
        dialog.exec_()

    def _insert_enhancement_suggestion(self, suggestion_text: str):
        """Inserts the accepted enhancement suggestion into the text editor."""
        if not suggestion_text:
            logger.warning("Attempted to insert an empty enhancement suggestion.")
            return
        
        cursor = self.text_edit.textCursor()
        # Add some spacing if not at the start of a line or if there's preceding text on the line
        if not cursor.atBlockStart():
            cursor.insertBlock() # Start a new paragraph for the suggestion
        
        # Could format it further, e.g., add a header or quote block
        cursor.insertText(suggestion_text)
        cursor.insertBlock() # Add a new line after insertion

        self.statusBar().showMessage("Enhancement suggestion inserted.", 3000)
        self._on_text_changed() # Ensure document state is updated

    def update_window_title_based_on_save_state(self):
        """Updates the window title based on the current file and save state."""
        base_title = "Smart Notes Editor"
        current_file = self.document_model.get_current_file()
        unsaved_changes = self.document_model.has_unsaved_changes()

        if current_file:
            file_name = os.path.basename(current_file)
            title = f"{'*' if unsaved_changes else ''}{file_name} - {base_title}"
        else:
            title = f"{'*' if unsaved_changes else ''}Untitled - {base_title}"
        self.setWindowTitle(title)

    def update_title(self):
        """Update the window title based on the current file and unsaved changes."""
        base_app_title = self.APP_TITLE # Use class constant
        if self.document_model.current_file:
            file_name = os.path.basename(self.document_model.current_file)
        else:
            file_name = "Untitled" # Or use self.EMPTY_NOTE_TITLE if preferred
        
        modified_indicator = "*" if self.document_model.unsaved_changes else ""
        
        self.setWindowTitle(f"{file_name}{modified_indicator} - {base_app_title}")
        logger.debug(f"Window title updated to: {file_name}{modified_indicator} - {base_app_title}")

    def _setup_ui(self):
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Text Editor
        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("MainTextEdit")
        layout.addWidget(self.text_edit)
        
        # Menu Bar
        menubar = self.menuBar()
        menubar.setObjectName("MainMenuBar")
        create_file_menu(self, menubar)
        create_edit_menu(self, menubar)
        create_ai_tools_menu(self, menubar)
        create_view_menu(self, menubar)
        create_web_menu(self, menubar)
        # Context menu actions are usually set up on the widget itself (e.g., text_edit)
        # create_context_menu_actions(self) # Assuming this is for the text_edit

        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setObjectName("MainToolBar")
        self.addToolBar(toolbar)
        populate_toolbar(self, toolbar)

        # Status Bar (already created by QMainWindow by default)
        self.statusBar().setObjectName("MainStatusBar")

    def _on_text_changed(self):
        """Handle the textChanged signal from the text editor."""
        # This method is called whenever the text in the editor changes.
        # logger.debug("Text changed") # Can be too verbose
        self.document_model.set_content(self.text_edit.toPlainText()) # Correct way to mark as dirty via DocumentModel
        self._update_status_bar_word_count()
        # Potentially update UI elements, e.g., enable save action
        if hasattr(self, 'action_save') and self.action_save:
             self.action_save.setEnabled(self.document_model.unsaved_changes) # Corrected from has_unsaved_changes()
        self.update_title() # Update window title to reflect potential unsaved changes
        # Auto-save logic could be triggered here after a delay

    def _on_cursor_position_changed(self):
        """Handle the cursorPositionChanged signal from the text editor."""
        # This method is called whenever the cursor position changes.
        # logger.debug("Cursor position changed") # Can be too verbose
        # Update status bar with current line/column, or other contextual info
        cursor = self.text_edit.textCursor()
        line_num = cursor.blockNumber() + 1
        col_num = cursor.columnNumber() + 1
        self.statusBar().showMessage(f"Line: {line_num}, Col: {col_num}", 1000) # Temporary message
        self._update_contextual_actions() # e.g. based on selection

    def _update_status_bar_word_count(self):
        """Update the word count in the status bar."""
        pass

    def _update_contextual_actions(self):
        """Placeholder: Update contextual actions based on editor state (e.g., selection)."""
        logger.debug("Updating contextual actions (placeholder).")
        # Example logic (to be expanded):
        # has_selection = self.text_edit.textCursor().hasSelection()
        # self.action_cut.setEnabled(has_selection)
        # self.action_copy.setEnabled(has_selection)
        # self.action_search_selected.setEnabled(has_selection)

    def enhance_current_note_with_ai(self):
        """Enhances the current note using AI directly for text generation."""
        current_note_text = self.text_edit.toPlainText()
        if not current_note_text.strip():
            self.update_status_bar("Cannot enhance an empty note.")
            QMessageBox.information(self, "Empty Note", "The note is empty. Please add some text to enhance.")
            return

        self.progress_manager.start_operation_with_message("Enhancing Note...")

        logger.info("Proceeding directly to AI text generation for note enhancement.")
        enhancement_prompt = (
            f"Please enhance the following text by adding relevant information, insights, and details. "
            f"If you have access to web information, please use it and cite your sources. "
            f"Original text:\n\n{current_note_text}"
        )
        
        try:
            # Directly request text generation for enhancement
            self.ai_controller.request_text_generation(prompt_text=enhancement_prompt)
            # Adjusted progress: 50% after sending request, actual generation will take more.
            self.progress_manager.on_progress_update(50)
            self.progress_manager.show_message("Requesting AI to enhance note...")
            self.update_status_bar("Sent request to AI for note enhancement...")
        except Exception as e:
            logger.error(f"Error requesting AI text generation for enhancement: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "AI Enhancement Error",
                f"Could not start AI enhancement: {e}"
            )
            self.progress_manager.on_operation_error(f"Failed to enhance note: {e}")
            self.update_status_bar("AI enhancement request failed.")

    def update_status_bar(self, message):
        """Update the status bar with a message."""
        self.statusBar().showMessage(message, 5000)

    def _display_enhanced_content(self, enhanced_text):
        """Display the enhanced content."""
        # Insert the enhanced text into the document
        self.text_edit.setPlainText(enhanced_text)
        self.statusBar().showMessage("Enhanced content inserted into the document.")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main window for the Smart Contextual Notes Editor.
Contains the UI definition and event handlers.
"""

import os
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QTextEdit, QAction, QMessageBox, 
    QStatusBar, QVBoxLayout, QWidget, QSplitter, 
    QApplication, QToolBar, QFileDialog
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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window for the Smart Contextual Notes Editor."""
    
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
        
        # Window properties
        self.setWindowTitle("Smart Contextual Notes Editor")
        
        # Set up the UI components
        self._setup_ui()
        
        # Connect all signals
        self._connect_signals()
        
        # Status message
        self.statusBar.showMessage("Ready")
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Create a splitter for the main editor and potential side panels
        self.splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(self.splitter)
        
        # Text editor
        self.text_edit = QTextEdit()
        self.splitter.addWidget(self.text_edit)
        
        # Connect text changed signal to track unsaved changes
        self.text_edit.textChanged.connect(self._on_text_changed)
        
        # Enable context menu for the text editor
        self.text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_edit.customContextMenuRequested.connect(self._show_context_menu)
        
        # Set up menus and toolbar
        self._setup_menus()
        self._setup_toolbar()
        
        # Status bar with progress bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.progress_manager.setup_progress_bar(self.statusBar)
        
        # Restore window state
        self._restore_window_state()
    
    def _restore_window_state(self):
        """Restore the window state from settings."""
        width = self.app_settings.get("window", "width", 800)
        height = self.app_settings.get("window", "height", 600)
        x = self.app_settings.get("window", "x", 100)
        y = self.app_settings.get("window", "y", 100)
        
        self.resize(width, height)
        self.move(x, y)
    
    def _setup_menus(self):
        """Set up the application menus."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        
        # New action
        new_action = QAction("&New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.setStatusTip("Create a new note")
        new_action.triggered.connect(self.file_controller.new_note)
        file_menu.addAction(new_action)
        
        # Open action
        open_action = QAction("&Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open an existing note")
        open_action.triggered.connect(self.file_controller.open_note)
        file_menu.addAction(open_action)
        
        # Save action
        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save the current note")
        save_action.triggered.connect(self.file_controller.save_note)
        file_menu.addAction(save_action)
        
        # Save As action
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.setStatusTip("Save the current note with a new name")
        save_as_action.triggered.connect(self.file_controller.save_note_as)
        file_menu.addAction(save_as_action)
        
        # Separator
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = self.menuBar().addMenu("&Edit")
        
        # Undo action
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.setStatusTip("Undo the last action")
        undo_action.triggered.connect(self.text_edit.undo)
        edit_menu.addAction(undo_action)
        
        # Redo action
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.setStatusTip("Redo the last undone action")
        redo_action.triggered.connect(self.text_edit.redo)
        edit_menu.addAction(redo_action)
        
        # Separator
        edit_menu.addSeparator()
        
        # Cut action
        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.setStatusTip("Cut the selected text")
        cut_action.triggered.connect(self.text_edit.cut)
        edit_menu.addAction(cut_action)
        
        # Copy action
        copy_action = QAction("&Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.setStatusTip("Copy the selected text")
        copy_action.triggered.connect(self.text_edit.copy)
        edit_menu.addAction(copy_action)
        
        # Paste action
        paste_action = QAction("&Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.setStatusTip("Paste the clipboard text")
        paste_action.triggered.connect(self.text_edit.paste)
        edit_menu.addAction(paste_action)
        
        # AI menu
        ai_menu = self.menuBar().addMenu("&AI")
        
        # Summarize action
        summarize_action = QAction("&Summarize Note", self)
        summarize_action.setShortcut("Ctrl+Alt+S")
        summarize_action.setStatusTip("Generate a summary of the current note using AI")
        summarize_action.triggered.connect(self.on_summarize_note)
        ai_menu.addAction(summarize_action)
        
        # Select Model action
        select_model_action = QAction("Select &Model...", self)
        select_model_action.setStatusTip("Select AI model for summarization")
        select_model_action.triggered.connect(self.on_select_model)
        ai_menu.addAction(select_model_action)
        
        # Web menu
        web_menu = self.menuBar().addMenu("&Web")
        
        # Search Web action
        search_web_action = QAction("&Search Web", self)
        search_web_action.setShortcut("Ctrl+Alt+W")
        search_web_action.setStatusTip("Search the web for information related to your note")
        search_web_action.triggered.connect(self.on_search_web)
        web_menu.addAction(search_web_action)
        
        # Search Selected Text action
        search_selected_action = QAction("Search &Selected Text", self)
        search_selected_action.setShortcut("Ctrl+Alt+F")
        search_selected_action.setStatusTip("Search the web for the selected text")
        search_selected_action.triggered.connect(self.on_search_selected)
        web_menu.addAction(search_selected_action)
        
        # Context menu
        context_menu = self.menuBar().addMenu("&Context")
        
        # Analyze context action
        analyze_context_action = QAction("&Analyze Context", self)
        analyze_context_action.setStatusTip("Analyze note and web content to generate contextual suggestions")
        analyze_context_action.triggered.connect(self.on_analyze_context)
        context_menu.addAction(analyze_context_action)
        
        # Show suggestions action
        show_suggestions_action = QAction("Show &Suggestions", self)
        show_suggestions_action.setStatusTip("Show contextual suggestions based on previous analysis")
        show_suggestions_action.triggered.connect(self.on_show_suggestions)
        context_menu.addAction(show_suggestions_action)
        
        # Auto-enhance action
        context_menu.addSeparator()
        auto_enhance_action = QAction("Auto-&Enhance Notes", self)
        auto_enhance_action.setStatusTip("Automatically enhance notes with AI-generated content")
        auto_enhance_action.triggered.connect(self.on_auto_enhance)
        context_menu.addAction(auto_enhance_action)
    
    def _setup_toolbar(self):
        """Set up the application toolbar."""
        # Create toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)
        
        # Add actions to toolbar
        # New action
        new_action = QAction("New", self)
        new_action.setStatusTip("Create a new note")
        new_action.triggered.connect(self.file_controller.new_note)
        self.toolbar.addAction(new_action)
        
        # Open action
        open_action = QAction("Open", self)
        open_action.setStatusTip("Open an existing note")
        open_action.triggered.connect(self.file_controller.open_note)
        self.toolbar.addAction(open_action)
        
        # Save action
        save_action = QAction("Save", self)
        save_action.setStatusTip("Save the current note")
        save_action.triggered.connect(self.file_controller.save_note)
        self.toolbar.addAction(save_action)
        
        # Add separator
        self.toolbar.addSeparator()
        
        # Summarize action
        summarize_action = QAction("Summarize", self)
        summarize_action.setStatusTip("Summarize the current note using AI")
        summarize_action.triggered.connect(self.on_summarize_note)
        self.toolbar.addAction(summarize_action)
        
        # Web search action
        search_action = QAction("Web Search", self)
        search_action.setStatusTip("Search the web for information related to the note")
        search_action.triggered.connect(self.on_search_web)
        self.toolbar.addAction(search_action)
        
        # Add separator
        self.toolbar.addSeparator()
        
        # Auto-enhance action
        enhance_action = QAction("Enhance Notes", self)
        enhance_action.setStatusTip("Automatically enhance notes with AI-generated content")
        enhance_action.triggered.connect(self.on_auto_enhance)
        self.toolbar.addAction(enhance_action)
    
    def _connect_signals(self):
        """Connect all signals to their handlers."""
        # AI controller signals
        self.ai_controller.summarization_started.connect(self.progress_manager.on_operation_started)
        self.ai_controller.summarization_progress.connect(self.progress_manager.on_progress_update)
        self.ai_controller.summarization_result.connect(self.panel_manager.show_summary_panel)
        self.ai_controller.summarization_error.connect(self.progress_manager.on_operation_error)
        self.ai_controller.summarization_finished.connect(self.progress_manager.on_operation_finished)
        
        self.ai_controller.model_preload_result.connect(self._on_model_preload_result)
        self.ai_controller.model_preload_error.connect(self.progress_manager.on_operation_error)
        
        # Web controller signals
        self.web_controller.web_search_started.connect(self.progress_manager.on_operation_started)
        self.web_controller.web_search_progress.connect(self.progress_manager.on_progress_update)
        self.web_controller.web_search_result.connect(self.panel_manager.show_web_results_panel)
        self.web_controller.web_search_error.connect(self.progress_manager.on_operation_error)
        self.web_controller.web_search_finished.connect(self.progress_manager.on_operation_finished)
        
        self.web_controller.content_fetch_started.connect(self._on_content_fetch_started)
        self.web_controller.content_fetch_progress.connect(self.progress_manager.on_progress_update)
        self.web_controller.content_fetch_result.connect(self._on_content_fetch_result)
        self.web_controller.content_fetch_error.connect(self.progress_manager.on_operation_error)
        self.web_controller.content_fetch_finished.connect(self.progress_manager.on_operation_finished)
        
        # Context controller signals
        self.context_controller.context_analysis_started.connect(self.progress_manager.on_operation_started)
        self.context_controller.context_analysis_progress.connect(self.progress_manager.on_progress_update)
        self.context_controller.suggestions_ready.connect(self.panel_manager.show_suggestions_panel)
        self.context_controller.context_analysis_error.connect(self.progress_manager.on_operation_error)
        self.context_controller.context_analysis_finished.connect(self.progress_manager.on_operation_finished)
    
    def _show_context_menu(self, position):
        """Show a context menu for the text editor."""
        menu = self.text_edit.createStandardContextMenu()
        
        # Add custom actions if text is selected
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            # Add separator
            menu.addSeparator()
            
            # Add web search action
            search_action = QAction("Search Web for Selected Text", self)
            search_action.triggered.connect(self.on_search_selected)
            menu.addAction(search_action)
        
        # Show the menu at the cursor position
        menu.exec_(self.text_edit.mapToGlobal(position))
    
    def _on_text_changed(self):
        """Handle text changed event."""
        # Update document model
        self.document_model.set_content(self.text_edit.toPlainText())
        
        # Update window title
        if self.document_model.get_current_file():
            self.setWindowTitle(f"*{os.path.basename(self.document_model.get_current_file())} - Smart Contextual Notes Editor")
        else:
            self.setWindowTitle("*Untitled - Smart Contextual Notes Editor")
    
    #
    # AI Summarization Methods
    #
    
    def on_summarize_note(self):
        """Generate a summary of the current note using AI."""
        # Get the text to summarize
        text = self.text_edit.toPlainText()
        
        # Check if there's enough text to summarize
        if not text or len(text.split()) < 50:
            QMessageBox.warning(
                self,
                "Not Enough Text",
                "Please enter more text to generate a meaningful summary (at least 50 words)."
            )
            return
        
        try:
            # Use the AI controller to summarize the text
            self.ai_controller.summarize_text(text)
            
        except Exception as e:
            self.progress_manager.on_operation_error(str(e))
            QMessageBox.critical(
                self,
                "Summarization Error",
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
            
            if result == QApplication.DialogCode.Accepted:
                # Get the selected model
                selected_model = dialog.get_selected_model()
                if selected_model != self.ai_controller.get_current_model():
                    self.ai_controller.set_current_model(selected_model)
                    self.statusBar.showMessage(f"AI model set to: {selected_model}")
                    
                    # Preload the model in the background
                    self.statusBar.showMessage(f"Loading model {selected_model} in background...")
                    self.ai_controller.preload_model(selected_model)
        
        except ImportError as e:
            QMessageBox.critical(
                self,
                "Missing Dependencies",
                f"The required libraries for AI models are not installed: {str(e)}\n\n"
                "Please install them using: pip install transformers torch"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while selecting the model: {str(e)}"
            )
    
    def _on_model_preload_result(self, result, model_name):
        """Handle the model preload result signal."""
        if result:
            self.statusBar.showMessage(f"Model {model_name} loaded successfully")
        else:
            self.statusBar.showMessage(f"Failed to load model {model_name}")
            
            QMessageBox.critical(
                self,
                "Model Loading Error",
                f"Failed to load model {model_name}. Please check the logs for details."
            )
    
    def insert_summary_at_cursor(self, summary):
        """Insert the summary at the current cursor position."""
        # Get the current cursor
        cursor = self.text_edit.textCursor()
        
        # Insert a newline if we're not at the beginning of a line
        if cursor.columnNumber() > 0:
            cursor.insertText("\n\n")
        
        # Insert the summary with a header
        cursor.insertText("## Summary\n\n")
        cursor.insertText(summary)
        cursor.insertText("\n\n")
        
        self.statusBar.showMessage("Summary inserted at cursor position")
    
    #
    # Web Search Methods
    #
    
    def on_search_web(self):
        """Search the web for information related to the current note."""
        # Get the text to search for
        text = self.text_edit.toPlainText()
        
        # Check if there's enough text to search
        if not text or len(text.split()) < 10:
            QMessageBox.warning(
                self,
                "Not Enough Text",
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
                "Missing Dependencies",
                f"The required libraries for web search are not installed: {str(e)}\n\n"
                "Please install them using: pip install requests beautifulsoup4"
            )
        except Exception as e:
            self.progress_manager.on_operation_error(str(e))
            QMessageBox.critical(
                self,
                "Web Search Error",
                f"An error occurred while preparing for web search: {str(e)}"
            )
    
    def _on_content_fetch_started(self, url):
        """Handle the content fetch started signal."""
        self.statusBar.showMessage(f"Fetching content from: {url}...")
    
    def _on_content_fetch_result(self, result):
        """Handle the content fetch result signal."""
        self.statusBar.showMessage("Content fetched successfully")
        
        # Display the content in the web panel
        if hasattr(self.panel_manager, 'web_panel') and self.panel_manager.web_panel:
            self.panel_manager.web_panel.display_content(result)
    
    def fetch_web_content(self, url):
        """Fetch content from a URL."""
        try:
            # Use the web controller to fetch the content
            self.web_controller.fetch_content(url)
            
        except Exception as e:
            self.progress_manager.on_operation_error(str(e))
            QMessageBox.critical(
                self,
                "Content Fetch Error",
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
        
        self.statusBar.showMessage("Link inserted at cursor position")
    
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
                "Empty Note",
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
        
        self.statusBar.showMessage("Suggestion inserted at cursor position")
    
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
                "Empty Note",
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
            if not web_results:
                # Extract keywords from the note for the search query
                # This is a simple implementation - could be improved with better keyword extraction
                words = note_text.split()
                query = " ".join(words[:10])  # Use first 10 words as a simple query
                
                dialog.set_progress(20, "Searching the web for relevant information...")
                
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
        self.statusBar.showMessage("Notes enhanced with AI-generated content")
    
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

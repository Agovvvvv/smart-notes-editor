#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main window for the Smart Contextual Notes Editor.
Contains the UI definition and event handlers.
"""

import os
import logging
import traceback 
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QTextEdit, QAction,
    QFileDialog, QSplitter, QTreeWidget, QTreeWidgetItem, QInputDialog, # Changed QTreeView, QFileSystemModel to QTreeWidget, QTreeWidgetItem
    QStatusBar, QLabel, QMessageBox, QToolBar, QAbstractItemView
)
from PyQt5.QtCore import Qt, QThreadPool, QDir, QModelIndex
from PyQt5.QtGui import QTextCursor, QIcon
from typing import Optional, Tuple

# Import settings first if it's a base config
from utils.settings import Settings # Added: Import Settings

# Import models
from models.document_model import DocumentModel

# Import controllers
from controllers.file_controller import FileController
from controllers.ai_controller import AIController
from controllers.context_controller import ContextController

# Import view managers
from managers.panel_manager import PanelManager
from managers.progress_manager import ProgressManager
from managers.enhancement_state_manager import EnhancementStateManager 
from managers.dialog_manager import DialogManager
from managers.workspace_manager import WorkspaceManager
from managers.explorer_panel_manager import ExplorerPanelManager 
from managers.ai_feature_manager import AIFeatureManager

# Import dialogs
from views.dialogs.ai_services_dialog import AIServicesDialog
from views.dialogs.enhancement_preview_dialog import EnhancementPreviewDialog 
from views.dialogs.template_manager_dialog import TemplateManagerDialog
from views.panels.summary_panel import SummaryPanel
from views.dialogs.workspace_manager_dialog import WorkspaceManagerDialog
from views.widgets.workspace_welcome_widget import WorkspaceWelcomeWidget

# Import handlers
from handlers.ai_signal_handlers import AISignalHandler

# Import UI factory
from .ui_factory import (
    create_file_menu, create_edit_menu, create_ai_tools_menu,
    create_view_menu, create_context_menu_actions,
    populate_toolbar
)

from backend.ai_utils import estimate_tokens 

logger = logging.getLogger(__name__)

AI_FEATURES_UNAVAILABLE_ERROR = "Cannot insert summary: AI features are not available."

# UI String Constants (example - add more as needed)
EMPTY_NOTE_TITLE = "Empty Note" 
NO_TEXT_TO_SUMMARIZE_MESSAGE = "There is no text to summarize."
NOTE_ENHANCEMENT_ERROR_TITLE = "Note Enhancement Error" 
ENHANCEMENT_SEQUENCE_ERROR_TITLE = "Note Enhancement Error" 
NO_SUGGESTIONS_DIALOG_TITLE = "No Suggestions"
NO_SUGGESTIONS_MESSAGE = "No enhancement suggestions were generated."
SUMMARY_ERROR_DIALOG_TITLE = "Summarization Error"
TEXT_GENERATION_ERROR_TITLE = "Text Generation Error"
NOTE_ENHANCEMENT_TITLE = "Enhance Note" 

# File Operation Dialog Titles
DELETE_CONFIRM_TITLE = "Confirm Delete"
DELETE_FAILED_TITLE = "Delete Failed"
DELETE_SUCCESSFUL_TITLE = "Delete Successful"
INVALID_NAME_TITLE = "Invalid Name"
RENAME_ERROR_TITLE = "Rename Error"
RENAME_FAILED_TITLE = "Rename Failed"
RENAME_SUCCESSFUL_TITLE = "Rename Successful"
MSG_ENHANCEMENT_ACCEPTED = "Enhancement accepted by user."
MSG_APPLYING_TO_SELECTION = "Applying enhancement to selection."
MSG_APPLYING_TO_FULL_NOTE = "Applying enhancement to full note."
MSG_ENHANCED_SUCCESSFULLY = "Note enhanced successfully!"

class MainWindow(QMainWindow):
    """Main application window for the Smart Contextual Notes Editor."""
    APP_TITLE = "Smart Contextual Notes Editor"  
    MSG_NOT_ENOUGH_TEXT = "Not Enough Text"
    MIN_WORDS_FOR_ENHANCEMENT = 5 
    
    def __init__(self, settings=None):
        """Initialize the main window and set up the UI."""
        super().__init__()
        
        # Initialize models
        self.settings = settings if settings else Settings()
        self.workspace_manager = WorkspaceManager(self.settings) # Add this line
        self.document_model = DocumentModel()
        
        # Initialize controllers
        self.file_controller = FileController(self, self.settings, self.document_model)
        self.ai_controller = AIController(self, self.settings)
        self.ai_feature_manager = AIFeatureManager(self, self.ai_controller, self.settings)
        self.context_controller = ContextController(self)
        self._current_file_explorer_root_path: Optional[str] = None # Added for file explorer context menu
        
        # Initialize view managers
        self.panel_manager = PanelManager(self)
        self.progress_manager = ProgressManager(self)
        self.enhancement_state_manager = EnhancementStateManager(self) 
        self.dialog_manager = DialogManager(self)

        # Initialize thread pool for background tasks
        self.thread_pool = QThreadPool()
        logger.info(f"Maximum thread count: {self.thread_pool.maxThreadCount()}")

        # Initialize Summary Panel components
        self.summary_dock_widget, self.summary_panel_view = self.panel_manager.create_summary_dock_widget()
        self.addDockWidget(Qt.RightDockWidgetArea, self.summary_dock_widget)
        # Note: Signal connections for summary_panel_view previously in _setup_summary_dock_widget
        # are now expected to be handled by direct calls from SummaryPanel to parent (MainWindow) methods.

        # Initialize File Explorer Panel
        # This creates the dock widget and tree widget instances
        self.file_explorer_dock_widget, self.file_tree_widget = self.panel_manager.create_file_explorer_dock_widget() # Adjusted for new return
        # self.file_system_model is no longer used with QTreeWidget
        
        self.file_explorer_toggle_action = self.file_explorer_dock_widget.toggleViewAction()
        self.file_explorer_toggle_action.setText("File Explorer Panel") # Or "Toggle Sidebar", "Workspace Panel", etc.
        self.file_explorer_toggle_action.setStatusTip("Show or hide the File Explorer panel")
        
        # Create a container widget for the dock's content (to switch between welcome and tree)
        self.file_explorer_container = QWidget()
        self.file_explorer_container_layout = QVBoxLayout(self.file_explorer_container)
        self.file_explorer_container_layout.setContentsMargins(0,0,0,0)
        self.file_explorer_dock_widget.setWidget(self.file_explorer_container) # Set container as dock's widget

        # Create and setup WorkspaceWelcomeWidget
        self.workspace_welcome_widget = WorkspaceWelcomeWidget(self) # main_window is parent for UI
        self.file_explorer_container_layout.addWidget(self.workspace_welcome_widget)
        
        # Add file_tree_widget to layout but ensure it's hidden initially
        self.file_explorer_container_layout.addWidget(self.file_tree_widget) # Renamed

        # Initialize ExplorerPanelManager (AFTER all relevant UI components are created)
        self.explorer_panel_manager = ExplorerPanelManager(
            main_window=self,
            workspace_manager=self.workspace_manager,
            dialog_manager=self.dialog_manager,
            file_tree_widget=self.file_tree_widget,
            workspace_welcome_widget=self.workspace_welcome_widget,
            file_explorer_dock_widget=self.file_explorer_dock_widget,
            file_controller=self.file_controller,
            status_bar=self.statusBar()
        )

        # Initial update of the explorer panel view (shows welcome or tree based on active workspace)
        self.explorer_panel_manager._update_explorer_panel_view() # Call through the manager
        
        # Set initial root path for file explorer - This logic is now handled by _update_file_explorer_root
        # default_notes_dir = self.settings.get('General', 'default_notes_directory', QDir.homePath())
        
        self.addDockWidget(Qt.LeftDockWidgetArea, self.file_explorer_dock_widget) # REINSTATE THIS LINE
        
        # Window properties
        self.setWindowTitle(self.APP_TITLE) 
        
        # Set up the UI components
        self._setup_ui()

        # AIFeatureManager is now initialized before _setup_ui()

        # AISignalHandler is being replaced by AIFeatureManager which connects its own signals
        # self.AISignalHandler = AISignalHandler(self) # Removed
    
        # Connect all signals
        self._connect_signals()
        
        # Status message
        self.statusBar().setObjectName("MainStatusBar")
        self.statusBar().showMessage("Ready")
        self.progress_manager.setup_progress_bar(self.statusBar()) 

        # Word count label for status bar
        self.word_count_label = QLabel("Words: 0")
        self.word_count_label.setObjectName("WordCountLabel")
        self.statusBar().addPermanentWidget(self.word_count_label)

        self.settings_dialog = None
        self.ai_services_dialog = None
        # Removed obsolete state flags: _pending_enhancement_data, _selection_based_enhancement_info

        self.update_title()

    def _connect_signals(self):
        """Connect signals from various components to their respective slots."""
        # Example: self.some_button.clicked.connect(self.on_some_button_clicked)
        # --- File Controller Signals ---
        # self.file_controller.file_opened.connect(self._on_file_opened)
        # self.file_controller.file_saved.connect(self._on_file_saved)
        # self.file_controller.save_error.connect(self._on_save_error)
        # self.file_controller.unsaved_changes_status.connect(self.update_window_title_based_on_save_state)

        # AI related signals from AIController are now connected internally by AIFeatureManager.

        # --- Text Edit Signals ---
        if hasattr(self, 'text_edit') and self.text_edit: 
            self.text_edit.textChanged.connect(self._on_text_changed)
            self.text_edit.cursorPositionChanged.connect(self._on_cursor_position_changed)

        # File Explorer connections (now handled by ExplorerPanelManager)
        if self.file_tree_widget:
            self.file_tree_widget.itemActivated.connect(self.explorer_panel_manager.on_sidebar_file_activated)
            self.file_tree_widget.customContextMenuRequested.connect(self.explorer_panel_manager.on_file_explorer_context_menu)
            # Drag and drop for QTreeWidget might need specific handling later.
            # QAbstractItemView.InternalMove is for model-based views.
            # For QTreeWidget, if drag/drop reordering is needed, custom event handling is typical.
            # Setting to NoDragDrop as a placeholder until custom D&D is implemented.
            self.file_tree_widget.setDragDropMode(QAbstractItemView.NoDragDrop)
            self.file_tree_widget.setDragEnabled(True)
            self.file_tree_widget.setAcceptDrops(True)
            self.file_tree_widget.setDropIndicatorShown(True)

        # --- Other UI elements (e.g., from menus/toolbars if actions are dynamic) ---
        # Example: self.some_button.clicked.connect(self.on_some_button_clicked)
        # Connections for actions created in ui_factory will be set there or here if actions are attributes of MainWindow


        logger.info("MainWindow signals connected.")


     # --- UI Setup and Helper Methods ---
    def _setup_ui(self):
        """Set up the main UI components.
        """
        logger.debug("Setting up UI")
        # --- Central Widget --- 
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralContentArea")
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)
        
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
        # create_web_menu(self, menubar) 
        create_context_menu_actions()
        
        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setObjectName("MainToolBar")
        self.addToolBar(toolbar)
        populate_toolbar(self, toolbar)

        # Status Bar (already created by QMainWindow by default)
        self.statusBar().setObjectName("MainStatusBar")

    # Removed obsolete _handle_enhancement_result method

    # General text generation results and errors are now handled by AIFeatureManager

    def on_trigger_full_enhancement_pipeline(self):
        """
        Starts the full note enhancement pipeline:
        1. Extracts entities from the current note.
        2. Proceeds to generate enhancement using original text and entities, but no web content.
        """
        logger.info("Full note enhancement pipeline triggered.")
        
        note_text = self.text_edit.toPlainText()
        
        if not note_text or len(note_text.split()) < self.MIN_WORDS_FOR_ENHANCEMENT:
            logger.warning(f"Not enough text to enhance (less than {self.MIN_WORDS_FOR_ENHANCEMENT} words).")
            self.dialog_manager.show_warning(
                self.MSG_NOT_ENOUGH_TEXT,
                f"Please provide at least {self.MIN_WORDS_FOR_ENHANCEMENT} words in your note to start the enhancement process."
            )
            return
            
        # Call the method that sets up the enhancement data and starts the first step
        self.on_start_note_enhancement_workflow() 

    

    def _display_enhancement_suggestions(self, suggestions: list):
        """Display the enhancement suggestions in a dialog using DialogManager."""
        if not suggestions:
            logger.info("No enhancement suggestions to display.")
            self.dialog_manager.show_information(self.NO_SUGGESTIONS_DIALOG_TITLE, self.NO_SUGGESTIONS_MESSAGE)
            return

        logger.info(f"Displaying {len(suggestions)} enhancement suggestions.")

        # NEW: Use DialogManager
        accepted_suggestion_text = self.dialog_manager.show_enhancement_suggestions_dialog(suggestions)
        if accepted_suggestion_text:
            self._insert_enhancement_suggestion(accepted_suggestion_text)

    def _insert_enhancement_suggestion(self, suggestion_text: str):
        """Inserts the accepted enhancement suggestion into the text editor."""
        if not suggestion_text:
            logger.warning("Attempted to insert an empty enhancement suggestion.")
            return
        
        cursor = self.text_edit.textCursor()
        # Add some spacing if not at the start of a line or if there's preceding text on the line
        if not cursor.atBlockStart():
            cursor.insertBlock() 
        # Could format it further, e.g., add a header or quote block
        cursor.insertText(suggestion_text)
        cursor.insertBlock() 

        self.statusBar().showMessage("Enhancement suggestion inserted.", 3000)
        self._on_text_changed()

    def insert_summary_at_cursor(self, summary: str):
        """
        Slot to handle request from SummaryPanel to insert summary at cursor.
        Delegates to AIFeatureManager.
        """
        logger.debug(f"MainWindow: insert_summary_at_cursor called with summary (first 50 chars): {summary[:50]}...")
        if self.ai_feature_manager:
            self.ai_feature_manager.insert_summary_into_editor(summary)
        else:
            logger.error("AIFeatureManager not initialized. Cannot insert summary.")
            # It's good practice to check for dialog_manager before using it,
            # though in MainWindow's __init__ it should be available.
            if hasattr(self, 'dialog_manager') and self.dialog_manager:
                self.dialog_manager.show_critical("Error", AI_FEATURES_UNAVAILABLE_ERROR)
            else: # Fallback if dialog_manager is somehow not there
                print("CRITICAL ERROR: AIFeatureManager and DialogManager not available.")

    def insert_summary_at_top(self, summary: str):
        """
        Slot to handle request from SummaryPanel to insert summary at the top.
        Delegates to AIFeatureManager.
        """
        logger.debug(f"MainWindow: insert_summary_at_top called with summary (first 50 chars): {summary[:50]}...")
        if self.ai_feature_manager:
            self.ai_feature_manager.insert_summary_at_top(summary)
        else:
            logger.error("AIFeatureManager not initialized. Cannot insert summary at top.")
            if hasattr(self, 'dialog_manager') and self.dialog_manager:
                self.dialog_manager.show_critical("Error", AI_FEATURES_UNAVAILABLE_ERROR)

    def insert_summary_at_bottom(self, summary: str):
        """
        Slot to handle request from SummaryPanel to insert summary at the bottom.
        Delegates to AIFeatureManager.
        """
        logger.debug(f"MainWindow: insert_summary_at_bottom called with summary (first 50 chars): {summary[:50]}...")
        if self.ai_feature_manager:
            self.ai_feature_manager.insert_summary_at_bottom(summary)
        else:
            logger.error("AIFeatureManager not initialized. Cannot insert summary at bottom.")
            if hasattr(self, 'dialog_manager') and self.dialog_manager:
                self.dialog_manager.show_critical("Error", AI_FEATURES_UNAVAILABLE_ERROR) 

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
        """Update the window title based on the current file, unsaved changes, and active workspace."""
        base_app_title = self.APP_TITLE
        active_workspace_name = self.workspace_manager.get_active_workspace_name()

        file_name_part = "Untitled"
        if self.document_model.current_file:
            file_name_part = os.path.basename(self.document_model.current_file)

        modified_indicator = "*" if self.document_model.unsaved_changes else ""

        title_elements = []
        if active_workspace_name:
            title_elements.append(f"[{active_workspace_name}]")
        
        title_elements.append(f"{file_name_part}{modified_indicator}")
        title_elements.append(base_app_title)

        self.setWindowTitle(" - ".join(title_elements))
        # logger.debug(f"Window title updated to: {' - '.join(title_elements)}")

    def enhance_current_note_with_ai(self):
        """Enhances the current note using AI, requesting plaintext output and using the standard preview dialog flow."""
        current_note_text = self.text_edit.toPlainText() # Check for empty text before calling on_enhance_note_triggered
        if not current_note_text.strip() or len(current_note_text.split()) < self.MIN_WORDS_FOR_ENHANCEMENT:
            self.dialog_manager.show_warning(
                self.MSG_NOT_ENOUGH_TEXT,
                f"Please provide at least {self.MIN_WORDS_FOR_ENHANCEMENT} words in your note to enhance it."
            )
            return

        logger.info("Triggering plaintext enhancement via on_enhance_note_triggered with style 'simple_enhance_plaintext'.")
        # This will now use the EnhancementStateManager and show the preview dialog.
        # Progress messages and status bar updates will be handled by the on_enhance_note_triggered flow.
        self.on_enhance_note_triggered(style="simple_enhance_plaintext")

    def update_status_bar(self, message):
        """Update the status bar with a message."""
        self.statusBar().showMessage(message, 5000)

    # Removed obsolete _display_enhanced_content method

    # --- NEW Enhancement Handler for Styles --- 

    def _handle_custom_prompt_for_enhancement(self) -> Optional[str]:
        """Handles the input dialog for a custom enhancement prompt."""
        text, ok = self.dialog_manager.get_text_input('Custom Enhancement Prompt',
                                        'Enter your enhancement instruction:')
        if ok and text:
            logger.info(f"User provided custom prompt: '{text[:50]}...'" )
            return text
        else:
            logger.info("Custom enhancement cancelled by user or empty prompt.")
            self.enhancement_state_manager.reset() # Reset if custom prompt is cancelled
            return None

    def _handle_template_prompt_for_enhancement(self, custom_prompt_from_template: str) -> Optional[str]:
        """Handles the prompt provided from a template selection."""
        if custom_prompt_from_template:
            logger.info("Using prompt from selected template.")
            return custom_prompt_from_template
        else:
            # This case should ideally not be reached if on_enhance_from_template_triggered handles it
            logger.error("Template style chosen but no prompt provided from template selection.")
            self.dialog_manager.show_critical(self, "Template Error", "No prompt was provided from the selected template.")
            self.enhancement_state_manager.reset()
            return None

    def on_enhance_note_triggered(self, style: str, custom_prompt_from_template: str = None):
        """Handles the 'Enhance Note' action trigger for different styles."""
        logger.info(f"Enhance Note triggered with style: {style}")

        # 1. Determine text to enhance (selection or full note)
        cursor = self.text_edit.textCursor()
        selected_text = cursor.selectedText()
        original_full_text = self.text_edit.toPlainText()
        
        text_for_prompt_generation = selected_text if selected_text else original_full_text
        is_selection = bool(selected_text)
        selection_info = {'start': cursor.selectionStart(), 'end': cursor.selectionEnd()} if is_selection else None

        # 2. Validate text length
        if not text_for_prompt_generation or len(text_for_prompt_generation.split()) < self.MIN_WORDS_FOR_ENHANCEMENT:
            logger.warning(f"Not enough text to enhance (less than {self.MIN_WORDS_FOR_ENHANCEMENT} words)")
            self.dialog_manager.show_warning(
                self.MSG_NOT_ENOUGH_TEXT,
                f"Please select or write more text ({self.MIN_WORDS_FOR_ENHANCEMENT} words minimum) to enhance."
            )
            return

        # 3. Handle Prompt Input based on style
        custom_prompt_input = None
        if style == "custom":
            custom_prompt_input = self._handle_custom_prompt_for_enhancement()
            if custom_prompt_input is None: # User cancelled or empty prompt
                return
        elif style == "template":
            custom_prompt_input = self._handle_template_prompt_for_enhancement(custom_prompt_from_template)
            if custom_prompt_input is None: # Error in template prompt handling
                return
        
        # 4. Construct the Prompt using the helper method
        prompt = self.enhancement_state_manager.get_enhancement_prompt(style, text_for_prompt_generation, custom_prompt_input)
        if not prompt: # Handle cases where prompt generation might fail
            logger.warning("Enhancement prompt generation failed.")
            self.enhancement_state_manager.reset() # Reset state if we abort
            return

        # 5. Initialize Enhancement State Manager
        self.enhancement_state_manager.start_enhancement(original_full_text, selection_info)
        self.enhancement_state_manager.generating_enhancement(prompt)

        # --- 6. Call AI Controller --- 
        try:
            max_tokens_setting = self.settings.get('AI', 'max_new_tokens_generation', 2048)
            try:
                max_tokens = int(max_tokens_setting)
            except (ValueError, TypeError):
                logger.warning(f"Invalid value '{max_tokens_setting}' for regeneration. Using default 2048.")
                max_tokens = 2048
            
            self.ai_controller.request_text_generation(prompt, max_new_tokens=max_tokens)
            self.statusBar().showMessage(f"Requesting '{style}' enhancement...", 3000)
            self.progress_manager.start_operation_with_message(f"Requesting AI enhancement ({style})...")
        except Exception as e:
            logger.error(f"Error triggering note enhancement (style: {style}): {e}", exc_info=True)
            self.dialog_manager.show_critical(NOTE_ENHANCEMENT_ERROR_TITLE, f"Could not start enhancement: {e}")
            self.enhancement_state_manager.enhancement_error(f"Failed to trigger AI: {e}")
            self.progress_manager.hide_progress()

    # --- Window Event Handlers ---
    def closeEvent(self, event):
        """Handles the window close event, checking for unsaved changes."""
        logger.debug("Close event triggered.")
        if self.document_model.unsaved_changes:
            logger.info("Unsaved changes detected on close.")
            reply = self.dialog_manager.show_question(
                title='Unsaved Changes',
                text="You have unsaved changes. Do you want to save them before quitting?",
                buttons=(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel),
                default_button=QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                logger.debug("User chose Save.")
                # Attempt to save. save_file returns True on success, False on failure/cancel.
                if self.file_controller.save_file():
                    logger.info("File saved successfully. Accepting close event.")
                    event.accept()
                else:
                    # Save failed or was cancelled by the user (e.g., in Save As dialog)
                    logger.info("Save operation failed or cancelled. Ignoring close event.")
                    event.ignore()
            elif reply == QMessageBox.Discard:
                logger.info("User chose Discard. Accepting close event.")
                event.accept()
            else: 
                logger.info("User chose Cancel or closed the dialog. Ignoring close event.")
                event.ignore()
        else:
            logger.debug("No unsaved changes. Accepting close event.")
            event.accept() 

    # --- Summary Panel Setup ---
    # Removed _setup_summary_dock_widget method

    def _get_token_estimates_for_preview(self, current_text: Optional[str]) -> tuple[Optional[int], Optional[int]]:
        """Helper to get token estimates for the preview dialog."""
        if not self.settings.get_ai_backend_is_api():
            return None, None

        estimated_input_tokens = None
        max_output_tokens = None

        if current_text:
            estimated_input_tokens = estimate_tokens(current_text)

        # Try to get max_output_tokens from the parameters of the last AI request
        last_request_params = self.enhancement_state_manager.get_last_request_params()
        if last_request_params:
            # 'max_new_tokens' is commonly used for generation tasks (see memory 3682c2ef...)
            if 'max_new_tokens' in last_request_params:
                max_output_tokens = last_request_params['max_new_tokens']
            elif 'max_output_tokens' in last_request_params: # Fallback for different naming
                max_output_tokens = last_request_params['max_output_tokens']
            # Add other potential keys if necessary

        # If not found in params, use general defaults as a last resort
        if max_output_tokens is None:
            logger.warning("Max output tokens not found in last request params, using general defaults.")
            backend_name = self.settings.get("ai", "backend")
            if backend_name == "google_gemini":
                max_output_tokens = 2048 # Default for Gemini (from memory 3682c2ef...)
            elif backend_name == "huggingface_api":
                max_output_tokens = 1024 # General placeholder
            else:
                # For local or unknown, maybe no explicit max output token concept for preview
                pass 

        return estimated_input_tokens, max_output_tokens

    def _show_enhancement_preview_dialog(self):
        """Shows the dialog for previewing, accepting, or refining the AI enhancement."""
        logger.info("Showing enhancement preview dialog.")
        if self.enhancement_state_manager.get_generated_text() is None: # CORRECTED METHOD
            logger.warning("No enhanced text available to preview.")
            self.dialog_manager.show_information(self, "No Enhancement", "No enhancement was generated or is available for preview.")
            return

        current_text = self.enhancement_state_manager.get_original_note_text() # CORRECTED METHOD
        enhanced_text = self.enhancement_state_manager.get_generated_text()

        estimated_input_tokens, max_output_tokens = self._get_token_estimates_for_preview(current_text)

        logger.debug(f"Preview Dialog - Input Tokens: {estimated_input_tokens}, Max Output: {max_output_tokens}")

        accepted_text_from_dialog = self.dialog_manager.show_enhancement_preview_dialog(enhanced_text, current_text, estimated_input_tokens, max_output_tokens)
        if accepted_text_from_dialog is not None:
            logger.info(self.MSG_ENHANCEMENT_ACCEPTED)
            accepted_text = accepted_text_from_dialog 
            selection_info = self.enhancement_state_manager.get_original_selection_info() # CORRECTED METHOD

            self.enhancement_state_manager.enhancement_accepted() # Update state

            if selection_info:
                logger.info(self.MSG_APPLYING_TO_SELECTION)
                cursor = self.text_edit.textCursor()
                cursor.beginEditBlock() 
                cursor.setPosition(selection_info['start'])
                cursor.setPosition(selection_info['end'], QTextCursor.KeepAnchor)
                cursor.insertText(accepted_text) 
                cursor.endEditBlock()
            else:
                logger.info(self.MSG_APPLYING_TO_FULL_NOTE)
                self.text_edit.setPlainText(accepted_text)

            self.document_model.set_content(self.text_edit.toPlainText()) # Update model
            self.statusBar().showMessage(self.MSG_ENHANCED_SUCCESSFULLY, 5000)
            self.enhancement_state_manager.reset() # Reset after successful application

    def _handle_enhancement_acceptance(self):
        """Handles the acceptance action from the EnhancementPreviewDialog."""
        logger.info(self.MSG_ENHANCEMENT_ACCEPTED)
        # Assumes the dialog is closed right after 'accepted' signal if modal
        # Need to get the final text *before* dialog might be destroyed
        # This requires coordination - maybe dialog passes text via signal?
        # Or we get it from the state manager *before* resetting?

        if self.enhancement_state_manager.get_state() != 'enhancement_received':
            logger.warning("Enhancement accepted in unexpected state: %s", self.enhancement_state_manager.get_state())
            # Don't reset if state is wrong
            return

        accepted_text = self.enhancement_state_manager.get_generated_text() # Get text before state change
        selection_info = self.enhancement_state_manager.get_original_selection_info() # CORRECTED METHOD

        self.enhancement_state_manager.enhancement_accepted() # Update state

        if selection_info:
            logger.info(self.MSG_APPLYING_TO_SELECTION)
            cursor = self.text_edit.textCursor()
            cursor.beginEditBlock() 
            cursor.setPosition(selection_info['start'])
            cursor.setPosition(selection_info['end'], QTextCursor.KeepAnchor)
            cursor.insertText(accepted_text) 
            cursor.endEditBlock()
        else:
            logger.info(self.MSG_APPLYING_TO_FULL_NOTE)
            self.text_edit.setPlainText(accepted_text)

        self.document_model.set_content(self.text_edit.toPlainText()) # Update model
        self.statusBar().showMessage(self.MSG_ENHANCED_SUCCESSFULLY, 5000)
        self.enhancement_state_manager.reset() # Reset after successful application

    def _handle_enhancement_rejection(self):
        """Handles the rejection action from the EnhancementPreviewDialog."""
        logger.info("Enhancement rejected by user.")
        if self.enhancement_state_manager.get_state() == 'enhancement_received':
            self.enhancement_state_manager.enhancement_rejected() # Update state
            self.statusBar().showMessage("Enhancement discarded.", 3000)
            self.enhancement_state_manager.reset() # Reset state
        else:
            logger.warning("Enhancement rejected in unexpected state: %s", self.enhancement_state_manager.get_state())

    def _on_enhancement_regenerate_requested(self):
        """Handles the request to regenerate an enhancement from the preview dialog."""
        logger.info("Enhancement regeneration requested by user.")

        # Close the current dialog that emitted the signal
        dialog_instance = self.sender()
        if dialog_instance and isinstance(dialog_instance, QDialog):
            logger.debug("Closing current enhancement preview dialog before regeneration.")
            dialog_instance.accept() # Or done(QDialog.Accepted) - just closes it

        if not self.enhancement_state_manager.is_active() or self.enhancement_state_manager.get_state() != 'enhancement_received':
            logger.warning("Regeneration requested but state is not 'enhancement_received' or not active. Resetting.")
            self.enhancement_state_manager.reset()
            self.dialog_manager.show_warning("Regeneration Error", "Cannot regenerate at this moment. Please try starting the enhancement again.")
            return

        original_prompt = self.enhancement_state_manager.enhancement_prompt
        if not original_prompt:
            logger.error("Cannot regenerate: Original prompt not found in state manager.")
            self.enhancement_state_manager.enhancement_error("Original prompt missing for regeneration.")
            self.dialog_manager.show_critical(NOTE_ENHANCEMENT_ERROR_TITLE, "Could not regenerate: original prompt is missing.")
            return

        logger.info("Proceeding with regeneration using the original prompt.")
        self.enhancement_state_manager.generating_enhancement(original_prompt) # Reset to awaiting_enhancement with same prompt

        try:
            max_tokens_setting = self.settings.get('AI', 'max_new_tokens_generation', 2048)
            try:
                max_tokens = int(max_tokens_setting)
            except (ValueError, TypeError):
                logger.warning(f"Invalid value '{max_tokens_setting}' for regeneration. Using default 2048.")
                max_tokens = 2048
            
            self.ai_controller.request_text_generation(original_prompt, max_new_tokens=max_tokens)
            self.statusBar().showMessage("Regenerating enhancement...", 3000)
            self.progress_manager.start_operation_with_message("Regenerating AI enhancement...")
        except Exception as e:
            logger.error(f"Error triggering note regeneration: {e}", exc_info=True)
            self.dialog_manager.show_critical(NOTE_ENHANCEMENT_ERROR_TITLE, f"Could not start regeneration: {e}")
            self.enhancement_state_manager.enhancement_error(f"Failed to trigger AI for regeneration: {e}") # Update state
            self.progress_manager.hide_progress()

    def _on_enhancement_refine_requested(self):
        """Handles the request to refine an enhancement from the preview dialog."""
        logger.info("Enhancement refinement requested by user.")

        # Close the current dialog that emitted the signal
        dialog_instance = self.sender()
        if dialog_instance and isinstance(dialog_instance, QDialog):
            logger.debug("Closing current enhancement preview dialog before refinement.")
            dialog_instance.accept() # Or done(QDialog.Accepted) - just closes it

        if not self.enhancement_state_manager.is_active() or self.enhancement_state_manager.get_state() != 'enhancement_received':
            logger.warning("Refinement requested but state is not 'enhancement_received' or not active. Resetting.")
            self.enhancement_state_manager.reset()
            self.dialog_manager.show_warning("Refinement Error", "Cannot refine at this moment. Please try starting the enhancement again.")
            return

        current_generated_text = self.enhancement_state_manager.get_generated_text()
        original_note_context = self.enhancement_state_manager.get_original_note_text() # Full original text for context
        # Original prompt that led to current_generated_text could also be useful context for the AI
        # prev_prompt = self.enhancement_state_manager.enhancement_prompt 

        if not current_generated_text:
            logger.error("Cannot refine: current generated text not found in state manager.")
            self.enhancement_state_manager.enhancement_error("Current generated text missing for refinement.")
            self.dialog_manager.show_critical(NOTE_ENHANCEMENT_ERROR_TITLE, "Could not refine: current text is missing.")
            return

        refinement_instructions, ok = self.dialog_manager.get_text_input(
            "Refine Enhancement", 
            "Provide instructions to refine the current enhancement:",
            QLineEdit.Normal,
            "e.g., Make it more formal, focus on the historical aspects, expand on the third point."
        )

        if ok and refinement_instructions:
            logger.info(f"User provided refinement instructions: '{refinement_instructions[:70]}...'" )
            
            # Construct a new prompt for refinement
            # Including original_note_context helps AI remember what the base was.
            # Including current_generated_text shows what it's starting from for this step.
            refinement_prompt = (
                f"You are refining a previously AI-generated text. Please consider the original context, "
                f"the text generated so far, and the user's specific instructions for this refinement pass.\n\n"
                f"## Original Full Note Context:\n---\n{original_note_context}\n---\n\n"
                f"## AI-Generated Text to Refine:\n---\n{current_generated_text}\n---\n\n"
                f"## User's Refinement Instructions:\n---\n{refinement_instructions}\n---\n\n"
                f"Based on all the above, please provide ONLY the new, fully refined version of the 'AI-Generated Text to Refine'."
            )
            
            self.enhancement_state_manager.start_refinement(feedback=refinement_instructions)
            self.enhancement_state_manager.generating_enhancement(prompt=refinement_prompt)

            try:
                max_tokens_setting = self.settings.get('AI', 'max_new_tokens_generation', 2048) # Default to a higher value for generation
                try:
                    max_tokens = int(max_tokens_setting)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value '{max_tokens_setting}' for max_new_tokens_generation. Using default 2048.")
                    max_tokens = 2048

                self.ai_controller.request_text_generation(refinement_prompt, max_new_tokens=max_tokens)
                self.statusBar().showMessage("Refining enhancement...", 3000)
                self.progress_manager.start_operation_with_message("Refining AI enhancement based on your feedback...")
            except Exception as e:
                logger.error(f"Error triggering note refinement: {e}", exc_info=True)
                self.dialog_manager.show_critical(NOTE_ENHANCEMENT_ERROR_TITLE, f"Could not start refinement: {e}")
                self.enhancement_state_manager.enhancement_error(f"Failed to trigger AI for refinement: {e}")
                self.progress_manager.hide_progress()
        else:
            logger.info("Refinement cancelled by user or empty instructions. Resetting state.")
            self.enhancement_state_manager.reset() # Reset if user cancels refinement input
            self.statusBar().showMessage("Refinement cancelled.", 3000)

    def on_manage_enhancement_templates(self):
        """Open the dialog to manage enhancement templates."""
        logger.info("Opening enhancement template manager dialog.")
        try:
            # Use DialogManager to show the template manager dialog
            self.dialog_manager.show_template_manager_dialog(settings=self.settings, parent=self)
            # The dialog_manager method will handle creation and exec_()
        except Exception as e:
            logger.error(f"Error opening template manager dialog via DialogManager: {e}", exc_info=True)
            self.dialog_manager.show_critical("Error", f"Could not open template manager: {e}")

    def on_enhance_from_template_triggered(self):
        """Trigger enhancement using a user-selected saved template."""
        logger.info("Enhance from template triggered.")
        templates = self.settings.get_enhancement_templates()

        if not templates:
            self.dialog_manager.show_information("No Templates", 
                                  "You don't have any saved enhancement templates yet. "
                                  "Please create some via 'AI Tools' -> 'Manage Enhancement Templates...'")
            return

        template_names = list(templates.keys())
        chosen_template_name, ok = self.dialog_manager.get_item_input(self, "Select Enhancement Template", 
                                                      "Choose a template:", template_names, 0, False)

        if ok and chosen_template_name:
            chosen_prompt = templates.get(chosen_template_name)
            if chosen_prompt:
                logger.info(f"User selected template: '{chosen_template_name}'")
                # Call the main enhancement trigger with 'template' style and the chosen prompt
                self.on_enhance_note_triggered(style="template", custom_prompt_from_template=chosen_prompt)
            else:
                # Should not happen if templates dict is consistent
                logger.error(f"Selected template '{chosen_template_name}' has no prompt. This is unexpected.")
                self.dialog_manager.show_critical("Template Error", f"The selected template '{chosen_template_name}' is empty or corrupted.")
        else:
            logger.info("Template selection cancelled by user.")

    def on_configure_ai_services(self):
        """Opens the AI Services configuration dialog."""
        logger.info("AI Services configuration action triggered.")
        # Pass the main app_settings instance (Settings class) to the dialog
        self.dialog_manager.show_ai_services_dialog(settings=self.settings) # Use DialogManager
        logger.info("AI Services configuration dialog closed.")

    # --- File Explorer Panel Setup and Slots ---

    def on_open_folder_selected(self):
        """Handles the 'Open Folder...' action from the File menu."""
        current_path = self.file_system_model.rootPath()
        folder_path = self.dialog_manager.get_existing_directory(
            "Select Workspace Folder",
            current_path
        )
        if folder_path:
            logger.info(f"User selected new workspace folder: {folder_path}")
            self.file_system_model.setRootPath(folder_path)
            self.file_tree_view.setRootIndex(self.file_system_model.index(folder_path))
            self.settings.set('General', 'last_workspace_path', folder_path)
            self.update_window_title() # Update window title with new folder if needed

    def on_toggle_file_explorer(self, checked):
        """Handles the 'Toggle File Explorer' action from the View menu."""
        if checked:
            self.file_explorer_dock_widget.show()
            logger.debug("File Explorer panel shown.")
        else:
            self.file_explorer_dock_widget.hide()
            logger.debug("File Explorer panel hidden.")

    def on_refresh_file_explorer(self):
        """Refreshes the file explorer tree view."""
        logger.info("Refresh file explorer action triggered.")
        if self.file_system_model and self.file_tree_view:
            # Store current expansion state
            # expanded_items = self._get_expansion_state()

            # Re-set the root path to force a refresh of the model's directory listing.
            # This is a common way to refresh QFileSystemModel.
            current_root_path = self.file_system_model.rootPath()
            # self.file_system_model.setRootPath('') # Temporarily set to empty to force complete refresh
            self.file_system_model.setRootPath(current_root_path)
            self.file_tree_view.setRootIndex(self.file_system_model.index(current_root_path))

            # Re-apply filters if any (e.g., to hide .git, .DS_Store)
            # self.file_system_model.setNameFilters(["*"])
            # self.file_system_model.setNameFilterDisables(False) # Ensure filters are active
            # self.file_tree_view.setColumnHidden(1, True) # Hide size
            # self.file_tree_view.setColumnHidden(2, True) # Hide type
            # self.file_tree_view.setColumnHidden(3, True) # Hide date modified

            # Restore expansion state
            # self._restore_expansion_state(expanded_items) # This might be tricky with simple setRootPath
            # A simple refresh might not need to preserve expansion perfectly if not easily done.

            self.statusBar().showMessage("File explorer refreshed.", 3000)
            logger.info(f"File explorer refreshed for path: {current_root_path}")
        else:
            logger.warning("File system model or tree view not available for refresh.")

    def on_rename_item(self, index):
        """Handles renaming a file or folder from the context menu."""
        if not index.isValid():
            return

        old_path = self.file_system_model.filePath(index)
        is_dir = self.file_system_model.isDir(index)
        old_base_name = os.path.basename(old_path)

        item_type = "folder" if is_dir else "file"
        prompt_title = f"Rename {item_type.capitalize()}"
        prompt_label = f"Enter new name for {item_type} '{old_base_name}':"

        new_name_input, ok = self.dialog_manager.get_text_input(self, prompt_title, prompt_label, old_base_name)

        if not ok or not new_name_input:
            logger.info("Rename operation cancelled by user or empty name provided.")
            return

        if new_name_input == old_base_name:
            logger.info("Rename operation cancelled: new name is the same as old name.")
            return

        is_valid, msg_or_validated_name, validated_name = self._validate_new_name_for_rename(new_name_input, old_base_name, is_dir)
        
        if not is_valid:
            self.dialog_manager.show_warning(INVALID_NAME_TITLE, msg_or_validated_name)
            return

        parent_dir = os.path.dirname(old_path)
        new_path = os.path.join(parent_dir, validated_name)

        if os.path.exists(new_path):
            self.dialog_manager.show_warning(RENAME_ERROR_TITLE, f"A file or folder with the name '{validated_name}' already exists.")
            return

        logger.info(f"Attempting to rename '{old_path}' to '{new_path}'")
        # print(f"DEBUG: Calling file_controller.rename_item('{old_path}', '{new_path}')") # Temporary debug
        
        success, message = self.file_controller.rename_item(old_path, new_path)
        
        if success:
            self.dialog_manager.show_information(RENAME_SUCCESSFUL_TITLE, message)
            # QFileSystemModel should update automatically. If not, uncomment below or find a better way.
            # current_root = self.file_system_model.rootPath()
            # self.file_system_model.setRootPath("") # Invalidate current model view temporarily
            # self.file_system_model.setRootPath(current_root) # Reset to force refresh
            # self.file_tree_view.setRootIndex(self.file_system_model.index(current_root))
        else:
            self.dialog_manager.show_critical(RENAME_FAILED_TITLE, message)

    def on_create_new_file_item(self, in_directory=None):
        """Handles creation of a new file from context menu."""
        base_path = in_directory if in_directory else self.file_system_model.rootPath()
        
        file_name, ok = self.dialog_manager.get_text_input("New File", "Enter file name (e.g., note.txt or note.md):", "untitled.md")
        if ok and file_name:
            if not (file_name.endswith(".txt") or file_name.endswith(".md")):
                self.dialog_manager.show_warning(INVALID_NAME_TITLE, "File name must end with .txt or .md")
                return
            
            new_file_path = QDir(base_path).filePath(file_name)

            logger.info(f"Attempting to create new file: {new_file_path}")
            success, message = self.file_controller.create_file(new_file_path)
            if success:
                logger.info(f"File created: {new_file_path}")
                # QFileSystemModel should update automatically. If not, specific refresh might be needed.
                # self.file_system_model.directoryLoaded.emit(base_path) # Force refresh of parent
            else:
                self.dialog_manager.show_warning("Error Creating File", message)
                logger.error(f"Error creating file '{new_file_path}': {message}")

    def on_create_new_folder_item(self, in_directory=None):
        """Handles creation of a new folder from context menu."""
        base_path = in_directory if in_directory else self.file_system_model.rootPath()
        
        folder_name, ok = self.dialog_manager.get_text_input("New Folder", "Enter folder name:", "Untitled Folder")
        if ok and folder_name:
            new_folder_path = QDir(base_path).filePath(folder_name)

            logger.info(f"Attempting to create new folder: {new_folder_path}")
            success, message = self.file_controller.create_folder(new_folder_path)
            if success:
                logger.info(f"Folder created: {new_folder_path}")
            else:
                self.dialog_manager.show_warning("Error Creating Folder", message)
                logger.error(f"Error creating folder '{new_folder_path}': {message}")

    def _on_text_changed(self):
        """Handle the textChanged signal from the text editor."""
        # This method is called whenever the text in the editor changes.
        # logger.debug("Text changed") 
        self.document_model.set_content(self.text_edit.toPlainText()) 
        self._update_status_bar_word_count() # Update word count on text change
        # Potentially update UI elements, e.g., enable save action
        if hasattr(self, 'action_save') and self.action_save:
             self.action_save.setEnabled(self.document_model.unsaved_changes) 
        self.update_title() 
        # Auto-save logic could be triggered here after a delay

    def _on_cursor_position_changed(self):
        """Handle the cursorPositionChanged signal from the text editor."""
        # This method is called whenever the cursor position changes.
        # logger.debug("Cursor position changed") 
        # Update status bar with current line/column, or other contextual info
        cursor = self.text_edit.textCursor()
        line_num = cursor.blockNumber() + 1
        col_num = cursor.columnNumber() + 1
        self.statusBar().showMessage(f"Line: {line_num}, Col: {col_num}", 2000) # Show briefly 
        self._update_contextual_actions() 

    def _update_status_bar_word_count(self):
        """Update the word count in the status bar."""
        current_text = self.text_edit.toPlainText()
        if not current_text.strip(): # Handle empty or whitespace-only text
            word_count = 0
        else:
            words = current_text.split() # Simple split by whitespace
            word_count = len(words)
        
        if hasattr(self, 'word_count_label'): # Ensure label exists
            self.word_count_label.setText(f"Words: {word_count}")
        else:
            logger.warning("Word count label not initialized in status bar.")

    def _update_contextual_actions(self):
        """Placeholder: Update contextual actions based on editor state (e.g., selection)."""
        # logger.debug("Updating contextual actions (placeholder).")
        # Example logic (to be expanded):
        has_selection = self.text_edit.textCursor().hasSelection()
        # Example: Enable/disable actions based on selection
        if hasattr(self, 'action_cut'): self.action_cut.setEnabled(has_selection)
        if hasattr(self, 'action_copy'): self.action_copy.setEnabled(has_selection)
        if hasattr(self, 'action_search_selected'): self.action_search_selected.setEnabled(has_selection)
        # Add more actions as needed

    def _validate_new_name_for_rename(self, new_name: str, old_base_name: str, is_dir: bool) -> tuple[bool, str, str]:
        """Validates the new name for a rename operation.

        Returns:
            Tuple: (is_valid, message_or_validated_name, validated_name_if_different)
                   If not valid, message_or_validated_name contains the error message.
                   If valid, message_or_validated_name contains the (potentially modified) new_name.
                   validated_name_if_different returns the final validated name. 
        """
        validated_name = new_name
        if not is_dir:  # File specific validation
            old_name_parts = os.path.splitext(old_base_name)
            new_name_parts = os.path.splitext(new_name)

            # Ensure extension is maintained or correctly changed for .txt/.md files
            if old_name_parts[1].lower() in ['.txt', '.md'] and new_name_parts[1].lower() not in ['.txt', '.md']:
                validated_name += old_name_parts[1]  # Append old extension if new one is missing or different
                logger.info(f"Appended original extension to new file name: {validated_name}")
            
            if not (validated_name.endswith('.txt') or validated_name.endswith('.md')):
                return False, "File name must end with .txt or .md", validated_name
        
        # Basic validation for any OS-prohibited characters
        if any(char in validated_name for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            return False, "The name contains invalid characters.", validated_name
        
        return True, validated_name, validated_name

    def on_delete_item(self, path: str, is_dir: bool):
        """Handles deleting a file or folder from the context menu."""
        item_type = "folder" if is_dir else "file"
        item_name = os.path.basename(path)

        reply = self.dialog_manager.show_question(
            DELETE_CONFIRM_TITLE,
            f"Are you sure you want to permanently delete the {item_type} '{item_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            logger.info(f"User confirmed deletion of {item_type}: {path}")
            success, message = self.file_controller.delete_item(path, is_dir)
            if success:
                self.dialog_manager.show_information(DELETE_SUCCESSFUL_TITLE, message)
                # If the deleted file was the currently open note, clear the editor
                if not is_dir and self.document_model.get_current_file() == path:
                    self.file_controller.new_note(ask_save=False) # Clears editor and resets model
                    self.statusBar().showMessage(f"{item_type.capitalize()} '{item_name}' deleted and editor cleared.", 5000)
                else:
                    self.statusBar().showMessage(message, 3000)
                # QFileSystemModel should update automatically. 
                # If issues, might need to trigger a refresh of the parent directory or root.
            else:
                self.dialog_manager.show_critical(DELETE_FAILED_TITLE, message)
                self.statusBar().showMessage(f"Failed to delete {item_name}: {message}", 5000)
        else:
            logger.info(f"User cancelled deletion of {item_type}: {path}")


    def _update_file_explorer_root(self, new_root_path: Optional[str] = None):
        """Updates the root directory of the file explorer panel based on the active workspace path."""
        # If new_root_path is not provided, try to get it from the workspace_manager
        if new_root_path is None:
            active_workspace_path = self.workspace_manager.get_active_workspace_path()
            logger.debug(f"_update_file_explorer_root called. Active workspace path: {active_workspace_path}")
            new_root_path = active_workspace_path # Use this path
        else:
            logger.debug(f"_update_file_explorer_root called with new_root_path: {new_root_path}")

        active_ws_name = self.workspace_manager.get_active_workspace_name()

        # Delegate display logic to ExplorerPanelManager
        if hasattr(self, 'explorer_panel_manager') and self.explorer_panel_manager:
            self.explorer_panel_manager.update_explorer_display(new_root_path, active_ws_name)
        else:
            logger.error("ExplorerPanelManager not available in MainWindow during _update_file_explorer_root")
            # Fallback or error handling if explorer_panel_manager is not set up
            # This part might need adjustment based on how critical this is at this stage
            if self.workspace_welcome_widget:
                self.workspace_welcome_widget.show()
            if self.file_tree_widget:
                self.file_tree_widget.hide()

        # MainWindow remains responsible for status bar and title updates
        if new_root_path and os.path.isdir(new_root_path):
            self.statusBar().showMessage(f"Workspace '{active_ws_name}' loaded.", 3000)
        elif active_ws_name and (not new_root_path or not os.path.isdir(new_root_path)):
            self.statusBar().showMessage(f"Workspace '{active_ws_name}' path invalid. Please select a workspace.", 5000)
        elif not active_ws_name:
            self.statusBar().showMessage("No active workspace. Please select or create one.", 3000)
        else: # new_root_path was provided but invalid
            self.statusBar().showMessage(f"Cannot open path: {new_root_path}.", 5000)

        self.update_title() # Update window title
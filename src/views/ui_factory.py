from PyQt5.QtWidgets import QAction, QToolBar
from PyQt5.QtGui import QIcon
import logging
from functools import partial

logger = logging.getLogger(__name__)

def create_file_menu(main_window, menubar):
    """Creates and returns the File menu."""
    file_menu = menubar.addMenu('&File')
    
    new_action = QAction("&New", main_window)
    new_action.setShortcut("Ctrl+N")
    new_action.setStatusTip("Create a new note")
    new_action.triggered.connect(main_window.file_controller.new_note)
    file_menu.addAction(new_action)
    
    open_action = QAction("&Open", main_window)
    open_action.setShortcut("Ctrl+O")
    open_action.setStatusTip("Open an existing note")
    open_action.triggered.connect(main_window.file_controller.open_note)
    file_menu.addAction(open_action)
    
    save_action = QAction("&Save", main_window)
    save_action.setShortcut("Ctrl+S")
    save_action.setStatusTip("Save the current note")
    save_action.triggered.connect(main_window.file_controller.save_note)
    file_menu.addAction(save_action)
    
    save_as_action = QAction("Save &As...", main_window)
    save_as_action.setShortcut("Ctrl+Shift+S")
    save_as_action.setStatusTip("Save the current note with a new name")
    save_as_action.triggered.connect(main_window.file_controller.save_note_as)
    file_menu.addAction(save_as_action)
    
    file_menu.addSeparator()
    
    exit_action = QAction("E&xit", main_window)
    exit_action.setShortcut("Ctrl+Q")
    exit_action.setStatusTip("Exit the application")
    exit_action.triggered.connect(main_window.close)
    file_menu.addAction(exit_action)
    
    return file_menu

def create_edit_menu(main_window, menubar):
    """Creates and returns the Edit menu."""
    edit_menu = menubar.addMenu("&Edit")
    
    main_window.undo_action = QAction("&Undo", main_window)
    main_window.undo_action.setShortcut("Ctrl+Z")
    main_window.undo_action.setStatusTip("Undo the last action")
    main_window.undo_action.triggered.connect(main_window.text_edit.undo)
    edit_menu.addAction(main_window.undo_action)
    
    main_window.redo_action = QAction("&Redo", main_window)
    main_window.redo_action.setShortcut("Ctrl+Y")
    main_window.redo_action.setStatusTip("Redo the last undone action")
    main_window.redo_action.triggered.connect(main_window.text_edit.redo)
    edit_menu.addAction(main_window.redo_action)
    
    edit_menu.addSeparator()
    
    main_window.cut_action = QAction("Cu&t", main_window)
    main_window.cut_action.setShortcut("Ctrl+X")
    main_window.cut_action.setStatusTip("Cut the selected text")
    main_window.cut_action.triggered.connect(main_window.text_edit.cut)
    edit_menu.addAction(main_window.cut_action)
    
    main_window.copy_action = QAction("&Copy", main_window)
    main_window.copy_action.setShortcut("Ctrl+C")
    main_window.copy_action.setStatusTip("Copy the selected text")
    main_window.copy_action.triggered.connect(main_window.text_edit.copy)
    edit_menu.addAction(main_window.copy_action)
    
    main_window.paste_action = QAction("&Paste", main_window)
    main_window.paste_action.setShortcut("Ctrl+V")
    main_window.paste_action.setStatusTip("Paste text from clipboard")
    main_window.paste_action.triggered.connect(main_window.text_edit.paste)
    edit_menu.addAction(main_window.paste_action)
    
    edit_menu.addSeparator()
    
    main_window.select_all_action = QAction("Select &All", main_window)
    main_window.select_all_action.setShortcut("Ctrl+A")
    main_window.select_all_action.setStatusTip("Select all text")
    main_window.select_all_action.triggered.connect(main_window.text_edit.selectAll)
    edit_menu.addAction(main_window.select_all_action)
    
    return edit_menu

def create_ai_tools_menu(main_window, menubar):
    """Create the AI Tools menu and its actions."""
    ai_menu = menubar.addMenu("&AI Tools")
    ai_menu.setObjectName("AiMenu")

    # --- Summarization --- #
    action_summarize = QAction(QIcon.fromTheme("edit-copy"), "&Summarize Note", main_window)
    action_summarize.setStatusTip("Generate a summary of the current note using AI")
    # Check if the target method exists before connecting
    if hasattr(main_window, 'on_summarize_note'):
        action_summarize.triggered.connect(main_window.on_summarize_note)
    else:
        logger.warning("Method 'on_summarize_note' not found in main_window.")
        action_summarize.setEnabled(False)
    ai_menu.addAction(action_summarize)
    main_window.action_summarize = action_summarize # Store action reference

    # --- Enhancement Submenu --- #
    enhance_menu = ai_menu.addMenu(QIcon.fromTheme("document-edit"), "&Enhance Note") # Changed to addMenu
    enhance_menu.setObjectName("EnhanceNoteMenu")

    styles = {
        "Improve Clarity": "clarity",
        "Make Concise": "concise",
        "Expand Details": "expand",
        "Custom Prompt...": "custom"
    }

    for text, style_key in styles.items():
        action_enhance_style = QAction(text, main_window)
        action_enhance_style.setStatusTip(f"Enhance the note or selection using AI ({text})")
        # Use partial to pass the style_key to the handler
        if hasattr(main_window, 'on_enhance_note_triggered'):
            action_enhance_style.triggered.connect(partial(main_window.on_enhance_note_triggered, style=style_key))
            # Store action reference if needed, e.g., for dynamic enabling/disabling
            setattr(main_window, f"action_enhance_{style_key}", action_enhance_style)
        else:
            logger.warning(f"Method 'on_enhance_note_triggered' not found in main_window for style '{style_key}'.")
            action_enhance_style.setEnabled(False)
        enhance_menu.addAction(action_enhance_style)

    action_enhance_from_template = QAction(QIcon.fromTheme("view-list-text"), "From Saved &Template...", main_window) # Example Icon
    action_enhance_from_template.setStatusTip("Enhance text using a saved template")
    if hasattr(main_window, 'on_enhance_from_template_triggered'):
        action_enhance_from_template.triggered.connect(main_window.on_enhance_from_template_triggered)
    else:
        logger.warning("Method 'on_enhance_from_template_triggered' not found in main_window.")
        action_enhance_from_template.setEnabled(False)
    enhance_menu.addAction(action_enhance_from_template)
    main_window.action_enhance_from_template = action_enhance_from_template

    enhance_menu.addSeparator()

    # --- Text Generation --- #
    action_generate_text = QAction(QIcon.fromTheme("applications-accessories"), "&Generate Text from Prompt...", main_window)
    action_generate_text.setStatusTip("Generate new text content based on a prompt")
    if hasattr(main_window, 'on_generate_note_text'):
        action_generate_text.triggered.connect(main_window.on_generate_note_text)
    else:
        logger.warning("Method 'on_generate_note_text' not found in main_window.")
        action_generate_text.setEnabled(False)
    ai_menu.addAction(action_generate_text)
    main_window.action_generate_text = action_generate_text

    ai_menu.addSeparator()

    # --- Enhancement Templates --- #
    action_manage_templates = QAction(QIcon.fromTheme("document-properties"), "Manage Enhancement &Templates...", main_window)
    action_manage_templates.setStatusTip("Create, edit, or delete custom enhancement templates")
    if hasattr(main_window, 'on_manage_enhancement_templates'):
        action_manage_templates.triggered.connect(main_window.on_manage_enhancement_templates)
    else:
        logger.warning("Method 'on_manage_enhancement_templates' not found in main_window.")
        action_manage_templates.setEnabled(False)
    ai_menu.addAction(action_manage_templates)
    main_window.action_manage_templates = action_manage_templates

    # --- AI Services Configuration --- #
    action_configure_ai = QAction(QIcon.fromTheme("preferences-system"), "&AI Services", main_window)
    action_configure_ai.setStatusTip("Configure AI model settings, backends, and API keys")
    if hasattr(main_window, 'on_configure_ai_services'):
        action_configure_ai.triggered.connect(main_window.on_configure_ai_services)
    else:
        logger.warning("Method 'on_configure_ai_services' not found in main_window.")
        action_configure_ai.setEnabled(False)
    ai_menu.addAction(action_configure_ai)
    main_window.action_configure_ai = action_configure_ai

    # --- Model Selection (Legacy/Alternative) --- #
    action_select_model = QAction(QIcon.fromTheme("deepbrain"), "Select &Local Model...", main_window) # Example Icon
    action_select_model.setStatusTip("Select the local AI model for processing")
    if hasattr(main_window, 'on_select_model'):
        action_select_model.triggered.connect(main_window.on_select_model)
    else:
        logger.warning("Method 'on_select_model' not found in main_window.")
        action_select_model.setEnabled(False)
    # ai_menu.addAction(action_select_model) # Optionally hide if Configure AI is preferred
    main_window.action_select_model = action_select_model

    logger.debug("AI Tools menu created.")
    return ai_menu

def create_view_menu(main_window, menubar):
    """Creates and returns the View menu."""
    view_menu = menubar.addMenu("&View")
    # Add view-related actions here, e.g., toggle panels, themes
    # Example: Toggle Summary Panel Action (if it's not already handled by dock widget itself)
    # if hasattr(main_window, 'summary_dock_widget'):
    #     toggle_summary_panel_action = main_window.summary_dock_widget.toggleViewAction()
    #     toggle_summary_panel_action.setText("Toggle Summary Panel")
    #     view_menu.addAction(toggle_summary_panel_action)
    return view_menu

def create_context_menu_actions(main_window, menubar):
    """Creates and returns the Context menu (for menubar)."""
    context_menu = menubar.addMenu("&Context")
    
    return context_menu

def populate_toolbar(main_window, toolbar):
    """Populates the given toolbar with actions."""
    new_action = QAction(QIcon.fromTheme("document-new"), "New", main_window) 
    new_action.setStatusTip("Create a new note")
    new_action.triggered.connect(main_window.file_controller.new_note)
    toolbar.addAction(new_action)
    
    open_action = QAction(QIcon.fromTheme("document-open"), "Open", main_window)
    open_action.setStatusTip("Open an existing note")
    open_action.triggered.connect(main_window.file_controller.open_note)
    toolbar.addAction(open_action)
    
    save_action = QAction(QIcon.fromTheme("document-save"), "Save", main_window)
    save_action.setStatusTip("Save the current note")
    save_action.triggered.connect(main_window.file_controller.save_note)
    toolbar.addAction(save_action)
    

    if hasattr(main_window, 'action_summarize_note'): # Check correct attribute name
        toolbar.addAction(main_window.action_summarize_note)
    elif hasattr(main_window, 'action_summarize'):
        toolbar.addAction(main_window.action_summarize)

    # Add Enhance Note submenu trigger (optional, could be complex for toolbar)
    # enhance_button = QToolButton()
    # enhance_button.setIcon(QIcon.fromTheme("document-edit"))
    # enhance_button.setToolTip("Enhance Note (Styles)")
    # enhance_button.setPopupMode(QToolButton.InstantPopup)
    # enhance_menu = QMenu()
    # if hasattr(main_window, 'action_enhance_clarity'): enhance_menu.addAction(main_window.action_enhance_clarity)
    # if hasattr(main_window, 'action_enhance_concise'): enhance_menu.addAction(main_window.action_enhance_concise)
    # if hasattr(main_window, 'action_enhance_expand'): enhance_menu.addAction(main_window.action_enhance_expand)
    # if hasattr(main_window, 'action_enhance_custom'): enhance_menu.addAction(main_window.action_enhance_custom)
    # enhance_menu.setMenu(enhance_button)
    # toolbar.addWidget(enhance_button)

    if hasattr(main_window, 'action_generate_text'):
        toolbar.addAction(main_window.action_generate_text)

from PyQt5.QtWidgets import QAction, QToolBar, QApplication, QMenu
from PyQt5.QtGui import QIcon
import logging
from functools import partial

logger = logging.getLogger(__name__)

def _create_enhance_note_submenu(main_window, ai_tools_menu):
    """Helper function to create the 'Enhance Note' submenu."""
    enhance_note_menu = QMenu("&Enhance Note", main_window)
    ai_tools_menu.addMenu(enhance_note_menu)

    enhancement_styles = {
        "Default Enhance": "default_enhance",
        "Improve Clarity": "clarity",
        "Make Concise": "concise",
        "Expand Details": "expand",
        "Custom Prompt...": "custom"
    }

    for text, style_key in enhancement_styles.items():
        action = QAction(text, main_window)
        action.setStatusTip(f"Enhance note focusing on {style_key.replace('_', ' ')}")
        # Use functools.partial to pass the style_key to the handler
        action.triggered.connect(partial(main_window.on_enhance_note_triggered, style_key))
        enhance_note_menu.addAction(action)
    
    # Add 'Enhance from Template...' action separately
    enhance_from_template_action = QAction("Enhance from &Template...", main_window)
    enhance_from_template_action.setStatusTip("Enhance note using a saved prompt template")
    enhance_from_template_action.triggered.connect(main_window.on_enhance_from_template_triggered)
    enhance_note_menu.addAction(enhance_from_template_action)

    # Action to manage templates
    manage_templates_action = QAction("&Manage Enhancement Templates...", main_window)
    manage_templates_action.setStatusTip("Open the enhancement template manager")
    manage_templates_action.triggered.connect(main_window.on_manage_enhancement_templates)
    enhance_note_menu.addSeparator()
    enhance_note_menu.addAction(manage_templates_action)


def create_file_menu(main_window, menubar):
    """Creates the File menu and its actions."""
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
    
    main_window.open_folder_action = QAction(QIcon.fromTheme("folder-open", QIcon(":/icons/folder-open.png")), "&Open Folder...", main_window)
    main_window.open_folder_action.setStatusTip("Open an existing folder to browse files")
    main_window.open_folder_action.triggered.connect(main_window.on_open_folder_selected) # Connect to slot
    file_menu.addAction(main_window.open_folder_action)

    manage_workspaces_action = QAction(QIcon.fromTheme("system-file-manager"), "&Manage Workspaces...", main_window)
    manage_workspaces_action.setStatusTip("Create, remove, or set active workspaces")
    manage_workspaces_action.triggered.connect(main_window.explorer_panel_manager.show_workspace_manager_dialog)
    file_menu.addAction(manage_workspaces_action)
    
    file_menu.addSeparator()
    
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

    # Recent Workspaces submenu
    # The menu is now created and managed by ExplorerPanelManager
    recent_workspaces_menu = main_window.explorer_panel_manager.get_recent_workspaces_menu()
    file_menu.addMenu(recent_workspaces_menu)
    
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
    ai_tools_menu = menubar.addMenu("&AI Tools")

    # Summarize Note action
    summarize_action = QAction("&Summarize Note", main_window)
    summarize_action.setStatusTip("Generate a summary of the current note")
    summarize_action.triggered.connect(main_window.ai_feature_manager.trigger_summarization)
    ai_tools_menu.addAction(summarize_action)

    # Generate Note Text action
    main_window.action_generate_text = QAction("Generate Text from &Prompt...", main_window)
    main_window.action_generate_text.setStatusTip("Generate new text content based on a custom prompt")
    main_window.action_generate_text.triggered.connect(main_window.ai_feature_manager.trigger_text_generation)
    ai_tools_menu.addAction(main_window.action_generate_text)

    ai_tools_menu.addSeparator()

    # Enhance Note submenu (created by helper)
    _create_enhance_note_submenu(main_window, ai_tools_menu)

    ai_tools_menu.addSeparator()

    # AI Services Configuration action
    configure_ai_services_action = QAction("&AI Services", main_window)
    configure_ai_services_action.setStatusTip("Configure AI model providers and API keys")
    configure_ai_services_action.triggered.connect(main_window.on_configure_ai_services)
    ai_tools_menu.addAction(configure_ai_services_action)

    # Select Model action (if using local models directly that need selection)
    action_select_model = QAction("Select &Model...", main_window)
    action_select_model.setStatusTip("Select the AI model for summarization and generation")
    action_select_model.triggered.connect(main_window.ai_feature_manager.trigger_model_selection)
    ai_tools_menu.addAction(action_select_model)

    return ai_tools_menu

def create_view_menu(main_window, menubar):
    """Creates and returns the View menu."""
    view_menu = menubar.addMenu("&View")

    # Add the toggle action for the File Explorer Panel
    # This action was created in MainWindow.__init__ using file_explorer_dock_widget.toggleViewAction()
    if hasattr(main_window, 'file_explorer_toggle_action') and main_window.file_explorer_toggle_action:
        view_menu.addAction(main_window.file_explorer_toggle_action)
        # The text and status tip are already set on this action in MainWindow
    else:
        # This case should ideally not be hit if MainWindow initializes correctly.
        # logger.warning("create_view_menu: main_window.file_explorer_toggle_action not found.") # Optional logging
        pass # Or add a disabled placeholder action

    # Example: Add a toggle for the Summary Panel if you want one
    if hasattr(main_window, 'summary_dock_widget'):
        summary_panel_toggle_action = main_window.summary_dock_widget.toggleViewAction()
        summary_panel_toggle_action.setText("Toggle Summary Panel")
        summary_panel_toggle_action.setStatusTip("Show or hide the Summary panel")
        view_menu.addAction(summary_panel_toggle_action)
    
    # Themes submenu (ensure QMenu is imported)
    # from PyQt5.QtWidgets import QMenu 
    themes_menu = QMenu("&Themes", main_window) 
    view_menu.addMenu(themes_menu)
    
    return view_menu

def create_context_menu_actions():
    """Creates context menu actions for the text editor."""
    # Example: main_window.text_edit.customContextMenuRequested.connect(lambda pos: on_text_edit_context_menu(main_window, pos))
    # For now, this function might not be strictly necessary if context menus are
    # built directly where needed (e.g., in MainWindow for the text_edit)
    # If it becomes a factory for actions used in multiple context menus, it makes sense.
    
    # This function appears to be unused as per lint. Removing main_window and menubar params if not used here.
    # If it's intended to be called, its call site and usage need to be clarified.
    pass # Placeholder if no actions are being created globally here

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

class UiFactory:
    def setup_menus_and_toolbar(self):
        """Sets up the main menus and toolbar for the main window."""
        menubar = self.main_window.menuBar()

        create_file_menu(self.main_window, menubar)
        create_edit_menu(self.main_window, menubar)
        create_view_menu(self.main_window, menubar)
        create_ai_tools_menu(self.main_window, menubar)
        # create_web_menu(self.main_window, menubar) # If web menu is needed later
        create_context_menu_actions() # Corrected: Call with no arguments

        toolbar = QToolBar("Main Toolbar")
        toolbar.setObjectName("MainToolbar")

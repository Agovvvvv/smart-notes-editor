from PyQt5.QtWidgets import QAction, QToolBar
from PyQt5.QtGui import QIcon

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
    """Creates and returns the AI Tools menu. Sets actions on main_window."""
    ai_menu = menubar.addMenu("&AI Tools")
    
    main_window.summarize_action = QAction(QIcon.fromTheme("edit-paste"), "&Summarize Note", main_window)
    main_window.summarize_action.setStatusTip("Generate a summary of the current note using AI")
    main_window.summarize_action.triggered.connect(main_window.on_summarize_note)
    ai_menu.addAction(main_window.summarize_action)

    main_window.generate_note_action = QAction(QIcon.fromTheme("document-new"), "&Generate Note...", main_window)
    main_window.generate_note_action.setStatusTip("Generate new note content based on a prompt using AI")
    main_window.generate_note_action.triggered.connect(main_window.on_generate_note_text)
    ai_menu.addAction(main_window.generate_note_action)

    main_window.enhance_note_action = QAction(QIcon.fromTheme("system-run"), "&Enhance Note", main_window)
    main_window.enhance_note_action.setStatusTip("Analyze the current note, fetch relevant web info, and suggest enhancements")
    main_window.enhance_note_action.triggered.connect(main_window.on_trigger_full_enhancement_pipeline)
    ai_menu.addAction(main_window.enhance_note_action)

    ai_menu.addSeparator()
    main_window.configure_ai_services_action = QAction(QIcon.fromTheme("preferences-system"), "&Configure AI Services...", main_window)
    main_window.configure_ai_services_action.setStatusTip("Configure AI model and API settings")
    main_window.configure_ai_services_action.triggered.connect(main_window._configure_ai_services)
    ai_menu.addAction(main_window.configure_ai_services_action)
    
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

def create_web_menu(main_window, menubar):
    """Creates and returns the Web menu."""
    web_menu = menubar.addMenu("&Web")
    
    search_web_action = QAction("&Search Web", main_window)
    search_web_action.setShortcut("Ctrl+Alt+W")
    search_web_action.setStatusTip("Search the web for information related to your note")
    search_web_action.triggered.connect(main_window.on_search_web)
    web_menu.addAction(search_web_action)
    
    search_selected_action = QAction("Search &Selected Text", main_window)
    search_selected_action.setShortcut("Ctrl+Alt+F")
    search_selected_action.setStatusTip("Search the web for the selected text")
    search_selected_action.triggered.connect(main_window.on_search_selected)
    web_menu.addAction(search_selected_action)
    
    return web_menu

def create_context_menu_actions(main_window, menubar):
    """Creates and returns the Context menu (for menubar)."""
    context_menu = menubar.addMenu("&Context")
    
    analyze_context_action = QAction("&Analyze Context", main_window)
    analyze_context_action.setStatusTip("Analyze note and web content to generate contextual suggestions")
    analyze_context_action.triggered.connect(main_window.on_analyze_context)
    context_menu.addAction(analyze_context_action)
    
    show_suggestions_action = QAction("Show &Suggestions", main_window)
    show_suggestions_action.setStatusTip("Show contextual suggestions based on previous analysis")
    show_suggestions_action.triggered.connect(main_window.on_show_suggestions)
    context_menu.addAction(show_suggestions_action)
    
    context_menu.addSeparator()
    auto_enhance_action = QAction("Auto-&Enhance Notes", main_window)
    auto_enhance_action.setStatusTip("Automatically enhance notes with AI-generated content")
    auto_enhance_action.triggered.connect(main_window.on_auto_enhance)
    context_menu.addAction(auto_enhance_action)
    
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
    
    toolbar.addSeparator()
    
    # Use the existing summarize_action from main_window if it's defined by create_ai_tools_menu
    # It's generally better to create a distinct action for the toolbar if icons/text differ,
    # or reuse if they are identical and main_window.summarize_action is reliably set beforehand.
    # For clarity and independence, creating a new one here:
    summarize_tb_action = QAction(QIcon.fromTheme("edit-paste"), "Summarize", main_window)
    summarize_tb_action.setStatusTip("Summarize the current note using AI")
    summarize_tb_action.triggered.connect(main_window.on_summarize_note)
    toolbar.addAction(summarize_tb_action)

    search_tb_action = QAction(QIcon.fromTheme("system-search"), "Web Search", main_window)
    search_tb_action.setStatusTip("Search the web for information related to the note")
    search_tb_action.triggered.connect(main_window.on_search_web)
    toolbar.addAction(search_tb_action)

    toolbar.addSeparator()

    enhance_tb_action = QAction(QIcon.fromTheme("system-run"), "Enhance Note", main_window) # Consider a more specific icon
    enhance_tb_action.setStatusTip("Automatically enhance note with AI-generated content")
    enhance_tb_action.triggered.connect(main_window.on_auto_enhance) # Changed from on_trigger_full_enhancement_pipeline to on_auto_enhance based on original main_window.py toolbar
    toolbar.addAction(enhance_tb_action)

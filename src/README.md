# Project Source Code (`src/`) Overview

The  `src/` directory contains all the core Python source code for your Smart Contextual Notes Editor application. It's structured into subdirectories to separate different concerns, making the project more organized, maintainable, and testable.

## Directory Structure (`src/`)

```text
src/
├── __init__.py           # Makes src/ a Python package
├── main.py              # The main entry point of the application
├── ui/                  # UI-related files
│   ├── __init__.py      # Makes ui/ a Python package
│   ├── main_window.py    # Code for the main application window
│   └── ui_design.py     # (Optional) Code generated from .ui files if using Qt Designer
├── backend/             # Core application logic (non-UI)
│   ├── __init__.py      # Makes backend/ a Python package
│   ├── editor_logic.py  # Logic for file handling, text manipulation
│   └── ai_utils.py      # AI and NLP related functions (summarization, context analysis)
├── web/                 # Web interaction logic
│   ├── __init__.py      # Makes web/ a Python package
│   └── scraper.py       # Functions for web searching and scraping
└── utils/               # Generic utility functions (e.g., settings handling, threading helpers)
    ├── __init__.py      # Makes utils/ a Python package
    ├── settings.py      # Code for loading/saving application settings
    └── threads.py       # Worker classes and signals for background operations
```

## File Breakdown and Details

### src/__init__.py
**Purpose:** Empty file that marks src directory as a Python package, enabling imports like `from src.ui.main_window import MainWindow`.  
**Details:** Usually left empty.

### src/main.py
**Purpose:** Main entry point that initializes the application.  
**Details:**
- Imports necessary UI classes
- Initializes single QApplication instance
- Creates and shows main window
- Starts application event loop (app.exec_())
- Typically includes `if __name__ == "__main__":` block
- May load stylesheets or initialize backend components at startup

### src/ui/
**Purpose:** Contains all UI-related code.  
**Details:** Separates UI from application logic for cleaner code and easier maintenance.

### src/ui/__init__.py
**Purpose:** Makes ui directory a Python package.  
**Details:** Usually left empty.

### src/ui/main_window.py
**Purpose:** Defines the main application window.  
**Details:**
- Inherits from QMainWindow
- Sets up window properties, widgets, and layouts
- Creates menus, toolbars, and status bars
- Implements slots for user actions:
  - File operations (new_note, open_note, save_note)
  - AI features (on_summarize_note, on_find_related_info)
  - Context menu handling
  - Thread result handling
- Acts as central coordinator between UI and backend
- **Security/Robustness:**
  - Validates input before passing to backend
  - Displays user-friendly error messages
  - Handles exceptions gracefully
  - Carefully manages content from external sources

### src/ui/ui_design.py (Optional)
**Purpose:** Generated code from Qt Designer .ui files.  
**Details:**
- Automatically generated, not manually edited
- Defines UI layout and widgets
- Useful for complex UIs but adds a build step

### src/backend/
**Purpose:** Contains core application logic separate from UI.  
**Details:** Logic should be testable without requiring the GUI.

### src/backend/__init__.py
**Purpose:** Makes backend directory a Python package.  
**Details:** Usually left empty.

### src/backend/editor_logic.py
**Purpose:** Handles note operations and text transformations.  
**Details:**
- **save_text_to_file(text, filepath):**
  - Uses built-in file handling with proper encoding
  - Implements error handling for IO issues
  - Validates filepath security
- **load_text_from_file(filepath):**
  - Reads files with proper encoding
  - Handles potential encoding errors
  - Implements comprehensive error handling
- Optional text processing functions

### src/backend/ai_utils.py
**Purpose:** Contains AI and NLP functionality.  
**Details:**
- **initialize_ai_models():** Loads models efficiently
- **generate_summary(text):** Processes text and returns summary
- **analyze_context(note_text, web_results):** Finds relevant information
- Helper NLP functions for tokenization, entity extraction, etc.
- **Security/Robustness:**
  - Secures API keys (no hardcoding)
  - Validates inputs
  - Implements error handling for AI operations

### src/web/
**Purpose:** Manages web interactions.  
**Details:** Designed to handle network issues and website variations.

### src/web/__init__.py
**Purpose:** Makes web directory a Python package.  
**Details:** Can define custom web-related exceptions.

### src/web/scraper.py
**Purpose:** Handles web requests and HTML parsing.  
**Details:**
- **search_web(query):** Executes web searches
  - Handles network errors and retries
  - **Security/Ethics:**
    - Respects robots.txt
    - Uses custom User-Agent
    - Implements request delays
    - Manages API security if applicable
- **scrape_page_content(url):** Fetches and extracts content
  - Handles network and parsing errors
  - Removes boilerplate content
  - Sanitizes retrieved content

### src/utils/
**Purpose:** Provides general utility functions.  
**Details:** Contains independent functions and helper classes.

### src/utils/__init__.py
**Purpose:** Makes utils directory a Python package.  
**Details:** Can expose key utility functions directly.

### src/utils/settings.py
**Purpose:** Manages application settings.  
**Details:**
- Functions for loading/saving settings
- Uses configparser or json format
- **Security:**
  - Handles sensitive information carefully
  - Uses environment variables for API keys
  - Implements error handling

### src/utils/threads.py
**Purpose:** Manages background operations to keep UI responsive.  
**Details:**
- Defines worker classes (SummarizationWorker, WebScrapingWorker, etc.)
- Implements run() method for blocking operations
- Uses signals to communicate results back to UI
- Includes robust error handling to prevent crashes
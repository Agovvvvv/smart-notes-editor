# Smart Contextual Notes Editor

**Project Goal:** A modern text editor that can summarize notes and enrich them with web-sourced information using AI.

## Features

- **Modern UI**: Clean, intuitive interface with dark theme support
- **Basic Text Editing**: Create, open, edit, and save text files
- **File Management**: Supports .txt and .md file formats
- **AI Summarization**: Summarize your notes with AI using transformer models
- **Web Information Enrichment**: Find relevant information from the web to enhance your notes
- **Context-Aware Suggestions**: (Coming soon) Get intelligent suggestions based on your notes

## Technology Stack

- **Frontend (UI)**: PyQt5
- **Backend (Logic & AI)**: Python
- **AI/NLP**: Hugging Face Transformers
- **Web Scraping**: Requests, Beautiful Soup
- **Data Storage**: Simple file I/O (.txt, .md)
- **Concurrency**: Python threading

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd gestore_appunti
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Activate the virtual environment (if not already activated)

2. Run the application:
   ```bash
   python src/main.py
   ```

3. Use the menu options to create, open, and save notes

## Project Structure

```
gestore_appunti/
├── venv/                    # Virtual environment
├── src/                     # Source code
│   ├── __init__.py          # Makes src/ a Python package
│   ├── main.py              # Application entry point
│   ├── ui/                  # UI-related files
│   │   ├── __init__.py      # Makes ui/ a Python package
│   │   ├── main/            # Main window components
│   │   │   ├── __init__.py  # Makes main/ a Python package
│   │   │   └── main_window.py # Main application window
│   │   ├── panels/          # UI panels
│   │   │   ├── __init__.py  # Makes panels/ a Python package
│   │   │   ├── summary_panel.py # Summary display panel
│   │   │   ├── web_panel.py # Web results panel
│   │   │   └── suggestions_panel.py # Contextual suggestions panel
│   │   ├── dialogs/         # Dialog windows
│   │   │   ├── __init__.py  # Makes dialogs/ a Python package
│   │   │   ├── model_dialog.py # Model selection dialog
│   │   │   └── auto_enhance_dialog.py # Auto-enhancement dialog
│   │   └── managers/        # UI managers
│   │       ├── __init__.py  # Makes managers/ a Python package
│   │       ├── ai_manager.py # AI operations manager
│   │       ├── web_search_manager.py # Web search manager
│   │       └── context_manager.py # Context analysis manager
│   ├── backend/             # Core application logic
│   │   ├── __init__.py      # Makes backend/ a Python package
│   │   ├── editor_logic.py  # File handling, text manipulation
│   │   ├── ai_utils.py      # AI summarization functions
│   │   └── context_analyzer.py # Context analysis functions
│   ├── web/                 # Web interaction logic
│   │   ├── __init__.py      # Makes web/ a Python package
│   │   └── scraper.py       # Web search and scraping functions
│   └── utils/               # Utility functions
│       ├── __init__.py      # Makes utils/ a Python package
│       ├── settings.py      # Application settings
│       └── threads.py       # Threading utilities
├── data/                    # Directory for saved notes
├── styles/                  # QSS stylesheets
│   └── dark_theme.qss       # Dark theme stylesheet
├── tests/                   # Unit tests
│   ├── __init__.py          # Makes tests/ a Python package
│   ├── test_editor_logic.py # Tests for editor logic
│   └── test_context_analyzer.py # Tests for context analyzer
├── .gitignore               # Git ignore file
├── requirements.txt         # Project dependencies
└── README.md                # This file
```

## Development Roadmap

### Phase 1: Foundation (Current)
- ✅ Basic text editor with modern UI
- ✅ File operations (create, open, save)
- ✅ Settings management
- ✅ Dark theme

### Phase 2: AI Summarization (Completed)
- ✅ Integrate AI for text summarization
- ✅ Threading for responsive UI during AI operations
- ✅ Summary display panel
- ✅ Model selection dialog

### Phase 3: Web Information Retrieval (Completed)
- ✅ Web search functionality
- ✅ Content extraction from web pages
- ✅ Display of retrieved information
- ✅ Integration with notes via link insertion

### Phase 4: Context Enhancement
- 🔄 AI analysis of notes and web content
- 🔄 Contextual suggestions
- 🔄 Integration of suggestions into notes

### Phase 5: Polish and Refinement
- 🔄 UI/UX improvements
- 🔄 Performance optimization
- 🔄 Comprehensive testing
- 🔄 Documentation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.





## Phase 1: Foundation (Weeks 1-2)

**Objective:** Set up the project environment and build a basic, functional text editor.

**Detailed Steps:**

1.  **Project & Environment Setup:**
    *   Create a new directory for your project (e.g., `smart_notes_editor`).
    *   Set up a virtual environment to manage dependencies:
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows use `venv\Scripts\activate`
        ```
    *   Install initial required libraries:
        ```bash
        pip install PyQt5  # Or PySide6
        pip install transformers
        pip install requests
        pip install beautifulsoup4
        pip install openai  # Install if you plan to use OpenAI
        pip install nltk spaCy  # Install early if you plan on basic NLP
        ```
    *   Initialize a Git repository for version control:
        ```bash
        git init
        git add .
        git commit -m "Initial project setup"
        ```
    *   Create basic project directories: `src` (for main code), `ui` (for UI definition or files), `data` (for saved notes), `utils` (for helper functions).
    *   Create an initial main script (e.g., `src/main.py`).

2.  **Basic Text Editor UI:**
    *   Import necessary modules from your chosen GUI library (e.g., `from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QMenuBar, QAction, QFileDialog, QStatusBar`).
    *   Create the main application class inheriting from `QMainWindow`.
    *   Initialize the main window (`__init__` method): set window title, geometry, etc.
    *   Create a central `QTextEdit` widget as the main text area. Set it as the central widget of the main window.
    *   Add a menu bar (`QMenuBar`) and a status bar (`QStatusBar`) and set them in the main window.
    *   Add a "File" menu (`QMenu`) to the menu bar.
    *   Add "New," "Open," and "Save" actions (`QAction`) to the "File" menu. Set appropriate text and potentially shortcuts.
    *   Connect file actions to placeholder methods (e.g., `self.new_note`, `self.open_note`, `self.save_note`).
    *   Create and run the application instance within the `if __name__ == "__main__":` block.

3.  **Basic File Handling:**
    *   Implement the `new_note` method: Clear the text area (`self.text_edit.clear()`). Update the window title to indicate an unsaved file.
    *   Implement the `open_note` method:
        *   Use `QFileDialog.getOpenFileName` to allow the user to select a file, filtering by desired file types (e.g., "*.txt").
        *   If a file is selected, open it in read mode (`'r'`) with appropriate encoding (e.g., `'utf-8'`).
        *   Read the entire file content.
        *   Set the text area content (`self.text_edit.setText(content)`).
        *   Update the window title to show the opened file name.
        *   Include basic `try...except` blocks for handling `FileNotFoundError` or `IOError`.
    *   Implement the `save_note` method:
        *   Use `QFileDialog.getSaveFileName` to allow the user to choose a save path, suggesting a default file name and filtering.
        *   If a path is selected, open the file in write mode (`'w'`) with `'utf-8'` encoding.
        *   Get the text content from the text area (`self.text_edit.toPlainText()`).
        *   Write the content to the file.
        *   Update the window title to show the saved file name.
        *   Include `try...except` blocks for handling `IOError`. Store the current file path internally.

4.  **Basic Text Editing Features:**
    *   Verify that standard keyboard shortcuts for Cut (Ctrl+X), Copy (Ctrl+C), and Paste (Ctrl+V) work in the `QTextEdit`. These are typically handled automatically.
    *   (Optional) Add an "Edit" menu with "Cut," "Copy," "Paste," "Undo," and "Redo" actions, connecting them to the `QTextEdit`'s built-in slots (`cut()`, `copy()`, `paste()`, `undo()`, `redo()`).

**Milestone:** A functional text editor that can create, save, and load plain text files. You can type, cut, copy, and paste text, and monitor saving/loading in the status bar.

---

## Phase 2: Integrating AI for Summarization (Weeks 3-4)

**Objective:** Add the ability to summarize the current note using an AI model.

**Detailed Steps:**

1.  **Choose and Implement Summarization Library/API:**
    *   **Option A (Hugging Face - Recommended for local execution):**
        *   In your backend logic (or create a new `ai_utils.py` file), import: `from transformers import pipeline`.
        *   Load a summarization pipeline: `summarizer = pipeline("summarization", model="bart-large-cnn")`. Research other suitable models if needed. Loading can take time, so do this once at application startup or lazily on the first call.
        *   Write a function `generate_summary(text)` that takes text and returns `summarizer(text)[0]['summary_text']`.
    *   **Option B (External API - e.g., OpenAI):**
        *   Install the API client library (`pip install openai`).
        *   Obtain an API key (requires an account and potentially payment).
        *   Write a function `generate_summary_api(text, api_key)` that calls the API (e.g., `openai.Completion.create(...)` or the newer Chat Completions API) with a prompt asking for a summary. Handle API key management securely (don't hardcode).

2.  **Integrate Summarization into the UI:**
    *   Add a new menu called "AI" to your `QMenuBar`.
    *   Add a "Summarize Note" action (`QAction`) to the "AI" menu.
    *   Connect this action to a new method in your main window class, e.g., `self.on_summarize_note`.

3.  **Implement the Summarization Logic & Display:**
    *   In the `on_summarize_note` method:
        *   Get the current text from the `QTextEdit`: `text = self.text_edit.toPlainText()`.
        *   **Input Validation:** Check if `text` is empty or too short. Display a message box if necessary.
        *   **Handle Long Text:** Summarization models have input length limits. For longer texts, implement chunking (splitting the text into smaller parts) and summarize each chunk, or use a model designed for longer inputs if available.
        *   **Concurrency:** Since summarization can block the UI, run the `generate_summary` (or API call) in a separate thread. PyQt/PySide use `QThread` or you can use Python's `threading` combined with emitting signals to update the UI from the worker thread.
        *   **UI Feedback:** Update the status bar or show a temporary dialog ("Generating summary...") while processing.
        *   **Call Backend:** In the worker thread, call your `generate_summary` function.
    *   **Display the Summary:**
        *   When the worker thread finishes (it should emit a signal with the result):
        *   Create a suitable UI element to display the summary. Options:
            *   A non-editable `QTextEdit` or `QTextBrowser` in a resizable side panel (using `QSplitter`).
            *   A a `QMessageBox` (simple, but less flexible).
            *   A dedicated new window (e.g., inheriting from `QDialog` or `QMainWindow`). Add buttons to copy the summary.
        *   Populate the chosen display element with the returned summary text.
        *   Handle potential errors from the summarization function/API and display an error message.

**Milestone:** The editor has an "AI" menu with a "Summarize Note" option. Clicking it triggers a summarization process (potentially in a separate thread), and the resulting summary is displayed to the user in a dedicated UI element.

---

## Phase 3: Web-Based Information Retrieval (Weeks 5-6)

**Objective:** Implement the ability to fetch potentially relevant information from the web based on the note's content.

**Detailed Steps:**

1.  **Plan Information Retrieval Strategy:**
    *   **Trigger:**
        *   Add an action in the "AI" menu, perhaps "Find Related Info".
        *   Allow the user to select text in the editor and right-click to bring up a context menu with a "Search Web for Selection" option.
    *   **Search Method:**
        *   **Option A (Basic Search & Scrape ):** Perform a search on a privacy-friendly search engine (e.g., DuckDuckGo) by constructing a search URL. Use `requests` to fetch the search results page HTML. Use `beautifulsoup4` to parse the HTML and extract the URLs of the top search results. Then, fetch and scrape the content of a few of the promising linked pages. *Be cautious with this method due to website changes and terms of service.*
        *   **Option B (Search API - More Robust but potentially costly/limited):** Use a dedicated search API (e.g., SerpApi, a paid service; Google Custom Search Engine with API; Microsoft Bing Search API). This provides structured JSON results directly, making parsing easier. Implement API key handling.
    *   **Query Generation:** If triggering from the whole note, how will you generate the search query? Extract keywords or the title? If triggering from a selection, use the selected text as the query.
    *   **What to Extract from Pages:** Decide what kind of content you're looking for on retrieved pages (e.g., main body text, headings, specific factual data points). Focus on extracting clean text content.

2.  **Implement Web Search/Scraping Backend:**
    *   Create functions in your backend logic (e.g., `web_utils.py`).
    *   Write a function `search_web(query)` that executes the search based on your chosen method (API call or scraping search results). Return a list of relevant URLs and titles.
    *   Write a function `scrape_page_content(url)` that fetches a given URL and extracts the main text content using `beautifulsoup4`. Focus on common page structures (e.g., `<article>`, `<p>` tags within main content areas). Implement basic boilerplate removal (headers, footers, navigation).
    *   Handle potential network errors (`requests.exceptions.RequestException`), HTTP errors (404, 500), and parsing errors. Implement retries for transient errors.
    *   Set a User-Agent header in your requests to identify your scraper (e.g., `headers = {'User-Agent': 'MySmartNotesEditor/1.0 (University Project)'}`).
    *   (Optional but good practice) Check `robots.txt` before scraping.

3.  **Integrate Web Retrieval into the UI:**
    *   Add an action "Find Related Info" to the "AI" or a new "Web" menu and connect it to `self.on_find_related_info`.
    *   (Optional) For selection-based search, implement a context menu for the `QTextEdit`. Connect the `customContextMenuRequested` signal to a slot that builds and shows a context menu based on the current selection. Add a "Search Web for Selected Text" action to this menu.

4.  **Implement Retrieval Logic & Display:**
    *   In the `on_find_related_info` method:
        *   Determine the search query (e.g., get selected text, or generate from note content).
        *   **Concurrency:** Run the web search and scraping process in a separate thread to keep the UI responsive.
        *   **UI Feedback:** Update the status bar ("Searching the web...") and show results as they come in if possible.
        *   Call your backend `search_web` function.
        *   For each found URL, call your `scrape_page_content` function (potentially in parallel across a few URLs, using a `ThreadPoolExecutor`).
    *   **Display Retrieved Information:**
        *   When the worker thread finishes (emitting a signal with results):
        *   Create a side panel (`QSplitter`) or a new window (`QDialog` or `QMainWindow`) to display the results.
        *   Use a widget that can display rich text and links, like a `QTextBrowser`.
        *   Present the results clearly: list the source URLs and titles, and display the extracted text content below each source. Hyperlink the titles to the original URLs.
        *   Include error messages for sources that failed to load or parse.

**Milestone:** The editor can take a query (from selection or note analysis), perform a web search, retrieve content from potentially relevant pages, and display the raw or partially processed web content in a separate UI area.

---

## Phase 4: Enhancing Notes with AI and Context (Weeks 7-8)

**Objective:** Use AI to analyze the retrieved web information, compare it to the notes, and suggest relevant additions or contextual information. This is the core AI component.

**Detailed Steps:**

1.  **Choose and Implement AI Analysis Techniques:**
    *   Create or modify your AI utility functions (e.g., in `ai_utils.py`).
    *   Implement one or more of the following:
        *   **Keyword/Entity Extraction & Matching:**
            *   Use NLTK or spaCy (`pip install spacy`, `python -m spacy download en_core_web_sm`) to extract keywords and Named Entities (people, organizations, locations, etc.) from both the user's note and the scraped web text.
            *   Compare the extracted entities/keywords. Find web passages that contain entities or keywords present in the note. Prioritize matches.
        *   **Semantic Similarity:**
            *   Install a sentence embedding library (e.g., `pip install sentence-transformers`).
            *   Load a pre-trained sentence embedding model (e.g., `from sentence_transformers import SentenceTransformer; model = SentenceTransformer('all-MiniLM-L6-v2')`).
            *   Split the user's note and the scraped web content into sentences.
            *   Generate embeddings for all sentences.
            *   Calculate the cosine similarity between embeddings of sentences from the note and sentences from the web.
            *   Identify web sentences with high similarity to sentences in the note.
        *   **Topic Modeling:** (More complex)
            *   Use libraries like `gensim` or scikit-learn's `LatentDirichletAllocation`.
            *   Preprocess text (tokenization, stop word removal, stemming/lemmatization).
            *   Train a topic model on a combined corpus of your note and retrieved web content.
            *   Analyze which topics are prominent in your note and find web passages that strongly relate to those topics.

    *   Your AI analysis function should take the user's note text and the list of scraped web content (text + source URL) as input.
    *   It should return a structured result: a list of suggested snippets from the web content, each associated with its original source URL and potentially a relevance score.

2.  **Integrate AI Suggestions into the UI:**
    *   Modify the UI panel where you display retrieved web results to incorporate suggestions.
    *   Design how suggestions will be presented:
        *   A separate section within the results panel titled "Suggested Additions."
        *   Highlighting within the displayed web content that corresponds to suggestions.
        *   Linking suggested snippets directly back to the part of the note they are relevant to (more advanced).
    *   Ensure each suggestion clearly shows its original source (URL).

3.  **Implement Suggestion Workflow:**
    *   Modify your `on_find_related_info` logic. After scraping the web content, pass both the note text and the list of scraped content to your AI analysis function (again, preferably in the background thread).
    *   Receive the AI's analysis results (list of suggestions).
    *   Update the UI panel to display these highlighted suggestions in a user-friendly way.
    *   Add functionality for the user to interact with suggestions:
        *   A button next to each suggestion to "Insert" it into the user's note.
        *   A button to "Copy" the suggestion text.
        *   Clickable links to view the original source URL in a web browser.
        *   If inserting, define where it should be inserted (e.g., at the cursor position, at the end of the note).

**Milestone:** The editor performs AI analysis on retrieved web content in relation to the note's content. It displays a list of specific "suggested" text snippets from the web, relevant to the user's note, with options to insert them.

---

## Phase 5: Polish and Refinement (Weeks 9-10)

**Objective:** Improve the user experience, optimize performance, test thoroughly, and finalize for presentation.

**Detailed Steps:**

1.  **Improve UI/UX:**
    *   **Modern Styling (QSS):** Create a `.qss` file and apply CSS-like styling to your widgets to achieve a modern look. Refer to PyQt/PySide documentation for QSS syntax.
    *   **Icons:** Find or create icons for menu actions and toolbar buttons. Add a toolbar (`QToolBar`) for frequently used actions (New, Open, Save, Summarize, Find Info).
    *   **Status Bar Enhancements:** Use the status bar to show progress for longer operations (e.g., "Summarizing... 50% complete," "Scraping page 3 of 5").
    *   **Preferences/Settings:** Add a menu option "Settings" or "Preferences." Create a `QDialog` with options (e.g., font size, default save directory, choice of summarization model if you implemented multiple, API keys). Save and load settings using Python's `configparser` or `json`.
    *   **Improved Error Handling UI:** Instead of just printing errors to the console, display user-friendly error messages using `QMessageBox.critical()` or in the status bar.
    *   **Responsiveness:** Ensure the side panel for results and suggestions is resizable and that the main text editor adjusts correctly when the window is resized.

2.  **Optimize Performance:**
    *   **Concurrency Maturity:** Refine your threading implementation. Ensure threads are managed correctly, signals are emitted safely to update the UI, and threads are properly shut down when the application closes. Consider using `QThreadPool` for managing multiple worker threads.
    *   **Model Loading:** Explicitly load larger AI models only once when needed. For summarization, load the pipeline on application startup.
    *   **Caching:** Cache web scraping results for a short period to avoid redundant requests if the user triggers search multiple times for similar queries.
    *   **Efficient Text Processing:** For very large notes or web content, optimize text processing steps (NLP, similarity calculations) for efficiency. Consider using libraries like Numba or Cython if performance is a critical issue (though likely not necessary for this project scope).

3.  **Testing and Bug Fixing:**
    *   **Functional Testing:** Test every menu option, button, and text editing feature.
    *   Test saving and loading various file types (if supported) and with different encodings.
    *   Test summarization with short, medium, and long texts. Test edge cases (empty text, text with only numbers or symbols).
    *   Test web search and scraping with various queries. Test URLs that might be problematic (e.g., requiring login, complex JavaScript rendering - though avoid complex scraping for this project). Test how it handles network errors and missing content.
    *   Test the AI suggestion feature. Does it find relevant information? Does it handle cases where no relevant info is found gracefully? Are the suggestions placed/displayed correctly?
    *   **UI Testing:** Test on different operating systems (if possible). Check that the UI looks correct and is responsive to resizing.

4.  **Documentation and Presentation Preparation:**
    *   **Code Documentation:** Ensure all classes, methods, and functions have clear docstrings explaining their purpose, arguments, and return values.
    *   **Project README:** Update your `README.md`. Provide clear instructions on how to install dependencies, run the application, and use its main features. Explain the AI functionalities.
    *   **University Report/Presentation:**
        *   Structure your presentation logically: Introduction (Problem & Goal), Design (Architecture, Technologies), Implementation (Key Features, UI, Backend, AI Techniques), Challenges and Solutions, Demo, Future Work, Conclusion.
        *   Prepare clear slides and diagrams (e.g., a simple class diagram, a workflow diagram showing how data/control flows when you summarize or search).
        *   Focus on explaining the *AI* aspects: how summarization works at a high level, and specifically how your chosen method for context enrichment (e.g., semantic similarity, entity matching) works and why it's suitable.
        *   Prepare a compelling live demo showcasing the core features, especially summarization and finding relevant web info.
        *   Discuss the limitations of your AI approach and potential areas for improvement (e.g., handling ambiguity, deeper understanding of text, integrating more diverse knowledge sources).

**Milestone:** A well-tested, polished application with a user-friendly UI, comprehensive code documentation, a polished README file, and materials prepared for your university submission. The project is stable and showcases the core AI features effectively.

---

This plan outlines the key stages and steps. Remember that software development is iterative. You may need to revisit earlier phases as you progress. Good luck with your university project!

# Quantum Computing Basics

Quantum computing is an emerging field that uses quantum mechanics to process information. Unlike classical computers that use bits (0s and 1s), quantum computers use quantum bits or "qubits" that can exist in multiple states simultaneously due to superposition.

Some key concepts in quantum computing include:
- Superposition: Qubits can represent multiple states at once
- Entanglement: Qubits can be correlated in ways that have no classical equivalent
- Quantum gates: Operations that manipulate qubits

Current challenges include maintaining quantum coherence and scaling up the number of qubits. Companies like IBM and Google are racing to build practical quantum computers.

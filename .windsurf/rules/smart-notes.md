---
trigger: always_on
---

# Project Rules for Smart Contextual Notes Editor

This document outlines key guidelines and context for the "Smart Contextual Notes Editor" project. Adhering to these rules will help maintain consistency and align with the project's objectives.

## 1. Project Goal & Core Features

*   **Primary Goal:** Develop a modern text editor that can summarize notes and enrich them with web-sourced information using AI.
*   **Core Features:**
    *   Modern UI (PyQt5) with dark theme support.
    *   Basic text editing: Create, open, edit, save (.txt, .md).
    *   AI Summarization: Utilize Hugging Face Transformers for note summarization.
    *   Web Information Enrichment: Fetch and display relevant information from the web (using Requests, Beautiful Soup).
    *   Context-Aware Suggestions (Future Goal): Provide intelligent suggestions based on note content.

## 2. Technology Stack

*   **Frontend (UI):** PyQt5
*   **Backend (Logic & AI):** Python
*   **AI/NLP:** Hugging Face Transformers (primarily for summarization).
*   **Web Scraping/Requests:** `requests` library for HTTP calls, `Beautiful Soup` for HTML parsing.
*   **Data Storage:** Simple file I/O for notes (.txt, .md).
*   **Concurrency:** Python threading for background tasks (AI processing, web requests) to keep the UI responsive.
*   **Settings Management:** `configparser` or `json` for application settings.

## 3. Project Structure & Key Files

*   **Main Source Directory:** `src/`
*   **Entry Point:** `src/main.py` (initializes QApplication, main window).
*   **UI Logic:**
    *   Directory: `src/ui/`
    *   Main Window: `src/ui/main_window.py` (inherits QMainWindow, coordinates UI and backend).
    *   (Optional) UI Design: `src/ui/ui_design.py` if Qt Designer is used.
*   **Backend Logic:**
    *   Directory: `src/backend/`
    *   Editor Logic: `src/backend/editor_logic.py` (file operations, text manipulation).
    *   AI Utilities: `src/backend/ai_utils.py` (summarization, context analysis, model initialization).
*   **Web Interaction Logic:**
    *   Directory: `src/web/`
    *   Scraper: `src/web/scraper.py` (web searching, page content scraping).
        *   **Ethical Scraping:** Respect `robots.txt`, use a custom User-Agent, implement delays.
*   **Utility Functions:**
    *   Directory: `src/utils/`
    *   Settings: `src/utils/settings.py` (loading/saving application settings, secure API key handling).
    *   Threading: `src/utils/threads.py` (worker classes for background operations).
*   **Stylesheets:** `styles/` (e.g., `dark_theme.qss`).
*   **Dependencies:** `requirements.txt`.
*   **Saved Notes:** `data/` (default directory for user notes).

## 4. Development Principles & Best Practices

*   **Separation of Concerns:** Keep UI, backend logic, AI utilities, and web interaction code in their respective directories and modules.
*   **UI Responsiveness:** Perform long-running operations (AI tasks, web requests) in background threads (`QThread` or Python's `threading` with signals) to prevent UI freezes.
*   **Error Handling:** Implement robust error handling (e.g., network issues, file I/O errors, API errors) and provide user-friendly feedback.
*   **Security:**
    *   Handle API keys securely (e.g., environment variables, settings file not committed to VCS). Do NOT hardcode API keys.
    *   Validate user inputs.
    *   Sanitize web content before display or processing.
*   **Code Clarity & Maintainability:** Write clean, well-documented code. Use meaningful names for variables, functions, and classes.
*   **Modularity:** Design components to be as independent as possible.
*   **User Experience (UX):** Aim for an intuitive and clean interface. Provide feedback for ongoing operations.
*   **Testing:** (Future Goal) Implement unit tests for backend logic.

## 5. AI-Specific Guidelines

*   **Summarization:**
    *   Primarily use Hugging Face Transformers models (e.g., `bart-large-cnn` or similar).
    *   Handle input length limits of models (e.g., by chunking long texts if necessary).
    *   Load models efficiently (e.g., once at startup or lazily).
*   **Web Information Enrichment:**
    *   Focus on extracting meaningful content from web pages.
    *   Consider techniques like keyword/entity extraction (NLTK, spaCy) or semantic similarity (sentence-transformers) to find relevant information.
*   **Contextual Suggestions:**
    *   When developing this feature, the AI should analyze note content and retrieved web information to offer relevant snippets or links.

## 6. File Naming and Conventions

*   Follow Python PEP 8 guidelines.
*   Use descriptive names for files and modules (e.g., `ai_utils.py` is preferred over `ai.py`).
*   Ensure `__init__.py` files are present in subdirectories to mark them as packages.

By following these rules, the AI can better assist in developing and maintaining the Smart Contextual Notes Editor project.
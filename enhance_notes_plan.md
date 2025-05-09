# Plan: Enhance Notes Feature

## 1. Goal
Implement an "Enhance Notes" feature that analyzes the current note's content, searches the web for relevant information, extracts key details from the search results, and suggests these enriched insights (with sources) to the user.

## 2. Core Functionality
1.  **Contextual Analysis:** Extract keywords, topics, or named entities from the current note.
2.  **Web Search:** Use extracted terms to perform targeted web searches.
3.  **Information Extraction:** From the fetched web content, extract answers to implicit/explicit questions or generate summaries.
4.  **Suggestion Presentation:** Display the extracted information and their source URLs to the user.

## 3. Proposed Models (Hugging Face Pipelines)
*   **Named Entity Recognition (NER):** `dslim/bert-base-NER` for identifying key entities.
*   **Question Answering (QA):** `distilbert-base-cased-distilled-squad` for extracting specific answers from web content.
*   **Summarization:** `Falconsai/text_summarization` or `facebook/bart-large-cnn` for summarizing web page content.

## 4. Affected Modules & Files

*   **`src/controllers/ai_controller.py`**:
    *   Add new methods for NER, QA, and web content summarization.
    *   Integrate new worker threads for these tasks.
*   **`src/views/main_window.py`**:
    *   Add a new UI action (e.g., "Enhance Note" button/menu item).
    *   Implement the main handler `on_enhance_note()` to orchestrate the feature.
    *   Develop UI for displaying enhancement suggestions (e.g., a new dialog or panel).
*   **`src/utils/threads.py`**:
    *   Create new `QRunnable` worker classes for background NLP tasks (NER, QA, Web Content Summarization).
    *   Potentially an orchestrator worker for the entire enhancement flow.
*   **`src/views/dialogs/` (or `src/views/panels/`)**:
    *   New Python file for the suggestion display UI (e.g., `enhancement_suggestions_dialog.py`).
*   **`src/web/web_controller.py` (or `web_search_manager.py`)**:
    *   Ensure it can be used to fetch content from multiple URLs provided by the search.
*   **`config/settings.ini` & `src/models/settings_model.py` (Optional):**
    *   If model selection for enhancement tasks is desired, update settings.

## 5. Detailed Implementation Steps

### Step 5.1: AI Controller Enhancements (`ai_controller.py`)
1.  **Method for Entity Extraction:**
    *   `extract_entities(self, text)`:
        *   Uses `ner` pipeline.
        *   Signal: `entities_extracted(list_of_entities)`
2.  **Method for Question Answering:**
    *   `answer_question_from_context(self, question, context)`:
        *   Uses `question-answering` pipeline.
        *   Signal: `answer_found(answer_text, score)`
3.  **Method for Web Content Summarization:**
    *   `summarize_web_content(self, web_page_text)`:
        *   Uses `summarization` pipeline.
        *   Signal: `web_summary_ready(summary_text)`
4.  **Integrate Workers:**
    *   These methods will instantiate and run new worker threads from `threads.py`.

### Step 5.2: Worker Threads (`threads.py`)
1.  **`EntityExtractionWorker(QRunnable)`**:
    *   Input: text.
    *   Process: Runs NER pipeline.
    *   Output Signal: `result(entities_list)`, `error(str)`.
2.  **`QuestionAnsweringWorker(QRunnable)`**:
    *   Input: question, context.
    *   Process: Runs QA pipeline.
    *   Output Signal: `result(answer_dict)`, `error(str)`.
3.  **`WebContentSummarizationWorker(QRunnable)`**:
    *   Input: text.
    *   Process: Runs summarization pipeline.
    *   Output Signal: `result(summary_text)`, `error(str)`.
4.  **(Optional) `NoteEnhancementOrchestratorWorker(QRunnable)`**:
    *   Manages the sequential calls: NER -> Web Search -> Fetch Content -> QA/Summarize.
    *   Emits progress updates and final results.

### Step 5.3: MainWindow UI and Logic (`main_window.py`)
1.  **Add "Enhance Note" Action:**
    *   In a menu (e.g., "AI Tools" or "Context") and/or toolbar.
    *   Connect to `on_enhance_note()`.
2.  **Implement `on_enhance_note()`:**
    *   Get current note text from `text_edit`.
    *   If an orchestrator worker is used, trigger it.
    *   Otherwise, start the sequence:
        *   Call `ai_controller.extract_entities()`.
        *   **Handle `entities_extracted` signal:**
            *   Formulate search queries based on entities.
            *   Call `web_controller.perform_search()` (assuming it handles multiple queries or iterate).
        *   **Handle `web_search_result` (or similar from `WebController`):**
            *   For each relevant URL:
                *   Call `web_controller.fetch_content(url)`.
        *   **Handle `content_fetch_result`:**
            *   Pass fetched content to `ai_controller.answer_question_from_context()` (formulate questions based on note/entities) OR `ai_controller.summarize_web_content()`.
        *   **Handle `answer_found` / `web_summary_ready` signals:**
            *   Collect all suggestions (text, source URL).
            *   Once all processing is done, display suggestions using the new UI.
3.  **Connect to Worker Signals:** Connect to `error` signals from all AI workers for robust error display.

### Step 5.4: Suggestion Display UI
1.  **Create `EnhancementSuggestionsDialog` (or Panel):**
    *   Located in `src/views/dialogs/enhancement_suggestions_dialog.py`.
    *   Should display a list of suggestions. Each item shows:
        *   Extracted snippet/summary.
        *   Source URL (clickable if possible).
        *   Option to insert the snippet into the note.
2.  **`MainWindow` instantiates and shows this dialog** with the collected suggestions.

### Step 5.5: Error Handling and User Feedback
*   Implement `try-except` blocks for model loading and pipeline calls in workers.
*   Show informative error messages to the user via `QMessageBox` or status bar.
*   Provide progress updates (e.g., "Extracting entities...", "Searching web...", "Analyzing content...").

## 6. Future Considerations
*   Allow user to select which entities to search for.
*   More advanced relevance scoring for suggestions.
*   Caching of web content or extracted information.
*   Configuration for the number of search results to process.

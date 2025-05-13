8.  **Enhanced Contextual Awareness (Structure):**
    *   **Description:** Improve the AI's ability to understand the note's structure (headings, lists, paragraphs) when enhancing. For example, ensuring enhancements maintain list formatting or are relevant to the specific section they modify.
    *   **Implementation:**
        *   Prompt Engineering: Refine the default and custom prompts sent to the AI. Include explicit instructions like "Maintain the original markdown formatting (lists, headings)" or "Focus the enhancement on the content within the current section/paragraph".
        *   (Optional) Pre-processing: If simple prompt engineering isn't sufficient, implement logic to analyze the text structure (using regex or a simple parser) before sending it to the AI. This could involve adding lightweight structural markers or providing surrounding context (like the section heading) to the AI.

9.  **Cost/Token Usage Indicator (for APIs):**
    *   **Description:** When using API-based backends (Gemini, HF Inference), display an estimated token count *before* the user confirms the enhancement request. This provides transparency for potentially paid services.
    *   **Implementation:**
        *   Token Estimation: Implement a simple token counting function (e.g., based on word count or using a basic tokenizer if available) in `ai_utils.py` or `ai_controller.py`. Estimate input tokens for the text to be enhanced.
        *   Output Estimation: Base output estimation on the `max_output_tokens` setting, acknowledging it's an upper bound.
        *   UI Integration: Add labels to the dialog where enhancement is confirmed (e.g., `EnhancementPreviewDialog` or a preceding options dialog) to display "Estimated Input Tokens: X", "Max Output Tokens: Y".
        *   Focus: Prioritize showing token counts rather than monetary cost, as pricing can change. Optionally link to API pricing pages.
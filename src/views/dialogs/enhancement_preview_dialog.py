import logging
import difflib
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox,
    QSizePolicy, QLabel, QStackedWidget, QPushButton, QTextEdit,
    QHBoxLayout, QGroupBox 
)
from PyQt5.QtCore import Qt, pyqtSignal 

logger = logging.getLogger(__name__)

class EnhancementPreviewDialog(QDialog):
    """
    A dialog to display proposed AI note enhancements for user review,
    allowing for iterative refinement.
    """
    # Signal emitted when user requests regeneration with feedback
    # Args: original_text (str), current_enhanced_text (str), feedback (str)
    regenerate_requested = pyqtSignal(str, str, str)

    def __init__(self, enhanced_text, original_text="", estimated_input_tokens=None, max_output_tokens=None, parent=None):
        """
        Initialize the dialog.

        Args:
            enhanced_text (str): The initial AI-generated enhanced text.
            original_text (str): The original text for comparison and regeneration.
            estimated_input_tokens (int, optional): Estimated input tokens. Defaults to None.
            max_output_tokens (int, optional): Maximum output tokens. Defaults to None.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        logger.debug("EnhancementPreviewDialog.__init__ started.") # ADDED LOG
        self.setWindowTitle("Enhancement Preview - Enhanced Text")
        self._enhanced_text = enhanced_text
        self._original_text = original_text # Store original text
        self._estimated_input_tokens = estimated_input_tokens
        self._max_output_tokens = max_output_tokens

        layout = QVBoxLayout()

        # --- Create Stacked Widget for Preview ---
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # --- Page 0: Enhanced Text View ---
        self.enhanced_text_edit = QTextEdit()
        self.enhanced_text_edit.setPlainText(self._enhanced_text)
        self.enhanced_text_edit.setReadOnly(True) # Keep it read-only for preview
        self.stacked_widget.addWidget(self.enhanced_text_edit)

        # --- Page 1: Diff View ---
        self.diff_browser = QTextBrowser()
        self.diff_browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        logger.debug("Calling _generate_and_set_diff_html inside __init__.") # ADDED LOG
        self._generate_and_set_diff_html()
        logger.debug("Returned from _generate_and_set_diff_html inside __init__.") # ADDED LOG
        self.stacked_widget.addWidget(self.diff_browser)

        # --- Token Information Layout (conditionally displayed)
        self.token_info_layout = QHBoxLayout()
        self.input_tokens_label = QLabel("")
        self.output_tokens_label = QLabel("")
        self.token_info_layout.addWidget(self.input_tokens_label)
        self.token_info_layout.addStretch()
        self.token_info_layout.addWidget(self.output_tokens_label)
        
        if self._estimated_input_tokens is not None and self._max_output_tokens is not None:
            self.input_tokens_label.setText(f"Estimated Input Tokens: {self._estimated_input_tokens}")
            self.output_tokens_label.setText(f"Max Output Tokens: {self._max_output_tokens}")
        else:
            self.input_tokens_label.setVisible(False)
            self.output_tokens_label.setVisible(False)

        layout.addLayout(self.token_info_layout) # Add token info layout

        # --- Toggle Button ---
        self.toggle_button = QPushButton("Show Differences")
        self.toggle_button.clicked.connect(self._toggle_view)
        layout.addWidget(self.toggle_button)

        # --- Regeneration GroupBox ---
        self.regeneration_group = QGroupBox("Request Refinement")
        regeneration_layout = QVBoxLayout()

        self.feedback_label = QLabel("Provide feedback for regeneration (optional):")
        regeneration_layout.addWidget(self.feedback_label)

        self.feedback_input = QTextEdit()
        self.feedback_input.setPlaceholderText("e.g., 'Make it shorter', 'Focus more on topic X'...")
        self.feedback_input.setFixedHeight(60) # Make feedback box smaller
        regeneration_layout.addWidget(self.feedback_input)

        self.regenerate_button = QPushButton("Regenerate Enhancement")
        self.regenerate_button.clicked.connect(self._request_regeneration)
        regeneration_layout.addWidget(self.regenerate_button)

        self.regeneration_group.setLayout(regeneration_layout)
        layout.addWidget(self.regeneration_group)

        # --- Standard OK/Cancel Buttons ---
        # Use Accept/Reject roles for clarity
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText("Accept Current") # Clarify button text
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)
        self.stacked_widget.setCurrentIndex(0) # Start with enhanced text view
        self.resize(600, 500) # Adjust size if needed
        logger.debug("EnhancementPreviewDialog.__init__ finished.") # ADDED LOG

    def _generate_and_set_diff_html(self):
        """Generates the HTML diff table and sets it in the diff_browser."""
        logger.debug("_generate_and_set_diff_html started.") # ADDED LOG
        try:
            original_lines = self._original_text.splitlines()
            enhanced_lines = self._enhanced_text.splitlines()

            differ = difflib.HtmlDiff(wrapcolumn=80)
            # Keep the same style as before
            style = """
            <style>
                table.diff { font-family: Courier, monospace; border: medium; width: 100%; border-collapse: collapse; }
                .diff_header { background-color: #4a4a4a; color: #ffffff; font-weight: bold; } /* Darker grey header */
                td.diff_header { text-align: right; padding: 2px; }
                .diff_next { background-color: #555555; color: #cccccc; } /* Slightly lighter grey for context marker */
                /* Darker backgrounds with white text for changes */
                .diff_add { background-color: #1a4d2e; color: #ffffff; } /* Dark Green */
                .diff_chg { background-color: #b08c0f; color: #ffffff; } /* Dark Yellow/Orange */
                .diff_sub { background-color: #8b2323; color: #ffffff; } /* Dark Red */
                td { padding: 1px 3px; vertical-align: top; }
            </style>
            """
            diff_html = differ.make_table(
                original_lines,
                enhanced_lines,
                fromdesc='Original Text',
                todesc='Current Enhanced Text', # Updated label
                context=True,
                numlines=3
            )
            self.diff_browser.setHtml(style + diff_html)
            logger.debug("_generate_and_set_diff_html completed successfully.") # ADDED LOG
        except Exception as e:
            logger.error(f"Error generating diff HTML: {e}", exc_info=True) # Keep exc_info=True
            self.diff_browser.setPlainText(f"Error generating comparison view.\n\nEnhanced Text:\n{self._enhanced_text}")
            logger.debug("_generate_and_set_diff_html finished after catching exception.") # ADDED LOG

    def _toggle_view(self):
        """Switches between the enhanced text view and the diff view."""
        current_index = self.stacked_widget.currentIndex()
        if current_index == 0:
            self.stacked_widget.setCurrentIndex(1)
            self.toggle_button.setText("Show Enhanced Text")
            self.setWindowTitle("Enhancement Preview - Diff View")
        else:
            self.stacked_widget.setCurrentIndex(0)
            self.toggle_button.setText("Show Differences")
            self.setWindowTitle("Enhancement Preview - Enhanced Text")

    def _request_regeneration(self):
        """Emits the signal to request regeneration based on feedback."""
        feedback = self.feedback_input.toPlainText().strip()
        logger.info(f"Regeneration requested. Feedback: '{feedback[:50]}...'" )
        # Emit the signal with original text, *current* enhanced text, and feedback
        self.regenerate_requested.emit(self._original_text, self._enhanced_text, feedback)
        # Optionally disable button while waiting? Or provide visual cue?
        # For now, just emit. MainWindow will handle the AI call.

    def update_preview(self, new_enhanced_text: str):
        """Updates the dialog with a newly generated enhancement."""
        logger.info("Updating Enhancement Preview Dialog with new text.")
        self._enhanced_text = new_enhanced_text
        # Update the plain text view
        self.enhanced_text_edit.setPlainText(self._enhanced_text)
        # Regenerate and update the diff view
        self._generate_and_set_diff_html()
        # Clear the feedback input for the next round
        self.feedback_input.clear()
        # Optionally, switch back to the enhanced text view? Or stay on diff?
        # self.stacked_widget.setCurrentIndex(0) # Back to enhanced text
        # self.setWindowTitle("Enhancement Preview - Enhanced Text") # Reset title
        # self.toggle_button.setText("Show Differences") # Reset button

    def get_enhanced_text(self):
        """
        Returns the *currently displayed* enhanced text.
        Useful if the dialog is accepted ('Accept Current').
        """
        return self._enhanced_text

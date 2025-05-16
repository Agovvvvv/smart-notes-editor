#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Manages the state and data associated with the multi-step note enhancement process.
"""

import logging
from typing import Optional, Tuple

# Get the specific logger for this module
logger = logging.getLogger(__name__)

class EnhancementStateManager:
    """Handles state transitions and data for the note enhancement workflow."""

    def __init__(self, main_window):
        """Initialize the state manager."""
        self.main_window = main_window
        self.current_step = None
        self.reset()
        logger.info("EnhancementStateManager initialized.")

    def reset(self):
        """Reset the enhancement state to its initial condition."""
        old_state = self.current_step
        self.current_step = None
        self.original_note_text = None
        self.original_selection_info = None # {start: int, end: int}
        self.entities = None
        self.enhancement_prompt = None
        self.generated_text = None
        self.is_iterative_refinement = False
        self.feedback = None
        self.error_flag = False
        self.error_message = None
        self.last_request_params = {} # Store params like max_tokens
        if old_state != None:
            logger.debug(f"Enhancement state reset from '{old_state}' to 'None'.")
        logger.info("Enhancement state fully reset.")

    # --- State Transitions ---

    def start_enhancement(self, note_text: str, selection_info: dict = None):
        """Initiate the enhancement process."""
        self.reset()
        old_state = self.current_step # Will be None after reset
        self.current_step = 'started'
        self.original_note_text = note_text
        self.original_selection_info = selection_info
        logger.info(f"Enhancement state changed from '{old_state}' to 'started'. Selection: {bool(selection_info)}")
        # Trigger the first AI step (e.g., entity extraction) from MainWindow

    def entities_extracted(self, entities: list):
        """Update state after entity extraction."""
        if self.current_step in ['started', 'awaiting_entities']:
            old_state = self.current_step
            self.entities = entities
            self.current_step = 'entities_extracted'
            logger.info(f"Enhancement state changed from '{old_state}' to 'entities_extracted'. Entities count: {len(entities)}")
        else:
            logger.warning(f"entities_extracted called in unexpected state: {self.current_step}")

    def generating_enhancement(self, prompt: str):
        """Update state before calling the text generation AI."""
        if self.current_step in ['entities_extracted', 'started', 'refining']:
            old_state = self.current_step
            self.enhancement_prompt = prompt
            self.current_step = 'awaiting_enhancement'
            logger.info(f"Enhancement state changed from '{old_state}' to 'awaiting_enhancement'.")
        else:
            logger.warning(f"generating_enhancement called in unexpected state: {self.current_step}")

    def enhancement_generated(self, generated_text: str):
        """Update state after receiving generated enhancement text."""
        if self.current_step == 'awaiting_enhancement':
            old_state = self.current_step
            self.generated_text = generated_text
            self.current_step = 'enhancement_received'
            logger.info(f"Enhancement state changed from '{old_state}' to 'enhancement_received'.")
        else:
            logger.warning(f"enhancement_generated called in unexpected state: {self.current_step}")

    def start_refinement(self, feedback: str = None):
        """Initiate iterative refinement based on feedback."""
        if self.current_step == 'enhancement_received':
            old_state = self.current_step
            self.is_iterative_refinement = True
            self.feedback = feedback
            self.current_step = 'refining'
            logger.info(f"Enhancement state changed from '{old_state}' to 'refining'. Feedback provided: {bool(feedback)}")
        else:
            logger.warning(f"start_refinement called in unexpected state: {self.current_step}")

    def enhancement_accepted(self):
        """Mark the enhancement as accepted by the user."""
        if self.current_step == 'enhancement_received':
            old_state = self.current_step
            self.current_step = 'accepted'
            logger.info(f"Enhancement state changed from '{old_state}' to 'accepted'.")
            # MainWindow will handle applying the text
        else:
            logger.warning(f"enhancement_accepted called in unexpected state: {self.current_step}")

    def enhancement_rejected(self):
        """Mark the enhancement as rejected by the user."""
        if self.current_step == 'enhancement_received':
            old_state = self.current_step
            self.current_step = 'rejected'
            logger.info(f"Enhancement state changed from '{old_state}' to 'rejected'.")
            # MainWindow handles UI dismissal
        else:
            logger.warning(f"enhancement_rejected called in unexpected state: {self.current_step}")

    def enhancement_error(self, message: str):
        """Record an error during the enhancement process."""
        old_state = self.current_step
        self.error_flag = True
        self.error_message = message
        self.current_step = 'error'
        logger.error(f"Enhancement state changed from '{old_state}' to 'error'. Message: {message}")

    # --- Getters ---

    def is_active(self) -> bool:
        """Check if an enhancement process is currently active."""
        return self.current_step not in [None, 'accepted', 'rejected', 'error']

    def get_state(self) -> str:
        """Return the current step/state."""
        return self.current_step

    def get_original_note_text(self) -> Optional[str]:
        """Returns the original text that was the basis for the enhancement."""
        return self.original_note_text

    def get_original_selection_info(self) -> Optional[dict]:
        """Returns the original selection info (start, end) if any."""
        return self.original_selection_info

    def get_generated_text(self) -> Optional[str]:
        """Return the latest generated enhancement text."""
        return self.generated_text

    def get_last_request_params(self) -> dict:
        """Returns the parameters used for the last AI request (e.g., max_tokens)."""
        return self.last_request_params

    def set_last_request_params(self, params: dict):
        """Sets the parameters used for the last AI request."""
        self.last_request_params = params
        logger.debug(f"Last request params set: {params}")

    def get_error_info(self) -> tuple[bool, Optional[str]]:
        """Return the error status and message."""
        return self.error_flag, self.error_message

    def was_selection_based(self) -> bool:
        """Check if the enhancement was initiated on a text selection."""
        return self.original_selection_info is not None

    # --- Utility Methods ---
    def is_enhancement_pending(self) -> bool:
        """Check if an enhancement process is active."""
        return self.current_step in ['started', 'awaiting_entities', 'entities_extracted', 'awaiting_enhancement', 'enhancement_received', 'refining']

    # --- Prompt Generation Logic (moved from MainWindow) ---

    def _build_standard_style_prompt(self, style: str, text_to_enhance: str, structural_instruction: str, base_instruction_text: str) -> str:
        """Builds prompt for standard enhancement styles."""
        style_modifier = ""
        if style == "clarity":
            style_modifier = " Focus on improving clarity and readability."
        elif style == "concise":
            style_modifier = " Make the text more concise while retaining the core meaning."
        elif style == "expand":
            style_modifier = " Expand on the details and provide more context or information."
        else: 
            logger.debug(f"Unknown or default enhancement style '{style}' requested. Applying general enhancement.")
            style_modifier = " Add relevant information, insights, and details."

        full_instruction = f"{base_instruction_text}{style_modifier}"
        prompt = f"{full_instruction.strip()}\n\n{structural_instruction}\n\nOriginal text:\n---\n{text_to_enhance}\n---"
        return prompt

    def _build_custom_template_prompt(self, style: str, custom_prompt_text: Optional[str], text_to_enhance: str, structural_instruction: str, base_instruction_text: str) -> str:
        """Builds prompt for custom or template-based enhancement styles."""
        if custom_prompt_text:
            user_main_instruction = custom_prompt_text.strip()
            
            if "{text_to_enhance}" in user_main_instruction:
                prompt_body = user_main_instruction.replace("{text_to_enhance}", text_to_enhance)
                if not any(keyword in prompt_body.lower() for keyword in ["maintain formatting", "preserve structure", "markdown format"]):
                    prompt = f"{prompt_body}\n\n{structural_instruction}"
                else:
                    prompt = prompt_body
            else: # User provides a general instruction.
                prompt_prefix = user_main_instruction
                if not any(keyword in prompt_prefix.lower() for keyword in ["maintain formatting", "preserve structure", "markdown format"]):
                    prompt_prefix = f"{user_main_instruction}\n\n{structural_instruction}"
                prompt = f"{prompt_prefix}\n\nOriginal text:\n---\n{text_to_enhance}\n---"
            logger.info(f"Using custom/template enhancement prompt (style: {style})")
        else: # Fallback for empty custom_prompt_text when style is custom/template
            logger.warning(f"{style.capitalize()} style selected but no custom prompt provided. Using default enhancement logic.")
            style_modifier = " Add relevant information, insights, and details." # Default enhancement
            full_instruction = f"{base_instruction_text}{style_modifier}"
            prompt = f"{full_instruction.strip()}\n\n{structural_instruction}\n\nOriginal text:\n---\n{text_to_enhance}\n---"
        return prompt

    def get_enhancement_prompt(self, style: str, text_to_enhance: str, custom_prompt_text: str = None) -> str:
        """Constructs the prompt for the AI based on the enhancement style."""
        base_instruction_text = "Please enhance the following text."
        
        if style == "simple_enhance_plaintext":
            # For plaintext, we don't want complex structural instructions about markdown.
            simple_instruction = "Focus on enhancing the content, clarity, and flow. The output should be plain text."
            prompt = f"{base_instruction_text}\n{simple_instruction}\n\nOriginal text:\n---\n{text_to_enhance}\n---"
        elif style == "custom" or style == "template":
            # Define structural_instruction only where it's needed and used
            structural_instruction = (
                "Important guidance for enhancement: "
                "Maintain the original markdown formatting (e.g., headings #, lists *, -, 1., blockquotes >, code blocks ```). "
                "Integrate new content and modifications smoothly within the existing structure of the provided text. "
                "If enhancing a list, ensure the list format is preserved. If enhancing a paragraph within a section, "
                "keep the changes relevant to that paragraph's context."
            )
            prompt = self._build_custom_template_prompt(
                style, custom_prompt_text, text_to_enhance, structural_instruction, base_instruction_text
            )
        else: # For other standard styles (clarity, concise, expand, or default)
            # Define structural_instruction only where it's needed and used
            structural_instruction = (
                "Important guidance for enhancement: "
                "Maintain the original markdown formatting (e.g., headings #, lists *, -, 1., blockquotes >, code blocks ```). "
                "Integrate new content and modifications smoothly within the existing structure of the provided text. "
                "If enhancing a list, ensure the list format is preserved. If enhancing a paragraph within a section, "
                "keep the changes relevant to that paragraph's context."
            )
            prompt = self._build_standard_style_prompt(
                style, text_to_enhance, structural_instruction, base_instruction_text
            )
        
        self.enhancement_prompt = prompt # Store the generated prompt
        logger.debug(f"Constructed enhancement prompt (style: {style}) - First 100 chars: {prompt[:100]}...")
        return prompt

# Add more methods as needed for specific state queries or transitions.

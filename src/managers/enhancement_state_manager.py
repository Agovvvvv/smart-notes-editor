#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Manages the state and data associated with the multi-step note enhancement process.
"""

import logging
from typing import Optional

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
        logger.debug("Enhancement state reset.")

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

# Add more methods as needed for specific state queries or transitions.

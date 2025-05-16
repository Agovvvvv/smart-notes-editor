#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Workspace Manager for the Smart Contextual Notes Editor.
Handles logic for managing workspaces and notes within them.
"""

import os
import logging
from typing import List, Optional, Dict

from utils.settings import Settings

logger = logging.getLogger(__name__)

class WorkspaceManager:
    """Manages workspaces and notes within them."""

    SUPPORTED_EXTENSIONS = (".txt", ".md")

    def __init__(self, settings: Settings):
        """Initialize the WorkspaceManager.

        Args:
            settings: The application settings instance.
        """
        self.settings = settings

    def get_all_workspaces(self) -> List[Dict[str, str]]:
        """Get a list of all configured workspaces."""
        return self.settings.get_workspaces()

    def add_workspace(self, name: str, path: str) -> bool:
        """Add a new workspace.

        Args:
            name: The name for the new workspace.
            path: The root directory path for the new workspace.

        Returns:
            True if the workspace was added successfully, False otherwise.
        """
        if not os.path.isdir(path):
            logger.error(f"Failed to add workspace '{name}': Path '{path}' is not a valid directory.")
            return False
        return self.settings.add_workspace(name, path)

    def remove_workspace(self, name: str) -> bool:
        """Remove a workspace.

        Args:
            name: The name of the workspace to remove.

        Returns:
            True if the workspace was removed successfully, False otherwise.
        """
        return self.settings.remove_workspace(name)

    def get_active_workspace_name(self) -> Optional[str]:
        """Get the name of the currently active workspace."""
        return self.settings.get_active_workspace_name()

    def set_active_workspace(self, name: Optional[str]) -> bool:
        """Set the active workspace.

        Args:
            name: The name of the workspace to set as active. Pass None to deactivate.

        Returns:
            True if setting the active workspace was successful, False otherwise.
        """
        return self.settings.set_active_workspace_name(name)

    def get_active_workspace_path(self) -> Optional[str]:
        """Get the path of the currently active workspace."""
        active_name = self.get_active_workspace_name()
        if active_name:
            return self.settings.get_workspace_path(active_name)
        return None

    def list_notes_in_workspace(self, workspace_name: Optional[str] = None) -> List[str]:
        """List note files (filenames only) in the specified or active workspace.

        Args:
            workspace_name: The name of the workspace. If None, uses the active workspace.

        Returns:
            A list of note filenames (e.g., ['note1.txt', 'note2.md']).
        """
        target_workspace_name = workspace_name or self.get_active_workspace_name()
        if not target_workspace_name:
            logger.info("No workspace specified or active to list notes from.")
            return []

        workspace_path = self.settings.get_workspace_path(target_workspace_name)
        if not workspace_path or not os.path.isdir(workspace_path):
            logger.warning(f"Path for workspace '{target_workspace_name}' not found or is not a directory.")
            return []

        notes = []
        try:
            for item in os.listdir(workspace_path):
                if os.path.isfile(os.path.join(workspace_path, item)) and \
                   item.lower().endswith(self.SUPPORTED_EXTENSIONS):
                    notes.append(item)
            notes.sort() # For consistent ordering
            return notes
        except OSError as e:
            logger.error(f"Error listing notes in workspace '{target_workspace_name}': {e}")
            return []

    def create_note_in_active_workspace(self, note_title: str, extension: str = "md") -> Optional[str]:
        """Create a new, empty note file in the active workspace.

        The filename will be derived from the note_title.
        Example: if note_title is "My New Idea", filename becomes "My New Idea.md".
        If a file with that name already exists, it appends a number (e.g., "My New Idea (1).md").

        Args:
            note_title: The desired title for the note.
            extension: The file extension (without dot), defaults to "md".

        Returns:
            The full path to the newly created note file, or None on failure.
        """
        active_workspace_path = self.get_active_workspace_path()
        if not active_workspace_path:
            logger.error("Cannot create note: No active workspace set.")
            return None

        if not note_title.strip():
            logger.error("Cannot create note: Note title cannot be empty.")
            return None
        
        # Sanitize title for filename - basic sanitization
        safe_title = "".join(c if c.isalnum() or c in (' ', '_', '-') else '' for c in note_title).strip()
        if not safe_title:
            safe_title = "Untitled Note"

        base_filename = f"{safe_title}.{extension.lstrip('.')}"
        note_path = os.path.join(active_workspace_path, base_filename)

        counter = 1
        while os.path.exists(note_path):
            filename_wo_ext, ext = os.path.splitext(base_filename)
            note_path = os.path.join(active_workspace_path, f"{filename_wo_ext} ({counter}){ext}")
            counter += 1

        try:
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write("")  # Create an empty file
            logger.info(f"Created new note: {note_path}")
            return note_path
        except OSError as e:
            logger.error(f"Error creating note file '{note_path}': {e}")
            return None

    def get_note_path(self, note_filename: str, workspace_name: Optional[str] = None) -> Optional[str]:
        """Get the full path of a note within a specified or active workspace.

        Args:
            note_filename: The filename of the note (e.g., 'my_note.txt').
            workspace_name: The name of the workspace. If None, uses the active workspace.

        Returns:
            The full absolute path to the note, or None if not found.
        """
        target_workspace_name = workspace_name or self.get_active_workspace_name()
        if not target_workspace_name:
            logger.warning("No workspace specified or active to get note path from.")
            return None

        workspace_path = self.settings.get_workspace_path(target_workspace_name)
        if not workspace_path:
            logger.warning(f"Path for workspace '{target_workspace_name}' not found.")
            return None

        note_path = os.path.join(workspace_path, note_filename)
        # We don't check os.path.exists here, as the caller might want the theoretical path
        return note_path

    def rename_note_in_active_workspace(self, old_filename: str, new_filename_base: str) -> Optional[str]:
        """Renames a note in the active workspace.
        The new_filename_base should be the name without extension.
        The extension of the old file will be preserved.
        Handles uniqueness for the new name automatically.

        Args:
            old_filename: The current filename of the note (e.g., "old_note.md").
            new_filename_base: The new base name for the note (e.g., "new shiny note").

        Returns:
            The new full path if successful, else None.
        """
        active_workspace_path = self.get_active_workspace_path()
        if not active_workspace_path:
            logger.error("Cannot rename note: No active workspace.")
            return None

        old_note_path = os.path.join(active_workspace_path, old_filename)
        if not os.path.exists(old_note_path):
            logger.error(f"Cannot rename note: Source file '{old_note_path}' does not exist.")
            return None

        _, extension = os.path.splitext(old_filename)
        new_filename_base_sanitized = "".join(c if c.isalnum() or c in (' ', '_', '-') else '' for c in new_filename_base).strip()
        if not new_filename_base_sanitized:
            logger.error("Cannot rename note: New name is invalid after sanitization.")
            return None

        new_filename_candidate = f"{new_filename_base_sanitized}{extension}"
        new_note_path = os.path.join(active_workspace_path, new_filename_candidate)

        counter = 1
        while os.path.exists(new_note_path) and new_note_path != old_note_path:
            new_note_path = os.path.join(active_workspace_path, f"{new_filename_base_sanitized} ({counter}){extension}")
            counter += 1
        
        if new_note_path == old_note_path and new_filename_candidate != old_filename:
            # This case means the target name is the same as original but might have changed due to sanitization
            # or the user is trying to rename to the exact same name (potentially just changing case on some systems)
            # If the exact target is the same as source, we can consider it a success if no actual rename is needed.
            # However, if the *candidate* name was different, it implies an issue.
            logger.info(f"Rename not strictly needed or target name resolves to current name: {old_filename} -> {new_filename_candidate}")
            # We might allow this, or disallow if the *intended* new name (before unique check) was different.
            # For now, let's attempt rename; os.rename might handle case changes.
            pass 

        try:
            os.rename(old_note_path, new_note_path)
            logger.info(f"Renamed note from '{old_note_path}' to '{new_note_path}'.")
            return new_note_path
        except OSError as e:
            logger.error(f"Error renaming note from '{old_note_path}' to '{new_note_path}': {e}")
            return None

    def delete_note_from_active_workspace(self, note_filename: str) -> bool:
        """Deletes a note from the active workspace.

        Args:
            note_filename: The filename of the note to delete (e.g., "my_note.txt").

        Returns:
            True if deletion was successful, False otherwise.
        """
        active_workspace_path = self.get_active_workspace_path()
        if not active_workspace_path:
            logger.error("Cannot delete note: No active workspace.")
            return False

        note_path = os.path.join(active_workspace_path, note_filename)
        if not os.path.exists(note_path):
            logger.warning(f"Cannot delete note: File '{note_path}' does not exist.")
            return False

        try:
            os.remove(note_path)
            logger.info(f"Deleted note: {note_path}")
            return True
        except OSError as e:
            logger.error(f"Error deleting note '{note_path}': {e}")
            return False

    def get_recent_workspaces_details(self) -> List[Dict[str, str]]:
        """Returns a list of dictionaries, each containing 'name' and 'path' for recent workspaces."""
        recent_names = self.settings.get_recent_workspaces_names()
        details = []
        for name in recent_names:
            path = self.settings.get_workspace_path(name)
            if path:
                details.append({'name': name, 'path': path})
            else:
                logger.warning(f"Recent workspace '{name}' has no path in settings. Skipping.")
        return details

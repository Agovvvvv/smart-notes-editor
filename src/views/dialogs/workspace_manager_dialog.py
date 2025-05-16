#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dialog for managing workspaces in the Smart Contextual Notes Editor.
"""

import logging
from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, 
    QLineEdit, QFileDialog, QMessageBox, QLabel, QInputDialog, 
    QListWidgetItem, QAbstractItemView
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

from managers.workspace_manager import WorkspaceManager

logger = logging.getLogger(__name__)

class WorkspaceManagerDialog(QDialog):
    """Dialog for managing workspaces."""
    workspaces_updated = pyqtSignal()  # Emitted when workspaces change (add, remove, active)

    def __init__(self, workspace_manager: WorkspaceManager, parent=None):
        super().__init__(parent)
        self.workspace_manager = workspace_manager
        self.setWindowTitle("Manage Workspaces")
        self.setMinimumWidth(500)
        self.setModal(True)

        self._init_ui()
        self.populate_workspaces_list()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # List of workspaces
        self.workspaces_list_widget = QListWidget()
        self.workspaces_list_widget.setAlternatingRowColors(True)
        self.workspaces_list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.workspaces_list_widget.itemSelectionChanged.connect(self._update_button_states)
        layout.addWidget(QLabel("Available Workspaces:"))
        layout.addWidget(self.workspaces_list_widget)

        # Buttons layout
        buttons_layout = QHBoxLayout()

        self.add_button = QPushButton("&Add New...")
        self.add_button.clicked.connect(self.handle_add_workspace)
        buttons_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("&Remove Selected")
        self.remove_button.clicked.connect(self.handle_remove_workspace)
        buttons_layout.addWidget(self.remove_button)

        self.set_active_button = QPushButton("Set as &Active")
        self.set_active_button.clicked.connect(self.handle_set_active_workspace)
        buttons_layout.addWidget(self.set_active_button)
        
        buttons_layout.addStretch()

        self.close_button = QPushButton("&Close")
        self.close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_button)

        layout.addLayout(buttons_layout)
        self._update_button_states() # Initial state

    def _update_button_states(self):
        selected_item = self.get_selected_workspace_item()
        has_selection = selected_item is not None
        self.remove_button.setEnabled(has_selection)
        self.set_active_button.setEnabled(has_selection)

        # Disable 'Set Active' if the selected workspace is already active
        if has_selection:
            active_workspace_name = self.workspace_manager.get_active_workspace_name()
            if selected_item.text() == active_workspace_name:
                self.set_active_button.setEnabled(False)

    def populate_workspaces_list(self):
        self.workspaces_list_widget.clear()
        workspaces = self.workspace_manager.get_all_workspaces()
        active_workspace_name = self.workspace_manager.get_active_workspace_name()

        for ws in workspaces:
            item = QListWidgetItem(ws['name'])
            item.setData(Qt.UserRole, ws) # Store full workspace dict for later use
            if ws['name'] == active_workspace_name:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                item.setSelected(True) # This also helps visually, selectionChanged will fire
            self.workspaces_list_widget.addItem(item)
        self._update_button_states()

    def get_selected_workspace_item(self) -> Optional[QListWidgetItem]:
        selected_items = self.workspaces_list_widget.selectedItems()
        return selected_items[0] if selected_items else None

    def get_selected_workspace_name(self) -> Optional[str]:
        item = self.get_selected_workspace_item()
        return item.text() if item else None

    def handle_add_workspace(self):
        workspace_name, ok = QInputDialog.getText(self, "Add Workspace", "Enter a name for the new workspace:")
        if ok and workspace_name:
            workspace_path = QFileDialog.getExistingDirectory(self, "Select Workspace Root Directory")
            if workspace_path:
                if self.workspace_manager.add_workspace(workspace_name, workspace_path):
                    logger.info(f"Workspace '{workspace_name}' added with path '{workspace_path}'.")
                    self.populate_workspaces_list()
                    self.workspaces_updated.emit()
                else:
                    QMessageBox.warning(self, "Add Workspace Failed", 
                                        f"Could not add workspace '{workspace_name}'. Check logs for details (e.g., name conflict or invalid path).")
            else:
                logger.info("Workspace directory selection cancelled.")
        else:
            logger.info("Workspace name input cancelled or empty.")

    def handle_remove_workspace(self):
        selected_name = self.get_selected_workspace_name()
        if not selected_name:
            QMessageBox.information(self, "Remove Workspace", "Please select a workspace to remove.")
            return

        reply = QMessageBox.question(self, "Confirm Removal", 
                                     f"Are you sure you want to remove the workspace '{selected_name}'?\nThis will only remove it from the application's list, not delete files on disk.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if self.workspace_manager.remove_workspace(selected_name):
                logger.info(f"Workspace '{selected_name}' removed.")
                self.populate_workspaces_list()
                self.workspaces_updated.emit()
            else:
                QMessageBox.warning(self, "Remove Failed", f"Could not remove workspace '{selected_name}'.")

    def handle_set_active_workspace(self):
        selected_name = self.get_selected_workspace_name()
        if not selected_name:
            QMessageBox.information(self, "Set Active Workspace", "Please select a workspace to set as active.")
            return

        if self.workspace_manager.set_active_workspace(selected_name):
            logger.info(f"Workspace '{selected_name}' set as active.")
            self.populate_workspaces_list() # Refreshes bolding and button states
            self.workspaces_updated.emit()
        else:
            QMessageBox.warning(self, "Set Active Failed", f"Could not set '{selected_name}' as active workspace.")

if __name__ == '__main__':
    # Example usage (for testing the dialog directly)
    from PyQt5.QtWidgets import QApplication
    import sys
    from src.utils.settings import Settings

    # Ensure a clean settings file for testing if needed
    # test_settings_path = "./test_settings.json"
    # if os.path.exists(test_settings_path):
    #     os.remove(test_settings_path)

    app = QApplication(sys.argv)
    
    # Create dummy settings and manager for testing
    # You might want to point settings to a test file if you run this often
    temp_settings = Settings() # This will use the default or existing settings.json
    # temp_settings.settings_file = test_settings_path # Optional: redirect for test
    
    # Clear existing workspaces for a clean test if desired
    # for ws in temp_settings.get_workspaces():
    #     temp_settings.remove_workspace(ws['name'])
    # temp_settings.set_active_workspace_name(None)

    manager = WorkspaceManager(temp_settings)
    
    dialog = WorkspaceManagerDialog(manager)
    dialog.workspaces_updated.connect(lambda: print("Event: Workspaces updated!"))
    
    if dialog.exec_():
        print("Dialog accepted.")
    else:
        print("Dialog rejected/closed.")
    
    print(f"Active workspace after dialog: {manager.get_active_workspace_name()}")
    print(f"All workspaces: {manager.get_all_workspaces()}")

    # Clean up test settings file if created
    # if os.path.exists(test_settings_path):
    #     os.remove(test_settings_path)

    sys.exit(app.exec_())

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
    QPushButton, QMessageBox, QInputDialog, QTextEdit,
    QLabel, QLineEdit, QDialogButtonBox, QListWidgetItem
)
from PyQt5.QtCore import Qt

# Assuming Settings is accessible, e.g., passed in or via a global accessor
# from utils.settings import Settings # This might need adjustment based on how settings are passed

logger = logging.getLogger(__name__)

class TemplateEditDialog(QDialog):
    """Dialog for adding or editing a single template."""
    def __init__(self, template_name="", template_prompt="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Template" if template_name else "Add New Template")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        self.name_label = QLabel("Template Name:")
        self.name_edit = QLineEdit(template_name)
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_edit)

        self.prompt_label = QLabel("Template Prompt:")
        self.prompt_edit = QTextEdit(template_prompt)
        self.prompt_edit.setMinimumHeight(100)
        layout.addWidget(self.prompt_label)
        layout.addWidget(self.prompt_edit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_template_data(self):
        """Returns the template name and prompt from the dialog."""
        return self.name_edit.text().strip(), self.prompt_edit.toPlainText().strip()

class TemplateManagerDialog(QDialog):
    """Dialog for managing enhancement templates."""
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Manage Enhancement Templates")
        self.setMinimumSize(500, 400)

        self._init_ui()
        self._load_templates()

    def _init_ui(self):
        """Initialize UI components."""
        main_layout = QVBoxLayout(self)

        # List widget for templates
        self.template_list_widget = QListWidget()
        self.template_list_widget.itemDoubleClicked.connect(self._edit_selected_template)
        main_layout.addWidget(self.template_list_widget)

        # Button layout
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("&Add New...")
        self.add_button.clicked.connect(self._add_template)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("&Edit Selected...")
        self.edit_button.clicked.connect(self._edit_selected_template)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("&Delete Selected")
        self.delete_button.clicked.connect(self._delete_template)
        button_layout.addWidget(self.delete_button)

        button_layout.addStretch()

        self.close_button = QPushButton("&Close")
        self.close_button.clicked.connect(self.accept) # QDialog.accept() closes the dialog
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)

    def _load_templates(self):
        """Load templates from settings and populate the list widget."""
        self.template_list_widget.clear()
        try:
            templates = self.settings.get_enhancement_templates()
            if templates:
                for name in sorted(templates.keys()):
                    item = QListWidgetItem(name)
                    self.template_list_widget.addItem(item)
            logger.info(f"Loaded {len(templates)} templates into manager dialog.")
        except Exception as e:
            logger.error(f"Error loading templates into dialog: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Could not load templates: {e}")

    def _add_template(self):
        """Handle adding a new template."""
        dialog = TemplateEditDialog(parent=self)
        if dialog.exec_() != QDialog.Accepted:
            return

        name, prompt = dialog.get_template_data()
        if not name or not prompt:
            QMessageBox.warning(self, "Input Required", "Template name and prompt cannot be empty.")
            return

        if name in self.settings.get_enhancement_templates():
            QMessageBox.warning(self, "Template Exists", 
                                  f"A template named '{name}' already exists. Please choose a different name.")
            return

        if self.settings.save_enhancement_template(name, prompt):
            self._load_templates() # Refresh list
            logger.info(f"Added new template: {name}")
        else:
            QMessageBox.critical(self, "Error", "Failed to save the new template.")

    def _edit_selected_template(self):
        """Handle editing the selected template."""
        selected_item = self.template_list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "No Selection", "Please select a template to edit.")
            return

        original_name = selected_item.text()
        original_prompt = self.settings.get_enhancement_templates().get(original_name, "")

        dialog = TemplateEditDialog(template_name=original_name, template_prompt=original_prompt, parent=self)
        if dialog.exec_() != QDialog.Accepted:
            return

        new_name, new_prompt = dialog.get_template_data()
        if not new_name or not new_prompt:
            QMessageBox.warning(self, "Input Required", "Template name and prompt cannot be empty.")
            return

        # Check for name conflict only if the name has changed
        if new_name != original_name and new_name in self.settings.get_enhancement_templates():
            QMessageBox.warning(self, "Template Exists", 
                                  f"A template named '{new_name}' already exists. Please choose a different name.")
            return
        
        # Attempt to save the template
        if not self.settings.save_enhancement_template(new_name, new_prompt):
            QMessageBox.critical(self, "Error", f"Failed to save template '{new_name}'.")
            return

        # If name changed and save was successful, delete the old template
        if new_name != original_name:
            if not self.settings.delete_enhancement_template(original_name):
                # This case is tricky: new one saved, old one failed to delete.
                # For simplicity, log it. User might see both for a moment until manual correction or next load.
                logger.error(f"Saved new template '{new_name}' but failed to delete old template '{original_name}'.")
            else:
                logger.info(f"Successfully renamed template '{original_name}' to '{new_name}'.")

        self._load_templates() # Refresh list
        logger.info(f"Edited template (final name: {new_name})")

    def _delete_template(self):
        """Handle deleting the selected template."""
        selected_item = self.template_list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "No Selection", "Please select a template to delete.")
            return

        template_name = selected_item.text()
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete the template '{template_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if self.settings.delete_enhancement_template(template_name):
                self._load_templates() # Refresh list
                logger.info(f"Deleted template: {template_name}")
            else:
                QMessageBox.critical(self, "Error", f"Failed to delete template '{template_name}'.")

if __name__ == '__main__':
    # Example usage (for testing purposes)
    from PyQt5.QtWidgets import QApplication
    import sys

    # Mock Settings class for testing
    class MockSettings:
        def __init__(self):
            self.templates = {
                "Test Template 1": "This is the first test prompt.",
                "Another Template": "Make this formal."
            }
        def get_enhancement_templates(self):
            return self.templates.copy()
        def save_enhancement_template(self, name, prompt):
            self.templates[name] = prompt
            print(f"Saved template: {name} - {prompt}")
            return True
        def delete_enhancement_template(self, name):
            if name in self.templates:
                del self.templates[name]
                print(f"Deleted template: {name}")
                return True
            return False

    app = QApplication(sys.argv)
    mock_settings = MockSettings()
    dialog = TemplateManagerDialog(settings=mock_settings)
    dialog.show()
    sys.exit(app.exec_())

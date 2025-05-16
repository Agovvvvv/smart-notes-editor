import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QLabel
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QIcon # Ensured QIcon is imported

logger = logging.getLogger(__name__)

class WorkspaceWelcomeWidget(QWidget):
    """Widget to display when no workspace is active or to welcome the user."""
    manage_workspaces_requested = pyqtSignal()
    recent_workspace_selected = pyqtSignal(str) # Emits workspace name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setObjectName("WorkspaceWelcomeWidget") # Added
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Title Label
        title_label = QLabel("Welcome to Smart Notes")
        title_label.setObjectName("welcomeTitleLabel") # Added
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        layout.addSpacing(10)

        # Open Workspace Button (Renamed from manage_workspaces_button)
        # Using a standard icon for file manager, or you can use a custom one
        self.open_workspace_button = QPushButton(QIcon.fromTheme("folder-open", QIcon(":/icons/default_folder_icon.png")), "Open Workspace...") # Renamed variable and text
        self.open_workspace_button.setObjectName("openWorkspaceButton") # Added
        self.open_workspace_button.setToolTip("Open or create a workspace") # Updated tooltip
        self.open_workspace_button.clicked.connect(self.manage_workspaces_requested) # Signal remains the same, button's purpose is to trigger this
        layout.addWidget(self.open_workspace_button)

        layout.addSpacing(15)

        # Recent Workspaces Section
        recent_title_label = QLabel("Recent Workspaces")
        recent_title_label.setObjectName("recentWorkspacesTitleLabel") # Added
        recent_font = QFont()
        recent_font.setPointSize(12)
        recent_title_label.setFont(recent_font)
        layout.addWidget(recent_title_label)

        self.recent_workspaces_list = QListWidget()
        self.recent_workspaces_list.setObjectName("RecentWorkspacesList")
        self.recent_workspaces_list.setSpacing(3)
        self.recent_workspaces_list.itemClicked.connect(self._on_recent_workspace_clicked)
        layout.addWidget(self.recent_workspaces_list)
        
        layout.addStretch()

    def populate_recent_workspaces(self, recent_workspaces_details: list[dict]):
        """
        Populates the list with recent workspace names and paths.
        Each item will store the workspace name as its data.
        Args:
            recent_workspaces_details: A list of dicts, each with 'name' and 'path'.
        """
        self.recent_workspaces_list.clear()
        if not recent_workspaces_details:
            no_recent_item = QListWidgetItem("No recent workspaces found.")
            no_recent_item.setFlags(no_recent_item.flags() & ~Qt.ItemIsSelectable)
            self.recent_workspaces_list.addItem(no_recent_item)
        else:
            for ws_detail in recent_workspaces_details:
                name = ws_detail.get('name')
                if name:
                    item = QListWidgetItem(name)
                    item.setData(Qt.UserRole, name) # Store the name for retrieval
                    item.setToolTip(f"Path: {ws_detail.get('path', 'N/A')}")
                    self.recent_workspaces_list.addItem(item)
        logger.debug(f"Recent workspaces list populated with {len(recent_workspaces_details)} items.")

    def _on_recent_workspace_clicked(self, item: QListWidgetItem):
        workspace_name = item.data(Qt.UserRole)
        if workspace_name:
            logger.info(f"Recent workspace selected: {workspace_name}")
            self.recent_workspace_selected.emit(workspace_name)
        else:
            logger.debug("Clicked on a non-selectable item in recent workspaces list.")

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    # This is a basic example, you might need to adjust paths for icons if using resource files
    # For QIcon.fromTheme to work well, your desktop environment might need to be configured with icon themes.
    # A fallback QIcon can be provided as the second argument if the theme icon is not found.

    app = QApplication(sys.argv)
    # Example recent workspaces
    example_recents = [
        {'name': 'Project Alpha Notes', 'path': '/path/to/alpha'},
        {'name': 'Personal Journal', 'path': '/path/to/personal'},
        {'name': 'Research Papers', 'path': '/path/to/research'}
    ]

    welcome_widget = WorkspaceWelcomeWidget()
    welcome_widget.populate_recent_workspaces(example_recents)
    welcome_widget.setWindowTitle("Workspace Welcome Test")
    welcome_widget.setGeometry(300, 300, 350, 450) # Adjusted size for better view
    welcome_widget.show()

    welcome_widget.manage_workspaces_requested.connect(lambda: print("Manage Workspaces Requested via test script"))
    welcome_widget.recent_workspace_selected.connect(lambda name: print(f"Recent Workspace Selected via test script: {name}"))

    sys.exit(app.exec_())

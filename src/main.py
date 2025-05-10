#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smart Contextual Notes Editor
Main entry point for the application.
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QFile, QTextStream
from views.main_window import MainWindow
from utils.settings import Settings
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_stylesheet(theme="dark"):
    """
    Load the application stylesheet.
    
    Args:
        theme (str): The theme to load (light or dark).
        
    Returns:
        str: The stylesheet content.
    """
    # Get the project root directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # Determine the stylesheet file path
    # Currently we only have a dark theme, so we use it for all themes
    # In the future, we can add more theme options
    stylesheet_path = os.path.join(project_root, "styles", "dark_theme.qss")
    
    # Load the stylesheet
    if os.path.exists(stylesheet_path):
        file = QFile(stylesheet_path)
        file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(file)
        stylesheet = stream.readAll()
        file.close()
        logger.info(f"Loaded stylesheet: {stylesheet_path}")
        return stylesheet
    else:
        logger.warning(f"Stylesheet not found: {stylesheet_path}")
        return ""

def main():
    """Initialize and run the application."""
    # Load environment variables from .env file
    load_dotenv()
    logger.info(".env file loaded (if present).")

    # Create the application
    app = QApplication(sys.argv)
    
    # Load settings
    settings = Settings()
    
    # Load and apply the stylesheet
    theme = settings.get("appearance", "theme", "dark")
    stylesheet = load_stylesheet(theme)
    if stylesheet:
        app.setStyleSheet(stylesheet)
    
    # Create and show the main window
    window = MainWindow(settings)
    
    # Set window geometry from settings
    width = settings.get("window", "width", 800)
    height = settings.get("window", "height", 600)
    x = settings.get("window", "x", 100)
    y = settings.get("window", "y", 100)
    window.setGeometry(x, y, width, height)
    
    window.show()
    
    # Run the application
    exit_code = app.exec_()
    
    # Save window geometry to settings before exiting
    settings.set("window", "width", window.width())
    settings.set("window", "height", window.height())
    settings.set("window", "x", window.x())
    settings.set("window", "y", window.y())
    settings.save_settings()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

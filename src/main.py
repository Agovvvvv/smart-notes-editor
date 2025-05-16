#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smart Contextual Notes Editor
Main entry point for the application.
"""

import sys
import os
import logging
import re # New import
import resources_rc
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QFile, QTextStream, QVariant # Added QVariant
from views.main_window import MainWindow
from utils.settings import Settings
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def _read_qss_file(resource_path, current_logger):
    """Helper function to read a QSS file from Qt Resources."""
    qss_file = QFile(resource_path)
    if not qss_file.exists(): # Check existence for resource paths
        current_logger.warning(f"Stylesheet resource not found: {resource_path}")
        return None

    if not qss_file.open(QFile.ReadOnly | QFile.Text):
        current_logger.warning(f"Could not open stylesheet resource: {resource_path} - Error: {qss_file.errorString()}")
        return None
    
    stream = QTextStream(qss_file)
    content = stream.readAll()
    qss_file.close()
    current_logger.info(f"Successfully loaded stylesheet from resource: {resource_path}")
    return content

def apply_base_variables_as_properties(app_instance, base_variables_content, current_logger):
    """
    Parses QSS content (from base_variables.qss) and sets qproperty- values
    as dynamic properties on the QApplication instance.
    """
    if not base_variables_content:
        current_logger.warning("No base variables content provided to apply_base_variables_as_properties.")
        return

    star_block_match = re.search(r"\*\s*\{([^}]+)\}", base_variables_content, re.DOTALL)
    content_to_search = base_variables_content
    if star_block_match:
        content_to_search = star_block_match.group(1)
        current_logger.debug("Found and using content within * { ... } block for qproperties.")
    else:
        current_logger.warning("Could not find a global '* { ... }' block in base_variables.qss. Searching the entire file for qproperties. This might be unintended.")

    prop_matches = re.findall(r"qproperty-(\w+)\s*:\s*([^;]+);", content_to_search)

    if not prop_matches:
        current_logger.warning("No qproperties found in the processed content of base_variables.qss.")
        return

    found_props_count = 0
    for prop_name, prop_value in prop_matches:
        prop_value = prop_value.strip()
        url_match = re.match(r"url\(([^)]+)\)", prop_value)
        if url_match:
            prop_value = url_match.group(1).strip().strip("'\"")

        app_instance.setProperty(prop_name, QVariant(prop_value))
        current_logger.debug(f"Set application property: {prop_name} = {prop_value}")
        found_props_count +=1
    
    if found_props_count > 0:
        current_logger.info(f"Successfully applied {found_props_count} qproperties from base_variables.qss to QApplication.")
    else:
        current_logger.warning("No qproperties were successfully applied. Check regex and QSS format.")

def main():
    """Initialize and run the application."""
    # Load environment variables from .env file
    load_dotenv()
    logger.info(".env file loaded (if present).")

    # Create the application
    app = QApplication(sys.argv)
    
    # Load settings
    settings = Settings()
    
    # Load base variables QSS and apply them as properties to the QApplication instance
    base_variables_qss_content = _read_qss_file(":/styles/base_variables.qss", logger)
    if base_variables_qss_content:
        apply_base_variables_as_properties(app, base_variables_qss_content, logger)
    else:
        logger.error("Could not load base_variables.qss. Dynamic properties for styling will not be set.")

    # Determine the theme and load the theme-specific stylesheet
    theme_name = settings.get("appearance", "theme", "dark")
    theme_stylesheet_path = f":/styles/{theme_name}_theme.qss"
    theme_qss_content = _read_qss_file(theme_stylesheet_path, logger)
    
    if theme_qss_content:
        app.setStyleSheet(theme_qss_content)
        logger.info(f"Applied {theme_name}_theme.qss stylesheet.")
    else:
        logger.error(f"Could not load {theme_stylesheet_path}. Application may appear unstyled or use default Qt styling.")
    
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

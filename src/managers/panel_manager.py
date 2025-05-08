#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Manager for handling UI panels.
"""

import logging
from PyQt5.QtWidgets import QWidget

# Import panels
from views.panels.summary_panel import SummaryPanel
from views.panels.web_panel import WebPanel
from views.panels.suggestions_panel import SuggestionsPanel

logger = logging.getLogger(__name__)

class PanelManager:
    """Manager for handling UI panels."""
    
    def __init__(self, main_window):
        """Initialize the panel manager."""
        self.main_window = main_window
        self.summary_panel = None
        self.web_panel = None
        self.suggestions_panel = None
    
    def show_summary_panel(self, summary):
        """
        Show the summary panel with the generated summary.
        
        Args:
            summary (str): The generated summary
        """
        logger.info("PanelManager: Attempting to show summary panel.")
        # If the summary panel already exists, remove it
        if self.summary_panel is not None:
            logger.info("PanelManager: Existing summary panel found, removing it.")
            self.main_window.splitter.replaceWidget(1, QWidget())
        
        # Create the summary panel
        logger.info("PanelManager: Creating new SummaryPanel.")
        self.summary_panel = SummaryPanel(self.main_window)
        self.summary_panel.set_summary(summary)
        
        # Add the summary panel to the splitter
        logger.info(f"PanelManager: Adding SummaryPanel to splitter. Splitter count before: {self.main_window.splitter.count()}")
        self.main_window.splitter.addWidget(self.summary_panel)
        logger.info(f"PanelManager: SummaryPanel added. Splitter count after: {self.main_window.splitter.count()}")
        
        # Set the sizes of the splitter widgets
        main_width = int(self.main_window.width() * 0.6)
        panel_width = int(self.main_window.width() * 0.4)
        if panel_width == 0 and self.main_window.width() > 0: 
            panel_width = 200 
            main_width = self.main_window.width() - panel_width

        logger.info(f"PanelManager: Setting splitter sizes. Main: {main_width}, Panel: {panel_width}. Current window width: {self.main_window.width()}")
        self.main_window.splitter.setSizes([main_width, panel_width])
        logger.info(f"PanelManager: Splitter sizes set to: {self.main_window.splitter.sizes()}")
    
    def close_summary_panel(self):
        """Close the summary panel."""
        logger.info("PanelManager: Attempting to close summary panel.")
        if self.summary_panel is not None:
            # Find the index of the summary_panel in the splitter
            panel_index = -1
            for i in range(self.main_window.splitter.count()):
                if self.main_window.splitter.widget(i) == self.summary_panel:
                    panel_index = i
                    break
            
            if panel_index != -1:
                logger.info(f"PanelManager: SummaryPanel found at index {panel_index}. Replacing with empty QWidget.")
                # Create a new QWidget to replace the panel
                placeholder = QWidget()
                self.main_window.splitter.replaceWidget(panel_index, placeholder)
                # The placeholder takes ownership, no need to delete summary_panel explicitly if it was a child of splitter
                self.summary_panel.setParent(None) 
                self.summary_panel = None
                logger.info(f"PanelManager: SummaryPanel closed. Splitter count: {self.main_window.splitter.count()}")
            else:
                logger.warning("PanelManager: SummaryPanel not found in splitter during close.")
                self.summary_panel = None # Still nullify to prevent issues
            
            # Reset the splitter sizes
            main_editor_width = self.main_window.splitter.widget(0).width()
            if self.main_window.splitter.count() > 1:
                 # This assumes editor is widget 0, and placeholder is widget 1
                 self.main_window.splitter.setSizes([main_editor_width + self.main_window.splitter.widget(1).width(), 0])
            else:
                 self.main_window.splitter.setSizes([main_editor_width, 0])
            logger.info(f"PanelManager: Splitter sizes reset to: {self.main_window.splitter.sizes()}")
        else:
            logger.info("PanelManager: No summary panel to close.")
    
    def show_web_results_panel(self, results):
        """
        Show the web results panel with the search results.
        
        Args:
            results (list): The search results
        """
        logger.info("PanelManager: Attempting to show web results panel.")
        # If the web panel already exists, remove it
        if self.web_panel is not None:
            logger.info("PanelManager: Existing web panel found, removing it.")
            self.main_window.splitter.replaceWidget(1, QWidget())
        
        # Create the web panel
        logger.info("PanelManager: Creating new WebPanel.")
        self.web_panel = WebPanel(self.main_window)
        self.web_panel.set_results(results)
        
        # Add the web panel to the splitter
        logger.info(f"PanelManager: Adding WebPanel to splitter. Splitter count before: {self.main_window.splitter.count()}")
        self.main_window.splitter.addWidget(self.web_panel)
        logger.info(f"PanelManager: WebPanel added. Splitter count after: {self.main_window.splitter.count()}")
        
        # Set the sizes of the splitter widgets
        main_width = int(self.main_window.width() * 0.6)
        panel_width = int(self.main_window.width() * 0.4)
        if panel_width == 0 and self.main_window.width() > 0:
            panel_width = 200
            main_width = self.main_window.width() - panel_width
        logger.info(f"PanelManager: Setting splitter sizes. Main: {main_width}, Panel: {panel_width}. Current window width: {self.main_window.width()}")
        self.main_window.splitter.setSizes([main_width, panel_width])
        logger.info(f"PanelManager: Splitter sizes set to: {self.main_window.splitter.sizes()}")
    
    def close_web_panel(self):
        """Close the web results panel."""
        logger.info("PanelManager: Attempting to close web panel.")
        if self.web_panel is not None:
            panel_index = -1
            for i in range(self.main_window.splitter.count()):
                if self.main_window.splitter.widget(i) == self.web_panel:
                    panel_index = i
                    break
            
            if panel_index != -1:
                logger.info(f"PanelManager: WebPanel found at index {panel_index}. Replacing with empty QWidget.")
                placeholder = QWidget()
                self.main_window.splitter.replaceWidget(panel_index, placeholder)
                self.web_panel.setParent(None)
                self.web_panel = None
                logger.info(f"PanelManager: WebPanel closed. Splitter count: {self.main_window.splitter.count()}")
            else:
                logger.warning("PanelManager: WebPanel not found in splitter during close.")
                self.web_panel = None
            
            # Reset the splitter sizes
            if self.main_window.splitter.count() > 1:
                 self.main_window.splitter.setSizes([self.main_window.splitter.widget(0).width() + self.main_window.splitter.widget(1).width(), 0])
            else:
                 self.main_window.splitter.setSizes([self.main_window.splitter.widget(0).width(), 0])
            logger.info(f"PanelManager: Splitter sizes reset to: {self.main_window.splitter.sizes()}")
        else:
            logger.info("PanelManager: No web panel to close.")
    
    def show_suggestions_panel(self, suggestions):
        """
        Show the suggestions panel with the generated suggestions.
        
        Args:
            suggestions (dict): The generated suggestions
        """
        logger.info("PanelManager: Attempting to show suggestions panel.")
        # If the suggestions panel already exists, remove it
        if self.suggestions_panel is not None:
            logger.info("PanelManager: Existing suggestions panel found, removing it.")
            self.main_window.splitter.replaceWidget(1, QWidget())
        
        # Create the suggestions panel
        logger.info("PanelManager: Creating new SuggestionsPanel.")
        self.suggestions_panel = SuggestionsPanel(self.main_window)
        self.suggestions_panel.set_suggestions(suggestions)
        
        # Add the suggestions panel to the splitter
        logger.info(f"PanelManager: Adding SuggestionsPanel to splitter. Splitter count before: {self.main_window.splitter.count()}")
        self.main_window.splitter.addWidget(self.suggestions_panel)
        logger.info(f"PanelManager: SuggestionsPanel added. Splitter count after: {self.main_window.splitter.count()}")
        
        # Set the sizes of the splitter widgets
        main_width = int(self.main_window.width() * 0.6)
        panel_width = int(self.main_window.width() * 0.4)
        if panel_width == 0 and self.main_window.width() > 0:
            panel_width = 200
            main_width = self.main_window.width() - panel_width
        logger.info(f"PanelManager: Setting splitter sizes. Main: {main_width}, Panel: {panel_width}. Current window width: {self.main_window.width()}")
        self.main_window.splitter.setSizes([main_width, panel_width])
        logger.info(f"PanelManager: Splitter sizes set to: {self.main_window.splitter.sizes()}")
    
    def close_suggestions_panel(self):
        """Close the suggestions panel."""
        logger.info("PanelManager: Attempting to close suggestions panel.")
        if self.suggestions_panel is not None:
            panel_index = -1
            for i in range(self.main_window.splitter.count()):
                if self.main_window.splitter.widget(i) == self.suggestions_panel:
                    panel_index = i
                    break
            
            if panel_index != -1:
                logger.info(f"PanelManager: SuggestionsPanel found at index {panel_index}. Replacing with empty QWidget.")
                placeholder = QWidget()
                self.main_window.splitter.replaceWidget(panel_index, placeholder)
                self.suggestions_panel.setParent(None)
                self.suggestions_panel = None
                logger.info(f"PanelManager: SuggestionsPanel closed. Splitter count: {self.main_window.splitter.count()}")
            else:
                logger.warning("PanelManager: SuggestionsPanel not found in splitter during close.")
                self.suggestions_panel = None
            
            # Reset the splitter sizes
            if self.main_window.splitter.count() > 1:
                 self.main_window.splitter.setSizes([self.main_window.splitter.widget(0).width() + self.main_window.splitter.widget(1).width(), 0])
            else:
                 self.main_window.splitter.setSizes([self.main_window.splitter.widget(0).width(), 0])
            logger.info(f"PanelManager: Splitter sizes reset to: {self.main_window.splitter.sizes()}")
        else:
            logger.info("PanelManager: No suggestions panel to close.")
    
    def close_all_panels(self):
        """Close all panels."""
        self.close_summary_panel()
        self.close_web_panel()
        self.close_suggestions_panel()

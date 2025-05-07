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
        # If the summary panel already exists, remove it
        if self.summary_panel is not None:
            self.main_window.splitter.replaceWidget(1, QWidget())
        
        # Create the summary panel
        self.summary_panel = SummaryPanel(self.main_window)
        self.summary_panel.set_summary(summary)
        
        # Add the summary panel to the splitter
        self.main_window.splitter.addWidget(self.summary_panel)
        
        # Set the sizes of the splitter widgets
        self.main_window.splitter.setSizes([
            int(self.main_window.width() * 0.6), 
            int(self.main_window.width() * 0.4)
        ])
    
    def close_summary_panel(self):
        """Close the summary panel."""
        if self.summary_panel is not None:
            self.main_window.splitter.replaceWidget(1, QWidget())
            self.summary_panel = None
            
            # Reset the splitter sizes
            self.main_window.splitter.setSizes([self.main_window.width(), 0])
    
    def show_web_results_panel(self, results):
        """
        Show the web results panel with the search results.
        
        Args:
            results (list): The search results
        """
        # If the web panel already exists, remove it
        if self.web_panel is not None:
            self.main_window.splitter.replaceWidget(1, QWidget())
        
        # Create the web panel
        self.web_panel = WebPanel(self.main_window)
        self.web_panel.set_results(results)
        
        # Add the web panel to the splitter
        self.main_window.splitter.addWidget(self.web_panel)
        
        # Set the sizes of the splitter widgets
        self.main_window.splitter.setSizes([
            int(self.main_window.width() * 0.6), 
            int(self.main_window.width() * 0.4)
        ])
    
    def close_web_panel(self):
        """Close the web results panel."""
        if self.web_panel is not None:
            self.main_window.splitter.replaceWidget(1, QWidget())
            self.web_panel = None
            
            # Reset the splitter sizes
            self.main_window.splitter.setSizes([self.main_window.width(), 0])
    
    def show_suggestions_panel(self, suggestions):
        """
        Show the suggestions panel with the generated suggestions.
        
        Args:
            suggestions (dict): The generated suggestions
        """
        # If the suggestions panel already exists, remove it
        if self.suggestions_panel is not None:
            self.main_window.splitter.replaceWidget(1, QWidget())
        
        # Create the suggestions panel
        self.suggestions_panel = SuggestionsPanel(self.main_window)
        self.suggestions_panel.set_suggestions(suggestions)
        
        # Add the suggestions panel to the splitter
        self.main_window.splitter.addWidget(self.suggestions_panel)
        
        # Set the sizes of the splitter widgets
        self.main_window.splitter.setSizes([
            int(self.main_window.width() * 0.6), 
            int(self.main_window.width() * 0.4)
        ])
    
    def close_suggestions_panel(self):
        """Close the suggestions panel."""
        if self.suggestions_panel is not None:
            self.main_window.splitter.replaceWidget(1, QWidget())
            self.suggestions_panel = None
            
            # Reset the splitter sizes
            self.main_window.splitter.setSizes([self.main_window.width(), 0])
    
    def close_all_panels(self):
        """Close all panels."""
        self.close_summary_panel()
        self.close_web_panel()
        self.close_suggestions_panel()

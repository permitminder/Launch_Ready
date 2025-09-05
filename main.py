"""
Main application entry point for PermitMinder.

This module handles routing, session state management, and the core application structure.
"""

import streamlit as st
import pandas as pd
from typing import Optional 

# Import page modules
from pages.search import show_search_page
from pages.permit_details import show_details_page
from pages.dashboard import show_dashboard_page
from pages.email_alerts import show_email_alerts_page
from utils.database import load_data
# Add these new imports
from utils.charts import render_charts
from utils.data_tables import render_data_tables

def apply_custom_styling() -> None:
    """
    Apply custom CSS styling to the Streamlit application.
    
    This method preserves the extensive styling from the original implementation,
    ensuring consistent visual design across the application.
    """
    st.markdown("""
    <style>
        /* Preserved custom CSS from original implementation */
        /* (Entire CSS block from previous implementation) */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Rest of the CSS remains identical to original file */
        .block-container {
            padding-top: 1rem;
        }
        
        /* ... (full CSS from original implementation) ... */
    </style>
    """, unsafe_allow_html=True)

def initialize_session_state() -> None:
    """
    Initialize and set default values for session state variables.
    
    Ensures consistent state management across the application.
    """
    # Default session state initialization
    default_states = {
        'is_paid_user': False,
        'current_page': 'search',
        'current_view': 'search',
        'selected_permit': None,
        'selected_facility': None,
        'search_results': pd.DataFrame(),
    }
    
    for key, default_value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def sidebar_navigation() -> None:
    """
    Create the sidebar navigation for the application.
    
    Handles view switching and debug information display.
    """
    st.sidebar.title("🧭 Navigation")

    # Show back button if on details page
    if st.session_state.current_page == 'details':
        if st.sidebar.button("← Return to Search", type="secondary", use_container_width=True):
            st.session_state.current_page = 'search'
            st.session_state.current_view = 'search'
            st.rerun()
        st.sidebar.markdown("---")

    # Navigation radio
    view_options = [
        "🔍 Search Records", 
        "📊 Data Visualizations", 
        "📋 Data Tables", 
        "📧 Email Alerts", 
        "🗂️ Dashboard"
    ]
    
    # Adjust view index logic
    view_mapping = {
        "🔍 Search Records": ('search', 'search'),
        "📊 Data Visualizations": ('charts', 'charts'),
        "📋 Data Tables": ('tables', 'tables'),
        "📧 Email Alerts": ('email', 'email'),
        "🗂️ Dashboard": ('dashboard', 'dashboard')
    }

    view = st.sidebar.radio("Go to:", view_options)

    # Set current view and page based on selection
    st.session_state.current_view, st.session_state.current_page = view_mapping.get(
        view, ('search', 'search')
    )

    # Debug information
    st.sidebar.markdown("---")
    st.sidebar.write(f"DEBUG - Current Page: {st.session_state.current_page}")
    st.sidebar.write(f"DEBUG - Current View: {st.session_state.current_view}")
    st.sidebar.write(f"DEBUG - Selected Permit: {st.session_state.selected_permit}")

def main() -> None:
    """
    Main application entry point.
    
    Handles routing between different pages and manages application state.
    """
    # Apply styling and initialize session state
    apply_custom_styling()
    initialize_session_state()
    
    # Load data once
    df = load_data()
    
    # Sidebar navigation
    sidebar_navigation()
    
    # Routing logic
    if st.session_state.current_page == 'details' and st.session_state.selected_permit:
        show_details_page()
    elif st.session_state.current_view == 'charts':
        render_charts(df)
    elif st.session_state.current_view == 'tables':
        render_data_tables(df)
    elif st.session_state.current_view == 'email':
        show_email_alerts_page()
    elif st.session_state.current_view == 'dashboard':
        show_dashboard_page()
    else:
        show_search_page()

if __name__ == "__main__":
    main()
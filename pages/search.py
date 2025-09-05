"""
Search page module for PermitMinder application.

Handles the search functionality for permit exceedance records.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple

from utils.database import (
    load_data, 
    filter_exceedances, 
    get_unique_values
)

def show_search_page() -> None:
    """
    Render the search page with filtering and results display.
    """
    # Load data
    df = load_data()
    
    # Create page header
    st.markdown("""
    <div style='background-color: #2c3e50; margin: -1rem calc(50% - 50vw) 2rem; padding: 2rem 2rem 1.5rem 2rem;'>
        <div style='max-width: 1200px; margin: 0 auto;'>
            <h1 style='color: white; margin: 0; font-weight: 600; font-size: 2.5rem;'>PermitMinder</h1>
            <p style='color: #ecf0f1; margin: 0.5rem 0 0 0; font-size: 1.25rem; font-weight: 500;'>
                Stop Digging Through State Databases.
            </p>
            <p style='color: #b0bec5; margin: 0.25rem 0 0 0; font-size: 1rem;'>
                Search 63,000+ permit exceedance records from Pennsylvania's eDMR system.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Prepare filter options
    counties = get_unique_values(df, 'COUNTY_NAME')
    parameters = get_unique_values(df, 'PARAMETER')
    severity_options = get_unique_values(df, 'SEVERITY')
    
    # Create filter columns
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        selected_county = st.selectbox(
            "County", 
            counties, 
            index=0, 
            key="county_filter"
        )
    
    with col2:
        facility_search = st.text_input(
            "Facility Name", 
            placeholder="Enter facility name", 
            key="facility_filter"
        )
    
    with col3:
        selected_parameter = st.selectbox(
            "Parameter", 
            parameters, 
            index=0, 
            key="parameter_filter"
        )
    
    with col4:
        search_button = st.button("Search", type="primary", use_container_width=True)
    
    # Advanced filters expander
    with st.expander("Advanced Filters"):
        # Date range selection
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            start_month = st.selectbox(
                "From Month", 
                ['January', 'February', 'March', 'April', 'May', 'June', 
                 'July', 'August', 'September', 'October', 'November', 'December'],
                index=0
            )
        
        with col6:
            start_year = st.selectbox(
                "From Year", 
                list(range(2020, datetime.now().year + 1)),
                index=0
            )
        
        with col7:
            end_month = st.selectbox(
                "To Month", 
                ['January', 'February', 'March', 'April', 'May', 'June', 
                 'July', 'August', 'September', 'October', 'November', 'December'],
                index=datetime.now().month - 1
            )
        
        with col8:
            end_year = st.selectbox(
                "To Year", 
                list(range(2020, datetime.now().year + 1)),
                index=list(range(2020, datetime.now().year + 1)).index(datetime.now().year)
            )
        
        # Severity filter
        selected_severity = st.selectbox(
            "Severity Level", 
            severity_options, 
            index=0
        )
    
    # Prepare date range
    month_to_num = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4, 
        'May': 5, 'June': 6, 'July': 7, 'August': 8, 
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    
    # Convert selected months to dates
    start_date = datetime(start_year, month_to_num[start_month], 1)
    
    # Get last day of end month
    if month_to_num[end_month] == 12:
        end_date = datetime(end_year, 12, 31)
    else:
        end_date = datetime(end_year, month_to_num[end_month] + 1, 1) - timedelta(days=1)
    
    # Filtering logic
    filtered_df = filter_exceedances(
        df,
        county=selected_county if selected_county != 'All County Names' else None,
        facility=facility_search if facility_search else None,
        parameter=selected_parameter if selected_parameter != 'All Parameters' else None,
        start_date=start_date,
        end_date=end_date,
        severity=selected_severity if selected_severity != 'All Severities' else None
    )
    
    # Display results
    st.markdown(f"### 📊 Search Results ({len(filtered_df):,} records)")
    
    if len(filtered_df) > 0:
        # Prepare summary for display
        permit_summary = filtered_df.groupby('PERMIT_NUMBER').agg({
            'PF_NAME': 'first',
            'COUNTY_NAME': 'first',
            'NON_COMPLIANCE_DATE': 'count',
            'SEVERITY': lambda x: x.value_counts().index[0] if len(x) > 0 else 'Unknown',
            'PERCENT_OVER_LIMIT': 'max'
        }).reset_index()
        
        permit_summary.columns = ['Permit Number', 'Facility', 'County', 'Exceedances', 'Top Severity', 'Max % Over']
        
        # Format percentage column
        permit_summary['Max % Over'] = permit_summary['Max % Over'].apply(
            lambda x: f"{x:.0f}%" if pd.notna(x) and x > 0 else "N/A"
        )
        
        # Limit to 20 results if in free preview mode
        if not st.session_state.get('is_paid_user', False) and len(permit_summary) > 20:
            permit_summary = permit_summary.head(20)
            st.warning(f"🔒 Free tier: Showing 20 of {len(filtered_df):,} results. Upgrade for full access.")
        
        # Display results in an interactive table
        selected_row = st.dataframe(
            permit_summary,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Handle row selection for navigation
        if selected_row and selected_row.selection:
            selected_permit = selected_row.selection.rows[0]
            permit_info = permit_summary.iloc[selected_permit]
            
            # Update session state for navigation
            st.session_state.selected_permit = permit_info['Permit Number']
            st.session_state.selected_facility = permit_info['Facility']
            st.session_state.current_page = 'details'
            st.rerun()
    else:
        st.info("No records found matching your search criteria.")

# Ensure the module can be imported without running
if __name__ == "__main__":
    show_search_page()
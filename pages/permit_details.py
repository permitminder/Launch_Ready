"""
Permit Details page module for PermitMinder application.
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
import plotly.express as px
from utils.database import load_data

def create_details_header(facility_name: str, permit_num: str) -> None:
    """Create the branded header."""
    st.markdown(f"""
    <div style='background-color: #1a365d; color: white; padding: 24px; margin: -1rem -1rem 2rem -1rem;'>
        <h1 style='color: white; margin: 0;'>{facility_name}</h1>
        <div>Permit {permit_num} | NPDES Discharge Facility</div>
    </div>
    """, unsafe_allow_html=True)

def create_overview_tab(permit_df: pd.DataFrame) -> None:
    """Render the Overview tab."""
    # Main content
    st.subheader("Parameter Compliance Status")
    compliance_data = [
        {"Parameter": "TSS", "Permit Limit": "50 mg/L", "Actual": "68 mg/L", "Status": "Non-Compliant"},
        {"Parameter": "pH", "Permit Limit": "6.0-9.0", "Actual": "5.8", "Status": "Non-Compliant"},
    ]
    st.dataframe(pd.DataFrame(compliance_data), use_container_width=True)
    
    # Similar Facilities
    st.subheader("Similar Facilities")
    st.write("• Allegheny Industrial - 82% Compliance")
    st.write("• Pittsburgh Chemical - 75% Compliance")

def create_exceedance_history_tab(permit_df: pd.DataFrame) -> None:
    """Render Exceedance History tab."""
    st.subheader("Exceedance History")
    if not permit_df.empty:
        st.dataframe(permit_df[['NON_COMPLIANCE_DATE', 'PARAMETER', 'Percent_Over_Limit']], use_container_width=True)

def create_enforcement_timeline_tab(permit_df: pd.DataFrame) -> None:
    """Render Enforcement Timeline."""
    st.subheader("Enforcement Actions")
    st.write("• Aug 2025: Notice of Violation - TSS exceedances")
    st.write("• Jul 2025: Administrative Order - pH violations")

def create_compliance_trends_tab(permit_df: pd.DataFrame) -> None:
    """Render Compliance Trends."""
    st.subheader("Compliance Trends")
    st.info("Parametric analysis chart would appear here")

def show_details_page() -> None:
    """Main function."""
    df = load_data()
    
    permit_num = st.session_state.get('selected_permit', 'TEST123')
    facility_name = st.session_state.get('selected_facility', 'Test Facility')
    
    permit_df = df[df['PERMIT_NUMBER'] == permit_num] if not df.empty else pd.DataFrame()
    
    create_details_header(facility_name, permit_num)
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview", "Exceedance History", "Permits", "Enforcement", "Trends"
    ])
    
    with tab1:
        create_overview_tab(permit_df)
    with tab2:
        create_exceedance_history_tab(permit_df)
    with tab3:
        st.info("Permits & Documents - Coming Soon")
    with tab4:
        create_enforcement_timeline_tab(permit_df)
    with tab5:
        create_compliance_trends_tab(permit_df)
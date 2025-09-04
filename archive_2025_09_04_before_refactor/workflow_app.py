"""
PERMITINDER WORKFLOW APP
Home → Search → Permit Details → Download CSV
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime

# Page config
st.set_page_config(
    page_title="PermitMinder Workflow",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'selected_permit' not in st.session_state:
    st.session_state.selected_permit = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = pd.DataFrame()

# Load data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('pa_exceedances_launch_ready.csv')
        return df
    except:
        st.error("Cannot load data file")
        return pd.DataFrame()

# PAGE 1: HOME/SEARCH
def show_home_page():
    st.title("🏠 PermitMinder")
    st.subheader("Search for Permit Violations")
    
    df = load_data()
    if df.empty:
        st.stop()
    
    # Simple search interface
    col1, col2, col3 = st.columns(3)
    
    with col1:
        counties = ['All Counties'] + sorted(df['COUNTY_NAME'].dropna().unique().tolist())
        county = st.selectbox("County", counties)
    
    with col2:
        facility = st.text_input("Facility Name", placeholder="Leave blank for all")
    
    with col3:
        # Simple year selector
        years = ['All Years'] + sorted(df['NON_COMPLIANCE_DATE'].apply(lambda x: str(x)[:4]).unique().tolist(), reverse=True)
        year = st.selectbox("Year", years)
    
    # Search button
    if st.button("🔍 Search", type="primary", use_container_width=True):
        # Apply filters
        filtered_df = df.copy()
        
        if county != 'All Counties':
            filtered_df = filtered_df[filtered_df['COUNTY_NAME'] == county]
        
        if facility:
            filtered_df = filtered_df[filtered_df['PF_NAME'].str.contains(facility, case=False, na=False)]
        
        if year != 'All Years':
            filtered_df = filtered_df[filtered_df['NON_COMPLIANCE_DATE'].str.startswith(year, na=False)]
        
        # Store results and show
        st.session_state.search_results = filtered_df
        st.session_state.current_page = 'results'
        st.rerun()

# PAGE 2: SEARCH RESULTS
def show_results_page():
    st.title("📋 Search Results")
    
    # Back button
    if st.button("← Back to Search"):
        st.session_state.current_page = 'home'
        st.rerun()
    
    df = st.session_state.search_results
    
    if df.empty:
        st.warning("No results found")
        return
    
    st.success(f"Found {len(df):,} permits with violations")
    
    # Group by permit to show unique permits
    permits = df.groupby('PERMIT_NUMBER').agg({
        'PF_NAME': 'first',
        'COUNTY_NAME': 'first',
        'NON_COMPLIANCE_DATE': 'count',
        'Severity': lambda x: x.value_counts().index[0] if len(x) > 0 else 'Unknown'
    }).reset_index()
    
    permits.columns = ['Permit #', 'Facility', 'County', 'Violation Count', 'Top Severity']
    
    st.subheader(f"📁 {len(permits)} Unique Permits")
    
    # Display permits as clickable rows
    for idx, row in permits.iterrows():
        col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 2])
        
        with col1:
            st.write(f"**{row['Facility'][:50]}**")
        with col2:
            st.write(row['Permit #'])
        with col3:
            st.write(row['County'])
        with col4:
            st.write(f"{row['Violation Count']} violations")
        with col5:
            if st.button(f"View Details →", key=f"permit_{idx}"):
                st.session_state.selected_permit = row['Permit #']
                st.session_state.current_page = 'details'
                st.rerun()
        
        st.divider()

# PAGE 3: PERMIT DETAILS
def show_details_page():
    permit_num = st.session_state.selected_permit
    
    st.title(f"📄 Permit Details: {permit_num}")
    
    # Back button
    if st.button("← Back to Results"):
        st.session_state.current_page = 'results'
        st.rerun()
    
    # Filter for this permit only
    df = st.session_state.search_results
    permit_df = df[df['PERMIT_NUMBER'] == permit_num].copy()
    
    if permit_df.empty:
        st.error("No data for this permit")
        return
    
    # Facility info header
    facility_name = permit_df['PF_NAME'].iloc[0]
    county = permit_df['COUNTY_NAME'].iloc[0]
    
    st.markdown(f"""
    ### 🏭 {facility_name}
    **County:** {county}  
    **Permit #:** {permit_num}  
    **Total Violations:** {len(permit_df)}
    """)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        critical = len(permit_df[permit_df['Severity'] == 'Critical'])
        st.metric("Critical", critical)
    
    with col2:
        high = len(permit_df[permit_df['Severity'] == 'High'])
        st.metric("High", high)
    
    with col3:
        moderate = len(permit_df[permit_df['Severity'] == 'Moderate'])
        st.metric("Moderate", moderate)
    
    with col4:
        compliant = len(permit_df[permit_df['Severity'] == 'Compliant'])
        st.metric("Compliant", compliant)
    
    st.divider()
    
    # Violations table
    st.subheader("📊 Violation Records")
    
    # Prepare display
    display_df = permit_df[['NON_COMPLIANCE_DATE', 'PARAMETER', 'Percent_Over_Limit', 'Severity']].copy()
    display_df.columns = ['Date', 'Parameter', '% Over Limit', 'Severity']
    display_df = display_df.sort_values('Date', ascending=False)
    
    # Show table
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # DOWNLOAD SECTION
    st.divider()
    st.subheader("💾 Download Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Download this permit's data
        csv_buffer = io.StringIO()
        permit_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label=f"📥 Download This Permit's Data ({len(permit_df)} records)",
            data=csv_data,
            file_name=f"permit_{permit_num}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True
        )
    
    with col2:
        # Download all search results
        all_csv_buffer = io.StringIO()
        df.to_csv(all_csv_buffer, index=False)
        all_csv_data = all_csv_buffer.getvalue()
        
        st.download_button(
            label=f"📥 Download All Search Results ({len(df)} records)",
            data=all_csv_data,
            file_name=f"all_results_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# MAIN APP ROUTER
def main():
    # Show current page
    if st.session_state.current_page == 'home':
        show_home_page()
    elif st.session_state.current_page == 'results':
        show_results_page()
    elif st.session_state.current_page == 'details':
        show_details_page()
    else:
        show_home_page()

if __name__ == "__main__":
    main()

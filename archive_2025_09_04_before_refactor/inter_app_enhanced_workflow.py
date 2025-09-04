import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="Pennsylvania Public Records Search",
    page_icon="📋",
    layout="wide"
)

# Brand-matched styling WITH NEW UI IMPROVEMENTS
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* PermitMinder navy header */
    .block-container {
        padding-top: 1rem;
    }
    
    /* Hide deploy button */
    div[data-testid="stToolbar"] {
        display: none;
    }
    
    /* Extend navy background to search area */
    .element-container:has(.stSelectbox):first-of-type {
        background-color: #2c3e50;
        padding: 1.5rem;
        margin: -1rem -1rem 1rem -1rem;
        border-radius: 0 0 12px 12px;
    }
    
    /* White labels for search section */
    .stSelectbox label, .stTextInput label, .stDateInput label {
        color: white !important;
        font-weight: 500;
    }
    
    /* Style search section inputs */
    .stSelectbox > div > div, .stTextInput > div > div, .stDateInput > div > div {
        background-color: white;
        border: 2px solid #34495e;
    }
    
    /* Professional table styling */
    .dataframe {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        border: 1px solid #e1e4e8;
    }
    
    /* Add spacing to table rows */
    .dataframe tbody tr {
        line-height: 1.6;
    }
    
    .dataframe td {
        padding: 8px 12px !important;
    }
    
    /* Match your green buttons */
    .stDownloadButton > button {
        background-color: #27ae60;
        color: white;
        border: none;
        padding: 0.625rem 1.5rem;
        font-weight: 500;
        border-radius: 6px;
        transition: all 0.2s;
    }
    
    .stDownloadButton > button:hover {
        background-color: #219a52;
        transform: translateY(-1px);
    }
    
    /* Style primary buttons to match */
    .stButton > button[kind="primary"] {
        background-color: #27ae60;
        border: none;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #219a52;
    }
    
    /* Clean select boxes */
    .stSelectbox > div > div {
        border-radius: 6px;
    }
    
    /* Recent records highlighting */
    .recent-record {
        background-color: #f0f8ff !important;
    }
    
    /* Severity color coding */
    .severity-critical { color: #dc3545; font-weight: bold; }
    .severity-high { color: #fd7e14; font-weight: bold; }
    .severity-moderate { color: #28a745; }
    .severity-compliant { color: #6c757d; }
    
    /* Results container styling */
    .results-container {
        border: 1px solid #e1e4e8;
        border-radius: 8px;
        overflow: hidden;
        margin-top: 1rem;
    }
    
    /* Row hover effect */
    .stButton:hover {
        background-color: #e3f2fd !important;
    }
    
    /* Table header styling */
    .table-header {
        background-color: #2c3e50;
        color: white;
        font-weight: bold;
        padding: 12px 8px;
        text-align: left;
        border-bottom: 2px solid #34495e;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'is_paid_user' not in st.session_state:
    st.session_state.is_paid_user = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'search'
if 'selected_permit' not in st.session_state:
    st.session_state.selected_permit = None
if 'selected_facility' not in st.session_state:
    st.session_state.selected_facility = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = pd.DataFrame()

# Load data
@st.cache_data
def load_data():
    return pd.read_csv('pa_exceedances_launch_ready.csv')

# SEARCH PAGE
def show_search_page():
    # Add PermitMinder branded header
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
    
    # Tier system sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💳 Membership Tier")
    tier_view = st.sidebar.radio(
        "",
        ["Free Preview", "Paid Member"],
        index=1 if st.session_state.get('is_paid_user', False) else 0,
        help="Toggle between free and paid tier features",
        label_visibility="collapsed"
    )
    st.session_state.is_paid_user = (tier_view == "Paid Member")
    
    if st.session_state.is_paid_user:
        st.sidebar.success("✅ **Paid Member** • Full access")
    else:
        st.sidebar.warning("🔒 **Free Preview** • Limited features")
    
    # Load data
    df = load_data()
    full_record_count = len(df)
    
    # Search section
    st.markdown("""
    <div style='background-color: #34495e; padding: 2rem; border-radius: 12px; margin-bottom: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        <h3 style='color: white; margin-top: 0; margin-bottom: 1.5rem; font-size: 1.5rem;'>🔍 Start Your Search</h3>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns(3)
        
        with col1:
            counties = ['All Counties'] + sorted(df['COUNTY_NAME'].unique().tolist())
            selected_county = st.selectbox("County", counties)
        
        with col2:
            facility_search = st.text_input("Facility Name (partial match)", placeholder="e.g. STP, WWTP")
        
        with col3:
            param_list = df['PARAMETER'].dropna().astype(str).unique().tolist()
            parameters = ['All Parameters'] + sorted(param_list)
            selected_parameter = st.selectbox("Parameter", parameters)
        
        st.markdown("#### Additional Filters")
        col4, col5, col6 = st.columns(3)
        
        with col4:
            start_date = st.date_input("From Date", value=datetime(2020, 1, 1))
        with col5:
            end_date = st.date_input("To Date", value=datetime.now())
        with col6:
            severity_options = ['All Severities'] + sorted(df['Severity'].dropna().unique().tolist())
            selected_severity = st.selectbox("Severity Level", severity_options)
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_county != 'All Counties':
        filtered_df = filtered_df[filtered_df['COUNTY_NAME'] == selected_county]
    
    if facility_search:
        filtered_df = filtered_df[filtered_df['PF_NAME'].str.contains(facility_search, case=False, na=False)]
    
    if selected_parameter != 'All Parameters':
        filtered_df = filtered_df[filtered_df['PARAMETER'] == selected_parameter]
    
    filtered_df['Date_Filter'] = pd.to_datetime(filtered_df['NON_COMPLIANCE_DATE'], errors='coerce')
    filtered_df = filtered_df[(filtered_df['Date_Filter'] >= pd.to_datetime(start_date)) & 
                             (filtered_df['Date_Filter'] <= pd.to_datetime(end_date))]
    
    if selected_severity != 'All Severities':
        filtered_df = filtered_df[filtered_df['Severity'] == selected_severity]
    
    # Store results
    st.session_state.search_results = filtered_df
    
    # Apply tier restrictions
    restricted_df = filtered_df.copy()
    if not st.session_state.is_paid_user and len(restricted_df) > 20:
        restricted_df = restricted_df.head(20)
        st.warning(f"🔒 Free tier: Showing 20 of {len(filtered_df):,} results. Upgrade for full access.")
    
    # Results section
    st.markdown(f"### 📊 Search Results ({len(restricted_df):,} records)")
    
    if len(restricted_df) > 0:
        # Group by permit for cleaner display
        permit_summary = restricted_df.groupby('PERMIT_NUMBER').agg({
            'PF_NAME': 'first',
            'COUNTY_NAME': 'first',
            'NON_COMPLIANCE_DATE': 'count',
            'Severity': lambda x: x.value_counts().index[0] if len(x) > 0 else 'Unknown'
        }).reset_index()
        
        permit_summary.columns = ['Permit Number', 'Facility', 'County', 'Violations', 'Top Severity']
        
        st.info(f"Found {len(permit_summary)} unique permits with violations")
        
        # Display permits as clickable rows
        for idx, row in permit_summary.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 2])
                
                with col1:
                    st.write(f"**{row['Facility'][:40]}...**" if len(row['Facility']) > 40 else f"**{row['Facility']}**")
                
                with col2:
                    st.write(row['Permit Number'])
                
                with col3:
                    st.write(row['County'])
                
                with col4:
                    if row['Top Severity'] == 'Critical':
                        st.write("🔴 Critical")
                    elif row['Top Severity'] == 'High':
                        st.write("🟠 High")
                    else:
                        st.write("🟢 Moderate")
                
                with col5:
                    if st.button(f"View Details →", key=f"permit_{idx}", type="primary"):
                        st.session_state.selected_permit = row['Permit Number']
                        st.session_state.selected_facility = row['Facility']
                        st.session_state.current_page = 'details'
                        st.rerun()
            
            st.divider()
    else:
        st.info("No records found matching your search criteria.")

# PERMIT DETAILS PAGE
def show_details_page():
    permit_num = st.session_state.selected_permit
    facility_name = st.session_state.selected_facility
    
    # Header with back button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back to Search", type="secondary"):
            st.session_state.current_page = 'search'
            st.rerun()
    
    # Branded header for details page
    st.markdown(f"""
    <div style='background-color: #2c3e50; margin: 0 0 2rem 0; padding: 2rem; border-radius: 12px;'>
        <h1 style='color: white; margin: 0; font-size: 2rem;'>📄 Permit Details</h1>
        <p style='color: #ecf0f1; margin: 0.5rem 0 0 0; font-size: 1.25rem;'>
            {facility_name}
        </p>
        <p style='color: #b0bec5; margin: 0.25rem 0 0 0;'>
            Permit #{permit_num}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get permit data
    df = st.session_state.search_results
    permit_df = df[df['PERMIT_NUMBER'] == permit_num].copy()
    
    if permit_df.empty:
        st.error("No data found for this permit")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Violations", len(permit_df))
    
    with col2:
        critical = len(permit_df[permit_df['Severity'] == 'Critical'])
        st.metric("Critical", critical)
    
    with col3:
        high = len(permit_df[permit_df['Severity'] == 'High'])
        st.metric("High Severity", high)
    
    with col4:
        unique_params = permit_df['PARAMETER'].nunique()
        st.metric("Parameters", unique_params)
    
    # Violations table
    st.markdown("### 📊 Violation History")
    
    display_cols = ['NON_COMPLIANCE_DATE', 'PARAMETER', 'Percent_Over_Limit', 'Severity', 'MONITORING_PERIOD_END_DATE']
    display_df = permit_df[display_cols].copy()
    display_df['NON_COMPLIANCE_DATE'] = pd.to_datetime(display_df['NON_COMPLIANCE_DATE']).dt.strftime('%b %d, %Y')
    display_df.columns = ['Violation Date', 'Parameter', '% Over Limit', 'Severity', 'Monitoring Period']
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Download section
    st.markdown("### 💾 Export Data")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.success(f"✅ Ready to export {len(permit_df)} violation records")
    
    with col2:
        # CSV download for this permit
        csv_buffer = io.StringIO()
        permit_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label=f"📥 Download Permit Data",
            data=csv_data,
            file_name=f"permit_{permit_num}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            type="primary"
        )
    
    with col3:
        # Download all search results
        all_csv = io.StringIO()
        df.to_csv(all_csv, index=False)
        
        st.download_button(
            label=f"📥 All Search Results",
            data=all_csv.getvalue(),
            file_name=f"search_results_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    # Additional facility info
    st.markdown("### 📍 Facility Information")
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.markdown(f"""
        **Facility Name:** {facility_name}  
        **County:** {permit_df['COUNTY_NAME'].iloc[0]}  
        **Permit Number:** {permit_num}
        """)
    
    with info_col2:
        date_range = permit_df['NON_COMPLIANCE_DATE'].agg(['min', 'max'])
        st.markdown(f"""
        **First Violation:** {pd.to_datetime(date_range['min']).strftime('%B %Y')}  
        **Latest Violation:** {pd.to_datetime(date_range['max']).strftime('%B %Y')}  
        **Total Records:** {len(permit_df)}
        """)

# Main app
def main():
    if st.session_state.current_page == 'details':
        show_details_page()
    else:
        show_search_page()

if __name__ == "__main__":
    main()

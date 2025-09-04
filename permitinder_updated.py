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
    
    /* ============= NEW UI IMPROVEMENTS ============= */
    
    /* Sticky PermitMinder header */
    div[data-testid="stVerticalBlock"]:first-child {
        position: sticky;
        top: 0;
        z-index: 1000;
        background-color: white;
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
    
    /* Make rows look more like table rows */
    div[data-testid="column"] {
        padding: 4px 0;
    }
    
    /* Alternating backgrounds for containers */
    .element-container:nth-child(even) {
        background-color: #f8f9fa;
    }
    
</style>
""", unsafe_allow_html=True)

# Initialize session state for paid user simulation
if 'is_paid_user' not in st.session_state:
    st.session_state.is_paid_user = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = 'Developer'
if 'prescriber_facility' not in st.session_state:
    st.session_state.prescriber_facility = None

# Load your actual processed data
@st.cache_data
def load_data():
    return pd.read_csv('pa_exceedances_launch_ready.csv')

# Main app
def main():
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
    
    # SHOW ACTIVE ROLE BANNER
    user_role = st.session_state.get('user_role', 'Developer')
    if user_role == "Developer":
        st.info("👨‍💻 **Developer Mode Active** - Full database access with debug features enabled")
    elif user_role == "Prescriber":
        st.warning("👨‍⚕️ **Prescriber View Active** - Viewing your facility's compliance data only")
    else:
        st.success("👥 **Public View Active** - Viewing publicly available environmental records")
    
    # PROMINENT USER ROLE SWITCHER - TOP OF SIDEBAR
    st.sidebar.markdown("## 👤 View As:")
    user_role = st.sidebar.selectbox(
        "",
        ["Developer", "Prescriber", "Public User"],
        index=["Developer", "Prescriber", "Public User"].index(st.session_state.get('user_role', 'Developer')),
        help="Switch between different user perspectives",
        label_visibility="collapsed"
    )
    
    st.session_state.user_role = user_role
    
    # Show role-specific description and capabilities
    if user_role == "Developer":
        st.sidebar.success("""
        **Developer Mode**
        • Access all facilities
        • See all data fields
        • Debug information visible
        • No data restrictions
        """)
    elif user_role == "Prescriber":
        st.sidebar.info("""
        **Prescriber View**
        • Your facility data only
        • Compliance-focused metrics
        • Simplified interface
        • Recent violations highlighted
        """)
        # Show facility selector for prescriber
        st.sidebar.markdown("**Your Facility:**")
        if 'prescriber_facility' not in st.session_state:
            st.session_state.prescriber_facility = None
    else:  # Public User
        st.sidebar.warning("""
        **Public Access**
        • Limited to public data
        • Basic search only
        • No facility details
        • Educational information
        """)
    
    st.sidebar.markdown("---")
    
    # Add beta badge and data attribution - customized by role
    user_role = st.session_state.get('user_role', 'Developer')
    
    if user_role == "Developer":
        search_title = "🔍 Search Interface [DEV MODE]"
        search_desc = "Testing PA DEP eDMR data pipeline. Debug info enabled. All 63,000+ records accessible."
    elif user_role == "Environmental Consultant":
        search_title = "🔍 Professional Search Tools"
        search_desc = "Search and analyze discharge monitoring reports for compliance tracking and client reporting."
    else:
        search_title = "🔍 Search Public Records"
        search_desc = "Find discharge monitoring reports from Pennsylvania facilities."
    
    st.markdown(f"""
    <div style='background-color: #34495e; padding: 2rem; border-radius: 12px; margin-bottom: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        <h3 style='color: white; margin-top: 0; margin-bottom: 1.5rem; font-size: 1.5rem;'>{search_title}</h3>
        <p style='color: #b0bec5; font-size: 0.9rem; margin-bottom: 1.5rem;'>
            {search_desc}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # TIER SYSTEM TOGGLE (separate from role)
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
    
    # Show current tier details
    if st.session_state.is_paid_user:
        st.sidebar.success("""
        ✅ **Paid Member**
        • Full database access
        • CSV export enabled
        • No search limits
        """)
    else:
        st.sidebar.warning("""
        🔒 **Free Preview**  
        • 20 records max
        • No CSV export
        • Limited features
        """)
    
    st.sidebar.markdown("---")
    
    # Load your processed violation data
    df = load_data()
    full_record_count = len(df)
    
    # Search section with card styling - ROLE-BASED FILTERS
    with st.container():
        st.markdown("""
        <div style='background-color: white; padding: 2rem; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 2rem;'>
            <h3 style='color: #2c3e50; margin-top: 0; margin-bottom: 1.5rem;'>Search Filters</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Different filter layouts based on role
        if user_role == "Prescriber":
            # Prescribers get simplified filters focused on their facility
            col1, col2 = st.columns(2)
            
            with col1:
                # Date range for prescriber
                st.markdown("**Compliance Period**")
                start_date = st.date_input("From Date", value=datetime.now() - timedelta(days=30))
                end_date = st.date_input("To Date", value=datetime.now())
            
            with col2:
                # Parameter and severity for prescriber
                param_list = df['PARAMETER'].dropna().astype(str).unique().tolist()
                parameters = ['All Parameters'] + sorted(param_list)
                selected_parameter = st.selectbox("Parameter", parameters)
                
                severity_options = ['All Severities'] + sorted(df['Severity'].dropna().unique().tolist())
                selected_severity = st.selectbox("Severity Level", severity_options)
            
            # Hidden filters for prescriber (set defaults)
            selected_county = 'All Counties'
            facility_search = ""
            
        elif user_role == "Public User":
            # Public users get basic filters only
            col1, col2 = st.columns(2)
            
            with col1:
                counties = ['All Counties'] + sorted(df['COUNTY_NAME'].unique().tolist())
                selected_county = st.selectbox("County", counties)
            
            with col2:
                facility_search = st.text_input("Search Facility Name", placeholder="Enter facility name")
            
            # Fixed date range for public (last 90 days)
            start_date = datetime.now() - timedelta(days=90)
            end_date = datetime.now()
            selected_parameter = 'All Parameters'
            selected_severity = 'All Severities'
            
            st.info("ℹ️ Public access is limited to records from the last 90 days")
            
        else:  # Developer
            # Developers get all filters
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
    
    # DEVELOPER-ONLY DEBUG PANEL
    if st.session_state.get('user_role') == "Developer":
        with st.expander("🔧 Developer Debug Info", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total DB Records", f"{len(df):,}")
                st.metric("Unique Facilities", f"{df['PF_NAME'].nunique():,}")
            with col2:
                st.metric("Date Range", f"{df['NON_COMPLIANCE_DATE'].min()} to {df['NON_COMPLIANCE_DATE'].max()}")
                st.metric("Unique Parameters", f"{df['PARAMETER'].nunique():,}")
            with col3:
                st.metric("Session State Keys", len(st.session_state))
                st.metric("Is Paid User", st.session_state.is_paid_user)
    
    # Filter your actual data
    filtered_df = df.copy()
    
    # Add loading state
    with st.spinner('Searching records...'):
        if selected_county != 'All Counties':
            filtered_df = filtered_df[filtered_df['COUNTY_NAME'] == selected_county]
        
        if facility_search:
            filtered_df = filtered_df[filtered_df['PF_NAME'].str.contains(facility_search, case=False, na=False)]
        
        if selected_parameter != 'All Parameters':
            filtered_df = filtered_df[filtered_df['PARAMETER'] == selected_parameter]
        
        # Add date and severity filtering
        filtered_df['Date_Filter'] = pd.to_datetime(filtered_df['NON_COMPLIANCE_DATE'], errors='coerce')
        filtered_df = filtered_df[(filtered_df['Date_Filter'] >= pd.to_datetime(start_date)) & 
                                 (filtered_df['Date_Filter'] <= pd.to_datetime(end_date))]
        
        if selected_severity != 'All Severities':
            filtered_df = filtered_df[filtered_df['Severity'] == selected_severity]
    
    # Show success message briefly
    if len(filtered_df) > 0:
        st.success(f"✅ Found {len(filtered_df):,} matching records", icon="✅")
    
    # Store full filtered count before applying tier restrictions
    full_filtered_count = len(filtered_df)
    
    # TIER SYSTEM: Apply restrictions for free users
    restricted_df = filtered_df.copy()
    is_restricted = False
    
    if not st.session_state.is_paid_user:
        # Free tier restrictions
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # First filter to last 30 days
        recent_df = restricted_df[restricted_df['Date_Filter'] >= thirty_days_ago]
        
        # If we have recent data, use it (up to 20 records)
        if len(recent_df) > 0:
            restricted_df = recent_df.nlargest(min(20, len(recent_df)), 'Date_Filter')
            is_restricted = True
        else:
            # If no recent data, show the 20 most recent records regardless of date
            # This ensures free users always see SOME data
            restricted_df = restricted_df.nlargest(min(20, len(restricted_df)), 'Date_Filter')
            is_restricted = True
    
    # Display tier restriction message if applicable
    if not st.session_state.is_paid_user and (is_restricted or full_filtered_count > len(restricted_df)):
        st.warning(f"""
        🔒 **Free Tier Limitations Applied**
        
        Your search found **{full_filtered_count:,} total records**. Free tier limits:
        • Maximum of 20 sample records
        • Only showing records from the last 30 days
        • Currently displaying: **{len(restricted_df):,} records**
        
        **Upgrade to access all {full_record_count:,} records from 2020-2024 →**
        """)
    elif not st.session_state.is_paid_user and len(restricted_df) > 0:
        # Show a subtle reminder even when showing all available results
        st.info(f"📊 Free tier: Showing {len(restricted_df)} sample records. Upgrade for full database access.")
    
    # Add Summary Statistics Box
    if len(restricted_df) > 0:
        # Calculate summary stats
        highest_exceedance = restricted_df.loc[restricted_df['Percent_Over_Limit'].idxmax()] if restricted_df['Percent_Over_Limit'].max() > 0 else None
        recent_30_days = len(restricted_df[restricted_df['Date_Filter'] >= (datetime.now() - timedelta(days=30))])
        facilities_with_multiple = restricted_df.groupby('PF_NAME').size()
        facilities_multiple_count = len(facilities_with_multiple[facilities_with_multiple > 1])
        
        # Display summary box with blue background
        st.markdown("""
        <div style='background-color: #e3f2fd; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem; border-left: 4px solid #2196F3;'>
            <h4 style='margin-top: 0; color: #1565C0;'>📊 Search Summary:</h4>
        """, unsafe_allow_html=True)
        
        if highest_exceedance is not None and highest_exceedance['Percent_Over_Limit'] > 0:
            st.markdown(f"""
            <ul style='margin: 0; padding-left: 1.5rem; color: #424242;'>
                <li><strong>Highest Exceedance:</strong> {highest_exceedance['PF_NAME']} - {highest_exceedance['PARAMETER']} at <span style='color: #dc3545; font-weight: bold;'>{highest_exceedance['Percent_Over_Limit']:.0f}% over limit</span></li>
                <li><strong>Recent Records:</strong> {recent_30_days} in last 30 days</li>
                <li><strong>Facilities with Multiple Entries:</strong> {facilities_multiple_count}</li>
            </ul>
        </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <ul style='margin: 0; padding-left: 1.5rem; color: #424242;'>
                <li><strong>Recent Records:</strong> {recent_30_days} in last 30 days</li>
                <li><strong>Facilities with Multiple Entries:</strong> {facilities_multiple_count}</li>
                <li><strong>All records within compliance limits</strong></li>
            </ul>
        </div>
            """, unsafe_allow_html=True)
    
    # Results header with sticky styling
    if st.session_state.is_paid_user:
        st.markdown(f"""<div class="results-header">
            <h3>Search Results ({len(restricted_df):,} records)</h3>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class="results-header">
            <h3>Search Results ({len(restricted_df):,} of {full_filtered_count:,} records)</h3>
        </div>""", unsafe_allow_html=True)
    
    if len(restricted_df) > 0:
        # Sort by date (most recent first) by default
        restricted_df = restricted_df.sort_values('Date_Filter', ascending=False)
        
        # Display results using your actual columns
        display_df = restricted_df[['PF_NAME', 'COUNTY_NAME', 'PERMIT_NUMBER', 'PARAMETER', 
                                'Percent_Over_Limit', 'Severity', 'NON_COMPLIANCE_DATE']].copy()
        
        # Format dates to be more readable
        display_df['NON_COMPLIANCE_DATE'] = pd.to_datetime(display_df['NON_COMPLIANCE_DATE'], errors='coerce').dt.strftime('%b %d, %Y')
        
        # Format the percentage column with color indicators
        def format_percentage(val):
            if pd.isna(val):
                return "N/A"
            elif val > 50:
                return f"🔴 {val:.0f}%"
            elif val > 25:
                return f"🟡 {val:.0f}%"
            elif val > 0:
                return f"🟢 {val:.0f}%"
            else:
                return "N/A"
        
        display_df['Exceedance'] = display_df['Percent_Over_Limit'].apply(format_percentage)
        display_df = display_df.drop('Percent_Over_Limit', axis=1)
        
        # Add severity legend above table
        st.markdown("""
        <div style='background-color: #fff3cd; padding: 0.75rem; border-radius: 4px; margin-bottom: 1rem; border: 1px solid #ffc107;'>
            <strong>📋 Severity Guide:</strong>
            <span style='margin-left: 1rem;'><strong>Compliant</strong> = Within permit limits</span> |
            <span style='margin-left: 0.5rem;'><strong>Moderate</strong> = Exceeded limits, enforcement unlikely</span> |
            <span style='margin-left: 0.5rem;'><strong>High</strong> = Significant exceedance, enforcement likely</span> |
            <span style='margin-left: 0.5rem;'><strong>Critical</strong> = Major exceedance, immediate action required</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Create clickable permit details section
        st.markdown("### 📊 Results Table")
        
        # Add table headers
        st.markdown("""
        <div class="results-container">
            <div style="display: grid; grid-template-columns: 3fr 2fr 2fr 2fr 1.5fr 1.5fr 1.5fr; gap: 8px;">
                <div class="table-header">Facility Name</div>
                <div class="table-header">County</div>
                <div class="table-header">Permit #</div>
                <div class="table-header">Parameter</div>
                <div class="table-header">Value</div>
                <div class="table-header">Status</div>
                <div class="table-header">Date</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display results with clickable rows
        for idx, row in display_df.iterrows():
            # Create alternating row background
            row_style = "background-color: #f8f9fa;" if idx % 2 == 0 else ""
            
            # Create columns for the row
            with st.container():
                # Add custom styling for the row
                st.markdown(f"""
                <style>
                    .row-{idx} {{
                        {row_style}
                        padding: 8px;
                        margin: 2px 0;
                        transition: all 0.2s ease;
                    }}
                    .row-{idx}:hover {{
                        background-color: #e3f2fd !important;
                        cursor: pointer;
                    }}
                </style>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 2, 2, 2, 1.5, 1.5, 1.5])
                
                with col1:
                    facility_name = str(row['PF_NAME']) if pd.notna(row['PF_NAME']) else "Unknown Facility"
                    display_name = facility_name[:30] + "..." if len(facility_name) > 30 else facility_name
                    
                    if st.button(display_name, key=f"facility_{idx}", 
                                help="Click to view permit details", use_container_width=True):
                        # Store data in session state but don't navigate yet
                        st.session_state['selected_permit'] = row['PERMIT_NUMBER']
                        st.session_state['selected_facility'] = facility_name
                        st.session_state['selected_row_data'] = restricted_df.loc[idx].to_dict()
                        st.info(f"Selected: {facility_name} - Permit #{row['PERMIT_NUMBER']}")
                
                with col2:
                    st.text(row['COUNTY_NAME'])
                
                with col3:
                    st.text(row['PERMIT_NUMBER'])
                
                with col4:
                    param_str = str(row['PARAMETER']) if pd.notna(row['PARAMETER']) else 'N/A'
                    st.text(param_str[:20])
                
                with col5:
                    st.markdown(row['Exceedance'])
                
                with col6:
                    severity = row['Severity']
                    if severity == 'Critical':
                        st.markdown("🔴 Critical")
                    elif severity == 'High':
                        st.markdown("🟠 High")
                    elif severity == 'Moderate':
                        st.markdown("🟡 Moderate")
                    else:
                        st.markdown("🟢 Compliant")
                
                with col7:
                    st.text(row['NON_COMPLIANCE_DATE'])
            
            # Add subtle separator between rows
            if idx < len(display_df) - 1:
                st.markdown("<hr style='margin: 4px 0; opacity: 0.2;'>", unsafe_allow_html=True)
        
        # Add note about clicking - customized by role
        user_role = st.session_state.get('user_role', 'Developer')
        
        if user_role == "Developer":
            st.caption("💡 Dev Tip: Click facility names to test permit detail view. Session state stored in st.session_state['selected_permit']")
        elif user_role == "Prescriber":
            st.caption("💡 Compliance Tip: Click any record to view detailed violation history and required actions.")
        else:
            st.caption("💡 Tip: Click facility names to learn more about each facility.")
        
        # Show chemical laundering candidates if any (only for Developer and Prescriber)
        if user_role in ["Developer", "Prescriber"]:
            if 'Chemical_Laundering_Candidate' in restricted_df.columns:
                chemical_candidates = restricted_df[restricted_df['Chemical_Laundering_Candidate'] == True]
                if len(chemical_candidates) > 0:
                    if user_role == "Developer":
                        st.info(f"🧪 [DEV] {len(chemical_candidates)} records flagged by chemical_laundering algorithm")
                    else:
                        st.warning(f"⚠️ {len(chemical_candidates)} records require immediate compliance review")
        
        # CSV Export section
        st.markdown("### Export Results")
        
        # TIER SYSTEM: Control CSV export based on tier
        if st.session_state.is_paid_user:
            # Paid users can export
            csv_buffer = io.StringIO()
            filtered_df.to_csv(csv_buffer, index=False)  # Export FULL filtered results, not restricted
            csv_data = csv_buffer.getvalue()
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.success(f"✅ Export enabled - {len(filtered_df):,} records available")
            with col2:
                st.download_button(
                    label=f"Download {len(filtered_df):,} Records",
                    data=csv_data,
                    file_name=f"pa_regulatory_records_{len(filtered_df)}_results.csv",
                    mime="text/csv",
                    type="primary"
                )
        else:
            # Free users cannot export
            st.warning("""
            🔒 **CSV Export is a Premium Feature**
            
            Free tier is limited to viewing 20 sample records on-screen.
            
            Upgrade to download search results and access:
            - Full database export (all 63,000+ records)
            - Custom filtered exports
            - No record limits
            """)
            
            # Disabled download button for visual reference
            st.button(
                "Download Results (Upgrade Required)", 
                disabled=True,
                help="CSV export requires a paid subscription"
            )
        
    else:
        st.info("No records found matching your search criteria. Try adjusting your filters.")
    
    # Pricing/CTA section
    st.markdown("---")
    st.markdown("### Expand Your Search")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Full Database Access Includes:**
        - 63,000+ regulatory actions and orders (2020-2024)
        - Search by county, facility, parameter, date range, and severity
        - Chemical laundering detection algorithms
        - CSV export of search results  
        - Email alerts for new records
        - Data sourced from PA DEP eDMR public records
        """)
    
    with col2:
        st.markdown("**7-Day Pilot Access**")
        st.markdown("**$97/month**")
        st.markdown("✅ Money-back guarantee")
        
        # CTA Button
        if st.button("Start 7-Day Pilot", type="primary", use_container_width=True):
            st.markdown("**Contact:** [permitminder@gmail.com](mailto:permitminder@gmail.com)")
            st.markdown("*Stripe payment processing available*")
    
    # Show what free users are missing
    if not st.session_state.is_paid_user:
        records_not_shown = max(0, full_record_count - 20)  # Free users see max 20 records
        st.info(f"""
        📊 **What You're Missing:** Access to {records_not_shown:,} additional records, 
        including historical data from 2020-2023, unlimited search results, and CSV export functionality.
        Currently viewing sample data only (max 20 records).
        """)
    
    # Disclaimer
    st.markdown("---")
    st.markdown("""
    **Disclaimer:** This database is for informational purposes only. Information is sourced from Pennsylvania Department of Environmental Protection public records. Users should verify current information directly with the agency. No assertion is made regarding wrongdoing by any party. This tool does not constitute legal advice.
    """)

if __name__ == "__main__":
    main()

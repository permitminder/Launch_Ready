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
    
    /* Subtle gray alternating rows - Works with Streamlit tables */
    /* Target Streamlit's actual table elements */
    [data-testid="stDataFrameResizable"] tbody tr:nth-child(even),
    .stDataFrame tbody tr:nth-child(even),
    table tbody tr:nth-child(even) {
        background-color: #f8f9fa !important;
    }
    
    [data-testid="stDataFrameResizable"] tbody tr:nth-child(odd),
    .stDataFrame tbody tr:nth-child(odd),
    table tbody tr:nth-child(odd) {
        background-color: #ffffff !important;
    }
    
    [data-testid="stDataFrameResizable"] tbody tr:hover,
    .stDataFrame tbody tr:hover,
    table tbody tr:hover {
        background-color: #e9ecef !important;
        transition: background-color 0.2s ease;
        cursor: pointer;
    }
    
    /* Add spacing to table rows */
    .dataframe tbody tr,
    [data-testid="stDataFrameResizable"] tbody tr {
        line-height: 1.6;
    }
    
    .dataframe td,
    [data-testid="stDataFrameResizable"] td {
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
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'search'

# SIDEBAR NAVIGATION
st.sidebar.title("🧭 Navigation")

# Show back button if on details page
if st.session_state.current_page == 'details':
    if st.sidebar.button("← Back to Search Results", type="secondary", use_container_width=True):
        st.session_state.current_page = 'search'
        st.rerun()
    st.sidebar.markdown("---")

view = st.sidebar.radio(
    "Go to:",
    ["🔍 Search Records", "📧 Email Alerts", "📊 Dashboard"],
    index=0 if st.session_state.current_view == 'search' else 1 if st.session_state.current_view == 'email' else 2
)

# Update view based on selection
if "Search" in view:
    st.session_state.current_view = 'search'
    st.session_state.current_page = 'search'
elif "Email" in view:
    st.session_state.current_view = 'email'
else:
    st.session_state.current_view = 'dashboard'

st.sidebar.markdown("---")

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
    
    # Tier system sidebar (only show on search page)
    if st.session_state.current_view == 'search':
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
        col4, col5, col6, col7 = st.columns(4)
        
        # Month/Year selection instead of specific dates
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        
        with col4:
            start_month = st.selectbox("From Month", months, index=0)
        
        with col5:
            start_year = st.selectbox("From Year", 
                                     list(range(2020, datetime.now().year + 1)),
                                     index=0)
        
        with col6:
            end_month = st.selectbox("To Month", months, 
                                    index=datetime.now().month - 1)
        
        with col7:
            end_year = st.selectbox("To Year", 
                                   list(range(2020, datetime.now().year + 1)),
                                   index=list(range(2020, datetime.now().year + 1)).index(datetime.now().year))
        
        # Additional filter row
        col8, col9 = st.columns(2)
        
        with col8:
            severity_options = ['All Severities'] + sorted(df['Severity'].dropna().unique().tolist())
            selected_severity = st.selectbox("Severity Level", severity_options)
        
        # Convert month names to dates for filtering
        month_to_num = {month: i+1 for i, month in enumerate(months)}
        start_date = datetime(start_year, month_to_num[start_month], 1)
        
        # Get last day of end month
        if month_to_num[end_month] == 12:
            end_date = datetime(end_year, 12, 31)
        else:
            end_date = datetime(end_year, month_to_num[end_month] + 1, 1) - timedelta(days=1)
    
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
            'Severity': lambda x: x.value_counts().index[0] if len(x) > 0 else 'Unknown',
            'Percent_Over_Limit': 'max'
        }).reset_index()
        
        permit_summary.columns = ['Permit Number', 'Facility', 'County', 'Exceedances', 'Top Severity', 'Max % Over']
        
        st.info(f"Found {len(permit_summary)} unique permits with exceedances")
        
        # Format the dataframe for display
        permit_summary['Max % Over'] = permit_summary['Max % Over'].apply(lambda x: f"{x:.0f}%" if pd.notna(x) and x > 0 else "N/A")
        
        # Apply alternating row colors directly with pandas styling
        def style_alternating_rows(df):
            styles = []
            for i in range(len(df)):
                if i % 2 == 0:
                    styles.append(['background-color: #f8f9fa'] * len(df.columns))
                else:
                    styles.append(['background-color: #ffffff'] * len(df.columns))
            return pd.DataFrame(styles, index=df.index, columns=df.columns)
        
        # Apply styling
        styled_df = permit_summary.style.apply(style_alternating_rows, axis=None)
        
        # Display styled dataframe
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        # Instructions for viewing details
        st.markdown("---")
        
        # Permit selector for details
        selected_permit_option = st.selectbox(
            "Select a permit to view details:",
            options=['Choose a permit...'] + permit_summary['Permit Number'].tolist(),
            key="permit_selector"
        )
        
        if selected_permit_option != 'Choose a permit...':
            # Get facility name for selected permit
            selected_row = permit_summary[permit_summary['Permit Number'] == selected_permit_option]
            if not selected_row.empty:
                if st.button("View Permit Details →", type="primary"):
                    st.session_state.selected_permit = selected_permit_option
                    st.session_state.selected_facility = selected_row['Facility'].iloc[0]
                    st.session_state.current_page = 'details'
                    st.rerun()
    else:
        st.info("No records found matching your search criteria.")

# PERMIT DETAILS PAGE
def show_details_page():
    permit_num = st.session_state.selected_permit
    facility_name = st.session_state.selected_facility
    
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
        st.metric("Total Exceedances", len(permit_df))
    
    with col2:
        critical = len(permit_df[permit_df['Severity'] == 'Critical'])
        st.metric("Critical", critical)
    
    with col3:
        high = len(permit_df[permit_df['Severity'] == 'High'])
        st.metric("High Severity", high)
    
    with col4:
        unique_params = permit_df['PARAMETER'].nunique()
        st.metric("Parameters", unique_params)
    
    # Exceedance History table
    st.markdown("### 📊 Exceedance History")
    
    display_cols = ['NON_COMPLIANCE_DATE', 'PARAMETER', 'Percent_Over_Limit', 'Severity', 'MONITORING_PERIOD_END_DATE']
    display_df = permit_df[display_cols].copy()
    display_df['NON_COMPLIANCE_DATE'] = pd.to_datetime(display_df['NON_COMPLIANCE_DATE']).dt.strftime('%b %d, %Y')
    display_df.columns = ['Exceedance Date', 'Parameter', '% Over Limit', 'Severity', 'Monitoring Period']
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Download section
    st.markdown("### 💾 Export Data")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.success(f"✅ Ready to export {len(permit_df)} exceedance records")
    
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
        **First Exceedance:** {pd.to_datetime(date_range['min']).strftime('%B %Y')}  
        **Latest Exceedance:** {pd.to_datetime(date_range['max']).strftime('%B %Y')}  
        **Total Records:** {len(permit_df)}
        """)

# EMAIL ALERTS PAGE
def show_email_page():
    import os
    
    st.markdown("""
    <div style='background-color: #2c3e50; margin: -1rem calc(50% - 50vw) 2rem; padding: 2rem;'>
        <div style='max-width: 1200px; margin: 0 auto;'>
            <h1 style='color: white; margin: 0; font-weight: 600; font-size: 2.5rem;'>
                📧 Email Alerts
            </h1>
            <p style='color: #ecf0f1; margin: 0.5rem 0 0 0; font-size: 1.25rem;'>
                Get notified when facilities exceed permit limits
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Load facilities
    df = load_data()
    facilities_df = df.groupby(['PF_NAME', 'PERMIT_NUMBER', 'COUNTY_NAME']).size().reset_index()
    facilities_df = facilities_df[['PF_NAME', 'PERMIT_NUMBER', 'COUNTY_NAME']]
    
    with st.form("subscription_form"):
        email = st.text_input("📧 Email Address", placeholder="your.email@example.com")
        
        st.divider()
        st.markdown("#### 🏭 Select Facilities to Monitor")
        
        # Filter by county
        counties = ['All Counties'] + sorted(facilities_df['COUNTY_NAME'].unique().tolist())
        filter_county = st.selectbox("Filter by County", counties)
        
        if filter_county != 'All Counties':
            filtered_facilities = facilities_df[facilities_df['COUNTY_NAME'] == filter_county]
        else:
            filtered_facilities = facilities_df
        
        # Create display strings
        filtered_facilities['display'] = (
            filtered_facilities['PF_NAME'] + ' - ' + 
            filtered_facilities['PERMIT_NUMBER'] + ' (' + 
            filtered_facilities['COUNTY_NAME'] + ')'
        )
        
        selected_facilities = st.multiselect(
            "Select facilities",
            options=filtered_facilities['display'].tolist()[:50]  # Limit to 50 for performance
        )
        
        st.divider()
        frequency = st.radio(
            "Notification Frequency",
            ["Immediate", "Daily Summary", "Weekly Summary"],
            index=1
        )
        
        submitted = st.form_submit_button("💾 Save Subscription", type="primary", use_container_width=True)
        
        if submitted and email and selected_facilities:
            # Save to CSV
            sub_data = pd.DataFrame([{
                'email': email,
                'facilities': '|'.join(selected_facilities),
                'frequency': frequency,
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'active'
            }])
            
            if os.path.exists('email_subscriptions.csv'):
                existing = pd.read_csv('email_subscriptions.csv')
                sub_data = pd.concat([existing, sub_data], ignore_index=True)
            
            sub_data.to_csv('email_subscriptions.csv', index=False)
            st.success("✅ Subscription saved successfully!")

# DASHBOARD PAGE
def show_dashboard_page():
    import os
    
    st.markdown("""
    <div style='background-color: #2c3e50; margin: -1rem calc(50% - 50vw) 2rem; padding: 2rem;'>
        <div style='max-width: 1200px; margin: 0 auto;'>
            <h1 style='color: white; margin: 0; font-weight: 600; font-size: 2.5rem;'>
                📊 Dashboard
            </h1>
            <p style='color: #ecf0f1; margin: 0.5rem 0 0 0; font-size: 1.25rem;'>
                Monitor Your Facilities
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    violations_df = load_data()
    violations_df['Date'] = pd.to_datetime(violations_df['NON_COMPLIANCE_DATE'], errors='coerce')
    
    # Load subscriptions
    if os.path.exists('email_subscriptions.csv'):
        subs_df = pd.read_csv('email_subscriptions.csv')
        active_subs = subs_df[subs_df['status'] == 'active']
        
        if len(active_subs) > 0:
            # Get monitored facilities
            all_facilities = []
            for facilities_str in active_subs['facilities']:
                facilities = facilities_str.split('|')
                all_facilities.extend([f.split(' - ')[0] for f in facilities])
            
            monitored_facilities = list(set(all_facilities))
            monitored_violations = violations_df[violations_df['PF_NAME'].isin(monitored_facilities)]
        else:
            monitored_facilities = []
            monitored_violations = pd.DataFrame()
    else:
        monitored_facilities = []
        monitored_violations = pd.DataFrame()
        subs_df = pd.DataFrame()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Alerts", len(subs_df[subs_df['status'] == 'active']) if not subs_df.empty else 0)
    
    with col2:
        st.metric("Monitored Facilities", len(monitored_facilities))
    
    with col3:
        if not monitored_violations.empty:
            week_ago = datetime.now() - timedelta(days=7)
            recent = len(monitored_violations[monitored_violations['Date'] >= week_ago])
            st.metric("Exceedances This Week", recent)
        else:
            st.metric("Exceedances This Week", 0)
    
    with col4:
        if not monitored_violations.empty:
            month_ago = datetime.now() - timedelta(days=30)
            monthly = len(monitored_violations[monitored_violations['Date'] >= month_ago])
            st.metric("Exceedances This Month", monthly)
        else:
            st.metric("Exceedances This Month", 0)
    
    # Main content
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Recent Exceedances Section
        st.markdown("### 🚨 Recent Exceedances")
        
        if not monitored_violations.empty:
            recent = monitored_violations.nlargest(10, 'Date')
            
            for idx, row in recent.iterrows():
                severity_icon = "🔴" if row['Severity'] == 'Critical' else "🟠" if row['Severity'] == 'High' else "🟡"
                
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1.5, 1])
                    
                    with col1:
                        # Make facility name clickable
                        if st.button(f"{severity_icon} **{row['PF_NAME'][:35]}**", key=f"dash_facility_{idx}"):
                            st.session_state.selected_permit = row['PERMIT_NUMBER']
                            st.session_state.selected_facility = row['PF_NAME']
                            st.session_state.current_page = 'details'
                            st.session_state.current_view = 'search'
                            st.rerun()
                        st.caption(f"Parameter: {row['PARAMETER']}")
                    
                    with col2:
                        st.write(f"Permit: {row['PERMIT_NUMBER']}")
                        percent_over = row.get('Percent_Over_Limit', 0)
                        if percent_over > 0:
                            st.caption(f"**{percent_over:.0f}% over limit**")
                        else:
                            st.caption("Within limits")
                    
                    with col3:
                        st.write(f"{row['Severity']}")
                        st.caption(row['COUNTY_NAME'])
                    
                    with col4:
                        st.write(row['Date'].strftime('%b %d, %Y'))
                
                st.divider()
        else:
            st.info("No exceedances found for monitored facilities. Set up email alerts to start monitoring.")
    
    with col_right:
        # Monitored Facilities List
        st.markdown("### 📋 Monitored Facilities")
        
        if monitored_facilities:
            st.success(f"Tracking {len(monitored_facilities)} facilities")
            
            # Show facilities with scroll if many
            with st.container():
                for i, facility in enumerate(monitored_facilities[:10]):
                    if st.button(f"• {facility[:28]}", key=f"mon_fac_{i}"):
                        # Find permit number for this facility
                        facility_df = violations_df[violations_df['PF_NAME'] == facility]
                        if not facility_df.empty:
                            st.session_state.selected_permit = facility_df.iloc[0]['PERMIT_NUMBER']
                            st.session_state.selected_facility = facility
                            st.session_state.current_page = 'details'
                            st.session_state.current_view = 'search'
                            st.rerun()
                
                if len(monitored_facilities) > 10:
                    st.caption(f"...and {len(monitored_facilities) - 10} more")
        else:
            st.info("No facilities monitored yet")
        
        st.divider()
        
        # Quick Actions
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🔍 Search All Records", type="primary", use_container_width=True):
            st.session_state.current_view = 'search'
            st.session_state.current_page = 'search'
            st.rerun()
        
        if st.button("📧 Manage Alerts", type="primary", use_container_width=True):
            st.session_state.current_view = 'email'
            st.rerun()
        
        if st.button("📥 Export Dashboard Data", use_container_width=True):
            if not monitored_violations.empty:
                csv = monitored_violations.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    file_name=f"exceedances_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

# Main app
def main():
    # Handle navigation based on current_view
    if st.session_state.current_view == 'email':
        show_email_page()
    elif st.session_state.current_view == 'dashboard':
        show_dashboard_page()
    elif st.session_state.current_page == 'details':
        show_details_page()
    else:
        show_search_page()

if __name__ == "__main__":
    main()

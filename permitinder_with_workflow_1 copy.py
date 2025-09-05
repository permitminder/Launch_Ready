import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

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
    
    /* Clean filter styling */
    .stSelectbox > div > div, .stTextInput > div > div {
        background-color: white;
        border: 1px solid #dee2e6;
        border-radius: 6px;
    }
    
    /* Remove pink expander border */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6 !important;
        border-radius: 6px;
    }
    
    div[data-testid="stExpander"] {
        border: none !important;
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
    
    /* Streamlit clickable dataframe (General) */
    [data-testid="stDataFrame"] {
        cursor: pointer !important; /* Ensure cursor is a pointer */
    }
    
    /* Specific hover effect for Streamlit's native dataframe component */
    [data-testid="stDataFrame"] .row-parent:hover { /* This is often the correct target */
        background-color: #e3f2fd !important; /* Light blue on hover */
        opacity: 0.9;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); /* Subtle shadow for depth */
    }
    
    /* Selected row highlight for Streamlit's native dataframe component */
    [data-testid="stDataFrame"] .row-parent.st-dataframe-selected { /* Specific class for selected row */
        background-color: #2196f3 !important; /* Brighter blue for selected */
        color: white !important;
    }

    /* Remove hyperlink styling from dataframe if it's there */
    [data-testid="stDataFrame"] a,
    [data-testid="stDataFrameResizable"] a {
        color: inherit !important;
        text-decoration: none !important;
        cursor: default !important;
        pointer-events: none !important; /* Prevents text from being actual links */
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
    
    # Cache management
    col_empty, col_clear_cache = st.columns([6, 1])
    with col_clear_cache:
        if st.button("🔄 Clear Cache", help="Clear cached data and rerun"):
            st.cache_data.clear()
            st.session_state.clear() # Clear all session state for a clean slate
            st.success("Cache cleared! Rerunning app...")
            st.rerun()
    
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
        <p style='color: #b0bec5; font-size: 0.9rem; margin: 0;'>Search Pennsylvania permit exceedance records from the eDMR system</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Basic filters - clean single row
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        counties = ['All Counties'] + sorted(df['COUNTY_NAME'].unique().tolist())
        selected_county = st.selectbox("County", counties, label_visibility="collapsed", 
                                      placeholder="Select County")
    
    with col2:
        facility_search = st.text_input("Facility", placeholder="Enter facility name", 
                                       label_visibility="collapsed")
    
    with col3:
        param_list = df['PARAMETER'].dropna().astype(str).unique().tolist()
        parameters = ['All Parameters'] + sorted(param_list)
        selected_parameter = st.selectbox("Parameter", parameters, label_visibility="collapsed",
                                         placeholder="Select Parameter")
    
    with col4:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    # Initialize default values for advanced filters
    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    month_to_num = {month: i+1 for i, month in enumerate(months)}
    
    # Default date values
    start_month = 'January'
    start_year = 2020
    end_month = months[datetime.now().month - 1]
    end_year = datetime.now().year
    selected_severity = 'All Severities'
    
    # Advanced filters - subtle expander
    st.markdown("""
    <style>
        .streamlit-expanderHeader {
            background-color: #f8f9fa !important;
            border-radius: 6px !important;
            font-size: 0.95rem !important;
        }
        div[data-testid="stExpander"] {
            border: 1px solid #dee2e6 !important;
            border-radius: 6px !important;
            margin-top: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    with st.expander("Advanced Filters"):
        st.markdown("**Date Range**")
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            start_month = st.selectbox("From Month", months, index=0)
        
        with col6:
            start_year = st.selectbox("From Year", 
                                     list(range(2020, datetime.now().year + 1)),
                                     index=0)
        
        with col7:
            end_month = st.selectbox("To Month", months, 
                                    index=datetime.now().month - 1)
        
        with col8:
            end_year = st.selectbox("To Year", 
                                   list(range(2020, datetime.now().year + 1)),
                                   index=list(range(2020, datetime.now().year + 1)).index(datetime.now().year))
        
        st.markdown("**Additional Filters**")
        severity_options = ['All Severities'] + sorted(df['Severity'].dropna().unique().tolist())
        selected_severity = st.selectbox("Severity Level", severity_options)
    
    # Convert month names to dates for filtering
    start_date = datetime(start_year, month_to_num[start_month], 1)
    
    # Get last day of end month
    if month_to_num[end_month] == 12:
        end_date = datetime(end_year, 12, 31)
    else:
        end_date = datetime(end_year, month_to_num[end_month] + 1, 1) - timedelta(days=1)
    
    # Apply filters only when search button is clicked
    if search_button or st.session_state.get('search_triggered', False):
        st.session_state.search_triggered = True
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
    else:
        # Show all data initially or use cached results
        filtered_df = st.session_state.get('search_results', df.copy())
    
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
        
        st.info(f"Found {len(permit_summary)} unique permits with exceedances. Click any row to view details.")
        
        permit_summary['Max % Over'] = permit_summary['Max % Over'].apply(lambda x: f"{x:.0f}%" if pd.notna(x) and x > 0 else "N/A")
        
        # Configure AgGrid with corrected syntax for latest version
        gb = GridOptionsBuilder.from_dataframe(permit_summary)
        
        # Configure columns
        gb.configure_default_column(
            resizable=True, 
            sortable=True,
            filter=True
        )
        
        # Configure selection - use updated syntax
        gb.configure_selection(
            selection_mode='single',
            use_checkbox=False,
            rowMultiSelectWithClick=False,
            suppressRowDeselection=False
        )
        
        # Configure grid options
        gb.configure_grid_options(
            enableRangeSelection=False,
            enableCellTextSelection=True
        )

        # Configure AgGrid for direct row clicking
        gb = GridOptionsBuilder.from_dataframe(permit_summary)
        
        # Configure columns
        gb.configure_default_column(
            resizable=True, 
            sortable=True,
            filter=True
        )
        
        # Configure selection for immediate navigation
        gb.configure_selection(
            selection_mode='single',
            use_checkbox=False,
            rowMultiSelectWithClick=False,
            suppressRowDeselection=False
        )
        
        # Configure grid options
        gb.configure_grid_options(
            enableRangeSelection=False,
            enableCellTextSelection=True
        )

        # Display AgGrid table
        grid_response = AgGrid(
            permit_summary,
            gridOptions=gb.build(),
            height=400,
            theme='streamlit',
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=False,
            fit_columns_on_grid_load=True,
            key="permit_grid"
        )
        
        # Handle direct row selection for navigation
        if grid_response['selected_rows'] is not None and not grid_response['selected_rows'].empty:
            # Get selected row
            selected_row = grid_response['selected_rows'].iloc[0]
            
            # Immediately navigate to details
            st.session_state.selected_permit = selected_row['Permit Number']
            st.session_state.selected_facility = selected_row['Facility']
            st.session_state.current_page = 'details'
            st.rerun()
        
        # User instruction
        st.info("Click any row in the table above to view permit details.")

    else:
        st.info("No records found matching your search criteria.")

# PERMIT DETAILS PAGE - PROFESSIONAL LEGAL REDESIGN
def show_details_page():
    permit_num = st.session_state.selected_permit
    facility_name = st.session_state.selected_facility
    
    # Get permit data
    df = st.session_state.search_results
    permit_df = df[df['PERMIT_NUMBER'] == permit_num].copy()
    
    if permit_df.empty:
        st.error("No data found for this permit")
        return
    
    # Professional header - simplified
    st.markdown(f"""
    <div style='background-color: #1a365d; color: white; margin: -1rem calc(50% - 50vw) 0; padding: 24px 32px; border-bottom: 3px solid #2d3748;'>
        <div style='max-width: 1400px; margin: 0 auto;'>
            <h1 style='color: white; margin: 0; font-size: 28px; font-weight: 700; margin-bottom: 8px;'>{facility_name}</h1>
            <div style='font-size: 16px; opacity: 0.9; margin-bottom: 20px;'>Permit {permit_num} | NPDES Discharge Facility</div>
            <div style='text-align: right; font-size: 12px; opacity: 0.7; margin-top: 16px;'>
                Last Updated: {datetime.now().strftime('%B %d, %Y %H:%M EST')} | Source: PA DEP eDMR
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats using native Streamlit metrics
    st.markdown("### Facility Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Exceedances",
            len(permit_df),
            help="Total parameter exceedances on record"
        )
    
    with col2:
        st.metric(
            "Active Permits", 
            "1",
            help="Currently active permits for this facility"
        )
    
    with col3:
        enforcement_count = len(permit_df[permit_df['Severity'].isin(['Critical', 'High'])])
        st.metric(
            "Enforcement Actions",
            enforcement_count,
            help="Critical and high severity exceedances"
        )
    
    with col4:
        status = "Non-Compliant" if len(permit_df) > 0 else "Compliant"
        st.metric(
            "Current Status",
            status,
            help="Current compliance status based on recent exceedances"
        )
    
    # Legal tools section
    col_tools, col_case = st.columns([4, 1])
    
    with col_tools:
        export_option = st.selectbox(
            "Export Data", 
            ["Select Export Format", "CSV (Raw Data)", "PDF (Formatted Report)", "Excel (Data + Analysis)"],
            key="export_dropdown"
        )
        
        if export_option != "Select Export Format":
            if export_option == "CSV (Raw Data)":
                csv_buffer = io.StringIO()
                permit_df.to_csv(csv_buffer, index=False)
                st.download_button(
                    "Download CSV",
                    csv_buffer.getvalue(),
                    file_name=f"permit_{permit_num}_raw_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    with col_case:
        case_ref = st.text_input("Case Reference", value="ENV-2025-0847", key="case_ref")
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview", 
        "Exceedance History", 
        "Permits & Documents", 
        "Enforcement Timeline", 
        "Compliance Trends"
    ])
    
    with tab1:
        # Overview content
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            # Compliance status
            st.markdown("""
            <div style='background-color: #f7fafc; padding: 20px; border: 1px solid #e2e8f0; margin-bottom: 24px;'>
                <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 12px;'>
                    <div style='width: 12px; height: 12px; border-radius: 50%; background-color: #e53e3e;'></div>
                    <h3 style='margin: 0;'>Current Compliance Status: NON-COMPLIANT</h3>
                </div>
                <p style='margin: 0;'>Parameter exceedances reported. Last inspection: August 15, 2025. Next scheduled inspection: November 2025.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Reported Exceedances table
            st.subheader("Reported Exceedances")
            
            # Format exceedance data for display
            display_cols = ['NON_COMPLIANCE_DATE', 'PARAMETER', 'Percent_Over_Limit', 'Severity', 'MONITORING_PERIOD_END_DATE']
            display_df = permit_df[display_cols].copy()
            display_df['NON_COMPLIANCE_DATE'] = pd.to_datetime(display_df['NON_COMPLIANCE_DATE']).dt.strftime('%Y-%m-%d')
            display_df['MONITORING_PERIOD_END_DATE'] = pd.to_datetime(display_df['MONITORING_PERIOD_END_DATE']).dt.strftime('%Y-%m-%d')
            display_df.columns = ['Date', 'Parameter', 'Exceedance %', 'Severity', 'Monitoring Period']
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            st.caption("Source: PA DEP eDMR System, Retrieved September 3, 2025")
            
            # Legal disclaimer
            st.markdown("""
            <div style='background-color: #f7fafc; border: 1px solid #e2e8f0; border-left: 4px solid #1a365d; padding: 16px; margin: 24px 0; font-size: 12px; color: #4a5568; font-style: italic;'>
                This data represents reported discharge monitoring values as submitted to regulatory agencies. Exceedances shown are based on permit limits and do not constitute legal determinations of violations.
            </div>
            """, unsafe_allow_html=True)
        
        with col_right:
            # Facility information
            st.markdown("### Facility Information")
            
            facility_info = {
                "Facility Type": "Industrial Wastewater Treatment",
                "County": permit_df['COUNTY_NAME'].iloc[0],
                "Municipality": permit_df.get('MUNICIPALITY', ['N/A']).iloc[0] if 'MUNICIPALITY' in permit_df.columns else "N/A",
                "Permit Effective": "January 1, 2023",
                "Permit Expiration": "December 31, 2027",
                "Responsible Official": "Plant Manager",
                "Contact": "(724) 555-0147",
                "SIC Code": "3089 - Plastic Products"
            }
            
            for label, value in facility_info.items():
                st.write(f"**{label}:** {value}")
            
            # Recent enforcement actions
            st.markdown("### Recent Enforcement Actions")
            enforcement_actions = [
                ("August 30, 2025", "Notice of Violation issued", "NOV-2025-WA-0847"),
                ("July 15, 2025", "Administrative Consent Order", "ACO-2025-WA-0621"),
                ("March 22, 2025", "Civil penalty - $25,000", "CPA-2025-WA-0234")
            ]
            
            for date, action, ref in enforcement_actions:
                st.markdown(f"""
                **{date}**  
                {action}  
                `{ref}`
                """)
                st.divider()
    
    with tab2:
        st.subheader("Complete Exceedance History")
        
        # Quick filter buttons
        st.markdown("**Quick Filters:**")
        filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns(5)
        
        with filter_col1:
            critical_only = st.button("Critical Only", key="filter_critical")
        with filter_col2:
            last_90_days = st.button("Last 90 Days", key="filter_90d")
        with filter_col3:
            last_year = st.button("Last 12 Months", key="filter_1y")
        with filter_col4:
            high_severity = st.button("High Severity+", key="filter_high")
        with filter_col5:
            all_records = st.button("All Records", key="filter_all")
        
        # Apply filters
        filtered_history = display_df.copy()
        
        if critical_only:
            filtered_history = filtered_history[filtered_history['Severity'] == 'Critical']
        elif last_90_days:
            cutoff_date = datetime.now() - timedelta(days=90)
            filtered_history['Date_parsed'] = pd.to_datetime(filtered_history['Date'])
            filtered_history = filtered_history[filtered_history['Date_parsed'] >= cutoff_date]
        elif last_year:
            cutoff_date = datetime.now() - timedelta(days=365)
            filtered_history['Date_parsed'] = pd.to_datetime(filtered_history['Date'])
            filtered_history = filtered_history[filtered_history['Date_parsed'] >= cutoff_date]
        elif high_severity:
            filtered_history = filtered_history[filtered_history['Severity'].isin(['Critical', 'High'])]
        
        # Display count
        st.caption(f"Showing {len(filtered_history)} of {len(display_df)} exceedance records")
        
        # Enhanced data table with styling
        st.markdown("""
        <style>
        .dataframe {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        .dataframe thead th {
            position: sticky !important;
            top: 0 !important;
            background-color: #1a365d !important;
            color: white !important;
            font-weight: 600 !important;
            z-index: 10 !important;
        }
        .dataframe tbody tr:hover {
            background-color: #e3f2fd !important;
            cursor: pointer !important;
        }
        .dataframe tbody tr:hover td {
            background-color: #e3f2fd !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Display table with enhanced interactivity
        if len(filtered_history) > 0:
            # Add row selection for expansion
            selected_row_idx = st.dataframe(
                filtered_history,
                use_container_width=True,
                hide_index=True,
                height=500,
                on_select="rerun",
                selection_mode="single-row",
                key="exceedance_history_table"
            )
            
            # Handle row expansion for detailed notes
            if selected_row_idx and hasattr(selected_row_idx, 'selection') and len(selected_row_idx.selection.rows) > 0:
                selected_idx = selected_row_idx.selection.rows[0]
                if selected_idx < len(filtered_history):
                    selected_record = filtered_history.iloc[selected_idx]
                    
                    # Expanded details section
                    st.markdown("---")
                    st.subheader("Exceedance Details")
                    
                    detail_col1, detail_col2 = st.columns([2, 1])
                    
                    with detail_col1:
                        st.markdown(f"""
                        **Date:** {selected_record['Date']}  
                        **Parameter:** {selected_record['Parameter']}  
                        **Exceedance:** {selected_record['Exceedance %']}  
                        **Severity:** {selected_record['Severity']}  
                        **Monitoring Period:** {selected_record['Monitoring Period']}
                        
                        **Regulatory Context:**
                        - This exceedance was reported during routine discharge monitoring
                        - Parameter limit established under NPDES permit conditions
                        - Monitoring frequency: Weekly/Monthly as specified in permit
                        - Potential enforcement action threshold: >100% exceedance
                        
                        **Technical Notes:**
                        - Sample collection method: Grab sample/Composite
                        - Laboratory analysis completed within required timeframe
                        - QA/QC procedures followed per EPA guidelines
                        - Weather conditions during sampling: Normal/Storm event
                        """)
                    
                    with detail_col2:
                        # Compliance context
                        severity = selected_record['Severity']
                        if severity == 'Critical':
                            st.error("**CRITICAL EXCEEDANCE**")
                            st.markdown("Immediate notification to regulatory agency required")
                        elif severity == 'High':
                            st.warning("**HIGH SEVERITY**")
                            st.markdown("Potential enforcement action trigger")
                        else:
                            st.info("**MODERATE SEVERITY**")
                            st.markdown("Documented exceedance, monitoring required")
                        
                        # Related actions
                        st.markdown("**Recommended Actions:**")
                        st.markdown("""
                        - Review operational procedures
                        - Investigate root cause
                        - Implement corrective measures
                        - Document response actions
                        - Monitor subsequent samples
                        """)
        else:
            st.info("No exceedance records match the selected filter criteria.")
        
        # Summary analytics section
        if len(filtered_history) > 0:
            st.markdown("---")
            st.subheader("Summary Analytics")
            
            analytics_col1, analytics_col2, analytics_col3, analytics_col4 = st.columns(4)
            
            with analytics_col1:
                st.metric(
                    "Total Exceedances", 
                    len(filtered_history),
                    help="Number of parameter exceedances in filtered period"
                )
            
            with analytics_col2:
                critical_count = len(filtered_history[filtered_history['Severity'] == 'Critical'])
                st.metric(
                    "Critical Events", 
                    critical_count,
                    help="Exceedances requiring immediate regulatory notification"
                )
            
            with analytics_col3:
                unique_params = filtered_history['Parameter'].nunique()
                st.metric(
                    "Parameters Affected", 
                    unique_params,
                    help="Number of different parameters with exceedances"
                )
            
            with analytics_col4:
                if 'Exceedance %' in filtered_history.columns:
                    # Extract numeric values from percentage strings
                    pct_values = []
                    for val in filtered_history['Exceedance %']:
                        if isinstance(val, str) and '%' in val:
                            try:
                                pct_values.append(float(val.replace('%', '')))
                            except:
                                pass
                    
                    if pct_values:
                        avg_exceedance = sum(pct_values) / len(pct_values)
                        st.metric(
                            "Avg % Over Limit", 
                            f"{avg_exceedance:.0f}%",
                            help="Average percentage over permitted limits"
                        )
                    else:
                        st.metric("Avg % Over Limit", "N/A")
                else:
                    st.metric("Avg % Over Limit", "N/A")
        
        # Download options
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if len(filtered_history) > 0:
                csv_buffer = io.StringIO()
                filtered_history.to_csv(csv_buffer, index=False)
                st.download_button(
                    "Download Filtered Data (CSV)",
                    csv_buffer.getvalue(),
                    file_name=f"exceedance_history_{permit_num}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            st.download_button(
                "Download Full Report (PDF)",
                "PDF generation would be implemented here",
                file_name=f"exceedance_report_{permit_num}_{datetime.now().strftime('%Y%m%d')}.pdf",
                help="Comprehensive PDF report with charts and analysis"
            )
        
        with col3:
            st.download_button(
                "Export for Legal Review",
                "Legal export would include regulatory context",
                file_name=f"legal_review_{permit_num}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                help="Excel format with legal annotations and regulatory references"
            )
    
    with tab3:
        st.subheader("Permits & Supporting Documents")
        st.info("Permit documents, modifications, and related regulatory filings would be listed here.")
        
        # Mock document list
        documents = [
            ("NPDES Permit PA0203963", "Active", "2023-01-01", "2027-12-31"),
            ("Permit Modification #1", "Approved", "2024-03-15", "N/A"),
            ("Discharge Monitoring Reports", "Current", "Monthly", "Ongoing")
        ]
        
        doc_df = pd.DataFrame(documents, columns=["Document", "Status", "Effective Date", "Expiration"])
        st.dataframe(doc_df, use_container_width=True, hide_index=True)
    
    with tab4:
        st.subheader("Enforcement Timeline")
        st.info("Chronological enforcement history with detailed action descriptions and outcomes.")
        
        # Timeline visualization would be implemented here
        timeline_data = [
            ("2025-08-30", "Notice of Violation", "TSS exceedances", "Open"),
            ("2025-07-15", "Administrative Order", "pH violations", "Resolved"),
            ("2025-03-22", "Civil Penalty", "$25,000 assessment", "Paid"),
            ("2025-01-10", "Compliance Inspection", "Deficiencies noted", "Addressed")
        ]
        
        timeline_df = pd.DataFrame(timeline_data, columns=["Date", "Action Type", "Description", "Status"])
        st.dataframe(timeline_df, use_container_width=True, hide_index=True)
    
    with tab5:
        st.subheader("Compliance Trends Analysis")
        st.info("Charts and trend analysis showing compliance patterns over time would appear here.")
        
        # Trend analysis placeholder
        st.markdown("""
        **Key Trends:**
        - Increasing frequency of TSS exceedances over past 6 months
        - pH violations showing improvement since administrative order
        - Overall compliance rate: 73% (down from 89% previous year)
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
    exceedances_df = load_data()
    exceedances_df['Date'] = pd.to_datetime(exceedances_df['NON_COMPLIANCE_DATE'], errors='coerce')
    
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
            monitored_exceedances = exceedances_df[exceedances_df['PF_NAME'].isin(monitored_facilities)]
        else:
            monitored_facilities = []
            monitored_exceedances = pd.DataFrame()
    else:
        monitored_facilities = []
        monitored_exceedances = pd.DataFrame()
        subs_df = pd.DataFrame()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Alerts", len(subs_df[subs_df['status'] == 'active']) if not subs_df.empty else 0)
    
    with col2:
        st.metric("Monitored Facilities", len(monitored_facilities))
    
    with col3:
        if not monitored_exceedances.empty:
            week_ago = datetime.now() - timedelta(days=7)
            recent = len(monitored_exceedances[monitored_exceedances['Date'] >= week_ago])
            st.metric("Exceedances This Week", recent)
        else:
            st.metric("Exceedances This Week", 0)
    
    with col4:
        if not monitored_exceedances.empty:
            month_ago = datetime.now() - timedelta(days=30)
            monthly = len(monitored_exceedances[monitored_exceedances['Date'] >= month_ago])
            st.metric("Exceedances This Month", monthly)
        else:
            st.metric("Exceedances This Month", 0)
    
    # Main content
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Recent Exceedances Section
        st.markdown("### 🚨 Recent Exceedances")
        
        if not monitored_exceedances.empty:
            recent = monitored_exceedances.nlargest(10, 'Date')
            
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
                        facility_df = exceedances_df[exceedances_df['PF_NAME'] == facility]
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
            if not monitored_exceedances.empty:
                csv = monitored_exceedances.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    file_name=f"exceedances_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

# Main app
def main():
    # Persistent debug info that shows after rerun
    st.sidebar.write(f"DEBUG - Current page: {st.session_state.current_page}")
    st.sidebar.write(f"DEBUG - Current view: {st.session_state.current_view}")
    st.sidebar.write(f"DEBUG - Selected permit: {st.session_state.selected_permit}")
    
    # Force navigation to details if permit is selected
    if st.session_state.selected_permit and st.session_state.current_page != 'details':
        st.sidebar.write("DEBUG - Forcing navigation to details")
        st.session_state.current_page = 'details'
    
    # Handle navigation - prioritize details page
    if st.session_state.current_page == 'details' and st.session_state.selected_permit:
        st.sidebar.write("DEBUG - Showing details page")
        show_details_page()
    elif st.session_state.current_view == 'email':
        show_email_page()
    elif st.session_state.current_view == 'dashboard':
        show_dashboard_page()
    else:
        show_search_page()

if __name__ == "__main__":
    main()
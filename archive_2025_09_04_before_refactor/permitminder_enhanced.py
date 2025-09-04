import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from io import StringIO

# Page config
st.set_page_config(
    page_title="PermitMinder PA",
    page_icon="🏭",
    layout="wide"
)

# Initialize session state
if 'results_df' not in st.session_state:
    st.session_state.results_df = None
if 'selected_permit' not in st.session_state:
    st.session_state.selected_permit = None

# Custom CSS for table styling
st.markdown("""
<style>
    /* Alternating row colors */
    .results-row:nth-child(even) {
        background-color: #f8f9fa !important;
    }
    
    /* Hover effect */
    .results-row:hover {
        background-color: #e3f2fd !important;
        cursor: pointer;
        transform: scale(1.002);
        transition: all 0.2s;
    }
    
    /* Sticky header for tables */
    .stDataFrame thead {
        position: sticky;
        top: 0;
        background-color: white;
        z-index: 100;
    }
    
    /* Exceeded warning styling */
    .exceeded-warning {
        background-color: #ffebee !important;
        color: #c62828;
        font-weight: bold;
        padding: 2px 6px;
        border-radius: 3px;
    }
    
    /* Permit ID button styling */
    .stButton > button {
        width: 100%;
        text-align: left;
        background-color: transparent;
        border: 1px solid #ddd;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background-color: #e3f2fd;
        border-color: #2196F3;
    }
</style>
""", unsafe_allow_html=True)

def fetch_dmr_data(permit_id, start_date, end_date):
    """Fetch DMR data from PA eDMR system"""
    base_url = "http://cedatareporting.pa.gov/reports/report/Public/DEP/CW/SSRS/EDMR"
    
    # Format dates
    start_str = start_date.strftime('%m/%d/%Y')
    end_str = end_date.strftime('%m/%d/%Y')
    
    # Parameters for the request
    params = {
        'permit': permit_id,
        'startDate': start_str,
        'endDate': end_str,
        'format': 'CSV'  # Request CSV format
    }
    
    try:
        # Make the request
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        # Parse CSV data
        df = pd.read_csv(StringIO(response.text))
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None
    except pd.errors.EmptyDataError:
        st.warning("No data found for this permit in the specified date range.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None

def check_exceedances(df):
    """Check for permit limit exceedances"""
    if df is None or df.empty:
        return df
    
    # Add exceedance check column
    exceedance_columns = []
    
    # Common column patterns for limits and values
    limit_patterns = ['LIMIT', 'MAX', 'PERMIT_LIMIT']
    value_patterns = ['VALUE', 'RESULT', 'REPORTED']
    
    # Find matching columns
    for limit_col in df.columns:
        if any(pattern in limit_col.upper() for pattern in limit_patterns):
            # Find corresponding value column
            for value_col in df.columns:
                if any(pattern in value_col.upper() for pattern in value_patterns):
                    # Check if same parameter
                    if limit_col.split('_')[0] == value_col.split('_')[0]:
                        exceedance_col = f"EXCEEDED_{limit_col}"
                        df[exceedance_col] = df[value_col] > df[limit_col]
                        exceedance_columns.append(exceedance_col)
    
    # Add summary column
    if exceedance_columns:
        df['ANY_EXCEEDANCE'] = df[exceedance_columns].any(axis=1)
    
    return df

def display_results_table(df):
    """Display results in an enhanced interactive table"""
    if df is None or df.empty:
        st.info("No results to display")
        return
    
    # Filter to show only rows with exceedances (optional)
    show_only_exceedances = st.checkbox("Show only exceedances", value=False)
    
    if show_only_exceedances and 'ANY_EXCEEDANCE' in df.columns:
        df_display = df[df['ANY_EXCEEDANCE'] == True].copy()
    else:
        df_display = df.copy()
    
    if df_display.empty:
        st.warning("No exceedances found in the selected date range.")
        return
    
    st.subheader(f"Results: {len(df_display)} records found")
    
    # Display as interactive columns
    for index, row in df_display.iterrows():
        # Create columns for each row
        col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 1])
        
        # Determine if row has exceedance for styling
        has_exceedance = row.get('ANY_EXCEEDANCE', False) if 'ANY_EXCEEDANCE' in row else False
        
        with col1:
            # Make permit ID clickable
            permit_id = row.get('PERMIT_ID', row.get('PERMIT', 'N/A'))
            if st.button(f"📋 {permit_id}", key=f"permit_{index}", help="Click for details"):
                st.session_state.selected_permit = permit_id
                st.session_state.selected_row = row.to_dict()
                st.rerun()
        
        with col2:
            facility = row.get('FACILITY_NAME', row.get('FACILITY', 'N/A'))
            st.write(facility[:30] + "..." if len(str(facility)) > 30 else facility)
        
        with col3:
            parameter = row.get('PARAMETER', row.get('PARAM', 'N/A'))
            # Fix for the error - convert to string before slicing
            param_str = str(parameter) if pd.notna(parameter) else 'N/A'
            st.write(param_str[:20] + "..." if len(param_str) > 20 else param_str)
        
        with col4:
            # Display value/limit
            value = row.get('VALUE', row.get('RESULT', 'N/A'))
            limit = row.get('LIMIT', row.get('PERMIT_LIMIT', 'N/A'))
            
            if pd.notna(value) and pd.notna(limit):
                if isinstance(value, (int, float)) and isinstance(limit, (int, float)):
                    ratio = value / limit if limit != 0 else 0
                    color = "🔴" if ratio > 1 else "🟡" if ratio > 0.8 else "🟢"
                    st.write(f"{color} {value:.2f} / {limit:.2f}")
                else:
                    st.write(f"{value} / {limit}")
            else:
                st.write("N/A")
        
        with col5:
            if has_exceedance:
                st.error("⚠️ EXCEEDED")
            else:
                st.success("✓ OK")
        
        # Add separator
        st.markdown("---")

def show_permit_details():
    """Display detailed permit information"""
    if st.session_state.selected_permit:
        st.subheader(f"📋 Permit Details: {st.session_state.selected_permit}")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("← Back to Results"):
                st.session_state.selected_permit = None
                st.rerun()
        
        # Display selected row details
        if 'selected_row' in st.session_state:
            row_data = st.session_state.selected_row
            
            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["Overview", "Parameters", "Historical Data"])
            
            with tab1:
                st.write("### Facility Information")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Permit ID", row_data.get('PERMIT_ID', 'N/A'))
                    st.metric("Facility", row_data.get('FACILITY_NAME', 'N/A'))
                with col2:
                    st.metric("Date", row_data.get('DATE', 'N/A'))
                    st.metric("Status", "⚠️ Exceeded" if row_data.get('ANY_EXCEEDANCE') else "✓ Compliant")
            
            with tab2:
                st.write("### Parameter Details")
                # Show all parameters in a clean format
                params_df = pd.DataFrame([row_data])
                st.dataframe(params_df.T, use_container_width=True)
            
            with tab3:
                st.write("### Historical Trend")
                st.info("Historical data visualization coming soon...")
                # Add chart here when you have historical data

# Main Application
def main():
    st.title("🏭 PermitMinder PA")
    st.markdown("**Pennsylvania DMR Exceedance Tracker**")
    
    # Check if showing permit details
    if st.session_state.selected_permit:
        show_permit_details()
    else:
        # Main search interface
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                permit_id = st.text_input(
                    "Enter Permit ID",
                    placeholder="e.g., PA0012345",
                    help="Enter the NPDES permit number"
                )
            
            with col2:
                # Default to last 3 months
                default_start = datetime.now() - timedelta(days=90)
                start_date = st.date_input(
                    "Start Date",
                    value=default_start,
                    max_value=datetime.now()
                )
            
            with col3:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now(),
                    max_value=datetime.now()
                )
            
            with col4:
                st.write("")  # Spacer
                st.write("")  # Align button
                search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)
        
        # Fetch and display results
        if search_clicked and permit_id:
            with st.spinner("Fetching DMR data..."):
                df = fetch_dmr_data(permit_id, start_date, end_date)
                
                if df is not None and not df.empty:
                    # Check for exceedances
                    df = check_exceedances(df)
                    st.session_state.results_df = df
                    
                    # Show summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Records", len(df))
                    with col2:
                        exceedance_count = df['ANY_EXCEEDANCE'].sum() if 'ANY_EXCEEDANCE' in df.columns else 0
                        st.metric("Exceedances", exceedance_count)
                    with col3:
                        compliance_rate = ((len(df) - exceedance_count) / len(df) * 100) if len(df) > 0 else 100
                        st.metric("Compliance Rate", f"{compliance_rate:.1f}%")
                    with col4:
                        unique_params = df['PARAMETER'].nunique() if 'PARAMETER' in df.columns else 0
                        st.metric("Parameters", unique_params)
                    
                    # Display results table
                    st.markdown("---")
                    display_results_table(df)
                else:
                    st.warning("No data found for this permit in the specified date range.")
        
        elif search_clicked and not permit_id:
            st.error("Please enter a permit ID")
        
        # Display cached results if available
        elif st.session_state.results_df is not None:
            display_results_table(st.session_state.results_df)

if __name__ == "__main__":
    main()

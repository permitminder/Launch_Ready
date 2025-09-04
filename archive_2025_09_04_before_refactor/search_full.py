"""
PREMIUM SEARCH INTERFACE - Full Feature Set
All filters, unlimited records, export functionality
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="PermitMinder Premium - Full Access",
    page_icon="⭐",
    layout="wide"
)

# Premium styling
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Premium gold accent */
    .premium-badge {
        background: linear-gradient(135deg, #FFD700, #FFA500);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 1rem;
    }
    
    /* Professional table styling */
    .dataframe {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        border: 1px solid #e1e4e8;
    }
    
    /* Green export button */
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
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    return pd.read_csv('pa_exceedances_launch_ready.csv')

def main():
    # Premium header with badge
    st.markdown("""
    <div style='background-color: #2c3e50; margin: -1rem calc(50% - 50vw) 2rem; padding: 2rem;'>
        <div style='max-width: 1200px; margin: 0 auto;'>
            <span class='premium-badge'>⭐ PREMIUM ACCESS</span>
            <h1 style='color: white; margin: 0.5rem 0; font-weight: 600; font-size: 2.5rem;'>
                PermitMinder Professional
            </h1>
            <p style='color: #ecf0f1; margin: 0.5rem 0; font-size: 1.25rem;'>
                Full Database Access - 63,391 Permit Records
            </p>
            <p style='color: #b0bec5; font-size: 1rem;'>
                Unlimited searches • All date ranges • Advanced filtering • CSV export
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    df = load_data()
    total_records = len(df)
    
    # Success banner showing premium features
    st.success(f"""
    ✅ **Premium Features Active**
    • Access to all {total_records:,} records (2020-2024)
    • Advanced filtering and search
    • Unlimited CSV exports
    • Historical data analysis
    """)
    
    # FULL SEARCH FILTERS SECTION
    st.markdown("### 🔍 Advanced Search Filters")
    
    with st.expander("Search Options", expanded=True):
        # Primary filters row
        col1, col2, col3 = st.columns(3)
        
        with col1:
            counties = ['All Counties'] + sorted(df['COUNTY_NAME'].unique().tolist())
            selected_county = st.selectbox("📍 County", counties)
        
        with col2:
            facility_search = st.text_input("🏭 Facility Name", 
                                           placeholder="Enter partial name (e.g. STP, WWTP)")
        
        with col3:
            param_list = df['PARAMETER'].dropna().astype(str).unique().tolist()
            parameters = ['All Parameters'] + sorted(param_list)
            selected_parameter = st.selectbox("🧪 Parameter", parameters)
        
        # Advanced filters row
        st.markdown("#### Advanced Filters")
        col4, col5, col6, col7 = st.columns(4)
        
        with col4:
            start_date = st.date_input("📅 From Date", 
                                       value=datetime(2020, 1, 1),
                                       min_value=datetime(2020, 1, 1),
                                       max_value=datetime.now())
        
        with col5:
            end_date = st.date_input("📅 To Date", 
                                    value=datetime.now(),
                                    min_value=datetime(2020, 1, 1),
                                    max_value=datetime.now())
        
        with col6:
            severity_options = ['All Severities'] + sorted(df['Severity'].dropna().unique().tolist())
            selected_severity = st.selectbox("⚠️ Severity Level", severity_options)
        
        with col7:
            permit_number = st.text_input("📋 Permit Number", 
                                         placeholder="e.g. PA0012345")
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_county != 'All Counties':
        filtered_df = filtered_df[filtered_df['COUNTY_NAME'] == selected_county]
    
    if facility_search:
        filtered_df = filtered_df[filtered_df['PF_NAME'].str.contains(facility_search, case=False, na=False)]
    
    if selected_parameter != 'All Parameters':
        filtered_df = filtered_df[filtered_df['PARAMETER'] == selected_parameter]
    
    if permit_number:
        filtered_df = filtered_df[filtered_df['PERMIT_NUMBER'].str.contains(permit_number, case=False, na=False)]
    
    # Date filtering
    filtered_df['Date_Filter'] = pd.to_datetime(filtered_df['NON_COMPLIANCE_DATE'], errors='coerce')
    filtered_df = filtered_df[(filtered_df['Date_Filter'] >= pd.to_datetime(start_date)) & 
                             (filtered_df['Date_Filter'] <= pd.to_datetime(end_date))]
    
    if selected_severity != 'All Severities':
        filtered_df = filtered_df[filtered_df['Severity'] == selected_severity]
    
    # Results summary
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Results", f"{len(filtered_df):,}")
    with col2:
        st.metric("Unique Facilities", f"{filtered_df['PF_NAME'].nunique():,}")
    with col3:
        critical_count = len(filtered_df[filtered_df['Severity'] == 'Critical'])
        st.metric("Critical Violations", f"{critical_count:,}")
    with col4:
        recent_30 = len(filtered_df[filtered_df['Date_Filter'] >= (datetime.now() - timedelta(days=30))])
        st.metric("Last 30 Days", f"{recent_30:,}")
    
    # FULL RESULTS TABLE
    st.markdown("### 📊 Search Results")
    
    if len(filtered_df) > 0:
        # Sort by date
        filtered_df = filtered_df.sort_values('Date_Filter', ascending=False)
        
        # Prepare display dataframe with ALL columns
        display_df = filtered_df[['PF_NAME', 'COUNTY_NAME', 'PERMIT_NUMBER', 
                                 'PARAMETER', 'Percent_Over_Limit', 'Severity', 
                                 'NON_COMPLIANCE_DATE', 'MONITORING_PERIOD_END_DATE']].copy()
        
        # Format dates
        display_df['NON_COMPLIANCE_DATE'] = pd.to_datetime(display_df['NON_COMPLIANCE_DATE'], errors='coerce').dt.strftime('%b %d, %Y')
        display_df['MONITORING_PERIOD_END_DATE'] = pd.to_datetime(display_df['MONITORING_PERIOD_END_DATE'], errors='coerce').dt.strftime('%b %Y')
        
        # Rename columns for display
        display_df.columns = ['Facility Name', 'County', 'Permit #', 'Parameter', 
                             '% Over Limit', 'Severity', 'Violation Date', 'Monitoring Period']
        
        # Display with color coding
        def highlight_severity(row):
            if row['Severity'] == 'Critical':
                return ['background-color: #ffebee'] * len(row)
            elif row['Severity'] == 'High':
                return ['background-color: #fff3e0'] * len(row)
            elif row['Severity'] == 'Moderate':
                return ['background-color: #f1f8e9'] * len(row)
            else:
                return [''] * len(row)
        
        styled_df = display_df.style.apply(highlight_severity, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=500)
        
        # EXPORT SECTION - PREMIUM FEATURE
        st.markdown("### 💾 Export Options")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.success(f"✅ Ready to export {len(filtered_df):,} records")
        
        with col2:
            # CSV Export
            csv_buffer = io.StringIO()
            filtered_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label=f"📥 Download CSV ({len(filtered_df):,} records)",
                data=csv_data,
                file_name=f"permitinder_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                type="primary"
            )
        
        with col3:
            # Excel Export (Premium only)
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='Violations')
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label=f"📥 Download Excel",
                data=excel_data,
                file_name=f"permitinder_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Advanced analytics (Premium only)
        st.markdown("### 📈 Premium Analytics")
        
        tab1, tab2, tab3 = st.tabs(["Trend Analysis", "Top Violators", "Parameter Analysis"])
        
        with tab1:
            # Monthly trend
            monthly_violations = filtered_df.groupby(filtered_df['Date_Filter'].dt.to_period('M')).size()
            st.line_chart(monthly_violations, use_container_width=True)
        
        with tab2:
            # Top violating facilities
            top_facilities = filtered_df['PF_NAME'].value_counts().head(10)
            st.bar_chart(top_facilities, use_container_width=True)
        
        with tab3:
            # Parameter breakdown
            param_breakdown = filtered_df['PARAMETER'].value_counts().head(10)
            st.bar_chart(param_breakdown, use_container_width=True)
    
    else:
        st.info("No records found matching your search criteria. Try adjusting your filters.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p><strong>PermitMinder Premium</strong> | Full Database Access</p>
        <p>Data sourced from Pennsylvania DEP eDMR Public Records</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

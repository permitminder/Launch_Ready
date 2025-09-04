import streamlit as st
import pandas as pd
import io

# Page config
st.set_page_config(
    page_title="Pennsylvania Public Records Search",
    page_icon="📋",
    layout="wide"
)

# Load your actual processed data
@st.cache_data
def load_data():
    return pd.read_csv('pa_violations_launch_ready.csv')

# Main app
def main():
    # Header
    st.title("Pennsylvania Public Records: NPDES-Related Regulatory Actions and Orders (2020-2024)")
    st.subheader("Search public records and administrative documents with source links and CSV export.")
    
    # Load your processed violation data
    df = load_data()
    
    # Search inputs
    st.markdown("### Search Records")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # County filter using your actual data
        counties = ['All Counties'] + sorted(df['COUNTY_NAME'].unique().tolist())
        selected_county = st.selectbox("County", counties)
    
    with col2:
        # Facility name search using your actual column
        facility_search = st.text_input("Facility Name (partial match)", placeholder="e.g. STP, WWTP")
    
    with col3:
        # Parameter filter using your actual data - handle mixed data types
        param_list = df['PARAMETER'].dropna().astype(str).unique().tolist()
        parameters = ['All Parameters'] + sorted(param_list)
        selected_parameter = st.selectbox("Parameter", parameters)
    
    # Filter your actual data
    filtered_df = df.copy()
    
    if selected_county != 'All Counties':
        filtered_df = filtered_df[filtered_df['COUNTY_NAME'] == selected_county]
    
    if facility_search:
        filtered_df = filtered_df[filtered_df['PF_NAME'].str.contains(facility_search, case=False, na=False)]
    
    if selected_parameter != 'All Parameters':
        filtered_df = filtered_df[filtered_df['PARAMETER'] == selected_parameter]
    
    # Results
    st.markdown(f"### Search Results ({len(filtered_df)} records)")
    
    if len(filtered_df) > 0:
        # Display results using your actual columns
        display_df = filtered_df[['PF_NAME', 'COUNTY_NAME', 'PERMIT_NUMBER', 'PARAMETER', 
                                'Percent_Over_Limit', 'Severity', 'NON_COMPLIANCE_DATE']].copy()
        
        # Format the percentage column
        display_df['Percent_Over_Limit'] = display_df['Percent_Over_Limit'].apply(
            lambda x: f"{x:.0f}%" if pd.notna(x) else 'N/A'
        )
        
        st.dataframe(
            display_df,
            column_config={
                'PF_NAME': 'Facility Name',
                'COUNTY_NAME': 'County', 
                'PERMIT_NUMBER': 'Permit Number',
                'PARAMETER': 'Parameter',
                'Percent_Over_Limit': 'Exceedance',
                'Severity': 'Severity Level',
                'NON_COMPLIANCE_DATE': 'Date'
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Show chemical laundering candidates if any
        if 'Chemical_Laundering_Candidate' in filtered_df.columns:
            chemical_candidates = filtered_df[filtered_df['Chemical_Laundering_Candidate'] == True]
            if len(chemical_candidates) > 0:
                st.info(f"🧪 {len(chemical_candidates)} records show potential industrial discharge patterns")
        
        # CSV Export of your actual data
        st.markdown("### Export Results")
        
        # Convert to CSV
        csv_buffer = io.StringIO()
        filtered_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="Download Results as CSV",
            data=csv_data,
            file_name=f"pa_regulatory_records_{len(filtered_df)}_results.csv",
            mime="text/csv",
            type="primary"
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
        - Advanced search filters and bulk export
        - Chemical laundering detection algorithms
        - Historical trend analysis
        - Email alerts for new records
        - Priority support
        """)
    
    with col2:
        st.markdown("**7-Day Pilot Access**")
        st.markdown("**$97/month**")
        st.markdown("✅ Money-back guarantee")
        
        # CTA Button
        if st.button("Start 7-Day Pilot", type="primary", use_container_width=True):
            st.markdown("**Contact:** [permits@permitmlinder.com](mailto:permits@permitmlinder.com)")
            st.markdown("*Stripe payment processing available*")
    
    # Disclaimer
    st.markdown("---")
    st.markdown("""
    **Disclaimer:** This database is for informational purposes only. Information is sourced from Pennsylvania Department of Environmental Protection public records. Users should verify current information directly with the agency. No assertion is made regarding wrongdoing by any party. This tool does not constitute legal advice.
    """)

if __name__ == "__main__":
    main()

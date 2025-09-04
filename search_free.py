"""
FREE SEARCH INTERFACE - Limited Feature Set
Basic search only, 30-day data, max 100 results, no export
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="PermitMinder - Free Access",
    page_icon="🔍",
    layout="wide"
)

# Free tier styling
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Free tier styling */
    .free-badge {
        background: #6c757d;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 1rem;
    }
    
    /* Upgrade CTA styling */
    .upgrade-cta {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin: 2rem 0;
    }
    
    .upgrade-button {
        background: white;
        color: #667eea;
        padding: 12px 32px;
        border-radius: 8px;
        font-weight: bold;
        text-decoration: none;
        display: inline-block;
        margin-top: 1rem;
    }
    
    /* Simple table */
    .dataframe {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        border: 1px solid #e1e4e8;
    }
    
    /* Disabled elements */
    .disabled-feature {
        opacity: 0.5;
        pointer-events: none;
        position: relative;
    }
    
    .locked-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    return pd.read_csv('pa_exceedances_launch_ready.csv')

def main():
    # Free tier header
    st.markdown("""
    <div style='background-color: #2c3e50; margin: -1rem calc(50% - 50vw) 2rem; padding: 2rem;'>
        <div style='max-width: 1200px; margin: 0 auto;'>
            <span class='free-badge'>FREE TIER</span>
            <h1 style='color: white; margin: 0.5rem 0; font-weight: 600; font-size: 2.5rem;'>
                PermitMinder
            </h1>
            <p style='color: #ecf0f1; margin: 0.5rem 0; font-size: 1.25rem;'>
                Limited Access - Recent Records Only
            </p>
            <p style='color: #ffd700; font-size: 1rem; font-weight: bold;'>
                ⚡ Upgrade to access all 63,391 records and advanced features
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data and apply FREE TIER RESTRICTIONS
    df = load_data()
    total_records = len(df)
    
    # FREE TIER: Only last 30 days of data
    thirty_days_ago = datetime.now() - timedelta(days=30)
    df['Date_Filter'] = pd.to_datetime(df['NON_COMPLIANCE_DATE'], errors='coerce')
    df = df[df['Date_Filter'] >= thirty_days_ago]
    
    # Show limitations banner
    st.warning(f"""
    🔒 **Free Tier Limitations:**
    • Showing only last 30 days of data ({len(df):,} of {total_records:,} total records)
    • Maximum 100 results displayed
    • No export functionality
    • Basic search only
    
    **[Upgrade to Premium for $97/month →](mailto:permitminder@gmail.com)**
    """)
    
    # BASIC SEARCH ONLY - No advanced filters
    st.markdown("### 🔍 Basic Search")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # County filter
        counties = ['All Counties'] + sorted(df['COUNTY_NAME'].unique().tolist())
        selected_county = st.selectbox("Select County", counties)
    
    with col2:
        # Basic facility search
        facility_search = st.text_input("Search Facility Name", 
                                       placeholder="Enter facility name")
    
    # Show locked advanced features
    with st.expander("🔒 Advanced Filters (Premium Only)", expanded=False):
        st.markdown("""
        <div style='opacity: 0.5; padding: 1rem; background: #f8f9fa; border-radius: 8px;'>
            <p><strong>Unlock these premium filters:</strong></p>
            <ul>
                <li>📅 Custom date ranges (2020-2024)</li>
                <li>🧪 Parameter-specific search</li>
                <li>⚠️ Severity level filtering</li>
                <li>📋 Permit number lookup</li>
                <li>📊 Advanced analytics</li>
                <li>💾 CSV & Excel export</li>
            </ul>
            <p style='text-align: center; margin-top: 1rem;'>
                <strong>Upgrade to Premium to unlock all features</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Apply basic filters
    filtered_df = df.copy()
    
    if selected_county != 'All Counties':
        filtered_df = filtered_df[filtered_df['COUNTY_NAME'] == selected_county]
    
    if facility_search:
        filtered_df = filtered_df[filtered_df['PF_NAME'].str.contains(facility_search, case=False, na=False)]
    
    # FREE TIER: Limit to 100 results
    result_count = len(filtered_df)
    if result_count > 100:
        filtered_df = filtered_df.head(100)
        st.info(f"ℹ️ Showing first 100 of {result_count:,} results. Upgrade to see all results.")
    
    # Basic results summary
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Results (Limited)", f"{len(filtered_df):,} of {result_count:,}")
    with col2:
        st.metric("Date Range", "Last 30 Days Only")
    with col3:
        st.metric("Export", "🔒 Premium Only")
    
    # SIMPLIFIED RESULTS TABLE - Fewer columns
    st.markdown("### 📊 Search Results (Limited)")
    
    if len(filtered_df) > 0:
        # Sort by date
        filtered_df = filtered_df.sort_values('Date_Filter', ascending=False)
        
        # Simplified display - only essential columns
        display_df = filtered_df[['PF_NAME', 'COUNTY_NAME', 'PARAMETER', 
                                 'Severity', 'NON_COMPLIANCE_DATE']].copy()
        
        # Format dates
        display_df['NON_COMPLIANCE_DATE'] = pd.to_datetime(display_df['NON_COMPLIANCE_DATE'], errors='coerce').dt.strftime('%b %d, %Y')
        
        # Rename columns
        display_df.columns = ['Facility', 'County', 'Parameter', 'Severity', 'Date']
        
        # Display basic table
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # Show upgrade CTA instead of export
        st.markdown("""
        <div class='upgrade-cta'>
            <h3>🚀 Unlock Full Features</h3>
            <p>Get instant access to:</p>
            <ul style='text-align: left; max-width: 500px; margin: 1rem auto;'>
                <li>✅ All 63,391 historical records (2020-2024)</li>
                <li>✅ Advanced search filters</li>
                <li>✅ CSV & Excel export</li>
                <li>✅ Detailed violation data</li>
                <li>✅ Trend analytics</li>
                <li>✅ No result limits</li>
            </ul>
            <h4>Only $97/month</h4>
            <a href='mailto:permitminder@gmail.com' class='upgrade-button'>
                Upgrade to Premium →
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        # Disabled export section
        st.markdown("### 💾 Export Options")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.error("🔒 Export is a Premium feature - Upgrade to download results")
        
        with col2:
            st.button("Download CSV", disabled=True, help="Premium feature - Upgrade required")
    
    else:
        st.info("No records found in the last 30 days matching your search. Try adjusting your filters.")
        
        # Upgrade prompt when no results
        st.markdown("""
        <div style='background: #e3f2fd; padding: 1.5rem; border-radius: 8px; margin-top: 2rem;'>
            <h4>💡 Looking for older records?</h4>
            <p>The free tier only shows data from the last 30 days. 
            Upgrade to Premium to search our full database dating back to 2020.</p>
            <p style='margin-top: 1rem;'>
                <strong>Premium includes:</strong> 63,391 total records • 2020-2024 data • Advanced search
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Comparison table
    st.markdown("---")
    st.markdown("### Compare Plans")
    
    comparison_data = {
        'Feature': ['Database Access', 'Date Range', 'Search Results', 'Export CSV/Excel', 
                   'Advanced Filters', 'Analytics', 'Email Alerts', 'API Access'],
        'Free Tier': ['Last 30 days only', '30 days', 'Max 100', '❌', '❌', '❌', '❌', '❌'],
        'Premium ($97/mo)': ['Full database', '2020-2024', 'Unlimited', '✅', '✅', '✅', '✅', '✅']
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    st.table(comparison_df)
    
    # Footer with upgrade CTA
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 2rem; background: #f8f9fa; border-radius: 12px;'>
        <h3>Ready to unlock full access?</h3>
        <p>Join hundreds of environmental professionals using PermitMinder Premium</p>
        <p style='font-size: 1.5rem; font-weight: bold; color: #27ae60; margin: 1rem 0;'>
            Only $97/month
        </p>
        <p>
            <a href='mailto:permitminder@gmail.com' 
               style='background: #27ae60; color: white; padding: 12px 32px; 
                      border-radius: 8px; text-decoration: none; font-weight: bold;'>
                Start 7-Day Free Trial →
            </a>
        </p>
        <p style='color: #666; margin-top: 1rem; font-size: 0.9rem;'>
            No credit card required • Cancel anytime
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

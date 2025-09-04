"""
EMAIL SUBSCRIPTION MANAGEMENT
Users can subscribe to permit violation alerts
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Page config
st.set_page_config(
    page_title="PermitMinder - Email Alerts",
    page_icon="📧",
    layout="wide"
)

# PermitMinder styling
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
    
    /* Green buttons */
    .stButton > button[kind="primary"] {
        background-color: #27ae60;
        color: white;
        border: none;
        padding: 0.625rem 1.5rem;
        font-weight: 500;
        border-radius: 6px;
        transition: all 0.2s;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #219a52;
        transform: translateY(-1px);
    }
    
    /* Form styling */
    .subscription-form {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    
    /* Success message */
    .stSuccess {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_facilities():
    try:
        df = pd.read_csv('pa_exceedances_launch_ready.csv')
        # Get unique facilities with their permit numbers
        facilities = df.groupby(['PF_NAME', 'PERMIT_NUMBER', 'COUNTY_NAME']).size().reset_index()
        facilities = facilities[['PF_NAME', 'PERMIT_NUMBER', 'COUNTY_NAME']]
        return facilities.sort_values('PF_NAME')
    except:
        return pd.DataFrame()

def load_subscriptions():
    """Load existing subscriptions from CSV"""
    if os.path.exists('email_subscriptions.csv'):
        return pd.read_csv('email_subscriptions.csv')
    else:
        return pd.DataFrame(columns=['email', 'facilities', 'frequency', 'created_date', 'status'])

def save_subscription(email, facilities, frequency):
    """Save subscription to CSV"""
    subscriptions = load_subscriptions()
    
    # Create new subscription record
    new_sub = pd.DataFrame([{
        'email': email,
        'facilities': '|'.join(facilities),  # Store as pipe-separated string
        'frequency': frequency,
        'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'active'
    }])
    
    # Append to existing or create new
    subscriptions = pd.concat([subscriptions, new_sub], ignore_index=True)
    subscriptions.to_csv('email_subscriptions.csv', index=False)
    
    return True

def main():
    # Header
    st.markdown("""
    <div style='background-color: #2c3e50; margin: -1rem calc(50% - 50vw) 2rem; padding: 2rem;'>
        <div style='max-width: 1200px; margin: 0 auto;'>
            <h1 style='color: white; margin: 0; font-weight: 600; font-size: 2.5rem;'>
                📧 Email Alerts
            </h1>
            <p style='color: #ecf0f1; margin: 0.5rem 0 0 0; font-size: 1.25rem;'>
                Get notified when facilities exceed permit limits
            </p>
            <p style='color: #b0bec5; margin: 0.25rem 0 0 0; font-size: 1rem;'>
                Monitor specific facilities and receive automatic violation alerts
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'subscription_saved' not in st.session_state:
        st.session_state.subscription_saved = False
    
    # Load facilities
    facilities_df = load_facilities()
    
    if facilities_df.empty:
        st.error("Unable to load facility data")
        return
    
    # Subscription form
    st.markdown("### 🔔 Set Up Your Alerts")
    
    with st.form("subscription_form"):
        # Email input
        col1, col2 = st.columns([2, 1])
        
        with col1:
            email = st.text_input(
                "📧 Email Address",
                placeholder="your.email@example.com",
                help="We'll send violation alerts to this address"
            )
        
        with col2:
            st.markdown("")  # Spacer
            st.markdown("")
            verify_email = st.checkbox("Send test email after setup")
        
        st.divider()
        
        # Facility selection
        st.markdown("#### 🏭 Select Facilities to Monitor")
        
        # Filter options
        col3, col4 = st.columns(2)
        
        with col3:
            counties = ['All Counties'] + sorted(facilities_df['COUNTY_NAME'].unique().tolist())
            filter_county = st.selectbox("Filter by County", counties)
        
        with col4:
            search_term = st.text_input("Search Facilities", placeholder="Enter facility name...")
        
        # Apply filters
        filtered_facilities = facilities_df.copy()
        
        if filter_county != 'All Counties':
            filtered_facilities = filtered_facilities[filtered_facilities['COUNTY_NAME'] == filter_county]
        
        if search_term:
            filtered_facilities = filtered_facilities[
                filtered_facilities['PF_NAME'].str.contains(search_term, case=False, na=False)
            ]
        
        # Create facility display strings
        filtered_facilities['display'] = (
            filtered_facilities['PF_NAME'] + ' - ' + 
            filtered_facilities['PERMIT_NUMBER'] + ' (' + 
            filtered_facilities['COUNTY_NAME'] + ')'
        )
        
        # Multi-select for facilities
        selected_facilities = st.multiselect(
            "Select facilities (choose multiple)",
            options=filtered_facilities['display'].tolist(),
            help="Select one or more facilities to monitor for violations"
        )
        
        st.divider()
        
        # Notification frequency
        st.markdown("#### ⏰ Notification Frequency")
        
        frequency = st.radio(
            "How often would you like to receive alerts?",
            options=[
                "Immediate (when violations occur)",
                "Daily Summary",
                "Weekly Summary",
                "Monthly Report"
            ],
            index=0,
            help="Choose how frequently you want to receive violation notifications"
        )
        
        # Additional options
        st.markdown("#### ⚙️ Alert Options")
        
        col5, col6 = st.columns(2)
        
        with col5:
            severity_filter = st.multiselect(
                "Only alert for these severities",
                options=["Critical", "High", "Moderate"],
                default=["Critical", "High"],
                help="Only receive alerts for selected severity levels"
            )
        
        with col6:
            include_summary = st.checkbox("Include violation summary in email", value=True)
            include_csv = st.checkbox("Attach CSV with violation details", value=False)
        
        st.divider()
        
        # Submit button
        submitted = st.form_submit_button("💾 Save Subscription", type="primary", use_container_width=True)
        
        if submitted:
            # Validation
            if not email:
                st.error("Please enter an email address")
            elif '@' not in email:
                st.error("Please enter a valid email address")
            elif not selected_facilities:
                st.error("Please select at least one facility to monitor")
            else:
                # Save subscription
                success = save_subscription(email, selected_facilities, frequency)
                
                if success:
                    st.session_state.subscription_saved = True
                    st.rerun()
    
    # Show success message outside form
    if st.session_state.subscription_saved:
        st.success("""
        ✅ **Subscription Saved Successfully!**
        
        You will receive email alerts at the specified frequency when the selected facilities have new violations.
        
        **Next Steps:**
        - You'll receive a confirmation email shortly
        - Alerts will begin based on your selected frequency
        - You can update your preferences anytime
        """)
        
        if st.button("Set Up Another Alert"):
            st.session_state.subscription_saved = False
            st.rerun()
    
    # Show existing subscriptions
    st.markdown("---")
    st.markdown("### 📋 Manage Existing Subscriptions")
    
    subscriptions = load_subscriptions()
    
    if not subscriptions.empty:
        # Email lookup
        lookup_email = st.text_input("Enter email to view subscriptions", placeholder="your.email@example.com")
        
        if lookup_email:
            user_subs = subscriptions[subscriptions['email'] == lookup_email]
            
            if not user_subs.empty:
                st.success(f"Found {len(user_subs)} subscription(s) for {lookup_email}")
                
                for idx, sub in user_subs.iterrows():
                    with st.expander(f"Subscription created {sub['created_date']}", expanded=True):
                        facilities = sub['facilities'].split('|')
                        st.write(f"**Monitoring {len(facilities)} facilities**")
                        st.write(f"**Frequency:** {sub['frequency']}")
                        st.write(f"**Status:** {sub['status']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"Pause", key=f"pause_{idx}"):
                                subscriptions.loc[idx, 'status'] = 'paused'
                                subscriptions.to_csv('email_subscriptions.csv', index=False)
                                st.rerun()
                        
                        with col2:
                            if st.button(f"Delete", key=f"delete_{idx}", type="secondary"):
                                subscriptions = subscriptions.drop(idx)
                                subscriptions.to_csv('email_subscriptions.csv', index=False)
                                st.rerun()
            else:
                st.info(f"No subscriptions found for {lookup_email}")
    else:
        st.info("No subscriptions yet. Create your first alert above!")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>Email alerts are sent automatically when new violations are detected</p>
        <p>Data sourced from Pennsylvania DEP eDMR Public Records</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

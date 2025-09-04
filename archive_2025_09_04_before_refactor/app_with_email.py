"""
MAIN APP WITH EMAIL SUBSCRIPTION
Combines search, details, and email alerts
"""

import streamlit as st

# Page config
st.set_page_config(
    page_title="PermitMinder",
    page_icon="📋",
    layout="wide"
)

# Initialize session state
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'search'

# Navigation sidebar
st.sidebar.title("🧭 Navigation")

view = st.sidebar.radio(
    "Go to:",
    ["🔍 Search Records", "📧 Email Alerts", "📊 Dashboard"],
    index=0
)

# Update view based on selection
if "Search" in view:
    st.session_state.current_view = 'search'
elif "Email" in view:
    st.session_state.current_view = 'email'
else:
    st.session_state.current_view = 'dashboard'

# Load appropriate page
if st.session_state.current_view == 'search':
    import inter_app_enhanced_workflow
    inter_app_enhanced_workflow.main()
    
elif st.session_state.current_view == 'email':
    import email_subscription
    email_subscription.main()
    
else:  # Dashboard
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
    import pandas as pd
    import os
    from datetime import datetime, timedelta
    
    # Load violations data
    try:
        violations_df = pd.read_csv('pa_exceedances_launch_ready.csv')
        violations_df['Date'] = pd.to_datetime(violations_df['NON_COMPLIANCE_DATE'], errors='coerce')
    except:
        violations_df = pd.DataFrame()
    
    # Load subscriptions
    if os.path.exists('email_subscriptions.csv'):
        subs_df = pd.read_csv('email_subscriptions.csv')
        active_subs = subs_df[subs_df['status'] == 'active']
        
        # Get user's email (for demo, using first subscription)
        if len(active_subs) > 0:
            user_email = active_subs.iloc[0]['email']
            user_facilities = active_subs.iloc[0]['facilities'].split('|')
            
            # Extract facility names from the display format
            monitored_facilities = [f.split(' - ')[0] for f in user_facilities]
            
            # Filter violations for monitored facilities
            if not violations_df.empty and monitored_facilities:
                monitored_violations = violations_df[violations_df['PF_NAME'].isin(monitored_facilities)]
            else:
                monitored_violations = pd.DataFrame()
        else:
            monitored_violations = pd.DataFrame()
            monitored_facilities = []
    else:
        subs_df = pd.DataFrame()
        monitored_violations = pd.DataFrame()
        monitored_facilities = []
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active_count = len(subs_df[subs_df['status'] == 'active']) if not subs_df.empty else 0
        st.metric("Active Alerts", active_count)
    
    with col2:
        st.metric("Monitored Facilities", len(monitored_facilities))
    
    with col3:
        if not monitored_violations.empty:
            week_ago = datetime.now() - timedelta(days=7)
            recent_violations = len(monitored_violations[monitored_violations['Date'] >= week_ago])
            st.metric("Violations This Week", recent_violations)
        else:
            st.metric("Violations This Week", 0)
    
    with col4:
        if not monitored_violations.empty:
            month_ago = datetime.now() - timedelta(days=30)
            monthly_violations = len(monitored_violations[monitored_violations['Date'] >= month_ago])
            st.metric("Violations This Month", monthly_violations)
        else:
            st.metric("Violations This Month", 0)
    
    # Main content area
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Recent Alerts Section
        st.markdown("### 🚨 Recent Violations")
        
        if not monitored_violations.empty:
            recent = monitored_violations.nlargest(10, 'Date')
            
            for idx, row in recent.iterrows():
                severity_color = "🔴" if row['Severity'] == 'Critical' else "🟠" if row['Severity'] == 'High' else "🟡"
                
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.write(f"{severity_color} **{row['PF_NAME'][:30]}...**")
                        st.caption(f"Parameter: {row['PARAMETER']}")
                    with col2:
                        st.write(f"Permit: {row['PERMIT_NUMBER']}")
                        st.caption(f"{row['Severity']} Severity")
                    with col3:
                        st.write(pd.to_datetime(row['Date']).strftime('%b %d, %Y'))
                
                st.divider()
        else:
            st.info("No recent violations for your monitored facilities")
        
        # Violation Trends
        st.markdown("### 📈 Violation Trends")
        
        if not monitored_violations.empty:
            # Group by month for last 6 months
            six_months_ago = datetime.now() - timedelta(days=180)
            trend_data = monitored_violations[monitored_violations['Date'] >= six_months_ago].copy()
            
            if not trend_data.empty:
                trend_data['Month'] = trend_data['Date'].dt.to_period('M')
                monthly_counts = trend_data.groupby('Month').size()
                
                st.line_chart(monthly_counts, use_container_width=True)
            else:
                st.info("No data available for trend analysis")
        else:
            st.info("Start monitoring facilities to see trends")
    
    with col_right:
        # Your Subscriptions
        st.markdown("### 📋 Your Subscriptions")
        
        if monitored_facilities:
            st.success(f"Monitoring {len(monitored_facilities)} facilities")
            
            for facility in monitored_facilities[:5]:  # Show first 5
                st.write(f"• {facility[:30]}...")
            
            if len(monitored_facilities) > 5:
                st.caption(f"...and {len(monitored_facilities) - 5} more")
            
            st.divider()
            
            # Quick stats
            st.markdown("#### Quick Stats")
            if not monitored_violations.empty:
                top_violator = monitored_violations['PF_NAME'].value_counts().head(1)
                if not top_violator.empty:
                    st.write(f"**Most Violations:**")
                    st.write(f"{top_violator.index[0][:25]}...")
                    st.caption(f"{top_violator.values[0]} violations")
                
                critical_count = len(monitored_violations[monitored_violations['Severity'] == 'Critical'])
                st.write(f"**Critical Violations:** {critical_count}")
        else:
            st.info("No active subscriptions")
            if st.button("Set Up Your First Alert", type="primary"):
                st.session_state.current_view = 'email'
                st.rerun()
    
    st.markdown("---")
    st.markdown("### Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Search All Violations", type="primary", use_container_width=True):
            st.session_state.current_view = 'search'
            st.rerun()
    
    with col2:
        if st.button("📧 Manage Alerts", type="primary", use_container_width=True):
            st.session_state.current_view = 'email'
            st.rerun()
    
    with col3:
        if st.button("📥 Export Dashboard Data", use_container_width=True):
            if not monitored_violations.empty:
                csv = monitored_violations.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    file_name=f"dashboard_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

"""
MAIN APP - Toggle between Free and Premium versions
Use this for testing and demonstrating tier differences
"""

import streamlit as st
import importlib

# Page config
st.set_page_config(
    page_title="PermitMinder - Version Selector",
    page_icon="🔄",
    layout="wide"
)

# Initialize session state
if 'version' not in st.session_state:
    st.session_state.version = 'premium'

def main():
    # Sidebar version selector
    st.sidebar.title("⚙️ Version Control")
    st.sidebar.markdown("---")
    
    # Version toggle
    version = st.sidebar.radio(
        "Select Version:",
        ["Premium (Full Features)", "Free (Limited)"],
        index=0 if st.session_state.version == 'premium' else 1,
        help="Switch between free and premium versions for testing"
    )
    
    # Update session state
    if "Premium" in version:
        st.session_state.version = 'premium'
    else:
        st.session_state.version = 'free'
    
    # Show current version details
    if st.session_state.version == 'premium':
        st.sidebar.success("""
        ⭐ **Premium Version Active**
        • All 63,391 records
        • Advanced filters
        • Export enabled
        • Analytics included
        • No restrictions
        """)
    else:
        st.sidebar.warning("""
        🔒 **Free Version Active**
        • Last 30 days only
        • Max 100 results
        • Basic search only
        • No export
        • Limited features
        """)
    
    st.sidebar.markdown("---")
    
    # Quick comparison
    st.sidebar.markdown("### Quick Comparison")
    st.sidebar.markdown("""
    **Free Tier:**
    - 30-day data window
    - 100 result limit
    - Basic search only
    - No export
    
    **Premium Tier:**
    - Full 2020-2024 data
    - Unlimited results
    - Advanced filters
    - CSV/Excel export
    - Analytics dashboard
    """)
    
    # Developer notes
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📝 Developer Notes")
    st.sidebar.info("""
    This toggle is for testing only.
    
    In production:
    - User auth determines version
    - Stripe subscription status
    - Database flags user tier
    """)
    
    # Load appropriate version
    if st.session_state.version == 'premium':
        # Import and run premium version
        try:
            import search_full
            search_full.main()
        except ImportError:
            st.error("Error: search_full.py not found. Please ensure the file exists.")
            st.code("""
# Create search_full.py with the premium version code
# This file should contain the full-featured search interface
            """)
    else:
        # Import and run free version
        try:
            import search_free
            search_free.main()
        except ImportError:
            st.error("Error: search_free.py not found. Please ensure the file exists.")
            st.code("""
# Create search_free.py with the free version code
# This file should contain the limited search interface
            """)

if __name__ == "__main__":
    main()

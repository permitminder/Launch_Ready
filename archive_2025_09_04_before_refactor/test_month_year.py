"""
Quick test to see the month/year date selection
Run: streamlit run test_month_year.py
"""

import streamlit as st
from datetime import datetime, timedelta

st.title("Month/Year Selection Test")

st.markdown("### Date Range Selection")

col1, col2, col3, col4 = st.columns(4)

months = ['January', 'February', 'March', 'April', 'May', 'June',
          'July', 'August', 'September', 'October', 'November', 'December']

with col1:
    start_month = st.selectbox("From Month", months, index=0)

with col2:
    start_year = st.selectbox("From Year", 
                             list(range(2020, datetime.now().year + 1)),
                             index=0)

with col3:
    end_month = st.selectbox("To Month", months, 
                            index=datetime.now().month - 1)

with col4:
    end_year = st.selectbox("To Year", 
                           list(range(2020, datetime.now().year + 1)),
                           index=list(range(2020, datetime.now().year + 1)).index(datetime.now().year))

# Convert to dates
month_to_num = {month: i+1 for i, month in enumerate(months)}
start_date = datetime(start_year, month_to_num[start_month], 1)

# Get last day of end month
if month_to_num[end_month] == 12:
    end_date = datetime(end_year, 12, 31)
else:
    end_date = datetime(end_year, month_to_num[end_month] + 1, 1) - timedelta(days=1)

# Show results
st.markdown("---")
st.markdown("### Selected Range:")
st.info(f"From: **{start_month} {start_year}** (starts {start_date.strftime('%B %d, %Y')})")
st.info(f"To: **{end_month} {end_year}** (ends {end_date.strftime('%B %d, %Y')})")

# Show how it looks in display
st.success(f"Searching records from **{start_month} {start_year}** to **{end_month} {end_year}**")
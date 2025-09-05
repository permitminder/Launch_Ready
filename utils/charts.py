"""
Comprehensive charting module for PermitMinder application.

Provides advanced data visualization capabilities for permit exceedance records.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd

class PermitCharts:
    @staticmethod
    def severity_distribution(df):
        """
        Create pie chart of severity levels across permit exceedances.
        
        Args:
            df (pd.DataFrame): Permit exceedance DataFrame
        
        Returns:
            plotly.graph_objs._figure.Figure: Pie chart of severity distribution
        """
        severity_counts = df['SEVERITY'].value_counts()
        fig = px.pie(
            names=severity_counts.index, 
            values=severity_counts.values, 
            title='Permit Exceedance Severity Distribution',
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        return fig

    @staticmethod
    def compliance_trend_by_parameter(df):
        """
        Generate line chart showing compliance trends for different parameters.
        
        Args:
            df (pd.DataFrame): Permit exceedance DataFrame
        
        Returns:
            plotly.graph_objs._figure.Figure: Line chart of parameter compliance trends
        """
        # Prepare data for trend analysis
        df['MONTH'] = pd.to_datetime(df['NON_COMPLIANCE_DATE']).dt.to_period('M')
        grouped = df.groupby(['MONTH', 'PARAMETER'])['PERCENT_OVER_LIMIT'].mean().reset_index()
        grouped['MONTH'] = grouped['MONTH'].astype(str)

        fig = px.line(
            grouped, 
            x='MONTH', 
            y='PERCENT_OVER_LIMIT', 
            color='PARAMETER',
            title='Monthly Compliance Trend by Parameter',
            labels={'PERCENT_OVER_LIMIT': '% Over Permit Limit'},
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        fig.update_layout(
            xaxis_title='Month',
            yaxis_title='Average % Over Permit Limit'
        )
        return fig

    @staticmethod
    def county_exceedance_heatmap(df):
        """
        Create heatmap showing exceedance intensity by county.
        
        Args:
            df (pd.DataFrame): Permit exceedance DataFrame
        
        Returns:
            plotly.graph_objs._figure.Figure: Heatmap of county exceedances
        """
        # Aggregate exceedance data by county
        county_data = df.groupby('COUNTY_NAME').agg({
            'PERMIT_NUMBER': 'count',
            'PERCENT_OVER_LIMIT': 'mean'
        }).reset_index()
        
        county_data.columns = ['County', 'Exceedance Count', 'Average % Over Limit']
        
        fig = go.Figure(data=go.Heatmap(
            z=county_data['Average % Over Limit'],
            x=county_data['County'],
            colorscale='Viridis',
            colorbar=dict(title='Avg % Over Limit')
        ))
        
        fig.update_layout(
            title='Permit Exceedance Intensity by County',
            xaxis_title='County',
            yaxis_title='Intensity'
        )
        return fig

def render_charts(df):
    """
    Render interactive chart selection interface in Streamlit.
    
    Args:
        df (pd.DataFrame): Permit exceedance DataFrame
    """
    st.header("PermitMinder Data Visualizations")
    
    # Chart selection
    chart_options = {
        "Severity Distribution": PermitCharts.severity_distribution,
        "Compliance Trends by Parameter": PermitCharts.compliance_trend_by_parameter,
        "County Exceedance Heatmap": PermitCharts.county_exceedance_heatmap
    }
    
    # Dropdown for chart selection
    selected_chart = st.selectbox(
        "Choose Visualization", 
        list(chart_options.keys())
    )
    
    # Render selected chart
    if selected_chart:
        fig = chart_options[selected_chart](df)
        st.plotly_chart(fig, use_container_width=True)

# Optional: Main block for standalone testing
if __name__ == "__main__":
    # This would typically be used for testing or standalone script functionality
    import streamlit as st
    from utils.database import load_data
    
    df = load_data()
    render_charts(df)
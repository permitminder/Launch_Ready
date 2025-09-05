"""
Advanced data table module for PermitMinder application.

Provides interactive and exportable data exploration capabilities.
"""

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from typing import Optional, List, Dict, Any

class PermitDataTables:
    @staticmethod
    def interactive_permit_table(
        df: pd.DataFrame, 
        page_size: int = 20, 
        selection_mode: str = 'multiple'
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Create an interactive, filterable permit table using AgGrid.
        
        Args:
            df (pd.DataFrame): Permit exceedance DataFrame
            page_size (int, optional): Number of rows per page. Defaults to 20.
            selection_mode (str, optional): Row selection mode. Defaults to 'multiple'.
        
        Returns:
            Optional[List[Dict[str, Any]]]: Selected rows, if any
        """
        # Configure grid options
        gb = GridOptionsBuilder.from_dataframe(df)
        
        # Enable pagination
        gb.configure_pagination(
            paginationAutoPageSize=False, 
            paginationPageSize=page_size
        )
        
        # Configure selection
        gb.configure_selection(
            selection_mode=selection_mode, 
            use_checkbox=True
        )
        
        # Configure default column properties
        gb.configure_default_column(
            groupable=True, 
            value=True, 
            enableRowGroup=True, 
            aggFunc='count', 
            editable=False,
            resizable=True
        )
        
        # Custom cell styling for severity
        severity_color_map = JsCode("""
        function(params) {
            switch(params.value) {
                case 'Critical': return {'color': 'white', 'backgroundColor': 'darkred'};
                case 'High': return {'color': 'white', 'backgroundColor': 'red'};
                case 'Moderate': return {'color': 'black', 'backgroundColor': 'orange'};
                case 'Low': return {'color': 'black', 'backgroundColor': 'lightgreen'};
                default: return null;
            }
        }
        """)
        
        # Apply custom styling to Severity column
        gb.configure_column(
            'SEVERITY', 
            cellStyle=severity_color_map
        )
        
        # Build grid options
        grid_options = gb.build()
        
        # Render AgGrid
        st.header("Permit Exceedance Records")
        
        response = AgGrid(
            df, 
            gridOptions=grid_options,
            enable_enterprise_modules=True,
            height=500, 
            width='100%',
            theme='alpine'  # Clean, modern theme
        )
        
        return response.selected_rows

    @staticmethod
    def export_data_section(df: pd.DataFrame) -> None:
        """
        Create a data export section with multiple format options.
        
        Args:
            df (pd.DataFrame): Permit exceedance DataFrame
        """
        st.sidebar.header("📤 Data Export")
        
        # Export format selection
        export_format = st.sidebar.selectbox(
            "Select Export Format", 
            ["CSV", "Excel", "JSON"]
        )
        
        # Export filters
        st.sidebar.subheader("Export Filters")
        export_columns = st.sidebar.multiselect(
            "Select Columns to Export", 
            df.columns.tolist(), 
            default=df.columns.tolist()
        )
        
        # Prepare filtered DataFrame
        export_df = df[export_columns]
        
        # Export button and logic
        if st.sidebar.button("🚀 Export Data"):
            try:
                if export_format == "CSV":
                    csv = export_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="permit_exceedances.csv",
                        mime="text/csv"
                    )
                elif export_format == "Excel":
                    excel = export_df.to_excel(index=False)
                    st.download_button(
                        label="Download Excel",
                        data=excel,
                        file_name="permit_exceedances.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                else:  # JSON
                    json = export_df.to_json(orient='records')
                    st.download_button(
                        label="Download JSON",
                        data=json,
                        file_name="permit_exceedances.json",
                        mime="application/json"
                    )
                st.success(f"Data exported successfully as {export_format}!")
            except Exception as e:
                st.error(f"Export failed: {e}")

def render_data_tables(df: pd.DataFrame) -> None:
    """
    Render comprehensive data table interface.
    
    Args:
        df (pd.DataFrame): Permit exceedance DataFrame
    """
    # Sidebar for global data options
    st.sidebar.header("📊 Data Exploration")
    
    # Data view mode selection
    view_mode = st.sidebar.radio(
        "View Mode", 
        ["Interactive Table", "Export Data"]
    )
    
    # Render appropriate view
    if view_mode == "Interactive Table":
        selected_rows = PermitDataTables.interactive_permit_table(df)
        
        # Display selected rows details if any
        if selected_rows:
            st.subheader("Selected Rows Details")
            st.dataframe(pd.DataFrame(selected_rows))
    else:
        PermitDataTables.export_data_section(df)

# Optional: Main block for standalone testing
if __name__ == "__main__":
    # This would typically be used for testing or standalone script functionality
    import streamlit as st
    from utils.database import load_data
    
    df = load_data()
    render_data_tables(df)
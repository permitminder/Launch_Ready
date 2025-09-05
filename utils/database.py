"""
Database utility functions for PermitMinder application.

Handles data loading, processing, and basic query operations for permit exceedance records.
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

def load_data(
    primary_file: str = '/Users/ameliaminder/Desktop/Launch_Ready/pa_exceedances_launch_ready.csv',
    backup_file: str = '/Users/ameliaminder/Desktop/Launch_Ready/trimmed_pa_exceedances_2020_2024.csv'
) -> pd.DataFrame:
    """
    Load and cache permit exceedance data from CSV file.

    Args:
        primary_file (str, optional): Primary CSV file path.
        backup_file (str, optional): Backup CSV file path.

    Returns:
        pd.DataFrame: Loaded and processed DataFrame of permit exceedances.
    """
    @st.cache_data
    def _cached_load_data(path: str) -> pd.DataFrame:
        """
        Internal cached function to load data with additional processing.

        Args:
            path (str): File path to the CSV file.

        Returns:
            pd.DataFrame: Processed DataFrame with additional columns and type conversions.
        """
        try:
            # Load the raw data
            df = pd.read_csv(path)

            # Standardize column names
            df.columns = [col.upper().replace(' ', '_') for col in df.columns]

            # Ensure key columns exist
            _ensure_columns(df)

            # Date parsing with error handling
            date_columns = ['NON_COMPLIANCE_DATE', 'MONITORING_PERIOD_END_DATE']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            # Calculate severity 
            df['SEVERITY'] = _calculate_severity(df)

            return df

        except FileNotFoundError:
            st.error(f"Error: File not found at {path}")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Unexpected error loading data: {e}")
            return pd.DataFrame()

    # Try primary file first
    if os.path.exists(primary_file):
        return _cached_load_data(primary_file)
    
    # If primary file doesn't exist, try backup
    if os.path.exists(backup_file):
        st.warning(f"Primary file not found. Using backup file: {backup_file}")
        return _cached_load_data(backup_file)
    
    # If both files are missing, raise an error
    st.error("No data files found. Please check file paths.")
    return pd.DataFrame()

def _ensure_columns(df: pd.DataFrame) -> None:
    """
    Ensure critical columns exist in the DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame to check and potentially modify.
    """
    # List of columns that should always be present
    critical_columns = [
        'PERMIT_NUMBER', 
        'PF_NAME', 
        'COUNTY_NAME', 
        'PARAMETER', 
        'NON_COMPLIANCE_DATE'
    ]

    # Add missing columns with default values
    for col in critical_columns:
        if col not in df.columns:
            st.warning(f"Column {col} not found. Adding with default values.")
            if 'DATE' in col:
                df[col] = pd.NaT
            else:
                df[col] = 'Unknown'

def _calculate_severity(df: pd.DataFrame) -> pd.Series:
    """
    Calculate severity based on percentage over limit.

    Args:
        df (pd.DataFrame): Input DataFrame with exceedance data.

    Returns:
        pd.Series: Series of severity classifications.
    """
    def determine_severity(row: pd.Series) -> str:
        """
        Determine severity for a single row.

        Args:
            row (pd.Series): Single row of exceedance data.

        Returns:
            str: Severity level (Critical, High, Moderate, Low)
        """
        try:
            # Attempt to get percentage over limit
            if 'PERCENT_OVER_LIMIT' not in row.index:
                return 'Moderate'

            percent_over = row.get('PERCENT_OVER_LIMIT', 0)

            # Handle string percentages
            if isinstance(percent_over, str):
                try:
                    percent_over = float(percent_over.rstrip('%'))
                except (ValueError, TypeError):
                    return 'Moderate'

            # Severity calculation
            if percent_over > 200:
                return 'Critical'
            elif percent_over > 100:
                return 'High'
            elif percent_over > 50:
                return 'Moderate'
            else:
                return 'Low'

        except Exception:
            return 'Moderate'  # Default to moderate if any calculation fails

    return df.apply(determine_severity, axis=1)

def filter_exceedances(
    df: pd.DataFrame, 
    county: Optional[str] = None,
    facility: Optional[str] = None,
    parameter: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    severity: Optional[str] = None
) -> pd.DataFrame:
    """
    Apply advanced filtering to exceedance records.

    Args:
        df (pd.DataFrame): Input DataFrame of exceedance records.
        county (str, optional): Filter by county name.
        facility (str, optional): Filter by facility name.
        parameter (str, optional): Filter by specific parameter.
        start_date (datetime, optional): Start of date range filter.
        end_date (datetime, optional): End of date range filter.
        severity (str, optional): Filter by severity level.

    Returns:
        pd.DataFrame: Filtered DataFrame matching specified criteria.
    """
    filtered_df = df.copy()

    # County filter
    if county and county != 'All County Names':
        filtered_df = filtered_df[filtered_df['COUNTY_NAME'] == county]

    # Facility name filter
    if facility:
        filtered_df = filtered_df[
            filtered_df['PF_NAME'].str.contains(facility, case=False, na=False)
        ]

    # Parameter filter
    if parameter and parameter != 'All Parameters':
        filtered_df = filtered_df[filtered_df['PARAMETER'] == parameter]

    # Date range filter
    if start_date and end_date:
        filtered_df = filtered_df[
            (filtered_df['NON_COMPLIANCE_DATE'] >= start_date) & 
            (filtered_df['NON_COMPLIANCE_DATE'] <= end_date)
        ]

    # Severity filter
    if severity and severity != 'All Severities':
        filtered_df = filtered_df[filtered_df['SEVERITY'] == severity]

    return filtered_df

def get_unique_values(
    df: pd.DataFrame, 
    column: str, 
    include_all: bool = True
) -> List[str]:
    """
    Retrieves unique values for a given column.

    Args:
        df (pd.DataFrame): Input DataFrame.
        column (str): Column to extract unique values from.
        include_all (bool, optional): Whether to include 'All' option. Defaults to True.

    Returns:
        List[str]: List of unique values, optionally including 'All' option.
    """
    # Ensure column exists
    if column not in df.columns:
        st.warning(f"Column {column} not found in DataFrame")
        return ['All Columns']

    unique_values = df[column].dropna().unique().tolist()
    unique_values.sort()

    if include_all:
        all_prefix = 'All ' + column.replace('_', ' ').title()
        unique_values.insert(0, all_prefix)

    return unique_values
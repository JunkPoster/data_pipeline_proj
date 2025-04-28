"""
    File: transformer.py
  Author: Ian Featherston
    Date: 04/25/2025
    Desc: This script acts as the data transformer, taking the raw event data 
            from the S3 bucket, transforming it, and storing it in the 
            PostgreSQL database.
"""
import pandas as pd

from utilities.logger import setup_logger
from src.db_psql_interface import DatabaseInterface
from constants.psql_constants import PsqlCompanies, PsqlDevices, PsqlAds, \
                                     PsqlAuctions, PsqlUsers


class Transformer:
    """
    Class to transform raw event data from the S3 bucket, process it, and
    store it in the PostgreSQL database.
    """
    def __init__(self, psql_client: DatabaseInterface):
        """
        Initialize the transformer class.
        
        Parameters:
            psql_client (DatabaseInterface): Connection to the PostgreSQL server
        """
        self.logger = setup_logger()

        self.psql = psql_client


    def merge_all_tables(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Merges all tables on relevant keys, returning as a DataFrame

        Parameters:
            df (DataFrame): DataFrame to merge with all tables (raw_events)
        Returns:
            pd.DataFrame: A DataFrame that's been combined with all tables
        """
        # Merge with companies
        df2 = self.psql.get_table_df(PsqlCompanies.COMP_TABLE_NAME)
        merged = df.merge(df2, on='company_id')

        # Merge with devices
        df2 = self.psql.get_table_df(PsqlDevices.DEV_TABLE_NAME)
        merged = merged.merge(df2, on='device_id')

        # Merge with ads
        df2 = self.psql.get_table_df(PsqlAds.ADS_TABLE_NAME)
        merged = merged.merge(df2, on='ad_id')

        # Merge with auctions
        df2 = self.psql.get_table_df(PsqlAuctions.AUCT_TABLE_NAME)
        merged = merged.merge(df2, on='auction_id')

        # Merge with users
        df2 = self.psql.get_table_df(PsqlUsers.USERS_TABLE_NAME)
        merged = merged.merge(df2, on='user_id')

        return merged


    def clean_events(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms the raw events into more useful and clean data by joining 
        with related tables and presenting it in a more readable fashion.

        Parameters:
            df (pd.DataFrame): Contains all data from the raw_events table
        Returns:
            pd.DataFrame: A DataFrame of the processed events
        """
        # Ensure tables have already been merged
        if 'company_id_x' not in df.columns:
            df = self.merge_all_tables(df)

        # List of columns we want to keep
        keep = [
            'event_id', 'event_type', 'user_id', 'user_name', 'geo_location',
            'ad_type', 'company_name', 'auction_id', 'bid_amount', 'device_type'
        ]

        cleaned = df[keep]
        cleaned = cleaned.rename(
            columns={
                'geo_location': 'location',
                'company_name': 'company'
            }
        )

        return cleaned


    def report_company_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates a report based on the total amount spent on bidding per-
        company, returning it as a DataFrame

        Parameters:
            df (DataFrame): The DataFrame to perform analytics on
        Returns:
            pd.DataFrame: A DataFrame containing the processed data
        """
        # Ensure we're working with cleaned data
        if 'metadata' in df.columns:
            df = self.clean_events(df)

        # Columns to keep after cleaning
        keep = ['company', 'bid_amount', 'event_id']

        df = (
            df[keep]
            .groupby('company', as_index=False)
            .agg(
                bid_total=('bid_amount', 'sum'),
                total_events=('event_id', 'count')
            )
        )

        df['bid_total'] = pd.to_numeric(df['bid_total'], errors='coerce')
        df['avg_dollar_per_event'] = df['bid_total'] / df['total_events']

        # Add a currency ($) symbol to this column
        df['avg_dollar_per_event'] = df['avg_dollar_per_event'].apply(lambda x: f"${x:,.2f}")

        return df


    def report_device_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates a report based on devices used by users and which companies
        trend towards specific types.

        Parameters:
            df (DataFrame): A DataFrame to generate the report on
        Returns:
            DataFrame: The results stored as a DataFrame
        """
        # Ensure we're working with all tables
        if 'device_type' not in df.columns:
            df = self.merge_all_tables(df)

        # Columns to keep after merging
        keep = ['company_name', 'device_type']
        df = df[keep]

        # Create pivot table: device types as columns, their counts as values
        device_counts = (
            df.pivot_table(
                index='company_name',
                columns='device_type',
                aggfunc='size',
                fill_value=0
            )
            .reset_index()
            .rename_axis(None, axis=1)      # Clear index column's name
        )

        return device_counts


    def report_interaction_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates a report based on the 'event_type' column to show companies
        how their ads are being interacted with.

        Parameters:
            df (DataFrame): A DataFrame to generate the report on
        Returns:
            DataFrame: The results stored as a DataFrame
        """
        # Ensure we're working with all tables
        if 'company_name' not in df.columns:
            df = self.merge_all_tables(df)

        # Columns to keep after mergin
        keep = ['company_name', 'event_type']
        df = df[keep]

        # Create pivot table: event types as columns, their counts as values
        interaction_types = (
            df.pivot_table(
                index='company_name',
                columns='event_type',
                aggfunc='size',
                fill_value=0
            )
            .reset_index()
            .rename_axis(None, axis=1)      # Clear index column's name
        )

        return interaction_types

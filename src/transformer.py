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
from src.helpers.db_psql_interface import DatabaseInterface
from constants.psql_constants import PsqlCompanies, PsqlDevices, PsqlAds, \
                                     PsqlAuctions, PsqlUsers
from constants.helper_constants import TransformerConstants


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
        merged = df.copy()

        for table_name, key in [
            (PsqlCompanies.COMP_TABLE_NAME, 'company_id'),
            (PsqlDevices.DEV_TABLE_NAME, 'device_id'),
            (PsqlAds.ADS_TABLE_NAME, 'ad_id'),
            (PsqlAuctions.AUCT_TABLE_NAME, 'auction_id'),
            (PsqlUsers.USERS_TABLE_NAME, 'user_id'),
        ]:
            # Get the table DataFrame
            df2 = self.psql.get_table_df(table_name)

            # Merge with the main DataFrame
            merged = merged.merge(df2, on=key, suffixes=('', '_drop'))

            # Drop columns ending with '_drop' to avoid duplicates
            merged = merged.loc[:, ~merged.columns.str.endswith('_drop')]

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
        if 'company_name' not in df.columns:
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


    def report_company_stats(self, df: pd.DataFrame, company: str) -> pd.DataFrame:
        """
        Generates a report on the passed company's statistics by month.
        
        Columns:
            - month: Month of the year (YYYY-MM)
            - num_auctions: Total auctions won
            - num_events: Total events generated
            - num_users: Total unique users in events
            - num_ads: Total number of ads in 'ads' table
            - top_location: Most common geo_location in events
            - top_device: Most common device_type used in events
            - top_events: Most common event_type used in events
            - bid_total: Total spent bidding
            - avg_dollar_per_event: num_events / bid_total

        Parameters:
            df (DataFrame): The DataFrame to perform analytics on
            company (str): The name of the company to filter by
        Returns:
            pd.DataFrame: A DataFrame containing the processed data
        """
        # Ensure we're working with merged data
        if 'auction_timestamp' not in df.columns:
            df = self.merge_all_tables(df)

        # Convert UNIX timestamps to datetime and extract the month (YYYY-MM)
        df['timestamp'] = pd.to_datetime(df['auction_timestamp'], unit='s')
        df['month'] = df['timestamp'].dt.to_period('M').astype(str)

        # Filter by company name
        df = df[df['company_name'] == company]
        df = df.drop(columns=['company_name'])

        # Columns to keep after merging
        keep = [
            'month', 'bid_amount', 'event_id', 'user_id', 'ad_id',
            'geo_location', 'device_type', 'event_type'
        ]
        df = df[keep]

        # Group by month and aggregate the data
        df = (
            df.groupby('month', as_index=False)
            .agg(
                num_auctions=('bid_amount', 'count'),
                num_events=('event_id', 'count'),
                num_users=('user_id', 'nunique'),
                num_ads=('ad_id', 'nunique'),
                top_location=('geo_location', lambda x: x.mode()[0]),
                top_device=('device_type', lambda x: x.mode()[0]),
                top_events=('event_type', lambda x: x.mode()[0]),
                bid_total=('bid_amount', 'sum')
            )
        )

        # Convert 'bid_total' to numeric instead of string
        df['bid_total'] = pd.to_numeric(df['bid_total'], errors='coerce')

        # Create a new column calculating the average dollar-per-event spent
        df['avg_dollar_per_event'] = df['bid_total'] / df['num_events']

        # Add a currency ($) symbol to these columns, rounding to .2 decimal places
        df['avg_dollar_per_event'] = df['avg_dollar_per_event'].apply(lambda x: f"${x:,.2f}")
        df['bid_total'] = df['bid_total'].apply(lambda x: f"${x:,.2f}")

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


    def report_revenue(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Reports on the total revenue from auctions, our profit from it, and
        the total interactions.
        """
        # Ensure we're working with all tables
        if 'company_name' not in df.columns:
            df = self.merge_all_tables(df)

        # Convert UNIX timestamps to datetime and extract the month (YYYY-MM)
        df['timestamp'] = pd.to_datetime(df['auction_timestamp'], unit='s')
        df['month'] = df['timestamp'].dt.to_period('M').astype(str)

        # Columns to keep after merging
        keep = [
            'bid_amount', 'event_type', 'month'
        ]

        df = (
            df[keep]
            .groupby('month', as_index = False)
            .agg(
                num_auctions=('bid_amount', 'count'),
                bid_total=('bid_amount', 'sum'),
                num_events=('event_type', 'count')
            )
        )

        # Convert 'bid_total' to numeric from string
        df['bid_total'] = pd.to_numeric(df['bid_total'], errors='coerce')

        # Create column to show our total revenue, multiplying by our
        # specified constant value in constants\helper_constants.py
        df['total_revenue'] = df['bid_total'] * TransformerConstants.AUCTION_FEE

        # Add '$' symbol and round to 2 decimal places
        df['total_revenue'] = df['total_revenue'].apply(lambda x: f"${x:,.2f}")

        return df

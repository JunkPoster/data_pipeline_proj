"""
    File: psql_constants.py
  Author: Ian Featherston
    Date: 04/22/2025
    Desc: Contains the constant values for various parameters regarding a
            self-hosted PostgreSQL database connection and table structure. 

   Notes: Since there are so many dependencies, tables need to be populated in
            this order:
                1. companies
                2. devices
                3. ads
                4. auctions
                5. users
                6. events
        - Schemas are also written as dicts to ensure more consistency, and
            to help make future modifications easier.
        - Possible TODO: Make the table names and columns more dynamic to allow 
            for easier table creation and modification.
            - Currently, the table names are hardcoded in the SQL schema strings
                and you'll have to adjust the table creation within the
                /src/psql_client.py file.
"""
import os
from dotenv import load_dotenv      # To read from our '.env' file


# PostgreSQL Constants
class PsqlClient:
    """
    Constants for the PostgreSQL database connection
    """
    load_dotenv()

    # Database connection parameters
    DB_NAME = os.getenv("POSTGRES_DB")
    DB_USER = os.getenv("POSTGRES_USER")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    DB_HOST = os.getenv("POSTGRES_HOST", "db")
    DB_PORT = 5432


class PsqlCompanies:
    """
    Defines the companies table in the PostgreSQL database
    """
    COMP_TABLE_NAME = 'companies'
    COMP_TABLE_SCHEMA_DICT = {
        'company_id': 'SERIAL PRIMARY KEY',
        'company_name': 'TEXT NOT NULL UNIQUE'
    }
    COMP_TABLE_COLUMNS = list(COMP_TABLE_SCHEMA_DICT.keys())

    COMPANY_NAMES = [
        'Netflix', 'Hulu', 'Amazon', 'Google', 'Facebook',
        'Apple', 'Microsoft'
    ]

    @classmethod
    def schema_sql(cls):
        """
        Generates the SQL schema string for creating the table in PostgreSQL.
        
        Returns:
            str: SQL schema string for creating the table
        """
        return ',\n    '.join(
            f'{col} {dtype}' for col, dtype in cls.COMP_TABLE_SCHEMA_DICT.items()
        )


class PsqlDevices:
    """
    Defines the devices table in the PostgreSQL database
    """
    DEV_TABLE_NAME = 'devices'
    DEV_TABLE_SCHEMA_DICT = {
        'device_id': 'SERIAL PRIMARY KEY',
        'device_type': 'TEXT'
    }
    DEV_TABLE_COLUMNS = list(DEV_TABLE_SCHEMA_DICT.keys())

    DEVICE_TYPES = [
        'mobile', 'desktop', 'tablet', 'smart_tv', 'gaming_console'
    ]

    @classmethod
    def schema_sql(cls):
        """
        Generates the SQL schema string for creating the table in PostgreSQL.
        
        Returns:
            str: SQL schema string for creating the table
        """
        return ',\n    '.join(
            f'{col} {dtype}' for col, dtype in cls.DEV_TABLE_SCHEMA_DICT.items()
        )


class PsqlAds:
    """
    Defines the ads table in the PostgreSQL database
    """
    ADS_TABLE_NAME = 'ads'
    ADS_SIZE_LIMIT = 1_000          # Max num records to keep in the table
    ADS_TABLE_SCHEMA_DICT = {
        'ad_id': 'SERIAL PRIMARY KEY',
        'ad_type': 'TEXT',
        'ad_category': 'TEXT',
        'company_id': 'INTEGER REFERENCES companies(company_id)' # Foreign Key
    }
    ADS_TABLE_COLUMNS = list(ADS_TABLE_SCHEMA_DICT.keys())

    AD_CATEGORIES = [
        'sports', 'entertainment', 'technology', 'fashion', 'gaming', 
        'finance', 'health', 'film', 'streaming', 'news', 'travel',
        'food', 'automotive', 'education', 'real estate', 'lifestyle'
    ]
    AD_TYPES = [
        'video', 'banner', 'native', 'interstitial', 'rewarded', 'post'
    ]

    @classmethod
    def schema_sql(cls):
        """
        Generates the SQL schema string for creating the table in PostgreSQL.
        
        Returns:
            str: SQL schema string for creating the table
        """
        return ',\n    '.join(
            f'{col} {dtype}' for col, dtype in cls.ADS_TABLE_SCHEMA_DICT.items()
        )


class PsqlAuctions:
    """
    Definest the auctions table in the PostgreSQL database
    """
    AUCT_TABLE_NAME = 'auctions'
    AUCT_SIZE_LIMIT = 1_000             # Max num records to keep in the table
    AUCT_BID_MIN = 0.01                 # Minimum Bidding Amount
    AUCT_BID_MAX = 10.00                # Maximum Bidding Amount
    AUCT_TABLE_SCHEMA_DICT = {
        'auction_id': 'SERIAL PRIMARY KEY',
        'ad_id': 'INTEGER REFERENCES ads(ad_id)',                 # Foreign Key
        'company_id': 'INTEGER REFERENCES companies(company_id)', # Foreign Key
        'device_id': 'INTEGER REFERENCES devices(device_id)',     # Foreign Key
        'auction_timestamp': 'BIGINT',
        'bid_amount': 'NUMERIC(10, 2)'
    }
    AUCT_TABLE_COLUMNS = list(AUCT_TABLE_SCHEMA_DICT.keys())

    @classmethod
    def schema_sql(cls):
        """
        Generates the SQL schema string for creating the table in PostgreSQL.
        
        Returns:
            str: SQL schema string for creating the table
        """
        return ',\n    '.join(
            f'{col} {dtype}' for col, dtype in cls.AUCT_TABLE_SCHEMA_DICT.items()
        )


class PsqlUsers:
    """
    Holds the constants for the users table in the PostgreSQL database
    """
    USERS_TABLE_NAME = 'users'
    USERS_SIZE_LIMIT = 1_000          # Max num records to keep in the table
    USERS_TABLE_SCHEMA_DICT = {
        'user_id': 'TEXT PRIMARY KEY',      # UUID
        'user_name': 'TEXT',
        'user_email': 'TEXT',
        'user_phone': 'TEXT'
    }
    USERS_TABLE_COLUMNS = list(USERS_TABLE_SCHEMA_DICT.keys())

    @classmethod
    def schema_sql(cls):
        """
        Generates the SQL schema string for creating the table in PostgreSQL.
        
        Returns:
            str: SQL schema string for creating the table
        """
        return ',\n    '.join(
            f'{col} {dtype}' for col, dtype in cls.USERS_TABLE_SCHEMA_DICT.items()
        )


class PsqlRawEvents:
    """
    Constants for the raw_events table structure
    """
    EVENTS_TABLE_NAME = 'raw_events'
    EVENTS_SIZE_LIMIT = 1_000           # Max num records to keep in the table
    EVENTS_TABLE_SCHEMA_DICT = {
        'event_id': 'SERIAL PRIMARY KEY',
        'event_type': 'TEXT',
        'event_timestamp': 'BIGINT',
        'user_id': 'TEXT REFERENCES users(user_id)',              # Foreign Key
        'ad_id': 'INTEGER REFERENCES ads(ad_id)',                 # Foreign Key
        'company_id': 'INTEGER REFERENCES companies(company_id)', # Foreign Key
        'auction_id': 'INTEGER REFERENCES auctions(auction_id)',  # Foreign Key
        'device_id': 'INTEGER REFERENCES devices(device_id)',     # Foreign Key
        'geo_location': 'VARCHAR(2)',
        'metadata': 'JSONB'
    }
    EVENTS_TABLE_COLUMNS = list(EVENTS_TABLE_SCHEMA_DICT.keys())

    EVENT_TYPES = [
        'impression', 'click', 'conversion', 'hover', 'view', 'like', 'share'
    ]

    # This is a SQL schema string that helps generate the table dynamically
    @classmethod
    def schema_sql(cls):
        """
        Generates the SQL schema string for creating the table in PostgreSQL.
        
        Returns:
            str: SQL schema string for creating the table
        """
        return ',\n    '.join(
            f'{col} {dtype}' for col, dtype in cls.EVENTS_TABLE_SCHEMA_DICT.items()
        )


class PsqlProcessedEvents:
    """
    Constants for the processed_events table
    """
    PROC_EVENTS_TABLE_NAME = 'processed_events'

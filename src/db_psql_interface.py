"""
    File: db_psql_interface.py
  Author: Ian Featherston
    Date: 04/28/2025
    Desc: This script interfaces with the psql_client.py to perform our
            database-specific tasks
"""
import random
import json
from typing import List

import pandas as pd
from faker import Faker

from utilities.logger import setup_logger
from src.helpers.psql_client import PsqlConnector
from constants.psql_constants import PsqlClient, PsqlCompanies, PsqlDevices, \
                                     PsqlAds, PsqlAuctions, PsqlUsers, \
                                     PsqlRawEvents


class DatabaseInterface:
    """
    Class to interface with our PostgreSQL server and perform tasks specific
    to our database parameters and such.e
    """
    def __init__(self):
        """
        Initializes our DatabaseInterface class with our base parameters
        """
        self.logger = setup_logger()
        self.faker = Faker()

        self.dbname = PsqlClient.DB_NAME
        self.user = PsqlClient.DB_USER
        self.password = PsqlClient.DB_PASSWORD
        self.host = PsqlClient.DB_HOST
        self.port = PsqlClient.DB_PORT

        self.db = PsqlConnector(self.dbname, self.user, self.password,
                                self.host, self.port)

        self.conn = self.db.get_connection()
        self.cursor = self.conn.cursor()


    def save(self):
        """
        Simply saves any current changes made to the PostgreSQL connection
        """
        self.conn.commit()


    def exit(self):
        """
        Simply closes the connection to the PostgreSQL server
        """
        self.db.close_connection(self.conn, self.cursor)


    def get_connection(self):
        """
        Returns the connection to the server via an object.
        """
        return self.db.get_connection()


    def get_table_df(self, table_name: str, rows: int = -1) -> pd.DataFrame:
        """
        Return a table as a DataFrame

        Parameters:
            table_name (str): The table to retrieve
        """
        return self.db.get_table_data(self.cursor, table_name, rows)


    def store_events(self, records: List[dict], table_name: str, table_columns: List[str]):
        """
        Store the events (raw or processed) in the PostgreSQL database.
        """
        conn = self.db.get_connection()

        # If the table doesn't exist, create one
        if not self.db.table_exists(self.cursor, table_name):
            self.db.copy_df_into_table(
                cursor=self.cursor,
                df=pd.DataFrame(records),
                table_name=table_name,
                append=False
            )

        with conn:
            with conn.cursor() as cur:
                columns = table_columns[1:]   # Skip ID column
                col_names = ', '.join(columns)
                placeholders = ', '.join(['%s'] * len(columns))

                insert_sql = f"""
                    INSERT INTO {table_name} ({col_names})
                    VALUES ({placeholders});
                """

                for event in records:
                    # Safely extract values in column order
                    values = [event.get(col, None) for col in columns]

                    # Ensure metadata is a JSON String
                    if 'metadata' in columns:
                        idx = columns.index('metadata')
                        values[idx] = json.dumps(values[idx]) \
                                      if values[idx] else '{}'

                    cur.execute(insert_sql, values)
        conn.commit()


    def initialize_database(self):
        """
        Initializes our Database on the PostgreSQL server for our job.
        """
        self.db.init_db(self.dbname, self.user, self.password,
                        self.host, self.port)
        self.save()
        self.initialize_tables()

        self.save()
        self.populate_tables()


    def initialize_tables(self):
        """
        Initializes the PostgreSQL database and deletes any existing tables, 
        then creates new tables based on the defined schemas in the constants.
        """
        tables = [
            (PsqlCompanies.COMP_TABLE_NAME, PsqlCompanies.schema_sql()),
            (PsqlDevices.DEV_TABLE_NAME, PsqlDevices.schema_sql()),
            (PsqlAds.ADS_TABLE_NAME, PsqlAds.schema_sql()),
            (PsqlAuctions.AUCT_TABLE_NAME, PsqlAuctions.schema_sql()),
            (PsqlUsers.USERS_TABLE_NAME, PsqlUsers.schema_sql()),
            (PsqlRawEvents.EVENTS_TABLE_NAME, PsqlRawEvents.schema_sql())
        ]

        self.db.init_tables(self.cursor, tables)
        self.save()


    def get_raw_events(self) -> pd.DataFrame:
        """
        Returns the raw_events table as a DataFrame
        """
        return self.db.get_table_data(self.cursor, PsqlRawEvents.EVENTS_TABLE_NAME)


    def populate_tables(self):
        """
        This function is used to populate the various tables with their base data.
        It does NOT populate the events table, as that is done later 
        by the (simulated) producer.
        """
        self.logger.info("Populating tables with base data.")

        # The order is important here, as some tables depend on others.
        self.populate_companies(self.cursor)
        self.populate_devices(self.cursor)
        self.populate_ads(self.cursor)
        self.populate_auctions(self.cursor)
        self.populate_users(self.cursor)

        self.save()


    def populate_companies(self, cursor):
        """
        Populate the companies table with base data.
        """
        self.logger.info("Populating '%s' with base data.", PsqlCompanies.COMP_TABLE_NAME)

        for company_name in PsqlCompanies.COMPANY_NAMES:
            cursor.execute(f"""
                INSERT INTO {PsqlCompanies.COMP_TABLE_NAME}
                    (company_name)
                VALUES (%s);
            """, (company_name,)
            )


    def populate_devices(self, cursor):
        """
        Populate the devices table with base data.
        """
        self.logger.info("Populating '%s' with base data.", PsqlDevices.DEV_TABLE_NAME)

        for device_type in PsqlDevices.DEVICE_TYPES:
            cursor.execute(f"""
                INSERT INTO {PsqlDevices.DEV_TABLE_NAME}
                    (device_type)
                VALUES (%s);
            """, (device_type,)
            )


    def populate_ads(self, cursor):
        """
        Populate the ads table with base data.
        """
        self.logger.info("Populating '%s' with base data.", PsqlAds.ADS_TABLE_NAME)

        # Assuming the company_id is already populated in the companies table,
        # we want to fetch it for the ads table.
        cursor.execute(f'SELECT company_id FROM {PsqlCompanies.COMP_TABLE_NAME};')
        company_ids = [row[0] for row in cursor.fetchall()]

        # Check if company_ids is empty
        if not company_ids:
            self.logger.error("No company IDs found in the companies table. " \
                        "Check order of population.")
            return

        for _ in range(PsqlAds.ADS_SIZE_LIMIT):
            ad_type = random.choice(PsqlAds.AD_TYPES)
            ad_category = random.choice(PsqlAds.AD_CATEGORIES)
            company_id = random.choice(company_ids)

            cursor.execute(f"""
                INSERT INTO {PsqlAds.ADS_TABLE_NAME}
                    (ad_type, ad_category, company_id) 
                VALUES (%s, %s, %s);
            """, (ad_type, ad_category, company_id)
            )


    def populate_auctions(self, cursor):
        """
        Populate the auctions table with base data.
        """
        self.logger.info("Populating '%s' with base data.", PsqlAuctions.AUCT_TABLE_NAME)

        # Fetch valid ad-related data
        cursor.execute(f'''
            SELECT ad_id, ad_category, company_id 
            FROM {PsqlAds.ADS_TABLE_NAME};
        ''')
        ads = cursor.fetchall()

        if not ads:
            self.logger.error("No ads found in the ads table. " \
                        "Check order of population.")
            return

        # Fetch valid device-related data
        cursor.execute(f'''
            SELECT device_id, device_type 
            FROM {PsqlDevices.DEV_TABLE_NAME};
        ''')
        devices = [row[0] for row in cursor.fetchall()]

        if not devices:
            self.logger.error("No devices found in the devices table. " \
                        "Check order of population.")
            return

        for _ in range(PsqlAuctions.AUCT_SIZE_LIMIT):
            # This index is used to ensure consistent data across tables
            ad_index = random.randint(0, len(ads) - 1)
            ad_id, company_id = ads[ad_index][0], ads[ad_index][2]
            device_id = random.choice(devices)
            # UNIX Timestamp: 04-2025 to 05-2025
            auction_timestamp = random.randint(1_711_929_600, 1_743_465_600)
            bid_amount = round(random.uniform(
                    PsqlAuctions.AUCT_BID_MIN,
                    PsqlAuctions.AUCT_BID_MAX
                ), 2
            )

            cursor.execute(f"""
                INSERT INTO {PsqlAuctions.AUCT_TABLE_NAME}
                    (ad_id, company_id, device_id, auction_timestamp, bid_amount) 
                VALUES (%s, %s, %s, %s, %s)
            """, (ad_id, company_id, device_id, auction_timestamp, bid_amount)
            )


    def populate_users(self, cursor):
        """
        Populate the users table with base data.
        """
        self.logger.info("Populating '%s' with base data.", PsqlUsers.USERS_TABLE_NAME)

        for _ in range(PsqlUsers.USERS_SIZE_LIMIT):
            user_id = self.faker.uuid4()
            user_name = self.faker.name()
            user_email = self.faker.email()
            user_phone = self.faker.phone_number()

            cursor.execute(f"""
            INSERT INTO {PsqlUsers.USERS_TABLE_NAME} (
                    user_id, user_name, user_email, user_phone
                ) VALUES (%s, %s, %s, %s);
            """, (user_id, user_name, user_email, user_phone)
            )


    def generate_events(self, n: int = 100) -> pd.DataFrame:
        """
        Generate 'n' simulated ad events using relational data from the 
        database and the Faker package.

        Returns:
            pd.DataFrame: A DataFrame containing the generated events.
        """
        self.logger.info("Generating %d events.", n)
        df_events = []

        with self.conn.cursor() as cur:
            # Preload the related IDs
            cur.execute("SELECT user_id FROM users")
            user_ids = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT auction_id FROM auctions")
            auction_ids = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT ad_id FROM auctions")
            ad_ids = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT device_id FROM auctions")
            device_ids = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT company_id FROM auctions")
            company_ids = [row[0] for row in cur.fetchall()]

        # Generate events
        for _ in range(n):
            # This index helps ensure consistent data across the various tables
            auction_index = random.randint(0, len(auction_ids) - 1)
            event = {
                'user_id': random.choice(user_ids),
                'event_type': random.choice(PsqlRawEvents.EVENT_TYPES),
                # UNIX Timestamp: 04-2025 to 05-2025
                'event_timestamp': random.randint(1_711_929_600, 1_743_465_600),
                'ad_id': ad_ids[auction_index],
                'company_id': company_ids[auction_index],
                'auction_id': auction_ids[auction_index],
                # For some reason I had to cast this to a string to avoid NULLs
                'device_id': str(device_ids[auction_index]),
                'geo_location': self.faker.country_code(representation='alpha-2'),
                'metadata': {
                    'browser': self.faker.user_agent(),
                    'ip_address': self.faker.ipv4()
                }
            }
            df_events.append(event)

        return pd.DataFrame(df_events)

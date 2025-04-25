"""
    File: psql_client.py
  Author: Ian Featherston
    Date: 04/22/2025
    Desc: This script contains the PSQL client class that connects to a 
            PostgreSQL database and performs operations such as inserting 
            data into the database and creating tables. It is designed to be
            run as a standalone helper script, and it will not be run as
            part of the pipeline.
"""
import random

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pandas as pd
from faker import Faker

from utilities.logger import setup_logger
from constants.psql_constants import PsqlClient, PsqlCompanies, PsqlDevices, \
                                     PsqlAds, PsqlAuctions, PsqlUsers, PsqlEvents

faker = Faker()
logger = setup_logger()

def get_connection():
    """
    Establish a connection to the PostgreSQL database using the
    connection parameters defined in PsqlConstants.

    Returns:
        conn: A connection object to the PostgreSQL database.
    """
    conn = psycopg2.connect(
        dbname=PsqlClient.DB_NAME,
        user=PsqlClient.DB_USER,
        password=PsqlClient.DB_PASSWORD,
        host=PsqlClient.DB_HOST,
        port=PsqlClient.DB_PORT
    )
    logger.info("Connected to PostgreSQL database '%s' at %s:%s",
                PsqlClient.DB_NAME, PsqlClient.DB_HOST, PsqlClient.DB_PORT)
    return conn


def init_db():
    """
    Create the PostgreSQL database if it doesn't exist.

    Note: This function connects to the default 'postgres' database first 
            to check if the target database already exists. If not, it
            creates the target database.
    """
    # Connect to the default DB first
    conn = psycopg2.connect(
        dbname='postgres',
        user=PsqlClient.DB_USER,
        password=PsqlClient.DB_PASSWORD,
        host=PsqlClient.DB_HOST,
        port=PsqlClient.DB_PORT
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Check if the database already exists
    cur.execute("SELECT 1 from pg_database WHERE datname = %s", (PsqlClient.DB_NAME,))
    exists = cur.fetchone()

    if not exists:
        cur.execute(f"CREATE DATABASE {PsqlClient.DB_NAME};")
        logger.info("Database '%s' created successfully.", PsqlClient.DB_NAME)
    else:
        logger.info("Database '%s' already exists. Connecting to existing database.",
                    PsqlClient.DB_NAME)

    cur.close()
    conn.close()


def init_tables():
    """
    Initializes the PostgreSQL database and deletes any existing tables, 
    then creates new tables based on the defined schemas in the constants.
    """
    conn = get_connection()
    cursor = conn.cursor()

    tables = [
        (PsqlCompanies.COMP_TABLE_NAME, PsqlCompanies.schema_sql()),
        (PsqlDevices.DEV_TABLE_NAME, PsqlDevices.schema_sql()),
        (PsqlAds.ADS_TABLE_NAME, PsqlAds.schema_sql()),
        (PsqlAuctions.AUCT_TABLE_NAME, PsqlAuctions.schema_sql()),
        (PsqlUsers.USERS_TABLE_NAME, PsqlUsers.schema_sql()),
        (PsqlEvents.EVENTS_TABLE_NAME, PsqlEvents.schema_sql())
    ]

    for table_name, schema in tables:
        logger.info("Creating table '%s'", table_name)

        # Drop the tables first.
        cursor.execute(f"""
            DROP TABLE IF EXISTS {table_name} CASCADE;
        """)

        # Create the tables
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} ({schema});
        """)

    conn.commit()
    cursor.close()
    conn.close()


def populate_tables():
    """
    This function is used to populate the various tables with their base data.
    It does NOT populate the events table, as that is done later 
    by the (simulated) producer.
    """
    conn = get_connection()
    cursor = conn.cursor()

    logger.info("Populating tables with base data.")

    # The order is important here, as some tables depend on others.
    populate_companies(cursor)
    populate_devices(cursor)
    populate_ads(cursor)
    populate_auctions(cursor)
    populate_users(cursor)

    conn.commit()
    cursor.close()
    conn.close()


def populate_companies(cursor):
    """
    Populate the companies table with base data.
    """
    logger.info("Populating '%s' with base data.", PsqlCompanies.COMP_TABLE_NAME)

    for company_name in PsqlCompanies.COMPANY_NAMES:
        cursor.execute(f"""
            INSERT INTO {PsqlCompanies.COMP_TABLE_NAME}
                (company_name)
            VALUES (%s);
        """, (company_name,)
        )


def populate_devices(cursor):
    """
    Populate the devices table with base data.
    """
    logger.info("Populating '%s' with base data.", PsqlDevices.DEV_TABLE_NAME)

    for device_type in PsqlDevices.DEVICE_TYPES:
        cursor.execute(f"""
            INSERT INTO {PsqlDevices.DEV_TABLE_NAME}
                (device_type)
            VALUES (%s);
        """, (device_type,)
        )


def populate_ads(cursor):
    """
    Populate the ads table with base data.
    """
    logger.info("Populating '%s' with base data.", PsqlAds.ADS_TABLE_NAME)

    # Assuming the company_id is already populated in the companies table,
    # we want to fetch it for the ads table.
    cursor.execute(f'SELECT company_id FROM {PsqlCompanies.COMP_TABLE_NAME};')
    company_ids = [row[0] for row in cursor.fetchall()]

    # Check if company_ids is empty
    if not company_ids:
        logger.error("No company IDs found in the companies table. " \
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


def populate_auctions(cursor):
    """
    Populate the auctions table with base data.
    """
    logger.info("Populating '%s' with base data.", PsqlAuctions.AUCT_TABLE_NAME)

    # Fetch valid ad-related data
    cursor.execute(f'''
        SELECT ad_id, ad_category, company_id 
        FROM {PsqlAds.ADS_TABLE_NAME};
    ''')
    ads = cursor.fetchall()

    if not ads:
        logger.error("No ads found in the ads table. " \
                     "Check order of population.")
        return

    # Fetch valid device-related data
    cursor.execute(f'''
        SELECT device_id, device_type 
        FROM {PsqlDevices.DEV_TABLE_NAME};
    ''')
    devices = [row[0] for row in cursor.fetchall()]

    if not devices:
        logger.error("No devices found in the devices table. " \
                     "Check order of population.")
        return

    for _ in range(PsqlAuctions.AUCT_SIZE_LIMIT):
        ad_id, company_id = random.choice(ads)[0], random.choice(ads)[2]
        device_id = random.choice(devices)
        auction_timestamp = random.randint(1_600_000000, 1_700_000000)  # UNIX
        bid_amount = round(random.uniform(0.01, 10.00), 2)

        cursor.execute(f"""
            INSERT INTO {PsqlAuctions.AUCT_TABLE_NAME}
                (ad_id, company_id, device_id, auction_timestamp, bid_amount) 
            VALUES (%s, %s, %s, %s, %s)
        """, (ad_id, company_id, device_id, auction_timestamp, bid_amount)
        )


def populate_users(cursor):
    """
    Populate the users table with base data.
    """
    logger.info("Populating '%s' with base data.", PsqlUsers.USERS_TABLE_NAME)

    for _ in range(PsqlUsers.USERS_SIZE_LIMIT):
        user_id = faker.uuid4()
        user_name = faker.name()
        user_email = faker.email()
        user_phone = faker.phone_number()

        cursor.execute(f"""
           INSERT INTO {PsqlUsers.USERS_TABLE_NAME} (
                user_id, user_name, user_email, user_phone
            ) VALUES (%s, %s, %s, %s);
        """, (user_id, user_name, user_email, user_phone)
        )


def generate_events(n: int = 100) -> pd.DataFrame:
    """
    Generate 'n' simulated ad events using relational data from the 
    database and the Faker package.

    Returns:
        pd.DataFrame: A DataFrame containing the generated events.
    """
    logger.info("Generating %d events.", n)
    conn = get_connection()
    df_events = []

    with conn.cursor() as cur:
        # Preload the related IDs
        cur.execute("SELECT user_id FROM users")
        user_ids = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT auction_id FROM auctions")
        auction_ids = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT ad_id FROM ads")
        ad_ids = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT device_id FROM devices")
        device_ids = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT company_id FROM companies")
        company_ids = [row[0] for row in cur.fetchall()]

    # Generate events
    for _ in range(n):
        event = {
            'user_id': random.choice(user_ids),
            'event_type': random.choice(PsqlEvents.EVENT_TYPES),
            'event_timestamp': random.randint(1_600_000000, 1_700_000000), # UNIX
            'ad_id': random.choice(ad_ids),
            'company_id': random.choice(company_ids),
            'auction_id': random.choice(auction_ids),
            # For some reason I had to cast this to a string to avoid NULLs
            'device_id': str(random.choice(device_ids)),
            'geo_location': faker.country_code(representation='alpha-2'),
            'metadata': {
                'geo': faker.country_code(representation='alpha-2'),
                'browser': faker.user_agent(),
                'ip_address': faker.ipv4()
            }
        }
        df_events.append(event)

    return pd.DataFrame(df_events)

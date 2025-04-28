"""
    File: run.py
  Author: Ian Featherston
    Date: 03/26/2025 - Largely rewritten on 04/22/2025
    Desc: Runs all of the scripts in the project under one process so that
            the mock data is persistent and can be tested.
"""
from moto import mock_aws

from utilities.logger import setup_logger
from src.producer_script import Producer
from src.consumer_script import Consumer
from src.transformer import Transformer
from src.db_psql_interface import DatabaseInterface


@mock_aws
def main():
    """
    Creates a mock Kinesis stream and sends fake events to it
    """
    logger = setup_logger()

    # 1. [SETUP] Initialize the PostgreSQL database table
    db = DatabaseInterface()
    db.initialize_database()


    # 2A. [PRODUCE] Simulate produced events & send to the Kinesis stream
    producer = Producer(db)
    producer.generate_events()
    logger.info('Producer Script Finished.')


    # 3A. [CONSUME] Simulate a consumer by reading from the Kinesis stream
    consumer = Consumer(db)

    # Read the raw events from the Kinesis stream into a list of dictionaries
    records = consumer.read_from_kinesis()

    # 3B. [STORE] Store the events in the PostgreSQL database and S3 bucket
    # Mainly storing in PostgreSQL for testing purposes
    # Note: We retrieve the records from our PostgreSQL server for consistency,
    #       and so it'll automatically generate the 'event_id' column
    consumer.store_raw_events(records)
    df_events = db.get_raw_events()
    consumer.store_raw_events_in_s3(df_events)


    # 4A. [PROCESS] Process the records from the S3 bucket and clean them up
    df_events = consumer.get_raw_events_from_s3()
    transformer = Transformer(db)

    # Combine all tables into one based on common columns
    df_all_tables = transformer.merge_all_tables(df_events)

    # Clean the raw_events data
    cleaned_tables = transformer.clean_events(df_all_tables)

    # 4B. [PROCESS] Store the cleaned events dataframe in PostgreSQL
    consumer.store_processed_events(cleaned_tables)


    # Report 1: Report on each Company's stats regarding auctions & events.
    report_company_stats = transformer.report_company_stats(cleaned_tables)
    print(report_company_stats)

    # Report 2: Report on which devices companies see more interaction with.
    report_device_metrics = transformer.report_device_metrics(df_all_tables)
    print(report_device_metrics)

    # Report 3: Report on which interaction types each company sees the most of
    report_interaction_metrics = transformer.report_interaction_metrics(df_all_tables)
    print(report_interaction_metrics)

    db.exit()

if __name__ == '__main__':
    main()

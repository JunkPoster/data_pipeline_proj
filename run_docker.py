"""
    File: run_docker.py
  Author: Ian Featherston
    Date: 04/30/2025
    Desc: This version is ran when Docker is used to run the project.
"""
from moto import mock_aws

from utilities.logger import setup_logger
from src.producer import Producer
from src.consumer import Consumer
from src.transformer import Transformer
from src.helpers.db_psql_interface import DatabaseInterface
from src.visualizer import DataframeVisualizer


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

    # Clean the raw_events data
    cleaned_tables = transformer.clean_events(df_events)

    # 4B. [STORE] Store the cleaned events in the 'proccessed_events' table
    consumer.store_processed_events(cleaned_tables)


    # 5. [REPORT] Generate various reports and plot them using Matplotlib
    visualize = DataframeVisualizer()

    # Combine all tables into one based on common columns
    df_all_tables = transformer.merge_all_tables(df_events)

    # Report 1: Our Total Revenue over time from Auction bids
    report_revenue = transformer.report_revenue(df_all_tables)
    figure = visualize.plot_revenue_over_time(report_revenue)
    visualize.store_report(figure, 'report_revenue-over-time')

    # Report 2: Detailed Statistics for an sample Company
    sample_company = 'Amazon'
    report_company = transformer.report_company_stats(df_all_tables,
                                                      sample_company)
    print(sample_company, "'s statisticts: \n", report_company)
    figure = visualize.plot_company_stats(report_company, sample_company)
    visualize.store_report(figure, 'report_company-stats-' + sample_company)

    db.exit()


if __name__ == '__main__':
    main()

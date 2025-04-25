"""
    File: run.py
  Author: Ian Featherston
    Date: 03/26/2025 - Largely rewritten on 04/22/2025
    Desc: Runs all of the scripts in the project under one process so that
            the mock data is persistent and can be tested.
"""
import boto3
from moto import mock_aws

from utilities.logger import setup_logger
from constants.aws_constants import AWSConstants, KinesisConstants, S3Constants
from constants.helper_constants import ProducerConstants
from src.producer_script import Producer
from src.consumer_script import Consumer
from src.psql_client import init_db, init_tables, generate_events, \
                            populate_tables

@mock_aws
def main():
    """
    Creates a mock Kinesis stream and sends fake events to it
    """
    logger = setup_logger()

    # 1. [SETUP] Initialize the PostgreSQL database table
    init_db()
    init_tables()
    populate_tables()

    # Set up the AWS region and credentials
    # Note: Credentials aren't actually needed since we're mocking with moto
    # Change your region in \constants\aws_constants.py
    user_region_name = AWSConstants.REGION_NAME

    # Set up the Kinesis client and stream
    kinesis_client = boto3.client('kinesis', region_name=user_region_name)
    stream_name = KinesisConstants.STREAM_NAME

    # Create the mock Kinesis Data Stream (KDS)
    kinesis_client.create_stream(
            StreamName=stream_name,
            ShardCount=KinesisConstants.SHARD_COUNT
    )

    # Create mock S3 Bucket for storing raw events
    s3_client = boto3.client('s3', region_name=user_region_name)
    bucket_name = S3Constants.RAW_EVENTS_BUCKET_NAME
    s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={
            'LocationConstraint': user_region_name
        }
    )


    # 2A. [PRODUCE] Simulate produced events & send to the Kinesis stream
    logger.info("Initializing producer for stream: '%s'", stream_name)
    producer = Producer(kinesis_client, stream_name)

    # Generate a set amount of data to push to the Kinesis stream
    # Note: The data is generated using the PostgreSQL database for consistency.
    # Change the number of events in \constants\helper_constants.py
    events_df = generate_events(ProducerConstants.EVENT_TOTAL)

    # 2B. [PUSH] Push the events to the Kinesis stream
    producer.send_events(events_df)
    logger.info('Producer Script Finished.')


    # 3A. [CONSUME] Simulate a consumer by reading from the Kinesis stream
    # Create a consumer instance, then read the raw events from the KDS
    logger.info("Initializing consumer for stream: '%s'", stream_name)
    consumer = Consumer(kinesis_client, s3_client, stream_name, bucket_name)

    # Read the raw events from the Kinesis stream into a list of dictionaries
    records = consumer.read_from_kinesis()

    # 3B. [STORE] Store the events in the PostgreSQL database and S3 bucket
    # Mainly storing in PostgreSQL for testing purposes
    consumer.store_in_postgres_batch(records)
    consumer.store_in_s3(records, 'raw-events.json')
    logger.info('Consumer Script Finished.')


    # 4. [PROCESS] Process the records from the S3 bucket


if __name__ == '__main__':
    main()

"""
    File: consumer_script.py
  Author: Ian Featherston
    Date: 03/28/2025 - Largely rewritten on 04/22/2025
    Desc: This script simulates a consumer by taking the data from the 
            Kinesis stream, processing it, then storing it in the Postgres
            database.
"""
from typing import List

import pandas as pd

from utilities.logger import setup_logger
from src.helpers.kinesis import KinesisConnector
from src.helpers.s3 import S3BucketConnector
from src.helpers.db_psql_interface import DatabaseInterface
from constants.aws_constants import KinesisConstants, S3Constants
from constants.psql_constants import PsqlRawEvents, PsqlProcessedEvents


class Consumer:
    """
    Class to simulate a consumer by reading data from a Kinesis stream
    and processing it.
    """
    def __init__(self, psql_client: DatabaseInterface):
        """
        Initialize the consumer with the Kinesis client, S3 client, 
            stream name, and bucket name.
        Parameters:
            s3_client (boto3): The S3 client
            psql_client: Connection to the PostgreSQL Database
        """
        self.logger = setup_logger()

        # Connect to the Kinesis Stream
        self.kinesis = KinesisConnector(
            stream_name=KinesisConstants.STREAM_NAME,
            region=KinesisConstants.REGION_NAME
        )

        # Connect to the S3 Bucket and create it
        self.s3 = S3BucketConnector(
            bucket_name=S3Constants.RAW_EVENTS_BUCKET_NAME
        )
        self.s3.create_bucket()

        self.psql = psql_client


    def read_from_kinesis(self) -> List[dict]:
        """
        Fetch data from the mock Kinesis stream, and return the records 
        as a list of dictionaries.
        
        Returns:
            List[dict]: A list of records fetched from the Kinesis stream
        """
        return self.kinesis.read_from_stream(
            shard_id=KinesisConstants.SHARD_ID,
            iter_type=KinesisConstants.SHARD_ITERATOR_TYPE
        )


    def store_raw_events(self, records: List[dict]):
        """
        Store the raw events in the PostgreSQL database.
        """
        self.psql.store_events(
            records=records,
            table_name=PsqlRawEvents.EVENTS_TABLE_NAME,
            table_columns=PsqlRawEvents.EVENTS_TABLE_COLUMNS
        )
        self.logger.info("Raw events stored into '%s'.",
                         PsqlRawEvents.EVENTS_TABLE_NAME)


    def store_processed_events(self, df: pd.DataFrame):
        """
        Store the processed events in the PostgreSQL database
        """
        self.logger.info("Storing processed events into '%s' table.",
                    PsqlProcessedEvents.PROC_EVENTS_TABLE_NAME)

        if df.empty:
            self.logger.warning("The passed DataFrame is empty!")
            return

        self.psql.db.copy_df_into_table(
            cursor=self.psql.cursor,
            df=df,
            table_name=PsqlProcessedEvents.PROC_EVENTS_TABLE_NAME,
            append=False
        )
        self.psql.save()

        self.logger.info("Events stored into '%s' table.",
                    PsqlProcessedEvents.PROC_EVENTS_TABLE_NAME)


    def store_raw_events_in_s3(self, df: pd.DataFrame):
        """
        Stores the passed DataFrame into the S3 Bucket

        Parameters:
            df (pd.DataFrame): The data (table) to be stored
        """
        self.s3.store_df_in_bucket(df, S3Constants.RAW_EVENTS_KEY)


    def get_raw_events_from_s3(self) -> pd.DataFrame:
        """
        Fetch the raw events from the S3 bucket

        Returns:
            pd.DataFrame: Contains the data read from the S3 bucket
        """
        return self.s3.load_json_from_s3(S3Constants.RAW_EVENTS_KEY)

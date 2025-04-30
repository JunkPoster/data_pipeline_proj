"""
    File: producer_script.py
  Author: Ian Featherston
    Date: 03/26/2025 - Largely rewritten on 04/22/2025
    Desc: This script simulates a producer by generating fake events
            and sending them to a Kinesis stream.
"""
import pandas as pd

from utilities.logger import setup_logger
from src.helpers.kinesis import KinesisConnector
from constants.aws_constants import KinesisConstants
from constants.helper_constants import ProducerConstants


class Producer:
    """
    Class to simulate a producer by generating fake events and sending them 
    to a mock Kinesis stream
    """
    def __init__(self, db):
        """
        Initialize the producer with the Kinesis client and stream name

        Parameters:
            db: A connection to the psycopg2 client (PostgreSQL Database)
        """
        self.logger = setup_logger()

        self.db = db
        self.stream_name = KinesisConstants.STREAM_NAME
        self.kinesis = KinesisConnector(
                stream_name=self.stream_name,
                region=KinesisConstants.REGION_NAME
        )
        self.kinesis.create_stream(
            shard_count=KinesisConstants.SHARD_COUNT
        )


    def send_event(self, event):
        """
        Send a single event to the Kinesis stream

        Parameters:
            kinesis_client (boto3): The Kinesis client
            stream_name (str): The name of the Kinesis
        """
        self.logger.info("Sending event to Kinesis stream.")

        self.kinesis.send_to_stream(
            data=event,
            key=event['user_id']
        )


    # Send a DataFrame of events to Kinesis
    def send_events(self, events_df: pd.DataFrame):
        """
        Send a DataFrame of events to the Kinesis stream

        Parameters:
            events_df (pd.DataFrame): The DataFrame containing the events
        """
        self.logger.info("Sending events to Kinesis stream.")

        for _, row in events_df.iterrows():
            event = row.to_dict()
            self.kinesis.send_to_stream(
                data=event,
                key=event['user_id']
            )


    def generate_events(self, num_events: int = ProducerConstants.EVENT_TOTAL):
        """
        Generate a series of raw events to be pushed to the KDS
        """
        df_raw_events = self.db.generate_events(num_events)

        # Push the events to stream
        self.send_events(df_raw_events)

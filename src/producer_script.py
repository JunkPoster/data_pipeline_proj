"""
    File: producer_script.py
  Author: Ian Featherston
    Date: 03/26/2025 - Largely rewritten on 04/22/2025
    Desc: This script simulates a producer by generating fake events
            and sending them to a Kinesis stream.
"""
import json

import boto3
import pandas as pd

from utilities.logger import setup_logger

class Producer:
    """
    Class to simulate a producer by generating fake events and sending them 
    to a mock Kinesis stream
    """
    def __init__(self, kinesis_client: boto3, stream_name: str):
        """
        Initialize the producer with the Kinesis client and stream name

        Parameters:
            kinesis_client (boto3): The Kinesis client
            stream_name (str): The name of the Kinesis stream
        """
        self.logger = setup_logger()
        self.kinesis_client = kinesis_client
        self.stream_name = stream_name

    # Send a single event to Kinesis
    def send_event(self, event):
        """
        Send a fake event to the Kinesis stream

        Parameters:
            kinesis_client (boto3): The Kinesis client
            stream_name (str): The name of the Kinesis
        """
        self.logger.info("Sending event to Kinesis stream.")
        self.kinesis_client.put_record(
            StreamName=self.stream_name,
            Data=json.dumps(event),
            PartitionKey=event['user_id']
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
            self.kinesis_client.put_record(
                StreamName=self.stream_name,
                Data=json.dumps(event),
                PartitionKey=event['user_id']
            )

"""
    File: kinesis.py
  Author: Ian Featherston
    Date: 04/25/2025
    Desc: Contains the KinesisConnector class which is used to interact 
            with Kinesis Data Streams.
"""
import json
from typing import List

import boto3

from utilities.logger import setup_logger


class KinesisConnector:
    """
    A simple class to interact with Kinesis
    """
    def __init__(self, stream_name: str, region: str):
        """
        Initialize the Kinesis Data Stream
        """
        self.logger = setup_logger()

        self.kinesis_client = boto3.client('kinesis', region_name=region)
        self.stream_name = stream_name


    def create_stream(self, shard_count: int):
        """
        Creates a Kinesis Stream

        Parameters:
            shard_count (int): Number of shards to allocate to the stream
        """
        self.logger.info("Creating a new Kinesis Stream, '%s'.", self.stream_name)
        self.kinesis_client.create_stream(
            StreamName=self.stream_name,
            ShardCount=shard_count
        )


    def get_client(self) -> boto3:
        """
        Return this instance's kinesis_client object
        """
        return self.kinesis_client


    def send_to_stream(self, data, key):
        """
        Sends the passed data into the Kinesis stream

        Parameters:
            data: The data to push to stream
            key: The Partition Key of the data
        """
        self.logger.info("Sending data to Kinesis Stream '%s'.", self.stream_name)

        self.kinesis_client.put_record(
            StreamName=self.stream_name,
            Data=json.dumps(data),
            PartitionKey=key
        )


    def read_from_stream(self, shard_id: str, iter_type: str) -> List[dict]:
        """
        Reads data from the Kinesis stream, returning as a list of dictionaries

        Parameters:
            shard_id (str): The ID of the shard to read from 
                - (i.e. 'shardId-00000000000')
            iter_type (str): Method to read through the shard 
                - (i.e. 'TRIM_HORIZON', read from start)
        """
        # Get the shard iterator and read from the start.
        shard_iterator = self.kinesis_client.get_shard_iterator(
            StreamName=self.stream_name,
            ShardId=shard_id,
            ShardIteratorType=iter_type
        )['ShardIterator']

        # Read records from the Kinesis stream into a list of dictionaries
        self.logger.info("Reading from Kinesis stream '%s'.", self.stream_name)

        records = []
        while True:
            response = self.kinesis_client.get_records(
                    ShardIterator=shard_iterator,
                    Limit=10
            )

            # Check if there are any records to process, if not, break the loop
            if not response['Records']:
                self.logger.info("No more records to read.")
                break

            # Load the records into a list of dictionaries
            for record in response['Records']:
                payload = json.loads(record['Data'])
                records.append(payload)

            # Update the shard iterator for the next read
            shard_iterator = response['NextShardIterator']

        self.logger.info("Received %s records from Kinesis stream '%s'.",
                         str(len(records)), self.stream_name)

        return records

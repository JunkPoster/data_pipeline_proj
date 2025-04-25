"""
    File: consumer_script.py
  Author: Ian Featherston
    Date: 03/28/2025 - Largely rewritten on 04/22/2025
    Desc: This script simulates a consumer by taking the data from the 
            Kinesis stream, processing it, then storing it in the Postgres
            database.
"""
import json
from typing import List
import pandas as pd

from src.psql_client import get_connection
from utilities.logger import setup_logger
from constants.aws_constants import KinesisConstants
from constants.psql_constants import PsqlEvents

class Consumer:
    """
    Class to simulate a consumer by reading data from a Kinesis stream
    and processing it.
    """
    def __init__(self, kinesis_client, s3_client, stream_name, bucket_name):
        """
        Initialize the consumer with the Kinesis client, S3 client, 
            stream name, and bucket name.
        Parameters:
            kinesis_client (boto3): The Kinesis client
            s3_client (boto3): The S3 client
            stream_name (str): The name of the Kinesis stream
            bucket_name (str): The name of the S3 bucket
        """
        self.logger = setup_logger()

        # Constants necessary for reading from the same mock Kinesis stream
        self.kinesis = kinesis_client
        self.s3 = s3_client
        self.stream_name = stream_name
        self.bucket_name = bucket_name

    def read_from_kinesis(self) -> List[dict]:
        """
        Fetch data from the mock Kinesis stream, and return the records 
        as a list of dictionaries.
        
        Returns:
            List[dict]: A list of records fetched from the Kinesis stream
        """
        # Get the shard iterator and read from the start.
        shard_iterator = self.kinesis.get_shard_iterator(
            StreamName=self.stream_name,
            ShardId=KinesisConstants.SHARD_ID,              # Default shard ID
            ShardIteratorType=KinesisConstants.SHARD_ITERATOR_TYPE
        )['ShardIterator']

        # Read records from the Kinesis stream into a list of dictionaries
        self.logger.info("Reading from Kinesis stream '%s'.", self.stream_name)
        records = []
        while True:
            response = self.kinesis.get_records(
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

    def store_in_s3(self, data: dict, key: str = 'stored_data.json'):
        """
        Store the processed data in S3.

        Parameters:
            data (dict): The processed data to be stored
        """
        self.logger.info("Storing data in S3 as '%s'.", key)
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json.dumps(data, indent=4)
        )

    def store_in_postgres_batch(self, records: List[dict]):
        """
        Store the event in the PostgreSQL database.

        I tried to write this to be more flexible to possible schema changes.
        """
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                columns = PsqlEvents.EVENTS_TABLE_COLUMNS[1:]   # Skip ID column
                col_names = ', '.join(columns)
                placeholders = ', '.join(['%s'] * len(columns)) # %s for each column

                insert_sql = f'''
                    INSERT INTO {PsqlEvents.EVENTS_TABLE_NAME} ({col_names})
                    VALUES ({placeholders});
                '''

                for event in records:
                    # Safely extract values in column order
                    values = [event.get(col, None) for col in columns]

                    # Ensure metadata is a JSON String
                    if 'metadata' in columns:
                        idx = columns.index('metadata')
                        values[idx] = json.dumps(values[idx]) \
                                      if values[idx] else '{}'

                    cur.execute(insert_sql, values)

    def fetch_all_events(self):
        """
        Retrieve all events from the PostgreSQL database and return them 
        as a DataFrame.

        Returns:
            pd.DataFrame: A DataFrame containing all events from the database
        """
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM events", conn)
        conn.close()
        return df

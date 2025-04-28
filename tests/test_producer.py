
'''
    File: test_producer.py
  Author: Ian Featherston
    Date: 03/26/2025
    Desc: This script tests that the producer_script.py file is running
            correctly by reading the data from the Kinesis stream.
'''
import json
import time

import boto3
from faker import Faker
from moto import mock_aws

# DEBUG: Read records from Kinesis
@mock_aws
def read_events(kinesis_client, stream_name):
    '''
    Debug Function: Reads the data in the stream
    '''
    # Get the shard iterator
    shard_iterator = kinesis_client.get_shard_iterator(
        StreamName=stream_name,
        ShardId='shardId-000000000000',     # Default shard ID
        ShardIteratorType='TRIM_HORIZON'    # Read from the start
    )['ShardIterator']

    # Get records from the stream
    records = kinesis_client.get_records(
        ShardIterator=shard_iterator,
        Limit=10  # Maximum number of records to retrieve
    )

    # Process and print retrieved records
    for record in records['Records']:
        data = json.loads(record['Data'])
        print(f"Received: {data}")

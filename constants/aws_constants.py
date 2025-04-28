"""
    File: aws_constants.py
  Author: Ian Featherston
    Date: 03/26/2025 - Largely rewritten on 04/23/2025
    Desc: Contains the constant values for various parameters regarding
            AWS services such as Kinesis and S3.
"""

class AWSConstants:
    """
    Constants for AWS services
    """
    # AWS Region and credentials
    REGION_NAME = 'us-east-2'               # AWS Region, change as needed


class KinesisConstants:
    """
    Constants for the Kinesis stream
    """
    STREAM_NAME = 'EventStream'
    REGION_NAME = AWSConstants.REGION_NAME
    SHARD_COUNT = 1
    SHARD_ID = 'shardId-000000000000'               # Default shard ID
    SHARD_ITERATOR_TYPE = 'TRIM_HORIZON'            # Read from the start


class S3Constants:
    """
    Constants for the S3 bucket
    """
    REGION_NAME = AWSConstants.REGION_NAME
    RAW_EVENTS_BUCKET_NAME = 'raw-events-bucket'    # Name of the S3 bucket
    RAW_EVENTS_KEY = 'raw-events.json'              # Name of the raw-events data

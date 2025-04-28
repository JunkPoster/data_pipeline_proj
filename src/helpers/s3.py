"""
    File: s3.py
  Author: Ian Featherston
    Date: 04/25/2025
    Desc: Contains the S3BucketConnector class which is used to interact 
            with S3 buckets (I copied this from my other repo).
"""
import json
from io import StringIO

import boto3
import pandas as pd

from constants.aws_constants import AWSConstants
from utilities.logger import setup_logger


class S3BucketConnector:
    """
    Class to interact with S3 buckets.
    """
    def __init__(self, bucket_name: str):
        """
        Initialize the S3 bucket connector with the bucket name.
        
        Parameters:
            bucket_name (str): The name of the S3 bucket
        """
        self.logger = setup_logger()

        self.region = AWSConstants.REGION_NAME
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3', region_name=self.region)


    def get_s3_client(self) -> boto3.client:
        """
        Create an S3 client, returning it as an object.
        
        Returns:
            boto3.client: The S3 client
        """
        return self.s3_client


    def create_bucket(self):
        """
        Creates a bucket based on the class instance's bucket_name
        """
        self.s3_client.create_bucket(
            Bucket=self.bucket_name,
            CreateBucketConfiguration= {
                'LocationConstraint': self.region
            }
        )


    def get_bucket_name(self):
        """
        Simply returns the bucket name of the current S3 instance
        """
        return self.bucket_name


    def store_json_in_bucket(self, data: dict, key: str = 'stored_data.json'):
        """
        Store the passed data in S3.

        Parameters:
            data (dict): The data to be stored
        """
        self.logger.info("Storing data in S3 '%s' as '%s'.", self.bucket_name, key)
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json.dumps(data, indent=4)
        )


    def store_df_in_bucket(self, df: pd.DataFrame, key: str = 'stored_data.json'):
        """
        Stores a DataFrame in S3 as a JSON file.

        Parameters:
            df (pd.DataFrame): The DataFrame to be stroed.
            key (str): The S3 object key name.
        """
        self.logger.info("Storing DataFrame in S3 '%s' as '%s'.", self.bucket_name, key)
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=df.to_json(orient='records', indent=4)
        )


    def load_json_from_s3(self, key: str) -> pd.DataFrame:
        """
        Loads a JSON file from the S3 bucket and returns it as a DataFrame

        Parameters:
            key (str): The name of the actual file itself
        
        Returns:
            pd.DataFrame: A DataFrame containing the json data
        """
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        json_data = response["Body"].read().decode("utf-8")

        df = pd.read_json(StringIO(json_data), orient='records')
        return df

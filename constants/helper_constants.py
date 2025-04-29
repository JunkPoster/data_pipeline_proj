"""
    File: helper_constants.py
  Author: Ian Featherston
    Date: 04/25/2025
    Desc: Contains the constant values for various parameters regarding
            AWS services such as Kinesis and S3.
"""

class ProducerConstants:
    """
    Constants for the producer script that generates mock event data
    """
    EVENT_TOTAL = 1000                  # Total number of events to generate


class TransformerConstants:
    """
    Constants for the transformer.py script for generating reports
    """
    AUCTION_FEE = 0.10                  # % we take from each transaction

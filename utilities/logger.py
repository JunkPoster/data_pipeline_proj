"""
    File: logger.py
  Author: Ian Featherston
    Date: 03/26/2025
    Desc: Custom formatting for the logger throughout the project
"""
import logging
import os

def setup_logger(name='data_pipeline_logger', log_file='logs/data_pipeline.log',
                 level=logging.INFO):
    """
    Setup the logger for the project
    """
    # Constants for various formats
    log_file_name = log_file
    log_format = '[%(asctime)s %(filename)s->%(funcName)s():%(lineno)s]  ' \
                 '%(message)s'
    time_format = '%Y-%m-%d %H:%M:%S'

    # Creates the directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Check if the logger already exists and return it
    if name in logging.Logger.manager.loggerDict:
        return logging.getLogger(name)


    # Create logger object
    logger = logging.getLogger(name)

    # Remove existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Set the logging level, log format, and force a new file to be created
    handler = logging.FileHandler(log_file_name, mode='w')
    handler.setFormatter(logging.Formatter(log_format, time_format))
    logger.addHandler(handler)
    logger.setLevel(level)

    return logger

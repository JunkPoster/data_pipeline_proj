"""
    File: psql_client.py
  Author: Ian Featherston
    Date: 04/22/2025
    Desc: This script contains the PsqlConnector class that connects to a 
            PostgreSQL database and performs operations such as inserting 
            data into the database and creating tables.

            - TODO: Modularize this so it acts purely as an interface,
                    and separate core functionality for this project into its
                    own file.
"""
import io
from typing import List

import pandas as pd
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from utilities.logger import setup_logger


class PsqlConnector:
    """
    Acts as an interface to a self-hosted PostgreSQL server
    """
    def __init__(self, in_dbname, in_user, in_password, in_host, in_port):
        """
        Initializes the connection to the PostgreSQL database

        Parameters:
            in_dbname (str): The name of the database
            in_user (str): The user's Postgres username
            in_password (str): The password to said Postgres user
            in_host (str): The name of the host
            in_port (str): The port number to connect on
        """
        self.logger = setup_logger()

        self.dbname = in_dbname
        self.user = in_user
        self.password = in_password
        self.host = in_host
        self.port = in_port


    def get_connection(self):
        """
        Simply returns the current connection object to the PostgreSQL database
        """
        conn = psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )

        self.logger.info("Connected to PostgreSQL database '%s' at %s:%s",
                    self.dbname, self.port, self.port)

        return conn


    def commit_to_db(self, conn):
        """
        Commits the current changes to the db through the connection

        Parameters:
            conn: psycopg2 connection
        """
        conn.commit()


    def close_connection(self, conn, cursor):
        """
        Simply closes connection for the passed arguments

        Parameters:
            conn: psycopg2 connection
            cursor: psycopg2 connection's cursor
        """
        cursor.close()
        conn.close()


    def init_db(self, db_name: str, db_user: str,
                db_password: str, db_host: str, db_port: str):
        """
        Create a new PostgreSQL database if the passed name doesn't exist.

        Parameters:
            db_name (str): The name of the new database to create
            db_user (str): The name of the user to create it on
            db_password (str): The target user's password
            db_host (str): Target host name
            db_port (str): Target port number

        Note: This function connects to the default 'postgres' database first 
                to check if the target database already exists. If not, it
                creates the target database.
        """
        # Connect to the default DB first
        conn = psycopg2.connect(
            dbname='postgres',
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Check if the database already exists
        cur.execute("SELECT 1 from pg_database WHERE datname = %s", (db_name,))
        exists = cur.fetchone()

        if not exists:
            cur.execute(f"CREATE DATABASE {db_name};")
            self.logger.info("Database '%s' created successfully.", db_name)
        else:
            self.logger.info("Database '%s' already exists. Connecting to existing database.",
                        db_name)

        conn.commit()
        cur.close()
        conn.close()


    def init_tables(self, cursor, tables: List[tuple]):
        """
        Initializes the PostgreSQL database and deletes any existing tables, 
        then creates new tables based on the defined schemas in the constants.
        """
        for table_name, schema in tables:
            self.logger.info("Creating table '%s'", table_name)

            # Drop the tables first.
            cursor.execute(f"""
                DROP TABLE IF EXISTS {table_name} CASCADE;
            """)

            # Create the tables
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} ({schema});
            """)


    def table_exists(self, cursor, table_name: str) -> bool:
        """
        Simply checks the PostgreSQL database to see if the passed table_name
        exists.

        Parameters:
            cursor (psycopg2): psycopg2 connection cursor
            table_name (str): The name of the table to check for
        Returns:
            bool: Returns True if it DOES exist, False otherwise.
        """
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = %s
            );
        """, (table_name,))
        result = cursor.fetchone()
        return result[0] if result else False


    def create_table_from_df(self, cursor, df: pd.DataFrame, table_name: str):
        """
        Creates a table within the PostgreSQL server based on the DataFrame's
        schema.

        Parameters:
            cursor (psycopg2): psycopg2 connection cursor
            df (DataFrame): The DataFrame to create the table from
            table_name (str): The name of the table to create
        """
        # Build CREATE TABLE schema from df.dtypes
        columns = []
        dtype_mapping = {
            'object': 'TEXT',
            'int64': 'BIGINT',
            'float64': 'FLOAT',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'TIMESTAMP'
        }
        for col_name, dtype in df.dtypes.items():
            sql_dtype = dtype_mapping.get(str(dtype), 'TEXT')   # Fallback
            columns.append(f"{col_name} {sql_dtype}")

        create_table_sql = f"CREATE TABLE {table_name} ({', '.join(columns)});"
        cursor.execute(create_table_sql)


    def copy_df_into_table(self, cursor, df: pd.DataFrame, table_name: str,
                           append: bool = False):
        """
        Uses the COPY FROM operator to insert a DataFrame into PostgreSQL

        Parameters:
            cursor: psycopg2 cursor
            df (DataFrame): Data to insert
            table_name (str): Target table
            append (bool): If True, add data to the end of a table
                           If False, recreate the table with the DataFrame

        Notes:
            - This should be much faster for large tables than my
                insert_dataframe() approach below.
        """
        # If the table doesn't exist or append=True, recreate it using the
        # DataFrame's columns & dtypes.
        if not self.table_exists(cursor, table_name):
            self.create_table_from_df(cursor, df, table_name)
        elif not append:
            self.drop_table(cursor, table_name)
            self.create_table_from_df(cursor, df, table_name)

        buffer = io.StringIO()
        df.to_csv(buffer, index=False, header=False)
        buffer.seek(0)

        columns = ', '.join(df.columns)
        sql = f"COPY {table_name} ({columns}) FROM STDIN WITH CSV"
        cursor.copy_expert(sql, buffer)


    def drop_table(self, cursor, table_name: str):
        """
        Drops a table from the PostgreSQL database

        Parameters:
            table_name (str): Name of the table to drop
        """
        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
        self.logger.info("Table '%s' dropped.", table_name)


    def get_table_data(self, cursor, table_name: str, num_rows: int = -1) -> pd.DataFrame:
        """
        Simply returns all data from a table as a List of dictionaries

        Parameters:
            table_name (str): Contains the exact table name to fetch data from
            num_rows (int): Optional, a LIMIT can be enforced on the records
        
        Returns:
            pd.DataFrame: A DataFrame containing the table data
        """

        # Check if table exists first
        if not self.table_exists(cursor, table_name):
            self.logger.error("Table '%s' does NOT exist.", table_name)
            return

        # Convert num_rows to string. If -1 or 0, then '*'
        limit = "" if num_rows <= 0 else f" LIMIT {num_rows}"
        query = f"SELECT * FROM {table_name}" + limit

        # Read table data into a List of dictionaries
        self.logger.info("Fetching records from table '%s'.", table_name)
        cursor.execute(query)

        # Fetch column names
        col_names = [desc[0] for desc in cursor.description]
        records = cursor.fetchall()

        df = pd.DataFrame(records, columns=col_names)

        self.logger.info("Fetched %d records from '%s'.", len(records), table_name)
        return df
